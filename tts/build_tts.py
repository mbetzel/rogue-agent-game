"""Tabletop Simulator module builder for Too Many Secrets (v0.46.0).

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

VERSION = "v0.46.0"
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
        label = nickname or f"{color} die"
        return self.base("Die_6", label, self.transform(x, z, y=y, scale=(0.75, 0.75, 0.75)), color=DIE_TINTS[color])

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

    # ---- Client Company + White Hat decks ----------------------------------
    cw, cd = g.CARD_W * K, g.COMPANY_CARD_H * K
    cdeck = sb.custom_deck("company_cards", "company_back", 3, 2)
    objs.append(sb.deck(_cards_from_sheet(sb, cdeck, [c.name for c in g.COMPANIES], cw, cd),
                        "Client Company deck", -25.6, 4.4, cw, cd, description="Shuffle; deal 1 per player."))
    wd = g.WHITE_HAT_CARD_H * K
    wdeck = sb.custom_deck("white_hat_cards", "white_hat_back", 3, 2)
    objs.append(sb.deck(_cards_from_sheet(sb, wdeck, [w.name for w in g.WHITE_HATS], cw, wd),
                        "White Hat Dossier deck", -25.6, 0.9, cw, wd, description="Shuffle; deal 1 per player."))

    # ---- tokens (left column, lower) ----------------------------------------
    for i, (img, name, desc) in enumerate((
        ("token_secret", "Corporate Secret", "1 Secret = 1 VP."),
        ("token_research", "Research Token", "Spent on the 4 Research Tracks and Pen Test."),
        ("token_money_1", "$1", "Money."),
        ("token_money_5", "$5", "Money."),
    )):
        tok = sb.tile(img, name, 0, 0, 0.9, 0.9, tile_type=2, thickness=0.1, stackable=True, description=desc)
        objs.append(sb.bag(f"{name} supply", -19.6 - i * 2.1, -4.6, [tok], infinite=True))
    objs.append(sb.tile("first_player_marker", "First Player Marker", -28.6, -2.0, 86 * K, 56 * K, tile_type=3,
                        thickness=0.15, description="Passes clockwise at the end of Phase 6."))
    objs.append(sb.tile("version_marker", "Active Version Marker", -28.6, -4.2, 86 * K, 56 * K, tile_type=3,
                        thickness=0.15, description="Starts on v1.0."))

    # ---- market dice + Variant cards (right column) -------------------------
    for color, z in (("Red", 5.0), ("Blue", 2.6), ("Green", 0.2), ("Yellow", -2.2)):
        dice = [sb.die(color, 0, 0) for _ in range(8)]
        objs.append(sb.bag(f"{color} dice (Central Market)", 18.6, z, dice, tint=DIE_TINTS[color],
                           description="Stack 2 x players on this colour's Variant Card."))
    objs.append(sb.bag("Gray Legacy dice", 18.6, -4.6, [sb.die("Gray", 0, 0) for _ in range(12)],
                       tint=DIE_TINTS["Gray"], description="Gained from Level 1 Breakthroughs."))

    vw, vd = 126 * K, 194 * K
    vdeck_sheet = sb.custom_deck("variant_cards", "variant_back", 4, 4)
    cells = _variant_grid()
    for ci, (color, x, z) in enumerate((("Red", 21.4, 2.2), ("Blue", 24.2, 2.2),
                                        ("Green", 21.4, -2.2), ("Yellow", 24.2, -2.2))):
        names = [cells[row * 4 + ci][1].name for row in range(3)]
        cards = _cards_from_sheet(sb, vdeck_sheet, names, vw, vd, [row * 4 + ci for row in range(3)])
        objs.append(sb.deck(cards, f"{color} Variant cards", x, z, vw, vd,
                            description="Shuffle; place 1 face up in this colour's Market slot."))
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

    cup = sb.bag("Staging Cup", 21.0, -7.4, [], tint=(0.85, 0.85, 0.9),
                 description="Public: anyone may look inside. Phase 2: press 'Drop Staging Cup' on the Cube Tower panel.")
    objs.append(cup)
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
                            description="Front: dice & Secret yields. Flip: six-phase round."))
        for c_i, label in enumerate(PLAYER_CUBES):
            cx = kx - 1.6 + (c_i % 4) * 1.05
            cz = mz + f * (0.2 + (c_i // 4) * 1.05)
            objs.append(sb.cube(f"{label} ({seat})", tint, cx, cz))
        dice = [("Gray", "Gray Legacy die"), ("Gray", "Gray Legacy die"), ("Purple", "Purple Specialist die"),
                ("Purple", "Purple Specialist die (Personal Reserve)")]
        for d_i, (color, name) in enumerate(dice):
            objs.append(sb.die(color, kx - 1.6 + d_i * 1.05, mz + f * 2.9, nickname=name))
        objs.append(sb.hand(seat, mx, mz - f * 11.6, rot))

    lua = open(os.path.join(HERE, "global.lua"), encoding="utf-8").read()
    cfg = (
        f'STAGING_CUP_GUID = "{cup["GUID"]}"\n'
        f'TOWER_GUID = "{tower["GUID"]}"\n'
        f"TRAY_ORIGIN = {{ {tray_origin[0]}, {tray_origin[1]}, {tray_origin[2]} }}\n"
        f"CUBE_TEMPLATES = JSON.decode([==[{json.dumps(templates)}]==])\n"
    )
    lua = lua.replace("-- __CONFIG__ (replaced by the builder: STAGING_CUP_GUID, TOWER_GUID, TRAY_ORIGIN, CUBE_TEMPLATES)", cfg)
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

[b]Setup[/b]
1. Shuffle each SETEC Version tile stack; deal 1 v1.0, 1 v2.0 and 1 v3.0 face up into the Agent Board slots. Active Version Marker on v1.0.
2. Cube Tower panel (top right): press [b]Prime the Compiler[/b] (drops 1 Red, 1 Blue, 1 Green, 1 Black; exits return to the supply).
3. Put the v1.0 tile's starting cubes into the Staging Cup bag.
4. Shuffle each colour's Variant cards; 1 face up per Market slot, with 2 x players dice of that colour on it.
5. Deal 1 Client Company and 1 White Hat Dossier card per player. Take your starting colored die from that colour's market stack.
6. Each mat: 2 Gray + 1 Purple die in Ready for Release; the 2nd Purple die on the Personal Reserve outline (Public Relations L3).
7. $6, 5 Corporate Secrets (+1 with Data Scraper), 0 Research. Market Share 14 (2P) or 18 (3-4P); 2P adds the SETEC Corp Black Cube at 0. Vulnerability 0. Signature Cube on its cradle.
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
