# v0.49 "Lock all dice" sweeps (on v0.48 base)

Preset `GameConfig.v049_roster()` = `v048_roster` + locked colored, Secret/R&D and Gray warning faces, V046_VULN premium faces, safe zone 0-4 (bands 5/8/11, min target 5), once-per-game Helix bypass. Seeds 42..1241 (1,200 per pod), mixed1 roster, `--assert-invariants` (no failures). Raw output: `sim_results/v049_lock_all/` (main + arms), `sim_results/v049_lock_all_grayoff/main.json`, `sim_results/v049_roster/dominance_matrix.json`.

Labels: the script prints the v048 comparator as "v0.46" and v049 as "v0.47". Here: **v048 / v049**.

**Comparator check:** the v048_roster rows reproduce FINDINGS section 64 (S2): rounds 8.31 / 8.37 / 8.12, Market Collapse 36.4 / 16.4 / 16.3 (script: 8.31 / 8.37 / 8.12, 36.42 / 16.42 / 16.33). Singularity % is not printed by the script and was not extracted (raw JSON not read).

## Main (v048 -> v049)
| Metric | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Rounds | 8.31 -> 8.41 | 8.37 -> 8.31 | 8.12 -> 8.06 |
| Patient Zero % | 31.3 -> 41.8 | 54.4 -> 60.7 | 60.4 -> 68.4 |
| Total Wipeout % | 7.0 -> 7.9 | 1.9 -> 2.5 | 0.6 -> 0.3 |
| Market Collapse % | 36.4 -> 26.1 | 16.4 -> 10.3 | 16.3 -> 10.1 |
| Green lost / player-game | 2.29 -> 1.82 | 2.11 -> 1.62 | 1.92 -> 1.45 |
| Green no-target % | 64.5 -> 71.3 | 53.4 -> 61.8 | 44.7 -> 53.7 |
| Pen Test steps / player-game | 2.10 -> 2.23 | 2.33 -> 2.43 | 2.44 -> 2.43 |
| End Secrets | 8.01 -> 6.35 | 8.03 -> 7.05 | 8.13 -> 7.45 |
| Locks / player-round | 1.79 | 1.80 | 1.77 |
| P(star) / colored die | 0.164 | 0.162 | 0.164 |

Paired deltas (95% CI): Market Collapse -10.3 [-13.0,-7.9] / -6.1 [-8.2,-3.6] / -6.3 [-8.4,-3.8]; Green lost -0.46 / -0.49 / -0.47 (all CIs exclude 0); end Secrets -1.7 / -1.0 / -0.7 (exclude 0); rounds CI includes 0 at every pod.

Locked warning faces (fraction of rolled dice of that colour, 2P / 3P / 4P): blue3 .219/.227/.217, blue5 .219/.220/.222, green1 .223/.235/.220, green5 .239/.233/.225, purple4 .193/.193/.192, purple5 .189/.192/.191, red1 .223/.216/.211, red5 .209/.212/.207, yellow1 .203/.200/.202, yellow5 .191/.187/.190. **Gray face 3 prints `n/a` per face** (script limitation); Gray's lock contribution appears only in "kept warning per player-round by source": gray 0.356 / 0.353 / 0.352 (core 0.81-0.85, secret 0.50-0.53). The gray-off control (below) drops locks/player-round 1.79 -> 1.36, so Gray locks add about 0.43 per player-round.

Helix (2P / 3P / 4P): bypass use 33.6 / 39.1 / 39.0 % of seats; burned by Black Signature 40.2 / 35.4 / 34.0 %; Helix locked-rerolls per game 0.22 / 0.43 / 0.55; **Helix win 39.5 / 26.9 / 16.8 %** (delta vs v048 -7.1 / +1.6 / -0.7 pp).

Win rates: Prodigy 48.5 / 31.6 / 21.3; Operator 54.5 / 33.2 / 21.4 (delta vs v048 Prodigy +0.7/+1.5/-1.1, Operator +3.4/+3.6/-0.9 pp).
4P company win %: Acoustic 26.1, Cipher 25.2, Operator 21.4, Phreaker 26.8, Prodigy 21.3, Spook 29.2, Helix 16.8. Script-reported company spread **20.1 pp** (seat spread 1.25 pp).
Per-colour win % (company die "a"): 2P red 47.7, blue 59.0*, green 43.5*; 3P 30.3, 43.3*, 26.7*; 4P 24.7, 33.6*, 17.0* (* > 5 pp from colour mean). Bought-dice "b" and weighted "c" views have no flags in the main run. The flags track the company die (confounded with company strength), same as the v0.47-on-v0.46 report.

## Guardrails (v0.49 main; absolute = v0.46 section 8.2 set vs v0.45, deltas vs v0.48; script verdicts)
| Guardrail | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Rounds 6.5-8.5 | PASS 8.41 | PASS 8.31 | PASS 8.06 |
| Patient Zero <= v0.45 + 3 | PASS | PASS | PASS |
| Total Wipeout cap | PASS 7.9 | PASS 2.5 | PASS 0.3 |
| Market Collapse v0.45 +-5 | **FAIL** 26.1 vs 33.1 | **FAIL** 10.3 vs 16.6 | **FAIL** 10.1 vs 16.5 |
| v1.0 breach <= v0.45 | PASS 7.3 | PASS 9.8 | PASS 11.3 |
| Green lost 1.2-2.5 | PASS | PASS | PASS |
| No-target overall 25-70 | **FAIL** 71.3 | PASS 61.8 | PASS 53.7 |
| No-target rounds 7+ <= 60 | **FAIL** 74.2 | **FAIL** 63.7 | PASS 55.5 |
| Lose-3 <= 5 % | PASS | PASS | PASS |
| Liquid income <= v0.45 x 1.25 | **FAIL** 8.18 | **FAIL** 8.26 | **FAIL** 8.25 |
| 4P company spread <= 10 | n/a | n/a | **FAIL** 20.1 |
| 4P seat spread <= 6 | n/a | n/a | PASS 1.25 |
| 2+ L4, cap, back-to-back | PASS | PASS | PASS |
| Per-colour parity 5 pp | **FAIL** | **FAIL** | **FAIL** |
| Helix win >= v0.48 - 2 pp | **FAIL** -7.1 | PASS +1.6 | PASS -0.7 |
| Prodigy within +-3 pp | PASS | PASS | PASS |
| Operator within +-3 pp | **FAIL** +3.4 | **FAIL** +3.6 | PASS |
| P(star) >= 0.12 | PASS | PASS | PASS |
| Colored dice bought >= v0.48 -10 % | PASS | PASS | PASS |

Liquid income (about 8.2 vs v0.45 4.1-4.4 x 1.25): the same metric-definition mismatch as before (v0.48 itself runs 1.26-1.30 x v0.45 old-bot per FINDINGS section 64 and was re-based). Market Collapse FAIL is a drop below the v0.45 band, not a rise; v0.48 was 36.4 / 16.4 / 16.3. The Helix 2P CI is -13.4 to -0.2; Operator CIs include 0.

## Arms (rounds | PZ % | TW % | MC % | Green lost | no-target % | Pen steps | end Secrets | Helix win %)
| Arm | 2P | 3P | 4P |
|:--|:--|:--|:--|
| main | 8.41 / 41.8 / 7.9 / 26.1 / 1.82 / 71.3 / 2.23 / 6.35 / 39.5 | 8.31 / 60.7 / 2.5 / 10.3 / 1.62 / 61.8 / 2.43 / 7.05 / 26.9 | 8.06 / 68.4 / 0.3 / 10.1 / 1.45 / 53.7 / 2.43 / 7.45 / 16.8 |
| B_safe03 | 8.14 / 44.1 / 8.8 / 26.2 / 2.11 / 65.3 / 2.63 / 6.17 / 37.4 | 7.95 / 66.1 / 1.2 / 11.2 / 1.88 / 55.6 / 2.71 / 6.67 / 26.9 | 7.83 / 70.5 / 0.8 / 10.5 / 1.67 / 47.7 / 2.92 / 7.12 / 14.8 |
| A_safe03 | 8.03 / 43.8 / 9.2 / 27.4 / 2.08 / 66.0 / 2.43 / 5.96 / 42.1 | 7.84 / 66.5 / 1.8 / 13.6 / 1.85 / 55.8 / 2.58 / 6.54 / 25.2 | 7.77 / 70.7 / 0.6 / 11.6 / 1.66 / 48.4 / 2.75 / 6.99 / 15.9 |
| A_nopremium | 8.27 / 41.8 / 8.6 / 26.8 / 1.79 / 71.6 / 2.06 / 6.40 / 36.0 | 8.23 / 60.7 / 3.0 / 12.5 / 1.61 / 62.3 / 2.25 / 6.77 / 25.0 | 8.09 / 67.3 / 1.0 / 11.9 / 1.45 / 54.9 / 2.33 / 7.31 / 14.9 |
| helix_per_version | 8.41 / 41.2 / 8.1 / 26.4 / 1.81 / 71.3 / 2.25 / 6.42 / 41.9 | 8.29 / 60.2 / 2.6 / 10.7 / 1.61 / 62.0 / 2.44 / 7.11 / 29.0 | 8.07 / 68.8 / 0.3 / 10.6 / 1.45 / 54.0 / 2.44 / 7.44 / 19.2 |
| helix_legacy | 8.46 / 39.6 / 7.3 / 28.2 / 1.86 / 70.9 / 2.23 / 6.88 / 46.0 | 8.26 / 60.9 / 1.7 / 11.2 / 1.61 / 61.9 / 2.38 / 7.34 / 30.8 | 8.16 / 63.9 / 0.3 / 11.3 / 1.47 / 53.9 / 2.46 / 7.78 / 21.0 |
| secret_lock_off | 8.26 / 41.8 / 9.8 / 25.4 / 1.71 / 72.1 / 2.09 / 6.26 / 37.9 | 7.99 / 64.6 / 2.8 / 10.4 / 1.45 / 63.7 / 2.19 / 6.50 / 26.4 | 7.94 / 69.5 / 0.6 / 11.1 / 1.32 / 56.3 / 2.29 / 6.86 / 12.9 |
| bots_aware | 8.22 / 41.6 / 8.3 / 27.8 / 2.13 / 67.1 / 2.40 / 6.37 / 36.7 | 7.97 / 63.6 / 2.8 / 12.7 / 1.82 / 56.4 / 2.58 / 6.78 / 23.2 | 7.93 / 68.8 / 0.5 / 11.3 / 1.67 / 49.1 / 2.79 / 7.01 / 16.9 |
| gray-off control (`vuln_lock_gray:false`, main step) | 8.34 / 39.4 / 9.9 / 27.1 / 2.18 / 66.0 / 2.08 / 6.55 / 38.1 | 8.15 / 61.8 / 2.8 / 12.0 / 1.92 / 55.4 / 2.23 / 6.90 / 24.7 | 7.92 / 68.3 / 0.3 / 11.3 / 1.75 / 47.2 / 2.36 / 7.29 / 14.9 |

Arm notes:
- **Safe 0-3 (B/A_safe03)** raises Green lost to 2.1 / 1.9 / 1.7 and cuts no-target to 65 / 56 / 48 %, and shortens games by 0.3-0.5 round (7.8-8.1). 2P no-target rounds 7+ still FAIL (68.5 for B). Helix 2P: -9.3 pp for B (FAIL), A_safe03 up to 42.1. A_safe03 passes every pod's no-target guardrail but keeps the colour-parity and 4P spread FAILs. 3P A_safe03 failed only Liquid income and colour parity.
- **A_nopremium:** nearly identical to main; premium faces change Green lost by under 0.03 and Pen steps by 0.1-0.2. Helix 2P -3.5 pp vs main, 4P -1.9.
- **helix_per_version / helix_legacy:** per-version lifts Helix by +2.4 / +2.1 / +2.4 pp; legacy (no lock bypass, no use) by +6.5 / +3.9 / +4.2 pp (46.0 / 30.8 / 21.0). Both clear the Helix delta bar; legacy gives the best 4P spread (19.5) but only marginally. The bypass is burned by Black 0 % in these arms.
- **secret_lock_off:** locks per player-round fall 1.79 -> 1.29; Green lost 1.71 / 1.45 / 1.32 and no-target rises to 72 / 64 / 56 %. Worse on the no-target guardrail. 4P spread 24.9. Prodigy 3P FAIL.
- **bots_aware:** locks 2.03-2.06 per player-round, P(star) falls to 0.133-0.137 (still above 0.12), Green lost 2.13 / 1.82 / 1.67; 4P spread 15.4 (best of all arms) but still FAIL.
- **Gray flag off:** locks 1.79 -> 1.36; Green lost up (2.18 / 1.92 / 1.75), no-target down (66.0 / 55.4 / 47.2 %), Pen steps down 0.15-0.07, Patient Zero down 2P. Locking Gray therefore costs about 0.4 Green lost per player-game and pushes 2P no-target over the 70 % cap.
- Tooling note: the batch ran a stray extra command (`A_nopremium` with `--set vuln_lock_gray false`) that overwrote `arm_A_nopremium.json`; the A_nopremium figures here come from the first run's printed summary. The gray-off control was rerun correctly on the main step to `v049_lock_all_grayoff`.

## Dominance matrix (3P, 600 games per cell, `v049_roster`, focal vs Adaptive field)
Win share (fair 33.3): Adaptive 32.7, RerollAllVuln 32.7, PenTestRush 33.0, StarChase 25.7, KeepAll / Kamikaze 18.8, NoColorReroll 14.2. Paired vs Adaptive control: RerollAllVuln +0.0, PenTestRush +0.3 [-4.7,+5.5], StarChase -7.0, KeepAll -13.8, NoColorReroll -18.5. Green loss per player-game: Adaptive 2.13, PenTestRush 1.23, StarChase 3.88, KeepAll 4.51, NoColorReroll 2.50. All rows marked ok; no dominant strategy (PenTestRush is neutral and does not reach 2 L4 tracks). Adaptive keep rate 62 %. Adaptive beats an all-KeepAll field by +17.5 pp.

## Reference bot ref1 (3P)
Run at 600 games (the script default), not 1,200; the 3P seat SE is about 2 pp. 1,200 games takes about 40 minutes per preset.
| Preset | ref1 win % (fair 33.3) | field win % | Ref keep rate | Ref 2+ L4 % |
|:--|:--|:--|:--|:--|
| v046 (FINDINGS section 62) | 44.9 | n/a | n/a | 28 |
| v048_roster | 53.0 | 23.5 | 40.0 | 76.7 |
| v049_roster | **60.7** | 19.7 | 41.6 | 86.0 |

No v0.48 ref1 figure existed in FINDINGS or docs/reports, so v048 was run here. v0.49 adds +7.7 pp over v0.48 (about 2.7 SE) and sits within the v0.36-v0.38 range (66.6-78.6 %) at its low end. Stance mix v049: Adaptive 32 %, KeepAll 18 %, StarChase 17 %, NoColorReroll 16 %, PenTestRush 16 %, RerollAll under 1 %. Watch item: the ref bot reaches 2+ L4 in 86 % of seats (field 0 %).

## Verdict
v0.49 makes a large Green loss and Market Collapse cut (about -0.47 Green lost, -6 to -10 pp Market Collapse) and keeps Singularity/rounds in band. Open failures: Market Collapse below the v0.45 band (all pods), 2P no-target (71.3 % overall, 74.2 % at rounds 7+) and 3P late no-target (63.7 %), Helix 2P -7.1 pp, Operator +3.4 / +3.6 pp, 4P company spread 20.1 pp, colour parity and the pre-existing income metric. ref1 rises to 60.7 %. Candidate fixes from the arms: safe zone 0-3 (A_safe03) for the no-target rows, helix_per_version for the Helix row.

## Final package (H1B) confirmation
`v049_roster` with Helix H1B (commit b344770), main step, mixed1 roster, 1,200 games per pod, seeds 42..1241, `--assert-invariants` (no invariant failures). Output: `sim_results/v049_final/`; ref1 output: `sim_results/reference_bot_v049_final/`. Columns are v0.48 -> v0.49 (H1B).

| Metric | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Rounds | 8.31 -> 8.42 | 8.37 -> 8.34 | 8.12 -> 8.12 |
| Patient Zero % | 31.3 -> 40.6 | 54.4 -> 59.5 | 60.4 -> 66.6 |
| Total Wipeout % | 7.0 -> 7.8 | 1.9 -> 2.1 | 0.6 -> 0.5 |
| Market Collapse % | 36.4 -> 26.6 | 16.4 -> 11.0 | 16.3 -> 10.2 |
| PZ + Collapse % | 67.8 -> 67.2 | 70.8 -> 70.5 | 76.8 -> 76.8 |
| Green lost / player-game | 2.29 -> 1.83 | 2.11 -> 1.63 | 1.92 -> 1.46 |
| Green no-target % | 64.5 -> 71.3 | 53.4 -> 61.9 | 44.7 -> 54.1 |
| Pen Test steps / player-game | 2.10 -> 2.24 | 2.33 -> 2.45 | 2.44 -> 2.48 |
| End Secrets | 8.01 -> 6.52 | 8.03 -> 7.18 | 8.13 -> 7.58 |
| Liquid income / player-round (v0.49) | 8.15 | 8.25 | 8.23 |

Paired deltas (95% CI): Market Collapse -9.8 [-12.8,-7.3] / -5.4 [-7.4,-3.2] / -6.2 [-8.3,-3.8]; Green lost -0.46 / -0.49 / -0.47 (CIs exclude 0).

**Helix win % (probe target 45.2 / 28.2 / 19.2):** 45.2 / 28.2 / 19.2 (exactly the probe). Delta vs v0.48: -1.4 / +2.8 / +1.7 pp (bar >= -2 pp: PASS at all pods; 2P CI -8.1 to +5.6). Bypass use 52.6 / 56.2 / 54.6 % of seats. `helix_lost_to_black` = **0.0 %** at all pods (must be 0: PASS). `helix_bypass_face_sets` and `helix_bypass_black_blocked` are not printed by the script and were not read from the JSON. Helix mean warnings removed 0.95 / 1.11 / 1.16. Prodigy 47.5 / 31.4 / 21.9, Operator 54.3 / 32.9 / 22.0.

**4P company win %:** Acoustic 25.4, Cipher 24.9, Operator 22.0, Phreaker 24.7, Prodigy 21.9, Spook 30.9, Helix 19.2. Script-reported company spread **18.41 pp** (v0.49 main earlier: 20.1); seat spread 0.58 pp. The bar is still FAIL; it is driven by Spook (+6 above the field) and by the colour-die confound.

**Reference bot ref1 (3P, 1,200 games, `v049_roster`):** ref1 win **60.6 %** (fair 33.3; SE about 1.4 pp), field 19.7 %, ref keep rate 33.8 %, Pen Test steps/seat 2.33, ref 2+ L4 88.3 % (field 0 %). Previous v0.49 run at 600 games read 60.7; v0.48 read 53.0 (600 games). Delta vs v0.48 is +7.6 pp (about 2.6 SE with the v0.48 600-game SE). Stance mix: Adaptive 29 %, KeepAll 18 %, StarChase 16 %, PenTestRush 15 %, NoColorReroll 15 %, RerollAll 0.6 %.

### Guardrails (re-based per GD plan section 11)
| Guardrail | 2P | 3P | 4P |
|:--|:--|:--|:--|
| Rounds 6.5-8.5 | PASS 8.42 | PASS 8.34 | PASS 8.12 |
| Patient Zero <= v0.45 + 3 | PASS | PASS | PASS |
| Total Wipeout cap | PASS 7.8 | PASS 2.1 | PASS 0.5 |
| PZ + Collapse <= v0.48 + 3 pp | PASS -0.6 | PASS -0.3 | PASS 0.0 |
| Collapse >= 8 % (3P/4P) | n/a | PASS 11.0 | PASS 10.2 |
| v1.0 breach <= v0.45 | PASS 7.2 | PASS 9.8 | PASS 11.0 |
| Green lost 1.2-2.5 | PASS | PASS | PASS |
| No-target overall 25-70 | FAIL 71.3 | PASS 61.9 | PASS 54.1 |
| No-target rounds 7+ <= 60 | FAIL 74.3 | FAIL 64.0 | PASS 56.2 |
| Lose-3 <= 5 % | PASS | PASS | PASS |
| Income <= v0.48 x 1.20 | PASS 1.17 (8.15 vs 6.94) | PASS* | PASS* |
| 4P company spread <= 10 | n/a | n/a | FAIL 18.41 |
| 4P seat spread <= 6 | n/a | n/a | PASS 0.58 |
| 2+ L4, cap, back-to-back | PASS | PASS | PASS |
| Per-colour parity 5 pp | FAIL | FAIL | FAIL |
| Helix win >= v0.48 - 2 pp | PASS -1.4 | PASS +2.8 | PASS +1.7 |
| Helix lost to Black = 0 | PASS | PASS | PASS |
| Prodigy within +-3 pp | PASS | PASS | PASS |
| Operator within +-3 pp | FAIL +3.2 | FAIL +3.3 | PASS -0.3 |
| P(star) >= 0.12 | PASS | PASS | PASS |
| Colored dice bought >= v0.48 -10 % | PASS | PASS | PASS |

\* The script does not print v0.48 income for 3P/4P. 2P v0.48 = 6.94 is from `docs/reports/v049_balance_assessment.md`. At 3P/4P the v0.49 income (8.25 / 8.23) matches the earlier run, which the assessment put at +18 % vs v0.48, so about x1.18; this is inferred, not computed from a printed v0.48 row.

Verdict: H1B restores Helix to the probe target at every pod with zero Black Signature losses. The re-based Market Collapse and income rows PASS. Remaining FAILs are unchanged from the main run: 2P and 3P late no-target, 2P overall no-target, 4P company spread, per-colour parity, and Operator +3 pp at 2P/3P (CIs include 0).
