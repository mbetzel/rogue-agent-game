# v0.47.0 Sweep Report (Phase 68, Sprint Plan & Gray Legacy Rotation)

Run: `scripts/run_v047_sweep.py`, 1,200 games per pod, 2P/3P/4P, seeds 42..1241, `mixed1` roster, all arms re-run on current code. S2 was run with `--assert-invariants` (all three pods; no assertion errors) and `--ref45` (V45 income reference). Tables only; no balance judgement.

Arms: S0 = v046 control; S1 = v047, LEGACY bots; S2 = v047_roster, THINNING_AWARE bots (candidate); S2b = S2 plus bots push Pen Test to L3; S3 = bot fix on v046; R0 = rush stress vs S1; R1-R3 = rush stress vs S2.

## 1. Main table (per pod)
dR = delta mean rounds vs S0 (bar +-0.30). Sing = Singularity %. PZ+Col = Patient Zero + Collapse % (4P bar <=95.5). Green = Secrets lost per seat (bar 1.2-2.5). Liquid = Phase 3 liquid income per seat-round. Gray% = Gray roll share (bar >=45). Streak = longest Gray stranding run (bar <=8). Seat0 = seat-0 win %.

| Arm | P | Rounds | dR | Sing% | PZ% | Col% | Wipe% | Green | Dead% | Liquid | Inc ratio (S2 x v0.45; others x S0) | Gray% | Streak | WH spread pp | Seat0% | Rush edge pp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 | 2P | 8.2 | None | 27.17 | 32.08 | 35.67 | 5.08 | 2.42 | 2.41 | 5.98 | None | n/a | 0 | 10.11 | 53.08 | None |
| S0 | 3P | 7.77 | None | 20.83 | 56.67 | 21.08 | 1.42 | 2.08 | 2.29 | 6.02 | None | n/a | 0 | 9.05 | 30.42 | None |
| S0 | 4P | 7.51 | None | 16.08 | 61.0 | 22.83 | 0.08 | 1.86 | 2.29 | 6.02 | None | n/a | 0 | 8.07 | 26.5 | None |
| S1 | 2P | 8.06 | -0.14 | 19.33 | 35.83 | 37.83 | 7.0 | 1.97 | 0.66 | 6.53 | 1.09 | 49.14 | 10 | 11.39 | 51.08 | None |
| S1 | 3P | 7.91 | 0.14 | 17.42 | 57.92 | 21.92 | 2.75 | 1.73 | 0.58 | 6.54 | 1.09 | 48.64 | 10 | 9.56 | 33.0 | None |
| S1 | 4P | 7.6 | 0.1 | 12.33 | 64.0 | 23.33 | 0.33 | 1.55 | 0.63 | 6.53 | 1.08 | 48.3 | 9 | 6.73 | 24.75 | None |
| S2 | 2P | 8.26 | 0.06 | 25.0 | 30.0 | 37.92 | 7.08 | 2.26 | 0.42 | 6.96 | 1.3 | 56.16 | 5 | 4.81 | 51.5 | None |
| S2 | 3P | 8.13 | 0.35 | 21.83 | 54.25 | 22.17 | 1.75 | 2.04 | 0.3 | 7.0 | 1.26 | 54.86 | 7 | 7.2 | 31.92 | None |
| S2 | 4P | 7.81 | 0.3 | 15.75 | 58.58 | 24.92 | 0.75 | 1.84 | 0.34 | 7.03 | 1.26 | 54.93 | 6 | 8.04 | 23.83 | None |
| S2b | 2P | 8.25 | 0.05 | 24.67 | 31.92 | 38.83 | 4.58 | 2.25 | 0.4 | 6.73 | 1.13 | 59.08 | 7 | 8.16 | 50.67 | None |
| S2b | 3P | 8.11 | 0.34 | 21.75 | 52.83 | 23.58 | 1.83 | 2.03 | 0.37 | 6.79 | 1.13 | 57.48 | 6 | 10.66 | 36.33 | None |
| S2b | 4P | 7.81 | 0.3 | 12.92 | 58.83 | 27.92 | 0.33 | 1.84 | 0.36 | 6.77 | 1.13 | 57.47 | 7 | 10.56 | 26.17 | None |
| S3 | 2P | 8.21 | 0.0 | 29.33 | 32.08 | 35.42 | 3.17 | 2.75 | 1.13 | 6.69 | 1.12 | n/a | 0 | 9.67 | 52.5 | None |
| S3 | 3P | 7.89 | 0.12 | 25.5 | 53.58 | 20.08 | 0.83 | 2.38 | 1.16 | 6.72 | 1.12 | n/a | 0 | 6.52 | 32.75 | None |
| S3 | 4P | 7.76 | 0.25 | 19.17 | 55.42 | 25.17 | 0.25 | 2.22 | 1.14 | 6.69 | 1.11 | n/a | 0 | 7.15 | 25.67 | None |
| R0 | 2P | 8.21 | 0.01 | 22.33 | 34.33 | 37.25 | 6.08 | 2.16 | 0.52 | 6.7 | 1.12 | 55.09 | 10 | 5.16 | 56.58 | +5.50 |
| R0 | 3P | 7.91 | 0.14 | 18.67 | 57.92 | 21.83 | 1.58 | 1.82 | 0.53 | 6.65 | 1.1 | 52.35 | 9 | 8.51 | 41.42 | +8.42 |
| R0 | 4P | 7.71 | 0.2 | 12.25 | 62.08 | 25.42 | 0.25 | 1.66 | 0.59 | 6.65 | 1.1 | 50.99 | 10 | 6.65 | 31.5 | +6.75 |
| R1 | 2P | 8.32 | 0.12 | 24.0 | 31.5 | 40.5 | 4.0 | 2.3 | 0.41 | 6.91 | 1.16 | 59.06 | 5 | 9.67 | 51.75 | +0.25 |
| R1 | 3P | 8.17 | 0.4 | 22.75 | 54.08 | 21.83 | 1.33 | 2.05 | 0.4 | 6.98 | 1.16 | 56.97 | 7 | 8.54 | 36.92 | +5.00 |
| R1 | 4P | 7.94 | 0.43 | 16.83 | 57.58 | 25.25 | 0.33 | 1.85 | 0.32 | 7.0 | 1.16 | 56.26 | 6 | 9.3 | 27.42 | +3.58 |
| R2 | 2P | 8.38 | 0.18 | 25.42 | 29.25 | 40.0 | 5.33 | 2.29 | 0.45 | 6.93 | 1.16 | 57.19 | 6 | 8.72 | 51.25 | -0.25 |
| R2 | 3P | 8.12 | 0.34 | 21.92 | 54.5 | 22.67 | 0.92 | 2.03 | 0.37 | 7.0 | 1.16 | 56.0 | 5 | 11.25 | 35.0 | +3.08 |
| R2 | 4P | 7.81 | 0.3 | 15.33 | 59.0 | 25.5 | 0.17 | 1.84 | 0.35 | 7.0 | 1.16 | 55.59 | 6 | 9.53 | 26.58 | +2.75 |
| R3 | 2P | 8.35 | 0.14 | 25.58 | 29.58 | 40.42 | 4.42 | 2.29 | 0.43 | 6.87 | 1.15 | 63.05 | 6 | 7.67 | 51.83 | +0.33 |
| R3 | 3P | 8.37 | 0.6 | 23.25 | 51.08 | 24.83 | 0.83 | 2.12 | 0.41 | 6.91 | 1.15 | 61.58 | 6 | 9.19 | 32.67 | +0.75 |
| R3 | 4P | 7.97 | 0.46 | 15.83 | 56.58 | 27.5 | 0.08 | 1.86 | 0.33 | 6.89 | 1.15 | 61.27 | 6 | 5.07 | 26.08 | +2.25 |

Notes: "Inc x v0.45" is only computed by the script for S2 (method b, uses V45 ref); other arms print income x S0 (liquid) which is the column above for S1/S3/S2b/R*, so they are shown as the script's ratio vs S0, not vs v0.45. Dividing liquid by the S2 reference (liquid / ratio: 2P 5.35, 3P 5.56, 4P 5.58 for v0.45) gives approximate x v0.45 for other arms: S0 ~1.12/1.08/1.08, S1 ~1.22/1.18/1.17, S2b ~1.26/1.22/1.21 (approximation, not script output). Rush edge = seat-0 win pp, R0 vs S1, R1-R3 vs S2.

(The script prints the Inc column from its own method; where the table shows a value for non-S2 arms it is the "income x S0" ratio.)

## 2. Guardrail results (script PASS/FAIL, S2 = candidate)
| Guardrail | 2P | 3P | 4P |
|---|---|---|---|
| dRounds vs v0.46 within +-0.30 | +0.06 PASS | +0.35 FAIL | +0.30 (rounded; script FAIL) |
| Singularity share of S0 (>=60) | 92.0% PASS | 104.8% PASS | 97.9% PASS |
| Income x v0.45 <=1.25 | 1.30 FAIL | 1.26 FAIL | 1.26 FAIL |
| Green Secrets lost 1.2-2.5 | 2.26 | 2.04 | 1.84 (all PASS) |
| 4P PZ + Collapse <=95.5 | n/a | n/a | 83.5 PASS |
| Gray roll share >=45 | 56.2 | 54.9 | 54.9 (PASS) |
| Longest Gray streak <=8 | 5 | 7 | 6 (PASS) |
| Seat-0 rush edge <=+4 pp | R1 +0.25 / R2 -0.25 / R3 +0.33 | R1 +5.00 / R2 +3.08 / R3 +0.75 | R1 +3.58 / R2 +2.75 / R3 +2.25 |

Other script FAILs: S1 Gray streak 10/10/9 (bar 8) in all pods; S3 2P Green lost 2.75 (bar 2.5); S2b 3P dR +0.34 (4P +0.30); R0 streak 10/9/10 (bar 8) and rush edge +5.50/+8.42/+6.75 pp (R0 vs S1, bar +4); R1 3P/4P dR +0.40/+0.43; R2 3P/4P dR +0.34/+0.30; R3 dR +0.60 (3P), +0.46 (4P). S1 Gray roll share (48-49%) passes the >=45 bar; its only FAIL is the Gray streak.

## 3. S1 vs S2 vs S2b (key differences)
| Metric | S1 (2P/3P/4P) | S2 | S2b |
|---|---|---|---|
| dRounds | -0.14 / +0.14 / +0.10 | +0.06 / +0.35 / +0.30 | +0.05 / +0.34 / +0.30 |
| Liquid | 6.53 / 6.54 / 6.53 | 6.96 / 7.00 / 7.03 | 6.73 / 6.79 / 6.77 |
| Income ratio (script) | 1.09 / 1.09 / 1.08 (x S0) | 1.30 / 1.26 / 1.26 (x v0.45) | 1.13 / 1.13 / 1.13 (x S0) |
| Singularity % | 19.3 / 17.4 / 12.3 | 25.0 / 21.8 / 15.8 | 24.7 / 21.8 / 12.9 |
| Gray roll share % | 49.1 / 48.6 / 48.3 | 56.2 / 54.9 / 54.9 | 59.1 / 57.5 / 57.5 |
| Longest Gray streak | 10 / 10 / 9 | 5 / 7 / 6 | 7 / 6 / 7 |
| First thin round (mean) | 3.37 / 3.37 / 3.39 | 2.40 / 2.37 / 2.41 | 2.40 / 2.37 / 2.40 |
| Second thin round (mean) | n/a | 4.70 / 4.63 / 4.64 | 4.47 / 4.46 / 4.49 |
| Dead turns % | 0.66 / 0.58 / 0.63 | 0.42 / 0.30 / 0.34 | 0.40 / 0.37 / 0.36 |

Note: income ratios are on different bases (S1/S2b are x S0 by script, S2 is x v0.45); compare liquid rows directly. Liquid / v0.46 S0 = 5.98 / 6.02 / 6.02.

## 4. Thinning by source (per seat, S2 / S2b / S1; 3P pod)
| Source | S1 | S2 | S2b | R1 | R3 |
|---|---|---|---|---|---|
| BURN_NOTICE | 0.131 | 0.137 | 0.135 | 0.131 | 0.144 |
| PEN_TEST_L3 | 0.194 | 0.172 | 0.872 | 0.429 | 0.948 |
| RELEASE_L3 | 0.371 | 0.983 | 0.982 | 0.986 | 0.993 |
| TRIAGE_L4 | 0.379 | 0.307 | 0.174 | 0.264 | 0.166 |

## 5. Owned Gray dice by round R1..R8 (3P; 2P/4P within 0.1)
| Arm | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|---|---|---|---|---|---|---|---|---|
| S1 | 5.0 | 4.8 | 4.3 | 4.0 | 4.0 | 3.9 | 3.9 | 3.9 |
| S2 | 5.0 | 4.3 | 4.0 | 3.7 | 3.5 | 3.4 | 3.3 | 3.3 |
| S2b | 5.0 | 4.3 | 4.0 | 3.3 | 3.0 | 2.9 | 2.8 | 2.7 |
| R0 | 5.0 | 4.6 | 4.0 | 3.7 | 3.6 | 3.6 | 3.5 | 3.5 |
| R1 | 5.0 | 4.2 | 3.9 | 3.5 | 3.3 | 3.2 | 3.1 | 3.1 |
| R3 | 5.0 | 4.1 | 3.5 | 3.1 | 3.0 | 2.8 | 2.7 | 2.7 |

## 6. Secret faces per roll by round R1..R8 (Round 2 dip)
| Arm / P | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|---|---|---|---|---|---|---|---|---|
| S0 2P | 0.61 | 0.59 | 0.67 | 0.69 | 0.76 | 0.80 | 0.86 | 0.83 |
| S0 3P | 0.60 | 0.51 | 0.56 | 0.61 | 0.68 | 0.72 | 0.77 | 0.81 |
| S0 4P | 0.58 | 0.51 | 0.57 | 0.62 | 0.67 | 0.76 | 0.80 | 0.80 |
| S1 3P | 0.60 | 0.27 | 0.55 | 0.38 | 0.62 | 0.52 | 0.65 | 0.64 |
| S2 2P | 0.63 | 0.49 | 0.62 | 0.57 | 0.71 | 0.72 | 0.78 | 0.77 |
| S2 3P | 0.60 | 0.43 | 0.55 | 0.52 | 0.63 | 0.65 | 0.74 | 0.78 |
| S2 4P | 0.59 | 0.42 | 0.55 | 0.51 | 0.62 | 0.66 | 0.73 | 0.75 |
| S2b 3P | 0.60 | 0.43 | 0.55 | 0.50 | 0.58 | 0.62 | 0.72 | 0.75 |
| S3 3P | 0.60 | 0.48 | 0.55 | 0.60 | 0.70 | 0.80 | 0.86 | 0.87 |

S1 shows a dip at R2 (0.26-0.28) and R4 in every pod; S2 R2 dip 0.42-0.49 vs S0 0.51-0.59.

## 7. v1.0 card (S2 / S0, rounds and Singularity %)
| Pod | DATA_SCRAPER S0 | DATA_SCRAPER S2 | SCRIPT_KIDDIE S0 | SCRIPT_KIDDIE S2 |
|---|---|---|---|---|
| 2P | 8.43 r, 38% | 8.52 r, 35% | 7.97 r, 16% | 7.99 r, 14% |
| 3P | 7.18 r, 18% | 7.59 r, 22% | 8.44 r, 24% | 8.73 r, 21% |
| 4P | 6.91 r, 16% | 7.28 r, 16% | 8.12 r, 16% | 8.35 r, 16% |

## 8. Win spreads
White Hat spread (max-min seat-win pp across White Hats), from the script:
S0 10.11 / 9.05 / 8.07; S1 11.39 / 9.56 / 6.73; S2 4.81 / 7.20 / 8.04; S2b 8.16 / 10.66 / 10.56; S3 9.67 / 6.52 / 7.15 (2P/3P/4P). 4P bar <=12: all PASS.

## 9. Not delivered (script/tooling gaps)
- Spook and Operator win% print as `None` in every pod: the script keys `by_wh["spook"]`/`["operator"]` but the saved White Hat codes do not match those strings. Not fixed (no code edits); needs the game-designer/engineer to confirm the code strings.
- Win spread by bot and by company: not printed by the script. I attempted to aggregate them from the saved per-game JSON but the permission layer denied access to raw sim_results JSON, so they are missing.
- Cash and Research in rounds 1-4: not printed by the script summary; missing.
- Per-pod seed outliers: the script prints no per-seed outlier log, so outlier seeds are not logged.
- Method-b income x v0.45 exists only for S2 (the arm run with `--ref45`); other arms' x v0.45 are approximations above.
