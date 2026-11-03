"""Master Print-and-Play PDF Generator for Too Many Secrets (Rogue Agent v0.26.0 Baseline).

Generates minimalist, ink-saver, print-ready US Letter (11" x 8.5") PDFs:
  - 01_Player_Boards.pdf (6 pages — 4x Consultancy Terminal Mats with empty modular card docks + 6x Client Company Cards sheet + 6x White Hat Dossier Cards sheet)
  - 02_Central_Game_Boards.pdf (2 pages — SETEC Agent Board matching Wireframe Page 2 + Market & Supply Board)
  - 03_Dice_Visual_Aids_and_Market_Cards.pdf (4 pages — Master Pip Aid, 4x Player Pocket Aids, 12x Variant ★ Cards)
  - 04_SETEC_Version_Cards_and_Tokens.pdf (2 pages — 6x SETEC Version Tiles sized to board slots + Cut-Out PnP Tokens)
  - 00_Too_Many_Secrets_Complete_PnP.pdf (All 14 pages combined in print order)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from pnp.illustrations import draw_character_illustration
from pnp.pdf_engine import PALETTE, Color, PDFDocument, PDFPage, measure_text


# =============================================================================
# Canonical Game Data (Synchronized 1:1 with RULES.md v0.26.0 & sim/entities.py)
# =============================================================================

@dataclass(frozen=True)
class CompanyCardSpec:
    code: str
    name: str
    sector: str
    override_name: str
    override_timing: str
    override_desc: str
    flavor: str


COMPANIES: List[CompanyCardSpec] = [
    CompanyCardSpec(
        code="MERIDIAN",
        name="Meridian Financial Trust",
        sector="Banking Infrastructure",
        override_name="Redundant Crew",
        override_timing="P1: STAFFING",
        override_desc=(
            "Hire up to **2 White Contractor Dice for free** this round, "
            "bypassing progressive contractor costs."
        ),
        flavor='"When liquidity is limitless, headcount is merely an accounting variable."',
    ),
    CompanyCardSpec(
        code="OMNIDYNE",
        name="Omnidyne Systems",
        sector="Tech Giant",
        override_name="Magnetic Splice",
        override_timing="P3: PIPELINE PREP",
        override_desc=(
            "Move **1 die** from your **Glitched Box** directly to your "
            "**Ready for Release Zone** for **free** (bypassing Scanned and saving {WRENCH})."
        ),
        flavor='"Proprietary hardware backplanes allow instantaneous hot-swapping under live load."',
    ),
    CompanyCardSpec(
        code="AEGIS",
        name="Aegis Defense Relay",
        sector="Security Firm",
        override_name="Baffle Echo",
        override_timing="P2: STEP 2B DMG",
        override_desc=(
            "When resolving compiler damage, ignore **1 Attack Cube** ({RED}, {BLUE}, or {GREEN}) "
            "of your choice for yourself this round. Exited cubes remain in tray and recycle as normal."
        ),
        flavor='"Multi-layered kinetic dampeners disperse inbound network blast energy."',
    ),
    CompanyCardSpec(
        code="DTO",
        name="Department of Telecom Oversight",
        sector="Federal Agency",
        override_name="Slush Fund",
        override_timing="P2: STEP 2B DMG",
        override_desc=(
            "The DTO accesses emergency black budget reserves: absorb up to **2 Corporate Secret loss** "
            "(from Blue Spyware or unpaid Red Ransom) for free without paying cash."
        ),
        flavor='"Classified black budget allocations absorb compliance failures without public oversight."',
    ),
    CompanyCardSpec(
        code="HELIX",
        name="Helix Biomedical Consortium",
        sector="Medical Research",
        override_name="Brute-Force Bypass",
        override_timing="P1: STEP 4 REROLLS",
        override_desc=(
            "During your rerolls this phase, you may include **any number of Locked dice** in "
            "your free rerolls without spending {WRENCH} tokens. In addition, turn **1 rolled die** to "
            "any legal non-Star face of choice."
        ),
        flavor='"Massively parallel quantum sequencing breaks deterministic encryption gates."',
    ),
    CompanyCardSpec(
        code="PROMETHEUS",
        name="The Prometheus Foundation",
        sector="Non-Profit",
        override_name="Algorithmic Arbitrage",
        override_timing="P3: OPERATIONS",
        override_desc=(
            "In Phase 3 Operations, purchase **1 Colored Die** from the Market or Personal "
            "Reserve at a **$2 discount** (min $0), **OR** gain an immediate **+$2 cash payout** "
            "from the bank."
        ),
        flavor='"Open-source cryptographic protocols circumvent proprietary enterprise licensing fees."',
    ),
]


@dataclass(frozen=True)
class WhiteHatDossierSpec:
    code: str
    name: str
    role: str
    reserve_cost_str: str
    flavor: str
    purple_faces: Tuple[str, str, str, str, str, str]
    protocol_name: str
    protocol_timing: str
    protocol_desc: str


WHITE_HATS: List[WhiteHatDossierSpec] = [
    WhiteHatDossierSpec(
        code="OPERATOR",
        name="The Operator",
        role="Tactical Staffing & Logistics Lead",
        reserve_cost_str="$5",
        flavor='"Redundant contractor pipelines ready on zero notice."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{PURPLE} {STAR}"),
        protocol_name="Contingent Staffing",
        protocol_timing="P1: STEP 4 ROLLING",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, immediately roll **1 free White Contractor Die** "
            "from supply directly into your active pool (eligible for remaining rerolls this phase)."
        ),
    ),
    WhiteHatDossierSpec(
        code="PHREAKER",
        name="The Phreaker",
        role="Hardware Intrusion Specialist",
        reserve_cost_str="$4",
        flavor='"Raw voltage pulses extract signal from dormant silicon."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{PURPLE} {STAR}"),
        protocol_name="Jumper Diagnostics",
        protocol_timing="P3: PART 3A OPS",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, select & roll **1 offline die** currently in your "
            "Glitched Box or Scanned Box; immediately collect rolled cash and patches "
            "(shields/glitches produce 0; die remains in place)."
        ),
    ),
    WhiteHatDossierSpec(
        code="ACOUSTIC",
        name="The Acoustic",
        role="Side-Channel Cryptanalyst",
        reserve_cost_str="$4",
        flavor='"Harmonic resonance frequencies decode physical chassis vibrations."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{PURPLE} {STAR}"),
        protocol_name="Resonance Sensor",
        protocol_timing="P3: PART 3A INCOME",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, gain **+$1 cash** per distinct cube color "
            "present in the Tower Exit Tray this round ({RED}, {BLUE}, {GREEN}, {BLACK}; max **+$4**)."
        ),
    ),
    WhiteHatDossierSpec(
        code="SPOOK",
        name="The Spook",
        role="Covert Intelligence Specialist",
        reserve_cost_str="$5",
        flavor='"Scorched-earth protocols ensure zero forensic recovery."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{PURPLE} {STAR}"),
        protocol_name="Burn Notice",
        protocol_timing="P3: PART 3A OPS",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, gain an immediate **+$2 cash payout**; "
            "in addition, you may optionally **permanently return 1 owned colored module die to the market** "
            "to gain **+1 Corporate Secret**."
        ),
    ),
    WhiteHatDossierSpec(
        code="PRODIGY",
        name="The Prodigy",
        role="Autonomous Exploit Hacker",
        reserve_cost_str="$5",
        flavor='"Payload injection executes before memory boundaries establish."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{PURPLE} {STAR}"),
        protocol_name="Arbitrary Code Execution",
        protocol_timing="P1: STEP 4 REROLLS",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, turn **1 other rolled die** in your active "
            "pool to **any legal non-Star face of that die's color**."
        ),
    ),
    WhiteHatDossierSpec(
        code="CIPHER",
        name="The Cipher",
        role="Distributed Ledger Architect",
        reserve_cost_str="$6",
        flavor='"Parity calculations balance zero-knowledge proofs flawlessly."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{PURPLE} {STAR}"),
        protocol_name="Algorithmic Parity",
        protocol_timing="P1: STEP 5 & P3: 3A",
        protocol_desc=(
            "**Phase 1 Step 5:** Purple Star acts as a **Wildcard** completing any rolled pair into "
            "a 3-of-a-kind triplet (**+1 Corporate Secret**).\n"
            "**Phase 3A Income:** Purple Star generates an additional **+$2 cash**."
        ),
    ),
]


@dataclass(frozen=True)
class DieSpec:
    color_key: str
    title: str
    subtitle: str
    cost_str: str
    faces: Tuple[str, str, str, str, str, str]
    notes: str


DICE_SPECS: List[DieSpec] = [
    DieSpec(
        color_key="gray",
        title="GRAY",
        subtitle="Legacy Code",
        cost_str="Starter (x4)",
        faces=("Block 1 Any", "Block 1 Any", "+$1", "+$1", "+$1 / +1 {WRENCH}", "+1 {WRENCH}"),
        notes="Starter pool (4 per player). Face 5 is a Choice (/): declare +$1 or +1 {WRENCH} in Step 5.",
    ),
    DieSpec(
        color_key="white",
        title="WHITE",
        subtitle="Contractor",
        cost_str="$1 / $2 / $3",
        faces=("Block 1 Any", "Block 1 Any", "Block 1 Any", "+$1", "{LOCK} Glitch", "{LOCK} Glitch"),
        notes="Temp hire (max 3/rd). Never wears; returns to supply after Phase 2. Can sacrifice vs {GREEN} Malware.",
    ),
    DieSpec(
        color_key="red",
        title="RED",
        subtitle="FinSec",
        cost_str="$5–$6 (by Variant)",
        faces=("Block 1 {RED}", "+$2", "+$2", "+$2", "{LOCK} Glitch", "{RED} {STAR}"),
        notes="FinSec revenue & defense. Face 5 Glitch (Locked), Face 6 Red {STAR}.",
    ),
    DieSpec(
        color_key="blue",
        title="BLUE",
        subtitle="Firewall",
        cost_str="$5–$7 (by Variant)",
        faces=("Block 1 {BLUE}", "+1 {WRENCH}", "+$1", "Block 1 {BLUE} / +1 {WRENCH}", "{LOCK} Glitch", "{BLUE} {STAR}"),
        notes="Spyware defense & patch hybrid. Face 5 Glitch (Locked), Face 6 Blue {STAR}.",
    ),
    DieSpec(
        color_key="green",
        title="GREEN",
        subtitle="Antivirus",
        cost_str="$5–$6 (by Variant)",
        faces=("Block 1 {GREEN}", "+1 {WRENCH}", "+2 {WRENCH}", "+1 {WRENCH} / +$1", "{LOCK} Glitch", "{GREEN} {STAR}"),
        notes="Malware defense & patch engine. Face 5 Glitch (Locked), Face 6 Green {STAR}.",
    ),
    DieSpec(
        color_key="yellow",
        title="YELLOW",
        subtitle="Commercial AI",
        cost_str="$6–$7 (by Variant)",
        faces=("+$3", "+$2", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{YELLOW} {STAR}"),
        notes="Commercial AI revenue. Face 5 Glitch (Locked), Face 6 Yellow {STAR}.",
    ),
    DieSpec(
        color_key="purple",
        title="PURPLE",
        subtitle="Specialist AI",
        cost_str="$4–$6 (by Operative)",
        faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{LOCK} Glitch", "{PURPLE} {STAR}"),
        notes="Standardized Any-shields & utility + Archetype Signature Protocol. Face 5 Glitch (Locked), Face 6 Purple {STAR}.",
    ),
]


@dataclass(frozen=True)
class VariantCardSpec:
    code: str
    color_key: str
    die_label: str
    cost_str: str
    base_summary_1: str
    base_summary_2: str
    name: str
    timing: str
    effect: str
    lock_note: str


VARIANT_CARDS: List[VariantCardSpec] = [
    # RED (R1-R3)
    VariantCardSpec(
        "R1", "red", "RED // FINSEC", "$6",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} {LOCK}Glitch  |  {PIP6} {STAR}",
        "Ransom Insurance", "P1 BOOT + P2 DEFENSE",
        "**Block 1 {RED} Red** in Phase 2 **AND** gain **+$2** in Phase 1 Boot.",
        "Locks in v2.0 RaaS & v3.0 Zero-Day.",
    ),
    VariantCardSpec(
        "R2", "red", "RED // FINSEC", "$6",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} {LOCK}Glitch  |  {PIP6} {STAR}",
        "Threat Bounty", "P2 DEFENSE + BONUS",
        "**Block 2 {RED} Red**; if you take **0 unblocked Red** damage this round, gain **+$2**.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "R3", "red", "RED // FINSEC", "$5",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} {LOCK}Glitch  |  {PIP6} {STAR}",
        "Short Squeeze", "P1 BOOT + P2 SURGE",
        "Gain **+$3** in Phase 1 (or **+$4** total if **3+ {RED} Red** cubes exit the tower in Phase 2).",
        "Locks in v2.0 RaaS (Cash).",
    ),
    # BLUE (B1-B3)
    VariantCardSpec(
        "B1", "blue", "BLUE // FIREWALL", "$6",
        "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Honeypot Telemetry", "P2 DEFENSE + BONUS",
        "**Block 2 {BLUE} Blue**; if **1+ {BLUE} Blue** cubes exit and you take **0 Blue** damage, gain **+$3**.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "B2", "blue", "BLUE // FIREWALL", "$7",
        "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Deep R&D Vault", "P2 DEF -OR- P3 OPS",
        "**Block 1 {BLUE} Blue**, **OR** leave unassigned to pay **$4** in Phase 3 for **+1 Secret**.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "B3", "blue", "BLUE // FIREWALL", "$5",
        "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Air-Gapped Backup", "P2 DEFENSE (REDIRECT)",
        "**Block 1 {BLUE} Blue**; when taking unblocked **Green Malware**, sacrifice **1 other Ready die** to Under Development instead of In Production.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    # GREEN (G1-G3)
    VariantCardSpec(
        "G1", "green", "GREEN // ANTIVIRUS", "$6",
        "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Self-Healing Kernel", "P1 BOOT + P2 DEFENSE",
        "**Block 2 {GREEN} Green** in Phase 2 **AND** gain **+1 {WRENCH}** in Phase 1 Boot.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "G2", "green", "GREEN // ANTIVIRUS", "$5",
        "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Universal Sandbox", "P1 BOOT + P2 DEFENSE",
        "**Block 1 Any** color in Phase 2 **AND** gain **+1 {WRENCH}** in Phase 1 Boot.",
        "Commit color in Step 5. Locks in v3.0.",
    ),
    VariantCardSpec(
        "G3", "green", "GREEN // ANTIVIRUS", "$5",
        "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Live Reboot", "P1 BOOT OUTPUT",
        "Gain **+2 {WRENCH}** and **+$1** immediately in Phase 1 Step 6.",
        "Locks in v2.0 RaaS (Cash).",
    ),
    # YELLOW (Y1-Y3)
    VariantCardSpec(
        "Y1", "yellow", "YELLOW // COMM. AI", "$7",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH} | {PIP5} {LOCK}Glitch",
        "Algorithmic Trading", "P1 INCOME + P3 OPTION",
        "Gain **+$4** in Phase 3; in Phase 3 you may also pay **$2** to gain **+1 Corporate Secret**.",
        "Locks in v2.0 RaaS (Cash).",
    ),
    VariantCardSpec(
        "Y2", "yellow", "YELLOW // COMM. AI", "$6",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH} | {PIP5} {LOCK}Glitch",
        "Cloud Monopoly", "P1 SCALING REVENUE",
        "Gain **+$2**, plus **+$1 per different colored** module die you own (**max +$5** total).",
        "Counts R/B/G/Y owned. Locks in v2.0 RaaS.",
    ),
    VariantCardSpec(
        "Y3", "yellow", "YELLOW // COMM. AI", "$6",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH} | {PIP5} {LOCK}Glitch",
        "Proprietary Training", "P1 SECRET + GLITCH",
        "Gain **+1 Corporate Secret** in Phase 1 Step 5, then immediately move **this die to Under Development (Glitched)**.",
        "Locks in v2.0 RaaS (Cash).",
    ),
]


@dataclass(frozen=True)
class VersionTrackSpaceSpec:
    num: int
    label: str
    is_milestone: bool = False
    is_singularity: bool = False


@dataclass(frozen=True)
class VersionTileSpec:
    version: str
    name: str
    profile: str
    banner_text: str
    spaces: Tuple[VersionTrackSpaceSpec, ...]


VERSION_TILES: List[VersionTileSpec] = [
    VersionTileSpec(
        version="v3.0",
        name="Zero-Day Override",
        profile="6 SPACES // SINGULARITY TIER",
        banner_text="**Kernel Lock:** Space 4 locks Shields next Phase 1. Final space triggers Singularity!",
        spaces=(
            VersionTrackSpaceSpec(1, "+1 {RED} 1 {BLUE} 1 {GREEN}"),
            VersionTrackSpaceSpec(2, "Lose $3 & 1 {WRENCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} +1 {BLUE}"),
            VersionTrackSpaceSpec(4, "Lock {SHIELD}\nNext P1 +1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Return 1\nColored Die"),
            VersionTrackSpaceSpec(6, "SINGULARITY!\n+2 {RED} 2 {BLUE} 2 {GREEN}", is_singularity=True),
        ),
    ),
    VersionTileSpec(
        version="v3.0",
        name="Corrupted Kernel",
        profile="6 SPACES // SINGULARITY TIER",
        banner_text="**Overclocked Surge:** 2+ Black: Lead Attack +2. Space 4 leaks 1 Secret.",
        spaces=(
            VersionTrackSpaceSpec(1, "Glitch 1 Die\n+1 {RED} 1 {BLUE}"),
            VersionTrackSpaceSpec(2, "Lose $3 & 1 {WRENCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} +1 {GREEN}"),
            VersionTrackSpaceSpec(4, "Lose 1 Secret\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Return 1\nColored Die"),
            VersionTrackSpaceSpec(6, "SINGULARITY!\nLose 1 Sec +2R 2B 1G", is_singularity=True),
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="Ransomware-as-a-Service",
        profile="5 SPACES // ESCALATION TIER",
        banner_text="**Encrypted Memory:** Space 3 locks Cash next Phase 1. Space 5 upgrades to v3.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "All Lose $2"),
            VersionTrackSpaceSpec(2, "+1 {RED} +1 {GREEN}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Lock Cash ($)\nNext P1"),
            VersionTrackSpaceSpec(4, "Lose $3 & 1 {WRENCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "UPGRADE v3.0\n+1 {RED}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="Polymorphic Worm",
        profile="5 SPACES // ESCALATION TIER",
        banner_text="**Subroutine Throttling:** 1 Free Reroll. Space 3 locks Patches next Phase 1.",
        spaces=(
            VersionTrackSpaceSpec(1, "Lose 2 {WRENCH}"),
            VersionTrackSpaceSpec(2, "+2 {GREEN}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Lock {WRENCH}\nNext P1"),
            VersionTrackSpaceSpec(4, "Glitch 1 Die\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "UPGRADE v3.0\n+1 {RED}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Script Kiddie",
        profile="4 SPACES // INITIAL TIER",
        banner_text="**Setup Staging Payload:** Add 1 {RED} 1 {BLUE} 1 {GREEN} to Staging Cup. Upgrade at space 4.",
        spaces=(
            VersionTrackSpaceSpec(1, "+1 {RED}"),
            VersionTrackSpaceSpec(2, "All Lose $2\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Lose 1 {WRENCH}"),
            VersionTrackSpaceSpec(4, "UPGRADE v2.0\nLose 1 {WRENCH}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Data Scraper",
        profile="4 SPACES // INITIAL TIER",
        banner_text="**Setup Staging Payload:** Add 1 {RED} 2 {BLUE} to Staging Cup. All players start with +$1.",
        spaces=(
            VersionTrackSpaceSpec(1, "Lose 1 {WRENCH}"),
            VersionTrackSpaceSpec(2, "Lose $1\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {GREEN}"),
            VersionTrackSpaceSpec(4, "UPGRADE v2.0\nGlitch 1 Die", is_milestone=True),
        ),
    ),
]


# =============================================================================
# Helper UI Primitives
# =============================================================================

def _color_pair(color_key: str) -> Tuple[Color, Color]:
    k = color_key.lower()
    if k == "red":
        return PALETTE["red"], PALETTE["red_light"]
    if k == "blue":
        return PALETTE["blue"], PALETTE["blue_light"]
    if k == "green":
        return PALETTE["green"], PALETTE["green_light"]
    if k == "yellow":
        return PALETTE["yellow"], PALETTE["yellow_light"]
    if k == "purple":
        return PALETTE["purple"], PALETTE["purple_light"]
    if k == "black":
        return PALETTE["black"], PALETTE["black_light"]
    if k == "gray":
        return PALETTE["gray"], PALETTE["gray_light"]
    return PALETTE["ink"], PALETTE["white"]


def draw_board_outer_frame(page: PDFPage, left_tag: str, right_tag: str) -> None:
    """Draw outer minimalist terminal frame across US Letter Landscape safe zone."""
    x, y, w, h = 28.0, 22.0, 736.0, 568.0
    page.rect(x, y, w, h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.4)
    page.corner_ticks(x - 3, y - 3, w + 6, h + 6, size=6.0, color=PALETTE["ink"])
    # Subtle micro-telemetry above outer frame
    page.text(x, y - 5, left_tag, font="mono_bold", size=6.5, color=PALETTE["muted"])
    page.text(x + w, y - 5, right_tag, font="mono", size=6.5, color=PALETTE["muted"], align="right")


# =============================================================================
# 1. Individual Player Boards & Modular Cards (Pages 1-6)
# =============================================================================

def _draw_company_card(page: PDFPage, x: float, y: float, w: float, h: float, comp: CompanyCardSpec, is_dock: bool = False) -> None:
    """Render a single Client Company card (w ~ 238, h ~ 210) with sector, flavor, override, and 3 version slots."""
    # Outer Card Frame
    page.rect(x, y, w, h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)

    # 1. Header Strip (y..y+18)
    page.rect(x, y, w, 18.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    dock_tag = " [MODULAR DOCK]" if is_dock else ""
    page.text(x + 6.0, y + 12.0, f"CLIENT COMPANY CARD{dock_tag}", font="mono_bold", size=6.0, color=PALETTE["ink"])
    page.text(x + w - 6.0, y + 12.0, comp.sector.upper(), font="mono_bold", size=5.8, color=PALETTE["ink_soft"], align="right")

    # 2. Company Name (y+20..y+34)
    page.text(x + w / 2.0, y + 30.5, comp.name.upper(), font="bold", size=10.2, color=PALETTE["ink"], align="center")

    # 3. Flavor Quote Box (y+36..y+60, h=24)
    fy, fh = y + 36.0, 24.0
    page.rect(x + 6.0, fy, w - 12.0, fh, stroke=PALETTE["guide"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_paragraph(
        x + 10.0, fy + 8.0, w - 20.0,
        f"*{comp.flavor}*",
        size=5.9, leading=7.6, color=PALETTE["ink_soft"], align="center",
    )

    # 4. Once-Per-Version Institutional Override Box (y+64..y+184, h=120)
    o_y, o_h = y + 64.0, 120.0
    page.rect(x + 6.0, o_y, w - 12.0, o_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.85)

    # Sub-header strip with Override Name & Timing Pill
    page.rect(x + 6.0, o_y, w - 12.0, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.text(x + 10.0, o_y + 11.2, f"1x/VER: {comp.override_name.upper()}", font="bold", size=7.2, color=PALETTE["ink"])

    tw = measure_text(comp.override_timing, font="mono_bold", size=5.6) + 6.0
    page.rounded_rect(x + w - 10.0 - tw, o_y + 2.5, tw, 11.0, r=2.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.55)
    page.text(x + w - 10.0 - tw / 2.0, o_y + 10.2, comp.override_timing, font="mono_bold", size=5.6, color=PALETTE["ink"], align="center")

    # Override Description Paragraph
    page.rich_paragraph(
        x + 10.0, o_y + 24.0, w - 20.0,
        comp.override_desc,
        size=6.6, leading=8.8, color=PALETTE["ink"],
    )

    # Version Check Boxes Track (y+142..y+178)
    ty = o_y + o_h - 32.0
    page.line(x + 10.0, ty, x + w - 10.0, ty, stroke=PALETTE["rule"], width=0.5, dash=(2, 1.5))
    page.text(x + 10.0, ty + 12.0, "ONCE / VER:", font="mono_bold", size=5.6, color=PALETTE["ink_soft"])

    slots = ["v1.0", "v2.0", "v3.0"]
    sx_start = x + 58.0
    sw_box = 44.0
    for s_idx, ver_lbl in enumerate(slots):
        bx = sx_start + s_idx * (sw_box + 4.0)
        page.rounded_rect(bx, ty + 2.5, sw_box, 14.0, r=2.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
        page.rect(bx + 3.0, ty + 5.0, 9.0, 9.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.6)
        page.text(bx + 15.0, ty + 12.0, ver_lbl, font="mono_bold", size=6.2, color=PALETTE["ink"])

    page.text(x + w / 2.0, o_y + o_h - 4.5, "Unused charge forfeits upon SETEC upgrade.", font="italic", size=5.0, color=PALETTE["muted"], align="center")

    # 5. Bottom Card Footer (y+188..y+206)
    page.line(x + 6.0, y + 192.0, x + w - 6.0, y + 192.0, stroke=PALETTE["guide"], width=0.5)
    page.text(x + 8.0, y + 203.0, f"REF: COMP-{comp.code}", font="mono", size=5.2, color=PALETTE["muted"])
    page.text(x + w - 8.0, y + 203.0, "SLIPS FLUSH BESIDE TERMINAL MAT", font="mono", size=4.8, color=PALETTE["muted"], align="right")


def _draw_white_hat_card(page: PDFPage, x: float, y: float, w: float, h: float, white_hat: WhiteHatDossierSpec, is_dock: bool = False) -> None:
    """Render a single White Hat Operative dossier card (w ~ 238, h ~ 210) with role, purple die breakdown, and protocol."""
    # Outer Card Frame
    page.rect(x, y, w, h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=1.0)

    # 1. Header Strip (y..y+18)
    page.rect(x, y, w, 18.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.8)
    page.rect(x, y, w, 2.5, stroke=None, fill=PALETTE["purple"])
    page.draw_color_badge(x + 9.0, y + 10.0, 5.0, "purple")
    dock_tag = " [MODULAR DOCK]" if is_dock else ""
    page.text(x + 19.0, y + 12.0, f"WHITE HAT DOSSIER{dock_tag}", font="bold", size=6.2, color=PALETTE["purple"])
    # Prominent Procurement Cost Pill in Header
    cost_pill_w = 46.0
    cost_pill_x = x + w - 46.0 - 52.0
    page.rounded_rect(cost_pill_x, y + 3.0, cost_pill_w, 12.0, r=2.0, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.6)
    page.rich_line(cost_pill_x + cost_pill_w / 2.0, y + 11.2, f"**DICE: {white_hat.reserve_cost_str}**", size=5.4, color=PALETTE["purple"], align="center")
    page.text(x + w - 6.0, y + 12.0, f"REF: WH-{white_hat.code}", font="mono_bold", size=5.2, color=PALETTE["purple"], align="right")

    # 2. Operative Name & Tactical Role (y+20..y+40)
    page.text(x + w / 2.0, y + 29.5, white_hat.name.upper(), font="bold", size=10.5, color=PALETTE["ink"], align="center")
    page.text(x + w / 2.0, y + 38.5, white_hat.role.upper(), font="mono_bold", size=5.8, color=PALETTE["purple"], align="center")

    # 3. Purple Die Face Reference Breakdown Strip (y+42..y+69, h=27)
    f_y, f_h = y + 42.0, 27.0
    page.rect(x + 6.0, f_y, w - 12.0, f_h, stroke=PALETTE["purple"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.text(x + 9.0, f_y + 8.5, f"PURPLE SPECIALIST DIE FACES (d6 // Procure: {white_hat.reserve_cost_str} in Reserve):", font="mono_bold", size=4.8, color=PALETTE["purple"])

    cell_y = f_y + 11.5
    cell_h = 12.5
    cell_w = (w - 12.0 - 8.0 - 4 * 3.0) / 5.0
    labels = [
        "1-2: Any Shield",
        "3: +$2 Cash",
        "4: +$1 & 1 🔧",
        "5: {LOCK} Glitch",
        "6: {PURPLE} {STAR}",
    ]
    for c_i, lbl in enumerate(labels):
        cx_i = x + 10.0 + c_i * (cell_w + 3.0)
        c_fill = PALETTE["purple_light"] if c_i == 4 else PALETTE["white"]
        page.rounded_rect(cx_i, cell_y, cell_w, cell_h, r=1.5, stroke=PALETTE["purple"], fill=c_fill, line_width=0.45)
        page.rich_line(cx_i + cell_w / 2.0, cell_y + 9.0, lbl, size=4.7, color=PALETTE["purple"] if c_i == 4 else PALETTE["ink"], align="center")

    # 4. Purple ★ Signature Protocol Box (y+72..y+174, h=102)
    s_y, s_h = y + 72.0, 102.0
    page.rect(x + 6.0, s_y, w - 12.0, s_h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.85)

    # Sub-header strip with Protocol Name & Timing Pill
    page.rect(x + 6.0, s_y, w - 12.0, 16.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.6)
    page.text(x + 10.0, s_y + 11.2, f"PURPLE STAR: {white_hat.protocol_name.upper()}", font="bold", size=7.0, color=PALETTE["purple"])

    tw_s = measure_text(white_hat.protocol_timing, font="mono_bold", size=5.5) + 6.0
    page.rounded_rect(x + w - 10.0 - tw_s, s_y + 2.5, tw_s, 11.0, r=2.0, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.55)
    page.text(x + w - 10.0 - tw_s / 2.0, s_y + 10.2, white_hat.protocol_timing, font="mono_bold", size=5.5, color=PALETTE["purple"], align="center")

    # Protocol Description
    page.rich_paragraph(
        x + 10.0, s_y + 24.0, w - 20.0,
        white_hat.protocol_desc,
        size=6.5, leading=8.6, color=PALETTE["ink"],
    )

    # Repeatable Star Notice at bottom of protocol box
    page.line(x + 10.0, s_y + s_h - 15.0, x + w - 10.0, s_y + s_h - 15.0, stroke=PALETTE["purple_light"], width=0.5)
    page.text(x + w / 2.0, s_y + s_h - 5.5, "Repeatable: Triggers whenever rolling Purple Face 6 ({STAR}).", font="italic", size=5.2, color=PALETTE["purple"], align="center")

    # 5. Flavor Text Box (y+177..y+203, h=26)
    fy, fh = y + 177.0, 26.0
    page.rect(x + 6.0, fy, w - 12.0, fh, stroke=PALETTE["guide"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_paragraph(
        x + 10.0, fy + 8.0, w - 20.0,
        f"*{white_hat.flavor}*",
        size=5.8, leading=7.4, color=PALETTE["ink_soft"], align="center",
    )

    # Bottom Tag
    page.text(x + 8.0, y + 208.0, "SLIPS FLUSH BESIDE TERMINAL MAT", font="mono", size=4.5, color=PALETTE["muted"])
    page.text(x + w - 8.0, y + 208.0, f"2x PURPLE SPECIALIST DICE ({white_hat.reserve_cost_str} EA IN RESERVE)", font="mono", size=4.5, color=PALETTE["purple"], align="right")


def _draw_empty_company_card_slot(page: PDFPage, x: float, y: float, w: float, h: float, idx: int = 1) -> None:
    """Render an empty docking slot for the Client Company Card (w ~ 238, h ~ 210)."""
    # Outer Card Dock Frame
    page.rect(x, y, w, h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)

    # 1. Header Strip (y..y+18)
    page.rect(x, y, w, 18.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(x + 6.0, y + 12.0, "CLIENT COMPANY CARD [MODULAR DOCK]", font="mono_bold", size=6.0, color=PALETTE["ink"])
    page.text(x + w - 6.0, y + 12.0, "ONCE / VER OVERRIDE", font="mono_bold", size=5.6, color=PALETTE["ink_soft"], align="right")

    # Inset dashed placement guide matching 3.30" x 2.92" cut card
    page.rect(x + 4.0, y + 21.0, w - 8.0, h - 25.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.75, dash=(3.0, 2.0))
    page.corner_ticks(x + 4.0, y + 21.0, w - 8.0, h - 25.0, size=6.0, color=PALETTE["ink_soft"])

    # Center Slot Callout
    page.text(x + w / 2.0, y + 36.0, "SLOT CLIENT COMPANY CARD HERE", font="bold", size=8.5, color=PALETTE["ink"], align="center")
    page.text(x + w / 2.0, y + 46.0, "3.30\" x 2.92\" Modular Card  |  Cut from Sheet [Page 5]", font="mono", size=5.4, color=PALETTE["ink_soft"], align="center")

    page.line(x + 16.0, y + 51.0, x + w - 16.0, y + 51.0, stroke=PALETTE["rule"], width=0.5, dash=(2.0, 1.5))

    # Rules Summary Box
    by = y + 54.0
    bw = w - 16.0
    bh = 94.0
    page.rounded_rect(x + 8.0, by, bw, bh, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.75)
    page.rect(x + 8.0, by, bw, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.text(x + 12.0, by + 10.0, "ROLE 1: CLIENT CONTRACTOR RULES", font="mono_bold", size=5.6, color=PALETTE["ink"])
    page.text(x + bw + 4.0, by + 10.0, "1 CARD / PLAYER", font="mono_bold", size=5.2, color=PALETTE["ink_soft"], align="right")

    rules_text = (
        "**1. Contract Assignment:** Draw 1 Client Company at setup and slot flush into this dock.\n"
        "**2. Institutional Override:** Each company grants 1 powerful override per SETEC Version (**v1.0**, **v2.0**, **v3.0**).\n"
        "**3. Use-It-or-Lose-It:** Must activate before SETEC advances in Step 2A (unspent charges forfeit upon upgrade).\n"
        "**4. Immediate Unlock:** Upgraded version override unlocks immediately upon compiler advancement."
    )
    page.rich_paragraph(x + 12.0, by + 23.0, bw - 8.0, rules_text, size=5.6, leading=7.6, color=PALETTE["ink"])

    intro_comps = [
        "Meridian Financial Trust (COMP-01)",
        "Omnidyne Systems (COMP-02)",
        "Aegis Defense Relay (COMP-03)",
        "Dept of Telecom Oversight (COMP-04)",
    ]
    comp_preset = intro_comps[idx - 1] if 1 <= idx <= len(intro_comps) else "Open Assignment"
    page.line(x + 12.0, by + bh - 14.0, x + 8.0 + bw - 4.0, by + bh - 14.0, stroke=PALETTE["rule"], width=0.5, dash=(2.0, 1.5))
    page.rich_line(x + w / 2.0, by + bh - 5.0, f"**Intro Preset (Optional):** {comp_preset}", size=5.2, color=PALETTE["ink_soft"], align="center")

    # Slotted Card Track Mockup
    ty = y + 152.0
    page.text(x + 10.0, ty + 10.0, "SLOTTED CARD TRACK:", font="mono_bold", size=5.3, color=PALETTE["ink_soft"])
    page.text(x + w - 10.0, ty + 10.0, "3 VERSION SLOTS", font="mono", size=5.0, color=PALETTE["muted"], align="right")
    slots = ["v1.0", "v2.0", "v3.0"]
    sx_start = x + 10.0
    sw_box = (w - 20.0 - 2 * 4.0) / 3.0
    for s_idx, ver_lbl in enumerate(slots):
        bx_s = sx_start + s_idx * (sw_box + 4.0)
        page.rounded_rect(bx_s, ty + 13.0, sw_box, 15.0, r=2.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.5, dash=(2.0, 1.5))
        page.rect(bx_s + 4.0, ty + 16.0, 9.0, 9.0, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.5)
        page.text(bx_s + 17.0, ty + 23.0, f"{ver_lbl} [Ready]", font="mono_bold", size=5.4, color=PALETTE["muted"])

    # Bottom Tag
    page.line(x + 8.0, y + 193.0, x + w - 8.0, y + 193.0, stroke=PALETTE["rule"], width=0.5)
    page.text(x + 8.0, y + 203.0, "SLIPS FLUSH BESIDE MAT", font="mono", size=4.6, color=PALETTE["muted"])
    page.text(x + w - 8.0, y + 203.0, "6 ENTERPRISE CLIENTS (PAGE 5)", font="mono", size=4.6, color=PALETTE["muted"], align="right")


def _draw_empty_white_hat_slot(page: PDFPage, x: float, y: float, w: float, h: float, idx: int = 1) -> None:
    """Render an empty docking slot for the White Hat Dossier (w ~ 238, h ~ 210)."""
    # Outer Card Dock Frame
    page.rect(x, y, w, h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=1.0)

    # 1. Header Strip (y..y+18)
    page.rect(x, y, w, 18.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.8)
    page.rect(x, y, w, 2.5, stroke=None, fill=PALETTE["purple"])
    page.draw_color_badge(x + 9.0, y + 10.0, 5.0, "purple")
    page.text(x + 19.0, y + 12.0, "WHITE HAT DOSSIER [MODULAR DOCK]", font="bold", size=6.2, color=PALETTE["purple"])
    page.text(x + w - 6.0, y + 12.0, "TACTICAL ROLE & PROTOCOL", font="mono_bold", size=5.6, color=PALETTE["purple"], align="right")

    # Inset dashed placement guide matching 3.30" x 2.92" cut card
    page.rect(x + 4.0, y + 21.0, w - 8.0, h - 25.0, stroke=PALETTE["purple_light"], fill=PALETTE["paper_tint"], line_width=0.75, dash=(3.0, 2.0))
    page.corner_ticks(x + 4.0, y + 21.0, w - 8.0, h - 25.0, size=6.0, color=PALETTE["purple"])

    # Center Slot Callout
    page.text(x + w / 2.0, y + 36.0, "SLOT WHITE HAT DOSSIER HERE", font="bold", size=8.5, color=PALETTE["purple"], align="center")
    page.text(x + w / 2.0, y + 46.0, "3.30\" x 2.92\" Modular Card  |  Cut from Sheet [Page 6]", font="mono", size=5.4, color=PALETTE["purple"], align="center")

    page.line(x + 16.0, y + 51.0, x + w - 16.0, y + 51.0, stroke=PALETTE["purple_light"], width=0.5, dash=(2.0, 1.5))

    # Rules Summary Box
    by = y + 54.0
    bw = w - 16.0
    bh = 94.0
    page.rounded_rect(x + 8.0, by, bw, bh, r=3.0, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.75)
    page.rect(x + 8.0, by, bw, 14.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.6)
    page.text(x + 12.0, by + 10.0, "ROLE 2: WHITE HAT OPERATIVE RULES", font="mono_bold", size=5.6, color=PALETTE["purple"])
    page.text(x + bw + 4.0, by + 10.0, "1 DOSSIER / PLAYER", font="mono_bold", size=5.2, color=PALETTE["purple"], align="right")

    wh_rules_text = (
        "**1. Operative Assignment:** Draw 1 White Hat Dossier at setup and slot flush into this dock.\n"
        "**2. Personal Reserve:** Holds your **2 Purple Specialist Dice** ($4–$6 (per Dossier) in Phase 3A Operations).\n"
        "**3. Face 6 Signature Protocol ({STAR}):** Rolling Purple Face 6 triggers your operative's repeatable protocol.\n"
        "**4. Repeatable:** Each rolled Purple Star ({STAR}) triggers the protocol once."
    )
    page.rich_paragraph(x + 12.0, by + 23.0, bw - 8.0, wh_rules_text, size=5.6, leading=7.6, color=PALETTE["ink"])

    intro_wh = [
        "The Operator (WH-01)",
        "The Phreaker (WH-02)",
        "The Acoustic (WH-03)",
        "The Spook (WH-04)",
    ]
    wh_preset = intro_wh[idx - 1] if 1 <= idx <= len(intro_wh) else "Open Assignment"
    page.line(x + 12.0, by + bh - 14.0, x + 8.0 + bw - 4.0, by + bh - 14.0, stroke=PALETTE["purple_light"], width=0.5, dash=(2.0, 1.5))
    page.rich_line(x + w / 2.0, by + bh - 5.0, f"**Intro Preset (Optional):** {wh_preset}", size=5.2, color=PALETTE["purple"], align="center")

    # Purple Specialist Dice Faces Strip
    f_y = y + 152.0
    page.text(x + 10.0, f_y + 10.0, "PURPLE SPECIALIST FACES (d6 // $4–$6 Reserve):", font="mono_bold", size=5.3, color=PALETTE["purple"])
    cell_w = (w - 20.0 - 4 * 2.5) / 5.0
    labels = ["1-2: Any Shld", "3: +$2 Cash", "4: +$1 & 1 {WRENCH}", "5: {LOCK} Glitch", "6: {STAR} Proto"]
    for c_i, lbl in enumerate(labels):
        cx_i = x + 10.0 + c_i * (cell_w + 2.5)
        c_fill = PALETTE["purple_light"] if c_i in (4, 5) else PALETTE["paper_tint"]
        page.rounded_rect(cx_i, f_y + 13.0, cell_w, 15.0, r=2.0, stroke=PALETTE["purple"], fill=c_fill, line_width=0.5, dash=(2.0, 1.5))
        page.rich_line(cx_i + cell_w / 2.0, f_y + 23.0, lbl, size=4.4, color=PALETTE["purple"], align="center")

    # Bottom Tag
    page.line(x + 8.0, y + 193.0, x + w - 8.0, y + 193.0, stroke=PALETTE["purple_light"], width=0.5)
    page.text(x + 8.0, y + 204.0, "SLIPS FLUSH BESIDE MAT", font="mono", size=4.6, color=PALETTE["muted"])
    page.text(x + w - 8.0, y + 204.0, "2x PURPLE SPECIALIST DICE ($4–$6 IN RESERVE)", font="mono", size=4.6, color=PALETTE["purple"], align="right")


def render_player_board(
    page: PDFPage,
    idx: int,
    comp: Optional[CompanyCardSpec] = None,
    white_hat: Optional[WhiteHatDossierSpec] = None,
) -> None:
    draw_board_outer_frame(
        page,
        left_tag=f"TOO MANY SECRETS // CONSULTANCY TERMINAL [TERM-0{idx}/4]",
        right_tag="PNP PROTOTYPE v0.26.0 // US LETTER",
    )

    # -------------------------------------------------------------------------
    # LEFT COLUMN (x = 40..278, w = 238) — DOCKED COMPANY & WHITE HAT CARDS
    # -------------------------------------------------------------------------
    lx, lw = 40.0, 238.0

    # Top Card: Client Company Card (Once-per-Version Institutional Override)
    if comp is not None:
        _draw_company_card(page, lx, 36.0, lw, 210.0, comp, is_dock=True)
    else:
        _draw_empty_company_card_slot(page, lx, 36.0, lw, 210.0, idx=idx)

    # Bottom Card: White Hat Dossier Card (Personal Reserve & Purple Face 6 Protocol)
    if white_hat is not None:
        _draw_white_hat_card(page, lx, 252.0, lw, 210.0, white_hat, is_dock=True)
    else:
        _draw_empty_white_hat_slot(page, lx, 252.0, lw, 210.0, idx=idx)

    # -------------------------------------------------------------------------
    # RIGHT COLUMN (x = 292..752, w = 460) — Revised Player Terminal Layout
    # -------------------------------------------------------------------------
    rx, rw = 292.0, 460.0

    # =========================================================================
    # ZONE 1: READY FOR RELEASE (x = 292..620, w = 328, y = 36..118, h = 82)
    # ZONE 0: PERSONAL RESERVE  (x = 626..752, w = 126, y = 36..118, h = 82)
    # =========================================================================
    r1_y, r1_h = 36.0, 82.0
    w_ready = 328.0
    x_res = rx + w_ready + 6.0
    w_res = rw - w_ready - 6.0  # 126.0 pt

    # Ready for Release Box
    page.rect(rx, r1_y, w_ready, r1_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, r1_y, w_ready, 18.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(rx + 8, r1_y + 12.5, "ZONE 1: READY FOR RELEASE", font="bold", size=8.5, color=PALETTE["ink"])
    page.rich_line(
        rx + w_ready - 8, r1_y + 12.5,
        "Start: **4** {GRAY} Gray Starter Dice",
        size=6.5, color=PALETTE["ink_soft"], align="right",
    )

    # 6 faint 16mm die placement guides centered in Ready Zone
    slot_s = 28.0
    gap_s = 6.0
    row_w = 6 * slot_s + 5 * gap_s
    gx0 = rx + (w_ready - row_w) / 2.0
    gy0 = r1_y + 22.0
    for i in range(6):
        gx = gx0 + i * (slot_s + gap_s)
        page.rounded_rect(gx, gy0, slot_s, slot_s, r=3.0, stroke=PALETTE["rule"], fill=None, line_width=0.6, dash=(2.0, 2.0))
        if i < 4:
            page.text(gx + slot_s / 2.0, gy0 + slot_s / 2.0 + 2.0, "START", font="mono", size=5.5, color=PALETTE["watermark"], align="center")

    page.rich_line(
        rx + w_ready / 2.0, r1_y + 63.5,
        "Phase 1: Roll Ready + Contractors. Max 2 Rerolls (Glitches lock).",
        size=6.0, color=PALETTE["ink_soft"], align="center",
    )
    page.rich_line(
        rx + w_ready / 2.0, r1_y + 74.0,
        "**HASH MATCH:** 3 matching faces in roll = **+1 Corporate Secret** *(no Glitches)*",
        size=6.1, color=PALETTE["blue"], align="center",
    )

    # Dedicated Personal Reserve Dock (Holding 2 Purple Specialist Dice)
    page.rect(x_res, r1_y, w_res, r1_h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=1.0)
    page.rect(x_res, r1_y, w_res, 18.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.8)
    page.rect(x_res, r1_y, w_res, 2.5, stroke=None, fill=PALETTE["purple"])
    page.draw_color_badge(x_res + 9.0, r1_y + 10.0, 5.5, "purple")
    page.text(x_res + w_res / 2.0 + 3.0, r1_y + 12.5, "PERSONAL RESERVE", font="bold", size=7.5, color=PALETTE["purple"], align="center")

    # 2 dedicated Purple Specialist die guide slots
    ds_res = 26.0
    gap_res = 8.0
    dx0_res = x_res + (w_res - (2 * ds_res + gap_res)) / 2.0
    dy0_res = r1_y + 22.0
    for d_i in range(2):
        bx = dx0_res + d_i * (ds_res + gap_res)
        page.rounded_rect(bx, dy0_res, ds_res, ds_res, r=3.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.75, dash=(2.0, 1.5))
        page.text(bx + ds_res / 2.0, dy0_res + 10.5, f"DIE {d_i + 1}", font="mono_bold", size=5.5, color=PALETTE["purple"], align="center")
        page.rich_line(bx + ds_res / 2.0, dy0_res + 19.5, "{PURPLE}", size=5.5, color=PALETTE["purple"], align="center")

    page.rich_line(
        x_res + w_res / 2.0, r1_y + 63.5,
        "**$4–$6 (per Dossier)** in P3A",
        size=5.8, color=PALETTE["purple"], align="center",
    )
    page.text(
        x_res + w_res / 2.0, r1_y + 73.5,
        "Private dock (counts to 2 limit)",
        font="italic", size=5.2, color=PALETTE["ink_soft"], align="center",
    )

    # Procurement arrow from Personal Reserve to Zone 1
    page.line(x_res - 1.0, r1_y + 40.0, rx + w_ready + 1.0, r1_y + 40.0, stroke=PALETTE["purple"], width=1.1)
    page.line(rx + w_ready + 1.0, r1_y + 40.0, rx + w_ready + 4.5, r1_y + 37.0, stroke=PALETTE["purple"], width=1.1)
    page.line(rx + w_ready + 1.0, r1_y + 40.0, rx + w_ready + 4.5, r1_y + 43.0, stroke=PALETTE["purple"], width=1.1)

    # =========================================================================
    # ZONE 2: IN PRODUCTION (Middle Box: y = 125..313, h = 188)
    # =========================================================================
    r2_y, r2_h = 125.0, 188.0
    page.rect(rx, r2_y, rw, r2_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, r2_y, rw, 18.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(
        rx + 8, r2_y + 12.5,
        "**ZONE 2: IN PRODUCTION** (Zero Dice Wear — Shields never wear down!)",
        size=8.2, color=PALETTE["ink"],
    )
    page.text(rx + rw - 8, r2_y + 12.5, "DEPLOYED MODULES", font="mono_bold", size=6.5, color=PALETTE["ink_soft"], align="right")

    # Sub-box 1: Income (wide rectangle spanning the width)
    ix = rx + 7.0
    iy = r2_y + 22.0
    iw = rw - 14.0  # 446.0 pt
    ih = 48.0
    page.rect(ix, iy, iw, ih, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
    page.rect(ix, iy, iw, 15.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.rich_line(ix + 6.0, iy + 10.5, "**INCOME SLOT** (Cash, Patches & Non-Shield Star Outputs)", size=7.2, color=PALETTE["ink"])
    page.text(ix + iw - 6.0, iy + 10.5, "COLLECTED IN PHASE 3", font="mono_bold", size=5.8, color=PALETTE["muted"], align="right")

    page.rich_paragraph(
        ix + 8.0, iy + 25.0, 280.0,
        "Modules producing cash, patches, and non-shield star abilities.\n"
        "**Delayed Income:** Surviving dice collect cash & patches in Phase 3.",
        size=6.2, leading=8.4, color=PALETTE["ink_soft"],
    )
    # 5 faint die guide slots on right of Income box
    ds_inc = 25.0
    ds_gap = 4.0
    inc_x0 = ix + iw - (5 * ds_inc + 4 * ds_gap) - 6.0
    inc_y0 = iy + 18.0
    inc_lbls = ["+$", "+$", "+{WRENCH}", "+{WRENCH}", "{STAR}"]
    for i, lbl in enumerate(inc_lbls):
        gx = inc_x0 + i * (ds_inc + ds_gap)
        page.rounded_rect(gx, inc_y0, ds_inc, ds_inc, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6, dash=(2.0, 2.0))
        page.rich_line(gx + ds_inc / 2.0, inc_y0 + 15.0, lbl, size=5.5, color=PALETTE["muted"], align="center")

    # Sub-boxes 2, 3, 4: Red Shields | Blue Shields | Green Shields (under Income)
    sy = iy + ih + 6.0  # 147 + 48 + 6 = 201.0
    sh = r2_y + r2_h - sy - 7.0  # 313 - 201 - 7 = 105.0 pt
    sgap = 8.0
    sw = (iw - 2 * sgap) / 3.0  # 143.33 pt each

    shield_boxes = [
        ("red", "{RED} RED SHIELDS", "Blocks Ransomware", "-$1 Cash per unblocked", "*(Unpaid: -1 Secret)*"),
        ("blue", "{BLUE} BLUE SHIELDS", "Blocks Spyware", "**-1 Corporate Secret**", "per unblocked cube"),
        ("green", "{GREEN} GREEN SHIELDS", "Blocks Malware", "Unblocked: **Glitch 1 Die**", "*(Income 1st -> Glitched)*"),
    ]
    for i, (ckey, title_mk, sub1, sub2, sub3) in enumerate(shield_boxes):
        bx = ix + i * (sw + sgap)
        fg, bg = _color_pair(ckey)
        page.rect(bx, sy, sw, sh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.9)
        # Header strip with color accent
        page.rect(bx, sy, sw, 18.0, stroke=PALETTE["ink"], fill=bg, line_width=0.7)
        page.rect(bx, sy, sw, 2.8, stroke=None, fill=fg)
        page.rich_line(bx + sw / 2.0, sy + 13.0, f"**{title_mk}**", size=7.8, color=fg, align="center")

        # 2 die guide slots inside each shield box
        ds = 36.0
        dx0 = bx + (sw - (2 * ds + 8.0)) / 2.0
        dy0 = sy + 24.0
        for d_i in range(2):
            page.rounded_rect(dx0 + d_i * (ds + 8.0), dy0, ds, ds, r=3.5, stroke=PALETTE["rule"], fill=None, line_width=0.6, dash=(2.0, 2.0))

        page.text(bx + sw / 2.0, sy + 73.0, sub1, font="bold", size=6.5, color=PALETTE["ink"], align="center")
        page.rich_line(bx + sw / 2.0, sy + 84.0, sub2, size=6.0, color=fg, align="center")
        page.rich_line(bx + sw / 2.0, sy + 94.5, sub3, size=5.6, color=PALETTE["muted"], align="center")

    # =========================================================================
    # ZONE 3: UNDER DEVELOPMENT (Bottom Box: y = 320..456, h = 136)
    # =========================================================================
    r3_y, r3_h = 320.0, 136.0
    page.rect(rx, r3_y, rw, r3_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, r3_y, rw, 18.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(
        rx + 8, r3_y + 12.5,
        "**ZONE 3: UNDER DEVELOPMENT** (CI/CD Triage Conveyor)",
        size=8.2, color=PALETTE["ink"],
    )
    page.text(rx + rw - 8, r3_y + 12.5, "OFFLINE MODULES (DO NOT ROLL)", font="mono_bold", size=6.4, color=PALETTE["muted"], align="right")

    # Sub-box 1: Glitched Box
    gx = rx + 7.0
    gy = r3_y + 22.0
    gw = 180.0
    gh = 80.0
    page.rect(gx, gy, gw, gh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.85)
    page.rect(gx, gy, gw, 16.0, stroke=PALETTE["ink"], fill=PALETTE["red_light"], line_width=0.6)
    page.rich_line(gx + 6.0, gy + 11.0, "**GLITCHED BOX** (Quarantine)", size=7.2, color=PALETTE["red"])

    page.rich_paragraph(
        gx + 6.0, gy + 22.0, gw - 12.0,
        "Modules quarantined for repair (from roll glitches or green malware/corruption).",
        size=5.7, leading=7.5, color=PALETTE["ink_soft"],
    )
    # 3 die slots on left of Glitched Box
    ds_g = 25.0
    dy_g = gy + 48.0
    for d_i in range(3):
        page.rounded_rect(gx + 7.0 + d_i * (ds_g + 4.0), dy_g, ds_g, ds_g, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6, dash=(2.0, 2.0))
        page.rich_line(gx + 7.0 + d_i * (ds_g + 4.0) + ds_g / 2.0, dy_g + 15.0, "{LOCK}", size=5.5, color=PALETTE["muted"], align="center")

    # Fast-Patch option on right of Glitched Box
    fp_x = gx + 98.0
    fp_w = gw - 104.0
    page.rounded_rect(fp_x, dy_g, fp_w, ds_g, r=2.5, stroke=PALETTE["green"], fill=PALETTE["green_light"], line_width=0.7)
    page.rich_line(fp_x + fp_w / 2.0, dy_g + 10.0, "**FAST-PATCH**", size=5.6, color=PALETTE["green"], align="center")
    page.rich_line(fp_x + fp_w / 2.0, dy_g + 19.5, "Pay **1** {WRENCH} -> Scanned", size=5.0, color=PALETTE["ink"], align="center")

    # Conveyor Arrow connecting Glitched to Scanned
    c_x1 = gx + gw + 4.0
    c_x2 = rx + rw - 7.0 - 180.0 - 4.0
    c_cx = (c_x1 + c_x2) / 2.0
    page.rich_line(c_cx, gy + 16.0, "**Fast-Patch**", size=6.3, color=PALETTE["green"], align="center")
    page.rich_line(c_cx, gy + 25.5, "(Pay 1 {WRENCH})", size=5.6, color=PALETTE["ink_soft"], align="center")

    # Arrow line and head
    page.line(c_x1 + 4.0, gy + 42.0, c_x2 - 4.0, gy + 42.0, stroke=PALETTE["ink"], width=1.4)
    page.line(c_x2 - 4.0, gy + 42.0, c_x2 - 11.0, gy + 37.0, stroke=PALETTE["ink"], width=1.4)
    page.line(c_x2 - 4.0, gy + 42.0, c_x2 - 11.0, gy + 47.0, stroke=PALETTE["ink"], width=1.4)

    page.text(c_cx, gy + 58.0, "OR", font="mono_bold", size=5.5, color=PALETTE["muted"], align="center")
    page.text(c_cx, gy + 67.0, "NATURAL SHIFT", font="mono_bold", size=5.8, color=PALETTE["ink_soft"], align="center")
    page.text(c_cx, gy + 75.5, "at Round End (Free)", font="italic", size=5.1, color=PALETTE["muted"], align="center")

    # Sub-box 2: Scanned Box
    sx = rx + rw - 7.0 - 180.0
    sy = gy
    sw_sc = 180.0
    sh_sc = 80.0
    page.rect(sx, sy, sw_sc, sh_sc, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.85)
    page.rect(sx, sy, sw_sc, 16.0, stroke=PALETTE["ink"], fill=PALETTE["blue_light"], line_width=0.6)
    page.rich_line(sx + 6.0, sy + 11.0, "**SCANNED BOX** (Verified)", size=7.2, color=PALETTE["blue"])

    page.rich_paragraph(
        sx + 6.0, sy + 22.0, sw_sc - 12.0,
        "Remediated modules completing automated linting & verification.",
        size=5.7, leading=7.5, color=PALETTE["ink_soft"],
    )
    # 3 die slots on left of Scanned Box
    for d_i in range(3):
        page.rounded_rect(sx + 7.0 + d_i * (ds_g + 4.0), dy_g, ds_g, ds_g, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6, dash=(2.0, 2.0))
        page.rich_line(sx + 7.0 + d_i * (ds_g + 4.0) + ds_g / 2.0, dy_g + 15.0, "{BLUE}", size=5.5, color=PALETTE["muted"], align="center")

    # Graduation status pill on right of Scanned Box
    grad_x = sx + 98.0
    grad_w = sw_sc - 104.0
    page.rounded_rect(grad_x, dy_g, grad_w, ds_g, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.7)
    page.text(grad_x + grad_w / 2.0, dy_g + 10.0, "GRADUATION", font="mono_bold", size=5.6, color=PALETTE["ink"], align="center")
    page.rich_line(grad_x + grad_w / 2.0, dy_g + 19.5, "-> **Ready** at EOR", size=5.2, color=PALETTE["ink_soft"], align="center")

    # Bottom caption across Zone 3
    page.line(rx + 8.0, r3_y + 107.0, rx + rw - 8.0, r3_y + 107.0, stroke=PALETTE["rule"], width=0.5, dash=(2.0, 2.0))
    page.rich_paragraph(
        rx + 8.0, r3_y + 116.0, rw - 16.0,
        "**PIPELINE TRANSITION:** At round end, Scanned dice graduate to Ready for Release; remaining Glitched dice shift naturally to Scanned *(or Fast-Patch for 1 {WRENCH})*. Surviving In Production dice return to Ready.",
        size=5.7, leading=7.7, color=PALETTE["ink_soft"], align="center",
    )
    page.text(
        rx + rw / 2.0, r3_y + 130.5,
        "DESTRUCTION FALLBACK: If In Production is empty vs Green Malware, destroy 1 die from Under Development!",
        font="italic", size=5.3, color=PALETTE["muted"], align="center",
    )

    # -------------------------------------------------------------------------
    # BOTTOM ROW: Money | Patches | Secrets (x = 40..752, y = 468..578)
    # -------------------------------------------------------------------------
    by, bh = 468.0, 110.0
    bgap = 14.0
    bw = (712.0 - 2 * bgap) / 3.0  # 228.0 pt each

    # 1. Money
    mx = 40.0
    page.rect(mx, by, bw, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(mx, by, bw, 20.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(mx + 8, by + 13.8, "MONEY ($)", font="bold", size=9.5, color=PALETTE["ink"])
    page.text(mx + bw / 2.0, by + 66.0, "$", font="bold", size=28.0, color=PALETTE["guide"], align="center")
    page.text(mx + bw / 2.0, by + bh - 7.0, "Start: $4 (+$1 Data Scraper)  |  Never drops below $0", font="regular", size=6.7, color=PALETTE["muted"], align="center")

    # 2. Patches (with 3 dedicated token slots enforcing Cleanup Cap: Max 3 🔧)
    px = mx + bw + bgap
    page.rect(px, by, bw, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(px, by, bw, 20.0, stroke=PALETTE["ink"], fill=PALETTE["green_light"], line_width=0.8)
    page.rich_line(px + 8, by + 13.8, "{WRENCH} **PATCHES**", size=9.2, color=PALETTE["green"])
    page.text(px + bw - 8, by + 13.8, "CLEANUP CAP: 3", font="mono_bold", size=7.4, color=PALETTE["green"], align="right")

    ps_size = 50.0
    ps_gap = 12.0
    ps_x0 = px + (bw - (3 * ps_size + 2 * ps_gap)) / 2.0
    ps_y = by + 30.0
    for p_i in range(3):
        sx = ps_x0 + p_i * (ps_size + ps_gap)
        page.rounded_rect(sx, ps_y, ps_size, ps_size, r=6.0, stroke=PALETTE["muted"], fill=PALETTE["paper_tint"], line_width=0.75, dash=(3, 2))
        lbl = f"SLOT {p_i + 1}" if p_i < 2 else "CLEANUP (3)"
        page.text(sx + ps_size / 2.0, ps_y + 13.0, lbl, font="mono", size=5.8, color=PALETTE["muted"], align="center")
        page.draw_wrench_icon(sx + ps_size / 2.0, ps_y + 31.0, 14.0, color=PALETTE["rule"])
    page.rich_line(px + bw / 2.0, by + bh - 7.0, "Start: **2** Tokens  |  Fast-Patch (1 {WRENCH}: Glitched -> Scanned)  |  Discard >3 at Cleanup", size=5.8, color=PALETTE["muted"], align="center")

    # 3. Secrets
    scx = px + bw + bgap
    page.rect(scx, by, bw, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(scx, by, bw, 20.0, stroke=PALETTE["ink"], fill=PALETTE["blue_light"], line_width=0.8)
    page.rich_line(scx + 8, by + 13.8, "{SECRET} **SECRETS**", size=9.2, color=PALETTE["blue"])
    page.text(scx + bw - 8, by + 13.8, "PRIMARY OBJECTIVE", font="mono_bold", size=7.5, color=PALETTE["blue"], align="right")
    page.draw_secret_icon(scx + bw / 2.0, by + 56.0, 26.0, color=PALETTE["guide"])
    page.text(scx + bw / 2.0, by + bh - 16.5, "Start: 8 Secrets (2P/3P)  |  12 Secrets (4P)", font="regular", size=6.7, color=PALETTE["ink_soft"], align="center")
    page.text(scx + bw / 2.0, by + bh - 6.0, "<= 0 SECRETS = TOTAL DATA BREACH (PATIENT ZERO)", font="bold", size=6.5, color=PALETTE["red"], align="center")


def render_company_cards_page(page: PDFPage) -> None:
    """Render all 6 Client Company Cards on a single US Letter print-and-cut sheet."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // 6x CLIENT COMPANY CARDS [PAGE 5/6]",
        right_tag="PNP PROTOTYPE v0.26.0 // US LETTER",
    )

    page.text(
        396.0, 35.0,
        "6x CLIENT COMPANY CARDS -- CUT ALONG TICKS -- SIZED TO DOCK FLUSH (3.30\" x 2.92\") BESIDE TERMINAL MAT",
        font="mono_bold", size=6.8, color=PALETTE["ink_soft"], align="center",
    )

    cw = 238.0
    ch = 210.0
    gap_x = 2.0
    gap_y = 6.0
    x0 = 37.0
    y0 = 46.0

    for idx, comp in enumerate(COMPANIES):
        col = idx % 3
        row = idx // 3
        bx = x0 + col * (cw + gap_x)
        by = y0 + row * (ch + gap_y)

        # Draw crop corner ticks for cutting
        page.corner_ticks(bx - 3.0, by - 3.0, cw + 6.0, ch + 6.0, size=5.0, color=PALETTE["muted"])
        _draw_company_card(page, bx, by, cw, ch, comp, is_dock=False)

    # Bottom Rules Summary Panel (y = 478..578, h = 100 pt)
    ry = 478.0
    rw = 718.0
    rx = 37.0
    page.rect(rx, ry, rw, 100.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.8)
    page.rect(rx, ry, rw, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.text(rx + 8.0, ry + 11.5, "CLIENT COMPANY RULES REFERENCE // INSTITUTIONAL OVERRIDES (ONCE PER VERSION)", font="bold", size=7.2, color=PALETTE["ink"])
    page.text(rx + rw - 8.0, ry + 11.5, "USE-IT-OR-LOSE-IT TIMING", font="mono_bold", size=6.0, color=PALETTE["ink_soft"], align="right")

    rules_text = (
        "**1. Contract Assignment:** At setup, each player is dealt 1 Client Company card (or introductory preset). Place card flush into the Terminal Mat top dock.\n"
        "**2. Once-per-Version Lifecycle:** Each company provides 1 Institutional Override per SETEC Version (**v1.0**, **v2.0**, and **v3.0**). Mark the checkbox upon activation.\n"
        "**3. Use-It-or-Lose-It:** A version's override must be activated before SETEC compiles to the next version. When SETEC advances to a new version in Phase 2 Step 2A, any unspent charge from the previous version is **forfeited**.\n"
        "**4. Immediate Version Unlock:** The newly active version's override unlocks immediately in the same round SETEC upgrades, available starting in Step 2B or Phase 3 Operations."
    )
    page.rich_paragraph(rx + 10.0, ry + 25.0, rw - 20.0, rules_text, size=6.4, leading=8.6, color=PALETTE["ink"])


def render_white_hat_dossiers_page(page: PDFPage) -> None:
    """Render all 6 White Hat Dossier Cards on a single US Letter print-and-cut sheet."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // 6x WHITE HAT DOSSIER CARDS [PAGE 6/6]",
        right_tag="PNP PROTOTYPE v0.26.0 // US LETTER",
    )

    page.text(
        396.0, 35.0,
        "6x WHITE HAT DOSSIER CARDS -- CUT ALONG TICKS -- SIZED TO DOCK FLUSH (3.30\" x 2.92\") BESIDE TERMINAL MAT",
        font="mono_bold", size=6.8, color=PALETTE["purple"], align="center",
    )

    cw = 238.0
    ch = 210.0
    gap_x = 2.0
    gap_y = 6.0
    x0 = 37.0
    y0 = 46.0

    for idx, wh in enumerate(WHITE_HATS):
        col = idx % 3
        row = idx // 3
        bx = x0 + col * (cw + gap_x)
        by = y0 + row * (ch + gap_y)

        # Draw crop corner ticks for cutting
        page.corner_ticks(bx - 3.0, by - 3.0, cw + 6.0, ch + 6.0, size=5.0, color=PALETTE["purple"])
        _draw_white_hat_card(page, bx, by, cw, ch, wh, is_dock=False)

    # Bottom Rules Summary Panel (y = 478..578, h = 100 pt)
    ry = 478.0
    rw = 718.0
    rx = 37.0
    page.rect(rx, ry, rw, 100.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.8)
    page.rect(rx, ry, rw, 16.0, stroke=PALETTE["purple"], fill=PALETTE["purple"], line_width=0.6)
    page.text(rx + 8.0, ry + 11.5, "WHITE HAT OPERATIVE DOSSIER RULES // PERSONAL RESERVE & PURPLE STAR PROTOCOLS", font="bold", size=7.2, color=PALETTE["white"])
    page.text(rx + rw - 8.0, ry + 11.5, "REPEATABLE PER PURPLE STAR", font="mono_bold", size=6.0, color=PALETTE["rule"], align="right")

    wh_rules_text = (
        "**1. Operative Assignment:** At setup, each player is dealt 1 White Hat Dossier card (or introductory preset). Place card flush into the Terminal Mat bottom dock.\n"
        "**2. Personal Reserve (2 Purple Dice):** Each player holds **2 Purple Specialist Dice** in their private dock on the Terminal Mat. Procured for **$4–$6 each (per Dossier)** in Phase 3A Operations (counts to 2-dice buy limit).\n"
        "**3. Standardized Faces 1-5:** All Purple Specialist dice feature: **Faces 1-2:** `Block 1 Any`, **Face 3:** `+$2`, **Face 4:** `+$1 & +1 🔧`, **Face 5:** `Glitch (Locked)`.\n"
        "**4. Face 6 Signature Protocol:** Rolling Face 6 ({PURPLE} {STAR}) triggers the operative's bespoke Signature Protocol. Repeatable: each rolled Star triggers the protocol once."
    )
    page.rich_paragraph(rx + 10.0, ry + 25.0, rw - 20.0, wh_rules_text, size=6.4, leading=8.6, color=PALETTE["ink"])


# =============================================================================
# 2A. Central SETEC Agent Board (Matches Wireframe Page 2)
# =============================================================================

def render_agent_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // CENTRAL ROGUE AGENT & COMPILER BOARD [1/2]",
        right_tag="PNP PROTOTYPE v0.26.0 // US LETTER",
    )

    # Top Title Bar inside board
    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "PROJECT: SETEC  //  AUTONOMOUS MAINFRAME COMPILER", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "PLACE VERSION TILES ON LEFT  |  DROP CUBE TOWER IN PHASE 2", font="mono", size=7.2, color=PALETTE["rule"], align="right")

    col_top = 64.0
    col_bot = 578.0
    col_h = col_bot - col_top  # 514 pt

    # -------------------------------------------------------------------------
    # COLUMN 1 (Left): v3.0 / v2.0 / v1.0 Slots + Corruption Track
    # Matches Wireframe Page 2 exact spatial hierarchy!
    # -------------------------------------------------------------------------
    label_cx = 56.0
    slot_x = 78.0
    slot_w = 220.0  # 3.056" (printable tiles are 212 x 112 pt = 2.94" x 1.56")
    slot_h = 120.0  # 1.667"
    slot_gap = 15.0

    tiers = [
        ("v3.0", "SINGULARITY TIER", "Deal 1 face-up v3.0 Tile here", "Corruption Track fills = SINGULARITY!"),
        ("v2.0", "ESCALATION TIER", "Deal 1 face-up v2.0 Tile here", "On Upgrade: Add Payload -> Staging Cup"),
        ("v1.0", "INITIAL TIER (START)", "Deal 1 face-up v1.0 Tile here", "Setup: Add Start Payload -> Staging Cup"),
    ]

    for idx, (ver_str, tier_sub, hint1, hint2) in enumerate(tiers):
        sy = col_top + idx * (slot_h + slot_gap)
        # Left Version Label (matching wireframe's v3.0 / v2.0 / v1.0 column)
        page.rounded_rect(38.0, sy + 42.0, 34.0, 36.0, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"] if idx < 2 else PALETTE["ink"], line_width=1.0)
        v_col = PALETTE["ink"] if idx < 2 else PALETTE["white"]
        page.text(55.0, sy + 60.0, ver_str, font="bold", size=10.5, color=v_col, align="center")
        page.text(55.0, sy + 71.0, "START" if idx == 2 else f"TIER {3 - idx}", font="mono", size=5.5, color=PALETTE["rule"] if idx == 2 else PALETTE["muted"], align="center")

        # Upward upgrade arrow between version badges
        if idx < 2:
            ay_mid = sy + slot_h + slot_gap / 2.0
            page.line(55.0, sy + 84.0, 55.0, sy + slot_h + slot_gap + 38.0, stroke=PALETTE["muted"], width=0.9, dash=(2, 2))
            # Upward arrow in slot gap
            gx_mid = slot_x + slot_w / 2.0
            page.text(gx_mid, ay_mid + 3.0, "^  UPGRADE WHEN TRACK FILLS  ^", font="mono_bold", size=6.3, color=PALETTE["muted"], align="center")

        # Card Placement Slot
        page.rect(slot_x, sy, slot_w, slot_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.1)
        page.rect(slot_x + 4.0, sy + 4.0, slot_w - 8.0, slot_h - 8.0, stroke=PALETTE["muted"], fill=PALETTE["white"], line_width=0.6, dash=(4, 3))
        page.corner_ticks(slot_x + 4.0, sy + 4.0, slot_w - 8.0, slot_h - 8.0, size=6.0, color=PALETTE["ink_soft"])
        page.text(slot_x + slot_w / 2.0, sy + 46.0, f"{ver_str}  //  {tier_sub}", font="mono_bold", size=8.0, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 64.0, hint1, font="italic", size=7.8, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 80.0, hint2, font="regular", size=6.8, color=PALETTE["muted"], align="center")

    # Corruption Track Box directly beneath v1.0 slot (aligned x = 78..298, matching Wireframe Page 2!)
    ct_y = col_top + 3 * (slot_h + slot_gap)  # 64 + 405 = 469.0
    ct_h = col_bot - ct_y  # 109.0 pt
    page.rect(slot_x, ct_y, slot_w, ct_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.2)
    page.rect(slot_x, ct_y, slot_w, 19.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.8)
    page.rich_line(slot_x + slot_w / 2.0, ct_y + 13.5, "**ACTIVE VERSION CORRUPTION PROTOCOL** (v0.25.0)", size=7.5, color=PALETTE["white"], align="center")

    # 3 Version Track Capacity Milestones
    tiers_summary = [
        ("v1.0 (4 Spaces)", "Start Priming -> Up v2.0"),
        ("v2.0 (5 Spaces)", "Escalation -> Up v3.0"),
        ("v3.0 (6 Spaces)", "Singularity -> GAME OVER"),
    ]
    sw_t = (slot_w - 20.0) / 3.0
    for t_i, (t_hdr, t_sub) in enumerate(tiers_summary):
        tx_b = slot_x + 6.0 + t_i * (sw_t + 4.0)
        page.rounded_rect(tx_b, ct_y + 24.0, sw_t, 30.0, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.7)
        page.text(tx_b + sw_t / 2.0, ct_y + 36.0, t_hdr, font="bold", size=6.5, color=PALETTE["ink"], align="center")
        page.text(tx_b + sw_t / 2.0, ct_y + 46.5, t_sub, font="mono", size=4.8, color=PALETTE["muted"], align="center")

    page.rich_paragraph(
        slot_x + 6.0, ct_y + 60.0, slot_w - 12.0,
        "**Step 2A Protocol:** Place exited {BLACK} 1-by-1 onto the active Version Tile's track. "
        "Each space immediately triggers its mechanical impact for all players. "
        "When track fills (**4** on v1.0, **5** on v2.0, **6** on v3.0), advance Version (**v3.0 Space 6 = SINGULARITY!**). "
        "Newly injected cubes from track spaces go to the Staging Cup for the next compile cycle.",
        size=5.8, leading=7.8, color=PALETTE["ink_soft"], align="center",
    )

    # -------------------------------------------------------------------------
    # COLUMN 2 (Middle): Agent Cube Effect Summary (x = 312, w = 214)
    # -------------------------------------------------------------------------
    m_x, m_w = 312.0, 214.0
    page.rect(m_x, col_top, m_w, col_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    page.rect(m_x, col_top, m_w, 22.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.9)
    page.text(m_x + m_w / 2.0, col_top + 15.0, "AGENT CUBE EFFECT SUMMARY", font="bold", size=9.2, color=PALETTE["ink"], align="center")

    cy_cur = col_top + 35.0
    page.rich_paragraph(
        m_x + 8.0, cy_cur, m_w - 16.0,
        "In **Phase 2**, drop all cubes from the **Staging Cup** into the **Cube Tower**. Stuck cubes stay inside; exited cubes resolve in order:",
        size=7.2, leading=9.8, color=PALETTE["ink_soft"],
    )

    cube_cards = [
        (
            "black",
            "{BLACK} BLACK // CORRUPTION",
            "STEP 2A (FIRST)",
            (
                "Advance active **Version Corruption Track** 1 space per exited {BLACK}.\n"
                "**Space Effects:** Each filled space immediately triggers its effect for all players.\n"
                "**Track End:** Advance to next Version (**4** on v1.0, **5** on v2.0, **6** on v3.0 = **SINGULARITY!**)."
            ),
            88.0,
        ),
        (
            "red",
            "{RED} RED // RANSOMWARE",
            "BLOCKS: {RED} SHIELD",
            (
                "Lose **$1** per unblocked {RED} cube.\n"
                "**Cash-Only Ransom:** Must pay with cash. Held {WRENCH} tokens cannot absorb ransom!\n"
                "**Ransom Leak:** Any unpaid ransom loses **1 Secret** per $1 unpaid! *(Cash min $0).*"
            ),
            88.0,
        ),
        (
            "blue",
            "{BLUE} BLUE // SPYWARE",
            "BLOCKS: {BLUE} SHIELD",
            (
                "Lose **1 Corporate Secret** per unblocked {BLUE} cube.\n"
                "**Patient Zero:** Reaching **<= 0 Secrets** triggers immediate **Total Data Breach** (eliminated)!"
            ),
            70.0,
        ),
        (
            "green",
            "{GREEN} GREEN // MALWARE",
            "BLOCKS: {GREEN} SHIELD",
            (
                "Unblocked: Glitch **1 die from In Production** (Income 1st, then Shields) to Glitched Box.\n"
                "**Income Forfeiture:** Glitched income dice produce $0 this round.\n"
                "**Sacrifice:** Discard 1 {WHITE} Contractor instead of module die.\n"
                "**Destruction Fallback:** If In Production empty, **Destroy 1 die from Under Development**!"
            ),
            104.0,
        ),
    ]

    cy_box = col_top + 62.0
    for ckey, ctitle, ctag, cbody, bh_card in cube_cards:
        fg, bg = _color_pair(ckey)
        page.rounded_rect(m_x + 7.0, cy_box, m_w - 14.0, bh_card, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
        page.rect(m_x + 7.0, cy_box, m_w - 14.0, 16.5, stroke=PALETTE["ink"], fill=bg, line_width=0.6)
        page.rich_line(m_x + 12.0, cy_box + 11.8, f"**{ctitle}**", size=7.3, color=fg if ckey != "black" else PALETTE["ink"])
        page.rich_line(m_x + m_w - 11.0, cy_box + 11.8, ctag, size=6.0, base_font="mono_bold", color=PALETTE["ink_soft"], align="right")
        page.rich_paragraph(m_x + 12.0, cy_box + 28.0, m_w - 24.0, cbody, size=6.9, leading=9.4, color=PALETTE["ink"])
        cy_box += bh_card + 6.5

    # Bottom Wear & Recycle summary box inside Column 2
    rem_h = col_bot - 7.0 - cy_box
    page.rounded_rect(m_x + 7.0, cy_box, m_w - 14.0, rem_h, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.8)
    page.rich_paragraph(
        m_x + 11.0, cy_box + 12.5, m_w - 22.0,
        "**ZERO DICE WEAR:** Shields NEVER wear down when blocking; stay in In Production.\n"
        "**RECYCLE:** Return all exited {RED} {BLUE} {GREEN} cubes -> **Staging Cup**. All {WHITE} Contractors -> Supply.",
        size=6.6, leading=9.0, color=PALETTE["ink"],
    )

    # -------------------------------------------------------------------------
    # COLUMN 3 (Right): Game Sequence Overview (x = 538, w = 214)
    # -------------------------------------------------------------------------
    g_x, g_w = 538.0, 214.0
    page.rect(g_x, col_top, g_w, col_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    page.rect(g_x, col_top, g_w, 22.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.9)
    page.text(g_x + g_w / 2.0, col_top + 15.0, "GAME SEQUENCE OVERVIEW", font="bold", size=9.2, color=PALETTE["ink"], align="center")

    gy = col_top + 34.0
    sections = [
        (
            "PHASE 1: ROLL & DEPLOY (Simultaneous)",
            (
                "**1. Pulse:** Add **+1** {BLACK} Black Cube -> Staging Cup.\n"
                "**2. Temp Staffing:** Hire {WHITE} Contractors (**$1** / **$2** / **$3**, max 3).\n"
                "**3. Roll Pool:** Roll Ready Zone + hired Contractors.\n"
                "**4. Pure Rerolls:** Up to **2 free rerolls** of unlocked dice. Glitches & locked faces cannot be unlocked.\n"
                "**5. Assign:** Commit Shields ({RED}/{BLUE}/{GREEN}) & Income. Unresolved Glitches -> **Glitched Box**.\n"
                "**6. Hash Match:** 3 matching faces in roll = **+1 Secret** *(uncapped; no Glitches)*."
            ),
        ),
        (
            "PHASE 2: SETEC COMPILE (Simultaneous)",
            (
                "**Drop** entire Staging Cup into Cube Tower.\n"
                "**2A.** Resolve {BLACK} Black Cubes on Corruption Track.\n"
                "**2B.** Resolve {RED} {BLUE} {GREEN} vs Shields (**Zero Dice Wear**); apply damage; recycle exited {RED} {BLUE} {GREEN} -> Staging Cup.\n"
                "**Empty Tray (Buffer Overflow):** If 0 cubes exit into tray, idle cycle injects **+1** {RED}, **+1** {BLUE}, **+1** {GREEN} from supply into Staging Cup.\n"
                "**2C. End Check:** **Singularity** OR any player **<= 0 Secrets** triggers **Final Round** *(Patient Zero eliminated; survivors take 1 final P3)*."
            ),
        ),
        (
            "PHASE 3: OPERATIONS & PIPELINE PREP",
            (
                "1. **Collect Income:** All cash, patches, & non-shield {STAR} from dice in In Production.\n"
                "2. **Buy Dice (max 2/turn):** Pay $ -> place in **Ready Zone**.\n"
                "3. **Pipeline Prep:** Fast-Patch (**1** {WRENCH}: Glitched -> Scanned); Scanned -> Ready; In Production -> Ready; Glitched -> Scanned.\n"
                "4. **Cleanup:** Discard unspent {WRENCH} >3; pass 1st Player."
            ),
        ),
        (
            "SECRETS VICTORY & TIEBREAKERS",
            (
                "**Surviving Firms Only** *(Patient Zero eliminated at <=0 Secrets)*:\n"
                "**Most Corporate Secrets Wins!** (Uncapped).\n"
                "*Tiebreakers: 1. Most Cash ($)  2. Ready Colored Dice  3. Patches ({WRENCH})  4. Fewest Under Dev.*"
            ),
        ),
    ]

    for stitle, sbody in sections:
        page.rect(g_x + 7.0, gy - 9.5, g_w - 14.0, 14.5, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.6)
        page.text(g_x + 11.0, gy + 0.5, stitle, font="bold", size=6.9, color=PALETTE["white"])
        gy += 14.0
        gy = page.rich_paragraph(g_x + 9.0, gy, g_w - 18.0, sbody, size=6.75, leading=9.3, color=PALETTE["ink"])
        gy += 5.5


# =============================================================================
# 2B. Companion Software Market & Supply Board (Page 2 of Central Boards)
# =============================================================================

def render_market_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // SOFTWARE MODULE MARKET & CENTRAL SUPPLY [2/2]",
        right_tag="PNP PROTOTYPE v0.25.0 // US LETTER",
    )

    # Top Title Bar
    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "SOFTWARE MODULE MARKET  &  CENTRAL COMPILER SUPPLY", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "4 MARKET STACKS (R/B/G/Y)  |  PURPLE IN PERSONAL RESERVES", font="mono", size=7.0, color=PALETTE["rule"], align="right")

    # -------------------------------------------------------------------------
    # TOP ROW: Staging Cup | Phase 2 Exit Sorting Tray | White Contractor Pool
    # -------------------------------------------------------------------------
    ty, th = 64.0, 126.0

    # 1. Staging Cup Zone (x = 40, w = 212)
    page.rect(40.0, ty, 212.0, th, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(40.0, ty, 212.0, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(146.0, ty + 13.2, "STAGING CUP (RELAY QUEUE)", font="bold", size=8.6, color=PALETTE["ink"], align="center")
    page.circle(94.0, ty + 73.0, 38.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.1, dash=(4, 2))
    page.circle(94.0, ty + 73.0, 28.0, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
    page.text(94.0, ty + 71.0, "STAGING", font="mono_bold", size=7.2, color=PALETTE["muted"], align="center")
    page.text(94.0, ty + 80.5, "CUP", font="mono_bold", size=7.2, color=PALETTE["muted"], align="center")
    page.rich_paragraph(
        140.0, ty + 34.0, 106.0,
        "**Queued for Next Drop:**\n"
        "- **P1 Pulse:** Injected {BLACK}\n"
        "- **P2 End:** Recycled {RED}{BLUE}{GREEN}\n"
        "- **Corruption:** Track Cubes",
        size=6.7, leading=9.8, color=PALETTE["ink_soft"],
    )
    page.text(146.0, ty + 118.0, "Setup Priming: Drop 1 R/B/G/Black into tower; stuck prime R1.", font="italic", size=5.6, color=PALETTE["muted"], align="center")

    # 2. Phase 2 Exit Sorting Tray (x = 264, w = 212)
    ex_x = 264.0
    page.rect(ex_x, ty, 212.0, th, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(ex_x, ty, 212.0, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(ex_x + 106.0, ty + 13.2, "COMPILER EXIT TRAY (SORTING)", font="bold", size=8.6, color=PALETTE["ink"], align="center")
    tray_cols = [("black", "2A: BLACK"), ("red", "2B: RED"), ("blue", "2B: BLUE"), ("green", "2B: GREEN")]
    tw_sub = 45.0
    tgap = 5.5
    tx0 = ex_x + (212.0 - (4 * tw_sub + 3 * tgap)) / 2.0
    for i, (ck, clbl) in enumerate(tray_cols):
        bx = tx0 + i * (tw_sub + tgap)
        fg, bg = _color_pair(ck)
        page.rounded_rect(bx, ty + 27.0, tw_sub, 76.0, r=3.0, stroke=fg, fill=bg if ck != "black" else PALETTE["paper_tint"], line_width=0.8)
        page.draw_color_badge(bx + tw_sub / 2.0, ty + 52.0, 13.0, ck)
        page.text(bx + tw_sub / 2.0, ty + 94.0, clbl, font="mono_bold", size=5.8, color=PALETTE["ink"], align="center")
    page.text(ex_x + 106.0, ty + 117.5, "Sort exited Cube Tower packets here before resolving Step 2A -> 2B.", font="italic", size=6.3, color=PALETTE["muted"], align="center")

    # 3. White Contractor Pool (x = 488, w = 264)
    wx, ww = 488.0, 264.0
    page.rect(wx, ty, ww, th, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(wx, ty, ww, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(wx + ww / 2.0, ty + 13.2, "{WHITE} **WHITE CONTRACTOR POOL (12 DICE)**", size=8.5, color=PALETTE["ink"], align="center")

    # Progressive Hiring Cost Boxes
    tiers_hire = [("1st HIRE", "$1"), ("2nd HIRE", "$2"), ("3rd HIRE", "$3")]
    hw = 76.0
    hgap = 9.0
    hx0 = wx + (ww - (3 * hw + 2 * hgap)) / 2.0
    for i, (hlbl, hcost) in enumerate(tiers_hire):
        hx = hx0 + i * (hw + hgap)
        page.rounded_rect(hx, ty + 26.0, hw, 34.0, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.8)
        page.text(hx + hw / 2.0, ty + 38.0, hlbl, font="mono", size=6.5, color=PALETTE["muted"], align="center")
        page.text(hx + hw / 2.0, ty + 53.0, hcost, font="bold", size=11.0, color=PALETTE["ink"], align="center")

    page.rich_line(
        wx + ww / 2.0, ty + 77.0,
        "**Faces:**  {PIP1}{PIP2}{PIP3} Block 1 Any   |   {PIP4} +$1   |   {PIP5}{PIP6} {LOCK} Glitch (0 output)",
        size=7.0, color=PALETTE["ink"], align="center",
    )
    page.rich_paragraph(
        wx + 8.0, ty + 94.0, ww - 16.0,
        "Hire in **Phase 1 Step 2** (max 3/round = $6). Never wears; returns to supply after Phase 2. May sacrifice vs {GREEN} Malware.",
        size=6.4, leading=8.8, color=PALETTE["ink_soft"], align="center",
    )

    # -------------------------------------------------------------------------
    # MIDDLE ROW: 4 Software Module Market Slots (x = 40..752, y = 200..498)
    # Streamlined 4-stack market layout with spacious 166 pt column width!
    # -------------------------------------------------------------------------
    my, mh = 200.0, 298.0
    mgap = 16.0
    mw = (712.0 - 3 * mgap) / 4.0  # 166.0 pt wide each!

    market_colors = [
        ("red", "RED // FINSEC", "$5–$6", "{PIP1} 1{RED} | {PIP2}-{PIP4} +$2", "{PIP5} {LOCK}Glitch | {PIP6} {STAR}", ""),
        ("blue", "BLUE // FIREWALL", "$5–$7", "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}", ""),
        ("green", "GREEN // ANTIVIRUS", "$5–$6", "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}", ""),
        ("yellow", "YELLOW // COMM. AI", "$6–$7", "{PIP1} +$3 | {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH} | {PIP5} {LOCK}Glitch", ""),
    ]

    for idx, (ckey, mtitle, mcost, f_row1, f_row2, passive_warn) in enumerate(market_colors):
        sx = 40.0 + idx * (mw + mgap)
        fg, bg = _color_pair(ckey)
        page.rect(sx, my, mw, mh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
        # Header
        page.rect(sx, my, mw, 22.0, stroke=PALETTE["ink"], fill=bg, line_width=0.8)
        page.rect(sx, my, mw, 3.5, stroke=None, fill=fg)
        page.draw_color_badge(sx + 12.0, my + 12.5, 9.0, ckey)
        page.text(sx + 24.0, my + 15.2, mtitle, font="bold", size=8.0, color=fg)

        # Market Cost & Stock strip
        page.rect(sx, my + 22.0, mw, 17.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
        page.text(sx + 8.0, my + 33.5, f"MARKET COST: {mcost}", font="bold", size=7.5, color=PALETTE["ink"])
        page.text(sx + mw - 8.0, my + 33.5, "STOCK: 2xP", font="mono_bold", size=7.0, color=PALETTE["ink_soft"], align="right")

        # Base Faces 1-4 summary above card slot
        page.rich_line(sx + mw / 2.0, my + 52.0, f_row1, size=7.0, color=PALETTE["ink"], align="center")
        page.rich_line(sx + mw / 2.0, my + 65.5, f_row2, size=6.8, color=PALETTE["ink"], align="center")
        if passive_warn:
            page.rich_line(sx + mw / 2.0, my + 77.5, passive_warn, size=6.0, color=PALETTE["red"], align="center")
        else:
            page.rich_line(sx + mw / 2.0, my + 77.5, "{PIP6} = Active {STAR} Card Below", size=6.3, color=PALETTE["muted"], align="center")

        # Card Slot (124 x 190 pt -> holds 120 x 182 pt Variant ★ Card centered in 166 pt column)
        cs_w, cs_h = 124.0, 190.0
        cs_x = sx + (mw - cs_w) / 2.0
        cs_y = my + mh - cs_h - 6.0
        page.rect(cs_x, cs_y, cs_w, cs_h, stroke=fg, fill=PALETTE["paper_tint"], line_width=0.8, dash=(4, 2.5))
        page.corner_ticks(cs_x, cs_y, cs_w, cs_h, size=5.0, color=fg)
        page.draw_star_icon(cs_x + cs_w / 2.0, cs_y + 72.0, 18.0, fill=PALETTE["rule"])
        page.text(cs_x + cs_w / 2.0, cs_y + 98.0, f"PLACE {ckey.upper()} (STAR)", font="mono_bold", size=6.8, color=PALETTE["muted"], align="center")
        page.text(cs_x + cs_w / 2.0, cs_y + 109.0, "VARIANT CARD HERE", font="mono", size=6.5, color=PALETTE["muted"], align="center")
        page.text(cs_x + cs_w / 2.0, cs_y + 128.0, "Stack 2x Players", font="italic", size=6.8, color=PALETTE["muted"], align="center")
        page.text(cs_x + cs_w / 2.0, cs_y + 138.0, "Colored Dice on card", font="italic", size=6.8, color=PALETTE["muted"], align="center")

    # -------------------------------------------------------------------------
    # BOTTOM ROW: Player-Count Setup Table + Portfolio Scoring Reference
    # -------------------------------------------------------------------------
    fy, fh = 508.0, 70.0
    fw = (712.0 - 14.0) / 2.0  # 349.0 pt each

    # Left: Setup by Player Count & Compiler Priming
    page.rect(40.0, fy, fw, fh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(40.0, fy, fw, 16.5, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
    page.text(48.0, fy + 11.8, "SETUP QUICK-REFERENCE & COMPILER PRIMING", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_paragraph(
        48.0, fy + 26.5, fw - 16.0,
        "- **2P:** $4 | **8 Secrets** | **2** {WRENCH} | **4 Dice/col** | *Track: 4 spaces*\n"
        "- **3P:** $4 | **8 Secrets** | **2** {WRENCH} | **6 Dice/col** | *Track: 5 spaces*\n"
        "- **4P:** $4 | **12 Secrets** | **2** {WRENCH} | **8 Dice/col** | *Track: 6 spaces*\n"
        "- **Setup:** 4 Market Stacks (R/B/G/Y). 2 Purple Specialist dice per player placed in Personal Reserves ($4–$6 (per Dossier); not in central market).",
        size=6.2, leading=8.7, color=PALETTE["ink"],
    )

    # Right: Portfolio Scoring & End-Game Triggers
    rx_f = 40.0 + fw + 14.0
    page.rect(rx_f, fy, fw, fh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx_f, fy, fw, 16.5, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
    page.text(rx_f + 8.0, fy + 11.8, "SECRETS VICTORY & TIEBREAKERS  (SURVIVING CONSULTANCIES)", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_paragraph(
        rx_f + 8.0, fy + 27.5, fw - 16.0,
        "- **Primary Victory Condition:** Most remaining **Corporate Secrets** wins! (Uncapped).\n"
        "- **Tiebreakers:** 1. Most Cash ($)  |  2. Most Ready Colored Dice  |  3. Most Patches ({WRENCH})  |  4. Fewest Under Dev.\n"
        "- *Patient Zero (<=0 Secrets) eliminated! Total wipeout: rank by net breach depth & unfulfilled destructions.*",
        size=6.8, leading=11.8, color=PALETTE["ink"],
    )


# =============================================================================
# 3. Dice Visual Aids & Printable Variant (★) Market Cards (4 Pages)
# =============================================================================

def render_master_dice_reference(page: PDFPage) -> None:
    """Page 1 of Dice Aids: Large-Print Full-Table Master Pip-to-Ability Reference."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // MASTER DICE PIP & ABILITY VISUAL AID [1/4]",
        right_tag="STANDARD 1-6 PIPPED D6 MAPPING",
    )

    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "SOFTWARE MODULE DICE  //  PIP-TO-ABILITY VISUAL REFERENCE", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "ROLL STANDARD 1-6 COLORED D6s  |  ZERO BLANK FACES", font="mono", size=7.2, color=PALETTE["rule"], align="right")

    # Table Geometry (x = 40..752, y = 64..486)
    tx, ty, tw = 40.0, 64.0, 712.0
    col_die = 112.0
    col_meta = 66.0
    col_face = (tw - col_die - col_meta) / 6.0  # 89.0 pt per face!

    # Header Row (h = 28 pt)
    hh = 28.0
    page.rect(tx, ty, tw, hh, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=1.0)
    page.text(tx + 8.0, ty + 18.0, "DIE TYPE", font="bold", size=8.2, color=PALETTE["ink"])
    page.line(tx + col_die, ty, tx + col_die, ty + hh, stroke=PALETTE["ink"], width=0.8)
    page.text(tx + col_die + col_meta / 2.0, ty + 18.0, "MARKET COST", font="bold", size=7.6, color=PALETTE["ink"], align="center")

    for p_i in range(6):
        fx = tx + col_die + col_meta + p_i * col_face
        page.line(fx, ty, fx, ty + hh, stroke=PALETTE["ink"], width=0.8)
        page.draw_pip_die(fx + 18.0, ty + 14.0, 16.0, p_i + 1)
        page.text(fx + 31.0, ty + 18.0, f"FACE {p_i + 1}", font="mono_bold", size=7.8, color=PALETTE["ink"])

    # 7 Die Rows
    row_h = 56.0
    for r_idx, dspec in enumerate(DICE_SPECS):
        ry = ty + hh + r_idx * row_h
        fg, bg = _color_pair(dspec.color_key)
        row_bg = PALETTE["white"] if r_idx % 2 == 0 else PALETTE["paper_tint"]
        page.rect(tx, ry, tw, row_h, stroke=PALETTE["ink"], fill=row_bg, line_width=0.85)

        # Left color tab + Die Name
        page.rect(tx, ry, 5.0, row_h, stroke=None, fill=fg)
        page.draw_color_badge(tx + 17.0, ry + 18.0, 11.0, dspec.color_key)
        page.text(tx + 28.0, ry + 21.5, dspec.title, font="bold", size=9.2, color=fg if dspec.color_key != "white" else PALETTE["ink"])
        page.text(tx + 12.0, ry + 34.5, dspec.subtitle, font="regular", size=7.4, color=PALETTE["ink_soft"])
        if dspec.color_key == "white":
            page.text(tx + 12.0, ry + 46.5, "NO WEAR / TEMP", font="mono_bold", size=6.0, color=PALETTE["muted"])

        # Cost cell
        mx = tx + col_die
        page.line(mx, ry, mx, ry + row_h, stroke=PALETTE["rule"], width=0.7)
        if " (" in dspec.cost_str:
            main_cost, paren = dspec.cost_str.split(" (", 1)
            paren = "(" + paren
            page.text(mx + col_meta / 2.0, ry + 25.0, main_cost, font="bold", size=8.5, color=PALETTE["ink"], align="center")
            page.text(mx + col_meta / 2.0, ry + 38.0, paren, font="mono", size=5.4, color=PALETTE["ink_soft"], align="center")
        else:
            page.text(mx + col_meta / 2.0, ry + 32.0, dspec.cost_str, font="bold", size=8.5, color=PALETTE["ink"], align="center")

        # 6 Face cells
        for f_idx, f_mk in enumerate(dspec.faces):
            fx = mx + col_meta + f_idx * col_face
            page.line(fx, ry, fx, ry + row_h, stroke=PALETTE["rule"], width=0.7)
            is_star = "{STAR}" in f_mk
            is_glitch = "Glitch" in f_mk
            is_choice = "/" in f_mk

            if is_star:
                page.rounded_rect(fx + 5.0, ry + 7.0, col_face - 10.0, row_h - 14.0, r=3.0, stroke=fg, fill=bg, line_width=0.7)
                page.rich_line(fx + col_face / 2.0, ry + 25.0, f"**{f_mk}**", size=8.0, color=fg, align="center")
                if dspec.color_key == "purple":
                    page.text(fx + col_face / 2.0, ry + 36.5, "Archetype Power", font="bold", size=6.3, color=PALETTE["purple"], align="center")
                    page.text(fx + col_face / 2.0, ry + 46.0, "Signature Protocol", font="italic", size=5.5, color=PALETTE["ink_soft"], align="center")
                else:
                    page.text(fx + col_face / 2.0, ry + 39.5, "See Market Card", font="italic", size=6.3, color=PALETTE["ink_soft"], align="center")
            elif is_glitch:
                page.rounded_rect(fx + 5.0, ry + 7.0, col_face - 10.0, row_h - 14.0, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7, dash=(2, 1.5))
                page.rich_line(fx + col_face / 2.0, ry + 26.5, f"**{f_mk}**", size=7.6, color=PALETTE["ink"], align="center")
                page.text(fx + col_face / 2.0, ry + 39.5, "Locked / 0 Output", font="mono", size=5.9, color=PALETTE["muted"], align="center")
            elif is_choice:
                page.rounded_rect(fx + 4.0, ry + 7.0, col_face - 8.0, row_h - 14.0, r=3.0, stroke=PALETTE["muted"], fill=PALETTE["white"], line_width=0.6)
                parts_c = [p.strip() for p in f_mk.split("/")]
                page.rich_line(fx + col_face / 2.0, ry + 21.5, f"**{parts_c[0]}**", size=7.4, color=PALETTE["ink"], align="center")
                page.text(fx + col_face / 2.0, ry + 31.0, "-- OR --", font="mono_bold", size=5.6, color=PALETTE["muted"], align="center")
                page.rich_line(fx + col_face / 2.0, ry + 41.5, f"**{parts_c[1]}**", size=7.4, color=PALETTE["ink"], align="center")
            else:
                page.rich_line(fx + col_face / 2.0, ry + 31.5, f"**{f_mk}**", size=8.4, color=PALETTE["ink"], align="center")

    # Bottom Rules Callout Strip (y = 494..578, h = 84 pt)
    by = 494.0
    bh = 84.0
    box_w = (712.0 - 20.0) / 3.0
    callouts = [
        (
            "CHOICE FACES ( / ) & HYBRID ( & )",
            (
                "- **Slash ( / ):** Choose **1** option in Phase 1 Step 5 *(e.g. Blue Face 4: assign as Block 1 {BLUE} Shield OR keep for +1 {WRENCH})*.\n"
                "- **Ampersand ( & ):** Gain **both** outputs in Phase 3 *(+$1 & +1 {WRENCH})*.\n"
                "- **Purple Specialist:** Dual Any-Shield baseline; Face 6 executes Archetype Signature Protocol."
            ),
        ),
        (
            "LOCKED DICE ({LOCK}) & ABSOLUTE LOCKS",
            (
                "- **{LOCK} Glitch:** Face 5 on colored dice is locked; cannot be rerolled.\n"
                "- **Track Locks:** Corruption spaces lock Cash, Patch, or Shield faces.\n"
                "- **Absolute Locks:** Locked dice CANNOT be unlocked in Phase 1 (no patch spending).\n"
                "- **Fast-Patching:** Consolidated in Phase 3 Part 3B (1 {WRENCH}: Glitched -> Scanned)."
            ),
        ),
        (
            "PERSONAL RESERVE & ZERO WEAR PIPELINE",
            (
                "- **Personal Reserve:** Each player holds **2 Purple Specialist dice** ($4–$6 (per Dossier) in Phase 3A).\n"
                "- **Zero Dice Wear:** Shields **never wear down** when blocking in Phase 2.\n"
                "- **Glitched Box:** Unresolved Glitch faces or Green Malware move to Under Development.\n"
                "- **Triage Conveyor:** Fast-Patch (**1** {WRENCH}) moves Glitched -> Scanned immediately."
            ),
        ),
    ]
    for i, (ct, cb) in enumerate(callouts):
        cx = 40.0 + i * (box_w + 10.0)
        page.rect(cx, by, box_w, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.9)
        page.rect(cx, by, box_w, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
        page.rich_line(cx + 7.0, by + 11.4, f"**{ct}**", size=7.1, color=PALETTE["ink"])
        page.rich_paragraph(cx + 7.0, by + 27.5, box_w - 14.0, cb, size=6.5, leading=9.1, color=PALETTE["ink"])


def render_four_player_pocket_aids(page: PDFPage) -> None:
    """Page 2 of Dice Aids: 4x Cut-Out Individual Player Pocket Reference Cards (2x2 grid)."""
    page.text(40.0, 18.0, "TOO MANY SECRETS // INDIVIDUAL PLAYER POCKET REFERENCE CARDS (CUT ALONG DASHED LINES — 1 PER PLAYER) [2/4]", font="mono_bold", size=6.5, color=PALETTE["muted"])

    cw, ch = 356.0, 272.0  # 4.94" x 3.78" each
    gx0, gy0 = 32.0, 26.0
    gap_x, gap_y = 16.0, 16.0

    # Dashed cut lines through center gutters
    mid_x = gx0 + cw + gap_x / 2.0
    mid_y = gy0 + ch + gap_y / 2.0
    page.line(mid_x, 16.0, mid_x, 596.0, stroke=PALETTE["muted"], width=0.5, dash=(4, 3))
    page.line(20.0, mid_y, 772.0, mid_y, stroke=PALETTE["muted"], width=0.5, dash=(4, 3))

    compact_rows = [
        ("gray", "GRAY", "Starter", ("1 Any", "1 Any", "+$1", "+$1", "$1 / 1{WRENCH}", "+1{WRENCH}")),
        ("white", "WHITE", "$1-$3", ("1 Any", "1 Any", "1 Any", "+$1", "{LOCK}Glitch", "{LOCK}Glitch")),
        ("red", "RED", "$5–$6", ("1 {RED}", "+$2", "+$2", "+$2", "{LOCK}Glitch", "{RED} {STAR}")),
        ("blue", "BLUE", "$5–$7", ("1 {BLUE}", "+1{WRENCH}", "+$1", "1{BLUE}/1{WRENCH}", "{LOCK}Glitch", "{BLUE} {STAR}")),
        ("green", "GREEN", "$5–$6", ("1 {GREEN}", "+1{WRENCH}", "+2{WRENCH}", "1{WRENCH}/$1", "{LOCK}Glitch", "{GREEN} {STAR}")),
        ("yellow", "YELLOW", "$6–$7", ("+$3", "+$2", "+$2", "$1 & 1{WRENCH}", "{LOCK}Glitch", "{YELLOW} {STAR}")),
        ("purple", "PURPLE", "Res $4–$6", ("1 Any", "1 Any", "+$2", "$1 & 1{WRENCH}", "{LOCK}Glitch", "{PURPLE}★ Protocol")),
    ]

    for r in range(2):
        for c in range(2):
            p_num = r * 2 + c + 1
            x = gx0 + c * (cw + gap_x)
            y = gy0 + r * (ch + gap_y)
            page.crop_marks(x, y, cw, ch)
            page.rect(x, y, cw, ch, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
            page.rect(x, y, cw, 18.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.8)
            page.text(x + 7.0, y + 12.5, f"CONSULTANCY DICE & OPS QUICK-AID  [P{p_num}]", font="bold", size=7.8, color=PALETTE["white"])
            page.text(x + cw - 7.0, y + 12.5, "1-6 PIP MAP", font="mono", size=6.5, color=PALETTE["rule"], align="right")

            # Mini table header
            ty = y + 18.0
            c_name = 52.0
            c_cost = 44.0
            c_f = (cw - c_name - c_cost) / 6.0  # 43.3 pt
            page.rect(x, ty, cw, 18.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
            page.text(x + 5.0, ty + 12.2, "DIE", font="bold", size=6.5, color=PALETTE["ink"])
            page.text(x + c_name + c_cost / 2.0, ty + 12.2, "COST", font="bold", size=6.5, color=PALETTE["ink"], align="center")
            for p_i in range(6):
                fx = x + c_name + c_cost + p_i * c_f
                page.line(fx, ty, fx, ty + 18.0, stroke=PALETTE["rule"], width=0.5)
                page.draw_pip_die(fx + c_f / 2.0, ty + 9.0, 11.5, p_i + 1)

            rh = 24.5
            for idx, (ck, dname, dmeta, dfaces) in enumerate(compact_rows):
                ry = ty + 18.0 + idx * rh
                fg, _ = _color_pair(ck)
                page.rect(x, ry, cw, rh, stroke=PALETTE["rule"], fill=PALETTE["white"] if idx % 2 == 0 else PALETTE["paper_tint"], line_width=0.5)
                page.draw_color_badge(x + 9.0, ry + rh / 2.0, 7.5, ck)
                page.text(x + 16.0, ry + 15.2, dname, font="bold", size=6.5, color=fg if ck != "white" else PALETTE["ink"])
                page.line(x + c_name, ry, x + c_name, ry + rh, stroke=PALETTE["rule"], width=0.5)
                page.text(x + c_name + c_cost / 2.0, ry + 15.0, dmeta, font="mono", size=5.9, color=PALETTE["ink_soft"], align="center")

                for fi, ftxt in enumerate(dfaces):
                    fx = x + c_name + c_cost + fi * c_f
                    page.line(fx, ry, fx, ry + rh, stroke=PALETTE["rule"], width=0.5)
                    page.rich_line(fx + c_f / 2.0, ry + 15.2, f"**{ftxt}**", size=6.2, color=fg if "{STAR}" in ftxt else PALETTE["ink"], align="center")

            # Compact Footer Cheat-Sheet inside each Pocket Card
            fy = ty + 18.0 + 7 * rh  # y + 207.5 -> 64.5 pt left!
            fh = y + ch - fy
            page.rect(x, fy, cw, fh, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.7)
            page.rich_paragraph(
                x + 6.0, fy + 6.0, cw - 12.0,
                "**P1 Roll & Deploy:** +1{BLACK} -> Hire {WHITE} ($1/$2/$3, max 3) -> Roll Ready + Contractors -> Up to 2 Pure Rerolls (Glitches lock immediately; no P1 patch unlocks) -> Unresolved Glitches -> Glitched Box -> Commit Shields & Income -> Hash Match (3-of-a-kind = +1 Secret).\n"
                "**P2 SETEC Compile:** Drop Staging Cup -> 2A: {BLACK} advances track (4/5/6=Upgr/Singularity) -> 2B: Resolve vs Shields (Zero Wear!) -> Dmg: {RED} -$1 (Unpaid: -1 Secret) | {BLUE} -1 Secret | {GREEN} Glitch 1 die (Income 1st, then Shield; empty: destroy Under Dev) -> Recycle {RED}{BLUE}{GREEN} -> 2C: End Check (Singularity or <=0 Secrets).\n"
                "**P3 Operations & Pipeline:** Collect Income ($/🔧/★) -> Buy <=2 dice (Market R/B/G/Y or $4–$6 (per Dossier) Personal Reserve Purple) -> Fast-Patch (1{WRENCH}: Glitched -> Scanned) -> Scanned -> Ready -> In Production -> Ready -> Glitched -> Scanned -> Cap held 🔧 at 3 -> Pass 1st Player.\n"
                "**VICTORY:** Most Corporate Secrets among survivors. Patient Zero (<=0 Secrets) eliminated. Ties: 1. $ Capital  2. Ready Modules  3. Patches  4. Fewest Under Dev.",
                size=5.4, leading=7.7, color=PALETTE["ink"],
            )
            # Mini CI/CD Conveyor summary bar at bottom
            cb_y = y + ch - 13.0
            page.rect(x + 5.0, cb_y, cw - 10.0, 11.0, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.5)
            page.rich_line(x + cw / 2.0, cb_y + 8.2, "**CI/CD CONVEYOR:** Glitched  --(1 {WRENCH} Fast-Patch)-->  Scanned  ---->  Ready for Release (Round End)", size=5.2, color=PALETTE["ink_soft"], align="center")


def _draw_single_variant_card(page: PDFPage, x: float, y: float, w: float, h: float, card: VariantCardSpec) -> None:
    """Draw a single 120 x 182 pt Software Module Variant (★) Market Card."""
    fg, bg = _color_pair(card.color_key)
    page.crop_marks(x, y, w, h, length=4.5, offset=2.0)
    page.rounded_rect(x, y, w, h, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)

    # Top Color Banner
    page.rect(x, y, w, 22.0, stroke=PALETTE["ink"], fill=bg, line_width=0.8)
    page.rect(x, y, w, 3.5, stroke=None, fill=fg)
    page.draw_color_badge(x + 10.5, y + 12.8, 8.5, card.color_key)
    page.text(x + 19.0, y + 15.2, card.die_label, font="bold", size=6.9, color=fg)
    # Code pill on right
    page.rounded_rect(x + w - 24.0, y + 5.5, 19.0, 12.0, r=2.0, stroke=fg, fill=PALETTE["white"], line_width=0.7)
    page.text(x + w - 14.5, y + 13.8, card.code, font="mono_bold", size=6.8, color=fg, align="center")

    # Cost Sub-bar
    page.rect(x, y + 22.0, w, 14.5, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.text(x + w / 2.0, y + 31.8, f"Cost: {card.cost_str}", font="bold", size=7.2, color=PALETTE["ink"], align="center")

    # Base Faces 1-4 Mini Reference
    page.rich_line(x + w / 2.0, y + 48.0, card.base_summary_1, size=6.1, color=PALETTE["ink_soft"], align="center")
    page.rich_line(x + w / 2.0, y + 59.5, card.base_summary_2, size=5.9, color=PALETTE["ink_soft"], align="center")

    # Prominent Face 6 (★) Variant Box
    sy = y + 66.0
    sh = h - 66.0 - 18.0  # 98 pt tall
    page.rect(x + 5.0, sy, w - 10.0, sh, stroke=fg, fill=PALETTE["white"], line_width=0.9)
    page.rect(x + 5.0, sy, w - 10.0, 17.5, stroke=fg, fill=bg, line_width=0.6)
    page.draw_pip_die(x + 16.0, sy + 8.8, 11.0, 6)
    page.rich_line(x + w - 9.0, sy + 11.8, "{STAR} **FACE 6 VARIANT**", size=6.8, color=fg, align="right")

    # Variant Title & Timing
    page.text(x + w / 2.0, sy + 30.5, card.name.upper(), font="bold", size=7.5, color=PALETTE["ink"], align="center")
    page.text(x + w / 2.0, sy + 40.0, card.timing, font="mono_bold", size=5.7, color=fg, align="center")
    page.line(x + 10.0, sy + 44.0, x + w - 10.0, sy + 44.0, stroke=PALETTE["rule"], width=0.5)

    # Variant Effect Body
    page.rich_paragraph(x + 9.0, sy + 55.5, w - 18.0, card.effect, size=6.65, leading=9.2, color=PALETTE["ink"])

    # Bottom Lock / Passive Note
    page.text(x + w / 2.0, y + h - 6.5, card.lock_note, font="italic", size=5.7, color=PALETTE["muted"], align="center")


def _draw_color_divider_card(page: PDFPage, x: float, y: float, w: float, h: float, dspec: DieSpec, variants: Sequence[VariantCardSpec]) -> None:
    """Draw a bonus All-in-One Market Summary / Divider Card for a die color."""
    fg, bg = _color_pair(dspec.color_key)
    page.crop_marks(x, y, w, h, length=4.5, offset=2.0)
    page.rounded_rect(x, y, w, h, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.0)
    page.rect(x, y, w, 22.0, stroke=PALETTE["ink"], fill=fg, line_width=0.8)
    page.text(x + w / 2.0, y + 14.5, f"{dspec.title} // ALL VARIANTS", font="bold", size=7.2, color=PALETTE["white"], align="center")
    page.text(x + w / 2.0, y + 33.0, f"Market Cost: {dspec.cost_str}", font="bold", size=5.8, color=PALETTE["ink_soft"], align="center")

    cy = y + 46.0
    for v in variants:
        page.rounded_rect(x + 5.0, cy - 8.5, w - 10.0, 40.0, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
        page.text(x + 9.0, cy + 1.0, f"[{v.code}] {v.name}", font="bold", size=6.4, color=fg)
        page.rich_paragraph(x + 9.0, cy + 10.5, w - 18.0, v.effect, size=5.6, leading=7.5, color=PALETTE["ink"])
        cy += 44.0


def render_variant_market_cards_pages(page3: PDFPage, page4: PDFPage) -> None:
    """Pages 3 & 4 of Dice Aids: All 12 Printable Variant (★) Market Cards (120 x 182 pt) + 4 Deck Summary Cards."""
    # Organize by Color Column (Red, Blue, Green, Yellow) so cutting & sorting is effortless!
    by_color: Dict[str, List[VariantCardSpec]] = {"red": [], "blue": [], "green": [], "yellow": []}
    for vc in VARIANT_CARDS:
        if vc.color_key in by_color:
            by_color[vc.color_key].append(vc)
    order = ["red", "blue", "green", "yellow"]

    cw, ch = 120.0, 182.0  # 1.67" x 2.53" — fits inside 124 x 190 pt Market Board slots!
    gap_x = 40.0
    gap_y = 28.0
    total_w = 4 * cw + 3 * gap_x  # 600 pt
    x0 = (792.0 - total_w) / 2.0  # 96.0 pt
    y0 = 48.0

    # Page 3: Row 0 = Set 1 (R1..Y1 Baseline), Row 1 = Set 2 (R2..Y2)
    page3.text(52.0, 26.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS — SHEET 1 (SETS 1 & 2) [3/4]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    page3.text(740.0, 26.0, "SIZE: 1.67\" x 2.53\" (FITS MARKET BOARD)", font="mono", size=6.5, color=PALETTE["muted"], align="right")

    for col_idx, ckey in enumerate(order):
        cx = x0 + col_idx * (cw + gap_x)
        _draw_single_variant_card(page3, cx, y0, cw, ch, by_color[ckey][0])
        _draw_single_variant_card(page3, cx, y0 + ch + gap_y, cw, ch, by_color[ckey][1])

    page3.text(396.0, 594.0, "Setup: Shuffle the 3 Variant (STAR) cards of each market color (R/B/G/Y) and place 1 face-up in each Market slot (Row 1 = Default Baseline R1-Y1).", font="italic", size=6.8, color=PALETTE["muted"], align="center")

    # Page 4: Row 0 = Set 3 (R3..Y3), Row 1 = 4 Color Reference / Divider Cards
    page4.text(52.0, 26.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS — SHEET 2 (SET 3 + DIVIDERS) [4/4]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    page4.text(740.0, 26.0, "SIZE: 1.67\" x 2.53\" (FITS MARKET BOARD)", font="mono", size=6.5, color=PALETTE["muted"], align="right")

    spec_map = {d.color_key: d for d in DICE_SPECS}
    for col_idx, ckey in enumerate(order):
        cx = x0 + col_idx * (cw + gap_x)
        _draw_single_variant_card(page4, cx, y0, cw, ch, by_color[ckey][2])
        _draw_color_divider_card(page4, cx, y0 + ch + gap_y, cw, ch, spec_map[ckey], by_color[ckey])

    page4.text(396.0, 594.0, "Bottom row provides optional All-Variants Divider / Reference cards for storing each 3-card color mini-deck. Purple uses Archetype Signature Protocols.", font="italic", size=6.8, color=PALETTE["muted"], align="center")


# =============================================================================
# 4. Printable SETEC Version Cards/Tiles + Optional Cut-Out PnP Tokens (2 Pages)
# =============================================================================

def _draw_version_tile(page: PDFPage, x: float, y: float, w: float, h: float, tile: VersionTileSpec) -> None:
    """Draw a 212 x 112 pt SETEC Version Tile sized to fit inside the 220 x 120 pt Agent Board slots."""
    page.crop_marks(x, y, w, h, length=5.5, offset=2.5)
    page.rounded_rect(x, y, w, h, r=3.5, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.2)

    # Top Header Bar
    ver_bg = PALETTE["ink"] if tile.version == "v3.0" else (PALETTE["ink_soft"] if tile.version == "v2.0" else PALETTE["panel_tint"])
    ver_fg = PALETTE["white"] if tile.version in ("v3.0", "v2.0") else PALETTE["ink"]
    page.rect(x, y, w, 20.0, stroke=PALETTE["ink"], fill=ver_bg, line_width=0.9)

    # Version pill on left
    page.rounded_rect(x + 5.0, y + 3.0, 28.0, 14.0, r=2.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.7)
    page.text(x + 19.0, y + 12.8, tile.version, font="mono_bold", size=7.8, color=PALETTE["ink"], align="center")

    # Card Name
    page.text(x + 38.0, y + 13.8, tile.name.upper(), font="bold", size=8.0, color=ver_fg)

    # Profile badge on right
    page.text(x + w - 6.0, y + 13.2, tile.profile, font="mono", size=5.8, color=PALETTE["rule"] if tile.version in ("v3.0", "v2.0") else PALETTE["muted"], align="right")

    # Banner Row (y + 20 .. y + 35)
    py_bar = y + 20.0
    page.rect(x, py_bar, w, 15.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.rich_line(x + 6.0, py_bar + 10.5, tile.banner_text, size=5.8, color=PALETTE["ink"])

    # Corruption Track Spaces (y + 35 .. y + 109)
    y_track = py_bar + 17.0
    sh = 70.0
    n_spaces = len(tile.spaces)
    gap = 3.0
    sw = (w - 10.0 - (n_spaces - 1) * gap) / n_spaces

    for i, sp in enumerate(tile.spaces):
        sx = x + 5.0 + i * (sw + gap)
        bg = PALETTE["red_light"] if sp.is_singularity else (PALETTE["panel_tint"] if sp.is_milestone else PALETTE["white"])
        border = PALETTE["red"] if sp.is_singularity else (PALETTE["ink"] if sp.is_milestone else PALETTE["rule"])
        lw = 1.1 if (sp.is_singularity or sp.is_milestone) else 0.6
        page.rounded_rect(sx, y_track, sw, sh, r=2.5, stroke=border, fill=bg, line_width=lw)

        # Space Number Pill
        badge_w = min(16.0, sw - 4.0)
        page.rounded_rect(sx + (sw - badge_w) / 2.0, y_track + 2.5, badge_w, 8.5, r=1.5, stroke=border, fill=PALETTE["white"], line_width=0.5)
        page.text(sx + sw / 2.0, y_track + 8.5, str(sp.num), font="mono_bold", size=5.8, color=border, align="center")

        # Cube placement outline
        page.rect(sx + (sw - 14.0) / 2.0, y_track + 13.0, 14.0, 14.0, stroke=PALETTE["muted"], fill=PALETTE["paper_tint"], line_width=0.5, dash=(2, 2))
        page.rich_line(sx + sw / 2.0, y_track + 22.5, "{BLACK}", size=5.5, color=PALETTE["muted"], align="center")

        # Space effect text below
        page.rich_paragraph(sx + 1.0, y_track + 33.0, sw - 2.0, sp.label, size=4.9, leading=6.5, color=PALETTE["ink"], align="center")


def render_version_tiles_page(page: PDFPage) -> None:
    """Page 1 of Version Cards PDF: All 6 SETEC Version Tiles (v3.0, v2.0, v1.0) in 2x3 grid."""
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // PRINTABLE ROGUE AGENT VERSION TILES [1/2]",
        right_tag="TILE SIZE: 2.94\" x 1.56\" (FITS AGENT BOARD SLOTS)",
    )

    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "SETEC VERSION ROADMAP TILES  (v1.0  /  v2.0  /  v3.0)", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "CUT ALONG CROP MARKS  |  DEAL 1 PER TIER ON AGENT BOARD", font="mono", size=7.0, color=PALETTE["rule"], align="right")

    tw, th = 212.0, 112.0
    gap_x, gap_y = 48.0, 32.0
    grid_w = 2 * tw + gap_x  # 472 pt
    gx0 = (792.0 - grid_w) / 2.0 + 36.0  # leave room on left for tier legend!
    gy0 = 84.0

    # Left Tier Legend labels
    tier_notes = [
        ("v3.0 TILES", "Deal 1 face-up\nto top slot.\n6-space Track:\nSpace 6 = SINGULARITY!"),
        ("v2.0 TILES", "Deal 1 face-up\nto middle slot.\n5-space Track:\nSpace 5 = Upgrade."),
        ("v1.0 TILES", "Deal 1 face-up\nto bottom slot.\n4-space Track:\nSpace 4 = Upgrade."),
    ]
    for r_i, (t_head, t_desc) in enumerate(tier_notes):
        ry = gy0 + r_i * (th + gap_y)
        page.rounded_rect(48.0, ry + 12.0, 102.0, 88.0, r=4.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.7)
        page.text(99.0, ry + 28.0, t_head, font="bold", size=8.5, color=PALETTE["ink"], align="center")
        page.rich_paragraph(56.0, ry + 43.0, 86.0, t_desc, size=6.8, leading=9.5, color=PALETTE["muted"], align="center")

    # 2x3 Grid of Version Tiles
    for idx, vtile in enumerate(VERSION_TILES):
        r = idx // 2
        c = idx % 2
        tx = gx0 + c * (tw + gap_x)
        ty = gy0 + r * (th + gap_y)
        _draw_version_tile(page, tx, ty, tw, th, vtile)

    page.text(
        396.0, 566.0,
        "Cut along corner crop marks. Each tile (2.94\" x 1.56\") nests directly inside the v1.0, v2.0, and v3.0 slots on the SETEC Central Agent Board.",
        font="italic", size=7.2, color=PALETTE["ink_soft"], align="center",
    )


def render_pnp_tokens_page(page: PDFPage) -> None:
    """Page 2 of Version Cards PDF: Optional Cut-Out Markers & Prototype Chits."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // OPTIONAL CUT-OUT PROTOTYPE MARKERS & TOKENS [2/2]",
        right_tag="USE COINS / CUBES OR CUT THESE CHITS",
    )

    page.rect(40.0, 32.0, 712.0, 22.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.9)
    page.text(50.0, 46.8, "OPTIONAL PRINT-AND-PLAY TOKENS & STATUS MARKERS  (CUT GRID)", font="bold", size=9.2, color=PALETTE["ink"])
    page.text(742.0, 46.5, "1st PLAYER + VERSION MARKER + SECRETS + PATCHES + CREDITS", font="mono", size=6.8, color=PALETTE["muted"], align="right")

    # Row 1 (y = 64..122): Special Markers + 18x Archetype Slot Markers ([USED] / [FORFEIT])
    # Lead Consultant Marker
    page.rounded_rect(42.0, 64.0, 118.0, 52.0, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.2)
    page.text(101.0, 84.0, "LEAD CONSULTANT", font="bold", size=8.5, color=PALETTE["white"], align="center")
    page.text(101.0, 96.5, "1ST PLAYER MARKER", font="mono_bold", size=6.8, color=PALETTE["rule"], align="center")
    page.text(101.0, 108.5, "Pass Clockwise End of P3", font="italic", size=6.0, color=PALETTE["rule"], align="center")

    # Active SETEC Version Marker
    page.rounded_rect(170.0, 64.0, 112.0, 52.0, r=4.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=1.2)
    page.text(226.0, 84.0, "ACTIVE VERSION >>", font="bold", size=8.5, color=PALETTE["red"], align="center")
    page.text(226.0, 97.5, "SETEC TIER POINTER", font="mono_bold", size=6.6, color=PALETTE["ink"], align="center")
    page.text(226.0, 108.5, "Move v1.0 -> v2.0 -> v3.0", font="italic", size=6.0, color=PALETTE["ink_soft"], align="center")

    # 12x Archetype Ability Status Chits (place on v1.0 / v2.0 / v3.0 boxes on Player Board)
    ax0, ay0 = 294.0, 64.0
    aw, ah = 38.0, 25.0
    for i in range(12):
        r = i // 6
        c = i % 6
        bx = ax0 + c * (aw + 36.0 if False else (aw + 39.0))
    # Clean tight 6x2 grid across x = 294..750 (width = 456 -> 6 * 73 + 5 * 3.6 = 456)
    aw = 73.0
    agap = 3.6
    for i in range(12):
        r = i // 6
        c = i % 6
        bx = 294.0 + c * (aw + agap)
        by = 64.0 + r * (ah + 2.0)
        is_used = (r == 0)
        page.rect(bx, by, aw, ah, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"] if is_used else PALETTE["white"], line_width=0.6, dash=(2, 1))
        page.text(bx + aw / 2.0, by + 11.5, "[X] ABILITY USED" if is_used else "[/] FORFEITED", font="mono_bold", size=6.2, color=PALETTE["ink"] if is_used else PALETTE["muted"], align="center")
        page.text(bx + aw / 2.0, by + 20.5, "Archetype Slot", font="regular", size=5.5, color=PALETTE["muted"], align="center")

    # Section 2 (y = 128..292): 32x Corporate Secret Chits (8 cols x 4 rows)
    page.text(42.0, 136.0, "CORPORATE SECRET TOKENS (x32 — PRIMARY OBJECTIVE / 1 PT EACH)", font="mono_bold", size=6.8, color=PALETTE["blue"])
    sw = (710.0) / 8.0  # 88.75 pt
    sh = 36.0
    sy0 = 141.0
    for r in range(4):
        for c in range(8):
            bx = 41.0 + c * sw
            by = sy0 + r * sh
            page.rect(bx, by, sw, sh, stroke=PALETTE["blue"], fill=PALETTE["white"], line_width=0.6, dash=(3, 1.5))
            page.draw_secret_icon(bx + 15.0, by + 18.0, 12.0, color=PALETTE["blue"])
            page.text(bx + 26.0, by + 16.0, "SECRET", font="bold", size=7.6, color=PALETTE["blue"])
            page.text(bx + 26.0, by + 26.5, "1 Pt  |  Client Data", font="regular", size=5.8, color=PALETTE["muted"])

    # Section 3 (y = 298..410): 16x Patch (🔧) Tokens (8 cols x 2 rows)
    page.text(42.0, 300.0, "SPLICE / PATCH TOKENS (x16 — CLEANUP CAP: MAX 3 HELD)", font="mono_bold", size=6.8, color=PALETTE["green"])
    py0 = 305.0
    ph = 42.0
    for r in range(2):
        for c in range(8):
            bx = 41.0 + c * sw
            by = py0 + r * ph
            page.rect(bx, by, sw, ph, stroke=PALETTE["green"], fill=PALETTE["green_light"], line_width=0.6, dash=(3, 1.5))
            page.draw_wrench_icon(bx + 15.0, by + 21.0, 13.0, color=PALETTE["green"])
            page.text(bx + 26.0, by + 18.5, "1 PATCH", font="bold", size=7.6, color=PALETTE["green"])
            page.text(bx + 26.0, by + 29.5, "Fast-Patch (1/die)", font="regular", size=5.6, color=PALETTE["ink_soft"])

    # Section 4 (y = 404..574): Currency Chits ($1 x 24 + $5 x 16)
    page.text(42.0, 404.0, "CONSULTANCY CREDITS ($1 x 24  &  $5 x 16)", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    cy0 = 409.0
    ch_h = 33.0
    for r in range(5):
        is_five = (r >= 3)
        val = "$5" if is_five else "$1"
        sub = "FIVE CREDITS" if is_five else "ONE CREDIT"
        fill_c = PALETTE["panel_tint"] if is_five else PALETTE["white"]
        for c in range(8):
            bx = 41.0 + c * sw
            by = cy0 + r * ch_h
            page.rect(bx, by, sw, ch_h, stroke=PALETTE["ink_soft"], fill=fill_c, line_width=0.55, dash=(3, 1.5))
            page.text(bx + 18.0, by + 21.0, val, font="bold", size=11.0, color=PALETTE["ink"], align="center")
            page.text(bx + 34.0, by + 16.5, sub, font="mono_bold", size=5.8, color=PALETTE["ink_soft"])
            page.text(bx + 34.0, by + 25.5, "Tiebreak Asset", font="regular", size=5.4, color=PALETTE["muted"])


# =============================================================================
# Build All Standalone & Combined Print-and-Play PDFs
# =============================================================================

def generate_all_pdfs(out_dir: str) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    generated: List[str] = []

    # 1. Player Terminal Mats & Split Cards (6 pages: 4x Mats with empty modular docks + 1x Company Cards + 1x White Hat Cards)
    doc_players = PDFDocument("Too Many Secrets - Player Terminal Mats & Split Cards (v0.26.0)")
    for idx in range(1, 5):
        p = doc_players.add_page()
        render_player_board(p, idx)

    # Page 5: 6x Client Company Cards Sheet
    render_company_cards_page(doc_players.add_page())

    # Page 6: 6x White Hat Dossier Cards Sheet
    render_white_hat_dossiers_page(doc_players.add_page())

    path_players = os.path.join(out_dir, "01_Player_Boards.pdf")
    doc_players.save(path_players)
    generated.append(path_players)

    # 2. Central Agent Board + Companion Software Market Board (2 pages)
    doc_central = PDFDocument("Too Many Secrets - Central Agent & Market Boards")
    render_agent_board(doc_central.add_page())
    render_market_board(doc_central.add_page())
    path_central = os.path.join(out_dir, "02_Central_Game_Boards.pdf")
    doc_central.save(path_central)
    generated.append(path_central)

    # 3. Dice Visual Aids & Printable Variant (★) Market Cards (4 pages)
    doc_dice = PDFDocument("Too Many Secrets - Dice Visual Aids & Variant Market Cards")
    render_master_dice_reference(doc_dice.add_page())
    render_four_player_pocket_aids(doc_dice.add_page())
    render_variant_market_cards_pages(doc_dice.add_page(), doc_dice.add_page())
    path_dice = os.path.join(out_dir, "03_Dice_Visual_Aids_and_Market_Cards.pdf")
    doc_dice.save(path_dice)
    generated.append(path_dice)

    # 4. Printable SETEC Version Cards/Tiles + Optional PnP Tokens (2 pages)
    doc_versions = PDFDocument("Too Many Secrets - SETEC Version Tiles & PnP Tokens")
    render_version_tiles_page(doc_versions.add_page())
    render_pnp_tokens_page(doc_versions.add_page())
    path_versions = os.path.join(out_dir, "04_SETEC_Version_Cards_and_Tokens.pdf")
    doc_versions.save(path_versions)
    generated.append(path_versions)

    # 5. Combined Master Print-and-Play Pack (All 14 pages)
    doc_master = PDFDocument("Too Many Secrets - Complete Print and Play Prototype (v0.26.0)")
    for sub_doc in (doc_central, doc_players, doc_dice, doc_versions):
        for pg in sub_doc.pages:
            doc_master.pages.append(pg)
    path_master = os.path.join(out_dir, "00_Too_Many_Secrets_Complete_PnP.pdf")
    doc_master.save(path_master)
    generated.append(path_master)

    return generated


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base, "output")
    files = generate_all_pdfs(base)
    files_out = generate_all_pdfs(out_dir)
    for f in files:
        print(f"Generated: {f} ({os.path.getsize(f):,} bytes)")
    for f in files_out:
        print(f"Generated (output/): {f} ({os.path.getsize(f):,} bytes)")
