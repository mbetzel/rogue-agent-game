# Technical Architecture Specification: Phase 34 (v0.27.0)
## Per-Version Corruption Track Recalibration

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation  
**Target Version:** `v0.27.0`  
**Dependencies:** [RULES.md](../../RULES.md), [PLAN.md](../../PLAN.md), [v260_variable_dice_costs_spec.md](./v260_variable_dice_costs_spec.md)  
**Target Components:**
- `sim/entities.py`
- `web/static/js/components/modals.js`
- `pnp/generate_pnp.py`
- `tests/test_v270_track_recalibration.py`

---

## 1. Executive Summary & Architectural Motivation

### 1.1 The Inverted & Mild Track Friction Anomaly
Following the economic calibration of `v0.26.0` (reducing starting capital from $7 to $4 and establishing dynamic module costs $5–$7), the early game economy functions with tight operational liquidity ($0.06–$0.20 ending capital). However, investigation into mid- and late-game threat resolution revealed an operational disconnect between mature dice pools and Corruption Track penalties:

1. **Inverted Friction on `v2.0` Transition:**
   - In `v1.0 Script Kiddie`, Space 2 inflicts **"All lose $2 + Add 1K"** against a $4 starting economy (a 50% capital drain).
   - Upon compiling into `v2.0 Ransomware-as-a-Service (RaaS)`, Space 1 inflicts only **"All lose $1"**. The financial pressure paradoxically *drops* by 50% at the exact moment players are deploying 5–6 dice and generating higher revenue.
2. **Mild Friction in `v3.0`:**
   - In `v3.0 Zero-Day Override`, Space 2 inflicts only **"All lose $2 + Add 1K"** (with 0 patch deduction).
   - In late game (rounds 7–10), players roll 6–8 dice and generate $6–$10 in Phase 3. A static $2 cash loss fails to pressure mature firms.
3. **The Red Ransomware Immunity Effect:**
   - Because late-game track spaces left surplus liquidity untouched, players entering Phase 2 defense routinely carried $1–$2 in spare capital.
   - When unblocked Red Ransomware cubes exited the tower, players casually paid the $1 per cube from excess cash, completely muting the existential threat of Red Ransomware.

### 1.2 Approved Architectural Decisions
Rather than adding rules bloat or complex card directives, `v0.27.0` strictly recalibrates the printed values on the Standard Profile (Profile 1) Corruption Tracks to match the expanding economy:

```
+-----------------------------------------------------------------------------------------+
|                       PHASE 34 CORRUPTION TRACK RECALIBRATION                           |
+-----------------------------------------------------------------------------------------+
|  v2.0 RaaS Space 1:                All lose $1      -->  All lose $2                    |
|  v2.0 RaaS Space 4:                Lose $2 & 1 🔧   -->  Lose $3 & 1 🔧 (+ Add 1K)      |
|  v3.0 Zero-Day Override Space 2:   All lose $2      -->  Lose $3 & 1 🔧 (+ Add 1K)      |
|  v3.0 Corrupted Kernel Space 2:    Lose $2 & 1 🔧   -->  Lose $3 & 1 🔧 (+ Add 1K)      |
+-----------------------------------------------------------------------------------------+
```

By draining capital buffers immediately prior to Step 2B threat resolution, late-game unblocked Red Ransomware cubes ($1 each) directly threaten firm solvency and leak into Corporate Secrets when defenses fail.

---

## 2. Invariant Specifications

### `INV-TRACK-CALIB-01`: Standard Profile Track Definitions
In `sim/entities.py`, the `get_all_version_cards(profile="STANDARD")` factory must construct the `corruption_track` tuple with the following exact specifications:
- **`v2.0 RaaS` Space 1 (`index=1`):**
  - `label`: `"All lose $2"`
  - `lose_money`: `2`
  - `lose_patches`: `0`
  - `add_cubes`: `{}`
- **`v2.0 RaaS` Space 4 (`index=4`):**
  - `label`: `"Lose $3 & 1 🔧 + Add 1K"`
  - `lose_money`: `3`
  - `lose_patches`: `1`
  - `add_cubes`: `{CubeColor.BLACK: 1}`
- **`v3.0 Zero-Day Override` Space 2 (`index=2`):**
  - `label`: `"Lose $3 & 1 🔧 + Add 1K"`
  - `lose_money`: `3`
  - `lose_patches`: `1`
  - `add_cubes`: `{CubeColor.BLACK: 1}`
- **`v3.0 Corrupted Kernel` Space 2 (`index=2`):**
  - `label`: `"Lose $3 & 1 🔧 + Add 1K"`
  - `lose_money`: `3`
  - `lose_patches`: `1`
  - `add_cubes`: `{CubeColor.BLACK: 1}`

### `INV-TRACK-AGGR-01`: Aggressive Profile Consistency
In `sim/entities.py`, the `profile="AGGRESSIVE"` factory must maintain parity with or exceed the Standard Profile:
- `v2.0 RaaS` Space 1: `lose_money: 2`, `label: "All lose $2"`
- `v2.0 RaaS` Space 4: `lose_money: 3, lose_patches: 1`, `label: "Lose $3 & 1 🔧 + Add 1K"`
- `v3.0 Zero-Day Override` Space 2: `lose_money: 3, lose_patches: 1`, `label: "Lose $3 & 1 🔧 + Add 1K"`
- `v3.0 Corrupted Kernel` Space 2: `lose_money: 3, lose_patches: 1`, `label: "Lose $3 & 1 🔧 + Add 1K"`

### `INV-TRACK-CAPACITY-01`: Pacing Invariance
Track capacities remain strictly immutable across player counts:
- `v1.0`: exactly 4 spaces
- `v2.0`: exactly 5 spaces
- `v3.0`: exactly 6 spaces
Total black cubes to Singularity: exactly 15 cubes.

### `INV-STEP2A-DEDUCTION-01`: Sequential Step 2A Threat Resolution
In `sim/engine/phase2_threat.py`, `resolve_corruption_space()` executes before Step 2B attack resolution. When a black cube covers a recalibrated space:
- Player capital must decrement by `space.lose_money` (floored at `$0`).
- Player patch tokens must decrement by `space.lose_patches` (floored at `0`).
- Black cubes added to `add_cubes` must enter the staging cup for subsequent compilation.

---

## 3. Component Updates

### 3.1 `sim/entities.py`
Update `get_all_version_cards()` for the Standard Profile:
1. `RAAS` `corruption_track[0]` updated to `CorruptionSpace(index=1, label="All lose $2", lose_money=2)`.
2. `RAAS` `corruption_track[3]` updated to `CorruptionSpace(index=4, label="Lose $3 & 1 🔧 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1})`.
3. `ZERO_DAY_OVERRIDE` `corruption_track[1]` updated to `CorruptionSpace(index=2, label="Lose $3 & 1 🔧 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1})`.
4. `CORRUPTED_KERNEL` `corruption_track[1]` updated to `CorruptionSpace(index=2, label="Lose $3 & 1 🔧 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1})`.

### 3.2 `pnp/generate_pnp.py`
Update `VersionTileSpecs` dictionary or text rendering helpers for Rogue Agent Version cards so physical Print-and-Play assets render the updated space labels:
- `v2.0 RaaS`: Space 1 -> `"Lose $2"`, Space 4 -> `"Lose $3 & 1 🔧 + 1K"`
- `v3.0 Zero-Day`: Space 2 -> `"Lose $3 & 1 🔧 + 1K"`
- `v3.0 Kernel`: Space 2 -> `"Lose $3 & 1 🔧 + 1K"`

### 3.3 Documentation & Rules Draft
- `RULES.md` Section 6C: Update Profile 1 and Profile 2 table rows to reflect the calibrated track values.
- `PLAN.md`: Log Phase 34 milestone checklist and verification steps.
- `FINDINGS.md`: Log Section 22 with the 3,000-match verification telemetry sweep.

---

## 4. Verification Test Matrix (`tests/test_v270_track_recalibration.py`)

| Test ID | Invariant Tested | Verification Condition |
| :--- | :--- | :--- |
| `test_standard_raas_space_1` | `INV-TRACK-CALIB-01` | Verify `c.corruption_track[0]` has `lose_money == 2`, `label == "All lose $2"`. |
| `test_standard_raas_space_4` | `INV-TRACK-CALIB-01` | Verify `c.corruption_track[3]` has `lose_money == 3`, `lose_patches == 1`, `BLACK == 1`. |
| `test_standard_zeroday_space_2`| `INV-TRACK-CALIB-01` | Verify `c.corruption_track[1]` has `lose_money == 3`, `lose_patches == 1`, `BLACK == 1`. |
| `test_standard_kernel_space_2` | `INV-TRACK-CALIB-01` | Verify `c.corruption_track[1]` has `lose_money == 3`, `lose_patches == 1`, `BLACK == 1`. |
| `test_aggressive_profile_parity`| `INV-TRACK-AGGR-01` | Verify Aggressive Profile cards match or exceed calibrated thresholds. |
| `test_track_capacity_invariance`| `INV-TRACK-CAPACITY-01` | Verify 4, 5, 6 spaces across all version cards in both profiles. |
| `test_step2a_raas_space_1_execution`| `INV-STEP2A-DEDUCTION-01` | Trigger RaaS Space 1 in Step 2A; assert player cash decrements by exactly $2 (min $0). |
| `test_step2a_zeroday_space_2_execution`| `INV-STEP2A-DEDUCTION-01` | Trigger Zero-Day Space 2; assert player cash decrements by $3 and patches decrement by 1. |
| `test_floor_at_zero` | `INV-STEP2A-DEDUCTION-01` | Player with $1 cash and 0 patches suffers Space 2; assert cash == 0, patches == 0, zero secret leak. |

---

## 5. Acceptance Criteria
1. 100% of existing 466 unit tests continue to pass.
2. Dedicated unit test suite `tests/test_v270_track_recalibration.py` passes 100%.
3. 3,000-match Monte Carlo sweep across 2P, 3P, and 4P pods confirms:
   - Match duration remains inside 8.0–9.0 rounds target corridor.
   - Pacing invariance preserved across pods.
   - Singularity rate remains in healthy 5%–20% corridor.
   - 0.00% early blowouts ($\le$ R3).
4. Physical PnP cards in `pnp/output/` regenerated and synchronized.
