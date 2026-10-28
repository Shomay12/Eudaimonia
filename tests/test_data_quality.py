"""Tests for Data Quality anomaly detection and feed integrity.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from eudaimonia.engine.data_quality import DataQualityMonitor
from eudaimonia.models.events import DataQualityStatus
from eudaimonia.models.instrument import Exchange, Segment
from eudaimonia.models.market_data import MarketTick


def create_sample_tick(
    symbol: str = "NSE:NIFTY",
    ltp: Decimal = Decimal("25000.0"),
    seq: int | None = None,
    exchange_time: datetime | None = None,
    receipt_time: datetime | None = None,
) -> MarketTick:
    now = datetime.now(timezone.utc)
    return MarketTick(
        symbol=symbol,
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        provider_id="mock",
        ltp=ltp,
        ltq=50,
        total_volume=1000,
        exchange_time=exchange_time or now,
        receipt_time=receipt_time or now,
        sequence_id=seq,
    )


def test_non_positive_price_detection():
    monitor = DataQualityMonitor()
    bad_tick = create_sample_tick(ltp=Decimal("-10.0"))

    validated, event = monitor.validate_tick(bad_tick)
    assert validated.quality == DataQualityStatus.SUSPECT_PRICE
    assert event is not None
    assert event.status == DataQualityStatus.SUSPECT_PRICE


def test_sequence_gap_and_duplicate_detection():
    monitor = DataQualityMonitor()

    # Tick 1: seq 100
    t1 = create_sample_tick(seq=100)
    v1, e1 = monitor.validate_tick(t1)
    assert v1.quality == DataQualityStatus.OK
    assert e1 is None

    # Tick 2: seq 101 (consecutive, OK)
    t2 = create_sample_tick(seq=101)
    v2, e2 = monitor.validate_tick(t2)
    assert v2.quality == DataQualityStatus.OK

    # Tick 3: seq 105 (gap of 3 lost ticks)
    t3 = create_sample_tick(seq=105)
    v3, e3 = monitor.validate_tick(t3)
    assert v3.quality == DataQualityStatus.SEQUENCE_GAP
    assert e3 is not None

    # Tick 4: seq 104 (out of order / duplicate sequence)
    t4 = create_sample_tick(seq=104)
    v4, e4 = monitor.validate_tick(t4)
    assert v4.quality == DataQualityStatus.OUT_OF_ORDER


def test_out_of_order_timestamp_detection():
    monitor = DataQualityMonitor()
    t_now = datetime.now(timezone.utc)

    # First tick
    t1 = create_sample_tick(exchange_time=t_now)
    v1, _ = monitor.validate_tick(t1)
    assert v1.quality == DataQualityStatus.OK

    # Second tick with older timestamp
    t2 = create_sample_tick(exchange_time=t_now - timedelta(seconds=10))
    v2, e2 = monitor.validate_tick(t2)
    assert v2.quality == DataQualityStatus.OUT_OF_ORDER
    assert e2 is not None


def test_staleness_detection():
    monitor = DataQualityMonitor(stale_threshold_seconds=2.0)
    t_now = datetime.now(timezone.utc)

    t1 = create_sample_tick(receipt_time=t_now)
    monitor.validate_tick(t1)

    # Immediately: not stale
    assert monitor.is_symbol_stale("NSE:NIFTY", current_time=t_now + timedelta(seconds=1.0)) is False

    # After 3.5 seconds: stale!
    assert monitor.is_symbol_stale("NSE:NIFTY", current_time=t_now + timedelta(seconds=3.5)) is True
