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
  const v1 = versionDeck[0] || state.active_version || { name: "Script Kiddie", version_str: "v1.0", staging_payload: { red: 2, blue: 2, green: 2 } };
  const v2 = versionDeck[1] || { name: "Ransomware-as-a-Service", version_str: "v2.0", staging_payload: {} };
  const v3 = versionDeck[2] || { name: "Zero-Day Override", version_str: "v3.0", staging_payload: {} };

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
            <div class="tier-track-info">
              <span class="track-spaces-badge">${v3.corruption_track ? v3.corruption_track.length : 6} Corruption Spaces</span>
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
            <div class="tier-track-info">
              <span class="track-spaces-badge">${v2.corruption_track ? v2.corruption_track.length : 5} Corruption Spaces</span>
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
            <div class="tier-payload-strip">
              <span class="payload-lbl">Setup Cup:</span>
              <span class="payload-val">${formatPayload(v1.staging_payload)}</span>
            </div>
            <div class="tier-track-info">
              <span class="track-spaces-badge">${v1.corruption_track ? v1.corruption_track.length : 4} Corruption Spaces${v1.starting_cash_bonus ? ` (+$${v1.starting_cash_bonus} Start)` : ''}</span>
            </div>
            ${activeVerIdx === 0 ? '<div class="active-pulse-badge">● CURRENTLY ACTIVE</div>' : '<div class="completed-badge">✓ ARCHIVED</div>'}
          </div>
        </div>

        <!-- Corruption Track Box directly beneath v1.0 -->
        <div class="agent-corruption-track-box">
          <div class="agent-track-header">
            <span class="track-title">CORRUPTION TRACK (${capacity} SPACES)</span>
            <span class="track-step-badge">PHASE 2</span>
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
            <strong>Phase 2: Compiler Drop &amp; Corruption:</strong> Each exited ■ Black advances track 1 space and triggers its printed effect. Fills at <strong>${capacity} spaces</strong>: advance Version (v3.0 fill = <strong>SINGULARITY</strong>).
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

        <!-- Compiler Exit Sorting Tray (Phase 2: Black; Phase 4: Red, Blue, Green) -->
        <div class="exit-sorting-tray-card">
          <div class="exit-tray-hdr">
            <span class="exit-tray-title">COMPILER EXIT TRAY (SORTING)</span>
            <span class="exit-tray-sub">Black resolves in Phase 2: Compiler Drop &amp; Corruption; Red / Blue / Green wait here for Phase 4: Attack Resolution</span>
          </div>

          <div class="exit-pockets-grid" id="lastCompileResult">
            ${(() => {
              if (state.last_compile_result) {
                const res = state.last_compile_result;
                return `
                  <div class="exit-pocket black-pocket">
                    <div class="pocket-color-tag" title="Phase 2: Compiler Drop &amp; Corruption">PHASE 2: BLACK</div>
                    <div class="pocket-val">+${(res.exited_cubes || {}).black || 0}</div>
                    <div class="pocket-sub">Corruption</div>
                  </div>
                  <div class="exit-pocket red-pocket">
                    <div class="pocket-color-tag" title="Phase 4: Attack Resolution">PHASE 4: RED</div>
                    <div class="pocket-val">${(res.exited_cubes || {}).red || 0}</div>
                    <div class="pocket-sub">${state.is_market_share ? 'Market Manipulation' : 'Ransomware'}</div>
                  </div>
                  <div class="exit-pocket blue-pocket">
                    <div class="pocket-color-tag" title="Phase 4: Attack Resolution">PHASE 4: BLUE</div>
                    <div class="pocket-val">${(res.exited_cubes || {}).blue || 0}</div>
                    <div class="pocket-sub">Spyware</div>
                  </div>
                  <div class="exit-pocket green-pocket">
                    <div class="pocket-color-tag" title="Phase 4: Attack Resolution">PHASE 4: GREEN</div>
                    <div class="pocket-val">${(res.exited_cubes || {}).green || 0}</div>
                    <div class="pocket-sub">Malware</div>
                  </div>
                `;
              }
              return `
                <div class="exit-pocket black-pocket"><div class="pocket-color-tag" title="Phase 2: Compiler Drop &amp; Corruption">PHASE 2: BLACK</div><div class="pocket-val">0</div><div class="pocket-sub">Corruption</div></div>
                <div class="exit-pocket red-pocket"><div class="pocket-color-tag" title="Phase 4: Attack Resolution">PHASE 4: RED</div><div class="pocket-val">0</div><div class="pocket-sub">${state.is_market_share ? 'Market Manipulation' : 'Ransomware'}</div></div>
                <div class="exit-pocket blue-pocket"><div class="pocket-color-tag" title="Phase 4: Attack Resolution">PHASE 4: BLUE</div><div class="pocket-val">0</div><div class="pocket-sub">Spyware</div></div>
                <div class="exit-pocket green-pocket"><div class="pocket-color-tag" title="Phase 4: Attack Resolution">PHASE 4: GREEN</div><div class="pocket-val">0</div><div class="pocket-sub">Malware</div></div>
              `;
            })()}
          </div>
        </div>

        <!-- Agent Cube Effects Breakdown Stack -->
        <div class="cube-threat-effects-list">
          <div class="cube-threat-row black-row">
            <span class="threat-pill black">■ BLACK // CORRUPTION</span>
            <div class="threat-row-text">
              <strong>Phase 2: Compiler Drop &amp; Corruption:</strong> Advance Corruption Track 1 space per exited Black. Fills at capacity: queue Version upgrade for next round. <strong>v3.0 fill = SINGULARITY!</strong>
              ${state.is_market_share ? marketShareComparisonNote() : ""}
            </div>
          </div>
          <div class="cube-threat-row red-row">
            ${state.is_market_share ? `
            <span class="threat-pill red">◆ RED // MARKET MANIPULATION</span>
            <div class="threat-row-text">
              <strong>Blocks: Red / Any Shield.</strong> Lose 1 Market Share per unblocked Red (never below 0). <em>Market Collapse: any surviving player at 0 Market Share after Phase 4 makes this the Final Round.</em>
            </div>` : `
            <span class="threat-pill red">◆ RED // RANSOMWARE</span>
            <div class="threat-row-text">
              <strong>Blocks: Red / Any Shield.</strong> Lose $1 per unblocked Red. <em>Flat Leak Penalty: if any unpaid ransom remains (shortfall &gt; $0), lose a flat 1 Corporate Secret!</em>
            </div>`}
          </div>
          <div class="cube-threat-row blue-row">
            <span class="threat-pill blue">● BLUE // SPYWARE</span>
            <div class="threat-row-text">
              <strong>Blocks: Blue / Any Shield.</strong> Lose 1 Corporate Secret per unblocked Blue. <strong>Reaching ≤ 0 Secrets triggers Total Data Breach (Patient Zero)!</strong>
            </div>
          </div>
          <div class="cube-threat-row green-row">
            <span class="threat-pill green">▲ GREEN // MALWARE</span>
            <div class="threat-row-text">
              <strong>Blocks: Green / Any Shield.</strong> Move 1 active die from In Production → Glitched Box per unblocked Green (or sacrifice White Contractor). <em>Empty In Production = 0 effect!</em>
            </div>
          </div>
        </div>

        <div class="wear-recycle-summary-box">
          <strong>SHIELD PERSISTENCE:</strong> Permanent Shields blocking attacks remain in In Production (unless glitched by unblocked Green Malware). Contractors return to supply.<br>
          <strong>RECYCLE:</strong> Exited Red, Blue, and Green cubes recycle back into the Staging Cup.
        </div>
      </div>

      <!-- ========================================================= -->
      <!-- COLUMN 3 (Right): Game Sequence Reference & Victory       -->
      <!-- ========================================================= -->
      <div class="agent-board-col sequence-col">
        <div class="col-title-bar">
          <span class="col-title">GAME SEQUENCE OVERVIEW</span>
        </div>

        <div class="sequence-cards-stack">
          <!-- Phase 1 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 1: ROLL & DEPLOY (Simultaneous)</div>
            <div class="seq-card-body">
              <strong>0. Version Transition:</strong> Apply queued Version upgrade at start of round.<br>
              <strong>1. Pulse:</strong> Add +1 Black → Staging Cup.<br>
              <strong>2. Staffing:</strong> Hire White Contractors ($1 / $2 / $3, max 3).<br>
              <strong>3. Roll & Rerolls:</strong> Roll Ready for Release + Contractors. Up to 2 free rerolls of unlocked dice (⚠️ Glitches lock immediately).<br>
              <strong>4. Triage & Deploy:</strong> Glitched dice → Glitched Box. Deploy Shields (up to Defense Capacity) & Income dice to In Production.
            </div>
          </div>

          <!-- Phase 2 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 2: COMPILER DROP & CORRUPTION (Simultaneous)</div>
            <div class="seq-card-body">
              <strong>Drop</strong> entire Staging Cup into Cube Tower.<br>
              Resolve Black cubes on the Corruption Track (Version Advance, Spillover, Singularity).<br>
              <strong>Compile Buffer Overflow:</strong> If 0 cubes exit, inject +1 R, +1 B, +1 G into the cup (no attacks this round).<br>
              <strong>End Check:</strong> Singularity ends the game; any player ≤ 0 Secrets → Final Round.
            </div>
          </div>

          <!-- Phase 3 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 3: INCOME (Simultaneous)</div>
            <div class="seq-card-body">
              Collect $, 🔬, &amp; ★ from every die still In Production (Income + Shield slots, incl. White Contractors). Signature Protocols (Burn Notice, Jumper Diagnostics) resolve here.
            </div>
          </div>

          <!-- Phase 4 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 4: ATTACK RESOLUTION (Simultaneous)</div>
            <div class="seq-card-body">
              Two-Stage Defensive Blocking → Red / Blue / Green damage → Defense L4 payout.<br>
              <strong>Snowball Recycle</strong> exited R/B/G → Staging Cup; <strong>Contractor Expiration</strong>; End Check.
            </div>
          </div>

          <!-- Phase 5 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 5: CI/CD PIPELINE SHIFT (Simultaneous)</div>
            <div class="seq-card-body">
              1. <strong>Magnetic Splice:</strong> Glitched → Ready (Omnidyne).<br>
              2. <strong>Production Return:</strong> In Production → Scanned Box.<br>
              3. <strong>Scanned Graduation:</strong> Scanned → Ready (≤ Release Bandwidth, your choice).<br>
              4. <strong>Conveyor Triage:</strong> Glitched → Scanned (≤ Triage Bandwidth).
            </div>
          </div>

          <!-- Phase 6 -->
          <div class="seq-card">
            <div class="seq-card-header">PHASE 6: OPERATIONS (Clockwise)</div>
            <div class="seq-card-body">
              Buy Dice (max 2, straight to Ready for Release), Upgrade Tracks (🔬), ${state.is_share_regain ? 'regain Market Share on the Public Relations Track (🔬)' : 'File Patents (🔬)'}, paid ★ actions; then pass the First Player Marker.
            </div>
          </div>

          <!-- Scoring -->
          <div class="seq-card portfolio-scoring-card">
            <div class="seq-card-header">SECRETS VICTORY &amp; TIEBREAKERS</div>
            <div class="seq-card-body">
              <strong>Surviving White Hat Operatives Only</strong> (Patient Zero eliminated):<br>
              ${state.is_market_leader_bonus ? `<strong>Market Leader Bonus:</strong> survivors gain Corporate Secrets by final <strong>Market Share</strong> place (${(state.market_leader_bonus_schedule || []).map((b, i) => `${i + 1}${["st", "nd", "rd"][i] || "th"} +${b}`).filter((t) => !t.endsWith("+0")).join(", ")}; ties share the better place).<br>` : ""}
              <strong>Primary Victory Goal:</strong> Most <strong>Corporate Secrets</strong>${state.is_market_leader_bonus ? " (held + Market Leader Bonus)" : " held"}.<br>
              ${state.is_market_share ? `<strong>Tiebreaker 1:</strong> Highest <strong>Market Share</strong>.<br>
              <strong>Tiebreaker 2:</strong> Most remaining <strong>Money ($)</strong>.<br>
              <strong>Tiebreaker 3:</strong> Most <strong>Active Colored Module Dice</strong> in Ready for Release.<br>
              <strong>Tiebreaker 4:</strong> Most remaining <strong>Research Tokens (🔬)</strong>.<br>
              <strong>Tiebreaker 5:</strong> Fewest dice <strong>Under Development</strong>.<br>` : `<strong>Tiebreaker 1:</strong> Most remaining <strong>Money ($)</strong>.<br>
              <strong>Tiebreaker 2:</strong> Most owned <strong>Colored Dice</strong> (all zones).<br>
              <strong>Tiebreaker 3:</strong> Most remaining <strong>Research Tokens (🔬)</strong>.<br>`}
              <em>(Total Wipeout: ranked by the same tiebreakers${state.is_market_leader_bonus ? "; no Market Leader Bonus" : ""}).</em>
            </div>
          </div>
        </div>
      </div>

    </div>
  `;
}

// v0.36.0: Market Share comparison when a Version's final space is covered (bank payout; v2.0 only by default)
function marketShareComparisonNote() {
  const pay = Object.entries(state.version_share_payout || {}).map(([v, n]) => `${v} fill: $${n}`).join(", ");
  const last = (state.version_comparisons || []).slice(-1)[0];
  const nameOf = (pid) => ((state.players || [])[pid] || {}).name || `Player ${pid + 1}`;
  let res = "";
  if (last) {
    if (last.all_tied) {
      res = `<br><em>${last.version} comparison: tied, no Money moved.</em>`;
    } else {
      const top = last.top_pids.map((p) => `${nameOf(p)} +$${last.gains[p]}`).join(", ");
      const bottom = last.bottom_pids.map((p) => `${nameOf(p)} -$${last.paid[p]}${last.forgiven[p] ? ` ($${last.forgiven[p]} forgiven)` : ""}`).join(", ");
      res = `<br><em>${last.version} comparison: highest ${top}; lowest ${bottom}.</em>`;
    }
  }
  const rule = pay ? `<br><strong>Market Share comparison</strong> (${pay}): highest Market Share gains the payout from the bank; lowest pays what it can.` : "";
  return rule + res;
}
