"""The six workers of an audit, in the order they are reported.

Each worker is a module with the same surface:

- `KEY`, `LABEL`, `WEIGHT` — its category and its share of the health score.
- `CHECKS` — the checks it owns, keyed by rule: a weight inside the category plus the
  wording the UI shows (`label`, `checks`, `fix`, `unit`, `predicate`, ...).
- `evaluate(c)` — runs every check against the profile in `c`, calling `c.assess`
  exactly once per rule and `c.emit` for each finding.

Workers are independent: none reads another's result. They are built one at a time,
and an empty `CHECKS` simply means that category is not evaluated yet.
"""

from types import ModuleType

from app.services.recommendations.categories import (
    content,
    operations,
    performance,
    profile,
    reputation,
    visibility,
)

WORKERS: tuple[ModuleType, ...] = (
    profile,
    reputation,
    visibility,
    operations,
    performance,
    content,
)

BY_KEY = {worker.KEY: worker for worker in WORKERS}


def worker_for(category: str) -> ModuleType:
    return BY_KEY[category]
