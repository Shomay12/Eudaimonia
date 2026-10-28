"""Full-screen interactive Candlestick Chart screen.

Developer: KJshomay12
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from eudaimonia.engine.market_state import MarketStateEngine
from eudaimonia.models.market_data import CandleInterval
from eudaimonia.providers.base import BaseMarketDataProvider
from eudaimonia.ui.components.chart_view import CandlestickChartView


class ChartScreen(Widget):
    """Full-screen Candlestick chart with interval shortcuts and VWAP."""

    DEFAULT_CSS = """
    ChartScreen {
        layout: vertical;
        height: 1fr;
    }
    #chart-controls-bar {
        height: 1;
        background: #161b22;
        color: #8b949e;
        border-bottom: solid #30363d;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        state_engine: MarketStateEngine,
        provider: BaseMarketDataProvider,
        symbol: str = "NSE:NIFTY",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.state_engine = state_engine
        self.provider = provider
        self.symbol = symbol
        self.interval = CandleInterval.M5
        self.chart_view = CandlestickChartView()

    def compose(self) -> ComposeResult:
        yield Static("INTERVAL: [1] 1m  [3] 3m  [5] 5m  [f] 15m  [d] Daily  |  [v] Toggle VWAP  |  [←/→] Move Crosshair", id="chart-controls-bar")
        yield self.chart_view

    def on_mount(self) -> None:
        asyncio.create_task(self.load_data())

    def set_symbol(self, symbol: str) -> None:
        self.symbol = symbol
        asyncio.create_task(self.load_data())

    def set_interval(self, interval: CandleInterval) -> None:
        self.interval = interval
        asyncio.create_task(self.load_data())

    async def load_data(self) -> None:
        """Fetch historical bars and update chart."""
        now = datetime.now(timezone.utc)
        from_time = now - timedelta(hours=8 if self.interval != CandleInterval.D1 else 100)
        historical_bars = await self.provider.fetch_historical_bars(
            symbol=self.symbol,
            interval=self.interval,
            from_time=from_time,
            to_time=now,
        )

        agg = self.state_engine.candle_engine.get_or_create(self.symbol, self.interval)
        if historical_bars:
            agg.add_historical_bars(historical_bars)

        bars = agg.get_all_bars()
        self.chart_view.set_data(self.symbol, self.interval, bars)

    def refresh_chart(self) -> None:
        bars = self.state_engine.candle_engine.get_bars(self.symbol, self.interval)
        self.chart_view.set_data(self.symbol, self.interval, bars)

    def move_cursor_left(self) -> None:
        self.chart_view.move_cursor_left()

    def move_cursor_right(self) -> None:
        self.chart_view.move_cursor_right()

    def toggle_vwap(self) -> None:
        self.chart_view.toggle_vwap()
