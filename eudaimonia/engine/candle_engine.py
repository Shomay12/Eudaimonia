"""Real-time multi-timeframe Candlestick aggregator and historical bar manager.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from eudaimonia.config import settings
from eudaimonia.models.market_data import CandleBar, CandleInterval, MarketTick

IST_ZONE = ZoneInfo("Asia/Kolkata")
MARKET_OPEN_TIME = time(9, 15)
MARKET_CLOSE_TIME = time(15, 30)


class SessionCandleAggregator:
    """Aggregates streaming ticks into OHLCV bars aligned with Indian market session boundaries."""

    def __init__(self, symbol: str, interval: CandleInterval) -> None:
        self.symbol = symbol
        self.interval = interval
        self.bars: list[CandleBar] = []
        self._current_bar: CandleBar | None = None
        self._cumulative_pv: Decimal = Decimal("0.0")  # Price * Volume for VWAP
        self._cumulative_volume: int = 0
        self._last_tick_volume: int = 0

    def _get_bar_start_time(self, dt: datetime) -> datetime:
        """Align datetime to interval boundary in Asia/Kolkata."""
        ist_dt = dt.astimezone(IST_ZONE)
        interval_secs = self.interval.seconds

        if self.interval == CandleInterval.D1:
            return ist_dt.replace(hour=9, minute=15, second=0, microsecond=0)

        # For intraday bars, align relative to 09:15 market open
        session_start = ist_dt.replace(hour=9, minute=15, second=0, microsecond=0)
        if ist_dt < session_start:
            # Pre-market or early tick
            epoch_secs = int(ist_dt.timestamp())
            aligned_epoch = epoch_secs - (epoch_secs % interval_secs)
            return datetime.fromtimestamp(aligned_epoch, tz=IST_ZONE)

        seconds_since_open = int((ist_dt - session_start).total_seconds())
        bar_offset = seconds_since_open - (seconds_since_open % interval_secs)
        return session_start + timedelta(seconds=bar_offset)

    def process_tick(self, tick: MarketTick) -> CandleBar | None:
        """Process incoming tick, update active bar or complete previous bar."""
        if tick.symbol != self.symbol:
            return None

        price = tick.ltp
        # Volume delta for this tick
        if self._last_tick_volume == 0:
            vol_delta = tick.ltq if tick.ltq > 0 else 1
        else:
            vol_delta = max(0, tick.total_volume - self._last_tick_volume)
        self._last_tick_volume = tick.total_volume

        # Update session VWAP statistics
        self._cumulative_pv += price * Decimal(str(vol_delta))
        self._cumulative_volume += vol_delta
        current_vwap = (
            self._cumulative_pv / Decimal(str(self._cumulative_volume))
            if self._cumulative_volume > 0
            else price
        )

        bar_start = self._get_bar_start_time(tick.exchange_time)
        completed_bar: CandleBar | None = None

        if self._current_bar is None:
            # Start new bar
            self._current_bar = CandleBar(
                symbol=self.symbol,
                interval=self.interval,
                timestamp=bar_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=vol_delta,
                trades=1,
                vwap=round(current_vwap, 2),
                is_complete=False,
            )
        elif bar_start == self._current_bar.timestamp:
            # Update existing bar
            self._current_bar = CandleBar(
                symbol=self.symbol,
                interval=self.interval,
                timestamp=self._current_bar.timestamp,
                open=self._current_bar.open,
                high=max(self._current_bar.high, price),
                low=min(self._current_bar.low, price),
                close=price,
                volume=self._current_bar.volume + vol_delta,
                trades=self._current_bar.trades + 1,
                vwap=round(current_vwap, 2),
                is_complete=False,
            )
        else:
            # Bar rolled over: finalize previous bar
            completed_bar = self._current_bar.model_copy(update={"is_complete": True})
            self.bars.append(completed_bar)

            # Start new bar
            self._current_bar = CandleBar(
                symbol=self.symbol,
                interval=self.interval,
                timestamp=bar_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=vol_delta,
                trades=1,
                vwap=round(current_vwap, 2),
                is_complete=False,
            )

        return completed_bar

    def get_all_bars(self) -> list[CandleBar]:
        """Return all finalized bars plus active forming bar."""
        result = list(self.bars)
        if self._current_bar:
            result.append(self._current_bar)
        return result

    def add_historical_bars(self, bars: list[CandleBar]) -> None:
        """Prepend or merge historical bars."""
        existing_ts = {b.timestamp for b in self.bars}
        new_bars = [b for b in bars if b.timestamp not in existing_ts]
        self.bars = sorted(self.bars + new_bars, key=lambda b: b.timestamp)


class CandleEngine:
    """Manages multi-timeframe aggregators across multiple symbols."""

    def __init__(self) -> None:
        # Key: (symbol, interval) -> SessionCandleAggregator
        self._aggregators: dict[tuple[str, CandleInterval], SessionCandleAggregator] = {}

    def get_or_create(self, symbol: str, interval: CandleInterval) -> SessionCandleAggregator:
        key = (symbol, interval)
        if key not in self._aggregators:
            self._aggregators[key] = SessionCandleAggregator(symbol, interval)
        return self._aggregators[key]

    def on_tick(self, tick: MarketTick) -> None:
        """Feed tick to intervals for this symbol."""
        for interval in CandleInterval:
            agg = self.get_or_create(tick.symbol, interval)
            agg.process_tick(tick)

    def get_bars(self, symbol: str, interval: CandleInterval) -> list[CandleBar]:
        agg = self.get_or_create(symbol, interval)
        return agg.get_all_bars()
