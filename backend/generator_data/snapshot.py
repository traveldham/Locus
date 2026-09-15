"""Build the audit engine's snapshot straight from generated rows, without a database.

`app.services.recommendations.snapshot.read_snapshot` reads every model column, drops
the identity and ingestion fields, and flattens dates, UUIDs and enums to strings. This
module does the same thing to the generator's output, so the whole catalogue can be
audited in milliseconds while it is being tuned. The database path produces the same
snapshot; `verify.py` checks both agree.
"""

from __future__ import annotations

from app.models import (
    AttributeCatalogItem,
    Booking,
    CompetitorObservation,
    KeywordRank,
    Location,
    LocationAttributeValue,
    LocationCategory,
    LocationHoursPeriod,
    MediaSummary,
    PerformanceDaily,
    Post,
    Project,
    Review,
    SearchTermMonthly,
    TrackedKeyword,
)
from app.services.recommendations.contracts import EXCLUDED
from app.services.recommendations.snapshot import scalar
from generator_data.generator import ProfileData

MODELS = {
    "locations": Location,
    "hours": LocationHoursPeriod,
    "categories": LocationCategory,
    "attributes": LocationAttributeValue,
    "catalog": AttributeCatalogItem,
    "reviews": Review,
    "performance": PerformanceDaily,
    "search_terms": SearchTermMonthly,
    "media": MediaSummary,
    "posts": Post,
    "bookings": Booking,
    "keywords": TrackedKeyword,
    "ranks": KeywordRank,
    "competitors": CompetitorObservation,
    "projects": Project,
}

# Column defaults the models apply on insert, which a hand-built row must carry too.
DEFAULTS: dict[str, dict] = {
    "locations": {"source": "fixture"},
    "hours": {"hours_type": "REGULAR"},
    "categories": {"is_primary": False},
    "reviews": {"is_anonymous": False},
    "performance": {"source": "locus"},
    "search_terms": {"source": "locus", "is_threshold": False},
    "media": {"source": "locus"},
    "posts": {"source": "locus"},
    "bookings": {"source": "locus"},
    "keywords": {"source": "locus"},
    "ranks": {"source": "locus", "found": False},
    "competitors": {"source": "locus"},
    "projects": {"status": "active"},
}


def _row(table: str, values: dict, row_id: str, **extra) -> dict:
    """One snapshot row: every column of the model, flattened the way the engine sees it."""
    model = MODELS[table]
    columns = {column.key for column in model.__table__.columns}
    row = dict.fromkeys(columns)
    row.update(DEFAULTS.get(table, {}))
    row.update({k: v for k, v in values.items() if k in columns})
    row.update({k: v for k, v in extra.items() if k in columns})
    row["id"] = row_id
    return {key: scalar(value) for key, value in row.items() if key not in EXCLUDED}


def snapshot_of(data: ProfileData) -> dict:
    """The engine snapshot for one generated profile."""
    key = data.key
    location_id = f"{key}-location"
    project_id = f"{key}-project"
    keyword_id = {
        row["external_keyword_id"]: f"{key}-keyword-{index:02d}"
        for index, row in enumerate(data.keywords)
    }

    def rows(table: str, values: list[dict], scoped: bool = True) -> list[dict]:
        extra = {"location_id": location_id} if scoped else {}
        return [
            _row(table, value, f"{key}-{table}-{index:04d}", **extra)
            for index, value in enumerate(values)
        ]

    snapshot = {
        "locations": [_row("locations", data.location, location_id)],
        "hours": rows("hours", data.hours),
        "categories": rows("categories", data.categories),
        "attributes": rows("attributes", data.attributes),
        "catalog": rows("catalog", data.catalog, scoped=False),
        "reviews": rows("reviews", data.reviews),
        "performance": rows("performance", data.performance),
        "search_terms": rows("search_terms", data.search_terms),
        "media": rows("media", [data.media] if data.media else []),
        "posts": rows("posts", data.posts),
        "bookings": rows("bookings", data.bookings),
        "keywords": [
            _row("keywords", value, keyword_id[value["external_keyword_id"]],
                 location_id=location_id)
            for value in data.keywords
        ],
        "ranks": [
            _row(
                "ranks",
                value,
                f"{key}-ranks-{index:04d}",
                location_id=location_id,
                tracked_keyword_id=keyword_id[value["keyword_ref"]],
            )
            for index, value in enumerate(data.ranks)
        ],
        "competitors": [
            _row(
                "competitors",
                value,
                f"{key}-competitors-{index:04d}",
                tracked_keyword_id=keyword_id[value["keyword_ref"]],
            )
            for index, value in enumerate(data.competitors)
        ],
        "projects": [_row("projects", data.project, project_id)],
    }
    return snapshot
