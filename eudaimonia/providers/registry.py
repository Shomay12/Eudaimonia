"""Market data provider factory and registry.

Developer: KJshomay12
"""

from __future__ import annotations

from eudaimonia.config import settings
from eudaimonia.providers.base import BaseMarketDataProvider
from eudaimonia.providers.kite_provider import KiteConnectMarketDataProvider
from eudaimonia.providers.mock_provider import MockMarketDataProvider
from eudaimonia.providers.upstox_provider import UpstoxMarketDataProvider


def get_market_data_provider(provider_name: str | None = None) -> BaseMarketDataProvider:
    """Create and return configured provider instance."""
    name = (provider_name or settings.PROVIDER_NAME).lower()

    if name in ("mock", "simulation"):
        return MockMarketDataProvider()
    elif name in ("kite", "zerodha"):
        return KiteConnectMarketDataProvider()
    elif name in ("upstox", "upstox_v2"):
        return UpstoxMarketDataProvider()
    else:
        # Default fallback to Mock
        return MockMarketDataProvider()
