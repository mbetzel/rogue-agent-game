"""Master Print-and-Play PDF Generator for Too Many Secrets (Rogue Agent v0.47.0 Baseline).

Generates minimalist, ink-saver, print-ready US Letter (11" x 8.5") PDFs:
  - 01_Player_Boards.pdf (6 pages — 4x Company Terminal Mats with CI/CD Pipeline loop + 6x Client Company Cards sheet + 6x White Hat Dossier Cards sheet)
  - 02_Central_Game_Boards.pdf (2 pages — SETEC Agent & Market Share Board + Market & Supply Board)
  - 03_Dice_Visual_Aids_and_Market_Cards.pdf (5 pages — Master Pip Aid, 4x Dice Pocket Aids, 4x Six-Phase Round Reference Cards, 12x Variant ★ Cards)
  - 04_SETEC_Version_Cards_and_Tokens.pdf (2 pages — 6x SETEC Version Tiles sized to board slots + Cut-Out PnP Tokens)
  - 00_Too_Many_Secrets_Complete_PnP.pdf (All 15 pages combined in print order)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from pnp.illustrations import draw_character_illustration
from pnp.pdf_engine import PALETTE, Color, PDFDocument, PDFPage, measure_text


# =============================================================================
# Canonical Game Data (Synchronized 1:1 with RULES.md v0.47.0 Baseline & sim/entities.py)
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
    starting_die: str = ""
    hardware_summary: str = ""
    starting_bonus: str = ""


COMPANIES: List[CompanyCardSpec] = [
    CompanyCardSpec(
        code="MERIDIAN",
        name="Meridian Financial Trust",
        sector="Banking Infrastructure",
        override_name="Capital Injection",
        override_timing="P3: INCOME",
        override_desc=(
            "Gain **+$3 Cash** from the bank."
        ),
        flavor='"When liquidity is limitless, capital allocation is an offensive discipline."',
        starting_die="RED",
    ),
    CompanyCardSpec(
        code="OMNIDYNE",
        name="Omnidyne Systems",
        sector="Tech Giant",
        override_name="Magnetic Splice",
        override_timing="P6: CI/CD STEP 1",
        override_desc=(
            "Move **1 die** from your **Processing Box** directly to your "
            "**Ready for Release Zone** for **free** (bypassing Scanned); it banks its Secret now."
        ),
        flavor='"Proprietary hardware backplanes allow instantaneous hot-swapping under live load."',
        starting_die="GREEN",
    ),
    CompanyCardSpec(
        code="AEGIS",
        name="Aegis Defense Relay",
        sector="Security Firm",
        override_name="Baffle Echo",
        override_timing="P4: ATTACK RESOLUTION",
        override_desc=(
            "Ignore **1 {RED} cube**, **1 {BLUE} cube**, or the **Secret loss** of **1 {GREEN} hit** for yourself "
            "this round (your Vulnerability still resets). Exited cubes recycle as normal."
        ),
        flavor='"Multi-layered kinetic dampeners disperse inbound network blast energy."',
        starting_die="BLUE",
    ),
    CompanyCardSpec(
        code="DTO",
        name="Department of Telecom Oversight",
        sector="Federal Agency",
        override_name="Slush Fund",
        override_timing="P4: ONCE PER GAME",
        override_desc=(
            "The DTO accesses emergency black budget reserves: absorb up to **2 Corporate Secret loss** "
            "from **{BLUE} cubes** for free. **Once per game** (optional when it applies)."
        ),
        flavor='"Classified black budget allocations absorb compliance failures without public oversight."',
        starting_die="BLUE",
    ),
    CompanyCardSpec(
        code="HELIX",
        name="Helix Biomedical Consortium",
        sector="Medical Research",
        override_name="Brute-Force Bypass",
        override_timing="P1: STEP 3 REROLLS",
        override_desc=(
            "Gain **1 extra free reroll** this phase. In addition, turn **1 rolled die** "
            "to any legal non-Star face of its color (the Secret face is allowed)."
        ),
        flavor='"Massively parallel quantum sequencing breaks deterministic encryption gates."',
        starting_die="GREEN",
    ),
    CompanyCardSpec(
        code="PROMETHEUS",
        name="The Prometheus Foundation",
        sector="Non-Profit",
        override_name="Algorithmic Arbitrage",
        override_timing="P5: OPERATIONS",
        override_desc=(
            "In Phase 5: Operations, purchase **1 Colored Die** from the Central "
            "Market at a **$2 discount** (min $0) into your **Scanned Box**, **OR** gain an immediate **+$2 cash payout** "
            "from the bank."
        ),
        flavor='"Open-source cryptographic protocols circumvent proprietary enterprise licensing fees."',
        starting_die="RED",
    ),
]


@dataclass(frozen=True)
class WhiteHatDossierSpec:
    code: str
    name: str
    role: str
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
        flavor='"Optimized resource pipelines yield sustained intelligence."',
        purple_faces=("+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$2", "+$1 & +1 {RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE} {STAR}"),
        protocol_name="Logistics Bounty",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "Gain **+1 {RESEARCH} Research Token** per different color die currently in your **Scanned Box** *(all colors incl. Gray, Purple, Yellow)*."
        ),
    ),
    WhiteHatDossierSpec(
        code="PHREAKER",
        name="The Phreaker",
        role="Hardware Intrusion Specialist",
        flavor='"Raw voltage pulses extract signal from dormant silicon."',
        purple_faces=("+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$2", "+$1 & +1 {RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE} {STAR}"),
        protocol_name="Jumper Diagnostics",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "Gain **+$1 cash** AND **+1 Release Bandwidth** this round *(applies in Phase 6 Step 3)*."
        ),
    ),
    WhiteHatDossierSpec(
        code="ACOUSTIC",
        name="The Acoustic",
        role="Side-Channel Cryptanalyst",
        flavor='"Harmonic resonance frequencies decode physical chassis vibrations."',
        purple_faces=("+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$2", "+$1 & +1 {RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE} {STAR}"),
        protocol_name="Resonance Sensor",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "Gain **+$1 cash** per unique colored cube that exited the Cube Tower this round "
            "*(including Operative Signature Cubes)*, up to **+$5 max**."
        ),
    ),
    WhiteHatDossierSpec(
        code="SPOOK",
        name="The Spook",
        role="Covert Intelligence Specialist",
        flavor='"Scorched-earth protocols ensure zero forensic recovery."',
        purple_faces=("+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$2", "+$1 & +1 {RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE} {STAR}"),
        protocol_name="Burn Notice",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "Gain **+$2 cash**; optionally permanently return **1** owned **Gray Legacy Die** "
            "to the box for **+$3 cash**."
        ),
    ),
    WhiteHatDossierSpec(
        code="PRODIGY",
        name="The Prodigy",
        role="Autonomous Exploit Hacker",
        flavor='"Payload injection executes before memory boundaries establish."',
        purple_faces=("+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$2", "+$1 & +1 {RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE} {STAR}"),
        protocol_name="Arbitrary Code Execution",
        protocol_timing="P1: STEP 4",
        protocol_desc=(
            "*(After rerolls, before assignment.)* Turn **1 other rolled die** in your active "
            "pool to **any legal non-Star face of its color** other than the Secret face."
        ),
    ),
    WhiteHatDossierSpec(
        code="CIPHER",
        name="The Cipher",
        role="Distributed Ledger Architect",
        flavor='"Parity calculations balance zero-knowledge proofs flawlessly."',
        purple_faces=("+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$2", "+$1 & +1 {RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE} {STAR}"),
        protocol_name="Algorithmic Parity",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "Gain **+$2 cash** AND **+1 {RESEARCH} Research Token**."
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
        cost_str="Starter (2 each)",
        faces=("+$1 & +1 {RESEARCH} {WARN}", "+2 {RESEARCH} {WARN}", "+$2 / +2 {RESEARCH} {WARN}", "+$1 / +1 {RESEARCH}", "+$1", "+1 {RESEARCH}"),
        notes="Start: 2 Gray + 1 starting colored die + 1 Purple in Ready for Release; more Gray via Level 1 Breakthroughs. Faces 3-4 are Choices (/): declare in Phase 1 Step 4. {WARN} = +1 Vulnerability if kept.",
    ),
    DieSpec(
        color_key="red",
        title="RED",
        subtitle="Marketing",
        cost_str="$4-$5 (by Variant)",
        faces=("+1 Market Share / +$1 {WARN}", "+$2", "+$2", "+$2", "{SECRET} Secret {WARN}", "{RED} {STAR}"),
        notes="Marketing revenue & Market Share. Face 5 Secret face (+2), Face 6 Red {STAR}.",
    ),
    DieSpec(
        color_key="blue",
        title="BLUE",
        subtitle="Firewall",
        cost_str="$4-$5 (by Variant)",
        faces=("+1 Corporate Secret", "+2 {RESEARCH}", "+$2 {WARN}", "+1 {RESEARCH} / +$1", "{SECRET} Secret {WARN}", "{BLUE} {STAR}"),
        notes="Direct Secrets. Face 5 Secret face (+2, or +3 at Pen Test L3+), Face 6 Blue {STAR}.",
    ),
    DieSpec(
        color_key="green",
        title="GREEN",
        subtitle="Antivirus",
        cost_str="$4-$5 (by Variant)",
        faces=("+2 {RESEARCH} {WARN}", "+1 {RESEARCH}", "+2 {RESEARCH}", "+1 {RESEARCH} / +$1", "{SECRET} Secret {WARN}", "{GREEN} {STAR}"),
        notes="Premier Research engine. Face 5 Secret face (+2, then -2 Vulnerability), Face 6 Green {STAR}.",
    ),
    DieSpec(
        color_key="yellow",
        title="YELLOW",
        subtitle="Commercial AI",
        cost_str="$5-$6 (by Variant)",
        faces=("+2 Market Share {WARN}", "+1 Market Share / +1 {RESEARCH}", "+$1 & +1 Market Share", "+$2 / +1 {RESEARCH}", "+$2 / +1 {RESEARCH} {WARN}", "{YELLOW} {STAR}"),
        notes="Commercial AI revenue & Market Share. No Secret face. Face 6 Yellow {STAR}.",
    ),
    DieSpec(
        color_key="purple",
        title="PURPLE",
        subtitle="Specialist AI",
        cost_str="Not sold (Public Rel. L3)",
        faces=("+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$2", "+$1 & +1 {RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE} {STAR}"),
        notes="Not purchasable. 2nd Purple die only from Public Relations Track Level 3. Faces 1-2 are Choices (/). Face 5 Secret face (+1), Face 6 Purple {STAR} Signature Protocol.",
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
    footer_note: str


VARIANT_CARDS: List[VariantCardSpec] = [
    VariantCardSpec(
        'R1', 'red', 'RED // MARKETING', '$5',
        '{PIP1} +1 Share/$1 {WARN} | {PIP2}{PIP3}{PIP4} +$2', '{PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Brand Protection', 'P3 INCOME',
        'Gain **+$2 & +1 Market Share** *(not above max; outside Public Relations limit)*.',
        'Brand Protection: +$2 & +1 Market Share.',
    ),
    VariantCardSpec(
        'R2', 'red', 'RED // MARKETING', '$4',
        '{PIP1} +1 Share/$1 {WARN} | {PIP2}{PIP3}{PIP4} +$2', '{PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Ad Campaign', 'P3 INCOME',
        'Pay **$2** to gain **+2 Market Share** *(not above max; outside Public Relations limit)*.',
        'Ad Campaign: pay $2 for +2 Market Share.',
    ),
    VariantCardSpec(
        'R3', 'red', 'RED // MARKETING', '$5',
        '{PIP1} +1 Share/$1 {WARN} | {PIP2}{PIP3}{PIP4} +$2', '{PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Customer Poaching', 'P3 AFTER ALL INCOME',
        'After all players collect Income, take **1 Market Share** from the surviving rival with the **most** *(you choose among ties)*. At your max, the rival still loses 1.',
        'Poaching: take 1 Market Share from the leader.',
    ),
    VariantCardSpec(
        'B1', 'blue', 'BLUE // FIREWALL', '$5',
        '{PIP1} +1 Secret | {PIP2} +2{RESEARCH} | {PIP3} +$2 {WARN}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Honeypot Telemetry', 'P3 INCOME',
        'Gain **+2 {RESEARCH}** if **0 {BLUE} Blue** cubes are in the Exit Tray, **OR** gain **+$3** if **1+ {BLUE} Blue** cubes are in the Exit Tray.',
        'Honeypot: +2 Research (0 Blue) or +$3 (1+ Blue).',
    ),
    VariantCardSpec(
        'B2', 'blue', 'BLUE // FIREWALL', '$5',
        '{PIP1} +1 Secret | {PIP2} +2{RESEARCH} | {PIP3} +$2 {WARN}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Deep R&D Vault', 'P3 INCOME',
        'Gain **+$2**, **OR** spend **1 Corporate Secret** to gain **+3 Market Share** *(not above max; outside Public Relations limit)*.',
        'R&D Vault: +$2 or spend 1 Secret for +3 Share.',
    ),
    VariantCardSpec(
        'B3', 'blue', 'BLUE // FIREWALL', '$4',
        '{PIP1} +1 Secret | {PIP2} +2{RESEARCH} | {PIP3} +$2 {WARN}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Air-Gapped Backup', 'P3 INCOME',
        'Gain **+$2** and lower your **Vulnerability** by **1**.',
        'Air-Gapped: +$2 & -1 Vulnerability.',
    ),
    VariantCardSpec(
        'G1', 'green', 'GREEN // ANTIVIRUS', '$5',
        '{PIP1} +2{RESEARCH} {WARN} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Self-Healing Kernel', 'P3 INCOME',
        'Lower your **Vulnerability** by **2** and gain **+1 {RESEARCH}**.',
        'Kernel: -2 Vulnerability & +1 Research.',
    ),
    VariantCardSpec(
        'G2', 'green', 'GREEN // ANTIVIRUS', '$5',
        '{PIP1} +2{RESEARCH} {WARN} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Universal Sandbox', 'P3 INCOME',
        'Gain **+1 {RESEARCH}**, plus **+1 {RESEARCH}** per **{GREEN} cube** in the Exit Tray *(max +3)*.',
        'Sandbox: +1 Research, +1 per Green in tray (max +3).',
    ),
    VariantCardSpec(
        'G3', 'green', 'GREEN // ANTIVIRUS', '$4',
        '{PIP1} +2{RESEARCH} {WARN} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret {WARN} | {PIP6} {STAR}',
        'Live Reboot', 'P3 INCOME',
        'Gain **+1 {RESEARCH} & +$1**, and move **1 die** from your **Scanned Box** to your **Ready for Release Zone**.',
        'Live Reboot: +1 Research, +$1 & Scanned -> Ready.',
    ),
    VariantCardSpec(
        'Y1', 'yellow', 'YELLOW // COMM. AI', '$6',
        '{PIP1} +2 Share {WARN} {PIP2} +1 Share/1{RESEARCH}', '{PIP3} $1 & 1 Share | {PIP4}{PIP5} $2/1{RESEARCH} {WARN} | {PIP6} {STAR}',
        'Algorithmic Trading', 'P3 INCOME',
        'Gain **+$4**, **OR** pay **$2** to gain **+1 Corporate Secret**.',
        'Trading: +$4 OR pay $2 for +1 Secret.',
    ),
    VariantCardSpec(
        'Y2', 'yellow', 'YELLOW // COMM. AI', '$5',
        '{PIP1} +2 Share {WARN} {PIP2} +1 Share/1{RESEARCH}', '{PIP3} $1 & 1 Share | {PIP4}{PIP5} $2/1{RESEARCH} {WARN} | {PIP6} {STAR}',
        'Cloud Monopoly', 'P3 INCOME',
        'Gain **+$2**, plus **+$1** per different Central Market die color you own *(R/B/G/Y; excludes Purple; **max +$6**)*.',
        'Monopoly: +$2 plus +$1 per Market color (max +$6).',
    ),
    VariantCardSpec(
        'Y3', 'yellow', 'YELLOW // COMM. AI', '$5',
        '{PIP1} +2 Share {WARN} {PIP2} +1 Share/1{RESEARCH}', '{PIP3} $1 & 1 Share | {PIP4}{PIP5} $2/1{RESEARCH} {WARN} | {PIP6} {STAR}',
        'Proprietary Training', 'P3 INCOME',
        'Gain **+1 Corporate Secret**, plus **+$1** per **Gray Legacy** die you own.',
        'Training: +1 Secret plus +$1 per Gray die.',
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
        profile="SINGULARITY",
        banner_text="**Escalation:** Space 4 raises the lowest Vulnerability & adds cubes.\nSpace 6 = Singularity!",
        spaces=(
            VersionTrackSpaceSpec(1, "+1 {RED} 2 {BLUE} 1 {GREEN}"),
            VersionTrackSpaceSpec(2, "Most $ -$3\nMost {RESEARCH} -1{RESEARCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} 2 {BLUE}"),
            VersionTrackSpaceSpec(4, "Lowest Vulnerability\n+2 Vulnerability\n+1 {BLUE} 1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Most Colored\nreturns 1 die"),
            VersionTrackSpaceSpec(6, "**SINGULARITY!**", is_singularity=True),
        ),
    ),
    VersionTileSpec(
        version="v3.0",
        name="Corrupted Kernel",
        profile="SINGULARITY",
        banner_text="**Escalation:** Space 1 raises the lowest Vulnerability & adds cubes.\nSpace 4 leaks 1 Secret.",
        spaces=(
            VersionTrackSpaceSpec(1, "Lowest Vulnerability\n+2 Vulnerability\n+1 {RED} 2 {BLUE}"),
            VersionTrackSpaceSpec(2, "Most MS loses $3\n& 1 {RESEARCH} +1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} 1 {BLUE} 1 {GREEN}"),
            VersionTrackSpaceSpec(4, "Most Secrets\nloses 1 Secret\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Most Colored\nreturns 1 die"),
            VersionTrackSpaceSpec(6, "**SINGULARITY!**\nMost Secrets -1", is_singularity=True),
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="RaaS",
        profile="ESCALATION",
        banner_text="**Financial Extortion:** Space 3 drains cash & adds Red cube.\nSpace 5 upgrades to v3.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "Transfer: Least MS\ntakes $1 from Most MS"),
            VersionTrackSpaceSpec(2, "+1 {RED} +1 {BLUE}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Most $ loses $2\n& Add 1 {RED}"),
            VersionTrackSpaceSpec(4, "Most MS loses $3\n& 1 {RESEARCH} +1 {BLACK}"),
            VersionTrackSpaceSpec(5, "UPGRADE v3.0\n+1 {RED}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="Polymorphic Worm",
        profile="ESCALATION",
        banner_text="**Memory Infiltration:** Space 3 raises the lowest Vulnerability & adds Green cube.\nSpace 5 upgrades to v3.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "Transfer: Least {RESEARCH}\ntakes 1 {RESEARCH} from Most"),
            VersionTrackSpaceSpec(2, "+1 {BLUE} +1 {GREEN}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Lowest Vulnerability\n+2 Vulnerability & +1 {GREEN}"),
            VersionTrackSpaceSpec(4, "Most Secrets\nloses $3 +1 {BLACK}"),
            VersionTrackSpaceSpec(5, "UPGRADE v3.0\n+1 {RED}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Script Kiddie",
        profile="INITIAL",
        banner_text="**Setup Payload:** Add 2 {RED} 1 {BLUE} 1 {GREEN} to Staging Cup.\nSpace 4 upgrades to v2.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "+1 {RED}"),
            VersionTrackSpaceSpec(2, "Most $ loses $2\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Most {RESEARCH}\nloses 1 {RESEARCH}"),
            VersionTrackSpaceSpec(4, "UPGRADE v2.0\nMost MS loses 1 MS", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Data Scraper",
        profile="INITIAL",
        banner_text="**Setup Payload:** Add 1 {RED} 2 {BLUE} 1 {GREEN} to Staging Cup.\nAll players start with +1 Secret.",
        spaces=(
            VersionTrackSpaceSpec(1, "Most {RESEARCH}\nloses 1 {RESEARCH}"),
            VersionTrackSpaceSpec(2, "Most $ loses $2\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {GREEN}"),
            VersionTrackSpaceSpec(4, "UPGRADE v2.0\nLowest Vulnerability +2", is_milestone=True),
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

# -----------------------------------------------------------------------------
# Card & Dock Geometry (cards are printed at EXACTLY the mat dock size so the
# full card -- name, flavor text, abilities -- sits inside the dock outline).
# -----------------------------------------------------------------------------
CARD_W = 232.0          # 3.22"
COMPANY_CARD_H = 140.0  # 1.94"
WHITE_HAT_CARD_H = 146.0  # 2.03"

# Standard poker chip = 39 mm diameter (110.6 pt). Token wells are drawn at
# 40 mm (113.4 pt) so a chip (or short chip stack) drops in with clearance.
POKER_CHIP_WELL_D = 113.0


def _fit_paragraph(
    page: PDFPage, x: float, y: float, w: float, markup: str, bottom: float,
    size: float, leading: float, min_size: float = 4.5, color: Color = PALETTE["ink"],
    align: str = "left",
) -> None:
    """Render a rich paragraph, shrinking type until its last line sits above `bottom`."""
    s, ld = size, leading
    while s > min_size:
        probe = PDFPage()
        end_y = probe.rich_paragraph(x, y, w, markup, size=s, leading=ld)
        if end_y - ld <= bottom:
            break
        s = max(min_size, s - 0.2)
        ld = s * (leading / size)
    page.rich_paragraph(x, y, w, markup, size=s, leading=ld, color=color, align=align)


def _wrap_to_width(text: str, width: float, font: str, size: float) -> List[str]:
    """Greedy word-wrap of plain text into lines no wider than `width` (inline icon tokens count as 1 word)."""
    words = text.split(" ")
    lines: List[str] = []
    cur = ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if cur and measure_text(trial, font=font, size=size) > width:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def _draw_company_card(page: PDFPage, x: float, y: float, w: float, h: float, comp: CompanyCardSpec, is_dock: bool = False) -> None:
    """Render a Client Company card. Identical layout on the cut sheet and in the mat dock."""
    page.rect(x, y, w, h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)

    # Header strip
    page.rect(x, y, w, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(x + 5.0, y + 9.8, f"CLIENT COMPANY // COMP-{comp.code}", font="mono_bold", size=5.4, color=PALETTE["ink"])
    page.text(x + w - 5.0, y + 9.8, comp.sector.upper(), font="mono_bold", size=5.2, color=PALETTE["ink_soft"], align="right")

    # Name + flavor
    page.text(x + w / 2.0, y + 24.5, comp.name.upper(), font="bold", size=8.6, color=PALETTE["ink"], align="center")
    fy, fh = y + 28.0, 15.0
    page.rect(x + 4.0, fy, w - 8.0, fh, stroke=PALETTE["guide"], fill=PALETTE["paper_tint"], line_width=0.5)
    _fit_paragraph(page, x + 7.0, fy + 6.0, w - 14.0, f"*{comp.flavor}*", fy + fh - 2.0, size=5.0, leading=6.0, min_size=4.5, color=PALETTE["ink_soft"], align="center")

    # Starting Colored Die strip
    hw_y, hw_h = y + 45.0, 14.0
    die_col = comp.starting_die.lower()
    fg_col, bg_col = _color_pair(die_col)
    page.rect(x + 4.0, hw_y, w - 8.0, hw_h, stroke=fg_col, fill=bg_col, line_width=0.7)
    page.rich_line(x + w / 2.0, hw_y + 9.5, f"**STARTING COLORED DIE: {{{comp.starting_die}}} {comp.starting_die}**", size=5.8, color=fg_col, align="center")

    # Institutional Override box
    o_y = y + 62.0
    o_h = h - 65.0
    page.rect(x + 4.0, o_y, w - 8.0, o_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.7)
    page.rect(x + 4.0, o_y, w - 8.0, 12.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.5)
    tw = measure_text(comp.override_timing, font="mono_bold", size=4.7) + 4.0
    page.rounded_rect(x + w - 7.0 - tw, o_y + 1.8, tw, 8.6, r=1.5, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.5)
    page.text(x + w - 7.0 - tw / 2.0, o_y + 7.7, comp.override_timing, font="mono_bold", size=4.7, color=PALETTE["ink"], align="center")
    title = f"1x/VER: {comp.override_name.upper()}"
    avail = (w - 14.0) - tw - 6.0
    t_size = min(6.0, 6.0 * avail / max(1.0, measure_text(title, font="bold", size=6.0)))
    page.text(x + 7.0, o_y + 8.6, title, font="bold", size=t_size, color=PALETTE["ink"])

    ty = o_y + o_h - 15.0
    _fit_paragraph(page, x + 7.0, o_y + 21.5, w - 14.0, comp.override_desc, ty - 2.5, size=8.6, leading=10.8, min_size=5.0)

    # Once-per-version checkboxes
    page.line(x + 6.0, ty, x + w - 6.0, ty, stroke=PALETTE["rule"], width=0.5, dash=(2, 1.5))
    page.text(x + 7.0, ty + 9.5, "ONCE / VER:", font="mono_bold", size=4.8, color=PALETTE["ink_soft"])
    sx_start = x + 46.0
    sw_box = 34.0
    for s_idx, ver_lbl in enumerate(["v1.0", "v2.0", "v3.0"]):
        bx = sx_start + s_idx * (sw_box + 3.0)
        page.rounded_rect(bx, ty + 2.0, sw_box, 11.0, r=2.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.5)
        page.rect(bx + 2.0, ty + 3.8, 7.2, 7.2, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.5)
        page.text(bx + 11.5, ty + 9.6, ver_lbl, font="mono_bold", size=5.2, color=PALETTE["ink"])
    page.text(x + w - 7.0, ty + 9.5, "Unused forfeits on upgrade.", font="italic", size=4.8, color=PALETTE["muted"], align="right")


def _draw_white_hat_card(page: PDFPage, x: float, y: float, w: float, h: float, white_hat: WhiteHatDossierSpec, is_dock: bool = False) -> None:
    """Render a White Hat Dossier card. Identical layout on the cut sheet and in the mat dock."""
    page.rect(x, y, w, h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=1.0)

    # Header strip
    page.rect(x, y, w, 14.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.8)
    page.rect(x, y, w, 2.2, stroke=None, fill=PALETTE["purple"])
    page.draw_color_badge(x + 8.5, y + 8.2, 4.2, "purple")
    page.text(x + 16.0, y + 10.0, "WHITE HAT DOSSIER", font="bold", size=5.6, color=PALETTE["purple"])
    page.text(x + w - 5.0, y + 10.0, f"REF: WH-{white_hat.code}", font="mono_bold", size=5.0, color=PALETTE["purple"], align="right")

    # Name, role, flavor
    page.text(x + w / 2.0, y + 24.0, white_hat.name.upper(), font="bold", size=8.6, color=PALETTE["ink"], align="center")
    page.text(x + w / 2.0, y + 31.5, white_hat.role.upper(), font="mono_bold", size=4.9, color=PALETTE["purple"], align="center")
    fy, fh = y + 34.5, 15.0
    page.rect(x + 4.0, fy, w - 8.0, fh, stroke=PALETTE["guide"], fill=PALETTE["paper_tint"], line_width=0.5)
    _fit_paragraph(page, x + 7.0, fy + 6.0, w - 14.0, f"*{white_hat.flavor}*", fy + fh - 2.0, size=5.0, leading=6.0, min_size=4.5, color=PALETTE["ink_soft"], align="center")

    # Purple Star Signature Protocol box
    r_h = 32.0
    s_y = y + 52.0
    s_h = h - 52.0 - r_h - 5.0
    page.rect(x + 4.0, s_y, w - 8.0, s_h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.7)
    page.rect(x + 4.0, s_y, w - 8.0, 12.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.5)
    tw_s = measure_text(white_hat.protocol_timing, font="mono_bold", size=4.7) + 4.0
    page.rounded_rect(x + w - 7.0 - tw_s, s_y + 1.8, tw_s, 8.6, r=1.5, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.5)
    page.text(x + w - 7.0 - tw_s / 2.0, s_y + 7.7, white_hat.protocol_timing, font="mono_bold", size=4.7, color=PALETTE["purple"], align="center")
    title = f"PURPLE STAR: {white_hat.protocol_name.upper()}"
    avail = (w - 14.0) - tw_s - 6.0
    t_size = min(5.8, 5.8 * avail / max(1.0, measure_text(title, font="bold", size=5.8)))
    page.text(x + 7.0, s_y + 8.6, title, font="bold", size=t_size, color=PALETTE["purple"])
    note_y = s_y + s_h - 2.8
    _fit_paragraph(page, x + 7.0, s_y + 22.0, w - 14.0, white_hat.protocol_desc, note_y - 7.5, size=9.6, leading=11.6, min_size=5.0)
    repeat_note = (
        "*Repeatable: once per Purple {STAR} die (Phase 1 Step 3 Rerolls).*"
        if "P1" in white_hat.protocol_timing
        else "*Repeatable: once per Purple {STAR} die (Phase 3: die must still be In Production).*"
    )
    page.rich_line(x + w / 2.0, note_y, repeat_note, size=4.6, color=PALETTE["purple"], align="center")

    # Personal Reserve strip (the Purple Specialist Die rests on the card itself)
    r_y = y + h - r_h - 3.0
    page.rect(x + 4.0, r_y, w - 8.0, r_h, stroke=PALETTE["purple"], fill=PALETTE["paper_tint"], line_width=0.7)
    ds = r_h - 4.0
    page.rounded_rect(x + 6.0, r_y + 2.0, ds + 14.0, ds, r=2.5, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.6)
    page.text(x + 13.0 + ds / 2.0, r_y + 10.0, "RESERVE DIE", font="mono_bold", size=4.5, color=PALETTE["purple"], align="center")
    page.text(x + 13.0 + ds / 2.0, r_y + 18.0, "PUBLIC REL.", font="bold", size=5.0, color=PALETTE["ink"], align="center")
    page.text(x + 13.0 + ds / 2.0, r_y + 25.0, "TRACK L3", font="bold", size=5.0, color=PALETTE["ink"], align="center")
    page.rich_paragraph(
        x + ds + 26.0, r_y + 7.5, w - ds - 32.0,
        "**PERSONAL RESERVE** (2nd Purple die; not purchasable)\n"
        "1-2: +$1 / +1{RESEARCH} | 3: +$2 | 4: +$1 & +1{RESEARCH} {WARN}\n"
        "5: Secret face {WARN} (+1 Secret) | 6: {STAR} Signature Protocol",
        size=4.6, leading=6.6, color=PALETTE["ink_soft"],
    )


TRACK_STEP_COSTS = (None, 1, 2, 2, 3)  # {RESEARCH} to reach L1..L4 (RULES.md v0.47.0 baseline)


def _draw_track_cells(page: PDFPage, cells: Sequence[Tuple[float, float, float, float]],
                      levels: Sequence[Tuple[str, str]], accent: Color, compact: bool = False) -> None:
    """Draw a 5-level (L0-L4) track. levels[i] = (main value, effect text).

    L1 and L3 cells get a solid accent header (one-time reward on reaching that level).
    compact=True puts the level label in a left tab (for short, wide rows).
    """
    for lv, ((cx, cy, cw, ch), (main, effect)) in enumerate(zip(cells, levels)):
        once = lv in (1, 3) or (lv == 2 and "+1 {SECRET}" in effect)
        edge = accent if lv else PALETTE["rule"]
        page.rounded_rect(cx, cy, cw, ch, r=2.0, stroke=edge,
                          fill=PALETTE["purple_light"] if once else PALETTE["white"], line_width=0.65)
        if compact:
            tab_w = 24.0
            page.rect(cx, cy, tab_w, ch, stroke=edge, fill=accent if once else PALETTE["panel_tint"], line_width=0.5)
            lbl_col = PALETTE["white"] if once else PALETTE["ink"]
            if lv:
                page.rect(cx + 2.0, cy + 2.0, 5.5, 5.5, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.5)
            page.text(cx + tab_w / 2.0 + (2.5 if lv else 0.0), cy + 7.2, f"L{lv}", font="bold", size=5.2, color=lbl_col, align="center")
            if lv:
                page.rounded_rect(cx + 3.0, cy + ch - 9.5, tab_w - 6.0, 7.5, r=1.5, stroke=None, fill=PALETTE["white"])
                page.rich_line(cx + tab_w / 2.0, cy + ch - 3.8, f"**{TRACK_STEP_COSTS[lv]}{{RESEARCH}}**", size=4.8, color=PALETTE["ink"], align="center")
            bx = cx + tab_w + (cw - tab_w) / 2.0
            if effect:
                page.rich_line(bx, cy + ch / 2.0 - 1.0, f"**{main}**", size=5.4, color=PALETTE["ink"], align="center")
                page.rich_line(bx, cy + ch / 2.0 + 6.0, effect, size=4.7, color=PALETTE["purple"], align="center")
            else:
                page.rich_line(bx, cy + ch / 2.0 + 2.0, f"**{main}**", size=5.6, color=PALETTE["ink"], align="center")
            continue
        page.rect(cx, cy, cw, 9.0, stroke=edge, fill=accent if once else PALETTE["panel_tint"], line_width=0.5)
        hx = cx + 3.0
        if lv:
            page.rect(cx + 2.0, cy + 1.5, 6.0, 6.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.5)
            hx = cx + 10.0
            pill_w = 14.0
            page.rounded_rect(cx + cw - pill_w - 1.5, cy + 1.2, pill_w, 6.6, r=1.5, stroke=None, fill=PALETTE["white"])
            page.rich_line(cx + cw - 1.5 - pill_w / 2.0, cy + 6.6, f"**{TRACK_STEP_COSTS[lv]}{{RESEARCH}}**", size=4.8, color=PALETTE["ink"], align="center")
        page.text(hx, cy + 6.8, f"L{lv}", font="bold", size=5.2, color=PALETTE["white"] if once else PALETTE["ink"])
        body_top = cy + 11.0
        if lv == 1 and "+1 Gray" in effect:
            if ch > 40.0:
                if main:
                    page.rich_line(cx + cw / 2.0, cy + 16.5, f"**{main}**", size=5.4, color=PALETTE["ink"], align="center")
                die_sz = min(22.0, ch - 30.0)
                dx = cx + (cw - die_sz) / 2.0
                dy = cy + 20.0
                page.rounded_rect(dx, dy, die_sz, die_sz, r=2.5, stroke=accent, fill=PALETTE["white"], line_width=0.8, dash=(2.5, 1.5))
                page.text(cx + cw / 2.0, dy + die_sz / 2.0 + 1.8, "GRAY", font="mono_bold", size=5.0, color=accent, align="center")
                page.rich_line(cx + cw / 2.0, cy + ch - 3.0, "**+1 DIE -> READY**", size=4.4, color=accent, align="center")
            else:
                die_sz = 19.0
                dx = cx + cw - die_sz - 4.0
                dy = cy + 11.5
                page.rounded_rect(dx, dy, die_sz, die_sz, r=2.0, stroke=accent, fill=PALETTE["white"], line_width=0.75, dash=(2.0, 1.5))
                page.text(dx + die_sz / 2.0, dy + die_sz / 2.0 + 1.8, "GRAY", font="mono_bold", size=4.6, color=accent, align="center")
                if main:
                    page.rich_line(cx + (cw - die_sz) / 2.0 - 2.0, cy + 18.0, f"**{main}**", size=5.2, color=PALETTE["ink"], align="center")
                page.rich_line(cx + (cw - die_sz) / 2.0 - 2.0, cy + 28.0, "**+1 DIE**", size=4.6, color=accent, align="center")
        else:
            if main:
                page.rich_line(cx + cw / 2.0, cy + 17.5, f"**{main}**", size=5.6, color=PALETTE["ink"], align="center")
                body_top = cy + 20.0
            if effect:
                _fit_paragraph(page, cx + 2.5, body_top + 4.0, cw - 5.0, effect, cy + ch - 1.5,
                               size=4.6, leading=5.6, min_size=4.5, color=PALETTE["purple"] if once else PALETTE["ink_soft"], align="center")


def _cells_row(x: float, y: float, w: float, h: float, gap: float = 2.0) -> List[Tuple[float, float, float, float]]:
    cw = (w - 4 * gap) / 5.0
    return [(x + i * (cw + gap), y, cw, h) for i in range(5)]


def _cells_col(x: float, y: float, w: float, h: float, gap: float = 2.0) -> List[Tuple[float, float, float, float]]:
    ch = (h - 4 * gap) / 5.0
    return [(x, y + i * (ch + gap), w, ch) for i in range(5)]


PEN_TEST_LEVELS = [
    ("Limit 1", ""),
    ("Limit 1", "+1 Gray Legacy die -> Ready"),
    ("Limit 2", ""),
    ("Limit 2", "+1 {SECRET} Corporate Secret; Blue Secret +1"),
    ("Limit 3", "Free -1 Vulnerability at start of each Operations Turn"),
]
TRIAGE_LEVELS = [
    ("1 die", ""),
    ("1 die", "+1 Gray Legacy die -> Ready"),
    ("2 dice", ""),
    ("2 dice", "+1 {SECRET} Corporate Secret"),
    ("2 dice", "Replace 1 Gray -> Colored ($0, to Ready)"),
]
RELEASE_LEVELS = [
    ("4 dice", ""),
    ("4 dice", "+1 Gray Legacy die -> Ready"),
    ("5 dice", ""),
    ("5 dice", "+1 {SECRET} Corporate Secret"),
    ("6 dice", "Set 1 rolled Gray die to any face (P1 Step 3)"),
]
PR_REGAIN_COST_MONEY = 3  # $ Cash per +1 Market Share (RULES.md v0.47.0 baseline)
PUBLIC_RELATIONS_LEVELS = [
    ("Regain up to 1/turn", ""),
    ("Regain up to 1/turn", "+$3"),
    ("Regain up to 2/turn", ""),
    ("Regain up to 2/turn", "+2nd Purple die (to Scanned)"),
    ("Regain up to 3/turn", "+2 Market Share now"),
]

# Market Share track (RULES.md v0.47.0): start = 14 (2P) / 18 (3-4P); max = 20; 0 = Market Collapse;
# Market Leader Bonus by Market Share place (1st +3 Secrets; 2nd +1).
MARKET_SHARE_MAX = 20
MARKET_SHARE_START = {14: "2P START", 18: "3-4P START"}



def _draw_empty_company_card_slot(page: PDFPage, x: float, y: float, w: float, h: float, idx: int = 1) -> None:
    """Render a clean, uncluttered empty dock outline sized to a Client Company card."""
    page.rect(x, y, w, h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.0, dash=(4.0, 2.5))
    page.corner_ticks(x + 4.0, y + 4.0, w - 8.0, h - 8.0, size=7.0, color=PALETTE["ink_soft"])
    page.text(x + w / 2.0, y + h / 2.0 - 8.0, "CLIENT COMPANY CARD", font="bold", size=9.0, color=PALETTE["ink"], align="center")
    page.text(x + w / 2.0, y + h / 2.0 + 4.0, f"PLACE CARD HERE  ({w / 72.0:.2f}\" x {h / 72.0:.2f}\")", font="mono_bold", size=5.5, color=PALETTE["ink_soft"], align="center")
    page.text(x + w / 2.0, y + h / 2.0 + 16.0, "1 Institutional Override per Version (v1.0 / v2.0 / v3.0)", font="italic", size=5.5, color=PALETTE["muted"], align="center")


def _draw_empty_white_hat_slot(page: PDFPage, x: float, y: float, w: float, h: float, idx: int = 1) -> None:
    """Render a clean, uncluttered empty dock outline sized to a White Hat Dossier card."""
    page.rect(x, y, w, h, stroke=PALETTE["purple"], fill=PALETTE["paper_tint"], line_width=1.0, dash=(4.0, 2.5))
    page.corner_ticks(x + 4.0, y + 4.0, w - 8.0, h - 8.0, size=7.0, color=PALETTE["purple"])
    page.text(x + w / 2.0, y + h / 2.0 - 8.0, "WHITE HAT DOSSIER", font="bold", size=9.0, color=PALETTE["purple"], align="center")
    page.text(x + w / 2.0, y + h / 2.0 + 4.0, f"PLACE CARD HERE  ({w / 72.0:.2f}\" x {h / 72.0:.2f}\")", font="mono_bold", size=5.5, color=PALETTE["purple"], align="center")
    page.rich_line(x + w / 2.0, y + h / 2.0 + 16.0, "Personal Reserve (2nd Purple die)  |  Purple {STAR} Protocol", size=5.4, color=PALETTE["muted"], align="center")


def _draw_resource_holder(
    page: PDFPage,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    title_color: Color,
    border: Color,
    tint: Color,
    tag: str,
    icon_type: str,
    line1: str,
    line2: str,
    line3: str,
    line4: str = "",
) -> None:
    """A labelled holder box for Corporate Secrets, Liquid Cash, or Research tokens."""
    page.rect(x, y, w, h, stroke=border, fill=PALETTE["white"], line_width=1.0)
    page.rect(x, y, w, 14.0, stroke=border, fill=tint, line_width=0.7)
    page.rich_line(x + 6.0, y + 10.0, title, size=6.0, color=title_color)
    page.text(x + w - 6.0, y + 10.0, tag, font="mono_bold", size=5.0, color=title_color, align="right")

    # Left token staging well
    well_sz = 48.0
    wx = x + 6.0
    wy = y + 14.0 + (h - 14.0 - well_sz) / 2.0
    page.rounded_rect(wx, wy, well_sz, well_sz, r=4.0, stroke=border, fill=PALETTE["paper_tint"], line_width=0.8, dash=(3.0, 2.0))
    page.circle(wx + well_sz / 2.0, wy + well_sz / 2.0, well_sz / 2.0 - 4.0, stroke=PALETTE["guide"], fill=None, line_width=0.4)

    cx, cy = wx + well_sz / 2.0, wy + well_sz / 2.0
    if icon_type == "secret":
        page.draw_secret_icon(cx, cy, 20.0, color=title_color)
    elif icon_type == "research":
        page.draw_research_icon(cx, cy, 18.0, color=title_color)
    else:
        page.text(cx, cy + 6.0, "$", font="bold", size=22.0, color=PALETTE["ink"], align="center")

    # Right info lines
    tx = wx + well_sz + 8.0
    page.rich_line(tx, y + 27.5, line1, size=6.4, color=title_color)
    page.rich_line(tx, y + 41.0, line2, size=5.6, color=PALETTE["ink"])
    page.rich_line(tx, y + 53.5, line3, size=5.4, color=PALETTE["ink_soft"])
    if line4:
        page.rich_line(tx, y + 66.0, line4, size=5.1, color=PALETTE["muted"])


def _draw_public_relations_area(
    page: PDFPage,
    x: float,
    y: float,
    w: float,
    h: float,
) -> None:
    """Render the enlarged Public Relations Track & Personal Reserve (2nd Purple die placeholder)."""
    page.rect(x, y, w, h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=1.0)

    # Header strip
    page.rect(x, y, w, 20.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.8)
    page.rich_line(x + 8.0, y + 13.5, "{RESEARCH} **PUBLIC RELATIONS TRACK**", size=7.2, color=PALETTE["purple"])
    page.text(x + w - 8.0, y + 13.5, "PHASE 5 OPERATIONS", font="mono_bold", size=5.2, color=PALETTE["purple"], align="right")

    # Subhead banner
    banner_y = y + 23.0
    banner_h = 14.0
    page.rect(x + 4.0, banner_y, w - 8.0, banner_h, stroke=PALETTE["guide"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_line(
        x + w / 2.0, banner_y + 9.5,
        f"**${PR_REGAIN_COST_MONEY} Cash = +1 Market Share**  |  Regain limit per turn scales with track level",
        size=4.9, color=PALETTE["red"], align="center",
    )

    # 5 Track Levels (L0 to L4)
    row_y0 = y + 40.0
    rh = 46.0
    gap = 3.5
    rw = w - 8.0
    rx = x + 4.0

    for lv in range(5):
        ry = row_y0 + lv * (rh + gap)
        is_once = lv in (1, 3)
        edge = PALETTE["purple"] if is_once else PALETTE["rule"]
        fill_col = PALETTE["purple_light"] if is_once else PALETTE["white"]
        page.rounded_rect(rx, ry, rw, rh, r=2.5, stroke=edge, fill=fill_col, line_width=0.75 if is_once else 0.5)

        # Left level tab
        tab_w = 34.0
        page.rect(rx, ry, tab_w, rh, stroke=edge, fill=PALETTE["purple"] if is_once else PALETTE["panel_tint"], line_width=0.5)
        lbl_col = PALETTE["white"] if is_once else PALETTE["ink"]

        if lv > 0:
            page.rect(rx + 3.0, ry + 2.5, 6.0, 6.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.5)
            page.text(rx + tab_w / 2.0 + 3.0, ry + 8.5, f"L{lv}", font="bold", size=6.2, color=lbl_col, align="center")
            page.rounded_rect(rx + 3.0, ry + rh - 11.5, tab_w - 6.0, 8.5, r=1.5, stroke=None, fill=PALETTE["white"])
            page.rich_line(rx + tab_w / 2.0, ry + rh - 5.0, f"**{TRACK_STEP_COSTS[lv]}{{RESEARCH}}**", size=5.0, color=PALETTE["purple"] if is_once else PALETTE["ink"], align="center")
        else:
            page.text(rx + tab_w / 2.0, ry + 8.5, f"L{lv}", font="bold", size=6.2, color=lbl_col, align="center")
            page.text(rx + tab_w / 2.0, ry + rh - 5.0, "START", font="mono_bold", size=4.8, color=PALETTE["ink_soft"], align="center")

        bx = rx + tab_w + 6.0

        if lv == 0:
            page.rich_line(bx, ry + 26.5, "**Regain up to 1 Market Share / turn**", size=6.8, color=PALETTE["ink"])

        elif lv == 1:
            page.rich_line(bx, ry + 18.0, "**Regain up to 1 Market Share / turn**", size=6.6, color=PALETTE["ink"])
            page.rich_line(bx, ry + 33.0, "{STAR} **BREAKTHROUGH: +$3 LIQUID CASH**", size=6.2, color=PALETTE["purple"])

        elif lv == 2:
            page.rich_line(bx, ry + 26.5, "**Regain up to 2 Market Share / turn**", size=6.8, color=PALETTE["ink"])

        elif lv == 3:
            # Right side: dedicated outline space for 2nd Purple Specialist die
            die_sz = 36.0
            die_x = rx + rw - die_sz - 5.0
            die_y = ry + (rh - die_sz) / 2.0
            page.rounded_rect(die_x, die_y, die_sz, die_sz, r=3.0, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=1.0, dash=(3.0, 2.0))
            page.draw_color_badge(die_x + die_sz / 2.0, die_y + 9.5, 4.0, "purple")
            page.text(die_x + die_sz / 2.0, die_y + 21.0, "PURPLE", font="mono_bold", size=5.2, color=PALETTE["purple"], align="center")
            page.text(die_x + die_sz / 2.0, die_y + 30.0, "DIE 2", font="mono_bold", size=5.0, color=PALETTE["purple"], align="center")

            # Left of die box
            page.rich_line(bx, ry + 16.0, "**Regain up to 2 Market Share / turn**", size=6.4, color=PALETTE["ink"])
            page.rich_line(bx, ry + 28.5, "{STAR} **BREAKTHROUGH: 2ND PURPLE DIE**", size=6.0, color=PALETTE["purple"])
            page.text(bx, ry + 39.5, "Personal Reserve -> Scanned Box", font="italic", size=5.0, color=PALETTE["ink_soft"])

        elif lv == 4:
            page.rich_line(bx, ry + 18.0, "**Regain up to 3 Market Share / turn**", size=6.4, color=PALETTE["ink"])
            page.rich_line(bx, ry + 32.0, "{STAR} **+2 Market Share now**", size=6.2, color=PALETTE["purple"])

    # Bottom setup note
    page.rich_line(
        x + w / 2.0, y + h - 5.5,
        "*Setup: Place 2nd Purple die on L3 outline (unlocks at L3).*",
        size=5.0, color=PALETTE["muted"], align="center",
    )


def render_player_board(
    page: PDFPage,
    idx: int,
    comp: Optional[CompanyCardSpec] = None,
    white_hat: Optional[WhiteHatDossierSpec] = None,
) -> None:
    draw_board_outer_frame(
        page,
        left_tag=f"TOO MANY SECRETS // COMPANY TERMINAL MAT [TERM-0{idx}/4] // CI/CD PIPELINE & PEN TEST",
        right_tag="PNP PROTOTYPE v0.47.0 // US LETTER",
    )

    # -------------------------------------------------------------------------
    # LEFT COLUMN: CORPORATE HQ (x = 32..264, w = 232)
    # Stacks Corporate Secrets, Liquid Cash, Research Tokens, and Public Relations
    # vertically. (Client Company & White Hat cards sit alongside the mat).
    # -------------------------------------------------------------------------
    lx, lw = 32.0, CARD_W

    # 1. Corporate Secrets Holder (y = 30..106, h = 76)
    _draw_resource_holder(
        page, lx, 30.0, lw, 76.0,
        title="{SECRET} **CORPORATE SECRETS**",
        title_color=PALETTE["blue"],
        border=PALETTE["blue"],
        tint=PALETTE["blue_light"],
        tag="1 SECRET = 1 VP",
        icon_type="secret",
        line1="Start: **5** Secrets (+1 if Data Scraper)",
        line2="Most Secrets wins (1 Secret = 1 VP)",
        line3="<= 0 Secrets = **TOTAL DATA BREACH**",
        line4="",
    )

    # 2. Liquid Cash ($) Holder (y = 110..186, h = 76)
    _draw_resource_holder(
        page, lx, 110.0, lw, 76.0,
        title="**LIQUID CASH ($)**",
        title_color=PALETTE["ink"],
        border=PALETTE["ink"],
        tint=PALETTE["panel_tint"],
        tag="UNCAPPED",
        icon_type="money",
        line1="Start: **$6**",
        line2="P5: Buy 1 die ($4-$6) -> Scanned",
        line3="P5: Regain Market Share ($3 each)",
        line4="Tiebreaker #2",
    )

    # 3. Research Tokens (🔬) Holder (y = 190..266, h = 76)
    _draw_resource_holder(
        page, lx, 190.0, lw, 76.0,
        title="{RESEARCH} **RESEARCH TOKENS ({RESEARCH})**",
        title_color=PALETTE["purple"],
        border=PALETTE["purple"],
        tint=PALETTE["purple_light"],
        tag="UNCAPPED",
        icon_type="research",
        line1="Start: **0 {RESEARCH}**",
        line2="P5: Track Upgrades (1/2/2/3 {RESEARCH})",
        line3="Max 2 upgrades per turn",
        line4="Tiebreaker #4",
    )

    # 4. Expanded Public Relations Track & Personal Reserve (y = 272..576, h = 304)
    _draw_public_relations_area(page, lx, 272.0, lw, 304.0)

    # -------------------------------------------------------------------------
    # MAIN COLUMN: CI/CD PIPELINE & PEN TEST (x = 268..756, w = 488)
    # Clockwise CI/CD Pipeline Flow:
    # Ready (top) -> In Production (mid) -> Processing Box FIFO queue (bot-right)
    # -> Conveyor Triage (bot-mid) -> Scanned (bot-left) -> Release Bandwidth column (left) -> Ready (top)
    # -------------------------------------------------------------------------
    rx, rw = 268.0, 488.0

    # =========================================================================
    # 1. READY FOR RELEASE (Top Box: x = 268..756, y = 30..112, h = 82)
    # =========================================================================
    r1_y, r1_h = 30.0, 82.0
    page.rect(rx, r1_y, rw, r1_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, r1_y, rw, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(rx + 8.0, r1_y + 11.2, "ZONE 1: READY FOR RELEASE  (ROLLING POOL)", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_line(rx + rw - 8.0, r1_y + 11.2, "Start: **2 Gray + 1 Company die + 1 Purple**", size=5.6, color=PALETTE["ink_soft"], align="right")

    # Clean die staging boxes for physical dice
    die_sz = 36.0
    die_gap = 8.0
    num_slots = 10
    total_dw = num_slots * die_sz + (num_slots - 1) * die_gap
    dx0 = rx + (rw - total_dw) / 2.0
    dy0 = r1_y + 23.0
    for di in range(num_slots):
        dsx = dx0 + di * (die_sz + die_gap)
        is_starter = di < 4
        page.rounded_rect(
            dsx, dy0, die_sz, die_sz, r=3.0,
            stroke=PALETTE["ink_soft"] if is_starter else PALETTE["rule"],
            fill=PALETTE["paper_tint"] if is_starter else PALETTE["white"],
            line_width=0.7 if is_starter else 0.5,
            dash=(3.0, 2.0) if not is_starter else None,
        )
        if is_starter:
            st_lbl = ("GRAY", "GRAY", "COMP", "PURP")[di]
            page.text(dsx + die_sz / 2.0, dy0 + die_sz / 2.0 + 2.0, st_lbl, font="mono_bold", size=5.2, color=PALETTE["muted"], align="center")

    page.text(rx + 8.0, r1_y + 72.0, "^ GRADUATES FROM SCANNED (P6)  |  BREAKTHROUGHS ENTER HERE", font="mono_bold", size=5.4, color=PALETTE["blue"])
    page.text(rx + rw - 8.0, r1_y + 72.0, "ROLL IN PHASE 1  v", font="mono_bold", size=5.4, color=PALETTE["ink_soft"], align="right")

    # =========================================================================
    # 2. VERTICAL RELEASE TRACK & RELEASE BANDWIDTH COLUMN (Left Column: x = 268..342, y = 118..402, h = 284)
    # =========================================================================
    vx, vw = 268.0, 74.0
    vy, vh = 118.0, 284.0
    page.rect(vx, vy, vw, vh, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=1.0)

    # Header strip
    page.rect(vx, vy, vw, 24.0, stroke=PALETTE["blue"], fill=PALETTE["blue"], line_width=0.7)
    rb_label = "^ RELEASE TRACK ^"
    rb_size = min(5.8, 5.8 * (vw - 6.0) / max(1.0, measure_text(rb_label, font="bold", size=5.8)))
    page.text(vx + vw / 2.0, vy + 9.5, rb_label, font="bold", size=rb_size, color=PALETTE["white"], align="center")
    page.text(vx + vw / 2.0, vy + 19.0, "SCANNED -> READY", font="mono_bold", size=4.8, color=PALETTE["white"], align="center")

    # 5-level Release Track stacked vertically along the column (L1 has Gray die outline)
    _draw_track_cells(page, _cells_col(vx + 3.0, vy + 28.0, vw - 6.0, vh - 32.0, gap=3.5), RELEASE_LEVELS, PALETTE["blue"])

    # =========================================================================
    # 3. ZONE 2: IN PRODUCTION (Middle-Right Box: x = 346..756, y = 118..402, h = 284)
    # =========================================================================
    px, pw = 346.0, 410.0
    py, ph = 118.0, 284.0
    page.rect(px, py, pw, ph, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(px, py, pw, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(px + 8.0, py + 11.2, "**ZONE 2: IN PRODUCTION  (DEPLOYED DICE)**", size=7.8, color=PALETTE["ink"])
    page.text(px + pw - 8.0, py + 11.2, "P6: MOVES TO SCANNED BOX", font="mono_bold", size=5.8, color=PALETTE["ink_soft"], align="right")

    # --- 3A: Deployed Dice area (one open space for assigned dice) (h = 114) ---
    page.rect(px + 6.0, py + 21.0, pw - 12.0, 114.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
    page.rect(px + 6.0, py + 21.0, pw - 12.0, 14.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_line(px + 10.0, py + 30.5, "**DEPLOYED DICE**", size=6.8, color=PALETTE["ink"])
    page.rich_line(px + pw - 14.0, py + 30.5, "{WARN} **KEPT IN P1 = +1 VULNERABILITY**   |   RESOLVES IN P3", size=5.2, color=PALETTE["ink_soft"], align="right")
    page.rounded_rect(px + 9.0, py + 39.0, pw - 18.0, 91.0, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6)

    # --- 3B: Pen Test Track (Bottom of In Production, h = 137) ---
    st_y = py + 141.0
    st_h = 137.0
    page.rect(px + 6.0, st_y, pw - 12.0, st_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.85)
    page.rect(px + 6.0, st_y, pw - 12.0, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(px + 10.0, st_y + 10.0, "{RESEARCH} **PEN TEST TRACK**  (LOWERS VULNERABILITY)", size=6.8, color=PALETTE["ink"])
    page.text(px + pw - 14.0, st_y + 10.0, "UPGRADE IN PHASE 5", font="mono_bold", size=5.2, color=PALETTE["purple"], align="right")
    page.rich_line(px + pw / 2.0, st_y + 29.0, "{WARN} **PHASE 5:  2 {RESEARCH} = -1 VULNERABILITY**  (UP TO YOUR LIMIT EACH TURN)", size=7.4, color=PALETTE["ink"], align="center")

    # 5-level Pen Test Track (L1 has Gray die outline)
    _draw_track_cells(page, _cells_row(px + 9.0, st_y + 36.0, pw - 18.0, st_h - 41.0, gap=3.0), PEN_TEST_LEVELS, PALETTE["ink"])

    # =========================================================================
    # 4. ZONE 3: UNDER DEVELOPMENT (Bottom Box: x = 268..756, y = 408..580, h = 172)
    # Conveyor Triage: Processing Box FIFO Queue -> Scanned Box -> Ready for Release
    # =========================================================================
    uy, uh = 408.0, 172.0
    page.rect(rx, uy, rw, uh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, uy, rw, 15.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(rx + 8.0, uy + 10.5, "**ZONE 3: UNDER DEVELOPMENT  (CI/CD PIPELINE)**", size=7.5, color=PALETTE["ink"])
    page.text(rx + rw - 8.0, uy + 10.5, "OFFLINE MODULES (DO NOT ROLL)", font="mono_bold", size=5.8, color=PALETTE["muted"], align="right")

    # --- 4A: Scanned Box (Bottom Left: x = 272..390, w = 118, y = 427..576, h = 149) ---
    # Unbounded staging area (no misleading dice outlines)
    sc_x, sc_w = rx + 4.0, 118.0
    sc_y, sc_h = uy + 19.0, uh - 23.0
    page.rect(sc_x, sc_y, sc_w, sc_h, stroke=PALETTE["blue"], fill=PALETTE["white"], line_width=0.9)
    page.rect(sc_x, sc_y, sc_w, 14.0, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=0.6)
    page.rich_line(sc_x + 6.0, sc_y + 10.0, "{BLUE} **SCANNED BOX**", size=6.8, color=PALETTE["blue"])
    page.text(sc_x + sc_w - 6.0, sc_y + 10.0, "P6 STEP 2-3", font="mono_bold", size=4.6, color=PALETTE["blue"], align="right")

    # Open staging well
    page.rounded_rect(sc_x + 4.0, sc_y + 18.0, sc_w - 8.0, sc_h - 22.0, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 38.0, "^ **GRADUATES TO READY** ^", size=6.2, color=PALETTE["blue"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 52.0, "Up to Release Bandwidth (**4/5/6**)", size=5.6, color=PALETTE["ink"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 72.0, "Market Buys  ·  P6 Return", size=5.4, color=PALETTE["ink_soft"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 85.0, "Triage Exits Arrive Here", size=5.4, color=PALETTE["ink_soft"], align="center")

    # --- 4B: Embedded Triage Upgrade Track (Top Right: x = 394..752, w = 358, y = 427..480, h = 53) ---
    tt_x, tt_w = rx + 126.0, rw - 130.0
    tt_y, tt_h = uy + 19.0, 53.0
    page.rect(tt_x, tt_y, tt_w, tt_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.85)
    page.rect(tt_x, tt_y, tt_w, 13.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(tt_x + 6.0, tt_y + 9.5, "{RESEARCH} **TRIAGE TRACK**  (CONVEYOR BANDWIDTH — P6 STEP 4)", size=6.2, color=PALETTE["ink"])
    page.text(tt_x + tt_w - 6.0, tt_y + 9.5, "UPGRADE IN PHASE 5", font="mono_bold", size=4.8, color=PALETTE["purple"], align="right")

    _draw_track_cells(page, _cells_row(tt_x + 3.0, tt_y + 15.0, tt_w - 6.0, tt_h - 17.0, gap=2.5), TRIAGE_LEVELS, PALETTE["purple"])

    # --- 4C: Processing Box (Bottom Right: x = 394..752, w = 358, y = 484..576, h = 92) ---
    # Elongated FIFO Queue with dedicated Operative Signature Cube cradle
    gl_x, gl_w = rx + 126.0, rw - 130.0
    gl_y, gl_h = uy + 76.0, 92.0
    page.rect(gl_x, gl_y, gl_w, gl_h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.9)
    page.rect(gl_x, gl_y, gl_w, 13.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.6)
    page.rich_line(gl_x + 6.0, gl_y + 9.5, "{SECRET} **PROCESSING BOX  (FIRST IN, FIRST OUT PIPELINE)**", size=6.2, color=PALETTE["purple"])
    page.text(gl_x + gl_w - 6.0, gl_y + 9.5, "P1 STEP 4: SECRET FACES ENTER", font="mono_bold", size=4.8, color=PALETTE["purple"], align="right")

    # Layout: Dedicated Signature Cube cradle (left, adjacent to Scanned) + FIFO Conveyor Lane (right)
    cube_spot_w = 48.0
    lane_w = gl_w - cube_spot_w - 12.0
    lane_y = gl_y + 15.5
    lane_h = 59.0

    # Dedicated Operative Signature Cube cradle (Left side, immediately next to Scanned Box boundary)
    cube_x = gl_x + 4.0
    page.rounded_rect(cube_x, lane_y, cube_spot_w, lane_h, r=2.5, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.8, dash=(2.5, 1.5))
    page.rect(cube_x + cube_spot_w / 2.0 - 5.0, lane_y + 2.5, 10.0, 10.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.6)
    page.text(cube_x + cube_spot_w / 2.0, lane_y + 9.5, "CUBE", font="mono_bold", size=4.2, color=PALETTE["purple"], align="center")
    page.text(cube_x + cube_spot_w / 2.0, lane_y + 17.5, "SIGNATURE CUBE", font="mono_bold", size=4.4, color=PALETTE["purple"], align="center")
    page.text(cube_x + cube_spot_w / 2.0, lane_y + 21.5, "(TOWER RELAY)", font="italic", size=3.8, color=PALETTE["muted"], align="center")

    # FIFO conveyor lane (Right side, flowing right to left into Scanned Box)
    lane_x = cube_x + cube_spot_w + 4.0
    page.rounded_rect(lane_x, lane_y, lane_w, lane_h, r=2.5, stroke=PALETTE["purple_light"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.rich_line(lane_x + 6.0, lane_y + 7.5, "<-- **[EXIT: TO SCANNED]**", size=5.0, color=PALETTE["purple"])
    page.rich_line(lane_x + lane_w / 2.0 + 8.0, lane_y + 7.5, "<===  **FIFO CONVEYOR FLOW**  <===", size=4.6, color=PALETTE["purple"], align="center")
    page.rich_line(lane_x + lane_w - 6.0, lane_y + 7.5, "**[ENTRY]** <---", size=5.0, color=PALETTE["purple"], align="right")
    page.text(lane_x + lane_w / 2.0, lane_y + lane_h - 4.0, "Dice line up in entry order; in Phase 6, up to Triage Bandwidth oldest dice move first", font="italic", size=4.3, color=PALETTE["muted"], align="center")

    # Bank on Exit Yield Key banner below lane
    page.rich_line(
        gl_x + gl_w / 2.0, gl_y + gl_h - 5.0,
        "**Bank on Exit (P6 Step 4):**  {PURPLE} **+1**  |  {RED} **+2** *(MLB)*  |  {BLUE} **+2** *(+1 if Pen Test L3+)*  |  {GREEN} **+2**, then **-2 Vuln.**  |  *Moves Signature Cube -> Staging Cup*",
        size=4.7, color=PALETTE["ink_soft"], align="center",
    )


def render_company_cards_page(page: PDFPage) -> None:
    """Render all 6 Client Company Cards on a single US Letter print-and-cut sheet."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // 6x CLIENT COMPANY CARDS [PAGE 5/6]",
        right_tag="PNP PROTOTYPE v0.47.0 // US LETTER",
    )

    page.text(
        396.0, 35.0,
        "6x CLIENT COMPANY CARDS -- CUT ALONG TICKS -- DEALT AT SETUP TO SIT ALONGSIDE TERMINAL MAT (3.22\" x 1.94\")",
        font="mono_bold", size=6.8, color=PALETTE["ink_soft"], align="center",
    )

    cw = CARD_W
    ch = COMPANY_CARD_H
    gap_x = 12.0
    gap_y = 14.0
    x0 = (792.0 - (3 * cw + 2 * gap_x)) / 2.0
    y0 = 60.0

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
        "**1. Once-per-Version Lifecycle:** Activate once per SETEC Version (**v1.0**, **v2.0**, **v3.0**); mark the checkbox when used. *(DTO Slush Fund: once per game.)*\n"
        "**2. Version Transition Timing:** If SETEC's Corruption Track fills in Phase 2, excess {BLACK} cubes **spill over** immediately, but the old version stays active through Phases 3-6.\n"
        "**3. Round-Start Switch:** At the start of the next round (Phase 1 Step 1), unspent old-version overrides **forfeit** and the new version's override unlocks."
    )
    page.rich_paragraph(rx + 10.0, ry + 27.0, rw - 20.0, rules_text, size=7.2, leading=11.0, color=PALETTE["ink"])


def render_white_hat_dossiers_page(page: PDFPage) -> None:
    """Render all 6 White Hat Dossier Cards on a single US Letter print-and-cut sheet."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // 6x WHITE HAT DOSSIER CARDS [PAGE 6/6]",
        right_tag="PNP PROTOTYPE v0.47.0 // US LETTER",
    )

    page.text(
        396.0, 35.0,
        "6x WHITE HAT DOSSIER CARDS -- CUT ALONG TICKS -- DEALT AT SETUP TO SIT ALONGSIDE TERMINAL MAT (3.22\" x 2.03\")",
        font="mono_bold", size=6.8, color=PALETTE["purple"], align="center",
    )

    cw = CARD_W
    ch = WHITE_HAT_CARD_H
    gap_x = 12.0
    gap_y = 14.0
    x0 = (792.0 - (3 * cw + 2 * gap_x)) / 2.0
    y0 = 60.0

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
        "**1. Personal Reserve:** Your 2nd Purple Specialist Die sits on Public Relations Track L3 and moves to your **Scanned Box** at **Level 3** (not purchasable; not replaced if lost).\n"
        "**2. Faces 1-5:** **1-2:** +$1 / +1 {RESEARCH}  |  **3:** +$2  |  **4:** +$1 & +1 {RESEARCH} {WARN}  |  **5:** Secret face {WARN} (+1 Secret on exit).\n"
        "**3. Face 6 Signature Protocol:** Repeatable per Purple {STAR} die rolled (Phase 3 protocols require the die to still be In Production; Prodigy fires in Phase 1 Step 4)."
    )
    page.rich_paragraph(rx + 10.0, ry + 27.0, rw - 20.0, wh_rules_text, size=7.2, leading=11.0, color=PALETTE["ink"])


# =============================================================================
# 2A. Central SETEC Agent Board (Matches Wireframe Page 2)
# =============================================================================

def render_agent_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // CENTRAL ROGUE AGENT & MARKET SHARE BOARD [1/2]",
        right_tag="PNP PROTOTYPE v0.47.0 // US LETTER",
    )

    # Top Title Bar inside board
    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "PROJECT: SETEC  //  AUTONOMOUS MAINFRAME COMPILER & MARKET SHARE", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "VERSION TILES ON LEFT  |  CENTRAL MARKET SHARE TRACK ON RIGHT", font="mono", size=7.0, color=PALETTE["rule"], align="right")

    # -------------------------------------------------------------------------
    # VULNERABILITY TRACK STRIP (full width, y = 62..136): 0-15, safe zone 0-3,
    # bands 4-6 / 7-9 / 10-15 printed with Green damage. One marker per player.
    # -------------------------------------------------------------------------
    vt_y, vt_h = 62.0, 74.0
    page.rect(40.0, vt_y, 712.0, vt_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    lab_w = 112.0
    page.rect(40.0, vt_y, lab_w, vt_h, stroke=PALETTE["ink"], fill=PALETTE["yellow_light"], line_width=1.1)
    page.draw_warn_icon(58.0, vt_y + 20.0, 20.0)
    page.text(40.0 + lab_w / 2.0 + 8.0, vt_y + 18.0, "VULNERABILITY", font="bold", size=8.6, color=PALETTE["ink"], align="center")
    page.text(40.0 + lab_w / 2.0 + 8.0, vt_y + 29.0, "TRACK  0-15", font="bold", size=8.6, color=PALETTE["ink"], align="center")
    page.text(40.0 + lab_w / 2.0, vt_y + 47.0, "1 marker per player", font="italic", size=6.4, color=PALETTE["ink_soft"], align="center")
    page.text(40.0 + lab_w / 2.0, vt_y + 58.0, "all start on 0", font="italic", size=6.4, color=PALETTE["ink_soft"], align="center")
    v_gap = 2.0
    v_x0 = 40.0 + lab_w + 6.0
    v_cw = (752.0 - 6.0 - v_x0 - 15 * v_gap) / 16.0
    bands = [
        (0, 3, "SAFE ZONE (NEVER HIT)", PALETTE["green_light"], PALETTE["green"], PALETTE["green"], PALETTE["white"]),
        (4, 6, "-1 SECRET", PALETTE["yellow_light"], PALETTE["yellow"], PALETTE["yellow"], PALETTE["white"]),
        (7, 9, "-2 SECRETS", PALETTE["red_light"], PALETTE["red"], PALETTE["red"], PALETTE["white"]),
        (10, 15, "-3 SECRETS", PALETTE["red"], PALETTE["red"], PALETTE["red"], PALETTE["white"]),
    ]
    for lo, hi, btxt, cell_fill, edge, hdr_fill, hdr_txt in bands:
        bx0 = v_x0 + lo * (v_cw + v_gap)
        bx1 = v_x0 + hi * (v_cw + v_gap) + v_cw
        page.rect(bx0, vt_y + 5.0, bx1 - bx0, 14.0, stroke=edge, fill=hdr_fill, line_width=0.7)
        page.text((bx0 + bx1) / 2.0, vt_y + 15.0, btxt, font="bold", size=7.0, color=hdr_txt, align="center")
        for v in range(lo, hi + 1):
            vx_c = v_x0 + v * (v_cw + v_gap)
            page.rounded_rect(vx_c, vt_y + 21.0, v_cw, 30.0, r=2.0, stroke=edge, fill=cell_fill, line_width=0.9)
            page.text(vx_c + v_cw / 2.0, vt_y + 42.0, str(v), font="bold", size=15.0, color=PALETTE["white"] if cell_fill == PALETTE["red"] else PALETTE["ink"], align="center")
    page.rich_line(
        v_x0 + (752.0 - 6.0 - v_x0) / 2.0, vt_y + 62.0,
        "**Each {GREEN} cube hits the highest at 4+ (all ties):** they lose the band's Secrets and **reset to 0**. The next cube re-checks.  {WARN} kept in P1 = **+1**.",
        size=6.9, color=PALETTE["ink"], align="center",
    )
    page.rich_line(
        v_x0 + (752.0 - 6.0 - v_x0) / 2.0, vt_y + 71.0,
        "**The Staging Cup's contents are public.**  Pen Test (P5): 2 {RESEARCH} = -1.",
        size=6.4, color=PALETTE["ink_soft"], align="center",
    )

    col_top = 144.0
    col_bot = 578.0
    col_h = col_bot - col_top  # 434 pt

    # -------------------------------------------------------------------------
    # COLUMN 1 (Left): v3.0 / v2.0 / v1.0 Slots + Corruption Track
    # -------------------------------------------------------------------------
    slot_x = 78.0
    slot_w = 220.0  # 3.056" (printable tiles are 212 x 112 pt = 2.94" x 1.56")
    slot_h = 128.0  # 1.78"
    slot_gap = (col_h - 3 * slot_h) / 2.0  # 54.5 pt

    tiers = [
        ("v3.0", "SINGULARITY TIER", "Deal 1 face-up v3.0 Tile here", "Corruption Track fills = SINGULARITY!"),
        ("v2.0", "ESCALATION TIER", "Deal 1 face-up v2.0 Tile here", "On Upgrade: Add Payload -> Staging Cup"),
        ("v1.0", "INITIAL TIER (START)", "Deal 1 face-up v1.0 Tile here", "Setup: Add Start Payload -> Staging Cup"),
    ]

    for idx, (ver_str, tier_sub, hint1, hint2) in enumerate(tiers):
        sy = col_top + idx * (slot_h + slot_gap)
        by_mid = sy + (slot_h - 36.0) / 2.0
        page.rounded_rect(38.0, by_mid, 34.0, 36.0, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"] if idx < 2 else PALETTE["ink"], line_width=1.0)
        v_col = PALETTE["ink"] if idx < 2 else PALETTE["white"]
        page.text(55.0, by_mid + 18.0, ver_str, font="bold", size=10.5, color=v_col, align="center")
        page.text(55.0, by_mid + 29.0, "START" if idx == 2 else f"TIER {3 - idx}", font="mono", size=5.5, color=PALETTE["rule"] if idx == 2 else PALETTE["muted"], align="center")

        if idx < 2:
            ay_mid = sy + slot_h + slot_gap / 2.0
            next_by = (sy + slot_h + slot_gap) + (slot_h - 36.0) / 2.0
            page.line(55.0, by_mid + 38.0, 55.0, next_by - 4.0, stroke=PALETTE["muted"], width=0.9, dash=(2, 2))
            gx_mid = slot_x + slot_w / 2.0
            page.text(gx_mid, ay_mid + 3.0, "^  UPGRADE WHEN TRACK FILLS  ^", font="mono_bold", size=6.5, color=PALETTE["muted"], align="center")

        page.rect(slot_x, sy, slot_w, slot_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.1)
        page.rect(slot_x + 4.0, sy + 4.0, slot_w - 8.0, slot_h - 8.0, stroke=PALETTE["muted"], fill=PALETTE["white"], line_width=0.6, dash=(4, 3))
        page.corner_ticks(slot_x + 4.0, sy + 4.0, slot_w - 8.0, slot_h - 8.0, size=6.0, color=PALETTE["ink_soft"])
        page.text(slot_x + slot_w / 2.0, sy + 48.0, f"{ver_str}  //  {tier_sub}", font="mono_bold", size=8.5, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 66.0, hint1, font="italic", size=8.0, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 82.0, hint2, font="regular", size=7.0, color=PALETTE["muted"], align="center")

    # -------------------------------------------------------------------------
    # COLUMN 2 (Middle): Agent Cube Effect & Target Lock Summary (x = 308, w = 196)
    # Printed in exact top-to-bottom tie-breaking priority order: Green > Black > Blue > Red
    # -------------------------------------------------------------------------
    m_x, m_w = 308.0, 196.0
    page.rect(m_x, col_top, m_w, col_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    page.rect(m_x, col_top, m_w, 22.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.9)
    page.text(m_x + m_w / 2.0, col_top + 15.0, "CUBES & TARGET LOCK SUMMARY", font="bold", size=8.6, color=PALETTE["ink"], align="center")

    # Top overview & Target Lock tie-breaking banner
    page.rect(m_x + 7.0, col_top + 26.0, m_w - 14.0, 38.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6)
    _fit_paragraph(
        page, m_x + 11.0, col_top + 35.5, m_w - 22.0,
        "**P2:** Drop Staging Cup. {BLACK} resolves now; {RED}{BLUE}{GREEN} attack in **P4**, then recycle.\n"
        "**Target Lock (Signature Exits):** After P4 damage, resolve top tray color (**Tie Priority: {GREEN} > {BLACK} > {BLUE} > {RED}**; 0 cubes = fizzle).",
        col_top + 63.0, size=6.8, leading=8.4, min_size=5.4, color=PALETTE["ink"],
    )

    cube_cards = [
        (
            "green",
            "{GREEN} GREEN // MALWARE",
            "1ST TIE",
            "**P4:** One cube at a time hits the highest **Vulnerability 4+** (ties all): **-1 / -2 / -3** Secrets by band, then **reset to 0**.",
            "**Target Lock:** Place 1 green cube on next space of **2 Research Tracks** w/o green (**2x {RESEARCH}** to advance); unplaceable: **+2 Vulnerability** each.",
            87.0,
        ),
        (
            "black",
            "{BLACK} BLACK // CORRUPTION",
            "2ND TIE",
            "**P2 Immediate:** Advance active **Corruption Track** 1/cube (**4/5/6** spaces; **v3.0 full = SINGULARITY!**).",
            "**Target Lock:** Mark **Institutional Override** `Used` for this Version *(if already used, lose **2 Corporate Secrets**)*.",
            87.0,
        ),
        (
            "blue",
            "{BLUE} BLUE // SPYWARE",
            "3RD TIE",
            "**P4:** **-1 Corporate Secret** per {BLUE}. **<= 0 = Patient Zero!**",
            "**Target Lock:** Move **1 Gray Legacy Die** (`Scanned` -> `Prod`) to back of **Processing Box** (**0** Secrets).",
            87.0,
        ),
        (
            "red",
            "{RED} RED // MARKET MANIP.",
            "4TH TIE",
            "**P4:** **-1 Market Share** per {RED} *(min 0)*. **0 after P4 = Market Collapse**.",
            "**Target Lock:** **-2 Market Share**; lowest rival gains **+2** *(2P: SETEC Corp counts)*.",
            87.0,
        ),
    ]

    cy_box = col_top + 68.0
    card_gap = 5.0
    for ckey, ctitle, ctag, cbody_base, cbody_sig, bh_card in cube_cards:
        fg, bg = _color_pair(ckey)
        page.rounded_rect(m_x + 7.0, cy_box, m_w - 14.0, bh_card, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
        page.rect(m_x + 7.0, cy_box, m_w - 14.0, 18.0, stroke=PALETTE["ink"], fill=bg, line_width=0.6)
        page.rich_line(m_x + 11.0, cy_box + 12.4, f"**{ctitle}**", size=7.8, color=fg if ckey != "black" else PALETTE["ink"])
        page.rich_line(m_x + m_w - 11.0, cy_box + 12.2, ctag, size=6.4, base_font="mono_bold", color=PALETTE["ink_soft"], align="right")
        _fit_paragraph(page, m_x + 11.0, cy_box + 27.5, m_w - 22.0, cbody_base, cy_box + 47.5, size=7.8, leading=9.4, min_size=5.4, color=PALETTE["ink"])
        # Target Lock Signature Attack sub-box
        sig_y = cy_box + 49.0
        sig_h = bh_card - 52.0
        page.rounded_rect(m_x + 10.0, sig_y, m_w - 20.0, sig_h, r=2.0, stroke=fg if ckey != "black" else PALETTE["ink_soft"], fill=PALETTE["paper_tint"], line_width=0.55)
        _fit_paragraph(page, m_x + 13.0, sig_y + 11.5, m_w - 26.0, cbody_sig, sig_y + sig_h - 3.0, size=7.6, leading=9.4, min_size=5.4, color=PALETTE["ink"])
        cy_box += bh_card + card_gap

    # -------------------------------------------------------------------------
    # COLUMN 3 (Right): Shared Central Market Share Track (x = 514, w = 238)
    # -------------------------------------------------------------------------
    g_x, g_w = 514.0, 238.0
    page.rect(g_x, col_top, g_w, col_h, stroke=PALETTE["red"], fill=PALETTE["white"], line_width=1.1)
    page.rect(g_x, col_top, g_w, 22.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.9)
    page.rich_line(g_x + g_w / 2.0, col_top + 15.0, "{RED} **CENTRAL MARKET SHARE TRACK**", size=9.0, color=PALETTE["red"], align="center")

    # Subheader / Start & Max instruction strip
    page.rect(g_x + 6.0, col_top + 26.0, g_w - 12.0, 22.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.rich_line(g_x + g_w / 2.0, col_top + 36.0, "**START:** **14** (2P)  |  **18** (3-4P)  ·  **MAX:** **20**", size=7.2, color=PALETTE["ink"], align="center")
    page.rich_line(g_x + g_w / 2.0, col_top + 45.0, "**-1** per {RED} cube  |  **0** = Market Collapse", size=5.8, color=PALETTE["ink_soft"], align="center")

    # 21-space Track Grid (20 down to 0) in 3 columns x 7 rows — large cells for multiple player markers!
    grid_top = col_top + 53.0
    grid_h = 312.0
    pad_x = 8.0
    gap_c = 5.0
    gap_r = 4.0
    cw = (g_w - 2 * pad_x - 2 * gap_c) / 3.0  # ~70.6 pt wide
    ch = (grid_h - 6 * gap_r) / 7.0           # ~50.3 pt tall

    for idx_val, val in enumerate(range(MARKET_SHARE_MAX, -1, -1)):
        r_i = idx_val // 3
        c_i = idx_val % 3
        cx = g_x + pad_x + c_i * (cw + gap_c)
        cy = grid_top + r_i * (ch + gap_r)
        tag = MARKET_SHARE_START.get(val)
        if val == 0:
            page.rounded_rect(cx, cy, cw, ch, r=3.0, stroke=PALETTE["red"], fill=PALETTE["red"], line_width=1.0)
            page.text(cx + cw / 2.0, cy + 16.5, "0", font="bold", size=15.0, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 27.5, "MARKET", font="mono_bold", size=6.0, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 35.5, "COLLAPSE", font="mono_bold", size=6.0, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 45.0, "Final Round", font="italic", size=5.4, color=PALETTE["white"], align="center")
        elif tag:
            page.rounded_rect(cx, cy, cw, ch, r=3.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=1.0)
            page.rect(cx, cy, cw, 12.0, stroke=PALETTE["red"], fill=PALETTE["red"], line_width=0.6)
            page.text(cx + cw / 2.0, cy + 8.6, tag, font="mono_bold", size=5.8, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 36.0, str(val), font="bold", size=17.0, color=PALETTE["ink"], align="center")
        elif val == MARKET_SHARE_MAX:
            page.rounded_rect(cx, cy, cw, ch, r=3.0, stroke=PALETTE["red"], fill=PALETTE["paper_tint"], line_width=0.9)
            page.rect(cx, cy, cw, 12.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.6)
            page.text(cx + cw / 2.0, cy + 8.6, "TRACK MAX", font="mono_bold", size=5.8, color=PALETTE["red"], align="center")
            page.text(cx + cw / 2.0, cy + 36.0, str(val), font="bold", size=17.0, color=PALETTE["ink"], align="center")
        else:
            page.rounded_rect(cx, cy, cw, ch, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.7)
            page.text(cx + cw / 2.0, cy + 31.0, str(val), font="bold", size=16.0, color=PALETTE["ink"], align="center")

    # Market Leader Bonus & Collapse Callout Box at bottom of Right Column
    mb_y = grid_top + grid_h + 6.0
    mb_h = col_bot - mb_y - 6.0
    page.rounded_rect(g_x + 6.0, mb_y, g_w - 12.0, mb_h, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.8)
    page.rect(g_x + 6.0, mb_y, g_w - 12.0, 14.5, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.6)
    page.text(g_x + g_w / 2.0, mb_y + 10.2, "MARKET LEADER BONUS & TIEBREAKERS", font="bold", size=6.6, color=PALETTE["white"], align="center")
    page.rich_paragraph(
        g_x + 10.0, mb_y + 23.0, g_w - 20.0,
        "**Bonus (no Patient Zeros):** **1st +3**, **2nd +1** Secrets *(ties share)*.\n"
        "**When:** End of P6 if a **Red Secret** banked, & **Game End** *(not Wipeout)*.\n"
        "**2P SETEC Corp ({BLACK}):** Starts **0**; **+1** MS if **>=1** {RED} exits tray; ranks in MLB.\n"
        "**Ties:** Market Share > $ > Ready Colored > {RESEARCH} > Fewest Under Dev.",
        size=5.8, leading=7.8, color=PALETTE["ink"],
    )


# =============================================================================
# 2B. Companion Software Market & Supply Board (Page 2 of Central Boards)
# =============================================================================

def render_market_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // SOFTWARE MODULE MARKET & CENTRAL SUPPLY [2/2]",
        right_tag="PNP PROTOTYPE v0.47.0 // US LETTER",
    )

    # Top Title Bar
    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "SOFTWARE MODULE MARKET  &  CENTRAL COMPILER SUPPLY", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "4 MARKET STACKS (R/B/G/Y)  |  PURPLE IN PERSONAL RESERVES", font="mono", size=7.0, color=PALETTE["rule"], align="right")

    # -------------------------------------------------------------------------
    # TOP ROW: Staging Cup Zone & Compiler Exit Sorting Tray (2 Wide Symmetric Panels)
    # -------------------------------------------------------------------------
    ty, th = 64.0, 126.0
    top_w = (712.0 - 14.0) / 2.0  # 349.0 pt each (matches bottom row symmetry!)

    # 1. Staging Cup Zone (x = 40, w = 349)
    page.rect(40.0, ty, top_w, th, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(40.0, ty, top_w, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(40.0 + top_w / 2.0, ty + 13.2, "STAGING CUP (RELAY QUEUE)", font="bold", size=8.6, color=PALETTE["ink"], align="center")
    page.circle(104.0, ty + 73.0, 38.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.1, dash=(4, 2))
    page.circle(104.0, ty + 73.0, 28.0, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
    page.text(104.0, ty + 71.0, "STAGING", font="mono_bold", size=7.2, color=PALETTE["muted"], align="center")
    page.text(104.0, ty + 80.5, "CUP", font="mono_bold", size=7.2, color=PALETTE["muted"], align="center")
    page.rich_paragraph(
        158.0, ty + 32.0, 180.0,
        "**Queued for Next Drop:**\n"
        "- **P1 Pulse:** Injected {BLACK} Cube\n"
        "- **P4 End:** Recycled {RED}{BLUE}{GREEN} Cubes\n"
        "- **Corruption:** Advance Track Cubes",
        size=7.2, leading=10.5, color=PALETTE["ink_soft"],
    )
    page.text(40.0 + top_w / 2.0, ty + 118.0, "Setup Priming: Drop 1 R/B/G/Black into tower; stuck cubes prime R1.", font="italic", size=6.0, color=PALETTE["muted"], align="center")

    # 2. Phase 2 Exit Sorting Tray (x = 403, w = 349)
    ex_x = 40.0 + top_w + 14.0
    page.rect(ex_x, ty, top_w, th, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(ex_x, ty, top_w, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(ex_x + top_w / 2.0, ty + 13.2, "COMPILER EXIT TRAY (SORTING & RESOLUTION)", font="bold", size=8.6, color=PALETTE["ink"], align="center")
    tray_cols = [
        ("green", "P4: GREEN", "Vuln. Hit [1st Sig]"),
        ("black", "P2: CORRUPT", "Track [2nd Sig]"),
        ("blue", "P4: BLUE", "-1 Sec [3rd Sig]"),
        ("red", "P4: RED", "-1 MS [4th Sig]"),
    ]
    tw_sub = 74.0
    tgap = 8.0
    tx0 = ex_x + (top_w - (4 * tw_sub + 3 * tgap)) / 2.0
    for i, (ck, clbl, csub) in enumerate(tray_cols):
        bx = tx0 + i * (tw_sub + tgap)
        fg, bg = _color_pair(ck)
        page.rounded_rect(bx, ty + 26.0, tw_sub, 76.0, r=3.0, stroke=fg, fill=bg if ck != "black" else PALETTE["paper_tint"], line_width=0.8)
        page.draw_color_badge(bx + tw_sub / 2.0, ty + 46.0, 13.0, ck)
        page.text(bx + tw_sub / 2.0, ty + 72.0, clbl, font="mono_bold", size=6.5, color=PALETTE["ink"], align="center")
        page.text(bx + tw_sub / 2.0, ty + 86.0, csub, font="regular", size=5.8, color=PALETTE["ink_soft"], align="center")
    page.text(ex_x + top_w / 2.0, ty + 117.5, "Black resolves in P2; Red/Blue/Green attack in P4. Target Lock Tie Priority: Green > Black > Blue > Red.", font="italic", size=6.0, color=PALETTE["muted"], align="center")

    # -------------------------------------------------------------------------
    # MIDDLE ROW: 4 Software Module Market Slots (x = 40..752, y = 200..498)
    # Streamlined 4-stack market layout with spacious 166 pt column width!
    # -------------------------------------------------------------------------
    my, mh = 200.0, 298.0
    mgap = 16.0
    mw = (712.0 - 3 * mgap) / 4.0  # 166.0 pt wide each!

    market_colors = [
        ("red", "RED // MARKETING"),
        ("blue", "BLUE // FIREWALL"),
        ("green", "GREEN // ANTIVIRUS"),
        ("yellow", "YELLOW // COMM. AI"),
    ]

    for idx, (ckey, mtitle) in enumerate(market_colors):
        sx = 40.0 + idx * (mw + mgap)
        fg, bg = _color_pair(ckey)
        page.rect(sx, my, mw, mh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
        # Header
        page.rect(sx, my, mw, 22.0, stroke=PALETTE["ink"], fill=bg, line_width=0.8)
        page.rect(sx, my, mw, 3.5, stroke=None, fill=fg)
        page.draw_color_badge(sx + 12.0, my + 12.5, 9.0, ckey)
        page.text(sx + 24.0, my + 15.2, mtitle, font="bold", size=8.0, color=fg)

        # Card Slot (126 x 194 pt centered vertically in remaining column space)
        cs_w, cs_h = 126.0, 194.0
        cs_x = sx + (mw - cs_w) / 2.0
        cs_y = my + 22.0 + (mh - 22.0 - cs_h) / 2.0  # 200 + 22 + (276 - 194)/2 = 263.0
        page.rect(cs_x, cs_y, cs_w, cs_h, stroke=fg, fill=PALETTE["paper_tint"], line_width=0.8, dash=(4, 2.5))
        page.corner_ticks(cs_x, cs_y, cs_w, cs_h, size=6.0, color=fg)
        page.draw_star_icon(cs_x + cs_w / 2.0, cs_y + 72.0, 18.0, fill=PALETTE["rule"])
        page.text(cs_x + cs_w / 2.0, cs_y + 98.0, f"PLACE {ckey.upper()} (STAR)", font="mono_bold", size=7.0, color=PALETTE["muted"], align="center")
        page.text(cs_x + cs_w / 2.0, cs_y + 110.0, "VARIANT CARD HERE", font="mono", size=6.7, color=PALETTE["muted"], align="center")
        page.text(cs_x + cs_w / 2.0, cs_y + 130.0, "Stack 2x Players", font="italic", size=7.0, color=PALETTE["muted"], align="center")
        page.text(cs_x + cs_w / 2.0, cs_y + 141.0, "Colored Dice on card", font="italic", size=7.0, color=PALETTE["muted"], align="center")

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
        48.0, fy + 27.5, fw - 16.0,
        "- **2P / 3P / 4P:** **$6** | **5** Secrets | **14 (2P) / 18 (3-4P)** Share [Max 20] | **0** {RESEARCH}\n"
        "- **Market:** **4 / 6 / 8** dice/color | All tracks L0 | Vulnerability **0** | 2P: **SETEC {BLACK}** at **0**\n"
        "- **Player Start:** 2 Gray + 1 Company die + 1 Purple in Ready; 1 Purple in Reserve",
        size=6.6, leading=9.5, color=PALETTE["ink"],
    )

    # Right: Portfolio Scoring & End-Game Triggers
    rx_f = 40.0 + fw + 14.0
    page.rect(rx_f, fy, fw, fh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx_f, fy, fw, 16.5, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
    page.text(rx_f + 8.0, fy + 11.8, "SECRETS VICTORY & TIEBREAKERS  (SURVIVING OPERATIVES)", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_paragraph(
        rx_f + 8.0, fy + 27.5, fw - 16.0,
        "- **Market Leader Bonus:** **1st +3**, **2nd +1** Secrets *(ties share; P6 if Red Secret & End)*\n"
        "- **Victory:** Most **Corporate Secrets** wins. **Ties:** Share > $ > Ready Colored > {RESEARCH} > Fewest Dev.\n"
        "- **Ends:** Singularity | Final Round (**Patient Zero** or **Market Collapse**) | Total Wipeout",
        size=6.4, leading=9.5, color=PALETTE["ink"],
    )


# =============================================================================
# 3. Dice Visual Aids & Printable Variant (★) Market Cards (4 Pages)
# =============================================================================

SECRET_YIELD_SHORT = {
    "red": "Bank +2 (MLB)",
    "blue": "Bank +2 (+3 @ Pen L3)",
    "green": "Bank +2, -2 Vuln.",
    "purple": "Bank +1",
}


def render_master_dice_reference(page: PDFPage) -> None:
    """Page 1 of Dice Aids: Large-Print Full-Table Master Pip-to-Ability Reference."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // MASTER DICE PIP & ABILITY VISUAL AID [1/4]",
        right_tag="PNP PROTOTYPE v0.47.0 // US LETTER",
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

    # 6 Die Rows
    row_h = 56.0
    for r_idx, dspec in enumerate(DICE_SPECS):
        ry = ty + hh + r_idx * row_h
        fg, bg = _color_pair(dspec.color_key)
        row_bg = PALETTE["white"] if r_idx % 2 == 0 else PALETTE["paper_tint"]
        page.rect(tx, ry, tw, row_h, stroke=PALETTE["ink"], fill=row_bg, line_width=0.85)

        # Left color tab + Die Name
        page.rect(tx, ry, 5.0, row_h, stroke=None, fill=fg)
        page.draw_color_badge(tx + 17.0, ry + 18.0, 11.0, dspec.color_key)
        page.text(tx + 28.0, ry + 21.5, dspec.title, font="bold", size=9.2, color=fg)
        page.text(tx + 12.0, ry + 34.5, dspec.subtitle, font="regular", size=7.4, color=PALETTE["ink_soft"])

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
            has_warn = "{WARN}" in f_mk
            f_mk = f_mk.replace(" {WARN}", "")
            is_star = "{STAR}" in f_mk
            is_secret = "{SECRET}" in f_mk
            is_choice = "/" in f_mk

            if is_star:
                page.rounded_rect(fx + 5.0, ry + 7.0, col_face - 10.0, row_h - 14.0, r=3.0, stroke=fg, fill=bg, line_width=0.7)
                page.rich_line(fx + col_face / 2.0, ry + 23.0, f"**{f_mk}**", size=8.0, color=fg, align="center")
                if dspec.color_key == "purple":
                    page.text(fx + col_face / 2.0, ry + 33.5, "White Hat Power", font="bold", size=6.3, color=PALETTE["purple"], align="center")
                    page.text(fx + col_face / 2.0, ry + 42.0, "Signature Protocol", font="italic", size=5.5, color=PALETTE["ink_soft"], align="center")
                else:
                    page.text(fx + col_face / 2.0, ry + 36.5, "See Market Card", font="italic", size=6.3, color=PALETTE["ink_soft"], align="center")
            elif is_secret:
                page.rounded_rect(fx + 5.0, ry + 7.0, col_face - 10.0, row_h - 14.0, r=3.0, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=0.8)
                page.rich_line(fx + col_face / 2.0, ry + 22.0, f"**{f_mk}**", size=8.0, color=PALETTE["blue"], align="center")
                page.text(fx + col_face / 2.0, ry + 31.5, "-> Processing Box", font="mono_bold", size=5.4, color=PALETTE["ink"], align="center")
                page.text(fx + col_face / 2.0, ry + 39.0, SECRET_YIELD_SHORT[dspec.color_key], font="italic", size=5.4, color=PALETTE["ink_soft"], align="center")
            elif is_choice:
                page.rounded_rect(fx + 4.0, ry + 5.0, col_face - 8.0, row_h - 10.0, r=3.0, stroke=PALETTE["muted"], fill=PALETTE["white"], line_width=0.6)
                parts_c = [p.strip() for p in f_mk.split("/")]
                lines_c: List[Tuple[str, bool]] = []
                for pi_, part_ in enumerate(parts_c):
                    for ln_ in _wrap_to_width(part_, col_face - 14.0, "bold", 6.8):
                        lines_c.append((ln_, True))
                    if pi_ == 0:
                        lines_c.append(("-- OR --", False))
                lead_c = 7.2
                y_c = ry + row_h / 2.0 - (len(lines_c) - 1) * lead_c / 2.0 + 2.2
                for ln_, is_opt in lines_c:
                    if is_opt:
                        page.rich_line(fx + col_face / 2.0, y_c, f"**{ln_}**", size=6.8, color=PALETTE["ink"], align="center")
                    else:
                        page.text(fx + col_face / 2.0, y_c, ln_, font="mono_bold", size=5.0, color=PALETTE["muted"], align="center")
                    y_c += lead_c
            else:
                plain_size = min(8.4, 8.4 * (col_face - 12.0) / max(1.0, measure_text(f_mk, font="bold", size=8.4)))
                page.rich_line(fx + col_face / 2.0, ry + 29.5, f"**{f_mk}**", size=max(plain_size, 5.8), color=PALETTE["ink"], align="center")
            if has_warn:
                page.draw_warn_icon(fx + col_face - 13.0, ry + 15.0, 11.0)

    # Bottom strip (y = 442..578, h = 136 pt): Secret Face Yields table + two rules callouts
    by = 442.0
    bh = 136.0
    yw = 232.0
    page.rect(40.0, by, yw, bh, stroke=PALETTE["blue"], fill=PALETTE["white"], line_width=0.9)
    page.rect(40.0, by, yw, 16.0, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=0.7)
    page.rich_line(47.0, by + 11.4, "{SECRET} **SECRET FACE YIELDS** (Face 5, banked when it leaves the Processing Box)", size=5.6, color=PALETTE["blue"])
    yield_rows = [
        ("red", "RED", "**+2** Secrets *(triggers **Market Leader Bonus**)*."),
        ("blue", "BLUE", "**+2** Secrets (**+1** at Pen Test L3+, max **+3**)."),
        ("green", "GREEN", "**+2** Secrets, then **-2 Vulnerability**."),
        ("purple", "PURPLE", "**+1** Secret."),
    ]
    yr_h = 17.0
    for yi, (yk, yn, yt) in enumerate(yield_rows):
        yy = by + 18.0 + yi * yr_h
        fgy, bgy = _color_pair(yk)
        page.rect(40.0, yy, yw, yr_h, stroke=PALETTE["rule"], fill=PALETTE["white"] if yi % 2 == 0 else PALETTE["paper_tint"], line_width=0.5)
        page.rect(40.0, yy, 4.0, yr_h, stroke=None, fill=fgy)
        page.text(49.0, yy + 11.0, yn, font="bold", size=6.2, color=fgy)
        _fit_paragraph(page, 86.0, yy + (7.6 if yk in ("blue", "green") else 11.0), yw - 92.0, yt, yy + yr_h + 6.0, size=5.4 if yk in ("blue", "green") else 5.6, leading=6.0, min_size=4.5, color=PALETTE["ink"])
    page.text(46.0, by + bh - 6.4, "Dice still in the Processing Box at game end, or returned to supply, bank nothing.", font="italic", size=4.6, color=PALETTE["muted"])

    box_w = (712.0 - yw - 20.0) / 2.0
    callouts = [
        (
            "CHOICE FACES & VULNERABILITY",
            (
                "- **Slash ( / ):** Choose **1** option in Phase 1 Step 4 *(e.g. Red Face 1: +1 Market Share OR +$1)*. **Ampersand ( & ):** gain **both**.\n"
                "- **{WARN} Vulnerability:** each {WARN} on your final faces (Secret faces always) = **+1 Vulnerability** at lock-in (max 15). {GREEN} cubes hit the highest at **4+**: **-1 / -2 / -3** Secrets, then reset to **0**. Pen Test (P5): **2 {RESEARCH} = -1**.\n"
                "- **Secret Faces:** Secret faces (Face 5) may be rerolled or kept normally during rerolls."
            ),
        ),
        (
            "BREAKTHROUGHS & MILESTONES // TRACKS 1/2/2/3 {RESEARCH}",
            (
                "- **Pen Test:** L1 +1 Gray die | L2 limit 2 | L3 +1 Secret (+Blue Secret +1) | L4 limit 3 + free -1 Vulnerability each Operations Turn.\n"
                "- **Release:** L1 +1 Gray die | L3 +1 Secret | L4 BW 6 + set 1 rolled Gray die to any face.\n"
                "- **Triage:** L1 +1 Gray die | L2 BW 2 | L3 +1 Secret | L4 BW 2 + Replace 1 Gray -> Colored ($0, to Ready).\n"
                "- **Public Relations** ($3 Cash per +1 Market Share): L1 +$3 Cash | L3 2nd Purple die (to Scanned) | L4 Regain up to 3/turn + +2 MS now.\n"
                "- Breakthrough Gray dice -> Ready; PR L3 Purple & bought dice -> Scanned. Max 2 hardware upgrades/turn."
            ),
        ),
    ]
    for i, (ct, cb) in enumerate(callouts):
        cx = 40.0 + yw + 10.0 + i * (box_w + 10.0)
        page.rect(cx, by, box_w, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.9)
        page.rect(cx, by, box_w, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
        page.rich_line(cx + 7.0, by + 11.4, f"**{ct}**", size=6.6, color=PALETTE["ink"])
        _fit_paragraph(page, cx + 7.0, by + 27.0, box_w - 14.0, cb, by + bh - 3.0, size=6.7, leading=9.0, min_size=4.8, color=PALETTE["ink"])


def render_four_player_pocket_aids(page: PDFPage) -> None:
    """Page 2 of Dice Aids: 4x Cut-Out Individual Player Dice & Yield Reference Cards (2x2 grid)."""
    page.text(40.0, 18.0, "TOO MANY SECRETS // INDIVIDUAL PLAYER DICE & YIELD REFERENCE CARDS (CUT ALONG DASHED LINES — 1 PER PLAYER) [2/5]", font="mono_bold", size=6.5, color=PALETTE["muted"])

    cw, ch = 356.0, 272.0  # 4.94" x 3.78" each
    gx0, gy0 = 32.0, 26.0
    gap_x, gap_y = 16.0, 16.0

    # Dashed cut lines through center gutters
    mid_x = gx0 + cw + gap_x / 2.0
    mid_y = gy0 + ch + gap_y / 2.0
    page.line(mid_x, 16.0, mid_x, 596.0, stroke=PALETTE["muted"], width=0.5, dash=(4, 3))
    page.line(20.0, mid_y, 772.0, mid_y, stroke=PALETTE["muted"], width=0.5, dash=(4, 3))

    compact_rows = [
        ("gray", "GRAY", "Starter", ("+$1 &\n+1{RESEARCH} {WARN}", "+2{RESEARCH} {WARN}", "+$2 /\n+2{RESEARCH} {WARN}", "+$1 /\n+1{RESEARCH}", "+$1", "+1{RESEARCH}")),
        ("red", "RED", "$4-$5", ("+1 Share\n/ +$1 {WARN}", "+$2", "+$2", "+$2", "{SECRET} Secret {WARN}", "{RED} {STAR}")),
        ("blue", "BLUE", "$4-$5", ("+1 Secret", "+2{RESEARCH}", "+$2 {WARN}", "+1{RESEARCH}\n/ +$1", "{SECRET} Secret {WARN}", "{BLUE} {STAR}")),
        ("green", "GREEN", "$4-$5", ("+2{RESEARCH} {WARN}", "+1{RESEARCH}", "+2{RESEARCH}", "+1{RESEARCH}\n/ +$1", "{SECRET} Secret {WARN}", "{GREEN} {STAR}")),
        ("yellow", "YELLOW", "$5-$6", ("+2 Share {WARN}", "+1 Share\n/ +1{RESEARCH}", "+$1 &\n+1 Share", "+$2 /\n+1{RESEARCH}", "+$2 /\n+1{RESEARCH} {WARN}", "{YELLOW} {STAR}")),
        ("purple", "PURPLE", "Not sold", ("+$1 /\n+1{RESEARCH}", "+$1 /\n+1{RESEARCH}", "+$2", "+$1 &\n+1{RESEARCH} {WARN}", "{SECRET} Secret {WARN}", "{PURPLE}{STAR} Protocol")),
    ]

    for r in range(2):
        for c in range(2):
            p_num = r * 2 + c + 1
            x = gx0 + c * (cw + gap_x)
            y = gy0 + r * (ch + gap_y)
            page.crop_marks(x, y, cw, ch)
            page.rect(x, y, cw, ch, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
            page.rect(x, y, cw, 18.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.8)
            page.text(x + 7.0, y + 12.5, f"WHITE HAT DICE & SECRET YIELDS REFERENCE  [P{p_num}]", font="bold", size=7.8, color=PALETTE["white"])
            page.text(x + cw - 7.0, y + 12.5, "1-6 PIP MAP", font="mono", size=6.5, color=PALETTE["rule"], align="right")

            # Mini table header
            ty = y + 18.0
            c_name = 52.0
            c_cost = 44.0
            c_f = (cw - c_name - c_cost) / 6.0  # 43.3 pt
            page.rect(x, ty, cw, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
            page.text(x + 5.0, ty + 12.6, "DIE", font="bold", size=6.5, color=PALETTE["ink"])
            page.text(x + c_name + c_cost / 2.0, ty + 12.6, "COST", font="bold", size=6.5, color=PALETTE["ink"], align="center")
            for p_i in range(6):
                fx = x + c_name + c_cost + p_i * c_f
                page.line(fx, ty, fx, ty + 19.0, stroke=PALETTE["rule"], width=0.5)
                page.draw_pip_die(fx + c_f / 2.0, ty + 9.5, 11.5, p_i + 1)

            rh = 22.0
            for idx, (ck, dname, dmeta, dfaces) in enumerate(compact_rows):
                ry = ty + 19.0 + idx * rh
                fg, _ = _color_pair(ck)
                page.rect(x, ry, cw, rh, stroke=PALETTE["rule"], fill=PALETTE["white"] if idx % 2 == 0 else PALETTE["paper_tint"], line_width=0.5)
                page.draw_color_badge(x + 9.0, ry + rh / 2.0, 7.5, ck)
                page.text(x + 16.0, ry + rh / 2.0 + 2.4, dname, font="bold", size=6.6, color=fg)
                page.line(x + c_name, ry, x + c_name, ry + rh, stroke=PALETTE["rule"], width=0.5)
                page.text(x + c_name + c_cost / 2.0, ry + rh / 2.0 + 2.2, dmeta, font="mono", size=6.0, color=PALETTE["ink_soft"], align="center")

                for fi, ftxt in enumerate(dfaces):
                    fx = x + c_name + c_cost + fi * c_f
                    page.line(fx, ry, fx, ry + rh, stroke=PALETTE["rule"], width=0.5)
                    has_warn = "{WARN}" in ftxt
                    ftxt = ftxt.replace(" {WARN}", "")
                    f_col = fg if "{STAR}" in ftxt else (PALETTE["blue"] if "{SECRET}" in ftxt else PALETTE["ink"])
                    f_lines = ftxt.split("\n")
                    if len(f_lines) == 1:
                        f_sz = min(6.4, 6.4 * (c_f - (13.0 if has_warn else 3.0)) / max(1.0, measure_text(f_lines[0], font="bold", size=6.4)))
                        page.rich_line(fx + c_f / 2.0 - (4.0 if has_warn else 0.0), ry + rh / 2.0 + 2.2, f"**{f_lines[0]}**", size=max(f_sz, 4.8), color=f_col, align="center")
                    else:
                        for li_, ltxt in enumerate(f_lines):
                            page.rich_line(fx + c_f / 2.0 - (4.0 if has_warn else 0.0), ry + 7.5 + li_ * 6.8, f"**{ltxt}**", size=5.0, color=f_col, align="center")
                    if has_warn:
                        page.draw_warn_icon(fx + c_f - 6.0, ry + rh / 2.0, 7.5)

            # Clean Secret Face Yields & Icon Legend Footer
            fy = ty + 19.0 + len(compact_rows) * rh
            fh = y + ch - fy
            page.rect(x, fy, cw, fh, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.7)
            page.rect(x, fy, cw, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
            page.rich_line(x + 6.0, fy + 9.8, "{SECRET} **SECRET FACE YIELDS** *(banked when leaving Processing Box)*", size=6.2, color=PALETTE["ink"])
            page.rich_paragraph(
                x + 6.0, fy + 23.0, cw - 12.0,
                "- {RED} **Red Secret:** **+2** Corporate Secrets *(also triggers **Market Leader Bonus** at end of Phase 6)*\n"
                "- {BLUE} **Blue Secret:** **+2** Secrets (**+1** at Pen Test L3+; max **3**)\n"
                "- {GREEN} **Green Secret:** **+2** Secrets, then **-2 Vulnerability**   |   {PURPLE} **Purple Secret:** **+1** Secret\n"
                "- {WARN} = **+1 Vulnerability** if kept (P1 Step 4)   |   **Choice ( / ):** Commit in P1 Step 4   |   **Dual ( & ):** Gain both",
                size=5.6, leading=8.0, color=PALETTE["ink"],
            )


def render_four_player_round_reference_cards(page: PDFPage) -> None:
    """Page 3 of Dice Aids: 4x Cut-Out Individual Player Six-Phase Round Reference Cards (2x2 grid)."""
    page.text(40.0, 18.0, "TOO MANY SECRETS // INDIVIDUAL PLAYER SIX-PHASE ROUND REFERENCE CARDS (CUT ALONG DASHED LINES — 1 PER PLAYER) [3/5]", font="mono_bold", size=6.5, color=PALETTE["muted"])

    cw, ch = 356.0, 272.0  # 4.94" x 3.78" each — matches Dice Pocket Aid size (can be backed 2-sided!)
    gx0, gy0 = 32.0, 26.0
    gap_x, gap_y = 16.0, 16.0

    # Dashed cut lines through center gutters
    mid_x = gx0 + cw + gap_x / 2.0
    mid_y = gy0 + ch + gap_y / 2.0
    page.line(mid_x, 16.0, mid_x, 596.0, stroke=PALETTE["muted"], width=0.5, dash=(4, 3))
    page.line(20.0, mid_y, 772.0, mid_y, stroke=PALETTE["muted"], width=0.5, dash=(4, 3))

    phases = [
        (
            "P1: ROLL & DEPLOY (Simultaneous)",
            "**1. Pulse:** +1 {BLACK} -> Staging Cup (do pending Version Switch first). **2-3. Roll & Rerolls:** Roll Ready dice; up to 2 free rerolls (Secret faces can reroll). **4. Lock-in:** each {WARN} kept = **+1 Vulnerability**. Secret faces -> Processing Box; rest -> In Production.",
        ),
        (
            "P2: COMPILER DROP & CORRUPTION",
            "**Drop** Staging Cup into Tower. Exited {BLACK} fill Corruption Track **now** (v3.0 full = **Singularity!**). Signature Cube exits -> **Target Lock** (return to mat). Empty Tray: +1 {RED}{BLUE}{GREEN} -> Staging Cup. *(Patient Zero skips P3-P6; survivors finish Final Round.)*",
        ),
        (
            "P3: INCOME (Simultaneous)",
            "Collect $, {RESEARCH}, Secrets, Market Share & {STAR} from dice still **In Production**. Purple {STAR} protocols fire once/die. Then **Customer Poaching** (clockwise from First Player): -1 Share from top rival.",
        ),
        (
            "P4: ATTACK RESOLUTION (Simultaneous)",
            "No cube can be blocked. {RED} **-1 Share** | {BLUE} **-1 Secret** | {GREEN} one at a time hits highest **Vulnerability 4+** (ties all): **-1 / -2 / -3** Secrets, reset to **0**. **Target Lock** *(tie {GREEN} > {BLACK} > {BLUE} > {RED})*: {GREEN} +green on 2 tracks (2x {RESEARCH}) | {BLACK} Override Used (-2 Sec if used) | {BLUE} 1 Gray -> Processing (0 Sec) | {RED} -2 Share, +2 to lowest rival (2P: or SETEC Corp). Recycle {RED}{BLUE}{GREEN} -> Cup *(2P: {BLACK} +1 MS if >=1 {RED})*. **End Check:** Wipeout, PZ, **Market Collapse**.",
        ),
        (
            "P5: OPERATIONS (Clockwise from First Player)",
            "Upgrade Tracks (<= 2/turn [1/2/2/3 {RESEARCH}]; L1/L3 Breakthroughs resolve at once) | Regain Market Share ($3 each, up to PR limit 1/1/2/2/3) | **Pen Test** (2 {RESEARCH} = -1 Vulnerability, up to limit 1/1/2/2/3) | Buy <= 1 die -> Scanned Box.",
        ),
        (
            "P6: CI/CD PIPELINE SHIFT (Simultaneous)",
            "**1.** Magnetic Splice. **2.** In Production -> **Scanned Box**. **3.** Scanned -> **Ready** (<= Release Bandwidth 4/5/6). **4.** Conveyor Triage: **Processing -> Scanned** (<= Triage Bandwidth, oldest first; banks Secret & queues Signature Cube). **5.** Red Secret banked: **Market Leader Bonus**. Pass First Player.",
        ),
    ]

    for r in range(2):
        for c in range(2):
            p_num = r * 2 + c + 1
            x = gx0 + c * (cw + gap_x)
            y = gy0 + r * (ch + gap_y)
            page.crop_marks(x, y, cw, ch)
            page.rect(x, y, cw, ch, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
            page.rect(x, y, cw, 18.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.8)
            page.text(x + 7.0, y + 12.5, f"SIX-PHASE ROUND REFERENCE CARD  [P{p_num}]", font="bold", size=7.8, color=PALETTE["white"])
            page.text(x + cw - 7.0, y + 12.5, "ROUND FLOW & SCORING", font="mono", size=6.2, color=PALETTE["rule"], align="right")

            cy = y + 21.0
            for p_title, p_body in phases:
                page.rect(x + 5.0, cy, cw - 10.0, 10.5, stroke=PALETTE["rule"], fill=PALETTE["panel_tint"], line_width=0.5)
                page.text(x + 8.0, cy + 7.6, p_title, font="bold", size=6.0, color=PALETTE["ink"])
                cy = page.rich_paragraph(x + 8.0, cy + 16.5, cw - 16.0, p_body, size=5.5, leading=7.0, color=PALETTE["ink"])
                cy += 1.5

            # Bottom Victory & Tiebreakers Strip
            vy = y + ch - 25.0
            page.rect(x + 5.0, vy, cw - 10.0, 21.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.6)
            page.rich_paragraph(
                x + 8.0, vy + 7.5, cw - 16.0,
                "**VICTORY & MARKET LEADER BONUS:** **1st +3**, **2nd +1** Secrets by Share (ties share; no PZ) at P6 if Red Secret banked & at Game End. Most **Secrets** wins! *Ties: Share > $ > Ready Colored > {RESEARCH} > Fewest Dev.*",
                size=5.3, leading=6.8, color=PALETTE["ink"],
            )


def _draw_single_variant_card(page: PDFPage, x: float, y: float, w: float, h: float, card: VariantCardSpec) -> None:
    """Draw a single 126 x 194 pt Software Module Variant (★) Market Card."""
    fg, bg = _color_pair(card.color_key)
    page.crop_marks(x, y, w, h, length=4.5, offset=2.0)
    page.rounded_rect(x, y, w, h, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)

    # Top Color Banner
    page.rect(x, y, w, 24.0, stroke=PALETTE["ink"], fill=bg, line_width=0.8)
    page.rect(x, y, w, 3.5, stroke=None, fill=fg)
    page.draw_color_badge(x + 11.0, y + 13.8, 9.0, card.color_key)
    page.text(x + 20.0, y + 16.5, card.die_label, font="bold", size=7.2, color=fg)
    # Code pill on right
    page.rounded_rect(x + w - 26.0, y + 6.0, 20.0, 13.0, r=2.0, stroke=fg, fill=PALETTE["white"], line_width=0.7)
    page.text(x + w - 16.0, y + 15.0, card.code, font="mono_bold", size=7.0, color=fg, align="center")

    # Cost Sub-bar
    page.rect(x, y + 24.0, w, 16.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.text(x + w / 2.0, y + 35.0, f"Cost: {card.cost_str}", font="bold", size=8.0, color=PALETTE["ink"], align="center")

    # Prominent Face 6 (★) Variant Box
    sy = y + 44.0
    sh = h - 44.0 - 20.0  # 130 pt tall
    page.rect(x + 5.0, sy, w - 10.0, sh, stroke=fg, fill=PALETTE["white"], line_width=0.9)
    page.rect(x + 5.0, sy, w - 10.0, 18.5, stroke=fg, fill=bg, line_width=0.6)
    page.draw_pip_die(x + 16.0, sy + 9.2, 12.0, 6)
    page.rich_line(x + w - 9.0, sy + 12.5, "{STAR} **FACE 6 VARIANT**", size=7.0, color=fg, align="right")

    # Variant Title & Timing
    page.text(x + w / 2.0, sy + 34.0, card.name.upper(), font="bold", size=8.2, color=PALETTE["ink"], align="center")
    page.text(x + w / 2.0, sy + 44.5, card.timing, font="mono_bold", size=6.0, color=fg, align="center")
    page.line(x + 10.0, sy + 49.0, x + w - 10.0, sy + 49.0, stroke=PALETTE["rule"], width=0.5)

    # Variant Effect Body
    _fit_paragraph(page, x + 9.0, sy + 62.0, w - 18.0, card.effect, sy + sh - 4.0, size=7.0, leading=10.0, min_size=5.6)

    # Bottom Footer Note
    fn_size = min(5.8, 5.8 * (w - 10.0) / max(1.0, measure_text(card.footer_note, font="italic", size=5.8)))
    page.text(x + w / 2.0, y + h - 7.0, card.footer_note, font="italic", size=fn_size, color=PALETTE["muted"], align="center")


def _draw_color_divider_card(page: PDFPage, x: float, y: float, w: float, h: float, dspec: DieSpec, variants: Sequence[VariantCardSpec]) -> None:
    """Draw a bonus All-in-One Market Summary / Divider Card for a die color."""
    fg, bg = _color_pair(dspec.color_key)
    page.crop_marks(x, y, w, h, length=4.5, offset=2.0)
    page.rounded_rect(x, y, w, h, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.0)
    page.rect(x, y, w, 24.0, stroke=PALETTE["ink"], fill=fg, line_width=0.8)
    page.text(x + w / 2.0, y + 15.5, f"{dspec.title} // ALL VARIANTS", font="bold", size=7.5, color=PALETTE["white"], align="center")
    page.text(x + w / 2.0, y + 36.0, f"Market Cost: {dspec.cost_str}", font="bold", size=6.2, color=PALETTE["ink_soft"], align="center")

    cy = y + 49.0
    for v in variants:
        page.rounded_rect(x + 5.0, cy - 8.5, w - 10.0, 43.0, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
        page.text(x + 9.0, cy + 1.0, f"[{v.code}] {v.name}", font="bold", size=6.6, color=fg)
        _fit_paragraph(page, x + 9.0, cy + 11.0, w - 18.0, v.effect, cy + 33.0, size=5.8, leading=7.8, min_size=4.5)
        cy += 47.0


def render_variant_market_cards_pages(page3: PDFPage, page4: PDFPage) -> None:
    """Pages 3 & 4 of Dice Aids: All 12 Printable Variant (★) Market Cards (126 x 194 pt) + 4 Deck Summary Cards."""
    # Organize by Color Column (Red, Blue, Green, Yellow) so cutting & sorting is effortless!
    by_color: Dict[str, List[VariantCardSpec]] = {"red": [], "blue": [], "green": [], "yellow": []}
    for vc in VARIANT_CARDS:
        if vc.color_key in by_color:
            by_color[vc.color_key].append(vc)
    order = ["red", "blue", "green", "yellow"]

    cw, ch = 126.0, 194.0  # Matches exact 126 x 194 pt Market Board slot size!
    gap_x = 36.0
    gap_y = 24.0
    total_w = 4 * cw + 3 * gap_x  # 504 + 108 = 612 pt
    x0 = (792.0 - total_w) / 2.0  # 90.0 pt
    y0 = 42.0

    # Page 3: Row 0 = Set 1 (R1..Y1 Baseline), Row 1 = Set 2 (R2..Y2)
    page3.text(52.0, 24.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS -- SHEET 1 (SETS 1 & 2) [4/5]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    page3.text(740.0, 24.0, "SIZE: 1.75\" x 2.69\" (126 x 194 pt -- MATCHES MARKET BOARD)", font="mono", size=6.5, color=PALETTE["muted"], align="right")

    for col_idx, ckey in enumerate(order):
        cx = x0 + col_idx * (cw + gap_x)
        _draw_single_variant_card(page3, cx, y0, cw, ch, by_color[ckey][0])
        _draw_single_variant_card(page3, cx, y0 + ch + gap_y, cw, ch, by_color[ckey][1])

    page3.text(396.0, 594.0, "Setup: Shuffle the 3 Variant (STAR) cards of each market color (R/B/G/Y) and place 1 face-up in each Market slot (Row 1 = Default Baseline R1-Y1).", font="italic", size=6.8, color=PALETTE["muted"], align="center")

    # Page 4: Row 0 = Set 3 (R3..Y3), Row 1 = 4 Color Reference / Divider Cards
    page4.text(52.0, 24.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS -- SHEET 2 (SET 3 + DIVIDERS) [5/5]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    page4.text(740.0, 24.0, "SIZE: 1.75\" x 2.69\" (126 x 194 pt -- MATCHES MARKET BOARD)", font="mono", size=6.5, color=PALETTE["muted"], align="right")

    spec_map = {d.color_key: d for d in DICE_SPECS}
    for col_idx, ckey in enumerate(order):
        cx = x0 + col_idx * (cw + gap_x)
        _draw_single_variant_card(page4, cx, y0, cw, ch, by_color[ckey][2])
        _draw_color_divider_card(page4, cx, y0 + ch + gap_y, cw, ch, spec_map[ckey], by_color[ckey])

    page4.text(396.0, 594.0, "Bottom row provides optional All-Variants Divider / Reference cards for storing each 3-card color mini-deck. Purple uses White Hat Signature Protocols.", font="italic", size=6.8, color=PALETTE["muted"], align="center")


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

    # Profile / Tier badge on right
    tag_fg = PALETTE["rule"] if tile.version in ("v3.0", "v2.0") else PALETTE["muted"]
    page.text(x + w - 6.0, y + 13.0, tile.profile, font="mono_bold", size=5.5, color=tag_fg, align="right")
    tag_w = measure_text(tile.profile, font="mono_bold", size=5.5)

    # Card Name (dynamically fitted so it never collides with right badge)
    avail_name_w = (w - 6.0 - tag_w - 6.0) - 38.0
    name_str = tile.name.upper()
    name_size = 7.8
    name_w = measure_text(name_str, font="bold", size=name_size)
    if name_w > avail_name_w:
        name_size = min(name_size, avail_name_w / (name_w / name_size))
    page.text(x + 38.0, y + 13.5, name_str, font="bold", size=name_size, color=ver_fg)

    # Banner Row (y + 20 .. y + 37.5, h = 17.5 pt, wrapped 2 lines)
    py_bar = y + 20.0
    page.rect(x, py_bar, w, 17.5, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.rich_paragraph(x + 5.0, py_bar + 7.0, w - 10.0, tile.banner_text, size=5.1, leading=6.8, color=PALETTE["ink"])

    # Corruption Track Spaces (y + 38.5 .. y + 107)
    y_track = py_bar + 18.5
    sh = 68.5
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

        # Space effect text below (scaled to avoid overflow in narrow spaces, e.g. v3.0 Singularity)
        sp_size = 4.1 if sp.is_singularity else 5.0
        sp_leading = 5.4 if sp.is_singularity else 6.4
        page.rich_paragraph(sx + 1.5, y_track + 33.0, sw - 3.0, sp.label, size=sp_size, leading=sp_leading, color=PALETTE["ink"], align="center")


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
        ("v3.0 TILES", "Deal 1 face-up to top slot.\nSpace 6 = SINGULARITY!"),
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
    page.text(742.0, 46.5, "1st PLAYER + VERSION + MARKET SHARE + SECRETS + VULNERABILITY + RESEARCH + CREDITS", font="mono", size=6.8, color=PALETTE["muted"], align="right")

    # Row 1 (y = 64..122): Special Markers + 12x Institutional Override Status Chits ([USED] / [FORFEITED])
    # First Player Marker
    page.rounded_rect(42.0, 64.0, 82.0, 52.0, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.2)
    page.text(83.0, 84.0, "FIRST PLAYER", font="bold", size=8.0, color=PALETTE["white"], align="center")
    page.text(83.0, 96.5, "MARKER", font="mono_bold", size=6.6, color=PALETTE["rule"], align="center")
    page.text(83.0, 108.5, "Pass clockwise end of P6", font="italic", size=5.4, color=PALETTE["rule"], align="center")

    # Active SETEC Version Marker
    page.rounded_rect(128.0, 64.0, 82.0, 52.0, r=4.0, stroke=PALETTE["ink_soft"], fill=PALETTE["panel_tint"], line_width=1.2)
    page.text(169.0, 84.0, "ACTIVE VERSION >>", font="bold", size=7.4, color=PALETTE["ink"], align="center")
    page.text(169.0, 97.5, "SETEC TIER POINTER", font="mono_bold", size=5.6, color=PALETTE["ink"], align="center")
    page.text(169.0, 108.5, "Move v1.0 -> v2.0 -> v3.0", font="italic", size=5.4, color=PALETTE["ink_soft"], align="center")

    # 4x Market Share Markers (1 per player; sized to sit in a Market Share track cell)
    for m_i in range(4):
        mx = 214.0 + (m_i % 2) * 38.0
        my = 64.0 + (m_i // 2) * 27.0
        page.rounded_rect(mx, my, 34.0, 25.0, r=3.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.9)
        page.text(mx + 17.0, my + 9.5, "MARKET", font="mono_bold", size=4.6, color=PALETTE["red"], align="center")
        page.text(mx + 17.0, my + 15.5, "SHARE", font="mono_bold", size=4.6, color=PALETTE["red"], align="center")
        page.text(mx + 17.0, my + 22.0, f"P{m_i + 1}", font="bold", size=5.4, color=PALETTE["ink"], align="center")

    # 12x Institutional Override Status Chits (place on v1.0 / v2.0 / v3.0 boxes on Company Card)
    # Clean tight 6x2 grid across x = 294..750 (width = 456 -> 6 * 73 + 5 * 3.6 = 456)
    ah = 25.0
    aw = 73.0
    agap = 3.6
    for i in range(12):
        r = i // 6
        c = i % 6
        bx = 294.0 + c * (aw + agap)
        by = 64.0 + r * (ah + 2.0)
        is_used = (r == 0)
        page.rect(bx, by, aw, ah, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"] if is_used else PALETTE["white"], line_width=0.6, dash=(2, 1))
        page.text(bx + aw / 2.0, by + 11.5, "[X] OVERRIDE USED" if is_used else "[/] FORFEITED", font="mono_bold", size=6.2, color=PALETTE["ink"] if is_used else PALETTE["muted"], align="center")
        page.text(bx + aw / 2.0, by + 20.5, "Override Slot", font="regular", size=5.5, color=PALETTE["muted"], align="center")

    # Section 2 (y = 128..292): 32x Corporate Secret Chits (8 cols x 4 rows)
    page.text(42.0, 136.0, "CORPORATE SECRET TOKENS (x32 — PRIMARY OBJECTIVE / 1 PT EACH)", font="mono_bold", size=6.8, color=PALETTE["blue"])
    sw = (710.0) / 8.0  # 88.75 pt
    sh = 30.0
    sy0 = 141.0
    for r in range(4):
        for c in range(8):
            bx = 41.0 + c * sw
            by = sy0 + r * sh
            page.rect(bx, by, sw, sh, stroke=PALETTE["blue"], fill=PALETTE["white"], line_width=0.6, dash=(3, 1.5))
            page.draw_secret_icon(bx + 15.0, by + 15.0, 12.0, color=PALETTE["blue"])
            page.text(bx + 26.0, by + 13.5, "SECRET", font="bold", size=7.6, color=PALETTE["blue"])
            page.text(bx + 26.0, by + 23.0, "1 Pt  |  Client Data", font="regular", size=5.8, color=PALETTE["muted"])

    # Section 2b (y = 268..330): 4x Vulnerability markers (1 per player; start on 0)
    page.text(42.0, 270.0, "VULNERABILITY MARKERS (x4 — 1 PER PLAYER; START ON 0 OF THE VULNERABILITY TRACK)", font="mono_bold", size=6.8, color=PALETTE["yellow"])
    gy0 = 275.0
    gh = 26.0
    for c in range(4):
        bx = 41.0 + c * sw
        page.rect(bx, gy0, sw, gh, stroke=PALETTE["yellow"], fill=PALETTE["yellow_light"], line_width=0.6, dash=(3, 1.5))
        page.draw_warn_icon(bx + 14.0, gy0 + gh / 2.0, 13.0)
        page.text(bx + 26.0, gy0 + 11.5, "VULNERABILITY", font="mono_bold", size=6.4, color=PALETTE["ink"])
        page.text(bx + 26.0, gy0 + 20.5, f"Marker P{c + 1}", font="mono_bold", size=5.8, color=PALETTE["yellow"])

    # Section 3 (y = 334..420): 16x Research (🔬) Tokens (8 cols x 2 rows)
    page.text(42.0, 342.0, "RESEARCH TOKENS (x16 — UNCAPPED STORAGE)", font="mono_bold", size=6.8, color=PALETTE["green"])
    py0 = 347.0
    ph = 36.0
    for r in range(2):
        for c in range(8):
            bx = 41.0 + c * sw
            by = py0 + r * ph
            page.rect(bx, by, sw, ph, stroke=PALETTE["green"], fill=PALETTE["green_light"], line_width=0.6, dash=(3, 1.5))
            page.draw_research_icon(bx + 15.0, by + 18.0, 13.0, color=PALETTE["green"])
            page.text(bx + 26.0, by + 15.5, "1 RESEARCH", font="bold", size=7.6, color=PALETTE["green"])
            page.text(bx + 26.0, by + 26.0, "Hardware Track Upgrades", font="regular", size=5.4, color=PALETTE["ink_soft"])

    # Section 4 (y = 404..574): Currency Chits ($1 x 24 + $5 x 16)
    page.text(42.0, 434.0, "MONEY TOKENS ($1 x 24  &  $5 x 16)", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    cy0 = 439.0
    ch_h = 28.0
    for r in range(5):
        is_five = (r >= 3)
        val = "$5" if is_five else "$1"
        sub = "FIVE CREDITS" if is_five else "ONE CREDIT"
        fill_c = PALETTE["panel_tint"] if is_five else PALETTE["white"]
        for c in range(8):
            bx = 41.0 + c * sw
            by = cy0 + r * ch_h
            page.rect(bx, by, sw, ch_h, stroke=PALETTE["ink_soft"], fill=fill_c, line_width=0.55, dash=(3, 1.5))
            page.text(bx + 18.0, by + 18.5, val, font="bold", size=11.0, color=PALETTE["ink"], align="center")
            page.text(bx + 34.0, by + 13.5, sub, font="mono_bold", size=5.8, color=PALETTE["ink_soft"])
            page.text(bx + 34.0, by + 22.0, "Tiebreak Asset", font="regular", size=5.4, color=PALETTE["muted"])


# =============================================================================
# Build All Standalone & Combined Print-and-Play PDFs
# =============================================================================

def generate_all_pdfs(out_dir: str) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    generated: List[str] = []

    # 1. Player Terminal Mats & Split Cards (6 pages: 4x Mats with vertical resource holders, expanded PR & FIFO Processing Box + 1x Company Cards + 1x White Hat Cards)
    doc_players = PDFDocument("Too Many Secrets - Player Terminal Mats & Split Cards (v0.47.0)")
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

    # 3. Dice Visual Aids, Round Reference Cards & Printable Variant (★) Market Cards (5 pages)
    doc_dice = PDFDocument("Too Many Secrets - Dice Visual Aids, Round Reference & Variant Market Cards")
    render_master_dice_reference(doc_dice.add_page())
    render_four_player_pocket_aids(doc_dice.add_page())
    render_four_player_round_reference_cards(doc_dice.add_page())
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
    doc_master = PDFDocument("Too Many Secrets - Complete Print and Play Prototype (v0.47.0)")
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
