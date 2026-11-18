# v0.46 Vulnerability Track: Steps 1-3 sweeps

Commands (all `--procs 7`, seeds default 42..): smoke `--games 300 --assert-invariants`; main `--games 1200 --verbose`; matrix `--games 600`.
Runtime: smoke 3 s, main 17 s, matrix 40 s. Source: script stdout only (raw JSON not read).

## Step 1: smoke (300 games per pod, invariants asserted)

All invariants OK at 2P / 3P / 4P, no crashes.

| pod | rounds | PZ % | Wipeout % | Collapse % | Singularity % | Green lost / player-game | no-target % | Adaptive keep % (early / late) | Pen Test steps / player-game |
|:---|---:|---:|---:|---:|---:|---:|---:|:---|---:|
| 2P | 6.94 | 46.3 | 11.3 | 21.7 | 20.7 | 3.69 | 41.3 | 68.4 (68.6 / 67.5) | 1.11 |
| 3P | 6.53 | 72.3 | 2.7 | 9.3 | 15.7 | 3.03 | 21.0 | 68.7 (69.3 / 68.2) | 1.52 |
| 4P | 6.16 | 72.0 | 1.0 | 14.7 | 12.3 | 2.62 | 15.7 | 69.6 (69.1 / 70.8) | 1.82 |

## Step 2: main (1,200 games per pod, v0.45 vs v0.46, mixed1)

| pod | ver | rounds | PZ % | Wipeout % | Collapse % | Singularity % | Green lost / pg | Pen steps / pg |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| 2P | v0.45 | 7.42 | 49.4 | 11.7 | 33.1 | 5.8 | 1.45 | 0 |
| 2P | v0.46 | 7.15 | 47.9 | 8.3 | 22.4 | 21.4 | 3.81 | 1.16 |
| 3P | v0.45 | 6.99 | 75.5 | 3.6 | 16.6 | 4.3 | 1.15 | 0 |
| 3P | v0.46 | 6.67 | 67.5 | 2.8 | 12.8 | 16.9 | 3.13 | 1.53 |
| 4P | v0.45 | 6.73 | 79.2 | 1.6 | 16.5 | 2.8 | 0.98 | 0 |
| 4P | v0.46 | 6.24 | 73.5 | 0.4 | 15.7 | 10.4 | 2.63 | 1.80 |

Keep rate (script's Adaptive/mixed figure): 68.5 / 69.0 / 69.3 % at 2P / 3P / 4P, early about equal to late (no early-high, late-low shape).

### Guardrails (script verdicts)

| metric | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Mean rounds 6.5-8.5 | 7.15 PASS | 6.67 PASS | 6.24 FAIL |
| Patient Zero <= v0.45 + 3 | PASS | PASS | PASS |
| Total Wipeout cap | 8.25 PASS | 2.83 PASS | 0.42 PASS |
| Market Collapse v0.45 +-5 | 22.4 vs 33.1 FAIL | 12.8 vs 16.6 PASS | 15.7 vs 16.5 PASS |
| v1.0 breach <= v0.45 | 26.5 vs 12.0 FAIL | 32.1 vs 18.8 FAIL | 33.6 vs 22.0 FAIL |
| Green lost / pg 1.2-2.5 | 3.81 FAIL | 3.13 FAIL | 2.63 FAIL |
| Green no-target 25-70 % | 37.9 PASS | 25.3 PASS (edge) | 16.8 FAIL |
| No-target, rounds 7+ (flag > 60) | 51.6 PASS | 38.6 PASS | 28.2 PASS |
| Player-rounds losing 3 to Green <= 5 % | 0.40 PASS | 0.46 PASS | 0.56 PASS |
| Liquid income (a), raw | 7.68 vs 4.1 x 1.25 | 7.75 vs 4.35 | 7.74 vs 4.38 |
| 2+ L4 tracks <= 5 % | 0.0 PASS | 0.0 PASS | 0.0 PASS |
| Cap rounds <= 1 % | 0.18 PASS | 0.29 PASS | 0.30 PASS |
| Back-to-back unaffordable <= v0.45 | 0.30 vs 2.44 PASS | 0.40 vs 2.82 PASS | 0.45 vs 3.32 PASS |
| Company spread (4P) <= 10 pp | n/a | n/a | 19.07 FAIL |
| Seat spread (4P) <= 6 pp | n/a | n/a | 4.96 PASS |

Income: (a) is +87% / +78% / +77% by the script. The script FAILs it, but per your instruction I do not count that as a failure. (b), with v0.45 Block-face rolls counted as 1 unit, was not computed. The script's stdout has no per-face roll counts, and I did not mine the raw JSON. It needs either a script flag or a separate telemetry pass.

Pen Test: steps per player-game 1.1 to 1.8. L4 reach rate and per-track reach are not in stdout (2+ L4 is 0.0%).

## Step 3: dominance matrix (600 games per cell)

3P focal win % (pp vs fair 33.3), columns are the field:

| focal | Adaptive | KeepAll | RerollAllVuln |
|:---|:---|:---|:---|
| KeepAll | 28.0 (-5.3) | 34.8 (+1.5) | 42.2 (+8.8) |
| RerollAllVuln | 24.8 (-8.5) | 31.7 (-1.7) | 33.3 (0.0) |
| Adaptive | 34.0 (+0.7) | 40.7 (+7.3) | 45.6 (+12.2) |
| PenTestRush | 38.3 (+5.0) | 45.7 (+12.3) | 52.3 (+19.0) |
| Kamikaze | 17.2 (-16.2) | 22.5 (-10.8) | 21.8 (-11.5) |

Adaptive-field row at each pod (rule: fixed strategy <= fair +5; Adaptive >= fair -3):

| focal vs Adaptive field | 2P (fair 50) | 3P (fair 33.3) | 4P (fair 25) |
|:---|:---|:---|:---|
| KeepAll | -4.2 PASS | -5.3 PASS | -3.3 PASS |
| RerollAllVuln | -4.2 PASS | -8.5 PASS | -7.8 PASS |
| PenTestRush | +3.2 PASS | +5.0 FAIL (borderline, script marks FAIL) | +10.0 FAIL |
| Kamikaze | -18.5 PASS | -16.2 PASS | -12.8 PASS |
| Adaptive | -1.7 PASS | +0.7 PASS | +1.5 PASS |

Adaptive vs KeepAll / RerollAllVuln fields (3P): +7.3 / +12.2, PASS. Adaptive keep rate in its own field: 62.2 / 62.1 / 63.2 % (2P / 3P / 4P), inside 35-85 %. By round it is 45-50% in round 1, about 65% rounds 2-10, and 47-55% in the last rounds. Not strongly early-high/late-low.

**2P KeepAll watch cell:** -4.2 pp vs fair against an Adaptive field, PASS. The toy forecast was +4 pp, so KeepAll is clearly not dominant at 2P.

## Not available from stdout (gaps)

Win rate by company / colour, win rate by strategy in the main step, Secret ledger, Pen Test L4 reach by track, per-face keep rates (Gray F1-F3, Purple F4), Green loss split by strategy, and income method (b). The scripts print none of these. Say if you want a script flag added (engine code untouched) or permission to aggregate the JSON.

## Balance concerns

1. **PenTestRush dominates** at 3P (+5.0, borderline) and 4P (+10.0), and beats every field at 3P (+12 to +19 pp). Pen Test is under-priced for a dedicated rusher.
2. **Green loss 2.6 to 3.8 Secrets per player-game** is above the 1.2-2.5 band at every pod, about 2.5-3x v0.45 Overflow. v1.0 breach also rises by 14 to 20 pp. The Adaptive keep rate (about 62-69%) shows no early/late shape, and I cannot split the Green loss by strategy from stdout. Do not conclude Adaptive loses less than KeepAll without that split. Retune is the game-designer's call.
3. **Singularity endings jump** from 3-6% to 10-21%. Market Collapse falls at 2P (33% to 22%, FAIL), and 4P mean rounds is 6.24 (below 6.5). 4P company spread is 19 pp against the 10 pp bound.

---

# Full tables (rerun with `--tables full`, same seeds)

Commands: `run_v046_sweep.py --step main --games 1200 --procs 7` (19 s) and `run_v046_dominance_matrix.py --games 600 --procs 7` (41 s). Headline numbers (guardrails, matrix win rates) are identical to the first run (same seeds). Stdout only.

## T1 Income per player-round (guardrail is (b))

| pod | $ v0.45 / v0.46 | RP v0.45 / v0.46 | (a) liquid v0.45 / v0.46 (ratio) | Block rolls v0.45 | (b) v0.45 / v0.46 (ratio) |
|:---|:---|:---|:---|---:|:---|
| 2P | 2.64 / 4.46 | 1.52 / 3.23 | 4.17 / 7.69 (1.84) | 1.16 | 5.33 / 7.69 (**1.44**) |
| 3P | 2.72 / 4.44 | 1.71 / 3.31 | 4.42 / 7.75 (1.75) | 1.14 | 5.56 / 7.75 (**1.39**) |
| 4P | 2.75 / 4.39 | 1.70 / 3.36 | 4.45 / 7.75 (1.74) | 1.14 | 5.60 / 7.75 (**1.39**) |

Method (b): Block-face rolls counted as 1 unit each (script's own adjusted row). v0.45 Block share of final faces: Gray about 52%, Purple about 57%. Guardrail is <= +25%, so (b) **FAILS at +39 to +44%** at every pod. It is a smaller miss than (a). Money is up 59-69% and research 94-112%.

## T3 Win rate and Green loss by strategy

Main sweep (Adaptive vs Mixed seat): win % vs fair: 2P Adaptive 49.2 / Mixed 50.7; 3P 34.5 / 30.9; 4P 25.4 / 23.7. Green loss per player-game: 2P 3.67 / 3.96; 3P 3.03 / 3.32; 4P 2.59 / 2.74.

Matrix, focal seat vs Adaptive field, win % (Green loss per player-game):

| focal | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Adaptive | 48.3 (4.91) | 34.0 (4.17) | 26.5 (3.70) |
| KeepAll | 45.8 (4.41) | 28.0 (3.89) | 21.7 (3.48) |
| RerollAllVuln | 45.8 (2.76) | 24.8 (2.23) | 17.2 (1.82) |
| PenTestRush | 53.2 (3.86) | 38.3 (3.07) | 35.0 (2.48) |
| Kamikaze | 31.5 (6.09) | 17.2 (5.71) | 12.2 (5.18) |

**Does Adaptive lose as much Green as KeepAll? Yes, more.** Adaptive 4.91 / 4.17 / 3.70 vs KeepAll 4.41 / 3.89 / 3.48 (2P / 3P / 4P), 7-11% more, and 2P to 4P Adaptive is the second-highest loser after Kamikaze. In the main sweep Adaptive also loses about as much as the Mixed seat. Adaptive's win rate edge comes from Adaptive's play elsewhere, not from avoiding Green. Only RerollAllVuln (-45%) and PenTestRush (-26% to -33%) lose clearly less. The Adaptive keep rate of about 62% (about 68% in the main sweep) is not low enough to protect it. Not retuned.

## T6 Keep rate per ⚠ face (every seat, 3P shown; 2P and 4P within about 5 pp except Red and Yellow, noted)

| face | events/pg | keep % (3P) | 2P / 4P |
|:---|---:|---:|:---|
| Gray F1 +$2 & +1 RP | 3.22 | 98.6 | 99.0 / 97.9 |
| Gray F2 +2 RP | 2.51 | 46.6 | 45.9 / 47.5 |
| Gray F3 +$2 / +2 RP | 2.63 | 57.2 | 57.7 / 57.3 |
| Purple F4 +$1 & +2 RP | 1.87 | 74.0 | 73.0 / 73.0 |
| Purple F5 Secret | 1.86 | 76.7 | 76.0 / 76.4 |
| Blue F3 +$2 & +1 RP | 1.03 | 35.8 | 40.5 / 33.1 |
| Blue F5 Secret | 1.32 | 97.6 | 97.7 / 98.5 |
| Green F1 +3 RP | 0.87 | 54.3 | 52.9 / 53.7 |
| Green F5 Secret | 1.07 | 98.9 | 98.7 / 99.2 |
| Red F1 +1 MS & +1 RP | 1.46 | 56.8 | 40.9 / 62.4 |
| Red F5 Secret | 1.78 | 94.3 | 98.3 / 89.0 |
| Yellow F1 +2 MS | 2.48 | 59.6 | 45.8 / 64.5 |
| Yellow F5 +$2 & +1 RP | 2.27 | 43.1 | 46.0 / 41.1 |

Plan band for Gray F1-F3 and Purple F4 is 30-80%. **Gray F1 (about 98%) is far outside**: the bots almost never reroll it, so Gray F1 is effectively a free +$2 & +1 RP with no ⚠ cost (it also has the most events, about 3.2 per player-game). Gray F2, F3, Purple F4 are in band. Secret faces are kept 89-99% (Purple F5 about 76%). So ⚠ avoidance happens only on Gray F2/F3, Blue F3, Yellow F5 and Green F1.

## T5 Pen Test reach (3P/4P, PenTestRush vs Adaptive field)

| focal | Pen Test L1 / L2 / L3 / L4 | Triage L4 | Release L4 | PR L4 |
|:---|:---|---:|---:|---:|
| PenTestRush 3P | 95.0 / 89.3 / 78.7 / **70.5** | 0 | 0 | 0 |
| PenTestRush 4P | 95.8 / 89.2 / 77.7 / **66.0** | 0 | 0 | 0 |
| Adaptive 3P | 83.5 / 70.5 / 0 / 0 | 86.7 | 0 | 0 |
| Adaptive 4P | 83.7 / 66.2 / 0 / 0 | 85.8 | 0 | 0 |

PenTestRush reaches Pen Test L4 in about 70% (3P) and 66% (4P) of seats and wins +5.0 / +10.0 pp over fair with no other track past L2 (Triage and Release stop at L2, PR at L1). That is it taking Pen Test L4 (the free -1 Vulnerability per round) and nothing else, and it also takes the lowest Green loss after RerollAllVuln (3.07 / 2.48 vs Adaptive 4.17 / 3.70). Other strategies cap Pen Test at L2 and push Triage to L4 (86-91%). In the main (mixed1) sweep Pen Test L4 reach is 14% vs 5-6% in v0.45, below Triage (34%) and Release (27%), so the plan's "Pen Test L4 <= PR/Triage L4" holds there. 2+ L4 tracks is 0.0% everywhere.

## T8 What fills v3.0 faster?

| pod | Singularity v0.45 / v0.46 | Black exited per round in v3.0 | track advance per round in v3.0 | v3.0 entry round | non-Singularity rounds |
|:---|:---|:---|:---|:---|:---|
| 2P | 5.8 / 21.4 % | 1.47 / 1.54 | 0.69 / 0.94 | 8.34 / 8.34 | 7.21 / 6.12 |
| 3P | 4.3 / 16.9 % | 1.43 / 1.59 | 0.69 / 0.93 | 8.32 / 8.46 | 6.82 / 5.81 |
| 4P | 2.8 / 10.4 % | 1.46 / 1.53 | 0.59 / 0.89 | 8.31 / 8.31 | 6.62 / 5.69 |

Black cubes staged per round are the same in both versions at every stage (1.24-1.62), and v0.46 exits only 0.07-0.16 more Black per round in v3.0. But the track advances +0.24 to +0.30 per round in v3.0 (0.69 to 0.93), so **the cause is the v3.0 fill conversion (the v3.0 minimum target / Blue x1 change), not more Black supply**. v1.0 and v2.0 advance rates are unchanged. Games reaching v3.0 fall (45% to 42% at 3P), but a 3P game that reaches v3.0 now ends by Singularity about 40% of the time vs about 10% in v0.45. Non-Singularity games also end about 1 round sooner, which comes from the Green loss pushing Patient Zero earlier.

## T2 / 4P company spread

| 4P | v0.45 | v0.46 |
|:---|:---|:---|
| company spread | 16.9 pp | **19.1 pp** (HELIX 15.7 ... DTO 34.7) |
| colour spread | 9.8 pp | 11.2 pp (blue 32.2, green 21.1, red 21.9) |

Company win (v0.46): AEGIS 29.8, DTO 34.7, HELIX 15.7, MERIDIAN 20.8, OMNIDYNE 26.5, PROMETHEUS 23.0. Colour drives about 11 pp of it: Blue companies gained +7.0 pp and Green companies lost -8.6 pp vs v0.45 (Red +2.0). The Secret ledger fits: Blue face Secrets +0.58 per player-game (Blue Secret ⚠ is kept 98%), Green face Secrets -0.11, Purple -0.15. The remaining spread is within-colour company differences (DTO +10.4, HELIX -9.7 vs v0.45), which the telemetry does not decompose further (the company-to-colour mapping is not printed). The same pattern appears at 2P and 3P (green companies down 10 to 13 pp, blue up 7 to 9 pp). Green colour start also meets Green-loss pressure, but the stdout does not split Green loss by company, so the cause for Green is an inference.

## T4, T7 summary

Secret ledger (net per player-game, v0.45 to v0.46): 2P 6.31 to 7.42, 3P 6.29 to 6.89, 4P 6.61 to 7.31. Start +1.00, Blue +0.57, Breakthrough +0.15-0.20, Green loss -1.65 to -2.36 (the main drain), Blue loss +0.33-0.64 (smaller than before). Green resolution (3P): v1.0 no-target 6.0%, v2.0 25.2%, v3.0 40.0%, avg damage 1.36, hit per cube 1.31; at 4P no-target is only 2.9% in v1.0 and 16.8% overall.

## Updated pass/fail (income as (b))

| item | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Rounds 6.5-8.5 | PASS | PASS | FAIL (6.24) |
| PZ, Wipeout caps | PASS | PASS | PASS |
| Market Collapse +-5 | FAIL | PASS | PASS |
| v1.0 breach <= v0.45 | FAIL | FAIL | FAIL |
| Green loss 1.2-2.5 | FAIL (3.81) | FAIL (3.13) | FAIL (2.63) |
| Green no-target 25-70 | PASS | PASS (25.3) | FAIL (16.8) |
| 3-loss rounds, cap rounds, 2+ L4, unaffordable | PASS | PASS | PASS |
| Liquid income (b) <= +25% | FAIL (+44%) | FAIL (+39%) | FAIL (+39%) |
| Company spread <= 10 | n/a | n/a | FAIL (19.1) |
| Seat spread <= 6 | n/a | n/a | PASS (4.96) |
| Dominance: KeepAll, RerollAllVuln, Kamikaze | PASS | PASS | PASS |
| Dominance: PenTestRush | PASS (+3.2) | FAIL (+5.0) | FAIL (+10.0) |
| Adaptive >= fair -3 | PASS | PASS | PASS |
| Adaptive keep 35-85 | PASS (62) | PASS (62) | PASS (63) |
| Gray F1-F3 / Purple F4 keep 30-80 | Gray F1 FAIL (99%), others PASS | same | same |

## Top concerns

1. PenTestRush dominance (3P/4P) from Pen Test L4 reach of 66-70%, and Pen Test is far cheaper to reach under v0.46 for rushers than other tracks.
2. Green loss is 2.6-3.8 per player-game and Adaptive suffers as much as KeepAll. Adaptive's ⚠ policy does not protect it, and a ⚠ policy that does not protect is a retune question for the game-designer (λ).
3. Income (b) +39-44% vs v0.45 with Gray F1 kept 98% (a ⚠ that costs nothing), plus a v3.0 Singularity conversion that ends 4-5x more games by Singularity, shortening 4P to 6.24 rounds.

---

# Package + 0-3 safe zone (2026-11-18)

Defaults under test: calibrated bots (B-1, B-2), Pen Test cost 2, bands 4/7/10 with min target 4 (Vulnerability 0-3 safe), Gray F1 `+$1 & +1 RP` ⚠, Data Scraper +1 Secret (not +$1), per-round Green telemetry fix. Same seeds as before. Main: `--step main --games 1200 --procs 7` (20 s). Matrix: `--games 600 --procs 7` (50 s), PenTestRush/KeepAll rerun at 2,400 per cell (2m55). Reference "min-3" = the package with min target 3 (figures from the coordinator, not re-run).

## Guardrails (v0.46 now | min-3 | v0.45), 2P / 3P / 4P

| metric | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Mean rounds | 8.19 / 7.94 / 7.42 | 7.79 / 7.50 / 6.99 | 7.50 / 7.31 / 6.73 |
| v1.0 breach % | 10.4 / 13.2 / 12.0 | 15.2 / 17.6 / 18.8 | 16.9 / 19.0 / 22.0 |
| Green lost per player-game | 2.44 / 3.14 / 1.45 | 2.05 / 2.60 / 1.15 | 1.82 / 2.29 / 0.98 |
| Green lost per player-round | 0.32 / n.a. / 0.21 | 0.28 / n.a. / 0.17 | 0.25 / n.a. / 0.15 |
| Patient Zero % (v0.45) | 36.3 (49.4) | 58.2 (75.5) | 61.9 (79.2) |
| Market Collapse % (v0.45) | 32.9 (33.1) | 20.3 (16.6) | 21.6 (16.5) |
| Singularity % (v0.45) | 26.0 (5.8) | 19.8 (4.3) | 16.2 (2.8) |
| Total Wipeout % | 4.75 | 1.83 | 0.33 |
| Income (b) v0.46 / v0.45 (ratio) | 6.71 / 5.33 (1.26) | 6.79 / 5.56 (1.22) | 6.81 / 5.60 (1.22) |
| Income (a) ratio | 1.61 | 1.53 | 1.53 |
| Green no-target % overall / rounds 7+ | 62.2 / 70.2 | 50.6 / 58.9 | 42.1 / 51.4 |
| 3-loss rounds % | 0.37 | 0.29 | 0.35 |
| Company spread (4P) / seat spread | n/a | n/a | 16.9 pp / 4.17 pp |
| 2+ L4, cap rounds | 0.0 / 0.01 | 0.0 / 0.02 | 0.0 / 0.01 |
| Back-to-back unaffordable (v0.45) | 0.88 (2.44) | 1.04 (2.82) | 1.21 (3.32) |

Pen Test reach (all seats, v0.45 in brackets): L4 15.4 (6.1) / 16.4 (5.4) / 15.5 (4.9); L1 about 78-83%. 2+ L4 = 0%. Singularity ends 26 / 20 / 16% (v0.45 6 / 4 / 3%), and games reaching v3.0 rise 53 to 61 / 45 to 54 / 43 to 52%.

## v1.0 card split (v0.46 | v0.45), per card

| pod | card | games % | v1.0 breach % | rounds | PZ % | Sing % | MC % | TW % |
|:---|:---|---:|:---|:---|:---|:---|:---|:---|
| 2P | Data Scraper | 51.1 | 15.0 \| 21.0 | 8.28 \| 7.16 | 50.4 \| 69.3 | 34.4 \| 7.5 | 7.5 \| 5.5 | 7.7 \| 17.6 |
| 2P | Script Kiddie | 48.9 | 5.6 \| 2.6 | 8.09 \| 7.69 | 21.6 \| 28.6 | 17.2 \| 4.1 | 59.5 \| 61.8 | 1.7 \| 5.5 |
| 3P | Data Scraper | 52.8 | 21.8 \| 31.2 | 7.20 \| 6.07 | 76.5 \| 92.6 | 18.8 \| 2.7 | 2.1 \| 0.2 | 2.7 \| 4.6 |
| 3P | Script Kiddie | 47.2 | 7.8 \| 4.9 | 8.44 \| 8.01 | 37.6 \| 56.4 | 20.8 \| 6.2 | 40.6 \| 35.0 | 0.9 \| 2.5 |
| 4P | Data Scraper | 50.3 | 24.3 \| 35.4 | 6.91 \| 5.68 | 83.3 \| 96.4 | 14.7 \| 1.2 | 1.3 \| 0.2 | 0.7 \| 2.3 |
| 4P | Script Kiddie | 49.7 | 9.4 \| 8.4 | 8.11 \| 7.79 | 40.3 \| 61.7 | 17.6 \| 4.4 | 42.1 \| 33.1 | 0.0 \| 0.8 |

The card gap is still wide: Data Scraper games run 1.0-1.2 rounds shorter at 3P/4P (7.20 and 6.91 vs 8.44 and 8.11), with 3-4x the v1.0 breach rate and 77-83% Patient Zero endings vs 38-40%. Both cards are better than v0.45 (Data Scraper breach -6 to -11 pp; its rounds +1.0 to +1.2), but Script Kiddie breach is higher (+1 to +3 pp).

## Dominance matrix

Focal win % vs Adaptive field (pp vs fair). N = 600, then in brackets the N = 2,400 rerun:

| focal | 2P | 3P | 4P |
|:---|:---|:---|:---|
| KeepAll | 42.5 (-7.5) [-8.3] PASS | 26.5 (-6.8) [-7.0] PASS | 19.5 (-5.5) [-6.1] PASS |
| RerollAllVuln | -11.5 [-11.7] PASS | -11.3 [-10.2] PASS | -8.8 [-8.8] PASS |
| PenTestRush | 49.2 (-0.8) [-2.2] PASS | 32.2 (-1.1) [+1.9] PASS | 30.8 (**+5.8** FAIL) [**+2.1** PASS] |
| Kamikaze | -17.8 [-18.0] PASS | -16.0 [-16.9] PASS | -14.5 [-13.5] PASS |
| Adaptive (vs Adaptive) | +2.5 [+1.5] | +0.8 [+1.3] | +5.5 [-0.4] |

The 600-game 4P PenTestRush FAIL (+5.8) did not survive the 2,400-game rerun (+2.1), so it was noise. Adaptive vs KeepAll / RerollAllVuln field at 3P: +8.8 / +16.5 (600), +8.0 / +14.8 (2,400), all PASS (floor is -3). The 2P KeepAll watch cell is -7.5 (-8.3 at 2,400): clearly not dominant. PenTestRush is no longer dominant (min-3 reference +0.8 / +2.1 at 3P/4P; now +1.9 / +2.1 at 2,400). Pen Test L4 for PenTestRush is 78.5 / 72.3% at 3P / 4P (2P 83.8%), with no other track past L2.

Adaptive keep rate in its own field: 39.6 / 38.0 / 38.9% (2P / 3P / 4P), inside 35-85% but at the low end, with round 1 only 15-16% and rounds 7-10 45-55%. Green loss per player-game, focal vs Adaptive field (2P / 3P / 4P): Adaptive 3.63 / 3.34 / 2.87, KeepAll 3.91 / 3.60 / 3.34, RerollAllVuln 2.34 / 2.22 / 1.81, PenTestRush 2.72 / 2.47 / 2.16, Kamikaze 5.87 / 5.59 / 5.40. Adaptive now loses 7-14% less Green than KeepAll (the previous run had it losing more).

## Keep rate per ⚠ face (main sweep, 2P / 3P / 4P)

Gray F1 21.9 / 19.9 / 19.0 (was 98%), Gray F2 17.9 / 17.4 / 14.8, Gray F3 20.6 / 20.2 / 18.5, Purple F4 39.2 / 37.0 / 33.4, Blue F3 8.9 / 8.5 / 7.8, Green F1 18.6 / 17.0 / 14.5, Red F1 39.3 / 54.0 / 59.5, Yellow F1 44.4 / 56.1 / 61.4, Yellow F5 20.2 / 18.9 / 17.4. Gray F1 is now in the reroll-heavy regime. But Gray F1-F3 sit at 15-22%, **below the plan's 30-80% band** (Purple F4 is in band). Bots now avoid Gray ⚠ most of the time, which is the intended direction but past the band.

## Bot-threshold check (pen_clean_target 3, trigger 4)

Main 3P with `--vuln-params '{"pen_clean_target":3,"pen_clean_trigger":4}'` and the matrix (3P row, `--no-repeat-2p4p`): the output is **bit-identical to the defaults** (Adaptive vs Adaptive +0.8, vs KeepAll +8.8, vs RerollAllVuln +16.5; Green loss 2.05; rounds 7.79). A 200-game probe shows that 2/3, 3/4 and the default are the same, and 1/2 or trigger 99 differ (1/2: Adaptive 34.0 vs 34.8, no gain). So 3/4 is a no-op under the 0-3 safe zone (cleaning only starts when it matters, and the thresholds below 4 don't bind). **No improvement, no recommended default change.** Note that `--out` takes a path under `sim_results/v046/` only when given an absolute or correct relative path: with `--out sim_results/v046/x.json` the sweep script crashed at save (path double-prefixed) after printing everything, so the JSON for that run was not written (stdout was complete).

## Pass/fail (income as (b))

| item | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Rounds 6.5-8.5 | PASS 8.19 | PASS 7.79 | PASS 7.50 |
| PZ, Wipeout | PASS | PASS | PASS |
| Market Collapse v0.45 +-5 | PASS (-0.2) | PASS (+3.7) | **FAIL (+5.1)** |
| v1.0 breach <= v0.45 | PASS | PASS | PASS |
| Green per player-game 1.2-2.5 | PASS 2.44 | PASS 2.05 | PASS 1.82 |
| Green per player-round (<= 0.35) | PASS 0.32 | PASS 0.28 | PASS 0.25 |
| Green no-target 25-70 | PASS 62.2 | PASS | PASS |
| No-target rounds 7+ (flag > 60) | **FAIL 70.2** | PASS 58.9 | PASS |
| 3-loss rounds, cap, 2+ L4, unaffordable | PASS | PASS | PASS |
| Income (b) <= +25% | **FAIL +26%** (marginal) | PASS +22% | PASS +22% |
| Company spread <= 10 (4P) | | | **FAIL 16.9** (colour 12.9) |
| Seat spread <= 6 | | | PASS 4.17 |
| Dominance cells | all PASS | all PASS | all PASS (PenTestRush +2.1 at 2,400) |
| Adaptive keep 35-85% | PASS 39.6 | PASS 38.0 | PASS 38.9 |
| Gray F1-F3 keep 30-80% | FAIL (15-22%) | FAIL | FAIL |

Residual concerns: 4P company/colour spread (colour spread grew 9.8 to 12.9), a Data Scraper v1.0 card that still ends games sooner with 3-4x the breach, and Singularity endings still 3-6x v0.45 (16-26%).

---

# Steps 4-5 (2026-11-18)

Defaults: package + 0-3 safe zone (same as the section above).

## Step 4: ref1 (3P, 1,200 games, v046_roster)

Command: `run_reference_bot_validation.py --config v046_roster --cells ref1 --players 3 --games 1200 --procs 7 --out-dir sim_results/v046 --overwrite` (wall 20m48s; 0 errors; `--procs 7` and `--overwrite` added to the given command).

| | seats | win % | keep rate | Pen Test steps / seat |
|:---|---:|---:|---:|---:|
| ref1 | 1,200 | **52.0** (fair 33.3, **+18.7 pp**) | 28.9% | 1.81 |
| Mixed field | 2,400 | 24.0 | 38.8% | 2.03 |

ref1 stance choices: ADAPTIVE 4,110, KEEP_ALL 2,946, REROLL_ALL 2,278, PEN_TEST_RUSH 883 (8.6% of 10,217).

**Verdict: FAIL.** The pass condition is no line better than about +5 pp over fair, and ref1 is +18.7 pp. Pen Test L4 is **not** its default (Rush is 8.6% of stances, and ref1 takes fewer Pen Test steps per seat, 1.81, than the field, 2.03). So the edge comes from something else (search over keep/reroll and stance mixing), which stdout does not identify. Not available in stdout: keep rate per ⚠ face (Gray in particular), Pen Test L4 rate, and tracks reached. They need a script flag or a read of the JSON (`sim_results/v046/v046_roster_push_nonref_ref1_3p_1200.json`), which I was told not to do.

## Step 5: arms (600 games per pod, 2P / 3P / 4P)

Method: `--step arm` prints only rounds, PZ, Wipeout, Collapse, Singularity and Green per player-game (no income, breach or company spread). So the non-Red arms were run via `--step main --games 600 --procs 7 --set '<arm overrides>'` for all three pods (same seeds), which gives the full metrics. The Red arms need integer-keyed dict overrides that JSON cannot express (red_B / red_AB crashed, red_none was silently different), so those four were run with `--step arm --players 2,3,4` and have no income / breach / spread columns. Default = `red_A` = `pen_cost_2` = `ds_secret` (identical output, as expected). SE at N=600: about +-1.6 pp for end rates, about +-3 pp for 4P company spread (differences under about 5 pp there are noise).

Default (2P / 3P / 4P): rounds 8.17 / 7.75 / 7.55; breach 12.3 / 15.7 / 17.7; PZ 39.5 / 61.8 / 62.0; Wipeout 4.3 / 1.7 / 0.5; Collapse 28.8 / 18.5 / 19.2; Singularity 27.3 / 18.0 / 18.3; Green per player-round 0.32 / 0.28 / 0.26; income (b) ratio 1.26 / 1.22 / 1.22; 4P company spread 19.1.

Trimmed table (arms that matter; each cell is 2P / 3P / 4P):

| arm | rounds | v1.0 breach | Wipeout % | Collapse % | Singularity % | Green / player-round | income (b) | 4P spread |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| default | 8.17 / 7.75 / 7.55 | 12.3 / 15.7 / 17.7 | 4.3 / 1.7 / 0.5 | 28.8 / 18.5 / 19.2 | 27.3 / 18.0 / 18.3 | .32 / .28 / .26 | 1.26 / 1.22 / 1.22 | 19.1 |
| premium_off | 8.20 / 7.61 / 7.45 | 11.7 / 18.5 / 17.5 | 5.3 / 1.8 / 0.2 | 33.7 / 19.8 / 20.5 | 28.3 / 18.0 / 17.2 | .31 / .28 / .26 | **1.12 / 1.08 / 1.07** | 14.6 |
| bands_3_6_9 | 8.02 / 7.43 / 7.17 | 12.2 / 18.3 / 20.2 | 6.2 / 1.7 / 0.7 | 27.0 / 16.8 / 17.3 | 27.0 / 17.3 / 15.0 | .36 / .32 / .29 | 1.25 / 1.22 / 1.21 | 12.4 |
| min_target_3 | 7.92 / 7.41 / 7.31 | 13.3 / 18.2 / 19.0 | 5.0 / 1.3 / 0.3 | 29.0 / 19.0 / 18.8 | 23.7 / 15.5 / 14.2 | .42 / .37 / .33 | 1.28 / 1.23 / 1.22 | 18.4 |
| v3_min3 | 8.13 / 7.73 / 7.49 | 12.3 / 15.7 / 17.7 | 4.3 / 1.8 / 0.5 | 28.0 / 17.8 / 20.2 | 26.7 / 17.8 / 14.8 | .35 / .31 / .28 | 1.26 / 1.22 / 1.23 | 17.6 |
| red_none | 8.07 / 7.73 / 7.14 | n/a | 4.8 / 1.0 / 0.2 | 30.8 / 22.5 / 24.7 | 26.2 / 18.0 / 10.7 | n/a | n/a | n/a |
| red_B | 8.21 / 7.64 / 7.28 | n/a | 5.2 / 1.2 / 0.0 | 26.2 / 16.3 / 20.7 | 29.3 / 19.5 / 13.8 | n/a | n/a | n/a |
| red_AB | 8.32 / 7.79 / 7.58 | n/a | 5.7 / 1.5 / 0.2 | 23.2 / 11.8 / 16.8 | 31.7 / 24.5 / 20.5 | n/a | n/a | n/a |
| pen_l1_zero | 8.32 / 7.81 / 7.53 | 11.8 / 16.2 / 18.3 | 4.5 / 1.8 / 0.3 | 29.8 / 19.3 / 21.2 | 29.5 / 19.3 / 19.5 | .27 / .25 / .22 | 1.23 / 1.19 / 1.18 | 20.1 |
| ds_cash | 7.73 / 7.14 / 6.72 | 17.8 / 25.0 / 28.8 | 5.7 / 2.3 / 0.5 | 29.2 / 18.3 / 19.5 | 22.8 / 17.0 / 13.3 | .31 / .27 / .25 | 1.26 / 1.22 / 1.21 | 21.9 |

Other arms (bands_3_5_7, green_yield_1/0, l4_set_zero, ctr_corruption3, pen_cost_1, pen_first_step_2, ds_both, ctr_l4_free0) show nothing beyond noise on the four failing items, or are worse: bands_3_5_7 raises breach (15.7 / 21.3 / 24.8) and shortens rounds (6.85 at 4P); ctr_corruption3 raises 4P spread to 24.6; ds_both 24.1. Full per-arm numbers are in the scratchpad JSON only, not committed.

### Against the four failing items

| item | default | best arm | verdict |
|:---|:---|:---|:---|
| 2P income (b) <= 1.25 | 1.26 | **premium_off 1.12** (and 3P 1.08, 4P 1.07) | Only arm that moves it |
| 4P company spread <= 10 | 19.1 | bands_3_6_9 12.4, premium_off 14.6 | Neither reaches 10; differences are about 1.5-2 SE |
| 4P Market Collapse (v0.45 +-5; v0.45 15.5 at this N) | 19.2 | bands_3_6_9 17.3 | Within noise of default |
| Singularity (lower is better) | 27 / 18 / 18 | min_target_3 23.7 / 15.5 / 14.2, red_none 4P 10.7 | Both break something else (below) |

**Break-checks:**
- premium_off: 2P Collapse 33.7 (v0.45 30.5, +3.2, still within +-5), 4P Collapse 20.5 (+5.0, borderline); other guardrails unchanged. No new failure.
- bands_3_6_9: Green 2P 2.68 (above 2.5 band, 0.36 per player-round above 0.35), 4P breach 20.2 (v0.45 23.7 OK), rounds 7.17 at 4P (OK). Breaks the 2P Green band.
- min_target_3 / v3_min3: 2P Green 3.14 / 2.64 (above 2.5). Breaks the Green band.
- red_none: 4P Collapse 24.7 (v0.45 15.5, +9), 3P Collapse 22.5 (+5.0). Breaks Collapse.
- red_AB: 3P Collapse 11.8 (below v0.45 17.5 by 5.7), Singularity up to 24.5 / 31.7. Breaks Collapse and Singularity.
- ds_cash: breach 25-29% (v0.45 22-24% at 3P/4P) and rounds 6.72 at 4P. Breaks rounds and breach.

### Verdict on arms

**Worth adopting: premium_off** (`die_face_profile: V046_VULN_NOPREMIUM`), if the target is the 2P income failure. It fixes income (b) at every pod (1.26 to 1.12 at 2P) with no new failure, and its 4P company spread (14.6) is lower though within noise. It does not fix Singularity (about 17-28%) or the 4P spread bound. **No arm reduces Singularity without breaking another guardrail**: the closest are bands_3_6_9 (4P 15.0, breaks 2P Green) and min_target_3 (breaks 2P Green). Both are options for the game-designer if Singularity matters more than the Green band. Total Wipeout stays 0.0-6.2% in every arm at every pod (2P maximum 6.2 in bands_3_6_9, well under 15).
