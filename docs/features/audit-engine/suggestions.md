# Suggestions — the AI draft layer

Code: `backend/app/services/recommendations/suggestions/`.

After a worker's deterministic checks have run, the pipeline asks a language model to draft
the text a person would otherwise have to write: a reply to an unanswered review, a
rewritten business description, a shot list for missing photos, two Google posts, a
follow-up message to a customer whose request was never answered.

## The contract

**A suggestion is never a fact.** The deterministic verdict stands entirely on its own, and
a person reviews the draft before anything is published. Concretely:

- **Verdicts and scores are never affected by the suggestion pass.** `enrich` runs after
  scoring inputs are already fixed, and it only ever attaches to findings.
- **Facts only the business knows are never drafted** — phone number, address, opening
  hours, opening date, website. The model is told this, and the schemas do not offer those
  fields.
- **`enrich` never raises.** The outcome is recorded on the worker result as
  `generated`, `skipped` or `failed`, and the findings survive either way. An audit never
  fails because a model was slow, absent or wrong.

## How it runs

`enrich(category, snapshot, result, settings)` is the single entry point, called by
`run_category` in `backend/app/tasks/audit.py` immediately after `run_worker`, while the
worker row shows the stage "Drafting suggestions".

```
run_worker  →  deterministic findings + verdicts
                     │
enrich       →  targets()          which findings want a draft
                business_context() the business, its projects, the relevant card data
                build_prompt()     one prompt, one call
                generate_json()    the provider, constrained by RESPONSE_SCHEMA
                apply()            validate in code, attach to the matching finding
```

One optional module per worker, discovered by name: `suggestions/<category>.py`. A worker
without one simply has no module and reports `skipped`. Each module exposes `targets`,
`wants`, `business_context`, `build_prompt`, `apply`, `fallback_summary` and
`RESPONSE_SCHEMA`.

## What gets drafted

A check opts in by declaring a `suggests` field in its `CHECKS` entry. The field name is
what the model must fill, and `apply` drops anything attached to the wrong field.

| Category | Checks | Field | Shape |
| --- | --- | --- | --- |
| profile | `description_missing`, `description_short`, `description_too_long`, `description_keyword_stuffed`, `description_quality` | `description` | text, ≤750 chars, no links or promotions |
| profile | `secondary_categories_few`, `services_without_category` | `additional_categories` | list of Google category names |
| profile | `attributes_sparse`, `accessibility_unanswered`, `category_attribute_mismatch`, `services_without_attribute` | `attributes` | map of catalog attribute name → yes/no |
| profile | `name_keyword_stuffed` | `title` | the real-world business name |
| reputation | `critical_review_unanswered` (10 newest at most) | `review_reply` | ≤350 chars, one per review |
| reputation | `rating_low`, `one_star_share_high`, `rating_trend_falling` | `themes` | ≤8 short phrases naming recurring complaints and praise |
| visibility | `near_pack_opportunity`, `high_intent_lagging` | `keyword_plan` | map of keyword → one sentence naming the profile change |
| visibility | `search_term_losing` | `term_action` | one sentence naming the profile change |
| operations | `requests_unanswered` (10 oldest at most) | `followup_message` | ≤300 chars, names the service, asks the customer to confirm |
| operations | `no_show_rate_high` | `reminder_plan` | 3-5 concrete steps |
| operations | `weekend_demand_without_hours` | `hours_note` | ≤400 chars for the manager |
| performance | every decline and shift check, `zero_action_days` | `investigation_plan` | 3-5 checks, ≤160 chars each, ordered by likelihood |
| content | `posts_none_recent`, `posts_sparse`, `post_types_uniform`, `posts_without_cta` | `post_drafts` | exactly two posts — one update, one offer or event — ≤300 chars each, ending with the button |
| content | `photos_few`, `photos_below_target`, `photo_type_empty` | `photo_shot_list` | 5-8 specific shots, ≤120 chars each, matched to the empty type |

## Validation happens in code, not in the prompt

The prompt asks; the code enforces. A draft that breaks a rule is dropped rather than
attached half-finished, and a draft *set* that loses a member to the rules is dropped
whole. Enforced across the layers:

- no URLs, e-mail addresses or phone numbers
- no greeting followed by a customer's name, no honorifics
- no promotional language in a review reply, no price
- no word of four or more letters in ALL CAPS (content)
- no promise words — calls, customers, rankings, revenue (performance)
- length caps, list-length bounds, exactly two post drafts, 5-8 distinct shots
- one suggestion per finding, and the field must match the rule that asked for it
- a plan is kept only for the keyword the finding names

Customer identity never reaches the model: `customer_name`, `reviewer_display_name` and
`reviewer_photo_url` are stripped from the snapshot before it is written
(`contracts.EXCLUDED`), so booking findings identify a request by `external_booking_id` and
review findings by the Google review id.

## What a finding carries afterwards

```json
"suggestion": {
  "field": "review_reply",
  "value": "Thank you for telling us …",
  "reason": "…",
  "confidence": "high | medium | low",
  "source": "vertex",
  "model": "gemini-3.8-flash",
  "generated_at": "2026-09-14T…"
}
```

and the finding's `explanation_source` becomes `deterministic+generated`. Everything not
carrying a suggestion stays `deterministic`.

## Summaries

Each module also provides `fallback_summary(result)` — a deterministic paragraph, ordered
by severity, used when no model answered. It is always computed, so a category card is
never blank. `suggestions/overall.py` produces the one-paragraph summary across all six
workers that the Overview screen shows.

## Providers

`suggestions/llm.py` is the only place the audit talks to a model. One interface,
`generate_json(prompt, schema) -> dict`, two implementations chosen by `LLM_PROVIDER`:

| Provider | Auth | Endpoint | Settings |
| --- | --- | --- | --- |
| `vertex` (default) | Google application default credentials on the machine (`gcloud auth application-default login`) — no API key | Vertex AI `generateContent`, global endpoint | `VERTEX_PROJECT`, `VERTEX_LOCATION` (default `global`), `VERTEX_MODEL` |
| `gemini` | API key | Gemini Developer API | `GEMINI_API_KEY`, `GEMINI_MODEL` |

Common settings: `SUGGESTIONS_ENABLED` (default true), `SUGGESTIONS_TIMEOUT_SECONDS`.
Default model for both: `gemini-3.8-flash`.

Everything that goes wrong becomes a `SuggestionError`, which the caller records and moves
past. To add a provider, implement `generate_json` and register it in
`provider_from_settings`.

## Status reporting

Every worker result carries `suggestions`:

```json
{"status": "generated", "provider": "vertex", "model": "gemini-3.8-flash",
 "requested": 7, "attached": 7}
{"status": "skipped",  "reason": "Suggestions are disabled."}
{"status": "failed",   "error": "Vertex returned 429: …"}
```

`skipped` covers three different things — no suggestion layer for that worker, suggestions
disabled by settings, or no credentials configured — and the `reason` says which.

## In tests

No test in the suite calls a real model. The `no_llm` autouse fixture in
`tests/conftest.py` forces a `Settings` with `llm_provider="gemini"` and no API key, so
every worker reports `skipped` and the deterministic path is what is asserted. Each
category has its own `test_<category>_suggestions.py` covering target selection, prompt
contents, attachment, and every validation rule, against a stub provider.

## Related

- [overview.md](overview.md) · [scoring.md](scoring.md) · [categories/](categories/)
- [../ai-agent/overview.md](../ai-agent/overview.md) — the conversational agent is a separate system with its own tools; this layer only drafts text for findings.
