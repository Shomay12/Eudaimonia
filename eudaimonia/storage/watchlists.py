"""Watchlists storage repository.

Developer: KJshomay12
"""

from __future__ import annotations

import aiosqlite
from pathlib import Path

from eudaimonia.config import settings
from eudaimonia.storage.database import DatabaseManager


class WatchlistRepository:
    """Manages watchlist persistence in SQLite."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

    async def get_or_create_default_watchlist(self) -> str:
        """Ensure at least one default watchlist exists and return its name."""
        await self.db_manager.init_schema()
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            async with db.execute("SELECT name FROM watchlists WHERE is_active = 1 LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    return str(row[0])

            # Check if any watchlist exists
            async with db.execute("SELECT id, name FROM watchlists LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    await db.execute("UPDATE watchlists SET is_active = 1 WHERE id = ?", (row[0],))
                    await db.commit()
                    return str(row[1])

            # Seed default watchlist
            default_name = "MAIN"
            await db.execute("INSERT OR IGNORE INTO watchlists (name, is_active) VALUES (?, 1)", (default_name,))
            async with db.execute("SELECT id FROM watchlists WHERE name = ?", (default_name,)) as c_id:
                row_id = await c_id.fetchone()
                wl_id = row_id[0] if row_id else 1
            default_symbols = [
                "NSE:NIFTY",
                "NSE:BANKNIFTY",
                "BSE:SENSEX",
                "NSE:RELIANCE",
                "NSE:HDFCBANK",
                "NSE:TCS",
                "NSE:INFY",
                "NSE:ICICIBANK",
            ]
            for idx, sym in enumerate(default_symbols):
                await db.execute(
                    "INSERT OR IGNORE INTO watchlist_items (watchlist_id, symbol, sort_order) VALUES (?, ?, ?)",
                    (wl_id, sym, idx),
                )
            await db.commit()
            return default_name

    async def list_watchlists(self) -> list[str]:
        await self.db_manager.init_schema()
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            async with db.execute("SELECT name FROM watchlists ORDER BY name ASC") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_watchlist_symbols(self, watchlist_name: str) -> list[str]:
        await self.db_manager.init_schema()
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            async with db.execute(
                """
                SELECT item.symbol
                FROM watchlist_items item
                JOIN watchlists wl ON item.watchlist_id = wl.id
                WHERE wl.name = ?
                ORDER BY item.sort_order ASC, item.id ASC
                """,
                (watchlist_name,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def add_symbol(self, watchlist_name: str, symbol: str) -> bool:
        await self.db_manager.init_schema()
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            async with db.execute("SELECT id FROM watchlists WHERE name = ?", (watchlist_name,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    # Create watchlist if doesn't exist
                    c = await db.execute("INSERT INTO watchlists (name, is_active) VALUES (?, 0)", (watchlist_name,))
                    wl_id = c.lastrowid
                else:
                    wl_id = row[0]

            try:
                await db.execute(
                    "INSERT INTO watchlist_items (watchlist_id, symbol) VALUES (?, ?)",
                    (wl_id, symbol.upper()),
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def remove_symbol(self, watchlist_name: str, symbol: str) -> bool:
        await self.db_manager.init_schema()
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            async with db.execute(
                """
                DELETE FROM watchlist_items
                WHERE watchlist_id = (SELECT id FROM watchlists WHERE name = ?)
                AND symbol = ?
                """,
                (watchlist_name, symbol.upper()),
            ) as cursor:
                await db.commit()
                return cursor.rowcount > 0

    async def set_active_watchlist(self, watchlist_name: str) -> bool:
        await self.db_manager.init_schema()
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            await db.execute("UPDATE watchlists SET is_active = 0")
            cursor = await db.execute("UPDATE watchlists SET is_active = 1 WHERE name = ?", (watchlist_name,))
            await db.commit()
            return cursor.rowcount > 0
