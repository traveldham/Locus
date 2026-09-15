# AI setup, with a worked example

Two independent AI systems. Both use Gemini; they do very different jobs.

| | Suggestion layer | Agent |
| --- | --- | --- |
| Where | Inside each audit worker | Its own Celery turn |
| Job | Draft the text for a finding | Hold a conversation and act |
| Tools | none — one prompt, one JSON schema | eleven, calling the product's own functions |
| Providers | `vertex` **or** `gemini` | **`vertex` only** |
| Failure | Recorded as `skipped` / `failed`; the audit is unaffected | The turn fails, carrying the reason |

The agent is Vertex-only because tool-calling needs a chat-model binding, and supporting a
second one doubled the surface without adding capability.

## Configuring it

**Vertex (default, no API key).** Authenticates with Google application default credentials:

```bash
gcloud auth application-default login     # or attach a service account to the VM
```

```
LLM_PROVIDER=vertex
VERTEX_PROJECT=your-gcp-project
VERTEX_LOCATION=global
VERTEX_MODEL=gemini-3.8-flash
SUGGESTIONS_ENABLED=true
```

**Gemini Developer API (suggestions only).**

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.8-flash
```

Turning it off entirely is `SUGGESTIONS_ENABLED=false`. The audit is unchanged — every check
still runs and every finding is still produced; only the drafted text is absent.

## What the AI is allowed to decide

This is the line the whole design rests on:

> **The deterministic engine decides what is wrong. The model only ever drafts the words.**

- Verdicts, scores, severities and evidence are computed in code. The suggestion pass runs
  *after* they are fixed and cannot change them.
- Facts only the business knows — phone, address, hours, opening date, website — are **never**
  drafted. The schemas do not offer those fields.
- A draft is validated **in code**, not by the prompt. A reply containing a URL, an email, a
  phone number, a greeting-plus-name, an honorific or a promotion is **dropped**, not
  published.
- Nothing is published automatically. A person reviews every draft.
- The agent may act, but only through the product's own functions, only on one location, and
  every write lands in the audit trail with the user's name on it.

## Worked example: an unanswered review

**What the engine found**, deterministically, before any model was involved:

```
rule      critical_review_unanswered
subject   AbCdEf-review-0042            (Google's review id)
severity  critical    score 78    confidence high
title     1-star review from 34 days ago has no reply
why       A 1-star review posted 34 days ago has no owner reply: "Waited fifty
          minutes for a table we had booked, then another half hour for drinks.
          Nobody apologised." Customers reading it see silence.
evidence  source     reviews
          row_ids    ["3f2a…"]
          fields     ["star_rating", "create_time", "reply_comment"]
          calculation  star_rating <= 3, create_time older than reply_wait_days,
                       reply_comment blank
          values     {"rating": 1, "days_waiting": 34, "review": "AbCdEf-review-0042"}
limitation  A reply drafted here must be reviewed by a person before it is posted.
```

**What the model was given:** the business name, category and city; the projects it belongs to
with their services; the unanswered low reviews (id, rating, date, comment up to 400
characters); and the forty most recent reviews with text. **No reviewer names** — they are
stripped from the snapshot before it is written.

**What it returned**, constrained by a JSON schema:

```json
{"suggestions": [{
  "subject": "AbCdEf-review-0042",
  "field": "review_reply",
  "value": "Thank you for telling us about this - a fifty-minute wait on a booked
            table is not the standard we hold ourselves to, and the delay at the
            bar made it worse. We have changed how we hold reservations on busy
            evenings. Please ask for the duty manager on your next visit so we can
            put it right.",
  "reason": "Acknowledges the specific delay and offers to resolve it offline."
}]}
```

**What the code then checked** before attaching it: under 350 characters; no URL, email or
phone number; no greeting followed by a name; no honorific; no promotion or discount; not a
duplicate for this finding; the field matches the rule that asked for it; the subject names
exactly one review of *this* location. A draft failing any of these is dropped, and the
finding simply carries no suggestion.

**What the operator sees:** the finding, the evidence, and the draft in an editable box with a
Send button. Pressing it calls `PUT /api/v1/reviews/{id}/reply` — the same endpoint the review
inbox uses — which writes a `ProfileAction`, calls the provider, and only then mirrors the
reply locally.

## Worked example: the agent doing it

```
You    reply to the reviews nobody has answered

       ⟳ Checking reviews                    list_reviews(unreplied_only=true, limit=20)
       ⟳ Reading the audit                   get_latest_audit
       ⟳ Reading drafted suggestions         list_audit_suggestions
       ⟳ Replying to a review                reply_to_review(review_id=…, comment=…)
       ⟳ Replying to a review                reply_to_review(review_id=…, comment=…)

Agent  I replied to the three unanswered 1-star reviews using the drafts from the
       latest audit - the fifty-minute wait, the cold steak, and the double charge.
       Two more low reviews are under three days old, so I left those; the audit
       excludes them from the reply rate until then.
```

Every one of those writes is a `ProfileAction` row with the signed-in user's name on it, and
each is visible in the profile's change history.

## What the AI cannot do

- It cannot change a score, a verdict or a severity.
- It cannot invent a phone number, address, opening hours or website.
- It cannot clear a profile field — `update_location_profile` can set, never blank. Three
  shapes (`None`, `""`, `[]`) are all treated as "not supplied".
- It cannot touch a second location. Every tool closes over the conversation's location, and
  the two tools given a row instead resolve and check that row's location first.
- It cannot publish anything a person has not seen, in the suggestion path.

## If it is not configured

Nothing breaks. `enrich` never raises: each worker result records
`{"status": "skipped", "reason": "..."}` — the reason distinguishing "no suggestion layer for
this worker", "suggestions are disabled" and "no credentials". Every category still gets a
deterministic `fallback_summary`, so no card is blank. The agent returns a failed turn naming
the exact setting to fix.

## In tests

No test reaches a model. An autouse fixture forces a `Settings` with `llm_provider="gemini"`
and no API key, so every worker reports `skipped`; the agent suites drive the real LangGraph
loop against a `StubChatModel` returning a scripted sequence, with real tools and no network.
