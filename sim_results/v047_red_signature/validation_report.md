# v0.47.0 Red Signature confirm sweep (spec §9.2)

4,000 games per arm, seeds 42..4041, `mixed1` roster, `v046_roster` vs `v047_roster`; 2P also arm D1 (`signature_red_setec_gain=1`).
Runner `scripts/run_v047_red_signature_sweep.py`, summary `scripts/summarize_v047_red_signature.py`; raw JSON alongside (not read back). Reference: `docs/findings/red_signature_lowest_rival_analysis.md` §3-§6 (12k games).
Archetype CIs: normal approx, per-seat win fractions (Mixed has 1 seat per game so a narrower CI). Spread = max - min archetype win %.

## Pace / endings
| arm | n | rounds | MC% | PZ% | Sing% | TW% | winner Secrets |
|---|---|---|---|---|---|---|---|
| 2P_v046 | 4000 | 8.09 | 36.8 | 33.3 | 25.1 | 4.8 | 12.52 |
| 2P_v047 | 4000 | 8.15 | 33.6 | 34.5 | 26.9 | 4.9 | 11.53 |
| 2P_v047_D1 | 4000 | 8.16 | 34.2 | 34.3 | 26.7 | 4.8 | 11.74 |
| 3P_v046 | 4000 | 7.84 | 23.4 | 54.5 | 20.7 | 1.4 | 12.95 |
| 3P_v047 | 4000 | 8.11 | 14.8 | 56.6 | 27.0 | 1.5 | 12.61 |
| 4P_v046 | 4000 | 7.50 | 24.0 | 60.1 | 15.7 | 0.3 | 13.82 |
| 4P_v047 | 4000 | 7.84 | 13.4 | 63.0 | 23.3 | 0.3 | 13.48 |
  (end reasons raw: {'2P_v046': {'market_collapse': 1471, 'patient_zero': 1333, 'singularity': 1004, 'total_wipeout': 192}, '2P_v047': {'market_collapse': 1346, 'patient_zero': 1382, 'singularity': 1077, 'total_wipeout': 195}, '2P_v047_D1': {'market_collapse': 1367, 'patient_zero': 1372, 'singularity': 1067, 'total_wipeout': 194}, '3P_v046': {'patient_zero': 2181, 'singularity': 828, 'market_collapse': 934, 'total_wipeout': 57}, '3P_v047': {'patient_zero': 2265, 'singularity': 1081, 'market_collapse': 594, 'total_wipeout': 60}, '4P_v046': {'market_collapse': 959, 'patient_zero': 2404, 'singularity': 626, 'total_wipeout': 11}, '4P_v047': {'market_collapse': 535, 'patient_zero': 2521, 'singularity': 932, 'total_wipeout': 12}} )

## Archetype win % (95% CI) and spread

- 2P_v046: AccelerationistBot 50.1±3.5, AdaptiveBalancedBot 58.4±3.5, MixedPolicyBot 47.9±1.5, RecklessSaboteurBot 45.4±3.4, SecOpsTurtleBot 55.0±3.4, VentureGreedBot 51.7±3.5 | **spread 13.0** | company spread 17.8
- 2P_v047: AccelerationistBot 53.8±3.5, AdaptiveBalancedBot 60.5±3.4, MixedPolicyBot 46.5±1.5, RecklessSaboteurBot 43.9±3.4, SecOpsTurtleBot 60.0±3.3, VentureGreedBot 49.2±3.5 | **spread 16.6** | company spread 19.1
- 2P_v047_D1: AccelerationistBot 52.5±3.5, AdaptiveBalancedBot 60.2±3.4, MixedPolicyBot 46.7±1.5, RecklessSaboteurBot 44.3±3.4, SecOpsTurtleBot 58.9±3.3, VentureGreedBot 50.7±3.5 | **spread 15.9** | company spread 19.3
- 3P_v046: AccelerationistBot 35.8±2.3, AdaptiveBalancedBot 37.7±2.4, MixedPolicyBot 29.6±1.4, RecklessSaboteurBot 27.1±2.2, SecOpsTurtleBot 41.5±2.4, VentureGreedBot 33.7±2.4 | **spread 14.4** | company spread 17.1
- 3P_v047: AccelerationistBot 35.7±2.3, AdaptiveBalancedBot 38.1±2.4, MixedPolicyBot 29.7±1.4, RecklessSaboteurBot 25.2±2.1, SecOpsTurtleBot 42.2±2.4, VentureGreedBot 34.6±2.4 | **spread 17.0** | company spread 16.0
- 4P_v046: AccelerationistBot 24.6±1.7, AdaptiveBalancedBot 28.2±1.8, MixedPolicyBot 22.3±1.3, RecklessSaboteurBot 20.7±1.6, SecOpsTurtleBot 31.6±1.9, VentureGreedBot 24.4±1.7 | **spread 11.0** | company spread 14.6
- 4P_v047: AccelerationistBot 24.2±1.7, AdaptiveBalancedBot 29.9±1.8, MixedPolicyBot 22.1±1.3, RecklessSaboteurBot 18.9±1.6, SecOpsTurtleBot 32.2±1.9, VentureGreedBot 24.7±1.7 | **spread 13.3** | company spread 16.0

## SETEC Corp (2P)
| arm | final MS | MLB 1st/g | MLB 2nd/g | Secrets absorbed/g |
|---|---|---|---|---|
| 2P_v046 | 6.74 | 0.37 | 0.54 | 1.65 |
| 2P_v047 | 8.48 | 0.81 | 0.39 | 2.81 |
| 2P_v047_D1 | 7.70 | 0.67 | 0.43 | 2.44 |

## signature_red telemetry (per 1000 games; fizzle % of events; SETEC share of gifts)
| arm | events/g | gifts_locked | mutual | fizzles | setec_gifts | setec_ms | capped | zero_rescues | fizzle% | setec share |
|---|---|---|---|---|---|---|---|---|---|---|
| 2P_v046 | 1.23 | 0 | 0 | 2568 | 0 | 0 | 0 | 0 | 52.1 | 0.0 |
| 2P_v047 | 1.23 | 1258 | 551 | 0 | 2934 | 6812 | 0 | 698 | 0.0 | 59.6 |
| 2P_v047_D1 | 1.25 | 1240 | 522 | 0 | 3169 | 3664 | 0 | 694 | 0.0 | 63.6 |
| 3P_v046 | 1.53 | 0 | 0 | 1438 | 0 | 0 | 0 | 0 | 23.6 | 0.0 |
| 3P_v047 | 1.64 | 4756 | 1909 | 21 | 0 | 0 | 1 | 746 | 0.3 | 0.0 |
| 4P_v046 | 1.63 | 0 | 0 | 683 | 0 | 0 | 0 | 0 | 10.5 | 0.0 |
| 4P_v047 | 1.77 | 6726 | 2234 | 2 | 0 | 0 | 0 | 1030 | 0.0 | 0.0 |

## Deltas v047 - v046
- 2P: rounds +0.06, MC -3.1, Sing +1.8, arch spread +3.5 (13.0->16.6), company spread +1.3
- 3P: rounds +0.27, MC -8.5, Sing +6.3, arch spread +2.6 (14.4->17.0), company spread -1.1
- 4P: rounds +0.34, MC -10.6, Sing +7.7, arch spread +2.4 (11.0->13.3), company spread +1.4

Note on "SETEC share of gifts": telemetry `setec_gifts` counts events with a SETEC recipient (59.6% of 2P events). Gain-based estimate (setec_ms_gained/2 over events plus double-lock extras at the analysis' 24% share, not measured here) is about 56%, matching the analysis. The unlocked-human-recipient count is not a counter, so the exact per-gift share was not measured.

## Acceptance (spec §9.2 / §9.3)
| Criterion | Result | Verdict |
|---|---|---|
| 2P fizzle 0% | 0 of 4,920 events (v046: 52.1%) | PASS |
| 2P SETEC share of gifts ~56% | 59.6% per event; ~56% gain-based estimate | PASS (definition caveat) |
| 3P Market Collapse 13-15% | 14.8% (v046 23.4%) | PASS |
| 4P Market Collapse 13-15% | 13.4% (v046 24.0%) | PASS |
| 3P Singularity 23-27% | 27.0% (edge of band; analysis 27.4%) | PASS |
| 4P Singularity 23-27% | 23.3% (analysis 22.7%) | PASS |
| About +0.3 rounds (3P/4P) | +0.27 / +0.34 (2P +0.06) | PASS |
| 2P archetype spread ~16.3 | 16.6 (v046 13.0); D1 15.9 | PASS |
| 4P spread rise <= +4 (release-blocking) | +2.4 (11.0 -> 13.3); analysis +2.7. SecOps +0.6, Reckless -1.8 | PASS, watch item not triggered |
Other: 3P spread +2.6 (analysis +1.5; Reckless -1.9, within noise at this CI); company spread 2P +1.3, 3P -1.1, 4P +1.4; Total Wipeout unchanged (4.8->4.9, 1.4->1.5, 0.3->0.3). 2P SETEC final MS 8.48, MLB 1st 0.81/g, absorbed 2.81/g (analysis A: 8.49 / 0.78 / 2.74); D1 7.70 / 0.67 / 2.44 (analysis 7.72 / 0.66 / 2.41). All telemetry matches the analysis.
