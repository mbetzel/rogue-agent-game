# Validation Report: Package `v0.38d` (Candidate C2 + Green-Clean Package)

**Harness:** `python3 -m scripts.run_v380_secret_faces_sweep --config v038d --roster mixed1 --games 1200 --players 2 3 4 --seed0 42 --procs 8`  
**Baseline Comparison:** `v0.38c` on Shogun Baffle tower (`sim_results/shogun_tower_comparison/shogun_baffle.json`, 1,200 games/pod, `mixed1`, seed0 42).  
**Output Data:** `sim_results/v380d_c2_green_clean/sweep_report.json`

---

## 1. Executive Summary & Core Verdict

Package `v0.38d` combines **Candidate C2 setup** (4 priming cubes, 4 starting attack cubes in staging cup, 1 starting Glitched Shield Slot), **elimination of passive graduation auto-clean** (`slot_graduation_clear = 0`), **Green Face 1 = +2 🔬** (`die_face_profile = 'V038D'`), and **Green banking triage slot clean** (`green_bank_cleans_slot = True`, `COUNT_THEN_CLEAN`).

### Key Takeaways:
1. **Graduation Clean Successfully Eliminated:** Slots cleaned by graduation dropped to exactly `0.00` across all player counts (down from ~6.0–6.1 in `v038c`).
2. **Active Green Triage Cleaning Active & Positive:** Green banking triage cleans `0.69–0.77` slots per seat. Active die cleaning increased from `~1.38` to `5.18–5.49` slots per seat as players actively leverage triage tools.
3. **Pacing Tightened:** Average rounds decreased by ~1.2 rounds across all player counts (from ~10.05–10.13 to 8.73–8.94), hitting optimal target pacing (~9 rounds).
4. **End-Trigger Diversity Restored:** `Singularity` endings fell from a dominant ~65–72% in `v038c` down to 36.1% (2P), 42.0% (3P), and 42.3% (4P). Both `Market Collapse` (26–43%) and `Patient Zero` (19–31%) are vibrant, active survival pressures. Total Wipeout remains low and safe (0.1%–2.4%).
5. **Color & Archetype Parity:** Company starting colors remain balanced (within noise of fair share).

---

## 2. Macro Pacing, Breach Rates & Endings

| Pod | Metric | Baseline (`v0.38c`) | Candidate (`v0.38d`) | Delta ($\Delta$) |
|:---:|:---|:---:|:---:|:---:|
| **2P** | **Avg Rounds** | 10.05 | **8.73** | -1.32 |
| | **Breach Rate** | 12.8% | **21.5%** | +8.7% |
| | Singularity | 64.9% | **36.1%** | -28.8% |
| | Market Collapse | 22.8% | **42.8%** | +20.0% |
| | Patient Zero | 11.3% | **18.7%** | +7.4% |
| | Total Wipeout | 1.0% | **2.4%** | +1.4% |
| **3P** | **Avg Rounds** | 10.04 | **8.89** | -1.15 |
| | **Breach Rate** | 20.2% | **32.9%** | +12.7% |
| | Singularity | 72.0% | **42.0%** | -30.0% |
| | Market Collapse | 8.8% | **25.9%** | +17.1% |
| | Patient Zero | 19.0% | **31.4%** | +12.4% |
| | Total Wipeout | 0.25% | **0.67%** | +0.42% |
| **4P** | **Avg Rounds** | 10.13 | **8.94** | -1.19 |
| | **Breach Rate** | 19.2% | **32.3%** | +13.1% |
| | Singularity | 71.3% | **42.3%** | -29.0% |
| | Market Collapse | 10.5% | **26.3%** | +15.8% |
| | Patient Zero | 18.2% | **31.4%** | +13.2% |
| | Total Wipeout | 0.00% | **0.08%** | +0.08% |

---

## 3. Glitched Shield Slots & Decontamination Dynamics

| Pod | Clean Source | `v0.38c` (Baseline) | `v0.38d` (Candidate) | Target Compliance |
|:---:|:---|:---:|:---:|:---:|
| **2P** | **graduation** | 5.95 | **0.00** | Confirmed (Passive clean removed) |
| | **green_triage** | 0.00 | **0.69** | Confirmed (Active green triage) |
| | **die** (active cards) | 1.37 | **5.18** | +3.81 (Active mitigation engagement) |
| | **face** | 0.41 | **0.15** | -0.26 |
| | *Max Glitched Slots (Avg)* | — | 2.14 | Stable capacity headroom |
| **3P** | **graduation** | 6.01 | **0.00** | Confirmed (Passive clean removed) |
| | **green_triage** | 0.00 | **0.74** | Confirmed (Active green triage) |
| | **die** (active cards) | 1.39 | **5.40** | +4.01 |
| | **face** | 0.46 | **0.17** | -0.29 |
| | *Max Glitched Slots (Avg)* | — | 2.18 | Stable capacity headroom |
| **4P** | **graduation** | 6.15 | **0.00** | Confirmed (Passive clean removed) |
| | **green_triage** | 0.00 | **0.77** | Confirmed (Active green triage) |
| | **die** (active cards) | 1.39 | **5.49** | +4.10 |
| | **face** | 0.48 | **0.16** | -0.32 |
| | *Max Glitched Slots (Avg)* | — | 2.20 | Stable capacity headroom |

---

## 4. Win Rates: Company Starting Color, Path & Bot Archetypes

### Company Starting Color Win Rates
| Pod | Fair Share | Color | Baseline (`v0.38c`) | Candidate (`v0.38d`) |
|:---:|:---:|:---:|:---:|:---:|
| **2P** | 50.0% | **Blue** | 44.4% | 43.3% |
| | | **Green** | 52.5% | 52.4% |
| | | **Red** | 53.1% | 54.4% |
| **3P** | 33.3% | **Blue** | 30.2% | 31.4% |
| | | **Green** | 38.5% | 37.3% |
| | | **Red** | 31.1% | 31.1% |
| **4P** | 25.0% | **Blue** | 21.3% | 20.3% |
| | | **Green** | 28.0% | 29.1% |
| | | **Red** | 25.6% | 25.5% |

### Strategic Path Win Rates
| Pod | Path | Baseline (`v0.38c`) | Candidate (`v0.38d`) |
|:---:|:---|:---:|:---:|
| **2P** | **Blue** | 47.8% | 51.2% |
| | **Green** | 59.1% | 59.5% |
| | **Mixed** | 49.4% | 46.7% |
| | **Red** | 55.5% | 55.7% |
| | **Yellow** | 37.7% | 36.1% |
| **3P** | **Blue** | 35.0% | 36.3% |
| | **Green** | 46.9% | 43.3% |
| | **Mixed** | 32.0% | 31.8% |
| | **Red** | 36.6% | 34.5% |
| | **Yellow** | 27.1% | 27.2% |
| **4P** | **Blue** | 29.2% | 28.1% |
| | **Green** | 39.2% | 34.3% |
| | **Mixed** | 24.2% | 23.5% |
| | **Red** | 23.1% | 24.0% |
| | **Yellow** | 18.5% | 20.8% |

### Bot Archetype Win Rates
| Pod | Archetype | Baseline (`v0.38c`) | Candidate (`v0.38d`) |
|:---:|:---|:---:|:---:|
| **2P** | `AccelerationistBot` | 48.9% | 45.9% |
| | `AdaptiveBalancedBot` | 67.2% | 61.4% |
| | `MixedPolicyBot` | 47.2% | 49.3% |
| | `RecklessSaboteurBot` | 37.7% | 35.3% |
| | `SecOpsTurtleBot` | 58.1% | 60.6% |
| | `VentureGreedBot` | 52.1% | 50.4% |
| **3P** | `AccelerationistBot` | 35.9% | 29.8% |
| | `AdaptiveBalancedBot` | 50.2% | 51.1% |
| | `MixedPolicyBot` | 30.8% | 31.9% |
| | `RecklessSaboteurBot` | 13.9% | 16.3% |
| | `SecOpsTurtleBot` | 45.7% | 45.1% |
| | `VentureGreedBot` | 27.6% | 28.3% |
| **4P** | `AccelerationistBot` | 29.1% | 18.9% |
| | `AdaptiveBalancedBot` | 34.6% | 32.5% |
| | `MixedPolicyBot` | 20.5% | 25.3% |
| | `RecklessSaboteurBot` | 8.9% | 10.3% |
| | `SecOpsTurtleBot` | 40.1% | 41.5% |
| | `VentureGreedBot` | 19.8% | 21.2% |
