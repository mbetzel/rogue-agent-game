"""Entities: Dice, Faces, Variant Cards, and Version Cards for Rogue Agent."""

from __future__ import annotations

import random
import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor


class ArchetypeCode(str, Enum):
    """Enumeration of the 6 consultancy archetypes per RULES.md Section 6D."""

    ACOUSTIC = "ACOUSTIC"
    PHREAKER = "PHREAKER"
    PRODIGY = "PRODIGY"
    SPOOK = "SPOOK"
    CIPHER = "CIPHER"
    OPERATOR = "OPERATOR"


class CompanyCode(str, Enum):
    """Enumeration of the 6 Client Companies providing Institutional Overrides."""

    MERIDIAN = "MERIDIAN"
    OMNIDYNE = "OMNIDYNE"
    AEGIS = "AEGIS"
    DTO = "DTO"
    HELIX = "HELIX"
    PROMETHEUS = "PROMETHEUS"


class WhiteHatCode(str, Enum):
    """Enumeration of the 6 White Hat Operatives providing Signature Protocols."""

    OPERATOR = "OPERATOR"
    PHREAKER = "PHREAKER"
    ACOUSTIC = "ACOUSTIC"
    SPOOK = "SPOOK"
    PRODIGY = "PRODIGY"
    CIPHER = "CIPHER"


class AbilityStatus(str, Enum):
    """Lifecycle status of once-per-version archetype special abilities."""

    LOCKED = "LOCKED"
    AVAILABLE = "AVAILABLE"
    USED = "USED"
    FORFEITED = "FORFEITED"


class TargetCriterion(str, Enum):
    """Target selection criteria for Phase 2 Corruption Track spaces."""
    ALL = "ALL"                             # Table-wide hit (legacy baseline)
    MOST_MONEY = "MOST_MONEY"               # Player(s) with highest cash ($)
    MOST_RESEARCH = "MOST_RESEARCH"         # Player(s) with highest Research Tokens (🔬)
    MOST_MARKET_SHARE = "MOST_MARKET_SHARE" # Player(s) with highest Market Share (MS)
    FEWEST_GLITCHED = "FEWEST_GLITCHED"     # Player(s) with lowest glitched shield slots
    MOST_COLORED_DICE = "MOST_COLORED_DICE" # Player(s) with most colored dice
    MOST_SECRETS = "MOST_SECRETS"           # Player(s) with highest Corporate Secrets


class TargetScope(str, Enum):
    """Scope of target selection for Phase 2 Corruption Track spaces."""
    ALL = "ALL"
    TARGETED = "TARGETED"


class TransferType(str, Enum):
    """Robin Hood transfer types for Phase 2 Corruption Track spaces."""
    NONE = "NONE"
    LEAST_MS_TAKES_CASH = "LEAST_MS_TAKES_CASH"                     # Least MS takes cash from Most MS
    LEAST_RESEARCH_TAKES_RESEARCH = "LEAST_RESEARCH_TAKES_RESEARCH" # Least 🔬 takes 🔬 from Most 🔬


@dataclass(frozen=True)
class ArchetypeCard:
    """Represents a consultancy archetype card with once-per-version ability."""

    code: ArchetypeCode
    name: str
    timing_window: str
    ability_name: str
    description: str


@dataclass(frozen=True)
class Company:
    """Represents a Client Company card contracting the terminal."""

    code: CompanyCode
    name: str
    sector: str
    override_name: str
    timing_window: str
    description: str
    flavor: str
    starting_defense_capacity: int = 2
    starting_triage_bandwidth: int = 2
    starting_release_bandwidth: int = 4
    starting_triage_level: int = 0
    starting_release_level: int = 0
    starting_defense_level: int = 0
    starting_patent_level: int = 0
    starting_cash_bonus: int = 0
    starting_research_bonus: int = 0
    starting_secrets_bonus: int = 0
    upgrade_discount: int = 0

    @property
    def starting_pipeline_level(self) -> int:
        return self.starting_triage_level


@dataclass(frozen=True)
class WhiteHat:
    """Represents a White Hat Operative dossier card assigned to the terminal."""

    code: WhiteHatCode
    name: str
    role: str
    protocol_name: str
    timing_window: str
    description: str
    flavor: str
    reserve_cost: int = 5  # [v0.26.0 Baseline: Personal Reserve Purple die cost (INV-RES-COST-01)]


@dataclass(frozen=True)
class Face:
    """Represents a single face on a d6 die."""

    name: str
    block_amount: int = 0
    shield_color: Optional[ShieldColor] = None  # None for non-shield faces
    money: int = 0
    patches: int = 0
    secrets: int = 0
    is_star: bool = False
    star_code: Optional[str] = None  # e.g. "R1", "B3", etc.
    is_glitch: bool = False
    is_choice: bool = False
    choices: Tuple[Face, ...] = ()
    # v0.38.0 candidate (spec v380 §4.1). ``secrets_pending`` marks the Secret face (banked on Processing Box exit;
    # not ``secrets``, which is Y3's immediate Phase 3 Secret). Defaults keep every v0.37 face unchanged.
    secrets_pending: bool = False
    market_share: int = 0
    clean_slots: int = 0

    @property
    def is_secret_face(self) -> bool:
        return self.secrets_pending

    @property
    def is_shield(self) -> bool:
        return self.block_amount > 0 and self.shield_color is not None and not self.is_glitch

    @property
    def has_cash_option(self) -> bool:
        if self.is_choice:
            return any(c.has_cash_option for c in self.choices)
        return self.money > 0 and not self.is_glitch

    @property
    def has_shield_option(self) -> bool:
        if self.is_choice:
            return any(c.has_shield_option for c in self.choices)
        return self.is_shield

    @property
    def has_patch_option(self) -> bool:
        if self.is_choice:
            return any(c.has_patch_option for c in self.choices)
        return self.patches > 0 and not self.is_glitch


@dataclass
class Die:
    """Represents an individual software module die."""

    die_id: int
    color: DieColor
    cost: int
    vp: int = 0  # Deprecated in v0.19.0: Software modules have 0 VP (Corporate Secrets determine victory)
    faces: List[Face] = field(default_factory=list)
    current_face: Optional[Face] = None
    variant_code: Optional[str] = None
    is_locked: bool = False
    chosen_choice_index: Optional[int] = None
    production_role: Optional[Any] = None
    secret_pending: bool = False  # v0.38: in the Processing Box from a Secret face (atomic: fast_clone fast path)
    processing_entry_seq: int = 0  # RSP-1: per-player Processing Box entry order (OLDEST_FIRST triage)
    processing_entry_round: int = 0  # RSP-1: round the die entered the Processing Box (stall telemetry)

    def roll(self, rng: random.Random) -> Face:
        """Roll the die and record the rolled face."""
        self.chosen_choice_index = None
        self.current_face = rng.choice(self.faces)
        return self.current_face

    @property
    def effective_face(self) -> Optional[Face]:
        if self.current_face is None:
            return None
        if self.current_face.is_choice:
            if (
                self.chosen_choice_index is not None
                and 0 <= self.chosen_choice_index < len(self.current_face.choices)
            ):
                return self.current_face.choices[self.chosen_choice_index]
            return self.current_face
        return self.current_face


@dataclass(frozen=True)
class VariantCard:
    """Defines the Special (★) face behavior for a colored die type."""

    code: str  # e.g., "R1", "B3"
    name: str
    die_color: DieColor
    description: str
    star_face: Face
    cost: int = 5  # [v0.26.0 Baseline: Dynamic market cost per variant card (INV-VAR-COST-01)]
    display_code: Optional[str] = None  # printed label when it differs from the internal code (e.g. R2_MKT -> "R2")

    @property
    def printed_code(self) -> str:
        return self.display_code or self.code


@dataclass(frozen=True)
class CorruptionSpace:
    """Represents a single space on a Version Corruption Track (RULES.md Section 6C)."""

    index: int  # 1-indexed space number on this version card (1..4, 1..5, or 1..6)
    label: str  # Human-readable summary
    add_cubes: Dict[CubeColor, int] = field(default_factory=dict)
    lose_money: int = 0
    lose_patches: int = 0
    demote_dice: int = 0
    return_colored_dice: int = 0
    lose_secrets: int = 0
    lose_market_share: int = 0                      # v0.41.0: Direct Market Share loss
    next_phase_lock: Optional[str] = None
    is_upgrade: bool = False
    is_singularity: bool = False

    # Player-Specific Targeting:
    target_criterion: Optional[TargetCriterion] = None
    target_money_criterion: Optional[TargetCriterion] = None
    target_patches_criterion: Optional[TargetCriterion] = None
    target_demote_criterion: Optional[TargetCriterion] = None
    target_return_colored_criterion: Optional[TargetCriterion] = None
    target_secrets_criterion: Optional[TargetCriterion] = None
    target_market_share_criterion: Optional[TargetCriterion] = None
    target_scope: Optional[TargetScope] = None

    # Robin Hood Transfers:
    transfer_type: TransferType = TransferType.NONE
    transfer_amount: int = 0


@dataclass(frozen=True)
class VersionCard:
    """Represents a Rogue Agent roadmap version card (v1.0, v2.0, or v3.0)."""

    version_str: str  # "v1.0", "v2.0", "v3.0"
    name: str
    staging_payload: Dict[CubeColor, int]
    directive_description: str
    directive_code: str  # SCRIPT_KIDDIE, DATA_SCRAPER, RAAS, POLYMORPHIC_WORM, ZERO_DAY_OVERRIDE, CORRUPTED_KERNEL
    staging_payload_2p: Optional[Dict[CubeColor, int]] = None
    corruption_track: Tuple[CorruptionSpace, ...] = ()
    starting_cash_bonus: int = 0

    @property
    def track_capacity(self) -> int:
        return len(self.corruption_track) if self.corruption_track else (
            4 if self.version_str == "v1.0" else (5 if self.version_str == "v2.0" else 6)
        )

    def get_staging_payload(self, num_players: int = 4) -> Dict[CubeColor, int]:
        """Returns the version's staging payload cubes scaled for player count (2P vs 3P/4P)."""
        if num_players == 2 and self.staging_payload_2p is not None:
            return dict(self.staging_payload_2p)
        return dict(self.staging_payload)


# =====================================================================
# Factory Functions & Appendix Definitions
# =====================================================================

def get_marketing_red_variant_cards() -> List[VariantCard]:
    """v0.36.0 Red (Marketing) ★ Variant Cards: Brand Protection, Ad Campaign, Customer Poaching.

    Internal codes are distinct (``R2_MKT`` / ``R3_MKT``) so that no v0.35 star-code branch can fire a retired
    effect; ``display_code`` keeps the printed R1/R2/R3 labels.
    """
    return [
        VariantCard(
            code="R1",
            name="Brand Protection",
            die_color=DieColor.RED,
            description="Block 1 Red + gain +$2.",
            cost=5,
            star_face=Face(
                name="R1: Brand Protection",
                block_amount=1,
                shield_color=ShieldColor.RED,
                money=2,
                is_star=True,
                star_code="R1",
            ),
        ),
        VariantCard(
            code="R2_MKT",
            name="Ad Campaign",
            die_color=DieColor.RED,
            description="No Income. If this die is In Production in Phase 3, you may pay $2 in Phase 6: Operations to gain +1 Market Share (does not count toward the Public Relations Track limit).",
            cost=4,
            star_face=Face(
                name="R2: Ad Campaign",
                block_amount=0,
                money=0,  # Paid action latched in Phase 3, spent in Phase 6
                is_star=True,
                star_code="R2_MKT",
            ),
            display_code="R2",
        ),
        VariantCard(
            code="R3_MKT",
            name="Customer Poaching",
            die_color=DieColor.RED,
            description="In Phase 3 (Income), take 1 Market Share from the rival with the most Market Share (your own Market Share cannot exceed its maximum).",
            cost=5,
            star_face=Face(
                name="R3: Customer Poaching",
                block_amount=0,
                money=0,  # Resolved after all players' Income (market_share.resolve_poaches)
                is_star=True,
                star_code="R3_MKT",
            ),
            display_code="R3",
        ),
    ]


_MARKETING_RED_CODE_MAP = {"R1": "R1", "R2": "R2_MKT", "R3": "R3_MKT"}


def resolve_variant_cards(
    variant_cards: Dict[DieColor, VariantCard], red_variant_set: Any = "V035"
) -> Dict[DieColor, VariantCard]:
    """Maps a drawn Red card onto the configured Red ★ set (INV-MS-RNG-02).

    Under ``MARKETING`` a V035 Red card is replaced by code (R1 -> R1 renamed, R2 -> R2_MKT, R3 -> R3_MKT), so
    setup draws made with ``get_random_setup(rng)`` stay identical (seed-paired) across ``red_variant_set`` cells.
    Under ``V035`` the mapping is returned unchanged (same object).
    """
    rv = getattr(red_variant_set, "value", red_variant_set)
    if rv != "MARKETING":
        return variant_cards
    red = variant_cards.get(DieColor.RED)
    if red is None:
        return variant_cards
    mkt = {c.code: c for c in get_marketing_red_variant_cards()}
    target = _MARKETING_RED_CODE_MAP.get(red.code, red.code)
    if target not in mkt:
        return variant_cards
    out = dict(variant_cards)
    out[DieColor.RED] = mkt[target]
    return out


def get_all_variant_cards(red_variant_set: Any = "V035") -> Dict[str, VariantCard]:
    """Returns a dictionary of all 15 prototype Variant Cards (R1-R3, B1-B3, G1-G3, Y1-Y3, P1-P3).

    ``red_variant_set="MARKETING"`` replaces the Red trio with R1 / R2_MKT / R3_MKT (same list order).
    """
    if getattr(red_variant_set, "value", red_variant_set) == "MARKETING":
        base = get_all_variant_cards("V035")
        out: Dict[str, VariantCard] = {}
        for c in get_marketing_red_variant_cards():
            out[c.code] = c
        for code, c in base.items():
            if c.die_color != DieColor.RED:
                out[code] = c
        return out
    cards = [
        # Red ★ Variants
        VariantCard(
            code="R1",
            name="Ransom Insurance",
            die_color=DieColor.RED,
            description="Block 1 Red + gain +$2.",
            cost=5,
            star_face=Face(
                name="R1: Ransom Insurance",
                block_amount=1,
                shield_color=ShieldColor.RED,
                money=2,
                is_star=True,
                star_code="R1",
            ),
        ),
        VariantCard(
            code="R2",
            name="Threat Bounty",
            die_color=DieColor.RED,
            description="Block 2 Red; if you take 0 unblocked Red damage in Phase 4 this round, gain +$2 (this die must still be In Production in Phase 4).",
            cost=5,
            star_face=Face(
                name="R2: Threat Bounty",
                block_amount=2,
                shield_color=ShieldColor.RED,
                money=0,  # Bonus handled conditionally in Phase 4: Attack Resolution
                is_star=True,
                star_code="R2",
            ),
        ),
        VariantCard(
            code="R3",
            name="Short Squeeze",
            die_color=DieColor.RED,
            description="Gain +$3 in Phase 3 (plus +$1 in Phase 4 if 3+ Red cubes exit the tower this round and this die is still In Production).",
            cost=4,
            star_face=Face(
                name="R3: Short Squeeze",
                block_amount=0,
                money=3,  # Base $3 in P1, +$1 bonus checked in Phase 4 if exited Red >= 3
                is_star=True,
                star_code="R3",
            ),
        ),
        # Blue ★ Variants
        VariantCard(
            code="B1",
            name="Honeypot Telemetry",
            die_color=DieColor.BLUE,
            description="Block 2 Blue; if 1+ Blue cubes exit the tower and you take 0 Blue damage in Phase 4, gain +$2 (this die must still be In Production in Phase 4).",
            cost=5,
            star_face=Face(
                name="B1: Honeypot Telemetry",
                block_amount=2,
                shield_color=ShieldColor.BLUE,
                money=0,  # Bonus (+$2) handled conditionally in Phase 4 (INV-B1-BOUNTY-01)
                is_star=True,
                star_code="B1",
            ),
        ),
        VariantCard(
            code="B2",
            name="Deep R&D Vault",
            die_color=DieColor.BLUE,
            description="Block 1 Blue, OR pay $4 during Phase 6: Operations to gain +1 Corporate Secret.",
            cost=6,
            star_face=Face(
                name="B2: Deep R&D Vault",
                block_amount=1,
                shield_color=ShieldColor.BLUE,
                is_star=True,
                star_code="B2",
            ),
        ),
        VariantCard(
            code="B3",
            name="Air-Gapped Backup",
            die_color=DieColor.BLUE,
            description="Block 1 Blue; in Phase 3: Income, move 1 die from your Glitched Box to your Scanned Box.",
            cost=4,
            star_face=Face(
                name="B3: Air-Gapped Backup",
                block_amount=1,
                shield_color=ShieldColor.BLUE,
                is_star=True,
                star_code="B3",
            ),
        ),
        # Green ★ Variants
        VariantCard(
            code="G1",
            name="Self-Healing Kernel",
            die_color=DieColor.GREEN,
            description="Block 2 Green + gain +1 🔬.",
            cost=5,
            star_face=Face(
                name="G1: Self-Healing Kernel",
                block_amount=2,
                shield_color=ShieldColor.GREEN,
                patches=1,
                is_star=True,
                star_code="G1",
            ),
        ),
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
        ),
        VariantCard(
            code="G3",
            name="Live Reboot",
            die_color=DieColor.GREEN,
            description="Gain +2 🔬 + +$1.",
            cost=4,
            star_face=Face(
                name="G3: Live Reboot",
                block_amount=0,
                patches=2,
                money=1,
                is_star=True,
                star_code="G3",
            ),
        ),
        # Yellow ★ Variants
        VariantCard(
            code="Y1",
            name="Algorithmic Trading",
            die_color=DieColor.YELLOW,
            description="Gain +$4, OR pay $2 in Phase 6: Operations to gain +1 Corporate Secret.",
            cost=6,
            star_face=Face(
                name="Y1: Algorithmic Trading",
                block_amount=0,
                money=4,
                is_star=True,
                star_code="Y1",
            ),
        ),
        VariantCard(
            code="Y2",
            name="Cloud Monopoly",
            die_color=DieColor.YELLOW,
            description="Gain +$2, plus +$1 per different colored module die owned (max +$5).",
            cost=5,
            star_face=Face(
                name="Y2: Cloud Monopoly",
                block_amount=0,
                money=2,  # Base $2, scaled dynamically in engine
                is_star=True,
                star_code="Y2",
            ),
        ),
        VariantCard(
            code="Y3",
            name="Proprietary Training",
            die_color=DieColor.YELLOW,
            description="Gain +1 Corporate Secret, then move this die to Under Development (Glitched).",
            cost=5,
            star_face=Face(
                name="Y3: Proprietary Training",
                block_amount=0,
                secrets=1,
                is_star=True,
                star_code="Y3",
            ),
        ),
        # Purple ★ Variants
        VariantCard(
            code="P1",
            name="Zero-Day Injection",
            die_color=DieColor.PURPLE,
            description="Gain +$2; in Phase 6: Operations you may add 1 Attack Cube (Red/Blue/Green) to the Staging Cup.",
            cost=5,
            star_face=Face(
                name="P1: Zero-Day Injection",
                block_amount=0,
                money=2,
                is_star=True,
                star_code="P1",
            ),
        ),
        VariantCard(
            code="P2",
            name="Chaos Profiteer",
            die_color=DieColor.PURPLE,
            description="Gain +$1 now, plus +$2 per Black Cube that exits the tower in Phase 2.",
            cost=5,
            star_face=Face(
                name="P2: Chaos Profiteer",
                block_amount=0,
                money=1,
                is_star=True,
                star_code="P2",
            ),
        ),
        VariantCard(
            code="P3",
            name="Packet Deflection",
            die_color=DieColor.PURPLE,
            description="Block 2 of any single color; in Phase 6: Operations you may pay $1 to add 1 cube of that color from the supply to the Staging Cup.",
            cost=5,
            star_face=Face(
                name="P3: Packet Deflection",
                block_amount=2,
                shield_color=ShieldColor.ANY,
                is_star=True,
                star_code="P3",
            ),
        ),
    ]
    return {card.code: card for card in cards}


def get_default_variant_cards() -> Dict[DieColor, VariantCard]:
    """Returns the default baseline variant card for central market dice (Red, Blue, Green, Yellow)."""
    all_cards = get_all_variant_cards()
    return {
        DieColor.RED: all_cards["R1"],
        DieColor.BLUE: all_cards["B1"],
        DieColor.GREEN: all_cards["G1"],
        DieColor.YELLOW: all_cards["Y1"],
    }


def get_random_variant_cards(rng: random.Random) -> Dict[DieColor, VariantCard]:
    """Randomly selects 1 Variant Card per central market colored die (Red, Blue, Green, Yellow)."""
    all_variants = list(get_all_variant_cards().values())
    chosen: Dict[DieColor, VariantCard] = {}
    for color in [
        DieColor.RED,
        DieColor.BLUE,
        DieColor.GREEN,
        DieColor.YELLOW,
    ]:
        matching = [v for v in all_variants if v.die_color == color]
        chosen[color] = rng.choice(matching)
    return chosen


def _get_legacy_version_cards(is_aggressive: bool = False) -> List[VersionCard]:
    """Returns legacy pre-v0.41.0 Version cards with uniform table-wide hazards (INV-TARGET-08)."""
    if is_aggressive:
        return [
            VersionCard(
                version_str="v1.0",
                name="Script Kiddie",
                staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
                directive_description="None.",
                directive_code="SCRIPT_KIDDIE",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 1R", add_cubes={CubeColor.RED: 1}),
                    CorruptionSpace(index=2, label="All lose $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Glitch 1 die", demote_dice=1),
                    CorruptionSpace(index=4, label="Upgrade: Lose 1 🔬", lose_patches=1, is_upgrade=True),
                ),
            ),
            VersionCard(
                version_str="v1.0",
                name="Data Scraper",
                staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2},
                directive_description="Players start with +$1 extra Money.",
                directive_code="DATA_SCRAPER",
                starting_cash_bonus=1,
                corruption_track=(
                    CorruptionSpace(index=1, label="Lose 2 🔬", lose_patches=2),
                    CorruptionSpace(index=2, label="Lose $2 + Add 1K", lose_money=2, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 1G", add_cubes={CubeColor.GREEN: 1}),
                    CorruptionSpace(index=4, label="Upgrade: Glitch 2 dice", demote_dice=2, is_upgrade=True),
                ),
            ),
            VersionCard(
                version_str="v2.0",
                name="Ransomware-as-a-Service",
                staging_payload={},
                directive_description="None.",
                directive_code="RAAS",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="All lose $2", lose_money=2),
                    CorruptionSpace(index=2, label="Add 1R, 1G + Add 1K", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="All lose $2 & Add 1R", lose_money=2, add_cubes={CubeColor.RED: 1}),
                    CorruptionSpace(index=4, label="Lose $3 & 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Upgrade: Add 1R", add_cubes={CubeColor.RED: 1}, is_upgrade=True),
                ),
            ),
            VersionCard(
                version_str="v2.0",
                name="Polymorphic Worm",
                staging_payload={},
                directive_description="None.",
                directive_code="POLYMORPHIC_WORM",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="Lose 2 🔬", lose_patches=2),
                    CorruptionSpace(index=2, label="Add 2G + Add 1K", add_cubes={CubeColor.GREEN: 2, CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="All glitch 1 die & Add 1G", demote_dice=1, add_cubes={CubeColor.GREEN: 1}),
                    CorruptionSpace(index=4, label="Glitch 2 dice + Add 1K", demote_dice=2, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Upgrade: Add 1R", add_cubes={CubeColor.RED: 1}, is_upgrade=True),
                ),
            ),
            VersionCard(
                version_str="v3.0",
                name="Zero-Day Override",
                staging_payload={},
                directive_description="None.",
                directive_code="ZERO_DAY_OVERRIDE",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 1R, 1B, 1G", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}),
                    CorruptionSpace(index=2, label="Lose $3 & 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 1R, 1B", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
                    CorruptionSpace(index=4, label="All glitch 1 die & Add 1B, 1K", demote_dice=1, add_cubes={CubeColor.BLUE: 1, CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Return 1 Colored Die & glitch 1 die", return_colored_dice=1, demote_dice=1),
                    CorruptionSpace(index=6, label="Singularity", is_singularity=True),
                ),
            ),
            VersionCard(
                version_str="v3.0",
                name="Corrupted Kernel",
                staging_payload={},
                directive_description="None.",
                directive_code="CORRUPTED_KERNEL",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="Glitch 2 dice + Add 1R, 1B", demote_dice=2, add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
                    CorruptionSpace(index=2, label="Lose $3 & 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 1R, 1G", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1}),
                    CorruptionSpace(index=4, label="Lose 2 Secrets + Add 1K", lose_secrets=2, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Return 1 Colored Die & glitch 1 die", return_colored_dice=1, demote_dice=1),
                    CorruptionSpace(index=6, label="Singularity: Lose 1 Secret", lose_secrets=1, is_singularity=True),
                ),
            ),
        ]
    return [
        VersionCard(
            version_str="v1.0",
            name="Script Kiddie",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
            directive_description="None.",
            directive_code="SCRIPT_KIDDIE",
            corruption_track=(
                CorruptionSpace(index=1, label="Add 1R", add_cubes={CubeColor.RED: 1}),
                CorruptionSpace(index=2, label="All lose $2 + Add 1K", lose_money=2, add_cubes={CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="Lose 1 🔬", lose_patches=1),
                CorruptionSpace(index=4, label="Upgrade: Lose 1 🔬", lose_patches=1, is_upgrade=True),
            ),
        ),
        VersionCard(
            version_str="v1.0",
            name="Data Scraper",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2},
            directive_description="Players start with +$1 extra Money.",
            directive_code="DATA_SCRAPER",
            starting_cash_bonus=1,
            corruption_track=(
                CorruptionSpace(index=1, label="Lose 1 🔬", lose_patches=1),
                CorruptionSpace(index=2, label="Lose $1 + Add 1K", lose_money=1, add_cubes={CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="Add 1G", add_cubes={CubeColor.GREEN: 1}),
                CorruptionSpace(index=4, label="Upgrade: Glitch 1 die", demote_dice=1, is_upgrade=True),
            ),
        ),
        VersionCard(
            version_str="v2.0",
            name="Ransomware-as-a-Service",
            staging_payload={},
            directive_description="None.",
            directive_code="RAAS",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="All lose $2", lose_money=2),
                CorruptionSpace(index=2, label="Add 1R, 1G + Add 1K", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="All lose $2 & Add 1R", lose_money=2, add_cubes={CubeColor.RED: 1}),
                CorruptionSpace(index=4, label="Lose $3 & 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
                CorruptionSpace(index=5, label="Upgrade: Add 1R", add_cubes={CubeColor.RED: 1}, is_upgrade=True),
            ),
        ),
        VersionCard(
            version_str="v2.0",
            name="Polymorphic Worm",
            staging_payload={},
            directive_description="None.",
            directive_code="POLYMORPHIC_WORM",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="Lose 2 🔬", lose_patches=2),
                CorruptionSpace(index=2, label="Add 2G + Add 1K", add_cubes={CubeColor.GREEN: 2, CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="All glitch 1 die & Add 1G", demote_dice=1, add_cubes={CubeColor.GREEN: 1}),
                CorruptionSpace(index=4, label="Glitch 1 die + Add 1K", demote_dice=1, add_cubes={CubeColor.BLACK: 1}),
                CorruptionSpace(index=5, label="Upgrade: Add 1R", add_cubes={CubeColor.RED: 1}, is_upgrade=True),
            ),
        ),
        VersionCard(
            version_str="v3.0",
            name="Zero-Day Override",
            staging_payload={},
            directive_description="None.",
            directive_code="ZERO_DAY_OVERRIDE",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="Add 1R, 1B, 1G", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}),
                CorruptionSpace(index=2, label="Lose $3 & 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="Add 1R, 1B", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
                CorruptionSpace(index=4, label="All glitch 1 die & Add 1B, 1K", demote_dice=1, add_cubes={CubeColor.BLUE: 1, CubeColor.BLACK: 1}),
                CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1),
                CorruptionSpace(index=6, label="Singularity", is_singularity=True),
            ),
        ),
        VersionCard(
            version_str="v3.0",
            name="Corrupted Kernel",
            staging_payload={},
            directive_description="None.",
            directive_code="CORRUPTED_KERNEL",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="Glitch 1 die + Add 1R, 1B", demote_dice=1, add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
                CorruptionSpace(index=2, label="Lose $3 & 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="Add 1R, 1G", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1}),
                CorruptionSpace(index=4, label="Lose 1 Secret + Add 1K", lose_secrets=1, add_cubes={CubeColor.BLACK: 1}),
                CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1),
                CorruptionSpace(index=6, label="Singularity: Lose 1 Secret", lose_secrets=1, is_singularity=True),
            ),
        ),
    ]


def get_all_version_cards(profile: str = "STANDARD", player_specific: bool = True) -> List[VersionCard]:
    """Returns Version cards with per-version Corruption Tracks per RULES.md Section 6C.

    Supported profiles: "STANDARD" (Profile 1), "AGGRESSIVE" (Profile 2), and "V040_ASYMMETRIC" (v0.40.0).
    When player_specific is False (or profile begins with "LEGACY"), returns legacy table-wide hazard cards (INV-TARGET-08).
    """
    p = profile.upper()
    if not player_specific or p.startswith("LEGACY"):
        is_aggressive = ("AGGRESSIVE" in p)
        return _get_legacy_version_cards(is_aggressive=is_aggressive)
    if p == "V040_ASYMMETRIC":
        return [
            # --- Branch Alpha: Economic Extortion (Red-Heavy) ---
            VersionCard(
                version_str="v1.0",
                name="Script Kiddie (Alpha)",
                staging_payload={CubeColor.RED: 2, CubeColor.BLUE: 1},
                directive_description="None.",
                directive_code="SCRIPT_KIDDIE",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 1R", add_cubes={CubeColor.RED: 1}),
                    CorruptionSpace(index=2, label="All lose $2 + Add 1K", lose_money=2, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="All lose $2", lose_money=2),
                    CorruptionSpace(index=4, label="Upgrade: Add 1R", add_cubes={CubeColor.RED: 1}, is_upgrade=True),
                ),
            ),
            VersionCard(
                version_str="v1.0",
                name="Data Scraper (Beta)",
                staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2},
                directive_description="None.",
                directive_code="DATA_SCRAPER",
                corruption_track=(
                    CorruptionSpace(index=1, label="Lose 2 🔬", lose_patches=2),
                    CorruptionSpace(index=2, label="Add 1B + Add 1K", add_cubes={CubeColor.BLUE: 1, CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Lose 1 🔬", lose_patches=1),
                    CorruptionSpace(index=4, label="Upgrade: Add 1B", add_cubes={CubeColor.BLUE: 1}, is_upgrade=True),
                ),
            ),
            VersionCard(
                version_str="v1.0",
                name="Logic Daemon (Gamma)",
                staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
                directive_description="None.",
                directive_code="LOGIC_DAEMON",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 1G", add_cubes={CubeColor.GREEN: 1}),
                    CorruptionSpace(index=2, label="Glitch 1 die + Add 1K", demote_dice=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 1G", add_cubes={CubeColor.GREEN: 1}),
                    CorruptionSpace(index=4, label="Upgrade: Glitch 1 die", demote_dice=1, is_upgrade=True),
                ),
            ),
            # --- Branch Alpha v2.0 ---
            VersionCard(
                version_str="v2.0",
                name="Ransomware-as-a-Service (Alpha)",
                staging_payload={},
                directive_description="None.",
                directive_code="RAAS",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 2R", add_cubes={CubeColor.RED: 2}),
                    CorruptionSpace(index=2, label="All lose $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 1R & All lose $2", add_cubes={CubeColor.RED: 1}, lose_money=2),
                    CorruptionSpace(index=4, label="All lose $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Upgrade: Add 2R", add_cubes={CubeColor.RED: 2}, is_upgrade=True),
                ),
            ),
            # --- Branch Beta v2.0 ---
            VersionCard(
                version_str="v2.0",
                name="Spyware Mesh (Beta)",
                staging_payload={},
                directive_description="None.",
                directive_code="SPYWARE_MESH",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 2B", add_cubes={CubeColor.BLUE: 2}),
                    CorruptionSpace(index=2, label="Lose 2 🔬 + Add 1K", lose_patches=2, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 1B & Lose 1 🔬", add_cubes={CubeColor.BLUE: 1}, lose_patches=1),
                    CorruptionSpace(index=4, label="Lose 1 Secret + Add 1K", lose_secrets=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Upgrade: Add 2B", add_cubes={CubeColor.BLUE: 2}, is_upgrade=True),
                ),
            ),
            # --- Branch Gamma v2.0 ---
            VersionCard(
                version_str="v2.0",
                name="Polymorphic Worm (Gamma)",
                staging_payload={},
                directive_description="None.",
                directive_code="POLYMORPHIC_WORM",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 2G", add_cubes={CubeColor.GREEN: 2}),
                    CorruptionSpace(index=2, label="Glitch 1 die + Add 1K", demote_dice=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="All glitch 1 die & Add 1G", demote_dice=1, add_cubes={CubeColor.GREEN: 1}),
                    CorruptionSpace(index=4, label="Glitch 1 die + Add 1K", demote_dice=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Upgrade: Add 1G", add_cubes={CubeColor.GREEN: 1}, is_upgrade=True),
                ),
            ),
            # --- Branch Alpha v3.0 ---
            VersionCard(
                version_str="v3.0",
                name="Zero-Day Override (Alpha)",
                staging_payload={},
                directive_description="None.",
                directive_code="ZERO_DAY_OVERRIDE",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 2R, 1B", add_cubes={CubeColor.RED: 2, CubeColor.BLUE: 1}),
                    CorruptionSpace(index=2, label="All lose $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 2R", add_cubes={CubeColor.RED: 2}),
                    CorruptionSpace(index=4, label="All lose $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Add 1R & Return 1 Colored Die", add_cubes={CubeColor.RED: 1}, return_colored_dice=1),
                    CorruptionSpace(index=6, label="Singularity", is_singularity=True),
                ),
            ),
            # --- Branch Beta v3.0 ---
            VersionCard(
                version_str="v3.0",
                name="Corrupted Kernel (Beta)",
                staging_payload={},
                directive_description="None.",
                directive_code="CORRUPTED_KERNEL",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 2B, 1R", add_cubes={CubeColor.BLUE: 2, CubeColor.RED: 1}),
                    CorruptionSpace(index=2, label="Lose 1 Secret + Add 1K", lose_secrets=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 2B", add_cubes={CubeColor.BLUE: 2}),
                    CorruptionSpace(index=4, label="Lose 2 🔬 + Add 1K", lose_patches=2, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1),
                    CorruptionSpace(index=6, label="Singularity: Lose 1 Secret", lose_secrets=1, is_singularity=True),
                ),
            ),
            # --- Branch Gamma v3.0 ---
            VersionCard(
                version_str="v3.0",
                name="Subversion Engine (Gamma)",
                staging_payload={},
                directive_description="None.",
                directive_code="SUBVERSION_ENGINE",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 1R, 1B, 1G", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}),
                    CorruptionSpace(index=2, label="Lose $2 & 1 🔬 + Add 1K", lose_money=2, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Add 1G, 1R", add_cubes={CubeColor.GREEN: 1, CubeColor.RED: 1}),
                    CorruptionSpace(index=4, label="All glitch 1 die + Add 1K", demote_dice=1, add_cubes={CubeColor.BLACK: 1}),
                    CorruptionSpace(index=5, label="Return 1 Colored Die", return_colored_dice=1),
                    CorruptionSpace(index=6, label="Singularity", is_singularity=True),
                ),
            ),
        ]

    is_aggressive = p == "AGGRESSIVE"

    if is_aggressive:
        # Profile 2: Aggressive Escalation Tracks (Same Pacing Clock, Heightened Economic Friction)
        return [
            # v1.0 Script Kiddie (4 spaces)
            VersionCard(
                version_str="v1.0",
                name="Script Kiddie",
                staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
                directive_description="None.",
                directive_code="SCRIPT_KIDDIE",
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 1R", add_cubes={CubeColor.RED: 1}),
                    CorruptionSpace(index=2, label="Most $ loses $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MONEY),
                    CorruptionSpace(index=3, label="Fewest Glitched glitches 1 slot", demote_dice=1, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                    CorruptionSpace(
                        index=4,
                        label="Upgrade: Most 🔬 loses 2 🔬",
                        lose_patches=2,
                        is_upgrade=True,
                        target_criterion=TargetCriterion.MOST_RESEARCH,
                    ),
                ),
            ),
            # v1.0 Data Scraper (4 spaces)
            VersionCard(
                version_str="v1.0",
                name="Data Scraper",
                staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2},
                directive_description="Players start with +$1 extra Money.",
                directive_code="DATA_SCRAPER",
                starting_cash_bonus=1,
                corruption_track=(
                    CorruptionSpace(index=1, label="Most 🔬 loses 2 🔬", lose_patches=2, target_criterion=TargetCriterion.MOST_RESEARCH),
                    CorruptionSpace(index=2, label="Most $ loses $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MONEY),
                    CorruptionSpace(index=3, label="Add 1G", add_cubes={CubeColor.GREEN: 1}),
                    CorruptionSpace(
                        index=4,
                        label="Upgrade: Fewest Glitched glitches 2 slots",
                        demote_dice=2,
                        is_upgrade=True,
                        target_criterion=TargetCriterion.FEWEST_GLITCHED,
                    ),
                ),
            ),
            # v2.0 RaaS (5 spaces)
            VersionCard(
                version_str="v2.0",
                name="Ransomware-as-a-Service",
                staging_payload={},
                directive_description="None.",
                directive_code="RAAS",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="Transfer: Least MS takes $2 from Most MS", transfer_type=TransferType.LEAST_MS_TAKES_CASH, transfer_amount=2),
                    CorruptionSpace(index=2, label="Add 1R, 1B + Add 1K", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Most $ loses $3 & Add 1R", lose_money=3, add_cubes={CubeColor.RED: 1}, target_criterion=TargetCriterion.MOST_MONEY),
                    CorruptionSpace(index=4, label="Most MS loses $3 & 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MARKET_SHARE),
                    CorruptionSpace(
                        index=5,
                        label="Upgrade: Add 1R",
                        add_cubes={CubeColor.RED: 1},
                        is_upgrade=True,
                    ),
                ),
            ),
            # v2.0 Polymorphic Worm (5 spaces)
            VersionCard(
                version_str="v2.0",
                name="Polymorphic Worm",
                staging_payload={},
                directive_description="None.",
                directive_code="POLYMORPHIC_WORM",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="Transfer: Least 🔬 takes 2 🔬 from Most 🔬", transfer_type=TransferType.LEAST_RESEARCH_TAKES_RESEARCH, transfer_amount=2),
                    CorruptionSpace(index=2, label="Add 1B, 1G + Add 1K", add_cubes={CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}),
                    CorruptionSpace(index=3, label="Fewest Glitched glitches 1 slot & Add 1G", demote_dice=1, add_cubes={CubeColor.GREEN: 1}, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                    CorruptionSpace(index=4, label="Fewest Glitched glitches 2 slots + Add 1K", demote_dice=2, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                    CorruptionSpace(
                        index=5,
                        label="Upgrade: Add 1R",
                        add_cubes={CubeColor.RED: 1},
                        is_upgrade=True,
                    ),
                ),
            ),
            # v3.0 Zero-Day Override (6 spaces)
            VersionCard(
                version_str="v3.0",
                name="Zero-Day Override",
                staging_payload={},
                directive_description="None.",
                directive_code="ZERO_DAY_OVERRIDE",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="Add 1R, 1B, 1G", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}),
                    CorruptionSpace(index=2, label="Most $ loses $4; Most 🔬 loses 2 🔬 + Add 1K", lose_money=4, lose_patches=2, add_cubes={CubeColor.BLACK: 1}, target_money_criterion=TargetCriterion.MOST_MONEY, target_patches_criterion=TargetCriterion.MOST_RESEARCH),
                    CorruptionSpace(index=3, label="Add 1R, 1B", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
                    CorruptionSpace(index=4, label="Fewest Glitched glitches 1 slot & Add 1B, 1K", demote_dice=1, add_cubes={CubeColor.BLUE: 1, CubeColor.BLACK: 1}, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                    CorruptionSpace(index=5, label="Most Colored Dice returns 1 die & glitches 1 slot", return_colored_dice=1, demote_dice=1, target_return_colored_criterion=TargetCriterion.MOST_COLORED_DICE, target_demote_criterion=TargetCriterion.MOST_COLORED_DICE, target_criterion=TargetCriterion.MOST_COLORED_DICE),
                    CorruptionSpace(
                        index=6,
                        label="Singularity",
                        is_singularity=True,
                    ),
                ),
            ),
            # v3.0 Corrupted Kernel (6 spaces)
            VersionCard(
                version_str="v3.0",
                name="Corrupted Kernel",
                staging_payload={},
                directive_description="None.",
                directive_code="CORRUPTED_KERNEL",
                staging_payload_2p={},
                corruption_track=(
                    CorruptionSpace(index=1, label="Fewest Glitched glitches 2 slots + Add 1R, 1B", demote_dice=2, add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                    CorruptionSpace(index=2, label="Most MS loses $4 & 2 🔬 + Add 1K", lose_money=4, lose_patches=2, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MARKET_SHARE),
                    CorruptionSpace(index=3, label="Add 1R, 1G", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1}),
                    CorruptionSpace(index=4, label="Most Secrets loses 2 Secrets + Add 1K", lose_secrets=2, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_SECRETS),
                    CorruptionSpace(index=5, label="Most Colored Dice returns 1 die & glitches 1 slot", return_colored_dice=1, demote_dice=1, target_return_colored_criterion=TargetCriterion.MOST_COLORED_DICE, target_demote_criterion=TargetCriterion.MOST_COLORED_DICE, target_criterion=TargetCriterion.MOST_COLORED_DICE),
                    CorruptionSpace(
                        index=6,
                        label="Singularity: Most Secrets loses 1 Secret",
                        lose_secrets=1,
                        is_singularity=True,
                        target_criterion=TargetCriterion.MOST_SECRETS,
                    ),
                ),
            ),
        ]

    # Profile 1: Standard Escalation Tracks
    return [
        # v1.0 Script Kiddie (4 spaces)
        VersionCard(
            version_str="v1.0",
            name="Script Kiddie",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
            directive_description="None.",
            directive_code="SCRIPT_KIDDIE",
            corruption_track=(
                CorruptionSpace(index=1, label="Add 1R", add_cubes={CubeColor.RED: 1}),
                CorruptionSpace(index=2, label="Player with most $ loses $2 + Add 1K", lose_money=2, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MONEY),
                CorruptionSpace(index=3, label="Player with most 🔬 loses 1 🔬", lose_patches=1, target_criterion=TargetCriterion.MOST_RESEARCH),
                CorruptionSpace(
                    index=4,
                    label="Upgrade: Player with most MS loses 1 MS",
                    lose_market_share=1,
                    is_upgrade=True,
                    target_criterion=TargetCriterion.MOST_MARKET_SHARE,
                ),
            ),
        ),
        # v1.0 Data Scraper (4 spaces)
        VersionCard(
            version_str="v1.0",
            name="Data Scraper",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2},
            directive_description="Players start with +$1 extra Money.",
            directive_code="DATA_SCRAPER",
            starting_cash_bonus=1,
            corruption_track=(
                CorruptionSpace(index=1, label="Player with most 🔬 loses 1 🔬", lose_patches=1, target_criterion=TargetCriterion.MOST_RESEARCH),
                CorruptionSpace(index=2, label="Player with most $ loses $2 + Add 1K", lose_money=2, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MONEY),
                CorruptionSpace(index=3, label="Add 1G", add_cubes={CubeColor.GREEN: 1}),
                CorruptionSpace(
                    index=4,
                    label="Upgrade: Player with fewest Glitched slots glitches 1 slot",
                    demote_dice=1,
                    is_upgrade=True,
                    target_criterion=TargetCriterion.FEWEST_GLITCHED,
                ),
            ),
        ),
        # v2.0 RaaS (5 spaces)
        VersionCard(
            version_str="v2.0",
            name="Ransomware-as-a-Service",
            staging_payload={},
            directive_description="None.",
            directive_code="RAAS",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="Transfer: Least MS takes $1 from Most MS", transfer_type=TransferType.LEAST_MS_TAKES_CASH, transfer_amount=1),
                CorruptionSpace(index=2, label="Add 1R, 1B + Add 1K", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="Player with most $ loses $2 & Add 1R", lose_money=2, add_cubes={CubeColor.RED: 1}, target_criterion=TargetCriterion.MOST_MONEY),
                CorruptionSpace(index=4, label="Player with most MS loses $3 and 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MARKET_SHARE),
                CorruptionSpace(
                    index=5,
                    label="Upgrade: Add 1R",
                    add_cubes={CubeColor.RED: 1},
                    is_upgrade=True,
                ),
            ),
        ),
        # v2.0 Polymorphic Worm (5 spaces)
        VersionCard(
            version_str="v2.0",
            name="Polymorphic Worm",
            staging_payload={},
            directive_description="None.",
            directive_code="POLYMORPHIC_WORM",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="Transfer: Least 🔬 takes 1 🔬 from Most 🔬", transfer_type=TransferType.LEAST_RESEARCH_TAKES_RESEARCH, transfer_amount=1),
                CorruptionSpace(index=2, label="Add 1B, 1G + Add 1K", add_cubes={CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}),
                CorruptionSpace(index=3, label="Player with fewest Glitched slots glitches 1 slot & Add 1G", demote_dice=1, add_cubes={CubeColor.GREEN: 1}, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                CorruptionSpace(index=4, label="Player with most Secrets loses $3 + Add 1K", lose_money=3, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_SECRETS),
                CorruptionSpace(
                    index=5,
                    label="Upgrade: Add 1R",
                    add_cubes={CubeColor.RED: 1},
                    is_upgrade=True,
                ),
            ),
        ),
        # v3.0 Zero-Day Override (6 spaces)
        VersionCard(
            version_str="v3.0",
            name="Zero-Day Override",
            staging_payload={},
            directive_description="None.",
            directive_code="ZERO_DAY_OVERRIDE",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="Add 1R, 1B, 1G", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}),
                CorruptionSpace(index=2, label="Most $ loses $3; Most 🔬 loses 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}, target_money_criterion=TargetCriterion.MOST_MONEY, target_patches_criterion=TargetCriterion.MOST_RESEARCH),
                CorruptionSpace(index=3, label="Add 1R, 1B", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
                CorruptionSpace(index=4, label="Player with fewest Glitched slots glitches 1 slot & Add 1B, 1K", demote_dice=1, add_cubes={CubeColor.BLUE: 1, CubeColor.BLACK: 1}, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                CorruptionSpace(index=5, label="Player with most Colored Dice returns 1 Colored Die", return_colored_dice=1, target_criterion=TargetCriterion.MOST_COLORED_DICE),
                CorruptionSpace(
                    index=6,
                    label="Singularity",
                    is_singularity=True,
                ),
            ),
        ),
        # v3.0 Corrupted Kernel (6 spaces)
        VersionCard(
            version_str="v3.0",
            name="Corrupted Kernel",
            staging_payload={},
            directive_description="None.",
            directive_code="CORRUPTED_KERNEL",
            staging_payload_2p={},
            corruption_track=(
                CorruptionSpace(index=1, label="Player with fewest Glitched slots glitches 1 slot + Add 1R, 1B", demote_dice=1, add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}, target_criterion=TargetCriterion.FEWEST_GLITCHED),
                CorruptionSpace(index=2, label="Player with most MS loses $3 and 1 🔬 + Add 1K", lose_money=3, lose_patches=1, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_MARKET_SHARE),
                CorruptionSpace(index=3, label="Add 1R, 1G", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1}),
                CorruptionSpace(index=4, label="Player with most Secrets loses 1 Secret + Add 1K", lose_secrets=1, add_cubes={CubeColor.BLACK: 1}, target_criterion=TargetCriterion.MOST_SECRETS),
                CorruptionSpace(index=5, label="Player with most Colored Dice returns 1 Colored Die", return_colored_dice=1, target_criterion=TargetCriterion.MOST_COLORED_DICE),
                CorruptionSpace(
                    index=6,
                    label="Singularity: Most Secrets loses 1 Secret",
                    lose_secrets=1,
                    is_singularity=True,
                    target_criterion=TargetCriterion.MOST_SECRETS,
                ),
            ),
        ),
    ]


get_version_cards = get_all_version_cards


def get_default_version_deck(profile: str = "STANDARD", player_specific: bool = True) -> List[VersionCard]:
    """Returns the default baseline version cards: Script Kiddie (v1.0), RaaS (v2.0), Zero-Day Override (v3.0)."""
    cards = get_all_version_cards(profile=profile, player_specific=player_specific)
    v1_pool = [v for v in cards if v.version_str == "v1.0"]
    v2_pool = [v for v in cards if v.version_str == "v2.0"]
    v3_pool = [v for v in cards if v.version_str == "v3.0"]
    return [v1_pool[0], v2_pool[0], v3_pool[0]]


def get_roadmap_deck(path_id: int, profile: str = "STANDARD", player_specific: bool = True) -> List[VersionCard]:
    """Returns a deterministic 3-card roadmap deck for a designated path ID (1-4).

    Path 1 (Kinetic): Script Kiddie (v1.0), RaaS (v2.0), Corrupted Kernel (v3.0)
    Path 2 (Contagion): Script Kiddie (v1.0), Polymorphic Worm (v2.0), Zero-Day Override (v3.0)
    Path 3 (Mixed A): Script Kiddie (v1.0), RaaS (v2.0), Zero-Day Override (v3.0)
    Path 4 (Mixed B): Script Kiddie (v1.0), Polymorphic Worm (v2.0), Corrupted Kernel (v3.0)
    """
    cards = {c.directive_code: c for c in get_all_version_cards(profile=profile, player_specific=player_specific)}
    if path_id == 1:
        return [cards["SCRIPT_KIDDIE"], cards["RAAS"], cards["CORRUPTED_KERNEL"]]
    elif path_id == 2:
        return [cards["SCRIPT_KIDDIE"], cards["POLYMORPHIC_WORM"], cards["ZERO_DAY_OVERRIDE"]]
    elif path_id == 3:
        return [cards["SCRIPT_KIDDIE"], cards["RAAS"], cards["ZERO_DAY_OVERRIDE"]]
    elif path_id == 4:
        return [cards["SCRIPT_KIDDIE"], cards["POLYMORPHIC_WORM"], cards["CORRUPTED_KERNEL"]]
    else:
        raise ValueError(f"Unknown roadmap path_id: {path_id}. Must be 1, 2, 3, or 4.")


def get_random_version_deck(rng: random.Random, profile: str = "STANDARD", player_specific: bool = True) -> List[VersionCard]:
    """Randomly selects 1 v1.0 card, 1 v2.0 card, and 1 v3.0 card for the Rogue Agent roadmap."""
    all_versions = get_all_version_cards(profile=profile, player_specific=player_specific)
    v1_pool = [v for v in all_versions if v.version_str == "v1.0"]
    v2_pool = [v for v in all_versions if v.version_str == "v2.0"]
    v3_pool = [v for v in all_versions if v.version_str == "v3.0"]
    return [
        rng.choice(v1_pool),
        rng.choice(v2_pool),
        rng.choice(v3_pool),
    ]


def get_random_setup(
    rng: random.Random,
    profile: str = "STANDARD",
) -> Tuple[Dict[DieColor, VariantCard], List[VersionCard]]:
    """Returns randomized variant cards and version deck for game setup."""
    return get_random_variant_cards(rng), get_random_version_deck(rng, profile=profile)


# =====================================================================
# Legacy archetype cards (bridge to White Hat Operatives; RULES.md Section 6D)
# =====================================================================

def get_all_archetype_cards() -> List[ArchetypeCard]:
    """Returns all 6 consultancy archetype cards defined in RULES.md Section 6D."""
    return [
        ArchetypeCard(
            code=ArchetypeCode.ACOUSTIC,
            name="The Acoustic",
            timing_window="Phase 4: Attack Resolution",
            ability_name="Baffle Echo",
            description="When resolving compiler damage, ignore 1 Attack Cube (Red, Blue, or Green) of your choice for yourself this round. (All exited cubes remain in the exit tray and recycle into the Staging Cup as normal).",
        ),
        ArchetypeCard(
            code=ArchetypeCode.PHREAKER,
            name="The Phreaker",
            timing_window="Phase 5: Emergency Hotfix & Magnetic Splice",
            ability_name="Magnetic Splice",
            description="Move 1 die from your Glitched Box directly to your Ready for Release Zone for free (bypassing Scanned and saving 1 🔬).",
        ),
        ArchetypeCard(
            code=ArchetypeCode.PRODIGY,
            name="The Prodigy",
            timing_window="Phase 1: Step 4 Rerolls",
            ability_name="Brute-Force Bypass",
            description="During your rerolls this phase, you may include any number of Locked dice in your free rerolls without spending 🔬 tokens. In addition, you may turn 1 of your rolled dice to any non-Star face of your choice.",
        ),
        ArchetypeCard(
            code=ArchetypeCode.SPOOK,
            name="The Spook",
            timing_window="Phase 4: Attack Resolution",
            ability_name="Slush Fund",
            description="The Spook accesses emergency black budget reserves: Absorb up to 2 Corporate Secret loss (from Blue Spyware) for free without paying cash. (Any additional Secret loss may be absorbed by paying $1 per Secret as normal).",
        ),
        ArchetypeCard(
            code=ArchetypeCode.CIPHER,
            name="The Cipher",
            timing_window="Phase 6: Operations Turn",
            ability_name="Algorithmic Arbitrage",
            description="Purchase 1 Colored Die from the Market at a $2 discount (minimum cost $0), OR gain an immediate +$2 cash payout from the bank.",
        ),
        ArchetypeCard(
            code=ArchetypeCode.OPERATOR,
            name="The Operator",
            timing_window="Phase 3: Income",
            ability_name="Capital Injection",
            description="Once per Rogue Agent version during Phase 3 (Income), gain +3 $ cleanly before resolving Phase 4 attacks.",
        ),
    ]


def get_archetype_by_code(code: ArchetypeCode | str) -> ArchetypeCard:
    """Retrieves an archetype card by ArchetypeCode enum or string name/code."""
    code_str = code.value.upper() if isinstance(code, ArchetypeCode) else str(code).upper()
    for card in get_all_archetype_cards():
        if card.code.value.upper() == code_str or card.code.name.upper() == code_str or card.name.upper() == code_str:
            return card
    raise ValueError(f"Unknown Archetype code: {code}")


def get_random_archetypes(num_players: int, rng: random.Random) -> List[ArchetypeCard]:
    """Randomly selects unique consultancy archetypes without replacement for all players."""
    all_cards = get_all_archetype_cards()
    if not (1 <= num_players <= len(all_cards)):
        raise ValueError(f"num_players must be between 1 and {len(all_cards)}, got {num_players}")
    return rng.sample(all_cards, num_players)


ARCHETYPES: Dict[ArchetypeCode, ArchetypeCard] = {c.code: c for c in get_all_archetype_cards()}


# =====================================================================
# Modular Client Companies & White Hat Operatives (v0.25.0 Canonical)
# =====================================================================

COMPANIES: Dict[CompanyCode, Company] = {
    CompanyCode.MERIDIAN: Company(
        code=CompanyCode.MERIDIAN,
        name="Meridian Financial Trust",
        sector="Banking Infrastructure",
        override_name="Capital Injection",
        timing_window="Phase 3: Income",
        description="Once per Rogue Agent version during Phase 3 (Income), gain +3 $ cleanly before resolving Phase 4 attacks.",
        flavor="When liquidity is limitless, headcount is merely an accounting variable.",
        starting_defense_capacity=2,
        starting_triage_bandwidth=2,
        starting_release_bandwidth=4,
        starting_triage_level=0,
        starting_release_level=0,
        starting_defense_level=0,
        starting_patent_level=0,
        starting_cash_bonus=2,
    ),
    CompanyCode.OMNIDYNE: Company(
        code=CompanyCode.OMNIDYNE,
        name="Omnidyne Systems",
        sector="Tech Giant",
        override_name="Magnetic Splice",
        timing_window="Phase 5: Emergency Hotfix & Magnetic Splice",
        description="Move 1 die from your Glitched Box directly to your Ready for Release Zone for free (bypassing Scanned and saving 1 🔬).",
        flavor="Proprietary hardware backplanes allow instantaneous hot-swapping under live load.",
        starting_defense_capacity=1,
        starting_triage_bandwidth=3,
        starting_release_bandwidth=5,
        starting_triage_level=1,
        starting_release_level=1,
        starting_defense_level=0,
        starting_patent_level=0,
    ),
    CompanyCode.AEGIS: Company(
        code=CompanyCode.AEGIS,
        name="Aegis Defense Relay",
        sector="Security Firm",
        override_name="Baffle Echo",
        timing_window="Phase 4: Attack Resolution",
        description="When resolving compiler damage, ignore 1 Attack Cube (Red, Blue, or Green) of your choice for yourself this round. (All exited cubes remain in the exit tray and recycle into the Staging Cup as normal).",
        flavor="Multi-layered kinetic dampeners disperse inbound network blast energy.",
        starting_defense_capacity=3,
        starting_triage_bandwidth=1,
        starting_release_bandwidth=3,
        starting_triage_level=0,
        starting_release_level=0,
        starting_defense_level=1,
        starting_patent_level=0,
    ),
    CompanyCode.DTO: Company(
        code=CompanyCode.DTO,
        name="Department of Telecommunications Oversight",
        sector="Federal Agency",
        override_name="Slush Fund",
        timing_window="Phase 4: Attack Resolution",
        description="Absorb up to 2 Corporate Secret loss (from Blue Spyware) for free without paying cash. (Any additional Secret loss may be absorbed by paying $1 per Secret as normal).",
        flavor="Classified black budget allocations absorb compliance failures without public oversight.",
        starting_defense_capacity=2,
        starting_triage_bandwidth=2,
        starting_release_bandwidth=4,
        starting_triage_level=0,
        starting_release_level=0,
        starting_defense_level=0,
        starting_patent_level=0,
        starting_secrets_bonus=1,
    ),
    CompanyCode.HELIX: Company(
        code=CompanyCode.HELIX,
        name="Helix Biomedical Consortium",
        sector="Medical Research",
        override_name="Brute-Force Bypass",
        timing_window="Phase 1: Step 4 Rerolls",
        description="During your rerolls this phase, you may turn 1 of your rolled dice to any legal non-Star face of your choice.",
        flavor="Massively parallel quantum sequencing breaks deterministic encryption gates.",
        starting_defense_capacity=2,
        starting_triage_bandwidth=2,
        starting_release_bandwidth=4,
        starting_triage_level=0,
        starting_release_level=0,
        starting_defense_level=0,
        starting_patent_level=1,
        starting_research_bonus=2,
    ),
    CompanyCode.PROMETHEUS: Company(
        code=CompanyCode.PROMETHEUS,
        name="The Prometheus Foundation",
        sector="Non-Profit",
        override_name="Algorithmic Arbitrage",
        timing_window="Phase 6: Operations Turn",
        description="Purchase 1 Colored Die from the Market or Personal Reserve at a $2 discount (minimum cost $0), OR gain an immediate +$2 cash payout from the bank.",
        flavor="Open-source cryptographic protocols circumvent proprietary enterprise licensing fees.",
        starting_defense_capacity=2,
        starting_triage_bandwidth=2,
        starting_release_bandwidth=4,
        starting_triage_level=0,
        starting_release_level=0,
        starting_defense_level=0,
        starting_patent_level=0,
        upgrade_discount=1,
    ),
}

WHITE_HATS: Dict[WhiteHatCode, WhiteHat] = {
    WhiteHatCode.OPERATOR: WhiteHat(
        code=WhiteHatCode.OPERATOR,
        name="The Operator",
        role="Tactical Staffing & Logistics Lead",
        protocol_name="Logistics Bounty",
        timing_window="Phase 3: Income",
        description="During Phase 3 (Income), each of your Purple ★ faces still In Production yields +1 🔬 (in addition to its base $1).",
        flavor="Redundant contractor pipelines ready on zero notice.",
        reserve_cost=5,
    ),
    WhiteHatCode.PHREAKER: WhiteHat(
        code=WhiteHatCode.PHREAKER,
        name="The Phreaker",
        role="Hardware Intrusion Specialist",
        protocol_name="Jumper Diagnostics",
        timing_window="Phase 3: Income",
        description="When Purple ★ is rolled, roll 1 offline die in Under Development (Glitched or Scanned); if Under Development is empty, collect +$1 cash (shields/glitches produce 0; die remains in place).",
        flavor="Raw voltage pulses extract signal from dormant silicon.",
        reserve_cost=4,
    ),
    WhiteHatCode.ACOUSTIC: WhiteHat(
        code=WhiteHatCode.ACOUSTIC,
        name="The Acoustic",
        role="Side-Channel Cryptanalyst",
        protocol_name="Resonance Sensor",
        timing_window="Phase 3: Income",
        description="When Purple ★ is rolled, gain +$1 cash per distinct cube color present in the Exit Tray this round (Red, Blue, Green, Black; max +$4).",
        flavor="Harmonic resonance frequencies decode physical chassis vibrations.",
        reserve_cost=4,
    ),
    WhiteHatCode.SPOOK: WhiteHat(
        code=WhiteHatCode.SPOOK,
        name="The Spook",
        role="Covert Intelligence Specialist",
        protocol_name="Burn Notice",
        timing_window="Phase 3: Income",
        description="When Purple ★ is rolled, gain +$2 cash payout. Additionally, you may optionally burn 1 owned colored die back to supply to gain +1 Corporate Secret.",
        flavor="Scorched-earth protocols ensure zero forensic recovery.",
        reserve_cost=5,
    ),
    WhiteHatCode.PRODIGY: WhiteHat(
        code=WhiteHatCode.PRODIGY,
        name="The Prodigy",
        role="Autonomous Exploit Hacker",
        protocol_name="Arbitrary Code Execution",
        timing_window="Phase 1: Step 4 Rolling",
        description="When Purple ★ is rolled, turn 1 other rolled die in your active pool to any legal non-Star face of that die's color.",
        flavor="Payload injection executes before memory boundaries establish.",
        reserve_cost=5,
    ),
    WhiteHatCode.CIPHER: WhiteHat(
        code=WhiteHatCode.CIPHER,
        name="The Cipher",
        role="Distributed Ledger Architect",
        protocol_name="Algorithmic Parity",
        timing_window="Phase 3: Income",
        description="When Purple ★ is rolled, collect +$2 cash and +1 🔬 Research Token in Phase 3: Income.",
        flavor="Parity calculations balance zero-knowledge proofs flawlessly.",
        reserve_cost=6,
    ),
}

INTRODUCTORY_PRESETS: Dict[int, List[Tuple[CompanyCode, WhiteHatCode]]] = {
    2: [
        (CompanyCode.MERIDIAN, WhiteHatCode.OPERATOR),
        (CompanyCode.OMNIDYNE, WhiteHatCode.PHREAKER),
    ],
    3: [
        (CompanyCode.MERIDIAN, WhiteHatCode.OPERATOR),
        (CompanyCode.OMNIDYNE, WhiteHatCode.PHREAKER),
        (CompanyCode.AEGIS, WhiteHatCode.ACOUSTIC),
    ],
    4: [
        (CompanyCode.MERIDIAN, WhiteHatCode.OPERATOR),
        (CompanyCode.OMNIDYNE, WhiteHatCode.PHREAKER),
        (CompanyCode.AEGIS, WhiteHatCode.ACOUSTIC),
        (CompanyCode.DTO, WhiteHatCode.SPOOK),
    ],
}

CANONICAL_COMPANY_FOR_OPERATIVE: Dict[WhiteHatCode, CompanyCode] = {
    WhiteHatCode.OPERATOR: CompanyCode.MERIDIAN,
    WhiteHatCode.PHREAKER: CompanyCode.OMNIDYNE,
    WhiteHatCode.ACOUSTIC: CompanyCode.AEGIS,
    WhiteHatCode.SPOOK: CompanyCode.DTO,
    WhiteHatCode.PRODIGY: CompanyCode.HELIX,
    WhiteHatCode.CIPHER: CompanyCode.PROMETHEUS,
}

CANONICAL_OPERATIVE_FOR_COMPANY: Dict[CompanyCode, WhiteHatCode] = {
    CompanyCode.MERIDIAN: WhiteHatCode.OPERATOR,
    CompanyCode.OMNIDYNE: WhiteHatCode.PHREAKER,
    CompanyCode.AEGIS: WhiteHatCode.ACOUSTIC,
    CompanyCode.DTO: WhiteHatCode.SPOOK,
    CompanyCode.HELIX: WhiteHatCode.PRODIGY,
    CompanyCode.PROMETHEUS: WhiteHatCode.CIPHER,
}


def get_all_companies() -> List[Company]:
    """Returns all 6 Client Companies."""
    return list(COMPANIES.values())


def get_company_by_code(code: CompanyCode | str) -> Company:
    """Retrieves a Company by enum or string code/name."""
    code_str = code.value.upper() if isinstance(code, CompanyCode) else str(code).upper()
    for comp in COMPANIES.values():
        if comp.code.value.upper() == code_str or comp.code.name.upper() == code_str or comp.name.upper() == code_str:
            return comp
    raise ValueError(f"Unknown Company code: {code}")


def get_random_companies(num_players: int, rng: random.Random) -> List[Company]:
    """Randomly selects unique Client Companies without replacement for all players."""
    all_comps = get_all_companies()
    if not (1 <= num_players <= len(all_comps)):
        raise ValueError(f"num_players must be between 1 and {len(all_comps)}, got {num_players}")
    return rng.sample(all_comps, num_players)


def get_all_white_hats() -> List[WhiteHat]:
    """Returns all 6 White Hat Operatives."""
    return list(WHITE_HATS.values())


def get_white_hat_by_code(code: WhiteHatCode | str) -> WhiteHat:
    """Retrieves a White Hat Operative by enum or string code/name."""
    code_str = code.value.upper() if isinstance(code, WhiteHatCode) else str(code).upper()
    for wh in WHITE_HATS.values():
        if wh.code.value.upper() == code_str or wh.code.name.upper() == code_str or wh.name.upper() == code_str:
            return wh
    raise ValueError(f"Unknown White Hat code: {code}")


def get_random_white_hats(num_players: int, rng: random.Random) -> List[WhiteHat]:
    """Randomly selects unique White Hat Operatives without replacement for all players."""
    all_wh = get_all_white_hats()
    if not (1 <= num_players <= len(all_wh)):
        raise ValueError(f"num_players must be between 1 and {len(all_wh)}, got {num_players}")
    return rng.sample(all_wh, num_players)


GRAY_FACE_PROFILES = ("V034", "V035_D1")


def create_gray_die(die_id: int, profile: Optional[str] = "V035_D1") -> Die:
    """Creates a Gray (Legacy Code) die.

    ``profile``: ``"V035_D1"`` (v0.35.0 canonical) or ``"V034"`` (legacy ``B, B, $1, $1, $1/🔬, 🔬``).
    """
    profile = profile or "V035_D1"

    def choice() -> Face:
        return Face(
            name="+$1 / +1 🔬",
            is_choice=True,
            choices=(Face("+$1", money=1), Face("+1 🔬", patches=1)),
        )

    if profile == "V034":
        faces = [
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="+$1", money=1),
            Face(name="+$1", money=1),
            choice(),
            Face(name="+1 🔬", patches=1),
        ]
    elif profile == "V035_D1":
        faces = [
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="+$1 & +1 🔬", money=1, patches=1),
            choice(),
            choice(),
            Face(name="+1 🔬", patches=1),
        ]
    else:
        raise ValueError(f"Unknown Gray face profile: {profile}")
    return Die(
        die_id=die_id,
        color=DieColor.GRAY,
        cost=0,
        vp=0,
        faces=faces,
    )


def effective_company(company: Optional[Company], config: Any = None) -> Optional[Company]:
    """v0.35.0 (INV-RT-FLAT-SETUP-01): with ``company_setup_bonuses=False`` every Client Company starts
    from the flat baseline (capacity 2 / 2 / 4, all levels 0, no cash / research / Secret bonus, no discount)."""
    if company is None or config is None or getattr(config, "company_setup_bonuses", True):
        return company
    return dataclasses.replace(
        company,
        starting_defense_capacity=2,
        starting_triage_bandwidth=2,
        starting_release_bandwidth=4,
        starting_triage_level=0,
        starting_release_level=0,
        starting_defense_level=0,
        starting_patent_level=0,
        starting_cash_bonus=0,
        starting_research_bonus=0,
        starting_secrets_bonus=0,
        upgrade_discount=0,
    )


def create_white_die(die_id: int) -> Die:
    """Creates a White (Contractor) temporary staffing die per RULES.md Section 6A (v0.7)."""
    faces = [
        Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
        Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
        Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
        Face(name="+$1", money=1),
        Face(name="Glitch (Locked)", is_glitch=True),
        Face(name="Glitch (Locked)", is_glitch=True),
    ]
    return Die(
        die_id=die_id,
        color=DieColor.WHITE,
        cost=1,
        vp=0,
        faces=faces,
    )


def create_colored_die(
    color: DieColor,
    die_id: int,
    variant_card: Optional[VariantCard] = None,
    reserve_cost: Optional[int] = None,
    cost: Optional[int] = None,
    gray_profile: Optional[str] = "V035_D1",
    face_profile: Optional[str] = "V037",
) -> Die:
    """Creates a colored die of the specified color with dynamic cost (v0.26.0 Baseline).

    ``face_profile="V038_DRAFT"`` uses the v0.38 candidate tables (Secret face on Face 5, no colored shields;
    spec v380 §4.2). Gray and White dice are unchanged by the profile.
    """
    if color == DieColor.GRAY:
        return create_gray_die(die_id, gray_profile)
    if color == DieColor.WHITE:
        return create_white_die(die_id)

    star_face = variant_card.star_face if variant_card else Face(name=f"{color.value} ★", is_star=True)
    var_code = variant_card.code if variant_card else None
    glitch_face = Face(name="Glitch (Locked)", is_glitch=True)

    # Derive dynamic cost with safe default fallbacks
    if cost is not None:
        die_cost = cost
    elif color == DieColor.PURPLE:
        die_cost = reserve_cost if reserve_cost is not None else (
            variant_card.cost if variant_card is not None else 4
        )
    else:
        if variant_card is not None:
            die_cost = variant_card.cost
        else:
            # Fallback default costs if variant card is omitted:
            # Red default R1: $5, Blue default B1: $5, Green default G1: $5, Yellow default Y1: $6
            default_costs = {
                DieColor.RED: 5,
                DieColor.BLUE: 5,
                DieColor.GREEN: 5,
                DieColor.YELLOW: 6,
                DieColor.PURPLE: 4,
            }
            die_cost = default_costs.get(color, 4)

    if face_profile in ("V038_DRAFT", "V038_YELLOW_MS", "V038_YELLOW_MS_ALT", "V038_YELLOW_MS_F3", "V038D", "V038F"):
        return _create_colored_die_v038(color, die_id, variant_card, star_face, var_code, die_cost, face_profile)

    if color == DieColor.RED:
        faces = [
            Face(name="Block 1 Red", block_amount=1, shield_color=ShieldColor.RED),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.BLUE:
        faces = [
            Face(name="Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
            Face(name="+1 🔬", patches=1),
            Face(name="+$1", money=1),
            Face(
                name="Block 1 Blue / +1 🔬",
                is_choice=True,
                choices=(
                    Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
                    Face("+1 🔬", patches=1),
                ),
            ),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.GREEN:
        faces = [
            Face(name="Block 1 Green", block_amount=1, shield_color=ShieldColor.GREEN),
            Face(name="+1 🔬", patches=1),
            Face(name="+2 🔬", patches=2),
            Face(
                name="+1 🔬 / +$1",
                is_choice=True,
                choices=(
                    Face("+1 🔬", patches=1),
                    Face("+$1", money=1),
                ),
            ),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.YELLOW:
        faces = [
            Face(name="+$3", money=3),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔬", money=1, patches=1),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)

    elif color == DieColor.PURPLE:
        star_face = Face(
            name="Purple ★",
            is_star=True,
            star_code="PURPLE_STAR",
        )
        faces = [
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔬", money=1, patches=1),
            glitch_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code="PURPLE_STAR")

    raise ValueError(f"Unsupported die color: {color}")


SECRET_FACE = Face(name="Secret", secrets_pending=True)
CLEAN_SLOT_NAME = "Clean 1 Glitched Shield Slot"


def _choice(a: Face, b: Face) -> Face:
    return Face(name=f"{a.name} / {b.name}", is_choice=True, choices=(a, b))


V038D_V1_STAGING_PAYLOAD: Dict[str, Dict[CubeColor, int]] = {
    "SCRIPT_KIDDIE": {CubeColor.RED: 2, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
    "DATA_SCRAPER": {CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.GREEN: 1},
}


def _create_colored_die_v038(color: DieColor, die_id: int, variant_card: Optional[VariantCard], star_face: Face,
                             var_code: Optional[str], die_cost: int, profile: str = "V038_DRAFT") -> Die:
    """spec v380 §4.2 ``V038_DRAFT`` tables [TUNE]."""
    if color == DieColor.RED:
        faces = [_choice(Face("+1 Market Share", market_share=1), Face("+$1", money=1)),
                 Face(name="+$2", money=2), Face(name="+$2", money=2), Face(name="+$2", money=2),
                 SECRET_FACE, star_face]
    elif color == DieColor.BLUE:
        if profile == "V038F":
            faces = [
                Face(name="+1 Corporate Secret", secrets=1),
                Face(name="+1 Corporate Secret", secrets=1),
                Face(name="+$1", money=1),
                _choice(Face("+1 🔬", patches=1), Face("+$1", money=1)),
                SECRET_FACE,
                star_face,
            ]
        else:
            faces = [Face(name="+1 🔬", patches=1), Face(name="+1 🔬", patches=1), Face(name="+$1", money=1),
                     _choice(Face("+1 🔬", patches=1), Face("+$1", money=1)), SECRET_FACE, star_face]
    elif color == DieColor.GREEN:
        f1 = (Face(name="+2 🔬", patches=2) if profile in ("V038D", "V038F")
              else _choice(Face(CLEAN_SLOT_NAME, clean_slots=1), Face("+$1", money=1)))
        faces = [f1,
                 Face(name="+1 🔬", patches=1), Face(name="+2 🔬", patches=2),
                 _choice(Face("+1 🔬", patches=1), Face("+$1", money=1)), SECRET_FACE, star_face]
    elif color == DieColor.YELLOW and profile in ("V038_YELLOW_MS", "V038_YELLOW_MS_ALT", "V038_YELLOW_MS_F3", "V038D", "V038F"):
        y = lambda: _choice(Face("+$2", money=2), Face("+1 🔬", patches=1))  # noqa: E731
        f1 = (Face(name="+$1 & +1 Market Share", money=1, market_share=1) if profile == "V038_YELLOW_MS_ALT"
              else Face(name="+2 Market Share", market_share=2))
        # RSP-1 (spec §14.5.1): _F3 / V038D swaps F3 "+$3" for "+$1 & +1 Market Share"
        f3 = (Face(name="+$1 & +1 Market Share", money=1, market_share=1) if profile in ("V038_YELLOW_MS_F3", "V038D", "V038F")
              else Face(name="+$3", money=3))
        faces = [f1, _choice(Face("+1 Market Share", market_share=1), Face("+1 🔬", patches=1)),
                 f3, y(), y(), star_face]
    elif color == DieColor.YELLOW:
        y = lambda: _choice(Face("+$2", money=2), Face("+1 🔬", patches=1))  # noqa: E731
        faces = [Face(name="+$3", money=3), y(), y(), Face(name="+$1 & +1 🔬", money=1, patches=1), y(), star_face]
    elif color == DieColor.PURPLE:
        faces = [Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
                 Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
                 Face(name="+$2", money=2), Face(name="+$1 & +1 🔬", money=1, patches=1), SECRET_FACE,
                 Face(name="Purple ★", is_star=True, star_code="PURPLE_STAR")]
        return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code="PURPLE_STAR")
    else:
        raise ValueError(f"Unsupported die color: {color}")
    return Die(die_id=die_id, color=color, cost=die_cost, vp=0, faces=faces, variant_code=var_code)


def _v038_star(card: VariantCard, description: str, **face_kw: Any) -> VariantCard:
    face = dataclasses.replace(card.star_face, block_amount=0, shield_color=None, **face_kw)
    return dataclasses.replace(card, description=description, star_face=face)


def apply_variant_profile(variant_cards: Dict[DieColor, VariantCard], profile: Optional[str]) -> Dict[DieColor, VariantCard]:
    """spec v380 §5: ``V038_DRAFT`` Variant Card texts (costs unchanged; every colour-specific Block removed).
    ``"V037"`` returns the mapping unchanged (same object)."""
    if profile != "V038_DRAFT":
        return variant_cards
    out = dict(variant_cards)
    for color, card in variant_cards.items():
        code = card.code
        if code == "R1":
            out[color] = _v038_star(card, "Gain +$2 and +1 Market Share.", money=2, market_share=1)
        elif code == "B1":
            out[color] = _v038_star(card, "Gain +1 🔬; if 1+ Blue cubes exit the tower and you take 0 Blue damage in "
                                          "Phase 4, gain +$2 (this die must still be In Production).", patches=1)
        elif code == "B2":
            out[color] = _v038_star(card, "Pay $4 during Phase 6: Operations to gain +1 Corporate Secret.")
        elif code == "B3":
            out[color] = _v038_star(card, "In Phase 3: Income, move 1 die from your Processing Box to your Scanned "
                                          "Box (banking its Secret).")
        elif code == "G1":
            out[color] = _v038_star(card, f"{CLEAN_SLOT_NAME} and gain +1 🔬.", patches=1, clean_slots=1)
        elif code == "G2":
            out[color] = _v038_star(
                card,
                "Gain +2 🔬, plus +1 🔬 for each of your Glitched Shield Slots.",
                patches=2,
                clean_slots=0,
            )
        elif code == "Y3":
            out[color] = dataclasses.replace(
                card, description="Gain +1 Corporate Secret, then move this die to the Scanned Box.")
    return out


# =====================================================================
# Identity checks (v0.34.0): Institutional Overrides come ONLY from the Client Company and Signature
# Protocols ONLY from the White Hat Dossier. v0.33 granted each White Hat its paired company's override
# (and vice versa) through the legacy ``PlayerState.archetype`` bridge; that behaviour is reproduced only
# when ``GameConfig.legacy_archetype_override_bridge`` is True (set by ``GameConfig.legacy_v033()``).
# =====================================================================
_COMPANY_TO_LEGACY_ARCHETYPE = {
    CompanyCode.MERIDIAN: ArchetypeCode.OPERATOR,
    CompanyCode.OMNIDYNE: ArchetypeCode.PHREAKER,
    CompanyCode.AEGIS: ArchetypeCode.ACOUSTIC,
    CompanyCode.DTO: ArchetypeCode.SPOOK,
    CompanyCode.HELIX: ArchetypeCode.PRODIGY,
    CompanyCode.PROMETHEUS: ArchetypeCode.CIPHER,
}


def legacy_bridge_enabled(ctx: Any) -> bool:
    """Reads ``legacy_archetype_override_bridge`` from a config, engine, game state or web controller."""
    cfg = getattr(ctx, "config", None)
    if cfg is None:
        st = getattr(ctx, "state", None)
        cfg = getattr(st, "config", None)
    return bool(getattr(cfg, "legacy_archetype_override_bridge", False))


def has_company_override(player: Any, company_code: CompanyCode, bridge: bool = False) -> bool:
    """True if the player's Client Company is ``company_code`` (legacy bridge: or the paired archetype)."""
    comp = getattr(player, "company", None)
    if comp is not None and comp.code == company_code:
        return True
    if bridge:
        arch = player.archetype
        return bool(arch and arch.code == _COMPANY_TO_LEGACY_ARCHETYPE[company_code])
    return False


def has_signature_protocol(player: Any, white_hat_code: WhiteHatCode, bridge: bool = False) -> bool:
    """True if the player's White Hat Operative is ``white_hat_code`` (legacy bridge: or the archetype)."""
    wh = getattr(player, "white_hat", None)
    if wh is not None and wh.code == white_hat_code:
        return True
    if bridge:
        arch = player.archetype
        return bool(arch and arch.code == ArchetypeCode(white_hat_code.value))
    return False
