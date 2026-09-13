"""Content worker: every check passes, fails, or abstains for the right reason.

Mutation tests: change one input, one verdict changes. Missing evidence abstains.
"""

from datetime import date, timedelta

from app.services.recommendations.categories import content
from app.services.recommendations.engine import analyze, run_worker
from app.services.recommendations.types import EngineConfig

AS_OF = date(2026, 9, 14)
LOC = "loc-1"


def post(n: int, days_ago: int, kind: str = "standard", cta: str | None = "book") -> dict:
    return {
        "id": f"post-{n}",
        "location_id": LOC,
        "google_post_id": f"g-{n}",
        "post_type": kind,
        "summary": f"Post number {n} about a service we offer.",
        "cta_type": cta,
        "published_on": (AS_OF - timedelta(days=days_ago)).isoformat(),
    }


def complete() -> dict:
    """A profile that passes every content check."""
    kinds = ("standard", "offer", "event")
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
        "media": [
            {
                "id": "m1",
                "location_id": LOC,
                "photo_count": 44,
                "interior_photo_count": 15,
                "exterior_photo_count": 14,
                "team_photo_count": 10,
                "video_count": 4,
                "has_profile_photo": True,
                "has_cover_photo": True,
                "last_photo_uploaded_on": "2026-08-29",
            }
        ],
        # Eight posts, one every twelve days, three types, every one with a button.
        "posts": [post(n, 5 + 12 * n, kinds[n % 3]) for n in range(8)],
        "projects": [
            {
                "id": "p1",
                "name": "Brightpath Dental Group",
                "website_url": "https://example.org",
                "description": "Family dental group.",
                "services": ["Routine cleaning", "Teeth whitening", "Invisalign"],
                "slug": "bdg",
                "status": "active",
            }
        ],
    }


def verdicts(snapshot, config=None):
    result = run_worker(snapshot, AS_OF, config or EngineConfig(), "content")
    return {e["rule"]: e for e in result["evaluations"]}, result["items"]


def finding(items, rule, subject=""):
    return next(i for i in items if i["rule"] == rule and i["subject"] == subject)


def test_every_check_is_declared_and_assessed_exactly_once():
    states, items = verdicts(complete())
    assert set(states) == set(content.CHECKS)
    assert all(v["state"] == "clear" for v in states.values()), {
        k: v["reason"] for k, v in states.items() if v["state"] != "clear"
    }
    assert items == []
    report = analyze(complete(), AS_OF)
    score = next(
        c for c in report["location"]["health"]["categories"] if c["category"] == "content"
    )
    assert score["score"] == 100 and score["checks_passed"] == len(content.CHECKS)
    assert score["checks_not_evaluated"] == 0
    assert content.WEIGHT == 10 and score["weight"] == 10


def test_permanently_closed_suppresses_everything():
    snapshot = complete()
    snapshot["locations"][0]["open_status"] = "closed_permanently"
    states, items = verdicts(snapshot)
    assert all(v["state"] == "suppressed" for v in states.values()) and items == []


def test_missing_media_row_abstains_every_photo_check():
    snapshot = complete()
    snapshot["media"] = []
    states, items = verdicts(snapshot)
    for rule in content.GROUPS["photos"]:
        assert states[rule]["state"] == "insufficient_data"
    for rule in content.GROUPS["posts"]:
        assert states[rule]["state"] == "clear"
    assert items == []


def test_null_counts_abstain_only_their_own_check():
    snapshot = complete()
    row = snapshot["media"][0]
    row["photo_count"] = None
    row["team_photo_count"] = None
    row["video_count"] = None
    row["last_photo_uploaded_on"] = None
    states, _ = verdicts(snapshot)
    assert states["photos_few"]["state"] == "insufficient_data"
    assert states["photos_below_target"]["state"] == "insufficient_data"
    assert states["video_missing"]["state"] == "insufficient_data"
    assert states["photos_stale"]["state"] == "insufficient_data"
    # Interior and exterior are still known and non-zero.
    assert states["photo_type_empty"]["state"] == "clear"
    assert states["photo_type_empty"]["reason"] == "All 2 photo types have photos."


def test_photo_floor_and_target():
    snapshot = complete()
    snapshot["media"][0]["photo_count"] = 3
    states, items = verdicts(snapshot)
    assert states["photos_few"]["state"] == "triggered"
    assert states["photos_below_target"]["state"] == "suppressed"
    few = finding(items, "photos_few")
    assert few["severity"] == "warning" and few["evidence"][0]["row_ids"] == ["m1"]
    assert few["evidence"][0]["values"] == {"photo_count": 3, "floor": 10}

    snapshot["media"][0]["photo_count"] = 18
    states, items = verdicts(snapshot)
    assert states["photos_few"]["state"] == "clear"
    assert states["photos_below_target"]["state"] == "triggered"
    assert finding(items, "photos_below_target")["severity"] == "notice"
    assert (
        verdicts(snapshot, EngineConfig(content_photo_target=15))[0]["photos_below_target"]["state"]
        == "clear"
    )
    assert (
        verdicts(snapshot, EngineConfig(content_photo_floor=20))[0]["photos_few"]["state"]
        == "triggered"
    )


def test_empty_photo_types_enumerate_one_finding_each():
    snapshot = complete()
    snapshot["media"][0]["interior_photo_count"] = 0
    snapshot["media"][0]["team_photo_count"] = 0
    states, items = verdicts(snapshot)
    verdict = states["photo_type_empty"]
    assert verdict["state"] == "triggered"
    assert verdict["issues"] == 2 and verdict["evaluated"] == 3
    subjects = sorted(i["subject"] for i in items if i["rule"] == "photo_type_empty")
    assert subjects == ["interior", "team"]
    interior = finding(items, "photo_type_empty", "interior")
    assert interior["severity"] == "warning"
    assert interior["key"] == f"{LOC}:photo_type_empty:interior"
    assert interior["evidence"][0]["fields"] == ["interior_photo_count"]


def test_video_and_stale_upload():
    snapshot = complete()
    snapshot["media"][0]["video_count"] = 0
    snapshot["media"][0]["last_photo_uploaded_on"] = "2025-12-04"
    states, items = verdicts(snapshot)
    assert states["video_missing"]["state"] == "triggered"
    assert finding(items, "video_missing")["severity"] == "notice"
    assert states["photos_stale"]["state"] == "triggered"
    stale = finding(items, "photos_stale")
    assert stale["severity"] == "warning"
    assert stale["evidence"][0]["values"]["days"] == 284
    assert (
        verdicts(snapshot, EngineConfig(content_photo_stale_days=365))[0]["photos_stale"]["state"]
        == "clear"
    )
    # No photos at all: staleness is covered by the floor, not counted twice.
    snapshot["media"][0]["photo_count"] = 0
    states, _ = verdicts(snapshot)
    assert states["photos_few"]["state"] == "triggered"
    assert states["photos_stale"]["state"] == "suppressed"


def test_no_posts_at_all_is_reported_with_medium_confidence():
    snapshot = complete()
    snapshot["posts"] = []
    states, items = verdicts(snapshot)
    assert states["posts_none_recent"]["state"] == "triggered"
    never = finding(items, "posts_none_recent")
    assert never["severity"] == "critical" and never["confidence"] == "medium"
    assert "export" in never["limitation"]
    assert states["posts_sparse"]["state"] == "suppressed"
    assert states["post_types_uniform"]["state"] == "insufficient_data"
    assert states["posts_without_cta"]["state"] == "insufficient_data"


def test_post_gap_and_cadence():
    snapshot = complete()
    # Shift every post back six weeks: the gap fires, and only two land in 90 days.
    for row in snapshot["posts"]:
        row["published_on"] = (
            date.fromisoformat(row["published_on"]) - timedelta(days=42)
        ).isoformat()
    states, items = verdicts(snapshot)
    assert states["posts_none_recent"]["state"] == "triggered"
    gap = finding(items, "posts_none_recent")
    assert gap["severity"] == "warning" and gap["evidence"][0]["values"]["days"] == 47
    assert states["posts_sparse"]["state"] == "triggered"
    sparse = finding(items, "posts_sparse")
    assert sparse["evidence"][0]["values"]["posts_90d"] == 4
    assert (
        verdicts(snapshot, EngineConfig(content_post_gap_days=60, content_posts_min_90d=4))[0][
            "posts_sparse"
        ]["state"]
        == "clear"
    )
    # Every post older than 90 days: the cadence check defers to the gap check.
    for row in snapshot["posts"]:
        row["published_on"] = (
            date.fromisoformat(row["published_on"]) - timedelta(days=60)
        ).isoformat()
    states, _ = verdicts(snapshot)
    assert states["posts_none_recent"]["state"] == "triggered"
    assert states["posts_sparse"]["state"] == "suppressed"


def test_post_mix_and_cta_share():
    snapshot = complete()
    for row in snapshot["posts"]:
        row["post_type"] = "STANDARD"  # upper-case as the raw export spells it
    states, items = verdicts(snapshot)
    assert states["post_types_uniform"]["state"] == "triggered"
    uniform = finding(items, "post_types_uniform")
    assert uniform["severity"] == "notice" and "update" in uniform["title"]
    assert states["posts_without_cta"]["state"] == "clear"

    for row in snapshot["posts"][:6]:
        row["cta_type"] = None
    states, items = verdicts(snapshot)
    assert states["posts_without_cta"]["state"] == "triggered"
    assert states["posts_without_cta"]["issues"] == 6
    assert states["posts_without_cta"]["evaluated"] == 8
    assert finding(items, "posts_without_cta")["severity"] == "notice"
    assert (
        verdicts(snapshot, EngineConfig(content_post_cta_max_missing_share=0.8))[0][
            "posts_without_cta"
        ]["state"]
        == "clear"
    )

    # Too few posts in the window to judge either.
    snapshot["posts"] = snapshot["posts"][:2]
    states, _ = verdicts(snapshot)
    assert states["post_types_uniform"]["state"] == "insufficient_data"
    assert states["posts_without_cta"]["state"] == "insufficient_data"


def test_posts_without_a_date_are_ignored():
    snapshot = complete()
    snapshot["posts"].append(post(99, 0, cta=None) | {"published_on": None})
    states, _ = verdicts(snapshot)
    assert states["posts_without_cta"]["reason"] == "0 of 8 posts without a call to action."


def test_card_reports_coverage_and_timeline():
    snapshot = complete()
    snapshot["as_of"] = AS_OF.isoformat()
    card = content.card(snapshot)
    assert card["has_media_summary"] is True
    assert card["photos"] == {
        "total": 44,
        "interior": 15,
        "exterior": 14,
        "team": 10,
        "other": 5,
        "videos": 4,
        "last_uploaded_on": "2026-08-29",
        "days_since_upload": 16,
    }
    posts = card["posts"]
    assert posts["total"] == 8 and posts["in_90_days"] == 8
    assert posts["last_published_on"] == "2026-09-09" and posts["days_since_post"] == 5
    assert posts["last_type"] == "standard" and posts["cta_share"] == 1.0
    assert posts["type_mix"] == {"standard": 3, "offer": 3, "event": 2}
    assert len(posts["recent"]) == 5
    assert posts["recent"][0] == {
        "type": "standard",
        "published_on": "2026-09-09",
        "summary": "Post number 0 about a service we offer.",
        "cta": "book",
    }

    snapshot["media"] = []
    snapshot["posts"] = []
    card = content.card(snapshot)
    assert card["has_media_summary"] is False
    assert card["photos"]["total"] is None and card["photos"]["days_since_upload"] is None
    assert card["posts"]["total"] == 0 and card["posts"]["recent"] == []
