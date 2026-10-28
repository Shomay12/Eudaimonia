"""Options data models: contracts, greeks, strike rows, and chain snapshots.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

from eudaimonia.models.instrument import Exchange, Instrument, OptionType
from eudaimonia.models.market_data import MarketTick


class Moneyness(str, Enum):
    ITM = "ITM"
    ATM = "ATM"
    OTM = "OTM"


class Greeks(BaseModel):
    """Option Greeks and valuation analytics."""

    model_config = ConfigDict(frozen=True)

    iv: float = Field(..., ge=0.0, description="Implied Volatility (e.g. 0.15 = 15%)")
    delta: float = Field(..., description="Option Delta dV/dS")
    gamma: float = Field(..., ge=0.0, description="Option Gamma d2V/dS2")
    theta: float = Field(..., description="1-calendar-day Theta decay in INR")
    vega: float = Field(..., ge=0.0, description="Vega for 1% IV shift")
    rho: float = Field(..., description="Rho for 1% interest rate shift")
    intrinsic_value: Decimal = Field(default=Decimal("0.0"))
    extrinsic_value: Decimal = Field(default=Decimal("0.0"))
    is_converged: bool = True
    model_name: str = "Black-Scholes-Merton"
    calculated_at: datetime | None = None


class OptionStrikeRow(BaseModel):
    """Pair of Call and Put at a specific strike price."""

    strike_price: Decimal
    call_instrument: Instrument | None = None
    put_instrument: Instrument | None = None
    call_tick: MarketTick | None = None
    put_tick: MarketTick | None = None
    call_greeks: Greeks | None = None
    put_greeks: Greeks | None = None
    call_moneyness: Moneyness = Moneyness.OTM
    put_moneyness: Moneyness = Moneyness.OTM

    @property
    def call_ltp(self) -> Decimal | None:
        return self.call_tick.ltp if self.call_tick else None

    @property
    def put_ltp(self) -> Decimal | None:
        return self.put_tick.ltp if self.put_tick else None

    @property
    def call_oi(self) -> int:
        return self.call_tick.open_interest if self.call_tick else 0

    @property
    def put_oi(self) -> int:
        return self.put_tick.open_interest if self.put_tick else 0

    @property
    def call_oi_change(self) -> int:
        return self.call_tick.oi_change if self.call_tick else 0

    @property
    def put_oi_change(self) -> int:
        return self.put_tick.oi_change if self.put_tick else 0

    @property
    def call_volume(self) -> int:
        return self.call_tick.total_volume if self.call_tick else 0

    @property
    def put_volume(self) -> int:
        return self.put_tick.total_volume if self.put_tick else 0


class OptionChainSnapshot(BaseModel):
    """Complete snapshot of an options chain for a given underlying and expiry."""

    exchange: Exchange
    underlying: str
    underlying_price: Decimal = Field(..., ge=Decimal("0.0"))
    expiry: date
    available_expiries: list[date] = Field(default_factory=list)
    strikes: list[OptionStrikeRow] = Field(default_factory=list)
    atm_strike: Decimal
    pcr_oi: float | None = None
    pcr_volume: float | None = None
    total_ce_oi: int = 0
    total_pe_oi: int = 0
    total_ce_volume: int = 0
    total_pe_volume: int = 0
    max_pain: Decimal | None = None
    snapshot_time: datetime
