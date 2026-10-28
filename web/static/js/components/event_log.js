/**
 * Rogue Agent — Event Log Feed Component
 */

import { state } from "../state.js";

export function renderEventLog() {
  if (!state || !state.event_log) return;

  const container = document.getElementById("eventLog");
  if (!container) return;
  container.innerHTML = "";

  state.event_log.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "log-entry";
    item.innerText = entry;
    container.appendChild(item);
  });
}
