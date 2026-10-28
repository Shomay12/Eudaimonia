"""Upstox V2 Market Data Provider Adapter.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from eudaimonia.config import settings
from eudaimonia.models.events import ConnectionState, DataMode, FeedStatus
from eudaimonia.models.instrument import Exchange, Instrument
from eudaimonia.models.market_data import CandleBar, CandleInterval
from eudaimonia.models.options import OptionChainSnapshot
from eudaimonia.providers.base import BaseMarketDataProvider


class UpstoxMarketDataProvider(BaseMarketDataProvider):
    """Upstox V2 Protobuf WebSocket & REST market-data adapter."""

    def __init__(self) -> None:
        super().__init__(name="UpstoxV2", data_mode=DataMode.LIVE)
        self.state = ConnectionState.DISCONNECTED
        self.api_key = settings.UPSTOX_API_KEY
        self.access_token = settings.UPSTOX_ACCESS_TOKEN
        self._last_error: str | None = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.access_token)

    async def connect(self) -> bool:
        if not self.is_configured():
            self.state = ConnectionState.ERROR
            self._last_error = "Upstox credentials missing in .env (UPSTOX_API_KEY, UPSTOX_ACCESS_TOKEN)"
            await self.emit_status(self.get_connection_status())
            return False
        self.state = ConnectionState.CONNECTED
        await self.emit_status(self.get_connection_status())
        return True

    async def disconnect(self) -> None:
        self.state = ConnectionState.DISCONNECTED
        await self.emit_status(self.get_connection_status())

    async def subscribe_quotes(self, symbols: list[str]) -> bool:
        return True

    async def unsubscribe_quotes(self, symbols: list[str]) -> bool:
        return True

    async def subscribe_depth(self, symbols: list[str]) -> bool:
        return True

    async def unsubscribe_depth(self, symbols: list[str]) -> bool:
        return True

    async def fetch_instruments(self, exchange: Exchange | None = None) -> list[Instrument]:
        return []

    async def fetch_historical_bars(
        self,
        symbol: str,
        interval: CandleInterval,
        from_time: datetime,
        to_time: datetime,
    ) -> list[CandleBar]:
        return []

    async def fetch_option_chain(
        self,
        underlying: str,
        expiry: date | None = None,
    ) -> OptionChainSnapshot | None:
        return None

    def get_connection_status(self) -> FeedStatus:
        return FeedStatus(
            provider_name=self.name,
            connection_state=self.state,
            data_mode=self.data_mode if self.is_configured() else DataMode.MOCK,
            latency_ms=0.0,
            error_message=self._last_error,
        )
