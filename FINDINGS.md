# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.

---

> [!NOTE] Sections §1–§35 (Phases 15–45, the v0.13–v0.36 baselines, and the §35 engine fix) are archived in [docs/archive/FINDINGS_s01-s35.md](docs/archive/FINDINGS_s01-s35.md). Section numbering continues here unchanged. **Agents: do not read the archive unless a task cites a specific §N ≤ 35.**

---

## 36. Pre-SDLC Exploration: Blue Defense Agency (no rules change)

Question (User, 2026-11-06): blocking Blue always comes first, so defense "plays itself", and v0.36 has no repeatable Secrets engine. Probes (hooks only, not rules code; `GameConfig.v036`, current bot roster, seeds `42 + n*100000 + idx`, 600 games per pod): `scripts/explore_v360_blue_pressure_probe.py`, `scripts/explore_v360_topoff_probe.py`, `scripts/explore_v360_blue_block2_probe.py`.

**Diagnosis (baseline, per seat per game):**

| | 2P | 3P | 4P |
|---|---|---|---|
| Block rate Red / Blue / Green | 15 / 67 / 12% | 15 / 68 / 12% | 15 / 67 / 12% |
| Any shields spent on Blue | 63% | 63% | 62% |
| Contested Any splits (Blue covered first) | 66% of attack rounds (94%) | 66% (94%) | 67% (94%) |
| Start → final Secrets; lost to Blue | 7 → 3.12; 3.96 | 7 → 3.29; 3.79 | 8 → 4.17; 3.94 |
| All other Secret gains minus Corruption losses | +0.08 | +0.07 | +0.11 |

1. **Final Secrets ≈ starting Secrets − Blue losses.** Blue defense is effectively the score. A Blue cube costs a permanent VP; Red and Green cost recoverable resources, so Blue-first is always correct. (Bots fill Blue first by policy, but the scoring math backs it.)
2. Patient Zero seats lose 7.5–8.7 Secrets to Blue vs 3.1–3.4 for survivors.

**Idea 3 — L4 top-off** (once per round in Phase 6, any track at L4: pay X 🔬 for +1 Corporate Secret; working name only, no glossary term):
- Research income is ~1.3 🔬 per round per seat; 42–44% of seats reach one L4 track, around round 4–5.
- Bots that convert only leftover research rarely use it (2–8% of seats).
- A top-off-aware bot (tops off before other spending; prices the first repairable Blue cube each round at X 🔬): at 3 🔬, 27% of seats use it, about 1.75 Secrets per user. Endings stay within ~3 points of baseline, rounds unchanged. One aware seat vs current bots wins 50.2 / 37.2 / 27.7% (fair share 50 / 33 / 25%). At 2 🔬: 40.7% at 3P and 31.1% at 4P, too strong.
- Starting Secrets −1 with top-off pushes Patient Zero to 37–41%: keep 7 / 7 / 8.
- **Agency barely moves:** Blue left open on purpose in contested splits goes from ~6% to 7–8% (8–9% at 2 🔬). A repairable Blue (3 🔬) still costs more than Red (2 🔬 regain) or Green, and the L4 gate arrives late.

**Idea 2 — Block 2 Blue faces** (A: Face 1 → Block 2 Blue; C: Faces 1 and 4 → Block 2 Blue):
- Blue lost per seat falls by 0.2–0.4 (3P: 3.79 → 3.59 / 3.42); Any shields on Blue 63% → 61 / 60%; endings shift 1–3 points.
- Small because seats own only 0.75–0.86 Blue dice and see Blue block faces 2 times in 6, vs ~1.5 Blue cubes per round.
- **Must-buy risk:** win rate by Blue dice owned (0 / 2+) at 4P goes from 17 / 39% to 13 / 47% (C). Partly correlational; bots' buying logic does not know Blue got stronger.

**Not simulated:** idea 1 (lower a track for a Secret — a late lifeline, would lower Patient Zero endings), idea 4 (new track — Patents again), idea 5 (Market Share → Secrets thresholds — the −1 side brings back the Unpaid Ransom Leak; shared Red cubes push toward Total Wipeouts).

**Takeaways:**
1. Making Blue cheaper to block (idea 2) or to recover from (idea 3) leaves Blue the costliest cube to take, so Blue-first stays correct. Real shield-split agency likely needs Red or Green damage to hurt more.
2. Idea 3 at 3 🔬 is worth keeping as a Secrets engine and strategic path (pacing-neutral, modest edge). Idea 2 is at most a small tuning option.
3. Sim/rules mismatch: `sim/engine/phase4_attack_resolution.py` lets DTO *Slush Fund* pay `$1` per extra Secret beyond the free 2; RULES.md has no such rule.

**Status: exploration recorded (User, 2026-11-07). No RULES.md, PnP or web change. Next candidate: probe costlier Red / Green damage.**

## 37. Pre-SDLC Exploration: Market Share Threshold Penalties (no rules change)

Question (User, 2026-11-07): would 2–3 threshold points on the Market Share track, each switching off something while a player is below it, push players to invest in Public Relations and make tanking toward Market Collapse less attractive? Candidate penalties: Client Company ability (Institutional Override) unavailable, Signature Protocol unavailable, lose a Purple die. Each comes back when the player climbs back above the threshold. Probes ran on scratchpad hooks only, not rules code: `GameConfig.v036`, the current bot roster, seeds `42 + n*100000 + idx`, 600–800 games per pod.

**Baseline Market Share curve (3P mean):** r2 16.7, r4 14.5, r6 11.9, r7 9.5, r8 6.7, r9 5.3. It falls about 1 per round in `v1.0`/`v2.0`, then about 2.5 per round once `v3.0` Red cubes arrive. Share of seats that ever reach ≤12 / ≤9 / ≤6 / ≤3: 94 / 84 / 70 / 51% (2P and 4P are similar). **The surviving player with the lowest Market Share wins 68 / 47 / 37%** (fair share 50 / 33 / 25%).

**Value of each penalty (one seat with it switched off all game):** without the Client Company ability, that seat wins 33.7 / 19.8 / 12.5%, about half its fair share. Without the Signature Protocol it wins 46.4 / 31.3 / 20.3%, a small loss. A lost Purple die was not simulated.

**Fixed thresholds** (Company off at ≤9 and Signature off at ≤5; at ≤6 / ≤3; at ≤12 / ≤9; both off at ≤14): endings move 1–5 points and rounds stay at 8.6–8.9. The lowest-Market-Share player wins just as often. Shared Red cubes push every player across a threshold together, and only late, after most Institutional Overrides are already used, so a threshold acts as a tax on everyone rather than a penalty for tanking.

**Relative lock** (the lowest-Market-Share survivor(s) lose the Client Company ability; nobody when everyone is tied). Aware bots spend research before track upgrades to get strictly above their lowest rival, except in the Final Round.

| 3P | Patient Zero / Singularity / Market Collapse | Market Share regained per seat | Final Secrets | Lowest Market Share wins |
|---|---|---|---|---|
| Baseline | 35 / 31 / 34% | 1.14 | 3.29 | 47% |
| Lock, bots ignore it | 37 / 31 / 32% | 1.16 | 3.09 | 42% |
| Lock, all bots aware | 40 / 36 / 24% | 2.43 | 2.65 | 49% |
| Lock, one aware bot | 38 / 30 / 32% | 1.42 | 2.98 | aware seat wins 33.2% (fair 33%) |
| Lock with a 2-point gap, all aware | 40 / 36 / 24% | 2.44 | 2.65 | 55% |

2P and 4P show the same pattern. With all bots aware, the lowest-Market-Share player wins 74% (2P) and 32% (4P). One aware bot wins 50.2% (2P) and 27.5% (4P).

**Takeaways:**
1. The relative lock does change behaviour: regain roughly doubles. But it becomes an arms race. Placings barely move, the research comes out of defense, Final Secrets fall by about 0.6, Patient Zero rises 3–6 points and Market Collapse falls about 10 points.
2. Avoiding the lock gives no edge (the one aware bot wins at its fair share), and tanking still pays as well as before.
3. Root cause (hypothesis): Market Share pays too little against Secrets, so research spent on defense beats research spent on Public Relations. Penalties add cost but don't change that trade-off.
4. Caveat: the aware bot follows a fixed "never be last" rule and doesn't weigh the lock against what it gives up.

**Next candidate:** reward Market Share instead of punishing it (for example, end-game Market Share → Secrets, or a `v2.0` comparison that pays Secrets), while watching the Total Wipeout risk noted for idea 5 in §36. Any lock rule would need a new glossary term, which must be confirmed with the User first.

**Status: exploration recorded (User, 2026-11-07). No RULES.md, PnP or web change.**

## 38. Pre-SDLC Exploration: End-Game Market Share Placement Bonus (no rules change yet)

Question (User, 2026-11-07): at game end, award bonus Corporate Secrets by relative Market Share placement (proposed 5/3/2/1). Patient Zeros get nothing; ties broken by the standard tiebreakers. What does it do to Blue as the default block? Probe (hooks only, not rules code; `GameConfig.v036`, current bot roster): `scripts/explore_v360_share_placement_probe.py` (modes `main`, `variants`, `cands`, `deep`, `prfirst`, `tw2p`, `fresh`). Seeds `42 + n*100000 + idx`, re-checked on `7000 + …`; 1,500–3,000 games per cell. Data: `sim_results/v360_share_placement_*.txt|json`.

A **bonus-aware** seat (probe heuristic, TUNE-BOT) values one Red cube at time weight × 3 × the expected change in bonus. The time weight is 0.3 / 0.6 / 1.0 in `v1.0` / `v2.0` / `v3.0`–Final Round; 3 is the value of one Secret saved by blocking Blue. From `v2.0` on it also buys the smallest regain that raises its expected bonus. Lethal Blue stays protected.

**Only the gaps between places matter.** Every survivor gets a bonus, so 5/3/2/1 is really +2 / +1 / +1, and 3/2/1/0 plays the same as 2/1/0/0 at 2–3P.

| 5/3/2/1, standard ties (2P / 3P / 4P) | Value |
|---|---|
| Winner changed by the bonus (current bots) | 21 / 36 / 46% |
| Highest-Market-Share survivor wins (baseline 55 / 45 / 34%) | 72 / 68 / 61% |
| One bonus-aware seat wins (fair 50 / 33 / 25%) | 57 / 44 / 40% |
| 3P Patient Zero / Singularity / Market Collapse, all bonus-aware (baseline 35 / 33 / 33) | 53 / 30 / 18 |

Too strong: a 4-Secret swing at 4P against ~4.7 average survivor Secrets.

**Findings:**
1. **Ties are common.** Every player takes the same Red cubes, so a scoring place is tied on Market Share in 19 / 45 / 72% of games. Under standard tiebreakers, Money decides a 1–2 Secret bonus in those games. Shared ties (tied players all take the better place) cut winner flips by ~5 points.
2. **Survivors-only vs all-player placement:** almost no difference. Use survivors only.
3. **Patient Zero rises when players chase the bonus**, by +6–19 points depending on the schedule. This is rational: a more Red-aggressive seat wins *more*. +1 starting Secret offsets it at 3–4P.
4. **The 2P bonus needs a gap of 2.** A 1-point gap does nothing (bonus-aware seat 49.6%) because Market Share is already the first tiebreaker.
5. **Red die buying doesn't pay:** Red purchases roughly double (0.6 → 1.1–1.3), win rate unchanged. **Public Relations-first still loses:** 46 / 27 / 18% with the bonus vs 39 / 21 / 13% without (fair 50 / 33 / 25%). Research income (~1.3 🔬/round), not the regain limit, is the bottleneck. Average Public Relations level stays 0.2–0.4.
6. **Blue agency:** with shields short, Blue left open on purpose 6–7% → 17–22%; Red chosen 22% → 39–43%; Any shields on Blue 63% → 57–60%. Blue stays the main target. Red overtakes Blue only if players treat Market Share loss as permanent from round 1, and then Patient Zero hits 59–67% (degenerate). Win rate for 0 vs 2+ Blue dice flattens: 2P 40 / 66% → 45 / 61%.
7. **2P Total Wipeout:** at 8 starting Secrets, all bonus-aware, 10.1–10.4% (baseline 7.6%). At 9 Secrets it is 7.7–8.4%, with Singularity 45–46% (guardrail 43%).

**Proposed package (seed base 7000):** 2P 1st +2; 3–4P 1st +2, 2nd +1; others 0; Market Share ties share the better place; survivors only; no bonus on a Total Wipeout; starting Secrets **9 / 8 / 9** (2P +2 chosen by User).

| | 2P | 3P | 4P |
|---|---|---|---|
| Baseline endings | 30 / 36 / 34 | 33 / 34 / 33 | 30 / 34 / 35 |
| Endings, current bots | 18 / 42 / 39 | 26 / 39 / 36 | 24 / 38 / 38 |
| Endings, all bonus-aware | 27 / 46 / 27 | 37 / 41 / 22 | 32 / 39 / 28 |
| Total Wipeout, all bonus-aware (baseline) | 8.4% (7.1%) | 3.8% (2.6%) | 1.2% (1.0%) |
| Rounds, all bonus-aware (baseline) | 9.13 (8.83) | 8.97 (8.79) | 8.95 (8.83) |
| One bonus-aware seat wins | 59.2% | 39.6% | 33.7% |
| Winner changed by the bonus | 15–18% | 17–20% | 25–27% |
| Lowest-Market-Share survivor wins (baseline) | 31% (44%) | 20% (33%) | 13% (23%) |

Seed-42 results agree within ~2 points. RecklessSaboteur's 2P win rate rises 27 → 37–42%.

**Watch items:** 2P Singularity 46% (over the 43% guardrail); 2P bonus-aware edge +9 points; Patient Zero 18–26% if players ignore the bonus; Public Relations Track weakness (separate exploration).

**Implementation plan (pending User sign-off). Rule name: Market Leader Bonus (User, 2026-11-07).**
1. **Glossary:** add **Market Leader Bonus**. Change Market Share's "Scores `0 VP`" line, and update the Corporate Secrets and Total Wipeout entries.
2. **RULES.md:**
   - Section 5 scoring step: award by placement before comparing Secrets; ties share; Patient Zeros excluded; none on a Total Wipeout.
   - Starting Secrets `[TUNE]` 9 / 8 / 9.
   - Market Collapse note: the player at `0` scores normally but places last.
3. **sim:**
   - `GameConfig` fields for the bonus schedule and tie mode, plus a v0.37 factory.
   - `sim/engine/end_game.py`: apply the bonus before ranking; record pre-bonus Secrets and the bonus in telemetry.
   - `sim/bots/market_share_policy.py`: placement-bonus valuation in `marginal_block_value` and `urgent_regain` (time weight [TUNE-BOT]).
   - Tests: tie sharing, Patient Zero exclusion, Total Wipeout, 2P schedule.
4. **Acceptance sweep** with the full guardrail set (product-owner) and an independent balance check (game-designer).
5. **PnP and web:** scoring summary, Market Share track placement reminder, Company Terminal Mat and end-game screen (graphic-designer).

**Status: exploration recorded (User, 2026-11-07). No RULES.md, PnP or web change.**

## 39. Phase 46 Market Leader Bonus Sweep & Balance: APPROVED WITH TUNE (`v0.37.0`)

Sources: product-owner [docs/findings/v370_market_leader_bonus_telemetry_report.md](docs/findings/v370_market_leader_bonus_telemetry_report.md) (spec cells at seed 42, V036 / V037 / ONE-AWARE again at seed 7000, extra 2P seed bases 9000 and 13000); game-designer [docs/findings/v370_balance_assessment.md](docs/findings/v370_balance_assessment.md) (~48,000 more games of tune slices). Implementation: spec [docs/specs/v370_market_leader_bonus_spec.md](docs/specs/v370_market_leader_bonus_spec.md), `GameConfig.v037()`.

| V037, seed 42 | Patient Zero / Singularity / Market Collapse | Total Wipeout (V036) | Rounds | Winner changed (over all games) | Bonus-aware edge |
|---|---|---|---|---|---|
| 2P | 27.0 / 47.1 / 25.9 | 8.4% (7.6) | 9.14 | 10.7% | +7.9 |
| 3P | 37.5 / 39.9 / 22.6 | 4.2% (2.6) | 8.97 | 14.4% | +6.2 |
| 4P | 30.4 / 40.1 / 29.4 | 1.6% (1.0) | 8.99 | 24.5% | +7.4 |

Seeds 42 and 7000 agree within 2.1 points. Endings, Total Wipeout and edge match §38 within 2.5 points.

**2P Singularity** is 46.0% [45.1, 46.9] pooled over 12,000 games (four seed bases), on the 46% fail line. It is driven by the 9-Secret 2P start, not the bonus: with V036 starting Secrets it is 36.2%, but Patient Zero is 42.2% and Total Wipeout 12.0%.

| 2P tune option | Patient Zero / Singularity / Market Collapse | Total Wipeout | Edge | Outcome |
|---|---|---|---|---|
| A. 9 Secrets, +2 (kept) | 27 / 47 / 26 | 8.4 / 7.7 | +7.9 | Singularity on the line |
| B. 8 Secrets, +2 | 34 / 42 / 24 | 10.4 / 9.3 | +7.1 | Total Wipeout fails |
| C. 9 Secrets, +1 | 23 / 45 / 31 | 5.8 | +1 to +2.5 | Bonus barely worth chasing |
| D. 8 Secrets, +3 | 42 / 39 / 19 | 13 | +9.4 | Three guardrails fail |

The 46–47% is the worst case, where every bot chases the bonus. With one bonus-aware seat it is 44.2 / 42.4%; with none, 43.0%.

**Blue agency goal: met.**
- Generic shields on Blue: 63% → 57–60%.
- Blue left open in contested rounds: 6–7% → 17–23%.
- Red chosen in contested rounds: 22% → 39–44%.
- Red block rate: 15% → 21–22%.
- 2P win rate with 0 vs 2+ Blue dice: 41 / 67% → 44 / 62%.

**Game-designer notes:**
- The winner-changed gap with §38 is a counting difference, not a gameplay one. The probe divided by all games and used a shorter pre-bonus tiebreak. Like-for-like it is ~13% vs the sweep's 10.7–11.7%. The new 2P baseline is 11–13%.
- At 2P, 4.7% of games see a 2-Secret lead overturned: +2 creates a tie and Market Share breaks it. Accepted as a playtest watch item; Market Share is public and the trailing player must win it outright.
- RecklessSaboteur's 2P win rate rises 29.4 → 37.7%. This is intended catch-up; it is still the weakest bot, and the spread between bots narrows from 31.5 to 22.5 points.

**Watch items:**
- 3P Market Collapse 22.6 / 23.2%.
- Bonus-aware edge +7.4 to +9.4 (fail +10).
- Zero Day Override as the v3.0 card: 2P Singularity 50.5% (fail 55%).
- 2P Patient Zero 17.4% when no bot chases the bonus.
- 2P Blue left open 23.1% (line 25%).

**Decisions (User, 2026-11-07):** keep option A (starting Secrets 9 / 8 / 9; 2P 1st +2; 3–4P 1st +2, 2nd +1). Move the 2P Singularity guardrail to pass ≤ 43%, watch 43–48%, fail > 48%. The game-designer's notes on 2-Secret overturns and the 11–13% winner-changed baseline are adopted as watch / baseline values.

**Status: approved for Phase B (RULES.md v0.37.0, glossary, `GameConfig()` default, web, PnP).**

## 40. Phase 47 Reference Bot Assessment and Kamikaze Market Collapse Check (no rules change)

Question (User, 2026-11-07): is the reference bot fit as the "competent player" check, what does it say about §36–§38, and does its win after its own Market Collapse trigger (195 of 1,200 v0.37 ref1 games) show a kamikaze strategy? Sources: `sim_results/reference_bot/validation_report.md`; game-designer report [docs/findings/v370_reference_bot_assessment.md](docs/findings/v370_reference_bot_assessment.md). Extra probe: the validation seeds replayed with per-round Market Share / Secrets telemetry, 3P, 1,200 games per cell, plus a Market Collapse-off counterfactual (scratch only).

**Bot verdict: fit.** ref1 edge over fair share: +33 / +36 points at 3P (v0.36 / v0.37), well past the +10 gate. Mixed seats sit at fair share. Limits: it only chooses among moves the existing policies propose; rollouts are played by scripted policies; only Phase 4 shields and Phase 6 spending are searched.

**§36–§38 re-judged:**
- Blue-first stands, softened: ref still puts ~49% of blocks on Blue but blocks Red more (Red block rate 0.29 vs rivals 0.22 at v0.37).
- §37 root cause stands: ref regains less Market Share than rivals (1.31 vs 2.06) and still wins.
- "Tanking pays" was a bot artifact (see below).
- Public Relations-first still loses (ref Public Relations Track 0.65–0.77).

| Kamikaze check, 3P ref1 | v0.36 | v0.37 |
|---|---|---|
| ref at 0 when Market Collapse triggered (others at 0 too / alone) | 432 (390 / 42) | 375 (316 / 59) |
| ...ref won | 236 | 195 |
| ref Secrets lead at trigger in those wins | +3.8 (never behind) | +7.5 (behind 0.5%) |
| ref wins when it alone triggers | 40% (17/42) | 37% (22/59) |
| Market Share lost to Red, ref / rivals | 16.7 / 17.8 | 16.4 / 17.7 |
| ref win with Market Collapse off (counterfactual) | 64.5% (−2.1) | 66.7% (−2.4) |
| Singularity with Market Collapse off | 83% | 84% |

**Takeaways:**
1. No kamikaze strategy. The ref seat loses *less* Market Share than rivals, is usually at 0 together with everyone else (shared Red cubes), and wins those games because it already leads on Secrets. Alone at 0 it wins only at about fair share.
2. Market Collapse is not what the ref's edge depends on (−2.4 points when switched off). Collapse is doing its pacing job: without it Singularity takes ~83% of endings.
3. Watch item: under v0.37 the ref is strictly lowest on Market Share the round before trigger in 43% of its at-0 games (v0.36: 26%). It trades Public Relations for Secrets, a legitimate trade that confirms §37.
4. Archetypes: VentureGreed leads (51% at 3P v0.37) on economy and Blue defense, not a rule exploit; the ref seat holds it to 32%. SecOpsTurtle rises 26 → 39% under the Market Leader Bonus (intended). RecklessSaboteur Patient Zero 10% at 3P. No other degenerate pattern.

**Candidate levers (none decided):** A. no change (recommended); B. a larger 3–4P Market Leader Bonus gap ([TUNE]); C. cheaper Public Relations regain ([TUNE], small expected effect); D. a Secrets penalty at 0 Market Share (new rule and likely new term, needs User approval; Unpaid Ransom Leak risk); E. remove Market Collapse (shown only as a counterfactual; breaks pacing).

**Open questions for User:** adopt one Mixed seat in every sweep and a ref1 edge check on every rule candidate? Close the kamikaze concern (lever A)? Add "Public Relations push" and "Market Share dump" candidates to the bot portfolio?

**Status: analysis recorded (game-designer, 2026-11-07). No RULES.md, PnP, web or sim change.**

**Decisions (User, 2026-11-07):** adopt the roster rule (one Mixed seat in every routine sweep; ref1, 3P, 1,200 games, as the edge check on every rule candidate). Close the kamikaze Market Collapse concern with lever A (no rule change). Add "Public Relations push" and "Market Share dump" as reference-bot candidates so future no-exploit results cover those lines.

**Addendum: portfolio follow-up (game-designer, 2026-11-07).** The 13-member portfolio lifts ref1 v0.37 3P win 69.1 → 78.6% (±2.3). Attribution, 1,200 games each, same seeds; details in [docs/findings/v370_reference_bot_attribution.md](docs/findings/v370_reference_bot_attribution.md), data in `sim_results/reference_bot/attribution/`:

| Portfolio | Win % | Δ | Collapse off | Ref at 0 at trigger (alone) | MLB 1st | Red share of blocks |
|---|---|---|---|---|---|---|
| 11 | 69.1 | — | 66.7 | 375 (59) | 64% | 36% |
| + push | 74.2 | +5.1 | 68.0 | 254 (35) | 78% | 42% |
| + dump | 76.3 | +7.2 | 78.6 | 446 (94) | 63% | 34% |
| 13 | 78.6 | +9.5 | 77.6 | 321 (51) | 75% | 40% |

Both lines contribute (overlapping, not additive). Push is undervalued Red blocking and Public Relations, and it pays mainly by keeping the ref off 0 when Market Collapse triggers. Dump trades Market Share for Secrets and is stronger with Collapse off, so it is not kamikaze. §40 "no kamikaze" and §38 "Public Relations-first loses" both stand; §38 is refined to "situational Public Relations wins". Candidate levers (none decided): A bot update only (recommended); B larger Market Leader Bonus gap [TUNE]; C stronger Red [TUNE]; D Secrets penalty at 0 Market Share (new term, needs User approval). No RULES.md, PnP, web or sim change.

## 41. Phase 48 Lever A Post-Telemetry Assessment (bot-only, no rules change)

Question (User, 2026-11-07): did lever A (situational Public Relations push / Market Share dump for AdaptiveBalanced, Blue-safe split, default `PrPushParams` kept by User decision) make the roster play closer to competent? Should `bot_pr_push=True` become the default roster, and which scope should the ref1 edge check use? Is VentureGreed's >40% win rate a rules or a bot problem? Sources: `sim_results/lever_a/sweep/sweep_report.md`, `docs/findings/lever_a_regression_diagnosis.md`; report [docs/findings/v370_lever_a_assessment.md](docs/findings/v370_lever_a_assessment.md). Extra probes (scratch, 4 procs): ref1 3P switch off on the current tree (300 games, 300/300 identical to the 13-member file), ref1 2P switch off (600 games, heads-up).

**Correction:** the sweep compared ref1 "on" with the 11-member 69.1% file. The true switch-off baseline (13 members) is **78.6%**.

| ref1, 3P, 1,200 | ref win % | edge | Δ vs off |
|---|---|---|---|
| 13 members, off | 78.6 | +45 | — |
| on, scope `all` | 77.1 | +44 | −1.5 |
| on, scope `non_reference` | 71.2 | +38 | −7.4 |

| Check | Off | On | Result |
|---|---|---|---|
| AdaptiveBalanced 2P / 3P / 4P | 39.1 / 17.2 / 8.8 | 51.2 / 26.5 / 16.1 | PASS |
| Patient Zero Δ 2P / 3P / 4P | — | −0.3 / −0.3 / −1.3 | PASS (≤ +2) |
| Mixed seat 3P | 34.2 | 32.7 | PASS |
| Max archetype 3P | 51.2 (Vent) | 48.8 (Vent) | FAIL, pre-existing |

**Verdict: lever A met its goal (partial on the edge).** Every guardrail passes at 2/3/4P, AdaptiveBalanced gains 7–12 points, and the edge fell +45 → +38 (inside the scoping estimate +37 to +42). It stopped short of +35 because only AdaptiveBalanced learned the lines (the ref faces it in 40% of pods), the Phase 6 comfortable-leader dump is out of scope, and the search keeps a real tactical edge. Scope `all` hides the drop because the ref's fallback and rollouts improve too. The reference bot remains a valid competent-player check (2P heads-up 88%, Mixed at fair share).

**Proposed roster rule (needs User sign-off):** rule probes and routine sweeps use `bot_pr_push=True` with default `PrPushParams`, the `_bot_classes()` rotation and one Mixed seat; the edge check is ref1, 3P, 1,200 games, `bot_pr_push_scope="non_reference"`, reference 71.2% (+38), flag at ±5 points or below +10. Historical fixtures pin `bot_pr_push=False`.

**VentureGreed (3P 51.2 off / 48.8 on; 2P 59.0): a bot problem.** Heads-up against the ref at 2P it wins 20% (ref 80%, n = 120); with the ref at a 3P table it falls to 29–32%. It is the ref's hardest opponent (ref 59% with it vs 79% without), so its economy line (Yellow-first, paid Secrets with no cushion, light shielding) is strong, not degenerate; the other scripts answer it badly. Watch item: 2P spread. Candidate levers (none decided): V1 teach another archetype VG's paid-Secret timing [TUNE-BOT]; V2 re-define the 40% guardrail to also require ref1 holding the archetype below fair share; V3 add a second competent seat to the rotation; V4 dearer Money → Secret actions [TUNE] (scratch B2-only probe inconclusive); V5 larger 2P Market Leader Bonus [TUNE]. No new game term proposed.

**Follow-up:** `scripts/run_reference_bot_validation.py` output names include `_params` but not the `--pr-params` values, so runs with different overrides overwrite each other. Add a hash or `key=value` tag (engineering).

**Open questions for User:** adopt the roster rule above? Close Phase 48 at +38 or open a Phase 6 comfortable-leader dump lever? Accept the VentureGreed "bot problem" diagnosis and pick V1/V2/V3? Re-baseline sweep reports to the 13-member 78.6% file? Schedule the script naming fix?

**Status: analysis recorded (game-designer, 2026-11-07). No RULES.md, PnP, web or sim change.**

**Decisions (User, 2026-11-07):**
1. Roster rule adopted: every rule probe and routine sweep uses `bot_pr_push=True` with default `PrPushParams`, the `_bot_classes()` rotation and one Mixed seat. The edge check on every rule candidate is ref1, 3P, 1,200 games, seeds `42+300000+idx`, `bot_pr_push_scope="non_reference"`, reference value 71.2% (+38). Flag if it moves more than ±5 points or falls below +10. Historical fixtures pin `bot_pr_push=False`.
2. Phase 48 closed at +38; the Phase 6 comfortable-leader dump is not pursued now.
3. VentureGreed diagnosis accepted (bot problem). Lever V2 adopted: the 40% archetype guardrail fails only if ref1 also cannot hold that archetype below fair share. V1 kept for later; V3–V5 not pursued.
4. Sweep reports re-baseline to the 13-member switch-off ref1 value (78.6%).
5. Fix `run_reference_bot_validation.py` output naming so `--pr-params` runs don't overwrite each other.
