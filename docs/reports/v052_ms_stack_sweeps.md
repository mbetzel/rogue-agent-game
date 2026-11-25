# v0.52.0 Market Share stack validation sweeps

Command: `python3 scripts/run_ms_stack_sweep.py --players 2,3,4 --games 2400 --seed0 {42,10042}` (mixed1 roster).
B = v051_roster + tie telemetry, M = v052_roster (FIRST_SEAT_TOP default). Pooled = 2 x 2,400 games per arm per player count (mean of the two blocks).
Ablations: 1,200 games, 3P/4P, seed0 42, M arm only overridden (B is the same-seed baseline).
Not emitted by the sweep script (not reported here): per-company win rates (only the spread), White Hat spread, elimination % (PZ % is the elimination-ending share; Total Wipeouts are not split out). Sweep JSON in sim_results/ms_stack_v052/ is overwritten per same-name run (the ablation 1200g_s42 file holds only the last run); the printed tables are the source.

## Pooled results (B -> M, delta)

| Metric | 2P B | 2P M | d | 3P B | 3P M | d | 4P B | 4P M | d |
|---|---|---|---|---|---|---|---|---|---|
| Rounds | 8.16 | 8.18 | +0.03 | 8.21 | 8.16 | -0.05 | 8.08 | 8.08 | 0.00 |
| PZ % | 43.2 | 42.8 | -0.4 | 62.3 | 64.7 | +2.4 | 68.6 | 67.8 | -0.9 |
| MC % | 28.1 | 30.1 | +2.0 | 11.7 | 12.5 | +0.8 | 12.2 | 12.1 | -0.1 |
| Singularity % | 20.0 | 19.3 | -0.7 | 24.1 | 21.4 | -2.7 | 18.5 | 19.7 | +1.2 |
| MLB Secrets / game | 10.48 | 10.28 | -0.20 | 17.22 | 16.14 | -1.08 | 21.75 | 23.73 | +1.98 |
| Winner Secrets | 9.29 | 9.56 | +0.27 | 11.38 | 11.87 | +0.49 | 12.50 | 13.73 | +1.23 |
| Company win spread pp | 19.6 | 15.5 | -4.2 | 14.6 | 12.0 | -2.7 | 11.2 | 9.3 | -1.9 |
| Seat win spread pp | 1.1 | 4.2 | +3.1 | 2.4 | 1.7 | -0.7 | 2.2 | 3.5 | +1.3 |
| Raw top-space tie (MLB 1st) % | 12.1 | 13.4 | +1.3 | 25.9 | 20.7 | -5.3 | 32.5 | 25.5 | -7.0 |
| Effective MLB 1st tie % | 12.1 | 0.00 | -12.1 | 25.9 | 0.00 | -25.9 | 32.5 | 0.00 | -32.5 |
| Top-space same, % rounds | 17.9 | 18.9 | +1.0 | 30.1 | 24.7 | -5.4 | 35.5 | 28.5 | -7.0 |
| Lead changes / game | 1.07 | 1.80 | +0.73 | 1.39 | 2.57 | +1.18 | 1.45 | 2.96 | +1.51 |
| End MS spread | 2.04 | 2.02 | -0.02 | 3.19 | 3.49 | +0.30 | 4.36 | 4.73 | +0.37 |
| Poach stack-decided / game | 0.00 | 0.00 | 0 | 0.12 | 0.13 | +0.01 | 0.19 | 0.22 | +0.03 |
| Sig-red stack-decided / game | 0.06 | 0.06 | 0 | 0.27 | 0.29 | +0.02 | 0.49 | 0.55 | +0.06 |
| Tiebreak decided by stack, % games | 0 | 1.5 | +1.5 | 0 | 1.1 | +1.1 | 0 | 1.6 | +1.6 |

Per-block checks: unique winner 100% and tied-paid MLB places 0 in every M run (both blocks and ablations). Per-block seat spreads (M): 2P 4.9/3.4, 3P 2.3/1.2, 4P 3.4/3.5.
Seat win rates, pooled-block A (M): 2P 52.5/47.5; 3P 32.8/34.7/32.5; 4P 26.9/25.8/23.5/23.9. Block B: 2P 51.7/48.3; 3P 33.0/34.1/32.9; 4P 24.9/26.7/23.2/25.2.
Pre-sweep reference match: 4P M PZ 68.5/MC 11.6/Sing 19.4 vs 67.8/12.1/19.7; 3P M PZ 65.9/MC 11.7/Sing 21.0 vs 64.7/12.5/21.4. Consistent.

## Acceptance lines

| Line | 2P | 3P | 4P |
|---|---|---|---|
| Effective ties = 0 | PASS | PASS | PASS |
| Unique winner 100% | PASS | PASS | PASS |
| PZ within +-5pp | PASS (-0.4) | PASS (+2.4) | PASS (-0.9) |
| MC within +-5pp | PASS (+2.0) | PASS (+0.8) | PASS (-0.1) |
| Singularity within +-5pp | PASS (-0.7) | PASS (-2.7) | PASS (+1.2) |
| Rounds within +-0.3 | PASS | PASS | PASS |
| Seat spread <= 5pp | WATCH (4.2 pooled; block A 4.9; seat 0 about 52%) | PASS (1.7) | PASS (3.5) |
| Company spread not worse by > 5pp | PASS (better) | PASS (better) | PASS (better) |

## Ablations (1,200 games, seed0 42; B same seeds)

| Arm | P | Rounds | PZ | MC | Sing | MLB/game | Seat spread | Co spread | Seat wins |
|---|---|---|---|---|---|---|---|---|---|
| B | 3 | 8.14 | 62.8 | 10.3 | 24.8 | 17.00 | 4.7 | 17.4 | - |
| LAST_SEAT_TOP | 3 | 8.08 | 66.9 | 11.9 | 20.2 | 15.75 | 8.1 | 17.3 | 30.2/31.4/38.3 |
| bot_ms_stack_aware=false | 3 | 7.94 | 68.3 | 9.6 | 20.4 | 13.68 | 4.5 | 14.4 | 30.4/34.7/34.9 |
| B | 4 | 8.17 | 68.2 | 11.7 | 19.3 | 21.92 | 2.9 | 9.8 | - |
| LAST_SEAT_TOP | 4 | 8.21 | 65.4 | 12.3 | 22.2 | 24.46 | 4.5 | 13.6 | 24.2/22.7/25.9/27.2 |
| bot_ms_stack_aware=false | 4 | 7.97 | 71.1 | 10.7 | 17.8 | 20.49 | 4.7 | 15.1 | 26.9/24.2/22.2/26.6 |

Reading: LAST_SEAT_TOP in 3P hands the last seat +5pp (38.3%), failing the seat spread line, so FIRST_SEAT_TOP is the better default. Disabling stack-aware bots in 3P pushes PZ +5.5pp over B (just outside +-5), lowers rounds by 0.2 and MLB Secrets by 3.3 per game, and in 4P widens company spread by +5.3pp (WATCH/FAIL on that arm). Awareness is therefore load-bearing for keeping the M results close to B. Ablation n is 1,200 (seed noise of a few pp).

## Surprises
- Lead changes per game roughly double (1.1-1.5 to 1.8-3.0): the intended anti-stagnation effect, larger than expected.
- 2P MC +2.0pp (WATCH-level but within band) and 2P seat 0 edge about 52%.
- 4P MLB Secrets +2.0 per game and winner Secrets +1.2, while 3P MLB is -1.1 per game.
- Raw top-space ties fall 5-7pp in 3P/4P (stack order alters play), and effective ties all become 0.
