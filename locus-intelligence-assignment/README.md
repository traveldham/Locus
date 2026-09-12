# Locus — Take-home: Location Intelligence Prototype

## The context

Locus works with multi-location businesses. A single company might run 5 or 500 physical
locations, each with its own Google Business Profile, its own reviews, its own local search
ranking, and its own customers. The owner cannot look at 500 dashboards. They want to know one
thing: **what should we do next, and where?**

This exercise gives you a snapshot of one such business and asks you to build the layer that
answers that question.

## The dataset

`data/` contains a simplified, fully synthetic export for **Brightpath Dental**, a dental group
with 12 clinics across Texas and Arizona. It covers roughly a year of reviews and a rolling
quarter of performance, ranking, booking and profile data.

Every column is documented in `DATA.md`. The data is simplified compared to production, but the
shape, the join keys and the value vocabularies mirror what we actually store.

Nothing in the data is labelled. There is no answer key column, no score, no flag. Reading the
data is part of the task.

## The task

Build a working prototype of an **intelligence layer** on top of this data: a system that looks at
a location and produces specific, defensible recommendations for how that location could perform
better.

What "better" means for a local business is yours to define and defend. So is what a good
recommendation looks like. We care much more about the reasoning behind your system than about
the number of features in it.

Every recommendation your system makes must carry its own justification: why this location, why
this action, and which data it rests on. A recommendation a clinic manager cannot trace back to
something in the dataset is not finished.

At minimum, your prototype should be able to take a location and return its recommendations, and
should be able to run across all 12 locations. How you surface that — CLI output, JSON, a notebook,
a small web page, an API — is your call. A small web UI is highly recommended: seeing the
recommendations laid out is usually the fastest way for us to understand what your engine is
doing and how you think it should be read.

We will be looking at two things: the thought process behind how you approach this problem with an
AI intelligence engine, and how you think about showcasing it. What you choose to put in front of
someone, and why that form makes the reasoning and the evidence easy to judge, is part of the
answer — not packaging on top of it.

You may use any language, any libraries, and an LLM if you want one. If you use an LLM, be
deliberate about what it decides and what your own code decides.

We will not be running your prototype. What we look at is the output it produced and the code
behind it, so hand back real output rather than a promise of it.

## What to hand back

1. **Output** — the real recommendations your system produced for all 12 locations, committed so
   we can read them directly (JSON, Markdown, CSV, or screenshots / a short screen recording if
   you built a web UI).
2. **The code** that produced it, plus a short note on how it runs — for reading, not for us to
   execute.
3. **A write-up, max 2 pages** (`NOTES.md`) covering:
   - how your system decides what to recommend, and why you designed it that way;
   - what you would trust in your output and what you would not;
   - what you deliberately did not build, and what you would build next with another week;
   - anything in the data you found unreliable, ambiguous, or misleading.

## How we will read it

- Did you understand the data before building on it?
- Are the recommendations specific, grounded in the data, and actually actionable by a clinic
  manager — or are they generic advice that would be true for any business?
- Can you show the evidence for any given recommendation?
- Does the system distinguish between what matters a lot and what matters a little?
- Is the code something a teammate could pick up and extend?
- Does the write-up show judgement, including about your own work's limits?

Scope honestly. A small system that works, whose limits you understand and state, beats a large
one that mostly asserts things.

## Ground rules

- The data is synthetic. Do not go looking for the real business; it does not exist.
- Questions about the *task* are welcome — ask.
- Send back a git repo (zip or link) with your commit history intact.
