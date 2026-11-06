"""Bot archetypes and AI decision heuristics for Rogue Agent simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set, Tuple

from sim.config import CubeColor, DieColor, ShieldColor
from sim.entities import ArchetypeCode, Face

if TYPE_CHECKING:
    from sim.engine import GameState, PlayerState
    from sim.engine.state import ProductionRole
    from sim.entities import Die, Face


@dataclass
class Phase3ActionPlan:
    """Operations plan chosen by a bot (v0.34: Phase 6 Operations; v0.33: Phase 3).

    In the six-phase round, ``spook_burn_die_id``, ``phreaker_diagnostics_die_id`` and
    ``use_omnidyne_override`` are ignored by Phase 6 (they belong to Phases 3 and 5).
    """

    take_dirty_income: bool = False
    dirty_income_cube_choice: CubeColor = CubeColor.RED
    dirty_income_backlash_die_index: int = 0  # Index in ready_dice to demote on backlash
    # Each entry in patch_actions is a dict: {"die_index": int, "use_cash": bool}
    patch_actions: List[Dict[str, int | bool]] = field(default_factory=list)
    # Market purchases: list of die colors to buy (up to 2)
    market_purchases: List[DieColor] = field(default_factory=list)
    buy_purple_reserve: bool = False
    # Special star actions
    use_b2_secret: bool = False  # Pay $4 for +1 Secret
    use_y1_secret: bool = False  # Pay $2 for +1 Secret
    p1_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P1
    p3_cube_choice: Optional[CubeColor] = None  # Add 1 Attack cube via P3
    # Institutional Overrides (Company)
    use_omnidyne_override: bool = False
    use_prometheus_override: bool = False
    prometheus_mode: Optional[str] = None  # "DISCOUNT" / "BUY_FREE_DIE" or "CASH" / "DIRTY_INCOME"
    prometheus_discount_die_color: Optional[DieColor] = None
    # White Hat Face 6 Protocols
    spook_burn_die_id: Optional[int] = None
    phreaker_diagnostics_die_id: Optional[int] = None
    prodigy_override_die_id: Optional[int] = None
    prodigy_override_target_face: Optional[Face] = None
    # Phase 3 Hardware Upgrades & Patents (v0.28.0)
    track_upgrades: List[str] = field(default_factory=list)
    patent_filings: int = 0
    # v0.35.0: {(track, level): BreakthroughChoice}; missing entries ask bot.choose_breakthrough
    breakthrough_choices: Dict[Any, Any] = field(default_factory=dict)
    # Phase 3 Part 3B Fast-patching (v0.22.0)
    fast_patch_indices: List[int] = field(default_factory=list)

    # Legacy Backward Compatibility fields
    use_phreaker_ability: bool = False
    use_cipher_ability: bool = False
    cipher_mode: Optional[str] = None
    cipher_free_die_color: Optional[DieColor] = None

    def __post_init__(self) -> None:
        if self.use_phreaker_ability:
            self.use_omnidyne_override = True
        if self.use_cipher_ability:
            self.use_prometheus_override = True
        if self.cipher_mode is not None and self.prometheus_mode is None:
            self.prometheus_mode = self.cipher_mode
        if self.cipher_free_die_color is not None and self.prometheus_discount_die_color is None:
            self.prometheus_discount_die_color = self.cipher_free_die_color


# v0.34 code alias; the dataclass name is kept for backward compatibility.
OperationsActionPlan = Phase3ActionPlan


def is_six_phase_state(game_state: Any) -> bool:
    """True when the game runs the v0.34 six-phase round (tolerates mock / partial game states)."""
    cfg = getattr(game_state, "config", None)
    return bool(getattr(cfg, "is_six_phase", False)) if cfg is not None else False


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


def purple_purchasable(game_state: Any) -> bool:
    """False under v0.35.0 (Purple dice are gained only from the Patents L3 Breakthrough)."""
    cfg = getattr(game_state, "config", None)
    return True if cfg is None else bool(getattr(cfg, "purple_purchasable", True))


class BaseBot:
    """Abstract base class for Rogue Agent bot archetypes."""

    # v0.35.0 research-aware policy (sim/bots/research_policy.py)
    research_focus: Tuple[str, str, str, str] = ("TRIAGE", "DEFENSE", "RELEASE", "PATENT")
    research_focus_mode: str = "fixed"  # "fixed" | "random" (seeded from the engine rng)
    research_aware: bool = True
    # Preferred Central Market colours for the Triage L3 Breakthrough (falls back to Yellow > Green > Red > Blue)
    market_color_preference: Tuple[DieColor, ...] = ()

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

    # =========================================================================
    # Company Institutional Overrides (Once-per-Version)
    # =========================================================================

    def choose_meridian_override(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        rng: random.Random,
        corruption_track: int = 0,
    ) -> bool:
        """Returns True if the bot activates Meridian's Redundant Crew override."""
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

    def choose_omnidyne_override(
        self,
        player_state: PlayerState,
        game_state: Any,
        rng: random.Random,
    ) -> Optional[int]:
        """Returns die_id in glitched_dice to splice directly to ready, or None."""
        if not player_state.glitched_dice:
            return None
        colored = [d for d in player_state.glitched_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)]
        return colored[0].die_id if colored else player_state.glitched_dice[0].die_id

    def choose_aegis_override(
        self,
        player_state: PlayerState,
        qualifying_colors: List[CubeColor],
        exited_cubes: Dict[CubeColor, int],
        active_version_str: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> Optional[CubeColor]:
        """Returns CubeColor to ignore via Aegis Baffle Echo, or None."""
        if not qualifying_colors:
            return None
        if CubeColor.BLUE in qualifying_colors:
            return CubeColor.BLUE
        if CubeColor.RED in qualifying_colors:
            return CubeColor.RED
        return qualifying_colors[0]

    def choose_dto_override(
        self,
        player_state: PlayerState,
        secrets_at_risk: int,
        active_version_str: str,
        rng: random.Random,
        corruption_track: int = 0,
    ) -> int:
        """Returns secrets to absorb via DTO Slush Fund (up to 2)."""
        return min(2, secrets_at_risk)

    def choose_helix_override(
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
        """Returns True if the bot activates Helix's Brute-Force Bypass override."""
        fn = getattr(self, "choose_prodigy_ability", None)
        if fn is not None:
            func_target = getattr(fn, "__func__", fn)
            if func_target is not BaseBot.choose_helix_override:
                try:
                    return fn(
                        player_state=player_state,
                        active_dice=active_dice,
                        staging_cubes=staging_cubes,
                        stuck_cubes=stuck_cubes,
                        directive_code=directive_code,
                        rng=rng,
                        corruption_track=corruption_track,
                    )
                except TypeError:
                    return fn(
                        player_state,
                        active_dice,
                        staging_cubes,
                        stuck_cubes,
                        directive_code,
                        rng,
                    )
        return False

    def choose_helix_face_override(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        staging_cubes: Dict[CubeColor, int],
        stuck_cubes: Dict[CubeColor, int],
        directive_code: str,
        rng: random.Random,
    ) -> Optional[Tuple[int, Face]]:
        """Returns (die_index, target_face) to turn 1 rolled die to any legal non-Star face, or None."""
        fn = getattr(self, "choose_prodigy_face_override", None)
        if fn is not None:
            func_target = getattr(fn, "__func__", fn)
            if func_target is not BaseBot.choose_helix_face_override:
                try:
                    return fn(
                        player_state=player_state,
                        active_dice=active_dice,
                        staging_cubes=staging_cubes,
                        stuck_cubes=stuck_cubes,
                        directive_code=directive_code,
                        rng=rng,
                    )
                except TypeError:
                    return fn(player_state, active_dice, rng)

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

    def choose_prometheus_override(
        self,
        player_state: PlayerState,
        game_state: Any,
        rng: random.Random,
    ) -> str:
        """Returns 'DISCOUNT' or 'CASH' for Prometheus Algorithmic Arbitrage."""
        return "DISCOUNT" if player_state.money >= 2 else "CASH"

    # =========================================================================
    # White Hat Signature Protocols (Purple Face 6)
    # =========================================================================

    def choose_operator_contingent_staffing(
        self,
        player_state: PlayerState,
        contractor_supply: int,
        rng: random.Random,
    ) -> bool:
        """Operator Protocol: Always accepts free White Contractor die into pool."""
        return contractor_supply > 0

    # =========================================================================
    # Backward Compatibility Aliases
    # =========================================================================
    choose_operator_ability = choose_meridian_override
    choose_phreaker_ability = choose_omnidyne_override
    choose_acoustic_ability = choose_aegis_override
    choose_spook_ability = choose_dto_override
    choose_prodigy_ability = choose_helix_override
    choose_prodigy_face_override = choose_helix_face_override
    choose_cipher_ability = choose_prometheus_override

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
        - Gray Face 5 (+$1 / +1 🔬): if patches < 2, choose 1 (+1 🔬), else choose 0 (+$1).
        - Green Face 4 (+1 🔬 / +$1): if patches < 2, choose 0 (+1 🔬), else choose 1 (+$1).
        - Blue Face 4 (Block 1 Blue / +1 🔬): if Blue threat > 0, choose 0 (Block 1 Blue), else choose 1 (+1 🔬).
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
            elif face.name == "+$1 / +1 🔬":
                declarations[idx] = 1 if player_state.patches < 2 else 0
            elif face.name == "+1 🔬 / +$1":
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
        """Maps die indices in rolled_dice to assigned ShieldColor.

        Generic (ANY) shields are committed as ShieldColor.ANY (flexible generic defense, INV-FLEX-SHIELD-01).
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
                    assignments[idx] = ShieldColor.ANY
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

    def choose_colored_dice_to_return(
        self,
        player: PlayerState,
        count: int,
        threat_strengths: Dict[CubeColor, int],
        expected_income: int = 0,
    ) -> List[Die]:
        """Selects up to `count` owned Colored Module Dice to return to Market in Step 2A (INV-RETURN-CHOICE-01).

        ``expected_income`` (v0.34 six-phase): previewed Phase 3 cash, so a Red shield is judged
        "unfunded" against post-income cash (0 on the legacy path).

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

        # Identify which In Production shield dice are actively needed vs redundant surplus
        needed_shield_ids: Set[int] = set()
        role_to_cube = {
            "RED_SHIELD": CubeColor.RED,
            "BLUE_SHIELD": CubeColor.BLUE,
            "GREEN_SHIELD": CubeColor.GREEN,
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
        for role_name, c_color in role_to_cube.items():
            role_dice = [
                d for d in player.in_production_dice
                if getattr(getattr(d, "production_role", None), "value", getattr(d, "production_role", None)) == role_name
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
            if getattr(getattr(d, "production_role", None), "value", getattr(d, "production_role", None)) == "ANY_SHIELD"
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
            role_val = getattr(role, "value", role)
            is_shield_role = role_val in (
                "RED_SHIELD",
                "BLUE_SHIELD",
                "GREEN_SHIELD",
                "ANY_SHIELD",
            ) or (role is None and eff is not None and eff.is_shield)

            if is_shield_role:
                if d.die_id in needed_shield_ids:
                    # Tier 6: Needed Active Shield
                    if role_val == "BLUE_SHIELD" or (eff and eff.shield_color == ShieldColor.BLUE):
                        s_prio = 5
                    elif role_val == "RED_SHIELD" or (eff and eff.shield_color == ShieldColor.RED):
                        s_prio = 4 if player.money + expected_income < red_threat else 2
                    elif role_val == "ANY_SHIELD" or (eff and eff.shield_color == ShieldColor.ANY):
                        s_prio = 3
                    else:
                        s_prio = 1
                    blk = eff.block_amount if (eff and eff.block_amount > 0) else 1
                    scored_candidates.append(((6, s_prio, blk, is_purple, cost, d.die_id), d))
                else:
                    # Redundant shield: if it has income output (e.g. R1, G1, G2, B3), score as Income Tier 4/5
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

    def choose_fast_patches(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> List[int]:
        """Deprecated in v0.29.0: Fast-patching is excised (INV-FASTPATCH-EXCISE-01)."""
        return []

    def take_operations_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        """Phase 6: Operations. Called after Income, Attack Resolution and Pipeline Shift."""
        if type(self).take_phase3_actions is not BaseBot.take_phase3_actions:
            return self.take_phase3_actions(player_state, game_state, rng)  # legacy subclass override
        return Phase3ActionPlan()

    def take_phase3_actions(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Phase3ActionPlan:
        """Deprecated alias (v0.33 name) of take_operations_actions."""
        if type(self).take_operations_actions is not BaseBot.take_operations_actions:
            return self.take_operations_actions(player_state, game_state, rng)
        return Phase3ActionPlan()

    # ------------------------------------------------------------------
    # v0.34.0 Six-Phase hooks
    # ------------------------------------------------------------------
    def choose_scanned_graduates(
        self,
        player_state: PlayerState,
        n: int,
        game_state: Optional[GameState] = None,
        rng: Optional[random.Random] = None,
    ) -> List[Die]:
        """Phase 5 step 3: choose up to n dice to graduate Scanned -> Ready (OQ-1: fewer is allowed; the
        default graduates the maximum). Priority: Purple, then Colored by descending cost, then Gray."""
        key = lambda d: (  # noqa: E731
            0 if d.color == DieColor.PURPLE else (1 if d.color != DieColor.GRAY else 2),
            -getattr(d, "cost", 0),
            d.die_id,
        )
        return sorted(player_state.scanned_dice, key=key)[: max(0, n)]

    def choose_malware_glitch_targets(
        self,
        player_state: PlayerState,
        in_production_dice: List[Die],
        count: int,
        game_state: Optional[GameState] = None,
    ) -> List[Die]:
        """Phase 4 Green Malware targets (six-phase). Income is already collected, so only future
        availability matters: White first (Contractor Sacrifice), Gray, cheapest Colored, Purple last."""
        key = lambda d: (  # noqa: E731
            0 if d.color == DieColor.WHITE else 1,
            0 if d.color == DieColor.GRAY else 1,
            1 if d.color == DieColor.PURPLE else 0,
            getattr(d, "cost", 0),
            d.die_id,
        )
        return sorted(in_production_dice, key=key)[: max(0, count)]

    def release_pressure(self, player_state: PlayerState, planned_purchases: int = 0) -> int:
        """Permanent dice (+ planned purchases) in excess of Release Bandwidth."""
        permanent = sum(1 for d in player_state.total_dice if d.color != DieColor.WHITE)
        return max(0, permanent + planned_purchases - player_state.release_bandwidth)

    def plan_release_upgrade(
        self,
        player_state: PlayerState,
        plan: Phase3ActionPlan,
        res_available: int,
        min_pressure: int = 1,
    ) -> int:
        """Six-phase Release Track valuation (Levels 1 and 2). Appends "RELEASE" when owned dice exceed
        Release Bandwidth and research allows; returns the remaining research budget."""
        if player_state.release_level >= 2:
            return res_available
        planned = len(plan.market_purchases)
        if plan.buy_purple_reserve and DieColor.PURPLE not in plan.market_purchases:
            planned += 1
        if plan.use_prometheus_override and plan.prometheus_mode in ("BUY_FREE_DIE", "DISCOUNT"):
            planned += 1
        if self.release_pressure(player_state, planned) < min_pressure:
            return res_available
        cost = player_state.get_track_upgrade_cost("RELEASE")
        if cost is None or res_available < cost:
            return res_available
        plan.track_upgrades.append("RELEASE")
        return res_available - cost

    def expected_income(
        self,
        player_state: PlayerState,
        game_state: Optional[GameState] = None,
        exclude_die_ids: Iterable[int] = (),
    ) -> int:
        """Previewed Phase 3 cash ($ only) from dice still In Production."""
        if game_state is None:
            return 0
        from sim.engine.phase3_income import preview_player_income

        excluded = set(exclude_die_ids)
        rec = preview_player_income(game_state, player_state)
        return sum(r["money"] for r in rec.details if r["die_id"] not in excluded)

    def choose_purple_reserve_purchase(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> bool:
        """Evaluates whether to purchase the single reserve Purple die ($4-$6) (v0.34 only)."""
        if not purple_purchasable(game_state):
            return False
        if getattr(player_state, "personal_purple_reserve", 0) <= 0:
            return False
        reserve_cost = player_state.get_purple_reserve_cost() if hasattr(player_state, "get_purple_reserve_cost") else 4
        if player_state.money < reserve_cost:
            return False
        # Since player already starts with 1 Purple die, purchasing the 2nd Purple die
        # is prioritized when cash reserves exceed $8 or when facing heavy threat (>4 cubes).
        return player_state.money >= (reserve_cost + 2)

    def choose_breakthrough(
        self,
        player_state: PlayerState,
        game_state: GameState,
        track: str,
        level: int,
        options: Any,
    ) -> Any:
        """v0.35.0 Breakthrough choice (only Triage L3 is optional). Default: accept if possible; Gray die
        Glitched > Scanned > Ready (lowest die_id within zone); colour by ``market_color_preference`` then
        Yellow > Green > Red > Blue."""
        from sim.engine.research_tracks import TRIAGE_L3_COLOR_FALLBACK, BreakthroughChoice

        if options is None:
            return BreakthroughChoice()
        if not getattr(options, "possible", False):
            return BreakthroughChoice(accept=False)
        color = None
        for c in tuple(self.market_color_preference) + TRIAGE_L3_COLOR_FALLBACK:
            if c in options.colors:
                color = c
                break
        return BreakthroughChoice(accept=True, gray_die_id=options.gray_die_ids[0], color=color)

    def choose_slush_fund(self, player_state: PlayerState, game_state: GameState, potential_secret_loss: int) -> bool:
        """v0.35.0 DTO Slush Fund (once per game, optional): use on a 2+ Secret loss or to avoid a Total Data Breach."""
        return potential_secret_loss >= 2 or player_state.secrets - potential_secret_loss <= 0

    def choose_spook_burn_notice(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Optional[int]:
        """Chooses an owned colored die to permanently burn to market for +1 Secret."""
        if player_state.secrets <= 3 and not getattr(game_state, "is_final_round", False):
            return None  # Do not cannibalize dice early if secrets are precarious
        # Prioritize burning glitched colored dice over active ready dice
        glitched_colored = [d for d in player_state.glitched_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)]
        if glitched_colored:
            return glitched_colored[0].die_id
        if getattr(game_state, "is_final_round", False):
            # In final round, burn lowest-impact colored die for +1 Secret tiebreaker
            candidates = [d for d in player_state.colored_dice if d.color != DieColor.PURPLE]
            if candidates:
                return candidates[0].die_id
        return None

    def choose_phreaker_jumper_diagnostics(
        self,
        player_state: PlayerState,
        game_state: GameState,
        rng: random.Random,
    ) -> Optional[int]:
        """Selects an offline die to roll for diagnostics. If pipeline empty, returns None (invokes fallback)."""
        ud_dice = player_state.under_development_dice
        if not ud_dice:
            return None  # Triggers +$1 cash fallback cleanly
        # Prioritize Green/Yellow dice for higher expected yield
        best_die = max(
            ud_dice,
            key=lambda d: 2 if d.color in (DieColor.GREEN, DieColor.YELLOW) else 1,
        )
        return best_die.die_id

    def choose_prodigy_purple_star_override(
        self,
        player_state: PlayerState,
        active_dice: List[Die],
        rng: random.Random,
    ) -> Optional[Tuple[int, Face]]:
        """Selects a die in active pool to override to any legal non-Star face."""
        # Find any other die with a Glitch or unwanted face
        for idx, d in enumerate(active_dice):
            eff = d.effective_face or d.current_face
            if eff and eff.is_star and eff.star_code == "PURPLE_STAR":
                continue
            if d.current_face and d.current_face.is_glitch:
                # Override to Block 1 Any or +$2
                target = Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY)
                return (idx, target)
        return None


