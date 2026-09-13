"""Per-location measurements shown beside the audit score.

Metrics describe observed data. They are not scored, and an unavailable metric is
reported as unavailable rather than as zero.
"""

from app.services.recommendations.context import Context, day, number
from app.services.recommendations.performance import ACTIONS, IMPRESSIONS
from app.services.recommendations.types import Metric


def change(current: float | None, previous: float | None) -> float | None:
    if current is None or not previous:
        return None
    return round((current - previous) / previous, 4)


def metric(key, label, category, value, unit="count", previous=None, direction="neutral", basis=""):
    return Metric(
        key=key,
        label=label,
        category=category,
        value=value,
        unit=unit,
        previous=previous,
        change_pct=change(value, previous),
        direction=direction,
        available=value is not None,
        basis=basis,
    )


def collect(c: Context) -> list[Metric]:
    days = c.config.window_days
    out: list[Metric] = []

    perf = c.rows("performance")

    def totals(rows, keys):
        usable = [r for r in rows if all(number(r.get(k)) for k in (*IMPRESSIONS, *ACTIONS))]
        return sum(r[k] for r in usable for k in keys) if usable else None

    current, previous = c.window(perf, "date", days), c.window(perf, "date", days, days)
    impressions, before = totals(current, IMPRESSIONS), totals(previous, IMPRESSIONS)
    actions, before_actions = totals(current, ACTIONS), totals(previous, ACTIONS)
    out.append(
        metric(
            "impressions",
            f"Impressions ({days}d)",
            "performance",
            impressions,
            previous=before,
            direction="up_is_good",
            basis=f"Sum of the four impression surfaces over {days} observed days.",
        )
    )
    out.append(
        metric(
            "actions",
            f"Customer actions ({days}d)",
            "performance",
            actions,
            previous=before_actions,
            direction="up_is_good",
            basis="Website clicks, calls and direction requests. Events, not unique customers.",
        )
    )
    out.append(
        metric(
            "action_rate",
            "Actions per impression",
            "performance",
            round(100 * actions / impressions, 2) if actions is not None and impressions else None,
            unit="percent",
            previous=(
                round(100 * before_actions / before, 2)
                if before_actions is not None and before
                else None
            ),
            direction="up_is_good",
            basis="Event intensity, not a conversion rate.",
        )
    )

    reviews = [
        r
        for r in c.window(c.rows("reviews"), "create_time", c.config.outcome_window_days)
        if number(r.get("star_rating"))
    ]
    replied = [r for r in reviews if r.get("reply_comment")]
    critical = [r for r in reviews if r["star_rating"] <= 3 and not r.get("reply_comment")]
    out.append(
        metric(
            "average_rating",
            f"Average rating ({c.config.outcome_window_days}d)",
            "reputation",
            round(sum(r["star_rating"] for r in reviews) / len(reviews), 2) if reviews else None,
            unit="rating",
            direction="up_is_good",
            basis="Mean of stored star ratings. Reviews are a self-selected sample.",
        )
    )
    out.append(
        metric(
            "review_volume",
            f"Reviews received ({c.config.outcome_window_days}d)",
            "reputation",
            float(len(reviews)) if reviews else None,
            direction="neutral",
            basis="Count of dated reviews in the window.",
        )
    )
    out.append(
        metric(
            "reply_rate",
            "Reviews with a reply",
            "reputation",
            round(100 * len(replied) / len(reviews), 1) if reviews else None,
            unit="percent",
            direction="up_is_good",
            basis="Reply state is current, not reconstructed for the window.",
        )
    )
    out.append(
        metric(
            "unanswered_critical",
            "Unanswered reviews rated 1-3",
            "reputation",
            float(len(critical)) if reviews else None,
            direction="down_is_good",
            basis="Current reply state for reviews in the window.",
        )
    )

    keywords = c.rows("keywords")
    latest: list[dict] = []
    for keyword in keywords:
        ranks = [
            r
            for r in c.rows("ranks")
            if r["tracked_keyword_id"] == keyword["id"]
            and day(r.get("week_start"))
            and day(r["week_start"]) <= c.as_of
        ]
        if ranks and c.fresh(ranks, "week_start"):
            latest.append(max(ranks, key=lambda r: r["week_start"]))
    in_pack = [r for r in latest if r.get("rank_in_local_pack") in (1, 2, 3)]
    found = [r["rank_absolute"] for r in latest if number(r.get("rank_absolute"))]
    out.append(
        metric(
            "keywords_tracked",
            "Keywords tracked",
            "visibility",
            float(len(keywords)) if keywords else None,
            basis="Tracked keywords stored for this location.",
        )
    )
    out.append(
        metric(
            "local_pack_presence",
            "Keywords in the local pack",
            "visibility",
            round(100 * len(in_pack) / len(latest), 1) if latest else None,
            unit="percent",
            direction="up_is_good",
            basis="Most recent fresh weekly check per keyword. Not found is not rank zero.",
        )
    )
    out.append(
        metric(
            "average_rank",
            "Average position where found",
            "visibility",
            round(sum(found) / len(found), 1) if found else None,
            unit="rank",
            direction="down_is_good",
            basis="Excludes checks where the listing was not found; sampled positions vary.",
        )
    )

    window = c.config.outcome_window_days
    visits = c.window(c.rows("bookings"), "requested_for_date", window)
    settled = [
        r
        for r in visits
        if day(r["requested_for_date"]) < c.as_of
        and r.get("status") in ("completed", "cancelled", "no_show")
    ]
    requests = c.window(c.rows("bookings"), "booking_created_at", days)
    out.append(
        metric(
            "settled_visits",
            f"Settled past visits ({window}d)",
            "operations",
            float(len(settled)) if settled else None,
            basis="Completed, cancelled or no-show appointments with a past date.",
        )
    )
    out.append(
        metric(
            "failed_visit_rate",
            "Cancelled or no-show",
            "operations",
            round(100 * sum(r["status"] != "completed" for r in settled) / len(settled), 1)
            if settled
            else None,
            unit="percent",
            direction="down_is_good",
            basis="Share of settled past visits that did not happen. Excludes unsettled statuses.",
        )
    )
    out.append(
        metric(
            "open_requests",
            f"Requests still marked new ({days}d)",
            "operations",
            float(sum(r.get("status") == "new" for r in requests)) if requests else None,
            direction="down_is_good",
            basis="CRM status as currently stored; may be stale.",
        )
    )

    posts = [
        r
        for r in c.rows("posts")
        if day(r.get("published_on")) and day(r["published_on"]) <= c.as_of
    ]
    out.append(
        metric(
            "days_since_post",
            "Days since last post",
            "content",
            float((c.as_of - day(max(posts, key=lambda r: r["published_on"])["published_on"])).days)
            if posts
            else None,
            unit="days",
            direction="down_is_good",
            basis="Latest dated post in the export; an incomplete export looks like a gap.",
        )
    )
    return out
