from app.services.recommendations.context import Context, day, number
from app.services.recommendations.policy import graded

IMPRESSIONS = (
    "impressions_maps_desktop",
    "impressions_maps_mobile",
    "impressions_search_desktop",
    "impressions_search_mobile",
)
ACTIONS = ("website_clicks", "call_clicks", "direction_requests")


def bands(config) -> tuple[float, float]:
    """Report from the notice floor upward; treat twice the warning threshold as severe."""
    floor = min(config.decline_notice_fraction, config.decline_fraction)
    return floor, max(config.decline_fraction * 2, floor + 0.05)


def evaluate_performance(c: Context):
    if c.location.get("open_status") != "open":
        c.assess("performance", "suppressed", "Only compare active locations.")
        return
    days = c.config.window_days
    rows = c.rows("performance")
    current = c.window(rows, "date", days)
    previous = c.window(rows, "date", days, days)

    # Equal weekday windows plus exact overlap of observed positions prevents missing
    # days from becoming a decline. Both windows require all contributing measurements.
    def complete(row):
        return all(number(row.get(key)) for key in (*IMPRESSIONS, *ACTIONS))

    current_by_day = {(day(r["date"]) - c.as_of).days: r for r in current if complete(r)}
    previous_by_day = {(day(r["date"]) - c.as_of).days + days: r for r in previous if complete(r)}
    shared = sorted(current_by_day.keys() & previous_by_day.keys())
    if len(shared) / days < c.config.min_daily_coverage or not c.fresh(current, "date"):
        c.assess(
            "performance",
            "insufficient_data",
            f"Need paired daily coverage >= {c.config.min_daily_coverage:.0%} and fresh data.",
        )
        return
    a = [current_by_day[k] for k in shared]
    b = [previous_by_day[k] for k in shared]

    def total(rs, keys):
        return sum(r[k] for r in rs for k in keys)

    now, before = total(a, IMPRESSIONS), total(b, IMPRESSIONS)
    if min(now, before) < c.config.min_impressions:
        c.assess("performance", "insufficient_data", "Impression volume too small for comparison.")
        return
    decline = (before - now) / before
    now_actions, before_actions = total(a, ACTIONS), total(b, ACTIONS)
    old_rate = before_actions / before
    new_rate = now_actions / now
    rate_decline = (old_rate - new_rate) / old_rate if old_rate else 0
    worst = max(decline, rate_decline)
    floor, ceiling = bands(c.config)
    if worst < floor:
        c.assess(
            "performance",
            "clear",
            f"Largest measured fall {worst:.1%} is below the {floor:.0%} reporting floor.",
        )
        return
    visibility = decline >= rate_decline
    why = (
        f"Impressions fell {decline:.1%}, from {before:,} to {now:,}."
        if visibility
        else f"Action events per impression fell {rate_decline:.1%}, "
        f"from {old_rate:.2%} to {new_rate:.2%}."
    )
    c.assess("performance", "triggered", why, 1)
    c.emit(
        "performance",
        "Investigate a recent performance decline",
        "Review the affected dates and device/surface split. Check listing accuracy, "
        "website and phone availability, and local demand before selecting a remedy.",
        why + f" Compared {len(shared)} matched days in consecutive {days}-day windows.",
        graded(38, (worst - floor) / (ceiling - floor), 42, 80),
        [
            c.evidence(
                "performance",
                a + b,
                ["date", *IMPRESSIONS, *ACTIONS],
                "Matched offsets: sum impressions; actions / impressions; "
                "(previous - current) / previous",
                current_impressions=now,
                previous_impressions=before,
                impression_change=round(-decline, 6),
                current_actions=now_actions,
                previous_actions=before_actions,
                action_rate_change=round(-rate_decline, 6),
                matched_days=len(shared),
                window_days=days,
                current_start=min(r["date"] for r in a),
                current_end=max(r["date"] for r in a),
                previous_start=min(r["date"] for r in b),
                previous_end=max(r["date"] for r in b),
                reporting_floor=floor,
                warning_fraction=c.config.decline_fraction,
            )
        ],
        "/insights/performance",
        "Descriptive change, not attribution. Actions can repeat per customer and are not "
        "a conversion rate. Seasonality and partial reporting may contribute.",
    )


def evaluate_search(c: Context):
    if c.location.get("open_status") != "open":
        c.assess("search", "suppressed", "Only evaluate active locations.")
        return
    previous_month_end = c.as_of.replace(day=1).toordinal() - 1
    latest_month = c.as_of.fromordinal(previous_month_end)
    before_month = c.as_of.fromordinal(latest_month.replace(day=1).toordinal() - 1)
    months = (latest_month.strftime("%Y-%m"), before_month.strftime("%Y-%m"))
    rows = [
        r
        for r in c.rows("search_terms")
        if r.get("year_month") in months
        and not r.get("is_threshold")
        and number(r.get("impressions"))
    ]
    current = {r["search_term"]: r for r in rows if r["year_month"] == months[0]}
    previous = {r["search_term"]: r for r in rows if r["year_month"] == months[1]}
    paired = [(current[t], previous[t]) for t in sorted(current.keys() & previous.keys())]
    qualified = [
        (a, b)
        for a, b in paired
        if b["impressions"] >= c.config.min_impressions
        and (b["impressions"] - a["impressions"]) / b["impressions"] >= c.config.decline_fraction
    ]
    if not paired:
        c.assess(
            "search", "insufficient_data", "Need exact matching terms in two latest full months."
        )
        return
    if not qualified:
        c.assess("search", "clear", "No qualifying matched-term decline.")
        return
    lost = sum(b["impressions"] - a["impressions"] for a, b in qualified)
    c.assess(
        "search",
        "triggered",
        f"{len(qualified)} of {len(paired)} matched terms fell at least "
        f"{c.config.decline_fraction:.0%}, losing {lost:,} impressions.",
        len(qualified),
        len(paired),
    )
    # Every qualifying term is reported. A manager investigating lost visibility needs the
    # full list, not one representative; severity separates the large losses from the rest.
    ceiling = max(0.6, c.config.decline_fraction + 0.05)
    for a, b in sorted(
        qualified,
        key=lambda pair: (pair[0]["impressions"] - pair[1]["impressions"], pair[0]["search_term"]),
    ):
        share = (b["impressions"] - a["impressions"]) / b["impressions"]
        magnitude = (share - c.config.decline_fraction) / (ceiling - c.config.decline_fraction)
        c.emit(
            "search",
            f"Lost search visibility for “{a['search_term']}”",
            f"Inspect the listing and relevant website page for “{a['search_term']}”. "
            "Confirm actual services and compare demand before changing copy or categories.",
            f"“{a['search_term']}” fell {share:.0%}, from {b['impressions']:,} ({months[1]}) "
            f"to {a['impressions']:,} impressions ({months[0]}).",
            graded(42, magnitude, 26, 68),
            [
                c.evidence(
                    "search_terms",
                    [a, b],
                    ["search_term", "year_month", "impressions"],
                    "Compare same exact term in consecutive complete months",
                    search_term=a["search_term"],
                    previous=b["impressions"],
                    current=a["impressions"],
                    lost_impressions=b["impressions"] - a["impressions"],
                    decline_share=round(share, 4),
                    threshold=c.config.decline_fraction,
                )
            ],
            "/insights/search-terms",
            "Search-term reporting is truncated. Missing terms are not treated as zero; "
            "this does not establish demand or a service the business offers.",
            subject=a["search_term"],
        )
