"""Operations worker: appointment requests and their outcomes.

Not built yet: no checks, so this category is reported as not evaluated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.recommendations.context import Context

KEY = "operations"
LABEL = "Operations"
WEIGHT = 15

CHECKS: dict[str, dict] = {}


def evaluate(c: Context) -> None:
    """Run every check this worker owns. Nothing to run yet."""
