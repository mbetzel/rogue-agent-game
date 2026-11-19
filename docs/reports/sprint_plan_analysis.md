# Sprint Plan (Current / Next Sprint): Pre-SDLC Analysis and Implementation Plan

**Status:** this is a proposal for the User to decide. No rules, glossary, sim, PnP, TTS or web files were changed.
**Baseline:** v0.46.0 (`GameConfig.v046_roster`, `mixed1` roster).
**Author:** game-designer.
**Date:** 2026-11-19.

## 0. Verdict

**The proposal does what it was meant to do.**
- Gray Legacy dice now take part in rolls. Gray roll share rises from 33% to 58%.
- The longest Gray stranding run falls from 11–12 rounds to 8.
- Colored dice now face a real choice of what to leave behind. In about two thirds of player-rounds, dice of different colors compete for Release Bandwidth.

**Cost: v0.46 pacing gets worse.**
- Games run 0.7–0.8 rounds shorter.
- Singularity falls to about 40% of its v0.46 share.
- Patient Zero rises by 10–14 pp.

The cause is **income, not breaches**. Release Bandwidth is the binding limit, so every forced Gray takes a slot from a colored die. Fewer colored dice roll each round, so fewer Secret faces are rolled.

**Recommendation:**
- **One lever:** starting Corporate Secrets `5 → 6` (`[TUNE]`). This is the only single lever that brings round length back within 0.1–0.3 rounds and passes every §8.2 guardrail. Singularity recovers only to about 55% of v0.46.
- **If Singularity share matters, a minimal combo:** +1 Secret **plus** Gray F1 `+$1 & +1 🔬` losing its ⚠, so Gray dice have 2 ⚠ faces. Rounds come within −0.0 to +0.26 of v0.46, Singularity recovers to 62–76%, and every guardrail passes. This changes the pillar text "Gray dice carry three ⚠", so it needs the User's approval.
- **Rejected:** Release Bandwidth 4→5 fails income. "Gray dice don't use Release Bandwidth" fails income (×1.47) and Green loss.

## 1. Method

- **Probe:** a scratch harness that monkeypatches the sim; it is not project code.
  - Path: `/tmp/claude-1000/-home-mike-antigravity-rogue-agent--claude-worktrees-scanned-box-sprint-plan-dc5f20/59928f72-1253-405a-809e-daadc89559d6/scratchpad/sprint_probe2.py`
  - It patches `production_return_to_scanned`, `graduate_scanned`, `conveyor_triage_v038` and `vulnerability.lock_in`.
- **Rules modelled (arm `A`, the User's priority reading):**
  - Production Return goes to the Current Sprint if the Current Sprint is empty, otherwise to the Next Sprint.
  - Current Sprint dice graduate first and are forced, up to Release Bandwidth.
  - Any spare bandwidth may take Next Sprint dice.
  - All leftover dice then become the Current Sprint.
  - Dice from Triage, purchases, PR L3 and the Blue Signature Attack enter the Next Sprint.
- **Bot choice:** the bots use the default priority (Purple > colored by cost > Gray) both to pick Current dice when Current > BW and to fill spare bandwidth from Next.
- **Sample:** 1,200 games per pod at 2P, 3P and 4P.
  - Seeds `42..1241` match the v0.46 sweeps. BASE reproduces FINDINGS §62 exactly: 8.20 / 7.77 / 7.51 rounds.
  - A second seed block (`5000..`) was run as a noise check. Seed-block noise is about ±0.25 rounds and ±3 pp on end shares, so all comparisons below are paired on the same seeds.
- **Income** is $ + 🔬 collected in Phase 3 per player-round, from `income_by_player`. This is a proxy for method (b).

## 2. Pacing, end triggers, Secrets (Ask 1)

### 2.1 Headline: BASE → A (seed block 1; block 2 in brackets)

| | 2P | 3P | 4P |
|:---|:---|:---|:---|
| Mean rounds | 8.20 → **7.41** [8.13 → 7.34] | 7.77 → **7.02** [8.01 → 7.35] | 7.51 → **6.76** [7.46 → 6.84] |
| Singularity | 27.2 → **11.8%** | 20.8 → **8.2%** | 16.1 → **6.2%** |
| Patient Zero | 32.1 → 46.0% | 56.7 → 70.0% | 61.0 → 71.2% |
| Market Collapse | 35.7 → 34.0% | 21.1 → 18.7% | 22.8 → 21.9% |
| Total Wipeout (guardrail 15 / 5 / 2) | 5.1 → 8.2% | 1.4 → 3.2% | 0.1 → 0.6% |
| Final Secrets per seat (all seats) | 9.14 → 6.21 | 8.05 → 5.88 | 8.40 → 6.37 |
| Income $+🔬 per player-round | ×1.04 | ×1.03 | ×1.03 |

### 2.2 Secrets ledger (3P, per seat-game; 2P and 4P are the same shape)

| Source | BASE | A | Δ | Per round, BASE → A |
|:---|---:|---:|---:|:---|
| Secret-face banks (R / B / G / P) | 8.26 | 5.96 | **−2.30** | 1.06 → 0.85 (**−20%**) |
| Market Leader payouts | 4.88 | 3.54 | **−1.34** | 0.63 → 0.50 |
| Other gains (Breakthrough, Blue F1, Y3) | 1.77 | 1.51 | −0.26 | flat |
| Blue damage | −10.80 | −9.28 | +1.52 | 1.39 → 1.32 |
| Green hits | −2.08 | −1.97 | +0.11 | 0.27 → 0.28 (flat) |
| Black Signature Attack, corruption | −0.87 | −0.71 | +0.16 | flat |

**The whole drop comes from fewer Secret faces rolled. Breaches do not rise.** Per round, Blue and Green losses stay flat or fall; per game they fall because games are shorter. Games end sooner because Secret income per round falls while the Blue clock is unchanged.

### 2.3 Why fewer Secret faces (per player-round, 3P)

| | BASE | A |
|:---|---:|---:|
| Dice in the Ready pool | 4.90 | 5.00 |
| …of which Gray | 1.25 | 2.31 |
| Colored dice rolled | 3.41 | **2.56 (−25%)** |
| Secret faces locked in | 0.65 | **0.53 (−18%)** |
| Colored dice that wait 1+ graduation after entering | 2% | **39%** |
| Purchases per seat-game | 3.91 | 3.37 |

The roll pool stays the same size, about one Release Bandwidth. Under A it fills in proportion to the dice you own, so each Gray displaces a colored die.

### 2.4 Vulnerability from forced Gray rolls (3P, kept ⚠ per player-round)

| | BASE | A |
|:---|---:|---:|
| Gray ⚠ | 0.52 | **0.88 (+0.36)** |
| Colored ⚠ | 1.14 | 0.87 |
| Total lock-in Vulnerability per round | 1.66 | 1.74 (+5%) |
| Green Secrets lost per game (band 1.2–2.5) | 2.08 | 1.97 (PASS) |

### 2.5 Win rates (paired seeds; spread = max − min)

| Spread | BASE | A |
|:---|:---|:---|
| Bot spread 2P / 3P / 4P | 10.5 / 18.0 / 10.7 pp | 4.5 / 16.2 / 9.1 pp |
| Company spread 2P / 3P / 4P | 19.2 / 17.8 / 15.7 pp | 23.5 / 18.4 / 17.7 pp |
| White Hat spread 2P / 3P / 4P | 10.1 / 9.0 / 8.1 pp | 10.3 / 6.5 / 15.0 pp |

- **Bots:** parity improves.
  - SecOpsTurtle falls (3P 43 → 35%; 4P 32 → 23%).
  - Acceleration gains (3P 34 → 43%).
- **Companies:** about the same, within noise of roughly ±3 pp on a spread. Aegis still leads and Helix still trails, so the v0.47 company-pass item stands.
- **White Hats:** the 4P widening is Spook up (28 → 33%) and Operator down (21 → 18%). Both are about 2–3 SE and have a mechanism (§4). Watch them.

### 2.6 Stranding

| | BASE | A |
|:---|:---|:---|
| Gray left in the Sprint Plan after graduation | 2.5 | 1.6 |
| Longest Gray stranding run (rounds) | 11–12 | **8** |
| Gray graduations after waiting 2+ rounds | 5.5% | 1.7% |
| Current > BW | 0% | 15–17% of player-rounds |
| Player-rounds with a multi-color leave-behind choice | — | **66%** (Next fill choice 50%) |

## 3. Compensating levers (Ask 2)

Rounds are shown as Δ against BASE; the other columns are values. Income is relative to v0.46. v0.46 is already ×1.08 of v0.45 and the guardrail is ×1.25 of v0.45, so the headroom is about **×1.157**.

| Arm (all on A) | Δ rounds 2P / 3P / 4P | Singularity 2P / 3P / 4P | PZ 3P | Income | Green lost 2P / 3P / 4P | Gray share | Verdict |
|:---|:---|:---|---:|---:|:---|---:|:---|
| A (no lever) | −0.79 / −0.75 / −0.75 | 11.8 / 8.2 / 6.2 | 70.0 | ×1.03 | 2.33 / 1.97 / 1.72 | 58% | pacing fails |
| **+1 starting Secret** | **−0.26 / −0.10 / −0.10** (block 2: −0.29 / −0.04 / +0.03) | 15.3 / 11.3 / 8.0 | 63.6 | ×1.04 | 2.52 / 2.18 / 1.93 | 57% | **PASS (single lever)** |
| +2 starting Secrets | +0.14 / +0.43 / +0.47 | 18.2 / 15.2 / 11.5 | 57.3 | ×1.04 | 2.65 / 2.34 / 2.11 | 57% | overshoots; Collapse +5 pp |
| **+1 Secret + Gray F1 clean** | **+0.02 / +0.26 / +0.16** | **20.3 / 15.8 / 10.0** | 57.6 | ×1.09 | 1.90 / 1.64 / 1.47 | 56% | **PASS (minimal combo)** |
| Release Bandwidth +1 (5 / 6 / 7) | −0.53 / −0.53 / −0.47 | 17.9 / 12.4 / 9.8 | 65.3 | **×1.20** | 2.80 / 2.35 / 2.08 | 67% | income FAIL |
| BW +1 + 1 Secret | 0.00 / +0.17 / +0.28 | 21.8 / 16.8 / 12.5 | 58.8 | **×1.21** | **3.02 / 2.62** / 2.37 | 65% | income and Green FAIL |
| BW +1 + Gray F1 clean | −0.12 / +0.02 / −0.05 | 23.1 / 16.4 / 12.8 | 59.0 | **×1.27** | 2.16 / 1.84 / 1.64 | 65% | income FAIL |
| Gray F1 clean (2 ⚠) | −0.42 / −0.39 / −0.51 | 17.1 / 11.9 / 7.4 | 64.0 | ×1.08 | 1.78 / 1.47 / 1.30 | 57% | pacing short |
| Gray F1 + F2 clean (1 ⚠) | −0.33 / −0.19 / −0.37 | 17.5 / 11.8 / 8.4 | 62.5 | ×1.08 | 1.44 / **1.23** / **1.04** | 57% | Green below band at 4P |
| Gray clean faces +1 (`up` / `up2`) | about −0.5 | 15 / 11–14 / 8 | 62–68 | — | about −0.2 | 55% | weak lever |
| Gray in Current graduates free | −0.21 / −0.32 / −0.36 | 25.4 / 17.8 / 14.0 | 63.2 | **×1.47** | **3.73 / 3.06 / 2.66** | 84% | FAIL |
| Purchases enter Current (against the ruling) | −0.52 / −0.50 / −0.41 | 15.2 / 10.2 / 8.2 | 65.9 | ×1.03 | 2.34 / 2.00 / 1.83 | 54% | weak; breaks the ruling |
| *Control:* no Sprint Plan, Gray don't use BW | −0.30 / −0.46 / −0.37 | 22.7 / 15.6 / 12.2 | 66.5 | ×1.59 | 4.08 / 3.28 / 2.87 | 99% | FAIL (simpler rule, worse) |

**Notes:**
- **+1 Secret** works as a buffer. It does not restore the per-round economy (Secret faces stay at 0.53 per round), so Singularity recovers only partly. Singularity needs survival into `v3.0`. The direct Singularity lever is still `v3.0` track capacity (v0.46 report §8.3 item 3). It was not modelled here.
- **The combo**:
  - Collapse rises 2.5–3.7 pp (4P 26.2%).
  - Patient Zero + Collapse stays under the restated D1 guardrail: 4P is 89.6 against 95.5.
  - Company spread is 19.5 / 14.2 / 15.2 pp, about the same as BASE.
  - White Hat spread at 2P / 3P is 13.6 / 13.3 pp, up 3–4 pp; watch it.
- Every lever keeps Gray rotation at 55% or more, except "purchases enter Current" (54%).

## 4. Edge cases and degenerate strategies (Ask 3)

1. **Indefinite stranding when Current > BW.**
   - **When it can happen:** leftovers all become Current, so a die can be passed over again only while Current > BW every round. That needs Current − BW + Next ≥ BW, i.e. more than about 2 × BW dice in the Sprint Plan.
   - **Observed:** Current > BW in 15–17% of player-rounds. The longest Gray run is 8 rounds and the longest colored run is 4. It is rare, late-game, and it is the intended "leave behind" choice.
   - **Backup rule (not modelled):** if a playtest shows it is abused, leftover Current dice stay Current and Next dice join only when Current is empty. Then every Current die graduates within ⌈|Current| / BW⌉ rounds.
2. **Deliberately small or no purchases.** No degenerate line.
   - Purchased dice wait in Next and never displace a Current die, so buying cannot hurt throughput.
   - Not buying leaves your roll pool Gray-heavy, which is strictly worse.
   - Rolling Secret faces frees bandwidth, so the incentive to keep Secret faces gets slightly stronger, which is fine.
3. **Gray Legacy dice become a debt.**
   - Each owned Gray takes a Release Bandwidth slot most rounds. The **Level 1 Breakthroughs ("gain 1 Gray Legacy die")** therefore turn from small gifts into small costs. You can't skip L1 to reach L2.
   - This is thematic: legacy code you must keep shipping. Bots still take L1, so the effect is in the numbers.
   - **Decision for the User:** keep it, or make the Breakthrough Gray optional.
4. **Burn Notice (Spook).** Its value rises: it permanently frees a Release Bandwidth slot.
   - Spook at 4P goes 28 → 33%.
   - The sim's `spook_gray_dice_burned` counter is not populated, so the senior engineer should wire it before sign-off.
5. **Triage L4 capstone.**
   - Its value rises: it converts a Gray that consumes bandwidth into a colored die that goes straight to Ready.
   - **Suggested wording:** "from your Ready for Release Zone, Sprint Plan (either sprint) or Research & Development".
6. **Release L4 set-gray-face.** Slightly more valuable, because Gray is rolled 1.7× as often. There is no rules interaction.
7. **Blue Signature Attack.**
   - Suggested wording: "1 Gray from your Sprint Plan (either sprint, your choice), else In Production, else Ready".
   - The cost is unchanged: the Gray blocks the oldest-first Triage queue. When it leaves R&D, it enters the Next Sprint.
8. **G3 Live Reboot.**
   - Suggestion: **either sprint**. In practice it fast-tracks a Next die, which is its strongest and most thematic use.
   - Taking a Current die frees a slot for Next in Phase 6, so the throughput is the same either way.
   - If G3 empties the Current Sprint in Phase 3, the Phase 6 Production Return goes to Current. That is consistent with the rule.
9. **Logistics Bounty (Operator).**
   - Suggestion: count colors across the **whole Sprint Plan**.
   - Operator is 2–3 pp lower at 2P and 4P; watch it. Fewer Gray pile up in the Sprint Plan by Phase 3.
10. **Jumper Diagnostics, Magnetic Splice.** Jumper's +1 BW counts toward the forced cap, so the rule text should say "effective Release Bandwidth". Splice still bypasses to Ready. Both gain a little value; no wording risk.
11. **Singularity / Final Round / Total Wipeout.** No interaction, because Phases 3–6 are skipped. One text fix: "no Secrets leave Research & Development". The last tiebreak ("fewest dice Under Development") counts both sprints.
12. **Corruption "return X colored dice".** A returned Current die may empty the Current Sprint. That is consistent with the rule.
13. **Interaction with the in-flight locked-⚠ proposal** (colored dice locked on ⚠ / Secret faces):
    - **Complementary:** more Secret faces locked means more R&D occupancy and more spare bandwidth for Next. That pulls the main loss channel (§2.2) the other way.
    - **Risk:** colored ⚠ becomes forced while the Sprint Plan forces Gray into the pool. If that proposal also locks **Gray** ⚠, the forced Vulnerability gets close to the User's "no dead-turn" preference.
    - **Plan:** sweep the two together before locking either `[TUNE]`.

## 5. Terminology (Ask 4)

### 5.1 New terms, after User confirmation (GLOSSARY §3 and §5)

| New term | Replaces |
|:---|:---|
| **Sprint Plan** (Zone 3 sub-zone) | *Scanned Box* |
| **Current Sprint**, **Next Sprint** (its two areas) | — |
| **Research & Development** (Zone 3 sub-zone) | *Processing Box* |
| **R&D face** | *Secret face* (the face only; the resource **Corporate Secrets** is unchanged) |

### 5.2 Retire to GLOSSARY §7 and the CLAUDE.md / AGENTS.md lists

- *Scanned Box*
- *Processing Box*
- *Secret face*
- *Scanned Graduation*, if it is renamed

### 5.3 Clashes and new names the User needs to confirm

1. **The "Terminal Hardware & R&D Upgrade Tracks" heading** (RULES §2, GLOSSARY *Company Terminal Mat*). Proposal: **Terminal Hardware Tracks**. It is already canonical in the GLOSSARY §4 heading and in RULES Phase 5 ("Terminal Hardware Track Upgrades"), so it adds no new term.
2. ***Deep R&D Vault* (B2).** It is a Blue ★ face in In Production, but it would now read as "a vault in R&D".
   - Option a: keep it as flavor.
   - Option b: rename it. *Deep Data Vault* is a new term and needs approval.
   - Recommendation: b.
3. **"R&D face" yields Secrets, not 🔬.** New players will expect Research. Consider a reminder line on the PnP face legend.
4. **The step name "Scanned Graduation".** It needs a replacement.
   - Option a: plain **Graduation**. No new term; recommended.
   - Option b: **Sprint Review**. A new term.
5. **"Secret Face Yields" heading** → **R&D Face Yields**.
6. **The `{SECRET}` icon.** Keep it; it shows the Corporate Secret it yields.

### 5.4 Files and areas to update

| Area | What changes |
|:---|:---|
| **RULES.md** | §2 mat bullets, Hardware Throughput Limits, track table (Release Bandwidth wording, PR L3 "to Next Sprint"), ASCII wireframe; Gray / Purple die bullets ("Secret face"); §4 Phase 1 rerolls and lock-in "→ Processing Box"; Phase 2 Singularity text; Phase 3 G3 and Logistics Bounty; Phase 4 Blue Signature Attack; Phase 5 PR L3, Triage L4 and Purchase "→ Scanned Box"; Phase 6 steps 1–4 (new Production Return / Graduation / Triage text), Secret Face Yields; §5 tiebreak wording |
| **RULES_QUICKREF.md** | 6 "Scanned", 4 "Processing" and the Phase 6 summary |
| **GLOSSARY.md** | Rows: *Under Development Pipeline*, *Processing Box*, *Scanned Box*, *Secret face*, *Triage / Release Track & Bandwidth*, *Phase 6*, *Company Terminal Mat*, *Logistics Bounty*, *Magnetic Splice*, *Blue Dice* and other face rows, *Total Data Breach* (Deep R&D Vault); §7 Retired Terms |
| **RULES_APPENDIX.md** | 8 "Secret face" references in the die tables, G3, Operator, Blue Signature Attack |
| **pnp/generate_pnp.py** | About 35 strings. **Mat layout:** box 4A must split into Current / Next (lines ~1105–1160), box 4C is renamed. Face legends, Phase 6 card, PR L3 strip, Purchase line |
| **tts/** | Rebuild with `python3 -m tts.build_tts`; `global.lua` is unaffected. Version bump to v0.47.0 across the CLAUDE.md list |
| **web/** | `static/js/components/{player_mats,action_dock,compiler,market}.js`, `state.js`, `api.js`; `controller/{phase6_pipeline_actions,phase1_actions,phase5_operations_actions,core}.py`; `schemas.py`; `server.py`. Two Sprint drop zones; the forced-graduation UI |
| **sim/** | Keep the internal identifiers. Precedent: `glitched_dice` = Processing Box. `scanned_dice` (84 uses), `graduate_scanned`, `production_return_to_scanned`, `choose_scanned_graduates`, `purchased_dice_to_scanned`, `pr_l3_purple_to_scanned`, `held_in_scanned`. Rename only user-facing strings (`phase3_income` star notes, face names in `entities.py`, `secret_faces.py` docstrings) |
| **CLAUDE.md / AGENTS.md** | The pillar "Dice = Software Modules…" names Processing / Scanned Box and "Secret face", plus the deprecated list. Needs User approval (as with D7) |
| **PLAN.md, FINDINGS.md** | New phase and new section |

## 6. Implementation plan for the SDLC chain (Ask 5)

### 6.1 Spec items (principal-engineer)

1. **Config:**
   - `sprint_plan_enabled: bool = False`.
   - `sprint_graduation_reading: "PRIORITY" | "STRICT"` (default PRIORITY; STRICT is for sweeps only).
   - Preset `GameConfig.v047()` = `v046()` + Sprint Plan + `starting_secrets_by_player_count = V047_STARTING_SECRETS {2: 6, 3: 6, 4: 6}`.
   - Optional `gray_face_profile = "V047_SPRINT"` (F1 without ⚠) behind the combo decision.
2. **State:**
   - `PlayerState.current_sprint_ids: Set[int]`.
   - A die in `scanned_dice` whose id is not in the set is in the **Next Sprint** by default. Every entry path except Production Return then needs no code: Triage, B3, purchases, Prometheus, PR L3, Blue Signature Attack.
   - Helpers: `current_sprint(p)` and `next_sprint(p)`. Both filter by the ids currently in `scanned_dice`, so removal paths (G3, Burn Notice, corruption returns, Triage L4, Blue Signature Attack) stay correct.
   - `fast_clone` must copy the set (test this).
3. **Production Return** (`production_return_to_scanned`): if `current_sprint(p)` is empty, add the returned ids to `current_sprint_ids`.
4. **Graduation** (`graduate_scanned`):
   - Forced: `min(|Current|, effective BW)` Current dice, chosen by the bot.
   - If `|Current| < BW`: 0..(BW − |Current|) Next dice, optional.
   - Afterwards: `current_sprint_ids = ids(scanned_dice)`.
   - New bot hook `choose_sprint_graduates(p, current, next, bw, state) -> (cur_ids, next_ids)`. Its default is today's priority; it falls back to `choose_scanned_graduates`.
5. **Rules-text rulings to encode:** G3 either sprint; Logistics Bounty counts the whole Sprint Plan; Triage L4 and Blue Signature Attack take from either sprint (player's choice); Jumper counts toward the forced cap.
6. **Telemetry:**
   - Per player-round: Current size, Next size, Current > BW, graduates by sprint, Gray roll share, wait-histogram by color class.
   - Gray ⚠ vs colored ⚠ split at lock-in.
   - Wire `spook_gray_dice_burned`.
   - Add a seat-level `secrets_by_source` aggregate to the sweep summary.

### 6.2 Invariants and tests (senior-engineer, reviewed by staff-engineer)

- **INV-SPRINT-01:** after Graduation, `current_sprint_ids == ids(scanned_dice)`.
- **INV-SPRINT-02:** Production Return goes to Current if and only if Current was empty.
- **INV-SPRINT-03:** graduates ⊇ `min(|Cur|, BW)` Current dice; Next dice appear only when `|Cur| < BW`; total ≤ BW.
- **INV-SPRINT-04:** every non-Production entry lands in Next. Parametrize over Triage, B3, purchase, Prometheus, PR L3 and Blue Signature Attack.
- **INV-SPRINT-05:** `current_sprint_ids ⊆ ids(scanned_dice)` at every phase boundary.
- **Parity:** with the flag off, the game is bit-identical to v0.46 on the v0.35 / v0.46 parity seeds.
- **Other tests:** a `fast_clone` round-trip; web controller tests for forced picks and the 400 error on illegal Next picks.

### 6.3 Sweep arms (product-owner; 1,200 per pod, 2P / 3P / 4P, seeds `42..1241`, plus the per-card split)

| Arm | Purpose |
|:---|:---|
| S0 | `v046` (control) |
| S1 | Sprint PRIORITY, no lever |
| S2 | S1 + 6 starting Secrets (**recommended**) |
| S3 | S2 + Gray `V047_SPRINT` (combo) |
| S4 | S1 + BW +1 (expected to fail income; confirms §3) |
| S5 | Sprint STRICT (informative) |

Then:
- the dominance matrix (KeepAll / RerollAllVuln / PenTestRush against Adaptive, 600 per cell) on the chosen arm;
- ref1 under the D5 bar;
- a joint arm with the locked-⚠ proposal once that branch lands.

Guardrails come from v0.46 report §8.2, plus:
- Gray roll share ≥ 50%;
- longest stranding run ≤ 8;
- White Hat spread ≤ 12 pp.

### 6.4 Decisions for the User

1. Lever: +1 Secret alone, or +1 Secret + Gray F1 clean (pillar text change)?
2. Accept Singularity at about 55% (single lever) or 62–76% (combo) of v0.46, or open a `v3.0` capacity lever?
3. Rulings in §4 items 5 and 7–10 (either-sprint wording).
4. Keep the L1 Breakthrough Gray as mandatory "legacy debt", or make it optional?
5. Terms: *Terminal Hardware Tracks*; *Deep R&D Vault* rename; *Graduation* or *Sprint Review*; approval of the five new terms and four retirements; the CLAUDE.md / AGENTS.md pillar edits.
6. The stranding backup rule (§4 item 1): keep it in reserve for playtest?

## 7. Locked Gray follow-up

**Date:** 2026-11-19. **User decisions applied:** Gray dice have 1 ⚠ face, on Face 3 (`+$2 / +2 🔬`), and Faces 1 and 2 are clean. Any die showing a ⚠ face is locked and can't be rerolled; Helix *Brute-Force Bypass*, Release L4 set-Gray-face and Prodigy ACE can still change it. Starting Corporate Secrets `6`. Sprint Plan priority reading (arm `A`). Renames: *Deep Data Vault*, Phase 6 **Sprint Review**.

### 7.1 Method

- **Probe:** `/tmp/claude-1000/-home-mike-antigravity-rogue-agent--claude-worktrees-scanned-box-sprint-plan-dc5f20/59928f72-1253-405a-809e-daadc89559d6/scratchpad/sprint_probe3.py` (probe2 plus `LOCK`, `PROFILE` and `BTDEC`). Grids: `grid5.sh` and `grid6.sh` in the same folder.
- **The lock is a monkeypatch in this probe.** Branch `claude/vulnerability-dice-risk-reward-4668d8` has no sim support committed; it has only an uncommitted probe. I read that probe and used the same hook: a wrapper on `vulnerability_policy.adjust_rerolls` drops any die whose current face has ⚠. Helix stays exempt, read from the caller's `helix_active`. Release L4 and Prodigy ACE resolve after rerolls, so they are untouched.
- **Sample and pairing:** 1,200 games per pod, seeds `42..1241`, `mixed1` roster. Every arm is paired against BASE v0.46, which reproduces 8.20 / 7.77 / 7.51 rounds. L0 reproduces §3. Noise is about ±0.25 rounds and ±3 pp on end shares.
- **Income** uses the §1 proxy, restated as ×v0.45 (= 1.08 × the ratio to v0.46). The guardrail is ×1.25.
- **L4 decline rule (bots):** decline a Level 1 Breakthrough Gray die (Pen Test, Triage or Release) when Scanned + In Production ≥ effective Release Bandwidth, i.e. when the next Sprint Review is already full. `L4x` declines every time.

### 7.2 Headline (2P / 3P / 4P)

| Arm | Δ rounds | Singularity % (share of v0.46) | PZ + Collapse (4P ≤ 95.5) | Wipeout (≤ 15 / 5 / 2) | Income ×v0.45 (≤ 1.25) | Green lost (1.2–2.5) |
|:---|:---|:---|:---|:---|:---|:---|
| BASE v0.46 | 0 | 27.2 / 20.8 / 16.1 | 72.8 / 79.2 / 83.9 | 5.1 / 1.4 / 0.1 | 1.08 | 2.42 / 2.08 / 1.86 |
| L0 Sprint + 6 | −0.26 / −0.10 / −0.10 | 15.3 / 11.3 / 8.0 (54%) | 84.7 / 88.7 / 92.0 | 7.8 / 2.8 / 0.4 | 1.12 | 2.52 / 2.18 / 1.93 |
| *ref:* L0 + Gray 1⚠, no lock | +0.06 / +0.43 / +0.32 | 20.6 / 15.8 / 11.5 (75%) | 79.4 / 84.2 / 88.5 | 4.8 / 1.8 / 0.3 | 1.17 | 1.53 / 1.35 / **1.19** |
| **L1** Gray 1⚠ locked | **−0.17 / +0.18 / +0.17** | **17.2 / 13.9 / 9.2 (63%)** | 82.8 / 86.1 / 90.8 | 7.8 / 1.8 / 0.8 | 1.23 (edge) | 2.01 / 1.80 / 1.61 |
| L2 unified lock, NOPREMIUM | −0.50 / −0.34 / −0.28 | 11.4 / 7.7 / 6.3 (39%) | 88.6 / 92.3 / 93.7 | 9.7 / 2.9 / 0.9 | 1.22–1.23 (edge) | **2.65** / 2.32 / 2.07 |
| L3 unified lock, V046_VULN | −0.48 / −0.28 / −0.18 | 11.4 / 8.2 / 7.1 (42%) | 88.6 / 91.8 / 92.9 | 9.1 / 2.8 / 0.7 | **1.37–1.38 FAIL** | **2.60** / 2.31 / 2.08 |
| L4 = L2 + optional L1 Gray (bind-aware) | −0.45 / −0.24 / −0.18 | 13.8 / 9.6 / 7.8 (48%) | 86.2 / 90.4 / 92.2 | 11.0 / 2.2 / 0.6 | 1.08 | **2.62** / 2.35 / 2.11 |
| *residual:* L2 + 7 Secrets | −0.12 / +0.20 / +0.22 | 14.4 / 10.7 / 8.4 (52%) | 85.6 / 89.2 / 91.6 | 10.2 / 3.2 / 0.8 | 1.22–1.23 (edge) | **2.80** / 2.50 / 2.25 |

### 7.3 Dice, ⚠ and Vulnerability (3P per player-round; 2P and 4P within ±0.03)

| | BASE | L0 | L1 | L2 | L3 | L4 |
|:---|---:|---:|---:|---:|---:|---:|
| Gray rolled / colored rolled | 1.38 / 3.41 | 2.27 / 2.60 | 2.31 / 2.63 | 2.32 / 2.60 | 2.33 / 2.64 | 1.70 / 2.83 |
| Gray roll share (owned Gray in Ready) | 33% | 57% | 56% | 57% | 56% | 68% |
| Kept Gray ⚠ | 0.52 | 0.86 | 0.62 | 0.63 | 0.63 | 0.48 |
| Kept colored ⚠ | 1.14 | 0.88 | 0.88 | 1.31 | 1.34 | 1.43 |
| Locked: rerolls blocked, Gray / colored | — | — | 0.79 / 0 | 0.76 / 1.00 | 0.76 / 1.07 | 0.56 / 1.07 |
| Secret faces locked in | 0.65 | 0.53 | 0.54 | **0.49** | 0.50 | 0.53 |
| Lock-in Vulnerability per seat-game | 12.9 | 13.4 | 11.9 | 14.4 | 14.7 | 14.4 |
| Reroll decisions with nothing left to reroll | 11% | 9% | 16% | 23% | 23% | 25% |
| Final Secrets per seat | 8.05 | 6.53 | 7.08 | 5.80 | 5.97 | 6.40 |

- Corruption and Target Lock Vulnerability stay flat (about 1.1 and 0.1–0.3 per seat-game). All of the change comes from lock-in.
- **When it can, a bot rerolls Gray F3 85% of the time**, because it pays only 1–2 more than a clean Gray face. The Gray lock therefore bites: it forces a kept `+$2 / +2 🔬` and +1 Vulnerability on 1 roll in 6.
- **The colored lock costs Secret faces.** A core ⚠ face that is locked can no longer be rerolled toward the Secret face, so Secret faces fall 0.54 → 0.49. This, plus more Green, is why L2 is shorter than L1 even though income is the same.

### 7.4 Dead-turn check (the User rejects income denial)

Share of player-rounds with Phase 3 income ($ + 🔬) ≤ 1 / ≤ 2:

| BASE | L0 | L1 | L2 | L3 | L4 |
|:---|:---|:---|:---|:---|:---|
| 2.3 / 7.0% | 0.8 / 3.5% | 0.7 / 2.5% | 0.5 / 2.2% | 0.4 / 1.5% | 1.0 / 4.3% |

- **No arm creates dead turns.** A locked face still pays, and the locked faces are high-output ones, so low-income rounds become rarer.
- The cost of a lock is paid in Vulnerability, and later in Green Secrets lost. It is never paid in income.
- The only "empty" outcome is a reroll step with nothing left to reroll: 16% (L1) and 23% (L2) of decisions, against 11% today. That is a lost choice, not lost income.

### 7.5 Win-rate spread (pp, max − min; 2P / 3P / 4P)

| | BASE | L0 | L1 | L2 | L3 | L4 |
|:---|:---|:---|:---|:---|:---|:---|
| Bot | 10.5 / 18.0 / 10.7 | 4.9 / 16.1 / 10.4 | 14.0 / 18.0 / 11.6 | 20.3 / 14.9 / 13.7 | 16.6 / 16.1 / 13.5 | 14.1 / 17.0 / 9.0 |
| Company | 19.2 / 17.8 / 15.7 | 19.6 / 19.1 / 16.5 | 22.1 / 13.8 / 17.2 | 15.0 / 14.2 / 18.7 | 19.1 / 19.3 / 22.0 | 20.3 / 17.9 / 19.8 |
| White Hat | 10.1 / 9.0 / 8.1 | 9.4 / 8.9 / 13.1 | **7.3 / 5.5 / 5.2** | 9.7 / 6.7 / 9.2 | 8.0 / 6.8 / 3.0 | 8.1 / 7.2 / 4.0 |

- **Bots:** under both locks, Accelerationist leads (L1 3P 45%, L2 2P 58%). SecOpsTurtle and Reckless trail (L2 2P 41 / 38%).
- **Companies:** Aegis still leads and Helix still trails in every arm (L2 4P Helix 15%). This is the v0.47 company-pass item, and the lock does not change it. Helix keeps *Brute-Force Bypass* as its only way to reroll a locked die; the lock does not visibly help it.
- **White Hats:** L1 has the tightest spread of any arm.

### 7.6 Is a Level 1 Breakthrough Gray die worth taking under Sprint Plan? (L4 data; no ruling proposed)

- **How often bots decline:** about 2.75 Level 1 Gray dice are offered per seat-game. Release Bandwidth would already be binding in 77–78% of those offers, so the bind-aware bot declines 77–78%. Gray roll share then rises to 68% and the longest Gray stranding run falls from 8 to 5–6 rounds.
- **Whole-table effect, every seat bind-aware (L4 vs L2):** +0.05 / +0.10 / +0.10 rounds and +0.47 / +0.60 / +0.50 Secrets per seat. Income drops ×1.13 → ×1.00 of v0.46. Green Secrets lost is flat.
- **Marginal value for one seat (seat 0 declines; everyone else takes; paired seeds):**

| Seat 0 policy | 2P win / Secrets | 3P | 4P |
|:---|:---|:---|:---|
| L2, takes every Gray | 53.3% / 5.96 | 33.5% / 5.90 | 25.5% / 6.40 |
| L2, bind-aware decline | 55.3% / 6.38 | 34.7% / 6.20 | 31.0% / 6.97 |
| L2, always declines | 55.0% / 6.62 | 34.2% / 6.18 | 30.5% / 7.12 |
| L1, takes every Gray | 53.9% / 7.60 | 35.3% / 7.17 | 24.9% / 7.31 |
| L1, always declines | 54.7% / 8.31 | 37.4% / 7.86 | 29.3% / 8.17 |

- **Under Sprint Plan, a Level 1 Gray die has zero to negative value for these bots:**
  - Declining it is worth +0.3 to +0.9 Secrets per seat.
  - In win rate it is worth +1 to +2 pp at 2P / 3P, which is noise, and **+4 to +5.5 pp at 4P**, which is about 3 SE.
  - The mechanism: each Gray die takes a Release Bandwidth slot from a colored die about every other round (§2.3), and it now brings a locked ⚠ on 1 face in 6.
- **If the die becomes optional:** declining becomes the near-dominant line once a player owns a purchased die. The decision itself would be shallow, since "decline unless your Sprint Plan has room" is almost always right.
- **If it stays mandatory:** it is a small tax, worth up to about 5 pp at 4P.

### 7.7 Is Gray a decision or a tax?

- **In the roll:** with 1 ⚠ and the lock, Gray offers no reroll choice on F3. Otherwise it plays like v0.46, where 80% of Gray ⚠ faces were rerolled when possible. The only Gray roll decision left is whether to reroll the five clean faces, which pay little, and bots rarely do.
- **At Sprint Review:** Gray is a real decision. It competes for Release Bandwidth in about two thirds of player-rounds (§2.6).
- **At research:** if the Level 1 Gray die stays mandatory, it is a mild tax (§7.6).
- **Net:** Gray is a pipeline-management decision, not a roll decision. This was already true under Sprint Plan, and the lock does not change it.

### 7.8 Recommendation

- **Recommend L1 (Gray 1⚠ on F3, locked; colored dice not locked; 6 Secrets).**
  - It is the only arm that passes every guardrail.
  - Rounds come within −0.17 to +0.18 of v0.46.
  - Singularity recovers to 58–67% of v0.46, against 54% for L0.
  - Green lost is 2.01 / 1.80 / 1.61, mid-band. Without the lock, 4P falls out of band at 1.19, so the Gray lock is what keeps Green in band.
  - PZ + Collapse at 4P is 90.8, under 95.5.
  - It has the tightest White Hat spread of any arm.
  - **Watch:** income is ×1.23 of v0.45, 0.02 under the guardrail on the proxy. Confirm it with method (b) in the SDLC sweep.
- **L2 (unified lock) fails as it stands:**
  - 2P Green lost is 2.65, above the 2.5 band.
  - Rounds fall 0.3–0.5.
  - Singularity falls to 39% of v0.46.
  - **Residual tuning:** 7 Secrets fixes pacing (−0.12 / +0.20 / +0.22) but pushes 2P Green to 2.80 and 3P to 2.50. A unified rule would also need a 2P Green lever, such as the 2P Green cube count. That was not modelled.
- **L3 fails income** (×1.37–1.38), as D6 predicted.
- **If the User wants one unified sentence for the rulebook:** adopt L1 now and keep the colored half on the 4668d8 branch. Re-test it there with 2P Green tuning.

## 8. Starting pool and Gray thinning

**Date:** 2026-11-19.

**Base for every arm:** §7 L1. That is Sprint Plan (priority reading), Gray with 1 ⚠ on F3, Gray locked, colored dice not locked, and 6 Secrets unless the arm says otherwise.

**User direction:**
- The Level 1 "gain 1 Gray Legacy die" Breakthroughs on Pen Test, Triage and Release are removed.
- New setup: Ready for Release = 2 Gray + Purple + company die. Current Sprint = 3 Gray. Round 1's Sprint Review takes those 3 Gray first.
- Thinning uses the existing wording: "return 1 Gray Legacy die you own to the box". No new terms are needed.

### 8.1 Method

- **Probe:** `/tmp/claude-1000/-home-mike-antigravity-rogue-agent--claude-worktrees-scanned-box-sprint-plan-dc5f20/59928f72-1253-405a-809e-daadc89559d6/scratchpad/sprint_probe4.py`. Grids: `grid7.sh` and `grid8.sh`.
- **Probe settings:** `START7` puts 3 Gray in the Current Sprint at setup. `L1R` sets each track's Level 1 reward. `S0` runs the seat-0 probes.
- **Pairing:** 1,200 games per pod, seeds `42..1241`, paired against BASE v0.46 and against L1.
- **Thinning bot:** a bot always thins when it reaches the space. It returns the Gray furthest from rolling, in this order: Processing Box, Next Sprint, In Production, Current Sprint, Ready.
- **Limitation:** bots do not value thinning when they choose which research to buy.
- **Arm names:**
  - P1a / P1b / P1c: Release L1 thins; Pen Test L1 and Triage L1 each give `+$3`, `+1 🔬` or `+1 Secret`.
  - P2a / P2b / P2c: Release L1 and Pen Test L1 both thin; Triage L1 gives `+$3`, `+1 🔬` or `+1 Secret`.

### 8.2 Guardrails (2P / 3P / 4P)

| Arm | Δ rounds vs v0.46 | Singularity vs v0.46 | Income ×v0.45 (≤ 1.25) | Green lost | 4P PZ + Collapse (≤ 95.5) |
|:---|:---|:---|:---|:---|:---|
| L1 (§7) | −0.17 / +0.18 / +0.17 | 63 / 67 / 58% | 1.23 | 2.01 / 1.80 / 1.61 | 90.8 |
| P0 (7-die start, no Level 1 reward) | −0.43 / −0.12 / −0.14 | 53 / 58 / 44% | 1.15 | 1.83 / 1.61 / 1.44 | 92.9 |
| P1a (Release thins; Pen Test and Triage +$3) | −0.15 / +0.16 / +0.10 | 72 / 89 / 73% | 1.13 | 1.95 / 1.73 / 1.53 | 88.3 |
| P1b (Pen Test and Triage +1 🔬) | −0.23 / −0.02 / −0.07 | 67 / 66 / 55% | 1.15 | 1.86 / 1.62 / 1.46 | 91.1 |
| P1c (Pen Test and Triage +1 Secret) | +0.27 / +0.80 / +0.77 | 82 / 96 / 95% | 1.15 | 2.03 / 1.87 / 1.68 | 84.7 |
| **P2a (Release and Pen Test thin; Triage +$3)** | **−0.10 / +0.17 / +0.17** | **78 / 86 / 82%** | **1.12** | 1.97 / 1.74 / 1.56 | **86.8** |
| P2b (Triage +1 🔬) | −0.15 / +0.08 / +0.06 | 73 / 77 / 68% | 1.13 | 1.90 / 1.65 / 1.51 | 89.0 |
| P2c (Triage +1 Secret) | +0.15 / +0.60 / +0.67 | 81 / 96 / 95% | 1.13 | 1.99 / 1.83 / 1.67 | 84.8 |
| P2a, 5 Secrets | −0.71 / −0.51 / −0.62 | 60 / 68 / 60% | 1.11 | 1.79 / 1.55 / 1.37 | 90.4 |
| P2a, 7 Secrets | +0.25 / +0.68 / +0.68 | 90 / 102 / 104% | 1.12 | 2.05 / 1.88 / 1.68 | 83.3 |
| P2c, 5 Secrets | −0.22 / +0.08 / +0.10 | 71 / 76 / 75% | 1.12 | 1.88 / 1.69 / 1.53 | 87.9 |
| *P2a, Current Sprint = 2 Gray (4 Gray total)* | +0.30 / +0.48 / +0.45 | 99 / 108 / 104% | 1.07 | 2.10 / 1.83 / 1.68 | 83.2 |
| *the same, 5 Secrets* | −0.14 / −0.22 / −0.19 | 84 / 80 / 87% | 1.06 | 1.97 / 1.65 / 1.51 | 86.1 |

- **Every arm passes income.** Thinning removes Gray payouts, so income falls back from the L1 edge (×1.23) to ×1.12–1.15.
- **Total Wipeout** stays at or under 8.5 / 3.4 / 0.9%, inside the 15 / 5 / 2 guardrail.
- **P0 alone is too short:** −0.3 rounds against L1. Without the Level 1 Gray dice there is nothing to offset the larger start pool.
- **A Level 1 reward of +1 Secret overshoots at 6 Secrets.** At 5 Secrets it gives about the same result as P2a with +$3.

### 8.3 Owned Gray, Gray roll share, and early income (3P; 2P and 4P within ±0.2)

| Owned Gray at Sprint Review, R1 → R8 | Gray roll share | Gray rolled per round |
|:---|---:|---:|
| BASE: 2.9, 3.5, 3.7, 3.9, 4.1, 4.2, 4.3, 4.3 | 33% | 1.38 |
| L1: 3.0, 3.6, 3.8, 4.3, 4.5, 4.6, 4.6, 4.6 | 56% | 2.31 |
| P0: 5.0, 4.8, 4.7, 4.6, 4.5, 4.5, 4.5, 4.5 | 48% | 2.20 |
| P1a: 5.0, 4.4, 4.1, 3.8, 3.6, 3.5, 3.5, 3.5 | 48% | 1.92 |
| P2a: 5.0, 4.2, 3.7, 3.2, 2.8, 2.6, 2.6, 2.5 | 52% | 1.80 |

| 3P | Phase 3 cash, R1–4 | Phase 3 🔬, R1–4 | Secret faces per player-round, R1–4 / R5–8 |
|:---|---:|---:|:---|
| BASE | 11.4 | 12.0 | 0.57 / 0.74 |
| L1 | 10.6 | 15.1 | 0.51 / 0.58 |
| P0 | 9.6 | 14.4 | 0.44 / 0.55 |
| P2a | 9.8 (+$3 from Triage L1 = 12.8) | 13.8 | 0.46 / 0.66 |

- **Early cash does not rise from the dice. Early 🔬 does.**
  - Bots take the Gray choice faces as 🔬. Phase 3 cash in R1–4 falls by $1.6 against BASE, and 🔬 rises by 1.8.
  - Under P2a the only early cash gain is the Triage L1 `+$3`. Bots reach Triage L1 in Round 1 (mean 1.03), so it works almost as `+$3` at setup.
- **The Round 2 dip comes from the Sprint Plan holding the company die back.**
  - Round 2 rolls 3 Gray + Purple, because the company die waits in the Next Sprint.
  - Secret faces in Round 2 fall to 0.27, against 0.51 in BASE.
  - Total $ + 🔬 in Round 2 is 6.0, against BASE's 6.2. There is no dead turn: rounds with income ≤ 1 stay under 1.5% in every arm.
- **Late game:** under P2a, thinning brings Secret faces back to 0.66 per round in R5–8.

### 8.4 Thinning: how often, how much, and is Gray break-even?

- **How often bots thin:** P1 thins 0.94–0.98 times per seat-game; P2 thins 1.80–1.90.
  - Bots reach Release L1 at mean round 3.2 and Pen Test L1 at mean round 3.9, the same as P0. Bots do not rush it, but they are not choosing for it (§8.1).
- **Total thinning available (P2a, per seat-game):**
  - Level 1 thinning: 1.82.
  - Triage L4 swap: 0.38.
  - Spook *Burn Notice*: 0.28–0.51 per game, on the Spook seat only.
  - About 2.3 of the 5 Gray in total. The late pool settles at about 2.5 Gray, against BASE's 4.3, while the Gray roll share stays 52% (BASE 33%).
- **Seat 0 alone changes policy (P2a; paired seeds):**

| Seat 0 change | Win rate 2P / 3P / 4P | Secrets per seat-game |
|:---|:---|:---|
| P2a reference | 51.2 / 35.0 / 25.7% | 7.62 / 7.52 / 7.55 |
| Skips both thinnings (about 1.8 actions) | −5.8 / −8.2 / −5.3 pp | −0.81 / −1.17 / −0.82 |
| P1a: skips its one thinning | −3.2 / −2.5 / −2.1 pp | −0.37 / −0.53 / −0.28 |
| Starts with 1 fewer Gray (2 in the Current Sprint) | **+8.0 / +4.3 / +6.0 pp** | **+1.71 / +0.96 / +1.02** |
| Starts with 1 more Gray (4 in the Current Sprint) | −7.0 / −5.1 / −4.8 pp | −0.90 / −1.10 / −1.00 |

- **"Break-even" does not hold.** Under Sprint Plan with Release Bandwidth binding, each Gray a player owns costs about 1 Secret and 5 pp of win rate. That is because it takes a Release Bandwidth slot from a colored die.
- **Value of one thinning:** about +0.4 to +0.6 Secrets and +2 to +4 pp.
- **Thinning is a strong space.** A player who knows this will race to Release L1 and Pen Test L1. Each costs only `1 🔬`, so a race is cheap and over by Round 2–3. It is a soft must-take, not a degenerate rush. The bots here don't race, so this is an estimate.

### 8.5 Win spreads (pp, 2P / 3P / 4P)

| | BASE | L1 | P1a | P2a |
|:---|:---|:---|:---|:---|
| Bot | 10.5 / 18.0 / 10.7 | 14.0 / 18.0 / 11.6 | 11.0 / 12.0 / 9.8 | 15.7 / 12.4 / 8.7 |
| Company | 19.2 / 17.8 / 15.7 | 22.1 / 13.8 / 17.2 | 20.3 / 12.6 / 11.5 | 23.4 / 15.5 / 16.7 |
| White Hat | 10.1 / 9.0 / 8.1 | 7.3 / 5.5 / 5.2 | 9.7 / 12.1 / 5.9 | 10.4 / 10.4 / 5.7 |
| Spook win % | 50 / 39 / 28 | 52 / 36 / 28 | 56 / 41 / 28 | 55 / 39 / 28 |
| Operator win % | 51 / 31 / 21 | 51 / 30 / 24 | 48 / 31 / 23 | 49 / 29 / 22 |

- **Spook:** no gain from having more Gray to burn. It burns 0.28–0.51 per game and stays at BASE.
- **Operator:** flat.
- **Other spreads:** the 3P bot spread tightens against BASE. The White Hat spread is about BASE, wider than L1's unusually tight 5–7. The company spread is about BASE, and Aegis and Helix still set it.

### 8.6 Recommendation

- **Recommend P2a:**
  - Release L1 and Pen Test L1 read "return 1 Gray Legacy die you own to the box".
  - Triage L1 gives `+$3`, the same wording as the Public Relations L1 Breakthrough.
  - Starting Corporate Secrets stay at 6.
  - The 7-die start (5 Gray).
- **Why P2a:**
  - It is closest to v0.46 pacing: −0.10 / +0.17 / +0.17 rounds.
  - It has the best Singularity share at 6 Secrets: 78–86%.
  - Income is ×1.12. 4P PZ + Collapse is 86.8. Green is mid-band.
  - The late Gray pool is about 2.5 and the Gray roll share stays 52%, so sprints keep their effect.
- **Lighter alternative: P1a** (Release thins; Pen Test L1 `+$3`).
  - Pacing and guardrails are about the same as P2a.
  - Company and bot spreads are tighter.
  - Singularity is lower at 4P (73%), and the late Gray pool is 3.5.
- **Starting Secrets:** 5 is too short (−0.5 to −0.7) and 7 overshoots (+0.7), so 6 stands. Use +1 Secret as the Triage reward only together with 5 starting Secrets (P2c at 5 is about P2a).
- **Residual issue: Gray is not break-even.** Each Gray still costs about 1 Secret.
  - The cleanest fix modelled is a **Current Sprint of 2 Gray (4 Gray total) with 5 Secrets**: −0.14 / −0.22 / −0.19 rounds, Singularity 80–87%, income ×1.06.
  - That breaks the "5 Gray per player" goal for the start, though not for the component count. It is the User's call.
- **Watch: the thinning race.** A seat that skips thinning loses 5–8 pp. Expect playtesters to buy Release L1 and Pen Test L1 early.

## 9. Level 3 thinning

**Date:** 2026-11-19.

**Base for every arm:**
- The 7-die start (5 Gray). Sprint Plan priority reading. Gray with 1 ⚠ on F3, locked. Colored dice not locked.
- No Level 1 Gray dice.
- Release L3 and Pen Test L3 read "return 1 Gray Legacy die you own to the box" instead of "+1 Corporate Secret".
- Pen Test L3 keeps the +3 yield on Blue Secret faces. Triage L3 keeps +1 Secret. Triage L4 and *Burn Notice* are unchanged.

### 9.1 Method

- **Probe:** `/tmp/claude-1000/-home-mike-antigravity-rogue-agent--claude-worktrees-scanned-box-sprint-plan-dc5f20/59928f72-1253-405a-809e-daadc89559d6/scratchpad/sprint_probe5.py`. Grids: `grid9.sh`, `grid10.sh` and `grid11.sh`.
- **Probe settings:**
  - `L3THIN`: swaps the L3 Secret for thinning.
  - `RUSH`: the stress bot.
    - When set, the bot's research plan buys Release up to L3, then Pen Test up to L3, before its normal want-list.
    - It respects the 2-upgrades-per-turn cap and saves toward the next step.
    - `p0`: seat 0 always rushes. `p0half`: seat 0 rushes on a seeded coin flip each round. `all`: every seat rushes.
  - `S0`: seat-0 probes. `secret`: seat 0 takes the old +1 Secret instead of thinning. `nothin`: seat 0 neither thins nor gains a Secret.
- **Pairing:** 1,200 games per pod, seeds `42..1241`, paired against BASE v0.46 and §7 L1.
- **Level 1 reward sets** (existing terms only; PR L1 stays `+$3`):

| Set | Pen Test L1 | Triage L1 | Release L1 |
|:---|:---|:---|:---|
| Q0 | — | — | — |
| QA | Lower your Vulnerability to `0` | `+$2` | `+1` Release Bandwidth this round |
| QB | Lower your Vulnerability to `0` | `+2 🔬` | `+1` Market Share |
| QC | `+1` Corporate Secret | `+$2` | `+1` Release Bandwidth this round |

"+1 Release Bandwidth this round" uses the wording of the Phreaker's *Jumper Diagnostics*. "Lower your Vulnerability to 0" is the sim's existing `pen_test_l1 = SET_ZERO` option.

### 9.2 Guardrails (2P / 3P / 4P)

| Arm | Δ rounds vs v0.46 | Singularity vs v0.46 | Income ×v0.45 (≤ 1.25) | Green lost | 4P PZ + Collapse |
|:---|:---|:---|:---|:---|:---|
| §8 P2a (thin at L1) | −0.10 / +0.17 / +0.17 | 78 / 86 / 82% | 1.12 | 1.97 / 1.74 / 1.56 | 86.8 |
| Q0 (no Level 1 reward) | −0.66 / −0.36 / −0.44 | 47 / 50 / 44% | 1.15 | 1.79 / 1.57 / 1.40 | 92.9 |
| QA | −0.34 / −0.12 / −0.19 | 61 / 63 / 65% | 1.17 | 1.69 / 1.45 / 1.29 | 89.5 |
| QB | −0.26 / −0.14 / −0.08 | 63 / 68 / 68% | 1.16 | 1.62 / 1.37 / **1.23 (edge)** | 89.1 |
| **QC** | **−0.14 / +0.14 / +0.10** | **71 / 84 / 77%** | **1.17** | **1.97 / 1.73 / 1.55** | **87.7** |
| QC, 5 Secrets | −0.71 / −0.59 / −0.62 | 57 / 61 / 57% | 1.16 | 1.82 / 1.55 / 1.37 | 90.8 |
| QC, 7 Secrets | +0.21 / +0.67 / +0.68 | 86 / 103 / 102% | 1.18 | 2.06 / 1.87 / 1.70 | 83.6 |
| QA, 7 Secrets | +0.04 / +0.44 / +0.42 | 74 / 86 / 82% | 1.18 | 1.78 / 1.58 / 1.43 | 86.8 |
| QC, every seat rushes | +0.14 / +0.60 / +0.46 | 94 / 112 / 98% | **1.24 (edge)** | 2.29 / 2.12 / 1.86 | 84.2 |

- **Total Wipeout** stays at or under 9.8 / 3.7 / 0.8% in every arm.
- **Moving thinning to L3 costs pacing.** Q0 is −0.5 rounds against L1, because L3 comes late and one Secret Breakthrough is gone.
- **The Level 1 rewards have to pay that back:**
  - QC does, at 6 Secrets.
  - QA and QB fall 0.1–0.35 short.
  - Pen Test L1 "Vulnerability to 0" pulls Green down toward the bottom of the band (QB 4P 1.23).

### 9.3 Owned Gray, Gray roll share, early income, and Secret faces (3P)

| Arm | Owned Gray, R1 → R8 | Gray roll share | Cash / 🔬 in R1–4 (Phase 3) | Secret faces by round, R1 → R8 |
|:---|:---|---:|:---|:---|
| BASE | 2.9, 3.5, 3.7, 3.9, 4.1, 4.2, 4.3, 4.3 | 33% | 11.4 / 12.0 | .60 .51 .56 .61 .68 .72 .77 .81 |
| P2a (§8) | 5.0, 4.2, 3.7, 3.2, 2.8, 2.6, 2.6, 2.5 | 52% | 9.8 / 13.8 | .60 **.27** .52 .45 .58 .63 .70 .75 |
| **QC** | **5.0, 4.8, 4.3, 4.0, 4.0, 3.9, 3.9, 3.9** | 49% | 10.2 / 14.6 (+$2 from Triage L1 in R1 = **12.2**) | .60 **.27** .55 .38 .62 .52 .65 .64 |
| QC, seat 0 rushes | 5.0, 4.6, 4.0, 3.7, 3.6, 3.6, 3.5, 3.5 | 52% | 10.5 / 15.2 | .60 .34 .52 .43 .60 .56 .68 .68 |

- **The "good suck" is there.**
  - Players hold 4.8–5 Gray through Round 2 and about 4 for the rest of the game.
  - Per seat-game: 0.56 L3 thinnings, 0.38 Triage L4 swaps, and 0.26–0.52 *Burn Notice* per game on the Spook seat.
- **Early cash:** bots reach Triage L1 in Round 1 (mean 1.03). With its `+$2`, QC's R1–4 cash is $12.2 against BASE's $11.4. Early 🔬 is +2.6.
- **The Round 2 dip (0.27 Secret faces) is unchanged.**
  - The cause is structural. Round 1's Sprint Review takes the 3 Current Gray plus Purple, so the company die waits until Round 3.
  - Release L1 "+1 Release Bandwidth this round" fixes it only for a player who buys Release L1 in Round 1. Bots reach it in Round 3.1, so the fix doesn't show here; rushers reach 0.34.
  - There is no dead turn: income still pays in Round 2.

### 9.4 Thinning-rush stress test

**First and second thin (mean round, earliest round):**

| | First thin | Second thin | Share of seats that ever thin |
|:---|:---|:---|:---|
| Normal bots (QC) | 3.4 (earliest 3) | none | 56% |
| Rusher (seat 0) | **2.2 (earliest 2; 84% in Round 2)** | 3.8 (earliest 3) | 99% / 93% |
| Mixed rusher (seat 0, 50% of rounds) | 3.4 (earliest 2; 19% in Round 2) | 5.8 (earliest 4) | 93% / 69% |

- **The first thin is never earlier than Round 2's Phase 5 Operations.** That meets the "not before the end of Round 2" target, at the margin. The thinned die has already rolled twice and sat through Round 1's Sprint Review.

**Rusher win rate (paired seeds; seat 0; 2P / 3P / 4P):**

| Arm | Seat 0 win (normal) | Seat 0 win (rushing) | Δ |
|:---|:---|:---|:---|
| BASE v0.46 (L3 = +1 Secret) | 53.1 / 30.4 / 26.5 | 54.3 / 42.0 / 32.2 | +1.2 / **+11.6** / +5.7 |
| L1 (§7) | 53.9 / 35.3 / 24.9 | 63.5 / 46.4 / 37.1 | **+9.6 / +11.1 / +12.2** |
| QC | 51.1 / 33.0 / 24.8 | 56.6 / 41.4 / 31.5 | +5.5 / +8.4 / +6.7 |
| QC, mixed rusher | | 57.0 / 38.6 / 29.9 | +5.9 / +5.6 / +5.1 |
| QC, rushes but takes +1 Secret instead of thinning | | 65.8 / 46.1 / 37.9 | +14.7 / +13.1 / +13.1 |
| QC, rushes but neither thins nor gains | | 51.9 / 34.1 / 24.7 | +0.8 / +1.1 / −0.1 |

- **Rushing is strong in every ruleset, including v0.46 today.** Thinning does not create the rush, and QC gives the rush its smallest edge.
  - The gain comes from the research path: Release L2 (Release Bandwidth 5) and the L3 Breakthrough itself.
  - The bots' default focus (Triage first) undervalues it.
  - This is a bot-policy gap that already exists, not a new degenerate line. It would justify a research-focus pass on the bots before playtest numbers are trusted.
- **Under QC, rushing becomes less dominant than under L1** (+6 to +8 pp, against +10 to +12). That is because the L3 reward is now worth less.

### 9.5 Lost L3 Secrets against thinning value

| Seat 0 at Release / Pen Test L3 (QC) | Δ win, 2P / 3P / 4P | Δ Secrets |
|:---|:---|:---|
| Normal bot takes the old +1 Secret instead of thinning | +2.0 / +1.8 / +1.5 pp | +0.27 / +0.44 / +0.34 |
| Normal bot gets nothing (neither thins nor gains) | −0.4 / −2.3 / −1.4 pp | −0.28 / −0.17 / −0.31 |
| Rusher: thin rather than nothing (about 1.9 thins) | +4.7 / +7.3 / +6.8 pp | +0.78 / +1.20 / +1.27 |
| Rusher: +1 Secret rather than thin | +9.2 / +4.7 / +6.4 pp | +1.41 / +0.94 / +1.01 |

- **One thin is worth about +0.4 to +0.65 Secrets.** The +1 Secret it replaces is worth about 1.
- **So each Breakthrough that thins costs its owner about 0.5 Secret.** That is the price of the "good suck". Across the table, QC's Level 1 rewards repay it: Pen Test L1 +1 Secret and Triage L1 +$2.

### 9.6 Win spreads (pp, 2P / 3P / 4P)

| | BASE | QC |
|:---|:---|:---|
| Bot | 10.5 / 18.0 / 10.7 | 15.9 / 11.3 / 11.6 |
| Company | 19.2 / 17.8 / 15.7 | 20.6 / 16.1 / 16.1 |
| White Hat | 10.1 / 9.0 / 8.1 | 11.4 / 9.6 / 6.7 |
| Spook win % | 50 / 39 / 28 | 56 / 39 / 30 |
| Operator win % | 51 / 31 / 21 | 50 / 31 / 24 |

All are within noise of BASE. The 2P Spook rise (+6 pp) is about 2 SE; watch it.

### 9.7 Recommendation: QC with 6 starting Corporate Secrets

| Track | L0 | L1 (Breakthrough) | L2 | L3 (Breakthrough) | L4 |
|:---|:---|:---|:---|:---|:---|
| Pen Test | limit 1 | Gain 1 Corporate Secret | limit 2 | Return 1 Gray Legacy die you own to the box *(Blue Secret faces yield +3)* | limit 3 + free −1 Vulnerability per Operations Turn |
| Triage | Bandwidth 1 | Gain +$2 | Bandwidth 2 | Gain 1 Corporate Secret | Bandwidth 2 + replace 1 Gray with a Central Market colored die |
| Release | Bandwidth 4 | +1 Release Bandwidth this round | Bandwidth 5 | Return 1 Gray Legacy die you own to the box | Bandwidth 6 + set 1 rolled Gray to any face |
| Public Relations | regain 1 | Gain +$3 | regain 2 | 2nd Purple die (to Scanned) | regain 3 + gain +2 Market Share |

**Setup:**
- Ready for Release: 2 Gray + Purple + company die.
- Current Sprint: 3 Gray.
- 6 Corporate Secrets. 5 is −0.6 rounds and 7 is +0.7, so 6 stands.

**Why QC:**
- It is closest to v0.46 pacing among the Level 3 arms.
- Singularity reaches 71–84% of v0.46.
- Income is ×1.17. Green is mid-band. 4P PZ + Collapse is 87.7.
- Early cash beats BASE.
- Players live with 5 Gray for 2 rounds.

**Thematic alternative: QA at 7 Secrets** (Pen Test L1 "Lower your Vulnerability to 0"). It passes, but 3P / 4P run +0.4 long and Green is lower.

**Levers and watch items:**
- **Bot research focus:** fix it before trusting rush data; the rush gap exists in v0.46 too.
- **All-rush income:** it reaches ×1.24. If real players rush, the next lever is the Gray face cash / 🔬 mix (F3 `+$2 / +2 🔬` → `+$1 / +2 🔬`). That was not tested, because no arm failed.
- **Round 2 dip:** if the User wants it gone, the cheapest lever is making the company die the Round 1 Next Sprint priority. Not tested.
