"""Terminal Candlestick and Volume Charting Component.

Developer: KJshomay12
"""

from __future__ import annotations

from decimal import Decimal
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from eudaimonia.models.market_data import CandleBar, CandleInterval


class CandlestickChartView(Widget):
    """Terminal ASCII/Unicode Candlestick & Volume Chart with Crosshair."""

    DEFAULT_CSS = """
    CandlestickChartView {
        height: 1fr;
        background: #0d1117;
        color: #c9d1d9;
        padding: 0 1;
    }
    #chart-hud {
        height: 2;
        background: #161b22;
        border-bottom: solid #21262d;
        padding: 0 1;
    }
    #chart-body {
        height: 1fr;
    }
    """

    VOLUME_BLOCKS = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.symbol: str = "NSE:NIFTY"
        self.interval: CandleInterval = CandleInterval.M5
        self.bars: list[CandleBar] = []
        self.cursor_idx: int = -1  # -1 means latest bar
        self.show_vwap: bool = True

    def compose(self) -> ComposeResult:
        yield Static(id="chart-hud")
        yield Static(id="chart-body")

    def set_data(self, symbol: str, interval: CandleInterval, bars: list[CandleBar]) -> None:
        self.symbol = symbol
        self.interval = interval
        self.bars = bars
        if self.cursor_idx >= len(bars) or self.cursor_idx == -1:
            self.cursor_idx = max(0, len(bars) - 1)
        self.render_chart()

    def move_cursor_left(self) -> None:
        if self.bars and self.cursor_idx > 0:
            self.cursor_idx -= 1
            self.render_chart()

    def move_cursor_right(self) -> None:
        if self.bars and self.cursor_idx < len(self.bars) - 1:
            self.cursor_idx += 1
            self.render_chart()

    def toggle_vwap(self) -> None:
        self.show_vwap = not self.show_vwap
        self.render_chart()

    def render_chart(self) -> None:
        try:
            hud_widget = self.query_one("#chart-hud", Static)
            body_widget = self.query_one("#chart-body", Static)
        except Exception:
            return

        if not self.bars:
            hud_widget.update(Text(f"CHART: {self.symbol} [{self.interval.value}] - No bar data", style="#8b949e"))
            body_widget.update(Text("Awaiting market data...", style="#8b949e"))
            return

        active_bar = self.bars[self.cursor_idx] if 0 <= self.cursor_idx < len(self.bars) else self.bars[-1]
        time_str = active_bar.timestamp.strftime("%Y-%m-%d %H:%M")
        chg = active_bar.close - active_bar.open
        pct = (chg / active_bar.open) * Decimal("100") if active_bar.open > 0 else Decimal("0")
        color = "#3fb950" if chg >= 0 else "#f85149"
        sign = "+" if chg >= 0 else ""

        # HUD Line
        hud = Text()
        hud.append(f"{self.symbol} ", style="bold #58a6ff")
        hud.append(f"[{self.interval.value}]  ", style="bold #d29922")
        hud.append(f"TIME: {time_str}  ", style="#c9d1d9")
        hud.append(f"O: {active_bar.open:,.2f}  ", style="#c9d1d9")
        hud.append(f"H: {active_bar.high:,.2f}  ", style="#c9d1d9")
        hud.append(f"L: {active_bar.low:,.2f}  ", style="#c9d1d9")
        hud.append(f"C: {active_bar.close:,.2f}  ", style=f"bold {color}")
        hud.append(f"CHG: {sign}{chg:.2f} ({sign}{pct:.2f}%)  ", style=color)
        hud.append(f"VOL: {active_bar.volume:,}  ", style="#58a6ff")
        if self.show_vwap and active_bar.vwap:
            hud.append(f"VWAP: {active_bar.vwap:,.2f}", style="#d29922")

        hud_widget.update(hud)

        # Body Dimensions
        # Estimate usable height and width
        total_height = max(15, self.size.height - 4) if self.size.height > 6 else 18
        price_height = int(total_height * 0.75)
        volume_height = max(3, total_height - price_height)
        scale_width = 12
        available_width = max(30, self.size.width - scale_width - 2) if self.size.width > 40 else 70

        # Bar width: 2 chars per candle (1 wick/body + 1 space)
        bar_width = 2
        max_visible_bars = max(5, available_width // bar_width)
        visible_bars = self.bars[-max_visible_bars:]
        if not visible_bars:
            return

        min_price = float(min(b.low for b in visible_bars))
        max_price = float(max(b.high for b in visible_bars))
        if max_price == min_price:
            max_price += 1.0
            min_price -= 1.0
        price_range = max_price - min_price

        max_volume = max((b.volume for b in visible_bars), default=1)
        if max_volume == 0:
            max_volume = 1

        # Build ASCII / Rich Canvas line by line
        chart_text = Text()

        # 1. Price Rows
        for row in range(price_height):
            # Calculate price for this row (top row is max_price)
            row_price = max_price - (row / (price_height - 1)) * price_range
            row_text = Text()

            # Plot each candle
            for i, bar in enumerate(visible_bars):
                is_cursor = (i == (len(visible_bars) - (len(self.bars) - self.cursor_idx)))
                is_green = bar.close >= bar.open
                candle_color = "#3fb950" if is_green else "#f85149"

                b_high = float(bar.high)
                b_low = float(bar.low)
                b_top = float(max(bar.open, bar.close))
                b_bottom = float(min(bar.open, bar.close))

                # Check position of row
                candle_char = " "
                char_style = candle_color

                # Does row intersect wick or body?
                high_y = int(round((max_price - b_high) / price_range * (price_height - 1)))
                low_y = int(round((max_price - b_low) / price_range * (price_height - 1)))
                top_y = int(round((max_price - b_top) / price_range * (price_height - 1)))
                bottom_y = int(round((max_price - b_bottom) / price_range * (price_height - 1)))

                if top_y <= row <= bottom_y:
                    # Candle Body
                    candle_char = "█"
                elif high_y <= row <= low_y:
                    # Wick
                    candle_char = "│"
                elif is_cursor:
                    # Dotted crosshair vertical line
                    candle_char = "·"
                    char_style = "#58a6ff"

                row_text.append(candle_char, style=char_style)
                row_text.append(" ")

            # Fill remaining width
            row_text.append(" " * max(0, available_width - len(visible_bars) * bar_width))
            # Price axis label on right
            row_text.append(f"│ {row_price:10.2f}\n", style="#8b949e")
            chart_text.append(row_text)

        # Divider between price and volume
        sep = Text()
        sep.append("─" * available_width, style="#30363d")
        sep.append("┼ VOLUME\n", style="#8b949e")
        chart_text.append(sep)

        # 2. Volume Rows
        for v_row in range(volume_height):
            # top v_row corresponds to higher fraction of volume
            threshold = (volume_height - v_row) / volume_height
            row_text = Text()

            for bar in visible_bars:
                ratio = bar.volume / max_volume
                is_green = bar.close >= bar.open
                vol_color = "#238636" if is_green else "#da3633"

                if ratio >= threshold:
                    row_text.append("█", style=vol_color)
                elif ratio >= threshold - (1.0 / (volume_height * 2)):
                    row_text.append("▄", style=vol_color)
                else:
                    row_text.append(" ", style="#8b949e")
                row_text.append(" ")

            row_text.append(" " * max(0, available_width - len(visible_bars) * bar_width))
            v_label = int(max_volume * ((volume_height - v_row) / volume_height))
            row_text.append(f"│ {v_label:10,}\n", style="#8b949e")
            chart_text.append(row_text)

        body_widget.update(chart_text)
