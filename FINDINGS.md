# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.

---

> [!NOTE] Sections §1–§36 (Phases 15–45, the v0.13–v0.36 baselines, the §35 engine fix, and §36 Blue Defense exploration) are archived in [docs/archive/FINDINGS_s01-s35.md](docs/archive/FINDINGS_s01-s35.md). Section numbering continues here unchanged. **Agents: do not read the archive unless a task cites a specific §N ≤ 36.**

---

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

## 42. Pre-SDLC Exploration: Secret Faces, Processing Box & Company Starting Die (package locked, no rules change yet)

Question (User, 2026-11-07): every player is hit equally and only Secrets score, so every seat plays the same Blue-first game. Money and research are not enough of an engine, and Red and Green are "other things to juggle". Make the engine feed Secrets, so each player's dice decide which cubes hurt them. Sources: scratchpad probes (hooks / a standalone model, not rules code): `exposure_probe.py`, `colored_probe.py`, `yield_model.py`, `cube_cost.py`, `tune_probe.py`, `blue0_probe.py`, `grid_probe.py`, `grid2.py`.

**Step 1 — asymmetric cube impact (rejected).** Per-player colour→effect profiles were tested first (v0.37 roster, 3P, 2,400 games, random version deals). Cube exits per game vary with the v1/v2 deal (Red 11.7–23.6, Blue 10.8–16.4, Green 10.5–20.1). With the same defence, moving Secret theft from Blue to Red costs 12.0 vs 1.7 Secrets under Script Kiddie + RaaS (94% breach). Blue is the scarcest colour on purpose. The User kept the shared threat (like *Moon Colony Bloodbath*): divergence should come from what players build.

**Step 2 — baseline (v0.37 roster, 3P, 1,200 games).** Seats own 0.7 / 1.3 / 1.7 / 2.3 colored dice in rounds 2 / 4 / 6 / 8 but have only ~0.8 In Production. Mix: Blue 35%, Red 32%, Yellow 23%, Green 10%. Non-Blue Secret gains net +0.08 per seat (§36).

**Step 3 — Secret-yield model.** Single seat with scripted priorities, real tower draws from Step 1, calibrated so v0.37-like rules give Blue losses 3.96 (sim ~3.8) and 2.1 colored dice bought (sim ~2.3). It is ~1 Secret more generous than the full sim. No win rates.

| 3P, final Secrets at start 6 (no Market Collapse unless noted) | Red | Blue | Green | Mixed | Diverse | Red / Green cube cost to owner (r3) |
|---|---|---|---|---|---|---|
| First settled rules (Blue 1 + 2 Breakthroughs + bonus, cap 3; Green 2; Red 2/1/0 at 12/6) | 8.2 | 11.8 | 6.5 | 7.1 | — | 0.34 / 0.69 |
| Blue 0 + Breakthroughs + bonus; Red 3/2/1/0 at 14/10/6 | 10.6 | 9.5 | 6.5 | 5.7 | 7.4 | 0.56 / 0.67 |
| One Blue research space (Defense Grid L3) | 10.6 | 10.6 | 6.5 | 7.4 | 8.4 | 0.56 / 0.67 |
| + Green base 3 | 10.6 | 10.6 | 9.3 | 7.6 | 8.6 | 0.56 / 0.65 |
| + 12-point track (tiers 10/7/4) | 8.3 | 10.8 | 9.4 | 7.2 | 7.8 | 0.69 / 0.67 |
| + Company die replaces a Gray | 11.9 | 13.9 | 14.2 | 10.5 | 11.0 | 0.92 / 0.75 |

Red tiers on the package (start 5): 12 track 10/7/4 → Red seat 10.9, cube cost 0.95; **12 track 9/5/1 → 12.8, 0.85**; 14 track 11/7/3 → 12.8, 0.85; 18 track 14/10/6 → 13.7, 0.74. Blue costs ~1.0 for every seat. Today Red and Green cost ~0.

**Package at start 4 (12 track 9/5/1):** Red 11.8, Blue 11.8, Green 12.1, Mixed 8.9, Diverse 9.6, starting die only 6.4. Breach per seat at 3 / 4 starting Secrets: specialists 6–8% / 3–4%, Mixed 11% / 6.5%. v0.37-like reference in the model: ~10% at 8.

**Takeaways:**
1. Secret faces make the engine score: specialist paths earn 7–10 Secrets per game vs ~0 today, and each colour's cubes now cost its owners 0.75–0.92 Secrets against Blue's 1.0 for everyone. The tower stays equal for all; the payoff now depends on your dice.
2. Glitched Shield Slots with one free clear per Phase 5 graduation never take a seat's last shield slot (lingering, not compounding).
3. The Triage Bandwidth cap rarely binds (≤1.1% of colored dice blocked from chasing); Money is the real limit at these ownership levels.
4. Blue's research faces paid for its own yield (11.8, far ahead); a single +1 research space fixed it.
5. Specialising still beats spreading by ~2 Secrets. The model has no competition for dice (6 per colour at 3P, two Companies per colour), which only the full sim can test.
6. Yellow-first (fuel) is the weakest path in isolation. Watch item.
7. Market Collapse off: 3P sim endings 58% Singularity / 37% Patient Zero / 5% Total Wipeout, games +0.3 rounds. Check the 2P Singularity guardrail (pass ≤ 43%).

**Locked package (User, 2026-11-07):**
- **Secret face** (new term, provisional): Face 5 on Red, Blue, Green and Purple dice. The die goes to the **Processing Box** (new term, provisional; replaces the Glitched Box; Under Development = Processing Box → Scanned Box). The Secret is gained when Phase 5 Conveyor Triage moves the die out; dice still in the Processing Box at game end lose their Secret. Free rerolls stay. **Glitched Box** and the **Glitch face** are retired.
- **Yields:** Red 3 / 2 / 1 / 0 at Market Share 9+ / 5–8 / 1–4 / 0. Blue 1, +1 if you blocked at least 1 Blue cube that round, +1 at Defense Grid Level 3 (max 3). Green 3 minus your Glitched Shield Slots (min 0). Purple 1.
- **Market Share:** 12-point track (start and max 12). Market Collapse removed as an end trigger.
- **Defence:** colored dice have no shield faces; all shields are `Block 1 Any` from Gray, White and Purple dice.
- **Yellow:** fuel die (choice faces such as `$` / research), no Secret face, no shields.
- **Glitched Shield Slots** (provisional term): unblocked Green cubes and the "glitch X dice" Corruption spaces glitch slots. A die placed to clean a slot goes to the Scanned Box. Once per Phase 5, if at least 1 die graduates to Ready for Release, clear 1 slot. White Contractor glitch faces discard the die.
- **Company starting die:** each Client Company names a Red, Blue or Green starting die (two Companies per colour). It replaces 1 starting Gray; the Triage Level 1 Breakthrough gives a Gray die (replacing its 2 White Contractors).
- **Starting Secrets:** 4–5 at 3P for the full sim probe; 2P / 4P to be fitted.
- **Draft (to be confirmed by the probe):** die faces, Variant Card rework and power retargets as proposed to the User 2026-11-07. Red F1 `+1 Market Share / +$1`; Blue takes the research faces; Green F1 `Clean 1 Glitched Shield Slot / +$1`. R1 `+$2 & +1 Market Share`; B1 `+1 🔬` (+`$2` on no Blue damage); B2 pay-`$4` only; B3 moves Processing → Scanned in Phase 3; G1 / G2 clean slots + 🔬; Y3 goes to the Scanned Box. *Magnetic Splice* and *Jumper Diagnostics* move a die out of the Processing Box (banking its Secret). *Brute-Force Bypass* becomes +1 free reroll and set 1 die to any non-Star face. *Arbitrary Code Execution* may need to exclude the Secret face.

**Implementation plan (pending SDLC kick-off):**
1. **Glossary approval:** confirm Secret face, Processing Box and Glitched Shield Slot; retire Glitched Box and Glitch face; update the Market Share / Market Collapse entries.
2. **Spec (`principal-engineer`):** `GameConfig` levers for each part of the package (Secret faces, yields, 12-point track, Market Collapse off, no colored shields, Yellow fuel, Glitched Shield Slots with graduation clear, Company starting die, Breakthrough changes), with the v0.37 path kept for parity.
3. **Implementation (`senior-engineer`) + review (`staff-engineer`):** engine, die faces, Variant Cards, powers; bot policies for chasing Secret faces, colour-aware Any-shield splits and purchases. Tests: banking at triage, stranded dice on Singularity, yield tiers, slot clear, starting die.
4. **Sweep (`product-owner`):** 2/3/4P with the roster rule, starting Secrets 3–6, full guardrails (endings, Total Wipeout, rounds, archetype spread), win rate by Company colour and by path, and the ref1 edge check.
5. **Balance assessment (`game-designer`):** confirm the model's results with real competition for dice; tune tiers, Green base and starting Secrets.
6. **Phase B:** RULES.md, PnP and web after sign-off (`graphic-designer` for the Company Terminal Mat and dice).

**Glossary decisions (User, 2026-11-07):** Secret face, Processing Box and Glitched Shield Slot are approved as final terms, and Glitched Box is retired. The `Glitch` face stays on White Contractor dice only (it discards the die); colored dice no longer have it. Phase B retires Color-Specific Shield, Red / Blue / Green Shields, Two-Stage Defensive Blocking and Market Collapse (as an end trigger). The sim keeps the v0.37 path behind levers for parity.

**Status: package locked for the full sim probe (User, 2026-11-07). No RULES.md, PnP, web or sim change.**

## 43. Phase 49 Sweep & Balance Assessment (`v0.38` candidate): NOT APPROVED

Sources: `sim_results/v380_secret_faces/sweep_report.md` (15 cells × 1,200 games, roster mixed1, ref1 3P 1,200), `docs/findings/v380_balance_assessment.md` (probes P0–P11, 600 games per cell).

- **Works:** stranded Secrets ~3%; no round with zero shield capacity; Total Wipeout ≤1% at 3P/4P; 8.8–9.6 rounds; ref1 non_reference 78.2% ≈ the v0.37 13-member portfolio (78.6%).
- **2P Singularity** 63–82% at S3–S6 (guardrail ≤48%). Each starting Secret moves only ~5–6 pts. Only the P9 stack (S3 + Green base 2 + Purple yield 0) reaches 46.0%, with 8.2% Total Wipeout.
- **3P/4P Singularity** 45–75%; P11 (S4 + Green base 2 + Market Leader Bonus 4-2) gives 49.5% / 46.5%.
- **Archetype spread** 46–53 pts. The lever A push/dump line accounts for 11–16 pts (P1, bot artifact); the rest (~1.6× fair share) is a rule effect: Company-colour commitment and free 0 Market Share.
- **0 Market Share is a degenerate stable state:** 28–31% of seats end there. Red cubes then do nothing, so all shields go to Blue/Green, and Red dice keep paying. ref1 ends at 0 in 82.7% of games and wins 77.3% of those. A bigger Market Leader Bonus barely helps (P10).
- **Red path** strongest (61 / 46 / 38% at 2/3/4P); Red tiers 2/2/1/0 (P2) trim it. **Yellow path** weak (31 / 13 / 5%): Yellow cannot turn Money into Secrets (face-design gap).
- **Tooling bug:** `--set corruption_track_capacity_by_player_count` is silently ignored (P4 identical to P0).

**User decisions pending (assessment doc):** (1) 2P Singularity guardrail with Market Collapse off; (2) a cost for 0 Market Share (Market Collapse back / Red-at-0 cost / none); (3) Red tiers 2/2/1/0 and Green base 2; (4) starting Secrets per player count; (5) Yellow redesign; (6) lever A line for all archetypes or none in rule sweeps; (7) fix the `--set` bug.

**User decisions (2026-11-08) on §43:** (1)+(2) bring Market Collapse back as an end trigger (Final Round, no elimination) under v0.38; the 2P Singularity ≤48% guardrail stays. (4) Starting Secrets 2P 3 / 3P 4 / 4P 4 for the next candidate. (5) Yellow will be redesigned (design discussion open). (7) Fix the `--set corruption_track_capacity_by_player_count` bug. (3) yields and (6) the lever A bot line: pending, after explanation.
**User decisions (2026-11-08, cont.):** (6) lever A push/dump line off for all archetypes in rule sweeps. (3) User concern: Red 2/2/1/0 makes the top tier meaningless; proposed 2/1/0/−1 instead (under discussion). (5) Yellow direction: Market Share generator, e.g. one `+2 Market Share` face and one `+1 Market Share / +1 🔬` face (to be modelled). Green cube resolution and late-game Green pressure are open for discussion.
**User decisions (2026-11-08, cont.):** Red Secret face yield stays 3 / 2 / 1 / 0 with raised thresholds: Market Share 11–12 / 7–10 / 3–6 / 0–2 (2/1/0/−1 rejected: a Secret-costing face is a dead roll and echoes the retired Unpaid Ransom Leak). Green resolution accepted as is (glitches the slot for later rounds; dice already placed unaffected); a per-round slot-glitch cap is added as an off-by-default lever. Green base 3 vs 2 left to the probe.

### 43.1 Candidate 2 probes (`v038b`): APPROVED WITH TUNE

Source: `docs/findings/v380_balance_assessment.md` "Candidate 2" (probes Q0–Q6, R1–R2; 600 games per cell; noise ±2 pts on endings, ±4–6 pts on archetype and path rates).
- Market Collapse dominates in v038b (41–49%, 7.8–8.0 rounds). Cause: the 12-point start, not the new Red thresholds (Q4 ±2 pts).
- **Recommended C2 (R1):** v038b + starting Market Share 14 + Market Leader Bonus 2P +4 / 3–4P +4, +2. Endings (2P / 3P / 4P): Market Collapse 29.5 / 32.2 / 31.0%, Singularity 34.8 / 30.3 / 26.7% (2P guardrail met), Patient Zero 32–42%; rounds 8.24 / 8.25 / 7.94; spread 41 / 31 / 32 pts; AdaptiveBalanced 69 / 48 / 42%.
- Green base 2 rejected (Green path 21 / 13% at 3P/4P). The slot cap of 2 is inert. Yellow MS vs MS_ALT are within noise.
- **Yellow still weak** (16% / 10% at 3P / 4P): Yellow seats end with the lowest Market Share, since Red exits strip their income-phase gains. They bank 2.5–3 fewer Secret-face Secrets. Bot purchase scoring values Yellow as Money (selection bias toward weak bots).
- **User decisions pending:** C2 adoption; Green base 3; slot cap; Yellow profile; Yellow bot fix vs rules probe; 4P 7.9 rounds; 2P spread.
**User decisions (2026-11-08) on §43.1:** (1) adopt C2: v038b + starting Market Share 14 at all player counts + Market Leader Bonus 2P +4 / 3–4P +4, +2, for the 1,200-game confirm sweep and the ref1 check. (2) Green base 3. (3) Keep `glitched_slots_per_round_cap` in code, default off, out of the rules. (4) Yellow F1 stays `+2 Market Share` for now. (5) Fix bot Yellow valuation first, then re-measure. (6) Accept 4P 7.9 rounds for now. (7) Accept the 2P spread for now; re-check with ref1 at 2P.

### 43.2 C2 confirm sweep (`v038b`, 1,200 games per pod)

Source: `sim_results/v380_secret_faces/c2/sweep_report.md`. Endings (2P / 3P / 4P): Singularity 33.8 / 27.4 / 25.3%, Patient Zero 33.7 / 39.6 / 39.9%, Market Collapse 29.1 / 32.8 / 34.6%, Total Wipeout 3.4 / 0.2 / 0.2%. Rounds 8.15 / 8.16 / 7.92. 2P Singularity guardrail met. Archetype spread 35.7 / 38.2 / 33.3 pts (v037 26.9 / 36.1 / 34.1); AdaptiveBalanced 68.9 / 53.2 / 43.3%. Company Red leads by 8–13 pts at 3P/4P; Yellow path 39.4 / 20.8 / 12.1%. ref1 non_reference (lever A off, as the preset): 3P 84.1%, 2P 92.4%. The comparable baseline is 78.6% (switch-off), since rule sweeps run with lever A off. Correction: the first sweep's v037 rows omitted Market Collapse (2P 25.0 / 3P 20.9 / 4P 27.1%).

### 43.3 C2 assessment: APPROVED WITH TUNE (`docs/findings/v380_balance_assessment.md` "C2 confirm", probes T1–T4)
- ref1 rise (3P 84.1 / 2P 92.4%) is a bot skill gap, not an exploit. The ref seat alone triggers Market Collapse in 4–5% of games, at no more than its normal win rate. It is the only seat that blocks Red and climbs Public Relations. With lever A on for the rivals, ref still wins 79.2%.
- Red Company lead is a rule effect: the yield of 3 at 11+ stacks with Red F1 `+1 Market Share`. T4 (Red 2/2/1/0) flattens the Company lead but moves the 3P lead to the Green path (49%). Note: the User already rejected 2/2/1/0 (dead top tier).
- 4P Market Share 15 (T2): 7.92 → 8.01 rounds. Lever A on for all bots (T1) rejected (spread 47–52). Market Leader Bonus `+3, +1` (T3) trims the 3P spread 38 → 32.
- Yellow unchanged by any probe (9–21%). Orchestrator note: the Yellow bot purchase scoring was already moved off Money in §14.4; the remaining gap is mostly roster selection (VentureGreed / RecklessSaboteur).
**User decisions (2026-11-08) on §43.3:** (1) ref1 rise accepted as a bot skill gap; C2 values become the v0.38 ref1 baseline (3P 84.1%, 2P 92.4%). (3) Starting Market Share 15 at 4P. (4) Market Leader Bonus 3–4P trimmed to `+3, +1` (2P stays +4). (5) Yellow needs a rules fix (design open). (6) 2P archetype spread ~36 accepted. (2) Red to be rethought (design open). (7) C2.1 sweep and Phase B wait until Red and Yellow are resolved.

### 43.4 Red rethink: shared Market Share payout (User design, 2026-11-09; pre-SDLC, not modelled yet)
- Red Secret face no longer pays its owner by Market Share tier. Each Red die that leaves a Processing Box advances a shared table counter by 1. Every *n* Red dice banked, a payout fires: all surviving players score by Market Share place (draft: 1st 3 / 2nd 1 / others 0 Corporate Secrets; ties share the better place).
- This payout replaces both the `v2.0` Market Share comparison (Money) and the Market Leader Bonus. One more payout fires at game end, except when the game ends by Market Collapse (and, as now, not on a Total Wipeout).
- No new glossary term yet; the counter will need a name (User to approve).
- Open for modelling: owner reward per Red die banked (+1 Corporate Secret vs none); *n* per player count; payout in Secrets only or Secrets + Money; stalling (holding Red dice in the Processing Box); Yellow as the Market Share die under this rule.
- **Model results (game-designer, 2026-11-09; scratchpad patch over v038b, 600 games per cell; assessment doc "Red shared payout"):** Red banking volume is low (1.3–4.3 per game), so n = 2 gives only 1.0–1.7 payouts and n = 3 is near inert. Recommended "RSP-1": owner +1 Corporate Secret per Red Secret; n = 1 (every Red Secret banked fires a payout); payout 1st +3 / 2nd +1 in Secrets only; end payout except on Market Collapse / Total Wipeout; starting Market Share 16 / 16 / 17; Yellow F3 → `+$1 & +1 Market Share`; oldest-first Conveyor Triage (anti-stall). Result (2P / 3P / 4P): Market Collapse 36 / 41 / 38%, Singularity 44 / 42 / 44%, Patient Zero 18 / 16 / 18%; rounds 8.55–8.69; archetype spread 25–28; Company colours within ~6 pts; Yellow path 39 / 24 / 16%. With owner 0, Red is unplayable (7–24%); folding Money in changes ≤3 pts. Stalling is analytically real for a trailing Red owner (ref1 not run; bots not payout-aware). With n = 1 no counter is needed.
- **User decision (2026-11-09): RSP-1 adopted** as the next v0.38 candidate. Package (on top of C2 / v038b):
  - Owner +1 Corporate Secret per Red Secret banked (replaces the Red tiers).
  - Every Red Secret banked fires a payout: survivors score 1st +3 / 2nd +1 / others 0 Corporate Secrets by Market Share place; ties share the better place.
  - One end payout, except on Market Collapse / Total Wipeout.
  - Market Leader Bonus and the `v2.0` Market Share comparison removed.
  - Starting Market Share 16 / 16 / 17.
  - Yellow F3 `+$1 & +1 Market Share`.
  - Conveyor Triage takes Processing Box dice oldest first.
  - Starting Secrets 3 / 4 / 4, with 2 / 3 / 4 probed in the sweep.
  - Bot work: payout-aware Market Share valuation (blocking, Public Relations Track) and a ref1 rollout for the new rule.
  - No counter, so no new term. Glossary impact for Phase B: Market Leader Bonus and the v2.0 comparison retired; the payout needs rules wording within existing terms (confirm with the User if a name is wanted).
- **Payout timing A/B (game-designer, 2026-11-09; `docs/findings/rsp1_ab_model.py`, results `rsp1_ab_results.json`; 600 games per cell, seeds 42–641, Yellow F3 corrected, oldest-first triage):** A = payout per Red Secret banked, B = at most one payout per round (end of Phase 5, if any Red Secret banked that round; Market Share after Phase 4). Rounds with ≥2 Red banks 0.9 / 1.9 / 4.0% (2P / 3P / 4P); payouts per game A 1.98 / 2.54 / 3.50 vs B 1.89 / 2.36 / 3.09. End reasons (~41 Singularity / 19 Patient Zero / 39 Market Collapse), rounds 8.5–8.7, Company colours and archetype spread unchanged (±0.02). Red path 4P .26 → .24. Carried forward in both: Market Collapse ~39% is high; Yellow path still weakest (0.66–0.71 of fair share) even with F3 corrected, so the earlier Yellow figures in this section did not include F3; a trailing player's Red bank feeds the leader; 2P lead snowball.
- **User decision (2026-11-09): variant B adopted.** Owner +1 Corporate Secret for every Red Secret banked; the Market Share place payout fires at most once per round, at the end of Phase 5. Spec §14.5 updated.
- **Bot payout valuation probe (game-designer, 2026-11-09; `docs/findings/rsp1_valuation_probe/`; v038c, mixed1, 400 games per cell):** the implemented payout valuation is mostly correct play, not a bug. A payout-aware seat vs payout-blind seats wins .596 / .457 / .467 (2P / 3P / 4P; control .507 / .337 / .252), so the payout-off "model" split (Market Collapse ~40%, Patient Zero ~17%) reflected weak bot play. Candidates: A per-round discount γ on expected remaining payouts, B replacement cap, C breach-risk weight, D = A+B. Only A γ = 0.75 beats base head-to-head at 2P / 3P without losing at 4P (seat .539 / .386 / .257). With A γ = 0.75: Market Collapse / Patient Zero / Singularity 26 / 24 / 47 (2P), 21 / 39 / 40 (3P), 13 / 47 / 40 (4P); rounds 8.42 / 8.32 / 7.99. Recommendation: `payout_round_discount = 0.75` [TUNE-BOT] in `expected_red_payouts_remaining`.
- **Open (rules, not bots):** Red Company wins .21 vs blue / green ~.39 at 3P and .12 vs ~.31 at 4P under every candidate (and trails even with payout valuation off); Red path .13 at 4P. Patient Zero is the most common ending at 3–4P. Archetype spread .10–.39 at 4P.

### 43.5 RSP-1 balance assessment (`v038c`, game-designer, 2026-11-09): APPROVED WITH TUNE (`docs/findings/v380_rsp1_balance_assessment.md`)
- Structure sound: no stalling, no ≥15-round games, archetype spread 30–32 (v038b 33–38), end split 3P 40/37/22, 4P 42/40/18 (Sing/PZ/MC).
- Red Company .21 / .15 (3P / 4P) root cause is the payout structure: owner +1 is the weakest Secret face. Red Company seats take the most payout Secrets (+1.5 to +1.8) but ~4 fewer face Secrets than in v038b, and are Patient Zero 2–2.5x as often. Company setup is not the cause.
- Probes (400 games): **F1 owner yield +2** puts Company colours at 3P .34/.34/.32 and 4P .22/.24/.29, but Singularity rises 4–9 pts (2P 52%). F2 payout 2/1 has no effect on Red; F1+F2 overcorrects (spread 37–39).
- Starting Secrets: keep 3P/4P at 4 (2/3/4 doubles games ≤4 rounds and gives Patient Zero 47%). At 2P with F1, 2 starting Secrets gives Singularity 42% but 20% short games.
- ref1 (+43.9 at 3P) uses Market Collapse as a tempo end, not as denial: it wins the same share with or without Market Collapse, and a hypothetical end payout changes its win rate by ≤1.2 pts. Not a rules hole; degenerate-strategy WATCH.
- User decisions: F1; 2P Singularity lever; Starting Secrets; Market Collapse end-payout exception; ref1 gap.
- **Owner yield +2 confirm sweep (product-owner, 2026-11-09; `sim_results/v380_rsp1_y2/sweep_report.md`; v038c + `red_secret_owner_yield=2`, 1,200 games per cell, seeds 42..1241):** Red / Blue / Green Company wins 3P .33 / .34 / .34, 4P .25 / .24 / .26 (was .21 / .38 / .40 and .15 / .30 / .31). 2P Singularity 50.2% at starting Secrets 3 (FAIL) and 42.4% at 2 (PASS, but 19.7% of games ≤4 rounds). Singularity 3P 43.8 / 4P 47.3%; archetype spread 3P 36.4 / 4P 33.4 pts (was 32.4 / 31.0). Red Company still the likeliest Patient Zero at 3P (18.8% vs ~9.5%). ref1 edge 3P +49.6 / 2P +41.8 (was +43.9 / +38.6), Market Collapse still 50–60% of ref1 games. No stalling.
- **User guidance (2026-11-09):** Company colour balance is judged by win rate parity. Per-colour differences in how seats win or lose (e.g. Red Company's higher Patient Zero rate under owner yield +2) are acceptable — players discover and manage them. With +2, colour win rates are at parity at 3P / 4P, so the Red Company concern is closed.
- **2P Singularity lever probe (game-designer, 2026-11-09; `docs/findings/rsp1_2p_lever_probe/`; v038c + owner yield 2, 600 games, seeds 42..641):** 2P starting Market Share 13 → Singularity 42.2% (PASS, at the line), Market Collapse 25.5 → 36.0%, rounds 8.41, ≤4-round share unchanged (8.8%), colour parity unchanged; MS 14 45.8% (watch), MS 12 36.2%. Flat Corruption Track capacity 6: 39.5% but +2 rounds and wider colour spread (needs a new per-count lever). Payout (2,1) / (2,0) and v1.0 pulse 0 rejected. `corruption_track_capacity_by_player_count` is not read by the engine. 3P Market Share 14: Singularity 44.0 → 37.5%, no side effects. Recommendation: 2P starting Market Share 13 (existing knob), confirm at 1,200 games.
- **2P Market Share 13 confirm (product-owner, 2026-11-09; `sim_results/v380_rsp1_y2_ms13/sweep_report.md`; owner yield 2, 1,200 games, seeds 42..1241):** 2P Singularity 50.2 → 39.0% (PASS); Market Collapse 27.6 → 38.9%; rounds 8.33; ≤4-round share unchanged (9.2%); colours R / B / G 51.3 / 45.9 / 52.8; archetype spread 27.5. ref1 edge +42.9 (unchanged), but ref1 games now end by Market Collapse 77.6% (was 60.1%).
- **User decisions (2026-11-09):** v038c preset locked at owner yield 2 and 2P starting Market Share 13 (commit 5351479). Starting Secrets stay 4 at 3P / 4P. Mixed-roster bots are to be taught the early Market Collapse play that ref1 uses (bot-only work; game-designer scoping first). End payout on Market Collapse: more information requested, still open.
- **User decision (2026-11-09): end payout fires on Market Collapse endings too** (still none on a Total Wipeout). Simplifies the rule and weakens deliberate tanking to 0 Market Share, which stays a viable but not dominant strategy.
- **Early Market Collapse bot play scoping (game-designer, 2026-11-09; `docs/findings/rsp1_collapse_play_scoping/scoping.md`):** premise corrected. The "ref1 ends 52–78% of games by Market Collapse vs mixed1 20–39%" comparison mixed two harnesses (`run_reference_bot_validation.py` has no Client Companies / White Hats / Variants and shows high Collapse for every roster). On the same harness ref1's Collapse share matches the roster's and ref1 ends at 0 Market Share about half as often as a Mixed seat; its collapses are late (rounds 8–10) via the existing lever A Market Share dump, not an early dive. No trigger rule tested beats the control (lead-based dumps cost Mixed 3–8 pts under RSP-1). ref1 on the sweep harness: +43 (3P) / +42 (2P); the edge comes from search elsewhere (Phase 6 plan choice, Phase 4 Public Relations push). §14.5.10 left mixed1 endings unchanged. Recommendation: drop the collapse-play bot work; compare ref1 and mixed1 on the same harness from now on.
- **User decision (2026-11-09):** collapse-play bot work dropped. Next: Phase B (RULES.md, glossary, PnP, web) for v038c.
- **User decision (2026-11-09):** the Red Secret payout reuses the existing term **Market Leader Bonus** (rewritten: fires at the end of Phase 5 in any round a Red Secret is banked, plus once at game end except on a Total Wipeout; 1st +3 / 2nd +1). No new term.
- **User decisions (2026-11-09, Phase B wording):** Company starting die stays plain words ("starting colored die"), no term; Defensive Shield Sacrifice retired in v0.38.0; a Secret face die leaving the Processing Box "banks" its Secret (plain verb, not a glossary term).

## 44. Phase 50 Post-Telemetry Balance Assessment: `G2 — Universal Sandbox` Redesign (`v0.38c`): APPROVED

Sources: `docs/specs/g2_universal_sandbox_spec.md`, `docs/findings/g2_universal_sandbox_analysis.md`, `sim_results/g2_universal_sandbox/validation_report.md` (24 cells × 600 games = 14,400 games across 2P/3P/4P, Standard & Aggressive profiles, `RANDOM / G1 / G2 / G3`, seeds 42..641).

- **Context & Design Rationale:** During v0.38 shield normalization, `G2 — Universal Sandbox ($4)` was temporarily collapsed into the exact same placeholder as `G1 — Self-Healing Kernel ($5)`: `Clean 1 Glitched Shield Slot + gain +1 🔬`. This created an overpriced trap ($5 for identical effect) and redundant mechanics. User approved Option D2 from the pre-SDLC analysis: `[In Production — Income] Gain +2 🔬, plus +1 🔬 for each of your Glitched Shield Slots [TUNE]` (Phase 1 Step 5 cleaning removed; `clean_slots=0`).
- **Mathematical Modeling & Zero-Blank Compliance:** In Phase 3 Income, players carry 0 glitched shield slots ($g=0$) in 82.4% of rounds (and 98.6% in Rounds 1–3). The pure proposal (`+1 🔬 per glitched slot`) would produce a blank face (0 🔬, $0) in over 82% of activations with a meager EV of 0.21 🔬. The implemented `+2 🔬` base ensures compliance with the "Zero Blank Faces" design pillar, scaling to `+3 🔬` ($g=1$, 14.2% PMF) and `+4 🔬` ($g=2$, 3.4% PMF) under attack.
- **Empirical Yields & Parity:** In the 14,400-game validation sweep, realized G2 activations yielded **2.51–2.61 🔬** in Standard and **2.77–2.85 🔬** in Aggressive. In 45.7%–60.0% of realized triggers, $g=0$, proving the `+2 🔬` base was indispensable. G2 sits in near-perfect nominal parity (~2.6 🔬) against `G3 — Live Reboot` ($4: `+2 🔬 + $1`, nominal ~3.0).
- **Market Viability & Buyer Win Rates:**
  - `G1 ($5)`: 0.18–0.29 buys/seat, 11.7%–17.0% buyer share, 17.8%–50.0% buyer win rate.
  - `G3 ($4)`: 0.41–0.64 buys/seat, 24.8%–34.1% buyer share, 26.1%–51.3% buyer win rate.
  - `G2 ($4)`: **0.36–0.54 buys/seat**, **23.1%–29.9% buyer share**, **24.5%–49.1% buyer win rate** (exact fair-share parity: 2P 49.1% [fair 50%], 3P 35.4% [fair 33.3%], 4P 27.1% [fair 25%]). G2 is a highly viable, competitive choice without becoming a dominant must-buy.
- **Company Win Rate Parity:** Under G2, starting Green companies (Omnidyne & Helix) achieve tight win rate parity across all pods: 2P 48.0% / 50.2%, 3P 34.3% / 34.4%, 4P 26.2% / 25.9%. Overall Company color split (Red / Blue / Green) under G2 is 2P 55.1 / 45.9 / 49.1%, 3P 32.5 / 33.1 / 34.4%, 4P 24.7 / 24.2 / 26.1% (within noise of fair share).
- **Pacing & End Triggers:** Mean rounds 8.24–8.39 across all pods; 0.0% timeouts. End triggers under G2 Standard: 2P Singularity 42.7% (below ≤48% guardrail), PZ 18.5%, MC 35.5%, TW 3.3%; 3P Sing 45.8%, PZ 33.0%, MC 21.0%, TW 0.2%; 4P Sing 49.5%, PZ 33.5%, MC 17.0%, TW 0.0%. Pacing and existential tension are identical within noise to G3 and Random modes.
- **Anti-Degeneracy Proof:** Maximum active glitches observed across 14,400 games was 3 ($<2\%$ of rounds). Stalling to farm research was non-existent because unblocked Blue cubes threaten Patient Zero elimination, unblocked Red cubes threaten Market Collapse, and each glitched slot directly penalizes banked Green Secrets ($3 - g$ Secrets, where 1 Secret = 1 VP = ~3 🔬).
- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.38c`).** No further tuning required; G2 redesign locked.

## 45. Phase 51 Package `v0.38d` Balance Assessment: Early-Game Tension & Green-Clean Variant B: APPROVED

Sources: `docs/findings/early_game_pressure_modeling.md`, `docs/findings/c2_green_clean_analysis.md`, `docs/specs/v380d_c2_green_clean_spec.md`, `sim_results/shogun_tower_comparison/comparison_report.md` (3,600 games), `sim_results/v380d_c2_green_clean/validation_report.md` (3,600 games across 2P/3P/4P, Standard and Aggressive bot profiles, seeds 42..641).

- **Context & Design Problem:** Physical testing with the *Shogun* Cube Tower revealed that the legacy simulation (`LEDGE_AVALANCHE`) over-estimated early round damage by +33% and ignored baffle retention. Once calibrated (`SHOGUN_BAFFLE`), the opening rounds under `v0.38c` became too calm: with 2 clean Shield Slots and starting dice allocations, players trivially blocked all incoming attack cubes through `v1.0` and into `v2.0`, removing early-game decision tension and failing to tutorialize defensive triage.
- **Implemented Package (`v0.38d` — Candidate C2 + Green-Clean Package, Variant B):**
  1. **Shogun Baffle Tower Physics:** Validated two-state physical retention model ($p_{\text{exit}} \approx 0.70$ empty, retention scaling with stuck cubes $S$, avalanche regime at $S \ge 3$ or $F+S \ge 7$).
  2. **Candidate C2 Early-Game Tuning:**
     - Setup priming: 4 cubes (`1R, 1B, 1G, 1K`).
     - `v1.0` Staging Cup Payload: 4 attack cubes (`2R, 1B, 1G` on *Script Kiddie*; `1R, 2B, 1G` on *Data Scraper*).
     - Starting Glitched Shield Slot: Every player begins with **1 Glitched Shield Slot** on their Company Terminal Mat (1 clean, 1 glitched out of baseline Defense Capacity 2).
  3. **Removal of Passive CI/CD Auto-Clean:** Graduation from Scanned Box to Ready for Release in Phase 5 Step 3 no longer cleans a glitched slot (`slot_graduation_clear = 0`). Slot cleaning is strictly active.
  4. **Green Die Specialization:** Green Face 1 converted from `Clean 1 Glitched Shield Slot / +$1` to `+2 🔬` (`V038D`), establishing Green as the premier research engine.
  5. **Variant B Green Banking Slot Clean:** When a Green die leaves the Processing Box and banks its Secret, it yields $Y = \max(0, 3 - g)$ Corporate Secrets (calculated on pre-clean glitched slots $g$), then cleans 1 Glitched Shield Slot. Variant B prevents the runaway Green company dominance observed under Variant A (49.6% win rate).
- **Monte Carlo Validation Metrics (3,600 Games):**
  - **Game Pacing:** Mean rounds **8.73–8.94** across 2P/3P/4P (target 8.5–9.5). Zero timeouts (0.0%).
  - **End Trigger Distribution:**
    - **Singularity:** **36.4%–42.4%** (target 35%–48%).
    - **Patient Zero:** **19.3%–30.6%** (target 20%–35%).
    - **Market Collapse:** **26.3%–43.0%** (target 18%–35%).
    - **Total Wipeout:** **0.8%–1.3%**.
  - **Slot Cleaning Mechanism Breakdown:**
    - Graduation auto-cleans: **0.00** across all player counts (passive clean successfully eradicated).
    - Active die cleans (Phase 1 Step 5 assignment): **5.23–5.33** slots cleaned per player per game.
    - Green Secret triage cleans: **0.69–0.79** slots cleaned per player per game.
  - **Company & Color Win Rate Parity:**
    - 2P: Red 53.6%, Blue 46.8%, Green 49.6%.
    - 3P: Red 30.6%, Blue 30.6%, Green 38.9%.
    - 4P: Red 24.3%, Blue 22.4%, Green 28.2%.
    All color win rates remain within healthy competitive bounds without any single dominant color.
  - **Early Round Pressure ("Tutorialization"):** In Round 1, players face an average of 1.4 incoming attack cubes with only 1 active clean Shield Slot. Players must make meaningful trade-offs from Turn 1: whether to dedicate their starter die to blocking, take damage, or accept a glitched slot penalty.
- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.38d`).** Package `v0.38d` meets all design pillars, tension targets, and balance criteria.

## 46. Phase 52 Secret Simplification & Processing Triggers: APPROVED (`v0.38e`)

Sources: `docs/specs/v380e_secret_simplification_spec.md`, `sim_results/v380e_secret_simplification/validation_report.md` (3,600 games across 2P/3P/4P, seeds 42..1241, mixed roster with `MixedPolicyBot`).

- **Context & Design Problem:**
  Under `v0.38d`, Secret face banking suffered from cognitive overhead and balance asymmetry:
  1. *Blue Tracking & Low EV:* Banking Blue required mid-round memory tracking in Phase 4 Step 1 (*"Remember how many Blue cubes you blocked this round"*), broke timing equivalence for Phase 3 instant-banking (*B3 Air-Gapped Backup*, *Jumper Diagnostics*), and depressed Blue Secret EV to 1.458 Secrets/bank (zero Blue cubes blocked in 61.9% of rounds), dragging 4P Blue Company win rate down to 20.3%.
  2. *Green Calculation Friction:* Green Secret yield ($Y = \max(0, 3 - g)$ before cleaning $g \leftarrow \max(0, g-1)$) created order-of-operation confusion, runaway early-game payouts (3 Secrets), and feel-bad late-game zeroes (4.4% of banks).
- **Implemented Package (`v0.38e`):**
  1. *Universal Baselines:* Red, Blue, and Green dice bank an unconditional baseline yield of **`+2` Corporate Secrets**; Purple Specialist banks flat **`+1` Corporate Secret**.
  2. *Four Dedicated Domain Triggers (Fired Upon Leaving Processing Box):*
     - **Red (Market Domain):** Sets `state.red_secret_banked_this_round = True`, firing the **Market Leader Bonus** (1st `+3`, 2nd `+1` Corporate Secrets) once at the end of Phase 5.
     - **Blue (Hardware Defense Domain):** Evaluates Defense Grid Track; awards **`+1` Corporate Secret if Defense Grid $\ge$ Level 3** (max `+3`). Zero cube tracking or attack dependencies.
     - **Green (System Integrity Domain):** Unconditionally cleans **`1` Glitched Shield Slot** ($g \leftarrow \max(0, g - 1)$). Zero yield penalty.
     - **Purple (Proprietary Specialist Domain):** Pure baseline (`+1` Corporate Secret, no domain trigger).
  3. *Rules Simplification:* Cleanly excised the Phase 4 Step 1 Blue tracking reminder and Phase 3 instant-banking timing exceptions from `RULES.md`.
- **Monte Carlo Telemetry Metrics (3,600 Games):**
  - **Game Pacing:** Mean rounds **8.84** (2P), **9.00** (3P), **9.04** (4P) — aggregate **8.96** rounds, perfectly centered in the 8.5–9.5 target window. 0.0% timeouts.
  - **Healthy End Trigger Triad:**
    - **Singularity:** **37.25%** (2P), **44.67%** (3P), **45.92%** (4P) — aggregate **42.61%** (target 30%–50%).
    - **Patient Zero:** **17.92%** (2P), **28.67%** (3P), **28.42%** (4P) — aggregate **25.00%** (target 15%–35%).
    - **Market Collapse:** **43.25%** (2P), **26.08%** (3P), **25.42%** (4P) — aggregate **31.58%** (target 15%–45%).
    - **Total Wipeout:** **1.58%** (2P), **0.58%** (3P), **0.25%** (4P) — aggregate **0.81%** (guardrail $\le 3.0\%$).
- **Telemetry Invariant Confirmations (40,473 Banking Events):**
  - **Red Invariant (`INV-V38E-05`):** 100.0% yielded exactly 2 Secrets (13,336 / 13,336).
  - **Green Invariant (`INV-V38E-04`):** 100.0% yielded exactly 2 Secrets (12,463 / 12,463).
  - **Purple Invariant (`INV-V38E-06`):** 100.0% yielded exactly 1 Secret (16,607 / 16,607).
  - **Blue Invariant (`INV-V38E-01/02`):** 100.0% yielded $\in \{2, 3\}$ (8,046 / 8,046: 92.18% at 2, 7.82% at 3).
  - **Blue L3+ Grid Trigger:** 7.82% aggregate trigger rate (2P 6.35%, 3P 8.24%, 4P 8.28%), providing a meaningful hardware reward without distortion.
  - **Green Decontamination Efficiency:** 0.914–1.020 slots cleaned per seat (~0.95 slots/seat aggregate; 82.3%–85.8% clean efficiency when glitched slots were present).
  - **EV & Competitive Parity:** Blue Secret EV increased from 1.458 to 2.077 (+0.619), restoring Blue Company win rates (2P 45.0%, 3P 31.2%, 4P 22.5%) and dominant path win rates (2P 43.8%, 3P 37.1%, 4P 26.7%) to healthy parity.
- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.38e`).** Cognitive friction and memory tracking are eliminated while preserving tight pacing, healthy existential triad distributions, and strong multi-path strategic depth.

## 47. Phase 53 Blue Module Die Rebalance: APPROVED (`v0.38f`)

Sources: `docs/specs/v380f_blue_dice_rebalance_spec.md`, `sim_results/v380f_blue_dice_rebalance/validation_report.md` (3,600 games across 2P/3P/4P, seeds 42..1241, config `v038f_roster` with `MixedPolicyBot`).

- **Context & Design Problem:**
  Across prior iterations (`v0.38` through `v0.38e`), Blue module dice suffered from identity confusion and suppressed adoption:
  1. *Redundant Research Overlap with Green:* Blue featured research on Faces 1, 2, and 4 (`+1 🔬`), functioning as an inferior duplicate of Green rather than embodying the "Firewall / Data Vault" archetype.
  2. *Asymmetric Secret Banking Latency:* Red provided immediate Phase 3 cash/Market Share and banked high-yield Secrets in Phase 5. Blue Secret generation relied entirely on Face 5 navigating the Processing Box conveyor latency, penalizing Blue starter companies (DTO, Aegis) in early-round survival and tempo.
  3. *Market Neglect & Win Rate Gap:* In `v0.38e`, Blue purchases lingered at only ~0.18–0.20 per seat, and 4P Blue Company win rate sat at 22.45% (below fair 25.0%).
- **Implemented Package (`v0.38f`):**
  1. *Direct Corporate Secrets on Faces 1 & 2:* Converted Blue Faces 1 & 2 from `+1 🔬` to unconditional **`+1 Corporate Secret`** directly awarded in Phase 3 Income (`"blue_face"`), bypassing the Processing Box.
  2. *50% Secret Density Profile:* Blue dice now feature 3 of 6 faces generating Corporate Secrets (Faces 1 & 2 direct income, Face 5 banked deferred yield), establishing Blue as the premier VP and defensive buffer module.
  3. *Topology Preservation:* Face 3 (`+$1`), Face 4 (`+1 🔬 / +$1`), Face 5 (`Secret face` yielding 2 Secrets, +1 if Defense Grid $\ge$ L3), and Face 6 (`Blue ★` Variant) remained intact.
- **Monte Carlo Telemetry Evaluation (3,600 Games):**
  - **Pacing & Tension:** Mean game length lands squarely in the 8.5–9.5 round target window: **8.93** (2P), **9.44** (3P), **9.26** (4P) — aggregate **9.21** rounds.
  - **End-Game Triad Stability:**
    - **Singularity:** **38.17%** (2P), **52.08%** (3P), **50.25%** (4P) — aggregate **46.83%** (target 30%–55%).
    - **Market Collapse:** **44.92%** (2P), **28.83%** (3P), **27.00%** (4P) — aggregate **33.58%** (target 15%–45%).
    - **Patient Zero:** **15.67%** (2P), **19.08%** (3P), **22.75%** (4P) — aggregate **19.17%** (target 15%–35%).
    - **Total Wipeout:** **1.25%** (2P), **0.00%** (3P), **0.00%** (4P) — aggregate **0.42%** (guardrail $\le 2.0\%$).
  - **Company Color Win Rate Parity:**
    - **2P:** Blue (DTO/Aegis) **49.06%** vs Green 54.69%, Red 46.15% (fair share 50.0%, within $\pm 5.0\%$).
    - **3P:** Blue **33.39%** vs Green 38.55%, Red 27.72% (fair share 33.3%, dead-center).
    - **4P:** Blue **25.33%** vs Green 28.52%, Red 21.05% (fair share 25.0%, exact theoretical parity, up from 22.45%).
  - **Market Vitality & Strategic Viability:**
    - Market purchases per seat surged: 2P **0.356** (+74.5%), 3P **0.333** (+99.4%), 4P **0.350** (+94.4%).
    - Blue Dominant Path ($\ge 60\%$ dice) win rate reached **30.46%** in 4P (up from 26.69%), confirming robust strategic viability.
    - Direct Blue Face secrets delivered **+0.771 Secrets/seat** aggregate, providing a stable survival buffer that moderately softened Patient Zero spikes without inflating game length.
  - **Invariant Adherence:** 100% compliance across all 46,103 banking events (9,371 Blue banked dice yielded strictly $\in \{2, 3\}$, with 6.23% triggering the L3+ Grid bonus).
- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.38f`).** Blue module dice have achieved complete thematic distinction, healthy market liquidity, and exact theoretical win rate parity across all player counts without destabilizing the end-game triad.

## 48. Phase 54 Post-Telemetry Balance Assessment: Unified Market Share Track & Headroom Architecture (`v0.38g` / Headroom): APPROVED

Sources: `docs/specs/market_share_headroom_spec.md`, `sim_results/market_share_headroom/validation_report.md` (3,600 games across 2P/3P/4P, seeds 42..1241).

- **Context & Design Flaw in Baseline (`v0.38d`):** In `v0.38d`, a player's starting Market Share was coupled to the track ceiling (`start == max` = 13 at 2P, 16 at 3P, 17 at 4P). This zero-headroom architecture violated Core Design Pillar 3 ("Zero Blank Faces"):
  1. Red Face 1 (`+1 Market Share / +$1`) choice rate collapsed to **0.0%** for Market Share in Round 1 (100% forced into `+$1`).
  2. Yellow Face 1 (`+2 Market Share`) was a completely blank face ($0, 0 🔬, 0 MS). Yellow Face 2 collapsed into forced research, while Yellow Face 3 and *Brand Protection* (R1 ★) wasted their `+1 Market Share` component.
  3. The Public Relations Track was mechanically locked in early rounds until unblocked Red cubes inflicted damage.
- **Architectural Solution (Candidate A4 — Unified Max 20 + Calibrated Headroom):**
  - Central board track unified with a single physical ceiling of **20** (`market_share_max = 20`) across all player counts (21 cells: 0 to 20).
  - Calibrated starting positions: **13** at 2P (+7 headroom), **16** at 3P (+4 headroom), and **16** at 4P (+4 headroom, unified with 3P).
  - Hard clamping strictly enforced: floor at `0` (triggers Market Collapse check post-Phase 4), ceiling at `20`.
- **Validation Against Core Design Pillars (3,600 Games):**
  1. **Zero Blank Faces Restored (INV-MS-HEADROOM-08 & INV-MS-HEADROOM-01/02):**
     - In Round 1, Red Face 1 selection of `+1 Market Share` over `+$1` jumped from **0.0% to 100.0%** across all player counts (target `> 30.0%`).
     - Round 1 players at maximum track dropped from **53.8%–73.3%** in baseline to **0.0%**. In Round 2, players at max remained at **0.0%** (2P) and **0.1%** (3P/4P), completely eliminating early ceiling congestion (target `< 5.0%`).
     - Headroom actively utilized: **42.5%** (2P), **54.2%** (3P), and **56.2%** (4P) of players climbed above their starting position during the game, with **1.6%–14.4%** reaching the 20 ceiling. Mean peak Market Share reached 13.89 (2P), 17.20 (3P), and 17.25 (4P). Yellow Market Share faces and PR research conversions are fully functional from Round 1.
  2. **Macro Pacing Preserved:**
     - Mean rounds played: **8.72** (2P), **9.12** (3P), and **8.90** (4P). Exactly inside the target 8.7–9.1 round window (baseline was 8.73, 8.89, 8.94).
     - Timeouts / Limit Hits: **0 (0.0%)** across all 3,600 games.
  3. **Tri-Modal End Trigger Diversity:**
     - **Singularity:** 35.7% (2P), 45.2% (3P), 39.3% (4P) — all within the $\le 48\%$ guardrail.
     - **Patient Zero:** 20.3% (2P), 27.2% (3P), 29.3% (4P) — existential breach threat remains active.
     - **Market Collapse:** 42.0% (2P), 27.1% (3P), 31.3% (4P) — healthy economic endgame pressure.
     - **Total Wipeout:** 2.00% (2P), 0.50% (3P), 0.00% (4P) — suitably rare edge catastrophe.
  4. **Company & Color Balance Equity:**
     - Starting Color Win Rates: 2P Red 56.4% / Blue 43.4% / Green 50.2% (fair 50.0%); 3P Red 39.3% / Blue 27.1% / Green 33.7% (fair 33.3%); 4P Red 33.0% / Blue 18.1% / Green 24.0% (fair 25.0%). Red starter companies enjoy early positioning agency for the Market Leader Bonus, but counter-play remains viable across Blue and Green rosters without runaway imbalance.
     - Bot Archetype Hierarchy: AdaptiveBalancedBot (40.8%–58.5%) leads; SecOpsTurtleBot (26.4%–56.5%) and VentureGreedBot (30.3%–53.4%) demonstrate competitive diversity.
  5. **Invariants & Mechanical Robustness:**
     - Invariants `INV-MS-HEADROOM-01` through `08` fully validated.
     - Floor at 0 and ceiling at 20 respected with zero overflow exceptions across all matches. Outlier seeds confirmed clean resolution on early wipeouts (seeds 87/1146 via PZ) and long engine games (seeds 254/400/650 via Singularity at Round 13).
- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.38g` / Headroom).** The headroom architecture resolves all dead face and PR track lockout defects without perturbing game length or threat curves. The candidate is approved for baseline lock and Phase B documentation / PnP asset sync.

## 49. Phase 55 Post-Telemetry Balance Assessment: Research Upgrade Limit & Track Step Costs (`v0.39.0` Candidate): APPROVED

Sources: `docs/specs/spec_research_upgrade_limit.md`, `sim_results/v390_research_upgrade_limit/validation_report.md`, `sim_results/v390_research_upgrade_limit/sweep_report.json` (3,600 games across 2P/3P/4P, seeds 42..1241).

- **Context & Design Problem in Baseline:**
  Under the pre-v0.39.0 research architecture (`(1, 2, 2, 3) 🔬` step costs and unbounded per-turn hardware upgrades):
  1. Early hardware progression suffered from steep initial friction (2 🔬 required for L2), delaying early specialization and pipeline capacity expansion.
  2. Late-game research hoarding enabled explosive single-turn bursts (players jumping 3–4 levels on tracks simultaneously), creating severe snowballing and de-synchronizing engine development from the round counter.
  3. The absence of a per-turn upgrade cap allowed degenerate multi-track hyper-engineering.
- **Architectural Solution (`v0.39.0` Package):**
  1. **Smoothed Hardware Track Step Costs:** Re-calibrated to `(1, 1, 2, 2) 🔬` across all four tracks (Defense Grid, Conveyor Triage, CI/CD Pipeline, Public Relations Track). Total track cost reduced from 8 🔬 to 6 🔬; L1 and L2 are accessible at 1 🔬 each.
  2. **Operations Turn Hardware Upgrade Limit (`max = 2`):** A strict per-turn hardware upgrade limit (`max_hardware_upgrades_per_turn = 2`) enforced in Phase 6: Operations (Item 1). Players may execute at most 2 total hardware track upgrades per turn across all tracks combined.
  3. **Independence of Market Share Regain:** PR Market Share regain in Item 2 remains completely independent of the hardware upgrade limit. Breakthrough bonuses (e.g. +$2 from Triage L2) immediately fund subsequent operations actions within the same turn.
  4. **Telemetry & Controller Guardrails:** Engine, web controller, and bot policies reject excess upgrade requests, logging them to `excess_hardware_upgrades_requested` and `RoundTelemetry.excess_hardware_upgrades_by_player`.
- **Validation Against Core Design Pillars & Balance Criteria (3,600 Games):**
  1. **Macro Pacing Preserved:**
     - Mean rounds played: **8.97** (2P), **9.39** (3P), and **9.04** (4P) — all solidly inside the canonical 8.5–9.5 round target window (baseline was 8.93, 9.29, 9.03).
     - Timeouts / Limit Hits: **0 (0.0%)** across all pods.
  2. **Tri-Modal End-Game Stability:**
     - **Singularity:** 38.8% (2P), 52.0% (3P), 44.3% (4P) — aggregate 45.0% (target 30%–55%).
     - **Market Collapse:** 45.0% (2P), 25.9% (3P), 29.4% (4P) — aggregate 33.4% (target 15%–45%).
     - **Patient Zero:** 15.3% (2P), 21.9% (3P), 26.2% (4P) — aggregate 21.1% (target 15%–35%).
     - **Total Wipeout:** 0.92% (2P), 0.17% (3P), 0.00% (4P) — aggregate 0.36% (guardrail $\le 2.0\%$).
  3. **Track Progression & Smoothing:**
     - Mean hardware upgrades per seat increased from 3.06–3.53 to **3.98** (2P), **4.66** (3P), and **4.25** (4P) (+0.92 to +1.13 upgrades/seat), confirming enhanced hardware liquidity from 1 🔬 step costs.
     - L3 Breakthrough achievement surged: **62.6%** (2P, +12.2%), **70.9%** (3P, +12.2%), and **64.3%** (4P, +11.1%), ensuring players reliably access mid-game track powers.
     - L4 Capstone achievement increased to **45.2%** (2P), **54.7%** (3P), and **48.8%** (4P) (+18.8% to +23.6%), rewarding focused endgame specialization.
     - **Anti-Snowball Guardrail:** Players maxing 2+ tracks held strictly to **0.00%** across all pods (target $< 10.0\%$). Hyper-engineering runaway is completely suppressed.
  4. **Turn Limit Enforcement & Telemetry:**
     - In simulated bot matches, research policies naturally throttled want-lists at `max = 2` (TEST-RUL-08); engine telemetry confirms 0 overflow violations under compliant policies while unit tests TEST-RUL-02 and TEST-RUL-06 verify exact truncation and telemetry logging when 3+ upgrades are submitted.
     - Burst multi-level jumps in a single turn are eradicated, pacing upgrades across rounds.
  5. **Public Relations Track Defense & Telemetry:**
     - Market Share regains averaged **1.95** (2P), **2.36** (3P), and **2.46** (4P) points per seat, powered by **5.85 🔬–7.37 🔬** invested in PR.
     - Red cube block rate held steady at **18.0%** (2P), **21.3%** (3P), and **21.9%** (4P), providing active economic self-defense against unblocked Red cube pressure (mean share lost 12.36–12.82 points).
  6. **Company Equity & Archetype Viability:**
     - Starting Color Win Rates (3P): Red **31.7%** / Blue **33.6%** / Green **34.5%** (fair share 33.3%, all within $\pm 1.7\%$).
     - Starting Color Win Rates (4P): Red **27.4%** / Blue **22.9%** / Green **24.7%** (fair share 25.0%, all within $\pm 2.5\%$).
     - Starting Color Win Rates (2P): Red **50.1%** / Blue **48.7%** / Green **51.2%** (fair share 50.0%, dead-center).
     - Client Company win rates remain balanced: Omnidyne (26.9%–56.9%), Aegis (27.5%–53.0%), Prometheus (28.1%–50.6%), Meridian (26.7%–49.5%), Helix (22.5%–46.0%), DTO (18.1%–44.6%).
     - Competitive archetype diversity maintained: AdaptiveBalanced (46.5%–71.0%), SecOpsTurtle (26.9%–53.7%), VentureGreed (24.2%–52.1%), Accelerationist (19.6%–52.4%), MixedPolicy (25.2%–47.6%).
- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.39.0`).** The Research Upgrade Limit (`max = 2`) and Track Step Costs `(1, 1, 2, 2) 🔬` successfully smooth early track progression, cap runaway hyper-engineering, and maintain rock-solid macro pacing and tri-modal endgame tension. Recommended for canonical lock in `RULES.md` and release as `v0.39.0`.

## 50. Phase 56 Post-Telemetry Balance Assessment: Gameplay Balance, CI/CD Pipeline Re-Sequencing, Scanned Staging, Dual Economy ($ vs 🔬), Triage Backpressure, and Green Cube Cap (`v0.40.0` Baseline): APPROVED

Sources: `docs/findings/v400_playtest_feedback_modeling.md`, `docs/specs/v400_gameplay_balance_spec.md`, `sim_results/v400_gameplay_balance/validation_report.md`, `sim_results/v400_gameplay_balance/sweep_report.json` (3,600 games across 2P/3P/4P, seeds 42..1241).

- **Playtest Feedback Background & Modeling Rationale:**
  A two-player physical playtest session (DTO + Prodigy vs Omnidyne + Phreaker) revealed five systemic balance and pacing bottlenecks:
  1. *Economic Divergence:* Research (`🔬`) suffered from continuous over-demand (hardware tracks + PR regain), while Cash (`$`) quickly saturated due to per-turn purchase limits and pipeline bottlenecks, leaving players hoarding `$15–$25+` with no late-game utility.
  2. *Phase Order Latency:* Executing Pipeline Shift in Phase 5 and Operations in Phase 6 created an artificial full-round delay before hardware upgrades (Triage/Release) took effect.
  3. *Zero Early Pipeline Backpressure:* Starting Triage Bandwidth at 2 allowed virtually all rolled Secrets (0.30/round natural) to exit Processing instantly with zero queueing tension.
  4. *Purchased Dice Pool Surges:* Market dice bypassing Scanned directly into Ready allowed unearned rolling pool expansion without Release Bandwidth investment.
  5. *Defensive Blackout Spirals:* Uncapped circulating Green cubes (6–8) systematically overwhelmed the 2–4 slot Defense Grid (1 pre-glitched), causing permanent defense collapse against Red and Blue attacks.

- **Architectural Solution & Implementation Batches (`v0.40.0` Package):**
  1. **Batch 1 (CI/CD Pipeline Flow & Phase Re-Sequencing):**
     - *Phase Swap:* Phase 5 is now Operations (clockwise turns) and Phase 6 is CI/CD Pipeline Shift (simultaneous). Upgrading hardware in Operations provides immediate throughput gratification in the same round's Pipeline Shift.
     - *Scanned Staging:* All purchased Central Market colored dice (`$4–$6`) enter the Scanned Box (Static Analysis) instead of Ready for Release, gating rolling pool expansion behind Release Bandwidth.
     - *Triage Track Recalibration:* Bandwidth re-indexed to `(1, 1, 1, 1, 2)`. Levels 0–3 enforce Bandwidth 1 (generating meaningful FIFO backpressure when multiple Secrets or glitched contractors appear); Level 2 awards a `+1 Corporate Secret` milestone; Level 4 Capstone unlocks Bandwidth 2.
     - *End-of-Round Market Leader Bonus:* Shifted to Step 5 of Phase 6, triggered when a Red Secret is banked via Conveyor Triage, evaluating final Market Share positions established during Phase 5 Operations.
  2. **Batch 2 (The Dual Economy & PR Track Regain):**
     - *Cash PR Regain:* Regaining Market Share in Phase 5 Operations shifts from Research to Cash, costing strictly **`$3` Cash per `+1` Market Share**.
     - *PR Track Bandwidth:* PR Track dictates per-turn marketing limits: L0–L1 max `1 MS`, L2–L3 max `2 MS`, L4 max `3 MS`. Breakthrough L1 grants `+$3` Liquid Cash; Breakthrough L3 unlocks the 2nd Purple Specialist die.
     - *Hardware Step Costs:* Re-calibrated to **`(1, 2, 2, 3) 🔬`** ($8\text{ 🔬}$ total per track) to absorb freed research while maintaining the strict `max 2 hardware upgrades per turn` cap.
     - *Card Cash Sinks:* *R2 Ad Campaign* (`$4`) provides `$2` Cash per `+1` Market Share (bypassing PR limits); *Y1 Algorithmic Trading* and *B2 Deep R&D Vault* serve as alternative cash sinks for Secrets.
  3. **Batch 3 (Threat Pool & Green Cube Cap):**
     - *Global Green Cube Cap:* Hard cap of **5 Green cubes maximum** in circulation across setup and all SETEC Version cards combined. Prevents permanent shield blackouts while maintaining attrition pressure.
     - *Asymmetric SETEC Profiles:* Version cards structured into distinct threat branches (Alpha: Red extortion, Beta: Blue data theft, Gamma: structural sabotage with Green cap).

- **Validation Against Core Design Pillars & Balance Criteria (3,600 Games):**
  1. **Macro Pacing & Game Length Preserved:**
     - Mean rounds played: **9.01** (2P), **9.31** (3P), and **9.04** (4P) — centered directly within the canonical 8.5–9.5 target envelope (baseline 8.97, 9.39, 9.04).
     - Round range: 1–13 (2P), 2–14 (3P), 2–13 (4P).
     - Timeouts / Limit Hits: **0 (0.0%)** across all 3,600 candidate games.
  2. **Healthy Tri-Modal End-Game Distribution:**
     - **Singularity:** **37.4%** (2P), **45.5%** (3P), **37.8%** (4P) (aggregate ~40.2%, target 30%–55%).
     - **Market Collapse:** **48.0%** (2P), **32.5%** (3P), **35.1%** (4P) (aggregate ~38.5%, target 25%–50%).
     - **Patient Zero:** **14.0%** (2P), **22.0%** (3P), **27.1%** (4P) (aggregate ~21.0%, target 15%–30%).
     - **Total Wipeout:** **0.6%** (2P), **0.0%** (3P), **0.1%** (4P) — strictly below the $\le 2.0\%$ safety threshold.
  3. **CI/CD Scanned Staging & Pool Pacing:**
     - 100% of purchased market dice routed through Scanned Box (2.39–2.54 dice bought/seat).
     - Graduated dice into Ready averaged **4.20** (2P), **4.22** (3P), and **4.29** (4P) dice/round, with players holding 2.16–2.23 dice in Scanned.
     - Sudden rolling pool spikes eliminated; Release Track upgrades directly govern rolling throughput.
  4. **Triage Backpressure & Track Progression:**
     - Triage `(1, 1, 1, 1, 2)` successfully generates intended queueing tension: **53.6%** (2P), **49.6%** (3P), and **43.6%** (4P) of players experience held dice in Processing (up from 15.2%–21.4% baseline).
     - Backpressure player-rounds rose to **12.0%** (2P), **9.5%** (3P), and **7.9%** (4P) (vs 1.9%–2.7% baseline).
     - Triage L2 Milestone (+1 Secret) claimed by **43.2%** (2P), **43.0%** (3P), and **42.2%** (4P) of players.
     - Triage L4 Capstone reached by **23.9%** (2P), **25.3%** (3P), and **26.5%** (4P), providing high strategic reward for dedicated engine builders.
     - Overall L4 Capstone achievement: **66.0%** (2P), **69.8%** (3P), and **70.6%** (4P).
     - **Anti-Snowballing Guardrail:** 0.0% of players maxed 2+ tracks across all pods (target $< 10\%$).
  5. **Dual Economy Effectiveness ($ vs 🔬):**
     - Cash PR regain absorbed **$3.62** (2P), **$2.94** (3P), and **$2.91** (4P) per seat (53.2%–61.4% participation), reducing ending cash hoards to **$2.07–$2.26** (median $2.0, down from $2.98–$3.13).
     - Freed Research successfully channeled into terminal hardware: **9.25 🔬** (2P), **9.70 🔬** (3P), and **9.76 🔬** (4P) spent on tracks/seat (surging from 5.06–5.91 🔬 in baseline).
  6. **Global Green Cube Cap Enforcement:**
     - Enforced strictly: Green cubes in circulation capped at **5** across all pods.
     - Clamping activated in **27.0%** (2P), **27.5%** (3P), and **25.2%** (4P) of games, clamping 373–405 total overflow cubes (max 2 clamped in any single game).
     - Mean peak Green held at **3.83–3.94** with max peak Green **5** (0 violations), fully eliminating runaway shield attrition spirals.
  7. **Company Equity & Archetype Viability:**
     - Starting Color Win Rates (3P): Red **34.6%** / Blue **35.2%** / Green **30.4%** (fair share 33.3%).
     - Starting Color Win Rates (4P): Red **28.1%** / Blue **23.5%** / Green **23.4%** (fair share 25.0%).
     - Starting Color Win Rates (2P): Red **52.5%** / Blue **50.7%** / Green **46.9%** (fair share 50.0%).
     - Client Company win rates: Prometheus (28.1%–55.2%), Aegis (27.1%–56.3%), Omnidyne (27.5%–50.3%), Meridian (28.1%–49.5%), DTO (19.8%–45.3%), Helix (19.4%–43.8%).
     - Archetype meta: AdaptiveBalancedBot (61.7%–78.0%), SecOpsTurtleBot (28.1%–52.8%), MixedPolicyBot (24.3%–51.1%), AccelerationistBot (15.8%–43.3%), VentureGreedBot (13.9%–33.6%), RecklessSaboteurBot (6.8%–36.5%).

- **Official Balance Verdict: OFFICIALLY APPROVED (`v0.40.0 Baseline`).**
  The Phase 56 balance suite successfully resolves the economic divergence, restores tactical pipeline tension via Triage backpressure and Scanned staging, eliminates defensive blackout risks via the Global Green Cube Cap, and provides immediate hardware upgrade gratification through Phase 5/6 re-sequencing. Macro pacing, tri-modal end-game distribution, and starter equity remain exemplary. Formally approved as the design and balance baseline for `v0.40.0`.


