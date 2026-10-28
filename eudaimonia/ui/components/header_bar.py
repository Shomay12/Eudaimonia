"""Terminal Header Bar displaying market indices, feed status, and clock.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from eudaimonia.config import settings
from eudaimonia.models.events import ConnectionState, DataMode, FeedStatus
from eudaimonia.models.market_data import MarketTick

IST_ZONE = ZoneInfo("Asia/Kolkata")


class HeaderBar(Widget):
    """Top-level market overview and connection status bar."""

    DEFAULT_CSS = """
    HeaderBar {
        height: 3;
        dock: top;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(id="header-bar", **kwargs)
        self.indices_ticks: dict[str, MarketTick] = {}
        self.feed_status: FeedStatus = FeedStatus(
            provider_name=settings.PROVIDER_NAME,
            connection_state=ConnectionState.DISCONNECTED,
            data_mode=DataMode(settings.DATA_MODE),
        )

    def compose(self) -> ComposeResult:
        yield Static(id="header-line-1")
        yield Static(id="header-line-2")

    def update_ticks(self, ticks: dict[str, MarketTick]) -> None:
        """Update tracked index ticks."""
        for sym in ("NSE:NIFTY", "NSE:BANKNIFTY", "BSE:SENSEX", "NSE:FINNIFTY"):
            if sym in ticks:
                self.indices_ticks[sym] = ticks[sym]
        self.refresh_display()

    def update_status(self, status: FeedStatus) -> None:
        self.feed_status = status
        self.refresh_display()

    def refresh_display(self) -> None:
        try:
            line1_widget = self.query_one("#header-line-1", Static)
            line2_widget = self.query_one("#header-line-2", Static)
        except Exception:
            return

        now_ist = datetime.now(IST_ZONE).strftime("%H:%M:%S IST")

        # Top line: Title & Indices
        t1 = Text()
        t1.append("EUDAIMONIA ", style="bold #58a6ff")
        t1.append("[KJshomay12]  ", style="#8b949e")

        # Indices ticker
        tracked = [
            ("NSE:NIFTY", "NIFTY"),
            ("NSE:BANKNIFTY", "BNIFTY"),
            ("BSE:SENSEX", "SENSEX"),
        ]

        for full_sym, short_name in tracked:
            tick = self.indices_ticks.get(full_sym)
            t1.append(f"{short_name}: ", style="bold #c9d1d9")
            if tick:
                chg = tick.change or 0.0
                pct = tick.change_pct or 0.0
                color = "#3fb950" if chg >= 0 else "#f85149"
                sign = "+" if chg >= 0 else ""
                t1.append(f"{tick.ltp:,.2f} ", style=f"bold {color}")
                t1.append(f"{sign}{chg:.2f} ({sign}{pct:.2f}%)  ", style=color)
            else:
                t1.append("--  ", style="#8b949e")

        # Line 2: Feed Health, Data Mode, Latency, Clock
        t2 = Text()
        mode_style = "bold #d29922" if self.feed_status.data_mode == DataMode.MOCK else "bold #3fb950"
        t2.append(f"FEED: [{self.feed_status.data_mode.value}] ", style=mode_style)
        t2.append(f"PROVIDER: {self.feed_status.provider_name} ", style="#c9d1d9")

        # State
        st = self.feed_status.connection_state
        if st == ConnectionState.CONNECTED:
            st_style = "bold #3fb950"
        elif st in (ConnectionState.CONNECTING, ConnectionState.RECONNECTING):
            st_style = "bold #d29922"
        else:
            st_style = "bold #f85149"

        t2.append(f"STATE: {st.value} ", style=st_style)
        t2.append(f"SUBS: {self.feed_status.subscribed_count} ", style="#8b949e")
        t2.append(f"LATENCY: {self.feed_status.latency_ms:.1f}ms ", style="#58a6ff")

        if self.feed_status.is_stale:
            t2.append("[FEED STALE] ", style="bold #f85149")

        t2.append(f" | {now_ist}", style="#8b949e")

        line1_widget.update(t1)
        line2_widget.update(t2)
