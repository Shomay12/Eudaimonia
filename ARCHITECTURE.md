# System Architecture: Eudaimonia (Quaxiom Trade Terminal)

**Developer**: `KJshomay12`  
**Project**: Eudaimonia  
**Target Exchanges**: National Stock Exchange of India (NSE) & Bombay Stock Exchange (BSE)

---

## 1. Architectural Philosophy

Eudaimonia is engineered from the ground up for experienced Indian equity and options traders who require dense numerical information, keyboard-driven workflows, compact displays, and predictable low-latency updates.

Unlike web-based trading portals or electron apps, Eudaimonia operates entirely within a monospaced terminal environment using Python's `asyncio`, `Textual`, and `Rich`.

### Core Architectural Principles:
1. **Decoupled Data Pipeline**: Market data ingestion, internal state synchronization, analytical processing, and terminal rendering operate independently.
2. **Normalized Data Modeling**: All exchange and broker-specific data structures are normalized into canonical models using `Decimal` representation for prices.
3. **Data Quality First**: Incomplete, stale, or out-of-order events are strictly tagged and prevented from corrupting the authoritative market state.
4. **Zero Forced Latency**: Non-blocking asynchronous event handling ensures feed processing never blocks UI interactions.

---

## 2. High-Level Component Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               Market Data Feed               │
                    │   (MockProvider / KiteConnect / UpstoxV2)    │
                    └──────────────────────┬───────────────────────┘
                                           │ MarketTick / MarketDepth
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │             Data Quality Monitor             │
                    │ (Out-of-Order / Sequence Gaps / Staleness)   │
                    └──────────────────────┬───────────────────────┘
                                           │ Validated Event
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             Market State Engine                                  │
│                                                                                  │
│   ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────────┐   │
│   │ Instrument Master  │   │   Candle Engine    │   │   Options Analytics    │   │
│   │ (NSE/BSE Reference)│   │(1m, 3m, 5m, 15m, 1d│   │ (Black-Scholes, Greeks,│   │
│   │                    │   │  Session VWAP)     │   │   IV Solver, Max Pain) │   │
│   └────────────────────┘   └────────────────────┘   └────────────────────────┘   │
└──────────────────────────────────────────┬───────────────────────────────────────┘
                                           │ Thread-safe State Update
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            Textual Terminal UI App                               │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐   │
│   │                               HeaderBar                                  │   │
│   │        [Indices: NIFTY, BNIFTY, SENSEX | Feed Health | Latency | Clock]  │   │
│   ├──────────────────────────────────────────────────────────────────────────┤   │
│   │                            Active Screen View                            │   │
│   │   • OverviewScreen (Benchmarks & Watchlist)                              │   │
│   │   • OptionsChainScreen (Calls/Puts, Greeks, PCR, Strike Ladder)          │   │
│   │   • QuoteScreen (LTP, OHLC, Level-2 5-Depth Order Book)                  │   │
│   │   • ChartScreen (OHLCV Candlesticks, Volume Bars, Crosshair, VWAP)       │   │
│   │   • WatchlistScreen (Watchlist Manager)                                  │   │
│   │   • HelpScreen (Keyboard Shortcuts & Command Reference)                  │   │
│   ├──────────────────────────────────────────────────────────────────────────┤   │
│   │                     CommandLine (Interactive Input Bar)                  │   │
│   ├──────────────────────────────────────────────────────────────────────────┤   │
│   │                     StatusFooter (Hotkeys & Context)                     │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                           ▲
                                           │ Persistence
                    ┌──────────────────────┴───────────────────────┐
                    │             SQLite Storage Layer             │
                    │        (Watchlists & User Preferences)       │
                    └──────────────────────────────────────────────┘
```

---

## 3. Data Flow & Concurrency Model

### 1. Asynchronous Ingestion Loop
- The configured provider (e.g., `MockMarketDataProvider` or `KiteConnectMarketDataProvider`) runs in an isolated `asyncio.Task`.
- In streaming mode, ticks and order-book snapshots are pushed into asynchronous callbacks rather than polled over HTTP.

### 2. Quality Verification
- Before a tick enters the `MarketStateEngine`, it passes through `DataQualityMonitor.validate_tick()`.
- If an exchange timestamp is older than previously recorded ticks, or a sequence number drops, the event is tagged as `OUT_OF_ORDER`.
- If a sequence jump occurs, `SEQUENCE_GAP` is emitted.
- If a price is non-positive, `SUSPECT_PRICE` is flagged.

### 3. State Management & Candle Accumulation
- The `MarketStateEngine` maintains the latest price, depth, and volume for each subscribed symbol.
- Validated ticks are routed to the `CandleEngine`, which aggregates them into timeframe buckets (1m, 3m, 5m, 15m, 1d) aligned strictly to Indian trading hours (09:15 to 15:30 IST).
- Volume Weighted Average Price (VWAP) is dynamically updated:
  $$\text{VWAP} = \frac{\sum (P_i \times V_i)}{\sum V_i}$$

### 4. Mathematical Greeks & Options Pricing
- When an options chain is requested or refreshed, `MarketStateEngine.build_option_chain_snapshot()` performs high-performance analytical Black-Scholes pricing for all strikes around the At-The-Money (ATM) strike.
- The implied volatility solver uses Brent's method (`scipy.optimize.brentq`) with quadratic convergence.
- Put-Call Ratios (PCR) are calculated for both Open Interest and Traded Volume:
  $$\text{PCR}_{\text{OI}} = \frac{\text{Total Put OI}}{\text{Total Call OI}}, \quad \text{PCR}_{\text{Vol}} = \frac{\text{Total Put Volume}}{\text{Total Call Volume}}$$
- Max Pain is computed by evaluating aggregate buyer payoff across all active strikes.

### 5. UI Rendering & Refresh Throttling
- The UI render loop is decoupled from the tick ingestion frequency.
- The terminal refreshes at a configurable rate (`settings.UI_REFRESH_HZ`, default 4 Hz), preventing UI render saturation while processing thousands of background market ticks.
