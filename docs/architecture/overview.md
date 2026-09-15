# System overview

Locus is a **Google Business Profile management platform**. An operator connects their Google
account, sees every profile they run, audits each one against 67 deterministic checks, reads
the evidence behind every finding, and fixes what is wrong — by hand, from an AI draft, or by
asking an agent to do it.

## The shape of it

```
┌─ frontend ────────────────────────────────────────────────────────┐
│  Next.js 16 App Router · TanStack Query · Tailwind v4             │
│  Profiles · Reviews · Posts · Bookings · Insights · Market        │
│  Profile audit  ·  floating AI agent widget on every page         │
└───────────────────────────┬───────────────────────────────────────┘
                            │  REST + one SSE stream, bearer JWT
┌───────────────────────────▼───────────────────────────────────────┐
│  FastAPI  /api/v1                                                 │
│   auth  integrations  projects  locations  reviews  posts         │
│   bookings  insights  market  recommendations  agent              │
│   demo-profiles                                                   │
└───────┬───────────────────────────────┬───────────────────────────┘
        │                               │
┌───────▼─────────┐            ┌────────▼────────┐
│  PostgreSQL     │            │  Celery + Redis │
│  ~30 tables     │            │  audit pipeline │
│                 │            │  agent turns    │
└───────┬─────────┘            └────────┬────────┘
        │                               │
┌───────▼──────────────────┐   ┌────────▼────────────────────────┐
│ GbpProvider (one impl)   │   │ Vertex AI — Gemini              │
│ SampleGbpProvider → CSVs │   │ audit suggestions · agent loop  │
└──────────────────────────┘   └─────────────────────────────────┘
```

## The four subsystems

**1. Profile management.** Mirror a profile, show it as a customer sees it, edit it with a
preview and a consent step, and record every write in `profile_actions`.
→ [features/google-business-profile](../features/google-business-profile/overview.md)

**2. The audit engine.** One pipeline, six independent workers, 67 checks, a weighted health
score, and evidence for every finding.
→ [features/audit-engine](../features/audit-engine/overview.md)

**3. AI.** Two separate systems with different jobs:
- the **suggestion layer** drafts text for a finding (a reply, a description, a shot list)
- the **agent** holds a conversation and calls the product's own functions as tools
→ [features/audit-engine/suggestions.md](../features/audit-engine/suggestions.md) ·
[features/ai-agent](../features/ai-agent/overview.md)

**4. The data surfaces.** Reviews, posts, bookings, insights and local search — each a screen,
and each also an input to the audit.

## Principles you will see everywhere

**Absent is not zero.** Every optional metric is nullable and a blank cell stays `NULL`. "No
calls were reported" and "no calls happened" are different facts. The audit abstains rather
than inventing a zero, and charts draw a gap.

**Provenance is written, not inferred.** Every analytics row carries `source`, so the UI can
say where a number came from instead of letting a user assume Google supplied it.
→ [provenance.md](provenance.md)

**Cross-tenant is a 404, not a 403.** Every scoped query filters on `organization_id` in the
same statement that fetches the row, so "not yours" and "not there" are indistinguishable from
outside.

**A write goes through one function.** The agent calls the same `apply_edit` the profile
editor calls. There is one implementation of each behaviour, so the audit trail cannot be
bypassed and the agent cannot drift from the product.

**Thresholds live in one place.** `EngineConfig` has `extra="forbid"`, so a magic number
cannot hide in a rule body.

**Background work is a row, not a request.** An audit and an agent turn each own a database
row with status, progress and error, so a finished job stays findable after the broker has
forgotten the task.

## The honest limitation

**Nothing talks to Google.** The Cloud project was never approved for Business Profile API
access — every live call returned `429 RESOURCE_EXHAUSTED` with `quota_limit_value: 0`. The
live implementation was **removed** rather than kept as code that cannot run, and one
`SampleGbpProvider` reading the assignment's CSVs sits behind the abstraction.

The read path, the edit path, the update mask, the validation, the audit trail and the agent
are all real. `get_provider()` is the one function that changes when quota is granted.

## Related

- [data-model.md](data-model.md) — every table and why it exists
- [tenancy-and-auth.md](tenancy-and-auth.md) — sign-in, sessions, org scoping
- [provenance.md](provenance.md) — google / locus / fixture
- [../tech/running-locally.md](../tech/running-locally.md) — run the whole thing
