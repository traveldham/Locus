"""Reading the sample CSV dataset into the provider-neutral shapes.

This is the parsing half of the sample provider: it turns the flat take-home CSVs into
the provider-neutral dataclasses in `providers/base.py`, in Google's own shape, so
nothing above the provider seam sees the CSV at all. Everything is cached — the CSVs are
read once per process, not once per request.

The mapping is deliberately faithful to Google's shape rather than to the CSV's:
one row per weekday becomes a `regularHours` period with an `open_day`/`close_day`, a
blank row means the business is closed that day and produces no period at all, and every
attribute keeps the type its catalog entry declares instead of collapsing to a string.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.models import OpenStatus
from app.services.providers.base import (
    DAYS_OF_WEEK,
    ProviderAccount,
    ProviderAttribute,
    ProviderCategory,
    ProviderError,
    ProviderHoursPeriod,
    ProviderLocation,
)

# The dataset is checked out next to the backend, not inside it:
# <repo>/backend/app/services/providers/sample_data.py -> <repo>/locus-intelligence-assignment/data
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[4] / "locus-intelligence-assignment" / "data"

LOCATIONS_FILE = "locations.csv"
HOURS_FILE = "location_hours.csv"
ATTRIBUTES_FILE = "location_attributes.csv"
CATALOG_FILE = "attribute_catalog.csv"
REVIEWS_FILE = "reviews.csv"
REPLIES_FILE = "review_replies.csv"

# One Google account owns the whole sample set, mirroring a single location group.
SAMPLE_ACCOUNT = ProviderAccount(
    resource_name="accounts/100000000000000000001",
    account_name="Brightpath Dental Group",
    account_type="LOCATION_GROUP",
    role="PRIMARY_OWNER",
    verification_state="VERIFIED",
)

_OPEN_STATUS = {
    "OPEN": OpenStatus.open,
    "CLOSED_TEMPORARILY": OpenStatus.closed_temporarily,
    "CLOSED_PERMANENTLY": OpenStatus.closed_permanently,
}

# The catalog's lowercase type names -> Google's attribute value types.
_VALUE_TYPES = {
    "bool": "BOOL",
    "enum": "ENUM",
    "repeated_enum": "REPEATED_ENUM",
    "url": "URL",
}

_REGION_CODE = "US"


def data_dir() -> Path:
    """Where the CSVs are read from — `SAMPLE_DATA_DIR`, or the checked-out dataset."""
    configured = (get_settings().sample_data_dir or "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_DATA_DIR


def _rows(file_name: str) -> list[dict[str, str]]:
    """One CSV as stripped string rows, or a `ProviderError` naming what is missing."""
    directory = data_dir()
    if not directory.is_dir():
        raise ProviderError(
            f"The sample dataset directory does not exist: {directory}. Set SAMPLE_DATA_DIR "
            "to the directory holding the sample CSVs."
        )
    path = directory / file_name
    if not path.is_file():
        raise ProviderError(
            f"The sample dataset is incomplete: {path} is missing. Set SAMPLE_DATA_DIR to a "
            "directory holding the full sample CSV set."
        )
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items() if key}
            for row in csv.DictReader(handle)
        ]


def clear_cache() -> None:
    """Forget every parsed CSV — used when the dataset directory changes under us."""
    for loader in (
        load_locations,
        load_reviews,
        csv_id_by_google_name,
        _hours_by_location,
        _attributes_by_location,
        _attribute_catalog,
    ):
        loader.cache_clear()


# ---------------------------------------------------------------------------
# Field parsing
# ---------------------------------------------------------------------------


def _flag(value: str) -> bool:
    return value.upper() in {"TRUE", "T", "YES", "1"}


def _number(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _day(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _moment(value: str) -> datetime | None:
    parsed = _day(value)
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=UTC) if parsed else None


def _clock(value: str) -> tuple[int, int] | None:
    """`"08:30"` -> `(8, 30)`; anything else is not a time we can publish."""
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return None
    hour, minute = int(parts[0]), int(parts[1])
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return hour, minute


def _category(display_name: str, *, is_primary: bool) -> ProviderCategory:
    """Google names a category `categories/gcid:dentist`, never by its display name."""
    slug = re.sub(r"[^a-z0-9]+", "_", display_name.lower()).strip("_")
    return ProviderCategory(
        category_name=f"categories/gcid:{slug}",
        display_name=display_name,
        is_primary=is_primary,
    )


def _categories(row: dict[str, str]) -> tuple[ProviderCategory, ...]:
    primary = row.get("primary_category", "")
    items = [_category(primary, is_primary=True)] if primary else []
    items.extend(
        _category(name.strip(), is_primary=False)
        for name in row.get("additional_categories", "").split("|")
        if name.strip()
    )
    return tuple(items)


# ---------------------------------------------------------------------------
# Hours and attributes
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _hours_by_location() -> dict[str, tuple[ProviderHoursPeriod, ...]]:
    """One period per open weekday. A row with blank times is a closed day, not a period."""
    grouped: dict[str, list[ProviderHoursPeriod]] = defaultdict(list)
    for row in _rows(HOURS_FILE):
        opens = _clock(row.get("open_time", ""))
        closes = _clock(row.get("close_time", ""))
        day = row.get("day_of_week", "").upper()
        if opens is None or closes is None or day not in DAYS_OF_WEEK:
            continue
        grouped[row["location_id"]].append(
            ProviderHoursPeriod(
                open_day=day,
                open_hour=opens[0],
                open_minute=opens[1],
                close_day=day,
                close_hour=closes[0],
                close_minute=closes[1],
            )
        )
    return {location_id: tuple(periods) for location_id, periods in grouped.items()}


@lru_cache(maxsize=1)
def _attribute_catalog() -> dict[str, tuple[str, str]]:
    """`attr_01` -> (`attributes/wheelchair_accessible_entrance`, `BOOL`)."""
    catalog: dict[str, tuple[str, str]] = {}
    for row in _rows(CATALOG_FILE):
        attribute_id = row.get("attribute_id", "")
        if not attribute_id:
            continue
        name = row.get("attribute_name") or attribute_id
        value_type = _VALUE_TYPES.get(row.get("value_type", "").lower(), "BOOL")
        catalog[attribute_id] = (f"attributes/{name}", value_type)
    return catalog


def _attribute_values(value_type: str, raw: str) -> tuple[object, ...]:
    """A typed value, because Google rejects a boolean sent in an enum container."""
    if value_type == "BOOL":
        return (_flag(raw),)
    if value_type == "URL":
        return (raw,)
    return (raw.upper(),)


@lru_cache(maxsize=1)
def _attributes_by_location() -> dict[str, tuple[ProviderAttribute, ...]]:
    catalog = _attribute_catalog()
    grouped: dict[str, list[ProviderAttribute]] = defaultdict(list)
    for row in _rows(ATTRIBUTES_FILE):
        entry = catalog.get(row.get("attribute_id", ""))
        if entry is None:
            continue  # an attribute with no catalog entry has no type, so it cannot be sent
        google_id, value_type = entry
        grouped[row["location_id"]].append(
            ProviderAttribute(
                attribute_id=google_id,
                value_type=value_type,
                values=_attribute_values(value_type, row.get("value", "")),
            )
        )
    return {location_id: tuple(items) for location_id, items in grouped.items()}


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------


def _location(row: dict[str, str]) -> ProviderLocation:
    csv_id = row["location_id"]
    google_location_name = row["gbp_location_id"]
    categories = _categories(row)
    primary = categories[0] if categories and categories[0].is_primary else None
    return ProviderLocation(
        google_location_name=google_location_name,
        source_location_id=csv_id,
        # The v4 reviews API addresses a location as accounts/{a}/locations/{l}, so the
        # account-qualified form is synthesized here in exactly that shape.
        google_resource_name=f"{SAMPLE_ACCOUNT.resource_name}/{google_location_name}",
        store_code=row.get("store_code") or None,
        title=row.get("name") or google_location_name,
        primary_category_name=primary.category_name if primary else None,
        primary_category_display=primary.display_name if primary else None,
        # The dataset carries no street line, only the town. Inventing one would make the
        # "Incomplete" chip lie, so the address stays as incomplete as the data really is.
        locality=row.get("city") or None,
        administrative_area=row.get("state") or None,
        postal_code=row.get("postal_code") or None,
        region_code=_REGION_CODE,
        latitude=_number(row.get("latitude", "")),
        longitude=_number(row.get("longitude", "")),
        phone_primary=row.get("phone") or None,
        # Left empty where the dataset leaves them empty: those profiles are genuinely
        # incomplete, and the UI is supposed to say so.
        website_uri=row.get("website_url") or None,
        description=row.get("description") or None,
        open_status=_OPEN_STATUS.get(row.get("open_status", "").upper()),
        opening_date=_day(row.get("opened_on", "")),
        has_voice_of_merchant=_flag(row.get("verified", "")),
        categories=categories,
        hours_periods=_hours_by_location().get(csv_id, ()),
        attributes=_attributes_by_location().get(csv_id, ()),
    )


@lru_cache(maxsize=1)
def load_locations() -> tuple[ProviderLocation, ...]:
    """Every sample location, in the order the CSV lists them."""
    return tuple(_location(row) for row in _rows(LOCATIONS_FILE) if row.get("gbp_location_id"))


@lru_cache(maxsize=1)
def csv_id_by_google_name() -> dict[str, str]:
    """`locations/1029…` -> `LOC-001`, which is how the review CSVs address a location."""
    return {
        row["gbp_location_id"]: row["location_id"]
        for row in _rows(LOCATIONS_FILE)
        if row.get("gbp_location_id") and row.get("location_id")
    }


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SampleReviewRow:
    """One joined `reviews.csv` + `review_replies.csv` row.

    Kept provider-neutral rather than a `ProviderReview` so this module never has to
    import the reviews provider that imports it.
    """

    review_id: str
    star_rating: int
    comment: str
    reviewer_name: str
    created_at: datetime
    reply_comment: str | None = None
    reply_at: datetime | None = None


def _star_rating(raw: str) -> int:
    return min(max(int(raw), 1), 5) if raw.isdigit() else 1


@lru_cache(maxsize=1)
def load_reviews() -> dict[str, tuple[SampleReviewRow, ...]]:
    """Reviews with their owner reply already joined on, keyed by Google location name."""
    replies = {
        row["review_id"]: (row.get("reply_text", ""), _moment(row.get("replied_at", "")))
        for row in _rows(REPLIES_FILE)
        if row.get("review_id")
    }
    google_name_by_csv_id = {
        csv_id: google_name for google_name, csv_id in csv_id_by_google_name().items()
    }

    grouped: dict[str, list[SampleReviewRow]] = defaultdict(list)
    for row in _rows(REVIEWS_FILE):
        google_name = google_name_by_csv_id.get(row.get("location_id", ""))
        if google_name is None or not row.get("review_id"):
            continue  # a review whose location is not in the dataset has nowhere to live
        reply = replies.get(row["review_id"])
        created_at = _moment(row.get("created_at", ""))
        grouped[google_name].append(
            SampleReviewRow(
                review_id=row["review_id"],
                star_rating=_star_rating(row.get("rating", "")),
                comment=row.get("review_text", ""),
                reviewer_name=row.get("reviewer_name", ""),
                created_at=created_at or datetime.now(UTC),
                reply_comment=(reply[0] or None) if reply else None,
                reply_at=reply[1] if reply else None,
            )
        )
    return {google_name: tuple(items) for google_name, items in grouped.items()}
