# Data Quality & Feed Integrity: Eudaimonia

**Developer**: `KJshomay12`  
**Project**: Eudaimonia (Quaxiom Trade Terminal)

---

## 1. Overview

In financial market terminals, data corruption, stale quotes, or silently dropped sequence events can lead to catastrophic analytical misinterpretations. Eudaimonia incorporates a dedicated `DataQualityMonitor` that validates every incoming event before it enters the `MarketStateEngine`.

---

## 2. Monitored Data Quality Anomaly Types

### 1. Non-Positive / Suspect Price (`SUSPECT_PRICE`)
- **Condition**: $\text{LTP} \le 0$
- **Resolution**:
  - Flagged as `DataQualityStatus.SUSPECT_PRICE`.
  - Rejected from updating `MarketStateEngine.ticks` to avoid corrupting previous valid prices.
  - Anomaly event logged with exchange timestamp and local receipt timestamp.

### 2. Sequence Gaps (`SEQUENCE_GAP`)
- **Condition**: Incoming tick sequence number exceeds expected sequence:
  $$\text{Seq}_{\text{current}} > \text{Seq}_{\text{previous}} + 1$$
- **Resolution**:
  - The number of lost packets is computed:
    $$\text{Lost Count} = \text{Seq}_{\text{current}} - \text{Seq}_{\text{previous}} - 1$$
  - Flagged as `DataQualityStatus.SEQUENCE_GAP`.
  - Logged in internal audit ring buffer.

### 3. Out-Of-Order & Duplicate Events (`OUT_OF_ORDER`)
- **Condition**:
  1. Sequence number decreases or repeats ($\text{Seq}_{\text{current}} \le \text{Seq}_{\text{previous}}$), OR
  2. Exchange timestamp is strictly earlier than the latest known exchange timestamp ($T_{\text{exchange}} < T_{\text{previous}}$).
- **Resolution**:
  - Flagged as `DataQualityStatus.OUT_OF_ORDER`.
  - Out-of-order ticks are discarded from updating the latest market state, preserving temporal integrity.

### 4. Feed Staleness (`STALE`)
- **Condition**:
  $$\Delta t = t_{\text{now}} - t_{\text{last\_receipt}} > \text{EUDAIMONIA\_STALE\_THRESHOLD\_SECONDS}$$
- **Resolution**:
  - The terminal header immediately displays a high-contrast warning banner: `[FEED STALE]`.
  - Quotes in the watchlist and options chain are visually marked as stale.

---

## 3. Reconnection & State Resynchronization

When a network drop or provider disconnection occurs:
1. `FeedStatus.connection_state` transitions from `CONNECTED` to `RECONNECTING` or `ERROR`.
2. Exponential backoff with jitter is applied to prevent thundering herd reconnection storms.
3. Upon reconnection, the provider resubscribes to active watchlist symbols and index benchmarks.
4. Historical candle aggregators are synchronized with the exchange session.
