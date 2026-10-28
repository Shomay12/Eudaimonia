"""User preferences and UI configuration repository.

Developer: KJshomay12
"""

from __future__ import annotations

import json
import aiosqlite
from typing import Any

from eudaimonia.storage.database import DatabaseManager


class PreferencesRepository:
    """Persists user configuration and terminal display preferences."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

    async def get(self, key: str, default: Any = None) -> Any:
        await self.db_manager.init_schema()
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            async with db.execute("SELECT value FROM user_preferences WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    try:
                        return json.loads(row[0])
                    except Exception:
                        return row[0]
                return default

    async def set(self, key: str, value: Any) -> None:
        await self.db_manager.init_schema()
        val_str = json.dumps(value) if not isinstance(value, str) else value
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, val_str),
            )
            await db.commit()
