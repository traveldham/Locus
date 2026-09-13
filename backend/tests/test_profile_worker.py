"""Profile worker: every check passes, fails, or abstains for the right reason.

Mutation tests: change one input, one verdict changes. Missing evidence abstains.
"""

from datetime import date

from app.services.recommendations.categories import profile
from app.services.recommendations.engine import analyze, run_worker
from app.services.recommendations.types import EngineConfig

AS_OF = date(2026, 9, 11)
LOC = "loc-1"

ACCESSIBILITY = (
    "wheelchair_accessible_entrance",
    "wheelchair_accessible_restroom",
    "wheelchair_accessible_seating",
    "wheelchair_accessible_parking",
    "hearing_loop",
)
OTHER = (
    "saturday_appointments",
    "pediatric_care",
    "orthodontic_care",
    "teeth_whitening",
    "free_parking",
    "wifi",
)


def attr(name, value, kind="BOOL"):
    return {
        "id": f"a-{name}",
        "location_id": LOC,
        "attribute_id": f"attributes/{name}",
        "value_type": kind,
        "values": [value],
    }


def complete() -> dict:
    """A profile that passes every check."""
    return {
        "locations": [
            {
                "id": LOC,
                "title": "Brightpath Dental",
                "source": "fixture",
                "primary_category_display": "Dentist",
                "locality": "Austin",
                "administrative_area": "TX",
                "postal_code": "78701",
                "region_code": "US",
                "latitude": 30.2,
                "longitude": -97.7,
                "phone_primary": "+1-512-555-0100",
                "website_uri": "https://example.org/austin",
                "description": (
                    "A family dentist in Austin offering general, cosmetic and emergency "
                    "care for adults and children. Routine cleaning, Invisalign consults "
                    "and teeth whitening, with same-day appointments and digital x-rays "
                    "in a calm, modern clinic near downtown. Most insurance accepted."
                ),
                "open_status": "open",
                "opening_date": "2015-03-01",
                "has_voice_of_merchant": True,
            }
        ],
        "categories": [
            {"id": "c0", "location_id": LOC, "display_name": "Dentist", "is_primary": True},
            {
                "id": "c1",
                "location_id": LOC,
                "display_name": "Pediatric dentist",
                "is_primary": False,
            },
            {
                "id": "c2",
                "location_id": LOC,
                "display_name": "Cosmetic dentist",
                "is_primary": False,
            },
            {
                "id": "c3",
                "location_id": LOC,
                "display_name": "Teeth whitening service",
                "is_primary": False,
            },
        ],
        "hours": [
            {
                "id": f"h-{d}",
                "location_id": LOC,
                "hours_type": "REGULAR",
                "open_day": d,
                "open_hour": 8,
                "open_minute": 0,
                "close_day": d,
                "close_hour": 17,
                "close_minute": 0,
            }
            for d in ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY")
        ],
        "attributes": [attr(n, True) for n in ACCESSIBILITY]
        + [
            attr("saturday_appointments", True),
            attr("pediatric_care", True),
            attr("teeth_whitening", True),
        ]
        + [attr(n, False) for n in ("orthodontic_care", "free_parking", "wifi")],
        "catalog": [
            {
                "id": f"cat-{n}",
                "attribute_name": n,
                "attribute_group": "accessibility" if n in ACCESSIBILITY else "services",
                "applies_to_category": "Dentist",
                "value_type": "bool",
            }
            for n in ACCESSIBILITY + OTHER
        ],
        "media": [
            {
                "id": "m1",
                "location_id": LOC,
                "has_profile_photo": True,
                "has_cover_photo": True,
            }
        ],
        "projects": [
            {
                "id": "p1",
                "name": "Brightpath Dental Group",
                "website_url": "https://example.org",
                "description": "Family dental group.",
                "services": ["Routine cleaning", "Kids checkup", "Teeth whitening"],
                "slug": "bdg",
                "status": "active",
            }
        ],
    }


def verdicts(snapshot, config=None):
    result = run_worker(snapshot, AS_OF, config or EngineConfig(), "profile")
    return {e["rule"]: e for e in result["evaluations"]}, result["items"]


def test_every_check_is_declared_and_assessed_exactly_once():
    states, items = verdicts(complete())
    assert set(states) == set(profile.CHECKS)
    assert all(v["state"] == "clear" for v in states.values()), {
        k: v["reason"] for k, v in states.items() if v["state"] != "clear"
    }
    assert items == []
    report = analyze(complete(), AS_OF)
    health = report["location"]["health"]
    # Other workers judge the same fixture on their own; only the profile category is
    # asserted here.
    profile_score = next(c for c in health["categories"] if c["category"] == "profile")
    assert profile_score["score"] == 100 and profile_score["checks_passed"] == len(profile.CHECKS)
    assert profile_score["checks_not_evaluated"] == 0


def test_permanently_closed_suppresses_everything():
    snapshot = complete()
    snapshot["locations"][0]["open_status"] = "closed_permanently"
    states, items = verdicts(snapshot)
    assert all(v["state"] == "suppressed" for v in states.values()) and items == []
    assert analyze(snapshot, AS_OF)["location"]["health"]["score"] is None


def test_missing_contact_fields_are_critical():
    snapshot = complete()
    loc = snapshot["locations"][0]
    loc["phone_primary"] = " "
    loc["website_uri"] = None
    states, items = verdicts(snapshot)
    assert states["phone_missing"]["state"] == "triggered"
    assert states["website_missing"]["state"] == "triggered"
    assert states["website_not_https"]["state"] == "insufficient_data"
    by_rule = {i["rule"]: i for i in items}
    assert by_rule["phone_missing"]["severity"] == "critical"
    assert by_rule["website_missing"]["severity"] == "critical"
    assert by_rule["phone_missing"]["evidence"][0]["row_ids"] == [LOC]


def test_http_website_is_a_notice():
    snapshot = complete()
    snapshot["locations"][0]["website_uri"] = "http://example.org"
    states, items = verdicts(snapshot)
    assert states["website_not_https"]["state"] == "triggered"
    assert next(i for i in items if i["rule"] == "website_not_https")["severity"] == "notice"


def test_street_line_only_required_from_google_sourced_profiles():
    snapshot = complete()
    assert verdicts(snapshot)[0]["address_incomplete"]["state"] == "clear"
    snapshot["locations"][0]["source"] = "google"
    states, _ = verdicts(snapshot)
    assert states["address_incomplete"]["state"] == "triggered"
    snapshot["locations"][0]["address_lines"] = ["1 Main St"]
    assert verdicts(snapshot)[0]["address_incomplete"]["state"] == "clear"
    snapshot["locations"][0]["postal_code"] = None
    assert "postal code" in verdicts(snapshot)[0]["address_incomplete"]["reason"]


def test_pin_and_opening_date():
    snapshot = complete()
    snapshot["locations"][0]["latitude"] = None
    snapshot["locations"][0]["opening_date"] = None
    states, _ = verdicts(snapshot)
    assert states["pin_missing"]["state"] == "triggered"
    assert states["opening_date_missing"]["state"] == "triggered"


def test_categories_missing_few_and_contradicted():
    snapshot = complete()
    snapshot["categories"] = []
    snapshot["locations"][0]["primary_category_display"] = None
    states, _ = verdicts(snapshot)
    assert states["primary_category_missing"]["state"] == "triggered"
    assert states["secondary_categories_few"]["state"] == "insufficient_data"
    assert states["category_attribute_mismatch"]["state"] == "insufficient_data"

    snapshot = complete()
    snapshot["categories"] = snapshot["categories"][:2]
    snapshot["projects"] = []
    states, items = verdicts(snapshot)
    assert states["secondary_categories_few"]["state"] == "triggered"
    assert (
        verdicts(snapshot, EngineConfig(min_additional_categories=1))[0][
            "secondary_categories_few"
        ]["state"]
        == "clear"
    )

    snapshot = complete()
    # Pediatric dentist listed, pediatric_care explicitly false: contradiction.
    for row in snapshot["attributes"]:
        if row["attribute_id"].endswith("pediatric_care"):
            row["values"] = [False]
    states, items = verdicts(snapshot)
    assert states["category_attribute_mismatch"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "category_attribute_mismatch")
    assert finding["subject"] == "Pediatric dentist" and len(finding["evidence"]) == 2
    # Unset is unknown, not a contradiction.
    snapshot["attributes"] = [
        r for r in snapshot["attributes"] if not r["attribute_id"].endswith("pediatric_care")
    ]
    # Teeth whitening is still checkable and agrees, so the check is clear.
    assert verdicts(snapshot)[0]["category_attribute_mismatch"]["state"] == "clear"
    snapshot["attributes"] = [
        r for r in snapshot["attributes"] if not r["attribute_id"].endswith("teeth_whitening")
    ]
    assert verdicts(snapshot)[0]["category_attribute_mismatch"]["state"] == "insufficient_data"


def test_verification_and_closure():
    snapshot = complete()
    snapshot["locations"][0]["has_voice_of_merchant"] = False
    states, items = verdicts(snapshot)
    assert states["unverified"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "unverified")
    assert finding["severity"] == "critical" and finding["confidence"] == "medium"
    snapshot["locations"][0]["source"] = "google"
    assert (
        next(i for i in verdicts(snapshot)[1] if i["rule"] == "unverified")["confidence"] == "high"
    )

    snapshot = complete()
    snapshot["locations"][0]["open_status"] = "closed_temporarily"
    assert verdicts(snapshot)[0]["temporarily_closed"]["state"] == "triggered"
    snapshot["locations"][0]["open_status"] = None
    assert verdicts(snapshot)[0]["temporarily_closed"]["state"] == "insufficient_data"


def test_description_missing_short_long_and_stuffed():
    snapshot = complete()
    snapshot["locations"][0]["description"] = None
    states, _ = verdicts(snapshot)
    assert states["description_missing"]["state"] == "triggered"
    for rule in ("description_short", "description_too_long", "description_keyword_stuffed"):
        assert states[rule]["state"] == "insufficient_data"

    snapshot["locations"][0]["description"] = (
        "Dentist in Austin offering gentle family care for everyone."
    )
    states, items = verdicts(snapshot)
    assert states["description_missing"]["state"] == "clear"
    assert states["description_short"]["state"] == "triggered"
    assert states["description_keyword_stuffed"]["state"] == "clear"
    assert (
        verdicts(snapshot, EngineConfig(description_min_chars=50))[0]["description_short"]["state"]
        == "clear"
    )

    snapshot["locations"][0]["description"] = "x " * 400
    assert verdicts(snapshot)[0]["description_too_long"]["state"] == "triggered"

    snapshot["locations"][0]["description"] = (
        "Dentist Austin dentist, the Austin dentist for Austin families. Dentist! " * 4
    )
    states, items = verdicts(snapshot)
    assert states["description_keyword_stuffed"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "description_keyword_stuffed")
    assert finding["evidence"][0]["values"]["repeated"]["dentist"] >= 4


def test_name_keyword_stuffing_heuristic():
    snapshot = complete()
    assert verdicts(snapshot)[0]["name_keyword_stuffed"]["state"] == "clear"
    # A branch suffix with a multi-word city is normal, not stuffing.
    snapshot["locations"][0]["locality"] = "Round Rock"
    snapshot["locations"][0]["title"] = "Brightpath Dental — Round Rock"
    assert verdicts(snapshot)[0]["name_keyword_stuffed"]["state"] == "clear"
    snapshot["locations"][0]["title"] = "Brightpath Dentist Round Rock"
    assert verdicts(snapshot)[0]["name_keyword_stuffed"]["state"] == "triggered"
    snapshot["locations"][0]["title"] = "Dentist Dentist Brightpath"
    assert verdicts(snapshot)[0]["name_keyword_stuffed"]["state"] == "triggered"
    snapshot["locations"][0]["title"] = ""
    assert verdicts(snapshot)[0]["name_keyword_stuffed"]["state"] == "insufficient_data"


def test_logo_and_cover_flags():
    snapshot = complete()
    snapshot["media"][0]["has_cover_photo"] = False
    snapshot["media"][0]["has_profile_photo"] = None
    states, _ = verdicts(snapshot)
    assert states["cover_photo_missing"]["state"] == "triggered"
    assert states["logo_missing"]["state"] == "insufficient_data"
    snapshot["media"] = []
    states, _ = verdicts(snapshot)
    assert states["logo_missing"]["state"] == "insufficient_data"
    assert states["cover_photo_missing"]["state"] == "insufficient_data"


def test_hours_missing_gaps_and_saturday_consistency():
    snapshot = complete()
    snapshot["hours"] = []
    states, items = verdicts(snapshot)
    assert states["hours_missing"]["state"] == "triggered"
    assert states["hours_weekday_gaps"]["state"] == "insufficient_data"
    assert states["saturday_hours_inconsistent"]["state"] == "insufficient_data"

    snapshot = complete()
    snapshot["hours"] = [
        h for h in snapshot["hours"] if h["open_day"] not in ("TUESDAY", "SATURDAY")
    ]
    states, items = verdicts(snapshot)
    assert states["hours_weekday_gaps"]["state"] == "triggered"
    assert states["hours_weekday_gaps"]["issues"] == 1
    assert states["hours_weekday_gaps"]["evaluated"] == 5
    gaps = [i for i in items if i["rule"] == "hours_weekday_gaps"]
    assert [g["subject"] for g in gaps] == ["Tuesday"]
    assert states["saturday_hours_inconsistent"]["state"] == "triggered"

    for row in snapshot["attributes"]:
        if row["attribute_id"].endswith("saturday_appointments"):
            row["values"] = [False]
    assert verdicts(snapshot)[0]["saturday_hours_inconsistent"]["state"] == "clear"
    snapshot["attributes"] = [
        r for r in snapshot["attributes"] if not r["attribute_id"].endswith("saturday_appointments")
    ]
    assert verdicts(snapshot)[0]["saturday_hours_inconsistent"]["state"] == "insufficient_data"


def test_attributes_sparse_and_accessibility():
    snapshot = complete()
    # Drop every answer except two: sparse, and accessibility unanswered.
    snapshot["attributes"] = [attr("saturday_appointments", True), attr("hearing_loop", False)]
    states, items = verdicts(snapshot)
    assert states["attributes_sparse"]["state"] == "triggered"
    assert states["attributes_sparse"]["issues"] == 9
    assert states["attributes_sparse"]["evaluated"] == 11
    assert states["accessibility_unanswered"]["state"] == "triggered"
    assert states["accessibility_unanswered"]["issues"] == 4
    subjects = sorted(i["subject"] for i in items if i["rule"] == "accessibility_unanswered")
    assert subjects == sorted(set(ACCESSIBILITY) - {"hearing_loop"})
    # An explicit no is an answer.
    assert "hearing_loop" not in subjects

    # Enum stored as strings still counts as answered and as true/false.
    snapshot = complete()
    for row in snapshot["attributes"]:
        row["values"] = ["TRUE" if row["values"] == [True] else "FALSE"]
        row["value_type"] = "ENUM"
    states, _ = verdicts(snapshot)
    assert states["attributes_sparse"]["state"] == "clear"
    assert states["accessibility_unanswered"]["state"] == "clear"
    assert states["saturday_hours_inconsistent"]["state"] == "clear"

    snapshot["catalog"] = []
    states, _ = verdicts(snapshot)
    assert states["attributes_sparse"]["state"] == "insufficient_data"
    assert states["accessibility_unanswered"]["state"] == "insufficient_data"


def test_score_falls_with_severity_and_findings_carry_evidence():
    snapshot = complete()
    snapshot["locations"][0]["phone_primary"] = None
    critical = analyze(snapshot, AS_OF)["location"]["health"]["score"]
    snapshot = complete()
    snapshot["locations"][0]["opening_date"] = None
    notice = analyze(snapshot, AS_OF)["location"]["health"]["score"]
    assert critical < notice < 100
    for item in run_worker(complete() | {"media": []}, AS_OF, EngineConfig(), "profile")["items"]:
        assert item["evidence"] and item["why"] and item["action"]


def test_services_versus_categories_and_attributes():
    snapshot = complete()
    states, _ = verdicts(snapshot)
    assert states["services_without_category"]["state"] == "clear"
    assert states["services_without_attribute"]["state"] == "clear"

    snapshot["projects"][0]["services"].append("Implant consult")
    states, items = verdicts(snapshot)
    assert states["services_without_category"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "services_without_category")
    assert finding["subject"] == "Implant consult"
    assert "Dental implants periodontist" in finding["why"]
    # implant_services is not in the catalog, so the attribute side cannot be judged.
    assert states["services_without_attribute"]["state"] == "clear"

    for row in snapshot["attributes"]:
        if row["attribute_id"].endswith("teeth_whitening"):
            row["values"] = [False]
    states, items = verdicts(snapshot)
    assert states["services_without_attribute"]["state"] == "triggered"
    assert next(i for i in items if i["rule"] == "services_without_attribute")["subject"] == (
        "Teeth whitening"
    )

    snapshot["projects"] = []
    states, _ = verdicts(snapshot)
    assert states["services_without_category"]["state"] == "insufficient_data"
    assert states["services_without_attribute"]["state"] == "insufficient_data"


def test_description_quality_needs_what_where_or_services():
    snapshot = complete()
    assert verdicts(snapshot)[0]["description_quality"]["state"] == "clear"
    snapshot["locations"][0]["description"] = (
        "We are a friendly practice that welcomes everyone and offers a comfortable "
        "experience with modern equipment, flexible appointments and gentle care for "
        "the whole family, every day of the week, with parking on site, a play corner "
        "for little ones, evening slots for busy households, and a warm team that takes "
        "time to explain every step before anything happens."
    )
    states, items = verdicts(snapshot)
    assert states["description_quality"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "description_quality")
    assert finding["evidence"][0]["values"]["says_what"] is False
    snapshot["locations"][0]["description"] = "short"
    assert verdicts(snapshot)[0]["description_quality"]["state"] == "insufficient_data"


def test_hours_plausibility_and_future_opening_date():
    snapshot = complete()
    assert verdicts(snapshot)[0]["hours_implausible"]["state"] == "clear"
    monday = next(h for h in snapshot["hours"] if h["open_day"] == "MONDAY")
    monday["close_hour"] = 7
    states, items = verdicts(snapshot)
    assert states["hours_implausible"]["state"] == "triggered"
    assert next(i for i in items if i["rule"] == "hours_implausible")["subject"] == "Monday"
    monday["close_hour"] = 23
    monday["open_hour"] = 5
    assert verdicts(snapshot)[0]["hours_implausible"]["state"] == "triggered"

    snapshot = complete()
    snapshot["locations"][0]["opening_date"] = "2030-01-01"
    assert verdicts(snapshot)[0]["opening_date_in_future"]["state"] == "triggered"
    snapshot["locations"][0]["opening_date"] = None
    assert verdicts(snapshot)[0]["opening_date_in_future"]["state"] == "insufficient_data"


def test_card_and_priorities_and_summary_fallback():
    from app.services.recommendations.categories import profile as worker
    from app.services.recommendations.suggestions.profile import fallback_summary

    card = worker.card(complete())
    assert card["name"] == "Brightpath Dental" and card["phone"] == "+1-512-555-0100"
    assert [h["day"] for h in card["hours"]][:2] == ["Monday", "Tuesday"]
    assert "pediatric_care" in card["attributes_yes"] and "wifi" in card["attributes_no"]

    snapshot = complete()
    snapshot["locations"][0]["phone_primary"] = None
    snapshot["locations"][0]["opening_date"] = None
    report = analyze(snapshot, AS_OF)
    location = report["location"]
    assert location["priorities"][0].endswith(":phone_missing")
    assert location["cards"]["profile"]["phone"] is None
    assert all(row["group"] and row["effort"] for row in location["by_rule"])
    summary = fallback_summary(run_worker(snapshot, AS_OF, EngineConfig(), "profile"))
    assert summary["source"] == "deterministic" and "Fix first" in summary["text"]
