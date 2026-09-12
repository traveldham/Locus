"""Reviews provider — reading reviews and writing owner replies.

Reviews sit on a different Google surface from everything in `providers/base.py`: they
were never migrated to the split v1 services and are still v4 only, addressed by the
account-qualified name stored on `Location.google_resource_name` rather than the v1
`locations/{id}` form in `google_location_name`. That constraint is preserved here: a
location missing the account-qualified name cannot have its reviews fetched at all, and
that is surfaced as a provider error rather than a silently empty inbox.

The data itself comes from `reviews.csv` joined to `review_replies.csv`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.services.providers.base import ProviderError
from app.services.providers.sample_data import SampleReviewRow, load_reviews

if TYPE_CHECKING:
    from app.models import GoogleConnection, Location


@dataclass(frozen=True, slots=True)
class ProviderReview:
    """One review plus its owner reply, in our shape."""

    google_review_id: str
    star_rating: int
    create_time: datetime
    google_review_name: str | None = None
    reviewer_display_name: str | None = None
    reviewer_photo_url: str | None = None
    is_anonymous: bool = False
    comment: str | None = None
    update_time: datetime | None = None
    reply_comment: str | None = None
    reply_update_time: datetime | None = None


@runtime_checkable
class ReviewsProvider(Protocol):
    """The only reviews surface the API layer knows about."""

    name: str

    async def list_reviews(
        self, connection: GoogleConnection, location: Location
    ) -> list[ProviderReview]: ...

    async def reply(
        self,
        connection: GoogleConnection,
        location: Location,
        google_review_id: str,
        comment: str,
    ) -> ProviderReview: ...

    async def delete_reply(
        self, connection: GoogleConnection, location: Location, google_review_id: str
    ) -> None: ...


def account_qualified_name(location: Location) -> str:
    """The `accounts/{a}/locations/{l}` name the v4 reviews endpoints require."""
    resource_name = (location.google_resource_name or "").strip()
    if not resource_name:
        raise ProviderError(
            f"{location.title!r} has no account-qualified Google resource name "
            "(accounts/{account}/locations/{location}), which the v4 reviews API requires. "
            "Re-run the seed for this location."
        )
    return resource_name


# Replies written against the sample dataset, keyed by (location name, review id). `None`
# records a deleted reply, which is different from never having had one. The CSVs are
# read-only, so this is what lets a reply survive the round trip back into the inbox.
_sample_replies: dict[tuple[str, str], tuple[str, datetime] | None] = {}


def forget_sample_replies() -> None:
    """Drop every in-process reply, returning the inbox to what the CSVs say."""
    _sample_replies.clear()


class SampleReviewsProvider:
    """Serves `reviews.csv` joined to `review_replies.csv`, and remembers owner replies."""

    name = "sample"

    def _to_review(self, location: Location, row: SampleReviewRow) -> ProviderReview:
        qualified = account_qualified_name(location)
        review = ProviderReview(
            google_review_id=row.review_id,
            google_review_name=f"{qualified}/reviews/{row.review_id}",
            star_rating=row.star_rating,
            create_time=row.created_at,
            update_time=row.created_at,
            reviewer_display_name=row.reviewer_name or None,
            comment=row.comment or None,
            reply_comment=row.reply_comment,
            reply_update_time=row.reply_at,
        )
        key = (location.google_location_name, row.review_id)
        if key not in _sample_replies:
            return review
        override = _sample_replies[key]
        if override is None:
            return replace(review, reply_comment=None, reply_update_time=None)
        return replace(review, reply_comment=override[0], reply_update_time=override[1])

    async def list_reviews(
        self, connection: GoogleConnection, location: Location
    ) -> list[ProviderReview]:
        del connection
        rows = load_reviews().get(location.google_location_name, ())
        return [self._to_review(location, row) for row in rows]

    async def reply(
        self,
        connection: GoogleConnection,
        location: Location,
        google_review_id: str,
        comment: str,
    ) -> ProviderReview:
        del connection
        rows = load_reviews().get(location.google_location_name, ())
        row = next((item for item in rows if item.review_id == google_review_id), None)
        if row is None:
            raise ProviderError(
                f"Review {google_review_id} is not part of the sample dataset for "
                f"{location.title!r}."
            )
        _sample_replies[(location.google_location_name, google_review_id)] = (
            comment,
            datetime.now(UTC),
        )
        return self._to_review(location, row)

    async def delete_reply(
        self, connection: GoogleConnection, location: Location, google_review_id: str
    ) -> None:
        del connection
        _sample_replies[(location.google_location_name, google_review_id)] = None


def get_reviews_provider() -> ReviewsProvider:
    """The reviews provider. There is only one, and it reads the sample CSVs."""
    return SampleReviewsProvider()
