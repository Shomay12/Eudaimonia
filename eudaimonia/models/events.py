"""Event and connection models for Eudaimonia.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class ConnectionState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class DataMode(str, Enum):
    MOCK = "MOCK"
    LIVE = "LIVE"
    HISTORICAL = "HISTORICAL"
    DELAYED = "DELAYED"


class DataQualityStatus(str, Enum):
    OK = "OK"
    STALE = "STALE"
    SEQUENCE_GAP = "SEQUENCE_GAP"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    SUSPECT_PRICE = "SUSPECT_PRICE"
    INCOMPLETE = "INCOMPLETE"


class FeedStatus(BaseModel):
    """Feed status information displayed on terminal header."""

    model_config = ConfigDict(frozen=False)

    provider_name: str
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    data_mode: DataMode = DataMode.MOCK
    last_event_time: datetime | None = None
    last_receipt_time: datetime | None = None
    subscribed_count: int = 0
    latency_ms: float = 0.0
    is_stale: bool = False
    error_message: str | None = None


class DataQualityEvent(BaseModel):
    """Loggable data quality incident."""

    timestamp: datetime
    symbol: str
    status: DataQualityStatus
    message: str
    received_timestamp: datetime
    exchange_timestamp: datetime | None = None
    details: dict[str, str | int | float] = Field(default_factory=dict)
