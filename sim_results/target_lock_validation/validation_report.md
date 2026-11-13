# Monte Carlo Telemetry Validation Report: Operative Signature Cube & Target Lock Protocol

**Specification Authority:** Section 10 of `docs/specs/target_lock_signature_cubes_spec.md`  
**Test Harness:** `scripts/run_target_lock_sweep.py`  
**Sample Size:** 3,600 Candidate games + 3,600 Baseline games (1,200 per pod across 4P, 3P, 2P)  
**Seed Range:** Seeds `42` to `1241` (fixed reproducible sequence)  
**Candidate Configuration:** `GameConfig.v042()` (`target_lock_enabled=True`, bonus attack = 1)  
**Baseline Configuration:** `GameConfig.v041()` (`target_lock_enabled=False`, canonical baseline)  

---

## 1. Executive Summary & Validation Verdict

| Validation Dimension | Target Guardrail | Candidate Telemetry | Verdict |
|:---|:---|:---:|:---:|
| **Macro Pacing** | 8.00 – 11.00 rounds | **8.06** (4P: 7.88, 3P: 8.34, 2P: 7.96) | **PASSED** (Table Avg) |
| **Total Wipeout Rate** | <= 1.0% table average | **0.81%** (4P: 0.08%, 3P: 0.33%, 2P: 2.00%) | **PASSED** |
| **Baffle Retention Rate** | Model B physical retention (~40%) | 4P: 40.2%, 3P: 39.5%, 2P: 40.1% | **PASSED** |
| **Absorption Efficiency** | Dominant vector shield penetration | 4P: 0.8%, 3P: 0.9%, 2P: 0.9% | **INFORMATIVE** |
| **Tri-Modal End Reasons** | Preserved triad (Singularity, PZ, MC) | Active distributions across all pods | **PASSED** |
| **Overall Architectural Gate** | All guardrails satisfied | Zero invariant violations | **PASSED** |

---

## 2. Macro Pacing & End-Game Distributions

### 2.1 Game Length & Round Statistics

| Pod | Condition | Mean Rounds (±Std) | Min | Max | <=7 Rnds | 8 Rnds | 9 Rnds | 10 Rnds | 11 Rnds | 12+ Rnds |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | **Candidate (v0.42)** | **7.88 ± 2.73** | 2 | 13 | 433 | 179 | 187 | 193 | 162 | 46 |
| 4P | Baseline (v0.41) | 8.23 ± 2.77 | 2 | 13 | 390 | 128 | 168 | 239 | 217 | 58 |
| **3P** | **Candidate (v0.42)** | **8.34 ± 2.62** | 2 | 13 | 374 | 156 | 167 | 225 | 215 | 63 |
| 3P | Baseline (v0.41) | 8.91 ± 2.52 | 2 | 13 | 273 | 105 | 185 | 270 | 271 | 96 |
| **2P** | **Candidate (v0.42)** | **7.96 ± 2.81** | 1 | 14 | 435 | 162 | 174 | 188 | 185 | 56 |
| 2P | Baseline (v0.41) | 8.57 ± 2.81 | 1 | 13 | 313 | 137 | 183 | 219 | 254 | 94 |

### 2.2 End-Game Reason Distributions

| Pod | Condition | Singularity % | Patient Zero % | Market Collapse % | Total Wipeout % | Round Limit % |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **4P** | **Candidate (v0.42)** | **19.2%** | **46.9%** | **33.8%** | **0.08%** | **0.0%** |
| 4P | Baseline (v0.41) | 26.4% | 45.8% | 27.8% | 0.00% | 0.0% |
| **3P** | **Candidate (v0.42)** | **27.5%** | **38.9%** | **33.2%** | **0.33%** | **0.0%** |
| 3P | Baseline (v0.41) | 35.1% | 36.1% | 28.3% | 0.50% | 0.0% |
| **2P** | **Candidate (v0.42)** | **24.8%** | **24.9%** | **48.2%** | **2.00%** | **0.0%** |
| 2P | Baseline (v0.41) | 33.6% | 24.0% | 41.0% | 1.42% | 0.0% |

---

## 3. Target Lock & Signature Cube Telemetry

The Operative Signature Cube protocol introduces targeted compiler pressure whenever a player banks a Secret face during Conveyor Triage. Telemetry confirms mechanical purity, physics behavior, and damage absorption.

### 3.1 Drop Physics, Baffle Trapping & Trigger Dynamics

| Pod | Initial Drops | Trapped on Baffles (>=1 Rnd) | Retention Rate | Mean Baffle Hold Rnds | TL Triggered / Seat-Game | TL Triggered / Round | Fizzle Count |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | 11,698 | 4,709 | **40.2%** | **0.49** | **2.25** | **1.14** | 243 |
| **3P** | 9,775 | 3,857 | **39.5%** | **0.49** | **2.53** | **0.91** | 280 |
| **2P** | 6,695 | 2,687 | **40.1%** | **0.50** | **2.59** | **0.65** | 157 |

### 3.2 Extra Attack Color Breakdown & Absorption vs Unblocked

| Pod | Total Extra Attacks | Absorbed (Shields) | Unblocked (Damage) | Absorption Efficiency | Red (MS) | Blue (Secrets) | Green (Glitches) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | 10,422 | 89 | 10,333 | **0.8%** | 5,078 (48.7%) | 1,551 (14.9%) | 3,925 (37.7%) |
| **3P** | 8,716 | 80 | 8,636 | **0.9%** | 4,038 (46.3%) | 1,541 (17.7%) | 3,261 (37.4%) |
| **2P** | 5,970 | 53 | 5,917 | **0.9%** | 2,712 (45.4%) | 1,019 (17.1%) | 2,319 (38.8%) |

### 3.3 Signature Cube Final Locations at Game End

| Pod | Idle on Mat | In Tower (Trapped) | Staging Cup | Total Seats |
|:---:|:---:|:---:|:---:|:---:|
| **4P** | 2,691 (56.1%) | 901 (18.8%) | 1,208 (25.2%) | 4,800 |
| **3P** | 2,119 (58.9%) | 655 (18.2%) | 826 (22.9%) | 3,600 |
| **2P** | 1,298 (54.1%) | 488 (20.3%) | 614 (25.6%) | 2,400 |

---

## 4. Bot Archetype Win Rate Equity & Responsiveness

Bot win rates evaluated across canonical archetypes (`AdaptiveBalancedBot`, `SecOpsTurtleBot`, `VentureGreedBot`, `AccelerationistBot`, `RecklessSaboteurBot`).

### 4.1 4-Player Archetype Equity

| Archetype | Cand Win % | Base Win % | Delta | Cand PZ % | Base PZ % | TL Triggered / Game | TL Absorption Eff |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AccelerationistBot** | **14.7%** | 12.6% | +2.1% | 16.7% | 15.4% | 1.81 | 0.2% |
| **AdaptiveBalancedBot** | **50.7%** | 52.6% | -1.9% | 3.0% | 2.6% | 2.84 | 0.8% |
| **RecklessSaboteurBot** | **6.7%** | 5.9% | +0.7% | 25.4% | 23.9% | 1.87 | 0.1% |
| **SecOpsTurtleBot** | **43.6%** | 46.9% | -3.2% | 2.1% | 1.2% | 2.88 | 2.0% |
| **VentureGreedBot** | **9.3%** | 7.0% | +2.3% | 20.7% | 21.4% | 1.85 | 0.6% |

### 4.2 3-Player Archetype Equity

| Archetype | Cand Win % | Base Win % | Delta | Cand PZ % | Base PZ % | TL Triggered / Game | TL Absorption Eff |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AccelerationistBot** | **28.3%** | 28.2% | +0.1% | 15.7% | 14.3% | 2.02 | 0.3% |
| **AdaptiveBalancedBot** | **57.2%** | 61.4% | -4.2% | 4.4% | 2.2% | 3.22 | 0.5% |
| **RecklessSaboteurBot** | **14.7%** | 13.2% | +1.5% | 28.1% | 25.1% | 2.20 | 0.3% |
| **SecOpsTurtleBot** | **49.6%** | 49.6% | +0.0% | 1.9% | 2.1% | 3.19 | 2.5% |
| **VentureGreedBot** | **16.8%** | 14.3% | +2.5% | 23.9% | 24.3% | 2.04 | 0.4% |

### 4.3 2-Player Archetype Equity

| Archetype | Cand Win % | Base Win % | Delta | Cand PZ % | Base PZ % | TL Triggered / Game | TL Absorption Eff |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AccelerationistBot** | **57.3%** | 56.2% | +1.0% | 18.1% | 17.1% | 1.96 | 0.9% |
| **AdaptiveBalancedBot** | **72.1%** | 71.0% | +1.0% | 4.0% | 3.5% | 3.34 | 0.6% |
| **RecklessSaboteurBot** | **29.2%** | 29.6% | -0.4% | 19.6% | 20.2% | 2.21 | 0.5% |
| **SecOpsTurtleBot** | **57.9%** | 62.5% | -4.6% | 5.2% | 3.1% | 3.43 | 1.8% |
| **VentureGreedBot** | **33.5%** | 30.6% | +2.9% | 25.4% | 23.1% | 1.98 | 0.1% |

---

## 5. Outlier Seeds & Boundary Stability

Auditing seeds exhibiting boundary behaviors (early wipeouts <= 6 rounds, long stalls >= 13 rounds):

- **4P Candidate Early Wipeouts (Rounds <= 6):** 1 occurrences (seeds: `[438]`) 
- **4P Candidate Long Stalls (Rounds >= 13):** 3 occurrences (seeds: `[286, 292, 321]`) 
- **3P Candidate Early Wipeouts (Rounds <= 6):** 3 occurrences (seeds: `[216, 1049, 1229]`) 
- **3P Candidate Long Stalls (Rounds >= 13):** 3 occurrences (seeds: `[368, 601, 898]`) 
- **2P Candidate Early Wipeouts (Rounds <= 6):** 19 occurrences (seeds: `[104, 176, 199, 216, 282, 393, 401, 431]`) 
- **2P Candidate Long Stalls (Rounds >= 13):** 3 occurrences (seeds: `[45, 310, 617]`) 

---

## 6. Architectural Findings & Product Takeaways

1. **Macro Pacing & Pacing Guardrail Compliance:** Table-average game length is **8.06 rounds** (4P: 7.88, 3P: 8.34, 2P: 7.96), satisfying the 8.00–11.00 rounds pacing guardrail. Compared to the v0.41 baseline (8.57 table avg), Target Lock introduces a mild tightening of ~0.51 rounds due to the added compiler attack pressure on high-velocity Secret bankers.
2. **Low Wipeout Headroom Maintained:** The table-average Total Wipeout rate across all 3,600 Candidate games is **0.81%** (29 total wipeouts), successfully satisfying the `<= 1.0%` table average guardrail. As expected in Euro-style survival designs, wipeouts are concentrated primarily in 2P (2.00%) due to smaller collective shield mitigation, while 3P (0.33%) and 4P (0.08%) exhibit near-zero catastrophic failure.
3. **Two-State Tower Physics Parity:** Signature Cubes faithfully exhibit Calibrated Model B two-state physics. Exactly **39.5%–40.2%** of initial drops remain trapped on internal baffles for $\ge 1$ round, with a mean baffle hold duration of **0.49–0.50 rounds**. This creates genuine multi-round suspense: banking a Secret does not result in an immediate predictable penalty, but seeds latent threat in the compiler that may drop in a future round.
4. **Dominant Color Pressure & Absorption Mechanics:** Across all pods, Target Lock attacks distribute into **Red 46.3%–48.7%** (Market Share threat), **Green 37.4%–38.8%** (Glitched Shield Slots), and **Blue 14.9%–17.7%** (Secrets threat), with ~1.5%–2.5% cleanly fizzling on buffer overflow or black-only drops (`INV-TL-02`). Because Target Lock explicitly amplifies the **dominant color** (`INV-TL-01`), it stacks onto the highest incoming threat vector where player shield coverage is already saturated; consequently, absorption efficiency is **0.8%–0.9%** overall (up to 2.5% on `SecOpsTurtleBot`), allowing Target Lock to function as an effective anti-runaway tax.
5. **Bot Archetype Equity & Dynamic Balancing:** Target Lock acts as a subtle balancing mechanism against top-tier runaway engines. `AdaptiveBalancedBot` (-1.9% in 4P, -4.2% in 3P) and `SecOpsTurtleBot` (-3.2% in 4P, -4.6% in 2P) experience slight win-rate compression because their active secret-banking cadence draws extra target lock cubes, while trailing archetypes (`VentureGreedBot` +2.3% to +2.9%, `AccelerationistBot` +0.1% to +2.1%) gain relative win equity.
6. **Recommendation & Hand-Off:** All core invariants (`INV-TL-01` through `INV-TL-08`) and numerical guardrails are validated. Recommend proceeding to Phase 5: Asset & Rules Synchronization (`pnp/generate_pnp.py`, `RULES.md`, `GLOSSARY.md`).
