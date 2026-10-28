"""Minimalist Tape-Punk / Technical Schematic Vector Illustrations for the 6 Archetypes.

Designed for crisp ink-saver printing in both color and monochrome laser output.
"""

from __future__ import annotations

import math
from typing import List, Tuple

from pnp.pdf_engine import PALETTE, PDFPage


def draw_character_illustration(page: PDFPage, code: str, x: float, y: float, w: float, h: float) -> None:
    """Render a framed minimalist tape-punk schematic illustration inside (x, y, w, h)."""
    # Outer crisp frame + subtle inner technical reticle
    page.rect(x, y, w, h, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    pad = 6.0
    ix, iy, iw, ih = x + pad, y + pad, w - 2 * pad, h - 2 * pad
    page.rect(ix, iy, iw, ih, stroke=PALETTE["guide"], fill=PALETTE["paper_tint"], line_width=0.5)
    page.corner_ticks(ix + 3, iy + 3, iw - 6, ih - 6, size=5.0, color=PALETTE["muted"])

    cx = x + w / 2.0
    cy = y + h / 2.0 - 4.0

    key = code.upper()
    if key == "ACOUSTIC":
        _draw_acoustic(page, ix, iy, iw, ih, cx, cy)
    elif key == "PHREAKER":
        _draw_phreaker(page, ix, iy, iw, ih, cx, cy)
    elif key == "PRODIGY":
        _draw_prodigy(page, ix, iy, iw, ih, cx, cy)
    elif key == "SPOOK":
        _draw_spook(page, ix, iy, iw, ih, cx, cy)
    elif key == "CIPHER":
        _draw_cipher(page, ix, iy, iw, ih, cx, cy)
    elif key == "OPERATOR":
        _draw_operator(page, ix, iy, iw, ih, cx, cy)

    # Bottom technical telemetry bar inside illustration frame
    captions = {
        "ACOUSTIC": "FIG 01 // ACOUSTIC BAFFLE RESONANCE",
        "PHREAKER": "FIG 02 // MAGNETIC TAPE SPLICE RIG",
        "PRODIGY": "FIG 03 // KERNEL INTERRUPT OVERRIDE",
        "SPOOK": "FIG 04 // REDACTED SLUSH ROUTING",
        "CIPHER": "FIG 05 // ALGORITHMIC LATTICE ROTOR",
        "OPERATOR": "FIG 06 // AUXILIARY PATCH SWITCHBOARD",
    }
    tag = captions.get(key, "SCHEMATIC")
    page.line(ix + 8, iy + ih - 16, ix + iw - 8, iy + ih - 16, stroke=PALETTE["rule"], width=0.5)
    page.text(cx, iy + ih - 6, tag, font="mono", size=6.5, color=PALETTE["muted"], align="center")


def _draw_acoustic(page: PDFPage, ix: float, iy: float, iw: float, ih: float, cx: float, cy: float) -> None:
    # Subtle oscilloscope grid
    gx, gy, gw, gh = ix + 18, iy + 16, iw - 36, ih - 40
    page.rounded_rect(gx, gy, gw, gh, r=6.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    for i in range(1, 6):
        vx = gx + (gw / 6.0) * i
        page.line(vx, gy + 4, vx, gy + gh - 4, stroke=PALETTE["guide"], width=0.4)
    for j in range(1, 4):
        hy = gy + (gh / 4.0) * j
        page.line(gx + 4, hy, gx + gw - 4, hy, stroke=PALETTE["guide"], width=0.4)

    # Central compiler tower shaft & two angled baffles
    tw = 54.0
    tx = cx - tw / 2.0
    page.line(tx, gy + 12, tx, gy + gh - 12, stroke=PALETTE["ink_soft"], width=1.1, dash=(3, 2))
    page.line(tx + tw, gy + 12, tx + tw, gy + gh - 12, stroke=PALETTE["ink_soft"], width=1.1, dash=(3, 2))
    # Baffles
    page.line(tx, gy + 38, tx + 34, gy + 56, stroke=PALETTE["ink"], width=2.0)
    page.line(tx + tw, gy + 78, tx + tw - 34, gy + 96, stroke=PALETTE["ink"], width=2.0)

    # Harmonic acoustic sine wave sweeping horizontally across oscilloscope
    pts: List[Tuple[float, float]] = []
    steps = 64
    for s in range(steps + 1):
        t = s / steps
        px = gx + 10 + t * (gw - 20)
        envelope = math.sin(t * math.pi)
        py = cy - 4 + math.sin(t * math.pi * 5.0) * 28.0 * envelope
        pts.append((px, py))
    page.polygon(pts, stroke=PALETTE["blue"], fill=None, line_width=1.4, closed=False)

    # Shattered / isolated rogue cube in resonance node
    qx, qy = cx + 6, gy + 114
    page.rect(qx - 8, qy - 8, 16, 16, stroke=PALETTE["red"], fill=PALETTE["red_light"], line_width=1.1, dash=(2, 1.5))
    page.line(qx - 13, qy - 13, qx + 13, qy + 13, stroke=PALETTE["red"], width=0.9)
    page.line(qx + 13, qy - 13, qx - 13, qy + 13, stroke=PALETTE["red"], width=0.9)


def _draw_phreaker(page: PDFPage, ix: float, iy: float, iw: float, ih: float, cx: float, cy: float) -> None:
    # Two reel-to-reel magnetic tape spools
    r_spool = 38.0
    ly = cy - 18
    lx = cx - 48
    rx = cx + 48

    for sx in (lx, rx):
        page.circle(sx, ly, r_spool, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.3)
        page.circle(sx, ly, r_spool * 0.72, stroke=PALETTE["rule"], fill=None, line_width=0.6)
        page.circle(sx, ly, 10.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=1.0)
        page.circle(sx, ly, 3.0, stroke=PALETTE["ink"], fill=PALETTE["ink"])
        # 3 hub cutouts
        for k in range(3):
            ang = math.radians(-90 + k * 120)
            p1 = (sx + 14 * math.cos(ang), ly + 14 * math.sin(ang))
            p2 = (sx + 29 * math.cos(ang), ly + 29 * math.sin(ang))
            page.line(p1[0], p1[1], p2[0], p2[1], stroke=PALETTE["ink"], width=3.0)

    # Tension rollers + magnetic tape path feeding into central splice block
    pin_y = cy + 38
    page.circle(lx + 16, pin_y, 5.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)
    page.circle(rx - 16, pin_y, 5.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)

    # Tape ribbon lines
    page.line(lx - r_spool * 0.65, ly + r_spool * 0.75, lx + 14, pin_y + 4, stroke=PALETTE["ink"], width=1.3)
    page.line(rx + r_spool * 0.65, ly + r_spool * 0.75, rx - 14, pin_y + 4, stroke=PALETTE["ink"], width=1.3)
    page.line(lx + 16, pin_y + 5, rx - 16, pin_y + 5, stroke=PALETTE["ink"], width=1.6)

    # Central splicing block with diagonal green splice tape
    bx, by, bw, bh = cx - 26, pin_y - 7, 52, 24
    page.rounded_rect(bx, by, bw, bh, r=2.5, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
    page.polygon(
        [(cx - 9, by + 3), (cx + 5, by + 3), (cx + 9, by + bh - 3), (cx - 5, by + bh - 3)],
        stroke=PALETTE["green"],
        fill=PALETTE["green_light"],
        line_width=1.0,
    )
    page.line(cx - 3, by + 2, cx + 3, by + bh - 2, stroke=PALETTE["green"], width=1.2)
    page.text(cx, cy - 64, "2600 Hz // DUAL-REEL SPLICE", font="mono_bold", size=6.8, color=PALETTE["ink_soft"], align="center")


def _draw_prodigy(page: PDFPage, ix: float, iy: float, iw: float, ih: float, cx: float, cy: float) -> None:
    # CRT Terminal Monitor Screen
    mw, mh = 148.0, 96.0
    mx, my = cx - mw / 2.0, iy + 16
    page.rounded_rect(mx, my, mw, mh, r=6.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.3)
    page.rounded_rect(mx + 6, my + 6, mw - 12, mh - 12, r=3.0, stroke=PALETTE["ink_soft"], fill=PALETTE["paper_tint"], line_width=0.75)

    # Terminal prompt header
    page.text(mx + 12, my + 19, "> IRQ_BYPASS --UNLOCK-ALL", font="mono_bold", size=6.8, color=PALETTE["ink"])

    # Popped open padlock in center of CRT
    lx, ly = cx, my + 56
    # Popped shackle shifted up and rotated open on right
    page.polygon(
        [(lx - 10, ly - 4), (lx - 10, ly - 20), (lx - 5, ly - 26), (lx + 5, ly - 26), (lx + 10, ly - 20), (lx + 10, ly - 13)],
        stroke=PALETTE["purple"],
        fill=None,
        line_width=2.0,
        closed=False,
    )
    # Lock body
    page.rounded_rect(lx - 15, ly - 4, 30, 24, r=2.5, stroke=PALETTE["ink"], fill=PALETTE["purple_light"], line_width=1.2)
    # Keyhole slash
    page.circle(lx, ly + 5, 2.6, stroke=None, fill=PALETTE["ink"])
    page.line(lx, ly + 6, lx, ly + 13, stroke=PALETTE["ink"], width=1.6)

    # Spark / bypass vectors around popped shackle
    for ang_deg in (-145, -115, -55, -25):
        a = math.radians(ang_deg)
        page.line(
            lx + 18 * math.cos(a), ly - 16 + 18 * math.sin(a),
            lx + 26 * math.cos(a), ly - 16 + 26 * math.sin(a),
            stroke=PALETTE["purple"], width=1.1,
        )

    # 3 Mechanical Keycaps below monitor
    ky = my + mh + 10
    kw = 34.0
    gap = 10.0
    start_x = cx - (3 * kw + 2 * gap) / 2.0
    labels = ["ESC", "BRK", "RUN"]
    for i, lbl in enumerate(labels):
        kx = start_x + i * (kw + gap)
        page.rounded_rect(kx, ky, kw, 24, r=3.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
        page.rounded_rect(kx + 3, ky + 2, kw - 6, 17, r=2.0, stroke=PALETTE["muted"], fill=PALETTE["panel_tint"], line_width=0.6)
        page.text(kx + kw / 2.0, ky + 13.5, lbl, font="mono_bold", size=7.0, color=PALETTE["ink"], align="center")


def _draw_spook(page: PDFPage, ix: float, iy: float, iw: float, ih: float, cx: float, cy: float) -> None:
    # Classified Dossier Sheet in background
    dw, dh = 128.0, 128.0
    dx, dy = cx - dw / 2.0, cy - dh / 2.0 - 2
    # Folder tab back
    page.polygon(
        [(dx - 6, dy + 8), (dx + 38, dy + 8), (dx + 46, dy - 2), (dx + dw - 6, dy - 2), (dx + dw - 6, dy + dh - 4), (dx - 6, dy + dh - 4)],
        stroke=PALETTE["muted"],
        fill=PALETTE["panel_tint"],
        line_width=0.8,
    )
    # Front sheet
    page.rect(dx, dy + 6, dw, dh - 6, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.2)
    page.text(dx + 8, dy + 20, "EYES ONLY // ACCT-00", font="mono_bold", size=7.0, color=PALETTE["blue"])
    page.line(dx + 8, dy + 25, dx + dw - 8, dy + 25, stroke=PALETTE["ink"], width=0.7)

    # Redacted black censor bars
    bars = [
        (dx + 10, dy + 32, 76, 6),
        (dx + 92, dy + 32, 24, 6),
        (dx + 10, dy + 44, 48, 6),
        (dx + 10, dy + 104, 64, 6),
        (dx + 80, dy + 104, 36, 6),
        (dx + 10, dy + 116, 94, 6),
    ]
    for bx, by, bw, bh in bars:
        page.rect(bx, by, bw, bh, stroke=None, fill=PALETTE["ink"])

    # Central geometric surveillance eye / aperture
    ey = dy + 76
    # Eye almond polygon
    eye_pts: List[Tuple[float, float]] = []
    for i in range(25):
        t = i / 24.0
        ang = t * math.pi
        eye_pts.append((cx - 42 * math.cos(ang), ey - 20 * math.sin(ang)))
    for i in range(25):
        t = i / 24.0
        ang = t * math.pi
        eye_pts.append((cx + 42 * math.cos(ang), ey + 20 * math.sin(ang)))
    page.polygon(eye_pts, stroke=PALETTE["blue"], fill=PALETTE["blue_light"], line_width=1.3)
    page.circle(cx, ey, 14.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.2)
    page.circle(cx, ey, 6.0, stroke=None, fill=PALETTE["ink"])
    page.circle(cx + 2.5, ey - 2.5, 1.8, stroke=None, fill=PALETTE["white"])


def _draw_cipher(page: PDFPage, ix: float, iy: float, iw: float, ih: float, cx: float, cy: float) -> None:
    # Outer & inner cryptographic Enigma/prime rings
    r_outer = 58.0
    r_mid = 44.0
    page.circle(cx, cy - 2, r_outer, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.2)
    page.circle(cx, cy - 2, r_mid, stroke=PALETTE["ink_soft"], fill=PALETTE["paper_tint"], line_width=0.8, dash=(3, 2))

    # 24 rotor degree ticks around ring
    for i in range(24):
        ang = math.radians(i * 15)
        r1 = r_mid + 2 if i % 2 == 0 else r_mid + 5
        r2 = r_outer - 2
        page.line(
            cx + r1 * math.cos(ang), (cy - 2) + r1 * math.sin(ang),
            cx + r2 * math.cos(ang), (cy - 2) + r2 * math.sin(ang),
            stroke=PALETTE["ink"] if i % 3 == 0 else PALETTE["muted"],
            width=0.9 if i % 3 == 0 else 0.5,
        )

    # Isometric 3D wireframe d6 module cube inside rotor
    r_hex = 26.0
    oy = cy - 2
    hex_pts = [
        (cx + r_hex * math.cos(math.radians(-90 + 60 * k)), oy + r_hex * math.sin(math.radians(-90 + 60 * k)))
        for k in range(6)
    ]
    # Top rhomb tint
    page.polygon([hex_pts[5], hex_pts[0], hex_pts[1], (cx, oy)], stroke=PALETTE["yellow"], fill=PALETTE["yellow_light"], line_width=1.0)
    # Outer hex + inner Y-edges of isometric cube
    page.polygon(hex_pts, stroke=PALETTE["ink"], fill=None, line_width=1.4)
    for idx in (1, 3, 5):
        page.line(cx, oy, hex_pts[idx][0], hex_pts[idx][1], stroke=PALETTE["ink"], width=1.2)

    # Cardinal hex coordinates outside rotor
    page.text(ix + 10, iy + 18, "0x4F", font="mono", size=6.5, color=PALETTE["muted"])
    page.text(ix + iw - 10, iy + 18, "0xA7", font="mono", size=6.5, color=PALETTE["muted"], align="right")
    page.text(ix + 10, iy + ih - 24, "P=257", font="mono", size=6.5, color=PALETTE["muted"])
    page.text(ix + iw - 10, iy + ih - 24, "dCost=-$2", font="mono", size=6.5, color=PALETTE["yellow"], align="right")


def _draw_operator(page: PDFPage, ix: float, iy: float, iw: float, ih: float, cx: float, cy: float) -> None:
    # Left Patch-Bay Jack Matrix (3 Contractor Ports) -> Central Hub -> Right Defense Bus
    panel_w, panel_h = iw - 28, ih - 42
    px, py = ix + 14, iy + 14
    page.rounded_rect(px, py, panel_w, panel_h, r=4.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.2)
    page.text(px + 8, py + 13, "CONTRACTOR BUS", font="mono_bold", size=6.5, color=PALETTE["ink_soft"])
    page.text(px + panel_w - 8, py + 13, "ACTIVE RELAY", font="mono_bold", size=6.5, color=PALETTE["ink_soft"], align="right")
    page.line(px + 6, py + 18, px + panel_w - 6, py + 18, stroke=PALETTE["rule"], width=0.6)

    # 3 Left Contractor Jacks (C-01, C-02, C-03)
    lx = px + 30
    rx = px + panel_w - 30
    hub_x, hub_y = cx + 6, py + 22 + (panel_h - 26) / 2.0

    ys = [py + 38, py + 72, py + 106]
    tags = ["AUX-1", "AUX-2", "AUX-3"]
    colors = [PALETTE["blue"], PALETTE["green"], PALETTE["ink_soft"]]

    # Routing lines first
    for idx, jy in enumerate(ys):
        mid_x = lx + 34 + idx * 8
        pts = [(lx + 6, jy), (mid_x, jy), (hub_x - 16, hub_y + (idx - 1) * 7), (hub_x, hub_y)]
        page.polygon(pts, stroke=colors[idx], fill=None, line_width=1.5 if idx < 2 else 1.0, closed=False, dash=() if idx < 2 else (2.5, 1.5))

    # Output lines from Hub to Right Ports
    for idx, jy in enumerate(ys):
        pts = [(hub_x, hub_y), (rx - 26, jy), (rx - 6, jy)]
        page.polygon(pts, stroke=PALETTE["ink"], fill=None, line_width=1.1, closed=False)

    # Central Dispatch Switch Node
    page.circle(hub_x, hub_y, 16.0, stroke=PALETTE["ink"], fill=PALETTE["blue_light"], line_width=1.3)
    page.circle(hub_x, hub_y, 6.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.0)

    # Left & Right Jack Sockets
    for idx, jy in enumerate(ys):
        page.circle(lx, jy, 6.0, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=1.1)
        page.circle(lx, jy, 2.5, stroke=None, fill=colors[idx])
        page.text(lx - 9, jy + 2.5, tags[idx], font="mono", size=5.8, color=PALETTE["muted"], align="right")

        page.circle(rx, jy, 6.0, stroke=PALETTE["ink"], fill=PALETTE["panel_tint"], line_width=1.1)
        page.circle(rx, jy, 2.5, stroke=None, fill=PALETTE["ink"])
