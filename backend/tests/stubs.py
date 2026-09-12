"""In-memory stand-ins for the Google Business Profile providers.

Made-up data lives here and only here: the application ships no sample dataset, so the
suite supplies its own. Nothing in this module touches the network — every call is
answered from the tuples below, which is what lets the whole API be exercised offline.

The datasets are deliberately tiny and hand-checkable, so a test can assert an exact
count rather than a magic number copied out of a CSV.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.models import LocationSource, OpenStatus
from app.services.providers.base import (
    LocationChanges,
    ProviderAccount,
    ProviderAttribute,
    ProviderCategory,
    ProviderHoursPeriod,
    ProviderLocation,
    UpdateResult,
    build_update_mask,
    validate_changes,
)
from app.services.providers.reviews import ProviderReview

if TYPE_CHECKING:
    from app.models import GoogleConnection, Location

STUB_ACCOUNT = ProviderAccount(
    resource_name="accounts/800000000000000000001",
    account_name="Stub Business Group",
    account_type="LOCATION_GROUP",
    role="PRIMARY_OWNER",
    verification_state="VERIFIED",
)

RIVERSIDE = "locations/8000000000000000001"
HARBOUR_POINT = "locations/8000000000000000002"
OLD_MILL = "locations/8000000000000000003"


def resource_name(google_location_name: str) -> str:
    """The account-qualified name the v4 reviews API needs."""
    return f"{STUB_ACCOUNT.resource_name}/{google_location_name}"


_WEEKDAY_HOURS = tuple(
    ProviderHoursPeriod(open_day=day, open_hour=9, close_day=day, close_hour=17)
    for day in ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
)

# Three locations: one complete, one missing the fields the "Incomplete" chip looks for,
# one complete again. That is enough to test listing, filtering, paging and editing.
STUB_LOCATIONS: tuple[ProviderLocation, ...] = (
    ProviderLocation(
        google_location_name=RIVERSIDE,
        google_resource_name=resource_name(RIVERSIDE),
        place_id="ChIJstub0000000001",
        store_code="RVS-01",
        title="Riverside Studio",
        primary_category_name="categories/gcid:dentist",
        primary_category_display="Dentist",
        address_lines=("12 Riverside Walk",),
        locality="Bristol",
        administrative_area="England",
        postal_code="BS1 4RN",
        region_code="GB",
        latitude=51.4511,
        longitude=-2.5983,
        phone_primary="+44 117 555 0101",
        website_uri="https://riverside.example.com",
        description="A dental studio beside the harbour.",
        open_status=OpenStatus.open,
        has_voice_of_merchant=True,
        maps_uri="https://maps.google.com/?cid=8000000000000000001",
        new_review_uri="https://search.google.com/local/writereview?placeid=ChIJstub0000000001",
        categories=(
            ProviderCategory(
                category_name="categories/gcid:dentist", display_name="Dentist", is_primary=True
            ),
        ),
        hours_periods=_WEEKDAY_HOURS,
        attributes=(
            ProviderAttribute(
                attribute_id="attributes/has_wheelchair_accessible_entrance",
                value_type="BOOL",
                values=(True,),
            ),
        ),
    ),
    ProviderLocation(
        google_location_name=HARBOUR_POINT,
        google_resource_name=resource_name(HARBOUR_POINT),
        place_id="ChIJstub0000000002",
        store_code="HBP-02",
        title="Harbour Point Practice",
        primary_category_name="categories/gcid:dentist",
        primary_category_display="Dentist",
        address_lines=("4 Harbour Point",),
        locality="Bristol",
        administrative_area="England",
        postal_code="BS1 5TY",
        region_code="GB",
        phone_primary="+44 117 555 0102",
        # No description and no website: this is the incomplete profile.
        open_status=OpenStatus.open,
        has_voice_of_merchant=False,
        has_pending_edits=True,
        categories=(
            ProviderCategory(
                category_name="categories/gcid:dentist", display_name="Dentist", is_primary=True
            ),
        ),
        hours_periods=_WEEKDAY_HOURS,
    ),
    ProviderLocation(
        google_location_name=OLD_MILL,
        google_resource_name=resource_name(OLD_MILL),
        place_id="ChIJstub0000000003",
        store_code="OML-03",
        title="Old Mill Clinic",
        primary_category_name="categories/gcid:orthodontist",
        primary_category_display="Orthodontist",
        address_lines=("90 Mill Lane",),
        locality="Bath",
        administrative_area="England",
        postal_code="BA1 1QP",
        region_code="GB",
        phone_primary="+44 1225 555 0103",
        website_uri="https://oldmill.example.com",
        description="Orthodontics in central Bath.",
        open_status=OpenStatus.open,
        has_voice_of_merchant=True,
        categories=(
            ProviderCategory(
                category_name="categories/gcid:orthodontist",
                display_name="Orthodontist",
                is_primary=True,
            ),
            ProviderCategory(
                category_name="categories/gcid:dentist", display_name="Dentist", is_primary=False
            ),
        ),
        hours_periods=_WEEKDAY_HOURS,
    ),
)

LOCATION_COUNT = len(STUB_LOCATIONS)


class StubGbpProvider:
    """Answers account and location reads from `STUB_LOCATIONS`, and validates writes."""

    name = "stub"
    location_source = LocationSource.google

    async def list_accounts(self, connection: GoogleConnection) -> list[ProviderAccount]:
        del connection
        return [STUB_ACCOUNT]

    async def list_locations(
        self, connection: GoogleConnection, account_resource_name: str
    ) -> list[ProviderLocation]:
        del connection
        if account_resource_name and account_resource_name != STUB_ACCOUNT.resource_name:
            return []
        return list(STUB_LOCATIONS)

    async def update_location(
        self,
        connection: GoogleConnection | None,
        location: Location,
        changes: LocationChanges,
        *,
        validate_only: bool,
    ) -> UpdateResult:
        """Apply the same field rules the live provider asks Google to apply.

        A dry run has to be able to *fail*, so the shared validation in `providers.base`
        stands in for Google's `fieldViolations`.
        """
        del connection
        mask = build_update_mask(changes)
        if not mask:
            return UpdateResult(ok=False, error="No fields to update")

        errors = validate_changes(changes)
        if errors:
            return UpdateResult(ok=False, field_errors=errors, applied_mask=mask)

        return UpdateResult(
            ok=True,
            applied_mask=mask,
            response={
                "provider": "stub",
                "name": location.google_location_name,
                "updateMask": ",".join(mask),
                "validateOnly": validate_only,
            },
        )


def _review(
    review_id: str,
    star_rating: int,
    day: int,
    comment: str,
    reviewer: str,
    reply: str | None = None,
) -> ProviderReview:
    return ProviderReview(
        google_review_id=review_id,
        star_rating=star_rating,
        create_time=datetime(2026, 5, day, 12, 0, tzinfo=UTC),
        reviewer_display_name=reviewer,
        comment=comment,
        reply_comment=reply,
        reply_update_time=datetime(2026, 5, day + 1, 9, 0, tzinfo=UTC) if reply else None,
    )


# Eight reviews over two locations: five at Riverside (three of them replied to) and three
# at Harbour Point. Both locations have exactly one one-star review, and "parking" appears
# in exactly two Riverside comments, so search and filter counts are exact.
STUB_REVIEWS: dict[str, tuple[ProviderReview, ...]] = {
    RIVERSIDE: (
        _review(
            "RVS-R1",
            5,
            1,
            "Fantastic visit, everything explained clearly.",
            "Alex R.",
            "Thank you!",
        ),
        _review(
            "RVS-R2", 4, 3, "Good care, though parking was tricky.", "Priya S.", "Sorry about that."
        ),
        _review("RVS-R3", 1, 5, "Waited forty minutes past my appointment.", "Jordan M."),
        _review(
            "RVS-R4", 5, 7, "Easy parking and a friendly front desk.", "Sam T.", "Glad to hear it."
        ),
        _review("RVS-R5", 3, 9, "Fine, nothing out of the ordinary.", "Chris L."),
    ),
    HARBOUR_POINT: (
        _review("HBP-R1", 2, 2, "The hygienist was lovely but the wait was long.", "Dana P."),
        _review("HBP-R2", 1, 4, "Called three times and nobody answered.", "Ravi K."),
        _review("HBP-R3", 5, 6, "Best cleaning I have had.", "Mo N.", "Thanks so much!"),
    ),
}

RIVERSIDE_REVIEW_COUNT = len(STUB_REVIEWS[RIVERSIDE])
HARBOUR_POINT_REVIEW_COUNT = len(STUB_REVIEWS[HARBOUR_POINT])
RIVERSIDE_REPLIED_COUNT = sum(1 for item in STUB_REVIEWS[RIVERSIDE] if item.reply_comment)


class StubReviewsProvider:
    """Serves `STUB_REVIEWS` and remembers replies for the lifetime of one test.

    Replies are kept per instance rather than in a module global, so each test starts
    from the declared dataset with no reset step to forget.
    """

    name = "stub"

    def __init__(self) -> None:
        # (google_location_name, review_id) -> (comment, updated_at), or None when deleted.
        self._replies: dict[tuple[str, str], tuple[str, datetime] | None] = {}

    def _with_reply(self, google_location_name: str, review: ProviderReview) -> ProviderReview:
        key = (google_location_name, review.google_review_id)
        if key not in self._replies:
            return review
        override = self._replies[key]
        if override is None:
            return replace(review, reply_comment=None, reply_update_time=None)
        return replace(review, reply_comment=override[0], reply_update_time=override[1])

    def _reviews_for(self, location: Location) -> tuple[ProviderReview, ...]:
        name = location.google_location_name
        qualified = (location.google_resource_name or "").strip()
        return tuple(
            replace(
                self._with_reply(name, review),
                google_review_name=(
                    f"{qualified}/reviews/{review.google_review_id}" if qualified else None
                ),
            )
            for review in STUB_REVIEWS.get(name, ())
        )

    async def list_reviews(
        self, connection: GoogleConnection, location: Location
    ) -> list[ProviderReview]:
        del connection
        return list(self._reviews_for(location))

    async def reply(
        self,
        connection: GoogleConnection,
        location: Location,
        google_review_id: str,
        comment: str,
    ) -> ProviderReview:
        del connection
        self._replies[(location.google_location_name, google_review_id)] = (
            comment,
            datetime.now(UTC),
        )
        for review in self._reviews_for(location):
            if review.google_review_id == google_review_id:
                return review
        raise AssertionError(f"Review {google_review_id} is not part of the stub dataset")

    async def delete_reply(
        self, connection: GoogleConnection, location: Location, google_review_id: str
    ) -> None:
        del connection
        self._replies[(location.google_location_name, google_review_id)] = None
