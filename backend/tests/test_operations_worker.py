"""Operations worker: every check passes, fails, or abstains for the right reason.

Mutation tests: change one input, one verdict changes. Missing evidence abstains.
"""

from datetime import date, timedelta

from app.services.recommendations.categories import operations
from app.services.recommendations.engine import run_worker
from app.services.recommendations.scoring import score_location
from app.services.recommendations.types import EngineConfig

AS_OF = date(2026, 9, 11)
LOC = "loc-1"
CHANNELS = ("website", "google_profile", "phone", "walk_in")
SERVICES = ("Routine cleaning", "Teeth whitening", "Kids checkup", "Implant consult")


def booking(n: int, status: str, made_days_ago: int, lead: int, **overrides) -> dict:
    made = AS_OF - timedelta(days=made_days_ago)
    row = {
        "id": f"b-{n}",
        "location_id": LOC,
        "external_booking_id": f"BK-{n:04d}",
        "service": SERVICES[n % len(SERVICES)],
        "requested_for_date": str(made + timedelta(days=lead)),
        "status": status,
        "booking_source": CHANNELS[n % len(CHANNELS)],
        "booking_created_at": f"{made} 09:00:00+00:00",
        "source": "locus",
    }
    row.update(overrides)
    return row


def weekday_lead(made_days_ago: int, lead: int) -> int:
    """A lead that lands the requested date on a weekday."""
    wanted = AS_OF - timedelta(days=made_days_ago) + timedelta(days=lead)
    while wanted.weekday() >= 5:
        wanted += timedelta(days=1)
    return (wanted - (AS_OF - timedelta(days=made_days_ago))).days


def healthy_bookings() -> list[dict]:
    """Forty requests over 80 days: answered, mostly kept, weekday, every channel."""
    rows = []
    n = 0
    # Settled, older visits: 18 completed, 2 cancelled, 1 no-show.
    for i in range(21):
        status = "completed" if i < 18 else ("cancelled" if i < 20 else "no_show")
        made = 80 - i * 2
        rows.append(booking(n, status, made, weekday_lead(made, 10)))
        n += 1
    # Confirmed future visits.
    for i in range(16):
        made = 20 - i
        rows.append(booking(n, "confirmed", made, weekday_lead(made, 10)))
        n += 1
    # Fresh requests still within the wait.
    for i in range(3):
        rows.append(booking(n, "new", i, weekday_lead(i, 10)))
        n += 1
    return rows


def complete() -> dict:
    """A location whose operations pass every check."""
    return {
        "locations": [
            {
                "id": LOC,
                "title": "Brightpath Dental",
                "source": "fixture",
                "primary_category_display": "Dentist",
                "locality": "Austin",
                "open_status": "open",
            }
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
            for d in ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
        ],
        "bookings": healthy_bookings(),
        "performance": [
            {
                "id": f"p-{i}",
                "location_id": LOC,
                "date": str(AS_OF - timedelta(days=i)),
                "bookings": 1 if i % 7 == 0 else 0,
                "conversations": 0,
            }
            for i in range(60)
        ],
        "projects": [
            {
                "id": "p1",
                "name": "Brightpath Dental Group",
                "website_url": "https://example.org",
                "description": "Family dental group.",
                "services": list(SERVICES),
                "slug": "bdg",
                "status": "active",
            }
        ],
    }


def verdicts(snapshot, config=None):
    result = run_worker(snapshot, AS_OF, config or EngineConfig(), "operations")
    return {e["rule"]: e for e in result["evaluations"]}, result["items"]


def category_score(snapshot) -> dict:
    result = run_worker(snapshot, AS_OF, EngineConfig(), "operations")
    health = score_location(result["evaluations"], result["items"]).model_dump()
    return next(c for c in health["categories"] if c["category"] == "operations")


def test_every_check_is_declared_and_assessed_exactly_once():
    states, items = verdicts(complete())
    assert set(states) == set(operations.CHECKS)
    assert all(v["state"] == "clear" for v in states.values()), {
        k: v["reason"] for k, v in states.items() if v["state"] != "clear"
    }
    assert items == []
    score = category_score(complete())
    assert score["score"] == 100 and score["checks_passed"] == len(operations.CHECKS)
    assert score["checks_not_evaluated"] == 0


def test_permanently_closed_suppresses_and_no_requests_abstains():
    snapshot = complete()
    snapshot["locations"][0]["open_status"] = "closed_permanently"
    states, items = verdicts(snapshot)
    assert all(v["state"] == "suppressed" for v in states.values()) and items == []

    snapshot = complete()
    snapshot["bookings"] = []
    states, items = verdicts(snapshot)
    assert all(v["state"] == "insufficient_data" for v in states.values()) and items == []
    assert category_score(snapshot)["score"] is None


def test_stale_new_requests_are_enumerated_by_booking_id_without_names():
    snapshot = complete()
    snapshot["bookings"][-1] = booking(99, "new", 30, 10, service="Root canal")
    snapshot["bookings"][-2] = booking(98, "new", 6, 10)
    states, items = verdicts(snapshot)
    assert states["requests_unanswered"]["state"] == "triggered"
    assert states["requests_unanswered"]["issues"] == 2
    findings = [i for i in items if i["rule"] == "requests_unanswered"]
    assert [f["subject"] for f in findings] == ["BK-0099", "BK-0098"]  # oldest first
    assert findings[0]["severity"] == "critical" and findings[1]["severity"] == "warning"
    assert "Root canal" in findings[0]["why"]
    assert findings[0]["evidence"][0]["row_ids"] == ["b-99"]
    assert "customer_name" not in str(findings)
    # The wait is a policy knob.
    assert (
        verdicts(snapshot, EngineConfig(booking_wait_days=30))[0]["requests_unanswered"]["state"]
        == "clear"
    )


def test_new_requests_past_their_date_fire_expired():
    snapshot = complete()
    assert verdicts(snapshot)[0]["requests_expired"]["state"] == "clear"
    snapshot["bookings"][-1] = booking(99, "new", 20, 5)
    states, items = verdicts(snapshot)
    assert states["requests_expired"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "requests_expired")
    assert finding["evidence"][0]["values"]["expired"] == 1
    # A new request for a future date is not expired.
    snapshot["bookings"][-1] = booking(99, "new", 1, 5)
    assert verdicts(snapshot)[0]["requests_expired"]["state"] == "clear"


def test_confirmation_rate_and_its_floor():
    snapshot = complete()
    for row in snapshot["bookings"][:12]:
        row["status"] = "cancelled"
    for row in snapshot["bookings"][21:30]:
        row["status"] = "new"
    states, items = verdicts(snapshot)
    assert states["confirmation_rate_low"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "confirmation_rate_low")
    assert finding["evidence"][0]["values"]["rate"] < 0.7
    assert (
        verdicts(snapshot, EngineConfig(booking_confirmation_min=0.3))[0]["confirmation_rate_low"][
            "state"
        ]
        == "clear"
    )
    snapshot["bookings"] = snapshot["bookings"][-5:]
    assert verdicts(snapshot)[0]["confirmation_rate_low"]["state"] == "insufficient_data"


def test_cancellation_and_no_show_rates_use_settled_visits_only():
    snapshot = complete()
    for row in snapshot["bookings"][:8]:
        row["status"] = "cancelled"
    states, items = verdicts(snapshot)
    assert states["cancellation_rate_high"]["state"] == "triggered"
    assert states["no_show_rate_high"]["state"] == "clear"
    finding = next(i for i in items if i["rule"] == "cancellation_rate_high")
    assert finding["evidence"][0]["values"]["settled"] == 21

    snapshot = complete()
    for row in snapshot["bookings"][:5]:
        row["status"] = "no_show"
    states, items = verdicts(snapshot)
    assert states["no_show_rate_high"]["state"] == "triggered"
    assert next(i for i in items if i["rule"] == "no_show_rate_high")["severity"] == "warning"
    # Confirmed visits never count as settled, so the denominator stays honest.
    for row in snapshot["bookings"][:21]:
        row["status"] = "confirmed"
    states, _ = verdicts(snapshot)
    assert states["cancellation_rate_high"]["state"] == "insufficient_data"
    assert states["no_show_rate_high"]["state"] == "insufficient_data"


def test_requested_service_not_on_project_list():
    snapshot = complete()
    snapshot["bookings"][0]["service"] = "Emergency visit"
    snapshot["bookings"][1]["service"] = "Emergency visit"
    snapshot["bookings"][2]["service"] = "Whitening"  # shares a word: listed
    states, items = verdicts(snapshot)
    assert states["service_not_listed"]["state"] == "triggered"
    findings = [i for i in items if i["rule"] == "service_not_listed"]
    assert [f["subject"] for f in findings] == ["Emergency visit"]
    assert findings[0]["evidence"][0]["values"]["requests"] == 2
    snapshot["projects"] = []
    assert verdicts(snapshot)[0]["service_not_listed"]["state"] == "insufficient_data"


def test_weekend_demand_needs_hours_and_a_floor():
    snapshot = complete()
    saturday = AS_OF + timedelta(days=(5 - AS_OF.weekday()) % 7 or 7)
    for row in snapshot["bookings"][21:27]:
        row["requested_for_date"] = str(saturday)
    states, items = verdicts(snapshot)
    assert states["weekend_demand_without_hours"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "weekend_demand_without_hours")
    assert finding["subject"] == "Saturday" and len(finding["evidence"]) == 2
    snapshot["hours"].append({**snapshot["hours"][0], "id": "h-SAT", "open_day": "SATURDAY"})
    assert verdicts(snapshot)[0]["weekend_demand_without_hours"]["state"] == "clear"
    snapshot["hours"] = []
    assert verdicts(snapshot)[0]["weekend_demand_without_hours"]["state"] == "insufficient_data"
    snapshot = complete()
    snapshot["bookings"][21]["requested_for_date"] = str(saturday)
    # Below the floor there is no demand to miss, so the check passes.
    assert verdicts(snapshot)[0]["weekend_demand_without_hours"]["state"] == "clear"


def test_lead_time_collapse():
    snapshot = complete()
    for row in snapshot["bookings"]:
        made = date.fromisoformat(row["booking_created_at"][:10])
        if (AS_OF - made).days < 28:
            row["requested_for_date"] = str(made + timedelta(days=1))
    states, items = verdicts(snapshot)
    assert states["lead_time_shrinking"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "lead_time_shrinking")
    assert finding["severity"] == "notice"
    assert finding["evidence"][0]["values"]["recent_median"] < 5
    snapshot["bookings"] = snapshot["bookings"][:21]
    assert verdicts(snapshot)[0]["lead_time_shrinking"]["state"] == "insufficient_data"


def test_channel_concentration_and_unknown_channels():
    snapshot = complete()
    for row in snapshot["bookings"]:
        row["booking_source"] = "phone"
    states, items = verdicts(snapshot)
    assert states["channel_concentrated"]["state"] == "triggered"
    assert "phone" in next(i for i in items if i["rule"] == "channel_concentrated")["title"]
    for row in snapshot["bookings"]:
        row["booking_source"] = None
    assert verdicts(snapshot)[0]["channel_concentrated"]["state"] == "insufficient_data"


def test_google_bookings_zero_is_a_tracking_gap_and_null_is_unknown():
    snapshot = complete()
    for row in snapshot["performance"]:
        row["bookings"] = 0
    states, items = verdicts(snapshot)
    assert states["google_bookings_untracked"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "google_bookings_untracked")
    assert finding["severity"] == "notice" and len(finding["evidence"]) == 2
    for row in snapshot["performance"]:
        row["bookings"] = None
    assert verdicts(snapshot)[0]["google_bookings_untracked"]["state"] == "insufficient_data"


def test_card_summarises_the_funnel_without_names():
    snapshot = complete()
    snapshot["bookings"][-1] = booking(99, "new", 30, 10, customer_name="Should Not Leak")
    card = operations.card(snapshot)
    assert card["requests"] == 40
    assert card["funnel"]["completed"] == 18 and card["funnel"]["new"] == 3
    assert card["cancellation_rate"] == round(2 / 21, 3)
    assert card["no_show_rate"] == round(1 / 21, 3)
    assert card["oldest_new_age_days"] == 30
    assert card["median_lead_days"] and card["median_lead_days"] >= 10
    assert {c["channel"] for c in card["channels"]} == {
        "website",
        "Google profile",
        "phone",
        "walk-in",
    }
    assert card["services"][0]["requests"] >= 9
    assert "Should Not Leak" not in str(card)
    assert operations.card({"locations": snapshot["locations"], "bookings": []})["requests"] == 0
