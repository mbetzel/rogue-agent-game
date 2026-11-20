# v0.50 Gray vulnerability sweeps (HEAD 547135c)

Mixed1 roster, pooled seeds 42..2441 (`--games 2400 --seed0 42`, 2,400 games per pod). Script: `scripts/run_gray_vuln_sweep.py`. Outputs: `sim_results/gray_vuln_v050/` (`M_pooled`, `A_stock`, `A_noL2`: .txt and .json). Command lines are in the handoff; B0, B0-GA and B48 are in M_pooled. A-GA0, the dominance matrix and the reference-bot validation were not run (not requested).

## Guardrails (M = v050_roster vs B0 = v049_roster)

| Guardrail | 2P | 3P | 4P | Result |
|:--|:--|:--|:--|:--|
| G1 PZ+MC vs B0 (bar +3 pp) | 66.8 vs 66.8 (+0.0) | 70.7 vs 71.8 (-1.0) | 73.8 vs 76.8 (-3.1) | PASS |
| G1 vs B0-GA (report only) | +0.9 | +0.0 | +0.1 | n/a |
| G2 Collapse (>= 8%) | 29.4 | 11.5 | 12.1 | PASS |
| G3 Green lost (2P <= 2.5) | 2.20 | 1.97 | 1.82 | PASS |
| G4 income vs v0.48 (<= x1.20) | x1.096 | x1.103 | x1.100 | PASS |
| G5 dead turns (<= 0.5%) | 0.29% | 0.26% | 0.29% | PASS |
| G6 invariants | clean | clean | clean | PASS |

## Arms (2P / 3P / 4P)

| Metric | B0 | B0-GA | M | A-stock | A-noL2 |
|:--|:--|:--|:--|:--|:--|
| PZ+MC % | 66.8 / 71.8 / 76.8 | 65.9 / 70.7 / 73.6 | 66.8 / 70.7 / 73.8 | 67.6 / 72.5 / 77.6 | 67.6 / 72.3 / 76.1 |
| Collapse % | 27.5 / 12.5 / 11.0 | 28.2 / 13.3 / 12.4 | 29.4 / 11.5 / 12.1 | 27.9 / 11.1 / 11.0 | 28.7 / 11.9 / 12.5 |
| Rounds | 8.41 / 8.34 / 8.20 | 8.42 / 8.43 / 8.38 | 8.45 / 8.38 / 8.32 | 8.32 / 8.17 / 8.02 | 8.32 / 8.24 / 8.16 |
| Singularity % | 25.6 / 26.1 / 22.7 | 26.8 / 27.7 / 26.1 | 25.9 / 27.6 / 25.7 | 24.5 / 25.7 / 21.9 | 25.8 / 25.9 / 23.3 |
| Total Wipeout % | 7.6 / 2.1 / 0.5 | 7.3 / 1.6 / 0.3 | 7.3 / 1.7 / 0.6 | 8.0 / 1.8 / 0.5 | 6.5 / 1.8 / 0.5 |
| Green lost | 1.81 / 1.63 / 1.47 | 1.84 / 1.63 / 1.52 | 2.20 / 1.97 / 1.82 | 2.18 / 1.91 / 1.76 | 2.16 / 1.91 / 1.79 |
| Income | 8.17 / 8.25 / 8.23 | 8.03 / 8.10 / 8.09 | 7.63 / 7.73 / 7.72 | 7.81 / 7.89 / 7.91 | 7.62 / 7.70 / 7.70 |
| Gray removed / seat | 1.72 / 1.72 / 1.70 | 2.30 / 2.33 / 2.34 | 2.77 / 2.79 / 2.75 | 2.20 / 2.18 / 2.15 | 2.46 / 2.48 / 2.44 |
| Gray <=3 round | 4.18 / 4.16 / 4.17 | 4.37 / 4.34 / 4.32 | 3.35 / 3.33 / 3.32 | 4.51 / 4.48 / 4.49 | 4.20 / 4.14 / 4.17 |

B48 (v0.48): PZ+MC 68.2 / 71.9 / 75.9, Collapse 36.7 / 17.2 / 15.5, income 6.97 / 7.01 / 7.01. All A arms: G1-G6 PASS.

## Mitigation telemetry (M)

| | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Gray held per seat, rounds 1..8 | 4.98 4.15 3.28 2.99 2.53 2.28 2.12 2.07 | 4.97 4.14 3.27 2.96 2.50 2.26 2.09 2.04 | 4.97 4.13 3.27 2.98 2.53 2.28 2.11 2.05 |
| Removed: Burn Notice / Pen Test L2 / Pen Test L3 / Release L3 / Triage L4 | 0.18 / 0.94 / 0.17 / 1.00 / 0.48 | 0.19 / 0.95 / 0.16 / 1.00 / 0.49 | 0.18 / 0.94 / 0.16 / 0.99 / 0.48 |
| Round first <=3 Gray (mean) | 3.35 | 3.33 | 3.32 |
| Never reach <=3 (%) | 4.3 | 4.3 | 5.4 |
| Seat win %: early vs late <=3 thinners | 50.7 vs 53.4 | 33.7 vs 37.0 | 25.4 vs 23.7 |
| n early / late | 4331 / 262 | 6551 / 338 | 8587 / 490 |
| Gray kept per Gray rolled / per seat-round | 0.32 / 0.64 | 0.32 / 0.64 | 0.32 / 0.64 |
| Hot rounds per seat | 4.9 | 5.0 | 5.1 |

Early vs late: the gap is within about +-3 pp, and the late group is small (n of about 260 to 490), so there is no meaningful early-thinning advantage.

## Win-rate watch rows (M)

| | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Helix win (par 50 / 33 / 25) | 42.6 | 26.5 | 20.2 (B0 19.1) |
| Spook win | 56.1 | 41.6 | 31.0 (B0 32.9) |
| Prodigy / Operator | 47.5 / 48.9 | 30.7 / 30.5 | 23.5 / 23.6 |
| Company spread (pp) | 21.6 | 19.2 | 12.7 |
| White Hat spread (pp) | 8.6 | 11.1 | 9.0 |

## Anomalies

- 4P G1 is -3.1 pp against B0. This is under the bar, but it is mostly the GA bot effect: B0-GA is already 73.6. The M-vs-B0-GA gap is +0.1.
- Helix stays below par at every player count (4P 20.2 against par 25). Spook stays above par (4P 31.0 against 25). The 2P company spread of 21.6 pp is the widest.
- Income is x1.10 vs v0.48. M's own income is about 7% below B0.
