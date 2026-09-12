"""Loading the sample CSV dataset into the analytics tables.

The eight tables filled here hold data the profile import has nowhere to put: daily
performance, search terms, media rollups, posts, bookings, tracked keywords, weekly ranks
and competitor observations. Until Google approves the app — and, for four of them,
forever, because no Google API exists — the sample CSVs are where those rows come from.

Three rules run through the whole module:

* **Empty means absent, not zero.** Every optional metric parses to `None` when the CSV
  cell is blank, so "Google reported no calls that day" and "Google reported nothing that
  day" stay different facts in the database, in the chart and in the totals.
* **Provenance is written, not inferred.** Performance, search terms, media and posts are
  `google`; keywords, ranks, competitors and bookings are `locus`, permanently, because
  Google never supplies them (see `tasks/016-data-provenance-marks.md`).
* **Running it twice changes nothing.** Every table is upserted on its natural key, and
  competitor observations — which deliberately have no unique constraint, since a
  keyword-week holds several rivals — are deleted per keyword-week before reinsertion.

Locations the organization has not imported are skipped in silence: the CSVs describe
twelve clinics and an organization may have imported three of them, which is ordinary.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AttributeCatalogItem,
    Booking,
    BookingChannel,
    BookingStatus,
    CompetitorObservation,
    DataSource,
    KeywordRank,
    Location,
    MediaSummary,
    PerformanceDaily,
    Post,
    PostCtaType,
    PostType,
    SearchIntent,
    SearchTermMonthly,
    TrackedKeyword,
)
from app.services.providers import sample_data

LOCATIONS_FILE = "locations.csv"
PERFORMANCE_FILE = "location_daily_kpis.csv"
SEARCH_TERMS_FILE = "location_search_terms_monthly.csv"
MEDIA_FILE = "location_media_summary.csv"
POSTS_FILE = "posts.csv"
BOOKINGS_FILE = "booking_requests.csv"
KEYWORDS_FILE = "tracked_keywords.csv"
RANKS_FILE = "keyword_rank_weekly.csv"
COMPETITORS_FILE = "competitor_ranks_weekly.csv"
ATTRIBUTE_CATALOG_FILE = "attribute_catalog.csv"

# ~8,800 rows land in eight tables; they go out in batched executemany statements rather
# than one INSERT per row.
BATCH_SIZE = 500

# The nine daily metrics, named identically in the CSV and on the model.
PERFORMANCE_METRICS = (
    "impressions_maps_desktop",
    "impressions_maps_mobile",
    "impressions_search_desktop",
    "impressions_search_mobile",
    "website_clicks",
    "call_clicks",
    "direction_requests",
    "conversations",
    "bookings",
)

MEDIA_COUNTS = (
    "photo_count",
    "interior_photo_count",
    "exterior_photo_count",
    "team_photo_count",
    "video_count",
)


class SampleDataError(RuntimeError):
    """The sample dataset is missing or unreadable — a deployment problem, not a bug."""


@dataclass(slots=True)
class SampleLoadResult:
    """What one load run touched, per table, for the response and the `SyncRun`."""

    locations_matched: int = 0
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


# ---------------------------------------------------------------------------
# Reading and parsing
# ---------------------------------------------------------------------------


def _read_csv(directory: Path, file_name: str) -> list[dict[str, str]]:
    """One CSV as stripped string rows.

    Deliberately not the sample provider's cached reader: this runs once per load, and a
    process-lifetime cache would mean a test (or an operator) pointing `SAMPLE_DATA_DIR`
    at a different dataset silently got the old one.
    """
    if not directory.is_dir():
        raise SampleDataError(
            f"The sample dataset directory does not exist: {directory}. Set SAMPLE_DATA_DIR "
            "to the directory holding the sample CSVs."
        )
    path = directory / file_name
    if not path.is_file():
        raise SampleDataError(f"The sample dataset is incomplete: {path} is missing.")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in csv.DictReader(handle)
        ]


def _int(value: str) -> int | None:
    """A blank cell is an absent measurement. It must never become a zero."""
    text = value.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _float(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _text(value: str) -> str | None:
    return value.strip() or None


def _day(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _moment(value: str) -> datetime | None:
    """The CSVs carry dates where the model wants a timestamp; midnight UTC is the honest
    reading of "this happened on that day" without inventing a time of day."""
    parsed = _day(value)
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=UTC) if parsed else None


def _flag(value: str) -> bool:
    return value.strip().upper() in {"TRUE", "T", "YES", "1"}


def _optional_flag(value: str) -> bool | None:
    """For columns where "we did not observe it" is a third state, not a False."""
    text = value.strip().upper()
    if not text:
        return None
    return text in {"TRUE", "T", "YES", "1"}


def _member[E: StrEnum](enum: type[E], value: str) -> E | None:
    """A CSV label to an enum member, or None — an unrecognised label must not fail the
    load of the other 8,000 rows."""
    try:
        return enum(value.strip().lower())
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def _chunks(rows: list[dict[str, Any]]) -> Iterator[list[dict[str, Any]]]:
    for start in range(0, len(rows), BATCH_SIZE):
        yield rows[start : start + BATCH_SIZE]


async def _upsert(
    db: AsyncSession,
    model: type[Any],
    key_fields: tuple[str, ...],
    organization_id: UUID,
    payloads: list[dict[str, Any]],
) -> int:
    """Insert or update every payload, keyed on the table's unique constraint.

    The existing keys are read once, then the work splits into two executemany statements
    — which is what keeps a re-run cheap and, more importantly, non-duplicating.
    """
    if not payloads:
        return 0

    # A duplicate key inside one CSV is the file contradicting itself; the last row wins,
    # which is also what a row-by-row upsert would have done.
    deduplicated: dict[tuple[Any, ...], dict[str, Any]] = {
        tuple(payload[name] for name in key_fields): payload for payload in payloads
    }

    result = await db.execute(
        select(model.id, *(getattr(model, name) for name in key_fields)).where(
            model.organization_id == organization_id
        )
    )
    existing = {tuple(row[1:]): row[0] for row in result.all()}

    inserts: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    for key, payload in deduplicated.items():
        row_id = existing.get(key)
        if row_id is None:
            inserts.append({"id": uuid4(), **payload})
        else:
            updates.append({**payload, "id": row_id})

    for chunk in _chunks(inserts):
        await db.execute(insert(model), chunk)
    for chunk in _chunks(updates):
        await db.execute(update(model), chunk)
    await db.flush()
    return len(deduplicated)


async def _insert_all(db: AsyncSession, model: type[Any], payloads: list[dict[str, Any]]) -> int:
    for chunk in _chunks(payloads):
        await db.execute(insert(model), [{"id": uuid4(), **payload} for payload in chunk])
    await db.flush()
    return len(payloads)


# ---------------------------------------------------------------------------
# The load
# ---------------------------------------------------------------------------


async def _location_ids_by_csv_id(
    db: AsyncSession, organization_id: UUID, directory: Path
) -> dict[str, UUID]:
    """`LOC-001` -> our `Location.id`, for the locations this organization imported.

    The bridge is `locations.csv`'s `gbp_location_id`, which is the Google resource name
    the import stored as `Location.google_location_name` — the same join the sample
    provider makes for reviews.
    """
    csv_id_by_google_name = {
        row["gbp_location_id"]: row["location_id"]
        for row in _read_csv(directory, LOCATIONS_FILE)
        if row.get("gbp_location_id") and row.get("location_id")
    }
    result = await db.execute(
        select(Location.id, Location.google_location_name).where(
            Location.organization_id == organization_id
        )
    )
    mapping: dict[str, UUID] = {}
    for location_id, google_name in result.all():
        csv_id = csv_id_by_google_name.get(google_name or "")
        if csv_id is not None:
            mapping[csv_id] = location_id
    return mapping


def _performance_payloads(
    rows: Sequence[dict[str, str]], organization_id: UUID, locations: dict[str, UUID]
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        location_id = locations.get(row.get("location_id", ""))
        day = _day(row.get("date", ""))
        if location_id is None or day is None:
            continue
        payloads.append(
            {
                "organization_id": organization_id,
                "location_id": location_id,
                "date": day,
                # `_int` yields None for a blank cell. Nothing here coalesces to 0.
                **{name: _int(row.get(name, "")) for name in PERFORMANCE_METRICS},
                "source": DataSource.google,
            }
        )
    return payloads


def _attribute_catalog_payloads(
    rows: Sequence[dict[str, str]], organization_id: UUID
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        external_id = _text(row.get("attribute_id", ""))
        name = _text(row.get("attribute_name", ""))
        group = _text(row.get("attribute_group", ""))
        category = _text(row.get("applies_to_category", ""))
        value_type = _text(row.get("value_type", ""))
        if not all((external_id, name, group, category, value_type)):
            continue
        payloads.append(
            {
                "organization_id": organization_id,
                "external_attribute_id": external_id,
                "attribute_name": name,
                "attribute_group": group,
                "applies_to_category": category,
                "value_type": value_type,
            }
        )
    return payloads


def _search_term_payloads(
    rows: Sequence[dict[str, str]], organization_id: UUID, locations: dict[str, UUID]
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        location_id = locations.get(row.get("location_id", ""))
        year_month = _text(row.get("year_month", ""))
        term = _text(row.get("search_term", ""))
        if location_id is None or year_month is None or term is None:
            continue
        payloads.append(
            {
                "organization_id": organization_id,
                "location_id": location_id,
                "year_month": year_month,
                "search_term": term,
                "impressions": _int(row.get("impressions", "")),
                # The export carries exact counts only; when a feed starts sending
                # Google's "fewer than N" ceiling this is where it gets marked.
                "is_threshold": _flag(row.get("is_threshold", "")),
                "source": DataSource.google,
            }
        )
    return payloads


def _media_payloads(
    rows: Sequence[dict[str, str]], organization_id: UUID, locations: dict[str, UUID]
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        location_id = locations.get(row.get("location_id", ""))
        if location_id is None:
            continue
        payloads.append(
            {
                "organization_id": organization_id,
                "location_id": location_id,
                **{name: _int(row.get(name, "")) for name in MEDIA_COUNTS},
                "has_profile_photo": _flag(row.get("has_profile_photo", "")),
                "has_cover_photo": _flag(row.get("has_cover_photo", "")),
                "last_photo_uploaded_on": _day(row.get("last_photo_uploaded_on", "")),
                "source": DataSource.google,
            }
        )
    return payloads


def _post_payloads(
    rows: Sequence[dict[str, str]], organization_id: UUID, locations: dict[str, UUID]
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        location_id = locations.get(row.get("location_id", ""))
        post_id = _text(row.get("post_id", ""))
        post_type = _member(PostType, row.get("post_type", ""))
        if location_id is None or post_id is None or post_type is None:
            continue
        payloads.append(
            {
                "organization_id": organization_id,
                "location_id": location_id,
                "google_post_id": post_id,
                "post_type": post_type,
                "summary": _text(row.get("summary", "")),
                # A post with no call to action is normal; it stays None rather than
                # acquiring a made-up default.
                "cta_type": _member(PostCtaType, row.get("cta_type", "")),
                "published_on": _day(row.get("published_on", "")),
                "source": DataSource.google,
            }
        )
    return payloads


def _booking_payloads(
    rows: Sequence[dict[str, str]], organization_id: UUID, locations: dict[str, UUID]
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        location_id = locations.get(row.get("location_id", ""))
        booking_id = _text(row.get("booking_id", ""))
        status = _member(BookingStatus, row.get("status", ""))
        if location_id is None or booking_id is None or status is None:
            continue
        payloads.append(
            {
                "organization_id": organization_id,
                "location_id": location_id,
                "external_booking_id": booking_id,
                "customer_name": _text(row.get("customer_name", "")),
                "service": _text(row.get("service", "")),
                "requested_for_date": _day(row.get("requested_for_date", "")),
                "status": status,
                # The CSV's `source` column is the *channel* the request arrived through,
                # not the provenance of the row — which is always locus here.
                "booking_source": _member(BookingChannel, row.get("source", "")),
                "booking_created_at": _moment(row.get("created_at", "")),
                "source": DataSource.locus,
            }
        )
    return payloads


def _keyword_payloads(
    rows: Sequence[dict[str, str]], organization_id: UUID, locations: dict[str, UUID]
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        location_id = locations.get(row.get("location_id", ""))
        keyword_id = _text(row.get("keyword_id", ""))
        keyword = _text(row.get("keyword", ""))
        if location_id is None or keyword_id is None or keyword is None:
            continue
        payloads.append(
            {
                "organization_id": organization_id,
                "location_id": location_id,
                "external_keyword_id": keyword_id,
                "keyword": keyword,
                "search_intent": _member(SearchIntent, row.get("search_intent", "")),
                "device": _text(row.get("device", "")),
                "tracking_started_on": _day(row.get("tracking_started_on", "")),
                "source": DataSource.locus,
            }
        )
    return payloads


async def _tracked_keywords_by_external_id(
    db: AsyncSession, organization_id: UUID
) -> dict[str, tuple[UUID, UUID]]:
    """`KW-0001` -> (tracked_keyword_id, location_id), the join the rank feeds need."""
    result = await db.execute(
        select(
            TrackedKeyword.external_keyword_id,
            TrackedKeyword.id,
            TrackedKeyword.location_id,
        ).where(TrackedKeyword.organization_id == organization_id)
    )
    return {external: (keyword_id, location_id) for external, keyword_id, location_id in result}


def _rank_payloads(
    rows: Sequence[dict[str, str]],
    organization_id: UUID,
    keywords: dict[str, tuple[UUID, UUID]],
) -> list[dict[str, Any]]:
    payloads = []
    for row in rows:
        entry = keywords.get(row.get("keyword_id", ""))
        week_start = _day(row.get("week_start", ""))
        if entry is None or week_start is None:
            continue
        tracked_keyword_id, location_id = entry
        payloads.append(
            {
                "organization_id": organization_id,
                "location_id": location_id,
                "tracked_keyword_id": tracked_keyword_id,
                "week_start": week_start,
                # Blank means the location was not found in the checked results. Not
                # rank 0, not "worst" — absent. `found` carries that fact separately, and
                # both are preserved rather than derived from one another.
                "rank_absolute": _int(row.get("rank_absolute", "")),
                "rank_in_local_pack": _int(row.get("rank_in_local_pack", "")),
                "found": _flag(row.get("found", "")),
                "result_url": _text(row.get("result_url", "")),
                "source": DataSource.locus,
            }
        )
    return payloads


async def _load_competitors(
    db: AsyncSession,
    rows: Sequence[dict[str, str]],
    organization_id: UUID,
    keywords: dict[str, tuple[UUID, UUID]],
) -> int:
    """Replace every keyword-week the feed covers, rather than upserting row by row.

    `competitor_observations` has no unique constraint on purpose — several rivals share
    one keyword-week — so the only way to stay idempotent is to clear the weeks this feed
    speaks for and write them again.
    """
    payloads: list[dict[str, Any]] = []
    weeks_by_keyword: dict[UUID, set[date]] = defaultdict(set)
    for row in rows:
        entry = keywords.get(row.get("keyword_id", ""))
        week_start = _day(row.get("week_start", ""))
        name = _text(row.get("competitor_name", ""))
        if entry is None or week_start is None or name is None:
            continue
        tracked_keyword_id, _ = entry
        weeks_by_keyword[tracked_keyword_id].add(week_start)
        payloads.append(
            {
                "organization_id": organization_id,
                "tracked_keyword_id": tracked_keyword_id,
                "week_start": week_start,
                "competitor_name": name,
                "competitor_place_id": _text(row.get("competitor_place_id", "")),
                "rank_absolute": _int(row.get("rank_absolute", "")),
                "review_count": _int(row.get("review_count", "")),
                "average_rating": _float(row.get("average_rating", "")),
                "photo_count": _int(row.get("photo_count", "")),
                "is_claimed": _optional_flag(row.get("is_claimed", "")),
                "source": DataSource.locus,
            }
        )

    # Keywords almost always share one week set, so this collapses to a single DELETE —
    # and where they differ, each group still deletes exactly the weeks it will rewrite.
    groups: dict[frozenset[date], list[UUID]] = defaultdict(list)
    for tracked_keyword_id, weeks in weeks_by_keyword.items():
        groups[frozenset(weeks)].append(tracked_keyword_id)
    for weeks, keyword_ids in groups.items():
        await db.execute(
            delete(CompetitorObservation).where(
                CompetitorObservation.organization_id == organization_id,
                CompetitorObservation.tracked_keyword_id.in_(keyword_ids),
                CompetitorObservation.week_start.in_(weeks),
            )
        )
    await db.flush()
    return await _insert_all(db, CompetitorObservation, payloads)


async def load_sample_datasets(db: AsyncSession, organization_id: UUID) -> SampleLoadResult:
    """Fill the eight analytics tables from the sample CSVs for one organization.

    Flushes but does not commit — the caller owns the transaction, so a failure halfway
    through leaves no half-loaded dataset behind.
    """
    directory = sample_data.data_dir()
    locations = await _location_ids_by_csv_id(db, organization_id, directory)
    result = SampleLoadResult(locations_matched=len(locations))
    if not locations:
        # Nothing imported yet: every CSV row belongs to a location we do not have.
        result.counts = dict.fromkeys(
            (
                "performance_daily",
                "search_terms_monthly",
                "media_summary",
                "posts",
                "bookings",
                "tracked_keywords",
                "keyword_ranks",
                "competitor_observations",
                "attribute_catalog_items",
            ),
            0,
        )
        return result

    result.counts["attribute_catalog_items"] = await _upsert(
        db,
        AttributeCatalogItem,
        ("external_attribute_id",),
        organization_id,
        _attribute_catalog_payloads(_read_csv(directory, ATTRIBUTE_CATALOG_FILE), organization_id),
    )

    result.counts["performance_daily"] = await _upsert(
        db,
        PerformanceDaily,
        ("location_id", "date"),
        organization_id,
        _performance_payloads(_read_csv(directory, PERFORMANCE_FILE), organization_id, locations),
    )
    result.counts["search_terms_monthly"] = await _upsert(
        db,
        SearchTermMonthly,
        ("location_id", "year_month", "search_term"),
        organization_id,
        _search_term_payloads(_read_csv(directory, SEARCH_TERMS_FILE), organization_id, locations),
    )
    result.counts["media_summary"] = await _upsert(
        db,
        MediaSummary,
        ("location_id",),
        organization_id,
        _media_payloads(_read_csv(directory, MEDIA_FILE), organization_id, locations),
    )
    result.counts["posts"] = await _upsert(
        db,
        Post,
        ("location_id", "google_post_id"),
        organization_id,
        _post_payloads(_read_csv(directory, POSTS_FILE), organization_id, locations),
    )
    result.counts["bookings"] = await _upsert(
        db,
        Booking,
        ("location_id", "external_booking_id"),
        organization_id,
        _booking_payloads(_read_csv(directory, BOOKINGS_FILE), organization_id, locations),
    )
    result.counts["tracked_keywords"] = await _upsert(
        db,
        TrackedKeyword,
        ("location_id", "external_keyword_id"),
        organization_id,
        _keyword_payloads(_read_csv(directory, KEYWORDS_FILE), organization_id, locations),
    )

    # The rank and competitor feeds join on the keyword, so they can only be read back
    # once the keywords themselves are in the table.
    keywords = await _tracked_keywords_by_external_id(db, organization_id)
    result.counts["keyword_ranks"] = await _upsert(
        db,
        KeywordRank,
        ("tracked_keyword_id", "week_start"),
        organization_id,
        _rank_payloads(_read_csv(directory, RANKS_FILE), organization_id, keywords),
    )
    result.counts["competitor_observations"] = await _load_competitors(
        db, _read_csv(directory, COMPETITORS_FILE), organization_id, keywords
    )
    return result
