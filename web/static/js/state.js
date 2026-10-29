/**
 * Rogue Agent — Shared UI & Selection State
 */

export let state = null;
export let selectedCommitments = {};
export let selectedBacklashIndex = 0;
export let selectedBacklashDieId = null;
export let selectedPhreakerDieId = null;
export let patchCashSelected = false;
export let cipherDiscountSelected = false;
export let selectedRerollIndices = new Set();
export let selectedChoiceDeclarations = {};

export function getState() {
  return state;
}

export function getEligibleBacklashDice(player) {
  if (!player) return [];
  const result = [];
  const seen = new Set();
  for (const d of (player.ready_dice || [])) {
    if (!seen.has(d.die_id)) {
      seen.add(d.die_id);
      result.push({ ...d, zone_label: "Ready Zone" });
    }
  }
  for (const d of (player.rolled_pool || [])) {
    if (!d.is_contractor && d.color !== "white" && !seen.has(d.die_id)) {
      seen.add(d.die_id);
      result.push({ ...d, zone_label: "Active Pool" });
    }
  }
  return result;
}

export function sanitizeSelectionState(newState) {
  if (!newState || !newState.players) return;
  const human = newState.players.find((p) => p.is_human) || newState.players[0];
  if (!human) return;
  const caps = newState.action_capabilities || {};

  // 1. Phase 1 reroll / commitment state
  if (newState.phase !== 1 || !human.has_rolled || human.has_committed) {
    selectedRerollIndices.clear();
    selectedCommitments = {};
    for (const k of Object.keys(selectedChoiceDeclarations)) {
      delete selectedChoiceDeclarations[k];
    }
  } else {
    const poolLen = (human.rolled_pool || []).length;
    for (const idx of Array.from(selectedRerollIndices)) {
      if (idx < 0 || idx >= poolLen) {
        selectedRerollIndices.delete(idx);
      }
    }
  }

  // 2. Cipher discount toggle auto-reset when no longer available
  const canAnyCipherBuy = Boolean(
    newState.phase === 3 &&
    caps.can_cipher_buy &&
    Object.values(caps.can_cipher_buy).some(Boolean)
  );
  if (!canAnyCipherBuy) {
    cipherDiscountSelected = false;
  }

  // 3. Patch mode toggle auto-sync
  if (newState.phase === 3) {
    if (patchCashSelected && !caps.can_patch_cash && caps.can_patch_token) {
      patchCashSelected = false;
    } else if (!patchCashSelected && !caps.can_patch_token && caps.can_patch_cash) {
      patchCashSelected = true;
    }
  }

  // 4. Backlash die ID & Phreaker die ID validation
  const eligibleBacklash = getEligibleBacklashDice(human);
  if (!eligibleBacklash.some((d) => d.die_id === selectedBacklashDieId)) {
    selectedBacklashDieId = eligibleBacklash.length > 0 ? eligibleBacklash[0].die_id : null;
  }

  const unpatched = human.unpatched_dice || [];
  if (!unpatched.some((d) => d.die_id === selectedPhreakerDieId)) {
    selectedPhreakerDieId = unpatched.length > 0 ? unpatched[0].die_id : null;
  }
}

export function setState(newState) {
  state = newState;
  sanitizeSelectionState(newState);
}

export function setSelectedBacklashIndex(idx) {
  selectedBacklashIndex = idx;
}

export function setSelectedBacklashDieId(id) {
  selectedBacklashDieId = id !== null && id !== undefined ? Number(id) : null;
}

export function setSelectedPhreakerDieId(id) {
  selectedPhreakerDieId = id !== null && id !== undefined ? Number(id) : null;
}

export function setPatchCashSelected(val) {
  patchCashSelected = Boolean(val);
}

export function setCipherDiscountSelected(val) {
  cipherDiscountSelected = Boolean(val);
}

export function clearSelectedRerolls() {
  selectedRerollIndices.clear();
}

export function resetCommitments() {
  selectedCommitments = {};
}

export function getHumanPlayerId() {
  if (!state || !state.players) return 0;
  const human = state.players.find((p) => p.is_human);
  return human ? human.player_id : (state.active_player_index || 0);
}
