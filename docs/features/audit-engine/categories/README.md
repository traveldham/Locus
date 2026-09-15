# The six workers

One document per category. Each lists every check the worker owns, its weight inside the
category, its severity, exactly when it fires, exactly when it abstains, what it drafts, and
what was deliberately not built.

| Worker | Key | Weight | Checks | Answers |
| --- | --- | --- | --- | --- |
| [Profile completeness](profile.md) | `profile` | 20 | 28 | Is the listing complete, correct and verified? |
| [Reputation](reputation.md) | `reputation` | 20 | 10 | What do customers read, and does the business answer? |
| [Local visibility](visibility.md) | `visibility` | 25 | 11 | Does the profile show up when people search, and against whom? |
| [Operations](operations.md) | `operations` | 15 | 10 | Do appointment requests become visits? |
| [Performance](performance.md) | `performance` | 10 | 9 | Are impressions and actions holding up against the four weeks before? |
| [Content](content.md) | `content` | 10 | 9 | Does the profile show what the place looks like, and say anything new? |

67 checks. Weights sum to 100 and are asserted at import time.

## What every worker has in common

- A module at `backend/app/services/recommendations/categories/<key>.py` exporting `KEY`,
  `LABEL`, `WEIGHT`, a `CHECKS` dict and `evaluate(c)`.
- **One `assess` per check, always** — including when the check fires. A check that never
  assesses is invisible to the score.
- **A missing row is never treated as zero.** Abstain instead.
- A permanently closed profile **suppresses every check** in every worker.
- Wording is for a location manager: what was found, what to do. No column names in
  user-facing text.
- Most have a `card(snapshot)` for the category screen, and a suggestion module drafting text
  for the checks that declare a `suggests` field.

## Reading one

Each document's table has the same five columns — group, rule, weight, severity, fires when,
abstains when. The **abstains** column is the one to read carefully: it is where the
minimum-evidence gates live, and it is why a sparse profile scores nothing rather than badly.

The research behind the thresholds is in [../research/](../research/).
