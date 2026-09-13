from app.services.recommendations.context import Context, day, number
from app.services.recommendations.policy import graded

# The failure rate the policy treats as fully severe. Not an industry benchmark.
SEVERE_FAILURE_RATE = 0.5


def evaluate_operations(c: Context):
    recent = c.window(c.rows("reviews"), "create_time", c.config.window_days)
    valid = [
        r for r in recent if number(r.get("star_rating")) and r["star_rating"] in (1, 2, 3, 4, 5)
    ]
    if len(valid) < c.config.min_reviews or not c.fresh(valid, "create_time"):
        c.assess("reviews", "insufficient_data", "Too few recent valid reviews or stale activity.")
    else:
        pending = [
            r
            for r in valid
            if r["star_rating"] <= 3
            and not r.get("reply_comment")
            and (c.as_of - day(r["create_time"])).days >= c.config.reply_wait_days
        ]
        if pending:
            share = len(pending) / len(valid)
            oldest = max((c.as_of - day(r["create_time"])).days for r in pending)
            c.assess(
                "reviews",
                "triggered",
                f"{len(pending)} of {len(valid)} recent reviews rated 1-3 are unanswered.",
                len(pending),
                len(valid),
            )
            c.emit(
                "reviews",
                "Respond to unanswered critical reviews",
                "Read the flagged reviews, acknowledge the concern without sharing customer "
                "details, and invite private follow-up. Investigate recurring issues internally.",
                f"{len(pending)} reviews rated 1-3 remain unanswered after "
                f"{c.config.reply_wait_days} days, among {len(valid)} recent reviews "
                f"({share:.0%}). The oldest has waited {oldest} days.",
                graded(72, max(share, min(1.0, len(pending) / 10)), 23, 95),
                [
                    c.evidence(
                        "reviews",
                        valid,
                        ["google_review_id", "star_rating", "create_time", "reply_comment"],
                        "Count rating <= 3, reply absent, age >= wait days",
                        unanswered=len(pending),
                        pending_row_ids=sorted(str(r["id"]) for r in pending),
                        recent_reviews=len(valid),
                        unanswered_share=round(share, 4),
                        oldest_wait_days=oldest,
                        wait_days=c.config.reply_wait_days,
                    )
                ],
                "/reviews",
                "Reply state is current; reviews are a self-selected sample. "
                "No automatic public reply is sent.",
                "high",
            )
        else:
            c.assess("reviews", "clear", "No qualifying unanswered critical reviews.")

    requests = c.window(c.rows("bookings"), "booking_created_at", c.config.window_days)
    if not requests or not c.fresh(requests, "booking_created_at"):
        c.assess("booking_followup", "insufficient_data", "No recent booking activity.")
    else:
        waiting = [
            r
            for r in requests
            if r.get("status") == "new"
            and (c.as_of - day(r["booking_created_at"])).days >= c.config.booking_wait_days
        ]
        if waiting:
            oldest = max((c.as_of - day(r["booking_created_at"])).days for r in waiting)
            magnitude = max(
                min(1.0, len(waiting) / 10), min(1.0, oldest / (c.config.booking_wait_days * 10))
            )
            c.assess(
                "booking_followup",
                "triggered",
                f"{len(waiting)} requests still say new after {c.config.booking_wait_days} days.",
                len(waiting),
                len(requests),
            )
            c.emit(
                "booking_followup",
                "Reconcile outstanding appointment requests",
                "Check the flagged requests in the booking system. Confirm pending appointments "
                "or correct stale statuses before contacting customers.",
                f"{len(waiting)} of {len(requests)} recent requests still say new after at least "
                f"{c.config.booking_wait_days} days. The oldest was created {oldest} days ago.",
                graded(74, magnitude, 20, 94),
                [
                    c.evidence(
                        "bookings",
                        waiting,
                        [
                            "external_booking_id",
                            "status",
                            "booking_created_at",
                            "requested_for_date",
                        ],
                        "Count new requests aged >= configured wait",
                        count=len(waiting),
                        recent_requests=len(requests),
                        oldest_age_days=oldest,
                        wait_days=c.config.booking_wait_days,
                    )
                ],
                "/bookings",
                "Current statuses may be stale. This is a reconciliation task, "
                "not proof of lost appointments.",
                "high",
            )
        else:
            c.assess("booking_followup", "clear", "No aged new requests in the recent window.")

    # Settled outcomes accumulate far more slowly than requests arrive, so this check
    # reads a longer window than the daily comparisons. A 28-day window cannot reach a
    # denominator worth reporting on a clinic-sized appointment book.
    window = c.config.outcome_window_days
    visits = c.window(c.rows("bookings"), "requested_for_date", window)
    settled = [
        r
        for r in visits
        if day(r["requested_for_date"]) < c.as_of
        and r.get("status") in ("completed", "cancelled", "no_show")
        and day(r.get("booking_created_at"))
        and day(r["booking_created_at"]) <= c.as_of
    ]
    if len(settled) < c.config.min_completed_visits or not c.fresh(settled, "requested_for_date"):
        c.assess(
            "booking_outcomes",
            "insufficient_data",
            f"Fewer than {c.config.min_completed_visits} settled past visits "
            f"in {window} days ({len(settled)}).",
        )
    else:
        failed = [r for r in settled if r["status"] in ("cancelled", "no_show")]
        rate = len(failed) / len(settled)
        if rate >= c.config.failed_visit_fraction:
            ceiling = max(SEVERE_FAILURE_RATE, c.config.failed_visit_fraction + 0.05)
            magnitude = (rate - c.config.failed_visit_fraction) / (
                ceiling - c.config.failed_visit_fraction
            )
            cancelled = sum(r["status"] == "cancelled" for r in settled)
            c.assess(
                "booking_outcomes",
                "triggered",
                f"{len(failed)} of {len(settled)} settled past visits did not happen ({rate:.0%}).",
                1,
            )
            c.emit(
                "booking_outcomes",
                "Review cancellation and no-show follow-up",
                "Audit the flagged past appointments and reminder process with the manager. "
                "Check cancellation reasons before deciding whether to change reminders.",
                f"{len(failed)} of {len(settled)} settled past visits were cancelled or no-show "
                f"({rate:.1%}) over {window} days, against a {c.config.failed_visit_fraction:.0%} "
                "policy threshold.",
                graded(58, magnitude, 30, 88),
                [
                    c.evidence(
                        "bookings",
                        settled,
                        ["status", "requested_for_date"],
                        "(cancelled + no_show) / settled past visits",
                        failed=len(failed),
                        cancelled=cancelled,
                        no_show=len(failed) - cancelled,
                        settled=len(settled),
                        rate=round(rate, 6),
                        window_days=window,
                        threshold=c.config.failed_visit_fraction,
                    )
                ],
                "/bookings",
                "Excludes future appointments and unsettled statuses; excludes unknown outcomes. "
                "The threshold is a configurable operating policy, not an industry benchmark.",
            )
        else:
            c.assess("booking_outcomes", "clear", "Settled failure rate below policy threshold.")
