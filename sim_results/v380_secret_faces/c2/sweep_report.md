# C2 (v038b) confirm sweep (Phase 49)

Config v038b = C2 (lever A off; the ref1 runs used `--pr-push off` to match the preset, so the 71.2% reference value, measured with push on, is not a like-for-like comparison; Market Share 14, Market Leader Bonus +4 / +4,+2, starting Secrets 3/4/4, Market Collapse on, lever A off). Seeds 42..1241, 1,200 games per cell, roster mixed1 (one MixedPolicyBot seat at seed % P), `--procs 8`. v037 base rows are reused from ../v037_roster.json (same seeds). Raw JSON files are in this folder.

## Endings, rounds, breach

| P | cell | Singularity | Patient Zero | Total Wipeout | Market Collapse | round limit | mean rounds | breach | winner Secrets |
|---|---|---|---|---|---|---|---|---|---|
| 2 | C2 v038b | 33.8 | 33.7 | 3.4 | 29.1 | 0.0 | 8.151 | 39.0 | 10.878 |
| 2 | v037 base | 47.0 | 20.4 | 7.6 | 25.0 | 0.0 | 9.126 | 30.8 | 6.329 |
| 3 | C2 v038b | 27.4 | 39.6 | 0.2 | 32.8 | 0.0 | 8.164 | 41.2 | 12.932 |
| 3 | v037 base | 37.7 | 37.5 | 3.9 | 20.9 | 0.0 | 8.875 | 45.2 | 6.26 |
| 4 | C2 v038b | 25.3 | 39.9 | 0.2 | 34.6 | 0.0 | 7.915 | 41.6 | 13.719 |
| 4 | v037 base | 41.5 | 29.9 | 1.5 | 27.1 | 0.0 | 8.998 | 34.8 | 7.402 |

## Win rate by archetype (%)

| P | cell | Accelerationist | AdaptiveBalanced | MixedPolicy | RecklessSaboteur | SecOpsTurtle | VentureGreed | spread (pts) |
|---|---|---|---|---|---|---|---|---|
| 2 | C2 v038b | 51.9 | 68.9 | 49.6 | 33.2 | 57.9 | 39.9 | 35.7 |
| 2 | v037 base | 59.7 | 50.6 | 49.1 | 33.6 | 50.6 | 60.5 | 26.9 |
| 3 | C2 v038b | 37.6 | 53.2 | 33.1 | 15.1 | 38.3 | 23.7 | 38.2 |
| 3 | v037 base | 39.9 | 26.1 | 33.6 | 15.7 | 34.0 | 51.7 | 36.1 |
| 4 | C2 v038b | 20.0 | 43.3 | 28.8 | 10.0 | 28.6 | 16.8 | 33.3 |
| 4 | v037 base | 31.4 | 15.2 | 26.2 | 6.8 | 28.6 | 40.9 | 34.1 |

## Win rate by Company colour and by path (%)

Path is the colour holding at least 60% of a player's owned Red, Blue, Green and Yellow dice at game end; otherwise the path is mixed (Mixed/Diverse). Seat counts are in parentheses.

| P | cell | Co Red | Co Blue | Co Green | path red | path blue | path green | path yellow | path mixed |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | C2 v038b | 56.9 | 45.0 | 48.2 | 54.0 (420) | 47.5 (181) | 53.3 (344) | 39.4 (241) | 50.1 (1214) |
| 2 | v037 base | 46.6 | 58.3 | 45.2 | 41.8 (541) | 61.9 (501) | 61.2 (116) | 38.2 (102) | 48.6 (1140) |
| 3 | C2 v038b | 39.4 | 29.7 | 31.2 | 43.9 (592) | 29.1 (265) | 38.2 (649) | 20.8 (457) | 31.8 (1637) |
| 3 | v037 base | 27.3 | 43.0 | 29.8 | 23.6 (886) | 48.0 (859) | 38.1 (155) | 21.7 (157) | 31.5 (1543) |
| 4 | C2 v038b | 34.4 | 19.5 | 21.2 | 41.4 (917) | 20.3 (389) | 21.9 (895) | 12.1 (529) | 23.2 (2070) |
| 4 | v037 base | 22.6 | 34.0 | 18.7 | 14.3 (1169) | 37.5 (1154) | 34.2 (219) | 21.4 (275) | 23.5 (1983) |

## Secrets by source (per seat), stranded, Glitched Shield Slots

| P | cell | face R/B/G/P | blue dmg | corruption | MLB | stranded % | slots glitched cube/corr | cleaned die/face/grad | max slots | zero-cap rds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | C2 v038b | 2.832/1.234/2.699/1.403 | -6.08 | -0.472 | 2.267 | 2.6 | 5.841/2.079 | 1.212/0.414/5.255 | 2.047 | 0.0 |
| 2 | v037 base | 0/0/0/0 | 0 | 0 | 0 | 0.0 | 0/0 | 0.0/0.0/0.0 | 0.0 | 0.0 |
| 3 | C2 v038b | 2.795/1.248/2.981/1.42 | -6.543 | -0.425 | 2.385 | 2.1 | 5.828/2.083 | 1.107/0.44/5.29 | 2.104 | 0.0 |
| 3 | v037 base | 0/0/0/0 | 0 | 0 | 0 | 0.0 | 0/0 | 0.0/0.0/0.0 | 0.0 | 0.0 |
| 4 | C2 v038b | 3.02/1.141/2.872/1.392 | -6.036 | -0.376 | 1.942 | 2.1 | 5.695/1.97 | 1.035/0.422/5.178 | 2.066 | 0.0 |
| 4 | v037 base | 0/0/0/0 | 0 | 0 | 0 | 0.0 | 0/0 | 0.0/0.0/0.0 | 0.0 | 0.0 |

## Final Market Share and cube exits

| P | cell | MS 0 % | MS 1–3 % | MS 4–7 % | MS 8–12 % | min MS avg | exits R/B/G |
|---|---|---|---|---|---|---|---|
| 2 | C2 v038b | 14.1 | 29.5 | 23.5 | 32.9 | 4.965 | 17.117/13.039/14.633 |
| 2 | v037 base | 17.3 | 25.6 | 26.6 | 30.4 | 4.818 | 20.667/15.679/17.478 |
| 3 | C2 v038b | 14.0 | 29.9 | 23.6 | 32.6 | 4.848 | 16.887/13.287/14.241 |
| 3 | v037 base | 12.6 | 21.5 | 26.3 | 39.6 | 6.022 | 19.563/15.081/16.244 |
| 4 | C2 v038b | 9.6 | 28.9 | 24.1 | 37.4 | 5.438 | 15.967/12.374/13.445 |
| 4 | v037 base | 12.1 | 24.0 | 27.9 | 36.0 | 5.702 | 20.169/15.208/16.878 |

## Outlier seeds

| P | cell | shortest | longest | Total Wipeout | round limit | highest winner Secrets |
|---|---|---|---|---|---|---|
| 2 | C2 v038b | 87,494,579,677,1056 | 1240,1228,1192,1190,1188 | 43,53,107,176,178,214,216,287,318,334,347,354,377,429,443,449,469,481,488,490 | - | 468,203,422,1105,417 |
| 2 | v037 base | 579,80,178,216,346 | 1240,1216,1211,1210,1208 | 48,52,71,72,130,139,142,151,173,177,240,254,272,276,280,303,318,324,328,330 | - | 46,42,95,99,101 |
| 3 | C2 v038b | 57,122,557,669,672 | 1228,1208,1141,1128,1075 | 885,1091 | - | 185,773,705,1141,180 |
| 3 | v037 base | 770,84,173,579,929 | 1238,1227,1216,1208,1202 | 51,57,62,69,76,85,86,92,95,105,121,148,151,176,178,200,207,227,232,291 | - | 259,650,1172,74,112 |
| 4 | C2 v038b | 72,148,216,325,343 | 1238,1190,1184,1156,1145 | 68,1193 | - | 190,1022,338,1190,376 |
| 4 | v037 base | 400,63,139,273,346 | 1208,1201,1189,1184,1156 | 87,123,231,306,328,373,402,585,622,672,702,715,818,882,904,930,1154,1225 | - | 159,111,152,618,1016 |

## Purchases per seat by archetype

| P | archetype | purchases by colour |
|---|---|---|
| 2 | AccelerationistBot | blue 0.065, green 1.485, red 0.459, yellow 0.541 |
| 2 | AdaptiveBalancedBot | blue 0.174, green 0.34, red 0.78, yellow 0.419 |
| 2 | MixedPolicyBot | blue 0.188, green 0.336, red 0.982, yellow 0.839 |
| 2 | RecklessSaboteurBot | blue 0.18, green 0.098, red 0.787, yellow 0.439 |
| 2 | SecOpsTurtleBot | blue 0.207, green 0.069, red 0.102, yellow 0.195 |
| 2 | VentureGreedBot | blue 0.42, green 0.983, red 1.462, yellow 2.319 |
| 3 | AccelerationistBot | blue 0.034, green 2.025, red 0.445, yellow 0.618 |
| 3 | AdaptiveBalancedBot | blue 0.198, green 0.36, red 0.815, yellow 0.379 |
| 3 | MixedPolicyBot | blue 0.15, green 0.328, red 1.2, yellow 1.003 |
| 3 | RecklessSaboteurBot | blue 0.058, green 0.118, red 0.91, yellow 0.635 |
| 3 | SecOpsTurtleBot | blue 0.16, green 0.055, red 0.121, yellow 0.14 |
| 3 | VentureGreedBot | blue 0.32, green 0.798, red 1.715, yellow 3.026 |
| 4 | AccelerationistBot | blue 0.025, green 2.039, red 0.515, yellow 0.527 |
| 4 | AdaptiveBalancedBot | blue 0.162, green 0.328, red 0.961, yellow 0.36 |
| 4 | MixedPolicyBot | blue 0.163, green 0.367, red 1.306, yellow 0.926 |
| 4 | RecklessSaboteurBot | blue 0.071, green 0.122, red 0.951, yellow 0.525 |
| 4 | SecOpsTurtleBot | blue 0.175, green 0.073, red 0.139, yellow 0.161 |
| 4 | VentureGreedBot | blue 0.281, green 0.73, red 1.725, yellow 3.198 |

## Guardrails

| check | result | flag |
|---|---|---|
| 2P Singularity ≤ 48% (C2 v038b) | 33.8 | OK |
| 2P rounds 8–11 (C2 v038b) | 8.151 | OK |
| 2P Singularity ≤ 48% (v037 base) | 47.0 | OK |
| 2P rounds 8–11 (v037 base) | 9.126 | OK |
| 3P Total Wipeout ≤ 5% (C2 v038b) | 0.2 | OK |
| 3P rounds 8–11 (C2 v038b) | 8.164 | OK |
| 3P Total Wipeout ≤ 5% (v037 base) | 3.9 | OK |
| 3P rounds 8–11 (v037 base) | 8.875 | OK |
| 4P Total Wipeout ≤ 5% (C2 v038b) | 0.2 | OK |
| 4P rounds 8–11 (C2 v038b) | 7.915 | FAIL |
| 4P Total Wipeout ≤ 5% (v037 base) | 1.5 | OK |
| 4P rounds 8–11 (v037 base) | 8.998 | OK |
| 2P archetype spread vs v037 | 35.7 vs 26.9 pts | WIDER |
| 3P archetype spread vs v037 | 38.2 vs 36.1 pts | WIDER |
| 4P archetype spread vs v037 | 33.3 vs 34.1 pts | OK |
| ref1 v038b_nonref_ref1_2p_1200.json (ref 71.2%) | 92.4 | ABOVE 71.2 |
| ref1 v038b_nonref_ref1_3p_1200.json (ref 71.2%) | 84.1 | ABOVE 71.2 |
