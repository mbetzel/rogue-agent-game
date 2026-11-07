# v0.37.0 Market Leader Bonus: Acceptance Sweep Telemetry Report

**Author:** product-owner (data only; no engine, bot, test or rules changes). **Date:** 2026-11-07.
**Spec:** `docs/specs/v370_market_leader_bonus_spec.md` §8 (with §14.1 resolutions). **Context:** FINDINGS.md §34 (v0.36 guardrails), §38 (exploration and expected magnitudes).

## 1. Runs and reproducibility

| Run | Command (repo root, `PYTHONDONTWRITEBYTECODE=1 python3 …`) | Games per pod (2P/3P/4P) | Raw output |
|---|---|---|---|
| Main, base seed 42 | `scripts/run_v370_market_leader_bonus_sweep.py --workers 8` | V036, V037, V037-S036, V037-ONE-AWARE 3,000; V037-NAIVE 2,000 | `sim_results/v370_market_leader_bonus_sweep.json` / `.txt` |
| Fresh seeds, base 7000 | `… --seed 7000 --cells V036,V037,V037-ONE-AWARE --workers 8` | 3,000 | `sim_results/v370_market_leader_bonus_sweep_seed7000.json` / `.txt` |
| Extra 2P Singularity check (not in spec; added to settle the 46% line) | `… --seed {9000,13000} --pods 2 --cells V036,V037 --workers 8 --out sim_results/v370_market_leader_bonus_sweep_2p_seed{S}.json` | 2P only, 3,000 | `sim_results/v370_market_leader_bonus_sweep_2p_seed9000.json`, `…13000.json` |
| Supplementary pass | read-only re-run of the same `build_engine` and seeds (scratchpad script, engine fields only) for metrics the sweep script does not aggregate: win rate by Red dice owned, pre/post-bonus bot win rates and Secrets, flip margins, round distributions, outlier seeds | same as main / fresh | `sim_results/v370_market_leader_bonus_supplement.json`, `…_supplement_seed7000.json` |

Seeds: `seed = base + n × 100_000 + idx`, paired across cells. The supplementary pass reproduces the main sweep exactly (all 15 seed-42 and 9 seed-7000 pods match bot win rates to 1e-3). Total ≈ 81,000 games; wall time < 3 minutes at 8 workers.

## 2. Headline (V037 acceptance cell, seed 42; seed 7000 in parentheses)

| Metric | 2P | 3P | 4P | §38 expected |
|---|---|---|---|---|
| Patient Zero / Singularity / Market Collapse | 27.0 / **47.1** / 25.9 (27.0 / 46.7 / 26.3) | 37.5 / 39.9 / 22.6 (36.0 / 40.8 / 23.2) | 30.4 / 40.1 / 29.4 (30.6 / 39.6 / 29.8) | 27/46/27 · 37/41/22 · 32/39/28 |
| Total Wipeout (V036) | 8.4 (7.6) · fresh 7.7 (7.1) | 4.2 (2.6) · fresh 3.3 (2.6) | 1.6 (1.0) · fresh 1.6 (1.0) | 8.4 (7.1) · 3.8 (2.6) · 1.2 (1.0) |
| Rounds (V036) | 9.14 (8.84) | 8.97 (8.76) | 8.99 (8.84) | 9.13 · 8.97 · 8.95 |
| Winner changed / awarded games | **11.7** (12.7) | 15.1 (15.7) | 24.9 (23.9) | 15–18 · 17–20 · 25–27 |
| Winner changed / all games | 10.7 | 14.4 | 24.5 | – |
| Bonus-aware seat (ONE-AWARE) win credit, edge | 57.9%, +7.9 (+7.7) | 39.5%, +6.2 (+7.6) | 32.4%, +7.4 (+9.4) | 59.2 · 39.6 · 33.7 |
| Lowest-Market-Share survivor wins (V036) | 33.5 (45.1) | 21.9 (31.4) | 13.6 (22.7) | 31 (44) · 20 (33) · 13 (23) |
| Generic (`Any`) shields on Blue (V036) | 57.0 (63.3) | 59.8 (63.8) | 59.3 (63.0) | 57–60 (63) |
| Blue left open in contested rounds (V036) | 23.1 (7.1) | 17.9 (6.3) | 17.1 (6.6) | 17–22 (6–7) |

## 3. Guardrails (V037, spec §8 bands; seed 42 / seed 7000)

| Guardrail | 2P | 3P | 4P |
|---|---|---|---|
| Patient Zero 25–40% | pass 27.0 [25.4, 28.6] / pass 27.0 | pass 37.5 / pass 36.0 | pass 30.4 / pass 30.6 |
| Singularity (2P: ≤43 pass, 43–46 watch, >46 fail; else 25–40) | **fail 47.1 [45.3, 48.9] / fail 46.7 [45.0, 48.5]**; 4-base pooled 46.0 [45.1, 46.9] (see §5) | pass 39.9 / **watch 40.8** | **watch 40.1 [38.4, 41.9]** / pass 39.6 |
| Market Collapse 25–40% | pass 25.9 / pass 26.3 | **watch 22.6 / watch 23.2** | pass 29.4 / pass 29.8 |
| Highest single-setup trigger ≤43 (groups n ≥ 200) | **watch** ZERO_DAY_OVERRIDE v3.0 → Singularity 50.5% (n=1511); AEGIS@1 52.9% | **watch** AEGIS@1 Singularity 46.3% | **watch** AEGIS@0 Singularity 45.4% |
| Rounds mean 8.4–9.2 | pass 9.14 / 9.13 | pass 8.97 / 8.98 | pass 8.99 / 8.97 |
| Total Wipeout ≤ V036 + 1.0 (2P ≤ 16%) | pass +0.8 / pass +0.6 | **watch +1.6** / pass +0.7 | pass +0.6 / pass +0.6 |
| No Market Collapse in ≤ 5 rounds | pass (0) / pass (0) | pass / pass | pass / pass |
| Red block rate ≥ V036 | pass 22.0 vs 15.3 | pass 20.5 vs 14.7 | pass 20.9 vs 14.9 |
| Regain share of research 20–40% | pass 36.6 | pass 38.2 | pass 36.1 |
| Winner changed 10–30% (awarded) | pass 11.7 / 12.7 (near the 10% floor) | pass 15.1 / 15.7 | pass 24.9 / 23.9 |
| Bonus-aware edge ≤ +7 pts | **watch +7.9 [+6.1, +9.7] / watch +7.7** | pass +6.2 / **watch +7.6** | **watch +7.4 / watch +9.4** |
| Generic (`Any`) shields on Blue ≥ 55% | pass 57.0 | pass 59.8 | pass 59.3 |
| Blue left open ≤ 25% | pass 23.1 / 23.2 (close to the 25% line) | pass 17.9 | pass 17.1 |
| Lowest-MS survivor wins (2P watch < 25%) | report 33.5 | report 21.9 | report 13.6 |
| Company spread ≤ V036 + 3 pts | pass 17.3 vs 19.5 | pass 14.6 vs 21.1 | pass 16.6 vs 23.5 |
| V037-NAIVE Patient Zero (watch < 20%) | **watch 17.4 [15.8, 19.1]** | report 26.4 | report 24.7 |

No guardrail fails except **2P Singularity**. Watches: 3P Market Collapse, 4P Singularity (seed 42 only), 3P Singularity (seed 7000 only), setup concentration in every pod, 3P Total Wipeout (seed 42 only), bonus-aware edge at 2P/4P (both seeds) and 3P (seed 7000), and 2P NAIVE Patient Zero.

## 4. Comparison against FINDINGS §38 (flag = off by > 3 pts)

| Metric | Pod | Sweep (42 / 7000) | §38 | Flag |
|---|---|---|---|---|
| Endings (PZ / Sing / MC) | 2P | 27.0/47.1/25.9 · 27.0/46.7/26.3 | 27/46/27 | ok (≤ 1.1) |
| | 3P | 37.5/39.9/22.6 · 36.0/40.8/23.2 | 37/41/22 | ok (≤ 1.1) |
| | 4P | 30.4/40.1/29.4 · 30.6/39.6/29.8 | 32/39/28 | ok (≤ 1.8) |
| Total Wipeout | 2P/3P/4P | 8.4/4.2/1.6 · 7.7/3.3/1.6 | 8.4/3.8/1.2 | ok |
| Rounds | all | 9.14/8.97/8.99 | 9.13/8.97/8.95 | ok |
| Winner changed | 2P | 11.7 · 12.7 | 15–18 | **FLAG: 3.3 below the range floor at seed 42 (2.3 at 7000), 4.8 below the midpoint** |
| | 3P | 15.1 · 15.7 | 17–20 | borderline: 1.9 below the floor, 3.4 below the midpoint |
| | 4P | 24.9 · 23.9 | 25–27 | ok |
| One bonus-aware seat wins | 2P/3P/4P | 57.9/39.5/32.4 · 57.7/40.9/34.4 | 59.2/39.6/33.7 | ok (≤ 1.3) |
| Lowest-MS survivor wins | 2P/3P/4P | 33.5/21.9/13.6 · 32.6/21.2/13.4 | 31/20/13 | ok (≤ 2.5) |
| Any shields on Blue | all | 57.0–59.8 | 57–60 | ok |
| Blue left open | all | 17.1–23.2 | 17–22 | ok (2P 1.1 above the top) |
| Red chosen in contested rounds | all | 43.6/39.1/39.8 | 39–43 | ok |
| Win rate 0 vs 2+ Blue dice, 2P | 2P | 44.0 / 62.0 | 45 / 61 | ok |
| RecklessSaboteur 2P win rate | 2P | 37.7 | 37–42 | ok |
| V037-NAIVE Patient Zero | 2P/3P/4P | 17.4/26.4/24.7 | 18–26 | ok |

The endings, Total Wipeout and edge all port within ~2 points, so the §8 "porting defect" test (endings off by > 3) is not triggered. The one outlier is **2P (and to a lesser degree 3P) winner changed**, which runs ~3–5 points below §38. Possible causes for the game-designer and staff-engineer to check (not investigated, because that needs engine reading beyond data scope): (a) §38's figure may count winner changes differently (for example over all games, or with shared pre-bonus victories counted as changed); (b) a difference in how `pre_bonus_winner_ids` resolves pre-bonus ties versus the probe; (c) `deep=False` vs `deep=True` behaviour (spec §8 note). The over-all-games rate (10.7 / 14.4 / 24.5) is lower still, so (a) alone does not explain it.

## 5. 2P Singularity: settled with confidence intervals

| Seed base | V036 Singularity | V037 Singularity (95% CI) | V037 Total Wipeout |
|---|---|---|---|
| 42 | 35.1 | 47.1 [45.3, 48.9] | 8.4 |
| 7000 | 35.5 | 46.7 [45.0, 48.5] | 7.7 |
| 9000 | 34.4 | 44.9 [43.2, 46.7] | 8.0 |
| 13000 | 34.9 | 45.1 [43.3, 46.9] | 8.2 |
| **Pooled (n=12000)** | 35.0 [34.1, 35.8] | **46.0 [45.1, 46.9]** | – |


**Reading.** 2P Singularity is 46.0% pooled over 12,000 games [45.1, 46.9]. That is **at the 46% fail line, and the CI straddles it**. The seed-42 and seed-7000 bases (the spec's acceptance runs) both fail on their own (47.1 and 46.7). The two extra bases land in the watch band (44.9, 45.1). The 2P CI excludes the 43% pass line by a wide margin. Verdict: **not a pass. Treat it as fail-or-top-of-watch, decided by game-designer judgement.** The 300-game 50% reading was noise above a true value of ~46%. The rise is +11.0 pts over V036 (35.0), the largest single shift in the sweep. In the ablation (V037-S036, v0.36 starting Secrets 7/7/8), 2P Singularity is 36.2% but Patient Zero jumps to 42.2% and Total Wipeout to 12.0%. So the +2 starting Secrets at 2P, not the bonus itself, drives most of the Singularity shift. Setup concentration agrees: ZERO_DAY_OVERRIDE as the v3.0 card gives 2P Singularity in 50.5% of its games (V036 37.5%).

## 6. Per-pod tables (seed 42; all five cells)

Win rates are win credit (`1/|winner_ids|`). The Red-dice win rate, pre-bonus bot win rate and Secrets pre→post columns come from the supplementary pass. "Secrets pre → post" in the bonus table is the survivor mean. In the bot table it is the mean over all seats (Patient Zeros included).

**Blue block rate is not reported.** No engine field records Blue incoming or blocked per player (`red_by_player` / `red_*_total` exist only for Red), and §6.3 defines no Blue block metric. This is a missing telemetry hook, not a sim bug (see §9).

### 2P

**Endings, Total Wipeout, rounds (seed 42; 95% Wilson CIs)**

| Cell | n | Patient Zero (incl. TW) | Singularity | Market Collapse | Total Wipeout | Rounds mean / median / sd |
|---|---|---|---|---|---|---|
| V036 | 3000 | 30.5 [28.9, 32.2] | 35.1 [33.4, 36.8] | 34.4 [32.7, 36.1] | 7.6 [6.7, 8.6] | 8.84 / 9.0 / 1.15 |
| V037 | 3000 | 27.0 [25.4, 28.6] | 47.1 [45.3, 48.9] | 25.9 [24.4, 27.5] | 8.4 [7.5, 9.4] | 9.14 / 9.0 / 1.02 |
| V037-S036 | 3000 | 42.2 [40.4, 43.9] | 36.2 [34.5, 38.0] | 21.6 [20.2, 23.1] | 12.0 [10.8, 13.2] | 8.86 / 9.0 / 1.18 |
| V037-NAIVE | 2000 | 17.4 [15.8, 19.1] | 43.0 [40.9, 45.2] | 39.6 [37.4, 41.7] | 4.5 [3.6, 5.4] | 9.08 / 9.0 / 1.00 |
| V037-ONE-AWARE | 3000 | 19.8 [18.4, 21.3] | 44.2 [42.4, 46.0] | 36.0 [34.3, 37.7] | 5.3 [4.6, 6.2] | 9.10 / 9.0 / 1.01 |

**Market Leader Bonus metrics (seed 42)**

| Cell | Winner changed / awarded | Winner changed / all games | Paid place tied / awarded | Highest-MS survivor wins | Lowest-MS survivor wins | Bonus-aware seat edge (pts, CI) | Survivor Secrets pre → post | Mean bonus by place |
|---|---|---|---|---|---|---|---|---|
| V036 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.1] | 0.0 | 54.9 [53.0, 56.8] | 45.1 [43.2, 47.0] | – | 3.90 → 3.90 | 1:0, 2:0 |
| V037 | 11.7 [10.6, 13.0] | 10.7 [9.7, 11.9] | 27.4 | 66.5 [64.7, 68.2] | 33.5 [31.8, 35.3] | – | 4.54 → 5.99 | 1:2, 2:0 |
| V037-S036 | 9.7 [8.7, 10.9] | 8.6 [7.6, 9.6] | 21.1 | 69.0 [67.1, 70.9] | 31.0 [29.1, 32.9] | – | 3.32 → 4.82 | 1:2, 2:0 |
| V037-NAIVE | 17.8 [16.1, 19.6] | 17.0 [15.4, 18.7] | 23.9 | 70.0 [68.0, 71.9] | 30.0 [28.1, 32.0] | – | 5.32 → 6.66 | 1:2, 2:0 |
| V037-ONE-AWARE | 16.2 [14.8, 17.6] | 15.3 [14.1, 16.6] | 23.7 | 69.0 [67.3, 70.6] | 31.0 [29.4, 32.7] | +7.9 [+6.1, +9.7] (seat 57.9% vs 50.0%) | 5.13 → 6.48 | 1:2, 2:0 |

**Blue agency (seed 42)**

| Cell | Generic shields on Blue / Red / Green | Contested rounds | Blue left open | Red chosen | Red block rate | Regain share of research | Win rate by Blue dice 0 / 1 / 2+ | Win rate by Red dice 0 / 1 / 2+ |
|---|---|---|---|---|---|---|---|---|
| V036 | 63.3 / 22.6 / 14.1 | 27777 | 7.1 | 22.4 | 15.3 | 26.1 | 40.9 (3259) / 55.8 (1501) / 66.8 (1240) | 51.4 (4061) / 51.4 (1161) / 40.6 (778) |
| V037 | 57.0 / 34.9 / 8.2 | 28418 | 23.1 | 43.6 | 22.0 | 36.6 | 44.0 (3384) / 54.3 (1453) / 62.0 (1163) | 50.0 (4335) / 52.2 (1012) / 46.6 (653) |
| V037-S036 | 58.0 / 33.7 / 8.3 | 27619 | 20.4 | 41.4 | 21.7 | 36.6 | 43.2 (3352) / 56.2 (1449) / 61.6 (1199) | 50.1 (4363) / 51.9 (999) / 46.2 (638) |
| V037-NAIVE | 62.7 / 23.3 / 14.1 | 18954 | 8.1 | 23.3 | 15.4 | 25.1 | 45.4 (2178) / 52.6 (1015) / 59.2 (807) | 48.0 (2695) / 56.0 (768) / 51.6 (537) |
| V037-ONE-AWARE | 62.0 / 26.1 / 11.9 | 28457 | 11.3 | 28.6 | 17.1 | 28.2 | 44.6 (3281) / 53.8 (1486) / 59.9 (1233) | 49.8 (4062) / 53.2 (1155) / 46.5 (783) |

**Bot win rates (win credit; post-bonus, with pre-bonus in parentheses) and final Secrets pre → post (all seats, seed 42)**

| Cell | Accelerationist | AdaptiveBalanced | RecklessSaboteur | SecOpsTurtle | VentureGreed |
|---|---|---|---|---|---|
| V036 | 60.3 (60.3); 3.67→3.67 | 52.2 (52.2); 2.75→2.75 | 29.4 (29.4); 1.85→1.85 | 47.2 (47.2); 2.97→2.97 | 60.9 (60.9); 3.81→3.81 |
| V037 | 54.1 (60.2); 4.23→5.36 | 46.2 (50.9); 3.18→4.23 | 37.7 (29.4); 2.33→3.38 | 51.8 (46.8); 3.53→4.90 | 60.2 (62.7); 4.43→5.66 |
| V037-S036 | 55.6 (61.1); 2.85→3.96 | 48.0 (51.3); 1.91→2.90 | 36.3 (29.3); 1.17→2.01 | 50.3 (46.3); 2.18→3.41 | 59.8 (62.0); 2.92→4.08 |
| V037-NAIVE | 52.5 (61.5); 5.31→6.38 | 42.8 (51.7); 4.29→5.21 | 42.0 (28.6); 3.31→4.58 | 54.6 (46.7); 4.55→5.99 | 58.1 (61.5); 5.55→6.76 |
| V037-ONE-AWARE | 54.4 (61.7); 5.03→6.13 | 47.0 (52.2); 3.99→5.02 | 38.2 (28.2); 3.10→4.26 | 52.5 (47.0); 4.32→5.70 | 57.9 (61.0); 5.26→6.46 |

**Setup concentration and company spread (seed 42)**

| Cell | Max trigger, v3.0 card | Max trigger, company@seat | Max trigger, White Hat@seat | Company spread pts (bootstrap CI) | Tiebreak decided by (top 3) |
|---|---|---|---|---|---|
| V036 | ZERO_DAY_OVERRIDE singularity 37.5 (n=1511) | AEGIS@0 singularity 38.2 (n=489) | ACOUSTIC@0 singularity 39.4 (n=502) | 19.5 [16.2, 24.55] | secrets 54.3, sole_survivor 25.0, market_share 13.5 |
| V037 | ZERO_DAY_OVERRIDE singularity 50.5 (n=1511) | AEGIS@1 singularity 52.9 (n=526) | ACOUSTIC@1 singularity 52.1 (n=482) | 17.3 [14.24, 22.22] | secrets 60.9, sole_survivor 21.9, market_share 9.7 |
| V037-S036 | CORRUPTED_KERNEL patient_zero 46.3 (n=1489) | HELIX@1 patient_zero 45.6 (n=526) | CIPHER@0 patient_zero 44.2 (n=477) | 17.2 [13.6, 22.04] | secrets 47.3, sole_survivor 33.7, market_share 11.2 |
| V037-NAIVE | ZERO_DAY_OVERRIDE singularity 44.4 (n=1004) | AEGIS@1 singularity 46.9 (n=358) | ACOUSTIC@1 singularity 50.0 (n=316) | 18.5 [13.75, 25.49] | secrets 69.1, sole_survivor 14.8, market_share 9.6 |
| V037-ONE-AWARE | ZERO_DAY_OVERRIDE singularity 44.7 (n=1511) | AEGIS@0 singularity 48.7 (n=489) | PHREAKER@1 singularity 49.5 (n=509) | 18.3 [14.56, 23.14] | secrets 68.1, sole_survivor 16.3, market_share 10.1 |

### 3P

**Endings, Total Wipeout, rounds (seed 42; 95% Wilson CIs)**

| Cell | n | Patient Zero (incl. TW) | Singularity | Market Collapse | Total Wipeout | Rounds mean / median / sd |
|---|---|---|---|---|---|---|
| V036 | 3000 | 34.8 [33.1, 36.6] | 32.6 [31.0, 34.3] | 32.5 [30.9, 34.2] | 2.6 [2.1, 3.2] | 8.76 / 9.0 / 1.26 |
| V037 | 3000 | 37.5 [35.8, 39.2] | 39.9 [38.2, 41.7] | 22.6 [21.1, 24.1] | 4.2 [3.5, 4.9] | 8.97 / 9.0 / 1.17 |
| V037-S036 | 3000 | 46.6 [44.9, 48.4] | 33.7 [32.0, 35.4] | 19.7 [18.3, 21.2] | 4.5 [3.8, 5.3] | 8.78 / 9.0 / 1.29 |
| V037-NAIVE | 2000 | 26.4 [24.5, 28.3] | 38.0 [35.9, 40.2] | 35.6 [33.6, 37.8] | 2.1 [1.6, 2.8] | 8.92 / 9.0 / 1.15 |
| V037-ONE-AWARE | 3000 | 29.0 [27.4, 30.6] | 37.8 [36.1, 39.6] | 33.2 [31.5, 34.9] | 2.8 [2.2, 3.4] | 8.92 / 9.0 / 1.14 |

**Market Leader Bonus metrics (seed 42)**

| Cell | Winner changed / awarded | Winner changed / all games | Paid place tied / awarded | Highest-MS survivor wins | Lowest-MS survivor wins | Bonus-aware seat edge (pts, CI) | Survivor Secrets pre → post | Mean bonus by place |
|---|---|---|---|---|---|---|---|---|
| V036 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.1] | 0.0 | 44.7 [43.1, 46.3] | 31.4 [29.9, 32.9] | – | 3.97 → 3.97 | 1:0, 2:0, 3:0 |
| V037 | 15.1 [13.8, 16.4] | 14.4 [13.2, 15.7] | 47.6 | 56.5 [54.9, 58.1] | 21.9 [20.6, 23.2] | – | 4.06 → 5.46 | 1:2, 2:1, 3:0 |
| V037-S036 | 14.2 [13.0, 15.6] | 13.6 [12.4, 14.9] | 42.6 | 58.9 [57.2, 60.5] | 22.6 [21.3, 24.1] | – | 3.49 → 4.91 | 1:2, 2:1, 3:0 |
| V037-NAIVE | 18.6 [16.9, 20.4] | 18.2 [16.6, 20.0] | 50.1 | 57.4 [55.5, 59.3] | 19.2 [17.8, 20.8] | – | 4.63 → 5.96 | 1:2, 2:1, 3:0 |
| V037-ONE-AWARE | 17.5 [16.2, 18.9] | 17.0 [15.7, 18.4] | 47.8 | 56.8 [55.2, 58.4] | 20.6 [19.4, 21.9] | +6.2 [+4.5, +8.0] (seat 39.5% vs 33.3%) | 4.58 → 5.91 | 1:2, 2:1, 3:0 |

**Blue agency (seed 42)**

| Cell | Generic shields on Blue / Red / Green | Contested rounds | Blue left open | Red chosen | Red block rate | Regain share of research | Win rate by Blue dice 0 / 1 / 2+ | Win rate by Red dice 0 / 1 / 2+ |
|---|---|---|---|---|---|---|---|---|
| V036 | 63.8 / 21.6 / 14.6 | 41431 | 6.3 | 21.5 | 14.7 | 25.6 | 24.1 (4875) / 39.6 (2046) / 48.8 (2079) | 35.2 (6152) / 32.4 (1736) / 24.4 (1112) |
| V037 | 59.8 / 32.2 / 8.0 | 42079 | 17.9 | 39.1 | 20.5 | 38.2 | 25.9 (4963) / 36.4 (1966) / 48.3 (2071) | 34.8 (6560) / 32.2 (1469) / 24.8 (971) |
| V037-S036 | 60.1 / 31.7 / 8.1 | 41267 | 16.6 | 38.2 | 20.5 | 38.5 | 25.6 (4931) / 36.2 (2004) / 49.0 (2065) | 34.5 (6576) / 33.8 (1475) / 24.3 (949) |
| V037-NAIVE | 64.0 / 21.6 / 14.5 | 28068 | 6.7 | 21.4 | 14.5 | 24.5 | 27.8 (3248) / 35.5 (1343) / 44.0 (1409) | 34.2 (4081) / 34.6 (1169) / 26.8 (750) |
| V037-ONE-AWARE | 63.1 / 23.8 / 13.1 | 42164 | 8.7 | 25.1 | 15.8 | 27.1 | 26.4 (4922) / 36.1 (2010) / 47.0 (2068) | 34.6 (6169) / 33.4 (1736) / 25.9 (1095) |

**Bot win rates (win credit; post-bonus, with pre-bonus in parentheses) and final Secrets pre → post (all seats, seed 42)**

| Cell | Accelerationist | AdaptiveBalanced | RecklessSaboteur | SecOpsTurtle | VentureGreed |
|---|---|---|---|---|---|
| V036 | 44.0 (44.0); 3.84→3.84 | 27.1 (27.1); 3.05→3.05 | 12.6 (12.6); 1.81→1.81 | 34.2 (34.2); 3.33→3.33 | 48.9 (48.9); 4.01→4.01 |
| V037 | 41.2 (45.0); 3.80→4.93 | 22.4 (24.6); 2.90→3.94 | 15.6 (11.9); 1.75→2.61 | 37.8 (35.4); 3.32→4.65 | 49.8 (49.8); 3.94→5.21 |
| V037-S036 | 41.4 (44.5); 3.17→4.31 | 23.2 (25.4); 2.32→3.32 | 15.5 (12.2); 1.23→2.00 | 36.6 (35.1); 2.70→3.99 | 49.9 (49.5); 3.24→4.47 |
| V037-NAIVE | 35.9 (43.7); 4.62→5.67 | 23.9 (27.8); 3.80→4.81 | 19.0 (12.5); 2.52→3.60 | 40.6 (34.4); 4.07→5.50 | 47.2 (48.4); 4.77→6.01 |
| V037-ONE-AWARE | 40.1 (44.7); 4.51→5.62 | 22.4 (25.4); 3.60→4.59 | 16.2 (12.2); 2.35→3.34 | 39.9 (35.2); 4.00→5.40 | 48.1 (49.1); 4.69→5.91 |

**Setup concentration and company spread (seed 42)**

| Cell | Max trigger, v3.0 card | Max trigger, company@seat | Max trigger, White Hat@seat | Company spread pts (bootstrap CI) | Tiebreak decided by (top 3) |
|---|---|---|---|---|---|
| V036 | CORRUPTED_KERNEL patient_zero 38.6 (n=1507) | AEGIS@2 patient_zero 40.8 (n=463) | PHREAKER@2 patient_zero 39.7 (n=517) | 21.1 [18.43, 25.16] | secrets 66.9, market_share 18.7, sole_survivor 7.5 |
| V037 | ZERO_DAY_OVERRIDE singularity 41.4 (n=1493) | AEGIS@1 singularity 46.3 (n=471) | OPERATOR@1 singularity 43.3 (n=490) | 14.6 [12.54, 19.12] | secrets 68.9, market_share 13.3, sole_survivor 9.4 |
| V037-S036 | CORRUPTED_KERNEL patient_zero 50.2 (n=1507) | OMNIDYNE@0 patient_zero 51.9 (n=466) | PHREAKER@0 patient_zero 49.9 (n=469) | 15.8 [13.64, 19.61] | secrets 67.0, market_share 12.9, sole_survivor 11.6 |
| V037-NAIVE | ZERO_DAY_OVERRIDE singularity 39.3 (n=997) | DTO@1 singularity 41.8 (n=335) | OPERATOR@1 singularity 41.2 (n=313) | 18.6 [15.44, 23.76] | secrets 72.1, market_share 15.5, sole_survivor 5.5 |
| V037-ONE-AWARE | ZERO_DAY_OVERRIDE singularity 39.4 (n=1493) | MERIDIAN@1 singularity 42.1 (n=520) | SPOOK@0 singularity 40.8 (n=498) | 17.7 [14.61, 21.89] | secrets 73.7, market_share 13.7, sole_survivor 6.0 |

### 4P

**Endings, Total Wipeout, rounds (seed 42; 95% Wilson CIs)**

| Cell | n | Patient Zero (incl. TW) | Singularity | Market Collapse | Total Wipeout | Rounds mean / median / sd |
|---|---|---|---|---|---|---|
| V036 | 3000 | 29.4 [27.8, 31.1] | 34.5 [32.8, 36.2] | 36.1 [34.4, 37.8] | 1.0 [0.7, 1.4] | 8.84 / 9.0 / 1.16 |
| V037 | 3000 | 30.4 [28.8, 32.1] | 40.1 [38.4, 41.9] | 29.4 [27.8, 31.1] | 1.6 [1.2, 2.1] | 8.99 / 9.0 / 1.09 |
| V037-S036 | 3000 | 38.5 [36.8, 40.3] | 35.1 [33.4, 36.8] | 26.4 [24.9, 28.0] | 1.8 [1.4, 2.3] | 8.84 / 9.0 / 1.17 |
| V037-NAIVE | 2000 | 24.7 [22.9, 26.6] | 37.0 [35.0, 39.2] | 38.2 [36.1, 40.4] | 0.8 [0.5, 1.3] | 8.96 / 9.0 / 1.08 |
| V037-ONE-AWARE | 3000 | 25.3 [23.7, 26.9] | 38.3 [36.6, 40.1] | 36.4 [34.7, 38.2] | 0.7 [0.5, 1.1] | 8.96 / 9.0 / 1.08 |

**Market Leader Bonus metrics (seed 42)**

| Cell | Winner changed / awarded | Winner changed / all games | Paid place tied / awarded | Highest-MS survivor wins | Lowest-MS survivor wins | Bonus-aware seat edge (pts, CI) | Survivor Secrets pre → post | Mean bonus by place |
|---|---|---|---|---|---|---|---|---|
| V036 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.1] | 0.0 | 34.1 [32.6, 35.5] | 22.7 [21.5, 23.9] | – | 4.73 → 4.73 | 1:0, 2:0, 3:0, 4:0 |
| V037 | 24.9 [23.4, 26.5] | 24.5 [23.0, 26.1] | 59.9 | 48.6 [47.1, 50.1] | 13.6 [12.6, 14.6] | – | 4.88 → 5.98 | 1:2, 2:1, 3:0, 4:0 |
| V037-S036 | 24.3 [22.8, 25.9] | 23.9 [22.4, 25.4] | 57.0 | 50.7 [49.2, 52.3] | 13.2 [12.2, 14.3] | – | 4.24 → 5.35 | 1:2, 2:1, 3:0, 4:0 |
| V037-NAIVE | 25.4 [23.5, 27.3] | 25.1 [23.3, 27.1] | 62.2 | 50.5 [48.6, 52.3] | 11.5 [10.4, 12.7] | – | 5.41 → 6.49 | 1:2, 2:1, 3:0, 4:0 |
| V037-ONE-AWARE | 24.7 [23.2, 26.2] | 24.5 [23.0, 26.1] | 59.4 | 49.5 [48.0, 51.1] | 11.8 [10.9, 12.8] | +7.4 [+5.7, +9.0] (seat 32.4% vs 25.0%) | 5.38 → 6.45 | 1:2, 2:1, 3:0, 4:0 |

**Blue agency (seed 42)**

| Cell | Generic shields on Blue / Red / Green | Contested rounds | Blue left open | Red chosen | Red block rate | Regain share of research | Win rate by Blue dice 0 / 1 / 2+ | Win rate by Red dice 0 / 1 / 2+ |
|---|---|---|---|---|---|---|---|---|
| V036 | 63.0 / 22.0 / 15.0 | 55584 | 6.6 | 21.8 | 14.9 | 24.2 | 16.5 (6612) / 30.2 (2663) / 40.5 (2725) | 27.1 (8124) / 25.3 (2283) / 13.8 (1593) |
| V037 | 59.3 / 32.8 / 7.8 | 56232 | 17.1 | 39.8 | 20.9 | 36.1 | 18.3 (6757) / 28.7 (2589) / 38.5 (2654) | 26.6 (8554) / 24.5 (2060) / 16.1 (1386) |
| V037-S036 | 59.6 / 32.5 / 7.9 | 55394 | 16.2 | 39.2 | 21.0 | 36.2 | 18.3 (6715) / 28.1 (2600) / 38.7 (2685) | 26.5 (8573) / 24.8 (2059) / 15.8 (1368) |
| V037-NAIVE | 63.3 / 21.9 / 14.8 | 37429 | 6.9 | 21.8 | 14.7 | 23.7 | 19.9 (4387) / 28.0 (1783) / 34.4 (1830) | 25.3 (5451) / 28.6 (1482) / 18.3 (1067) |
| V037-ONE-AWARE | 62.5 / 23.8 / 13.7 | 56133 | 8.3 | 24.7 | 15.8 | 25.5 | 19.3 (6680) / 26.4 (2615) / 37.7 (2705) | 25.7 (8160) / 28.4 (2245) / 16.6 (1595) |

**Bot win rates (win credit; post-bonus, with pre-bonus in parentheses) and final Secrets pre → post (all seats, seed 42)**

| Cell | Accelerationist | AdaptiveBalanced | RecklessSaboteur | SecOpsTurtle | VentureGreed |
|---|---|---|---|---|---|
| V036 | 33.3 (33.3); 4.73→4.73 | 14.8 (14.8); 3.88→3.88 | 6.7 (6.7); 2.66→2.66 | 26.7 (26.7); 4.36→4.36 | 43.5 (43.5); 4.92→4.92 |
| V037 | 30.2 (35.3); 4.81→5.74 | 12.6 (13.5); 3.85→4.64 | 8.4 (6.5); 2.72→3.50 | 29.8 (25.4); 4.39→5.59 | 43.9 (44.4); 5.02→6.11 |
| V037-S036 | 30.2 (34.8); 4.08→5.00 | 13.2 (13.4); 3.19→3.98 | 8.2 (6.2); 2.05→2.75 | 30.3 (26.2); 3.73→4.92 | 43.1 (44.4); 4.28→5.36 |
| V037-NAIVE | 26.8 (33.8); 5.43→6.25 | 12.5 (15.1); 4.57→5.31 | 12.3 (6.9); 3.35→4.31 | 33.9 (26.8); 5.06→6.34 | 39.6 (42.5); 5.63→6.70 |
| V037-ONE-AWARE | 29.2 (34.3); 5.44→6.33 | 12.3 (13.7); 4.48→5.20 | 10.7 (6.3); 3.33→4.25 | 31.6 (26.0); 5.00→6.21 | 41.2 (44.7); 5.68→6.75 |

**Setup concentration and company spread (seed 42)**

| Cell | Max trigger, v3.0 card | Max trigger, company@seat | Max trigger, White Hat@seat | Company spread pts (bootstrap CI) | Tiebreak decided by (top 3) |
|---|---|---|---|---|---|
| V036 | ZERO_DAY_OVERRIDE market_collapse 37.9 (n=1482) | PROMETHEUS@0 market_collapse 40.0 (n=533) | SPOOK@2 market_collapse 38.8 (n=495) | 23.5 [20.49, 26.5] | secrets 71.8, market_share 19.3, money 4.6 |
| V037 | ZERO_DAY_OVERRIDE singularity 42.4 (n=1482) | AEGIS@0 singularity 45.4 (n=449) | ACOUSTIC@0 singularity 42.9 (n=543) | 16.6 [14.62, 19.82] | secrets 72.9, market_share 16.4, money 5.8 |
| V037-S036 | CORRUPTED_KERNEL patient_zero 42.9 (n=1518) | AEGIS@1 patient_zero 42.4 (n=505) | ACOUSTIC@2 patient_zero 41.3 (n=463) | 15.7 [14.01, 19.37] | secrets 71.9, market_share 16.0, money 6.4 |
| V037-NAIVE | ZERO_DAY_OVERRIDE market_collapse 39.4 (n=974) | AEGIS@0 singularity 43.9 (n=305) | OPERATOR@1 market_collapse 41.1 (n=314) | 17.4 [14.92, 20.46] | secrets 75.0, market_share 16.4, money 4.7 |
| V037-ONE-AWARE | ZERO_DAY_OVERRIDE singularity 39.2 (n=1482) | AEGIS@0 singularity 42.5 (n=449) | PHREAKER@0 singularity 40.3 (n=509) | 16.5 [13.55, 19.28] | secrets 75.9, market_share 14.6, money 5.3 |


## 7. Seed 42 vs seed 7000 agreement

Every V036 / V037 / V037-ONE-AWARE metric agrees within 3 pts across bases (largest: 4P ONE-AWARE edge +2.1, 4P ONE-AWARE Market Collapse +2.0, 3P V036 Patient Zero −1.9). No row is flagged.


| Pod | Cell | Metric | Seed 42 | Seed 7000 | Δ (pts) |
|---|---|---|---|---|---|
| 2P | V036 | Patient Zero | 30.5 | 30.0 | -0.5 |
| 2P | V036 | Singularity | 35.1 | 35.5 | +0.4 |
| 2P | V036 | Market Collapse | 34.4 | 34.5 | +0.1 |
| 2P | V036 | Total Wipeout | 7.6 | 7.1 | -0.5 |
| 2P | V036 | Any shields on Blue | 63.3 | 63.1 | -0.2 |
| 2P | V036 | Blue left open | 7.1 | 7.3 | +0.1 |
| 2P | V036 | Lowest-MS survivor wins | 45.1 | 44.2 | -0.9 |
| 2P | V037 | Patient Zero | 27.0 | 27.0 | +0.0 |
| 2P | V037 | Singularity | 47.1 | 46.7 | -0.4 |
| 2P | V037 | Market Collapse | 25.9 | 26.3 | +0.4 |
| 2P | V037 | Total Wipeout | 8.4 | 7.7 | -0.7 |
| 2P | V037 | Winner changed / awarded | 11.7 | 12.7 | +1.0 |
| 2P | V037 | Any shields on Blue | 57.0 | 56.8 | -0.1 |
| 2P | V037 | Blue left open | 23.1 | 23.2 | +0.1 |
| 2P | V037 | Lowest-MS survivor wins | 33.5 | 32.6 | -0.9 |
| 2P | V037-ONE-AWARE | Patient Zero | 19.8 | 21.0 | +1.2 |
| 2P | V037-ONE-AWARE | Singularity | 44.2 | 42.4 | -1.8 |
| 2P | V037-ONE-AWARE | Market Collapse | 36.0 | 36.6 | +0.6 |
| 2P | V037-ONE-AWARE | Total Wipeout | 5.3 | 5.4 | +0.0 |
| 2P | V037-ONE-AWARE | Winner changed / awarded | 16.2 | 16.3 | +0.1 |
| 2P | V037-ONE-AWARE | Any shields on Blue | 62.0 | 61.8 | -0.1 |
| 2P | V037-ONE-AWARE | Blue left open | 11.3 | 11.6 | +0.3 |
| 2P | V037-ONE-AWARE | Lowest-MS survivor wins | 31.0 | 30.0 | -1.0 |
| 2P | V037-ONE-AWARE | Bonus-aware edge (pts) | 7.9 | 7.7 | -0.2 |
| 2P | V037 | Rounds | 9.14 | 9.13 | – |
| 3P | V036 | Patient Zero | 34.8 | 32.9 | -1.9 |
| 3P | V036 | Singularity | 32.6 | 34.1 | +1.5 |
| 3P | V036 | Market Collapse | 32.5 | 32.9 | +0.4 |
| 3P | V036 | Total Wipeout | 2.6 | 2.6 | +0.0 |
| 3P | V036 | Any shields on Blue | 63.8 | 62.8 | -1.0 |
| 3P | V036 | Blue left open | 6.3 | 6.4 | +0.1 |
| 3P | V036 | Lowest-MS survivor wins | 31.4 | 32.6 | +1.3 |
| 3P | V037 | Patient Zero | 37.5 | 36.0 | -1.5 |
| 3P | V037 | Singularity | 39.9 | 40.8 | +0.9 |
| 3P | V037 | Market Collapse | 22.6 | 23.2 | +0.6 |
| 3P | V037 | Total Wipeout | 4.2 | 3.3 | -0.8 |
| 3P | V037 | Winner changed / awarded | 15.1 | 15.7 | +0.6 |
| 3P | V037 | Any shields on Blue | 59.8 | 58.8 | -1.0 |
| 3P | V037 | Blue left open | 17.9 | 17.6 | -0.4 |
| 3P | V037 | Lowest-MS survivor wins | 21.9 | 21.2 | -0.7 |
| 3P | V037-ONE-AWARE | Patient Zero | 29.0 | 27.6 | -1.4 |
| 3P | V037-ONE-AWARE | Singularity | 37.8 | 38.7 | +0.9 |
| 3P | V037-ONE-AWARE | Market Collapse | 33.2 | 33.6 | +0.5 |
| 3P | V037-ONE-AWARE | Total Wipeout | 2.8 | 1.7 | -1.0 |
| 3P | V037-ONE-AWARE | Winner changed / awarded | 17.5 | 18.3 | +0.8 |
| 3P | V037-ONE-AWARE | Any shields on Blue | 63.1 | 62.1 | -1.0 |
| 3P | V037-ONE-AWARE | Blue left open | 8.7 | 8.5 | -0.2 |
| 3P | V037-ONE-AWARE | Lowest-MS survivor wins | 20.6 | 20.3 | -0.3 |
| 3P | V037-ONE-AWARE | Bonus-aware edge (pts) | 6.2 | 7.6 | +1.4 |
| 3P | V037 | Rounds | 8.97 | 8.98 | – |
| 4P | V036 | Patient Zero | 29.4 | 30.5 | +1.1 |
| 4P | V036 | Singularity | 34.5 | 34.1 | -0.4 |
| 4P | V036 | Market Collapse | 36.1 | 35.4 | -0.7 |
| 4P | V036 | Total Wipeout | 1.0 | 1.0 | +0.0 |
| 4P | V036 | Any shields on Blue | 63.0 | 63.3 | +0.3 |
| 4P | V036 | Blue left open | 6.6 | 6.5 | -0.1 |
| 4P | V036 | Lowest-MS survivor wins | 22.7 | 22.9 | +0.2 |
| 4P | V037 | Patient Zero | 30.4 | 30.6 | +0.2 |
| 4P | V037 | Singularity | 40.1 | 39.6 | -0.6 |
| 4P | V037 | Market Collapse | 29.4 | 29.8 | +0.4 |
| 4P | V037 | Total Wipeout | 1.6 | 1.6 | +0.0 |
| 4P | V037 | Winner changed / awarded | 24.9 | 23.9 | -1.0 |
| 4P | V037 | Any shields on Blue | 59.3 | 59.3 | -0.1 |
| 4P | V037 | Blue left open | 17.1 | 17.7 | +0.6 |
| 4P | V037 | Lowest-MS survivor wins | 13.6 | 13.4 | -0.2 |
| 4P | V037-ONE-AWARE | Patient Zero | 25.3 | 24.8 | -0.5 |
| 4P | V037-ONE-AWARE | Singularity | 38.3 | 36.8 | -1.5 |
| 4P | V037-ONE-AWARE | Market Collapse | 36.4 | 38.4 | +2.0 |
| 4P | V037-ONE-AWARE | Total Wipeout | 0.7 | 0.8 | +0.1 |
| 4P | V037-ONE-AWARE | Winner changed / awarded | 24.7 | 25.8 | +1.2 |
| 4P | V037-ONE-AWARE | Any shields on Blue | 62.5 | 62.9 | +0.4 |
| 4P | V037-ONE-AWARE | Blue left open | 8.3 | 8.3 | -0.1 |
| 4P | V037-ONE-AWARE | Lowest-MS survivor wins | 11.8 | 12.3 | +0.5 |
| 4P | V037-ONE-AWARE | Bonus-aware edge (pts) | 7.4 | 9.4 | +2.1 |
| 4P | V037 | Rounds | 8.99 | 8.97 | – |


## 8. Outlier seeds

No game in any cell or seed base reached ≥ 15 rounds (maximum 12, one game in 2P V037 and one in 3P V036). No Market Collapse ended a game in ≤ 5 rounds. Patient Zero or Total Wipeout in ≤ 3 rounds is rare: seed 300948 and 301520 (3P V036 and V037-S036, base 42), 208078 (2P V036, base 7000), 309380 (3P V036/V037/ONE-AWARE, base 7000). V037 cuts very short games: 2P ≤ 5-round games drop from 26 (V036) to 0. The V037-S036 ablation brings them back (26).

"Extreme bonus flips" are measured as (i) the bonus overturned a 2-Secret pre-bonus lead (the maximum possible: lead 2 then 2P +2 ties, and the Market Share tiebreak decides), and (ii) at 3–4P, the new winner had the fewest pre-bonus Secrets among ≥ 3 survivors. **At 2P, 43% of flips (140 of 322) overturn a 2-Secret lead**: the +2 bonus plus Market Share as the first tiebreaker means 1st place is worth +2 Secrets and also wins every tie that the +2 creates. The game-designer should review this.

**Counts (seed 42 / seed 7000; "–" = cell not run at 7000)**


| Pod | Cell | PZ/TW ≤ 3 rounds | ≥ 15 rounds | any end ≤ 5 rounds | Flip overturned a 2-Secret pre-bonus lead | Flip winner was last pre-bonus (≥3 survivors) | Flip lead dist (lead:games) |
|---|---|---|---|---|---|---|---|
| 2P | V036 | 0 / 1 | 0 / 0 | 26 / 28 | 0 / 0 | 0 / 0 | {} |
| 2P | V037 | 0 / 0 | 0 / 0 | 0 / 1 | 140 / 143 | 0 / 0 | {'1': 182, '2': 140} |
| 2P | V037-S036 | 0 / – | 0 / – | 26 / – | 105 / – | 0 / – | {'1': 152, '2': 105} |
| 2P | V037-NAIVE | 0 / – | 0 / – | 0 / – | 146 / – | 0 / – | {'1': 194, '2': 146} |
| 2P | V037-ONE-AWARE | 0 / 0 | 0 / 0 | 0 / 1 | 196 / 183 | 0 / 0 | {'1': 263, '2': 196} |
| 3P | V036 | 2 / 1 | 0 / 0 | 50 / 35 | 0 / 0 | 0 / 0 | {} |
| 3P | V037 | 0 / 1 | 0 / 0 | 18 / 8 | 91 / 84 | 159 / 176 | {'1': 342, '2': 91} |
| 3P | V037-S036 | 2 / – | 0 / – | 50 / – | 78 / – | 148 / – | {'1': 330, '2': 78} |
| 3P | V037-NAIVE | 0 / – | 0 / – | 13 / – | 60 / – | 159 / – | {'1': 304, '2': 60} |
| 3P | V037-ONE-AWARE | 0 / 1 | 0 / 0 | 18 / 8 | 87 / 90 | 203 / 210 | {'1': 424, '2': 87} |
| 4P | V036 | 0 / 0 | 0 / 0 | 20 / 21 | 0 / 0 | 0 / 0 | {} |
| 4P | V037 | 0 / 0 | 0 / 0 | 8 / 4 | 214 / 203 | 178 / 193 | {'1': 522, '2': 214} |
| 4P | V037-S036 | 0 / – | 0 / – | 21 / – | 199 / – | 184 / – | {'1': 517, '2': 199} |
| 4P | V037-NAIVE | 0 / – | 0 / – | 7 / – | 122 / – | 132 / – | {'1': 381, '2': 122} |
| 4P | V037-ONE-AWARE | 0 / 0 | 0 / 0 | 7 / 4 | 192 / 234 | 169 / 188 | {'1': 543, '2': 192} |

**Seed lists (first ≤ 10 per category)**

- base 42, 2P V037, `flip_overturned_pre_bonus_lead_ge_2`: 200044, 200050, 200059, 200061, 200077, 200079, 200117, 200139, 200145, 200182
- base 42, 2P V037-NAIVE, `flip_overturned_pre_bonus_lead_ge_2`: 200074, 200079, 200086, 200098, 200100, 200114, 200117, 200136, 200139, 200152
- base 42, 2P V037-ONE-AWARE, `flip_overturned_pre_bonus_lead_ge_2`: 200043, 200044, 200063, 200113, 200114, 200117, 200120, 200136, 200142, 200143
- base 42, 2P V037-S036, `flip_overturned_pre_bonus_lead_ge_2`: 200050, 200059, 200061, 200079, 200117, 200182, 200231, 200246, 200335, 200374
- base 42, 3P V036, `pz_or_tw_le_3_rounds`: 300948, 301520
- base 42, 3P V037, `flip_winner_was_last_pre_bonus`: 300068, 300078, 300084, 300095, 300141, 300165, 300168, 300187, 300222, 300225
- base 42, 3P V037, `flip_overturned_pre_bonus_lead_ge_2`: 300078, 300133, 300165, 300179, 300240, 300267, 300301, 300321, 300425, 300453
- base 42, 3P V037-NAIVE, `flip_winner_was_last_pre_bonus`: 300051, 300054, 300066, 300087, 300105, 300132, 300134, 300140, 300142, 300159
- base 42, 3P V037-NAIVE, `flip_overturned_pre_bonus_lead_ge_2`: 300054, 300060, 300146, 300159, 300202, 300238, 300240, 300271, 300328, 300396
- base 42, 3P V037-ONE-AWARE, `flip_overturned_pre_bonus_lead_ge_2`: 300064, 300121, 300167, 300204, 300240, 300266, 300324, 300328, 300357, 300391
- base 42, 3P V037-ONE-AWARE, `flip_winner_was_last_pre_bonus`: 300064, 300068, 300073, 300087, 300092, 300103, 300110, 300132, 300133, 300134
- base 42, 3P V037-S036, `flip_winner_was_last_pre_bonus`: 300068, 300078, 300084, 300132, 300141, 300165, 300168, 300187, 300196, 300222
- base 42, 3P V037-S036, `flip_overturned_pre_bonus_lead_ge_2`: 300078, 300133, 300165, 300179, 300240, 300267, 300301, 300321, 300425, 300453
- base 42, 3P V037-S036, `pz_or_tw_le_3_rounds`: 300948, 301520
- base 42, 4P V037, `flip_overturned_pre_bonus_lead_ge_2`: 400050, 400053, 400086, 400088, 400109, 400111, 400140, 400161, 400170, 400176
- base 42, 4P V037, `flip_winner_was_last_pre_bonus`: 400053, 400086, 400088, 400101, 400114, 400115, 400152, 400160, 400171, 400190
- base 42, 4P V037-NAIVE, `flip_winner_was_last_pre_bonus`: 400052, 400058, 400064, 400094, 400095, 400119, 400131, 400158, 400159, 400171
- base 42, 4P V037-NAIVE, `flip_overturned_pre_bonus_lead_ge_2`: 400096, 400109, 400131, 400159, 400164, 400227, 400234, 400246, 400250, 400266
- base 42, 4P V037-ONE-AWARE, `flip_overturned_pre_bonus_lead_ge_2`: 400042, 400053, 400062, 400067, 400086, 400098, 400109, 400120, 400131, 400147
- base 42, 4P V037-ONE-AWARE, `flip_winner_was_last_pre_bonus`: 400042, 400047, 400053, 400062, 400064, 400077, 400094, 400095, 400131, 400158
- base 42, 4P V037-S036, `flip_overturned_pre_bonus_lead_ge_2`: 400050, 400053, 400086, 400088, 400109, 400140, 400161, 400170, 400176, 400179
- base 42, 4P V037-S036, `flip_winner_was_last_pre_bonus`: 400053, 400072, 400086, 400088, 400101, 400114, 400115, 400152, 400160, 400171
- base 7000, 2P V036, `pz_or_tw_le_3_rounds`: 208078
- base 7000, 2P V037, `flip_overturned_pre_bonus_lead_ge_2`: 207001, 207015, 207037, 207068, 207083, 207089, 207093, 207109, 207116, 207160
- base 7000, 2P V037-ONE-AWARE, `flip_overturned_pre_bonus_lead_ge_2`: 207026, 207027, 207049, 207057, 207063, 207083, 207090, 207093, 207109, 207168
- base 7000, 3P V036, `pz_or_tw_le_3_rounds`: 309380
- base 7000, 3P V037, `flip_winner_was_last_pre_bonus`: 307000, 307003, 307016, 307035, 307057, 307072, 307077, 307086, 307106, 307107
- base 7000, 3P V037, `flip_overturned_pre_bonus_lead_ge_2`: 307003, 307072, 307086, 307112, 307125, 307145, 307225, 307265, 307272, 307330
- base 7000, 3P V037, `pz_or_tw_le_3_rounds`: 309380
- base 7000, 3P V037-ONE-AWARE, `flip_overturned_pre_bonus_lead_ge_2`: 307000, 307069, 307088, 307140, 307177, 307197, 307204, 307229, 307264, 307295
- base 7000, 3P V037-ONE-AWARE, `flip_winner_was_last_pre_bonus`: 307000, 307016, 307020, 307032, 307047, 307073, 307077, 307082, 307088, 307091
- base 7000, 3P V037-ONE-AWARE, `pz_or_tw_le_3_rounds`: 309380
- base 7000, 4P V037, `flip_overturned_pre_bonus_lead_ge_2`: 407003, 407015, 407017, 407037, 407051, 407071, 407073, 407079, 407081, 407089
- base 7000, 4P V037, `flip_winner_was_last_pre_bonus`: 407003, 407017, 407031, 407037, 407051, 407081, 407094, 407103, 407108, 407130
- base 7000, 4P V037-ONE-AWARE, `flip_overturned_pre_bonus_lead_ge_2`: 407025, 407055, 407056, 407066, 407069, 407074, 407081, 407086, 407096, 407128
- base 7000, 4P V037-ONE-AWARE, `flip_winner_was_last_pre_bonus`: 407058, 407069, 407085, 407086, 407096, 407101, 407141, 407144, 407158, 407179

## 9. Anomalies, missing hooks, notes

1. **2P Singularity fails at the spec's two seed bases** (47.1 / 46.7). Pooled over 4 bases it is 46.0 [45.1, 46.9], at the fail line. The ablation points to the 9-Secret 2P start as the driver. Its counterweight is Patient Zero / Total Wipeout (S036: 42.2 / 12.0).
2. **Winner changed runs low against §38 at 2P** (11.7 / 12.7 vs 15–18; flag > 3 pts) and somewhat low at 3P (15.1 / 15.7 vs 17–20). Endings, Total Wipeout and the bonus-aware edge port within 2 pts, so this is likely a definition or tie-handling difference in `market_leader_bonus_changed_winner` / `pre_bonus_winner_ids` versus the probe. Recommend a staff-engineer check of the §4.3 definition against `scripts/explore_v360_share_placement_probe.py`. Not patched (out of product-owner scope).
3. **Missing hook: Blue block rate.** No per-player Blue incoming or blocked counters exist in `RoundTelemetry` or the ranking rows. Blue agency is measured here only through Generic (`Any`) shield split, contested choices and Blue dice owned.
4. **Script coverage gaps** (filled by the read-only supplementary pass, not by editing the script): the sweep does not aggregate win rate by Red dice owned, pre-bonus bot win rates, per-bot Secrets pre/post, or round-based outlier seeds. Its `seed_log` only lists `bonus_changed_winner` (first 50).
5. **Bot shifts under V037:** RecklessSaboteur gains +8 pts at 2P (29.4 → 37.7) and +3 / +2 at 3P/4P. Accelerationist and AdaptiveBalanced lose 3–6 pts. SecOpsTurtle gains 3–5 pts. VentureGreed is flat. Bonus flips mostly move wins from Accelerationist to Reckless and SecOps (compare the pre- and post-bonus columns).
6. **Win rate by Red dice owned** stays highest at 0–1 Red dice in every pod. 2+ Red dice is the weakest bucket (2P 46.6, 3P 24.8, 4P 16.1), slightly better than in V036. This matches §38 finding 5: buying Red dice does not pay.
7. **Terminology note:** ranking rows and `tiebreak_decided_by` still use the internal key `patches` (deprecated term). It is internal telemetry only and appears nowhere player-facing. Flagged for glossary governance, not changed.
8. No crashes, no invariant errors, deterministic across re-runs.
