# Lever A: Roster Upgrade ("Public Relations push") — Pre-SDLC Scoping (game-designer)

Date: 2026-11-07 · Status: **spec inputs final (state log done), awaiting User sign-off** · Scope: `sim/bots/` and test fixtures only (no `RULES.md`, `web/`, `pnp/` change; no new game terms; no rule change)

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

## 3. Final heuristic spec inputs: push + dump (1,200-game state log)

### 3.1 Data (measured)

State log: `sim_results/reference_bot/lever_a/v037_ref1_statelog_3p_1200.json` (scratch scripts `/tmp/claude-1000/levera2/probe.py`, `an.py`). Full 13-member portfolio, v0.37 3P ref1, seeds `42 + 300000 + idx`, 1,200 games, 8 procs. Ref win 78.6%, identical to the §40 13-member cell (so the logging hook did not change play). 16,672 searched decisions. A line counts as "distinct" when its candidate survived deduplication (it differs from the fallback and every earlier member). Rates are choice rate when distinct, with 95% Wilson CIs. "Market Collapse threat" = own Market Share ≤ Red pressure (Red in the Staging Cup + stuck on the Internal Baffles) + 2.

**Push** (Phase 4 Generic shield split: distinct 4,641, chosen 1,167; Phase 6 Operations plan: distinct 4,774, chosen 574; Phase 1 shield commits: never distinct):

| State bucket | Phase 4 | Phase 6 |
|---|---|---|
| Rounds 1–3 / 4–6 / 7+ | 24% [22–27] / **30% [28–32]** / 21% [19–23] | 13% / 9% / 14% |
| v1.0 / v2.0 / v3.0 | 27% / 27% / **17% [15–20]** | 13% / 10% / 14% |
| Gap to lowest rival ≤ 3 / 4–7 / ≥ 8 | 26% / 26% / **13% [10–17]** | 11% / 16% / 18% (n=33) |
| Gap to highest rival −3..+3 / ≥ +4 | 23–26% / 21% [18–24] | 12–14% / 16% |
| Secrets lead −2..+2 / ≥ +3 / ≤ −3 | 26% / **10% [6–16]** / 17% (n=54) | 9–12%, no signal |
| Own Market Share ≤ 3 / 4–5 / 6–8 / ≥ 9 | (Phase 4 search almost always at ≥ 9) | **5% / 10%** / **24% [20–29]** / 12% |
| Research Tokens ≤ 2 / ≥ 3 | 26% / 20% | 15% / **3% [2–4]** |
| Public Relations Track level 0 / 1 / 2 | 27% / 24% / 22% | **15%** / 7% / 10% |
| Market Collapse threat no / yes | 25% / (n=0) | 12% / 14%, no signal |

Proposed push window (below) vs outside it: Phase 4 27% [26–29] (n=3,272) vs 20% [18–22] (n=1,369). Phase 6 is not window-sensitive (12% vs 14%); its signal is Public Relations Track level 0 with ≤ 2 Research Tokens (17% [15–19]) and dented Market Share 6–8 (24%).

**Dump** (Phase 4: distinct 3,011, chosen 688; Phase 6: distinct 1,731, chosen 636):

| State bucket | Phase 4 | Phase 6 |
|---|---|---|
| Own Market Share ≤ 3 / 4–5 / 6–8 / ≥ 9 | **81% [73–87] / 62% [54–70]** / 20% / 18% | 14% / 22% / 25% / **45% [42–48]** |
| Market Collapse threat no / yes | 20% / **80% [73–86]** | 45% / 20% |
| Gap to highest rival ≤ −4 / −3..−2 / −1..+3 / ≥ +4 | 57% (n=30) / 46% [37–54] / 23% / 15% | 22–38% |
| Share ≤ 5 and highest-rival gap ≤ −2 / ≥ −1 | 75% [64–83] / 70% [63–77] | 23% / 15% |
| Share ≤ 5 and Market Collapse threat | 80% [73–86] | 17% [13–21] |
| Share ≤ 5, no threat, gap ≥ −1 | 61% [51–70] (n=94) | — |
| Secrets lead ≥ +3 | 41% [35–48] | 13% |

Reading (measured):
1. **Push thresholds confirmed with two revisions.** Phase 4 is still the main effect and peaks in rounds 4–6 under v1.0/v2.0, fading under v3.0. Revision a: the low-rival fade starts at gap ≥ 8, not ≥ 4 (≤ 3 and 4–7 are equal at 26%), so `PUSH_LOW_GAP` goes 3 → **7**. Revision b: a lopsided Secrets race (|lead| ≥ 3) cuts push to 10–17%, so it is now a window condition. The top-rival fade at ≥ +4 is weaker than the 300-game probe showed (21% vs 26%) but real, so `PUSH_TOP_GAP` 3 stays. The Market Collapse threat clause is dropped from push: it never co-occurs with a distinct Phase 4 push, and at Phase 6 it shows no signal. That threat belongs to dump.
2. **Dump is a Phase 4 behaviour at ≤ 5 Market Share.** At ≤ 5 the ref stops Red-first blocks 62–81% of the time; above 5 only ~19%. Market Collapse threat is the sharpest single trigger (80%). "1st place out of reach" adds little on top of share ≤ 5 (75% vs 70%, CIs overlap).
3. **Phase 6 dump at ≤ 5 is weak (14–23%).** The big Phase 6 dump rate (45%) sits at ≥ 9 Market Share in rounds 4–6, under v2.0: a comfortable leader skips the Public Relations Track and regain to spend research elsewhere. That is a different behaviour, it overlaps the push window, and it is outside the User's dump definition, so it is **not** in this spec (see §8).
4. Push and dump windows never overlap in the log (0 of 16,672 decisions), since push needs share ≥ 6 and dump needs ≤ 5.

### 3.2 The heuristic to add (AdaptiveBalanced only, behind `bot_pr_push`)

When `bot_pr_push` is on and Market Share is in play (`market_share_policy.is_aware(state)`), compute at each searched-hook equivalent (Phase 4 split, Phase 6 plan, dice buying):

- `ms` = own Market Share; `lo` / `hi` = lowest / highest surviving rival Market Share; `v` = Version index (0 = v1.0); `sl` = own Corporate Secrets − best surviving rival's; `threat` = `ms <= red_pressure(state) + DUMP_THREAT_MARGIN`.
- **Dump window** = `ms <= DUMP_MAX_SHARE` **and** (`ms - hi <= -DUMP_TOP_GAP` **or** `threat`). Checked first.
- **Push window** = not dump window **and** `v <= PUSH_MAX_VERSION` **and** `ms >= PUSH_MIN_SHARE` **and** `ms - lo <= PUSH_LOW_GAP` **and** `ms - hi <= PUSH_TOP_GAP` **and** `|sl| <= PUSH_SECRETS_BAND`.
- Since `PUSH_MIN_SHARE > DUMP_MAX_SHARE` is required (assert it at config load), the two windows are disjoint by construction; the "not dump window" guard is belt-and-braces.

**Push (in push window):**
- *Phase 4 Generic shield split:* use `PR_PUSH_POLICY` values (`red_base_value 5.0`, `red_danger_value 3.0`, `danger_margin 4`) and fill order Red → Blue → Green, **except** `blue_lethal_value` stays first (a Blue block that prevents a Total Data Breach always wins).
- *Phase 6 Operations plan:* if Public Relations Track level < `PUSH_PR_CAP` and Research Tokens on hand ≤ `PUSH_MAX_RESEARCH` and the step is affordable, buy one Public Relations Track step before the archetype's own focus order; then spend any Market Share regain budget. Otherwise keep the archetype's own order.
- *Dice buying:* `red_buy_share_frac 1.0`; colour preference Red → Blue → Green → Yellow.

**Dump (in dump window):**
- *Phase 4 Generic shield split:* `DUMP_POLICY` values (Red block value 0 except it is never below what `blue_lethal_value` protection needs) and fill order Blue → Green → Red. `blue_lethal_value` first as always.
- *Phase 6 Operations plan:* no Public Relations Track step and no Market Share regain; the research that would have gone there follows the archetype's own focus order with those two entries skipped (`DUMP_FOCUS`).
- *Dice buying:* `red_buy_share_frac 0.0`; colour preference Blue → Green → Yellow (no Red bought for Market Share).
- *Phase 1 shield commits:* unchanged (the dump member's Blue-option override is not adopted; Phase 1 never showed a distinct signal for push, and the Phase 4 change carries the effect).

**Outside both windows:** the existing AdaptiveBalanced behaviour, byte-identical.

### 3.3 Threshold constants (`[TUNE-BOT]`, bot parameters, not game rules)

| Constant | Start | Basis | Sweep (§6 step 3) |
|---|---|---|---|
| `PUSH_MIN_SHARE` | 6 | Phase 6 push 5–10% at ≤ 5, 24% at 6–8 | {5\*, 6, 7} |
| `PUSH_LOW_GAP` | **7** (was 3) | fade only at ≥ 8 | {5, 7, 9} |
| `PUSH_TOP_GAP` | 3 | 21% vs 26% at ≥ +4 | {2, 3, 4} |
| `PUSH_MAX_VERSION` | 1 (v2.0) | 17% under v3.0 | fixed |
| `PUSH_SECRETS_BAND` | 2 | 10–17% outside ±2 | {2, 3} |
| `PUSH_PR_CAP` | 1 | 15% at level 0, 7% at 1 | fixed |
| `PUSH_MAX_RESEARCH` | 2 | 3% at ≥ 3 tokens | fixed |
| `DUMP_MAX_SHARE` | 5 | 62–81% at ≤ 5, ~19% above | {4, 5} |
| `DUMP_TOP_GAP` | 2 | 46–75% at gap ≤ −2 | {1, 2, 3} |
| `DUMP_THREAT_MARGIN` | 2 | 80% under threat | {2, 3} |

\* `PUSH_MIN_SHARE` 5 is only legal with `DUMP_MAX_SHARE` 4 (disjointness).

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
3. **Constant sweep (small):** one-at-a-time over the §3.3 sweep column (push and dump constants), 3P, 600 games each, respecting `PUSH_MIN_SHARE > DUMP_MAX_SHARE`. Measure AdaptiveBalanced's own win rate and pick the best cell, so the heuristic is tuned rather than guessed.
4. **Archetype win spread** (baseline, 3P/4P): the per-archetype win rates and their spread, compared with v0.37. The goal is AdaptiveBalanced up with no single archetype above ~40% (3P), and the other four kept distinct (focus and block-colour profiles do not converge).
5. **ref1 edge before/after** (3P 1,200, 2P/4P 600): 13-member portfolio, switch off vs on. Also the 11-member portfolio, so the result can be compared with §40. Report MLB 1st %, ref at 0 at Market Collapse, Red share of blocks, and dump-line choice share (it should rise if push is now absorbed by the roster).
6. **Mixed seat ≈ fair share** (mixed1, 2/3/4P 1,200): Mixed win within ±3 points of 1/N.
7. Record the result in FINDINGS.md as a new section.

## 7. Modeled expected impact (estimates, not measured; revised after the 1,200-game state log)

- **AdaptiveBalanced baseline win rate (3P):** *estimate* +3 to +6 points (was +2 to +5). Push alone ~+2 to +3; dump adds ~+1 to +3, mostly by not wasting Generic shields on Red at ≤ 5 Market Share where 1st place is gone.
- **Baseline endings:** *estimate* Market Collapse −1 to −3 points (push holds Market Share), partly offset because dump seats at ≤ 5 stop defending and may hit 0 sooner; net −0.5 to −2. Singularity +1 to +3 (more Blue/Green blocked by dumpers). Patient Zero flat to −1 (`blue_lethal_value` stays first, dumpers block more Blue). Total Wipeout flat.
- **Mixed seat:** *estimate* +0.5 to +1.5 points; stays within fair-share tolerance.
- **ref1 edge (3P, 13 members, 78.6% = +45 over fair share):** *estimate* falls to ~70–75% (+37 to +42), was ~74–77%. The push gain (+5.1) and the Phase 4 half of the dump gain (+7.2) are now both partly covered; the ref's fallback and rollout seats improve too (§4), which damps the drop. The Phase 6 "comfortable-leader dump" (§3.1 reading 3) is not covered.
- **~+35 target (≈ 69%):** *estimate* within reach only at the optimistic end. If validation lands at +40 or above, the remaining gap is most likely the Phase 6 comfortable-leader dump and the search's tactical edge itself.

## 8. Open questions for the User (resolved 2026-11-07; see "User decisions" below)

1. **Target:** lever A covers only the push line. The dump line is the larger half of the +9.5. Should this cycle also add a situational dump heuristic to AdaptiveBalanced (stop Red blocks and regain when Market Share ≤ 5 and 1st place is out of reach)? Or do we accept an estimated ~+41–44 ref1 edge and re-baseline the target?
2. **Archetypes:** AdaptiveBalanced only (recommended), or also SecOpsTurtle (Phase 4 part only)?
3. **Flag:** a GameConfig `[TUNE-BOT]` switch `bot_pr_push` default off plus new `v037_push` fixtures (recommended)? After validation, should it become the default for future rule probes, with old fixtures pinned to off?
4. **Reference bot coupling:** with the switch on, the ref's fallback and rollout seats also use push (a consistent model, recommended). Or should the ref's rollouts stay frozen at the old AdaptiveBalanced to isolate the opponent effect, at the cost of an extra code path?
5. **Probe size:** the trigger table rests on 300 games (2,429 decisions). Is that enough, or do you want a 1,200-game state log first (about 8 min at 4 procs)?

## 9. New open questions after the state log

1. **Dump trigger:** at ≤ 5 Market Share the ref dumps 61% even when 1st place still looks reachable (gap ≥ −1, no threat). Keep the User's "out of reach" condition (spec as written), or drop it and dump on share ≤ 5 alone?
2. **Comfortable-leader Phase 6 dump** (45% at ≥ 9 Market Share, rounds 4–6, v2.0): out of scope for this cycle, or a later lever?
3. **`PUSH_LOW_GAP` 3 → 7** changes a constant from the earlier draft; confirm.

## User decisions (2026-11-07)

1. Add a situational **dump** heuristic in the same cycle (stop defending Market Share at ≤5 when 1st Market Leader Bonus place is out of reach), alongside push.
2. AdaptiveBalanced only; other archetypes unchanged.
3. `bot_pr_push` [TUNE-BOT] switch, default off, plus new fixtures; becomes the default for rule probes once validated.
4. With the switch on, the reference bot's fallback and rollout seats use the new behaviour too (consistent).
5. Run a 1,200-game state log first to fix the trigger thresholds before the spec.

## User decisions on §9 (2026-11-07)

1. Dump window starts as **Market Share ≤ `DUMP_MAX_SHARE` alone** (any rival gap, threat or not). The "1st place out of reach or Market Collapse threat" condition is kept as a sweep variant only.
2. Leader-side Phase 6 dump (≥9 Market Share skipping Public Relations Track / regain) is deferred to a later lever.
3. `PUSH_LOW_GAP` = 7 confirmed.
