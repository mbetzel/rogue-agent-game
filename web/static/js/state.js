/**
 * Rogue Agent — Shared UI & Selection State
 */

export let state = null;
export let selectedCommitments = {};
export let selectedBacklashIndex = 0;
export let patchCashSelected = false;
export let cipherDiscountSelected = false;
export let selectedRerollIndices = new Set();
export let selectedChoiceDeclarations = {};

export function getState() {
  return state;
}

export function setState(newState) {
  state = newState;
}

export function setSelectedBacklashIndex(idx) {
  selectedBacklashIndex = idx;
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
