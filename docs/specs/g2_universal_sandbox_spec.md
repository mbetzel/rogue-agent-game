# Technical Architecture Specification: Phase 50
## Green Die G2 (`Universal Sandbox`) Redesign

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation (User-Aligned, Phase 50)  
**Target Version:** `v0.38c` Baseline / `V038_DRAFT`  
**Dependencies:** [RULES.md](../../RULES.md), [RULES_APPENDIX.md](../../RULES_APPENDIX.md), [GLOSSARY.md](../../GLOSSARY.md), [g2_universal_sandbox_analysis.md](../findings/g2_universal_sandbox_analysis.md)  
**Target Components:**
- [`sim/config.py`](file:///home/mike/antigravity/rogue-agent/sim/config.py)
- [`sim/entities.py`](file:///home/mike/antigravity/rogue-agent/sim/entities.py)
- [`sim/engine/phase1_roll_deploy.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/phase1_roll_deploy.py)
- [`sim/engine/phase3_income.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/phase3_income.py)
- [`sim/engine/secret_faces.py`](file:///home/mike/antigravity/rogue-agent/sim/engine/secret_faces.py)
- [`sim/bots/secret_face_policy.py`](file:///home/mike/antigravity/rogue-agent/sim/bots/secret_face_policy.py)
- [`sim/bots/base.py`](file:///home/mike/antigravity/rogue-agent/sim/bots/base.py)
- [`pnp/generate_pnp.py`](file:///home/mike/antigravity/rogue-agent/pnp/generate_pnp.py)
- [`tests/test_g2_universal_sandbox.py`](file:///home/mike/antigravity/rogue-agent/tests/test_g2_universal_sandbox.py)

---

## 1. Executive Summary & Design Motivation

### 1.1 Context & Problem Statement
During the `v0.38` rework, colored shields were eliminated from central market dice. Green's defensive role pivoted from raw shields to Glitched Shield Slot remediation. During that initial transition, `G2 — Universal Sandbox` (`$4`) was temporarily mapped to the exact same placeholder as `G1 — Self-Healing Kernel` (`$5`): `Clean 1 Glitched Shield Slot + gain +1 🔬`.

This created a severe design flaw:
1. **Redundancy & Price Inversion:** G1 ($5) and G2 ($4) possessed identical mechanical profiles, making G1 strictly overpriced and G2 an overt trap for G1.
2. **Loss of Mechanical Identity:** Green lacked a counter-cyclical recovery card that leverages active glitches into operational intelligence.

### 1.2 Approved Rule Change
The User approved Option D2 from [g2_universal_sandbox_analysis.md](../findings/g2_universal_sandbox_analysis.md):
- **Card:** Green `★` Variant `G2 — Universal Sandbox` (`$4`).
- **Timing:** `[In Production — Income]` (Phase 3: Income).
- **Ability:** Gain `+2 🔬`, plus `+1 🔬` for each of your **Glitched Shield Slots** `[TUNE]`.
- **Phase 1 Step 5 Removal:** G2 no longer cleans a Glitched Shield Slot (`clean_slots = 0`). Only Green Face 1 and `G1` retain intrinsic Phase 1 Step 5 cleaning.

### 1.3 Expected Value & Zero-Blank Compliance
Telemetric simulation shows that in Phase 3 Income, players carry $0$ glitched shield slots ($g=0$) in **82.4%** of all rounds (and **98.6%** in Rounds 1–3). 
- Providing a baseline of `+2 🔬` satisfies the core architectural pillar (`AGENTS.md: Zero Blank Faces` on colored module dice) while scaling to `+3 🔬` ($g=1$, 14.2% PMF) and `+4 🔬` ($g=2$, 3.4% PMF).
- At `$4` market cost, this yields a nominal EV of `2.21 🔬` (Standard) to `2.35 🔬` (Aggressive), achieving mathematical balance against `G3 — Live Reboot` (`$4`: `+2 🔬 + $1`).

---

## 2. Configuration (`sim/config.py`)

### 2.1 Tunable Levers
Add explicit tuning parameters to `GameConfig` to govern G2 yield:

```python
# --- Green G2 Universal Sandbox [TUNE] (Phase 50) ---
g2_base_research: int = 2   # Base Phase 3 research output on G2 Universal Sandbox face
g2_glitch_bonus: int = 1    # Phase 3 research bonus per active Glitched Shield Slot
```

### 2.2 Validation Logic
In `GameConfig._validate_v038(self)`:
- Ensure `g2_base_research >= 0` and `isinstance(g2_base_research, int)`.
- Ensure `g2_glitch_bonus >= 0` and `isinstance(g2_glitch_bonus, int)`.

---

## 3. Data Model & Entities (`sim/entities.py`)

### 3.1 Base Variant Definition (`get_all_variant_cards`)
In `get_all_variant_cards()`, keep the legacy V037 profile untouched for backward compatibility:
```python
VariantCard(
    code="G2",
    name="Universal Sandbox",
    die_color=DieColor.GREEN,
    description="Block 1 Any + gain +1 🔬.",
    cost=4,
    star_face=Face(
        name="G2: Universal Sandbox",
        block_amount=1,
        shield_color=ShieldColor.ANY,
        patches=1,
        is_star=True,
        star_code="G2",
    ),
)
```

### 3.2 V038 Profile Mapping (`apply_variant_profile`)
In `apply_variant_profile(variant_cards, profile)`:
When `profile == "V038_DRAFT"`, decouple `G2` from `G1`:

```python
elif code == "G1":
    out[color] = _v038_star(card, f"{CLEAN_SLOT_NAME} and gain +1 🔬.", patches=1, clean_slots=1)
elif code == "G2":
    out[color] = _v038_star(
        card,
        "Gain +2 🔬, plus +1 🔬 for each of your Glitched Shield Slots.",
        patches=2,
        clean_slots=0,
    )
```

`_v038_star()` resets `block_amount = 0` and `shield_color = None`.  
Resulting `star_face` properties under `V038_DRAFT`:
- `name`: `"G2: Universal Sandbox"`
- `block_amount`: `0`
- `shield_color`: `None`
- `patches`: `2` (the base yield)
- `clean_slots`: `0`
- `is_star`: `True`
- `star_code`: `"G2"`

---

## 4. Engine Module Contracts

### 4.1 Phase 1: Roll & Deploy (`sim/engine/phase1_roll_deploy.py`)
- **Step 5c Slot Cleaning:** In Phase 1 Step 5c, slot cleaning evaluates `eff.clean_slots > 0`. Because `clean_slots == 0` for G2, rolled G2 dice do not trigger `secret_faces.clean_slots()`.
- **In Production Assignment:** Because `block_amount == 0` and `shield_color is None`, G2 cannot be committed to a Shield slot. It is assigned to `ProductionRole.INCOME`.

### 4.2 Phase 3: Income (`sim/engine/phase3_income.py`)
In `_die_income_row(state: GameState, player: PlayerState, die: Die) -> Optional[Dict[str, Any]]`:
When `eff.is_star and eff.star_code == "G2"`:
1. Check if V038 rules apply: `is_v038 = (getattr(state.config, "variant_profile", None) == "V038_DRAFT" or getattr(state.config, "glitched_shield_slots_enabled", False))`.
2. If `is_v038`:
   - Baseline research is initialized from `eff.patches` (which is `state.config.g2_base_research`, baseline `2`).
   - Glitched slots count: `g = getattr(player, "glitched_shield_slots", 0)`.
   - Bonus calculation: `bonus = g * getattr(state.config, "g2_glitch_bonus", 1)`.
   - Total research: `research += bonus`.
   - Update `star_note`:
     ```python
     if g > 0:
         star_note = f"Universal Sandbox (+{research} 🔬, incl. +{bonus} from {g} glitched slots)"
     else:
         star_note = f"Universal Sandbox (+{research} 🔬)"
     ```
3. If not `is_v038` (legacy V037):
   - Leave `research = eff.patches` (`1 🔬`).
   - `star_note = _STAR_NOTES.get("G2")` (`"Universal Sandbox (+1 🔬)"`).

In `_STAR_NOTES`:
Update default string:
```python
"G2": "Universal Sandbox (+2 🔬)",
```

### 4.3 Documentation Cleanup (`sim/engine/secret_faces.py`)
Update docstring of `clean_slots()`:
```python
def clean_slots(p: "PlayerState", n: int, how: str) -> int:
    """Cleans up to ``n`` glitched slots. ``how``: ``"die"`` (placement), ``"face"`` (Green F1 / G1),
    ``"graduation"`` (Phase 5 step 3b)."""
```

---

## 5. Bot Decision Heuristics (`sim/bots/`)

### 5.1 Reroll Policy Evaluation (`sim/bots/secret_face_policy.py`)
In `face_value(player: PlayerState, face: Optional[Face], state: Optional[GameState] = None) -> float`:
When valuing a G2 face, account for the dynamic research yield from active glitched slots:
```python
if face.is_star and getattr(face, "star_code", None) == "G2":
    if state is not None and getattr(state.config, "variant_profile", None) == "V038_DRAFT":
        glitches = getattr(player, "glitched_shield_slots", 0)
        multiplier = getattr(state.config, "g2_glitch_bonus", 1)
        v += RESEARCH_VALUE * glitches * multiplier
```

### 5.2 Production Allocation & Economic Scoring (`sim/bots/base.py`)
In `_face_econ_score(face: Optional[Face]) -> int`:
If G2 is evaluated for priority or corruption sacrifice:
```python
if getattr(face, "star_code", None) == "G2":
    score += 2 * getattr(player, "glitched_shield_slots", 0)
```

---

## 6. Print-and-Play Assets (`pnp/generate_pnp.py`)

Update `VariantCardSpec` for `G2`:
```python
VariantCardSpec(
    'G2', 'green', 'GREEN // ANTIVIRUS', '$4',
    '{PIP1} Clean/$1 | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}',
    '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret | {PIP6} {STAR}',
    'Universal Sandbox', 'P3 INCOME',
    'Gain **+2 {RESEARCH}**, plus **+1 {RESEARCH}** for each of your **Glitched Shield Slots** in Phase 3: Income.',
    'Sandbox: generates research from quarantined glitches.',
),
```

---

## 7. Web UI & Serialization (`web/`)

- `web/schemas.py:serialize_variant_card()` dynamically serializes `card.description` and `card.star_face`. No static string overrides exist in `web/schemas.py` or `web/static/js/components/market.js`.
- During Phase 3 income execution, `_die_income_row` details (including `patches`, `research`, and `star_note`) are transmitted via the existing `/api/game/state` and log feeds without schema changes.

---

## 8. Parity & Backward Compatibility Strategy

| Configuration Profile | Variant Profile | G2 Face Properties | Phase 1 Clean? | Phase 3 Yield | Parity Impact |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `GameConfig.legacy_v035()` / `v037()` | `"V037"` | `Block 1 Any`, 1 🔬 | No (blocks Any) | Flat `1 🔬` | **100% Bit-Identical.** Matches golden parity fixtures. |
| `tests/fixtures/v038b_parity` | `"V038_DRAFT"` | Standard setup | N/A | N/A | **100% Bit-Identical.** Uses scenario `"mixed"` which loads default card `G1`. |
| `v038()`, `v038b()`, `v038c()` | `"V038_DRAFT"` | Cost $4, Income, 2 🔬 | **NO** | `2 + 1*g 🔬` | **New Phase 50 Behavior.** |

---

## 9. Architectural Invariants

- **`INV-G2-INCOME-BASE-01`:** An active G2 die In Production yields strictly `g2_base_research` (baseline 2 🔬) when `player.glitched_shield_slots == 0`.
- **`INV-G2-INCOME-SCALING-02`:** An active G2 die In Production yields `g2_base_research + (player.glitched_shield_slots * g2_glitch_bonus)` in Phase 3 Income.
- **`INV-G2-NO-P1-CLEAN-03`:** A rolled G2 die in Phase 1 Step 5 cleans 0 glitched shield slots (`clean_slots == 0`).
- **`INV-G2-ZERO-BLANK-04`:** G2 yields $> 0$ resources across all reachable player states, preserving the zero-blank-faces design pillar.
- **`INV-G2-PARITY-V037-05`:** When `variant_profile == "V037"`, G2 retains `block_amount = 1`, `shield_color = ShieldColor.ANY`, `clean_slots = 0`, and yields flat `1 🔬` in Phase 3.

---

## 10. Comprehensive Test Matrix (`tests/test_g2_universal_sandbox.py`)

| Test ID | Method Name | Description & Assertion |
| :--- | :--- | :--- |
| **TC-G2-01** | `test_g2_income_at_zero_glitches` | Verify G2 In Production yields exactly `2 🔬` and `$0` when `glitched_shield_slots == 0`. |
| **TC-G2-02** | `test_g2_income_scaling_with_glitches` | Set `glitched_shield_slots` to 1, 2, 3; verify yields are 3 🔬, 4 🔬, 5 🔬. |
| **TC-G2-03** | `test_g2_does_not_clean_in_phase1` | Player has 2 glitched slots. Roll G2. Execute Phase 1 Step 5. Verify glitched slots remain 2. |
| **TC-G2-04** | `test_g2_cannot_commit_to_shield` | Verify G2 star face has `is_shield == False` and assigns to `ProductionRole.INCOME`. |
| **TC-G2-05** | `test_multiple_g2_dice_independent_scaling` | Two G2 dice In Production with $g=2$; verify total yield is `(2 + 2) + (2 + 2) = 8 🔬`. |
| **TC-G2-06** | `test_legacy_v037_parity` | Under `GameConfig.legacy_v035()`, verify G2 retains `Block 1 Any + 1 🔬` and does not scale with $g$. |
| **TC-G2-07** | `test_config_tuning_levers` | Override `g2_base_research=3, g2_glitch_bonus=2`; verify yield with $g=2$ is `3 + 2*2 = 7 🔬`. |
| **TC-G2-08** | `test_bot_face_valuation` | Verify `face_value(player, g2_face, state)` increases strictly monotonically as `player.glitched_shield_slots` increases. |
| **TC-G2-09** | `test_pnp_and_web_serialization` | Assert `serialize_variant_card(g2_card)["description"]` contains `"Gain +2 🔬, plus +1 🔬 for each of your Glitched Shield Slots."`. |

---

## 11. Senior Engineer Implementation Checklist

- [ ] Add `g2_base_research` and `g2_glitch_bonus` to `sim/config.py` with validation in `_validate_v038()`.
- [ ] Update `apply_variant_profile()` in `sim/entities.py` to decouple G2 from G1 under `"V038_DRAFT"`.
- [ ] Implement dynamic research scaling in `_die_income_row()` in `sim/engine/phase3_income.py`.
- [ ] Update `_STAR_NOTES` in `sim/engine/phase3_income.py`.
- [ ] Update bot heuristic valuation in `sim/bots/secret_face_policy.py` and `sim/bots/base.py`.
- [ ] Update PnP spec in `pnp/generate_pnp.py`.
- [ ] Clean up docstring in `sim/engine/secret_faces.py`.
- [ ] Create `tests/test_g2_universal_sandbox.py` covering all 9 test cases in Section 10.
- [ ] Verify full test suite and parity fixtures pass with zero regressions.
