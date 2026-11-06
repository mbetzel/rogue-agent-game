/**
 * Rogue Agent — API Client & Action Handlers
 */

import {
  state,
  setState,
  selectedCommitments,
  resetCommitments,
  selectedBacklashIndex,
  selectedBacklashDieId,
  selectedPhreakerDieId,
  selectedRerollIndices,
  clearSelectedRerolls,
  selectedChoiceDeclarations,
  setCipherDiscountSelected,
  getHumanPlayerId,
} from "./state.js";

let renderAppCallback = null;
let isActionInFlight = false;

export function setRenderAppCallback(fn) {
  renderAppCallback = fn;
}

function notifyRender() {
  if (typeof renderAppCallback === "function") {
    renderAppCallback();
  }
}

export async function apiCall(endpoint, method = "GET", body = null) {
  if (method === "POST" && isActionInFlight) {
    return null;
  }
  if (method === "POST") {
    isActionInFlight = true;
  }

  const options = {
    method: method,
    cache: "no-store",
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
      if (method === "POST") {
        try {
          const syncRes = await fetch("/api/game/state", { cache: "no-store" });
          const syncData = await syncRes.json();
          if (syncRes.ok && syncData.success && syncData.state) {
            setState(syncData.state);
            notifyRender();
          }
        } catch (_syncErr) {
          // ignore secondary sync failure
        }
      }
      return null;
    }
    return data.state;
  } catch (err) {
    console.error("API error:", err);
    alert(`Network Error: ${err.message}`);
    return null;
  } finally {
    if (method === "POST") {
      isActionInFlight = false;
    }
  }
}

export async function refreshState() {
  const newState = await apiCall("/api/game/state");
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function startNewGame(
  numPlayers = 4,
  customPlayers = null,
  seed = null,
  randomizeCards = true,
  company = null,
  enableCorporateAsymmetry = true
) {
  const payload = {
    num_players: numPlayers,
    randomize_cards: Boolean(randomizeCards),
    enable_corporate_asymmetry: Boolean(enableCorporateAsymmetry),
  };
  if (customPlayers) {
    payload.players = customPlayers;
    if (company && company !== "RANDOM" && payload.players.length > 0) {
      payload.players[0].company = payload.players[0].company || company;
    }
  } else if (company && company !== "RANDOM") {
    payload.players = [
      {
        is_human: true,
        name: "Player 1",
        company: company,
      },
    ];
  }
  if (seed !== null && seed !== "") payload.seed = parseInt(seed, 10);

  const newState = await apiCall("/api/game/new", "POST", payload);
  if (newState) {
    setState(newState);
    resetCommitments();
    notifyRender();
    const modal = document.getElementById("newGameModal");
    if (modal) modal.classList.remove("open");
  }
}

export async function doHireContractors(count = 1, useOperator = false, buyThird = false) {
  const newState = await apiCall("/api/game/action/hire_contractors", "POST", {
    player_id: getHumanPlayerId(),
    count: count,
    use_operator_ability: Boolean(useOperator),
    buy_third_die: Boolean(buyThird),
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doReroll(useProdigy = false) {
  const indices = Array.from(selectedRerollIndices);
  if (indices.length === 0) return;
  const newState = await apiCall("/api/game/action/reroll", "POST", {
    player_id: getHumanPlayerId(),
    reroll_indices: indices,
    use_prodigy_ability: Boolean(useProdigy),
  });
  if (newState) {
    setState(newState);
    clearSelectedRerolls();
    notifyRender();
  }
}

export async function doDebugUnlock(dieIndex) {
  console.warn("Debug unlocks deprecated in v0.23.0.");
}

export async function doRoll() {
  const newState = await apiCall("/api/game/action/roll", "POST", { player_id: getHumanPlayerId() });
  if (newState) {
    setState(newState);
    resetCommitments();
    clearSelectedRerolls();
    notifyRender();
  }
}

export async function doHotfix(dieIndex) {
  const newState = await apiCall("/api/game/action/hotfix", "POST", { player_id: getHumanPlayerId(), die_index: dieIndex });
  if (newState) {
    setState(newState);
    delete selectedCommitments[dieIndex];
    notifyRender();
  }
}

export async function doCommit() {
  const newState = await apiCall("/api/game/action/commit", "POST", {
    player_id: getHumanPlayerId(),
    commitments: selectedCommitments,
    choice_declarations: selectedChoiceDeclarations,
  });
  if (newState) {
    setState(newState);
    resetCommitments();
    for (const key of Object.keys(selectedChoiceDeclarations)) {
      delete selectedChoiceDeclarations[key];
    }
    notifyRender();
  }
}

export async function doCompile() {
  const newState = await apiCall("/api/game/action/compile", "POST", {});
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

// Phase 3: Income (optional Spook Burn Notice / Phreaker Jumper Diagnostics targets)
export async function doConfirmIncome(spookBurnDieId = null, phreakerDieId = null) {
  const payload = { player_id: getHumanPlayerId() };
  if (spookBurnDieId !== null && spookBurnDieId !== undefined) {
    payload.spook_burn_die_id = spookBurnDieId;
  }
  if (phreakerDieId !== null && phreakerDieId !== undefined) {
    payload.phreaker_die_id = phreakerDieId;
  }
  const newState = await apiCall("/api/game/action/confirm_income", "POST", payload);
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

// Phase 4: Attack Resolution (Generic Any shield allocation, Green Malware targets, Aegis color)
export async function doConfirmAttacks(glitchDieIds = [], anyShieldAllocations = null, aegisColor = null) {
  const payload = {
    player_id: getHumanPlayerId(),
    glitch_die_ids: glitchDieIds,
  };
  if (anyShieldAllocations !== null && anyShieldAllocations !== undefined) {
    payload.any_shield_allocations = anyShieldAllocations;
  }
  if (aegisColor) {
    payload.aegis_color = aegisColor;
  }
  const newState = await apiCall("/api/game/action/confirm_attacks", "POST", payload);
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

// Phase 5: CI/CD Pipeline Shift (Scanned Graduation <= Release Bandwidth; Hotfix / Splice targets)
export async function doChooseGraduates(graduateDieIds = [], spliceDieId = null, hotfixDieId = null) {
  const payload = {
    player_id: getHumanPlayerId(),
    graduate_die_ids: graduateDieIds,
  };
  if (spliceDieId !== null && spliceDieId !== undefined) {
    payload.splice_die_id = spliceDieId;
  }
  if (hotfixDieId !== null && hotfixDieId !== undefined) {
    payload.hotfix_die_id = hotfixDieId;
  }
  const newState = await apiCall("/api/game/action/choose_graduates", "POST", payload);
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doBuy(color, useCipher = false) {
  const newState = await apiCall("/api/game/action/buy", "POST", {
    player_id: getHumanPlayerId(),
    color: color,
    use_cipher_ability: Boolean(useCipher),
  });
  if (newState) {
    setState(newState);
    setCipherDiscountSelected(false);
    notifyRender();
  }
}

export async function doPatch(dieIndex, useCash) {
  const newState = await apiCall("/api/game/action/patch", "POST", {
    player_id: getHumanPlayerId(),
    die_index: dieIndex,
    use_cash: useCash,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doDirtyIncome(useCipher = false) {
  const backlashSelect = document.getElementById("dirtyBacklashSelect");
  const dieId = backlashSelect && backlashSelect.value !== ""
    ? parseInt(backlashSelect.value, 10)
    : selectedBacklashDieId;

  const newState = await apiCall("/api/game/action/dirty_income", "POST", {
    player_id: getHumanPlayerId(),
    backlash_die_id: Number.isNaN(dieId) ? null : dieId,
    use_cipher_ability: Boolean(useCipher),
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doPhreaker(count = 1) {
  const phreakerSelect = document.getElementById("phreakerDieSelect");
  const dieId = phreakerSelect && phreakerSelect.value !== ""
    ? parseInt(phreakerSelect.value, 10)
    : selectedPhreakerDieId;

  const newState = await apiCall("/api/game/action/phreaker", "POST", {
    player_id: getHumanPlayerId(),
    count: 1,
    die_id: Number.isNaN(dieId) ? null : dieId,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doAcoustic(color) {
  const newState = await apiCall("/api/game/action/acoustic", "POST", {
    player_id: getHumanPlayerId(),
    color: color,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doSpook(dollars) {
  const newState = await apiCall("/api/game/action/spook", "POST", {
    player_id: getHumanPlayerId(),
    dollars: dollars,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doStarAction(actionType, cubeColor = null) {
  const payload = { player_id: getHumanPlayerId(), action_type: actionType };
  if (cubeColor) payload.cube_color = cubeColor;
  const newState = await apiCall("/api/game/action/star", "POST", payload);
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doFastPatch(dieIds = null, dieIndices = null) {
  console.warn("doFastPatch is deprecated in v0.29.0: fast-patching has been excised.");
}

export async function doUpgradeTrack(trackType) {
  const newState = await apiCall("/api/game/action/upgrade_track", "POST", {
    player_id: getHumanPlayerId(),
    track_type: trackType,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doFilePatent() {
  const newState = await apiCall("/api/game/action/patent", "POST", {
    player_id: getHumanPlayerId(),
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

export async function doEndTurn() {
  const newState = await apiCall("/api/game/action/end_turn", "POST", { player_id: getHumanPlayerId() });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}
