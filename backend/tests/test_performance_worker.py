"""Performance worker: every check passes, fails, or abstains for the right reason.

Synthetic daily rows with a weekly cycle. Mutation tests: change one input, one
verdict changes. Missing days and NULL metrics abstain; they never invent a decline.
"""

from datetime import date, timedelta

from app.services.recommendations.categories import performance
from app.services.recommendations.engine import analyze, run_worker
from app.services.recommendations.types import EngineConfig

AS_OF = date(2026, 9, 14)
LATEST = date(2026, 9, 11)  # the sample export ends here; the audit runs three days later
LOC = "loc-1"
DAYS = 90

# A weekly cycle like the sample data: Saturday about half a weekday, Sunday a sixth.
WEEKDAY_FACTOR = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.45, 6: 0.15}


def daily(d: date, scale: float = 1.0, **overrides) -> dict:
    f = WEEKDAY_FACTOR[d.weekday()] * scale
    row = {
        "id": f"p-{d.isoformat()}",
        "location_id": LOC,
        "date": d.isoformat(),
        "impressions_maps_desktop": round(60 * f),
        "impressions_maps_mobile": round(240 * f),
        "impressions_search_desktop": round(70 * f),
        "impressions_search_mobile": round(280 * f),
        "website_clicks": round(30 * f),
        "call_clicks": round(25 * f),
        "direction_requests": round(20 * f),
        "conversations": round(4 * f),
        "bookings": round(6 * f),
    }
    row.update(overrides)
    return row


def steady(days: int = DAYS, latest: date = LATEST) -> dict:
    """A profile whose performance is flat: every check clears."""
    return {
        "locations": [
            {
                "id": LOC,
                "title": "Brightpath Dental",
                "source": "fixture",
                "primary_category_display": "Dentist",
                "locality": "Austin",
                "open_status": "open",
                "phone_primary": "+1-512-555-0100",
                "website_uri": "https://example.org/austin",
                "has_voice_of_merchant": True,
            }
        ],
        "performance": [daily(latest - timedelta(days=i)) for i in range(days)],
    }


def current_days(snapshot: dict, window: int = 28) -> list[dict]:
    start = LATEST - timedelta(days=window - 1)
    return [r for r in snapshot["performance"] if date.fromisoformat(r["date"]) >= start]


def scale_current(snapshot: dict, fields: tuple[str, ...], factor: float) -> None:
    for row in current_days(snapshot):
        for field in fields:
            row[field] = round(row[field] * factor)


def verdicts(snapshot, config=None, as_of=AS_OF):
    result = run_worker(snapshot, as_of, config or EngineConfig(), "performance")
    return {e["rule"]: e for e in result["evaluations"]}, result["items"]


def test_every_check_is_declared_and_assessed_exactly_once():
    states, items = verdicts(steady())
    assert set(states) == set(performance.CHECKS)
    assert all(v["state"] == "clear" for v in states.values()), {
        k: v["reason"] for k, v in states.items() if v["state"] != "clear"
    }
    assert items == []
    report = analyze(steady(), AS_OF)
    score = next(
        c for c in report["location"]["health"]["categories"] if c["category"] == "performance"
    )
    assert score["score"] == 100 and score["checks_passed"] == len(performance.CHECKS)
    assert score["checks_not_evaluated"] == 0
    assert "performance" in report["location"]["cards"]


def test_permanently_closed_suppresses_everything():
    snapshot = steady()
    snapshot["locations"][0]["open_status"] = "closed_permanently"
    states, items = verdicts(snapshot)
    assert all(v["state"] == "suppressed" for v in states.values()) and items == []


def test_no_rows_or_stale_data_abstains_instead_of_lying():
    states, _ = verdicts({**steady(), "performance": []})
    assert all(v["state"] == "insufficient_data" for v in states.values())
    # Data ends 2026-09-11; an audit a month later must not present it as current.
    states, items = verdicts(steady(), as_of=LATEST + timedelta(days=15))
    assert all(v["state"] == "insufficient_data" for v in states.values()) and items == []
    assert "15 days old" in states["impressions_decline"]["reason"]
    # Raising the freshness knob makes the same data usable again.
    states, _ = verdicts(
        steady(),
        EngineConfig(performance_max_stale_days=30),
        as_of=LATEST + timedelta(days=15),
    )
    assert states["impressions_decline"]["state"] == "clear"


def test_windows_anchor_on_the_last_data_day_not_the_audit_date():
    # Three days between data end and as-of: the current window is still 28 full days.
    states, _ = verdicts(steady())
    assert "28 of 28" in states["data_gaps"]["reason"]


def test_impressions_decline_is_graded_by_size():
    snapshot = steady()
    scale_current(snapshot, performance.IMPRESSIONS, 0.88)
    states, items = verdicts(snapshot)
    assert states["impressions_decline"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "impressions_decline")
    assert finding["severity"] == "notice"
    assert finding["evidence"][0]["values"]["paired_days"] == 28
    assert finding["evidence"][0]["values"]["current_end"] == LATEST.isoformat()
    # Actions scaled with impressions: the rate holds, so only impressions fire.
    assert states["action_rate_decline"]["state"] == "clear"

    snapshot = steady()
    scale_current(snapshot, performance.IMPRESSIONS + performance.ACTIONS, 0.6)
    states, items = verdicts(snapshot)
    finding = next(i for i in items if i["rule"] == "impressions_decline")
    assert finding["severity"] == "critical"
    assert {i["rule"] for i in items} >= {
        "impressions_decline",
        "calls_decline",
        "directions_decline",
        "website_clicks_decline",
    }


def test_a_rise_or_a_small_wobble_is_clear():
    snapshot = steady()
    scale_current(snapshot, performance.IMPRESSIONS, 1.3)
    assert verdicts(snapshot)[0]["impressions_decline"]["state"] == "clear"
    snapshot = steady()
    scale_current(snapshot, performance.IMPRESSIONS, 0.95)
    assert verdicts(snapshot)[0]["impressions_decline"]["state"] == "clear"
    # The floor is a knob.
    assert (
        verdicts(snapshot, EngineConfig(performance_impressions_decline=0.03))[0][
            "impressions_decline"
        ]["state"]
        == "triggered"
    )


def test_each_action_is_its_own_check():
    snapshot = steady()
    scale_current(snapshot, ("call_clicks",), 0.8)
    states, items = verdicts(snapshot)
    assert states["calls_decline"]["state"] == "triggered"
    assert states["directions_decline"]["state"] == "clear"
    assert states["website_clicks_decline"]["state"] == "clear"
    assert states["impressions_decline"]["state"] == "clear"
    finding = next(i for i in items if i["rule"] == "calls_decline")
    assert "calls" in finding["title"].lower() and finding["severity"] == "notice"
    assert finding["evidence"][0]["fields"] == ["date", "call_clicks"]
    # A steeper fall is graded up.
    snapshot = steady()
    scale_current(snapshot, ("call_clicks",), 0.65)
    _, items = verdicts(snapshot)
    assert next(i for i in items if i["rule"] == "calls_decline")["severity"] == "warning"


def test_action_rate_decline_fires_when_impressions_hold_and_every_action_slips():
    snapshot = steady()
    scale_current(snapshot, performance.ACTIONS, 0.8)
    states, items = verdicts(snapshot)
    assert states["action_rate_decline"]["state"] == "triggered"
    assert states["impressions_decline"]["state"] == "clear"
    finding = next(i for i in items if i["rule"] == "action_rate_decline")
    assert (
        finding["evidence"][0]["values"]["previous_rate"]
        > finding["evidence"][0]["values"]["current_rate"]
    )


def test_weekend_mix_does_not_fake_a_decline():
    # Pairing by weekday: a window with the same days compares equal even though
    # weekend days are a fraction of weekdays.
    states, _ = verdicts(steady(days=56))
    assert states["impressions_decline"]["state"] == "clear"


def test_missing_days_are_dropped_from_both_windows_never_zero():
    snapshot = steady()
    # Five missing days would read as an 18% fall if summed as zero.
    dropped = {(LATEST - timedelta(days=i)).isoformat() for i in (1, 3, 5, 7, 9)}
    snapshot["performance"] = [r for r in snapshot["performance"] if r["date"] not in dropped]
    states, items = verdicts(snapshot)
    assert states["impressions_decline"]["state"] == "clear"
    assert states["calls_decline"]["state"] == "clear"
    assert states["data_gaps"]["state"] == "triggered"
    gap = next(i for i in items if i["rule"] == "data_gaps")
    assert gap["severity"] == "notice" and len(gap["evidence"][0]["values"]["missing_days"]) == 5
    # Too few paired days: abstain, not a verdict. The latest day stays so the
    # window anchor does not move.
    dropped = {(LATEST - timedelta(days=i)).isoformat() for i in range(2, 28, 2)}
    snapshot["performance"] = [r for r in snapshot["performance"] if r["date"] not in dropped]
    states, _ = verdicts(snapshot)
    assert states["impressions_decline"]["state"] == "insufficient_data"
    assert "in both windows" in states["impressions_decline"]["reason"]
    # A gap in the previous window drops the pair too, and is not a current-window gap.
    snapshot = steady()
    snapshot["performance"] = [
        r for r in snapshot["performance"] if r["date"] != (LATEST - timedelta(days=30)).isoformat()
    ]
    states, _ = verdicts(snapshot)
    assert states["impressions_decline"]["state"] == "clear"
    assert states["data_gaps"]["state"] == "clear"


def test_null_metric_is_unknown_not_zero():
    snapshot = steady()
    for row in current_days(snapshot):
        row["call_clicks"] = None
    states, _ = verdicts(snapshot)
    assert states["calls_decline"]["state"] == "insufficient_data"
    assert states["impressions_decline"]["state"] == "clear"
    assert states["directions_decline"]["state"] == "clear"
    # A NULL action in the current window cannot count as a zero-action day either.
    assert states["zero_action_days"]["state"] == "insufficient_data"
    # A few NULLs drop those days for that metric only.
    snapshot = steady()
    for row in current_days(snapshot)[:3]:
        row["impressions_maps_mobile"] = None
    states, _ = verdicts(snapshot)
    assert states["impressions_decline"]["state"] == "clear"
    assert states["calls_decline"]["state"] == "clear"


def test_thin_volume_abstains():
    snapshot = steady()
    for row in snapshot["performance"]:
        for field in performance.IMPRESSIONS:
            row[field] = 1
        row["call_clicks"] = 0
    states, _ = verdicts(snapshot)
    assert states["impressions_decline"]["state"] == "insufficient_data"
    assert states["calls_decline"]["state"] == "insufficient_data"
    assert states["action_rate_decline"]["state"] == "insufficient_data"
    assert states["surface_split_shift"]["state"] == "insufficient_data"


def test_surface_and_mobile_shares():
    snapshot = steady()
    for row in current_days(snapshot):
        moved = row["impressions_search_mobile"] // 2
        row["impressions_search_mobile"] -= moved
        row["impressions_maps_mobile"] += moved
    states, items = verdicts(snapshot)
    assert states["surface_split_shift"]["state"] == "triggered"
    assert states["mobile_share_shift"]["state"] == "clear"
    assert states["impressions_decline"]["state"] == "clear"
    finding = next(i for i in items if i["rule"] == "surface_split_shift")
    assert finding["severity"] == "notice" and "Maps" in finding["title"]

    snapshot = steady()
    for row in current_days(snapshot):
        moved = row["impressions_search_mobile"] // 2
        row["impressions_search_mobile"] -= moved
        row["impressions_search_desktop"] += moved
    states, _ = verdicts(snapshot)
    assert states["mobile_share_shift"]["state"] == "triggered"
    assert states["surface_split_shift"]["state"] == "clear"


def test_zero_action_streak_needs_impressions_and_reported_zeros():
    snapshot = steady()
    for row in current_days(snapshot)[-4:]:
        for field in performance.ACTIONS:
            row[field] = 0
    states, items = verdicts(snapshot)
    assert states["zero_action_days"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "zero_action_days")
    assert finding["severity"] == "warning" and "4 days" in finding["title"]
    assert finding["evidence"][0]["values"]["streak_days"] == 4
    # Two zero days, a normal day, two zero days: no streak of three.
    snapshot = steady()
    for i in (0, 1, 3, 4):
        for field in performance.ACTIONS:
            current_days(snapshot)[-1 - i][field] = 0
    assert verdicts(snapshot)[0]["zero_action_days"]["state"] == "clear"
    # Zero actions on days the profile was barely shown is not a signal.
    snapshot = steady()
    for row in current_days(snapshot)[-4:]:
        for field in performance.ACTIONS:
            row[field] = 0
        for field in performance.IMPRESSIONS:
            row[field] = 2
    assert verdicts(snapshot)[0]["zero_action_days"]["state"] == "clear"
    # The streak length is a knob.
    snapshot = steady()
    for row in current_days(snapshot)[-2:]:
        for field in performance.ACTIONS:
            row[field] = 0
    assert verdicts(snapshot)[0]["zero_action_days"]["state"] == "clear"
    assert (
        verdicts(snapshot, EngineConfig(performance_zero_action_streak_days=2))[0][
            "zero_action_days"
        ]["state"]
        == "triggered"
    )


def test_card_reports_windows_deltas_and_weekly_series():
    snapshot = steady()
    scale_current(snapshot, ("call_clicks",), 0.5)
    visual = performance.card(snapshot)
    assert visual["window"]["current_end"] == LATEST.isoformat()
    assert visual["window"]["previous_end"] == (LATEST - timedelta(days=28)).isoformat()
    assert visual["days_with_data"] == 28
    metrics = visual["metrics"]
    assert metrics["impressions"]["change"] == 0.0
    assert metrics["calls"]["change"] < -0.4
    assert (
        metrics["impressions_maps"]["current"] + metrics["impressions_search"]["current"]
        == (metrics["impressions"]["current"])
    )
    assert 0.44 < visual["maps_share"] < 0.47 and 0.79 < visual["mobile_share"] < 0.81
    assert metrics["action_rate"]["current"] < metrics["action_rate"]["previous"]
    assert len(visual["weekly_impressions"]) == 12
    assert visual["weekly_impressions"][-1]["end"] == LATEST.isoformat()
    assert all(w["days"] == 7 for w in visual["weekly_impressions"])
    # Missing days lower the day count instead of reading as zero.
    gone = {(LATEST - timedelta(days=i)).isoformat() for i in (1, 2, 3)}
    snapshot["performance"] = [r for r in snapshot["performance"] if r["date"] not in gone]
    visual = performance.card(snapshot)
    assert visual["days_with_data"] == 25
    assert visual["weekly_impressions"][-1]["days"] == 4
    # An empty profile gives an empty card, not a crash.
    empty = performance.card({**snapshot, "performance": []})
    assert empty["window"] is None and empty["metrics"] == {}
