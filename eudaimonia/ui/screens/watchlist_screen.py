"""Watchlist management and selection screen.

Developer: KJshomay12
"""

from __future__ import annotations

import asyncio
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Static

from eudaimonia.storage.watchlists import WatchlistRepository


class WatchlistScreen(Widget):
    """Screen for managing and switching watchlists."""

    DEFAULT_CSS = """
    WatchlistScreen {
        layout: vertical;
        height: 1fr;
    }
    #wl-title {
        height: 2;
        background: #161b22;
        color: #58a6ff;
        padding: 0 1;
        border-bottom: solid #30363d;
    }
    #wl-body {
        layout: horizontal;
        height: 1fr;
    }
    #wl-lists-table {
        width: 1fr;
        border-right: solid #30363d;
    }
    #wl-symbols-table {
        width: 1fr;
    }
    """

    def __init__(self, wl_repo: WatchlistRepository | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.wl_repo = wl_repo or WatchlistRepository()
        self.active_wl_name: str = "MAIN"

    def compose(self) -> ComposeResult:
        yield Static("WATCHLISTS MANAGER (Press ENTER to select active watchlist, ESC to exit)", id="wl-title")
        with Horizontal(id="wl-body"):
            with Vertical():
                yield Static("AVAILABLE WATCHLISTS", classes="bold blue")
                yield DataTable(id="wl-lists-table")
            with Vertical():
                yield Static("SYMBOLS IN SELECTED WATCHLIST", classes="bold blue")
                yield DataTable(id="wl-symbols-table")

    def on_mount(self) -> None:
        lists_table = self.query_one("#wl-lists-table", DataTable)
        lists_table.cursor_type = "row"
        lists_table.add_columns("WATCHLIST NAME", "STATUS")

        symbols_table = self.query_one("#wl-symbols-table", DataTable)
        symbols_table.cursor_type = "row"
        symbols_table.add_columns("SYMBOL", "EXCHANGE")

        asyncio.create_task(self.load_watchlists())

    async def load_watchlists(self) -> None:
        lists_table = self.query_one("#wl-lists-table", DataTable)
        symbols_table = self.query_one("#wl-symbols-table", DataTable)

        names = await self.wl_repo.list_watchlists()
        self.active_wl_name = await self.wl_repo.get_or_create_default_watchlist()

        lists_table.clear()
        for name in names:
            is_active = (name == self.active_wl_name)
            st_text = Text("[ACTIVE]", style="bold #3fb950") if is_active else Text("", style="#8b949e")
            lists_table.add_row(name, st_text, key=name)

        symbols = await self.wl_repo.get_watchlist_symbols(self.active_wl_name)
        symbols_table.clear()
        for s in symbols:
            exch = "NSE" if "NSE" in s else ("BSE" if "BSE" in s else "--")
            symbols_table.add_row(s, exch)

    async def select_watchlist(self, name: str) -> None:
        await self.wl_repo.set_active_watchlist(name)
        self.active_wl_name = name
        await self.load_watchlists()
