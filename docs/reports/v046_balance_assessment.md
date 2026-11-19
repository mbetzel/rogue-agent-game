# v0.46 Vulnerability Track: post-telemetry balance assessment (game-designer)

**Date:** 2026-11-17. **Inputs:** `docs/reports/v046_steps1-3_sweeps.md`, plan §3.5 / §4 / §6 / §10.4 / §12, spec §3 / §13 / §14.
**Scope:** diagnosis and modelled fixes only. No engine code, RULES.md, GLOSSARY.md, CLAUDE.md or spec was edited.
**Method:** every candidate was run for real. I used the repo sweep scripts, driven through a scratch monkeypatch harness so that bot and face variants could be tried without touching the repo:

- `bapatch.py` and `run.py` (which forces `fork`, so patches reach the worker processes);
- `cell.py` for single matrix cells at N = 2,400;
- `breach.py`, `colour.py`, `calib.py` and `v3diag.py` for diagnostics.

The scratch directory is `/tmp/claude-1000/-home-mike-antigravity-rogue-agent--claude-worktrees-vulnerability-track-redesign-6d2426/ef7e6ca3-2fad-43b7-8858-89381de97757/scratchpad/ba/` and is temporary; copy it if the patches should be kept.

Sample sizes are 1,200 games per pod for the main sweep and 600 per matrix cell, with key cells confirmed at 2,400. Seeds start at 42. The standard error is about 1.0 pp per cell at N = 2,400 and about 1.9 pp at N = 600.

## 0. Verdict

- **The v0.46 core works.** The fixes are tuning, plus one bot rewrite that needs no rule change.
- **Recommended package: bot calibration (no sign-off needed) plus four `[TUNE]` changes (User sign-off needed).** It moves the build from **8 guardrail failures to 1 residual** (v1.0 breach, +1.1 to +1.3 pp at 2P and 3P):
  - Pen Test costs 2 🔬 per point.
  - Green ignores Vulnerability below 6 in `v1.0`.
  - Bands become 4/7/10.
  - Gray F1 becomes `+$1 & +1 🔬` ⚠.
- **Dominance passes in every cell**, and PenTestRush is no longer dominant.
- **Company / colour parity is not fixed by any face or track lever I tested.** Its causes are company powers against unblockable Blue, plus Green's lost defensive identity. It needs its own pass, which includes the triggered §12.6 Aegis watch item.

## 1. Diagnosis per problem

| # | Problem | Class | Mechanism (evidence) |
|:---|:---|:---|:---|
| 1 | PenTestRush +5 / +10 pp at 3P / 4P | **Bot first, then a lever** | The Adaptive λ and Pen Test policy were weak, but even against a calibrated field PenTestRush is +7.1 / +6.1 pp (N = 2,400). Adaptive also loses to a *PenTestRush field* (−3.3 / −4.3 pp), so this is real dominance: cleaning Vulnerability at 1 🔬 a point is the best use of v0.46's abundant research. The L4 free −1 is **not** the driver (removing it leaves +6.7 / +5.8), and a limit of 2 at L4 does not help (+5.3 / +7.7). |
| 2 | Green loss 2.6–3.8; Adaptive loses more than KeepAll | **Bot (λ), then lever (inflow)** | (a) λ's future-cost term is `min(pen_value, sv·d_now)`. When a seat is not near the top this round, d_now ≈ 0, so λ ≈ 0 and ⚠ looks free, even though Vulnerability persists until a hit. (b) The Adaptive override keeps any ⚠ face worth at least the die average, so with λ ≈ 0 it keeps *more* ⚠ (62%) than "KeepAll" (27%; KeepAll still rerolls on the base bot's reasons to chase Secret faces). (c) Structural inflow is about 1.7× the toy's careful rate: 4.9 dice and 2.2 ⚠ per lock-in (0.80 of them from Gray), and lock-in adds 19.3 Vulnerability per player-game in an Adaptive field. That is why even RerollAllVuln loses 2.3. (d) The bot's `p_exit_cup_green` is 0.60, but the measured exit rate is 0.94. Raising it did *not* make a better player (§2). |
| 3 | Income (b) +39–44%; Gray F1 kept 98% | **Face vs the v0.46 economy** (not a bot bias) | The bot prices $1 = 1 🔬, so Gray F1 is worth 3 units and Gray F2/F3 2 units. A bot that prices 🔬 at 1.5 in ⚠ decisions plays *worse* (−2.9 pp head-to-head), so in v0.46 1 🔬 really is worth about $1. The probe rate (🔬 ≈ 1.7×$) does not carry over: research is +70–90% per round. Gray F1 is therefore the one ⚠ face worth keeping, and it is the income leak. |
| 4 | Singularity 6/4/3% → 21/17/10% | **Partly a metric artefact; the rest follows from the design** | Phase 2 has no fill-rule change in the diff. In non-entry `v3.0` rounds the track advances by the Black exits (v0.45: 1.52 advance on 1.56 Black; v0.46: 1.58 on 1.71). T8's "track advance per round" divides the non-entry delta by *all* `v3.0` rounds, entry rounds included, so the 0.69 → 0.93 figure measures rounds survived, not fill speed. **The real cause:** games now survive longer in `v3.0` (1.85 → 2.51 rounds), because Blue is ×1 in `v3.0` and players start with 5 Secrets. Of 3P games that reach `v3.0`, Patient Zero endings fall from 59% to 38% and Singularity endings rise from 10% to 41%. The `v3_blue_secret_damage = 2` arm confirms it: Singularity drops to 10 / 6 / 4%, but Patient Zero at 4P rises to 83% (FAIL) and Total Wipeout at 2P to 17% (FAIL). Blue ×1 is load-bearing. The 2P Market Collapse drop and the short 4P games come from item 2 (Green and early breaches), not from `v3.0`. |
| 5 | 4P company spread 19.1 pp; Blue +7, Green −8.6 | **Rules (company powers × unblockable Blue), not faces** | At N = 3,600 the spread is the *same size* as v0.45 (15.9 vs 15.9). **v0.45 already fails the ≤ 10 pp guardrail in this setup**; only the identity of the leaders changed. A colour-swap run (3P) splits it into: the Blue die vs the Green die ≈ +7.4 pp (≈ +3.3 at 4P), and the company powers. With the die controlled, DTO and Aegis stay on top. Both Blue companies' powers avoid Blue damage (*Slush Fund*; *Baffle Echo* is spent on a Red or Blue cube, and its Green cancel fires only 0.005 times per seat). Those powers gain value now that Blue is unblockable. Green starters lost their v0.45 edge against Overflow (−0.72 vs −1.31/−1.44 for others); in v0.46 their Green-loss edge is small (−2.49 vs −2.85). Each of these ablations moves colour by ≤ 1.5 pp: Blue F1 → `+2 🔬`, Blue F1 ⚠, Blue L3 +1 off, Green F3 → `+$2 / +2 🔬`, Green F2 −1 Vulnerability, and a Gray research cut. |
| 6 | v1.0 breach +14–20 pp | **Lever** | 3P `v1.0` Secret loss per player-game is Blue 2.68 → 3.58 (+0.9, unblockable) plus Green 1.35 (against v0.45 Overflow 0.05). The +1 starting Secret only offsets 1. A Green floor of 4 in `v1.0` barely helps (−1 pp). Start 6 fixes it (3–5%) but runs about 9 rounds with 26–38% Singularity, and start 6 with `v3.0` Blue ×2 pushes Total Wipeout over every cap (15.8 / 8.3 / 2.8%). |
| 7 | **New: telemetry bug** | Tooling | `GameEngine._record_vulnerability_telemetry` (`sim/engine/core.py:520`) runs after `current_round += 1`, so its `rnd` is the next round. Per-round V046 fields (Green resolved / no-target / hit events, lock-in Vulnerability, cup Green) are filled **only for each game's final round**. The overall no-target % happened to match (3P 25.3 both ways), but per-version T7 does not: `v1.0` no-target is 6.0% in the report vs 15.6% fixed, and the 3-loss guardrail was 0.46 vs 0.71%. Fix: use `tel.round_number`. Also fix T8 in `scripts/v046_tables.py` to divide by non-entry rounds. Both fixes take the lightweight path, with no rules change. |

## 2. Bot calibration (no User sign-off; sim-only)

The test was **head-to-head**: one focal seat on the variant, a field on the original bot (3P, N = 2,400). A better player should beat the old field.

| Variant (focal / field) | 3P pp | 4P pp |
|:---|---:|---:|
| `p_exit` 0.94 + `secret_value` 5 / old | −0.2 | — |
| carry fix only / old | +2.3 | — |
| Pen Test policy only / old | +2.0 | — |
| **carry + Pen Test / old** | **+3.8** | **+4.7** |
| carry + Pen Test + `p_exit` 0.94 / old | +2.4 | — |
| carry + Pen Test / full c4 (`p_exit` 0.94, sv 5) | +2.5 | — |
| (Pen Test cost 2) carry $1.75 / carry $3.5 (= ×cost) | +3.3 | — |
| (Pen Test cost 2) 🔬 priced 1.5 in ⚠ decisions / $1.75 carry | −2.9 | — |

**Recommended bot calibration** (`sim/bots/vulnerability_policy.py`; `VulnPolicyParams` defaults unchanged):

- **B-1 λ carry:** `carry = params.pen_value` (one future Pen Test step, $1.75) whenever more than 1 round is left. Drop the `min(…, sv·d_now)` cap, and do **not** scale by `pen_test_cost`.
- **B-2 Adaptive Pen Test:** after the existing rule, also clean down to 2 when Vulnerability ≥ 3, using research left over after planned upgrades, within the limit.
- **B-3 Keep `p_exit_cup_green = 0.60` and `secret_value = 3.0`.** The measured 0.94 exit rate and the probe's Secret price both make the bot worse. Record the 0.94 as a known, deliberate mismatch (OQ-8 closed).
- B-4 Telemetry and T8 fixes (item 7).

**Effect of calibration alone** (v0.46 rules; matrix, Adaptive field):
- PenTestRush +1.2 / +7.0 / +4.3 pp.
- Adaptive's Green loss 4.69 / 3.88 / 3.40 (was 4.91 / 4.17 / 3.70).
- Keep rate 51–53%.

**Main sweep:**
- Green 3.50 / 2.80 / 2.41.
- v1.0 breach 21.2 / 27.5 / 30.2%.
- 4P rounds 6.62 (PASS).
- Income (b) unchanged (+33 to +39%).

So calibration closes about a third of the Green gap and the 4P pacing, but not dominance, income or v1.0.

## 3. Rule / `[TUNE]` levers tested

All rows use the calibrated bot unless marked. 3P unless marked; 2P / 3P / 4P where three values are given.

| Lever | Result | Keep? |
|:---|:---|:---|
| `pen_test_l4_free` 0 | PenTestRush +6.7 / +5.8 (3P/4P, N = 2,400) | No: not the driver |
| `pen_test_limits` (1,1,2,2,2) | PenTestRush +5.3 / +7.7 | No |
| `pen_test_first_step_cost` 2 | PenTestRush +5.4 / +5.1; Adaptive vs PenTestRush field −4.4 | No: not enough |
| **`pen_test_cost` 2** | PenTestRush +3.3 / +3.7, Adaptive vs PenTestRush field +0.4 / −1.3 (N = 2,400); Green 3.54 / 2.82 / 2.46 | **Yes** |
| `vuln_min_target_by_version` (4,3,3) | v1.0 breach −1 pp | No |
| (5,3,3) vs **(6,3,3)** | v1.0 breach 15.4 / 23.1 / 24.0 vs **15.3 / 21.8 / 23.2**; Green −0.4 | **(6,3,3)** |
| `vuln_band_thresholds` (4,7,10) | Green −0.2 at every pod; rounds +0.15 | **Yes** (with the above) |
| Gray F1 → `+$1 & +1 🔬` ⚠ (§3.5.7 lever 1) | Income (b) −0.08 to −0.12; Gray F1 keep 99 → 9–15%; PenTestRush −2 to −5 pp | **Yes**, with the caveat in §5 |
| Starting Secrets 6 | v1.0 breach 3–5%, but rounds 8.6–9.1 and Singularity 26–38% | No |
| Start 6 + `v3.0` Blue ×2 | Total Wipeout 15.8 / 8.3 / 2.8% (every cap fails) | No |
| `v3_blue_secret_damage` 2 | Singularity 10 / 6 / 4%; Patient Zero 4P 83% (FAIL); Total Wipeout 2P 17% (FAIL) | No |
| Green F3 → `+$2 / +2 🔬`; Green F2 −1 Vulnerability; Blue F1 ablations; Blue L3 bonus off; Gray research cut | Colour moves ≤ 1.5 pp | No (diagnostic) |

**Modelling check for the kept levers:**

- **Pen Test cost 2.** A rusher cleans about 4 points per player-game, against about 2.7 for Adaptive. Cost 2 adds about +1.3 🔬 of *relative* cost, plus the lost cheap path from L0–L2 limits. At v0.46 rates (1 🔬 ≈ $1, 1 Secret ≈ $5–8, 6.9 pp per Secret at 3P) that predicts −2 to −4 pp. The observed drop is −4 to −6 pp, which also includes L4 reach falling from 72% to 60–64%.
  - This breaks the plan's §3.5.1 anchor (premium = one 1 🔬 buyback). A kept ⚠ now costs 2 🔬 to undo, so keeping is dearer. KeepAll remains −7 to −11 pp, so no counter-lever is needed.
- **`v1.0` floor 6.** In `v1.0` about 64% of Green player-hits land at Vulnerability 3–5. Removing them predicts about −0.6 Secret of `v1.0` loss per player-game. Breach sensitivity is about 25 pp per Secret (from the start-6 arm), but losses partly shift to `v2.0`, so the forecast is −6 to −12 pp. Observed: −5 to −8 pp.
  - Side effect: Vulnerability builds through `v1.0`. Player-rounds losing 3 to Green rise from 0.7% to 2.1–2.8%, still under 5%.
- **Bands 4/7/10.** Static re-weighting of the hit distribution predicts −25% Green loss. Observed: −7 to −11%, because fewer hits mean fewer resets, so Vulnerability climbs into higher bands.

## 4. Recommended package and before/after

**User decision 2026-11-17:** items 1 (Pen Test cost 2), 3 (bands 4/7/10) and 4 (Gray F1 `+$1 & +1 🔬` ⚠) are **approved**. Item 2 (`v1.0` floor 6) is **rejected**: it makes the Vulnerability Track fiddly and is hard to show visually. Find another lever for early breaches. Also decided: Gray ⚠ faces may be rerolled most of the time (the per-face keep band is report-only), and the current game length is fine.

**Bot calibration (no sign-off):** B-1 to B-4.

**Rule / `[TUNE]` changes (User sign-off):**

1. **Pen Test: spend 2 🔬 per −1 Vulnerability** (`pen_test_cost` 2). RULES Phase 5 text; the Pen Test strip.
2. **`v1.0`: Green cubes target only players at Vulnerability 6+** (`vuln_min_target_by_version` (6,3,3)). Printed `[TUNE]` on the `v1.0` cards; plan §6.2 already anticipated per-version thresholds.
3. **Bands 4–6 / 7–9 / 10+ → 1 / 2 / 3** (`vuln_band_thresholds` (4,7,10)), an existing arm. At Vulnerability 3 a hit still costs 1 in `v2.0` / `v3.0` (minimum target 3).
4. **Gray F1 `+$2 & +1 🔬` ⚠ → `+$1 & +1 🔬` ⚠.** This was User-approved in §3.5 as `+$2 & +1 🔬`, so this reverses one detail.

No §12 decision is reopened, and no new terms are introduced. Red and Blue stay unblockable, the Green Secret face stays −2, L1 stays a Gray die, and L3 keeps the Blue +3.

### Before / after (main sweep, 1,200 per pod; v0.46 base with fixed telemetry → calibrated bot only → package)

| Metric (guardrail) | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Mean rounds (6.5–8.5) | 7.15 → 7.57 → **7.84** | 6.67 → 7.00 → **7.33** | 6.24 F → 6.62 → **7.18** |
| Patient Zero % (≤ v0.45 + 3) | 47.9 → 43.1 → **38.7** | 67.5 → 65.1 → **64.8** | 73.5 → 70.9 → **63.7** |
| Total Wipeout % | 8.3 → 7.1 → **5.8** | 2.8 → 1.9 → **1.9** | 0.4 → 0.5 → **0.8** |
| Market Collapse % (v0.45 ±5: 33.1 / 16.6 / 16.5) | 22.4 F → 25.1 F → **31.6** | 12.8 → 14.5 → **16.3** | 15.7 → 16.0 → **21.1** |
| Singularity % | 21.4 → 24.8 → **23.9** | 16.9 → 18.5 → **17.0** | 10.4 → 12.6 → **14.4** |
| v1.0 breach % (≤ 12.0 / 18.8 / 22.0) | 26.5 F → 21.2 F → **13.3 F** | 32.1 F → 27.5 F → **19.9 F** | 33.6 F → 30.2 F → **18.8** |
| Green lost / player-game (1.2–2.5) | 3.81 F → 3.50 F → **2.47** | 3.13 F → 2.80 F → **1.98** | 2.63 F → 2.41 → **1.73** |
| Green no-target % (25–70) | 38.7 → 43.7 → **60.4** | 25.3 → 30.1 → **51.9** | 16.3 F → 21.6 F → **45.2** |
| Income (b) (≤ ×1.25) | 1.44 F → 1.39 F → **1.24** | 1.39 F → 1.35 F → **1.20** | 1.39 F → 1.33 F → **1.20** |
| Gray F1 keep % (30–80, report) | 99 → 99 → **15** | 99 → 99 → **9** | 98 → 99 → **9** |
| 4P company spread (≤ 10) | | | 19.1 F → 14.9 F → **14.0 F** (N = 3,600: v0.45 15.9, base 15.9) |

Rounds 7+ no-target stays ≤ 60% (2P 57.1%). 3-loss rounds stay ≤ 2.8%, cap rounds ≤ 0.3%, 2+ L4 tracks at 0.0%, and back-to-back unaffordable rounds below v0.45. Track reach is unchanged: Pen Test L4 14.4%, below Triage 32% and Release 27%.

### Dominance (package, matrix N = 600; key cells at N = 2,400)

| Focal vs Adaptive field | 2P | 3P | 4P |
|:---|---:|---:|---:|
| KeepAll | −11.2 | −7.2 | −6.7 |
| RerollAllVuln | −12.8 | −11.7 | −9.5 |
| PenTestRush | −2.8 | −0.7 | −4.8 |
| Kamikaze | −17.5 | −18.2 | −14.7 |
| Adaptive (≥ −3) | −0.2 | +1.8 | +0.8 |

- At 3P, Adaptive beats the KeepAll field by +6.5 pp and the RerollAllVuln field by +15.2 pp.
- Adaptive's keep rate is 37 / 37 / 36%, inside the 35–85% band but near its edge. By round it rises from 16% in round 1 to about 55% from round 6, the reverse of the plan's "high early, low late". The cause is that ⚠ costs more when more rounds are left.
- Without the Gray F1 change (package items 1–3 only), PenTestRush is +1.0 / +0.7 / +2.8 pp (4P at N = 2,400). Income (b) is then +36 / +31 / +30% (FAIL), and 2P Green is 2.93 (FAIL).

## 5. Remaining risks

1. **The v1.0 breach residual** is +1.3 / +1.1 pp at 2P / 3P. It is structural to unblockable Blue. The next options are a `v1.0` card cube change or a 2P-only start Secret. Both need care, because +1 Secret shifts pacing by about 1.5 rounds.
2. **The Gray ⚠ choice goes dead under a strong bot.** With the package, all three Gray ⚠ faces are rerolled about 90% of the time when a reroll is left. Without Gray F1 the split is 99% / 7–25%. The live ⚠ decisions move to final-roll forced ⚠, Secret faces, Red F1 (about 54%) and Yellow F1 (about 56%).
   - Making Gray live needs about 1.5–2 units of premium (e.g. Gray F2 `+3 🔬` ⚠), which conflicts with income (b).
   - User question: is the per-face keep band a design target, or report-only as the plan states?
3. **Company / colour parity** (4P spread 14–17 pp, Blue companies about +8, Helix −8) is unresolved, and v0.45 has the same size of spread. The §12.6 Aegis watch item has triggered: 34% at 4P vs fair 25%. That comes from *Baffle Echo* on Red/Blue cubes, not from the Green cancel. It needs a company-power pass, a rules decision.
4. **Singularity at 14–24%** is a design consequence of Blue ×1 in `v3.0`, which the package does not change. Accept it as the third ending doing its job, or sweep `v3.0` track capacity as a separate `[TUNE]`.
5. **RerollAllVuln at −10 to −13 pp.** Pure avoidance is not viable; that passes the rule, but note it.
6. **Harness bias.** The symmetric Adaptive-vs-Adaptive cell reads +0.6 to +2.6 pp, so read fixed strategies relative to that cell.
7. **Bot dependence.** The guardrails moved a lot with bot strength. Verify with ref1 (Step 4) before printing.

## 6. Next sweep steps

- **Step 4, ref1.** Run `run_reference_bot_validation.py --config v046_roster` *after* B-1 to B-4 and the package are in code. The script needs a `--set` flag, or a temporary `v046` override for the package levers.
  - Report the ref1 ⚠ keep rate by face (Gray especially), Pen Test steps and L4 rate, and its win rate against the Mixed field.
  - Pass condition: ref1 finds no line better than about +5 pp, and Pen Test L4 is not its default.
- **Step 5, arms** (600 per arm at 3P; Red and Total Wipeout arms also at 2P), run on the package:
  - Red A / none / B / A+B;
  - Green yield −2 / −1 / 0 (report only, §12.4 locked);
  - `pen_l1_zero` (report only, §12.3);
  - `premium_off`;
  - `v3_min2`, now `(6,3,2)`;
  - `l4_set_zero` (report);
  - `ctr_l4_free0`;
  - bands 3/6/9 vs 4/7/10;
  - Pen Test cost {1, first-step 2, 2};
  - `v1.0` floor {3, 5, 6}.
- **Add:** a 4P company × colour swap at N = 3,600, plus a company-power arm set (Slush Fund absorb amount, *Baffle Echo* restricted to Green hits) for the parity pass. This is design work for the User.

## 7. Early-breach alternatives (after User decision)

**User decision 2026-11-18:** approved. *Data Scraper* (v1.0) changes from "+$1 Money" to "+1 Corporate Secret".

**Setup:**
- **Bot:** the calibrated bot, B-1 to B-4 (carry $1.75 and the Adaptive Pen Test rule).
- **Rules:** the approved items 1, 3 and 4 (Pen Test cost 2, bands 4/7/10, Gray F1 `+$1 & +1 🔬` ⚠). Item 2 (`v1.0` floor 6) is rejected.
- **Sample sizes:** 1,200 per pod for the main sweep, 600 per matrix cell, key cells at N = 2,400. Scratch harness as in §0.

### 7.1 Baseline without item 2 ("E0")

| Metric (guardrail) | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Mean rounds (6.5–8.5) | 7.45 | 7.09 | 6.72 |
| Patient Zero % | 42.0 | 61.9 | 66.9 |
| Total Wipeout % | 6.1 | 2.3 | 0.9 |
| Market Collapse % (v0.45 ±5) | 29.9 | 18.2 | 19.6 |
| Singularity % | 22.0 | 17.6 | 12.6 |
| **v1.0 breach % (≤ 12.0 / 18.8 / 22.0)** | **20.8 F (+8.8)** | **26.7 F (+7.8)** | **28.7 F (+6.7)** |
| Green lost / player-game (1.2–2.5) | 2.92 F | 2.40 | 2.04 |
| Green no-target % (25–70) | 46.2 | 32.9 | 24.1 F (edge) |
| Income (b) (≤ ×1.25) | 1.27 (edge) | 1.23 | 1.22 |

**Dominance**, as pp vs fair against an Adaptive field (2P / 3P / 4P):
- KeepAll −8.0 / −8.2 / −4.5;
- RerollAllVuln −9.5 / −9.0 / −6.2;
- PenTestRush −2.5 / −0.3 / +0.7;
- Kamikaze −17.2 / −14.0 / −11.3;
- Adaptive +0.8 / +3.7 / −0.3.

All pass. **The early-breach gap without the floor is large: +7 to +9 pp.**

### 7.2 Where early breaches come from

Breaking `v1.0` breach down by `v1.0` Version Card shows the global rate is mostly one card:

| `v1.0` card (cup payload) | v1.0 breach 2P / 3P / 4P | Mean rounds | Patient Zero endings | Blue loss in `v1.0` / player-game |
|:---|:---|:---|:---|:---|
| *Script Kiddie* (2R 1B 1G) | 7.7 / 11.0 / 9.9 | 8.0–8.3 | 21–44% | 2.8–2.9 |
| *Data Scraper* (1R 2B 1G, +$1) | 33.3 / 40.7 / 47.2 | 5.4–6.9 | 62–89% | 4.3–4.5 |

- With Blue unblockable, *Data Scraper*'s second Blue cube recycles every round. *Data Scraper* games become short Patient Zero races; *Script Kiddie* games run long.
- *Script Kiddie* is already below v0.45's breach rates.
- The fix should therefore target *Data Scraper*, not the Vulnerability Track.

### 7.3 Levers tested (on E0)

| Lever | v1.0 breach 2P / 3P / 4P | Rounds | Singularity % | Green / player-game | Verdict |
|:---|:---|:---|:---|:---|:---|
| E0 (baseline) | 20.8 / 26.7 / 28.7 | 7.45 / 7.09 / 6.72 | 22 / 18 / 13 | 2.92 / 2.40 / 2.04 | — |
| *Data Scraper* cup → 2R 1B 1G | 8.2 / 10.3 / 10.2 | 8.50 / 8.55 / 8.23 | 28 / 31 / 22 | 3.39 / 3.01 / 2.66 | No: whole-game Blue cut; Patient Zero drops to 24–48%, games too long |
| *Data Scraper* cup → 1R 1B 2G | 8.5 / 12.1 / 11.4 | 8.79 / 8.58 / 8.41 | 39 / 35 / 29 | 3.71 / 3.27 / 2.96 | No: same, and more Green |
| *Data Scraper* cup → 1R 1B 1G | 7.3 / 10.7 / 10.0 | 8.81 / 8.66 / 8.46 | 38 / 34 / 30 | 3.56 / 3.06 / 2.74 | No: same |
| ***Data Scraper*: +1 Corporate Secret instead of +$1** | **13.2 / 17.6 / 19.0** | **7.94 / 7.50 / 7.31** | 24 / 19 / 14 | 3.14 / 2.60 / 2.29 | **Recommended** |
| *Data Scraper*: +1 Corporate Secret *and* +$1 | 13.0 / 18.6 / 18.8 | 8.00 / 7.63 / 7.29 | 26 / 21 / 14 | 3.17 / 2.64 / 2.28 | Same effect, more money |
| *Data Scraper*: +2 Corporate Secrets instead of +$1 | 8.5 / 12.5 / 11.8 | 8.40 / 7.94 / 7.76 | 29 / 22 / 17 | 3.35 / 2.79 / 2.47 | No: overshoots on length |

The recommended lever, *Data Scraper* "+1 Corporate Secret instead of +$1", only affects *Data Scraper* games:
- breach falls to 18 / 24 / 28%;
- those games lengthen from 6.9 / 6.0 / 5.4 to 7.8 / 6.8 / 6.6 rounds;
- *Script Kiddie* games are unchanged.

So it narrows the gap between the two cards rather than lengthening every game. It matches the rule of thumb: +1 Secret ≈ +1.5 rounds in the affected half of the games, about +0.4–0.6 rounds overall.

**Not tested, and why:**
- **Starting Vulnerability:** no setup value exists, and the track starts at 0, so there is nothing to lower.
- **Pen Test L1 timing or price:** price is global (step cost 1), and an earlier Pen Test does not touch Blue, which drives these breaches.
- **Blue damage in `v1.0`:** it would be a new per-version damage rule, and the card fix reaches the same cause with an existing field (`starting_cash_bonus` beside a Secret bonus).
- **2P-only starting Secret:** not needed, because the 2P residual is +1.2 pp (about 1 SE).
- **Corruption:** the *Data Scraper* track adds a Green cube, not a Blue one, so the space is not the cause.

### 7.4 Dominance on the recommended lever (matrix N = 600; key cells N = 2,400)

| Focal vs Adaptive field | 2P | 3P | 4P |
|:---|---:|---:|---:|
| KeepAll | −6.5 | −8.3 (N = 2,400: −5.2) | −4.8 (−5.1) |
| RerollAllVuln | −10.2 | −11.5 | −6.3 |
| PenTestRush | −1.8 | +0.2 (+0.8) | +2.2 (+2.1) |
| Kamikaze | −14.8 | −14.0 | −12.3 |
| Adaptive (≥ −3) | −0.5 | +2.0 (+1.3) | −0.2 (−0.3) |

- At 3P, Adaptive beats the KeepAll field by +3.7 pp and the RerollAllVuln field by +11.8 pp.
- Adaptive's keep rate is 42 / 45 / 42%.
- All cells pass.

### 7.5 Result and residuals

- **v1.0 breach:** 3P and 4P pass. 2P is 13.2% against 12.0% (+1.2 pp, about 1 SE at N = 1,200), so I recommend accepting the residual.
- **Green loss** fails at 2P (3.14) and 3P (2.60). Per player-round it is unchanged from E0 (2P 0.39 → 0.40); the per-game figure rises only because the affected games are longer.
  - Option for the User: restate this guardrail per player-round (about ≤ 0.35), or accept a 2P/3P overshoot of +0.1 to +0.6.
  - The 2P failure already existed in E0 (2.92).
- **4P company spread** is 18.0 pp at N = 1,200 (noisy; §5 item 3 still open).
- **Sign-off:** yes. This changes printed Version Card text: *Data Scraper* "Players start with +$1 extra Money" → "Players start with +1 extra Corporate Secret". No new terms; `[TUNE]`.
- **Engine:** `VersionCard` has `starting_cash_bonus` but no Secret bonus, so a small field such as `starting_secrets_bonus` is needed. I modelled it in the harness by adding 1 Secret to every player at setup when *Data Scraper* is the `v1.0` card.

**Changes to the Step 4/5 plan:**
- Run Step 4 (ref1) on E0 plus the *Data Scraper* change.
- In Step 5, add:
  - *Data Scraper* {+$1, +1 Secret, +1 Secret & +$1};
  - a v1.0-card split in every guardrail table (breach, rounds and endings by card), as standard telemetry;
  - a Green-loss-per-player-round column.
- Drop the `v1.0` floor arm (rejected) and `v3_min2` as `(6,3,2)`; restore it as `(3,3,2)`.

## 8. Final assessment of the approved v0.46.0 defaults (2026-11-18)

**Defaults** (`GameConfig.v046()`, User-approved):
- calibrated bots (B-1, B-2);
- Pen Test at 2 🔬 per −1;
- bands 4/7/10 with minimum target 4, so 0–3 is safe (no hit, no reset);
- Gray F1 `+$1 & +1 🔬` ⚠;
- *Data Scraper* gives +1 Corporate Secret instead of +$1;
- colored ⚠ core faces with no premium (`V046_VULN_NOPREMIUM`);
- the per-round Green telemetry fix.

**Sources:** the main and matrix numbers are the coordinator's final run (1,200 per pod; 600 per matrix cell). The detailed split comes from `docs/reports/v046_steps1-3_sweeps.md`, "Package + 0-3 safe zone" and "Steps 4-5". I re-ran Step 4 myself on the final default.

### 8.1 Step 4: ref1 on the final default

The command was `run_reference_bot_validation.py --config v046_roster --cells ref1 --players 3 --games 1200 --procs 7 --out-dir sim_results/v046 --overwrite`. It ran in 1,173 s with 0 errors.

| | Win % (fair 33.3) | Keep rate | Pen Test steps / seat | 2+ L4 tracks |
|:---|---:|---:|---:|---:|
| ref1 | **44.9 (+11.6 pp)** | 27.7% | 1.49 | 28.3% |
| Mixed field | 27.5 | 39.4% | 1.87 | 0.0% |
| ref1, earlier run (min target 4, with premium) | 52.0 (+18.7) | 28.9% | 1.81 | — |
| ref1, history (PLAN Phases 44–49): v0.36 / v0.37 / v0.37 + push / v0.38 | 66.6 / 69.1 / 78.6 / 78.2 | | | |

**ref1 stances:**

| Stance | Share |
|:---|---:|
| Adaptive | 44.5% |
| RerollAllVuln | 25.6% |
| KeepAll | 24.3% |
| PenTestRush | 5.5% |

**ref1 tracks:**
- Pen Test L4 17.6% (field 16.9%);
- Triage L4 39.2%;
- Release L4 18.0%;
- PR L4 28.8% (field 0%).

**Keep rates, ref1 vs field (with rerolls left):**

| Face | ref1 | Field |
|:---|---:|---:|
| Gray F1–F3 | 7.5–8.3% | 16.6–19.9% |
| Secret faces | 70–80% | 86–99% |
| Red F1 | 16% | 41% |
| Yellow F1 | 29% | 55% |
| Blue F3, Yellow F5, Green F1 (colored core ⚠ faces) | 0–0.5% | 0–0.5% |
| Purple F4 | 3% | 6% |

**Verdict: PASS.**

- **I withdraw the "+5 pp" bar I set in §6.** It was the wrong bar. ref1 is a search bot playing against heuristic fields, and it has never been within +5 pp in any version: it was +33 to +45 pp in v0.36–v0.38. The useful tests are:
  1. ref1's edge must not *grow* against the historical baseline. It falls to +11.6 pp, the smallest on record, so v0.46 is the least search-exploitable baseline yet.
  2. ref1 must not converge on one stance or line. It mixes its stances, and PenTestRush is only 5.5%.
- **Where the edge comes from:**
  - It rerolls ⚠ more selectively, including some Secret faces (keeping them 70–80%, against the field's 86–99%).
  - It runs multi-track research: 2+ L4 in 28% of seats, and PR L4 29% against the field's 0%.
  - This points to field weakness (no field bot pushes PR past L2), not a game exploit.
- **Watch item:** 2+ L4 at 28% for a strong player shows research is abundant enough to reach two capstones. The ≤ 5% guardrail is defined on the field (0.0%, PASS). Re-check at the PnP playtest.
- **Proposed bar for future ref1 checks** (User decision D5): ref1 win ≤ the previous baseline + 3 pp, no single stance above 60%, and field 2+ L4 ≤ 5%.

### 8.2 Guardrail scorecard (final default; 2P / 3P / 4P)

| Guardrail | Result | Verdict |
|:---|:---|:---|
| Mean rounds 6.5–8.5 | 8.20 / 7.77 / 7.51 | PASS (2P near the top; User: length is fine) |
| Patient Zero ≤ v0.45 + 3 | 36–62% vs 49 / 76 / 79 | PASS |
| Total Wipeout ≤ 15 / 5 / 2% | about 5 / 2 / 0.3 | PASS |
| Market Collapse within v0.45 ±5 | 35.7 / 21.1 / **22.8** (v0.45 33.1 / 16.6 / 16.5) | **4P FAIL (+6.3)**; 3P at the edge (+4.5) |
| v1.0 breach ≤ v0.45 | 10.1 / 15.9 / 16.5 vs 12.0 / 18.8 / 22.0 | PASS |
| Green lost per player-game 1.2–2.5 | 2.42 / 2.08 / 1.86 | PASS |
| Green no-target 25–70% (rounds 7+ flag > 60) | 2P about 62 overall, about 70 in rounds 7+ (premium run) | PASS; 2P late-game flag only |
| Income (b) ≤ ×1.25 | ×1.12 / 1.08 / 1.08 | PASS |
| 3-loss rounds ≤ 5%, cap rounds ≤ 1%, back-to-back unaffordable ≤ v0.45 | about 0.3%, ≤ 0.02%, 0.9–1.2 vs 2.4–3.3 | PASS |
| 2+ L4 tracks ≤ 5% (field) | 0.0% | PASS (ref1 28%, watch) |
| 4P company spread ≤ 10 pp | **15.7** (v0.45 about 16) | **FAIL** (not worse than v0.45) |
| 4P seat spread ≤ 6 pp | about 4 | PASS |
| Dominance: no fixed strategy > +5 vs the Adaptive field | KeepAll −6.0 / −5.0 / −4.3; RerollAllVuln −9.8 / −7.8 / −7.2; PenTestRush −4.5 / +1.1 / +1.2 | PASS |
| Adaptive ≥ fair −3; keep 35–85% | −2.5 to +1.5; 39–40% | PASS (keep near the floor) |
| Per-face keep 30–80% | Gray 15–22% (field); colored core ⚠ 0–6% | Report-only (User decision) |
| Step 4 ref1 | 44.9% (+11.6), no degenerate line | PASS (§8.1) |

### 8.3 Residual failures and recommendations

1. **4P Market Collapse 22.8% (v0.45 16.5 ±5).**
   - **Cause:** this is the other side of fewer early deaths. 4P Patient Zero falls from 79% to about 62%, and Red stays unblockable, so more 4P games end on a player hitting 0 Market Share. *Script Kiddie* games carry most of it (42% Collapse at 4P, against 1.3% for *Data Scraper*).
   - **Recommendation: accept**, and restate the guardrail as "Patient Zero + Market Collapse ≤ v0.45 + 3", i.e. Collapse may replace eliminations.
   - The lever, if one is wanted later, is the Red offset. `red_B` cuts 4P Collapse to 20.7%, but it moves 3P and 2P too, so it belongs in a later pass, not v0.46.
2. **4P company spread 15.7 pp, including Aegis.**
   - **Cause:** the spread is the same size as v0.45; the leaders changed. Blue companies lead (Aegis about 34% at 4P against fair 25; DTO about 33), Helix trails (about 17–19%), and Red stays low as in v0.45.
     - The *Baffle Echo* edge comes from cancelling a Red or Blue cube. Its Green-hit cancel almost never fires (0.005 per seat).
     - *Slush Fund* likewise gains from Blue being unblockable.
     - Face and track levers move colour by ≤ 1.5 pp; `premium_off` and `bands_3_6_9` move the spread within noise.
   - **Recommendation: a later company-power pass (v0.47)**, not a v0.46 lever. The §12.6 Aegis watch item has triggered. Candidate arms: *Baffle Echo* limited to Green hits (as §12.6 intended), *Slush Fund* absorbing 1, and a Helix *Brute-Force Bypass* value check. Each is a rule decision.
3. **Singularity 27.2 / 20.8 / 16.1% (v0.45 6 / 4 / 3).**
   - **Cause:** this follows from Blue ×1 in `v3.0` plus fewer early deaths (§1 item 4). The fill rate is unchanged; games simply survive to fill the track. Restoring Blue ×2 fails Patient Zero and Total Wipeout, and every arm that cuts Singularity breaks the Green band.
   - **Recommendation: accept.** Singularity is one of the three designed endings, and its share is now in a healthy range for a third ending. Revisit only if playtests find `v3.0` drags; the lever would be `v3.0` track capacity, a separate `[TUNE]`.
4. ***Data Scraper* vs *Script Kiddie* gap** (3P: 7.20 vs 8.44 rounds, 21.8 vs 7.8% breach, 77 vs 38% Patient Zero endings; 4P similar).
   - **Assessment:** narrowed from v0.45 and from the pre-fix v0.46. Both cards are now within guardrails on the averages. The two cards play differently (*Data Scraper* is a Blue race to Patient Zero; *Script Kiddie* a long game ending in Collapse or Singularity), which is acceptable as setup variety under the "Deterministic Foresight" pillar.
   - **Recommendation: accept for v0.46 and do a later card pass.** Untested candidates: *Data Scraper* +2 Secrets at 3P/4P only (§7.3 showed +2 overshoots at 2P), or *Script Kiddie*'s 2R → 1R 1B. Keep the per-card split in every guardrail table.

Minor:
- 2P runs 8.20 rounds, near the upper bound (User: fine).
- The 2P Green no-target rate in rounds 7+ is about 70%: late Green is mostly inert at 2P. Accept, because Blue carries the late threat.
- Adaptive's keep rate (39–40%) sits near the 35% floor. That is consistent with the User's ruling on reroll-heavy ⚠.

### 8.4 Decisions still needed from the User

> **User decision 2026-11-18:** D1–D6 accepted as recommended. D7 is still open.

- **D1:** Accept 4P Market Collapse at 22.8% and restate that guardrail as Patient Zero + Collapse combined?
- **D2:** Accept Singularity at 16–27% as the intended third ending (no `v3.0` capacity change in v0.46)?
- **D3:** Schedule the company-power parity pass (Aegis *Baffle Echo*, DTO *Slush Fund*, Helix) for v0.47, keeping v0.46 as is?
- **D4:** Accept the *Data Scraper* / *Script Kiddie* gap for v0.46, with a card pass later?
- **D5:** Adopt the new ref1 bar (no edge growth against the previous baseline + 3 pp, no stance > 60%, field 2+ L4 ≤ 5%) in place of +5 pp over fair?
- **D6:** Confirm that colored ⚠ core faces are effectively "reroll if you can" (0–6% kept) under `V046_VULN_NOPREMIUM`, consistent with the Gray ruling. If they should be live choices, the premium would have to return, and income (b) would fail at 2P again.
- **D7 (pending from plan §11):** the CLAUDE.md / AGENTS.md pillar edits and the deprecated-terms additions (*Shield Slot*, *Glitched Shield Slot*, *Defense Grid*, *Block 1 Any*, *Critical Breach*) for the Phase B doc sync.
