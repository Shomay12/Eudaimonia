/**
 * Linting & Design Verification Script for Eudaimonia Website.
 * Enforces quality standards, zero broken links, accessibility, and zero emojis.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");

let errors = 0;

function report(condition, message) {
  if (!condition) {
    console.error(`[FAIL] ${message}`);
    errors++;
  } else {
    console.log(`[PASS] ${message}`);
  }
}

console.log("--- Eudaimonia Website Quality & Lint Check ---");

// 1. Read index.html
const indexPath = path.join(ROOT_DIR, "index.html");
report(fs.existsSync(indexPath), "index.html exists");

const html = fs.readFileSync(indexPath, "utf-8");

// 2. Check no href="#"
const hasHashPlaceholder = /href=["']#["']/i.test(html);
report(!hasHashPlaceholder, "No placeholder href='#' links found in index.html");

// 3. Check for emojis in HTML (Design restriction: absolute restriction against emojis)
// Regex matches common emoji ranges
const emojiRegex = /[\u{1F300}-\u{1F5FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F018}-\u{1F270}\u{2388}\u{2B05}\u{2B06}\u{2B07}\u{2B1B}\u{2B1C}\u{2B50}\u{2B55}]/u;
const hasEmoji = emojiRegex.test(html);
report(!hasEmoji, "No emojis found anywhere in the interface");

// 4. Check Product Identity & Creator Attribution
report(html.includes("Eudaimonia"), "Product name 'Eudaimonia' present and properly capitalized");
report(html.includes("Shomay Singh Parihar"), "Creator 'Shomay Singh Parihar' explicitly credited");
report(html.includes("@shomay12"), "@shomay12 username credited");
report(html.includes("https://github.com/shomay12"), "Verified GitHub profile URL linked");
report(html.includes("shomaysinghparihar.online"), "Personal website URL 'shomaysinghparihar.online' credited");

// 5. Check Section Headlines
const hasHeroHeadline = /The markets,[\s\S]*?without the noise\./i.test(html);
report(hasHeroHeadline, "Hero headline 'The markets, without the noise.' present");
report(html.includes("Clarity is a competitive advantage."), "Philosophy headline 'Clarity is a competitive advantage.' present");
report(html.includes("Know what you’re looking at."), "Data transparency headline 'Know what you’re looking at.' present");
report(html.includes("Less interface. More information."), "Ergonomics headline 'Less interface. More information.' present");
report(html.includes("Built in the open."), "Developer access headline 'Built in the open.' present");
report(html.includes("A more focused way to read the markets."), "Final CTA headline present");

// 6. Check DEMO DATA disclosure
report(html.includes("DEMO DATA"), "DEMO DATA explicitly labeled for simulated market preview");

// 7. Check Accessibility & Landmarks
report(html.includes('<header class="site-header" role="banner">'), "Semantic <header> landmark present");
report(html.includes('<main id="main-content" role="main">'), "Semantic <main> landmark present");
report(html.includes('<footer class="site-footer" role="contentinfo">'), "Semantic <footer> landmark present");
report(html.includes("Skip to main content"), "Accessibility skip link present");

// 8. Check CSS and JS assets
const cssPath = path.join(ROOT_DIR, "styles", "main.css");
report(fs.existsSync(cssPath), "styles/main.css exists");

const jsAppPath = path.join(ROOT_DIR, "js", "app.js");
report(fs.existsSync(jsAppPath), "js/app.js exists");

const jsEnginePath = path.join(ROOT_DIR, "js", "terminal-engine.js");
report(fs.existsSync(jsEnginePath), "js/terminal-engine.js exists");

const faviconPath = path.join(ROOT_DIR, "public", "favicon.svg");
report(fs.existsSync(faviconPath), "public/favicon.svg exists");

const ogImagePath = path.join(ROOT_DIR, "public", "og-image.svg");
report(fs.existsSync(ogImagePath), "public/og-image.svg exists");

if (errors > 0) {
  console.error(`\nLinting finished with ${errors} error(s).`);
  process.exit(1);
} else {
  console.log("\nAll quality & design linting checks passed successfully.");
  process.exit(0);
}

