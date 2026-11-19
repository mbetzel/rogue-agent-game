/**
 * Rogue Agent — API Client & Action Handlers
 */

import {
  state,
  setState,
  resetChoiceDeclarations,
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
  enableCorporateAsymmetry = true,
  rulesVersion = null
) {
  const payload = {
    num_players: numPlayers,
    randomize_cards: Boolean(randomizeCards),
    enable_corporate_asymmetry: Boolean(enableCorporateAsymmetry),
  };
  if (rulesVersion) payload.rules_version = rulesVersion;
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
    resetChoiceDeclarations();
    notifyRender();
    const modal = document.getElementById("newGameModal");
    if (modal) modal.classList.remove("open");
  }
}

export async function doCapitalInjection() {
  const newState = await apiCall("/api/game/action/capital_injection", "POST", {
    player_id: getHumanPlayerId(),
  });
  if (newState) {
    setState(newState);
    notifyRender();
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

export async function doRoll() {
  const newState = await apiCall("/api/game/action/roll", "POST", { player_id: getHumanPlayerId() });
  if (newState) {
    setState(newState);
    resetChoiceDeclarations();
    clearSelectedRerolls();
    notifyRender();
  }
}

// Phase 1: Brute-Force Bypass ("helix") / Arbitrary Code Execution ("prodigy") / Release Track Level 4 ("release_l4")
export async function doOverrideFace(dieIndex, faceIndex, source = "helix") {
  const newState = await apiCall("/api/game/action/override_face", "POST", {
    player_id: getHumanPlayerId(),
    die_index: dieIndex,
    face_index: faceIndex,
    source: source,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

// Phase 1 Step 4: Lock-in & Assign Dice (+1 Vulnerability per ⚠ on the final faces)
export async function doLockIn() {
  const newState = await apiCall("/api/game/action/lock_in", "POST", {
    player_id: getHumanPlayerId(),
    choice_declarations: selectedChoiceDeclarations,
  });
  if (newState) {
    setState(newState);
    resetChoiceDeclarations();
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

// Phase 4: Attack Resolution choices (nothing is blocked): Aegis Baffle Echo, DTO Slush Fund, Target Lock choices
export async function doConfirmAttacks(choices = {}) {
  const payload = { player_id: getHumanPlayerId() };
  if (choices.aegisColor) payload.aegis_color = choices.aegisColor;
  if (choices.aegisGreen) payload.aegis_green = choices.aegisGreen;
  if (choices.useSlushFund !== null && choices.useSlushFund !== undefined) {
    payload.use_slush_fund = !!choices.useSlushFund;
  }
  if (Array.isArray(choices.signatureGreenTracks)) payload.signature_green_tracks = choices.signatureGreenTracks;
  if (choices.signatureRedRecipient !== null && choices.signatureRedRecipient !== undefined) {
    payload.signature_red_recipient = choices.signatureRedRecipient;
  }
  const newState = await apiCall("/api/game/action/confirm_attacks", "POST", payload);
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

// Phase 6: CI/CD Pipeline Shift (Scanned Graduation <= Release Bandwidth; Magnetic Splice target)
export async function doChooseGraduates(graduateDieIds = [], spliceDieId = null) {
  const payload = {
    player_id: getHumanPlayerId(),
    graduate_die_ids: graduateDieIds,
  };
  if (spliceDieId !== null && spliceDieId !== undefined) {
    payload.splice_die_id = spliceDieId;
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

export async function doResolveBreakthrough(accept, grayDieId, color) {
  const newState = await apiCall("/api/game/action/breakthrough", "POST", {
    player_id: getHumanPlayerId(),
    accept: !!accept,
    gray_die_id: grayDieId,
    color: color,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

// Phase 5: Pen Test Track (-1 Vulnerability per step for research, up to the level's limit per turn)
export async function doPenTest(steps = 1) {
  const newState = await apiCall("/api/game/action/pen_test", "POST", {
    player_id: getHumanPlayerId(),
    steps: steps,
  });
  if (newState) {
    setState(newState);
    notifyRender();
  }
}

// Phase 5: Public Relations Track: +1 Market Share for cash
export async function doRegainMarketShare() {
  const newState = await apiCall("/api/game/action/regain_market_share", "POST", {
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
