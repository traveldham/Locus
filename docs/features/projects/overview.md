# Projects

A named folder of locations. One Google connection can feed many projects, and a location may
belong to several.

Code: `app/api/projects.py`, `app/models/project.py`. Screens:
`frontend/src/components/projects/`.

## Why it exists

The whole dashboard is **project-scoped**. The header carries a project switcher, `?project=`
in the URL is the source of truth, and almost every data hook passes the active project id
down to the API. A location that belongs to no project shows up in neither the profiles list
nor the audit directory.

A project also carries the operator's own description of the business — and that is not
decoration. Three audit checks read `Project.services`:

- `service_not_listed` (operations) — a requested service matching none of them
- `service_not_surfacing` (visibility) — a service no search term mentions
- `services_without_category` / `services_without_attribute` (profile) — a service whose usual
  Google category or attribute is missing

The suggestion layer also puts the project's name, description and services in every prompt,
which is what makes a drafted description about *this* business.

## The model

`projects`, unique on `(organization_id, slug)`.

```
name          2-160 characters
slug          derived, unique per organization
website_url   validated through HttpUrl; credentials in the URL are rejected
description   ≤5000 characters
services      JSON list, de-duplicated case-insensitively, ≤100 entries of 1-120 chars
status        active | archived
google_connection_id, created_by_user_id   both ON DELETE SET NULL
```

`ProjectLocation` is the join, unique on `(project_id, location_id)`.

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/projects` | Optional `status`; each row carries a location count |
| `POST` | `/api/v1/projects` | `201`. Queues an audit per location supplied |
| `GET` | `/api/v1/projects/{id}` | Detail |
| `PATCH` | `/api/v1/projects/{id}` | Partial update |
| `POST` | `/api/v1/projects/{id}/locations` | Adds links. **Queues an audit per location** |
| `DELETE` | `/api/v1/projects/{id}/locations/{location_id}` | Unlinks. The location itself stays |
| `DELETE` | `/api/v1/projects/{id}` | Deletes the project and its links, **not** the locations |

Details worth knowing:

- The slug is generated, truncated to 90 characters, and suffixed `-2`, `-3`, … until unique
  within the organization. A racing duplicate name is a **409**.
- Every submitted location id is validated to belong to the organization, else **400** naming
  the ids.
- Linking is idempotent — existing links are read first and only the missing ones inserted.
- `PATCH` applies `name` and `status` when not `None`, but applies `website_url`,
  `description` and `services` only when **present in the request**, so an explicit `null`
  clears them and an omitted field does not.
- Removing a location that is not in the project is a **404**.

## Audits are queued on membership change

Both `create_project` and `add_project_locations` call `enqueue_audits`, which skips any
location already having a `pending` or `running` job, builds one `AuditJob` per remaining
location with today's date and the default `EngineConfig`, each with its six worker rows, and
dispatches them.

So a profile never sits in a project unaudited. With no Celery worker running, the job simply
stays `pending` and the dashboard shows "Audit queued".

A project created with **no** locations queues nothing.

## `populate_business`

`app/sample_business.py` fills a project's business details from the sample CSVs — the website
host from `locations.csv`, the service list from the distinct `service` values in
`booking_requests.csv`, and a fixed description naming them.

It **only fills missing values**; it never overwrites an operator's own details. It is called
from exactly one place, `seed_project` in `app/seed.py`, and from no API endpoint.
