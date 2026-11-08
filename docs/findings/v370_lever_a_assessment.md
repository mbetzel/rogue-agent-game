# Phase 48 Lever A post-telemetry assessment (`v0.37`, bot-only, no rules change)

**Author:** game-designer, 2026-11-07. **Status:** assessment; open questions for the User (§6).
**Inputs:** `sim_results/lever_a/sweep/sweep_report.md`, `docs/findings/lever_a_regression_diagnosis.md`,
`docs/findings/lever_a_roster_upgrade_scoping.md` §7, spec + both User sections, FINDINGS §40 and addendum.
**User decision (2026-11-07):** keep the current `PrPushParams` defaults.
**Extra probes (scratch only, `/tmp/claude-1000/la/`, 4 procs, existing seed scheme `42 + P*100000 + idx`):**
(a) ref1 3P switch off, 300 games, current code; (b) ref1 2P switch off, 600 games (heads-up ref vs each archetype);
(c) per-seat re-analysis of the existing JSON files.

## 1. Correction to the sweep's ref1 reference row

The sweep report compares ref1 "on" with `sim_results/reference_bot/v037_ref1_3p_1200.json` (69.1%). That file is the
**11-member portfolio** from Phase 47. The current code has the 13-member portfolio (commit `4f1c31d`), and its
switch-off value is **78.6%** (`sim_results/reference_bot/followup/v037_ref1_3p_1200.json`). Probe (a) confirms
this: the first 300 games on the current tree with the switch off match that file game for game (300/300 identical
winners, 78.0% ref win on those 300).

So the correct before/after is:

| ref1, 3P, 1,200 games | ref win % | edge vs 33.3% | Δ vs off |
|---|---|---|---|
| 11 members, switch off (§40, stale reference) | 69.1 | +36 | — |
| **13 members, switch off (true baseline)** | **78.6** | **+45** | — |
| 13 members, on, scope `all` | 77.1 | +44 | −1.5 |
| 13 members, on, scope `non_reference` | 71.2 | +38 | **−7.4** |

Lever A did not leave the edge "about where it was". It cut it by 7.4 points (non_reference), from +45 to +38.

## 2. Did lever A meet its goal?

| Check | Off | On (defaults) | Target / guardrail | Result |
|---|---|---|---|---|
| AdaptiveBalanced 2P | 39.1 | 51.2 | up, CIs disjoint | PASS (+12.1) |
| AdaptiveBalanced 3P (1,200 / 6,000) | 17.2 / 18.2 | 26.5 / 27.7 | up | PASS (+9.3 / +9.5) |
| AdaptiveBalanced 4P | 8.8 | 16.1 | up | PASS (+7.3) |
| Patient Zero Δ (2/3/4P) | — | −0.3 / −0.3 / −1.3 | ≤ +2 | PASS |
| Total Wipeout Δ | — | −0.2 / +0.2 / +0.1 | ≤ +2 | PASS |
| AB Secrets lost to Blue, 3P | 3.53 | 3.13 | not worse | PASS |
| Mixed seat 3P | 34.2 | 32.7 | 33.3 ± 3 | PASS |
| Max archetype 3P | 51.2 (Vent) | 48.8 (Vent) | ≤ ~40 | FAIL, pre-existing, slightly better |
| ref1 edge (non_reference) | +45 | +38 | toward ~+35 | PARTIAL (7.4 of ~10 pts) |
| AB seats inside ref1 pods (non_reference) | 2.9* | 8.5 | up | PASS |

\* 11-member file; the 13-member file was not split by seat here.

**Verdict: yes, lever A met its main goal, with a partial result on the edge.** The roster's weakest
sensible seat now plays the push/dump lines the reference bot found, at no guardrail cost at any player count,
and the reference bot's edge fell from +45 to +38. Reaching +35 was flagged in scoping §7 as possible "only at
the optimistic end"; the result sits inside the scoping estimate (+37 to +42).

### Why +38 and not +35

1. **Only one seat in five learned the lines.** The switch changes AdaptiveBalanced only. In a ref1 pod the ref
   faces AB in 480 of 1,200 games. The ref's win rate in pods without AB (Accelerationist, VentureGreed,
   SecOpsTurtle, RecklessSaboteur) is unchanged by lever A by construction, so most of the 13-member gain
   (+9.5) stays.
2. **The Phase 6 "comfortable-leader dump" is not covered** (scoping §3.1 reading 3; out of scope by User
   decision). The dump line was the larger half of the +9.5 in the attribution (+7.2 alone).
3. **Search edge remains.** The ref's tactical one-step search over shields and Phase 6 is a real skill edge no
   scripted heuristic copies. +35 was always an estimate for the 11-member search (69.1%), not a floor.
4. **Scope `all` hides the drop.** With scope `all` the ref's fallback and rollouts also use the new AB, so the ref
   gains about as much as its opponents (77.1%, −1.5). This is the damping effect predicted in scoping §4.

### Is the reference bot still a valid "competent player" check?

**Yes.** It still beats every archetype by a wide margin (3P +38 at non_reference; 2P heads-up 88.2% overall,
probe b), it holds VentureGreed far below its roster rate, and the Mixed seat sits at fair share, so the edge is
skill and not seat bias. Its job is to find lines the roster misses; lever A shows that loop works (the ref found
push/dump, the roster learned them, the edge fell). The check stays valid as long as the ref's opponents and the
ref's own model are kept separate, which is what scope `non_reference` does.

## 3. Roster recommendation

Recommend promoting `bot_pr_push=True` to the default roster for future rule probes. It is validated: every
guardrail passes at 2/3/4P, the response surface is flat (the defaults are robust), and the Mixed seat is unchanged.

**Proposed roster rule (for User sign-off):**

> For every rule probe and routine sweep from Phase 48 on: build the config with `bot_pr_push=True` and default
> `PrPushParams` (`push_blue_slack=0`, `dump_condition="share_only"`), on the `_bot_classes()` rotation, with one
> Mixed seat (mixed1). The edge check on every rule candidate is ref1, 3P, 1,200 games, seeds
> `42 + 300000 + idx`, with `bot_pr_push=True` and **`bot_pr_push_scope="non_reference"`**. Its reference value is
> **71.2% (+38)**; a rule candidate is flagged if the edge moves more than ±5 points from the same-config
> reference, or falls below +10 (the §40 gate). Old fixtures and historical comparisons pin `bot_pr_push=False`
> explicitly.

**Why non_reference:** it measures the gap between a stronger roster and a fixed reference, so the number moves
only when the roster or the rules change. Scope `all` moves the ref and its opponents together and hides
both roster gains and rule effects. Cost: the ref's rollout model of AB seats is slightly wrong (old AB). This is a
small, known bias that makes the ref weaker, which is the conservative direction.

The flip itself is a separate engineering change (spec §9: tests keep `bot_pr_push=False` explicitly).

## 4. VentureGreed: rules problem or bot problem?

| VentureGreed | 2P | 3P | 4P |
|---|---|---|---|
| vs scripted roster, switch off | 59.0 | 51.2 | 44.8 |
| vs scripted roster, switch on | 59.0 | 48.8 | 43.5 |
| with the ref seat at the table (3P, off, 11 members / on, non_ref) | — | 32.1 / 29.0 | — |
| **heads-up vs the ref (2P, switch off, probe b, n = 120)** | **20.0** (ref 80%) | — | — |
| ref win in pods with VG vs without (3P, non_ref) | — | 59.0 vs 79.3 | — |

Profile (3P baseline, off): highest final Secrets (7.76), fewest Secrets lost to Blue among non-ref seats (2.98
vs 3.53 AB), Patient Zero 0.7%, average Market Share (2.10). It wins on economy (Yellow-first buying, low
shielding) and paid Secret actions with no Money cushion.

**Diagnosis: a bot problem, not a rules problem (with one watch item).**
- The same rules give a competent player an 80% heads-up win against VentureGreed at 2P and hold it to 29–32% at
  3P. A dominant rule exploit would hold up against the stronger player; this one does not.
- VentureGreed is the ref's hardest opponent (ref 59% vs 79% without it), so its plan is good, not degenerate:
  a strong economy line the other scripts answer badly (they over-shield, under-buy, or chase Market Share).
- The 40% guardrail measures the roster as much as the rules. With four weaker scripts, one good script
  will exceed it.
- Watch item: 2P, where VG is 59% against every script and the Market Leader Bonus (+2 to 1st, no 2nd place)
  rewards its average Market Share less. That 2P spread is above the 3P one and is worth tracking if more roster
  levers fail to close it.

**Candidate levers (none decided; impact is modelled, not measured, unless stated):**

| ID | Lever | Type | Modelled impact on VG 3P | Notes |
|---|---|---|---|---|
| V1 | Roster: teach one more archetype (e.g. SecOpsTurtle or Accelerationist) VG's paid-Secret timing (no Money cushion on B2/Y1) | `[TUNE-BOT]` | −3 to −6 pts (redistributes Secrets) | Same method as lever A; no new term |
| V2 | Re-define the guardrail as "no archetype above 40% **and** ref1 holds it below fair share" | process | 0 (guardrail passes: 29% < 33%) | Makes the gate test rules, not roster weakness |
| V3 | Promote the Mixed seat or a second AB-like competent seat into the rotation | roster | −5 to −8 pts (estimate, more competent seats dilute VG) | Changes historical comparability |
| V4 | Raise the price of Money → Secret actions (B2 `$4` → `$5`, Y1 `$6` → `$7`) | `[TUNE]` rule | −2 to −5 pts (estimate); also weakens the ref's economy line | a scratch 3P `b2_secret_cost=5` probe gave results identical to off in 1,200 games (B2 is a rare ★ roll; the override path was not verified, so treat as inconclusive); Y1 is hard-coded in the bot and would need a config field |
| V5 | Larger 2P Market Leader Bonus spread (e.g. 2P 1st +3) | `[TUNE]` rule | 2P only, −2 to −4 (estimate) | Already a §40 candidate (B) |

No lever needs a new game term. Any lever that does (e.g. a named "Secret purchase limit") needs User approval
first.

## 5. Follow-up: validation-script output names

`scripts/run_reference_bot_validation.py` builds the output tag as `_push` + `_params` + scope suffix
(line ~127). The `_params` tag does not encode the values of `--pr-params`, so two runs with different overrides
write the same file and the second silently overwrites the first. Fix (engineering follow-up, not done here):
add a short stable hash or a sanitised `key=value` string of `pr_params` to the file name, and store
`pr_params` in the JSON (already done) so files can be checked. The sweep avoided the problem by writing through
its own wrapper.

## 6. Open questions for the User

1. Adopt the roster rule in §3 (switch on by default for rule probes; ref1 edge check at scope `non_reference`,
   reference 71.2%, flag at ±5)?
2. Close Phase 48 at +38, or open a lever A2 for the Phase 6 comfortable-leader dump (estimated −2 to −4 more on
   the edge)?
3. VentureGreed: accept the "bot problem" diagnosis and redefine the 40% guardrail (V2), or start a roster lever
   (V1/V3)? Rule levers (V4/V5) are not recommended now.
4. Re-baseline the reference row in sweep reports to the 13-member switch-off file (78.6%) so future
   comparisons do not use the stale 69.1% file.
5. Schedule the validation-script naming fix (§5).
