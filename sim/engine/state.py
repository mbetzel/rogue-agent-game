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
    effective_company,
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
    upgrade_discount: int = 0
    excess_hardware_upgrades_requested: int = 0

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

    # --- v0.40.0 fields ---
    money_spent_regain: int = 0
    scanned_dice_purchased_this_turn: int = 0
    triage_milestones_claimed: List[str] = field(default_factory=list)

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
    market_share: Optional[int] = None
    market_share_max: Optional[int] = None
    market_share_min: Optional[int] = None
    market_share_start: Optional[int] = None
    market_share_peak: Optional[int] = None

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
        config: Optional[GameConfig] = None,
        **kwargs: Any,
    ) -> None:
        self.config = config
        # v0.35.0 research telemetry / ledger (INV-RT-RESEARCH-LEDGER-01)
        self.research_earned_total = 0
        self.research_earned_by_source: Dict[str, int] = {}
        self.research_lost_total = 0
        self.research_spent_tracks: Dict[str, int] = {}
        self.research_spent_patents = 0
        self.patent_secrets_gained = 0
        self.level_reached_round: Dict[str, Dict[int, int]] = {}
        self.breakthroughs: List[Any] = []  # List[research_tracks.BreakthroughRecord]
        self.l4_payouts: Dict[str, int] = {
            "defense_cash": 0, "triage_research": 0, "release_rerolls_used": 0, "patent_secrets": 0,
        }
        self.slush_fund_used_game = False
        self.triage_l3_upgrade_color: Optional[str] = None
        self.excess_hardware_upgrades_requested = 0
        # v0.36.0 Market Share (None under RedMode.RANSOM; initialised by GameEngine under MARKET_SHARE)
        self.market_share: Optional[int] = None
        self.market_share_max: Optional[int] = None
        self.market_share_min: Optional[int] = None
        self.market_share_start: Optional[int] = None
        self.market_share_peak: Optional[int] = None
        self.market_share_lost_red = 0  # actual decrease from Red (after floor clamp)
        self.market_share_red_overflow = 0  # unblocked Red beyond the floor (telemetry only)
        self.market_share_lost_poach = 0  # Customer Poaching taken from this player
        self.market_share_gained_poach = 0
        self.market_share_regained = 0  # +1 steps bought with research (Public Relations Track)
        self.market_share_gained_r2 = 0  # Ad Campaign
        self.research_spent_regain = 0
        self.regain_this_turn = 0  # reset at the start of each Operations Turn
        self.r2_actions_available = 0  # earned in Phase 3, spent/cleared in Phase 6
        self.r2_uses = 0
        self.comparison_money_gained = 0
        self.comparison_money_paid = 0
        self.comparison_shortfall_forgiven = 0
        # Red ledgers (both modes; telemetry only)
        self.red_incoming_total = 0  # effective Red attack after Baffle Echo / Aegis
        self.red_blocked_color_total = 0
        self.red_blocked_any_total = 0
        self.red_unblocked_total = 0
        # v0.37.0 Generic shield / contested-round telemetry (spec §4.4; telemetry only)
        self.any_shield_allocated_by_color: Dict[str, int] = {"red": 0, "blue": 0, "green": 0}
        self.contested_defense_rounds = 0
        self.contested_blue_left_open = 0
        self.contested_red_chosen = 0
        self.purchases_by_color: Dict[str, int] = {}  # Central Market purchases incl. Algorithmic Arbitrage
        # v0.38.0 candidate (spec v380 §3.2 / §11). Plain ints / dicts / lists so fast_clone copies them.
        self.glitched_shield_slots = 0
        self.slots_glitched_this_round = 0  # §14.3 glitched_slots_per_round_cap
        self.blocked_blue_this_round = 0
        self.slot_clear_used_this_phase5 = False
        self.secrets_by_source: Dict[str, int] = {}  # ledger only (gains positive, losses negative)
        self.secret_faces_rolled: Dict[str, int] = {}
        self.secret_faces_banked: Dict[str, int] = {}
        self.secret_yield_hist: Dict[str, Dict[str, int]] = {}
        self.secrets_lost_returned = 0
        self.slots_glitched_by_source: Dict[str, int] = {}
        self.slots_cleaned_by_die = 0
        self.slots_cleaned_by_face = 0
        self.slots_cleared_by_graduation = 0
        self.slots_cleaned_by_green_triage = 0  # Added for v0.38d Green banking triage
        self.max_glitched_slots = 0
        self.zero_capacity_rounds = 0
        self.market_share_gained_face = 0  # Red F1 / R1 (outside the Public Relations limit)
        self.company_color: Optional[str] = None
        self.colored_dice_owned_by_round: List[Dict[str, int]] = []
        # RSP-1 (spec §14.5.4 / §14.5.5). Plain ints / dicts so fast_clone copies them.
        self.processing_entry_counter = 0  # per-player Processing Box entry sequence (OLDEST_FIRST triage)
        self.red_secrets_banked = 0
        self.red_payout_places: Dict[str, int] = {}
        self.red_payout_secrets = 0
        self.red_processing_wait_rounds = 0  # stall diagnostic: sum of rounds a banked Red die sat pending
        self.red_processing_wait_count = 0
        # v0.39.1 / v0.40.0 telemetry (Phase 56)
        self.capital_injection_uses = 0
        self.logistics_bounty_triggers = 0
        self.money_by_source: Dict[str, int] = {}
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

        setup_company = effective_company(self.company, config)
        if setup_company is not None:
            self.defense_capacity = getattr(setup_company, "starting_defense_capacity", 2) if defense_capacity is None else defense_capacity
            self.triage_bandwidth = getattr(setup_company, "starting_triage_bandwidth", 2) if triage_bandwidth is None else triage_bandwidth
            self.release_bandwidth = getattr(setup_company, "starting_release_bandwidth", 4) if release_bandwidth is None else release_bandwidth
            init_triage = triage_level if triage_level is not None else (pipeline_level if pipeline_level is not None else getattr(setup_company, "starting_triage_level", 0))
            init_release = release_level if release_level is not None else (pipeline_level if pipeline_level is not None else getattr(setup_company, "starting_release_level", 0))
            self.triage_level = init_triage
            self.release_level = init_release
            self.defense_level = getattr(setup_company, "starting_defense_level", 0) if defense_level is None else defense_level
            self.patent_level = getattr(setup_company, "starting_patent_level", 0) if patent_level is None else patent_level
            self.upgrade_discount = getattr(setup_company, "upgrade_discount", 0) if upgrade_discount is None else upgrade_discount
        else:
            if config is not None and getattr(config, "is_v035_tracks", False):
                def_cap = config.track_capacity_by_level.get("DEFENSE", (2,))[0]
                tri_bw = config.track_capacity_by_level.get("TRIAGE", (2,))[0]
                rel_bw = config.track_capacity_by_level.get("RELEASE", (4,))[0]
            else:
                def_cap, tri_bw, rel_bw = 2, 2, 4
            self.defense_capacity = def_cap if defense_capacity is None else defense_capacity
            self.triage_bandwidth = tri_bw if triage_bandwidth is None else triage_bandwidth
            self.release_bandwidth = rel_bw if release_bandwidth is None else release_bandwidth
            init_triage = triage_level if triage_level is not None else (pipeline_level if pipeline_level is not None else 0)
            init_release = release_level if release_level is not None else (pipeline_level if pipeline_level is not None else 0)
            self.triage_level = init_triage
            self.release_level = init_release
            self.defense_level = 0 if defense_level is None else defense_level
            self.patent_level = 0 if patent_level is None else patent_level
            self.upgrade_discount = 0 if upgrade_discount is None else upgrade_discount

        self.money_spent_regain = 0
        self.scanned_dice_purchased_this_turn = 0
        self.triage_milestones_claimed = []

        self._has_emergency_hotfix = has_emergency_hotfix or (self.triage_level >= 2)
        self._has_passive_firewall = has_passive_firewall or (self.defense_level >= 2)
        self.starting_research = self.research_tokens

        self.ability_v1_status = ability_v1_status
        self.ability_v2_status = ability_v2_status
        self.ability_v3_status = ability_v3_status
        self.personal_purple_reserve = personal_purple_reserve
        self.purple_star_available = purple_star_available
        self.purple_star_count = purple_star_count

    # --- v0.36.0 Market Share (INV-MS-LEDGER-01) ---
    def init_market_share(self, start: int, max_share: Optional[int] = None) -> None:
        """Initializes Market Share, decoupling starting marker position from track ceiling.

        If max_share is None, defaults to start (preserving legacy test and fixture behavior).
        """
        self.market_share = self.market_share_min = self.market_share_start = self.market_share_peak = int(start)
        self.market_share_max = int(max_share) if max_share is not None else int(start)

    def change_market_share(self, delta: int, source: str) -> int:
        """Applies a Market Share change clamped to [0, max]; updates ledgers; returns the actual change.

        ``source`` is one of ``"red"``, ``"poach_lost"``, ``"poach_gained"``, ``"regain"``, ``"r2"``, ``"face"``.
        """
        if self.market_share is None:
            return 0
        before = self.market_share
        after = max(0, min(self.market_share_max, before + int(delta)))
        actual = after - before
        self.market_share = after
        if source == "red":
            self.market_share_lost_red += -actual
            self.market_share_red_overflow += max(0, -int(delta)) - (-actual)
        elif source == "poach_lost":
            self.market_share_lost_poach += -actual
        elif source == "poach_gained":
            self.market_share_gained_poach += actual
        elif source == "regain":
            self.market_share_regained += actual
        elif source == "r2":
            self.market_share_gained_r2 += actual
        elif source == "face":
            self.market_share_gained_face += actual
        else:
            raise ValueError(f"unknown Market Share source {source!r}")
        if self.market_share_min is None or after < self.market_share_min:
            self.market_share_min = after
        if self.market_share_peak is None or after > self.market_share_peak:
            self.market_share_peak = after
        return actual

    def gain_secrets(self, amount: int, source: str) -> None:
        """Corporate Secrets change with a ledger entry (telemetry only; behaviour = ``secrets += amount``)."""
        self.secrets += amount
        if amount:
            self.secrets_by_source[source] = self.secrets_by_source.get(source, 0) + amount

    def gain_money(self, amount: int, source: str = "other") -> None:
        """Cash gain with a ledger entry (telemetry only; behaviour = ``money += amount``)."""
        if amount <= 0:
            return
        self.money += amount
        self.money_by_source[source] = self.money_by_source.get(source, 0) + amount
        if source == "capital_injection":
            self.capital_injection_uses += 1

    @property
    def processing_box(self) -> List[Die]:
        """v0.38 name of the first Under Development box (the sim attribute stays ``glitched_dice``)."""
        return self.glitched_dice

    def record_purchase(self, color: Any) -> None:
        key = getattr(color, "value", color)
        self.purchases_by_color[key] = self.purchases_by_color.get(key, 0) + 1

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

    # --- v0.35.0 research-track dispatch ---
    @property
    def is_v035_tracks(self) -> bool:
        cfg = getattr(self, "config", None)
        return bool(cfg is not None and getattr(cfg, "is_v035_tracks", False))

    @property
    def _level2_perks_enabled(self) -> bool:
        cfg = getattr(self, "config", None)
        return True if cfg is None else bool(getattr(cfg, "level2_perks_enabled", True))

    @property
    def has_emergency_hotfix(self) -> bool:
        """Triage Level 2 perk (v0.34 only; always False under v0.35, INV-RT-NO-L2-PERKS-01)."""
        return bool(self._has_emergency_hotfix) and self._level2_perks_enabled

    @has_emergency_hotfix.setter
    def has_emergency_hotfix(self, value: bool) -> None:
        self._has_emergency_hotfix = bool(value)

    @property
    def has_passive_firewall(self) -> bool:
        """Defense Level 2 perk (v0.34 only; always False under v0.35, INV-RT-NO-L2-PERKS-01)."""
        return bool(self._has_passive_firewall) and self._level2_perks_enabled

    @has_passive_firewall.setter
    def has_passive_firewall(self, value: bool) -> None:
        self._has_passive_firewall = bool(value)

    def gain_research(self, amount: int, source: str = "other") -> None:
        """Every research gain goes through here (INV-RT-RESEARCH-LEDGER-01)."""
        if amount <= 0:
            return
        self.research_tokens += amount
        self.research_earned_total += amount
        self.research_earned_by_source[source] = self.research_earned_by_source.get(source, 0) + amount

    def lose_research(self, amount: int, source: str = "corruption") -> int:
        """Research removed by an effect (e.g. Corruption Track). Returns the amount actually lost."""
        lost = max(0, min(int(amount), self.research_tokens))
        self.research_tokens -= lost
        self.research_lost_total += lost
        return lost

    def get_track_upgrade_cost(self, track: str) -> Optional[int]:
        """Research cost of the next step of ``track`` (None at max level) (INV-UPGRADE-TRACK-01 / INV-RT-COST-01)."""
        if self.is_v035_tracks:
            from sim.engine import research_tracks

            return research_tracks.step_cost(self.config, self, track)
        return self._v034_get_track_upgrade_cost(track)

    def upgrade_track(self, track: str, round_number: Optional[int] = None) -> bool:
        """Pays and raises ``track`` one level. Under v0.35 it does NOT resolve the Breakthrough
        (the Phase 6 caller does, see ``research_tracks.upgrade_and_resolve``)."""
        t = track.upper().strip()
        if not self.is_v035_tracks:
            before = self.research_tokens
            ok = self._v034_upgrade_track(t)
            if ok:
                self.research_spent_tracks[t] = self.research_spent_tracks.get(t, 0) + (before - self.research_tokens)
            return ok
        from sim.engine import research_tracks

        cost = research_tracks.step_cost(self.config, self, t)
        if cost is None or self.research_tokens < cost:
            return False
        self.research_tokens -= cost
        self.research_spent_tracks[t] = self.research_spent_tracks.get(t, 0) + cost
        new_level = research_tracks.level_of(self, t) + 1
        rnd = round_number if round_number is not None else getattr(self, "_current_round", 0)
        research_tracks.apply_level(self.config, self, t, new_level, rnd)
        return True

    def get_patent_cost(self) -> int:
        """Research cost of one Cryptographic Patent filing at the current Patents level."""
        if self.is_v035_tracks:
            from sim.engine import research_tracks

            return research_tracks.patent_rate(self.config, self)[0]
        return self._v034_get_patent_cost()

    def get_patent_gain(self) -> int:
        """Corporate Secrets gained by one filing at the current Patents level."""
        if self.is_v035_tracks:
            from sim.engine import research_tracks

            return research_tracks.patent_rate(self.config, self)[1]
        return 1

    def file_patent(self) -> bool:
        """Files one Cryptographic Patent (INV-PATENT-CONV-01 / INV-RT-PATENT-RATE-01).

        Under the Public Relations Track (``patents_mode=SHARE_REGAIN``) Patent Filing does not exist:
        returns False without changing state (INV-MS-NO-PATENT-01).
        """
        cfg = getattr(self, "config", None)
        if cfg is not None and getattr(cfg, "is_share_regain", False):
            return False
        if not self.is_v035_tracks:
            cost = self._v034_get_patent_cost()
            ok = self._v034_file_patent()
            if ok:
                self.research_spent_patents += cost
                self.patent_secrets_gained += 1
            return ok
        cost, gain = self.get_patent_cost(), self.get_patent_gain()
        if self.research_tokens < cost:
            return False
        self.research_tokens -= cost
        self.secrets += gain  # uncapped
        self.research_spent_patents += cost
        self.patent_secrets_gained += gain
        if self.patent_level >= 4:
            self.l4_payouts["patent_secrets"] = self.l4_payouts.get("patent_secrets", 0) + gain
        return True

    def is_slush_fund_available(self, active_ver: Optional[str] = None) -> bool:
        """DTO Slush Fund: once per version (v0.34) or once per game (v0.35, INV-RT-SLUSH-ONCE-01)."""
        cfg = getattr(self, "config", None)
        if cfg is not None and getattr(cfg, "slush_fund_once_per_game", False) and self.slush_fund_used_game:
            return False
        return self.is_ability_available(active_ver)

    def _v034_get_track_upgrade_cost(self, track: str) -> Optional[int]:
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

    def _v034_upgrade_track(self, track: str) -> bool:
        """Upgrades the specified terminal track, expanding hardware capabilities (INV-UPGRADE-TRACK-01)."""
        t = track.upper().strip()
        cost = self._v034_get_track_upgrade_cost(t)
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
                self._has_emergency_hotfix = True
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
                self._has_passive_firewall = True
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
                self._has_emergency_hotfix = True
        return True

    def _v034_get_patent_cost(self) -> int:
        """Returns research token cost to file a Cryptographic Patent for +1 Corporate Secret."""
        if self.patent_level == 0:
            return 4
        elif self.patent_level == 1:
            return 3
        else:
            return 2

    def _v034_file_patent(self) -> bool:
        """Files a Cryptographic Patent: spends research tokens to gain +1 Corporate Secret (INV-PATENT-CONV-01)."""
        cost = self._v034_get_patent_cost()
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
    def _normalize_version_key(v: Any) -> int:
        raw = getattr(v, "version_str", v)
        s = str(raw).strip().lower()
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
    # --- v0.35.0 research telemetry ---
    research_gained_by_player: Dict[int, int] = field(default_factory=dict)
    track_upgrades_by_player: Dict[int, List[Tuple[str, int]]] = field(default_factory=dict)
    breakthroughs_by_player: Dict[int, List[Dict[str, Any]]] = field(default_factory=dict)
    rejected_purple_purchases_by_player: Dict[int, int] = field(default_factory=dict)
    excess_hardware_upgrades_by_player: Dict[int, int] = field(default_factory=dict)
    # --- v0.36.0 Market Share telemetry (empty / None under RANSOM except red_by_player, purchases_by_player) ---
    market_share_after_p4: Dict[int, Optional[int]] = field(default_factory=dict)
    market_share_end_of_round: Dict[int, Optional[int]] = field(default_factory=dict)
    red_by_player: Dict[int, Dict[str, int]] = field(default_factory=dict)
    regain_by_player: Dict[int, Dict[str, int]] = field(default_factory=dict)
    r2_by_player: Dict[int, int] = field(default_factory=dict)
    r3_events: List[Dict[str, Any]] = field(default_factory=list)
    version_comparisons: List[Dict[str, Any]] = field(default_factory=list)
    purchases_by_player: Dict[int, Dict[str, int]] = field(default_factory=dict)
    end_triggers_this_round: List[str] = field(default_factory=list)
    green_cubes_clamped_per_round: int = 0


@dataclass
class VersionComparisonRecord:
    """v0.36.0 Market Share comparison when a non-last Version's final space is covered (Phase 2)."""

    version: str  # completed version: "v1.0" | "v2.0"
    round_number: int
    payout: int
    during_spillover: bool
    eligible_pids: List[int] = field(default_factory=list)
    shares: Dict[int, int] = field(default_factory=dict)
    money_before: Dict[int, int] = field(default_factory=dict)
    top_pids: List[int] = field(default_factory=list)
    bottom_pids: List[int] = field(default_factory=list)
    gains: Dict[int, int] = field(default_factory=dict)  # bank -> player
    paid: Dict[int, int] = field(default_factory=dict)  # player -> bank
    forgiven: Dict[int, int] = field(default_factory=dict)
    all_tied: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "round_number": self.round_number,
            "payout": self.payout,
            "during_spillover": self.during_spillover,
            "eligible_pids": list(self.eligible_pids),
            "shares": dict(self.shares),
            "money_before": dict(self.money_before),
            "top_pids": list(self.top_pids),
            "bottom_pids": list(self.bottom_pids),
            "gains": dict(self.gains),
            "paid": dict(self.paid),
            "forgiven": dict(self.forgiven),
            "all_tied": self.all_tied,
        }


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
    version_comparisons: List[VersionComparisonRecord] = field(default_factory=list)  # v0.36.0


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
    protocol_research: int = 0
    capital_injection_used: bool = False
    capital_injection_cash: int = 0

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
            "capital_injection_used": self.capital_injection_used,
            "capital_injection_cash": self.capital_injection_cash,
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
    # --- v0.36.0 telemetry (INV-MS-*) ---
    end_triggers: List[str] = field(default_factory=list)
    market_collapse_pids: List[int] = field(default_factory=list)
    market_collapse_round: Optional[int] = None
    version_comparisons: List[Dict[str, Any]] = field(default_factory=list)
    tiebreak_decided_by: Optional[str] = None
    setup: Dict[str, Any] = field(default_factory=dict)
    collapse_trigger_pids_were_secret_leaders: List[bool] = field(default_factory=list)
    market_collapse_context: Dict[str, Any] = field(default_factory=dict)
    double_version_fill_events: int = 0
    # --- v0.37.0 Market Leader Bonus telemetry (INV-MLB-*) ---
    market_leader_bonus_awarded: bool = False  # bonus enabled and not a Total Wipeout
    market_leader_bonus_schedule: List[int] = field(default_factory=list)  # the padded schedule used
    pre_bonus_winner_ids: List[int] = field(default_factory=list)
    market_leader_bonus_changed_winner: bool = False
    market_leader_bonus_tied_paid_place: bool = False
    # --- RSP-1 Red Secret payout telemetry (spec §14.5.5); filled only when an RSP-1 lever is on ---
    red_secret_payouts: List[Dict[str, Any]] = field(default_factory=list)
    red_secret_payouts_fired: int = 0
    rounds_with_multi_red_banks: int = 0
    red_banks_by_round: List[int] = field(default_factory=list)
    red_secret_payout_end_fired: bool = False
    red_secret_payout_end_awards: Dict[int, int] = field(default_factory=dict)
    red_pending_at_end: int = 0
    other_pending_at_end: int = 0


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
    # Extra queued Version Switches beyond the first, when spillover fills a whole non-final track in the
    # same compile (e.g. v1.0 -> v2.0 -> v3.0). The pending target is current + 1 + this value, and
    # overflow_black_cubes_on_next_track counts cubes on that target's track.
    pending_extra_version_advances: int = 0
    # Telemetry: compiles in which spillover filled an entire non-final Version track.
    multi_version_spill_events: int = 0
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
    # --- v0.36.0 Market Share state ---
    version_comparisons: List[VersionComparisonRecord] = field(default_factory=list)
    version_comparisons_done: Set[str] = field(default_factory=set)  # once-guard
    market_collapse_triggered: bool = False
    market_collapse_round: Optional[int] = None
    market_collapse_pids: List[int] = field(default_factory=list)
    market_collapse_secret_leaders: List[bool] = field(default_factory=list)  # kamikaze watch
    market_collapse_context: Dict[str, Any] = field(default_factory=dict)  # survivors / strict leader at Collapse
    end_triggers: List[str] = field(default_factory=list)  # ordered, e.g. ["patient_zero", "market_collapse"]
    r3_events: List[Dict[str, Any]] = field(default_factory=list)
    double_version_fill_events: int = 0
    first_player_index_start: int = 0
    # Market Share of every player at the start of this round's Phase 4 (bot projections; INV-MS-RNG-01 safe)
    phase4_market_share_start: Dict[int, Optional[int]] = field(default_factory=dict)
    phase4_snapshot_round: Optional[int] = None
    _pending_poaches: List[Tuple[int, int]] = field(default_factory=list)  # (player_id, die_id), Phase 3
    # --- RSP-1 Red Secret payout (spec §14.5.3 / §14.5.5). Plain values: fast_clone copies them. ---
    red_secret_banked_this_round: bool = False  # reset at Phase 1 entry
    red_secrets_banked_this_round: int = 0
    red_bankers_this_round: List[int] = field(default_factory=list)
    red_secret_payouts: List[Dict[str, Any]] = field(default_factory=list)  # one record per round fired
    red_secret_payouts_fired: int = 0
    red_banks_by_round: List[int] = field(default_factory=list)  # index = round - 1

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

    @property
    def exit_tray(self) -> Dict[CubeColor, int]:
        return self.last_exited_cubes

    def total_green_cubes_in_circulation(self) -> int:
        staged = self.staging_cup.get(CubeColor.GREEN, 0) if isinstance(self.staging_cup, dict) else self.staging_cup.count(CubeColor.GREEN)
        exited = self.last_exited_cubes.get(CubeColor.GREEN, 0) if isinstance(self.last_exited_cubes, dict) else self.last_exited_cubes.count(CubeColor.GREEN)
        if hasattr(self.tower, "stuck_cubes") and isinstance(self.tower.stuck_cubes, dict):
            stuck = self.tower.stuck_cubes.get(CubeColor.GREEN, 0)
        elif hasattr(self.tower, "count"):
            stuck = self.tower.count(CubeColor.GREEN)
        elif hasattr(self.tower, "get_stuck_copy"):
            stuck = self.tower.get_stuck_copy().get(CubeColor.GREEN, 0)
        else:
            stuck = 0
        return staged + exited + stuck

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


