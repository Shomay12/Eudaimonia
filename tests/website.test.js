import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  normalCDF,
  normalPDF,
  calculateD1D2,
  calculateGreeks,
  calculatePCR,
  calculateMaxPain,
  generateOptionsChain,
  generateCandleBars,
  generateMarketDepth,
} from "../js/terminal-engine.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");

test("1. Options Chain Math — Black-Scholes-Merton and Greeks", async (t) => {
  await t.test("normalCDF and normalPDF properties", () => {
    assert.strictEqual(normalCDF(0).toFixed(4), "0.5000");
    assert.ok(normalCDF(10) > 0.9999);
    assert.ok(normalCDF(-10) < 0.0001);
    assert.ok(normalPDF(0) > 0.398);
  });

  await t.test("calculateD1D2 returns valid finite terms", () => {
    const { d1, d2 } = calculateD1D2(24850, 24850, 7 / 365, 0.065, 0.135);
    assert.ok(Number.isFinite(d1));
    assert.ok(Number.isFinite(d2));
    assert.ok(d1 > d2);
  });

  await t.test("Greeks obey mathematical constraints (Call Delta, Put Delta, Parity)", () => {
    const spot = 24850;
    const strike = 24850;
    const days = 7;
    const r = 0.065;
    const iv = 0.135;

    const greeks = calculateGreeks(spot, strike, days, r, iv);

    // Call Delta in (0, 1)
    assert.ok(greeks.callDelta > 0.45 && greeks.callDelta < 0.60, `Call delta ${greeks.callDelta} out of expected ATM range`);
    // Put Delta in (-1, 0)
    assert.ok(greeks.putDelta > -0.60 && greeks.putDelta < -0.40, `Put delta ${greeks.putDelta} out of expected ATM range`);
    // Delta relation: Delta_Call - Delta_Put = 1
    assert.ok(Math.abs((greeks.callDelta - greeks.putDelta) - 1.0) < 1e-6);

    // Gamma > 0 and Vega > 0
    assert.ok(greeks.gamma > 0);
    assert.ok(greeks.vega > 0);

    // Put-Call Parity: C - P = S - K * exp(-r * T)
    const T = days / 365;
    const parityDiff = (greeks.callLtp - greeks.putLtp) - (spot - strike * Math.exp(-r * T));
    assert.ok(Math.abs(parityDiff) < 1.0, `Put-call parity discrepancy: ${parityDiff}`);
  });

  await t.test("PCR and Max Pain calculations", () => {
    const pcr = calculatePCR(1200000, 1000000);
    assert.strictEqual(pcr, 1.2);

    const strikes = [24700, 24750, 24800, 24850, 24900];
    const callsOI = [200000, 500000, 1200000, 2500000, 3100000];
    const putsOI = [3000000, 2400000, 1400000, 600000, 100000];

    const maxPain = calculateMaxPain(strikes, callsOI, putsOI);
    assert.ok(strikes.includes(maxPain), "Max pain must be a valid strike");
  });

  await t.test("generateOptionsChain produces full strike ladder", () => {
    const chain = generateOptionsChain("NIFTY", 0);
    assert.ok(chain.rows.length >= 7, "Must contain at least 7 strike rows");
    assert.ok(chain.pcrOI > 0, "PCR OI must be positive");
    assert.ok(chain.maxPain > 0, "Max pain strike must be positive");
    const atmRow = chain.rows.find((r) => r.isATM);
    assert.ok(atmRow, "ATM strike row must exist");
  });
});

test("2. Candle Engine & Market Depth Generators", async (t) => {
  await t.test("generateCandleBars builds consistent OHLCV structure", () => {
    const bars = generateCandleBars(20, "5m");
    assert.strictEqual(bars.length, 20);
    for (const b of bars) {
      assert.ok(b.high >= Math.max(b.open, b.close), "High must be >= max(open, close)");
      assert.ok(b.low <= Math.min(b.open, b.close), "Low must be <= min(open, close)");
      assert.ok(b.volume > 0, "Volume must be positive");
      assert.ok(b.vwap > 0, "VWAP must be positive");
    }
  });

  await t.test("generateMarketDepth builds 5-depth book", () => {
    const depth = generateMarketDepth(24852.15);
    assert.strictEqual(depth.bids.length, 5);
    assert.strictEqual(depth.asks.length, 5);
    assert.ok(depth.bids[0].price < depth.asks[0].price, "Best bid must be strictly less than best ask");
    assert.ok(depth.totalBidQty > 0);
    assert.ok(depth.totalAskQty > 0);
  });
});

test("3. HTML Structure, Copy & Semantic Requirements", () => {
  const html = fs.readFileSync(path.join(ROOT_DIR, "index.html"), "utf-8");

  // Product name
  assert.ok(html.includes("Eudaimonia"), "Must contain product name Eudaimonia");

  // Creator Attribution
  assert.ok(html.includes("Shomay Singh Parihar"), "Must attribute creator Shomay Singh Parihar");
  assert.ok(html.includes("@shomay12"), "Must include creator handle @shomay12");
  assert.ok(html.includes("https://github.com/shomay12"), "Must link to creator profile https://github.com/shomay12");

  // Required Section Copy
  assert.ok(html.includes("The markets,"), "Hero headline part 1 present");
  assert.ok(html.includes("without the noise."), "Hero headline part 2 present");
  assert.ok(html.includes("Eudaimonia is a keyboard-first market intelligence terminal"), "Hero supporting text present");
  assert.ok(html.includes("Clarity is a competitive advantage."), "Philosophy headline present");
  assert.ok(html.includes("Know what you’re looking at."), "Data transparency headline present");
  assert.ok(html.includes("Less interface. More information."), "Ergonomics headline present");
  assert.ok(html.includes("Built in the open."), "Developer access headline present");
  assert.ok(html.includes("A more focused way to read the markets."), "Final CTA headline present");

  // Absolute Design Restrictions
  assert.ok(!html.includes('href="#"'), "Must not contain placeholder href='#' links");
  const emojiRegex = /[\u{1F300}-\u{1F5FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F018}-\u{1F270}]/u;
  assert.ok(!emojiRegex.test(html), "Must not contain emojis");

  // Label DEMO DATA
  assert.ok(html.includes("DEMO DATA"), "Must explicitly label demo data");

  // Tactile Components in DOM
  assert.ok(html.includes("draggable-token"), "Contains draggable instrument token");
  assert.ok(html.includes("magnetic-wrap"), "Contains magnetic button wrappers");
  assert.ok(html.includes("interactive-keyboard-box"), "Contains interactive keyboard playground");
  assert.ok(html.includes("greek-simulator-box"), "Contains interactive Greek sensitivity scrubber");

  // Semantic Landmarks
  assert.ok(html.includes("<header"), "Header element present");
  assert.ok(html.includes("<main"), "Main element present");
  assert.ok(html.includes("<nav"), "Nav element present");
  assert.ok(html.includes("<footer"), "Footer element present");
});

test("4. Light Theme & Tactile Design System Integrity", () => {
  const css = fs.readFileSync(path.join(ROOT_DIR, "styles", "main.css"), "utf-8");

  // Check light theme palette
  assert.ok(css.includes("#F7F5F0") || css.includes("--bg-paper"), "Contains warm paper background");
  assert.ok(css.includes("#121417") || css.includes("--text-ink"), "Contains deep ink typography");
  assert.ok(css.includes("#15803D") || css.includes("--accent-green"), "Contains botanical accent green");
  assert.ok(css.includes("--shadow-button"), "Contains tactile physical shadow tokens");

  // Check Accessibility & Focus
  assert.ok(css.includes(":focus-visible"), "Contains visible focus states");
  assert.ok(css.includes("prefers-reduced-motion"), "Contains prefers-reduced-motion media query");

  // Check Responsive Breakpoints
  assert.ok(css.includes("@media (max-width: 768px)"), "Contains tablet/mobile breakpoint");
  assert.ok(css.includes("@media (max-width: 1024px)"), "Contains desktop/tablet breakpoint");
});
