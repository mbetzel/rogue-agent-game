/**
 * Rogue Agent — Web Playtesting Single Page Application
 * Pure vanilla JavaScript interacting with standard library Python backend.
 */

let state = null;
let selectedCommitments = {};
let selectedBacklashIndex = 0;
let patchCashSelected = false;

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

async function startNewGame(numPlayers = 4, customPlayers = null, seed = null) {
  const payload = { num_players: numPlayers };
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

async function doRoll() {
  const newState = await apiCall("/api/game/action/roll", "POST", { player_id: getHumanPlayerId() });
  if (newState) {
    state = newState;
    selectedCommitments = {};
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
  const newState = await apiCall("/api/game/action/commit", "POST", { player_id: getHumanPlayerId(), commitments: selectedCommitments });
  if (newState) {
    state = newState;
    selectedCommitments = {};
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

async function doBuy(color) {
  const newState = await apiCall("/api/game/action/buy", "POST", { player_id: getHumanPlayerId(), color: color });
  if (newState) {
    state = newState;
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

async function doDirtyIncome() {
  const backlashSelect = document.getElementById("dirtyBacklashSelect");
  const backlashIdx = backlashSelect && backlashSelect.value !== ""
    ? parseInt(backlashSelect.value, 10)
    : (selectedBacklashIndex ?? 0);

  const newState = await apiCall("/api/game/action/dirty_income", "POST", {
    player_id: getHumanPlayerId(),
    backlash_die_index: Number.isNaN(backlashIdx) ? 0 : backlashIdx,
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

    const canBuy = state.action_capabilities && state.action_capabilities.can_buy && state.action_capabilities.can_buy[color];

    el.innerHTML = `
      <div class="market-die-info">
        <div class="market-die-title" style="color: var(--color-${color});">
          ${color.toUpperCase()} DIE (${item.stock} left)
        </div>
        <div class="market-die-meta">
          Cost: $${item.cost} | Value: ${item.vp} VP
        </div>
        <div class="market-variant-card">
          ★ ${item.variant ? item.variant.name + ': ' + item.variant.description : 'Standard'}
        </div>
      </div>
      <div>
        <button class="action-btn btn-accent" ${canBuy ? "" : "disabled"} onclick="doBuy('${color}')">
          Buy ($${item.cost})
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
    p.ready_dice.forEach((d, idx) => {
      const chip = document.createElement("div");
      chip.className = `die-chip ${d.color}`;
      chip.innerHTML = `<span>${d.color.toUpperCase()}</span>`;
      readyTray.appendChild(chip);
    });

    const rolledTray = document.getElementById(`rolled_tray_${p.player_id}`);
    const lockedSet = new Set(p.locked_reroll_indices || []);
    p.rolled_pool.forEach((d, idx) => {
      const chip = document.createElement("div");
      const isLocked = lockedSet.has(idx);
      const canHotfix = (p.is_human && state.action_capabilities.can_hotfix && !isLocked);
      chip.className = `die-chip ${d.color} ${canHotfix ? "clickable" : ""} ${isLocked ? "locked" : ""}`;
      if (isLocked) {
        chip.style.opacity = "0.5";
        chip.style.borderStyle = "dashed";
      }
      const faceName = d.current_face ? d.current_face.name : "Unrolled";
      chip.innerHTML = `
        <span>${d.color.toUpperCase()}${isLocked ? " [SPENT]" : ""}</span>
        <span class="die-face-name">${faceName}</span>
      `;
      if (canHotfix) {
        chip.title = "Click to spend 1 🔧 and hotfix reroll this die";
        chip.onclick = () => doHotfix(idx);
      } else if (isLocked) {
        chip.title = "This die was spent as a patch token and is locked from rerolling";
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
    if (caps.can_roll) {
      const btn = document.createElement("button");
      btn.className = "action-btn btn-accent";
      btn.innerText = "Roll Ready Pool";
      btn.onclick = doRoll;
      controls.appendChild(btn);
    }

    if (caps.can_commit) {
      // Clean up stale commitments for dice that are no longer shields (e.g. after reroll)
      const rolled = human.rolled_pool;
      Object.keys(selectedCommitments).forEach((idxStr) => {
        const i = parseInt(idxStr, 10);
        if (!rolled[i] || !rolled[i].current_face || !rolled[i].current_face.is_shield) {
          delete selectedCommitments[idxStr];
        }
      });

      // Build Shield Commitment selectors for rolled shields
      let hasShields = false;

      rolled.forEach((d, idx) => {
        const face = d.current_face;
        if (face && face.is_shield) {
          hasShields = true;
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

            wrap.innerHTML = `<span>Die #${idx + 1} (${d.color}):</span>`;
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
      commitBtn.onclick = doCommit;
      controls.appendChild(commitBtn);
    }
  } else if (state.phase === 2) {
    const compileBtn = document.createElement("button");
    compileBtn.className = "action-btn btn-compile";
    compileBtn.innerText = "COMPILE (Drop Cubes)";
    compileBtn.disabled = !caps.can_compile;
    compileBtn.onclick = doCompile;
    controls.appendChild(compileBtn);
  } else if (state.phase === 3) {
    // Dirty Income with Backlash die selector
    if (caps.can_dirty_income) {
      const dirtyWrap = document.createElement("div");
      dirtyWrap.style.display = "inline-flex";
      dirtyWrap.style.alignItems = "center";
      dirtyWrap.style.gap = "6px";

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
        doDirtyIncome();
      };

      dirtyWrap.appendChild(backlashSelect);
      dirtyWrap.appendChild(dirtyBtn);
      controls.appendChild(dirtyWrap);
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
      b2Btn.innerText = "B2: Deep R&D ($2 -> +1 Secret)";
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
      p3Btn.innerText = `P3: Deflect ${p3Color.toUpperCase()} Cube to Staging`;
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

// Initial Boot
window.addEventListener("DOMContentLoaded", () => {
  refreshState();
});
