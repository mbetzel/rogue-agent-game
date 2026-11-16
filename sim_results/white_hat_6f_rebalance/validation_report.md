# White Hat 6F Rebalance — Monte Carlo Validation Report

- **Config**: Baseline `GameConfig.v043(white_hat_6f_rebalance=False)` vs. Candidate `GameConfig.v043(white_hat_6f_rebalance=True)`
- **Matrix**: 4P, 3P, 2P pods × 1000 games/pod (seeds `42..1041`), randomized White Hat & Client Company pairings (3000 games/arm, 6000 total).

## 1. Macro Metrics (Pooled & By Pod)

| Scope | Arm | Mean Rounds | Total Wipeout % | Singularity % | Patient Zero % | Market Collapse % | Mean Surv. Secrets |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| All (3,000) | Baseline | 7.56 | 5.6% | 6.9% | 61.3% | 26.2% | 8.44 |
| All (3,000) | Candidate | 7.56 | 5.6% | 6.7% | 61.5% | 26.1% | 8.39 |
| 4P (1000) | Baseline | 7.36 | 2.1% | 4.3% | 74.4% | 19.2% | 7.97 |
| 4P (1000) | Candidate | 7.35 | 2.5% | 3.4% | 73.9% | 20.2% | 7.90 |
| 3P (1000) | Baseline | 7.71 | 4.2% | 8.2% | 66.2% | 21.4% | 8.36 |
| 3P (1000) | Candidate | 7.72 | 4.7% | 7.3% | 66.6% | 21.4% | 8.37 |
| 2P (1000) | Baseline | 7.60 | 10.6% | 8.2% | 43.2% | 38.0% | 9.60 |
| 2P (1000) | Candidate | 7.62 | 9.7% | 9.5% | 44.0% | 36.8% | 9.49 |

## 2. Per-White-Hat Operative Metrics (Pooled Across 2P/3P/4P)

*Note: Mean Stars and Protocol Yields are per game in which the operative appeared.*

| Operative | Arm | Games | Win Rate % | Patient Zero % | Mean ★/Game | Protocol Yield / Game |
| :--- | :--- | ---: | ---: | ---: | ---: | :--- |
| OPERATOR | Baseline | 1552 | 34.5% | 30.0% | 0.50 | 0.00 🔬 |
| OPERATOR | Candidate | 1552 | 32.8% | 30.5% | 0.51 | 1.20 🔬 |
| PHREAKER | Baseline | 1506 | 35.1% | 27.7% | 0.52 | 0.00 extra grads, $0.00 |
| PHREAKER | Candidate | 1506 | 33.4% | 28.4% | 0.52 | 0.43 extra grads, $0.52 |
| ACOUSTIC | Baseline | 1511 | 32.8% | 30.6% | 0.57 | $0.00 |
| ACOUSTIC | Candidate | 1511 | 33.7% | 32.5% | 0.58 | $2.29 |
| SPOOK | Baseline | 1473 | 31.8% | 30.3% | 0.54 | 0.00 burns ($0.00) |
| SPOOK | Candidate | 1473 | 34.9% | 29.9% | 0.54 | 0.53 burns ($0.53) |
| PRODIGY | Baseline | 1469 | 32.0% | 28.3% | 0.53 | 0.00 overrides |
| PRODIGY | Candidate | 1469 | 32.9% | 30.0% | 0.55 | 0.55 overrides |
| CIPHER | Baseline | 1489 | 33.7% | 28.9% | 0.59 | — (parity) |
| CIPHER | Candidate | 1489 | 32.4% | 28.7% | 0.55 | — (parity) |

### Operative Win Rate % By Pod (Baseline → Candidate)

| Operative | 4P Win % | 3P Win % | 2P Win % |
| :--- | ---: | ---: | ---: |
| OPERATOR | 24.7% → 23.0% | 33.7% → 32.8% | 54.8% → 52.0% |
| PHREAKER | 26.4% → 24.1% | 34.7% → 33.7% | 52.2% → 50.7% |
| ACOUSTIC | 24.4% → 27.3% | 33.3% → 33.1% | 50.2% → 48.6% |
| SPOOK | 26.3% → 28.4% | 30.1% → 30.5% | 45.3% → 54.1% |
| PRODIGY | 20.4% → 22.3% | 33.8% → 36.2% | 50.7% → 47.5% |
| CIPHER | 27.5% → 24.7% | 34.3% → 33.7% | 46.2% → 46.8% |

## 3. Client Company Win-Rate Parity Check (Pooled)

| Company | Baseline Win % | Candidate Win % | Delta (pp) | Candidate PZ % |
| :--- | ---: | ---: | ---: | ---: |
| MERIDIAN | 30.1% | 29.4% | -0.7 | 42.3% |
| OMNIDYNE | 41.2% | 41.4% | +0.2 | 25.5% |
| AEGIS | 37.4% | 38.9% | +1.5 | 22.3% |
| DTO | 37.3% | 38.0% | +0.7 | 21.8% |
| HELIX | 29.9% | 29.4% | -0.5 | 28.6% |
| PROMETHEUS | 24.3% | 23.1% | -1.2 | 40.0% |

## 4. Outlier Seeds

- **Baseline**: Shortest `2P seed=236` (1 rounds, `patient_zero`); Longest `2P seed=860` (13 rounds, `singularity`); Sample wipeout seeds: `[52, 77, 105, 226, 267, 274, 354, 403, 433, 470]`
- **Candidate**: Shortest `2P seed=236` (1 rounds, `patient_zero`); Longest `2P seed=860` (13 rounds, `singularity`); Sample wipeout seeds: `[52, 62, 77, 105, 198, 226, 274, 338, 354, 395]`
