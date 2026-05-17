/**
 * PC Health Checker – Dashboard JavaScript
 *
 * Security notes:
 *   - Never uses eval()
 *   - Uses textContent (not innerHTML) for user-facing strings
 *   - DOM nodes for warnings are built with createElement()
 *   - No external requests; only fetches from same origin
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────────────────────
const REFRESH_INTERVAL_MS = 5000; // auto-refresh every 5 seconds
const API_ENDPOINT        = "/api/system-health";

// Holds a reference to the interval so we can clear it if needed
let autoRefreshTimer = null;

// Cache the most recent successful API response for the export feature
let lastSnapshot = null;


// ─────────────────────────────────────────────────────────────────────────────
// Utility helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Safely set textContent on an element by ID.
 * Falls back to "N/A" if the element doesn't exist or value is null/undefined.
 */
function setText(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = (value !== null && value !== undefined) ? String(value) : "N/A";
}

/**
 * Remove all badge colour classes and apply a new one.
 */
function setBadge(id, label, colorClass) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = "badge " + (colorClass || "badge-gray");
  el.textContent = label || "–";
}

/**
 * Set a progress bar fill width (0–100) and apply a colour class.
 */
function setProgress(fillId, percent, colorClass) {
  const fill = document.getElementById(fillId);
  if (!fill) return;
  const clamped = Math.min(100, Math.max(0, Number(percent) || 0));
  fill.style.width = clamped + "%";
  fill.className = "progress-fill " + (colorClass || "fill-green");
}

/**
 * Pick a colour class based on a numeric percentage and threshold config.
 * thresholds: [{ max: 70, color: "fill-green" }, { max: 90, color: "fill-yellow" }, ...]
 * The last entry acts as the catch-all.
 */
function pickFillColor(percent, thresholds) {
  const p = Number(percent) || 0;
  for (const t of thresholds) {
    if (p <= t.max) return t.color;
  }
  return thresholds[thresholds.length - 1].color;
}

/**
 * Pick a badge colour class based on a status string.
 */
function statusToBadgeColor(status) {
  const s = (status || "").toLowerCase();
  if (s.includes("normal") || s.includes("good") || s.includes("excellent") || s.includes("fully"))
    return "badge-green";
  if (s.includes("moderate") || s.includes("attention") || s.includes("warning") || s.includes("discharging"))
    return "badge-yellow";
  if (s.includes("high") || s.includes("critical"))
    return "badge-red";
  if (s.includes("charging"))
    return "badge-blue";
  return "badge-gray";
}

/**
 * Pick a fill colour class based on a status string.
 */
function statusToFillColor(status) {
  const s = (status || "").toLowerCase();
  if (s.includes("normal") || s.includes("good") || s.includes("excellent") || s.includes("fully"))
    return "fill-green";
  if (s.includes("moderate") || s.includes("attention") || s.includes("warning"))
    return "fill-yellow";
  if (s.includes("high") || s.includes("critical"))
    return "fill-red";
  if (s.includes("charging"))
    return "fill-blue";
  return "fill-green";
}


// ─────────────────────────────────────────────────────────────────────────────
// State management: show/hide dashboard vs loading vs error
// ─────────────────────────────────────────────────────────────────────────────

function showLoading() {
  document.getElementById("loading-state").classList.remove("hidden");
  document.getElementById("error-state").classList.add("hidden");
  document.getElementById("dashboard").classList.add("hidden");
}

function showError() {
  document.getElementById("loading-state").classList.add("hidden");
  document.getElementById("error-state").classList.remove("hidden");
  document.getElementById("dashboard").classList.add("hidden");
}

function showDashboard() {
  document.getElementById("loading-state").classList.add("hidden");
  document.getElementById("error-state").classList.add("hidden");
  document.getElementById("dashboard").classList.remove("hidden");
}


// ─────────────────────────────────────────────────────────────────────────────
// Render functions – one per major data section
// ─────────────────────────────────────────────────────────────────────────────

function renderCpu(cpu) {
  const pct = cpu.percent;
  setText("cpu-percent", pct);
  setBadge("cpu-badge", cpu.status, statusToBadgeColor(cpu.status));

  const fillColor = pickFillColor(pct, [
    { max: 50, color: "fill-green" },
    { max: 80, color: "fill-yellow" },
    { max: 100, color: "fill-red" },
  ]);
  setProgress("cpu-fill", pct, fillColor);

  const cores = cpu.core_count || "N/A";
  const physical = cpu.physical_cores || "N/A";
  setText("cpu-cores", `${cores} logical cores · ${physical} physical`);
}

function renderMemory(mem) {
  setText("ram-percent", mem.percent);
  setBadge("ram-badge", mem.status, statusToBadgeColor(mem.status));

  const fillColor = pickFillColor(mem.percent, [
    { max: 60, color: "fill-green" },
    { max: 85, color: "fill-yellow" },
    { max: 100, color: "fill-red" },
  ]);
  setProgress("ram-fill", mem.percent, fillColor);

  setText("ram-used",  mem.used);
  setText("ram-total", mem.total);
  setText("ram-free",  mem.available);
}

function renderDisk(disk) {
  setText("disk-percent", disk.percent);
  setBadge("disk-badge", disk.status, statusToBadgeColor(disk.status));

  const fillColor = pickFillColor(disk.percent, [
    { max: 70, color: "fill-green" },
    { max: 90, color: "fill-yellow" },
    { max: 100, color: "fill-red" },
  ]);
  setProgress("disk-fill", disk.percent, fillColor);

  setText("disk-used",  disk.used);
  setText("disk-total", disk.total);
  setText("disk-free",  disk.free);
}

function renderBattery(battery) {
  const content = document.getElementById("battery-content");
  const barWrapper = document.getElementById("battery-bar-wrapper");

  if (!battery.available) {
    // No battery – show the friendly message
    setBadge("battery-badge", "N/A", "badge-gray");
    setText("battery-percent", battery.message || "Not available");
    if (barWrapper) barWrapper.classList.add("hidden");
    setText("battery-meta", "");
    return;
  }

  if (barWrapper) barWrapper.classList.remove("hidden");

  const pct = battery.percent;
  const plugged = battery.plugged;

  setText("battery-percent", pct + "%");
  setBadge("battery-badge", battery.status, statusToBadgeColor(battery.status));

  let fillColor;
  if (plugged) {
    fillColor = "fill-blue"; // charging = blue
  } else {
    fillColor = pickFillColor(pct, [
      { max: 30, color: "fill-red" },
      { max: 60, color: "fill-yellow" },
      { max: 100, color: "fill-green" },
    ]);
  }
  setProgress("battery-fill", pct, fillColor);

  const plugLabel = plugged ? "Power adapter connected" : "Running on battery";
  setText("battery-meta", plugLabel);
}

function renderHealth(health) {
  const score = health.score;
  setText("health-score", score);
  setBadge("health-badge", health.label, statusToBadgeColor(health.label));
  setText("health-label-text", health.label);

  const fillColor = pickFillColor(score, [
    { max: 49, color: "fill-red" },
    { max: 69, color: "fill-orange" },
    { max: 89, color: "fill-yellow" },
    { max: 100, color: "fill-green" },
  ]);
  setProgress("health-fill", score, fillColor);

  // Health summary banner
  const bannerEl = document.getElementById("health-summary-text");
  if (bannerEl) {
    let summary;
    if (score >= 90) {
      summary = "Your system is in excellent condition with no major issues detected.";
    } else if (score >= 70) {
      summary = "Your system is running well. Minor attention may be beneficial.";
    } else if (score >= 50) {
      summary = "Your system needs attention. Review the warnings below for guidance.";
    } else {
      summary = "Your system is in a critical state. Immediate action is recommended.";
    }
    bannerEl.textContent = summary;
  }
}

function renderUptime(system) {
  setText("uptime-value", system.uptime);
  setText("boot-time",    system.boot_time);
  setText("process-count", system.process_count + " running processes");
}

function renderNetwork(network) {
  setText("net-sent",      network.bytes_sent);
  setText("net-recv",      network.bytes_received);
  setText("net-pkts-sent", Number(network.packets_sent).toLocaleString());
  setText("net-pkts-recv", Number(network.packets_received).toLocaleString());
}

function renderSystemInfo(system) {
  setText("sys-os",        system.os);
  setText("sys-version",   system.os_version);
  setText("sys-arch",      system.architecture);
  setText("sys-processor", system.processor);
  setText("sys-hostname",  system.hostname);
  setText("sys-boot",      system.boot_time);
}

/**
 * Call /api/fix/<action> (POST) and update button feedback inline.
 * Uses only safe DOM methods – no innerHTML, no eval.
 */
async function applyFix(action, btn, feedbackEl) {
  // Show "Launching…" state
  btn.disabled = true;
  feedbackEl.textContent = "Launching…";
  feedbackEl.className = "fix-feedback fb-launching";

  try {
    const resp = await fetch("/api/fix/" + encodeURIComponent(action), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await resp.json();

    if (data.success) {
      feedbackEl.textContent = "✔ Launched";
      feedbackEl.className = "fix-feedback fb-done";
      btn.textContent = "Launched ✔";
    } else {
      feedbackEl.textContent = "Error: " + (data.error || "Unknown error");
      feedbackEl.className = "fix-feedback fb-error";
      btn.disabled = false;
    }
  } catch (err) {
    feedbackEl.textContent = "Could not reach server";
    feedbackEl.className = "fix-feedback fb-error";
    btn.disabled = false;
  }

  // Auto-clear the feedback label after 5 seconds
  setTimeout(function () {
    feedbackEl.textContent = "";
    feedbackEl.className = "fix-feedback";
  }, 5000);
}

/**
 * Build the warnings list safely using createElement – no innerHTML.
 * Expects warnings to be an array of objects:
 *   { message, severity, fix_action, fix_label }
 * Also accepts plain strings (backwards-compatible).
 */
function renderWarnings(warnings) {
  const container = document.getElementById("warnings-container");
  if (!container) return;

  // Clear existing children safely
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  (warnings || []).forEach(function (warn) {
    // Support both object shape (new) and plain string (old)
    const isObj    = warn && typeof warn === "object";
    const msg      = isObj ? (warn.message    || "") : String(warn);
    const severity = isObj ? (warn.severity   || "warning") : "warning";
    const action   = isObj ? (warn.fix_action || null) : null;
    const label    = isObj ? (warn.fix_label  || "Fix") : null;

    // Outer row
    const item = document.createElement("div");
    item.classList.add("warning-item");

    if (severity === "ok") {
      item.classList.add("warning-ok");
    } else if (severity === "critical") {
      item.classList.add("warning-critical");
    } else {
      item.classList.add("warning-warn");
    }

    // Message text span
    const textSpan = document.createElement("span");
    textSpan.classList.add("warning-text");
    textSpan.textContent = msg;
    item.appendChild(textSpan);

    // Fix button + feedback (only when there's an action and it's not an ok status)
    if (action && severity !== "ok") {
      const btn = document.createElement("button");
      btn.classList.add("fix-btn");
      btn.textContent = label || "Fix";
      btn.setAttribute("aria-label", label || "Fix");
      btn.setAttribute("type", "button");

      const feedbackEl = document.createElement("span");
      feedbackEl.className = "fix-feedback";

      // Wire up click → applyFix
      btn.addEventListener("click", function () {
        applyFix(action, btn, feedbackEl);
      });

      item.appendChild(btn);
      item.appendChild(feedbackEl);
    }

    container.appendChild(item);
  });
}

function renderTimestamp(timestamp) {
  setText("last-updated", timestamp || "–");
}


// ─────────────────────────────────────────────────────────────────────────────
// Main fetch and render pipeline
// ─────────────────────────────────────────────────────────────────────────────

function renderAll(data) {
  renderCpu(data.cpu || {});
  renderMemory(data.memory || {});
  renderDisk(data.disk || {});
  renderBattery(data.battery || { available: false });
  renderHealth(data.health || { score: 0, label: "Unknown" });
  renderUptime(data.system || {});
  renderNetwork(data.network || {});
  renderSystemInfo(data.system || {});
  renderWarnings(data.warnings || []);
  renderTimestamp(data.timestamp);
}

/**
 * Fetch fresh data from the Flask API and update the dashboard.
 * Called on page load, every 5 s automatically, and on manual refresh.
 */
async function fetchData() {
  // Disable refresh button during fetch
  const btn = document.getElementById("refresh-btn");
  if (btn) btn.disabled = true;

  // Only show the loading overlay on the very first load
  const dashboard = document.getElementById("dashboard");
  const isFirstLoad = dashboard.classList.contains("hidden");
  if (isFirstLoad) showLoading();

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "GET",
      headers: { "Accept": "application/json" },
    });

    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }

    const data = await response.json();
    lastSnapshot = data; // cache for export
    renderAll(data);
    showDashboard();

  } catch (err) {
    console.error("Failed to fetch system data:", err);
    if (isFirstLoad) showError();
    // If dashboard was already visible, keep showing stale data
    // so the user doesn't lose context – just log the error.
  } finally {
    if (btn) btn.disabled = false;
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// Export report feature
// ─────────────────────────────────────────────────────────────────────────────

function exportReport() {
  if (!lastSnapshot) {
    alert("No data available yet. Please wait for the dashboard to load.");
    return;
  }

  const d = lastSnapshot;
  const lines = [
    "PC Health Checker – System Report",
    "Generated: " + (d.timestamp || new Date().toLocaleString()),
    "=".repeat(60),
    "",
    "HEALTH SCORE",
    "  Score : " + (d.health ? d.health.score : "N/A") + " / 100",
    "  Label : " + (d.health ? d.health.label : "N/A"),
    "",
    "CPU",
    "  Usage : " + (d.cpu ? d.cpu.percent : "N/A") + "%",
    "  Status: " + (d.cpu ? d.cpu.status : "N/A"),
    "  Cores : " + (d.cpu ? d.cpu.core_count : "N/A") + " logical / " + (d.cpu ? d.cpu.physical_cores : "N/A") + " physical",
    "",
    "MEMORY (RAM)",
    "  Usage : " + (d.memory ? d.memory.percent : "N/A") + "%",
    "  Total : " + (d.memory ? d.memory.total : "N/A"),
    "  Used  : " + (d.memory ? d.memory.used : "N/A"),
    "  Free  : " + (d.memory ? d.memory.available : "N/A"),
    "",
    "DISK",
    "  Usage : " + (d.disk ? d.disk.percent : "N/A") + "%",
    "  Total : " + (d.disk ? d.disk.total : "N/A"),
    "  Used  : " + (d.disk ? d.disk.used : "N/A"),
    "  Free  : " + (d.disk ? d.disk.free : "