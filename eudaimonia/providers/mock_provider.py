"""Realistic Mock Market Data Provider for NSE and BSE.

Developer: KJshomay12
"""

from __future__ import annotations

import asyncio
import math
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from eudaimonia.analytics.black_scholes import black_scholes_price
from eudaimonia.config import settings
from eudaimonia.models.events import ConnectionState, DataMode, FeedStatus
from eudaimonia.models.instrument import Exchange, Instrument, InstrumentType, OptionType, Segment
from eudaimonia.models.market_data import (
    CandleBar,
    CandleInterval,
    MarketDepth,
    MarketDepthLevel,
    MarketTick,
)
from eudaimonia.models.options import OptionChainSnapshot
from eudaimonia.providers.base import BaseMarketDataProvider


def _get_upcoming_thursdays(count: int = 4) -> list[date]:
    """Calculate upcoming Thursdays for weekly and monthly Indian F&O expiries."""
    today = datetime.now(timezone.utc).date()
    thursdays: list[date] = []
    current = today
    while len(thursdays) < count:
        if current.weekday() == 3 and current >= today:  # Thursday
            thursdays.append(current)
        current += timedelta(days=1)
    return thursdays


class MockMarketDataProvider(BaseMarketDataProvider):
    """High-fidelity simulation feed generating correlated Indian market data."""

    def __init__(self) -> None:
        super().__init__(name="MockIndianFeed", data_mode=DataMode.MOCK)
        self.state = ConnectionState.DISCONNECTED
        self._subscribed_symbols: set[str] = set()
        self._subscribed_depth_symbols: set[str] = set()
        self._ticker_task: asyncio.Task | None = None
        self._sequence_counter: int = 1000

        # Master instruments catalog cache
        self._instruments: list[Instrument] = []
        self._price_state: dict[str, Decimal] = {}
        self._prev_closes: dict[str, Decimal] = {}
        self._volumes: dict[str, int] = {}
        self._open_interests: dict[str, int] = {}

        self._build_instruments_catalog()

    def _build_instruments_catalog(self) -> None:
        """Create reference metadata for NSE and BSE indices, equities, and options."""
        # 1. Major Indices
        indices_data = [
            ("NSE:NIFTY", "NIFTY", "Nifty 50 Index", Exchange.NSE, Decimal("24850.0"), 25, Decimal("0.05")),
            ("NSE:BANKNIFTY", "BANKNIFTY", "Nifty Bank Index", Exchange.NSE, Decimal("52300.0"), 15, Decimal("0.05")),
            ("NSE:FINNIFTY", "FINNIFTY", "Nifty Financial Services", Exchange.NSE, Decimal("23850.0"), 25, Decimal("0.05")),
            ("BSE:SENSEX", "SENSEX", "BSE SENSEX Index", Exchange.BSE, Decimal("81600.0"), 10, Decimal("0.05")),
            ("BSE:BANKEX", "BANKEX", "BSE BANKEX Index", Exchange.BSE, Decimal("58200.0"), 15, Decimal("0.05")),
        ]

        for sym, tsym, name, exch, price, lot, tick in indices_data:
            inst = Instrument(
                symbol=sym,
                tradingsymbol=tsym,
                name=name,
                exchange=exch,
                segment=Segment.INDEX,
                instrument_type=InstrumentType.INDEX,
                provider_id=f"idx_{tsym.lower()}",
                underlying=tsym,
                lot_size=lot,
                tick_size=tick,
            )
            self._instruments.append(inst)
            self._price_state[sym] = price
            self._prev_closes[sym] = price * Decimal("0.996")
            self._volumes[sym] = 150000000
            self._open_interests[sym] = 0

        # 2. Bluechip Equities
        equities_data = [
            ("NSE:RELIANCE", "RELIANCE", "Reliance Industries Ltd.", Exchange.NSE, Decimal("2960.0"), 250),
            ("NSE:TCS", "TCS", "Tata Consultancy Services Ltd.", Exchange.NSE, Decimal("4180.0"), 175),
            ("NSE:INFY", "INFY", "Infosys Ltd.", Exchange.NSE, Decimal("1835.0"), 400),
            ("NSE:HDFCBANK", "HDFCBANK", "HDFC Bank Ltd.", Exchange.NSE, Decimal("1690.0"), 550),
            ("NSE:ICICIBANK", "ICICIBANK", "ICICI Bank Ltd.", Exchange.NSE, Decimal("1230.0"), 700),
            ("NSE:SBIN", "SBIN", "State Bank of India", Exchange.NSE, Decimal("825.0"), 750),
            ("NSE:TATAMOTORS", "TATAMOTORS", "Tata Motors Ltd.", Exchange.NSE, Decimal("985.0"), 500),
            ("BSE:RELIANCE", "RELIANCE", "Reliance Industries Ltd. (BSE)", Exchange.BSE, Decimal("2959.5"), 250),
        ]

        for sym, tsym, name, exch, price, lot in equities_data:
            inst = Instrument(
                symbol=sym,
                tradingsymbol=tsym,
                name=name,
                exchange=exch,
                segment=Segment.EQUITY,
                instrument_type=InstrumentType.EQUITY,
                provider_id=f"eq_{exch.value.lower()}_{tsym.lower()}",
                underlying=tsym,
                lot_size=lot,
                tick_size=Decimal("0.05"),
            )
            self._instruments.append(inst)
            self._price_state[sym] = price
            self._prev_closes[sym] = price * Decimal("0.992")
            self._volumes[sym] = 1200000
            self._open_interests[sym] = 0

        # 3. Dynamic Options Ladder for NIFTY, BANKNIFTY, SENSEX
        expiries = _get_upcoming_thursdays(count=4)
        ladder_configs = [
            ("NIFTY", Exchange.NSE, Decimal("24850.0"), 50, 20, 25),
            ("BANKNIFTY", Exchange.NSE, Decimal("52300.0"), 100, 20, 15),
            ("SENSEX", Exchange.BSE, Decimal("81600.0"), 100, 20, 10),
        ]

        for und, exch, spot, step, count, lot in ladder_configs:
            atm = round(spot / step) * step
            for exp in expiries:
                for i in range(-count, count + 1):
                    strike = atm + Decimal(str(i * step))
                    exp_str = exp.strftime("%d%b%y").upper()

                    for opt_type in (OptionType.CE, OptionType.PE):
                        tsym = f"{und}{exp_str}{strike}{opt_type.value}"
                        sym = f"{exch.value}:{tsym}"
                        name = f"{und} {strike} {opt_type.value}"

                        inst = Instrument(
                            symbol=sym,
                            tradingsymbol=tsym,
                            name=name,
                            exchange=exch,
                            segment=Segment.DERIVATIVE,
                            instrument_type=InstrumentType.OPTION,
                            provider_id=f"opt_{sym}",
                            underlying=und,
                            lot_size=lot,
                            tick_size=Decimal("0.05"),
                            strike_price=strike,
                            expiry_date=exp,
                            option_type=opt_type,
                        )
                        self._instruments.append(inst)

                        # Calculate initial Black-Scholes theoretical price
                        days = max(1, (exp - datetime.now(timezone.utc).date()).days)
                        t = days / 365.0
                        vol = 0.13 + (abs(i) * 0.003)  # Volatility smile
                        bs_p = black_scholes_price(
                            option_type=opt_type,
                            spot=float(spot),
                            strike=float(strike),
                            time_to_expiry_years=t,
                            risk_free_rate=settings.RISK_FREE_RATE,
                            volatility=vol,
                        )
                        initial_price = Decimal(str(max(0.05, round(bs_p, 2))))
                        self._price_state[sym] = initial_price
                        self._prev_closes[sym] = initial_price * Decimal("0.98")
                        self._volumes[sym] = random.randint(10000, 2500000)
                        self._open_interests[sym] = random.randint(50000, 8000000)

    async def connect(self) -> bool:
        self.state = ConnectionState.CONNECTED
        status = self.get_connection_status()
        await self.emit_status(status)

        # Launch simulated streaming ticker
        if self._ticker_task is None or self._ticker_task.done():
            self._ticker_task = asyncio.create_task(self._run_ticker())
        return True

    async def disconnect(self) -> None:
        self.state = ConnectionState.DISCONNECTED
        if self._ticker_task and not self._ticker_task.done():
            self._ticker_task.cancel()
        status = self.get_connection_status()
        await self.emit_status(status)

    async def subscribe_quotes(self, symbols: list[str]) -> bool:
        for s in symbols:
            self._subscribed_symbols.add(s)
        await self.emit_status(self.get_connection_status())
        return True

    async def unsubscribe_quotes(self, symbols: list[str]) -> bool:
        for s in symbols:
            self._subscribed_symbols.discard(s)
        await self.emit_status(self.get_connection_status())
        return True

    async def subscribe_depth(self, symbols: list[str]) -> bool:
        for s in symbols:
            self._subscribed_depth_symbols.add(s)
        return True

    async def unsubscribe_depth(self, symbols: list[str]) -> bool:
        for s in symbols:
            self._subscribed_depth_symbols.discard(s)
        return True

    async def fetch_instruments(self, exchange: Exchange | None = None) -> list[Instrument]:
        if exchange:
            return [inst for inst in self._instruments if inst.exchange == exchange]
        return list(self._instruments)

    async def fetch_historical_bars(
        self,
        symbol: str,
        interval: CandleInterval,
        from_time: datetime,
        to_time: datetime,
    ) -> list[CandleBar]:
        """Synthesize historical bars based on current price level with realistic variance."""
        base_price = self._price_state.get(symbol, Decimal("24850.0"))
        sec = interval.seconds
        total_seconds = int((to_time - from_time).total_seconds())
        bar_count = min(150, max(5, total_seconds // sec))

        bars: list[CandleBar] = []
        curr_price = float(base_price) * 0.985
        curr_time = from_time

        for _ in range(bar_count):
            change = (random.random() - 0.49) * (curr_price * 0.002)
            open_p = curr_price
            close_p = curr_price + change
            high_p = max(open_p, close_p) + abs(random.random() * (curr_price * 0.001))
            low_p = min(open_p, close_p) - abs(random.random() * (curr_price * 0.001))
            vol = random.randint(100, 50000)

            bar = CandleBar(
                symbol=symbol,
                interval=interval,
                timestamp=curr_time,
                open=Decimal(str(round(open_p, 2))),
                high=Decimal(str(round(high_p, 2))),
                low=Decimal(str(round(low_p, 2))),
                close=Decimal(str(round(close_p, 2))),
                volume=vol,
                trades=random.randint(5, 500),
                vwap=Decimal(str(round((open_p + high_p + low_p + close_p) / 4.0, 2))),
                is_complete=True,
            )
            bars.append(bar)
            curr_price = close_p
            curr_time += timedelta(seconds=sec)

        return bars

    async def fetch_option_chain(
        self,
        underlying: str,
        expiry: date | None = None,
    ) -> OptionChainSnapshot | None:
        # State engine maintains the dynamic snapshot
        return None

    def get_connection_status(self) -> FeedStatus:
        return FeedStatus(
            provider_name=self.name,
            connection_state=self.state,
            data_mode=self.data_mode,
            subscribed_count=len(self._subscribed_symbols),
            latency_ms=random.uniform(0.5, 3.2) if self.state == ConnectionState.CONNECTED else 0.0,
        )

    def _generate_depth(self, ltp: Decimal, tick_size: Decimal) -> MarketDepth:
        """Create realistic 5-level bid and ask books around LTP."""
        half_spread = tick_size
        best_bid = max(tick_size, ltp - half_spread)
        best_ask = ltp + half_spread

        bids = [
            MarketDepthLevel(
                price=best_bid - Decimal(str(i)) * tick_size,
                quantity=random.randint(50, 1500) * 25,
                orders=random.randint(2, 25),
            )
            for i in range(5)
        ]
        asks = [
            MarketDepthLevel(
                price=best_ask + Decimal(str(i)) * tick_size,
                quantity=random.randint(50, 1500) * 25,
                orders=random.randint(2, 25),
            )
            for i in range(5)
        ]
        return MarketDepth(bids=bids, asks=asks)

    async def _run_ticker(self) -> None:
        """Background coroutine generating market ticks."""
        while self.state == ConnectionState.CONNECTED:
            try:
                active_symbols = list(self._subscribed_symbols) or [
                    "NSE:NIFTY",
                    "NSE:BANKNIFTY",
                    "BSE:SENSEX",
                    "NSE:RELIANCE",
                    "NSE:HDFCBANK",
                ]

                # Update 2 to 4 symbols each tick cycle
                symbols_to_update = random.sample(active_symbols, min(len(active_symbols), random.randint(2, 5)))
                now_utc = datetime.now(timezone.utc)

                for sym in symbols_to_update:
                    prev_p = self._price_state.get(sym, Decimal("100.0"))
                    # Brownian walk tick perturbation
                    pct_delta = Decimal(str(round((random.random() - 0.498) * 0.002, 6)))
                    delta = prev_p * pct_delta
                    new_p = max(Decimal("0.05"), round(prev_p + delta, 2))
                    self._price_state[sym] = new_p

                    vol_delta = random.randint(10, 2000)
                    self._volumes[sym] = self._volumes.get(sym, 0) + vol_delta
                    oi_delta = random.randint(-500, 1500)
                    self._open_interests[sym] = max(0, self._open_interests.get(sym, 100000) + oi_delta)

                    depth = self._generate_depth(new_p, Decimal("0.05"))
                    self._sequence_counter += 1

                    tick = MarketTick(
                        symbol=sym,
                        exchange=Exchange.NSE if "BSE" not in sym else Exchange.BSE,
                        segment=Segment.DERIVATIVE if ("CE" in sym or "PE" in sym) else (Segment.INDEX if "NIFTY" in sym or "SENSEX" in sym else Segment.EQUITY),
                        provider_id=f"mock_{sym}",
                        ltp=new_p,
                        ltq=vol_delta,
                        total_volume=self._volumes[sym],
                        open_interest=self._open_interests[sym],
                        oi_change=oi_delta,
                        exchange_time=now_utc - timedelta(milliseconds=random.randint(1, 15)),
                        receipt_time=now_utc,
                        best_bid=depth.bids[0].price,
                        best_ask=depth.asks[0].price,
                        bid_qty=depth.bids[0].quantity,
                        ask_qty=depth.asks[0].quantity,
                        depth=depth,
                        open_price=self._prev_closes.get(sym, new_p),
                        prev_close=self._prev_closes.get(sym, new_p),
                        sequence_id=self._sequence_counter,
                        source="MOCK_FEED",
                    )

                    await self.emit_tick(tick)

                    if sym in self._subscribed_depth_symbols:
                        await self.emit_depth(sym, depth)

                await asyncio.sleep(1.0 / max(1, settings.UI_REFRESH_HZ))
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)
