"""The sample provider, exercised directly against the CSVs it ships with.

These are the only tests that touch the sample dataset. Every API-level test keeps its
own hand-written stubs in `tests/stubs.py`, so an exact count here can be asserted
against the real CSVs without any endpoint test depending on their contents.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.models import Location, LocationSource, OpenStatus
from app.services.providers import get_provider
from app.services.providers.base import (
    LocationChanges,
    ProviderCategory,
    ProviderError,
    ProviderHoursPeriod,
)
from app.services.providers.reviews import (
    SampleReviewsProvider,
    forget_sample_replies,
    get_reviews_provider,
)
from app.services.providers.sample import SampleGbpProvider, forget_edits
from app.services.providers.sample_data import (
    SAMPLE_ACCOUNT,
    clear_cache,
    data_dir,
    load_locations,
    load_reviews,
)

# Counts taken from the CSVs themselves, so a change to the dataset fails loudly here
# rather than quietly changing what the product shows.
LOCATION_COUNT = 12
REVIEW_COUNT = 1514
REPLY_COUNT = 874
MUELLER = "locations/10293847561122334455"
ROUND_ROCK = "locations/10293847561122334457"


@pytest.fixture(autouse=True)
def clean_sample_state() -> Iterator[None]:
    """Every test starts from the CSVs, with no edit or reply left over from another."""
    clear_cache()
    forget_edits()
    forget_sample_replies()
    yield
    clear_cache()
    forget_edits()
    forget_sample_replies()


def sample_location(google_location_name: str = MUELLER) -> Location:
    """A stored location as import would have written it, without touching a database."""
    return Location(
        google_location_name=google_location_name,
        google_resource_name=f"{SAMPLE_ACCOUNT.resource_name}/{google_location_name}",
        title="Brightpath Dental — Mueller",
        source=LocationSource.fixture,
    )


def by_name(google_location_name: str):
    return next(
        item for item in load_locations() if item.google_location_name == google_location_name
    )


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def test_the_sample_provider_is_the_only_provider() -> None:
    """Nothing is configurable any more: there is one provider and it reads the CSVs."""
    provider = get_provider()
    assert isinstance(provider, SampleGbpProvider)
    # Locations it creates are tagged as sample data, which the API and UI both surface.
    assert provider.location_source is LocationSource.fixture
    assert isinstance(get_reviews_provider(), SampleReviewsProvider)


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------


async def test_lists_every_location_under_one_account() -> None:
    provider = SampleGbpProvider()

    assert [account.resource_name for account in await provider.list_accounts(None)] == [
        SAMPLE_ACCOUNT.resource_name
    ]
    locations = await provider.list_locations(None, SAMPLE_ACCOUNT.resource_name)
    assert len(locations) == LOCATION_COUNT
    assert await provider.list_locations(None, "accounts/999") == []


def test_identity_uses_the_csv_location_name_and_a_qualified_resource_name() -> None:
    mueller = by_name(MUELLER)
    assert mueller.google_location_name == MUELLER
    # The v4 reviews API cannot address a location without the account-qualified form.
    assert mueller.google_resource_name == f"{SAMPLE_ACCOUNT.resource_name}/{MUELLER}"


def test_maps_into_the_google_shape_not_the_flat_csv_shape() -> None:
    mueller = by_name(MUELLER)
    assert mueller.title == "Brightpath Dental — Mueller"
    assert mueller.open_status is OpenStatus.open
    # `verified` in the CSV is Google's "voice of merchant", which is what the UI reads.
    assert mueller.has_voice_of_merchant is True
    assert mueller.opening_date is not None and mueller.opening_date.year == 2016
    assert mueller.primary_category_name == "categories/gcid:dentist"
    assert mueller.primary_category_display == "Dentist"
    assert [item.display_name for item in mueller.categories] == [
        "Dentist",
        "Cosmetic dentist",
        "Teeth whitening service",
    ]
    assert sum(1 for item in mueller.categories if item.is_primary) == 1


def test_hours_become_periods_and_blank_rows_are_skipped() -> None:
    mueller = by_name(MUELLER)
    days = [period.open_day for period in mueller.hours_periods]

    # Seven CSV rows, six of them with times: the blank Sunday row is a closed day.
    assert days == ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]
    assert "SUNDAY" not in days
    monday = mueller.hours_periods[0]
    assert (monday.open_hour, monday.open_minute) == (8, 0)
    assert (monday.close_hour, monday.close_minute) == (17, 0)
    assert monday.close_day == monday.open_day
    assert monday.hours_type == "REGULAR"

    # Round Rock closes both weekend days, so it carries two fewer periods.
    assert len(by_name(ROUND_ROCK).hours_periods) == 5


def test_attributes_keep_the_type_their_catalog_entry_declares() -> None:
    attributes = {item.attribute_id: item for item in by_name(MUELLER).attributes}

    wheelchair = attributes["attributes/wheelchair_accessible_restroom"]
    assert wheelchair.value_type == "BOOL"
    assert wheelchair.values == (True,)
    assert attributes["attributes/wheelchair_accessible_entrance"].values == (False,)

    # The one enum in the catalog must not be flattened into a boolean.
    language = attributes["attributes/language_assistance"]
    assert language.value_type == "ENUM"
    assert language.values == ("FALSE",)


def test_genuinely_empty_profiles_stay_empty() -> None:
    """The incomplete profiles are the data's, not ours — the UI has to be able to say so."""
    round_rock = by_name(ROUND_ROCK)
    assert round_rock.description is None
    assert round_rock.website_uri is None
    assert any(item.description for item in load_locations())


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


async def test_update_location_rejects_what_google_would_reject() -> None:
    provider = SampleGbpProvider()
    result = await provider.update_location(
        None,
        sample_location(),
        LocationChanges(title="", website_uri="not-a-url"),
        validate_only=True,
    )

    assert result.ok is False
    assert set(result.field_errors) == {"title", "website_uri"}
    assert result.applied_mask == ["title", "websiteUri"]


async def test_update_location_with_nothing_to_change_is_refused() -> None:
    result = await SampleGbpProvider().update_location(
        None, sample_location(), LocationChanges(), validate_only=False
    )
    assert result.ok is False
    assert result.error == "No fields to update"


async def test_a_preview_changes_nothing_and_a_confirm_sticks() -> None:
    provider = SampleGbpProvider()
    changes = LocationChanges(
        description="Now open on Sundays.",
        hours_periods=(
            ProviderHoursPeriod(open_day="SUNDAY", open_hour=10, close_day="SUNDAY", close_hour=16),
        ),
        primary_category=ProviderCategory(
            category_name="categories/gcid:orthodontist", display_name="Orthodontist"
        ),
    )
    location = sample_location()

    preview = await provider.update_location(None, location, changes, validate_only=True)
    assert preview.ok is True
    assert by_name(MUELLER).description != "Now open on Sundays."

    applied = await provider.update_location(None, location, changes, validate_only=False)
    assert applied.ok is True
    assert applied.applied_mask == ["profile", "regularHours", "categories"]

    updated = next(
        item
        for item in await provider.list_locations(None, SAMPLE_ACCOUNT.resource_name)
        if item.google_location_name == MUELLER
    )
    assert updated.description == "Now open on Sundays."
    assert [period.open_day for period in updated.hours_periods] == ["SUNDAY"]
    assert updated.primary_category_display == "Orthodontist"
    # Swapping the primary category keeps the additional ones, as Google does.
    assert [item.display_name for item in updated.categories if not item.is_primary] == [
        "Cosmetic dentist",
        "Teeth whitening service",
    ]


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


def test_reviews_join_their_replies() -> None:
    reviews = load_reviews()
    assert sum(len(rows) for rows in reviews.values()) == REVIEW_COUNT
    assert sum(1 for rows in reviews.values() for row in rows if row.reply_comment) == REPLY_COUNT

    first = reviews[MUELLER][0]
    assert first.review_id == "REV-00001"
    assert first.star_rating == 5
    assert first.created_at == datetime(2026, 7, 25, tzinfo=UTC)
    assert first.reply_comment is not None
    assert first.reply_at == datetime(2026, 7, 27, tzinfo=UTC)


async def test_reviews_are_served_for_the_location_that_owns_them() -> None:
    provider = SampleReviewsProvider()
    reviews = await provider.list_reviews(None, sample_location())

    assert len(reviews) == len(load_reviews()[MUELLER])
    assert all(review.google_review_name.endswith(review.google_review_id) for review in reviews)
    assert all(
        review.google_review_name.startswith(SAMPLE_ACCOUNT.resource_name) for review in reviews
    )


async def test_replying_and_removing_the_reply_round_trip() -> None:
    provider = SampleReviewsProvider()
    location = sample_location()
    unreplied = next(
        review
        for review in await provider.list_reviews(None, location)
        if review.reply_comment is None
    )

    written = await provider.reply(None, location, unreplied.google_review_id, "Thank you.")
    assert written.reply_comment == "Thank you."
    listed = {
        review.google_review_id: review for review in await provider.list_reviews(None, location)
    }
    assert listed[unreplied.google_review_id].reply_comment == "Thank you."

    await provider.delete_reply(None, location, unreplied.google_review_id)
    listed = {
        review.google_review_id: review for review in await provider.list_reviews(None, location)
    }
    assert listed[unreplied.google_review_id].reply_comment is None


async def test_a_location_without_a_qualified_name_cannot_have_reviews() -> None:
    location = sample_location()
    location.google_resource_name = None
    with pytest.raises(ProviderError, match="accounts/"):
        await SampleReviewsProvider().list_reviews(None, location)


# ---------------------------------------------------------------------------
# A missing dataset
# ---------------------------------------------------------------------------


def test_a_missing_dataset_directory_names_the_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing = tmp_path / "no-such-dataset"
    monkeypatch.setattr("app.services.providers.sample_data.data_dir", lambda: missing)

    with pytest.raises(ProviderError) as excinfo:
        load_locations()
    message = str(excinfo.value)
    assert str(missing) in message
    assert "SAMPLE_DATA_DIR" in message


def test_an_incomplete_dataset_names_the_missing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "locations.csv").write_text("location_id,gbp_location_id\n", encoding="utf-8")
    monkeypatch.setattr("app.services.providers.sample_data.data_dir", lambda: tmp_path)

    with pytest.raises(ProviderError) as excinfo:
        load_reviews()
    assert str(tmp_path / "review_replies.csv") in str(excinfo.value)


def test_the_default_dataset_directory_is_the_checked_out_one() -> None:
    assert data_dir().name == "data"
    assert (data_dir() / "locations.csv").is_file()
