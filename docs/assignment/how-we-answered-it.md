# How the build answers the brief

Requirement by requirement, with where each lives.

---

## 1. "Take a location and return its recommendations"

`POST /api/v1/recommendations/runs` with a `location_id` and an optional `as_of`. One audit is
about **one** Google Business Profile — the same unit the brief asks about.

```
POST /recommendations/runs        →  202, the job with its six workers
GET  /recommendations/jobs/{id}   →  progress, per worker
GET  /recommendations/latest?location_id=  →  the current run
```

In-process, with no broker: `run_job(job_id, session_factory)`.

→ [features/audit-engine/overview.md](../features/audit-engine/overview.md)

## 2. "Run across all 12 locations"

`GET /api/v1/recommendations/overview` is the directory: every profile with its score, grade,
issue count and active job. Creating a project, or adding locations to one, **queues an audit
for each profile automatically**, so a profile never sits in a workspace unaudited.

## 3. "Every recommendation must carry its own justification"

This is the requirement the whole design is built around. Every finding carries:

| Field | What it answers |
| --- | --- |
| `title` | What was found |
| `why` | Why it matters, with the actual numbers |
| `action` | What to do about it |
| `score` + `severity` | How much it matters |
| `confidence` + `confidence_reason` | How strongly the evidence supports it |
| `limitation` | What this finding **cannot** tell you |
| `evidence[]` | `source` table, `row_ids`, `fields`, `calculation`, `values` |

A worked example, from an unanswered review:

```
evidence  source       reviews
          row_ids      ["3f2a…"]
          fields       ["star_rating", "create_time", "reply_comment"]
          calculation  star_rating <= 3, create_time older than reply_wait_days,
                       reply_comment blank
          values       {"rating": 1, "days_waiting": 34}
```

`GET /recommendations/runs/{id}/evidence` returns the **actual rows** behind any finding, and
the UI has an evidence panel on every issue. A recommendation a clinic manager cannot trace
back to something in the dataset is not finished — so none of them are un-traceable.

## 4. "Distinguish what matters a lot from what matters a little"

Four mechanisms, and they compose:

1. **Category weights** — visibility 25, profile 20, reputation 20, operations 15,
   performance 10, content 10. Policy, asserted to sum to 100.
2. **Per-check weights** inside each category.
3. **Severity graded from magnitude, not fixed per rule.** A 3.9 rating and a 1.8 rating both
   trigger `rating_low`; only the second is critical. `graded(base, magnitude, span, cap)`
   scales the score by how far past the threshold the finding sits.
4. **Share of subjects failed.** A check that enumerates — one finding per keyword, per
   review, per weekday — is scored on the *share* that failed, never the raw count, so a
   clinic tracking forty keywords is not punished for tracking them.

And `priorities` names the few findings to do first: worst severity, drafts and quick fixes
ahead of the rest, and no category taking more than two of five slots while another still has
something to say.

→ [features/audit-engine/scoring.md](../features/audit-engine/scoring.md)

## 5. "Be deliberate about what an LLM decides and what your own code decides"

The line is absolute:

> **The deterministic engine decides what is wrong. The model only ever drafts the words.**

- Verdicts, scores, severities and evidence are computed in code, with no model involved. The
  suggestion pass runs *after* they are fixed and cannot change them.
- Facts only the business knows — phone, address, hours, opening date, website — are never
  drafted.
- Every draft is validated **in code**, not by the prompt: length caps, and a draft carrying a
  URL, an email, a phone number, a greeting-plus-name, an honorific or a promotion is
  **dropped**, not published.
- Nothing is published automatically.
- `enrich` never raises — a model that is slow, absent or wrong records `skipped` or `failed`
  and the audit is unaffected.

The original prototype used **no LLM at all**, and said why: "a complete deterministic
explanation is more defensible than unvalidated interpretation". That reasoning still holds —
which is why the model was added *around* the engine rather than inside it.

→ [features/audit-engine/suggestions.md](../features/audit-engine/suggestions.md) ·
[tech/ai-setup.md](../tech/ai-setup.md)

## 6. "Code a teammate could pick up and extend"

Adding a check is a local change:

1. Add an entry to that worker's `CHECKS` dict — weight, label, what it checks, the fix, the
   wording, its group and effort.
2. Add one `c.assess(...)` and one `c.emit(...)` in `evaluate`.
3. Put any threshold on `EngineConfig`, which has `extra="forbid"` so it cannot hide in a rule
   body.
4. Bump `ENGINE_VERSION`.

Nothing else changes. Policy reads `CHECKS`; the API serves it at
`GET /recommendations/policy`, so the frontend never hardcodes a weight or a band. A worker
never reads another worker's result, so the six are genuinely independent.

Adding a **whole category** is a new module under `categories/` and one card component
registered by key.

→ [features/audit-engine/architecture.md](../features/audit-engine/architecture.md)

## 7. "Real output, the code, and a write-up"

- **Output**: every audit is stored as a `RecommendationRun` with its full report and the
  snapshot it was computed from, and served over the API and the UI.
- **Code**: this repository, with its commit history.
- **Write-up**: `locus-intelligence-assignment/NOTES.md` — and this documentation tree, which
  is the version that matches the code as it now stands.

---

## Against the grading questions

**"Did you understand the data before building on it?"** → [data.md](data.md) lists nine traps
in the export and what the engine does about each. The abstention machinery exists *because*
of them.

**"Are the recommendations specific and actionable, or generic advice?"** → Every finding
names the subject. Not "improve your reviews" but *"a 1-star review posted 34 days ago has no
owner reply: 'Waited fifty minutes for a table we had booked'"*. Enumerating checks emit one
finding per keyword, per review, per weekday — because a manager investigating lost visibility
needs the list, not a representative.

**"Can you show the evidence for any given recommendation?"** → Yes, down to the row ids, over
the API.

**"Does the system distinguish what matters?"** → Four mechanisms above, plus a `priorities`
list.

**"Is the code something a teammate could extend?"** → Six independent workers, declarative
checks, one config object, 364 tests.

**"Does the write-up show judgement about its own limits?"** → Every finding carries a
`limitation` sentence. Every report carries three. Every category doc has a "not built" section
naming what the data cannot support and why.

---

## What was deliberately not built

Stated plainly, because the brief asks for it:

- **No predicted uplift.** The score ranks work. It is not a forecast of bookings or revenue,
  and nothing claims raising it will raise either.
- **No learned ranking.** The data has no outcome column, so there is nothing to learn from
  and nothing to validate against. Weights are declared policy, versioned.
- **No automatic public writes.** Every draft is reviewed by a person.
- **No cross-location causal claims.** A rival ahead with more reviews is a description, not a
  mechanism.
- **No acquisition funnel.** The datasets cover different periods and cannot be joined into
  one reliably.
- **No review-text sentiment as a deterministic check.** The model extracts themes, capped at
  medium confidence, and that is as far as it goes.

## What is beyond the brief

The brief asked for an intelligence layer. What is here is a platform around one:

- **Profile management** — read, preview, edit and apply changes with a real Google update
  mask, a consent step and a `profile_actions` audit trail.
- **A conversational agent** that can read the audit and *act on it* — replying to reviews and
  editing profiles through the product's own functions, scoped to one location, every write
  audited.
- **Review, post, booking, insights and local-search screens.**
- **A demo-profile generator** — ten deliberately poor-quality businesses across ten
  industries, generated deterministically, because the twelve dental clinics are healthy and
  demonstrate the engine badly.

## The honest caveat

**Nothing talks to Google.** The Cloud project was never approved for Business Profile API
access — every live call returned `429 RESOURCE_EXHAUSTED` with `quota_limit_value: 0`. The
live implementation was removed rather than kept as code that cannot run, and one provider
reading the assignment's CSVs sits behind the abstraction. The read path, the edit path, the
update mask, the validation, the audit trail and the agent are all real;
`get_provider()` is the one function that changes when quota is granted.
