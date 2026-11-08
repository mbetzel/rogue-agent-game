# Lever A regression diagnosis (Phase 48)

**Author:** game-designer, 2026-11-07. **Status:** diagnosis + proposed fix; awaiting User decision (§5).
**Inputs:** `docs/specs/lever_a_roster_upgrade_spec.md`, `docs/findings/lever_a_roster_upgrade_scoping.md`,
`sim_results/reference_bot/lever_a/v037_ref1_statelog_3p_1200.json`.
**Results:** `sim_results/lever_a/diagnosis/*_3p_1200.json` (v037, 3P, seeds 300042..301241, 6 procs).
**Harness:** a scratch driver (`/tmp/claude-1000/diag/drive.py`, not committed) that reuses
`scripts/run_reference_bot_validation.py::play` and wraps `pr_push_policy.window` (telemetry only) and, for the
two probe variants, `AdaptiveBalancedBot.choose_any_shield_allocation`. No sim/, tests/ or scripts/ edit.

## 1. Ablation (baseline cell, AdaptiveBalanced seats, n = 720 seats / 1,200 games per cell)

| Cell | Params / probe | AB win % (95% CI) | AB Patient Zero % (seat) | Patient Zero endings % | Secrets lost to Blue / game | Phase 4 in push / dump window | Blue lost in push-window rounds / game | Final Market Share | Market Leader Bonus place 1st / 2nd / 3rd % | Blocked R / B / G % |
|---|---|---|---|---|---|---|---|---|---|---|
| off | switch off | 17.2 ± 2.8 | 3.6 | 9.3 | 3.53 | 0 / 0 | – | 2.05 | 36 / 37 / 24 | 43 / 48 / 9 |
| on | defaults | 13.1 ± 2.5 | 12.1 | 13.0 | 4.83 | 59 / 2 | 2.58 | 3.43 | 57 / 26 / 5 | 57 / 35 / 8 |
| push only | `dump_max_share: 0` | 12.2 ± 2.4 | 12.4 | 13.1 | 4.97 | 59 / 0 | 2.58 | 3.47 | 58 / 24 / 5 | 58 / 34 / 8 |
| dump only | `push_min_share: 99` | 19.8 ± 2.9 | 2.9 | 9.0 | 3.09 | 0 / 4 | – | 1.94 | 31 / 38 / 28 | 40 / 51 / 9 |
| p4off (probe) | defaults; push window ignored in the Phase 4 Generic shield split | 23.0 ± 3.1 | 3.6 | 9.0 | 3.22 | 79 / 4 | 0.70 | 2.27 | 40 / 38 / 18 | 44 / 47 / 8 |
| **bluesafe (probe)** | defaults; push split used only if it blocks ≥ as many Blue as the default split | **26.5 ± 3.2** | 3.1 | 8.8 | 3.13 | 79 / 4 | 0.66 | 2.45 | 43 / 37 / 17 | 46 / 48 / 7 |

"Phase 4 in window" is the share of AdaptiveBalanced Phase 4 Generic shield decisions (one per seat per round)
in each window. Place counts exclude eliminated seats (no Market Leader Bonus), so rows sum below 100.
`dump_max_share: 0` leaves the dump window only at 0 Market Share (already a Market Collapse), so it is
effectively off.

## 2. Cause

The regression is entirely the **push window's Phase 4 Generic shield split** (A4: `PR_PUSH_POLICY`, fill
Red → Blue → Green).

1. The push window is not a narrow situational line for AdaptiveBalanced: it covers **59%** of its Phase 4
   decisions (79% once the seat survives longer). Rivals in the baseline roster sit at similar Market Share
   through v1.0–v2.0, so the gap and Secrets-band gates rarely bind.
2. Inside it, Generic shields move from Blue to Red (blocked mix 43/48 → 57/35). Market Share rises
   (+1.4 final, 1st place 36% → 57%), but each extra Red blocked costs an unblocked Blue: Secrets lost to Blue
   +1.3 per game, almost all in push-window rounds (2.58 of 4.83).
3. The Market Leader Bonus is worth at most +2 Secrets (+1 for the move from 2nd to 1st). Paying ~1.3 Secrets
   plus a 3.4× rise in Total Data Breach risk (Patient Zero 3.6% → 12.1%) to gain it is a net loss: win rate
   −4.1 pp and Patient Zero endings +3.7 pp. An eliminated seat also forfeits the bonus.
4. The other push parts (one Public Relations Track step, regain, Red bought first) are not the problem: with the
   Phase 4 split removed (p4off) the same windows give **+5.8 pp**. The dump window alone is a small gain
   (+2.6 pp, within noise of significance).
5. The ref1 seat rises (69.1% → 77.5% in the 600-game smoke) because its AdaptiveBalanced opponents now breach
   more often and trigger Patient Zero endings the reference bot is better placed to survive.

### Reference-bot comparison (hypothesis 3)

From the state log, when the reference bot's own push window condition held, it chose the
`PublicRelationsPush` line in **25.1%** of Phase 6 choices (`choose`) and 12.0% of opponent-model takes;
`fallback` (AdaptiveBalanced-like, no push) was 68%. Its push rate falls with Red pressure (`rp`): ~24% at 0–1,
9–15% at 4–7, 2% at 8. The log has no Blue-pressure field, so the Blue condition cannot be read from it
directly; the probes test it instead. Hypothesis confirmed: a fixed always-push rule is too blunt, and the cost
it misses is the Blue block it gives up.

## 3. Recommended fix

**Rule (bot heuristic, `[TUNE-BOT]`, no game rule change):** in the push window, AdaptiveBalanced computes both
its default Generic shield split and the push split; it uses the push split **only if it blocks at least as
many Blue cubes as the default split** (`push_alloc[Blue] >= default_alloc[Blue]`); otherwise it uses the
default split. The Phase 6 Public Relations Track step, regain and dice-buying colours are unchanged.

New constant: `PUSH_BLUE_SAFE: bool = True` `[TUNE-BOT]` (in `PrPushParams`), optionally generalised to
`PUSH_BLUE_SLACK: int = 0` `[TUNE-BOT]` (Blue blocks the push split may give up; 0 = the rule above).

**Expected impact (measured, baseline cell):** AdaptiveBalanced 17.2% → 26.5% (+9.3 pp, CIs disjoint),
Patient Zero endings 9.3% → 8.8%, Secrets lost to Blue 3.53 → 3.13, 1st Market Share place 36% → 43%.
The ref1 edge: see §4.

The existing `PrPushParams` cannot express this rule, so it was run as a probe hook; it needs a
principal/senior-engineer change in `pr_push_policy.windowed_any_shield_allocation`.

## 4. ref1 cell (1,200 games)

| ref1 cell | ref1 seat win % (95% CI) | AdaptiveBalanced win % (non-ref seats, n = 480) | Patient Zero endings % |
|---|---|---|---|
| off (`sim_results/reference_bot/v037_ref1_3p_1200.json`) | 69.1 ± 2.6 | 2.9 | 7.2 |
| on, defaults | 78.8 ± 2.3 | 2.1 | 12.1 |
| on, bluesafe probe | 77.1 ± 2.4 | 5.0 | 7.8 |

Blue-safe fixes the Patient Zero regression in the ref1 cell too and more than doubles AdaptiveBalanced there,
but the **ref1 edge does not return to 69%**: it stays ~8 pp higher than off. The likely reason is that the
switch also reaches the reference bot's own fallback and rollout seats (A7), so the reference bot itself gets
the Phase 6 push and dump lines; the edge then measures the reference bot's gain as well as its opponents'.
Using the ref1 edge as a lever A acceptance metric needs that confound separated (switch on for
non-reference seats only). Not tested here.

## 5. User decisions needed

1. Adopt the Blue-safe push split (`PUSH_BLUE_SAFE`, `[TUNE-BOT]`) as the lever A default, or the simpler p4off
   form (push window never changes the Phase 4 Generic shield split; 23.0%)?
2. Keep the dump window (small positive, +2.6 pp alone) as specified?
3. Should the ref1 edge be re-measured with the switch on for non-reference seats only, before it is used as the
   acceptance check?
4. Narrowing the push window itself (59–79% of rounds) is optional once the split is Blue-safe; leave as is?
