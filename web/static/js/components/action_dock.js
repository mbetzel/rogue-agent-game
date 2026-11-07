/**
 * Rogue Agent — Action Dock Component
 */

import {
  state,
  selectedCommitments,
  selectedBacklashIndex,
  setSelectedBacklashIndex,
  selectedBacklashDieId,
  setSelectedBacklashDieId,
  selectedPhreakerDieId,
  setSelectedPhreakerDieId,
  getEligibleBacklashDice,
  patchCashSelected,
  setPatchCashSelected,
  cipherDiscountSelected,
  setCipherDiscountSelected,
  selectedRerollIndices,
  clearSelectedRerolls,
  selectedChoiceDeclarations,
  selectedGlitchDieIds,
  toggleSelectedGlitchDieId,
  clearSelectedGlitchDieIds,
  selectedAnyAllocations,
  setSelectedAnyAllocation,
  initSelectedAnyAllocations,
  clearSelectedAnyAllocations,
  selectedGraduateIds,
  initSelectedGraduateIds,
  toggleSelectedGraduateId,
} from "../state.js";
import {
  doResolveBreakthrough,
  doHireContractors,
  doRoll,
  doReroll,
  doCommit,
  doCompile,
  doConfirmIncome,
  doConfirmAttacks,
  doChooseGraduates,
  doAcoustic,
  doSpook,
  doDirtyIncome,
  doPhreaker,
  doFastPatch,
  doStarAction,
  doEndTurn,
  doUpgradeTrack,
  doFilePatent,
  doRegainMarketShare,
} from "../api.js";
import { openModal } from "./modals.js";
import { renderMarket } from "./market.js";
import { renderPlayerMats } from "./player_mats.js";

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
          opBtn.innerText = "⚡ Meridian: Overtime Sprint (2 Free Contractors)";
          opBtn.onclick = () => doHireContractors(2, true);
          hireWrap.appendChild(opBtn);
        }

        controls.appendChild(hireWrap);
      }

      if (caps.can_roll) {
        const btn = document.createElement("button");
        btn.className = "action-btn btn-accent";
        const poolSize = human.ready_dice.length + (human.contractor_dice ? human.contractor_dice.length : 0);
        btn.innerText = `Roll Ready Pool (${poolSize} dice)`;
        btn.onclick = () => {
          clearSelectedRerolls();
          doRoll();
        };
        controls.appendChild(btn);
      }
    }

    if (caps.can_commit || caps.can_reroll) {
      const unresolvedGlitches = (human.rolled_pool || []).filter(
        (d) => d && d.current_face && d.current_face.is_glitch
      ).length;
      if (unresolvedGlitches > 0) {
        const glitchWarn = document.createElement("div");
        glitchWarn.className = "glitch-warning";
        glitchWarn.innerHTML = `<span>⚠️ ${unresolvedGlitches} Unresolved Hardware Glitch${unresolvedGlitches > 1 ? "es" : ""}: Committing routes glitched dice to the Glitched Box (White Contractors are discarded to supply).</span>`;
        controls.appendChild(glitchWarn);
      }

      const rerollsLeft = human.rerolls_remaining !== undefined ? human.rerolls_remaining : 0;
      const maxRerolls = human.max_rerolls !== undefined ? human.max_rerolls : 2;

      const rerollInfo = document.createElement("span");
      rerollInfo.style.fontSize = "0.8rem";
      rerollInfo.style.color = "#38bdf8";
      rerollInfo.style.fontWeight = "600";
      rerollInfo.innerText = `Rerolls: ${rerollsLeft}/${maxRerolls} left | Click unlocked dice to reroll | Glitches lock immediately`;
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
            // Blue Face 4: Block 1 Blue vs +1 🔬
            const optShield = document.createElement("option");
            optShield.value = "shield";
            optShield.innerText = "Commit Block 1 Blue";
            const optPatch = document.createElement("option");
            optPatch.value = "patch";
            optPatch.innerText = "Gain +1 🔬 (Research)";
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
            selectedCommitments[idx] = "any";
            const colStr = d.color === "white" ? "#f8fafc" : `var(--color-${d.color})`;
            wrap.innerHTML = `<span style="color: ${colStr};">Die #${idx + 1} (${d.color}):</span> <span style="background: rgba(56, 189, 248, 0.15); border: 1px solid #38bdf8; color: #38bdf8; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">🛡️ FLEXIBLE ANY SHIELD</span>`;
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
          opt.innerText = `Ignore 1 ${c.toUpperCase()} (${exited[c]} exited)`;
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

    if (caps.can_spook) {
      const spookWrap = document.createElement("div");
      spookWrap.style.display = "inline-flex";
      spookWrap.style.alignItems = "center";
      spookWrap.style.gap = "6px";

      const spookInput = document.createElement("input");
      spookInput.type = "number";
      spookInput.min = "0";
      spookInput.max = String(human.money || 0);
      spookInput.value = "0";
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
      spookBtn.innerText = "⚡ Spook: Slush Fund (2 Free + $1/extra)";
      spookBtn.onclick = () => {
        const amt = parseInt(spookInput.value, 10);
        doSpook(isNaN(amt) ? 0 : Math.max(0, amt));
      };

      spookWrap.appendChild(document.createTextNode("Extra $:"));
      spookWrap.appendChild(spookInput);
      spookWrap.appendChild(spookBtn);
      controls.appendChild(spookWrap);
    }
  } else if (state.phase === 3) {
    renderIncomePanel(controls, human, caps);
  } else if (state.phase === 5) {
    renderGraduationPanel(controls, human, caps);
  } else if (state.phase === 4 || state.phase === 6) {
    if (state.phase === 4) {
      const compileRes = state.last_compile_result || {};
      const attackRes = state.last_attack_result || {};
      const exited = compileRes.exited_cubes || {};
      const incomeMap = state.last_income_result || {};
      const rawIncome = incomeMap[human.player_id] || incomeMap[String(human.player_id)] || { money: 0, patches: 0, secrets: 0, details: [] };
      const threatMap = attackRes.threat_summary || {};
      const humanThreat = threatMap[human.player_id] || threatMap[String(human.player_id)] || attackRes.human_threat || {};
      if (!caps.can_confirm_attacks) {
        const waitMsg = document.createElement("span");
        waitMsg.style.fontSize = "0.8rem";
        waitMsg.style.color = "var(--text-dim)";
        waitMsg.innerText = "Phase 4: Attack Resolution — waiting for other corporations to confirm defenses.";
        controls.appendChild(waitMsg);
        return;
      }

      const redInfo = humanThreat.red || { cubes: exited.red || 0, shields: 0, unblocked: exited.red || 0 };
      const blueInfo = humanThreat.blue || { cubes: exited.blue || 0, shields: 0, unblocked: exited.blue || 0 };
      const greenInfo = humanThreat.green || { cubes: exited.green || 0, shields: 0, unblocked: exited.green || 0 };
      const blackCubes = exited.black || 0;

      const anyShieldCount = (humanThreat.any && humanThreat.any.shields) || 0;
      const anyDice = (humanThreat.any && humanThreat.any.dice) || [];

      // Build expanded list of individual Any-shield units (1 per shield point)
      const anyShieldUnits = [];
      if (anyDice.length > 0) {
        anyDice.forEach((d, dIdx) => {
          const amt = d.block_amount || 1;
          for (let k = 0; k < amt; k++) {
            anyShieldUnits.push({
              unit_idx: anyShieldUnits.length,
              die_id: d.die_id,
              color: d.color || "gray",
              face_name: d.face_name || "Block 1 Any",
              label: amt > 1 ? `${(d.color || "gray").toUpperCase()} Die (${k + 1}/${amt})` : `${(d.color || "gray").toUpperCase()} Die`,
            });
          }
        });
      }
      while (anyShieldUnits.length < anyShieldCount) {
        anyShieldUnits.push({
          unit_idx: anyShieldUnits.length,
          die_id: null,
          color: "gray",
          face_name: "Block 1 Any",
          label: `Flexible Shield #${anyShieldUnits.length + 1}`,
        });
      }

      // Initialize selectedAnyAllocations from server default if not yet initialized
      if (anyShieldCount > 0 && selectedAnyAllocations.length !== anyShieldCount) {
        const defaultAllocObj = (humanThreat.any && humanThreat.any.allocated) || { red: 0, blue: 0, green: 0 };
        const initialList = [];
        for (let i = 0; i < (defaultAllocObj.blue || 0); i++) initialList.push("blue");
        for (let i = 0; i < (defaultAllocObj.red || 0); i++) initialList.push("red");
        for (let i = 0; i < (defaultAllocObj.green || 0); i++) initialList.push("green");
        const fallbackColor = (exited.blue > 0) ? "blue" : (exited.green > 0 ? "green" : (exited.red > 0 ? "red" : "blue"));
        while (initialList.length < anyShieldCount) {
          initialList.push(fallbackColor);
        }
        initSelectedAnyAllocations(initialList.slice(0, anyShieldCount));
      }

      // Tally current user-selected Any shield allocations
      const userAnyAlloc = { red: 0, blue: 0, green: 0 };
      if (anyShieldCount > 0) {
        selectedAnyAllocations.forEach((col) => {
          if (col === "red" || col === "blue" || col === "green") {
            userAnyAlloc[col] += 1;
          }
        });
      }

      // Compute live blocked / unblocked counts based on userAnyAlloc
      const effAtk = humanThreat.effective_attacks || {
        red: redInfo.attack !== undefined ? redInfo.attack : (exited.red || 0),
        blue: blueInfo.attack !== undefined ? blueInfo.attack : (exited.blue || 0),
        green: greenInfo.attack !== undefined ? greenInfo.attack : (exited.green || 0),
      };

      const fixedRedShields = redInfo.shields || 0;
      const fixedBlueShields = blueInfo.shields || 0;
      const fixedGreenShields = greenInfo.shields || 0;

      const remRedStage1 = Math.max(0, (effAtk.red || 0) - fixedRedShields);
      const remBlueStage1 = Math.max(0, (effAtk.blue || 0) - fixedBlueShields);
      const remGreenStage1 = Math.max(0, (effAtk.green || 0) - fixedGreenShields);

      // v0.36.0 free choice: every available Any shield must block while unblocked cubes remain; the player
      // chooses only the split. Mirror the engine's legalisation (clamp, trim Blue > Red > Green, back-fill).
      if (anyShieldCount > 0 && humanThreat.any_shield_policy === "FREE_CHOICE") {
        const rem = { red: remRedStage1, blue: remBlueStage1, green: remGreenStage1 };
        let budget = anyShieldCount;
        ["blue", "red", "green"].forEach((c) => {
          userAnyAlloc[c] = Math.min(Math.max(0, userAnyAlloc[c]), rem[c], budget);
          budget -= userAnyAlloc[c];
        });
        let short = Math.min(anyShieldCount, rem.red + rem.blue + rem.green) - (userAnyAlloc.red + userAnyAlloc.blue + userAnyAlloc.green);
        ["blue", "red", "green"].forEach((c) => {
          const add = Math.min(short, rem[c] - userAnyAlloc[c]);
          if (add > 0) { userAnyAlloc[c] += add; short -= add; }
        });
      }

      const liveUnblockedRed = anyShieldCount > 0
        ? Math.max(0, remRedStage1 - userAnyAlloc.red)
        : (redInfo.unblocked || 0);
      const liveUnblockedBlue = anyShieldCount > 0
        ? Math.max(0, remBlueStage1 - userAnyAlloc.blue)
        : (blueInfo.unblocked || 0);
      const liveUnblockedGreen = anyShieldCount > 0
        ? Math.max(0, remGreenStage1 - userAnyAlloc.green)
        : (greenInfo.unblocked || 0);

      const liveBlockedRed = (effAtk.red || 0) - liveUnblockedRed;
      const liveBlockedBlue = (effAtk.blue || 0) - liveUnblockedBlue;
      const liveBlockedGreen = (effAtk.green || 0) - liveUnblockedGreen;

      // Post-income cash (Phase 3 already paid) + star bonuses to determine live flat leak
      const preMoney = humanThreat.money !== undefined ? humanThreat.money : (human.money || 0);
      const r2Bonus = (humanThreat.r2_count || 0) > 0 && liveUnblockedRed === 0 ? 2 * humanThreat.r2_count : 0;
      const r3Bonus = (humanThreat.r3_count || 0) > 0 && (exited.red || 0) >= 3 ? 1 * humanThreat.r3_count : 0;
      const b1Bonus = (humanThreat.b1_count || 0) > 0 && (exited.blue || 0) >= 1 && liveUnblockedBlue === 0 ? 2 * humanThreat.b1_count : 0;
      const availableCashForRansom = preMoney + r2Bonus + r3Bonus + b1Bonus;
      const liveFlatLeak = anyShieldCount > 0
        ? (liveUnblockedRed > availableCashForRansom)
        : Boolean(redInfo.flat_leak);

      const unblockedGreen = liveUnblockedGreen;
      let candidates = attackRes.candidate_glitch_dice || (greenInfo.candidate_dice) || [];
      if (!candidates || candidates.length === 0) {
        const fallbackCandidates = [];
        (human.contractor_dice || []).forEach((d) => {
          fallbackCandidates.push({
            die_id: d.die_id,
            color: "white",
            face_name: (d.current_face && d.current_face.name) || "Contractor",
            role: "Contractor",
            money: 0,
            patches: 0,
            secrets: 0,
            is_contractor: true,
            is_shield: false,
            is_income: false,
          });
        });
        (human.in_production_dice || []).forEach((d) => {
          const eff = d.effective_face || d.current_face;
          const role = d.production_role || "income";
          const isShield = String(role).toLowerCase().includes("shield");
          fallbackCandidates.push({
            die_id: d.die_id,
            color: d.color,
            face_name: (eff && eff.name) || "Module",
            role: isShield ? String(role).replace(/_/g, " ").toUpperCase() : "Income",
            money: (eff && !isShield) ? (eff.money || 0) : 0,
            patches: (eff && !isShield) ? (eff.patches || 0) : 0,
            secrets: (eff && !isShield) ? (eff.secrets || 0) : 0,
            is_contractor: d.color === "white",
            is_shield: isShield,
            is_income: !isShield,
          });
        });
        candidates = fallbackCandidates;
      }

      const actualRequired = Math.min(unblockedGreen, candidates.length);

      // Clean up stale or excess selections
      const validCandidateIds = new Set(candidates.map((c) => c.die_id));
      for (const id of Array.from(selectedGlitchDieIds)) {
        if (!validCandidateIds.has(id)) {
          selectedGlitchDieIds.delete(id);
        }
      }
      while (selectedGlitchDieIds.size > actualRequired) {
        const lastId = Array.from(selectedGlitchDieIds).pop();
        selectedGlitchDieIds.delete(lastId);
      }

      // If only 1 candidate die exists and 1 is required, auto-select it for convenience
      if (actualRequired === 1 && candidates.length === 1 && selectedGlitchDieIds.size === 0) {
        selectedGlitchDieIds.add(candidates[0].die_id);
      }

      // Phase 3 income was already collected; a glitch now only costs future tempo
      const effectiveDetails = (rawIncome.details || []).map((det) => ({
        ...det,
        is_glitched: selectedGlitchDieIds.has(det.die_id),
      }));
      const effectiveMoney = rawIncome.money || 0;
      const effectiveResearch = rawIncome.research || 0;
      const effectiveSecrets = rawIncome.secrets || 0;

      const hasEnoughSelections = (actualRequired === 0) || (selectedGlitchDieIds.size === actualRequired);

      let btnText = "✓ Confirm Defenses & Resolve Attacks";
      if (actualRequired > 0) {
        if (!hasEnoughSelections) {
          const needed = actualRequired - selectedGlitchDieIds.size;
          btnText = `Select ${needed} Die to Glitch (${selectedGlitchDieIds.size}/${actualRequired})`;
        } else {
          btnText = `✓ Confirm & Move ${actualRequired} Selected Die${actualRequired > 1 ? 's' : ''} to Glitched Box`;
        }
      }

      const panel = document.createElement("div");
      panel.className = "confirm-income-panel";

      // Build Interactive Any Shield Assignment section if player has Block 1 Any dice
      let anyShieldSelectorHtml = "";
      if (anyShieldCount > 0) {
        anyShieldSelectorHtml = `
          <div class="confirm-any-shield-panel" style="background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.45); border-radius: 6px; padding: 10px 12px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 6px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="background: rgba(168, 85, 247, 0.25); color: #d8b4fe; border: 1px solid #a855f7; font-size: 0.7rem; font-weight: 800; padding: 2px 6px; border-radius: 4px;">🛡️ ANY SHIELD ASSIGNMENT</span>
                <span style="font-size: 0.8rem; font-weight: 700; color: #f3e8ff;">CHOOSE TARGET THREAT COLOR FOR ${anyShieldCount} FLEXIBLE SHIELD${anyShieldCount > 1 ? 'S' : ''}</span>
              </div>
              <span style="font-size: 0.72rem; color: #cbd5e1;">
                Unblocked before Any: <strong>${remRedStage1}R</strong> · <strong>${remBlueStage1}B</strong> · <strong>${remGreenStage1}G</strong>
              </span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              ${anyShieldUnits.map((unit, uIdx) => {
                const curCol = selectedAnyAllocations[uIdx] || "blue";
                const btnStyle = (col, hex, bgRgba) => {
                  const active = curCol === col;
                  return `padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; cursor: pointer; border: 1px solid ${active ? hex : 'rgba(255,255,255,0.18)'}; background: ${active ? bgRgba : 'rgba(15, 23, 42, 0.7)'}; color: ${active ? '#fff' : '#94a3b8'}; box-shadow: ${active ? '0 0 8px ' + bgRgba : 'none'};`;
                };
                return `
                  <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.55); padding: 6px 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.08); flex-wrap: wrap; gap: 8px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #e2e8f0;">
                      🎲 ${unit.label}: <span style="color: #c084fc;">${unit.face_name}</span>
                    </span>
                    <div style="display: inline-flex; gap: 6px; align-items: center;">
                      <button type="button" class="any-alloc-btn" data-unit-idx="${uIdx}" data-target-color="red" style="${btnStyle('red', '#f43f5e', 'rgba(244, 63, 94, 0.35)')}">
                        ◆ Block Red (${remRedStage1} atk)
                      </button>
                      <button type="button" class="any-alloc-btn" data-unit-idx="${uIdx}" data-target-color="blue" style="${btnStyle('blue', '#38bdf8', 'rgba(56, 189, 248, 0.35)')}">
                        ● Block Blue (${remBlueStage1} atk)
                      </button>
                      <button type="button" class="any-alloc-btn" data-unit-idx="${uIdx}" data-target-color="green" style="${btnStyle('green', '#4ade80', 'rgba(74, 222, 128, 0.35)')}">
                        ▲ Block Green (${remGreenStage1} atk)
                      </button>
                    </div>
                  </div>
                `;
              }).join("")}
            </div>
          </div>
        `;
      }

      let malwareHtml = "";
      if (actualRequired > 0) {
        malwareHtml = `
          <div class="confirm-malware-panel">
            <div class="confirm-malware-hdr">
              <div class="confirm-malware-title-row">
                <span class="confirm-malware-badge">⚠️ MALWARE BREACH</span>
                <span class="confirm-malware-title">LOGIC BOMB INFECTION (${unblockedGreen} Unblocked Green Cube${unblockedGreen > 1 ? 's' : ''})</span>
              </div>
              <span class="confirm-malware-sub">
                You took unblocked malware damage! Click below to select <strong>${actualRequired}</strong> active module${actualRequired > 1 ? 's' : ''} to move to the <strong>Glitched Box</strong> (or sacrifice a White Contractor). This round's income was already collected in Phase 3, so a glitch only delays that die.
              </span>
            </div>
            <div class="confirm-malware-grid">
              ${candidates.map((c) => {
                const isSel = selectedGlitchDieIds.has(c.die_id);
                const roleClass = (c.role || "").toLowerCase().replace(/[^a-z0-9]/g, "-");
                let consequenceText = "";
                if (c.is_contractor) {
                  consequenceText = "Contractor Sacrifice: Discard to supply (saves permanent modules)";
                } else if (c.is_shield) {
                  consequenceText = "Defensive Shield Sacrifice: moves to Glitched Box (its block still counts)";
                } else {
                  consequenceText = "Moves to Glitched Box (income already collected in Phase 3)";
                }
                return `
                  <div class="malware-die-card ${c.color} ${isSel ? 'selected' : ''}" data-die-id="${c.die_id}">
                    <div class="malware-die-top">
                      <span class="malware-die-role ${roleClass}">${c.role.toUpperCase()}</span>
                      <span style="font-weight: 700; font-size: 0.72rem; color: #fff;">${c.color.toUpperCase()} DIE</span>
                    </div>
                    <div class="malware-die-face">${c.face_name}${c.star_note ? ' (' + c.star_note + ')' : ''}</div>
                    <div class="malware-die-consequence">${consequenceText}</div>
                    <div class="malware-die-status">
                      ${isSel ? '⚠️ SELECTED FOR GLITCH' : '○ Click to Glitch'}
                    </div>
                  </div>
                `;
              }).join("")}
            </div>
          </div>
        `;
      } else if (unblockedGreen > 0) {
        malwareHtml = `
          <div class="confirm-malware-panel" style="border-color: rgba(74, 222, 128, 0.4); background: rgba(74, 222, 128, 0.05);">
            <div class="confirm-malware-hdr">
              <div class="confirm-malware-title-row">
                <span class="confirm-malware-badge" style="background: rgba(74, 222, 128, 0.2); color: #4ade80;">🛡️ 0 MALWARE EFFECT</span>
                <span class="confirm-malware-title" style="color: #4ade80;">ZERO ACTIVE PRODUCTION EXPLOITS</span>
              </div>
              <span class="confirm-malware-sub" style="color: #86efac;">
                ${unblockedGreen} unblocked Green Malware cube${unblockedGreen > 1 ? 's' : ''} struck your corporate network, but your In Production zone is completely empty! Excess malware has 0 effect (no dice destroyed).
              </span>
            </div>
          </div>
        `;
      }

      panel.innerHTML = `
        <div class="confirm-income-header">
          <div class="confirm-income-title-wrap">
            <span class="confirm-badge">PHASE 4: ATTACK RESOLUTION</span>
            <span class="confirm-income-title">TWO-STAGE DEFENSIVE BLOCKING SUMMARY</span>
          </div>
          <span style="font-size: 0.72rem; color: var(--text-dim); font-family: monospace;">
            Round ${state.current_round} // Allocate Any shields and Green targets before damage resolves
          </span>
        </div>

        ${anyShieldSelectorHtml}

        <div class="confirm-income-grid">
          <!-- Card 1: Threat Resolution -->
          <div class="confirm-income-card">
            <div class="confirm-income-card-hdr">
              <span>CUBE TOWER OUTPUT & DEFENSES</span>
              <span style="color: var(--text-highlight);">${exited.red || 0}R · ${exited.blue || 0}B · ${exited.green || 0}G · ${exited.black || 0}K</span>
            </div>
            ${anyShieldCount > 0 ? `
              <div class="confirm-threat-row" style="background: rgba(168, 85, 247, 0.1); border-left: 3px solid #a855f7; padding-left: 6px;">
                <span style="color: #c084fc; font-weight: 700;">🛡️ ANY // FLEXIBLE</span>
                <span>${anyShieldCount} shield${anyShieldCount > 1 ? 's' : ''} -> Blocking <strong>${userAnyAlloc.red}R · ${userAnyAlloc.blue}B · ${userAnyAlloc.green}G</strong></span>
              </div>
            ` : ''}
            <div class="confirm-threat-row">
              <span style="color: var(--color-black); font-weight: 700;">■ BLACK // CORRUPTION</span>
              <span>${blackCubes} cube${blackCubes === 1 ? '' : 's'} -> Track space ${state.corruption_track || 0}</span>
            </div>
            <div class="confirm-threat-row">
              <span style="color: var(--color-red); font-weight: 700;">◆ RED // ${state.is_market_share ? 'MARKET MANIPULATION' : 'RANSOMWARE'}</span>
              <span>${redInfo.cubes} exited vs ${liveBlockedRed} blocked -> ${liveUnblockedRed > 0 && state.is_market_share ? `<strong style="color: #f43f5e;">-${Math.min(liveUnblockedRed, humanThreat.market_share || 0)} Market Share${(humanThreat.market_share || 0) - liveUnblockedRed <= 0 ? ' (MARKET COLLAPSE!)' : ''}</strong>` : liveUnblockedRed > 0 ? (liveFlatLeak ? `<strong style="color: #f43f5e;">-${liveUnblockedRed} Cash (Flat -1 Secret Leak!)</strong>` : `<strong style="color: #f43f5e;">-${liveUnblockedRed} Cash</strong>`) : '<strong style="color: #4ade80;">Fully Blocked</strong>'}</span>
            </div>
            <div class="confirm-threat-row">
              <span style="color: var(--color-blue); font-weight: 700;">● BLUE // SPYWARE</span>
              <span>${blueInfo.cubes} exited vs ${liveBlockedBlue} blocked -> ${liveUnblockedBlue > 0 ? `<strong style="color: #f43f5e;">-${liveUnblockedBlue} Secrets</strong>` : '<strong style="color: #4ade80;">Fully Blocked</strong>'}</span>
            </div>
            <div class="confirm-threat-row">
              <span style="color: var(--color-green); font-weight: 700;">▲ GREEN // MALWARE</span>
              <span>${greenInfo.cubes} exited vs ${liveBlockedGreen} blocked -> ${liveUnblockedGreen > 0 ? (actualRequired === 0 ? '<strong style="color: #4ade80;">0 effect (Empty Production)</strong>' : `<strong style="color: #f43f5e;">${liveUnblockedGreen} Unblocked Malware</strong>`) : '<strong style="color: #4ade80;">Fully Blocked</strong>'}</span>
            </div>
          </div>

          <!-- Card 2: Harvested Income -->
          <div class="confirm-income-card" style="border-color: rgba(234, 179, 8, 0.4);">
            <div class="confirm-income-card-hdr">
              <span style="color: #facc15;">PHASE 3 INCOME (COLLECTED)</span>
              <span>Banked before attacks</span>
            </div>
            <div class="confirm-pills-row">
              <span class="income-pill money">+$${effectiveMoney} Cash</span>
              <span class="income-pill research">+${effectiveResearch} 🔬 Research</span>
              ${effectiveSecrets > 0 ? `<span class="income-pill secrets">+${effectiveSecrets} Secrets</span>` : ''}
            </div>
            <div class="confirm-dice-chips">
              ${(effectiveDetails && effectiveDetails.length > 0)
                ? effectiveDetails.map((d) => `
                    <span class="confirm-die-chip ${d.color} ${d.is_glitched ? 'glitched-chip' : ''}">
                      <strong>${d.color.toUpperCase()}:</strong> ${d.face_name}${d.star_note ? ' (' + d.star_note + ')' : ''} ${d.is_glitched ? '<em>(GLITCHED)</em>' : ''}
                    </span>
                  `).join('')
                : '<span style="font-size: 0.75rem; color: var(--text-dim); font-style: italic;">No surviving production dice yielded income.</span>'}
            </div>
          </div>
        </div>

        ${malwareHtml}

        <div class="confirm-action-bar">
          <span style="font-size: 0.75rem; color: var(--text-dim);">
            Confirming resolves Red / Blue / Green damage. Glitched dice move to the <strong>Glitched Box</strong>; contractors expire at the end of Phase 4.
          </span>
          ${(humanThreat.aegis && humanThreat.aegis.available) ? `
            <select id="aegisEchoSelect" style="padding: 4px 8px;" title="Aegis Baffle Echo (Institutional Override, once per Version)">
              <option value="none">Aegis Baffle Echo: do not use</option>
              ${(humanThreat.aegis.qualifying_colors || []).map((c) => `<option value="${c}">Aegis Baffle Echo: ignore 1 ${c.toUpperCase()}</option>`).join("")}
            </select>` : ''}
          ${(humanThreat.slush_fund && humanThreat.slush_fund.available) ? `
            <label style="font-size: 0.75rem;" title="DTO Slush Fund (Institutional Override, once per game)">
              <input type="checkbox" id="slushFundCheck"> Use DTO Slush Fund (absorb up to 2 Secret loss; once per game)
            </label>` : ''}
          <button class="action-btn btn-confirm-income ${hasEnoughSelections ? '' : 'disabled'}" id="btnConfirmIncome" ${hasEnoughSelections ? '' : 'disabled'}>
            ${btnText}
          </button>
        </div>
      `;

      panel.querySelectorAll(".any-alloc-btn").forEach((btn) => {
        btn.onclick = () => {
          const uIdx = parseInt(btn.getAttribute("data-unit-idx"), 10);
          const chosenColor = btn.getAttribute("data-target-color");
          setSelectedAnyAllocation(uIdx, chosenColor);
          renderActionDock();
        };
      });

      panel.querySelectorAll(".malware-die-card").forEach((card) => {
        card.onclick = () => {
          const dId = parseInt(card.getAttribute("data-die-id"), 10);
          toggleSelectedGlitchDieId(dId, actualRequired);
          renderActionDock();
        };
      });

      const confirmBtn = panel.querySelector("#btnConfirmIncome");
      if (confirmBtn) {
        confirmBtn.onclick = () => {
          if (!hasEnoughSelections && actualRequired > 0) return;
          const toGlitch = Array.from(selectedGlitchDieIds);
          const allocPayload = anyShieldCount > 0 ? {
            red: userAnyAlloc.red,
            blue: userAnyAlloc.blue,
            green: userAnyAlloc.green,
          } : null;
          clearSelectedGlitchDieIds();
          clearSelectedAnyAllocations();
          const aegisSel = panel.querySelector("#aegisEchoSelect");
          const slushChk = panel.querySelector("#slushFundCheck");
          doConfirmAttacks(toGlitch, allocPayload, aegisSel ? aegisSel.value : null, slushChk ? slushChk.checked : null);
        };
      }

      controls.appendChild(panel);
      return;
    }

    // Dirty Income with Backlash die selector
    if (caps.can_dirty_income || caps.can_cipher_dirty) {
      const dirtyWrap = document.createElement("div");
      dirtyWrap.style.display = "inline-flex";
      dirtyWrap.style.alignItems = "center";
      dirtyWrap.style.gap = "6px";

      const eligibleBacklash = getEligibleBacklashDice(human);
      if (caps.can_dirty_income && eligibleBacklash.length > 0) {
        const backlashSelect = document.createElement("select");
        backlashSelect.id = "dirtyBacklashSelect";
        backlashSelect.style.padding = "4px 8px";
        backlashSelect.style.background = "var(--bg-card)";
        backlashSelect.style.color = "#fff";
        backlashSelect.style.border = "1px solid var(--border-color)";
        backlashSelect.style.borderRadius = "4px";

        eligibleBacklash.forEach((die) => {
          const opt = document.createElement("option");
          opt.value = String(die.die_id);
          opt.innerText = `Backlash: ${die.color.toUpperCase()}${die.vp ? ' (' + die.vp + 'VP)' : ''} [${die.zone_label}]`;
          backlashSelect.appendChild(opt);
        });

        const validTarget = eligibleBacklash.some((d) => d.die_id === selectedBacklashDieId)
          ? selectedBacklashDieId
          : eligibleBacklash[0].die_id;
        backlashSelect.value = String(validTarget);
        setSelectedBacklashDieId(validTarget);
        backlashSelect.onchange = (e) => {
          setSelectedBacklashDieId(parseInt(e.target.value, 10));
        };

        const dirtyBtn = document.createElement("button");
        dirtyBtn.className = "action-btn";
        dirtyBtn.style.borderColor = "var(--color-black-glow)";
        dirtyBtn.style.color = "#ff3377";
        dirtyBtn.innerText = "Dirty Income (+$3, -1 Secret)";
        dirtyBtn.onclick = () => {
          setSelectedBacklashDieId(parseInt(backlashSelect.value, 10));
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
        cipherDirtyBtn.innerText = "⚡ Cipher: Arbitrage Payout (+$2 Cash)";
        cipherDirtyBtn.onclick = () => doDirtyIncome(true);
        dirtyWrap.appendChild(cipherDirtyBtn);
      }

      controls.appendChild(dirtyWrap);
    }

    // Phreaker Ability: Free Repair with target selector
    if (caps.can_phreaker && (human.unpatched_dice || []).length > 0) {
      const phreakWrap = document.createElement("div");
      phreakWrap.style.display = "inline-flex";
      phreakWrap.style.alignItems = "center";
      phreakWrap.style.gap = "6px";

      const phreakSelect = document.createElement("select");
      phreakSelect.id = "phreakerDieSelect";
      phreakSelect.style.padding = "4px 8px";
      phreakSelect.style.background = "var(--bg-card)";
      phreakSelect.style.color = "#fff";
      phreakSelect.style.border = "1px solid var(--border-color)";
      phreakSelect.style.borderRadius = "4px";

      human.unpatched_dice.forEach((die, idx) => {
        const opt = document.createElement("option");
        opt.value = String(die.die_id);
        opt.innerText = `Repair: #${idx + 1} ${die.color.toUpperCase()}${die.vp ? ' (' + die.vp + 'VP)' : ''}`;
        phreakSelect.appendChild(opt);
      });

      const validPhreakTarget = human.unpatched_dice.some((d) => d.die_id === selectedPhreakerDieId)
        ? selectedPhreakerDieId
        : human.unpatched_dice[0].die_id;
      phreakSelect.value = String(validPhreakTarget);
      setSelectedPhreakerDieId(validPhreakTarget);
      phreakSelect.onchange = (e) => {
        setSelectedPhreakerDieId(parseInt(e.target.value, 10));
      };

      const phreakBtn = document.createElement("button");
      phreakBtn.className = "action-btn";
      phreakBtn.style.borderColor = "#4ade80";
      phreakBtn.style.color = "#4ade80";
      phreakBtn.innerText = "⚡ Omnidyne: Magnetic Splice (Glitched → Ready)";
      phreakBtn.onclick = () => {
        setSelectedPhreakerDieId(parseInt(phreakSelect.value, 10));
        doPhreaker(1);
      };

      phreakWrap.appendChild(phreakSelect);
      phreakWrap.appendChild(phreakBtn);
      controls.appendChild(phreakWrap);
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
          opt.innerText = `Ignore 1 ${c.toUpperCase()} (${exited[c]} exited)`;
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

    // Spook Slush Fund in Phase 3
    if (caps.can_spook) {
      const spookWrap = document.createElement("div");
      spookWrap.style.display = "inline-flex";
      spookWrap.style.alignItems = "center";
      spookWrap.style.gap = "6px";

      const spookInput = document.createElement("input");
      spookInput.type = "number";
      spookInput.min = "0";
      spookInput.max = String(human.money || 0);
      spookInput.value = "0";
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
      spookBtn.innerText = "⚡ Spook: Slush Fund (2 Free + $1/extra)";
      spookBtn.onclick = () => {
        const amt = parseInt(spookInput.value, 10);
        doSpook(isNaN(amt) ? 0 : Math.max(0, amt));
      };

      spookWrap.appendChild(document.createTextNode("Extra $:"));
      spookWrap.appendChild(spookInput);
      spookWrap.appendChild(spookBtn);
      controls.appendChild(spookWrap);
    }


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
    if (caps.is_market_share && (caps.ad_campaign_actions || 0) > 0) {
      // v0.36.0 Ad Campaign (Red ★): pay $2 for +1 Market Share; does not count toward the Public Relations limit
      const adBtn = document.createElement("button");
      adBtn.className = "action-btn";
      adBtn.style.color = "var(--color-red)";
      adBtn.innerText = `R2 Ad Campaign ($${caps.ad_campaign_cost} -> +1 Market Share) x${caps.ad_campaign_actions}`;
      adBtn.disabled = !caps.can_ad_campaign;
      adBtn.title = caps.can_ad_campaign ? "Pay to gain +1 Market Share" : "Requires Money and Market Share below its maximum";
      adBtn.onclick = () => doStarAction("R2");
      controls.appendChild(adBtn);
    }


    if (caps.is_share_regain) {
      // v0.36.0 Public Relations Track: spend research to regain Market Share (limit per Operations Turn)
      const prBtn = document.createElement("button");
      prBtn.className = "action-btn";
      prBtn.style.borderColor = "#c084fc";
      prBtn.style.color = "#c084fc";
      prBtn.innerText = `📣 Regain Market Share (${caps.regain_cost} 🔬 → +1; ${caps.regain_left_this_turn}/${caps.regain_cap} left this turn)`;
      prBtn.disabled = !caps.can_regain_market_share;
      prBtn.title = caps.can_regain_market_share
        ? `Public Relations Track: spend ${caps.regain_cost} 🔬 for +1 Market Share`
        : "Requires research, Market Share below its maximum, and turn limit remaining";
      prBtn.onclick = () => doRegainMarketShare();
      controls.appendChild(prBtn);
    }

    // Cryptographic Patents (INV-PATENT-CONV-01) - v0.35 ruleset only
    const patCost = caps.patent_cost || 4;
    const canPat = caps.can_file_patent || false;
    const patBtn = document.createElement("button");
    patBtn.className = "action-btn";
    patBtn.style.borderColor = "#c084fc";
    patBtn.style.color = "#c084fc";
const patGain = caps.patent_gain || 1;
    const legacyPatCash = (caps.max_track_level || 2) === 2 && (human.patent_level || 0) >= 2;
    patBtn.innerText = `📜 File Patent (${patCost} 🔬 → +${patGain} Sec${legacyPatCash ? ', +$1' : ''})`;
    patBtn.disabled = !canPat;
    patBtn.title = canPat ? `Spend ${patCost} 🔬 to gain +${patGain} Corporate Secret${patGain === 1 ? '' : 's'}` : `Requires ${patCost} 🔬 to file patent`;
    patBtn.onclick = () => doFilePatent();
    if (!caps.is_share_regain) controls.appendChild(patBtn);

    // Terminal Hardware Upgrade Tracks (INV-UPGRADE-TRACK-01)
    const upgradeCosts = caps.upgrade_track_costs || {};
    const canUp = caps.can_upgrade_track || {};
    const maxTrackLevel = caps.max_track_level || 2;
    const btPreview = caps.breakthrough_preview || {};
    const btNote = (key) => (btPreview[key] && btPreview[key].breakthrough ? ` — Breakthrough: ${btPreview[key].breakthrough}` : "");

    // Triage Level 3 Breakthrough prompt (pay $3 to replace a Gray Legacy die; resolves before other operations)
    if (caps.pending_breakthrough) {
      const opts = caps.pending_breakthrough.options || {};
      const box = document.createElement("div");
      box.className = "breakthrough-prompt";
      box.style.cssText = "border: 1px solid #38bdf8; border-radius: 4px; padding: 6px; margin: 4px 0; display: flex; gap: 6px; flex-wrap: wrap; align-items: center;";
      const label = document.createElement("span");
      label.style.color = "#38bdf8";
      label.innerText = `⚙️ Triage L3 Breakthrough: pay $${opts.cost || 3} to replace 1 Gray Legacy die with a Central Market die`;
      box.appendChild(label);
      const graySel = document.createElement("select");
      graySel.innerHTML = (opts.gray_die_ids || []).map((id) => `<option value="${id}">Gray #${id}</option>`).join("");
      box.appendChild(graySel);
      const colorSel = document.createElement("select");
      colorSel.innerHTML = (opts.colors || []).map((c) => `<option value="${c}">${c.toUpperCase()}</option>`).join("");
      box.appendChild(colorSel);
      const okBtn = document.createElement("button");
      okBtn.className = "action-btn btn-accent";
      okBtn.innerText = `Confirm ($${opts.cost || 3})`;
      okBtn.disabled = !opts.possible;
      okBtn.onclick = () => doResolveBreakthrough(true, parseInt(graySel.value, 10), colorSel.value);
      box.appendChild(okBtn);
      const noBtn = document.createElement("button");
      noBtn.className = "action-btn";
      noBtn.innerText = "Decline";
      noBtn.onclick = () => doResolveBreakthrough(false, null, null);
      box.appendChild(noBtn);
      controls.appendChild(box);
    }

    if ((human.triage_level || 0) < maxTrackLevel && upgradeCosts.triage !== null && upgradeCosts.triage !== undefined) {
      const triageCost = upgradeCosts.triage;
      const triageBtn = document.createElement("button");
      triageBtn.className = "action-btn";
      triageBtn.style.borderColor = "#38bdf8";
      triageBtn.style.color = "#38bdf8";
      triageBtn.innerText = `⚙️ Upgr Triage [L${(human.triage_level || 0) + 1}] (${triageCost} 🔬)`;
      triageBtn.disabled = !canUp.triage;
      triageBtn.title = canUp.triage ? `Upgrade Triage to Level ${(human.triage_level || 0) + 1} (${triageCost} 🔬)` : `Requires ${triageCost} 🔬`;
      triageBtn.title += btNote("triage");
      triageBtn.onclick = () => doUpgradeTrack("triage");
      controls.appendChild(triageBtn);
    }

    if ((human.release_level || 0) < maxTrackLevel && upgradeCosts.release !== null && upgradeCosts.release !== undefined) {
      const relCost = upgradeCosts.release;
      const relBtn = document.createElement("button");
      relBtn.className = "action-btn";
      relBtn.style.borderColor = "#06b6d4";
      relBtn.style.color = "#06b6d4";
      relBtn.innerText = `🚀 Upgr Release [L${(human.release_level || 0) + 1}] (${relCost} 🔬)`;
      relBtn.disabled = !canUp.release;
      relBtn.title = canUp.release ? `Upgrade Release to Level ${(human.release_level || 0) + 1} (${relCost} 🔬)` : `Requires ${relCost} 🔬`;
      relBtn.title += btNote("release");
      relBtn.onclick = () => doUpgradeTrack("release");
      controls.appendChild(relBtn);
    }

    if ((human.defense_level || 0) < maxTrackLevel && upgradeCosts.defense !== null && upgradeCosts.defense !== undefined) {
      const defCost = upgradeCosts.defense;
      const defBtn = document.createElement("button");
      defBtn.className = "action-btn";
      defBtn.style.borderColor = "#4ade80";
      defBtn.style.color = "#4ade80";
      defBtn.innerText = `🛡️ Upgr Defense [L${(human.defense_level || 0) + 1}] (${defCost} 🔬)`;
      defBtn.disabled = !canUp.defense;
      defBtn.title = canUp.defense ? `Upgrade Defense Grid to Level ${(human.defense_level || 0) + 1} (${defCost} 🔬)` : `Requires ${defCost} 🔬`;
      defBtn.title += btNote("defense");
      defBtn.onclick = () => doUpgradeTrack("defense");
      controls.appendChild(defBtn);
    }

    if ((human.patent_level || 0) < maxTrackLevel && upgradeCosts.patent !== null && upgradeCosts.patent !== undefined) {
      const patentTrackCost = upgradeCosts.patent;
      const patUpBtn = document.createElement("button");
      patUpBtn.className = "action-btn";
      patUpBtn.style.borderColor = "#a855f7";
      patUpBtn.style.color = "#a855f7";
      patUpBtn.innerText = `🔬 Upgr ${caps.is_share_regain ? 'Public Relations' : 'Patents'} [L${(human.patent_level || 0) + 1}] (${patentTrackCost} 🔬)`;
      patUpBtn.disabled = !canUp.patent;
      patUpBtn.title = canUp.patent ? `Upgrade ${caps.patent_track_name || 'Patent R&D'} to Level ${(human.patent_level || 0) + 1} (${patentTrackCost} 🔬)` : `Requires ${patentTrackCost} 🔬`;
      patUpBtn.title += btNote("patent");
      patUpBtn.onclick = () => doUpgradeTrack("patent");
      controls.appendChild(patUpBtn);
    }

    // End Turn
    const endTurnBtn = document.createElement("button");
    endTurnBtn.className = "action-btn btn-accent";
    endTurnBtn.innerText = "End Turn";
    endTurnBtn.disabled = !caps.can_end_turn;
    endTurnBtn.onclick = doEndTurn;
    controls.appendChild(endTurnBtn);
  } else if (state.phase === 7) {
    const viewBtn = document.createElement("button");
    viewBtn.className = "action-btn btn-accent";
    viewBtn.innerText = "View Standings";
    viewBtn.onclick = () => openModal("gameOverModal");
    controls.appendChild(viewBtn);
  }
}


// ---------------------------------------------------------------------------
// Phase 3: Income (simultaneous) — preview, optional Signature Protocol targets, confirm
// ---------------------------------------------------------------------------
function renderIncomePanel(controls, human, caps) {
  const incomeMap = state.last_income_result || {};
  const inc = incomeMap[human.player_id] || incomeMap[String(human.player_id)] || { money: 0, research: 0, secrets: 0, details: [] };
  const panel = document.createElement("div");
  panel.className = "confirm-income-panel";
  const details = inc.details || [];
  const ownedColored = []
    .concat(human.in_production_dice || [], human.glitched_dice || [], human.scanned_dice || [], human.ready_for_release_dice || [])
    .filter((d) => d.color !== "gray" && d.color !== "white");
  const ud = [].concat(human.glitched_dice || [], human.scanned_dice || []);

  panel.innerHTML = `
    <div class="confirm-income-header">
      <div class="confirm-income-title-wrap">
        <span class="confirm-badge">PHASE 3: INCOME</span>
        <span class="confirm-income-title">COLLECT $, 🔬 &amp; ★ FROM DICE STILL IN PRODUCTION</span>
      </div>
      <span style="font-size: 0.72rem; color: var(--text-dim); font-family: monospace;">
        Round ${state.current_round} // Income is banked before Phase 4 attacks
      </span>
    </div>
    <div class="confirm-income-card" style="border-color: rgba(234, 179, 8, 0.4);">
      <div class="confirm-income-card-hdr">
        <span style="color: #facc15;">${inc.preview ? "INCOME PREVIEW" : "INCOME COLLECTED"}</span>
        <span>Income slot + Shield slots + White Contractor dice</span>
      </div>
      <div class="confirm-pills-row">
        <span class="income-pill money">+$${inc.money || 0} Cash</span>
        <span class="income-pill research">+${inc.research || 0} 🔬 Research</span>
        ${(inc.secrets || 0) > 0 ? `<span class="income-pill secrets">+${inc.secrets} Secrets</span>` : ""}
      </div>
      <div class="confirm-dice-chips">
        ${details.length > 0
          ? details.map((d) => `<span class="confirm-die-chip ${d.color}"><strong>${d.color.toUpperCase()}:</strong> ${d.face_name}${d.star_note ? " (" + d.star_note + ")" : ""}</span>`).join("")
          : '<span style="font-size: 0.75rem; color: var(--text-dim); font-style: italic;">No dice In Production yield income this round.</span>'}
      </div>
    </div>
    <div class="confirm-action-bar" id="incomeActionBar"></div>
  `;

  const bar = panel.querySelector("#incomeActionBar");
  const burnSelects = [];
  let diagSelect = null;
  const triggers = Math.max(1, inc.purple_star_triggers || 1);
  if (caps.can_spook_burn && ownedColored.length > 0) {
    // One Burn Notice per Purple ★ trigger (OQ-17); the same die cannot be burned twice.
    for (let t = 0; t < triggers; t++) {
      const burnSelect = document.createElement("select");
      burnSelect.style.padding = "4px 8px";
      burnSelect.className = "burn-notice-select";
      burnSelect.innerHTML = `<option value="">Burn Notice ${triggers > 1 ? "#" + (t + 1) + " " : ""}: decline</option>` +
        ownedColored.map((d) => `<option value="${d.die_id}">Burn Notice ${triggers > 1 ? "#" + (t + 1) + " " : ""}: ${d.color.toUpperCase()} #${d.die_id} (+1 Secret)</option>`).join("");
      bar.appendChild(burnSelect);
      burnSelects.push(burnSelect);
    }
  }
  if (caps.can_phreaker_diagnostics) {
    diagSelect = document.createElement("select");
    diagSelect.style.padding = "4px 8px";
    diagSelect.innerHTML = ud.length > 0
      ? ud.map((d) => `<option value="${d.die_id}">Jumper Diagnostics: roll ${d.color.toUpperCase()} #${d.die_id}</option>`).join("")
      : `<option value="">Jumper Diagnostics: empty Under Development (+$1)</option>`;
    bar.appendChild(diagSelect);
  }
  const btn = document.createElement("button");
  btn.className = "action-btn btn-confirm-income";
  btn.innerText = caps.can_confirm_income ? "✓ Confirm Income" : "Waiting for other corporations…";
  btn.disabled = !caps.can_confirm_income;
  btn.onclick = () => {
    const burnIds = [];
    burnSelects.forEach((sel) => {
      if (sel.value === "") return;
      const id = parseInt(sel.value, 10);
      if (!burnIds.includes(id)) burnIds.push(id);
    });
    const diagId = diagSelect && diagSelect.value !== "" ? parseInt(diagSelect.value, 10) : null;
    doConfirmIncome(burnIds.length > 0 ? burnIds : null, diagId);
  };
  bar.appendChild(btn);
  controls.appendChild(panel);
}

// ---------------------------------------------------------------------------
// Phase 5: CI/CD Pipeline Shift — Magnetic Splice, Scanned Graduation choice
// ---------------------------------------------------------------------------
function renderGraduationPanel(controls, human, caps) {
  const pendMap = state.pending_graduation || {};
  const pend = pendMap[human.player_id] || pendMap[String(human.player_id)];
  if (!pend || !caps.can_choose_graduates) {
    const waitMsg = document.createElement("span");
    waitMsg.style.fontSize = "0.8rem";
    waitMsg.style.color = "var(--text-dim)";
    waitMsg.innerText = "Phase 5: CI/CD Pipeline Shift — waiting for other corporations.";
    controls.appendChild(waitMsg);
    return;
  }
  if (selectedGraduateIds === null) {
    initSelectedGraduateIds(pend.default_graduate_ids || []);
  }
  const chosen = selectedGraduateIds || new Set();
  const panel = document.createElement("div");
  panel.className = "confirm-income-panel";
  panel.innerHTML = `
    <div class="confirm-income-header">
      <div class="confirm-income-title-wrap">
        <span class="confirm-badge">PHASE 5: CI/CD PIPELINE SHIFT</span>
        <span class="confirm-income-title">SCANNED GRADUATION (${chosen.size} / ${pend.n} — Release Bandwidth ${pend.release_bandwidth})</span>
      </div>
      <span style="font-size: 0.72rem; color: var(--text-dim);">
        Magnetic Splice → In Production → Scanned Box → Ready for Release (≤ Release Bandwidth, your choice; fewer is allowed) → Glitched → Scanned (≤ Triage Bandwidth)
      </span>
    </div>
    <div class="confirm-malware-grid">
      ${(pend.candidates || []).map((c) => `
        <div class="malware-die-card ${c.color} ${chosen.has(c.die_id) ? "selected" : ""}" data-die-id="${c.die_id}">
          <div class="malware-die-top"><span style="font-weight: 700; font-size: 0.72rem; color: #fff;">${c.color.toUpperCase()} DIE #${c.die_id}</span></div>
          <div class="malware-die-status">${chosen.has(c.die_id) ? "✓ GRADUATES TO READY" : "○ Held in Scanned Box"}</div>
        </div>`).join("")}
    </div>
    <div class="confirm-action-bar" id="gradActionBar"></div>
  `;
  panel.querySelectorAll(".malware-die-card").forEach((card) => {
    card.onclick = () => {
      toggleSelectedGraduateId(parseInt(card.getAttribute("data-die-id"), 10), pend.n);
      renderActionDock();
    };
  });
  const bar = panel.querySelector("#gradActionBar");
  let spliceSelect = null;
  let hotfixSelect = null;
  const glitched = pend.glitched || [];
  if (pend.splice_available && glitched.length > 0) {
    spliceSelect = document.createElement("select");
    spliceSelect.innerHTML = `<option value="">Magnetic Splice: decline</option>` +
      glitched.map((d) => `<option value="${d.die_id}">Magnetic Splice: ${d.color.toUpperCase()} #${d.die_id} → Ready</option>`).join("");
    bar.appendChild(spliceSelect);
  }
  if (pend.hotfix_available && glitched.length > 0) {
    hotfixSelect = document.createElement("select");
    hotfixSelect.innerHTML = glitched.map((d) => `<option value="${d.die_id}">Emergency Hotfix: ${d.color.toUpperCase()} #${d.die_id} → Ready</option>`).join("");
    bar.appendChild(hotfixSelect);
  }
  const btn = document.createElement("button");
  btn.className = "action-btn btn-confirm-income";
  btn.innerText = `✓ Confirm Pipeline Shift (${chosen.size} graduate${chosen.size === 1 ? "" : "s"})`;
  btn.onclick = () => {
    const spliceId = spliceSelect && spliceSelect.value !== "" ? parseInt(spliceSelect.value, 10) : null;
    const hotfixId = hotfixSelect && hotfixSelect.value !== "" ? parseInt(hotfixSelect.value, 10) : null;
    doChooseGraduates(Array.from(chosen), spliceId, hotfixId);
  };
  bar.appendChild(btn);
  controls.appendChild(panel);
}
