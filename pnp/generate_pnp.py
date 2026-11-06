"""Master Print-and-Play PDF Generator for Too Many Secrets (Rogue Agent v0.35.0 Baseline).

Generates minimalist, ink-saver, print-ready US Letter (11" x 8.5") PDFs:
  - 01_Player_Boards.pdf (6 pages — 4x Company Terminal Mats with CI/CD Pipeline loop + 6x Client Company Cards sheet + 6x White Hat Dossier Cards sheet)
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
# Canonical Game Data (Synchronized 1:1 with RULES.md v0.35.0 & sim/entities.py)
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
    hardware_summary: str = ""
    starting_bonus: str = ""


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
        hardware_summary="DEF CAP: 2  |  TRIAGE: 2  |  RELEASE: 4  |  ALL 4 TRACKS AT LEVEL 0",
        starting_bonus="START: $6  |  8 SECRETS  |  0 {RESEARCH}  (IDENTICAL FOR EVERY COMPANY)",
    ),
    CompanyCardSpec(
        code="OMNIDYNE",
        name="Omnidyne Systems",
        sector="Tech Giant",
        override_name="Magnetic Splice",
        override_timing="P5: CI/CD STEP 1",
        override_desc=(
            "Move **1 die** from your **Glitched Box** directly to your "
            "**Ready for Release Zone** for **free** (bypassing Scanned)."
        ),
        flavor='"Proprietary hardware backplanes allow instantaneous hot-swapping under live load."',
        hardware_summary="DEF CAP: 2  |  TRIAGE: 2  |  RELEASE: 4  |  ALL 4 TRACKS AT LEVEL 0",
        starting_bonus="START: $6  |  8 SECRETS  |  0 {RESEARCH}  (IDENTICAL FOR EVERY COMPANY)",
    ),
    CompanyCardSpec(
        code="AEGIS",
        name="Aegis Defense Relay",
        sector="Security Firm",
        override_name="Baffle Echo",
        override_timing="P4: ATTACK RESOLUTION",
        override_desc=(
            "When resolving compiler damage, ignore **1 Attack Cube** ({RED}, {BLUE}, or {GREEN}) "
            "of your choice for yourself this round. Exited cubes remain in tray and recycle as normal."
        ),
        flavor='"Multi-layered kinetic dampeners disperse inbound network blast energy."',
        hardware_summary="DEF CAP: 2  |  TRIAGE: 2  |  RELEASE: 4  |  ALL 4 TRACKS AT LEVEL 0",
        starting_bonus="START: $6  |  8 SECRETS  |  0 {RESEARCH}  (IDENTICAL FOR EVERY COMPANY)",
    ),
    CompanyCardSpec(
        code="DTO",
        name="Department of Telecom Oversight",
        sector="Federal Agency",
        override_name="Slush Fund",
        override_timing="P4: ONCE PER GAME",
        override_desc=(
            "The DTO accesses emergency black budget reserves: absorb up to **2 Corporate Secret loss** "
            "(from Blue Spyware or unpaid Red Ransom) for free. **Once per game** (optional when it applies)."
        ),
        flavor='"Classified black budget allocations absorb compliance failures without public oversight."',
        hardware_summary="DEF CAP: 2  |  TRIAGE: 2  |  RELEASE: 4  |  ALL 4 TRACKS AT LEVEL 0",
        starting_bonus="START: $6  |  8 SECRETS  |  0 {RESEARCH}  (IDENTICAL FOR EVERY COMPANY)",
    ),
    CompanyCardSpec(
        code="HELIX",
        name="Helix Biomedical Consortium",
        sector="Medical Research",
        override_name="Brute-Force Bypass",
        override_timing="P1: STEP 4 REROLLS",
        override_desc=(
            "During your rerolls this phase, you may include **any number of Glitched dice** in "
            "your free rerolls. In addition, turn **1 rolled die** to "
            "any legal non-Star face of choice."
        ),
        flavor='"Massively parallel quantum sequencing breaks deterministic encryption gates."',
        hardware_summary="DEF CAP: 2  |  TRIAGE: 2  |  RELEASE: 4  |  ALL 4 TRACKS AT LEVEL 0",
        starting_bonus="START: $6  |  8 SECRETS  |  0 {RESEARCH}  (IDENTICAL FOR EVERY COMPANY)",
    ),
    CompanyCardSpec(
        code="PROMETHEUS",
        name="The Prometheus Foundation",
        sector="Non-Profit",
        override_name="Algorithmic Arbitrage",
        override_timing="P6: OPERATIONS",
        override_desc=(
            "In Phase 6: Operations, purchase **1 Colored Die** from the Central "
            "Market at a **$2 discount** (min $0), **OR** gain an immediate **+$2 cash payout** "
            "from the bank."
        ),
        flavor='"Open-source cryptographic protocols circumvent proprietary enterprise licensing fees."',
        hardware_summary="DEF CAP: 2  |  TRIAGE: 2  |  RELEASE: 4  |  ALL 4 TRACKS AT LEVEL 0",
        starting_bonus="START: $6  |  8 SECRETS  |  0 {RESEARCH}  (IDENTICAL FOR EVERY COMPANY)",
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
        flavor='"Redundant contractor pipelines ready on zero notice."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{PURPLE} {STAR}"),
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
        flavor='"Raw voltage pulses extract signal from dormant silicon."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{PURPLE} {STAR}"),
        protocol_name="Jumper Diagnostics",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, roll **1 offline die** in Under Development; "
            "if Under Development is empty, collect **+$1 cash** "
            "(collect rolled cash and research; shields/glitches produce 0; die remains in place)."
        ),
    ),
    WhiteHatDossierSpec(
        code="ACOUSTIC",
        name="The Acoustic",
        role="Side-Channel Cryptanalyst",
        flavor='"Harmonic resonance frequencies decode physical chassis vibrations."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{PURPLE} {STAR}"),
        protocol_name="Resonance Sensor",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, gain **+$1 cash** per distinct cube color "
            "present in the Tower Exit Tray this round ({RED}, {BLUE}, {GREEN}, {BLACK}; max **+$4**)."
        ),
    ),
    WhiteHatDossierSpec(
        code="SPOOK",
        name="The Spook",
        role="Covert Intelligence Specialist",
        flavor='"Scorched-earth protocols ensure zero forensic recovery."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{PURPLE} {STAR}"),
        protocol_name="Burn Notice",
        protocol_timing="P3: INCOME",
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
        flavor='"Payload injection executes before memory boundaries establish."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{PURPLE} {STAR}"),
        protocol_name="Arbitrary Code Execution",
        protocol_timing="P1: STEP 4 ROLLING",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, turn **1 other rolled die** in your active "
            "pool to **any legal non-Star face of that die's color**."
        ),
    ),
    WhiteHatDossierSpec(
        code="CIPHER",
        name="The Cipher",
        role="Distributed Ledger Architect",
        flavor='"Parity calculations balance zero-knowledge proofs flawlessly."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{PURPLE} {STAR}"),
        protocol_name="Algorithmic Parity",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, gain an additional **+$2 cash income** "
            "AND **+1 {RESEARCH} Research Token** during Phase 3: Income."
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
        cost_str="Starter (3, max 5)",
        faces=("Block 1 Any", "Block 1 Any", "+$1 & +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+1 {RESEARCH}"),
        notes="Start: 3 Gray + 1 Purple in Ready for Release; up to 5 Gray via Defense Grid / Release Level 1. Faces 4-5 are Choices (/): declare in Phase 1 Step 5.",
    ),
    DieSpec(
        color_key="white",
        title="WHITE",
        subtitle="Contractor",
        cost_str="$1 / $2 / $3",
        faces=("Block 1 Any", "Block 1 Any", "Block 1 Any", "+$1", "Glitch", "Glitch"),
        notes="Temp hire (max 3/rd). +$1 face pays in Phase 3: Income. Returns to supply after Phase 4. Can sacrifice vs {GREEN} Malware.",
    ),
    DieSpec(
        color_key="red",
        title="RED",
        subtitle="FinSec",
        cost_str="$4–$5 (by Variant)",
        faces=("Block 1 {RED}", "+$2", "+$2", "+$2", "Glitch", "{RED} {STAR}"),
        notes="FinSec revenue & defense. Face 5 Glitch, Face 6 Red {STAR}.",
    ),
    DieSpec(
        color_key="blue",
        title="BLUE",
        subtitle="Firewall",
        cost_str="$4–$6 (by Variant)",
        faces=("Block 1 {BLUE}", "+1 {RESEARCH}", "+$1", "Block 1 {BLUE} / +1 {RESEARCH}", "Glitch", "{BLUE} {STAR}"),
        notes="Spyware defense & research hybrid. Face 5 Glitch, Face 6 Blue {STAR}.",
    ),
    DieSpec(
        color_key="green",
        title="GREEN",
        subtitle="Antivirus",
        cost_str="$4–$5 (by Variant)",
        faces=("Block 1 {GREEN}", "+1 {RESEARCH}", "+2 {RESEARCH}", "+1 {RESEARCH} / +$1", "Glitch", "{GREEN} {STAR}"),
        notes="Malware defense & research engine. Face 5 Glitch, Face 6 Green {STAR}.",
    ),
    DieSpec(
        color_key="yellow",
        title="YELLOW",
        subtitle="Commercial AI",
        cost_str="$5–$6 (by Variant)",
        faces=("+$3", "+$2", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{YELLOW} {STAR}"),
        notes="Commercial AI revenue. Face 5 Glitch, Face 6 Yellow {STAR}.",
    ),
    DieSpec(
        color_key="purple",
        title="PURPLE",
        subtitle="Specialist AI",
        cost_str="Not sold (Patents L3)",
        faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "Glitch", "{PURPLE} {STAR}"),
        notes="Not purchasable. 2nd Purple die only from Cryptographic Patents Level 3. Face 5 Glitch, Face 6 Purple {STAR} Signature Protocol.",
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
    # RED (R1-R3)
    VariantCardSpec(
        "R1", "red", "RED // FINSEC", "$5",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} Glitch  |  {PIP6} {STAR}",
        "Ransom Insurance", "P4 DEFENSE + P3 INCOME",
        "**Block 1 {RED} Red** in Phase 4 **AND** gain **+$2** in Phase 3: Income.",
        "FinSec Baseline: Blocks Red Ransom & yields cash.",
    ),
    VariantCardSpec(
        "R2", "red", "RED // FINSEC", "$5",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} Glitch  |  {PIP6} {STAR}",
        "Threat Bounty", "P4 DEFENSE + P4 BONUS",
        "**Block 2 {RED} Red**; if you take **0 unblocked Red** damage in Phase 4, gain **+$2** *(die must still be In Production)*.",
        "Threat Bounty: Blocks 2 Red; bonus if 0 unblocked.",
    ),
    VariantCardSpec(
        "R3", "red", "RED // FINSEC", "$4",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} Glitch  |  {PIP6} {STAR}",
        "Short Squeeze", "P3 INCOME + P4 SURGE",
        "Gain **+$3** in Phase 3; **+$1** more in Phase 4 if **3+ {RED} Red** cubes exit the tower *(die must still be In Production)*.",
        "Short Squeeze: Revenue scales with 3+ Red cubes.",
    ),
    # BLUE (B1-B3)
    VariantCardSpec(
        "B1", "blue", "BLUE // FIREWALL", "$5",
        "{PIP1} 1{BLUE} | {PIP2} +1{RESEARCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{RESEARCH} | {PIP5} Glitch | {PIP6} {STAR}",
        "Honeypot Telemetry", "P4 DEFENSE + P4 BONUS",
        "**Block 2 {BLUE} Blue**; if **1+ {BLUE} Blue** cubes exit and you take **0 Blue** damage in Phase 4, gain **+$2** *(die must still be In Production)*.",
        "Honeypot: Blocks 2 Blue; +$2 if 0 unblocked.",
    ),
    VariantCardSpec(
        "B2", "blue", "BLUE // FIREWALL", "$6",
        "{PIP1} 1{BLUE} | {PIP2} +1{RESEARCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{RESEARCH} | {PIP5} Glitch | {PIP6} {STAR}",
        "Deep R&D Vault", "P4 DEF -OR- P6 OPS",
        "**Block 1 {BLUE} Blue** in Phase 4, **OR** leave unassigned to pay **$4** in Phase 6 for **+1 Secret**.",
        "R&D Vault: Blocks Blue OR pay $4 in P6 for Secret.",
    ),
    VariantCardSpec(
        "B3", "blue", "BLUE // FIREWALL", "$4",
        "{PIP1} 1{BLUE} | {PIP2} +1{RESEARCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{RESEARCH} | {PIP5} Glitch | {PIP6} {STAR}",
        "Air-Gapped Backup", "P4 DEFENSE + P3 INCOME",
        "**Block 1 {BLUE} Blue** in Phase 4 **AND** move **1 die from Glitched to Scanned** in Phase 3: Income.",
        "Air-Gapped: Blocks 1 Blue & moves 1 die to Scanned.",
    ),
    # GREEN (G1-G3)
    VariantCardSpec(
        "G1", "green", "GREEN // ANTIVIRUS", "$5",
        "{PIP1} 1{GREEN} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}", "{PIP4} 1{RESEARCH}/$1 | {PIP5} Glitch | {PIP6} {STAR}",
        "Self-Healing Kernel", "P4 DEFENSE + P3 INCOME",
        "**Block 2 {GREEN} Green** in Phase 4 **AND** gain **+1 {RESEARCH}** in Phase 3: Income.",
        "Kernel: Blocks 2 Green & yields Research.",
    ),
    VariantCardSpec(
        "G2", "green", "GREEN // ANTIVIRUS", "$4",
        "{PIP1} 1{GREEN} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}", "{PIP4} 1{RESEARCH}/$1 | {PIP5} Glitch | {PIP6} {STAR}",
        "Universal Sandbox", "P4 DEFENSE + P3 INCOME",
        "**Block 1 Any** color in Phase 4 **AND** gain **+1 {RESEARCH}** in Phase 3: Income.",
        "Sandbox: Blocks 1 Any color & yields Research.",
    ),
    VariantCardSpec(
        "G3", "green", "GREEN // ANTIVIRUS", "$4",
        "{PIP1} 1{GREEN} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}", "{PIP4} 1{RESEARCH}/$1 | {PIP5} Glitch | {PIP6} {STAR}",
        "Live Reboot", "P3 INCOME OUTPUT",
        "Gain **+2 {RESEARCH}** and **+$1** in Phase 3: Income.",
        "Live Reboot: High-yield immediate income.",
    ),
    # YELLOW (Y1-Y3)
    VariantCardSpec(
        "Y1", "yellow", "YELLOW // COMM. AI", "$6",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{RESEARCH} | {PIP5} Glitch",
        "Algorithmic Trading", "P3 INCOME -OR- P6 OPS",
        "Gain **+$4** in Phase 3: Income, **OR** pay **$2** in Phase 6: Operations to gain **+1 Corporate Secret**.",
        "Trading: High cash revenue OR Secret buy.",
    ),
    VariantCardSpec(
        "Y2", "yellow", "YELLOW // COMM. AI", "$5",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{RESEARCH} | {PIP5} Glitch",
        "Cloud Monopoly", "P3 SCALING REVENUE",
        "Gain **+$2** in Phase 3, plus **+$1 per different colored** module die you own (**max +$5** total).",
        "Monopoly: Scales revenue per owned color.",
    ),
    VariantCardSpec(
        "Y3", "yellow", "YELLOW // COMM. AI", "$5",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{RESEARCH} | {PIP5} Glitch",
        "Proprietary Training", "P3 SECRET + GLITCH",
        "Gain **+1 Corporate Secret** in Phase 3, then immediately move **this die to the Glitched Box** (before Phase 4).",
        "Training: Quick Secret gain, then die glitches.",
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
        banner_text="**Aggressive Infiltration:** Space 4 glitches 1 die & adds cubes.\nFinal space triggers Singularity!",
        spaces=(
            VersionTrackSpaceSpec(1, "+1 {RED} 1 {BLUE} 1 {GREEN}"),
            VersionTrackSpaceSpec(2, "Lose $3 & 1 {RESEARCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} +1 {BLUE}"),
            VersionTrackSpaceSpec(4, "All glitch 1 die\n+1 {BLUE} 1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Return 1\nColored Die"),
            VersionTrackSpaceSpec(6, "**SINGULARITY!**", is_singularity=True),
        ),
    ),
    VersionTileSpec(
        version="v3.0",
        name="Corrupted Kernel",
        profile="SINGULARITY",
        banner_text="**Overclocked Surge:** Space 1 glitches 1 die & adds cubes.\nSpace 4 leaks 1 Secret.",
        spaces=(
            VersionTrackSpaceSpec(1, "Glitch 1 Die\n+1 {RED} 1 {BLUE}"),
            VersionTrackSpaceSpec(2, "Lose $3 & 1 {RESEARCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} +1 {GREEN}"),
            VersionTrackSpaceSpec(4, "Lose 1 Secret\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Return 1\nColored Die"),
            VersionTrackSpaceSpec(6, "**SINGULARITY!**\nLose 1 Secret", is_singularity=True),
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="Ransomware-as-a-Service",
        profile="ESCALATION",
        banner_text="**Financial Extortion:** Space 3 drains cash & adds Red cube.\nSpace 5 upgrades to v3.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "All Lose $2"),
            VersionTrackSpaceSpec(2, "+1 {RED} +1 {GREEN}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "All Lose $2\n& Add 1 {RED}"),
            VersionTrackSpaceSpec(4, "Lose $3 & 1 {RESEARCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "UPGRADE v3.0\n+1 {RED}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="Polymorphic Worm",
        profile="ESCALATION",
        banner_text="**Memory Infiltration:** Space 3 glitches 1 die & adds Green cube.\nSpace 5 upgrades to v3.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "Lose 2 {RESEARCH}"),
            VersionTrackSpaceSpec(2, "+2 {GREEN}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "All glitch 1 die\n& Add 1 {GREEN}"),
            VersionTrackSpaceSpec(4, "Glitch 1 Die\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "UPGRADE v3.0\n+1 {RED}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Script Kiddie",
        profile="INITIAL",
        banner_text="**Setup Payload:** Add 1 {RED} 1 {BLUE} 1 {GREEN} to Staging Cup.\nSpace 4 upgrades to v2.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "+1 {RED}"),
            VersionTrackSpaceSpec(2, "All Lose $2\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Lose 1 {RESEARCH}"),
            VersionTrackSpaceSpec(4, "UPGRADE v2.0\nLose 1 {RESEARCH}", is_milestone=True),
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Data Scraper",
        profile="INITIAL",
        banner_text="**Setup Payload:** Add 1 {RED} 2 {BLUE} to Staging Cup.\nAll players start with +$1.",
        spaces=(
            VersionTrackSpaceSpec(1, "Lose 1 {RESEARCH}"),
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
    size: float, leading: float, min_size: float = 4.2, color: Color = PALETTE["ink"],
    align: str = "left",
) -> None:
    """Render a rich paragraph, shrinking type until its last line sits above `bottom`."""
    s, ld = size, leading
    while s > min_size:
        probe = PDFPage()
        end_y = probe.rich_paragraph(x, y, w, markup, size=s, leading=ld)
        if end_y - ld <= bottom:
            break
        s -= 0.2
        ld = s * (leading / size)
    page.rich_paragraph(x, y, w, markup, size=s, leading=ld, color=color, align=align)


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
    _fit_paragraph(page, x + 7.0, fy + 6.0, w - 14.0, f"*{comp.flavor}*", fy + fh - 2.0, size=5.0, leading=6.0, min_size=4.2, color=PALETTE["ink_soft"], align="center")

    # Hardware & bonus strip
    hw_y, hw_h = y + 45.0, 16.0
    page.rect(x + 4.0, hw_y, w - 8.0, hw_h, stroke=PALETTE["ink"], fill=PALETTE["purple_light"], line_width=0.5)
    page.rich_line(x + w / 2.0, hw_y + 6.8, f"**{comp.hardware_summary}**", size=4.9, color=PALETTE["ink"], align="center")
    page.rich_line(x + w / 2.0, hw_y + 13.4, f"**{comp.starting_bonus}**", size=4.6, color=PALETTE["purple"], align="center")

    # Institutional Override box
    o_y = y + 63.0
    o_h = h - 66.0
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
    _fit_paragraph(page, x + 7.0, o_y + 18.5, w - 14.0, comp.override_desc, ty - 1.5, size=5.3, leading=6.7, min_size=4.3)

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
    page.text(x + w - 7.0, ty + 9.5, "Unused charge forfeits on upgrade.", font="italic", size=4.3, color=PALETTE["muted"], align="right")


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
    _fit_paragraph(page, x + 7.0, fy + 6.0, w - 14.0, f"*{white_hat.flavor}*", fy + fh - 2.0, size=5.0, leading=6.0, min_size=4.2, color=PALETTE["ink_soft"], align="center")

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
    _fit_paragraph(page, x + 7.0, s_y + 18.5, w - 14.0, white_hat.protocol_desc, note_y - 6.5, size=5.3, leading=6.7, min_size=4.3)
    page.rich_line(x + w / 2.0, note_y, "*Repeatable: once per Purple {STAR} die (Phase 3: die must still be In Production).*", size=4.3, color=PALETTE["purple"], align="center")

    # Personal Reserve strip (the Purple Specialist Die rests on the card itself)
    r_y = y + h - r_h - 3.0
    page.rect(x + 4.0, r_y, w - 8.0, r_h, stroke=PALETTE["purple"], fill=PALETTE["paper_tint"], line_width=0.7)
    ds = r_h - 4.0
    page.rounded_rect(x + 6.0, r_y + 2.0, ds + 14.0, ds, r=2.5, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.6)
    page.text(x + 13.0 + ds / 2.0, r_y + 11.0, "RESERVE DIE", font="mono_bold", size=4.4, color=PALETTE["purple"], align="center")
    page.text(x + 13.0 + ds / 2.0, r_y + 22.0, "PATENTS L3", font="bold", size=5.4, color=PALETTE["ink"], align="center")
    page.rich_paragraph(
        x + ds + 26.0, r_y + 7.5, w - ds - 32.0,
        "**PERSONAL RESERVE** (2nd Purple die; not purchasable)\n"
        "Faces 1-2: Block 1 Any | 3: +$2 | 4: +$1 & +1{RESEARCH}\n"
        "5: Glitch | 6: {STAR} Signature Protocol",
        size=4.6, leading=6.6, color=PALETTE["ink_soft"],
    )


TRACK_STEP_COSTS = (None, 1, 2, 2, 3)  # {RESEARCH} to reach L1..L4 (RULES.md v0.35.0)


def _draw_track_cells(page: PDFPage, cells: Sequence[Tuple[float, float, float, float]],
                      levels: Sequence[Tuple[str, str]], accent: Color, compact: bool = False) -> None:
    """Draw a 5-level (L0-L4) track. levels[i] = (main value, effect text).

    L1 and L3 cells get a solid accent header (one-time reward on reaching that level).
    compact=True puts the level label in a left tab (for short, wide rows).
    """
    for lv, ((cx, cy, cw, ch), (main, effect)) in enumerate(zip(cells, levels)):
        once = lv in (1, 3)
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
        if main:
            page.rich_line(cx + cw / 2.0, cy + 17.5, f"**{main}**", size=5.6, color=PALETTE["ink"], align="center")
            body_top = cy + 20.0
        if effect:
            _fit_paragraph(page, cx + 2.5, body_top + 4.0, cw - 5.0, effect, cy + ch - 1.5,
                           size=4.6, leading=5.6, min_size=3.4, color=PALETTE["purple"] if once else PALETTE["ink_soft"], align="center")


def _cells_row(x: float, y: float, w: float, h: float, gap: float = 2.0) -> List[Tuple[float, float, float, float]]:
    cw = (w - 4 * gap) / 5.0
    return [(x + i * (cw + gap), y, cw, h) for i in range(5)]


def _cells_col(x: float, y: float, w: float, h: float, gap: float = 2.0) -> List[Tuple[float, float, float, float]]:
    ch = (h - 4 * gap) / 5.0
    return [(x, y + i * (ch + gap), w, ch) for i in range(5)]


DEFENSE_LEVELS = [
    ("Cap 2", "Color & Any Shields"),
    ("Cap 2", "+1 Gray Legacy die -> Ready"),
    ("Cap 3", ""),
    ("Cap 3", "+1 {SECRET} Corporate Secret"),
    ("Cap 4", "+$1 per Attack Cube blocked in P4 (max $3), after damage"),
]
TRIAGE_LEVELS = [
    ("2 dice", ""),
    ("2 dice", "+2 {WHITE} White Contractors (next round)"),
    ("3 dice", ""),
    ("3 dice", "Pay $3: swap 1 Gray for 1 Market colored die"),
    ("4 dice", "+1 {RESEARCH} per die moved beyond the 2nd"),
]
RELEASE_LEVELS = [
    ("4 dice", ""),
    ("4 dice", "+1 Gray Legacy die -> Ready"),
    ("5 dice", ""),
    ("5 dice", "+1 {SECRET} Corporate Secret"),
    ("6 dice", "+1 free reroll in P1 Step 4"),
]
PATENT_LEVELS = [
    ("2{RESEARCH} -> 1 Secret", ""),
    ("2{RESEARCH} -> 1 Secret", "+$3"),
    ("3{RESEARCH} -> 2 Secrets", ""),
    ("3{RESEARCH} -> 2 Secrets", "+2nd Purple die (Reserve)"),
    ("1{RESEARCH} -> 1 Secret", ""),
]



def _draw_empty_company_card_slot(page: PDFPage, x: float, y: float, w: float, h: float, idx: int = 1) -> None:
    """Render an empty dock outline sized exactly to a Client Company card."""
    page.rect(x, y, w, h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.0, dash=(4.0, 2.5))
    page.corner_ticks(x + 3.0, y + 3.0, w - 6.0, h - 6.0, size=6.0, color=PALETTE["ink_soft"])
    page.text(x + w / 2.0, y + 22.0, "CLIENT COMPANY CARD", font="bold", size=8.0, color=PALETTE["ink"], align="center")
    page.text(x + w / 2.0, y + 31.0, f"PLACE CARD HERE  //  DOCK SIZE {w / 72.0:.2f}\" x {h / 72.0:.2f}\"", font="mono_bold", size=5.0, color=PALETTE["ink_soft"], align="center")
    by, bw, bh = y + 40.0, w - 20.0, 58.0
    page.rounded_rect(x + 10.0, by, bw, bh, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
    rules_text = (
        "**1. Contract:** Deal 1 Client Company card at setup.\n"
        "**2. Override:** 1 override per SETEC Version (**v1.0**, **v2.0**, **v3.0**).\n"
        "**3. Round-Start Switch:** Override stays usable in Phases 3-6 of the upgrade round; forfeits at next round start.\n"
        "**4. Spillover:** Excess cubes mark the next track immediately."
    )
    page.rich_paragraph(x + 14.0, by + 9.0, bw - 8.0, rules_text, size=5.0, leading=6.8, color=PALETTE["muted"])


def _draw_empty_white_hat_slot(page: PDFPage, x: float, y: float, w: float, h: float, idx: int = 1) -> None:
    """Render an empty dock outline sized exactly to a White Hat Dossier card."""
    page.rect(x, y, w, h, stroke=PALETTE["purple"], fill=PALETTE["paper_tint"], line_width=1.0, dash=(4.0, 2.5))
    page.corner_ticks(x + 3.0, y + 3.0, w - 6.0, h - 6.0, size=6.0, color=PALETTE["purple"])
    page.text(x + w / 2.0, y + 22.0, "WHITE HAT DOSSIER", font="bold", size=8.0, color=PALETTE["purple"], align="center")
    page.text(x + w / 2.0, y + 31.0, f"PLACE CARD HERE  //  DOCK SIZE {w / 72.0:.2f}\" x {h / 72.0:.2f}\"", font="mono_bold", size=5.0, color=PALETTE["purple"], align="center")
    by, bw, bh = y + 40.0, w - 20.0, 50.0
    page.rounded_rect(x + 10.0, by, bw, bh, r=2.5, stroke=PALETTE["purple_light"], fill=PALETTE["white"], line_width=0.6)
    wh_rules_text = (
        "**1. Operative:** Deal 1 White Hat Dossier at setup.\n"
        "**2. Personal Reserve:** Your Purple Specialist Die rests on the Dossier's reserve strip.\n"
        "**3. Purple Star ({STAR}):** Each Purple {STAR} die triggers the Signature Protocol once."
    )
    page.rich_paragraph(x + 14.0, by + 9.0, bw - 8.0, wh_rules_text, size=5.0, leading=6.8, color=PALETTE["muted"])


def _draw_chip_well(
    page: PDFPage, x: float, y: float, w: float, h: float, title: str, title_color: Color,
    border: Color, tint: Color, sub_top: str, sub_bottom: str, icon: str,
) -> None:
    """A labelled box holding a 40 mm circular well for a standard 39 mm poker chip."""
    page.rect(x, y, w, h, stroke=border, fill=PALETTE["white"], line_width=1.0)
    page.rect(x, y, w, 11.0, stroke=border, fill=tint, line_width=0.7)
    page.rich_line(x + w / 2.0, y + 8.0, title, size=5.8, color=title_color, align="center")
    r = POKER_CHIP_WELL_D / 2.0
    cx, cy = x + w / 2.0, y + 11.0 + (h - 11.0) / 2.0
    page.circle(cx, cy, r, stroke=border, fill=PALETTE["paper_tint"], line_width=0.8, dash=(3.0, 2.0))
    page.circle(cx, cy, r - 7.0, stroke=PALETTE["guide"], fill=None, line_width=0.4)
    if icon == "secret":
        page.draw_secret_icon(cx, cy - 8.0, 22.0, color=PALETTE["guide"])
    elif icon == "research":
        page.draw_research_icon(cx, cy - 8.0, 20.0, color=PALETTE["guide"])
    else:
        page.text(cx, cy - 1.0, "$", font="bold", size=26.0, color=PALETTE["guide"], align="center")
    page.rich_line(cx, cy + 16.0, sub_top, size=4.9, color=PALETTE["ink_soft"], align="center")
    page.text(cx, cy + 23.5, sub_bottom, font="regular", size=4.4, color=PALETTE["muted"], align="center")
    page.text(cx, cy + r - 9.0, "POKER CHIP (39 mm)", font="mono", size=3.8, color=PALETTE["muted"], align="center")


def render_player_board(
    page: PDFPage,
    idx: int,
    comp: Optional[CompanyCardSpec] = None,
    white_hat: Optional[WhiteHatDossierSpec] = None,
) -> None:
    draw_board_outer_frame(
        page,
        left_tag=f"TOO MANY SECRETS // COMPANY TERMINAL MAT [TERM-0{idx}/4]",
        right_tag="PNP PROTOTYPE v0.35.0 // US LETTER",
    )

    # -------------------------------------------------------------------------
    # LEFT COLUMN: CORPORATE HQ (x = 32..264, w = 232)
    # -------------------------------------------------------------------------
    lx, lw = 32.0, CARD_W

    # 1. Client Company Card dock -- exact card size (y = 30..170)
    if comp is not None:
        _draw_company_card(page, lx, 30.0, lw, COMPANY_CARD_H, comp, is_dock=True)
    else:
        _draw_empty_company_card_slot(page, lx, 30.0, lw, COMPANY_CARD_H, idx=idx)

    # 2. White Hat Dossier dock -- exact card size, Personal Reserve on card (y = 174..320)
    wh_y = 30.0 + COMPANY_CARD_H + 4.0
    if white_hat is not None:
        _draw_white_hat_card(page, lx, wh_y, lw, WHITE_HAT_CARD_H, white_hat, is_dock=True)
    else:
        _draw_empty_white_hat_slot(page, lx, wh_y, lw, WHITE_HAT_CARD_H, idx=idx)

    # 3. Poker-chip token wells + Patents (2 x 2 grid, y = 324..576)
    cell_w = (lw - 4.0) / 2.0          # 114 pt
    cell_h = 124.0
    g_y1 = wh_y + WHITE_HAT_CARD_H + 4.0
    g_y2 = g_y1 + cell_h + 4.0
    g_x2 = lx + cell_w + 4.0

    _draw_chip_well(
        page, lx, g_y1, cell_w, cell_h,
        "{SECRET} **CORPORATE SECRETS (VP)**", PALETTE["blue"], PALETTE["blue"], PALETTE["blue_light"],
        "Start: **8** (all companies)", "Uncapped | 1 Secret = 1 VP", "secret",
    )
    _draw_chip_well(
        page, g_x2, g_y1, cell_w, cell_h,
        "**MONEY ($)**", PALETTE["ink"], PALETTE["ink"], PALETTE["panel_tint"],
        "Start: **$6** (all companies)", "Min $0 | Tiebreaker #1", "money",
    )
    _draw_chip_well(
        page, lx, g_y2, cell_w, cell_h,
        "{RESEARCH} **RESEARCH** (UNCAPPED)", PALETTE["purple"], PALETTE["purple"], PALETTE["purple_light"],
        "Start: **0** (all companies)", "Spend in Phase 6", "research",
    )

    # Compact Cryptographic Patents Track
    px0, py0 = g_x2, g_y2
    page.rect(px0, py0, cell_w, cell_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(px0, py0, cell_w, 11.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
    page.rich_line(px0 + cell_w / 2.0, py0 + 8.0, "{RESEARCH} **CRYPTOGRAPHIC PATENTS** (P6)", size=5.6, color=PALETTE["ink"], align="center")
    pt_cells = _cells_col(px0 + 3.0, py0 + 13.0, cell_w - 6.0, cell_h - 15.0, gap=1.5)
    _draw_track_cells(page, pt_cells, PATENT_LEVELS, PALETTE["purple"], compact=True)

    # -------------------------------------------------------------------------
    # MAIN COLUMN: CI/CD PIPELINE & DEFENSE GRID (x = 268..756, w = 488)
    # Clockwise CI/CD Pipeline Flow:
    # Ready (top) -> In Production (mid) -> Glitched (bot-right)
    # -> Triage Track (bot-mid) -> Scanned (bot-left) -> Release Bandwidth column (left) -> Ready (top)
    # -------------------------------------------------------------------------
    rx, rw = 268.0, 488.0

    # =========================================================================
    # 1. READY FOR RELEASE (Top Box: x = 268..756, y = 30..106, h = 76)
    # =========================================================================
    r1_y, r1_h = 30.0, 76.0
    page.rect(rx, r1_y, rw, r1_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, r1_y, rw, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(rx + 8.0, r1_y + 11.0, "ZONE 1: READY FOR RELEASE (ACTIVE STAGING / ROLLING POOL)", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_line(rx + rw - 8.0, r1_y + 11.0, "Start: **3 Gray Legacy + 1 Purple Specialist Die (Rolls in Round 1)**", size=5.4, color=PALETTE["ink_soft"], align="right")

    # Staging instructions & visual dice slots
    page.text(rx + 8.0, r1_y + 28.0, "Phase 1: Roll Ready + Hired Contractors ($1/$2/$3). Max 2 Free Rerolls (Glitched dice cannot be rerolled).", font="regular", size=6.2, color=PALETTE["ink_soft"])
    page.text(rx + 8.0, r1_y + 39.0, "Assign surviving dice to In Production (Color & Any Shields up to Defense Capacity; remainder to Income).", font="regular", size=6.0, color=PALETTE["muted"])

    # Directional Arrows on Ready for Release
    # Entry from Release Bandwidth column at left
    page.text(rx + 8.0, r1_y + 58.0, "^ ENTERS HERE: PHASE 5 SCANNED GRADUATION (<= RELEASE BANDWIDTH 4/5/6), MAGNETIC SPLICE  |  PHASE 6 PURCHASES & NEW TRACK DICE", font="mono_bold", size=5.3, color=PALETTE["blue"])

    # =========================================================================
    # 2. VERTICAL RELEASE TRACK & RELEASE BANDWIDTH COLUMN (Left Column: x = 268..342, y = 110..442, h = 332)
    # =========================================================================
    vx, vw = 268.0, 74.0
    vy, vh = 110.0, 332.0
    page.rect(vx, vy, vw, vh, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=1.0)

    # Header strip
    page.rect(vx, vy, vw, 24.0, stroke=PALETTE["blue"], fill=PALETTE["blue"], line_width=0.7)
    rb_label = "^ RELEASE BANDWIDTH ^"
    rb_size = min(5.8, 5.8 * (vw - 6.0) / max(1.0, measure_text(rb_label, font="bold", size=5.8)))
    page.text(vx + vw / 2.0, vy + 9.5, rb_label, font="bold", size=rb_size, color=PALETTE["white"], align="center")
    page.text(vx + vw / 2.0, vy + 19.0, "SCANNED -> READY (P5)", font="mono_bold", size=4.8, color=PALETTE["white"], align="center")

    # Upward graduation flow arrows
    page.text(vx + vw / 2.0, vy + 38.0, "^ ^ ^", font="bold", size=8.0, color=PALETTE["blue"], align="center")
    page.text(vx + vw / 2.0, vy + 48.0, "GRADUATION", font="mono_bold", size=5.2, color=PALETTE["ink"], align="center")
    page.text(vx + vw / 2.0, vy + 56.0, "THROUGHPUT", font="mono_bold", size=5.0, color=PALETTE["ink_soft"], align="center")

    # 5-level Release Track stacked vertically along the column
    _draw_track_cells(page, _cells_col(vx + 3.0, vy + 62.0, vw - 6.0, vh - 65.0, gap=3.0), RELEASE_LEVELS, PALETTE["blue"])

    # =========================================================================
    # 3. ZONE 2: IN PRODUCTION (Middle-Right Box: x = 346..756, y = 110..442, h = 332)
    # =========================================================================
    px, pw = 346.0, 410.0
    py, ph = 110.0, 332.0
    page.rect(px, py, pw, ph, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(px, py, pw, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(px + 8.0, py + 11.0, "**ZONE 2: IN PRODUCTION (DEPLOYED MODULES)**", size=7.5, color=PALETTE["ink"])
    page.text(px + pw - 8.0, py + 11.0, "MOVES TO SCANNED IN PHASE 5", font="mono_bold", size=6.0, color=PALETTE["ink_soft"], align="right")

    # --- 3A: Income Bays (Money, Research, Special) (y = 130..222, h = 92) ---
    page.rect(px + 6.0, py + 20.0, pw - 12.0, 92.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
    page.rect(px + 6.0, py + 20.0, pw - 12.0, 13.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_line(px + 10.0, py + 29.0, "**INCOME BAYS**", size=6.5, color=PALETTE["ink"])
    page.text(px + pw - 16.0, py + 29.0, "PHASE 3: INCOME", font="mono_bold", size=5.2, color=PALETTE["muted"], align="right")

    income_bays = [
        "MONEY ($)",
        "RESEARCH ({RESEARCH})",
        "SPECIAL ({STAR})",
    ]
    ib_w = (pw - 24.0) / 3.0
    for ib_i, ib_title in enumerate(income_bays):
        ib_x = px + 9.0 + ib_i * (ib_w + 3.0)
        page.rounded_rect(ib_x, py + 36.0, ib_w - 3.0, 72.0, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6)
        page.rich_line(ib_x + (ib_w - 3.0) / 2.0, py + 52.0, f"**{ib_title}**", size=7.2, color=PALETTE["ink"], align="center")

    # --- 3B: Defense Grid (Color & Any Shields) (y = 226..358, h = 132) ---
    page.rect(px + 6.0, py + 116.0, pw - 12.0, 134.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.85)
    page.rect(px + 6.0, py + 116.0, pw - 12.0, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(px + 10.0, py + 126.0, "**DEFENSE GRID** (Color & Any Shields -- Committed up to Defense Capacity)", size=6.8, color=PALETTE["ink"])
    page.text(px + pw - 16.0, py + 126.0, "DEFENSE CAPACITY ENFORCED", font="mono_bold", size=5.4, color=PALETTE["ink_soft"], align="right")

    # Single unified box for defense dice
    d_box_x = px + 9.0
    d_box_w = pw - 18.0
    page.rounded_rect(d_box_x, py + 133.0, d_box_w, 114.0, r=2.5, stroke=PALETTE["border"], fill=PALETTE["white"], line_width=0.8)
    page.rect(d_box_x, py + 133.0, d_box_w, 14.0, stroke=PALETTE["border"], fill=PALETTE["panel_tint"], line_width=0.5)
    page.rich_line(d_box_x + d_box_w / 2.0, py + 143.0, "**ACTIVE DEFENSE DICE ({RED} RED / {BLUE} BLUE / {GREEN} GREEN / ANY)**", size=6.8, color=PALETTE["ink"], align="center")

    # Threat summaries
    page.text(d_box_x + 10.0, py + 160.0, "- Red Shields block Red Ransomware (-$1 Cash per unblocked cube; flat -1 Secret on shortfall).", font="regular", size=5.8, color=PALETTE["red"])
    page.text(d_box_x + 10.0, py + 172.0, "- Blue Shields block Blue Spyware (-1 Corporate Secret per unblocked cube).", font="regular", size=5.8, color=PALETTE["blue"])
    page.text(d_box_x + 10.0, py + 184.0, "- Green Shields block Green Malware (glitches 1 die from In Production per unblocked cube; 0 effect if empty).", font="regular", size=5.8, color=PALETTE["green"])
    page.text(d_box_x + 10.0, py + 196.0, "- Any Shields flexibly block any Attack Cube color of your choice.", font="regular", size=5.8, color=PALETTE["ink_soft"])
    page.text(d_box_x + d_box_w / 2.0, py + 216.0, "Place committed defense dice here (up to current Defense Capacity). Dice absorb cleanly & remain in In Production.", font="italic", size=5.2, color=PALETTE["muted"], align="center")

    # --- 3C: Embedded Shield Upgrade Track (Bottom of In Production, y = 254..326) ---
    st_y = py + 254.0
    st_h = 72.0
    page.rect(px + 6.0, st_y, pw - 12.0, st_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.85)
    page.rect(px + 6.0, st_y, pw - 12.0, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(px + 10.0, st_y + 10.0, "{RESEARCH} **DEFENSE GRID TRACK** (Defense Capacity)", size=6.5, color=PALETTE["ink"])
    page.text(px + pw - 16.0, st_y + 10.0, "SPEND IN PHASE 6", font="mono_bold", size=5.2, color=PALETTE["purple"], align="right")

    _draw_track_cells(page, _cells_row(px + 9.0, st_y + 16.0, pw - 18.0, st_h - 18.0, gap=3.0), DEFENSE_LEVELS, PALETTE["ink"])

    # Arrow down from In Production to Glitched Box

    # =========================================================================
    # 4. ZONE 3: UNDER DEVELOPMENT (Bottom Box: x = 268..756, y = 448..580, h = 132)
    # Conveyor Triage: Glitched Box (bottom right) -> Embedded Triage Track (center) -> Scanned Box (bottom left)
    # =========================================================================
    uy, uh = 448.0, 132.0
    page.rect(rx, uy, rw, uh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, uy, rw, 15.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(rx + 8.0, uy + 10.5, "**ZONE 3: UNDER DEVELOPMENT (OFFLINE CI/CD PIPELINE)**", size=7.2, color=PALETTE["ink"])
    page.text(rx + rw - 8.0, uy + 10.5, "OFFLINE MODULES (DO NOT ROLL)", font="mono_bold", size=5.8, color=PALETTE["muted"], align="right")

    # --- 4A: Scanned Box (Bottom Left: x = 272..388, w = 116, y = 466..576, h = 110) ---
    sc_x, sc_w = rx + 4.0, 116.0
    sc_y, sc_h = uy + 18.0, uh - 22.0
    page.rect(sc_x, sc_y, sc_w, sc_h, stroke=PALETTE["blue"], fill=PALETTE["white"], line_width=0.9)
    page.rect(sc_x, sc_y, sc_w, 14.0, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=0.6)
    page.rich_line(sc_x + 6.0, sc_y + 10.0, "{BLUE} **SCANNED BOX**", size=6.8, color=PALETTE["blue"])
    page.text(sc_x + sc_w - 6.0, sc_y + 10.0, "VALIDATED", font="mono_bold", size=4.2, color=PALETTE["blue"], align="right")

    page.rich_paragraph(
        sc_x + 6.0, sc_y + 24.0, sc_w - 12.0,
        "**PHASE 5 ROUTING:**\n**In Production -> Scanned**\n**-> Ready (<= Release Bandwidth)**\n*Your choice of dice; the rest wait here. Triaged dice also land here.*",
        size=5.2, leading=6.9, color=PALETTE["ink_soft"],
    )

    page.text(sc_x + sc_w / 2.0, sc_y + sc_h - 14.0, "^ GRADUATES UP ^", font="mono_bold", size=5.5, color=PALETTE["blue"], align="center")
    page.text(sc_x + sc_w / 2.0, sc_y + sc_h - 5.0, "to Ready (Release Bandwidth: 4/5/6)", font="italic", size=4.5, color=PALETTE["ink_soft"], align="center")

    # --- 4B: Embedded Triage Upgrade Track (Center Conveyor Triage: x = 394..630, w = 236, y = 466..576, h = 110) ---
    tt_x, tt_w = rx + 124.0, 236.0
    tt_y, tt_h = uy + 18.0, uh - 22.0
    page.rect(tt_x, tt_y, tt_w, tt_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.85)
    page.rect(tt_x, tt_y, tt_w, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(tt_x + 6.0, tt_y + 10.0, "{RESEARCH} **TRIAGE TRACK (PHASE 5 STEP 4)**", size=6.2, color=PALETTE["ink"])
    page.text(tt_x + tt_w - 6.0, tt_y + 10.0, "CONVEYOR TRIAGE", font="mono_bold", size=5.2, color=PALETTE["purple"], align="right")

    # Prominent Left-Pointing Conveyor Triage Arrow Banner
    page.rect(tt_x + 4.0, tt_y + 17.0, tt_w - 8.0, 14.0, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
    page.rich_line(tt_x + (tt_w - 8.0) / 2.0 + 4.0, tt_y + 26.5, "<------ **CONVEYOR TRIAGE: GLITCHED TO SCANNED** ------<", size=5.6, color=PALETTE["purple"], align="center")

    _draw_track_cells(page, _cells_row(tt_x + 3.0, tt_y + 33.0, tt_w - 6.0, tt_h - 44.0, gap=2.0), TRIAGE_LEVELS, PALETTE["purple"])
    page.text(tt_x + tt_w / 2.0, tt_y + tt_h - 4.0, "Throughput limit: excess glitched dice remain quarantined in Glitched Box.", font="italic", size=4.4, color=PALETTE["muted"], align="center")

    # --- 4C: Glitched Box (Bottom Right: x = 636..752, w = 116, y = 466..576, h = 110) ---
    gl_x, gl_w = rx + 364.0, 116.0
    gl_y, gl_h = uy + 18.0, uh - 22.0
    page.rect(gl_x, gl_y, gl_w, gl_h, stroke=PALETTE["red"], fill=PALETTE["white"], line_width=0.9)
    page.rect(gl_x, gl_y, gl_w, 14.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.6)
    page.rich_line(gl_x + 6.0, gl_y + 10.0, "{RED} **GLITCHED BOX**", size=6.8, color=PALETTE["red"])
    page.text(gl_x + gl_w - 6.0, gl_y + 10.0, "QUARANTINE", font="mono_bold", size=4.2, color=PALETTE["red"], align="right")

    page.rich_paragraph(
        gl_x + 6.0, gl_y + 24.0, gl_w - 12.0,
        "Quarantined modules (Phase 1 glitches, Phase 2 corruption, Phase 4 Green malware).",
        size=5.2, leading=6.8, color=PALETTE["ink_soft"],
    )

    page.text(gl_x + gl_w / 2.0, gl_y + gl_h - 14.0, "< SHIFTS LEFT <", font="mono_bold", size=5.5, color=PALETTE["red"], align="center")
    page.text(gl_x + gl_w / 2.0, gl_y + gl_h - 5.0, "to Scanned (Triage Bandwidth: 2/3/4)", font="italic", size=4.5, color=PALETTE["ink_soft"], align="center")


def render_company_cards_page(page: PDFPage) -> None:
    """Render all 6 Client Company Cards on a single US Letter print-and-cut sheet."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // 6x CLIENT COMPANY CARDS [PAGE 5/6]",
        right_tag="PNP PROTOTYPE v0.35.0 // US LETTER",
    )

    page.text(
        396.0, 35.0,
        "6x CLIENT COMPANY CARDS -- CUT ALONG TICKS -- PRINTED AT EXACT MAT DOCK SIZE (3.22\" x 1.94\")",
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
        "**1. Contract Assignment:** At setup, each player is dealt 1 Client Company card (or introductory preset). Place the card inside the matching dock outline on the Company Terminal Mat.\n"
        "**2. Once-per-Version Lifecycle:** Each company provides 1 Institutional Override per SETEC Version (**v1.0**, **v2.0**, and **v3.0**). Mark the checkbox upon activation.\n"
        "**3. Version Transition Timing:** When SETEC's corruption track fills in Phase 2: Compiler Drop & Corruption, the active version remains current for the rest of the round. Defensive and operational overrides remain usable through Phases 3-6. Excess {BLACK} cubes immediately **spill over** onto the next track.\n"
        "**4. Round-Start Switch & Unlock:** At the start of the next round (in Phase 1 Step 1), unspent overrides from the old version forfeit, and the new version's override unlocks to Available."
    )
    page.rich_paragraph(rx + 10.0, ry + 25.0, rw - 20.0, rules_text, size=6.4, leading=8.6, color=PALETTE["ink"])


def render_white_hat_dossiers_page(page: PDFPage) -> None:
    """Render all 6 White Hat Dossier Cards on a single US Letter print-and-cut sheet."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // 6x WHITE HAT DOSSIER CARDS [PAGE 6/6]",
        right_tag="PNP PROTOTYPE v0.35.0 // US LETTER",
    )

    page.text(
        396.0, 35.0,
        "6x WHITE HAT DOSSIER CARDS -- CUT ALONG TICKS -- PRINTED AT EXACT MAT DOCK SIZE (3.22\" x 2.03\")",
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
        "**1. Operative Assignment:** At setup, each player is dealt 1 White Hat Dossier card (or introductory preset). Place the card inside the matching dock outline on the Company Terminal Mat.\n"
        "**2. Personal Reserve (1 Purple Die):** Your 2nd Purple Specialist Die waits on the Personal Reserve strip. Purple dice are **not purchasable**: it moves to Ready for Release only when your Cryptographic Patents Track reaches **Level 3**. A Purple die lost to an effect is not replaced.\n"
        "**3. Standardized Faces 1-5:** All Purple Specialist dice feature: **Faces 1-2:** `Block 1 Any`, **Face 3:** `+$2`, **Face 4:** `+$1 & +1 {RESEARCH}`, **Face 5:** `Glitch`.\n"
        "**4. Face 6 Signature Protocol:** Rolling Face 6 ({PURPLE} {STAR}) triggers the operative's bespoke Signature Protocol. Repeatable: each Purple Star die triggers the protocol once (Phase 3: Income protocols require the die to still be In Production)."
    )
    page.rich_paragraph(rx + 10.0, ry + 25.0, rw - 20.0, wh_rules_text, size=6.4, leading=8.6, color=PALETTE["ink"])


# =============================================================================
# 2A. Central SETEC Agent Board (Matches Wireframe Page 2)
# =============================================================================

def render_agent_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // CENTRAL ROGUE AGENT & COMPILER BOARD [1/2]",
        right_tag="PNP PROTOTYPE v0.35.0 // US LETTER",
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
    slot_h = 135.0  # 1.875" (expanded now that bottom corruption protocol box is removed)
    slot_gap = (col_h - 3 * slot_h) / 2.0  # (514 - 405) / 2 = 54.5 pt

    tiers = [
        ("v3.0", "SINGULARITY TIER", "Deal 1 face-up v3.0 Tile here", "Corruption Track fills = SINGULARITY!"),
        ("v2.0", "ESCALATION TIER", "Deal 1 face-up v2.0 Tile here", "On Upgrade: Add Payload -> Staging Cup"),
        ("v1.0", "INITIAL TIER (START)", "Deal 1 face-up v1.0 Tile here", "Setup: Add Start Payload -> Staging Cup"),
    ]

    for idx, (ver_str, tier_sub, hint1, hint2) in enumerate(tiers):
        sy = col_top + idx * (slot_h + slot_gap)
        # Left Version Label (matching wireframe's v3.0 / v2.0 / v1.0 column)
        by_mid = sy + (slot_h - 36.0) / 2.0
        page.rounded_rect(38.0, by_mid, 34.0, 36.0, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"] if idx < 2 else PALETTE["ink"], line_width=1.0)
        v_col = PALETTE["ink"] if idx < 2 else PALETTE["white"]
        page.text(55.0, by_mid + 18.0, ver_str, font="bold", size=10.5, color=v_col, align="center")
        page.text(55.0, by_mid + 29.0, "START" if idx == 2 else f"TIER {3 - idx}", font="mono", size=5.5, color=PALETTE["rule"] if idx == 2 else PALETTE["muted"], align="center")

        # Upward upgrade arrow between version badges
        if idx < 2:
            ay_mid = sy + slot_h + slot_gap / 2.0
            next_by = (sy + slot_h + slot_gap) + (slot_h - 36.0) / 2.0
            page.line(55.0, by_mid + 38.0, 55.0, next_by - 4.0, stroke=PALETTE["muted"], width=0.9, dash=(2, 2))
            # Upward arrow in slot gap
            gx_mid = slot_x + slot_w / 2.0
            page.text(gx_mid, ay_mid + 3.0, "^  UPGRADE WHEN TRACK FILLS  ^", font="mono_bold", size=6.5, color=PALETTE["muted"], align="center")

        # Card Placement Slot
        page.rect(slot_x, sy, slot_w, slot_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=1.1)
        page.rect(slot_x + 4.0, sy + 4.0, slot_w - 8.0, slot_h - 8.0, stroke=PALETTE["muted"], fill=PALETTE["white"], line_width=0.6, dash=(4, 3))
        page.corner_ticks(slot_x + 4.0, sy + 4.0, slot_w - 8.0, slot_h - 8.0, size=6.0, color=PALETTE["ink_soft"])
        page.text(slot_x + slot_w / 2.0, sy + 52.0, f"{ver_str}  //  {tier_sub}", font="mono_bold", size=8.5, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 72.0, hint1, font="italic", size=8.0, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 90.0, hint2, font="regular", size=7.0, color=PALETTE["muted"], align="center")

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
        "In **Phase 2**, drop the **Staging Cup** into the **Cube Tower** (stuck cubes stay inside). Exited {BLACK} resolves now; Attack Cubes wait in the **Exit Tray** for **Phase 4**:",
        size=7.2, leading=9.8, color=PALETTE["ink_soft"],
    )

    cube_cards = [
        (
            "black",
            "{BLACK} BLACK // CORRUPTION",
            "PHASE 2 (NOW)",
            (
                "Advance active **Version Corruption Track** 1 space per exited {BLACK}.\n"
                "**Space Effects:** Each filled space immediately triggers its effect for all players.\n"
                "**Track End** (**4** on v1.0, **5** on v2.0): excess {BLACK} **spills over** now; the new Version takes effect next round. **6** on v3.0 = **SINGULARITY!**"
            ),
            102.0,
        ),
        (
            "red",
            "{RED} RED // RANSOMWARE",
            "PHASE 4 // {RED} / ANY",
            (
                "Pay **$1** per unblocked {RED} cube.\n"
                "**Ransom Leak:** If any unpaid ransom remains (shortfall > 0), lose **1 Corporate Secret flat** *(Cash min $0)*."
            ),
            88.0,
        ),
        (
            "blue",
            "{BLUE} BLUE // SPYWARE",
            "PHASE 4 // {BLUE} / ANY",
            (
                "Lose **1 Corporate Secret** per unblocked {BLUE} cube.\n"
                "**Patient Zero:** Reaching **<= 0 Secrets** triggers immediate **Total Data Breach** (eliminated)!"
            ),
            88.0,
        ),
        (
            "green",
            "{GREEN} GREEN // MALWARE",
            "PHASE 4 // {GREEN} / ANY",
            (
                "Glitch **1 die from In Production** per unblocked {GREEN} cube.\n"
                "**Empty Production:** If In Production is empty, excess malware has **0 effect** *(no dice destroyed)*!"
            ),
            88.0,
        ),
    ]

    cy_box = col_top + 78.0
    card_gap = 14.0
    for ckey, ctitle, ctag, cbody, bh_card in cube_cards:
        fg, bg = _color_pair(ckey)
        page.rounded_rect(m_x + 7.0, cy_box, m_w - 14.0, bh_card, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
        page.rect(m_x + 7.0, cy_box, m_w - 14.0, 17.5, stroke=PALETTE["ink"], fill=bg, line_width=0.6)
        page.rich_line(m_x + 12.0, cy_box + 12.2, f"**{ctitle}**", size=7.5, color=fg if ckey != "black" else PALETTE["ink"])
        page.rich_line(m_x + m_w - 11.0, cy_box + 12.2, ctag, size=6.2, base_font="mono_bold", color=PALETTE["ink_soft"], align="right")
        page.rich_paragraph(m_x + 12.0, cy_box + 29.0, m_w - 24.0, cbody, size=7.1, leading=9.8, color=PALETTE["ink"])
        cy_box += bh_card + card_gap

    # -------------------------------------------------------------------------
    # COLUMN 3 (Right): Game Sequence Overview (x = 538, w = 214)
    # -------------------------------------------------------------------------
    g_x, g_w = 538.0, 214.0
    page.rect(g_x, col_top, g_w, col_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    page.rect(g_x, col_top, g_w, 22.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.9)
    page.text(g_x + g_w / 2.0, col_top + 15.0, "SIX-PHASE ROUND REFERENCE", font="bold", size=9.2, color=PALETTE["ink"], align="center")

    gy = col_top + 34.0
    sections = [
        (
            "PHASE 1: ROLL & DEPLOY (Simultaneous)",
            (
                "**1. Pulse:** **+1** {BLACK} -> Staging Cup (do any pending Version Switch first).\n"
                "**2. Temp Staffing:** Hire {WHITE} Contractors (**$1** / **$2** / **$3**, max 3).\n"
                "**3-4. Roll & Rerolls:** Roll Ready Zone + Contractors; up to **2 free rerolls** (Glitched dice cannot be rerolled).\n"
                "**5. Assign:** Shields (up to Defense Capacity) & Income -> **In Production**. Glitches -> **Glitched Box**."
            ),
        ),
        (
            "PHASE 2: COMPILER DROP & CORRUPTION",
            (
                "**Drop** the whole Staging Cup into the Cube Tower. Exited {BLACK} fill the Corruption Track **now** (before income; excess **spills over**). Attack Cubes wait in the Exit Tray.\n"
                "**Empty Tray:** **+1** {RED} {BLUE} {GREEN} -> Staging Cup; no attacks.\n"
                "**End Check:** **Singularity** ends the game now. Patient Zero skips Phases 3-6; survivors finish the **Final Round**."
            ),
        ),
        (
            "PHASE 3: INCOME (Simultaneous)",
            (
                "Collect $, {RESEARCH} & {STAR} from **every die still In Production** (Income & Shields, incl. {WHITE}). Purple {STAR} Signature Protocols fire once per die."
            ),
        ),
        (
            "PHASE 4: ATTACK RESOLUTION (Simultaneous)",
            (
                "Color Shields -> Any Shields. Unblocked: {RED} **$1**/cube (shortfall: **-1 Secret** flat) | {BLUE} **-1 Secret**/cube | {GREEN} glitch 1 In Production die.\n"
                "Recycle {RED} {BLUE} {GREEN} -> Staging Cup; {WHITE} -> supply. **End Check:** Patient Zero."
            ),
        ),
        (
            "PHASE 5: CI/CD PIPELINE SHIFT (Simultaneous)",
            (
                "**1.** Magnetic Splice (Omnidyne: Glitched -> Ready).\n"
                "**2.** In Production -> **Scanned Box**.\n"
                "**3.** Scanned -> Ready (**up to Release Bandwidth**, your choice).\n"
                "**4.** Glitched -> Scanned (up to Triage Bandwidth)."
            ),
        ),
        (
            "PHASE 6: OPERATIONS (Clockwise)",
            (
                "Upgrade Tracks (1/2/2/3 {RESEARCH}; L1 & L3 Breakthroughs resolve at once) & File Patents | Paid {STAR} | Buy up to **2 dice** -> Ready Zone. Then pass the **First Player Marker**."
            ),
        ),
        (
            "SECRETS VICTORY & TIEBREAKERS",
            (
                "**Most Corporate Secrets** among survivors wins. *Ties: 1. Cash ($)  2. Ready Colored Dice  3. Research ({RESEARCH})  4. Fewest Under Dev.*"
            ),
        ),
    ]

    for stitle, sbody in sections:
        page.rect(g_x + 7.0, gy - 9.5, g_w - 14.0, 14.5, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.6)
        page.text(g_x + 11.0, gy + 0.5, stitle, font="bold", size=6.9, color=PALETTE["white"])
        gy += 14.0
        gy = page.rich_paragraph(g_x + 9.0, gy, g_w - 18.0, sbody, size=6.9, leading=9.4, color=PALETTE["ink"])
        gy += 5.5


# =============================================================================
# 2B. Companion Software Market & Supply Board (Page 2 of Central Boards)
# =============================================================================

def render_market_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // SOFTWARE MODULE MARKET & CENTRAL SUPPLY [2/2]",
        right_tag="PNP PROTOTYPE v0.35.0 // US LETTER",
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
        "- **P4 End:** Recycled {RED}{BLUE}{GREEN}\n"
        "- **Corruption:** Track Cubes",
        size=6.7, leading=9.8, color=PALETTE["ink_soft"],
    )
    page.text(146.0, ty + 118.0, "Setup Priming: Drop 1 R/B/G/Black into tower; stuck prime R1.", font="italic", size=5.6, color=PALETTE["muted"], align="center")

    # 2. Phase 2 Exit Sorting Tray (x = 264, w = 212)
    ex_x = 264.0
    page.rect(ex_x, ty, 212.0, th, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(ex_x, ty, 212.0, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(ex_x + 106.0, ty + 13.2, "COMPILER EXIT TRAY (SORTING)", font="bold", size=8.6, color=PALETTE["ink"], align="center")
    tray_cols = [("black", "P2: BLACK"), ("red", "P4: RED"), ("blue", "P4: BLUE"), ("green", "P4: GREEN")]
    tw_sub = 45.0
    tgap = 5.5
    tx0 = ex_x + (212.0 - (4 * tw_sub + 3 * tgap)) / 2.0
    for i, (ck, clbl) in enumerate(tray_cols):
        bx = tx0 + i * (tw_sub + tgap)
        fg, bg = _color_pair(ck)
        page.rounded_rect(bx, ty + 27.0, tw_sub, 76.0, r=3.0, stroke=fg, fill=bg if ck != "black" else PALETTE["paper_tint"], line_width=0.8)
        page.draw_color_badge(bx + tw_sub / 2.0, ty + 52.0, 13.0, ck)
        page.text(bx + tw_sub / 2.0, ty + 94.0, clbl, font="mono_bold", size=5.8, color=PALETTE["ink"], align="center")
    page.text(ex_x + 106.0, ty + 117.5, "Black resolves in Phase 2; Red/Blue/Green wait here for Phase 4.", font="italic", size=6.3, color=PALETTE["muted"], align="center")

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
        wx + ww / 2.0, ty + 84.0,
        "Hire in **Phase 1 Step 2** (max 3/round = $6).",
        size=7.2, color=PALETTE["ink"], align="center",
    )
    page.rich_line(
        wx + ww / 2.0, ty + 100.0,
        "{WHITE} **+$1** face pays in Phase 3. All return to supply after **Phase 4**.",
        size=6.4, color=PALETTE["ink_soft"], align="center",
    )

    # -------------------------------------------------------------------------
    # MIDDLE ROW: 4 Software Module Market Slots (x = 40..752, y = 200..498)
    # Streamlined 4-stack market layout with spacious 166 pt column width!
    # -------------------------------------------------------------------------
    my, mh = 200.0, 298.0
    mgap = 16.0
    mw = (712.0 - 3 * mgap) / 4.0  # 166.0 pt wide each!

    market_colors = [
        ("red", "RED // FINSEC"),
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
        48.0, fy + 26.5, fw - 16.0,
        "- **2P / 3P / 4P:** **$6** | **8 Secrets** | **0** {RESEARCH} | Market **4 / 6 / 8** dice per color\n"
        "- **Client Companies:** identical start (all tracks Level 0); DTO Slush Fund **once per game**\n"
        "- **Corruption Tracks:** v1.0 **4** / v2.0 **5** / v3.0 **6** spaces (all player counts)\n"
        "- **Each player:** 3 Gray + 1 Purple in Ready for Release; 1 Purple in Personal Reserve (5 Gray per player in the box).",
        size=6.2, leading=8.7, color=PALETTE["ink"],
    )

    # Right: Portfolio Scoring & End-Game Triggers
    rx_f = 40.0 + fw + 14.0
    page.rect(rx_f, fy, fw, fh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx_f, fy, fw, 16.5, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
    page.text(rx_f + 8.0, fy + 11.8, "SECRETS VICTORY & TIEBREAKERS  (SURVIVING OPERATIVES)", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_paragraph(
        rx_f + 8.0, fy + 27.5, fw - 16.0,
        "- **Primary Victory Condition:** Most remaining **Corporate Secrets** wins! (Uncapped).\n"
        "- **Tiebreakers:** 1. Most Cash ($)  |  2. Most Ready Colored Dice  |  3. Most Research ({RESEARCH})  |  4. Fewest Under Dev.\n"
        "- *Patient Zero (<=0 Secrets) eliminated! Total Wipeout: rank by the tiebreakers only (breach depth ignored).*",
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
        right_tag="PNP PROTOTYPE v0.35.0 // US LETTER",
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
            page.text(tx + 12.0, ry + 46.5, "TEMP / 1 ROUND", font="mono_bold", size=6.0, color=PALETTE["muted"])

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
                    page.text(fx + col_face / 2.0, ry + 36.5, "White Hat Power", font="bold", size=6.3, color=PALETTE["purple"], align="center")
                    page.text(fx + col_face / 2.0, ry + 46.0, "Signature Protocol", font="italic", size=5.5, color=PALETTE["ink_soft"], align="center")
                else:
                    page.text(fx + col_face / 2.0, ry + 39.5, "See Market Card", font="italic", size=6.3, color=PALETTE["ink_soft"], align="center")
            elif is_glitch:
                page.rounded_rect(fx + 5.0, ry + 7.0, col_face - 10.0, row_h - 14.0, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7, dash=(2, 1.5))
                page.rich_line(fx + col_face / 2.0, ry + 26.5, f"**{f_mk}**", size=7.6, color=PALETTE["ink"], align="center")
                page.text(fx + col_face / 2.0, ry + 39.5, "0 Output / Glitched", font="mono", size=5.9, color=PALETTE["muted"], align="center")
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
                "- **Slash ( / ):** Choose **1** option in Phase 1 Step 5 *(e.g. Blue Face 4: assign as Block 1 {BLUE} Shield OR keep for +1 {RESEARCH})*.\n"
                "- **Ampersand ( & ):** Gain **both** outputs in Phase 3: Income *(+$1 & +1 {RESEARCH})*.\n"
                "- **Purple Specialist:** Dual Any-Shield baseline; Face 6 executes White Hat Signature Protocol."
            ),
        ),
        (
            "GLITCHED DICE & CI/CD PIPELINE",
            (
                "- **Glitch Face:** Face 5 on colored dice cannot be rerolled.\n"
                "- **Unresolved Glitches:** Move directly to Glitched Box in Under Development.\n"
                "- **CI/CD Pipeline (Phase 5):** In Production -> Scanned -> Ready (<= Release Bandwidth); Glitched -> Scanned (<= Triage Bandwidth)."
            ),
        ),
        (
            "BREAKTHROUGHS (L1 / L3) // TRACKS 1/2/2/3 {RESEARCH}",
            (
                "- **Defense Grid:** L1 +1 Gray die | L3 +1 Secret.  **Release:** L1 +1 Gray die | L3 +1 Secret.\n"
                "- **Triage:** L1 +2 {WHITE} (next round) | L3 pay $3: swap 1 Gray for 1 Market colored die.\n"
                "- **Patents:** L1 +$3 | L3 2nd Purple from Personal Reserve (Purple is never sold).\n"
                "- New dice -> Ready. Declined or unpayable = lost. DTO Slush Fund: once per game."
            ),
        ),
    ]
    for i, (ct, cb) in enumerate(callouts):
        cx = 40.0 + i * (box_w + 10.0)
        page.rect(cx, by, box_w, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.9)
        page.rect(cx, by, box_w, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
        page.rich_line(cx + 7.0, by + 11.4, f"**{ct}**", size=7.1, color=PALETTE["ink"])
        _fit_paragraph(page, cx + 7.0, by + 27.5, box_w - 14.0, cb, by + bh - 3.0, size=6.5, leading=9.1, min_size=5.0, color=PALETTE["ink"])


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
        ("gray", "GRAY", "Starter", ("1 Any", "1 Any", "$1 & 1{RESEARCH}", "$1 / 1{RESEARCH}", "$1 / 1{RESEARCH}", "+1{RESEARCH}")),
        ("white", "WHITE", "$1-$3", ("1 Any", "1 Any", "1 Any", "+$1", "Glitch", "Glitch")),
        ("red", "RED", "$4–$5", ("1 {RED}", "+$2", "+$2", "+$2", "Glitch", "{RED} {STAR}")),
        ("blue", "BLUE", "$4–$6", ("1 {BLUE}", "+1{RESEARCH}", "+$1", "1{BLUE}/1{RESEARCH}", "Glitch", "{BLUE} {STAR}")),
        ("green", "GREEN", "$4–$5", ("1 {GREEN}", "+1{RESEARCH}", "+2{RESEARCH}", "1{RESEARCH}/$1", "Glitch", "{GREEN} {STAR}")),
        ("yellow", "YELLOW", "$5–$6", ("+$3", "+$2", "+$2", "$1 & 1{RESEARCH}", "Glitch", "{YELLOW} {STAR}")),
        ("purple", "PURPLE", "Not sold", ("1 Any", "1 Any", "+$2", "$1 & 1{RESEARCH}", "Glitch", "{PURPLE}★ Protocol")),
    ]

    for r in range(2):
        for c in range(2):
            p_num = r * 2 + c + 1
            x = gx0 + c * (cw + gap_x)
            y = gy0 + r * (ch + gap_y)
            page.crop_marks(x, y, cw, ch)
            page.rect(x, y, cw, ch, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
            page.rect(x, y, cw, 18.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.8)
            page.text(x + 7.0, y + 12.5, f"WHITE HAT DICE & OPS QUICK-AID  [P{p_num}]", font="bold", size=7.8, color=PALETTE["white"])
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

            rh = 20.5
            for idx, (ck, dname, dmeta, dfaces) in enumerate(compact_rows):
                ry = ty + 18.0 + idx * rh
                fg, _ = _color_pair(ck)
                page.rect(x, ry, cw, rh, stroke=PALETTE["rule"], fill=PALETTE["white"] if idx % 2 == 0 else PALETTE["paper_tint"], line_width=0.5)
                page.draw_color_badge(x + 9.0, ry + rh / 2.0, 7.5, ck)
                page.text(x + 16.0, ry + 13.4, dname, font="bold", size=6.5, color=fg if ck != "white" else PALETTE["ink"])
                page.line(x + c_name, ry, x + c_name, ry + rh, stroke=PALETTE["rule"], width=0.5)
                page.text(x + c_name + c_cost / 2.0, ry + 13.2, dmeta, font="mono", size=5.9, color=PALETTE["ink_soft"], align="center")

                for fi, ftxt in enumerate(dfaces):
                    fx = x + c_name + c_cost + fi * c_f
                    page.line(fx, ry, fx, ry + rh, stroke=PALETTE["rule"], width=0.5)
                    page.rich_line(fx + c_f / 2.0, ry + 13.4, f"**{ftxt}**", size=6.2, color=fg if "{STAR}" in ftxt else PALETTE["ink"], align="center")

            # Compact Footer Cheat-Sheet inside each Pocket Card
            fy = ty + 18.0 + 7 * rh  # y + 179.5 -> 92.5 pt left
            fh = y + ch - fy
            page.rect(x, fy, cw, fh, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.7)
            cb_y = y + ch - 13.0
            _fit_paragraph(
                page, x + 6.0, fy + 7.0, cw - 12.0,
                "**P1 Roll & Deploy:** +1{BLACK} Pulse -> Hire {WHITE} ($1/$2/$3, max 3) -> Roll Ready + Contractors -> 2 free rerolls (Glitched dice cannot be rerolled) -> Assign Shields (<= Defense Capacity) & Income to In Production; Glitches -> Glitched Box.\n"
                "**P2 Compiler Drop & Corruption:** Drop Staging Cup -> {BLACK} fills Corruption Track now (excess spills over; v3.0 full = Singularity). Attack Cubes wait in Exit Tray. Empty tray: +1 {RED}{BLUE}{GREEN}.\n"
                "**P3 Income:** Collect $ / {RESEARCH} / {STAR} from every die still In Production (incl. {WHITE}). Purple {STAR} Signature Protocols fire once per die.\n"
                "**P4 Attack Resolution:** Color, then Any Shields -> {RED} $1/cube (shortfall: -1 Secret flat) | {BLUE} -1 Secret/cube | {GREEN} glitch 1 die -> Recycle {RED}{BLUE}{GREEN}; {WHITE} -> supply.\n"
                "**P5 CI/CD Pipeline Shift:** Magnetic Splice -> Production Return (In Production -> Scanned) -> Scanned Graduation (-> Ready, <= Release Bandwidth, your choice) -> Conveyor Triage (Glitched -> Scanned, <= Triage Bandwidth).\n"
                "**P6 Operations (clockwise):** Upgrade Tracks (1/2/2/3 {RESEARCH}) / File Patents ({RESEARCH}) | Paid {STAR} | Buy <= 2 dice -> Ready -> Pass First Player.\n"
                "**Breakthroughs (L1 / L3):** Defense & Release: +1 Gray die / +1 Secret | Triage: +2 {WHITE} / pay $3 swap Gray -> Market die | Patents: +$3 / 2nd Purple. Purple is never sold. DTO Slush Fund: once per game.\n"
                "**VICTORY:** Most Secrets among survivors (Patient Zero eliminated). Ties: $ > Ready Colored Dice > {RESEARCH} > Fewest Under Dev. Total Wipeout: tiebreakers only.",
                cb_y - 2.0, size=5.1, leading=6.9, min_size=4.3,
            )
            # Mini CI/CD Pipeline summary bar at bottom
            page.rect(x + 5.0, cb_y, cw - 10.0, 11.0, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.5)
            page.rich_line(x + cw / 2.0, cb_y + 8.2, "**CI/CD PIPELINE (P5):** In Production -> Scanned --(Release: 4/5/6)--> Ready  |  Glitched --(Triage: 2/3/4)--> Scanned", size=5.2, color=PALETTE["ink_soft"], align="center")


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
        page.rich_paragraph(x + 9.0, cy + 11.0, w - 18.0, v.effect, size=5.8, leading=7.8, color=PALETTE["ink"])
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
    page3.text(52.0, 24.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS -- SHEET 1 (SETS 1 & 2) [3/4]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    page3.text(740.0, 24.0, "SIZE: 1.75\" x 2.69\" (126 x 194 pt -- MATCHES MARKET BOARD)", font="mono", size=6.5, color=PALETTE["muted"], align="right")

    for col_idx, ckey in enumerate(order):
        cx = x0 + col_idx * (cw + gap_x)
        _draw_single_variant_card(page3, cx, y0, cw, ch, by_color[ckey][0])
        _draw_single_variant_card(page3, cx, y0 + ch + gap_y, cw, ch, by_color[ckey][1])

    page3.text(396.0, 594.0, "Setup: Shuffle the 3 Variant (STAR) cards of each market color (R/B/G/Y) and place 1 face-up in each Market slot (Row 1 = Default Baseline R1-Y1).", font="italic", size=6.8, color=PALETTE["muted"], align="center")

    # Page 4: Row 0 = Set 3 (R3..Y3), Row 1 = 4 Color Reference / Divider Cards
    page4.text(52.0, 24.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS -- SHEET 2 (SET 3 + DIVIDERS) [4/4]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
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
    page.text(742.0, 46.5, "1st PLAYER + VERSION MARKER + SECRETS + RESEARCH + CREDITS", font="mono", size=6.8, color=PALETTE["muted"], align="right")

    # Row 1 (y = 64..122): Special Markers + 12x Institutional Override Status Chits ([USED] / [FORFEITED])
    # First Player Marker
    page.rounded_rect(42.0, 64.0, 118.0, 52.0, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.2)
    page.text(101.0, 84.0, "FIRST PLAYER", font="bold", size=8.5, color=PALETTE["white"], align="center")
    page.text(101.0, 96.5, "FIRST PLAYER MARKER", font="mono_bold", size=6.8, color=PALETTE["rule"], align="center")
    page.text(101.0, 108.5, "Pass Clockwise End of P6", font="italic", size=6.0, color=PALETTE["rule"], align="center")

    # Active SETEC Version Marker
    page.rounded_rect(170.0, 64.0, 112.0, 52.0, r=4.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=1.2)
    page.text(226.0, 84.0, "ACTIVE VERSION >>", font="bold", size=8.5, color=PALETTE["red"], align="center")
    page.text(226.0, 97.5, "SETEC TIER POINTER", font="mono_bold", size=6.6, color=PALETTE["ink"], align="center")
    page.text(226.0, 108.5, "Move v1.0 -> v2.0 -> v3.0", font="italic", size=6.0, color=PALETTE["ink_soft"], align="center")

    # 12x Institutional Override Status Chits (place on v1.0 / v2.0 / v3.0 boxes on Company Card)
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
        page.text(bx + aw / 2.0, by + 11.5, "[X] OVERRIDE USED" if is_used else "[/] FORFEITED", font="mono_bold", size=6.2, color=PALETTE["ink"] if is_used else PALETTE["muted"], align="center")
        page.text(bx + aw / 2.0, by + 20.5, "Override Slot", font="regular", size=5.5, color=PALETTE["muted"], align="center")

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

    # Section 3 (y = 298..410): 16x Research (🔬) Tokens (8 cols x 2 rows)
    page.text(42.0, 300.0, "RESEARCH (🔬) TOKENS (x16 — UNCAPPED STORAGE)", font="mono_bold", size=6.8, color=PALETTE["green"])
    py0 = 305.0
    ph = 42.0
    for r in range(2):
        for c in range(8):
            bx = 41.0 + c * sw
            by = py0 + r * ph
            page.rect(bx, by, sw, ph, stroke=PALETTE["green"], fill=PALETTE["green_light"], line_width=0.6, dash=(3, 1.5))
            page.draw_research_icon(bx + 15.0, by + 21.0, 13.0, color=PALETTE["green"])
            page.text(bx + 26.0, by + 18.5, "1 RESEARCH", font="bold", size=7.6, color=PALETTE["green"])
            page.text(bx + 26.0, by + 29.5, "Upgrades & Patents", font="regular", size=5.6, color=PALETTE["ink_soft"])

    # Section 4 (y = 404..574): Currency Chits ($1 x 24 + $5 x 16)
    page.text(42.0, 404.0, "MONEY TOKENS ($1 x 24  &  $5 x 16)", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
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
    doc_players = PDFDocument("Too Many Secrets - Player Terminal Mats & Split Cards (v0.35.0)")
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
    doc_master = PDFDocument("Too Many Secrets - Complete Print and Play Prototype (v0.35.0)")
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
