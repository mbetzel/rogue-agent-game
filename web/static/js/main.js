/**
 * Rogue Agent — Main Client Entry Point & Application Coordinator
 */

import { state } from "./state.js";
import {
  setRenderAppCallback,
  refreshState,
  startNewGame,
  doHireContractors,
  doReroll,
  doDebugUnlock,
  doRoll,
  doHotfix,
  doCommit,
  doCompile,
  doBuy,
  doPatch,
  doDirtyIncome,
  doPhreaker,
  doAcoustic,
  doSpook,
  doStarAction,
  doEndTurn,
} from "./api.js";
import {
  openModal,
  closeModal,
  renderGameOverModal,
  renderVersionsModal,
} from "./components/modals.js";
import { renderHeader, renderVersionSlotBadge } from "./components/header.js";
import { renderCompiler } from "./components/compiler.js";
import { renderMarket } from "./components/market.js";
import {
  renderPlayerMats,
  setPlayerMatsRenderCallback,
} from "./components/player_mats.js";
import { renderActionDock } from "./components/action_dock.js";
import { renderEventLog } from "./components/event_log.js";

export function renderApp() {
  if (!state) return;

  renderHeader();
  renderCompiler();
  renderMarket();
  renderPlayerMats();
  renderActionDock();
  renderEventLog();
  renderVersionsModal();

  if (state.game_over && state.final_result) {
    renderGameOverModal();
  }
}

// Wire up render callbacks
setRenderAppCallback(renderApp);
setPlayerMatsRenderCallback(renderApp);

// Expose handlers to window for inline onclick attributes in index.html
window.openModal = openModal;
window.closeModal = closeModal;
window.renderApp = renderApp;
window.refreshState = refreshState;
window.startNewGame = startNewGame;
window.doHireContractors = doHireContractors;
window.doReroll = doReroll;
window.doDebugUnlock = doDebugUnlock;
window.doRoll = doRoll;
window.doHotfix = doHotfix;
window.doCommit = doCommit;
window.doCompile = doCompile;
window.doBuy = doBuy;
window.doPatch = doPatch;
window.doDirtyIncome = doDirtyIncome;
window.doPhreaker = doPhreaker;
window.doAcoustic = doAcoustic;
window.doSpook = doSpook;
window.doStarAction = doStarAction;
window.doEndTurn = doEndTurn;

// Initial Boot
if (document.readyState === "loading") {
  window.addEventListener("DOMContentLoaded", () => {
    refreshState();
  });
} else {
  refreshState();
}
