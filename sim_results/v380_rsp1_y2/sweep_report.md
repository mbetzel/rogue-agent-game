# RSP-1 owner yield +2 confirm sweep (Phase 49, FINDINGS §43.5 fix F1)

Same protocol as `sim_results/v380_rsp1/`: seeds 42..1241, 1,200 games per cell, roster mixed1, `--procs 8`. yield2 cells add `--set red_secret_owner_yield=2` on v038c (own-face Red Secret yields +2 per banked Red face instead of +1). yield1 cells are the previous sweep at identical seeds. Overrides recorded in the JSON: {"red_secret_owner_yield": 2} (3/4/4), {"red_secret_owner_yield": 2, "starting_secrets_by_player_count": {"2": 2, "3": 4, "4": 4}} (2P starting 2). Cell labels give starting Secrets at 2P/3P/4P; the "yield2 2/4/4" cell is 2P only (starting Secrets 2 at 2P, 3P/4P unchanged); its yield1 comparator is the previous 2/3/4 cell (2P starting 2 as well; 3P/4P values do not matter at 2P). No-op guard: the sweep script rejected nothing and ran without `--allow-noop`, and yield2 games differ from yield1 (see Override check).

## Endings, rounds, guardrail

| P | cell | Singularity | Patient Zero | Market Collapse | Total Wipeout | mean rds | rds 1-4 % | games <=4 | games >=15 | max rds | 2P Sing guardrail | stranded % | winner Secrets |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | yield1 2/3/4 | 38.5 | 34.4 | 24.4 | 2.7 | 7.659 | 20.1 | 241 | 0 | 11 | PASS | 3.8 | 10.915 |
| 2 | yield1 3/4/4 | 46.8 | 23.8 | 27.4 | 2.0 | 8.473 | 9.4 | 113 | 0 | 11 | WATCH | 2.8 | 12.045 |
| 2 | yield2 2/4/4 | 42.4 | 30.5 | 24.2 | 2.8 | 7.753 | 19.7 | 236 | 0 | 11 | PASS | 4.5 | 12.658 |
| 2 | yield2 3/4/4 | 50.2 | 20.2 | 27.6 | 2.0 | 8.572 | 9.2 | 110 | 0 | 11 | FAIL | 3.3 | 14.136 |
| 3 | yield1 3/4/4 | 40.1 | 37.3 | 22.2 | 0.3 | 8.156 | 13.0 | 156 | 0 | 11 | - | 2.6 | 12.553 |
| 3 | yield2 3/4/4 | 43.8 | 32.8 | 23.2 | 0.2 | 8.277 | 12.0 | 144 | 0 | 11 | - | 3.0 | 14.131 |
| 4 | yield1 3/4/4 | 42.3 | 39.5 | 18.2 | 0.0 | 8.149 | 11.9 | 143 | 0 | 12 | - | 2.5 | 13.554 |
| 4 | yield2 3/4/4 | 47.3 | 34.2 | 18.3 | 0.2 | 8.312 | 12.3 | 148 | 0 | 11 | - | 2.9 | 15.259 |

## Archetype win rate (%)

| P | cell | Accel | AdaptBal | Mixed | Reckless | SecOpsTurtle | VentureGreed | spread (pts) |
|---|---|---|---|---|---|---|---|---|
| 2 | yield1 2/3/4 | 44.2 | 63.1 | 49.8 | 37.3 | 67.1 | 38.7 | 29.8 |
| 2 | yield1 3/4/4 | 47.6 | 63.7 | 50.5 | 33.6 | 63.0 | 39.1 | 30.1 |
| 2 | yield2 2/4/4 | 48.5 | 63.9 | 48.8 | 40.6 | 66.3 | 36.5 | 29.7 |
| 2 | yield2 3/4/4 | 49.4 | 66.6 | 48.0 | 38.5 | 64.2 | 41.2 | 28.1 |
| 3 | yield1 3/4/4 | 34.9 | 46.6 | 31.8 | 15.1 | 47.4 | 26.5 | 32.4 |
| 3 | yield2 3/4/4 | 33.2 | 51.3 | 31.1 | 14.9 | 47.6 | 25.4 | 36.4 |
| 4 | yield1 3/4/4 | 20.8 | 41.2 | 24.8 | 10.2 | 38.6 | 14.6 | 31.0 |
| 4 | yield2 3/4/4 | 15.3 | 43.2 | 25.8 | 9.7 | 40.4 | 15.0 | 33.4 |

## Company colour and path win rate (%)

| P | cell | Co Red | Co Blue | Co Green | path red | path blue | path green | path yellow | path mixed |
|---|---|---|---|---|---|---|---|---|---|
| 2 | yield1 2/3/4 | 41.7 | 53.7 | 54.4 | 39.1 (432) | 64.0 (222) | 62.3 (393) | 41.0 (244) | 49.0 (1109) |
| 2 | yield1 3/4/4 | 44.6 | 52.3 | 53.0 | 44.5 (393) | 59.8 (179) | 62.1 (335) | 40.8 (294) | 49.2 (1199) |
| 2 | yield2 2/4/4 | 50.2 | 48.1 | 51.7 | 51.7 (543) | 61.1 (221) | 59.7 (315) | 33.7 (187) | 47.0 (1134) |
| 2 | yield2 3/4/4 | 52.8 | 46.2 | 50.9 | 55.6 (529) | 58.2 (182) | 58.5 (270) | 34.4 (224) | 47.3 (1195) |
| 3 | yield1 3/4/4 | 21.2 | 38.4 | 39.9 | 20.5 (361) | 43.5 (290) | 45.8 (635) | 24.7 (689) | 33.2 (1625) |
| 3 | yield2 3/4/4 | 32.5 | 33.5 | 34.0 | 32.9 (483) | 38.3 (282) | 41.7 (513) | 25.3 (637) | 33.1 (1685) |
| 4 | yield1 3/4/4 | 14.7 | 29.6 | 30.5 | 14.7 (500) | 33.8 (429) | 36.2 (869) | 19.3 (969) | 23.6 (2033) |
| 4 | yield2 3/4/4 | 25.2 | 24.1 | 25.7 | 24.3 (621) | 29.6 (398) | 29.8 (736) | 19.6 (917) | 25.0 (2128) |

## Patient Zero rate (% of seats) and own-face Secrets per seat, by Company colour

Own-face = Secrets from the seat's own Company-colour Secret face (`secrets_by_source[secret_face_<company colour>]`, mean per seat).

| P | cell | PZ Red Co | PZ Blue Co | PZ Green Co | own-face Red Co | own-face Blue Co | own-face Green Co |
|---|---|---|---|---|---|---|---|
| 2 | yield1 2/3/4 | 27.9 | 14.6 | 18.4 | 2.04 | 2.86 | 5.97 |
| 2 | yield1 3/4/4 | 20.2 | 10.0 | 12.7 | 2.29 | 3.17 | 6.49 |
| 2 | yield2 2/4/4 | 24.7 | 13.9 | 16.8 | 4.53 | 2.88 | 5.65 |
| 2 | yield2 3/4/4 | 16.9 | 9.2 | 10.9 | 5.17 | 3.19 | 6.16 |
| 3 | yield1 3/4/4 | 24.2 | 9.4 | 10.9 | 1.79 | 3.09 | 6.62 |
| 3 | yield2 3/4/4 | 18.8 | 9.8 | 9.3 | 4.18 | 2.99 | 6.29 |
| 4 | yield1 3/4/4 | 19.8 | 7.6 | 9.3 | 1.76 | 2.87 | 6.30 |
| 4 | yield2 3/4/4 | 15.1 | 7.3 | 9.1 | 4.19 | 2.83 | 5.98 |

## Payout stats

| P | cell | payouts/game | end-payout % | >=2 Red banks rounds % | payout leader wins % | payout Secrets/seat | payout share of (payout+face) % | Red banked/seat | Red face Secrets/seat | Red mean wait rds | Red pending/game |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | yield1 2/3/4 | 1.699 | 72.9 | 2.2 | 87.4 | 5.585 | 48.9 | 0.935 | 0.935 | 0.020 | 0.117 |
| 2 | yield1 3/4/4 | 1.928 | 70.6 | 2.2 | 84.9 | 6.181 | 48.6 | 1.060 | 1.060 | 0.018 | 0.112 |
| 2 | yield2 2/4/4 | 2.015 | 72.9 | 3.4 | 84.3 | 6.410 | 47.8 | 1.145 | 2.291 | 0.023 | 0.163 |
| 2 | yield2 3/4/4 | 2.311 | 70.4 | 3.6 | 81.2 | 7.218 | 47.9 | 1.318 | 2.637 | 0.022 | 0.155 |
| 3 | yield1 3/4/4 | 1.893 | 77.4 | 1.9 | 74.1 | 5.376 | 46.9 | 0.685 | 0.685 | 0.009 | 0.087 |
| 3 | yield2 3/4/4 | 2.362 | 76.6 | 3.6 | 71.6 | 6.359 | 47.9 | 0.895 | 1.789 | 0.016 | 0.128 |
| 4 | yield1 3/4/4 | 2.322 | 81.8 | 3.1 | 65.7 | 5.857 | 49.7 | 0.649 | 0.649 | 0.010 | 0.110 |
| 4 | yield2 3/4/4 | 2.875 | 81.5 | 6.0 | 64.8 | 6.921 | 50.6 | 0.860 | 1.720 | 0.014 | 0.154 |

## Override check

- 2P 3/4/4: 369/1200 games differ in (rounds, end reason)
- 3P 3/4/4: 374/1200 games differ in (rounds, end reason)
- 4P 3/4/4: 414/1200 games differ in (rounds, end reason)

## ref1 reference-bot check (v038c, preset starting Secrets, `--pr-push on`, scope non_reference, 1,200 games, seeds 42+P*100000+i)

Edge = ref1 win rate minus fair share (1/P); gate +10. yield1 rows are re-derived from `sim_results/v380_rsp1/ref1/` with the same code. Yield override injected by the scratch wrapper `ref1/ref_run.py` (the validation script has no `--set`; it monkeypatches `make_config` to add `red_secret_owner_yield=2`); the stall diagnostic replays the same seeds with `ref1/ref_diag_y2.py` (ref_diag.py with the same patch; a first diag attempt via `ref_run.py diag` did not pick up the patch, was discarded and rerun; replayed round counts match the main run 1200/1200).

| P | cell | ref win % | edge (pts) | Singularity | Patient Zero | Market Collapse | Total Wipeout | mean rds | games <=4 | games >=15 | Red waits (count) | mean wait rds | pending Red/game | payouts/game | end-payout % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | yield1 | 77.2 | +43.9 | 33.5 | 14.4 | 52.1 | 0.0 | 8.620 | 50 | 0 | 4140 | 0.027 | 0.055 | 2.984 | 47.9 |
| 3 | yield2 | 82.9 | +49.6 | 39.0 | 10.8 | 50.2 | 0.0 | 8.763 | 50 | 0 | 5823 | 0.035 | 0.093 | 3.893 | 49.8 |
| 2 | yield1 | 88.6 | +38.6 | 34.9 | 5.3 | 59.8 | 0.0 | 8.837 | 22 | 0 | 4614 | 0.046 | 0.083 | 3.300 | 40.2 |
| 2 | yield2 | 91.8 | +41.8 | 35.5 | 4.3 | 60.1 | 0.1 | 8.884 | 20 | 0 | 5810 | 0.060 | 0.124 | 3.957 | 39.8 |

## Flags

- 2P Singularity guardrail: yield2 at preset 3/4/4 = 50.2% (FAIL, >48; yield1 was 46.8% WATCH). yield2 with 2P starting Secrets 2 = 42.4% (PASS, just under 43; yield1 2/3/4 38.5%).
- Yield +2 brings Red Company win rate to parity (3P 21.2 -> 32.5 vs Blue 33.5 / Green 34.0; 4P 14.7 -> 25.2 vs 24.1 / 25.7; 2P Red 44.6 -> 52.8 at 3/4/4, 50.2 at 2/4/4), path red similarly.
- Patient Zero rate by Red Company drops at every P but stays the highest colour (3P 24.2 -> 18.8 vs ~9-10 for Blue/Green). Own-face Red Secrets/seat 1.8-2.3 -> 4.2-5.2.
- Side effects: Singularity +3.6-5 pts at 3P/4P (43.8 / 47.3), winner Secrets +1.6-1.7, Red banked/seat +25-35%, >=2 Red banks rounds roughly double (3.4-6.0%), Red pending at end 0.13-0.16/game; mean wait still <=0.023 rounds (no stall). No game reached 15 rounds. Games <=4 rounds unchanged (9-12%).
- ref1 edge rises: 3P +43.9 -> +49.6, 2P +38.6 -> +41.8 (gate +10 still failed by a wide margin); Market Collapse share 3P 52.1 -> 50.2, 2P 59.8 -> 60.1.
- Archetype spread: 2P 28-30, 3P 36.4 (was 32.4), 4P 33.4 (was 31.0).
