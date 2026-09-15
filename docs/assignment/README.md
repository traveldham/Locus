# The assignment

The take-home this repository grew out of, what was asked, and what was built.

The original brief, data dictionary and write-up are unmodified in
`locus-intelligence-assignment/` — `README.md`, `DATA.md`, `NOTES.md` and `data/`.

## What was asked

> Build a working prototype of an **intelligence layer** on top of this data: a system that
> looks at a location and produces specific, defensible recommendations for how that location
> could perform better.

The context: Locus works with multi-location businesses — 5 to 500 physical locations, each
with its own Google Business Profile, reviews, local ranking and customers. The owner cannot
look at 500 dashboards. They want to know one thing: **what should we do next, and where?**

The dataset is a synthetic export for **Brightpath Dental**, twelve clinics across Texas and
Arizona, covering roughly a year of reviews and a rolling quarter of performance, ranking,
booking and profile data. Nothing is labelled — no answer key, no score, no flag. *Reading the
data is part of the task.*

### The explicit requirements

| # | Requirement |
| --- | --- |
| 1 | Take a location and return its recommendations |
| 2 | Run across all 12 locations |
| 3 | **Every recommendation carries its own justification** — why this location, why this action, which data it rests on |
| 4 | Distinguish what matters a lot from what matters a little |
| 5 | Be deliberate about what an LLM decides and what your own code decides |
| 6 | Code a teammate could pick up and extend |
| 7 | Hand back real output, the code, and a write-up of at most two pages |

And the stated grading questions: did you understand the data before building on it; are the
recommendations specific and actionable rather than generic advice true of any business; can
you show the evidence for any given recommendation; does the system distinguish severity; is
the code extensible; does the write-up show judgement about its own limits.

> Scope honestly. A small system that works, whose limits you understand and state, beats a
> large one that mostly asserts things.

## What was built

The prototype answered the brief with a deterministic ten-check engine and a CLI. That version
is what `locus-intelligence-assignment/NOTES.md` describes.

What is in this repository now is **a Google Business Profile management platform** — the
audit is one feature of it, rebuilt to version 4.0.0:

| Then | Now |
| --- | --- |
| 10 checks, one module | **67 checks** across **six independent workers** |
| One pass, in-process | A **pipeline**: snapshot → six workers → assemble → score → publish |
| CLI output | A full web UI, plus a REST API |
| No LLM, by choice | A **suggestion layer** drafting the fix, and a **conversational agent** that can apply it |
| Read-only | Real profile **edits** with preview, consent and an audit trail |
| 12 dental clinics | Plus **ten generated businesses** across ten industries for demonstrating the engine |

The core judgement did not change, and that matters more than the feature count: the engine is
still deterministic, every finding still carries its evidence, and **checks without enough
evidence are still excluded from the score rather than counted as passes**.

## Documents here

| | |
| --- | --- |
| [data.md](data.md) | The dataset: every file, every column, and the traps in it |
| [how-we-answered-it.md](how-we-answered-it.md) | Requirement by requirement, what was built and where it lives |
| [email.md](email.md) | The hand-back email |

## One thing to read first

If you read a single page of this documentation, read
[features/audit-engine/scoring.md](../features/audit-engine/scoring.md). It contains the one
decision everything else follows from: a check that cannot find enough evidence is **excluded
from the denominator**, so a location with thin data scores nothing rather than a flattering
pass.
