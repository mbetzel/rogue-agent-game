# Teaching the roster ref1's "early Market Collapse" play: pre-SDLC scoping (game-designer)

Date: 2026-11-09 · HEAD a5deb71 · preset `GameConfig.v038c()` (RSP-1, owner yield 2, Market Share 13/16/17, γ 0.75, end payout on Market Collapse per §14.5.10) · bot-only, no rule / glossary change · nothing in `sim/` edited.

Scratch: `diag.py` (ref1 decision/state log), `an.py`, `an2.py`, `probe.py` (monkeypatch switch), `ps.py`; outputs `*.json` in this folder.

## 0. Headline

The premise does not hold on like-for-like harnesses. ref1 is **not** collapsing the market more than the roster does, and it is the 0-Market-Share player **less** often than a Mixed seat. The "52–78% vs 20–39%" gap compares two different harnesses:

- ref1 numbers come from `scripts/run_reference_bot_validation.py` (no Client Companies, no White Hat Operatives, no Variant setup: `_bot_classes()` rotation only).
- mixed1 numbers come from `scripts/run_v380_secret_faces_sweep.py` (random Companies / White Hats / Variants, `enable_corporate_asymmetry`).

The no-Company harness ends far more games by Market Collapse for **every** roster. Every probed collapse trigger made the Mixed seat weaker or left it unchanged. Recommendation: **do not add a collapse trigger**; re-baseline the claim instead (§6).

## 1. ref1 re-measured on v038c (600 games, validation harness, `--pr-push on`, non_reference, seeds 42+P·100000+i)

| | 3P ref1 | 3P mixed1 (same harness) | 2P ref1 | 2P mixed1 (same harness) |
|---|---|---|---|---|
| special-seat win | **84.2% (+50.8)** | 31.8% (−1.5) | **91.0% (+41.0)** | 49.7% (−0.3) |
| Market Collapse ending | 49.2% | 52.5% | 74.8% | 74.5% |
| special seat is a 0-Market-Share trigger (share of all games) | **15.0%** | 32.8% | **39.2%** | 61.0% |
| ref win when it is the 0 seat / Collapse by others / no Collapse | 66.7 / 91.7 / 84.3% | | 88.1 / 93.9 / 91.4% | |

The same check on the sweep harness (Companies on; the rule-sweep roster): 3P ref1 76.3% (+43.0), Market Collapse **19.5%** (mixed1 21.0%), ref is the 0 seat in **6.8%** of games (Mixed seat 12.0%); 2P ref1 92.0% (+42.0), Market Collapse **40.0%** (mixed1 36.0%), ref is the 0 seat in **16.3%** (Mixed 27.7%), Singularity 48.5%. On like-for-like harnesses ref1's Collapse share matches the roster's (within ~4 pts), and ref1 is the 0-Market-Share player about half as often.

Did §14.5.10 weaken it? It did not change the roster at all (mixed1 with `red_secret_payout_skip_on_collapse=True` vs False: identical endings, Mixed ±0.3 pts). The ref edge on this harness (+50.8 at 3P) is in line with §43.5 (+49.6), so §14.5.10 neither strengthened nor removed the ref edge. The edge does not come from collapsing.

## 2. When ref1 collapses (diagnostic replay, state at the start of the collapse round)

ref-triggered Collapses, 3P n = 90 / 2P n = 235:
- **Late, not early:** rounds 8–10 (3P mode 9; 2P mode 9), Version v3.0 in 87% / 66%, estimated rounds left 2–3.
- **Market Share already low by attrition:** 1–5 at the start of the round in 89% / 95%. The ref's Market Share track mirrors its rivals' track (3P round 8: ref 8.5 vs rival mean 8.6; 2P round 8: 6.4 vs 6.0). Everyone erodes together. There is no early dive.
- **Secrets lead is usually large but not required:** lead ≥ +6 in 29% (3P) / 61% (2P); behind in 29% / 13%.
- **Payout position:** lowest Market Share at the table in 59% / 59% of these.
- **Decision that does it:** the Phase 4 Generic shield split. The ref picks the MarketShareDump line at own Market Share ≤ 2: 87–100%; at 3–5: 49–70%; at 6–8: 1–10%; at ≥ 9: 0%. The Secrets lead makes **no difference** (lead ≥ 3 vs < 3 within 7 pts in every bucket). This is the lever A dump window (`DUMP_MAX_SHARE` 5) already measured in Phase 48.

### Why the lever A dump line "does not fire under v038c"
1. `v038c()` (like `v038`/`v038b`) leaves `bot_pr_push=False`. `run_v380_secret_faces_sweep.py --config v038c` does not set it either, so rule sweeps run lever A **off** (FINDINGS §43.3 notes this). Only the ref1 check passes `--pr-push on`.
2. Even when on, only AdaptiveBalanced (and a Mixed seat whose phase-4 draw is AdaptiveBalanced) has `pr_push_capable`. The other four archetypes never window.
3. The dump window also needs `ms - hi <= -2` or Red threat, which cuts it further.

## 3. Candidate trigger rules (all `[TUNE-BOT]`, monkeypatched; switch default off = byte-identical)

One switch, `bot_collapse_play` (proposal only; not built). It acts at the decisions the dump window already owns:
- Phase 4 Generic shield split → `DUMP_POLICY` / Blue → Green → Red fill (`blue_lethal_value` still first).
- Phase 6 research → no Public Relations Track step, no Market Share regain.
- Market dice buying → no Red for Market Share (DUMP colours); no Red purchase nudge; no Ad Campaign.
- Phase 1 shield commits: unchanged.

It applies to **all five archetypes** (BaseBot and AdaptiveBalanced Phase 4 hooks, plus the shared `prp.window`), so a Mixed seat gets it whatever it draws. Reference-owned bots and rollouts are excluded, as with `non_reference`.

Variants probed:
- **L*k* "lead dump":** own Corporate Secrets − best surviving rival ≥ *k* → dump at any Market Share. Options: `maxms`, `minv` (Version index).
- **F*k* "finisher":** lead ≥ *k* **and** own Market Share ≤ Red still unblocked this Phase 4 (+ margin) → do not block Red, so the Collapse lands this round. Outside Phase 4 it uses Red pressure (Cup + Baffles).
- **D*m* "dump for all archetypes":** own Market Share ≤ *m* (lead ≥ −99 / ≥ 0), i.e. the ref's measured behaviour.

## 4. Probe results (sweep harness = rule-sweep roster, mixed1, seeds 42..641, 600 games per cell)

Head-to-head (switch on for the Mixed seat only, off for the rest). Control: Mixed 29.7% (3P) / 47.7% (2P). SE ≈ ±1.9 / ±2.0 pts, same seeds.

| rule | 3P Mixed win | 3P MC % | 2P Mixed win | 2P MC % | 2P Sing % |
|---|---|---|---|---|---|
| off | 29.7 | 21.0 | 47.7 | 36.0 | 42.2 |
| L1 (lead ≥1) | 25.0 | 26.3 | 39.3 | 45.2 | 36.0 |
| L2 | 25.3 | 24.0 | 41.3 | 44.3 | 37.2 |
| L3 | 26.7 | 22.8 | 42.8 | 42.8 | 37.5 |
| L2, ms ≤ 8 | 29.2 | 22.2 | 47.3 | 39.5 | 39.2 |
| L2, v ≥ v2.0 | 25.5 | 22.7 | 44.2 | 42.0 | 38.5 |
| F0 / F1 / F2 / F3 (finisher) | 28.5 / 29.0 / 29.0 / 29.3 | 21.3–21.8 | 47.7 (all) | 38.5–39.7 | 38.8–39.8 |
| F1 + margin 2 | 29.3 | 21.5 | 47.7 | 39.7 | 38.8 |
| D3 / D4 / D5 / D6 | 28.8 / 28.3 / 28.5 / 27.8 | 21.2–23.7 | 47.5 / 47.5 / 46.7 / 46.5 | 37.3–42.2 | 36.3–41.2 |
| D5, lead ≥ 0 | 28.7 | 21.3 | 48.0 | 39.2 | 39.2 |

No variant beats control. The "lead dump" costs 3–8 pts: under RSP-1, Market Share position decides every Red Secret payout (+3 / +1) **and** the end payout (now paid on a Collapse too, §14.5.10), so a script that sheds Market Share early gives those Secrets away. The finisher and the late dump are inert (≤ ±1 pt): by the time they fire, the game is already decided.

Switch on for all seats (endings):

| rule | 3P MC / PZ / Sing | 2P MC / PZ / Sing | TW 2P | rounds 3P / 2P |
|---|---|---|---|---|
| off | 21.0 / 34.7 / 44.0 | 36.0 / 19.0 / 42.2 | 2.8% | 8.28 / 8.41 |
| D5, lead ≥ 0 | 22.3 / 34.2 / 43.2 | 41.3 / 19.2 / 37.0 | 2.5% | 8.25 / 8.27 |
| F1 | 22.8 / 34.0 / 42.8 | 41.8 / 18.8 / 36.7 | 2.7% | 8.24 / 8.27 |
| L2 | 30.8 / 30.5 / 38.3 | 51.0 / 17.5 / 29.7 | 1.8% | 8.20 / 8.11 |

ref1 edge with the roster upgraded: sweep harness, 3P, 600 games, non-ref seats on D5 (lead ≥ 0): ref 76.0% (+42.7) vs 76.3% (+43.0) off. No change.

## 5. Risks
- **Kamikaze / degenerate:** L-rules make the leader shed Market Share on purpose. Collapse rises 10–15 pts with no skill gain. That pattern ("end it while ahead") is what the User wants to keep "viable, not too strong", and in the scripts it is *not* viable. No Total Wipeout increase in any cell (2P 1.8–3.2%, 3P 0.3%), since the Collapse does not eliminate.
- **2P Singularity guardrail ≤ 43%:** every switch-on cell **lowers** 2P Singularity (42.2 → 29.7–39.8%). No guardrail risk. A roster-wide L2 would, however, change what rule sweeps measure (2P Collapse 36 → 51%).
- **Measurement risk (the real one):** comparing ref1 MC% (no-Company harness) with mixed1 MC% (Company harness) mislabels a harness effect as a ref tactic.

## 6. Recommendation (for User sign-off)
1. **Do not implement a collapse trigger now.** No explainable rule makes the roster stronger, and the lead-based rule makes it weaker and inflates Collapse. The ref's own collapse behaviour is the lever A dump (Market Share ≤ 5, Phase 4), and copying it to all archetypes is neutral (±1 pt).
2. **Fix the measurement first:** run the ref1 edge check on the sweep harness (Companies on), or report mixed1 on the validation harness next to ref1, so Collapse shares compare like with like. On the sweep harness the ref1 edge is +43 (3P) and +42 (2P), with Collapse 19.5 / 40.0%.
3. Optional, low value: if parity of the bot model with the ref is wanted anyway, extend the lever A dump window to all archetypes (D5, lead ≥ 0) behind `bot_collapse_play` default off. Expected effect: Mixed ±1 pt, 2P Collapse +5 pts, 2P Singularity −5 pts. No new game term is needed.
4. The ref1 edge (+41 to +51) is a search-skill gap elsewhere (Phase 6 plan choice and Phase 4 PR push), not the Collapse.
