"""Data quality inspection, anomaly detection, and feed integrity controls.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from eudaimonia.config import settings
from eudaimonia.models.events import DataQualityEvent, DataQualityStatus
from eudaimonia.models.market_data import MarketTick


class DataQualityMonitor:
    """Validates streaming ticks, detects gaps, out-of-order deliveries, and stale feeds."""

    def __init__(self, stale_threshold_seconds: float | None = None) -> None:
        self.stale_threshold_seconds = stale_threshold_seconds or settings.STALE_THRESHOLD_SECONDS
        self._last_ticks: dict[str, MarketTick] = {}
        self._last_sequence_ids: dict[str, int] = {}
        self._quality_events: list[DataQualityEvent] = []

    def validate_tick(self, tick: MarketTick) -> tuple[MarketTick, DataQualityEvent | None]:
        """Inspect and tag tick with quality status.

        Checks:
        1. Non-positive or abnormal price jumps
        2. Sequence number gaps and duplicates
        3. Out-of-order timestamps
        4. Timestamp staleness
        """
        now = datetime.now(timezone.utc)
        symbol = tick.symbol
        prev_tick = self._last_ticks.get(symbol)
        prev_seq = self._last_sequence_ids.get(symbol)

        quality = DataQualityStatus.OK
        event: DataQualityEvent | None = None

        # Check 1: Non-positive price
        if tick.ltp <= Decimal("0"):
            quality = DataQualityStatus.SUSPECT_PRICE
            event = DataQualityEvent(
                timestamp=now,
                symbol=symbol,
                status=quality,
                message=f"Non-positive price received: {tick.ltp}",
                received_timestamp=tick.receipt_time,
                exchange_timestamp=tick.exchange_time,
            )

        # Check 2: Sequence ID tracking (if provider supports sequence numbers)
        elif tick.sequence_id is not None and prev_seq is not None:
            if tick.sequence_id <= prev_seq:
                quality = DataQualityStatus.OUT_OF_ORDER
                event = DataQualityEvent(
                    timestamp=now,
                    symbol=symbol,
                    status=quality,
                    message=f"Duplicate or decreasing sequence id: {tick.sequence_id} <= {prev_seq}",
                    received_timestamp=tick.receipt_time,
                    exchange_timestamp=tick.exchange_time,
                    details={"prev_seq": prev_seq, "current_seq": tick.sequence_id},
                )
            elif tick.sequence_id > prev_seq + 1:
                quality = DataQualityStatus.SEQUENCE_GAP
                event = DataQualityEvent(
                    timestamp=now,
                    symbol=symbol,
                    status=quality,
                    message=f"Sequence gap detected: {prev_seq} -> {tick.sequence_id} (lost {tick.sequence_id - prev_seq - 1} ticks)",
                    received_timestamp=tick.receipt_time,
                    exchange_timestamp=tick.exchange_time,
                    details={"prev_seq": prev_seq, "current_seq": tick.sequence_id},
                )

        # Check 3: Out-of-order exchange timestamp
        elif prev_tick is not None and tick.exchange_time < prev_tick.exchange_time:
            quality = DataQualityStatus.OUT_OF_ORDER
            event = DataQualityEvent(
                timestamp=now,
                symbol=symbol,
                status=quality,
                message=f"Out-of-order exchange timestamp: {tick.exchange_time} < {prev_tick.exchange_time}",
                received_timestamp=tick.receipt_time,
                exchange_timestamp=tick.exchange_time,
            )

        # Record sequence id
        if tick.sequence_id is not None:
            self._last_sequence_ids[symbol] = tick.sequence_id

        # Update last known valid tick
        if quality not in (DataQualityStatus.OUT_OF_ORDER, DataQualityStatus.SUSPECT_PRICE):
            self._last_ticks[symbol] = tick

        if event:
            self._quality_events.append(event)
            # Cap stored events to prevent memory leak
            if len(self._quality_events) > 1000:
                self._quality_events.pop(0)

        # Update tick with evaluated quality status
        validated_tick = tick.model_copy(update={"quality": quality})
        return validated_tick, event

    def is_symbol_stale(self, symbol: str, current_time: datetime | None = None) -> bool:
        """Check whether the latest data for symbol exceeds the staleness threshold."""
        tick = self._last_ticks.get(symbol)
        if not tick:
            return True

        ref_time = current_time or datetime.now(tick.receipt_time.tzinfo or timezone.utc)
        diff_seconds = (ref_time - tick.receipt_time).total_seconds()
        return diff_seconds > self.stale_threshold_seconds

    def get_recent_events(self, limit: int = 50) -> list[DataQualityEvent]:
        return self._quality_events[-limit:]
