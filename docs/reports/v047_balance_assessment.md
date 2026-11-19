# v0.47.0 Balance Assessment (Phase 68: Sprint Plan & Gray Legacy Rotation)

**Date:** 2026-11-19. **Author:** game-designer. **Candidate:** S2 = `v047_roster` (QC Level 1 rewards, thinning at Level 3, 6 starting Corporate Secrets, `THINNING_AWARE` bots, `bot_thin_tracks=("RELEASE",)`).

**Inputs:**
- `docs/reports/sprint_plan_analysis.md` §9, which covers arm QC and is User-approved.
- `docs/specs/sprint_plan_spec.md` §17, which sets the guardrails.
- `docs/reports/v047_sweep_report.md`, with 1,200 games per pod and seeds `42..1241`.
- The re-run summaries for S0 / S1 / S2 / S2b / S3. These use fixed tooling: method-b income for every arm, and win rates by bot, company and White Hat.
- A game-designer scratch probe. It ran 600 games per pod on seeds `42..641`, reusing `scripts/run_v047_sweep.py` `play` / `metrics`, and wrote no JSON.

## 0. Verdict: APPROVED. No `[TUNE]` change. One guardrail re-base needs User sign-off.

- S2 fails two guardrails against the spec §17 base: Δ rounds at 3P (+0.35) and 4P (+0.30), and income ×v0.45 (1.30 / 1.26 / 1.26).
- Both fails come mostly from the bot fix, not from the rules.
  - The v0.45 income reference and the S0 control both use the old LEGACY research bots. S2 uses `THINNING_AWARE`.
  - On a like-for-like base, where both sides use the fixed bots, S2 passes every guardrail:
    - Δ rounds vs S3: +0.05 / +0.24 / +0.05.
    - Income ×v0.45 (with the fixed bots on v0.45 too): 1.19 / 1.15 / 1.16.
- **None of the small levers fixes the failing metrics against the old base** (§3).
  - Triage L1 `+$1` and Gray F3 `+$1 / +2 🔬` do not touch the measured income.
  - 5 Secrets at 3P / 4P overshoots pacing by about −0.7 rounds.
  - Tuning against a mismatched bot baseline would make the game worse for the wrong reason.

## 1. Bots vs rules (Question 1)

### 1.1 Income, method b (×v0.45; 1,200 per pod; v0.45 reference = LEGACY bots)

| Arm | Rules | Bots | 2P | 3P | 4P |
|:--|:--|:--|--:|--:|--:|
| S0 | v0.46 | LEGACY | 1.12 | 1.08 | 1.08 |
| S1 | v0.47 | LEGACY | 1.22 | 1.18 | 1.17 |
| S3 | v0.46 | THINNING_AWARE | 1.25 | 1.21 | 1.20 |
| S2 | v0.47 | THINNING_AWARE | 1.30 | 1.26 | 1.26 |

How the change from S0 to S2 splits (+0.18 / +0.18 / +0.18):

| Component | 2P | 3P | 4P |
|:--|--:|--:|--:|
| Bot fix on v0.46 rules (S3 − S0) | +0.13 | +0.13 | +0.12 |
| v0.47 rules under the fixed bots (S2 − S3) | +0.05 | +0.05 | +0.06 |
| v0.47 rules under LEGACY bots (S1 − S0), for reference | +0.10 | +0.10 | +0.09 |

**About 70% of the overshoot comes from the bots.** The bot fix also lifts v0.45 by itself. In the 600-game probe, v0.45 with the fixed bots against v0.45 with LEGACY bots is ×1.10 / 1.10 / 1.09. So the ×1.25 cap is being read against a weaker opponent model.

**Like-for-like (probe, 600 per pod; both sides use `THINNING_AWARE`):**

| Ratio | 2P | 3P | 4P |
|:--|--:|--:|--:|
| S0 / V45 (LEGACY / LEGACY; check against the v0.46 record of 1.12 / 1.08 / 1.08) | 1.12 | 1.09 | 1.07 |
| S3 / V45TA | 1.14 | 1.11 | 1.10 |
| **S2 / V45TA** | **1.19** | **1.15** | **1.16** |

### 1.2 Pacing (Δ mean rounds)

| Comparison | 2P | 3P | 4P |
|:--|--:|--:|--:|
| S2 − S0 (spec base) | +0.06 | +0.35 | +0.30 |
| S3 − S0 (bot fix only) | +0.01 | +0.12 | +0.25 |
| **S2 − S3 (rules, like-for-like; 1,200)** | **+0.05** | **+0.24** | **+0.05** |
| S2 − S3 (probe, 600) | +0.01 | +0.16 | +0.14 |

Other guardrails on the like-for-like base:
- **Singularity:** S2 reaches 85 / 86 / 82% of S3's rate (bar ≥ 60%).
- **Green:** S2 loses 2.26 / 2.04 / 1.84 Secrets per seat, inside the 1.2–2.5 band. With the fixed bots, v0.46 itself breaks the band at 2P (S3 2.75). The band was set with the LEGACY bots, so S2 is the arm that brings Green back into it.

### 1.3 Recommendation

Re-base the two bot-sensitive guardrails on the fixed-bot baseline:
- Δ rounds against S3;
- income against a v0.45 reference that also uses `THINNING_AWARE` (a "V45TA" arm).

Keep the absolute bars as they are: Green band, Total Wipeout, PZ + Collapse, dead turns, stranding and spreads.

Engineering follow-up (not done here, because sim/ and scripts/ are out of scope): add a matched-bot `V45TA` arm to `scripts/run_v047_sweep.py` and use it for `--ref45` whenever the candidate uses `THINNING_AWARE`.

## 2. S2 vs S2b: which bot research default to ship (Question 2)

| Metric (2P / 3P / 4P) | S2 (thin on Release only) | S2b (thin on Release and Pen Test) |
|:--|:--|:--|
| Δ rounds vs S0 | +0.06 / +0.35 / +0.30 | +0.05 / +0.34 / +0.30 |
| Income ×v0.45 (LEGACY reference) | 1.30 / 1.26 / 1.26 | 1.26 / 1.22 / 1.21 |
| Singularity % | 25.0 / 21.8 / 15.8 | 24.7 / 21.8 / 12.9 |
| 4P Market Collapse % | 24.9 | 27.9 |
| White Hat spread pp | **4.8 / 7.2 / 8.0** | 8.2 / 10.7 / 10.6 |
| Bot spread pp | **14.0 / 15.3 / 9.9** | 18.5 / 19.0 / 10.0 |
| Company spread pp | **19.6 / 17.4 / 15.8** | 26.4 / 19.0 / 18.9 |
| Owned Gray dice at R8 (3P) | 3.3 | 2.7 |

**Recommendation: ship S2 as `v047_roster`.**
- Balance is judged by win-rate parity, and S2 is tighter on all three spreads.
- S2 keeps more of the intended Gray "good suck".
- S2b's lower income is the only thing it does better. That comes from fewer dice rolling once Gray is thinned twice, and it disappears on the like-for-like base.
- Keep S2b as a sensitivity arm for players who thin on both tracks. R3, where every seat rushes, already covers the extreme case.

## 3. Lever probes (Question 3; 600 per pod, paired against S2)

| Arm | Change | Δ rounds vs S2 | Liquid income | Other effects |
|:--|:--|:--|:--|:--|
| T1 | Triage L1 `+$2` → `+$1` | +0.04 / +0.04 / +0.07 | +0.02 / +0.04 / 0.00 | Rush edge +4.1 / +3.5 / +1.8 pp (within noise of S2) |
| T2 | 5 starting Secrets at 3P / 4P | — / **−0.72 / −0.85** | −0.03 / −0.05 | 3P / 4P vs S0: −0.35 / −0.45 rounds; PZ 63.8 / 67.2%; Green 1.78 / 1.60; Singularity 17.5 / 11.0% |
| T3 | Gray F3 `+$2 / +2 🔬` → `+$1 / +2 🔬` | **0.00** (bit-identical) | 0.00 | No effect at all |

Findings:
1. **Breakthrough rewards fall outside the income guardrail.** The guardrail counts only Phase 3 die income plus blocks. Triage L1 `+$2` and PR L1 `+$3` are Breakthrough rewards, so T1 cannot move it.
2. **The bots never take cash on a Gray choice face.**
   - `research_policy.adjust_declared_choices` (v0.35) always takes 🔬 on choice faces without a shield option.
   - So T3, the lever named in §9.7 of the design report, cannot be tested in the sim. A 40-game paired check came out identical, and so did the 600-game pods.
   - It would only bite on human players who take the cash.
   - The bots' cash/🔬 policy on choice faces is a separate engineering item.
3. **T2 swings pacing too far the other way.** The analysis in §9.2 already found this. A whole Secret is the smallest step available, and it costs about −0.7 rounds.
4. **Where the extra income comes from:**
   - Phase 3 research rises in R1–4 (3.83 against 2.98 🔬 per seat-round, +29%).
   - Phase 3 cash dips slightly (2.78 against 2.86). Triage L1 `+$2` more than repays that, but the metric doesn't count it.
   - This early-research surge is the intended "5 Gray" start. In v0.46 decisions, `1 🔬 ≈ $1`.

**Fallback if the User declines the re-base:**
- The lever that would actually move the metric is a cut to Gray research faces, such as F2 `+2 🔬` → `+1 🔬`.
- That weakens the "good suck" and works against the design intent.
- I don't recommend it, and it is untested.

## 4. Residuals (Question 4): none is blocking

### 4.1 Rush edge

Seat-0 win, rushing minus normal play, in pp (2P / 3P / 4P):

| Rules / bots | Rush edge |
|:--|:--|
| v0.46 / LEGACY (S0R − S0, 600) | +1.0 / **+12.4** / +6.3 |
| v0.46 / fixed bots (S3R − S3, 600) | −3.5 / +3.5 / +2.3 |
| v0.47 S2 (R1 − S2, 1,200) | +0.3 / **+5.0** / +3.6 |
| v0.47 S2 (R1 − S2, 600) | −1.1 / +5.2 / +6.0 |

- v0.47 S2 sits about +1.5 pp above v0.46 with the fixed bots.
- The SE of a paired difference is about 1.5–2 pp at 1,200 games and about 2–2.5 pp at 600.
- At 4P the 1,200 and 600 results differ by 2.4 pp, so the estimate is noisy.
- **Residual / watch item**, with two points in its favour:
  - It is down from +12.4 pp under the shipped v0.46 bots.
  - Rushing still pays for its gains with Breakthroughs rather than by locking anyone out.
- R3, where every seat rushes, runs +0.60 / +0.46 rounds at 3P / 4P. That is the pacing tail if human tables all rush. Re-check it in playtest.

### 4.2 Spook and Helix

- **Spook, 3P:** S0 38.8 / S2 38.0 / S3 36.4 (fair share 33.3). This was already there in v0.46, and v0.47 does not widen it.
- **Spook, 2P:** S2 52.7 against S0 50.2. The probe's +6 pp warning appeared only under the LEGACY bots (S1 56.0).
- **Helix** has the lowest company win rate in every arm, including S3. In S2 it wins 44.8 / 26.6 / 17.7%; in S0 it wins 40.5 / 28.2 / 19.4%.
- **Company spread:** S2 19.6 / 17.4 / 15.8 pp against S0 19.2 / 17.8 / 15.7. It is unchanged; the Aegis-led spread is the existing v0.46 residual.
- Both belong to the planned company-power pass, not to this phase.

### 4.3 Round 2 dip

Secret faces per roll, S2 against S0:

| Round | S2 (2P / 3P / 4P) | S0 (2P / 3P / 4P) |
|:--|:--|:--|
| R2 | 0.49 / 0.43 / 0.42 | 0.59 / 0.51 / 0.51 (about −17%) |
| R4 | 0.57 / 0.52 / 0.51 | 0.69 / 0.61 / 0.62 |

- This is much smaller than under the LEGACY bots, where S1 dropped to 0.27.
- Dead turns fall to 0.3–0.4%, against 2.3% in v0.46, so there is no income denial.
- **Residual.** The reserved lever, making the company die the Round 1 Next Sprint priority, stays parked unless playtesters notice the dip.

## 5. Decisions for the User

1. **D-68-1:** Re-base the Δ-rounds and income guardrails on the fixed-bot baseline (S3 and V45TA). *Recommended.*
2. **D-68-2:** Ship `v047_roster` with `bot_thin_tracks=("RELEASE",)` (S2). *Recommended.*
3. **D-68-3:** Make no `[TUNE]` change. Keep Triage L1 `+$2`, Gray F3 `+$2 / +2 🔬`, and 6 starting Secrets.

Next steps, per spec §17 "Then":
- run the dominance matrix and the ref1 check on S2;
- add the V45TA reference arm to the sweep script.
