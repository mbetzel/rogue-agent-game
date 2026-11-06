# Six-Phase Round Sequence — Implementation Plan (Rev 3 — Signed Off)

**Status:** ✅ Signed off by user (2026-11-05). D1–D5 and O1–O3 confirmed; handed off to `principal-engineer`.
**Target version:** `v0.34.0`
**Evidence:** `scripts/investigate_income_before_defense.py`. Re-run the Rev 2 configuration with:
`MODES=LITERAL FLAT_SECRETS=8 python3 scripts/investigate_income_before_defense.py 3000`

---

## 1. Goal & Approved Round Structure

Income is collected **after corruption but before attack cubes**. Unblocked Green Malware therefore delays dice into future rounds instead of also deleting this round's income. Corruption (cash loss, glitches) still lands on the pre-income buffer.

| # | Phase | Mode | Contents |
|---|---|---|---|
| 1 | **Roll & Deploy** | Simultaneous | Unchanged: Version Switch, Pulse (+1 Black Cube), Temp Staffing, Roll, Yahtzee Rerolls, Assign to In Production. |
| 2 | **Compiler Drop & Corruption** | Simultaneous | Drop the Staging Cup into the Cube Tower. Resolve Black Cubes on the Corruption Track: Version Advance, Spillover, Singularity. Compile Buffer Overflow also happens here. |
| 3 | **Income** | Simultaneous | Collect `$`, `🔬` and `★` outputs from every die still In Production (both the Income slot and Shield slots), including White Contractor dice. |
| 4 | **Attack Resolution** | Simultaneous | Passive Firewall, Two-Stage Defensive Blocking, Red/Blue/Green damage, Snowball Recycle, Contractor Expiration, end-game trigger check. |
| 5 | **CI/CD Pipeline Shift** | Simultaneous | Pipeline shift in the D1 order below. |
| 6 | **Operations** | Clockwise from First Player | Buy dice (limit 2), Terminal Hardware Track upgrades, Patent Filings, paid `★` actions, Prometheus override. Then pass the First Player Marker. |

---

## 2. Recorded Decisions

### D1 — In Production dice route through Scanned ✅
Every In Production die goes through the **Scanned Box**, so **Release Bandwidth** becomes a hard cap on how many dice re-enter the Ready for Release Zone each round.

**Phase 5 order:**
1. **Emergency Hotfix & Magnetic Splice:** Emergency Hotfix (Triage Track Level 2) and Omnidyne *Magnetic Splice* each move 1 die Glitched → Ready.
2. **Production Return:** all surviving In Production dice → **Scanned Box**.
3. **Scanned Graduation:** move up to `release_bandwidth` dice (4 / 5 / 6) from Scanned → Ready. **The player chooses which ones** (see open item O2).
4. **Conveyor Triage:** move up to `triage_bandwidth` dice (2 / 3 / 4) from Glitched → Scanned.

What this does:
- **Your active pool is capped.** The dice you roll next round are at most the Release Bandwidth graduates, plus dice bought in Phase 6, plus any Hotfix/Splice die.
- **Release Track upgrades become a core engine decision.** At the 4-die baseline, the starting pool (3 Gray + 1 Purple) fits exactly, and every extra die competes for a slot.
- **Sim cost:** about 1.8 dice per player-game are held in Scanned. Income per turn is about 2.3 under this option, versus 2.5 if dice returned straight to Ready and 1.6 under v0.33.

### D2 — Phase names ✅ (two of my recommendations corrected)
- **Phase 4 is "Attack Resolution", not "Defense Grid".** "Defense Grid" is already the canonical name of the Defense Grid Track and Defense Grid Capacity, so using it for a phase would collide.
- **Phase 6 is "Operations".** It reuses the canonical *Operations Turns* term, so no new vocabulary is needed.
- The deprecated **"Boot & Configure"** and **"Rogue Agent Compile"** names in `web/controller/core.py:65,275,328` get replaced in the same pass.

### D3 — Rule consequences ✅ (all accepted)
1. **Contractors** expire at the end of Phase 4, so their `+$1` face now pays in Phase 3. Contractor Sacrifice against Green still applies.
2. **"Income Forfeiture" is removed.** Green is a tempo hit only.
3. **Red** becomes a tax on this round's income. Ransom leaks fall about 15%.
4. **Patient Zero in Phase 2** (a *Lose X Secrets* corruption space) is eliminated immediately and skips Phases 3–6.
5. **Finish the round.** When anyone becomes Patient Zero (Phase 2 or Phase 4), the round becomes the Final Round and **survivors complete every remaining phase**:
   - If the breach happened in Phase 2, survivors still collect income and still face Phase 4 attacks.
   - A Phase 4 breach by every remaining survivor becomes a **Total Wipeout**.
   - Phase 6 Patent Filings can still add Secrets before scoring.
6. **Singularity** still ends the game immediately at the end of Phase 2, skipping Phases 3–6.
7. **Compile Buffer Overflow:** Phase 2 adds 1R/1B/1G to the Staging Cup, Phase 4 resolves nothing, and Phase 3 income still happens.
8. **Income-timed abilities move to Phase 3.** These are Acoustic, Cipher, Spook's +$2 and Burn Notice, Phreaker's Jumper Diagnostics, and the B3 / Y2 / Y3 star faces. Burn Notice (+1 Secret) now resolves *before* Blue hits. The v0.34 sweep will watch the Spook win rate.
9. **Paid `★` actions** (B2, Y1, P1/P3) move to Phase 6.
10. **Damage-conditional `★` faces** (R2, R3, B1) stay in Phase 4.

### D4 — Override timing ✅
| Company | Override | Timing |
|---|---|---|
| Meridian | *Redundant Crew* | Phase 1 |
| Helix | *Brute-Force Bypass* | Phase 1 |
| Aegis | *Baffle Echo* | Phase 4 |
| DTO | *Slush Fund* | Phase 4 |
| Omnidyne | *Magnetic Splice* | Phase 5 (step 1) |
| Prometheus | *Algorithmic Arbitrage* | Phase 6 |

The version-transition text "remains usable through Phase 2B and Phase 3" becomes "remains usable through Phases 3–6".

### D5 — Flat 8 starting Secrets at every player count ✅
- **8 Corporate Secrets** for 2P, 3P and 4P. DTO still gets +1, so 9.
- Rationale: attack cubes are shared across all players, so player count doesn't scale the threat each player faces.
- The `[TUNE: v0.21.0 9-round buffer parity]` 4P exception (12) is retired.

**Re-projected outcomes** (Rev 2 configuration = D1 Scanned routing + flat 8 Secrets; 3,000 games per pod):

| Metric (2P / 3P / 4P) | v0.33 (4P = 12) | Rev 2 | Guardrail | Status |
|---|---|---|---|---|
| Mean rounds | 8.0 / 7.6 / 8.7 | 8.3 / 8.0 / **7.8** | 8–11 | ⚠ 4P short, 3P at the edge |
| Patient Zero ending | 63% / 83% / 64% | 58% / 73% / 82% | Informational | — |
| Singularity ending | 19% / 11% / 36% | 26% / 20% / 16% | ≤ 45% | ✅ |
| Total Wipeout ending | 19% / 6% / 1% | 16% / 6% / 2% | ≤ 15% | ⚠ 2P (already a v0.33 issue) |
| Player survival | 48% / 59% / 76% | 53% / 62% / 68% | Informational | — |
| Income per turn ($ + 🔬) | 1.61 / 1.65 / 1.51 | 2.23 / 2.29 / 2.34 | Informational | — |
| Zero-income turns | 37% / 36% / 41% | 27% / 26% / 25% | ≤ 30% | ✅ |
| Income in double-whammy rounds | 1.00 / 1.07 / 0.94 | 1.82 / 1.90 / 1.97 | Informational | ✅ goal met |
| Colored dice owned at end | 1.2 / 1.3 / 1.0 | 1.9 / 2.0 / 2.1 | Informational | — |
| Bot win-rate spread | 61 / 54 / 52 pts | 39 / 34 / 33 pts | ≤ 45 | ✅ |

Notes:
- Flat 8 erases the 4P Singularity surge (46% → 16%). The trade-off is shorter 4P games, because one breach among four players ends the game sooner.
- For reference, flat 8 *without* the sequence change gives 4P a 7.45-round mean and 89% Patient Zero endings. The six-phase sequence is what keeps 4P near 8 rounds.

**If 4P pacing stays under 8 rounds** in the v0.34 sweep, there are levers to model, one at a time with sign-off. None of them touch starting Secrets, per D5:
- `v1.0` track `4 → 5` spaces, which delays the first escalation.
- A softer Unpaid Ransom Leak (none if the shortfall is ≤ $1).
- Accept the shorter 4P game, since target length is ~45–60 minutes and 4P turns are longer.

### 2.6 Follow-ups ✅ (all confirmed as recommended)
- **O1 — Terminology.** The user's "Release Bridge" means the canonical **Release Bandwidth** (Release Track). No new term is introduced.
- **O2 — Scanned graduation choice.** The player chooses freely which Scanned dice graduate. The Scanned Box is a physical box, not a queue.
- **O3 — Phase 6 purchases.** Newly bought dice go **directly to Ready for Release**, bypassing the Release Bandwidth cap.

---

### 2.7 Spec open questions — user resolutions (2026-11-05)
The full table is in `docs/specs/v340_six_phase_round_sequence_spec.md` §12.1.
- **OQ-1:** graduate any number of Scanned dice up to Release Bandwidth (player's choice of how many and which).
- **OQ-2:** the Purple `★` die must still be In Production at Phase 3 to fire its Signature Protocol.
- **OQ-3:** Burn Notice may target an In Production die.
- **OQ-4:** Total Wipeout is ranked by the standard tiebreakers only (Money > Ready Colored dice > Research > fewest Under Development). *Net Wipeout Score* is retired.
- **OQ-8:** Conveyor Triage is "die of your choice".
- **OQ-9:** Emergency Hotfix target is the player's choice.
- **OQ-13:** a new **Final Round** glossary entry is approved, and Phase 5 step 1 is named "Emergency Hotfix & Magnetic Splice".
- **OQ-17:** Signature Protocols fire once per Purple `★` die. Watch Spook in the sweep.

## 3. Implementation Plan

### Step 1 — Rules & glossary (`RULES.md`)
- **§3 Setup:** flat 8 Secrets for every player count (DTO 9). Remove the 4P `[TUNE]` note.
- **§4:** rewrite as six phases per §1. Phase 5 follows the D1 order. Remove "Income Forfeiture". Contractor Expiration moves to the end of Phase 4. Final Round per D3.5. Override and protocol timings per D3/D4.
- **§6 card text:** "Phase 3A Income" → "Phase 3: Income"; Phase 2 defense → "Phase 4"; paid stars → "Phase 6". Affects R1, R3, B1, B2, B3, G-block, Y1, Y2, Y3 and the Purple dossiers.
- **§7 Glossary:**
  - Replace the three Phase entries with six (all names approved under D2).
  - Update the *Scanned Box*, *In Production Area* and *Release Track & Release Bandwidth* entries for the D1 routing.
  - Update cross-references in: Two-Stage Defensive Blocking, Unpaid Ransom Leak, Defensive Shield Sacrifice, Contractor Sacrifice, Total Data Breach, Singularity, Total Wipeout, Red/Blue/Green/Black Cubes, Snowball Recycle, Compile Buffer Overflow, Emergency Hotfix, Passive Firewall, White Contractor Dice, First Player.
- Bump the header to `v0.34.0`.

### Step 2 — Simulation engine (`sim/`)
- **`config.py`:**
  - `round_sequence: Literal["V033_THREE_PHASE", "SIX_PHASE"] = "SIX_PHASE"`. The legacy path keeps `tests/version_baselines/*` and the v0.2x–v0.33 tests passing.
  - `starting_secrets_by_player_count = {2: 8, 3: 8, 4: 8}`. The legacy configuration pins 4P back to 12.
- **Modules** (old names kept as re-export shims):
  - `phase1_boot.py` → `phase1_roll_deploy.py`.
  - `phase2_threat.py` splits into `phase2_compiler.py` and `phase4_attack_resolution.py`.
  - `phase3_ops.py` splits into `phase3_income.py`, `phase5_pipeline_shift.py` and `phase6_operations.py`.
- **`core.run_round`:**
  - Runs the six phases in order and returns early on Singularity or Total Wipeout.
  - Patient Zero players skip the remaining phases.
  - Once the Final Round is flagged, the remaining phases still run, then the game ends.
- **Phase 5:** implement the D1 steps 1–4, with a bot hook `choose_scanned_graduates(player, n)` (O2).
- **Telemetry:** per-phase snapshots, plus income per player and dice held in Scanned per round.
- **New invariants:**
  - `INV-SEQ-INCOME-BEFORE-ATTACK-01`: income is collected exactly once per surviving player per round, after Phase 2 and before Phase 4.
  - `INV-SEQ-CONTRACTOR-EXPIRY-01`: contractors are present in Phase 3 and gone after Phase 4.
  - `INV-SEQ-PZ-SKIP-01`: a Phase 2 Patient Zero collects nothing afterwards.
  - `INV-SEQ-FINAL-ROUND-COMPLETE-01`: survivors execute every remaining phase in the Final Round.
  - `INV-PIPE-RELEASE-CAP-01`: Scanned → Ready count ≤ `release_bandwidth`, and In Production never goes straight to Ready.

### Step 3 — Bots (`sim/bots/`)
- `take_phase3_actions` becomes `take_operations_actions`, called in Phase 6 with money after damage. Keep an alias.
- **Green / corruption glitch choice:** re-key by future roll value (sacrifice Gray or cheap dice first), since income has already been collected.
- **New `choose_scanned_graduates`:** prioritize Purple, then colored by cost, then Gray.
- **Release Track valuation:** raise the priority of Release Track upgrades once owned dice exceed `release_bandwidth`.
- **`commit_shields`:** count expected Phase 3 income when judging whether Red is "funded" (`base.py:736` area).

### Step 4 — Web UI (`web/`)
- **`controller/core.py`:** phases `1–6`, `7 = game over`. Approved names. Phase 6 keeps the clockwise turn queue.
- **Actions:** split `phase2_actions.py` and `phase3_actions.py` to match the engine. The `confirm_income` subphase moves to Phase 3. Add a Phase 5 "choose graduates" interaction for humans when Scanned holds more dice than Release Bandwidth.
- **JS:** `header.js` names; `action_dock.js` phase branches; `state.js` / `player_mats.js` (`phase === 3` → `phase === 6`); `compiler.js`. Show the Release Bandwidth counter on the Scanned Box.
- **Data and tests:** setup screen and serializer use flat 8 Secrets; update `schemas.py`, `tests/test_web_api.py` and `tests/test_variants_and_web.py`.

### Step 5 — Print-and-Play (`pnp/generate_pnp.py`)
- **New six-phase player aid** replacing the current Phase 2/3 strips (around lines 1209 and 1293–1295).
- **Setup text** (lines 770, 1456–1458): 4P goes from 12 to 8 Secrets.
- **Re-timed card text:** about 12 strings ("Phase 3A Income", "Phase 2"), plus the contractor note "Returns to supply after Phase 2" → "after Phase 4".
- **Version-transition panel** (line 1081): "P2B and P3" → "Phases 3–6".
- **Player mat:** add a Scanned Box annotation showing the arrows "In Production → Scanned → Ready (≤ Release Bandwidth)".
- Regenerate the PDFs. Graphic-designer layout review.

### Step 6 — Tests
New `tests/test_v340_six_phase_sequence.py`:
- Green no longer removes income.
- Contractor `+$1` pays.
- Corruption cash loss lands before income.
- Phase 2 Patient Zero skips income.
- A Phase 2 breach still lets survivors run Phases 3–6.
- Singularity skips Phases 3–6.
- Buffer overflow still pays income.
- Burn Notice resolves before Blue.
- Phase 5 order, Release Bandwidth cap and Emergency Hotfix & Magnetic Splice step.
- Purchases go to Ready.
- Flat 8 Secrets setup (DTO 9).

Re-pin any v0.33 default-sequence tests to the legacy configuration.

### Step 7 — Validation & docs
- **`scripts/run_v340_telemetry_sweep.py`:** 3,000 games per pod, all 5 bots, companies and White Hats. Check the D5 guardrails, with 4P pacing as the main watch item.
- **`FINDINGS.md`:** Phase 42 entry covering the investigation sweeps (v0.33 vs Income-first vs Scanned routing, 12 vs 8 Secrets), the v0.34 sweep and the rationale.
- **`PLAN.md`:** add **Phase 42: Six-Phase Round Sequence, Release Bandwidth Routing & Flat Starting Secrets (`v0.34.0`)** with checkboxes.
- **Spec:** `docs/specs/v340_six_phase_round_sequence_spec.md`, written by the principal engineer.

---

## 4. SDLC Routing (per `PLAN.md` §2)
1. **game-designer:** this plan plus the investigation sweeps. ✅ Signed off by user 2026-11-05.
2. **principal-engineer:** v0.34 technical spec.
3. **senior-engineer ↔ staff-engineer:** Steps 2–4 and 6, with code review.
4. **product-owner:** scenario walkthroughs (corruption plus Green double whammy, Phase 2 breach with a finished round, Singularity round, buffer overflow, Scanned overflow beyond Release Bandwidth).
5. **game-designer:** Step 7 sweep against the D5 guardrails.
6. **graphic-designer:** Step 5 PnP six-phase aid and Scanned Box annotation.

## 5. Risk Summary
| Risk | Likelihood | Mitigation |
|---|---|---|
| 4P games run short (< 8 rounds) under flat 8 Secrets | Medium–High | D5 pacing levers (no Secret changes), modeled one at a time |
| 2P Total Wipeout stays at ~16% (pre-existing) | Medium | Track in the sweep; separate tuning item if it persists |
| Release Bandwidth cap feels punitive early | Low–Medium | Starting pool (4) equals baseline bandwidth (4); purchases bypass the cap (O3) |
| Web phase renumbering breaks the UI state machine | Medium | Server phase enum plus API tests before the JS changes |
| Legacy regression tests break | Medium | `round_sequence` legacy configuration |
| Spook Burn Notice before Blue | Low–Medium | Watch in the v0.34 sweep (currently 47% win) |
