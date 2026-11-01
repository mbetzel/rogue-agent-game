"""Bot archetypes and AI decision heuristics for Rogue Agent simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.entities import Die, Face


@dataclass
class Phase3ActionPlan:
    """Operations plan chosen by a bot during Phase 3."""

    take_dirty_income: bool = False
    dirty_income_cube_choice: CubeColor = CubeColor.RED
    dirty_income_backlash_die_index: int = 0  # Index in ready_dice to demote on backlash
    # Each entry in patch_actions is a dict: {"die_index": int, "use_cash": bool}
    patch_actions: List[Dict[str, int | bool]] = field(default_factory=list)
    # Market purchases: list of die colors to buy (up to 2)
    market_purchases: List[DieColor] = field(default_factory=list)
    # Special star actions
    use_b2_secret: bool = False  # Pay $4 for +1 Secret
    use_y1_secret: bool = False  # Pay $2 for +1 Secret
    p1_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P1
    p3_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P3
    # Archetype Phase 3 actions
    use_phreaker_ability: bool = False
    use_cipher_ability: bool = False
    cipher_mode: Optional[str] = None  # "BUY_FREE_DIE" or "DIRTY_INCOME"
    cipher_free_die_color: Optional[DieColor] = None
    # Phase 3 Part 3B Fast-patching (v0.22.0)
    fast_patch_indices: List[int] = field(default_factory=list)


def choose_backlash_die_index(ready_dice: List[Die]) -> int:
    """Selects the best die to demote for Technical Debt Backlash (Gray starter dice first, then lowest cost)."""
    if not ready_dice:
        return 0
    best_idx = 0
    best_score = (0 if ready_dice[0].color == DieColor.GRAY else 1, ready_dice[0].cost)
    for idx, d in enumerate(ready_dice):
        score = (0 if d.color == DieColor.GRAY else 1, d.cost)
        if score < best_score:
            best_score = score
            best_idx = idx
    return best_idx


def plan_final_round_repairs(
    player_state: PlayerState,
    game_state: GameState,
    current_money: int,
    current_patches: int,
    patch_cash_cost: int,
    plan: Phase3ActionPlan,
) -> Tuple[int, int]:
    """Plans repairs for the final round using patch tokens only (preserving cash for Tiebreaker #1).

    Prioritizes colored dice first (Tiebreaker #2 Ready Colored Dice), then gray dice (Tiebreaker #4).
    """
    sim_unpatched = list(player_state.unpatched_dice)
    if plan.use_phreaker_ability:
        for _ in range(min(1, len(sim_unpatched))):
            sim_unpatched.pop(0)

    while current_patches > 0 and sim_unpatched:
        colored_indices = [
            idx for idx, d in enumerate(sim_unpatched) if d.color != DieColor.GRAY
        ]
        if colored_indices:
            target_idx = colored_indices[0]
        else:
            target_idx = 0

        plan.patch_actions.append({"die_index": target_idx, "use_cash": False})
        current_patches -= 1
        sim_unpatched.pop(target_idx)

    return current_money, current_patches


class BaseBot:
    """Abstract base class for Rogue Agent bot archetypes."""

    def __init__(self, bot_id: int, name: str = "BaseBot") -> None:
        self.bot_id = bot_id
        self.name = name

    def choose_hotfix_rerolls(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> List[int]:
        """Returns the indices of rolled dice to reroll using available patch tokens (legacy v0.5)."""
        return []

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        """Returns the number of contractor dice to hire (0 to 3) in Phase 1 Step 2."""
        return 0

    def choose_yahtzee_rerolls(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        rerolls_remaining: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        """Returns indices of active_dice to reroll (must be unlocked)."""
        return []

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        """DEPRECATED in v0.23.0. Phase 1 debug unlocks have been removed.

        Always returns an empty list. All wrench spending decisions are consolidated
        into choose_fast_patches() in Phase 3 Part 3B.
        """
        return []

    def choose_glitch_demotion(
        self,
        player_state: PlayerState,
        glitch_die: Optional[Die] = None,
        active_dice: Optional[List[Die]] = None,
        validated_commitments: Optional[Dict[int, ShieldColor]] = None,
        rng: Optional[random.Random] = None,
    ) -> Optional[Die]:
        """Chooses a die to sacrifice/demote for Glitch Backlash Routine.

        Default heuristic per RULES.md (v0.19.0):
        1. Sacrifice a White contractor die first (if available in player_state.contractor_dice).
        2. Else demote lowest cost uncommitted die in player_state.ready_dice, Gray first.
        """
        if player_state.contractor_dice:
            return player_state.contractor_dice[0]

        if not player_state.ready_dice:
            return None

        commitments = validated_commitments or {}
        dice_pool = active_dice or player_state.ready_dice

        def get_demotion_key(d: Die) -> Tuple[int, int, int]:
            is_committed = 0
            if d in dice_pool:
                try:
                    idx = dice_pool.index(d)
                    if idx in commitments:
                        is_committed = 1
                except ValueError:
                    pass
            is_gray = 0 if d.color == DieColor.GRAY else 1
            return (is_committed, is_gray, getattr(d, "cost", 0))

        return min(player_state.ready_dice, key=get_demotion_key)

    def choose_operator_ability(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        """Returns True if the bot activates The Operator's Redundant Crew ability."""
        return False

    def choose_operator_buy_third_die(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        """Returns True if the bot purchases a 3rd contractor die for progressive cost ($3) after using Redundant Crew."""
        return False

    def choose_prodigy_ability(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        rerolls_remaining: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        """Returns True if the bot activates The Prodigy's Brute-Force Bypass ability."""
        return False

    def choose_prodigy_face_override(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> Optional[Tuple[int, Face]]:
        """Returns (die_index, target_face) to turn 1 rolled die to any legal non-Star face, or None."""
        if not active_dice:
            return None
        candidates = [
            (idx, d) for idx, d in enumerate(active_dice)
            if d.is_locked or (d.current_face and d.current_face.is_glitch)
        ]
        if not candidates:
            candidates = list(enumerate(active_dice))
        if not candidates:
            return None

        best_choice = None
        best_score = -1
        for idx, d in candidates:
            valid_faces = [f for f in d.faces if not f.is_star and not f.is_glitch]
            for f in valid_faces:
                score = f.block_amount * 3 + f.money * 2 + f.patches * 2
                if score > best_score:
                    best_score = score
                    best_choice = (idx, f)
        return best_choice

    def choose_acoustic_ability(
        self,
        player_state: PlayerState,
        qualifying_colors: List[CubeColor],
        exited_cubes: Dict[CubeColor, int],
        active_version_str: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> Optional[CubeColor]:
        """Returns the CubeColor of an exited cube to permanently remove via Baffle Echo, or None."""
        if not qualifying_colors:
            return None
        if CubeColor.BLUE in qualifying_colors:
            return CubeColor.BLUE
        if CubeColor.RED in qualifying_colors:
            return CubeColor.RED
        return qualifying_colors[0]

    def choose_spook_ability(
        self,
        player_state: PlayerState,
        secrets_at_risk: int,
        active_version_str: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> int:
        """Returns the number of dollars to pay from supply to prevent Corporate Secret loss via Slush Fund."""
        return 0

    def choose_malware_sacrifice(
        self,
        player_state: PlayerState,
        unblocked_green: int,
        rng: random.Random,
    ) -> bool:
        """Returns True if the player chooses to sacrifice an active White contractor die to absorb Green malware."""
        return len(player_state.contractor_dice) > 0

    def declare_choices(
        self,
        player_state: PlayerState,
        active_dice: Optional[List[Die]] = None,
        staging_cubes: Optional[Dict[CubeColor, int]] = None,
        stuck_cubes: Optional[Dict[CubeColor, int]] = None,
        directive_code: str = "",
        rng: Optional[random.Random] = None,
        rolled_dice: Optional[List[Die]] = None,
    ) -> Dict[int, int]:
        """Maps die indices with choice faces to chosen option index (0 or 1).

        Default heuristics:
        - Gray Face 5 (+$1 / +1 🔧): if patches < 2, choose 1 (+1 🔧), else choose 0 (+$1).
        - Green Face 4 (+1 🔧 / +$1): if patches < 2, choose 0 (+1 🔧), else choose 1 (+$1).
        - Blue Face 4 (Block 1 Blue / +1 🔧): if Blue threat > 0, choose 0 (Block 1 Blue), else choose 1 (+1 🔧).
        """
        dice = active_dice if active_dice is not None else (rolled_dice or [])
        staging = staging_cubes or {}
        stuck = stuck_cubes or {}
        blue_threat = staging.get(CubeColor.BLUE, 0) + stuck.get(CubeColor.BLUE, 0)

        declarations: Dict[int, int] = {}
        for idx, die in enumerate(dice):
            face = die.current_face
            if not face or not face.is_choice:
                continue
            if face.has_shield_option:
                declarations[idx] = 0 if blue_threat > 0 else 1
            elif face.name == "+$1 / +1 🔧":
                declarations[idx] = 1 if player_state.patches < 2 else 0
            elif face.name == "+1 🔧 / +$1":
                declarations[idx] = 0 if player_state.patches < 2 else 1
            else:
                declarations[idx] = 0
        return declarations

    def commit_shields(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> Dict[int, ShieldColor]:
        """Maps die indices in rolled_dice to assigned ShieldColor (RED, BLUE, GREEN).

        Generic (ANY) shields MUST choose a specific color: RED, BLUE, or GREEN.
        Choice faces with shield options (e.g. Blue Face 4) are committed to their shield color if threatened.
        """
        assignments: Dict[int, ShieldColor] = {}
        staging = staging_cubes or {}
        stuck = stuck_cubes or {}
        blue_threat = staging.get(CubeColor.BLUE, 0) + stuck.get(CubeColor.BLUE, 0)

        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if not face or face.is_glitch:
                continue
            if face.is_shield:
                if face.shield_color == ShieldColor.ANY:
                    assignments[idx] = ShieldColor.BLUE  # Prioritize Blue over Red/Green
                else:
                    assignments[idx] = face.shield_color
            elif face.has_shield_option and blue_threat > 0:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def choose_shield_wear_order(
        self,
        player_state: PlayerState,
        color: ShieldColor,
        assigned_dice: List[Die],
        cubes_to_absorb: Optional[int] = None,
    ) -> List[Die]:
        """Returns assigned shield dice ordered by absorption priority.

        Default heuristics:
        1. Prioritize White contractor dice (immune to wear, returns to supply at round end).
        2. Prioritize B3 (Air-Gapped Backup) next if other ready dice are available to be sacrificed.
        3. Lowest VP die next (preserves valuable dice in Ready zone).
        4. Lowest cost die next.
        """
        def wear_priority_key(d: Die) -> Tuple[int, int, int, int]:
            is_white = 0 if d.color == DieColor.WHITE else 1
            face = d.effective_face or d.current_face
            has_other_ready = any(rd.die_id != d.die_id for rd in player_state.ready_dice)
            is_b3 = 0 if (face and face.star_code == "B3" and has_other_ready) else 1
            return (is_white, is_b3, d.vp, d.cost)

        return sorted(assigned_dice, key=wear_priority_key)

    def choose_b3_sacrificial_die(
        self,
        player_state: PlayerState,
        other_ready_dice: List[Die],
    ) -> Die:
        """Picks a sacrificial ready die to move to Unpatched instead of B3 when B3 blocks damage.

        Default heuristic: picks lowest VP die, preferring Gray starter dice.
        """
        def sacrifice_key(d: Die) -> Tuple[int, int, int]:
            is_gray = 0 if d.color == DieColor.GRAY else 1
            return (is_gray, d.vp, d.cost)

        return min(other_ready_dice, key=sacrifice_key)

    def choose_fast_patches(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> List[int]:
        """Returns indices in player_state.glitched_dice to fast-patch to scanned_dice.

        Heuristic Priorities per Section 7.1:
        1. Patch Cap Avoidance: If player_state.patches > 3, ALWAYS spend down to <= 3
           to avoid discarding unspent patches at end-of-round cleanup.
        2. Infrastructure Need: If ready_for_release pool < 4 dice and incoming threat > 5,
           spend patches aggressively.
        3. Die Quality Sorting: Fast-patch colored dice first (higher output/defense value),
           leaving Gray starter dice to shift naturally along the conveyor.
        4. Final Round Valuation: In the final round, fast-patch colored dice into Ready
           to maximize Tiebreaker #2 (Active Colored Module Dice).
        """
        if player_state.patches <= 0 or not player_state.glitched_dice:
            return []

        available_patches = player_state.patches
        glitched = list(player_state.glitched_dice)

        def sort_key(idx: int) -> Tuple[int, int]:
            d = glitched[idx]
            is_colored = 1 if d.color != DieColor.GRAY and d.color != DieColor.WHITE else 0
            return (is_colored, getattr(d, "cost", 0))

        sorted_indices = sorted(range(len(glitched)), key=sort_key, reverse=True)
        chosen: List[int] = []

        # 1. Patch Cap Avoidance: spend down to <= 3
        excess_patches = max(0, available_patches - 3)
        for idx in sorted_indices:
            if len(chosen) < excess_patches and len(chosen) < available_patches:
                chosen.append(idx)

        # 2. Final round or infrastructure need
        is_final_round = getattr(game_state, "is_final_round", False) or getattr(game_state, "singularity_triggered", False)
        threat_level = sum(game_state.staging_cup.values())
        if hasattr(game_state, "tower"):
            threat_level += sum(game_state.tower.get_stuck_copy().values())
        need_infra = len(player_state.ready_for_release_dice) < 4 and threat_level > 5

        if is_final_round or need_infra:
            for idx in sorted_indices:
                if idx not in chosen and len(chosen) < available_patches:
                    chosen.append(idx)

        return chosen

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        """Returns the actions to execute during Phase 3: Corporate Operations."""
        return Phase3ActionPlan()


