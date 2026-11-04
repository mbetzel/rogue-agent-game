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
import { doBuy, doUpgradeTrack, doFilePatent } from "../api.js";
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

// Full Modular Dossier specs matching pnp/generate_pnp.py CHARACTERS & COMPANIES
const COMPANIES_DATA = {
  MERIDIAN: {
    code: "MERIDIAN",
    name: "Meridian Global Logistics",
    sector: "Defense & Logistics",
    overrideName: "Contingent Staffing",
    timing: "P1: STAFFING",
    description: "Roll 1 additional Contractor die without paying cash cost during Phase 1 Boot.",
    themeColor: "#f59e0b",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4, +$2 Starting Cash ($8 total).",
  },
  OMNIDYNE: {
    code: "OMNIDYNE",
    name: "Omnidyne Systems",
    sector: "Industrial Automation",
    overrideName: "Magnetic Splice",
    timing: "P3: OPERATIONS",
    description: "Move 1 die from your Glitched Box directly to Ready for Release for free (bypassing Scanned and saving 1 🔧).",
    themeColor: "#4ade80",
    startingSetupDesc: "Def Cap 1, Triage Lvl 1 (Bandwidth 3), Release Lvl 1 (Bandwidth 5).",
  },
  AEGIS: {
    code: "AEGIS",
    name: "Aegis Security Group",
    sector: "Physical & Cyber Defense",
    overrideName: "Baffle Echo",
    timing: "P2: STEP 2B DMG",
    description: "Ignore 1 attack cube (Red, Blue, or Green) when resolving compiler damage for yourself this round.",
    themeColor: "#38bdf8",
    startingSetupDesc: "Defense Lvl 1 (3 Shields Cap), Triage 1, Release 3.",
  },
  DTO: {
    code: "DTO",
    name: "DTO Sovereign Trust",
    sector: "Offshore Banking & Intelligence",
    overrideName: "Slush Fund",
    timing: "P2: STEP 2B DMG",
    description: "Absorb up to 2 Corporate Secret loss (from Blue Spyware or Red Ransom) for free without paying cash.",
    themeColor: "#a855f7",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4, +1 Corporate Secret.",
  },
  HELIX: {
    code: "HELIX",
    name: "Helix Bio-Informatics",
    sector: "Genomic Computation",
    overrideName: "Brute-Force Bypass",
    timing: "P1: REROLLS",
    description: "During Phase 1 rerolls, include locked dice for free, and turn 1 rolled die to any legal non-Star face.",
    themeColor: "#f43f5e",
    startingSetupDesc: "Starts at Patent Lvl 1 (3 🔬 cost), +2 🔬 Starting Research (2 🔬 total).",
  },
  PROMETHEUS: {
    code: "PROMETHEUS",
    name: "Prometheus Quantitative",
    sector: "High-Frequency Arbitrage",
    overrideName: "Algorithmic Arbitrage",
    timing: "P3: OPERATIONS",
    description: "Mode A: $2 discount on purchasing 1 Colored or Purple Specialist Die; Mode B: Gain +$3 cash payout directly.",
    themeColor: "#00d4ff",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4, -1 🔬 Track Upgrade Discount.",
  },
};

const WHITE_HATS_DATA = {
  OPERATOR: {
    code: "OPERATOR",
    name: "The Operator",
    role: "Master Strategist // Contractor Dispatch",
    flavor: "Never burn internal hardware when three night-shift phreakers are waiting by a payphone.",
    protocolName: "Overtime Sprint",
    protocolDesc: "Phase 1 Staffing: hire up to 2 White Contractors for free.",
    passiveDesc: "Gray die with [1 $, 1 🔧] yields +$1 extra.",
    themeColor: "#f59e0b",
  },
  PHREAKER: {
    code: "PHREAKER",
    name: "The Phreaker",
    role: "Hardware Tinkerer // Emergency Relays",
    flavor: "A strip of Mylar splicing tape and a 2600-Hz whistle will fix what ten grand of silicon can't.",
    protocolName: "Jumper Diagnostics",
    protocolDesc: "When Purple ★ is rolled, roll 1 offline die in Under Development (or gain +$1 Cash fallback if pipeline is empty).",
    passiveDesc: "Free Phase 3 diagnostic roll on 1 die in Scanned or Glitched (or +$1 fallback).",
    themeColor: "#4ade80",
  },
  ACOUSTIC: {
    code: "ACOUSTIC",
    name: "The Acoustic",
    role: "Pattern Genius // Mainframe Resonance",
    flavor: "Every mainframe hums before it strikes. Listen to the baffles -- you can hear which packet drops next.",
    protocolName: "Decoy Route",
    protocolDesc: "Phase 3 Income: +$1 for each distinct attack cube color in Exit Tray (Red, Blue, Green, Black; max +$4).",
    passiveDesc: "Production dice produce +1 🔧 each time they generate patches.",
    themeColor: "#38bdf8",
  },
  SPOOK: {
    code: "SPOOK",
    name: "The Spook",
    role: "Ex-Intelligence // OpSec & Slush Funds",
    flavor: "Every breach has a price tag. That's what non-attributable slush accounts are for.",
    protocolName: "Burn Notice",
    protocolDesc: "Phase 3 Ops: Gain +$2; optional: permanently return 1 owned colored die to market for +1 Corporate Secret.",
    passiveDesc: "Once per turn in Phase 3, burn 1 owned colored die for +1 Secret.",
    themeColor: "#a855f7",
  },
  PRODIGY: {
    code: "PRODIGY",
    name: "The Prodigy",
    role: "Reckless Hacker // Lock Bypassing",
    flavor: "Locked memory is just a polite suggestion from someone who left debug interrupts enabled.",
    protocolName: "Exploit Payload",
    protocolDesc: "Phase 1 Rerolls: Turn any 1 other rolled die to any legal non-Star face of choice.",
    passiveDesc: "If Gray die has only 🔧, generate +1 extra 🔧.",
    themeColor: "#f43f5e",
  },
  CIPHER: {
    code: "CIPHER",
    name: "The Cipher",
    role: "Mathematician // Algorithmic Arbitrage",
    flavor: "Why pay retail for entropy when SETEC's own arbitrage equations subsidize the upgrade?",
    protocolName: "Algorithmic Parity",
    protocolDesc: "Phase 3 Income: Collect +$2 cash and +1 🔬 Research Token.",
    passiveDesc: "Purple Specialist Die faces yield optimized cryptographic yield.",
    themeColor: "#00d4ff",
  },
};

const CHARACTER_DOSSIERS = WHITE_HATS_DATA;

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
      <span class="tab-vp-badge">${p.secrets} Secrets</span>
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

    // Resolve modular Client Company and White Hat Dossier (with backward compatibility)
    const companyCode = (p.company && p.company.code) ? p.company.code : (p.archetype ? p.archetype.code : "MERIDIAN");
    const whiteHatCode = (p.white_hat && p.white_hat.code) ? p.white_hat.code : (p.archetype ? p.archetype.code : "OPERATOR");

    const compFallback = COMPANIES_DATA[companyCode] || COMPANIES_DATA["MERIDIAN"];
    const company = p.company ? {
      name: p.company.name || compFallback.name,
      sector: p.company.sector || compFallback.sector,
      overrideName: p.company.override_name || compFallback.overrideName,
      timing: p.company.timing_window || compFallback.timing,
      description: p.company.description || compFallback.description,
      themeColor: p.company.theme_color || compFallback.themeColor,
      startingSetupDesc: p.company.starting_setup_desc || compFallback.startingSetupDesc,
    } : compFallback;

    const whFallback = WHITE_HATS_DATA[whiteHatCode] || WHITE_HATS_DATA["OPERATOR"];
    const whiteHat = p.white_hat ? {
      code: p.white_hat.code || whFallback.code,
      name: p.white_hat.name || whFallback.name,
      role: p.white_hat.role || whFallback.role,
      flavor: p.white_hat.flavor || whFallback.flavor,
      protocolName: p.white_hat.protocol_name || (p.white_hat.purple_star_spec ? p.white_hat.purple_star_spec.split(":")[0] : whFallback.protocolName),
      protocolDesc: p.white_hat.description || p.white_hat.purple_star_spec || whFallback.protocolDesc,
      passiveDesc: p.white_hat.passive_protocol || whFallback.passiveDesc,
      themeColor: p.white_hat.theme_color || whFallback.themeColor,
    } : whFallback;

    const isActivelyRolling = Boolean(p.has_rolled && !p.has_committed);
    const readyDiceList = (p.ready_for_release_dice && p.ready_for_release_dice.length !== undefined)
      ? p.ready_for_release_dice
      : (p.ready_dice || []);
    const contractorCount = (!p.has_rolled && p.contractor_dice) ? p.contractor_dice.length : 0;
    const readyCount = readyDiceList.length + contractorCount;

    const redShieldDice = (p.shield_slots && p.shield_slots.red && p.shield_slots.red.length)
      ? p.shield_slots.red
      : ((p.production_slots && p.production_slots.red_shield) || []);
    const blueShieldDice = (p.shield_slots && p.shield_slots.blue && p.shield_slots.blue.length)
      ? p.shield_slots.blue
      : ((p.production_slots && p.production_slots.blue_shield) || []);
    const greenShieldDice = (p.shield_slots && p.shield_slots.green && p.shield_slots.green.length)
      ? p.shield_slots.green
      : ((p.production_slots && p.production_slots.green_shield) || []);
    const anyShieldDice = (p.shield_slots && p.shield_slots.any && p.shield_slots.any.length)
      ? p.shield_slots.any
      : ((p.production_slots && p.production_slots.any_shield) || []);

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
          ${p.is_patient_zero ? '<span class="breach-pill">TOTAL DATA BREACH</span>' : ''}
          <span class="vp-pill">${p.secrets} Secrets</span>
        </div>
      </div>

      <!-- Main Two-Column Terminal Body -->
      <div class="terminal-body-grid">
        <!-- ========================================================= -->
        <!-- LEFT COLUMN: Identity, Wireframe, Flavor, & Ability Card  -->
        <!-- ========================================================= -->
        <div class="terminal-left-col">
          <!-- Client Company Box -->
          <div class="company-card-box" style="margin-bottom: 8px; border: 1px solid ${company.themeColor || 'var(--border-color)'}; border-radius: 4px; padding: 6px; background: rgba(0,0,0,0.35);">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
              <span style="font-weight: 700; font-size: 0.8rem; color: ${company.themeColor || '#fff'};">${company.name.toUpperCase()}</span>
              <span style="font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase;">${company.sector}</span>
            </div>
            <div style="margin-top: 4px; display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600; font-size: 0.75rem; color: #f1f5f9;">OVERRIDE: ${company.overrideName.toUpperCase()}</span>
              <span class="ability-timing-pill" style="font-size: 0.6rem;">${company.timing}</span>
            </div>
            <div style="font-size: 0.7rem; color: #cbd5e1; margin-top: 2px; line-height: 1.25;">
              ${company.description}
            </div>
            ${(company.startingSetupDesc || compFallback.startingSetupDesc) ? `
              <div style="font-size: 0.68rem; color: #94a3b8; margin-top: 5px; background: rgba(255,255,255,0.04); padding: 3px 6px; border-radius: 3px; border-left: 2px solid ${company.themeColor || 'var(--border-color)'};">
                <strong style="color: #e2e8f0;">Starting Setup:</strong> ${company.startingSetupDesc || compFallback.startingSetupDesc}
              </div>
            ` : ''}
            <div class="version-ability-track-panel" style="margin-top: 6px;">
              <div class="version-track-header">
                <span class="track-hdr-lbl">OVERRIDE CHARGE (ONCE / VER):</span>
                <span class="track-hdr-sub">Unused charge forfeits on SETEC upgrade</span>
              </div>
              <div class="version-track-slots-row">
                ${renderVersionSlotBadge("v1.0", p.ability_v1_status)}
                ${renderVersionSlotBadge("v2.0", p.ability_v2_status)}
                ${renderVersionSlotBadge("v3.0", p.ability_v3_status)}
              </div>
            </div>
          </div>

          <!-- White Hat Dossier Box -->
          <div class="white-hat-card-box" style="border: 1px solid ${whiteHat.themeColor || 'var(--border-color)'}; border-radius: 4px; padding: 6px; background: rgba(0,0,0,0.25);">
            <div class="character-identity-box" style="margin-bottom: 4px;">
              <h3 class="character-name" style="font-size: 0.85rem; margin: 0; color: ${whiteHat.themeColor || '#fff'};">${whiteHat.name.toUpperCase()}</h3>
              <div class="character-role" style="font-size: 0.65rem; color: var(--text-dim);">${whiteHat.role.toUpperCase()}</div>
            </div>

            <!-- Schematic Blueprint Wireframe -->
            <div class="schematic-blueprint-box">
              ${renderSchematicSvg(whiteHat.code)}
            </div>

            <!-- Flavor Text Box -->
            <div class="flavor-quote-box" style="margin: 4px 0; font-size: 0.68rem;">
              <em>"${whiteHat.flavor}"</em>
            </div>

            ${whiteHat.passiveDesc ? `
            <div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px; line-height: 1.2;">
              <span style="color: #38bdf8; font-weight: 600;">PASSIVE:</span> ${whiteHat.passiveDesc}
            </div>` : ''}

            <!-- Face 6 Purple Star Protocol -->
            <div class="signature-protocol-panel" style="padding-top: 4px; border-top: 1px dashed rgba(168, 85, 247, 0.4);">
              <div class="protocol-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span style="font-weight: bold; color: #c084fc; font-size: 0.72rem;">PURPLE ★ PROTOCOL: ${(whiteHat.protocolName || 'SIGNATURE').toUpperCase()}</span>
                <span class="ability-timing-pill" style="background: rgba(168, 85, 247, 0.2); color: #c084fc; font-size: 0.6rem;">FACE 6</span>
              </div>
              <div style="font-size: 0.7rem; color: #cbd5e1; line-height: 1.25;">
                ${whiteHat.protocolDesc || ''}
              </div>
            </div>
          </div>
        </div>

        <!-- ========================================================= -->
        <!-- RIGHT COLUMN: Operational Dice Zones & CI/CD Pipeline Matrix -->
        <!-- ========================================================= -->
        <div class="terminal-right-col">
          <!-- Zone 1: Ready for Release Zone (Rolls managed here, then move to In Production) -->
          <div class="operational-zone ready-zone-panel">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name">READY FOR RELEASE</span>
                <span class="zone-count-badge">(${isActivelyRolling 
                  ? `${p.rolled_pool.length} ROLLED` 
                  : `${readyCount} READY`})</span>
              </div>
              <div class="zone-subtext">
                ${isActivelyRolling 
                  ? (p.is_human && state.phase === 1 
                      ? `Free Rerolls: <strong>${p.rerolls_remaining || 0}</strong>/2 | Click unlocked dice to reroll | Glitches lock immediately` 
                      : `Phase 1 Rolling | Glitches lock immediately → Glitched Box`)
                  : (p.has_committed 
                      ? (readyCount > 0 ? 'Dice ready for next round' : 'All dice deployed to In Production | Dice return or graduate here in Phase 3')
                      : 'Start: 3 Gray + 1 Purple Specialist Die | Phase 1: Roll all Ready + hired Contractors | Offline dice do not roll')}
              </div>
            </div>
            ${isActivelyRolling ? `
            <div class="zone-watermark-note">
              ROLLED POOL // YAHTZEE REROLLS // DEPLOY TO IN PRODUCTION
            </div>` : ''}
            <div class="dice-tray ready-tray" id="ready_tray_${p.player_id}"></div>
          </div>

          <!-- Zone 2: In Production (Income slot + Red, Blue, Green Shield slots) -->
          <div class="operational-zone production-zone-panel" style="border: 1px solid rgba(56, 189, 248, 0.3); background: rgba(15, 23, 42, 0.4); border-radius: 6px; padding: 10px; margin-bottom: 12px;">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name" style="color: #38bdf8;">IN PRODUCTION</span>
                <span class="zone-count-badge">(${(p.in_production_dice || []).length})</span>
                <span class="zone-count-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; font-size: 0.7rem;">SHIELDS: ${redShieldDice.length + blueShieldDice.length + greenShieldDice.length + anyShieldDice.length}/${p.defense_capacity || 2} CAP</span>
              </div>
              <div class="zone-subtext">
                Delayed Income: Collect $, 🔬, ★ in Phase 3 | Defense Capacity: max ${p.defense_capacity || 2} shields (Flexible Firewall Ready)${p.has_passive_firewall ? ' | 🛡️ Passive Firewall Active (Absorbs 1 cube free in P2B)' : ''}
              </div>
            </div>

            <!-- In Production Grid (Income + Any/Red/Blue/Green Shield Slots) -->
            <div class="shield-matrix-row" style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-top: 8px;">
              <!-- Income Slot -->
              <div class="shield-box" style="border-color: #eab308; background: rgba(234, 179, 8, 0.08);">
                <div class="shield-header-bar">
                  <div class="shield-title">
                    <span class="shield-symbol" style="color: #eab308;">$</span>
                    <span style="color: #eab308;">INCOME</span>
                    <span class="shield-count">(${((p.production_slots && p.production_slots.income) || []).length})</span>
                  </div>
                </div>
                <div class="shield-desc-sub1">Delayed Yield</div>
                <div class="shield-desc-sub2">$, 🔬, ★ in P3</div>
                <div class="shield-slots-tray" id="income_tray_${p.player_id}"></div>
              </div>

              <!-- Any Shields -->
              <div class="shield-box any-shield-box" style="border-color: #38bdf8; background: rgba(56, 189, 248, 0.08);">
                <div class="shield-header-bar">
                  <div class="shield-title">
                    <span class="shield-symbol" style="color: #38bdf8;">🛡️</span>
                    <span style="color: #38bdf8;">ANY SHIELD</span>
                    <span class="shield-count">(${anyShieldDice.length})</span>
                  </div>
                </div>
                <div class="shield-desc-sub1">Flexible Defense</div>
                <div class="shield-desc-sub2">Absorbs in P2B</div>
                <div class="shield-slots-tray" id="shields_any_${p.player_id}"></div>
              </div>

              <!-- Red Shields -->
              <div class="shield-box red-shield-box">
                <div class="shield-header-bar">
                  <div class="shield-title">
                    <span class="shield-symbol">◆</span>
                    <span>RED SHIELDS</span>
                    <span class="shield-count">(${redShieldDice.length})</span>
                  </div>
                </div>
                <div class="shield-desc-sub1">Blocks Ransomware</div>
                <div class="shield-desc-sub2">Unblocked: -$1 (Flat -1 Sec if unpaid)</div>
                <div class="shield-slots-tray" id="shields_red_${p.player_id}"></div>
              </div>

              <!-- Blue Shields -->
              <div class="shield-box blue-shield-box">
                <div class="shield-header-bar">
                  <div class="shield-title">
                    <span class="shield-symbol">●</span>
                    <span>BLUE SHIELDS</span>
                    <span class="shield-count">(${blueShieldDice.length})</span>
                  </div>
                </div>
                <div class="shield-desc-sub1">Blocks Spyware</div>
                <div class="shield-desc-sub2">Unblocked: -1 Secret</div>
                <div class="shield-slots-tray" id="shields_blue_${p.player_id}"></div>
              </div>

              <!-- Green Shields -->
              <div class="shield-box green-shield-box">
                <div class="shield-header-bar">
                  <div class="shield-title">
                    <span class="shield-symbol">▲</span>
                    <span>GREEN SHIELDS</span>
                    <span class="shield-count">(${greenShieldDice.length})</span>
                  </div>
                </div>
                <div class="shield-desc-sub1">Blocks Malware</div>
                <div class="shield-desc-sub2">Unblocked: Glitches 1 die (Empty: Fizzles)</div>
                <div class="shield-slots-tray" id="shields_green_${p.player_id}"></div>
              </div>
            </div>

            <!-- Zero Dice Wear Note -->
            <div class="wear-transition-caption" style="margin-top: 8px;">
              <span style="color: #4ade80;">ZERO DICE WEAR: Permanent shields blocking attacks DO NOT wear down! They remain deployed in In Production.</span>
            </div>
          </div>

          <!-- Zone 3: Under Development (Two-stage conveyor: Glitched Box -> Scanned Box) -->
          <div class="operational-zone pipeline-zone-panel" style="border: 1px solid rgba(244, 63, 94, 0.3); background: rgba(15, 23, 42, 0.4); border-radius: 6px; padding: 10px; margin-bottom: 12px;">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name" style="color: #f43f5e;">UNDER DEVELOPMENT (CI/CD PIPELINE)</span>
                <span class="zone-count-badge">(${p.under_development_count !== undefined ? p.under_development_count : ((p.glitched_dice || []).length + (p.scanned_dice || []).length)})</span>
                <span class="zone-count-badge" style="background: rgba(244, 63, 94, 0.2); color: #f43f5e; font-size: 0.7rem;">TRIAGE: ${p.triage_bandwidth || 2}/RND | RELEASE: ${p.release_bandwidth || 4}/RND</span>
              </div>
              <div class="zone-subtext">
                Two-Stage Conveyor: Glitched Box → Scanned Box → Ready for Release${p.has_emergency_hotfix ? ' | ⚡ Emergency Hotfix Active (1 die Glitched -> Ready in P3B)' : ''}
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
              <!-- Glitched Box -->
              <div style="border: 1px solid rgba(244, 63, 94, 0.4); background: rgba(244, 63, 94, 0.08); border-radius: 6px; padding: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <span style="font-weight: 600; color: #f43f5e; font-size: 0.85rem;">⚠️ GLITCHED BOX (${(p.glitched_dice || []).length})</span>
                  <span style="font-size: 0.75rem; color: var(--text-dim);">Quarantined Pipeline</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 6px;">
                  Shifts to Scanned Box at round end (Triage Bandwidth: ${p.triage_bandwidth || 2})
                </div>
                <div class="dice-tray" id="glitched_tray_${p.player_id}" style="min-height: 48px;"></div>
              </div>

              <!-- Scanned Box -->
              <div style="border: 1px solid rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.08); border-radius: 6px; padding: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <span style="font-weight: 600; color: #38bdf8; font-size: 0.85rem;">✓ SCANNED BOX (${(p.scanned_dice || []).length})</span>
                  <span style="font-size: 0.75rem; color: #4ade80;">Ready next round!</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 6px;">
                  Graduates to Ready for Release at round end (Release Bandwidth: ${p.release_bandwidth || 4})
                </div>
                <div class="dice-tray" id="scanned_tray_${p.player_id}" style="min-height: 48px;"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- HARDWARE & R&D UPGRADE TRACKS (v0.28.0)                   -->
      <!-- ========================================================= -->
      <div class="terminal-hardware-tracks-panel" style="border: 1px solid rgba(168, 85, 247, 0.35); background: rgba(15, 23, 42, 0.5); border-radius: 6px; padding: 10px; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <div>
            <span style="font-weight: 700; color: #c084fc; font-size: 0.8rem; letter-spacing: 0.5px;">TERMINAL HARDWARE & R&D UPGRADE TRACKS</span>
            <span style="font-size: 0.65rem; color: var(--text-dim); margin-left: 8px;">Spend 🔬 in Phase 3A Operations</span>
          </div>
          <div style="font-size: 0.7rem; color: #a855f7;">
            ${p.upgrade_discount ? `<span style="background: rgba(168,85,247,0.2); padding: 2px 6px; border-radius: 4px;">-${p.upgrade_discount} 🔬 Track Upgrade Discount</span>` : ''}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">
          <!-- Track 1: Triage Track -->
          <div class="track-card" style="border: 1px solid ${p.triage_level >= 1 ? '#38bdf8' : 'var(--border-color)'}; background: rgba(0,0,0,0.25); border-radius: 4px; padding: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 700; font-size: 0.75rem; color: #38bdf8;">⚙️ TRIAGE</span>
              <span style="font-size: 0.65rem; color: var(--text-dim);">Level ${p.triage_level || 0}/2</span>
            </div>
            <div style="font-size: 0.68rem; color: #cbd5e1; margin-top: 2px;">Bandwidth: ${p.triage_bandwidth || 2}/rnd</div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.triage_level || 0) === 0 ? 'rgba(56,189,248,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.triage_level || 0) === 0 ? '#38bdf8' : 'var(--text-dim)'}; border: 1px solid ${(p.triage_level || 0) === 0 ? '#38bdf8' : 'transparent'}; font-weight: ${(p.triage_level || 0) === 0 ? '700' : 'normal'};">[L0] 2</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.triage_level || 0) === 1 ? 'rgba(56,189,248,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.triage_level || 0) === 1 ? '#38bdf8' : 'var(--text-dim)'}; border: 1px solid ${(p.triage_level || 0) === 1 ? '#38bdf8' : 'transparent'}; font-weight: ${(p.triage_level || 0) === 1 ? '700' : 'normal'};">[L1] 3</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.triage_level || 0) === 2 ? 'rgba(56,189,248,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.triage_level || 0) === 2 ? '#38bdf8' : 'var(--text-dim)'}; border: 1px solid ${(p.triage_level || 0) === 2 ? '#38bdf8' : 'transparent'}; font-weight: ${(p.triage_level || 0) === 2 ? '700' : 'normal'};">[L2] 4+Hotfix</span>
            </div>
          </div>

          <!-- Track 2: Release Track -->
          <div class="track-card" style="border: 1px solid ${p.release_level >= 1 ? '#06b6d4' : 'var(--border-color)'}; background: rgba(0,0,0,0.25); border-radius: 4px; padding: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 700; font-size: 0.75rem; color: #06b6d4;">🚀 RELEASE</span>
              <span style="font-size: 0.65rem; color: var(--text-dim);">Level ${p.release_level || 0}/2</span>
            </div>
            <div style="font-size: 0.68rem; color: #cbd5e1; margin-top: 2px;">Bandwidth: ${p.release_bandwidth || 4}/rnd</div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.release_level || 0) === 0 ? 'rgba(6,182,212,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.release_level || 0) === 0 ? '#06b6d4' : 'var(--text-dim)'}; border: 1px solid ${(p.release_level || 0) === 0 ? '#06b6d4' : 'transparent'}; font-weight: ${(p.release_level || 0) === 0 ? '700' : 'normal'};">[L0] 4</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.release_level || 0) === 1 ? 'rgba(6,182,212,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.release_level || 0) === 1 ? '#06b6d4' : 'var(--text-dim)'}; border: 1px solid ${(p.release_level || 0) === 1 ? '#06b6d4' : 'transparent'}; font-weight: ${(p.release_level || 0) === 1 ? '700' : 'normal'};">[L1] 5</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.release_level || 0) === 2 ? 'rgba(6,182,212,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.release_level || 0) === 2 ? '#06b6d4' : 'var(--text-dim)'}; border: 1px solid ${(p.release_level || 0) === 2 ? '#06b6d4' : 'transparent'}; font-weight: ${(p.release_level || 0) === 2 ? '700' : 'normal'};">[L2] 6</span>
            </div>
          </div>

          <!-- Track 3: Defense Track -->
          <div class="track-card" style="border: 1px solid ${p.defense_level >= 1 ? '#4ade80' : 'var(--border-color)'}; background: rgba(0,0,0,0.25); border-radius: 4px; padding: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 700; font-size: 0.75rem; color: #4ade80;">🛡️ DEFENSE GRID</span>
              <span style="font-size: 0.65rem; color: var(--text-dim);">Level ${p.defense_level || 0}/2</span>
            </div>
            <div style="font-size: 0.68rem; color: #cbd5e1; margin-top: 2px;">Cap: ${p.defense_capacity || 2} Shields${p.has_passive_firewall ? ' + Firewall' : ''}</div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.defense_level || 0) === 0 ? 'rgba(74,222,128,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.defense_level || 0) === 0 ? '#4ade80' : 'var(--text-dim)'}; border: 1px solid ${(p.defense_level || 0) === 0 ? '#4ade80' : 'transparent'}; font-weight: ${(p.defense_level || 0) === 0 ? '700' : 'normal'};">[L0] 2 Cap</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.defense_level || 0) === 1 ? 'rgba(74,222,128,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.defense_level || 0) === 1 ? '#4ade80' : 'var(--text-dim)'}; border: 1px solid ${(p.defense_level || 0) === 1 ? '#4ade80' : 'transparent'}; font-weight: ${(p.defense_level || 0) === 1 ? '700' : 'normal'};">[L1] 3 Cap</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.defense_level || 0) === 2 ? 'rgba(74,222,128,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.defense_level || 0) === 2 ? '#4ade80' : 'var(--text-dim)'}; border: 1px solid ${(p.defense_level || 0) === 2 ? '#4ade80' : 'transparent'}; font-weight: ${(p.defense_level || 0) === 2 ? '700' : 'normal'};">[L2] 4 Cap+Firewall</span>
            </div>
          </div>

          <!-- Track 4: Patents Track -->
          <div class="track-card" style="border: 1px solid ${p.patent_level >= 1 ? '#c084fc' : 'var(--border-color)'}; background: rgba(0,0,0,0.25); border-radius: 4px; padding: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 700; font-size: 0.75rem; color: #c084fc;">📜 PATENTS R&D</span>
              <span style="font-size: 0.65rem; color: var(--text-dim);">Level ${p.patent_level || 0}/2</span>
            </div>
            <div style="font-size: 0.68rem; color: #cbd5e1; margin-top: 2px;">Cost: ${p.patent_level === 0 ? 4 : (p.patent_level === 1 ? 3 : 2)} 🔬 → +1 Sec${(p.patent_level || 0) >= 2 ? ', +$1' : ''}</div>
            <div style="display: flex; gap: 4px; margin-top: 6px;">
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.patent_level || 0) === 0 ? 'rgba(192,132,252,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.patent_level || 0) === 0 ? '#c084fc' : 'var(--text-dim)'}; border: 1px solid ${(p.patent_level || 0) === 0 ? '#c084fc' : 'transparent'}; font-weight: ${(p.patent_level || 0) === 0 ? '700' : 'normal'};">[L0] 4 🔬</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.patent_level || 0) === 1 ? 'rgba(192,132,252,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.patent_level || 0) === 1 ? '#c084fc' : 'var(--text-dim)'}; border: 1px solid ${(p.patent_level || 0) === 1 ? '#c084fc' : 'transparent'}; font-weight: ${(p.patent_level || 0) === 1 ? '700' : 'normal'};">[L1] 3 🔬</span>
              <span style="flex: 1; text-align: center; font-size: 0.62rem; padding: 3px 0; border-radius: 3px; background: ${(p.patent_level || 0) === 2 ? 'rgba(192,132,252,0.3)' : 'rgba(255,255,255,0.05)'}; color: ${(p.patent_level || 0) === 2 ? '#c084fc' : 'var(--text-dim)'}; border: 1px solid ${(p.patent_level || 0) === 2 ? '#c084fc' : 'transparent'}; font-weight: ${(p.patent_level || 0) === 2 ? '700' : 'normal'};">[L2] 2 🔬+$1</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- BOTTOM ROW: Money | Research | Secrets Balance Sheet      -->
      <!-- ========================================================= -->
      <div class="terminal-reserves-row">
        <!-- 1. Money -->
        <div class="reserve-card money-reserve-card">
          <div class="reserve-card-header">
            <span class="reserve-card-title">MONEY ($)</span>
            <span class="reserve-rate-pill">TIEBREAKER #1</span>
          </div>
          <div class="reserve-card-main">
            <span class="reserve-currency-symbol">$</span>
            <span class="reserve-currency-value">${p.money}</span>
          </div>
          <div class="reserve-card-footer">
            Start: $4 | Never drops below $0
          </div>
        </div>

        <!-- 2. Research Tokens (Uncapped v0.28.0) -->
        <div class="reserve-card patches-reserve-card" style="border-color: rgba(168, 85, 247, 0.4);">
          <div class="reserve-card-header">
            <span class="reserve-card-title" style="color: #c084fc;">🔬 RESEARCH</span>
            <span class="reserve-rate-pill" style="background: rgba(168, 85, 247, 0.2); color: #c084fc;">UNCAPPED</span>
          </div>
          <div class="reserve-card-main">
            <span class="reserve-currency-symbol" style="color: #c084fc;">🔬</span>
            <span class="reserve-currency-value" style="color: #c084fc;">${p.research_tokens !== undefined ? p.research_tokens : p.patches}</span>
          </div>
          <div class="reserve-card-footer">
            Hardware Upgrades | Cryptographic Patents
          </div>
        </div>

        <!-- 3. Corporate Secrets -->
        <div class="reserve-card secrets-reserve-card">
          <div class="reserve-card-header">
            <span class="reserve-card-title">🔒 SECRETS</span>
            <span class="reserve-rate-pill">VICTORY GOAL</span>
          </div>
          <div class="reserve-card-main">
            <span class="reserve-secrets-symbol">🔒</span>
            <span class="reserve-secrets-value ${p.secrets <= 2 ? 'critical' : ''}">${p.secrets}</span>
          </div>
          <div class="reserve-card-footer ${p.secrets <= 0 ? 'breach-alert' : ''}">
            ${p.secrets <= 0 ? '<strong style="color: #ff0055;">TOTAL DATA BREACH (PATIENT ZERO)</strong>' : 'Start: 8 (2P/3P) | 12 (4P) — ≤0 = Total Breach'}
          </div>
        </div>

        <!-- 4. Personal Purple Reserve -->
        <div class="reserve-card purple-reserve-card ${p.can_buy_purple_reserve ? 'clickable' : ''}" id="purple_reserve_${p.player_id}" style="border-color: rgba(168, 85, 247, 0.4);">
          <div class="reserve-card-header">
            <span class="reserve-card-title" style="color: #c084fc;">▼ PURPLE RESERVE</span>
            <span class="reserve-rate-pill" style="background: rgba(168, 85, 247, 0.2); color: #c084fc;">${p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 1}/1 DIE</span>
          </div>
          <div class="reserve-card-main" style="display: flex; gap: 8px; justify-content: center; padding: 4px 0;">
            <div class="patch-token-slot empty" style="border-color: #a855f7; opacity: 0.8;" title="Die 1: Active in Starting Pool (Purchased at Setup)">
              <span class="slot-number-lbl">DIE 1</span>
              <span class="slot-wrench-icon" style="color: #4ade80; font-size: 0.7rem;">SETUP</span>
            </div>
            <div class="patch-token-slot ${(p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 1) >= 1 ? 'filled' : 'empty'}" style="border-color: #a855f7;" title="${(p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 1) >= 1 ? 'Die 2: In Reserve (1 Available)' : 'Die 2: Procured'}">
              <span class="slot-number-lbl">DIE 2</span>
              <span class="slot-wrench-icon" style="color: #c084fc;">${(p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 1) >= 1 ? `▼ $${p.purple_reserve_cost !== undefined ? p.purple_reserve_cost : 4}` : '✓'}</span>
            </div>
          </div>
          <div class="reserve-card-footer">
            ${p.can_buy_purple_reserve ? `<strong style="color: #c084fc;">CLICK TO PROCURE ($${p.purple_reserve_cost !== undefined ? p.purple_reserve_cost : 4})</strong>` : 'Die 1: Setup | Die 2: Reserve ($' + (p.purple_reserve_cost !== undefined ? p.purple_reserve_cost : 4) + ')'}
          </div>
        </div>
      </div>
    `;

    terminalsGrid.appendChild(terminalMat);

    // Personal Purple Reserve Click Handler
    const purpleReserveEl = terminalMat.querySelector(`#purple_reserve_${p.player_id}`);
    if (purpleReserveEl && p.can_buy_purple_reserve && p.is_human) {
      purpleReserveEl.style.cursor = "pointer";
      purpleReserveEl.onclick = () => {
        doBuy("purple");
      };
    }

    // =========================================================
    // Populate Dice in Trays
    // =========================================================

    // Ready Zone Tray (Managing rolls & ready dice)
    const readyTray = terminalMat.querySelector(`#ready_tray_${p.player_id}`);
    if (readyTray) {
      if (isActivelyRolling) {
        // While rolling / rerolling in Phase 1: manage rolls directly in Ready for Release
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
            }
          }
          readyTray.appendChild(chip);
        });
      } else if (!p.has_rolled) {
        // Unrolled: ready dice + hired contractors
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
      } else {
        // Completed rolls: dice have been deployed to In Production
        if (p.ready_dice && p.ready_dice.length > 0) {
          p.ready_dice.forEach((d) => {
            const chip = document.createElement("div");
            chip.className = `die-chip ${d.color}`;
            chip.innerHTML = `<span>${d.color.toUpperCase()}</span>`;
            readyTray.appendChild(chip);
          });
        } else {
          const emptyMsg = document.createElement("div");
          emptyMsg.className = "empty-tray-msg";
          emptyMsg.style.fontSize = "0.68rem";
          emptyMsg.style.color = "var(--text-muted)";
          emptyMsg.style.fontStyle = "italic";
          emptyMsg.style.padding = "4px 8px";
          emptyMsg.innerText = "All dice deployed to In Production";
          readyTray.appendChild(emptyMsg);
        }
      }
    }

    // Income Tray
    const incomeTray = terminalMat.querySelector(`#income_tray_${p.player_id}`);
    if (incomeTray) {
      const incomeDice = (p.production_slots && p.production_slots.income) || [];
      incomeDice.forEach((d) => {
        const item = document.createElement("div");
        item.className = `shield-die-chip ${d.color}`;
        item.innerText = `${d.color.toUpperCase()}: ${d.effective_face ? d.effective_face.name : (d.current_face ? d.current_face.name : 'Yield')}`;
        incomeTray.appendChild(item);
      });
    }

    // Shield Slots
    ["any", "red", "blue", "green"].forEach((c) => {
      const slotEl = terminalMat.querySelector(`#shields_${c}_${p.player_id}`);
      if (slotEl) {
        const slotDice = (p.shield_slots && p.shield_slots[c] && p.shield_slots[c].length)
          ? p.shield_slots[c]
          : ((p.production_slots && p.production_slots[`${c}_shield`]) || []);
        slotDice.forEach((d) => {
          const item = document.createElement("div");
          item.className = `shield-die-chip ${d.color}`;
          item.innerText = `${d.color.toUpperCase()}: ${d.current_face ? d.current_face.name : 'Shield'}`;
          slotEl.appendChild(item);
        });
      }
    });

    // Glitched Box Tray
    const glitchedTray = terminalMat.querySelector(`#glitched_tray_${p.player_id}`);
    if (glitchedTray) {
      (p.glitched_dice || []).forEach((d) => {
        const chip = document.createElement("div");
        chip.className = `die-chip ${d.color}`;
        chip.title = "Glitched: shifts to Scanned Box via Triage Bandwidth at end of round";
        chip.innerHTML = `<span>${d.color.toUpperCase()}</span>`;
        glitchedTray.appendChild(chip);
      });
    }

    // Scanned Box Tray
    const scannedTray = terminalMat.querySelector(`#scanned_tray_${p.player_id}`);
    if (scannedTray) {
      (p.scanned_dice || []).forEach((d) => {
        const chip = document.createElement("div");
        chip.className = `die-chip ${d.color}`;
        chip.title = "Scanned: graduates to Ready for Release at end of round";
        chip.innerHTML = `<span>${d.color.toUpperCase()}</span>`;
        scannedTray.appendChild(chip);
      });
    }
  });

  container.appendChild(terminalsGrid);
}
