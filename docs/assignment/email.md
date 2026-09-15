# Hand-back email

A ready-to-send reply. Adjust the greeting, the link and the sign-off; the body is accurate as
written.

---

**Subject:** Locus take-home — Brightpath Dental intelligence layer

---

Hi [name],

Thanks for the take-home — I enjoyed it, and it ran away with me a little. The repository is
here: **[link]**

## What it does

Point it at one Google Business Profile and it returns a health score, every issue behind that
score, and the stored rows each issue rests on. It runs across all twelve Brightpath clinics,
and creating a project queues an audit for each profile automatically.

It is an audit, not a forecast. It ranks work; it does not predict revenue.

## How it decides what to recommend

Six independent workers, one per category — profile completeness, reputation, local
visibility, operations, performance, content — running **67 deterministic checks** over a
repeatable-read snapshot of one profile's rows. Category weights are declared policy
(visibility 25, profile and reputation 20 each, operations 15, performance and content 10) and
sum to 100.

Every check ends in one of four verdicts: triggered, clear, insufficient_data or suppressed.

**The decision I would most want you to look at** is what happens to the third one. A check
that cannot find enough evidence is *excluded from the denominator* — never counted as a
failure, never as a pass. So a location with thin data reports low coverage and a
`not_evaluated` grade rather than a flattering score. Everything else follows from that:
minimum-evidence gates on every rate, weekday-paired performance windows that drop unpaired
days, rankings that need four consecutive fresh checks, and "not found" treated as a state
rather than rank zero.

Severity is graded from magnitude rather than fixed per rule, and a check that enumerates —
one finding per keyword, per review, per weekday — is scored on the *share* of subjects that
failed, so a clinic tracking forty keywords is not punished for tracking them.

## Evidence

Every finding carries its own justification: what was found, why it matters with the actual
numbers, what to do, how confident and **why**, what the finding cannot tell you, and the
evidence — source table, row ids, fields, the calculation and the values.

`GET /recommendations/runs/{id}/evidence` returns the real rows behind any finding, and the UI
has an evidence panel on every issue.

## Where I used a model, and where I did not

The engine is entirely deterministic. No model decides a verdict, a score or a severity.

After the checks run, a separate layer asks Gemini to draft the *text* of a fix — a reply to
an unanswered review, a rewritten description, two posts, a photo shot list. Those drafts are
validated in code, not by the prompt: length caps, and anything carrying a URL, an email, a
phone number, a greeting-plus-name or a promotion is dropped rather than published. Nothing is
published without a person. If the model is unreachable the audit is unaffected and the finding
simply carries no draft.

My first version used no LLM at all, on the grounds that a complete deterministic explanation
is more defensible than unvalidated interpretation. I still think that is right, which is why
the model sits *around* the engine rather than inside it.

## What I would not trust

- The score as evidence that raising it raises bookings. It orders work, nothing more.
- Any cross-dataset funnel — the windows do not line up and Google truncates the long tail.
- Competitor figures as anything but context. They are scraped observations compared with our
  stored counts, which are not measured the same way, and every such finding says so.
- `new` booking statuses, which may simply be stale CRM state.

The export has a discrepancy worth flagging: `DATA.md` states 93 posts, the shipped file has
69. The engine handles thin post data as an observation at medium confidence, with the
limitation that an incomplete export looks identical to never posting.

## What I went on to build

More than the brief asked for, and I should be upfront about that. Around the audit there is
now a Google Business Profile management platform: profile editing with a real Google update
mask, a preview-and-consent step and an audit trail on every write; review, post, booking,
insights and local-search screens; and a conversational agent that can read an audit and act
on it — replying to reviews and editing profiles through the product's *own* functions, scoped
to a single location, with every write recorded the same way a person's would be.

I also wrote a generator for ten deliberately poor-quality businesses across ten industries,
because the twelve Brightpath clinics are mostly healthy and demonstrate the engine badly.

## One thing to be clear about

**Nothing talks to Google.** The Cloud project was never approved for Business Profile API
access — every live call came back `429 RESOURCE_EXHAUSTED` with `quota_limit_value: 0`. I
removed the live client rather than leave code that cannot run, and there is one provider
behind the abstraction that reads your CSVs. The read path, the edit path, the update mask,
the validation, the audit trail and the agent are all real; `get_provider()` is the single
function that changes when quota is granted.

## Reading it

Start with `docs/README.md`. If you only read one page, read
`docs/features/audit-engine/scoring.md` — it is the decision everything else follows from.
`docs/assignment/how-we-answered-it.md` maps your brief to what was built, requirement by
requirement.

`uv run pytest` is green at 364 tests; no test reaches a model, a broker or the network.

Happy to walk through any of it.

Best,
Pawan
