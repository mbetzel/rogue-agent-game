# Rogue Agent v0.35.0 Telemetry Sweep Report
## Phase 43: Research Track Rebalance (5-level tracks, Breakthroughs, flat company setup)

**Date:** 2026-11-06
**Author:** Product Owner
**Target version:** `v0.35.0` (uncommitted, staff-approved). Measured against `GameConfig.legacy_v034()` on the same seeds.
**Matches:** 18,000. That is 3,000 per pod (2P / 3P / 4P) for each config, or 27,000 player-games per config.
**Seeds:** base seed `42`. Match seed = `42 + num_players*100000 + match_idx`: 2P = 200042–203041, 3P = 300042–303041, 4P = 400042–403041. Both configs use the same seeds.
**Runtime:** about 64 s in total.
**Script:** `scripts/run_v350_telemetry_sweep.py`. Replay a seed with `--replay <seed> --players <n> --cfg v035|v034`.
**Raw data:** [v350_telemetry_summary.json](./v350_telemetry_summary.json)

**Match setup** is the same as `run_v340_telemetry_sweep.py`:
- 5-bot rotation, shuffled into seats.
- `get_random_setup` STANDARD.
- Random Client Companies and White Hat Operatives.
- `starting_money=6`, 3 Gray + 1 Purple dice, 1 Purple in the Personal Reserve, `enable_corporate_asymmetry=True`.

All metrics come from the engine's native v0.35 ledger in `EndGameResult.rankings`. The script installs no wrappers and changes no engine code.

**Metric definitions:**
- **Win:** the player ranked 1st. A Total Wipeout's top-ranked player counts as the winner, and tied winners share the win.
- **Purple lost:** (starter die + the reserve die if drawn) − Purple dice owned at game end. Under v0.34 the reserve die is drawn by buying it. Under v0.35 it comes from the Patents L3 Breakthrough.

**Baseline note:** the v0.34 numbers here come from `legacy_v034()` with the current bots. They differ a little from `v340_telemetry_sweep_report.md`, for example 2P mean rounds 8.21 vs 8.30 and DTO 2P win rate 88% vs 76%. This report uses the same-seed `legacy_v034()` run as the comparison. I did not trace the cause of the gap.

---

### 1. Guardrails (plan §4 + v0.34 D5)

| Guardrail | Target | 2P v0.35 | 3P v0.35 | 4P v0.35 | v0.34 (2P / 3P / 4P) |
|---|---|---|---|---|---|
| Mean / median rounds | 8–11 | 8.87 / 9 ✅ | 8.71 / 9 ✅ | 8.59 / 9 ✅ | 8.21 / 7.85 / 7.66 (3P and 4P fail) |
| Singularity ending | ≤ 45% (2P ~45% accepted) | 41.7% ✅ | 35.7% ✅ | 31.5% ✅ | 23.8% / 17.9% / 14.9% |
| Total Wipeout ending | ≤ 15% | **16.0% ❌** | 5.8% ✅ | 1.9% ✅ | 16.5% / 5.8% / 2.3% |
| Patient Zero ending (end reason) | Informational | 42.3% | 58.6% | 66.6% | 59.7% / 76.3% / 82.8% |
| Bot win-rate spread | ≤ 45 pts | 20.0 ✅ | 31.5 ✅ | 36.1 ✅ | 32.8 / 32.2 / 25.5 |
| 🔬 earned per player | 12–14 | 11.98 (median 11) ⚠ | 11.84 ⚠ | 11.82 ⚠ | 3.86 / 3.77 / 3.79 |
| No seat maxes all tracks | 0 | 0 ✅ | 0 ✅ | 0 ✅ | — |
| One track ≤ ~50% of maxed tracks | ≤ 50% | **Patents 59.3% ❌** | **59.8% ❌** | **59.2% ❌** | — |

- 2P Total Wipeout stays just over the limit. It is 0.5 pts better than v0.34 and is a carried-forward issue.
- 🔬 per player is just under the 12 target at every player count. The p10–p90 range is 5–21 in every pod.
- The 4P short-game watch item is fixed: 4P mean rounds went from 7.66 to 8.59.

### 2. Pacing and outliers

- Rounds range from 4 to 11 in 2P and 3P, and from 3 to 11 in 4P.
- No game hit the round limit, ran 14 or more rounds (so none reached 20+), or ended in a round-2 Total Wipeout.
- Games of 3 rounds or fewer:
  - v0.35: 1 game (4P seed `402281`).
  - v0.34: 46 games (9 / 13 / 24). Examples: seeds `200295`, `300076`, `400242`.

### 3. Win rates

**Bots (v0.35, 2P / 3P / 4P):**

| Bot | 2P | 3P | 4P |
|---|---|---|---|
| Accelerationist | 61.8% | 49.6% | 44.1% |
| Venture Greed | 54.9% | 47.2% | 41.3% |
| Reckless Saboteur | 49.6% | 32.7% | 22.4% |
| SecOps Turtle | 42.0% | 19.2% | 9.1% |
| Adaptive Balanced | 41.7% | 18.0% | 8.0% |

In v0.34, Adaptive Balanced was the strongest bot at 3P and 4P (47% / 37%) and Venture Greed was the weakest (12–31%). v0.35 reverses that order. Adaptive Balanced and SecOps Turtle now trail at 4P.

**Client Companies (win rate / survival rate):**

| Company | 2P v0.35 | 3P v0.35 | 4P v0.35 | v0.34 (2P / 3P / 4P win) |
|---|---|---|---|---|
| DTO | **58.3%** / 70% | **42.9%** / 78% | **34.8%** / 82% | 88.3% / 80.0% / 75.4% |
| Aegis | 53.5% | 34.9% | 27.9% | 28.9% / 14.5% / 8.4% |
| Meridian | 49.6% | 32.2% | 21.9% | 54.2% / 32.1% / 21.5% |
| Omnidyne | 48.8% | 32.3% | 23.9% | 25.2% / 10.9% / 5.3% |
| Helix | 45.9% | 30.9% | 21.2% | 54.2% / 29.9% / 19.8% |
| Prometheus | 44.5% | 26.7% | 20.5% | 50.3% / 30.9% / 20.7% |
| **Company spread** | 13.8 pts | 16.2 pts | 14.3 pts | 63.1 / 69.1 / 70.2 pts |

**DTO watch item:** DTO is still the top company in every pod. Its edge over a fair share is now +8 / +10 / +10 pts, down from +38 / +47 / +50. DTO used Slush Fund in **94.7% / 93.2% / 93.3%** of its seats, so the once-per-game Slush Fund is almost always spent. Under v0.34 it was used 2.1–2.3 times per DTO seat.

**White Hat spread:** 3.6 / 6.3 / 4.6 pts (v0.34: 5.8 / 7.5 / 4.3). Cipher is slightly high at 3P (37.1% vs 33.3% fair share).

### 4. Research economy

| Metric (2P / 3P / 4P) | v0.35 | v0.34 |
|---|---|---|
| 🔬 earned per player (mean) | 11.98 / 11.84 / 11.82 | 3.86 / 3.77 / 3.79 |
| 🔬 sources per seat (3P) | income 11.57, Signature Protocol 0.15, Triage L4 0.09, ★ 0.04 | income 3.61 |
| 🔬 unspent at game end | 0.77 / 0.68 / 0.65 | 0.67 / 0.70 / 0.72 |
| Mean track steps per seat | 4.68 / 4.55 / 4.47 | 1.63 / 1.60 / 1.61 |
| Seats with exactly 1 L4 track | 50.1% / 48.8% / 47.2% | 0% |
| Seats with 2+ L4 tracks | 0% | — |

**Track level distribution (3P, share of seats; 2P and 4P are within ±2 pts):**

| Track | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|
| Defense Grid | 47.1% | 36.8% | 7.8% | 6.9% | 1.4% |
| Triage | 44.1% | 33.4% | 9.0% | 10.3% | 3.3% |
| Release | 53.7% | 15.6% | 11.8% | 3.9% | 15.0% |
| Cryptographic Patents | 44.4% | 8.6% | 8.8% | 9.0% | 29.2% |

**Which track seats max (share of maxed tracks, 3P):** Patents 59.8%, Release 30.6%, Triage 6.7%, Defense 2.9%. The 2P and 4P pods are the same within 1 pt. This is the Patents concentration watch item: it is above the ~50% guardrail. The game-designer sweep predicted 58% under bot-biased focus.

### 5. Breakthroughs (taken per seat, 2P / 3P / 4P)

| Breakthrough | Per seat |
|---|---|
| Defense L1 (Gray die) | 0.55 / 0.53 / 0.52 |
| Defense L3 (+1 Secret) | 0.09 / 0.08 / 0.08 |
| Triage L1 (2 White Contractors) | 0.58 / 0.56 / 0.54 |
| Triage L3 ($3 upgrade) | 0.14 / 0.14 / 0.13 resolutions |
| Release L1 (Gray die) | 0.48 / 0.46 / 0.46 |
| Release L3 (+1 Secret) | 0.19 / 0.19 / 0.19 |
| Patents L1 (+$3) | 0.56 / 0.56 / 0.55 |
| Patents L3 (2nd Purple die) | 0.39 / 0.38 / 0.38 |

Every Breakthrough except Triage L3 was taken whenever it was reached. There were no Triage L1 contractor-supply forfeits and no Patents L3 reserve-empty forfeits.

**Triage L3 `$3` upgrade:** 867 / 1,220 / 1,608 resolutions.

| | 2P | 3P | 4P |
|---|---|---|---|
| Take rate | 36.4% | 35.2% | 37.9% |
| Forfeit rate (all forfeits were for being unable to afford `$3`) | 63.6% | 64.8% | 62.1% |
| Declined | 0% | 0% | 0% |

- Every upgrade picked **Yellow**. The bots apparently always take the first colour in the fallback order.
- The bots never decline. They forfeit only when they are short of cash, which happens nearly two-thirds of the time.

### 6. Level 4 effect payouts (per L4 holder per game, 2P / 3P / 4P)

| Effect | Holders (2P / 3P / 4P) | Payout per holder |
|---|---|---|
| Defense L4 `+$1` per blocked cube (max `$3`) | 89 / 128 / 180 | $7.4 / $7.0 / $7.1 |
| Triage L4 `+1 🔬` per move beyond the 2nd | 213 / 293 / 406 | 2.7 🔬 |
| Release L4 extra reroll (**OQ-15**) | 921 / 1,347 / 1,724 | **0.07 / 0.08 / 0.08 uses** |
| Patents L4 filings (`1 🔬 → 1 Secret`) | 1,782 / 2,628 / 3,353 | 4.5 / 4.6 / 4.9 Secrets |

- **OQ-15:** the Release L4 extra reroll is almost never used. Release L4 holders average 5.3 rerolls per game and rarely use up the base free rerolls, so the bonus reroll seldom comes into play.
- This is bot reroll policy, not an engine bug. The counter at `phase1_roll_deploy.py:388` increments only for rerolls beyond the base allowance.
- In practice the Release L4 payoff is Bandwidth 6.

### 7. Purple dice lost permanently (OQ-10)

| Metric (2P / 3P / 4P) | v0.35 | v0.34 |
|---|---|---|
| Purple lost per seat | **0.31 / 0.28 / 0.25** | 0.24 / 0.20 / 0.16 |
| Games with at least 1 Purple lost | 45.3% / 45.0% / 42.2% | 31.9% / 28.4% / 24.8% |
| Purple owned at game end per seat | 1.08 / 1.10 / 1.13 | 1.15 / 1.19 / 1.22 |

Losses come from Burn Notice and v3.0 Return Colored Die. They are more frequent than in v0.34, and under v0.35 they cannot be replaced. On average, more Purple dice are lost (0.25–0.31 per seat) than Patents L3 adds (0.38 per seat, net of the starter die).

### 8. End-of-game Corporate Secrets (informational; the User set no limit)

| Metric (2P / 3P / 4P) | v0.35 | v0.34 |
|---|---|---|
| Survivor Secrets | 4.09 / 4.25 / 4.40 | 3.28 / 3.61 / 3.79 |
| Winner Secrets | 3.60 / 5.05 / 6.08 | 2.72 / 4.12 / 4.98 |
| Maximum seen | 21 / 25 / 20 | 10 / 11 / 11 |
| Secrets from Patents per seat | 1.86 / 1.94 / 2.04 | 0.08 |

Patents L4 seats produce the high outliers. A 20–25 Secret game is now possible.

### 9. Sim bugs found

None that block. Two bot-policy observations, not engine faults:
1. The Triage L3 colour choice is always Yellow, and the bots never decline the upgrade.
2. The Release L4 extra reroll goes almost unused.

Determinism and seeds are reproducible with `--replay`.

### 10. Hand-off items for `game-designer`

1. Patents concentration is 59% of maxed tracks, above the ~50% guardrail.
2. 2P Total Wipeout is 16.0%, just over the 15% limit (carried forward from v0.34).
3. 🔬 per player is 11.8–12.0, just under the 12–14 target.
4. DTO is still the top company (+8 to +10 pts over fair share), but company spread fell from about 65 pts to about 15 pts.
5. The OQ-15 Release L4 extra reroll has almost no effect with the current bots.
6. OQ-10 Purple attrition: 0.25–0.31 per seat, and it cannot be replaced.
7. Bot order flipped: Adaptive Balanced and SecOps Turtle fell to 8–9% at 4P.
