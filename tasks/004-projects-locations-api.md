# 004 — Projects + Locations API

**Status:** BUILT (unverified end to end) — 20 backend tests pass

## Goal

The read/write endpoints the dashboard runs on.

## Concept

A **Project** is a named folder of locations. One Google connection feeds many projects; a location can belong to several. `ProjectLocation` is many-to-many by design, so a user can build a new project from locations already imported — **without reconnecting Google**. No one-project-per-connection assumption may creep in anywhere.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/projects` | `location_count` via SQL aggregate, not by loading relationships |
| POST | `/api/v1/projects` | Slug unique **within the organization** |
| GET | `/api/v1/projects/{id}` | With locations |
| PATCH | `/api/v1/projects/{id}` | Rename / archive |
| POST | `/api/v1/projects/{id}/locations` | Idempotent — re-adding is a no-op |
| DELETE | `/api/v1/projects/{id}/locations/{lid}` | Unlinks only; the location survives |
| DELETE | `/api/v1/projects/{id}` | Deletes the project and links; locations survive |
| GET | `/api/v1/locations` | `project_id` filter, `q` search, paginated with a hard cap |
| GET | `/api/v1/locations/{id}` | Eager-loads categories, hours, attributes |

## Tenancy rule (security-critical)

Every query is scoped to the caller's organization. Out-of-organization resources return **404, not 403**, so IDs cannot be enumerated. This is covered by a test.

## Data shape notes

- Hours periods are returned raw. Do **not** collapse to one row per weekday — Google allows multiple periods per day and overnight spans where `close_day` differs from `open_day`.
- Attributes keep their `value_type` and JSON `values`. Do not stringify.
- `maps_uri` and `new_review_uri` must be returned when present. Some actions are only possible in Google's own dashboard, so the UI deep-links there — dropping these fields creates dead ends.

## Response conventions

- Both DELETE endpoints return **200 with `{"message": ...}`**, not 204 — matching the house style set by `auth.py`'s logout.
- `POST /projects/{id}/locations` returns the full `ProjectDetailResponse`, so the caller can refresh from the response instead of refetching.
- `LocationSummary.address` is a prebuilt single-line string; clients do not assemble it from parts.
- `PATCH` deliberately leaves the slug unchanged on rename, so existing links keep working.

## Implementation notes

- `location_count` comes from a grouped `func.count` subquery with `outerjoin` + `coalesce` — one query, no N+1.
- The `q` search escapes `%`, `_` and `\` so user input cannot inject wildcards.
- Unlink and project delete issue a core `DELETE` against `ProjectLocation` only. This never touches the `Location` rows and avoids an async lazy-load on the delete-orphan cascade.
- Org scoping lives in one place: the `OrganizationId` dependency in `app/api/scoping.py`.

## Verification

Tests cover auth, create/list/get, rename/archive, per-org slug uniqueness **and** a second org reusing the same slug, idempotent adds (including duplicate IDs within one request body), unlink keeping the location and its membership in other projects, project deletion not cascading to locations, filtering/search/pagination and the limit cap, **cross-organization access returning 404**, and a foreign location ID smuggled into a create being rejected with 400 rather than silently succeeding.
