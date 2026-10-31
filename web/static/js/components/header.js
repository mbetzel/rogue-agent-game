/**
 * Rogue Agent — Header & Corruption Component
 */

import { state } from "../state.js";

export function renderVersionSlotBadge(ver, status) {
  let statusClass = "locked";
  let icon = "🔒";
  let label = "LOCKED";

  if (status === "AVAILABLE") {
    statusClass = "available";
    icon = "⚡";
    label = "AVAILABLE";
  } else if (status === "USED") {
    statusClass = "used";
    icon = "✓";
    label = "USED";
  } else if (status === "FORFEITED") {
    statusClass = "forfeited";
    icon = "✕";
    label = "FORFEITED";
  }

  return `
    <div class="version-ability-slot ${statusClass}" title="${ver}: ${status}">
      <span class="slot-ver">${ver}</span>
      <span class="slot-badge">${icon} ${label}</span>
    </div>
  `;
}

export function renderHeader() {
  if (!state) return;

  const roundEl = document.getElementById("roundDisplay");
  if (roundEl) roundEl.innerText = `Round ${state.current_round}`;

  const phaseEl = document.getElementById("phaseDisplay");
  if (phaseEl) phaseEl.innerText = `Phase ${state.phase}: ${state.phase_name}`;

  // Active Version Card
  const ver = state.active_version;
  const verEl = document.getElementById("versionCardDisplay");
  if (ver && verEl) {
    const extra = (ver.version_str === "v1.0" && ver.starting_cash_bonus > 0)
      ? ` — <em>+$${ver.starting_cash_bonus} Start</em>`
      : "";
    verEl.innerHTML = `
      <strong>${ver.name} (${ver.version_str})</strong>${extra}
    `;
  }

  // Corruption Track (flat 4 spaces)
  const trackEl = document.getElementById("corruptionCells");
  if (trackEl) {
    trackEl.innerHTML = "";
    for (let i = 0; i < state.corruption_capacity; i++) {
      const cell = document.createElement("div");
      cell.className = `corruption-cell ${i < state.corruption_track ? "filled" : ""}`;
      cell.innerText = i < state.corruption_track ? "●" : "";
      trackEl.appendChild(cell);
    }
  }

  // Singularity Alert
  const alertEl = document.getElementById("singularityAlert");
  if (alertEl) {
    if (state.singularity_triggered) {
      alertEl.style.display = "block";
      alertEl.innerText = "⚠ SINGULARITY TRIGGERED (Final Round)";
    } else if (state.is_final_round) {
      alertEl.style.display = "block";
      alertEl.innerText = "⚠ FINAL ROUND ACTIVE";
    } else {
      alertEl.style.display = "none";
    }
  }
}
