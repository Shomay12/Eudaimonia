# Data Provider Setup Guide: Eudaimonia

**Developer**: `KJshomay12`  
**Project**: Eudaimonia (Quaxiom Trade Terminal)

---

## 1. Provider Modes Overview

Eudaimonia strictly differentiates between data modes to prevent false claims of live data connectivity:

| Mode | Identifier | Description |
| :--- | :--- | :--- |
| **MOCK** | `DataMode.MOCK` | High-fidelity local simulation generating realistic Indian market Brownian-walk ticks, options Greek surfaces, and 5-depth order books. |
| **LIVE** | `DataMode.LIVE` | Authenticated real-time streaming WebSocket feed from an authorized Indian broker API. |
| **DELAYED** | `DataMode.DELAYED` | Public exchange-delayed feed (typically 15-minute delayed). |
| **HISTORICAL**| `DataMode.HISTORICAL`| Offline or replayed end-of-day / historical bar data. |

---

## 2. Setting Up the Mock Provider (Default)

The mock provider is ready out-of-the-box and requires no credentials or internet access. It generates:
- Correlated benchmarks: `NSE:NIFTY`, `NSE:BANKNIFTY`, `NSE:FINNIFTY`, `BSE:SENSEX`, `BSE:BANKEX`.
- Major bluechips: `NSE:RELIANCE`, `NSE:TCS`, `NSE:INFY`, `NSE:HDFCBANK`, `NSE:ICICIBANK`, `NSE:SBIN`, `NSE:TATAMOTORS`.
- Complete dynamic options chain ladder with analytical Black-Scholes pricing and realistic volatility smile.
- 5-depth Level-2 bid/ask books.

### Configuration:
In your `.env` file (or via CLI):
```bash
EUDAIMONIA_PROVIDER=mock
EUDAIMONIA_DATA_MODE=MOCK
```

Launch with:
```bash
eudaimonia
```

---

## 3. Zerodha Kite Connect Setup

Zerodha Kite Connect is India's most popular retail broker API. To connect live market data from Zerodha:

### Prerequisites:
1. An active Zerodha Trading and Demat account.
2. A registered developer account at [Kite Connect Developer Portal](https://developers.kite.trade).
3. An active Kite Connect app subscription.

### Step-by-Step Configuration:

1. **Create an App in Developer Console**:
   - Go to [Kite Developer Apps](https://developers.kite.trade/apps).
   - Create a new app and specify:
     - App Name: `Eudaimonia Terminal`
     - Redirect URL: `http://127.0.0.1:5000/` (or your preferred local URL)
   - Note down your **API Key** and **API Secret**.

2. **Generate Daily Access Token**:
   - Kite Connect access tokens expire daily at 06:00 AM IST.
   - To obtain the token:
     1. Open your browser to:
        ```text
        https://kite.zerodha.com/connect/login?v=3&api_key=YOUR_API_KEY
        ```
     2. Complete your 2FA login (Password + TOTP).
     3. You will be redirected to:
        ```text
        http://127.0.0.1:5000/?request_token=XXXXXX&action=login&status=success
        ```
     4. Copy the `request_token` parameter from the URL.
     5. Generate the session access token using Python or curl:
        ```python
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key="YOUR_API_KEY")
        data = kite.generate_session("REQUEST_TOKEN_COPIED", api_secret="YOUR_API_SECRET")
        print("ACCESS TOKEN:", data["access_token"])
        ```

3. **Configure Eudaimonia Environment**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Populate the Kite variables:
     ```bash
     EUDAIMONIA_PROVIDER=kite
     EUDAIMONIA_DATA_MODE=LIVE

     KITE_API_KEY=your_kite_api_key_here
     KITE_API_SECRET=your_kite_api_secret_here
     KITE_ACCESS_TOKEN=your_access_token_here
     ```

4. **Launch Eudaimonia in Live Mode**:
   ```bash
   eudaimonia --provider kite --mode LIVE
   ```

---

## 4. Upstox V2 API Setup

Upstox provides WebSocket feeds streaming Protobuf-encoded ticks.

### Configuration:
1. Register at [Upstox Developer Portal](https://developer.upstox.com).
2. Generate an Access Token using OAuth 2.0.
3. Configure `.env`:
   ```bash
   EUDAIMONIA_PROVIDER=upstox
   EUDAIMONIA_DATA_MODE=LIVE

   UPSTOX_API_KEY=your_upstox_api_key_here
   UPSTOX_ACCESS_TOKEN=your_upstox_access_token_here
   ```

---

## 5. Safe Mode Switching

To switch back to Mock mode at any time without removing credentials:

```bash
# Launch with CLI flag overrides
eudaimonia --provider mock --mode MOCK
```
The terminal header will immediately reflect `FEED: [MOCK]` in amber or `FEED: [LIVE]` in green.
