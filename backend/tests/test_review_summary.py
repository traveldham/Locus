from datetime import UTC, datetime
from uuid import UUID

from conftest import sign_in
from sqlalchemy import select
from test_reviews import seed_location

from app.models import Review


async def test_summary_counts_all_reviews_updates_and_is_tenant_scoped(client, session_factory):
    assert (await client.get("/api/v1/reviews/summary")).status_code == 401
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Preview location", "locations/preview")
    path = f"/api/v1/reviews/summary?location_id={location_id}"
    empty = (await client.get(path, headers=headers)).json()
    assert empty["total"] == 0 and empty["average"] is None
    async with session_factory() as db:
        db.add_all(
            [
                Review(
                    organization_id=org,
                    location_id=UUID(location_id),
                    google_review_id=f"r{i}",
                    star_rating=5 if i < 200 else 1,
                    create_time=datetime.now(UTC),
                )
                for i in range(201)
            ]
        )
        await db.commit()
    response = await client.get(path, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 201
    assert body["average"] == round(1001 / 201, 2)
    assert body["distribution"] == {"1": 1, "2": 0, "3": 0, "4": 0, "5": 200}
    async with session_factory() as db:
        review = await db.scalar(select(Review).where(Review.google_review_id == "r200"))
        review.star_rating = 5
        await db.commit()
    assert (await client.get(path, headers=headers)).json()["average"] == 5
    other, _ = await sign_in(client, "preview-other@example.org", "Other organization")
    assert (await client.get(path, headers=other)).status_code == 404
