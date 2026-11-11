/**
 * Rogue Agent — Software Module Market & Central Supply Board Component
 * Structured faithfully after Print-and-Play Market Board Page 2 (02_Central_Game_Boards.pdf)
 */

import { state, cipherDiscountSelected } from "../state.js";
import { doBuy } from "../api.js";

const MARKET_BASE_SPECS = {
  red: { title: "RED // MARKETING", symbol: "◆" },
  blue: { title: "BLUE // FIREWALL", symbol: "●" },
  green: { title: "GREEN // ANTIVIRUS", symbol: "▲" },
  yellow: { title: "YELLOW // COMM.", symbol: "⬡" },
  purple: { title: "PURPLE // BLK-HAT", symbol: "▼" },
};

const DIE_GLYPHS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];

/** Two text rows (faces 1-3, faces 4-6) from the printed faces the server sends for the active ruleset. */
function faceRows(color) {
  const names = (state && state.die_faces && state.die_faces[color]) || [];
  const fmt = (i) => `${DIE_GLYPHS[i]} ${names[i] === "Secret" ? "Secret face" : names[i]}`;
  if (names.length < 6) return ["", ""];
  return [[0, 1, 2].map(fmt).join(" | "), [3, 4, 5].map(fmt).join(" | ")];
}

function secretNote(color) {
  const y = (state && state.secret_yields) || {};
  if (!state || !state.is_secret_faces || color === "yellow") return null;
  if (color === "red") return `Secret face: +${y.red} Corporate Secrets when it leaves the Processing Box`;
  if (color === "blue") {
    if (y.blue_block && y.blue_block > 0) {
      return `Secret face: +${y.blue_base} (+${y.blue_block} if you blocked a Blue cube, +${y.blue_grid} at Defense Grid Level 3+; max ${y.blue_cap})`;
    }
    return `Secret face: +${y.blue_base} Corporate Secrets (+${y.blue_grid} at Defense Grid Level 3+; max ${y.blue_cap})`;
  }
  if (color === "green") {
    if (y.green_glitch_penalty) {
      return `Secret face: ${y.green_base} minus your Glitched Shield Slots`;
    }
    return `Secret face: +${y.green_base} Corporate Secrets (cleans 1 Glitched Shield Slot)`;
  }
  return `Secret face: +${y.purple} Corporate Secret`;
}

export function renderMarket() {
  if (!state || !state.market) return;

  const container = document.getElementById("marketContainer");
  if (!container) return;
  container.innerHTML = "";

  const order = ["red", "blue", "green", "yellow"];

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
        Phase 1 Staffing | Max 3/Round | Pays income in Phase 3 | Returns to supply after Phase 4 | Never enters the Processing Box
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
        <strong>Faces:</strong> ⚀⚁⚂ Block 1 Any &nbsp;|&nbsp; ⚃ +$1 &nbsp;|&nbsp; ⚄⚅ ⚠️ Glitch (0 output, discarded to supply; the only Glitch faces)
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

    const spec = { ...MARKET_BASE_SPECS[color] };
    [spec.row1, spec.row2] = faceRows(color);
    spec.warning = secretNote(color);
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

      <!-- Cost / Market Strip -->
      <div class="module-cost-vp-row">
        <span class="module-cost-lbl">COST: <strong>$${effectiveCost}</strong> ${cipherDiscountSelected ? '<span class="cipher-discount-tag">(-$2 ARB)</span>' : ''}</span>
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
          ${item.variant && item.variant.cost ? `<span class="variant-cost-badge" style="margin-left: auto; background: rgba(0,0,0,0.4); padding: 1px 6px; border-radius: 4px; font-weight: bold; color: #4ade80;">$${item.variant.cost}</span>` : ''}
        </div>
        ${item.variant ? `
          <div class="variant-card-body">
            <div class="variant-card-code-row">
              <span class="variant-code-pill">${item.variant.printed_code || item.variant.code}</span>
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
