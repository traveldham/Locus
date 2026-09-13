"""Operations worker: do appointment requests become visits?

Four groups of checks, all deterministic, all over the CRM's booking requests:

- Response: are requests answered, and in time?
- Outcomes: how many settled visits are lost to cancellations and no-shows?
- Demand: do the services and days customers ask for match what the profile offers?
- Tracking: are requests arriving through every channel, and does Google see them?

Statuses are current state and often stale, so a future visit is never a failure and
outcome rates use only settled statuses as their denominator. Small denominators
abstain. Customer identity never reaches the snapshot, so no finding names a person.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta
from statistics import median
from typing import TYPE_CHECKING

from app.services.recommendations.grading import graded
from app.services.recommendations.values import day, number

if TYPE_CHECKING:
    from app.services.recommendations.context import Context

KEY = "operations"
LABEL = "Operations"
WEIGHT = 15

SETTLED = ("completed", "cancelled", "no_show")
CONFIRMED = ("confirmed", "completed", "no_show")
WEEKEND = ("SATURDAY", "SUNDAY")
CHANNEL_LABELS = {
    "website": "website",
    "google_profile": "Google profile",
    "phone": "phone",
    "walk_in": "walk-in",
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
    group: str = "response",
    effort: str = "hour",
) -> dict:
    return {
        "weight": weight,
        # Which of the four groups the check belongs to, for the completeness strip.
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
        # The field a suggestion may be drafted for. None: nothing to draft.
        "suggests": suggests,
    }


CHECKS: dict[str, dict] = {
    # Response
    "requests_unanswered": check(
        3,
        "Request waiting for an answer",
        "Requests still marked new longer than the configured wait after they were made.",
        "Reply to each waiting request today and confirm a time, or mark it cancelled if "
        "the customer has gone elsewhere. A request left for days is a customer lost.",
        unit="request",
        predicate="are still waiting for an answer",
        predicate_one="is still waiting for an answer",
        subject="request",
        subject_predicate="are still waiting for an answer",
        suggests="followup_message",
    ),
    "requests_expired": check(
        2,
        "Requested date passed with no decision",
        "Requests still marked new whose requested date is already in the past.",
        "Work through the expired requests: record what happened, and if the customer "
        "never heard back, contact them with a new time.",
        predicate="have requests whose date passed unanswered",
        predicate_one="has requests whose date passed unanswered",
    ),
    "confirmation_rate_low": check(
        2,
        "Few requests confirmed",
        "The share of requests old enough to decide that were confirmed, completed or "
        "attended, against the configured minimum.",
        "Answer requests within a day and offer two alternative times when the first is "
        "taken. Track why requests are not confirmed.",
        predicate="confirm few of their requests",
        predicate_one="confirms few of its requests",
    ),
    # Outcomes
    "cancellation_rate_high": check(
        2,
        "High cancellation rate",
        "Cancelled visits as a share of settled visits (completed, cancelled, no-show) "
        "in the window, against the configured maximum.",
        "Send a confirmation at booking and a reminder two days before. Keep a short "
        "wait list so a cancelled slot is refilled the same day.",
        predicate="lose many visits to cancellations",
        predicate_one="loses many visits to cancellations",
        group="outcomes",
    ),
    "no_show_rate_high": check(
        2,
        "High no-show rate",
        "No-shows as a share of settled visits in the window, against the configured maximum.",
        "Add a text reminder the day before and the morning of the visit with a one-tap "
        "confirm. Call anyone who has not confirmed by the evening before.",
        predicate="lose many visits to no-shows",
        predicate_one="loses many visits to no-shows",
        suggests="reminder_plan",
        group="outcomes",
    ),
    # Demand
    "service_not_listed": check(
        1,
        "Requested service not on the service list",
        "Services customers requested that match none of the project's listed services.",
        "Add the service to the project's list if it is offered, so the profile and the "
        "website say so; if it is not offered, make that clear on the booking form.",
        unit="service",
        predicate="are requested but not listed",
        predicate_one="is requested but not listed",
        subject="service",
        subject_predicate="are requested but not listed",
        group="demand",
    ),
    "weekend_demand_without_hours": check(
        2,
        "Weekend requests with no weekend hours",
        "Requests for a Saturday or Sunday when no regular hours are posted for that day.",
        "Decide whether to open that day. If you do, post the hours on the profile; if "
        "not, let the booking form only offer days you are open.",
        unit="day",
        predicate="get weekend requests with no weekend hours",
        predicate_one="gets weekend requests with no weekend hours",
        subject="day",
        subject_predicate="get requests with no hours posted",
        suggests="hours_note",
        group="demand",
    ),
    "lead_time_shrinking": check(
        1,
        "Lead time collapsing",
        "The median days between a request and its requested date in the recent slice, "
        "against the earlier part of the window.",
        "Customers are asking for sooner visits. Hold a few same-week slots open each "
        "day, or the urgent requests will go to whoever can see them first.",
        predicate="see lead time collapsing",
        predicate_one="sees lead time collapsing",
        group="demand",
    ),
    # Tracking
    "channel_concentrated": check(
        1,
        "Requests come from one channel",
        "Whether a single channel carries more than the configured share of requests.",
        "Check that the other channels are wired up: the booking link on the profile, "
        "the website form, and phone requests being logged.",
        predicate="get nearly all requests from one channel",
        predicate_one="gets nearly all requests from one channel",
        group="tracking",
    ),
    "google_bookings_untracked": check(
        1,
        "Google reports no bookings",
        "Whether Google's daily bookings count is zero across the window while the "
        "booking system holds requests.",
        "Google only counts bookings made through a Reserve with Google partner. Connect "
        "one, or accept that the profile's booking traffic is invisible in Google's "
        "reports and rely on the booking system's own channel field.",
        predicate="have bookings Google does not see",
        predicate_one="has bookings Google does not see",
        group="tracking",
    ),
}


GROUPS = {
    "response": ("requests_unanswered", "requests_expired", "confirmation_rate_low"),
    "outcomes": ("cancellation_rate_high", "no_show_rate_high"),
    "demand": ("service_not_listed", "weekend_demand_without_hours", "lead_time_shrinking"),
    "tracking": ("channel_concentrated", "google_bookings_untracked"),
}
GROUP_LABELS = {
    "response": "Response",
    "outcomes": "Outcomes",
    "demand": "Demand",
    "tracking": "Tracking",
}
EFFORT = {
    "minutes": ("requests_unanswered", "service_not_listed"),
    "hour": (
        "requests_expired",
        "confirmation_rate_low",
        "weekend_demand_without_hours",
        "lead_time_shrinking",
        "channel_concentrated",
    ),
    "afternoon": ("cancellation_rate_high", "no_show_rate_high", "google_bookings_untracked"),
}
for _group, _rules in GROUPS.items():
    for _rule in _rules:
        CHECKS[_rule]["group"] = _group
for _effort, _rules in EFFORT.items():
    for _rule in _rules:
        CHECKS[_rule]["effort"] = _effort
assert {r for rules in GROUPS.values() for r in rules} == set(CHECKS)
assert {r for rules in EFFORT.values() for r in rules} == set(CHECKS)


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", str(text).casefold()) if len(w) > 3}


def status_of(row: dict) -> str:
    return str(row.get("status") or "").casefold()


def lead_days(row: dict) -> int | None:
    made, wanted = day(row.get("booking_created_at")), day(row.get("requested_for_date"))
    if made is None or wanted is None:
        return None
    return (wanted - made).days


def project_services(snapshot: dict) -> list[str]:
    seen: dict[str, None] = {}
    for project in snapshot.get("projects", []):
        for service in project.get("services") or []:
            if isinstance(service, str) and service.strip():
                seen.setdefault(service.strip(), None)
    return list(seen)


def listed(service: str, services: list[str]) -> bool:
    """A requested service is listed when its name matches, or shares a real word."""
    wanted = str(service).strip().casefold()
    for known in services:
        if known.casefold() == wanted or words(known) & words(service):
            return True
    return False


def weekend_days_open(hours: list[dict]) -> set[str]:
    return {
        str(r.get("open_day") or "").upper()
        for r in hours
        if (r.get("hours_type") or "REGULAR") == "REGULAR"
        and str(r.get("open_day") or "").upper() in WEEKEND
    }


def evaluate(c: Context) -> None:
    loc = c.location
    href = f"/locations/{loc['id']}/bookings"
    if loc.get("open_status") == "closed_permanently":
        for rule in CHECKS:
            c.assess(rule, "suppressed", "Permanently closed: operations are not audited.")
        return

    window = c.config.booking_window_days
    requests = c.window(c.rows("bookings"), "booking_created_at", window)
    if not requests:
        for rule in CHECKS:
            c.assess(rule, "insufficient_data", f"No booking requests in the last {window} days.")
        return

    _response(c, requests, href)
    _outcomes(c, requests, href)
    _demand(c, requests, href)
    _tracking(c, requests, href)


def _response(c: Context, requests: list[dict], href: str) -> None:
    wait = c.config.booking_wait_days
    new = [r for r in requests if status_of(r) == "new"]
    aged = sorted(
        (
            (r, (c.as_of - day(r["booking_created_at"])).days)
            for r in new
            if day(r.get("booking_created_at"))
        ),
        key=lambda pair: -pair[1],
    )
    stale = [(r, age) for r, age in aged if age > wait]
    if stale:
        c.assess(
            "requests_unanswered",
            "triggered",
            f"{len(stale)} of {len(requests)} requests have waited more than {wait} days.",
            len(stale),
            len(requests),
        )
        for r, age in stale:
            ref = str(r.get("external_booking_id") or r["id"])
            service = str(r.get("service") or "an appointment")
            c.emit(
                "requests_unanswered",
                f"Request {ref} has waited {age} days",
                CHECKS["requests_unanswered"]["fix"],
                f"A request for {service} made {age} days ago is still marked new; the "
                f"policy is to answer within {wait} days.",
                graded(62, (age - wait) / 30, 26, 88),
                [
                    c.evidence(
                        "bookings",
                        [r],
                        ["external_booking_id", "service", "status", "booking_created_at"],
                        "days between booking_created_at and the analysis date, status new",
                        age_days=age,
                        wait_days=wait,
                        service=service,
                        requested_for=r.get("requested_for_date"),
                    )
                ],
                href,
                "Status is current stored state. A request answered outside the booking "
                "system still shows as new.",
                "high",
                subject=ref,
            )
    else:
        c.assess(
            "requests_unanswered",
            "clear",
            f"No request has waited more than {wait} days ({len(new)} new).",
        )

    expired = [
        r
        for r in new
        if day(r.get("requested_for_date")) and day(r["requested_for_date"]) < c.as_of
    ]
    if expired:
        oldest = min(day(r["requested_for_date"]) for r in expired)
        c.assess(
            "requests_expired",
            "triggered",
            f"{len(expired)} new requests are for dates that have passed.",
            len(expired),
            len(requests),
        )
        c.emit(
            "requests_expired",
            f"{len(expired)} requests passed their date unanswered",
            CHECKS["requests_expired"]["fix"],
            f"{len(expired)} of {len(requests)} requests in the window are still marked "
            f"new although their requested date has passed; the oldest was for {oldest}.",
            graded(48, (len(expired) / len(requests) - 0.05) / 0.25, 20, 68),
            [
                c.evidence(
                    "bookings",
                    expired,
                    ["external_booking_id", "status", "requested_for_date"],
                    "status new and requested_for_date before the analysis date",
                    expired=len(expired),
                    requests=len(requests),
                    oldest_requested_for=str(oldest),
                )
            ],
            href,
            "The visit may have happened without the status being updated.",
            "high",
        )
    else:
        c.assess("requests_expired", "clear", "No new request is past its requested date.")

    decidable = [
        r
        for r in requests
        if day(r.get("booking_created_at")) and (c.as_of - day(r["booking_created_at"])).days > wait
    ]
    minimum = c.config.booking_min_requests
    floor = c.config.booking_confirmation_min
    if len(decidable) < minimum:
        c.assess(
            "confirmation_rate_low",
            "insufficient_data",
            f"Only {len(decidable)} requests are old enough to judge; the floor is {minimum}.",
        )
        return
    confirmed = [r for r in decidable if status_of(r) in CONFIRMED]
    rate = len(confirmed) / len(decidable)
    if rate < floor:
        c.assess(
            "confirmation_rate_low",
            "triggered",
            f"{len(confirmed)} of {len(decidable)} requests confirmed ({rate:.0%}).",
            len(decidable) - len(confirmed),
            len(decidable),
        )
        c.emit(
            "confirmation_rate_low",
            f"Only {rate:.0%} of requests are confirmed",
            CHECKS["confirmation_rate_low"]["fix"],
            f"{len(confirmed)} of {len(decidable)} requests older than {wait} days were "
            f"confirmed, completed or attended ({rate:.0%}); the policy minimum is {floor:.0%}.",
            graded(45, (floor - rate) / floor, 25, 72),
            [
                c.evidence(
                    "bookings",
                    decidable,
                    ["status", "booking_created_at"],
                    "confirmed + completed + no_show over requests older than the wait",
                    confirmed=len(confirmed),
                    decidable=len(decidable),
                    rate=round(rate, 3),
                    minimum=floor,
                )
            ],
            href,
            "Cancelled counts as not confirmed even when the customer cancelled.",
            "high",
        )
    else:
        c.assess(
            "confirmation_rate_low",
            "clear",
            f"{len(confirmed)} of {len(decidable)} requests confirmed ({rate:.0%}).",
        )


def _outcomes(c: Context, requests: list[dict], href: str) -> None:
    settled = [r for r in requests if status_of(r) in SETTLED]
    minimum = c.config.booking_min_settled
    if len(settled) < minimum:
        for rule in ("cancellation_rate_high", "no_show_rate_high"):
            c.assess(
                rule,
                "insufficient_data",
                f"Only {len(settled)} settled visits in the window; the floor is {minimum}.",
            )
        return
    for rule, status, maximum, title in (
        (
            "cancellation_rate_high",
            "cancelled",
            c.config.booking_cancellation_max,
            "cancelled",
        ),
        ("no_show_rate_high", "no_show", c.config.booking_no_show_max, "missed"),
    ):
        lost = [r for r in settled if status_of(r) == status]
        rate = len(lost) / len(settled)
        if rate > maximum:
            c.assess(
                rule,
                "triggered",
                f"{len(lost)} of {len(settled)} settled visits {title} ({rate:.0%}).",
                len(lost),
                len(settled),
            )
            c.emit(
                rule,
                f"{rate:.0%} of settled visits were {title}",
                CHECKS[rule]["fix"],
                f"{len(lost)} of {len(settled)} settled visits in the window were {title} "
                f"({rate:.0%}); the policy maximum is {maximum:.0%}.",
                graded(46, (rate - maximum) / maximum, 24, 74),
                [
                    c.evidence(
                        "bookings",
                        settled,
                        ["status"],
                        f"{status} over completed + cancelled + no_show",
                        lost=len(lost),
                        settled=len(settled),
                        rate=round(rate, 3),
                        maximum=maximum,
                    )
                ],
                href,
                "Only settled visits are counted; confirmed visits whose outcome was "
                "never recorded are left out, so the rate may run high.",
                "high",
            )
        else:
            c.assess(rule, "clear", f"{len(lost)} of {len(settled)} settled visits {title}.")


def _demand(c: Context, requests: list[dict], href: str) -> None:
    services = project_services(c.snapshot)
    requested = Counter(str(r.get("service")).strip() for r in requests if r.get("service"))
    if not services:
        c.assess(
            "service_not_listed",
            "insufficient_data",
            "No project service list to compare requests against.",
        )
    elif not requested:
        c.assess("service_not_listed", "insufficient_data", "No request names a service.")
    else:
        unlisted = [(s, n) for s, n in requested.most_common() if not listed(s, services)]
        if unlisted:
            c.assess(
                "service_not_listed",
                "triggered",
                f"{len(unlisted)} of {len(requested)} requested services are not listed.",
                len(unlisted),
                len(requested),
            )
            for service, count in unlisted:
                rows = [r for r in requests if str(r.get("service") or "").strip() == service]
                c.emit(
                    "service_not_listed",
                    f"“{service}” is requested but not listed",
                    CHECKS["service_not_listed"]["fix"],
                    f"{count} {'request' if count == 1 else 'requests'} asked for “{service}”, "
                    "which matches none of the services on the project.",
                    graded(22, (count - 1) / 10, 18, 42),
                    [
                        c.evidence(
                            "bookings",
                            rows,
                            ["service"],
                            "requested service name matched no project service by word",
                            service=service,
                            requests=count,
                            listed_services=services,
                        )
                    ],
                    href,
                    "Word matching between free-text names; a renamed service can look unlisted.",
                    subject=service,
                )
        else:
            c.assess(
                "service_not_listed",
                "clear",
                f"All {len(requested)} requested services match the project list.",
            )

    hours = c.rows("hours")
    regular = [r for r in hours if (r.get("hours_type") or "REGULAR") == "REGULAR"]
    by_day: dict[str, list[dict]] = {d: [] for d in WEEKEND}
    for r in requests:
        wanted = day(r.get("requested_for_date"))
        if wanted and wanted.weekday() >= 5:
            by_day[WEEKEND[wanted.weekday() - 5]].append(r)
    minimum = c.config.booking_weekend_min_requests
    if not regular:
        c.assess(
            "weekend_demand_without_hours",
            "insufficient_data",
            "No regular hours are stored, so open days are unknown.",
        )
    else:
        open_days = weekend_days_open(regular)
        judged = [d for d in WEEKEND if len(by_day[d]) >= minimum]
        missed = [d for d in judged if d not in open_days]
        if not judged:
            c.assess(
                "weekend_demand_without_hours",
                "clear",
                f"Fewer than {minimum} requests for any weekend day: no demand to miss.",
            )
        elif missed:
            c.assess(
                "weekend_demand_without_hours",
                "triggered",
                f"{len(missed)} weekend day(s) with requests have no hours posted.",
                len(missed),
                len(judged),
            )
            for d in missed:
                count = len(by_day[d])
                c.emit(
                    "weekend_demand_without_hours",
                    f"{count} requests for {d.title()} but no {d.title()} hours",
                    CHECKS["weekend_demand_without_hours"]["fix"],
                    f"{count} of {len(requests)} requests in the window asked for a "
                    f"{d.title()}, and the profile posts no hours for {d.title()}.",
                    graded(40, (count / len(requests) - 0.05) / 0.2, 20, 60),
                    [
                        c.evidence(
                            "bookings",
                            by_day[d],
                            ["requested_for_date"],
                            "requested_for_date falls on this weekday",
                            day=d.title(),
                            requests=count,
                            total=len(requests),
                        ),
                        c.evidence(
                            "hours",
                            regular,
                            ["open_day"],
                            f"no REGULAR row for {d}",
                        ),
                    ],
                    href,
                    "Demand, not proof it is worth opening. The booking form may offer "
                    "days the location is closed.",
                    "high",
                    subject=d.title(),
                )
        else:
            c.assess(
                "weekend_demand_without_hours",
                "clear",
                "Every weekend day with requests has hours posted.",
            )

    recent_days = c.config.booking_lead_recent_days
    minimum = c.config.booking_min_requests
    cutoff = c.as_of - timedelta(days=recent_days - 1)
    recent, earlier = [], []
    for r in requests:
        lead = lead_days(r)
        if lead is None or lead < 0:
            continue
        (recent if day(r["booking_created_at"]) >= cutoff else earlier).append(lead)
    if len(recent) < minimum or len(earlier) < minimum:
        c.assess(
            "lead_time_shrinking",
            "insufficient_data",
            f"Need {minimum} requests in both the recent {recent_days} days and before.",
        )
    else:
        now, before = median(recent), median(earlier)
        ratio = c.config.booking_lead_collapse_ratio
        if before > 0 and now < before * ratio:
            c.assess(
                "lead_time_shrinking",
                "triggered",
                f"Median lead time fell from {before:g} to {now:g} days.",
                1,
            )
            c.emit(
                "lead_time_shrinking",
                f"Lead time fell from {before:g} to {now:g} days",
                CHECKS["lead_time_shrinking"]["fix"],
                f"Requests made in the last {recent_days} days ask for a visit a median "
                f"{now:g} days out, against {before:g} days earlier in the window.",
                graded(25, (1 - now / before - (1 - ratio)) / ratio, 15, 42),
                [
                    c.evidence(
                        "bookings",
                        requests,
                        ["booking_created_at", "requested_for_date"],
                        "median of requested_for_date minus booking_created_at, recent vs earlier",
                        recent_median=now,
                        earlier_median=before,
                        recent=len(recent),
                        earlier=len(earlier),
                        ratio=ratio,
                    )
                ],
                href,
                "A shift in what customers ask for, not in what the schedule can hold.",
            )
        else:
            c.assess(
                "lead_time_shrinking",
                "clear",
                f"Median lead time {now:g} days recently, {before:g} before.",
            )


def _tracking(c: Context, requests: list[dict], href: str) -> None:
    channels = Counter(
        str(r.get("booking_source")).casefold() for r in requests if r.get("booking_source")
    )
    minimum = c.config.booking_min_requests
    maximum = c.config.booking_channel_share_max
    known = sum(channels.values())
    if known < minimum:
        c.assess(
            "channel_concentrated",
            "insufficient_data",
            f"Only {known} requests carry a channel; the floor is {minimum}.",
        )
    else:
        channel, count = channels.most_common(1)[0]
        share = count / known
        if share > maximum:
            label = CHANNEL_LABELS.get(channel, channel)
            c.assess(
                "channel_concentrated",
                "triggered",
                f"{share:.0%} of requests arrive by {label}.",
                1,
            )
            c.emit(
                "channel_concentrated",
                f"{share:.0%} of requests come by {label}",
                CHECKS["channel_concentrated"]["fix"],
                f"{count} of {known} requests with a known channel arrived by {label}; "
                f"the policy maximum for one channel is {maximum:.0%}.",
                graded(22, (share - maximum) / (1 - maximum), 18, 40),
                [
                    c.evidence(
                        "bookings",
                        requests,
                        ["booking_source"],
                        "largest channel share of requests with a channel",
                        channel=channel,
                        share=round(share, 3),
                        counts=dict(channels),
                    )
                ],
                href,
                "A channel field the booking system fills; a missing channel is unknown.",
            )
        else:
            c.assess("channel_concentrated", "clear", f"Largest channel share is {share:.0%}.")

    window = c.config.booking_window_days
    reported = [
        r for r in c.window(c.rows("performance"), "date", window) if number(r.get("bookings"))
    ]
    if not reported:
        c.assess(
            "google_bookings_untracked",
            "insufficient_data",
            "Google reported no bookings metric for any day in the window.",
        )
        return
    total = sum(int(r["bookings"]) for r in reported)
    if total == 0:
        c.assess(
            "google_bookings_untracked",
            "triggered",
            f"Google reports 0 bookings over {len(reported)} days while {len(requests)} "
            "requests exist.",
            1,
        )
        c.emit(
            "google_bookings_untracked",
            "Google sees none of the bookings",
            CHECKS["google_bookings_untracked"]["fix"],
            f"Google reported 0 bookings across {len(reported)} days in the window, while "
            f"the booking system holds {len(requests)} requests for the same period.",
            25,
            [
                c.evidence(
                    "performance",
                    reported,
                    ["date", "bookings"],
                    "sum of bookings over reported days",
                    google_bookings=0,
                    reported_days=len(reported),
                ),
                c.evidence(
                    "bookings",
                    requests,
                    ["booking_source"],
                    "requests in the window",
                    requests=len(requests),
                    from_google_profile=sum(
                        1 for r in requests if str(r.get("booking_source")) == "google_profile"
                    ),
                ),
            ],
            href,
            "Google only counts Reserve with Google bookings; the two numbers never reconcile.",
            "high",
        )
    else:
        c.assess(
            "google_bookings_untracked",
            "clear",
            f"Google reports {total} bookings over {len(reported)} days.",
        )


def card(snapshot: dict) -> dict:
    """The request funnel and its shape, for the operations tab."""
    from app.services.recommendations.types import EngineConfig

    window = EngineConfig().booking_window_days
    loc = snapshot["locations"][0]
    rows = [r for r in snapshot.get("bookings", []) if r.get("location_id") == loc["id"]]
    dated = [r for r in rows if day(r.get("booking_created_at"))]
    # No analysis date is handed to a card, so the newest request stands in for it.
    as_of: date | None = max((day(r["booking_created_at"]) for r in dated), default=None)
    requests = (
        [r for r in dated if (as_of - day(r["booking_created_at"])).days < window] if as_of else []
    )
    counts = Counter(status_of(r) for r in requests)
    settled = sum(counts[s] for s in SETTLED)
    decided = [r for r in requests if status_of(r) != "new"]
    leads = [lead for r in requests if (lead := lead_days(r)) is not None and lead >= 0]
    new_ages = [
        (as_of - day(r["booking_created_at"])).days for r in requests if status_of(r) == "new"
    ]
    services = Counter(str(r.get("service")).strip() for r in requests if r.get("service"))
    channels = Counter(
        str(r.get("booking_source")).casefold() for r in requests if r.get("booking_source")
    )
    return {
        "as_of": str(as_of) if as_of else None,
        "window_days": window,
        "requests": len(requests),
        "funnel": {
            "new": counts["new"],
            "confirmed": counts["confirmed"],
            "completed": counts["completed"],
            "cancelled": counts["cancelled"],
            "no_show": counts["no_show"],
        },
        "confirmation_rate": (
            round(sum(1 for r in decided if status_of(r) in CONFIRMED) / len(decided), 3)
            if decided
            else None
        ),
        "cancellation_rate": round(counts["cancelled"] / settled, 3) if settled else None,
        "no_show_rate": round(counts["no_show"] / settled, 3) if settled else None,
        "settled": settled,
        "median_lead_days": median(leads) if leads else None,
        "oldest_new_age_days": max(new_ages) if new_ages else None,
        "services": [{"service": s, "requests": n} for s, n in services.most_common(8)],
        "channels": [
            {"channel": CHANNEL_LABELS.get(ch, ch), "requests": n}
            for ch, n in channels.most_common()
        ],
        "weekend_requests": sum(
            1
            for r in requests
            if day(r.get("requested_for_date")) and day(r["requested_for_date"]).weekday() >= 5
        ),
    }
