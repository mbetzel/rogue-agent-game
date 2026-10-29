"""Master Print-and-Play PDF Generator for Too Many Secrets (Rogue Agent v0.11.0 Baseline / Phase 17).

Generates minimalist, ink-saver, print-ready US Letter (11" x 8.5") PDFs:
  - 01_Player_Boards.pdf (6 pages — 1 per Consultancy Archetype, matching Wireframe Page 1)
  - 02_Central_Game_Boards.pdf (2 pages — SETEC Agent Board matching Wireframe Page 2 + Market & Supply Board)
  - 03_Dice_Visual_Aids_and_Market_Cards.pdf (4 pages — Master Pip Aid, 4x Player Pocket Aids, 15x Variant ★ Cards)
  - 04_SETEC_Version_Cards_and_Tokens.pdf (2 pages — 6x SETEC Version Tiles sized to board slots + Cut-Out PnP Tokens)
  - 00_Too_Many_Secrets_Complete_PnP.pdf (All 14 pages combined in print order)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from pnp.illustrations import draw_character_illustration
from pnp.pdf_engine import PALETTE, Color, PDFDocument, PDFPage, measure_text


# =============================================================================
# Canonical Game Data (Synchronized 1:1 with RULES.md v0.11.0 & sim/entities.py)
# =============================================================================

@dataclass(frozen=True)
class CharacterSpec:
    code: str
    name: str
    role: str
    flavor: str
    timing: str
    ability_name: str
    ability_desc: str


CHARACTERS: List[CharacterSpec] = [
    CharacterSpec(
        code="ACOUSTIC",
        name="The Acoustic",
        role="Pattern Genius // Mainframe Resonance",
        flavor='"Every mainframe hums before it strikes. Listen to the baffles -- you can hear which packet drops next."',
        timing="P2: AFTER DROP",
        ability_name="Baffle Echo",
        ability_desc=(
            "If you take unblocked damage from any color during **Phase 2**, permanently "
            "remove **1 cube** of that color in the exit tray from the game (return to box)."
        ),
    ),
    CharacterSpec(
        code="PHREAKER",
        name="The Phreaker",
        role="Hardware Tinkerer // Emergency Relays",
        flavor='"A strip of Mylar splicing tape and a 2600-Hz whistle will fix what ten grand of silicon can\'t."',
        timing="P3: OPERATIONS",
        ability_name="Magnetic Splice",
        ability_desc=(
            "During your **Phase 3** turn, move **up to 2 worn dice** from your Unpatched Zone "
            "back to your Ready Zone for **free** (without spending {WRENCH} or **$**)."
        ),
    ),
    CharacterSpec(
        code="PRODIGY",
        name="The Prodigy",
        role="Reckless Hacker // Lock Bypassing",
        flavor='"Locked memory is just a polite suggestion from someone who left debug interrupts enabled."',
        timing="P1: REROLL STEP",
        ability_name="Brute-Force Bypass",
        ability_desc=(
            "During your **Phase 1** rerolls, include **any number of {LOCK} Locked dice** "
            "(including Glitch dice) in your free rerolls without spending {WRENCH} tokens."
        ),
    ),
    CharacterSpec(
        code="SPOOK",
        name="The Spook",
        role="Ex-Intelligence // OpSec & Slush Funds",
        flavor='"Every breach has a price tag. That\'s what non-attributable slush accounts are for."',
        timing="P2: STEP 2B DMG",
        ability_name="Slush Fund",
        ability_desc=(
            "When unblocked damage would cause **Secret** loss (from {BLUE} Blue or unpaid {RED} Red), "
            "pay **$1 per Secret** from your supply to prevent that loss (up to your cash)."
        ),
    ),
    CharacterSpec(
        code="CIPHER",
        name="The Cipher",
        role="Mathematician // Algorithmic Arbitrage",
        flavor='"Why pay retail for entropy when SETEC\'s own arbitrage equations subsidize the upgrade?"',
        timing="P3: OPERATIONS",
        ability_name="Algorithmic Arbitrage",
        ability_desc=(
            "In **Phase 3**, buy **1 Colored Die** at a **$2 discount** (min $0), **OR** take "
            "Backdoor Siphon (Dirty Income) **without demoting** a Ready die to Unpatched."
        ),
    ),
    CharacterSpec(
        code="OPERATOR",
        name="The Operator",
        role="Master Strategist // Contractor Dispatch",
        flavor='"Never burn internal hardware when three night-shift phreakers are waiting by a payphone."',
        timing="P1: STAFFING",
        ability_name="Redundant Crew",
        ability_desc=(
            "In **Phase 1 Staffing**, hire up to **2 {WHITE} White Contractor Dice for free** "
            "this round (bypassing progressive costs; hiring a 3rd die costs $3)."
        ),
    ),
]


@dataclass(frozen=True)
class DieSpec:
    color_key: str
    title: str
    subtitle: str
    cost_str: str
    vp_str: str
    faces: Tuple[str, str, str, str, str, str]
    notes: str


DICE_SPECS: List[DieSpec] = [
    DieSpec(
        color_key="gray",
        title="GRAY",
        subtitle="Legacy Code",
        cost_str="Starter (x4)",
        vp_str="0 VP",
        faces=("Block 1 Any", "Block 1 Any", "+$1", "+$1", "+$1 / +1 {WRENCH}", "+1 {WRENCH}"),
        notes="Starter pool (4 per player). Face 5 is a Choice (/): declare +$1 or +1 {WRENCH} in Step 5.",
    ),
    DieSpec(
        color_key="white",
        title="WHITE",
        subtitle="Contractor",
        cost_str="$1 / $2 / $3",
        vp_str="0 VP",
        faces=("Block 1 Any", "Block 1 Any", "Block 1 Any", "+$1", "{LOCK} Glitch", "{LOCK} Glitch"),
        notes="Temp hire (max 3/rd). Never wears to Unpatched; returns to supply after Phase 2. Can sacrifice vs {GREEN} (except {YELLOW}).",
    ),
    DieSpec(
        color_key="red",
        title="RED",
        subtitle="FinSec",
        cost_str="$4",
        vp_str="3 VP",
        faces=("Block 1 {RED}", "+$2", "+$2", "+$2", "{LOCK} Glitch", "{RED} {STAR}"),
        notes="FinSec revenue & defense. Face 5 Glitch: wear 1 active die. Face 6 Red {STAR}.",
    ),
    DieSpec(
        color_key="blue",
        title="BLUE",
        subtitle="Firewall",
        cost_str="$5",
        vp_str="4 VP",
        faces=("Block 1 {BLUE}", "+1 {WRENCH}", "+$1", "Block 1 {BLUE} / +1 {WRENCH}", "{LOCK} Glitch", "{BLUE} {STAR}"),
        notes="High-VP Spyware defense & patch hybrid. Face 5 Glitch. Face 6 Blue {STAR}.",
    ),
    DieSpec(
        color_key="green",
        title="GREEN",
        subtitle="Antivirus",
        cost_str="$4",
        vp_str="3 VP",
        faces=("Block 1 {GREEN}", "+1 {WRENCH}", "+2 {WRENCH}", "+1 {WRENCH} / +$1", "{LOCK} Glitch", "{GREEN} {STAR}"),
        notes="Malware defense & patch engine. Face 5 Glitch. Face 6 Green {STAR}.",
    ),
    DieSpec(
        color_key="yellow",
        title="YELLOW",
        subtitle="Commercial AI",
        cost_str="$5",
        vp_str="4 VP",
        faces=("+$3", "+$2", "+$2", "+$1 & +1 {WRENCH}", "{YELLOW} {STAR}", "{YELLOW} {STAR}"),
        notes="COMMERCIAL EXPOSURE: Unblocked {GREEN} Malware MUST demote Ready {YELLOW} dice first (no Contractor Sacrifice!).",
    ),
    DieSpec(
        color_key="purple",
        title="PURPLE",
        subtitle="Black-Hat AI",
        cost_str="$4",
        vp_str="3 VP",
        faces=("Block 1 Any", "Block 1 Any", "+$2", "+$1 & +1 {WRENCH}", "{PURPLE} {STAR}", "{PURPLE} {STAR}"),
        notes="Flexible Any-color shields, hybrid output, and sabotage/profiteering {STAR} variants.",
    ),
]


@dataclass(frozen=True)
class VariantCardSpec:
    code: str
    color_key: str
    die_label: str
    cost_str: str
    vp_str: str
    base_summary_1: str
    base_summary_2: str
    name: str
    timing: str
    effect: str
    lock_note: str


VARIANT_CARDS: List[VariantCardSpec] = [
    # RED (R1-R3)
    VariantCardSpec(
        "R1", "red", "RED // FINSEC", "$4", "3 VP",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} {LOCK}Glitch  |  {PIP6} {STAR}",
        "Ransom Insurance", "P1 BOOT + P2 DEFENSE",
        "**Block 1 {RED} Red** in Phase 2 **AND** gain **+$2** in Phase 1 Boot.",
        "Locks in v2.0 RaaS & v3.0 Zero-Day.",
    ),
    VariantCardSpec(
        "R2", "red", "RED // FINSEC", "$4", "3 VP",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} {LOCK}Glitch  |  {PIP6} {STAR}",
        "Threat Bounty", "P2 DEFENSE + BONUS",
        "**Block 2 {RED} Red**; if you take **0 unblocked Red** damage this round, gain **+$2**.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "R3", "red", "RED // FINSEC", "$4", "3 VP",
        "{PIP1} 1{RED}  |  {PIP2}{PIP3}{PIP4} +$2", "{PIP5} {LOCK}Glitch  |  {PIP6} {STAR}",
        "Short Squeeze", "P1 BOOT + P2 SURGE",
        "Gain **+$3** in Phase 1 (or **+$4** total if **3+ {RED} Red** cubes exit the tower in Phase 2).",
        "Locks in v2.0 RaaS (Cash).",
    ),
    # BLUE (B1-B3)
    VariantCardSpec(
        "B1", "blue", "BLUE // FIREWALL", "$5", "4 VP",
        "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Honeypot Telemetry", "P2 DEFENSE + BONUS",
        "**Block 2 {BLUE} Blue**; if **1+ {BLUE} Blue** cubes exit and you take **0 Blue** damage, gain **+$3**.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "B2", "blue", "BLUE // FIREWALL", "$5", "4 VP",
        "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Deep R&D Vault", "P2 DEF -OR- P3 OPS",
        "**Block 1 {BLUE} Blue**, **OR** leave unassigned to pay **$4** in Phase 3 for **+1 Secret** (max 10).",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "B3", "blue", "BLUE // FIREWALL", "$5", "4 VP",
        "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Air-Gapped Backup", "P2 DEFENSE (WEAR REDIRECT)",
        "**Block 1 {BLUE} Blue**; when blocking, you may move **1 other Ready die** to Unpatched instead of this die.",
        "If no other Ready die, this die wears.",
    ),
    # GREEN (G1-G3)
    VariantCardSpec(
        "G1", "green", "GREEN // ANTIVIRUS", "$4", "3 VP",
        "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Self-Healing Kernel", "P1 BOOT + P2 DEFENSE",
        "**Block 2 {GREEN} Green** in Phase 2 **AND** gain **+1 {WRENCH}** in Phase 1 Boot.",
        "Locks in v3.0 Zero-Day (Shield).",
    ),
    VariantCardSpec(
        "G2", "green", "GREEN // ANTIVIRUS", "$4", "3 VP",
        "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Universal Sandbox", "P1 BOOT + P2 DEFENSE",
        "**Block 1 Any** color in Phase 2 **AND** gain **+1 {WRENCH}** in Phase 1 Boot.",
        "Commit color in Step 5. Locks in v3.0.",
    ),
    VariantCardSpec(
        "G3", "green", "GREEN // ANTIVIRUS", "$4", "3 VP",
        "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}",
        "Live Reboot", "P1 BOOT OUTPUT",
        "Gain **+2 {WRENCH}** and **+$1** immediately in Phase 1 Step 6 (max 3 {WRENCH} held).",
        "Locks in v2.0 RaaS (Cash).",
    ),
    # YELLOW (Y1-Y3)
    VariantCardSpec(
        "Y1", "yellow", "YELLOW // COMM. AI", "$5", "4 VP",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH}",
        "Algorithmic Trading", "P1 BOOT + P3 OPTION",
        "Gain **+$4** in Phase 1; in Phase 3 you may also pay **$2** to gain **+1 Secret** (max 10).",
        "Commercial Exposure. Locks in v2.0 RaaS.",
    ),
    VariantCardSpec(
        "Y2", "yellow", "YELLOW // COMM. AI", "$5", "4 VP",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH}",
        "Cloud Monopoly", "P1 SCALING REVENUE",
        "Gain **+$2**, plus **+$1 per different colored** module die you own (**max +$5** total).",
        "Counts R/B/G/Y/P owned. Locks in v2.0.",
    ),
    VariantCardSpec(
        "Y3", "yellow", "YELLOW // COMM. AI", "$5", "4 VP",
        "{PIP1} +$3   {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH}",
        "Proprietary Training", "P1 SECRET + SELF-WEAR",
        "Gain **+1 Corporate Secret** in Phase 1 Step 6, then immediately move **this die to Unpatched**.",
        "Commercial Exposure applies while Ready.",
    ),
    # PURPLE (P1-P3)
    VariantCardSpec(
        "P1", "purple", "PURPLE // BLK-HAT", "$4", "3 VP",
        "{PIP1}{PIP2} Block 1 Any", "{PIP3} +$2  |  {PIP4} +$1 & 1{WRENCH}",
        "Zero-Day Injection", "P1 BOOT + P3 SABOTAGE",
        "Gain **+$2** in Phase 1; in Phase 3 you may add **1 Attack Cube** ({RED}/{BLUE}/{GREEN}) to Staging Cup.",
        "No Black cube added. Locks in v2.0 RaaS.",
    ),
    VariantCardSpec(
        "P2", "purple", "PURPLE // BLK-HAT", "$4", "3 VP",
        "{PIP1}{PIP2} Block 1 Any", "{PIP3} +$2  |  {PIP4} +$1 & 1{WRENCH}",
        "Chaos Profiteer", "P1 BOOT + P2 PAYOUT",
        "Gain **+$1** in Phase 1, plus **+$2 per {BLACK} Black Cube** that exits the tower in Phase 2.",
        "Locks in v2.0 RaaS (Cash).",
    ),
    VariantCardSpec(
        "P3", "purple", "PURPLE // BLK-HAT", "$4", "3 VP",
        "{PIP1}{PIP2} Block 1 Any", "{PIP3} +$2  |  {PIP4} +$1 & 1{WRENCH}",
        "Packet Deflection", "P2 DEF + P3 SABOTAGE",
        "**Block 2** of any 1 color; in Phase 3 you may pay **$1** to add **1 cube of that color** to Staging Cup.",
        "Commit color in Step 5. Locks in v3.0.",
    ),
]


@dataclass(frozen=True)
class VersionTileSpec:
    version: str
    name: str
    profile: str
    payload_label: str
    payload_3p4p: str
    payload_2p: str
    directive_title: str
    directive_body: str


VERSION_TILES: List[VersionTileSpec] = [
    VersionTileSpec(
        version="v3.0",
        name="Zero-Day Override",
        profile="SINGULARITY",
        payload_label="UPGRADE",
        payload_3p4p="+1 {RED}  +1 {BLACK}",
        payload_2p="All Counts",
        directive_title="Kernel Lock",
        directive_body=(
            "Any rolled die showing a **Shield** (Block 1/2, Shield `/` Choice, or Shield {STAR}) "
            "is **{LOCK} Locked** immediately (spend 1 {WRENCH} to unlock)."
        ),
    ),
    VersionTileSpec(
        version="v3.0",
        name="Corrupted Kernel",
        profile="KINETIC",
        payload_label="UPGRADE",
        payload_3p4p="+1 {RED}  +1 {BLUE}",
        payload_2p="All Counts",
        directive_title="Overclocked Surge",
        directive_body=(
            "If **2+ {BLACK} Black Cubes** exit the tower in Phase 2, the Attack Color "
            "({RED}/{BLUE}/{GREEN}) with the **most exited cubes** gains **+2 Strength** (tie: {RED}>{BLUE}>{GREEN})."
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="Ransomware-as-a-Service",
        profile="KINETIC",
        payload_label="UPGRADE",
        payload_3p4p="+1 {RED}  +1 {GREEN}",
        payload_2p="All Counts",
        directive_title="Encrypted Memory",
        directive_body=(
            "Any rolled die showing **Cash** (+$1/+$2/+$3, Cash `/` Choice, or Cash {STAR}) "
            "is **{LOCK} Locked** immediately (spend 1 {WRENCH} to unlock)."
        ),
    ),
    VersionTileSpec(
        version="v2.0",
        name="Polymorphic Worm",
        profile="CONTAGION",
        payload_label="UPGRADE",
        payload_3p4p="+1 {GREEN}  +1 {BLACK}",
        payload_2p="All Counts",
        directive_title="Subroutine Throttling",
        directive_body=(
            "Players receive only **1 free reroll** during Phase 1 Step 4 (instead of the normal 2 free rerolls)."
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Script Kiddie",
        profile="BASELINE",
        payload_label="START CUP",
        payload_3p4p="1 {RED}  1 {BLUE}  1 {GREEN}  1 {BLACK}",
        payload_2p="All Counts",
        directive_title="No Active Directive",
        directive_body=(
            "Standard initial compile protocol. Place Starting Payload into the Staging Cup during game setup."
        ),
    ),
    VersionTileSpec(
        version="v1.0",
        name="Data Scraper",
        profile="BREACH PROBE",
        payload_label="START CUP",
        payload_3p4p="1 {RED}  2 {BLUE}  1 {BLACK}",
        payload_2p="All Counts",
        directive_title="Seed Capital Leak",
        directive_body=(
            "**Setup:** All players start with **+$1 extra Money** ($8 total instead of $7). No ongoing Phase 1-3 restriction."
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
# 1. Individual Player Boards (6 Pages — Matches Wireframe Page 1)
# =============================================================================

def render_player_board(page: PDFPage, char: CharacterSpec, idx: int) -> None:
    draw_board_outer_frame(
        page,
        left_tag=f"TOO MANY SECRETS // CONSULTANCY TERMINAL [{idx}/6]",
        right_tag="PNP PROTOTYPE v0.11 // US LETTER",
    )

    # -------------------------------------------------------------------------
    # LEFT COLUMN (x = 40..278, w = 238)
    # -------------------------------------------------------------------------
    lx, lw = 40.0, 238.0
    lcx = lx + lw / 2.0

    # 1. <Player Character Name>
    page.text(lcx, 45.0, char.name.upper(), font="bold", size=14.0, color=PALETTE["ink"], align="center")
    page.text(lcx, 56.5, char.role.upper(), font="mono", size=6.8, color=PALETTE["muted"], align="center")

    # 2. Portrait / Schematic Box (367 x 358 wireframe zone)
    draw_character_illustration(page, char.code, lx, 64.0, lw, 206.0)

    # 3. Flavor Text Box
    fy, fh = 277.0, 39.0
    page.rect(lx, fy, lw, fh, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.9)
    page.rich_paragraph(
        lx + 8, fy + 15.0, lw - 16,
        f"*{char.flavor}*",
        size=7.4, leading=10.2, color=PALETTE["ink_soft"], align="center",
    )

    # 4. Special Ability Description Box (with integrated 1x/Version Track)
    ay, ah = 323.0, 133.0
    page.rect(lx, ay, lw, ah, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    # Header strip
    page.rect(lx, ay, lw, 20.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(lx + 7, ay + 13.5, char.ability_name.upper(), font="bold", size=8.6, color=PALETTE["ink"])
    # Timing pill
    tw = measure_text(char.timing, font="mono_bold", size=6.3) + 8.0
    page.rounded_rect(lx + lw - tw - 5, ay + 3.5, tw, 13.0, r=2.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.6)
    page.text(lx + lw - 5 - tw / 2.0, ay + 12.2, char.timing, font="mono_bold", size=6.3, color=PALETTE["ink"], align="center")

    # Ability body description
    page.rich_paragraph(
        lx + 8, ay + 34.0, lw - 16,
        char.ability_desc,
        size=7.9, leading=11.0, color=PALETTE["ink"],
    )

    # Bottom Once-Per-Version Ability Track inside Special Ability Box
    ty = ay + ah - 37.0
    page.line(lx + 6, ty, lx + lw - 6, ty, stroke=PALETTE["rule"], width=0.6, dash=(2, 1.5))
    page.text(lx + 8, ty + 14.5, "ONCE / VER:", font="mono_bold", size=6.5, color=PALETTE["ink_soft"])
    slots = ["v1.0", "v2.0", "v3.0"]
    sx_start = lx + 68.0
    sw_box = 50.0
    for s_idx, ver_lbl in enumerate(slots):
        bx = sx_start + s_idx * (sw_box + 5.0)
        page.rounded_rect(bx, ty + 4.0, sw_box, 17.0, r=2.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.75)
        # Checkbox square on left of pill
        page.rect(bx + 4.0, ty + 7.5, 10.0, 10.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.7)
        page.text(bx + 18.0, ty + 15.2, ver_lbl, font="mono_bold", size=7.2, color=PALETTE["ink"])
    page.text(lcx, ay + ah - 4.5, "Unused charge forfeits when SETEC upgrades; new version unlocks immediately.", font="italic", size=6.1, color=PALETTE["muted"], align="center")

    # -------------------------------------------------------------------------
    # RIGHT COLUMN (x = 292..752, w = 460)
    # -------------------------------------------------------------------------
    rx, rw = 292.0, 460.0

    # 1. Ready Zone
    ry, rh = 36.0, 98.0
    page.rect(rx, ry, rw, rh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, ry, rw, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(rx + 8, ry + 13.0, "READY ZONE", font="bold", size=9.2, color=PALETTE["ink"])
    page.rich_line(
        rx + rw - 8, ry + 13.0,
        "Start: **4** {GRAY} Gray Dice  |  Phase 1: Roll all Ready + hired {WHITE} Contractors",
        size=7.0, color=PALETTE["ink_soft"], align="right",
    )
    # Subtle 16mm die placement guides (8 faint slots across top-center of Ready Zone)
    slot_s = 44.0
    gap_s = 10.0
    row_w = 8 * slot_s + 7 * gap_s
    gx0 = rx + (rw - row_w) / 2.0
    gy0 = ry + 32.0
    for i in range(8):
        gx = gx0 + i * (slot_s + gap_s)
        page.rounded_rect(gx, gy0, slot_s, slot_s, r=4.0, stroke=PALETTE["rule"], fill=None, line_width=0.65, dash=(2.5, 2.0))
        if i < 4:
            page.text(gx + slot_s / 2.0, gy0 + slot_s / 2.0 + 2.5, "START", font="mono", size=6.0, color=PALETTE["watermark"], align="center")

    # 2. Active Zone
    act_y, act_h = 144.0, 82.0
    page.rect(rx, act_y, rw, act_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, act_y, rw, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(rx + 8, act_y + 13.0, "ACTIVE ZONE", font="bold", size=9.2, color=PALETTE["ink"])
    page.rich_line(
        rx + rw - 8, act_y + 13.0,
        "Max **2 Free Rerolls**  |  Spend **1** {WRENCH} to Unlock **1** {LOCK} Die  |  Unassigned yield **$** & {WRENCH}",
        size=6.9, color=PALETTE["ink_soft"], align="right",
    )
    page.text(rx + rw / 2.0, act_y + 54.0, "ROLLED POOL  //  DECLARE ( / ) CHOICES & ASSIGN SHIELDS BEFORE COLLECTING OUTPUTS", font="mono", size=6.4, color=PALETTE["watermark"], align="center")

    # 3. Shield Row (Red Shields | Blue Shields | Green Shields)
    sh_y, sh_h = 236.0, 114.0
    sh_gap = 11.0
    sh_w = (rw - 2 * sh_gap) / 3.0
    shield_defs = [
        ("red", "{RED} RED SHIELDS", "Blocks Ransomware", "Unblocked: -$1 -> {WRENCH} -> -1 Secret"),
        ("blue", "{BLUE} BLUE SHIELDS", "Blocks Spyware", "Unblocked: -1 Corporate Secret"),
        ("green", "{GREEN} GREEN SHIELDS", "Blocks Malware", "Unblocked: Wear 1 Ready ({YELLOW} 1st!)"),
    ]
    for i, (ckey, title_mk, sub1, sub2) in enumerate(shield_defs):
        sx = rx + i * (sh_w + sh_gap)
        fg, bg = _color_pair(ckey)
        page.rect(sx, sh_y, sh_w, sh_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
        # Top colored accent bar + header
        page.rect(sx, sh_y, sh_w, 21.0, stroke=PALETTE["ink"], fill=bg, line_width=0.8)
        page.rect(sx, sh_y, sh_w, 3.2, stroke=None, fill=fg)
        page.rich_line(sx + sh_w / 2.0, sh_y + 15.2, f"**{title_mk}**", size=8.4, color=fg, align="center")
        # 2 subtle die guides inside each shield box
        ds = 42.0
        dx0 = sx + (sh_w - (2 * ds + 10.0)) / 2.0
        for d_i in range(2):
            page.rounded_rect(dx0 + d_i * (ds + 10.0), sh_y + 34.0, ds, ds, r=4.0, stroke=PALETTE["rule"], fill=None, line_width=0.65, dash=(2.5, 2.0))
        page.text(sx + sh_w / 2.0, sh_y + 93.0, sub1, font="bold", size=6.8, color=PALETTE["ink_soft"], align="center")
        page.rich_line(sx + sh_w / 2.0, sh_y + 105.0, sub2, size=6.3, color=PALETTE["muted"], align="center")

    # Wear transition caption between Shields and Unpatched Zone
    page.text(
        rx + rw / 2.0, 360.5,
        "DICE WEAR: Permanent Shields blocking >= 1 cube move to Unpatched Zone  |  0 cubes blocked = stay Ready  |  Contractors -> Supply",
        font="italic", size=6.5, color=PALETTE["ink_soft"], align="center",
    )

    # 4. Unpatched Zone (bottom-aligned with Special Ability Description at y = 456!)
    up_y, up_h = 366.0, 90.0
    page.rect(rx, up_y, rw, up_h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx, up_y, rw, 19.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.8)
    page.text(rx + 8, up_y + 13.0, "UNPATCHED ZONE", font="bold", size=9.2, color=PALETTE["ink"])
    page.rich_line(
        rx + rw - 8, up_y + 13.0,
        "Offline (Do Not Roll)  |  **Phase 3 Patch:** Pay **1** {WRENCH} or **$2** per die -> Ready Zone",
        size=7.0, color=PALETTE["ink_soft"], align="right",
    )
    # Subtle hazard diagonal ticks along bottom strip
    for hx in range(int(rx + 12), int(rx + rw - 16), 18):
        page.line(hx, up_y + up_h - 8, hx + 6, up_y + up_h - 2, stroke=PALETTE["guide"], width=1.0)
    page.text(rx + rw / 2.0, up_y + 56.0, "WORN & DEMOTED MODULES  //  IF 0 READY/CONTRACTOR DICE VS GREEN MALWARE: DESTROY 1 UNPATCHED DIE", font="mono", size=6.3, color=PALETTE["muted"], align="center")

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
    page.text(mx + bw - 8, by + 13.8, "1 VP per $2", font="mono_bold", size=7.5, color=PALETTE["ink_soft"], align="right")
    page.text(mx + bw / 2.0, by + 66.0, "$", font="bold", size=28.0, color=PALETTE["guide"], align="center")
    page.text(mx + bw / 2.0, by + bh - 7.0, "Start: $7 (+$1 Data Scraper)  |  Never drops below $0", font="regular", size=6.7, color=PALETTE["muted"], align="center")

    # 2. Patches (with 3 dedicated token slots enforcing Max 3 🔧!)
    px = mx + bw + bgap
    page.rect(px, by, bw, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(px, by, bw, 20.0, stroke=PALETTE["ink"], fill=PALETTE["green_light"], line_width=0.8)
    page.rich_line(px + 8, by + 13.8, "{WRENCH} **PATCHES**", size=9.2, color=PALETTE["green"])
    page.text(px + bw - 8, by + 13.8, "MAX 3  |  0 VP", font="mono_bold", size=7.4, color=PALETTE["green"], align="right")

    ps_size = 50.0
    ps_gap = 12.0
    ps_x0 = px + (bw - (3 * ps_size + 2 * ps_gap)) / 2.0
    ps_y = by + 30.0
    for p_i in range(3):
        sx = ps_x0 + p_i * (ps_size + ps_gap)
        page.rounded_rect(sx, ps_y, ps_size, ps_size, r=6.0, stroke=PALETTE["muted"], fill=PALETTE["paper_tint"], line_width=0.75, dash=(3, 2))
        lbl = f"SLOT {p_i + 1}" if p_i < 2 else "MAX (3)"
        page.text(sx + ps_size / 2.0, ps_y + 13.0, lbl, font="mono", size=5.8, color=PALETTE["muted"], align="center")
        page.draw_wrench_icon(sx + ps_size / 2.0, ps_y + 31.0, 14.0, color=PALETTE["rule"])
    page.rich_line(px + bw / 2.0, by + bh - 7.0, "Start: **2** Tokens  |  Unlock {LOCK} / Patch / Auto-Absorb $1 {RED}", size=6.5, color=PALETTE["muted"], align="center")

    # 3. Secrets
    scx = px + bw + bgap
    page.rect(scx, by, bw, bh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(scx, by, bw, 20.0, stroke=PALETTE["ink"], fill=PALETTE["blue_light"], line_width=0.8)
    page.rich_line(scx + 8, by + 13.8, "{SECRET} **SECRETS**", size=9.2, color=PALETTE["blue"])
    page.text(scx + bw - 8, by + 13.8, "4 VP EACH", font="mono_bold", size=7.5, color=PALETTE["blue"], align="right")
    page.draw_secret_icon(scx + bw / 2.0, by + 56.0, 26.0, color=PALETTE["guide"])
    page.text(scx + bw / 2.0, by + bh - 16.5, "Start: 8 Secrets (2P/3P)  |  10 Secrets (4P)", font="regular", size=6.7, color=PALETTE["ink_soft"], align="center")
    page.text(scx + bw / 2.0, by + bh - 6.0, "<= 0 SECRETS = TOTAL DATA BREACH (PATIENT ZERO)", font="bold", size=6.5, color=PALETTE["red"], align="center")


# =============================================================================
# 2A. Central SETEC Agent Board (Matches Wireframe Page 2)
# =============================================================================

def render_agent_board(page: PDFPage) -> None:
    draw_board_outer_frame(
        page,
        left_tag="PROJECT: SETEC // CENTRAL ROGUE AGENT & COMPILER BOARD [1/2]",
        right_tag="PNP PROTOTYPE v0.11 // US LETTER",
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
    page.rich_line(slot_x + slot_w / 2.0, ct_y + 13.5, "**CORRUPTION TRACK**  (4 [2P] / 5 [3P] / 6 [4P] SPACES)", size=7.5, color=PALETTE["white"], align="center")

    # 6 Cube Spaces inside Corruption Track
    sq_s = 28.0
    sq_gap = 7.0
    sq_x0 = slot_x + (slot_w - (6 * sq_s + 5 * sq_gap)) / 2.0
    sq_y = ct_y + 27.0
    track_meta = [
        ("1", "BLACK", False),
        ("2", "BLACK", False),
        ("3", "BLACK", False),
        ("4!", "2P UP", True),
        ("5!", "3P UP", True),
        ("6!", "4P UP", True),
    ]
    for c_i, (lbl_num, sub_lbl, is_milestone) in enumerate(track_meta):
        cx_box = sq_x0 + c_i * (sq_s + sq_gap)
        page.rounded_rect(
            cx_box, sq_y, sq_s, sq_s, r=3.0,
            stroke=PALETTE["red"] if is_milestone else PALETTE["ink"],
            fill=PALETTE["red_light"] if is_milestone else PALETTE["paper_tint"],
            line_width=1.1 if is_milestone else 0.8,
        )
        page.text(
            cx_box + sq_s / 2.0, sq_y + 14.5,
            lbl_num,
            font="bold", size=8.5,
            color=PALETTE["red"] if is_milestone else PALETTE["ink"],
            align="center",
        )
        page.text(
            cx_box + sq_s / 2.0, sq_y + 24.5,
            sub_lbl,
            font="mono", size=5.0,
            color=PALETTE["red"] if is_milestone else PALETTE["muted"],
            align="center",
        )
        if c_i < 5:
            page.text(cx_box + sq_s + sq_gap / 2.0, sq_y + 18.0, ">", font="mono_bold", size=6.0, color=PALETTE["muted"], align="center")

    page.rich_paragraph(
        slot_x + 6.0, ct_y + 76.0, slot_w - 12.0,
        "**Step 2A:** Place exited {BLACK} 1-by-1. Fills at **4 (2P) / 5 (3P) / 6 (4P)**: clear track, advance Version, add Payload -> Staging Cup (**v3.0 fill = SINGULARITY**).",
        size=6.2, leading=8.3, color=PALETTE["ink_soft"], align="center",
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
                "Advance **Corruption Track** 1 space per exited {BLACK}.\n"
                "**4th Space:** Clear track, move to next Version, add Upgrade Payload to Staging Cup, "
                "apply new Directive **immediately**, & flip Archetype ability slots. **(v3.0 4th = SINGULARITY!)**"
            ),
            88.0,
        ),
        (
            "red",
            "{RED} RED // RANSOMWARE",
            "BLOCKS: {RED} SHIELD",
            (
                "Lose **$1** per unblocked {RED} cube.\n"
                "**Patch Absorption:** At **$0**, each held {WRENCH} token auto-absorbs **$1** unpaid ransom.\n"
                "**Ransom Leak:** Any remaining unpaid $1 loses **1 Secret** each! *(Cash min $0).*"
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
                "Move **1 Ready die -> Unpatched** per unblocked {GREEN}.\n"
                "**Commercial Exposure:** Ready {YELLOW} **Yellow** dice MUST be demoted first!\n"
                "**Sacrifice:** Discard 1 {WHITE} Contractor instead of non-Yellow Ready die.\n"
                "**Overwhelmed:** If 0 Ready/Contractor left, **Destroy 1 Unpatched die**!"
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
        "**WEAR:** Permanent Shields blocking >=1 cube -> **Unpatched** *(0 blocked = stay Ready)*.\n"
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
            "PHASE 1: BOOT & CONFIGURE (Simultaneous)",
            (
                "**1. Pulse:** Add **+1** {BLACK} Black Cube -> Staging Cup.\n"
                "**2. Temp Staffing:** Hire {WHITE} Contractors (**$1** / **$2** / **$3**, max 3).\n"
                "**3. Roll Pool:** Roll Ready Zone + Contractors -> Active Zone.\n"
                "**4. Rerolls & Debug:** Up to **2 free rerolls** of unlocked dice. Spend **1** {WRENCH} (or lock a rolled +1 {WRENCH} die) to **Unlock 1** {LOCK} die.\n"
                "**5. Assign:** Commit Shields (`Any` -> {RED}/{BLUE}/{GREEN}) & `/` Choices.\n"
                "**6. Outputs:** Unassigned dice yield **$**, {WRENCH} *(max 3)*, & Boot {STAR}."
            ),
        ),
        (
            "PHASE 2: SETEC COMPILE (Simultaneous)",
            (
                "**Drop** entire Staging Cup into Cube Tower.\n"
                "**2A.** Resolve {BLACK} Black Cubes on Corruption Track.\n"
                "**2B.** Resolve {RED} {BLUE} {GREEN} vs Shields; apply Wear & Damage; recycle exited {RED} {BLUE} {GREEN} -> Staging Cup.\n"
                "**Empty Tray (Buffer Overflow):** If 0 cubes exit into tray, no corruption/attacks occur (shields stay Ready). Idle cycle injects **+1** {RED}, **+1** {BLUE}, **+1** {GREEN} from supply into Staging Cup for next round.\n"
                "**2C. End Check:** **Singularity** OR any player **<= 0 Secrets** triggers **Final Round** *(Patient Zero skips P3; survivors take 1 final P3; skip P3 if ALL breach)*."
            ),
        ),
        (
            "PHASE 3: OPERATIONS (Clockwise Turns)",
            (
                "- **Buy Dice (max 2/turn):** Pay $ -> place in **Ready Zone**.\n"
                "- **Patch Dice (unlimited):** **1** {WRENCH} or **$2** each -> **Ready Zone**.\n"
                "- **Backdoor Siphon (max 1/turn):** *(Need >=2 Secrets & >=1 Ready)* Pay **1 Secret** + demote **1 Ready -> Unpatched** + **1** {BLACK} -> Staging Cup => Gain **+$3**.\n"
                "- **Cleanup:** Un-worn dice -> Ready; pass 1st Player clockwise."
            ),
        ),
        (
            "END-GAME PORTFOLIO SCORING",
            (
                "**Surviving Firms Only** *(Patient Zero eliminated)*:\n"
                "**4 VP** / Secret  |  **3-4 VP** / Ready Die (Unpatched = 0)  |  **1 VP** / **$2**  |  {WRENCH} = 0 VP.\n"
                "*Ties: 1. Secrets, 2. Cash. (Total Wipeout: -4 VP/Secret <0, -3 VP/unfulfilled destroy).*"
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
        right_tag="PNP PROTOTYPE v0.11 // US LETTER",
    )

    # Top Title Bar
    page.rect(40.0, 32.0, 712.0, 24.0, stroke=PALETTE["ink"], fill=PALETTE["ink"], line_width=1.0)
    page.text(50.0, 48.0, "SOFTWARE MODULE MARKET  &  CENTRAL COMPILER SUPPLY", font="bold", size=10.5, color=PALETTE["white"])
    page.text(742.0, 47.5, "DEAL 1 VARIANT (STAR) CARD PER COLOR  |  STACK 2x PLAYERS DICE", font="mono", size=7.2, color=PALETTE["rule"], align="right")

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
        "- **P1 Start:** +1 {BLACK}\n"
        "- **P2 End:** Recycled {RED}{BLUE}{GREEN}\n"
        "- **Upgrade:** Version Payload\n"
        "- **Siphon:** +1 {BLACK}",
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
        "Hire in **Phase 1 Step 2** (max 3/round = $6). Never wears to Unpatched; returns to supply after Phase 2. May sacrifice vs {GREEN} *(except {YELLOW} Yellow)*.",
        size=6.4, leading=8.8, color=PALETTE["ink_soft"], align="center",
    )

    # -------------------------------------------------------------------------
    # MIDDLE ROW: 5 Software Module Market Slots (x = 40..752, y = 200..498)
    # Sized so 120 x 182 pt Variant (★) Market Cards drop cleanly inside!
    # -------------------------------------------------------------------------
    my, mh = 200.0, 298.0
    mgap = 10.5
    mw = (712.0 - 4 * mgap) / 5.0  # 134.0 pt wide each!

    market_colors = [
        ("red", "RED // FINSEC", "$4", "3 VP", "{PIP1} 1{RED} | {PIP2}-{PIP4} +$2", "{PIP5} {LOCK}Glitch | {PIP6} {STAR}", ""),
        ("blue", "BLUE // FIREWALL", "$5", "4 VP", "{PIP1} 1{BLUE} | {PIP2} +1{WRENCH} | {PIP3} +$1", "{PIP4} 1{BLUE}/1{WRENCH} | {PIP5} {LOCK}Glitch | {PIP6} {STAR}", ""),
        ("green", "GREEN // ANTIVIRUS", "$4", "3 VP", "{PIP1} 1{GREEN} | {PIP2} +1{WRENCH} | {PIP3} +2{WRENCH}", "{PIP4} 1{WRENCH}/$1 | {PIP5} {LOCK}Glitch | {PIP6} {STAR}", ""),
        ("yellow", "YELLOW // COMM.", "$5", "4 VP", "{PIP1} +$3 | {PIP2}{PIP3} +$2", "{PIP4} +$1 & +1{WRENCH}", "EXPOSURE: {GREEN} hits {YELLOW} 1st!"),
        ("purple", "PURPLE // BLK-HAT", "$4", "3 VP", "{PIP1}{PIP2} Block 1 Any", "{PIP3} +$2 | {PIP4} $1 & 1{WRENCH}", ""),
    ]

    for idx, (ckey, mtitle, mcost, mvp, f_row1, f_row2, passive_warn) in enumerate(market_colors):
        sx = 40.0 + idx * (mw + mgap)
        fg, bg = _color_pair(ckey)
        page.rect(sx, my, mw, mh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
        # Header
        page.rect(sx, my, mw, 22.0, stroke=PALETTE["ink"], fill=bg, line_width=0.8)
        page.rect(sx, my, mw, 3.5, stroke=None, fill=fg)
        page.draw_color_badge(sx + 11.0, my + 12.5, 9.0, ckey)
        page.text(sx + 20.0, my + 15.2, mtitle, font="bold", size=7.6, color=fg)

        # Cost / VP / Stock strip
        page.rect(sx, my + 22.0, mw, 17.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
        page.text(sx + 7.0, my + 33.5, f"COST: {mcost}", font="bold", size=7.8, color=PALETTE["ink"])
        page.text(sx + mw - 7.0, my + 33.5, f"{mvp}  (2xP)", font="mono_bold", size=7.0, color=PALETTE["ink_soft"], align="right")

        # Base Faces 1-4 summary above card slot
        page.rich_line(sx + mw / 2.0, my + 52.0, f_row1, size=6.8, color=PALETTE["ink"], align="center")
        page.rich_line(sx + mw / 2.0, my + 65.5, f_row2, size=6.6, color=PALETTE["ink"], align="center")
        if passive_warn:
            page.rich_line(sx + mw / 2.0, my + 77.5, passive_warn, size=6.0, color=PALETTE["red"], align="center")
        else:
            page.rich_line(sx + mw / 2.0, my + 77.5, "{PIP5}{PIP6} = Active {STAR} Card Below", size=6.1, color=PALETTE["muted"], align="center")

        # Card Slot (124 x 190 pt -> holds 120 x 182 pt Variant ★ Card with 2-4 pt margin!)
        cs_w, cs_h = 124.0, 190.0
        cs_x = sx + (mw - cs_w) / 2.0
        cs_y = my + mh - cs_h - 6.0  # 200 + 298 - 196 = 302.0
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
        "- **2P:** $7 | **8 Secrets** | **2** {WRENCH} | **4 Dice/col** | *Track: 4 spaces*\n"
        "- **3P:** $7 | **8 Secrets** | **2** {WRENCH} | **6 Dice/col** | *Track: 5 spaces*\n"
        "- **4P:** $7 | **10 Secrets** | **2** {WRENCH} | **8 Dice/col** | *Track: 6 spaces*\n"
        "- **Setup:** Standard 2-cube payloads (all counts). Prime compiler: drop 1 R/B/G/Black stuck into tower.",
        size=6.2, leading=8.7, color=PALETTE["ink"],
    )

    # Right: Portfolio Scoring & End-Game Triggers
    rx_f = 40.0 + fw + 14.0
    page.rect(rx_f, fy, fw, fh, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.rect(rx_f, fy, fw, 16.5, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=0.7)
    page.text(rx_f + 8.0, fy + 11.8, "PORTFOLIO VALUE SCORING  (SURVIVING CONSULTANCIES)", font="bold", size=7.8, color=PALETTE["ink"])
    page.rich_paragraph(
        rx_f + 8.0, fy + 29.0, fw - 16.0,
        "- **Secrets:** **4 VP** each   |   **Cash:** **1 VP** per **$2** *(rounded down)*   |   **Patches ({WRENCH}):** **0 VP**\n"
        "- **Ready Colored Dice:** {BLUE} Blue / {YELLOW} Yellow = **4 VP**  |  {RED} Red / {GREEN} Green / {PURPLE} Purple = **3 VP**  |  (Unpatched = **0 VP**! | {GRAY}/{WHITE} = **0 VP**)\n"
        "- *Patient Zero (<=0 Secrets) eliminated! Wipeout only: -4 VP per Secret <0, -3 VP per unfulfilled destroy.*",
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
    page.text(tx + col_die + col_meta / 2.0, ty + 18.0, "COST / VP", font="bold", size=7.6, color=PALETTE["ink"], align="center")

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
        if dspec.color_key == "yellow":
            page.text(tx + 12.0, ry + 46.5, "EXPOSURE PASSIVE!", font="mono_bold", size=6.0, color=PALETTE["red"])
        elif dspec.color_key == "white":
            page.text(tx + 12.0, ry + 46.5, "NO WEAR / TEMP", font="mono_bold", size=6.0, color=PALETTE["muted"])

        # Cost / VP cell
        mx = tx + col_die
        page.line(mx, ry, mx, ry + row_h, stroke=PALETTE["rule"], width=0.7)
        page.text(mx + col_meta / 2.0, ry + 23.0, dspec.cost_str, font="bold", size=8.0, color=PALETTE["ink"], align="center")
        page.text(mx + col_meta / 2.0, ry + 38.0, dspec.vp_str, font="mono_bold", size=7.6, color=PALETTE["blue"] if "4" in dspec.vp_str else PALETTE["muted"], align="center")

        # 6 Face cells
        for f_idx, f_mk in enumerate(dspec.faces):
            fx = mx + col_meta + f_idx * col_face
            page.line(fx, ry, fx, ry + row_h, stroke=PALETTE["rule"], width=0.7)
            is_star = "{STAR}" in f_mk
            is_glitch = "Glitch" in f_mk
            is_choice = "/" in f_mk

            if is_star:
                page.rounded_rect(fx + 5.0, ry + 7.0, col_face - 10.0, row_h - 14.0, r=3.0, stroke=fg, fill=bg, line_width=0.7)
                page.rich_line(fx + col_face / 2.0, ry + 26.5, f"**{f_mk}**", size=8.2, color=fg, align="center")
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
                "- **Ampersand ( & ):** Gain **both** outputs in Step 6 *(+$1 & +1 {WRENCH})*.\n"
                "- **Any Shield:** Must commit to {RED}, {BLUE}, or {GREEN} before Phase 2."
            ),
        ),
        (
            "LOCKED DICE ({LOCK}) & DEBUG ({WRENCH})",
            (
                "- **{LOCK} Locked** dice cannot be rerolled during free rerolls.\n"
                "- **v2.0 RaaS** locks any face with a **Cash** option *(incl. `/` & {STAR})*.\n"
                "- **v3.0 Zero-Day** locks any face with a **Shield** option *(incl. `/` & {STAR})*.\n"
                "- **Debug:** Spend **1** {WRENCH} *(or lock a rolled +1 {WRENCH} die)* to Unlock 1 die."
            ),
        ),
        (
            "COMMERCIAL EXPOSURE ({YELLOW} YELLOW)",
            (
                "- {YELLOW} **Yellow Commercial** dice provide top revenue & 4 VP, but have **0 Shields** and attract malware.\n"
                "- When taking unblocked {GREEN} **Green Malware**, **Ready {YELLOW} Yellow dice MUST be demoted to Unpatched first** *(Contractor Sacrifice cannot save {YELLOW})*!"
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
        ("gray", "GRAY", "Start / 0V", ("1 Any", "1 Any", "+$1", "+$1", "$1 / 1{WRENCH}", "+1{WRENCH}")),
        ("white", "WHITE", "$1-$3 / 0V", ("1 Any", "1 Any", "1 Any", "+$1", "{LOCK}Glitch", "{LOCK}Glitch")),
        ("red", "RED", "$4 / 3 VP", ("1 {RED}", "+$2", "+$2", "+$2", "{LOCK}Glitch", "{RED} {STAR}")),
        ("blue", "BLUE", "$5 / 4 VP", ("1 {BLUE}", "+1{WRENCH}", "+$1", "1{BLUE}/1{WRENCH}", "{LOCK}Glitch", "{BLUE} {STAR}")),
        ("green", "GREEN", "$4 / 3 VP", ("1 {GREEN}", "+1{WRENCH}", "+2{WRENCH}", "1{WRENCH}/$1", "{LOCK}Glitch", "{GREEN} {STAR}")),
        ("yellow", "YELLOW*", "$5 / 4 VP", ("+$3", "+$2", "+$2", "$1 & 1{WRENCH}", "{YELLOW} {STAR}", "{YELLOW} {STAR}")),
        ("purple", "PURPLE", "$4 / 3 VP", ("1 Any", "1 Any", "+$2", "$1 & 1{WRENCH}", "{PURPLE} {STAR}", "{PURPLE} {STAR}")),
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
            page.text(x + c_name + c_cost / 2.0, ty + 12.2, "$/VP", font="bold", size=6.5, color=PALETTE["ink"], align="center")
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
                x + 6.0, fy + 10.5, cw - 12.0,
                "**P1:** +1{BLACK} -> Hire {WHITE} ($1/$2/$3) -> Roll -> 2 Free Rerolls *(1{WRENCH} unlocks {LOCK})* -> Shields & `/` -> Glitch Backlash *(Wear 1 or sacrifice {WHITE})* -> Gain **$** & {WRENCH}.\n"
                "**P2:** {BLACK} Track (4/5/6=Upgr) -> Shields *(hit->Unpatched)* -> Dmg: {RED}-$1->{WRENCH}->Secret | {BLUE}-1 Secret | {GREEN}Wear Ready *({YELLOW}* 1st!). *(0 cubes exit = Buffer Overflow: +1 R/B/G to Cup for next compile)*.\n"
                "**P3:** **Buy <=2** | **Patch:** 1{WRENCH} or $2 | **Siphon (1x):** -1 Secret, +1{BLACK}, Wear 1 Ready => **+$3**.  **VP:** Secret=4, Ready Die=3/4 (Unpatched=0), $2=1.",
                size=5.6, leading=8.1, color=PALETTE["ink"],
            )


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

    # Cost & VP Sub-bar
    page.rect(x, y + 22.0, w, 14.5, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.6)
    page.text(x + 6.0, y + 31.8, f"COST: {card.cost_str}", font="bold", size=6.9, color=PALETTE["ink"])
    page.text(x + w - 6.0, y + 31.8, f"VALUE: {card.vp_str}", font="mono_bold", size=6.6, color=PALETTE["ink_soft"], align="right")

    # Base Faces 1-4 Mini Reference
    page.rich_line(x + w / 2.0, y + 48.0, card.base_summary_1, size=6.1, color=PALETTE["ink_soft"], align="center")
    page.rich_line(x + w / 2.0, y + 59.5, card.base_summary_2, size=5.9, color=PALETTE["ink_soft"], align="center")

    # Prominent Faces 5 & 6 (★) Variant Box
    sy = y + 66.0
    sh = h - 66.0 - 18.0  # 98 pt tall
    page.rect(x + 5.0, sy, w - 10.0, sh, stroke=fg, fill=PALETTE["white"], line_width=0.9)
    page.rect(x + 5.0, sy, w - 10.0, 17.5, stroke=fg, fill=bg, line_width=0.6)
    page.draw_pip_die(x + 14.5, sy + 8.8, 10.5, 5)
    page.draw_pip_die(x + 27.0, sy + 8.8, 10.5, 6)
    page.rich_line(x + w - 9.0, sy + 11.8, "{STAR} **SPECIAL**", size=6.8, color=fg, align="right")

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
    page.text(x + w / 2.0, y + 33.0, f"Cost: {dspec.cost_str}  |  {dspec.vp_str}  |  Summary", font="regular", size=6.2, color=PALETTE["ink_soft"], align="center")

    cy = y + 46.0
    for v in variants:
        page.rounded_rect(x + 5.0, cy - 8.5, w - 10.0, 40.0, r=2.5, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
        page.text(x + 9.0, cy + 1.0, f"[{v.code}] {v.name}", font="bold", size=6.4, color=fg)
        page.rich_paragraph(x + 9.0, cy + 10.5, w - 18.0, v.effect, size=5.6, leading=7.5, color=PALETTE["ink"])
        cy += 44.0


def render_variant_market_cards_pages(page3: PDFPage, page4: PDFPage) -> None:
    """Pages 3 & 4 of Dice Aids: All 15 Printable Variant (★) Market Cards (120 x 182 pt) + 5 Deck Summary Cards."""
    # Organize by Color Column (Red, Blue, Green, Yellow, Purple) so cutting & sorting is effortless!
    by_color: Dict[str, List[VariantCardSpec]] = {"red": [], "blue": [], "green": [], "yellow": [], "purple": []}
    for vc in VARIANT_CARDS:
        by_color[vc.color_key].append(vc)
    order = ["red", "blue", "green", "yellow", "purple"]

    cw, ch = 120.0, 182.0  # 1.67" x 2.53" — fits inside 124 x 190 pt Market Board slots!
    gap_x, gap_y = 22.0, 28.0
    total_w = 5 * cw + 4 * gap_x  # 688 pt
    x0 = (792.0 - total_w) / 2.0  # 52.0 pt
    y0 = 48.0

    # Page 3: Row 0 = Set 1 (R1..P1 Baseline), Row 1 = Set 2 (R2..P2)
    page3.text(52.0, 26.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS — SHEET 1 (SETS 1 & 2) [3/4]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    page3.text(740.0, 26.0, "SIZE: 1.67\" x 2.53\" (FITS MARKET BOARD)", font="mono", size=6.5, color=PALETTE["muted"], align="right")

    for col_idx, ckey in enumerate(order):
        cx = x0 + col_idx * (cw + gap_x)
        _draw_single_variant_card(page3, cx, y0, cw, ch, by_color[ckey][0])
        _draw_single_variant_card(page3, cx, y0 + ch + gap_y, cw, ch, by_color[ckey][1])

    page3.text(396.0, 594.0, "Setup: Shuffle the 3 Variant (STAR) cards of each color and place 1 face-up in each Software Market slot (Row 1 = Default Baseline R1-P1).", font="italic", size=6.8, color=PALETTE["muted"], align="center")

    # Page 4: Row 0 = Set 3 (R3..P3), Row 1 = 5 Color Reference / Divider Cards
    page4.text(52.0, 26.0, "TOO MANY SECRETS // SOFTWARE MODULE VARIANT (STAR) MARKET CARDS — SHEET 2 (SET 3 + DIVIDERS) [4/4]", font="mono_bold", size=6.8, color=PALETTE["ink_soft"])
    page4.text(740.0, 26.0, "SIZE: 1.67\" x 2.53\" (FITS MARKET BOARD)", font="mono", size=6.5, color=PALETTE["muted"], align="right")

    spec_map = {d.color_key: d for d in DICE_SPECS}
    for col_idx, ckey in enumerate(order):
        cx = x0 + col_idx * (cw + gap_x)
        _draw_single_variant_card(page4, cx, y0, cw, ch, by_color[ckey][2])
        _draw_color_divider_card(page4, cx, y0 + ch + gap_y, cw, ch, spec_map[ckey], by_color[ckey])

    page4.text(396.0, 594.0, "Bottom row provides optional All-Variants Divider / Reference cards for storing each 3-card color mini-deck.", font="italic", size=6.8, color=PALETTE["muted"], align="center")


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
    page.rect(x, y, w, 22.0, stroke=PALETTE["ink"], fill=ver_bg, line_width=0.9)

    # Version pill on left
    page.rounded_rect(x + 5.0, y + 4.0, 28.0, 14.0, r=2.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.7)
    page.text(x + 19.0, y + 13.8, tile.version, font="mono_bold", size=7.8, color=PALETTE["ink"], align="center")

    # Card Name
    page.text(x + 38.0, y + 14.8, tile.name.upper(), font="bold", size=8.0, color=ver_fg)

    # Profile badge on right
    page.text(x + w - 6.0, y + 14.2, tile.profile, font="mono", size=5.8, color=PALETTE["rule"] if tile.version in ("v3.0", "v2.0") else PALETTE["muted"], align="right")

    # Payload Row (y + 22 .. y + 48)
    py_bar = y + 22.0
    page.rect(x, py_bar, w, 25.0, stroke=PALETTE["ink"], fill=PALETTE["paper_tint"], line_width=0.7)
    lbl_tag = "START CUP" if tile.version == "v1.0" else "UPGRADE"
    page.text(x + 6.0, py_bar + 10.5, f"{lbl_tag} PAYLOAD (ALL COUNTS):", font="mono_bold", size=5.9, color=PALETTE["muted"])
    page.rich_line(x + 6.0, py_bar + 21.0, f"**{tile.payload_3p4p}**", size=7.6, color=PALETTE["ink"])

    # Standard 2-Cube / Setup Pill on right
    page.rounded_rect(x + w - 88.0, py_bar + 4.0, 82.0, 17.0, r=2.0, stroke=PALETTE["rule"], fill=PALETTE["white"], line_width=0.6)
    sub_tag = "Setup Priming" if tile.version == "v1.0" else "Standard 2-Cube"
    page.rich_line(x + w - 47.0, py_bar + 15.2, sub_tag, size=6.3, color=PALETTE["ink_soft"], align="center")

    # Active Directive Body (y + 47 .. y + 112)
    dy = y + 60.0
    page.text(x + 8.0, dy, f"ACTIVE DIRECTIVE // {tile.directive_title.upper()}", font="bold", size=7.2, color=PALETTE["red"] if tile.version != "v1.0" else PALETTE["ink_soft"])
    page.rich_paragraph(x + 8.0, dy + 12.5, w - 16.0, tile.directive_body, size=6.85, leading=9.5, color=PALETTE["ink"])


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
        ("v3.0 TILES", "Deal 1 face-up\nto top slot.\nTrack fill (4/5/6)\n= SINGULARITY!"),
        ("v2.0 TILES", "Deal 1 face-up\nto middle slot.\nStandard 2-cube\nPayload to Cup."),
        ("v1.0 TILES", "Deal 1 face-up\nto bottom slot.\nLoad Start Cup\nat Setup."),
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
    page.text(42.0, 136.0, "CORPORATE SECRET TOKENS (x32 — 4 VP EACH)", font="mono_bold", size=6.8, color=PALETTE["blue"])
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
            page.text(bx + 26.0, by + 26.5, "4 VP  |  Client Data", font="regular", size=5.8, color=PALETTE["muted"])

    # Section 3 (y = 298..410): 16x Patch (🔧) Tokens (8 cols x 2 rows)
    page.text(42.0, 300.0, "SPLICE / PATCH TOKENS (x16 — MAX 3 HELD PER PLAYER)", font="mono_bold", size=6.8, color=PALETTE["green"])
    py0 = 305.0
    ph = 42.0
    for r in range(2):
        for c in range(8):
            bx = 41.0 + c * sw
            by = py0 + r * ph
            page.rect(bx, by, sw, ph, stroke=PALETTE["green"], fill=PALETTE["green_light"], line_width=0.6, dash=(3, 1.5))
            page.draw_wrench_icon(bx + 15.0, by + 21.0, 13.0, color=PALETTE["green"])
            page.text(bx + 26.0, by + 18.5, "1 PATCH", font="bold", size=7.6, color=PALETTE["green"])
            page.text(bx + 26.0, by + 29.5, "Unlock / Patch / -$1", font="regular", size=5.6, color=PALETTE["ink_soft"])

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
            page.text(bx + 34.0, by + 25.5, "1 VP per $2", font="regular", size=5.4, color=PALETTE["muted"])


# =============================================================================
# Build All Standalone & Combined Print-and-Play PDFs
# =============================================================================

def generate_all_pdfs(out_dir: str) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    generated: List[str] = []

    # 1. Individual Player Boards (6 pages)
    doc_players = PDFDocument("Too Many Secrets - Player Boards (6 Characters)")
    for idx, char in enumerate(CHARACTERS, start=1):
        p = doc_players.add_page()
        render_player_board(p, char, idx)
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
    doc_master = PDFDocument("Too Many Secrets - Complete Print and Play Prototype (v0.10.0)")
    for sub_doc in (doc_central, doc_players, doc_dice, doc_versions):
        for pg in sub_doc.pages:
            doc_master.pages.append(pg)
    path_master = os.path.join(out_dir, "00_Too_Many_Secrets_Complete_PnP.pdf")
    doc_master.save(path_master)
    generated.append(path_master)

    return generated


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    files = generate_all_pdfs(base)
    for f in files:
        print(f"Generated: {f} ({os.path.getsize(f):,} bytes)")
