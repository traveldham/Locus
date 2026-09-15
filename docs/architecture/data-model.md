# Data model

Roughly thirty tables. Every one is scoped to an organization, directly or through its parent.

## Identity and tenancy

| Table | Holds |
| --- | --- |
| `users` | `email` unique, `full_name`, `password_hash` **nullable**, `is_active` |
| `user_identities` | OAuth subjects — unique `(provider, subject)`. Written by nothing today |
| `organizations` | `name`, `slug` unique |
| `organization_memberships` | unique `(user_id, organization_id)`, `role` = owner / admin / member |
| `refresh_sessions` | `token_digest` (SHA-256, unique), `expires_at`, `revoked_at` |

`password_hash` is nullable because a user who signed up through Google never set one.

## Connection

| Table | Holds |
| --- | --- |
| `google_connections` | unique `(organization_id, google_subject)`; scopes, status, a placeholder refresh token |
| `external_accounts` | unique `(connection_id, resource_name)` — a Google `accounts/123` |

## The profile

| Table | Holds |
| --- | --- |
| `locations` | unique **`(organization_id, google_location_name)`** — the natural key everything hangs off |
| `location_categories` | `category_name`, `display_name`, `is_primary` |
| `location_hours_periods` | one row per opening period; never collapsed to one per weekday |
| `location_attribute_values` | unique `(location_id, attribute_id)`; `values` is JSON because Google attributes are typed |
| `attribute_catalog_items` | unique `(organization_id, external_attribute_id)` — the menu Google offers for a category |

`locations` keeps **both** Google identity forms: `google_location_name` (`locations/123`, v1)
and `google_resource_name` (`accounts/1/locations/123`, v4 — which reviews still need), plus
`source_location_id` (`LOC-001`, the assignment dataset's key).

## Projects

| Table | Holds |
| --- | --- |
| `projects` | unique `(organization_id, slug)`; `website_url`, `description`, `services` (JSON) |
| `project_locations` | unique `(project_id, location_id)` — many-to-many |

## Customer-facing data

| Table | Key | Notes |
| --- | --- | --- |
| `reviews` | `(location_id, google_review_id)` | The owner reply is **inline**, not a child table |
| `posts` | `(location_id, google_post_id)` | `post_type` enum, `cta_type` nullable |
| `media_summary` | `(location_id)` — one row | Counts, not photos |
| `bookings` | `(location_id, external_booking_id)` | `source = locus` always |

## Analytics

| Table | Key | Notes |
| --- | --- | --- |
| `performance_daily` | `(location_id, date)` | Nine metrics, **all nullable** |
| `search_terms_monthly` | `(location_id, year_month, search_term)` | `year_month` is `String(7)` |
| `tracked_keywords` | `(location_id, external_keyword_id)` | `source = locus` |
| `keyword_ranks` | `(tracked_keyword_id, week_start)` | `rank_absolute` NULL = not found |
| `competitor_observations` | **no unique key** | Hangs off the keyword; a keyword-week holds several |

## The audit

| Table | Holds |
| --- | --- |
| `recommendation_runs` | The **current** audit of one profile: `report` JSON, `snapshot` JSON, `fingerprint`, `engine_version`. No history — a new run replaces the old |
| `audit_jobs` | One pipeline per request: status, `as_of`, `config`, the snapshot while running, `run_id`, `error` |
| `audit_workers` | Six per job, unique `(job_id, category)`: status, stage, `result` JSON, error, timings |
| `audit_check_history` | One row per check per audit — enough to say fixed / new / unchanged without keeping the audits |
| `audit_score_history` | The health score of every audit a location has had |

The two history tables carry `run_id` as a plain UUID with **no foreign key**, deliberately:
the run they refer to is deleted when the next audit replaces it, and the history must
survive that.

## The agent

| Table | Holds |
| --- | --- |
| `agent_conversations` | One per chat; `location_id` **NOT NULL** — a chat with no location is an agent with no boundary |
| `agent_messages` | `role` = user / assistant / tool; `content`, `tool_calls` (JSON), `tool_call_id`, `tool_name` |
| `agent_turns` | One per user message; partial unique index enforces **one live turn per conversation** |

## Audit trail and sync

| Table | Holds |
| --- | --- |
| `profile_actions` | Every write we send to Google: who, what, the update mask, the before/after, the status, the provider's reply |
| `sync_runs` | One execution of a background pull: kind, status, `records_written`, error |

`profile_actions.user_id` is `ON DELETE SET NULL`, so the trail outlives the user.

## Conventions

- **UUID primary keys**, `default=uuid4`, everywhere.
- **`TimestampMixin`** (`created_at`, `updated_at`) on most tables — but note `Booking` has
  both `created_at` (when *we* wrote the row) and `booking_created_at` (when the customer
  made the request). They are different facts, and the API returns the second.
- **`ondelete="CASCADE"`** down every ownership edge; **`SET NULL`** where the record must
  outlive its referent (`user_id` on an action, `run_id` on a job).
- **Enums are `StrEnum`** and named in the database, so a migration can alter them.
- **Nullable means unknown.** No metric defaults to zero.

## Migrations

Fifteen files, one linear chain, head `20260914_0015`. Three are worth knowing because they
**deleted data** deliberately rather than migrating it:

- `0009` made runs and jobs per-location; the old org-wide rows were unattributable, so they
  were deleted.
- `0010` split an audit into six worker rows; the rule set had changed, so old results were
  meaningless.
- `0015` reverted `0014`'s project-scoped agent conversations and deleted the conversations
  that had no location.

Run them with `uv run alembic upgrade head`.
