# Locus documentation

**Locus is a Google Business Profile management platform.** An operator connects their Google
account, sees every profile they run, audits each one against 67 deterministic checks, reads
the evidence behind every finding, and fixes what is wrong — by hand, from an AI draft, or by
asking an agent to do it.

## Start here

| If you want to… | Read |
| --- | --- |
| **Run it** | [tech/running-locally.md](tech/running-locally.md) |
| Understand the system in one page | [architecture/overview.md](architecture/overview.md) |
| Understand the audit — the heart of the product | [features/audit-engine/overview.md](features/audit-engine/overview.md) |
| Understand **the one decision everything follows from** | [features/audit-engine/scoring.md](features/audit-engine/scoring.md) |
| Know what the take-home asked and how this answers it | [assignment/](assignment/README.md) |

## Architecture

| | |
| --- | --- |
| [overview.md](architecture/overview.md) | The whole system, the four subsystems, the principles |
| [data-model.md](architecture/data-model.md) | ~30 tables, their keys, and the conventions |
| [tenancy-and-auth.md](architecture/tenancy-and-auth.md) | Sign-in, tokens, organization scoping |
| [provenance.md](architecture/provenance.md) | `google` / `locus` / `fixture`, and why it matters |

## Features

One folder each. Every folder opens with `overview.md`.

**[Google Business Profile](features/google-business-profile/overview.md)** — the core
· [locations & the API](features/google-business-profile/overview.md)
· [editing a profile](features/google-business-profile/editing-a-profile.md)
· [hours, categories, attributes](features/google-business-profile/hours-categories-attributes.md)
· [connection, provider and sync](features/google-business-profile/connection-and-sync.md)

**[Audit engine](features/audit-engine/overview.md)** — the intelligence layer
· [architecture](features/audit-engine/architecture.md)
· [scoring](features/audit-engine/scoring.md)
· [suggestions](features/audit-engine/suggestions.md)
· [the six categories](features/audit-engine/categories/README.md)
· [research](features/audit-engine/research/README.md)

**[AI agent](features/ai-agent/overview.md)** — the conversational operator
· [architecture](features/ai-agent/architecture.md)
· [tools](features/ai-agent/tools.md)
· [streaming](features/ai-agent/streaming.md)
· [safety](features/ai-agent/safety.md)

**[Reviews](features/reviews/overview.md)** · [inbox and replies](features/reviews/inbox-and-replies.md)
**[Posts](features/posts/overview.md)**
**[Bookings](features/bookings/overview.md)**
**[Insights](features/insights/overview.md)** · [performance](features/insights/performance.md) · [search terms](features/insights/search-terms.md) · [photos](features/insights/media.md)
**[Local search](features/local-search/overview.md)** · [keywords and ranks](features/local-search/keywords-and-ranks.md) · [competitors](features/local-search/competitors.md)
**[Projects](features/projects/overview.md)**
**[Demo profiles](features/demo-profiles/overview.md)** · [archetypes](features/demo-profiles/archetypes.md) · [generator](features/demo-profiles/generator.md) · [API](features/demo-profiles/api.md)

## Frontend

[frontend/overview.md](frontend/overview.md) — stack, routes, the API client, hooks, the audit
card registry, and the known gaps.

## Tech

| | |
| --- | --- |
| [overview.md](tech/overview.md) | The stack, the four processes, what runs in the background |
| [running-locally.md](tech/running-locally.md) | From nothing to a working app, with a tour |
| [configuration.md](tech/configuration.md) | Every environment variable |
| [ai-setup.md](tech/ai-setup.md) | The two AI systems, with a worked example |
| [deployment.md](tech/deployment.md) | The VM, systemd, nginx, the checklist |

## The assignment

| | |
| --- | --- |
| [README.md](assignment/README.md) | The brief, and what was built against it |
| [data.md](assignment/data.md) | The dataset, and the nine traps in it |
| [how-we-answered-it.md](assignment/how-we-answered-it.md) | Requirement by requirement |
| [email.md](assignment/email.md) | The hand-back email |

---

## Four things that explain most of the codebase

**1. Missing data does not produce a low score.** A check without enough evidence is excluded
from the denominator — never counted as a failure, never as a pass. A sparse profile reports
low coverage and a `not_evaluated` grade. Every minimum-evidence gate in the engine exists to
serve this.

**2. Absent is not zero.** Every optional metric is nullable and a blank cell stays `NULL`.
"No calls were reported" and "no calls happened" are different facts.

**3. A write goes through one function.** The agent calls the same `apply_edit` the profile
editor calls. One implementation per behaviour, so the audit trail cannot be bypassed.

**4. Nothing talks to Google.** The Cloud project was never approved for Business Profile API
access. The live client was removed rather than kept as code that cannot run; one provider
reads the assignment's CSVs. `get_provider()` is the single seam.

## Conventions in these documents

- Everything here was verified against the code, not against intention. Where a document and
  the code disagreed, the code won and the document was corrected.
- **Known gaps are written down**, not omitted. Several pages end with a list of real,
  verified discrepancies — mostly frontend types that are stricter than the API, or keys that
  do not line up. They are there so nobody rediscovers them.
- Where something was deliberately **not** built, the reason is given.
