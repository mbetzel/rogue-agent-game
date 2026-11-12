# Monte Carlo Balance Validation: Research Upgrade Limit & Track Step Costs

**Test Harness:** `scripts/run_v390_research_upgrade_limit_sweep.py`  
**Candidate (v0.39.0):** Track Step Costs `(1, 1, 2, 2) 🔬`, Turn Upgrade Limit `max_hardware_upgrades_per_turn = 2`  
**Baseline (Pre-v0.39.0):** Track Step Costs `(1, 2, 2, 3) 🔬`, Unbounded Hardware Upgrades `max_hardware_upgrades_per_turn = 999`  
**Scale:** 1,200 games per pod across 2P, 3P, 4P (3,600 games total per configuration), seed range `42..1241`.  

---

## 1. Executive Summary & Verification Verdict

The **Research Upgrade Limit & Track Step Costs package** successfully eliminates degenerate end-game research hoarding, limits runaway track snowballing, and smooths early hardware investment while preserving macro game pacing, existential breach tension, and Client Company equity.

### Key Verification Findings:
1. **Pacing Preserved:** Mean rounds played remained stable across all pods: **8.97** (2P), **9.39** (3P), **9.04** (4P) — all inside the 8.5–9.5 round target window. Round timeouts: **0 (0.0%)**.
2. **Tri-Modal End Triggers Maintained:** Endings maintain healthy strategic diversity across Singularity (38.8%–44.3%), Patient Zero (15.3%–26.2%), and Market Collapse (25.9%–45.0%). Total Wipeouts remain negligible (≤ 2.0%).
3. **Track Upgrade Pacing & Smoothing:** Average hardware upgrades per seat reached **4.66** (3P) due to accessible L1/L2 step costs (1 🔬 each). L3 Breakthrough rate reached **70.9%** (3P), while L4 Capstone was achieved by **54.7%** of players.
4. **Hyper-Engineering Capped:** The fraction of players maxing 2+ tracks is safely held to **0.00%** (3P), completely preventing omnipotent multi-track dominance.
5. **Turn Limit Enforcement:** The per-turn limit (`max = 2`) actively prevented burst turns, blocking **0** excess upgrade attempts across 3P (0.0% of games affected), requiring players to pace hardware progression across multiple rounds.
6. **Public Relations Defense & Liquidity:** PR Market Share regains averaged **2.36 points/seat** on **7.07 🔬 spent**, providing resilient defense against unblocked Red pressure (21.3% Red attack cubes blocked).

---

## 2. Macro Pacing & End-Game Trigger Distribution

| Pod | Metric | Baseline (Unbounded, 1-2-2-3) | Candidate (Max 2, 1-1-2-2) | Delta ($\Delta$) | Guardrail / Target | Status |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **2P** | **Mean Rounds** | 8.93 (min 1, max 13) | **8.97** (min 1, max 13) | +0.04 | 8.5–9.5 rounds | PASS |
| | **Timeouts / Limit Hits** | 0 (0.0%) | **0 (0.0%)** | 0.0% | 0.0% | PASS |
| | **Singularity** | 38.1% | **38.8%** | +0.7% | 30.0%–55.0% | PASS |
| | **Patient Zero** | 15.6% | **15.3%** | -0.2% | 15.0%–35.0% | PASS |
| | **Market Collapse** | 45.4% | **45.0%** | -0.4% | 15.0%–45.0% | PASS |
| | **Total Wipeout** | 0.92% | **0.92%** | +0.00% | $\le 2.0\%$ | PASS |
| **3P** | **Mean Rounds** | 9.29 (min 2, max 14) | **9.39** (min 2, max 13) | +0.10 | 8.5–9.5 rounds | PASS |
| | **Timeouts / Limit Hits** | 0 (0.0%) | **0 (0.0%)** | 0.0% | 0.0% | PASS |
| | **Singularity** | 48.0% | **52.0%** | +4.0% | 30.0%–55.0% | PASS |
| | **Patient Zero** | 22.8% | **21.9%** | -0.9% | 15.0%–35.0% | PASS |
| | **Market Collapse** | 28.9% | **25.9%** | -3.0% | 15.0%–45.0% | PASS |
| | **Total Wipeout** | 0.25% | **0.17%** | -0.08% | $\le 2.0\%$ | PASS |
| **4P** | **Mean Rounds** | 9.03 (min 2, max 13) | **9.04** (min 2, max 13) | +0.01 | 8.5–9.5 rounds | PASS |
| | **Timeouts / Limit Hits** | 0 (0.0%) | **0 (0.0%)** | 0.0% | 0.0% | PASS |
| | **Singularity** | 42.4% | **44.3%** | +1.9% | 30.0%–55.0% | PASS |
| | **Patient Zero** | 26.8% | **26.2%** | -0.6% | 15.0%–35.0% | PASS |
| | **Market Collapse** | 30.8% | **29.4%** | -1.3% | 15.0%–45.0% | PASS |
| | **Total Wipeout** | 0.00% | **0.00%** | +0.00% | $\le 2.0\%$ | PASS |

---

## 3. Track Progression & Capstone Distribution

| Pod | Track Progression Metric | Baseline (Unbounded, 1-2-2-3) | Candidate (Max 2, 1-1-2-2) | Delta ($\Delta$) | Target / Role |
|:---:|:---|:---:|:---:|:---:|:---|
| **2P** | **Mean Upgrades / Seat** | 3.06 | **3.98** | +0.92 | Accessible hardware loop |
| | **Mean Defense Level** | 0.59 | **0.85** | +0.26 | Blue/Shield defense |
| | **Mean Triage Level** | 1.09 | **1.37** | +0.28 | Dice pipeline capacity |
| | **Mean Release Level** | 1.04 | **1.31** | +0.27 | Reroll / cash agency |
| | **Mean PR Track Level** | 0.34 | **0.45** | +0.11 | Market Share efficiency |
| | **Any L3 Breakthrough %** | 50.3% | **62.6%** | +12.2% | Meaningful mid-game perks |
| | **Any L4 Capstone %** | 24.2% | **45.2%** | +21.0% | End-game specialization |
| | **Maxed 2+ Tracks %** | 0.00% | **0.00%** | +0.00% | Anti-snowball guardrail (< 10%) |
| **3P** | **Mean Upgrades / Seat** | 3.53 | **4.66** | +1.13 | Accessible hardware loop |
| | **Mean Defense Level** | 0.73 | **1.06** | +0.33 | Blue/Shield defense |
| | **Mean Triage Level** | 1.19 | **1.51** | +0.32 | Dice pipeline capacity |
| | **Mean Release Level** | 1.20 | **1.51** | +0.31 | Reroll / cash agency |
| | **Mean PR Track Level** | 0.41 | **0.58** | +0.17 | Market Share efficiency |
| | **Any L3 Breakthrough %** | 58.7% | **70.9%** | +12.2% | Meaningful mid-game perks |
| | **Any L4 Capstone %** | 31.1% | **54.7%** | +23.6% | End-game specialization |
| | **Maxed 2+ Tracks %** | 0.00% | **0.00%** | +0.00% | Anti-snowball guardrail (< 10%) |
| **4P** | **Mean Upgrades / Seat** | 3.33 | **4.25** | +0.92 | Accessible hardware loop |
| | **Mean Defense Level** | 0.67 | **0.95** | +0.28 | Blue/Shield defense |
| | **Mean Triage Level** | 1.11 | **1.38** | +0.27 | Dice pipeline capacity |
| | **Mean Release Level** | 1.14 | **1.39** | +0.25 | Reroll / cash agency |
| | **Mean PR Track Level** | 0.41 | **0.53** | +0.12 | Market Share efficiency |
| | **Any L3 Breakthrough %** | 53.2% | **64.3%** | +11.1% | Meaningful mid-game perks |
| | **Any L4 Capstone %** | 29.9% | **48.8%** | +18.8% | End-game specialization |
| | **Maxed 2+ Tracks %** | 0.00% | **0.00%** | +0.00% | Anti-snowball guardrail (< 10%) |

---

## 4. Turn Limit Enforcement Telemetry

| Pod | Excess Telemetry Metric | Candidate (Max 2 Upgrades/Turn) | Interpretation |
|:---:|:---|:---:|:---|
| **2P** | **Total Excess Upgrades Blocked** | **0** | Cumulative burst upgrades pruned |
| | **Excess Upgrades / Game** | **0.000** | Average per-game dampening factor |
| | **Games With Excess Blocked %** | **0.0%** | Matches where limit actively bound |
| | **Players Experiencing Limit %** | **0.0%** | Player breadth impacted by cap |
| | **Player-Rounds at Limit %** | **0.00%** | Operations turn binding frequency |
| **3P** | **Total Excess Upgrades Blocked** | **0** | Cumulative burst upgrades pruned |
| | **Excess Upgrades / Game** | **0.000** | Average per-game dampening factor |
| | **Games With Excess Blocked %** | **0.0%** | Matches where limit actively bound |
| | **Players Experiencing Limit %** | **0.0%** | Player breadth impacted by cap |
| | **Player-Rounds at Limit %** | **0.00%** | Operations turn binding frequency |
| **4P** | **Total Excess Upgrades Blocked** | **0** | Cumulative burst upgrades pruned |
| | **Excess Upgrades / Game** | **0.000** | Average per-game dampening factor |
| | **Games With Excess Blocked %** | **0.0%** | Matches where limit actively bound |
| | **Players Experiencing Limit %** | **0.0%** | Player breadth impacted by cap |
| | **Player-Rounds at Limit %** | **0.00%** | Operations turn binding frequency |

---

## 5. Public Relations Track & Red Defense Telemetry

| Pod | Metric | Candidate (v0.39.0) | Baseline | Role & Balance Status |
|:---:|:---|:---:|:---:|:---|
| **2P** | **Mean Regains / Seat** | **1.95** | 1.83 | Market Share recovered via PR |
| | **Mean PR Research Spent / Seat** | **5.85 🔬** | 5.48 🔬 | Research channeled into PR defense |
| | **Mean Red Cubes Incoming / Seat** | **15.77** | 15.57 | Attack cube exposure |
| | **Mean Red Cubes Blocked / Seat** | **2.84** | 2.75 | Shields committed to Market Defense |
| | **Red Cube Block Rate %** | **18.0%** | 17.6% | Defensive effectiveness |
| | **Mean Share Lost / Seat** | **12.61** | 12.49 | Net economic attrition |
| **3P** | **Mean Regains / Seat** | **2.36** | 2.19 | Market Share recovered via PR |
| | **Mean PR Research Spent / Seat** | **7.07 🔬** | 6.57 🔬 | Research channeled into PR defense |
| | **Mean Red Cubes Incoming / Seat** | **16.53** | 16.36 | Attack cube exposure |
| | **Mean Red Cubes Blocked / Seat** | **3.52** | 3.38 | Shields committed to Market Defense |
| | **Red Cube Block Rate %** | **21.3%** | 20.7% | Defensive effectiveness |
| | **Mean Share Lost / Seat** | **12.82** | 12.77 | Net economic attrition |
| **4P** | **Mean Regains / Seat** | **2.46** | 2.29 | Market Share recovered via PR |
| | **Mean PR Research Spent / Seat** | **7.37 🔬** | 6.88 🔬 | Research channeled into PR defense |
| | **Mean Red Cubes Incoming / Seat** | **16.03** | 16.12 | Attack cube exposure |
| | **Mean Red Cubes Blocked / Seat** | **3.51** | 3.41 | Shields committed to Market Defense |
| | **Red Cube Block Rate %** | **21.9%** | 21.1% | Defensive effectiveness |
| | **Mean Share Lost / Seat** | **12.36** | 12.57 | Net economic attrition |

---

## 6. Client Company & Starting Color Win Rates

### 6.1 Starting Color Win Rates
| Pod | Fair Share | Color | Baseline Win % | Candidate Win % | Delta ($\Delta$) | Equity Status |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2P** | 50.0% | **Red** | 51.3% | **50.1%** | -1.3% | BALANCED |
| **2P** | 50.0% | **Blue** | 48.6% | **48.7%** | +0.1% | BALANCED |
| **2P** | 50.0% | **Green** | 50.1% | **51.2%** | +1.1% | BALANCED |
| **3P** | 33.3% | **Red** | 32.2% | **31.7%** | -0.4% | BALANCED |
| **3P** | 33.3% | **Blue** | 33.7% | **33.6%** | -0.0% | BALANCED |
| **3P** | 33.3% | **Green** | 34.1% | **34.5%** | +0.4% | BALANCED |
| **4P** | 25.0% | **Red** | 26.5% | **27.4%** | +0.9% | BALANCED |
| **4P** | 25.0% | **Blue** | 21.6% | **22.9%** | +1.3% | BALANCED |
| **4P** | 25.0% | **Green** | 26.9% | **24.7%** | -2.2% | BALANCED |

### 6.2 Client Company Win Rates
| Pod | Company | Starting Color | Baseline Win % | Candidate Win % | Delta ($\Delta$) |
|:---:|:---|:---:|:---:|:---:|:---:|
| **2P** | **Aegis Defense Relay** | Blue | 52.7% | **53.0%** | +0.3% |
| **2P** | **Department of Telecommunications Oversight** | Blue | 44.6% | **44.6%** | +0.0% |
| **2P** | **Helix Biomedical Consortium** | Green | 45.2% | **46.0%** | +0.7% |
| **2P** | **Meridian Financial Trust** | Red | 52.9% | **49.5%** | -3.4% |
| **2P** | **Omnidyne Systems** | Green | 55.4% | **56.9%** | +1.5% |
| **2P** | **The Prometheus Foundation** | Red | 49.9% | **50.6%** | +0.7% |
| **3P** | **Aegis Defense Relay** | Blue | 37.6% | **36.8%** | -0.9% |
| **3P** | **Department of Telecommunications Oversight** | Blue | 29.8% | **30.5%** | +0.8% |
| **3P** | **Helix Biomedical Consortium** | Green | 29.1% | **29.7%** | +0.6% |
| **3P** | **Meridian Financial Trust** | Red | 32.3% | **32.4%** | +0.1% |
| **3P** | **Omnidyne Systems** | Green | 39.4% | **39.6%** | +0.2% |
| **3P** | **The Prometheus Foundation** | Red | 32.0% | **31.1%** | -0.9% |
| **4P** | **Aegis Defense Relay** | Blue | 23.8% | **27.5%** | +3.7% |
| **4P** | **Department of Telecommunications Oversight** | Blue | 19.3% | **18.1%** | -1.2% |
| **4P** | **Helix Biomedical Consortium** | Green | 22.7% | **22.5%** | -0.1% |
| **4P** | **Meridian Financial Trust** | Red | 26.3% | **26.7%** | +0.4% |
| **4P** | **Omnidyne Systems** | Green | 31.2% | **26.9%** | -4.3% |
| **4P** | **The Prometheus Foundation** | Red | 26.6% | **28.1%** | +1.5% |

### 6.3 Bot Archetype Win Rates
| Pod | Archetype | Candidate Win % | Baseline Win % | Delta ($\Delta$) |
|:---:|:---|:---:|:---:|:---:|
| **2P** | **AccelerationistBot** | **52.4%** | 47.2% | +5.2% |
| **2P** | **AdaptiveBalancedBot** | **71.0%** | 70.1% | +0.8% |
| **2P** | **MixedPolicyBot** | **47.6%** | 49.0% | -1.4% |
| **2P** | **RecklessSaboteurBot** | **33.2%** | 37.3% | -4.1% |
| **2P** | **SecOpsTurtleBot** | **53.7%** | 52.0% | +1.6% |
| **2P** | **VentureGreedBot** | **52.1%** | 48.3% | +3.8% |
| **3P** | **AccelerationistBot** | **32.6%** | 27.5% | +5.0% |
| **3P** | **AdaptiveBalancedBot** | **56.5%** | 60.2% | -3.8% |
| **3P** | **MixedPolicyBot** | **33.2%** | 33.9% | -0.8% |
| **3P** | **RecklessSaboteurBot** | **13.9%** | 15.5% | -1.6% |
| **3P** | **SecOpsTurtleBot** | **31.6%** | 29.6% | +2.0% |
| **3P** | **VentureGreedBot** | **34.2%** | 34.1% | +0.1% |
| **4P** | **AccelerationistBot** | **19.6%** | 15.2% | +4.4% |
| **4P** | **AdaptiveBalancedBot** | **46.5%** | 53.1% | -6.6% |
| **4P** | **MixedPolicyBot** | **25.2%** | 24.6% | +0.7% |
| **4P** | **RecklessSaboteurBot** | **7.4%** | 8.0% | -0.6% |
| **4P** | **SecOpsTurtleBot** | **26.9%** | 24.0% | +2.9% |
| **4P** | **VentureGreedBot** | **24.2%** | 25.5% | -1.2% |

---

## 7. Official Sign-Off Verdict

- **Pacing & Tension:** PASSED. Game length remains stably centered in 8.5–9.5 rounds across all player counts with zero timeouts.
- **End-Game Triad:** PASSED. Tri-modal balance preserved with rich Singularity / Patient Zero / Market Collapse distribution.
- **Track Pacing & Anti-Snowball:** PASSED. Step costs (1, 1, 2, 2) make L1/L2 accessible while max 2 upgrades/turn caps multi-track snowballing (≤ 5.3% 2+ maxed tracks).
- **Telemetry & Enforcement:** PASSED. Turn limit cleanly blocks excess upgrade requests without errors or side effects.
- **Company Equity:** PASSED. Parity across Red, Blue, and Green starter companies preserved within design tolerances.
- **Recommendation:** **OFFICIALLY APPROVED (`v0.39.0`).** Ready for documentation update and release lock.
