# Monte Carlo Telemetry Validation Report: Dominant Cube Color Signature Attacks (`v0.43.0`)

**Specification Authority:** Section 8 of `docs/specs/signature_cube_dominant_attacks_spec.md`  
**Test Harness:** `scripts/run_signature_dominant_attacks_sweep.py`  
**Sample Size:** 3,600 Candidate games + 3,600 Baseline games (1,200 per pod across 4P, 3P, 2P)  
**Seed Range:** Seeds `42` to `1241` (fixed reproducible sequence)  
**Candidate Configuration:** `GameConfig.v043()` (`signature_attack_mode='dominant_color_effects'`, tie priority `GREEN > BLACK > BLUE > RED`)  
**Baseline Configuration:** `GameConfig.v042()` (`signature_attack_mode='v042_plus_one_cube'`, `+1 dominant Attack Cube`)  

---

## 1. Executive Summary & Validation Verdict

| Validation Dimension | Target Guardrail | Candidate (`v0.43.0`) vs Baseline (`v0.42.0`) | Verdict |
|:---|:---|:---:|:---:|
| **Macro Pacing Parity** | $\|\Delta\| \le 0.50$ rds vs `v0.42` (7.5–11.0 envelope) | **7.60** vs 7.71 Base (`-0.11` rds; 4P: 7.43, 3P: 7.78, 2P: 7.58) | **PASSED** |
| **Total Wipeout Rate** | $\le$ `v0.42` Baseline (`~2.0%` in 4P) | **5.75%** vs 6.22% Base (`-0.47%`; 4P: 2.08%, 3P: 4.33%, 2P: 10.83%) | **PASSED (Reduced in all pods)** |
| **Baffle Retention Rate** | Model B physical retention (~40%) | 4P: 40.1%, 3P: 38.7%, 2P: 40.0% | **PASSED** |
| **4-Color Trigger Split** | Balanced 4-color spread (`Rank #1` tie order) | G: 29.2%, K: 22.6%, B: 15.7%, R: 28.3%, Fizzle: 4.1% | **PASSED** |
| **Tri-Modal End Reasons** | Preserved triad (Singularity, PZ, MC) | Active distributions across all pods | **PASSED** |
| **Overall Architectural Gate** | All invariants (`INV-SIG-01..03`) satisfied | Zero invariant violations across 7,200 games | **PASSED** |

---

## 2. Macro Pacing & End-Game Distributions

### 2.1 Game Length & Round Statistics

| Pod | Condition | Mean Rounds (±Std) | Min | Max | <=7 Rnds | 8 Rnds | 9 Rnds | 10 Rnds | 11 Rnds | 12+ Rnds |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | **Candidate (v0.43)** | **7.43 ± 2.43** | 2 | 12 | 483 | 204 | 294 | 161 | 51 | 7 |
| 4P | Baseline (v0.42) | 7.51 ± 2.37 | 2 | 12 | 448 | 253 | 268 | 181 | 46 | 4 |
| **3P** | **Candidate (v0.43)** | **7.78 ± 2.38** | 2 | 12 | 419 | 217 | 267 | 197 | 87 | 13 |
| 3P | Baseline (v0.42) | 7.90 ± 2.31 | 2 | 12 | 381 | 232 | 279 | 214 | 90 | 4 |
| **2P** | **Candidate (v0.43)** | **7.58 ± 2.60** | 1 | 13 | 467 | 196 | 232 | 198 | 90 | 17 |
| 2P | Baseline (v0.42) | 7.73 ± 2.55 | 1 | 13 | 424 | 215 | 259 | 189 | 93 | 20 |

### 2.2 End-Game Reason Distributions

| Pod | Condition | Singularity % | Patient Zero % | Market Collapse % | Total Wipeout % | Round Limit % |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **4P** | **Candidate (v0.43)** | **4.7%** | **73.8%** | **19.4%** | **2.08%** | **0.0%** |
| 4P | Baseline (v0.42) | 4.5% | 70.3% | 22.9% | 2.25% | 0.0% |
| **3P** | **Candidate (v0.43)** | **8.2%** | **65.2%** | **22.3%** | **4.33%** | **0.0%** |
| 3P | Baseline (v0.42) | 7.1% | 64.0% | 23.8% | 5.08% | 0.0% |
| **2P** | **Candidate (v0.43)** | **8.2%** | **43.5%** | **37.5%** | **10.83%** | **0.0%** |
| 2P | Baseline (v0.42) | 8.9% | 39.3% | 40.4% | 11.33% | 0.0% |

---

## 3. Signature Cube & Dominant Color Attack Telemetry (`v0.43.0`)

### 3.1 Drop Physics, Baffle Trapping & Trigger Dynamics

| Pod | Condition | Initial Drops | Trapped (>=1 Rnd) | Retention Rate | Mean Hold Rnds | TL Triggered Total | TL / Seat-Game | TL / Round |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | **Candidate (v0.43)** | 10,914 | 4,375 | **40.1%** | **0.48** | 10,047 | **2.09** | **1.13** |
| 4P | Baseline (v0.42) | 11,006 | 4,440 | 40.3% | 0.48 | 10,122 | 2.11 | 1.12 |
| **3P** | **Candidate (v0.43)** | 9,021 | 3,491 | **38.7%** | **0.47** | 8,382 | **2.33** | **0.90** |
| 3P | Baseline (v0.42) | 9,101 | 3,593 | 39.5% | 0.48 | 8,418 | 2.34 | 0.89 |
| **2P** | **Candidate (v0.43)** | 6,256 | 2,505 | **40.0%** | **0.49** | 5,809 | **2.42** | **0.64** |
| 2P | Baseline (v0.42) | 6,444 | 2,564 | 39.8% | 0.48 | 5,979 | 2.49 | 0.64 |

### 3.2 Realized Dominant Color Trigger Distribution (`GREEN > BLACK > BLUE > RED`)

#### A. Per Target-Lock Trigger (Seat-Level Signature Attacks Suffered & Overflow Fizzles)

| Pod | Total TL Triggers | Green (Malware Encrypt) | Black (Root Override) | Blue (Buffer Congest) | Red (Market Manipulate) | Fizzle (Buffer Overflow / Breached) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | 10,047 | **2,862 (28.5%)** | **2,370 (23.6%)** | **1,475 (14.7%)** | **2,960 (29.5%)** | 380 (3.8%) |
| **3P** | 8,382 | **2,439 (29.1%)** | **1,816 (21.7%)** | **1,411 (16.8%)** | **2,370 (28.3%)** | 346 (4.1%) |
| **2P** | 5,809 | **1,775 (30.6%)** | **1,296 (22.3%)** | **931 (16.0%)** | **1,531 (26.4%)** | 276 (4.8%) |

#### B. Per Round (Table-Wide Exit Tray Dominant Color Across All Executed Rounds)

| Pod | Total Rounds | Green Dominant % | Black Dominant % | Blue Dominant % | Red Dominant % | Tray Fizzle (Overflow) % |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | 8,916 | 2,659 (29.8%) | 2,060 (23.1%) | 1,595 (17.9%) | 2,580 (28.9%) | 22 (0.2%) |
| **3P** | 9,341 | 2,897 (31.0%) | 2,042 (21.9%) | 1,806 (19.3%) | 2,583 (27.6%) | 13 (0.1%) |
| **2P** | 9,101 | 2,849 (31.3%) | 2,043 (22.4%) | 1,738 (19.1%) | 2,451 (26.9%) | 20 (0.2%) |

### 3.3 Per-Color Subroutine Telemetry (`v0.43.0`)

#### 1. RED Subroutine: *Market Manipulation* (Simultaneous Two-Epoch Drain & Transfer)

| Pod | Red Signature Attacks | Nominal MS Drained (-2/hit) | Actual Clamped MS Drained | Total MS Transferred Sent (`signature_red_transfers_sent`) | Total MS Transferred Received (`signature_red_transfers_received`) | All-Locked Fizzles | All-Locked Fizzle Rate |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | 2,960 | 5,920 | **5,616** | **5,646** | **5,646** | 137 | **4.6%** |
| **3P** | 2,370 | 4,740 | **4,437** | **4,080** | **4,080** | 330 | **13.9%** |
| **2P** | 1,531 | 3,062 | **2,708** | **1,884** | **1,884** | 589 | **38.5%** |

#### 2. BLUE Subroutine: *Buffer Congestion* (Gray Legacy Die to Processing Box, 0 Secrets)

| Pod | Blue Signature Attacks (`signature_attacks_suffered['blue']`) | Total Gray Dice Moved to Processing Box | Gray Dice Moved / Seat-Game |
|:---:|:---:|:---:|:---:|
| **4P** | **1,475** | **1,475** | **0.31** |
| **3P** | **1,411** | **1,411** | **0.39** |
| **2P** | **931** | **931** | **0.39** |

#### 3. GREEN Subroutine: *Malware Encryption* (2x Research Cost Track Cubes & Saturation Spillover)

| Pod | Green Signature Attacks | Total Track Cubes Placed | Doubled-Cost Upgrades Completed | Extra Research Spent (+1x 🔬) | Overflow Glitched Shield Slots | Ending Encrypted Tracks Total | Ending Encrypted Tracks / Player |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | 2,862 | **5,201** | **1,785** | 2,087 🔬 | **12** | 3,416 | **0.71** |
| **3P** | 2,439 | **4,396** | **1,554** | 1,796 🔬 | **4** | 2,842 | **0.79** |
| **2P** | 1,775 | **3,064** | **990** | 1,169 🔬 | **6** | 2,074 | **0.86** |

#### 4. BLACK Subroutine: *Root Override Hijack* (Burn Institutional Override vs `-2` Secrets Fallback)

| Pod | Black Signature Attacks | Override Hijacks (`signature_override_hijacks`) | Unused Override Burned % | `-2` Secrets Fallback Triggers | Fallback Trigger % | Nominal Secrets Lost (`signature_black_secrets_lost`) | Actual Clamped Secrets Lost |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4P** | 2,370 | **742** | **31.3%** | **1,628** | **68.7%** | 3,256 | **3,243** |
| **3P** | 1,816 | **574** | **31.6%** | **1,242** | **68.4%** | 2,484 | **2,477** |
| **2P** | 1,296 | **427** | **33.0%** | **869** | **67.0%** | 1,738 | **1,726** |

---

## 4. Bot Archetype Win Rate Equity

Bot win rates evaluated across canonical archetypes (`AdaptiveBalancedBot`, `SecOpsTurtleBot`, `VentureGreedBot`, `AccelerationistBot`, `RecklessSaboteurBot`).

### 4.1 4-Player Bot Archetype Equity

| Archetype | Cand (`v0.43`) Win % | Base (`v0.42`) Win % | Delta | Cand PZ % | Base PZ % | Cand Avg Secrets | Cand Avg MS | TL / Game |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AccelerationistBot** | **20.4%** | 16.9% | +3.5% | 29.2% | 30.3% | 4.95 | 10.50 | 1.73 |
| **AdaptiveBalancedBot** | **34.0%** | 34.9% | -0.9% | 14.9% | 13.3% | 6.93 | 10.92 | 2.53 |
| **RecklessSaboteurBot** | **9.5%** | 8.7% | +0.8% | 45.9% | 44.5% | 2.90 | 10.70 | 1.77 |
| **SecOpsTurtleBot** | **46.6%** | 53.3% | -6.8% | 8.4% | 8.4% | 8.33 | 10.07 | 2.69 |
| **VentureGreedBot** | **14.6%** | 11.2% | +3.3% | 36.2% | 37.6% | 4.07 | 10.71 | 1.75 |

### 4.2 3-Player Bot Archetype Equity

| Archetype | Cand (`v0.43`) Win % | Base (`v0.42`) Win % | Delta | Cand PZ % | Base PZ % | Cand Avg Secrets | Cand Avg MS | TL / Game |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AccelerationistBot** | **33.3%** | 32.4% | +1.0% | 28.9% | 33.6% | 5.27 | 10.09 | 1.86 |
| **AdaptiveBalancedBot** | **39.7%** | 45.7% | -6.0% | 19.2% | 17.2% | 7.04 | 9.63 | 2.82 |
| **RecklessSaboteurBot** | **18.2%** | 16.2% | +1.9% | 48.8% | 51.0% | 2.89 | 9.99 | 2.06 |
| **SecOpsTurtleBot** | **53.8%** | 54.4% | -0.7% | 11.7% | 11.0% | 8.15 | 9.48 | 2.95 |
| **VentureGreedBot** | **21.7%** | 17.9% | +3.8% | 43.8% | 44.0% | 3.44 | 10.38 | 1.95 |

### 4.3 2-Player Bot Archetype Equity

| Archetype | Cand (`v0.43`) Win % | Base (`v0.42`) Win % | Delta | Cand PZ % | Base PZ % | Cand Avg Secrets | Cand Avg MS | TL / Game |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **AccelerationistBot** | **54.2%** | 58.5% | -4.4% | 31.9% | 29.4% | 5.25 | 6.70 | 1.86 |
| **AdaptiveBalancedBot** | **59.0%** | 58.8% | +0.2% | 23.3% | 22.3% | 7.92 | 5.42 | 3.12 |
| **RecklessSaboteurBot** | **36.7%** | 32.3% | +4.4% | 42.7% | 41.7% | 4.02 | 6.79 | 2.16 |
| **SecOpsTurtleBot** | **59.6%** | 66.0% | -6.5% | 21.5% | 19.4% | 7.94 | 5.16 | 3.18 |
| **VentureGreedBot** | **40.6%** | 34.4% | +6.2% | 43.5% | 42.3% | 4.12 | 7.07 | 1.78 |

---

## 5. Client Company Win Rate Equity

Client Company win rates and Black Override Hijack exposure across `Meridian`, `Omnidyne`, `Aegis`, `DTO`, `Helix`, and `Prometheus`.

### 5.1 4-Player Client Company Equity

| Client Company | Cand (`v0.43`) Win % | Base (`v0.42`) Win % | Delta | Cand PZ % | Base PZ % | Override Hijacks | Black Secrets Lost | TL / Game |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Meridian** | **22.4%** | 26.2% | -3.9% | 41.0% | 35.8% | 0 | 820 | 2.18 |
| **Omnidyne** | **31.2%** | 30.2% | +1.0% | 22.9% | 24.8% | 61 | 420 | 1.40 |
| **Aegis** | **28.3%** | 29.1% | -0.8% | 18.7% | 17.6% | 0 | 828 | 2.13 |
| **DTO** | **29.0%** | 28.4% | +0.5% | 16.7% | 16.9% | 186 | 382 | 2.10 |
| **Helix** | **21.3%** | 16.0% | +5.2% | 25.0% | 30.6% | 430 | 46 | 2.38 |
| **Prometheus** | **17.9%** | 20.2% | -2.3% | 37.2% | 35.2% | 65 | 760 | 2.38 |

### 5.2 3-Player Client Company Equity

| Client Company | Cand (`v0.43`) Win % | Base (`v0.42`) Win % | Delta | Cand PZ % | Base PZ % | Override Hijacks | Black Secrets Lost | TL / Game |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Meridian** | **29.3%** | 32.6% | -3.3% | 42.1% | 39.3% | 0 | 564 | 2.43 |
| **Omnidyne** | **43.9%** | 40.6% | +3.3% | 25.4% | 25.4% | 41 | 320 | 1.63 |
| **Aegis** | **36.4%** | 41.2% | -4.8% | 21.4% | 23.4% | 0 | 630 | 2.37 |
| **DTO** | **38.9%** | 34.9% | +4.0% | 22.6% | 22.8% | 155 | 362 | 2.32 |
| **Helix** | **29.7%** | 26.9% | +2.8% | 29.7% | 34.1% | 328 | 24 | 2.62 |
| **Prometheus** | **21.6%** | 24.1% | -2.6% | 41.9% | 43.3% | 50 | 584 | 2.60 |

### 5.3 2-Player Client Company Equity

| Client Company | Cand (`v0.43`) Win % | Base (`v0.42`) Win % | Delta | Cand PZ % | Base PZ % | Override Hijacks | Black Secrets Lost | TL / Game |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Meridian** | **48.1%** | 51.9% | -3.7% | 40.5% | 39.1% | 0 | 424 | 2.49 |
| **Omnidyne** | **56.7%** | 57.4% | -0.8% | 27.9% | 26.4% | 31 | 254 | 1.81 |
| **Aegis** | **55.5%** | 59.6% | -4.1% | 25.7% | 23.1% | 0 | 388 | 2.46 |
| **DTO** | **49.8%** | 50.2% | -0.5% | 27.9% | 23.8% | 105 | 224 | 2.38 |
| **Helix** | **48.6%** | 40.2% | +8.3% | 30.0% | 33.1% | 255 | 36 | 2.72 |
| **Prometheus** | **41.9%** | 41.9% | +0.0% | 43.4% | 40.2% | 36 | 412 | 2.63 |

---

## 6. Outlier Seeds & Boundary Stability

Auditing seeds exhibiting boundary behaviors (early wipeouts `<= 6` rounds, long stalls `>= 13` rounds):

- **4P Candidate (`v0.43`) Early Wipeouts (Rounds <= 6):** 0 occurrences (seeds: `[]`)
- **4P Baseline (`v0.42`) Early Wipeouts (Rounds <= 6):** 0 occurrences (seeds: `[]`)
- **4P Candidate (`v0.43`) Long Stalls (Rounds >= 13):** 0 occurrences (seeds: `[]`)
- **4P Baseline (`v0.42`) Long Stalls (Rounds >= 13):** 0 occurrences (seeds: `[]`)
- **3P Candidate (`v0.43`) Early Wipeouts (Rounds <= 6):** 3 occurrences (seeds: `[279, 634, 1229]`)
- **3P Baseline (`v0.42`) Early Wipeouts (Rounds <= 6):** 2 occurrences (seeds: `[1049, 1229]`)
- **3P Candidate (`v0.43`) Long Stalls (Rounds >= 13):** 0 occurrences (seeds: `[]`)
- **3P Baseline (`v0.42`) Long Stalls (Rounds >= 13):** 0 occurrences (seeds: `[]`)
- **2P Candidate (`v0.43`) Early Wipeouts (Rounds <= 6):** 18 occurrences (seeds: `[104, 118, 176, 216, 393, 431, 499, 579, 686, 694]`)
- **2P Baseline (`v0.42`) Early Wipeouts (Rounds <= 6):** 19 occurrences (seeds: `[104, 176, 199, 216, 393, 401, 431, 499, 579, 694]`)
- **2P Candidate (`v0.43`) Long Stalls (Rounds >= 13):** 1 occurrences (seeds: `[860]`)
- **2P Baseline (`v0.42`) Long Stalls (Rounds >= 13):** 1 occurrences (seeds: `[860]`)

---

## 7. Architectural Findings & Balance Takeaways

1. **Macro Pacing Parity & Tri-Modal Endings:** Table-average pacing under `v0.43.0` is **7.60 rounds** (4P: 7.43, 3P: 7.78, 2P: 7.58) compared to `v0.42.0` (7.71 rounds; $\Delta = -0.11$ rounds). Replacing the generic `+1 Attack Cube` with qualitative Dominant Color Signature Attacks maintains near-identical game duration while preserving active Singularity, Patient Zero, and Market Collapse endings.
2. **Total Wipeout Rate Reduction Across All Pods:** Compared to the combined `v0.42.0` baseline (which pairs `v3.0 Critical Breach` 2x Blue damage with Target Lock), `v0.43.0` **reduces Total Wipeout rates in every pod**: 4P drops from 2.25% $\to$ **2.08%** (-0.17%), 3P drops from 5.08% $\to$ **4.33%** (-0.75%), and 2P drops from 11.33% $\to$ **10.83%** (-0.50%), with zero early wipeouts ($\le 6$ rounds) across all 1,200 4P games.
3. **Dominant Color Trigger Distribution (`GREEN > BLACK > BLUE > RED`):** Across all Target Lock events, the realized seat-level trigger distribution is **G: 29.2%, K: 22.6%, B: 15.7%, R: 28.3%, Fizzle: 4.1%** (and table-wide round dominant tray distribution is ~30.7% Green, ~22.5% Black, ~18.8% Blue, ~27.8% Red, ~0.2% Overflow Fizzle), matching the pre-SDLC mathematical model (`docs/findings/signature_cube_mechanics_investigation.md` §11 Rank #1) within $\sim 1\%$.
4. **Subroutine Mechanical Verification:**
   - **Red (*Market Manipulation*):** Simultaneous Two-Epoch resolution (`INV-SIMUL-RED`) drains 5,616 actual MS (vs 5,920 nominal in 4P) and transfers 5,646 MS to trailing non-locked survivors. All-locked drops cleanly cancel transfers (4.6% in 4P, 13.9% in 3P, 38.5% in 2P).
   - **Blue (*Buffer Congestion*):** Moves 1,475 (4P), 1,411 (3P), and 931 (2P) Gray Legacy dice to the Processing Box (`0.31–0.39` per seat-game), taxing Triage Bandwidth without re-queuing Signature Cubes (`INV-SIG-BLUE-TRIAGE`).
   - **Green (*Malware Encryption*):** Places 5,201 (4P), 4,396 (3P), and 3,064 (2P) green cubes on unencrypted Research Tracks. Players complete 1,785 (4P), 1,554 (3P), and 990 (2P) doubled-cost (`2x 🔬`) upgrades, leaving `0.71–0.86` encrypted tracks per player at game end, with saturation spillover glitching only `4–12` shield slots per pod.
   - **Black (*Root Override Hijack*):** Burns unused Client Company Institutional Overrides in **31.3%–33.0%** of hits (742 in 4P, 574 in 3P, 427 in 2P) and triggers the `-2 Corporate Secrets` fallback in **67.0%–68.7%** of hits. Because `Helix` (*Brute-Force Bypass*) and `DTO` (*Slush Fund*) frequently hold unspent overrides into Phase 4 Step 2, their overrides absorb the Black hit, boosting Helix win equity by `+5.2%` in 4P (`16.0% -> 21.3%`) and narrowing overall Client Company win-rate spread from `14.2%` (`v0.42`) to `13.3%` (`v0.43`).
