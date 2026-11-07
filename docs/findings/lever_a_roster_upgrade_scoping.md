# Lever A: Roster Upgrade ("Public Relations push") — Pre-SDLC Scoping (game-designer)

Date: 2026-11-07 · Status: **draft, awaiting User review** · Scope: `sim/bots/` and test fixtures only (no `RULES.md`, `web/`, `pnp/` change; no new game terms; no rule change)

## 1. Problem

The 13-member reference portfolio wins 78.6% of v0.37 3P ref1 games, against 69.1% for the 11-member one (FINDINGS §40 addendum, `docs/findings/v370_reference_bot_attribution.md`). Adding only the Public Relations push line is worth +5.1. The push line blocks more Red, holds Public Relations Track level ~1, takes 1st Market Leader Bonus place 78% of the time (vs 64%), and sits at 0 Market Share when Market Collapse triggers far less often (254 vs 375 of 1,200). With Market Collapse off it is worth only +1.3.

Lever A (User-approved direction): leave the rules alone and teach the roster this behaviour, so the ref1 edge shrinks back toward ~+35 over fair share and later rule probes measure the rules, not the bots.

## 2. Data: when the reference bot chose push

`sim_results/reference_bot/attribution/*.json` records choice counts per game, but not the game state at each decision, so I ran a small probe. Scratch only: `/tmp/claude-1000/levera/probe.py` and `an.py`. Setup: portfolio A (11 + push, no dump, which isolates push), v0.37 3P ref1, seeds `42 + 300000 + idx`, 300 games, 4 procs. Ref win was 76.3%, inside the 1,200-game cell's CI (74.2 ± 2.5). Push was a distinct candidate at 2,429 searched decisions and was chosen at 472 of them: 313 in the Phase 4 Generic shield split and 159 in the Phase 6 Operations plan. In Phase 1 shield commits, push was never distinct from AdaptiveBalanced.

Push choice rate (n = decisions where push was distinct), 300 games:

| Slice | Phase 4 Generic shield split | Phase 6 Operations plan |
|---|---|---|
| Overall | 26% (1,204) | 13% (1,225) |
| Rounds 1–3 / 4–6 / 7+ | 24% / **36%** / 16% | 14% / 12% / 13% |
| v1.0 / v2.0 / v3.0 active | 29% / 29% / **13%** | 14% / 12% / 13% |
| Market Share gap to lowest rival ≤ 3 / 4–7 / ≥ 8 | **30%** / 23% / 12% | 12% / 12% / 25% (n=12) |
| Market Share gap to highest rival −2..+3 / ≥ +4 | **28–32%** / 12–19% | 10–13% / 20% (n=56) |
| Own Market Share ≤ 5 / 6–8 / ≥ 9 | — (rare) | **0–2%** / **27%** / 11–19% |
| Public Relations Track level 0 / 1 / 2 | 29% / 24% / 20% | **16%** / 8% / 14% |
| Research Tokens on hand ≤ 2 / ≥ 3 | 26% / 22% | **15%** / 4% |
| Secrets lead vs best rival −2..+2 / outside | 26–28% / 0–16% | no signal (10–14% throughout) |

Reading (measured, 300 games; buckets with n < 60 are noisy):
1. **Push is mostly a Phase 4 decision.** The value is filling Generic shields Red-first. The Phase 6 part (one Public Relations Track step, then Market Share regain) is the smaller half.
2. **It is a contested-race behaviour.** It peaks when the Market Leader Bonus race is close (within ~3 of the top and bottom rivals), in rounds 4–6 under v1.0/v2.0. It fades when the ref is clearly ahead (≥ +4) and under v3.0, where the game is close to Singularity and Blue/Green blocks matter more.
3. **It is abandoned when Market Share is low.** At ≤ 5 own Market Share the ref almost never picks push in Phase 6. Regain is too slow to save 1st place, and at that point the dump line (or AdaptiveBalanced) is better.
4. **Public Relations target is level 1, rarely 2.** The ref ends at ~0.95 (rivals ~0.2). Push is picked mostly at level 0 with ≤ 2 Research Tokens, i.e. "buy the first step, then stop".
5. **Secrets lead is not a trigger.** Only when the Secrets race is lopsided (±3 or more) does Phase 4 push fade.

## 3. The heuristic to add (exact)

New per-bot `[TUNE-BOT]` switch `pr_push_situational` (default **False**, see §5). When it is on and Market Share is in play (`market_share_policy.is_aware(state)`), compute each round:

- `ms` = own Market Share; `lo` / `hi` = lowest / highest surviving rival Market Share; `v` = current Version index (0 = v1.0).
- **Push window** = `v <= 1` **and** `ms >= PUSH_MIN_SHARE` (6) **and** `ms - lo <= PUSH_LOW_GAP` (3) **and** `ms - hi <= PUSH_TOP_GAP` (3), **or** a Market Collapse threat: `ms <= next-round Red pressure + danger_margin` while `ms >= PUSH_MIN_SHARE`.
- **Phase 4 Generic shield split (main effect):** in the window, use the push Market Share policy values (`red_base_value 5.0`, `red_danger_value 3.0`, `danger_margin 4`, the current `PR_PUSH_POLICY`) and fill order Red → Blue → Green, **except** when a Blue block prevents a Total Data Breach (`blue_lethal_value` stays first, as today).
- **Phase 6 Operations plan:** in the window, if Public Relations Track level is 0 and the step is affordable, buy one Public Relations Track step before the archetype's own focus order, then spend any regain budget on Market Share. **Cap: level `PUSH_PR_CAP` (1).** No step at level ≥ 1; at ≥ 3 Research Tokens keep the archetype's own order.
- **Market Share purchases:** in the window, `red_buy_share_frac 1.0` (prefer Red Central Market dice whenever below max), as in `PR_PUSH_POLICY`.
- **Outside the window:** the archetype's existing behaviour, unchanged.

All four constants are `[TUNE-BOT]` bot parameters, not game rules. They come from the table above and are a first cut to be swept (§6 step 3).

## 4. Which archetypes get it

**Recommendation: AdaptiveBalanced only, in this cycle.**
- AdaptiveBalanced is the "competent generalist" seat, and every reference portfolio member and the reference bot's non-searched hooks inherit from it. It is also one of the 5 Mixed bot pool members, so Mixed gets push on ~1/5 of its decisions with no Mixed code change.
- Accelerationist (race to Singularity), RecklessSaboteur, SecOpsTurtle (Blue/Green defence) and VentureGreed (Money) keep their identities. A push window would blur them (all would block Red first in rounds 4–6). §33–§34 showed that archetype artefacts mislead; adding the same line to all 5 would make the roster more uniform, not more competent.
- Optional second step (open question): SecOpsTurtle is the natural second adopter, since push is a defensive Phase 4 behaviour. It would get only the Phase 4 part, not the Public Relations step.

**Side effect to note.** The reference bot's rollouts play every seat at its default policy, including the reference seat's own fallback (AdaptiveBalanced). With the switch on, the ref's opponents get stronger, but so do its rollout model and its fallback. The ref1 edge therefore shrinks less than the opponent gain alone would suggest. The validation measures this directly, with no modelling assumption needed.

## 5. Parity impact and the flag

AdaptiveBalanced sits in every baseline pod, so turning push on shifts the v0.36 and v0.37 baseline, mixed1 and ref1 results and the parity fixtures (`tests/fixtures/v036_parity`, and the v0.37 runs that reuse it).

**Proposal:** a GameConfig-level `[TUNE-BOT]` switch, `bot_pr_push` (bool, default **False**), read by AdaptiveBalanced through a helper next to `market_share_policy.is_aware`. It follows the existing `market_share_bot_policy` pattern: a config value picks bot behaviour, so it does not create a rule.
- Default False: every existing fixture and result stays byte-identical. The parity test is required to prove this.
- A config switch (rather than only a class attribute) means the baseline seats, the Mixed bot's AdaptiveBalanced pool member, the ref's fallback and its rollout seats all switch together in one pod. That avoids an inconsistent rollout model.
- **New fixtures:** add a `v037_push` parity fixture set (same capture harness, switch on) so the new behaviour is pinned as well. Old fixtures are not regenerated.
- Promoting it to default on is a later User decision (open question 3), after validation.

## 6. Validation plan

Same harness as §40: `scripts/run_reference_bot_validation.py`, seeds `42 + 300000 + idx`, v0.37 (plus v0.36 for a spot check), switch off vs on.

1. **Parity:** switch off reproduces v0.36/v0.37 fixtures exactly; switch on matches the new `v037_push` fixture.
2. **Baseline endings shift** (2/3/4P, 1,200 games): Patient Zero / Singularity / Market Collapse %, average rounds, simultaneous-0 (Total Wipeout) rate. Guardrail: Patient Zero and Total Wipeout not up by more than 2 points each.
3. **Constant sweep (small):** `PUSH_LOW_GAP` / `PUSH_TOP_GAP` ∈ {2, 3, 4}, `PUSH_MIN_SHARE` ∈ {5, 6, 7}, 3P, 600 games each. Measure AdaptiveBalanced's own win rate and pick the best cell, so the heuristic is tuned rather than guessed.
4. **Archetype win spread** (baseline, 3P/4P): the per-archetype win rates and their spread, compared with v0.37. The goal is AdaptiveBalanced up with no single archetype above ~40% (3P), and the other four kept distinct (focus and block-colour profiles do not converge).
5. **ref1 edge before/after** (3P 1,200, 2P/4P 600): 13-member portfolio, switch off vs on. Also the 11-member portfolio, so the result can be compared with §40. Report MLB 1st %, ref at 0 at Market Collapse, Red share of blocks, and dump-line choice share (it should rise if push is now absorbed by the roster).
6. **Mixed seat ≈ fair share** (mixed1, 2/3/4P 1,200): Mixed win within ±3 points of 1/N.
7. Record the result in FINDINGS.md as a new section.

## 7. Modeled expected impact (estimates, not measured)

- **AdaptiveBalanced baseline win rate:** *estimate* +2 to +5 points in 3P. Basis: the ref gains +5.1 from push with full search; a fixed heuristic captures perhaps half of that.
- **Baseline endings:** *estimate* Market Collapse endings −1 to −3 points (fewer seats at 0) and Singularity +1 to +3. Patient Zero is about flat: the Phase 4 Blue lethal exception keeps Total Data Breach protection.
- **Mixed seat:** *estimate* +0.5 to +1 point (AdaptiveBalanced is ~1/5 of its decisions). It stays within fair-share tolerance.
- **ref1 edge (3P, 13 members, 78.6% = +45 over fair share):** *estimate* falls to ~74–77% (+41 to +44). An AdaptiveBalanced-only push covers part of the push line's +5.1. It does nothing for the dump line's +7.2, and the ref's own fallback improves too (§4).
- **Reaching the ~+35 target (≈ 69%) very likely needs more than this lever.** Options: teach the roster the dump line's situational "stop defending Market Share when 1st place is out of reach" as well, or accept ~+40 as the new competent-player reference. This is open question 1.

## 8. Open questions for the User

1. **Target:** lever A covers only the push line. The dump line is the larger half of the +9.5. Should this cycle also add a situational dump heuristic to AdaptiveBalanced (stop Red blocks and regain when Market Share ≤ 5 and 1st place is out of reach)? Or do we accept an estimated ~+41–44 ref1 edge and re-baseline the target?
2. **Archetypes:** AdaptiveBalanced only (recommended), or also SecOpsTurtle (Phase 4 part only)?
3. **Flag:** a GameConfig `[TUNE-BOT]` switch `bot_pr_push` default off plus new `v037_push` fixtures (recommended)? After validation, should it become the default for future rule probes, with old fixtures pinned to off?
4. **Reference bot coupling:** with the switch on, the ref's fallback and rollout seats also use push (a consistent model, recommended). Or should the ref's rollouts stay frozen at the old AdaptiveBalanced to isolate the opponent effect, at the cost of an extra code path?
5. **Probe size:** the trigger table rests on 300 games (2,429 decisions). Is that enough, or do you want a 1,200-game state log first (about 8 min at 4 procs)?
