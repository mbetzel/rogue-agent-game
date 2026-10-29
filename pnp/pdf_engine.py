"""Minimalist Vector PDF 1.4 Engine for Print-and-Play Tabletop Prototyping.

Pure Python 3 standard library implementation with top-left coordinate geometry
(72 pt = 1 inch), exact Adobe AFM character width metrics for Helvetica & Courier,
inline vector iconography, and precision print crop marks.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

Color = Tuple[float, float, float]


def hex_rgb(hex_str: str) -> Color:
    """Convert '#RRGGBB' hex string to normalized (r, g, b) floats in [0, 1]."""
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


# Functional Minimalist Print-and-Play Palette (Ink-Saver White + High-Contrast Spot Accents)
PALETTE: Dict[str, Color] = {
    "white": hex_rgb("#FFFFFF"),
    "paper_tint": hex_rgb("#F8FAFC"),
    "panel_tint": hex_rgb("#F1F5F9"),
    "ink": hex_rgb("#0F172A"),
    "ink_soft": hex_rgb("#334155"),
    "muted": hex_rgb("#64748B"),
    "border": hex_rgb("#1E293B"),
    "watermark": hex_rgb("#94A3B8"),
    "rule": hex_rgb("#CBD5E1"),
    "guide": hex_rgb("#E2E8F0"),
    # Functional Game Colors (chosen for crisp contrast on white & distinct luminance in B&W)
    "red": hex_rgb("#C62828"),
    "red_light": hex_rgb("#FFEBEE"),
    "blue": hex_rgb("#1565C0"),
    "blue_light": hex_rgb("#E3F2FD"),
    "green": hex_rgb("#2E7D32"),
    "green_light": hex_rgb("#E8F5E9"),
    "yellow": hex_rgb("#B45309"),       # Dark amber text/border for high legibility on white
    "yellow_fill": hex_rgb("#F59E0B"),  # Golden fill for hexagons
    "yellow_light": hex_rgb("#FEF3C7"),
    "purple": hex_rgb("#6A1B9A"),
    "purple_light": hex_rgb("#F3E5F5"),
    "black": hex_rgb("#111827"),
    "black_light": hex_rgb("#E5E7EB"),
    "gray": hex_rgb("#475569"),
    "gray_light": hex_rgb("#F1F5F9"),
}

# Standard PDF Type 1 Font Registry
FONTS = {
    "regular": ("F1", "Helvetica"),
    "bold": ("F2", "Helvetica-Bold"),
    "italic": ("F3", "Helvetica-Oblique"),
    "mono": ("F4", "Courier"),
    "mono_bold": ("F5", "Courier-Bold"),
}

# Exact Adobe AFM character widths (1/1000 em) for Helvetica & Helvetica-Bold
_HELV_REGULAR_WIDTHS: Dict[str, int] = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556,
    "@": 1015, "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778,
    "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556, "h": 556,
    "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556, "p": 556,
    "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722, "x": 500,
    "y": 500, "z": 500, "{": 334, "|": 260, "}": 334, "~": 584,
}

_HELV_BOLD_WIDTHS: Dict[str, int] = {
    " ": 278, "!": 333, '"': 474, "#": 556, "$": 556, "%": 889, "&": 722, "'": 238,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 333, ";": 333, "<": 584, "=": 584, ">": 584, "?": 611,
    "@": 975, "A": 722, "B": 722, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 556, "K": 722, "L": 611, "M": 833, "N": 722, "O": 778,
    "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 333, "\\": 278, "]": 333, "^": 584, "_": 556,
    "a": 556, "b": 611, "c": 556, "d": 611, "e": 556, "f": 333, "g": 611, "h": 611,
    "i": 278, "j": 278, "k": 556, "l": 278, "m": 889, "n": 611, "o": 611, "p": 611,
    "q": 611, "r": 389, "s": 556, "t": 333, "u": 611, "v": 556, "w": 778, "x": 556,
    "y": 556, "z": 500, "{": 389, "|": 280, "}": 389, "~": 584,
}


def _sanitize_winansi(text: str) -> str:
    """Ensure text uses clean WinAnsi characters for Type 1 fonts."""
    replacements = {
        "\u2014": "--",   # em-dash -> clean double hyphen or WinAnsi \x97
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "\xb7", # middle dot (WinAnsi 183, width 278)
        "\u00b7": "\xb7",
        "\u00d7": "x",
        "\u2192": "->",
        "\u2264": "<=",
        "\u2265": ">=",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    out = []
    for ch in text:
        code = ord(ch)
        if 32 <= code <= 126 or code == 183:
            out.append(ch)
        else:
            out.append("?")
    return "".join(out)


def _pdf_escape(text: str) -> str:
    """Escape PDF literal string characters and encode non-ASCII WinAnsi octals."""
    s = _sanitize_winansi(text)
    res = []
    for ch in s:
        c = ord(ch)
        if ch == "\\":
            res.append("\\\\")
        elif ch == "(":
            res.append("\\(")
        elif ch == ")":
            res.append("\\)")
        elif c > 126:
            res.append(f"\\{c:03o}")
        else:
            res.append(ch)
    return "".join(res)


def measure_text(text: str, font: str = "regular", size: float = 9.0) -> float:
    """Compute exact width in points for a string in the specified font & size."""
    s = _sanitize_winansi(text)
    if font in ("mono", "mono_bold"):
        return len(s) * 0.600 * size
    table = _HELV_BOLD_WIDTHS if font == "bold" else _HELV_REGULAR_WIDTHS
    total = 0
    for ch in s:
        if ch == "\xb7":
            total += 278
        else:
            total += table.get(ch, 556)
    return (total / 1000.0) * size


@dataclass
class RichSpan:
    """Represents a styled text word or inline vector icon token."""
    kind: str  # "text" or "icon"
    value: str
    font: str = "regular"
    color: Optional[Color] = None


_ICON_TOKENS = {
    "{WRENCH}", "{STAR}", "{LOCK}", "{SECRET}",
    "{RED}", "{BLUE}", "{GREEN}", "{YELLOW}", "{PURPLE}", "{BLACK}", "{GRAY}", "{WHITE}",
    "{PIP1}", "{PIP2}", "{PIP3}", "{PIP4}", "{PIP5}", "{PIP6}",
}


class PDFPage:
    """Single vector page with Top-Left (0, 0) coordinate system in points (72 pt = 1 in)."""

    def __init__(self, width: float = 792.0, height: float = 612.0) -> None:
        self.width = width
        self.height = height
        self._ops: List[str] = []

    def _py(self, y: float) -> float:
        """Convert top-down y to PDF bottom-up y."""
        return self.height - y

    def raw(self, cmd: str) -> None:
        self._ops.append(cmd)

    def save(self) -> None:
        self._ops.append("q")

    def restore(self) -> None:
        self._ops.append("Q")

    def set_stroke_color(self, color: Color) -> None:
        self._ops.append(f"{color[0]:.4f} {color[1]:.4f} {color[2]:.4f} RG")

    def set_fill_color(self, color: Color) -> None:
        self._ops.append(f"{color[0]:.4f} {color[1]:.4f} {color[2]:.4f} rg")

    def set_line_width(self, width: float) -> None:
        self._ops.append(f"{width:.3f} w")

    def set_dash(self, pattern: Sequence[float] = (), phase: float = 0.0) -> None:
        pat_str = " ".join(f"{p:.2f}" for p in pattern)
        self._ops.append(f"[{pat_str}] {phase:.2f} d")

    def set_line_join(self, style: int = 1) -> None:
        """0 = miter, 1 = round, 2 = bevel."""
        self._ops.append(f"{style} j")

    def set_line_cap(self, style: int = 1) -> None:
        """0 = butt, 1 = round, 2 = square."""
        self._ops.append(f"{style} J")

    # -------------------------------------------------------------------------
    # Geometric Primitives (Top-Left Coordinates)
    # -------------------------------------------------------------------------

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: Color = PALETTE["border"],
        width: float = 0.75,
        dash: Sequence[float] = (),
    ) -> None:
        self.save()
        self.set_stroke_color(stroke)
        self.set_line_width(width)
        if dash:
            self.set_dash(dash)
        self._ops.append(f"{x1:.2f} {self._py(y1):.2f} m {x2:.2f} {self._py(y2):.2f} l S")
        self.restore()

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        stroke: Optional[Color] = PALETTE["border"],
        fill: Optional[Color] = None,
        line_width: float = 0.85,
        dash: Sequence[float] = (),
    ) -> None:
        if stroke is None and fill is None:
            return
        self.save()
        if stroke is not None:
            self.set_stroke_color(stroke)
            self.set_line_width(line_width)
        if fill is not None:
            self.set_fill_color(fill)
        if dash:
            self.set_dash(dash)
        py = self._py(y + h)
        op = "B" if (stroke is not None and fill is not None) else ("f" if fill is not None else "S")
        self._ops.append(f"{x:.2f} {py:.2f} {w:.2f} {h:.2f} re {op}")
        self.restore()

    def rounded_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        r: float = 4.0,
        stroke: Optional[Color] = PALETTE["border"],
        fill: Optional[Color] = None,
        line_width: float = 0.85,
        dash: Sequence[float] = (),
    ) -> None:
        if stroke is None and fill is None:
            return
        r = min(r, w / 2.0, h / 2.0)
        if r <= 0.1:
            self.rect(x, y, w, h, stroke=stroke, fill=fill, line_width=line_width, dash=dash)
            return
        self.save()
        if stroke is not None:
            self.set_stroke_color(stroke)
            self.set_line_width(line_width)
        if fill is not None:
            self.set_fill_color(fill)
        if dash:
            self.set_dash(dash)

        k = 0.5522847498 * r
        # Convert corners to PDF bottom-up coords:
        left, right = x, x + w
        top, bot = self._py(y), self._py(y + h)

        cmds = [
            f"{left + r:.2f} {top:.2f} m",
            f"{right - r:.2f} {top:.2f} l",
            f"{right - r + k:.2f} {top:.2f} {right:.2f} {top - r + k:.2f} {right:.2f} {top - r:.2f} c",
            f"{right:.2f} {bot + r:.2f} l",
            f"{right:.2f} {bot + r - k:.2f} {right - r + k:.2f} {bot:.2f} {right - r:.2f} {bot:.2f} c",
            f"{left + r:.2f} {bot:.2f} l",
            f"{left + r - k:.2f} {bot:.2f} {left:.2f} {bot + r - k:.2f} {left:.2f} {bot + r:.2f} c",
            f"{left:.2f} {top - r:.2f} l",
            f"{left:.2f} {top - r + k:.2f} {left + r - k:.2f} {top:.2f} {left + r:.2f} {top:.2f} c",
            "h",
        ]
        op = "B" if (stroke is not None and fill is not None) else ("f" if fill is not None else "S")
        cmds.append(op)
        self._ops.append(" ".join(cmds))
        self.restore()

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        stroke: Optional[Color] = PALETTE["border"],
        fill: Optional[Color] = None,
        line_width: float = 0.85,
        dash: Sequence[float] = (),
    ) -> None:
        if stroke is None and fill is None:
            return
        self.save()
        if stroke is not None:
            self.set_stroke_color(stroke)
            self.set_line_width(line_width)
        if fill is not None:
            self.set_fill_color(fill)
        if dash:
            self.set_dash(dash)
        k = 0.5522847498 * r
        pcy = self._py(cy)
        cmds = [
            f"{cx:.2f} {pcy + r:.2f} m",
            f"{cx + k:.2f} {pcy + r:.2f} {cx + r:.2f} {pcy + k:.2f} {cx + r:.2f} {pcy:.2f} c",
            f"{cx + r:.2f} {pcy - k:.2f} {cx + k:.2f} {pcy - r:.2f} {cx:.2f} {pcy - r:.2f} c",
            f"{cx - k:.2f} {pcy - r:.2f} {cx - r:.2f} {pcy - k:.2f} {cx - r:.2f} {pcy:.2f} c",
            f"{cx - r:.2f} {pcy + k:.2f} {cx - k:.2f} {pcy + r:.2f} {cx:.2f} {pcy + r:.2f} c",
            "h",
        ]
        op = "B" if (stroke is not None and fill is not None) else ("f" if fill is not None else "S")
        cmds.append(op)
        self._ops.append(" ".join(cmds))
        self.restore()

    def polygon(
        self,
        pts: Sequence[Tuple[float, float]],
        stroke: Optional[Color] = PALETTE["border"],
        fill: Optional[Color] = None,
        line_width: float = 0.85,
        closed: bool = True,
        dash: Sequence[float] = (),
    ) -> None:
        if not pts or (stroke is None and fill is None):
            return
        self.save()
        self.set_line_join(1)
        self.set_line_cap(1)
        if stroke is not None:
            self.set_stroke_color(stroke)
            self.set_line_width(line_width)
        if fill is not None:
            self.set_fill_color(fill)
        if dash:
            self.set_dash(dash)
        cmds = [f"{pts[0][0]:.2f} {self._py(pts[0][1]):.2f} m"]
        for px, py in pts[1:]:
            cmds.append(f"{px:.2f} {self._py(py):.2f} l")
        if closed:
            cmds.append("h")
            op = "B" if (stroke is not None and fill is not None) else ("f" if fill is not None else "S")
        else:
            op = "S"
        cmds.append(op)
        self._ops.append(" ".join(cmds))
        self.restore()

    def crop_marks(self, x: float, y: float, w: float, h: float, length: float = 5.0, offset: float = 2.0) -> None:
        """Draw hairline corner trim marks outside a cut-out card or tile."""
        c = PALETTE["muted"]
        lw = 0.4
        # Top-left
        self.line(x - offset - length, y, x - offset, y, stroke=c, width=lw)
        self.line(x, y - offset - length, x, y - offset, stroke=c, width=lw)
        # Top-right
        self.line(x + w + offset, y, x + w + offset + length, y, stroke=c, width=lw)
        self.line(x + w, y - offset - length, x + w, y - offset, stroke=c, width=lw)
        # Bottom-left
        self.line(x - offset - length, y + h, x - offset, y + h, stroke=c, width=lw)
        self.line(x, y + h + offset, x, y + h + offset + length, stroke=c, width=lw)
        # Bottom-right
        self.line(x + w + offset, y + h, x + w + offset + length, y + h, stroke=c, width=lw)
        self.line(x + w, y + h + offset, x + w, y + h + offset + length, stroke=c, width=lw)

    def corner_ticks(self, x: float, y: float, w: float, h: float, size: float = 5.0, color: Color = PALETTE["ink"]) -> None:
        """Draw crisp L-shaped technical registration corners inside or on a frame."""
        lw = 1.2
        self.polygon([(x, y + size), (x, y), (x + size, y)], stroke=color, line_width=lw, closed=False)
        self.polygon([(x + w - size, y), (x + w, y), (x + w, y + size)], stroke=color, line_width=lw, closed=False)
        self.polygon([(x, y + h - size), (x, y + h), (x + size, y + h)], stroke=color, line_width=lw, closed=False)
        self.polygon([(x + w - size, y + h), (x + w, y + h), (x + w, y + h - size)], stroke=color, line_width=lw, closed=False)

    # -------------------------------------------------------------------------
    # Bespoke Game Iconography (Vector Symbols — Zero Emoji / Font Dependency)
    # -------------------------------------------------------------------------

    def draw_color_badge(self, cx: float, cy: float, size: float, color_key: str) -> None:
        """Draw distinct shape + spot-color badge (accessible in both Color and B&W print)."""
        r = size * 0.48
        key = color_key.lower()
        if key == "red":
            # Diamond ◆
            pts = [(cx, cy - r * 1.08), (cx + r * 1.05, cy), (cx, cy + r * 1.08), (cx - r * 1.05, cy)]
            self.polygon(pts, stroke=PALETTE["ink"], fill=PALETTE["red"], line_width=0.6)
        elif key == "blue":
            # Circle ●
            self.circle(cx, cy, r * 0.95, stroke=PALETTE["ink"], fill=PALETTE["blue"], line_width=0.6)
        elif key == "green":
            # Up-Triangle ▲
            pts = [(cx, cy - r * 1.05), (cx + r * 1.05, cy + r * 0.85), (cx - r * 1.05, cy + r * 0.85)]
            self.polygon(pts, stroke=PALETTE["ink"], fill=PALETTE["green"], line_width=0.6)
        elif key == "yellow":
            # Hexagon ⬡
            pts = [
                (cx + r * math.cos(math.radians(60 * i - 30)), cy + r * math.sin(math.radians(60 * i - 30)))
                for i in range(6)
            ]
            self.polygon(pts, stroke=PALETTE["ink"], fill=PALETTE["yellow_fill"], line_width=0.6)
        elif key == "purple":
            # Inverted Triangle ▼
            pts = [(cx - r * 1.05, cy - r * 0.85), (cx + r * 1.05, cy - r * 0.85), (cx, cy + r * 1.05)]
            self.polygon(pts, stroke=PALETTE["ink"], fill=PALETTE["purple"], line_width=0.6)
        elif key == "black":
            # Solid Corruption Square ■ with white inner core dot
            s = r * 1.75
            self.rect(cx - s / 2, cy - s / 2, s, s, stroke=PALETTE["ink"], fill=PALETTE["black"], line_width=0.6)
            self.circle(cx, cy, r * 0.28, stroke=None, fill=PALETTE["white"])
        elif key == "gray":
            s = r * 1.7
            self.rounded_rect(cx - s / 2, cy - s / 2, s, s, r=1.2, stroke=PALETTE["ink"], fill=PALETTE["muted"], line_width=0.6)
        elif key == "white":
            s = r * 1.7
            self.rounded_rect(cx - s / 2, cy - s / 2, s, s, r=1.2, stroke=PALETTE["ink"], fill=PALETTE["white"], line_width=0.75, dash=(1.5, 1.0))

    def draw_wrench_icon(self, cx: float, cy: float, size: float, color: Color = PALETTE["ink"]) -> None:
        """Draw a crisp minimalist wrench / splice tool icon centered at (cx, cy)."""
        r = size * 0.45
        # Diagonal handle from bottom-left to upper-right
        self.line(cx - r * 0.85, cy + r * 0.85, cx + r * 0.30, cy - r * 0.30, stroke=color, width=size * 0.20)
        # Open wrench jaw ring at upper-right
        self.circle(cx + r * 0.42, cy - r * 0.42, r * 0.48, stroke=color, fill=PALETTE["white"], line_width=size * 0.15)
        # Jaw notch cutout
        self.line(cx + r * 0.45, cy - r * 0.45, cx + r * 0.90, cy - r * 0.90, stroke=PALETTE["white"], width=size * 0.24)

    def draw_star_icon(self, cx: float, cy: float, size: float, fill: Color = PALETTE["ink"], stroke: Optional[Color] = None) -> None:
        """Draw a sharp 5-pointed star icon centered at (cx, cy)."""
        outer = size * 0.54
        inner = outer * 0.40
        pts: List[Tuple[float, float]] = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            rad = outer if i % 2 == 0 else inner
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        self.polygon(pts, stroke=stroke, fill=fill, line_width=0.4)

    def draw_lock_icon(self, cx: float, cy: float, size: float, color: Color = PALETTE["ink"]) -> None:
        """Draw a crisp padlock icon centered at (cx, cy)."""
        bw = size * 0.72
        bh = size * 0.52
        bx = cx - bw / 2
        by = cy - bh * 0.1
        # Shackle arch
        sr = bw * 0.30
        self.circle(cx, by - sr * 0.15, sr, stroke=color, fill=None, line_width=size * 0.13)
        # Lock body
        self.rounded_rect(bx, by, bw, bh, r=1.0, stroke=color, fill=color, line_width=0.5)
        # Keyhole dot in white
        self.circle(cx, by + bh * 0.48, size * 0.08, stroke=None, fill=PALETTE["white"])

    def draw_secret_icon(self, cx: float, cy: float, size: float, color: Color = PALETTE["blue"]) -> None:
        """Draw a classified folder / diamond-eye secret emblem."""
        w = size * 0.88
        h = size * 0.66
        x = cx - w / 2
        y = cy - h / 2
        pts = [
            (x, y + h * 0.22),
            (x + w * 0.38, y + h * 0.22),
            (x + w * 0.48, y),
            (x + w, y),
            (x + w, y + h),
            (x, y + h),
        ]
        self.polygon(pts, stroke=color, fill=PALETTE["white"], line_width=0.8)
        self.circle(cx, cy + h * 0.12, size * 0.13, stroke=None, fill=color)

    def draw_pip_die(
        self,
        cx: float,
        cy: float,
        size: float,
        pips: int,
        stroke: Color = PALETTE["ink"],
        fill: Color = PALETTE["white"],
        pip_color: Color = PALETTE["ink"],
    ) -> None:
        """Draw a rounded d6 face showing standard pips 1..6 centered at (cx, cy)."""
        half = size / 2.0
        self.rounded_rect(cx - half, cy - half, size, size, r=size * 0.18, stroke=stroke, fill=fill, line_width=0.75)
        pr = max(0.85, size * 0.088)
        off = size * 0.26
        coords: List[Tuple[float, float]] = []
        if pips in (1, 3, 5):
            coords.append((cx, cy))
        if pips in (2, 3, 4, 5, 6):
            coords.extend([(cx - off, cy - off), (cx + off, cy + off)])
        if pips in (4, 5, 6):
            coords.extend([(cx + off, cy - off), (cx - off, cy + off)])
        if pips == 6:
            coords.extend([(cx - off, cy), (cx + off, cy)])
        for px, py in coords:
            self.circle(px, py, pr, stroke=None, fill=pip_color)

    def draw_inline_icon(self, token: str, cx: float, cy: float, size: float) -> None:
        """Dispatch inline rich-text icon token centered at (cx, cy)."""
        if token == "{WRENCH}":
            self.draw_wrench_icon(cx, cy, size, color=PALETTE["green"])
        elif token == "{STAR}":
            self.draw_star_icon(cx, cy, size, fill=PALETTE["ink"])
        elif token == "{LOCK}":
            self.draw_lock_icon(cx, cy, size, color=PALETTE["ink"])
        elif token == "{SECRET}":
            self.draw_secret_icon(cx, cy, size, color=PALETTE["blue"])
        elif token in ("{RED}", "{BLUE}", "{GREEN}", "{YELLOW}", "{PURPLE}", "{BLACK}", "{GRAY}", "{WHITE}"):
            self.draw_color_badge(cx, cy, size, token.strip("{}"))
        elif token.startswith("{PIP") and token.endswith("}"):
            n = int(token[4:-1])
            self.draw_pip_die(cx, cy, size * 1.08, n)

    # -------------------------------------------------------------------------
    # Typography & Rich Inline Text Engine
    # -------------------------------------------------------------------------

    def text(
        self,
        x: float,
        y: float,
        content: str,
        font: str = "regular",
        size: float = 9.0,
        color: Color = PALETTE["ink"],
        align: str = "left",
    ) -> float:
        """Draw a single line of plain text with baseline at top-down `y`. Returns width."""
        w = measure_text(content, font=font, size=size)
        tx = x
        if align == "center":
            tx = x - w / 2.0
        elif align == "right":
            tx = x - w
        font_tag = FONTS[font][0]
        esc = _pdf_escape(content)
        self.save()
        self.set_fill_color(color)
        self._ops.append(f"BT /{font_tag} {size:.2f} Tf {tx:.2f} {self._py(y):.2f} Td ({esc}) Tj ET")
        self.restore()
        return w

    @staticmethod
    def _parse_rich_tokens(markup: str, base_font: str = "regular") -> List[RichSpan]:
        """Parse lightweight inline markup (`**bold**`, `*italic*`, `` `mono` ``, `{ICON}`) into word/icon spans."""
        markup = markup.replace("🔧", "{WRENCH}").replace("★", "{STAR}")
        style_pat = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")
        icon_pat = re.compile(r"(\{[A-Z0-9_]+\})")
        spans: List[RichSpan] = []

        def emit_plain_or_icons(chunk: str, font_name: str) -> None:
            for sub in icon_pat.split(chunk):
                if not sub:
                    continue
                if sub in _ICON_TOKENS:
                    spans.append(RichSpan(kind="icon", value=sub))
                else:
                    words = sub.split(" ")
                    for idx, word in enumerate(words):
                        if idx > 0:
                            spans.append(RichSpan(kind="text", value=" ", font=font_name))
                        if word:
                            spans.append(RichSpan(kind="text", value=word, font=font_name))

        for part in style_pat.split(markup):
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                emit_plain_or_icons(part[2:-2], "bold")
            elif part.startswith("`") and part.endswith("`"):
                emit_plain_or_icons(part[1:-1], "mono_bold")
            elif part.startswith("*") and part.endswith("*"):
                emit_plain_or_icons(part[1:-1], "italic")
            else:
                emit_plain_or_icons(part, base_font)
        return spans

    @staticmethod
    def _span_width(span: RichSpan, size: float) -> float:
        if span.kind == "icon":
            return size * 1.12
        return measure_text(span.value, font=span.font, size=size)

    def rich_line(
        self,
        x: float,
        y: float,
        markup: str,
        size: float = 8.5,
        color: Color = PALETTE["ink"],
        base_font: str = "regular",
        align: str = "left",
    ) -> float:
        """Render a single line of rich text + inline vector icons at baseline `y`."""
        spans = self._parse_rich_tokens(markup, base_font=base_font)
        total_w = sum(self._span_width(sp, size) for sp in spans)
        cx = x
        if align == "center":
            cx = x - total_w / 2.0
        elif align == "right":
            cx = x - total_w

        for sp in spans:
            sw = self._span_width(sp, size)
            if sp.kind == "icon":
                self.draw_inline_icon(sp.value, cx + sw / 2.0, y - size * 0.34, size * 0.96)
            else:
                self.text(cx, y, sp.value, font=sp.font, size=size, color=sp.color or color)
            cx += sw
        return total_w

    def rich_paragraph(
        self,
        x: float,
        y: float,
        max_width: float,
        markup: str,
        size: float = 8.0,
        leading: float = 11.0,
        color: Color = PALETTE["ink"],
        base_font: str = "regular",
        align: str = "left",
    ) -> float:
        """Word-wrap and render multi-line rich text + inline icons.

        `y` is the baseline of the first line. Returns baseline `y` ready for the next paragraph.
        """
        cur_y = y
        for raw_para in markup.split("\n"):
            if not raw_para.strip():
                cur_y += leading * 0.55
                continue
            spans = self._parse_rich_tokens(raw_para, base_font=base_font)
            # Group contiguous non-space spans into atomic word clusters so '(' or ')' never orphans
            clusters: List[List[RichSpan]] = []
            cur_cluster: List[RichSpan] = []
            for sp in spans:
                if sp.kind == "text" and sp.value == " ":
                    if cur_cluster:
                        clusters.append(cur_cluster)
                        cur_cluster = []
                    clusters.append([sp])
                else:
                    cur_cluster.append(sp)
            if cur_cluster:
                clusters.append(cur_cluster)

            lines: List[List[RichSpan]] = []
            cur_line: List[RichSpan] = []
            cur_w = 0.0

            for cl in clusters:
                is_space = (len(cl) == 1 and cl[0].kind == "text" and cl[0].value == " ")
                cl_w = sum(self._span_width(s, size) for s in cl)
                if is_space and not cur_line:
                    continue
                if cur_line and (cur_w + cl_w > max_width) and not is_space:
                    while cur_line and cur_line[-1].kind == "text" and cur_line[-1].value == " ":
                        cur_line.pop()
                    lines.append(cur_line)
                    cur_line = list(cl)
                    cur_w = cl_w
                else:
                    cur_line.extend(cl)
                    cur_w += cl_w

            while cur_line and cur_line[-1].kind == "text" and cur_line[-1].value == " ":
                cur_line.pop()
            if cur_line:
                lines.append(cur_line)

            for ln in lines:
                ln_w = sum(self._span_width(s, size) for s in ln)
                lx = x
                if align == "center":
                    lx = x + (max_width - ln_w) / 2.0
                elif align == "right":
                    lx = x + max_width - ln_w
                for s in ln:
                    sw = self._span_width(s, size)
                    if s.kind == "icon":
                        self.draw_inline_icon(s.value, lx + sw / 2.0, cur_y - size * 0.34, size * 0.96)
                    else:
                        self.text(lx, cur_y, s.value, font=s.font, size=size, color=s.color or color)
                    lx += sw
                cur_y += leading
        return cur_y

    def get_stream_bytes(self) -> bytes:
        return ("\n".join(self._ops) + "\n").encode("latin1")


class PDFDocument:
    """Multi-page PDF 1.4 serializer."""

    def __init__(self, title: str = "Too Many Secrets PnP") -> None:
        self.title = title
        self.pages: List[PDFPage] = []

    def add_page(self, width: float = 792.0, height: float = 612.0) -> PDFPage:
        p = PDFPage(width=width, height=height)
        self.pages.append(p)
        return p

    def save(self, filepath: str) -> None:
        """Serialize all pages and font resources to a valid PDF 1.4 file."""
        objects: List[bytes] = []

        def add_obj(body: bytes) -> int:
            objects.append(body)
            return len(objects)  # 1-based object ID

        # 1. Info dictionary
        info_id = add_obj(f"<< /Title ({_pdf_escape(self.title)}) /Producer (Too Many Secrets Vector PnP Engine) >>".encode("latin1"))

        # 2. Standard Type 1 Fonts with WinAnsiEncoding
        font_obj_ids: Dict[str, int] = {}
        for _, (tag, base_name) in FONTS.items():
            fid = add_obj(
                f"<< /Type /Font /Subtype /Type1 /BaseFont /{base_name} /Encoding /WinAnsiEncoding >>".encode("latin1")
            )
            font_obj_ids[tag] = fid

        font_dict_entries = " ".join(f"/{tag} {fid} 0 R" for tag, fid in font_obj_ids.items())
        resources_id = add_obj(f"<< /Font << {font_dict_entries} >> >>".encode("latin1"))

        # Reserve Pages root ID
        pages_root_id = add_obj(b"")  # placeholder

        page_ids: List[int] = []
        for page in self.pages:
            stream_data = page.get_stream_bytes()
            content_id = add_obj(
                f"<< /Length {len(stream_data)} >>\nstream\n".encode("latin1")
                + stream_data
                + b"endstream"
            )
            pid = add_obj(
                f"<< /Type /Page /Parent {pages_root_id} 0 R "
                f"/MediaBox [0 0 {page.width:.2f} {page.height:.2f}] "
                f"/Resources {resources_id} 0 R "
                f"/Contents {content_id} 0 R >>".encode("latin1")
            )
            page_ids.append(pid)

        kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
        objects[pages_root_id - 1] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>".encode("latin1")

        catalog_id = add_obj(f"<< /Type /Catalog /Pages {pages_root_id} 0 R >>".encode("latin1"))

        # Assemble binary PDF with exact byte offsets
        buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets: List[int] = [0]
        for idx, obj_bytes in enumerate(objects, start=1):
            offsets.append(len(buf))
            buf.extend(f"{idx} 0 obj\n".encode("latin1"))
            buf.extend(obj_bytes)
            buf.extend(b"\nendobj\n")

        xref_pos = len(buf)
        buf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin1"))
        buf.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            buf.extend(f"{off:010d} 00000 n \n".encode("latin1"))

        buf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n".encode("latin1")
        )

        with open(filepath, "wb") as f:
            f.write(buf)
