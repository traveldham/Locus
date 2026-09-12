"""The Google Business Profile data provider.

One implementation behind the `GbpProvider` protocol: `SampleGbpProvider`, which serves
the sample CSV dataset. Google never approved this Cloud project for Business Profile API
access — every live read came back `429 RESOURCE_EXHAUSTED` with `quota_limit_value: 0` —
so the live implementation has been removed rather than kept as code that cannot run.

`get_provider()` stays the single construction point so the API layer never instantiates
a provider itself.
"""

from app.services.providers.base import (
    EDITABLE_FIELDS,
    UPDATE_MASK_PATHS,
    GbpProvider,
    LocationChanges,
    ProviderAccount,
    ProviderAttribute,
    ProviderCategory,
    ProviderError,
    ProviderHoursPeriod,
    ProviderLocation,
    UpdateResult,
    build_update_mask,
    validate_changes,
)
from app.services.providers.sample import SampleGbpProvider


def get_provider() -> GbpProvider:
    """The Business Profile provider. There is only one, and it reads the sample CSVs."""
    return SampleGbpProvider()


__all__ = [
    "EDITABLE_FIELDS",
    "UPDATE_MASK_PATHS",
    "GbpProvider",
    "LocationChanges",
    "ProviderAccount",
    "ProviderAttribute",
    "ProviderCategory",
    "ProviderError",
    "ProviderHoursPeriod",
    "ProviderLocation",
    "SampleGbpProvider",
    "UpdateResult",
    "build_update_mask",
    "get_provider",
    "validate_changes",
]
