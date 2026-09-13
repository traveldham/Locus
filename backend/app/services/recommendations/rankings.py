from datetime import timedelta

from app.services.recommendations.context import Context, day, number
from app.services.recommendations.policy import graded

WEEKS = 4
MIN_WEEKS_OUTSIDE_PACK = 3


def valid_series(ranks: list[dict]) -> bool:
    """Reject a keyword unless four consecutive weekly checks are internally coherent."""
    if any(
        day(b["week_start"]) - day(a["week_start"]) != timedelta(days=7)
        for a, b in zip(ranks, ranks[1:])
    ):
        return False
    return not any(
        r.get("found") not in (True, False)
        or (
            r.get("found") is True
            and (not number(r.get("rank_absolute")) or r["rank_absolute"] < 1)
        )
        or (
            r.get("found") is False
            and (r.get("rank_absolute") is not None or r.get("rank_in_local_pack") is not None)
        )
        or (r.get("rank_in_local_pack") is not None and r["rank_in_local_pack"] not in (1, 2, 3))
        for r in ranks
    )


def evaluate_rankings(c: Context):
    if c.location.get("open_status") != "open":
        c.assess("rankings", "suppressed", "Only evaluate active locations.")
        return
    candidates = []
    evaluated = 0
    for keyword in c.rows("keywords"):
        ranks = sorted(
            [
                r
                for r in c.rows("ranks")
                if r["tracked_keyword_id"] == keyword["id"]
                and day(r.get("week_start"))
                and day(r["week_start"]) <= c.as_of
            ],
            key=lambda r: r["week_start"],
        )[-WEEKS:]
        if len(ranks) < WEEKS or not c.fresh(ranks, "week_start") or not valid_series(ranks):
            continue
        evaluated += 1
        off_pack = sum(r.get("rank_in_local_pack") is None for r in ranks)
        if off_pack < MIN_WEEKS_OUTSIDE_PACK:
            continue
        rivals = [
            r
            for r in c.snapshot.get("competitors", [])
            if r["tracked_keyword_id"] == keyword["id"]
            and r["week_start"] == ranks[-1]["week_start"]
            and number(r.get("rank_absolute"))
            and (not ranks[-1]["found"] or r["rank_absolute"] < ranks[-1]["rank_absolute"])
        ]
        candidates.append((off_pack, keyword, ranks, rivals))
    if not evaluated:
        c.assess(
            "rankings", "insufficient_data", "Need four consecutive fresh valid weekly checks."
        )
        return
    if not candidates:
        c.assess(
            "rankings",
            "clear",
            f"None of {evaluated} evaluated keywords missed the local pack "
            f"in {MIN_WEEKS_OUTSIDE_PACK} of {WEEKS} checks.",
        )
        return
    c.assess(
        "rankings",
        "triggered",
        f"{len(candidates)} of {evaluated} evaluated keywords missed the local pack "
        f"in at least {MIN_WEEKS_OUTSIDE_PACK} of {WEEKS} consecutive checks.",
        len(candidates),
        evaluated,
    )
    # Every persistently off-pack keyword is reported. Selecting one representative hid
    # how wide the gap was; severity and the keyword list carry that instead.
    for off_pack, keyword, ranks, rivals in sorted(
        candidates, key=lambda x: (-x[0], x[1]["keyword"])
    ):
        never_found = all(r["found"] is False for r in ranks)
        magnitude = 1.0 if never_found else (off_pack - MIN_WEEKS_OUTSIDE_PACK + 1) / 2
        best = [r["rank_absolute"] for r in ranks if number(r.get("rank_absolute"))]
        evidence = [
            c.evidence(
                "ranks",
                ranks,
                ["week_start", "rank_absolute", "rank_in_local_pack", "found"],
                f"Count weeks outside local pack in {WEEKS} consecutive checks",
                keyword=keyword["keyword"],
                outside_pack=off_pack,
                weeks=WEEKS,
                never_found=never_found,
                best_absolute_rank=min(best) if best else None,
            ),
            c.evidence(
                "keywords",
                [keyword],
                ["keyword", "device", "search_intent"],
                "Keyword and device context",
                keyword=keyword["keyword"],
                device=keyword.get("device"),
            ),
        ]
        if rivals:
            evidence.append(
                c.evidence(
                    "competitors",
                    rivals,
                    [
                        "competitor_name",
                        "week_start",
                        "rank_absolute",
                        "review_count",
                        "average_rating",
                        "photo_count",
                    ],
                    "Rivals ahead on the same keyword and latest week",
                    ahead=len(rivals),
                    rivals=[
                        {
                            k: r[k]
                            for k in (
                                "competitor_name",
                                "rank_absolute",
                                "review_count",
                                "average_rating",
                                "photo_count",
                            )
                        }
                        for r in rivals
                    ],
                )
            )
        c.emit(
            "rankings",
            f"Outside the local pack for “{keyword['keyword']}”",
            f"Check the result URL and listing relevance for “{keyword['keyword']}” "
            f"on {keyword.get('device') or 'the tracked device'}. "
            "Compare observed competitors and verify service relevance before changing anything.",
            f"This keyword missed the local pack in {off_pack} of {WEEKS} consecutive checks"
            + (
                ". It was not found in the tracked results at all."
                if never_found
                else f", best observed position {min(best)}."
                if best
                else "."
            ),
            graded(50, magnitude, 22, 72),
            evidence,
            "/market/rankings",
            "Sampled positions depend on query, device and geography. "
            "Competitor differences are descriptive and do not establish why they rank.",
            subject=keyword["keyword"],
        )
