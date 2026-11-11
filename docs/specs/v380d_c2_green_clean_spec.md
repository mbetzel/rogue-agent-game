# Technical Architecture Specification: Package `v0.38d`
## Candidate C2 Early-Game Setup + Green-Clean Package (Variant B)

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation (SDLC Architecture Phase)  
**Target Version:** `v0.38d` Baseline  
**Dependencies:** 
- [`docs/findings/c2_green_clean_analysis.md`](file:///home/mike/antigravity/rogue-agent/docs/findings/c2_green_clean_analysis.md)
- [`docs/findings/early_game_pressure_modeling.md`](file:///home/mike/antigravity/rogue-agent/docs/findings/early_game_pressure_modeling.md)
- [`docs/specs/v380_secret_faces_processing_box_spec.md`](file:///home/mike/antigravity/rogue-agent/docs/specs/v380_secret_faces_processing_box_spec.md)
- [`RULES.md`](file:///home/mike/antigravity/rogue-agent/RULES.md)
- [`RULES_APPENDIX.md`](file:///home/mike/antigravity/rogue-agent/RULES_APPENDIX.md)
- [`GLOSSARY.md`](file:///home/mike/antigravity/rogue-agent/GLOSSARY.md)

**Target Components:**
- [`sim/config.py`](file:///home/mike/antigravity/rogue-agent/sim/config.py)
- [`sim/entities.py`](file:///home/mike/antigravity/rogue-agent/sim/entities.py)
- [`sim/engine/secret_faces.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/secret_faces.py)
- [`sim/engine/phase5_pipeline_shift.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/phase5_pipeline_shift.py)
- [`sim/engine/core.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/core.py)
- [`sim/engine/state.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/state.py)
- [`sim/engine/end_game.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/end_game.py)
- [`sim/bots/secret_face_policy.py`](file:///home/mike/antigravity/rogue-agent/sim/bots/secret_face_policy.py)
- [`tests/test_v380d_c2_green_clean.py`](file:///home/mike/antigravity/rogue-agent/tests/test_v380d_c2_green_clean.py)

---

## 1. Executive Summary & Mathematical Motivation

### 1.1 Problem Statement: Baseline `v038c` Pacing & Diluted Triage Mechanics
Under baseline `v038c` (`TowerMode.SHOGUN_BAFFLE`), early-game pressure was excessively mild:
- **Pacing Drag:** Matches dragged out to **10.00–10.10 rounds** across 2P, 3P, and 4P, exceeding the core design envelope of **8.5–9.5 rounds**.
- **Singularity Monopolization:** End triggers were heavily skewed, with Singularity claiming **65%–73%** of all game endings, while Patient Zero eliminated only 12%–19%.
- **Dilution of Glitched Shield Slots:** Telemetry revealed that **77% of all cleaned slots were erased automatically by Phase 5 Step 3 CI/CD graduation (`6.05` slots/seat)**. Players experienced `0.00` zero-capacity rounds and virtually never needed to actively triage or spend shield dice on mat repairs (`1.38` slots/seat).

### 1.2 Approved Package: Candidate C2 + Green-Clean Package (Variant B)
To restore authentic operational tension, eliminate passive automation, and cement Green's identity as the premier Research Powerhouse, the User and Game Designer approved **Package `v038d`**:

1. **Candidate C2 Early-Game Setup:**
   - **Compiler Setup Priming:** `4` cubes (`1R, 1B, 1G, 1K`).
   - **`v1.0` Starting Staging Cup:** `4` Attack Cubes (`2R, 1B, 1G` for *Script Kiddie*; `1R, 2B, 1G` for *Data Scraper*).
   - **Starting Glitched Shield Slot:** Every player begins Setup with `1` Glitched Shield Slot (`starting_glitched_shield_slots = 1`), leaving 1 clean Shield Slot and 1 Glitched Shield Slot out of baseline Defense Capacity 2.
2. **Elimination of Passive Auto-Clean on CI/CD Graduation:**
   - Set `slot_graduation_clear = 0`. Scanned Box graduation no longer cleans glitched slots.
3. **Green Face 1 Becomes Unconditional `+2 🔬`:**
   - Under die profile `V038D`, Green Face 1 replaces `_choice(Clean 1 Slot, +$1)` with `Face(name="+2 🔬", patches=2)`. *G1 Self-Healing Kernel* retains its Phase 1 Step 5 cleaning (`Clean 1 Glitched Slot + 1 🔬`).
4. **Green Die Processing $\to$ Scanned Box Slot Cleaning (Variant B: Count then Clean):**
   - Whenever a Green die leaves the Processing Box and banks its Corporate Secret:
     1. Calculate Secret yield using pre-clean glitched slots: $Y = \max(0, 3 - g)$.
     2. Award Corporate Secrets to player.
     3. Clean 1 Glitched Shield Slot ($g \leftarrow \max(0, g - 1)$).
5. **Calibrated Shogun Baffle Physics Retained:**
   - Inherits `TowerMode.SHOGUN_BAFFLE` from `v038c`.

### 1.3 Mathematical Justification: Why Variant B (Count then Clean) is Mandatory
Empirical simulation of 4,500 full-game matches across 9 parameter cells demonstrated a decisive divergence between Variant A and Variant B:

```
+-------------------------------------------------------------------------------------------------------------------------+
| Candidate    | Timing Mechanic                  | Mean Rds (3P) | Sing % | PZ %   | MC %   | Green Win % (3P) | Verdict |
+-------------------------------------------------------------------------------------------------------------------------+
| Baseline     | Passive Grad Clean (6.09/seat)   | 10.10 rds     | 73.0%  | 19.2%  |  7.6%  | 36.1% (Balanced) | SLUGGISH|
| v038d Var A  | Clean 1 Slot BEFORE Counting     |  9.10 rds     | 44.4%  | 26.0%  | 29.4%  | 49.6% (DOMINANT) | REJECT  |
| v038d Var B  | Count Yield BEFORE Cleaning Slot |  8.94 rds     | 42.6%  | 29.2%  | 28.0%  | 38.9% (BALANCED) | APPROVE |
+-------------------------------------------------------------------------------------------------------------------------+
```

- **The Mathematical Defect of Variant A:**
  $$Y_A(g) = \max\big(0,\, 3 - \max(0, g - 1)\big)$$
  Under Variant A, $g=0$ and $g=1$ yield the exact same payout: **`3` Corporate Secrets**. Because players start with $g=1$ in Candidate C2, a Round 1–2 Green Secret banking incurs **zero yield penalty**. The player receives a free slot repair *and* maximum Corporate Secrets. Green Company win rate surged to **49.6% in 3P** and **61.5% in 2P**, crushing Blue Path down to 21.3%.
- **The Equilibrium of Variant B:**
  $$Y_B(g) = \max(0, 3 - g), \quad \text{followed by } g \leftarrow \max(0, g - 1)$$
  In Variant B, the initial $g=1$ glitch actively penalizes the first Green payout to **`2` Secrets**, rewarding the player with slot repair for subsequent rounds. Green Company win rate settles at a healthy **38.9% in 3P** (with Red at 30.0% and Blue at 30.7%), and Blue Path rebounds to **42.7% (3P) / 32.6% (4P)**.
- **Active Triage Activation:**
  With passive graduation removed, shield dice spent on active cleaning (`slots_cleaned_by_die`) jumps from **1.38** to **5.20–5.42 per seat** (+280%). Players experience **~0.88 zero-capacity rounds**, injecting vital early existential drama.

---

## 2. Invariants (System Rules)

- **INV-V38D-01 (C2 Compiler Priming & Staging Payload):**
  At game initialization, the compiler priming drop contains exactly 4 cubes (`1R, 1B, 1G, 1K`). The initial Staging Cup payload is determined by the active `v1.0` card: *Script Kiddie* stages `{RED: 2, BLUE: 1, GREEN: 1}`; *Data Scraper* stages `{RED: 1, BLUE: 2, GREEN: 1}`. Zero Black cubes enter the Staging Cup during setup.
- **INV-V38D-02 (C2 Starting Glitched Shield Slot):**
  Every player initializes at Setup with `glitched_shield_slots = 1`, `max_glitched_slots = 1`, and `slots_glitched_by_source["setup"] = 1`. With baseline Defense Grid Level 0 (Capacity 2), initial effective capacity is exactly `1` clean Shield Slot.
- **INV-V38D-03 (Elimination of Graduation Auto-Clean):**
  When `slot_graduation_clear = 0`, Phase 5 Step 3 CI/CD graduation of dice from Scanned Box to Ready for Release shall clean zero glitched slots (`slots_cleared_by_graduation == 0`, `player.slot_clear_used_this_phase5 == False`).
- **INV-V38D-04 (Green Face 1 Profile):**
  Under die face profile `V038D`, Green Face 1 is `Face(name="+2 🔬", patches=2)`. It contains zero clean actions, money, or shields. *G1 Self-Healing Kernel* retains `Clean 1 Glitched Shield Slot + 1 🔬` upon deployment in Phase 1 Step 5.
- **INV-V38D-05 (Variant B Green Banking Slot Clean):**
  Whenever a Green die leaves the Processing Box and banks its Corporate Secret (via Conveyor Triage, *B3 Air-Gapped Backup*, *Jumper Diagnostics*, or *Magnetic Splice*):
  1. Corporate Secret yield is calculated on pre-clean slots: $Y = \max(0, 3 - g)$.
  2. Player receives $Y$ Corporate Secrets.
  3. Player cleans 1 Glitched Shield Slot ($g \leftarrow \max(0, g - 1)$), incrementing `slots_cleaned_by_green_triage` by the number of slots actually cleaned ($0$ or $1$).
- **INV-V38D-06 (Stranded & Return Non-Banking Integrity):**
  If a Green die in the Processing Box is returned to the market or discarded without banking (e.g., via *Burn Notice* or *Return Colored Die*), zero Corporate Secrets are awarded and zero glitched slots are cleaned (`slots_cleaned_by_green_triage` is not incremented).
- **INV-V38D-07 (Telemetry & Ledger Completeness):**
  `PlayerState` maintains `slots_cleaned_by_green_triage`, which is exported in end-game telemetry. `fast_clone()` copies this field.
- **INV-V38D-08 (Backwards Parity Preservation):**
  `GameConfig.v038c()`, `v038b()`, `v038()`, and `v037()` remain completely unchanged in behavior and output, preserving golden fixtures.

---

## 3. Module Contracts & Exact Edits

### 3.1 [`sim/config.py`](file:///home/mike/antigravity/rogue-agent/sim/config.py)

#### 3.1.1 Add Profile Constant & Field Declarations
```python
# In sim/config.py:
V038_DIE_FACE_PROFILES = (
    "V038_DRAFT",
    "V038_YELLOW_MS",
    "V038_YELLOW_MS_ALT",
    "V038_YELLOW_MS_F3",
    "V038D",  # Added for v0.38d (Green Face 1 = +2 🔬, Yellow F3 = +$1 & +1 MS)
)
_GREEN_TRIAGE_CLEAN_MODES = ("NONE", "COUNT_THEN_CLEAN", "CLEAN_THEN_COUNT")
```

In `GameConfig` dataclass:
```python
    # v0.38d: C2 setup & Green-Clean package levers
    starting_glitched_shield_slots: int = 0  # v038d sets to 1 (INV-V38D-02)
    green_triage_clean_mode: str = "NONE"   # "NONE" | "COUNT_THEN_CLEAN" | "CLEAN_THEN_COUNT"
    v1_staging_payload_override: Optional[Dict[str, Dict[CubeColor, int]]] = None
```

#### 3.1.2 Update Validation `_validate_v038()`
```python
        if self.green_triage_clean_mode not in _GREEN_TRIAGE_CLEAN_MODES:
            raise ValueError(f"green_triage_clean_mode must be one of {_GREEN_TRIAGE_CLEAN_MODES}, got {self.green_triage_clean_mode!r}")
        if self.starting_glitched_shield_slots < 0:
            raise ValueError("starting_glitched_shield_slots must be >= 0")
```

#### 3.1.3 Factory Preset `v038d()`
```python
    @classmethod
    def v038d(cls, **overrides) -> "GameConfig":
        """v0.38 candidate 4 (C2 + Green-Clean Package, Variant B): ``v038c()`` + Candidate C2 setup (4 priming cubes,
        4 starting attack cubes in staging cup, 1 starting Glitched Shield Slot), elimination of passive graduation
        auto-clean (slot_graduation_clear = 0), Green Face 1 = +2 🔬 (die_face_profile = 'V038D'), and Green banking
        triage cleans 1 Glitched Shield Slot (COUNT_THEN_CLEAN). Preserves Shogun Baffle tower physics."""
        from sim.entities import V038D_V1_STAGING_PAYLOAD
        for k, v in (
            ("starting_glitched_shield_slots", 1),
            ("slot_graduation_clear", 0),
            ("green_triage_clean_mode", "COUNT_THEN_CLEAN"),
            ("die_face_profile", "V038D"),
            ("v1_staging_payload_override", dict(V038D_V1_STAGING_PAYLOAD)),
        ):
            overrides.setdefault(k, v)
        return cls.v038c(**overrides)
```

---

### 3.2 [`sim/entities.py`](file:///home/mike/antigravity/rogue-agent/sim/entities.py)

#### 3.2.1 Canonical Staging Payload Constant
```python
V038D_V1_STAGING_PAYLOAD: Dict[str, Dict[CubeColor, int]] = {
    "SCRIPT_KIDDIE": {CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
    "DATA_SCRAPER": {CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.GREEN: 1},
}
```

#### 3.2.2 Green Face 1 Update in `_create_colored_die_v038()`
```python
    elif color == DieColor.GREEN:
        f1 = (Face(name="+2 🔬", patches=2) if profile == "V038D" 
              else _choice(Face(CLEAN_SLOT_NAME, clean_slots=1), Face("+$1", money=1)))
        faces = [f1,
                 Face(name="+1 🔬", patches=1), Face(name="+2 🔬", patches=2),
                 _choice(Face("+1 🔬", patches=1), Face("+$1", money=1)), SECRET_FACE, star_face]
    elif color == DieColor.YELLOW and profile in ("V038_YELLOW_MS", "V038_YELLOW_MS_ALT", "V038_YELLOW_MS_F3", "V038D"):
        y = lambda: _choice(Face("+$2", money=2), Face("+1 🔬", patches=1))
        f1 = (Face(name="+$1 & +1 Market Share", money=1, market_share=1) if profile == "V038_YELLOW_MS_ALT"
              else Face(name="+2 Market Share", market_share=2))
        f3 = (Face(name="+$1 & +1 Market Share", money=1, market_share=1) if profile in ("V038_YELLOW_MS_F3", "V038D")
              else Face(name="+$3", money=3))
        faces = [f1, _choice(Face("+1 Market Share", market_share=1), Face("+1 🔬", patches=1)),
                 f3, y(), y(), star_face]
```

---

### 3.3 [`sim/engine/core.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/core.py)

#### 3.3.1 Setup Glitched Shield Slots Initialization
In `GameEngine.__init__()` when initializing `PlayerState`:
```python
            if config.glitched_shield_slots_enabled:
                start_g = int(getattr(config, "starting_glitched_shield_slots", 0))
                player.glitched_shield_slots = start_g
                player.max_glitched_slots = start_g
                if start_g > 0:
                    player.slots_glitched_by_source["setup"] = start_g
```

#### 3.3.2 Setup Staging Cup Payload Resolution
In `GameEngine.__init__()` when staging cubes from `version_deck[0]`:
```python
        staging_cup: Dict[CubeColor, int] = {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
        v1_code = self.version_deck[0].directive_code
        payload_override = getattr(self.config, "v1_staging_payload_override", None)
        if payload_override and v1_code in payload_override:
            staging_payload = payload_override[v1_code]
        else:
            staging_payload = self.version_deck[0].get_staging_payload(self.config.num_players)
        for color, count in staging_payload.items():
            staging_cup[color] = count
```

---

### 3.4 [`sim/engine/secret_faces.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/secret_faces.py)

#### 3.4.1 Triage Banking Clean Implementation in `bank()`
```python
def bank(cfg: "GameConfig", p: "PlayerState", die: "Die", state: Any = None) -> int:
    """Banks the Secret of a die leaving the Processing Box (INV-SF-01: once per visit). Returns Secrets gained.
    Under v0.38d (Variant B: COUNT_THEN_CLEAN), Green calculates yield on current glitched slots, awards Secrets,
    and then cleans 1 Glitched Shield Slot (INV-V38D-05)."""
    if not getattr(die, "secret_pending", False):
        return 0
    
    clean_mode = getattr(cfg, "green_triage_clean_mode", "NONE")
    
    # Variant A support (for sensitivity/comparison testing)
    if clean_mode == "CLEAN_THEN_COUNT" and die.color == DieColor.GREEN:
        clean_slots(p, 1, "green_triage")
        y = secret_yield(cfg, p, die.color)
    else:
        # Variant B (Standard approved rule) and NONE
        y = secret_yield(cfg, p, die.color)
        if clean_mode == "COUNT_THEN_CLEAN" and die.color == DieColor.GREEN:
            clean_slots(p, 1, "green_triage")

    if die.color == DieColor.RED:
        p.red_secrets_banked += 1
        if die.processing_entry_round and state is not None:
            p.red_processing_wait_rounds += int(state.current_round) - int(die.processing_entry_round)
            p.red_processing_wait_count += 1
        if state is not None:
            state.red_secret_banked_this_round = True
            state.red_secrets_banked_this_round += 1
            state.red_bankers_this_round.append(p.player_id)
            rb = state.red_banks_by_round
            while len(rb) < int(state.current_round):
                rb.append(0)
            rb[int(state.current_round) - 1] += 1

    die.secret_pending = False
    k = _ckey(die.color)
    p.secret_faces_banked[k] = p.secret_faces_banked.get(k, 0) + 1
    hist = p.secret_yield_hist.setdefault(k, {})
    hist[str(y)] = hist.get(str(y), 0) + 1
    if y > 0:
        p.gain_secrets(y, f"secret_face_{k}")
    return y
```

#### 3.4.2 Support `"green_triage"` in `clean_slots()`
```python
def clean_slots(p: "PlayerState", n: int, how: str) -> int:
    """Cleans up to ``n`` glitched slots. ``how``: ``"die"`` (placement), ``"face"`` (Green F1 / G1),
    ``"graduation"`` (Phase 5 step 3b), ``"green_triage"`` (Phase 5 step 1 Green banking)."""
    done = min(max(0, int(n)), int(p.glitched_shield_slots))
    if done:
        p.glitched_shield_slots -= done
        attr = {
            "die": "slots_cleaned_by_die",
            "face": "slots_cleaned_by_face",
            "graduation": "slots_cleared_by_graduation",
            "green_triage": "slots_cleaned_by_green_triage",
        }[how]
        setattr(p, attr, getattr(p, attr) + done)
    return done
```

---

### 3.5 [`sim/engine/phase5_pipeline_shift.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/phase5_pipeline_shift.py)

#### 3.5.1 Guard Zero Graduation Clear
```python
def graduation_slot_clear(engine: GameEngine, player: PlayerState, graduated: int) -> int:
    """v0.38 step 3b: once per Phase 5, if >= 1 die graduated, clear ``slot_graduation_clear`` slot(s)."""
    player.slot_clear_used_this_phase5 = False
    if graduated <= 0 or player.glitched_shield_slots <= 0 or engine.config.slot_graduation_clear <= 0:
        return 0
    player.slot_clear_used_this_phase5 = True
    return secret_faces.clean_slots(player, engine.config.slot_graduation_clear, "graduation")
```

---

### 3.6 [`sim/engine/state.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/state.py) & [`sim/engine/end_game.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/end_game.py)

#### 3.6.1 PlayerState Attributes & Cloner
In `PlayerState.__init__()`:
```python
        self.slots_cleaned_by_die = 0
        self.slots_cleaned_by_face = 0
        self.slots_cleared_by_graduation = 0
        self.slots_cleaned_by_green_triage = 0  # Added for v0.38d Green banking triage
```

#### 3.6.2 End Game Telemetry Export
In `evaluate_end_game()` / `_build_player_summary()`:
```python
        "slots_cleared_by_graduation": p.slots_cleared_by_graduation,
        "slots_cleaned_by_green_triage": p.slots_cleaned_by_green_triage,
```

---

### 3.7 [`sim/bots/secret_face_policy.py`](file:///home/mike/antigravity/rogue-agent/sim/bots/secret_face_policy.py)

#### 3.7.1 Valuation of Triage Cleaning
- In `choose_slot_cleaners`:
  Retain `if k > eff or (green_pending and not chosen and k >= 1):`.
  - When $k > \text{eff}$ (shield dice exceed open slots), the bot commits 1 excess shield die to repair the slot, raising capacity from $1 \to 2$, which immediately allows deploying the second shield die to block.
  - When $k \le \text{eff}$ and $g=1$ with a pending Green die, spending 1 shield die to clean raises the Green Secret yield from $2 \to 3$ (+1 Secret = +1 VP, value ~$4.0).
- In `marginal_block_value`:
  - With `slot_graduation_clear = 0`, Green attack cubes deal persistent damage to capacity. The existing baseline valuation $v = \text{SHIELD\_VALUE} + \text{SECRET\_VALUE} \cdot \min(\text{pending}, \text{bw})$ accurately prices the cost of taking a glitch.

---

## 4. Test Specifications (`tests/test_v380d_c2_green_clean.py`)

A dedicated unit and integration test suite must validate all invariants:

### 4.1 Suite Architecture
File: [`tests/test_v380d_c2_green_clean.py`](file:///home/mike/antigravity/rogue-agent/tests/test_v380d_c2_green_clean.py)

```python
class TestV038dC2GreenClean(unittest.TestCase):
```

### 4.2 Required Test Cases

1. `test_v038d_config_preset()`:
   - Instantiate `GameConfig.v038d()`.
   - Assert `starting_glitched_shield_slots == 1`.
   - Assert `slot_graduation_clear == 0`.
   - Assert `green_triage_clean_mode == "COUNT_THEN_CLEAN"`.
   - Assert `die_face_profile == "V038D"`.
   - Assert `tower_mode == TowerMode.SHOGUN_BAFFLE`.
   - Assert `red_secret_owner_yield == 2`.

2. `test_c2_setup_staging_cup_and_priming()`:
   - For *Script Kiddie* (`directive_code="SCRIPT_KIDDIE"`):
     Assert initial `staging_cup` has `{RED: 2, BLUE: 1, GREEN: 1, BLACK: 0}` (total 4 cubes).
   - For *Data Scraper* (`directive_code="DATA_SCRAPER"`):
     Assert initial `staging_cup` has `{RED: 1, BLUE: 2, GREEN: 1, BLACK: 0}` (total 4 cubes).
   - Verify compiler priming drops 4 cubes (`1R, 1B, 1G, 1K`).

3. `test_c2_starting_glitched_shield_slots()`:
   - Initialize game with `GameConfig.v038d(num_players=3)`.
   - For all players:
     Assert `player.glitched_shield_slots == 1`.
     Assert `player.max_glitched_slots == 1`.
     Assert `player.slots_glitched_by_source.get("setup") == 1`.
     Assert `effective_capacity(player) == 1` (Capacity 2 - 1 glitched).

4. `test_green_face_1_profile_v038d()`:
   - Create Green die under profile `"V038D"`.
   - Face 1 must be `Face(name="+2 🔬", patches=2)`. Clean slots must be 0; money must be 0.
   - Yellow die under `"V038D"` must retain F3 = `Face(name="+$1 & +1 Market Share", money=1, market_share=1)`.
   - *G1 Self-Healing Kernel* must retain `clean_slots == 1, patches == 1`.

5. `test_no_graduation_auto_clean()`:
   - Set up player with `glitched_shield_slots = 1`, 1 die in `scanned_dice`.
   - Run `phase5_pipeline_shift.execute_pipeline_shift()`.
   - Die graduates from Scanned to Ready for Release.
   - Assert `player.glitched_shield_slots == 1` (NOT cleaned).
   - Assert `player.slots_cleared_by_graduation == 0`.
   - Assert `player.slot_clear_used_this_phase5 is False`.

6. `test_green_triage_banking_variant_b_timing()`:
   - Case A ($g=1$): Player has `glitched_shield_slots = 1`. Green die with `secret_pending=True` in `glitched_dice`.
     Call `secret_faces.bank(cfg, player, die)`.
     Assert return value / Secrets awarded is **`2`** ($\max(0, 3 - 1)$).
     Assert `player.glitched_shield_slots == 0` (cleaned after counting).
     Assert `player.slots_cleaned_by_green_triage == 1`.
   - Case B ($g=0$): Player has `glitched_shield_slots = 0`. Bank Green die.
     Assert Secrets awarded is **`3`** ($\max(0, 3 - 0)$).
     Assert `player.glitched_shield_slots == 0`.
     Assert `player.slots_cleaned_by_green_triage == 0`.
   - Case C ($g=2$): Bank Green die.
     Assert Secrets awarded is **`1`**.
     Assert `player.glitched_shield_slots == 1`.
     Assert `player.slots_cleaned_by_green_triage == 1`.
   - Case D ($g=3$): Bank Green die.
     Assert Secrets awarded is **`0`**.
     Assert `player.glitched_shield_slots == 2`.
     Assert `player.slots_cleaned_by_green_triage == 1`.

7. `test_green_triage_exit_routes()`:
   - Verify slot cleaning and correct yield via:
     - Phase 5 Step 1 Conveyor Triage.
     - Phase 3 *B3 Air-Gapped Backup*.
     - Phase 3 *Jumper Diagnostics*.
     - Phase 5 Step 1 *Magnetic Splice*.

8. `test_green_stranded_and_burn_notice_no_clean()`:
   - Green die in `glitched_dice` removed via `secret_faces.lose_pending()`.
   - Assert `player.glitched_shield_slots` does not change.
   - Assert `player.slots_cleaned_by_green_triage == 0`.

9. `test_v038c_backwards_parity_preserved()`:
   - Instantiate `GameConfig.v038c()`.
   - Assert `starting_glitched_shield_slots == 0`.
   - Assert `slot_graduation_clear == 1`.
   - Assert `green_triage_clean_mode == "NONE"`.
   - Assert staging payload is 3 cubes (`1R, 1B, 1G` on Script Kiddie).
   - Assert Green Face 1 is split Clean/Cash face.

---

## 5. Architectural Risk Analysis & Mitigation

1. **Parity Golden Fixture Breakage Risk:**
   - *Risk:* Overwriting default `VersionCard` definitions in `sim/entities.py` would invalidate `tests/fixtures/v038b_parity` golden fixtures and older regression tests (`test_v210_rules.py`).
   - *Mitigation:* Implement `v1_staging_payload_override` on `GameConfig` and route setup staging through `V038D_V1_STAGING_PAYLOAD`. Legacy configs (`v038c`, `v038b`, `v038`, `v037`) omit this override, preserving exact bit-level parity.
2. **Double-Cleaning or Zero-Cleaning on Green Triage:**
   - *Risk:* Placing slot cleaning logic in Phase 5 Conveyor Triage would miss Phase 3 card plays (*B3*, *Jumper Diagnostics*).
   - *Mitigation:* Centralize slot cleaning inside `secret_faces.bank()`. Since every valid exit from the Processing Box routes through `bank()`, all cards and triage steps share identical Variant B semantics.
3. **Bot Decision Divergence:**
   - *Risk:* Bot logic failing to appreciate the yield increase of cleaning prior to Green banking.
   - *Mitigation:* Analytical verification in Section 3.7 demonstrates that the existing `k > eff` and `green_pending` conditions in `choose_slot_cleaners` correctly model the Variant B trade-off.
