# Configuration Reference: Eudaimonia

**Developer**: `KJshomay12`  
**Project**: Eudaimonia (Quaxiom Trade Terminal)

---

## 1. Environment Variables Reference

All runtime parameters can be configured via environment variables or specified in a local `.env` file in the project root directory.

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `EUDAIMONIA_DATA_MODE` | String | `MOCK` | Runtime feed mode: `MOCK`, `LIVE`, `HISTORICAL`, or `DELAYED`. |
| `EUDAIMONIA_PROVIDER` | String | `mock` | Active market data adapter: `mock`, `kite`, `upstox`, or `dhan`. |
| `EUDAIMONIA_DEFAULT_EXCHANGE` | String | `NSE` | Default exchange for symbols without explicit prefix (`NSE` or `BSE`). |
| `EUDAIMONIA_DEFAULT_UNDERLYING`| String | `NIFTY`| Default active index or equity underlying on launch. |
| `EUDAIMONIA_TIMEZONE` | String | `Asia/Kolkata`| Market timezone used for Indian session boundaries and clocks. |
| `EUDAIMONIA_RISK_FREE_RATE` | Float | `0.065` | Annualized risk-free rate for Black-Scholes Greeks (6.5% for RBI 91-day T-bills). |
| `EUDAIMONIA_STALE_THRESHOLD_SECONDS` | Float | `5.0` | Inactivity threshold before feed is flagged with a `[FEED STALE]` warning. |
| `EUDAIMONIA_UI_FPS` | Integer | `4` | Terminal UI refresh frequency (Hz). Keeps rendering non-blocking. |
| `EUDAIMONIA_DB_PATH` | Path | `data/eudaimonia.db`| SQLite database file path for watchlists and user preferences. |
| `KITE_API_KEY` | String | `None` | Zerodha Kite Connect API Key. |
| `KITE_API_SECRET` | String | `None` | Zerodha Kite Connect API Secret. |
| `KITE_ACCESS_TOKEN` | String | `None` | Zerodha Kite Connect active session access token. |
| `UPSTOX_API_KEY` | String | `None` | Upstox API Key. |
| `UPSTOX_ACCESS_TOKEN` | String | `None` | Upstox OAuth Access Token. |

---

## 2. Command-Line Arguments Override

Any configuration value can be overridden on launch without modifying the `.env` file:

```bash
eudaimonia --help

options:
  -h, --help            Show this help message and exit
  --version, -v         Show program's version number and exit
  --provider, -p        Market data provider adapter: mock, kite, upstox, dhan (default: mock)
  --mode, -m            Data mode: MOCK, LIVE, HISTORICAL, DELAYED (default: MOCK)
  --exchange, -e        Default primary exchange: NSE, BSE (default: NSE)
  --underlying, -u      Default active underlying: NIFTY, BANKNIFTY, SENSEX, RELIANCE, etc.
```

---

## 3. Local SQLite Persistence Design

Eudaimonia uses `aiosqlite` for asynchronous local persistence.

### What is Persisted:
1. **User Watchlists**: Names, custom ordering, and symbol lists across sessions.
2. **User Preferences**: Last-selected underlying, preferred expiry, visible strike windows, and theme settings.

### What is NOT Persisted:
- **Streaming Ticks**: To avoid unbounded disk growth and high I/O latency, streaming ticks are held in-memory in `MarketStateEngine`.
- If historical research tick recording is enabled in future releases, it should use partitioned **Parquet** files rather than SQLite row inserts.

### Disk Usage:
- Initial database creation: `< 50 KB`.
- Average disk footprint after storing dozens of watchlists: `< 1 MB`.
