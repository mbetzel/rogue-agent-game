"""Entities: Dice, Faces, Variant Cards, and Version Cards for Rogue Agent."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sim.config import CubeColor, DieColor, ShieldColor


class ArchetypeCode(str, Enum):
    """Enumeration of the 6 consultancy archetypes per RULES.md Section 6D."""

    ACOUSTIC = "ACOUSTIC"
    PHREAKER = "PHREAKER"
    PRODIGY = "PRODIGY"
    SPOOK = "SPOOK"
    CIPHER = "CIPHER"
    OPERATOR = "OPERATOR"


class AbilityStatus(str, Enum):
    """Lifecycle status of once-per-version archetype special abilities."""

    LOCKED = "LOCKED"
    AVAILABLE = "AVAILABLE"
    USED = "USED"
    FORFEITED = "FORFEITED"


@dataclass(frozen=True)
class ArchetypeCard:
    """Represents a consultancy archetype card with once-per-version ability."""

    code: ArchetypeCode
    name: str
    timing_window: str
    ability_name: str
    description: str


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
    vp: int
    faces: List[Face]
    current_face: Optional[Face] = None
    variant_code: Optional[str] = None
    is_locked: bool = False
    chosen_choice_index: Optional[int] = None

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


@dataclass(frozen=True)
class VersionCard:
    """Represents a Rogue Agent roadmap version card (v1.0, v2.0, or v3.0)."""

    version_str: str  # "v1.0", "v2.0", "v3.0"
    name: str
    staging_payload: Dict[CubeColor, int]
    directive_description: str
    directive_code: str  # SCRIPT_KIDDIE, DATA_SCRAPER, RAAS, POLYMORPHIC_WORM, ZERO_DAY_OVERRIDE, CORRUPTED_KERNEL
    staging_payload_2p: Optional[Dict[CubeColor, int]] = None

    def get_staging_payload(self, num_players: int = 4) -> Dict[CubeColor, int]:
        """Returns the version's staging payload cubes scaled for player count (2P vs 3P/4P)."""
        if num_players == 2 and self.staging_payload_2p is not None:
            return dict(self.staging_payload_2p)
        return dict(self.staging_payload)


# =====================================================================
# Factory Functions & Appendix Definitions
# =====================================================================

def get_all_variant_cards() -> Dict[str, VariantCard]:
    """Returns a dictionary of all 15 prototype Variant Cards (R1-R3, B1-B3, G1-G3, Y1-Y3, P1-P3)."""
    cards = [
        # Red ★ Variants
        VariantCard(
            code="R1",
            name="Ransom Insurance",
            die_color=DieColor.RED,
            description="Block 1 Red + gain +$2.",
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
            description="Block 2 Red; if you take 0 unblocked Red damage this round, gain +$2.",
            star_face=Face(
                name="R2: Threat Bounty",
                block_amount=2,
                shield_color=ShieldColor.RED,
                money=0,  # Bonus handled conditionally in Phase 2
                is_star=True,
                star_code="R2",
            ),
        ),
        VariantCard(
            code="R3",
            name="Short Squeeze",
            die_color=DieColor.RED,
            description="Gain +$3 (or +$4 if 3+ Red cubes exit the tower this round).",
            star_face=Face(
                name="R3: Short Squeeze",
                block_amount=0,
                money=3,  # Base $3 in P1, +$1 bonus checked in Phase 2 if exited Red >= 3
                is_star=True,
                star_code="R3",
            ),
        ),
        # Blue ★ Variants
        VariantCard(
            code="B1",
            name="Honeypot Telemetry",
            die_color=DieColor.BLUE,
            description="Block 2 Blue; if 1+ Blue cubes exit the tower and you take 0 Blue damage, gain +$3.",
            star_face=Face(
                name="B1: Honeypot Telemetry",
                block_amount=2,
                shield_color=ShieldColor.BLUE,
                money=0,  # Bonus handled conditionally in Phase 2
                is_star=True,
                star_code="B1",
            ),
        ),
        VariantCard(
            code="B2",
            name="Deep R&D Vault",
            die_color=DieColor.BLUE,
            description="Block 1 Blue, OR pay $4 during Phase 3 to gain +1 Corporate Secret (max 10).",
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
            description="Block 1 Blue; when this die actively blocks, you may move 1 other Ready die of your choice to Unpatched instead of this die (if you have no other Ready dice, this die moves to Unpatched).",
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
            description="Block 2 Green + gain +1 🔧.",
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
            description="Block 1 Any + gain +1 🔧.",
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
            description="Gain +2 🔧 + +$1.",
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
            description="Gain +$4, OR pay $2 in Phase 3 to gain +1 Corporate Secret.",
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
            description="Gain +1 Corporate Secret, then move this die to Unpatched.",
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
            description="Gain +$2; in Phase 3 you may add 1 Attack Cube (Red/Blue/Green) to the Staging Cup.",
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
            description="Block 2 of any single color; in Phase 3 you may pay $1 to add 1 cube of that color from the supply to the Staging Cup.",
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
    """Returns the default baseline variant card (1 per colored die: R1, B1, G1, Y1, P1)."""
    all_cards = get_all_variant_cards()
    return {
        DieColor.RED: all_cards["R1"],
        DieColor.BLUE: all_cards["B1"],
        DieColor.GREEN: all_cards["G1"],
        DieColor.YELLOW: all_cards["Y1"],
        DieColor.PURPLE: all_cards["P1"],
    }


def get_random_variant_cards(rng: random.Random) -> Dict[DieColor, VariantCard]:
    """Randomly selects 1 Variant Card per colored die (Red, Blue, Green, Yellow, Purple)."""
    all_variants = list(get_all_variant_cards().values())
    chosen: Dict[DieColor, VariantCard] = {}
    for color in [
        DieColor.RED,
        DieColor.BLUE,
        DieColor.GREEN,
        DieColor.YELLOW,
        DieColor.PURPLE,
    ]:
        matching = [v for v in all_variants if v.die_color == color]
        chosen[color] = rng.choice(matching)
    return chosen


def get_all_version_cards() -> List[VersionCard]:
    """Returns all 6 sample Version cards from RULES.md."""
    return [
        VersionCard(
            version_str="v1.0",
            name="Script Kiddie",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1},
            directive_description="None.",
            directive_code="SCRIPT_KIDDIE",
        ),
        VersionCard(
            version_str="v1.0",
            name="Data Scraper",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2, CubeColor.BLACK: 1},
            directive_description="Players start with +$1 extra Money.",
            directive_code="DATA_SCRAPER",
        ),
        VersionCard(
            version_str="v2.0",
            name="Ransomware-as-a-Service",
            staging_payload={CubeColor.RED: 1, CubeColor.GREEN: 1},
            directive_description="Encrypted Memory: Any rolled die showing Cash (+$1 or +$2) is Locked immediately.",
            directive_code="RAAS",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.GREEN: 1},
        ),
        VersionCard(
            version_str="v2.0",
            name="Polymorphic Worm",
            staging_payload={CubeColor.GREEN: 1, CubeColor.BLACK: 1},
            directive_description="Subroutine Throttling: Players receive only 1 free reroll in Phase 1 (instead of 2).",
            directive_code="POLYMORPHIC_WORM",
            staging_payload_2p={CubeColor.GREEN: 1, CubeColor.BLACK: 1},
        ),
        VersionCard(
            version_str="v3.0",
            name="Zero-Day Override",
            staging_payload={CubeColor.RED: 1, CubeColor.BLACK: 1},
            directive_description="Kernel Lock: Any rolled die showing a Shield (Block 1 or Block 2) is Locked immediately.",
            directive_code="ZERO_DAY_OVERRIDE",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.BLACK: 1},
        ),
        VersionCard(
            version_str="v3.0",
            name="Corrupted Kernel",
            staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1},
            directive_description="If 2+ Black Cubes exit the tower this round, the Attack Color with the most exited cubes gains +2 Strength total.",
            directive_code="CORRUPTED_KERNEL",
            staging_payload_2p={CubeColor.RED: 1, CubeColor.BLUE: 1},
        ),
    ]


def get_default_version_deck() -> List[VersionCard]:
    """Returns the default baseline version cards: Script Kiddie (v1.0), RaaS (v2.0), Zero-Day Override (v3.0)."""
    cards = get_all_version_cards()
    return [cards[0], cards[2], cards[4]]


def get_roadmap_deck(path_id: int) -> List[VersionCard]:
    """Returns a deterministic 3-card roadmap deck for a designated path ID (1-4).

    Path 1 (Kinetic): Script Kiddie (v1.0), RaaS (v2.0), Corrupted Kernel (v3.0)
    Path 2 (Contagion): Script Kiddie (v1.0), Polymorphic Worm (v2.0), Zero-Day Override (v3.0)
    Path 3 (Mixed A): Script Kiddie (v1.0), RaaS (v2.0), Zero-Day Override (v3.0)
    Path 4 (Mixed B): Script Kiddie (v1.0), Polymorphic Worm (v2.0), Corrupted Kernel (v3.0)
    """
    cards = {c.directive_code: c for c in get_all_version_cards()}
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


def get_random_version_deck(rng: random.Random) -> List[VersionCard]:
    """Randomly selects 1 v1.0 card, 1 v2.0 card, and 1 v3.0 card for the Rogue Agent roadmap."""
    all_versions = get_all_version_cards()
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
) -> Tuple[Dict[DieColor, VariantCard], List[VersionCard]]:
    """Returns randomized variant cards and version deck for game setup."""
    return get_random_variant_cards(rng), get_random_version_deck(rng)


# =====================================================================
# Consultancy Archetypes (RULES.md Section 6D)
# =====================================================================

def get_all_archetype_cards() -> List[ArchetypeCard]:
    """Returns all 6 consultancy archetype cards defined in RULES.md Section 6D."""
    return [
        ArchetypeCard(
            code=ArchetypeCode.ACOUSTIC,
            name="The Acoustic",
            timing_window="Phase 2: After Tower Drop",
            ability_name="Baffle Echo",
            description="If you take unblocked damage from any color, permanently remove 1 cube of that color in the exit tray from the game (return to box).",
        ),
        ArchetypeCard(
            code=ArchetypeCode.PHREAKER,
            name="The Phreaker",
            timing_window="Phase 3: Operations Turn",
            ability_name="Magnetic Splice",
            description="Move up to 2 worn dice from your Unpatched Zone back to your Ready Zone for free (without spending 🔧 or $).",
        ),
        ArchetypeCard(
            code=ArchetypeCode.PRODIGY,
            name="The Prodigy",
            timing_window="Phase 1: Reroll Step",
            ability_name="Brute-Force Bypass",
            description="During your rerolls this phase, you may include any number of Locked dice (including Glitch dice) in your free rerolls without spending 🔧 tokens.",
        ),
        ArchetypeCard(
            code=ArchetypeCode.SPOOK,
            name="The Spook",
            timing_window="Phase 2: Step 2B Damage",
            ability_name="Slush Fund",
            description="When suffering unblocked damage that would cause you to lose Corporate Secrets (from Blue Spyware or unpaid Red Ransom), pay $1 from your supply per Secret to prevent that loss (up to your available cash).",
        ),
        ArchetypeCard(
            code=ArchetypeCode.CIPHER,
            name="The Cipher",
            timing_window="Phase 3: Operations Turn",
            ability_name="Algorithmic Arbitrage",
            description="Purchase 1 Colored Die from the Market at a $2 discount (minimum cost $0), OR take the Backdoor Siphon (Dirty Income) action without demoting a Ready die to Unpatched.",
        ),
        ArchetypeCard(
            code=ArchetypeCode.OPERATOR,
            name="The Operator",
            timing_window="Phase 1: Staffing Step",
            ability_name="Redundant Crew",
            description="Hire up to 2 White Contractor Dice for free this round (bypassing progressive contractor costs).",
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


def create_gray_die(die_id: int) -> Die:
    """Creates a Gray (Legacy Code) starter die."""
    faces = [
        Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
        Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
        Face(name="+$1", money=1),
        Face(name="+$1", money=1),
        Face(
            name="+$1 / +1 🔧",
            is_choice=True,
            choices=(Face("+$1", money=1), Face("+1 🔧", patches=1)),
        ),
        Face(name="+1 🔧", patches=1),
    ]
    return Die(
        die_id=die_id,
        color=DieColor.GRAY,
        cost=0,
        vp=0,
        faces=faces,
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
) -> Die:
    """Creates a colored die of the specified color, applying the active Variant Card to faces 5 & 6."""
    if color == DieColor.GRAY:
        return create_gray_die(die_id)
    if color == DieColor.WHITE:
        return create_white_die(die_id)

    star_face = variant_card.star_face if variant_card else Face(name=f"{color.value} ★", is_star=True)
    var_code = variant_card.code if variant_card else None

    if color == DieColor.RED:
        faces = [
            Face(name="Block 2 Red", block_amount=2, shield_color=ShieldColor.RED),
            Face(name="Block 2 Red", block_amount=2, shield_color=ShieldColor.RED),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    elif color == DieColor.BLUE:
        faces = [
            Face(name="Block 2 Blue", block_amount=2, shield_color=ShieldColor.BLUE),
            Face(name="Block 2 Blue", block_amount=2, shield_color=ShieldColor.BLUE),
            Face(name="+$1", money=1),
            Face(
                name="Block 1 Blue / +1 🔧",
                is_choice=True,
                choices=(
                    Face("Block 1 Blue", block_amount=1, shield_color=ShieldColor.BLUE),
                    Face("+1 🔧", patches=1),
                ),
            ),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=5, vp=4, faces=faces, variant_code=var_code)

    elif color == DieColor.GREEN:
        faces = [
            Face(name="Block 2 Green", block_amount=2, shield_color=ShieldColor.GREEN),
            Face(name="Block 2 Green", block_amount=2, shield_color=ShieldColor.GREEN),
            Face(name="+2 🔧", patches=2),
            Face(
                name="+1 🔧 / +$1",
                is_choice=True,
                choices=(
                    Face("+1 🔧", patches=1),
                    Face("+$1", money=1),
                ),
            ),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    elif color == DieColor.YELLOW:
        faces = [
            Face(name="+$3", money=3),
            Face(name="+$2", money=2),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔧", money=1, patches=1),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=5, vp=4, faces=faces, variant_code=var_code)

    elif color == DieColor.PURPLE:
        faces = [
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="Block 1 Any", block_amount=1, shield_color=ShieldColor.ANY),
            Face(name="+$2", money=2),
            Face(name="+$1 & +1 🔧", money=1, patches=1),
            star_face,
            star_face,
        ]
        return Die(die_id=die_id, color=color, cost=4, vp=3, faces=faces, variant_code=var_code)

    raise ValueError(f"Unsupported die color: {color}")
