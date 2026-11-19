/**
 * Rogue Agent — Action Dock Component
 */

import {
  state,
  PHASE_OPERATIONS,
  PHASE_PIPELINE,
  selectedBacklashDieId,
  setSelectedBacklashDieId,
  selectedPhreakerDieId,
  setSelectedPhreakerDieId,
  getEligibleBacklashDice,
  cipherDiscountSelected,
  setCipherDiscountSelected,
  selectedRerollIndices,
  clearSelectedRerolls,
  selectedChoiceDeclarations,
  selectedGraduateIds,
  initSelectedGraduateIds,
  toggleSelectedGraduateId,
} from "../state.js";
import {
  doResolveBreakthrough,
  doCapitalInjection,
  doHireContractors,
  doRoll,
  doReroll,
  doOverrideFace,
  doLockIn,
  doCompile,
  doConfirmIncome,
  doConfirmAttacks,
  doChooseGraduates,
  doAcoustic,
  doSpook,
  doDirtyIncome,
  doPhreaker,
  doStarAction,
  doEndTurn,
  doUpgradeTrack,
  doRegainMarketShare,
  doPenTest,
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
      if (caps.can_hire_contractors && (state.contractor_max_hire > 0 || state.contractor_supply > 0)) {
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

    if (caps.can_lock_in || caps.can_reroll) {
      const rolled = human.rolled_pool || [];
      const rerollsLeft = human.rerolls_remaining !== undefined ? human.rerolls_remaining : 0;
      const maxRerolls = human.max_rerolls !== undefined ? human.max_rerolls : 2;

      const rerollInfo = document.createElement("span");
      rerollInfo.style.fontSize = "0.8rem";
      rerollInfo.style.color = "#38bdf8";
      rerollInfo.style.fontWeight = "600";
      rerollInfo.innerText = `Rerolls: ${rerollsLeft}/${maxRerolls} left | Click dice to reroll (a Secret face may be kept or rerolled)`;
      controls.appendChild(rerollInfo);

      if (caps.can_reroll && selectedRerollIndices.size > 0) {
        const hasLockedSelected = Array.from(selectedRerollIndices).some((i) => {
          const d = rolled[i];
          return d && d.is_locked;
        });
        const rerollBtn = document.createElement("button");
        rerollBtn.className = "action-btn btn-accent";
        if (hasLockedSelected) {
          rerollBtn.style.borderColor = "#38bdf8";
          rerollBtn.innerText = `Reroll Selected (${selectedRerollIndices.size}) [⚡ Brute-Force Bypass]`;
          rerollBtn.onclick = () => doReroll(true);
        } else {
          rerollBtn.innerText = `Reroll Selected (${selectedRerollIndices.size})`;
          rerollBtn.onclick = () => doReroll(false);
        }
        controls.appendChild(rerollBtn);
      }

      if (caps.can_override_face_helix) buildOverridePanel(controls, human, "helix");
      if (caps.can_override_face_prodigy) buildOverridePanel(controls, human, "prodigy");
      if (caps.can_override_face_release_l4) buildOverridePanel(controls, human, "release_l4", caps.release_l4_gray_indices || []);

      // Drop stale choice declarations for dice that changed after a reroll
      Object.keys(selectedChoiceDeclarations).forEach((idxStr) => {
        const i = parseInt(idxStr, 10);
        if (!rolled[i] || !rolled[i].current_face || !rolled[i].current_face.is_choice) {
          delete selectedChoiceDeclarations[idxStr];
        }
      });

      // Vulnerability preview: +1 per ⚠ on the final faces at Deploy
      const vt = state.vulnerability_track || { max: 15, min_target: 4, bands: [] };
      const icons = rolled.reduce((n, d) => n + ((d.current_face && d.current_face.vuln) || 0), 0);
      const vNow = human.vulnerability || 0;
      const vAfter = Math.min(vt.max, vNow + icons);
      const band = (v) => (vt.bands || []).find((b) => v >= b.from && v <= b.to);
      const bAfter = band(vAfter);
      const vulnInfo = document.createElement("span");
      vulnInfo.className = "vuln-preview " + (bAfter ? "at-risk" : "safe");
      vulnInfo.innerText = `⚠ ${icons} on your faces → Vulnerability ${vNow} → ${vAfter}`
        + (bAfter
          ? ` (a Green hit costs ${bAfter.damage} Corporate Secret${bAfter.damage === 1 ? "" : "s"})`
          : ` (safe zone 0–${vt.min_target - 1}: Green cubes never hit you)`);
      controls.appendChild(vulnInfo);

      // Choice Face selectors and Secret face notes for the rolled pool
      rolled.forEach((d, idx) => {
        const face = d.current_face;
        if (!face || face.is_glitch) return;
        const colStr = d.color === "gray" ? "#94a3b8" : `var(--color-${d.color})`;

        if (face.secrets_pending) {
          const noteWrap = document.createElement("div");
          noteWrap.style.fontSize = "0.8rem";
          const yNow = (human.secret_yield_now || {})[d.color];
          noteWrap.innerHTML = `<span style="color: ${colStr};">Die #${idx + 1} (${d.color.toUpperCase()}):</span> <span class="secret-face-tag">🔒 SECRET FACE ⚠ → PROCESSING BOX${yNow !== undefined ? ` (+${yNow} Corporate Secrets if it left now)` : ""}</span>`;
          controls.appendChild(noteWrap);
          return;
        }

        if (face.is_choice) {
          const wrap = document.createElement("div");
          wrap.style.display = "inline-flex";
          wrap.style.alignItems = "center";
          wrap.style.gap = "4px";
          wrap.style.fontSize = "0.8rem";

          const select = document.createElement("select");
          select.className = "dock-select";
          (face.choices || []).forEach((c, cIdx) => {
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
          wrap.innerHTML = `<span style="color: ${colStr};">Die #${idx + 1} (${d.color.toUpperCase()} Choice${face.vuln ? " ⚠" : ""}):</span>`;
          wrap.appendChild(select);
          controls.appendChild(wrap);
        }
      });

      const lockBtn = document.createElement("button");
      lockBtn.className = "action-btn btn-accent";
      lockBtn.innerText = `Deploy Dice (+${vAfter - vNow} Vulnerability)`;
      lockBtn.disabled = !caps.can_lock_in;
      lockBtn.onclick = () => {
        clearSelectedRerolls();
        doLockIn();
      };
      controls.appendChild(lockBtn);
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
  } else if (state.phase === PHASE_PIPELINE) {
    renderGraduationPanel(controls, human, caps);
  } else if (state.phase === 4) {
    renderAttackPanel(controls, human, caps);
  } else if (state.phase === PHASE_OPERATIONS) {
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


    // Pen Test Track: lower Vulnerability for research (limit per Operations Turn)
    const penLeft = caps.pen_test_left_this_turn || 0;
    const penBtn = document.createElement("button");
    penBtn.className = "action-btn btn-pen-test";
    penBtn.innerText = `🧪 Pen Test (${caps.pen_test_cost} 🔬 → −1 Vulnerability; ${penLeft}/${caps.pen_test_limit} left this turn)`;
    penBtn.disabled = !caps.can_pen_test;
    penBtn.title = caps.can_pen_test
      ? `Vulnerability ${human.vulnerability} → ${human.vulnerability - 1}`
      : "Requires research, Vulnerability above 0, and Pen Test limit remaining";
    penBtn.onclick = () => doPenTest(1);
    controls.appendChild(penBtn);

    if (caps.is_share_regain) {
      // Public Relations Track: regain Market Share (limit per Operations Turn)
      const price = caps.regain_currency === "money" ? `$${caps.regain_cost}` : `${caps.regain_cost} 🔬`;
      const prBtn = document.createElement("button");
      prBtn.className = "action-btn";
      prBtn.style.borderColor = "#c084fc";
      prBtn.style.color = "#c084fc";
      prBtn.innerText = `📣 Regain Market Share (${price} → +1; ${caps.regain_left_this_turn}/${caps.regain_cap} left this turn)`;
      prBtn.disabled = !caps.can_regain_market_share;
      prBtn.title = caps.can_regain_market_share
        ? `Public Relations Track: pay ${price} for +1 Market Share`
        : `Requires ${price}, Market Share below its maximum, and turn limit remaining`;
      prBtn.onclick = () => doRegainMarketShare();
      controls.appendChild(prBtn);
    }

    // Terminal Hardware Upgrade Tracks (INV-UPGRADE-TRACK-01)
    const upgradeCosts = caps.upgrade_track_costs || {};
    const canUp = caps.can_upgrade_track || {};
    const maxTrackLevel = caps.max_track_level || 4;
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

    const trackNames = caps.track_names || {};
    const trackStyle = { defense: ["🧪", "#4ade80"], triage: ["⚙️", "#38bdf8"], release: ["🚀", "#06b6d4"], patent: ["📣", "#a855f7"] };
    ["defense", "triage", "release", "patent"].forEach((key) => {
      const lvl = human[`${key}_level`] || 0;
      const cost = upgradeCosts[key];
      if (lvl >= maxTrackLevel || cost === null || cost === undefined) return;
      const [icon, color] = trackStyle[key];
      const name = (trackNames[key] || key).replace(/ Track$/, "");
      const enc = (human.encrypted_research_tracks || []).some((t) => t === key.toUpperCase() || (key === "patent" && t === "PR"));
      const btn = document.createElement("button");
      btn.className = "action-btn";
      btn.style.borderColor = color;
      btn.style.color = color;
      btn.innerText = `${icon} Upgr ${name} [L${lvl + 1}] (${cost} 🔬${enc ? ", green cube: 2×" : ""})`;
      btn.disabled = !canUp[key];
      btn.title = (canUp[key] ? `Upgrade ${trackNames[key] || key} to Level ${lvl + 1} (${cost} 🔬)` : `Requires ${cost} 🔬`) + btNote(key);
      btn.onclick = () => doUpgradeTrack(key);
      controls.appendChild(btn);
    });

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
// Phase 4: Attack Resolution (v0.47.0) — nothing is blocked. Red & Blue hit every survivor, Green cubes hit the
// highest Vulnerability at the minimum target or more (one cube at a time), then Target Lock Signature Attacks.
// The human only declares Institutional Override and Target Lock choices before damage resolves.
// ---------------------------------------------------------------------------
function renderAttackPanel(controls, human, caps) {
  const attackRes = state.last_attack_result || {};
  const exited = (state.last_compile_result || {}).exited_cubes || {};
  const threatMap = attackRes.threat_summary || {};
  const ts = threatMap[human.player_id] || threatMap[String(human.player_id)] || attackRes.human_threat || {};
  const vt = attackRes.vulnerability_track || state.vulnerability_track || { bands: [], min_target: 4 };
  const names = {};
  (state.players || []).forEach((p) => { names[p.player_id] = p.player_id === human.player_id ? "You" : p.name; });
  const red = ts.red || { cubes: exited.red || 0, attack: 0, market_share_lost: 0 };
  const blue = ts.blue || { cubes: exited.blue || 0, attack: 0, secrets_lost: 0 };
  const green = ts.green || { cubes: exited.green || 0, attack: 0, hits: [], secrets_at_risk: 0 };
  const sig = attackRes.signature || {};
  const greenHits = attackRes.green_hits || [];

  const panel = document.createElement("div");
  panel.className = "confirm-income-panel";

  const greenRows = greenHits.length === 0
    ? `<div class="confirm-threat-row"><span class="threat-label green">▲ GREEN // MALWARE</span><span>No Green cubes this round</span></div>`
    : greenHits.map((g) => {
      const who = g.pids.length ? g.pids.map((pid) => names[pid] || `Player ${pid + 1}`).join(", ") : null;
      const mine = g.pids.includes(human.player_id);
      return `<div class="confirm-threat-row ${mine ? "threat-row-hit" : ""}">
        <span class="threat-label green">▲ GREEN CUBE ${g.cube + 1}</span>
        <span>${who
          ? `hits <strong>${who}</strong> at Vulnerability ${g.v} → <strong class="${mine ? "loss" : ""}">−${g.damage} Corporate Secret${g.damage === 1 ? "" : "s"}</strong>, reset to 0`
          : `no player at Vulnerability ${vt.min_target}+ (no effect)`}</span>
      </div>`;
    }).join("");

  const vulnRows = (state.players || [])
    .filter((p) => !p.is_patient_zero)
    .map((p) => {
      const v = p.vulnerability || 0;
      const b = (vt.bands || []).find((x) => v >= x.from && v <= x.to);
      return `<span class="vuln-chip ${b ? "at-risk" : "safe"} ${p.player_id === human.player_id ? "mine" : ""}">
        ${names[p.player_id]}: ⚠ ${v}${b ? ` (−${b.damage})` : " (safe)"}</span>`;
    }).join("");

  const locked = (sig.locked_pids || []).includes(human.player_id);
  const choices = ts.signature_choices || {};
  let sigHtml = "";
  if (sig.enabled && (sig.locked_pids || []).length > 0 && sig.dominant_color) {
    const who = sig.locked_pids.map((pid) => names[pid]).join(", ");
    let choiceHtml = "";
    if (locked && choices.green_tracks) {
      choiceHtml = `<div class="sig-choice">Choose ${choices.green_tracks.count} Research Tracks for the green cubes:
        ${choices.green_tracks.options.map((o) => `<label><input type="checkbox" class="sig-track" value="${o.track}"> ${o.name}</label>`).join(" ")}</div>`;
    } else if (locked && choices.red_recipients) {
      choiceHtml = `<div class="sig-choice">Tied for the least Market Share after the drain — choose who gains 2:
        <select id="sigRedRecipient" class="dock-select">${choices.red_recipients.map((pid) => `<option value="${pid}">${pid === -1 ? "SETEC Corp" : names[pid]}</option>`).join("")}</select></div>`;
    }
    sigHtml = `
      <div class="confirm-income-card sig-card ${sig.dominant_color}">
        <div class="confirm-income-card-hdr">
          <span>🎯 TARGET LOCK — ${sig.dominant_color.toUpperCase()} DOMINANT</span>
          <span>${who}</span>
        </div>
        <div class="confirm-threat-row"><span>${sig.effect}</span></div>
        ${choiceHtml}
      </div>`;
  }

  panel.innerHTML = `
    <div class="confirm-income-header">
      <div class="confirm-income-title-wrap">
        <span class="confirm-badge">PHASE 4: ATTACK RESOLUTION</span>
        <span class="confirm-income-title">NO CUBE CAN BE BLOCKED</span>
      </div>
      <span style="font-size: 0.72rem; color: var(--text-dim); font-family: monospace;">
        Round ${state.current_round} // Red → Blue → Green (one cube at a time) → Patient Zero → Target Lock
      </span>
    </div>
    ${attackRes.buffer_overflow ? `<div class="confirm-threat-row"><strong>Compile Buffer Overflow:</strong> no damage resolves this round; every Vulnerability carries over.</div>` : ""}
    <div class="confirm-income-grid">
      <div class="confirm-income-card">
        <div class="confirm-income-card-hdr">
          <span>EXIT TRAY</span>
          <span style="color: var(--text-highlight);">${exited.red || 0}R · ${exited.blue || 0}B · ${exited.green || 0}G · ${exited.black || 0}K</span>
        </div>
        <div class="confirm-threat-row">
          <span class="threat-label red">◆ RED // MARKET MANIPULATION</span>
          <span>${red.attack} cube${red.attack === 1 ? "" : "s"} → ${red.attack > 0
            ? `<strong class="loss">−${red.market_share_lost} Market Share</strong> (${ts.market_share} → ${Math.max(0, (ts.market_share || 0) - red.market_share_lost)}${(ts.market_share || 0) - red.market_share_lost <= 0 ? ", MARKET COLLAPSE" : ""})`
            : "no effect"}</span>
        </div>
        <div class="confirm-threat-row">
          <span class="threat-label blue">● BLUE // SPYWARE</span>
          <span>${blue.attack} cube${blue.attack === 1 ? "" : "s"} → ${blue.attack > 0 ? `<strong class="loss">−${blue.secrets_lost} Corporate Secret${blue.secrets_lost === 1 ? "" : "s"}</strong>` : "no effect"}</span>
        </div>
        ${greenRows}
      </div>
      <div class="confirm-income-card">
        <div class="confirm-income-card-hdr">
          <span>VULNERABILITY TRACK</span>
          <span>Safe zone 0–${vt.min_target - 1} · ${(vt.bands || []).map((b) => `${b.from}–${b.to}: −${b.damage}`).join(" · ")}</span>
        </div>
        <div class="vuln-chip-row">${vulnRows}</div>
        <div class="confirm-threat-row">
          <span>Your Green damage this round</span>
          <strong class="${green.secrets_at_risk > 0 ? "loss" : "safe-text"}">${green.secrets_at_risk > 0 ? `−${green.secrets_at_risk} Corporate Secrets` : "none"}</strong>
        </div>
      </div>
    </div>
    ${sigHtml}
    <div class="confirm-action-bar" id="attackActionBar"></div>
  `;

  const bar = panel.querySelector("#attackActionBar");
  if (!caps.can_confirm_attacks) {
    const waitMsg = document.createElement("span");
    waitMsg.style.fontSize = "0.8rem";
    waitMsg.style.color = "var(--text-dim)";
    waitMsg.innerText = "Waiting for other corporations to confirm their Phase 4 choices.";
    bar.appendChild(waitMsg);
    controls.appendChild(panel);
    return;
  }

  let aegisSel = null;
  if (ts.aegis && ts.aegis.available) {
    aegisSel = document.createElement("select");
    aegisSel.className = "dock-select";
    aegisSel.title = "Aegis Baffle Echo (Institutional Override, once per Version)";
    aegisSel.innerHTML = `<option value="none">Baffle Echo: do not use</option>`
      + (ts.aegis.qualifying_colors || []).map((c) => `<option value="${c}">Baffle Echo: ignore 1 ${c.toUpperCase()} cube</option>`).join("")
      + (ts.aegis.green_hit ? `<option value="green">Baffle Echo: cancel the Secret loss of 1 Green hit</option>` : "");
    bar.appendChild(aegisSel);
  }
  let slushChk = null;
  if (ts.slush_fund && ts.slush_fund.available) {
    const lbl = document.createElement("label");
    lbl.style.fontSize = "0.75rem";
    lbl.title = "DTO Slush Fund (Institutional Override, once per game)";
    lbl.innerHTML = `<input type="checkbox" id="slushFundCheck"> Use DTO Slush Fund (absorb up to 2 Secret loss from Blue cubes; once per game)`;
    bar.appendChild(lbl);
    slushChk = lbl.querySelector("input");
  }

  const btn = document.createElement("button");
  btn.className = "action-btn btn-confirm-income";
  btn.innerText = "✓ Confirm & Resolve Attacks";
  const needTracks = locked && choices.green_tracks ? choices.green_tracks.count : 0;
  const syncBtn = () => {
    const n = panel.querySelectorAll(".sig-track:checked").length;
    btn.disabled = needTracks > 0 && n !== needTracks;
    if (needTracks > 0) btn.innerText = n === needTracks ? "✓ Confirm & Resolve Attacks" : `Choose ${needTracks} tracks (${n}/${needTracks})`;
  };
  panel.querySelectorAll(".sig-track").forEach((cb) => { cb.onchange = syncBtn; });
  syncBtn();
  btn.onclick = () => {
    const tracks = Array.from(panel.querySelectorAll(".sig-track:checked")).map((cb) => cb.value);
    const recSel = panel.querySelector("#sigRedRecipient");
    doConfirmAttacks({
      aegisColor: aegisSel ? aegisSel.value : null,
      useSlushFund: slushChk ? slushChk.checked : null,
      signatureGreenTracks: needTracks > 0 ? tracks : null,
      signatureRedRecipient: recSel ? parseInt(recSel.value, 10) : null,
    });
  };
  bar.appendChild(btn);
  controls.appendChild(panel);
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
  const pbox = human.processing_box_dice || [];
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
        <span>Every die In Production</span>
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
    diagSelect.innerHTML = pbox.length > 0
      ? pbox.map((d) => `<option value="${d.die_id}">Jumper Diagnostics: Processing Box ${d.color.toUpperCase()} #${d.die_id} → Scanned Box (+${d.secret_yield} Secrets now)</option>`).join("")
      : ((human.scanned_dice || []).length > 0
        ? (human.scanned_dice || []).map((d) => `<option value="${d.die_id}">Jumper Diagnostics: roll Scanned Box ${d.color.toUpperCase()} #${d.die_id}</option>`).join("")
        : `<option value="">Jumper Diagnostics: empty Under Development (+$1)</option>`);
    bar.appendChild(diagSelect);
  }
  if (caps.can_capital_injection) {
    const ciBtn = document.createElement("button");
    ciBtn.className = "action-btn";
    ciBtn.style.borderColor = "#38bdf8";
    ciBtn.style.color = "#38bdf8";
    ciBtn.innerText = "★ Capital Injection (+$3 Cash)";
    ciBtn.onclick = () => doCapitalInjection();
    bar.appendChild(ciBtn);
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
// Phase 6: CI/CD Pipeline Shift — Magnetic Splice, Scanned Graduation choice
// ---------------------------------------------------------------------------
function renderGraduationPanel(controls, human, caps) {
  const pendMap = state.pending_graduation || {};
  const pend = pendMap[human.player_id] || pendMap[String(human.player_id)];
  if (!pend || !caps.can_choose_graduates) {
    const waitMsg = document.createElement("span");
    waitMsg.style.fontSize = "0.8rem";
    waitMsg.style.color = "var(--text-dim)";
    waitMsg.innerText = "Phase 6: CI/CD Pipeline Shift — waiting for other corporations.";
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
        <span class="confirm-badge">PHASE 6: CI/CD PIPELINE SHIFT</span>
        <span class="confirm-income-title">SCANNED GRADUATION (${chosen.size} / ${pend.n} — Release Bandwidth ${pend.release_bandwidth})</span>
      </div>
      <span style="font-size: 0.72rem; color: var(--text-dim);">
        Magnetic Splice → In Production → Scanned Box → Ready for Release (≤ Release Bandwidth, your choice; fewer is allowed) → Conveyor Triage: Processing Box → Scanned Box (≤ Triage Bandwidth, oldest first, no choice)
      </span>
    </div>
    <div class="confirm-malware-grid">
      ${(pend.candidates || []).map((c) => `
        <div class="malware-die-card ${c.color} ${chosen.has(c.die_id) ? "selected" : ""}" data-die-id="${c.die_id}">
          <div class="malware-die-top"><span style="font-weight: 700; font-size: 0.72rem; color: #fff;">${c.color.toUpperCase()} DIE #${c.die_id}</span></div>
          <div class="malware-die-status">${chosen.has(c.die_id) ? "✓ GRADUATES TO READY" : "○ Held in Scanned Box"}</div>
        </div>`).join("")}
    </div>
    ${(pend.processing_box || []).length > 0 ? `
    <div class="confirm-income-card" style="border-color: rgba(244, 63, 94, 0.4); margin-top: 8px;">
      <div class="confirm-income-card-hdr">
        <span style="color: #fda4af;">CONVEYOR TRIAGE (PROCESSING BOX, OLDEST FIRST)</span>
        <span>Triage Bandwidth ${pend.triage_bandwidth}</span>
      </div>
      <div class="confirm-dice-chips">
        ${pend.processing_box.map((d, i) => `<span class="confirm-die-chip ${d.color}"><strong>#${i + 1} ${d.color.toUpperCase()}:</strong> +${d.yield} Secrets${d.will_triage ? " (moves this phase)" : " (stays)"}</span>`).join("")}
      </div>
    </div>` : ""}
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
  const glitched = pend.processing_box || pend.glitched || [];
  if (pend.splice_available && glitched.length > 0) {
    spliceSelect = document.createElement("select");
    spliceSelect.innerHTML = `<option value="">Magnetic Splice: decline</option>` +
      glitched.map((d) => `<option value="${d.die_id}">Magnetic Splice: ${d.color.toUpperCase()} #${d.die_id} → Ready for Release${d.yield !== undefined ? ` (+${d.yield} Secrets now)` : ""}</option>`).join("");
    bar.appendChild(spliceSelect);
  }
  const btn = document.createElement("button");
  btn.className = "action-btn btn-confirm-income";
  btn.innerText = `✓ Confirm Pipeline Shift (${chosen.size} graduate${chosen.size === 1 ? "" : "s"})`;
  btn.onclick = () => {
    const spliceId = spliceSelect && spliceSelect.value !== "" ? parseInt(spliceSelect.value, 10) : null;
    doChooseGraduates(Array.from(chosen), spliceId);
  };
  bar.appendChild(btn);
  controls.appendChild(panel);
}


/** Brute-Force Bypass (Helix) / Arbitrary Code Execution (Prodigy) / Release Track Level 4 (1 Gray Legacy die):
 * turn one rolled die to a legal face. */
function buildOverridePanel(controls, human, source, onlyIndices = null) {
  const rolled = human.rolled_pool || [];
  if (rolled.length === 0) return;
  const wrap = document.createElement("div");
  wrap.style.display = "inline-flex";
  wrap.style.alignItems = "center";
  wrap.style.gap = "6px";
  wrap.style.flexWrap = "wrap";
  const styleSel = (el) => {
    el.style.padding = "4px 8px";
    el.style.background = "var(--bg-card)";
    el.style.color = "#fff";
    el.style.border = "1px solid var(--border-color)";
    el.style.borderRadius = "4px";
  };
  const label = document.createElement("span");
  label.style.fontSize = "0.8rem";
  label.style.color = "#38bdf8";
  label.innerText = {
    helix: "⚡ Brute-Force Bypass (+1 free reroll; set 1 die to any non-Star face, Secret face allowed):",
    prodigy: "⚡ Arbitrary Code Execution (set 1 other die to any non-Star, non-Secret face):",
    release_l4: "🚀 Release Track Level 4 (set 1 rolled Gray Legacy die to any printed face):",
  }[source];
  const dieSel = document.createElement("select");
  styleSel(dieSel);
  rolled.forEach((d, i) => {
    if (onlyIndices && !onlyIndices.includes(i)) return;
    const o = document.createElement("option");
    o.value = String(i);
    o.innerText = `Die #${i + 1} ${d.color.toUpperCase()} (${d.current_face ? d.current_face.name : "?"})`;
    dieSel.appendChild(o);
  });
  const faceSel = document.createElement("select");
  styleSel(faceSel);
  const fillFaces = () => {
    faceSel.innerHTML = "";
    const d = rolled[parseInt(dieSel.value, 10)];
    (d.faces || []).forEach((f, fi) => {
      if (f.is_star) return;
      if (source === "prodigy" && f.secrets_pending) return;
      const o = document.createElement("option");
      o.value = String(fi);
      o.innerText = (f.secrets_pending ? "Secret face" : f.name) + (f.vuln && !String(f.name).includes("⚠") ? " ⚠" : "");
      faceSel.appendChild(o);
    });
  };
  dieSel.onchange = fillFaces;
  fillFaces();
  const btn = document.createElement("button");
  btn.className = "action-btn";
  btn.style.borderColor = "#38bdf8";
  btn.style.color = "#38bdf8";
  btn.innerText = "Apply";
  btn.onclick = () => doOverrideFace(parseInt(dieSel.value, 10), parseInt(faceSel.value, 10), source);
  [label, dieSel, faceSel, btn].forEach((el) => wrap.appendChild(el));
  controls.appendChild(wrap);
}
