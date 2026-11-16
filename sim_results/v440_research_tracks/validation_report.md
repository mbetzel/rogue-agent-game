# v0.44.0 Research Tracks & Capstones Validation Report

**Sweep:** `v043` (Baseline) vs `v044` (Candidate) | **Pods:** 4P, 3P, 2P | **Games/pod/variant:** 1200 (seeds 42..1241, 7200 games total)

## 1. Macro Pacing & End-Game Triad

| Pod | Variant | Mean Rounds | Median (Min–Max) | Wipeout % | Singularity % | Patient Zero % | Market Collapse % |
|---|---|---|---|---|---|---|---|
| 4P | `v043` | 7.43 | 8 (2–12) | 2.08% | 4.67% | 73.83% | 19.42% |
| 4P | `v044` | 7.30 | 8 (2–12) | 2.00% | 5.08% | 73.17% | 19.75% |
| 3P | `v043` | 7.78 | 8 (2–12) | 4.33% | 8.17% | 65.17% | 22.33% |
| 3P | `v044` | 7.61 | 8 (2–12) | 4.50% | 7.67% | 63.92% | 23.92% |
| 2P | `v043` | 7.58 | 8 (1–13) | 10.83% | 8.17% | 43.50% | 37.50% |
| 2P | `v044` | 7.49 | 8 (1–12) | 11.00% | 10.00% | 41.67% | 37.33% |

## 2. Research Track Progression & L4 Capstone Rates

| Pod | Variant | Track | Mean Lvl | L2+ Seat % | L3+ Seat % | L4 Seat % | L4 Game % | 2+ L4 Seats % |
|---|---|---|---|---|---|---|---|---|
| 4P | `v043` | Defense Grid | 1.25 | 33.4% | 14.7% | 8.08% | 32.33% | 0.00% |
| 4P | `v044` | Defense Grid | 0.95 | 23.9% | 8.1% | 4.19% | 16.75% | 0.00% |
| 4P | `v043` | Triage | 1.72 | 39.4% | 32.8% | 24.40% | 74.00% | 0.00% |
| 4P | `v044` | Triage | 2.46 | 93.4% | 31.1% | 21.81% | 67.00% | 0.00% |
| 4P | `v043` | Release | 1.79 | 46.9% | 36.3% | 33.04% | 88.25% | 0.00% |
| 4P | `v044` | Release | 1.60 | 42.2% | 30.7% | 26.31% | 73.25% | 0.00% |
| 4P | `v043` | Public Relations | 0.61 | 13.1% | 0.0% | 0.00% | 0.00% | 0.00% |
| 4P | `v044` | Public Relations | 0.50 | 10.5% | 0.0% | 0.00% | 0.00% | 0.00% |
| 3P | `v043` | Defense Grid | 1.24 | 32.8% | 14.3% | 8.44% | 25.33% | 0.00% |
| 3P | `v044` | Defense Grid | 0.97 | 24.2% | 8.4% | 4.36% | 13.08% | 0.00% |
| 3P | `v043` | Triage | 1.72 | 39.5% | 32.7% | 24.39% | 57.50% | 0.00% |
| 3P | `v044` | Triage | 2.47 | 94.1% | 31.2% | 21.56% | 52.17% | 0.00% |
| 3P | `v043` | Release | 1.82 | 47.2% | 36.7% | 33.14% | 70.25% | 0.00% |
| 3P | `v044` | Release | 1.60 | 42.4% | 30.8% | 26.17% | 58.17% | 0.00% |
| 3P | `v043` | Public Relations | 0.62 | 12.9% | 0.0% | 0.00% | 0.00% | 0.00% |
| 3P | `v044` | Public Relations | 0.51 | 10.6% | 0.0% | 0.00% | 0.00% | 0.00% |
| 2P | `v043` | Defense Grid | 1.12 | 30.3% | 13.6% | 7.29% | 14.58% | 0.00% |
| 2P | `v044` | Defense Grid | 0.84 | 21.2% | 7.8% | 3.67% | 7.33% | 0.00% |
| 2P | `v043` | Triage | 1.61 | 37.9% | 30.4% | 21.88% | 38.08% | 0.00% |
| 2P | `v044` | Triage | 2.38 | 90.4% | 29.6% | 19.04% | 33.08% | 0.00% |
| 2P | `v043` | Release | 1.65 | 42.7% | 33.3% | 29.17% | 46.17% | 0.00% |
| 2P | `v044` | Release | 1.37 | 36.2% | 26.2% | 21.29% | 35.83% | 0.00% |
| 2P | `v043` | Public Relations | 0.52 | 10.4% | 0.0% | 0.00% | 0.00% | 0.00% |
| 2P | `v044` | Public Relations | 0.40 | 7.7% | 0.0% | 0.00% | 0.00% | 0.00% |

## 3. v0.44.0 Capstone & Breakthrough Telemetry

| Pod | Variant | Def L4 Cash (Total / Per L4 Seat) | Rel L4 Gray Sets (Total / Per L4 Seat) | PR L4 Instant MS (Total / Per L4 Seat / Full +2 %) | Tri L4 Replacements (Taken / Rate %) | PR L3 Scanned Grad (Awarded / Grad %) |
|---|---|---|---|---|---|---|
| 4P | `v043` | $951 / $2.45 | 0 / 0.00 | 0 / 0.00 / 0.0% | 0 / 0.0% | 0 / 0.0% |
| 4P | `v044` | $365 / $1.82 | 2766 / 2.19 | 0 / 0.00 / 0.0% | 1008 / 96.3% | 0 / 0.0% |
| 3P | `v043` | $861 / $2.83 | 0 / 0.00 | 0 / 0.00 / 0.0% | 0 / 0.0% | 0 / 0.0% |
| 3P | `v044` | $294 / $1.87 | 2104 / 2.23 | 0 / 0.00 / 0.0% | 751 / 96.8% | 0 / 0.0% |
| 2P | `v043` | $475 / $2.71 | 0 / 0.00 | 0 / 0.00 / 0.0% | 0 / 0.0% | 0 / 0.0% |
| 2P | `v044` | $151 / $1.72 | 1047 / 2.05 | 0 / 0.00 / 0.0% | 445 / 97.4% | 0 / 0.0% |

**Triage L4 Upgrade Color Breakdown (`v044`):**
- 4P: green: 187, yellow: 821
- 3P: green: 80, yellow: 671
- 2P: green: 30, yellow: 415

## 4. Archetype & Client Company Win Rate Parity

### Bot Archetype Win Rates (%)
| Archetype | 4P v043 | 4P v044 | 3P v043 | 3P v044 | 2P v043 | 2P v044 |
|---|---|---|---|---|---|---|
| AccelerationistBot | 20.42% | 17.50% | 33.33% | 31.11% | 54.17% | 55.42% |
| AdaptiveBalancedBot | 33.96% | 37.29% | 39.72% | 44.17% | 58.96% | 61.04% |
| RecklessSaboteurBot | 9.48% | 13.33% | 18.19% | 22.50% | 36.67% | 38.54% |
| SecOpsTurtleBot | 46.56% | 41.04% | 53.75% | 48.89% | 59.58% | 59.58% |
| VentureGreedBot | 14.58% | 15.83% | 21.67% | 20.00% | 40.62% | 35.42% |

### Client Company Win Rates (%)
| Company | 4P v043 | 4P v044 | 3P v043 | 3P v044 | 2P v043 | 2P v044 |
|---|---|---|---|---|---|---|
| Aegis | 28.30% | 26.93% | 36.44% | 36.78% | 55.53% | 55.53% |
| DTO | 28.96% | 26.13% | 38.93% | 33.39% | 49.75% | 55.64% |
| Helix | 21.26% | 25.52% | 29.73% | 33.80% | 48.57% | 43.33% |
| Meridian | 22.36% | 20.62% | 29.31% | 27.76% | 48.15% | 46.83% |
| Omnidyne | 31.20% | 30.21% | 43.89% | 42.24% | 56.67% | 59.23% |
| Prometheus | 17.90% | 20.46% | 21.56% | 25.64% | 41.93% | 40.24% |

## 5. Outlier Seeds

- **4P `v043`:** Early wipeouts (<=6 rds): 0 (sample: []) | Long stalls (>=13 rds): 0 (sample: [])
- **4P `v044`:** Early wipeouts (<=6 rds): 1 (sample: [176]) | Long stalls (>=13 rds): 0 (sample: [])
- **3P `v043`:** Early wipeouts (<=6 rds): 3 (sample: [279, 634, 1229]) | Long stalls (>=13 rds): 0 (sample: [])
- **3P `v044`:** Early wipeouts (<=6 rds): 3 (sample: [122, 316, 879]) | Long stalls (>=13 rds): 0 (sample: [])
- **2P `v043`:** Early wipeouts (<=6 rds): 18 (sample: [104, 118, 176, 216, 393, 431, 499, 579]) | Long stalls (>=13 rds): 1 (sample: [860])
- **2P `v044`:** Early wipeouts (<=6 rds): 24 (sample: [104, 139, 176, 216, 328, 366, 384, 393]) | Long stalls (>=13 rds): 0 (sample: [])
