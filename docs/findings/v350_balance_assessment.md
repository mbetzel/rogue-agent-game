# v0.35.0 Balance Assessment (Phase 43, game-designer)

**Date:** 2026-11-06 · **Inputs:** `v350_telemetry_sweep_report.md`, `v350_telemetry_summary.json`, `v350_research_income_sweep.md`, plan `docs/explorations/2026_11_research_track_rebalance_plan.md` §4 / §6.
**No changes** were made to `sim/`, `web/`, `pnp/`, `RULES.md`, `PLAN.md` or `FINDINGS.md`.

## Verdict

**Sign off v0.35.0 as-is (no rules tuning package).** Both guardrail FAILs trace to bot policy or to an already-accepted structural issue, not to the v0.35 rules. Two small bot-policy follow-ups are recommended (not rule changes).

## 1. Targeted slice: fixed vs random research focus

Script: scratch driver calling `scripts/run_v350_telemetry_sweep.run_pod("V035", n, 1500, 777)`; the "random" cell sets `research_focus_mode="random"` on every bot class (existing engine/bot option, seeded per bot). 1,500 games per pod, base seed 777.

| Metric (2P / 3P / 4P) | Fixed focus (shipped bots) | Random focus |
|---|---|---|
| Patents share of maxed tracks | 59.7 / 60.1 / 59.4% ❌ | **21.7 / 23.6 / 22.1%** ✅ |
| Release share | 30.7 / 30.6 / 30.3% | 30.4 / 29.6 / 30.5% |
| Defense share | 3.1 / 2.9 / 3.4% | 28.6 / 27.5 / 28.2% |
| Triage share | 6.5 / 6.3 / 7.0% | 19.3 / 19.3 / 19.1% |
| Mean rounds | 8.89 / 8.70 / 8.56 | 8.84 / 8.57 / 8.45 |
| Total Wipeout | (sweep: 16.0 / 5.8 / 1.9%) | 15.9 / 5.6 / 2.3% |
| Patents L4 Secrets per holder | 4.6 / 4.4 / 4.9 | 3.2 / 3.3 / 3.5 |
| Release L4 extra reroll uses / holder | 0.05 / 0.07 / 0.08 | **1.12 / 1.18 / 1.06** |
| Defense L4 $ / holder | 7.7 / 7.0 / 6.6 | 5.9 / 5.6 / 5.7 |
| Triage L3 take rate | ~36% | 51 / 55 / 55% |
| Bot win spread (pts) | 23.4 / 33.1 / 38.4 | 28.5 / 32.1 / 31.1 |
| DTO win rate | — | 56.1 / 43.1 / 34.2% |
| Purple lost / seat | — | 0.28 / 0.24 / 0.22 |

**Reading:** with neutral focus, Patents is the *least* concentrated track except Triage (~22%), well under ~50%. The 59% figure is a direct consequence of the bot roster: 2 of 5 bots (Venture Greed, Reckless Saboteur) put Patents first and Accelerationist puts it second, and the late-game filing rule pushes leftover 🔬 into Patents. Patents L4 yield also drops ~30% when not paired with a Patents-first bot, so there is no evidence of a dominant L4. **Not a design dominance; no [TUNE] needed.**

Contingency only (if human playtests show Patents over-pick): raise Patents L4 rate `1→1` to `2→1` before touching L0 (`2→1`), since L4 drives the 20+ Secret outliers.

## 2. 2P Total Wipeout 16.0%

Unchanged under random focus (15.9%), and v0.34 was 16.5%. It is insensitive to research policy, so it is the same structural 2P effect the User accepted in FINDINGS §29. **Recommend accept** (1 pt over, slightly improved).

## 3. DTO (characterization only; companies deferred)

DTO 58 / 43 / 35% (fair share 50 / 33 / 25%), +8 to +10 pts; identical under random focus (56 / 43 / 34%), so it is a company effect, not a bot artifact. Remaining asymmetry is the once-per-game Slush Fund (used in ~94% of DTO seats) plus survival (70–82%). Company spread 14–16 pts vs ~65–70 in v0.34. Leave for the company-identity phase.

## 4. Triage L3, Release L4, Defense L4

| Item | Finding | Bot artifact or design? |
|---|---|---|
| Triage L3 62–65% forfeit (cash) | Falls to ~45–49% with random focus; seats that build Triage seriously can afford `$3`. | Mostly bot (no saving for $3, fixed-focus bots reach L3 incidentally). Mild design watch: `$3` at L3 competes with Market buys. |
| Triage L3 always Yellow | First colour in fallback order. | Bot artifact. Colour choice needs a heuristic before colour balance can be read. |
| Release L4 extra reroll ~0.07 uses | 1.1 uses/holder with random focus. Accelerationist (sole Release-first bot) rarely exhausts base rerolls. | Bot artifact. Real payoff is Bandwidth 6 + 1 reroll; acceptable. |
| Defense L4 ~$7/holder | Holders are few (3% of maxes) and are SecOps (defense-heavy) seats; random-focus holders get ~$5.7. Cap `$3`/round. | Fine. Not over-tuned; Defense is a viable focus under neutral bots (28% of maxes). |

## 5. Purple permanent loss (OQ-10)

0.25–0.31 per seat (random: 0.22–0.28) vs 0.16–0.24 in v0.34; 42–45% of games lose at least one. Patents L3 adds 0.38/seat, so the net Purple supply is roughly flat. Keep on watch; no action unless playtests report feel-bad Burn Notice losses.

## 6. v0.34 same-seed mismatch (2P DTO 88% vs 76%)

The research policy is gated on `is_v035_tracks`, so the ported bot code should not affect `legacy_v034()`. The gap is most likely either a metric-definition difference (the v350 script splits tied Total Wipeout wins and uses the engine's v0.35 ledger) or an incidental behaviour drift in the modified bots/engine when running `legacy_v034()`. **It does not affect the v0.35 verdict:** every v0.35-vs-v0.34 comparison uses the same script and seeds, and all v0.35 guardrails are judged on absolute targets. Recommend a one-off staff-engineer check that `legacy_v034()` reproduces the v340 report on its seeds before v0.34 numbers are cited again.

## 7. Bot heuristic note: patent filing AND vs OR

`research_policy.plan_research` withholds filings when *focus < L4* **OR** *🔬 < reserve_floor* (i.e. files only when focus is at L4 **AND** 🔬 ≥ 4), except in the late game. Seats that never reach L4 therefore hoard 🔬 until the late trigger, then file at their current (often poor 2→1) Patents rate. An OR-style rule ("file when focus is at L4 *or* 🔬 ≥ floor") would file earlier. This is a bot heuristic choice, not a rule; it biases toward Patents-first seats (which reach L4 and file at 1→1). Record for the bot-roster backlog.

## 8. Decisions for the User

1. **Accept Patents concentration as a bot-roster artifact** (59% fixed vs ~22% random focus) and sign off without a Patents [TUNE]? (Recommended: yes.)
2. **Accept 2P Total Wipeout 16.0%** as structural per FINDINGS §29? (Recommended: yes.)
3. **Accept 🔬 income 11.8–12.0** (target 12–14) as within tolerance? (Recommended: yes.)
4. Approve bot-only follow-ups (no rule change): (a) rebalance the roster's research focus so at most 1 bot is Patents-first, or run the official sweep with random focus; (b) Triage L3 colour heuristic; (c) decide AND vs OR filing rule.
5. Keep DTO and Purple attrition (OQ-10) as watch items for the company-identity phase.
6. Ask staff-engineer to verify `legacy_v034()` reproduces the v340 report (low priority).
