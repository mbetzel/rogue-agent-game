/**
 * Rogue Agent — Central Threat & Compiler (Cube Tower) Component
 */

import { state } from "../state.js";

export function renderCompiler() {
  if (!state) return;

  // Staging Cup
  const stagingEl = document.getElementById("stagingCupTray");
  if (stagingEl && state.staging_cup) {
    stagingEl.innerHTML = `
      <span class="cube-badge red">${state.staging_cup.red} Red</span>
      <span class="cube-badge blue">${state.staging_cup.blue} Blue</span>
      <span class="cube-badge green">${state.staging_cup.green} Green</span>
      <span class="cube-badge black">${state.staging_cup.black} Black</span>
    `;
  }

  // Tower Stuck
  const stuckEl = document.getElementById("towerStuckTray");
  if (stuckEl && state.tower_stuck_cubes) {
    stuckEl.innerHTML = `
      <span class="cube-badge red">${state.tower_stuck_cubes.red}</span>
      <span class="cube-badge blue">${state.tower_stuck_cubes.blue}</span>
      <span class="cube-badge green">${state.tower_stuck_cubes.green}</span>
      <span class="cube-badge black">${state.tower_stuck_cubes.black}</span>
      <span style="font-size: 0.8rem; color: var(--text-dim); margin-left: 6px;">(${state.tower_total_stuck} total stuck)</span>
    `;
  }

  // Last Compile Drop Results
  const resEl = document.getElementById("lastCompileResult");
  if (resEl) {
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
}
