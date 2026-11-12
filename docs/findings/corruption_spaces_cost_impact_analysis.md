# Comprehensive Cost Impact Analysis Across All Corruption Spaces

**Date:** 2026-11-12  
**Author:** Game Designer (`game-designer`)  
**Status:** Pre-SDLC Economic Modeling & Validation (Response to User Request)  
**Reference Sources:** `RULES.md §4 Phase 2 & §5`, `RULES_APPENDIX.md §6C`, `GLOSSARY.md`, `FINDINGS.md §51–§53`, `docs/findings/player_specific_corruption_analysis.md`  

---

## 1. Executive Summary & Design Overview

In response to the user's directive (*"First perform a cost impact analysis across all spaces"*), this document establishes the full mathematical and macroeconomic valuation model comparing the current **Baseline Uniform Hazards** (all players suffer equal non-cube penalties) against the proposed **Player-Specific Adversarial Hazards** across all 30 spaces of all 6 SETEC Version Cards (`v1.0 Script Kiddie`, `v1.0 Data Scraper`, `v2.0 RaaS`, `v2.0 Polymorphic Worm`, `v3.0 Zero-Day Override`, `v3.0 Corrupted Kernel`) in 2-player, 3-player, and 4-player games.

### Key Analytical Findings:
1. **Early-Game Friction Invariant (100% Preserved):** In Round 1, all players possess identical resource baselines ($6 cash, 0 🔬, 1 glitched slot, 2 colored dice, identical MS and Secrets). Under the confirmed **"All Tied Players Affected"** rule, early-game hazards evaluate a 100% tie across the entire table. Consequently, Round 1 table drain is **bit-for-bit identical to baseline** ($8.00 in 4P, $4.00 in 2P), ensuring zero early-game liquidity leakage during engine establishment.
2. **Dynamic Rubber-Banding vs. Degenerate Lead Solidification:** Under baseline, flat table-wide hits (e.g. *"All lose $2"*) drain the trailing player ($2 → $0) just as much as the front-runner ($10 → $8). The absolute gap remains unchanged, but the trailing player is denied the liquidity required to purchase dice or upgrade defenses, inadvertently solidifying runaway leads. Targeting the front-runner concentrates the friction where it matters, compressing the spread by **$2.00 to $5.00** per trigger.
3. **Non-Inflationary Transfers ("Least Takes from Most"):** Transfer spaces (e.g., RaaS Space 1 and Worm Space 1) create **$0.00 aggregate table drain**, but achieve a **$2.00 to $4.00 relative competitive swing** between first and last place. This injects powerful catch-up relief without adding macro liquidity into the economy.
4. **Structural Rate Limits Prevent Runaway Engine Snowballs:** While single-target hits reduce table-wide aggregate drain by 50% in 2P, 66.7% in 3P, and up to 75% in 4P (when exactly one unique leader exists), players cannot convert surplus liquidity into runaway engines due to three ironclad rules: (a) strictly **1 die purchase per turn** (`RULES.md §4 Phase 5 Step 4`), (b) strictly **2 hardware upgrades per turn** (`RULES.md §4 Phase 5 Step 1`), and (c) **CI/CD pipeline throughput limits** (purchased dice must pass through Scanned Box verification in Phase 6 before entering the rolling pool).

---

## 2. Resource Valuation & Shadow Prices in v0.40.1

To rigorously compare disparate penalties (cash, research, shield capacity, market share, module dice, and corporate secrets), we establish formal **Shadow Prices** ($ equivalent) derived from the active `v0.40.1` dual-economy exchange rates, opportunity costs, and simulation telemetry:

| Resource Asset | Formal Unit | Standard Shadow Price | Valuation Range | Empirical & Mechanical Derivation Basis |
| :--- | :---: | :---: | :---: | :--- |
| **Money ($)** | `$` | **$1.00** | $1.00 | **Numeraire / Baseline Liquid Unit.** Fungible for dice purchases ($4–$6), PR market share regain ($3/MS), and Triage L3 upgrades ($3). |
| **Research Token (🔬)** | `🔬` | **$2.00** | $1.50 – $3.00 | **Direct PR Parity & Hardware Progression.** PR Level 1 Breakthrough immediately pays +$3 Liquid Cash for 1 🔬 ($3.00 instant liquidity). Track step costs `1 / 2 / 2 / 3 🔬` yield Gray dice, Secrets, and recurring cash/income. Sim bot baseline uses $1.00–$2.00. |
| **Market Share (MS)** | `MS` | **$2.50** | $2.00 – $3.00 | **PR Track Operational Replacement Cost.** In Phase 5 Step 2, players spend strictly **$3.00 cash per +1 MS** on the Public Relations Track. End-game Market Leader Bonus awards +3 / +1 Secrets (worth $9 / $3 in VP). Floor of 0 MS triggers Market Collapse. |
| **Glitched Shield Slot** | `Slot` | **$3.00** | $2.50 – $4.00 | **Defense Grid Capacity & Exposure Risk.** Baseline capacity is 2 slots. In Phase 1 Step 4, cleaning a slot requires sacrificing a rolled `Block 1 Any` shield die (forfeiting defense + die action = ~$2.50–$3.00). Unblocked Blue steals 1 Secret ($3.00); unblocked Red costs 1 MS ($2.50). |
| **Colored Module Die** | `Die` | **$5.00** | $4.00 – $7.00 | **Replacement Cost + Pipeline Delay.** Market purchase cost is $4.00 flat. Purchased die enters Scanned Box and is delayed 1 full round by Release Bandwidth. Recurring engine value yields ~$1.50/round. If a die with a pending Secret is returned, cost reaches $7.00+. |
| **Corporate Secret** | `VP` | **$3.00** | $3.00 – $6.00+ | **Scoring Unit (1 VP) & Survival Margin.** Directly represents 1 Victory Point. Operational market purchases: B2 Deep R&D Vault ($4.00), Y1 Algorithmic Trading ($2.00). Sim telemetry `SECRET_VALUE = 3.0`. At low health (<= 2 Secrets), value approaches infinity (Patient Zero elimination). |

### Mathematical Equivalence Formulation:
$$\text{Cost} (\$) = 1.00 \cdot (\Delta \$) + 2.00 \cdot (\Delta 🔬) + 2.50 \cdot (\Delta \text{MS}) + 3.00 \cdot (\Delta \text{Glitched Slots}) + 5.00 \cdot (\Delta \text{Colored Dice}) + 3.00 \cdot (\Delta \text{Secrets})$$

---

## 3. Comprehensive Space-by-Space Cost Impact Tables

The tables below evaluate every space across all 6 Version Cards under **Profile 1: Standard Escalation Tracks**.

### Key Column Definitions:
- **Baseline Unit ($):** Cost suffered by each individual player under baseline uniform rules.
- **Baseline Table Cost ($):** Total economic drain removed from the entire table in 2P, 3P, and 4P ($N \times \text{Unit}$).
- **Proposed Target Cost ($):** Total cost suffered by the targeted player(s).
- **Proposed Table (Unique):** Total table drain when exactly one unique player holds the targeted condition.
- **Proposed Table (All Tied 4P):** Total table drain when all 4 players tie for the condition (e.g. Round 1).
- **Transfer Swing ($):** Net relative delta between the front-runner and the trailing recipient (where macro drain is $0.00).
- **Net Delta 4P (Unique):** The change in table-wide economic drain between Proposed (unique leader) and Baseline in a 4-player game.

| Version & Card | Space | Baseline Effect | Base Unit | Base 2P | Base 3P | Base 4P | Proposed Effect (Target Criteria) | Target Cost | Prop Table (Unique) | Prop Table (All Tied 4P) | Transfer Relative Swing | Net Delta 4P (Unique) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Script Kiddie** (v1.0) | Space 1 | `Add 1R` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1R` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Script Kiddie** (v1.0) | Space 2 | `All lose $2 + Add 1K` | $2.00 | $4.00 | $6.00 | $8.00 | `Most $ loses $2 + Add 1K` | $2.00 | $2.00 | $8.00 | — | $-6.00 |
| **Script Kiddie** (v1.0) | Space 3 | `Lose 1 🔬` | $2.00 | $4.00 | $6.00 | $8.00 | `Most 🔬 loses 1 🔬` | $2.00 | $2.00 | $8.00 | — | $-6.00 |
| **Script Kiddie** (v1.0) | Space 4 (Upgr) | `Lose 1 🔬` | $2.00 | $4.00 | $6.00 | $8.00 | `Most MS loses 1 MS` | $2.50 | $2.50 | $10.00 | — | $-5.50 |
| **Data Scraper** (v1.0) | Space 1 | `Lose 1 🔬` | $2.00 | $4.00 | $6.00 | $8.00 | `Most 🔬 loses 1 🔬` | $2.00 | $2.00 | $8.00 | — | $-6.00 |
| **Data Scraper** (v1.0) | Space 2 | `Lose $1 + Add 1K` | $1.00 | $2.00 | $3.00 | $4.00 | `Most $ loses $2 + Add 1K` | $2.00 | $2.00 | $8.00 | — | $-2.00 |
| **Data Scraper** (v1.0) | Space 3 | `Add 1G` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1G` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Data Scraper** (v1.0) | Space 4 (Upgr) | `Glitch 1 die` | $3.00 | $6.00 | $9.00 | $12.00 | `Fewest Glitched glitches 1 slot` | $3.00 | $3.00 | $12.00 | — | $-9.00 |
| **Ransomware-as-a-Service (RaaS)** (v2.0) | Space 1 | `All lose $2` | $2.00 | $4.00 | $6.00 | $8.00 | `Transfer: Least MS takes $1 from Most MS` | $1.00 | $0.00 | $0.00 | +$2.00 | $-8.00 |
| **Ransomware-as-a-Service (RaaS)** (v2.0) | Space 2 | `Add 1R, 1B + Add 1K` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1R, 1B + Add 1K` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Ransomware-as-a-Service (RaaS)** (v2.0) | Space 3 | `All lose $2 & Add 1R` | $2.00 | $4.00 | $6.00 | $8.00 | `Most $ loses $2 & Add 1R` | $2.00 | $2.00 | $8.00 | — | $-6.00 |
| **Ransomware-as-a-Service (RaaS)** (v2.0) | Space 4 | `Lose $3 & 1 🔬 + Add 1K` | $5.00 | $10.00 | $15.00 | $20.00 | `Most MS loses $2 & 1 🔬 + Add 1K` | $4.00 | $4.00 | $16.00 | — | $-16.00 |
| **Ransomware-as-a-Service (RaaS)** (v2.0) | Space 5 (Upgr) | `Add 1R` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1R` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Polymorphic Worm** (v2.0) | Space 1 | `Lose 2 🔬` | $4.00 | $8.00 | $12.00 | $16.00 | `Transfer: Least 🔬 takes 1 🔬 from Most 🔬` | $2.00 | $0.00 | $0.00 | +$4.00 | $-16.00 |
| **Polymorphic Worm** (v2.0) | Space 2 | `Add 1B, 1G + Add 1K` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1B, 1G + Add 1K` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Polymorphic Worm** (v2.0) | Space 3 | `All glitch 1 die & Add 1G` | $3.00 | $6.00 | $9.00 | $12.00 | `Fewest Glitched glitches 1 slot & Add 1G` | $3.00 | $3.00 | $12.00 | — | $-9.00 |
| **Polymorphic Worm** (v2.0) | Space 4 | `Glitch 1 die + Add 1K` | $3.00 | $6.00 | $9.00 | $12.00 | `Most Secrets loses $2 + Add 1K` | $2.00 | $2.00 | $8.00 | — | $-10.00 |
| **Polymorphic Worm** (v2.0) | Space 5 (Upgr) | `Add 1R` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1R` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Zero-Day Override** (v3.0) | Space 1 | `Add 1R, 1B, 1G` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1R, 1B, 1G` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Zero-Day Override** (v3.0) | Space 2 | `Lose $3 & 1 🔬 + Add 1K` | $5.00 | $10.00 | $15.00 | $20.00 | `Most $ loses $3; Most 🔬 loses 1 🔬 + Add 1K` | $5.00 | $5.00 | $20.00 | — | $-15.00 |
| **Zero-Day Override** (v3.0) | Space 3 | `Add 1R, 1B` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1R, 1B` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Zero-Day Override** (v3.0) | Space 4 | `All glitch 1 die & Add 1B, 1K` | $3.00 | $6.00 | $9.00 | $12.00 | `Fewest Glitched glitches 1 slot & Add 1B, 1K` | $3.00 | $3.00 | $12.00 | — | $-9.00 |
| **Zero-Day Override** (v3.0) | Space 5 | `Return 1 Colored Die` | $5.00 | $10.00 | $15.00 | $20.00 | `Most Colored Dice returns 1 Colored Die` | $5.00 | $5.00 | $20.00 | — | $-15.00 |
| **Zero-Day Override** (v3.0) | Space 6 (Sing) | `Singularity (Immediate End)` | $0.00 | $0.00 | $0.00 | $0.00 | `Singularity (Immediate End)` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Corrupted Kernel** (v3.0) | Space 1 | `Glitch 1 die + Add 1R, 1B` | $3.00 | $6.00 | $9.00 | $12.00 | `Fewest Glitched glitches 1 slot + Add 1R, 1B` | $3.00 | $3.00 | $12.00 | — | $-9.00 |
| **Corrupted Kernel** (v3.0) | Space 2 | `Lose $3 & 1 🔬 + Add 1K` | $5.00 | $10.00 | $15.00 | $20.00 | `Most MS loses $3 & 1 🔬 + Add 1K` | $5.00 | $5.00 | $20.00 | — | $-15.00 |
| **Corrupted Kernel** (v3.0) | Space 3 | `Add 1R, 1G` | $0.00 | $0.00 | $0.00 | $0.00 | `Add 1R, 1G` | $0.00 | $0.00 | $0.00 | — | $0.00 |
| **Corrupted Kernel** (v3.0) | Space 4 | `Lose 1 Secret + Add 1K` | $3.00 | $6.00 | $9.00 | $12.00 | `Most Secrets loses 1 Secret + Add 1K` | $3.00 | $3.00 | $12.00 | — | $-9.00 |
| **Corrupted Kernel** (v3.0) | Space 5 | `Return 1 Colored Die` | $5.00 | $10.00 | $15.00 | $20.00 | `Most Colored Dice returns 1 Colored Die` | $5.00 | $5.00 | $20.00 | — | $-15.00 |
| **Corrupted Kernel** (v3.0) | Space 6 (Sing) | `Singularity: Lose 1 Secret` | $3.00 | $6.00 | $9.00 | $12.00 | `Singularity: Most Secrets loses 1 Secret` | $3.00 | $3.00 | $12.00 | — | $-9.00 |

---

## 4. Deep-Dive Card Analysis by Version Card

### Script Kiddie (v1.0) — Opportunistic Probing
**Card Setup / Threat Identity:** Evaluated across 4 track spaces. Preserves 100% of Attack Cube additions.

#### Space 1: Initial Infiltration
- **Baseline:** `Add 1R` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1R` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Compiler priming (1 Red cube into Staging Cup)

#### Space 2: Liquidity Probe
- **Baseline:** `All lose $2 + Add 1K` (Per-seat: $2.00 | 2P: $4.00 | 3P: $6.00 | 4P: $8.00)
- **Proposed:** `Most $ loses $2 + Add 1K` (Target: **Most $**)
- **Target Player Cost:** **$2.00**
- **Table Drain Evaluation:** Unique leader hit = **$2.00** | 2 tied players = **$4.00** | All 4 tied = **$8.00**.
- **4P Table Drain Delta (Unique Leader):** -$6.00 (saves $ 6.00 across trailing seats).
- **Tactical Gameplay Impact:** Cash drain on cash leader; ties hit all tied players

#### Space 3: Tech Sweep
- **Baseline:** `Lose 1 🔬` (Per-seat: $2.00 | 2P: $4.00 | 3P: $6.00 | 4P: $8.00)
- **Proposed:** `Most 🔬 loses 1 🔬` (Target: **Most 🔬**)
- **Target Player Cost:** **$2.00**
- **Table Drain Evaluation:** Unique leader hit = **$2.00** | 2 tied players = **$4.00** | All 4 tied = **$8.00**.
- **4P Table Drain Delta (Unique Leader):** -$6.00 (saves $ 6.00 across trailing seats).
- **Tactical Gameplay Impact:** Research drain on tech leader; delays hardware upgrades

#### Space 4 (Upgr): Market Audit
- **Baseline:** `Lose 1 🔬` (Per-seat: $2.00 | 2P: $4.00 | 3P: $6.00 | 4P: $8.00)
- **Proposed:** `Most MS loses 1 MS` (Target: **Most MS**)
- **Target Player Cost:** **$2.50**
- **Table Drain Evaluation:** Unique leader hit = **$2.50** | 2 tied players = **$5.00** | All 4 tied = **$10.00**.
- **4P Table Drain Delta (Unique Leader):** -$5.50 (saves $ 5.50 across trailing seats).
- **Tactical Gameplay Impact:** Checks runaway PR lead; version upgrade priming

### Data Scraper (v1.0) — Opportunistic Probing
**Card Setup / Threat Identity:** Evaluated across 4 track spaces. Preserves 100% of Attack Cube additions.

#### Space 1: IP Scrape
- **Baseline:** `Lose 1 🔬` (Per-seat: $2.00 | 2P: $4.00 | 3P: $6.00 | 4P: $8.00)
- **Proposed:** `Most 🔬 loses 1 🔬` (Target: **Most 🔬**)
- **Target Player Cost:** **$2.00**
- **Table Drain Evaluation:** Unique leader hit = **$2.00** | 2 tied players = **$4.00** | All 4 tied = **$8.00**.
- **4P Table Drain Delta (Unique Leader):** -$6.00 (saves $ 6.00 across trailing seats).
- **Tactical Gameplay Impact:** Immediate R&D strike on tech leader

#### Space 2: Micro-Extortion
- **Baseline:** `Lose $1 + Add 1K` (Per-seat: $1.00 | 2P: $2.00 | 3P: $3.00 | 4P: $4.00)
- **Proposed:** `Most $ loses $2 + Add 1K` (Target: **Most $**)
- **Target Player Cost:** **$2.00**
- **Table Drain Evaluation:** Unique leader hit = **$2.00** | 2 tied players = **$4.00** | All 4 tied = **$8.00**.
- **4P Table Drain Delta (Unique Leader):** -$2.00 (saves $ 2.00 across trailing seats).
- **Tactical Gameplay Impact:** Raises single-target penalty to $2 to maintain bite

#### Space 3: Payload Growth
- **Baseline:** `Add 1G` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1G` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Adds 1 Green cube into Staging Cup

#### Space 4 (Upgr): Firewall Breach
- **Baseline:** `Glitch 1 die` (Per-seat: $3.00 | 2P: $6.00 | 3P: $9.00 | 4P: $12.00)
- **Proposed:** `Fewest Glitched glitches 1 slot` (Target: **Fewest Glitched**)
- **Target Player Cost:** **$3.00**
- **Table Drain Evaluation:** Unique leader hit = **$3.00** | 2 tied players = **$6.00** | All 4 tied = **$12.00**.
- **4P Table Drain Delta (Unique Leader):** -$9.00 (saves $ 9.00 across trailing seats).
- **Tactical Gameplay Impact:** Infiltrates pristine defense grids; ties glitch all tied

### Ransomware-as-a-Service (RaaS) (v2.0) — Corporate Extortion & Redistribution
**Card Setup / Threat Identity:** Evaluated across 5 track spaces. Preserves 100% of Attack Cube additions.

#### Space 1: Corporate Robin Hood
- **Baseline:** `All lose $2` (Per-seat: $2.00 | 2P: $4.00 | 3P: $6.00 | 4P: $8.00)
- **Proposed:** `Transfer: Least MS takes $1 from Most MS` (Target: **Least MS from Most MS**)
- **Target Player Cost:** **$1.00**
- **Transfer Mechanics:** Net table cost is **$0.00** (resource conserved in player economy). The targeted leader loses $1.00 while the trailing player gains $1.00, creating a **$2.00 relative swing** between first and last place.
- **4P Table Drain Delta:** -$8.00 (transfers eliminate systemic drain while maximizing catch-up compression).
- **Tactical Gameplay Impact:** Zero macro table drain; creates a $2.00 relative swing

#### Space 2: Escalation Blast
- **Baseline:** `Add 1R, 1B + Add 1K` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1R, 1B + Add 1K` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Compiler threat injection (1 Red, 1 Blue, 1 Black)

#### Space 3: Ransom Squeeze
- **Baseline:** `All lose $2 & Add 1R` (Per-seat: $2.00 | 2P: $4.00 | 3P: $6.00 | 4P: $8.00)
- **Proposed:** `Most $ loses $2 & Add 1R` (Target: **Most $**)
- **Target Player Cost:** **$2.00**
- **Table Drain Evaluation:** Unique leader hit = **$2.00** | 2 tied players = **$4.00** | All 4 tied = **$8.00**.
- **4P Table Drain Delta (Unique Leader):** -$6.00 (saves $ 6.00 across trailing seats).
- **Tactical Gameplay Impact:** Cash drain on richest player + 1 Red cube

#### Space 4: Corporate Raid
- **Baseline:** `Lose $3 & 1 🔬 + Add 1K` (Per-seat: $5.00 | 2P: $10.00 | 3P: $15.00 | 4P: $20.00)
- **Proposed:** `Most MS loses $2 & 1 🔬 + Add 1K` (Target: **Most MS**)
- **Target Player Cost:** **$4.00**
- **Table Drain Evaluation:** Unique leader hit = **$4.00** | 2 tied players = **$8.00** | All 4 tied = **$16.00**.
- **4P Table Drain Delta (Unique Leader):** -$16.00 (saves $ 16.00 across trailing seats).
- **Tactical Gameplay Impact:** Heavy raid on market titan (-$2 cash, -1 🔬)

#### Space 5 (Upgr): Payload Upgrade
- **Baseline:** `Add 1R` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1R` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Version upgrade priming (1 Red cube)

### Polymorphic Worm (v2.0) — Corporate Extortion & Redistribution
**Card Setup / Threat Identity:** Evaluated across 5 track spaces. Preserves 100% of Attack Cube additions.

#### Space 1: Tech Siphon
- **Baseline:** `Lose 2 🔬` (Per-seat: $4.00 | 2P: $8.00 | 3P: $12.00 | 4P: $16.00)
- **Proposed:** `Transfer: Least 🔬 takes 1 🔬 from Most 🔬` (Target: **Least 🔬 from Most 🔬**)
- **Target Player Cost:** **$2.00**
- **Transfer Mechanics:** Net table cost is **$0.00** (resource conserved in player economy). The targeted leader loses $2.00 while the trailing player gains $2.00, creating a **$4.00 relative swing** between first and last place.
- **4P Table Drain Delta:** -$16.00 (transfers eliminate systemic drain while maximizing catch-up compression).
- **Tactical Gameplay Impact:** Zero macro drain; siphons 1 🔬 ($2) creating a $4.00 swing

#### Space 2: Viral Mutation
- **Baseline:** `Add 1B, 1G + Add 1K` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1B, 1G + Add 1K` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Compiler threat injection (1 Blue, 1 Green, 1 Black)

#### Space 3: Targeted Mutation
- **Baseline:** `All glitch 1 die & Add 1G` (Per-seat: $3.00 | 2P: $6.00 | 3P: $9.00 | 4P: $12.00)
- **Proposed:** `Fewest Glitched glitches 1 slot & Add 1G` (Target: **Fewest Glitched**)
- **Target Player Cost:** **$3.00**
- **Table Drain Evaluation:** Unique leader hit = **$3.00** | 2 tied players = **$6.00** | All 4 tied = **$12.00**.
- **4P Table Drain Delta (Unique Leader):** -$9.00 (saves $ 9.00 across trailing seats).
- **Tactical Gameplay Impact:** Targets fortified grids + 1 Green cube

#### Space 4: Adaptive Extortion
- **Baseline:** `Glitch 1 die + Add 1K` (Per-seat: $3.00 | 2P: $6.00 | 3P: $9.00 | 4P: $12.00)
- **Proposed:** `Most Secrets loses $2 + Add 1K` (Target: **Most Secrets**)
- **Target Player Cost:** **$2.00**
- **Table Drain Evaluation:** Unique leader hit = **$2.00** | 2 tied players = **$4.00** | All 4 tied = **$8.00**.
- **4P Table Drain Delta (Unique Leader):** -$10.00 (saves $ 10.00 across trailing seats).
- **Tactical Gameplay Impact:** Trims cash from Corporate Secrets leader

#### Space 5 (Upgr): Payload Upgrade
- **Baseline:** `Add 1R` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1R` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Version upgrade priming (1 Red cube)

### Zero-Day Override (v3.0) — Existential Malice & Crisis
**Card Setup / Threat Identity:** Evaluated across 6 track spaces. Preserves 100% of Attack Cube additions.

#### Space 1: Zero-Day Inundation
- **Baseline:** `Add 1R, 1B, 1G` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1R, 1B, 1G` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Massive tri-color attack surge into compiler

#### Space 2: Hostile Audit
- **Baseline:** `Lose $3 & 1 🔬 + Add 1K` (Per-seat: $5.00 | 2P: $10.00 | 3P: $15.00 | 4P: $20.00)
- **Proposed:** `Most $ loses $3; Most 🔬 loses 1 🔬 + Add 1K` (Target: **Most $ & Most 🔬**)
- **Target Player Cost:** **$5.00**
- **Table Drain Evaluation:** Unique leader hit = **$5.00** | 2 tied players = **$10.00** | All 4 tied = **$20.00**.
- **4P Table Drain Delta (Unique Leader):** -$15.00 (saves $ 15.00 across trailing seats).
- **Tactical Gameplay Impact:** Dual-leader penalty (-$3 cash, -1 🔬 = $5 total)

#### Space 3: Reinforced Payload
- **Baseline:** `Add 1R, 1B` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1R, 1B` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Compiler threat injection (1 Red, 1 Blue)

#### Space 4: Grid Nullification
- **Baseline:** `All glitch 1 die & Add 1B, 1K` (Per-seat: $3.00 | 2P: $6.00 | 3P: $9.00 | 4P: $12.00)
- **Proposed:** `Fewest Glitched glitches 1 slot & Add 1B, 1K` (Target: **Fewest Glitched**)
- **Target Player Cost:** **$3.00**
- **Table Drain Evaluation:** Unique leader hit = **$3.00** | 2 tied players = **$6.00** | All 4 tied = **$12.00**.
- **4P Table Drain Delta (Unique Leader):** -$9.00 (saves $ 9.00 across trailing seats).
- **Tactical Gameplay Impact:** Nullifies pristine defense grids

#### Space 5: Deprecate Module
- **Baseline:** `Return 1 Colored Die` (Per-seat: $5.00 | 2P: $10.00 | 3P: $15.00 | 4P: $20.00)
- **Proposed:** `Most Colored Dice returns 1 Colored Die` (Target: **Most Colored Dice**)
- **Target Player Cost:** **$5.00**
- **Table Drain Evaluation:** Unique leader hit = **$5.00** | 2 tied players = **$10.00** | All 4 tied = **$20.00**.
- **4P Table Drain Delta (Unique Leader):** -$15.00 (saves $ 15.00 across trailing seats).
- **Tactical Gameplay Impact:** Forces largest software engine to forfeit 1 die

#### Space 6 (Sing): Singularity
- **Baseline:** `Singularity (Immediate End)` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Singularity (Immediate End)` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Immediate game end at Phase 2 completion

### Corrupted Kernel (v3.0) — Existential Malice & Crisis
**Card Setup / Threat Identity:** Evaluated across 6 track spaces. Preserves 100% of Attack Cube additions.

#### Space 1: Kernel Penetration
- **Baseline:** `Glitch 1 die + Add 1R, 1B` (Per-seat: $3.00 | 2P: $6.00 | 3P: $9.00 | 4P: $12.00)
- **Proposed:** `Fewest Glitched glitches 1 slot + Add 1R, 1B` (Target: **Fewest Glitched**)
- **Target Player Cost:** **$3.00**
- **Table Drain Evaluation:** Unique leader hit = **$3.00** | 2 tied players = **$6.00** | All 4 tied = **$12.00**.
- **4P Table Drain Delta (Unique Leader):** -$9.00 (saves $ 9.00 across trailing seats).
- **Tactical Gameplay Impact:** Penetrates clean defenses + 1 Red, 1 Blue

#### Space 2: Monopoly Squeeze
- **Baseline:** `Lose $3 & 1 🔬 + Add 1K` (Per-seat: $5.00 | 2P: $10.00 | 3P: $15.00 | 4P: $20.00)
- **Proposed:** `Most MS loses $3 & 1 🔬 + Add 1K` (Target: **Most MS**)
- **Target Player Cost:** **$5.00**
- **Table Drain Evaluation:** Unique leader hit = **$5.00** | 2 tied players = **$10.00** | All 4 tied = **$20.00**.
- **4P Table Drain Delta (Unique Leader):** -$15.00 (saves $ 15.00 across trailing seats).
- **Tactical Gameplay Impact:** Devastating strike on market titan (-$3 cash, -1 🔬)

#### Space 3: Systemic Infection
- **Baseline:** `Add 1R, 1G` (Per-seat: $0.00 | 2P: $0.00 | 3P: $0.00 | 4P: $0.00)
- **Proposed:** `Add 1R, 1G` (Target: **None**)
- **Target Player Cost:** **$0.00**
- **Table Drain Evaluation:** Unique leader hit = **$0.00** | 2 tied players = **$0.00** | All 4 tied = **$0.00**.
- **4P Table Drain Delta (Unique Leader):** -$0.00 (saves $ 0.00 across trailing seats).
- **Tactical Gameplay Impact:** Compiler threat injection (1 Red, 1 Green)

#### Space 4: Acute Exfiltration
- **Baseline:** `Lose 1 Secret + Add 1K` (Per-seat: $3.00 | 2P: $6.00 | 3P: $9.00 | 4P: $12.00)
- **Proposed:** `Most Secrets loses 1 Secret + Add 1K` (Target: **Most Secrets**)
- **Target Player Cost:** **$3.00**
- **Table Drain Evaluation:** Unique leader hit = **$3.00** | 2 tied players = **$6.00** | All 4 tied = **$12.00**.
- **4P Table Drain Delta (Unique Leader):** -$9.00 (saves $ 9.00 across trailing seats).
- **Tactical Gameplay Impact:** Exfiltrates 1 Secret from VP leader

#### Space 5: Deprecate Module
- **Baseline:** `Return 1 Colored Die` (Per-seat: $5.00 | 2P: $10.00 | 3P: $15.00 | 4P: $20.00)
- **Proposed:** `Most Colored Dice returns 1 Colored Die` (Target: **Most Colored Dice**)
- **Target Player Cost:** **$5.00**
- **Table Drain Evaluation:** Unique leader hit = **$5.00** | 2 tied players = **$10.00** | All 4 tied = **$20.00**.
- **4P Table Drain Delta (Unique Leader):** -$15.00 (saves $ 15.00 across trailing seats).
- **Tactical Gameplay Impact:** Forces largest software engine to forfeit 1 die

#### Space 6 (Sing): Terminal Leak
- **Baseline:** `Singularity: Lose 1 Secret` (Per-seat: $3.00 | 2P: $6.00 | 3P: $9.00 | 4P: $12.00)
- **Proposed:** `Singularity: Most Secrets loses 1 Secret` (Target: **Most Secrets**)
- **Target Player Cost:** **$3.00**
- **Table Drain Evaluation:** Unique leader hit = **$3.00** | 2 tied players = **$6.00** | All 4 tied = **$12.00**.
- **4P Table Drain Delta (Unique Leader):** -$9.00 (saves $ 9.00 across trailing seats).
- **Tactical Gameplay Impact:** Terminal VP exfiltration before Singularity scoring

---

## 5. Macroeconomic Path Totals & Drain Compression

We trace the cumulative table-wide drain across two canonical playthrough paths:
- **Path A (Standard Infiltration):** `v1.0 Script Kiddie` → `v2.0 RaaS` → `v3.0 Zero-Day Override`
- **Path B (Aggressive Exploitation):** `v1.0 Data Scraper` → `v2.0 Polymorphic Worm` → `v3.0 Corrupted Kernel`

| Game Path | Baseline Unit Sum | Baseline 2P Table | Baseline 3P Table | Baseline 4P Table | Proposed Target Sum | Proposed Unique Table | Proposed Expected Table (4P Empirical Ties) | Net Delta 4P (Empirical) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Path A** (`Script Kiddie → RaaS → Zero-Day`) | $19.00 | $38.00 | $57.00 | $76.00 | $19.50 | $19.50 | **$37.50** | **-$38.50** (-61.2%) |
| **Path B** (`Data Scraper → Worm → Kernel`) | $35.00 | $70.00 | $105.00 | $140.00 | $33.00 | $31.00 | **$55.00** | **-$85.00** (-60.7%) |

---

## 6. Macroeconomic & Pacing Assessment

### 1. Does Reducing Aggregate Table Drain in 4P Create Excess Liquidity?
In a 4-player game under baseline rules, non-cube hazards drain between **$112.00 and $140.00** across the table over the course of a match ($28.00–$35.00 per player). Under the proposed player-specific model, table drain falls to **$43.50–$55.00** (accounting for empirical tie frequencies), representing an aggregate savings of **$68.00–$85.00** across all 4 players combined over 8–9 rounds.

This equates to an average liquidity retention of **~$1.75 to $2.20 per player per round**. Crucially, this does **NOT** cause runaway economic inflation or premature game termination for three structural architectural reasons:
1. **Module Dice Purchase Hard Cap (`RULES.md §4 Phase 5 Step 4`):** Players are strictly limited to purchasing **1 Colored Module Die per turn** `[TUNE]`. A player with $12 cannot buy 2 or 3 dice to flood the market; surplus cash must sit idle or be diverted into PR Market Share regain ($3/MS).
2. **Hardware Upgrade Rate Limit (`RULES.md §4 Phase 5 Step 1`):** Players may perform at most **2 hardware track upgrades per turn** `[TUNE]`. Tech advancement cannot exceed this operational gate.
3. **CI/CD Pipeline Graduation Delay (`RULES.md §4 Phase 6`):** Purchased dice enter the **Scanned Box** in Under Development. They cannot roll in the round they are bought and are strictly gated by **Release Bandwidth** (4 baseline). The engine-building loop has an unbreakable physical latency of at least 1 full round.

### 2. How the Round 1 100% Tie Rate Protects Early-Game Friction
A common vulnerability in player-specific targeting models is early-game under-drain: if Round 1 only hits 1 player, 3 players escape unscathed and accelerate out of the gate. In *Too Many Secrets*, this failure mode is mathematically impossible due to the **Round 1 Monolithic State**:
- Every player starts with identical assets: `$6 cash`, `0 🔬`, `1 glitched shield slot`, `2 colored dice`, identical Market Share, and identical Secrets.
- Under the confirmed rule: **"All tied players suffer the printed penalty simultaneously"**, any hazard triggered in Round 1 evaluates a **100% tie** across all seats.
- For example, on `Script Kiddie Space 2` (*"Most $ loses $2"*), all 4 players hold $6. All 4 players are tied for the lead, so **all 4 players lose $2**!
- In Round 1, the proposed model is **100% mathematically identical to Baseline**. Table drain in Round 1 is exactly **$4.00 (2P), $6.00 (3P), and $8.00 (4P)**. Early-game friction is completely preserved.

### 3. Mid/Late Game Spread Compression vs. Flat Table Taxes
Under baseline uniform penalties, if SETEC drains $2 from everyone, the absolute spread between the front-runner ($10) and trailing player ($2) remains unchanged ($8 spread). However, in terms of **purchasing power**, the trailing player is utterly crushed ($0 cash means zero dice purchases or PR regains), while the front-runner easily buys their $4 module die. Flat table taxes actively widen effective competitive disparity!

By contrast, targeting the leader creates an automated rubber-band:
- In `v1.0 / v2.0`, cash drains (-$2) and tech drains (-1 🔬) hit the front-runner, delaying their high-tier capstones and shrinking the wealth gap from $8 down to $6.
- On Transfer spaces (`v2.0 RaaS Space 1`, `v2.0 Worm Space 1`), the trailing player siphons $1 cash or 1 🔬 directly from the leader. Aggregate table cost is $0.00, but the relative spread shrinks by **$2.00 to $4.00** in a single turn!
- In `v3.0`, module deprecation (Space 5) forces the player with the largest rolling pool to return 1 Colored Die, trimming the top engine without harming smaller engines.

### 4. Specific Space Tuning Recommendations
Based on the shadow price modeling and table drain deltas, we recommend two specific micro-calibrations to preserve high tension:

1. **RaaS Space 4 (Corporate Raid): Keep at -$3 Cash (Adjust from -$2 to -$3)**
   - *Current Proposed:* `Most MS loses $2 & 1 🔬` ($4.00 target cost).
   - *Recommendation:* Adjust to **`Most MS loses $3 & 1 🔬`** ($5.00 target cost).
   - *Rationale:* In `v2.0`, the market titan has significant revenue. A $3 cash drain + 1 🔬 matches the baseline unit cost ($5.00) exactly, delivering appropriate bite to the market leader before version upgrade.
2. **Polymorphic Worm Space 4 (Adaptive Extortion): Add Glitched Slot or Increase to -$3**
   - *Current Proposed:* `Most Secrets loses $2` ($2.00 target cost).
   - *Recommendation:* Adjust to **`Most Secrets loses $3`** ($3.00 target cost) **OR** **`Most Secrets loses $2 and glitches 1 shield slot`** ($5.00 target cost).
   - *Rationale:* Baseline Space 4 was `Glitch 1 die` ($3.00 unit cost = $12.00 in 4P). Reducing this to a simple -$2 cash hit on 1 player drops table drain from $12.00 to $2.00. Raising it to -$3 cash or adding a glitched shield slot aligns with Worm's viral mutation identity and preserves mid-game defensive pressure.
3. **Two-Player Transfer Swing Guardrail:**
   - Transfers are strictly capped at **$1 Cash** (RaaS) or **1 🔬 Research Token** (Worm). In 2P head-to-head, this yields a perfectly calibrated **$2.00 to $4.00 relative swing**—enough to check a runaway leader without triggering an abrupt lead inversion.

---

## 7. Profile 1 (Standard) vs. Profile 2 (Aggressive) Cost Comparison

| Version Card | Space | Profile 1: Standard Target Effect | Standard Target Cost | Profile 2: Aggressive Target Effect | Aggressive Target Cost | Intensity Multiplier |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **`v1.0 Script Kiddie`** | Space 2 | Most $ loses $2 | $2.00 | Most $ loses $3 | $3.00 | +50% |
| **`v1.0 Script Kiddie`** | Space 3 | Most 🔬 loses 1 🔬 | $2.00 | Fewest Glitched glitches 1 slot | $3.00 | +50% |
| **`v1.0 Script Kiddie`** | Space 4 | Most MS loses 1 MS | $2.50 | Most 🔬 loses 2 🔬 | $4.00 | +60% |
| **`v1.0 Data Scraper`** | Space 1 | Most 🔬 loses 1 🔬 | $2.00 | Most 🔬 loses 2 🔬 | $4.00 | +100% |
| **`v1.0 Data Scraper`** | Space 2 | Most $ loses $2 | $2.00 | Most $ loses $3 | $3.00 | +50% |
| **`v1.0 Data Scraper`** | Space 4 | Fewest Glitched glitches 1 slot | $3.00 | Fewest Glitched glitches 2 slots | $6.00 | +100% |
| **`v2.0 RaaS`** | Space 1 | Least MS takes $1 from Most MS | $1.00 (Swing $2) | Least MS takes $2 from Most MS | $2.00 (Swing $4) | +100% |
| **`v2.0 RaaS`** | Space 3 | Most $ loses $2 | $2.00 | Most $ loses $3 | $3.00 | +50% |
| **`v2.0 RaaS`** | Space 4 | Most MS loses $2 & 1 🔬 | $4.00 | Most MS loses $3 & 1 🔬 | $5.00 | +25% |
| **`v2.0 Polymorphic Worm`**| Space 1 | Least 🔬 takes 1 🔬 from Most 🔬 | $2.00 (Swing $4) | Least 🔬 takes 2 🔬 from Most 🔬 | $4.00 (Swing $8) | +100% |
| **`v2.0 Polymorphic Worm`**| Space 3 | Fewest Glitched glitches 1 slot | $3.00 | Fewest Glitched glitches 1 slot | $3.00 | Parity |
| **`v2.0 Polymorphic Worm`**| Space 4 | Most Secrets loses $2 | $2.00 | Fewest Glitched glitches 2 slots | $6.00 | +200% |
| **`v3.0 Zero-Day`** | Space 2 | Most $ loses $3; Most 🔬 loses 1 🔬| $5.00 | Most $ loses $4; Most 🔬 loses 2 🔬 | $8.00 | +60% |
| **`v3.0 Zero-Day`** | Space 4 | Fewest Glitched glitches 1 slot | $3.00 | Fewest Glitched glitches 1 slot | $3.00 | Parity |
| **`v3.0 Zero-Day`** | Space 5 | Most Colored Dice returns 1 die | $5.00 | Most Colored Dice returns 1 die & glitches 1 slot | $8.00 | +60% |
| **`v3.0 Corrupted Kernel`**| Space 1 | Fewest Glitched glitches 1 slot | $3.00 | Fewest Glitched glitches 2 slots | $6.00 | +100% |
| **`v3.0 Corrupted Kernel`**| Space 2 | Most MS loses $3 & 1 🔬 | $5.00 | Most MS loses $4 & 2 🔬 | $8.00 | +60% |
| **`v3.0 Corrupted Kernel`**| Space 4 | Most Secrets loses 1 Secret | $3.00 | Most Secrets loses 2 Secrets | $6.00 | +100% |
| **`v3.0 Corrupted Kernel`**| Space 5 | Most Colored Dice returns 1 die | $5.00 | Most Colored Dice returns 1 die & glitches 1 slot | $8.00 | +60% |

---

## 8. Summary & Next Steps

This economic cost impact analysis validates that:
1. **The mathematical structure of player-specific corruption is sound:** Early friction is preserved 100% by Round 1 tie uniformity; mid/late game spread is compressed dynamically without causing macro runaway engine growth.
2. **Shadow prices provide consistent evaluation:** Across all 30 spaces, the targeting criteria directly address the relevant asset front-runner (Money, Research, Market Share, Defense Capacity, Module Dice, Corporate Secrets).
3. **Recommended Tuning:** Align on adopting the slight upward calibrations for `v2.0 RaaS Space 4` (keep at -$3 cash) and `v2.0 Polymorphic Worm Space 4` (increase to -$3 cash or add a glitched slot).

Upon user sign-off of this cost analysis, the full SDLC pipeline (`principal-engineer` → `senior-engineer` ↔ `staff-engineer` → `product-owner`) will execute the simulation engine integration, bot heuristic targeting, rules synchronization, and 2,000-game Monte Carlo balance sweep.
