"""Reputation worker: what customers read about the business, and whether it answers.

Five groups of checks, all deterministic:

- Rating: is the average customers see above the level they act on, and are 1-star
  reviews a small share?
- Trend: has the rating fallen recently?
- Volume: does the review count hold up against the competitors seen on the same
  keywords?
- Recency: are reviews still arriving?
- Responsiveness: are reviews answered, are complaints answered, and how fast?

A review with no star rating is invalid for rating maths but still a stored review.
A blank reply is no reply. No reviews at all is unknown, never zero. A permanently
closed profile is not audited. Draft replies and themes are produced afterwards by the
suggestion layer, never here.
"""

from __future__ import annotations

from datetime import timedelta
from statistics import median
from typing import TYPE_CHECKING

from app.services.recommendations.grading import graded
from app.services.recommendations.values import day

if TYPE_CHECKING:
    from app.services.recommendations.context import Context

KEY = "reputation"
LABEL = "Reputation"
WEIGHT = 20

CRITICAL_STARS = (1, 2, 3)
COMMENT_PREVIEW_CHARS = 140


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
    group: str = "rating",
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
        # The field a suggestion may be drafted for. None: nothing to draft.
        "suggests": suggests,
    }


CHECKS: dict[str, dict] = {
    # Rating
    "rating_low": check(
        3,
        "Recent rating below the level customers act on",
        "The average star rating of reviews in the configured recent window against the "
        "warning and critical minimums.",
        "Look at the recent low reviews for a common cause, fix it, then ask happy "
        "customers to share a genuine review. Never offer anything in return.",
        predicate="have a low recent rating",
        predicate_one="has a low recent rating",
        suggests="themes",
    ),
    "one_star_share_high": check(
        2,
        "Too many 1-star reviews",
        "The share of reviews in the lookback window that are 1 star against the "
        "configured maximum.",
        "Read the 1-star reviews together and look for the repeated complaint. One fixed "
        "cause removes many future 1-star reviews.",
        predicate="have a high share of 1-star reviews",
        predicate_one="has a high share of 1-star reviews",
        suggests="themes",
    ),
    # Trend
    "rating_trend_falling": check(
        2,
        "Rating is falling",
        "The average rating of the last window against the window before it.",
        "Something changed recently. Compare the newest reviews with the older ones and "
        "find what customers started complaining about.",
        predicate="have a falling rating",
        predicate_one="has a falling rating",
        suggests="themes",
        group="trend",
    ),
    # Volume
    "reviews_few_vs_competitors": check(
        2,
        "Fewer reviews than competitors",
        "The stored review count against the median review count of the competitors "
        "observed on the location's keywords in their latest week.",
        "Build a steady habit of asking every satisfied customer for a review at the "
        "moment of service, with a direct link. Count is a ranking signal Google names.",
        predicate="trail competitors on review count",
        predicate_one="trails competitors on review count",
        group="volume",
        effort="afternoon",
    ),
    # Recency
    "no_recent_review": check(
        2,
        "No new review recently",
        "Days since the newest review against the configured maximum gap.",
        "Ask recent customers for a review. Profiles that stop receiving reviews lose "
        "ground within a few weeks, and customers read the dates.",
        predicate="have had no review recently",
        predicate_one="has had no review recently",
        group="recency",
    ),
    "review_velocity_low": check(
        1,
        "Few reviews in the last month",
        "Reviews received in the last 30 days against the configured monthly minimum.",
        "Set a monthly target and ask for reviews every day, not in bursts. Steady "
        "arrivals read as genuine.",
        predicate="received few reviews last month",
        predicate_one="received few reviews last month",
        group="recency",
    ),
    # Responsiveness
    "reply_rate_low": check(
        3,
        "Most reviews go unanswered",
        "The share of reviews older than the reply wait that carry an owner reply, "
        "against the configured minimum.",
        "Reply to every review, briefly and personally. Customers read the replies as "
        "much as the reviews, and Google says replying shows you value feedback.",
        predicate="answer too few reviews",
        predicate_one="answers too few reviews",
        group="responsiveness",
    ),
    "critical_reply_rate_low": check(
        2,
        "Complaints go unanswered",
        "The share of 1 to 3 star reviews older than the reply wait that carry an owner "
        "reply, against the configured minimum.",
        "Answer every low review first: thank, acknowledge the specific problem, "
        "apologise where warranted, and offer to resolve it offline.",
        predicate="answer too few low reviews",
        predicate_one="answers too few low reviews",
        group="responsiveness",
    ),
    "critical_review_unanswered": check(
        3,
        "Low review waiting for a reply",
        "1 to 3 star reviews older than the reply wait with no owner reply, newest first.",
        "Reply within a few days: thank the reviewer, acknowledge the specific concern, "
        "share no private details, and invite them to continue offline.",
        unit="review",
        predicate="are waiting for a reply",
        predicate_one="is waiting for a reply",
        subject="review",
        subject_predicate="are waiting for a reply",
        suggests="review_reply",
        group="responsiveness",
        effort="minutes",
    ),
    "reply_delay_high": check(
        2,
        "Replies take too long",
        "The median days between a review and its reply against the configured maximum.",
        "Check for new reviews at least every other day. Most customers expect a reply "
        "within a week, and complainers within three days.",
        predicate="reply slowly",
        predicate_one="replies slowly",
        group="responsiveness",
    ),
}


GROUPS = {
    "rating": ("rating_low", "one_star_share_high"),
    "trend": ("rating_trend_falling",),
    "volume": ("reviews_few_vs_competitors",),
    "recency": ("no_recent_review", "review_velocity_low"),
    "responsiveness": (
        "reply_rate_low",
        "critical_reply_rate_low",
        "critical_review_unanswered",
        "reply_delay_high",
    ),
}
GROUP_LABELS = {
    "rating": "Rating",
    "trend": "Trend",
    "volume": "Volume",
    "recency": "Recency",
    "responsiveness": "Responsiveness",
}
EFFORT = {
    "minutes": ("critical_review_unanswered",),
    "hour": (
        "rating_low",
        "one_star_share_high",
        "rating_trend_falling",
        "no_recent_review",
        "review_velocity_low",
        "reply_rate_low",
        "critical_reply_rate_low",
        "reply_delay_high",
    ),
    "afternoon": ("reviews_few_vs_competitors",),
}
for _group, _rules in GROUPS.items():
    for _rule in _rules:
        CHECKS[_rule]["group"] = _group
for _effort, _rules in EFFORT.items():
    for _rule in _rules:
        CHECKS[_rule]["effort"] = _effort
assert {r for rules in GROUPS.values() for r in rules} == set(CHECKS)
assert {r for rules in EFFORT.values() for r in rules} == set(CHECKS)


def stars(row: dict) -> int | None:
    """The rating as 1 to 5, or None when the row carries no usable rating."""
    value = row.get("star_rating")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = int(value)
    return value if 1 <= value <= 5 else None


def rated(rows: list[dict]) -> list[dict]:
    return [r for r in rows if stars(r) is not None]


def replied(row: dict) -> bool:
    text = row.get("reply_comment")
    return isinstance(text, str) and bool(text.strip())


def critical(row: dict) -> bool:
    return stars(row) in CRITICAL_STARS


def mean_stars(rows: list[dict]) -> float:
    return sum(stars(r) for r in rows) / len(rows)


def reply_delay(row: dict) -> int | None:
    """Days from review to reply, only when both dates are present."""
    created, answered = day(row.get("create_time")), day(row.get("reply_update_time"))
    if created is None or answered is None:
        return None
    return max(0, (answered - created).days)


def review_ref(row: dict) -> str:
    """A stable, non-identifying handle for a review: Google's id, else our own."""
    return str(row.get("google_review_id") or row.get("id"))


def preview(text) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= COMMENT_PREVIEW_CHARS:
        return text
    return text[:COMMENT_PREVIEW_CHARS].rsplit(" ", 1)[0] + "…"


def dated(rows: list[dict]) -> list[dict]:
    return [r for r in rows if day(r.get("create_time")) is not None]


def newest_first(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (str(r.get("create_time")), review_ref(r)), reverse=True)


def competitor_median_reviews(c: Context) -> tuple[float | None, list[dict]]:
    """Median across keywords of the competitors' review counts in each keyword's
    latest observed week. Rows with no count are ignored."""
    keyword_ids = {r["id"] for r in c.rows("keywords")}
    rows = [
        r
        for r in c.snapshot.get("competitors", [])
        if r.get("tracked_keyword_id") in keyword_ids
        and isinstance(r.get("review_count"), (int, float))
        and not isinstance(r.get("review_count"), bool)
    ]
    if not rows:
        return None, []
    latest_week: dict[str, str] = {}
    for r in rows:
        week = str(r.get("week_start") or "")
        if week > latest_week.get(r["tracked_keyword_id"], ""):
            latest_week[r["tracked_keyword_id"]] = week
    latest = [
        r for r in rows if str(r.get("week_start") or "") == latest_week[r["tracked_keyword_id"]]
    ]
    per_keyword = [
        median([r["review_count"] for r in latest if r["tracked_keyword_id"] == k])
        for k in latest_week
    ]
    return float(median(per_keyword)), latest


def evaluate(c: Context) -> None:
    loc = c.location
    href = f"/reviews?location_id={loc['id']}"
    if loc.get("open_status") == "closed_permanently":
        for rule in CHECKS:
            c.assess(rule, "suppressed", "Permanently closed: the profile is not audited.")
        return

    reviews = dated(c.rows("reviews"))
    _rating(c, reviews, href)
    _volume(c, reviews, href)
    _recency(c, reviews, href)
    _responsiveness(c, reviews, href)


def _rating(c: Context, reviews: list[dict], href: str) -> None:
    cfg = c.config
    window = rated(c.window(reviews, "create_time", cfg.rating_window_days))
    lookback = rated(c.window(reviews, "create_time", cfg.review_lookback_days))
    unrated = len(reviews) - len(rated(reviews))

    if len(window) < cfg.min_reviews:
        c.assess(
            "rating_low",
            "insufficient_data",
            f"{len(window)} rated reviews in the last {cfg.rating_window_days} days, "
            f"fewer than the {cfg.min_reviews} needed.",
        )
    else:
        average = mean_stars(window)
        if average < cfg.rating_warning_min:
            is_critical = average < cfg.rating_critical_min
            c.assess(
                "rating_low",
                "triggered",
                f"Average {average:.2f} over the last {cfg.rating_window_days} days, below "
                f"{cfg.rating_critical_min if is_critical else cfg.rating_warning_min}.",
                1,
            )
            c.emit(
                "rating_low",
                "Recent rating is " + ("well below" if is_critical else "below") + " 4 stars",
                CHECKS["rating_low"]["fix"],
                f"The {len(window)} reviews from the last {cfg.rating_window_days} days "
                f"average {average:.2f} stars; most customers filter at "
                f"{cfg.rating_warning_min:.1f}.",
                graded(75, (cfg.rating_critical_min - average) / 1.0, 15, 90)
                if is_critical
                else graded(50, (cfg.rating_warning_min - average) / 0.5, 20, 70),
                [
                    c.evidence(
                        "reviews",
                        window,
                        ["star_rating", "create_time"],
                        f"mean star_rating over the last {cfg.rating_window_days} days",
                        average=round(average, 2),
                        reviews=len(window),
                        unrated_excluded=unrated,
                        warning_min=cfg.rating_warning_min,
                        critical_min=cfg.rating_critical_min,
                    )
                ],
                href,
                "Reviews are a self-selected sample; the average describes what customers "
                "see, not service quality.",
                "high",
            )
        else:
            c.assess("rating_low", "clear", f"Average {average:.2f} over {len(window)} reviews.")

    if len(lookback) < cfg.min_reviews:
        c.assess(
            "one_star_share_high",
            "insufficient_data",
            f"{len(lookback)} rated reviews in the lookback, fewer than {cfg.min_reviews}.",
        )
    else:
        ones = [r for r in lookback if stars(r) == 1]
        share = len(ones) / len(lookback)
        if share > cfg.one_star_share_max:
            c.assess(
                "one_star_share_high",
                "triggered",
                f"{len(ones)} of {len(lookback)} reviews are 1 star ({share:.0%}).",
                1,
            )
            c.emit(
                "one_star_share_high",
                f"{share:.0%} of reviews are 1 star",
                CHECKS["one_star_share_high"]["fix"],
                f"{len(ones)} of the {len(lookback)} reviews from the last "
                f"{cfg.review_lookback_days} days are 1 star; the policy maximum is "
                f"{cfg.one_star_share_max:.0%}.",
                graded(45, (share - cfg.one_star_share_max) / 0.2, 25, 72),
                [
                    c.evidence(
                        "reviews",
                        ones,
                        ["star_rating", "create_time"],
                        "count of star_rating == 1 over rated reviews in the lookback",
                        one_star=len(ones),
                        rated=len(lookback),
                        share=round(share, 3),
                        maximum=cfg.one_star_share_max,
                    )
                ],
                href,
                "A share, not a cause. Read the reviews themselves before acting.",
                "high",
            )
        else:
            c.assess("one_star_share_high", "clear", f"{share:.0%} of reviews are 1 star.")

    recent = rated(c.window(reviews, "create_time", cfg.rating_window_days))
    prior = rated(
        c.window(reviews, "create_time", cfg.rating_window_days, offset=cfg.rating_window_days)
    )
    if len(recent) < cfg.min_reviews or len(prior) < cfg.min_reviews:
        c.assess(
            "rating_trend_falling",
            "insufficient_data",
            f"{len(recent)} recent and {len(prior)} prior rated reviews; both windows need "
            f"{cfg.min_reviews}.",
        )
    else:
        now, before = mean_stars(recent), mean_stars(prior)
        drop = before - now
        if drop > cfg.rating_drop_max:
            c.assess(
                "rating_trend_falling",
                "triggered",
                f"Average fell from {before:.2f} to {now:.2f}.",
                1,
            )
            c.emit(
                "rating_trend_falling",
                f"Rating fell from {before:.1f} to {now:.1f}",
                CHECKS["rating_trend_falling"]["fix"],
                f"Reviews from the last {cfg.rating_window_days} days average {now:.2f} "
                f"stars against {before:.2f} in the {cfg.rating_window_days} days before, "
                f"a drop of {drop:.2f}.",
                graded(45, (drop - cfg.rating_drop_max) / 1.0, 25, 72),
                [
                    c.evidence(
                        "reviews",
                        recent + prior,
                        ["star_rating", "create_time"],
                        "mean star_rating of the recent window minus the prior window",
                        recent_average=round(now, 2),
                        prior_average=round(before, 2),
                        recent_reviews=len(recent),
                        prior_reviews=len(prior),
                        maximum_drop=cfg.rating_drop_max,
                    )
                ],
                href,
                "Two window averages; small samples swing. Not a forecast.",
                "high",
            )
        else:
            c.assess("rating_trend_falling", "clear", f"Average {before:.2f} to {now:.2f}.")


def _volume(c: Context, reviews: list[dict], href: str) -> None:
    cfg = c.config
    benchmark, latest = competitor_median_reviews(c)
    if benchmark is None:
        c.assess(
            "reviews_few_vs_competitors",
            "insufficient_data",
            "No competitor review counts are stored for this location's keywords.",
        )
        return
    count = len(c.rows("reviews"))
    ratio = count / benchmark if benchmark else 1.0
    if ratio < cfg.competitor_review_ratio_min:
        c.assess(
            "reviews_few_vs_competitors",
            "triggered",
            f"{count} reviews against a competitor median of {benchmark:.0f}.",
            1,
        )
        c.emit(
            "reviews_few_vs_competitors",
            f"{count} reviews against competitors' {benchmark:.0f}",
            CHECKS["reviews_few_vs_competitors"]["fix"],
            f"The profile has {count} reviews; competitors seen on the same searches have "
            f"a median of {benchmark:.0f}. The policy floor is "
            f"{cfg.competitor_review_ratio_min:.0%} of that.",
            graded(
                30,
                (cfg.competitor_review_ratio_min - ratio) / cfg.competitor_review_ratio_min,
                25,
                55,
            ),
            [
                c.evidence(
                    "competitors",
                    latest,
                    ["tracked_keyword_id", "week_start", "review_count"],
                    "median over keywords of competitor review_count in each keyword's latest week",
                    competitor_median=round(benchmark),
                    stored_reviews=count,
                    ratio=round(ratio, 2),
                    minimum_ratio=cfg.competitor_review_ratio_min,
                )
            ],
            href,
            "Compares stored reviews with a scraped competitor figure; the two are not "
            "measured the same way.",
        )
    else:
        c.assess(
            "reviews_few_vs_competitors",
            "clear",
            f"{count} reviews against a competitor median of {benchmark:.0f}.",
        )


def _recency(c: Context, reviews: list[dict], href: str) -> None:
    cfg = c.config
    if not reviews:
        c.assess("no_recent_review", "insufficient_data", "No reviews are stored.")
        c.assess("review_velocity_low", "insufficient_data", "No reviews are stored.")
        return
    newest = newest_first(reviews)[0]
    gap = (c.as_of - day(newest["create_time"])).days
    if gap > cfg.review_gap_max_days:
        c.assess("no_recent_review", "triggered", f"Newest review is {gap} days old.", 1)
        c.emit(
            "no_recent_review",
            f"No review for {gap} days",
            CHECKS["no_recent_review"]["fix"],
            f"The newest review is {gap} days old; the policy maximum gap is "
            f"{cfg.review_gap_max_days} days.",
            graded(40, (gap - cfg.review_gap_max_days) / 60, 25, 65),
            [
                c.evidence(
                    "reviews",
                    [newest],
                    ["create_time"],
                    "as_of minus max(create_time)",
                    days_since_last=gap,
                    maximum=cfg.review_gap_max_days,
                )
            ],
            href,
            "Only reviews synced into Locus are counted.",
            "high",
        )
    else:
        c.assess("no_recent_review", "clear", f"Newest review is {gap} days old.")

    month = c.window(reviews, "create_time", 30)
    if len(month) < cfg.reviews_per_month_min:
        c.assess(
            "review_velocity_low",
            "triggered",
            f"{len(month)} reviews in the last 30 days, below {cfg.reviews_per_month_min}.",
            1,
        )
        c.emit(
            "review_velocity_low",
            f"{len(month)} {'review' if len(month) == 1 else 'reviews'} in the last 30 days",
            CHECKS["review_velocity_low"]["fix"],
            f"Only {len(month)} reviews arrived in the last 30 days; the policy minimum "
            f"is {cfg.reviews_per_month_min}.",
            graded(
                25, (cfg.reviews_per_month_min - len(month)) / cfg.reviews_per_month_min, 15, 40
            ),
            [
                c.evidence(
                    "reviews",
                    month,
                    ["create_time"],
                    "count of reviews with create_time in the last 30 days",
                    last_30_days=len(month),
                    minimum=cfg.reviews_per_month_min,
                )
            ],
            href,
            "A monthly count, sensitive to seasonality.",
            "high",
        )
    else:
        c.assess("review_velocity_low", "clear", f"{len(month)} reviews in the last 30 days.")


def _responsiveness(c: Context, reviews: list[dict], href: str) -> None:
    cfg = c.config
    lookback = c.window(reviews, "create_time", cfg.review_lookback_days)
    cutoff = c.as_of - timedelta(days=cfg.reply_wait_days)
    eligible = [r for r in lookback if day(r["create_time"]) <= cutoff]
    answered = [r for r in eligible if replied(r)]

    if len(eligible) < cfg.min_reviews:
        c.assess(
            "reply_rate_low",
            "insufficient_data",
            f"{len(eligible)} reviews old enough to expect a reply, fewer than {cfg.min_reviews}.",
        )
    else:
        rate = len(answered) / len(eligible)
        if rate < cfg.reply_rate_min:
            c.assess(
                "reply_rate_low",
                "triggered",
                f"{len(answered)} of {len(eligible)} reviews answered ({rate:.0%}).",
                len(eligible) - len(answered),
                len(eligible),
            )
            c.emit(
                "reply_rate_low",
                f"Only {rate:.0%} of reviews have a reply",
                CHECKS["reply_rate_low"]["fix"],
                f"{len(answered)} of the {len(eligible)} reviews older than "
                f"{cfg.reply_wait_days} days carry a reply ({rate:.0%}); the policy minimum "
                f"is {cfg.reply_rate_min:.0%}.",
                graded(45, (cfg.reply_rate_min - rate) / cfg.reply_rate_min, 30, 76),
                [
                    c.evidence(
                        "reviews",
                        eligible,
                        ["reply_comment", "create_time"],
                        "share of eligible reviews with a non-blank reply_comment",
                        answered=len(answered),
                        eligible=len(eligible),
                        rate=round(rate, 3),
                        minimum=cfg.reply_rate_min,
                    )
                ],
                href,
                "Reply state is current: a reply added later still counts. Reviews younger "
                "than the wait are excluded.",
                "high",
            )
        else:
            c.assess("reply_rate_low", "clear", f"{rate:.0%} of reviews answered.")

    low = [r for r in eligible if critical(r)]
    low_answered = [r for r in low if replied(r)]
    if len(low) < cfg.min_critical_reviews:
        c.assess(
            "critical_reply_rate_low",
            "insufficient_data",
            f"{len(low)} low reviews old enough to expect a reply, fewer than "
            f"{cfg.min_critical_reviews}.",
        )
    else:
        rate = len(low_answered) / len(low)
        if rate < cfg.critical_reply_rate_min:
            c.assess(
                "critical_reply_rate_low",
                "triggered",
                f"{len(low_answered)} of {len(low)} low reviews answered ({rate:.0%}).",
                len(low) - len(low_answered),
                len(low),
            )
            c.emit(
                "critical_reply_rate_low",
                f"Only {rate:.0%} of low reviews have a reply",
                CHECKS["critical_reply_rate_low"]["fix"],
                f"{len(low_answered)} of the {len(low)} reviews rated 1 to 3 stars and older "
                f"than {cfg.reply_wait_days} days carry a reply ({rate:.0%}); the policy "
                f"minimum is {cfg.critical_reply_rate_min:.0%}.",
                graded(
                    50, (cfg.critical_reply_rate_min - rate) / cfg.critical_reply_rate_min, 30, 80
                ),
                [
                    c.evidence(
                        "reviews",
                        low,
                        ["star_rating", "reply_comment", "create_time"],
                        "share of eligible 1 to 3 star reviews with a non-blank reply_comment",
                        answered=len(low_answered),
                        eligible=len(low),
                        rate=round(rate, 3),
                        minimum=cfg.critical_reply_rate_min,
                    )
                ],
                href,
                "Reply state is current, not historical.",
                "high",
            )
        else:
            c.assess("critical_reply_rate_low", "clear", f"{rate:.0%} of low reviews answered.")

    waiting = newest_first([r for r in low if not replied(r)])
    if not low:
        c.assess(
            "critical_review_unanswered",
            "insufficient_data",
            "No low review is old enough to expect a reply.",
        )
    elif waiting:
        c.assess(
            "critical_review_unanswered",
            "triggered",
            f"{len(waiting)} of {len(low)} low reviews have no reply.",
            len(waiting),
            len(low),
        )
        for row in waiting[: cfg.unanswered_list_max]:
            age = (c.as_of - day(row["create_time"])).days
            rating = stars(row)
            c.emit(
                "critical_review_unanswered",
                f"{rating}-star review from {age} days ago has no reply",
                CHECKS["critical_review_unanswered"]["fix"],
                f"A {rating}-star review posted {age} days ago has no owner reply"
                + (f": “{preview(row.get('comment'))}”" if preview(row.get("comment")) else ".")
                + " Customers reading it see silence.",
                graded(60 if rating == 1 else 50, (age - cfg.reply_wait_days) / 30, 20, 82),
                [
                    c.evidence(
                        "reviews",
                        [row],
                        ["star_rating", "create_time", "reply_comment"],
                        "star_rating <= 3, create_time older than reply_wait_days, "
                        "reply_comment blank",
                        rating=rating,
                        days_waiting=age,
                        review=review_ref(row),
                    )
                ],
                href,
                "A reply drafted here must be reviewed by a person before it is posted.",
                "high",
                subject=review_ref(row),
            )
    else:
        c.assess("critical_review_unanswered", "clear", f"All {len(low)} low reviews answered.")

    delays = [d for d in (reply_delay(r) for r in lookback if replied(r)) if d is not None]
    if len(delays) < cfg.min_reviews:
        c.assess(
            "reply_delay_high",
            "insufficient_data",
            f"{len(delays)} replies with both dates, fewer than {cfg.min_reviews}.",
        )
    else:
        typical = float(median(delays))
        if typical > cfg.reply_delay_max_days:
            c.assess(
                "reply_delay_high",
                "triggered",
                f"Median reply takes {typical:g} days.",
                1,
            )
            c.emit(
                "reply_delay_high",
                f"Replies take {typical:g} days on average",
                CHECKS["reply_delay_high"]["fix"],
                f"Across {len(delays)} answered reviews the median wait for a reply is "
                f"{typical:g} days; the policy maximum is {cfg.reply_delay_max_days}.",
                graded(35, (typical - cfg.reply_delay_max_days) / 14, 20, 55),
                [
                    c.evidence(
                        "reviews",
                        [r for r in lookback if replied(r) and reply_delay(r) is not None],
                        ["create_time", "reply_update_time"],
                        "median of reply_update_time minus create_time in days",
                        median_days=typical,
                        replies=len(delays),
                        maximum=cfg.reply_delay_max_days,
                    )
                ],
                href,
                "Uses the reply's last update time, which moves if a reply is edited.",
                "high",
            )
        else:
            c.assess("reply_delay_high", "clear", f"Median reply takes {typical:g} days.")


def card(snapshot: dict) -> dict:
    """The reviews as a customer sees them: rating, spread, and whether anyone answers."""
    loc = snapshot["locations"][0]
    reviews = [r for r in snapshot.get("reviews", []) if r.get("location_id") == loc["id"]]
    scored = rated(reviews)
    delays = [d for d in (reply_delay(r) for r in reviews if replied(r)) if d is not None]
    with_dates = newest_first(dated(reviews))
    waiting = newest_first([r for r in dated(reviews) if critical(r) and not replied(r)])
    return {
        "average": round(mean_stars(scored), 2) if scored else None,
        "count": len(reviews),
        "rated_count": len(scored),
        "distribution": {str(n): sum(1 for r in scored if stars(r) == n) for n in (5, 4, 3, 2, 1)},
        "replied_share": round(sum(1 for r in reviews if replied(r)) / len(reviews), 3)
        if reviews
        else None,
        "median_reply_days": float(median(delays)) if delays else None,
        "last_review_date": day(with_dates[0]["create_time"]).isoformat() if with_dates else None,
        "unanswered_critical_count": len(waiting),
        "unanswered": [
            {
                "id": review_ref(r),
                "rating": stars(r),
                "date": day(r["create_time"]).isoformat(),
                "comment": preview(r.get("comment")),
            }
            for r in waiting[:5]
        ],
    }
