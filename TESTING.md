# Testing Guide & Quality Assurance: Eudaimonia

**Developer**: `KJshomay12`  
**Project**: Eudaimonia (Quaxiom Trade Terminal)

---

## 1. Test Suite Overview

Eudaimonia includes a comprehensive, automated test suite covering all critical domains: mathematical analytics, IV solvers, candle aggregation, data quality monitors, storage persistence, and full headless Textual UI workflows.

---

## 2. Test Execution Commands

Run the complete test suite:

```bash
# Run all tests with verbose output
pytest -v

# Run with short test summary
pytest -q

# Run specific test modules
pytest tests/test_analytics.py -v
pytest tests/test_candle_engine.py -v
pytest tests/test_app_headless.py -v
```

---

## 3. Test Modules & Coverage

| Test Module | Coverage Domain | Key Verifications |
| :--- | :--- | :--- |
| `tests/test_analytics.py` | Mathematical Options Analytics | Put-Call parity, Analytical Greeks bounds (Delta, Gamma, Vega, Theta), PCR by OI & Volume, ATM strike selection, Moneyness classification, Max Pain strike calculation. |
| `tests/test_implied_vol.py` | Implied Volatility Solver | Brent's method convergence, recovery of exact input volatility from Black-Scholes price, handling of arbitrage boundary violations (lower/upper bound). |
| `tests/test_candle_engine.py`| Candlestick & Volume Engine | Real-time tick aggregation into 1m, 3m, 5m, 15m, 1d bars, Indian session alignment (`Asia/Kolkata`), Volume accumulation, Session VWAP calculation. |
| `tests/test_data_quality.py`| Feed Anomaly Detection | Non-positive price flagging, sequence gap detection and lost tick calculation, duplicate/decreasing sequence detection, out-of-order exchange timestamp handling, feed staleness threshold. |
| `tests/test_models.py` | Normalized Data Models | Decimal conversion, bid/ask spread computation, net change & percentage change properties, Level-2 depth volume totals. |
| `tests/test_instrument_master.py` | Reference Catalog | Dynamic instrument indexing, symbol lookup (with/without prefix), option lookup by (underlying, expiry, type, strike), strike filtering, instrument search. |
| `tests/test_storage.py` | SQLite Persistence | Asynchronous table schema initialization, default watchlist seeding, adding/removing symbols, duplicate protection, structured preference persistence. |
| `tests/test_mock_provider.py` | Provider Simulation Contract | Connection lifecycle, catalog generation, quote/depth subscription, streaming tick generation, historical bars synthesis. |
| `tests/test_commands.py` | CLI & Command Bar | Argument parsing for CLI flags, command line syntax checking, known commands validation. |
| `tests/test_app_headless.py` | Terminal UI Integration | Full headless Textual app mounting, screen navigation (Overview, Chain, Quote, Chart, Watchlists, Help), keyboard actions, interactive command execution. |

---

## 4. Test Determinism

- All test cases use deterministic inputs, mathematical bounds, and explicit timezone definitions (`ZoneInfo("Asia/Kolkata")` and `timezone.utc`).
- SQLite persistence tests execute against an isolated temporary database (`test_eudaimonia.db`) managed by `conftest.py`, ensuring zero side effects on production data.
