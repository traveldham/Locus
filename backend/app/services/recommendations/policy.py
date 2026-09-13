"""Versioned audit policy: categories, weights, severity bands and penalties.

Every number here is an explicit operating decision, not a measured business fact.
Changing one changes the health score, so it belongs in the engine version.
"""

from app.services.recommendations.types import Severity

# Category weights sum to 100. Rule weights are relative inside their category.
CATEGORIES: dict[str, dict] = {
    "profile": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "has incomplete customer-facing information",
        "unit": "location",
        "predicate": "have incomplete customer-facing information",
        "label": "Profile completeness",
        "weight": 20,
        "rules": {"profile": 3, "attributes": 1},
    },
    "reputation": {
        "label": "Reputation",
        "weight": 20,
        "rules": {"reviews": 3},
    },
    "visibility": {
        "label": "Local visibility",
        "weight": 25,
        "rules": {"rankings": 2, "search": 1},
    },
    "operations": {
        "label": "Operations",
        "weight": 15,
        "rules": {"booking_followup": 2, "booking_outcomes": 2},
    },
    "performance": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "has falling impressions or action intensity",
        "unit": "location",
        "predicate": "have falling impressions or action intensity",
        "label": "Performance",
        "weight": 10,
        "rules": {"performance": 1},
    },
    "content": {
        "label": "Content",
        "weight": 10,
        "rules": {"media": 1, "posts": 1},
    },
}

RULE_CATEGORY = {rule: name for name, spec in CATEGORIES.items() for rule in spec["rules"]}

# Score bands. A score orders work; it is not a probability or a predicted gain.
CRITICAL_SCORE = 75
WARNING_SCORE = 45

# How much of a rule's category credit a triggered finding removes, by worst severity.
SEVERITY_PENALTY: dict[str, float] = {"critical": 1.0, "warning": 0.6, "notice": 0.25}

# A rule that enumerates every affected keyword or term is scored on the share of the
# subjects it checked that failed, never on the raw count: otherwise a location tracking
# many keywords is punished for tracking them, and every wide failure saturates to zero.
# A single failure still costs this floor share of the severity penalty.
ENUMERATED_FLOOR = 0.4

GRADES = (("excellent", 90), ("good", 75), ("fair", 50), ("poor", 0))


def severity_of(score: int) -> Severity:
    if score >= CRITICAL_SCORE:
        return "critical"
    return "warning" if score >= WARNING_SCORE else "notice"


def grade_of(score: int | None) -> str:
    if score is None:
        return "not_evaluated"
    return next(name for name, floor in GRADES if score >= floor)


def graded(base: int, magnitude: float, span: int, cap: int) -> int:
    """Scale a rule's floor score by how far past its threshold the finding sits.

    `magnitude` is a 0..1 fraction of the way from the trigger point to the point
    the policy treats as fully severe. Bands are policy, not calibrated risk.
    """
    return int(min(cap, base + round(span * max(0.0, min(1.0, magnitude)))))


# What each check looks at and what to do about it. Written once per rule so the UI can
# explain an issue type without repeating a finding's own evidence, and deliberately
# phrased as verification steps: none of these assert a ranking or revenue outcome.
#
# `unit` and `predicate` compose the one-line issue row: "<count> <unit(s)> <predicate>".
# The unit is what a single finding of that rule stands for - one keyword, one search
# term, or one location - so the count in the row is always countable by the reader.
# `predicate_one` is spelled out rather than derived, because guessing verb agreement
# from the plural silently mangles any rule phrased differently from the rest.
# `subject` names what the check actually counted - reviews, requests, keywords - which
# is not the same as `unit`, what one finding stands for. A check with no countable
# subject leaves it null and is reported as simply passing or failing.
RULE_DOCS: dict[str, dict[str, str]] = {
    "profile": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "has incomplete customer-facing information",
        "unit": "location",
        "predicate": "have incomplete customer-facing information",
        "label": "Incomplete customer-facing profile",
        "checks": "Whether a customer can phone, click through to a site, read a description, "
        "see opening hours, and whether the listing is verified.",
        "fix": "Confirm each missing field with the location manager and publish only "
        "confirmed information. Never invent a phone number, URL or description.",
    },
    "attributes": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "has unset category attributes",
        "unit": "location",
        "predicate": "have unset category attributes",
        "label": "Unset category attributes",
        "checks": "Attributes the category catalog offers that this location has neither "
        "enabled nor explicitly set to false.",
        "fix": "Ask the manager which services actually apply, then record true or false. "
        "An unset attribute is unknown, not absent, and enabling one that is not offered "
        "misleads customers.",
    },
    "reviews": {
        "subject_predicate": "rated 1-3 are unanswered",
        "subject": "review",
        "predicate_one": "has unanswered critical reviews",
        "unit": "location",
        "predicate": "have unanswered critical reviews",
        "label": "Unanswered critical reviews",
        "checks": "Reviews rated 1-3 in the recent window with no stored reply after the "
        "configured wait.",
        "fix": "Reply acknowledging the concern without disclosing customer details, and "
        "invite private follow-up. Investigate repeated themes internally.",
    },
    "booking_followup": {
        "subject_predicate": "are still marked new",
        "subject": "request",
        "predicate_one": "has appointment requests still marked new",
        "unit": "location",
        "predicate": "have appointment requests still marked new",
        "label": "Appointment requests still marked new",
        "checks": "Requests created in the recent window whose stored status is still new "
        "past the configured wait.",
        "fix": "Reconcile each request in the booking system first. A stale CRM status and a "
        "genuinely unhandled request look identical here, so confirm before contacting anyone.",
    },
    "booking_outcomes": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "has a high cancellation and no-show rate",
        "unit": "location",
        "predicate": "have high cancellation and no-show rates",
        "label": "Cancellations and no-shows",
        "checks": "The share of settled past appointments that were cancelled or did not "
        "happen, over the longer outcome window.",
        "fix": "Audit the flagged appointments and the reminder process with the manager. "
        "Read cancellation reasons before changing how reminders work.",
    },
    "performance": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "has falling impressions or action intensity",
        "unit": "location",
        "predicate": "have falling impressions or action intensity",
        "label": "Falling impressions or action intensity",
        "checks": "Two consecutive weekday-aligned windows of daily metrics, compared only "
        "on days observed in both.",
        "fix": "Review the affected dates and the device and surface split, then check "
        "listing accuracy, website and phone availability, and local demand.",
    },
    "search": {
        "subject_predicate": "lost visibility month over month",
        "subject": "search term",
        "predicate_one": "lost visibility month over month",
        "unit": "search term",
        "predicate": "lost visibility month over month",
        "label": "Lost search-term visibility",
        "checks": "The same search term in two consecutive complete months, where reporting "
        "was not truncated in either.",
        "fix": "Inspect the listing and the relevant website page for that term. Confirm the "
        "service is genuinely offered before changing copy or categories.",
    },
    "rankings": {
        "subject_predicate": "are outside the local pack",
        "subject": "keyword",
        "predicate_one": "is outside the local pack",
        "unit": "keyword",
        "predicate": "are outside the local pack",
        "label": "Outside the local pack",
        "checks": "Four consecutive weekly rank checks per tracked keyword, counting the "
        "weeks the listing was not in the local pack.",
        "fix": "Check the result URL and listing relevance for the keyword on the tracked "
        "device. Observed competitors are context, not an explanation of why they rank.",
    },
    "media": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "is missing profile imagery",
        "unit": "location",
        "predicate": "are missing profile imagery",
        "label": "Missing profile imagery",
        "checks": "Profile and cover image flags that the photo summary explicitly marks "
        "as missing.",
        "fix": "Source accurate, current imagery from the manager and review it before "
        "uploading. Photo counts say nothing about photo quality.",
    },
    "posts": {
        "subject_predicate": None,
        "subject": None,
        "predicate_one": "has no recent customer update",
        "unit": "location",
        "predicate": "have no recent customer update",
        "label": "No recent customer update",
        "checks": "Days since the most recent dated post, against the configured gap.",
        "fix": "Confirm the post history is complete, then publish only if there is real "
        "news, an event or an available offer. An incomplete export looks like a gap.",
    },
}
