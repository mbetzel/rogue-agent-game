"""Tabletop Simulator module builder for Too Many Secrets (v0.52.0).

Renders the Print-and-Play components (pnp/generate_pnp.py draw functions) to PNG
images and writes a Tabletop Simulator save file that uses them.

    python3 -m tts.build_tts                     # images + save using GitHub raw URLs
    python3 -m tts.build_tts --install-dir DIR   # also a local-file save + images in DIR
    python3 -m tts.build_tts --check             # exit 1 if tts/ is stale vs pnp/ (no writes)

Needs `pdftoppm` (poppler-utils) for rasterizing. No other dependencies.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from pnp import generate_pnp as g
from pnp.pdf_engine import PALETTE, PDFDocument, PDFPage, measure_text

VERSION = "v0.52.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(HERE, "assets")
SAVE_NAME = f"Too Many Secrets ({VERSION})"
SAVE_FILE = "TooManySecrets.json"  # stable name: a version bump overwrites it
DEFAULT_BASE_URL = "https://raw.githubusercontent.com/mbetzel/rogue-agent-game/main/tts/assets/"

# One PnP point -> table units. A 792 pt (11") board is 16 units wide; cards keep
# the same scale, so they fit the printed slots on the boards like the paper PnP.
K = 16.0 / 792.0

# Player seats: TTS colours that do not clash with the game's cube and dice colours.
SEATS = [
    # (seat colour, tint, mat centre x, mat centre z, faces south?)
    ("White", (0.95, 0.95, 0.95), -8.4, -14.4, True),
    ("Pink", (0.96, 0.44, 0.81), 8.4, -14.4, True),
    ("Teal", (0.13, 0.69, 0.61), 8.4, 14.4, False),
    ("Orange", (0.96, 0.39, 0.11), -8.4, 14.4, False),
]

DIE_TINTS = {
    "Gray": (0.55, 0.57, 0.6),
    "Red": (0.78, 0.16, 0.16),
    "Blue": (0.08, 0.40, 0.75),
    "Green": (0.18, 0.49, 0.20),
    "Yellow": (0.96, 0.62, 0.04),
    "Purple": (0.42, 0.11, 0.60),
}
CUBE_TINTS = {
    "Red": (0.78, 0.16, 0.16),
    "Blue": (0.08, 0.40, 0.75),
    "Green": (0.18, 0.49, 0.20),
    "Black": (0.07, 0.09, 0.15),
}
PLAYER_CUBES = [
    "Pen Test Track cube",
    "Triage Track cube",
    "Release Track cube",
    "Public Relations Track cube",
    "Institutional Override cube",
    "Market Share marker",
    "Vulnerability marker",
    "Operative Signature Cube",
]
CUBE_KEYS = ["pen", "triage", "release", "pr", "override", "share", "vuln", "sig"]  # Quick Setup keys, same order

# Quick Setup starting values (RULES.md Section 3 / RULES_APPENDIX.md 6C).
START_MONEY = 6
START_SECRETS = 6
START_SHARE = {2: 14, 3: 18, 4: 18}


# =============================================================================
# 0. Quick Setup spots (PnP points on a 792 x 612 board -> table units)
# =============================================================================
# The numbers below repeat the layout of pnp/generate_pnp.py render_player_board,
# render_agent_board and render_market_board. Move them with that layout.

def board_point(bx: float, bz: float, px: float, py: float, south: bool = True) -> List[float]:
    """A point on a board image (top-left origin, points) -> table [x, z].

    A board at rotY 180 (south) reads upright from -z: image top is +z, image left is -x.
    A board at rotY 0 (north) is turned half a turn.
    """
    s = 1.0 if south else -1.0
    return [round(bx + s * (px - 396.0) * K, 3), round(bz + s * (306.0 - py) * K, 3)]


# Company Terminal Mat (render_player_board)
MAT_READY_SLOTS = [(314.0 + 44.0 * i, 71.0) for i in range(4)]      # Gray, Gray, Company die, Purple
MAT_CURRENT_SPRINT = [(303.0, 478.0), (347.0, 478.0), (391.0, 478.0)]
MAT_PERSONAL_RESERVE = (237.0, 483.5)                                # Public Relations L3 die outline
MAT_TRACK_L0 = {
    "release": (305.0, 170.0),
    "pen": (393.0, 343.0),
    "triage": (460.0, 460.0),
    "pr": (242.0, 335.0),
}
MAT_SIGNATURE_CRADLE = (454.0, 530.0)
MAT_TOKEN_WELLS = {"secret": (62.0, 75.0), "money": (62.0, 155.0), "research": (62.0, 235.0)}

# SETEC Central Agent & Market Share Board (render_agent_board)
_SLOT_TOP, _SLOT_H = 144.0, 128.0
_SLOT_GAP = (578.0 - _SLOT_TOP - 3 * _SLOT_H) / 2.0  # 25 pt
AGENT_VERSION_SLOTS = {ver: (188.0, _SLOT_TOP + i * (_SLOT_H + _SLOT_GAP) + _SLOT_H / 2.0)
                       for i, ver in enumerate(("v3.0", "v2.0", "v1.0"))}
AGENT_VERSION_MARKER = (-45.0, AGENT_VERSION_SLOTS["v1.0"][1])  # just off the left edge, pointing at v1.0
_VULN_X0, _VULN_CW = 158.0, (752.0 - 6.0 - 158.0 - 15 * 2.0) / 16.0
AGENT_VULN_ZERO = (_VULN_X0 + _VULN_CW / 2.0, 98.0)
SEAT_OFFSETS = [(-1, -1), (1, -1), (-1, 1), (1, 1)]  # 2 x 2 grid in a shared track cell, by seat


def market_share_cell(value: int) -> Tuple[float, float]:
    """Centre of a Central Market Share Track cell (25 down to 0, 4 columns x 7 rows)."""
    cols = g.MARKET_SHARE_COLS
    cw = (238.0 - 16.0 - 5.0 * (cols - 1)) / cols
    ch = (g.MARKET_SHARE_GRID_H - 24.0) / 7.0
    i = g.MARKET_SHARE_MAX - value
    r, c = divmod(i, cols)
    cy = 197.0 + r * (ch + 4.0) + ch / 2.0
    if value in g.MARKET_SHARE_START:
        cy += 5.0  # below the START header strip
    return 522.0 + c * (cw + 5.0) + cw / 2.0, cy


# Software Module Market & Central Supply Board (render_market_board)
MARKET_SLOT_COLORS = ["Red", "Blue", "Green", "Yellow"]
MARKET_VARIANT_SLOTS = {c: (123.0 + 182.0 * i, 360.0) for i, c in enumerate(MARKET_SLOT_COLORS)}
# 8 dice beside the Variant card: a row of 4 in the band below it, then a row of 4 in the band above it.
MARKET_DICE_GRID = [(dx, dy) for dy in (117.5, -117.5) for dx in (-60.0, -20.0, 20.0, 60.0)]


def version_payloads() -> Tuple[Dict[str, Dict[str, int]], Dict[str, int]]:
    """Staging Cup starting cubes and starting-Secret bonus per v1.0 tile, read from its banner."""
    import re
    payload: Dict[str, Dict[str, int]] = {}
    bonus: Dict[str, int] = {}
    for t in g.VERSION_TILES:
        if t.version != "v1.0":
            continue
        name = f"{t.version} {t.name}"
        m = re.search(r"Add (.*?) to Staging Cup", t.banner_text)
        cubes = {c.title(): int(n) for n, c in re.findall(r"(\d+) \{(RED|BLUE|GREEN|BLACK)\}", m.group(1))} if m else {}
        payload[name] = cubes
        b = re.search(r"start with \+(\d+) Secret", t.banner_text)
        if b:
            bonus[name] = int(b.group(1))
    return payload, bonus


# =============================================================================
# 1. Images
# =============================================================================

@dataclass
class Raster:
    """One PNG to produce from a page of the asset PDF."""

    name: str
    dpi: int
    crop_pt: Optional[Tuple[float, float, float, float]] = None  # x, y, w, h (top-left, points)


@dataclass
class AssetBook:
    doc: PDFDocument = field(default_factory=lambda: PDFDocument("Too Many Secrets - TTS assets"))
    rasters: List[Tuple[int, Raster]] = field(default_factory=list)

    def page(self, w: float, h: float, *rasters: Raster) -> PDFPage:
        p = self.doc.add_page(w, h)
        for r in rasters:
            self.rasters.append((len(self.doc.pages), r))
        return p


def _draw_card_back(page: PDFPage, w: float, h: float, title: str, subtitle: str, accent_key: str) -> None:
    accent = PALETTE[accent_key]
    page.rect(0, 0, w, h, stroke=None, fill=PALETTE["ink"])
    m = min(w, h) * 0.06
    page.rounded_rect(m, m, w - 2 * m, h - 2 * m, r=6.0, stroke=accent, fill=None, line_width=2.0)
    page.rounded_rect(m + 4, m + 4, w - 2 * m - 8, h - 2 * m - 8, r=4.0, stroke=PALETTE["ink_soft"], fill=None, line_width=0.8)
    size = min(w * 0.085, 15.0)
    page.text(w / 2, h / 2 - size * 0.4, "TOO MANY SECRETS", font="bold", size=size, color=PALETTE["white"], align="center")
    page.text(w / 2, h / 2 + size * 1.0, title, font="mono_bold", size=size * 0.7, color=PALETTE["rule"], align="center")
    if subtitle:
        page.text(w / 2, h / 2 + size * 2.0, subtitle, font="mono", size=size * 0.55, color=PALETTE["watermark"], align="center")


def _draw_round_token(page: PDFPage, d: float, label: str, sub: str, color_key: str, icon: str) -> None:
    col = PALETTE[color_key]
    light = PALETTE.get(f"{color_key}_light", PALETTE["paper_tint"])
    page.rect(0, 0, d, d, stroke=None, fill=light)
    page.circle(d / 2, d / 2, d / 2 - 3, stroke=col, fill=light, line_width=3.0)
    page.circle(d / 2, d / 2, d / 2 - 9, stroke=col, fill=None, line_width=0.8, dash=(3, 2))
    cy = d * 0.40
    if icon == "secret":
        page.draw_secret_icon(d / 2, cy, d * 0.36, color=col)
    elif icon == "research":
        page.draw_research_icon(d / 2, cy, d * 0.36, color=col)
    else:
        page.text(d / 2, cy + d * 0.12, icon, font="bold", size=d * 0.32, color=col, align="center")
    size = d * 0.12
    while measure_text(label, font="bold", size=size) > d * 0.62:
        size *= 0.92
    page.text(d / 2, d * 0.70, label, font="bold", size=size, color=col, align="center")
    if sub:
        page.text(d / 2, d * 0.81, sub, font="mono_bold", size=d * 0.075, color=PALETTE["ink_soft"], align="center")


def _grid(page: PDFPage, items: Sequence, cols: int, cw: float, ch: float, draw) -> None:
    for i, item in enumerate(items):
        x, y = (i % cols) * cw, (i // cols) * ch
        page.rect(x, y, cw, ch, stroke=None, fill=PALETTE["white"])
        draw(page, x, y, cw, ch, item)


def _variant_grid() -> List[Tuple[str, object]]:
    """4 columns (Red, Blue, Green, Yellow) x 4 rows (Sets 1-3, then the divider card)."""
    order = ["red", "blue", "green", "yellow"]
    by_color: Dict[str, List[g.VariantCardSpec]] = {k: [] for k in order}
    for vc in g.VARIANT_CARDS:
        if vc.color_key in by_color:
            by_color[vc.color_key].append(vc)
    spec_map = {d.color_key: d for d in g.DICE_SPECS}
    cells: List[Tuple[str, object]] = []
    for row in range(3):
        for ck in order:
            cells.append(("variant", by_color[ck][row]))
    for ck in order:
        cells.append(("divider", (spec_map[ck], by_color[ck])))
    return cells


# -- custom dice ----------------------------------------------------------------
# TTS Custom Dice (d6) texture, from Modding/Dice Templates/D6.png (2048 x 2048 px):
# a 3 x 3 grid with the top row unused. Middle row: faces 2, 4, 5. Bottom row:
# faces 1, 3, 6, with 1 and 6 drawn upside down. The white face squares are
# 613 px wide on a 690 px pitch, centred at x 333 / 1023 / 1713 and y 1023 / 1714.
DIE_TEX_PT = 576.0                     # page size; rendered at 256 dpi = 2048 px
DIE_TEX_DPI = 256
_PX = DIE_TEX_PT / 2048.0
DIE_FACE_PT = 613 * _PX                # 172 pt face square
DIE_FACE_CELLS = {                     # face -> (centre x px, centre y px, upside down?)
    2: (333.0, 1023.5, False), 4: (1023.5, 1023.5, False), 5: (1713.0, 1023.5, False),
    1: (333.0, 1714.0, True), 3: (1023.5, 1714.0, False), 6: (1713.0, 1714.0, True),
}
DIE_BODY = {"gray": "gray", "red": "red", "blue": "blue", "green": "green", "yellow": "yellow_fill", "purple": "purple"}


def _face_parts(face: str) -> List[List[str]]:
    """'+$2 / +2 {RESEARCH} {WARN}' -> [['+$2'], ['+2 {RESEARCH}']]: Choices (/), each a list of Dual (&) yields."""
    t = face.replace("{WARN}", "").replace("Corporate Secret", "Secret").strip()
    return [[p.strip() for p in alt.split(" & ")] for alt in t.split(" / ")]


def die_face_name(color: str, n: int, face: str) -> str:
    """Plain-text face name for TTS roll messages and tooltips (TTS fonts lack the icons)."""
    t = face.replace("{WARN}", "").strip()
    if "{STAR}" in t:
        t = "Purple Star: Signature Protocol" if color == "purple" else f"{color.title()} Star: Variant Card"
    elif "R&D" in t:
        t = "R&D face"
    t = t.replace("{RESEARCH}", "Research").replace(" / ", " or ").replace(" & ", " and ")
    return f"{n}: {t}" + (" [Locked Die]" if "{WARN}" in face else "")


def _rich_width(page: PDFPage, markup: str, size: float) -> float:
    return sum(page._span_width(sp, size) for sp in page._parse_rich_tokens(markup, base_font="bold"))


def _draw_die_face(page: PDFPage, cx: float, cy: float, spec, n: int) -> None:
    key = spec.color_key
    body = PALETTE[DIE_BODY[key]]
    face = spec.faces[n - 1]
    h = DIE_FACE_PT / 2.0
    page.rounded_rect(cx - h + 9, cy - h + 9, 2 * h - 18, 2 * h - 18, r=14.0, stroke=None,
                      fill=PALETTE.get(f"{key}_light", PALETTE["paper_tint"]))
    # Face number (pips, as on the reference cards) and the ⚠ mark.
    page.draw_pip_die(cx - h + 34, cy - h + 34, 30.0, n, stroke=body, fill=PALETTE["white"], pip_color=body)
    warn = "{WARN}" in face
    if warn:
        page.draw_warn_icon(cx + h - 34, cy - h + 36, 34.0)
        page.rounded_rect(cx - h + 18, cy + h - 40, 2 * h - 36, 24.0, r=5.0, stroke=None, fill=PALETTE["yellow_fill"])
        page.text(cx, cy + h - 21.5, "LOCKED", font="bold", size=15.0, color=PALETTE["ink"], align="center")
    top, bottom = cy - h + 56, cy + h - (46 if warn else 18)
    mid = (top + bottom) / 2.0
    if "{STAR}" in face:
        page.draw_star_icon(cx, mid - 14, 62.0, fill=body)
        label = "PROTOCOL" if key == "purple" else "VARIANT"
        page.text(cx, mid + 40, label, font="bold", size=17.0, color=PALETTE["ink"], align="center")
        return
    if "R&D" in face:
        page.draw_secret_icon(cx, mid - 18, 48.0, color=PALETTE["blue"])
        page.text(cx, mid + 30, "R&D", font="bold", size=26.0, color=PALETTE["ink"], align="center")
        return
    # Yields: Choices (/) separated by "or", Dual (&) yields stacked.
    alts = _face_parts(face)
    lines = [ln for alt in alts for ln in alt]
    max_w = 2 * h - 34
    sizes = {ln: min(30.0, 30.0 * max_w / _rich_width(page, f"**{ln}**", 30.0)) for ln in lines}
    or_h = 15.0
    total = sum(sizes[ln] * 1.08 for ln in lines) + (len(alts) - 1) * or_h
    if total > bottom - top:
        k = (bottom - top) / total
        sizes = {ln: v * k for ln, v in sizes.items()}
        total = bottom - top
    y = mid - total / 2.0
    for a_i, alt in enumerate(alts):
        if a_i:
            page.line(cx - 46, y + or_h / 2.0 - 1, cx - 14, y + or_h / 2.0 - 1, stroke=PALETTE["muted"], width=1.0)
            page.line(cx + 14, y + or_h / 2.0 - 1, cx + 46, y + or_h / 2.0 - 1, stroke=PALETTE["muted"], width=1.0)
            page.text(cx, y + or_h / 2.0 + 3, "or", font="italic", size=11.0, color=PALETTE["muted"], align="center")
            y += or_h
        for ln in alt:
            size = sizes[ln]
            y += size * 1.08
            page.rich_line(cx, y - size * 0.22, f"**{ln}**", size=size, color=PALETTE["ink"], align="center")


def draw_die_texture(page: PDFPage, spec) -> None:
    """One TTS Custom Dice texture for a DieSpec (all six faces)."""
    page.rect(0, 0, DIE_TEX_PT, DIE_TEX_PT, stroke=None, fill=PALETTE[DIE_BODY[spec.color_key]])
    for n, (px, py, flip) in DIE_FACE_CELLS.items():
        cx, cy = px * _PX, py * _PX
        if flip:  # half a turn about the face centre (PDF user space is y-up)
            page.raw(f"q -1 0 0 -1 {2 * cx:.2f} {2 * (DIE_TEX_PT - cy):.2f} cm")
        _draw_die_face(page, cx, cy, spec, n)
        if flip:
            page.raw("Q")


def build_asset_book() -> AssetBook:
    book = AssetBook()

    # Boards (full PnP pages)
    g.render_agent_board(book.page(792, 612, Raster("agent_board", 200)))
    g.render_market_board(book.page(792, 612, Raster("market_board", 200)))
    for idx in range(1, 5):
        g.render_player_board(book.page(792, 612, Raster(f"player_mat_{idx}", 200)), idx)
    g.render_master_dice_reference(book.page(792, 612, Raster("dice_reference", 170)))

    # Client Company cards (3 x 2 sheet) + back
    cw, ch = g.CARD_W, g.COMPANY_CARD_H
    p = book.page(3 * cw, 2 * ch, Raster("company_cards", 300))
    _grid(p, g.COMPANIES, 3, cw, ch, lambda pg, x, y, w, h, c: g._draw_company_card(pg, x, y, w, h, c, is_dock=False))
    _draw_card_back(book.page(cw, ch, Raster("company_back", 300)), cw, ch, "CLIENT COMPANY", "Deal 1 per player", "blue")

    # White Hat Dossier cards (3 x 2 sheet) + back
    ch = g.WHITE_HAT_CARD_H
    p = book.page(3 * cw, 2 * ch, Raster("white_hat_cards", 300))
    _grid(p, g.WHITE_HATS, 3, cw, ch, lambda pg, x, y, w, h, c: g._draw_white_hat_card(pg, x, y, w, h, c, is_dock=False))
    _draw_card_back(book.page(cw, ch, Raster("white_hat_back", 300)), cw, ch, "WHITE HAT DOSSIER", "Deal 1 per player", "purple")

    # Variant (★) Market cards (4 x 4 sheet) + back
    vw, vh = 126.0, 194.0

    def draw_variant(pg, x, y, w, h, cell):
        kind, payload = cell
        if kind == "variant":
            g._draw_single_variant_card(pg, x, y, w, h, payload)
        else:
            g._draw_color_divider_card(pg, x, y, w, h, payload[0], payload[1])

    p = book.page(4 * vw, 4 * vh, Raster("variant_cards", 300))
    _grid(p, _variant_grid(), 4, vw, vh, draw_variant)
    _draw_card_back(book.page(vw, vh, Raster("variant_back", 300)), vw, vh, "VARIANT CARD", "1 per market colour", "yellow")

    # SETEC Version tiles (2 x 3 sheet) + back
    tw, th = 212.0, 112.0
    p = book.page(2 * tw, 3 * th, Raster("version_tiles", 300))
    _grid(p, g.VERSION_TILES, 2, tw, th, g._draw_version_tile)
    _draw_card_back(book.page(tw, th, Raster("version_back", 300)), tw, th, "SETEC VERSION", "v1.0 / v2.0 / v3.0", "watermark")

    # Player reference cards: dice reference (face) / round reference (back), 2 x 2.
    # The PnP sheets put 4 cards on a 372 x 288 pt pitch starting at (24, 18).
    ref_crop = (24.0, 18.0, 744.0, 576.0)
    g.render_four_player_pocket_aids(book.page(792, 612, Raster("reference_faces", 220, ref_crop)))
    g.render_four_player_round_reference_cards(book.page(792, 612, Raster("reference_backs", 220, ref_crop)))

    # First Player Marker + Active Version marker, cropped from the PnP token sheet.
    g.render_pnp_tokens_page(book.page(
        792, 612,
        Raster("first_player_marker", 300, (40.0, 62.0, 86.0, 56.0)),
        Raster("version_marker", 300, (126.0, 62.0, 86.0, 56.0)),
    ))

    # Custom Dice textures, one per die colour.
    for spec in g.DICE_SPECS:
        draw_die_texture(book.page(DIE_TEX_PT, DIE_TEX_PT, Raster(f"die_{spec.color_key}", DIE_TEX_DPI)), spec)

    # Round resource tokens.
    d = 120.0
    for name, label, sub, ck, icon in (
        ("token_secret", "SECRET", "1 VP", "blue", "secret"),
        ("token_research", "RESEARCH", "", "green", "research"),
        ("token_money_1", "ONE CREDIT", "", "gray", "$1"),
        ("token_money_5", "FIVE CREDITS", "", "yellow", "$5"),
    ):
        _draw_round_token(book.page(d, d, Raster(name, 200)), d, label, sub, ck, icon)

    return book


def render_assets(out_dir: str) -> Dict[str, str]:
    """Render every asset PNG into `out_dir`; returns {name: sha1-prefix}."""
    if shutil.which("pdftoppm") is None:
        raise SystemExit("pdftoppm not found: install poppler-utils (sudo apt install poppler-utils)")
    os.makedirs(out_dir, exist_ok=True)
    book = build_asset_book()
    hashes: Dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "assets.pdf")
        book.doc.save(pdf)
        for page_no, r in book.rasters:
            stem = os.path.join(out_dir, r.name)
            cmd = ["pdftoppm", "-png", "-singlefile", "-r", str(r.dpi), "-f", str(page_no), "-l", str(page_no)]
            if r.crop_pt:
                s = r.dpi / 72.0
                x, y, w, h = r.crop_pt
                cmd += ["-x", str(round(x * s)), "-y", str(round(y * s)), "-W", str(round(w * s)), "-H", str(round(h * s))]
            subprocess.run(cmd + [pdf, stem], check=True)
            with open(stem + ".png", "rb") as f:
                hashes[r.name] = hashlib.sha1(f.read()).hexdigest()[:10]
    return hashes


# =============================================================================
# 2. Save file
# =============================================================================

class SaveBuilder:
    def __init__(self, url_for, seed: int = 46) -> None:
        self.url_for = url_for
        self._rng = random.Random(seed)
        self._guids: set = set()
        self._deck_id = 0

    def guid(self) -> str:
        while True:
            gid = f"{self._rng.randrange(16 ** 6):06x}"
            if gid not in self._guids:
                self._guids.add(gid)
                return gid

    @staticmethod
    def transform(x: float, z: float, y: float = 1.0, rot_y: float = 180.0, rot_z: float = 0.0,
                  scale: Sequence[float] = (1.0, 1.0, 1.0)) -> dict:
        return {
            "posX": round(x, 3), "posY": round(y, 3), "posZ": round(z, 3),
            "rotX": 0.0, "rotY": rot_y, "rotZ": rot_z,
            "scaleX": scale[0], "scaleY": scale[1], "scaleZ": scale[2],
        }

    def base(self, name: str, nickname: str, tf: dict, description: str = "", color=(1.0, 1.0, 1.0),
             locked: bool = False, gm_notes: str = "") -> dict:
        return {
            "GUID": self.guid(),
            "Name": name,
            "Transform": tf,
            "Nickname": nickname,
            "Description": description,
            "GMNotes": gm_notes,
            "ColorDiffuse": {"r": color[0], "g": color[1], "b": color[2]},
            "Locked": locked,
            "Grid": True,
            "Snap": True,
            "Autoraise": True,
            "Sticky": True,
            "Tooltip": True,
            "GridProjection": False,
            "Hands": False,
            "HideWhenFaceDown": False,
            "LuaScript": "",
            "LuaScriptState": "",
            "XmlUI": "",
        }

    # -- simple objects -------------------------------------------------------

    def tile(self, image: str, nickname: str, x: float, z: float, w: float, d: float, *, back: Optional[str] = None,
             tile_type: int = 0, thickness: float = 0.2, stackable: bool = False, locked: bool = False,
             rot_y: float = 180.0, description: str = "", y: float = 1.0) -> dict:
        obj = self.base("Custom_Tile", nickname, self.transform(x, z, y=y, rot_y=rot_y), description,
                        locked=locked, gm_notes=f"fit:{w:.3f}x{d:.3f}")
        obj["CustomImage"] = {
            "ImageURL": self.url_for(image),
            "ImageSecondaryURL": self.url_for(back or image),
            "ImageScalar": 1.0,
            "WidthScale": 0.0,
            "CustomTile": {"Type": tile_type, "Thickness": thickness, "Stackable": stackable, "Stretch": False},
        }
        return obj

    def die(self, color: str, x: float, z: float, nickname: str = "", y: float = 1.5) -> dict:
        """A TTS Custom Dice d6 with this colour's faces (die_<colour>.png). The global script
        renames the six rotation values to the face yields (GM Notes "die:<colour>")."""
        label = nickname or f"{color} die"
        obj = self.base("Custom_Dice", label, self.transform(x, z, y=y, scale=(0.75, 0.75, 0.75)),
                        gm_notes=f"die:{color.lower()}")
        obj["CustomImage"] = {
            "ImageURL": self.url_for(f"die_{color.lower()}"),
            "ImageSecondaryURL": "",
            "ImageScalar": 1.0,
            "WidthScale": 0.0,
            "CustomDice": {"Type": 1},  # DiceType d6
        }
        return obj

    def cube(self, nickname: str, tint, x: float = 0.0, z: float = 0.0, y: float = 1.5, description: str = "") -> dict:
        return self.base("BlockSquare", nickname, self.transform(x, z, y=y, scale=(0.38, 0.38, 0.38)), description,
                         color=tint)

    def bag(self, nickname: str, x: float, z: float, contents: List[dict], tint=(0.3, 0.3, 0.32),
            infinite: bool = False, description: str = "") -> dict:
        obj = self.base("Infinite_Bag" if infinite else "Bag", nickname, self.transform(x, z, y=1.5), description,
                        color=tint)
        obj["ContainedObjects"] = contents
        return obj

    # -- cards ----------------------------------------------------------------

    def custom_deck(self, face: str, back: str, cols: int, rows: int, unique_back: bool = False) -> Tuple[int, dict]:
        self._deck_id += 1
        return self._deck_id, {
            str(self._deck_id): {
                "FaceURL": self.url_for(face),
                "BackURL": self.url_for(back),
                "NumWidth": cols,
                "NumHeight": rows,
                "BackIsHidden": True,
                "UniqueBack": unique_back,
                "Type": 0,
            }
        }

    def card(self, deck: Tuple[int, dict], index: int, nickname: str, x: float, z: float, w: float, d: float,
             face_down: bool = False, rot_y: float = 180.0, description: str = "") -> dict:
        deck_id, deck_def = deck
        obj = self.base("Card", nickname, self.transform(x, z, rot_y=rot_y, rot_z=180.0 if face_down else 0.0),
                        description, gm_notes=f"fit:{w:.3f}x{d:.3f}")
        obj["CardID"] = deck_id * 100 + index
        obj["CustomDeck"] = copy.deepcopy(deck_def)
        obj["SidewaysCard"] = False
        return obj

    def deck(self, cards: List[dict], nickname: str, x: float, z: float, w: float, d: float,
             face_down: bool = True, description: str = "") -> dict:
        if len(cards) == 1:
            c = cards[0]
            c["Transform"] = self.transform(x, z, rot_z=180.0 if face_down else 0.0)
            return c
        obj = self.base("Deck", nickname, self.transform(x, z, rot_z=180.0 if face_down else 0.0), description,
                        gm_notes=f"fit:{w:.3f}x{d:.3f}")
        merged: Dict[str, dict] = {}
        for c in cards:
            merged.update(c["CustomDeck"])
        obj["DeckIDs"] = [c["CardID"] for c in cards]
        obj["CustomDeck"] = merged
        obj["ContainedObjects"] = cards
        obj["SidewaysCard"] = False
        return obj

    def hand(self, color: str, x: float, z: float, rot_y: float) -> dict:
        obj = self.base("HandTrigger", "", self.transform(x, z, y=4.0, rot_y=rot_y, scale=(15.0, 7.0, 4.5)),
                        locked=True)
        obj["FogColor"] = color
        return obj


def _cards_from_sheet(sb: SaveBuilder, deck, names: Sequence[str], w: float, d: float,
                      indices: Optional[Sequence[int]] = None) -> List[dict]:
    idx = list(indices) if indices is not None else list(range(len(names)))
    return [sb.card(deck, i, n, 0, 0, w, d, face_down=True) for i, n in zip(idx, names)]


def build_save(url_for) -> dict:
    sb = SaveBuilder(url_for)
    objs: List[dict] = []
    bw, bd = 792 * K, 612 * K  # 16 x 12.36
    agent_c, market_c = (-8.4, 0.0), (8.4, 0.0)
    payload, secret_bonus = version_payloads()
    setup: dict = {
        "start": {"money": START_MONEY, "secrets": START_SECRETS,
                  "share": {str(k): v for k, v in START_SHARE.items()}},
        "payload": payload,
        "secret_bonus": secret_bonus,
        "company_die": {c.name: c.starting_die.title() for c in g.COMPANIES},
        "version_decks": {}, "version_slots": {}, "variant_decks": {}, "variant_slots": {},
        "market_bags": {}, "cube_bags": {}, "token_bags": {},
        "market_dice_grid": [[round(dx * K, 3), round(-dy * K, 3)] for dx, dy in MARKET_DICE_GRID],
        "seats": [],
    }

    # ---- central boards ----------------------------------------------------
    objs.append(sb.tile("agent_board", "SETEC Central Agent & Market Share Board", -8.4, 0, bw, bd, locked=True,
                        description="Version slots, Corruption Tracks, Vulnerability Track and Central Market Share Track."))
    objs.append(sb.tile("market_board", "Software Module Market & Central Supply Board", 8.4, 0, bw, bd, locked=True,
                        description="Staging Cup, Exit Sorting Tray, 4 Market Card slots, setup and VP reference."))
    objs.append(sb.tile("dice_reference", "Master Dice Reference", -33.0, 0, bw * 0.55, bd * 0.55,
                        description="1-6 pip-to-ability reference for every die colour."))

    # ---- SETEC Version tiles (left column) ---------------------------------
    tw, td = 212 * K, 112 * K
    vdeck = sb.custom_deck("version_tiles", "version_back", 2, 3)
    by_version: Dict[str, List[Tuple[int, str]]] = {}
    for i, t in enumerate(g.VERSION_TILES):
        by_version.setdefault(t.version, []).append((i, f"{t.version} {t.name}"))
    for ver, vz in (("v3.0", 4.6), ("v2.0", 1.6), ("v1.0", -1.4)):
        entries = by_version[ver]
        cards = _cards_from_sheet(sb, vdeck, [n for _, n in entries], tw, td, [i for i, _ in entries])
        objs.append(sb.deck(cards, f"SETEC Version {ver} tiles", -20.2, vz, tw, td,
                            description=f"Shuffle and deal 1 {ver} tile face up into its slot on the Agent Board."))
        setup["version_decks"][ver] = objs[-1]["GUID"]
        setup["version_slots"][ver] = board_point(*agent_c, *AGENT_VERSION_SLOTS[ver])

    # ---- Client Company + White Hat decks ----------------------------------
    cw, cd = g.CARD_W * K, g.COMPANY_CARD_H * K
    cdeck = sb.custom_deck("company_cards", "company_back", 3, 2)
    objs.append(sb.deck(_cards_from_sheet(sb, cdeck, [c.name for c in g.COMPANIES], cw, cd),
                        "Client Company deck", -25.6, 4.4, cw, cd, description="Shuffle; deal 1 per player."))
    setup["company_deck"] = objs[-1]["GUID"]
    wd = g.WHITE_HAT_CARD_H * K
    wdeck = sb.custom_deck("white_hat_cards", "white_hat_back", 3, 2)
    objs.append(sb.deck(_cards_from_sheet(sb, wdeck, [w.name for w in g.WHITE_HATS], cw, wd),
                        "White Hat Dossier deck", -25.6, 0.9, cw, wd, description="Shuffle; deal 1 per player."))
    setup["white_hat_deck"] = objs[-1]["GUID"]

    # ---- tokens (left column, lower) ----------------------------------------
    for i, (key, img, name, desc) in enumerate((
        ("secret", "token_secret", "Corporate Secret", "1 Secret = 1 VP."),
        ("research", "token_research", "Research Token", "Spent on the 4 Research Tracks and Pen Test."),
        ("money1", "token_money_1", "$1", "Money."),
        ("money5", "token_money_5", "$5", "Money."),
    )):
        tok = sb.tile(img, name, 0, 0, 0.9, 0.9, tile_type=2, thickness=0.1, stackable=True, description=desc)
        objs.append(sb.bag(f"{name} supply", -19.6 - i * 2.1, -4.6, [tok], infinite=True))
        setup["token_bags"][key] = objs[-1]["GUID"]
    objs.append(sb.tile("first_player_marker", "First Player Marker", -28.6, -2.0, 86 * K, 56 * K, tile_type=3,
                        thickness=0.15, description="Passes clockwise at the end of Phase 6."))
    setup["first_player"] = objs[-1]["GUID"]
    objs.append(sb.tile("version_marker", "Active Version Marker", -28.6, -4.2, 86 * K, 56 * K, tile_type=3,
                        thickness=0.15, description="Starts on v1.0."))
    setup["version_marker"] = objs[-1]["GUID"]
    setup["version_marker_spot"] = board_point(*agent_c, *AGENT_VERSION_MARKER)

    # ---- market dice + Variant cards (right column) -------------------------
    for color, z in (("Red", 5.0), ("Blue", 2.6), ("Green", 0.2), ("Yellow", -2.2)):
        dice = [sb.die(color, 0, 0) for _ in range(8)]
        objs.append(sb.bag(f"{color} dice (Central Market)", 18.6, z, dice, tint=DIE_TINTS[color],
                           description="Stack 2 x players on this colour's Variant Card."))
        setup["market_bags"][color] = objs[-1]["GUID"]

    vw, vd = 126 * K, 194 * K
    vdeck_sheet = sb.custom_deck("variant_cards", "variant_back", 4, 4)
    cells = _variant_grid()
    for ci, (color, x, z) in enumerate((("Red", 21.4, 2.2), ("Blue", 24.2, 2.2),
                                        ("Green", 21.4, -2.2), ("Yellow", 24.2, -2.2))):
        names = [cells[row * 4 + ci][1].name for row in range(3)]
        cards = _cards_from_sheet(sb, vdeck_sheet, names, vw, vd, [row * 4 + ci for row in range(3)])
        objs.append(sb.deck(cards, f"{color} Variant cards", x, z, vw, vd,
                            description="Shuffle; place 1 face up in this colour's Market slot."))
        setup["variant_decks"][color] = objs[-1]["GUID"]
        setup["variant_slots"][color] = board_point(*market_c, *MARKET_VARIANT_SLOTS[color])
    dividers = [sb.card(vdeck_sheet, 12 + ci, f"{c} Variant summary", 0, 0, vw, vd)
                for ci, c in enumerate(("Red", "Blue", "Green", "Yellow"))]
    objs.append(sb.deck(dividers, "Variant summary cards", 27.0, 2.2, vw, vd, face_down=False))

    # ---- cube supply, Staging Cup, Cube Tower --------------------------------
    templates: Dict[str, dict] = {}
    for color, z in (("Red", 5.4), ("Blue", 3.6), ("Green", 1.8), ("Black", 0.0)):
        label = "Corruption Cube (Black)" if color == "Black" else f"{color} Attack Cube"
        template = sb.cube(label, CUBE_TINTS[color])
        templates[color] = copy.deepcopy(template)
        objs.append(sb.bag(f"{label} supply", 29.6, z, [template], tint=CUBE_TINTS[color], infinite=True))
        setup["cube_bags"][color] = objs[-1]["GUID"]

    cup = sb.bag("Staging Cup", 21.0, -7.4, [], tint=(0.85, 0.85, 0.9),
                 description="Public: anyone may look inside. Phase 2: press 'Drop Staging Cup' on the Cube Tower panel.")
    objs.append(cup)
    setup["staging_cup_spot"] = [21.0, -7.4]
    setup["setec_share_spot"] = board_point(*agent_c, *market_share_cell(0))
    tower = sb.base("BlockSquare", "Cube Tower", sb.transform(24.6, -7.4, y=1.8, scale=(1.8, 3.2, 1.8)),
                    "Scripted: use the Cube Tower panel (top right). Stuck cubes stay hidden inside.",
                    color=(0.12, 0.14, 0.2), locked=True)
    objs.append(tower)
    tray_origin = (27.2, 1.0, -6.6)

    # ---- player areas ----------------------------------------------------
    rw, rd = 356 * K * 0.78, 272 * K * 0.78
    ref_deck = sb.custom_deck("reference_faces", "reference_backs", 2, 2, unique_back=True)
    for p_i, (seat, tint, mx, mz, south) in enumerate(SEATS, start=1):
        rot = 180.0 if south else 0.0
        f = 1.0 if south else -1.0            # +1 for the south seats (player sits at -z)
        side = 1.0 if mx > 0 else -1.0
        kx = mx + side * 12.2                 # kit column beside the mat
        objs.append(sb.tile(f"player_mat_{p_i}", f"Company Terminal Mat P{p_i} ({seat})", mx, mz, bw, bd,
                            locked=True, rot_y=rot))
        objs.append(sb.card(ref_deck, p_i - 1, f"Player Reference P{p_i}", kx, mz - f * 3.8, rw, rd, rot_y=rot,
                            description="Front: dice & R&D face yields. Flip: six-phase round."))
        cubes: Dict[str, str] = {}
        for c_i, label in enumerate(PLAYER_CUBES):
            cx = kx - 1.6 + (c_i % 4) * 1.05
            cz = mz + f * (0.2 + (c_i // 4) * 1.05)
            objs.append(sb.cube(f"{label} ({seat})", tint, cx, cz))
            cubes[CUBE_KEYS[c_i]] = objs[-1]["GUID"]
        dice = [("Gray", "Gray Legacy die (Ready for Release)"), ("Gray", "Gray Legacy die (Ready for Release)"),
                ("Purple", "Purple Specialist die"), ("Purple", "Purple Specialist die (Personal Reserve)"),
                ("Gray", "Gray Legacy die (Current Sprint)"), ("Gray", "Gray Legacy die (Current Sprint)"),
                ("Gray", "Gray Legacy die (Current Sprint)")]
        dice_guids: List[str] = []
        for d_i, (color, name) in enumerate(dice):
            objs.append(sb.die(color, kx - 1.6 + (d_i % 4) * 1.05, mz + f * (2.9 + (d_i // 4) * 1.05), nickname=name))
            dice_guids.append(objs[-1]["GUID"])
        objs.append(sb.hand(seat, mx, mz - f * 11.6, rot))

        def mat(pt, _mx=mx, _mz=mz, _s=south):
            return board_point(_mx, _mz, pt[0], pt[1], _s)

        def shared(pt, _i=p_i - 1, dx=9.5, dy=8.0):
            ox, oy = SEAT_OFFSETS[_i]
            return board_point(*agent_c, pt[0] + ox * dx, pt[1] + oy * dy)

        setup["seats"].append({
            "color": seat,
            "rot": rot,
            "dice": {"ready": dice_guids[0:2], "purple": dice_guids[2], "reserve": dice_guids[3],
                     "sprint": dice_guids[4:7]},
            "cubes": cubes,
            "spots": {
                "ready": [mat(p) for p in MAT_READY_SLOTS],
                "sprint": [mat(p) for p in MAT_CURRENT_SPRINT],
                "reserve": mat(MAT_PERSONAL_RESERVE),
                **{k: mat(p) for k, p in MAT_TRACK_L0.items()},
                "sig": mat(MAT_SIGNATURE_CRADLE),
                **{k: mat(p) for k, p in MAT_TOKEN_WELLS.items()},
                "vuln": shared(AGENT_VULN_ZERO),
                "share": {str(v): shared(market_share_cell(v), dx=0.0, dy=0.0) for v in sorted(set(START_SHARE.values()))},
                # Kit column beside the mat: free once the dice and cubes move onto the mat.
                "company": [round(kx, 3), round(mz + f * 0.5, 3)],
                "override": [round(kx - side * 2.85, 3), round(mz + f * 0.5, 3)],
                "white_hat": [round(kx, 3), round(mz + f * 3.65, 3)],
                "first_player": [round(kx, 3), round(mz + f * 5.75, 3)],
            },
        })

    die_faces = {spec.color_key: [die_face_name(spec.color_key, n, f) for n, f in enumerate(spec.faces, start=1)]
                 for spec in g.DICE_SPECS}
    lua = open(os.path.join(HERE, "global.lua"), encoding="utf-8").read()
    cfg = (
        f'STAGING_CUP_GUID = "{cup["GUID"]}"\n'
        f'TOWER_GUID = "{tower["GUID"]}"\n'
        f"TRAY_ORIGIN = {{ {tray_origin[0]}, {tray_origin[1]}, {tray_origin[2]} }}\n"
        f"CUBE_TEMPLATES = JSON.decode([==[{json.dumps(templates)}]==])\n"
        f"SETUP = JSON.decode([==[{json.dumps(setup)}]==])\n"
        f"DIE_FACES = JSON.decode([==[{json.dumps(die_faces)}]==])\n"
    )
    placeholder = "-- __CONFIG__ (replaced by the builder: STAGING_CUP_GUID, TOWER_GUID, TRAY_ORIGIN, CUBE_TEMPLATES, SETUP, DIE_FACES)"
    if placeholder not in lua:
        raise SystemExit("tts/global.lua: the __CONFIG__ placeholder line is missing or changed")
    lua = lua.replace(placeholder, cfg)
    xml = open(os.path.join(HERE, "global.xml"), encoding="utf-8").read()

    return {
        "SaveName": SAVE_NAME,
        "EpochTime": 0,
        "Date": "",
        "VersionNumber": "",
        "GameMode": "Too Many Secrets",
        "GameType": "",
        "GameComplexity": "",
        "Tags": [],
        "Gravity": 0.5,
        "PlayArea": 0.75,
        "Table": "Table_RPG",
        "Sky": "Sky_Museum",
        "Note": NOTE,
        "TabStates": {},
        "LuaScript": lua,
        "LuaScriptState": "",
        "XmlUI": xml,
        "ObjectStates": objs,
    }


NOTE = f"""[b]Too Many Secrets {VERSION} -- Tabletop Simulator PnP module[/b]
Rules: RULES.md / RULES_QUICKREF.md in the repo.

[b]Quick Setup[/b]
Press [b]2P[/b], [b]3P[/b] or [b]4P[/b] on the Quick Setup panel (top right) to do steps 1-8 below. It uses the seated colours if exactly that many players sit at a mat, else the first mats (White, Pink, Teal, Orange). It runs once per game; load the save again to start over.

[b]Setup (by hand)[/b]
1. Shuffle each SETEC Version tile stack; deal 1 v1.0, 1 v2.0 and 1 v3.0 face up into the Agent Board slots. Active Version Marker on v1.0.
2. Cube Tower panel (top right): press [b]Prime the Compiler[/b] (drops 1 Red, 1 Blue, 1 Green, 1 Black; exits return to the supply).
3. Put the v1.0 tile's starting cubes into the Staging Cup bag.
4. Shuffle each colour's Variant cards; 1 face up per Market slot, with 2 x players dice of that colour on it.
5. Deal 1 Client Company and 1 White Hat Dossier card per player. Take your starting colored die from that colour's market stack.
6. Each mat: 2 Gray + 1 Purple die in Ready for Release and 3 Gray dice in the Current Sprint; the 2nd Purple die on the Personal Reserve outline (Public Relations L3). Each player owns 5 Gray dice; no Gray dice are gained later.
7. $6, 6 Corporate Secrets (+1 with Data Scraper), 0 Research. Market Share 14 (2P) or 18 (3-4P); 2P adds the SETEC Corp Black Cube at 0. Vulnerability 0. Signature Cube on its cradle.
8. Randomly give out the First Player Marker.

[b]Cube Tower[/b]
Phase 2: press [b]Drop Staging Cup[/b]. Exited cubes land in the Exit Tray area beside the tower; stuck cubes stay hidden inside (sim/tower.py Shogun Baffle odds). Move exited Black cubes to the Corruption Track and exited Signature Cubes back to their mats. Phase 4 step 5: put the exited Red, Blue and Green cubes back in the Staging Cup.
"""


# =============================================================================
# 3. CLI
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL, help="URL prefix the hosted images live under")
    ap.add_argument("--install-dir", help="TTS Saves folder (WSL path): writes a local-file save + images there")
    ap.add_argument("--skip-render", action="store_true", help="reuse the images already in tts/assets/")
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed module is out of date; writes nothing")
    args = ap.parse_args(argv)

    if args.check:
        raise SystemExit(check(args.base_url))

    if args.skip_render:
        hashes = {}
        for fn in sorted(os.listdir(ASSET_DIR)):
            if fn.endswith(".png"):
                with open(os.path.join(ASSET_DIR, fn), "rb") as f:
                    hashes[fn[:-4]] = hashlib.sha1(f.read()).hexdigest()[:10]
    else:
        hashes = render_assets(ASSET_DIR)
        print(f"Rendered {len(hashes)} images -> {ASSET_DIR}")

    out = os.path.join(HERE, SAVE_FILE)
    with open(out, "w", encoding="utf-8") as f:
        f.write(_save_text(hashes, args.base_url))
    print(f"Save (hosted images): {out}")

    if args.install_dir:
        img_dir = os.path.join(args.install_dir, "TooManySecrets_assets")
        os.makedirs(img_dir, exist_ok=True)
        for n in hashes:
            shutil.copy2(os.path.join(ASSET_DIR, n + ".png"), img_dir)
        win_dir = _to_windows_path(img_dir)
        local = build_save(lambda n: f"file:///{win_dir}/{n}.png")
        local["SaveName"] = SAVE_NAME + " [local images]"
        local_out = os.path.join(args.install_dir, SAVE_FILE.replace(".json", "_local.json"))
        for old in os.listdir(args.install_dir):  # earlier versioned installs
            if old.startswith("TooManySecrets_v") and old.endswith(".json"):
                os.remove(os.path.join(args.install_dir, old))
        with open(local_out, "w", encoding="utf-8") as f:
            json.dump(local, f, indent=2)
        shutil.copy2(out, args.install_dir)
        print(f"Installed: {local_out} and {os.path.join(args.install_dir, SAVE_FILE)}")


def _save_text(hashes: Dict[str, str], base_url: str) -> str:
    base = base_url if base_url.endswith("/") else base_url + "/"
    return json.dumps(build_save(lambda n: f"{base}{n}.png?v={hashes[n]}"), indent=2)


def check(base_url: str = DEFAULT_BASE_URL) -> int:
    """Re-render into a temp dir and compare with tts/assets/ and the committed save."""
    with tempfile.TemporaryDirectory() as tmp:
        fresh = render_assets(tmp)
    committed = {fn[:-4] for fn in os.listdir(ASSET_DIR) if fn.endswith(".png")} if os.path.isdir(ASSET_DIR) else set()
    stale = []
    for name, digest in sorted(fresh.items()):
        path = os.path.join(ASSET_DIR, name + ".png")
        if not os.path.exists(path):
            stale.append(f"missing  tts/assets/{name}.png")
            continue
        with open(path, "rb") as f:
            if hashlib.sha1(f.read()).hexdigest()[:10] != digest:
                stale.append(f"changed  tts/assets/{name}.png")
    stale += [f"orphan   tts/assets/{n}.png" for n in sorted(committed - set(fresh))]
    save_path = os.path.join(HERE, SAVE_FILE)
    current = open(save_path, encoding="utf-8").read() if os.path.exists(save_path) else ""
    if current != _save_text(fresh, base_url):
        stale.append(f"changed  tts/{SAVE_FILE}")
    if stale:
        print("TTS module is out of date; run `python3 -m tts.build_tts`:")
        print("\n".join("  " + s for s in stale))
        return 1
    print(f"TTS module is up to date ({len(fresh)} images, {VERSION}).")
    return 0


def _to_windows_path(path: str) -> str:
    path = os.path.abspath(path)
    if path.startswith("/mnt/") and len(path) > 6 and path[6] == "/":
        return f"{path[5].upper()}:/{path[7:]}"
    return path


if __name__ == "__main__":
    main()
