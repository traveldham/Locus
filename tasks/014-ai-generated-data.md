# 014 — AI-generated Business Profile data

**Status:** ❌ CANCELLED — never built. Superseded by [015](015-sample-data-provider.md).

> Planned, then dropped before any code was written. The owner chose a fixed sample
> dataset over live AI generation: simpler, free, instant, and stable across refreshes.
>
> The Vertex findings below are still accurate and worth keeping if generation is ever
> revisited — in particular that **Gemini 3.x is not available on this project** and the
> Vertex endpoint must be regional, not global.

---

*Original plan below, for reference.*

## The idea

Google will not return business data until the project is approved (`quota: 0`, proven). So instead of fetching from Google, **generate the same data with Gemini** and store it through the same pipeline.

The application cannot tell the difference, because the shapes are identical:

```
user connects Google
        ↓
   Celery task
        ↓
Vertex AI · gemini-2.5-flash-lite
        ↓
structured JSON in the real Google shape
        ↓
   same tables
        ↓
   same screens
```

When Google approves, the generator is swapped for `live.py`. Nothing downstream changes.

## Verified before planning

| Check | Result |
|---|---|
| `aiplatform.googleapis.com` enabled on `traveldham-d253e` | ✅ |
| `gemini-2.5-flash-lite` callable | ✅ HTTP 200 |
| `gemini-2.5-flash` callable | ✅ HTTP 200 |
| `gemini-3-*` (any variant) | ❌ 404 — not available |

**"Gemini 3.1 Lite" does not exist on this project.** `gemini-2.5-flash-lite` is the working equivalent: fastest and cheapest of the available models.

Endpoint shape (regional, not global — the global host 404s):
```
https://us-central1-aiplatform.googleapis.com/v1/projects/{project}
  /locations/us-central1/publishers/google/models/gemini-2.5-flash-lite:generateContent
```

## Non-negotiable: generated data must be labelled

The owner was angry when sample clinics appeared under their real Google account — correctly so.

AI-generated data is **the same risk, amplified**, because it is convincing. A business seeing invented locations and invented customer reviews about itself, unlabelled, is worse than obviously-fake data.

So:
- `Location.source` gets a `generated` value alongside `google` and `manual`
- Every screen showing generated data carries a visible **Demo data** badge
- A dismissible banner explains this is sample data until Google approves access

This is what makes the approach honest rather than deceptive.

## What gets generated

Everything Google would return after a connect:

| Data | Notes |
|---|---|
| Account | one, named from the connected email's domain |
| Locations | real Google shape — `periods[]` hours, typed attributes, categories |
| Reviews + replies | varied text, realistic rating spread, some unanswered |
| Performance daily | the nine real metric names |
| Search keywords | with the `value` vs `threshold` distinction |
| Posts | standard / event / offer |
| Media counts | derived, as Google's would be |
| Competitors | acknowledged as not-from-Google; generated for completeness |

## Rules for the generator

1. **Structured output only.** Use Vertex `responseSchema` + `responseMimeType: application/json`. Never parse free text — a malformed response must fail loudly, not half-populate the database.
2. **Generate once, store, reuse.** Not per page load, not per sync. Regenerating on every fetch would make a location change its name between refreshes, and would cost money for nothing.
3. **Real Google shape, not the CSV shape.** Hours as periods with `open_day`/`close_day` (multi-shift, overnight). Attributes typed. Ratings 1–5 mapped from Google's enum convention.
4. **Deterministic seed per organization**, so a regenerate produces a coherent set rather than an unrelated business.
5. **Never bypass the provider seam.** The generator is a `GbpProvider` implementation like any other.

## Celery

Chosen by the owner. Justified here in a way it was not for Google fetching: **LLM calls genuinely are slow** — generating a full business takes tens of seconds, which cannot sit inside an HTTP request.

- Broker: Redis (`brew install redis`)
- **Must degrade gracefully.** If no broker is configured, fall back to eager/inline execution so the app still works — the same lesson as the deleted sync engine: never make a queue a hard prerequisite.
- Tasks: `generate_business`, `generate_reviews`, `generate_performance`
- Progress tracked in the existing `SyncRun` table — that is exactly what it was kept for.

## Cost

`gemini-2.5-flash-lite` is the cheapest available model. A full business — roughly 10 locations plus reviews — is a few thousand tokens, so a fraction of a cent. Generating once rather than per request keeps it negligible.

## Build order

| Step | Work |
|---|---|
| 1 | Vertex client with structured output + auth via ADC |
| 2 | `generated.py` provider — accounts and locations |
| 3 | Generated reviews |
| 4 | Celery app, broker config, eager fallback, `SyncRun` progress |
| 5 | `source = generated` + the Demo data badge and banner in the UI |
| 6 | Generated performance, search terms, posts, media |

## The seam that makes this safe

All of it sits behind `get_provider()`. Three implementations — `live`, `generated`, and a test stub — one selector. Approval flips a setting; no other code moves.

That seam is also what let the sync engine be deleted in a single task. Worth preserving.
