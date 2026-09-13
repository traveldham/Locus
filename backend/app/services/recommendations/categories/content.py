"""Content worker: does the profile show customers what the place looks like, and does
it say anything new?

Two groups of checks, all deterministic:

- Photos: enough of them, every named type covered, a video, something recent.
- Posts: one recently, enough of them, more than one type, a next step for the reader.

Photo checks read the media summary, a rollup of counts. An absent row is unknown, a
null count is unknown for that type; both abstain. Posts are events: zero rows over a
window is an observation, reported with medium confidence because an incomplete export
looks the same. Posts are scored as conversion hygiene, never as a ranking factor. The
logo and cover photo flags belong to the profile worker and are not repeated here.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import TYPE_CHECKING

from app.services.recommendations.grading import graded
from app.services.recommendations.values import day, number

if TYPE_CHECKING:
    from app.services.recommendations.context import Context

KEY = "content"
LABEL = "Content"
WEIGHT = 10

PHOTO_TYPES = (
    ("interior", "interior_photo_count"),
    ("exterior", "exterior_photo_count"),
    ("team", "team_photo_count"),
)
POST_TYPE_LABELS = {
    "standard": "update",
    "event": "event",
    "offer": "offer",
    "alert": "alert",
}
HREF_PHOTOS = "/insights/photos"
HREF_POSTS = "/insights/posts"


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
    group: str = "photos",
    effort: str = "hour",
) -> dict:
    return {
        "weight": weight,
        # Which of the two groups the check belongs to, for the completeness strip.
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
        # The content a suggestion may be drafted for: post_drafts or photo_shot_list.
        "suggests": suggests,
    }


CHECKS: dict[str, dict] = {
    # Photos
    "photos_few": check(
        3,
        "Very few photos",
        "Whether the photo count reaches the configured floor.",
        "Add photos of the outside, the inside and the team. Listings with photos get "
        "more direction requests and website clicks than listings without.",
        predicate="have very few photos",
        predicate_one="has very few photos",
        suggests="photo_shot_list",
    ),
    "photos_below_target": check(
        1,
        "Photos below target",
        "Whether the photo count reaches the configured working target.",
        "Keep adding photos until the profile shows the whole experience: entrance, "
        "waiting area, treatment rooms, equipment, staff at work.",
        predicate="have fewer photos than the target",
        predicate_one="has fewer photos than the target",
        suggests="photo_shot_list",
    ),
    "photo_type_empty": check(
        2,
        "A photo type has no photos",
        "Photo types Google names, interior, exterior and team, with a count of zero.",
        "Add at least a few photos of that type. Each type answers a different customer "
        "question: can I find it, what is it like inside, who will I meet.",
        unit="photo type",
        predicate="have no photos",
        predicate_one="has no photos",
        subject="photo type",
        subject_predicate="have no photos",
        suggests="photo_shot_list",
    ),
    "video_missing": check(
        1,
        "No video",
        "Whether the profile has at least one video.",
        "Upload a short video: a walk from the door to the front desk, or the team "
        "saying hello. Google accepts up to 30 seconds at 720p.",
        predicate="have no video",
        predicate_one="has no video",
    ),
    "photos_stale": check(
        2,
        "No recent photo",
        "Days since the last photo upload against the configured limit.",
        "Upload a few new photos. A profile whose newest photo is months old reads as "
        "unattended, and customers look at dates.",
        predicate="have no recent photo",
        predicate_one="has no recent photo",
    ),
    # Posts
    "posts_none_recent": check(
        3,
        "No recent post",
        "Days since the last post, or whether any post exists, against the configured gap.",
        "Publish a post: an update, an offer or an event. Posts show on the profile and "
        "give a customer a next step. They do not move rank; they move clicks.",
        predicate="have no recent post",
        predicate_one="has no recent post",
        suggests="post_drafts",
        group="posts",
    ),
    "posts_sparse": check(
        2,
        "Too few posts in the last 90 days",
        "Posts published in the last 90 days against the configured minimum.",
        "Post about once every two weeks. A simple rota of update, offer, event keeps "
        "the profile current without much effort.",
        predicate="post too rarely",
        predicate_one="posts too rarely",
        suggests="post_drafts",
        group="posts",
    ),
    "post_types_uniform": check(
        1,
        "Posts are all one type",
        "Whether the posts in the six-month window use more than one post type.",
        "Mix in an offer or an event. Those types carry a date and a built-in button, "
        "so they do more than a plain update.",
        predicate="use only one post type",
        predicate_one="uses only one post type",
        suggests="post_drafts",
        group="posts",
    ),
    "posts_without_cta": check(
        1,
        "Posts without a call to action",
        "The share of posts in the six-month window with no call to action button.",
        "Add a button to each post: Book, Call, Learn more or Sign up. A post without "
        "a next step is a missed click.",
        predicate="publish posts without a button",
        predicate_one="publishes posts without a button",
        suggests="post_drafts",
        group="posts",
    ),
}

GROUPS = {
    "photos": (
        "photos_few",
        "photos_below_target",
        "photo_type_empty",
        "video_missing",
        "photos_stale",
    ),
    "posts": ("posts_none_recent", "posts_sparse", "post_types_uniform", "posts_without_cta"),
}
GROUP_LABELS = {"photos": "Photos", "posts": "Posts"}
EFFORT = {
    "minutes": ("posts_none_recent", "posts_without_cta"),
    "hour": ("photos_stale", "posts_sparse", "post_types_uniform", "video_missing"),
    "afternoon": ("photos_few", "photos_below_target", "photo_type_empty"),
}
for _group, _rules in GROUPS.items():
    for _rule in _rules:
        CHECKS[_rule]["group"] = _group
for _effort, _rules in EFFORT.items():
    for _rule in _rules:
        CHECKS[_rule]["effort"] = _effort
assert {r for rules in GROUPS.values() for r in rules} == set(CHECKS)
assert {r for rules in EFFORT.values() for r in rules} == set(CHECKS)


def count(value) -> int | None:
    """A non-negative integer count, or None for unknown."""
    return int(value) if number(value) else None


def post_type(row: dict) -> str:
    return str(row.get("post_type") or "").casefold()


def has_cta(row: dict) -> bool:
    return bool(str(row.get("cta_type") or "").strip())


def dated_posts(rows: list[dict]) -> list[dict]:
    """Posts with a readable publish date, newest first."""
    return sorted(
        (r for r in rows if day(r.get("published_on"))),
        key=lambda r: day(r["published_on"]),
        reverse=True,
    )


def evaluate(c: Context) -> None:
    loc = c.location
    if loc.get("open_status") == "closed_permanently":
        for rule in CHECKS:
            c.assess(rule, "suppressed", "Permanently closed: the profile is not audited.")
        return
    _photos(c)
    _posts(c)


def _photos(c: Context) -> None:
    media = c.rows("media")
    if not media:
        for rule in GROUPS["photos"]:
            c.assess(rule, "insufficient_data", "No photo summary is stored.")
        return
    row = media[0]
    floor, target = c.config.content_photo_floor, c.config.content_photo_target

    photos = count(row.get("photo_count"))
    if photos is None:
        c.assess("photos_few", "insufficient_data", "The photo count is unknown.")
        c.assess("photos_below_target", "insufficient_data", "The photo count is unknown.")
    elif photos < floor:
        c.assess("photos_few", "triggered", f"{photos} photos, below the floor of {floor}.", 1)
        c.emit(
            "photos_few",
            "Add photos" if photos else "Add the first photos",
            CHECKS["photos_few"]["fix"],
            f"The profile has {photos} {'photo' if photos == 1 else 'photos'}; the policy "
            f"floor is {floor}. The median listing in industry studies has about 11.",
            graded(50, (floor - photos) / floor, 20, 70),
            [
                c.evidence(
                    "media",
                    [row],
                    ["photo_count"],
                    "photo_count < floor",
                    photo_count=photos,
                    floor=floor,
                )
            ],
            HREF_PHOTOS,
            "A count from the summary, not an inspection of the photos. Includes customer uploads.",
            "high",
        )
        c.assess(
            "photos_below_target",
            "suppressed",
            "Already below the floor; counted under the photo floor check.",
        )
    else:
        c.assess("photos_few", "clear", f"{photos} photos, at or above the floor of {floor}.")
        if photos < target:
            c.assess(
                "photos_below_target",
                "triggered",
                f"{photos} photos, below the target of {target}.",
                1,
            )
            c.emit(
                "photos_below_target",
                "Add more photos",
                CHECKS["photos_below_target"]["fix"],
                f"The profile has {photos} photos; the working target is {target}.",
                graded(15, (target - photos) / max(1, target - floor), 15, 30),
                [
                    c.evidence(
                        "media",
                        [row],
                        ["photo_count"],
                        "photo_count < target",
                        photo_count=photos,
                        target=target,
                    )
                ],
                HREF_PHOTOS,
                "The target is an operating policy. The 100+ tier in industry studies is "
                "a correlation with busy listings, not a rule.",
                "high",
            )
        else:
            c.assess("photos_below_target", "clear", f"{photos} photos, at or above {target}.")

    known = [(name, field, count(row.get(field))) for name, field in PHOTO_TYPES]
    known = [(n, f, v) for n, f, v in known if v is not None]
    empty = [(n, f) for n, f, v in known if v == 0]
    if not known:
        c.assess("photo_type_empty", "insufficient_data", "No photo type counts are stored.")
    elif empty:
        c.assess(
            "photo_type_empty",
            "triggered",
            f"{len(empty)} of {len(known)} photo types have no photos.",
            len(empty),
            len(known),
        )
        for name, field in empty:
            c.emit(
                "photo_type_empty",
                f"No {name} photos",
                CHECKS["photo_type_empty"]["fix"],
                f"The profile has no {name} photos.",
                graded(45, (len(empty) - 1) / max(1, len(known) - 1), 15, 60),
                [c.evidence("media", [row], [field], f"{field} == 0", photo_type=name)],
                HREF_PHOTOS,
                "A count of zero in the summary. Uncategorised photos are not counted "
                "against any type.",
                "high",
                subject=name,
            )
    else:
        c.assess("photo_type_empty", "clear", f"All {len(known)} photo types have photos.")

    videos = count(row.get("video_count"))
    if videos is None:
        c.assess("video_missing", "insufficient_data", "The video count is unknown.")
    elif videos == 0:
        c.assess("video_missing", "triggered", "No video is stored.", 1)
        c.emit(
            "video_missing",
            "Add a short video",
            CHECKS["video_missing"]["fix"],
            "The profile has no video.",
            22,
            [c.evidence("media", [row], ["video_count"], "video_count == 0")],
            HREF_PHOTOS,
            "Video is a nice-to-have. Many strong profiles have none.",
            "high",
        )
    else:
        c.assess("video_missing", "clear", f"{videos} {'video' if videos == 1 else 'videos'}.")

    uploaded = day(row.get("last_photo_uploaded_on"))
    limit = c.config.content_photo_stale_days
    if uploaded is None:
        c.assess("photos_stale", "insufficient_data", "The last upload date is unknown.")
    elif photos == 0:
        c.assess("photos_stale", "suppressed", "No photos at all; counted under the floor.")
    else:
        age = (c.as_of - uploaded).days
        if age > limit:
            c.assess("photos_stale", "triggered", f"Last upload {age} days ago, over {limit}.", 1)
            c.emit(
                "photos_stale",
                "Upload new photos",
                CHECKS["photos_stale"]["fix"],
                f"The newest photo was uploaded {age} days ago, on {uploaded}; the policy "
                f"limit is {limit} days.",
                graded(45, (age - limit) / limit, 15, 60),
                [
                    c.evidence(
                        "media",
                        [row],
                        ["last_photo_uploaded_on"],
                        "as_of - last_photo_uploaded_on",
                        days=age,
                        limit=limit,
                    )
                ],
                HREF_PHOTOS,
                "Counts days to the analysis date, which may be after the last export.",
                "high",
            )
        else:
            c.assess("photos_stale", "clear", f"Last upload {age} days ago.")


def _posts(c: Context) -> None:
    posts = dated_posts(c.rows("posts"))
    gap = c.config.content_post_gap_days
    window_days = c.config.content_post_window_days
    minimum = c.config.content_posts_min_90d
    mix_min = c.config.content_post_mix_min_posts
    cta_max = c.config.content_post_cta_max_missing_share

    if not posts:
        c.assess("posts_none_recent", "triggered", "No post has ever been stored.", 1)
        c.emit(
            "posts_none_recent",
            "Publish the first post",
            CHECKS["posts_none_recent"]["fix"],
            "No post is stored for this profile.",
            75,
            [c.evidence("posts", [], ["published_on"], "zero post rows")],
            HREF_POSTS,
            "Zero stored posts. An incomplete export looks the same as never posting.",
            "medium",
        )
        c.assess("posts_sparse", "suppressed", "No posts at all; counted under the gap check.")
        c.assess("post_types_uniform", "insufficient_data", "No posts to compare.")
        c.assess("posts_without_cta", "insufficient_data", "No posts to check.")
        return

    latest = posts[0]
    age = (c.as_of - day(latest["published_on"])).days
    if age > gap:
        c.assess("posts_none_recent", "triggered", f"Last post {age} days ago, over {gap}.", 1)
        c.emit(
            "posts_none_recent",
            "Publish a post",
            CHECKS["posts_none_recent"]["fix"],
            f"The last post was {age} days ago, on {day(latest['published_on'])}; the "
            f"policy gap is {gap} days.",
            graded(45, (age - gap) / (window_days - gap), 25, 72),
            [
                c.evidence(
                    "posts",
                    [latest],
                    ["published_on", "post_type"],
                    "as_of - max(published_on)",
                    days=age,
                    gap=gap,
                )
            ],
            HREF_POSTS,
            "Counts days to the analysis date, which may be after the last export.",
            "high",
        )
    else:
        c.assess("posts_none_recent", "clear", f"Last post {age} days ago.")

    recent = c.window(posts, "published_on", 90)
    if not recent:
        c.assess(
            "posts_sparse",
            "suppressed",
            "No post in the last 90 days; counted under the gap check.",
        )
    elif len(recent) < minimum:
        c.assess(
            "posts_sparse",
            "triggered",
            f"{len(recent)} posts in 90 days, below the minimum of {minimum}.",
            1,
        )
        c.emit(
            "posts_sparse",
            "Post more often",
            CHECKS["posts_sparse"]["fix"],
            f"{len(recent)} {'post' if len(recent) == 1 else 'posts'} in the last 90 days; "
            f"the policy minimum is {minimum}.",
            graded(45, (minimum - len(recent)) / minimum, 12, 57),
            [
                c.evidence(
                    "posts",
                    recent,
                    ["published_on"],
                    "count of posts in the last 90 days",
                    posts_90d=len(recent),
                    minimum=minimum,
                )
            ],
            HREF_POSTS,
            "The minimum is an operating policy. Posts affect clicks, not rank.",
            "high",
        )
    else:
        c.assess("posts_sparse", "clear", f"{len(recent)} posts in the last 90 days.")

    visible = c.window(posts, "published_on", window_days)
    types = Counter(post_type(r) for r in visible)
    if len(visible) < mix_min:
        c.assess(
            "post_types_uniform",
            "insufficient_data",
            f"Only {len(visible)} posts in the {window_days}-day window; need {mix_min}.",
        )
        c.assess(
            "posts_without_cta",
            "insufficient_data",
            f"Only {len(visible)} posts in the {window_days}-day window; need {mix_min}.",
        )
        return

    if len(types) == 1:
        only = next(iter(types))
        label = POST_TYPE_LABELS.get(only, only)
        c.assess("post_types_uniform", "triggered", f"All {len(visible)} posts are {label}s.", 1)
        c.emit(
            "post_types_uniform",
            f"All posts are {label}s",
            CHECKS["post_types_uniform"]["fix"],
            f"All {len(visible)} posts in the last {window_days} days are of one type: {label}.",
            20,
            [
                c.evidence(
                    "posts",
                    visible,
                    ["post_type"],
                    "distinct post_type in window",
                    types=dict(types),
                )
            ],
            HREF_POSTS,
            "Variety is a proxy for a considered posting plan, not a Google rule.",
            "high",
        )
    else:
        c.assess("post_types_uniform", "clear", f"{len(types)} post types in use.")

    without = [r for r in visible if not has_cta(r)]
    share = len(without) / len(visible)
    if share > cta_max:
        c.assess(
            "posts_without_cta",
            "triggered",
            f"{len(without)} of {len(visible)} posts have no call to action ({share:.0%}).",
            len(without),
            len(visible),
        )
        c.emit(
            "posts_without_cta",
            "Add a button to each post",
            CHECKS["posts_without_cta"]["fix"],
            f"{len(without)} of {len(visible)} posts in the last {window_days} days have "
            f"no call to action ({share:.0%}); the policy limit is {cta_max:.0%}.",
            graded(18, (share - cta_max) / max(0.01, 1 - cta_max), 12, 30),
            [
                c.evidence(
                    "posts",
                    without,
                    ["cta_type"],
                    "share of posts in window with empty cta_type",
                    without_cta=len(without),
                    posts=len(visible),
                    limit=cta_max,
                )
            ],
            HREF_POSTS,
            "Offers get an automatic View offer button that the export does not record.",
            "high",
        )
    else:
        c.assess(
            "posts_without_cta",
            "clear",
            f"{len(without)} of {len(visible)} posts without a call to action.",
        )


def card(snapshot: dict) -> dict:
    """Photo coverage and the post timeline, for the category view."""
    loc = snapshot["locations"][0]
    location_id = loc["id"]
    rows = lambda source: [  # noqa: E731 - tiny local helper
        r for r in snapshot.get(source, []) if r.get("location_id") == location_id
    ]
    media = rows("media")
    row = media[0] if media else None
    # The snapshot carries no analysis date; the card is display only, so today serves.
    reference = day(snapshot.get("as_of")) or date.today()
    posts = dated_posts(rows("posts"))
    latest = posts[0] if posts else None
    photos = count(row.get("photo_count")) if row else None
    typed = {name: count(row.get(field)) if row else None for name, field in PHOTO_TYPES}
    known_typed = sum(v for v in typed.values() if v is not None)
    uploaded = day(row.get("last_photo_uploaded_on")) if row else None

    def since(when) -> int | None:
        return (reference - when).days if when else None

    window_start = reference - timedelta(days=89)
    recent = [r for r in posts if day(r["published_on"]) >= window_start]
    six_months = reference - timedelta(days=179)
    visible = [r for r in posts if day(r["published_on"]) >= six_months]
    with_cta = sum(1 for r in visible if has_cta(r))
    return {
        "has_media_summary": row is not None,
        "photos": {
            "total": photos,
            "interior": typed["interior"],
            "exterior": typed["exterior"],
            "team": typed["team"],
            "other": (photos - known_typed) if photos is not None else None,
            "videos": count(row.get("video_count")) if row else None,
            "last_uploaded_on": str(uploaded) if uploaded else None,
            "days_since_upload": since(uploaded),
        },
        "posts": {
            "total": len(posts),
            "in_90_days": len(recent),
            "last_published_on": str(day(latest["published_on"])) if latest else None,
            "last_type": post_type(latest) if latest else None,
            "days_since_post": since(day(latest["published_on"])) if latest else None,
            "type_mix": dict(Counter(post_type(r) for r in visible)),
            "cta_share": round(with_cta / len(visible), 2) if visible else None,
            "recent": [
                {
                    "type": post_type(r),
                    "published_on": str(day(r["published_on"])),
                    "summary": str(r.get("summary") or "")[:120],
                    "cta": (str(r.get("cta_type") or "").casefold() or None),
                }
                for r in posts[:5]
            ],
        },
    }
