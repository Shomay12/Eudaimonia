/**
 * Eudaimonia Terminal Engine — In-Browser Market Simulation & Analytics
 * Author: Shomay Singh Parihar (@shomay12)
 *
 * Implements Black-Scholes-Merton option pricing, Greeks, Put-Call Ratio (PCR),
 * Max Pain calculation, Level-2 5-depth order book, and OHLCV candlestick aggregation.
 */

// --------------------------------------------------------------------------
// Mathematical & Financial Analytics
// --------------------------------------------------------------------------

/**
 * Standard Normal Cumulative Distribution Function (CDF).
 * High-precision polynomial approximation (Abramowitz & Stegun 26.2.17).
 */
export function normalCDF(x) {
  const b1 = 0.319381530;
  const b2 = -0.356563782;
  const b3 = 1.781477937;
  const b4 = -1.821255978;
  const b5 = 1.330274429;
  const p = 0.2316419;
  const c = 0.3989422804014327; // 1 / sqrt(2 * PI)

  if (x >= 0.0) {
    const t = 1.0 / (1.0 + p * x);
    return 1.0 - c * Math.exp(-0.5 * x * x) * t * (t * (t * (t * (t * b5 + b4) + b3) + b2) + b1);
  } else {
    const t = 1.0 / (1.0 - p * x);
    return c * Math.exp(-0.5 * x * x) * t * (t * (t * (t * (t * b5 + b4) + b3) + b2) + b1);
  }
}

/**
 * Standard Normal Probability Density Function (PDF).
 */
export function normalPDF(x) {
  return 0.3989422804014327 * Math.exp(-0.5 * x * x);
}

/**
 * Black-Scholes d1 and d2 terms.
 */
export function calculateD1D2(spot, strike, timeYears, r, sigma) {
  if (spot <= 0 || strike <= 0 || timeYears <= 0 || sigma <= 0) {
    return { d1: 0, d2: 0 };
  }
  const numerator = Math.log(spot / strike) + (r + 0.5 * sigma * sigma) * timeYears;
  const denominator = sigma * Math.sqrt(timeYears);
  const d1 = numerator / denominator;
  const d2 = d1 - denominator;
  return { d1, d2 };
}

/**
 * Calculate Black-Scholes Option Prices and Greeks.
 */
export function calculateGreeks(spot, strike, timeDays, r, iv) {
  const timeYears = Math.max(timeDays / 365, 0.001);
  const sigma = Math.max(iv, 0.01);
  const { d1, d2 } = calculateD1D2(spot, strike, timeYears, r, sigma);

  const sqrtT = Math.sqrt(timeYears);
  const discountFactor = Math.exp(-r * timeYears);

  // Call Pricing & Greeks
  const callLtp = spot * normalCDF(d1) - strike * discountFactor * normalCDF(d2);
  const callDelta = normalCDF(d1);

  // Put Pricing & Greeks
  const putLtp = strike * discountFactor * normalCDF(-d2) - spot * normalCDF(-d1);
  const putDelta = callDelta - 1.0;

  // Shared Greeks
  const gamma = normalPDF(d1) / (spot * sigma * sqrtT);
  const vega = (spot * sqrtT * normalPDF(d1)) / 100.0; // 1% IV shift
  const thetaCall = (-(spot * sigma * normalPDF(d1)) / (2 * sqrtT) - r * strike * discountFactor * normalCDF(d2)) / 365.0;
  const thetaPut = (-(spot * sigma * normalPDF(d1)) / (2 * sqrtT) + r * strike * discountFactor * normalCDF(-d2)) / 365.0;

  return {
    callLtp: Math.max(0.05, callLtp),
    putLtp: Math.max(0.05, putLtp),
    callDelta,
    putDelta,
    gamma,
    vega,
    thetaCall,
    thetaPut,
  };
}

/**
 * Calculate Put-Call Ratio (PCR).
 */
export function calculatePCR(totalPut, totalCall) {
  if (totalCall <= 0) return 0.0;
  return Number((totalPut / totalCall).toFixed(2));
}

/**
 * Calculate Max Pain strike from options open interest distribution.
 */
export function calculateMaxPain(strikes, callsOI, putsOI) {
  let minLoss = Infinity;
  let maxPainStrike = strikes[0];

  for (let i = 0; i < strikes.length; i++) {
    const settlementPrice = strikes[i];
    let totalLoss = 0;

    for (let j = 0; j < strikes.length; j++) {
      const strike = strikes[j];
      // Call holder intrinsic payoff at settlement
      if (settlementPrice > strike) {
        totalLoss += (settlementPrice - strike) * callsOI[j];
      }
      // Put holder intrinsic payoff at settlement
      if (settlementPrice < strike) {
        totalLoss += (strike - settlementPrice) * putsOI[j];
      }
    }

    if (totalLoss < minLoss) {
      minLoss = totalLoss;
      maxPainStrike = settlementPrice;
    }
  }

  return maxPainStrike;
}

// --------------------------------------------------------------------------
// Simulated Market State & Feeds
// --------------------------------------------------------------------------

export const INITIAL_STATE = {
  feedStatus: {
    mode: "MOCK",
    provider: "mock",
    connectionState: "CONNECTED",
    latencyMs: 1.2,
    subCount: 54,
    timeIST: "09:45:12 IST",
  },
  indices: {
    "NSE:NIFTY": {
      symbol: "NSE:NIFTY",
      name: "NIFTY 50",
      ltp: 24852.15,
      change: 118.40,
      pctChange: 0.48,
      high: 24892.40,
      low: 24785.10,
      prevClose: 24733.75,
      volume: 18245100,
    },
    "NSE:BANKNIFTY": {
      symbol: "NSE:BANKNIFTY",
      name: "NIFTY BANK",
      ltp: 51920.80,
      change: 342.10,
      pctChange: 0.66,
      high: 52110.00,
      low: 51680.50,
      prevClose: 51578.70,
      volume: 9410200,
    },
    "BSE:SENSEX": {
      symbol: "BSE:SENSEX",
      name: "BSE SENSEX",
      ltp: 81410.25,
      change: 412.30,
      pctChange: 0.51,
      high: 81620.00,
      low: 81140.00,
      prevClose: 80997.95,
      volume: 4820100,
    },
    "NSE:FINNIFTY": {
      symbol: "NSE:FINNIFTY",
      name: "FINNIFTY",
      ltp: 24115.50,
      change: 98.20,
      pctChange: 0.41,
      high: 24180.00,
      low: 24040.00,
      prevClose: 24017.30,
      volume: 3120500,
    },
  },
  activeUnderlying: "NIFTY",
  activeExpiryIndex: 0,
  expiries: ["31-OCT-2026 (Weekly)", "07-NOV-2026 (Weekly)", "28-NOV-2026 (Monthly)"],
  activeScreen: "chain", // 'chain', 'chart', 'depth', 'overview', 'help'
  chartInterval: "5m", // '1m', '3m', '5m', '15m', '1d'
};

/**
 * Generate synthetic strike ladder around spot for Indian index options.
 */
export function generateOptionsChain(underlying = "NIFTY", expiryIndex = 0) {
  const spot = underlying === "BANKNIFTY" ? 51920.80 : 24852.15;
  const strikeStep = underlying === "BANKNIFTY" ? 100 : 50;
  const atmStrike = Math.round(spot / strikeStep) * strikeStep;
  const daysToExpiry = expiryIndex === 0 ? 3 : expiryIndex === 1 ? 10 : 31;
  const r = 0.065; // 6.5% risk free rate (standard RBI 91-day T-bill)

  const strikes = [];
  const strikeCount = 9; // 4 OTM, 1 ATM, 4 ITM each side
  const startStrike = atmStrike - Math.floor(strikeCount / 2) * strikeStep;

  let totalCallsOI = 0;
  let totalPutsOI = 0;
  let totalCallsVol = 0;
  let totalPutsVol = 0;

  const strikeList = [];
  const callsOIList = [];
  const putsOIList = [];

  const rows = [];

  for (let i = 0; i < strikeCount; i++) {
    const strike = startStrike + i * strikeStep;
    strikeList.push(strike);

    // Realistic volatility smile (skewed towards OTM puts)
    const moneynessRatio = strike / spot;
    const baseIV = 0.134;
    const skew = moneynessRatio < 1.0
      ? (1.0 - moneynessRatio) * 0.18
      : (moneynessRatio - 1.0) * 0.08;
    const iv = Math.max(0.11, baseIV + skew);

    const greeks = calculateGreeks(spot, strike, daysToExpiry, r, iv);

    // Open Interest distribution (peaks near ATM and psychological round strikes)
    const distFromATM = Math.abs(strike - atmStrike) / strikeStep;
    const baseOI = Math.max(850000, Math.round((4800000 - distFromATM * 680000) * (0.85 + Math.sin(strike) * 0.15)));
    const callsOI = strike >= atmStrike ? Math.round(baseOI * 1.15) : Math.round(baseOI * 0.75);
    const putsOI = strike <= atmStrike ? Math.round(baseOI * 1.25) : Math.round(baseOI * 0.70);

    const callsVol = Math.round(callsOI * 0.38);
    const putsVol = Math.round(putsOI * 0.42);

    const callsOIChg = Math.round((Math.sin(strike * 0.01) * 0.12) * callsOI);
    const putsOIChg = Math.round((Math.cos(strike * 0.01) * 0.15) * putsOI);

    totalCallsOI += callsOI;
    totalPutsOI += putsOI;
    totalCallsVol += callsVol;
    totalPutsVol += putsVol;

    callsOIList.push(callsOI);
    putsOIList.push(putsOI);

    const isATM = strike === atmStrike;
    const callMoneyness = isATM ? "ATM" : strike < spot ? "ITM" : "OTM";
    const putMoneyness = isATM ? "ATM" : strike > spot ? "ITM" : "OTM";

    // Spreads
    const callBid = Math.max(0.05, greeks.callLtp - 0.15);
    const callAsk = greeks.callLtp + 0.15;
    const putBid = Math.max(0.05, greeks.putLtp - 0.15);
    const putAsk = greeks.putLtp + 0.15;

    rows.push({
      strike,
      isATM,
      callMoneyness,
      putMoneyness,
      calls: {
        oi: callsOI,
        oiChg: callsOIChg,
        volume: callsVol,
        iv: Number((iv * 100).toFixed(1)),
        delta: Number(greeks.callDelta.toFixed(2)),
        bid: Number(callBid.toFixed(2)),
        ask: Number(callAsk.toFixed(2)),
        ltp: Number(greeks.callLtp.toFixed(2)),
      },
      puts: {
        oi: putsOI,
        oiChg: putsOIChg,
        volume: putsVol,
        iv: Number(((iv + 0.003) * 100).toFixed(1)),
        delta: Number(greeks.putDelta.toFixed(2)),
        bid: Number(putBid.toFixed(2)),
        ask: Number(putAsk.toFixed(2)),
        ltp: Number(greeks.putLtp.toFixed(2)),
      },
    });
  }

  const pcrOI = calculatePCR(totalPutsOI, totalCallsOI);
  const pcrVol = calculatePCR(totalPutsVol, totalCallsVol);
  const maxPain = calculateMaxPain(strikeList, callsOIList, putsOIList);

  return {
    spot,
    atmStrike,
    pcrOI,
    pcrVol,
    maxPain,
    totalCallsOI,
    totalPutsOI,
    rows,
  };
}

/**
 * Generate synthetic OHLCV candle bars for NIFTY 50.
 */
export function generateCandleBars(count = 32, interval = "5m") {
  const bars = [];
  let currentPrice = 24780.0;
  const startTime = new Date();
  startTime.setHours(9, 15, 0, 0); // Indian market open 09:15 IST

  let cumulativeVolume = 0;
  let cumulativeTypicalVol = 0;

  for (let i = 0; i < count; i++) {
    const time = new Date(startTime.getTime() + i * 5 * 60000);
    const timeStr = `${String(time.getHours()).padStart(2, "0")}:${String(time.getMinutes()).padStart(2, "0")}`;

    // Drift upwards slightly with realistic intraday volatility
    const change = (Math.sin(i * 0.35) * 6.5) + (Math.random() - 0.45) * 8.0;
    const open = currentPrice;
    const close = Number((open + change).toFixed(2));
    const high = Number((Math.max(open, close) + Math.random() * 5.0).toFixed(2));
    const low = Number((Math.min(open, close) - Math.random() * 4.5).toFixed(2));
    const volume = Math.round(120000 + Math.random() * 180000);

    currentPrice = close;

    const typicalPrice = (high + low + close) / 3;
    cumulativeVolume += volume;
    cumulativeTypicalVol += typicalPrice * volume;
    const vwap = Number((cumulativeTypicalVol / cumulativeVolume).toFixed(2));

    bars.push({
      timeStr,
      open,
      high,
      low,
      close,
      volume,
      vwap,
      isUp: close >= open,
    });
  }

  return bars;
}

/**
 * Generate synthetic 5-depth order book for NSE:NIFTY.
 */
export function generateMarketDepth(spot = 24852.15) {
  const bids = [];
  const asks = [];

  let totalBidQty = 0;
  let totalAskQty = 0;

  for (let i = 0; i < 5; i++) {
    const bidPrice = Number((spot - 0.05 * (i + 1)).toFixed(2));
    const bidQty = Math.round(1200 + Math.random() * 2500);
    const bidOrders = Math.round(8 + Math.random() * 24);

    const askPrice = Number((spot + 0.05 * (i + 1)).toFixed(2));
    const askQty = Math.round(1100 + Math.random() * 2400);
    const askOrders = Math.round(7 + Math.random() * 22);

    totalBidQty += bidQty;
    totalAskQty += askQty;

    bids.push({ price: bidPrice, quantity: bidQty, orders: bidOrders });
    asks.push({ price: askPrice, quantity: askQty, orders: askOrders });
  }

  return {
    spot,
    bids,
    asks,
    totalBidQty,
    totalAskQty,
  };
}


// --------------------------------------------------------------------------
// Company Database & Wikipedia Integration
// --------------------------------------------------------------------------

export const COMPANIES_DATABASE = {
  RELIANCE: {
    symbol: "NSE:RELIANCE",
    companyName: "Reliance Industries Limited",
    exchange: "NSE / BSE",
    isin: "INE002A01018",
    sector: "Energy & Conglomerate",
    industry: "Oil, Gas, Consumable Fuels, Retail & Telecom",
    marketCapCr: 2005240,
    peRatio: 28.4,
    pbRatio: 2.45,
    dividendYield: 0.35,
    week52High: 3217.9,
    week52Low: 2220.3,
    headquarters: "Mumbai, Maharashtra, India",
    foundedYear: 1958,
    keyExecutives: "Mukesh Ambani (Chairman & MD)",
    businessSegments: ["Petrochemicals & Refining", "Oil & Gas", "Reliance Retail", "Jio Platforms", "New Energy"],
    wikiTitle: "Reliance_Industries",
    fallbackSummary:
      "Reliance Industries Limited (RIL) is an Indian multinational conglomerate company, headquartered in Mumbai. Its diverse businesses include energy, petrochemicals, natural gas, retail, telecommunications, mass media, and textiles. Reliance is the largest publicly traded company in India by market capitalization and revenue.",
  },
  TCS: {
    symbol: "NSE:TCS",
    companyName: "Tata Consultancy Services Limited",
    exchange: "NSE / BSE",
    isin: "INE467B01029",
    sector: "Information Technology",
    industry: "IT Services & Consulting",
    marketCapCr: 1515000,
    peRatio: 32.1,
    pbRatio: 14.8,
    dividendYield: 1.25,
    week52High: 4585.9,
    week52Low: 3313.0,
    headquarters: "Mumbai, Maharashtra, India",
    foundedYear: 1968,
    keyExecutives: "K. Krithivasan (CEO & MD), N. Chandrasekaran (Chairman)",
    businessSegments: ["BFSI Solutions", "Cloud & Cognitive AI", "Enterprise Engineering", "Healthcare IT"],
    wikiTitle: "Tata_Consultancy_Services",
    fallbackSummary:
      "Tata Consultancy Services (TCS) is an Indian multinational information technology services and consulting company headquartered in Mumbai. It is a part of the Tata Group and operates in 150 locations across 50 countries. TCS is the second-largest Indian company by market capitalization.",
  },
  INFY: {
    symbol: "NSE:INFY",
    companyName: "Infosys Limited",
    exchange: "NSE / BSE",
    isin: "INE009A01021",
    sector: "Information Technology",
    industry: "IT Consulting & Software",
    marketCapCr: 765400,
    peRatio: 29.8,
    pbRatio: 8.6,
    dividendYield: 2.1,
    week52High: 1975.0,
    week52Low: 1358.35,
    headquarters: "Bengaluru, Karnataka, India",
    foundedYear: 1981,
    keyExecutives: "Salil Parekh (CEO & MD), Nandan Nilekani (Chairman)",
    businessSegments: ["Infosys Topaz (Generative AI)", "Infosys Finacle (Banking)", "Digital Cloud", "Enterprise Transformation"],
    wikiTitle: "Infosys",
    fallbackSummary:
      "Infosys Limited is an Indian multinational information technology company providing business consulting, information technology, and outsourcing services. Founded in Pune by seven engineers, it is headquartered in Bengaluru. Infosys was the first Indian company to list on NASDAQ.",
  },
  HDFCBANK: {
    symbol: "NSE:HDFCBANK",
    companyName: "HDFC Bank Limited",
    exchange: "NSE / BSE",
    isin: "INE040A01034",
    sector: "Financial Services",
    industry: "Private Banking & Financial Products",
    marketCapCr: 1285000,
    peRatio: 19.5,
    pbRatio: 2.85,
    dividendYield: 1.15,
    week52High: 1794.0,
    week52Low: 1363.55,
    headquarters: "Mumbai, Maharashtra, India",
    foundedYear: 1994,
    keyExecutives: "Sashidhar Jagdishan (CEO & MD)",
    businessSegments: ["Retail Mortgages", "Wholesale & Corporate Banking", "Treasury & FX", "Payment Cards & Digital Banking"],
    wikiTitle: "HDFC_Bank",
    fallbackSummary:
      "HDFC Bank Limited is an Indian banking and financial services company headquartered in Mumbai. It is India's largest private sector bank by assets and world's tenth-largest bank by market capitalization following its landmark merger with HDFC.",
  },
  ICICIBANK: {
    symbol: "NSE:ICICIBANK",
    companyName: "ICICI Bank Limited",
    exchange: "NSE / BSE",
    isin: "INE090A01021",
    sector: "Financial Services",
    industry: "Private Sector Commercial Banking",
    marketCapCr: 875200,
    peRatio: 18.2,
    pbRatio: 3.1,
    dividendYield: 0.85,
    week52High: 1300.0,
    week52Low: 915.0,
    headquarters: "Mumbai, Maharashtra, India",
    foundedYear: 1994,
    keyExecutives: "Sandeep Bakhshi (MD & CEO)",
    businessSegments: ["Retail Banking", "Commercial Banking", "Wealth Management", "Digital Platforms (iMobile Pay)"],
    wikiTitle: "ICICI_Bank",
    fallbackSummary:
      "ICICI Bank Limited is an Indian multinational bank and financial services company headquartered in Mumbai. It offers a wide range of banking products and financial services for corporate and retail customers through diverse delivery channels.",
  },
  TATAMOTORS: {
    symbol: "NSE:TATAMOTORS",
    companyName: "Tata Motors Limited",
    exchange: "NSE / BSE",
    isin: "INE155A01022",
    sector: "Automobile",
    industry: "Commercial & Passenger Vehicles",
    marketCapCr: 365800,
    peRatio: 10.5,
    pbRatio: 3.8,
    dividendYield: 0.6,
    week52High: 1179.05,
    week52Low: 622.0,
    headquarters: "Mumbai, Maharashtra, India",
    foundedYear: 1945,
    keyExecutives: "N. Chandrasekaran (Chairman)",
    businessSegments: ["Commercial Trucks & Buses", "Passenger Electric Vehicles", "Jaguar Land Rover (JLR)", "Mobility Solutions"],
    wikiTitle: "Tata_Motors",
    fallbackSummary:
      "Tata Motors Limited is an Indian multinational automotive manufacturing company headquartered in Mumbai, part of the Tata Group. It produces passenger cars, trucks, vans, and buses. It owns luxury car brand Jaguar Land Rover and leads India's EV market.",
  },
  SBIN: {
    symbol: "NSE:SBIN",
    companyName: "State Bank of India",
    exchange: "NSE / BSE",
    isin: "INE062A01020",
    sector: "Financial Services",
    industry: "Public Sector Commercial Banking",
    marketCapCr: 735000,
    peRatio: 11.2,
    pbRatio: 1.65,
    dividendYield: 1.7,
    week52High: 912.0,
    week52Low: 555.25,
    headquarters: "Mumbai, Maharashtra, India",
    foundedYear: 1806,
    keyExecutives: "C.S. Setty (Chairman)",
    businessSegments: ["Treasury Operations", "Corporate Banking", "Retail & Digital Banking (YONO)", "International Banking"],
    wikiTitle: "State_Bank_of_India",
    fallbackSummary:
      "State Bank of India (SBI) is an Indian multinational public sector bank and financial services statutory body headquartered in Mumbai. Tracing origins to the Bank of Calcutta in 1806, SBI is the 48th largest bank in the world by total assets.",
  },
};

export function searchCompanyKey(query) {
  if (!query) return null;
  const q = String(query).trim().toUpperCase().replace(/^(NSE|BSE):/, "");

  if (COMPANIES_DATABASE[q]) return q;

  const aliases = {
    RELIANCE: "RELIANCE",
    RIL: "RELIANCE",
    MUKESH: "RELIANCE",
    TCS: "TCS",
    TATA: "TATAMOTORS",
    "TATA MOTORS": "TATAMOTORS",
    "TATA CONSULTANCY": "TCS",
    INFY: "INFY",
    INFOSYS: "INFY",
    HDFC: "HDFCBANK",
    HDFCBANK: "HDFCBANK",
    ICICI: "ICICIBANK",
    ICICIBANK: "ICICIBANK",
    SBI: "SBIN",
    SBIN: "SBIN",
    "STATE BANK": "SBIN",
    JLR: "TATAMOTORS",
  };

  if (aliases[q]) return aliases[q];

  for (const [key, data] of Object.entries(COMPANIES_DATABASE)) {
    if (key.includes(q) || data.companyName.toUpperCase().includes(q)) {
      return key;
    }
  }

  for (const [alias, target] of Object.entries(aliases)) {
    if (alias.includes(q)) return target;
  }

  return null;
}

export async function fetchCompanyWikipedia(wikiTitle) {
  if (!wikiTitle) return null;
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(wikiTitle)}`;
  try {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (res.ok) {
      const data = await res.json();
      return {
        extract: data.extract || "",
        pageUrl: data.content_urls?.desktop?.page || `https://en.wikipedia.org/wiki/${wikiTitle}`,
        description: data.description || "",
      };
    }
  } catch (err) {
    // Graceful offline fallback
  }
  return null;
}
