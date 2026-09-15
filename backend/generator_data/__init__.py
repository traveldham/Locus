"""Synthetic demo profiles: deliberately poor-quality businesses for the audit demo.

The seeded demo world is twelve healthy dental clinics, which demos badly: the audit
finds little, so the suggestion layer and the agent have nothing to do. This package
generates ten extra profiles across ten different industries whose data is **present and
bad** rather than absent, so the real engine scores them low and produces a rich set of
findings.

Nothing here touches the application. It is a standalone data factory that writes
through `app.models` only:

    uv run python -m generator_data            # write every archetype into the database
    uv run python -m generator_data --verify   # audit each archetype, print the scores

The whole point is the "present and bad" rule. `scoring.py` excludes unevaluated checks
from the denominator, so a sparse profile reports low coverage and a `not_evaluated`
grade rather than a bad score. Every archetype therefore carries enough volume to clear
each check's minimum-evidence gate in `EngineConfig` before failing it.
"""

from generator_data.archetypes import ARCHETYPES, Archetype, Problems, by_key
from generator_data.generator import ProfileData, generate
from generator_data.importer import ImportResult, catalogue, import_archetypes
from generator_data.snapshot import snapshot_of

__all__ = [
    "ARCHETYPES",
    "Archetype",
    "ImportResult",
    "ProfileData",
    "Problems",
    "by_key",
    "catalogue",
    "generate",
    "import_archetypes",
    "snapshot_of",
]
