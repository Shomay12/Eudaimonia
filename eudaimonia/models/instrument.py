"""Normalized instrument definitions for NSE and BSE.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"


class Segment(str, Enum):
    EQUITY = "EQUITY"
    DERIVATIVE = "DERIVATIVE"
    INDEX = "INDEX"


class InstrumentType(str, Enum):
    EQUITY = "EQUITY"
    INDEX = "INDEX"
    FUTURES = "FUTURES"
    OPTION = "OPTION"


class OptionType(str, Enum):
    CE = "CE"  # Call European
    PE = "PE"  # Put European


class Instrument(BaseModel):
    """Normalized Instrument Representation."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., description="Canonical internal symbol e.g. NSE:NIFTY26OCT25000CE or NSE:RELIANCE")
    tradingsymbol: str = Field(..., description="Broker/Exchange trading symbol e.g. NIFTY26OCT25000CE")
    name: str = Field(..., description="Display name e.g. NIFTY 25000 CE")
    exchange: Exchange
    segment: Segment
    instrument_type: InstrumentType
    provider_id: str = Field(..., description="Provider token or exchange instrument id")
    underlying: str | None = Field(default=None, description="Underlying symbol e.g. NIFTY")
    lot_size: int = Field(default=1, ge=1)
    tick_size: Decimal = Field(default=Decimal("0.05"), ge=Decimal("0.01"))
    strike_price: Decimal | None = None
    expiry_date: date | None = None
    option_type: OptionType | None = None
    is_active: bool = True

    @property
    def is_option(self) -> bool:
        return self.instrument_type == InstrumentType.OPTION

    @property
    def is_future(self) -> bool:
        return self.instrument_type == InstrumentType.FUTURES

    @property
    def is_index(self) -> bool:
        return self.instrument_type == InstrumentType.INDEX
