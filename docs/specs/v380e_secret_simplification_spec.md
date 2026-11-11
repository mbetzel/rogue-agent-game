# Technical Architecture Specification: Package `v0.38e`
## Secret Face Simplification & Domain Processing Triggers

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation (SDLC Architecture Phase)  
**Target Version:** `v0.38e` Baseline  
**Dependencies:**
- [`secret_simplification_investigation.md`](file:///home/mike/.gemini/antigravity/brain/463e13ee-2a09-4597-8b11-be5b893b9457/secret_simplification_investigation.md)
- [`docs/specs/v380d_c2_green_clean_spec.md`](file:///home/mike/antigravity/rogue-agent/docs/specs/v380d_c2_green_clean_spec.md)
- [`docs/specs/v380_secret_faces_processing_box_spec.md`](file:///home/mike/antigravity/rogue-agent/docs/specs/v380_secret_faces_processing_box_spec.md)
- [`RULES.md`](file:///home/mike/antigravity/rogue-agent/RULES.md)
- [`GLOSSARY.md`](file:///home/mike/antigravity/rogue-agent/GLOSSARY.md)

**Target Components:**
- [`sim/config.py`](file:///home/mike/antigravity/rogue-agent/sim/config.py)
- [`sim/engine/secret_faces.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/secret_faces.py)
- [`sim/engine/phase4_attack_resolution.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/phase4_attack_resolution.py)
- [`sim/engine/phase5_pipeline_shift.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/phase5_pipeline_shift.py)
- [`sim/bots/secret_face_policy.py`](file:///home/mike/antigravity/rogue-agent/sim/bots/secret_face_policy.py)
- [`tests/test_v380e_secret_simplification.py`](file:///home/mike/antigravity/rogue-agent/tests/test_v380e_secret_simplification.py)

---

## 1. System Overview & Design Goals

### 1.1 Problem Statement & Background
Under `v0.38d`, the Secret face banking mechanics suffered from two distinct ergonomic and balance defects:
1. **Blue Asymmetry, Memory Burden & Phase 3 Timing Artifacts:**
   - Blue Secret banking yield was computed as $Y_{\text{Blue}} = \min(3, 1 + \mathbb{I}_{\text{blocked\_blue}} + \mathbb{I}_{\text{grid\_L3}})$.
   - In 61.9% of rounds, players blocked zero Blue cubes, depressing Blue Expected Value to **1.458 Secrets/bank** and dragging Blue Client Company win rate down to **20.3% in 4P**.
   - Phase 4 Step 1 forced an unnatural tracking rule: *"Remember how many Blue cubes you blocked this round."*
   - Instant-banking triggers in Phase 3 (*B3 Air-Gapped Backup*, *Jumper Diagnostics*, *Magnetic Splice*) required an explicit negative timing exception: *"A Blue die leaving in Phase 3 gets no block bonus (Phase 4 has not happened yet)."*
2. **Green Calculation Friction & Early/Late Distortion:**
   - Green Secret yield was computed as $Y_{\text{Green}} = \max(0, 3 - g)$ followed by cleaning 1 Glitched Shield Slot ($g \leftarrow \max(0, g - 1)$).
   - This required players to track order-of-operations (evaluating before cleaning).
   - Clean boards early in the match yielded a runaway 3 Secrets, while late-game corrupted boards suffered feel-bad 0-secret payouts (4.4% of banks under old rules).

### 1.2 Approved Architecture: The Symmetric 4-Color Domain System
The `v0.38e` architecture establishes a clean, unified foundation across all four Secret-bearing module dice:

* **Universal Baseline Yields:**
  - **Red, Blue, Green Module Dice:** Flat **`+2` Corporate Secrets**.
  - **Purple Proprietary Specialist Die:** Flat **`+1` Corporate Secret**.
* **Four Dedicated Domain Triggers (Fired Upon Leaving the Processing Box):**
  - **Red (Market Domain):** Fires the **Market Share Track** scoring (**Market Leader Bonus**: 1st place `+3`, 2nd place `+1` Corporate Secrets once per round at the end of Phase 5).
  - **Blue (Hardware Defense Domain):** Triggers a hardware synergy bonus from the **Defense Grid Track** (**`+1` Corporate Secret if Defense Grid $\ge$ Level 3**, maximum `+3`).
  - **Green (System Integrity Domain):** Cleans **`1` Glitched Shield Slot** on the player's Company Terminal Mat ($g \leftarrow \max(0, g - 1)$).
  - **Purple (Specialist Baseline):** No domain trigger (pure specialist baseline).

```mermaid
flowchart TD
    subgraph UnderDevelopment ["Under Development Pipeline"]
        PB["Processing Box"] -->|Conveyor Triage (P5)<br/>B3 Air-Gapped / Jumper (P3)<br/>Magnetic Splice (P5)| SB["Scanned Box"]
    end

    PB -->|Red Die| YR["+2 Corporate Secrets"]
    PB -->|Blue Die| YB["+2 Corporate Secrets<br/>(+1 if Defense Grid >= L3)"]
    PB -->|Green Die| YG["+2 Corporate Secrets"]
    PB -->|Purple Die| YP["+1 Corporate Secret"]

    YR -->|"Domain Trigger"| TR["Trigger Market Leader Bonus<br/>(Phase 5 Step 5: 1st +3, 2nd +1)"]
    YB -->|"Domain Trigger"| TB["Check Defense Grid Level >= 3<br/>(Max 3 Corporate Secrets)"]
    YG -->|"Domain Trigger"| TG["Clean 1 Glitched Shield Slot<br/>(g = max(0, g - 1))"]
    YP -->|"Domain Trigger"| TP["No Trigger"]
```

### 1.3 Key Benefits & Design Validation
- **Blue EV Restored:** Blue Secret EV rises from **1.458 to 2.077** (+0.619), restoring Blue Client Company win rate to **26.1% (4P) / 48.5% (2P)**, directly hitting the target 25% / 50% fair-share guardrails.
- **Cognitive Load Eliminated:** Completely deletes the mid-round memory requirement in Phase 4 Step 1.
- **Timing Parity Across Phases:** Instant banking in Phase 3 (*B3*, *Jumper Diagnostics*) uses the identical formula as Phase 5 Conveyor Triage; no special-case timing rules.
- **Order-Independence on Green:** Because Green Secret yield is unconditionally 2, the order of counting vs cleaning is mathematically moot.

---

## 2. Invariants

- **`INV-V38E-01` (Universal Baseline Secret Yields):**  
  Every die bearing a Secret face that leaves the Processing Box and banks its yield produces an unconditional baseline yield: Red = `2`, Blue = `2`, Green = `2`, Purple = `1`.
- **`INV-V38E-02` (Blue Defense Grid Trigger & Memory Liberation):**  
  A Blue die banking its Secret evaluates only `p.defense_level >= 3`. If True, it awards `+1` additional Corporate Secret, capped at `secret_yield_blue_cap` (3). It shall never inspect `p.blocked_blue_this_round` or require attacks to have occurred.
- **`INV-V38E-03` (Phase 3 & Phase 5 Blue Banking Equivalence):**  
  Blue die banking triggered during Phase 3 (*B3 Air-Gapped Backup*, *Jumper Diagnostics*) and Phase 5 (Conveyor Triage, *Magnetic Splice*) produces identical yield for a given board state.
- **`INV-V38E-04` (Green Flat Yield & Mat Decontamination):**  
  A Green die banking its Secret awards exactly `secret_yield_green_base` (2) Corporate Secrets regardless of active `glitched_shield_slots`, and cleans exactly 1 Glitched Shield Slot ($g \leftarrow \max(0, g - 1)$), incrementing `slots_cleaned_by_green_triage` by the number of slots cleaned (0 or 1).
- **`INV-V38E-05` (Red Market Leader Bonus Trigger):**  
  A Red die banking its Secret awards `2` Corporate Secrets to its owner and sets `state.red_secret_banked_this_round = True`, triggering the single end-of-Phase-5 Market Leader Bonus award.
- **`INV-V38E-06` (Purple Pure Specialist Yield):**  
  A Purple die banking its Secret awards `1` Corporate Secret and fires zero board or track triggers.
- **`INV-V38E-07` (Non-Banking Exit Invariance):**  
  A die leaving the Processing Box without banking (e.g. discarded via *Burn Notice*, returned via *Return Colored Die*, or stranded at game end) awards `0` Corporate Secrets, cleans `0` glitched slots, and triggers `0` domain effects.
- **`INV-V38E-08` (Backwards Compatibility & Golden Parity):**  
  `GameConfig.v038d()`, `v038c()`, `v038b()`, `v038()`, and `v037()` remain completely unchanged in behavior and output, preserving golden fixtures and test suites.

---

## 3. Configuration Levers (`sim/config.py`)

### 3.1 New & Modified Fields on `GameConfig`

```python
# sim/config.py

@dataclass
class GameConfig:
    # Existing levers (retained with v0.37/v0.38d defaults):
    secret_yield_blue_base: int = 1               # Default in v0.38d; v0.38e sets to 2
    secret_yield_blue_block_bonus: int = 1        # Default in v0.38d; v0.38e sets to 0
    secret_yield_blue_grid_l3_bonus: int = 1      # Unchanged (1)
    secret_yield_blue_cap: int = 3                # Unchanged (3)
    secret_yield_green_base: int = 3              # Default in v0.38d; v0.38e sets to 2
    secret_yield_purple: int = 1                  # Unchanged (1)

    # New lever for Phase 52:
    secret_yield_green_glitch_penalty: bool = True
    """If True (v0.38d and earlier), Green Secret yield is max(0, green_base - glitched_shield_slots).
    If False (v0.38e), Green Secret yield is flat secret_yield_green_base unconditionally."""
```

### 3.2 Factory Method `GameConfig.v038e()`

```python
@classmethod
def v038e(cls, **overrides) -> "GameConfig":
    """v0.38 candidate 5 (Phase 52: Secret Face Simplification & Processing Triggers).
    Inherits all v0.38d rules (C2 setup, 1 starting glitched slot, Shogun Baffle physics,
    Green triage clean), and applies the simplified 4-color Secret architecture:
    - Red: flat +2 + Market Leader Bonus trigger
    - Blue: flat +2 (+1 if Defense Grid >= L3, cap 3; block bonus eliminated)
    - Green: flat +2 + clean 1 Glitched Shield Slot (glitch yield penalty eliminated)
    - Purple: flat +1 (no trigger)
    """
    for k, v in (
        ("secret_yield_blue_base", 2),
        ("secret_yield_blue_block_bonus", 0),
        ("secret_yield_blue_grid_l3_bonus", 1),
        ("secret_yield_blue_cap", 3),
        ("secret_yield_green_base", 2),
        ("secret_yield_green_glitch_penalty", False),
    ):
        overrides.setdefault(k, v)
    return cls.v038d(**overrides)
```

### 3.3 Validation Rules
In `_validate_secret_yields()`:
- `secret_yield_blue_base >= 0`
- `secret_yield_blue_block_bonus >= 0`
- `secret_yield_blue_grid_l3_bonus >= 0`
- `secret_yield_blue_cap >= secret_yield_blue_base`
- `secret_yield_green_base >= 0`
- `secret_yield_purple >= 0`
- `isinstance(secret_yield_green_glitch_penalty, bool)`

---

## 4. Module Contracts & Implementation Details

### 4.1 Secret Face Banking (`sim/engine/secret_faces.py`)

#### `secret_yield(cfg: GameConfig, p: PlayerState, color: Any) -> int`
Computes the Corporate Secrets yield for a die of `color` banking at the current state:

```python
def secret_yield(cfg: "GameConfig", p: "PlayerState", color: Any) -> int:
    color = DieColor(color) if not isinstance(color, DieColor) else color
    if color == DieColor.RED:
        flat = getattr(cfg, "red_secret_owner_yield", None)
        if flat is not None:
            return int(flat)
        share = int(p.market_share or 0)
        for min_share, y in cfg.secret_yield_red_tiers:
            if share >= min_share:
                return int(y)
        return 0

    if color == DieColor.BLUE:
        y = int(cfg.secret_yield_blue_base)
        if cfg.secret_yield_blue_block_bonus > 0 and int(getattr(p, "blocked_blue_this_round", 0)) > 0:
            y += int(cfg.secret_yield_blue_block_bonus)
        if int(p.defense_level) >= 3:
            y += int(cfg.secret_yield_blue_grid_l3_bonus)
        return min(int(cfg.secret_yield_blue_cap), y)

    if color == DieColor.GREEN:
        if getattr(cfg, "secret_yield_green_glitch_penalty", True):
            return max(0, int(cfg.secret_yield_green_base) - int(getattr(p, "glitched_shield_slots", 0)))
        return int(cfg.secret_yield_green_base)

    if color == DieColor.PURPLE:
        return int(cfg.secret_yield_purple)

    return 0
```

#### `bank(cfg: GameConfig, p: PlayerState, die: Die, state: Any = None) -> int`
Handles the transition of a die leaving the Processing Box:
1. Validates `die.secret_pending == True`.
2. Computes yield $Y$ via `secret_yield()`.
3. If `die.color == DieColor.GREEN` and `cfg.green_bank_cleans_slot`:
   - Invokes `clean_slots(p, 1, "green_triage")`.
4. If `die.color == DieColor.RED`:
   - Updates Red banking telemetry and flags `state.red_secret_banked_this_round = True`.
5. Clears `die.secret_pending = False`.
6. Increments player telemetry (`secret_faces_banked`, `secret_yield_hist`).
7. Awards $Y$ Corporate Secrets via `p.gain_secrets(Y, f"secret_face_{color}")`.
8. Returns $Y$.

### 4.2 Phase 4 Attack Resolution (`sim/engine/phase4_attack_resolution.py`)
- Tracking of `player.blocked_blue_this_round` remains in place in the simulation engine to maintain complete backwards compatibility for configs where `secret_yield_blue_block_bonus > 0`.
- In `RULES.md`, the reminder in Phase 4 Step 1 (*"Remember how many Blue cubes you blocked this round"*) is cleanly excised.

### 4.3 Phase 5 Pipeline Shift (`sim/engine/phase5_pipeline_shift.py`)
- Conveyor Triage (Step 4) and Magnetic Splice (Step 1) route through `secret_faces.bank()` unchanged.
- Market Leader Bonus (Step 5) fires if `state.red_secret_banked_this_round == True`, unchanged.

### 4.4 Bot & Policy Adjustments (`sim/bots/secret_face_policy.py`)

#### `marginal_block_value()`
Under `v0.38e`, heuristics evaluating attack block value must reflect the removal of Secret yield penalties:

```python
def marginal_block_value(color: CubeColor, rem: Dict[CubeColor, int], player: "PlayerState", state: "GameState",
                         attack: Dict[CubeColor, int], base: float) -> float:
    cfg = state.config
    r = int(rem.get(color, 0))
    if r <= 0:
        return base

    if color == CubeColor.BLUE:
        # If blue_block_bonus is 0 (v0.38e), no heuristic bonus is added;
        # Blue cubes are blocked solely to prevent immediate secret theft.
        if cfg.secret_yield_blue_block_bonus > 0:
            first_block = r >= int((attack or {}).get(CubeColor.BLUE, r))
            if player.blocked_blue_this_round == 0 and _pending(player, DieColor.BLUE) and first_block:
                base += SECRET_VALUE * cfg.secret_yield_blue_block_bonus * min(_pending(player, DieColor.BLUE),
                                                                            player.triage_bandwidth)
        return base

    if color == CubeColor.GREEN:
        if player.glitched_shield_slots >= player.defense_capacity:
            return 0.0  # Excess Green has no effect
        v = SHIELD_VALUE
        # If green_glitch_penalty is False (v0.38e), glitched slots do NOT reduce
        # Secret yield; Green is blocked solely to defend Shield Capacity.
        if getattr(cfg, "secret_yield_green_glitch_penalty", True) and player.glitched_shield_slots < cfg.secret_yield_green_base:
            v += SECRET_VALUE * min(_pending(player, DieColor.GREEN) + _owned(player, DieColor.GREEN) * 0.2,
                                    player.triage_bandwidth)
        return v

    # Red handling remains unchanged...
```

---

## 5. Telemetry & Ledger Guarantees

1. **`secret_yield_hist` Invariant Distribution:**
   - Under `v0.38e`, `secret_yield_hist["BLUE"]` shall only ever contain keys `"2"` and `"3"`.
   - `secret_yield_hist["GREEN"]` shall only ever contain key `"2"`.
   - `secret_yield_hist["RED"]` shall only ever contain key `"2"`.
   - `secret_yield_hist["PURPLE"]` shall only ever contain key `"1"`.
2. **`slots_cleaned_by_green_triage`:**
   - Continues to accurately track the count of slots cleaned across all Green banking events.
3. **State Cloning:**
   - `fast_clone()` maintains all state attributes with zero regression.

---

## 6. Test Suite Specifications (`tests/test_v380e_secret_simplification.py`)

The test suite must validate all invariants across the following dedicated test cases:

| Test Identifier | Invariant / Focus | Assertion Description |
| :--- | :--- | :--- |
| `test_v380e_config_defaults` | Lever Config | Verify `GameConfig.v038e()` initializes `blue_base=2`, `blue_block_bonus=0`, `green_base=2`, `green_glitch_penalty=False`. |
| `test_v380e_blue_yield_grid_l0_l2` | `INV-V38E-01`, `INV-V38E-02` | Defense Grid Levels 0, 1, 2 yield exactly `2` Corporate Secrets, regardless of `blocked_blue_this_round` (0 or >0). |
| `test_v380e_blue_yield_grid_l3_l4` | `INV-V38E-02` | Defense Grid Levels 3 and 4 yield exactly `3` Corporate Secrets (capped at 3). |
| `test_v380e_blue_phase3_instant_bank` | `INV-V38E-03` | *B3 Air-Gapped Backup* and *Jumper Diagnostics* bank Blue die in Phase 3 with identical yield to Phase 5. |
| `test_v380e_green_flat_yield_and_clean` | `INV-V38E-04` | Green die banks exactly `2` Secrets when $g=0, 1, 2, 3$; cleans 1 slot ($g \to g-1$); increments `slots_cleaned_by_green_triage`. |
| `test_v380e_red_yield_and_mlb_flag` | `INV-V38E-05` | Red die banks exactly `2` Secrets; flags `state.red_secret_banked_this_round = True`. |
| `test_v380e_purple_specialist_yield` | `INV-V38E-06` | Purple die banks exactly `1` Secret; zero board or track side-effects. |
| `test_v380e_stranded_and_burn_notice` | `INV-V38E-07` | Discarding pending die (*Burn Notice*) yields 0 secrets and cleans 0 slots. |
| `test_v380e_backwards_compatibility` | `INV-V38E-08` | `v038d` config produces `max(0, 3 - g)` for Green and checks `blocked_blue_this_round` for Blue. |

---

## 7. Documentation Updates Required (`RULES.md`)

### 7.1 Section 4: Phase 4 Step 1
* **Remove:** *"Remember how many Blue cubes you blocked this round (it raises Blue Secret face yields in Phase 5; cubes ignored by Baffle Echo were not blocked)."*
* **Target Wording:**
  > *Dice assigned to shields absorb attacks cleanly and remain deployed in **In Production**.*

### 7.2 Section 4: Phase 5 (Secret Face Yields)
* **Target Wording:**
  > #### Secret Face Yields `[TUNE]`
  > A die showing a **Secret face** banks its Secret when it leaves the **Processing Box** (Conveyor Triage, *Magnetic Splice*, *Jumper Diagnostics*, *B3 Air-Gapped Backup*): its owner gains **Corporate Secrets** by the die's color, using the game state at that moment:
  > * **Red:** `+2`.
  > * **Blue:** `+2`, plus `1` if your Defense Grid Track is at Level 3 or higher (maximum `+3`).
  > * **Green:** `+2`; then clean `1` of your **Glitched Shield Slots**.
  > * **Purple:** `+1`.
