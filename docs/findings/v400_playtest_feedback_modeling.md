# Pre-SDLC Modeling & Plan of Record: Gameplay Balance & Feedback Review (`v0.40.0` Candidate)

**Date:** 2026-11-12  
**Author:** Game Designer Subagent  
**Context:** Two-Player Playtest Feedback Session (DTO + Prodigy vs Omnidyne + Phreaker; Script Kiddie -> Polymorphic Worm -> Corrupted Kernel; Ad Campaign, Deep R&D Vault, Self-Healing Kernel, Cloud Monopoly)  
**Status:** Plan of Record Locked & Signed Off by User  

---

## 1. Executive Summary & Core Design Objectives

The two-player playtest session revealed five interconnected balance and pacing friction points:
1. **The Cash/Research Economic Divergence:** Research had continuous sinks (tracks + PR regain), while cash saturated quickly due to dice purchase limits (max 2/turn) and pipeline capacity caps.
2. **Phase Order Latency:** Upgrading hardware in Phase 6 created a full-round delay before players experienced the benefit in Phase 5.
3. **Absence of Early Pipeline Backpressure:** Starting Triage Bandwidth at 2 allowed early Secret faces to pass through immediately with zero queueing.
4. **Purchased Dice Surges:** Bypassing the Scanned Box allowed players to immediately inflate their rolling pool without Release Bandwidth investment.
5. **Green Cube / Glitch Saturation:** The small shield pool (2–4 slots, 1 pre-glitched) easily collapsed into permanent defense blackout under circulating Green cubes.

This Plan of Record establishes the canonical design solution across three cohesive batches, preparing the codebase for the full multi-agent SDLC.

---

## 2. Batch 1: CI/CD Pipeline Architecture & Flow

### 2.1 Swapping Phase 5 and Phase 6
* **Previous Sequence:** Phase 1 (Roll & Deploy) $\to$ Phase 2 (Compiler Drop) $\to$ Phase 3 (Income) $\to$ Phase 4 (Attack Resolution) $\to$ Phase 5 (CI/CD Pipeline Shift) $\to$ Phase 6 (Operations).
* **New Canonical Sequence:**
  1. **Phase 1: Roll & Deploy (Simultaneous)**
  2. **Phase 2: Compiler Drop & Corruption (Simultaneous)**
  3. **Phase 3: Income (Simultaneous)**
  4. **Phase 4: Attack Resolution (Simultaneous)**
  5. **Phase 5: Operations (Operations Turns, Clockwise)**
  6. **Phase 6: CI/CD Pipeline Shift (Simultaneous)**
* **Mechanical & Psychological Impact:**
  * **Immediate Hardware Gratification:** When a player spends research in Phase 5 Operations to upgrade Triage or Release Bandwidth, the increased throughput applies *immediately* during Phase 6 Pipeline Shift in that same round.
  * **End-of-Round Market Leader Bonus:** In Phase 6, Conveyor Triage moves dice out of the Processing Box, banking Secrets. Any Red Secret banked fires the Market Leader Bonus check as the natural climax of the round, evaluating final Market Share positions established during Phase 5 Operations.

### 2.2 Purchased Dice Entering Scanned Box
* **New Rule:** Newly purchased Central Market colored dice (`$4–$6`) are placed into the **Scanned Box** (Static Analysis / Code Review / Verification), rather than directly into Ready for Release.
* **Pipeline Interaction:**
  * During Phase 5 Operations, the purchased die enters Scanned.
  * In Phase 6 Pipeline Shift (Scanned Graduation), the player may graduate up to `release_bandwidth` dice to Ready for Release.
  * If the player has spare Release Bandwidth, the new die immediately joins next round's rolling pool.
  * If Release Bandwidth is saturated (e.g. 4 dice returning from In Production at Bandwidth 4), the player faces a meaningful tactical choice:
    1. Spend $1\text{ 🔬}$ in Phase 5 Operations to upgrade Release Bandwidth from 4 to 5.
    2. Leave an older die (e.g., a Gray starter) behind in Scanned to promote the new die.
    3. Hold the new die in Scanned until the next cycle.
  * *Result:* Eliminates sudden rolling pool inflation and makes Release Track progression essential for engine-building.

### 2.3 Triage Track Recalibration & Level 4 Capstone
* **Empirical Baseline:** In simulation telemetry across 5,390 player-rounds:
  * Mean Secrets rolled naturally per player per round: **`0.30`** (approx. 1 Secret every 3.3 rounds).
  * Targeted Secret fishing (holding/rerolling with 2 dice): **`0.84`** Secrets/round; double-Secret occurs in **`17.7%`** of rounds.
  * Targeted Secret fishing with 3 dice: **`1.26`** Secrets/round; double-or-triple Secret occurs in **`38.3%`** of rounds.
  * Under previous Bandwidth 2, **`99.9%`** of all rolled Secrets passed through immediately without queueing.
* **New Triage Track Architecture:**
  * **Level 0 (Baseline):** **Triage Bandwidth `1`**. A single Secret passes through normally; rolling two Secrets (or consecutive Secrets) immediately triggers FIFO backpressure, holding the second die in Processing until the next round.
  * **Level 1 (Breakthrough):** Gain `1` Gray Legacy die.
  * **Level 2:** Gain **`+1 Corporate Secret`** (placeholder milestone while track balance is finalized).
  * **Level 3 (Breakthrough):** Pay `$3`: replace `1` Gray Legacy die with any available Central Market colored die.
  * **Level 4 (Capstone):** **Triage Bandwidth `2`**!
* **Design Justification:** For the vast majority of the game (Levels 0–3), players operate strictly at Bandwidth 1. Reaching Bandwidth 2 is reserved for the Level 4 Capstone, transforming it into an aspirational milestone that empowers heavy Secrets-hunting engines to process 2 Secrets per round.

---

## 3. Batch 2: The Dual Economy ($ vs 🔬) & Public Relations Track

### 3.1 Cash as the Operational Resource for Market Share
* **Mechanical Shift:** Money (`$`) becomes the operational fuel for regaining Market Share in Phase 5 Operations. Research tokens (`🔬`) are no longer spent directly on Market Share.
* **Thematic Alignment:** Corporate capital directly funds advertising blitzes, brand protection campaigns, enterprise lobbying, and PR retainers. Research remains focused on internal software engineering, defense grids, and pipeline hardware.
* **Conversion Rate:** Regaining Market Share costs **`$3` per `+1` Market Share**.

### 3.2 Public Relations Track Progression
The Public Relations Track dictates the player's per-turn **Marketing Bandwidth** (how much Market Share can be purchased each round):
* **Level 0–1:** Regain up to **`1` Market Share** per turn (cost: `$3`).
* **Level 1 Breakthrough:** Gain **`+$3` Liquid Cash** (immediately pays for 1 Market Share regain!).
* **Level 2–3:** Regain up to **`2` Market Share** per turn (cost: `$3` each, max `$6`).
* **Level 3 Breakthrough:** Unlock 2nd **Purple Proprietary Specialist Die** from Personal Reserve.
* **Level 4 (Capstone):** Regain up to **`3` Market Share** per turn (cost: `$3` each, max `$9`).

### 3.3 Hardware Track Step Cost Re-calibration
* In `v0.39.0`, step costs were reduced to `(1, 1, 2, 2) 🔬` ($6\text{ 🔬}$ total) because PR regains absorbed $5–$7\text{ 🔬}$ per game.
* Shifting PR regains to Cash frees up $5–$7\text{ 🔬}$. To protect the anti-snowball guardrail ($< 10\%$ maxing 2+ tracks), track step costs are re-calibrated:
  * **Step Costs:** **`(1, 2, 2, 3) 🔬`** ($8\text{ 🔬}$ per track across all 4 tracks).
  * Level 1 remains cheap ($1\text{ 🔬}$) to ensure immediate access to early Breakthroughs.
  * Higher tiers require deliberate specialization ($2\text{ 🔬}$ for L2/L3, $3\text{ 🔬}$ for L4).
  * Retain the strict **`max 2 hardware upgrades per turn`** limit from Phase 55.

### 3.4 Card Synergies & Cash Sinks
* ***R2 — Ad Campaign (`$4`):* Retains its text: *"Pay `$2` during Operations to gain `+1` Market Share"*. It acts as a permanent `$2` discount coupon (saving `$1` over standard `$3` PR) and bypasses the player's PR track turn limit.
* ***Y1 — Algorithmic Trading (`$6`):* Provides alternative cash conversion (Pay `$2` $\to$ `+1` Corporate Secret).
* ***B2 — Deep R&D Vault (`$6`):* Provides alternative cash conversion (Pay `$4` $\to$ `+1` Corporate Secret).

---

## 4. Batch 3: Threat Composition & Version Profiles

### 4.1 Global Green Cube Cap
* **The Problem:** Defense Capacity maxes out at 4 (starts at 2, with 1 pre-glitched). Circulating 6+ Green cubes through the recycling tower causes irreversible defense degradation, forcing clean-shield capacity to 0 and preventing players from blocking Red or Blue attacks.
* **The Rule:** Hard-cap total Green cubes in the game at **5–6 cubes maximum** across the entire setup and all Version cards combined. Green functions as an attrition hazard (eroding 1–2 shields), never a permanent defense blackout.

### 4.2 Asymmetric SETEC Threat Profiles
Version cards are structured into distinct thematic and operational threat vectors:
1. **Branch Alpha: Economic Extortion (Red-Heavy)**
   * Threat Vector: Market Manipulation, liquidity draining, corporate fines.
   * Cube Mix: Heavy Red cube additions (`+1R`, `+2R`), direct cash fines (`-$2`, `-$3`).
   * Strategic Test: Pressures Market Share reserves and liquidity; rewards high cash production and Public Relations investment.
2. **Branch Beta: Data Exfiltration (Blue-Heavy)**
   * Threat Vector: Spyware, backdoors, intellectual property theft.
   * Cube Mix: Heavy Blue cube additions (`+1B`, `+2B`), direct Corporate Secret loss.
   * Strategic Test: Pressures victory point health and threatens Patient Zero elimination; rewards raw Defense Grid capacity, shield consistency, and DTO/Aegis defensive overrides.
3. **Branch Gamma: Structural Sabotage (Balanced / Green Hazard)**
   * Threat Vector: Logic bombs, corrupted dependencies, hardware wear.
   * Cube Mix: Houses the 5–6 Green cubes alongside occasional direct dice glitches.
   * Strategic Test: Pressures pipeline throughput and shield maintenance without overwhelming defense grids.

---

## 5. Multi-Agent SDLC Hand-off Roadmap

Following approval of this modeling plan, work proceeds via the standard SDLC pipeline:
1. **Phase 56.1 (Technical Architecture Spec):** `principal-engineer` authors formal architectural specification (`docs/specs/v400_gameplay_balance_spec.md`) covering state invariants, phase execution re-sequencing, and controller contracts.
2. **Phase 56.2 (Engine Implementation):** `senior-engineer` updates simulation engine (`sim/engine/`), bots (`sim/bots/`), and test suites.
3. **Phase 56.3 (Code Review Gate):** `staff-engineer` audits changes for regression safety, spec fidelity, and invariant compliance.
4. **Phase 56.4 (Monte Carlo Sweep & Telemetry):** `product-owner` executes 3,600-game validation sweep across 2P, 3P, and 4P pods.
5. **Phase 56.5 (Balance Assessment):** `game-designer` assesses macro pacing, tri-modal end trigger distribution, and company equity.
6. **Phase 56.6 (Phase B Documentation & Asset Sync):** Sync `RULES.md`, `RULES_APPENDIX.md`, `GLOSSARY.md`, `pnp/generate_pnp.py`, and `web/`.
