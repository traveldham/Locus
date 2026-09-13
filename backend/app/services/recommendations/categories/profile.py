"""Profile worker: is the customer-facing listing complete, correct and verified?

Five groups of checks, all deterministic:

- Reach: can a customer call, visit the site, find the door?
- Identity: does Google know what the business is?
- Trust: verified, open, described, pictured?
- Hours: entered, every weekday, consistent with what the profile claims?
- Attributes: answered, especially accessibility?

Null is missing. An attribute with no row is unknown, never false. A permanently closed
profile is not audited for growth. Suggestions for the fields marked `suggests` are
drafted afterwards by the suggestion layer, never here.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

from app.services.recommendations.grading import graded
from app.services.recommendations.values import day

if TYPE_CHECKING:
    from app.services.recommendations.context import Context

KEY = "profile"
LABEL = "Profile completeness"
WEIGHT = 20

WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
ACCESSIBILITY_GROUP = "accessibility"

# Additional categories that imply a service attribute. A category listed while its
# attribute is explicitly false contradicts the profile; unset is unknown, not false.
CATEGORY_ATTRIBUTE_PAIRS = {
    "pediatric dentist": "pediatric_care",
    "orthodontist": "orthodontic_care",
    "dental implants periodontist": "implant_services",
    "teeth whitening service": "teeth_whitening",
    "emergency dental service": "emergency_services",
}


def check(
    weight: int,
    label: str,
    checks: str,
    fix: str,
    *,
    unit: str = "location",
    predicate: str,
    predicate_one: str,
    subject: str | None = None,
    subject_predicate: str | None = None,
    suggests: str | None = None,
    group: str = "trust",
    effort: str = "hour",
) -> dict:
    return {
        "weight": weight,
        # Which of the five groups the check belongs to, for the completeness strip.
        "group": group,
        # How long the fix usually takes: minutes, hour, afternoon. Orders the to-do.
        "effort": effort,
        "label": label,
        "checks": checks,
        "fix": fix,
        "unit": unit,
        "predicate": predicate,
        "predicate_one": predicate_one,
        "subject": subject,
        "subject_predicate": subject_predicate,
        # The profile field a suggestion may be drafted for. None: facts only the
        # business knows, or nothing to draft.
        "suggests": suggests,
    }


CHECKS: dict[str, dict] = {
    # Reach
    "phone_missing": check(
        3,
        "No phone number",
        "Whether a primary phone number is stored on the profile.",
        "Add the location's local phone number. Without it the profile shows no call "
        "button and every call click is lost.",
        predicate="have no phone number",
        predicate_one="has no phone number",
    ),
    "website_missing": check(
        3,
        "No website",
        "Whether a website link is stored on the profile.",
        "Add the location's page on the business website. Without it the profile "
        "shows no website button.",
        predicate="have no website",
        predicate_one="has no website",
    ),
    "website_not_https": check(
        1,
        "Website is not https",
        "Whether the website link uses https.",
        "Point the link at the https version of the page so browsers do not warn "
        "customers before they arrive.",
        predicate="link to a website without https",
        predicate_one="links to a website without https",
    ),
    "address_incomplete": check(
        2,
        "Incomplete address",
        "Whether city, state, postal code and, for Google-sourced profiles, the street "
        "line are all present.",
        "Complete the address exactly as it appears at the door. Customers and Google "
        "both rely on it for directions and for placing the pin.",
        predicate="have an incomplete address",
        predicate_one="has an incomplete address",
    ),
    "pin_missing": check(
        1,
        "No map pin",
        "Whether latitude and longitude are stored for the profile.",
        "Confirm the map pin in the Business Profile. Google may withhold coordinates "
        "for some listings, so verify before treating this as an error.",
        predicate="have no map pin",
        predicate_one="has no map pin",
    ),
    # Identity
    "primary_category_missing": check(
        3,
        "No primary category",
        "Whether a primary category is set.",
        "Set the single category that best describes the core business. It is the "
        "strongest relevance signal a profile has.",
        predicate="have no primary category",
        predicate_one="has no primary category",
    ),
    "secondary_categories_few": check(
        1,
        "Few additional categories",
        "How many additional categories are set against the configured minimum.",
        "Add additional categories for services the business genuinely offers. Only "
        "categories Google offers can be used, and only for real services.",
        predicate="have few additional categories",
        predicate_one="has few additional categories",
        suggests="additional_categories",
    ),
    "category_attribute_mismatch": check(
        1,
        "Category contradicted by its attribute",
        "Additional categories whose matching service attribute is explicitly set to false.",
        "Either remove the category or correct the attribute. A listing that says "
        "orthodontist and no orthodontic care confuses customers and Google.",
        unit="category",
        predicate="are contradicted by an attribute",
        predicate_one="is contradicted by an attribute",
        subject="category",
        subject_predicate="are contradicted by an attribute",
        suggests="attributes",
    ),
    # Trust
    "unverified": check(
        3,
        "Not verified",
        "Whether the profile has Voice of Merchant, Google's verified state.",
        "Complete verification in the Business Profile. Until then the listing cannot "
        "be edited, cannot reply to reviews and may not show at all.",
        predicate="are not verified",
        predicate_one="is not verified",
    ),
    "temporarily_closed": check(
        2,
        "Marked temporarily closed",
        "Whether the profile is marked temporarily closed.",
        "If the location is open, clear the temporary closure. While set, hours are "
        "hidden and the listing is demoted.",
        predicate="are marked temporarily closed",
        predicate_one="is marked temporarily closed",
    ),
    "opening_date_missing": check(
        1,
        "No opening date",
        "Whether an opening date is set.",
        "Add the month and year the location opened. Google shows years in business "
        "on the profile.",
        predicate="have no opening date",
        predicate_one="has no opening date",
    ),
    "description_missing": check(
        2,
        "No description",
        "Whether a business description is stored.",
        "Write a description of what the location offers and who it serves. Google "
        "allows 750 characters, no links, no promotions.",
        predicate="have no description",
        predicate_one="has no description",
        suggests="description",
    ),
    "description_short": check(
        2,
        "Description too short",
        "Whether the description reaches the configured minimum length.",
        "Expand the description to cover services, the area served and what sets "
        "the location apart. Stay under Google's 750 character cap.",
        predicate="have a short description",
        predicate_one="has a short description",
        suggests="description",
    ),
    "description_too_long": check(
        1,
        "Description over Google's cap",
        "Whether the description exceeds 750 characters, which Google will not save.",
        "Trim the description to 750 characters or fewer.",
        predicate="have a description over the cap",
        predicate_one="has a description over the cap",
        suggests="description",
    ),
    "description_keyword_stuffed": check(
        1,
        "Description repeats keywords",
        "Whether the category or city is repeated in the description more than the "
        "configured limit.",
        "Rewrite the description in plain language. Google rejects descriptions that "
        "read as keyword lists, and customers do not trust them.",
        predicate="have a keyword-stuffed description",
        predicate_one="has a keyword-stuffed description",
        suggests="description",
    ),
    "name_keyword_stuffed": check(
        1,
        "Name carries extra keywords",
        "Whether the business name includes category or location words beyond the real-world name.",
        "Use the name as it appears on signage. Extra words in the name breach "
        "Google's guidelines and can lead to suspension.",
        predicate="carry extra keywords in the name",
        predicate_one="carries extra keywords in the name",
        suggests="title",
    ),
    "logo_missing": check(
        2,
        "No logo",
        "Whether the photo summary marks a profile photo or logo as present.",
        "Upload the business logo as the profile photo. It is what customers see "
        "beside the name in search and Maps.",
        predicate="have no logo",
        predicate_one="has no logo",
    ),
    "cover_photo_missing": check(
        2,
        "No cover photo",
        "Whether the photo summary marks a cover photo as present.",
        "Upload a cover photo of the location. It is the first image on the profile.",
        predicate="have no cover photo",
        predicate_one="has no cover photo",
    ),
    # Hours
    "hours_missing": check(
        3,
        "No opening hours",
        "Whether any regular hours are stored.",
        "Enter regular hours for every day the location is open. Without them Maps "
        "shows hours unknown and customers cannot tell when to come.",
        predicate="have no opening hours",
        predicate_one="has no opening hours",
    ),
    "hours_weekday_gaps": check(
        2,
        "Weekday without hours",
        "Weekdays, Monday to Friday, with no regular hours entered.",
        "Enter hours for each weekday, or confirm with the manager that the location "
        "really is closed that day. A missing day and a closed day look the same.",
        unit="weekday",
        predicate="have no hours",
        predicate_one="has no hours",
        subject="weekday",
        subject_predicate="have no hours",
    ),
    "saturday_hours_inconsistent": check(
        1,
        "Saturday attribute without Saturday hours",
        "Whether the profile says Saturday appointments are offered while no Saturday "
        "hours are entered.",
        "Either add Saturday hours or set the Saturday appointments attribute to no.",
        predicate="claim Saturday appointments without Saturday hours",
        predicate_one="claims Saturday appointments without Saturday hours",
    ),
    # Attributes
    "attributes_sparse": check(
        2,
        "Attributes mostly unanswered",
        "The share of attributes Google offers for this category that are answered, "
        "yes or no, against the configured minimum.",
        "Go through the unanswered attributes with the location manager and record "
        "yes or no for each. Unanswered means unknown to customers.",
        predicate="have most attributes unanswered",
        predicate_one="has most attributes unanswered",
        suggests="attributes",
    ),
    "accessibility_unanswered": check(
        2,
        "Accessibility attribute unanswered",
        "Accessibility attributes with no yes or no recorded.",
        "Answer every accessibility attribute. Google shows accessibility prominently "
        "and an unanswered one reads as not accessible.",
        unit="attribute",
        predicate="are unanswered",
        predicate_one="is unanswered",
        subject="attribute",
        subject_predicate="are unanswered",
        suggests="attributes",
    ),
    # Consistency with the operator's own service list (projects)
    "description_quality": check(
        2,
        "Description does not say what you do or where",
        "Whether the description names the primary category, the city and at least one "
        "service from the project's service list.",
        "Rewrite the description to say what the location does, where it is and the "
        "main services it offers, in plain language.",
        predicate="have a description that says little",
        predicate_one="has a description that says little",
        suggests="description",
        group="trust",
        effort="hour",
    ),
    "services_without_category": check(
        1,
        "Service without a matching category",
        "Services in the project list whose usual Google category is not set on the profile.",
        "Add the matching category if the service is genuinely offered at this "
        "location. Categories are how Google matches a search to a profile.",
        unit="service",
        predicate="have no matching category",
        predicate_one="has no matching category",
        subject="service",
        subject_predicate="have no matching category",
        suggests="additional_categories",
        group="identity",
        effort="minutes",
    ),
    "services_without_attribute": check(
        1,
        "Service without a matching attribute",
        "Services in the project list whose matching attribute is unanswered or set to no.",
        "Confirm the service is offered here, then set the attribute to yes. If it is "
        "not offered at this location, leave the attribute at no.",
        unit="service",
        predicate="have no matching attribute",
        predicate_one="has no matching attribute",
        subject="service",
        subject_predicate="have no matching attribute",
        suggests="attributes",
        group="attributes",
        effort="minutes",
    ),
    "hours_implausible": check(
        1,
        "Implausible opening hours",
        "Days whose period closes before it opens, or lasts under three hours or over sixteen.",
        "Check the hours for that day against the real schedule. A typo here shows "
        "customers the wrong closing time.",
        unit="day",
        predicate="have implausible hours",
        predicate_one="has implausible hours",
        subject="day",
        subject_predicate="have implausible hours",
        group="hours",
        effort="minutes",
    ),
    "opening_date_in_future": check(
        1,
        "Opening date is in the future",
        "Whether the opening date is after the analysis date.",
        "Correct the opening date. A future date is allowed only for a location that "
        "has not opened yet.",
        predicate="have a future opening date",
        predicate_one="has a future opening date",
        group="trust",
        effort="minutes",
    ),
}


GROUPS = {
    "reach": (
        "phone_missing",
        "website_missing",
        "website_not_https",
        "address_incomplete",
        "pin_missing",
    ),
    "identity": (
        "primary_category_missing",
        "secondary_categories_few",
        "category_attribute_mismatch",
        "services_without_category",
    ),
    "trust": (
        "unverified",
        "temporarily_closed",
        "opening_date_missing",
        "opening_date_in_future",
        "description_missing",
        "description_short",
        "description_too_long",
        "description_keyword_stuffed",
        "description_quality",
        "name_keyword_stuffed",
        "logo_missing",
        "cover_photo_missing",
    ),
    "hours": (
        "hours_missing",
        "hours_weekday_gaps",
        "saturday_hours_inconsistent",
        "hours_implausible",
    ),
    "attributes": ("attributes_sparse", "accessibility_unanswered", "services_without_attribute"),
}
GROUP_LABELS = {
    "reach": "Reach",
    "identity": "Identity",
    "trust": "Trust",
    "hours": "Hours",
    "attributes": "Attributes",
}
EFFORT = {
    "minutes": (
        "phone_missing",
        "website_missing",
        "website_not_https",
        "pin_missing",
        "primary_category_missing",
        "secondary_categories_few",
        "category_attribute_mismatch",
        "temporarily_closed",
        "opening_date_missing",
        "opening_date_in_future",
        "description_too_long",
        "name_keyword_stuffed",
        "hours_missing",
        "hours_weekday_gaps",
        "saturday_hours_inconsistent",
        "hours_implausible",
        "services_without_category",
        "services_without_attribute",
    ),
    "hour": (
        "address_incomplete",
        "description_missing",
        "description_short",
        "description_keyword_stuffed",
        "description_quality",
        "logo_missing",
        "cover_photo_missing",
        "accessibility_unanswered",
    ),
    "afternoon": ("unverified", "attributes_sparse"),
}
for _group, _rules in GROUPS.items():
    for _rule in _rules:
        CHECKS[_rule]["group"] = _group
for _effort, _rules in EFFORT.items():
    for _rule in _rules:
        CHECKS[_rule]["effort"] = _effort
assert {r for rules in GROUPS.values() for r in rules} == set(CHECKS)
assert {r for rules in EFFORT.values() for r in rules} == set(CHECKS)

# Project services that usually imply a Google category and a service attribute.
# Matching is by keyword inside the service name, case-insensitive.
SERVICE_HINTS = (
    ("whitening", "Teeth whitening service", "teeth_whitening"),
    ("implant", "Dental implants periodontist", "implant_services"),
    ("invisalign", "Orthodontist", "orthodontic_care"),
    ("braces", "Orthodontist", "orthodontic_care"),
    ("kids", "Pediatric dentist", "pediatric_care"),
    ("child", "Pediatric dentist", "pediatric_care"),
    ("pediatric", "Pediatric dentist", "pediatric_care"),
    ("emergency", "Emergency dental service", "emergency_services"),
)


def project_services(c: Context) -> list[str]:
    seen: dict[str, None] = {}
    for project in c.snapshot.get("projects", []):
        for service in project.get("services") or []:
            if isinstance(service, str) and service.strip():
                seen.setdefault(service.strip(), None)
    return list(seen)


def hinted(services: list[str]) -> list[tuple[str, str, str]]:
    """(service, category, attribute) for every service a hint recognises."""
    out = []
    for service in services:
        lowered = service.casefold()
        for needle, category, attribute in SERVICE_HINTS:
            if needle in lowered:
                out.append((service, category, attribute))
                break
    return out


def blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def answered(row: dict) -> bool:
    values = row.get("values")
    return isinstance(values, list) and any(v is not None for v in values)


def truthy(row: dict) -> bool | None:
    """True, False, or None for unknown. Tolerates the enum-as-string fixture trap."""
    if not answered(row):
        return None
    first = row["values"][0]
    if isinstance(first, bool):
        return first
    if isinstance(first, str):
        if first.upper() == "TRUE":
            return True
        if first.upper() == "FALSE":
            return False
    return None


def attribute_name(row: dict) -> str:
    return str(row.get("attribute_id", "")).removeprefix("attributes/")


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def evaluate(c: Context) -> None:
    loc = c.location
    href = f"/locations/{loc['id']}"
    if loc.get("open_status") == "closed_permanently":
        for rule in CHECKS:
            c.assess(rule, "suppressed", "Permanently closed: the profile is not audited.")
        return

    _reach(c, loc, href)
    _identity(c, loc, href)
    _trust(c, loc, href)
    _hours(c, loc, href)
    _attributes(c, loc, href)
    _services(c, loc, href)


def _reach(c: Context, loc: dict, href: str) -> None:
    if blank(loc.get("phone_primary")):
        c.assess("phone_missing", "triggered", "No phone number is stored.", 1)
        c.emit(
            "phone_missing",
            "Add a phone number",
            CHECKS["phone_missing"]["fix"],
            "The profile has no phone number, so it shows no call button.",
            88,
            [c.evidence("locations", [loc], ["phone_primary"], "phone_primary is empty")],
            href,
            "Current stored state. Only the business can supply the number.",
            "high",
        )
    else:
        c.assess("phone_missing", "clear", "A phone number is stored.")

    website = loc.get("website_uri")
    if blank(website):
        c.assess("website_missing", "triggered", "No website is stored.", 1)
        c.emit(
            "website_missing",
            "Add a website link",
            CHECKS["website_missing"]["fix"],
            "The profile has no website, so it shows no website button.",
            85,
            [c.evidence("locations", [loc], ["website_uri"], "website_uri is empty")],
            href,
            "Current stored state. Only the business can supply the address.",
            "high",
        )
        c.assess("website_not_https", "insufficient_data", "No website to check.")
    else:
        c.assess("website_missing", "clear", "A website is stored.")
        if str(website).strip().lower().startswith("https://"):
            c.assess("website_not_https", "clear", "The website uses https.")
        else:
            c.assess("website_not_https", "triggered", "The website link is not https.", 1)
            c.emit(
                "website_not_https",
                "Use the https address",
                CHECKS["website_not_https"]["fix"],
                f"The website link is {website}, which does not start with https://.",
                20,
                [
                    c.evidence(
                        "locations",
                        [loc],
                        ["website_uri"],
                        "scheme of website_uri",
                        website=website,
                    )
                ],
                href,
                "Checks the stored link only, not whether the site itself redirects.",
                "high",
            )

    required = ["locality", "administrative_area", "postal_code"]
    missing = [f for f in required if blank(loc.get(f))]
    if loc.get("source") == "google" and not loc.get("address_lines"):
        missing.append("address_lines")
    if missing:
        labels = {
            "locality": "city",
            "administrative_area": "state",
            "postal_code": "postal code",
            "address_lines": "street line",
        }
        named = ", ".join(labels[f] for f in missing)
        c.assess("address_incomplete", "triggered", f"Address is missing {named}.", 1)
        c.emit(
            "address_incomplete",
            "Complete the address",
            CHECKS["address_incomplete"]["fix"],
            f"The address is missing: {named}.",
            graded(50, (len(missing) - 1) / 3, 15, 65),
            [
                c.evidence(
                    "locations",
                    [loc],
                    missing,
                    "Required address parts that are empty",
                    missing=missing,
                )
            ],
            href,
            "The street line is only required of Google-sourced profiles; the sample "
            "export never carries one.",
            "high",
        )
    else:
        c.assess("address_incomplete", "clear", "City, state and postal code are present.")

    if loc.get("latitude") is None or loc.get("longitude") is None:
        c.assess("pin_missing", "triggered", "No coordinates are stored.", 1)
        c.emit(
            "pin_missing",
            "Confirm the map pin",
            CHECKS["pin_missing"]["fix"],
            "No latitude and longitude are stored for the profile.",
            15,
            [c.evidence("locations", [loc], ["latitude", "longitude"], "coordinates empty")],
            href,
            "Google does not always return coordinates, so this may be a data gap "
            "rather than a missing pin.",
        )
    else:
        c.assess("pin_missing", "clear", "Coordinates are stored.")


def _identity(c: Context, loc: dict, href: str) -> None:
    categories = c.rows("categories")
    primary = [r for r in categories if r.get("is_primary")]
    if not primary and blank(loc.get("primary_category_display")):
        c.assess("primary_category_missing", "triggered", "No primary category is set.", 1)
        c.emit(
            "primary_category_missing",
            "Set a primary category",
            CHECKS["primary_category_missing"]["fix"],
            "The profile has no primary category.",
            90,
            [
                c.evidence(
                    "locations",
                    [loc],
                    ["primary_category_display"],
                    "no primary category row and primary_category_display empty",
                )
            ],
            href,
            "Current stored state.",
            "high",
        )
    else:
        c.assess("primary_category_missing", "clear", "A primary category is set.")

    additional = [r for r in categories if not r.get("is_primary")]
    minimum = c.config.min_additional_categories
    if not categories:
        c.assess(
            "secondary_categories_few",
            "insufficient_data",
            "No category rows were synced, so the count is unknown.",
        )
    elif len(additional) < minimum:
        c.assess(
            "secondary_categories_few",
            "triggered",
            f"{len(additional)} additional categories, below the minimum of {minimum}.",
            1,
        )
        c.emit(
            "secondary_categories_few",
            "Add additional categories",
            CHECKS["secondary_categories_few"]["fix"],
            f"The profile lists {len(additional)} additional "
            f"{'category' if len(additional) == 1 else 'categories'}; the policy "
            f"minimum is {minimum}.",
            graded(25, (minimum - len(additional)) / max(1, minimum), 15, 40),
            [
                c.evidence(
                    "categories",
                    categories,
                    ["display_name", "is_primary"],
                    "count of rows where is_primary is false",
                    additional=[r.get("display_name") for r in additional],
                    minimum=minimum,
                )
            ],
            href,
            "The minimum is an operating policy. Only genuine services should be "
            "added as categories.",
        )
    else:
        c.assess("secondary_categories_few", "clear", f"{len(additional)} additional categories.")

    attributes = {attribute_name(r): r for r in c.rows("attributes")}
    contradicted = []
    for row in additional:
        pair = CATEGORY_ATTRIBUTE_PAIRS.get(str(row.get("display_name") or "").casefold())
        if pair and pair in attributes and truthy(attributes[pair]) is False:
            contradicted.append((row, attributes[pair]))
    checkable = [
        r
        for r in additional
        if CATEGORY_ATTRIBUTE_PAIRS.get(str(r.get("display_name") or "").casefold()) in attributes
    ]
    if not checkable:
        c.assess(
            "category_attribute_mismatch",
            "insufficient_data",
            "No additional category has a matching answered attribute to compare.",
        )
    elif contradicted:
        c.assess(
            "category_attribute_mismatch",
            "triggered",
            f"{len(contradicted)} of {len(checkable)} categories are contradicted by an "
            "attribute set to no.",
            len(contradicted),
            len(checkable),
        )
        for category, attribute in contradicted:
            name = category.get("display_name")
            c.emit(
                "category_attribute_mismatch",
                f"“{name}” is listed but its attribute says no",
                CHECKS["category_attribute_mismatch"]["fix"],
                f"The profile lists “{name}” as a category while the attribute "
                f"“{attribute_name(attribute).replace('_', ' ')}” is set to no.",
                35,
                [
                    c.evidence(
                        "categories",
                        [category],
                        ["display_name"],
                        "additional category",
                        category=name,
                    ),
                    c.evidence(
                        "attributes",
                        [attribute],
                        ["attribute_id", "values"],
                        "matching attribute explicitly false",
                        attribute=attribute_name(attribute),
                    ),
                ],
                href,
                "A contradiction, not proof of which side is wrong. Confirm with the "
                "location manager.",
                "high",
                subject=str(name),
            )
    else:
        c.assess(
            "category_attribute_mismatch",
            "clear",
            f"No contradiction across {len(checkable)} checkable categories.",
        )


def _trust(c: Context, loc: dict, href: str) -> None:
    if loc.get("has_voice_of_merchant") is False:
        c.assess("unverified", "triggered", "The profile is not verified.", 1)
        c.emit(
            "unverified",
            "Verify the profile",
            CHECKS["unverified"]["fix"],
            "The profile does not have Voice of Merchant, Google's verified state.",
            92,
            [
                c.evidence(
                    "locations",
                    [loc],
                    ["has_voice_of_merchant"],
                    "has_voice_of_merchant is false",
                )
            ],
            href,
            "For sample-sourced profiles this flag comes from the export, not from Google.",
            "high" if loc.get("source") == "google" else "medium",
        )
    else:
        c.assess("unverified", "clear", "The profile is verified.")

    if loc.get("open_status") == "closed_temporarily":
        c.assess("temporarily_closed", "triggered", "Marked temporarily closed.", 1)
        c.emit(
            "temporarily_closed",
            "Review the temporary closure",
            CHECKS["temporarily_closed"]["fix"],
            "The profile is marked temporarily closed.",
            60,
            [c.evidence("locations", [loc], ["open_status"], "open_status")],
            href,
            "Correct if the location really is closed for now.",
            "high",
        )
    elif loc.get("open_status") is None:
        c.assess("temporarily_closed", "insufficient_data", "Open status is unknown.")
    else:
        c.assess("temporarily_closed", "clear", "The profile is open.")

    if blank(loc.get("opening_date")):
        c.assess("opening_date_missing", "triggered", "No opening date is set.", 1)
        c.emit(
            "opening_date_missing",
            "Add the opening date",
            CHECKS["opening_date_missing"]["fix"],
            "The profile has no opening date.",
            15,
            [c.evidence("locations", [loc], ["opening_date"], "opening_date empty")],
            href,
            "Only the business knows the date.",
            "high",
        )
    else:
        c.assess("opening_date_missing", "clear", "An opening date is set.")
        opened = day(loc.get("opening_date"))
        if opened is None:
            c.assess("opening_date_in_future", "insufficient_data", "Opening date is not a date.")
        elif opened > c.as_of:
            c.assess(
                "opening_date_in_future",
                "triggered",
                f"Opening date {opened} is after {c.as_of}.",
                1,
            )
            c.emit(
                "opening_date_in_future",
                "Correct the opening date",
                CHECKS["opening_date_in_future"]["fix"],
                f"The opening date is {opened}, after the analysis date {c.as_of}.",
                25,
                [c.evidence("locations", [loc], ["opening_date"], "opening_date > as_of")],
                href,
                "Legitimate only for a location that has not opened yet.",
                "high",
            )
        else:
            c.assess("opening_date_in_future", "clear", "Opening date is in the past.")
    if blank(loc.get("opening_date")):
        c.assess("opening_date_in_future", "insufficient_data", "No opening date.")

    _description(c, loc, href)
    _name(c, loc, href)

    media = c.rows("media")
    if not media:
        for rule in ("logo_missing", "cover_photo_missing"):
            c.assess(rule, "insufficient_data", "No photo summary is stored.")
    else:
        row = media[0]
        for rule, flag, title in (
            ("logo_missing", "has_profile_photo", "Upload a logo"),
            ("cover_photo_missing", "has_cover_photo", "Upload a cover photo"),
        ):
            if row.get(flag) is False:
                c.assess(rule, "triggered", f"{flag} is false.", 1)
                c.emit(
                    rule,
                    title,
                    CHECKS[rule]["fix"],
                    "The photo summary marks the "
                    + ("logo" if flag == "has_profile_photo" else "cover photo")
                    + " as missing.",
                    58 if rule == "logo_missing" else 50,
                    [c.evidence("media", [row], [flag], f"{flag} is false")],
                    "/insights/photos",
                    "A flag on the summary, not an inspection of the image itself.",
                    "high",
                )
            elif row.get(flag) is None:
                c.assess(rule, "insufficient_data", f"{flag} is unknown.")
            else:
                c.assess(rule, "clear", f"{flag} is true.")


def _description(c: Context, loc: dict, href: str) -> None:
    text = loc.get("description")
    dependent = ("description_short", "description_too_long", "description_keyword_stuffed")
    if blank(text):
        c.assess("description_missing", "triggered", "No description is stored.", 1)
        c.emit(
            "description_missing",
            "Write a description",
            CHECKS["description_missing"]["fix"],
            "The profile has no description.",
            62,
            [c.evidence("locations", [loc], ["description"], "description empty")],
            href,
            "A suggestion can be drafted, but the business must confirm it.",
            "high",
        )
        for rule in dependent:
            c.assess(rule, "insufficient_data", "No description to check.")
        return
    c.assess("description_missing", "clear", "A description is stored.")

    text = str(text).strip()
    length = len(text)
    minimum, maximum = c.config.description_min_chars, c.config.description_max_chars
    if length < minimum:
        c.assess("description_short", "triggered", f"{length} characters, below {minimum}.", 1)
        c.emit(
            "description_short",
            "Expand the description",
            CHECKS["description_short"]["fix"],
            f"The description is {length} characters; the policy minimum is {minimum}.",
            graded(35, (minimum - length) / minimum, 20, 55),
            [
                c.evidence(
                    "locations",
                    [loc],
                    ["description"],
                    "len(description)",
                    length=length,
                    minimum=minimum,
                )
            ],
            href,
            "Length is a proxy for usefulness, not a Google rule.",
            "high",
        )
    else:
        c.assess("description_short", "clear", f"{length} characters.")

    if length > maximum:
        c.assess("description_too_long", "triggered", f"{length} characters, over {maximum}.", 1)
        c.emit(
            "description_too_long",
            "Trim the description",
            CHECKS["description_too_long"]["fix"],
            f"The description is {length} characters; Google's cap is {maximum}.",
            30,
            [
                c.evidence(
                    "locations",
                    [loc],
                    ["description"],
                    "len(description)",
                    length=length,
                    maximum=maximum,
                )
            ],
            href,
            "Google will not save a description over the cap.",
            "high",
        )
    else:
        c.assess("description_too_long", "clear", "Within Google's cap.")

    terms = words(str(loc.get("primary_category_display") or "")) + words(
        str(loc.get("locality") or "")
    )
    counts = Counter(words(text))
    limit = c.config.description_max_term_repeats
    repeated = {t: counts[t] for t in set(terms) if counts.get(t, 0) >= limit}
    if not terms:
        c.assess(
            "description_keyword_stuffed",
            "insufficient_data",
            "No category or city to look for.",
        )
    elif repeated:
        c.assess(
            "description_keyword_stuffed",
            "triggered",
            f"{len(repeated)} terms repeated {limit} or more times.",
            1,
        )
        c.emit(
            "description_keyword_stuffed",
            "Rewrite the description in plain language",
            CHECKS["description_keyword_stuffed"]["fix"],
            "The description repeats "
            + ", ".join(f"“{t}” {n} times" for t, n in sorted(repeated.items()))
            + ".",
            graded(30, (max(repeated.values()) - limit) / limit, 10, 42),
            [
                c.evidence(
                    "locations",
                    [loc],
                    ["description", "primary_category_display", "locality"],
                    "count of category and city words in description",
                    repeated=repeated,
                    limit=limit,
                )
            ],
            href,
            "Word counts, not a judgement of quality.",
            "high",
        )
    else:
        c.assess("description_keyword_stuffed", "clear", "No term repeated past the limit.")


def _name(c: Context, loc: dict, href: str) -> None:
    title = str(loc.get("title") or "")
    if not title.strip():
        c.assess("name_keyword_stuffed", "insufficient_data", "No name stored.")
        return
    title_words = Counter(words(title))
    category = set(words(str(loc.get("primary_category_display") or "")))
    city = set(words(str(loc.get("locality") or "")))
    # A multi-word city or category counts once. A branch name such as
    # "Brightpath Dental — Round Rock" is one city mention, which is normal. Stuffing is
    # the category and the city together, or the category word repeated.
    has_category = bool(category) and category <= set(title_words)
    has_city = bool(city) and city <= set(title_words)
    repeats = max((title_words[w] for w in category), default=0)
    extra = int(has_category) + int(has_city) + max(0, repeats - 1)
    if extra >= 2:
        c.assess("name_keyword_stuffed", "triggered", "Name repeats category or city words.", 1)
        c.emit(
            "name_keyword_stuffed",
            "Use the real-world business name",
            CHECKS["name_keyword_stuffed"]["fix"],
            f"The name “{title}” carries {extra} category or city words.",
            40,
            [
                c.evidence(
                    "locations",
                    [loc],
                    ["title", "primary_category_display", "locality"],
                    "count of category and city words in title",
                    extra_words=extra,
                )
            ],
            href,
            "A heuristic. Some real names legitimately include a place or a trade.",
        )
    else:
        c.assess("name_keyword_stuffed", "clear", "Name does not repeat category or city.")


def _hours(c: Context, loc: dict, href: str) -> None:
    regular = [r for r in c.rows("hours") if (r.get("hours_type") or "REGULAR") == "REGULAR"]
    if not regular:
        c.assess("hours_missing", "triggered", "No regular hours are stored.", 1)
        c.emit(
            "hours_missing",
            "Enter opening hours",
            CHECKS["hours_missing"]["fix"],
            "The profile has no regular hours at all.",
            86,
            [c.evidence("hours", [], ["open_day"], "zero regular hours rows")],
            href,
            "Only the business knows its hours.",
            "high",
        )
        c.assess("hours_weekday_gaps", "insufficient_data", "No hours to check by day.")
        c.assess("saturday_hours_inconsistent", "insufficient_data", "No hours stored.")
        c.assess("hours_implausible", "insufficient_data", "No hours stored.")
        return
    c.assess("hours_missing", "clear", f"{len(regular)} hours periods stored.")

    days = {str(r.get("open_day")).upper() for r in regular}
    gaps = [d for d in WEEKDAYS if d not in days]
    if gaps:
        c.assess(
            "hours_weekday_gaps",
            "triggered",
            f"{len(gaps)} of 5 weekdays have no hours.",
            len(gaps),
            len(WEEKDAYS),
        )
        for day in gaps:
            c.emit(
                "hours_weekday_gaps",
                f"No hours on {day.title()}",
                CHECKS["hours_weekday_gaps"]["fix"],
                f"No regular hours are entered for {day.title()}.",
                graded(40, (len(gaps) - 1) / 4, 15, 55),
                [
                    c.evidence(
                        "hours",
                        regular,
                        ["open_day", "open_hour", "close_hour"],
                        "weekdays absent from regular hours",
                        missing_day=day,
                    )
                ],
                href,
                "A closed day and a day never entered look identical here.",
                subject=day.title(),
            )
    else:
        c.assess("hours_weekday_gaps", "clear", "Every weekday has hours.")

    odd = []
    for r in regular:
        if str(r.get("open_day")).upper() != str(r.get("close_day")).upper():
            continue  # an overnight span is legitimate and not judged here
        opens = int(r.get("open_hour") or 0) * 60 + int(r.get("open_minute") or 0)
        closes = int(r.get("close_hour") or 0) * 60 + int(r.get("close_minute") or 0)
        length = closes - opens
        if length <= 0 or length < 180 or length > 960:
            odd.append((r, length))
    if odd:
        c.assess(
            "hours_implausible",
            "triggered",
            f"{len(odd)} of {len(regular)} periods look wrong.",
            len(odd),
            len(regular),
        )
        for r, length in odd:
            day_name = str(r.get("open_day")).title()
            c.emit(
                "hours_implausible",
                f"{day_name} hours look wrong",
                CHECKS["hours_implausible"]["fix"],
                f"{day_name} opens {int(r.get('open_hour') or 0):02d}:"
                f"{int(r.get('open_minute') or 0):02d} and closes "
                f"{int(r.get('close_hour') or 0):02d}:{int(r.get('close_minute') or 0):02d}"
                + (
                    ", which is before it opens."
                    if length <= 0
                    else f", a {length // 60}h{length % 60:02d} day."
                ),
                30,
                [
                    c.evidence(
                        "hours",
                        [r],
                        ["open_day", "open_hour", "open_minute", "close_hour", "close_minute"],
                        "close minus open, same day",
                        minutes=length,
                    )
                ],
                href,
                "A plausibility check with fixed bounds, not knowledge of the schedule.",
                "high",
                subject=day_name,
            )
    else:
        c.assess("hours_implausible", "clear", "Every period is a plausible length.")

    attributes = {attribute_name(r): r for r in c.rows("attributes")}
    saturday = attributes.get("saturday_appointments")
    if saturday is None or truthy(saturday) is None:
        c.assess(
            "saturday_hours_inconsistent",
            "insufficient_data",
            "The Saturday appointments attribute is unanswered.",
        )
    elif truthy(saturday) and "SATURDAY" not in days:
        c.assess(
            "saturday_hours_inconsistent",
            "triggered",
            "Saturday appointments is yes but no Saturday hours are entered.",
            1,
        )
        c.emit(
            "saturday_hours_inconsistent",
            "Add Saturday hours or correct the attribute",
            CHECKS["saturday_hours_inconsistent"]["fix"],
            "The profile says Saturday appointments are offered, but no Saturday hours "
            "are entered.",
            30,
            [
                c.evidence(
                    "attributes",
                    [saturday],
                    ["attribute_id", "values"],
                    "saturday_appointments is true",
                ),
                c.evidence("hours", regular, ["open_day"], "no SATURDAY row"),
            ],
            href,
            "A contradiction to confirm with the manager.",
            "high",
        )
    else:
        c.assess("saturday_hours_inconsistent", "clear", "Saturday claim and hours agree.")


def _attributes(c: Context, loc: dict, href: str) -> None:
    category = str(loc.get("primary_category_display") or "").casefold()
    # The catalog is organization-wide vocabulary, so it is read from the snapshot
    # directly rather than through the location filter.
    catalog = [
        r
        for r in c.snapshot.get("catalog", [])
        if str(r.get("applies_to_category") or "").casefold() == category
    ]
    rows = {attribute_name(r): r for r in c.rows("attributes")}
    if not catalog:
        c.assess(
            "attributes_sparse", "insufficient_data", "No attribute catalog for this category."
        )
        c.assess(
            "accessibility_unanswered",
            "insufficient_data",
            "No attribute catalog for this category.",
        )
        return

    answered_names = [
        r["attribute_name"] for r in catalog if answered(rows.get(r["attribute_name"], {}))
    ]
    unanswered = [r for r in catalog if r["attribute_name"] not in answered_names]
    share = len(answered_names) / len(catalog)
    minimum = c.config.attribute_coverage_min
    if share < minimum:
        c.assess(
            "attributes_sparse",
            "triggered",
            f"{len(answered_names)} of {len(catalog)} attributes answered ({share:.0%}).",
            len(unanswered),
            len(catalog),
        )
        c.emit(
            "attributes_sparse",
            "Answer the unanswered attributes",
            CHECKS["attributes_sparse"]["fix"],
            f"Only {len(answered_names)} of {len(catalog)} attributes Google offers for "
            f"this category are answered ({share:.0%}); the policy minimum is {minimum:.0%}.",
            graded(40, (minimum - share) / minimum, 20, 60),
            [
                c.evidence(
                    "catalog",
                    catalog,
                    ["attribute_name", "attribute_group"],
                    "catalog attributes for the primary category",
                    unanswered=[r["attribute_name"] for r in unanswered],
                ),
                c.evidence(
                    "attributes",
                    list(rows.values()),
                    ["attribute_id", "values"],
                    "answered means a row with a value, yes or no",
                    answered=len(answered_names),
                ),
            ],
            href,
            "An answer of no counts as answered. Never mark a service the location does not offer.",
            "high",
        )
    else:
        c.assess(
            "attributes_sparse",
            "clear",
            f"{len(answered_names)} of {len(catalog)} attributes answered.",
        )

    accessibility = [r for r in catalog if r.get("attribute_group") == ACCESSIBILITY_GROUP]
    if not accessibility:
        c.assess(
            "accessibility_unanswered",
            "insufficient_data",
            "The catalog has no accessibility attributes.",
        )
        return
    open_items = [r for r in accessibility if not answered(rows.get(r["attribute_name"], {}))]
    if open_items:
        c.assess(
            "accessibility_unanswered",
            "triggered",
            f"{len(open_items)} of {len(accessibility)} accessibility attributes unanswered.",
            len(open_items),
            len(accessibility),
        )
        for item in open_items:
            name = item["attribute_name"]
            c.emit(
                "accessibility_unanswered",
                f"Answer “{name.replace('_', ' ')}”",
                CHECKS["accessibility_unanswered"]["fix"],
                f"The accessibility attribute “{name.replace('_', ' ')}” has no answer.",
                graded(40, (len(open_items) - 1) / max(1, len(accessibility) - 1), 12, 52),
                [
                    c.evidence(
                        "catalog",
                        [item],
                        ["attribute_name", "attribute_group"],
                        "accessibility attribute with no answered row",
                        attribute=name,
                    )
                ],
                href,
                "Unanswered is unknown, not no. Confirm on site before answering.",
                "high",
                subject=name,
            )
    else:
        c.assess(
            "accessibility_unanswered",
            "clear",
            f"All {len(accessibility)} accessibility attributes answered.",
        )


def _services(c: Context, loc: dict, href: str) -> None:
    """Checks against the operator's own service list, and the description's substance."""
    services = project_services(c)
    hints = hinted(services)
    categories = {str(r.get("display_name") or "").casefold() for r in c.rows("categories")} | {
        str(loc.get("primary_category_display") or "").casefold()
    }
    attributes = {attribute_name(r): r for r in c.rows("attributes")}
    catalog_names = {
        r["attribute_name"]
        for r in c.snapshot.get("catalog", [])
        if str(r.get("applies_to_category") or "").casefold()
        == str(loc.get("primary_category_display") or "").casefold()
    }

    # Description substance: what, where, which services.
    text = loc.get("description")
    if blank(text) or len(str(text).strip()) < c.config.description_min_chars:
        c.assess(
            "description_quality",
            "insufficient_data",
            "No description of usable length to judge.",
        )
    else:
        lowered = str(text).casefold()
        category_words = words(str(loc.get("primary_category_display") or ""))
        city_words = words(str(loc.get("locality") or ""))
        says_what = bool(category_words) and any(w in lowered for w in category_words)
        says_where = bool(city_words) and all(w in lowered for w in city_words)
        named = [s for s in services if any(w in lowered for w in words(s) if len(w) > 3)]
        met = int(says_what) + int(says_where) + int(bool(named))
        if met < 2:
            c.assess(
                "description_quality",
                "triggered",
                "The description covers fewer than two of: what, where, which services.",
                1,
            )
            c.emit(
                "description_quality",
                "Say what you do, where, and which services",
                CHECKS["description_quality"]["fix"],
                "The description "
                + ("names the category" if says_what else "does not name the category")
                + ", "
                + ("mentions the city" if says_where else "does not mention the city")
                + ", and "
                + (
                    f"names {len(named)} listed services."
                    if named
                    else "names none of the listed services."
                ),
                graded(38, (2 - met) / 2, 12, 50),
                [
                    c.evidence(
                        "locations",
                        [loc],
                        ["description", "primary_category_display", "locality"],
                        "category word, city words and service names found in description",
                        says_what=says_what,
                        says_where=says_where,
                        services_named=named,
                        services_listed=services,
                    )
                ],
                href,
                "Word matching, not a judgement of writing quality.",
                "high",
            )
        else:
            c.assess(
                "description_quality", "clear", "Description says what, where and which services."
            )

    # Services versus categories.
    if not hints:
        c.assess(
            "services_without_category",
            "insufficient_data",
            "No project services recognised for a category hint.",
        )
        c.assess(
            "services_without_attribute",
            "insufficient_data",
            "No project services recognised for an attribute hint.",
        )
        return
    uncategorised = [(s, cat) for s, cat, _ in hints if cat.casefold() not in categories]
    if uncategorised:
        c.assess(
            "services_without_category",
            "triggered",
            f"{len(uncategorised)} of {len(hints)} recognised services have no matching category.",
            len(uncategorised),
            len(hints),
        )
        for service, category in uncategorised:
            c.emit(
                "services_without_category",
                f"“{service}” has no matching category",
                CHECKS["services_without_category"]["fix"],
                f"The project lists “{service}” but the profile has no “{category}” category.",
                30,
                [
                    c.evidence(
                        "projects",
                        c.snapshot.get("projects", []),
                        ["name", "services"],
                        "service name matched a category hint",
                        service=service,
                        expected_category=category,
                    ),
                    c.evidence(
                        "categories",
                        c.rows("categories"),
                        ["display_name", "is_primary"],
                        "categories set on the profile",
                    ),
                ],
                href,
                "A hint from the service name. Only add the category if the service is "
                "offered at this location.",
                subject=service,
            )
    else:
        c.assess(
            "services_without_category",
            "clear",
            f"All {len(hints)} recognised services have a matching category.",
        )

    # Services versus attributes, only for attributes the catalog offers.
    checkable = [(s, attr) for s, _, attr in hints if attr in catalog_names]
    if not checkable:
        c.assess(
            "services_without_attribute",
            "insufficient_data",
            "The catalog offers no attribute for the recognised services.",
        )
        return
    missing = [(s, attr) for s, attr in checkable if truthy(attributes.get(attr, {})) is not True]
    if missing:
        c.assess(
            "services_without_attribute",
            "triggered",
            f"{len(missing)} of {len(checkable)} recognised services lack a yes on their "
            "attribute.",
            len(missing),
            len(checkable),
        )
        for service, attr in missing:
            state = truthy(attributes.get(attr, {}))
            c.emit(
                "services_without_attribute",
                f"“{service}” is offered but “{attr.replace('_', ' ')}” is "
                + ("unanswered" if state is None else "no"),
                CHECKS["services_without_attribute"]["fix"],
                f"The project lists “{service}” while the attribute "
                f"“{attr.replace('_', ' ')}” is {'unanswered' if state is None else 'set to no'}.",
                32 if state is None else 38,
                [
                    c.evidence(
                        "projects",
                        c.snapshot.get("projects", []),
                        ["name", "services"],
                        "service name matched an attribute hint",
                        service=service,
                        attribute=attr,
                        attribute_state=("unanswered" if state is None else "no"),
                    )
                ],
                href,
                "Unanswered is unknown, not no. Confirm on site before answering.",
                subject=service,
            )
    else:
        c.assess(
            "services_without_attribute",
            "clear",
            f"All {len(checkable)} recognised services have a yes on their attribute.",
        )


def clock(hour, minute) -> str:
    return f"{int(hour or 0):02d}:{int(minute or 0):02d}"


def card(snapshot: dict) -> dict:
    """The profile as a customer would see it, for the before-and-after view."""
    loc = snapshot["locations"][0]
    location_id = loc["id"]
    rows = lambda source: [  # noqa: E731 - tiny local helper
        r for r in snapshot.get(source, []) if r.get("location_id") == location_id
    ]
    media = (rows("media") or [{}])[0]
    hours = sorted(
        (
            {
                "day": str(r.get("open_day") or "").title(),
                "open": clock(r.get("open_hour"), r.get("open_minute")),
                "close": clock(r.get("close_hour"), r.get("close_minute")),
            }
            for r in rows("hours")
            if (r.get("hours_type") or "REGULAR") == "REGULAR"
        ),
        key=lambda h: (
            (WEEKDAYS + ("SATURDAY", "SUNDAY")).index(h["day"].upper())
            if h["day"].upper() in WEEKDAYS + ("SATURDAY", "SUNDAY")
            else 99
        ),
    )
    attributes = rows("attributes")
    return {
        "name": loc.get("title"),
        "primary_category": loc.get("primary_category_display"),
        "additional_categories": [
            r.get("display_name") for r in rows("categories") if not r.get("is_primary")
        ],
        "phone": loc.get("phone_primary"),
        "website": loc.get("website_uri"),
        "description": loc.get("description"),
        "address": {
            "lines": loc.get("address_lines") or [],
            "locality": loc.get("locality"),
            "administrative_area": loc.get("administrative_area"),
            "postal_code": loc.get("postal_code"),
        },
        "has_pin": loc.get("latitude") is not None and loc.get("longitude") is not None,
        "hours": hours,
        "verified": loc.get("has_voice_of_merchant"),
        "open_status": loc.get("open_status"),
        "opening_date": loc.get("opening_date"),
        "has_logo": media.get("has_profile_photo"),
        "has_cover": media.get("has_cover_photo"),
        "photo_count": media.get("photo_count"),
        "attributes_yes": sorted(attribute_name(r) for r in attributes if truthy(r) is True),
        "attributes_no": sorted(attribute_name(r) for r in attributes if truthy(r) is False),
    }
