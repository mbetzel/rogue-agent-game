/**
 * Rogue Agent — Software Module Market & Central Supply Board Component
 * Structured faithfully after Print-and-Play Market Board Page 2 (02_Central_Game_Boards.pdf)
 */

import { state, cipherDiscountSelected } from "../state.js";
import { doBuy } from "../api.js";

const MARKET_BASE_SPECS = {
  red: {
    title: "RED // FINSEC",
    symbol: "◆",
    baseCost: 4,
    baseVp: "3 VP",
    row1: "⚀ 1 Red Shield | ⚁-⚃ +$2",
    row2: "⚄ 🔒 Glitch | ⚅ ★ Variant",
    warning: null,
  },
  blue: {
    title: "BLUE // FIREWALL",
    symbol: "●",
    baseCost: 5,
    baseVp: "4 VP",
    row1: "⚀ 1 Blue Shield | ⚁ +1 🔧 | ⚂ +$1",
    row2: "⚃ 1 Blue / 1 🔧 | ⚄ 🔒 Glitch | ⚅ ★ Variant",
    warning: null,
  },
  green: {
    title: "GREEN // ANTIVIRUS",
    symbol: "▲",
    baseCost: 4,
    baseVp: "3 VP",
    row1: "⚀ 1 Green Shield | ⚁ +1 🔧 | ⚂ +2 🔧",
    row2: "⚃ 1 🔧 / +$1 | ⚄ 🔒 Glitch | ⚅ ★ Variant",
    warning: null,
  },
  yellow: {
    title: "YELLOW // COMM.",
    symbol: "⬡",
    baseCost: 5,
    baseVp: "4 VP",
    row1: "⚀ +$3 | ⚁-⚂ +$2",
    row2: "⚃ +$1 & +1 🔧 | ⚄ 🔒 Glitch | ⚅ ★ Variant",
    warning: "EXPOSURE: Green hits Yellow 1st!",
  },
  purple: {
    title: "PURPLE // BLK-HAT",
    symbol: "▼",
    baseCost: 4,
    baseVp: "3 VP",
    row1: "⚀-⚁ Block 1 Any | ⚂ +$2",
    row2: "⚃ +$1 & +1 🔧 | ⚄ 🔒 Glitch | ⚅ ★ Variant",
    warning: null,
  },
};

export function renderMarket() {
  if (!state || !state.market) return;

  const container = document.getElementById("marketContainer");
  if (!container) return;
  container.innerHTML = "";

  const order = ["red", "blue", "green", "yellow", "purple"];

  // Outer Market Board Wrapper
  const boardEl = document.createElement("div");
  boardEl.className = "pnp-market-board";

  // 1. Board Header
  boardEl.innerHTML = `
    <div class="market-board-header">
      <div class="market-board-header-left">
        <span class="m-board-title">SOFTWARE MODULE MARKET & CENTRAL SUPPLY</span>
        <span class="m-board-subtitle">PNP COMPANION BOARD</span>
      </div>
      <div class="market-board-header-right">
        <span>DEAL 1 VARIANT (★) CARD PER COLOR | STACK 2× PLAYERS DICE</span>
      </div>
    </div>
  `;

  // 2. White Contractor Supply Strip (Top of Market)
  const contractorPoolEl = document.createElement("div");
  contractorPoolEl.className = "contractor-pool-panel";
  contractorPoolEl.innerHTML = `
    <div class="contractor-hdr-row">
      <div class="contractor-title">
        <span class="contractor-symbol">◌</span>
        <span>WHITE CONTRACTOR SUPPLY (12 DICE TOTAL — ${state.contractor_supply || 0} IN POOL)</span>
      </div>
      <div class="contractor-rules-note">
        Phase 1 Staffing | Max 3/Round | Returns to supply after Phase 2 | Never wears to Unpatched
      </div>
    </div>
    <div class="contractor-cost-tiers">
      <div class="contractor-tier-box">
        <span class="tier-lbl">1ST HIRE</span>
        <span class="tier-cost">$1</span>
      </div>
      <div class="contractor-tier-box">
        <span class="tier-lbl">2ND HIRE</span>
        <span class="tier-cost">$2</span>
      </div>
      <div class="contractor-tier-box">
        <span class="tier-lbl">3RD HIRE</span>
        <span class="tier-cost">$3</span>
      </div>
      <div class="contractor-faces-summary">
        <strong>Faces:</strong> ⚀⚁⚂ Block 1 Any &nbsp;|&nbsp; ⚃ +$1 &nbsp;|&nbsp; ⚄⚅ 🔒 Glitch (0 output)
      </div>
    </div>
  `;
  boardEl.appendChild(contractorPoolEl);

  // 3. 5 Horizontal / Grid Market Slots
  const slotsGrid = document.createElement("div");
  slotsGrid.className = "market-slots-grid";

  for (const color of order) {
    const item = state.market[color];
    if (!item) continue;

    const spec = MARKET_BASE_SPECS[color];
    const baseCanBuy = Boolean(state.action_capabilities && state.action_capabilities.can_buy && state.action_capabilities.can_buy[color]);
    const cipherCanBuy = Boolean(state.action_capabilities && state.action_capabilities.can_cipher_buy && state.action_capabilities.can_cipher_buy[color]);
    const canBuy = cipherDiscountSelected ? cipherCanBuy : baseCanBuy;
    const effectiveCost = cipherDiscountSelected ? Math.max(0, item.cost - 2) : item.cost;

    const slotCard = document.createElement("div");
    slotCard.className = `market-module-card ${color}-module-card`;

    slotCard.innerHTML = `
      <!-- Color Header Strip -->
      <div class="module-card-header ${color}">
        <div class="module-title-row">
          <span class="module-symbol">${spec.symbol}</span>
          <span class="module-title">${spec.title}</span>
        </div>
        <div class="module-stock-tag">${item.stock} IN STOCK</div>
      </div>

      <!-- Cost / VP Strip -->
      <div class="module-cost-vp-row">
        <span class="module-cost-lbl">COST: <strong>$${effectiveCost}</strong> ${cipherDiscountSelected ? '<span class="cipher-discount-tag">(-$2 ARB)</span>' : ''}</span>
        <span class="module-vp-lbl">${spec.baseVp}</span>
      </div>

      <!-- Base Faces Summary -->
      <div class="module-base-faces-box">
        <div class="face-row-text">${spec.row1}</div>
        <div class="face-row-text">${spec.row2}</div>
        ${spec.warning ? `<div class="face-warning-text">${spec.warning}</div>` : ''}
      </div>

      <!-- Variant (★) Card Slot Box -->
      <div class="variant-card-slot">
        <div class="variant-card-slot-header">
          <span class="variant-star-icon">★</span>
          <span class="variant-header-title">${color.toUpperCase()} VARIANT CARD</span>
        </div>
        ${item.variant ? `
          <div class="variant-card-body">
            <div class="variant-card-code-row">
              <span class="variant-code-pill">${item.variant.code}</span>
              <strong class="variant-card-name">${item.variant.name}</strong>
            </div>
            <div class="variant-card-desc">${item.variant.description}</div>
          </div>
        ` : `
          <div class="variant-placeholder">Standard Module (No Active Variant)</div>
        `}
      </div>

      <!-- Module Buy Action -->
      <div class="module-buy-footer">
        <button class="action-btn btn-accent module-buy-btn" ${canBuy ? "" : "disabled"}>
          Buy ($${effectiveCost}) ${cipherDiscountSelected ? '[⚡ Cipher]' : ''}
        </button>
      </div>
    `;

    const buyBtn = slotCard.querySelector("button");
    buyBtn.onclick = () => doBuy(color, cipherDiscountSelected);

    slotsGrid.appendChild(slotCard);
  }

  boardEl.appendChild(slotsGrid);
  container.appendChild(boardEl);
}
