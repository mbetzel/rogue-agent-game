# v0.37 Reference Bot Portfolio Attribution (game-designer, 2026-11-07)

Question: the 13-member portfolio (adds PublicRelationsPush + MarketShareDump) raised ref1 v0.37 3P win from 69.1% to 78.6%. Which line is it, and does it overturn §40 "no kamikaze" / §38 "Public Relations-first loses"?

Method: scratch wrapper `sim_results/reference_bot/attribution/run.py` (copy of `/tmp/claude-1000/attr/run.py`) monkeypatches `reference_search.build_portfolio` to drop members; replays `scripts/run_reference_bot_validation.py::build_engine` ref1, 3P, seeds `42 + 300000 + idx`, 1,200 games, 8 procs. Market Collapse off = `GameConfig.v037(market_collapse_enabled=False)` (same hook as §40). Analysis: `an.py`; raw output `summary.txt`. The 11-member cell reproduces §40 exactly (69.1%; 375 at-0 / 195 won / 59 alone / 22 won), so the harness is the same.

Notes: "Lead at trigger" = ref Secrets minus best rival at the end of the trigger round, over all ref-at-0 trigger games (§40 quoted wins only). Choice shares count the "fallback" label in the denominator.

## Attribution table (3P ref1, v0.37 unless marked)

| Cell | Win % (95% CI) | Δ vs 11 | Collapse off win % | PZ / Sing / MC % | Ref at 0 at MC (won) | Alone (won) | Lead at trigger | MS lost to Red ref / rivals | Regain ref / rivals | PR level ref / rivals | MLB 1st / 2nd / 3rd % | Blocks R / B / G % | Red block rate | Choice P4 push/dump · P6 push/dump |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 members | 69.1 ± 2.6 | — | 66.7 ± 2.7 | 7.2 / 35.4 / 57.2 | 375 (195) | 59 (22) | +1.22 | 16.4 / 17.7 | 1.31 / 2.06 | 0.65 / 0.20 | 64 / 25 / 11 | 36 / 49 / 15 | 0.29 | — |
| A: + push | 74.2 ± 2.5 | +5.1 | 68.0 ± 2.6 | 7.2 / 34.4 / 58.2 | 254 (137) | 35 (14) | +1.04 | 15.5 / 17.8 | 0.98 / 2.01 | 0.95 / 0.21 | 78 / 17 / 5 | 42 / 47 / 11 | 0.33 | 20.2/– · 7.2/– |
| B: + dump | 76.3 ± 2.4 | +7.2 | 78.6 ± 2.3 | 6.3 / 35.4 / 58.2 | 446 (311) | 94 (46) | +2.54 | 16.2 / 17.7 | 0.87 / 2.08 | 0.62 / 0.20 | 63 / 26 / 11 | 34 / 50 / 17 | 0.28 | –/14.5 · –/9.7 |
| C: all 13 | 78.6 ± 2.3 | +9.5 | 77.6 ± 2.4 | 6.5 / 35.8 / 57.7 | 321 (225) | 51 (26) | +2.13 | 15.5 / 17.8 | 0.68 / 2.02 | 0.89 / 0.20 | 75 / 19 / 7 | 40 / 47 / 13 | 0.32 | 14.9/8.8 · 6.6/7.3 |
| C on v0.36 | 77.8 ± 2.4 | (v0.36 11: 66.6) | — | 5.1 / 22.6 / 72.3 | 471 (364) | 50 (33) | +1.65 | 16.1 / 17.8 | 0.44 / 1.44 | 0.97 / 0.38 | 60 / 28 / 12 | 32 / 51 / 17 | 0.26 | 14.8/10.0 · 6.8/3.3 |

Collapse-off endings: Singularity ~83–84%, Patient Zero ~16%, +0.75 rounds (as in §40).

## Findings
1. **Both lines contribute, and they overlap.** Push alone +5.1, dump alone +7.2, together +9.5 (not additive; each covers part of the other's gap over the scripted policies).
2. **Push = undervalued Red blocking + moderate Public Relations, and it works through Market Collapse.** The ref blocks more Red (42% of blocks, rate 0.33), loses less Market Share, reaches Public Relations level ~0.95, holds 1st Market Leader Bonus place 78% of the time, and is at 0 when Collapse triggers far less often (254 vs 375). With Collapse off, push is worth only +1.3: most of its value is staying off 0 when Collapse ends the game (and taking the +2 Bonus).
3. **Dump is not a kamikaze line.** It is a "spend on Secrets, ignore Market Share" line: fewer Red blocks, less regain, higher Secrets lead (+2.5) at trigger. It is at 0 alone more often (94 games, won 49%, versus fair share 33%), but it gets *stronger* with Collapse off (+11.9 vs +7.2). Collapse costs it about 2 points rather than feeding it. Its value comes from Market Share being cheap to give up (only the Market Leader Bonus is at stake), not from ending control.
4. **§40 "no kamikaze" stands.** Its supporting point 2 needs a softer wording: Collapse is still worth only ~1 point to the full portfolio (78.6 → 77.6 off).
5. **§38 "Public Relations-first loses" stands, refined.** The fixed Public Relations-first rotation still loses. A situational push (Red blocks plus Public Relations when the Bonus or a Collapse is in reach) wins. Public Relations is undervalued by the scripted policies, not overpowered.
6. The v0.36 result is similar (77.8%, +11 over 11 members), so it is not specific to the Market Leader Bonus.

## Candidate levers (none decided; modeled impact is a direction or estimate, not measured)
- **A. No rule change; update bots.** Teach the scripted policies (AdaptiveBalanced, Mixed) the push heuristic (Red-block weight when near 0 or near the Bonus). Expected: ref edge back toward ~+35 over fair share, and archetype win rates shift toward the policies that adopt it. Recommended first, because it measures the rules against a stronger roster.
- **B. Larger 3–4P Market Leader Bonus gap ([TUNE], e.g. 1st +3 / 2nd +1).** Raises the cost of the dump line (whose 1st-place share stays at ~63%) and the value of push. Estimate: dump's edge falls by ~1–2 points per +1 on the gap; it may push Blue-first down further (§38 risk: Patient Zero up).
- **C. Stronger Red (more Market Share lost per unblocked Red, [TUNE]).** Makes ignoring Market Share costlier. Estimate: more Collapse endings and more simultaneous 0s (Total Wipeout-style risk from §32), so this needs a probe.
- **D. Secrets penalty at 0 Market Share.** A new rule that likely needs a **new term: User approval required**. It hits the dump line directly; Unpaid Ransom Leak echo risk (deprecated term, do not resurrect).
- No lever is needed for kamikaze, since none exists.
