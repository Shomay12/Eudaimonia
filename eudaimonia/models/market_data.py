"""Normalized market data structures (ticks, quotes, depth, candles).

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

from eudaimonia.models.events import DataQualityStatus
from eudaimonia.models.instrument import Exchange, Segment


class MarketDepthLevel(BaseModel):
    """A single price level in the market depth order book."""

    model_config = ConfigDict(frozen=True)

    price: Decimal = Field(..., ge=Decimal("0.0"))
    quantity: int = Field(..., ge=0)
    orders: int = Field(default=0, ge=0)


class MarketDepth(BaseModel):
    """5-level market depth order book."""

    bids: list[MarketDepthLevel] = Field(default_factory=list)
    asks: list[MarketDepthLevel] = Field(default_factory=list)

    @property
    def total_bid_qty(self) -> int:
        return sum(b.quantity for b in self.bids)

    @property
    def total_ask_qty(self) -> int:
        return sum(a.quantity for a in self.asks)


class MarketTick(BaseModel):
    """Normalized tick / quote event."""

    symbol: str = Field(..., description="Canonical internal symbol, e.g. NSE:NIFTY")
    exchange: Exchange
    segment: Segment
    provider_id: str
    ltp: Decimal = Field(..., description="Last Traded Price")
    ltq: int = Field(default=0, ge=0, description="Last Traded Quantity")
    total_volume: int = Field(default=0, ge=0, description="Day Total Traded Volume")
    open_interest: int = Field(default=0, ge=0, description="Current Open Interest")
    oi_change: int = Field(default=0, description="Change in OI from previous close")
    exchange_time: datetime = Field(..., description="Exchange source timestamp")
    receipt_time: datetime = Field(..., description="Local ingestion timestamp")
    best_bid: Decimal | None = None
    best_ask: Decimal | None = None
    bid_qty: int | None = None
    ask_qty: int | None = None
    depth: MarketDepth | None = None
    open_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    prev_close: Decimal | None = None
    sequence_id: int | None = None
    source: str = "unknown"
    quality: DataQualityStatus = DataQualityStatus.OK

    @property
    def change(self) -> Decimal | None:
        if self.prev_close and self.prev_close > Decimal("0"):
            return self.ltp - self.prev_close
        return None

    @property
    def change_pct(self) -> Decimal | None:
        if self.prev_close and self.prev_close > Decimal("0"):
            return ((self.ltp - self.prev_close) / self.prev_close) * Decimal("100")
        return None

    @property
    def spread(self) -> Decimal | None:
        if self.best_bid is not None and self.best_ask is not None:
            return max(Decimal("0.0"), self.best_ask - self.best_bid)
        return None


class CandleInterval(str, Enum):
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    D1 = "1d"

    @property
    def seconds(self) -> int:
        mapping = {
            CandleInterval.M1: 60,
            CandleInterval.M3: 180,
            CandleInterval.M5: 300,
            CandleInterval.M15: 900,
            CandleInterval.D1: 86400,
        }
        return mapping[self]


class CandleBar(BaseModel):
    """Aggregated OHLCV Candlestick bar."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    interval: CandleInterval
    timestamp: datetime = Field(..., description="Start timestamp of interval in Asia/Kolkata")
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = Field(default=0, ge=0)
    trades: int = Field(default=0, ge=0)
    vwap: Decimal | None = None
    is_complete: bool = False
