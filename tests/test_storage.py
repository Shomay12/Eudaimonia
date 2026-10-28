"""Tests for SQLite persistence, watchlists, and user preferences.

Developer: KJshomay12
"""

from __future__ import annotations

import pytest

from eudaimonia.storage.database import DatabaseManager
from eudaimonia.storage.preferences import PreferencesRepository
from eudaimonia.storage.watchlists import WatchlistRepository


@pytest.mark.asyncio
async def test_watchlist_repository():
    db_mgr = DatabaseManager()
    repo = WatchlistRepository(db_manager=db_mgr)

    # 1. Seeding default watchlist
    default_wl = await repo.get_or_create_default_watchlist()
    assert default_wl == "MAIN"

    symbols = await repo.get_watchlist_symbols(default_wl)
    assert len(symbols) >= 5
    assert "NSE:NIFTY" in symbols

    # 2. Add symbol
    added = await repo.add_symbol("MAIN", "NSE:TATAPOWER")
    assert added is True

    symbols_after = await repo.get_watchlist_symbols("MAIN")
    assert "NSE:TATAPOWER" in symbols_after

    # 3. Prevent duplicate addition
    added_dup = await repo.add_symbol("MAIN", "NSE:TATAPOWER")
    assert added_dup is False

    # 4. Remove symbol
    removed = await repo.remove_symbol("MAIN", "NSE:TATAPOWER")
    assert removed is True
    symbols_final = await repo.get_watchlist_symbols("MAIN")
    assert "NSE:TATAPOWER" not in symbols_final


@pytest.mark.asyncio
async def test_preferences_repository():
    db_mgr = DatabaseManager()
    repo = PreferencesRepository(db_manager=db_mgr)

    # Key doesn't exist
    val = await repo.get("nonexistent_key", default="fallback")
    assert val == "fallback"

    # Set structured preference
    await repo.set("active_chain_config", {"underlying": "BANKNIFTY", "strike_window": 20})
    read_val = await repo.get("active_chain_config")

    assert isinstance(read_val, dict)
    assert read_val["underlying"] == "BANKNIFTY"
    assert read_val["strike_window"] == 20
