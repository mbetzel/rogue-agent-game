/**
 * Rogue Agent — Market & Modules Component
 */

import { state, cipherDiscountSelected } from "../state.js";
import { doBuy } from "../api.js";

export function renderMarket() {
  if (!state || !state.market) return;

  const container = document.getElementById("marketContainer");
  if (!container) return;
  container.innerHTML = "";

  const order = ["red", "blue", "green", "yellow", "purple"];
  for (const color of order) {
    const item = state.market[color];
    if (!item) continue;

    const el = document.createElement("div");
    el.className = "market-item";

    const baseCanBuy = Boolean(state.action_capabilities && state.action_capabilities.can_buy && state.action_capabilities.can_buy[color]);
    const cipherCanBuy = Boolean(state.action_capabilities && state.action_capabilities.can_cipher_buy && state.action_capabilities.can_cipher_buy[color]);
    const canBuy = cipherDiscountSelected ? cipherCanBuy : baseCanBuy;
    const effectiveCost = cipherDiscountSelected ? Math.max(0, item.cost - 2) : item.cost;

    el.innerHTML = `
      <div class="market-die-info">
        <div class="market-die-title" style="color: var(--color-${color});">
          ${color.toUpperCase()} DIE (${item.stock} left)
        </div>
        <div class="market-die-meta">
          Cost: $${effectiveCost} ${cipherDiscountSelected ? '<span style="color: #c084fc; font-weight: 700;">(-$2 Cipher Arbitrage)</span>' : ''} | Value: ${item.vp} VP
        </div>
        <div class="market-variant-card">
          ${item.variant ? `<span class="variant-code-badge">${item.variant.code}</span> <strong>${item.variant.name}</strong>: ${item.variant.description}` : '★ Standard'}
        </div>
      </div>
      <div>
        <button class="action-btn btn-accent" ${canBuy ? "" : "disabled"}>
          Buy ($${effectiveCost}) ${cipherDiscountSelected ? '[⚡ Cipher]' : ''}
        </button>
      </div>
    `;

    const btn = el.querySelector("button");
    btn.onclick = () => doBuy(color, cipherDiscountSelected);

    container.appendChild(el);
  }
}
