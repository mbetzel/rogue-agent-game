# Phase 47 Reference Bot Assessment (game-designer)

Date: 2026-11-07 · Status: **analysis only, for User discussion**. No RULES.md, PnP, web or sim change. No new game terms.

Inputs: `docs/findings/reference_bot_scoping.md`, `docs/specs/reference_bot_spec.md`, `sim_results/reference_bot/validation_report.md` (+ per-game JSON). Extra read-only probe: `/tmp/claude-1000/kz/probe.py` (replays the validation seeds `42 + 300000 + idx` through `scripts/run_reference_bot_validation.py::build_engine` and records per-round Market Share, Secrets, Red loss, Public Relations regain and Red blocks per seat). Replays match the validation run exactly (ref1 3P win 66.6% / 69.1%; seed 300042 identical). 3P, 1,200 games per cell. A `market_collapse_enabled=False` variant was run as a counterfactual only, not as a proposal.

## 1. Verdict on the bot as a tool

**Fit as the "competent player" reference.** The strength gate (≥ +10 points at 3P) passes by a wide margin: +33 / +36 points (v0.36 / v0.37), +28 / +31 at 2P, +36 / +39 at 4P. Mixed seats land at fair share (34–35% at 3P; 51–52% at 2P; 26–28% at 4P), so Mixed is a neutral roster seat that does not distort results.

Limits:
- **Portfolio-bound.** It only picks among moves some existing policy would make. It cannot find a line no archetype proposes (for example a full Public Relations push or a deliberate Market Share dump). A "no exploit found" result from it is evidence, not proof.
- **Rollouts are played by scripted policies.** It is optimized against the archetypes, not against itself. ref_all (33.3% per seat, by symmetry) is the only self-play check; its behavior there (Blue 48% of blocks, Public Relations Track 0.68–0.77) is close to ref1, which is reassuring.
- **Searched decisions are Phase 4 shields and Phase 6 spending only.** Purchases outside those hooks, Phase 1 commitments and Client Company timing follow AdaptiveBalanced.
- **Score is Secrets margin + small win bonus.** It does not value ending the game early as such; any "ending control" it shows comes through rollouts.
- Cost: ~95 s per 600-game ref1 pod; ref_all ~4× that.

**Recommended roster usage:**
1. One Mixed seat in every routine sweep (replaces one archetype; normal speed). Keeps archetype focus-order artifacts (§33–§34) from setting the result.
2. ref1 (3P, 1,200 games) as the **exploit / edge check** on every rule candidate: report the ref edge and what it does differently (block shares, Public Relations level, end triggers).
3. ref_all (3P, 600) only when a question is about how a table of competent players paces the game (end-trigger mix, rounds), not about edges.
4. Never trust a hand-written "aware" heuristic alone again (§36–§38 style) without a ref1 cross-check.

## 2. §36 / §37 / §38 re-judged

| Finding | Reference bot evidence | Status |
|---|---|---|
| §36 Blue-first is always correct | ref still puts ~49% of its blocks on Blue (ref_all 48%). It shifts toward Red: Red block rate 0.29 vs rivals 0.22 (v0.37), 0.24 vs 0.17 (v0.36), and loses ~1.3 less Market Share to Red per game. | **Stands, softened.** Blue is still the main target, but a searching player does leave Blue open for Red more than the scripts. Part of "Blue-first plays itself" was script behavior. |
| §37 root cause: Market Share pays too little vs Secrets | ref regains *less* Market Share than rivals (1.31 vs 2.06 v0.37; 0.79 vs 1.45 v0.36) and still wins two-thirds. | **Stands.** A competent player under-invests in Public Relations. The lock itself was not re-tested. |
| §37 tanking pays as well as before | See §3: no deliberate tanking found. | **Mostly a bot artifact.** "Lowest Market Share wins" was shared-Red correlation, not a strategy the search exploits. |
| §38 Public Relations-first loses | Public Relations Track avg 0.65–0.77 for ref; ref regains least. | **Stands.** |
| §38/§39 Market Leader Bonus rewards Market Share | ref takes 1st place 64% (v0.37) vs 58% (v0.36), mostly by blocking Red rather than buying regain. | **Stands**, the bonus is reached through shields, not the Public Relations Track. |

## 3. Kamikaze Market Collapse deep-dive (3P ref1, 1,200 games each)

| | v0.36 | v0.37 |
|---|---|---|
| Market Collapse triggered (any) | 75.4% | 62.6% |
| ref at 0 at trigger (with others / alone) | 432 (390 / 42) | 375 (316 / 59) |
| ...and ref won | 236 (54.6%) | 195 (52.0%) |
| ref Secrets lead at trigger, games ref won | +3.80 (ahead 89%, never behind) | +7.47 (ahead 94%) |
| ref Secrets lead at trigger, games ref lost | −1.13 | −0.62 |
| ref strictly lowest Market Share the round before | 25.9% | 42.9% |
| **Solo trigger (only ref at 0): ref wins** | **17/42 (40%)**, lead +0.13 | **22/59 (37%)**, lead +0.72 |
| Red block rate ref / rivals (ref-at-0 games) | 0.18 / 0.17 | 0.22 / 0.20 |
| Market Share lost to Red ref / rivals (all games) | 16.7 / 17.8 | 16.4 / 17.7 |
| Market Share regained ref / rivals | 0.79 / 1.45 | 1.31 / 2.06 |
| Market Leader Bonus to ref: ref-at-0 / other games | 0 / 0 (no bonus) | 1.26 / 1.65 |

Counterfactual, Market Collapse switched off:

| 3P | ref win | Patient Zero / Singularity | Rounds |
|---|---|---|---|
| v0.36 ref1 std → off | 66.6 → 64.5% | 6 / 23 → 16 / 83% | 8.73 → 9.74 |
| v0.37 ref1 std → off | 69.1 → 66.7% | 7 / 35 → 15 / 84% | 9.00 → 9.75 |
| v0.37 baseline std → off | — | 9 / 34 → 18 / 81% | 8.99 → 9.74 |

**Reading:**
1. **No kamikaze strategy.** The ref seat blocks *more* Red than rivals and loses *less* Market Share. In 84–90% of the "ref at 0 when Collapse triggered" games, the others were at 0 too: shared Red cubes drive everyone to the floor together.
2. **The 195 / 236 games are Secrets-lead wins, not Collapse wins.** In every one the ref was ahead or tied at trigger time (+3.8 / +7.5 Secrets). Switching Collapse off costs it only ~2.4 points of win rate. So the edge is not ending control; it is better defense.
3. **0 Market Share is not costless under v0.37**: at-0 games give the ref 0.4 less Market Leader Bonus on average, and when the ref alone hits 0 it wins only 37% (≈ fair share, far below its 69% overall). Under v0.36 it was costless (no bonus), and solo wins were 40%.
4. Small v0.37 watch signal: the ref is strictly lowest the round before trigger more often (43% vs 26%). It trades Public Relations research for Secrets and accepts last place on Market Share when its Secrets lead covers the +2/+1 gap. This is a legitimate trade, not a degenerate one, but it confirms §37's root cause.
5. Collapse is doing its pacing job: without it Singularity becomes ~83% of endings and games run ~0.75 rounds longer.

**Candidate levers (for User discussion only, none decided):**

| Lever | Modeled expected impact | Notes |
|---|---|---|
| A. No change; keep watching | ref solo-trigger win at fair share; no exploit found | Recommended default |
| B. Raise the 3–4P bonus gap (e.g. 1st +3) | Raises the cost of sitting last on Market Share by ~1 Secret vs a ref lead at trigger of +7.5 in its wins; flips few games. §38/§39 show bonus-aware edge near the +10 fail line and 2P Total Wipeout risk | Existing term (Market Leader Bonus), [TUNE] only |
| C. Cheaper Public Relations regain | Targets the real gap (ref regains 1.3/game); §38 says research income, not cost, is the bottleneck, so expect small effect | Existing track, [TUNE] only |
| D. Secrets penalty to a player at 0 Market Share at game end | Directly prices 0; risks bringing back the Unpaid Ransom Leak pattern (§36 idea 5) and Total Wipeouts | Would need a new rule and likely a new glossary term: **needs User approval** |
| E. Remove Market Collapse | ref edge −2.4 pts only; Singularity ~83%, +0.75 rounds | Shown as counterfactual; breaks pacing, not recommended |

## 4. Archetype ranking check (baseline 3P, per seat)

| v0.37 3P | win | PZ | Final Secrets | Market Share | Public Relations | Red / Blue block rate | 1st Market Leader place |
|---|---|---|---|---|---|---|---|
| VentureGreed | 51.2 | 0.7 | 7.76 | 2.10 | 0.26 | 0.17 / 0.72 | 54% |
| Accelerationist | 43.1 | 1.9 | 7.28 | 2.06 | 0.51 | 0.17 / 0.72 | 52% |
| SecOpsTurtle | 38.9 | 2.1 | 6.55 | 2.77 | 0.00 | 0.30 / 0.68 | 66% |
| AdaptiveBalanced | 17.2 | 3.6 | 5.61 | 2.05 | 0.02 | 0.26 / 0.64 | 36% |
| RecklessSaboteur | 16.4 | 10.0 | 5.10 | 2.43 | 0.13 | 0.21 / 0.58 | 50% |

- VentureGreed (61.7% v0.36 → 51.2% v0.37 at 3P; 45–59% at 2P/4P) wins on economy and Blue defense (highest final Secrets), with average Market Share and Public Relations. That is a strong script, not a degenerate rule exploit. The ref seat cuts its win rate to 32–40%, so it is beatable.
- SecOpsTurtle is the v0.37 riser (26 → 39% at 3P, 19 → 33% at 4P): Red-heavy blocking now pays through the Market Leader Bonus. Intended.
- RecklessSaboteur's Patient Zero rate is 10% at 3P v0.37 (6.9% v0.36). Watch item, not a degenerate strategy (it loses).
- AdaptiveBalanced (the ref fallback policy) is weak at 3–4P (9–17%). The ref's strength comes from search, not its fallback.
- No other degenerate pattern found. No archetype wins by stalling or by sitting at 0 Market Share.

## 5. Open questions for User

1. Adopt the roster rule (Mixed seat in every sweep; ref1 edge check on every rule candidate)?
2. Treat the kamikaze Market Collapse concern as closed (lever A), or explore lever B/C?
3. Should the next reference-bot iteration add a "Public Relations push" and a "Market Share dump" candidate to the portfolio, so a no-exploit result covers those lines too?
