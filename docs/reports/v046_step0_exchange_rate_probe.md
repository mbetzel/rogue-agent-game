# v0.46 Step 0: exchange-rate probe (v0.45 engine, 3P)

Command: `python3 scripts/run_v046_exchange_rate_probe.py --games 1200 --seed0 42 --procs 7 --verbose`
1,200 paired games per arm, seeds 42..1241, focal seat = seed % 3. Runtime about 10 s wall.
Raw JSON: `sim_results/v046/exchange_rate_probe.json` (not read).

| arm | win% | dWin (pp) | CI95 (pp) | dMargin | units/game | rounds |
|:---|---:|---:|:---|---:|---:|---:|
| control | 32.9 | 0 | | 0 | 0 | 7.07 |
| money (+$1/round) | 40.7 | +7.8 | [+5.1, +10.6] | +0.86 | 7.00 | 7.04 |
| research (+1 RP/round) | 43.8 | +11.0 | [+7.7, +13.9] | +1.63 | 7.12 | 7.16 |
| secret (+1 start Secret) | 41.5 | +8.6 | [+6.8, +10.6] | +1.17 | 0 | 7.24 |

Units per +1 Secret:

| currency | by win | by margin |
|:---|---:|---:|
| money | 7.70 | 9.56 |
| research | 5.60 | 5.11 |
| mean of four | 7.00 | |

End reasons (control): patient_zero 903, market_collapse 209, singularity 47, total_wipeout 41. Other arms are similar.

## Verdict

Mean 7.00 units per Secret, above the 5.7 threshold, so the rule says: apply the anti-avoid levers first (make the warning faces more rewarding before the main sweep).

## CI caveats

- The CI is not tight enough to decide on its own. The dWin CIs are about +-2.8 pp (money) and +-3.1 pp (research) against a point estimate of 8 to 11 pp. The ratio inherits roughly 20 to 30% relative error per currency, so the mean's plausible range is roughly 5 to 10 (rough propagation, no bootstrap on the ratio itself).
- Money and research disagree (7.7/9.6 vs 5.6/5.1). Research is near the 5 to 5.7 band, money is well above it. Money is the currency a ⚠-avoider gives up, so the money rate is the more relevant one, and it points to "levers needed".
- To resolve the 5.0 vs 5.7 boundary (about 5% relative error) would need roughly 5 to 6x the games (about 6,000 to 7,000 per arm, still only about a minute). That is above the 2x cap, so it was not run. I'd ask first.

---

# Rerun at 6,000 games per arm (cap lifted for this run)

Command: `python3 scripts/run_v046_exchange_rate_probe.py --games 6000 --seed0 42 --procs 7 --out sim_results/v046/exchange_rate_probe_6000.json` (seeds 42..6041, about 45 s). The 1,200-game JSON is kept as `exchange_rate_probe.json`.
Ratio CIs: paired bootstrap over seeds (1,500 resamples, all four arms resampled jointly, every ratio recomputed per resample), not propagated from the dWin/dMargin CIs.

| arm | win% | dWin (pp) [CI95] | dMargin | units/game | rounds |
|:---|---:|:---|---:|---:|---:|
| control | 34.1 | 0 | 0 | 0 | 7.07 |
| money | 41.0 | +6.9 [+5.7, +8.1] | +0.91 | 7.04 | 7.08 |
| research | 44.6 | +10.5 [+9.0, +11.9] | +1.79 | 7.15 | 7.20 |
| secret | 41.0 | +6.9 [+6.0, +7.8] | +1.13 | 0 | 7.23 |

Units per +1 Secret (bootstrap CI95):

| currency | by win | by margin | currency mean |
|:---|:---|:---|:---|
| money | 7.09 [5.84, 8.70] | 8.72 [7.20, 10.87] | 7.90 [6.69, 9.64] |
| research | 4.72 [4.03, 5.52] | 4.52 [3.97, 5.17] | 4.62 [4.05, 5.28] |
| mean of four | | | 6.26 [5.47, 7.32] |

Bootstrap probabilities for the mean of four: P(< 5.0) = 0.000, P(> 5.7) = 0.910.

## Verdict (6,000 games)

Mean 6.26 [5.47, 7.32]: above 5.7 with about 91% bootstrap probability, and below 5.0 essentially never. The rule says apply the anti-avoid levers first. The 1,200-game point estimate (7.00) was inflated by the money arm and research moved down (5.6 to 4.7), so the mean fell, but the conclusion holds.

Money and research still disagree: money 7.9 [6.7, 9.6] vs research 4.6 [4.1, 5.3], with non-overlapping CIs. Money is not worth much to the focal bot per unit (about 8 $ per Secret), research is worth more (about 4.6 per Secret). The "mean of four" is therefore sensitive to the currency mix. If the ⚠ trade-off is mostly paid in money, the case for levers is stronger (the money CI is entirely above 5.7). If paid in research, the +1 premium would be fine (research CI mostly below 5.7, 87% below 5.0). Recommend the game-designer weigh which currency the ⚠ faces actually pay.
