"""Abstract Market Data Provider Interface.

Developer: KJshomay12
"""

from __future__ import annotations

import abc
from datetime import date, datetime
from typing import Callable, Coroutine

from eudaimonia.models.events import DataMode, FeedStatus
from eudaimonia.models.instrument import Exchange, Instrument
from eudaimonia.models.market_data import CandleBar, CandleInterval, MarketDepth, MarketTick
from eudaimonia.models.options import OptionChainSnapshot

TickCallback = Callable[[MarketTick], Coroutine[None, None, None]]
DepthCallback = Callable[[str, MarketDepth], Coroutine[None, None, None]]
StatusCallback = Callable[[FeedStatus], Coroutine[None, None, None]]


class BaseMarketDataProvider(abc.ABC):
    """Abstract interface defining required provider interactions."""

    def __init__(self, name: str, data_mode: DataMode) -> None:
        self.name = name
        self.data_mode = data_mode
        self._on_tick_callbacks: list[TickCallback] = []
        self._on_depth_callbacks: list[DepthCallback] = []
        self._on_status_callbacks: list[StatusCallback] = []

    def register_on_tick(self, callback: TickCallback) -> None:
        """Register an async callback for market ticks."""
        self._on_tick_callbacks.append(callback)

    def register_on_depth(self, callback: DepthCallback) -> None:
        """Register an async callback for market depth updates."""
        self._on_depth_callbacks.append(callback)

    def register_on_status(self, callback: StatusCallback) -> None:
        """Register an async callback for feed status changes."""
        self._on_status_callbacks.append(callback)

    async def emit_tick(self, tick: MarketTick) -> None:
        """Deliver tick to registered listeners."""
        for cb in self._on_tick_callbacks:
            try:
                await cb(tick)
            except Exception:
                pass

    async def emit_depth(self, symbol: str, depth: MarketDepth) -> None:
        """Deliver depth to registered listeners."""
        for cb in self._on_depth_callbacks:
            try:
                await cb(symbol, depth)
            except Exception:
                pass

    async def emit_status(self, status: FeedStatus) -> None:
        """Deliver status update to registered listeners."""
        for cb in self._on_status_callbacks:
            try:
                await cb(status)
            except Exception:
                pass

    @abc.abstractmethod
    async def connect(self) -> bool:
        """Initialize provider session and start feed ingestion."""
        raise NotImplementedError

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Terminate provider connection and cleanup resources."""
        raise NotImplementedError

    @abc.abstractmethod
    async def subscribe_quotes(self, symbols: list[str]) -> bool:
        """Subscribe to real-time quotes/ticks for given canonical symbols."""
        raise NotImplementedError

    @abc.abstractmethod
    async def unsubscribe_quotes(self, symbols: list[str]) -> bool:
        """Unsubscribe from real-time quotes/ticks."""
        raise NotImplementedError

    @abc.abstractmethod
    async def subscribe_depth(self, symbols: list[str]) -> bool:
        """Subscribe to Level-2 5-depth order book for given symbols."""
        raise NotImplementedError

    @abc.abstractmethod
    async def unsubscribe_depth(self, symbols: list[str]) -> bool:
        """Unsubscribe from Level-2 5-depth order book."""
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_instruments(self, exchange: Exchange | None = None) -> list[Instrument]:
        """Fetch master list of tradable instruments."""
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_historical_bars(
        self,
        symbol: str,
        interval: CandleInterval,
        from_time: datetime,
        to_time: datetime,
    ) -> list[CandleBar]:
        """Fetch historical OHLCV bars."""
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_option_chain(
        self,
        underlying: str,
        expiry: date | None = None,
    ) -> OptionChainSnapshot | None:
        """Fetch full snapshot of option chain for given underlying and expiry."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_connection_status(self) -> FeedStatus:
        """Return current feed status."""
        raise NotImplementedError
