"""Authoritative in-memory Market State Engine for Eudaimonia.

Developer: KJshomay12
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

from eudaimonia.analytics.black_scholes import calculate_greeks
from eudaimonia.analytics.chain_analytics import (
    calculate_max_pain,
    calculate_pcr,
    classify_moneyness,
    find_atm_strike,
)
from eudaimonia.analytics.implied_vol import calculate_implied_volatility
from eudaimonia.config import settings
from eudaimonia.engine.candle_engine import CandleEngine
from eudaimonia.engine.data_quality import DataQualityMonitor
from eudaimonia.engine.instrument_master import InstrumentMaster
from eudaimonia.models.events import ConnectionState, DataMode, FeedStatus
from eudaimonia.models.instrument import Exchange, Instrument, InstrumentType, OptionType
from eudaimonia.models.market_data import MarketDepth, MarketTick
from eudaimonia.models.options import Moneyness, OptionChainSnapshot, OptionStrikeRow


class MarketStateEngine:
    """Maintains synchronized market state, orderbooks, options chains, and candles."""

    def __init__(
        self,
        instrument_master: InstrumentMaster | None = None,
        candle_engine: CandleEngine | None = None,
        quality_monitor: DataQualityMonitor | None = None,
    ) -> None:
        self.instruments = instrument_master or InstrumentMaster()
        self.candle_engine = candle_engine or CandleEngine()
        self.quality_monitor = quality_monitor or DataQualityMonitor()

        # State storage
        self.ticks: dict[str, MarketTick] = {}
        self.depths: dict[str, MarketDepth] = {}
        self.subscribed_symbols: set[str] = set()

        # Selected navigation state
        self.active_exchange: Exchange = Exchange(settings.DEFAULT_EXCHANGE)
        self.active_underlying: str = settings.DEFAULT_UNDERLYING
        self.active_expiry: date | None = None

        # Feed status
        self.feed_status = FeedStatus(
            provider_name=settings.PROVIDER_NAME,
            connection_state=ConnectionState.DISCONNECTED,
            data_mode=DataMode(settings.DATA_MODE),
        )

        # Listeners for UI state refresh
        self._update_callbacks: list[asyncio.Callable[[], asyncio.Coroutine[None, None, None]]] = []

    def register_update_callback(self, cb: asyncio.Callable[[], asyncio.Coroutine[None, None, None]]) -> None:
        self._update_callbacks.append(cb)

    async def _notify_updates(self) -> None:
        for cb in self._update_callbacks:
            try:
                await cb()
            except Exception:
                pass

    def update_feed_status(self, status: FeedStatus) -> None:
        self.feed_status = status

    def on_market_depth(self, symbol: str, depth: MarketDepth) -> None:
        self.depths[symbol] = depth

    def on_market_tick(self, raw_tick: MarketTick) -> None:
        """Process incoming raw tick from provider."""
        # Quality check
        validated_tick, event = self.quality_monitor.validate_tick(raw_tick)

        # Store latest tick
        self.ticks[validated_tick.symbol] = validated_tick

        # Update feed status timing & latency
        now = datetime.now(timezone.utc)
        self.feed_status.last_receipt_time = now
        self.feed_status.last_event_time = validated_tick.exchange_time
        if validated_tick.exchange_time:
            # Observability receipt latency
            try:
                latency = (validated_tick.receipt_time - validated_tick.exchange_time).total_seconds() * 1000.0
                self.feed_status.latency_ms = max(0.0, round(latency, 1))
            except Exception:
                pass

        # Update candles
        self.candle_engine.on_tick(validated_tick)

    def get_tick(self, symbol: str) -> MarketTick | None:
        return self.ticks.get(symbol)

    def get_depth(self, symbol: str) -> MarketDepth | None:
        return self.depths.get(symbol)

    def build_option_chain_snapshot(
        self,
        underlying: str | None = None,
        expiry: date | None = None,
        strike_window: int = 15,
    ) -> OptionChainSnapshot | None:
        """Construct full Option Chain with analytical Greeks, PCR, and Max Pain."""
        target_und = (underlying or self.active_underlying).upper()
        available_expiries = self.instruments.get_available_expiries(target_und)
        if not available_expiries:
            return None

        target_expiry = expiry or self.active_expiry or available_expiries[0]
        if target_expiry not in available_expiries:
            target_expiry = available_expiries[0]

        # Find underlying spot price
        und_inst = self.instruments.get_by_symbol(f"NSE:{target_und}") or self.instruments.get_by_symbol(f"BSE:{target_und}") or self.instruments.get_by_symbol(target_und)
        und_tick = self.ticks.get(und_inst.symbol) if und_inst else None
        if not und_tick:
            # Fallback scan in ticks
            for sym, t in self.ticks.items():
                if target_und in sym:
                    und_tick = t
                    break

        spot_price = und_tick.ltp if und_tick else Decimal("25000.0")

        all_strikes = self.instruments.get_available_strikes(target_und, target_expiry)
        if not all_strikes:
            return None

        atm_strike = find_atm_strike(spot_price, all_strikes)

        # Slice strikes around ATM strike
        try:
            atm_index = all_strikes.index(atm_strike)
            start_idx = max(0, atm_index - strike_window)
            end_idx = min(len(all_strikes), atm_index + strike_window + 1)
            selected_strikes = all_strikes[start_idx:end_idx]
        except ValueError:
            selected_strikes = all_strikes[: strike_window * 2]

        # Time to expiry in fraction of 365-day year
        now_dt = datetime.now(timezone.utc)
        today = now_dt.date()
        days_to_expiry = max(0, (target_expiry - today).days)
        time_to_expiry = max(0.001, days_to_expiry / 365.0)

        rows: list[OptionStrikeRow] = []
        total_ce_oi = 0
        total_pe_oi = 0
        total_ce_vol = 0
        total_pe_vol = 0

        for strike in selected_strikes:
            ce_inst = self.instruments.get_option_contract(target_und, target_expiry, OptionType.CE, strike)
            pe_inst = self.instruments.get_option_contract(target_und, target_expiry, OptionType.PE, strike)

            ce_tick = self.ticks.get(ce_inst.symbol) if ce_inst else None
            pe_tick = self.ticks.get(pe_inst.symbol) if pe_inst else None

            # Calculate Greeks for Call
            ce_greeks = None
            if ce_tick and ce_tick.ltp > Decimal("0"):
                ce_iv = calculate_implied_volatility(
                    option_type=OptionType.CE,
                    market_price=float(ce_tick.ltp),
                    spot=float(spot_price),
                    strike=float(strike),
                    time_to_expiry_years=time_to_expiry,
                    risk_free_rate=settings.RISK_FREE_RATE,
                ) or 0.15
                ce_greeks = calculate_greeks(
                    option_type=OptionType.CE,
                    spot=float(spot_price),
                    strike=float(strike),
                    time_to_expiry_years=time_to_expiry,
                    risk_free_rate=settings.RISK_FREE_RATE,
                    volatility=ce_iv,
                )

            # Calculate Greeks for Put
            pe_greeks = None
            if pe_tick and pe_tick.ltp > Decimal("0"):
                pe_iv = calculate_implied_volatility(
                    option_type=OptionType.PE,
                    market_price=float(pe_tick.ltp),
                    spot=float(spot_price),
                    strike=float(strike),
                    time_to_expiry_years=time_to_expiry,
                    risk_free_rate=settings.RISK_FREE_RATE,
                ) or 0.15
                pe_greeks = calculate_greeks(
                    option_type=OptionType.PE,
                    spot=float(spot_price),
                    strike=float(strike),
                    time_to_expiry_years=time_to_expiry,
                    risk_free_rate=settings.RISK_FREE_RATE,
                    volatility=pe_iv,
                )

            ce_moneyness = classify_moneyness(strike, spot_price, atm_strike, OptionType.CE)
            pe_moneyness = classify_moneyness(strike, spot_price, atm_strike, OptionType.PE)

            row = OptionStrikeRow(
                strike_price=strike,
                call_instrument=ce_inst,
                put_instrument=pe_inst,
                call_tick=ce_tick,
                put_tick=pe_tick,
                call_greeks=ce_greeks,
                put_greeks=pe_greeks,
                call_moneyness=ce_moneyness,
                put_moneyness=pe_moneyness,
            )
            rows.append(row)

            total_ce_oi += row.call_oi
            total_pe_oi += row.put_oi
            total_ce_vol += row.call_volume
            total_pe_vol += row.put_volume

        pcr_oi = calculate_pcr(total_pe_oi, total_ce_oi)
        pcr_vol = calculate_pcr(total_pe_vol, total_ce_vol)
        max_pain = calculate_max_pain(rows)

        return OptionChainSnapshot(
            exchange=self.active_exchange,
            underlying=target_und,
            underlying_price=spot_price,
            expiry=target_expiry,
            available_expiries=available_expiries,
            strikes=rows,
            atm_strike=atm_strike,
            pcr_oi=pcr_oi,
            pcr_volume=pcr_vol,
            total_ce_oi=total_ce_oi,
            total_pe_oi=total_pe_oi,
            total_ce_volume=total_ce_vol,
            total_pe_volume=total_pe_vol,
            max_pain=max_pain,
            snapshot_time=now_dt,
        )
