# Security and Market Data Rights: Eudaimonia

**Developer**: `KJshomay12`  
**Project**: Eudaimonia (Quaxiom Trade Terminal)

---

## 1. Credential Security & Secret Management

1. **Zero Secret Hardcoding**:
   - No API keys, secret keys, access tokens, or account passwords may ever be hardcoded into Python files or committed to Git.
   - The `.gitignore` file explicitly excludes `.env`, `*.key`, `*.pem`, and `*.token`.

2. **Template Configuration**:
   - A `.env.example` file is provided containing only empty placeholders and documentation.

3. **No Credential Logging**:
   - Authentication tokens, API keys, and session cookies are strictly sanitized from terminal logs, telemetry, and error output.
   - Connection failure messages provide actionable setup guidance without echoing secrets.

---

## 2. Regulatory Compliance & Market Data Rights

### Distinction: Personal Analytical Use vs. Commercial Redistribution

1. **Personal Analytical Use**:
   - Eudaimonia is designed as an analytical terminal interface for an individual trader connecting their personal registered broker credentials (e.g. Zerodha Kite Connect, Upstox, Dhan).
   - Under standard retail broker API terms in India, retail users are granted permission to access real-time data feeds for their own analytical and trading decision-making.

2. **Commercial Redistribution Prohibition**:
   - In accordance with National Stock Exchange of India (NSE) and Bombay Stock Exchange (BSE) regulations, as well as the Securities and Exchange Board of India (SEBI) guidelines:
     - Real-time market data obtained through retail broker APIs may **NOT** be rebroadcast, republished, redistributed to third parties, hosted on public servers, or sub-licensed without an authorized Market Data Vendor Agreement with NSE/BSE.
   - Before distributing, hosting, or providing this terminal to external third-party users, the operator must obtain official exchange vendor agreements.

---

## 3. Order Placement & Trading Boundary

1. **Scope of Initial Version**:
   - Eudaimonia is strictly a market-data and options-analysis terminal, not an automated algorithmic execution bot.
   - Initial versions intentionally omit automated order dispatching to prevent accidental order execution, fat-finger errors, or regulatory violations concerning unapproved algorithmic trading systems under SEBI circulars.

2. **Execution Safety**:
   - Any future order-routing features must implement manual double-confirmation dialogs, strict risk limits, pre-trade quantity validation, and exchange circuit breaker checks.
