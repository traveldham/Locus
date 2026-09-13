"""Generated suggestions, layered on top of a worker's deterministic result.

`enrich` is the one entry point. It never raises: the outcome is written on the
result under `suggestions` as generated, skipped or failed, and the worker's verdicts
and findings are untouched either way. Which model answers is decided by
`suggestions/llm.py`, not here.
"""

from importlib import import_module
from types import ModuleType

from app.core.config import Settings, get_settings
from app.services.recommendations.categories import WORKERS
from app.services.recommendations.suggestions.llm import (
    SuggestionError,
    provider_from_settings,
    unavailable_reason,
)


def _discover() -> dict[str, ModuleType]:
    """One optional module per worker: `suggestions/<category>.py`.

    A worker without a suggestion layer simply has no module. Each module exposes
    `targets`, `wants`, `business_context`, `build_prompt`, `apply`,
    `fallback_summary` and `RESPONSE_SCHEMA`, the way `profile.py` does.
    """
    found: dict[str, ModuleType] = {}
    for worker in WORKERS:
        try:
            found[worker.KEY] = import_module(
                f"app.services.recommendations.suggestions.{worker.KEY}"
            )
        except ModuleNotFoundError as error:
            if error.name != f"app.services.recommendations.suggestions.{worker.KEY}":
                raise
    return found


ENRICHERS = _discover()


async def enrich(category: str, snapshot: dict, result: dict, settings: Settings | None = None):
    settings = settings or get_settings()
    module = ENRICHERS.get(category)
    status: dict = {"status": "skipped", "provider": settings.llm_provider}
    provider = provider_from_settings(settings) if settings.suggestions_enabled else None
    if module is None:
        status["reason"] = "This worker has no suggestion layer."
    elif not settings.suggestions_enabled:
        status["reason"] = "Suggestions are disabled."
    elif provider is None:
        status["reason"] = unavailable_reason(settings)
    else:
        items = module.targets(result)
        status["model"] = provider.model
        if not module.wants(result):
            status["reason"] = "Nothing to draft or summarise."
        else:
            try:
                context = module.business_context(snapshot)
                response = await provider.generate_json(
                    module.build_prompt(context, items, result.get("items", [])),
                    module.RESPONSE_SCHEMA,
                )
                status["status"] = "generated"
                status["attached"] = module.apply(
                    result, response, provider.name, provider.model, context
                )
                status["requested"] = len(items)
            except SuggestionError as error:
                status["status"] = "failed"
                status["error"] = str(error)[:500]
    result["suggestions"] = status
    if module is not None and "summary" not in result:
        result["summary"] = module.fallback_summary(result)
    return result
