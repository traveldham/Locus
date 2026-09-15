# Scoring

Code: `backend/app/services/recommendations/scoring.py` and `policy.py`.
Every number on this page is an explicit operating decision. None of it is a calibrated
probability, a forecast, or a claim about Google's ranking algorithm. Changing any of it
changes the score, which is why it lives in the engine version rather than in a rule body.

## The one thing to understand first

**Missing data does not lower the score.** A check that cannot find enough evidence
returns `insufficient_data` and is dropped from the denominator — never counted as a
failure, never counted as a pass.

```python
if verdict is None or verdict["state"] in ("insufficient_data", "suppressed"):
    c_skipped += 1
    continue          # not in `possible`, not in `earned`
possible += weight
```

The consequence catches people out constantly: **a profile with sparse data reports high
coverage loss and a `not_evaluated` grade, not a bad score.** If you want a profile to
score badly, its data has to be *present and bad*, and it has to clear each check's
minimum-evidence gate first. Three reviews produce `insufficient_data`; thirty reviews
averaging 2.1 stars produce a critical finding. This is the entire reason
[demo-profiles](../demo-profiles/overview.md) generates volume rather than emptiness.

## The four verdicts

Every check ends in exactly one, recorded by `Context.assess(...)` — including when the
check fires.

| State | Meaning | Effect on the score |
| --- | --- | --- |
| `triggered` | The check found an issue | Loses credit, by severity and by how widely it failed |
| `clear` | The check passed | Full credit |
| `insufficient_data` | Not enough evidence to judge | Excluded from the denominator |
| `suppressed` | Does not apply | Excluded from the denominator |

`suppressed` is for "this question is not askable here", not "we could not answer it":
a permanently closed profile suppresses every check in every worker, and
`photos_below_target` is suppressed when the profile is already below the photo floor,
because the floor check owns that finding.

Each verdict also carries `issues` and `evaluated` — how many subjects failed out of how
many were examined. For a single-subject check these are `1` and `1`. For an enumerating
check (one finding per keyword, per review, per weekday) they are the real counts, and
they drive the penalty below.

## Category weights

Declared by each worker module as `WEIGHT`, gathered in `policy.CATEGORIES`, and asserted
to sum to 100 at import time.

| Category | Key | Weight |
| --- | --- | --- |
| Profile completeness | `profile` | 20 |
| Reputation | `reputation` | 20 |
| Local visibility | `visibility` | 25 |
| Operations | `operations` | 15 |
| Performance | `performance` | 10 |
| Content | `content` | 10 |

Inside a category each check carries its own weight, declared beside it in that worker's
`CHECKS` dict. Those weights do not sum to any particular number — a category score is a
share, so only the ratios matter.

## Severity

A finding's `score` (0-100) is computed by the rule, then banded:

```python
CRITICAL_SCORE = 75     # score >= 75 -> critical
WARNING_SCORE  = 45     # score >= 45 -> warning, below -> notice
```

Severity is **graded from magnitude, not fixed per rule**. `grading.graded(base,
magnitude, span, cap)` scales a rule's floor score by how far past its threshold the
finding sits, where `magnitude` is the 0..1 fraction of the way from the trigger point to
the point the policy treats as fully severe:

```python
def graded(base, magnitude, span, cap):
    return int(min(cap, base + round(span * max(0.0, min(1.0, magnitude)))))
```

So a rating of 3.9 and a rating of 1.8 both trigger `rating_low`, but only the second is
critical. This matters more than it looks: the penalty table below is keyed on severity,
so the difference between a 44 and a 46 is the difference between losing a quarter of a
check's credit and losing three fifths of it.

## The penalty

How much of a failing check's credit is removed:

```python
SEVERITY_PENALTY = {"critical": 1.0, "warning": 0.6, "notice": 0.25}
ENUMERATED_FLOOR = 0.4
```

For a single-subject check the penalty is simply the severity penalty. For an enumerating
check it is scaled by the share of examined subjects that failed, with a floor so that a
single failure still costs something:

```python
def penalty_for(verdict, rule_items):
    severity = SEVERITY_PENALTY[worst_severity_of(rule_items)]
    checked = max(1, verdict.get("evaluated", 1))
    if checked <= 1:
        return severity
    share = min(1.0, max(verdict.get("issues", 0), len(rule_items)) / checked)
    return min(1.0, severity * (ENUMERATED_FLOOR + (1 - ENUMERATED_FLOOR) * share))
```

The share, not the raw count, is deliberate: **a location that tracks forty keywords must
not score worse than one that tracks four**, simply for tracking them. One keyword out of
forty falling out of the pack is a small problem; thirty out of forty is a large one, and
the arithmetic says so.

Worked example — `hours_weekday_gaps`, weight 2, three of five weekdays missing, worst
severity `warning`:

```
share   = 3 / 5                        = 0.6
penalty = 0.6 * (0.4 + 0.6 * 0.6)      = 0.456
earned  = 2 * (1 - 0.456)              = 1.088   of a possible 2
```

## Category score

```
category score = round(100 * earned / possible)
```

where `possible` is the summed weight of the checks that were actually evaluated and
`earned` adds the full weight of each `clear` check plus the residue of each `triggered`
one. A category in which nothing could be evaluated scores `null` and is excluded from
the health score — it is not a zero.

## Health score

The weighted mean of the categories that produced a score:

```
health = round( Σ(category_score × category_weight) / Σ(category_weight) )
```

over scored categories only. An engine in which nothing evaluated therefore reports
`null`, never `100`.

`coverage` is reported alongside it:

```
coverage = (passed + failed) / (passed + failed + skipped)
```

Read the two together. A score of 78 at coverage 0.95 is a real result; a score of 78 at
coverage 0.40 means most of the profile was never judged.

## Grades

```python
GRADES = (("excellent", 90), ("good", 75), ("fair", 50), ("poor", 0))
```

`None` grades as `not_evaluated`. In practice:

| Grade | Score |
| --- | --- |
| excellent | 90-100 |
| good | 75-89 |
| fair | 50-74 |
| poor | 0-49 |
| not_evaluated | no category could be scored |

## What the shape of the policy implies

Worth knowing before you try to make a profile score a particular number:

- **Notices are nearly free.** A notice removes a quarter of one check's weight. A
  category made mostly of notices — visibility has several — cannot fall far however badly
  the location is doing. In practice visibility bottoms out near 45 and operations near
  55, even when every single check in them fires.
- **Criticals are where the score moves.** `unverified`, `phone_missing`,
  `primary_category_missing`, `hours_missing`, `posts_none_recent` (when no post exists)
  and a 1-star-heavy `critical_review_unanswered` each remove their full weight.
- **Reputation and performance fall furthest**, because their high-weight checks grade
  into critical readily.
- Therefore an overall score below 50 needs *every* category to be bad, not two.

## Check inventory

`check_inventory(items, evaluations)` returns one row per check the engine can run —
whether or not it fired — carrying its category, its documentation (`label`, `checks`,
`fix`, `unit`, `group`, `effort`), its state and reason, `subjects_failed`,
`subjects_examined`, the worst severity among its findings and its highest score. This is
what lets the UI show "23 of 67 checks passed, 9 could not be judged, and here is why"
rather than only listing the failures.

## The basis string

Every report carries the scoring rationale in prose, so the UI never restates it from
memory:

> Weighted share of evaluated checks that passed, reduced by each failing check's severity
> and by the share of the subjects it examined that failed. Checks without enough evidence
> are excluded from the score, never counted as passes.

## Related

- [architecture.md](architecture.md) — the pipeline that produces the verdicts
- [categories/](categories/) — every check, its weight, and when it abstains
- `GET /api/v1/recommendations/policy` returns all of the above as JSON, so the frontend
  never hardcodes a weight or a band.
