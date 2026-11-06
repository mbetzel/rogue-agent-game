"""Data classes and game state definitions for Rogue Agent engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from sim.config import CubeColor, DieColor, EndGameReason, GameConfig, ShieldColor
from sim.entities import (
    AbilityStatus,
    ArchetypeCard,
    ArchetypeCode,
    Company,
    CompanyCode,
    WhiteHat,
    WhiteHatCode,
    COMPANIES,
    WHITE_HATS,
    CANONICAL_COMPANY_FOR_OPERATIVE,
    CANONICAL_OPERATIVE_FOR_COMPANY,
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
from enum import Enum

if TYPE_CHECKING:
    from sim.bots.base import BaseBot


class ProductionRole(str, Enum):
    """Assignment role of a die deployed In Production."""

    INCOME = "INCOME"
    RED_SHIELD = "RED_SHIELD"
    BLUE_SHIELD = "BLUE_SHIELD"
    GREEN_SHIELD = "GREEN_SHIELD"
    ANY_SHIELD = "ANY_SHIELD"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


@dataclass
class _UnderDevelopmentProxy(list):
    """Proxy list enabling legacy code and tests to mutate unpatched_dice directly."""

    def __init__(self, player: "PlayerState") -> None:
        self.player = player
        super().__init__(player.glitched_dice + player.scanned_dice)

    def append(self, item: Die) -> None:
        self.player.glitched_dice.append(item)
        super().append(item)

    def extend(self, iterable: Any) -> None:
        for item in iterable:
            self.append(item)

    def insert(self, index: int, item: Die) -> None:
        self.player.glitched_dice.insert(index, item)
        super().insert(index, item)

    def remove(self, item: Die) -> None:
        if item in self.player.glitched_dice:
            self.player.glitched_dice.remove(item)
        elif item in self.player.scanned_dice:
            self.player.scanned_dice.remove(item)
        super().remove(item)

    def pop(self, index: int = -1) -> Die:
        item = super().pop(index)
        if item in self.player.glitched_dice:
            self.player.glitched_dice.remove(item)
        elif item in self.player.scanned_dice:
            self.player.scanned_dice.remove(item)
        return item

    def clear(self) -> None:
        self.player.glitched_dice.clear()
        self.player.scanned_dice.clear()
        super().clear()


class PlayerState:
    """Tracks corporate resources, dice pools, and breach status for one player."""

    player_id: int
    bot: BaseBot
    money: int
    secrets: int
    research_tokens: int = 0

    # --- CI/CD Pipeline & Hardware Bottlenecks (v0.29.0 Canonical) ---
    defense_capacity: int = 2
    triage_bandwidth: int = 2
    release_bandwidth: int = 4
    triage_level: int = 0
    release_level: int = 0
    defense_level: int = 0
    patent_level: int = 0
    has_emergency_hotfix: bool = False
    has_passive_firewall: bool = False
    upgrade_discount: int = 0

    # --- CI/CD Pipeline Zones (v0.22.0 Canonical) ---
    ready_for_release_dice: List[Die] = field(default_factory=list)
    in_production_dice: List[Die] = field(default_factory=list)
    glitched_dice: List[Die] = field(default_factory=list)
    scanned_dice: List[Die] = field(default_factory=list)
    contractor_dice: List[Die] = field(default_factory=list)
    hired_contractor_count: int = 0

    # --- Personal Reserve (v0.30.0 Canonical) ---
    personal_purple_reserve: int = 1  # [INV-PURPLE-RES-01: 1 reserve die remaining]
    purple_star_available: bool = False
    purple_star_count: int = 0

    is_patient_zero: bool = False
    elimination_round: Optional[int] = None
    elimination_reason: Optional[str] = None
    debt: int = 0  # Money deficit below $0
    breach_depth: int = 0  # Secret deficit below 0
    unfulfilled_destructions: int = 0  # Unfulfilled die destructions
    total_dirty_income_taken: int = 0
    total_contractors_hired: int = 0
    total_rerolls_used: int = 0
    hash_matches_secrets: int = 0
    total_fast_patches: int = 0
    b2_available: bool = False
    y1_available: bool = False
    p1_available: bool = False
    p3_available: Optional[ShieldColor] = None
    company: Optional[Company] = None
    white_hat: Optional[WhiteHat] = None
    ability_v1_status: AbilityStatus = AbilityStatus.AVAILABLE
    ability_v2_status: AbilityStatus = AbilityStatus.LOCKED
    ability_v3_status: AbilityStatus = AbilityStatus.LOCKED

    def __init__(
        self,
        player_id: int,
        bot: BaseBot,
        money: int,
        secrets: int,
        patches: int,
        ready_for_release_dice: Optional[List[Die]] = None,
        in_production_dice: Optional[List[Die]] = None,
        glitched_dice: Optional[List[Die]] = None,
        scanned_dice: Optional[List[Die]] = None,
        contractor_dice: Optional[List[Die]] = None,
        hired_contractor_count: int = 0,
        personal_purple_reserve: int = 2,
        purple_star_available: bool = False,
        purple_star_count: int = 0,
        is_patient_zero: bool = False,
        elimination_round: Optional[int] = None,
        elimination_reason: Optional[str] = None,
        debt: int = 0,
        breach_depth: int = 0,
        unfulfilled_destructions: int = 0,
        total_dirty_income_taken: int = 0,
        total_contractors_hired: int = 0,
        total_rerolls_used: int = 0,
        hash_matches_secrets: int = 0,
        total_fast_patches: int = 0,
        b2_available: bool = False,
        y1_available: bool = False,
        p1_available: bool = False,
        p3_available: Optional[ShieldColor] = None,
        company: Optional[Company] = None,
        white_hat: Optional[WhiteHat] = None,
        archetype: Optional[ArchetypeCard] = None,
        ability_v1_status: AbilityStatus = AbilityStatus.AVAILABLE,
        ability_v2_status: AbilityStatus = AbilityStatus.LOCKED,
        ability_v3_status: AbilityStatus = AbilityStatus.LOCKED,
        ready_dice: Optional[List[Die]] = None,
        unpatched_dice: Optional[List[Die]] = None,
        research_tokens: Optional[int] = None,
        defense_capacity: Optional[int] = None,
        triage_bandwidth: Optional[int] = None,
        release_bandwidth: Optional[int] = None,
        triage_level: Optional[int] = None,
        release_level: Optional[int] = None,
        pipeline_level: Optional[int] = None,
        defense_level: Optional[int] = None,
        patent_level: Optional[int] = None,
        has_emergency_hotfix: bool = False,
        has_passive_firewall: bool = False,
        upgrade_discount: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        self.player_id = player_id
        self.bot = bot
        self.money = money
        self.secrets = secrets
        self.research_tokens = patches if research_tokens is None else research_tokens

        if ready_for_release_dice is not None:
            self.ready_for_release_dice = list(ready_for_release_dice)
        elif ready_dice is not None:
            self.ready_for_release_dice = list(ready_dice)
        else:
            self.ready_for_release_dice = []

        self.in_production_dice = list(in_production_dice) if in_production_dice is not None else []

        if glitched_dice is not None:
            self.glitched_dice = list(glitched_dice)
            self.scanned_dice = list(scanned_dice) if scanned_dice is not None else []
        elif unpatched_dice is not None:
            self.glitched_dice = list(unpatched_dice)
            self.scanned_dice = list(scanned_dice) if scanned_dice is not None else []
        else:
            self.glitched_dice = []
            self.scanned_dice = list(scanned_dice) if scanned_dice is not None else []

        self.contractor_dice = list(contractor_dice) if contractor_dice is not None else []
        self.hired_contractor_count = hired_contractor_count

        self.is_patient_zero = is_patient_zero
        self.elimination_round = elimination_round
        self.elimination_reason = elimination_reason
        self.debt = debt
        self.breach_depth = breach_depth
        self.unfulfilled_destructions = unfulfilled_destructions
        self.total_dirty_income_taken = total_dirty_income_taken
        self.total_contractors_hired = total_contractors_hired
        self.total_rerolls_used = total_rerolls_used
        self.b2_available = b2_available
        self.y1_available = y1_available
        self.p1_available = p1_available
        self.p3_available = p3_available

        if company is not None and white_hat is not None:
            self.company = company
            self.white_hat = white_hat
        elif archetype is not None:
            self.archetype = archetype
        elif company is not None:
            self.company = company
            self.white_hat = WHITE_HATS[CANONICAL_OPERATIVE_FOR_COMPANY[company.code]]
        elif white_hat is not None:
            self.white_hat = white_hat
            self.company = COMPANIES[CANONICAL_COMPANY_FOR_OPERATIVE[white_hat.code]]
        else:
            self.company = None
            self.white_hat = None

        if self.company is not None:
            self.defense_capacity = getattr(self.company, "starting_defense_capacity", 2) if defense_capacity is None else defense_capacity
            self.triage_bandwidth = getattr(self.company, "starting_triage_bandwidth", 2) if triage_bandwidth is None else triage_bandwidth
            self.release_bandwidth = getattr(self.company, "starting_release_bandwidth", 4) if release_bandwidth is None else release_bandwidth
            init_triage = triage_level if triage_level is not None else (pipeline_level if pipeline_level is not None else getattr(self.company, "starting_triage_level", 0))
            init_release = release_level if release_level is not None else (pipeline_level if pipeline_level is not None else getattr(self.company, "starting_release_level", 0))
            self.triage_level = init_triage
            self.release_level = init_release
            self.defense_level = getattr(self.company, "starting_defense_level", 0) if defense_level is None else defense_level
            self.patent_level = getattr(self.company, "starting_patent_level", 0) if patent_level is None else patent_level
            self.upgrade_discount = getattr(self.company, "upgrade_discount", 0) if upgrade_discount is None else upgrade_discount
        else:
            self.defense_capacity = 2 if defense_capacity is None else defense_capacity
            self.triage_bandwidth = 2 if triage_bandwidth is None else triage_bandwidth
            self.release_bandwidth = 4 if release_bandwidth is None else release_bandwidth
            init_triage = triage_level if triage_level is not None else (pipeline_level if pipeline_level is not None else 0)
            init_release = release_level if release_level is not None else (pipeline_level if pipeline_level is not None else 0)
            self.triage_level = init_triage
            self.release_level = init_release
            self.defense_level = 0 if defense_level is None else defense_level
            self.patent_level = 0 if patent_level is None else patent_level
            self.upgrade_discount = 0 if upgrade_discount is None else upgrade_discount

        self.has_emergency_hotfix = has_emergency_hotfix or (self.triage_level >= 2)
        self.has_passive_firewall = has_passive_firewall or (self.defense_level >= 2)

        self.ability_v1_status = ability_v1_status
        self.ability_v2_status = ability_v2_status
        self.ability_v3_status = ability_v3_status
        self.personal_purple_reserve = personal_purple_reserve
        self.purple_star_available = purple_star_available
        self.purple_star_count = purple_star_count

    # --- Backward Compatibility Properties & Hardware Methods ---
    @property
    def patches(self) -> int:
        """Backward compatibility bridge forwarding patches to research_tokens."""
        return self.research_tokens

    @patches.setter
    def patches(self, value: int) -> None:
        self.research_tokens = value

    @property
    def pipeline_level(self) -> int:
        return self.triage_level

    @pipeline_level.setter
    def pipeline_level(self, value: int) -> None:
        self.triage_level = value
        self.release_level = value

    @property
    def hash_matches_secrets(self) -> int:
        return getattr(self, "_hash_matches_secrets", 0)

    @hash_matches_secrets.setter
    def hash_matches_secrets(self, value: int) -> None:
        self._hash_matches_secrets = value

    @property
    def total_fast_patches(self) -> int:
        return getattr(self, "_total_fast_patches", 0)

    @total_fast_patches.setter
    def total_fast_patches(self, value: int) -> None:
        self._total_fast_patches = value

    def get_track_upgrade_cost(self, track: str) -> Optional[int]:
        """Calculates research cost to upgrade the specified terminal mat track (INV-UPGRADE-TRACK-01)."""
        t = track.upper().strip()
        if t == "TRIAGE":
            if self.triage_level == 0:
                base_cost = 2
            elif self.triage_level == 1:
                base_cost = 3
            else:
                return None
        elif t == "RELEASE":
            if self.release_level == 0:
                base_cost = 2
            elif self.release_level == 1:
                base_cost = 3
            else:
                return None
        elif t == "DEFENSE":
            if self.defense_level == 0:
                base_cost = 2
            elif self.defense_level == 1:
                base_cost = 3
            else:
                return None
        elif t == "PATENT":
            if self.patent_level == 0:
                base_cost = 2
            elif self.patent_level == 1:
                base_cost = 3
            else:
                return None
        elif t == "PIPELINE":
            if self.pipeline_level == 0:
                base_cost = 2
            elif self.pipeline_level == 1:
                base_cost = 3
            else:
                return None
        else:
            return None
        return max(1, base_cost - self.upgrade_discount)

    def upgrade_track(self, track: str) -> bool:
        """Upgrades the specified terminal track, expanding hardware capabilities (INV-UPGRADE-TRACK-01)."""
        t = track.upper().strip()
        cost = self.get_track_upgrade_cost(t)
        if cost is None or self.research_tokens < cost:
            return False
        self.research_tokens -= cost
        if t == "TRIAGE":
            if self.triage_level == 0:
                self.triage_level = 1
                self.triage_bandwidth = max(self.triage_bandwidth, 3)
            elif self.triage_level == 1:
                self.triage_level = 2
                self.triage_bandwidth = max(self.triage_bandwidth, 4)
                self.has_emergency_hotfix = True
        elif t == "RELEASE":
            if self.release_level == 0:
                self.release_level = 1
                self.release_bandwidth = max(self.release_bandwidth, 5)
            elif self.release_level == 1:
                self.release_level = 2
                self.release_bandwidth = max(self.release_bandwidth, 6)
        elif t == "DEFENSE":
            if self.defense_level == 0:
                self.defense_level = 1
                self.defense_capacity = max(self.defense_capacity, 3)
            elif self.defense_level == 1:
                self.defense_level = 2
                self.defense_capacity = max(self.defense_capacity, 4)
                self.has_passive_firewall = True
        elif t == "PATENT":
            if self.patent_level == 0:
                self.patent_level = 1
            elif self.patent_level == 1:
                self.patent_level = 2
        elif t == "PIPELINE":
            if self.pipeline_level == 0:
                self.triage_level = 1
                self.triage_bandwidth = max(self.triage_bandwidth, 3)
                self.release_level = 1
                self.release_bandwidth = max(self.release_bandwidth, 3)
            elif self.pipeline_level == 1:
                self.triage_level = 2
                self.triage_bandwidth = max(self.triage_bandwidth, 4)
                self.release_level = 2
                self.release_bandwidth = max(self.release_bandwidth, 4)
                self.has_emergency_hotfix = True
        return True

    def get_patent_cost(self) -> int:
        """Returns research token cost to file a Cryptographic Patent for +1 Corporate Secret."""
        if self.patent_level == 0:
            return 4
        elif self.patent_level == 1:
            return 3
        else:
            return 2

    def file_patent(self) -> bool:
        """Files a Cryptographic Patent: spends research tokens to gain +1 Corporate Secret (INV-PATENT-CONV-01)."""
        cost = self.get_patent_cost()
        if self.research_tokens < cost:
            return False
        self.research_tokens -= cost
        self.secrets += 1
        if self.patent_level >= 2:
            self.money += 1
        return True

    # --- Backward Compatibility Properties ---
    @property
    def archetype(self) -> Optional[ArchetypeCard]:
        """Backward compatibility bridge mapping Company/WhiteHat to legacy ArchetypeCard."""
        if self.white_hat is not None:
            code_str = self.white_hat.code.value
            return get_archetype_by_code(code_str)
        if self.company is not None:
            compat_map = {
                CompanyCode.MERIDIAN: ArchetypeCode.OPERATOR,
                CompanyCode.OMNIDYNE: ArchetypeCode.PHREAKER,
                CompanyCode.AEGIS: ArchetypeCode.ACOUSTIC,
                CompanyCode.DTO: ArchetypeCode.SPOOK,
                CompanyCode.HELIX: ArchetypeCode.PRODIGY,
                CompanyCode.PROMETHEUS: ArchetypeCode.CIPHER,
            }
            legacy_code = compat_map.get(self.company.code)
            if legacy_code:
                return get_archetype_by_code(legacy_code)
        return None

    @archetype.setter
    def archetype(self, value: Optional[ArchetypeCard]) -> None:
        """Backward compatibility setter initializing Company and WhiteHat from legacy ArchetypeCard."""
        if value is None:
            self.company = None
            self.white_hat = None
            return

        legacy_code = value.code if isinstance(value.code, ArchetypeCode) else ArchetypeCode(value.code)
        wh_code = WhiteHatCode(legacy_code.value)
        self.company = COMPANIES[CANONICAL_COMPANY_FOR_OPERATIVE[wh_code]]
        self.white_hat = WHITE_HATS[wh_code]

    # --- CI/CD Pipeline In Production Role Accessors ---
    @property
    def income_dice(self) -> List[Die]:
        """Modules in In Production producing cash, patches, or special abilities."""
        return [
            d for d in self.in_production_dice
            if getattr(d, "production_role", None) == ProductionRole.INCOME
        ]

    @property
    def red_shield_dice(self) -> List[Die]:
        """Modules in In Production actively assigned to Red defense."""
        return [
            d for d in self.in_production_dice
            if getattr(d, "production_role", None) == ProductionRole.RED_SHIELD
        ]

    @property
    def blue_shield_dice(self) -> List[Die]:
        """Modules in In Production actively assigned to Blue defense."""
        return [
            d for d in self.in_production_dice
            if getattr(d, "production_role", None) == ProductionRole.BLUE_SHIELD
        ]

    @property
    def green_shield_dice(self) -> List[Die]:
        """Modules in In Production actively assigned to Green defense."""
        return [
            d for d in self.in_production_dice
            if getattr(d, "production_role", None) == ProductionRole.GREEN_SHIELD
        ]

    @property
    def any_shield_dice(self) -> List[Die]:
        """Modules in In Production actively assigned to Generic Any defense."""
        return [
            d for d in self.in_production_dice
            if getattr(d, "production_role", None) == ProductionRole.ANY_SHIELD
        ]

    @property
    def shield_dice(self) -> List[Die]:
        """All modules actively assigned to defense across Red, Blue, Green, and Any."""
        return [
            d for d in self.in_production_dice
            if getattr(d, "production_role", None) in (
                ProductionRole.RED_SHIELD,
                ProductionRole.BLUE_SHIELD,
                ProductionRole.GREEN_SHIELD,
                ProductionRole.ANY_SHIELD,
            )
        ]

    @property
    def under_development_dice(self) -> List[Die]:
        """All modules currently in the Under Development pipeline (Glitched + Scanned)."""
        return self.glitched_dice + self.scanned_dice

    # --- Backward Compatibility Accessors & Aliases ---
    @property
    def ready_dice(self) -> List[Die]:
        """Backward compatibility alias for ready_for_release_dice."""
        return self.ready_for_release_dice

    @ready_dice.setter
    def ready_dice(self, value: List[Die]) -> None:
        self.ready_for_release_dice = list(value)

    @property
    def unpatched_dice(self) -> List[Die]:
        """Backward compatibility alias mapping to under_development_dice (glitched + scanned)."""
        return _UnderDevelopmentProxy(self)

    @unpatched_dice.setter
    def unpatched_dice(self, value: List[Die]) -> None:
        self.glitched_dice = list(value)
        self.scanned_dice.clear()

    @property
    def total_dice(self) -> List[Die]:
        """All owned dice across all terminal zones (excludes temporary White contractors)."""
        return (
            self.ready_for_release_dice
            + self.in_production_dice
            + self.glitched_dice
            + self.scanned_dice
        )

    @property
    def colored_dice(self) -> List[Die]:
        """All owned non-Gray software module dice across all terminal zones."""
        return [d for d in self.total_dice if d.color != DieColor.GRAY and d.color != DieColor.WHITE]

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

    def get_purple_reserve_cost(self) -> int:
        """Returns the dynamic procurement cost for this player's Personal Purple Reserve."""
        if self.white_hat is not None:
            return getattr(self.white_hat, "reserve_cost", 4)
        return 4

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
    # --- v0.34.0 Six-Phase telemetry (defaults keep legacy constructors valid) ---
    round_sequence: str = "V033_THREE_PHASE"
    phases_executed: List[int] = field(default_factory=list)  # e.g. [1,2,3,4,5,6] or [1,2]
    phase_snapshots: Dict[int, List[Dict]] = field(default_factory=dict)  # key = phase that just ended
    income_by_player: Dict[int, Dict[str, int]] = field(default_factory=dict)  # {"money","research","secrets"}
    scanned_held_by_player: Dict[int, int] = field(default_factory=dict)  # Scanned count after Phase 5 step 3
    graduated_by_player: Dict[int, int] = field(default_factory=dict)
    purple_star_triggers_per_round: Dict[int, int] = field(default_factory=dict)  # Signature Protocol triggers (OQ-17)
    final_round_trigger_phase: Optional[int] = None  # 2 or 4
    end_phase: Optional[int] = None  # phase in which game_over was set


# ---------------------------------------------------------------------------
# v0.34.0 Six-Phase shared types
# ---------------------------------------------------------------------------
# As returned by Phase 1 (Roll & Deploy): (player, rolled dice, {rolled-index: shield color})
Commitments = List[Tuple["PlayerState", List[Die], Dict[int, ShieldColor]]]


@dataclass
class CompileResult:
    """Phase 2 (Compiler Drop & Corruption) output, consumed by Phase 4 and telemetry."""

    staged_before: Dict[CubeColor, int]
    stuck_before: Dict[CubeColor, int]
    exited_cubes: Dict[CubeColor, int]  # mutable: Mode-B corruption cube adds land here
    stuck_after: Dict[CubeColor, int]
    buffer_overflow: bool = False
    black_dropped: int = 0
    breached_pids: Set[int] = field(default_factory=set)  # players who became Patient Zero during Phase 2


@dataclass
class IncomeRecord:
    """Phase 3 (Income) result for one player (deltas plus per-die detail rows)."""

    money: int = 0
    research: int = 0
    secrets: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)
    burned_die_id: Optional[int] = None
    burned_die_ids: List[int] = field(default_factory=list)
    diagnostics_face: Optional[str] = None
    purple_star_triggers: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "money": self.money,
            "research": self.research,
            "secrets": self.secrets,
            "details": list(self.details),
            "burned_die_id": self.burned_die_id,
            "burned_die_ids": list(self.burned_die_ids),
            "diagnostics_face": self.diagnostics_face,
            "purple_star_triggers": self.purple_star_triggers,
        }


@dataclass
class PipelineShiftRecord:
    """Phase 5 (CI/CD Pipeline Shift) result for one player."""

    hotfixed_ids: List[int] = field(default_factory=list)
    returned_to_scanned_ids: List[int] = field(default_factory=list)
    graduated_ids: List[int] = field(default_factory=list)
    triaged_ids: List[int] = field(default_factory=list)
    held_in_scanned: int = 0


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
    # v0.34: every player tied for first after all tiebreakers (RULES §5 shared victory). On the six-phase
    # path winner_id is None when the victory is shared; the legacy path keeps v0.33 winner_id.
    winner_ids: List[int] = field(default_factory=list)
    is_shared_victory: bool = False


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
    pending_version_advance: bool = False
    overflow_black_cubes_on_next_track: int = 0
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
    last_exited_cubes: Dict[CubeColor, int] = field(default_factory=dict)
    first_player_index: int = 0
    current_round: int = 1
    game_over: bool = False
    is_final_round: bool = False
    final_round_trigger_phase: Optional[int] = None  # v0.34.0: 2 or 4 (six-phase path only)
    end_reason: EndGameReason = EndGameReason.NONE
    singularity_triggered: bool = False
    contractor_supply: int = 12
    next_die_id: int = 1
    pending_next_phase_locks: Set[str] = field(default_factory=set)
    active_phase1_locks: Set[str] = field(default_factory=set)
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        self.tower = CubeTower(self.config)

    @property
    def active_version(self) -> VersionCard:
        return self.version_deck[self.current_version_index]

    @property
    def active_directive_code(self) -> str:
        return self.active_version.directive_code

    @property
    def corruption_track_capacity(self) -> int:
        if self.config.corruption_track_flat_capacity is not None:
            return self.config.corruption_track_flat_capacity
        return self.active_version.track_capacity

    def get_market_die_cost(self, color: DieColor) -> int:
        """Returns the dynamic cost of a Central Market die based on the active variant card."""
        if color in self.variant_cards:
            return self.variant_cards[color].cost
        # Fallback default costs if variant cards not registered:
        default_costs = {
            DieColor.RED: 5,
            DieColor.BLUE: 5,
            DieColor.GREEN: 5,
            DieColor.YELLOW: 6,
        }
        return default_costs.get(color, 4)


