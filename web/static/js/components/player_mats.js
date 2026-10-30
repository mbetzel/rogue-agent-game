/**
 * Rogue Agent — Player Mats & Consultancy Terminal Component
 * Structured faithfully after Print-and-Play US Letter Consultancy Terminal (01_Player_Boards.pdf)
 */

import {
  state,
  selectedRerollIndices,
  patchCashSelected,
  activePlayerTab,
  setActivePlayerTab,
} from "../state.js";
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

// Full Dossier specs matching pnp/generate_pnp.py CHARACTERS
const CHARACTER_DOSSIERS = {
  ACOUSTIC: {
    code: "ACOUSTIC",
    name: "The Acoustic",
    role: "Pattern Genius // Mainframe Resonance",
    flavor: "Every mainframe hums before it strikes. Listen to the baffles -- you can hear which packet drops next.",
    timing: "P2: STEP 2B DMG",
    abilityName: "Baffle Echo",
    abilityDesc: "When resolving compiler damage, ignore 1 Attack Cube (Red, Blue, or Green) of your choice for yourself this round. Exited cubes remain in tray and recycle as normal.",
    themeColor: "#38bdf8",
  },
  PHREAKER: {
    code: "PHREAKER",
    name: "The Phreaker",
    role: "Hardware Tinkerer // Emergency Relays",
    flavor: "A strip of Mylar splicing tape and a 2600-Hz whistle will fix what ten grand of silicon can't.",
    timing: "P3: OPERATIONS",
    abilityName: "Magnetic Splice",
    abilityDesc: "Move 1 worn die from your Unpatched Zone back to your Ready Zone for free (without spending 🔧 or $).",
    themeColor: "#4ade80",
  },
  PRODIGY: {
    code: "PRODIGY",
    name: "The Prodigy",
    role: "Reckless Hacker // Lock Bypassing",
    flavor: "Locked memory is just a polite suggestion from someone who left debug interrupts enabled.",
    timing: "P1: REROLL STEP",
    abilityName: "Brute-Force Bypass",
    abilityDesc: "During rerolls, include any number of Locked dice in free rerolls without spending 🔧. Turn 1 rolled die to any non-Star face of choice.",
    themeColor: "#f43f5e",
  },
  SPOOK: {
    code: "SPOOK",
    name: "The Spook",
    role: "Ex-Intelligence // OpSec & Slush Funds",
    flavor: "Every breach has a price tag. That's what non-attributable slush accounts are for.",
    timing: "P2: STEP 2B DMG",
    abilityName: "Slush Fund",
    abilityDesc: "Absorb up to 2 Corporate Secret loss (from Blue Spyware or unpaid Red Ransom) for free without paying cash. (Additional loss absorbed at $1/Secret).",
    themeColor: "#a855f7",
  },
  CIPHER: {
    code: "CIPHER",
    name: "The Cipher",
    role: "Mathematician // Algorithmic Arbitrage",
    flavor: "Why pay retail for entropy when SETEC's own arbitrage equations subsidize the upgrade?",
    timing: "P3: OPERATIONS",
    abilityName: "Algorithmic Arbitrage",
    abilityDesc: "In Phase 3, buy 1 Colored Die at a $2 discount (min $0), OR take Backdoor Siphon (Dirty Income) without demoting a Ready die to Unpatched.",
    themeColor: "#00d4ff",
  },
  OPERATOR: {
    code: "OPERATOR",
    name: "The Operator",
    role: "Master Strategist // Contractor Dispatch",
    flavor: "Never burn internal hardware when three night-shift phreakers are waiting by a payphone.",
    timing: "P1: STAFFING",
    abilityName: "Redundant Crew",
    abilityDesc: "In Phase 1 Staffing, hire up to 2 White Contractor Dice for free this round (bypassing progressive costs).",
    themeColor: "#f59e0b",
  },
};

function getDossier(code) {
  if (!code) return null;
  const key = String(code).toUpperCase();
  return CHARACTER_DOSSIERS[key] || null;
}

function renderSchematicSvg(code) {
  const c = String(code || "").toUpperCase();
  if (c === "ACOUSTIC") {
    return `
      <svg viewBox="0 0 200 100" class="schematic-svg">
        <line x1="10" y1="50" x2="190" y2="50" stroke="rgba(56,189,248,0.2)" stroke-dasharray="2,3"/>
        <line x1="100" y1="10" x2="100" y2="90" stroke="rgba(56,189,248,0.2)" stroke-dasharray="2,3"/>
        <circle cx="100" cy="50" r="42" fill="none" stroke="#38bdf8" stroke-width="1" stroke-opacity="0.3" stroke-dasharray="4,3"/>
        <circle cx="100" cy="50" r="28" fill="none" stroke="#38bdf8" stroke-width="1.2" stroke-opacity="0.6"/>
        <circle cx="100" cy="50" r="14" fill="rgba(56,189,248,0.2)" stroke="#38bdf8" stroke-width="1.5"/>
        <circle cx="100" cy="50" r="3.5" fill="#38bdf8"/>
        <path d="M 15 50 Q 35 15, 55 50 T 95 50 T 135 50 T 175 50 T 185 50" fill="none" stroke="#00ffcc" stroke-width="1.4" opacity="0.85"/>
        <text x="100" y="94" fill="#38bdf8" font-size="6.5" font-family="monospace" text-anchor="middle" letter-spacing="1">RESONANCE // BAFFLE ECHO</text>
      </svg>
    `;
  }
  if (c === "PHREAKER") {
    return `
      <svg viewBox="0 0 200 100" class="schematic-svg">
        <circle cx="60" cy="50" r="34" fill="none" stroke="#4ade80" stroke-width="1.2" stroke-dasharray="4,2"/>
        <circle cx="60" cy="50" r="22" fill="none" stroke="#4ade80" stroke-width="1"/>
        <circle cx="60" cy="50" r="7" fill="rgba(74,222,128,0.2)" stroke="#4ade80" stroke-width="1"/>
        <circle cx="60" cy="27" r="3.5" fill="none" stroke="#4ade80" stroke-width="0.9"/>
        <circle cx="76" cy="34" r="3.5" fill="none" stroke="#4ade80" stroke-width="0.9"/>
        <circle cx="82" cy="50" r="3.5" fill="none" stroke="#4ade80" stroke-width="0.9"/>
        <circle cx="76" cy="66" r="3.5" fill="none" stroke="#4ade80" stroke-width="0.9"/>
        <circle cx="60" cy="73" r="3.5" fill="none" stroke="#4ade80" stroke-width="0.9"/>
        <circle cx="44" cy="66" r="3.5" fill="none" stroke="#4ade80" stroke-width="0.9"/>
        <path d="M 110 32 L 180 32 M 110 50 L 185 50 M 110 68 L 175 68" stroke="#4ade80" stroke-width="1.1"/>
        <path d="M 120 22 L 120 78 M 140 22 L 140 78 M 160 22 L 160 78" stroke="rgba(74,222,128,0.3)" stroke-width="0.8" stroke-dasharray="2,2"/>
        <rect x="130" y="40" width="22" height="18" fill="rgba(74,222,128,0.2)" stroke="#4ade80" stroke-width="0.9"/>
        <text x="141" y="52" fill="#4ade80" font-size="6.5" font-family="monospace" text-anchor="middle">2600Hz</text>
        <text x="100" y="94" fill="#4ade80" font-size="6.5" font-family="monospace" text-anchor="middle" letter-spacing="1">RELAY // MAGNETIC SPLICE</text>
      </svg>
    `;
  }
  if (c === "PRODIGY") {
    return `
      <svg viewBox="0 0 200 100" class="schematic-svg">
        <rect x="20" y="16" width="160" height="66" fill="rgba(244,63,94,0.06)" stroke="#f43f5e" stroke-width="1" stroke-dasharray="3,2"/>
        <text x="30" y="32" fill="#f43f5e" font-size="7.5" font-family="monospace">0x00: 01000010 01011001</text>
        <text x="30" y="46" fill="#f43f5e" font-size="7.5" font-family="monospace">0x08: [DEBUG_INTERRUPT_EN]</text>
        <text x="30" y="60" fill="#f43f5e" font-size="7.5" font-family="monospace">0x10: 11010100 00101011</text>
        <text x="30" y="74" fill="#f43f5e" font-size="7.5" font-family="monospace">0x18: [LOCK_MEM_OVERRIDE]</text>
        <path d="M 148 24 L 174 48 L 148 72" fill="none" stroke="#ffd700" stroke-width="1.6"/>
        <text x="100" y="94" fill="#f43f5e" font-size="6.5" font-family="monospace" text-anchor="middle" letter-spacing="1">INT 0x03 // BRUTE-FORCE BYPASS</text>
      </svg>
    `;
  }
  if (c === "SPOOK") {
    return `
      <svg viewBox="0 0 200 100" class="schematic-svg">
        <rect x="20" y="16" width="160" height="66" fill="rgba(168,85,247,0.06)" stroke="#a855f7" stroke-width="1"/>
        <path d="M 55 49 Q 100 22, 145 49 Q 100 76, 55 49 Z" fill="rgba(168,85,247,0.15)" stroke="#a855f7" stroke-width="1.3"/>
        <circle cx="100" cy="49" r="13" fill="none" stroke="#a855f7" stroke-width="1.1"/>
        <circle cx="100" cy="49" r="4.5" fill="#a855f7"/>
        <line x1="100" y1="26" x2="100" y2="72" stroke="#a855f7" stroke-width="0.8" stroke-dasharray="2,2"/>
        <line x1="72" y1="49" x2="128" y2="49" stroke="#a855f7" stroke-width="0.8" stroke-dasharray="2,2"/>
        <rect x="28" y="24" width="36" height="5" fill="#a855f7" opacity="0.6"/>
        <rect x="136" y="68" width="36" height="5" fill="#a855f7" opacity="0.6"/>
        <text x="100" y="94" fill="#a855f7" font-size="6.5" font-family="monospace" text-anchor="middle" letter-spacing="1">CLASSIFIED // SLUSH FUND</text>
      </svg>
    `;
  }
  if (c === "CIPHER") {
    return `
      <svg viewBox="0 0 200 100" class="schematic-svg">
        <path d="M 25 68 Q 65 78, 85 49 T 145 22 T 175 36" fill="none" stroke="#38bdf8" stroke-width="1.4"/>
        <circle cx="85" cy="49" r="3" fill="#38bdf8"/>
        <circle cx="145" cy="22" r="3" fill="#38bdf8"/>
        <text x="36" y="32" fill="#38bdf8" font-size="8" font-family="monospace">y² = x³ + ax + b</text>
        <text x="36" y="47" fill="rgba(56,189,248,0.7)" font-size="7.5" font-family="monospace">p, q ∈ ℙ (mod N)</text>
        <text x="110" y="68" fill="#ffd700" font-size="8.5" font-family="monospace">Δ = -$2 ARB</text>
        <line x1="15" y1="78" x2="185" y2="78" stroke="rgba(56,189,248,0.3)" stroke-width="0.7"/>
        <text x="100" y="94" fill="#38bdf8" font-size="6.5" font-family="monospace" text-anchor="middle" letter-spacing="1">ENTROPY // ALGORITHMIC ARBITRAGE</text>
      </svg>
    `;
  }
  if (c === "OPERATOR") {
    return `
      <svg viewBox="0 0 200 100" class="schematic-svg">
        <rect x="25" y="18" width="150" height="62" fill="rgba(245,158,11,0.06)" stroke="#f59e0b" stroke-width="1"/>
        <circle cx="50" cy="35" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <circle cx="80" cy="35" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <circle cx="110" cy="35" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <circle cx="140" cy="35" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <circle cx="50" cy="58" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <circle cx="80" cy="58" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <circle cx="110" cy="58" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <circle cx="140" cy="58" r="4" fill="none" stroke="#f59e0b" stroke-width="1.1"/>
        <path d="M 50 35 Q 65 75, 110 58" fill="none" stroke="#f59e0b" stroke-width="1.8"/>
        <path d="M 80 35 Q 110 12, 140 58" fill="none" stroke="#ffd700" stroke-width="1.8"/>
        <text x="100" y="94" fill="#f59e0b" font-size="6.5" font-family="monospace" text-anchor="middle" letter-spacing="1">DISPATCH // REDUNDANT CREW</text>
      </svg>
    `;
  }
  return `
    <svg viewBox="0 0 200 100" class="schematic-svg">
      <rect x="25" y="20" width="150" height="60" fill="none" stroke="var(--border-color)" stroke-width="1" stroke-dasharray="3,3"/>
      <circle cx="100" cy="50" r="20" fill="none" stroke="var(--text-dim)" stroke-width="1"/>
      <text x="100" y="94" fill="var(--text-dim)" font-size="6.5" font-family="monospace" text-anchor="middle">MAINFRAME TERMINAL NODE</text>
    </svg>
  `;
}

export function renderPlayerMats() {
  if (!state || !state.players) return;

  const container = document.getElementById("playersContainer");
  if (!container) return;
  container.innerHTML = "";

  const human = state.players.find((p) => p.is_human) || state.players[0];
  const humanId = human ? human.player_id : 0;

  // Resolve currently viewed player tab
  let currentTab = activePlayerTab;
  if (currentTab === "human") {
    currentTab = humanId;
  }

  // 1. Navigation / Switcher Bar at top of player mats section
  const switcherBar = document.createElement("div");
  switcherBar.className = "consultancy-switcher-bar";

  const switcherTitle = document.createElement("div");
  switcherTitle.className = "switcher-title";
  switcherTitle.innerHTML = `<span class="switcher-dot">●</span> CONSULTANCY TERMINALS:`;
  switcherBar.appendChild(switcherTitle);

  const tabsWrap = document.createElement("div");
  tabsWrap.className = "switcher-tabs";

  state.players.forEach((p) => {
    const isSelected = (currentTab !== "all" && Number(currentTab) === p.player_id);
    const isHuman = Boolean(p.is_human);
    const isTurn = (p.player_id === state.active_player_index && state.phase === 3);
    const isCISO = (p.player_id === state.first_player_index);

    const tabBtn = document.createElement("button");
    tabBtn.className = `terminal-tab-btn ${isSelected ? "active" : ""} ${isTurn ? "turn-active" : ""}`;
    tabBtn.innerHTML = `
      <span class="tab-player-icon">${isHuman ? "👤" : "🤖"}</span>
      <span class="tab-player-name">${p.name}</span>
      ${isCISO ? '<span class="tab-ciso-tag">CISO</span>' : ''}
      <span class="tab-vp-badge">${p.portfolio_value} VP</span>
    `;
    tabBtn.onclick = () => {
      setActivePlayerTab(p.player_id);
      requestRender();
    };
    tabsWrap.appendChild(tabBtn);
  });

  // "View All" toggle button
  const allBtn = document.createElement("button");
  const isAllSelected = (currentTab === "all");
  allBtn.className = `terminal-tab-btn ${isAllSelected ? "active" : ""}`;
  allBtn.innerHTML = `<span>📑 View All (${state.players.length})</span>`;
  allBtn.onclick = () => {
    setActivePlayerTab("all");
    requestRender();
  };
  tabsWrap.appendChild(allBtn);

  switcherBar.appendChild(tabsWrap);
  container.appendChild(switcherBar);

  // 2. Render Player Terminals (Single focused terminal or All)
  const playersToRender = (currentTab === "all")
    ? state.players
    : state.players.filter((p) => p.player_id === Number(currentTab));

  // If no match found (e.g. invalid tab), fallback to all
  const targetList = playersToRender.length > 0 ? playersToRender : state.players;

  const terminalsGrid = document.createElement("div");
  terminalsGrid.className = `terminals-display-grid ${currentTab === "all" ? "view-all-mode" : "single-terminal-mode"}`;

  targetList.forEach((p) => {
    const isTurn = (p.player_id === state.active_player_index && state.phase === 3);
    const isCISO = (p.player_id === state.first_player_index);
    const archetypeCode = (p.archetype && p.archetype.code) ? p.archetype.code : "";
    const dossier = getDossier(archetypeCode) || {
      name: p.archetype ? p.archetype.name : p.name,
      role: p.archetype && p.archetype.role ? p.archetype.role : "Cybersecurity Specialist",
      flavor: p.archetype && p.archetype.flavor ? p.archetype.flavor : "Data flows through darkness, leaving traces only we can read.",
      timing: p.archetype ? p.archetype.timing_window : "TACTICAL",
      abilityName: p.archetype ? p.archetype.ability_name : "Special Routine",
      abilityDesc: p.archetype ? p.archetype.description : "Consultancy ability active across versions.",
      code: archetypeCode,
    };

    const terminalMat = document.createElement("div");
    terminalMat.className = `pnp-terminal-mat ${isTurn ? "active-turn" : ""} ${p.is_patient_zero ? "patient-zero" : ""}`;

    terminalMat.innerHTML = `
      <!-- Terminal Frame Header Strip -->
      <div class="terminal-banner">
        <div class="terminal-banner-left">
          <span class="terminal-tag">TOO MANY SECRETS // CONSULTANCY TERMINAL</span>
          <span class="terminal-id">[TERM-0${p.player_id + 1}]</span>
          ${p.is_human ? '<span class="terminal-human-badge">HUMAN</span>' : `<span class="terminal-bot-badge">${p.bot_archetype || 'BOT'}</span>`}
        </div>
        <div class="terminal-banner-right">
          ${isCISO ? '<span class="ciso-pill">★ LEAD CONSULTANT (CISO)</span>' : ''}
          <span class="reboot-pill ${p.system_reboot_used ? 'reboot-used' : 'reboot-ready'}">
            ${p.system_reboot_used ? 'REBOOT: USED' : 'REBOOT: READY (1x/GAME)'}
          </span>
          ${p.is_patient_zero ? '<span class="breach-pill">TOTAL DATA BREACH</span>' : ''}
          <span class="vp-pill">${p.portfolio_value} VP</span>
        </div>
      </div>

      <!-- Main Two-Column Terminal Body -->
      <div class="terminal-body-grid">
        <!-- ========================================================= -->
        <!-- LEFT COLUMN: Identity, Wireframe, Flavor, & Ability Card  -->
        <!-- ========================================================= -->
        <div class="terminal-left-col">
          <!-- Character Header -->
          <div class="character-identity-box">
            <h3 class="character-name">${dossier.name.toUpperCase()}</h3>
            <div class="character-role">${dossier.role.toUpperCase()}</div>
          </div>

          <!-- Schematic Blueprint Wireframe -->
          <div class="schematic-blueprint-box">
            ${renderSchematicSvg(dossier.code)}
          </div>

          <!-- Flavor Text Box -->
          <div class="flavor-quote-box">
            <em>"${dossier.flavor}"</em>
          </div>

          <!-- Special Ability Box -->
          <div class="special-ability-card">
            <div class="ability-card-header">
              <span class="ability-card-title">${dossier.abilityName.toUpperCase()}</span>
              <span class="ability-timing-pill">${dossier.timing}</span>
            </div>
            <div class="ability-card-body">
              ${dossier.abilityDesc}
            </div>
            
            <!-- Once-Per-Version Ability Track inside Ability Card -->
            <div class="version-ability-track-panel">
              <div class="version-track-header">
                <span class="track-hdr-lbl">ONCE / VER:</span>
                <span class="track-hdr-sub">Unused charge forfeits on SETEC upgrade</span>
              </div>
              <div class="version-track-slots-row">
                ${renderVersionSlotBadge("v1.0", p.ability_v1_status)}
                ${renderVersionSlotBadge("v2.0", p.ability_v2_status)}
                ${renderVersionSlotBadge("v3.0", p.ability_v3_status)}
              </div>
            </div>
          </div>
        </div>

        <!-- ========================================================= -->
        <!-- RIGHT COLUMN: Operational Dice Zones & Defense Matrix      -->
        <!-- ========================================================= -->
        <div class="terminal-right-col">
          <!-- 1. Ready Zone -->
          <div class="operational-zone ready-zone-panel">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name">READY ZONE</span>
                <span class="zone-count-badge">(${p.ready_dice.length + (!p.has_rolled && p.contractor_dice ? p.contractor_dice.length : 0)})</span>
              </div>
              <div class="zone-subtext">
                Start: 4 Gray Dice | Phase 1: Roll all Ready + hired Contractors
              </div>
            </div>
            <div class="dice-tray ready-tray" id="ready_tray_${p.player_id}"></div>
          </div>

          <!-- 2. Active Zone (Rolled Pool) -->
          <div class="operational-zone active-zone-panel">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name">ACTIVE ZONE</span>
                <span class="zone-count-badge">(${p.rolled_pool.length} ROLLED)</span>
              </div>
              <div class="zone-subtext">
                ${p.is_human && state.phase === 1 && !p.has_committed 
                  ? `Free Rerolls: <strong>${p.rerolls_remaining || 0}</strong>/2 | Spend 1 🔧 to Unlock 🔒` 
                  : `Max 2 Free Rerolls | Spend 1 🔧 to Unlock 🔒 | Unassigned yield $ & 🔧`}
              </div>
            </div>
            <div class="zone-watermark-note">
              ROLLED POOL // DECLARE ( / ) CHOICES & ASSIGN SHIELDS BEFORE COLLECTING OUTPUTS
            </div>
            <div class="dice-tray active-tray" id="rolled_tray_${p.player_id}"></div>
          </div>

          <!-- 3. Shield Slots Row (3 Columns: Red, Blue, Green) -->
          <div class="shield-matrix-row">
            <!-- Red Shields -->
            <div class="shield-box red-shield-box">
              <div class="shield-header-bar">
                <div class="shield-title">
                  <span class="shield-symbol">◆</span>
                  <span>RED SHIELDS</span>
                  <span class="shield-count">(${p.shield_slots.red.length})</span>
                </div>
              </div>
              <div class="shield-desc-sub1">Blocks Ransomware</div>
              <div class="shield-desc-sub2">Unblocked: -$1 → 🔧 → -1 Secret</div>
              <div class="shield-slots-tray" id="shields_red_${p.player_id}"></div>
            </div>

            <!-- Blue Shields -->
            <div class="shield-box blue-shield-box">
              <div class="shield-header-bar">
                <div class="shield-title">
                  <span class="shield-symbol">●</span>
                  <span>BLUE SHIELDS</span>
                  <span class="shield-count">(${p.shield_slots.blue.length})</span>
                </div>
              </div>
              <div class="shield-desc-sub1">Blocks Spyware</div>
              <div class="shield-desc-sub2">Unblocked: -1 Corporate Secret</div>
              <div class="shield-slots-tray" id="shields_blue_${p.player_id}"></div>
            </div>

            <!-- Green Shields -->
            <div class="shield-box green-shield-box">
              <div class="shield-header-bar">
                <div class="shield-title">
                  <span class="shield-symbol">▲</span>
                  <span>GREEN SHIELDS</span>
                  <span class="shield-count">(${p.shield_slots.green.length})</span>
                </div>
              </div>
              <div class="shield-desc-sub1">Blocks Malware</div>
              <div class="shield-desc-sub2">Unblocked: Wear 1 Ready (Yellow 1st!)</div>
              <div class="shield-slots-tray" id="shields_green_${p.player_id}"></div>
            </div>
          </div>

          <!-- Dice Wear Transition Caption -->
          <div class="wear-transition-caption">
            <span>DICE WEAR: Permanent Shields blocking ≥ 1 cube move to Unpatched | 0 cubes blocked = stay Ready | Contractors → Supply</span>
          </div>

          <!-- 4. Unpatched Zone -->
          <div class="operational-zone unpatched-zone-panel">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name">UNPATCHED ZONE</span>
                <span class="zone-count-badge">(${p.unpatched_dice.length})</span>
              </div>
              <div class="zone-subtext">
                Offline (Do Not Roll) | Phase 3 Patch: Pay 1 🔧 or $2 per die → Ready Zone
              </div>
            </div>
            <div class="dice-tray unpatched-tray" id="unpatched_tray_${p.player_id}"></div>

            <!-- Integrated System Reboot Slot -->
            <div class="system-reboot-strip">
              <div class="reboot-indicator-card ${p.system_reboot_used ? 'used' : 'ready'}">
                <span class="reboot-check-icon">${p.system_reboot_used ? '✓' : '□'}</span>
                <span class="reboot-card-name">SYSTEM REBOOT</span>
                <span class="reboot-card-status">(${p.system_reboot_used ? 'USED' : 'READY'})</span>
                <span class="reboot-card-badge">1x / GAME</span>
              </div>
              <div class="reboot-explanation-text">
                <strong>Phase 3 Emergency Reboot:</strong> If you have <strong>0 Ready dice</strong>, return all <strong>Gray Starter Dice</strong> from Unpatched → Ready.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- BOTTOM ROW: Money | Patches | Secrets Balance Sheet       -->
      <!-- ========================================================= -->
      <div class="terminal-reserves-row">
        <!-- 1. Money -->
        <div class="reserve-card money-reserve-card">
          <div class="reserve-card-header">
            <span class="reserve-card-title">MONEY ($)</span>
            <span class="reserve-rate-pill">1 VP per $2</span>
          </div>
          <div class="reserve-card-main">
            <span class="reserve-currency-symbol">$</span>
            <span class="reserve-currency-value">${p.money}</span>
          </div>
          <div class="reserve-card-footer">
            Start: $7 | Never drops below $0
          </div>
        </div>

        <!-- 2. Patches (with 3 Dedicated Physical Token Slots) -->
        <div class="reserve-card patches-reserve-card">
          <div class="reserve-card-header">
            <span class="reserve-card-title">🔧 PATCHES</span>
            <span class="reserve-rate-pill">MAX 3 | 0 VP</span>
          </div>
          <div class="reserve-card-main patches-slots-main">
            <div class="patch-token-slot ${p.patches >= 1 ? 'filled' : 'empty'}">
              <span class="slot-number-lbl">SLOT 1</span>
              <span class="slot-wrench-icon">${p.patches >= 1 ? '🔧' : '◌'}</span>
            </div>
            <div class="patch-token-slot ${p.patches >= 2 ? 'filled' : 'empty'}">
              <span class="slot-number-lbl">SLOT 2</span>
              <span class="slot-wrench-icon">${p.patches >= 2 ? '🔧' : '◌'}</span>
            </div>
            <div class="patch-token-slot ${p.patches >= 3 ? 'filled' : 'empty'}">
              <span class="slot-number-lbl">MAX (3)</span>
              <span class="slot-wrench-icon">${p.patches >= 3 ? '🔧' : '◌'}</span>
            </div>
          </div>
          <div class="reserve-card-footer">
            Start: 2 Tokens | Unlock 🔒 / Patch / Auto-Absorb $1 Red
          </div>
        </div>

        <!-- 3. Corporate Secrets -->
        <div class="reserve-card secrets-reserve-card">
          <div class="reserve-card-header">
            <span class="reserve-card-title">🔒 SECRETS</span>
            <span class="reserve-rate-pill">4 VP EACH</span>
          </div>
          <div class="reserve-card-main">
            <span class="reserve-secrets-symbol">🔒</span>
            <span class="reserve-secrets-value ${p.secrets <= 2 ? 'critical' : ''}">${p.secrets}</span>
          </div>
          <div class="reserve-card-footer ${p.secrets <= 0 ? 'breach-alert' : ''}">
            ${p.secrets <= 0 ? '<strong style="color: #ff0055;">TOTAL DATA BREACH (PATIENT ZERO)</strong>' : 'Start: 8 (2P/3P) | 10 (4P) — ≤0 = Total Breach'}
          </div>
        </div>
      </div>
    `;

    terminalsGrid.appendChild(terminalMat);

    // =========================================================
    // Populate Dice in Trays
    // =========================================================

    // Ready Zone Tray
    const readyTray = terminalMat.querySelector(`#ready_tray_${p.player_id}`);
    if (readyTray) {
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
    }

    // Active Zone Tray (Rolled Pool)
    const rolledTray = terminalMat.querySelector(`#rolled_tray_${p.player_id}`);
    if (rolledTray) {
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
    }

    // Shield Slots
    ["red", "blue", "green"].forEach((c) => {
      const slotEl = terminalMat.querySelector(`#shields_${c}_${p.player_id}`);
      if (slotEl && p.shield_slots && p.shield_slots[c]) {
        p.shield_slots[c].forEach((d) => {
          const item = document.createElement("div");
          item.className = `shield-die-chip ${d.color}`;
          item.innerText = `${d.color.toUpperCase()}: ${d.current_face ? d.current_face.name : 'Shield'}`;
          slotEl.appendChild(item);
        });
      }
    });

    // Unpatched Zone Tray
    const unpatchedTray = terminalMat.querySelector(`#unpatched_tray_${p.player_id}`);
    if (unpatchedTray) {
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
    }
  });

  container.appendChild(terminalsGrid);
}
