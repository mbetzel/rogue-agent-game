# v0.37.0 Market Leader Bonus: Game-Designer Balance Assessment

**Author:** game-designer (post-telemetry balance validation). **Date:** 2026-11-07.
**Inputs:** FINDINGS §34, §36–§38; spec `docs/specs/v370_market_leader_bonus_spec.md` §8 / §14.1; product-owner report `docs/findings/v370_market_leader_bonus_telemetry_report.md` and `sim_results/v370_market_leader_bonus_*`.
**New runs (read-only, scratch scripts, not committed):** 2P tune slices through `scripts/run_v370_market_leader_bonus_sweep.py` (`run_pod` / `build_engine`, cells injected in memory), 3,000 games per cell, seed bases 42 and 7000 (paired seeds `base + 200_000 + idx`); and a winner-changed metric check on the V037 cell (2P and 3P, base 42, 3,000 games). About 48,000 games in total.

## 1. Verdict: APPROVED WITH TUNE (User decision required on the 2P Singularity band)

The Market Leader Bonus meets its design goal. Blue is no longer the automatic block, Red gets real defensive value, and the bonus does not take over the game. Every guardrail passes or sits in watch except 2P Singularity. That one sits exactly on the 46% fail line: 46.0% [45.1, 46.9] pooled over 12,000 games. Every `[TUNE]` option that clears it **fails a different guardrail or weakens the feature at 2P** (§3). My recommendation: **keep 9 / 8 / 9 Secrets and the 2P 1st +2 schedule, and move the 2P Singularity fail line from 46% to 48%** (watch band 43–48%). Moving the line is a guardrail change, so the User must approve it. The fallback, if the User wants Singularity ≤ 43%, is 2P starting Secrets 8. That trades the Singularity fail for a Total Wipeout fail (§3, option B).

## 2. Anomalies

### 2.1 Winner changed 11.7 / 15.1 vs §38's 15–18 / 17–20: the metric is defined differently; gameplay is the same

- The report's headline (11.7 / 15.1 / 24.9) is **winner changed over awarded games**. The §38 probe's `flip` divides by **all games** (`sum(flip)/G`), so it should be compared with the report's over-all rate: **10.7 / 14.4 / 24.5**. The staff-engineer is right that `flip` maps to `winner_changed_over_all`.
- The probe also used a coarser pre-bonus winner key: (Secrets, Market Share, Money) only. Any pre-bonus tie that a later tiebreaker settled counted as a "flip", even with the bonus off. The V036 probe cells already show 1–2% flips with no bonus at all.
- I re-scored the V037 games with the probe's key, base 42, 3,000 games per pod:

| Pod | Engine rate (all games) | Rate with probe key | Probe-only (false) flips | Engine-only flips |
|---|---|---|---|---|
| 2P V037 | 10.73% | 11.73% | 1.00% | 0 |
| 3P V037 | 14.43% | 16.13% | 1.70% | 0 |
| 2P V036 (bonus off) | 0.00% | 0.70% | 0.70% | 0 |

- Most of the remaining ~2 points is the dropped `deep=True` Red-purchase nudge. In the probe, the 2P all-aware cell at +1 Secret flips 10% without `deep` and 12% with it (`v360_share_placement_deep.txt`).
- §38's "15–18%" range also pools cells where the bots are not all bonus-aware (`none` 17%, `one` 18%). The like-for-like probe cell, 2P all-aware `+deep` at +2 Secrets, is **13% (seed 42) and 15% (seed 7000)**. Engine 10.7 + 1.0 (key) + ~2 (deep) ≈ 13.7.
- The sweep's own NAIVE and ONE-AWARE cells (17.0 / 15.3% over all games at 2P) reproduce the probe's `none` / `one` cells (17 / 17–18%).
- **Conclusion:** this is a metric and porting difference, not an engine defect. The end-reason split, Total Wipeout and edge all port within 2 points. Treat 2P winner changed ≈ 11–13% over awarded games as the correct v0.37 baseline. It is in the 10–30% pass band, and the bonus is clearly not inert.

### 2.2 At 2P, 43% of flips overturn a 2-Secret lead (tie plus Market Share tiebreak): acceptable, playtest watch

- Size: 140 games out of 3,000 (4.7% of all 2P games; 143 at seed 7000).
- Mechanism: 1st place is worth +2 Secrets, and Market Share is the first Hierarchical Tiebreaker, so in effect the bonus is worth "2.5 Secrets". §38 finding 4 already showed that a gap of 1 is inert at 2P because Market Share is the first tiebreaker. The 2-gap was chosen for exactly this reason.
- Why it is acceptable:
  1. It is fully visible (Deterministic Foresight). The Market Share track is public, and the leader can respond with Red blocks or a regain.
  2. Overturning a 2-Secret lead still requires winning the Market Share race outright. A tie on Market Share gives both players +2.
  3. The lowest-Market-Share survivor still wins 33.5% of 2P games, so a Secrets lead often holds.
  4. Rule fixes would be new rules (for example, no Market Share tiebreak after the bonus), which need User approval. The `[TUNE]` fixes are worse: +1 makes the bonus inert (§3, option C), and +3 breaks Total Wipeout (option D).
- Keep it as a playtest "feel" watch item. If testers call it a gotcha, the candidate is a rules-text reminder on the end-game summary (graphic-designer, Phase B), not a mechanics change.

### 2.3 RecklessSaboteur 2P 29.4 → 37.7%: intended catch-up, not a degenerate strategy

- Pre-bonus, its win rate is unchanged at 29.4%. The +8 comes from flips.
- Its survivor Market Share (4.74) matches the field (4.63–5.08). It is not exploiting Red.
- It is usually the trailing survivor on Secrets (3.80 before the bonus vs 4.07–5.41 for the other bots), so it is the most frequent beneficiary when the Market Share leader is not also the Secrets leader.
- More starting Secrets also cut its Patient Zero rate from 35.7% to 32.5%.
- The bot spread narrows from 31.5 to 22.5 points (2P), and RecklessSaboteur is still the weakest bot.
- Win rate by Red dice owned stays flat or falling (2+ Red is the worst bucket in every pod), so "buy Red" is not a dominant line.

## 3. 2P Singularity tune options (2P only; 3P / 4P unchanged; 3,000 games per seed base)

| Option (2P) | Seed | PZ / Sing / MC | TW (V036) | Rounds | Changed (awarded) | Aware edge | Blue open | Guardrail outcome |
|---|---|---|---|---|---|---|---|---|
| **A. 9 Secrets, +2 (V037 as built)** | 42 / 7000 | 27.0/47.1/25.9 · 27.0/46.7/26.3 (4-base pooled Sing 46.0 [45.1, 46.9]) | 8.4 (7.6) · 7.7 (7.1) | 9.14 | 11.7 · 12.7 | +7.9 · +7.7 | 23.1 | Sing on the fail line; all else pass/watch |
| **B. 8 Secrets, +2** | 42 / 7000 | 34.4/42.1/23.5 · 33.8/41.5/24.6 | **10.4 (+2.8) · 9.3 (+2.2)** | 9.03 | 10.8 · 11.9 | +7.1 · +7.2 | 22.0 | Sing passes (≤43); **TW fails** (> V036+2); MC watch |
| C. 9 Secrets, +1 | 42 / 7000 | 23.0/45.8/31.2 · 23.3/44.8/31.9 | 5.8 · 5.7 | 9.09 | 8.9 · 8.8 | **+1.1 · +2.5** (inert) | 15.5 | Sing watch; PZ watch; changed < 10%; bonus barely worth chasing at 2P (§38 finding 4) |
| D. 8 Secrets, +3 | 42 / 7000 | 42.1/38.9/19.0 · 41.8/38.3/19.9 | **13.5 · 12.2** | 8.95 | 12.9 · 13.8 | +9.0 · +9.7 | **34.2** | **TW fails; MC fails (< 20); Blue open fails (> 30)** |
| V037-S036 (7 Secrets, +2) | 42 | 42.2/36.2/21.6 | **12.0** | 8.86 | 9.7 | – | 20.4 | TW fails; PZ watch |

Other readings:
- Option B, NAIVE / ONE-AWARE: PZ 22.6–23.4 / 25.3–26.7; Singularity 39.4–39.7 / 38.8–40.6.
- Option B, highest v3.0-card trigger: Zero Day Override 44–46% (V037: 50.5%).

How to read the table:
- **Starting Secrets is a direct trade between Singularity and Patient Zero / Total Wipeout at 2P**, at about −5 to −6 Singularity, +7 to +8 PZ and +1.6 to +2 TW per Secret removed (9 → 8 → 7). No integer value satisfies both lines: 9 sits on the Singularity line, and 8 is over the Total Wipeout line.
- The bonus size changes the edge and Blue agency much more than it changes Singularity. +1 kills the incentive; +3 pushes players to give up Blue and die.
- 46% Singularity is the all-bonus-aware worst case. With mixed awareness it is lower: ONE-AWARE 44.2 / 42.4, NAIVE 43.0. All three endings stay live at 2P (each ≥ 25.9%). Rounds are 9.14, within band.
- Total Wipeout at 2P (both players eliminated, ranked on tiebreakers alone) is the worse experience to grow. v0.36 was tuned specifically to bring it down from 15.8%.

**Recommendation:**
1. Option A with a 2P Singularity band of pass ≤ 43, watch 43–48, fail > 48. The 4-base pooled CI upper bound is 46.9.
2. Fallback: option B (2P 8 Secrets), if the User weighs ending balance (34 / 42 / 24) over Total Wipeout (~9.8% pooled, +2.5 over V036). It would need the Total Wipeout band relaxed instead.
3. Do not adopt C or D.

## 4. Blue-agency goal: met

| 2P / 3P / 4P (V037 vs V036) | V036 | V037 |
|---|---|---|
| Any (generic) shields on Blue | 63.3 / 63.8 / 63.0 | 57.0 / 59.8 / 59.3 (≥ 55: Blue is still the main target) |
| Blue left open in contested rounds | 7.1 / 6.3 / 6.6 | 23.1 / 17.9 / 17.1 (a real choice; ≤ 25) |
| Red chosen in contested rounds | 22.4 / 21.5 / 21.8 | 43.6 / 39.1 / 39.8 |
| Red block rate | 15.3 / 14.7 / 14.9 | 22.0 / 20.5 / 20.9 |
| Win rate with 0 vs 2+ Blue dice, 2P | 40.9 / 66.8 | 44.0 / 62.0 (gap 25.9 → 18.0) |

Blue is no longer automatic: players leave it open on purpose about 3× as often, and Red is chosen about 2× as often. Blue is not dethroned either, which avoids the §38 degenerate case (Red over Blue → Patient Zero 59–67%). 2P Blue open at 23.1% is near the 25% line. Keep it as a watch item. It should not move under option A.

## 5. Watch items carried forward (no action now)

- **3P Market Collapse 22.6 / 23.2.** Watch band. Fixing it means 3P 7 Secrets, which sends Patient Zero to 46.6% (S036). Accept.
- **Bonus-aware edge +7.4–9.4 (2P / 4P).** Watch, under the +10 fail line, and in line with §38's +9. A skill reward for reading the Market Share track is intended. Re-check with the bot-roster diversification follow-up.
- **Setup concentration.** Zero Day Override v3.0 → 2P Singularity 50.5%; AEGIS@1 52.9%. Watch, under the 55% fail line. This follows from the 2P Singularity level and moves with it.
- **NAIVE 2P Patient Zero 17.4%.** Watch. Players who ignore the bonus survive more often. That is an argument for clear PnP and web reminders.
- **Telemetry.** Blue block rate has no engine hook; the internal `patches` key is a deprecated term, internal only. Both go to the staff-engineer backlog. They do not block this release.

## 6. Open decisions for the User

1. Approve moving the 2P Singularity fail line to 48% (watch 43–48) and keep 9 / 8 / 9 with 2P +2 (recommended). Or choose option B (2P 8 Secrets) and relax the 2P Total Wipeout band to V036 + 3.0.
2. Accept the 2-Secret-lead overturn (4.7% of 2P games) as intended, with a playtest watch. Changing the post-bonus tiebreak would be a new rule and needs separate approval.
3. Accept a winner-changed baseline of 11–13% at 2P (the engine's definition) in place of §38's 15–18%, which used the probe's coarser key and pooled cells.
