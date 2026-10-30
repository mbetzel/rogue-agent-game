/**
 * Rogue Agent — Player Mats & Dice Tray Component
 */

import { state, selectedRerollIndices, patchCashSelected } from "../state.js";
import { doDebugUnlock, doPatch } from "../api.js";
import { renderVersionSlotBadge } from "./header.js";

let renderAppCallback = null;

export function setPlayerMatsRenderCallback(fn) {
  renderAppCallback = fn;
}

function requestRender() {
  if (typeof renderAppCallback === "function") {
    renderAppCallback();
  }
}

export function renderPlayerMats() {
  if (!state || !state.players) return;

  const container = document.getElementById("playersContainer");
  if (!container) return;
  container.innerHTML = "";

  state.players.forEach((p) => {
    const isTurn = (p.player_id === state.active_player_index && state.phase === 3);
    const mat = document.createElement("div");
    mat.className = `player-mat ${isTurn ? "active-turn" : ""} ${p.is_patient_zero ? "patient-zero" : ""}`;

    // CISO indicator
    const isCISO = (p.player_id === state.first_player_index);

    mat.innerHTML = `
      <div class="player-header">
        <div class="player-name">
          ${p.name} ${p.is_human ? '<span style="font-size: 0.7rem; color: var(--text-highlight);">[HUMAN]</span>' : `<span style="font-size: 0.7rem; color: var(--text-dim);">[${p.bot_archetype || 'BOT'}]</span>`}
          ${p.archetype ? `<span class="archetype-tag">${p.archetype.name}</span>` : ''}
          ${isCISO ? '<span class="ciso-badge">CISO</span>' : ''}
          <span class="reboot-badge ${p.system_reboot_used ? 'reboot-used' : 'reboot-ready'}">${p.system_reboot_used ? '[REBOOT USED]' : '[REBOOT READY]'}</span>
        </div>
        <div style="font-size: 0.85rem; font-weight: 700; color: var(--accent-gold);">
          ${p.portfolio_value} VP
        </div>
      </div>

      <div class="player-resources">
        <div class="resource-pill" style="color: #4ade80;">$${p.money}</div>
        <div class="resource-pill" style="color: var(--color-blue);">${p.secrets} Secrets</div>
        <div class="resource-pill" style="color: var(--color-green);">${p.patches} 🔧</div>
        ${p.is_patient_zero ? '<div class="resource-pill" style="color: #ff0055; font-weight: 800;">BREACHED</div>' : ''}
      </div>

      ${p.archetype ? `
        <div class="player-archetype-card">
          <div class="archetype-card-header">
            <div class="archetype-name">${p.archetype.name}</div>
            <div class="archetype-timing-badge">${p.archetype.timing_window}</div>
          </div>
          <div class="archetype-ability-row">
            <span class="archetype-ability-name">${p.archetype.ability_name}:</span>
            <span class="archetype-ability-desc">${p.archetype.description}</span>
          </div>
          <div class="version-ability-track">
            <span class="track-label">Ability Track:</span>
            <div class="track-slots">
              ${renderVersionSlotBadge("v1.0", p.ability_v1_status)}
              ${renderVersionSlotBadge("v2.0", p.ability_v2_status)}
              ${renderVersionSlotBadge("v3.0", p.ability_v3_status)}
            </div>
          </div>
        </div>
      ` : ''}

      <div class="dice-zones-container">
        <!-- Ready Zone -->
        <div class="dice-zone">
          <div class="zone-label">Ready Zone (${p.ready_dice.length + (!p.has_rolled && p.contractor_dice ? p.contractor_dice.length : 0)})</div>
          <div class="dice-tray" id="ready_tray_${p.player_id}"></div>
        </div>

        <!-- Rolled Pool -->
        <div class="dice-zone">
          <div class="zone-label">Rolled Active Pool (${p.rolled_pool.length})</div>
          <div class="dice-tray" id="rolled_tray_${p.player_id}"></div>
        </div>

        <!-- Shield Slots (visible in Phase 1 and 2 during defense configuration and compile) -->
        <div class="shield-slots-row" style="${state.phase >= 3 ? 'display: none;' : ''}">
          <div class="shield-slot red">
            <div class="shield-slot-title" style="color: var(--color-red);">Red (${p.shield_slots.red.length})</div>
            <div id="shields_red_${p.player_id}"></div>
          </div>
          <div class="shield-slot blue">
            <div class="shield-slot-title" style="color: var(--color-blue);">Blue (${p.shield_slots.blue.length})</div>
            <div id="shields_blue_${p.player_id}"></div>
          </div>
          <div class="shield-slot green">
            <div class="shield-slot-title" style="color: var(--color-green);">Green (${p.shield_slots.green.length})</div>
            <div id="shields_green_${p.player_id}"></div>
          </div>
        </div>

        <!-- Unpatched Zone -->
        <div class="dice-zone">
          <div class="zone-label">Unpatched Zone (${p.unpatched_dice.length})</div>
          <div class="dice-tray" id="unpatched_tray_${p.player_id}"></div>
        </div>
      </div>
    `;

    container.appendChild(mat);

    // Populate Dice in Zones
    const readyTray = document.getElementById(`ready_tray_${p.player_id}`);
    p.ready_dice.forEach((d) => {
      const chip = document.createElement("div");
      chip.className = `die-chip ${d.color}`;
      chip.innerHTML = `<span>${d.color.toUpperCase()}</span>`;
      readyTray.appendChild(chip);
    });
    if (!p.has_rolled && p.contractor_dice) {
      p.contractor_dice.forEach((d) => {
        const chip = document.createElement("div");
        chip.className = `die-chip ${d.color}`;
        chip.innerHTML = `<span>${d.color.toUpperCase()} <span class="badge-contractor">CONTRACTOR</span></span>`;
        readyTray.appendChild(chip);
      });
    }

    const rolledTray = document.getElementById(`rolled_tray_${p.player_id}`);
    p.rolled_pool.forEach((d, idx) => {
      const chip = document.createElement("div");
      const isLocked = Boolean(d.is_locked);
      const isContractor = Boolean(d.is_contractor || d.color === "white");
      const isGlitch = Boolean(d.current_face && d.current_face.is_glitch);
      const isSelectedReroll = selectedRerollIndices.has(idx);

      chip.className = `die-chip ${d.color} ${isLocked ? "locked" : ""} ${isGlitch ? "glitch" : ""} ${isSelectedReroll ? "selected-reroll" : ""}`;
      const faceName = d.current_face ? d.current_face.name : "Unrolled";

      const isChoice = Boolean(d.current_face && d.current_face.is_choice);
      let badgeHtml = "";
      if (isContractor) badgeHtml += `<span class="badge-contractor">CONTRACTOR</span> `;
      if (isLocked) badgeHtml += `<span class="badge-locked">🔒 LOCKED</span> `;
      if (isGlitch) badgeHtml += `<span class="badge-glitch">⚠️ GLITCH</span> `;
      if (isChoice) badgeHtml += `<span class="badge-choice">CHOICE</span> `;

      let faceNameDisplay = faceName;
      if (d.effective_face && d.chosen_choice_index !== null && d.chosen_choice_index !== undefined) {
        faceNameDisplay += ` [→ ${d.effective_face.name}]`;
      }

      chip.innerHTML = `
        <div style="display: flex; gap: 4px; align-items: center;">
          <span>${d.color.toUpperCase()}</span>
          ${badgeHtml}
        </div>
        <span class="die-face-name">${faceNameDisplay}</span>
      `;

      if (p.is_human && state.phase === 1 && !p.has_committed) {
        const canProdigyReroll = Boolean(
          p.archetype && p.archetype.code === "PRODIGY" &&
          (Boolean(state.action_capabilities && state.action_capabilities.can_prodigy) ||
           p.ability_v1_status === "AVAILABLE" || p.ability_v2_status === "AVAILABLE" || p.ability_v3_status === "AVAILABLE")
        );

        if (!isLocked && (p.rerolls_remaining || 0) > 0) {
          chip.classList.add("clickable");
          chip.title = "Click to toggle for Yahtzee reroll";
          chip.onclick = () => {
            if (selectedRerollIndices.has(idx)) {
              selectedRerollIndices.delete(idx);
            } else {
              selectedRerollIndices.add(idx);
            }
            requestRender();
          };
        } else if (isLocked && canProdigyReroll && (p.rerolls_remaining || 0) > 0) {
          chip.classList.add("clickable");
          chip.title = "⚡ Prodigy: Click to include locked die in Brute-Force Bypass reroll";
          chip.onclick = () => {
            if (selectedRerollIndices.has(idx)) {
              selectedRerollIndices.delete(idx);
            } else {
              selectedRerollIndices.add(idx);
            }
            requestRender();
          };
        } else if (isLocked && p.patches > 0) {
          chip.classList.add("clickable");
          chip.title = "Click to spend 1 🔧 and Debug Unlock this die";
          chip.onclick = () => doDebugUnlock(idx);
        }
      }
      rolledTray.appendChild(chip);
    });

    // Shield Slots
    ["red", "blue", "green"].forEach((c) => {
      const slotEl = document.getElementById(`shields_${c}_${p.player_id}`);
      if (slotEl && p.shield_slots && p.shield_slots[c]) {
        p.shield_slots[c].forEach((d) => {
          const item = document.createElement("div");
          item.style.fontSize = "0.7rem";
          item.style.color = `var(--color-${d.color})`;
          item.innerText = `${d.color.toUpperCase()}: ${d.current_face ? d.current_face.name : ''}`;
          slotEl.appendChild(item);
        });
      }
    });

    // Unpatched Zone
    const unpatchedTray = document.getElementById(`unpatched_tray_${p.player_id}`);
    p.unpatched_dice.forEach((d, idx) => {
      const chip = document.createElement("div");
      const canPatchActiveMode = patchCashSelected
        ? Boolean(state.action_capabilities && state.action_capabilities.can_patch_cash)
        : Boolean(state.action_capabilities && state.action_capabilities.can_patch_token);
      const canPatch = (p.is_human && isTurn && canPatchActiveMode);
      chip.className = `die-chip ${d.color} ${canPatch ? "clickable" : ""}`;
      chip.innerHTML = `<span>${d.color.toUpperCase()}</span>`;
      if (canPatch) {
        chip.title = patchCashSelected ? "Click to patch this die ($2 Cash)" : "Click to patch this die (1 🔧 Token)";
        chip.onclick = () => doPatch(idx, patchCashSelected);
      }
      unpatchedTray.appendChild(chip);
    });
  });
}
