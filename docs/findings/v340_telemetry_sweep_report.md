# Rogue Agent v0.34.0 Telemetry Sweep Report
## Phase 42: Six-Phase Round Sequence, Release Bandwidth Routing & Flat Starting Secrets

**Date:** 2026-11-05
**Author:** Product Owner
**Target Version:** `v0.34.0` (uncommitted, staff-approved), measured against the `GameConfig.legacy_v033` baseline on identical seeds
**Total Matches:** 18,000. That is 3,000 per pod (2P, 3P, 4P) for each sequence, or 27,000 player-games per sequence.
**Seeds:** base seed `42`. Match seed = `42 + num_players*100000 + match_idx`, so 2P = 200042–203041, 3P = 300042–303041 and 4P = 400042–403041. Both sequences use the same seeds.
**Execution Runtime:** 103.2 s in total.
- Six-phase: 2P 13.0 s, 3P 18.0 s, 4P 23.2 s.
- Legacy: 2P 11.1 s, 3P 15.4 s, 4P 22.4 s.

**Script:** `scripts/run_v340_telemetry_sweep.py`
**Raw Telemetry Summary:** [v340_telemetry_summary.json](./v340_telemetry_summary.json)
**Plan / Spec:** [Six-phase plan (D5 guardrails)](../explorations/2026_11_six_phase_round_sequence_plan.md), [v0.34 spec](../specs/v340_six_phase_round_sequence_spec.md)

**Match setup** (identical to `run_v330_telemetry_sweep.py`):
- 5-bot rotation, shuffled into seats.
- `get_random_setup` STANDARD.
- Random Client Companies and White Hat Operatives.
- `starting_money=6`, 3 Gray + 1 Purple dice, 1 Purple reserve, `enable_corporate_asymmetry=True`.
- Six-phase uses `GameConfig()` (flat 8 Secrets, DTO 9). Legacy uses `GameConfig.legacy_v033(...)` (4P = 12 Secrets).

**Instrumentation:** observer wrappers are installed by the script only, with no engine edits:
- `phase3_income.collect_player_production_income`
- `phase3_income.resolve_spook_burn_notice`
- `phase4_attack_resolution.resolve_player_defense_and_wear` (plus the `legacy_v033` binding)
- `phase2_compiler.demote_player_dice_step2a`
- `phase5_pipeline_shift.graduate_scanned`

The wrappers are pass-throughs. Running 360 seeded games with and without them gave identical results (rounds, winner, end reason, final Secrets and money for every player). Six-phase native `RoundTelemetry` fields (`scanned_held_by_player`, `purple_star_triggers_per_round`, `income_by_player`) cross-check the wrapper counts.

**Metric definitions:**
- **Income per turn** is the `$` and `🔬` produced by `collect_player_production_income`, per survivor per round, measured the same way in both sequences. It excludes Signature Protocol effects. Native six-phase `income_by_player`, which includes the protocols, is reported separately.
- **Zero-income turn:** an income collection that yields `$0 + 0 🔬`.
- **Double-whammy round:** a player-round with both a corruption glitch (a Phase 2 corruption space removed at least one die from In Production) and unblocked Green > 0.
- **Win:** the player ranked 1st, counting a Total Wipeout's top-ranked player as the winner (same as v0.33). Colored dice owned counts non-Gray, non-White dice, Purple included.

---

### 1. D5 Guardrails

| Guardrail | Target | 2P Six-Phase | 2P Legacy | 3P Six-Phase | 3P Legacy | 4P Six-Phase | 4P Legacy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Mean / median rounds | 8–11 (both) | 8.30 / 9 **PASS** | 7.96 / 8 **FAIL** | 7.98 / 8 **FAIL** | 7.63 / 8 **FAIL** | 7.76 / 8 **FAIL** | 8.70 / 9 **PASS** |
| Singularity ending | ≤ 45% | 25.4% **PASS** | 17.3% **PASS** | 19.0% **PASS** | 10.1% **PASS** | 15.7% **PASS** | 34.7% **PASS** |
| Total Wipeout ending | ≤ 15% | 19.0% **FAIL** | 18.1% **FAIL** | 6.5% **PASS** | 6.2% **PASS** | 2.5% **PASS** | 0.8% **PASS** |
| Zero-income turns | ≤ 30% | 27.1% **PASS** | 36.8% **FAIL** | 25.8% **PASS** | 35.5% **FAIL** | 25.4% **PASS** | 41.5% **FAIL** |
| Bot win-rate spread | ≤ 45 pts | 34.5 **PASS** | 63.4 **FAIL** | 34.3 **PASS** | 57.2 **FAIL** | 31.2 **PASS** | 51.9 **FAIL** |
| Top-company win rate (no regression vs legacy, same seeds) | ≤ legacy | DTO 75.7% **FAIL** | DTO 72.0% (baseline) | DTO 65.0% **FAIL** | DTO 61.0% (baseline) | DTO 58.5% **FAIL** | DTO 53.2% (baseline) |

**Six-phase guardrail tally: 12 PASS, 6 FAIL.**
- Rounds fail in 3P and 4P.
- Total Wipeout fails in 2P.
- Top-company fails in every pod.

---

### 2. Pacing & Termination

| Metric | 2P Six | 2P Leg | 3P Six | 3P Leg | 4P Six | 4P Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Mean rounds | 8.30 | 7.96 | 7.98 | 7.63 | 7.76 | 8.70 |
| Median rounds | 9 | 8 | 8 | 8 | 8 | 9 |
| StDev | 1.59 | 1.58 | 1.63 | 1.60 | 1.72 | 1.31 |
| Min – Max | 3–11 | 3–11 | 3–11 | 3–11 | 3–11 | 5–11 |
| Patient Zero ending | 55.6% | 64.5% | 74.5% | 83.7% | 81.7% | 64.5% |
| Singularity ending | 25.4% | 17.3% | 19.0% | 10.1% | 15.7% | 34.7% |
| Total Wipeout ending | 19.0% | 18.1% | 6.5% | 6.2% | 2.5% | 0.8% |
| Round-limit ending | 0 | 0 | 0 | 0 | 0 | 0 |

**Round histogram (six-phase 4P vs legacy 4P):**

| Rounds | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Six-phase 4P | 17 | 107 | 207 | 416 | 465 | 617 | 689 | 430 | 52 |
| Legacy 4P | 0 | 0 | 34 | 148 | 375 | 631 | 917 | 732 | 163 |

**End phase (six-phase):** the phase in which the game ended.

| Pod | Phase 2 (Singularity / Phase 2 wipeout) | Phase 4 (Total Wipeout) | Phase 6 (completed Final Round) |
| :--- | :---: | :---: | :---: |
| 2P | 800 | 531 | 1,669 |
| 3P | 571 | 193 | 2,236 |
| 4P | 473 | 75 | 2,452 |

---

### 3. Economy

| Metric | 2P Six | 2P Leg | 3P Six | 3P Leg | 4P Six | 4P Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Player survival | 51.4% | 48.2% | 60.7% | 58.3% | 67.5% | 76.1% |
| Mean final Secrets (all players) | 1.24 | 1.05 | 1.81 | 1.69 | 2.25 | 3.41 |
| Mean final Secrets (survivors) | 3.15 | 3.20 | 3.46 | 3.55 | 3.67 | 4.84 |
| Income / turn (`$` + `🔬`) | 2.31 | 1.62 | 2.39 | 1.66 | 2.43 | 1.50 |
| — `$` / turn | 1.83 | 1.25 | 1.90 | 1.28 | 1.93 | 1.16 |
| — `🔬` / turn | 0.48 | 0.37 | 0.49 | 0.38 | 0.50 | 0.34 |
| Income / turn incl. Signature Protocols (native `income_by_player`) | 2.33 | — | 2.40 | — | 2.44 | — |
| Zero-income turns | 27.1% | 36.8% | 25.8% | 35.5% | 25.4% | 41.5% |
| Double-whammy player-rounds | 9,195 | 8,533 | 12,594 | 11,525 | 16,040 | 18,975 |
| — per player-game | 1.53 | 1.42 | 1.40 | 1.28 | 1.34 | 1.58 |
| Income in double-whammy rounds | 1.32 | 0.47 | 1.44 | 0.49 | 1.51 | 0.42 |
| Colored dice owned at end | 2.03 | 1.19 | 2.15 | 1.28 | 2.19 | 1.03 |
| Unblocked Green per player-game | 11.73 | 11.07 | 10.85 | 10.16 | 10.30 | 12.88 |

Combined player survival is 61.7% six-phase vs 64.0% legacy.

---

### 4. Win & Survival Rates

#### 4.1 Bots (win % / survival %)

| Bot | 2P Six | 2P Leg | 3P Six | 3P Leg | 4P Six | 4P Leg | Combined Six | Combined Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| AdaptiveBalancedBot | 62.4 / 66.7 | 73.6 / 70.2 | 50.2 / 77.2 | 62.2 / 82.8 | 40.9 / 85.0 | 54.3 / 93.5 | **48.8 / 78.4** | 61.2 / 84.8 |
| AccelerationistBot | 64.8 / 65.0 | 75.2 / 67.2 | 40.6 / 71.6 | 45.3 / 72.0 | 30.0 / 76.4 | 28.2 / 85.2 | **41.2 / 72.3** | 44.4 / 76.8 |
| RecklessSaboteurBot | 42.5 / 44.7 | 31.8 / 34.9 | 30.4 / 59.4 | 23.6 / 51.1 | 24.6 / 72.7 | 16.1 / 78.6 | **30.5 / 62.0** | 22.1 / 59.7 |
| SecOpsTurtleBot | 50.1 / 54.3 | 57.5 / 56.3 | 29.6 / 63.9 | 30.6 / 69.8 | 19.8 / 71.1 | 24.0 / 85.8 | **29.8 / 65.0** | 33.7 / 73.9 |
| VentureGreedBot | 30.2 / 26.4 | 11.8 / 12.5 | 15.9 / 31.6 | 4.9 / 15.7 | 9.7 / 32.3 | 2.4 / 37.2 | **16.3 / 30.8** | 5.4 / 24.5 |

#### 4.2 Client Companies (win % / survival %)

| Company | 2P Six | 2P Leg | 3P Six | 3P Leg | 4P Six | 4P Leg | Combined Six | Combined Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| DTO | 75.7 / 75.2 | 72.0 / 68.7 | 65.0 / 82.8 | 61.0 / 78.7 | 58.5 / 87.9 | 53.2 / 89.7 | **64.4 / 83.4** | 59.9 / 81.4 |
| HELIX | 55.9 / 56.8 | 53.1 / 52.5 | 39.1 / 68.5 | 35.2 / 61.8 | 27.6 / 72.2 | 26.3 / 80.1 | **37.9 / 67.5** | 35.4 / 67.6 |
| PROMETHEUS | 55.1 / 56.7 | 53.4 / 49.6 | 33.9 / 64.9 | 33.5 / 61.5 | 25.0 / 71.9 | 23.2 / 76.7 | **34.7 / 66.2** | 33.4 / 65.6 |
| MERIDIAN | 52.9 / 53.8 | 48.4 / 46.9 | 29.5 / 61.3 | 30.5 / 58.0 | 20.6 / 69.6 | 22.6 / 77.8 | **30.7 / 63.3** | 31.0 / 64.3 |
| OMNIDYNE | 34.0 / 34.2 | 29.9 / 28.3 | 15.5 / 40.5 | 11.6 / 31.4 | 10.5 / 50.4 | 7.9 / 57.9 | **17.3 / 43.6** | 14.0 / 42.6 |
| AEGIS | 27.1 / 32.4 | 43.3 / 43.6 | 15.3 / 45.0 | 27.3 / 57.4 | 8.5 / 53.4 | 17.3 / 74.5 | **14.9 / 45.9** | 26.4 / 62.0 |

#### 4.3 White Hat Operatives (win % / survival %)

| Operative | 2P Six | 2P Leg | 3P Six | 3P Leg | 4P Six | 4P Leg | Combined Six | Combined Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| The Spook | 65.1 / 66.5 | 62.7 / 61.5 | 48.7 / 73.7 | 48.1 / 71.3 | 37.5 / 78.7 | 37.8 / 85.3 | **47.4 / 74.3** | 46.8 / 75.3 |
| The Acoustic | 52.9 / 55.4 | 51.9 / 50.9 | 31.6 / 62.9 | 32.1 / 59.8 | 22.9 / 69.2 | 22.0 / 76.2 | **32.4 / 64.1** | 32.0 / 65.1 |
| The Cipher | 46.5 / 48.1 | 47.4 / 45.6 | 30.7 / 59.0 | 32.6 / 57.7 | 23.2 / 65.2 | 24.5 / 75.0 | **30.8 / 59.4** | 32.2 / 62.8 |
| The Phreaker | 43.0 / 45.6 | 45.7 / 43.5 | 30.7 / 57.0 | 31.2 / 55.1 | 24.0 / 64.8 | 24.0 / 73.2 | **30.5 / 57.9** | 31.2 / 60.6 |
| The Prodigy | 46.7 / 48.8 | 47.2 / 45.3 | 30.2 / 57.5 | 29.7 / 54.4 | 22.3 / 64.0 | 20.7 / 74.3 | **30.3 / 58.5** | 29.5 / 61.3 |
| The Operator | 45.4 / 44.0 | 45.0 / 42.4 | 28.3 / 54.5 | 26.5 / 51.5 | 20.0 / 63.2 | 21.0 / 72.6 | **28.6 / 55.9** | 28.3 / 58.7 |

---

### 5. Watch Items

#### 5.1 The Spook & Purple ★ double triggers (OQ-17)
- Spook win rate is 47.4% six-phase vs 46.8% legacy (combined). By pod: 65.1 / 48.7 / 37.5% vs 62.7 / 48.1 / 37.8%.
- **Purple ★ double triggers are rare.** Player-rounds with 2 or more Purple ★ dice In Production at Phase 3 (native `purple_star_triggers_per_round ≥ 2`):

  | Pod | Player-rounds | Share |
  | :--- | :---: | :---: |
  | 2P | 125 of 48,065 | 0.26% |
  | 3P | 168 of 69,934 | 0.24% |
  | 4P | 227 of 91,049 | 0.25% |

- **Spook-specific double-trigger turns:** 19 / 31 / 48, out of 8,323 / 11,640 / 15,228 Spook income turns (about 0.25–0.3%).
- **Burn Notice uses are low:**

  | Sequence | 2P | 3P | 4P | Uses per game |
  | :--- | :---: | :---: | :---: | :---: |
  | Six-phase | 159 | 232 | 285 | 0.05 / 0.08 / 0.10 |
  | Legacy | 202 | 272 | 479 | 0.07 / 0.09 / 0.16 |

- Burn Notice never targeted an In Production die (0 uses on In Production dice), even though OQ-3 allows it.

#### 5.2 Aegis (Release Bandwidth 3 vs a 4-die starting pool)
- Aegis win rate is **14.9% six-phase vs 26.4% legacy** (combined). Survival is 45.9% vs 62.0%.
- By pod, Aegis wins 27.1 / 15.3 / 8.5% six-phase vs 43.3 / 27.3 / 17.3% legacy.
- This is the largest company-level shift in the sweep.
- **Aegis graduation was capped by Release Bandwidth in 32–34% of its Phase 5 graduations.** Aegis averaged 0.40–0.43 dice held in Scanned per player-round. Every other company was capped in 3–20% of graduations:

  | Company | Capped (2P / 3P / 4P) | Held per player-round (2P / 3P / 4P) |
  | :--- | :---: | :---: |
  | AEGIS | 32.3 / 34.0 / 33.2% | 0.40 / 0.43 / 0.42 |
  | MERIDIAN | 18.9 / 19.3 / 19.8% | 0.24 / 0.25 / 0.26 |
  | DTO | 11.5 / 13.3 / 12.4% | 0.14 / 0.17 / 0.15 |
  | HELIX | 12.6 / 11.8 / 11.3% | 0.16 / 0.14 / 0.14 |
  | PROMETHEUS | 9.2 / 9.6 / 10.2% | 0.11 / 0.12 / 0.13 |
  | OMNIDYNE | 3.6 / 3.7 / 3.4% | 0.06 / 0.06 / 0.06 |

#### 5.3 Scanned Box holding and the Release Bandwidth cap

| Metric | 2P Six | 3P Six | 4P Six | Legacy (all pods) |
| :--- | :---: | :---: | :---: | :---: |
| Dice held in Scanned per player-round (after graduation) | 0.185 | 0.193 | 0.192 | 0.000 |
| Graduations capped by Release Bandwidth | 14.7% | 15.2% | 15.0% | 0.0% |

The native `scanned_held_by_player` mean matches the wrapper exactly.

Over a mean game of about 8 rounds, this works out to roughly 1.5 dice-rounds held per player-game. The plan projected about 1.8.

#### 5.4 Release Track adoption (final Release Track level)

| Level | 2P Six | 2P Leg | 3P Six | 3P Leg | 4P Six | 4P Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Level 0 | 42.3% | 73.8% | 43.3% | 73.2% | 42.5% | 72.9% |
| Level 1 | 47.3% | 26.3% | 46.4% | 26.8% | 47.2% | 27.1% |
| Level 2 | 10.5% | 0.0% | 10.3% | 0.0% | 10.2% | 0.0% |
| Level ≥ 1 | 57.7% | 26.3% | 56.7% | 26.8% | 57.5% | 27.1% |

#### 5.5 White Contractor dice

| Metric | 2P Six | 2P Leg | 3P Six | 3P Leg | 4P Six | 4P Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Contractor hires per game | 8.11 | 10.47 | 11.85 | 15.46 | 15.49 | 21.36 |
| Contractor hires per player-game | 4.06 | 5.24 | 3.95 | 5.15 | 3.87 | 5.34 |
| Contractor `+$1` payouts per game | 0.96 | 0.00 | 1.46 | 0.00 | 1.91 | 0.00 |

In legacy, contractors expire before income, so their `+$1` face never pays.

#### 5.6 Unpaid Ransom Leaks

Ransom leaks per player-game are 2.36 / 2.16 / 2.02 six-phase vs 2.77 / 2.56 / 3.27 legacy. That is 15% / 16% / 38% lower.

#### 5.7 Final Round trigger phase (six-phase)
The Final Round was triggered in Phase 2 or Phase 4:

| Pod | Phase 2 | Phase 4 |
| :--- | :---: | :---: |
| 2P | 111 | 1,618 |
| 3P | 124 | 2,144 |
| 4P | 130 | 2,346 |

Phase 4 accounts for 93–95% of Final Round triggers.

#### 5.8 Total Wipeout ranking: deciding tiebreaker level
The level is the first key that differs between ranks 1 and 2.

| Deciding key | 2P Six (n=569) | 3P Six (n=195) | 4P Six (n=76) | 2P Leg (n=544) | 3P Leg (n=186) | 4P Leg (n=24) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Legacy breach-depth score | — | — | — | 392 | 122 | 12 |
| Money | 95 | 35 | 19 | 9 | 3 | 0 |
| Ready Colored dice | 74 | 20 | 12 | 14 | 7 | 0 |
| Research | 230 | 87 | 26 | 38 | 18 | 1 |
| Fewest Under Development | 113 | 28 | 11 | 40 | 17 | 4 |
| Fully shared (no key separates) | 57 (10.0%) | 25 (12.8%) | 8 (10.5%) | 51 | 19 | 7 |

#### 5.9 R2 / R3 / B1 bonuses forfeited by the In Production requirement
- **0 forfeitures** in every six-phase pod.
- A forfeiture means an R2/R3/B1 face that was rolled, is no longer In Production at Phase 4 with its face intact, and whose damage condition was met.
- R2/R3/B1 faces still In Production at Phase 4: 722 / 936 / 1,107 six-phase vs 264 / 338 / 547 legacy.
- Dice removed by corruption have their face cleared in both sequences. The only Phase 3 removal paths are Y3 and Burn Notice, and Burn Notice never hit an In Production die.

#### 5.10 Burn Notice uses
See §5.1.

---

### 6. Outlier Seeds

Replay any of these with:

```
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v340_telemetry_sweep.py --replay <seed> --players <N> --seq six|legacy
```

The complete lists are in the JSON under `results.<SEQ>.<NP>.outliers`.

| Category | Six-phase | Legacy |
| :--- | :--- | :--- |
| **Round ≤ 3, 2P** | 6, all Patient Zero: 200135, 200295, 200875, 201050, 201565, 201573 | 6: 200745, 200968, 201345, 201573, 202918, 202985 |
| **Round ≤ 3, 3P** | 8: 300732, 301044, 301316, 301756, 302009, 302292, 302472, 302606 | 10: 300732, 300741, 301446, 302009, 302496, 302606, 302717, 302816, 302827, 302936 |
| **Round ≤ 3, 4P** | 17: 400046, 400192, 400242, 400407, 400427, 400603, 401367, 401752, 402051, 402155, 402167, 402191, 402313, 402326, 402598, 402920, 402953 | 0 |
| **≥ 14 rounds** | 0 (max 11) | 0 (max 11) |
| **4P < 6 rounds** | 331 (11.0%), all Patient Zero: 17 at R3, 107 at R4, 207 at R5. First seeds: 400046, 400048, 400051, 400066, 400085, 400103, 400135, 400141 | 34 (1.1%), all Patient Zero at R5. First seeds: 400046, 400158, 400253, 400407 |

Spot check, seed 400046 (4P):
- **Six-phase:** VentureGreedBot reaches 0 Secrets at R3 (8 → 5 → 3 → 0, from Blue). The game ends at R3.
- **Legacy, same seed:** the same bot starts at 12 Secrets and breaches at R5.

The trace is consistent with the rules. No anomaly was found.

---

### 7. Observations for Engineering (no balance recommendations)

1. **Fully shared Total Wipeout ranks are credited to the lowest seat index.**
   - When no tiebreaker separates ranks 1 and 2, the stable sort leaves player-index order intact. `winner_id` then becomes the lower-index player, even though the rules call the result "shared".
   - This happened in 57 / 25 / 8 six-phase games (about 10–13% of wipeouts) and 51 / 19 / 7 legacy games.
   - It slightly inflates seat-0 win attribution in all win-rate tables (at most about 1.9% of 2P games).
   - This is a scoring/telemetry representation issue (`EndGameResult` has a single `winner_id`), not a rule-logic defect.
   - Repro: run any 2P seed from the JSON with `wipeout_tiebreak_level == "shared"`, or filter with `tiebreak_level()` in the script.
2. **The code-level key `patches` backs the canonical Research (`🔬`) tiebreaker.** This is noted only so readers can map the JSON keys to terms (the JSON uses `patches`).
3. **No invariant violations were observed.** There were 0 round-limit stalls, and the native telemetry agreed with the wrapper counts (Scanned held, income).

### 8. Reproduction

```
cd /home/mike/antigravity/rogue-agent
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_v340_telemetry_sweep.py --games 3000 --seed 42 --json docs/findings/v340_telemetry_summary.json
```

The output is deterministic: two full runs produced identical headline metrics.
