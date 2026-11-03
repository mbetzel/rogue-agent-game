# Technical Architecture Specification: Phase 35 (v0.28.0)
## Asymmetric Corporate Terminal Mats, Hardware Bottlenecks & Research Economy

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation  
**Target Version:** `v0.28.0`  
**Dependencies:** [RULES.md](../../RULES.md), [PLAN.md](../../PLAN.md), [v270_corruption_track_recalibration_spec.md](./v270_corruption_track_recalibration_spec.md)  
**Target Components:**
- `sim/config.py`
- `sim/entities.py`
- `sim/engine/state.py`
- `sim/engine/phase1_boot.py`
- `sim/engine/phase2_threat.py`
- `sim/engine/phase3_ops.py`
- `sim/engine/core.py`
- `sim/bots/base.py` & all bot subclasses (`sim/bots/*.py`)
- `web/controller/` & `web/static/`
- `tests/test_v280_terminal_upgrades.py`
- `pnp/generate_pnp.py`

---

## 1. Architectural Motivation & Systemic Changes

### 1.1 The Single-Currency Agency Problem
Prior to `v0.28.0`, money (`$`) was the sole proactive currency in Phase 3A Operations. With module dice costing $5–$7, players who rolled $2–$4 had zero viable actions on their turn, creating passive "dead turns." Patch tokens (`🔧`) functioned solely as a reactive tax on glitches, restricted by a 3-token cap that discarded surplus tokens.

### 1.2 The Hardware Bottleneck Thesis
To prevent runaway dice pooling, previous versions restricted dice purchasing power. Under `v0.28.0`, the constraint shifts from artificial monetary poverty to **physical hardware bottlenecks on the player's Terminal Mat**:
1. **Defense Capacity (`defense_capacity`):** Limits how many dice may be assigned to Shields in Phase 1.
2. **CI/CD Pipeline Bandwidth:**
   - **Triage Bandwidth (`triage_bandwidth`):** Limits how many dice may move from Glitched $\to$ Scanned per round.
   - **Release Bandwidth (`release_bandwidth`):** Limits how many dice may move from Scanned $\to$ Ready per round.
3. **Research Economy (`🔬`):** Patches are replaced by uncapped Research tokens (`research_tokens`), which fund terminal hardware upgrades and convert directly into Corporate Secrets (Victory Points) via Cryptographic Patents.
4. **Corporate Asymmetry:** Each Client Company provides unique baseline hardware specifications and economic traits.

---

## 2. Invariant Specifications

### `INV-RESEARCH-UNCAPPED-01`: Uncapped Research Currency
- Patch tokens (`🔧`) are completely replaced by Research tokens (`🔬`). In code, `patches` / `patch_tokens` is transitioned to `research_tokens` in `PlayerState`.
- `research_tokens` has no upper bound. The end-of-round cap of 3 is eliminated.
- Track penalties (`lose_patches`) decrement `research_tokens` (floored at 0).
- Dice faces providing patches now yield `research_tokens`.

### `INV-DEF-CAP-01`: Defense Grid Shield Limit
- During Phase 1 Step 5 (Commit to In Production), the total number of dice assigned to Shield slots (`Red`, `Blue`, `Green`) by a player cannot exceed that player's `defense_capacity`.
- Any remaining rolled dice with shield faces that exceed `defense_capacity` cannot be committed to defense; if they possess no alternative income option, they are assigned to Income yielding 0 output.

### `INV-PIPE-GRAD-01`: Scanned Graduation Throughput
- In Phase 3B Step 1, at most `release_bandwidth` dice move from `scanned_dice` to `ready_for_release_dice`.
- Any excess dice in `scanned_dice` remain in `scanned_dice` for subsequent rounds.

### `INV-PIPE-TRIAGE-01`: Conveyor Triage Throughput
- In Phase 3B Step 2 (executed after Step 1 Scanned Graduation), at most `triage_bandwidth` dice move from `glitched_dice` to `scanned_dice`.
- Any excess dice in `glitched_dice` remain in `glitched_dice` for subsequent rounds.
- Newly triaged dice do not graduate in the same round; they remain in `scanned_dice` throughout the following round.

### `INV-UPGRADE-TRACK-01`: Terminal Mat Hardware Tracks
Each terminal mat possesses 3 tracks with levels $0 \to 1 \to 2$:
1. **`PIPELINE` Track:**
   - Level 0 $\to$ Level 1: Cost 2 `🔬`. Increases `triage_bandwidth` and `release_bandwidth` to 3.
   - Level 1 $\to$ Level 2: Cost 3 `🔬`. Increases `triage_bandwidth` and `release_bandwidth` to 4, and unlocks `emergency_hotfix` (once per Phase 3B, move 1 die from Glitched directly to Ready).
2. **`DEFENSE` Track:**
   - Level 0 $\to$ Level 1: Cost 2 `🔬`. Increases `defense_capacity` to 3.
   - Level 1 $\to$ Level 2: Cost 3 `🔬`. Increases `defense_capacity` to 4, and grants `passive_firewall` (absorb 1 attack cube of choice for free in Step 2B).
3. **`PATENT` Track:**
   - Level 0 $\to$ Level 1: Cost 2 `🔬`. Reduces patent filing cost from 4 `🔬` to 3 `🔬`.
   - Level 1 $\to$ Level 2: Cost 3 `🔬`. Reduces patent filing cost to 2 `🔬` and awards +$1 cash per patent filed.

### `INV-PATENT-CONV-01`: Cryptographic Patent Action
- In Phase 3A Operations, a player may execute `file_patent()`:
  - Deducts `patent_cost` Research tokens (`4` at Level 0, `3` at Level 1, `2` at Level 2).
  - Awards `+1 Corporate Secret`.
  - At Level 2, also awards `+$1` cash.
  - Can be performed multiple times per turn as long as the player has sufficient Research.

### `INV-ASYM-COMPANY-01`: Company Profiles & Baselines
The 6 Client Companies define starting terminal properties:
1. **`OMNIDYNE`:**
   - Starting Defense: 1
   - Starting Pipeline: Triage 3, Release 3 (Starts at Pipeline Level 1)
   - Starting Tracks: `pipeline_level=1`, `defense_level=0`, `patent_level=0`
2. **`AEGIS`:**
   - Starting Defense: 3 (Starts at Defense Level 1)
   - Starting Pipeline: Triage 1, Release 1
   - Starting Tracks: `pipeline_level=0`, `defense_level=1`, `patent_level=0`
3. **`MERIDIAN`:**
   - Starting Defense: 2
   - Starting Pipeline: Triage 2, Release 1
   - Starting Tracks: `pipeline_level=0`, `defense_level=0`, `patent_level=0`
   - Starting Cash: $+2$ bonus ($\$6$ starting money)
4. **`HELIX`:**
   - Starting Defense: 2
   - Starting Pipeline: Triage 2, Release 2
   - Starting Tracks: `pipeline_level=0`, `defense_level=0`, `patent_level=1` (Starts at Patent Level 1: 3 `🔬` cost)
   - Starting Research: $+2\ 🔬$ bonus
5. **`DTO`:**
   - Starting Defense: 2
   - Starting Pipeline: Triage 2, Release 2
   - Starting Tracks: `pipeline_level=0`, `defense_level=0`, `patent_level=0`
   - Starting Secrets: $+1$ Secret bonus
6. **`PROMETHEUS`:**
   - Starting Defense: 2
   - Starting Pipeline: Triage 2, Release 2
   - Starting Tracks: `pipeline_level=0`, `defense_level=0`, `patent_level=0`
   - Upgrade Trait: All track upgrades receive a $-1\ 🔬$ discount (min $1\ 🔬$).

### `INV-DIE-COST-01`: Recalibrated Module Market Costs
To enable meaningful pool scaling that stresses hardware throughput:
- Central Market Variant Costs:
  - R1: $4, R2: $5, R3: $4
  - B1: $4, B2: $5, B3: $4
  - G1: $4, G2: $4, G3: $4
  - Y1: $5, Y2: $5, Y3: $4
- Personal Reserve Purple Dice: $4 for all White Hat Operatives.

---

## 3. Data Model Changes

### 3.1 `PlayerState` (`sim/engine/state.py`)
Add fields:
```python
research_tokens: int = 0
defense_capacity: int = 2
triage_bandwidth: int = 2
release_bandwidth: int = 2
pipeline_level: int = 0  # 0, 1, 2
defense_level: int = 0   # 0, 1, 2
patent_level: int = 0    # 0, 1, 2
has_emergency_hotfix: bool = False
has_passive_firewall: bool = False
upgrade_discount: int = 0
```
Retain `patches` as a deprecated property forwarding to `research_tokens` for backwards compatibility during migration.

### 3.2 `Company` (`sim/entities.py`)
Add hardware configuration fields:
```python
starting_defense_capacity: int = 2
starting_triage_bandwidth: int = 2
starting_release_bandwidth: int = 2
starting_pipeline_level: int = 0
starting_defense_level: int = 0
starting_patent_level: int = 0
starting_cash_bonus: int = 0
starting_research_bonus: int = 0
starting_secrets_bonus: int = 0
upgrade_discount: int = 0
```

---

## 4. Verification Matrix (Test Suite: `tests/test_v280_terminal_upgrades.py`)

1. **`test_research_tokens_no_cap`**: Verify research accumulates $>3$ without being discarded in Phase 3B.
2. **`test_defense_capacity_enforcement`**: Attempt assigning 3 shield dice when `defense_capacity=2`; verify invariant enforces max 2 shields.
3. **`test_pipeline_triage_bandwidth`**: Place 4 dice in Glitched with `triage_bandwidth=2`; verify exactly 2 move to Scanned and 2 remain in Glitched.
4. **`test_pipeline_release_bandwidth`**: Place 4 dice in Scanned with `release_bandwidth=2`; verify exactly 2 move to Ready and 2 remain in Scanned.
5. **`test_upgrade_pipeline_track`**: Spend research to upgrade Pipeline to Level 1; verify bandwidths expand to 3.
6. **`test_upgrade_defense_track`**: Spend research to upgrade Defense to Level 1; verify capacity expands to 3.
7. **`test_patent_conversion_all_levels`**: Test `file_patent()` at Level 0 (4 `🔬`), Level 1 (3 `🔬`), and Level 2 (2 `🔬` + $1 cash).
8. **`test_corporate_asymmetry_initialization`**: Verify all 6 companies initialize with correct hardware, track levels, and starting bonuses.
9. **`test_prometheus_upgrade_discount`**: Verify Prometheus upgrades cost 1 `🔬` for L1 and 2 `🔬` for L2.
10. **`test_recalibrated_dice_costs`**: Verify new variant market costs ($4–$5) and reserve purple cost ($4).
