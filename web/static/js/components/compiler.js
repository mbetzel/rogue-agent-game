/**
 * Rogue Agent — Central Threat & Compiler Board (SETEC Mainframe)
 * Structured faithfully after Print-and-Play Central Game Board Page 1 (02_Central_Game_Boards.pdf)
 */

import { state } from "../state.js";
import { openModal } from "./modals.js";

function formatPayload(payload) {
  if (!payload) return "None";
  const parts = [];
  if (payload.red) parts.push(`+${payload.red} Red`);
  if (payload.blue) parts.push(`+${payload.blue} Blue`);
  if (payload.green) parts.push(`+${payload.green} Green`);
  if (payload.black) parts.push(`+${payload.black} Black`);
  return parts.length > 0 ? parts.join(", ") : "None";
}

export function renderCompiler() {
  if (!state) return;

  const compilerRoot = document.getElementById("centralAgentBoard");
  if (!compilerRoot) return;

  const activeVerIdx = state.current_version_index !== undefined ? state.current_version_index : 0;
  const versionDeck = state.version_deck || [];
  const v1 = versionDeck[0] || state.active_version || { name: "Script Kiddie", version_str: "v1.0", directive_description: "Standard initialization.", staging_payload: { red: 2, blue: 2, green: 2, black: 2 } };
  const v2 = versionDeck[1] || { name: "Worm Protocol", version_str: "v2.0", directive_description: "Payload escalation across nodes.", staging_payload: { red: 1, blue: 1, green: 1, black: 1 } };
  const v3 = versionDeck[2] || { name: "Autonomous Singularity", version_str: "v3.0", directive_description: "Autonomous self-directed threat synthesis.", staging_payload: { red: 1, blue: 1, green: 1, black: 1 } };

  const playerCount = state.players ? state.players.length : 4;
  const capacity = state.corruption_capacity || (playerCount === 2 ? 4 : playerCount === 3 ? 5 : 6);
  const currentTrack = state.corruption_track || 0;

  compilerRoot.innerHTML = `
    <!-- Top Central Board Outer Banner -->
    <div class="agent-board-banner">
      <div class="agent-board-banner-left">
        <span class="board-title-main">PROJECT: SETEC // CENTRAL ROGUE AGENT & COMPILER BOARD</span>
        <span class="board-round-tag">ROUND ${state.current_round || 1}</span>
      </div>
      <div class="agent-board-banner-right">
        <span class="board-sub-tag">PLACE VERSION TILES ON LEFT | DROP CUBE TOWER IN PHASE 2</span>
        <button class="info-icon-btn" onclick="openModal('cubeEffectsModal')" title="View Agent Cube Threat Reference">ℹ</button>
      </div>
    </div>

    <!-- 3-Column Spatial Grid -->
    <div class="agent-board-grid">
      
      <!-- ========================================================= -->
      <!-- COLUMN 1 (Left): Version Roadmap & Corruption Track        -->
      <!-- ========================================================= -->
      <div class="agent-board-col roadmap-col">
        <div class="col-title-bar">
          <span class="col-title">VERSION ROADMAP</span>
          <button class="action-btn" style="font-size: 0.7rem; padding: 2px 8px;" onclick="openModal('versionsModal')" title="View Detailed Roadmap">Roadmap Details</button>
        </div>

        <div class="version-tiers-stack">
          <!-- v3.0 Singularity Tier -->
          <div class="version-tier-card v3-tier ${activeVerIdx === 2 ? 'active-version' : ''} ${activeVerIdx > 2 ? 'completed-version' : ''}">
            <div class="tier-card-header">
              <span class="tier-badge v3">v3.0</span>
              <span class="tier-name">${v3.name.toUpperCase()}</span>
              <span class="tier-level-tag">SINGULARITY</span>
            </div>
            <div class="tier-directive">${v3.directive_description}</div>
            <div class="tier-payload-strip">
              <span class="payload-lbl">Payload:</span>
              <span class="payload-val">${formatPayload(v3.staging_payload)}</span>
            </div>
            ${activeVerIdx === 2 ? '<div class="active-pulse-badge">● CURRENTLY ACTIVE</div>' : (activeVerIdx > 2 ? '<div class="completed-badge">✓ ARCHIVED</div>' : '<div class="upcoming-badge">UPCOMING</div>')}
          </div>

          <div class="roadmap-arrow-strip">
            <span>▲ UPGRADE WHEN TRACK FILLS ▲</span>
          </div>

          <!-- v2.0 Escalation Tier -->
          <div class="version-tier-card v2-tier ${activeVerIdx === 1 ? 'active-version' : ''} ${activeVerIdx > 1 ? 'completed-version' : ''}">
            <div class="tier-card-header">
              <span class="tier-badge v2">v2.0</span>
              <span class="tier-name">${v2.name.toUpperCase()}</span>
              <span class="tier-level-tag">ESCALATION</span>
            </div>
            <div class="tier-directive">${v2.directive_description}</div>
            <div class="tier-payload-strip">
              <span class="payload-lbl">Upgrade:</span>
              <span class="payload-val">${formatPayload(v2.staging_payload)}</span>
            </div>
            ${activeVerIdx === 1 ? '<div class="active-pulse-badge">● CURRENTLY ACTIVE</div>' : (activeVerIdx > 1 ? '<div class="completed-badge">✓ ARCHIVED</div>' : '<div class="upcoming-badge">UPCOMING</div>')}
          </div>

          <div class="roadmap-arrow-strip">
            <span>▲ UPGRADE WHEN TRACK FILLS ▲</span>
          </div>

          <!-- v1.0 Initial Tier -->
          <div class="version-tier-card v1-tier ${activeVerIdx === 0 ? 'active-version' : ''} ${activeVerIdx > 0 ? 'completed-version' : ''}">
            <div class="tier-card-header">
              <span class="tier-badge v1">v1.0</span>
              <span class="tier-name">${v1.name.toUpperCase()}</span>
              <span class="tier-level-tag">INITIAL (START)</span>
            </div>
            <div class="tier-directive">${v1.directive_description}</div>
            <div class="tier-payload-strip">
              <span class="payload-lbl">Setup:</span>
              <span class="payload-val">${formatPayload(v1.staging_payload)}</span>
            </div>
            ${activeVerIdx === 0 ? '<div class="active-pulse-badge">● CURRENTLY ACTIVE</div>' : '<div class="completed-badge">✓ ARCHIVED</div>'}
          </div>
        </div>

        <!-- Corruption Track Box directly beneath v1.0 -->
        <div class="agent-corruption-track-box">
          <div class="agent-track-header">
            <span class="track-title">CORRUPTION TRACK (${capacity} SPACES)</span>
            <span class="track-step-badge">STEP 2A</span>
          </div>

          <div class="agent-track-cells-row">
            ${(() => {
              const activeCard = versionDeck[activeVerIdx] || state.active_version || v1;
              const spaces = activeCard.corruption_track || [];
              const cells = [];
              for (let i = 0; i < capacity; i++) {
                const isFilled = i < currentTrack;
                const space = spaces[i] || {};
                const label = space.label || `Space ${i + 1}`;
                const isMilestone = (i === capacity - 1);
                cells.push(`
                  <div class="agent-corruption-cell ${isFilled ? 'filled' : ''} ${isMilestone ? 'milestone-cell' : ''}" title="Space ${i + 1}: ${label}">
                    <span class="cell-num">${i + 1}</span>
                    <span class="cell-sub" style="font-size: 0.55rem; max-width: 50px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${label}</span>
                    ${isFilled ? '<span class="cell-cube">■</span>' : ''}
                  </div>
                `);
              }
              return cells.join("");
            })()}
          </div>

          <div class="agent-track-footnote">
            <strong>Step 2A:</strong> Each exited ■ Black advances track 1 space and triggers its printed effect. Fills at <strong>${capacity} spaces</strong>: advance Version (v3.0 fill = <strong>SINGULARITY</strong>).
            ${state.active_phase1_locks && state.active_phase1_locks.length > 0 ? `<div style="color: #ff3366; font-weight: bold; margin-top: 3px;">⚠️ Phase 1 Locks Active: ${state.active_phase1_locks.join(', ')}</div>` : ''}
            ${state.pending_next_phase_locks && state.pending_next_phase_locks.length > 0 ? `<div style="color: #ffaa00; font-weight: bold; margin-top: 3px;">⏳ Queued Next Phase 1 Locks: ${state.pending_next_phase_locks.join(', ')}</div>` : ''}
          </div>
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- COLUMN 2 (Middle): Threat Compiler & Cube Tower            -->
      <!-- ========================================================= -->
      <div class="agent-board-col compiler-col">
        <div class="col-title-bar">
          <span class="col-title">AGENT THREAT COMPILER & CUBE TOWER</span>
        </div>

        <!-- Staging Cup & Internal Baffles Dual-Box -->
        <div class="tower-containers-grid">
          <!-- Staging Cup -->
          <div class="tower-box staging-cup-box">
            <div class="box-hdr">
              <span class="box-hdr-title">STAGING CUP (RELAY QUEUE)</span>
            </div>
            <div class="cup-circle-graphic">
              <div class="circle-inner">
                <span class="circle-tag">STAGING</span>
                <span class="circle-tag">CUP</span>
              </div>
            </div>
            <div class="cube-tray" id="stagingCupTray">
              <span class="cube-badge red">${state.staging_cup ? state.staging_cup.red : 0} Red</span>
              <span class="cube-badge blue">${state.staging_cup ? state.staging_cup.blue : 0} Blue</span>
              <span class="cube-badge green">${state.staging_cup ? state.staging_cup.green : 0} Green</span>
              <span class="cube-badge black">${state.staging_cup ? state.staging_cup.black : 0} Black</span>
            </div>
            <div class="box-ftr">
              Queued for next drop: P1 Pulse (+1 Black), recycled attacks, Version payloads, & Siphons.
            </div>
          </div>

          <!-- Cube Tower Stuck (Internal Baffles) -->
          <div class="tower-box tower-stuck-box">
            <div class="box-hdr">
              <span class="box-hdr-title">CUBE TOWER (INTERNAL BAFFLES)</span>
            </div>
            <div class="baffles-graphic">
              <div class="baffle-lines-art"></div>
              <span class="baffle-tag">${state.tower_total_stuck || 0} STUCK</span>
            </div>
            <div class="cube-tray" id="towerStuckTray">
              <span class="cube-badge red">${state.tower_stuck_cubes ? state.tower_stuck_cubes.red : 0} Red</span>
              <span class="cube-badge blue">${state.tower_stuck_cubes ? state.tower_stuck_cubes.blue : 0} Blue</span>
              <span class="cube-badge green">${state.tower_stuck_cubes ? state.tower_stuck_cubes.green : 0} Green</span>
              <span class="cube-badge black">${state.tower_stuck_cubes ? state.tower_stuck_cubes.black : 0} Black</span>
            </div>
            <div class="box-ftr">
              Stuck cubes create latent tension; prime subsequent drops with unpredictable releases.
            </div>
          </div>
        </div>

        <!-- Compiler Exit Sorting Tray (2A: Black, 2B: Red, 2B: Blue, 2B: Green) -->
        <div class="exit-sorting-tray-card">
          <div class="exit-tray-hdr">
            <span class="exit-tray-title">COMPILER EXIT TRAY (SORTING)</span>
            <span class="exit-tray-sub">Sort exited Cube Tower packets here before resolving Step 2A → 2B</span>
          </div>

          <div class="exit-pockets-grid" id="lastCompileResult">
            ${(() => {
              if (state.last_compile_result) {
                const res = state.last_compile_result;
                return `
                  <div class="exit-pocket black-pocket">
                    <div class="pocket-color-tag">2A: BLACK</div>
                    <div class="pocket-val">+${res.exited_cubes.black}</div>
                    <div class="pocket-sub">Corruption</div>
                  </div>
                  <div class="exit-pocket red-pocket">
                    <div class="pocket-color-tag">2B: RED</div>
                    <div class="pocket-val">${res.exited_cubes.red} (Atk: ${res.attack_strengths.red})</div>
                    <div class="pocket-sub">Ransomware</div>
                  </div>
                  <div class="exit-pocket blue-pocket">
                    <div class="pocket-color-tag">2B: BLUE</div>
                    <div class="pocket-val">${res.exited_cubes.blue} (Atk: ${res.attack_strengths.blue})</div>
                    <div class="pocket-sub">Spyware</div>
                  </div>
                  <div class="exit-pocket green-pocket">
                    <div class="pocket-color-tag">2B: GREEN</div>
                    <div class="pocket-val">${res.exited_cubes.green} (Atk: ${res.attack_strengths.green})</div>
                    <div class="pocket-sub">Malware</div>
                  </div>
                `;
              }
              return `
                <div class="exit-pocket black-pocket"><div class="pocket-color-tag">2A: BLACK</div><div class="pocket-val">0</div><div class="pocket-sub">Corruption</div></div>
                <div class="exit-pocket red-pocket"><div class="pocket-color-tag">2B: RED</div><div class="pocket-val">0</div><div class="pocket-sub">Ransomware</div></div>
                <div class="exit-pocket blue-pocket"><div class="pocket-color-tag">2B: BLUE</div><div class="pocket-val">0</div><div class="pocket-sub">Spyware</div></div>
                <div class="exit-pocket green-pocket"><div class="pocket-color-tag">2B: GREEN</div><div class="pocket-val">0</div><div class="pocket-sub">Malware</div></div>
              `;
            })()}
          </div>
        </div>

        <!-- Agent Cube Effects Breakdown Stack -->
        <div class="cube-threat-effects-list">
          <div class="cube-threat-row black-row">
            <span class="threat-pill black">■ BLACK // CORRUPTION</span>
            <div class="threat-row-text">
              <strong>Step 2A (First):</strong> Advance Corruption Track 1 space per exited Black. Fills at capacity: advance Version & add payload. <strong>v3.0 fill = SINGULARITY!</strong>
            </div>
          </div>
          <div class="cube-threat-row red-row">
            <span class="threat-pill red">◆ RED // RANSOMWARE</span>
            <div class="threat-row-text">
              <strong>Blocks: Red Shield.</strong> Lose $1 per unblocked Red. At $0, held 🔧 tokens auto-absorb $1 each. <em>Ransom Leak: unpaid $1 loses 1 Secret each!</em>
            </div>
          </div>
          <div class="cube-threat-row blue-row">
            <span class="threat-pill blue">● BLUE // SPYWARE</span>
            <div class="threat-row-text">
              <strong>Blocks: Blue Shield.</strong> Lose 1 Corporate Secret per unblocked Blue. <strong>Reaching ≤ 0 Secrets triggers Total Data Breach (Patient Zero)!</strong>
            </div>
          </div>
          <div class="cube-threat-row green-row">
            <span class="threat-pill green">▲ GREEN // MALWARE</span>
            <div class="threat-row-text">
              <strong>Blocks: Green Shield.</strong> Move 1 Ready die → Unpatched per unblocked Green. Ready Yellow dice MUST be demoted first! If 0 Ready/Contractor: <em>Destroy 1 Unpatched die!</em>
            </div>
          </div>
        </div>

        <div class="wear-recycle-summary-box">
          <strong>WEAR:</strong> Permanent Shields blocking ≥ 1 cube move to Unpatched Zone. 0 blocked = stay Ready. Contractors return to supply.<br>
          <strong>RECYCLE:</strong> Exited Red, Blue, and Green cubes recycle back into the Staging Cup.
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- COLUMN 3 (Right): Game Sequence Reference & Portfolio     -->
      <!-- ========================================================= -->
      <div class="agent-board-col sequence-col">
        <div class="col-title-bar">
          <span class="col-title">GAME SEQUENCE OVERVIEW</span>
        </div>

        <div class="sequence-cards-stack">
          <!-- Phase 1 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 1: BOOT & CONFIGURE (Simultaneous)</div>
            <div class="seq-card-body">
              <strong>1. Pulse:</strong> Add +1 Black → Staging Cup.<br>
              <strong>2. Staffing:</strong> Hire White Contractors ($1 / $2 / $3, max 3).<br>
              <strong>3. Roll Pool:</strong> Roll Ready Zone + hired Contractors.<br>
              <strong>4. Rerolls:</strong> Up to 2 free rerolls of unlocked dice. Spend 1 🔧 to Unlock 1 🔒 die.<br>
              <strong>5. Assign:</strong> Commit Shields & declare ( / ) choice faces.<br>
              <strong>6. Outputs:</strong> Unassigned dice collect $, 🔧 (max 3), & Boot ★.
            </div>
          </div>

          <!-- Phase 2 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 2: SETEC COMPILE (Simultaneous)</div>
            <div class="seq-card-body">
              <strong>Drop</strong> entire Staging Cup into Cube Tower.<br>
              <strong>2A.</strong> Resolve Black cubes on Corruption Track.<br>
              <strong>2B.</strong> Resolve Red/Blue/Green attacks; apply Wear & damage; recycle exited R/B/G → Staging Cup.<br>
              <strong>Buffer Overflow:</strong> If 0 cubes exit, idle cycle injects +1 R, +1 B, +1 G into cup for next round.<br>
              <strong>2C. End Check:</strong> Singularity OR any player ≤ 0 Secrets triggers Final Round.
            </div>
          </div>

          <!-- Phase 3 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 3: OPERATIONS (Clockwise Turns)</div>
            <div class="seq-card-body">
              1. <strong>Buy Dice (max 2):</strong> Pay $ → place into Ready Zone.<br>
              2. <strong>Patch Dice (unlimited):</strong> Pay 1 🔧 or $2 per die → Ready Zone.<br>
              3. <strong>Backdoor Siphon (max 1):</strong> Pay 1 Secret + demote 1 Ready + 1 Black → Cup => Gain +$3.<br>
              4. <strong>System Reboot (1x/game):</strong> If 0 Ready dice, return all Gray Starter from Unpatched → Ready.<br>
              5. <strong>Cleanup:</strong> Un-worn dice stay Ready; pass CISO clockwise.
            </div>
          </div>

          <!-- Scoring -->
          <div class="seq-card portfolio-scoring-card">
            <div class="seq-card-header">END-GAME PORTFOLIO SCORING</div>
            <div class="seq-card-body">
              <strong>Surviving Firms Only</strong> (Patient Zero eliminated):<br>
              <strong>4 VP</strong> / Corporate Secret<br>
              <strong>4 VP</strong> / Ready Blue or Yellow Die<br>
              <strong>3 VP</strong> / Ready Red, Green, or Purple Die<br>
              <strong>1 VP</strong> / $2 Cash | <strong>0 VP</strong> / 🔧 Patches<br>
              <em>Ties: 1. Secrets, 2. Cash. (Wipeout: overflow penalties).</em>
            </div>
          </div>
        </div>
      </div>

    </div>
  `;
}
