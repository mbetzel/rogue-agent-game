# v0.44.0 Monte Carlo Validation Sweep: Colored Die F6 Variant Overhaul & Glitched Shield Slot Flow

**Date:** 2026-11-15
**Script:** `scripts/run_v044_f6_sweep.py`
**Command:** `python3 scripts/run_v044_f6_sweep.py --runs 300 --seed 42`
**Sample:** 1,800 games total — 300 games per player count (2P, 3P, 4P; seeds `42..341`) for `GameConfig.v044_roster()` (v0.44.0 Candidate) vs `GameConfig.v043_roster()` (v0.43.0 Baseline).

---

## 1. Macro Pacing & End-Trigger Breakdown

| Config | Pod | N | Mean Rounds (Std) | Min / P10 / P50 / P90 / Max | Singularity | Patient Zero | Market Collapse | Total Wipeout |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **v0.44.0** | ALL | 900 | **7.32** (2.65) | 1 / 3 / 8 / 10 / 12 | 6.1% | 63.4% | 23.3% | 7.1% (64) |
| v0.44.0 | 2P | 300 | 7.39 (2.72) | 1 / 3 / 8 / 11 / 12 | 8.7% | 42.0% | 36.0% | 13.3% (40) |
| v0.44.0 | 3P | 300 | 7.54 (2.43) | 2 / 4 / 8 / 10 / 12 | 4.3% | 73.7% | 19.0% | 3.0% (9) |
| v0.44.0 | 4P | 300 | 7.02 (2.76) | 2 / 3 / 8 / 10 / 12 | 5.3% | 74.7% | 15.0% | 5.0% (15) |
| **v0.43.0** | ALL | 900 | **7.59** (2.52) | 1 / 4 / 8 / 10 / 13 | 7.2% | 61.7% | 25.4% | 5.7% (51) |
| v0.43.0 | 2P | 300 | 7.71 (2.62) | 1 / 4 / 8 / 11 / 12 | 9.0% | 41.0% | 38.3% | 11.7% (35) |
| v0.43.0 | 3P | 300 | 7.68 (2.35) | 2 / 4 / 8 / 10 / 12 | 6.7% | 68.7% | 21.0% | 3.7% (11) |
| v0.43.0 | 4P | 300 | 7.37 (2.59) | 2 / 3 / 8 / 10 / 13 | 6.0% | 75.3% | 17.0% | 1.7% (5) |

- **Pacing:** v0.44.0 runs slightly faster than v0.43.0 (-0.27 rounds overall; 7.32 vs 7.59), sitting just under the 7.5–11.0 round spec target (3P hits 7.54). Zero games hit Round Limit or Shared Victory.
- **Wipeout Rate:** 7.1% overall (vs 5.7% in v0.43.0), concentrated in 2P (13.3%). Both versions exceed the ≤1.0% spec guardrail.

---

## 2. Seat Fairness & Client Company Win Rates

### Seat Fairness (Win Share %)
| Config | 2P (S1 / S2) | 3P (S1 / S2 / S3) | 4P (S1 / S2 / S3 / S4) |
|---|---|---|---|
| **v0.44.0** | 51.7% / 48.3% | 32.7% / 32.0% / 35.3% | **25.7% / 24.3% / 22.7% / 27.3%** |
| **v0.43.0** | 51.0% / 49.0% | 29.3% / 33.3% / 37.3% | 26.0% / 27.3% / 27.3% / 19.3% |

v0.44.0 notably improves 4P seat parity (4.6pp max spread vs 8.0pp in v0.43.0).

### Client Company & Starting Color Win Rates
| Client Company | Color | v0.44.0 Win Rate (vs Exp) | v0.43.0 Win Rate (vs Exp) | Delta (v0.44 - v0.43) |
|---|---|---:|---:|---:|
| **OMNIDYNE** | Green | **42.0%** (+8.89pp) | 42.3% (+9.11pp) | -0.3pp |
| **DTO** | Blue | **38.0%** (+4.20pp) | 39.9% (+6.02pp) | -1.9pp |
| **AEGIS** | Blue | **35.5%** (+2.61pp) | 36.0% (+3.05pp) | -0.5pp |
| **HELIX** | Green | **30.5%** (-2.69pp) | 25.8% (-7.45pp) | **+4.7pp** |
| **MERIDIAN** | Red | **28.9%** (-4.10pp) | 30.9% (-2.09pp) | -2.0pp |
| **PROMETHEUS** | Red | **25.1%** (-8.87pp) | 25.5% (-8.43pp) | -0.4pp |

- **Starting Color Equity (v0.44.0 vs v0.43.0):**
  - Red: **27.0%** (vs 28.2%) | Blue: **36.8%** (vs 37.9%) | Green: **36.2%** (vs 33.9%).
  - **Helix** gained +4.7pp in v0.44.0, narrowing the Green internal gap, while **Red starters** (Meridian, Prometheus) remain ~9.8pp behind Blue/Green (exceeding the ±4.0% spec guardrail; inherited from v0.43.0).

---

## 3. F6 Variant Card & Glitched Shield Slot Purge Telemetry (v0.44.0)

- **Glitched Shield Slot Purges (`slots_purged_by_shields_total`):**
  - **10,077 total purges** across 900 games (**11.20/game**, **0.513/player-round**).
- **F6 Variant Card Activations:**
  - **R2 (Ad Campaign):** 259 activations in 310 R2 games (**0.84/R2-game**).
  - **B2 (Encrypted Vault):** 255 cash activations (0.84/gm) vs 122 secret activations (0.40/gm) in 302 B2 games. **0 suicide breaches (0.0%)**.
  - **G1 (Hot-Patch):** 511 activations in 293 G1 games (**1.74/gm**); **172 shield promotions** (**33.7%** of activations promoted a shield from a glitched slot to a clean slot in Phase 3).
  - **G3 (Pipeline Reboot):** 439 graduations + **123 fizzles** in 285 G3 games (**1.97/gm**, **21.9% fizzle rate**).
  - **Y1 (Algorithmic Trading):** 1,361 cash activations (**4.57/gm**) vs 110 secret activations (**0.37/gm**) in 298 Y1 games.

---

## 4. Outlier Seeds & Anomalies

- **Crashes / Engine Errors:** 0 across all 1,800 games.
- **Long games (≥14 rounds):** 0 in both v0.44.0 (max 12) and v0.43.0 (max 13).
- **Short games (≤5 rounds):** 237/900 (26.3%) in v0.44.0 vs 204/900 (22.7%) in v0.43.0. Sample 2-round 2P outliers in v0.44.0:
  - `(2P, seed=48, 2r, total_wipeout)`, `(2P, seed=104, 2r, total_wipeout)`
  - `(2P, seed=43, 2r, patient_zero)`, `(2P, seed=53, 2r, patient_zero)`, `(2P, seed=62, 2r, patient_zero)`
- **Total Wipeout sample seeds (64 total in v0.44.0):** `(2P, 44, 10r)`, `(2P, 45, 11r)`, `(2P, 47, 10r)`, `(2P, 48, 2r)`, `(2P, 52, 9r)`, `(2P, 63, 9r)`, `(2P, 68, 9r)`, `(2P, 69, 10r)`.
- **B2 suicide breaches:** 0 seeds.
