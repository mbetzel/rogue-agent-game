/**
 * Rogue Agent — Web Playtesting Single Page Application
 * Pure vanilla JavaScript interacting with standard library Python backend.
 */

let state = null;
let selectedCommitments = {};
let selectedBacklashIndex = 0;
let patchCashSelected = false;
let cipherDiscountSelected = false;
let selectedRerollIndices = new Set();
let selectedChoiceDeclarations = {};

// Helper: Render Version Ability Slot Badge
function renderVersionSlotBadge(ver, status) {
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

// API Client Helper
async function apiCall(endpoint, method = "GET", body = null) {
  const options = {
    method: method,
    headers: {
      "Content-Type": "application/json",
    },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(endpoint, options);
    const data = await res.json();
    if (!res.ok || !data.success) {
      const msg = data.error || `HTTP error ${res.status}`;
      alert(`Action Failed: ${msg}`);
      return null;
    }
    return data.state;
  } catch (err) {
    console.error("API error:", err);
    alert(`Network Error: ${err.message}`);
    return null;
  }
}

// State Fetch & Refresh
async function refreshState() {
  const newState = await apiCall("/api/game/state");
  if (newState) {
    state = newState;
    renderApp();
  }
}

// User Actions
function getHumanPlayerId() {
  if (!state || !state.players) return 0;
  const human = state.players.find((p) => p.is_human);
  return human ? human.player_id : (state.active_player_index || 0);
}

async function startNewGame(numPlayers = 4, customPlayers = null, seed = null, randomizeCards = true) {
  const payload = { num_players: numPlayers, randomize_cards: Boolean(randomizeCards) };
  if (customPlayers) payload.players = customPlayers;
  if (seed !== null && seed !== "") payload.seed = parseInt(seed, 10);

  const newState = await apiCall("/api/game/new", "POST", payload);
  if (newState) {
    state = newState;
    selectedCommitments = {};
    renderApp();
    closeModal("newGameModal");
  }
}

async function doHireContractors(count = 1, useOperator = false, buyThird = false) {
  const newState = await apiCall("/api/game/action/hire_contractors", "POST", {
    player_id: getHumanPlayerId(),
    count: count,
    use_operator_ability: Boolean(useOperator),
    buy_third_die: Boolean(buyThird),
  });
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doReroll(useProdigy = false) {
  const indices = Array.from(selectedRerollIndices);
  if (indices.length === 0) return;
  const newState = await apiCall("/api/game/action/reroll", "POST", {
    player_id: getHumanPlayerId(),
    reroll_indices: indices,
    use_prodigy_ability: Boolean(useProdigy),
  });
  if (newState) {
    state = newState;
    selectedRerollIndices.clear();
    renderApp();
  }
}

async function doDebugUnlock(dieIndex) {
  const newState = await apiCall("/api/game/action/debug_unlock", "POST", {
    player_id: getHumanPlayerId(),
    die_index: dieIndex,
  });
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doRoll() {
  const newState = await apiCall("/api/game/action/roll", "POST", { player_id: getHumanPlayerId() });
  if (newState) {
    state = newState;
    selectedCommitments = {};
    selectedRerollIndices.clear();
    renderApp();
  }
}

async function doHotfix(dieIndex) {
  const newState = await apiCall("/api/game/action/hotfix", "POST", { player_id: getHumanPlayerId(), die_index: dieIndex });
  if (newState) {
    state = newState;
    delete selectedCommitments[dieIndex];
    renderApp();
  }
}

async function doCommit() {
  const newState = await apiCall("/api/game/action/commit", "POST", {
    player_id: getHumanPlayerId(),
    commitments: selectedCommitments,
    choice_declarations: selectedChoiceDeclarations,
  });
  if (newState) {
    state = newState;
    selectedCommitments = {};
    selectedChoiceDeclarations = {};
    renderApp();
  }
}

async function doCompile() {
  const newState = await apiCall("/api/game/action/compile", "POST", {});
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doBuy(color, useCipher = false) {
  const newState = await apiCall("/api/game/action/buy", "POST", {
    player_id: getHumanPlayerId(),
    color: color,
    use_cipher_ability: Boolean(useCipher),
  });
  if (newState) {
    state = newState;
    cipherDiscountSelected = false;
    renderApp();
  }
}

async function doPatch(dieIndex, useCash) {
  const newState = await apiCall("/api/game/action/patch", "POST", {
    player_id: getHumanPlayerId(),
    die_index: dieIndex,
    use_cash: useCash,
  });
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doDirtyIncome(useCipher = false) {
  const backlashSelect = document.getElementById("dirtyBacklashSelect");
  const backlashIdx = backlashSelect && backlashSelect.value !== ""
    ? parseInt(backlashSelect.value, 10)
    : (selectedBacklashIndex ?? 0);

  const newState = await apiCall("/api/game/action/dirty_income", "POST", {
    player_id: getHumanPlayerId(),
    backlash_die_index: Number.isNaN(backlashIdx) ? 0 : backlashIdx,
    use_cipher_ability: Boolean(useCipher),
  });
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doPhreaker(count = 2) {
  const newState = await apiCall("/api/game/action/phreaker", "POST", {
    player_id: getHumanPlayerId(),
    count: count,
  });
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doAcoustic(color) {
  const newState = await apiCall("/api/game/action/acoustic", "POST", {
    player_id: getHumanPlayerId(),
    color: color,
  });
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doSpook(dollars) {
  const newState = await apiCall("/api/game/action/spook", "POST", {
    player_id: getHumanPlayerId(),
    dollars: dollars,
  });
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doStarAction(actionType, cubeColor = null) {
  const payload = { player_id: getHumanPlayerId(), action_type: actionType };
  if (cubeColor) payload.cube_color = cubeColor;
  const newState = await apiCall("/api/game/action/star", "POST", payload);
  if (newState) {
    state = newState;
    renderApp();
  }
}

async function doEndTurn() {
  const newState = await apiCall("/api/game/action/end_turn", "POST", { player_id: getHumanPlayerId() });
  if (newState) {
    state = newState;
    renderApp();
  }
}

// Modal Helpers
function openModal(id) {
  if (id === "versionsModal") {
    renderVersionsModal();
  }
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

// Rendering Functions
function renderApp() {
  if (!state) return;

  renderHeader();
  renderCompiler();
  renderMarket();
  renderPlayerMats();
  renderActionDock();
  renderEventLog();
  renderVersionsModal();

  if (state.game_over && state.final_result) {
    renderGameOverModal();
  }
}

function renderHeader() {
  document.getElementById("roundDisplay").innerText = `Round ${state.current_round}`;
  document.getElementById("phaseDisplay").innerText = `Phase ${state.phase}: ${state.phase_name}`;

  // Active Version Card
  const ver = state.active_version;
  document.getElementById("versionCardDisplay").innerHTML = `
    <strong>${ver.name} (${ver.version_str})</strong> — <em>${ver.directive_description}</em>
  `;

  // Corruption Track (flat 4 spaces)
  const trackEl = document.getElementById("corruptionCells");
  trackEl.innerHTML = "";
  for (let i = 0; i < state.corruption_capacity; i++) {
    const cell = document.createElement("div");
    cell.className = `corruption-cell ${i < state.corruption_track ? "filled" : ""}`;
    cell.innerText = i < state.corruption_track ? "●" : "";
    trackEl.appendChild(cell);
  }

  // Singularity Alert
  const alertEl = document.getElementById("singularityAlert");
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

function renderCompiler() {
  // Staging Cup
  const stagingEl = document.getElementById("stagingCupTray");
  stagingEl.innerHTML = `
    <span class="cube-badge red">${state.staging_cup.red} Red</span>
    <span class="cube-badge blue">${state.staging_cup.blue} Blue</span>
    <span class="cube-badge green">${state.staging_cup.green} Green</span>
    <span class="cube-badge black">${state.staging_cup.black} Black</span>
  `;

  // Tower Stuck
  const stuckEl = document.getElementById("towerStuckTray");
  stuckEl.innerHTML = `
    <span class="cube-badge red">${state.tower_stuck_cubes.red}</span>
    <span class="cube-badge blue">${state.tower_stuck_cubes.blue}</span>
    <span class="cube-badge green">${state.tower_stuck_cubes.green}</span>
    <span class="cube-badge black">${state.tower_stuck_cubes.black}</span>
    <span style="font-size: 0.8rem; color: var(--text-dim); margin-left: 6px;">(${state.tower_total_stuck} total stuck)</span>
  `;

  // Last Compile Drop Results
  const resEl = document.getElementById("lastCompileResult");
  if (state.last_compile_result) {
    const res = state.last_compile_result;
    resEl.innerHTML = `
      <div style="font-size: 0.8rem; font-weight: 700; margin-bottom: 4px;">Last Drop (Round ${res.round}):</div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <span class="cube-badge red">Exited: ${res.exited_cubes.red} (Attack: ${res.attack_strengths.red})</span>
        <span class="cube-badge blue">Exited: ${res.exited_cubes.blue} (Attack: ${res.attack_strengths.blue})</span>
        <span class="cube-badge green">Exited: ${res.exited_cubes.green} (Attack: ${res.attack_strengths.green})</span>
        <span class="cube-badge black">Corruption: +${res.exited_cubes.black}</span>
      </div>
    `;
  } else {
    resEl.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-dim);">No compile drop executed yet.</span>`;
  }
}

function renderMarket() {
  const container = document.getElementById("marketContainer");
  container.innerHTML = "";

  const order = ["red", "blue", "green", "yellow", "purple"];
  for (const color of order) {
    const item = state.market[color];
    const el = document.createElement("div");
    el.className = "market-item";

    const baseCanBuy = Boolean(state.action_capabilities && state.action_capabilities.can_buy && state.action_capabilities.can_buy[color]);
    const cipherCanBuy = Boolean(state.action_capabilities && state.action_capabilities.can_cipher_buy && state.action_capabilities.can_cipher_buy[color]);
    const canBuy = cipherDiscountSelected ? cipherCanBuy : baseCanBuy;
    const effectiveCost = cipherDiscountSelected ? Math.max(0, item.cost - 2) : item.cost;

    el.innerHTML = `
      <div class="market-die-info">
        <div class="market-die-title" style="color: var(--color-${color});">
          ${color.toUpperCase()} DIE (${item.stock} left)
        </div>
        <div class="market-die-meta">
          Cost: $${effectiveCost} ${cipherDiscountSelected ? '<span style="color: #c084fc; font-weight: 700;">(-$2 Cipher Arbitrage)</span>' : ''} | Value: ${item.vp} VP
        </div>
        <div class="market-variant-card">
          ${item.variant ? `<span class="variant-code-badge">${item.variant.code}</span> <strong>${item.variant.name}</strong>: ${item.variant.description}` : '★ Standard'}
        </div>
      </div>
      <div>
        <button class="action-btn btn-accent" ${canBuy ? "" : "disabled"} onclick="doBuy('${color}', ${cipherDiscountSelected})">
          Buy ($${effectiveCost}) ${cipherDiscountSelected ? '[⚡ Cipher]' : ''}
        </button>
      </div>
    `;
    container.appendChild(el);
  }
}

function renderPlayerMats() {
  const container = document.getElementById("playersContainer");
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
          <div class="zone-label">Ready Zone (${p.ready_dice.length})</div>
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
    if (p.contractor_dice) {
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
      const isSelectedReroll = selectedRerollIndices.has(idx);

      chip.className = `die-chip ${d.color} ${isLocked ? "locked" : ""} ${isSelectedReroll ? "selected-reroll" : ""}`;
      const faceName = d.current_face ? d.current_face.name : "Unrolled";

      const isChoice = Boolean(d.current_face && d.current_face.is_choice);
      let badgeHtml = "";
      if (isContractor) badgeHtml += `<span class="badge-contractor">CONTRACTOR</span> `;
      if (isLocked) badgeHtml += `<span class="badge-locked">🔒 LOCKED</span> `;
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
            renderApp();
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
            renderApp();
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
      p.shield_slots[c].forEach((d) => {
        const item = document.createElement("div");
        item.style.fontSize = "0.7rem";
        item.style.color = `var(--color-${d.color})`;
        item.innerText = `${d.color.toUpperCase()}: ${d.current_face ? d.current_face.name : ''}`;
        slotEl.appendChild(item);
      });
    });

    // Unpatched Zone
    const unpatchedTray = document.getElementById(`unpatched_tray_${p.player_id}`);
    p.unpatched_dice.forEach((d, idx) => {
      const chip = document.createElement("div");
      const canPatch = (p.is_human && isTurn && (state.action_capabilities.can_patch_cash || state.action_capabilities.can_patch_token));
      chip.className = `die-chip ${d.color} ${canPatch ? "clickable" : ""}`;
      chip.innerHTML = `<span>${d.color.toUpperCase()}</span>`;
      if (canPatch) {
        chip.title = "Click to patch this die";
        chip.onclick = () => doPatch(idx, patchCashSelected);
      }
      unpatchedTray.appendChild(chip);
    });
  });
}

function renderActionDock() {
  const caps = state.action_capabilities || {};
  const controls = document.getElementById("dockControls");
  controls.innerHTML = "";

  const human = state.players.find((p) => p.is_human) || state.players[0];

  if (state.phase === 1) {
    if (caps.can_hire_contractors || caps.can_roll) {
      if (caps.can_hire_contractors) {
        const hireWrap = document.createElement("div");
        hireWrap.style.display = "inline-flex";
        hireWrap.style.alignItems = "center";
        hireWrap.style.gap = "6px";

        const hiredCount = human.hired_contractors || 0;
        const maxHire = state.contractor_max_hire || 3;
        const hireLabel = document.createElement("span");
        hireLabel.style.fontSize = "0.8rem";
        hireLabel.style.color = "var(--text-dim)";
        hireLabel.innerText = `Contractors: ${hiredCount}/${maxHire} (Supply: ${state.contractor_supply})`;

        const prog = state.contractor_cost_progression || [1, 2, 3];
        let nextCost = null;
        if (caps.next_contractor_cost !== undefined && caps.next_contractor_cost !== null) {
          nextCost = caps.next_contractor_cost;
        } else if (human.next_contractor_cost !== undefined && human.next_contractor_cost !== null) {
          nextCost = human.next_contractor_cost;
        } else if (hiredCount < prog.length) {
          nextCost = prog[hiredCount];
        }

        const hireBtn = document.createElement("button");
        hireBtn.className = "action-btn";
        if (hiredCount >= maxHire) {
          hireBtn.innerText = "Max Contractors Hired";
        } else if (nextCost !== null) {
          hireBtn.innerText = `Hire Contractor ($${nextCost})`;
        } else {
          hireBtn.innerText = `Hire Contractor ($${state.contractor_hire_cost || 1})`;
        }
        hireBtn.disabled = !caps.can_hire_contractors;
        hireBtn.onclick = () => doHireContractors(1);

        hireWrap.appendChild(hireLabel);
        hireWrap.appendChild(hireBtn);

        if (caps.can_operator) {
          const opBtn = document.createElement("button");
          opBtn.className = "action-btn";
          opBtn.style.borderColor = "#38bdf8";
          opBtn.style.color = "#38bdf8";
          opBtn.innerText = "⚡ Operator: Redundant Crew (2 Free Contractors)";
          opBtn.onclick = () => doHireContractors(2, true);
          hireWrap.appendChild(opBtn);
        }

        controls.appendChild(hireWrap);
      }

      if (caps.can_roll) {
        const btn = document.createElement("button");
        btn.className = "action-btn btn-accent";
        const poolSize = human.ready_dice.length + (human.contractor_dice ? human.contractor_dice.length : 0);
        btn.innerText = `Roll Active Pool (${poolSize} dice)`;
        btn.onclick = () => {
          selectedRerollIndices.clear();
          doRoll();
        };
        controls.appendChild(btn);
      }
    }

    if (caps.can_commit || caps.can_reroll || caps.can_debug_unlock) {
      const rerollsLeft = human.rerolls_remaining !== undefined ? human.rerolls_remaining : 0;
      const maxRerolls = human.max_rerolls !== undefined ? human.max_rerolls : 2;

      const rerollInfo = document.createElement("span");
      rerollInfo.style.fontSize = "0.8rem";
      rerollInfo.style.color = "#38bdf8";
      rerollInfo.style.fontWeight = "600";
      rerollInfo.innerText = `Rerolls: ${rerollsLeft}/${maxRerolls} left (click dice to select)`;
      controls.appendChild(rerollInfo);

      if (caps.can_reroll && selectedRerollIndices.size > 0) {
        const hasLockedSelected = Array.from(selectedRerollIndices).some((i) => {
          const d = human.rolled_pool[i];
          return d && d.is_locked;
        });
        const rerollBtn = document.createElement("button");
        rerollBtn.className = "action-btn btn-accent";
        if (hasLockedSelected) {
          rerollBtn.style.borderColor = "#38bdf8";
          rerollBtn.innerText = `Reroll Selected (${selectedRerollIndices.size}) [⚡ Prodigy Bypass]`;
          rerollBtn.onclick = () => doReroll(true);
        } else {
          rerollBtn.innerText = `Reroll Selected (${selectedRerollIndices.size})`;
          rerollBtn.onclick = () => doReroll(false);
        }
        controls.appendChild(rerollBtn);
      }

      // Clean up stale commitments and choice declarations for dice that changed after reroll
      const rolled = human.rolled_pool;
      Object.keys(selectedCommitments).forEach((idxStr) => {
        const i = parseInt(idxStr, 10);
        if (!rolled[i] || !rolled[i].current_face || (!rolled[i].current_face.is_shield && !rolled[i].current_face.has_shield_option)) {
          delete selectedCommitments[idxStr];
        }
      });
      Object.keys(selectedChoiceDeclarations).forEach((idxStr) => {
        const i = parseInt(idxStr, 10);
        if (!rolled[i] || !rolled[i].current_face || !rolled[i].current_face.is_choice) {
          delete selectedChoiceDeclarations[idxStr];
        }
      });

      // Build Shield Commitment & Choice selectors for rolled pool
      rolled.forEach((d, idx) => {
        const face = d.current_face;
        if (!face || face.is_glitch) return;

        if (face.is_choice) {
          const wrap = document.createElement("div");
          wrap.style.display = "inline-flex";
          wrap.style.alignItems = "center";
          wrap.style.gap = "4px";
          wrap.style.fontSize = "0.8rem";

          const select = document.createElement("select");
          select.style.padding = "4px 8px";
          select.style.background = "var(--bg-card)";
          select.style.color = "#fff";
          select.style.border = "1px solid var(--border-color)";
          select.style.borderRadius = "4px";

          if (face.has_shield_option) {
            // Blue Face 4: Block 1 Blue vs +1 🔧
            const optShield = document.createElement("option");
            optShield.value = "shield";
            optShield.innerText = "Commit Block 1 Blue";
            const optPatch = document.createElement("option");
            optPatch.value = "patch";
            optPatch.innerText = "Gain +1 🔧 (Resource)";
            select.appendChild(optShield);
            select.appendChild(optPatch);

            if (selectedCommitments[idx] === "blue") {
              select.value = "shield";
              selectedChoiceDeclarations[idx] = 0;
            } else {
              select.value = "patch";
              delete selectedCommitments[idx];
              selectedChoiceDeclarations[idx] = 1;
            }

            select.onchange = (e) => {
              if (e.target.value === "shield") {
                selectedCommitments[idx] = "blue";
                selectedChoiceDeclarations[idx] = 0;
              } else {
                delete selectedCommitments[idx];
                selectedChoiceDeclarations[idx] = 1;
              }
            };
            wrap.innerHTML = `<span style="color: var(--color-blue);">Die #${idx + 1} (Blue Choice):</span>`;
          } else {
            // Gray or Green Choice Face
            const choices = face.choices || [];
            choices.forEach((c, cIdx) => {
              const opt = document.createElement("option");
              opt.value = String(cIdx);
              opt.innerText = c.name;
              select.appendChild(opt);
            });

            const curDecl = selectedChoiceDeclarations[idx] !== undefined ? selectedChoiceDeclarations[idx] : 0;
            select.value = String(curDecl);
            selectedChoiceDeclarations[idx] = curDecl;

            select.onchange = (e) => {
              selectedChoiceDeclarations[idx] = parseInt(e.target.value, 10);
            };

            const colStr = d.color === "gray" ? "#94a3b8" : `var(--color-${d.color})`;
            wrap.innerHTML = `<span style="color: ${colStr};">Die #${idx + 1} (${d.color.toUpperCase()} Choice):</span>`;
          }

          wrap.appendChild(select);
          controls.appendChild(wrap);
        } else if (face.is_shield) {
          const wrap = document.createElement("div");
          wrap.style.display = "inline-flex";
          wrap.style.alignItems = "center";
          wrap.style.gap = "4px";
          wrap.style.fontSize = "0.8rem";

          if (face.star_code === "B2") {
            const select = document.createElement("select");
            select.style.padding = "4px 8px";
            select.style.background = "var(--bg-card)";
            select.style.color = "#fff";
            select.style.border = "1px solid var(--border-color)";
            select.style.borderRadius = "4px";

            const optHold = document.createElement("option");
            optHold.value = "hold";
            optHold.innerText = "Hold for Phase 3 Deep R&D";
            const optCommit = document.createElement("option");
            optCommit.value = "blue";
            optCommit.innerText = "Commit Block 1 Blue";
            select.appendChild(optHold);
            select.appendChild(optCommit);

            if (selectedCommitments[idx] === "blue") {
              select.value = "blue";
            } else {
              select.value = "hold";
              delete selectedCommitments[idx];
            }

            select.onchange = (e) => {
              if (e.target.value === "blue") {
                selectedCommitments[idx] = "blue";
              } else {
                delete selectedCommitments[idx];
              }
            };

            wrap.innerHTML = `<span style="color: var(--color-blue);">Die #${idx + 1} (B2):</span>`;
            wrap.appendChild(select);
          } else if (face.shield_color === "any") {
            const select = document.createElement("select");
            select.style.padding = "4px 8px";
            select.style.background = "var(--bg-card)";
            select.style.color = "#fff";
            select.style.border = "1px solid var(--border-color)";
            select.style.borderRadius = "4px";

            ["blue", "red", "green"].forEach((col) => {
              const opt = document.createElement("option");
              opt.value = col;
              opt.innerText = col.toUpperCase();
              select.appendChild(opt);
            });

            if (!selectedCommitments[idx]) selectedCommitments[idx] = "blue";
            select.value = selectedCommitments[idx];
            select.onchange = (e) => {
              selectedCommitments[idx] = e.target.value;
            };

            const colStr = d.color === "white" ? "#f8fafc" : `var(--color-${d.color})`;
            wrap.innerHTML = `<span style="color: ${colStr};">Die #${idx + 1} (${d.color}):</span>`;
            wrap.appendChild(select);
          } else {
            selectedCommitments[idx] = face.shield_color;
            wrap.innerHTML = `<span style="color: var(--color-${face.shield_color});">Die #${idx + 1} (${face.shield_color.toUpperCase()})</span>`;
          }
          controls.appendChild(wrap);
        }
      });

      const commitBtn = document.createElement("button");
      commitBtn.className = "action-btn btn-accent";
      commitBtn.innerText = "Commit Defenses";
      commitBtn.onclick = () => {
        selectedRerollIndices.clear();
        doCommit();
      };
      controls.appendChild(commitBtn);
    }
  } else if (state.phase === 2) {
    const compileBtn = document.createElement("button");
    compileBtn.className = "action-btn btn-compile";
    compileBtn.innerText = "COMPILE (Drop Cubes)";
    compileBtn.disabled = !caps.can_compile;
    compileBtn.onclick = doCompile;
    controls.appendChild(compileBtn);

    // Archetype Abilities applicable during/after Compile
    if (caps.can_acoustic && state.last_compile_result) {
      const exited = state.last_compile_result.exited_cubes || {};
      const qualifying = ["red", "blue", "green"].filter((c) => (exited[c] || 0) > 0);
      if (qualifying.length > 0) {
        const acWrap = document.createElement("div");
        acWrap.style.display = "inline-flex";
        acWrap.style.alignItems = "center";
        acWrap.style.gap = "6px";

        const acSelect = document.createElement("select");
        acSelect.id = "acousticColorSelect";
        acSelect.style.padding = "4px 8px";
        acSelect.style.background = "var(--bg-card)";
        acSelect.style.color = "#fff";
        acSelect.style.border = "1px solid var(--border-color)";
        acSelect.style.borderRadius = "4px";

        qualifying.forEach((c) => {
          const opt = document.createElement("option");
          opt.value = c;
          opt.innerText = `Remove 1 ${c.toUpperCase()} (${exited[c]} exited)`;
          acSelect.appendChild(opt);
        });

        const acBtn = document.createElement("button");
        acBtn.className = "action-btn";
        acBtn.style.borderColor = "#38bdf8";
        acBtn.style.color = "#38bdf8";
        acBtn.innerText = "⚡ Acoustic: Baffle Echo";
        acBtn.onclick = () => doAcoustic(acSelect.value);

        acWrap.appendChild(acSelect);
        acWrap.appendChild(acBtn);
        controls.appendChild(acWrap);
      }
    }

    if (caps.can_spook && human.money > 0) {
      const spookWrap = document.createElement("div");
      spookWrap.style.display = "inline-flex";
      spookWrap.style.alignItems = "center";
      spookWrap.style.gap = "6px";

      const spookInput = document.createElement("input");
      spookInput.type = "number";
      spookInput.min = "1";
      spookInput.max = String(human.money);
      spookInput.value = "1";
      spookInput.style.width = "50px";
      spookInput.style.padding = "4px 8px";
      spookInput.style.background = "var(--bg-card)";
      spookInput.style.color = "#fff";
      spookInput.style.border = "1px solid var(--border-color)";
      spookInput.style.borderRadius = "4px";

      const spookBtn = document.createElement("button");
      spookBtn.className = "action-btn";
      spookBtn.style.borderColor = "#f59e0b";
      spookBtn.style.color = "#f59e0b";
      spookBtn.innerText = "⚡ Spook: Slush Fund";
      spookBtn.onclick = () => {
        const amt = parseInt(spookInput.value, 10);
        if (!isNaN(amt) && amt > 0) doSpook(amt);
      };

      spookWrap.appendChild(document.createTextNode("Pay $"));
      spookWrap.appendChild(spookInput);
      spookWrap.appendChild(spookBtn);
      controls.appendChild(spookWrap);
    }
  } else if (state.phase === 3) {
    // Dirty Income with Backlash die selector
    if (caps.can_dirty_income || caps.can_cipher_dirty) {
      const dirtyWrap = document.createElement("div");
      dirtyWrap.style.display = "inline-flex";
      dirtyWrap.style.alignItems = "center";
      dirtyWrap.style.gap = "6px";

      if (caps.can_dirty_income) {
        const backlashSelect = document.createElement("select");
        backlashSelect.id = "dirtyBacklashSelect";
        backlashSelect.style.padding = "4px 8px";
        backlashSelect.style.background = "var(--bg-card)";
        backlashSelect.style.color = "#fff";
        backlashSelect.style.border = "1px solid var(--border-color)";
        backlashSelect.style.borderRadius = "4px";

        human.ready_dice.forEach((die, idx) => {
          const opt = document.createElement("option");
          opt.value = idx;
          opt.innerText = `Backlash: #${idx + 1} ${die.color.toUpperCase()}${die.vp ? ' (' + die.vp + 'VP)' : ''}`;
          backlashSelect.appendChild(opt);
        });

        backlashSelect.value = selectedBacklashIndex < human.ready_dice.length ? selectedBacklashIndex : 0;
        backlashSelect.onchange = (e) => {
          selectedBacklashIndex = parseInt(e.target.value, 10);
        };

        const dirtyBtn = document.createElement("button");
        dirtyBtn.className = "action-btn";
        dirtyBtn.style.borderColor = "var(--color-black-glow)";
        dirtyBtn.style.color = "#ff3377";
        dirtyBtn.innerText = "Dirty Income (+$3, -1 Secret)";
        dirtyBtn.onclick = () => {
          selectedBacklashIndex = parseInt(backlashSelect.value, 10);
          doDirtyIncome(false);
        };

        dirtyWrap.appendChild(backlashSelect);
        dirtyWrap.appendChild(dirtyBtn);
      }

      if (caps.can_cipher_dirty) {
        const cipherDirtyBtn = document.createElement("button");
        cipherDirtyBtn.className = "action-btn";
        cipherDirtyBtn.style.borderColor = "#a855f7";
        cipherDirtyBtn.style.color = "#c084fc";
        cipherDirtyBtn.innerText = "⚡ Cipher: Backdoor Siphon (No Backlash)";
        cipherDirtyBtn.onclick = () => doDirtyIncome(true);
        dirtyWrap.appendChild(cipherDirtyBtn);
      }

      controls.appendChild(dirtyWrap);
    }

    // Phreaker Ability: Free Repair
    if (caps.can_phreaker) {
      const phreakBtn = document.createElement("button");
      phreakBtn.className = "action-btn";
      phreakBtn.style.borderColor = "#4ade80";
      phreakBtn.style.color = "#4ade80";
      phreakBtn.innerText = "⚡ Phreaker: Magnetic Splice (Repair 2 Dice Free)";
      phreakBtn.onclick = () => doPhreaker(2);
      controls.appendChild(phreakBtn);
    }

    // Cipher Market Discount Toggle
    const isCipher = Boolean(human.archetype && human.archetype.code === "CIPHER");
    const cipherAvail = Boolean(
      isCipher && (
        (caps.can_cipher_buy && Object.values(caps.can_cipher_buy).some(Boolean)) ||
        caps.can_cipher_dirty ||
        human.ability_v1_status === "AVAILABLE" || human.ability_v2_status === "AVAILABLE" || human.ability_v3_status === "AVAILABLE"
      )
    );
    if (cipherAvail) {
      const cipherToggle = document.createElement("label");
      cipherToggle.style.fontSize = "0.8rem";
      cipherToggle.style.display = "inline-flex";
      cipherToggle.style.alignItems = "center";
      cipherToggle.style.gap = "4px";
      cipherToggle.style.color = "#c084fc";
      cipherToggle.innerHTML = `
        <input type="checkbox" id="cipherDiscountToggle" ${cipherDiscountSelected ? "checked" : ""}>
        ⚡ Cipher: -$2 Market Discount
      `;
      cipherToggle.querySelector("input").onchange = (e) => {
        cipherDiscountSelected = e.target.checked;
        renderMarket();
      };
      controls.appendChild(cipherToggle);
    }

    // Acoustic (if exited cubes remain from last compile)
    if (caps.can_acoustic && state.last_compile_result) {
      const exited = state.last_compile_result.exited_cubes || {};
      const qualifying = ["red", "blue", "green"].filter((c) => (exited[c] || 0) > 0);
      if (qualifying.length > 0) {
        const acWrap = document.createElement("div");
        acWrap.style.display = "inline-flex";
        acWrap.style.alignItems = "center";
        acWrap.style.gap = "6px";

        const acSelect = document.createElement("select");
        acSelect.id = "acousticColorSelectP3";
        acSelect.style.padding = "4px 8px";
        acSelect.style.background = "var(--bg-card)";
        acSelect.style.color = "#fff";
        acSelect.style.border = "1px solid var(--border-color)";
        acSelect.style.borderRadius = "4px";

        qualifying.forEach((c) => {
          const opt = document.createElement("option");
          opt.value = c;
          opt.innerText = `Remove 1 ${c.toUpperCase()} (${exited[c]} exited)`;
          acSelect.appendChild(opt);
        });

        const acBtn = document.createElement("button");
        acBtn.className = "action-btn";
        acBtn.style.borderColor = "#38bdf8";
        acBtn.style.color = "#38bdf8";
        acBtn.innerText = "⚡ Acoustic: Baffle Echo";
        acBtn.onclick = () => doAcoustic(acSelect.value);

        acWrap.appendChild(acSelect);
        acWrap.appendChild(acBtn);
        controls.appendChild(acWrap);
      }
    }

    // Patch Toggle
    const patchToggle = document.createElement("label");
    patchToggle.style.fontSize = "0.8rem";
    patchToggle.style.display = "inline-flex";
    patchToggle.style.alignItems = "center";
    patchToggle.style.gap = "4px";
    patchToggle.innerHTML = `
      <input type="checkbox" id="patchModeToggle" ${patchCashSelected ? "checked" : ""}>
      Use Cash ($2) for Patching
    `;
    patchToggle.querySelector("input").onchange = (e) => {
      patchCashSelected = e.target.checked;
    };
    controls.appendChild(patchToggle);

    // Star abilities
    if (caps.can_star && caps.can_star.B2) {
      const b2Btn = document.createElement("button");
      b2Btn.className = "action-btn";
      b2Btn.innerText = "B2: Deep R&D ($4 -> +1 Secret)";
      b2Btn.onclick = () => doStarAction("B2");
      controls.appendChild(b2Btn);
    }
    if (caps.can_star && caps.can_star.Y1) {
      const y1Btn = document.createElement("button");
      y1Btn.className = "action-btn";
      y1Btn.innerText = "Y1: Algorithmic ($6 -> +1 Secret)";
      y1Btn.onclick = () => doStarAction("Y1");
      controls.appendChild(y1Btn);
    }
    if (caps.can_star && caps.can_star.P1) {
      const p1Wrap = document.createElement("div");
      p1Wrap.style.display = "inline-flex";
      p1Wrap.style.alignItems = "center";
      p1Wrap.style.gap = "4px";

      const p1Select = document.createElement("select");
      p1Select.id = "p1ColorSelect";
      p1Select.style.padding = "4px 8px";
      p1Select.style.background = "var(--bg-card)";
      p1Select.style.color = "#fff";
      p1Select.style.border = "1px solid var(--border-color)";
      p1Select.style.borderRadius = "4px";

      ["red", "blue", "green"].forEach((col) => {
        const opt = document.createElement("option");
        opt.value = col;
        opt.innerText = `${col.toUpperCase()} Cube`;
        p1Select.appendChild(opt);
      });

      const p1Btn = document.createElement("button");
      p1Btn.className = "action-btn";
      p1Btn.innerText = "P1: Inject Attack Cube";
      p1Btn.onclick = () => {
        doStarAction("P1", p1Select.value);
      };

      p1Wrap.appendChild(p1Select);
      p1Wrap.appendChild(p1Btn);
      controls.appendChild(p1Wrap);
    }
    if (caps.can_star && caps.can_star.P3) {
      const p3Color = human.p3_available || "red";
      const p3Btn = document.createElement("button");
      p3Btn.className = "action-btn";
      p3Btn.style.color = `var(--color-${p3Color})`;
      p3Btn.innerText = `P3: Deflect ${p3Color.toUpperCase()} Cube to Staging ($1)`;
      p3Btn.onclick = () => doStarAction("P3", p3Color);
      controls.appendChild(p3Btn);
    }

    // End Turn
    const endTurnBtn = document.createElement("button");
    endTurnBtn.className = "action-btn btn-accent";
    endTurnBtn.innerText = "End Turn";
    endTurnBtn.disabled = !caps.can_end_turn;
    endTurnBtn.onclick = doEndTurn;
    controls.appendChild(endTurnBtn);
  } else if (state.phase === 4) {
    const viewBtn = document.createElement("button");
    viewBtn.className = "action-btn btn-accent";
    viewBtn.innerText = "View Standings";
    viewBtn.onclick = () => openModal("gameOverModal");
    controls.appendChild(viewBtn);
  }
}

function renderEventLog() {
  const container = document.getElementById("eventLog");
  container.innerHTML = "";
  state.event_log.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "log-entry";
    item.innerText = entry;
    container.appendChild(item);
  });
}

function renderGameOverModal() {
  const res = state.final_result;
  if (!res) return;

  const content = document.getElementById("gameOverContent");
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
      <button class="action-btn btn-accent" onclick="openModal('newGameModal'); closeModal('gameOverModal');">
        Start New Match
      </button>
    </div>
  `;

  openModal("gameOverModal");
}

function renderVersionsModal() {
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

    // Payload: If 2P and staging_payload_2p exists, use it
    const payload = (is2P && ver.staging_payload_2p) ? ver.staging_payload_2p : ver.staging_payload;
    const isStarting = idx === 0;
    const payloadLabel = isStarting ? "Starting Payload:" : (is2P && ver.staging_payload_2p ? "Upgrade Payload (2P Scaled):" : "Upgrade Payload:");

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
      corruptionInfo = `
        <div class="version-corruption-progress">
          <span style="color: var(--text-dim);">Corruption: 4 / 4 (Resolved)</span>
        </div>
      `;
    } else {
      corruptionInfo = `
        <div class="version-corruption-progress">
          <span style="color: var(--text-dim);">Corruption: 0 / 4 (Pending)</span>
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

// Initial Boot
window.addEventListener("DOMContentLoaded", () => {
  refreshState();
});
