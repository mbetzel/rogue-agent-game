# RSP-1 yield +2, 2P Market Share 13 confirm (Phase 49)

v038c, roster mixed1, 2P only, 1,200 games, seeds 42..1241, `--procs 8`. Overrides: `red_secret_owner_yield=2` and `market_share_start_by_player_count={"2":13,"3":16,"4":17}` (start = max; there is no separate max knob, `market_share_start()` is the maximum per config.py). Comparator: 2P yield2 3/4/4 cell (2P start 16) from `sim_results/v380_rsp1_y2/sweep_report.md`. Config hash 5c10ad76 equals the probe's ms13 cell. ref1: wrapper `ref1/ref_run.py` injects yield 2 and the same Market Share start; `--pr-push on`, scope non_reference, seeds 200042+i. Stall diagnostic replay not rerun. Analysis script: `summ_cmp.py`.

## Endings, rounds, guardrail

| cell | Singularity | Patient Zero | Market Collapse | Total Wipeout | mean rds | rds 1-4 % | games <=4 | games >=15 | max rds | 2P Sing guardrail | stranded % | winner Secrets |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yield2 3/4/4, MS start 16 | 50.2 | 20.2 | 27.6 | 2.0 | 8.572 | 9.2 | 110 | 0 | 11 | FAIL | 3.3 | 14.136 |
| yield2 3/4/4, MS start 13 | 39.0 | 20.0 | 38.9 | 2.1 | 8.332 | 9.2 | 110 | 0 | 11 | PASS | 2.9 | 13.808 |

## Colour win rate (%) and archetype win rate (%)

| cell | Co Red | Co Blue | Co Green | path red | path blue | path green | path yellow | path mixed |
|---|---|---|---|---|---|---|---|---|
| MS 16 | 52.8 | 46.2 | 50.9 | 55.6 | 58.2 | 58.5 | 34.4 | 47.3 |
| MS 13 | 51.3 | 45.9 | 52.8 | 56.0 | 51.2 | 58.1 | 36.9 | 47.3 |

| cell | Accel | AdaptBal | Mixed | Reckless | SecOpsTurtle | VentureGreed | spread (pts) |
|---|---|---|---|---|---|---|---|
| MS 16 | 49.4 | 66.6 | 48.0 | 38.5 | 64.2 | 41.2 | 28.1 |
| MS 13 | 49.6 | 66.4 | 48.3 | 38.9 | 61.0 | 42.4 | 27.5 |

## Payout stats

| cell | payouts/game | end-payout % | >=2 Red banks rounds % | payout leader wins % | payout Secrets/seat | payout share of (payout+face) % | Red banked/seat | Red own-face Secrets/seat | Red mean wait rds | Red pending/game | mean min Market Share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MS 16 | 2.311 | 70.4 | 3.6 | 81.2 | 7.218 | 47.9 | 1.318 | 2.637 | 0.022 | 0.155 | 5.96 |
| MS 13 | 2.290 | 59.0 | 3.6 | 81.2 | 6.942 | 47.4 | 1.303 | 2.607 | 0.024 | 0.133 | 4.02 |

## ref1 (2P, 1,200 games; edge = ref win % minus 50; gate +10)

| cell | ref win % | edge (pts) | Singularity | Patient Zero | Market Collapse | Total Wipeout | mean rds | games <=4 | games >=15 |
|---|---|---|---|---|---|---|---|---|---|
| yield2, MS 16 | 91.8 | +41.8 | 35.5 | 4.3 | 60.1 | 0.1 | 8.884 | 20 | 0 |
| yield2, MS 13 | 92.9 | +42.9 | 18.8 | 3.5 | 77.6 | 0.1 | 8.412 | 25 | 0 |

## Flags

- 2P Singularity guardrail: 50.2% FAIL to 39.0% PASS (margin 4 pts under 43). Mean rounds 8.57 to 8.33; <=4-round share unchanged (9.2%).
- Market Collapse rises 27.6% to 38.9% in mixed1; Patient Zero unchanged. In ref1 Market Collapse rises 60.1% to 77.6% (Singularity 35.5% to 18.8%): the reference bot ends games through Market Share collapse far more often.
- ref1 edge +41.8 to +42.9: gate +10 still failed by a wide margin, essentially unchanged. Games <=4 rounds in ref1 20 to 25.
- Colours within a 7-pt band (Red 51.3, Blue 45.9, Green 52.8); Blue lowest, Blue path 58.2 to 51.2. Archetype spread 28.1 to 27.5 (no worse). No stalls (wait <=0.024 rds, no game >=15 rounds); end-payout share 70.4 to 59.0% (fewer games end with Red payout pending).
