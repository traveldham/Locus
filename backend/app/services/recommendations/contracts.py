"""Field contracts: roles are explicit even when a field does not drive a rule."""

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
    Review,
    SearchTermMonthly,
    TrackedKeyword,
)

TABLES = {
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
}

# Operational identifiers and dates are sufficient for the rules. Never copy customer
# identity or third-party auth identifiers into run snapshots or exported evidence.
EXCLUDED = {
    "organization_id",
    "connection_id",
    "external_account_id",
    "customer_name",
    "reviewer_display_name",
    "reviewer_photo_url",
    "created_at",
    "updated_at",
}
MEASURES = {
    "photo_count",
    "interior_photo_count",
    "exterior_photo_count",
    "team_photo_count",
    "video_count",
    "star_rating",
    "rank_absolute",
    "rank_in_local_pack",
    "impressions",
    "impressions_maps_desktop",
    "impressions_maps_mobile",
    "impressions_search_desktop",
    "impressions_search_mobile",
    "website_clicks",
    "call_clicks",
    "direction_requests",
    "conversations",
    "bookings",
    "review_count",
    "average_rating",
}
DATES = {
    "date",
    "week_start",
    "year_month",
    "create_time",
    "update_time",
    "reply_update_time",
    "last_synced_at",
    "last_photo_uploaded_on",
    "published_on",
    "booking_created_at",
    "requested_for_date",
    "tracking_started_on",
    "opening_date",
}


def field_contracts() -> dict:
    contracts = {}
    for name, model in TABLES.items():
        fields = {}
        for column in model.__table__.columns:
            key = column.key
            role = "context"
            if key in EXCLUDED:
                role = "excluded_identity_or_ingestion_metadata"
            elif key in MEASURES:
                role = "measurement"
            elif key in DATES:
                role = "observation_time"
            elif key == "id" or key.endswith("_id"):
                role = "join_or_evidence_key"
            fields[key] = {"type": str(column.type), "nullable": column.nullable, "role": role}
        contracts[name] = {"table": model.__tablename__, "fields": fields}
    return contracts


SEMANTICS = {
    "missing": "NULL is unknown; absent rows are not proof of zero activity.",
    "attributes": "FALSE is explicit; missing is unknown. Never infer a service exists.",
    "ranks": "Lower is better. Not found is a state, never rank zero.",
    "performance": "Actions are events, not unique customers or conversion probability.",
    "search_terms": "Monthly truncated reporting; do not reconcile with daily impressions.",
    "bookings": "CRM requests are separate from GBP booking counts; future visits not failed.",
    "competitors": "Compare only within the same keyword and week. No causal ranking claims.",
    "time": "As-of selects dated observations; mutable fields reflect current stored state.",
}
