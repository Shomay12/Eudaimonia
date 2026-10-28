"""Market Overview screen displaying indices and active watchlist quotes.

Developer: KJshomay12
"""

from __future__ import annotations

from decimal import Decimal
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Static

from eudaimonia.engine.market_state import MarketStateEngine
from eudaimonia.models.market_data import MarketTick


class OverviewScreen(Widget):
    """Primary market overview and watchlist quotes screen."""

    DEFAULT_CSS = """
    OverviewScreen {
        layout: vertical;
        height: 1fr;
    }
    #overview-section-title {
        height: 1;
        background: #161b22;
        color: #58a6ff;
        text-style: bold;
        padding: 0 1;
    }
    #indices-table {
        height: 7;
        margin-bottom: 1;
    }
    #watchlist-table {
        height: 1fr;
    }
    """

    def __init__(self, state_engine: MarketStateEngine, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state_engine = state_engine
        self.watchlist_symbols: list[str] = []

    def compose(self) -> ComposeResult:
        yield Static("INDEX BENCHMARKS (NSE / BSE)", id="overview-section-title")
        yield DataTable(id="indices-table")
        yield Static("ACTIVE WATCHLIST QUOTES (Press ENTER for Quote/Depth, 'c' for Chart, 'o' for Options Chain)", id="watchlist-section-title")
        yield DataTable(id="watchlist-table")

    def on_mount(self) -> None:
        # Setup Indices Table
        idx_table = self.query_one("#indices-table", DataTable)
        idx_table.cursor_type = "row"
        idx_table.add_columns("EXCHANGE", "SYMBOL", "NAME", "LTP", "CHANGE", "%CHG", "HIGH", "LOW", "VOLUME")

        # Setup Watchlist Table
        wl_table = self.query_one("#watchlist-table", DataTable)
        wl_table.cursor_type = "row"
        wl_table.add_columns("SYMBOL", "LTP", "CHANGE", "%CHG", "BID", "ASK", "SPREAD", "VOLUME", "STATUS")

        self.refresh_data()

    def set_watchlist_symbols(self, symbols: list[str]) -> None:
        self.watchlist_symbols = symbols
        self.refresh_data()

    def refresh_data(self) -> None:
        """Update tables with latest ticks."""
        try:
            idx_table = self.query_one("#indices-table", DataTable)
            wl_table = self.query_one("#watchlist-table", DataTable)
        except Exception:
            return

        # 1. Populate Indices Table
        idx_table.clear()
        indices_tracked = [
            ("NSE", "NSE:NIFTY", "Nifty 50 Index"),
            ("NSE", "NSE:BANKNIFTY", "Nifty Bank Index"),
            ("NSE", "NSE:FINNIFTY", "Nifty Fin Services"),
            ("BSE", "BSE:SENSEX", "BSE SENSEX Index"),
            ("BSE", "BSE:BANKEX", "BSE BANKEX Index"),
        ]

        for exch, sym, name in indices_tracked:
            tick = self.state_engine.get_tick(sym)
            if tick:
                chg = tick.change or Decimal("0.0")
                pct = tick.change_pct or Decimal("0.0")
                color = "#3fb950" if chg >= 0 else "#f85149"
                sign = "+" if chg >= 0 else ""

                idx_table.add_row(
                    exch,
                    sym.split(":")[-1],
                    name,
                    Text(f"{tick.ltp:,.2f}", style=f"bold {color}"),
                    Text(f"{sign}{chg:.2f}", style=color),
                    Text(f"{sign}{pct:.2f}%", style=color),
                    f"{tick.high_price or tick.ltp:,.2f}",
                    f"{tick.low_price or tick.ltp:,.2f}",
                    f"{tick.total_volume:,}",
                    key=sym,
                )
            else:
                idx_table.add_row(exch, sym.split(":")[-1], name, "--", "--", "--", "--", "--", "--", key=sym)

        # 2. Populate Watchlist Table
        wl_table.clear()
        symbols = self.watchlist_symbols or [
            "NSE:NIFTY",
            "NSE:BANKNIFTY",
            "BSE:SENSEX",
            "NSE:RELIANCE",
            "NSE:HDFCBANK",
            "NSE:TCS",
            "NSE:INFY",
            "NSE:ICICIBANK",
        ]

        for sym in symbols:
            tick = self.state_engine.get_tick(sym)
            if tick:
                chg = tick.change or Decimal("0.0")
                pct = tick.change_pct or Decimal("0.0")
                color = "#3fb950" if chg >= 0 else "#f85149"
                sign = "+" if chg >= 0 else ""
                bid_str = f"{tick.best_bid:,.2f}" if tick.best_bid else "--"
                ask_str = f"{tick.best_ask:,.2f}" if tick.best_ask else "--"
                spread_str = f"{tick.spread:.2f}" if tick.spread is not None else "--"

                status_style = "#3fb950" if tick.quality.value == "OK" else "#f85149"

                wl_table.add_row(
                    Text(sym, style="bold #c9d1d9"),
                    Text(f"{tick.ltp:,.2f}", style=f"bold {color}"),
                    Text(f"{sign}{chg:.2f}", style=color),
                    Text(f"{sign}{pct:.2f}%", style=color),
                    Text(bid_str, style="#3fb950"),
                    Text(ask_str, style="#f85149"),
                    spread_str,
                    f"{tick.total_volume:,}",
                    Text(tick.quality.value, style=status_style),
                    key=sym,
                )
            else:
                wl_table.add_row(Text(sym, style="#8b949e"), "--", "--", "--", "--", "--", "--", "--", "PENDING", key=sym)

    def get_selected_symbol(self) -> str | None:
        try:
            table = self.query_one("#watchlist-table", DataTable)
            if table.cursor_row is not None and table.cursor_row < len(table.rows):
                row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
                return str(row_key.value)
        except Exception:
            pass
        return None
