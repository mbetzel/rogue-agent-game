/**
 * Rogue Agent — Action Dock Component
 */

import {
  state,
  selectedCommitments,
  selectedBacklashIndex,
  setSelectedBacklashIndex,
  patchCashSelected,
  setPatchCashSelected,
  cipherDiscountSelected,
  setCipherDiscountSelected,
  selectedRerollIndices,
  clearSelectedRerolls,
  selectedChoiceDeclarations,
} from "../state.js";
import {
  doHireContractors,
  doRoll,
  doReroll,
  doCommit,
  doCompile,
  doAcoustic,
  doSpook,
  doDirtyIncome,
  doPhreaker,
  doStarAction,
  doEndTurn,
} from "../api.js";
import { openModal } from "./modals.js";
import { renderMarket } from "./market.js";

export function renderActionDock() {
  if (!state) return;

  const caps = state.action_capabilities || {};
  const controls = document.getElementById("dockControls");
  if (!controls) return;
  controls.innerHTML = "";

  const human = (state.players && state.players.find((p) => p.is_human)) || (state.players && state.players[0]);
  if (!human) return;

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
          clearSelectedRerolls();
          doRoll();
        };
        controls.appendChild(btn);
      }
    }

    if (caps.can_commit || caps.can_reroll || caps.can_debug_unlock) {
      const unresolvedGlitches = (human.rolled_pool || []).filter(
        (d) => d && d.current_face && d.current_face.is_glitch
      ).length;
      if (unresolvedGlitches > 0) {
        const glitchWarn = document.createElement("div");
        glitchWarn.className = "glitch-warning";
        glitchWarn.innerHTML = `<span>⚠️ ${unresolvedGlitches} Unresolved Hardware Glitch${unresolvedGlitches > 1 ? "es" : ""}: Committing triggers Backlash (sacrifices Contractor or demotes Ready die to Unpatched).</span>`;
        controls.appendChild(glitchWarn);
      }

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
      const rolled = human.rolled_pool || [];
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
        clearSelectedRerolls();
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
          setSelectedBacklashIndex(parseInt(e.target.value, 10));
        };

        const dirtyBtn = document.createElement("button");
        dirtyBtn.className = "action-btn";
        dirtyBtn.style.borderColor = "var(--color-black-glow)";
        dirtyBtn.style.color = "#ff3377";
        dirtyBtn.innerText = "Dirty Income (+$3, -1 Secret)";
        dirtyBtn.onclick = () => {
          setSelectedBacklashIndex(parseInt(backlashSelect.value, 10));
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
        setCipherDiscountSelected(e.target.checked);
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
      setPatchCashSelected(e.target.checked);
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
