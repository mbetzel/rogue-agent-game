# Pre-SDLC Game Designer Analysis: Locked ⚠ Faces on Colored Dice

**Author:** Game Designer (pre-SDLC analysis)
**Date:** 2026-11-19
**Target version:** `v0.47.0` (from `v0.46.0`)
**Status:** Awaiting User sign-off on the open decisions in §8. No changes to `RULES.md`, `GLOSSARY.md`, `sim/`, `pnp/`, `tts/` or `web/`.
**Probe tooling (no engine edits):** `scripts/probe_locked_vuln.py` (monkeypatch sim probe) and `scripts/probe_locked_vuln_math.py` (exact per-die and per-pool math).

---

## 0. Verdict (TL;DR)

**The rule works, but it is stronger than it looks. Recommend arm B (lock + `V046_VULN` premium), paired with a safe zone of `0–4` (bands `5 / 8 / 11`, min target `5`). That pairing needs User approval as a new `[TUNE]` change.**

- **Lock on its own pushes Green past its guardrail.**
  - Kept ⚠ goes up by **+0.6 to +0.7 per player-round** (+35–40%).
  - Green Secrets lost per player-game go from **2.42 / 2.08 / 1.86** to **3.20 / 2.66 / 2.44** (A, naive bots). The 2P result breaks the 1.2–2.5 guardrail.
  - Patient Zero rises **+12 to +14 pp**. Games get about 0.6 rounds shorter. Survivors end with about 2 fewer Secrets.
- **The Secret-face "chokepoint" is close to a no-op.** Secret faces were already kept 86–99%, and the Processing Box is almost always empty at Deploy (0.01–0.06 dice). The whole effect comes from the **core ⚠ face**: its rate per colored die rises from 0.12–0.14 to 0.32–0.33.
- **Agency is real.** A simple bot that stops rerolling clean colored dice when one more ⚠ would cross 4/7/10 removes about 45% of the extra Green loss. That is exactly the near-threshold risk the design asks for.
- **No degenerate line was found.**
  - Never rerolling colored dice scores −0.4 / −0.7 / −2.4 pp against an aware field.
  - Always chasing ★ scores 0 / −0.8 / +0.3 pp.
- **B is better than A.** It gives +0.1 to +0.3 rounds, −1 to −3.5 pp Patient Zero, +0.2 to +0.4 Secrets, and +0.4 to +0.6 Pen Test steps. It also avoids forcing a ⚠ face that is a strictly worse twin of a clean face (Blue F3 `+$2 ⚠` against F2/F4, Yellow F5 against F4).
- **Side effects:**
  - Good: 4P Market Collapse drops from 22.8 to about 16–17%, which fixes the open v0.46 4P FAIL.
  - Bad: Helix, already the weakest company, loses another 1–4 pp in the probe. Yellow is the most heavily taxed die (§2).

## 1. Rule as modelled

| Item | Rule |
|:---|:---|
| What locks | During Phase 1, a **colored die** (Red, Blue, Green, Yellow or Purple) showing a ⚠ face can't be rerolled for the rest of the phase. This covers the core ⚠ face and the Secret face. The check runs after the roll and after every reroll. |
| What doesn't lock | Gray Legacy dice (3 ⚠ faces, free rerolls). Release L4 (sets a Gray face only) is unaffected. |
| What can change a locked face | Helix *Brute-Force Bypass* and Prodigy *Arbitrary Code Execution* (ACE). |
| Terminology | Step 4 "Lock-in & Assign Dice" becomes **"Deploy"**. |

## 2. Per-die math (exact; 3 rolls = 1 roll + 2 rerolls)

| Die / policy | E[⚠] v0.46 | E[⚠] lock | P(★) v0.46 | P(★) lock |
|:---|---:|---:|---:|---:|
| R/B/G/P, "safe" (reroll the core ⚠, keep Secret) | 0.204 | **0.333** | 0.199 | 0.167 |
| R/B/G/P, reroll every ⚠ (incl. Secret) | 0.037 | 0.333 (not possible) | 0.241 | 0.167 |
| R/B/G/P, ★-chase (reroll clean faces too) | 0.426 | **0.583** | 0.352 | 0.292 |
| **Yellow, safe** (2 core ⚠, no Secret) | **0.037** | **0.333** (×9) | 0.241 | 0.167 |
| Yellow, ★-chase | 0.231 | 0.583 | 0.421 | 0.292 |
| Gray, reroll ⚠ (unchanged) | 0.125 | 0.125 | — | — |

- The main session's first-pass figures check out: 0.20 → 0.33 for safe play, 0.43 → 0.58 for ★-chase, and P(★) 0.35 → 0.29.
- **Yellow takes the biggest hit.** Today, a careful player almost never keeps a Yellow ⚠. Under lock, a third of Yellow rolls carry one, and Yellow has no Secret face to pay for it.
- **Marginal risk of a reroll:**
  - Under lock, every reroll of a clean colored die carries a 1/3 chance of adding a ⚠ that can't be undone.
  - In v0.46, that ⚠ could be rerolled again whenever a reroll was left, so the risk only applied on the last reroll.
  - The rule therefore moves risk onto the **first** reroll and the **initial** roll.
- **Sim rates per colored die** (mixed1 bots), kept ⚠ = core + Secret:
  - v0.46: 0.12–0.14 core + 0.19–0.21 Secret, about 0.33 in total.
  - Lock: 0.32–0.33 core + 0.18–0.20 Secret, about 0.52 in total.
  - P(★) per colored die: 0.17 → 0.12–0.13 (−25 to −30%; bots chase ★ less once locked).

## 3. Per-pool ⚠ per round and threshold crossing

In this table:
- **X** = ⚠ kept in one round. Gray dice are "safe" (0.125 each) in the model rows and 0.38 each in the sim-observed rows.
- **P(cross | V0)** = P(V0 + X reaches the next band, 4, 7 or 10), shown for V0 one, two or three steps below that band.

| Pool | Policy | E[X] | V0 = t−3 | t−2 | t−1 |
|:---|:---|---:|---:|---:|---:|
| Starter 2G + 2C | v0.46 safe → lock safe | 0.66 → 0.92 | 0.01 → 0.03 | 0.13 → 0.22 | 0.51 → 0.66 |
| Starter | sim-observed v0.46 → lock | 1.42 → 1.80 | 0.13 → 0.24 | 0.45 → 0.61 | 0.83 → 0.91 |
| Mid 2G + 4C | v0.46 safe → lock safe | 1.07 → 1.58 | 0.07 → 0.19 | 0.29 → 0.50 | 0.69 → 0.85 |
| Mid | ★-chase v0.46 → lock | 1.95 → 2.58 | 0.30 → 0.53 | 0.65 → 0.84 | 0.92 → 0.98 |
| Mid | sim-observed | 2.08 → 2.84 | 0.35 → 0.61 | 0.67 → 0.87 | 0.92 → 0.98 |
| Late 2G + 6C | v0.46 safe → lock safe | 1.47 → 2.25 | 0.17 → 0.40 | 0.45 → 0.71 | 0.81 → 0.93 |
| Late | sim-observed | 2.74 → 3.88 | 0.55 → 0.84 | 0.82 → 0.96 | 0.97 → 1.00 |

Two things change:
- **Crossing from 0 to 4 in one round** stays rare in the starter pool (≤ 4%). It becomes common late: 16% for safe play, 58–60% for ★-chase or observed play with 6 colored dice.
- **The safe-zone buffer** (two or three steps below a band) roughly doubles its crossing odds. That is where the decision tension lives.

Telemetry: kept ⚠ per player-round in the sim, v0.46 → lock = 1.77 → 2.45 (2P), 1.76 → 2.39 (3P) and 1.74 → 2.35 (4P).

## 4. Sim-backed probe (v046_roster, mixed1, seeds 42–1241, 1,200 games per pod)

**How the probe works:**
- `adjust_rerolls` is wrapped so it drops colored dice that show ⚠. The engine already freezes un-rerolled dice, so this is equivalent to a lock.
- "aware" = skip rerolling a clean colored die when V + the ⚠ already on the table + 1 reaches 4, 7 or 10.
- The base row reproduces §62 exactly (2.42 / 2.08 / 1.86; rounds 8.20 / 7.77 / 7.51; MC 35.7 / 21.1 / 22.8).

| Arm (2P / 3P / 4P) | Rounds | Patient Zero % | Total Wipeout % | Market Collapse % | Green lost / player-game | Pen Test steps | End Secrets | Green no-target % |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| v0.46 base | 8.20 / 7.77 / 7.51 | 32 / 57 / 61 | 5.1 / 1.4 / 0.1 | 35.7 / 21.1 / 22.8 | 2.42 / 2.08 / 1.86 | 1.6 / 1.7 / 1.8 | 9.1 / 8.1 / 8.4 | 62 / 50 / 41 |
| A lock + NOPREMIUM (naive) | 7.56 / 7.01 / 6.88 | 45 / 70 / 73 | 10.2 / 1.9 / 0.9 | 25.9 / 16.3 / 17.3 | **3.20** / 2.66 / 2.44 | 1.8 / 2.0 / 2.1 | 6.6 / 6.5 / 6.9 | 50 / 36 / 27 |
| B lock + premium (naive) | 7.83 / 7.09 / 7.05 | 42 / 70 / 72 | 8.6 / 2.5 / 0.8 | 26.2 / 13.6 / 16.0 | **3.27** / 2.68 / 2.48 | 2.2 / 2.3 / 2.6 | 7.0 / 6.6 / 7.1 | 50 / 35 / 28 |
| A aware | 7.50 / 7.02 / 6.85 | 45 / 70 / 74 | 10.3 / 2.3 / 0.4 | 26.5 / 14.8 / 16.5 | **2.85** / 2.40 / 2.19 | 1.9 / 2.0 / 2.2 | 6.3 / 6.3 / 6.6 | 53 / 39 / 30 |
| B aware | 7.73 / 7.10 / 6.99 | 46 / 69 / 72 | 8.2 / 3.3 / 0.8 | 25.3 / 14.4 / 16.2 | **2.89** / 2.42 / 2.18 | 2.3 / 2.4 / 2.5 | 6.6 / 6.4 / 6.6 | 54 / 40 / 31 |
| B aware + Pen Test cost 1 | 7.79 / 7.26 / 7.01 | 46 / 69 / 73 | 8.2 / 2.4 / 0.3 | 24.6 / 13.8 / 16.3 | 2.87 / 2.39 / 2.11 | 2.6 / 2.8 / 3.0 | 6.8 / 6.4 / 7.0 | 54 / 41 / 32 |
| A aware + safe 0–4 | 7.73 / 7.23 / 7.08 | 41 / 68 / 72 | 8.7 / 2.6 / 1.2 | 29.8 / 15.7 / 17.1 | 2.24 / 1.90 / 1.74 | 2.5 / 2.6 / 2.6 | 6.9 / 6.4 / 6.6 | 64 / 52 / 44 |
| **B aware + safe 0–4** | **7.89 / 7.51 / 7.34** | **42 / 65 / 69** | 7.3 / 2.5 / 0.8 | 28.4 / 16.0 / 16.8 | **2.23 / 1.93 / 1.76** | 3.1 / 3.1 / 3.2 | 7.2 / 6.8 / 7.1 | 65 / 53 / 45 |

"Safe 0–4" = `vuln_band_thresholds (5, 8, 11)` and `vuln_min_target_by_version (5, 5, 5)`.

**Guardrails for B aware + safe 0–4** (bar = §8.2 of the v0.46 assessment):

| Guardrail | Result | Verdict |
|:---|:---|:---|
| Mean rounds 6.5–8.5 | — | PASS |
| Patient Zero ≤ v0.45 + 3 (52 / 79 / 82) | — | PASS |
| Total Wipeout ≤ 15 / 5 / 2% | — | PASS |
| Green lost 1.2–2.5 | — | PASS |
| 4P Market Collapse within v0.45 ±5 (16.5) | — | **now PASS** |
| Green no-target, 2P | 65% | at the ≤ 70% edge |
| 4P company spread | about 21 pp (Aegis 35.8 / Helix 14.7) | **still FAIL**, slightly worse |

**Dominance probe** (seat 0 deviates; the rest of the field is B aware):

| Seat 0 policy | Seat 0 win vs control (2P / 3P / 4P) |
|:---|:---|
| Never reroll colored dice | 48.7 vs 49.1 / 31.1 vs 31.8 / 22.3 vs 24.8 |
| Always ★-chase | 49.1 / 31.1 / 25.1 |

Neither policy dominates. Never-reroll is mildly worse, and ★-chase is neutral.

**Probe limits:**
1. Engine `is_locked` is not set, so Helix bots (which fire Brute-Force Bypass on `any(d.is_locked)`) rarely use it. **Helix is undervalued.**
2. ACE resolves only on the initial roll.
3. Field bots are not lock-aware except for the simple "aware" heuristic.
4. Per-colour win rates were not measured.

## 5. Other effects

- **Processing Box chokepoint.** It does not show up.
  - Forced Secret faces add only about 0.01 per colored die per round, because they were already kept.
  - The box is close to empty when Deploy resolves.
  - If the User wants a real throughput chokepoint, it needs a separate lever, for example limiting how much can sit in the Processing Box. That is out of scope here.
- **Pen Test 🔬 tax.** Pen Test steps rise by +0.2 to +0.4 per player-game (A), +0.6 to +0.8 (B) and +1.4 (B + safe 0–4). At cost 2, that is +0.4 to +2.8 🔬 per game. B's premium 🔬 mostly pays for this. Bots spend on Pen Test too little, so Green absorbs the rest. Cutting the Pen Test cost to 1 barely moves results with the current bots.
- **★ rates.** P(★) per colored die falls 16–30% (Yellow 31%). The B1–Y3 Variant Cards fire less often, which lowers the variance and payoff of ★-building.
- **Helix *Brute-Force Bypass*.**
  - Under lock, it becomes the only way to fully unlock a pool. It is worth about (0.33 − 0.20) × colored dice ≈ 0.5–0.8 ⚠ per use, plus restored ★ odds, three times per game.
  - The probe shows Helix down 1–4 pp, but that is a bot artefact (limit 1).
  - **Rules/sim mismatch (flag):** RULES says Brute-Force Bypass = +1 reroll **and** set 1 die face. The sim's `helix_active` instead lets every reroll ignore locks. That gap matters now; see decision D3.
- **Prodigy *ACE*.** It becomes a lock-breaker: turning a locked core ⚠ into the best clean face is worth +1 face-value + λ. The Purple ★ that triggers it is rarer under ★-chase (0.35 → 0.29), so the net effect is roughly neutral to positive. Measure it per White Hat.
- **B3 / G1 relief.** Vulnerability now sits at the thresholds more often, so −1 / −2 Vulnerability lands in the decision zone more often. Their value rises modestly. Watch B3 and G1 card win rates.

## 6. Edge cases and degenerate strategies

| Case | Assessment |
|:---|:---|
| Never reroll colored dice | Not dominant (§4). ⚠ per die stays 0.33, but you lose ★ and income. |
| Gray-only rerolling | The natural safe line. Gray dice become the only free reroll targets, so Release L4 (Gray face-set) gains relative value. Track Release L4 share. |
| Buying fewer colored dice | Each colored die adds about 0.13–0.20 ⚠ per round over v0.46. That is about 0.15 Secrets per extra ⚠, or about 0.15–0.2 Secrets per die per game. That is small next to the die's income, so no avoidance is expected. Verify colored dice bought per game. |
| Yellow | 2 core ⚠ and no Secret: E[⚠] goes up ×9 under safe play. On NOPREMIUM, F5 `+$2 / +1 🔬 ⚠` is a strict ⚠ twin of F4. **That is the case against A.** Under B, F5 `+$2 & +1 🔬` pays for itself. Gate on Yellow win-rate parity (balance-by-win-rate rule). |
| Blue F3 under A | `+$2 ⚠` is dominated by F2 `+2 🔬` and F4. A locked F3 is a pure tax. B pays `+$2 & +1 🔬`. |
| Locked Secret face, Processing Box full | No new case. Secret faces still go to the box. Note that a lock stops a player rerolling a Secret face to dodge a band, which ref1 did 20–30% of the time. That narrows ref1's edge. |
| Kamikaze | Forced ⚠ speeds up deliberate dumping. 2P Total Wipeout goes from 5.1 to 7–10% (≤ 15 guardrail). Watch it. |
| Choice face with ⚠ (Red F1 NOPREMIUM, Yellow F5 NOPREMIUM) | Lock applies to the die. The choice is still made at Deploy. |
| Purple starter | It is in every pool, so the starter E[⚠] already rises by 0.13. Purple F4 under A, `+$1 & +1 🔬 ⚠`, is a ⚠ twin of the F1/F2 choice faces. |
| Operator *Contingent Staffing* (6-face check after each reroll) | Unchanged, but fewer ★ appear. Check Operator win. |
| Glitch-face locks (legacy) | Same `is_locked` flag. Keep the v0.46 path free of glitch faces. The new flag must not change pre-v0.47 presets. |

## 7. Arm recommendation

- **B over A.** A forced ⚠ should be a lucrative face; that is the Cubitos pillar of "risk on lucrative faces". Under NOPREMIUM, three of the five core ⚠ faces are clean-face twins. B also lands better on every guardrail.
- **The lock needs a counterweight.** Without one, 2P Green breaks the guardrail even with aware bots (2.89). The safe zone `0–4` fixes this, and it is the smallest lever that restores the v0.46 Green economy and the no-target rate. It is a `[TUNE]` change to the §62 package and needs User approval (D1).
- **Alternatives for the sweep:**
  - Band damage `(1, 1, 2)`.
  - `green_secret_vuln_reduction` 2 → 3.
  - Cut the Pen Test cost to 1. This is weak with the current bots, but stronger with a lock-aware Pen Test policy.

## 8. Open decisions for the User

> **User decisions (2026-11-19):**
> - **D1 accepted:** safe zone `0–4` (bands 5 / 8 / 11, min target 5).
> - **D2 accepted:** arm B (`V046_VULN` premium faces) is the v0.47 default.
> - **D3 replaced by a User rule:** Helix *Brute-Force Bypass* becomes "you may reroll locked dice this phase", and it is **once per game** (like DTO *Slush Fund*), not once per Version. It no longer grants +1 reroll or sets a face. The sweep must report Helix's win rate, since Helix was already weakest at 4P (about 15%).
> - **D4 accepted:** "locked die" is the new term; Target Lock text becomes "Target-Locked player".
> - **D5 accepted:** Secret faces lock.
> - Also: Phase 1 Step 4 "Lock-in & Assign Dice" is renamed "Deploy".

- **D1.** Pair the lock with safe zone `0–4` (bands 5 / 8 / 11, min target 5)? The alternative is to sweep the counter-lever arms first.
- **D2.** Arm B (premium) as the v0.47 default? Recommended.
- **D3.** Brute-Force Bypass under lock: **(a)** follow RULES (+1 reroll and set 1 face; may target a locked die) or **(b)** follow the sim (all rerolls this phase ignore locks). Recommend **(b)**: it is the stronger answer to the Helix weakness, and it reads simply as "Helix ignores locks this phase". RULES text would need updating to match.
- **D4. Term collision.**
  - "Target Lock" (glossary) already says "the locked player", and the QUICKREF says "*(non-locked)* surviving player".
  - Options: keep "locked" for dice only and reword Target Lock to "the Target-Locked player", or pick a different die-state word.
  - Recommendation: keep "locked die", and change the Target Lock wording to "Target-Locked player".
  - "Lock-in" also appears in the GLOSSARY Vulnerability and Phase 1 entries, in the APPENDIX, and in the pnp text (§10). All of these become "Deploy".
- **D5.** Should Secret faces lock? The design says yes. The cost is about 0, apart from removing ref1's dodge. Keep yes.

## 9. Implementation plan (SDLC chain)

**Principal engineer (spec):**
1. Config flags:
   - `colored_vuln_lock: bool = False`.
   - `colored_vuln_lock_secret: bool = True`.
   - Preset `GameConfig.v046_locked()`, inheriting `v046()`: lock on, `die_face_profile = "V046_VULN"` (if D2), bands `(5, 8, 11)` and min target `(5, 5, 5)` (if D1).
   - Add `v046_locked_roster`.
   - Validation: the lock requires `is_vulnerability`.
2. Engine (`sim/engine/phase1_roll_deploy.py` about lines 436–530): extend `_evaluate_locks` so that `cfg.colored_vuln_lock and d.color != GRAY and face_vuln(face) > 0` sets `is_locked`.
   - Respect the Secret sub-flag.
   - It already runs before the Helix decision and after each reroll.
   - Clear the locks at Deploy.
   - ACE and the Brute-Force Bypass face-set clear `is_locked` (they already do). Implement the D3 choice.
3. Telemetry:
   - Locked-⚠ events per face.
   - Kept ⚠ per die, by colour and by source (core / Secret / Gray).
   - P(★) per colored die.
   - Count of lock-breaks by Brute-Force Bypass and ACE.
   - Count of declined near-threshold rerolls.
   - The v0.46 keep-rate metric only counts unlocked ⚠. Report colored keep-rate as "n/a under lock".

**Senior engineer (bots, `sim/bots/vulnerability_policy.py`):**
- In `adjust_rerolls`, for each clean colored die the base bot wants to reroll: drop it if `keep_value < mean(face values) − λ(V_table + 1) · P(⚠ face) + lock penalty`. Here λ is evaluated at the post-roll table Vulnerability, so the crossing step is priced.
- REROLL_ALL can now reroll only Gray and clean dice.
- Add stance `NO_COLOR_REROLL` for the dominance matrix.
- Helix `choose_helix_override`: value it as Σ λ over locked colored ⚠ dice plus ★ odds, instead of the current `any(is_locked)`.
- Prodigy ACE target: prefer a locked core ⚠.
- Pen Test policy: let λ near a threshold pull in Pen Test spending.

**Staff engineer (review):** check that pre-v0.47 presets are unchanged (golden fixtures), the invariants from `run_v046_sweep --assert-invariants`, and the new invariant "INV-LOCK-01: no colored ⚠ die rerolled unless BFB/ACE".

**Product owner (sweep design):**
- Base run: `run_v046_sweep.py`-style, `v046_locked_roster` vs `v046_roster`, mixed1, seeds 42–1241, 1,200 games per pod, 2P / 3P / 4P.
- Arms:
  - A, B (± safe 0–4).
  - Counter-levers: damage `(1, 1, 2)`, Green yield 3, Pen Test cost 1.
  - Secret-lock off (D5 control).
- Also run `run_v046_dominance_matrix.py` (KeepAll, RerollAllVuln, NO_COLOR_REROLL, ★-chase, PenTestRush, Kamikaze) and the ref1 check under the D5 bar.
- Guardrails: v0.46 §8.2 set, plus:

| New guardrail | Bar |
|:---|:---|
| Per-colour die win-rate parity | Yellow especially |
| Helix company win | ≥ v0.46 − 2 pp |
| Prodigy and Operator win | Within ±3 pp |
| P(★) per colored die | ≥ 0.12 |
| Colored dice bought per game | ≥ v0.46 − 10% |
| Release L4 share | Report only |

**Game designer (post-telemetry):** run the balance assessment and the FINDINGS §63 entry.

## 10. Doc and term sync list (after sign-off)

| Doc | Change |
|:---|:---|
| `RULES.md` | Phase 1 Step 3 (lock clause and timing), the Step 3 override list (Brute-Force Bypass / ACE vs locks, D3), Step 4 "Lock-in & Assign Dice" → "Deploy", and any changed `[TUNE]` bands or safe zone in the Vulnerability section |
| `RULES_QUICKREF.md` | Line 77 "Lock-in & Deploy Dice" → "Deploy"; the reroll lock line; line 129 "(non-locked)" → "(non-Target-Locked)" if D4 |
| `GLOSSARY.md` | Vulnerability entry (line 41 "at lock-in"); Phase 1 entry (line 96, step 4 name); Target Lock wording (line 33, if D4); new entry for the locked-die state, with term approval |
| `RULES_APPENDIX.md` | Line 19 "at lock-in" → "at Deploy"; the face tables if B (premium faces) |
| `pnp/generate_pnp.py` | Lines about 1772 and 1901 (lock-in / Roll & Rerolls text), premium face art if B, version strings; then rerun `python3 -m pnp.generate_pnp` |
| `tts/` | Rebuild with `python3 -m tts.build_tts`; bump `VERSION`, the `global.lua` header and the README. TTS `Locked` object properties are not game text, so ignore them. |
| `web/` | Phase 1 lock UI: `static/js/components/compiler.js`, `action_dock.js`, `player_mats.js`, `header.js`, `api.js`, `index.html`, `controller/core.py`, `controller/capabilities.py`, `schemas.py`, `server.py`. Grep each for "Lock-in" or `is_locked` and disable reroll on locked colored dice. |
| Version | Bump everything in the CLAUDE.md version list to v0.47.0 |
| `PLAN.md` / `FINDINGS.md` | Phase entry and §63 |

## 11. v0.49 decisions (User, 2026-11-19), after the merge with v0.48.0

- **Lock all dice.** The package moves onto v0.48 as `GameConfig.v049()`. Every die showing ⚠ locks: colored core ⚠, Secret/R&D faces and Gray ⚠ (`vuln_lock_gray`). The decision was made 2026-11-19, after main shipped v0.48's Gray-only lock.
- **Helix H1B** (`docs/reports/v049_balance_assessment.md`):
  - *Brute-Force Bypass* stays once per game: "you may reroll locked dice this phase".
  - It also sets 1 die to any non-★ face.
  - The Black Signature (Root Override Hijack) cannot mark it Used.
  - The probe reached 45.2 / 28.2 / 19.2% (2P −1.5 pp).
- **Safe zone 0–4 kept** (bands 5/8/11, min target 5). Premium faces (arm B) kept.
- **Guardrails re-based:**
  - The Market Collapse row is replaced by "Patient Zero + Collapse ≤ v0.48 + 3 pp" and "Collapse ≥ 8% at 3P/4P".
  - Income is +18% vs v0.48, which is accepted. The income bar is re-based on v0.48 at ≤ ×1.20.
- **Term collision:** the Institutional Override Track status "Locked" is renamed, so "locked" is reserved for dice. The new name needs User confirmation.
