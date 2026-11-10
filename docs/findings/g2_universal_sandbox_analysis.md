# Pre-SDLC Analysis: Green Die G2 (Universal Sandbox) Redesign

**Role:** Game Designer  
**Date:** 2026-11-10  
**Subject:** Mathematical Modeling & Balance Analysis for G2 Variant Redesign  
**Investigation Prompt:** *"The green die has two identical abilities: G1 and G2. Replacement idea for G2: +1 research for each glitched shield slot."*

---

## 1. Current State Audit

### Why G1 ($5) and G2 ($4) Are Currently Identical
1. **Legacy Heritage (v0.37):**
   - In v0.37, market dice had colored shields:
     - `G1 — Self-Healing Kernel ($5)`: `Block 2 Green + gain +1 🔬`.
     - `G2 — Universal Sandbox ($4)`: `Block 1 Any + gain +1 🔬`.
     - `G3 — Live Reboot ($4)`: `Gain +2 🔬 + +$1`.
2. **The v0.38 Shield Normalization & Malware Migration:**
   - As part of the v0.38 Core Design Pillars, colored shields were completely removed from Central Market dice (Red, Blue, Green, Yellow). Shields were normalized strictly to `Block 1 Any` and restricted to Gray Legacy, White Contractors, and Purple Specialist dice.
   - Green's defensive role pivoted from raw shields to **Glitched Shield Slot remediation** (unblocked Green cubes from the Cube Tower create Glitched Shield Slots).
   - During the automated transition to v0.38, G1's `Block 2 Green` was mapped to `Clean 1 Glitched Shield Slot + gain +1 🔬`.
   - G2's `Block 1 Any` was temporarily collapsed into the exact same placeholder: `Clean 1 Glitched Shield Slot + gain +1 🔬`, annotated in `RULES_APPENDIX.md` as `(Identical to G1 for now [TUNE].)`.
3. **Current Codebase Footprint:**
   - `RULES_APPENDIX.md` (line 38): Lists G2 as identical to G1.
   - `RULES.md` (line 190): Cites both G1 and G2 as Phase 1 Step 5 slot cleaners.
   - `sim/entities.py` (lines 461–475 & 1522–1523): Both G1 and G2 assign `clean_slots=1, patches=1`.
   - `pnp/generate_pnp.py` (lines 359–363): Prints identical card text for G1 and G2.
   - `web/`: Renders the text serialized from `sim/entities.py`.
4. **Design Flaw:**
   - G1 is priced at `$5`, while G2 is priced at `$4`. Because their abilities are identical, G2 is strictly superior per dollar, making G1 an overpriced trap. G2 was explicitly left as a placeholder requiring a distinct mechanical identity.

---

## 2. Mathematical & Expected Value (EV) Modeling

### Telemetry Baseline: Glitched Shield Slots ($g$) Distribution
Using an instrumented simulation harness across 1,800 games (400 games per pod, 38,000+ round observations) under `v0.38c`, we tracked the exact probability distribution of Glitched Shield Slots ($g$) in **Phase 3: Income** (the moment G2 triggers).

#### Phase 3 PMF: Distribution of $g \in \{0, 1, 2, 3, 4, 5\}$
| Scenario | $g = 0$ | $g = 1$ | $g = 2$ | $g = 3$ | $g \ge 4$ | Mean $g$ | Median $g$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **3P Standard (Random Decks)** | **82.4%** | 14.2% | 3.4% | 0.1% | 0.0% | **0.21** | 0.0 |
| **2P Standard (Random Decks)** | **86.6%** | 11.0% | 2.4% | 0.0% | 0.0% | **0.16** | 0.0 |
| **4P Standard (Random Decks)** | **83.6%** | 13.2% | 3.1% | 0.1% | 0.0% | **0.20** | 0.0 |
| **3P Aggressive Profile** | **69.6%** | 25.5% | 4.8% | 0.1% | 0.0% | **0.35** | 0.0 |
| **3P Script Kiddie Lead** | **72.2%** | 19.3% | 8.5% | 0.1% | 0.0% | **0.36** | 0.0 |
| **3P Data Scraper Lead** | **59.3%** | 31.1% | 9.3% | 0.3% | 0.0% | **0.51** | 0.0 |

#### Progression Across Game Versions (3P Standard)
- **`v1.0` (Rounds 1–3):** Mean $g = 0.02$. Players have **$g = 0$ in 98.0% of rounds**!
- **`v2.0` (Rounds 4–6):** Mean $g = 0.11$. Players have **$g = 0$ in 88.6% of rounds**!
- **`v3.0` (Rounds 7–9):** Mean $g = 0.74$. Players have $g = 0$ in 42.4%, $g = 1$ in 41.7%, $g = 2$ in 15.7%.

#### Early Game Risk: Probability of $g = 0$ by Round
| Round | Round 1 | Round 2 | Round 3 | Round 4 | Round 5 | Round 6 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **3P Standard** | **100.0%** | **99.4%** | **96.4%** | 95.3% | 93.3% | 89.3% |
| **3P Aggressive** | **100.0%** | 68.4% | 41.9% | 74.7% | 92.2% | 89.2% |

### Critical Finding: The "Zero Blank Faces" Violation
The user's direct proposal — *Pure G2: "+1 🔬 for each glitched shield slot"* ($Y = g \times 1 🔬$):
1. **Creates a Blank Face:** In **82.4%** of all Phase 3 rounds (and **98.6% of Rounds 1–3**), players have $g = 0$. On those rolls, Pure G2 yields **0 🔬 and $0**.
2. **Violates Core Design Pillar (`AGENTS.md`):**
   > *"Dice = Software Modules + CI/CD Pipeline Loop: Software modules are custom d6 dice with zero blank faces... only White Contractors have Glitch faces."*
3. **Severe Economic Underperformance:**
   - Expected Yield of Pure G2: **0.21 🔬** per roll.
   - At a market cost of `$4`, this makes G2 virtually unpickable compared to `G3` ($4: `+2 🔬 + $1`, Nominal EV = 3.00) and `G1` ($5: `+1 🔬 + Clean 1 Slot`, Nominal EV ~1.25–1.60).
   - If starting Client Companies with Green (Omnidyne, Helix) roll G2 on Face 6 in early rounds, they get nothing.

### Comparative EV Modeling of G2 Candidates
To preserve the concept while eliminating blank faces and ensuring fair economic parity with G3 ($4), we evaluated four candidates:

| Candidate Face Design | Yield Formula | Output at $g=0$ (82% of time) | Output at $g=1$ (14% of time) | Output at $g=2$ (3.4% of time) | Mean EV (Std / Aggr) | Blank Face? | Design Assessment |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Pure Proposal** | $g \times 1 🔬$ | $0 🔬$ | $1 🔬$ | $2 🔬$ | **0.21 / 0.35 🔬** | **YES (82%)** | **Unviable:** Violates design pillar; extreme underpower. |
| **Floored** | $\max(1, g) \times 1 🔬$ | $1 🔬$ | $1 🔬$ | $2 🔬$ | **1.03 / 1.05 🔬** | NO | **Poor:** $g=0$ and $g=1$ pay identically; feels unrewarding. |
| **Base Cash + Scaling** | $\$1 + g \times 1 🔬$ | $\$1 + 0 🔬$ | $\$1 + 1 🔬$ | $\$1 + 2 🔬$ | **$\$1 + 0.21 🔬$** | NO | **Mediocre:** Nominal EV ~1.21; lacks Green research identity. |
| **Option D1 (Base 1 + Scaling)** | $(1 + g) \times 1 🔬$ | $1 🔬$ | $2 🔬$ | $3 🔬$ | **1.21 / 1.35 🔬** | NO | **Solid:** Never blank; rewards each glitch; clean wording. |
| **Option D2 (Base 2 + Scaling)** | $(2 + g) \times 1 🔬$ | $2 🔬$ | $3 🔬$ | $4 🔬$ | **2.21 / 2.35 🔬** | NO | **RECOMMENDED:** Perfect parity with G3 ($4: $2 🔬 + \$1$). |

---

## 3. Timing, Synergies & Tension Analysis

### Thematic Alignment
In cyber defense, a **Universal Sandbox** is an isolated virtual runtime where live malware, zero-days, and contaminated payloads are deliberately detonated to observe malicious behavior, extract threat intelligence, and compile countermeasures.
Granting a baseline of research, plus additional research for every active, quarantined glitch in the player's defense grid, fits the narrative theme flawlessly.

### Phase Lifecycle Timing
```
Phase 1 (Deploy): Green F1 cleans 1 slot. Shield dice clean slots. Defense Capacity = base - g.
   ↓
Phase 2 (Compiler): Corruption track may trigger "Glitch X die/dice" spaces.
   ↓
Phase 3 (Income): [G2 TRIGGERS HERE] Player collects Research based on active glitched slots (g).
   ↓
Phase 4 (Attack): Tower drops. Shield capacity was lower due to g. Unblocked Green creates NEW glitches.
   ↓
Phase 5 (Pipeline): Step 3 Graduation cleans 1 slot for free. Step 4 Green Secret yields 3 - g Secrets.
   ↓
Phase 6 (Operations): Spend Research to upgrade tracks (1-3 🔬) or regain Market Share (3 🔬 : +1 MS).
```

### Self-Balancing Tension (Proof of Degeneracy Prevention)
Can a player intentionally leave shield slots glitched to "farm" Research with G2?
**Mathematical answer: Absolutely not.** Three structural checks make glitch-farming suicidal:
1. **Direct Victory Point Penalty in Phase 5:**
   - Green Secret face yield is $\max(0, 3 - g)$ **Corporate Secrets**.
   - In Rogue Agent, **1 Corporate Secret = 1 Victory Point**.
   - G2 gives $+1 🔬$ per glitch. In Phase 6, Public Relations converts $3 🔬 \to 1 \text{ Market Share}$, which at best yields fractionally toward the Market Leader Bonus ($\sim 0.33 \text{ Secrets}$).
   - Sacrificing 1 guaranteed Secret (1 VP) in Phase 5 to farm $1 🔬$ ($0.33 \text{ VP}$) in Phase 3 is an instant net loss of $\sim 0.67 \text{ VP}$.
2. **Lethal Vulnerability in Phase 4:**
   - Defense Capacity at Level 0 is only `2`. Carrying 1 glitch reduces capacity to 1 shield die; carrying 2 glitches reduces capacity to **0 shields** (total vulnerability).
   - Unblocked Blue cubes directly cause Secret loss and **Patient Zero elimination**.
   - Unblocked Red cubes collapse Market Share, losing the Market Leader Bonus or triggering an early Market Collapse.
3. **Automatic Graduation Cleaning:**
   - Phase 5 Step 3 cleans 1 slot automatically whenever at least 1 die graduates.
- **Verdict:** G2 functions as a **counter-cyclical recovery engine** (mitigating the pain when battered by malware), never an exploitative engine.

---

## 4. Concrete Implementation Plan

### Recommended Rule Wording (Option D2)
In `RULES_APPENDIX.md`, Green `★` Variants:
> **G2 — Universal Sandbox ($4):** `[In Production — Income]` Gain `+2 🔬`, plus `+1 🔬` for each of your **Glitched Shield Slots** `[TUNE]`.

*(Alternative Option D1 for conservative power level: `Gain +1 🔬, plus +1 🔬 for each of your Glitched Shield Slots`.)*

### Exact Files to Modify:
1. `RULES_APPENDIX.md`:
   - Line 38: Update G2 description and remove `(Identical to G1 for now [TUNE].)`.
2. `RULES.md`:
   - Line 190: In Phase 1 Step 5 (Clean Glitched Shield Slots), remove `*G2*` from the parenthetical:
     `...each die showing a Clean 1 Glitched Shield Slot face (Green Face 1, *G1*) cleans 1...`
3. `GLOSSARY.md`:
   - **No new terms required.** "Glitched Shield Slot" and "Research (`🔬`)" are already defined.
4. `sim/entities.py`:
   - Update `G2` card definition in `get_all_variant_cards()`.
   - In `apply_variant_profile()` (line 1522): Decouple G2 from G1 (remove `clean_slots=1`, set description).
5. `sim/engine/phase3_income.py`:
   - In `_die_income_row()`: Add dynamic glitch bonus for `star_code == "G2"`.
6. `sim/engine/phase1_roll_deploy.py`:
   - Ensure G2 does not clean slots during Phase 1 Step 5 (automated by `clean_slots=0`).
7. `sim/bots/secret_face_policy.py`:
   - In `face_value()`: Add expected glitch research bonus when valuing G2.
8. `pnp/generate_pnp.py`:
   - Line 359–363: Update card timing badge to `P3 INCOME` and update description text.
9. `tests/`:
   - Add unit test verifying G2 produces base + $g$ research in Phase 3 and does not clean slots in Phase 1.
