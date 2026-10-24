# Rogue Agent — Simulation Findings & Balance Log

Historical record of Monte Carlo simulation sweeps, statistical telemetry, degenerate loop diagnostics, and rule iteration rationale.

---

## 1. Phase 2 Baseline Monte Carlo Sweeps (v0.2 Baseline)

- **Date:** October 2026
- **Sample Size:** 40,000 games total ($N = 1,000$ games per cell across Experiments 1–4)
- **Engine Environment:** `sim/` pure Python 3 via WSL; deterministic master base seed 42. Full dataset archived in `phase2_results.json`.
- **Key Finding:** Critical collapse of game arc. Over **93% of 4P games ended on or before Round 4** (mean 2.8–3.5 rounds in 4P, 4.8 in 2P), with **0.0% Singularity endings**, **75%–92% Insolvency terminations**, and **AccelerationistBot dominating with a 47%–54% win rate**.

### A. Experiment 1: Starting Resources Grid (4P Pod: Balanced, Turtle, Greed, Accel)
Swept Money $\in \{\$3, \$5, \$7, \$9\} \times$ Secrets $\in \{4, 6, 8, 10\}$ ($N = 1,000$ per cell, 16,000 games).

| Starting Money | Starting Secrets | Mean Rounds (Std) | Early Deaths (≤4 Rds) | Singularity % | Insolvency % | Total Breach % | Wipeout % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$3** | 4 | 2.89 (±0.53) | 100.0% | 0.0% | 71.8% | 1.8% | 17.1% |
| **$3** | 6 | 2.94 (±0.56) | 99.7% | 0.0% | 86.9% | 0.2% | 11.1% |
| **$3** | 8 | 2.94 (±0.56) | 99.7% | 0.0% | 90.8% | 0.0% | 8.8% |
| **$3** | 10 | 2.94 (±0.56) | 99.7% | 0.0% | 91.2% | 0.0% | 8.8% |
| **$5** | 4 | 3.09 (±0.59) | 99.7% | 0.0% | 69.2% | 4.3% | 12.1% |
| **$5** (baseline) | 6 (baseline) | 3.16 (±0.62) | 99.3% | 0.0% | 87.1% | 0.4% | 9.9% |
| **$5** | 8 | 3.17 (±0.63) | 99.2% | 0.0% | 91.9% | 0.0% | 7.7% |
| **$5** | 10 | 3.17 (±0.63) | 99.1% | 0.0% | 92.5% | 0.0% | 7.3% |
| **$7** | 4 | 3.31 (±0.69) | 96.2% | 0.0% | 69.1% | 4.7% | 11.2% |
| **$7** | 6 | 3.38 (±0.70) | 96.0% | 0.0% | 83.8% | 0.5% | 10.3% |
| **$7** | 8 | 3.39 (±0.70) | 96.0% | 0.0% | 90.7% | 0.0% | 8.3% |
| **$7** | 10 | 3.40 (±0.71) | 95.2% | 0.0% | 92.4% | 0.0% | 7.5% |
| **$9** | 4 | 3.47 (±0.68) | 94.4% | 0.0% | 69.0% | 6.2% | 8.9% |
| **$9** | 6 | 3.55 (±0.69) | 93.5% | 0.0% | 84.3% | 0.7% | 10.2% |
| **$9** | 8 | 3.56 (±0.70) | 93.2% | 0.0% | 92.2% | 0.0% | 7.5% |
| **$9** | 10 | 3.56 (±0.70) | 93.2% | 0.0% | 93.6% | 0.0% | 6.4% |

- **Takeaway:** Increasing Secrets (4 → 10) had virtually zero impact on game duration (< 0.1 round shift) because Secrets are never spent in Phase 3. Increasing Money ($3 → $9) offered slight relief (2.89 → 3.56 rounds), but even at $9, 93.2% of games ended by Round 4.

### B. Experiment 2: Player-Count Scaling ($N = 1,000$ per count)

| Players | Mean Rounds (Std) | Range | Early Death (≤4 Rds) | Singularity % | Insolvency % | Total Breach % | Wipeout % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2P** | **4.84** (±1.19) | 2–10 | 42.6% | 0.0% | 64.0% | 6.3% | 29.7% |
| **3P** | **4.39** (±1.11) | 2–10 | 60.5% | 0.0% | 62.2% | 12.0% | 16.6% |
| **4P** | **3.16** (±0.62) | 2–5 | 99.3% | 0.0% | 87.1% | 0.4% | 9.9% |

- **Takeaway:** The shared Cube Tower escalates attack strength by the *sum* of all players taking Dirty Income (up to 4 cubes/round added in 4P vs 2 in 2P), while each player's defense remains an individual 4-die pool. 4P collapses 1.7 rounds faster than 2P.

### C. Experiment 3: Dirty Income & Wear Economy ($N = 1,000$ per cell, 18,000 games)
Swept Shield Strength (1 vs 2) $\times$ Dirty Income Cash ($2, $3, $4) $\times$ Patch Cash Cost ($1, $2, $3).

- Modulating Dirty Income from $2 to $4 only shifted mean game length by 0.14 rounds (3.10 to 3.24).
- Players finished matches with ~70% of their dice pool worn into the Unpatched Zone (3.1 to 3.3 unpatched dice out of ~4.5 dice owned).
- Shield strength reduction from Block 2 to Block 1 had minimal effect because players rarely rolled colored shields more than once before someone busted.

### D. Experiment 4: Ecosystem Tournament ($N = 1,000$ per Pod)

- **Pod A (Balanced, Turtle, Greed, Accel):**
  - Mean length: 3.10 rounds.
  - **AccelerationistBot**: **53.6% win rate**, mean score 30.6 VP.
  - **AdaptiveBalancedBot**: 27.0% win rate.
  - **VentureGreedBot**: 11.1% win rate.
  - **SecOpsTurtleBot**: 8.3% win rate (elimination rate 74.8%).
- **Pod B (Balanced, Turtle, Saboteur, Accel):**
  - Mean length: 2.77 rounds.
  - AccelerationistBot: **52.2% win rate**.
- **Pod C (Balanced, Greed, Saboteur, Accel):**
  - Mean length: 2.97 rounds.
  - AccelerationistBot: **47.3% win rate**.

---

## 2. Root Cause Diagnostics

1. **Dual-Use Currency Trap (Capital vs Life Total):** Players start with $5. Buying a $4–$5 die in Round 1 leaves $0–$1 cash. When unblocked Red cubes drop in Round 2, taking a single Red damage at $0 triggers sudden-death Insolvency (`< $0`). Investing in the engine causes immediate death.
2. **Sudden-Death Hair-Trigger:** Any single player reaching `< $0` or `0 Secrets` terminates the match immediately for the entire table. In 4P, the compound survival probability across 4 players is $< 41\%$ on Round 2.
3. **Zero-Risk Aggression of Dirty Income:** Taking Dirty Income grants `+$3` cash immediately. Even if the resulting attack cube slips through next round, it deals only `-$1` damage, leaving the aggressor with net `+$2` cash profit while bankrupting rivals sitting at `$0`.
4. **The Singularity Impossibility Theorem:** In v0.2, Black cubes entered *only* via Dirty Income. Advancing through v1.0, v2.0, and v3.0 in 4P required 15 Black cubes, which meant injecting 15 permanent recycled attack cubes into the tower (18 total attack cubes per round). Players all die by Round 3–4, leaving Singularity at a flat **0.0%**.

---

## 3. Game Designer Recommendations for Rogue Agent v0.3

1. **Corporate Credit Line & Debt Ceiling (`-$5` limit):**
   - Corporations are not eliminated at `$0`. Cash tracks debt down to `-$5`.
   - Patient Zero occurs strictly if cash drops below `-$5` (debt $\ge \$6$).
   - Debt must be repaid in Phase 3 before buying dice or cash-patching. End-game penalty: `-1 VP` per `$1` unpaid debt.
2. **Starting Capital Rebalance:**
   - Starting Money: `$7` (allows buying a $4–$5 die in Round 1 while keeping a $2–$3 cash cushion).
   - Starting Secrets: Retain at `6`. Starting Patches: Retain at `1 🔧`.
3. **Autonomous AI Corruption Clock:**
   - At the start of Phase 1, the Rogue Agent automatically adds `+1 Black Cube` to the Staging Cup.
   - Paces corruption through v1.0 → v2.0 → v3.0 over ~8–10 rounds, unlocking Singularity as a realistic ticking clock.
4. **Dirty Income Rework ("Technical Debt Backlash"):**
   - Gain `+$3` Cash + add `1 Black Cube` to Staging Cup.
   - **Backlash:** Monetizing player must immediately demote `1 Ready die` to their `Unpatched Zone`.
   - Stops spamming: stripping one's own Ready dice limits Dirty Income to 2–3 tactical uses per game.
5. **Version-Driven Attack Scaling:**
   - Upgrade payloads scale attack cubes cleanly (`v1.0` has 3 attack cubes, `v2.0` adds +3, `v3.0` adds +3).
   - Eliminates 4P runaway avalanche while aligning 2P/3P/4P duration within $\pm 0.8$ rounds.
6. **Round-End Patient Zero Resolution:**
   - If a player busts in Phase 2, remaining players complete Phase 3 of that round before final scoring.

---

## 4. Phase 3 Verification Monte Carlo Sweeps (v0.3 Baseline)

- **Date:** October 2026
- **Sample Size:** 40,000 games total across Experiments 1–4 ($N = 1,000$ games per cell, seed 42 via WSL).
- **Core Summary:** [RULES.md](./RULES.md) v0.3 successfully resolved the early-death crisis: **early deaths (< Round 5) dropped from 96.0% to 0.0%**, and mean game length extended from **3.16 to 6.09 rounds in 4P (and 7.94 rounds in 3P)**. However, `AccelerationistBot` established an exploitative monopoly (**81.5%–87.5% win rate**) by combining Dirty Income cash reserves against Red ransom with hard Blue shielding.

### A. Experiment 1: Starting Resources Grid ($N = 1,000$ per cell)

| Starting Money | Starting Secrets | Mean Rounds (Std) | Early Deaths (< R5) | Singularity % | Patient Zero % | Wipeout % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$7 (baseline)** | **6 (baseline)** | **6.09** (±0.59) | **0.0%** | **1.0%** | **84.0%** | **15.0%** |
| **$7** | 8 | 6.22 (±0.61) | 0.0% | 2.0% | 88.0% | 10.0% |
| **$9** | 6 | 6.38 (±0.64) | 0.0% | 3.5% | 89.5% | 7.0% |
| **$9** | 8 | 6.50 (±0.68) | 0.0% | 6.0% | 90.0% | 4.0% |

- **Key Takeaways:** 
  1. The combination of $7 starting capital and the non-negative cash rule eliminated early bankruptcies.
  2. Starting Secrets (6 vs 8) provides modest pacing elasticity (+0.2 rounds) without breaking game flow.

### B. Experiment 2: Player-Count Scaling ($N = 1,000$ per count)

| Players | Mean Rounds (Std) | Singularity % | Patient Zero % | Wipeout % | Dirty Income / Game |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2P** | 6.68 (±0.84) | 13.0% | 52.0% | 35.0% | 0.86 |
| **3P** | 7.94 (±1.03) | 3.5% | 83.5% | 13.0% | 1.56 |
| **4P** | 6.14 (±0.59) | 1.5% | 83.5% | 15.0% | 6.34 |

- **Key Takeaways:** 
  1. 3P achieved the ideal round arc (7.94 rounds).
  2. 2P unlocked Singularity (13.0%) due to lower aggregate attack cube recycling, but suffered higher simultaneous wipeouts (35.0%) due to lack of player diversity to absorb tower bursts.
  3. 4P sees 6.34 Dirty Income uses per game, accelerating cube drop counts and causing breach around Round 6.

### C. Experiment 3: Dirty Income & Patch Cost Economy

| Config (Dirty Cash / Patch Cost) | Mean Rounds | Mean Dirty Income / Gm | Wipeout % |
| :---: | :---: | :---: | :---: |
| **$3 Dirty / $2 Patch (Baseline)** | 6.09 | 6.43 | 15.0% |
| **$4 Dirty / $2 Patch** | 6.13 | 6.89 | 4.0% |
| **$3 Dirty / $1 Patch** | 6.26 | 5.91 | 3.0% |

- **Key Takeaways:** Cheaper patch costs ($1) reduce wipeouts to 3.0% and slightly extend game length by allowing defensive bots to maintain ready dice pools.

### D. Experiment 4: Ecosystem Tournament Pods ($N = 1,000$ per Pod)

- **Pod A (Balanced, Turtle, Greed, Accel):** Mean 5.55 rounds. End triggers: Singularity 0.5%, Patient Zero 88.0%, Wipeout 11.5%.
  - **AccelerationistBot: 81.5% win rate** (mean score 36.4 VP)
  - VentureGreedBot: 11.0%
  - AdaptiveBalancedBot: 5.0%
  - SecOpsTurtleBot: 2.5%
- **Pod B (Balanced, Turtle, Saboteur, Accel):** Mean 4.47 rounds. End triggers: Singularity 2.0%, Patient Zero 91.0%, Wipeout 7.0%.
  - **AccelerationistBot: 87.5% win rate**
  - AdaptiveBalancedBot: 5.5%
  - SecOpsTurtleBot: 4.0%
  - RecklessSaboteurBot: 3.0%
- **Pod C (Balanced, Greed, Saboteur, Accel):** Mean 4.49 rounds. End triggers: Singularity 0.5%, Patient Zero 87.5%, Wipeout 12.0%.
  - **AccelerationistBot: 83.5% win rate**
  - VentureGreedBot: 7.0%
  - RecklessSaboteurBot: 5.5%
  - AdaptiveBalancedBot: 4.0%

### E. Root Cause Analysis & v0.4 Tuning Roadmap

1. **The Cash-Ransom Shield Exploitation:** AccelerationistBot's frequent Dirty Income provides a large cash buffer that absorbs Red attacks, while it commits all shields to Blue (Secrets). Conservative bots stay cash-strapped from patching, resulting in Red attacks leaking into Secrets.
2. **Next Cycle Action Items:**
   - **TUNE 1:** Dirty Income costs `1 Corporate Secret` in addition to demoting 1 Ready die.
   - **TUNE 2:** Unpaid Red ransom can be absorbed by `🔧` Patch tokens before leaking Secrets.
   - **TUNE 3:** Flat `4-space` Corruption Track per version to make 4P Singularity competitive (12 Black cubes instead of 15).
   - **BOT FIX:** Update Adaptive/Turtle heuristics to prioritize Blue shields over Red, and maintain a $2 cash reserve before cash-patching.
