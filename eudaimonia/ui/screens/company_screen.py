"""Company Intelligence & Wikipedia Profile Screen for Eudaimonia.

Developer: KJshomay12
"""

from __future__ import annotations

from decimal import Decimal
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from eudaimonia.engine.company_info import CompanyProfile, get_company_profile
from eudaimonia.engine.market_state import MarketStateEngine


class CompanyScreen(Widget):
    """Full-screen Company Profile with Fundamental Metrics & Wikipedia Details."""

    DEFAULT_CSS = """
    CompanyScreen {
        layout: vertical;
        height: 1fr;
    }
    #company-scroll {
        height: 1fr;
        padding: 0 1;
    }
    #company-header-card {
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 1 1;
        margin-bottom: 1;
    }
    #company-metrics-card {
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 1 1;
        margin-bottom: 1;
    }
    #company-wiki-card {
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 1 1;
    }
    """

    def __init__(self, state_engine: MarketStateEngine, symbol_or_name: str = "RELIANCE", **kwargs) -> None:
        super().__init__(**kwargs)
        self.state_engine = state_engine
        self.target_query: str = symbol_or_name
        self.profile: CompanyProfile | None = None

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="company-scroll"):
            yield Static(id="company-header-card")
            yield Static(id="company-metrics-card")
            yield Static(id="company-wiki-card")

    def on_mount(self) -> None:
        self.load_company(self.target_query)

    def load_company(self, query: str) -> None:
        self.target_query = query
        self.profile = get_company_profile(query)
        self.refresh_display()

    def refresh_display(self) -> None:
        try:
            header_widget = self.query_one("#company-header-card", Static)
            metrics_widget = self.query_one("#company-metrics-card", Static)
            wiki_widget = self.query_one("#company-wiki-card", Static)
        except Exception:
            return

        if not self.profile:
            header_widget.update(Text(f"COMPANY SEARCH: '{self.target_query}' - No matching Indian listed entity found.", style="#f85149"))
            metrics_widget.update(Text("Available: RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, TATAMOTORS, SBIN", style="#8b949e"))
            wiki_widget.update(Text("", style="#8b949e"))
            return

        p = self.profile
        tick = self.state_engine.get_tick(p.symbol)

        # 1. Header Section
        h = Text()
        h.append("COMPANY INTELLIGENCE // ", style="bold #8b949e")
        h.append(f"{p.company_name.upper()}\n", style="bold #58a6ff")
        h.append(f"SYMBOL: {p.symbol}  |  EXCHANGE: {p.exchange}  |  ISIN: {p.isin}\n", style="#c9d1d9")
        h.append(f"SECTOR: {p.sector}  |  INDUSTRY: {p.industry}", style="#8b949e")
        header_widget.update(h)

        # 2. Market & Fundamental Metrics Section
        m = Text()
        m.append("KEY MARKET & VALUATION METRICS\n", style="bold #3fb950")
        if tick:
            chg = tick.change or Decimal("0.0")
            pct = tick.change_pct or Decimal("0.0")
            color = "#3fb950" if chg >= 0 else "#f85149"
            sign = "+" if chg >= 0 else ""
            m.append(f"  Current LTP: ₹{tick.ltp:,.2f}  ", style=f"bold {color}")
            m.append(f"Change: {sign}{chg:.2f} ({sign}{pct:.2f}%)  ", style=color)
            m.append(f"Day Volume: {tick.total_volume:,}\n", style="#58a6ff")
        else:
            m.append("  Current LTP: Awaiting real-time tick...\n", style="#8b949e")

        m.append(f"  Market Capitalization : ₹{p.market_cap_inr_cr:,.0f} Cr\n", style="#c9d1d9")
        m.append(f"  P/E Ratio (Trailing)  : {p.pe_ratio:.1f}x            |  P/B Ratio: {p.pb_ratio:.2f}x\n", style="#c9d1d9")
        m.append(f"  Dividend Yield        : {p.dividend_yield_pct:.2f}%            |  52-Week Range: ₹{p.week_52_low:,.2f} – ₹{p.week_52_high:,.2f}", style="#c9d1d9")
        metrics_widget.update(m)

        # 3. Wikipedia Integration Section
        w = Text()
        w.append("WIKIPEDIA // ABOUT & OPERATIONAL PROFILE\n", style="bold #d29922")
        w.append(f"  Headquarters : {p.headquarters}\n", style="#c9d1d9")
        w.append(f"  Founded Year : {p.founded_year}                      |  Leadership: {p.key_executives}\n", style="#c9d1d9")
        if p.business_segments:
            w.append(f"  Core Business: {', '.join(p.business_segments)}\n\n", style="#8b949e")
        else:
            w.append("\n")

        w.append(f"  Overview:\n  {p.wiki_summary}\n\n", style="#c9d1d9")
        w.append(f"  Wikipedia Reference: {p.wiki_url}\n", style="#58a6ff")
        w.append("  Press 'c' for Chart | 'o' for Options Chain | 'F4' for Order Book | ESC to return", style="#8b949e")
        wiki_widget.update(w)
