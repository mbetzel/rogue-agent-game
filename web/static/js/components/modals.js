/**
 * Rogue Agent — Modals & Overlay Component
 */

import { state } from "../state.js";

export function openModal(id) {
  if (id === "versionsModal") {
    renderVersionsModal();
  }
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}

export function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

export function renderGameOverModal() {
  if (!state) return;
  const res = state.final_result;
  if (!res) return;

  const content = document.getElementById("gameOverContent");
  if (!content) return;

  let rows = res.rankings.map((r) => `
    <tr style="border-bottom: 1px solid var(--border-color); text-align: left;">
      <td style="padding: 6px;">#${r.rank}</td>
      <td style="padding: 6px;">${r.bot_name}</td>
      <td style="padding: 6px;">${r.portfolio_value} VP</td>
      <td style="padding: 6px;">${r.overflow_penalties} VP</td>
      <td style="padding: 6px; font-weight: 700; color: var(--accent-gold);">${r.net_score} VP</td>
      <td style="padding: 6px;">${r.is_patient_zero ? '<span style="color: #ff0055;">Breached</span>' : '<span style="color: #00ff88;">Survived</span>'}</td>
    </tr>
  `).join("");

  content.innerHTML = `
    <h2 style="font-size: 1.4rem; color: #fff;">
      ${res.is_total_wipeout ? "💀 TOTAL WIPEOUT" : "🏆 VICTORY: " + res.winner_name}
    </h2>
    <p style="color: var(--text-dim); font-size: 0.85rem;">
      Concluded in Round ${res.total_rounds} | Trigger: ${res.end_reason.toUpperCase()}
    </p>

    <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 10px;">
      <thead>
        <tr style="color: var(--text-dim); border-bottom: 1px solid var(--border-color); text-align: left;">
          <th style="padding: 6px;">Rank</th>
          <th style="padding: 6px;">Corporation</th>
          <th style="padding: 6px;">Raw VP</th>
          <th style="padding: 6px;">Overflow</th>
          <th style="padding: 6px;">Net Score</th>
          <th style="padding: 6px;">Status</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>

    <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
      <button class="action-btn btn-accent" id="btnGameOverNewMatch">
        Start New Match
      </button>
    </div>
  `;

  const newMatchBtn = document.getElementById("btnGameOverNewMatch");
  if (newMatchBtn) {
    newMatchBtn.onclick = () => {
      openModal("newGameModal");
      closeModal("gameOverModal");
    };
  }

  openModal("gameOverModal");
}

export function renderVersionsModal() {
  if (!state || !state.version_deck) return;
  const container = document.getElementById("versionsModalDeck");
  if (!container) return;
  container.innerHTML = "";

  const roundBadge = document.getElementById("versionsModalRoundBadge");
  if (roundBadge) {
    roundBadge.innerText = `Round ${state.current_round}`;
  }

  const is2P = state.players && state.players.length === 2;

  state.version_deck.forEach((ver, idx) => {
    const isActive = idx === state.current_version_index;
    const isCompleted = idx < state.current_version_index;
    const isUpcoming = idx > state.current_version_index;

    const card = document.createElement("div");
    card.className = `version-roadmap-card ${isActive ? "active-version-card" : ""} ${isCompleted ? "completed-version-card" : ""}`;

    // Status badge
    let statusBadgeHtml = "";
    if (isActive) {
      statusBadgeHtml = `<span class="version-status-badge active">● Active (${state.corruption_track}/${state.corruption_capacity})</span>`;
    } else if (isCompleted) {
      statusBadgeHtml = `<span class="version-status-badge completed">✓ Completed</span>`;
    } else {
      statusBadgeHtml = `<span class="version-status-badge upcoming">Upcoming</span>`;
    }

    // Payload
    const payload = ver.staging_payload;
    const isStarting = idx === 0;
    const payloadLabel = isStarting ? "Starting Payload:" : "Upgrade Payload:";

    let cubesHtml = "";
    const colorOrder = ["red", "blue", "green", "black"];
    for (const c of colorOrder) {
      const count = (payload && payload[c]) ? payload[c] : 0;
      if (count > 0) {
        cubesHtml += `<span class="cube-badge ${c}" style="font-size: 0.72rem; padding: 2px 7px;">${isStarting ? "" : "+"}${count} ${c.toUpperCase()}</span>`;
      }
    }
    if (!cubesHtml) {
      cubesHtml = `<span style="font-size: 0.75rem; color: var(--text-dim);">None</span>`;
    }

    // Directive description
    const directiveHtml = `
      <div class="version-directive-section">
        <strong style="color: var(--text-highlight);">Directive:</strong> ${ver.directive_description || "None."}
      </div>
    `;

    // Corruption progress
    let corruptionInfo = "";
    if (isActive) {
      let dots = "";
      for (let i = 0; i < state.corruption_capacity; i++) {
        dots += (i < state.corruption_track) ? "● " : "○ ";
      }
      corruptionInfo = `
        <div class="version-corruption-progress">
          <span style="color: var(--color-red); font-weight: 700;">Corruption:</span>
          <span style="letter-spacing: 2px; color: ${state.corruption_track >= state.corruption_capacity - 1 ? '#ff0055' : 'var(--text-highlight)'}; font-size: 0.85rem;">${dots}</span>
          <span>(${state.corruption_track} / ${state.corruption_capacity})</span>
        </div>
      `;
    } else if (isCompleted) {
      const cap = state.corruption_capacity || 4;
      corruptionInfo = `
        <div class="version-corruption-progress">
          <span style="color: var(--text-dim);">Corruption: ${cap} / ${cap} (Resolved)</span>
        </div>
      `;
    } else {
      const cap = state.corruption_capacity || 4;
      corruptionInfo = `
        <div class="version-corruption-progress">
          <span style="color: var(--text-dim);">Corruption: 0 / ${cap} (Pending)</span>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="version-card-header">
        <span class="version-card-tag">${ver.version_str}</span>
        ${statusBadgeHtml}
      </div>
      <div class="version-card-title">${ver.name}</div>
      <div class="version-payload-section">
        <div class="version-payload-label">${payloadLabel}</div>
        <div class="version-payload-cubes">${cubesHtml}</div>
      </div>
      ${directiveHtml}
      ${corruptionInfo}
    `;

    container.appendChild(card);
  });
}
