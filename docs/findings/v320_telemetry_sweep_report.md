# Rogue Agent v0.32.0 Telemetry Sweep Report
## Phase 39: Blue Variant Rebalance (`B1 — Honeypot Telemetry` & `B3 — Air-Gapped Backup`)

**Date:** 2026-11-05  
**Total Matches:** 3,000 (1,000 matches per pod across [2P, 3P, 4P] = 9,000 player-games)  
**Execution Runtime:** 19.94 seconds (2P: 3.57s, 3P: 5.38s, 4P: 10.99s)  
**Base Seed:** 42  
**Historical Benchmarks:** [v0.30.0 Findings](file:///z:/home/mike/antigravity/rogue-agent/docs/findings/v300_telemetry_sweep_report.md), [v0.31.0 Findings](file:///z:/home/mike/antigravity/rogue-agent/docs/findings/v310_telemetry_sweep_report.md)  
**Raw Telemetry Summary:** [v320_telemetry_summary.json](file:///z:/home/mike/antigravity/rogue-agent/docs/findings/v320_telemetry_summary.json)

---

### 1. Executive Summary & Invariant Validation

Phase 39 (`v0.32.0`) resolves two structural balance anomalies in the Blue (`BLUE // FIREWALL`) central market variant suite identified following the `v0.22.0` CI/CD zero-wear shield overhaul and `v0.31.0` flexible generic defense rollout:

1. **`INV-B1-BOUNTY-01` (`B1 — Honeypot Telemetry`, `$5`):**
   - **Mechanical Calibration:** Calibrated `B1`'s conditional cash bounty from `+$3` down to **`+$2`** (`Block 2 Blue; if 1+ Blue cubes exit the tower and you take 0 Blue damage, gain +$2`).
   - **Verification:** Establishes exact mathematical symmetry with `R2 — Threat Bounty` (`$5`, `Block 2 Red` + `+$2` conditional bounty). Across 1,033 active `B1` games, `B1`'s Face 6 (`★`) was rolled **245 times** and triggered its `+$2` bounty **206 times (`84.1%` trigger rate)**, generating **`$412` in bounty cash** and directly preventing **25 unpaid Red ransomware leaks** (saving 25 Corporate Secrets from dark web leak fines).
2. **`INV-B3-BACKUP-01` (`B3 — Air-Gapped Backup`, `$4`):**
   - **Mechanical Overhaul:** Replaced `B3`'s obsolete pre-`v0.22.0` shield-wear redirection text (which was a complete no-op under zero-wear shield blocking) with a **Dual-Output Defense + Phase 3A Pipeline Recovery** ability: **`[In Production — Defense] Block 1 Blue` + `[In Production — Income] move 1 die from your Glitched Box to your Scanned Box`**.
   - **Verification:** Across 972 active `B3` games, players purchased **906 `B3` Blue dice** (`0.93` per game; `54.7%` of all market purchases in `B3` games). `B3`'s Face 6 (`★`) was rolled **704 times** in Phase 2, with **326 surviving to Phase 3A (`46.3%`)**. Those surviving dice executed **180 active `Glitched -> Scanned` rescues (`55.2%` active rescue rate; `146` empty-glitched no-ops)**, recovering **114 Colored Module Dice (`63.3%`)** and **66 Gray Legacy Dice (`36.7%`)** via the deterministic `(is_colored, cost, die_id)` priority selector.
3. **`INV-GLITCH-SHIELD-PRIO-01` (4-Tuple Green Malware Shield Sacrifice Priority):**
   - **Mechanical Enhancement:** Upgraded `glitch_sort_key` in [`sim/engine/phase2_threat.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py) and [`web/controller/phase3_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase3_actions.py) to a 4-tuple `(is_shield, has_phase3_output, is_gray, cost)` so pure shields with zero Phase 3A output are sacrificed to unblocked Green Malware *before* dual-output Star shields (`B3`, `R1`, `G1`, `G2`).
   - **Verification:** Across the 3,000-match sweep, dual-output Star shields were preserved over pure shields **99 times**, with **`B3 — Air-Gapped Backup` specifically preserved 79 times (`79.8%` of all dual-shield saves)** so it could execute its Phase 3A pipeline triage recovery.
4. **`INV-WEB-UI-SYNC-01` (Full-Stack & PnP Synchronization):**
   - **Verification:** Confirmed end-to-end parity across [`sim/entities.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/entities.py), [`web/controller/phase2_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase2_actions.py), [`web/controller/phase3_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase3_actions.py), [`web/static/js/components/action_dock.js`](file:///z:/home/mike/antigravity/rogue-agent/web/static/js/components/action_dock.js), [`pnp/generate_pnp.py`](file:///z:/home/mike/antigravity/rogue-agent/pnp/generate_pnp.py), and [`RULES.md`](file:///z:/home/mike/antigravity/rogue-agent/RULES.md).

---

### 2. Pod-by-Pod Survival, Pacing & Elimination Metrics (`v0.32.0` vs `v0.31.0`)

#### 2.1 Match Duration, Version Progression & Termination Breakdown

| Metric | 2-Player Pod (`2P`) | 3-Player Pod (`3P`) | 4-Player Pod (`4P`) | Combined (`3,000` Games) | `v0.31.0` Baseline | Target Corridor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Matches / Player-Games** | 1,000 / 2,000 | 1,000 / 3,000 | 1,000 / 4,000 | **3,000 / 9,000** | 3,000 / 9,000 | — |
| **Mean Round Length** | **7.79** | **7.33** | **8.60** | **7.91** | 8.34 / 7.19 / 8.50 | 6.5–8.8 rounds |
| **Median Round Length** | **8.0** | **7.0** | **9.0** | **8.0** | 9.0 / 7.0 / 9.0 | 7.0–9.0 rounds |
| **Round Length StDev** | 1.60 | 1.60 | 1.34 | 1.51 | 1.45 / 1.65 / 1.37 | Controlled variance |
| **Round Range (Min - Max)** | 3 - 11 | 3 - 11 | 5 - 11 | 3 - 11 | 3 - 11 | Min $\ge 3$, Max $\le 12$ |
| **`v1.0` Mean Rounds** | 4.50 | 4.47 | 4.48 | **4.48** | 4.49 / 4.42 / 4.48 | 3.5–4.8 rounds |
| **`v2.0` Mean Rounds** | 2.67 | 2.44 | 3.13 | **2.75** | 3.02 / 2.40 / 3.07 | 1.8–3.2 rounds |
| **`v3.0` Mean Rounds** | 0.62 | 0.42 | 0.99 | **0.68** | 0.84 / 0.38 / 0.95 | 0.3–1.0 rounds |
| **Track Spillover Rate** | 61.6% | 62.9% | 67.3% | **63.9%** | 66.2% / 59.8% / 66.8% | 50%–70% |
| **Mean Spillover Cubes** | 1.22 | 1.20 | 1.23 | **1.22** | 1.24 / 1.19 / 1.23 | 1.0–1.5 cubes |
| **Patient Zero Endings** | 70.8% (708) | 91.6% (916) | 89.7% (897) | **84.0% (2,521)** | Primary trigger | 70%–92% |
| **Total Wipeout Endings** | 28.0% (280) | 8.2% (82) | 3.3% (33) | **13.2% (395)** | Low in 3P/4P | $< 5\%$ in 4P |
| **Singularity Endings** | 1.2% (12) | 0.2% (2) | 7.0% (70) | **2.8% (84)** | Late-game clock | $\ge 0\%$ |
| **Round Limit (Turn 12)** | 0.0% (0) | 0.0% (0) | 0.0% (0) | **0.0% (0)** | 0.0% | Strictly 0.0% |

#### 2.2 Player-Level Survival, Patient Zero & Corporate Secret Metrics

| Metric | 2-Player Pod (`2P`) | 3-Player Pod (`3P`) | 4-Player Pod (`4P`) | Combined (`9,000` PG) | `v0.31.0` Baseline |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Surviving Players** | 732 (36.6%) | 1,573 (52.4%) | 2,507 (62.7%) | **4,812 (53.5%)** | 55.0% |
| **Patient Zero Players** | 1,268 (63.4%) | 1,427 (47.6%) | 1,493 (37.3%) | **4,188 (46.5%)** | 45.0% |
| **Early Deaths ($\le$ Round 4)** | **1.10%** (22) | **1.50%** (45) | **0.00%** (0) | **0.74%** (67) | **0.79%** (71) |
| **Winning Score Mean** | **2.04** | **3.63** | **5.13** | **3.60** | 3.84 |
| **Winning Score Median** | 2.0 | 4.0 | 5.0 | **4.0** | 4.0 |
| **Winning Score Range** | -4 to 9 | -3 to 9 | -3 to 13 | -4 to 13 | -4 to 12 |
| **Survivor Secrets Mean** | **3.14** | **3.42** | **3.96** | **3.66** | 3.72 |
| **Survivor Secrets Median** | 3.0 | 3.0 | 4.0 | **3.5** | 4.0 |
| **All Players Secrets Mean** | 0.45 | 1.35 | 2.03 | **1.45** | 1.70 |
| **Mean Track Level: Triage** | 0.26 | 0.26 | 0.27 | **0.27** | — |
| **Mean Track Level: Release** | 0.26 | 0.26 | 0.27 | **0.26** | — |
| **Mean Track Level: Defense** | 0.40 | 0.38 | 0.40 | **0.40** | — |
| **Mean Track Level: Patent** | 0.25 | 0.24 | 0.25 | **0.24** | — |

#### Key Pacing & Survival Takeaways
- **Rock-Solid Pacing Parity:** Match duration averages **7.79 rounds (2P)**, **7.33 rounds (3P)**, and **8.60 rounds (4P)**, yielding an overall mean of **7.91 rounds** (vs 8.01 rounds in `v0.31.0`). Zero games hit the round limit (`0.0%` stalls).
- **Reduced Early Eliminations:** Early deaths ($\le$ Round 4) improved further from `0.79%` (71 players) in `v0.31.0` down to **`0.74%` (67 players)** across 9,000 player-games (`0.00%` in 4P), as affordable `$4` `B3 — Air-Gapped Backup` dice provide reliable early Blue defense and pipeline recovery.
- **5-Bot Rotation Realism:** Note that the `v0.32.0` sweep rotates uniformly across all **5 bot archetypes** (`AdaptiveBalancedBot`, `SecOpsTurtleBot`, `VentureGreedBot`, `AccelerationistBot`, and `RecklessSaboteurBot`, each playing 1,800 games), providing full coverage of aggressive/saboteur playstyles alongside defensive and balanced archetypes.

---

### 3. Blue Variant Performance Deep Dive (`B1`, `B2`, `B3`)

#### 3.1 Cross-Variant Market Adoption, Win Share & Pipeline Comparison

| Blue Variant Metric | `B1 — Honeypot Telemetry ($5)` | `B2 — Deep R&D Vault ($6)` | `B3 — Air-Gapped Backup ($4)` | Design Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Active Matches** | 1,033 | 995 | 972 | Uniform ~1/3 setup distribution |
| **Active Player-Games** | 3,070 | 2,987 | 2,943 | Total = 9,000 player-games |
| **Blue Dice Purchased** | **394** (`0.38`/game) | **165** (`0.17`/game) | **906** (`0.93`/game) | Price-elastic demand ($4 > $5 > $6) |
| **Total Market Dice Bought** | 1,524 | 1,298 | 1,657 | `B3` stimulates overall market activity |
| **Blue Share of Market Buys** | **25.9%** | **12.7%** | **54.7%** | `B3` is premier `$4` value anchor |
| **Buyer Adoption Rate (% PG)** | **8.5%** (261 / 3,070) | **4.4%** (132 / 2,987) | **21.5%** (632 / 2,943) | High accessibility at `$4` tier |
| **Buyer Win Rate** | **49.8%** (130 / 261) | **51.5%** (68 / 132) | **40.2%** (254 / 632) | Strong positive ROI across all 3 cards |
| **Non-Buyer Win Rate** | 32.1% (903 / 2,809) | 32.5% (927 / 2,855) | 31.1% (718 / 2,311) | Baseline non-buyer win rate ~31–32% |
| **Buyer Win Rate Lift ($\Delta$)** | **`+17.7%`** | **`+19.0%`** | **`+9.1%`** | Scales cleanly with `$4 / $5 / $6` cost |
| **Buyer Survival Rate** | **69.7%** (182 / 261) | **68.9%** (91 / 132) | **59.5%** (376 / 632) | Blue shields directly protect Secrets |
| **Non-Buyer Survival Rate** | 51.2% (1,439 / 2,809) | 52.5% (1,498 / 2,855) | 53.1% (1,226 / 2,311) | +6.4% to +18.5% survival boost |
| **Buyer Mean Ending Secrets** | **2.51** | **2.54** | **2.01** | +0.67 to +1.19 Secret advantage |
| **Non-Buyer Mean Secrets** | 1.32 | 1.40 | 1.34 | Consistent non-buyer baseline |
| **Winners Owning Blue Share** | **12.6%** (130 / 1,033) | **6.8%** (68 / 995) | **26.1%** (254 / 972) | Over 1/4 of `B3` match winners own Blue |
| **Mean Ready Dice Snapshot** | 3.11 | 3.09 | **3.11** | Healthy active pool |
| **Mean Scanned Dice Snapshot** | 1.04 | 1.04 | **1.08** | **`+3.8%` Scanned boost from `B3` rescues** |
| **Mean Glitched Dice Snapshot** | 0.30 | 0.29 | 0.32 | Controlled quarantine debt |

#### 3.2 `B1 — Honeypot Telemetry ($5)` Star & Bounty Telemetry (`INV-B1-BOUNTY-01`)

| `B1` Telemetry Metric | Observed Value | Rate / Per-Event Impact |
| :--- | :---: | :--- |
| **`B1` Star Faces Rolled (Phase 2)** | **245** | Across 394 purchased `B1` dice |
| **Conditional `+$2` Bounty Triggers** | **206** | **`84.1%` trigger rate** when `★` is rolled (`1+` Blue exit & `0` Blue damage) |
| **Total Bounty Cash Generated** | **`$412`** | `$2.00` per trigger (`$1.68` expected value per `★` roll) |
| **Unpaid Red Ransom Leaks Prevented** | **25** | **`12.1%` of bounty triggers** directly prevented a flat 1-Secret dark web leak |

- **Analytical Conclusion (`B1`):** Because `B1`'s `★` face inherently provides `Block 2 Blue` alongside stage-2 reactive generic shields, rolling `B1 ★` achieves a massive **`84.1%` bounty conversion rate** whenever at least 1 Blue cube exits the compiler. At the calibrated `+$2` payout (`INV-B1-BOUNTY-01`), `B1` yields `$1.68` expected cash per `★` roll in addition to `Block 2 Blue`, driving a **49.8% buyer win rate** and **69.7% buyer survival rate** without eclipsing `$5` Red/Yellow economic modules. Furthermore, because `B1`'s bounty credits prior to Step 2B Red ransomware resolution, it prevented **25 dark web Secret leaks** in tight liquidity rounds.

#### 3.3 `B2 — Deep R&D Vault ($6)` Star & Choice Telemetry

| `B2` Telemetry Metric | Observed Value | Rate / Share |
| :--- | :---: | :--- |
| **`B2` Star Faces Rolled** | **88** | Across 165 purchased `B2` dice |
| **Committed to Defense Grid (`Block 1 Blue`)** | **85** | **`96.6%`** committed to protect Corporate Secrets |
| **Kept in Income Slot (`$4 -> +1 Secret` Option)** | **3** | **`3.4%`** retained when Blue defense was already saturated |
| **Phase 3A Secret Purchases (`$4 -> +1 Secret`)** | **0** | High liquidity pressure in Step 2A/2B |

- **Analytical Conclusion (`B2`):** At `$6`, `B2` serves as a specialist luxury module (`51.5%` buyer win rate among selective high-economy buyers, `4.4%` adoption rate). Under intense compiler threat, bots prioritize `B2`'s `Block 1 Blue` shield option `96.6%` of the time.

#### 3.4 `B3 — Air-Gapped Backup ($4)` Dual-Output & Triage Recovery Telemetry (`INV-B3-BACKUP-01` & `INV-GLITCH-SHIELD-PRIO-01`)

| `B3` Telemetry Metric | Observed Value | Rate / Breakdown |
| :--- | :---: | :--- |
| **`B3` Dice Purchased** | **906** | **`54.7%`** of all market dice bought in `B3` games (`0.93`/game) |
| **`B3` Star Faces Rolled in Phase 2** | **704** | Provides `Block 1 Blue` in Phase 2 Step 2B Stage 1 |
| **Dual-Output Shields Preserved Over Pure Shields** | **99** total (**79 `B3`**) | **`INV-GLITCH-SHIELD-PRIO-01`** saved `B3` from Green Malware **79 times** |
| **`B3` Star Faces Surviving to Phase 3A** | **326** | **`46.3%`** survival rate through Phase 2B malware |
| **Active `Glitched -> Scanned` Triage Rescues** | **180** | **`55.2%` active rescue rate** when surviving to Phase 3A |
| **Colored Module Dice Rescued (`Glitched -> Scanned`)** | **114** | **`63.3%`** of all rescued dice (high-value colored modules prioritized) |
| **Gray Legacy Starter Dice Rescued (`Glitched -> Scanned`)** | **66** | **`36.7%`** of all rescued dice |
| **Empty Glitched Box No-Ops** | **146** | **`44.8%`** cleanly no-op when `glitched_dice` is already empty |

- **Analytical Conclusion (`B3`):** Re-architecting `B3 — Air-Gapped Backup` from a dead legacy rule into a `$4` dual-output defense + pipeline triage card (`Block 1 Blue` + `1 Glitched -> Scanned`) is a resounding success:
  1. **Elimination of Dead Rolls:** Previously, rolling Face 6 (`★`) on `B3` did nothing beyond Face 1 (`Block 1 Blue`). Now, `55.2%` of surviving `B3 ★` rolls actively rescue a glitched die in Phase 3A—accelerating it into `scanned_dice` just in time to graduate back to `ready_for_release_dice` during Phase 3B Step 2 (`release_bandwidth`)!
  2. **Smart Malware Counter-Synergy:** Because Phase 2B unblocked Green Malware moves infected production dice into `glitched_dice` *before* Phase 3A income collection, a surviving `B3` die immediately rescues a teammate die that was just glitched by Green Malware in the same round.
  3. **Validated 4-Tuple Sacrifice Priority (`INV-GLITCH-SHIELD-PRIO-01`):** In 79 separate instances, a player with unblocked Green Malware held both a pure shield (e.g., Gray `Block 1 Any` or basic `Block 1 Blue`) and an active `B3 ★` shield. The 4-tuple `glitch_sort_key` sacrificed the pure shield first, preserving `B3 ★` so it could subsequently rescue that glitched die (or a higher-value Colored die) in Phase 3A!

---

### 4. Bot Archetype, Client Company (CEO), White Hat Operative & Patent Tier Balance Tables

#### 4.1 Bot Archetype Performance Matrix (All 9,000 Player-Games; Uniform 5-Bot Rotation)

| Bot Archetype | Total Matches | `2P` Win / Surv | `3P` Win / Surv | `4P` Win / Surv | Overall Survival Rate | Overall Win Rate | Strategic Profile |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`AdaptiveBalancedBot`** | 1,800 | 70.8% / 57.0% | 65.0% / 80.7% | 59.0% / 89.0% | **79.1%** (1,424) | **63.6%** (1,145) | Dynamic threat response & balanced upgrades |
| **`AccelerationistBot`** | 1,800 | 73.3% / 54.0% | 42.2% / 65.0% | 24.6% / 70.9% | **65.2%** (1,173) | **41.3%** (743) | High-tempo version pressure & defensive resilience |
| **`SecOpsTurtleBot`** | 1,800 | 57.0% / 44.0% | 32.0% / 61.5% | 24.1% / 73.6% | **63.0%** (1,134) | **34.1%** (613) | Prioritizes Defense Capacity, Blue dice & Firewall |
| **`RecklessSaboteurBot`** | 1,800 | 34.0% / 19.5% | 20.8% / 40.2% | 15.3% / 62.5% | **45.5%** (819) | **21.3%** (383) | High-variance contractor & aggressive risk-taking |
| **`VentureGreedBot`** | 1,800 | 15.0% / 8.5% | 6.7% / 14.8% | 2.0% / 17.4% | **14.6%** (262) | **6.4%** (116) | Pure greedy income/patent rush (punished by SETEC) |

#### 4.2 Client Company (CEO) Balance Matrix (All 9,000 Player-Games)

| Client Company | Code | Matches | `2P` Win % | `3P` Win % | `4P` Win % | Overall Survival | Overall Win Rate | `v0.31.0` Win Rate | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Dept. of Telecom Oversight** | `DTO` | 1,541 | 72.5% | 61.9% | 50.7% | **73.7%** (1,135) | **59.5%** (917) | 57.3% | High Performer (+1 Secret & Slush Fund) |
| **Helix Biomedical Consortium** | `HELIX` | 1,503 | 59.1% | 34.5% | 26.3% | **57.6%** (866) | **36.7%** (551) | 35.3% | High Performer (Patent Lvl 1 & +2 🔬) |
| **The Prometheus Foundation** | `PROMETHEUS` | 1,514 | 51.6% | 31.0% | 24.6% | **53.2%** (806) | **32.9%** (498) | 34.1% | Optimal Corridor (-1 🔬 Track Discount) |
| **Meridian Financial Trust** | `MERIDIAN` | 1,491 | 44.4% | 28.6% | 22.2% | **53.9%** (804) | **28.9%** (431) | 28.9% | Optimal Corridor ($8 Starting Cash) |
| **Aegis Defense Relay** | `AEGIS` | 1,501 | 45.3% | 32.1% | 18.1% | **52.1%** (782) | **28.7%** (431) | 30.1% | Optimal Corridor (Def Cap 3 & Baffle Echo) |
| **Omnidyne Systems** | `OMNIDYNE` | 1,450 | 22.6% | 10.2% | 8.0% | **28.9%** (419) | **11.9%** (172) | 13.0% | High-Skill Asymmetry (Def Cap 1 / Fast Pipe) |

#### 4.3 White Hat Operative Balance Matrix (All 9,000 Player-Games)

| White Hat Operative | Code | Reserve Cost | Matches | `2P` Win % | `3P` Win % | `4P` Win % | Overall Survival | Overall Win Rate | `v0.31.0` Win Rate | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **The Spook** | `SPOOK` | `$5` | 1,468 | 61.4% | 50.6% | 38.2% | **66.8%** (980) | **47.4%** (696) | 44.3% | High Performer (Burn Notice +1 Secret) |
| **The Acoustic** | `ACOUSTIC` | `$4` | 1,533 | 56.7% | 31.4% | 21.0% | **53.8%** (825) | **32.4%** (497) | 32.0% | Optimal Corridor (`30.8%–32.4%` Band) |
| **The Phreaker** | `PHREAKER` | `$4` | 1,516 | 45.6% | 30.6% | 23.6% | **50.2%** (761) | **31.1%** (471) | 29.4% | Optimal Corridor (`+1.7%` lift with `B3`) |
| **The Cipher** | `CIPHER` | `$6` | 1,511 | 43.4% | 32.4% | 23.3% | **52.3%** (791) | **30.8%** (466) | 33.4% | Optimal Corridor (`+$2` & `+1 🔬`) |
| **The Prodigy** | `PRODIGY` | `$5` | 1,523 | 48.1% | 29.9% | 21.2% | **51.6%** (786) | **29.7%** (453) | 30.5% | Optimal Corridor (Face Manipulation) |
| **The Operator** | `OPERATOR` | `$5` | 1,449 | 45.3% | 25.5% | 23.0% | **46.2%** (669) | **28.8%** (417) | 30.8% | Optimal Corridor (Free Contractor Roll) |

- **Operative Parity Highlight:** Five of the six White Hat Operatives (`ACOUSTIC`, `PHREAKER`, `CIPHER`, `PRODIGY`, `OPERATOR`) cluster within an extraordinarily tight **3.6 percentage point corridor (`28.8%` to `32.4%`)**, with **The Phreaker** gaining `+1.7%` win share (`29.4% -> 31.1%`) thanks to pipeline synergy with `B3 — Air-Gapped Backup`.

#### 4.4 Cryptographic Patent Tier Adoption & Performance Matrix (All 9,000 Player-Games)

| Patent Track Level | Player-Games | Share of Field | `2P` Win / Surv | `3P` Win / Surv | `4P` Win / Surv | Overall Survival | Overall Win Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Level 0 (Base `4 🔬` Patent Cost)** | 6,802 | **75.6%** | 51.8% / 37.9% | 35.8% / 55.5% | 27.3% / 67.2% | **56.8%** (3,863) | **35.6%** (2,419) |
| **Level 1 (`3 🔬` Patent Cost / Helix)** | 2,198 | **24.4%** | 44.6% / 32.7% | 25.6% / 42.8% | 17.9% / 48.7% | **43.2%** (949) | **26.4%** (581) |

*(Note: Patent Level 1 includes `VentureGreedBot` players that rush Patent track upgrades at the expense of Defense Grid capacity, explaining the lower survival rate of Level 1 relative to Defense-first Level 0 players; when paired with Helix Biomedical Consortium's free starting Level 1 Patent track, Helix achieves a **36.7% overall win rate** and **57.6% survival rate**).*

---

### 5. Key Design Conclusions & Formal `v0.32.0` Sign-Off

1. **`B1 — Honeypot Telemetry ($5)` Calibration Validated (`INV-B1-BOUNTY-01`):** Reducing `B1`'s conditional bounty from `+$3` to `+$2` aligns it symmetrically with `R2 — Threat Bounty ($5)`. With an **84.1% bounty trigger rate** (`206 / 245` star rolls), `$412` total bounty cash generated, and **25 unpaid ransom leaks prevented**, `B1` delivers a strong **49.8% buyer win rate** without distorting mid-game cash economies.
2. **`B3 — Air-Gapped Backup ($4)` Dual-Output Overhaul Validated (`INV-B3-BACKUP-01`):** Replacing the obsolete wear-redirect text with `Block 1 Blue` + Phase 3A `1 Glitched -> Scanned` transforms `B3` into the premier `$4` defensive-utility workhorse (`906` dice bought, `54.7%` of market purchases in `B3` games, `26.1%` of match winners owning `B3`, and `180` active `Glitched -> Scanned` rescues recovering `114` Colored and `66` Gray dice).
3. **Green Malware Shield Sacrifice Priority Validated (`INV-GLITCH-SHIELD-PRIO-01`):** The 4-tuple `glitch_sort_key` (`(is_shield, has_phase3_output, is_gray, cost)`) preserved dual-output Star shields over pure shields **99 times** (**79 times specifically for `B3`**), preventing bots and fallback handlers from sacrificing uncollected Phase 3A outputs.
4. **Status:** **OFFICIALLY APPROVED (`v0.32.0` Baseline).**

---
*Report compiled from `scripts/run_v320_telemetry_sweep.py` (`docs/findings/v320_telemetry_summary.json`).*
