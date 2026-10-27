"""Bot archetypes and AI decision heuristics for Rogue Agent simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor

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
    use_b2_secret: bool = False  # Pay $2 for +1 Secret
    use_y1_secret: bool = False  # Pay $2 for +1 Secret
    p1_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P1
    p3_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P3


def choose_backlash_die_index(ready_dice: List[Die]) -> int:
    """Selects the best die to demote for Technical Debt Backlash (lowest VP, Gray preferred)."""
    if not ready_dice:
        return 0
    best_idx = 0
    best_score = (ready_dice[0].vp, 0 if ready_dice[0].color == DieColor.GRAY else 1)
    for idx, d in enumerate(ready_dice):
        score = (d.vp, 0 if d.color == DieColor.GRAY else 1)
        if score < best_score:
            best_score = score
            best_idx = idx
    return best_idx


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
        """Returns indices of locked dice to unlock by spending 1 🔧 token each."""
        return []

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
        2. Prioritize B3 (Air-Gapped Backup) next (absorbs damage without wearing down).
        3. Lowest VP die next (preserves valuable dice in Ready zone).
        4. Lowest cost die next.
        """
        def wear_priority_key(d: Die) -> Tuple[int, int, int, int]:
            is_white = 0 if d.color == DieColor.WHITE else 1
            face = d.effective_face or d.current_face
            is_b3 = 0 if (face and face.star_code == "B3") else 1
            return (is_white, is_b3, d.vp, d.cost)

        return sorted(assigned_dice, key=wear_priority_key)

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        """Returns the actions to execute during Phase 3: Corporate Operations."""
        return Phase3ActionPlan()


class AdaptiveBalancedBot(BaseBot):
    """Balanced bot: monitors threat levels, hedges shields, patches worn dice, and buys counters."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="AdaptiveBalancedBot")

    def _get_threat_levels(
        self, staging_cubes: Dict[CubeColor, int], stuck_cubes: Dict[CubeColor, int]
    ) -> Dict[CubeColor, int]:
        return {
            color: staging_cubes.get(color, 0) + stuck_cubes.get(color, 0)
            for color in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN]
        }

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply <= 0 or player_state.money < 4:
            return 0
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        total_threat = sum(threats.values())
        if total_threat >= 8 and player_state.money >= 9:
            return min(3, contractor_supply)
        elif total_threat >= 6 and player_state.money >= 6:
            return min(2, contractor_supply)
        elif total_threat >= 3 and player_state.money >= 4:
            return min(1, contractor_supply)
        return 0

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        if player_state.patches <= 0:
            return []
        unlocks: List[int] = []
        for idx, die in enumerate(active_dice):
            if len(unlocks) >= player_state.patches:
                break
            if die.is_locked:
                unlocks.append(idx)
        return unlocks

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
        if rerolls_remaining <= 0:
            return []
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        red_shields = sum(
            d.current_face.block_amount
            for d in active_dice
            if d.current_face and d.current_face.shield_color in (ShieldColor.RED, ShieldColor.ANY)
        )
        blue_shields = sum(
            (1 if (d.current_face and d.current_face.has_shield_option) else d.current_face.block_amount)
            for d in active_dice
            if d.current_face and (
                d.current_face.shield_color in (ShieldColor.BLUE, ShieldColor.ANY)
                or d.current_face.has_shield_option
            )
        )
        green_shields = sum(
            d.current_face.block_amount
            for d in active_dice
            if d.current_face and d.current_face.shield_color in (ShieldColor.GREEN, ShieldColor.ANY)
        )

        rerolls: List[int] = []
        for idx, die in enumerate(active_dice):
            if die.is_locked:
                continue
            face = die.current_face
            if not face:
                continue
            if face.is_glitch:
                rerolls.append(idx)
            elif not face.is_shield and not face.has_shield_option and (
                threats[CubeColor.BLUE] > blue_shields
                or threats[CubeColor.RED] > red_shields
                or threats[CubeColor.GREEN] > green_shields
            ):
                rerolls.append(idx)
            elif not face.is_shield and not face.has_shield_option and not face.has_cash_option and face.money <= 1 and face.patches == 0:
                rerolls.append(idx)
        return rerolls

    def choose_hotfix_rerolls(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> List[int]:
        rerolls: List[int] = []
        available_patches = player_state.patches
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)

        # Count current shields rolled
        red_shields = sum(
            d.current_face.block_amount
            for d in rolled_dice
            if d.current_face and d.current_face.shield_color in (ShieldColor.RED, ShieldColor.ANY)
        )
        blue_shields = sum(
            (1 if (d.current_face and d.current_face.has_shield_option) else d.current_face.block_amount)
            for d in rolled_dice
            if d.current_face and (
                d.current_face.shield_color in (ShieldColor.BLUE, ShieldColor.ANY)
                or d.current_face.has_shield_option
            )
        )

        # Reroll non-shield faces if we lack defense and have patches
        for idx, die in enumerate(rolled_dice):
            if available_patches <= len(rerolls):
                break
            face = die.current_face
            if not face:
                continue
            if face.name == "Idle (0)":
                rerolls.append(idx)
            elif (
                not face.is_shield
                and not face.has_shield_option
                and (threats[CubeColor.RED] > red_shields or threats[CubeColor.BLUE] > blue_shields)
            ):
                rerolls.append(idx)

        return rerolls

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
        dice = active_dice if active_dice is not None else (rolled_dice or [])
        threats = self._get_threat_levels(staging_cubes or {}, stuck_cubes or {})
        declarations: Dict[int, int] = {}
        for idx, die in enumerate(dice):
            face = die.current_face
            if not face or not face.is_choice:
                continue
            if face.has_shield_option:
                declarations[idx] = 0 if threats[CubeColor.BLUE] > 0 else 1
            elif face.name == "+$1 / +1 🔧":
                need_patch = (player_state.patches < 2) or (len(player_state.unpatched_dice) > player_state.patches)
                declarations[idx] = 1 if need_patch else 0
            elif face.name == "+1 🔧 / +$1":
                need_patch = (player_state.patches < 2) or (len(player_state.unpatched_dice) > player_state.patches)
                declarations[idx] = 0 if need_patch else 1
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
        threats = self._get_threat_levels(staging_cubes, stuck_cubes)
        assignments: Dict[int, ShieldColor] = {}

        # First commit fixed colored shields
        committed_red = 0
        committed_blue = 0
        committed_green = 0

        any_shield_indices: List[int] = []
        blue_choice_indices: List[int] = []

        for idx, die in enumerate(rolled_dice):
            face = die.current_face
            if not face or face.is_glitch:
                continue

            if face.is_shield:
                if face.shield_color == ShieldColor.RED:
                    assignments[idx] = ShieldColor.RED
                    committed_red += face.block_amount
                elif face.shield_color == ShieldColor.BLUE:
                    assignments[idx] = ShieldColor.BLUE
                    committed_blue += face.block_amount
                elif face.shield_color == ShieldColor.GREEN:
                    assignments[idx] = ShieldColor.GREEN
                    committed_green += face.block_amount
                elif face.shield_color == ShieldColor.ANY:
                    any_shield_indices.append(idx)
            elif face.has_shield_option:
                blue_choice_indices.append(idx)

        # Assign Blue choice faces if Blue threat > committed_blue
        for idx in blue_choice_indices:
            if threats[CubeColor.BLUE] > committed_blue:
                assignments[idx] = ShieldColor.BLUE
                committed_blue += 1

        # Assign Generic Any shields prioritizing Blue (protect Secrets) first, then Red, then Green
        for idx in any_shield_indices:
            if threats[CubeColor.BLUE] > committed_blue:
                best_color = ShieldColor.BLUE
            elif threats[CubeColor.RED] > committed_red:
                best_color = ShieldColor.RED
            elif threats[CubeColor.GREEN] > committed_green:
                best_color = ShieldColor.GREEN
            else:
                best_color = ShieldColor.BLUE

            assignments[idx] = best_color
            if best_color == ShieldColor.BLUE:
                committed_blue += 1
            elif best_color == ShieldColor.RED:
                committed_red += 1
            else:
                committed_green += 1

        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        current_patches = player_state.patches
        threats = self._get_threat_levels(game_state.staging_cup, game_state.tower.stuck_cubes)
        total_threat = sum(threats.values())
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        # 1. Dirty Income: take dirty income if broke, has ready dice, secrets > 1, and threat is manageable
        if (
            current_money < 3
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
            and total_threat <= 6
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        # 2. Patching: patch worn dice using tokens first, then cash if preserving cushion
        patch_cash_cost = (
            3
            if game_state.active_directive_code == "POLYMORPHIC_WORM"
            else game_state.config.patch_cash_cost
        )

        for idx in range(len(player_state.unpatched_dice)):
            if current_patches > 0:
                plan.patch_actions.append({"die_index": idx, "use_cash": False})
                current_patches -= 1
            elif current_money - patch_cash_cost >= cash_cushion:
                plan.patch_actions.append({"die_index": idx, "use_cash": True})
                current_money -= patch_cash_cost

        # 3. Market Purchases: buy counter dice matching high threats (respecting cushion)
        purchases = 0
        preferred_colors = [DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]
        if threats[CubeColor.RED] > threats[CubeColor.BLUE]:
            preferred_colors = [DieColor.RED, DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW]

        for color in preferred_colors:
            if purchases >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost
                purchases += 1

        # 4. In Final Round: spend remaining cash on any available market dice
        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.YELLOW, DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.PURPLE]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        return plan


class SecOpsTurtleBot(BaseBot):
    """Paranoid defensive turtle: focuses on shields, heavy patching, and avoiding Dirty Income."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="SecOpsTurtleBot")

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply <= 0 or player_state.money < 3:
            return 0
        threat = sum(staging_cubes.get(c, 0) + stuck_cubes.get(c, 0) for c in [CubeColor.RED, CubeColor.BLUE, CubeColor.GREEN])
        if threat >= 6 and player_state.money >= 8:
            return min(3, contractor_supply)
        elif threat >= 3 and player_state.money >= 5:
            return min(2, contractor_supply)
        elif player_state.money >= 3:
            return min(1, contractor_supply)
        return 0

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        if player_state.patches <= 0:
            return []
        unlocks: List[int] = []
        for idx, die in enumerate(active_dice):
            if len(unlocks) >= player_state.patches:
                break
            if die.is_locked:
                unlocks.append(idx)
        return unlocks

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
        if rerolls_remaining <= 0:
            return []
        rerolls: List[int] = []
        for idx, die in enumerate(active_dice):
            if die.is_locked:
                continue
            face = die.current_face
            if face and (face.is_glitch or (not face.is_shield and not face.has_shield_option)):
                rerolls.append(idx)
        return rerolls

    def choose_hotfix_rerolls(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> List[int]:
        rerolls: List[int] = []
        available_patches = player_state.patches
        for idx, die in enumerate(rolled_dice):
            if available_patches <= len(rerolls):
                break
            face = die.current_face
            if face and not face.is_shield and not face.has_shield_option:
                rerolls.append(idx)
        return rerolls

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
                declarations[idx] = 1 if player_state.patches < 3 else 0
            elif face.name == "+1 🔧 / +$1":
                declarations[idx] = 0 if player_state.patches < 3 else 1
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
                    assignments[idx] = ShieldColor.BLUE
                else:
                    assignments[idx] = face.shield_color
            elif face.has_shield_option and blue_threat > 0:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        current_patches = player_state.patches
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        patch_cash_cost = (
            3
            if game_state.active_directive_code == "POLYMORPHIC_WORM"
            else game_state.config.patch_cash_cost
        )

        for idx in range(len(player_state.unpatched_dice)):
            if current_patches > 0:
                plan.patch_actions.append({"die_index": idx, "use_cash": False})
                current_patches -= 1
            elif current_money - patch_cash_cost >= cash_cushion:
                plan.patch_actions.append({"die_index": idx, "use_cash": True})
                current_money -= patch_cash_cost

        for color in [DieColor.BLUE, DieColor.GREEN, DieColor.RED]:
            if len(plan.market_purchases) >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color in (DieColor.RED, DieColor.GREEN) else 5
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost

        if is_final_round and len(plan.market_purchases) < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.BLUE, DieColor.GREEN, DieColor.RED, DieColor.YELLOW, DieColor.PURPLE]:
                if len(plan.market_purchases) >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost

        if (
            current_money == 0
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)

        return plan


class VentureGreedBot(BaseBot):
    """Greedy capitalist: maximizes Yellow dice, buys secrets, and minimizes shielding."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="VentureGreedBot")

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply <= 0 or player_state.money < 6:
            return 0
        if player_state.money >= 11:
            return min(3, contractor_supply)
        elif player_state.money >= 8:
            return min(2, contractor_supply)
        return min(1, contractor_supply)

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        if player_state.patches <= 0:
            return []
        unlocks: List[int] = []
        for idx, die in enumerate(active_dice):
            if len(unlocks) >= player_state.patches:
                break
            if die.is_locked and die.current_face and die.current_face.is_glitch:
                unlocks.append(idx)
        return unlocks

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
        if rerolls_remaining <= 0:
            return []
        rerolls: List[int] = []
        for idx, die in enumerate(active_dice):
            if die.is_locked:
                continue
            face = die.current_face
            if not face:
                continue
            if face.is_glitch or (face.money == 0 and not face.is_star and not face.has_cash_option):
                rerolls.append(idx)
        return rerolls

    def choose_hotfix_rerolls(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> List[int]:
        rerolls: List[int] = []
        available_patches = player_state.patches
        if player_state.secrets > 2 and player_state.money > 2:
            for idx, die in enumerate(rolled_dice):
                if available_patches <= len(rerolls):
                    break
                face = die.current_face
                if face and (face.is_shield or face.name == "Idle (0)"):
                    rerolls.append(idx)
        return rerolls

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
                declarations[idx] = 0 if (blue_threat > 0 and player_state.secrets <= 2) else 1
            elif face.name == "+$1 / +1 🔧":
                need_patch = (player_state.patches == 0 and len(player_state.unpatched_dice) > 0)
                declarations[idx] = 1 if need_patch else 0
            elif face.name == "+1 🔧 / +$1":
                need_patch = (player_state.patches == 0 and len(player_state.unpatched_dice) > 0)
                declarations[idx] = 0 if need_patch else 1
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
                    assignments[idx] = ShieldColor.BLUE
                else:
                    assignments[idx] = face.shield_color
            elif face.has_shield_option and blue_threat > 0 and player_state.secrets <= 2:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        if (
            current_money < 5
            and player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        if player_state.b2_available and (current_money - 2 >= cash_cushion) and player_state.secrets < 10:
            plan.use_b2_secret = True
            current_money -= 2

        if player_state.y1_available and (current_money - 6 >= cash_cushion) and player_state.secrets < 10:
            plan.use_y1_secret = True
            current_money -= 6

        purchases = 0
        for _ in range(game_state.config.max_market_purchases_per_turn):
            if game_state.market.get(DieColor.YELLOW, 0) > 0 and (current_money - 5 >= cash_cushion):
                plan.market_purchases.append(DieColor.YELLOW)
                current_money -= 5
                purchases += 1
            elif game_state.market.get(DieColor.BLUE, 0) > 0 and (current_money - 5 >= cash_cushion):
                plan.market_purchases.append(DieColor.BLUE)
                current_money -= 5
                purchases += 1

        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.YELLOW, DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.PURPLE]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.RED, DieColor.GREEN, DieColor.PURPLE) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        if len(player_state.ready_dice) <= 2:
            patch_cash_cost = (
                3
                if game_state.active_directive_code == "POLYMORPHIC_WORM"
                else game_state.config.patch_cash_cost
            )
            current_patches = player_state.patches
            for idx in range(len(player_state.unpatched_dice)):
                if current_patches > 0:
                    plan.patch_actions.append({"die_index": idx, "use_cash": False})
                    current_patches -= 1
                elif current_money - patch_cash_cost >= cash_cushion:
                    plan.patch_actions.append({"die_index": idx, "use_cash": True})
                    current_money -= patch_cash_cost

        return plan


class AccelerationistBot(BaseBot):
    """Rushes corruption and Singularity by weaponizing the Cube Tower and taking Dirty Income."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="AccelerationistBot")

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply > 0 and player_state.money >= 5 and player_state.secrets <= 3:
            return 1
        return 0

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        if player_state.patches <= 0:
            return []
        unlocks: List[int] = []
        for idx, die in enumerate(active_dice):
            if len(unlocks) >= player_state.patches:
                break
            if die.is_locked and die.current_face and die.current_face.is_glitch:
                unlocks.append(idx)
        return unlocks

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
        if rerolls_remaining <= 0:
            return []
        rerolls: List[int] = []
        for idx, die in enumerate(active_dice):
            if die.is_locked:
                continue
            face = die.current_face
            if face and (face.is_glitch or (face.money == 0 and not face.is_star and not face.is_shield and not face.has_cash_option and not face.has_shield_option)):
                rerolls.append(idx)
        return rerolls

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
                need_patch = (len(player_state.unpatched_dice) >= 2 or player_state.patches == 0)
                declarations[idx] = 1 if need_patch else 0
            elif face.name == "+1 🔧 / +$1":
                need_patch = (len(player_state.unpatched_dice) >= 2 or player_state.patches == 0)
                declarations[idx] = 0 if need_patch else 1
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
                    assignments[idx] = ShieldColor.BLUE
                else:
                    assignments[idx] = face.shield_color
            elif face.has_shield_option and blue_threat > 0:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        if (
            player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        if player_state.p1_available:
            plan.p1_cube_choice = CubeColor.RED
        if player_state.p3_available is not None:
            plan.p3_cube_choice = CubeColor(player_state.p3_available.value)

        purchases = 0
        for color in [DieColor.PURPLE, DieColor.BLUE]:
            if purchases >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4 if color == DieColor.PURPLE else 5
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost
                purchases += 1

        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.PURPLE, DieColor.BLUE, DieColor.RED, DieColor.GREEN, DieColor.YELLOW]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.PURPLE, DieColor.RED, DieColor.GREEN) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        current_patches = player_state.patches
        for idx in range(len(player_state.unpatched_dice)):
            if current_patches > 0:
                plan.patch_actions.append({"die_index": idx, "use_cash": False})
                current_patches -= 1

        return plan


class RecklessSaboteurBot(BaseBot):
    """Chaos bot: forces extreme threat escalations and pushes for simultaneous total wipeout."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id, name="RecklessSaboteurBot")

    def choose_contractor_hires(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
    ) -> int:
        if contractor_supply <= 0 or player_state.money < 3:
            return 0
        if player_state.money >= 8:
            return min(3, contractor_supply)
        elif player_state.money >= 5:
            return min(2, contractor_supply)
        elif player_state.money >= 3:
            return min(1, contractor_supply)
        return 0

    def choose_debug_unlocks(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> List[int]:
        if player_state.patches <= 0:
            return []
        unlocks: List[int] = []
        for idx, die in enumerate(active_dice):
            if len(unlocks) >= player_state.patches:
                break
            if die.is_locked:
                unlocks.append(idx)
        return unlocks

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
        if rerolls_remaining <= 0:
            return []
        rerolls: List[int] = []
        for idx, die in enumerate(active_dice):
            if die.is_locked:
                continue
            face = die.current_face
            if face and (face.is_glitch or (face.money < 1 and not face.has_cash_option and not face.is_shield and not face.has_shield_option)):
                rerolls.append(idx)
        return rerolls

    def commit_shields(
        self,
        player_state: PlayerState,
        rolled_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> Dict[int, ShieldColor]:
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
                    assignments[idx] = ShieldColor.BLUE
                else:
                    assignments[idx] = face.shield_color
            elif face.has_shield_option and blue_threat > 0:
                assignments[idx] = ShieldColor.BLUE
        return assignments

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        plan = Phase3ActionPlan()
        current_money = player_state.money
        is_final_round = getattr(game_state, "is_final_round", False)
        cash_cushion = 0 if is_final_round else 2

        if (
            player_state.secrets > game_state.config.dirty_income_secret_cost
            and len(player_state.ready_dice) >= 1
        ):
            plan.take_dirty_income = True
            plan.dirty_income_backlash_die_index = choose_backlash_die_index(player_state.ready_dice)
            current_money += game_state.config.dirty_income_cash

        purchases = 0
        for color in [DieColor.PURPLE, DieColor.RED]:
            if purchases >= game_state.config.max_market_purchases_per_turn:
                break
            cost = 4
            if game_state.market.get(color, 0) > 0 and (current_money - cost >= cash_cushion):
                plan.market_purchases.append(color)
                current_money -= cost
                purchases += 1

        if is_final_round and purchases < game_state.config.max_market_purchases_per_turn:
            for color in [DieColor.PURPLE, DieColor.RED, DieColor.GREEN, DieColor.BLUE, DieColor.YELLOW]:
                if purchases >= game_state.config.max_market_purchases_per_turn:
                    break
                cost = 4 if color in (DieColor.PURPLE, DieColor.RED, DieColor.GREEN) else 5
                if game_state.market.get(color, 0) > 0 and current_money >= cost:
                    plan.market_purchases.append(color)
                    current_money -= cost
                    purchases += 1

        patch_cash_cost = (
            3
            if game_state.active_directive_code == "POLYMORPHIC_WORM"
            else game_state.config.patch_cash_cost
        )
        if len(player_state.ready_dice) == 0 and len(player_state.unpatched_dice) > 0:
            if player_state.patches > 0:
                plan.patch_actions.append({"die_index": 0, "use_cash": False})
            elif current_money - patch_cash_cost >= cash_cushion:
                plan.patch_actions.append({"die_index": 0, "use_cash": True})

        return plan
