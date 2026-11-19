# v0.49 "Locked ⚠ Faces: lock all dice": Post-Telemetry Balance Assessment

**Author:** Game Designer (post-telemetry)
**Date:** 2026-11-19
**Preset:** `GameConfig.v049_roster` (inherits `v048_roster`)
**Inputs:**
- `docs/reports/v049_lock_all_dice_sweeps.md` (primary; 1,200 games per pod, seeds 42..1241, mixed1);
- `docs/plans/locked_vuln_faces_gd_plan.md` §8 (User decisions D1–D5);
- `FINDINGS.md` §62 and §64;
- `docs/reports/locked_vuln_faces_sweeps.md` (stale v0.46-base run, history only).

**New probes (this assessment):** `sim_results/v049_probe/helix_*.json`. They reuse `scripts/run_locked_vuln_sweep.py` (`play_all`, `metrics47`) with 1,200 games per pod and the same seeds. The probe script lives in the session scratchpad and monkeypatches the engine; the engine is not edited. Control H0 reproduces the main run exactly (Helix 39.52 / 26.92 / 16.77, rounds 8.41 / 8.31 / 8.06).

**Status:** Proposal only. RULES, the sim engine, pnp, tts and web are untouched.

---

## 0. Verdict

**CONDITIONAL PASS.** Ship v0.49 with safe zone `0–4` and arm B (D1 and D2 stand), once a Helix fix is chosen (§3).

Only one guardrail FAIL is both caused by the lock package and harmful: **Helix at 2P** (−7.1 pp). The other FAILs fall into three groups:
- **Pre-existing in v0.48:** late no-target, 4P company spread, colour parity.
- **Bot or metric artefacts:** 2P overall no-target, the absolute liquid-income bar.
- **Lock-caused but benign:** Market Collapse falls below the band while the combined Patient Zero + Collapse rate stays flat.

Two items were missed in the sweep report and should be logged:
1. **Real income growth.** The liquid-income FAIL is not purely a metric artefact. Income is **+18 % vs v0.48** (6.94 → 8.18 at 2P). About two-thirds of that comes from the premium faces and one-third from the lock.
2. **The gray-off control is a bot control, not a rule control.** v0.48's own Gray filter (`vuln_face_lock="GRAY"`) stays on, so Gray ⚠ faces are kept under either flag. `vuln_lock_gray` changes only two things: bot lock-awareness and the scope of the Helix bypass. The sweep report's "locking Gray costs about 0.4 Green lost" is therefore a bot-skill effect, not a rule effect.

## 1. FAIL classification

| Guardrail FAIL | Class | Evidence |
|:--|:--|:--|
| Market Collapse below v0.45 ±5 (all pods) | **Lock-caused, benign.** The absolute bar is the wrong instrument here. | The Patient Zero + Collapse pair holds: v0.48 67.7 / 70.8 / 76.7 → v0.49 67.9 / 71.0 / 78.5. Singularity is flat: 25.3 / 27.3 / 22.7 → 24.2 / 26.5 / 21.2. See §2.2. |
| No-target overall, 2P (71.3) | **Bot artefact.** The lock-aware filter now includes Gray. | The rule-equivalent gray-off control reads 66.0 (PASS). |
| No-target rounds 7+, 2P / 3P (74.2 / 63.7) | **Pre-existing.** | v0.48 read 70.7 / 60.5. Gray-off reads 71.2 / 60.4, the same as v0.48. The extra +3.5 pp is bot skill. |
| Liquid income ≤ v0.45 ×1.25 | **Absolute bar: metric artefact.** v0.48 already reads ×1.69 in this metric. **The delta is real**, though: +18 % vs v0.48. | Probe: the NOPREMIUM arm reads 7.36 / 7.45 / 7.47 (lock +6 %); main reads 8.18 / 8.26 / 8.25 (premium faces add another +11 %). |
| 4P company spread 20.1 | **Pre-existing**, worsened by the lock (+3.3 pp, near noise). | v0.48 16.8, v0.46 15.7. Spread is a max-minus-min over 7 companies with an SE of about 1.7 pp each. |
| Per-colour parity | **Pre-existing / metric artefact.** | Only the company-die view flags (company strength confound), as in the v0.47-draft report. |
| Helix 2P −7.1 pp (CI −13.4 to −0.2) | **Lock-caused** (D3 rule). | See §3. |
| Operator +3.4 / +3.6 pp | **Noise.** Watch item. | Both CIs include 0. |

## 2. Questions

### 2.1 Safe zone: `0–4` vs `0–3`

D1 was set on the v0.46 base, where the lock plus three Gray ⚠ faces pushed 2P Green lost to 3.2. On the v0.48 base the lock pressure is lower, and `0–4` now overshoots: main runs **−0.47** Green lost below v0.48. B_safe03 lands closer to v0.48.

| 2P / 3P / 4P | v0.48 | main (0–4) | B_safe03 | A_safe03 |
|:--|:--|:--|:--|:--|
| Green lost | 2.29 / 2.11 / 1.92 | 1.82 / 1.62 / 1.45 | 2.11 / 1.88 / 1.67 | 2.08 / 1.85 / 1.66 |
| No-target, rounds 7+ | 70.7 / 60.5 / 52.5 | 74.2 / 63.7 / 55.5 | 68.5 / 60.4 / 51.2 | report: PASS |
| Rounds | 8.31 / 8.37 / 8.12 | 8.41 / 8.31 / 8.06 | 8.14 / **7.95** / 7.83 | 8.03 / 7.84 / 7.77 |
| Patient Zero | 31.3 / 54.4 / 60.4 | 41.8 / 60.7 / 68.4 | 44.1 / 66.1 / 70.5 | 43.8 / 66.5 / 70.7 |
| Singularity | 25.3 / 27.3 / 22.7 | 24.2 / 26.5 / 21.2 | 20.9 / 21.6 / 18.3 | about 19.6 / 18.1 / 17.1 |
| 4P company spread | 16.8 | 20.1 | **25.6** | n/r |
| Helix 2P | 46.7 | 39.5 | 37.4 | 42.1 |

**Recommendation: keep `0–4`.**
- `0–3` restores Green bite, but the price is too high:
  - 3P runs −0.42 rounds vs v0.48;
  - Singularity drops −4 to −6 pp;
  - Patient Zero adds a further +2 to +5 pp on top of main;
  - 4P company spread worsens (25.6) and Helix 2P worsens;
  - and it still fails the 2P late no-target bar (68.5).
- Most of the no-target excess is pre-existing or bot skill (§1), so `0–3` would be treating the wrong cause.
- The data does not argue against keeping the premium faces (B). The cost of B is the income delta (§1); it is not a pacing cost.

### 2.2 Market Collapse "below band"

This is desirable, or at worst neutral. The lock moves endings from Collapse to Patient Zero and leaves the pair and Singularity unchanged. Collapse stays a live ending: 26 % at 2P and 10 % at 3P/4P, which is only about 1.3 pp below the v0.45 lower edge at 3P/4P.

The likely mechanism comes from the plan's math (§2):
- Under the lock, a third of colored dice are committed to their core ⚠ face. Previously these dice were rerolled to fish for the Secret face or ★.
- So end Secrets fall by −1.7 / −1.0 / −0.7 even though Green lost falls too.
- Players breach more often, and Market Share is kept more often.

The real cost is UX: more games end through elimination (Patient Zero +6 to +10 pp). Proposed guardrail restatement, following the §62 intent:
- Patient Zero + Collapse ≤ v0.48 + 3 pp;
- Collapse ≥ 8 % at 3P/4P.

### 2.3 Helix (once per game)

All probes use 1,200 games per pod. Δ is against v0.48 (46.7 / 25.4 / 17.5); the bar is ≥ −2 pp. The Helix seat SE is about 2.4 pp at 2P.

| Variant | Helix 2P / 3P / 4P | Δ 2P | Once/game? |
|:--|:--|:--|:--|
| main (H0) | 39.5 / 26.9 / 16.8 | −7.1 | yes |
| H3: bot spends whenever gain > 0 | 38.3 / 27.1 / 16.8 | −8.4 | yes |
| H1: + legacy face-set (turn 1 die to any non-★ face) | 41.9 / 27.2 / 17.5 | −4.8 | yes |
| H2a: Root Override Hijack can't mark an unused Bypass | 42.1 / 27.9 / 18.4 | −4.6 | yes |
| H2b: as H2a, but lose 2 Secrets instead | 35.2 / 22.9 / 14.2 | −11.5 | yes |
| **H1B: H1 + H2a** | **45.2 / 28.2 / 19.2** | **−1.5** | **yes** |
| helix_per_version | 41.9 / 29.0 / 19.2 | −4.8 | no |
| helix_legacy | 46.0 / 30.8 / 21.0 | −0.7 | no |

What the probes show:
- The bot is not under-using the Bypass. Use share is 34–39 %, and loosening the bot's gain gate (H3) does nothing.
- The power's real limits are its per-use value (it removes about 1.1–1.3 ⚠) and the Black burn (34–40 % of Helix seats).
- **A once-per-game "reroll locked dice" power cannot reach parity on its own.** Even the per-Version version is −4.8 at 2P.

**The smallest once-per-game fix is H1B,** which passes the bar at all pods. Proposed text: "Once per game: you may reroll locked dice this phase, and turn 1 rolled die to any non-★ face of its colour. Root Override Hijack cannot mark Brute-Force Bypass Used."

The fallback is H1 alone, accepting a 2P residual of about −5 pp.

### 2.4 ref1

| Preset | ref1 win % | ref1 seats with 2+ L4 |
|:--|:--|:--|
| v0.46 | 44.9 | 28 % |
| v0.48 | 53.0 | 77 % |
| v0.49 | 60.7 | 86 % |

These runs used 600 games, so the v0.49 rise is about 2.7 SE.

- **More than half of the growth predates the lock.** The thinning and QC rewards in v0.48 created the double-capstone line. v0.49 adds research income (+18 %) and committed rolls, which lookahead play can exploit.
- **This is not a fixed degenerate stance.** PenTestRush is neutral (+0.3 pp), and ref1 mixes 5 stances.
- **The field never reaches 2 L4 under any preset.** That is bot under-adaptation in research focus.
- ref1 sits at the low end of the v0.36–v0.38 accepted range (66.6–78.6 %).

**Not blocking.** Follow-ups:
- run ref1 at 1,200 games on v0.48 and v0.49;
- add a fixed "double capstone" stance to the dominance matrix. If that stance beats Adaptive by more than 5 pp, it is a real line, rooted in v0.48, and needs a capstone-cost fix.

### 2.5 Push-your-luck

The intended reroll tension is present.
- Each reroll of a clean R/B/G/P die carries a 2/6 chance of a committed ⚠.
- The observed P(★) is 0.164. That matches the lock-safe theoretical rate of 0.167 (it was 0.199 before the lock), so bots play the "safe" line.
- Both extremes lose against an Adaptive field:
  - NoColorReroll −18.5 pp;
  - KeepAll −13.8 pp;
  - StarChase −7.0 pp.
- Adaptive keep rate is 62 %. Locks are 1.8 per player-round; about 0.36 of them are Gray, and the Gray ones are unchanged from v0.48.

Caveat: at 2P late game, about 74 % of Green cubes find no target. The penalty side of the gamble is muted there; this is a pre-existing 2P issue.

### 2.6 Doc impact (later sync; no edits made)

| Item | Where |
|:--|:--|
| "Lock-in & Assign Dice" / "Lock-in & Deploy Dice" → **Deploy** | `RULES.md:188`, `RULES_QUICKREF.md:78`, `GLOSSARY.md:41` and `:99`, `RULES_APPENDIX.md:19`, `pnp/generate_pnp.py` (2 hits) |
| "locked player" / "(non-locked)" → **Target-Locked player** | `GLOSSARY.md:33`, `RULES.md` (1 hit), `RULES_QUICKREF.md:130` |
| **Collision:** the Institutional Override Track status "**Locked**" (Locked / Available / Used / Forfeited) vs "locked die" | `GLOSSARY.md:17`. This needs a User decision: keep both with a strict "locked die" noun form, or rename one (a new term needs approval). |
| v0.48 "Gray ⚠ faces must be kept" → "**every die showing ⚠ is locked**" (colored core, R&D and Gray) | `RULES.md:183`, `RULES_QUICKREF.md:77`, `GLOSSARY.md:82`, `RULES_APPENDIX.md:19` |
| Safe zone `0–3` → `0–4`; bands `4–6 / 7–9 / 10+` → `5–7 / 8–10 / 11+`; Vulnerability table | `RULES.md:28`, `:30`, `:262`, `:264`; `RULES_QUICKREF.md:11`, `:121`; `GLOSSARY.md:36`, `:40`, `:41`; pnp (1 hit); also the CLAUDE.md pillar text (User-owned) |
| Brute-Force Bypass text (currently the legacy "+1 reroll and set 1 face") | `RULES.md:186`, `RULES_APPENDIX.md:87`, `GLOSSARY.md` (1 hit), `pnp/generate_pnp.py:95` |
| Premium ⚠ faces (V046_VULN) | `RULES_APPENDIX.md` face tables, pnp die art |
| New glossary entry: **locked die** (approved as D4) | `GLOSSARY.md` |
| Version bump to v0.49.0 and TTS rebuild | the CLAUDE.md version list |

## 3. Recommended User decisions

1. **Safe zone:** keep `0–4` (D1). `0–3` costs 3P −0.42 rounds, −4 to −6 pp Singularity and +6.2 pp 4P company spread, and still fails 2P late no-target.
2. **Helix:** adopt H1B (once per game + face-set + immune to Root Override Hijack): 45.2 / 28.2 / 19.2, Δ 2P −1.5. The fallback is H1 (Δ 2P −4.8). Once-per-game lock bypass alone cannot reach parity.
3. **Market Collapse guardrail:** replace the v0.45 ±5 row with Patient Zero + Collapse ≤ v0.48 + 3 pp and Collapse ≥ 8 % at 3P/4P. Accept the shift toward elimination endings (Patient Zero +6 to +10 pp).
4. **Income:** accept the +18 % income vs v0.48 (premium +11 %, lock +6 %) as the price of D2, and re-base the absolute income row on v0.48 with ≤ ×1.20.
5. **ref1:** not blocking. Run a 1,200-game ref1 and a double-capstone stance before v0.50.
6. **Term collision:** choose how to handle the Institutional Override "Locked" status vs "locked die".
