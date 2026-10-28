"""Tests for normalized data models.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import pytest

from eudaimonia.models.instrument import Exchange, Instrument, InstrumentType, OptionType, Segment
from eudaimonia.models.market_data import (
    CandleBar,
    CandleInterval,
    MarketDepth,
    MarketDepthLevel,
    MarketTick,
)


def test_instrument_model():
    inst = Instrument(
        symbol="NSE:NIFTY26OCT25000CE",
        tradingsymbol="NIFTY26OCT25000CE",
        name="NIFTY 25000 CE",
        exchange=Exchange.NSE,
        segment=Segment.DERIVATIVE,
        instrument_type=InstrumentType.OPTION,
        provider_id="12345",
        underlying="NIFTY",
        lot_size=25,
        tick_size=Decimal("0.05"),
        strike_price=Decimal("25000.0"),
        expiry_date=date(2026, 10, 29),
        option_type=OptionType.CE,
    )

    assert inst.is_option is True
    assert inst.is_index is False
    assert inst.strike_price == Decimal("25000.0")
    assert inst.lot_size == 25


def test_market_tick_calculations():
    now = datetime.now(timezone.utc)
    tick = MarketTick(
        symbol="NSE:NIFTY",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        provider_id="idx_1",
        ltp=Decimal("25050.00"),
        ltq=50,
        total_volume=1000000,
        exchange_time=now,
        receipt_time=now,
        best_bid=Decimal("25049.50"),
        best_ask=Decimal("25050.50"),
        prev_close=Decimal("25000.00"),
    )

    assert tick.change == Decimal("50.00")
    assert tick.change_pct == Decimal("0.20")
    assert tick.spread == Decimal("1.00")


def test_market_depth_totals():
    depth = MarketDepth(
        bids=[
            MarketDepthLevel(price=Decimal("100.0"), quantity=50, orders=2),
            MarketDepthLevel(price=Decimal("99.5"), quantity=100, orders=4),
        ],
        asks=[
            MarketDepthLevel(price=Decimal("100.5"), quantity=60, orders=3),
            MarketDepthLevel(price=Decimal("101.0"), quantity=40, orders=1),
        ],
    )

    assert depth.total_bid_qty == 150
    assert depth.total_ask_qty == 100
