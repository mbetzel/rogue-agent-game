/**
 * Rogue Agent — Player Mats & Company Terminal Mat Component
 * Structured faithfully after Print-and-Play US Letter Company Terminal Mat (01_Player_Boards.pdf)
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

// v0.35.0 Terminal Hardware Tracks: five-step strips (L0-L4) with Breakthrough markers at L1 / L3.
const TRACK_STRIPS = [
  { key: "triage", label: "⚙️ TRIAGE", color: "#38bdf8", rgb: "56,189,248",
    steps: ["Bandwidth 2", "★ +2 White Contractors", "Bandwidth 3", "★ $3: Gray → Market die", "Bandwidth 4 + 🔬 per die beyond 2nd"] },
  { key: "release", label: "🚀 RELEASE", color: "#06b6d4", rgb: "6,182,212",
    steps: ["Bandwidth 4", "★ +1 Gray Legacy die", "Bandwidth 5", "★ +1 Secret", "Bandwidth 6 + 1 free reroll"] },
  { key: "defense", label: "🛡️ DEFENSE GRID", color: "#4ade80", rgb: "74,222,128",
    steps: ["Capacity 2", "★ +1 Gray Legacy die", "Capacity 3", "★ +1 Secret", "Capacity 4 + $1 per block (max $3)"] },
  { key: "patent", label: "📜 PATENTS", color: "#c084fc", rgb: "192,132,252",
    steps: ["2 🔬 → 1 Secret", "★ +$3", "3 🔬 → 2 Secrets", "★ 2nd Purple die", "1 🔬 → 1 Secret"] },
];
// v0.36.0: the fourth track is the Public Relations Track (Phase 6: spend research per +1 Market Share, limit per turn).
const PUBLIC_RELATIONS_STRIP = { key: "patent", label: "📣 PUBLIC RELATIONS", color: "#c084fc", rgb: "192,132,252",
  steps: ["+1 Market Share / turn (2 🔬)", "★ +$3 · +1 / turn", "+2 Market Share / turn", "★ 2nd Purple die · +2 / turn", "+3 Market Share / turn"] };
const TRACK_STRIPS_V034 = {
  triage: ["Bandwidth 2", "Bandwidth 3", "Bandwidth 4"],
  release: ["Bandwidth 4", "Bandwidth 5", "Bandwidth 6"],
  defense: ["Capacity 2", "Capacity 3", "Capacity 4"],
  patent: ["4 🔬 → 1 Secret", "3 🔬 → 1 Secret", "2 🔬 → 1 Secret"],
};

// v0.38.0 step texts (GLOSSARY.md: Triage 2/2/3/3/4, Release 4/4/5/5/6, Defense Grid 2/2/3/3/4; Breakthroughs at L1 / L3)
function v038Strip(t, p) {
  const regain = p.regain_cost || 3;
  if (t.key === "triage") return { ...t, steps: ["Bandwidth 2", "★ +1 Gray Legacy die", "Bandwidth 3", "★ $3: Gray → Market die", "Bandwidth 4 + 🔬 per die beyond 2nd"] };
  if (t.key === "defense") return { ...t, steps: ["Capacity 2", "★ +1 Gray Legacy die", "Capacity 3", "★ +1 Secret · Blue Secret face +1", "Capacity 4 + $1 per block (max $3)"] };
  if (t.key === "patent") return { ...t, steps: [`+1 Market Share / turn (${regain} 🔬)`, "★ +$3 · +1 / turn", "+2 Market Share / turn", "★ 2nd Purple die · +2 / turn", "+3 Market Share / turn"] };
  return t;
}

function renderTrackStrips(p) {
  const maxLvl = p.max_track_level === 2 ? 2 : 4;
  let strips = state.is_share_regain ? TRACK_STRIPS.map((t) => (t.key === "patent" ? PUBLIC_RELATIONS_STRIP : t)) : TRACK_STRIPS;
  if (state.is_secret_faces) strips = strips.map((t) => v038Strip(t, p));
  const cards = strips.map((t) => {
    const lvl = p[`${t.key}_level`] || 0;
    const steps = maxLvl === 4 ? t.steps : TRACK_STRIPS_V034[t.key];
    const cells = steps.map((txt, i) => {
      const on = i === lvl;
      const done = i < lvl;
      return `<span title="Level ${i}: ${txt}" style="flex: 1; text-align: center; font-size: 0.58rem; padding: 3px 1px; border-radius: 3px; background: ${on ? `rgba(${t.rgb},0.3)` : (done ? `rgba(${t.rgb},0.12)` : 'rgba(255,255,255,0.05)')}; color: ${on ? t.color : 'var(--text-dim)'}; border: 1px solid ${on ? t.color : 'transparent'}; font-weight: ${on ? '700' : 'normal'};">[L${i}] ${txt}</span>`;
    }).join("");
    return `
          <div class="track-card" style="border: 1px solid ${lvl >= 1 ? t.color : 'var(--border-color)'}; background: rgba(0,0,0,0.25); border-radius: 4px; padding: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 700; font-size: 0.75rem; color: ${t.color};">${t.label}</span>
              <span style="font-size: 0.65rem; color: var(--text-dim);">Level ${lvl}/${maxLvl}</span>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 3px; margin-top: 6px;">${cells}</div>
          </div>`;
  }).join("");
  return `<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">${cards}</div>`;
}

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
    name: "Meridian Financial Trust",
    sector: "Banking Infrastructure",
    overrideName: "Capital Injection",
    timing: "P3: INCOME",
    description: "Once per Rogue Agent Version, gain an immediate +$3 cash payout from the bank during Phase 3 Income.",
    themeColor: "#f59e0b",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4; Red starting die.",
  },
  OMNIDYNE: {
    code: "OMNIDYNE",
    name: "Omnidyne Systems",
    sector: "Industrial Automation",
    overrideName: "Magnetic Splice",
    timing: "P5: PIPELINE SHIFT",
    description: "Once per Rogue Agent Version, move 1 die from your Processing Box directly to Ready for Release for free (bypassing Scanned Box); it banks its Secret now.",
    themeColor: "#4ade80",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4; Green starting die.",
  },
  AEGIS: {
    code: "AEGIS",
    name: "Aegis Defense Relay",
    sector: "Telecommunications",
    overrideName: "Baffle Echo",
    timing: "P4: ATTACK RESOLUTION",
    description: "Once per Rogue Agent Version, ignore 1 attack cube (Red, Blue, or Green) when resolving compiler damage for yourself this round.",
    themeColor: "#38bdf8",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4; Blue starting die.",
  },
  DTO: {
    code: "DTO",
    name: "Dept. of Telecom Oversight [DTO]",
    sector: "Federal Agency",
    overrideName: "Slush Fund",
    timing: "P4: ATTACK RESOLUTION",
    description: "Once per game, absorb up to 2 Corporate Secret loss (from Blue Spyware) for free without paying cash.",
    themeColor: "#a855f7",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4; Blue starting die.",
  },
  HELIX: {
    code: "HELIX",
    name: "Helix Biomedical Consortium",
    sector: "Genomic R&D",
    overrideName: "Brute-Force Bypass",
    timing: "P1: REROLLS",
    description: "Once per Rogue Agent Version, during Phase 1 rerolls, gain 1 extra free reroll, and turn 1 rolled die to any legal non-Star face of its color (the Secret face is allowed).",
    themeColor: "#f43f5e",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4; Green starting die.",
  },
  PROMETHEUS: {
    code: "PROMETHEUS",
    name: "The Prometheus Foundation",
    sector: "Think Tank",
    overrideName: "Algorithmic Arbitrage",
    timing: "P6: OPERATIONS",
    description: "Once per Rogue Agent Version: buy 1 Central Market Colored Die at a $2 discount, or gain +$2 cash from the bank.",
    themeColor: "#00d4ff",
    startingSetupDesc: "Def Cap 2, Triage 2, Release 4; Red starting die.",
  },
};

const WHITE_HATS_DATA = {
  OPERATOR: {
    code: "OPERATOR",
    name: "The Operator",
    role: "Tactical Staffing & Logistics Lead",
    flavor: "Dedicated telemetry pipelines harvest live operational diagnostics on zero notice.",
    protocolName: "Logistics Bounty",
    protocolDesc: "Phase 3 Income, when rolled on Purple ★: gain +1 🔬 Research Token per Purple ★ die still In Production.",
    passiveDesc: "Harvests operational telemetry from active proprietary subroutines.",
    themeColor: "#f59e0b",
  },
  PHREAKER: {
    code: "PHREAKER",
    name: "The Phreaker",
    role: "Hardware Tinkerer // Emergency Relays",
    flavor: "A strip of Mylar splicing tape and a 2600-Hz whistle will fix what ten grand of silicon can't.",
    protocolName: "Jumper Diagnostics",
    protocolDesc: "Phase 3 Income, when rolled on Purple ★: move 1 die from your Processing Box to your Scanned Box, banking its Secret now. If the Processing Box is empty, roll 1 Scanned Box die and collect its $ / 🔬 (it stays in place); if Under Development is empty, gain +$1.",
    passiveDesc: "Diagnostic jumper triggers on an offline die in the Processing Box or Scanned Box.",
    themeColor: "#4ade80",
  },
  ACOUSTIC: {
    code: "ACOUSTIC",
    name: "The Acoustic",
    role: "Pattern Genius // Mainframe Resonance",
    flavor: "Every mainframe hums before it strikes. Listen to the baffles -- you can hear which packet drops next.",
    protocolName: "Harmonic Tap",
    protocolDesc: "Phase 3 Income: Gain +$1 for each distinct attack cube color in Exit Tray (Red, Blue, Green, Black; max +$4).",
    passiveDesc: "Converts compiler telemetry diversity directly into liquid capital.",
    themeColor: "#38bdf8",
  },
  SPOOK: {
    code: "SPOOK",
    name: "The Spook",
    role: "Ex-Intelligence // OpSec & Slush Funds",
    flavor: "Every breach has a price tag. That's what non-attributable slush accounts are for.",
    protocolName: "Burn Notice",
    protocolDesc: "Phase 3 Income: Gain +$2; optional: permanently return 1 owned colored die to market for +1 Corporate Secret.",
    passiveDesc: "Once per Purple ★ die in Phase 3, burn 1 owned colored die for +1 Secret.",
    themeColor: "#a855f7",
  },
  PRODIGY: {
    code: "PRODIGY",
    name: "The Prodigy",
    role: "Reckless Hacker // Lock Bypassing",
    flavor: "Locked memory is just a polite suggestion from someone who left debug interrupts enabled.",
    protocolName: "Zero-Day Override",
    protocolDesc: "Phase 1, when rolled on Purple ★: turn 1 other rolled die to any legal non-Star face of its color other than the Secret face.",
    passiveDesc: "Deterministic face manipulation during Phase 1 Roll & Deploy.",
    themeColor: "#f43f5e",
  },
  CIPHER: {
    code: "CIPHER",
    name: "The Cipher",
    role: "Mathematician // Algorithmic Arbitrage",
    flavor: "Why pay retail for entropy when SETEC's own arbitrage equations subsidize the upgrade?",
    protocolName: "Algorithmic Parity",
    protocolDesc: "Phase 3 Income: Collect +$2 cash and +1 🔬 Research Token.",
    passiveDesc: "Purple Specialist Die faces yield optimized cryptographic output.",
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
  switcherBar.className = "terminal-switcher-bar";

  const switcherTitle = document.createElement("div");
  switcherTitle.className = "switcher-title";
  switcherTitle.innerHTML = `<span class="switcher-dot">●</span> COMPANY TERMINALS:`;
  switcherBar.appendChild(switcherTitle);

  const tabsWrap = document.createElement("div");
  tabsWrap.className = "switcher-tabs";

  state.players.forEach((p) => {
    const isSelected = (currentTab !== "all" && Number(currentTab) === p.player_id);
    const isHuman = Boolean(p.is_human);
    const isTurn = (p.player_id === state.active_player_index && state.phase === 6);
    const isFirstPlayer = (p.player_id === state.first_player_index);

    const tabBtn = document.createElement("button");
    tabBtn.className = `terminal-tab-btn ${isSelected ? "active" : ""} ${isTurn ? "turn-active" : ""}`;
    tabBtn.innerHTML = `
      <span class="tab-player-icon">${isHuman ? "👤" : "🤖"}</span>
      <span class="tab-player-name">${p.name}</span>
      ${isFirstPlayer ? '<span class="tab-first-player-tag">1ST PLAYER</span>' : ''}
      <span class="tab-vp-badge">${p.secrets} Secrets${p.market_share !== null && p.market_share !== undefined ? ` · ${p.market_share} MS` : ''}</span>
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
    const isTurn = (p.player_id === state.active_player_index && state.phase === 6);
    const isFirstPlayerMat = (p.player_id === state.first_player_index);

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

    const slotsGlitched = p.glitched_shield_slots || 0;
    const effCap = p.effective_defense_capacity !== undefined ? p.effective_defense_capacity : (p.defense_capacity || 2);
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
          <span class="terminal-tag">TOO MANY SECRETS // COMPANY TERMINAL MAT</span>
          <span class="terminal-id">[TERM-0${p.player_id + 1}]</span>
          ${p.is_human ? '<span class="terminal-human-badge">HUMAN</span>' : `<span class="terminal-bot-badge">${p.bot_archetype || 'BOT'}</span>`}
        </div>
        <div class="terminal-banner-right">
          ${isFirstPlayerMat ? '<span class="first-player-pill">★ FIRST PLAYER</span>' : ''}
          ${p.is_patient_zero ? '<span class="breach-pill">TOTAL DATA BREACH</span>' : ''}
          <span class="vp-pill">${p.secrets} Secrets</span>${p.market_share !== null && p.market_share !== undefined ? `<span class="vp-pill" title="Market Share" style="color: #f43f5e;">📈 ${p.market_share}/${p.market_share_max}</span>` : ''}
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
                      ? `Free Rerolls: <strong>${p.rerolls_remaining || 0}</strong>/${p.max_rerolls || 2} | Click dice to reroll (a Secret face may be kept or rerolled) | Contractor Glitches lock` 
                      : `Phase 1 Rolling | Secret faces → Processing Box after rerolls`)
                  : (p.has_committed 
                      ? (readyCount > 0 ? 'Dice ready for next round' : 'All dice deployed to In Production | Scanned dice graduate here in Phase 5 (≤ Release Bandwidth)')
                      : 'Start: 2 Gray + 1 Company colored die + 1 Purple Specialist Die | Phase 1: Roll all Ready + hired Contractors | Offline dice do not roll')}
              </div>
            </div>
            ${isActivelyRolling ? `
            <div class="zone-watermark-note">
              ROLLED POOL // YAHTZEE REROLLS // DEPLOY TO IN PRODUCTION
            </div>` : ''}
            <div class="dice-tray ready-tray" id="ready_tray_${p.player_id}"></div>
          </div>

          <!-- Zone 2: In Production (Income slot + Defense Grid of Generic (Any) shields) -->
          <div class="operational-zone production-zone-panel" style="border: 1px solid rgba(56, 189, 248, 0.3); background: rgba(15, 23, 42, 0.4); border-radius: 6px; padding: 10px; margin-bottom: 12px;">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name" style="color: #38bdf8;">IN PRODUCTION</span>
                <span class="zone-count-badge">(${(p.in_production_dice || []).length})</span>
                <span class="zone-count-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; font-size: 0.7rem;">SHIELDS: ${redShieldDice.length + blueShieldDice.length + greenShieldDice.length + anyShieldDice.length}/${effCap} CAP</span>
              </div>
              <div class="zone-subtext">
                Income: Collect $, 🔬, ★ in Phase 3 | Defense Grid Capacity: max ${effCap} shields${slotsGlitched > 0 ? ` (${p.defense_capacity || 2} minus ${slotsGlitched} Glitched Shield Slot${slotsGlitched > 1 ? 's' : ''})` : ''}${p.defense_level >= 4 && p.max_track_level === 4 ? ' | Defense L4: +$1 per blocked Attack Cube (max $3)' : ''}
              </div>
            </div>

            <!-- In Production Grid: Income Slot + Unified Defense Grid -->
            <div class="production-matrix-row" style="display: grid; grid-template-columns: 1fr 2fr; gap: 8px; margin-top: 8px;">
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
                <div class="shield-desc-sub2">$, 🔬, ★ in Phase 3</div>
                <div class="shield-slots-tray" id="income_tray_${p.player_id}"></div>
              </div>

              <!-- Unified Defense Grid -->
              <div class="shield-box defense-grid-box" style="border-color: #38bdf8; background: rgba(56, 189, 248, 0.06);">
                <div class="shield-header-bar" style="display: flex; justify-content: space-between; align-items: center;">
                  <div class="shield-title">
                    <span class="shield-symbol" style="color: #38bdf8;">🛡️</span>
                    <span style="color: #38bdf8;">DEFENSE GRID</span>
                    <span class="shield-count">(${redShieldDice.length + blueShieldDice.length + greenShieldDice.length + anyShieldDice.length}/${effCap} CAP)</span>
                    ${slotsGlitched > 0 ? `<span class="shield-count" style="color: #f43f5e;" title="Glitched Shield Slots cannot hold a shield (clean in Phase 1 or Phase 5)">⚠️ ${slotsGlitched} GLITCHED SHIELD SLOT${slotsGlitched > 1 ? 'S' : ''}</span>` : ''}
                  </div>
                  <div style="font-size: 0.65rem; color: var(--text-dim);">
                    Generic (Any) shields only
                  </div>
                </div>
                <div class="shield-desc-sub1">Generic (Any) Shields Against Compiler Threats</div>
                <div class="shield-desc-sub2">In Phase 4 you split them across the exited Red, Blue and Green cubes.</div>
                <div class="shield-slots-tray defense-grid-unified-tray" id="defense_grid_${p.player_id}" style="display: flex; flex-wrap: wrap; gap: 6px; min-height: 36px; padding: 4px; background: rgba(0,0,0,0.2); border-radius: 4px;"></div>
              </div>
            </div>

            <!-- Shield Persistence Note -->
            <div class="wear-transition-caption" style="margin-top: 8px;">
              <span style="color: #4ade80;">Shields stay In Production through Phase 4, then return through the Scanned Box in Phase 5.</span>
            </div>
          </div>

          <!-- Zone 3: Under Development (Processing Box -> Scanned Box) -->
          <div class="operational-zone pipeline-zone-panel" style="border: 1px solid rgba(244, 63, 94, 0.3); background: rgba(15, 23, 42, 0.4); border-radius: 6px; padding: 10px; margin-bottom: 12px;">
            <div class="zone-header-strip">
              <div class="zone-title-wrap">
                <span class="zone-name" style="color: #f43f5e;">UNDER DEVELOPMENT (CI/CD PIPELINE)</span>
                <span class="zone-count-badge">(${p.under_development_count !== undefined ? p.under_development_count : ((p.glitched_dice || []).length + (p.scanned_dice || []).length)})</span>
                <span class="zone-count-badge" style="background: rgba(244, 63, 94, 0.2); color: #f43f5e; font-size: 0.7rem;">TRIAGE: ${p.triage_bandwidth || 2}/RND | RELEASE: ${p.release_bandwidth || 4}/RND</span>
              </div>
              <div class="zone-subtext">
                Processing Box → Scanned Box → Ready for Release${p.triage_level >= 4 && p.max_track_level === 4 ? ' | Triage L4: +1 🔬 per die moved beyond the 2nd' : ''}
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
              <!-- Processing Box -->
              <div style="border: 1px solid rgba(244, 63, 94, 0.4); background: rgba(244, 63, 94, 0.08); border-radius: 6px; padding: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <span style="font-weight: 600; color: #f43f5e; font-size: 0.85rem;">🔒 PROCESSING BOX (${(p.glitched_dice || []).length})</span>
                  <span style="font-size: 0.75rem; color: var(--text-dim);">Secret faces, oldest first</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 6px;">
                  Conveyor Triage in Phase 5 moves up to ${p.triage_bandwidth || 2} dice to the Scanned Box, oldest first, banking each Secret face yield
                </div>
                <div class="dice-tray" id="glitched_tray_${p.player_id}" style="min-height: 48px;"></div>
              </div>

              <!-- Scanned Box -->
              <div style="border: 1px solid rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.08); border-radius: 6px; padding: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <span style="font-weight: 600; color: #38bdf8; font-size: 0.85rem;">✓ SCANNED BOX (${(p.scanned_dice || []).length})</span>
                  <span style="font-size: 0.75rem; color: ${(p.scanned_over_release || 0) > 0 ? '#f59e0b' : '#4ade80'};">Release Bandwidth: ${Math.min((p.scanned_dice || []).length, p.release_bandwidth || 4)} / ${p.release_bandwidth || 4}${(p.scanned_over_release || 0) > 0 ? ` (${p.scanned_over_release} over)` : ''}</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 6px;">
                  In Production → Scanned Box → Ready for Release in Phase 5 (≤ Release Bandwidth, your choice)
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
            <span style="font-size: 0.65rem; color: var(--text-dim); margin-left: 8px;">Spend 🔬 in Phase 6: Operations</span>
          </div>
          <div style="font-size: 0.7rem; color: #a855f7;">
            ${p.max_track_level === 4 ? 'Step costs 1 / 2 / 2 / 3 🔬 · ★ = Breakthrough (L1, L3)' : ''}
          </div>
        </div>

        ${renderTrackStrips(p)}
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
            Start: $6 (Meridian: $8) | Never drops below $0
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
            Hardware Upgrades | ${p.patent_track_name || 'Public Relations Track'}
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
            ${p.secrets <= 0 ? '<strong style="color: #ff0055;">TOTAL DATA BREACH (PATIENT ZERO)</strong>' : (state.starting_secrets !== undefined && state.starting_secrets !== null ? `Start: ${state.starting_secrets} — ≤0 = Total Breach` : '≤0 = Total Breach')}
          </div>
        </div>

        ${p.market_share !== null && p.market_share !== undefined ? `
        <!-- 3b. Market Share (v0.36.0) -->
        <div class="reserve-card market-share-card" style="border-color: rgba(244, 63, 94, 0.45);">
          <div class="reserve-card-header">
            <span class="reserve-card-title" style="color: #f43f5e;">📈 MARKET SHARE</span>
            <span class="reserve-rate-pill" style="background: rgba(244, 63, 94, 0.18); color: #f43f5e;">MAX ${p.market_share_max}</span>
          </div>
          <div class="reserve-card-main">
            <span class="reserve-secrets-value ${p.market_share <= 3 ? 'critical' : ''}" style="color: #f43f5e;">${p.market_share}</span>
          </div>
          <div class="reserve-card-footer ${p.market_share <= 0 ? 'breach-alert' : ''}">
            ${p.market_share <= 0 ? '<strong style="color: #ff0055;">MARKET COLLAPSE (FINAL ROUND)</strong>' : `−1 per unblocked Red | Regain: ${p.regain_cost} 🔬 each, +${p.regain_cap} / turn`}
            ${(() => {
              const sched = state.is_round_leader_bonus ? state.round_leader_bonus_schedule : (state.is_market_leader_bonus ? state.market_leader_bonus_schedule : []);
              if (!sched || !sched.length) return '';
              const txt = sched.map((b, i) => `${i + 1}${["st", "nd", "rd"][i] || "th"} +${b}`).filter((t) => !t.endsWith("+0")).join(" · ");
              const when = state.is_round_leader_bonus ? "after Phase 5 when a Red Secret face was banked, and at game end" : "at game end";
              return `<br><span title="Market Leader Bonus: survivors gain Corporate Secrets by Market Share place (ties share the better place)">Market Leader Bonus (${when}): ${txt}</span>`;
            })()}
          </div>
        </div>` : ''}

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
            <div class="patch-token-slot ${(p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 1) >= 1 ? 'filled' : 'empty'}" style="border-color: #a855f7;" title="${(p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 1) >= 1 ? 'Die 2: In Personal Reserve' : 'Die 2: Released'}">
              <span class="slot-number-lbl">DIE 2</span>
              <span class="slot-wrench-icon" style="color: #c084fc;">${(p.personal_purple_reserve !== undefined ? p.personal_purple_reserve : 1) >= 1 ? (p.purple_purchasable === false ? (state.is_share_regain ? 'PR L3' : 'PAT L3') : `▼ $${p.purple_reserve_cost !== undefined ? p.purple_reserve_cost : 4}`) : '✓'}</span>
            </div>
          </div>
          <div class="reserve-card-footer">
            ${p.purple_purchasable === false ? `Die 1: Setup | Die 2: ${state.is_share_regain ? 'Public Relations' : 'Patents'} L3 Breakthrough` : (p.can_buy_purple_reserve ? `<strong style="color: #c084fc;">CLICK TO PROCURE ($${p.purple_reserve_cost !== undefined ? p.purple_reserve_cost : 4})</strong>` : 'Die 1: Setup | Die 2: Reserve ($' + (p.purple_reserve_cost !== undefined ? p.purple_reserve_cost : 4) + ')')}
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
          if (d.current_face && d.current_face.secrets_pending) badgeHtml += `<span class="badge-choice">🔒 SECRET → PROCESSING BOX</span> `;

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

    // Unified Defense Grid Tray
    const defenseGridTray = terminalMat.querySelector(`#defense_grid_${p.player_id}`);
    if (defenseGridTray) {
      let totalShieldDice = 0;
      ["any", "red", "blue", "green"].forEach((c) => {
        const slotDice = (p.shield_slots && p.shield_slots[c] && p.shield_slots[c].length)
          ? p.shield_slots[c]
          : ((p.production_slots && p.production_slots[`${c}_shield`]) || []);
        slotDice.forEach((d) => {
          totalShieldDice++;
          const item = document.createElement("div");
          item.className = `shield-die-chip ${d.color}`;
          item.innerText = `${d.color.toUpperCase()}: ${d.current_face ? d.current_face.name : 'Shield'}`;
          defenseGridTray.appendChild(item);
        });
      });
      if (totalShieldDice === 0) {
        const emptyMsg = document.createElement("div");
        emptyMsg.className = "empty-tray-msg";
        emptyMsg.style.fontSize = "0.68rem";
        emptyMsg.style.color = "var(--text-muted)";
        emptyMsg.style.fontStyle = "italic";
        emptyMsg.style.padding = "4px 8px";
        emptyMsg.innerText = "No defense dice deployed";
        defenseGridTray.appendChild(emptyMsg);
      }
    }

    // Processing Box Tray (oldest first; the first Triage Bandwidth dice move in Phase 5)
    const glitchedTray = terminalMat.querySelector(`#glitched_tray_${p.player_id}`);
    if (glitchedTray) {
      (p.processing_box_dice || p.glitched_dice || []).forEach((d, i) => {
        const chip = document.createElement("div");
        chip.className = `die-chip ${d.color}`;
        const nextUp = d.will_triage !== undefined ? d.will_triage : i < (p.triage_bandwidth || 2);
        chip.title = `Secret face (entered #${d.processing_entry_seq}): banks ${d.secret_yield !== undefined ? '+' + d.secret_yield : 'its yield'} Corporate Secrets when it leaves the Processing Box${nextUp ? " (next Conveyor Triage)" : ""}`;
        chip.innerHTML = `<span>${d.color.toUpperCase()} <span class="badge-choice">#${i + 1}${d.secret_yield !== undefined ? ` · +${d.secret_yield} Secrets` : ''}</span>${nextUp ? ' <span class="badge-contractor">NEXT</span>' : ''}</span>`;
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
