# v0.51.0 Green Landing + One Hit per Round sweeps

Mixed1 roster, two pooled 1,200-seed blocks (`--games 1200 --seed0 42,1242`, 2,400 games per pod). Script: `scripts/run_green_landing_sweep.py --players 2,3,4 --assert-invariants`. Output: `sim_results/green_landing_v051/v051_roster_s42_1242.json`. M = v051_roster, B0 = v050_roster, B48 = v048_roster (income comparator). Overall result: PASS at 2P, 3P and 4P.

## Guardrails (M)

| Guardrail | 2P | 3P | 4P | Result |
|:--|:--|:--|:--|:--|
| L1 PZ+MC % (probe 70.6 / 73.5 / 80.0, +-2.0) | 70.6 | 73.6 | 79.5 | PASS |
| L2 eliminated seats % (+-2.0) | 30.0 | 26.4 | 23.1 | PASS |
| L3 rounds (+-0.15) | 8.21 | 8.16 | 8.11 | PASS |
| L4 Green Secrets lost / player-game (+-0.15) | 2.78 | 2.41 | 2.24 | PASS |
| L5 back-to-back hit % (+-3.0) | 23.7 | 20.2 | 17.9 | PASS |
| L6 multi-hit seat-rounds (== 0) | 0 | 0 | 0 | PASS |
| L7 worst per-seat round Green loss (<= 3) | 3 | 3 | 3 | PASS |
| L8 Market Collapse % (>= 8) | n/a | 11.7 | 11.5 | PASS |
| L9 Total Wipeout % (< 15) | 8.9 | n/a | n/a | PASS |
| L10 income vs B48 (<= x1.20) | x1.090 | x1.094 | x1.094 | PASS |
| L11 invariants | 0 violations | 0 violations | 0 violations | PASS |

## M vs B0 (2P)

| Metric | M | B0 | Delta |
|:--|:--|:--|:--|
| PZ+MC % | 70.6 | 66.5 | +4.1 |
| Market Collapse % | 28.3 | 29.8 | -1.5 |
| Singularity % | 20.5 | 26.8 | -6.3 |
| Total Wipeout % | 8.9 | 6.7 | +2.2 |
| Eliminated seats % | 30.0 | 25.1 | +4.9 |
| Rounds | 8.21 | 8.41 | -0.20 |
| Green lost | 2.78 | 2.19 | +0.59 |
| Back-to-back hit % | 23.7 | 4.4 | +19.3 |
| Income | 7.59 | 7.62 | -0.03 |
| Dead turns % | 0.28 | 0.31 | -0.03 |

## M vs B0 (3P)

| Metric | M | B0 | Delta |
|:--|:--|:--|:--|
| PZ+MC % | 73.6 | 70.8 | +2.8 |
| Market Collapse % | 11.7 | 12.5 | -0.8 |
| Singularity % | 24.5 | 27.5 | -3.0 |
| Total Wipeout % | 1.9 | 1.6 | +0.3 |
| Eliminated seats % | 26.4 | 24.6 | +1.8 |
| Rounds | 8.16 | 8.41 | -0.25 |
| Green lost | 2.41 | 1.96 | +0.45 |
| Back-to-back hit % | 20.2 | 3.1 | +17.1 |
| Income | 7.67 | 7.73 | -0.06 |
| Dead turns % | 0.25 | 0.30 | -0.05 |

## M vs B0 (4P)

| Metric | M | B0 | Delta |
|:--|:--|:--|:--|
| PZ+MC % | 79.5 | 75.4 | +4.1 |
| Market Collapse % | 11.5 | 13.1 | -1.6 |
| Singularity % | 19.5 | 24.0 | -4.5 |
| Total Wipeout % | 1.0 | 0.6 | +0.4 |
| Eliminated seats % | 23.1 | 20.5 | +2.6 |
| Rounds | 8.11 | 8.32 | -0.21 |
| Green lost | 2.24 | 1.84 | +0.40 |
| Back-to-back hit % | 17.9 | 2.3 | +15.6 |
| Income | 7.68 | 7.71 | -0.03 |
| Dead turns % | 0.26 | 0.28 | -0.02 |

B48 (v0.48): PZ+MC 68.2 / 71.9 / 75.8, Collapse 36.7 / 17.2 / 15.5, income 6.97 / 7.01 / 7.01 (2P / 3P / 4P).

## Landing and cap telemetry (M)

| | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Unsafe-landing % of hits | 11.9 | 11.9 | 14.6 |
| Landing bands % (1 / 2 / 3) | 88.1 / 10.9 / 1.0 | 88.1 / 10.9 / 1.0 | 85.4 / 13.0 / 1.6 |
| Cap no-target cubes / game | 0.17 | 0.11 | 0.10 |
| Corruption +3 into-target (5+) / game | 0.000 | 0.000 | 0.000 |
| Multi-hit seat-rounds | 0 | 0 | 0 |
| Worst round loss | 3 | 3 | 3 |
| Pen Test L4 % | 12.7 | 12.4 | 12.1 |

## Win-rate watch rows (M)

| | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Helix win (par 50 / 33 / 25) | 44.0 | 29.4 | 20.7 |
| Aegis win | 62.6 | 43.0 | 31.6 |
| Spook win | 55.4 | 39.9 | 31.2 |
| Company spread (pp) | 18.6 | 14.3 | 10.9 |
| White Hat spread (pp) | 9.9 | 9.4 | 8.7 |

## Residuals

- D1 (accepted): PZ+MC rises against v0.50 by +4.1 / +2.8 / +4.1 pp (2P / 3P / 4P). All inside the L1 +-2.0 probe bands.
- D2 (accepted): 2P Green lost is 2.78 against the 2.5 cap. L4 passes against the re-based probe value (2.77). 3P and 4P are under 2.5.

## Anomalies

- Singularity falls 3.0 to 6.3 pp at every player count, so the PZ+MC rise comes with a matching Singularity loss. It is in line with D1 but is the largest shift.
- Back-to-back hits rise from 2 to 4% to 18 to 24%, as the probe expected (L5 passes).
- Helix stays under par at every count (4P 20.7 against par 25). Spook and Aegis stay above par. These are carry-overs from v0.50 (Helix 42.6 / 26.5 / 20.2 there); no new outlier.
- The user-brief delta figures (+4.0 / +2.6 / +4.5) differ slightly from the measured +4.1 / +2.8 / +4.1. The measured values are from this run.
- Nothing failed. No guardrail is MISS.
