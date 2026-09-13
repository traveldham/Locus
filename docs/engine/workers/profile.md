# Profile worker

Category `profile`, weight 20. Module: `backend/app/services/recommendations/categories/profile.py`.
Suggestion layer: `backend/app/services/recommendations/suggestions/` (provider service in `llm.py`).

## What it answers

Is the customer-facing listing complete, correct and verified? Five groups of checks.
Every check is deterministic. A permanently closed profile suppresses every check.

| Group | Rule | Weight | Severity | Fails when | Abstains when |
| --- | --- | --- | --- | --- | --- |
| Reach | `phone_missing` | 3 | critical | phone empty | never |
| Reach | `website_missing` | 3 | critical | website empty | never |
| Reach | `website_not_https` | 1 | notice | link not `https://` | website missing |
| Reach | `address_incomplete` | 2 | warning | city, state or postal code empty; street line empty on Google-sourced profiles | never |
| Reach | `pin_missing` | 1 | notice | latitude or longitude empty | never |
| Identity | `primary_category_missing` | 3 | critical | no primary category | never |
| Identity | `secondary_categories_few` | 1 | notice | additional categories below `min_additional_categories` (2) | no category rows synced |
| Identity | `category_attribute_mismatch` | 1 | notice | a listed category's service attribute is explicitly false, one finding per category | no category has an answered matching attribute |
| Trust | `unverified` | 3 | critical | Voice of Merchant false | never (confidence medium on sample data) |
| Trust | `temporarily_closed` | 2 | warning | open status is temporarily closed | open status unknown |
| Trust | `opening_date_missing` | 1 | notice | opening date empty | never |
| Trust | `description_missing` | 2 | warning | description empty | never |
| Trust | `description_short` | 2 | warning | under `description_min_chars` (250) | description missing |
| Trust | `description_too_long` | 1 | notice | over `description_max_chars` (750, Google's cap) | description missing |
| Trust | `description_keyword_stuffed` | 1 | notice | category or city word repeated `description_max_term_repeats` (4) or more times | description missing, or no category and city to look for |
| Trust | `name_keyword_stuffed` | 1 | notice | name carries both the category and the city, or repeats the category word; a branch suffix with the city alone is normal | name empty |
| Trust | `logo_missing` | 2 | warning | photo summary marks profile photo false | no summary, or flag unknown |
| Trust | `cover_photo_missing` | 2 | warning | photo summary marks cover photo false | no summary, or flag unknown |
| Hours | `hours_missing` | 3 | critical | no regular hours rows | never |
| Hours | `hours_weekday_gaps` | 2 | warning | a weekday Monday to Friday has no hours, one finding per day | no hours at all |
| Hours | `saturday_hours_inconsistent` | 1 | notice | Saturday appointments attribute true and no Saturday hours | attribute unanswered |
| Attributes | `attributes_sparse` | 2 | warning | answered share of the category catalog below `attribute_coverage_min` (0.5) | no catalog for the category |
| Attributes | `accessibility_unanswered` | 2 | warning | an accessibility attribute has no answer, one finding per attribute | no catalog, or no accessibility group |

Semantics that matter:

- Null is missing. Blank strings are missing.
- An attribute with no row is unknown, never false. An explicit no is an answer.
- Attribute values may arrive as booleans or as the strings `TRUE` and `FALSE`; both are read.
- The attribute catalog is organization-wide and is read from the snapshot directly, filtered to the primary category.
- The street line is only required of Google-sourced profiles, because the sample export never carries one.
- Every threshold is a field on `EngineConfig` and is an operating policy, except the 750 character description cap, which is Google's.

## Suggestions

After the checks run, the worker task calls the suggestion layer. It asks the configured
language model for one draft per finding whose check declares a `suggests` field:

| Check | Field drafted | Shape |
| --- | --- | --- |
| `description_missing`, `description_short`, `description_too_long`, `description_keyword_stuffed` | `description` | text, at most 750 characters, no links or promotions |
| `secondary_categories_few` | `additional_categories` | list of Google category names |
| `attributes_sparse`, `accessibility_unanswered`, `category_attribute_mismatch` | `attributes` | map of catalog attribute name to yes or no |
| `name_keyword_stuffed` | `title` | the real-world name |

The prompt carries the stored profile (name, categories, city, website, description,
hours, attributes answered yes, no, and unanswered) and every project the location
belongs to (name, website, description, services), so the draft is about this business.
The model must never invent a phone, address, hours, opening date or website, and the
response is constrained by a JSON schema.

Each finding then carries `suggestion` with `field`, `value`, `reason`, `confidence`,
`source`, `model` and `generated_at`, and its `explanation_source` becomes
`deterministic+generated`. The worker result carries `suggestions.status` as
`generated`, `skipped` (no key, disabled, or nothing to draft) or `failed` with the
error. Verdicts and scores are never affected by the suggestion pass.

Provider service (`suggestions/llm.py`): one interface, `generate_json(prompt, schema)`,
with two implementations chosen by `LLM_PROVIDER`:

| Provider | Auth | Endpoint | Settings |
| --- | --- | --- | --- |
| `vertex` (default) | Google application default credentials on the machine (`gcloud auth application-default login`), no API key | Vertex AI generateContent, global endpoint | `VERTEX_PROJECT`, `VERTEX_LOCATION` (global), `VERTEX_MODEL` |
| `gemini` | API key | Gemini Developer API, Interactions endpoint | `GEMINI_API_KEY`, `GEMINI_MODEL` |

Common: `SUGGESTIONS_ENABLED`, `SUGGESTIONS_TIMEOUT_SECONDS`. To add a provider,
implement `generate_json` and register it in `provider_from_settings`.

## Tests

- `backend/tests/test_profile_worker.py`: every check declared and assessed once, a
  complete profile scores 100, and one mutation per check flips its verdict or abstains.
- `backend/tests/test_profile_suggestions.py`: target selection, context and prompt
  content, attachment and validation of drafts, failure recorded without losing
  findings, skip conditions, and the HTTP client's error handling.

## Not built yet

Special hours, service area, services list, pending Google edits and Google-updated
fields: they need the Business Information API and are described in
`docs/engine/research/03-profile-worker-data-inventory.md`.
