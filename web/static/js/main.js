/**
 * Rogue Agent — Main Client Entry Point & Application Coordinator
 */

import { state, activeBoardView, setActiveBoardView } from "./state.js";
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
  doSystemReboot,
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

export function setBoardView(view) {
  setActiveBoardView(view);
  const workspace = document.getElementById("tabletopWorkspace");
  if (workspace) {
    workspace.dataset.view = view;
  }
  const buttons = document.querySelectorAll(".nav-view-btn");
  buttons.forEach((b) => b.classList.remove("active"));
  const viewId = `viewBtn${view.charAt(0).toUpperCase() + view.slice(1)}`;
  const activeBtn = document.getElementById(viewId);
  if (activeBtn) activeBtn.classList.add("active");
}

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
window.doSystemReboot = doSystemReboot;
window.doAcoustic = doAcoustic;
window.doSpook = doSpook;
window.doStarAction = doStarAction;
window.doEndTurn = doEndTurn;
window.setBoardView = setBoardView;

// Initial Boot
if (document.readyState === "loading") {
  window.addEventListener("DOMContentLoaded", () => {
    refreshState();
  });
} else {
  refreshState();
}
