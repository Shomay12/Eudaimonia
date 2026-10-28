"""Tests for Candlestick Engine and session-aligned aggregation.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
import pytest

from eudaimonia.engine.candle_engine import CandleEngine, SessionCandleAggregator
from eudaimonia.models.instrument import Exchange, Segment
from eudaimonia.models.market_data import CandleInterval, MarketTick

IST = ZoneInfo("Asia/Kolkata")


def make_tick(symbol: str, ltp: Decimal, volume: int, dt_ist: datetime) -> MarketTick:
    utc_dt = dt_ist.astimezone(timezone.utc)
    return MarketTick(
        symbol=symbol,
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        provider_id="mock",
        ltp=ltp,
        ltq=10,
        total_volume=volume,
        exchange_time=utc_dt,
        receipt_time=utc_dt,
    )


def test_candle_aggregation_and_vwap():
    symbol = "NSE:NIFTY"
    agg = SessionCandleAggregator(symbol, CandleInterval.M5)

    # Tick 1: 09:15:10 IST @ 25000, volume = 100
    t1 = datetime(2026, 10, 29, 9, 15, 10, tzinfo=IST)
    agg.process_tick(make_tick(symbol, Decimal("25000.0"), 100, t1))

    # Tick 2: 09:16:00 IST @ 25020, volume = 250 (delta = 150)
    t2 = datetime(2026, 10, 29, 9, 16, 0, tzinfo=IST)
    agg.process_tick(make_tick(symbol, Decimal("25020.0"), 250, t2))

    # Tick 3: 09:18:30 IST @ 24990, volume = 400 (delta = 150)
    t3 = datetime(2026, 10, 29, 9, 18, 30, tzinfo=IST)
    agg.process_tick(make_tick(symbol, Decimal("24990.0"), 400, t3))

    bars = agg.get_all_bars()
    assert len(bars) == 1
    b1 = bars[0]
    assert b1.open == Decimal("25000.0")
    assert b1.high == Decimal("25020.0")
    assert b1.low == Decimal("24990.0")
    assert b1.close == Decimal("24990.0")
    assert b1.trades == 3
    assert b1.is_complete is False

    # Rollover to next 5m candle: 09:20:05 IST @ 25010
    t4 = datetime(2026, 10, 29, 9, 20, 5, tzinfo=IST)
    completed_bar = agg.process_tick(make_tick(symbol, Decimal("25010.0"), 500, t4))

    assert completed_bar is not None
    assert completed_bar.is_complete is True
    assert completed_bar.close == Decimal("24990.0")

    all_bars = agg.get_all_bars()
    assert len(all_bars) == 2
    assert all_bars[1].open == Decimal("25010.0")


def test_candle_engine_multi_timeframe():
    engine = CandleEngine()
    symbol = "NSE:NIFTY"
    t1 = datetime(2026, 10, 29, 9, 15, 30, tzinfo=IST)
    engine.on_tick(make_tick(symbol, Decimal("25000.0"), 100, t1))

    # Verify both 1m and 5m bars are created
    bars_1m = engine.get_bars(symbol, CandleInterval.M1)
    bars_5m = engine.get_bars(symbol, CandleInterval.M5)

    assert len(bars_1m) == 1
    assert len(bars_5m) == 1
    assert bars_1m[0].open == Decimal("25000.0")
    assert bars_5m[0].open == Decimal("25000.0")
