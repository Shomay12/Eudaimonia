"""Options Chain screen with analytical Greeks, PCR, and Max Pain.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Static

from eudaimonia.engine.market_state import MarketStateEngine
from eudaimonia.models.options import Moneyness, OptionChainSnapshot


class OptionsChainScreen(Widget):
    """Full-screen terminal Options Chain viewer."""

    DEFAULT_CSS = """
    OptionsChainScreen {
        layout: vertical;
        height: 1fr;
    }
    #chain-summary-bar {
        height: 2;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 1;
    }
    #chain-table {
        height: 1fr;
    }
    """

    def __init__(self, state_engine: MarketStateEngine, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state_engine = state_engine
        self.underlying: str = state_engine.active_underlying
        self.selected_expiry: date | None = state_engine.active_expiry
        self.strike_window: int = 15

    def compose(self) -> ComposeResult:
        yield Static(id="chain-summary-bar")
        yield DataTable(id="chain-table")

    def on_mount(self) -> None:
        table = self.query_one("#chain-table", DataTable)
        table.cursor_type = "row"

        # 17 Columns: Calls (8) | Strike & Status (2) | Puts (7)
        table.add_columns(
            "CE OI",
            "CE CHG",
            "CE VOL",
            "CE IV",
            "DELTA",
            "BID",
            "ASK",
            "CALL LTP",
            "STRIKE",
            "M",
            "PUT LTP",
            "BID",
            "ASK",
            "DELTA",
            "PE IV",
            "PE VOL",
            "PE CHG",
            "PE OI",
        )
        self.refresh_chain()

    def set_underlying(self, underlying: str) -> None:
        self.underlying = underlying.upper()
        self.selected_expiry = None
        self.refresh_chain()

    def next_expiry(self) -> None:
        expiries = self.state_engine.instruments.get_available_expiries(self.underlying)
        if not expiries:
            return
        if self.selected_expiry is None or self.selected_expiry not in expiries:
            self.selected_expiry = expiries[0]
        else:
            idx = expiries.index(self.selected_expiry)
            if idx < len(expiries) - 1:
                self.selected_expiry = expiries[idx + 1]
        self.refresh_chain()

    def prev_expiry(self) -> None:
        expiries = self.state_engine.instruments.get_available_expiries(self.underlying)
        if not expiries:
            return
        if self.selected_expiry is None or self.selected_expiry not in expiries:
            self.selected_expiry = expiries[0]
        else:
            idx = expiries.index(self.selected_expiry)
            if idx > 0:
                self.selected_expiry = expiries[idx - 1]
        self.refresh_chain()

    def zoom_in_strikes(self) -> None:
        self.strike_window = max(5, self.strike_window - 5)
        self.refresh_chain()

    def zoom_out_strikes(self) -> None:
        self.strike_window = min(40, self.strike_window + 5)
        self.refresh_chain()

    def refresh_chain(self) -> None:
        """Fetch chain snapshot from state engine and update UI."""
        try:
            summary_widget = self.query_one("#chain-summary-bar", Static)
            table = self.query_one("#chain-table", DataTable)
        except Exception:
            return

        snapshot = self.state_engine.build_option_chain_snapshot(
            underlying=self.underlying,
            expiry=self.selected_expiry,
            strike_window=self.strike_window,
        )

        if not snapshot:
            summary_widget.update(Text(f"OPTIONS CHAIN: {self.underlying} - No contracts available", style="#8b949e"))
            table.clear()
            return

        self.selected_expiry = snapshot.expiry

        # Build Summary Bar
        exp_str = snapshot.expiry.strftime("%d-%b-%Y").upper()
        all_exp_str = " | ".join(d.strftime("%d%b") for d in snapshot.available_expiries)

        s = Text()
        s.append(f"CHAIN: {snapshot.underlying} ", style="bold #58a6ff")
        s.append(f"SPOT: {snapshot.underlying_price:,.2f}  ", style="bold #3fb950")
        s.append(f"EXPIRY: [{exp_str}]  ", style="bold #d29922")
        s.append(f"ATM: {snapshot.atm_strike:,.2f}  ", style="bold #79c0ff")
        s.append(f"MAX PAIN: {snapshot.max_pain:,.2f}  " if snapshot.max_pain else "MAX PAIN: --  ", style="#f0883e")
        s.append(f"PCR (OI): {snapshot.pcr_oi:.2f}  " if snapshot.pcr_oi else "PCR (OI): --  ", style="#58a6ff")
        s.append(f"PCR (VOL): {snapshot.pcr_volume:.2f}  " if snapshot.pcr_volume else "PCR (VOL): --  ", style="#58a6ff")
        s.append(f"(Use '[' and ']' to change expiry, '-' and '+' for strikes)\n", style="#8b949e")
        s.append(f"Available Expiries: {all_exp_str}", style="#8b949e")

        summary_widget.update(s)

        # Populate Table Rows
        table.clear()

        for row in snapshot.strikes:
            k = row.strike_price
            is_atm = k == snapshot.atm_strike

            # Calls side
            ce_ltp_str = f"{row.call_ltp:,.2f}" if row.call_ltp is not None else "--"
            ce_bid_str = f"{row.call_tick.best_bid:,.2f}" if (row.call_tick and row.call_tick.best_bid) else "--"
            ce_ask_str = f"{row.call_tick.best_ask:,.2f}" if (row.call_tick and row.call_tick.best_ask) else "--"
            ce_iv_str = f"{row.call_greeks.iv * 100:.1f}%" if row.call_greeks else "--"
            ce_delta_str = f"{row.call_greeks.delta:.2f}" if row.call_greeks else "--"
            ce_oi_str = f"{row.call_oi:,}" if row.call_oi else "--"
            ce_oi_chg = f"{row.call_oi_change:+d}" if row.call_oi_change else "--"
            ce_vol_str = f"{row.call_volume:,}" if row.call_volume else "--"

            # Puts side
            pe_ltp_str = f"{row.put_ltp:,.2f}" if row.put_ltp is not None else "--"
            pe_bid_str = f"{row.put_tick.best_bid:,.2f}" if (row.put_tick and row.put_tick.best_bid) else "--"
            pe_ask_str = f"{row.put_tick.best_ask:,.2f}" if (row.put_tick and row.put_tick.best_ask) else "--"
            pe_iv_str = f"{row.put_greeks.iv * 100:.1f}%" if row.put_greeks else "--"
            pe_delta_str = f"{row.put_greeks.delta:.2f}" if row.put_greeks else "--"
            pe_oi_str = f"{row.put_oi:,}" if row.put_oi else "--"
            pe_oi_chg = f"{row.put_oi_change:+d}" if row.put_oi_change else "--"
            pe_vol_str = f"{row.put_volume:,}" if row.put_volume else "--"

            # Row styling based on ATM / ITM / OTM
            if is_atm:
                strike_style = "bold #ffffff on #1f6feb"
                ce_style = "bold #79c0ff"
                pe_style = "bold #79c0ff"
                moneyness_str = "ATM"
            elif row.call_moneyness == Moneyness.ITM:
                strike_style = "bold #c9d1d9"
                ce_style = "#e3b341"  # ITM Call amber
                pe_style = "#8b949e"  # OTM Put muted
                moneyness_str = "ITM"
            else:
                strike_style = "bold #c9d1d9"
                ce_style = "#8b949e"  # OTM Call muted
                pe_style = "#e3b341"  # ITM Put amber
                moneyness_str = "OTM"

            table.add_row(
                ce_oi_str,
                ce_oi_chg,
                ce_vol_str,
                ce_iv_str,
                ce_delta_str,
                ce_bid_str,
                ce_ask_str,
                Text(ce_ltp_str, style=ce_style),
                Text(f"{k:,.2f}", style=strike_style),
                Text(moneyness_str, style=strike_style),
                Text(pe_ltp_str, style=pe_style),
                pe_bid_str,
                pe_ask_str,
                pe_delta_str,
                pe_iv_str,
                pe_vol_str,
                pe_oi_chg,
                pe_oi_str,
                key=str(k),
            )
