# EUDAIMONIA: QUAXIOM TRADE TERMINAL

**Developer**: `KJshomay12`  
**Version**: `0.1.0`  
**Target Markets**: National Stock Exchange of India (NSE) & Bombay Stock Exchange (BSE)

A professional, terminal-native market-data and options-analysis application engineered for Indian equity and derivatives traders who prefer dense numerical information, keyboard-driven workflows, compact displays, low-latency updates, and reliable market data over decorative dashboards.

---

## Key Features

1. **Terminal-Native Information Architecture**
   - Built on Textual and Rich with a high-density, monospaced dark terminal aesthetic.
   - 100% keyboard-navigable: zero mouse interaction required.
   - No landing pages, marketing banners, or artificial delays.

2. **National Stock Exchange (NSE) & Bombay Stock Exchange (BSE) Coverage**
   - Real-time index benchmarks: NIFTY 50, BANKNIFTY, FINNIFTY, SENSEX, BANKEX.
   - Equities: Reliance, TCS, Infosys, HDFC Bank, ICICI Bank, SBI, Tata Motors, etc.
   - Dynamic derivatives ladder: European options (CE & PE) across weekly and monthly expiries.

3. **High-Performance Options Chain & Greeks Analytics**
   - Complete Call and Put options ladder aligned around At-The-Money (ATM) strike.
   - Analytical Black-Scholes-Merton Greek calculations:
     - **Delta** ($dV/dS$)
     - **Gamma** ($d^2V/dS^2$)
     - **Theta** (1-calendar-day decay in INR)
     - **Vega** (P&L sensitivity per 1% change in IV)
     - **Rho** (Interest rate sensitivity)
   - Robust Implied Volatility (IV) solver using Brent's method with quadratic convergence.
   - Put-Call Ratio (PCR) calculated by Open Interest and Volume.
   - Max Pain strike determination.
   - Expiry cycling (`[` and `]`) and strike zoom controls (`-` and `+`).

4. **Candlestick & Multi-Timeframe Volume Engine**
   - Real-time session-aligned aggregation for 1m, 3m, 5m, 15m, and Daily candles.
   - Strictly mapped to Indian market hours (09:15 to 15:30 IST) in `Asia/Kolkata`.
   - Volume Weighted Average Price (VWAP) calculation.
   - ASCII/Unicode candlestick charts with interactive crosshair inspection (`←` and `→`).

5. **Normalized Market-Data Provider Interface**
   - Decoupled `BaseMarketDataProvider` architecture.
   - High-fidelity **Mock Provider** generating correlated Brownian-walk ticks and 5-depth order books under `DataMode.MOCK`.
   - Production **Zerodha Kite Connect** adapter (`DataMode.LIVE`).
   - Upstox V2 adapter architecture.
   - Strict data-mode distinction: simulated or stale data is never labelled as live.

6. **Data Quality & Feed Integrity Monitor**
   - Detects out-of-order exchange timestamps.
   - Detects sequence gaps and duplicate ticks.
   - Detects non-positive suspect prices and stale feeds.
   - Prevents stale or out-of-order ticks from corrupting current market state.

7. **Local SQLite Persistence**
   - Asynchronous storage via `aiosqlite`.
   - Persists user watchlists, symbol ordering, active exchange, preferred underlying, and display preferences.

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/KJshomay12/Eudaimonia.git
cd Eudaimonia

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Running the Terminal

```bash
# Launch in default Mock mode (demonstrates full interface with live simulation)
eudaimonia

# Or run directly via module
python -m eudaimonia.cli

# Launch with specific underlying or provider
eudaimonia --underlying BANKNIFTY --exchange NSE
```

---

## Keyboard Shortcuts Cheat Sheet

| Key | Description |
| :--- | :--- |
| `F1` | **Help & Command Reference** |
| `F2` | **Market Overview & Watchlist** |
| `F3` | **Options Chain Screen** |
| `F4` | **Quote & 5-Depth Order Book** |
| `F5` | **Candlestick Chart** |
| `F6` | **Watchlists Manager** |
| `:` or `/` | **Open Command Bar** |
| `ESC` | **Cancel Command / Return to Overview** |
| `q` | **Quit Application** |
| `[` / `]` | **Previous / Next Options Expiry** |
| `-` / `+` | **Zoom In / Zoom Out Strikes** |
| `1, 3, 5, f, d` | **Chart Interval (1m, 3m, 5m, 15m, Daily)** |
| `v` | **Toggle VWAP on Chart** |
| `←` / `→` | **Move Chart Crosshair Cursor** |

---

## Interactive Command Line

Open the command bar with `:` or `/`:

```text
chain NIFTY               # Open options chain for NIFTY
chain BANKNIFTY           # Open options chain for BANKNIFTY
quote NSE:RELIANCE        # Open detailed quote & 5-depth order book
chart NSE:NIFTY -i 5m     # Open 5-minute candlestick chart
watch NSE:TCS             # Add symbol to active watchlist
unwatch NSE:TCS           # Remove symbol from watchlist
expiry                    # Cycle to next available options expiry
status                    # Display data provider status & latency
help                      # Open help screen
quit                      # Exit application
```

---

## Documentation Index

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and component interactions.
- [DATA_PROVIDER_SETUP.md](DATA_PROVIDER_SETUP.md) - Setting up Zerodha Kite Connect & Upstox credentials.
- [CONFIGURATION.md](CONFIGURATION.md) - Environment variables and configuration options.
- [DATA_QUALITY.md](DATA_QUALITY.md) - Feed anomaly detection, sequence tracking, and staleness rules.
- [TESTING.md](TESTING.md) - Automated test suite execution and test coverage.
- [SECURITY_AND_DATA_RIGHTS.md](SECURITY_AND_DATA_RIGHTS.md) - Credential management and SEBI/Exchange compliance.
