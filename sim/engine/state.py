"""Data classes and game state definitions for Rogue Agent engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    Die,
    Face,
    VariantCard,
    VersionCard,
    create_gray_die,
    create_white_die,
    get_all_archetype_cards,
    get_archetype_by_code,
    get_default_variant_cards,
    get_default_version_deck,
    get_random_archetypes,
)
from sim.tower import CubeTower

if TYPE_CHECKING:
    from sim.bots.base import BaseBot


@dataclass
class PlayerState:
    """Tracks corporate resources, dice pools, and breach status for one player."""

    player_id: int
    bot: BaseBot
    money: int
    secrets: int
    patches: int
    ready_dice: List[Die] = field(default_factory=list)
    unpatched_dice: List[Die] = field(default_factory=list)
    contractor_dice: List[Die] = field(default_factory=list)
    hired_contractor_count: int = 0
    is_patient_zero: bool = False
    elimination_round: Optional[int] = None
    elimination_reason: Optional[str] = None
    debt: int = 0  # Money deficit below $0
    breach_depth: int = 0  # Secret deficit below 0
    unfulfilled_destructions: int = 0  # Unfulfilled die destructions
    total_dirty_income_taken: int = 0
    total_contractors_hired: int = 0
    total_rerolls_used: int = 0
    b2_available: bool = False
    y1_available: bool = False
    p1_available: bool = False
    p3_available: Optional[ShieldColor] = None
    archetype: Optional[ArchetypeCard] = None
    ability_v1_status: AbilityStatus = AbilityStatus.AVAILABLE
    ability_v2_status: AbilityStatus = AbilityStatus.LOCKED
    ability_v3_status: AbilityStatus = AbilityStatus.LOCKED
    system_reboot_used: bool = False

    @property
    def can_system_reboot(self) -> bool:
        return not self.system_reboot_used and len(self.ready_dice) == 0

    def execute_system_reboot(self) -> List[Die]:
        if not self.can_system_reboot:
            raise ValueError("Cannot execute system reboot: player already used reboot or has ready dice")
        self.system_reboot_used = True
        restored: List[Die] = []
        remaining_unpatched: List[Die] = []
        for die in self.unpatched_dice:
            if die.color == DieColor.GRAY:
                die.is_locked = False
                die.chosen_choice_index = None
                self.ready_dice.append(die)
                restored.append(die)
            else:
                remaining_unpatched.append(die)
        self.unpatched_dice = remaining_unpatched
        return restored

    @property
    def total_dice(self) -> List[Die]:
        return self.ready_dice + self.unpatched_dice

    @property
    def colored_dice(self) -> List[Die]:
        return [d for d in self.total_dice if d.color != DieColor.GRAY]

    @staticmethod
    def _normalize_version_key(v: str) -> int:
        s = str(v).strip().lower()
        if "1" in s:
            return 1
        elif "2" in s:
            return 2
        elif "3" in s:
            return 3
        raise ValueError(f"Unknown version string: {v}")

    def get_ability_status(self, version_str: str) -> AbilityStatus:
        k = self._normalize_version_key(version_str)
        if k == 1:
            return self.ability_v1_status
        elif k == 2:
            return self.ability_v2_status
        elif k == 3:
            return self.ability_v3_status
        raise ValueError(f"Unknown version string: {version_str}")

    def is_ability_available(self, version_str: Optional[str] = None) -> bool:
        if version_str is not None:
            return self.get_ability_status(version_str) == AbilityStatus.AVAILABLE
        return (
            self.ability_v1_status == AbilityStatus.AVAILABLE
            or self.ability_v2_status == AbilityStatus.AVAILABLE
            or self.ability_v3_status == AbilityStatus.AVAILABLE
        )

    def mark_ability_used(self, version_str: Optional[str] = None) -> None:
        if version_str is not None:
            k = self._normalize_version_key(version_str)
            if k == 1:
                self.ability_v1_status = AbilityStatus.USED
            elif k == 2:
                self.ability_v2_status = AbilityStatus.USED
            elif k == 3:
                self.ability_v3_status = AbilityStatus.USED
            else:
                raise ValueError(f"Unknown version string: {version_str}")
        else:
            if self.ability_v1_status == AbilityStatus.AVAILABLE:
                self.ability_v1_status = AbilityStatus.USED
            elif self.ability_v2_status == AbilityStatus.AVAILABLE:
                self.ability_v2_status = AbilityStatus.USED
            elif self.ability_v3_status == AbilityStatus.AVAILABLE:
                self.ability_v3_status = AbilityStatus.USED
            else:
                raise ValueError("No ability is currently available to mark as used")

    def mark_ability_forfeited(self, version_str: str) -> None:
        k = self._normalize_version_key(version_str)
        if k == 1:
            if self.ability_v1_status == AbilityStatus.AVAILABLE:
                self.ability_v1_status = AbilityStatus.FORFEITED
        elif k == 2:
            if self.ability_v2_status == AbilityStatus.AVAILABLE:
                self.ability_v2_status = AbilityStatus.FORFEITED
        elif k == 3:
            if self.ability_v3_status == AbilityStatus.AVAILABLE:
                self.ability_v3_status = AbilityStatus.FORFEITED
        else:
            raise ValueError(f"Unknown version string: {version_str}")

    def unlock_version_ability(self, version_str: str) -> None:
        k = self._normalize_version_key(version_str)
        if k == 1:
            if self.ability_v1_status == AbilityStatus.LOCKED:
                self.ability_v1_status = AbilityStatus.AVAILABLE
        elif k == 2:
            if self.ability_v2_status == AbilityStatus.LOCKED:
                self.ability_v2_status = AbilityStatus.AVAILABLE
        elif k == 3:
            if self.ability_v3_status == AbilityStatus.LOCKED:
                self.ability_v3_status = AbilityStatus.AVAILABLE
        else:
            raise ValueError(f"Unknown version string: {version_str}")

    @property
    def v1_used(self) -> bool:
        return self.ability_v1_status == AbilityStatus.USED

    @property
    def v2_used(self) -> bool:
        return self.ability_v2_status == AbilityStatus.USED

    @property
    def v3_used(self) -> bool:
        return self.ability_v3_status == AbilityStatus.USED


@dataclass
class RoundTelemetry:
    """Per-round execution metrics for telemetry and balance analysis."""

    round_number: int
    active_version_name: str
    corruption_track: int
    staged_cubes: Dict[CubeColor, int]
    stuck_cubes_before: Dict[CubeColor, int]
    exited_cubes: Dict[CubeColor, int]
    stuck_cubes_after: Dict[CubeColor, int]
    attack_strengths: Dict[CubeColor, int]
    player_snapshots: List[Dict]
    buffer_overflow: bool = False


@dataclass
class EndGameResult:
    """Comprehensive post-game evaluation and final standings."""

    end_reason: EndGameReason
    total_rounds: int
    winner_id: Optional[int]
    is_total_wipeout: bool
    singularity_reached: bool
    rankings: List[Dict]
    telemetry_history: List[RoundTelemetry]
    total_buffer_overflows: int = 0


@dataclass
class GameState:
    """Complete simulation state for a running match."""

    config: GameConfig
    players: List[PlayerState]
    market: Dict[DieColor, int]
    variant_cards: Dict[DieColor, VariantCard]
    version_deck: List[VersionCard]
    current_version_index: int = 0
    corruption_track: int = 0
    staging_cup: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
    )
    tower: CubeTower = field(init=False)
    priming_exited_cubes: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
    )
    priming_stuck_cubes: Dict[CubeColor, int] = field(
        default_factory=lambda: {
            CubeColor.RED: 0,
            CubeColor.BLUE: 0,
            CubeColor.GREEN: 0,
            CubeColor.BLACK: 0,
        }
    )
    last_round_buffer_overflow: bool = False
    total_buffer_overflows: int = 0
    first_player_index: int = 0
    current_round: int = 1
    game_over: bool = False
    is_final_round: bool = False
    end_reason: EndGameReason = EndGameReason.NONE
    singularity_triggered: bool = False
    contractor_supply: int = 12
    next_die_id: int = 1
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        self.tower = CubeTower(self.config)

    @property
    def active_version(self) -> VersionCard:
        return self.version_deck[self.current_version_index]

    @property
    def active_directive_code(self) -> str:
        return self.active_version.directive_code


