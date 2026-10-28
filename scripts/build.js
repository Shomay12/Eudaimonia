/**
 * Production verification and build checker for Eudaimonia website.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");

console.log("[Build] Verifying Eudaimonia website assets...");

const requiredFiles = [
  "index.html",
  "me.html",
  "styles/main.css",
  "js/app.js",
  "js/terminal-engine.js",
  "public/favicon.svg",
  "public/og-image.svg",
  "public/manifest.json",
];

for (const rel of requiredFiles) {
  const full = path.join(ROOT_DIR, rel);
  if (!fs.existsSync(full)) {
    console.error(`[Build Error] Missing required asset: ${rel}`);
    process.exit(1);
  }
  const size = fs.statSync(full).size;
  console.log(`  ✓ ${rel.padEnd(25)} (${size.toLocaleString()} bytes)`);
}

console.log("[Build] Production verification complete. Zero external build dependencies required.");
process.exit(0);

