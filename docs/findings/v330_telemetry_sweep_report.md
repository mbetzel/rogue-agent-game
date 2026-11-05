# Rogue Agent v0.33.0 Telemetry Sweep Report
## Phase 41: Step 2A Agency, White Contractor Sacrifice Enforcement, and Immediate Singularity

**Date:** 2026-11-05  
**Author:** Product Owner & QA Lead  
**Target Version:** `v0.33.0` Baseline  
**Total Matches:** 3,000 (1,000 matches per pod across [2P, 3P, 4P] = 9,000 player-games)  
**Execution Runtime:** 14.90 seconds (2P: 3.41s, 3P: 4.62s, 4P: 6.85s)  
**Base Seed:** 42  
**Unit Test Verification:** 563/563 tests passing (including 11 dedicated tests in `tests/test_v330_step2a_and_singularity.py`)  
**Raw Telemetry Summary:** [v330_telemetry_summary.json](file:///z:/home/mike/antigravity/rogue-agent/docs/findings/v330_telemetry_summary.json)  
**Historical Benchmarks:** [v0.32.0 Findings](file:///z:/home/mike/antigravity/rogue-agent/docs/findings/v320_telemetry_sweep_report.md), [v0.31.0 Findings](file:///z:/home/mike/antigravity/rogue-agent/docs/findings/v310_telemetry_sweep_report.md)

---

### 1. Executive Summary & Invariant Verification

Phase 41 (`v0.33.0`) addresses three critical gameplay flow, player agency, and rules alignment requirements in **Phase 2 Step 2A (Resolve Black Corruption Cubes, Track Spaces & Version Upgrades)** and **Step 2C (End Game Triggers)**:

1. **`INV-RETURN-CHOICE-01` (Step 2A Colored Dice Return Selection Agency):**
   - **Mechanical Requirement:** In `RULES.md` Section 4 Step 2A, when a corruption space triggers *Return X Colored Dice* (`v3.0` Space 5), players choose which owned Colored Module Dice across their mat to return to the Market (or scrap if Purple).
   - **Verification:** Implemented `BaseBot.choose_colored_dice_to_return` utilizing a deterministic 7-tier valuation hierarchy. Across 3,000 matches, **2,881 return events** occurred, returning **2,825 total dice** (429 returned to market supply, 2,396 Purple Specialist dice scrapped).
   - **Tactical Preservation:** Returned dice were overwhelmingly drawn from non-vital zones:
     - **Tier 0 (Glitched Box):** 1,001 dice (35.4%)
     - **Tier 1 (Scanned Box):** 1,199 dice (42.4%)
     - **Tier 2 (In Production Redundant Pure Shield):** 334 dice (11.8%)
     - **Tier 3 (Ready for Release):** 0 dice (0.0%)
     - **Tier 4 (In Production Low Income):** 223 dice (7.9%)
     - **Tier 5 (In Production Star Income):** 68 dice (2.4%)
     - **Tier 6 (In Production Strictly Needed Shield):** **0 dice (0.0%)**
   - **Key Finding:** **89.6%** of all returned dice came from Tiers 0, 1, and 2 (damaged, offline, or redundant defense dice), completely shielding vital defensive shields (`Tier 6`: 0 returned) and protecting active high-value income dice.

2. **`INV-STEP2A-CONTRACTOR-SACRIFICE-01` (White Contractor Sacrifice Enforcement):**
   - **Mechanical Requirement:** White Contractor dice deployed in `in_production_dice` that are selected for demotion in Step 2A (or sacrificed to Green Malware in Step 2B) must be discarded directly to `contractor_supply` and must **never** enter `glitched_dice`.
   - **Verification:** Verified **1,544 Step 2A contractor demotion sacrifices** and **10,032 Step 2B Green Malware contractor sacrifices**.
   - **Pipeline Invariant Check:** Across all 9,000 player-games, **0 White Contractor dice entered `glitched_dice`** (`contractor_glitched_box_violations = 0`, **100% PASSED**).

3. **`INV-SINGULARITY-IMMEDIATE-01` (Immediate Singularity Game Over & Metadata Integrity):**
   - **Mechanical Requirement:** Placing the 6th Black Cube on `v3.0` Space 6 triggers Singularity immediately in Step 2A, terminating the match before Step 2B attack cube damage resolution or Phase 3 operations. Obsolete `add_cubes` on `v3.0` Space 6 are excised. Surviving `in_production_dice` are returned to `ready_for_release_dice` and counted for tiebreaker #2. Corrupted Kernel Space 6 (`Lose 1 Secret`) breaches populate complete Patient Zero metadata.
   - **Verification:** Singularity triggered in **629 games (21.0% of matches)**. Step 2B was skipped in 100% of Singularity terminations. Corrupted Kernel Space 6 caused **88 player breaches**, each verifying **100% populated metadata** (`elimination_round`, `elimination_reason`, `breach_depth`).

---

### 2. Pod-by-Pod Survival, Pacing & Elimination Metrics

#### 2.1 Pacing, Duration & Termination Reasons

| Metric | 2-Player Pod (`2P`) | 3-Player Pod (`3P`) | 4-Player Pod (`4P`) | Combined (`3,000` Games) | Baseline Target |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Matches / Player-Games** | 1,000 / 2,000 | 1,000 / 3,000 | 1,000 / 4,000 | **3,000 / 9,000** | — |
| **Mean Round Length** | **7.98** | **7.54** | **8.72** | **8.08** | 7.0–9.0 rounds |
| **Median Round Length** | 8.0 | 8.0 | 9.0 | **8.0** | 7.0–9.0 rounds |
| **Round Length StDev** | 1.60 | 1.61 | 1.29 | **1.50** | Controlled variance |
| **Round Range (Min - Max)** | 3 - 11 | 3 - 11 | 5 - 11 | **3 - 11** | Min $\ge 3$, Max $\le 12$ |
| **`v1.0` Mean Rounds** | 4.50 | 4.48 | 4.49 | **4.49** | 3.5–4.8 rounds |
| **`v2.0` Mean Rounds** | 2.78 | 2.55 | 3.16 | **2.83** | 2.0–3.2 rounds |
| **`v3.0` Mean Rounds** | 0.71 | 0.51 | 1.08 | **0.77** | 0.4–1.2 rounds |
| **Track Spillover Rate** | 65.0% | 63.9% | 66.7% | **65.2%** | 50%–70% |
| **Mean Spillover Cubes** | 1.24 | 1.21 | 1.23 | **1.23** | 1.0–1.5 cubes |
| **Patient Zero Matches** | 65.3% (653) | 85.4% (854) | 63.2% (632) | **71.3% (2,139)** | Primary trigger |
| **Total Wipeout Matches** | 16.5% (165) | 5.9% (59) | 0.8% (8) | **7.7% (232)** | Safe ceiling ($< 10\%$ multi) |
| **Singularity Matches** | 18.2% (182) | 8.7% (87) | 36.0% (360) | **21.0% (629)** | Healthy organic clock |
| **Round Limit Stalls (Turn 12)** | 0.0% (0) | 0.0% (0) | 0.0% (0) | **0.0% (0)** | Strictly 0.0% |

#### 2.2 Player Survival, Patient Zero & Corporate Secret Distributions

| Metric | 2-Player Pod (`2P`) | 3-Player Pod (`3P`) | 4-Player Pod (`4P`) | Combined (`9,000` PG) |
| :--- | :---: | :---: | :---: | :---: |
| **Surviving Players** | 994 (49.7%) | 1,726 (57.5%) | 3,066 (76.6%) | **5,786 (64.3%)** |
| **Patient Zero Eliminations** | 1,006 (50.3%) | 1,274 (42.5%) | 934 (23.4%) | **3,214 (35.7%)** |
| **Early Deaths ($\le$ Round 4)** | **1.05%** (21) | **1.13%** (34) | **0.00%** (0) | **0.61%** (55) |
| **Winning Score Mean** | **2.77** | **3.96** | **6.52** | **4.42** |
| **Winning Score Median** | 3.0 | 4.0 | 7.0 | **4.0** |
| **Winning Score Range** | -4 to 9 | -2 to 9 | -2 to 13 | **-4 to 13** |
| **Survivor Secrets Mean** | 3.28 | 3.55 | 4.90 | **3.91** |
| **Survivor Secrets Median** | 3.0 | 3.0 | 5.0 | **4.0** |
| **Mean Track: Triage** | 0.25 | 0.26 | 0.26 | **0.26** |
| **Mean Track: Release** | 0.26 | 0.26 | 0.27 | **0.26** |
| **Mean Track: Defense** | 0.40 | 0.38 | 0.39 | **0.39** |
| **Mean Track: Patent** | 0.25 | 0.24 | 0.24 | **0.24** |

---

### 3. Step 2A Return Colored Die Valuation Analysis

Under `INV-RETURN-CHOICE-01`, bots utilize the 7-tier valuation hierarchy:
- **Tier 0 (Glitched Box):** 1,001 returns (35.4%) — Bots eagerly discard glitched dice, clearing damaged units without paying triage costs.
- **Tier 1 (Scanned Box):** 1,199 returns (42.4%) — Dice awaiting graduation are discarded next, preserving active deployment.
- **Tier 2 (In Prod Redundant Pure Shield):** 334 returns (11.8%) — Shields deployed against attack colors that exited 0 cubes are identified and safely returned.
- **Tier 3 (Ready for Release):** 0 returns (0.0%) — Bypassed because players had sufficient damaged, offline, or redundant dice.
- **Tier 4 (In Prod Low Income):** 223 returns (7.9%) — Low-value `$1` income dice sacrificed only when no redundant shields or offline dice were available.
- **Tier 5 (In Prod Star Income):** 68 returns (2.4%) — High-value star income preserved in 97.6% of cases.
- **Tier 6 (In Prod Strictly Needed Shield):** **0 returns (0.0%)** — Strictly needed shields were **100% preserved**, preventing artificial defensive collapse in Step 2B.

---

### 4. Bot Archetype Parity & Ecosystem Health

| Bot Archetype | Matches | Win Rate (Overall) | Survival Rate | Mean Secrets | 2P Win (Surv) | 3P Win (Surv) | 4P Win (Surv) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **AdaptiveBalancedBot** | 1,800 | **61.2%** | **85.4%** | 4.04 | 72.2% (69.0%) | 63.8% (84.5%) | 53.6% (94.4%) |
| **AccelerationistBot** | 1,800 | **44.1%** | **76.4%** | 3.10 | 74.2% (70.0%) | 44.2% (69.8%) | 28.9% (84.5%) |
| **SecOpsTurtleBot** | 1,800 | **32.9%** | **74.1%** | 2.85 | 56.0% (57.5%) | 30.3% (68.2%) | 23.2% (86.8%) |
| **RecklessSaboteurBot** | 1,800 | **23.2%** | **60.7%** | 1.88 | 34.8% (37.8%) | 23.7% (50.2%) | 17.1% (80.0%) |
| **VentureGreedBot** | 1,800 | **5.3%** | **24.9%** | -0.07 | 12.8% (14.2%) | 4.7% (15.0%) | 2.1% (37.6%) |

---

### 5. Client Company & White Hat Operative Balance

#### 5.1 Client Companies (CEOs)

| Client Company | Matches | Win Rate | Survival Rate | Mean Secrets | Mean Cash |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Department of Telecommunications Oversight (DTO)** | 1,541 | **61.7%** | 81.0% | 4.01 | $0.28 |
| **Helix Biomedical Consortium (HELIX)** | 1,503 | **35.4%** | 69.8% | 2.60 | $0.37 |
| **The Prometheus Foundation (PROMETHEUS)** | 1,514 | **32.7%** | 64.3% | 2.23 | $0.44 |
| **Meridian Financial Trust (MERIDIAN)** | 1,491 | **30.0%** | 64.9% | 2.30 | $0.37 |
| **Aegis Defense Relay (AEGIS)** | 1,501 | **26.3%** | 61.5% | 2.08 | $0.21 |
| **Omnidyne Systems (OMNIDYNE)** | 1,450 | **12.3%** | 43.2% | 0.85 | $0.30 |

#### 5.2 White Hat Operatives

| White Hat Operative | Matches | Win Rate | Survival Rate | Mean Secrets | Mean Cash |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **The Spook** | 1,468 | **47.3%** | 76.1% | 3.37 | $0.20 |
| **The Phreaker** | 1,516 | **32.1%** | 59.8% | 2.14 | $0.34 |
| **The Cipher** | 1,511 | **32.0%** | 63.1% | 2.25 | $0.47 |
| **The Acoustic** | 1,533 | **31.6%** | 65.5% | 2.29 | $0.33 |
| **The Prodigy** | 1,523 | **29.6%** | 62.0% | 2.19 | $0.34 |
| **The Operator** | 1,449 | **27.6%** | 59.4% | 1.93 | $0.27 |

---

### 6. Verification Checklist & QA Sign-Off

- [x] **Pacing Stability:** Verified 7.54–8.72 mean rounds across pods (overall 8.08 rounds); zero 12-round cap hits (0.00%).
- [x] **Singularity Trigger Rate:** 21.0% overall (18.2% in 2P, 8.7% in 3P, 36.0% in 4P), establishing a healthy late-game game-over clock.
- [x] **Immediate Singularity Game Over:** Step 2B attack cube resolution and Phase 3 operations were skipped cleanly in all 629 Singularity games.
- [x] **Step 2A Agency Valuation:** 89.6% of returned dice drawn from Tiers 0–2 (Glitched/Scanned/Redundant Shields); 0 strictly needed shields sacrificed.
- [x] **White Contractor Discard Enforcement:** 11,576 total contractor sacrifices across Step 2A and 2B with **zero Glitched Box contamination violations** (100% PASSED).
- [x] **Patient Zero Metadata Integrity:** 100% of Corrupted Kernel Space 6 breaches populated valid metadata (`elimination_round`, `elimination_reason`, `breach_depth`).
- [x] **Regression Free:** All 563 unit tests pass cleanly via WSL.

**QA Recommendation:** Phase 41 (`v0.33.0`) is thoroughly verified, robust, and approved for release.
