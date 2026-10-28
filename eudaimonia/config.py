"""Application configuration management for Eudaimonia.

Developer: KJshomay12
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load .env if present in project base directory only
env_path = BASE_DIR / ".env"
if env_path.is_file():
    load_dotenv(dotenv_path=env_path)

DataModeType = Literal["MOCK", "LIVE", "HISTORICAL", "DELAYED"]
ExchangeType = Literal["NSE", "BSE"]


class Settings:
    """Application-wide runtime settings."""

    # Project metadata
    PROJECT_NAME: str = "Eudaimonia"
    DEVELOPER: str = "KJshomay12"
    VERSION: str = "0.1.0"

    # Runtime Data Mode
    DATA_MODE: DataModeType = os.getenv("EUDAIMONIA_DATA_MODE", "MOCK").upper()  # type: ignore

    # Provider: 'mock', 'kite', 'upstox', 'dhan'
    PROVIDER_NAME: str = os.getenv("EUDAIMONIA_PROVIDER", "mock").lower()

    # Market Defaults
    DEFAULT_EXCHANGE: ExchangeType = os.getenv("EUDAIMONIA_DEFAULT_EXCHANGE", "NSE").upper()  # type: ignore
    DEFAULT_UNDERLYING: str = os.getenv("EUDAIMONIA_DEFAULT_UNDERLYING", "NIFTY").upper()

    # Market Timezone
    TIMEZONE_NAME: str = os.getenv("EUDAIMONIA_TIMEZONE", "Asia/Kolkata")
    TIMEZONE: ZoneInfo = ZoneInfo(TIMEZONE_NAME)

    # Risk-free rate (6.5% standard for Indian 91-day T-Bills)
    RISK_FREE_RATE: float = float(os.getenv("EUDAIMONIA_RISK_FREE_RATE", "0.065"))

    # Staleness & Health thresholds
    STALE_THRESHOLD_SECONDS: float = float(os.getenv("EUDAIMONIA_STALE_THRESHOLD_SECONDS", "5.0"))
    UI_REFRESH_HZ: int = int(os.getenv("EUDAIMONIA_UI_FPS", "4"))

    # Persistence
    DB_PATH: Path = Path(os.getenv("EUDAIMONIA_DB_PATH", str(DATA_DIR / "eudaimonia.db")))

    # Credentials (Accessed securely via os.getenv, never hardcoded or logged)
    KITE_API_KEY: str | None = os.getenv("KITE_API_KEY")
    KITE_API_SECRET: str | None = os.getenv("KITE_API_SECRET")
    KITE_ACCESS_TOKEN: str | None = os.getenv("KITE_ACCESS_TOKEN")

    UPSTOX_API_KEY: str | None = os.getenv("UPSTOX_API_KEY")
    UPSTOX_API_SECRET: str | None = os.getenv("UPSTOX_API_SECRET")
    UPSTOX_ACCESS_TOKEN: str | None = os.getenv("UPSTOX_ACCESS_TOKEN")

    DHAN_CLIENT_ID: str | None = os.getenv("DHAN_CLIENT_ID")
    DHAN_ACCESS_TOKEN: str | None = os.getenv("DHAN_ACCESS_TOKEN")


settings = Settings()
