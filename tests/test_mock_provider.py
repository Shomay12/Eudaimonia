"""Tests for Mock Provider simulation and provider interface contract.

Developer: KJshomay12
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import pytest

from eudaimonia.models.events import ConnectionState, DataMode
from eudaimonia.models.market_data import CandleInterval, MarketTick
from eudaimonia.providers.mock_provider import MockMarketDataProvider


@pytest.mark.asyncio
async def test_mock_provider_lifecycle():
    provider = MockMarketDataProvider()

    # Initial state
    assert provider.state == ConnectionState.DISCONNECTED
    assert provider.data_mode == DataMode.MOCK

    # Fetch instruments
    instruments = await provider.fetch_instruments()
    assert len(instruments) > 20

    # Ensure major indices and options are present
    symbols = [inst.symbol for inst in instruments]
    assert "NSE:NIFTY" in symbols
    assert "BSE:SENSEX" in symbols
    assert any("CE" in s for s in symbols)
    assert any("PE" in s for s in symbols)

    # Test tick emission callback
    received_ticks: list[MarketTick] = []

    async def on_tick(tick: MarketTick):
        received_ticks.append(tick)

    provider.register_on_tick(on_tick)

    # Connect and subscribe
    connected = await provider.connect()
    assert connected is True
    assert provider.state == ConnectionState.CONNECTED

    await provider.subscribe_quotes(["NSE:NIFTY", "NSE:BANKNIFTY"])

    # Wait briefly for ticker task to generate ticks
    await asyncio.sleep(0.6)

    assert len(received_ticks) > 0
    t = received_ticks[0]
    assert t.ltp > 0
    assert t.source == "MOCK_FEED"
    assert t.depth is not None

    # Fetch historical bars
    now = datetime.now(timezone.utc)
    bars = await provider.fetch_historical_bars(
        symbol="NSE:NIFTY",
        interval=CandleInterval.M5,
        from_time=now - timedelta(hours=2),
        to_time=now,
    )
    assert len(bars) > 5
    assert bars[0].open > 0
    assert bars[0].high >= bars[0].low

    # Disconnect
    await provider.disconnect()
    assert provider.state == ConnectionState.DISCONNECTED
