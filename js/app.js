/**
 * Eudaimonia Application Controller — Experimental Light & Tactile Edition
 * Author & Creator: Shomay Singh Parihar (@shomay12)
 *
 * Implements:
 * - Magnetic buttons with smooth pointer attraction
 * - Touch & pointer draggable instrument token
 * - 3D cursor-aware terminal chassis perspective tilt
 * - Real-time Black-Scholes Greek sensitivity scrubbers
 * - Interactive keyboard navigation playground (press '/' + arrows + Enter)
 * - Complete terminal simulation: Options Chain, Candlestick Chart, 5-Depth Book, Vim prompt
 */

import {
  INITIAL_STATE,
  generateOptionsChain,
  generateCandleBars,
  generateMarketDepth,
  calculateGreeks,
} from "./terminal-engine.js";

export const CREATOR_CONFIG = {
  name: "Shomay Singh Parihar",
  handle: "@shomay12",
  githubUrl: "https://github.com/shomay12",
  personalWebsiteUrl: null, // Configurable: keep null until verified domain is provided
};

class EudaimoniaWebsiteApp {
  constructor() {
    this.state = { ...INITIAL_STATE };
    this.candleBars = generateCandleBars(36, this.state.chartInterval);
    this.chainData = generateOptionsChain(this.state.activeUnderlying, this.state.activeExpiryIndex);
    this.depthData = generateMarketDepth(this.chainData.spot);
  }

  init() {
    this.setupNavigation();
    this.setupTactileInteractions();
    this.setupDraggableToken();
    this.setupTerminalPreview();
    this.setupTerminalKeybindings();
    this.setupCommandLine();
    this.setupKeyboardPlayground();
    this.setupGreekSimulator();
    this.setupCodeBlockCopy();
    this.renderAllScreens();
    this.startClock();
  }

  // ------------------------------------------------------------------------
  // Navigation & Mobile Drawer
  // ------------------------------------------------------------------------
  setupNavigation() {
    const mobileToggle = document.querySelector(".mobile-toggle");
    const navMenu = document.querySelector(".nav-menu");

    if (mobileToggle && navMenu) {
      mobileToggle.addEventListener("click", () => {
        const isExpanded = mobileToggle.getAttribute("aria-expanded") === "true";
        mobileToggle.setAttribute("aria-expanded", String(!isExpanded));
        navMenu.classList.toggle("mobile-open");
        mobileToggle.textContent = !isExpanded ? "[CLOSE]" : "[MENU]";
      });

      navMenu.querySelectorAll(".nav-link").forEach((link) => {
        link.addEventListener("click", () => {
          navMenu.classList.remove("mobile-open");
          mobileToggle.setAttribute("aria-expanded", "false");
          mobileToggle.textContent = "[MENU]";
        });
      });
    }
  }

  // ------------------------------------------------------------------------
  // Tactile Interactions: Magnetic Buttons & 3D Cursor Tilt
  // ------------------------------------------------------------------------
  setupTactileInteractions() {
    // Check prefers-reduced-motion
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    // 1. Magnetic Buttons
    const magneticElements = document.querySelectorAll(".magnetic-wrap");
    magneticElements.forEach((wrap) => {
      wrap.addEventListener("mousemove", (e) => {
        const rect = wrap.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const deltaX = (e.clientX - centerX) * 0.22;
        const deltaY = (e.clientY - centerY) * 0.22;
        wrap.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
      });

      wrap.addEventListener("mouseleave", () => {
        wrap.style.transform = "translate(0px, 0px)";
      });
    });

    // 2. 3D Cursor-Aware Terminal Chassis Tilt
    const heroRight = document.querySelector(".hero-right-col");
    const chassis = document.querySelector(".terminal-chassis");
    if (heroRight && chassis) {
      heroRight.addEventListener("mousemove", (e) => {
        const rect = heroRight.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        const rotateX = -y * 6; // Max 3 deg
        const rotateY = x * 7;
        chassis.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg)`;
      });

      heroRight.addEventListener("mouseleave", () => {
        chassis.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg)";
      });
    }
  }

  // ------------------------------------------------------------------------
  // Draggable Floating Instrument Token
  // ------------------------------------------------------------------------
  setupDraggableToken() {
    const token = document.querySelector(".draggable-token");
    if (!token) return;

    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;

    const onPointerDown = (e) => {
      isDragging = true;
      startX = e.clientX - currentX;
      startY = e.clientY - currentY;
      token.setPointerCapture(e.pointerId);
      token.style.cursor = "grabbing";
      token.style.zIndex = "100";
    };

    const onPointerMove = (e) => {
      if (!isDragging) return;
      currentX = e.clientX - startX;
      currentY = e.clientY - startY;
      token.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
    };

    const onPointerUp = (e) => {
      if (!isDragging) return;
      isDragging = false;
      try {
        token.releasePointerCapture(e.pointerId);
      } catch (err) {
        // Safe fallback
      }
      token.style.cursor = "grab";
    };

    token.addEventListener("pointerdown", onPointerDown);
    token.addEventListener("pointermove", onPointerMove);
    token.addEventListener("pointerup", onPointerUp);
    token.addEventListener("pointercancel", onPointerUp);
  }

  // ------------------------------------------------------------------------
  // Interactive Keyboard Navigation Playground (Focus Section)
  // ------------------------------------------------------------------------
  setupKeyboardPlayground() {
    const searchInput = document.querySelector("#playground-search-input");
    const rows = document.querySelectorAll(".instrument-row");
    let activeIdx = 0;

    if (!searchInput || rows.length === 0) return;

    const setActive = (idx) => {
      rows.forEach((r, i) => {
        if (i === idx) {
          r.classList.add("active");
          r.setAttribute("aria-selected", "true");
        } else {
          r.classList.remove("active");
          r.setAttribute("aria-selected", "false");
        }
      });
      activeIdx = idx;
    };

    rows.forEach((row, i) => {
      row.addEventListener("click", () => {
        setActive(i);
        const sym = row.dataset.symbol;
        if (sym) {
          this.loadInstrumentIntoTerminal(sym);
        }
      });
    });

    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        const next = (activeIdx + 1) % rows.length;
        setActive(next);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const prev = (activeIdx - 1 + rows.length) % rows.length;
        setActive(prev);
      } else if (e.key === "Enter") {
        e.preventDefault();
        const selected = rows[activeIdx];
        if (selected) {
          const sym = selected.dataset.symbol;
          this.loadInstrumentIntoTerminal(sym);
          const feedback = document.querySelector("#playground-status-msg");
          if (feedback) {
            feedback.textContent = `[LOADED] ${sym} dispatched to Terminal Chain`;
          }
        }
      }
    });

    // Global shortcut to focus playground search when '/' is pressed outside an input
    window.addEventListener("keydown", (e) => {
      if (e.key === "/" && document.activeElement !== searchInput && document.activeElement.id !== "cmd-input-field") {
        const playgroundBox = document.querySelector(".interactive-keyboard-box");
        if (playgroundBox) {
          // If in viewport or user pressed slash, focus it
          e.preventDefault();
          searchInput.focus();
        }
      }
    });
  }

  loadInstrumentIntoTerminal(sym) {
    if (sym === "NIFTY" || sym === "BANKNIFTY" || sym === "FINNIFTY") {
      this.state.activeUnderlying = sym;
      this.chainData = generateOptionsChain(sym, this.state.activeExpiryIndex);
      this.renderOptionsChain();
      this.switchScreen("chain");
    } else {
      this.switchScreen("depth");
    }

    const targetLabel = document.querySelector("#footer-active-target");
    if (targetLabel) {
      targetLabel.textContent = sym;
    }
  }

  // ------------------------------------------------------------------------
  // Greek Sensitivity Interactive Slider (Options Card)
  // ------------------------------------------------------------------------
  setupGreekSimulator() {
    const ivSlider = document.querySelector("#greek-iv-slider");
    const ivValLabel = document.querySelector("#greek-iv-val");
    const deltaEl = document.querySelector("#sim-greek-delta");
    const gammaEl = document.querySelector("#sim-greek-gamma");
    const thetaEl = document.querySelector("#sim-greek-theta");
    const vegaEl = document.querySelector("#sim-greek-vega");

    if (!ivSlider) return;

    const updateGreeks = () => {
      const iv = parseFloat(ivSlider.value) / 100.0;
      if (ivValLabel) ivValLabel.textContent = `${ivSlider.value}%`;

      const greeks = calculateGreeks(24850, 24850, 7, 0.065, iv);
      if (deltaEl) deltaEl.textContent = greeks.callDelta.toFixed(2);
      if (gammaEl) gammaEl.textContent = (greeks.gamma * 100).toFixed(3);
      if (thetaEl) thetaEl.textContent = greeks.thetaCall.toFixed(2);
      if (vegaEl) vegaEl.textContent = greeks.vega.toFixed(2);
    };

    ivSlider.addEventListener("input", updateGreeks);
    updateGreeks();
  }

  // ------------------------------------------------------------------------
  // Terminal Preview Screen Tabs
  // ------------------------------------------------------------------------
  setupTerminalPreview() {
    const tabs = document.querySelectorAll(".screen-tab");
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const targetScreen = tab.dataset.screen;
        if (targetScreen === "cmd") {
          this.toggleCommandLine();
        } else if (targetScreen) {
          this.switchScreen(targetScreen);
        }
      });
    });

    const intervalBtns = document.querySelectorAll(".chart-interval-btn");
    intervalBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const intVal = btn.dataset.interval;
        this.setChartInterval(intVal);
      });
    });

    const prevExpiryBtn = document.querySelector("#btn-prev-expiry");
    const nextExpiryBtn = document.querySelector("#btn-next-expiry");
    if (prevExpiryBtn && nextExpiryBtn) {
      prevExpiryBtn.addEventListener("click", () => this.cycleExpiry(-1));
      nextExpiryBtn.addEventListener("click", () => this.cycleExpiry(1));
    }
  }

  switchScreen(screenName) {
    this.state.activeScreen = screenName;

    document.querySelectorAll(".screen-tab").forEach((tab) => {
      if (tab.dataset.screen === screenName) {
        tab.classList.add("active");
        tab.setAttribute("aria-selected", "true");
      } else {
        tab.classList.remove("active");
        tab.setAttribute("aria-selected", "false");
      }
    });

    document.querySelectorAll(".terminal-screen").forEach((screen) => {
      if (screen.id === `screen-${screenName}`) {
        screen.classList.add("active");
      } else {
        screen.classList.remove("active");
      }
    });

    const targetLabel = document.querySelector("#footer-active-target");
    if (targetLabel) {
      targetLabel.textContent = this.state.activeUnderlying;
    }

    if (screenName === "chart") {
      this.renderCandlestickChart();
    }
  }

  cycleExpiry(delta) {
    const total = this.state.expiries.length;
    this.state.activeExpiryIndex = (this.state.activeExpiryIndex + delta + total) % total;
    this.chainData = generateOptionsChain(this.state.activeUnderlying, this.state.activeExpiryIndex);
    this.renderOptionsChain();
  }

  setChartInterval(interval) {
    this.state.chartInterval = interval;
    document.querySelectorAll(".chart-interval-btn").forEach((btn) => {
      if (btn.dataset.interval === interval) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
    this.candleBars = generateCandleBars(36, interval);
    this.renderCandlestickChart();
  }

  // ------------------------------------------------------------------------
  // Global Keyboard Shortcuts (F1-F6, Vim ':', etc.)
  // ------------------------------------------------------------------------
  setupTerminalKeybindings() {
    window.addEventListener("keydown", (e) => {
      const activeEl = document.activeElement;
      const isInput = activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA");

      if (isInput && activeEl.id !== "cmd-input-field") {
        return;
      }

      if (e.key === "Escape") {
        const cmdBar = document.querySelector(".terminal-command-bar");
        if (cmdBar && cmdBar.classList.contains("visible")) {
          e.preventDefault();
          this.closeCommandLine();
          return;
        }
      }

      if (activeEl && activeEl.id === "cmd-input-field") {
        return;
      }

      switch (e.key) {
        case "F1":
          e.preventDefault();
          this.switchScreen("help");
          break;
        case "F2":
          e.preventDefault();
          this.switchScreen("overview");
          break;
        case "F3":
          e.preventDefault();
          this.switchScreen("chain");
          break;
        case "F4":
          e.preventDefault();
          this.switchScreen("depth");
          break;
        case "F5":
          e.preventDefault();
          this.switchScreen("chart");
          break;
        case "F6":
          e.preventDefault();
          this.switchScreen("overview");
          break;
        case ":":
          e.preventDefault();
          this.openCommandLine();
          break;
        case "[":
          if (this.state.activeScreen === "chain") {
            e.preventDefault();
            this.cycleExpiry(-1);
          }
          break;
        case "]":
          if (this.state.activeScreen === "chain") {
            e.preventDefault();
            this.cycleExpiry(1);
          }
          break;
        case "1":
          if (this.state.activeScreen === "chart") {
            e.preventDefault();
            this.setChartInterval("1m");
          }
          break;
        case "3":
          if (this.state.activeScreen === "chart") {
            e.preventDefault();
            this.setChartInterval("3m");
          }
          break;
        case "5":
          if (this.state.activeScreen === "chart") {
            e.preventDefault();
            this.setChartInterval("5m");
          }
          break;
        case "f":
        case "F":
          if (this.state.activeScreen === "chart") {
            e.preventDefault();
            this.setChartInterval("15m");
          }
          break;
        case "d":
        case "D":
          if (this.state.activeScreen === "chart") {
            e.preventDefault();
            this.setChartInterval("1d");
          }
          break;
      }
    });
  }

  // ------------------------------------------------------------------------
  // Command Line Component
  // ------------------------------------------------------------------------
  setupCommandLine() {
    const cmdInput = document.querySelector("#cmd-input-field");
    const cmdFeedback = document.querySelector("#cmd-feedback-text");

    if (!cmdInput) return;

    cmdInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const value = cmdInput.value.trim();
        this.executeCommand(value);
      } else if (e.key === "Escape") {
        e.preventDefault();
        this.closeCommandLine();
      }
    });

    cmdInput.addEventListener("input", (e) => {
      const val = e.target.value.trim().toLowerCase();
      if (!val) {
        cmdFeedback.textContent = "Type 'help' to see all commands. Press ESC to close.";
        return;
      }
      const known = ["chain", "chart", "depth", "overview", "help", "status", "watch", "unwatch", "quit"];
      const matches = known.filter((cmd) => cmd.startsWith(val.split(" ")[0]));
      if (matches.length > 0) {
        cmdFeedback.textContent = `Matches: ${matches.join(", ")}`;
      } else {
        cmdFeedback.textContent = "Unknown command. Type 'help' for reference.";
      }
    });
  }

  openCommandLine() {
    const cmdBar = document.querySelector(".terminal-command-bar");
    const cmdInput = document.querySelector("#cmd-input-field");
    const cmdFeedback = document.querySelector("#cmd-feedback-text");
    if (cmdBar && cmdInput) {
      cmdBar.classList.add("visible");
      cmdInput.value = "";
      cmdInput.focus();
      cmdFeedback.textContent = "Type 'help' for command manual. (e.g. 'chain BANKNIFTY', 'chart 15m')";
    }
  }

  closeCommandLine() {
    const cmdBar = document.querySelector(".terminal-command-bar");
    if (cmdBar) {
      cmdBar.classList.remove("visible");
    }
  }

  toggleCommandLine() {
    const cmdBar = document.querySelector(".terminal-command-bar");
    if (cmdBar && cmdBar.classList.contains("visible")) {
      this.closeCommandLine();
    } else {
      this.openCommandLine();
    }
  }

  executeCommand(rawText) {
    const parts = rawText.split(" ").filter(Boolean);
    if (parts.length === 0) {
      this.closeCommandLine();
      return;
    }

    const cmd = parts[0].toLowerCase();
    const arg = parts[1] ? parts[1].toUpperCase() : null;

    if (cmd === "chain") {
      if (arg && (arg === "BANKNIFTY" || arg === "NIFTY")) {
        this.state.activeUnderlying = arg;
        this.chainData = generateOptionsChain(arg, this.state.activeExpiryIndex);
        this.renderOptionsChain();
      }
      this.switchScreen("chain");
    } else if (cmd === "chart") {
      if (parts[1]) {
        const intArg = parts[1].toLowerCase();
        if (["1m", "3m", "5m", "15m", "1d"].includes(intArg)) {
          this.setChartInterval(intArg);
        }
      }
      this.switchScreen("chart");
    } else if (cmd === "depth" || cmd === "quote") {
      this.switchScreen("depth");
    } else if (cmd === "overview") {
      this.switchScreen("overview");
    } else if (cmd === "help") {
      this.switchScreen("help");
    } else if (cmd === "quit" || cmd === "exit") {
      this.switchScreen("overview");
    }

    this.closeCommandLine();
  }

  // ------------------------------------------------------------------------
  // Screen Renderers
  // ------------------------------------------------------------------------
  renderAllScreens() {
    this.renderOptionsChain();
    this.renderCandlestickChart();
    this.renderMarketDepth();
    this.renderOverview();
  }

  renderOptionsChain() {
    const spotEl = document.querySelector("#chain-spot-price");
    const undEl = document.querySelector("#chain-underlying-name");
    const expiryEl = document.querySelector("#chain-active-expiry");
    const atmEl = document.querySelector("#metric-atm-strike");
    const pcrOiEl = document.querySelector("#metric-pcr-oi");
    const pcrVolEl = document.querySelector("#metric-pcr-vol");
    const maxPainEl = document.querySelector("#metric-max-pain");
    const tableBody = document.querySelector("#chain-table-body");

    if (!tableBody) return;

    if (spotEl) spotEl.textContent = this.chainData.spot.toLocaleString("en-IN", { minimumFractionDigits: 2 });
    if (undEl) undEl.textContent = `${this.state.activeUnderlying} 50`;
    if (expiryEl) expiryEl.textContent = this.state.expiries[this.state.activeExpiryIndex];
    if (atmEl) atmEl.textContent = this.chainData.atmStrike.toLocaleString("en-IN");
    if (pcrOiEl) pcrOiEl.textContent = this.chainData.pcrOI.toFixed(2);
    if (pcrVolEl) pcrVolEl.textContent = this.chainData.pcrVol.toFixed(2);
    if (maxPainEl) maxPainEl.textContent = this.chainData.maxPain.toLocaleString("en-IN");

    tableBody.innerHTML = "";

    this.chainData.rows.forEach((row) => {
      const tr = document.createElement("tr");
      if (row.isATM) {
        tr.classList.add("row-atm");
      }

      const callClass = row.callMoneyness === "ITM" ? "call-itm" : "";
      const putClass = row.putMoneyness === "ITM" ? "put-itm" : "";

      const callOIChgSign = row.calls.oiChg >= 0 ? "+" : "";
      const putOIChgSign = row.puts.oiChg >= 0 ? "+" : "";
      const callChgColor = row.calls.oiChg >= 0 ? "feed-val-up" : "feed-val-down";
      const putChgColor = row.puts.oiChg >= 0 ? "feed-val-up" : "feed-val-down";

      const atmPill = row.isATM ? `<span class="strike-pill">ATM</span>` : "";

      tr.innerHTML = `
        <td class="${callClass}">${row.calls.oi.toLocaleString("en-IN")}</td>
        <td class="${callClass} ${callChgColor}">${callOIChgSign}${row.calls.oiChg.toLocaleString("en-IN")}</td>
        <td class="${callClass}">${row.calls.volume.toLocaleString("en-IN")}</td>
        <td class="${callClass}">${row.calls.iv.toFixed(1)}%</td>
        <td class="${callClass}">${row.calls.delta.toFixed(2)}</td>
        <td class="${callClass}">${row.calls.bid.toFixed(2)}</td>
        <td class="${callClass}">${row.calls.ask.toFixed(2)}</td>
        <td class="${callClass} feed-val-up font-bold">${row.calls.ltp.toFixed(2)}</td>
        <td class="col-strike">${row.strike}${atmPill}</td>
        <td class="${putClass} feed-val-down font-bold">${row.puts.ltp.toFixed(2)}</td>
        <td class="${putClass}">${row.puts.bid.toFixed(2)}</td>
        <td class="${putClass}">${row.puts.ask.toFixed(2)}</td>
        <td class="${putClass}">${row.puts.delta.toFixed(2)}</td>
        <td class="${putClass}">${row.puts.iv.toFixed(1)}%</td>
        <td class="${putClass}">${row.puts.volume.toLocaleString("en-IN")}</td>
        <td class="${putClass} ${putChgColor}">${putOIChgSign}${row.puts.oiChg.toLocaleString("en-IN")}</td>
        <td class="${putClass}">${row.puts.oi.toLocaleString("en-IN")}</td>
      `;

      // Tactile strike row hover interaction
      tr.addEventListener("mouseenter", () => {
        tr.style.filter = "brightness(1.15)";
      });
      tr.addEventListener("mouseleave", () => {
        tr.style.filter = "none";
      });

      tableBody.appendChild(tr);
    });
  }

  renderCandlestickChart() {
    const container = document.querySelector("#chart-canvas-box");
    if (!container) return;

    const width = container.clientWidth || 720;
    const height = container.clientHeight || 320;
    const padding = { top: 20, right: 60, bottom: 40, left: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const volumeHeight = chartHeight * 0.22;
    const priceHeight = chartHeight - volumeHeight - 15;

    const bars = this.candleBars;
    if (!bars || bars.length === 0) return;

    const minPrice = Math.min(...bars.map((b) => b.low)) - 4;
    const maxPrice = Math.max(...bars.map((b) => b.high)) + 4;
    const maxVolume = Math.max(...bars.map((b) => b.volume)) * 1.15;

    const scaleYPrice = (price) =>
      padding.top + priceHeight - ((price - minPrice) / (maxPrice - minPrice)) * priceHeight;

    const scaleYVolume = (vol) =>
      padding.top + priceHeight + 15 + volumeHeight - (vol / maxVolume) * volumeHeight;

    const barWidth = Math.max(4, Math.floor(chartWidth / bars.length) - 3);

    let svgHtml = `<svg class="chart-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">`;

    const gridSteps = 5;
    for (let i = 0; i <= gridSteps; i++) {
      const priceVal = minPrice + (i / gridSteps) * (maxPrice - minPrice);
      const y = scaleYPrice(priceVal);
      svgHtml += `
        <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#232830" stroke-dasharray="2,2"/>
        <text x="${width - padding.right + 6}" y="${y + 4}" fill="#64748B" font-family="ui-monospace, monospace" font-size="10">${priceVal.toFixed(1)}</text>
      `;
    }

    const volSepY = padding.top + priceHeight + 10;
    svgHtml += `<line x1="${padding.left}" y1="${volSepY}" x2="${width - padding.right}" y2="${volSepY}" stroke="#2A303A"/>`;

    const vwapPoints = bars
      .map((b, idx) => {
        const x = padding.left + idx * (barWidth + 3) + barWidth / 2;
        const y = scaleYPrice(b.vwap);
        return `${x},${y}`;
      })
      .join(" ");

    svgHtml += `<polyline fill="none" stroke="#FBBF24" stroke-width="1.3" stroke-dasharray="3,3" points="${vwapPoints}"/>`;

    bars.forEach((b, idx) => {
      const x = padding.left + idx * (barWidth + 3);
      const centerX = x + barWidth / 2;
      const color = b.isUp ? "#86EFAC" : "#FCA5A5";

      const wickY1 = scaleYPrice(b.high);
      const wickY2 = scaleYPrice(b.low);
      svgHtml += `<line x1="${centerX}" y1="${wickY1}" x2="${centerX}" y2="${wickY2}" stroke="${color}" stroke-width="1"/>`;

      const bodyTop = scaleYPrice(Math.max(b.open, b.close));
      const bodyBottom = scaleYPrice(Math.min(b.open, b.close));
      const bodyHeight = Math.max(2, bodyBottom - bodyTop);
      svgHtml += `<rect x="${x}" y="${bodyTop}" width="${barWidth}" height="${bodyHeight}" fill="${color}"/>`;

      const volY = scaleYVolume(b.volume);
      const volHeight = Math.max(1, padding.top + priceHeight + 15 + volumeHeight - volY);
      svgHtml += `<rect x="${x}" y="${volY}" width="${barWidth}" height="${volHeight}" fill="${color}" opacity="0.35"/>`;

      if (idx % 6 === 0) {
        svgHtml += `<text x="${x}" y="${height - 10}" fill="#64748B" font-family="ui-monospace, monospace" font-size="10">${b.timeStr}</text>`;
      }
    });

    svgHtml += `</svg>`;
    container.innerHTML = svgHtml;

    const hud = document.querySelector("#chart-crosshair-hud");
    container.onmousemove = (e) => {
      const rect = container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left - padding.left;
      const barIdx = Math.floor(mouseX / (barWidth + 3));

      if (barIdx >= 0 && barIdx < bars.length && hud) {
        const b = bars[barIdx];
        hud.textContent = `${b.timeStr} | O: ${b.open.toFixed(2)} H: ${b.high.toFixed(2)} L: ${b.low.toFixed(2)} C: ${b.close.toFixed(2)} Vol: ${(b.volume / 1000).toFixed(0)}K VWAP: ${b.vwap.toFixed(2)}`;
      }
    };
  }

  renderMarketDepth() {
    const bidsTable = document.querySelector("#bids-table-body");
    const asksTable = document.querySelector("#asks-table-body");
    const totalBidQtyEl = document.querySelector("#depth-total-bids");
    const totalAskQtyEl = document.querySelector("#depth-total-asks");

    if (!bidsTable || !asksTable) return;

    if (totalBidQtyEl) totalBidQtyEl.textContent = this.depthData.totalBidQty.toLocaleString("en-IN");
    if (totalAskQtyEl) totalAskQtyEl.textContent = this.depthData.totalAskQty.toLocaleString("en-IN");

    bidsTable.innerHTML = "";
    this.depthData.bids.forEach((b) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="color:#92989F;">${b.orders}</td>
        <td>${b.quantity.toLocaleString("en-IN")}</td>
        <td class="depth-bid">${b.price.toFixed(2)}</td>
      `;
      bidsTable.appendChild(tr);
    });

    asksTable.innerHTML = "";
    this.depthData.asks.forEach((a) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="depth-ask">${a.price.toFixed(2)}</td>
        <td>${a.quantity.toLocaleString("en-IN")}</td>
        <td style="color:#92989F;">${a.orders}</td>
      `;
      asksTable.appendChild(tr);
    });
  }

  renderOverview() {
    const container = document.querySelector("#overview-indices-grid");
    if (!container) return;

    container.innerHTML = "";
    Object.values(this.state.indices).forEach((idx) => {
      const card = document.createElement("div");
      card.className = "overview-index-card";
      const isUp = idx.change >= 0;
      const colorClass = isUp ? "feed-val-up" : "feed-val-down";
      const sign = isUp ? "+" : "";

      card.innerHTML = `
        <div class="overview-card-top">
          <span class="overview-name">${idx.name}</span>
          <span style="font-size:0.7rem; color:#92989F;">${idx.symbol.split(":")[0]}</span>
        </div>
        <div class="overview-ltp font-mono ${colorClass}">${idx.ltp.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
        <div style="font-size:0.78rem;" class="font-mono ${colorClass}">${sign}${idx.change.toFixed(2)} (${sign}${idx.pctChange.toFixed(2)}%)</div>
      `;
      container.appendChild(card);
    });
  }

  startClock() {
    const clockEl = document.querySelector("#terminal-live-clock");
    const updateTime = () => {
      const now = new Date();
      const istTime = now.toLocaleTimeString("en-GB", { timeZone: "Asia/Kolkata" });
      if (clockEl) {
        clockEl.textContent = `${istTime} IST`;
      }
    };
    updateTime();
    setInterval(updateTime, 1000);
  }

  setupCodeBlockCopy() {
    const copyBtns = document.querySelectorAll(".copy-key-btn");
    copyBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = btn.dataset.target;
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          navigator.clipboard.writeText(targetEl.innerText).then(() => {
            const originalText = btn.textContent;
            btn.textContent = "[COPIED]";
            setTimeout(() => {
              btn.textContent = originalText;
            }, 2000);
          });
        }
      });
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const app = new EudaimoniaWebsiteApp();
  app.init();
});
