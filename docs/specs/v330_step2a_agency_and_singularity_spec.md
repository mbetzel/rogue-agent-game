# Technical Architecture Specification: Phase 41 (v0.33.0)
## Step 2A Agency, White Contractor Sacrifice Enforcement, & Immediate Singularity Game End

**Author:** Principal Engineer / Architect  
**Status:** Approved for Implementation  
**Target Version:** `v0.33.0` Baseline  
**Dependencies:** [RULES.md](../../RULES.md), [PLAN.md](../../PLAN.md), [v320_blue_variants_spec.md](./v320_blue_variants_spec.md)  
**Target Components:**
- [`sim/entities.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/entities.py)
- [`sim/bots/base.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/bots/base.py)
- [`sim/engine/phase2_threat.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py)
- [`sim/engine/end_game.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/end_game.py)
- [`web/controller/phase2_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase2_actions.py)
- [`web/controller/phase3_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase3_actions.py)
- [`web/static/js/components/header.js`](file:///z:/home/mike/antigravity/rogue-agent/web/static/js/components/header.js)
- [`pnp/generate_pnp.py`](file:///z:/home/mike/antigravity/rogue-agent/pnp/generate_pnp.py)
- [`RULES.md`](file:///z:/home/mike/antigravity/rogue-agent/RULES.md)
- [`tests/test_v330_step2a_and_singularity.py`](file:///z:/home/mike/antigravity/rogue-agent/tests/test_v330_step2a_and_singularity.py)

---

## 1. Executive Summary & Architectural Motivation

### 1.1 Context & Strategic Objectives
Following the deployment of Phase 39 (`v0.32.0`), Pre-SDLC Game Designer analysis and rules-to-code auditing identified three critical alignment and player-agency requirements in **Phase 2 Step 2A (Resolve Black Corruption Cubes, Track Spaces & Version Upgrades)** and **Step 2C (End Game Triggers)**:

1. **Player/Bot Selection Agency on `v3.0` Space 5 (`All Players Return X Colored Dice` — `INV-RETURN-CHOICE-01`):**  
   In [`RULES.md` Section 4 Step 2A](file:///z:/home/mike/antigravity/rogue-agent/RULES.md#L200), when a corruption space requires returning a Colored Die (*"Each player who owns at least 1 Colored Module Die across Under Development, In Production, or Ready for Release must return up to X Colored Module Dice of their choice to the Market supply"*), players have full tactical choice of which owned Colored Die to return. Previously, [`return_player_colored_dice_step2a`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L534-L589) hardcoded a rigid zone-iteration loop without consulting `player.bot` and blindly returned active `In Production` Income dice (even a `$6` Yellow `Y1` or `Y3` die about to yield `+1 Corporate Secret` in Phase 3A!) ahead of a redundant `In Production` Shield die whose threat color had `0` exited cubes. Adding `choose_colored_dice_to_return` to [`BaseBot`](file:///z:/home/mike/antigravity/rogue-agent/sim/bots/base.py) with a rigorous 7-tier mathematical valuation hierarchy restores full strategic agency.
2. **White Contractor Sacrifice Enforcement in Step 2A & Step 2B (`INV-STEP2A-CONTRACTOR-SACRIFICE-01`):**  
   Per [`RULES.md` Section 7 Glossary](file:///z:/home/mike/antigravity/rogue-agent/RULES.md#L486), **White "Contractor" Dice** *"Never enter Under Development—they are discarded to the general supply if they roll an unresolved Glitch, are sacrificed to Green Malware, or expire at the end of Phase 2."* However, in [`demote_player_dice_step2a`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L514-L517) (and in the `in_production_dice` fallback of Step 2B Green Malware resolution at [lines 461–488](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L461-L488)), if a White Contractor die deployed in `player.in_production_dice` was selected to be glitched, it was erroneously appended to `player.glitched_dice` (contaminating the permanent CI/CD pipeline with a temporary die) or left orphaned in `player.in_production_dice` when `player.contractor_dice.pop(0)` was called. Enforcing **Contractor Sacrifice** across both Step 2A and Step 2B guarantees `DieColor.WHITE` dice are always removed from *both* `in_production_dice` and `contractor_dice`, returned to `engine.state.contractor_supply`, and **never** enter `glitched_dice`.
3. **Immediate Game End on `v3.0` Space 6 Singularity (`INV-SINGULARITY-IMMEDIATE-01`):**  
   When the final (`6th`) space of `v3.0` (*Zero-Day Override* or *Corrupted Kernel*) is covered by a Black Cube in Step 2A, **Project: SETEC completes compilation (`Singularity`) and the game ends IMMEDIATELY at the end of Step 2A!**
   - Because Step 2B and Phase 3 are skipped on Singularity, any `add_cubes` on `v3.0` Space 6 (*Zero-Day Override* `Add 2R, 2B, 2G` and *Corrupted Kernel* `Add 2R, 2B, 1G`) are completely dead/obsolete and must be excised from [`sim/entities.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/entities.py), [`RULES.md`](file:///z:/home/mike/antigravity/rogue-agent/RULES.md), and [`pnp/generate_pnp.py`](file:///z:/home/mike/antigravity/rogue-agent/pnp/generate_pnp.py).
   - Space 6's printed non-cube effect (*Corrupted Kernel* Space 6: `Lose 1 Secret`) still resolves immediately in Step 2A before termination, and [`resolve_corruption_space`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L633-L639) must populate full Patient Zero metadata (`elimination_round`, `elimination_reason`, `breach_depth`) when `player.secrets <= 0`.
   - Upon immediate Step 2A Singularity termination, temporary White Contractor dice are returned to supply, surviving `in_production_dice` are returned to `ready_for_release_dice` (and [`evaluate_end_game`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/end_game.py) counts active Colored Dice across `ready_for_release_dice + in_production_dice`), and `engine.state.game_over = True` (`is_final_round = False`) is set immediately.

---

### 1.2 Summary Comparison Table (`v0.32.0` vs. `v0.33.0`)

```
+------------------------------------------------------------------------------------------------------------+
|                                       v0.33.0 ARCHITECTURAL BASELINE                                       |
+-------------------------------------+-----------------------------------+----------------------------------+
| Feature / Invariant                 | Legacy Baseline (v0.32.0)         | New Baseline (v0.33.0)           |
+-------------------------------------+-----------------------------------+----------------------------------+
| Step 2A Return Colored Die          | Hardcoded zone loop: Under Dev -> | Bot hook choose_colored_dice_to_ |
| (INV-RETURN-CHOICE-01)              | In Prod Income -> In Prod Shield  | return with 7-tier mathematical  |
|                                     | -> Ready for Release              | valuation (Redundant Shield T2   |
|                                     |                                   | before Ready T3 & Income T4/T5!) |
| Step 2A Glitch White Contractor     | Appended White die to             | Contractor Sacrifice: removed    |
| (INV-STEP2A-CONTRACTOR-SACRIFICE-01)| glitched_dice (pipeline bug!)     | from in_production & contractor_ |
|                                     |                                   | dice, returned to supply!        |
| choose_dice_to_glitch White Prio    | Treated White equal to permanent  | Prefers sacrificing WHITE within |
|                                     | dice                              | same tactical tier (0 pipeline   |
|                                     |                                   | recovery debt)                   |
| v3.0 Space 6 Cube Injection         | Zero-Day: +2R, 2B, 2G             | Zero-Day: "Singularity" ({} cubes|
| (INV-SINGULARITY-IMMEDIATE-01)      | Corrupted Kernel: Lose 1 Secret   | Corrupted Kernel: "Singularity:  |
|                                     | + 2R, 2B, 1G                      | Lose 1 Secret" ({} cubes)        |
| Step 2A Lose Secrets Breach Meta    | Only set is_patient_zero = True   | Populates is_patient_zero,       |
|                                     | (missing breach_depth/reason/rd)  | elimination_round, reason, and   |
|                                     |                                   | breach_depth = max(0, -secrets)  |
| Singularity End Game Timing         | Resolved Step 2B + Phase 3 Final  | Ends IMMEDIATELY at end of       |
| (INV-SINGULARITY-IMMEDIATE-01)      | Round (is_final_round = True,     | Step 2A! Skips Step 2B & Phase 3 |
|                                     | game_over = False)                | (game_over = True,               |
|                                     |                                   | is_final_round = False)          |
| Tiebreaker #2 Active Colored Dice   | Counted only ready_for_release_   | Returns in_production_dice on    |
| on Mid-Phase-2 Game End             | dice (missed in_production_dice   | Singularity AND counts ready_for |
|                                     | during mid-Phase-2 termination!)  | _release + in_production in      |
|                                     |                                   | evaluate_end_game!               |
+-------------------------------------+-----------------------------------+----------------------------------+
```

### 1.3 Architectural Execution Flow: Step 2A Resolution & Immediate Singularity Termination

```mermaid
sequenceDiagram
    autonumber
    participant Tower as Cube Tower Drop
    participant S2A as Phase 2 Step 2A (Black Cubes)
    participant Bot as Player / BaseBot Hooks
    participant S2B as Phase 2 Step 2B (Attack Cubes)
    participant End as End Game Scoring (Phase 4)

    Tower->>S2A: Exited Cubes (Black, Red, Blue, Green)
    loop For each exited Black Cube
        S2A->>S2A: Advance corruption_track += 1
        S2A->>S2A: resolve_corruption_space(space)
        opt space.demote_dice > 0
            S2A->>Bot: choose_dice_to_glitch(player, in_prod, count, threats)
            Note over S2A,Bot: White Contractor -> Contractor Supply (NEVER glitched_dice!)
        end
        opt space.return_colored_dice > 0
            S2A->>Bot: choose_colored_dice_to_return(player, count, threats)
            Note over S2A,Bot: 7-Tier Valuation across Glitched, Scanned, In Prod, Ready
        end
        opt space.lose_secrets > 0
            S2A->>S2A: Deduct secrets; if <= 0 set Patient Zero + breach_depth
        end
        alt v3.0 Space 6 Covered (Singularity!)
            S2A->>S2A: singularity_triggered = True; break loop!
        end
    end
    alt singularity_triggered == True
        S2A->>S2A: Expire White Contractors -> contractor_supply
        S2A->>S2A: Return surviving non-White in_production_dice -> ready_for_release_dice
        S2A->>S2A: Set game_over = True, is_final_round = False
        S2A->>S2A: Set end_reason = TOTAL_WIPEOUT (if all breached) else SINGULARITY
        Note over S2A,S2B: SKIP Step 2B (Attack Cubes) & SKIP Phase 3!
        S2A->>End: Transition directly to evaluate_end_game()
    else Normal Drop (No Singularity)
        S2A->>S2B: Proceed to Step 2B (Resolve Red, Blue, Green Attack Cubes)
    end
```

---

## 2. Detailed Invariant Specifications

### 2.1 `INV-RETURN-CHOICE-01`: Step 2A `All Players Return X Colored Dice` Player/Bot Selection Hook

1. **Method Signature in [`sim/bots/base.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/bots/base.py):**
   ```python
   def choose_colored_dice_to_return(
       self,
       player: PlayerState,
       count: int,
       threat_strengths: Dict[CubeColor, int],
   ) -> List[Die]:
   ```
2. **Candidate Eligibility:**
   - All owned Colored Software Module Dice (`d.color not in (DieColor.GRAY, DieColor.WHITE)`) across all four terminal mat zones:
     - `player.glitched_dice` (`Glitched Box`)
     - `player.scanned_dice` (`Scanned Box`)
     - `player.in_production_dice` (`In Production Area`)
     - `player.ready_for_release_dice` (`Ready for Release Zone`)
   - Unpurchased dice in `player.personal_purple_reserve` are **not** owned active/offline dice on the mat and remain completely immune (`INV-PURPLE-01`).
   - If the total number of eligible owned Colored Dice is `<= count`, return all eligible Colored Dice immediately.
3. **Deterministic 7-Tier Mathematical Valuation Hierarchy:**
   - Every candidate Colored Die is scored by a deterministic tuple `(tier, ...)` and sorted in **ascending** order (lowest tuple value is returned first).
   - Common tiebreaker terms for all tiers:
     - `is_purple = 1 if die.color == DieColor.PURPLE else 0` (prefer returning Central Market colors `0` before irreplaceable Purple Specialist dice `1`, since returned Market dice can be re-bought whereas returned Purple dice are permanently scrapped).
     - `cost = getattr(die, "cost", 0)` (prefer returning cheaper `$4` dice before `$5`/`$6` dice).
     - `die_id = getattr(die, "die_id", 0)` (deterministic ascending `die_id` tiebreaker).
   - **Redundant Shield Detection in `player.in_production_dice`:**
     - Group all shield dice in `player.in_production_dice` (both permanent and White Contractor shields) by their effective shield color (`ShieldColor.RED`, `ShieldColor.BLUE`, `ShieldColor.GREEN`, `ShieldColor.ANY`).
     - A Colored shield die in `player.in_production_dice` is classified as a **Redundant Shield (Tier 2)** if:
       1. Its committed `production_role` is `RED_SHIELD`, `BLUE_SHIELD`, or `GREEN_SHIELD` and the corresponding exited cube threat `threat_strengths.get(cube_color, 0) == 0`, **OR**
       2. Its committed `production_role` is `ANY_SHIELD` and total exited attack cubes `sum(threat_strengths.get(c, 0) for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)) == 0`, **OR**
       3. It provides surplus block beyond the exited threat of its color (when multiple shields are committed to the same color, sort shields of that color by `(is_white, -has_phase3_output, -is_purple, -cost, -die_id)` to assign "active needed blocking" to White/high-value shields first; any shield die whose cumulative block begins at or above `threat_strengths[color]` is redundant!).
       4. **Exception for Dual-Output Shields with Phase 3A Yield:** If a shield die has a Phase 3A income/triage output (`face.money > 0 or face.patches > 0 or face.secrets > 0 or face.star_code in ("B3", "R1", "G1", "G2")`), it still produces value in Phase 3A even if its shield block is redundant! Therefore, a redundant shield with Phase 3A output is evaluated at **Tier 4** (or **Tier 5** if Star) rather than Tier 2.
   - **The 7 Valuation Tiers (Ascending Priority to Return):**
     - **Tier 0 (`Glitched Box` — `player.glitched_dice`):**  
       `key = (0, 0, 0, is_purple, cost, die_id)` — Offline, requires 2 rounds of pipeline triage/graduation. Prime return candidate.
     - **Tier 1 (`Scanned Box` — `player.scanned_dice`):**  
       `key = (1, 0, 0, is_purple, cost, die_id)` — Offline, requires 1 round of graduation before rolling.
     - **Tier 2 (`In Production` Redundant Pure Shield):**  
       `key = (2, 0, 0, is_purple, cost, die_id)` — Deployed shield with `0` Phase 3A output whose block is unneeded this round (e.g., blocking `0` exited cubes or surplus block). Returning it costs `0` defense and `0` Phase 3A income!
     - **Tier 3 (`Ready for Release` — `player.ready_for_release_dice`):**  
       `key = (3, 0, 0, is_purple, cost, die_id)` — Online unrolled die (e.g. if Step 2A is invoked in isolation or unrolled dice remain in Ready).
     - **Tier 4 (`In Production` Non-Star Income Face):**  
       `key = (4, face_economic_score, 0, is_purple, cost, die_id)` where `face_economic_score = eff.money + 2 * eff.patches + 8 * eff.secrets`.
     - **Tier 5 (`In Production` Star `★` Income / Dual-Output Face):**  
       `key = (5, face_economic_score, 0, is_purple, cost, die_id)` where `face_economic_score` includes Star economic equivalents (`Y3` / `B2` / `Y1` secret potential = `+8`, `B3` pipeline triage = `+3`, `G3` = `1 + 2*2 = 5`, `R3` = `3`, `Y2` = `4`).
     - **Tier 6 (`In Production` Needed Active Shield):**  
       `key = (6, shield_priority, block_amount, is_purple, cost, die_id)` where `shield_priority` ranks the criticality of the threat being blocked:
       - `GREEN_SHIELD`: `shield_priority = 1` (prevents 1 glitch)
       - `RED_SHIELD` (when `player.money >= threat_strengths[RED]`): `shield_priority = 2` (saves `$1` cash)
       - `ANY_SHIELD`: `shield_priority = 3` (flexible reactive block)
       - `RED_SHIELD` (when `player.money < threat_strengths[RED]`): `shield_priority = 4` (prevents Unpaid Ransom Secret leak)
       - `BLUE_SHIELD`: `shield_priority = 5` (directly protects Corporate Secrets — highest preservation priority!)
4. **Execution & State Cleanup in [`return_player_colored_dice_step2a`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L534-L589):**
   - Update signature to accept `threat_strengths: Optional[Dict[CubeColor, int]] = None`:
     ```python
     def return_player_colored_dice_step2a(
         engine: GameEngine,
         player: PlayerState,
         rolled_dice: List[Die],
         commitments: Dict[int, ShieldColor],
         count: int,
         threat_strengths: Optional[Dict[CubeColor, int]] = None,
     ) -> None:
     ```
   - Query `player.bot.choose_colored_dice_to_return(player, count, threats)` if `hasattr(player.bot, "choose_colored_dice_to_return")`, and fall back to `BaseBot(player.player_id).choose_colored_dice_to_return(player, count, threats)` for any remainder if a custom test bot returns fewer than `count` dice while more owned Colored Dice exist.
   - For each validated chosen Colored Die (`die.color not in (DieColor.GRAY, DieColor.WHITE)` and `die` present in one of the player's 4 zones):
     - Remove `die` from its current zone (`glitched_dice`, `scanned_dice`, `in_production_dice`, or `ready_for_release_dice`).
     - If `die in rolled_dice`, find `idx = rolled_dice.index(die)` and `commitments.pop(idx, None)`.
     - Reset transient die attributes:
       ```python
       die.production_role = None
       die.is_locked = False
       die.chosen_choice_index = None
       die.current_face = None
       ```
     - If `die.color in engine.state.market` (i.e. `RED`, `BLUE`, `GREEN`, `YELLOW`), increment `engine.state.market[die.color] += 1`. (If `die.color == DieColor.PURPLE`, it is permanently scrapped and never added to `engine.state.market`, preserving `INV-PURPLE-02`).

---

### 2.2 `INV-STEP2A-CONTRACTOR-SACRIFICE-01`: White Contractor Sacrifice Enforcement in Step 2A & Step 2B

1. **Step 2A Glitch Resolution (`demote_player_dice_step2a` in [`sim/engine/phase2_threat.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L496-L532)):**
   - Update signature to accept `engine: Optional[GameEngine] = None` (defaulting to `None` for backward compatibility if any external caller omits it, though `resolve_corruption_space` will always pass `engine=engine`):
     ```python
     def demote_player_dice_step2a(
         player: PlayerState,
         rolled_dice: List[Die],
         commitments: Dict[int, ShieldColor],
         count: int,
         threat_strengths: Optional[Dict[CubeColor, int]] = None,
         engine: Optional[GameEngine] = None,
     ) -> None:
     ```
   - When a die `die` in `player.in_production_dice` is selected to be glitched in Step 2A:
     - Remove `die` from `player.in_production_dice`.
     - If `die in rolled_dice`, pop its index `idx = rolled_dice.index(die)` from `commitments`.
     - Reset transient die attributes (`die.production_role = None`, `die.is_locked = False`, `die.chosen_choice_index = None`, `die.current_face = None`).
     - **White Contractor Sacrifice Branch (`if die.color == DieColor.WHITE:`):**
       - If `die in player.contractor_dice`, remove `die` from `player.contractor_dice`.
       - Update `player.hired_contractor_count = len(player.contractor_dice)`.
       - If `engine is not None`: increment `engine.state.contractor_supply += 1`.
       - **NEVER append `die` to `player.glitched_dice`!**
     - **Permanent Die Branch (`else` — `GRAY` or `Colored`):**
       - Append `die` to `player.glitched_dice`.
2. **Bot Glitch Selection Priority (`choose_dice_to_glitch` in [`sim/bots/base.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/bots/base.py#L513-L549)):**
   - Within the same tactical tier (e.g., Tier 0 Redundant Shield, Tier 1 Low-Value `$1` Income, Tier 3 Critical Shield), prefer sacrificing a temporary `DieColor.WHITE` Contractor die ahead of a permanent `Gray` or `Colored` die (`is_not_white = 0 if die.color == DieColor.WHITE else 1`), because sacrificing a White Contractor die avoids 2 rounds of `Under Development` pipeline congestion while a permanent die would suffer a 2-round offline penalty:
     ```python
     def sort_key(die: Die) -> Tuple[int, int, int, int, int]:
         face = die.effective_face or die.current_face
         is_not_white = 0 if die.color == DieColor.WHITE else 1
         is_colored = 0 if die.color in (DieColor.GRAY, DieColor.WHITE) else 1
         cost = getattr(die, "cost", 0)
         # Tier 0: Redundant shield check
         if face and face.is_shield:
             color = face.shield_color
             if color == ShieldColor.ANY:
                 threat = sum(threat_strengths.get(c, 0) for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN))
             else:
                 c_map = {ShieldColor.RED: CubeColor.RED, ShieldColor.BLUE: CubeColor.BLUE, ShieldColor.GREEN: CubeColor.GREEN}
                 threat = threat_strengths.get(c_map.get(color), 0) if color else 0
             if threat == 0:
                 return (0, is_not_white, is_colored, cost, die.die_id)
         # Tier 1: Low income ($1, 0 research, non-star)
         if face and face.money <= 1 and face.patches == 0 and not face.is_star and not face.is_shield:
             return (1, is_not_white, face.money, is_colored, cost)
         # Tier 2: Valuable income
         if face and not face.is_shield:
             return (2, is_not_white, face.money + face.patches * 2 + face.secrets * 8, is_colored, cost)
         # Tier 3: Active needed shield last
         return (3, is_not_white, is_colored, cost, die.die_id)
     ```
3. **Step 2B Green Malware White Contractor Cleanup ([`sim/engine/phase2_threat.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L455-L492) & [`web/controller/phase3_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase3_actions.py#L218-L250)):**
   - In [`resolve_player_defense_and_wear`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L461-L488):
     - When `sacrifice and len(player.contractor_dice) > 0`:
       - Pop `c_die = player.contractor_dice.pop(0)`.
       - **Also remove `c_die` from `player.in_production_dice` if `c_die in player.in_production_dice`!** (Previously, `player.contractor_dice.pop(0)` left `c_die` inside `player.in_production_dice`, allowing a sacrificed contractor die to either be hit a second time by Green Malware or get double-counted during end-of-Phase-2 contractor expiration!).
       - Reset transient attributes on `c_die` and increment `engine.state.contractor_supply += 1`.
     - In `elif len(player.in_production_dice) > 0:`:
       - Update `glitch_sort_key` to include `is_not_white = 0 if d.color == DieColor.WHITE else 1` so White Contractor dice in `in_production_dice` are prioritized for sacrifice.
       - After removing `target_die` from `player.in_production_dice`, reset transient attributes (`target_die.production_role = None`, `target_die.is_locked = False`, `target_die.chosen_choice_index = None`, `target_die.current_face = None`).
       - **If `target_die.color == DieColor.WHITE`:** remove `target_die` from `player.contractor_dice` (if present) and increment `engine.state.contractor_supply += 1` (**never** append `target_die` to `player.glitched_dice`!).
       - **Else:** append `target_die` to `player.glitched_dice`.
   - Apply the exact same safeguard in [`web/controller/phase3_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase3_actions.py#L218-L251) during the auto-fallback Green Malware loop.

---

### 2.3 `INV-SINGULARITY-IMMEDIATE-01`: `v3.0` Space 6 Singularity — No Added Cubes & Immediate Game End at Step 2A

1. **Excise Obsolete `add_cubes` from `v3.0` Space 6 Definitions:**
   - In [`sim/entities.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/entities.py) (both `AGGRESSIVE` and `STANDARD` profiles in `get_all_version_cards`):
     - *Zero-Day Override* (`v3.0`) Space 6:
       ```python
       CorruptionSpace(
           index=6,
           label="Singularity",
           is_singularity=True,
       ),
       ```
       (`add_cubes` defaults to `{}`).
     - *Corrupted Kernel* (`v3.0`) Space 6:
       ```python
       CorruptionSpace(
           index=6,
           label="Singularity: Lose 1 Secret",
           lose_secrets=1,
           is_singularity=True,
       ),
       ```
       (`add_cubes` defaults to `{}`).
   - In [`RULES.md` Section 6C](file:///z:/home/mike/antigravity/rogue-agent/RULES.md#L352-L364) (both Profile 1 Standard and Profile 2 Aggressive tables):
     - *Zero-Day Override* Space 6: `**Singularity**` (instead of `**Singularity:** Add 2R, 2B, 2G`).
     - *Corrupted Kernel* Space 6: `**Singularity:** Lose 1 Secret` (instead of `**Singularity:** Lose 1 Secret + Add 2R, 2B, 1G`).
   - In [`pnp/generate_pnp.py`](file:///z:/home/mike/antigravity/rogue-agent/pnp/generate_pnp.py#L436-L450):
     - *Zero-Day Override* Space 6 (`VERSION_TILES[0]`): `VersionTrackSpaceSpec(6, "**SINGULARITY!**", is_singularity=True)` (already has no cubes).
     - *Corrupted Kernel* Space 6 (`VERSION_TILES[1]`): update label to `VersionTrackSpaceSpec(6, "**SINGULARITY!**\nLose 1 Secret", is_singularity=True)` so the physical Version Tile accurately displays Space 6's `Lose 1 Secret` effect.
2. **Step 2A `Lose X Corporate Secrets` Patient Zero Metadata Completeness:**
   - In [`resolve_corruption_space`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L633-L639), when `space.lose_secrets > 0` reduces `player.secrets <= 0`:
     ```python
     # 6. Lose Secrets
     if space.lose_secrets > 0:
         for player in engine.state.players:
             player.secrets -= space.lose_secrets
             if player.secrets <= 0:
                 player.is_patient_zero = True
                 if player.elimination_round is None:
                     player.elimination_round = engine.state.current_round
                 if player.elimination_reason is None:
                     player.elimination_reason = "Total Breach (<= 0 Secrets)"
                 player.breach_depth = max(0, -player.secrets)
     ```
   - This guarantees that if a player at `1` or `2` Corporate Secrets is eliminated in Step 2A (e.g. on *Corrupted Kernel* Space 4 `Lose 1 Secret` or Space 6 `Singularity: Lose 1 Secret`), their `elimination_round`, `elimination_reason`, and `breach_depth` are 100% populated even when Step 2B is skipped on Singularity!
3. **Immediate Game End on Step 2A Singularity (`execute_phase_2` in [`sim/engine/phase2_threat.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L66-L210)):**
   - During Step 2A, Black Cubes are placed one by one onto the active Corruption Track (including spillover from `v2.0` Space 5 onto `v3.0` if applicable, though `v3.0` has 6 spaces).
   - When the `6th` space of `v3.0` is covered (`engine.state.corruption_track >= engine.state.corruption_track_capacity` and `engine.state.current_version_index >= len(engine.state.version_deck) - 1`, or if overflow onto `v3.0` reaches `next_ver.track_capacity`):
     - Space 6's printed effect (`resolve_corruption_space`) resolves first.
     - `engine.state.singularity_triggered = True` is set, and the Black Cube loop breaks immediately.
   - **Check `if engine.state.singularity_triggered:` immediately after the Step 2A Black Cube loop (and P2 Chaos Profiteer check):**
     - **Skip Step 2B completely!** Do **not** call `resolve_player_defense_and_wear` for any player. Set `attack_strengths = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0}` (or record exited cube counts in telemetry with `0` resolved attacks, and clear `player._pre_step2b_snapshot = None` and `player.pending_unblocked_green = 0`).
     - **White Contractor Expiration & Production Return for Clean End-Game State:**
       - For every `player` in `engine.state.players`:
         - Return all `player.contractor_dice` to `engine.state.contractor_supply` and clear `player.contractor_dice` (`player.hired_contractor_count = 0`).
         - For every die `d` in `list(player.in_production_dice)`:
           - Remove `d` from `player.in_production_dice`.
           - Reset transient attributes (`d.production_role = None`, `d.is_locked = False`, `d.chosen_choice_index = None`, `d.current_face = None`).
           - If `d.color == DieColor.WHITE`: increment `engine.state.contractor_supply += 1`.
           - Else (`GRAY` or `Colored`): append `d` to `player.ready_for_release_dice`.
     - **Set Immediate Game Over Flags:**
       - `engine.state.game_over = True`
       - `engine.state.is_final_round = False`
       - Check `all_patient_zero = all(p.is_patient_zero for p in engine.state.players)`:
         - If `all_patient_zero`: `engine.state.end_reason = EndGameReason.TOTAL_WIPEOUT`
         - Else: `engine.state.end_reason = EndGameReason.SINGULARITY`
4. **Tiebreaker #2 (`Active Colored Module Dice`) Invariant in [`sim/engine/end_game.py`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/end_game.py#L55-L56):**
   - When a game ends at the end of Phase 3B (after `PATIENT_ZERO` final round) or after our new Singularity Production Return cleanup, all online dice reside in `p.ready_for_release_dice`.
   - However, if a game ends mid-Phase-2 via `TOTAL_WIPEOUT` in Step 2B, surviving non-glitched dice are still sitting in `p.in_production_dice`!
   - To make Tiebreaker #2 (`ready_colored_dice_count`) 100% invariant regardless of whether the game ends in Step 2A (`SINGULARITY`), Step 2B (`TOTAL_WIPEOUT`), or Phase 3B (`PATIENT_ZERO` / `ROUND_LIMIT`), [`evaluate_end_game`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/end_game.py#L55-L56) must compute:
     ```python
     online_dice = list(p.ready_for_release_dice) + [
         d for d in p.in_production_dice if d not in p.ready_for_release_dice
     ]
     "ready_dice_count": sum(1 for d in online_dice if d.color != DieColor.WHITE),
     "ready_colored_dice_count": sum(
         1 for d in online_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)
     ),
     ```
   - Because our Singularity cleanup already moves non-White `in_production_dice` back to `ready_for_release_dice` (and clears `in_production_dice`), `online_dice` will never double-count any die, while also guaranteeing that `TOTAL_WIPEOUT` mid-Phase-2 terminations accurately count active Colored Dice!
5. **Web Controller & Frontend UI Handling ([`web/controller/phase2_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase2_actions.py#L69-L345) & [`web/static/js/components/header.js`](file:///z:/home/mike/antigravity/rogue-agent/web/static/js/components/header.js#L74-L85)):**
   - In [`compile_drop`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase2_actions.py):
     - When `controller.state.game_over` is `True` after `controller.engine._execute_phase_2(...)` (either via immediate `SINGULARITY` or `TOTAL_WIPEOUT`), **do not** collect bot Phase 3A production income in the `compile_drop` loop (`if not is_human and not controller.state.game_over:`)! (Previously, lines 182–193 called `collect_player_production_income` for bots inside `compile_drop` before checking `if controller.state.game_over:` at line 336!).
     - At lines 336–344, when `controller.state.game_over` is `True`:
       - Transition directly to `controller.phase = 4`, `controller.phase_name = "Game Over"`, `controller.subphase = "game_over"`.
       - Compute `end_res = controller.engine.evaluate_end_game()` and `controller.final_result = controller._serialize_end_game_result(end_res)`.
       - Log the appropriate event message:
         - If `controller.state.end_reason == EndGameReason.SINGULARITY`:
           `"SINGULARITY REACHED! Project: SETEC completed v3.0 compilation. Game Over!"`
         - Else (`EndGameReason.TOTAL_WIPEOUT`):
           `"TOTAL WIPEOUT! All corporations suffered Total Breach simultaneously."`
   - In [`web/static/js/components/header.js`](file:///z:/home/mike/antigravity/rogue-agent/web/static/js/components/header.js#L76-L78):
     - Update the alert banner text when `state.singularity_triggered` is true from `"⚠ SINGULARITY TRIGGERED (Final Round)"` to `"⚠ SINGULARITY REACHED (Game Over)"`.

---

## 3. Module-by-Module Implementation Contracts

### 3.1 `sim/entities.py`
In [`get_all_version_cards`](file:///z:/home/mike/antigravity/rogue-agent/sim/entities.py#L600-L629) (Profile 2: `AGGRESSIVE`, lines 600–629) and (Profile 1: `STANDARD`, lines 730–759), update Space 6 of *Zero-Day Override* and *Corrupted Kernel*:

```python
            # v3.0 Zero-Day Override (6 spaces) — Space 6:
                    CorruptionSpace(
                        index=6,
                        label="Singularity",
                        is_singularity=True,
                    ),
            # v3.0 Corrupted Kernel (6 spaces) — Space 6:
                    CorruptionSpace(
                        index=6,
                        label="Singularity: Lose 1 Secret",
                        lose_secrets=1,
                        is_singularity=True,
                    ),
```

---

### 3.2 `sim/bots/base.py`
1. **Update [`choose_dice_to_glitch`](file:///z:/home/mike/antigravity/rogue-agent/sim/bots/base.py#L513-L549):**
   ```python
    def choose_dice_to_glitch(
        self,
        player: PlayerState,
        in_production_dice: List[Die],
        count: int,
        threat_strengths: Dict[CubeColor, int],
    ) -> List[Die]:
        """Selects count dice from In Production to glitch (INV-CORRUPT-CHOICE-01, INV-STEP2A-CONTRACTOR-SACRIFICE-01).
        Heuristic Priority:
        0. Redundant Shields (preferring White Contractor dice first).
        1. Low-Value Income ($1, preferring White Contractor dice first).
        2. Valuable Income (preferring White Contractor dice first).
        3. Essential Shields last (preferring White Contractor dice first).
        """
        if len(in_production_dice) <= count:
            return list(in_production_dice)

        def sort_key(die: Die) -> Tuple[int, int, int, int, int]:
            face = die.effective_face or die.current_face
            is_not_white = 0 if die.color == DieColor.WHITE else 1
            is_colored = 0 if die.color in (DieColor.GRAY, DieColor.WHITE) else 1
            cost = getattr(die, "cost", 0)
            die_id = getattr(die, "die_id", 0)

            # Redundant shield check
            if face and face.is_shield:
                color = face.shield_color
                if color == ShieldColor.ANY:
                    threat = sum(
                        threat_strengths.get(c, 0)
                        for c in (CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN)
                    )
                else:
                    c_map = {
                        ShieldColor.RED: CubeColor.RED,
                        ShieldColor.BLUE: CubeColor.BLUE,
                        ShieldColor.GREEN: CubeColor.GREEN,
                    }
                    threat = threat_strengths.get(c_map.get(color), 0) if color else 0
                if threat == 0:
                    return (0, is_not_white, is_colored, cost, die_id)

            # Low income next
            if face and face.money <= 1 and face.patches == 0 and not face.is_star and not face.is_shield:
                return (1, is_not_white, face.money, is_colored, cost)

            # Valuable income next
            if face and not face.is_shield:
                return (2, is_not_white, face.money + face.patches * 2 + face.secrets * 8, is_colored, cost)

            # Critical shield last
            return (3, is_not_white, is_colored, cost, die_id)

        sorted_dice = sorted(in_production_dice, key=sort_key)
        return sorted_dice[:count]
   ```

2. **Add `choose_colored_dice_to_return` to [`BaseBot`](file:///z:/home/mike/antigravity/rogue-agent/sim/bots/base.py):**
   ```python
    def choose_colored_dice_to_return(
        self,
        player: PlayerState,
        count: int,
        threat_strengths: Dict[CubeColor, int],
    ) -> List[Die]:
        """Selects up to `count` owned Colored Module Dice to return to Market in Step 2A (INV-RETURN-CHOICE-01).

        7-Tier Mathematical Valuation Hierarchy (ascending priority to return):
        - Tier 0: Glitched Box (glitched_dice) -> (0, 0, 0, is_purple, cost, die_id)
        - Tier 1: Scanned Box (scanned_dice) -> (1, 0, 0, is_purple, cost, die_id)
        - Tier 2: In Production Redundant Pure Shield -> (2, 0, 0, is_purple, cost, die_id)
        - Tier 3: Ready for Release (ready_for_release_dice) -> (3, 0, 0, is_purple, cost, die_id)
        - Tier 4: In Production Non-Star Income face -> (4, face_economic_score, 0, is_purple, cost, die_id)
        - Tier 5: In Production Star Income face -> (5, face_economic_score, 0, is_purple, cost, die_id)
        - Tier 6: In Production Needed Active Shield -> (6, shield_priority, block_amount, is_purple, cost, die_id)
        """
        if count <= 0:
            return []

        threats = threat_strengths or {}
        red_threat = threats.get(CubeColor.RED, 0)
        blue_threat = threats.get(CubeColor.BLUE, 0)
        green_threat = threats.get(CubeColor.GREEN, 0)
        total_threat = red_threat + blue_threat + green_threat

        # Identify which In Production shield dice are actively needed vs redundant surplus
        needed_shield_ids: Set[int] = set()
        role_to_cube = {
            ProductionRole.RED_SHIELD: CubeColor.RED,
            ProductionRole.BLUE_SHIELD: CubeColor.BLUE,
            ProductionRole.GREEN_SHIELD: CubeColor.GREEN,
        }

        def _has_phase3_output(face: Optional[Face]) -> bool:
            if face is None:
                return False
            return bool(
                face.money > 0
                or face.patches > 0
                or face.secrets > 0
                or getattr(face, "star_code", None) in ("B3", "R1", "G1", "G2")
            )

        def _face_econ_score(face: Optional[Face]) -> int:
            if face is None:
                return 0
            score = face.money + 2 * face.patches + 8 * face.secrets
            if face.is_star:
                sc = getattr(face, "star_code", None)
                if sc in ("Y1", "B2"):
                    score += 6
                elif sc == "Y2":
                    score += 2
                elif sc == "B3":
                    score += 3
                elif sc == "PURPLE_STAR":
                    score += 4
            return score

        # 1. Color-specific shields: allocate needed absorption to White/high-value shields first
        rem_by_color: Dict[CubeColor, int] = {
            CubeColor.RED: red_threat,
            CubeColor.BLUE: blue_threat,
            CubeColor.GREEN: green_threat,
        }
        for role, c_color in role_to_cube.items():
            role_dice = [
                d for d in player.in_production_dice
                if getattr(d, "production_role", None) == role
                or (
                    getattr(d, "production_role", None) is None
                    and (d.effective_face or d.current_face)
                    and (d.effective_face or d.current_face).is_shield
                    and (d.effective_face or d.current_face).shield_color == ShieldColor(c_color.value)
                )
            ]
            # Sort so White contractors and high-value/Purple shields take the "needed" slots first
            role_dice.sort(
                key=lambda d: (
                    0 if d.color == DieColor.WHITE else 1,
                    0 if _has_phase3_output(d.effective_face or d.current_face) else 1,
                    0 if d.color == DieColor.PURPLE else 1,
                    -getattr(d, "cost", 0),
                    -getattr(d, "die_id", 0),
                )
            )
            for d in role_dice:
                if rem_by_color[c_color] > 0:
                    needed_shield_ids.add(d.die_id)
                    eff = d.effective_face or d.current_face
                    blk = eff.block_amount if (eff and eff.block_amount > 0) else 1
                    rem_by_color[c_color] = max(0, rem_by_color[c_color] - blk)

        # 2. Generic ANY shields: needed only if remaining unblocked threat > 0
        rem_total_after_color = sum(rem_by_color.values())
        any_dice = [
            d for d in player.in_production_dice
            if getattr(d, "production_role", None) == ProductionRole.ANY_SHIELD
            or (
                getattr(d, "production_role", None) is None
                and (d.effective_face or d.current_face)
                and (d.effective_face or d.current_face).is_shield
                and (d.effective_face or d.current_face).shield_color == ShieldColor.ANY
            )
        ]
        any_dice.sort(
            key=lambda d: (
                0 if d.color == DieColor.WHITE else 1,
                0 if _has_phase3_output(d.effective_face or d.current_face) else 1,
                0 if d.color == DieColor.PURPLE else 1,
                -getattr(d, "cost", 0),
                -getattr(d, "die_id", 0),
            )
        )
        for d in any_dice:
            if rem_total_after_color > 0:
                needed_shield_ids.add(d.die_id)
                eff = d.effective_face or d.current_face
                blk = eff.block_amount if (eff and eff.block_amount > 0) else 1
                rem_total_after_color = max(0, rem_total_after_color - blk)

        scored_candidates: List[Tuple[Tuple[int, int, int, int, int, int], Die]] = []

        def _is_colored(d: Die) -> bool:
            return d.color not in (DieColor.GRAY, DieColor.WHITE)

        # Tier 0: Glitched Box
        for d in player.glitched_dice:
            if _is_colored(d):
                is_purple = 1 if d.color == DieColor.PURPLE else 0
                scored_candidates.append(((0, 0, 0, is_purple, getattr(d, "cost", 0), d.die_id), d))

        # Tier 1: Scanned Box
        for d in player.scanned_dice:
            if _is_colored(d):
                is_purple = 1 if d.color == DieColor.PURPLE else 0
                scored_candidates.append(((1, 0, 0, is_purple, getattr(d, "cost", 0), d.die_id), d))

        # Tier 3: Ready for Release
        for d in player.ready_for_release_dice:
            if _is_colored(d):
                is_purple = 1 if d.color == DieColor.PURPLE else 0
                scored_candidates.append(((3, 0, 0, is_purple, getattr(d, "cost", 0), d.die_id), d))

        # Tiers 2, 4, 5, 6: In Production
        for d in player.in_production_dice:
            if not _is_colored(d):
                continue
            is_purple = 1 if d.color == DieColor.PURPLE else 0
            cost = getattr(d, "cost", 0)
            eff = d.effective_face or d.current_face
            role = getattr(d, "production_role", None)
            is_shield_role = role in (
                ProductionRole.RED_SHIELD,
                ProductionRole.BLUE_SHIELD,
                ProductionRole.GREEN_SHIELD,
                ProductionRole.ANY_SHIELD,
            ) or (role is None and eff is not None and eff.is_shield)

            if is_shield_role:
                if d.die_id in needed_shield_ids:
                    # Tier 6: Needed Active Shield
                    if role == ProductionRole.BLUE_SHIELD or (eff and eff.shield_color == ShieldColor.BLUE):
                        s_prio = 5
                    elif role == ProductionRole.RED_SHIELD or (eff and eff.shield_color == ShieldColor.RED):
                        s_prio = 4 if player.money < red_threat else 2
                    elif role == ProductionRole.ANY_SHIELD or (eff and eff.shield_color == ShieldColor.ANY):
                        s_prio = 3
                    else:
                        s_prio = 1
                    blk = eff.block_amount if (eff and eff.block_amount > 0) else 1
                    scored_candidates.append(((6, s_prio, blk, is_purple, cost, d.die_id), d))
                else:
                    # Redundant shield: if it has Phase 3A output (e.g. R1, G1, G2, B3), score as Income Tier 4/5
                    if _has_phase3_output(eff):
                        econ = _face_econ_score(eff)
                        tier = 5 if (eff and eff.is_star) else 4
                        scored_candidates.append(((tier, econ, 0, is_purple, cost, d.die_id), d))
                    else:
                        # Tier 2: Redundant Pure Shield
                        scored_candidates.append(((2, 0, 0, is_purple, cost, d.die_id), d))
            else:
                # Income role (Tier 4 Non-Star or Tier 5 Star)
                econ = _face_econ_score(eff)
                tier = 5 if (eff and eff.is_star) else 4
                scored_candidates.append(((tier, econ, 0, is_purple, cost, d.die_id), d))

        scored_candidates.sort(key=lambda item: item[0])
        return [d for _, d in scored_candidates[:count]]
   ```

---

### 3.3 `sim/engine/phase2_threat.py`
1. **Immediate Singularity Termination in [`execute_phase_2`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L66-L210):**
   ```python
        # Step 2A: Resolve Black (Corruption) Cubes & Version Upgrades
        black_dropped = exited_cubes.get(CubeColor.BLACK, 0)

        for _ in range(black_dropped):
            if not engine.state.pending_version_advance:
                engine.state.corruption_track += 1
                curr_track = engine.state.active_version.corruption_track
                space_idx = engine.state.corruption_track
                if curr_track and 1 <= space_idx <= len(curr_track):
                    resolve_corruption_space(
                        engine=engine,
                        space=curr_track[space_idx - 1],
                        player_commitments=player_commitments,
                        exited_cubes=exited_cubes,
                    )

                if engine.state.corruption_track >= engine.state.corruption_track_capacity:
                    if engine.state.current_version_index >= len(engine.state.version_deck) - 1:
                        # Singularity reached on v3.0!
                        engine.state.singularity_triggered = True
                        break
                    else:
                        # Mark pending advance for next round start; excess cubes spill over immediately
                        engine.state.pending_version_advance = True
                        engine.state.overflow_black_cubes_on_next_track = 0
            else:
                # Excess cubes spill over onto the upcoming version's track immediately!
                engine.state.overflow_black_cubes_on_next_track += 1
                next_ver_idx = min(engine.state.current_version_index + 1, len(engine.state.version_deck) - 1)
                next_ver = engine.state.version_deck[next_ver_idx]
                spill_idx = engine.state.overflow_black_cubes_on_next_track
                if next_ver.corruption_track and 1 <= spill_idx <= len(next_ver.corruption_track):
                    resolve_corruption_space(
                        engine=engine,
                        space=next_ver.corruption_track[spill_idx - 1],
                        player_commitments=player_commitments,
                        exited_cubes=exited_cubes,
                    )
                if (
                    next_ver_idx >= len(engine.state.version_deck) - 1
                    and spill_idx >= next_ver.track_capacity
                ):
                    engine.state.current_version_index = next_ver_idx
                    engine.state.corruption_track = spill_idx
                    engine.state.pending_version_advance = False
                    engine.state.overflow_black_cubes_on_next_track = 0
                    engine.state.singularity_triggered = True
                    break

        # Apply P2 (Chaos Profiteer) Star bonus: +$2 per exited black cube
        if black_dropped > 0:
            for player, rolled_dice, _ in player_commitments:
                for die in rolled_dice:
                    if die.current_face and die.current_face.star_code == "P2":
                        player.money += 2 * black_dropped

        if engine.state.singularity_triggered:
            # INV-SINGULARITY-IMMEDIATE-01: Game ends IMMEDIATELY at the end of Step 2A!
            # Step 2B (Attack Cubes) and Phase 3 are skipped completely.
            attack_strengths = {
                CubeColor.RED: 0,
                CubeColor.BLUE: 0,
                CubeColor.GREEN: 0,
            }
            for player in engine.state.players:
                player._pre_step2b_snapshot = None
                player.pending_unblocked_green = 0
                engine.state.contractor_supply += len(player.contractor_dice)
                player.contractor_dice.clear()
                player.hired_contractor_count = 0
                for d in list(player.in_production_dice):
                    player.in_production_dice.remove(d)
                    d.production_role = None
                    d.is_locked = False
                    d.chosen_choice_index = None
                    d.current_face = None
                    if d.color == DieColor.WHITE:
                        engine.state.contractor_supply += 1
                    else:
                        player.ready_for_release_dice.append(d)

            all_patient_zero = all(p.is_patient_zero for p in engine.state.players)
            engine.state.game_over = True
            engine.state.is_final_round = False
            if all_patient_zero:
                engine.state.end_reason = EndGameReason.TOTAL_WIPEOUT
            else:
                engine.state.end_reason = EndGameReason.SINGULARITY
        else:
            # Step 2B: Resolve Attack Cubes (Red, Blue, Green)
            ...
   ```

2. **Step 2B Green Malware White Contractor Cleanup in [`resolve_player_defense_and_wear`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L455-L493):**
   ```python
    for _ in range(unblocked_green):
        sacrifice = player.bot.choose_malware_sacrifice(
            player_state=player,
            unblocked_green=unblocked_green,
            rng=engine.rng,
        )
        if sacrifice and len(player.contractor_dice) > 0:
            c_die = player.contractor_dice.pop(0)
            if c_die in player.in_production_dice:
                player.in_production_dice.remove(c_die)
            c_die.production_role = None
            c_die.is_locked = False
            c_die.chosen_choice_index = None
            c_die.current_face = None
            player.hired_contractor_count = len(player.contractor_dice)
            engine.state.contractor_supply += 1
        elif len(player.in_production_dice) > 0:
            def glitch_sort_key(d: Die) -> Tuple[int, int, int, int, int]:
                is_not_white = 0 if d.color == DieColor.WHITE else 1
                role = getattr(d, "production_role", None)
                is_shield = 0 if role in (
                    ProductionRole.RED_SHIELD,
                    ProductionRole.BLUE_SHIELD,
                    ProductionRole.GREEN_SHIELD,
                    ProductionRole.ANY_SHIELD,
                ) else 1
                face = d.effective_face or d.current_face
                has_phase3_output = 1 if (
                    face is not None and (
                        face.money > 0
                        or face.patches > 0
                        or face.secrets > 0
                        or getattr(face, "star_code", None) in ("B3", "R1", "G1", "G2")
                    )
                ) else 0
                is_gray = 0 if d.color in (DieColor.GRAY, DieColor.WHITE) else 1
                return (is_not_white, is_shield, has_phase3_output, is_gray, getattr(d, "cost", 0))

            target_die = min(player.in_production_dice, key=glitch_sort_key)
            player.in_production_dice.remove(target_die)
            target_die.production_role = None
            target_die.is_locked = False
            target_die.chosen_choice_index = None
            target_die.current_face = None
            if target_die.color == DieColor.WHITE:
                if target_die in player.contractor_dice:
                    player.contractor_dice.remove(target_die)
                player.hired_contractor_count = len(player.contractor_dice)
                engine.state.contractor_supply += 1
            else:
                player.glitched_dice.append(target_die)
        else:
            # MALWARE FIZZLE: in_production_dice is empty.
            # ZERO dice destroyed from glitched, scanned, or ready_for_release. Zero penalty!
            break
   ```

3. **Step 2A Glitch & Return Functions (`demote_player_dice_step2a`, `return_player_colored_dice_step2a`, `resolve_corruption_space`):**
   ```python
def demote_player_dice_step2a(
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    count: int,
    threat_strengths: Optional[Dict[CubeColor, int]] = None,
    engine: Optional[GameEngine] = None,
) -> None:
    demoted = 0
    threats = threat_strengths or {}
    prod_dice = list(player.in_production_dice)
    if prod_dice:
        if hasattr(player.bot, "choose_dice_to_glitch"):
            chosen = player.bot.choose_dice_to_glitch(player, prod_dice, count, threats)
        else:
            chosen = prod_dice[:count]
        for die in chosen:
            if demoted >= count:
                break
            if die in player.in_production_dice:
                player.in_production_dice.remove(die)
                if die in rolled_dice:
                    idx = rolled_dice.index(die)
                    commitments.pop(idx, None)
                die.production_role = None
                die.is_locked = False
                die.chosen_choice_index = None
                die.current_face = None
                if die.color == DieColor.WHITE:
                    if die in player.contractor_dice:
                        player.contractor_dice.remove(die)
                    player.hired_contractor_count = len(player.contractor_dice)
                    if engine is not None:
                        engine.state.contractor_supply += 1
                else:
                    player.glitched_dice.append(die)
                demoted += 1

    # Fallback to ready_for_release_dice if in_production_dice was empty or exhausted
    if demoted < count and player.ready_for_release_dice:
        ready_pool = list(player.ready_for_release_dice)
        ready_pool.sort(key=lambda d: (0 if d.color == DieColor.GRAY else 1, getattr(d, "cost", 0)))
        while demoted < count and ready_pool:
            die = ready_pool.pop(0)
            if die in player.ready_for_release_dice:
                player.ready_for_release_dice.remove(die)
                die.production_role = None
                die.is_locked = False
                die.chosen_choice_index = None
                die.current_face = None
                if die.color == DieColor.WHITE:
                    if die in player.contractor_dice:
                        player.contractor_dice.remove(die)
                    player.hired_contractor_count = len(player.contractor_dice)
                    if engine is not None:
                        engine.state.contractor_supply += 1
                else:
                    player.glitched_dice.append(die)
                demoted += 1


def return_player_colored_dice_step2a(
    engine: GameEngine,
    player: PlayerState,
    rolled_dice: List[Die],
    commitments: Dict[int, ShieldColor],
    count: int,
    threat_strengths: Optional[Dict[CubeColor, int]] = None,
) -> None:
    if count <= 0:
        return
    threats = threat_strengths or {}
    from sim.bots.base import BaseBot

    if hasattr(player.bot, "choose_colored_dice_to_return"):
        chosen = list(player.bot.choose_colored_dice_to_return(player, count, threats))
    else:
        chosen = BaseBot(player.player_id).choose_colored_dice_to_return(player, count, threats)

    returned = 0
    zones = (
        player.glitched_dice,
        player.scanned_dice,
        player.in_production_dice,
        player.ready_for_release_dice,
    )

    def _return_single_die(die: Die) -> bool:
        if die.color in (DieColor.GRAY, DieColor.WHITE):
            return False
        removed = False
        for z in zones:
            if die in z:
                z.remove(die)
                removed = True
                break
        if not removed:
            return False
        if die in rolled_dice:
            idx = rolled_dice.index(die)
            commitments.pop(idx, None)
        die.production_role = None
        die.is_locked = False
        die.chosen_choice_index = None
        die.current_face = None
        if die.color in engine.state.market:
            engine.state.market[die.color] += 1
        # If Purple, die is scrapped and not returned to market (INV-PURPLE-02)
        return True

    for die in chosen:
        if returned >= count:
            break
        if _return_single_die(die):
            returned += 1

    # Fallback if a custom bot returned fewer dice than count while player still owns Colored Dice
    if returned < count:
        fallback_dice = BaseBot(player.player_id).choose_colored_dice_to_return(
            player, count - returned, threats
        )
        for die in fallback_dice:
            if returned >= count:
                break
            if _return_single_die(die):
                returned += 1
   ```

4. **Update [`resolve_corruption_space`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/phase2_threat.py#L591-L643):**
   ```python
    threat_strengths = {
        CubeColor.RED: exited_cubes.get(CubeColor.RED, 0),
        CubeColor.BLUE: exited_cubes.get(CubeColor.BLUE, 0),
        CubeColor.GREEN: exited_cubes.get(CubeColor.GREEN, 0),
    }

    # 4. Demote Dice
    if space.demote_dice > 0:
        for player, rolled_dice, commitments in player_commitments:
            demote_player_dice_step2a(
                player, rolled_dice, commitments, space.demote_dice, threat_strengths, engine=engine
            )

    # 5. Return Colored Dice
    if space.return_colored_dice > 0:
        for player, rolled_dice, commitments in player_commitments:
            return_player_colored_dice_step2a(
                engine, player, rolled_dice, commitments, space.return_colored_dice, threat_strengths
            )

    # 6. Lose Secrets
    if space.lose_secrets > 0:
        for player in engine.state.players:
            player.secrets -= space.lose_secrets
            if player.secrets <= 0:
                player.is_patient_zero = True
                if player.elimination_round is None:
                    player.elimination_round = engine.state.current_round
                if player.elimination_reason is None:
                    player.elimination_reason = "Total Breach (<= 0 Secrets)"
                player.breach_depth = max(0, -player.secrets)
   ```

---

### 3.4 `sim/engine/end_game.py`
In [`evaluate_end_game`](file:///z:/home/mike/antigravity/rogue-agent/sim/engine/end_game.py#L40-L72), ensure `ready_dice_count` and `ready_colored_dice_count` include any non-White dice in `p.ready_for_release_dice` plus `p.in_production_dice` (without double-counting):

```python
        online_dice = list(p.ready_for_release_dice) + [
            d for d in p.in_production_dice if d not in p.ready_for_release_dice
        ]
        rankings.append(
            {
                ...
                "ready_dice_count": sum(1 for d in online_dice if d.color != DieColor.WHITE),
                "ready_colored_dice_count": sum(
                    1 for d in online_dice if d.color != DieColor.GRAY and d.color != DieColor.WHITE
                ),
```

---

### 3.5 `web/controller/phase2_actions.py`, `web/controller/phase3_actions.py`, & `web/static/js/components/header.js`
1. **In [`web/controller/phase2_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase2_actions.py#L182-L194):**
   - Guard bot income collection so it only runs when `not controller.state.game_over`:
     ```python
        if not is_human and not controller.state.game_over:
            money_before = player.money
            patches_before = player.patches
            secrets_before = player.secrets
            collect_player_production_income(controller.engine, player, None)
            meta["income_collected_this_turn"] = True
            income_breakdowns[pid] = {
                "money": max(0, player.money - money_before),
                "patches": max(0, player.patches - patches_before),
                "secrets": max(0, player.secrets - secrets_before),
                "details": details,
            }
     ```
   - At [lines 336–344](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase2_actions.py#L336-L344), handle both `SINGULARITY` and `TOTAL_WIPEOUT` when `controller.state.game_over` is `True`:
     ```python
    # Check end game triggers from Step 2A / Step 2C
    if controller.state.game_over:
        controller.phase = 4
        controller.phase_name = "Game Over"
        controller.subphase = "game_over"
        end_res = controller.engine.evaluate_end_game()
        controller.final_result = controller._serialize_end_game_result(end_res)
        if controller.state.end_reason == EndGameReason.SINGULARITY:
            controller.event_log.append(
                "SINGULARITY REACHED! Project: SETEC completed v3.0 compilation. Game Over!"
            )
        else:
            controller.event_log.append(
                "TOTAL WIPEOUT! All corporations suffered Total Breach simultaneously."
            )
        return controller.get_full_state()
     ```
2. **In [`web/controller/phase3_actions.py`](file:///z:/home/mike/antigravity/rogue-agent/web/controller/phase3_actions.py#L218-L251):**
   - Synchronize the Green Malware fallback loop so `player.contractor_dice.pop(0)` also removes the popped White Contractor die from `player.in_production_dice` (if present), and if `target_die` in `player.in_production_dice` has `target_die.color == DieColor.WHITE`, it is removed from `player.contractor_dice` and returned to `controller.state.contractor_supply` instead of being appended to `player.glitched_dice`.
3. **In [`web/static/js/components/header.js`](file:///z:/home/mike/antigravity/rogue-agent/web/static/js/components/header.js#L76-L78):**
   - Update `alertEl.innerText = "⚠ SINGULARITY REACHED (Game Over)";`.

---

### 3.6 `RULES.md` & `pnp/generate_pnp.py`
1. **In [`RULES.md`](file:///z:/home/mike/antigravity/rogue-agent/RULES.md):**
   - **Section 4 Step 2A (`All Players Glitch X Dice`, line 199):** Add explicit note: *"If you choose to glitch a **White Contractor Die** in **In Production**, it triggers **Contractor Sacrifice** and is discarded directly to the general supply instead of entering **Under Development**."*
   - **Section 4 Step 2A (`Singularity (v3.0 Track Fills)`, line 208):** Update to:
     *"When the final (`6th`) space of `v3.0` is covered by a Black Cube, resolve that space's printed effect (e.g., *Corrupted Kernel* `Lose 1 Secret`), and **Singularity is triggered—the game ends IMMEDIATELY at the end of Step 2A!** Step 2B (Attack Cubes) and Phase 3 are skipped completely; all surviving non-Contractor dice in **In Production** return to **Ready for Release**, and players proceed directly to **Section 5: End Game & Victory Scoring**."*
   - **Section 4 Step 2C (`Check End Game Triggers`, lines 237–244):** Remove Singularity from the Final Round triggers (since Singularity ends the game immediately in Step 2A) and specify that the Final Round is triggered in Step 2C when one or more (but not all) players suffer a **Total Data Breach (`<= 0 Secrets`)** in Step 2A or Step 2B.
   - **Section 6C (`Sample SETEC Version Cards`, lines 352–353 and 363–364):**
     - *Zero-Day Override* Space 6: `**Singularity**`
     - *Corrupted Kernel* Space 6: `**Singularity:** Lose 1 Secret`
   - **Section 7 Glossary (`Contractor Sacrifice`, line 506, and `Singularity`, line 508):**
     - Update **Contractor Sacrifice** definition to include Step 2A Corruption glitch effects alongside Phase 1 Glitch and Step 2B Green Malware.
     - Update **Singularity** definition: *"Triggered immediately in **Phase 2 Step 2A** when the final (`6th`) space of the `v3.0` **Corruption Track** is covered by a **Black Cube**. After resolving Space 6's printed effect, the game ends **immediately** (skipping Step 2B and Phase 3) and proceeds directly to victory scoring."*
2. **In [`pnp/generate_pnp.py`](file:///z:/home/mike/antigravity/rogue-agent/pnp/generate_pnp.py#L450):**
   - Update *Corrupted Kernel* (`v3.0`) Space 6 in `VERSION_TILES` to:
     ```python
     VersionTrackSpaceSpec(6, "**SINGULARITY!**\nLose 1 Secret", is_singularity=True),
     ```

---

## 4. Audit of Existing Regression Tests Requiring Updates

An exhaustive grep across `tests/` identified **4 existing test methods** that assert the legacy `v0.32.0` Final Round Singularity behavior (`is_final_round = True`, `game_over = False` after `v3.0` Space 6 fills). These 4 tests must be updated to assert the canonical `v0.33.0` Immediate Singularity Game End (`singularity_triggered = True`, `game_over = True`, `is_final_round = False`):

| Existing Test File | Test Method & Line Numbers | Legacy Assertion (`v0.32.0`) | Updated Assertion (`v0.33.0`) |
| :--- | :--- | :--- | :--- |
| [`tests/test_engine_phases.py`](file:///z:/home/mike/antigravity/rogue-agent/tests/test_engine_phases.py#L122-L144) | `test_phase2_singularity_trigger_on_v3` (lines 140–143) | `assertTrue(is_final_round)`<br>`assertFalse(game_over)` | `assertTrue(singularity_triggered)`<br>`assertFalse(is_final_round)`<br>`assertTrue(game_over)`<br>`assertEqual(end_reason, EndGameReason.SINGULARITY)` |
| [`tests/test_v150_corruption_tracks.py`](file:///z:/home/mike/antigravity/rogue-agent/tests/test_v150_corruption_tracks.py#L228-L248) | `test_v3_singularity_space_6_resolution` (lines 246–247) | `assertTrue(singularity_triggered)`<br>`assertTrue(is_final_round)` | `assertTrue(singularity_triggered)`<br>`assertTrue(game_over)`<br>`assertFalse(is_final_round)`<br>`assertEqual(end_reason, EndGameReason.SINGULARITY)` |
| [`tests/test_v290_rules_streamlining.py`](file:///z:/home/mike/antigravity/rogue-agent/tests/test_v290_rules_streamlining.py#L122-L144) | `test_v3_singularity_remains_immediate` (lines 142–143) | `assertTrue(singularity_triggered)`<br>`assertTrue(is_final_round)` | `assertTrue(singularity_triggered)`<br>`assertTrue(game_over)`<br>`assertFalse(is_final_round)`<br>`assertEqual(end_reason, EndGameReason.SINGULARITY)` |
| [`tests/version_baselines/test_v03_rules.py`](file:///z:/home/mike/antigravity/rogue-agent/tests/version_baselines/test_v03_rules.py#L385-L435) | `test_final_round_singularity_triggers_phase_3` (lines 385–435) | Asserted `is_final_round = True`, `game_over = False`, and that `_execute_phase_3()` ran for both bots. | Update to verify that covering `v3.0` Space 6 sets `singularity_triggered = True`, `game_over = True`, `is_final_round = False`, and `_execute_phase_3()` is a no-op (`len(p0_acted) == 0`, `len(p1_acted) == 0`). |

*(Note: Historical self-contained version card fixtures in `tests/version_baselines/test_v082_payloads.py` construct their own inline `VersionCard` instances and do not fail when `sim/entities.py` removes `add_cubes` from Space 6).*

---

## 5. Comprehensive Test Verification Matrix (`tests/test_v330_step2a_and_singularity.py`)

A dedicated unit and integration test suite [`tests/test_v330_step2a_and_singularity.py`](file:///z:/home/mike/antigravity/rogue-agent/tests/test_v330_step2a_and_singularity.py) must be authored to validate all `v0.33.0` invariants:

| Test ID | Targeted Invariant | Setup / Scenario Description | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **TEST-V330-01** | `INV-RETURN-CHOICE-01` | **7-Tier Full Ordering Verification:** Player owns Colored Dice across all 7 tiers (`Glitched`, `Scanned`, `In Prod Redundant Shield`, `Ready for Release`, `In Prod Non-Star Income`, `In Prod Star Income`, `In Prod Needed Blue Shield`). Call `choose_colored_dice_to_return(player, count=7, threat_strengths={BLUE: 1})`. | Returned list strictly follows Tier 0 $\to$ Tier 1 $\to$ Tier 2 $\to$ Tier 3 $\to$ Tier 4 $\to$ Tier 5 $\to$ Tier 6. |
| **TEST-V330-02** | `INV-RETURN-CHOICE-01` | **Tier 2 Redundant Shield vs Tier 4/5 Income:** Player has 1 Yellow `$6` `Y3` die (`+1 Secret`, Income role) and 1 Red `$5` Shield die (`Block 1 Red`, `RED_SHIELD` role) in `in_production_dice`. `exited_cubes[RED] == 0`. Trigger `Return 1 Colored Die`. | Bot selects the redundant Red Shield die (Tier 2) and returns it to `market[RED]`, preserving the Yellow `Y3` Income die (Tier 5) in `in_production_dice`! |
| **TEST-V330-03** | `INV-RETURN-CHOICE-01` | **Surplus Shield Redundancy:** Player commits 2 Blue `$5` Shield dice (`Block 1 Blue` each) to `BLUE_SHIELD`, and has 1 Yellow `$5` die (`+$3`, Income role). Tower drops only `1` Blue cube (`threat_strengths[BLUE] = 1`). Trigger `Return 1 Colored Die`. | One Blue Shield is Needed (Tier 6), while the second Blue Shield is Surplus/Redundant (Tier 2). Bot returns 1 Blue Shield die (leaving 1 Blue Shield to block the 1 Blue cube) and preserves the Yellow `+$3` Income die! |
| **TEST-V330-04** | `INV-RETURN-CHOICE-01` | **Purple Preservation Tiebreaker (`is_purple`):** Player has 1 Red die (`cost=5`) and 1 Purple Specialist die (`cost=0`, `reserve_cost=5`) in `glitched_dice` (both Tier 0). Trigger `Return 1 Colored Die`. | Bot returns the Red die (`is_purple=0`) to Central Market and preserves the irreplaceable Purple Specialist die (`is_purple=1`). |
| **TEST-V330-05** | `INV-RETURN-CHOICE-01` | **Custom Bot Hook & Commitment Revocation:** Custom bot overrides `choose_colored_dice_to_return` to pick a specific Colored Shield die in `in_production_dice`. Call `return_player_colored_dice_step2a`. | Chosen die is removed from `in_production_dice`, its index is popped from `commitments`, its transient attributes (`production_role`, `current_face`, etc.) are reset to `None`/`False`, and `market[color]` increments by `1`. |
| **TEST-V330-06** | `INV-STEP2A-CONTRACTOR-SACRIFICE-01` | **Step 2A Glitch White Contractor Sacrifice:** Player has 1 White Contractor die and 1 Yellow die in `in_production_dice` (and `contractor_dice = [white_die]`). Step 2A triggers `demote_dice=1`. | `choose_dice_to_glitch` selects the White Contractor die first. `demote_player_dice_step2a` removes it from `in_production_dice` and `contractor_dice`, increments `contractor_supply += 1`, and `player.glitched_dice` remains empty (`[]`)! |
| **TEST-V330-07** | `INV-STEP2A-CONTRACTOR-SACRIFICE-01` | **Step 2B Green Malware White Contractor Sacrifice Cleanup:** Player has 1 White Contractor die deployed in `in_production_dice` (and listed in `contractor_dice`). Player takes `1` unblocked Green Malware hit in Step 2B. | Whether sacrificed via `choose_malware_sacrifice` or via `in_production_dice` fallback, the White die is removed from **both** `contractor_dice` and `in_production_dice`, `contractor_supply` increases by exactly `1` (no double-return at end of Phase 2), and `glitched_dice` contains `0` White dice. |
| **TEST-V330-08** | `INV-SINGULARITY-IMMEDIATE-01` | **v3.0 Space 6 Definitions (`STANDARD` & `AGGRESSIVE`):** Inspect `ZERO_DAY_OVERRIDE` and `CORRUPTED_KERNEL` Space 6 across both profiles in `sim/entities.py` and `pnp/generate_pnp.py`. | `ZERO_DAY_OVERRIDE` Space 6 has `label == "Singularity"`, `add_cubes == {}`, `is_singularity == True`. `CORRUPTED_KERNEL` Space 6 has `label == "Singularity: Lose 1 Secret"`, `lose_secrets == 1`, `add_cubes == {}`, `is_singularity == True`. |
| **TEST-V330-09** | `INV-SINGULARITY-IMMEDIATE-01` | **Immediate Game End on Zero-Day Override Space 6 (Skips Step 2B & Phase 3):** `v3.0` *Zero-Day Override* is at `corruption_track = 5`. Tower drops `1` Black cube and `5` Blue cubes (unblocked). Player has `2` Secrets and uncollected `$3` Income in `in_production_dice`. Run `engine.run_round()`. | Step 2A covers Space 6 and triggers Singularity. Step 2B is **skipped** (player loses `0` Secrets from the 5 Blue cubes!), Phase 3 is **skipped** (player collects `$0` from Phase 3A), `in_production_dice` return to `ready_for_release_dice`, `game_over == True`, `is_final_round == False`, and `end_reason == EndGameReason.SINGULARITY`. |
| **TEST-V330-10** | `INV-SINGULARITY-IMMEDIATE-01` | **Corrupted Kernel Space 6 `Lose 1 Secret` Elimination & Metadata:** Player 0 has `1` Secret, Player 1 has `3` Secrets. `v3.0` *Corrupted Kernel* is at `corruption_track = 5`. Tower drops `1` Black cube. | Space 6 deducts `1` Secret from all players. Player 0 drops to `0` Secrets (`is_patient_zero == True`, `elimination_round == current_round`, `elimination_reason == "Total Breach (<= 0 Secrets)"`, `breach_depth == 0`). Game ends immediately (`end_reason == EndGameReason.SINGULARITY`), and Player 1 wins in `evaluate_end_game()`. |
| **TEST-V330-11** | `INV-SINGULARITY-IMMEDIATE-01` | **Simultaneous Wipeout on Corrupted Kernel Space 6:** Both Player 0 and Player 1 have `1` Secret (`breach_depth` tested with `1` vs `0` Secrets). `v3.0` *Corrupted Kernel* Space 6 triggers `Lose 1 Secret`. | Both players drop to `<= 0` Secrets (`all_patient_zero == True`). Game ends immediately in Step 2A with `game_over == True`, `end_reason == EndGameReason.TOTAL_WIPEOUT`, and `evaluate_end_game()` ranks by Net Wipeout Score (`-breach_depth`). |
| **TEST-V330-12** | `INV-SINGULARITY-IMMEDIATE-01` | **Tiebreaker #2 (`ready_colored_dice_count`) Accuracy on Singularity & Wipeout:** Two surviving players tie on Secrets and Money when Singularity ends the game in Step 2A; Player 0 had 3 Colored Dice deployed in `in_production_dice`, Player 1 had 1 Colored Die. | Surviving `in_production_dice` return to `ready_for_release_dice` on Singularity, and `evaluate_end_game()` records `ready_colored_dice_count == 3` for Player 0 vs `1` for Player 1, awarding Player 0 the Tiebreaker #2 victory! |
| **TEST-V330-13** | `INV-SINGULARITY-IMMEDIATE-01` | **Web Controller Immediate Singularity Transition (`compile_drop`):** In `GameController`, set `v3.0` at `corruption_track = 5` and call `compile_drop()` with `1` exited Black cube. | `compile_drop()` transitions immediately to `controller.phase == 4`, `controller.subphase == "game_over"`, populates `controller.final_result` with `end_reason == "singularity"`, does **not** award Phase 3A income to bots, and logs `"SINGULARITY REACHED! Project: SETEC completed v3.0 compilation. Game Over!"`. |

---

## 6. Implementation Roadmap & Senior Engineer Checklist

1. [ ] **Entity Definitions (`sim/entities.py`):**
   - Remove `add_cubes` from `ZERO_DAY_OVERRIDE` Space 6 and `CORRUPTED_KERNEL` Space 6 in both `AGGRESSIVE` and `STANDARD` profiles.
   - Update Space 6 labels to `"Singularity"` and `"Singularity: Lose 1 Secret"`.
2. [ ] **Bot Valuation & Glitch Heuristics (`sim/bots/base.py`):**
   - Update `choose_dice_to_glitch` to prioritize sacrificing `DieColor.WHITE` ahead of permanent dice within the same tactical tier.
   - Implement `choose_colored_dice_to_return(self, player, count, threat_strengths)` with the 7-tier mathematical valuation hierarchy.
3. [ ] **Phase 2 Threat & Step 2A/2B Resolution (`sim/engine/phase2_threat.py`):**
   - Update `demote_player_dice_step2a` to accept `engine`, enforce White Contractor Sacrifice (`contractor_supply += 1`, never append `DieColor.WHITE` to `glitched_dice`), and reset transient die attributes.
   - Update `return_player_colored_dice_step2a` to call `player.bot.choose_colored_dice_to_return`, validate owned Colored Dice, remove from zone, pop commitment, reset transient attributes, and return Market colors to `engine.state.market`.
   - Update `resolve_corruption_space` to pass `engine` and `threat_strengths`, and populate full Patient Zero metadata (`elimination_round`, `elimination_reason`, `breach_depth`) when `lose_secrets` reduces `player.secrets <= 0`.
   - Update `execute_phase_2` so `engine.state.singularity_triggered` ends the game **immediately** at the end of Step 2A (skipping Step 2B and Phase 3, expiring White Contractors, returning surviving `in_production_dice` to `ready_for_release_dice`, and setting `game_over = True`, `is_final_round = False`).
   - Update `resolve_player_defense_and_wear` Step 2B Green Malware loop to cleanly remove sacrificed White Contractor dice from *both* `contractor_dice` and `in_production_dice`.
4. [ ] **End Game Scoring (`sim/engine/end_game.py`):**
   - Update `ready_dice_count` and `ready_colored_dice_count` in `evaluate_end_game` to count across `online_dice` (`ready_for_release_dice + in_production_dice`).
5. [ ] **Web Controller & Frontend (`web/`):**
   - Update `web/controller/phase2_actions.py` (`compile_drop`) to skip bot Phase 3A income when `game_over` is `True`, and log the Singularity game-over message when `end_reason == EndGameReason.SINGULARITY`.
   - Update `web/controller/phase3_actions.py` Green Malware fallback to ensure White Contractor dice never enter `glitched_dice`.
   - Update `web/static/js/components/header.js` Singularity alert text.
6. [ ] **Rules & Print-and-Play (`RULES.md` & `pnp/generate_pnp.py`):**
   - Synchronize `RULES.md` (Section 4 Step 2A, Step 2C, Section 6C tables, and Section 7 Glossary) and `pnp/generate_pnp.py` (*Corrupted Kernel* Space 6 label).
7. [ ] **Test Suite Updates & Verification (`tests/`):**
   - Update the 4 legacy Singularity final-round tests (`tests/test_engine_phases.py`, `tests/test_v150_corruption_tracks.py`, `tests/test_v290_rules_streamlining.py`, `tests/version_baselines/test_v03_rules.py`).
   - Author all 13 tests in `tests/test_v330_step2a_and_singularity.py` and run the full test suite via WSL (`pytest`).
