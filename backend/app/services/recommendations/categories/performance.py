"""Performance worker: are impressions and customer actions holding up?

Every check is a comparison of two equal windows of daily Google Performance data,
paired day by day with the same weekday one window earlier, so a weekend never
masquerades as a decline. Every check is deterministic.

Semantics that matter:

- A missing day is unknown, not zero. It is dropped from both windows, pair and all.
- A NULL metric is unknown, not zero. Each metric pairs on its own.
- Windows end on the last day with data on or before as-of, never on as-of itself,
  so a partial trailing window cannot read as a fall. Data older than the freshness
  knob abstains everything rather than reporting a stale comparison as current.
- Actions are events, not customers. An action rate is engagement, not conversion.
- A finding is a descriptive change. The investigation plan drafted afterwards by the
  suggestion layer is a checklist, never a cause.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from app.services.recommendations.grading import graded
from app.services.recommendations.values import day, number

if TYPE_CHECKING:
    from app.services.recommendations.context import Context

KEY = "performance"
LABEL = "Performance"
WEIGHT = 10

MAPS = ("impressions_maps_desktop", "impressions_maps_mobile")
SEARCH = ("impressions_search_desktop", "impressions_search_mobile")
MOBILE = ("impressions_maps_mobile", "impressions_search_mobile")
IMPRESSIONS = MAPS + SEARCH
ACTIONS = ("call_clicks", "direction_requests", "website_clicks")
HREF = "/insights/performance"


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
    group: str = "trend",
    effort: str = "hour",
) -> dict:
    return {
        "weight": weight,
        # Which group the check belongs to: trend, mix, coverage.
        "group": group,
        # How long the investigation usually takes: minutes, hour, afternoon.
        "effort": effort,
        "label": label,
        "checks": checks,
        "fix": fix,
        "unit": unit,
        "predicate": predicate,
        "predicate_one": predicate_one,
        "subject": subject,
        "subject_predicate": subject_predicate,
        # What the suggestion layer may draft: an ordered investigation plan.
        "suggests": suggests,
    }


CHECKS: dict[str, dict] = {
    # Trend
    "impressions_decline": check(
        3,
        "Impressions fell",
        "Total profile impressions across Maps and Search in the last four weeks against "
        "the four weeks before, paired by weekday.",
        "Check the profile state first: suspension, temporary closure, changed hours or "
        "category. Then look for a new competitor on the main searches. Compare with "
        "nearby locations to rule out seasonal demand.",
        predicate="show fewer impressions",
        predicate_one="shows fewer impressions",
        suggests="investigation_plan",
    ),
    "calls_decline": check(
        2,
        "Calls fell",
        "Call button taps in the last four weeks against the four weeks before, paired by weekday.",
        "Confirm the phone number on the profile still rings through and was not swapped "
        "for a tracking or call-centre number. Check whether hours or the call button "
        "changed. Compare with impressions: calls falling alone points at the number.",
        predicate="show fewer calls",
        predicate_one="shows fewer calls",
        suggests="investigation_plan",
    ),
    "directions_decline": check(
        2,
        "Direction requests fell",
        "Direction requests in the last four weeks against the four weeks before, paired "
        "by weekday.",
        "Confirm the address and map pin have not moved and the profile is not marked "
        "closed. Directions falling alone often follows a pin or address edit.",
        predicate="show fewer direction requests",
        predicate_one="shows fewer direction requests",
        suggests="investigation_plan",
    ),
    "website_clicks_decline": check(
        2,
        "Website clicks fell",
        "Website button clicks in the last four weeks against the four weeks before, "
        "paired by weekday.",
        "Open the stored website link on a phone and confirm it loads and is the right "
        "page. Check whether the link was changed or redirected. Clicks falling while "
        "impressions hold points at the link or the page.",
        predicate="show fewer website clicks",
        predicate_one="shows fewer website clicks",
        suggests="investigation_plan",
    ),
    "action_rate_decline": check(
        2,
        "Fewer actions per impression",
        "Calls, directions and website clicks per impression in the last four weeks "
        "against the four weeks before.",
        "The profile is still shown but fewer people act on it. Review what a customer "
        "sees first: rating, photos, hours, and whether the call and website buttons "
        "are present. Compare with impressions to see if the mix of searches changed.",
        predicate="convert fewer impressions to actions",
        predicate_one="converts fewer impressions to actions",
        suggests="investigation_plan",
    ),
    # Mix
    "surface_split_shift": check(
        1,
        "Maps versus Search mix shifted",
        "The share of impressions from Maps against Search, last four weeks versus the "
        "four weeks before.",
        "A mix shift means Google is matching the profile differently. Check for a "
        "changed category, name or pin, and whether a competitor now takes the branded "
        "search. Not a problem in itself.",
        predicate="show a shifted Maps and Search mix",
        predicate_one="shows a shifted Maps and Search mix",
        suggests="investigation_plan",
        group="mix",
    ),
    "mobile_share_shift": check(
        1,
        "Mobile share shifted",
        "The share of impressions from mobile devices, last four weeks versus the four "
        "weeks before.",
        "A mobile share change with flat totals usually tracks a Google interface "
        "change. If totals moved too, check the profile on a phone: hours, buttons and "
        "photos as a customer sees them.",
        predicate="show a shifted mobile share",
        predicate_one="shows a shifted mobile share",
        group="mix",
    ),
    # Coverage
    "zero_action_days": check(
        2,
        "Days shown with no actions",
        "Consecutive days in the last four weeks where the profile was shown but calls, "
        "directions and website clicks were all reported as zero.",
        "Being shown with nobody acting for days in a row usually means the buttons are "
        "gone: a missing phone or website, a closure flag, or a suspension. Check the "
        "profile as a customer sees it on those dates.",
        predicate="have days shown with no actions",
        predicate_one="has days shown with no actions",
        suggests="investigation_plan",
        group="coverage",
    ),
    "data_gaps": check(
        1,
        "Missing days in the data",
        "Calendar days in the last four weeks with no performance row.",
        "Re-sync performance data for the missing days. Trend checks skip missing days "
        "rather than counting them as zero, so gaps lower confidence rather than scores.",
        predicate="have missing days",
        predicate_one="has missing days",
        group="coverage",
        effort="minutes",
    ),
}

GROUPS = {
    "trend": (
        "impressions_decline",
        "calls_decline",
        "directions_decline",
        "website_clicks_decline",
        "action_rate_decline",
    ),
    "mix": ("surface_split_shift", "mobile_share_shift"),
    "coverage": ("zero_action_days", "data_gaps"),
}
GROUP_LABELS = {"trend": "Trend", "mix": "Mix", "coverage": "Coverage"}
EFFORT = {
    "minutes": ("data_gaps", "mobile_share_shift"),
    "hour": (
        "calls_decline",
        "directions_decline",
        "website_clicks_decline",
        "surface_split_shift",
        "zero_action_days",
    ),
    "afternoon": ("impressions_decline", "action_rate_decline"),
}
for _group, _rules in GROUPS.items():
    for _rule in _rules:
        CHECKS[_rule]["group"] = _group
for _effort, _rules in EFFORT.items():
    for _rule in _rules:
        CHECKS[_rule]["effort"] = _effort
assert {r for rules in GROUPS.values() for r in rules} == set(CHECKS)
assert {r for rules in EFFORT.values() for r in rules} == set(CHECKS)

TREND_RULES = GROUPS["trend"] + GROUPS["mix"] + ("zero_action_days",)
ACTION_RULES = {
    "calls_decline": ("call_clicks", "calls"),
    "directions_decline": ("direction_requests", "direction requests"),
    "website_clicks_decline": ("website_clicks", "website clicks"),
}


# ---- windows and pairing ---------------------------------------------------------


def by_date(rows: list[dict]) -> dict[date, dict]:
    """One row per day. A later duplicate wins, which the unique constraint prevents."""
    out: dict[date, dict] = {}
    for row in rows:
        d = day(row.get("date"))
        if d is not None:
            out[d] = row
    return out


def anchor(dates: dict[date, dict], as_of: date) -> date | None:
    """The last day with data on or before as-of. Windows end here, not at as-of."""
    past = [d for d in dates if d <= as_of]
    return max(past) if past else None


def windows(end: date, length: int) -> tuple[tuple[date, date], tuple[date, date]]:
    current = (end - timedelta(days=length - 1), end)
    previous = (current[0] - timedelta(days=length), current[0] - timedelta(days=1))
    return current, previous


def total(row: dict | None, fields: tuple[str, ...]) -> int | None:
    """Sum of the fields when every one is a number; None when any is unknown."""
    if row is None:
        return None
    values = [row.get(f) for f in fields]
    if not all(number(v) for v in values):
        return None
    return int(sum(values))


def pairs(
    dates: dict[date, dict], end: date, length: int, fields: tuple[str, ...]
) -> list[tuple[date, int, int]]:
    """(current day, current value, previous value) for every day both windows report."""
    out = []
    for offset in range(length):
        d = end - timedelta(days=offset)
        now, before = (
            total(dates.get(d), fields),
            total(dates.get(d - timedelta(days=length)), fields),
        )
        if now is not None and before is not None:
            out.append((d, now, before))
    return sorted(out)


def change(now: int, before: int) -> float | None:
    return None if before <= 0 else (now - before) / before


def share(part: int, whole: int) -> float | None:
    return None if whole <= 0 else part / whole


# ---- evaluate --------------------------------------------------------------------


def evaluate(c: Context) -> None:
    loc = c.location
    if loc.get("open_status") == "closed_permanently":
        for rule in CHECKS:
            c.assess(rule, "suppressed", "Permanently closed: performance is not audited.")
        return

    rows = c.rows("performance")
    dates = by_date(rows)
    end = anchor(dates, c.as_of)
    if end is None:
        for rule in CHECKS:
            c.assess(rule, "insufficient_data", "No performance rows on or before the audit date.")
        return

    age = (c.as_of - end).days
    if age > c.config.performance_max_stale_days:
        for rule in CHECKS:
            c.assess(
                rule,
                "insufficient_data",
                f"Newest performance data is {age} days old, past the "
                f"{c.config.performance_max_stale_days}-day freshness limit.",
            )
        return

    length = c.config.performance_window_days
    current, previous = windows(end, length)
    span = {
        "current_start": current[0].isoformat(),
        "current_end": current[1].isoformat(),
        "previous_start": previous[0].isoformat(),
        "previous_end": previous[1].isoformat(),
        "window_days": length,
        "data_age_days": age,
    }
    in_current = [dates[d] for d in dates if current[0] <= d <= current[1]]
    in_both = [dates[d] for d in dates if previous[0] <= d <= current[1]]

    _impressions(c, dates, end, length, in_both, span)
    _actions(c, dates, end, length, in_both, span)
    _rate(c, dates, end, length, in_both, span)
    _mix(c, dates, end, length, in_both, span)
    _zero_days(c, dates, current, in_current, span)
    _gaps(c, dates, current, in_current, span)


def _enough(c: Context, rule: str, paired: list, name: str) -> bool:
    """The paired-day floor. Records the abstention itself when it fails."""
    need = c.config.performance_min_paired_share
    length = c.config.performance_window_days
    if len(paired) / length < need:
        c.assess(
            rule,
            "insufficient_data",
            f"Only {len(paired)} of {length} days report {name} in both windows; "
            f"{need:.0%} are needed.",
        )
        return False
    return True


def _decline_finding(
    c: Context,
    rule: str,
    title: str,
    name: str,
    now: int,
    before: int,
    fell: float,
    paired: list,
    rows: list[dict],
    fields: tuple[str, ...],
    span: dict,
    floor: float,
    severe: float,
    base: int,
    top: int,
) -> None:
    c.assess(rule, "triggered", f"{name.capitalize()} fell {fell:.0%}, {before:,} to {now:,}.", 1)
    c.emit(
        rule,
        title,
        CHECKS[rule]["fix"],
        f"{name.capitalize()} fell {fell:.0%}: {now:,} in the four weeks to "
        f"{span['current_end']}, against {before:,} in the four weeks before, on "
        f"{len(paired)} weekday-matched days.",
        graded(base, (fell - floor) / (severe - floor), top - base, top),
        [
            c.evidence(
                "performance",
                rows,
                ["date", *fields],
                "sum over days paired with the same weekday one window earlier; "
                "(previous - current) / previous",
                current=now,
                previous=before,
                change=round(-fell, 4),
                paired_days=len(paired),
                threshold=floor,
                **span,
            )
        ],
        HREF,
        "A descriptive change, not attribution. Actions are events, not customers; "
        "seasonality and Google restatements can contribute.",
    )


def _impressions(c: Context, dates, end, length, rows, span) -> None:
    rule = "impressions_decline"
    paired = pairs(dates, end, length, IMPRESSIONS)
    if not _enough(c, rule, paired, "impressions"):
        return
    now, before = sum(p[1] for p in paired), sum(p[2] for p in paired)
    floor_volume = c.config.performance_min_impressions
    if min(now, before) < floor_volume:
        c.assess(
            rule,
            "insufficient_data",
            f"Under {floor_volume} impressions in a window; too few to compare.",
        )
        return
    fell = -(change(now, before) or 0.0)
    threshold = c.config.performance_impressions_decline
    if fell >= threshold:
        _decline_finding(
            c,
            rule,
            "Investigate the fall in impressions",
            "impressions",
            now,
            before,
            fell,
            paired,
            rows,
            IMPRESSIONS,
            span,
            threshold,
            max(0.4, threshold * 4),
            35,
            80,
        )
    else:
        c.assess(rule, "clear", f"Impressions {change(now, before):+.0%}, {before:,} to {now:,}.")


def _actions(c: Context, dates, end, length, rows, span) -> None:
    for rule, (field, name) in ACTION_RULES.items():
        paired = pairs(dates, end, length, (field,))
        if not _enough(c, rule, paired, name):
            continue
        now, before = sum(p[1] for p in paired), sum(p[2] for p in paired)
        if before < c.config.performance_min_actions:
            c.assess(
                rule,
                "insufficient_data",
                f"Only {before} {name} in the previous window; under the "
                f"{c.config.performance_min_actions} needed to compare.",
            )
            continue
        fell = -(change(now, before) or 0.0)
        threshold = c.config.performance_actions_decline
        if fell >= threshold:
            _decline_finding(
                c,
                rule,
                f"Investigate the fall in {name}",
                name,
                now,
                before,
                fell,
                paired,
                rows,
                (field,),
                span,
                threshold,
                max(0.5, threshold * 3),
                30,
                75,
            )
        else:
            c.assess(rule, "clear", f"{name.capitalize()} {change(now, before):+.0%}.")


def _rate(c: Context, dates, end, length, rows, span) -> None:
    rule = "action_rate_decline"
    paired = pairs(dates, end, length, IMPRESSIONS + ACTIONS)
    if not _enough(c, rule, paired, "impressions and actions"):
        return
    imp_now = sum(total(dates[d], IMPRESSIONS) or 0 for d, _, _ in paired)
    imp_before = sum(
        total(dates[d - timedelta(days=length)], IMPRESSIONS) or 0 for d, _, _ in paired
    )
    act_now = sum(total(dates[d], ACTIONS) or 0 for d, _, _ in paired)
    act_before = sum(total(dates[d - timedelta(days=length)], ACTIONS) or 0 for d, _, _ in paired)
    if min(imp_now, imp_before) < c.config.performance_min_impressions or (
        act_before < c.config.performance_min_actions
    ):
        c.assess(rule, "insufficient_data", "Too few impressions or actions to compare a rate.")
        return
    rate_now, rate_before = act_now / imp_now, act_before / imp_before
    fell = (rate_before - rate_now) / rate_before
    threshold = c.config.performance_action_rate_decline
    if fell >= threshold:
        c.assess(
            rule,
            "triggered",
            f"Actions per impression fell {fell:.0%}, {rate_before:.1%} to {rate_now:.1%}.",
            1,
        )
        c.emit(
            rule,
            "Investigate why fewer people act on the profile",
            CHECKS[rule]["fix"],
            f"Calls, directions and website clicks per impression fell {fell:.0%}: "
            f"{rate_now:.1%} in the four weeks to {span['current_end']} against "
            f"{rate_before:.1%} before, on {len(paired)} weekday-matched days.",
            graded(30, (fell - threshold) / (max(0.5, threshold * 3) - threshold), 40, 70),
            [
                c.evidence(
                    "performance",
                    rows,
                    ["date", *IMPRESSIONS, *ACTIONS],
                    "(calls + directions + website clicks) / impressions on paired days; "
                    "relative change",
                    current_rate=round(rate_now, 4),
                    previous_rate=round(rate_before, 4),
                    change=round(-fell, 4),
                    current_actions=act_now,
                    previous_actions=act_before,
                    current_impressions=imp_now,
                    previous_impressions=imp_before,
                    paired_days=len(paired),
                    threshold=threshold,
                    **span,
                )
            ],
            HREF,
            "An engagement ratio of interface events, not a conversion rate. A change in "
            "which searches show the profile moves it without anything on the profile "
            "changing.",
        )
    else:
        c.assess(rule, "clear", f"Actions per impression {rate_before:.1%} to {rate_now:.1%}.")


def _mix(c: Context, dates, end, length, rows, span) -> None:
    paired = pairs(dates, end, length, IMPRESSIONS)
    for rule, part, name in (
        ("surface_split_shift", MAPS, "Maps"),
        ("mobile_share_shift", MOBILE, "mobile"),
    ):
        if not _enough(c, rule, paired, "impressions by surface and device"):
            continue
        whole_now = sum(p[1] for p in paired)
        whole_before = sum(p[2] for p in paired)
        if min(whole_now, whole_before) < c.config.performance_min_impressions:
            c.assess(rule, "insufficient_data", "Too few impressions to compare shares.")
            continue
        part_now = sum(total(dates[d], part) or 0 for d, _, _ in paired)
        part_before = sum(total(dates[d - timedelta(days=length)], part) or 0 for d, _, _ in paired)
        share_now, share_before = part_now / whole_now, part_before / whole_before
        shift = share_now - share_before
        threshold = c.config.performance_split_shift_points
        if abs(shift) >= threshold:
            c.assess(
                rule,
                "triggered",
                f"{name.capitalize()} share moved {shift * 100:+.0f} points, "
                f"{share_before:.0%} to {share_now:.0%}.",
                1,
            )
            c.emit(
                rule,
                f"{name.capitalize()} share of impressions moved {shift * 100:+.0f} points",
                CHECKS[rule]["fix"],
                f"{name.capitalize()} impressions were {share_now:.0%} of the total in the "
                f"four weeks to {span['current_end']}, against {share_before:.0%} before.",
                30,
                [
                    c.evidence(
                        "performance",
                        rows,
                        ["date", *IMPRESSIONS],
                        f"{name} impressions / all impressions on paired days; difference in share",
                        current_share=round(share_now, 4),
                        previous_share=round(share_before, 4),
                        shift=round(shift, 4),
                        paired_days=len(paired),
                        threshold=threshold,
                        **span,
                    )
                ],
                HREF,
                "A change in mix is diagnostic, not good or bad on its own.",
            )
        else:
            c.assess(rule, "clear", f"{name} share {share_before:.0%} to {share_now:.0%}.")


def _zero_days(c: Context, dates, current, rows, span) -> None:
    rule = "zero_action_days"
    need = c.config.performance_zero_action_streak_days
    floor_imp = c.config.performance_zero_action_min_impressions
    evaluable = 0
    best: list[date] = []
    streak: list[date] = []
    d = current[0]
    while d <= current[1]:
        row = dates.get(d)
        imp, act = total(row, IMPRESSIONS), total(row, ACTIONS)
        # A missing day or an unknown metric breaks the streak: no data is not no actions.
        if imp is None or act is None:
            streak = []
        else:
            evaluable += 1
            if imp >= floor_imp and act == 0:
                streak.append(d)
            else:
                streak = []
        if len(streak) > len(best):
            best = list(streak)
        d += timedelta(days=1)
    if evaluable < need:
        c.assess(
            rule,
            "insufficient_data",
            f"Only {evaluable} days in the window report both impressions and actions.",
        )
        return
    if len(best) >= need:
        c.assess(
            rule,
            "triggered",
            f"{len(best)} consecutive days shown with zero actions, {best[0]} to {best[-1]}.",
            1,
        )
        c.emit(
            rule,
            f"{len(best)} days in a row shown with no actions",
            CHECKS[rule]["fix"],
            f"From {best[0]} to {best[-1]} the profile had at least {floor_imp} impressions "
            "a day while calls, directions and website clicks were all reported as zero.",
            graded(55, (len(best) - need) / max(1, 14 - need), 20, 75),
            [
                c.evidence(
                    "performance",
                    [dates[x] for x in best],
                    ["date", *IMPRESSIONS, *ACTIONS],
                    "consecutive days with impressions >= floor and every action == 0",
                    streak_days=len(best),
                    first=best[0].isoformat(),
                    last=best[-1].isoformat(),
                    threshold=need,
                    **span,
                )
            ],
            HREF,
            "Reported zeros, not confirmed absence. Google can restate a day later.",
            "high",
        )
    else:
        c.assess(rule, "clear", f"Longest zero-action run {len(best)} days across {evaluable}.")


def _gaps(c: Context, dates, current, rows, span) -> None:
    rule = "data_gaps"
    present = {d for d in dates if current[0] <= d <= current[1]}
    missing = []
    d = current[0]
    while d <= current[1]:
        if d not in present:
            missing.append(d)
        d += timedelta(days=1)
    need = c.config.performance_data_gap_days
    if len(missing) >= need:
        c.assess(
            rule,
            "triggered",
            f"{len(missing)} of {span['window_days']} days have no performance row.",
            1,
        )
        c.emit(
            rule,
            f"{len(missing)} days missing from the last four weeks",
            CHECKS[rule]["fix"],
            f"No performance row is stored for {len(missing)} of the {span['window_days']} "
            f"days to {span['current_end']}. Trend checks skipped those days.",
            20,
            [
                c.evidence(
                    "performance",
                    rows,
                    ["date"],
                    "calendar days in the current window with no row",
                    missing_days=[m.isoformat() for m in missing],
                    threshold=need,
                    **span,
                )
            ],
            HREF,
            "A gap in what was synced, not in what happened.",
            "high",
        )
    else:
        c.assess(rule, "clear", f"{len(present)} of {span['window_days']} days present.")


# ---- card ------------------------------------------------------------------------


def window_total(dates: dict[date, dict], start: date, end: date, fields: tuple[str, ...]):
    """Sum of reported values and the number of days that reported them."""
    value, days = 0, 0
    d = start
    while d <= end:
        t = total(dates.get(d), fields)
        if t is not None:
            value += t
            days += 1
        d += timedelta(days=1)
    return (value if days else None), days


def metric(dates, current, previous, fields) -> dict:
    now, now_days = window_total(dates, *current, fields)
    before, before_days = window_total(dates, *previous, fields)
    return {
        "current": now,
        "previous": before,
        "change": (
            round(delta, 4)
            if now is not None and before is not None and (delta := change(now, before)) is not None
            else None
        ),
        "days": now_days,
        "previous_days": before_days,
    }


def card(snapshot: dict, as_of: date | None = None, window_days: int = 28) -> dict:
    """Four-week totals with the four weeks before, and twelve weekly points."""
    loc = snapshot["locations"][0]
    rows = [r for r in snapshot.get("performance", []) if r.get("location_id") == loc["id"]]
    dates = by_date(rows)
    end = anchor(dates, as_of or date.max)
    if end is None:
        return {
            "window": None,
            "days_with_data": 0,
            "metrics": {},
            "weekly_impressions": [],
            "maps_share": None,
            "mobile_share": None,
        }
    current, previous = windows(end, window_days)
    maps = metric(dates, current, previous, MAPS)
    search = metric(dates, current, previous, SEARCH)
    impressions = metric(dates, current, previous, IMPRESSIONS)
    actions = metric(dates, current, previous, ACTIONS)
    rate_now = (
        actions["current"] / impressions["current"]
        if actions["current"] is not None and impressions["current"]
        else None
    )
    rate_before = (
        actions["previous"] / impressions["previous"]
        if actions["previous"] is not None and impressions["previous"]
        else None
    )
    mobile, _ = window_total(dates, *current, MOBILE)
    weekly = []
    for week in range(12):
        w_end = end - timedelta(days=7 * week)
        w_start = w_end - timedelta(days=6)
        value, days = window_total(dates, w_start, w_end, IMPRESSIONS)
        weekly.append(
            {
                "start": w_start.isoformat(),
                "end": w_end.isoformat(),
                "impressions": value,
                "days": days,
            }
        )
    weekly.reverse()
    return {
        "window": {
            "days": window_days,
            "current_start": current[0].isoformat(),
            "current_end": current[1].isoformat(),
            "previous_start": previous[0].isoformat(),
            "previous_end": previous[1].isoformat(),
            "latest_date": end.isoformat(),
            "data_age_days": (as_of - end).days if as_of else None,
        },
        "days_with_data": impressions["days"],
        "metrics": {
            "impressions": impressions,
            "impressions_maps": maps,
            "impressions_search": search,
            "calls": metric(dates, current, previous, ("call_clicks",)),
            "directions": metric(dates, current, previous, ("direction_requests",)),
            "website_clicks": metric(dates, current, previous, ("website_clicks",)),
            "conversations": metric(dates, current, previous, ("conversations",)),
            "bookings": metric(dates, current, previous, ("bookings",)),
            "action_rate": {
                "current": round(rate_now, 4) if rate_now is not None else None,
                "previous": round(rate_before, 4) if rate_before is not None else None,
                "change": (
                    round((rate_now - rate_before) / rate_before, 4)
                    if rate_now is not None and rate_before
                    else None
                ),
                "days": actions["days"],
                "previous_days": actions["previous_days"],
            },
        },
        "maps_share": (
            round(maps["current"] / impressions["current"], 4)
            if maps["current"] is not None and impressions["current"]
            else None
        ),
        "mobile_share": (
            round(mobile / impressions["current"], 4)
            if mobile is not None and impressions["current"]
            else None
        ),
        "weekly_impressions": weekly,
    }
