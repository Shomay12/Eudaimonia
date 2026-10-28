"""Detailed Market Quote and 5-Depth Order Book Screen.

Developer: KJshomay12
"""

from __future__ import annotations

from decimal import Decimal
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Static

from eudaimonia.engine.market_state import MarketStateEngine
from eudaimonia.models.market_data import MarketDepth


class QuoteScreen(Widget):
    """Detailed Quote and Level-2 5-Depth Order Book."""

    DEFAULT_CSS = """
    QuoteScreen {
        layout: vertical;
        height: 1fr;
    }
    #quote-summary {
        height: 8;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 1;
    }
    #depth-container {
        height: 1fr;
        layout: horizontal;
    }
    #bids-table {
        width: 1fr;
        border-right: solid #30363d;
    }
    #asks-table {
        width: 1fr;
    }
    """

    def __init__(self, state_engine: MarketStateEngine, symbol: str = "NSE:NIFTY", **kwargs) -> None:
        super().__init__(**kwargs)
        self.state_engine = state_engine
        self.symbol = symbol

    def compose(self) -> ComposeResult:
        yield Static(id="quote-summary")
        with Horizontal(id="depth-container"):
            with Vertical():
                yield Static("BID DEPTH (BUY ORDERS)", classes="green bold")
                yield DataTable(id="bids-table")
            with Vertical():
                yield Static("ASK DEPTH (SELL ORDERS)", classes="red bold")
                yield DataTable(id="asks-table")

    def on_mount(self) -> None:
        bids_table = self.query_one("#bids-table", DataTable)
        bids_table.cursor_type = "none"
        bids_table.add_columns("ORDERS", "QTY", "BID PRICE")

        asks_table = self.query_one("#asks-table", DataTable)
        asks_table.cursor_type = "none"
        asks_table.add_columns("ASK PRICE", "QTY", "ORDERS")

        self.refresh_quote()

    def set_symbol(self, symbol: str) -> None:
        self.symbol = symbol
        self.refresh_quote()

    def refresh_quote(self) -> None:
        try:
            summary_widget = self.query_one("#quote-summary", Static)
            bids_table = self.query_one("#bids-table", DataTable)
            asks_table = self.query_one("#asks-table", DataTable)
        except Exception:
            return

        tick = self.state_engine.get_tick(self.symbol)
        inst = self.state_engine.instruments.get_by_symbol(self.symbol)
        depth = self.state_engine.get_depth(self.symbol) or (tick.depth if tick else None)

        # Summary Info
        s = Text()
        s.append(f"SYMBOL: {self.symbol}  ", style="bold #58a6ff")
        if inst:
            s.append(f"[{inst.name}]  EXCHANGE: {inst.exchange.value}  SEGMENT: {inst.segment.value}  LOT: {inst.lot_size}\n", style="#8b949e")
        else:
            s.append("\n")

        if tick:
            chg = tick.change or Decimal("0.0")
            pct = tick.change_pct or Decimal("0.0")
            color = "#3fb950" if chg >= 0 else "#f85149"
            sign = "+" if chg >= 0 else ""

            s.append(f"LTP: {tick.ltp:,.2f}  ", style=f"bold {color}")
            s.append(f"CHG: {sign}{chg:.2f} ({sign}{pct:.2f}%)  ", style=color)
            s.append(f"LTQ: {tick.ltq:,}  ", style="#c9d1d9")
            s.append(f"SPREAD: {tick.spread or 0.0:.2f}  ", style="#8b949e")
            s.append(f"STATUS: {tick.quality.value}\n", style="#3fb950" if tick.quality.value == "OK" else "#f85149")

            s.append(f"OPEN: {tick.open_price or tick.ltp:,.2f}  ", style="#c9d1d9")
            s.append(f"HIGH: {tick.high_price or tick.ltp:,.2f}  ", style="#3fb950")
            s.append(f"LOW: {tick.low_price or tick.ltp:,.2f}  ", style="#f85149")
            s.append(f"PREV CLOSE: {tick.prev_close or tick.ltp:,.2f}  ", style="#8b949e")
            s.append(f"TOTAL VOL: {tick.total_volume:,}  ", style="#58a6ff")
            s.append(f"OI: {tick.open_interest:,} ({tick.oi_change:+d})\n", style="#d29922")
            s.append(f"EXCHANGE TIME: {tick.exchange_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}  RECEIPT: {tick.receipt_time.strftime('%H:%M:%S.%f')[:-3]}", style="#8b949e")
        else:
            s.append(f"Awaiting market quote for {self.symbol}...", style="#8b949e")

        summary_widget.update(s)

        # Depth Tables
        bids_table.clear()
        asks_table.clear()

        if depth:
            for b in depth.bids:
                bids_table.add_row(
                    f"{b.orders:,}",
                    f"{b.quantity:,}",
                    Text(f"{b.price:,.2f}", style="bold #3fb950"),
                )
            for a in depth.asks:
                asks_table.add_row(
                    Text(f"{a.price:,.2f}", style="bold #f85149"),
                    f"{a.quantity:,}",
                    f"{a.orders:,}",
                )

            total_bids = depth.total_bid_qty
            total_asks = depth.total_ask_qty
            bids_table.add_row("TOTAL", Text(f"{total_bids:,}", style="bold #3fb950"), "")
            asks_table.add_row("", Text(f"{total_asks:,}", style="bold #f85149"), "TOTAL")
        else:
            bids_table.add_row("--", "--", "--")
            asks_table.add_row("--", "--", "--")
