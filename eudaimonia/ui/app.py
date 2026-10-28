"""Main Textual Application for Eudaimonia (Quaxiom Trade Terminal).

Developer: KJshomay12
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding

from eudaimonia.config import settings
from eudaimonia.engine.candle_engine import CandleEngine
from eudaimonia.engine.data_quality import DataQualityMonitor
from eudaimonia.engine.instrument_master import InstrumentMaster
from eudaimonia.engine.market_state import MarketStateEngine
from eudaimonia.models.events import DataMode, FeedStatus
from eudaimonia.models.market_data import CandleInterval, MarketDepth, MarketTick
from eudaimonia.providers.base import BaseMarketDataProvider
from eudaimonia.providers.registry import get_market_data_provider
from eudaimonia.storage.watchlists import WatchlistRepository
from eudaimonia.ui.components.command_line import CommandLine, CommandSubmitted
from eudaimonia.ui.components.header_bar import HeaderBar
from eudaimonia.ui.components.status_footer import StatusFooter
from eudaimonia.ui.screens.chart_screen import ChartScreen
from eudaimonia.ui.screens.chain_screen import OptionsChainScreen
from eudaimonia.ui.screens.help_screen import HelpScreen
from eudaimonia.ui.screens.overview_screen import OverviewScreen
from eudaimonia.ui.screens.quote_screen import QuoteScreen
from eudaimonia.ui.screens.watchlist_screen import WatchlistScreen


class EudaimoniaApp(App):
    """Eudaimonia Professional Indian Market Data & Options Terminal."""

    TITLE = "EUDAIMONIA"
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    BINDINGS = [
        Binding("f1", "switch_screen('help')", "Help", show=True),
        Binding("f2", "switch_screen('overview')", "Overview", show=True),
        Binding("f3", "switch_screen('chain')", "Chain", show=True),
        Binding("f4", "switch_screen('quote')", "Quote", show=True),
        Binding("f5", "switch_screen('chart')", "Chart", show=True),
        Binding("f6", "switch_screen('watchlist')", "Watchlists", show=True),
        Binding("colon", "open_cmd", "Cmd", show=True),
        Binding("slash", "open_cmd", "Cmd", show=False),
        Binding("escape", "handle_escape", "Back/Cancel", show=True),
        Binding("q", "quit_app", "Quit", show=True),
        # Contextual shortcuts
        Binding("left_square_bracket", "chain_prev_expiry", "Prev Expiry", show=False),
        Binding("right_square_bracket", "chain_next_expiry", "Next Expiry", show=False),
        Binding("minus", "chain_zoom_in", "Zoom In Strikes", show=False),
        Binding("plus", "chain_zoom_out", "Zoom Out Strikes", show=False),
        Binding("equals", "chain_zoom_out", "Zoom Out Strikes", show=False),
        # Chart controls
        Binding("1", "chart_m1", "1m Chart", show=False),
        Binding("3", "chart_m3", "3m Chart", show=False),
        Binding("5", "chart_m5", "5m Chart", show=False),
        Binding("f", "chart_m15", "15m Chart", show=False),
        Binding("d", "chart_d1", "1d Chart", show=False),
        Binding("v", "chart_toggle_vwap", "Toggle VWAP", show=False),
        Binding("left", "chart_cursor_left", "Crosshair Left", show=False),
        Binding("right", "chart_cursor_right", "Crosshair Right", show=False),
    ]

    def __init__(self, provider: BaseMarketDataProvider | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.provider = provider or get_market_data_provider()
        self.instruments = InstrumentMaster()
        self.candle_engine = CandleEngine()
        self.quality_monitor = DataQualityMonitor()
        self.state_engine = MarketStateEngine(
            instrument_master=self.instruments,
            candle_engine=self.candle_engine,
            quality_monitor=self.quality_monitor,
        )
        self.wl_repo = WatchlistRepository()

        # Components
        self.header_bar = HeaderBar()
        self.status_footer = StatusFooter()
        self.cmd_line = CommandLine()

        # Screens
        self.overview_screen = OverviewScreen(state_engine=self.state_engine)
        self.chain_screen = OptionsChainScreen(state_engine=self.state_engine)
        self.quote_screen = QuoteScreen(state_engine=self.state_engine)
        self.chart_screen = ChartScreen(state_engine=self.state_engine, provider=self.provider)
        self.watchlist_screen = WatchlistScreen(wl_repo=self.wl_repo)
        self.help_screen = HelpScreen()

        self.current_screen_name = "overview"

    def compose(self) -> ComposeResult:
        self.chain_screen.display = False
        self.quote_screen.display = False
        self.chart_screen.display = False
        self.watchlist_screen.display = False
        self.help_screen.display = False

        yield self.header_bar
        yield self.overview_screen
        yield self.chain_screen
        yield self.quote_screen
        yield self.chart_screen
        yield self.watchlist_screen
        yield self.help_screen
        yield self.cmd_line
        yield self.status_footer

    async def on_mount(self) -> None:
        """Initialize engine, load instruments, seed watchlists, connect provider."""
        # 1. Load active watchlist
        default_wl = await self.wl_repo.get_or_create_default_watchlist()
        symbols = await self.wl_repo.get_watchlist_symbols(default_wl)
        self.overview_screen.set_watchlist_symbols(symbols)

        # 2. Fetch master instruments from provider
        insts = await self.provider.fetch_instruments()
        self.instruments.load_instruments(insts)

        # 3. Setup provider callbacks
        self.provider.register_on_tick(self._on_tick_received)
        self.provider.register_on_depth(self._on_depth_received)
        self.provider.register_on_status(self._on_status_received)

        # 4. Connect provider
        await self.provider.connect()

        # 5. Subscribe to index benchmarks and watchlist symbols
        benchmark_symbols = ["NSE:NIFTY", "NSE:BANKNIFTY", "BSE:SENSEX", "NSE:FINNIFTY", "BSE:BANKEX"]
        all_to_sub = list(set(benchmark_symbols + symbols))
        await self.provider.subscribe_quotes(all_to_sub)
        await self.provider.subscribe_depth(["NSE:NIFTY", "NSE:BANKNIFTY", "NSE:RELIANCE"])

        # 6. Start UI refresh loop
        self.set_interval(1.0 / max(1, settings.UI_REFRESH_HZ), self._tick_ui_refresh)

    async def _on_tick_received(self, tick: MarketTick) -> None:
        self.state_engine.on_market_tick(tick)

    async def _on_depth_received(self, symbol: str, depth: MarketDepth) -> None:
        self.state_engine.on_market_depth(symbol, depth)

    async def _on_status_received(self, status: FeedStatus) -> None:
        self.state_engine.update_feed_status(status)
        self.header_bar.update_status(status)

    def _tick_ui_refresh(self) -> None:
        """Periodic refresh of the active screen."""
        self.header_bar.update_ticks(self.state_engine.ticks)

        if self.current_screen_name == "overview":
            self.overview_screen.refresh_data()
        elif self.current_screen_name == "chain":
            self.chain_screen.refresh_chain()
        elif self.current_screen_name == "quote":
            self.quote_screen.refresh_quote()
        elif self.current_screen_name == "chart":
            self.chart_screen.refresh_chart()

    def action_switch_screen(self, screen_name: str) -> None:
        """Switch active display screen."""
        if self.current_screen_name == screen_name:
            return

        # Hide current screen widget
        old_screen = self._get_screen_widget(self.current_screen_name)
        if old_screen:
            old_screen.display = False

        # Show new screen widget
        self.current_screen_name = screen_name
        new_screen = self._get_screen_widget(screen_name)
        if new_screen:
            new_screen.display = True
            new_screen.focus()

        # Update footer context
        ctx = self.state_engine.active_underlying
        if screen_name == "quote":
            ctx = self.quote_screen.symbol
        elif screen_name == "chart":
            ctx = f"{self.chart_screen.symbol} [{self.chart_screen.interval.value}]"
        self.status_footer.update_context(ctx)

    def _get_screen_widget(self, name: str):
        mapping = {
            "overview": self.overview_screen,
            "chain": self.chain_screen,
            "quote": self.quote_screen,
            "chart": self.chart_screen,
            "watchlist": self.watchlist_screen,
            "help": self.help_screen,
        }
        return mapping.get(name)

    def action_open_cmd(self) -> None:
        self.cmd_line.open_prompt()

    def action_handle_escape(self) -> None:
        if self.cmd_line.has_class("visible"):
            self.cmd_line.close_prompt()
        elif self.current_screen_name != "overview":
            self.action_switch_screen("overview")

    def action_quit_app(self) -> None:
        self.exit()

    # Options Chain Shortcuts
    def action_chain_next_expiry(self) -> None:
        if self.current_screen_name == "chain":
            self.chain_screen.next_expiry()

    def action_chain_prev_expiry(self) -> None:
        if self.current_screen_name == "chain":
            self.chain_screen.prev_expiry()

    def action_chain_zoom_in(self) -> None:
        if self.current_screen_name == "chain":
            self.chain_screen.zoom_in_strikes()

    def action_chain_zoom_out(self) -> None:
        if self.current_screen_name == "chain":
            self.chain_screen.zoom_out_strikes()

    # Chart Shortcuts
    def action_chart_m1(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.set_interval(CandleInterval.M1)

    def action_chart_m3(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.set_interval(CandleInterval.M3)

    def action_chart_m5(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.set_interval(CandleInterval.M5)

    def action_chart_m15(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.set_interval(CandleInterval.M15)

    def action_chart_d1(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.set_interval(CandleInterval.D1)

    def action_chart_toggle_vwap(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.toggle_vwap()

    def action_chart_cursor_left(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.move_cursor_left()

    def action_chart_cursor_right(self) -> None:
        if self.current_screen_name == "chart":
            self.chart_screen.move_cursor_right()

    # Command Handling
    async def on_command_submitted(self, message: CommandSubmitted) -> None:
        self.cmd_line.close_prompt()
        cmd = message.command
        args = message.args

        if cmd == "help":
            self.action_switch_screen("help")

        elif cmd == "status":
            self.action_switch_screen("overview")

        elif cmd in ("chain", "greeks"):
            if args:
                und = args[0].upper()
                self.state_engine.active_underlying = und
                self.chain_screen.set_underlying(und)
            self.action_switch_screen("chain")

        elif cmd in ("quote", "depth"):
            if args:
                sym = args[0].upper()
                if ":" not in sym:
                    sym = f"NSE:{sym}"
                self.quote_screen.set_symbol(sym)
                await self.provider.subscribe_quotes([sym])
                await self.provider.subscribe_depth([sym])
            self.action_switch_screen("quote")

        elif cmd in ("chart", "history"):
            if args:
                sym = args[0].upper()
                if ":" not in sym:
                    sym = f"NSE:{sym}"
                self.chart_screen.set_symbol(sym)
                await self.provider.subscribe_quotes([sym])
            # Check interval argument
            for i, arg in enumerate(args):
                if arg in ("-i", "--interval") and i + 1 < len(args):
                    int_str = args[i + 1].lower()
                    for ci in CandleInterval:
                        if ci.value == int_str:
                            self.chart_screen.set_interval(ci)
            self.action_switch_screen("chart")

        elif cmd == "watch":
            if args:
                sym = args[0].upper()
                if ":" not in sym:
                    sym = f"NSE:{sym}"
                default_wl = await self.wl_repo.get_or_create_default_watchlist()
                await self.wl_repo.add_symbol(default_wl, sym)
                symbols = await self.wl_repo.get_watchlist_symbols(default_wl)
                self.overview_screen.set_watchlist_symbols(symbols)
                await self.provider.subscribe_quotes([sym])
            self.action_switch_screen("overview")

        elif cmd == "unwatch":
            if args:
                sym = args[0].upper()
                if ":" not in sym:
                    sym = f"NSE:{sym}"
                default_wl = await self.wl_repo.get_or_create_default_watchlist()
                await self.wl_repo.remove_symbol(default_wl, sym)
                symbols = await self.wl_repo.get_watchlist_symbols(default_wl)
                self.overview_screen.set_watchlist_symbols(symbols)
            self.action_switch_screen("overview")

        elif cmd == "watchlist":
            self.action_switch_screen("watchlist")

        elif cmd == "expiry":
            if self.current_screen_name != "chain":
                self.action_switch_screen("chain")
            self.chain_screen.next_expiry()
