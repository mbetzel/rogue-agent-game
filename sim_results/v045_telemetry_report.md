# v0.45.0 Monte Carlo Telemetry Report

- **Configs**: `GameConfig.v045_roster()` vs `GameConfig.v044_roster()`
- **Sample**: 1000 games/pod/variant (seeds `42..1041`), elapsed `9.0s`

## 1. Pacing & Endings

| Pod | Variant | Mean Rounds | Singularity % | Patient Zero % | Market Collapse % | Total Wipeout % | v1.0 Breach % |
|---:|:---|---:|---:|---:|---:|---:|---:|
| 2P | `v044_roster` | 7.19 | 9.5% | 43.0% | 35.9% | 11.6% | 19.2% |
| 2P | `v045_roster` | 7.47 | 6.3% | 47.0% | 34.1% | 12.6% | 11.0% |
| 3P | `v044_roster` | 7.42 | 6.4% | 69.0% | 19.4% | 5.2% | 18.6% |
| 3P | `v045_roster` | 6.92 | 3.1% | 74.5% | 17.6% | 4.8% | 20.4% |
| 4P | `v044_roster` | 7.08 | 5.7% | 72.0% | 20.4% | 1.9% | 22.2% |
| 4P | `v045_roster` | 6.65 | 3.0% | 78.0% | 17.9% | 1.1% | 24.3% |

## 2. Defense Grid Overflow & Green Cube Stress

| Pod | Variant | Games w/ Overflow % | Overflows / Game | Secrets Lost / Game | Slots Purged / Game | Cubes Purged / Game | Final Green Util % | Clamped / Game |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|
| 2P | `v044_roster` | 0.0% | 0.00 | 0.00 | 7.02 | 7.02 | 41.2% | 0.04 |
| 2P | `v045_roster` | 55.1% | 2.83 | 2.83 | 7.51 | 9.75 | 67.2% | 0.03 |
| 3P | `v044_roster` | 0.0% | 0.00 | 0.00 | 10.54 | 10.54 | 41.0% | 0.03 |
| 3P | `v045_roster` | 57.8% | 3.43 | 3.43 | 10.02 | 12.57 | 63.9% | 0.01 |
| 4P | `v044_roster` | 0.0% | 0.00 | 0.00 | 13.24 | 13.24 | 40.1% | 0.03 |
| 4P | `v045_roster` | 55.9% | 3.70 | 3.70 | 12.61 | 15.54 | 60.7% | 0.01 |

## 3. WS-OPERATOR Telemetry

| Pod | Variant | Appearances | Win Rate % | Research / Game | Triggers / Game | Research / Trigger |
|---:|:---|---:|---:|---:|---:|---:|
| 2P | `v044_roster` | 352 | 45.7% | 0.52 | 0.43 | 1.20 |
| 2P | `v045_roster` | 352 | 46.9% | 0.54 | 0.45 | 1.20 |
| 3P | `v044_roster` | 516 | 34.9% | 0.56 | 0.49 | 1.14 |
| 3P | `v045_roster` | 516 | 35.7% | 0.51 | 0.46 | 1.11 |
| 4P | `v044_roster` | 684 | 23.7% | 0.67 | 0.55 | 1.22 |
| 4P | `v045_roster` | 684 | 23.0% | 0.57 | 0.50 | 1.14 |

## 4. 2P SETEC Corp (v0.45.0)

| Metric | Value |
|:---|---:|
| Mean Final SETEC Market Share | 6.33 |
| SETEC 1st / 2nd / 3rd Place % | 44.0% / 18.1% / 37.9% |
| Mean SETEC Advances / Game | 6.33 |
| Human Market Leader Bonus Share | 85.9% |
| Mean Human MLB Secrets / Game | 9.50 |
| Mean SETEC MLB Secrets Absorbed / Game | 1.55 |
| 2P Market Collapse % (v0.45 vs v0.44) | 34.1% vs 35.9% |

## 5. Notable Outlier Seeds (`v045_roster`)

- **2P**: shortest={'seed': 48, 'rounds': 2, 'end_reason': 'total_wipeout'}; longest={'seed': 268, 'rounds': 12, 'end_reason': 'patient_zero'}; fastest_v1_breach={'seed': 48, 'round': 2, 'end_reason': 'total_wipeout'}; max_overflow={'seed': 927, 'overflow_events': 25, 'secrets_lost': 25, 'rounds': 9}; max_setec_ms={'seed': 268, 'setec_ms': 12, 'rounds': 12, 'end_reason': 'patient_zero'}
- **3P**: shortest={'seed': 78, 'rounds': 2, 'end_reason': 'patient_zero'}; longest={'seed': 555, 'rounds': 12, 'end_reason': 'singularity'}; fastest_v1_breach={'seed': 78, 'round': 2, 'end_reason': 'patient_zero'}; max_overflow={'seed': 608, 'overflow_events': 30, 'secrets_lost': 30, 'rounds': 9}
- **4P**: shortest={'seed': 53, 'rounds': 2, 'end_reason': 'patient_zero'}; longest={'seed': 109, 'rounds': 12, 'end_reason': 'singularity'}; fastest_v1_breach={'seed': 53, 'round': 2, 'end_reason': 'patient_zero'}; max_overflow={'seed': 721, 'overflow_events': 38, 'secrets_lost': 38, 'rounds': 8}
