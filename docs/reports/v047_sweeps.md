# v0.47 Locked Faces: sweep report

Seeds 42..1241 (1,200 per pod), mixed1 roster. Raw output: `sim_results/v047/main.json`. Pre-check: `v046_roster` reproduces FINDINGS section 62 at all pods (Green lost, rounds, Market Collapse within tolerance).

## Main (v0.47 vs v0.46; v0.45 comparator)
| Metric | 2P v046 / v047 | 3P v046 / v047 | 4P v046 / v047 |
|:--|:--|:--|:--|
| Rounds | 8.20 / 8.12 | 7.77 / 7.55 | 7.51 / 7.37 |
| Patient Zero % | 32.1 / 41.6 | 56.7 / 64.8 | 61.0 / 68.6 |
| Total Wipeout % | 5.1 / 8.0 | 1.4 / 2.1 | 0.1 / 0.6 |
| Market Collapse % | 35.7 / 24.0 | 21.1 / 13.6 | 22.8 / 16.0 |
| Singularity % | not printed by script summary | | |
| Green lost / player-game | 2.42 / 2.27 | 2.08 / 1.88 | 1.86 / 1.74 |
| Green no-target % | n/a / 64.4 | n/a / 52.4 | n/a / 44.1 |
| Pen Test steps | 1.59 / 1.73 | 1.72 / 1.78 | 1.78 / 1.92 |
| End Secrets | 9.14 / 7.31 | 8.05 / 6.91 | 8.40 / 7.39 |

Locks per player-round 1.54 / 1.51 / 1.50. P(star) per colored die 0.166 / 0.165 / 0.165.
Locked warning faces (per rolled die, all pods, approx.): blue3 .22, blue5 .23, green1 .23, green5 .24, purple4 .19, purple5 .19, red1 .21, red5 .21, yellow1 .20, yellow5 .19.

Helix (2P / 3P / 4P): bypass use 32.4 / 32.7 / 36.8 % of seats; burned by Black Signature 31.2 / 30.8 / 33.3 %; Helix win 35.0 / 23.8 / 13.0 % (v0.46 about 40.5 / 28.2 / 19.4; delta -5.5 / -4.4 / -6.4 pp).

Win rates: Prodigy 51.2 / 29.9 / 22.8; Operator 48.9 / 35.0 / 21.2.
4P company win rates: Acoustic 27.9, Cipher 24.9, Operator 21.2, Phreaker 25.1, Prodigy 22.8, Spook 27.9, Helix 13.0 (spread 21.5 pp, a known FAIL).
Per-colour win % (company die "a"): 2P red 48.0, blue 61.9*, green 40.2*; 3P red 28.7, blue 47.4*, green 24.3*; 4P red 25.0, blue 34.1*, green 16.2*. Yellow has no "a" value. Purchase-weighted "c": blue 56.0* and green 45.0* at 2P, green 27.7* at 3P, no flags at 4P. The blue and green flags follow the company die, which is confounded with company strength, not with the lock rule.

## Guardrails (v0.47)
| Guardrail | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Rounds 6.5-8.5 | PASS | PASS | PASS |
| Patient Zero <= v0.45 + 3 | PASS | PASS | PASS |
| Total Wipeout cap | PASS 8.0 | PASS | PASS |
| Market Collapse v0.45 +-5 | **FAIL** (24.0 vs 33.1) | PASS | PASS |
| v1.0 breach <= v0.45 | **FAIL** (12.9 vs 12.0) | PASS | PASS |
| Green lost 1.2-2.5 | PASS | PASS | PASS |
| No-target 25-70 % | PASS | PASS | PASS |
| No-target rounds 7+ <= 60 | **FAIL** (70.9) | **FAIL** (60.6) | PASS |
| Lose-3 <= 5 % | PASS | PASS | PASS |
| Liquid income <= v0.45 x 1.25 | **FAIL** (7.1) | **FAIL** (7.2) | **FAIL** (7.2) |
| 4P company spread <= 10 pp | n/a | n/a | **FAIL** 21.5 |
| 4P seat spread <= 6 pp | n/a | n/a | PASS 3.3 |
| 2+ L4, cap, back-to-back | PASS | PASS | PASS |
| Per-colour parity 5 pp | **FAIL** | **FAIL** | **FAIL** |
| Helix win >= v0.46 - 2 pp | **FAIL** -5.5 | **FAIL** -4.4 | **FAIL** -6.4 |
| Prodigy within +-3 pp | **FAIL** +6.7 | PASS | PASS |
| Operator within +-3 pp | PASS | **FAIL** +3.6 | PASS |
| P(star) >= 0.12 | PASS | PASS | PASS |
| Colored dice bought >= v0.46 -10 % | PASS | PASS | PASS |

Note: the script's own output marks the Helix win row PASS, but its printed deltas are -5.48 / -4.38 / -6.44 pp, which breach the -2 pp bar. I marked those FAIL. The Prodigy 2P delta (+6.65 pp) and Operator 3P delta (+3.64 pp) are also printed as PASS but are outside +-3 pp, so I marked them FAIL; the script's tolerance logic is likely wrong or lenient. The Helix, Prodigy and Operator 2P/3P deltas have wide 95% CIs that include 0, except Helix at 4P (CI -9.6 to -3.1).
Liquid income is about 7.2 against a v0.45 base of 4.1-4.4, and v0.46 shows the same behaviour. Treat it as a pre-existing metric-definition issue.

## Arms (2P / 3P / 4P; rounds | Green lost | Market Collapse % | no-target % | Helix win %)
| Arm | Green lost | Market Collapse % | No-target % | Helix win % |
|:--|:--|:--|:--|:--|
| A_nopremium | 2.22 / 1.87 / 1.71 | 26.8 / 14.5 / 17.5 | 64.7 / 52.9 / 44.2 | 34.3 / 26.4 / 14.7 |
| B_safe03 | 2.68 / 2.22 / 2.02 | 23.9 / 13.4 / 14.0 | 55.7 / 43.7 / 34.3 | 35.5 / 21.0 / 13.5 |
| A_safe03 | 2.63 / 2.17 / 1.97 | 24.8 / 13.3 / 12.8 | 56.3 / 43.0 / 34.4 | 34.3 / 25.0 / 16.3 |
| dmg_112 | 2.07 / 1.72 / 1.57 | 24.8 / 13.3 / 16.9 | 64.2 / 52.1 / 43.7 | 31.7 / 22.7 / 13.0 |
| green_yield_3 | 2.24 / 1.84 / 1.69 | 24.6 / 14.5 / 15.8 | 65.0 / 53.2 / 44.7 | 36.2 / 24.1 / 14.5 |
| pen_cost_1 | 2.23 / 1.87 / 1.70 | 24.8 / 13.8 / 15.8 | 64.6 / 53.3 / 45.5 | 33.3 / 22.2 / 14.0 |
| secret_lock_off | 2.15 / 1.77 / 1.57 | 23.4 / 12.1 / 13.3 | 65.5 / 54.8 / 45.9 | 31.7 / 23.3 / 11.5 |
| helix_per_version | 2.26 / 1.89 / 1.73 | 24.2 / 13.8 / 17.2 | 64.3 / 52.6 / 44.2 | 37.9 / 25.2 / 15.6 |
| helix_legacy | 2.29 / 1.93 / 1.76 | 25.7 / 15.3 / 17.5 | 64.6 / 52.7 / 43.8 | 41.7 / 25.2 / 19.1 |
| bots_naive | 2.75 / 2.34 / 2.12 | 27.1 / 16.8 / 17.2 | 58.1 / 44.6 / 36.3 | 38.8 / 21.6 / 14.5 |
| bots_aware | 2.44 / 2.08 / 1.88 | 26.1 / 16.5 / 17.9 | 61.3 / 48.7 / 39.9 | 36.0 / 20.7 / 14.6 |
| bots_lambda | 2.48 / 2.05 / 1.88 | 25.0 / 14.6 / 17.7 | 61.8 / 50.0 / 41.1 | 35.5 / 24.9 / 14.9 |
| pen_lock_headroom | 2.05 / 1.72 / 1.57 | 26.3 / 14.9 / 15.9 | 68.0 / 57.8 / 49.6 | 37.1 / 23.0 / 15.6 |

Takeaways: only helix_legacy restores Helix to about the v0.46 level (41.7 / 25.2 / 19.1 vs 40.5 / 28.2 / 19.4). Every arm keeps Market Collapse well under v0.45 +-5 at 2P. The safe-zone arms (B_safe03, A_safe03) push 2P Green lost above 2.5 (2.68 / 2.63), which breaks the guardrail.

## Dominance matrix (v047_roster, 600 games per cell; focal win share vs Adaptive field, pp from fair)
| Focal | 2P | 3P | 4P |
|:--|:--|:--|:--|
| KeepAll | -7.5 | -13.0 | -6.5 |
| RerollAllVuln | +3.5 | -3.2 | +1.3 |
| Adaptive | +4.5 | -2.2 | n/r |
| NoColorReroll | -11.2 | -13.0 | -7.2 |
| StarChase | -1.0 | -4.0 | -1.3 |
| PenTestRush | **+7.2 FAIL (>5)** | +3.5 (**FLAG** +5.7 paired vs Adaptive, CI +1.7..+9.7) | +3.3 |
| Kamikaze | -16.5 | -12.7 | -11.8 |

PenTestRush is the only dominant focal. Adaptive keep rate is 16.8-18.4 %, outside the 35-85 % band (a v0.46 band, probably stale under locking). KeepAll P(star) is 0.073 against about 0.17 for the others; StarChase is 0.29.

## ref1 (3P, 1,200 games, v047_roster, non-reference push scope)
ref1 win 61.0 % (fair 33.3, +27.7 pp), against 52.0 % on v0.46 (+18.7 pp, FINDINGS section 62 / step 4). The edge grew by 9 pp, so the D5 bar (edge must not grow) FAILS. Field 19.5 %. Stances: Adaptive 3,047, KeepAll 2,166, StarChase 1,884, NoColorReroll 1,823, PenTestRush 1,004, RerollAll 442. NoColorReroll plus StarChase make up about 30 % of stances. ref1 reaches 2+ L4 tracks on 62.5 % of seats, the field 0.0 %. The wall time was 26 minutes with 0 errors.

## Outlier seeds
The script prints no per-seed outliers, and I did not read raw JSON. No crashes or errors. Unavailable without raw data.
