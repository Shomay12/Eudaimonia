"""SQLite Database manager using aiosqlite for persistence.

Developer: KJshomay12
"""

from __future__ import annotations

import aiosqlite
from pathlib import Path

from eudaimonia.config import settings


class DatabaseManager:
    """Manages SQLite connection lifecycle and schema migrations."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init_schema(self) -> None:
        """Create tables for preferences, watchlists, and items if not existing."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS watchlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    is_active INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS watchlist_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watchlist_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
                    UNIQUE(watchlist_id, symbol)
                );
            """)

            await db.commit()
