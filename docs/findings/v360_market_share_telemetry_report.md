# Rogue Agent v0.36.0 Telemetry Sweep Report
## Phase 45: Market Share, Market Collapse, Public Relations Track, Marketing ★ Variants, Free-Choice Generic Shields

**Date:** 2026-11-06
**Author:** Product Owner
**Target version:** `GameConfig.v036()` (uncommitted, staff-approved). Baseline: `GameConfig()` (v0.35.0 defaults) on the same seeds.
**Spec:** [`v360_market_share_red_rework_spec.md`](../specs/v360_market_share_red_rework_spec.md) §6 / §8. Guardrails: [design plan §6](../explorations/2026_11_market_share_red_rework_plan.md).
**Script:** `scripts/run_v360_market_share_sweep.py --seed 42 --workers 7` (unchanged; run as is).
**Matches:** the full §8 size. No cells were reduced.
- C0 `V035` and C1 `V036`: 3,000 per pod (2P / 3P / 4P).
- Each of the 11 secondary cells: 1,000 per pod.
- Total: 51,000 matches.

**Seeds:** base `42`. Match seed = `42 + n × 100000 + idx`. That gives 2P = 200042–203041, 3P = 300042–303041 and 4P = 400042–403041 for C0/C1. The secondary cells use the first 1,000 seeds of each range. Every cell uses the same seeds (paired).
**Runtime:** 60 s wall time for the whole sweep on 7 worker processes. Throughput is about 850 matches/s.
**Raw data:**
- `sim_results/v360_market_share_sweep.json`: every cell and pod, plus the script's guardrail flags.
- `sim_results/v360_market_share_sweep_stdout.txt`: console summary.
- `sim_results/v360_market_share_outlier_seeds.json`: complete outlier seed lists for V035 / V036 / KAMIKAZE.
  - I made this file with a read-only re-run that imports `build_engine` from the sweep script.
  - The script itself truncates its seed log to 50 seeds and logs only Total Wipeouts of ≤ 5 rounds.
  - The re-run reproduced the sweep's mean rounds exactly in every pod (deterministic).

**Match setup** follows spec §8 and `run_v360_red_rebalance_sweep.build_engine`:
- 5-bot rotation `(idx × n + i) % 5`, shuffled into seats.
- `get_random_setup(rng, "STANDARD")`, `get_random_companies` and `get_random_white_hats`.
- `starting_money=6`, 3 Gray + 1 Purple die, 1 Purple in the Personal Reserve, `enable_corporate_asymmetry=True`.

All telemetry comes from engine fields (`EndGameResult`, `RoundTelemetry`). There are no monkeypatched hooks.

**Notes on metric definitions** (spec §6.3):
- **Three-way split:** Total Wipeout is counted inside Patient Zero. It is also reported separately.
- **Red block rate:** (color + Generic blocks) / incoming Red. It covers Phase-4 resolutions of non-Patient-Zero players and excludes Compile Buffer Overflow rounds.
- **Red purchase share:** Red buys / all Central Market buys (Red, Blue, Green, Yellow). It excludes Triage L3 swaps.
- **Regain share:** 🔬 spent on Phase-6 Market Share regain / (🔬 spent on tracks + regain).
- **Maxed-track share:** the share of all L4 track levels at game end that belong to each track. Engine key `PATENT` is the Cryptographic Patents Track under V035 and the Public Relations Track under V036.
- **Collapser led in Secrets:** the share of games with a Market Collapse in which at least one player who hit 0 had the most Secrets among survivors at that moment. **Ties for the lead count as leading** (`market_share.py:183`).
- **Company spread:** max − min company win rate. Shared wins are split.
- **Tiebreak attribution:** the engine's `tiebreak_decided_by` keys are mapped to glossary terms. Engine key `patches` is Research Tokens and `unpatched_dice_count` is fewest dice Under Development. These engine keys use deprecated terminology. I am only flagging this; I have not changed anything.

---

### 1. Guardrail table: C1 `V036` vs C0 `V035` (plan §6 / spec §8)

95% Wilson CIs are in brackets. The 95% CI half-width on mean rounds is about ±0.05 in every pod. ✅ = pass, ❌ = fail, ⚖ = the designer judges (no numeric threshold).

| Guardrail | Target | 2P V036 | 3P V036 | 4P V036 | V035 (2P / 3P / 4P) |
|---|---|---|---|---|---|
| Patient Zero share (incl. Total Wipeout) | 25–40% | **43.4% [41.7–45.2] ❌** | **41.4% [39.7–43.2] ❌** | **41.6% [39.9–43.4] ❌** | 58.3% / 64.3% / 68.5% |
| Singularity share | 25–40% | 37.0% [35.3–38.7] ✅ | 38.5% [36.8–40.3] ✅ | 36.8% [35.1–38.5] ✅ | 41.7% / 35.7% / 31.5% |
| Market Collapse share | 25–40% | **19.6% [18.2–21.0] ❌** | **20.1% [18.7–21.5] ❌** | **21.6% [20.2–23.1] ❌** | 0 / 0 / 0 |
| No setup (v3.0 card, company@seat, White Hat@seat) has any trigger > ~55% | ≤ 55% | max 46.6% ✅ | max 46.2% ✅ | max 45.9% ✅ | max 61.3% / 69.1% / 73.6% |
| Mean rounds | 8.4–9.0 | 8.64 ✅ | 8.77 ✅ | 8.77 ✅ | 8.87 / 8.71 / 8.59 |
| Total Wipeout | ≤ C0 (2P ≤ 16%) | 5.8% [5.1–6.7] ✅ | 1.3% [1.0–1.8] ✅ | 0.2% [0.1–0.4] ✅ | 16.0% / 5.8% / 1.9% |
| Red block rate | clearly above C0 (~10%) | 15.1% (+4.7 pts) ⚖ | 14.4% (+4.0 pts) ⚖ | 14.5% (+3.7 pts) ⚖ | 10.4% / 10.4% / 10.8% |
| Red share of market buys | rises, ≤ ~35% | 26.1% (+11.4 pts) ✅ | 25.7% (+11.9 pts) ✅ | 26.7% (+12.5 pts) ✅ | 14.6% / 13.8% / 14.1% |
| Version-comparison any-tie rate, v1.0 | well below ~50% | **65.0% ❌** | **83.6% ❌** | **76.4% ❌** | n/a |
| Version-comparison any-tie rate, v2.0 | well below ~50% | 38.2% ⚖ (below 50%) | **57.4% ❌** | **55.1% ❌** | n/a |
| Regain share of research spend | 20–40% | 37.1% ✅ | 35.0% ✅ | 34.0% ✅ | 0 (no regain) |
| No track > ~50% of maxed tracks | ≤ 50% | **Public Relations 61.5% ❌** | **61.1% ❌** | **59.7% ❌** | Patents 59.3% / 59.8% / 59.2% |
| Company win-rate spread | ≤ C0 (~15 pts) | 12.3 ✅ | **17.5 ❌** (C0 16.2) | **19.5 ❌** (C0 14.3) | 13.8 / 16.2 / 14.3 |
| Market buys per seat: C1 ≤ 1.2 × T4 `NO_PAYOUT` | ≤ 1.2× | 2.04 vs 2.09 = 0.97× ✅ | 2.28 vs 2.33 = 0.98× ✅ | 2.41 vs 2.47 = 0.98× ✅ | — |
| Market buys per seat vs C0 | reported | 2.04 vs 1.13 (**+81%**) | 2.28 vs 1.20 (**+90%**) | 2.41 vs 1.20 (**+100%**) | 1.13 / 1.20 / 1.20 |
| Mean end Money vs C0 | reported | $2.50 vs $0.43 | $2.41 vs $0.49 | $2.40 vs $0.55 | — |

**Summary:** in every pod, V036 passes the guardrails for rounds, Total Wipeout, Red purchase share, regain share, setup concentration and payout-driven buy inflation (C1 vs T4).

V036 fails these guardrails in every pod:
- The end-reason split: Patient Zero is just above 40% and Market Collapse is at about 20%, against the 25% floor.
- The v1.0 comparison tie rate.
- Maxed-track concentration (Public Relations about 60%). This is carried over from V035 Patents at about 59%.

It also fails these in some pods:
- The v2.0 tie rate (3P and 4P).
- Company spread (3P and 4P).

The Red block rate rose by +3.7 to +4.7 pts. Whether that is "clearly above" is for the game-designer to judge.

Market buys roughly doubled vs V035. The NO_PAYOUT cell buys about as much as V036, so the bank payouts are not what drives this. The script's `purchases_le_1_2x_no_payout` flag passes.

---

### 2. End reasons and setup splits (V036)

Raw end reasons:

| Pod | Patient Zero | Total Wipeout | Singularity | Market Collapse | Games with any Collapse | Multi-trigger games |
|---|---|---|---|---|---|---|
| 2P | 37.6% | 5.8% | 37.0% | 19.6% | 22.5% | 11.2% (V035 18.6%) |
| 3P | 40.1% | 1.3% | 38.5% | 20.1% | 24.1% | 7.1% (V035 9.3%) |
| 4P | 41.5% | 0.2% | 36.8% | 21.6% | 26.1% | 6.6% (V035 5.0%) |

"Games with any Collapse" also counts Collapses that land in the same Phase 4 as, or after, a Patient Zero trigger (E8/E9), where `end_reason` stays Patient Zero.

**By v3.0 Version card**, as PZ / Singularity / Collapse:

| Pod | CORRUPTED_KERNEL | ZERO_DAY_OVERRIDE |
|---|---|---|
| 2P | 45.8 / 34.5 / 19.7 (n=1489) | 41.1 / 39.4 / 19.5 (n=1511) |
| 3P | 43.9 / 36.8 / 19.4 (n=1507) | 39.0 / 40.3 / 20.8 (n=1493) |
| 4P | 43.9 / 35.1 / 20.9 (n=1518) | 39.3 / 38.5 / 22.3 (n=1482) |

Only two v3.0 cards appear in the STANDARD setup draw.

**Highest single-trigger rate by company@seat and White Hat@seat** (all are Patient Zero; n ≈ 460–530 per bucket):
- 2P: HELIX@1 46.2%, PHREAKER@0 46.6%.
- 3P: AEGIS@2 45.8%, ACOUSTIC@1 / ACOUSTIC@2 46.2%.
- 4P: OMNIDYNE@3 45.9%, CIPHER@3 45.3%.

No V036 setup has any trigger above 55%. The highest is 46.6%, down from 61–74% for Patient Zero under V035. The highest Market Collapse rate for any setup is 22.7% in 2P (PRODIGY@0), 24.9% in 3P (DTO@0) and 24.2% in 4P (DTO@1). Per-bucket rates for all three setup keys are in the JSON under `by_setup`.

---

### 3. Pacing and outlier seeds

| Pod | V035 mean / median / sd | V036 mean / median / sd | V035 games ≤ 5 rounds | V036 games ≤ 5 rounds | ≥ 12 rounds |
|---|---|---|---|---|---|
| 2P | 8.87 / 9 / 1.33 | 8.64 / 9 / 1.49 | 67 (2.2%) | **145 (4.8%)** | none |
| 3P | 8.71 / 9 / 1.42 | 8.77 / 9 / 1.36 | 76 (2.5%) | 74 (2.5%) | V036: 1 (`302640`) |
| 4P | 8.59 / 9 / 1.46 | 8.77 / 9 / 1.31 | 106 (3.5%) | 58 (1.9%) | none |

- **Market Collapse in ≤ 5 rounds:** none in any pod or cell. Rounds to the first Collapse: mean 8.73–8.75, p10 8, p50 9, p90 10 in every pod.
- **Total Wipeouts (V036):** 175 / 40 / 5 games (2P / 3P / 4P), against V035's 481 / 173 / 57. Total Wipeouts in ≤ 5 rounds:
  - V036: one game, 2P seed `200636`.
  - V035: 2P `200205`, `200376`, `202142`, `202400`, `202737`.
- **Short-game examples (V036 ≤ 5 rounds):**
  - 2P: `200043`, `200052`, `200083`, `200100`, `200135`.
  - 3P: `300076`, `300099`, `300116`, `300149`, `300232`.
  - 4P: `400165`, `400192`, `400253`, `400276`, `400325`.
- 2P short games roughly doubled vs V035 (2.2% → 4.8%). In 3P and 4P they stayed level or fell.
- Full seed lists (every Total Wipeout, ≤ 5 and ≥ 12 rounds) are in `sim_results/v360_market_share_outlier_seeds.json`.

---

### 4. Market Share curves (V036, after Phase 6)

Mean (p10 / p50 / p90) over surviving seats. n = seat-rounds still in play. The start values are 19 / 20 / 20.

| Round | 2P | 3P | 4P |
|---|---|---|---|
| 1 | 18.5 (18/19/19) | 19.5 (19/20/20) | 19.5 (19/20/20) |
| 2 | 18.0 (16/18/19) | 19.0 (17/19/20) | 19.0 (17/19/20) |
| 3 | 17.2 (15/18/19) | 18.2 (16/19/20) | 18.2 (16/18/20) |
| 4 | 16.2 (13/17/19) | 17.1 (14/18/20) | 17.1 (14/17/20) |
| 5 | 15.3 (11/16/18) | 16.2 (12/17/19) | 16.1 (12/17/19) |
| 6 | 13.9 (9/14/18) | 14.8 (10/15/19) | 14.8 (10/15/19) |
| 7 | 11.5 (5/12/17) | 12.3 (6/13/18) | 12.3 (6/13/18) |
| 8 | 8.3 (1/8/15) | 9.0 (2/9/16) | 9.1 (2/9/15) |
| 9 | 6.1 (0/6/12) | 6.8 (1/7/13) | 6.8 (1/7/13) |
| 10 | 6.0 (1/6/12), n=1848 | 6.7 (1/6/13), n=2910 | 6.3 (1/6/12), n=3740 |
| 11 | 5.7 (2/5/11), n=316 | 6.2 (2/6/12), n=465 | 6.3 (2/6/11), n=560 |

The loss rate is about 1 per round through Round 5. It steepens to about 2.5–3.3 per round in Rounds 7–8.

Red per seat per game (V036 / V035):
- Incoming: 16.8 / 17.6 (2P), 17.3 / 17.2 (3P), 17.3 / 16.9 (4P).
- Market Share lost per seat (V036): 13.9 / 14.5 / 14.6.
- Overflow below 0: 0.35 / 0.28 / 0.25.
- Generic (`Any`) shields made 93–94% of Red blocks in both configs.

**Final Market Share by finishing rank** (mean; p10/p50/p90 in brackets):

| Pod | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| 2P | 6.9 (0/6/14) | 6.6 (0/6/14) | | |
| 3P | 7.3 (1/7/15) | 7.1 (0/7/15) | 6.9 (0/6/15) | |
| 4P | 7.2 (1/7/15) | 7.1 (1/6/15) | 7.1 (1/6/15) | 6.7 (0/6/15) |

**Tiebreak attribution, V036** (V035 in brackets):

| Pod | Secrets | Sole survivor | Market Share | Money | Ready colored dice | Research Tokens | Fewest Under Development | Shared |
|---|---|---|---|---|---|---|---|---|
| 2P | 44.3% (32.5%) | 40.1% (44.9%) | 10.5% | 3.8% (3.1%) | 0.4% (4.6%) | 0.6% (9.1%) | 0.2% (4.2%) | 0.1% (1.6%) |
| 3P | 75.4% (66.7%) | 2.7% (16.9%) | 16.4% | 4.0% (4.4%) | 1.0% (4.9%) | 0.3% (4.1%) | 0.2% (2.2%) | 0.1% (0.8%) |
| 4P | 73.5% (76.5%) | 0.8% (7.3%) | 18.9% | 5.3% (5.2%) | 1.0% (5.8%) | 0.3% (2.9%) | 0.1% (1.8%) | 0.2% (0.6%) |

---

### 5. Version comparisons (V036)

Totals over 3,000 games per pod. "Gained" is the bank payout to the top place(s). "Paid" is what the bottom place(s) actually paid the bank. "Forgiven" is the shortfall that was waived.

| Pod | Version | Events/game | Gained | Paid | Forgiven | Forgiven share of charges | All tied | Top tie | Bottom tie | Any tie |
|---|---|---|---|---|---|---|---|---|---|---|
| 2P | v1.0 ($2) | 1.000 | 2,098 | 1,800 | 298 | 14.2% | 65.0% | – | – | 65.0% |
| 2P | v2.0 ($4) | 0.916 | 6,792 | 3,344 | 3,448 | 50.8% | 38.2% | – | – | 38.2% |
| 3P | v1.0 | 1.000 | 5,018 | 3,821 | 613 | 13.8% | 42.0% | 25.7% | 15.9% | 83.6% |
| 3P | v2.0 | 0.937 | 12,428 | 5,682 | 6,342 | 52.7% | 13.3% | 23.8% | 20.2% | 57.4% |
| 4P | v1.0 | 1.000 | 7,192 | 5,247 | 813 | 13.4% | 31.3% | 33.8% | 23.7% | 76.4% |
| 4P | v2.0 | 0.943 | 15,192 | 7,391 | 7,833 | 51.5% | 5.0% | 30.5% | 29.1% | 55.1% |

In 2P, top and bottom ties are the same thing as all-tied, so they are not listed separately. "Forgiven share" is forgiven / (paid + forgiven).

- **Net bank Money injected per seat per game** (comparisons only): $0.62 / $0.88 / $0.81 (2P / 3P / 4P).
- **Double version fills** (v1.0 and v2.0 in one compile): 0 in every cell.
- **Comparisons during spillover:** 0%.

---

### 6. Economy, purchases, research

Purchases per seat per game, V036 (V035 in brackets):

| Pod | Red | Blue | Green | Yellow | Total market |
|---|---|---|---|---|---|
| 2P | 0.53 (0.17) | 0.79 (0.49) | 0.07 (0.03) | 0.64 (0.44) | 2.04 (1.13) |
| 3P | 0.59 (0.17) | 0.80 (0.46) | 0.07 (0.04) | 0.82 (0.54) | 2.28 (1.20) |
| 4P | 0.64 (0.17) | 0.75 (0.43) | 0.07 (0.04) | 0.94 (0.57) | 2.41 (1.20) |

End Money, V036: mean $2.50 / $2.41 / $2.40; p50 $2 and p90 $6 in every pod. V035 was mean $0.43–$0.55 with p50 $0 and p90 $2.

**Research and maxed tracks:**
- Regain steps per seat per game: 1.68 / 1.63 / 1.61.
- Share of L4 track levels (2P / 3P / 4P):
  - Public Relations: 61.5 / 61.1 / 59.7%.
  - Release: 30.2 / 30.5 / 32.4%.
  - Triage: 5.7 / 5.6 / 5.6%.
  - Defense Grid: 2.6 / 2.8 / 2.4%.

**Red ★ card usage:**
- *Ad Campaign* (R2) uses per seat per game: 0.002 / 0.003 / 0.003. This is about 1 use per 300–500 seats.
- *Customer Poaching* (R3) Market Share moved per game: 0.027 / 0.041 / 0.050.

Both are close to zero. I did not check how often the Red ★ set is in the market in these setups.

**Company win rates, V036** (V035 in brackets):

| Company | 2P | 3P | 4P |
|---|---|---|---|
| AEGIS | 53.1% (53.5%) | 41.1% (34.9%) | 32.3% (27.9%) |
| DTO | 57.6% (58.3%) | 44.7% (42.9%) | 37.7% (34.8%) |
| HELIX | 46.4% (45.9%) | 27.2% (30.9%) | 18.9% (21.2%) |
| MERIDIAN | 52.0% (49.6%) | 32.7% (32.2%) | 24.2% (21.9%) |
| OMNIDYNE | 45.2% (48.8%) | 27.2% (32.3%) | 18.8% (23.9%) |
| PROMETHEUS | 46.2% (44.5%) | 27.3% (26.7%) | 18.3% (20.5%) |
| **Spread (pts)** | 12.3 (13.8) | 17.5 (16.2) | 19.5 (14.3) |

---

### 7. Kamikaze signal

The metric is the share of Collapse games in which a collapsing player was tied for or held the Secrets lead.

| Cell | 2P | 3P | 4P |
|---|---|---|---|
| V036 | 74.2% | 65.3% | 60.3% |
| KAMIKAZE (RecklessSaboteur `collapse_seeking=True`) | 75.5% | 64.4% | 65.4% |
| TIERS (fixed 4-tier Generic shields) | 90.5% | 81.2% | 83.8% |
| NAIVE | 65.9% | 60.7% | 50.6% |

- The metric counts ties for the lead as leading. In 2P, Secrets are often tied, which pushes the number up.
- The KAMIKAZE cell's end-reason split, rounds and Collapse rate are within about 1–2 pts of V036 in every pod. Turning on collapse-seeking for the RecklessSaboteur seat made no measurable difference to how often or when Collapse happens.

---

### 8. Secondary cells (all v036 + the stated change; n = 1,000 per pod)

PZ includes Total Wipeout. "3-way OK" means all three triggers are inside 25–40%. "PR max" is the Public Relations share of maxed tracks. "Spread" is the company spread in pts.

| Cell | Pod | PZ | Sing | MC | 3-way OK | TW | Rounds | Red block | Red buy share | Buys/seat | Regain share | PR max | Spread | End $ | Any-tie v1.0 / v2.0 | Collapser led |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4-RATE | 2P | 42.5% | 37.5% | 20.0% | no | 5.7% | 8.71 | 15.3% | 25.6% | 2.06 | 36.5% | 61.6% | 9.5 | 2.53 | 65.4 / 39.9% | 75.9% |
| L4-RATE | 3P | 41.6% | 37.5% | 20.9% | no | 1.0% | 8.76 | 13.9% | 24.9% | 2.28 | 35.1% | 60.4% | 20.3 | 2.44 | 83.8 / 55.3% | 65.6% |
| L4-RATE | 4P | 40.2% | 39.0% | 20.8% | no | 0.1% | 8.85 | 14.6% | 26.1% | 2.43 | 34.0% | 60.0% | 20.0 | 2.37 | 76.4 / 53.4% | 67.6% |
| L4-BOTH | 2P | 42.7% | 37.6% | 19.7% | no | 5.6% | 8.71 | 15.2% | 25.5% | 2.05 | 37.1% | 61.7% | 9.2 | 2.54 | 65.5 / 40.2% | 76.5% |
| L4-BOTH | 3P | 41.7% | 37.9% | 20.4% | no | 1.0% | 8.76 | 13.9% | 24.8% | 2.28 | 35.7% | 60.4% | 20.1 | 2.43 | 83.9 / 56.8% | 67.1% |
| L4-BOTH | 4P | 40.1% | 39.6% | 20.3% | no | 0.1% | 8.86 | 14.6% | 25.8% | 2.42 | 34.6% | 60.0% | 19.7 | 2.36 | 76.7 / 53.0% | 67.9% |
| PAYOUT-LOW ($1/$2) | 2P | 39.3% | 37.8% | 22.9% | no | 4.9% | 8.72 | 13.7% | 24.2% | 1.96 | 36.6% | 62.8% | 10.5 | 2.44 | 65.0 / 35.1% | 75.9% |
| PAYOUT-LOW | 3P | 40.0% | 37.4% | 22.6% | no | 1.0% | 8.77 | 12.2% | 23.2% | 2.18 | 35.4% | 60.7% | 23.9 | 2.22 | 84.0 / 58.7% | 66.9% |
| PAYOUT-LOW | 4P | 39.7% | 38.0% | 22.3% | no | 0.3% | 8.81 | 13.1% | 24.7% | 2.31 | 34.3% | 59.9% | 20.6 | 2.27 | 76.7 / 56.3% | 64.2% |
| PAYOUT-HIGH ($3/$6) | 2P | 43.8% | 36.9% | 19.3% | no | 5.8% | 8.60 | 17.3% | 27.3% | 2.13 | 35.2% | 61.2% | 12.5 | 2.67 | 70.3 / 37.0% | 71.0% |
| PAYOUT-HIGH | 3P | 45.0% | 35.2% | 19.8% | no | 0.9% | 8.65 | 16.4% | 27.0% | 2.38 | 33.5% | 60.5% | 18.5 | 2.60 | 87.2 / 59.8% | 57.6% |
| PAYOUT-HIGH | 4P | 43.7% | 34.2% | 22.1% | no | 0.2% | 8.77 | 17.0% | 28.0% | 2.55 | 32.8% | 58.9% | 15.5 | 2.58 | 79.7 / 54.1% | 60.4% |
| NO_PAYOUT | 2P | 35.6% | 38.4% | 26.0% | **yes** | 4.5% | 8.67 | 13.3% | 26.2% | 2.09 | 21.3% | 61.2% | 12.0 | 2.52 | – | 73.8% |
| NO_PAYOUT | 3P | 37.0% | 35.6% | 27.4% | **yes** | 0.9% | 8.75 | 11.7% | 24.1% | 2.33 | 20.8% | 60.9% | 20.3 | 2.41 | – | 72.1% |
| NO_PAYOUT | 4P | 35.2% | 36.8% | 28.0% | **yes** | 0.4% | 8.85 | 12.5% | 25.4% | 2.47 | 20.9% | 60.5% | 18.8 | 2.31 | – | 65.1% |
| MS-2 (17/18/18) | 2P | 42.3% | 30.9% | 26.8% | no | 5.7% | 8.56 | 16.2% | 27.4% | 2.07 | 37.4% | 62.4% | 15.4 | 2.51 | 65.0 / 36.9% | 75.5% |
| MS-2 | 3P | 40.9% | 29.1% | 30.0% | no | 1.1% | 8.59 | 14.8% | 26.3% | 2.28 | 35.8% | 60.8% | 20.5 | 2.38 | 84.0 / 56.9% | 65.8% |
| MS-2 | 4P | 38.4% | 31.1% | 30.5% | **yes** | 0.2% | 8.69 | 15.5% | 27.1% | 2.41 | 35.2% | 60.2% | 19.1 | 2.36 | 76.7 / 55.4% | 61.5% |
| MS+2 (21/22/22) | 2P | 43.5% | 42.9% | 13.6% | no | 5.7% | 8.78 | 14.6% | 25.2% | 2.04 | 36.0% | 61.8% | 7.7 | 2.56 | 65.0 / 37.6% | 74.4% |
| MS+2 | 3P | 43.7% | 42.5% | 13.8% | no | 1.2% | 8.82 | 13.4% | 24.2% | 2.26 | 34.2% | 60.1% | 19.9 | 2.42 | 84.0 / 56.8% | 54.6% |
| MS+2 | 4P | 40.6% | 43.5% | 15.9% | no | 0.1% | 8.93 | 14.0% | 25.4% | 2.40 | 33.5% | 60.1% | 17.0 | 2.37 | 76.7 / 55.0% | 58.6% |
| NAIVE | 2P | 37.1% | 36.3% | 26.6% | **yes** | 3.7% | 8.68 | 17.3% | 19.3% | 1.94 | 17.5% | 61.1% | 11.1 | 3.20 | 54.8 / 26.4% | 65.9% |
| NAIVE | 3P | 37.2% | 35.3% | 27.5% | **yes** | 1.1% | 8.70 | 15.7% | 18.0% | 2.14 | 16.7% | 61.4% | 14.8 | 3.03 | 87.2 / 54.7% | 60.7% |
| NAIVE | 4P | 35.4% | 36.4% | 28.2% | **yes** | 0.2% | 8.81 | 16.8% | 19.4% | 2.29 | 17.2% | 60.9% | 15.7 | 2.95 | 87.5 / 53.6% | 50.6% |
| RANDOM_FOCUS | 2P | 42.0% | 38.1% | 19.9% | no | 4.9% | 8.72 | 15.6% | 28.4% | 2.10 | 35.4% | 18.6% | 13.1 | 2.63 | 65.1 / 37.7% | 72.0% |
| RANDOM_FOCUS | 3P | 39.2% | 38.3% | 22.5% | no | 0.9% | 8.82 | 14.7% | 28.9% | 2.36 | 33.2% | 18.8% | 19.7 | 2.53 | 75.9 / 50.5% | 56.1% |
| RANDOM_FOCUS | 4P | 37.5% | 38.2% | 24.3% | no | 0.1% | 8.89 | 14.5% | 29.6% | 2.51 | 31.9% | 18.7% | 19.9 | 2.44 | 67.1 / 45.0% | 47.5% |
| KAMIKAZE | 2P | 43.2% | 36.9% | 19.9% | no | 5.8% | 8.69 | 15.2% | 25.9% | 2.05 | 36.7% | 61.5% | 9.2 | 2.54 | 65.0 / 37.6% | 75.5% |
| KAMIKAZE | 3P | 42.2% | 36.5% | 21.3% | no | 1.0% | 8.73 | 13.9% | 25.1% | 2.27 | 35.1% | 60.4% | 17.2 | 2.40 | 84.0 / 56.9% | 64.4% |
| KAMIKAZE | 4P | 39.9% | 38.2% | 21.9% | no | 0.1% | 8.84 | 14.6% | 26.3% | 2.42 | 34.3% | 60.1% | 18.8 | 2.34 | 76.7 / 55.3% | 65.4% |
| TIERS | 2P | 39.6% | 32.2% | 28.2% | **yes** | 5.5% | 8.62 | **7.2%** | 26.4% | 2.12 | 38.7% | 63.2% | 7.4 | 2.54 | 62.0 / 36.6% | 90.5% |
| TIERS | 3P | 39.3% | 33.4% | 27.3% | **yes** | 0.9% | 8.67 | **6.2%** | 25.6% | 2.36 | 38.0% | 62.8% | 19.9 | 2.41 | 87.5 / 61.2% | 81.2% |
| TIERS | 4P | 36.8% | 35.2% | 28.0% | **yes** | 0.1% | 8.79 | **6.7%** | 26.2% | 2.51 | 37.1% | 61.1% | 15.4 | 2.35 | 81.1 / 58.4% | 83.8% |

Paired seeds (no interpretation):
- **Three-way split in band in all three pods:** NO_PAYOUT, NAIVE and TIERS. MS-2 is in band in 4P only.
- **TIERS:** the Red block rate falls to 6.2–7.2%, which is below V035's ~10.4%.
- **RANDOM_FOCUS:** the only cell where Public Relations is under 50% of maxed tracks (about 19%).
- **NO_PAYOUT and NAIVE:** regain share falls to about 21% and about 17%. NAIVE's 16.7–17.5% is below the 20% floor.
- **Setup concentration:** the highest single-setup trigger rate in any secondary cell is 54.9% (PAYOUT-HIGH 3P). It is below 55% in every cell.
- **Larger samples:** the secondary cells have 1,000 games per pod. Their three-way split CIs are about ±3 pts, against about ±1.7 pts for C0/C1.
