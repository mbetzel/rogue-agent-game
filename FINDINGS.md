# Rogue Agent — Monte Carlo Simulation Findings & Balance Index

This document tracks verified balance takeaways, bot meta equilibria, card tiering, and active tuning targets for Rogue Agent.

> [!NOTE] Historical Archives
> Full statistical datasets, raw telemetry tables, and sweep outputs are archived in:
> - [docs/findings/v0.2_to_v0.7_historical_sweeps.md](docs/findings/v0.2_to_v0.7_historical_sweeps.md): Core economy, starting resources, 2P buffers, and contractor tuning.
> - [docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md](docs/findings/v0.8_to_v0.9_variant_and_archetype_sweeps.md): Choice faces, 15 Module Variants (★), Asymmetric Payloads, and Consultancy Archetypes.
> - [docs/archive/FINDINGS_s01-s35.md](docs/archive/FINDINGS_s01-s35.md): Sections §1–§36 (Phases 15–45, v0.13–v0.36 baselines).
> - [docs/archive/FINDINGS_s37-s43.md](docs/archive/FINDINGS_s37-s43.md): Sections §37–§43 (Market Share threshold probes, Market Leader Bonus, v0.38 exploration).
> - [docs/archive/FINDINGS_s44-s49.md](docs/archive/FINDINGS_s44-s49.md): Sections §44–§54 (Phases 50–59, v0.38c–v0.41.0 baselines; file name kept for link stability).
> - [docs/archive/FINDINGS_s55-s57.md](docs/archive/FINDINGS_s55-s57.md): Sections §55–§57 (Phases 60–62, v3.0 escalation, Target Lock / v0.42.0, Dominant Cube Color Signature Attacks / v0.43.0).
> - [docs/archive/FINDINGS_s58-s60.md](docs/archive/FINDINGS_s58-s60.md): Sections §58 and §60 (Phases 63 and 65, v0.44.0 research tracks / capstones and F6 overhaul; §59 was never assigned).
> - [docs/archive/FINDINGS_s61.md](docs/archive/FINDINGS_s61.md): Section §61 (Phase 66, v0.45.0 baseline).

---

> [!NOTE] Active Sections (§62–§68)
> Section numbering continues here unchanged. **Agents: do not read the archives unless a task cites a specific §N ≤ 61.**

---

## 62. Vulnerability Track Redesign: Post-Telemetry Balance Assessment (`v0.46.0` Defaults): APPROVED (residuals open)

**Experiments:**
- `scripts/run_v046_sweep.py` (Steps 1, 2 and 5: 1,200 games per pod, 2P / 3P / 4P, seeds `42..1241`, `mixed1` roster);
- `scripts/run_v046_dominance_matrix.py` (Step 3: 600 per cell, key cells 2,400);
- `scripts/run_reference_bot_validation.py --config v046_roster --cells ref1` (Step 4: 3P, 1,200).

Reports:
- `docs/reports/v046_steps1-3_sweeps.md`;
- `docs/reports/v046_balance_assessment.md` §0–§8;
- `docs/plans/vulnerability_track_gd_plan.md`;
- `docs/specs/vulnerability_track_spec.md`.

### Key Changes (`v0.46.0` vs `v0.45.0`)
1. **Vulnerability Track replaces shields.**
   - No shields, slots or Defense Grid. Red and Blue cubes are unblockable.
   - Each Green cube hits the player(s) highest on the Vulnerability Track, at 4+. It costs `1 / 2 / 3` Secrets at `4–6 / 7–9 / 10+`, then resets them to `0`. Vulnerability `0–3` is a true safe zone.
   - Face 5 (Secret) and one core face per colored die carry ⚠; Gray dice carry three.
2. **Pen Test Track** (replaces the Defense Grid Track):
   - spend `2 🔬` per `−1` Vulnerability (`[TUNE]`, tuned up from `1`);
   - L1 gives a Gray die;
   - L3 gives +1 Secret and Blue Secret faces yield +3;
   - L4 gives a free −1 per turn.
3. **Faces** (`V046_VULN_NOPREMIUM`):
   - the colored ⚠ faces are the v0.45 faces plus ⚠, with no +1 🔬 premium;
   - Gray F1 is `+$1 & +1 🔬` ⚠.
4. **Setup and cards:**
   - 5 starting Secrets;
   - Market Share starts at 14 / 18 / 18;
   - Blue is ×1 in `v3.0`;
   - *Data Scraper* gives `+1` Corporate Secret instead of `+$1`.
5. **Bots (sim-only):**
   - λ's future cost is one Pen Test step (`$1.75`), no longer capped by this round's risk;
   - Adaptive also cleans to below the target when it has spare research;
   - `p_exit` stays 0.60 and `secret_value` 3.0 (raising them played worse head-to-head).

### Telemetry & Balance Verdict (`PASS` with residuals)
- **Pacing and endings (2P / 3P / 4P):**
  - Mean rounds `8.20 / 7.77 / 7.51` (v0.45 `7.42 / 6.99 / 6.73`).
  - `v1.0` breach `10.1 / 15.9 / 16.5%` (v0.45 `12.0 / 18.8 / 22.0%`).
  - Patient Zero `36–62%` (v0.45 `49–79%`); Total Wipeout ≤ `5%`.
- **Green threat:** `2.42 / 2.08 / 1.86` Secrets lost per player-game (band `1.2–2.5`). The no-target rate rises with careful play (2P late game about `70%`).
- **Economy:** income (b) is `×1.12 / 1.08 / 1.08` against v0.45 (guardrail ≤ `×1.25`). 2+ L4 tracks: `0%` for the field.
- **Dominance:**
  - KeepAll `−4.3` to `−6.0`, RerollAllVuln `−7.2` to `−9.8`, PenTestRush `−4.5` to `+1.2` pp against an Adaptive field;
  - Adaptive `−2.5` to `+1.5` pp, keep rate `39–40%`.
  - The pre-tuning build had PenTestRush at `+5 / +10` pp (3P / 4P), fixed by the Pen Test cost of 2.
- **Reference bot (ref1):** `44.9%` (fair `33.3%`). That is the lowest on record (v0.36–v0.38: `66.6–78.6%`). Its stance mix is Adaptive `45%` / RerollAllVuln `26%` / KeepAll `24%` / PenTestRush `5.5%`, so there is no degenerate line. Watch: ref1 reaches 2+ L4 in `28%` of seats.
- **Key findings:**
  1. Early breaches were a **`v1.0` card asymmetry**, not a track issue. *Data Scraper*'s second Blue cube recycles every round once Blue is unblockable (breach `33–47%` vs *Script Kiddie* `8–11%`, before the +1 Secret fix).
  2. The rise in Singularity comes from games **surviving longer in `v3.0`** (Blue ×1, +1 starting Secret), not a faster fill. The v3.0 "track advance" table was an artefact of counting entry rounds.
  3. The original λ priced ⚠ at about `0` for any seat not near the top, so Adaptive kept more ⚠ than KeepAll did.
  4. A per-round Green telemetry bug filled V046 round fields only on each game's final round. Fixed.
  5. In v0.46 `1 🔬 ≈ $1` for decision purposes; the v0.45 probe rate (`🔬 ≈ 1.7 × $`) does not carry over.
- **Residuals:**
  - 4P Market Collapse `22.8%` (v0.45 `16.5 ±5`): accept, and restate the guardrail as Patient Zero + Collapse.
  - 4P company spread `15.7` pp (v0.45 about `16`; Blue companies lead, Aegis about `34%` at 4P, so the §12.6 watch item has triggered): company-power pass in v0.47.
  - Singularity `16–27%`: accept as the third ending.
  - *Data Scraper* games still run about `1.2` rounds shorter, with `3×` the breach of *Script Kiddie*: card pass later.
  - Gray and colored core ⚠ faces are rerolled most of the time: accepted by the User, and the per-face keep band is report-only.
- **Open User decisions:** `D1–D7` in `docs/reports/v046_balance_assessment.md` §8.4.

## 63. Red Signature "Lowest Rival" (`v0.47.0` candidate): Post-Telemetry Balance Assessment: APPROVED

**Experiments:**
- Pre-SDLC probe: 12,000 games per pod (base / A at 2P–4P; C / D1 at 2P), 4,000 for B / D2. Report: `docs/findings/red_signature_lowest_rival_analysis.md`.
- Confirm sweep: `scripts/run_v047_red_signature_sweep.py` + `scripts/summarize_v047_red_signature.py`, 4,000 games per arm, seeds `42..4041`, `mixed1` roster, `v046_roster` vs `v047_roster` (2P also D1). Report: `sim_results/v047_red_signature/validation_report.md`.
- Spec: `docs/specs/red_signature_lowest_rival_spec.md`.

### Rule change (`v0.47.0` vs `v0.46.0`)
- Red Target Lock Signature Attack: the locker takes `-2` Market Share (not below `0`); the **surviving rival with the least Market Share gains `+2`, locked or not**. In 2P, **SETEC Corp counts** as a rival.
- Multi-lock rounds: all drains first, then each recipient is read from the post-drain positions.
- The "every survivor is locked" fizzle is gone. It fizzles only if the locker has no surviving rival (never in 2P).
- Card wording: "-2 Market Share; lowest rival gains +2 (2P: SETEC Corp counts)".

### User decisions (2026-11-19)
1. Arm **A** at all player counts.
2. 2P SETEC Corp gains `+2`; **D1** (`+1` to SETEC) kept in reserve.
3. Recipient read post-drain.
4. Wording as above; version `v0.47.0`.
5. 4P archetype spread is a watch item; a rise over `+4` blocks the release.

### Headline sweep (4,000 games per arm, v046 → v047)
| Pod | Rounds | Market Collapse % | Singularity % | Patient Zero % | Arch. spread | Company spread |
|---|---|---|---|---|---|---|
| 2P | 8.09 → 8.15 | 36.8 → 33.6 | 25.1 → 26.9 | 33.3 → 34.5 | 13.0 → 16.6 (D1 15.9) | 17.8 → 19.1 |
| 3P | 7.84 → 8.11 | 23.4 → 14.8 | 20.7 → 27.0 | 54.5 → 56.6 | 14.4 → 17.0 | 17.1 → 16.0 |
| 4P | 7.50 → 7.84 | 24.0 → 13.4 | 15.7 → 23.3 | 60.1 → 63.0 | 11.0 → 13.3 | 14.6 → 16.0 |

- 2P fizzles: `52.1% → 0%` of Red Signature events. Total Wipeout unchanged (`4.8 / 1.4 / 0.3%`).
- 2P SETEC Corp (v046 → A → D1): final Market Share `6.74 → 8.48 → 7.70`; MLB 1st places `0.37 → 0.81 → 0.67` per game; Secrets absorbed `1.65 → 2.81 → 2.44` per game. These match the analysis to within `0.07`. The 2P winner's Secrets fall `12.52 → 11.53`.
- Every spec §9.2 / §9.3 criterion PASSES.

### Takeaways
1. **The §62 4P Market Collapse residual is cleared** (`24.0 → 13.4%`, 3P `23.4 → 14.8%`). The cost is `+0.3` rounds and Singularity at `23–27%`, as modelled.
2. **3P spread `+2.6` (analysis `+1.5`).** This is noise, not drift. The confirm's own v046 arm already reads `14.4` (the 12k base read `12.9`). Spread moves under about `2` pts are noise at 4k games. The driver is Reckless `-1.9` (difference CI about `±3.2`). Pooled over 16k games the 3P move is about `+1.8`, with Reckless about `-1.1`.
3. **The direction is consistent across pods.** SecOpsTurtle gains a little and Reckless loses a little (4P `+0.6 / -1.8`; 2P SecOps `+5.0`, pooled with the 12k probe about `+3.7`). This is the expected cost of giving the lowest rival a catch-up gift.
4. **4P watch item not triggered:** `+2.4` (pooled about `+2.6`) against the `+4` block.
5. **The 2P SETEC acceleration works as intended.** It doubles SETEC's MLB 1st places. D1 stays the reserve lever (about `-0.7` spread for about half the SETEC effect).

**Verdict: APPROVED** as the `v0.47.0` Red Signature rule. **Watch items:**
- 2P SecOpsTurtle at about `60%` (fair `50%`);
- 4P spread against the `+4` block;
- recheck both in the next sweep that touches 2P SETEC Corp or the company-power pass.
## 64. Phase 69 Post-Telemetry Balance Assessment: Sprint Plan & Gray Legacy Rotation (`v0.48.0` Candidate): APPROVED (`v0.48.0 Baseline`)

> **Version note (2026-11-19):** this package was built and swept as `v0.47.0` on top of `v0.46.0`, in parallel with the Red Signature change (§63) that shipped as `v0.47.0`. It is renumbered `v0.48.0` / Phase 69 and rebased onto `v0.47.0`; the numbers below are against `v0.46.0`. See the combined-rules re-sweep note at the end of this section.

**Experiments:**
- `scripts/run_v047_sweep.py`: arms S0–S3 and R0–R3, 1,200 games per pod, 2P / 3P / 4P, seeds `42..1241`, `mixed1` roster.
- A re-run with fixed tooling (method-b income for every arm, win rates by bot / company / White Hat).
- A game-designer lever probe: 600 games per pod, seeds `42..641`.

Reports:
- `docs/reports/v047_sweep_report.md`;
- `docs/reports/v047_balance_assessment.md`;
- `docs/reports/sprint_plan_analysis.md` §9;
- `docs/specs/sprint_plan_spec.md` §17.

### Key Changes (`v0.47.0` vs `v0.46.0`)
1. **Sprint Plan with Gray Legacy Rotation.**
   - Setup: Ready for Release holds 2 Gray dice, the Purple die and the company die. The Current Sprint holds 3 Gray dice.
   - Gray dice have one ⚠, on F3, and that face is locked.
2. **Thinning at Level 3.**
   - Release L3 and Pen Test L3 read "return 1 Gray Legacy die you own to the box".
   - Pen Test L3 keeps the Blue Secret +3.
3. **QC Level 1 rewards:**
   - Pen Test L1 gives +1 Corporate Secret.
   - Triage L1 gives `+$2`.
   - Release L1 gives +1 Release Bandwidth this round.
4. **6 starting Corporate Secrets.**
5. **Bots (sim-only):**
   - `THINNING_AWARE` research focus;
   - `bot_thin_tracks=("RELEASE",)`.

### Telemetry & Balance Verdict (`PASS` on the like-for-like base)
- **Against the spec base (S0 and v0.45, both LEGACY bots), S2 fails two guardrails:**
  - Δ rounds +0.06 / +0.35 / +0.30;
  - income ×v0.45 1.30 / 1.26 / 1.26.
- **About 70% of the overshoot comes from the bots:**
  - The bot fix alone on v0.46 rules (S3 − S0) adds +0.13 / +0.13 / +0.12 income.
  - The v0.47 rules under the fixed bots (S2 − S3) add only +0.05 / +0.05 / +0.06.
  - The fixed bots also lift v0.45 by ×1.10.
- **Like-for-like, with both sides on `THINNING_AWARE`:**
  - Δ rounds vs S3: +0.05 / +0.24 / +0.05.
  - Income ×v0.45: 1.19 / 1.15 / 1.16.
  - Singularity: 82–86% of S3.
  - Green: 2.26 / 2.04 / 1.84. With the fixed bots, v0.46 itself breaks the 2P band at 2.75.
- **S2 is preferred over S2b**, which also thins on Pen Test L3:
  - White Hat spread 4.8 / 7.2 / 8.0 against 8.2 / 10.7 / 10.6 pp;
  - company spread 19.6 / 17.4 / 15.8 against 26.4 / 19.0 / 18.9 pp;
  - S2b's lower income is the only thing it does better.
- **Lever probes, 600 per pod. None is useful:**
  - **Triage L1 `+$1`:** no change. Breakthrough cash is outside the Phase 3 income metric.
  - **Gray F3 `+$1 / +2 🔬`:** bit-identical to S2. The bots always take 🔬 on choice faces (`adjust_declared_choices`), so this lever cannot be tested in the sim.
  - **5 Secrets at 3P / 4P:** −0.72 / −0.85 rounds against S2, an overcorrection.

### Key findings
1. **Guardrails must use the same bot policy on both sides.** The ×1.25 income cap and the ±0.30 rounds bar were calibrated with the LEGACY bots, which are known to undervalue research.
2. **The income guardrail measures Phase 3 dice income only.** Breakthrough rewards (Triage L1 `+$2`, PR L1 `+$3`) are invisible to it.
3. **The extra v0.47 income is early research:**
   - 🔬 in R1–4 is 3.83 per seat-round, against 2.98;
   - cash is 2.78, against 2.86.
   - This is the intended 5-Gray start.

### Residuals (none blocking)
- **Rush edge:**
  - v0.47: +0.3 / **+5.0** / +3.6 pp (bar +4).
  - v0.46 with the fixed bots: −3.5 / +3.5 / +2.3 (600 games). The SE is about 2 pp, so v0.47 is within noise of it.
  - v0.46 with the LEGACY bots: +12.4 pp at 3P.
  - If every seat rushes (R3), games run +0.60 / +0.46 rounds at 3P / 4P. Watch this in playtest.
- **Spook at 3P:** 38.0, against 38.8 in v0.46. Pre-existing.
- **Helix** is the lowest company in every arm, and the company spread is unchanged. Both go to the planned company-power pass.
- **Round 2 dip:** 0.43 Secret faces per roll at 3P, against 0.51. Dead turns are 0.3%, against 2.3%. The Round 1 company-die priority lever stays parked.

### User decisions (2026-11-19)
- **D-69-1 ACCEPTED:** the Δ-rounds and income guardrails are re-based on the fixed-bot baseline (S3 and V45TA); other bars stay absolute.
- **D-69-2 ACCEPTED:** ship S2 (Release-only thinning focus) as `v048_roster`.
- **D-69-3 ACCEPTED:** no `[TUNE]` change.
- **Next:**
  - the dominance matrix and ref1 on S2;
  - a matched-bot V45TA reference arm in the sweep script;
  - a bot cash/🔬 choice-face policy, needed before any Gray face-mix lever can be tested.

### Combined-rules re-sweep (`v0.48.0` on top of `v0.47.0` Red Signature, 2026-11-19)
`scripts/run_v048_sweep.py`, 1,200 games per pod, seeds `42..1241`, `mixed1`; S0 = `v047_roster`, S3 = `v047_roster` + fixed bots, S2 = `v048_roster` (`--assert-invariants`, no failures). Raw output is not committed.

| Measure (2P / 3P / 4P) | S3 (fixed-bot v0.47) | S2 (v0.48) | Bar |
|---|---|---|---|
| Rounds | 8.28 / 8.11 / 8.09 | 8.31 / 8.37 / 8.12 (Δ +0.03 / +0.26 / +0.03) | Δ within ±0.30 vs S3: PASS |
| Income ×v0.45 (old-bot ref) | 1.25 / 1.21 / 1.19 | 1.30 / 1.26 / 1.26 (Δ +0.05 / +0.05 / +0.07) | re-based (÷1.10 fixed-bot v0.45) ≈ 1.18 / 1.15 / 1.15: PASS |
| Singularity % | 30.3 / 31.0 / 28.2 | 25.3 / 27.3 / 22.7 (83 / 88 / 80% of S3) | PASS |
| Market Collapse % | 32.6 / 12.9 / 13.0 | 36.4 / 16.4 / 16.3 | watch (Red Signature's §63 gain partly given back, still well under v0.46's 21–24% at 3P/4P) |
| Green lost / seat | 2.79 / 2.47 / 2.32 | 2.29 / 2.11 / 1.92 | 1.2–2.5: PASS |
| Gray roll share % | — | 56.1 / 54.7 / 54.6 | ≥ 45: PASS |
| Longest Gray streak | — | 5 / 8 / 6 | ≤ 8: PASS |
| Seat-0 rush edge (R1 / R3 vs S2) | — | +1.7 / +5.6 / +4.1 pp; R3 −0.4 / +3.1 / +4.0 | 3P R1 over the +4 bar, as in the v0.46-based sweep (+5.0); residual |

**Verdict:** the `v0.46`-based assessment above carries over to the combined rules unchanged. The Sprint Plan adds the same +0.05–0.07 income on top of `v0.47` as it did on `v0.46`; no interaction with the Red Signature rule beyond a +3 pp Market Collapse give-back at 3P/4P. APPROVED as `v0.48.0`. Watch items: 3P rush edge, 3P/4P Market Collapse, 2P SecOpsTurtle (§63).

---

## 65. Phase 70 Post-Telemetry Balance Assessment: Locked ⚠ Faces, "Lock All Dice" (`v0.49.0 Baseline`): APPROVED (residuals open)

**Experiments** (seeds `42..1241`, 1,200 games per pod, `mixed1` roster, `--assert-invariants` clean):
- `scripts/run_locked_vuln_sweep.py --config v049_roster --base v048_roster` (main, arms and final H1B confirmation);
- `scripts/run_v046_dominance_matrix.py --config v049_roster` (600 per cell);
- `scripts/run_reference_bot_validation.py --config v049_roster --cells ref1` (3P, 1,200).

**Reports:**
- `docs/plans/locked_vuln_faces_gd_plan.md` (pre-SDLC; User decisions §8 and §11);
- `docs/specs/locked_vuln_faces_spec.md`;
- `docs/reports/v049_lock_all_dice_sweeps.md` (with the final H1B confirmation);
- `docs/reports/v049_balance_assessment.md`;
- the stale v0.46-base run: `docs/reports/locked_vuln_faces_sweeps.md`.

### Key Changes (`v0.49.0` vs `v0.48.0`)
1. **All ⚠ faces lock.** During Phase 1 rerolls, any die showing a ⚠ face is a **Locked Die** and can't be rerolled: colored core ⚠, R&D faces, and Gray Face 3.
   - It still produces its output.
   - *Arbitrary Code Execution*, *Brute-Force Bypass* and Release L4 can change its face; ⚠ is counted on the final face.
   - Locks end at **Deploy** (Phase 1 Step 4, formerly "Lock-in").
2. **Premium colored ⚠ faces** (`V046_VULN`): Red F1 `+1 MS & +1 🔬`, Blue F3 `+$2 & +1 🔬`, Green F1 `+3 🔬`, Yellow F5 `+$2 & +1 🔬`, Purple F4 `+$1 & +2 🔬`.
3. **Safe zone `0–4`**: bands `5–7 / 8–10 / 11+` = `−1 / −2 / −3` Secrets.
4. **Helix *Brute-Force Bypass* (H1B), once per game:**
   - reroll locked dice for the rest of the phase, then set 1 die to any non-★ face;
   - Root Override Hijack can't mark an unused Bypass Used.
5. **Terms:**
   - Institutional Override status *Locked* → **Pending**;
   - Target Lock text says **Target-Locked player**;
   - *Lock-in* is deprecated.

### Telemetry & Balance Verdict (`PASS` with residuals), v0.48 → v0.49 (2P / 3P / 4P)
- **Pacing:**
  - Rounds are `8.42 / 8.34 / 8.12`.
  - Market Collapse drops from `36.4 / 16.4 / 16.3` to `26.6 / 11.0 / 10.2`.
  - Patient Zero + Collapse goes from `67.8 / 70.8 / 76.8` to `67.2 / 70.5 / 76.8`, a PASS under the re-based bar.
- **Green threat:** `2.29 / 2.11 / 1.92` → `1.83 / 1.63 / 1.46` Secrets lost per player-game.
- **Locks:** about `1.8` per player-round; locking Gray adds about `0.4`. P(★) per colored die is `0.164`.
- **Helix:** win `45.2 / 28.2 / 19.2`, which is `−1.4 / +2.8 / +1.7` pp vs v0.48. Lost to Black: `0%`.
- **Income:** about `×1.17–1.18` vs v0.48. Premium faces account for about 11% and the lock for about 6%; accepted.
- **Dominance:** no dominant stance. PenTestRush is neutral; KeepAll and Kamikaze are about `−14` pp.
- **Reference bot (ref1, 3P):** `60.6%` (v0.48 `53.0%`, 600 games). More than half of the growth comes from v0.48's double-capstone line; it doesn't block.
- **Key findings:**
  1. On the v0.46 base the lock *raised* Green loss (it needed the 0–4 safe zone). On v0.48, where Gray has one ⚠ face, the same package *lowers* it.
  2. Once per game, the lock bypass alone can't keep Helix at parity; it reaches `−4.8` pp at 2P even with per-Version use. The face-set plus Black immunity (H1B) is the smallest fix that does.
  3. The 2P "no-target" fail is a bot artefact: the rule-equivalent Gray-off control reads `66.0`.
  4. A sweep-script bug printed PASS for every extra guardrail row. It's fixed; earlier Helix, Prodigy and Operator "PASS" rows in that script were unreliable.
- **Re-based guardrails** (User, 2026-11-19):
  - Patient Zero + Collapse ≤ v0.48 + 3 pp;
  - Collapse ≥ 8% at 3P/4P;
  - income ≤ v0.48 × 1.20.
- **Residuals:**
  - late no-target at 2P (`74.3`) and 3P (`64.0`), already failing in v0.48;
  - 4P company spread `18.4` pp (Spook `30.9`, Helix `19.2`) and per-colour parity, both failing since v0.48 and confounded with company strength;
  - Operator `+3.2 / +3.3` pp (CIs include 0).
- **Next:**
  - a company-power pass;
  - a double-capstone stance in the dominance matrix;
  - a v0.48 ref1 run at 1,200 games;
  - print the Helix face-set and Black-blocked counters in the sweep summary;
  - web sync to v0.49.


## 66. Phase 71 Post-Telemetry Balance Assessment: Gray ⚠ B23 + Pen Test L2 Gray Thinning (`v0.50.0` Candidate): APPROVED (residuals open)

**Experiments** (`mixed1` roster, `--assert-invariants` clean):
- `scripts/run_gray_vuln_sweep.py` at HEAD `547135c`, pooled seeds `42..2441` (2,400 games per pod). Arms: M = `v050_roster`, B0 = `v049_roster`, B0-GA, B48, A-stock, A-noL2.
- `scripts/probe_v050_motivation.py` (game designer, same seeds). It makes paired seat-0 policy swaps and gives seat 0 a −1 Gray handicap, on v0.50 and on v0.49 + the GRAY_AWARE bot.

**Reports:**
- `docs/plans/gray_vulnerability_gd_plan.md` (pre-SDLC, §9 follow-up);
- `docs/specs/gray_vuln_b23_spec.md`;
- `docs/reports/v050_gray_vuln_sweeps.md`.

### Key Changes (`v0.50.0` vs `v0.49.0`)
1. **Gray Legacy ⚠ on Face 2 (`+2 🔬`) and Face 3 (`+$2 / +2 🔬`)** (B23). It was on Face 3 only.
   - Per face, Gray now carries the Market-die ⚠ rate (1/3).
   - Per unit of output it is the heaviest liability in the pool: 0.22 ⚠ per resource, against 0.13–0.17 for Market dice.
2. **The Pen Test Level 2 Breakthrough** returns `1` Gray Legacy die you own to the box (a1). The Pen Test L3 thin is unchanged.
3. **Sim only:** the roster research focus becomes `GRAY_AWARE`. It weighs Gray ⚠ exposure and how close the seat is to Vulnerability 5 when it picks thinning tracks.
4. **Terms:** no new terms.

### Telemetry & Balance Verdict (`PASS` with residuals), v0.49 (B0) → v0.50 (M), 2P / 3P / 4P
- **Guardrails** (all PASS):
  - Patient Zero + Collapse is `66.8 / 70.7 / 73.8` (`+0.0 / −1.0 / −3.1` pp).
  - Collapse is `29.4 / 11.5 / 12.1`%.
  - Green lost is `2.20 / 1.97 / 1.82`.
  - Income is ×`1.10` vs v0.48, about 7% below v0.49.
  - Dead turns are `0.26–0.29`%.
  - Invariants are clean.
  - The 4P −3.1 is mostly the bot: B0-GA is already `73.6`, and M vs B0-GA is `+0.1`.
- **Pacing:** rounds are `8.45 / 8.38 / 8.32` (B0 `8.41 / 8.34 / 8.20`) and Singularity is `25.9 / 27.6 / 25.7`.
  - With the stock bots and no L2 (A-noL2), the PZ + MC rise comes back (`+0.8 / +0.5 / −0.7`). With stock bots, A-stock games run `−0.1 / −0.2 / −0.2` rounds shorter.
- **Mitigation adoption:**
  - Gray removed per seat is `2.77` (B0 `1.72`). The removals come from Release L3 `1.00`, Pen Test L2 `0.94`, Triage L4 `0.48`, Burn Notice `0.18` and Pen Test L3 `0.16`.
  - A seat first holds ≤ 3 Gray in round `3.33` (B0 `4.17`), and only 4–5% never get there.
  - Gray held per seat at R8 is about `2.05` (B0 about `3.2`).
- **Motivation (paired seat-0 swaps, win pp / Secrets):**

| Test | v0.50 | v0.49 + GRAY_AWARE |
|:---|:---|:---|
| Cost of not mitigating (field GA, seat 0 stock) | `−1.9 / −3.1 / −0.8` pp, `−0.36 / −0.49 / −0.35` Secrets | `−3.1 / −4.5 / −2.4` pp |
| Value of 1 fewer Gray at setup | `+4.5 / +2.4 / +4.0` pp, `+0.85 / +0.45 / +0.76` Secrets | `+5.3 / +3.8 / +4.5` pp |
| GA seat in a stock field | `+1.8 / +3.0 / −0.1` pp | — |

  The SE of a paired difference is about 1–1.2 pp.
- **Key findings:**
  1. **The early-vs-late thinner gap (about ±3 pp) is a cohort artefact, not missing motivation.**
     - Under GA, 95% of seats reach ≤ 3 Gray by R4. The "late" group (n `262–490`) is the starved or behind tail.
     - The probe's `+5 / +7.5 / +7` came from a1 with **stock** bots, where about half the seats thinned late.
     - The probe's own GA + a1 arm also read `−3 / −3 / +4`, which matches the PO.
     - When everyone mitigates early, that comparison stops measuring the payoff. Paired swaps do measure it.
  2. **Mitigation is rewarded, not dominant.**
     - One Gray die is worth about `+2.5` to `+4.5` pp and about `0.5–0.9` Secrets.
     - Skipping the mitigation focus costs `1–3` pp.
     - There is no forced line, which suits a Euro.
  3. **v0.50 raises how much mitigation happens and how early, not the value of each step.**
     - Per-die and per-policy values are flat to slightly lower than on v0.49 + the same bot.
     - The reason is that Pen Test L2 hands even the stock bots a cheap thin (they remove `2.17` vs `1.72`), so the field converges.
     - Players should *feel* Gray as a liability: they see 2 ⚠ faces, and roughly 1 ⚠ arrives from the 3 forced Gray rolls in R2. The EV case for mitigating already held in v0.49.
  4. **Bandwidth levers were rejected in the probe.** Release Bandwidth +1 breaks the 2P Green cap (`2.62–2.72`) and the income cap.
- **Residuals:**
  - Helix is below par: `42.6 / 26.5 / 20.2` (B0 4P `19.1`).
  - Spook is above par: `56.1 / 41.6 / 31.0` (B0 4P `32.9`).
  - The 2P company spread is `21.6` pp.
  - All three pre-date v0.50.
  - The `GRAY_AWARE` parameters are first guesses.
- **`[TUNE]` recommendations:** none required. Don't raise the per-⚠ cost (band damage) just to make mitigation bite harder: it would push 2P Green toward the cap.
- **Next:**
  - a dominance matrix with a no-thinning stance and `GRAY_AWARE`, plus a ref1 run on v0.50;
  - the company-power pass (Helix / Spook);
  - doc, PnP, TTS and web sync to v0.50.0;
  - FINDINGS now has 9 recent sections, so archive §57.

## 67. Phase 72 Post-Telemetry Balance Assessment: Green Hit Landing + One Hit per Round (S2H1, `v0.51.0` Candidate): APPROVED WITH RESIDUALS

**Experiments** (`mixed1` roster, `--assert-invariants` clean):
- `scripts/run_green_landing_sweep.py --players 2,3,4`, pooled seeds `42..2441` (2,400 games per pod). Arms: M = `v051_roster`, B0 = `v050_roster`, B48 = `v048_roster` (the income comparator).
- `scripts/probe_green_drop_band.py` (pre-SDLC monkeypatch probe, seeds `42..2041`, 2,000 games per pod).

**Reports:**
- `docs/plans/green_landing_gd_plan.md` (pre-SDLC, §0–§9);
- `docs/specs/green_landing_spec.md`;
- `docs/reports/v051_green_landing_sweeps.md`.

### Key Changes (`v0.51.0` vs `v0.50.0`)
1. **A Green hit moves the player down to the bottom of the next lower band.** `5–7` lands at `2` (not `0`), `8–10` at `5` and `11+` at `8`. The Secret cost by band (`1 / 2 / 3`) is unchanged.
2. **At most one Green hit per player per Phase 4.**
   - Each later cube hits the highest player(s) at `5`+ who have not been hit this phase. Ties still hit all tied players.
   - If no valid target remains, the cube has no effect and recycles, as in the existing rule.
   - An Aegis Baffle Echo cancel still uses up that player's one hit, and their Vulnerability still drops.
3. **Config:**
   - `vuln_hit_landing_by_band = (2, 5, 8)` and `vuln_one_hit_per_round = True` `[TUNE: v0.51.0]`.
   - The defaults (`None` / `False`) reproduce v0.50.
   - The bot `loss_if` replays the cap and the landing.
4. **Terms:** no new terms.

### Probe history (2,000 games per pod; ΔPZ + MC vs v0.50 R0, 2P / 3P / 4P)

| Arm | Rule | ΔPZ + MC | Why not / why |
|:---|:---|:---|:---|
| DB | `5–7 → 0`, `8–10 → 5`, `11+ → 8` | `+1.1 / +0.3 / +1.8` | 89% of hits are at 5–7 and stay the same as today, so the effect is small |
| S2 / S3 / S4 | `5–7` lands at `2 / 3 / 4` | S2: `+4.4 / +3.1 / +4.6` | User picked S2. Repeat hits allowed a 6-Secret round |
| S2S1, S2PT | S2 + 1 starting Secret / first Pen Test step at cost 1 | S2S1: `−5.7 / −11.0 / −31.6` (4P Singularity `56%`) | S2S1 overshoots; S2PT trims eliminations by only `0–1.4` pp |
| S2F1 | S2 + repeat hit costs a flat 1 | `+4.3 / +3.1 / +4.6` | the flat cost only bites after an 11+ hit; worst round `5`; superseded |
| SFA / SFA1 / SFA0 / SFA9 | rule-aware bot / `5–7 → 1` / 2P levers | SFA ≈ S2F1; SFA1 `+1.3 / +1.8 / +2.2` | the bot's awareness is worth 0; 2P levers undo the change or overshoot |
| S2HX | cap + 1 Secret per cube beyond the alive-player count | 2P elim `36.1%`, Total Wipeout `12.7%` | rejected (an overflow penalty) |
| **S2H1** | **S2 + one hit per player per round** | `+4.0 / +2.6 / +4.5` | **chosen**: worst round `3`, no multi-hit rounds |

### Telemetry & Balance Verdict (`PASS` with accepted residuals), v0.50 (B0) → v0.51 (M), 2P / 3P / 4P
- **Guardrails** (L1–L11 all PASS, re-based on the S2H1 probe per D1):
  - PZ + MC is `70.6 / 73.6 / 79.5` (probe `70.6 / 73.5 / 80.0`, ± 2).
  - Eliminated seats are `30.0 / 26.4 / 23.1`%.
  - Rounds are `8.21 / 8.16 / 8.11` (B0 `8.41 / 8.41 / 8.32`).
  - Green lost is `2.78 / 2.41 / 2.24`.
  - Back-to-back hits are `23.7 / 20.2 / 17.9`% (B0 `4.4 / 3.1 / 2.3`).
  - Multi-hit seat-rounds are `0`, and the worst round is `3`.
  - Collapse is `11.7 / 11.5`% at 3P / 4P.
  - 2P Total Wipeout is `8.9`%.
  - Income is ×`1.09` vs v0.48.
  - Invariants: 0 violations.
- **Exactness (INV-LAND-02):** with the one-hit cap, the Secrets lost in a single Phase 4 equal v0.50's for the same starting Vulnerabilities. A hit player is skipped, just as a reset-to-0 player could not be targeted.
  - All the extra pressure is **carry-over**: about 12–15% of hits land at 5+, and players re-enter band sooner.
  - The **reset-as-cleanse exploit is closed**: an 11+ hit now leaves the player at 8, 4 Pen Test steps from safety.
- **Pacing:**
  - Singularity is `20.5 / 24.5 / 19.5`% (`−6.3 / −3.0 / −4.5` pp). That is the matching cost of the PZ + MC rise.
  - All three end triggers stay live.
  - Rounds are `−0.20 / −0.25 / −0.21`.
- **Parity:**
  - Company spread is `18.6 / 14.3 / 10.9` pp (B0 about `24 / 14 / 17` in the probe), the best 4P spread since v0.48.
  - Helix is `44.0 / 29.4 / 20.7` (v0.50 `42.6 / 26.5 / 20.2`).
  - Aegis is `62.6 / 43.0 / 31.6`, and Spook `55.4 / 39.9 / 31.2`.
  - White Hat spread is `9.9 / 9.4 / 8.7`.
- **Corruption check** (game designer, 300-game instrumented runs):
  - The `+3` into-target counter reads `0.000` because the `+3` path is unreachable. The `+3` gain (`corruption_lowest_vuln_gain_double`) only fires on spaces with 2 printed demotes, and those exist only on the legacy Aggressive Version cards. Every space on the current cards has a single demote.
  - The counter is wired correctly. The `+2` key fires about `1.18 / 1.26 / 1.33` times per game on v0.51, against about `0.87 / 0.85 / 0.87` on v0.50.
  - That is a **+40–50% rise in Corruption pushing the lowest-Vulnerability player into Green range** (from 3–4). More seats now sit at 3–4 after a landing at 2 plus Phase 1 lock-in.
  - This is already inside the measured totals, so it is a mechanism note, not a new risk.
- **Pillars:**
  - Green still hunts the highest player at 5+.
  - Red and Blue are untouched.
  - No extra random draws.
  - Pen Test becomes more valuable (about +0.8 steps per seat).
  - The CLAUDE.md Cube Tower pillar text ("resets them to `0`") is now stale (D5).
- **Accepted residuals (User, 2026-11-20):**
  - **D1:** PZ + MC `+4.1 / +2.8 / +4.1` pp vs v0.50, waiving the +3 bar. This is intended pressure from the carry-over.
  - **D2:** 2P Green lost `2.78` vs the `2.5` cap. With the worst round unchanged at 3, it measures sustained pressure, not spikes. Re-state the 2P cap as `≤ 2.8` going forward.
  - Carried forward:
    - Helix is below par at every count;
    - Spook and Aegis are above par;
    - rules text still says "`+3` on Aggressive spaces" (RULES.md §Phase 2), which no current card can trigger.
- **`[TUNE]` recommendations:** none.
  - Don't add a 2P lever: "2P lands at 0" undoes the change, and "+1 starting Secret at 2P" overshoots (eliminations −6 pp, +0.75 rounds).
- **Next:**
  - D5: the v0.51.0 version bump and the CLAUDE.md pillar text (User);
  - doc, PnP, TTS and web sync to v0.51.0;
  - decide whether the `+3` Corruption rule text and `corruption_lowest_vuln_gain_double` should stay;
  - the company-power pass (Helix / Spook / Aegis);
  - ~~archive §58~~ (done: §58 and §60 moved to `docs/archive/FINDINGS_s58-s60.md`).

---

## 68. Phase 73 Post-Telemetry Balance Assessment: Market Share Markers Arrive On Top, Track Maximum 25, 4P Market Leader Bonus `+3 / +2` (`v0.52.0` Candidate): APPROVED WITH RESIDUALS

**Experiments** (`mixed1` roster):
- `scripts/run_ms_stack_sweep.py --players 2,3,4 --games 2400 --seed0 {42,10042}`, pooled 2 × 2,400 games per arm per pod. Arms: B = `v051_roster` + tie telemetry, M = `v052_roster` (`FIRST_SEAT_TOP`).
- Ablations (1,200 games, 3P / 4P, seed0 `42`): `LAST_SEAT_TOP`, `bot_ms_stack_aware = false`.
- Pre-SDLC probe: `scripts/probe_ms_ties.py` (monkeypatch, 3,000 games per pod; S32 / S321 rows before plan §9 are invalid).

**Reports:**
- `docs/plans/ms_tie_stagnation_probe.md` (§1–§2 diagnosis, §7 on top vs beneath, §8 decisions, §9 schedule correction);
- `docs/specs/ms_stack_order_spec.md` (Amendment A1 overrides the spec body);
- `docs/reports/v052_ms_stack_sweeps.md`.

### Key Changes (`v0.52.0` vs `v0.51.0`)
1. **On top.** A Market Share marker that moves onto an occupied space goes on top; a higher marker ranks ahead of those beneath it. Markers that reach a space at the same moment keep their previous order (Red, the clamp at `0`, *Baffle Echo*, Red Signature, Phase 3 gains). There are no Market Share ties.
2. **Setup:** all markers start on one space with the **First Player on top** (A1a). `LAST_SEAT_TOP` stays a sweep arm only.
3. **Track maximum `20 → 25`** at every player count; starts stay `14 / 18 / 18`.
4. **Market Leader Bonus:** 2P / 3P `+3 / +1` (unchanged), 4P `+3 / +2` (A1b).
5. **Targets read the stack:** Customer Poaching "most" and the Red Signature "least" pick the highest / lowest-ranked eligible marker (R2); a poaching actor lands on top of the rival (R4). A Patient Zero's marker stays frozen and takes no Market Leader Bonus place (R1).
6. **Section 5 tiebreakers trimmed** to Market Share position (R3); Money, ready dice, Research and fewest Under Development leave the ranking path.
7. **Terms:** no new terms (D2).

### Headline (pooled, v0.51 B → v0.52 M, Δ)

| Metric | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Effective MLB 1st tie % | `12.1 → 0` | `25.9 → 0` | `32.5 → 0` |
| Raw top-space tie % | `12.1 → 13.4` (+1.3) | `25.9 → 20.7` (−5.3) | `32.5 → 25.5` (−7.0) |
| Lead changes / game | `1.07 → 1.80` | `1.39 → 2.57` | `1.45 → 2.96` |
| End MS spread | `2.04 → 2.02` | `3.19 → 3.49` | `4.36 → 4.73` |
| PZ / MC / Singularity % | `42.8 / 30.1 / 19.3` (−0.4 / **+2.0** / −0.7) | `64.7 / 12.5 / 21.4` (+2.4 / +0.8 / −2.7) | `67.8 / 12.1 / 19.7` (−0.9 / −0.1 / +1.2) |
| Rounds | `8.18` (+0.03) | `8.16` (−0.05) | `8.08` (0.00) |
| MLB Secrets / game | `10.28` (−0.20) | `16.14` (−1.08) | `23.73` (**+1.98**) |
| Winner Secrets | `9.56` (+0.27) | `11.87` (+0.49) | `13.73` (**+1.23**) |
| Company win spread pp | `15.5` (−4.2) | `12.0` (−2.7) | `9.3` (−1.9) |
| Seat win spread pp | **`4.2`** (+3.1) | `1.7` (−0.7) | `3.5` (+1.3) |
| Final tiebreak decided by stack, % games | `1.5` | `1.1` | `1.6` |

All acceptance lines PASS (unique winner 100%, tied-paid MLB places 0 in every run); 2P seat spread is WATCH.

### Telemetry & Balance Verdict (`PASS` with residuals)
- **Original goal (plan §1–§2) met.**
  - *Ties for 1st:* the Market Leader Bonus can no longer be shared (effective tie `0` at every count). Raw same-space finishes at the top fall 5–7 pp at 3P / 4P, so players now pass rather than match.
  - *Movement:* the sole leader changes hands **1.7–2.0× as often** (4P `2.96` vs `1.45`, above the probe's `2.9`). The 4P end spread widens slightly (`4.73`), better than the probe's on-top arm feared (plan §7: tighter track).
  - 2P raw top ties are flat (+1.3): with 2 markers (plus SETEC Corp) there was little crowding to fix. The rule still removes the shared award.
- **Pacing neutral.** Every end trigger is within ±3 pp and rounds within ±0.05. The §8 "PZ about +4 pp" cost of on top did not appear: first seat on top plus the 4P `+3 / +2` schedule absorbed it.
- **Parity improves.** Company spread narrows at every count (2P −4.2 pp), which fits trimmed tiebreakers that no longer reward Money / dice hoarding.
- **Ruling, 2P seat edge (seat 0 `52.1%` pooled, blocks `52.5 / 51.7`): ACCEPT, WATCH.**
  - Real, not noise: the SE of a 2P seat spread at 4,800 games is about `1.4` pp, so `4.2` is about 3σ above v0.51's `1.1`.
  - Cause: the First Player starts on top, so every untouched start tie and every same-moment move favours seat 0. That is the price of A1a, which fixed the far worse `LAST_SEAT_TOP` skew (3P last seat `38.3%`, 4P `21–29%`).
  - It stays under the 5 pp line and is the size of an ordinary first-player edge. No `[TUNE]` now. If playtests feel it, the only clean lever is a 2P-only "second player on top" probe (`LAST_SEAT_TOP` at 2P); expect it to flip the edge rather than remove it, since seat 1 also acts later in Phase 5.
- **Ruling, 2P MC `+2.0` pp: ACCEPT.**
  - Marginal: the SE of the difference is about `0.9` pp (≈2σ), and PZ moves −0.4, so PZ + MC is +1.6 pp, within the ±5 band and far below §67's accepted D1.
  - No mechanism points at the stack: stack-decided Red Signatures are `0.06` / game at 2P (unchanged). Market Collapse is a non-elimination ending, so no dead-turn risk. Re-check in the web / playtest pass only.
- **Ruling, 4P MLB `+1.98` Secrets / game and winner `+1.23`: ACCEPT (intended).**
  - Plan §2: about a quarter to half of v0.51's 4P MLB came from shared ties. Removing ties with `+3 / +1` cut the faucet to about `16.4` and raised PZ about +6 pp (plan §9). `+3 / +2` refills it slightly past par (`23.7` vs `21.8`).
  - The extra ≈`0.5` Secret per player per game buys pacing parity (PZ −0.9, rounds 0). The winner's score scale rises about 10%, but the 2nd-place award narrows the 1st–2nd gap (`+3 / +2`), so it is anti-runaway, and the 4P company spread improves to `9.3`.
  - `+3 / +2 / +1` was too soft (A1b: PZ `64.3`). No further change.
- **Pillars:**
  - Red stays unblockable and simultaneous. Same-moment moves keep their order, so Red still never changes a gap; only gains reorder the stack.
  - Ranking is read off the board with no hidden lookup, and no extra random draws.
  - The Market Leader Bonus still pays on Red Secret rounds and once at game end (none on a Total Wipeout).
- **Accepted residuals / watch items:**
  1. **2P seat spread `4.2`** (WATCH, above).
  2. **3P PZ + MC `+3.2` pp** with Singularity −2.7 and MLB −1.1 / game. The 3P `+3 / +1` choice (A1b) leaves 3P the only pod that got harsher. In band; re-check if 3P playtests feel fragile (the lever is 3P `+3 / +2`, which gave PZ `59.5`, about −3 pp vs v0.51).
  3. **Bot stack awareness is load-bearing.** Without it, 3P PZ is +5.5 pp over B and the 4P company spread widens +5.3 pp. Humans read the stack naturally, so this is a sim-fidelity note, but any future bot changes must keep `bot_ms_stack_aware`.
  4. **Not emitted:** per-company win rates (spread only), White Hat spread, elimination split. The §67 carry-forwards (Helix below par, Spook / Aegis above) are not re-measured here.
  5. **Stale text:** the spec §1 scope table still lists `LAST_SEAT_TOP` and the `D4` schedule (A1 overrides it). The CLAUDE.md pillar still says "ties share the better place", "3P/4P `+1` 2nd" and the 5-step tiebreaker hierarchy (User to update).
- **`[TUNE]` recommendations:** none.
- **Next:** v0.52.0 version bump; RULES / QUICKREF / GLOSSARY wording sync (no new term); track-25 art in PnP, TTS (rebuild) and web; CLAUDE.md pillar text (User); ~~archive §61~~ (done: moved to `docs/archive/FINDINGS_s61.md`).
