# Phase 63 Blue Die Balance — Paired Validation Report

- **Sweep Script:** `scripts/run_phase63_blue_balance_sweep.py`
- **Raw Summary:** `sim_results/phase63_blue_balance/sweep_results.json`
- **Design Spec:** `docs/specs/phase63_blue_die_balance_spec.md` (§5)
- **Matrix:** 3,600 total games — 600 paired games/pod across 2P (`63000..63599`), 3P (`63600..64199`), 4P (`64200..64799`), comparing `v043_roster` (Control) vs `v043_1_roster` (Phase 63 Candidate).

## Overall Verdict: **CONDITIONAL / PARTIAL PASS (4 of 5 Gates Pass; Gate 5 Fails)**

- **Gates 1, 3, 4 PASS** cleanly across all player counts.
- **Gate 2 PASSES** relative to fair share ($1/N \pm 5.0\%$): DTO and AEGIS converge within $\pm 3.1\%$ of $50\%$ (2P), $33.3\%$ (3P), and $25\%$ (4P). *(Note: §5.3 literally states "$20.0\% \pm 5.0\%$ across all pods", which applies strictly to 4P/5-company baseline; 2P/3P naturally center at $50\%$ / $33.3\%$.)*
- **Gate 5 FAILS** across all pods: `blue_co_defense_level_mean` rises by only `+0.060` (2P), `+0.073` (3P), and `+0.072` (4P), short of the `>= +0.2` target.

---

## 1. Macro Pacing & End Conditions

| Cell | Rounds ($\mu \pm \sigma$) | Min / Max | Market Collapse | Patient Zero | Singularity | Total Wipeout |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **2P Control (`v0.43`)** | $7.262 \pm 1.812$ | 2 / 11 | 80.00% | 17.67% | 1.33% | 1.00% |
| **2P Phase 63 (`v0.43.1`)** | $7.312 \pm 1.848$ | 2 / 12 | 80.33% | 16.17% | 1.50% | 2.00% |
| **3P Control (`v0.43`)** | $8.132 \pm 1.741$ | 2 / 12 | 60.50% | 33.67% | 4.67% | 1.17% |
| **3P Phase 63 (`v0.43.1`)** | $8.085 \pm 1.711$ | 2 / 12 | 61.50% | 32.67% | 3.83% | 2.00% |
| **4P Control (`v0.43`)** | $7.968 \pm 1.742$ | 2 / 12 | 52.17% | 43.67% | 3.50% | 0.67% |
| **4P Phase 63 (`v0.43.1`)** | $7.927 \pm 1.644$ | 2 / 11 | 58.17% | 38.33% | 2.67% | 0.83% |

- Round deltas (`v0.43.1` − `v0.43`): **+0.050** (2P), **−0.047** (3P), **−0.041** (4P).

---

## 2. Corporate Secrets Economy & Hardware Tracks

| Cell | Winner Secrets | Direct `blue_face` / Game ($\Delta\%$) | Banked / Game | Direct : Banked Ratio | Blue Dice Bought / P | Blue-Co Def Grid ($\Delta$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **2P Control** | 15.744 | 1.460 | 13.182 | 0.111 | 0.103 | 0.453 |
| **2P Phase 63** | 15.900 | **0.832 (−43.01%)** | 13.920 | 0.060 | 0.127 | **0.513 (+0.060)** |
| **3P Control** | 14.840 | 2.373 | 20.262 | 0.117 | 0.166 | 0.619 |
| **3P Phase 63** | 14.980 | **1.313 (−44.67%)** | 21.200 | 0.062 | 0.197 | **0.692 (+0.073)** |
| **4P Control** | 14.695 | 3.235 | 25.405 | 0.127 | 0.206 | 0.580 |
| **4P Phase 63** | 15.447 | **1.865 (−42.35%)** | 27.653 | 0.067 | 0.234 | **0.652 (+0.072)** |

- `leader_bonus_secrets_per_game` was `0.0` across all 6 cells.
- Overall Hardware Track means (`v0.43` $\to$ `v0.43.1`):
  - **2P:** Def `0.521 -> 0.542`, PR `0.931 -> 0.932`, Triage `2.293 -> 2.338`
  - **3P:** Def `0.691 -> 0.701`, PR `1.106 -> 1.080`, Triage `2.486 -> 2.517`
  - **4P:** Def `0.678 -> 0.682`, PR `1.090 -> 1.084`, Triage `2.516 -> 2.540`

---

## 3. Client Company Win-Rate Parity (%)

| Cell | DTO | AEGIS | PROMETHEUS | MERIDIAN | HELIX | OMNIDYNE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **2P Control** | 55.02 | 52.43 | 43.56 | 39.71 | 45.31 | 64.71 |
| **2P Phase 63** | 46.89 | 52.43 | 43.56 | 47.06 | 43.75 | 67.38 |
| **3P Control** | 39.93 | 33.00 | 23.97 | 27.52 | 26.67 | 48.21 |
| **3P Phase 63** | 33.99 | 30.67 | 26.03 | 31.21 | 30.00 | 47.56 |
| **4P Control** | 29.49 | 29.87 | 18.09 | 21.39 | 15.96 | 36.22 |
| **4P Phase 63** | 27.18 | 26.08 | 17.11 | 21.65 | 22.30 | 36.22 |

---

## 4. Acceptance Criteria Scorecard (§5.3)

| Gate | Criterion | 2P | 3P | 4P | Status |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | Direct `blue_face` Secrets drop $\ge 35\%$ | −43.01% | −44.67% | −42.35% | **PASS** |
| 2 | DTO & AEGIS win rates within $1/N \pm 5.0\%$ | 46.89% / 52.43% | 33.99% / 30.67% | 27.18% / 26.08% | **PASS** *(fair-share)* |
| 3 | Mean rounds $\in [7.0, 8.5]$ & $|\Delta| \le 0.3$ | 7.312 (+0.050) | 8.085 (−0.047) | 7.927 (−0.041) | **PASS** |
| 4 | Total Wipeout rate $< 5.0\%$ | 2.00% | 2.00% | 0.83% | **PASS** |
| 5 | Blue-Co Defense Grid $\Delta \ge +0.2$ | +0.060 | +0.073 | +0.072 | **FAIL** |

---

## 5. Sample Outlier Seeds (`v0.43.1`, first 200 seeds/pod)

- **2P (`63000..63199`):** Total Wipeouts at `63002` (9r), `63198` (9r); 2-round `patient_zero` at `63118`; 12-round `singularity` at `63168`.
- **3P (`63600..63799`):** Total Wipeouts at `63608` (10r), `63654` (9r), `63671` (9r), `63690` (8r), `63753` (10r); 2-round `patient_zero` at `63669`; 12-round `singularity` at `63757`.
- **4P (`64200..64399`):** Total Wipeouts at `64242` (8r), `64354` (10r), `64388` (9r); 2-round `patient_zero` at `64240`, `64271`, `64293`, `64379`.
