"""Help and Command Reference Screen for Eudaimonia.

Developer: KJshomay12
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static


class HelpScreen(Widget):
    """Full-screen help manual and keybinding reference."""

    DEFAULT_CSS = """
    HelpScreen {
        layout: vertical;
        height: 1fr;
    }
    #help-scroll {
        height: 1fr;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-scroll"):
            yield Static(id="help-content")

    def on_mount(self) -> None:
        content = self.query_one("#help-content", Static)

        t = Text()
        t.append("EUDAIMONIA - QUAXIOM TRADE TERMINAL\n", style="bold #58a6ff")
        t.append("Developer: KJshomay12 | Version: 0.1.0\n", style="#8b949e")
        t.append("Target Markets: National Stock Exchange (NSE) & Bombay Stock Exchange (BSE)\n\n", style="#8b949e")

        t.append("1. GLOBAL KEYBOARD SHORTCUTS\n", style="bold #3fb950")
        shortcuts = [
            ("F1", "Display this Help and Reference Screen"),
            ("F2", "Market Overview Screen (Indices benchmarks and watchlist quotes)"),
            ("F3", "Options Chain Screen (Calls/Puts, Greeks, PCR, Max Pain)"),
            ("F4", "Detailed Quote & Level-2 5-Depth Order Book"),
            ("F5", "Candlestick Chart (OHLC, Volume, VWAP, Crosshair)"),
            ("F6", "Watchlists Management Screen"),
            ("F7", "Company Intelligence & Wikipedia Summary Screen"),
            (":", "Open interactive command line bar"),
            ("/", "Open interactive command line bar"),
            ("ESC", "Close command bar or return to Overview Screen"),
            ("q", "Quit Eudaimonia application"),
        ]
        for key, desc in shortcuts:
            t.append(f"  {key:<8}", style="bold #79c0ff")
            t.append(f"{desc}\n", style="#c9d1d9")

        t.append("\n2. OPTIONS CHAIN NAVIGATION\n", style="bold #3fb950")
        chain_keys = [
            ("[ and ]", "Cycle through available weekly and monthly expiry dates"),
            ("- and +", "Shrink or expand visible strike range around ATM"),
            ("↑ and ↓", "Scroll through strike ladder"),
        ]
        for key, desc in chain_keys:
            t.append(f"  {key:<8}", style="bold #79c0ff")
            t.append(f"{desc}\n", style="#c9d1d9")

        t.append("\n3. CANDLESTICK CHART SHORTCUTS\n", style="bold #3fb950")
        chart_keys = [
            ("1, 3, 5", "Switch interval to 1-minute, 3-minute, or 5-minute candles"),
            ("f, d", "Switch interval to 15-minute (f) or Daily (d) candles"),
            ("v", "Toggle Volume Weighted Average Price (VWAP) overlay"),
            ("← and →", "Move crosshair cursor across historical bars to inspect OHLCV"),
        ]
        for key, desc in chart_keys:
            t.append(f"  {key:<8}", style="bold #79c0ff")
            t.append(f"{desc}\n", style="#c9d1d9")

        t.append("\n4. INTERACTIVE COMMAND INTERFACE (Press ':' or '/')\n", style="bold #3fb950")
        cmds = [
            ("help", "Open this reference manual"),
            ("status", "Inspect data provider health, data mode, and latency"),
            ("exchanges", "Display supported exchanges (NSE and BSE)"),
            ("instruments", "Display total instruments in catalog"),
            ("watchlist", "Display active watchlist symbols"),
            ("watch <SYMBOL>", "Add symbol to watchlist (e.g. 'watch NSE:INFY')"),
            ("unwatch <SYMBOL>", "Remove symbol from watchlist"),
            ("quote <SYMBOL>", "Open detailed quote and 5-depth order book (e.g. 'quote NSE:RELIANCE')"),
            ("chain [UND]", "Open options chain for underlying (e.g. 'chain NIFTY', 'chain BANKNIFTY')"),
            ("expiry [DATE]", "Switch options chain expiry date"),
            ("chart <SYM> [-i INT]", "Open candlestick chart (e.g. 'chart NSE:NIFTY -i 5m')"),
            ("depth <SYMBOL>", "View Level-2 5-depth order book"),
            ("greeks [UND]", "Focus on options chain analytics and Greeks"),
            ("company <NAME>", "Open Company Data & Wikipedia intelligence (e.g. 'company RELIANCE')"),
            ("history <SYMBOL>", "Load historical bars for analysis"),
            ("settings", "Display active configuration and database path"),
            ("quit", "Exit application"),
        ]
        for cmd, desc in cmds:
            t.append(f"  {cmd:<22}", style="bold #d29922")
            t.append(f"{desc}\n", style="#c9d1d9")

        t.append("\n5. REGULATORY AND COMPLIANCE NOTICE\n", style="bold #f0883e")
        t.append(
            "  This software is designed strictly for personal analytical and educational purposes.\n"
            "  Market data feeds provided via broker APIs (Zerodha Kite, Upstox, Dhan) are governed by\n"
            "  their respective End User License Agreements and SEBI / Exchange regulations.\n"
            "  Commercial redistribution, public broadcasting, or unlicensed sub-licensing of real-time\n"
            "  exchange data is strictly prohibited by NSE and BSE regulations.\n\n",
            style="#8b949e",
        )

        content.update(t)
