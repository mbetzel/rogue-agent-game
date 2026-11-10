# Phase 48 Lever A tuning sweep (product-owner, data only)

Setup: GameConfig.v037, baseline `_bot_classes` rotation, seeds 42 + P*100000 + idx (3P = 42+300000+idx), 8 procs. Errors: 0 in every run.
Sweep driven by `scripts/run_lever_a_sweep.py` through a scratchpad wrapper that only adds a Secrets-lost-to-Blue counter per seat (top-level engine, same method as run_reference_bot_validation). Cells with duplicate params collapse (the script skips them).
Window % = share of AdaptiveBalanced window decisions (all hooks pooled) in dump / none / push.
Guard = Patient Zero and Total Wipeout each no more than +2 pts vs off. **The "no archetype above ~40% at 3P" guardrail fails in every cell, off included: VentureGreed is 50-52% at 3P with the switch off.** The switch slightly lowers it, so it is reported here as "not worse than off".
Compute: about 45 min (sweep runs in seconds; the 8 ref1 runs took about 5 min each).

## Step 1+2: 3P sweep, 600 games (the specified count)
| cell | AB win % [95% CI] | max archetype win % | PZ % (Δoff) | TW % (Δoff) | Sing % | MC % | rounds | AB Secrets lost Blue | all Secrets lost Blue | AB P4 push/dump/none % | guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 18.3 [14.7, 22.7] | 52.8 (Vent) | 8.7 (+0.0) | 0.2 (+0.0) | 34.8 | 62.7 | 9.01 | 3.50 | 3.34 | 100 (none) | PASS |
| on | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.03 | 3.22 | 11/12/76 (dump,none,push) | PASS |
| push_min_share=5 | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 33.2 | 63.8 | 9.00 | 3.16 | 3.26 | 9/14/76 (dump,none,push) | PASS |
| push_min_share=7 | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.03 | 3.22 | 11/13/76 (dump,none,push) | PASS |
| push_low_gap=5 | 24.0 [19.9, 28.7] | 50.8 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.03 | 3.22 | 11/13/76 (dump,none,push) | PASS |
| push_low_gap=9 | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.03 | 3.22 | 11/12/76 (dump,none,push) | PASS |
| push_top_gap=2 | 24.0 [19.9, 28.7] | 50.8 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.04 | 3.22 | 11/13/76 (dump,none,push) | PASS |
| push_top_gap=4 | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.03 | 3.22 | 11/12/76 (dump,none,push) | PASS |
| push_secrets_band=3 | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 33.0 | 63.8 | 8.99 | 3.04 | 3.22 | 11/10/78 (dump,none,push) | PASS |
| dump_max_share=4 | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 33.2 | 63.8 | 9.00 | 3.16 | 3.26 | 9/15/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=1,dump_threat_margin=2 | 24.0 [19.9, 28.7] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 33.0 | 64.0 | 8.99 | 3.08 | 3.23 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=1,dump_threat_margin=3 | 24.0 [19.9, 28.7] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.05 | 3.23 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=2,dump_threat_margin=2 | 23.8 [19.6, 28.4] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 33.0 | 64.0 | 9.00 | 3.16 | 3.25 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=2,dump_threat_margin=3 | 23.8 [19.6, 28.4] | 51.4 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.10 | 3.24 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=3,dump_threat_margin=2 | 23.5 [19.4, 28.1] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 33.2 | 63.8 | 9.00 | 3.20 | 3.26 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=3,dump_threat_margin=3 | 23.5 [19.4, 28.1] | 51.4 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.8 | 64.2 | 8.99 | 3.13 | 3.24 | 11/13/76 (dump,none,push) | PASS |
| {"push_blue_slack": 1} | 13.9 [10.7, 17.8] | 53.6 (Vent) | 10.2 (+1.5) | 0.3 (+0.2) | 31.7 | 64.2 | 8.98 | 4.50 | 3.49 | 9/35/56 (dump,none,push) | PASS |
| {"push_top_gap": 1} | 24.0 [19.9, 28.7] | 50.3 (Vent) | 7.8 (-0.8) | 0.2 (+0.0) | 33.2 | 63.8 | 9.00 | 3.03 | 3.22 | 11/16/73 (dump,none,push) | PASS |
| {"push_low_gap": 3} | 23.2 [19.1, 27.8] | 51.1 (Vent) | 8.0 (-0.7) | 0.2 (+0.0) | 32.7 | 64.3 | 8.99 | 3.01 | 3.21 | 11/16/72 (dump,none,push) | PASS |
| {"push_secrets_band": 1} | 23.8 [19.6, 28.4] | 51.4 (Vent) | 7.7 (-1.0) | 0.2 (+0.0) | 32.7 | 64.5 | 8.99 | 2.99 | 3.22 | 11/19/70 (dump,none,push) | PASS |

## Step 1+2 rerun at 6,000 games, 3P (extra, because the 600-game CIs are about ±4 pts; same seed scheme)
| cell | AB win % [95% CI] | max archetype win % | PZ % (Δoff) | TW % (Δoff) | Sing % | MC % | rounds | AB Secrets lost Blue | all Secrets lost Blue | AB P4 push/dump/none % | guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 18.2 [17.0, 19.5] | 52.2 (Vent) | 8.8 (+0.0) | 0.2 (+0.0) | 34.0 | 63.2 | 8.97 | 3.45 | 3.30 | 100 (none) | PASS |
| on | 27.7 [26.3, 29.2] | 50.4 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.12 | 3.25 | 11/12/76 (dump,none,push) | PASS |
| push_min_share=5 | 27.7 [26.3, 29.2] | 50.5 (Vent) | 8.8 (-0.1) | 0.3 (+0.0) | 34.3 | 62.5 | 8.98 | 3.25 | 3.28 | 9/14/77 (dump,none,push) | PASS |
| push_min_share=7 | 27.7 [26.3, 29.2] | 50.4 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.12 | 3.25 | 11/13/76 (dump,none,push) | PASS |
| push_low_gap=5 | 27.7 [26.3, 29.2] | 50.3 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.12 | 3.25 | 11/13/76 (dump,none,push) | PASS |
| push_low_gap=9 | 27.7 [26.3, 29.2] | 50.4 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.12 | 3.25 | 11/12/76 (dump,none,push) | PASS |
| push_top_gap=2 | 27.6 [26.2, 29.1] | 50.4 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.13 | 3.25 | 11/13/76 (dump,none,push) | PASS |
| push_top_gap=4 | 27.7 [26.3, 29.2] | 50.4 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.12 | 3.25 | 11/12/77 (dump,none,push) | PASS |
| push_secrets_band=3 | 27.7 [26.3, 29.2] | 50.4 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.7 | 8.97 | 3.13 | 3.25 | 11/11/78 (dump,none,push) | PASS |
| dump_max_share=4 | 27.7 [26.3, 29.2] | 50.5 (Vent) | 8.8 (-0.1) | 0.3 (+0.0) | 34.3 | 62.5 | 8.98 | 3.25 | 3.28 | 9/14/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=1,dump_threat_margin=2 | 27.1 [25.7, 28.6] | 50.5 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.19 | 3.26 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=1,dump_threat_margin=3 | 27.4 [26.0, 28.9] | 50.5 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.16 | 3.26 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=2,dump_threat_margin=2 | 26.5 [25.1, 27.9] | 50.7 (Vent) | 8.7 (-0.1) | 0.3 (+0.0) | 34.1 | 62.7 | 8.98 | 3.28 | 3.28 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=2,dump_threat_margin=3 | 27.1 [25.6, 28.5] | 50.7 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.21 | 3.27 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=3,dump_threat_margin=2 | 26.4 [25.0, 27.8] | 50.8 (Vent) | 8.7 (-0.1) | 0.3 (+0.0) | 34.2 | 62.6 | 8.98 | 3.31 | 3.29 | 11/13/76 (dump,none,push) | PASS |
| reach_or_threat,dump_top_gap=3,dump_threat_margin=3 | 27.0 [25.6, 28.5] | 50.7 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.7 | 8.97 | 3.23 | 3.27 | 11/13/76 (dump,none,push) | PASS |
| {"push_blue_slack": 1} | 14.8 [13.7, 16.0] | 51.9 (Vent) | 11.0 (+2.2) | 0.3 (+0.0) | 33.3 | 62.6 | 8.96 | 4.59 | 3.51 | 8/35/56 (dump,none,push) | FAIL |
| {"push_top_gap": 1} | 27.6 [26.1, 29.1] | 50.3 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.13 | 3.25 | 11/15/73 (dump,none,push) | PASS |
| {"push_low_gap": 3} | 27.5 [26.0, 28.9] | 50.3 (Vent) | 8.6 (-0.2) | 0.3 (+0.0) | 34.1 | 62.8 | 8.97 | 3.12 | 3.25 | 11/16/73 (dump,none,push) | PASS |
| {"push_secrets_band": 1} | 27.5 [26.1, 29.0] | 50.6 (Vent) | 8.5 (-0.3) | 0.3 (+0.1) | 34.0 | 62.9 | 8.97 | 3.12 | 3.24 | 11/19/70 (dump,none,push) | PASS |

## Step 4a: confirmation, 1,200 games
### 2P
| cell | AB win % [95% CI] | max archetype win % | PZ % (Δoff) | TW % (Δoff) | Sing % | MC % | rounds | AB Secrets lost Blue | all Secrets lost Blue | AB P4 push/dump/none % | guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 39.1 [34.8, 43.5] | 59.0 (Vent) | 4.0 (+0.0) | 0.7 (+0.0) | 34.2 | 64.1 | 8.97 | 3.89 | 3.62 | 100 (none) | PASS |
| on | 51.2 [46.8, 55.7] | 59.0 (Vent) | 3.7 (-0.3) | 0.5 (-0.2) | 34.2 | 64.3 | 8.98 | 3.28 | 3.49 | 13/13/74 (dump,none,push) | PASS |
| push_top_gap=4 | 51.0 [46.6, 55.5] | 59.0 (Vent) | 3.7 (-0.3) | 0.5 (-0.2) | 34.1 | 64.4 | 8.98 | 3.28 | 3.49 | 13/12/75 (dump,none,push) | PASS |
| push_secrets_band=3 | 51.5 [47.0, 55.9] | 59.0 (Vent) | 3.7 (-0.3) | 0.5 (-0.2) | 34.2 | 64.3 | 8.97 | 3.28 | 3.49 | 13/11/76 (dump,none,push) | PASS |
| dump_max_share=4 | 51.9 [47.4, 56.3] | 59.0 (Vent) | 3.8 (-0.2) | 0.6 (-0.1) | 34.3 | 64.1 | 8.99 | 3.42 | 3.53 | 11/15/74 (dump,none,push) | PASS |
### 3P
| cell | AB win % [95% CI] | max archetype win % | PZ % (Δoff) | TW % (Δoff) | Sing % | MC % | rounds | AB Secrets lost Blue | all Secrets lost Blue | AB P4 push/dump/none % | guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 17.2 [14.6, 20.1] | 51.2 (Vent) | 9.4 (+0.0) | 0.1 (+0.0) | 34.2 | 62.8 | 8.99 | 3.53 | 3.40 | 100 (none) | PASS |
| on | 26.5 [23.4, 29.8] | 48.8 (Vent) | 9.1 (-0.3) | 0.3 (+0.2) | 33.7 | 62.6 | 8.99 | 3.13 | 3.31 | 11/13/76 (dump,none,push) | PASS |
| push_top_gap=4 | 26.5 [23.4, 29.8] | 48.8 (Vent) | 9.1 (-0.3) | 0.3 (+0.2) | 33.7 | 62.6 | 8.99 | 3.13 | 3.31 | 11/12/76 (dump,none,push) | PASS |
| push_secrets_band=3 | 26.5 [23.4, 29.8] | 48.9 (Vent) | 9.1 (-0.3) | 0.3 (+0.2) | 33.8 | 62.4 | 8.99 | 3.14 | 3.31 | 11/10/78 (dump,none,push) | PASS |
| dump_max_share=4 | 25.8 [22.7, 29.1] | 49.0 (Vent) | 9.2 (-0.2) | 0.3 (+0.2) | 33.9 | 62.3 | 9.01 | 3.27 | 3.35 | 9/15/76 (dump,none,push) | PASS |
### 4P
| cell | AB win % [95% CI] | max archetype win % | PZ % (Δoff) | TW % (Δoff) | Sing % | MC % | rounds | AB Secrets lost Blue | all Secrets lost Blue | AB P4 push/dump/none % | guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 8.8 [7.1, 10.7] | 44.8 (Vent) | 5.8 (+0.0) | 0.0 (+0.0) | 27.7 | 70.8 | 8.86 | 3.26 | 3.13 | 100 (none) | PASS |
| on | 16.1 [14.0, 18.6] | 43.5 (Vent) | 4.4 (-1.3) | 0.1 (+0.1) | 28.1 | 71.0 | 8.87 | 3.03 | 3.06 | 10/14/76 (dump,none,push) | PASS |
| push_top_gap=4 | 16.1 [14.0, 18.6] | 43.4 (Vent) | 4.4 (-1.3) | 0.1 (+0.1) | 28.1 | 71.0 | 8.87 | 3.03 | 3.06 | 10/14/76 (dump,none,push) | PASS |
| push_secrets_band=3 | 16.5 [14.2, 18.9] | 43.3 (Vent) | 4.4 (-1.3) | 0.1 (+0.1) | 28.0 | 71.1 | 8.87 | 3.04 | 3.07 | 10/11/78 (dump,none,push) | PASS |
| dump_max_share=4 | 16.2 [14.1, 18.7] | 43.8 (Vent) | 4.8 (-1.0) | 0.1 (+0.1) | 28.2 | 70.9 | 8.88 | 3.17 | 3.10 | 8/16/76 (dump,none,push) | PASS |

## Step 4b: ref1 (3P, 1,200) and Mixed seat (mixed1, 3P, 1,200; fair share 33.3%)
Last two rows = switch-off references from sim_results/reference_bot/. Files: sim_results/lever_a/sweep/{ref1,mixed1}_<cell>_<scope>_3p_1200.json (on = explicit {"push_min_share":6}, which equals the defaults).
| file | games | errors | special-seat win % [95% CI] | PZ % | MC % | special seat MLB 1st % | special seat Secrets lost Blue |
|---|---|---|---|---|---|---|---|
| mixed1_band3_all_3p_1200.json | 1200 | 0 | 32.6 [30.0, 35.3] | 10.8 | 61.0 | 51.8 | 3.40 |
| mixed1_dump4_all_3p_1200.json | 1200 | 0 | 32.9 [30.3, 35.6] | 11.1 | 60.2 | 52.2 | 3.42 |
| mixed1_on_all_3p_1200.json | 1200 | 0 | 32.7 [30.1, 35.4] | 10.9 | 60.7 | 52.0 | 3.40 |
| mixed1_top4_all_3p_1200.json | 1200 | 0 | 32.7 [30.1, 35.4] | 10.9 | 60.7 | 52.0 | 3.40 |
| ref1_band3_all_3p_1200.json | 1200 | 0 | 77.3 [74.9, 79.6] | 8.2 | 63.4 | 73.8 | 1.35 |
| ref1_band3_non_reference_3p_1200.json | 1200 | 0 | 71.4 [68.8, 73.9] | 6.8 | 62.8 | 68.0 | 1.39 |
| ref1_dump4_all_3p_1200.json | 1200 | 0 | 79.3 [77.0, 81.5] | 8.1 | 62.7 | 76.5 | 1.32 |
| ref1_dump4_non_reference_3p_1200.json | 1200 | 0 | 71.3 [68.7, 73.8] | 7.1 | 62.5 | 68.2 | 1.41 |
| ref1_on_all_3p_1200.json | 1200 | 0 | 77.1 [74.6, 79.4] | 7.8 | 62.8 | 74.0 | 1.33 |
| ref1_on_non_reference_3p_1200.json | 1200 | 0 | 71.2 [68.5, 73.7] | 7.0 | 62.8 | 68.1 | 1.40 |
| ref1_top4_all_3p_1200.json | 1200 | 0 | 77.7 [75.2, 79.9] | 7.8 | 62.9 | 74.1 | 1.32 |
| ref1_top4_non_reference_3p_1200.json | 1200 | 0 | 71.2 [68.5, 73.7] | 7.0 | 62.8 | 68.1 | 1.40 |
| v037_ref1_3p_1200.json | 1200 | 0 | 69.1 [66.4, 71.6] | 7.3 | 62.6 | 63.9 | 1.24 |
| v037_mixed1_3p_1200.json | 1200 | 0 | 34.2 [31.5, 36.9] | 10.2 | 62.6 | 54.4 | 3.43 |

## Takeaways
- The response surface is flat. At 6,000 games every cell except `push_blue_slack=1` sits at 26.4-27.7% AdaptiveBalanced (off 18.2%), and the CIs overlap. Several constants (push_min_share 5/7, push_low_gap 5/9, push_top_gap 2/4) do not change outcomes at all.
- `push_blue_slack=1` is clearly harmful: AB 14.8% (below off), Patient Zero +2.2 (FAIL), AB Secrets lost to Blue 4.59 vs 3.12. Keep 0.
- The `reach_or_threat` dump is no better than `share_only` (26.4-27.4% vs 27.7%), and wider DUMP_TOP_GAP is worse.
- Top 3 non-default cells taken forward (by AB win %, guardrails passed, chosen to change window shares): dump_max_share=4, push_secrets_band=3, push_top_gap=4. None beats the defaults outside the CI at 2P, 3P or 4P.
- ref1: with scope all, the edge rises above off (77-79% vs 69.1%), because the reference rollouts use the stronger AB. With non_reference it is about 71% for every cell. The spec's 70-75% expectation holds only under non_reference.
- The Mixed seat is within ±3 of 33.3% for all cells (32.6-32.9).
- Recommendation (a candidate only, needs User sign-off): keep the current PrPushParams defaults. No sweep cell improves on them with significance under the selection rule (ties keep the default).
