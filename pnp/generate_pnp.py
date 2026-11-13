"""Master Print-and-Play PDF Generator for Too Many Secrets (Rogue Agent v0.42.0 Baseline).

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
# Canonical Game Data (Synchronized 1:1 with RULES.md v0.42.0 Baseline & sim/entities.py)
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
        override_name="Capital Injection",
        override_timing="P3: INCOME",
        override_desc=(
            "Gain **+$3 Cash** cleanly in Phase 3: Income (once per SETEC Version)."
        ),
        flavor='"When liquidity is limitless, capital allocation is an offensive discipline."',
        hardware_summary="DEF CAP 2  |  TRIAGE 1  |  RELEASE 4  |  TRACKS L0  |  START DIE: {RED} RED",
        starting_bonus="$6  |  SECRETS 3/4/4  |  MARKET SHARE 13 (2P) / 16 (3-4P) [MAX 20]  |  0 {RESEARCH}",
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
        hardware_summary="DEF CAP 2  |  TRIAGE 1  |  RELEASE 4  |  TRACKS L0  |  START DIE: {GREEN} GREEN",
        starting_bonus="$6  |  SECRETS 3/4/4  |  MARKET SHARE 13 (2P) / 16 (3-4P) [MAX 20]  |  0 {RESEARCH}",
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
        hardware_summary="DEF CAP 2  |  TRIAGE 1  |  RELEASE 4  |  TRACKS L0  |  START DIE: {BLUE} BLUE",
        starting_bonus="$6  |  SECRETS 3/4/4  |  MARKET SHARE 13 (2P) / 16 (3-4P) [MAX 20]  |  0 {RESEARCH}",
    ),
    CompanyCardSpec(
        code="DTO",
        name="Department of Telecom Oversight",
        sector="Federal Agency",
        override_name="Slush Fund",
        override_timing="P4: ONCE PER GAME",
        override_desc=(
            "The DTO accesses emergency black budget reserves: absorb up to **2 Corporate Secret loss** "
            "from unblocked **Blue Spyware** for free. **Once per game** (optional when it applies)."
        ),
        flavor='"Classified black budget allocations absorb compliance failures without public oversight."',
        hardware_summary="DEF CAP 2  |  TRIAGE 1  |  RELEASE 4  |  TRACKS L0  |  START DIE: {BLUE} BLUE",
        starting_bonus="$6  |  SECRETS 3/4/4  |  MARKET SHARE 13 (2P) / 16 (3-4P) [MAX 20]  |  0 {RESEARCH}",
    ),
    CompanyCardSpec(
        code="HELIX",
        name="Helix Biomedical Consortium",
        sector="Medical Research",
        override_name="Brute-Force Bypass",
        override_timing="P1: STEP 4 REROLLS",
        override_desc=(
            "Gain **1 extra free reroll** this phase. In addition, turn **1 rolled die** "
            "to any legal non-Star face of its color (the Secret face is allowed)."
        ),
        flavor='"Massively parallel quantum sequencing breaks deterministic encryption gates."',
        hardware_summary="DEF CAP 2  |  TRIAGE 1  |  RELEASE 4  |  TRACKS L0  |  START DIE: {GREEN} GREEN",
        starting_bonus="$6  |  SECRETS 3/4/4  |  MARKET SHARE 13 (2P) / 16 (3-4P) [MAX 20]  |  0 {RESEARCH}",
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
        hardware_summary="DEF CAP 2  |  TRIAGE 1  |  RELEASE 4  |  TRACKS L0  |  START DIE: {RED} RED",
        starting_bonus="$6  |  SECRETS 3/4/4  |  MARKET SHARE 13 (2P) / 16 (3-4P) [MAX 20]  |  0 {RESEARCH}",
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
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "{SECRET} Secret", "{PURPLE} {STAR}"),
        protocol_name="Logistics Bounty",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "Gain **+1 {RESEARCH}** in Phase 3: Income per **{PURPLE} {STAR}** still In Production."
        ),
    ),
    WhiteHatDossierSpec(
        code="PHREAKER",
        name="The Phreaker",
        role="Hardware Intrusion Specialist",
        flavor='"Raw voltage pulses extract signal from dormant silicon."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "{SECRET} Secret", "{PURPLE} {STAR}"),
        protocol_name="Jumper Diagnostics",
        protocol_timing="P3: INCOME",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, move **1 die** from your **Processing Box** to your **Scanned Box**, "
            "banking its Secret now. If your Processing Box is empty, roll **1 Scanned Box die** and collect "
            "only its $ / {RESEARCH} (it stays in place); if Under Development is empty, collect **+$1 cash**."
        ),
    ),
    WhiteHatDossierSpec(
        code="ACOUSTIC",
        name="The Acoustic",
        role="Side-Channel Cryptanalyst",
        flavor='"Harmonic resonance frequencies decode physical chassis vibrations."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "{SECRET} Secret", "{PURPLE} {STAR}"),
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
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "{SECRET} Secret", "{PURPLE} {STAR}"),
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
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "{SECRET} Secret", "{PURPLE} {STAR}"),
        protocol_name="Arbitrary Code Execution",
        protocol_timing="P1: STEP 4 ROLLING",
        protocol_desc=(
            "When Face 6 ({PURPLE} {STAR}) is rolled, turn **1 other rolled die** in your active "
            "pool to **any legal non-Star face of that die's color** other than the Secret face."
        ),
    ),
    WhiteHatDossierSpec(
        code="CIPHER",
        name="The Cipher",
        role="Distributed Ledger Architect",
        flavor='"Parity calculations balance zero-knowledge proofs flawlessly."',
        purple_faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "{SECRET} Secret", "{PURPLE} {STAR}"),
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
        cost_str="Starter (2 each)",
        faces=("Block 1 Any", "Block 1 Any", "+$1 & +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+$1 / +1 {RESEARCH}", "+1 {RESEARCH}"),
        notes="Start: 2 Gray + 1 starting colored die + 1 Purple in Ready for Release; more Gray via Level 1 Breakthroughs. Faces 4-5 are Choices (/): declare in Phase 1 Step 4.",
    ),
    DieSpec(
        color_key="red",
        title="RED",
        subtitle="Marketing",
        cost_str="$4-$5 (by Variant)",
        faces=("+1 Market Share / +$1", "+$2", "+$2", "+$2", "{SECRET} Secret", "{RED} {STAR}"),
        notes="Marketing revenue & Market Share. Face 5 Secret face (+2), Face 6 Red {STAR}.",
    ),
    DieSpec(
        color_key="blue",
        title="BLUE",
        subtitle="Firewall",
        cost_str="$4-$6 (by Variant)",
        faces=("+1 Corporate Secret", "+1 Corporate Secret", "+$1", "+1 {RESEARCH} / +$1", "{SECRET} Secret", "{BLUE} {STAR}"),
        notes="Direct Secrets & Defense synergy. Face 5 Secret face (+2, or +3 at Defense Grid L3+), Face 6 Blue {STAR}.",
    ),
    DieSpec(
        color_key="green",
        title="GREEN",
        subtitle="Antivirus",
        cost_str="$4-$5 (by Variant)",
        faces=("+2 {RESEARCH}", "+1 {RESEARCH}", "+2 {RESEARCH}", "+1 {RESEARCH} / +$1", "{SECRET} Secret", "{GREEN} {STAR}"),
        notes="Premier Research engine. Face 5 Secret face (+2, then cleans 1 Glitched Shield Slot), Face 6 Green {STAR}.",
    ),
    DieSpec(
        color_key="yellow",
        title="YELLOW",
        subtitle="Commercial AI",
        cost_str="$5-$6 (by Variant)",
        faces=("+2 Market Share", "+1 Market Share / +1 {RESEARCH}", "+$1 & +1 Market Share", "+$2 / +1 {RESEARCH}", "+$2 / +1 {RESEARCH}", "{YELLOW} {STAR}"),
        notes="Commercial AI revenue & Market Share. No Secret face. Face 6 Yellow {STAR}.",
    ),
    DieSpec(
        color_key="purple",
        title="PURPLE",
        subtitle="Specialist AI",
        cost_str="Not sold (Public Rel. L3)",
        faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {RESEARCH}", "{SECRET} Secret", "{PURPLE} {STAR}"),
        notes="Not purchasable. 2nd Purple die only from Public Relations Track Level 3. Face 5 Secret face (+1), Face 6 Purple {STAR} Signature Protocol.",
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
        '{PIP1} +1 Share/$1  |  {PIP2}{PIP3}{PIP4} +$2', '{PIP5} Secret  |  {PIP6} {STAR}',
        'Brand Protection', 'P3 INCOME',
        'Gain **+$2 & +1 Market Share** in Phase 3: Income *(not above max; outside Public Relations limit)*.',
        'Brand Protection: +$2 & +1 Market Share.',
    ),
    VariantCardSpec(
        'R2', 'red', 'RED // MARKETING', '$4',
        '{PIP1} +1 Share/$1  |  {PIP2}{PIP3}{PIP4} +$2', '{PIP5} Secret  |  {PIP6} {STAR}',
        'Ad Campaign', 'P3 IN PRODUCTION -> P5 OPS',
        'No shield or Income. If still **In Production** in Phase 3, you may pay **$2** in your Phase 5 turn for **+1 Market Share** *(not above max; outside Public Relations limit; lost if unused)*.',
        'Ad Campaign: pay $2 in P5 for +1 Market Share.',
    ),
    VariantCardSpec(
        'R3', 'red', 'RED // MARKETING', '$5',
        '{PIP1} +1 Share/$1  |  {PIP2}{PIP3}{PIP4} +$2', '{PIP5} Secret  |  {PIP6} {STAR}',
        'Customer Poaching', 'P3 AFTER ALL INCOME',
        'No shield or Income. After all Income in Phase 3, take **1 Market Share** from the surviving rival with the **most** *(you choose among ties)*. At your max, the rival still loses 1.',
        'Poaching: take 1 Market Share from the leader.',
    ),
    VariantCardSpec(
        'B1', 'blue', 'BLUE // FIREWALL', '$5',
        '{PIP1}{PIP2} +1 Secret | {PIP3} +$1', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret | {PIP6} {STAR}',
        'Honeypot Telemetry', 'P3 INCOME + P4 BONUS',
        'Gain **+1 {RESEARCH}** in Phase 3; if **1+ {BLUE} Blue** cubes exit and you take **0 Blue** damage in Phase 4, gain **+$2** *(die must still be In Production)*.',
        'Honeypot: +1 research; +$2 if 0 Blue damage.',
    ),
    VariantCardSpec(
        'B2', 'blue', 'BLUE // FIREWALL', '$6',
        '{PIP1}{PIP2} +1 Secret | {PIP3} +$1', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret | {PIP6} {STAR}',
        'Deep R&D Vault', 'P5 OPS',
        'Pay **$4** in Phase 5 to gain **+1 Corporate Secret**.',
        'R&D Vault: pay $4 in P5 for a Secret.',
    ),
    VariantCardSpec(
        'B3', 'blue', 'BLUE // FIREWALL', '$4',
        '{PIP1}{PIP2} +1 Secret | {PIP3} +$1', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret | {PIP6} {STAR}',
        'Air-Gapped Backup', 'P3 INCOME',
        'In Phase 3, move **1 die from your Processing Box to your Scanned Box**, banking its Secret.',
        'Air-Gapped: Processing -> Scanned, banks Secret.',
    ),
    VariantCardSpec(
        'G1', 'green', 'GREEN // ANTIVIRUS', '$5',
        '{PIP1} +2{RESEARCH} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret | {PIP6} {STAR}',
        'Self-Healing Kernel', 'P1 CLEAN + P3 INCOME',
        '**Clean 1 Glitched Shield Slot** (Phase 1 Step 5) **AND** gain **+1 {RESEARCH}** in Phase 3: Income.',
        'Kernel: cleans a slot & yields Research.',
    ),
    VariantCardSpec(
        'G2', 'green', 'GREEN // ANTIVIRUS', '$4',
        '{PIP1} +2{RESEARCH} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret | {PIP6} {STAR}',
        'Universal Sandbox', 'P3 INCOME',
        'Gain **+2 {RESEARCH}**, plus **+1 {RESEARCH}** for each of your **Glitched Shield Slots** in Phase 3: Income.',
        'Sandbox: generates research from quarantined glitches.',
    ),
    VariantCardSpec(
        'G3', 'green', 'GREEN // ANTIVIRUS', '$4',
        '{PIP1} +2{RESEARCH} | {PIP2} +1{RESEARCH} | {PIP3} +2{RESEARCH}', '{PIP4} 1{RESEARCH}/$1 | {PIP5} Secret | {PIP6} {STAR}',
        'Live Reboot', 'P3 INCOME OUTPUT',
        'Gain **+2 {RESEARCH}** and **+$1** in Phase 3: Income.',
        'Live Reboot: High-yield immediate income.',
    ),
    VariantCardSpec(
        'Y1', 'yellow', 'YELLOW // COMM. AI', '$6',
        '{PIP1} +2 Share  {PIP2} +1 Share/1{RESEARCH}', '{PIP3} $1 & 1 Share | {PIP4}{PIP5} $2/1{RESEARCH} | {PIP6} {STAR}',
        'Algorithmic Trading', 'P3 INCOME -OR- P5 OPS',
        'Gain **+$4** in Phase 3: Income, **OR** pay **$2** in Phase 5: Operations to gain **+1 Corporate Secret**.',
        'Trading: High cash revenue OR Secret buy.',
    ),
    VariantCardSpec(
        'Y2', 'yellow', 'YELLOW // COMM. AI', '$5',
        '{PIP1} +2 Share  {PIP2} +1 Share/1{RESEARCH}', '{PIP3} $1 & 1 Share | {PIP4}{PIP5} $2/1{RESEARCH} | {PIP6} {STAR}',
        'Cloud Monopoly', 'P3 SCALING REVENUE',
        'Gain **+$2** in Phase 3, plus **+$1 per different colored** module die you own (**max +$5** total).',
        'Monopoly: Scales revenue per owned color.',
    ),
    VariantCardSpec(
        'Y3', 'yellow', 'YELLOW // COMM. AI', '$5',
        '{PIP1} +2 Share  {PIP2} +1 Share/1{RESEARCH}', '{PIP3} $1 & 1 Share | {PIP4}{PIP5} $2/1{RESEARCH} | {PIP6} {STAR}',
        'Proprietary Training', 'P3 SECRET + SCANNED',
        'Gain **+1 Corporate Secret** in Phase 3, then immediately move **this die to the Scanned Box** (before Phase 4).',
        'Training: Quick Secret gain, then to Scanned.',
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
        banner_text="**Aggressive Infiltration:** Space 4 glitches 1 slot & adds cubes.\nFinal space triggers Singularity!",
        spaces=(
            VersionTrackSpaceSpec(1, "+1 {RED} 1 {BLUE} 1 {GREEN}"),
            VersionTrackSpaceSpec(2, "Most $ loses $3\nMost {RESEARCH} loses 1 {RESEARCH}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} +1 {BLUE}"),
            VersionTrackSpaceSpec(4, "Fewest Glitched\nglitches 1 slot\n+1 {BLUE} 1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Most Dice\nreturns 1 die"),
            VersionTrackSpaceSpec(6, "**SINGULARITY!**", is_singularity=True),
        ),
    ),
    VersionTileSpec(
        version="v3.0",
        name="Corrupted Kernel",
        profile="SINGULARITY",
        banner_text="**Overclocked Surge:** Space 1 glitches 1 slot & adds cubes.\nSpace 4 leaks 1 Secret.",
        spaces=(
            VersionTrackSpaceSpec(1, "Fewest Glitched\nglitches 1 slot\n+1 {RED} 1 {BLUE}"),
            VersionTrackSpaceSpec(2, "Most MS loses $3\n& 1 {RESEARCH} +1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {RED} +1 {GREEN}"),
            VersionTrackSpaceSpec(4, "Most Secrets\nloses 1 Secret\n+1 {BLACK}"),
            VersionTrackSpaceSpec(5, "Most Dice\nreturns 1 die"),
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
        banner_text="**Memory Infiltration:** Space 3 glitches 1 slot & adds Green cube.\nSpace 5 upgrades to v3.0.",
        spaces=(
            VersionTrackSpaceSpec(1, "Transfer: Least {RESEARCH}\ntakes 1 {RESEARCH} from Most"),
            VersionTrackSpaceSpec(2, "+1 {BLUE} +1 {GREEN}\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "Fewest Glitched\nglitches 1 slot & +1 {GREEN}"),
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
        banner_text="**Setup Payload:** Add 1 {RED} 2 {BLUE} 1 {GREEN} to Staging Cup.\nAll players start with +$1.",
        spaces=(
            VersionTrackSpaceSpec(1, "Most {RESEARCH}\nloses 1 {RESEARCH}"),
            VersionTrackSpaceSpec(2, "Most $ loses $2\n+1 {BLACK}"),
            VersionTrackSpaceSpec(3, "+1 {GREEN}"),
            VersionTrackSpaceSpec(4, "UPGRADE v2.0\nFewest Glitched glitches 1", is_milestone=True),
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
    _fit_paragraph(page, x + 7.0, o_y + 18.5, w - 14.0, comp.override_desc, ty - 1.5, size=5.3, leading=6.7, min_size=4.5)

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
    page.text(x + w - 7.0, ty + 9.5, "Unused charge forfeits on upgrade.", font="italic", size=4.5, color=PALETTE["muted"], align="right")


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
    _fit_paragraph(page, x + 7.0, s_y + 18.5, w - 14.0, white_hat.protocol_desc, note_y - 6.5, size=5.3, leading=6.7, min_size=4.5)
    page.rich_line(x + w / 2.0, note_y, "*Repeatable: once per Purple {STAR} die (Phase 3: die must still be In Production).*", size=4.5, color=PALETTE["purple"], align="center")

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
        "Faces 1-2: Block 1 Any | 3: +$2 | 4: +$1 & +1{RESEARCH}\n"
        "5: Secret face (+1 Secret) | 6: {STAR} Signature Protocol",
        size=4.6, leading=6.6, color=PALETTE["ink_soft"],
    )


TRACK_STEP_COSTS = (None, 1, 2, 2, 3)  # {RESEARCH} to reach L1..L4 (RULES.md v0.42.0 baseline)


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


DEFENSE_LEVELS = [
    ("Cap 2", "Block 1 Any shields only"),
    ("Cap 2", "+1 Gray Legacy die -> Ready"),
    ("Cap 3", ""),
    ("Cap 3", "+1 {SECRET} Corporate Secret"),
    ("Cap 4", "+$1 per Attack Cube blocked in P4 (max $3), after damage"),
]
TRIAGE_LEVELS = [
    ("1 die", ""),
    ("1 die", "+1 Gray Legacy die -> Ready"),
    ("1 die", "+1 {SECRET} Corporate Secret"),
    ("1 die", "Pay $3: swap 1 Gray for 1 Market colored die"),
    ("2 dice", ""),
]
RELEASE_LEVELS = [
    ("4 dice", ""),
    ("4 dice", "+1 Gray Legacy die -> Ready"),
    ("5 dice", ""),
    ("5 dice", "+1 {SECRET} Corporate Secret"),
    ("6 dice", "+1 free reroll in P1 Step 4"),
]
PR_REGAIN_COST_MONEY = 3  # $ Cash per +1 Market Share (RULES.md v0.42.0 baseline)
PUBLIC_RELATIONS_LEVELS = [
    ("Regain up to 1/turn", ""),
    ("Regain up to 1/turn", "+$3"),
    ("Regain up to 2/turn", ""),
    ("Regain up to 2/turn", "+2nd Purple die (Reserve)"),
    ("Regain up to 3/turn", ""),
]

# Market Share track (RULES.md v0.38e): start = 13 (2P) / 16 (3-4P); max = 20; 0 = Market Collapse;
# Market Leader Bonus by Market Share place (1st +3 Secrets; 2nd +1).
MARKET_SHARE_MAX = 20
MARKET_SHARE_START = {13: "2P START", 16: "3-4P START"}



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
    page.rich_line(tx, y + 26.5, line1, size=5.6, color=title_color)
    page.rich_line(tx, y + 38.0, line2, size=4.8, color=PALETTE["ink"])
    page.rich_line(tx, y + 49.0, line3, size=4.6, color=PALETTE["ink_soft"])
    if line4:
        page.rich_line(tx, y + 60.0, line4, size=4.3, color=PALETTE["muted"])


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
            page.rich_line(bx, ry + 15.0, "**Regain up to 1 Market Share / turn**", size=5.8, color=PALETTE["ink"])
            page.rich_line(bx, ry + 27.0, f"Cost: **${PR_REGAIN_COST_MONEY} Cash** per +1 Market Share (Phase 5 Operations)", size=4.8, color=PALETTE["ink_soft"])
            page.text(bx, ry + 38.0, "Baseline corporate communications; active from Round 1", font="italic", size=4.5, color=PALETTE["muted"])

        elif lv == 1:
            page.rich_line(bx, ry + 14.5, "**Regain up to 1 Market Share / turn**", size=5.8, color=PALETTE["ink"])
            page.rich_line(bx, ry + 26.5, "★ **BREAKTHROUGH: GAIN +$3 LIQUID CASH**", size=5.5, color=PALETTE["purple"])
            page.text(bx, ry + 38.0, "Collected immediately upon advancing to Level 1", font="italic", size=4.5, color=PALETTE["ink_soft"])

        elif lv == 2:
            page.rich_line(bx, ry + 15.0, "**Regain up to 2 Market Share / turn**", size=5.8, color=PALETTE["ink"])
            page.rich_line(bx, ry + 27.0, f"Cost: **${PR_REGAIN_COST_MONEY} Cash** per +1 Market Share (Phase 5 Operations)", size=4.8, color=PALETTE["ink_soft"])
            page.text(bx, ry + 38.0, "Expanded corporate PR campaigns and proactive outreach", font="italic", size=4.5, color=PALETTE["muted"])

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
            page.rich_line(bx, ry + 14.0, "**Regain up to 2 Market Share / turn**", size=5.6, color=PALETTE["ink"])
            page.rich_line(bx, ry + 25.5, "★ **BREAKTHROUGH: 2ND PURPLE SPECIALIST DIE**", size=5.4, color=PALETTE["purple"])
            page.text(bx, ry + 37.0, "Moves from Personal Reserve -> Ready for Release", font="italic", size=4.6, color=PALETTE["ink_soft"])

        elif lv == 4:
            page.rich_line(bx, ry + 15.0, "**Regain up to 3 Market Share / turn**", size=5.8, color=PALETTE["ink"])
            page.rich_line(bx, ry + 27.0, f"Cost: **${PR_REGAIN_COST_MONEY} Cash** per +1 Market Share (Phase 5 Operations)", size=4.8, color=PALETTE["ink_soft"])
            page.text(bx, ry + 38.0, "Maximum media saturation (full damage control blitz)", font="italic", size=4.5, color=PALETTE["muted"])

    # Bottom setup note
    page.rich_line(
        x + w / 2.0, y + h - 5.5,
        "*Setup: Place 2nd Purple Specialist die on L3 outline. Unlocks upon reaching L3.*",
        size=4.7, color=PALETTE["muted"], align="center",
    )


def render_player_board(
    page: PDFPage,
    idx: int,
    comp: Optional[CompanyCardSpec] = None,
    white_hat: Optional[WhiteHatDossierSpec] = None,
) -> None:
    draw_board_outer_frame(
        page,
        left_tag=f"TOO MANY SECRETS // COMPANY TERMINAL MAT [TERM-0{idx}/4]",
        right_tag="PNP PROTOTYPE v0.42.0 // US LETTER",
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
        tag="PRIMARY VICTORY GOAL",
        icon_type="secret",
        line1="Start: **3** (2P) / **4** (3-4P)",
        line2="Surviving player with most Secrets wins",
        line3="Trigger: ≤ 0 Secrets = **TOTAL DATA BREACH**",
        line4="Survivors earn Market Leader Bonus (P6 & End)",
    )

    # 2. Liquid Cash ($) Holder (y = 110..186, h = 76)
    _draw_resource_holder(
        page, lx, 110.0, lw, 76.0,
        title="**LIQUID CASH ($)**",
        title_color=PALETTE["ink"],
        border=PALETTE["ink"],
        tint=PALETTE["panel_tint"],
        tag="UNCAPPED RESERVE",
        icon_type="money",
        line1="Start: **$6**",
        line2="Phase 3: Gain Income from software modules",
        line3="Phase 5: Buy 1 die ($4–$6) -> Scanned | Regain MS ($3)",
        line4="Operational Tiebreaker #2 at game end",
    )

    # 3. Research Tokens (🔬) Holder (y = 190..266, h = 76)
    _draw_resource_holder(
        page, lx, 190.0, lw, 76.0,
        title="{RESEARCH} **RESEARCH TOKENS (🔬)**",
        title_color=PALETTE["purple"],
        border=PALETTE["purple"],
        tint=PALETTE["purple_light"],
        tag="UNCAPPED R&D",
        icon_type="research",
        line1="Start: **0 🔬**",
        line2="Phase 5: Upgrade Hardware Tracks (1/2/2/3 🔬)",
        line3="Max 2 hardware upgrades per turn",
        line4="Operational Tiebreaker #4 at game end",
    )

    # 4. Expanded Public Relations Track & Personal Reserve (y = 272..576, h = 304)
    _draw_public_relations_area(page, lx, 272.0, lw, 304.0)

    # -------------------------------------------------------------------------
    # MAIN COLUMN: CI/CD PIPELINE & DEFENSE GRID (x = 268..756, w = 488)
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
    # 2. VERTICAL RELEASE TRACK & RELEASE BANDWIDTH COLUMN (Left Column: x = 268..342, y = 118..438, h = 320)
    # =========================================================================
    vx, vw = 268.0, 74.0
    vy, vh = 118.0, 320.0
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
    # 3. ZONE 2: IN PRODUCTION (Middle-Right Box: x = 346..756, y = 118..438, h = 320)
    # =========================================================================
    px, pw = 346.0, 410.0
    py, ph = 118.0, 320.0
    page.rect(px, py, pw, ph, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(px, py, pw, 16.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(px + 8.0, py + 11.2, "**ZONE 2: IN PRODUCTION  (DEPLOYED DICE)**", size=7.8, color=PALETTE["ink"])
    page.text(px + pw - 8.0, py + 11.2, "P6: MOVES TO SCANNED BOX", font="mono_bold", size=5.8, color=PALETTE["ink_soft"], align="right")

    # --- 3A: Income Bays (Money, Research, Market Share / Star) (h = 98) ---
    page.rect(px + 6.0, py + 21.0, pw - 12.0, 98.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
    page.rect(px + 6.0, py + 21.0, pw - 12.0, 14.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_line(px + 10.0, py + 30.5, "**INCOME SLOT**", size=6.8, color=PALETTE["ink"])
    page.text(px + pw - 14.0, py + 30.5, "RESOLVES IN PHASE 3: INCOME", font="mono_bold", size=5.2, color=PALETTE["muted"], align="right")

    income_bays = [
        ("MONEY ($)", "Cash Faces"),
        ("RESEARCH ({RESEARCH})", "Research Faces"),
        ("MARKET SHARE & {STAR}", "Share & Star Faces"),
    ]
    ib_w = (pw - 24.0) / 3.0
    for ib_i, (ib_title, ib_sub) in enumerate(income_bays):
        ib_x = px + 9.0 + ib_i * (ib_w + 3.0)
        page.rounded_rect(ib_x, py + 39.0, ib_w - 3.0, 75.0, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6)
        page.rich_line(ib_x + (ib_w - 3.0) / 2.0, py + 50.0, f"**{ib_title}**", size=6.5, color=PALETTE["ink"], align="center")
        page.text(ib_x + (ib_w - 3.0) / 2.0, py + 106.0, ib_sub, font="italic", size=5.0, color=PALETTE["muted"], align="center")

    # --- 3B: Defense Grid (Shield Slots, Block 1 Any only) (h = 104) ---
    dg_y = py + 125.0
    page.rect(px + 6.0, dg_y, pw - 12.0, 104.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.85)
    page.rect(px + 6.0, dg_y, pw - 12.0, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(px + 10.0, dg_y + 10.0, "**DEFENSE GRID**  (SHIELD SLOTS — BLOCK 1 ANY)", size=6.8, color=PALETTE["ink"])
    page.text(px + pw - 14.0, dg_y + 10.0, "START WITH 1 GLITCHED SLOT  |  RESOLVES IN P4", font="mono_bold", size=5.2, color=PALETTE["muted"], align="right")

    # Four spacious Shield Slots; each carries a spot for a Glitched Shield Slot marker
    d_box_x = px + 9.0
    d_box_w = pw - 18.0
    slot_gap = 6.0
    slot_w = (d_box_w - 3 * slot_gap) / 4.0
    slot_y, slot_h = dg_y + 20.0, 78.0
    slot_tags = ("ACTIVE (START)", "START GLITCHED", "UNLOCKS AT L2", "UNLOCKS AT L4")
    for sl in range(4):
        sx = d_box_x + sl * (slot_w + slot_gap)
        page.rounded_rect(sx, slot_y, slot_w, slot_h, r=3.0, stroke=PALETTE["border"], fill=PALETTE["white"] if sl < 2 else PALETTE["paper_tint"], line_width=0.85, dash=(3.0, 2.0))
        page.text(sx + slot_w / 2.0, slot_y + 11.0, f"SHIELD SLOT {sl + 1}", font="bold", size=6.4, color=PALETTE["ink"], align="center")
        page.text(sx + slot_w / 2.0, slot_y + 20.0, slot_tags[sl], font="mono", size=4.8, color=PALETTE["muted"], align="center")
        # Die placement square in center
        ds_sz = 30.0
        page.rounded_rect(sx + (slot_w - ds_sz) / 2.0, slot_y + 25.0, ds_sz, ds_sz, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.5)
        page.text(sx + slot_w / 2.0, slot_y + 42.0, "1 ANY", font="mono_bold", size=5.0, color=PALETTE["guide"], align="center")
        # Glitched marker slot at bottom
        mk_w = slot_w - 12.0
        page.rect(sx + 6.0, slot_y + 60.0, mk_w, 13.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.5, dash=(2.0, 1.5))
        page.text(sx + slot_w / 2.0, slot_y + 68.5, "GLITCHED SLOT", font="mono_bold", size=4.6, color=PALETTE["red"], align="center")

    # --- 3C: Embedded Defense Grid Track (Bottom of In Production, h = 79) ---
    st_y = py + 235.0
    st_h = 79.0
    page.rect(px + 6.0, st_y, pw - 12.0, st_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.85)
    page.rect(px + 6.0, st_y, pw - 12.0, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(px + 10.0, st_y + 10.0, "{RESEARCH} **DEFENSE GRID TRACK**  (DEFENSE CAPACITY)", size=6.5, color=PALETTE["ink"])
    page.text(px + pw - 14.0, st_y + 10.0, "UPGRADE IN PHASE 5", font="mono_bold", size=5.2, color=PALETTE["purple"], align="right")

    # 5-level Defense Grid Track (L1 has Gray die outline)
    _draw_track_cells(page, _cells_row(px + 9.0, st_y + 17.0, pw - 18.0, st_h - 21.0, gap=3.0), DEFENSE_LEVELS, PALETTE["ink"])

    # =========================================================================
    # 4. ZONE 3: UNDER DEVELOPMENT (Bottom Box: x = 268..756, y = 444..580, h = 136)
    # Conveyor Triage: Processing Box FIFO Queue -> Scanned Box -> Ready for Release
    # =========================================================================
    uy, uh = 444.0, 136.0
    page.rect(rx, uy, rw, uh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, uy, rw, 15.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.rich_line(rx + 8.0, uy + 10.5, "**ZONE 3: UNDER DEVELOPMENT  (CI/CD PIPELINE)**", size=7.5, color=PALETTE["ink"])
    page.text(rx + rw - 8.0, uy + 10.5, "OFFLINE MODULES (DO NOT ROLL)", font="mono_bold", size=5.8, color=PALETTE["muted"], align="right")

    # --- 4A: Scanned Box (Bottom Left: x = 272..390, w = 118, y = 463..576, h = 113) ---
    # Unbounded staging area (no misleading dice outlines)
    sc_x, sc_w = rx + 4.0, 118.0
    sc_y, sc_h = uy + 19.0, uh - 23.0
    page.rect(sc_x, sc_y, sc_w, sc_h, stroke=PALETTE["blue"], fill=PALETTE["white"], line_width=0.9)
    page.rect(sc_x, sc_y, sc_w, 14.0, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=0.6)
    page.rich_line(sc_x + 6.0, sc_y + 10.0, "{BLUE} **SCANNED BOX**", size=6.8, color=PALETTE["blue"])
    page.text(sc_x + sc_w - 6.0, sc_y + 10.0, "P6 STEP 2-3", font="mono_bold", size=4.6, color=PALETTE["blue"], align="right")

    # Open staging well
    page.rounded_rect(sc_x + 4.0, sc_y + 18.0, sc_w - 8.0, sc_h - 22.0, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 36.0, "^ **GRADUATES TO READY** ^", size=5.8, color=PALETTE["blue"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 48.0, "Up to Release Bandwidth (**4 / 5 / 6**)", size=5.0, color=PALETTE["ink"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 66.0, "*Market Purchases & Production Return*", size=4.8, color=PALETTE["muted"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 78.0, "<-- Receives from Conveyor Triage", size=4.6, color=PALETTE["ink_soft"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 88.0, "& Glitched Slot Cleaning (Green)", size=4.5, color=PALETTE["ink_soft"], align="center")
    page.rich_line(sc_x + sc_w / 2.0, sc_y + 98.0, "Dice remain here until graduated", size=4.3, color=PALETTE["muted"], align="center")

    # --- 4B: Embedded Triage Upgrade Track (Top Right: x = 394..752, w = 358, y = 463..516, h = 53) ---
    tt_x, tt_w = rx + 126.0, rw - 130.0
    tt_y, tt_h = uy + 19.0, 53.0
    page.rect(tt_x, tt_y, tt_w, tt_h, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.85)
    page.rect(tt_x, tt_y, tt_w, 13.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
    page.rich_line(tt_x + 6.0, tt_y + 9.5, "{RESEARCH} **TRIAGE TRACK**  (CONVEYOR BANDWIDTH — P6 STEP 4)", size=6.2, color=PALETTE["ink"])
    page.text(tt_x + tt_w - 6.0, tt_y + 9.5, "UPGRADE IN PHASE 5", font="mono_bold", size=4.8, color=PALETTE["purple"], align="right")

    _draw_track_cells(page, _cells_row(tt_x + 3.0, tt_y + 15.0, tt_w - 6.0, tt_h - 17.0, gap=2.5), TRIAGE_LEVELS, PALETTE["purple"])

    # --- 4C: Processing Box (Bottom Right: x = 394..752, w = 358, y = 520..576, h = 56) ---
    # Elongated FIFO Queue (no misleading dice outlines)
    gl_x, gl_w = rx + 126.0, rw - 130.0
    gl_y, gl_h = uy + 76.0, 56.0
    page.rect(gl_x, gl_y, gl_w, gl_h, stroke=PALETTE["purple"], fill=PALETTE["white"], line_width=0.9)
    page.rect(gl_x, gl_y, gl_w, 13.0, stroke=PALETTE["purple"], fill=PALETTE["purple_light"], line_width=0.6)
    page.rich_line(gl_x + 6.0, gl_y + 9.5, "{SECRET} **PROCESSING BOX  (FIRST IN, FIRST OUT PIPELINE)**", size=6.2, color=PALETTE["purple"])
    page.text(gl_x + gl_w - 6.0, gl_y + 9.5, "P1 STEP 5: SECRET FACES ENTER", font="mono_bold", size=4.6, color=PALETTE["purple"], align="right")

    # Long FIFO conveyor lane
    lane_y = gl_y + 15.5
    lane_h = 23.0
    page.rounded_rect(gl_x + 4.0, lane_y, gl_w - 8.0, lane_h, r=2.5, stroke=PALETTE["purple_light"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.rich_line(gl_x + 8.0, lane_y + 7.5, "<-- **[EXIT: OLDEST / 1ST]**", size=5.0, color=PALETTE["purple"])
    page.rich_line(gl_x + gl_w / 2.0, lane_y + 7.5, "<=====  **FIFO CONVEYOR FLOW (TRIAGES NEXT TO SCANNED)**  <=====", size=4.8, color=PALETTE["purple"], align="center")
    page.rich_line(gl_x + gl_w - 8.0, lane_y + 7.5, "**[ENTRY: NEWEST]** <---", size=5.0, color=PALETTE["purple"], align="right")
    page.text(gl_x + gl_w / 2.0, lane_y + 17.5, "Dice line up in entry order; in Phase 6 Conveyor Triage, up to Triage Bandwidth oldest dice move first", font="italic", size=4.5, color=PALETTE["muted"], align="center")

    # Bank on Exit Yield Key banner below lane
    page.rich_line(
        gl_x + gl_w / 2.0, gl_y + gl_h - 5.0,
        "**Bank on Exit (P6 Step 4):**  {PURPLE} **+1**  |  {RED} **+2** *(MLB)*  |  {BLUE} **+2** *(+1 if Def L3+)*  |  {GREEN} **+2** *(cleans 1 Slot)*  |  *Moves Signature Cube -> Staging Cup*",
        size=4.7, color=PALETTE["ink_soft"], align="center",
    )


def render_company_cards_page(page: PDFPage) -> None:
    """Render all 6 Client Company Cards on a single US Letter print-and-cut sheet."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // 6x CLIENT COMPANY CARDS [PAGE 5/6]",
        right_tag="PNP PROTOTYPE v0.42.0 // US LETTER",
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
        "**1. Contract Assignment:** At setup, each player is dealt 1 Client Company card (or introductory preset). Place the card alongside your Company Terminal Mat.\n"
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
        right_tag="PNP PROTOTYPE v0.42.0 // US LETTER",
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
        "**1. Operative Assignment:** At setup, each player is dealt 1 White Hat Dossier card (or introductory preset). Place the card alongside your Company Terminal Mat.\n"
        "**2. Personal Reserve (1 Purple Die):** Your 2nd Purple Specialist Die waits on the Public Relations Track Level 3 outline. Purple dice are **not purchasable**: it moves to Ready for Release only when your Public Relations Track reaches **Level 3**. A Purple die lost to an effect is not replaced.\n"
        "**3. Standardized Faces 1-5:** All Purple Specialist dice feature: **Faces 1-2:** `Block 1 Any`, **Face 3:** `+$2`, **Face 4:** `+$1 & +1 {RESEARCH}`, **Face 5:** Secret face (`+1` Secret when it leaves the Processing Box).\n"
        "**4. Face 6 Signature Protocol:** Rolling Face 6 ({PURPLE} {STAR}) triggers the operative's bespoke Signature Protocol. Repeatable: each Purple Star die triggers the protocol once (Phase 3: Income protocols require the die to still be In Production)."
    )
    page.rich_paragraph(rx + 10.0, ry + 25.0, rw - 20.0, wh_rules_text, size=6.4, leading=8.6, color=PALETTE["ink"])


# =============================================================================
# 2A. Central SETEC Agent Board (Matches Wireframe Page 2)
# =============================================================================

def render_agent_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // CENTRAL ROGUE AGENT & MARKET SHARE BOARD [1/2]",
        right_tag="PNP PROTOTYPE v0.42.0 // US LETTER",
    )

    # Top Title Bar inside board
    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "PROJECT: SETEC  //  AUTONOMOUS MAINFRAME COMPILER & MARKET SHARE", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "VERSION TILES ON LEFT  |  CENTRAL MARKET SHARE TRACK ON RIGHT", font="mono", size=7.0, color=PALETTE["rule"], align="right")

    col_top = 64.0
    col_bot = 578.0
    col_h = col_bot - col_top  # 514 pt

    # -------------------------------------------------------------------------
    # COLUMN 1 (Left): v3.0 / v2.0 / v1.0 Slots + Corruption Track
    # -------------------------------------------------------------------------
    slot_x = 78.0
    slot_w = 220.0  # 3.056" (printable tiles are 212 x 112 pt = 2.94" x 1.56")
    slot_h = 135.0  # 1.875"
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
        page.text(slot_x + slot_w / 2.0, sy + 52.0, f"{ver_str}  //  {tier_sub}", font="mono_bold", size=8.5, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 72.0, hint1, font="italic", size=8.0, color=PALETTE["muted"], align="center")
        page.text(slot_x + slot_w / 2.0, sy + 90.0, hint2, font="regular", size=7.0, color=PALETTE["muted"], align="center")

    # -------------------------------------------------------------------------
    # COLUMN 2 (Middle): Agent Cube Effect Summary (x = 308, w = 196)
    # -------------------------------------------------------------------------
    m_x, m_w = 308.0, 196.0
    page.rect(m_x, col_top, m_w, col_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    page.rect(m_x, col_top, m_w, 22.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.9)
    page.text(m_x + m_w / 2.0, col_top + 15.0, "AGENT CUBE EFFECT SUMMARY", font="bold", size=8.8, color=PALETTE["ink"], align="center")

    cy_cur = col_top + 34.0
    page.rich_paragraph(
        m_x + 8.0, cy_cur, m_w - 16.0,
        "In **Phase 2**, drop the **Staging Cup** into the **Cube Tower** (stuck cubes stay inside). Exited {BLACK} resolves now; Attack Cubes wait in the **Exit Tray** for **Phase 4**:",
        size=6.8, leading=9.2, color=PALETTE["ink_soft"],
    )

    cube_cards = [
        (
            "black",
            "{BLACK} BLACK // CORRUPTION",
            "P2 (NOW)",
            (
                "Advance active **Version Corruption Track** 1 space per exited {BLACK}.\n"
                "**Space Effects:** Trigger immediately for all players.\n"
                "**Track End** (**4** on v1.0, **5** on v2.0): excess {BLACK} **spills over** now; new Version takes effect next round. **6** on v3.0 = **SINGULARITY!**\n"
                "**Glitch X Dice** space: turn X shield slots into **Glitched Shield Slots**."
            ),
            124.0,
        ),
        (
            "red",
            "{RED} RED // MARKET MANIPULATION",
            "P4 DAMAGE",
            (
                "Lose **1 Market Share** per unblocked {RED} cube *(min 0; never costs $ or Secrets)*.\n"
                "**Market Collapse:** any survivor at **0** after Phase 4 makes this the **Final Round** (no elimination)."
            ),
            88.0,
        ),
        (
            "blue",
            "{BLUE} BLUE // SPYWARE",
            "P4 DAMAGE",
            (
                "Lose **1 Corporate Secret** per unblocked {BLUE} cube.\n"
                "**Patient Zero:** Reaching **<= 0 Secrets** triggers immediate **Total Data Breach** (eliminated)!"
            ),
            88.0,
        ),
        (
            "green",
            "{GREEN} GREEN // MALWARE",
            "P4 DAMAGE",
            (
                "Each unblocked {GREEN} cube turns **1 shield slot** into a **Glitched Shield Slot** *(max Defense Capacity)*.\n"
                "Holds no shield until cleaned (P1 Step 5 or P6 Conveyor Triage)."
            ),
            88.0,
        ),
    ]

    cy_box = col_top + 78.0
    card_gap = 8.0
    for ckey, ctitle, ctag, cbody, bh_card in cube_cards:
        fg, bg = _color_pair(ckey)
        page.rounded_rect(m_x + 7.0, cy_box, m_w - 14.0, bh_card, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.8)
        page.rect(m_x + 7.0, cy_box, m_w - 14.0, 17.0, stroke=PALETTE["ink"], fill=bg, line_width=0.6)
        page.rich_line(m_x + 11.0, cy_box + 12.0, f"**{ctitle}**", size=7.0, color=fg if ckey != "black" else PALETTE["ink"])
        page.rich_line(m_x + m_w - 11.0, cy_box + 12.0, ctag, size=5.8, base_font="mono_bold", color=PALETTE["ink_soft"], align="right")
        page.rich_paragraph(m_x + 11.0, cy_box + 28.0, m_w - 22.0, cbody, size=6.6, leading=9.0, color=PALETTE["ink"])
        cy_box += bh_card + card_gap

    # Bottom Shield Blocking Rule Box inside Middle Column
    sh_y = cy_box + 2.0
    sh_h = col_bot - sh_y - 8.0
    page.rounded_rect(m_x + 7.0, sh_y, m_w - 14.0, sh_h, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.8)
    page.rich_line(m_x + m_w / 2.0, sh_y + 13.0, "**ANY-SHIELD BLOCKING RULE (PHASE 4)**", size=6.8, color=PALETTE["ink"], align="center")
    page.rich_paragraph(
        m_x + 11.0, sh_y + 24.5, m_w - 22.0,
        "Every shield is **Block 1 Any**. In Phase 4, split your active shields across {RED}, {BLUE}, and {GREEN} cubes; every shield must block while any unblocked cube remains.",
        size=6.3, leading=8.5, color=PALETTE["ink_soft"],
    )

    # -------------------------------------------------------------------------
    # COLUMN 3 (Right): Shared Central Market Share Track (x = 514, w = 238)
    # -------------------------------------------------------------------------
    g_x, g_w = 514.0, 238.0
    page.rect(g_x, col_top, g_w, col_h, stroke=PALETTE["red"], fill=PALETTE["white"], line_width=1.1)
    page.rect(g_x, col_top, g_w, 22.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.9)
    page.rich_line(g_x + g_w / 2.0, col_top + 15.0, "{RED} **CENTRAL MARKET SHARE TRACK**", size=9.0, color=PALETTE["red"], align="center")

    # Subheader / Start & Max instruction strip
    page.rect(g_x + 6.0, col_top + 26.0, g_w - 12.0, 22.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.rich_line(g_x + g_w / 2.0, col_top + 35.0, "**START:** **13** (2P)  |  **16** (3–4P)   •   **TRACK MAX:** **20**", size=6.3, color=PALETTE["ink"], align="center")
    page.rich_line(g_x + g_w / 2.0, col_top + 44.0, "Place all players' Market Share Markers here. **-1** per unblocked {RED}.", size=5.5, color=PALETTE["ink_soft"], align="center")

    # 21-space Track Grid (20 down to 0) in 3 columns x 7 rows — large cells for multiple player markers!
    grid_top = col_top + 53.0
    grid_h = 376.0
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
            page.text(cx + cw / 2.0, cy + 14.0, "0", font="bold", size=12.0, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 24.5, "MARKET", font="mono_bold", size=5.5, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 32.5, "COLLAPSE", font="mono_bold", size=5.5, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 42.5, "Final Round", font="italic", size=5.0, color=PALETTE["white"], align="center")
        elif tag:
            page.rounded_rect(cx, cy, cw, ch, r=3.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=1.0)
            page.rect(cx, cy, cw, 11.5, stroke=PALETTE["red"], fill=PALETTE["red"], line_width=0.6)
            page.text(cx + cw / 2.0, cy + 8.2, tag, font="mono_bold", size=5.4, color=PALETTE["white"], align="center")
            page.text(cx + cw / 2.0, cy + 28.0, str(val), font="bold", size=13.0, color=PALETTE["ink"], align="center")
            page.circle(cx + cw / 2.0, cy + 38.5, 6.5, stroke=PALETTE["red"], fill=None, line_width=0.4, dash=(2.0, 2.0))
        elif val == MARKET_SHARE_MAX:
            page.rounded_rect(cx, cy, cw, ch, r=3.0, stroke=PALETTE["red"], fill=PALETTE["paper_tint"], line_width=0.8)
            page.rect(cx, cy, cw, 11.5, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.6)
            page.text(cx + cw / 2.0, cy + 8.2, "TRACK MAX", font="mono_bold", size=5.4, color=PALETTE["red"], align="center")
            page.text(cx + cw / 2.0, cy + 28.0, str(val), font="bold", size=13.0, color=PALETTE["ink"], align="center")
            page.circle(cx + cw / 2.0, cy + 38.5, 6.5, stroke=PALETTE["guide"], fill=None, line_width=0.4, dash=(2.0, 2.0))
        else:
            page.rounded_rect(cx, cy, cw, ch, r=3.0, stroke=PALETTE["rule"], fill=PALETTE["paper_tint"], line_width=0.6)
            page.text(cx + 7.0, cy + 13.0, str(val), font="bold", size=10.0, color=PALETTE["ink_soft"])
            # Subtle marker placement ring
            page.circle(cx + cw / 2.0 + 6.0, cy + ch / 2.0 + 3.0, 10.0, stroke=PALETTE["guide"], fill=None, line_width=0.4, dash=(2.0, 2.0))

    # Market Leader Bonus & Collapse Callout Box at bottom of Right Column
    mb_y = grid_top + grid_h + 6.0
    mb_h = col_bot - mb_y - 6.0
    page.rounded_rect(g_x + 6.0, mb_y, g_w - 12.0, mb_h, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.8)
    page.rect(g_x + 6.0, mb_y, g_w - 12.0, 14.5, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=0.6)
    page.text(g_x + g_w / 2.0, mb_y + 10.2, "MARKET LEADER BONUS & TIEBREAKERS", font="bold", size=6.6, color=PALETTE["white"], align="center")
    page.rich_paragraph(
        g_x + 11.0, mb_y + 23.5, g_w - 22.0,
        "**Market Leader Bonus** (by Market Share, Patient Zeros excluded): **1st +3**, **2nd +1** Corporate Secrets (ties share the better place).\n"
        "**Awarded:** (1) End of Phase 6 in any round a **Red Secret** banks, and (2) at **Game End** (except Total Wipeout).\n"
        "**Tiebreakers:** 1. Market Share > 2. Cash ($) > 3. Ready Colored Dice > 4. Research ({RESEARCH}) > 5. Fewest Under Dev.",
        size=5.3, leading=7.1, color=PALETTE["ink"],
    )


# =============================================================================
# 2B. Companion Software Market & Supply Board (Page 2 of Central Boards)
# =============================================================================

def render_market_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // SOFTWARE MODULE MARKET & CENTRAL SUPPLY [2/2]",
        right_tag="PNP PROTOTYPE v0.42.0 // US LETTER",
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
        ("black", "P2: CORRUPT", "Track Space"),
        ("red", "P4: RED", "-1 Market Share"),
        ("blue", "P4: BLUE", "-1 Secret"),
        ("green", "P4: GREEN", "Glitch Slot"),
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
    page.text(ex_x + top_w / 2.0, ty + 117.5, "Black resolves in Phase 2; Red/Blue/Green attack in Phase 4 unless blocked.", font="italic", size=6.3, color=PALETTE["muted"], align="center")

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
        48.0, fy + 26.5, fw - 16.0,
        "- **2P / 3P / 4P:** **$6** | **3 / 4 / 4** Secrets | **13 (2P) / 16 (3-4P) [Max 20]** Market Share | **0** {RESEARCH}\n"
        "- **Market:** **4 / 6 / 8** dice per color | identical company start (all tracks L0); DTO Slush Fund **once per game**\n"
        "- **Corruption Tracks:** v1.0 **4** / v2.0 **5** / v3.0 **6** spaces (all player counts)\n"
        "- **Each player:** 2 Gray + 1 starting colored die (Company color) + 1 Purple in Ready; 1 Purple in Reserve; **1 Glitched Shield Slot** on mat; Market Share Marker on start value.",
        size=6.2, leading=8.7, color=PALETTE["ink"],
    )

    # Right: Portfolio Scoring & End-Game Triggers
    rx_f = 40.0 + fw + 14.0
    page.rect(rx_f, fy, fw, fh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx_f, fy, fw, 16.5, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
    page.text(rx_f + 8.0, fy + 11.8, "SECRETS VICTORY & TIEBREAKERS  (SURVIVING OPERATIVES)", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_paragraph(
        rx_f + 8.0, fy + 27.5, fw - 16.0,
        "- **Market Leader Bonus:** survivors by Market Share: 1st **+3**, 2nd **+1** Secrets; ties share. Awarded in any round a Red Secret banks (end of P6) and at game end.\n"
        "- **Victory:** Most **Corporate Secrets** wins. **Ties:** Market Share > $ > Ready Colored Dice > {RESEARCH} > Fewest Under Dev.\n"
        "- **Ends:** Singularity | Final Round after **Patient Zero** or **Market Collapse** (0 Share, no elimination) | Total Wipeout.\n"
        "- *Patient Zero (<=0 Secrets) eliminated, no bonus. Total Wipeout: no bonus; tiebreakers only.*",
        size=5.6, leading=7.6, color=PALETTE["ink"],
    )


# =============================================================================
# 3. Dice Visual Aids & Printable Variant (★) Market Cards (4 Pages)
# =============================================================================

SECRET_YIELD_SHORT = {
    "red": "Bank +2 (MLB)",
    "blue": "Bank +2 (+3 @ L3)",
    "green": "Bank +2, clean 1",
    "purple": "Bank +1",
}


def render_master_dice_reference(page: PDFPage) -> None:
    """Page 1 of Dice Aids: Large-Print Full-Table Master Pip-to-Ability Reference."""
    draw_board_outer_frame(
        page,
        left_tag="TOO MANY SECRETS // MASTER DICE PIP & ABILITY VISUAL AID [1/4]",
        right_tag="PNP PROTOTYPE v0.42.0 // US LETTER",
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

    # Bottom strip (y = 442..578, h = 136 pt): Secret Face Yields table + two rules callouts
    by = 442.0
    bh = 136.0
    yw = 232.0
    page.rect(40.0, by, yw, bh, stroke=PALETTE["blue"], fill=PALETTE["white"], line_width=0.9)
    page.rect(40.0, by, yw, 16.0, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=0.7)
    page.rich_line(47.0, by + 11.4, "{SECRET} **SECRET FACE YIELDS** (Face 5, banked when it leaves the Processing Box)", size=5.6, color=PALETTE["blue"])
    yield_rows = [
        ("red", "RED", "**+2** Secrets *(triggers **Market Leader Bonus**)*."),
        ("blue", "BLUE", "**+2** Secrets (**+1** at Defense Grid L3+, max **+3**)."),
        ("green", "GREEN", "**+2** Secrets, then **cleans 1 Glitched Shield Slot**."),
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
            "CHOICE FACES, SHIELDS & GLITCHED SLOTS",
            (
                "- **Slash ( / ):** Choose **1** option in Phase 1 Step 4 *(e.g. Red Face 1: +1 Market Share OR +$1)*. **Ampersand ( & ):** gain **both**.\n"
                "- **Shields:** only Gray and Purple show shields, all **Block 1 Any**. A **Glitched Shield Slot** cannot hold one; clean via Green Secret exit, G1, or 1 Any shield die.\n"
                "- **Secret Faces:** Secret faces (Face 5) may be rerolled or kept normally during rerolls."
            ),
        ),
        (
            "BREAKTHROUGHS & MILESTONES // TRACKS 1/2/2/3 {RESEARCH}",
            (
                "- **Defense Grid:** L1 +1 Gray die | L3 +1 Secret.  **Release:** L1 +1 Gray die | L3 +1 Secret.\n"
                "- **Triage:** L1 +1 Gray die | L2 +1 Secret | L3 pay $3: swap 1 Gray for 1 Market colored die | L4 Bandwidth 2.\n"
                "- **Public Relations** ($3 Cash per +1 Market Share): L1 +$3 Cash | L3 2nd Purple from Personal Reserve (Purple is never sold).\n"
                "- Breakthrough dice -> Ready; bought dice -> Scanned. Max 2 hardware upgrades/turn."
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
        ("gray", "GRAY", "Starter", ("1 Any", "1 Any", "$1 & 1{RESEARCH}", "$1 / 1{RESEARCH}", "$1 / 1{RESEARCH}", "+1{RESEARCH}")),
        ("red", "RED", "$4-$5", ("+1 Share\n/ +$1", "+$2", "+$2", "+$2", "{SECRET} Secret", "{RED} {STAR}")),
        ("blue", "BLUE", "$4-$6", ("+1 Secret", "+1 Secret", "+$1", "+1{RESEARCH}\n/ +$1", "{SECRET} Secret", "{BLUE} {STAR}")),
        ("green", "GREEN", "$4-$5", ("+2{RESEARCH}", "+1{RESEARCH}", "+2{RESEARCH}", "+1{RESEARCH}\n/ +$1", "{SECRET} Secret", "{GREEN} {STAR}")),
        ("yellow", "YELLOW", "$5-$6", ("+2 Share", "+1 Share\n/ +1{RESEARCH}", "+$1 &\n+1 Share", "+$2 /\n+1{RESEARCH}", "+$2 /\n+1{RESEARCH}", "{YELLOW} {STAR}")),
        ("purple", "PURPLE", "Not sold", ("1 Any", "1 Any", "+$2", "$1 & 1{RESEARCH}", "{SECRET} Secret", "{PURPLE}{STAR} Protocol")),
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
                    f_col = fg if "{STAR}" in ftxt else (PALETTE["blue"] if "{SECRET}" in ftxt else PALETTE["ink"])
                    f_lines = ftxt.split("\n")
                    if len(f_lines) == 1:
                        f_sz = min(6.4, 6.4 * (c_f - 3.0) / max(1.0, measure_text(f_lines[0], font="bold", size=6.4)))
                        page.rich_line(fx + c_f / 2.0, ry + rh / 2.0 + 2.2, f"**{f_lines[0]}**", size=max(f_sz, 4.8), color=f_col, align="center")
                    else:
                        for li_, ltxt in enumerate(f_lines):
                            page.rich_line(fx + c_f / 2.0, ry + 7.5 + li_ * 6.8, f"**{ltxt}**", size=5.0, color=f_col, align="center")

            # Clean Secret Face Yields & Icon Legend Footer
            fy = ty + 19.0 + len(compact_rows) * rh
            fh = y + ch - fy
            page.rect(x, fy, cw, fh, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.7)
            page.rect(x, fy, cw, 14.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.6)
            page.rich_line(x + 6.0, fy + 9.8, "{SECRET} **SECRET FACE YIELDS** *(banked when leaving Processing Box)*", size=6.2, color=PALETTE["ink"])
            page.rich_paragraph(
                x + 6.0, fy + 23.0, cw - 12.0,
                "- {RED} **Red Secret:** **+2** Corporate Secrets *(also triggers **Market Leader Bonus** at end of Phase 6)*\n"
                "- {BLUE} **Blue Secret:** **+2** Secrets (**+1** at Defense L3+; max **3**)\n"
                "- {GREEN} **Green Secret:** **+2** Secrets, then cleans 1 slot   |   {PURPLE} **Purple Secret:** **+1** Secret\n"
                "- **Choice ( / ):** Commit in P1 Step 4   |   **Dual ( & ):** Gain both   |   **Secret Faces:** Rerollable in P1 Step 3",
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
            "**1. Pulse:** +1 {BLACK} -> Staging Cup (do pending Version Switch first). **2-3. Roll & Rerolls:** Roll Ready dice; up to 2 free rerolls (Secret faces can reroll). **4. Assign:** Secret faces -> Processing Box; clean Glitched Shield Slots (G1 or 1 Any shield die); shields -> Defense Grid; rest -> Income.",
        ),
        (
            "P2: COMPILER DROP & CORRUPTION",
            "**Drop** Staging Cup into Cube Tower. Exited {BLACK} fill Corruption Track **now** (v3.0 full = **Singularity!**). Signature Cubes exit -> **Target Lock** (return to mat). Attack Cubes wait in Exit Tray. **Empty Tray:** +1 {RED}{BLUE}{GREEN} -> Staging Cup. *(Patient Zero skips P3-P6; survivors finish Final Round.)*",
        ),
        (
            "P3: INCOME (Simultaneous)",
            "Collect $, {RESEARCH}, Market Share & {STAR} from every die still **In Production**. Purple {STAR} Signature Protocols fire once per die. Then **Customer Poaching** (clockwise from First Player): take 1 Market Share from top rival.",
        ),
        (
            "P4: ATTACK RESOLUTION (Simultaneous)",
            "**Target Lock:** +1 Attack Cube of dominant color (you pick ties; blockable). Split all **Any** shields across cubes (all must block). Unblocked: {RED} **-1 Market Share** | {BLUE} **-1 Secret** | {GREEN} 1 shield slot -> **Glitched Shield Slot**. Recycle {RED}{BLUE}{GREEN} -> Staging Cup. **End Check:** Wipeout, PZ, **Market Collapse**.",
        ),
        (
            "P5: OPERATIONS (Clockwise from First Player)",
            "Upgrade Tracks (<= 2 upgrades/turn [1/2/2/3 {RESEARCH}]; L1 & L3 Breakthroughs resolve at once) | Regain Market Share ($3 Cash each, up to PR limit 1/1/2/2/3; separate) | Paid {STAR} incl. Ad Campaign | Buy <= 1 die -> Scanned Box.",
        ),
        (
            "P6: CI/CD PIPELINE SHIFT (Simultaneous)",
            "**1.** Magnetic Splice. **2.** In Production -> **Scanned Box**. **3.** Scanned -> **Ready** (<= Release Bandwidth 4/5/6). **4.** Conveyor Triage: **Processing -> Scanned** (<= Triage Bandwidth, oldest first; each banks its Secret; banking a Secret moves Signature Cube from mat -> Staging Cup). **5.** Red Secret banked: **Market Leader Bonus**. Pass First Player Marker.",
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
                page.text(x + 8.0, cy + 7.6, p_title, font="bold", size=5.8, color=PALETTE["ink"])
                cy = page.rich_paragraph(x + 8.0, cy + 16.5, cw - 16.0, p_body, size=5.0, leading=6.4, color=PALETTE["ink"])
                cy += 1.5

            # Bottom Victory & Tiebreakers Strip
            vy = y + ch - 25.0
            page.rect(x + 5.0, vy, cw - 10.0, 21.0, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.6)
            page.rich_paragraph(
                x + 8.0, vy + 7.2, cw - 16.0,
                "**VICTORY & MARKET LEADER BONUS:** 1st **+3**, 2nd **+1** Secrets by Market Share (ties share; Patient Zeros excluded) at P6 end if a Red Secret banked, and at Game End. Most **Secrets** wins! *Ties: Market Share > $ > Ready Colored Dice > {RESEARCH} > Fewest Under Dev.*",
                size=4.9, leading=6.2, color=PALETTE["ink"],
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
    page.text(742.0, 46.5, "1st PLAYER + VERSION + MARKET SHARE + SECRETS + SLOT MARKERS + RESEARCH + CREDITS", font="mono", size=6.8, color=PALETTE["muted"], align="right")

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

    # Section 2b (y = 268..330): 16x Glitched Shield Slot markers (4 per player; 8 cols x 2 rows)
    page.text(42.0, 270.0, "GLITCHED SHIELD SLOT MARKERS (x16 — 4 PER PLAYER; EACH PLAYER STARTS WITH 1 MARKER ON MAT)", font="mono_bold", size=6.8, color=PALETTE["red"])
    gy0 = 275.0
    gh = 26.0
    for r in range(2):
        for c in range(8):
            bx = 41.0 + c * sw
            by = gy0 + r * gh
            page.rect(bx, by, sw, gh, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=0.6, dash=(3, 1.5))
            page.text(bx + sw / 2.0, by + 11.5, "GLITCHED", font="mono_bold", size=6.8, color=PALETTE["red"], align="center")
            page.text(bx + sw / 2.0, by + 20.5, "SHIELD SLOT", font="mono_bold", size=5.8, color=PALETTE["ink"], align="center")

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
            page.text(bx + 26.0, by + 26.0, "Tracks & Market Share", font="regular", size=5.6, color=PALETTE["ink_soft"])

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
    doc_players = PDFDocument("Too Many Secrets - Player Terminal Mats & Split Cards (v0.42.0)")
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
    doc_master = PDFDocument("Too Many Secrets - Complete Print and Play Prototype (v0.42.0)")
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
