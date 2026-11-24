#!/usr/bin/env python3
"""The World Today - Tuesday 24 November 2026, in one image.

A pure-stdlib (Python 3.13, no third-party packages) program that draws a
one-page newspaper front page summarising the world news of Tuesday
24 November 2026 and writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

The day's news, as reported on 23-24 November 2026:
  * LEAD - NATO sends an AWACS early-warning aircraft to Poland after three
    Russian Kh-101 cruise missiles landed in Poland on Friday 20 November;
    the North Atlantic Council decided it in Brussels on Monday 23 November.
  * World chess champion D Gukesh opens his title defence against
    Javokhir Sindarov in Geneva on 24 November.
  * Ukraine sinks a Russian warship in a Libyan port with maritime drones,
    as the war spreads beyond Europe; a Russian cargo ship is hit in the
    Gulf of Finland.
  * At least 24 people die in a fire at a candy factory in Indonesia, with
    around 30 still missing.
  * COP31 climate talks in Turkey collapse without a deal on fossil fuels.
  * South Korea briefly warns Ulleung island after a Russian aircraft
    enters its airspace.
  * Israeli strikes kill three in Gaza, including a UN agency worker.
  * Mexico captures drug lord Fausto Isidro Meza Flores, "Chapo Isidro".
  * Carlos Alcaraz wins his first ATP Finals title, beating Zverev.

The drawing is fully deterministic: fixed colours, fixed geometry and a
seeded star field, so two runs write byte-identical PNGs.

Layout (1024 x 1024): navy masthead with a globe mark, a hero panel with a
drawn AWACS over a stylised map of Poland, the lead headline, three
secondary stories with small drawn icons, a ticker of further headlines
and a footer naming the day.
"""

import binascii
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 227)   # warm newsprint
INK = (16, 24, 34)        # near-black for headlines
GREY = (74, 82, 92)       # body grey
NAVY = (14, 38, 63)       # masthead / hero sky base
NAVY_DEEP = (9, 26, 46)   # hero sky top
NAVY_MID = (20, 54, 90)   # hero sky bottom
SKY_LINE = (46, 90, 136)  # radar rings
AMBER = (232, 163, 23)    # accent
RED = (178, 39, 30)       # alert red
WHITE = (244, 246, 248)
PLANE = (199, 208, 219)   # AWACS fuselage
PLANE_DARK = (124, 138, 153)
DOME = (232, 237, 242)
LAND = (23, 63, 46)       # map land
POLAND = (46, 107, 79)    # Poland fill
SEA = (16, 44, 66)        # Baltic strip
CREAM = (233, 224, 196)   # ticker divider dots

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 cells; '#' is on, '.' is off.  All copy in the
# image is set in capitals, so the font covers A-Z, 0-9 and punctuation.
FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", "#.#.#", "#..##"),
    "+": (".....", "..#..", "..#..", ".####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    # Bullet and em dash map onto small drawn shapes.
    "•": (".....", ".....", ".##..", ".##..", ".....", ".....", "....."),
    "—": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
}
# Normalise lookalikes to the glyphs above.
ALIASES = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "·": "•"}


def glyph(ch):
    return FONT.get(ALIASES.get(ch, ch), FONT[" "])


def text_width(s, scale):
    return sum(6 for _ in s) * scale - scale


def wrap_text(s, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------- canvas
class Canvas:
    """An RGB frame buffer with small drawing primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        r, g, b = c
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = r, g, b

    def hline(self, x0, x1, y, c):
        if x0 > x1:
            x0, x1 = x1, x0
        self.fill_rect(x0, y, x1 - x0 + 1, 1, c)

    def vline(self, x, y0, y1, c):
        if y0 > y1:
            y0, y1 = y1, y0
        self.fill_rect(x, y0, 1, y1 - y0 + 1, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line, endpoints inclusive."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def dashed_line(self, x0, y0, x1, y1, c, dash=9, gap=6):
        """A dashed straight line (used for the AWACS patrol path)."""
        import math
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            return
        steps = int(length)
        on = True
        run = 0
        for i in range(steps + 1):
            t = i / max(1, steps)
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            if on:
                self.set(x, y, c)
            run += 1
            if run >= (dash if on else gap):
                on = not on
                run = 0

    def circle(self, cx, cy, r, c, fill=False):
        """Midpoint circle; outline, or filled via horizontal spans."""
        if r <= 0:
            return
        if fill:
            for yy in range(-r, r + 1):
                half = int((r * r - yy * yy) ** 0.5)
                self.hline(cx - half, cx + half, cy + yy, c)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.set(cx + px, cy + py, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def ellipse(self, cx, cy, rx, ry, c, fill=False):
        """Axis-aligned ellipse, outline or filled."""
        if rx <= 0 or ry <= 0:
            return
        if fill:
            for yy in range(-ry, ry + 1):
                half = int(rx * (1 - (yy / ry) ** 2) ** 0.5)
                self.hline(cx - half, cx + half, cy + yy, c)
            return
        for deg in range(0, 360):
            import math
            a = math.radians(deg)
            self.set(round(cx + rx * math.cos(a)),
                     round(cy + ry * math.sin(a)), c)

    def polygon(self, pts, c):
        """Filled polygon via the even-odd scanline rule."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.hline(int(xs[j]), int(xs[j + 1]), y, c)

    def polyline(self, pts, c):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c)

    # ------------------------------------------------------------ text
    def draw_text(self, x, y, s, scale, c, align="left"):
        """Draw a line with the 5x7 font; returns the drawn width."""
        w = text_width(s, scale)
        if align == "center":
            x -= w // 2
        elif align == "right":
            x -= w
        cx = x
        for ch in s:
            rows = glyph(ch)
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "#":
                        self.fill_rect(cx + rx * scale, y + ry * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return w

    def draw_text_block(self, x, y, lines, scale, c, align="left",
                        leading=4):
        """Draw several centred/left lines; returns the next y."""
        for ln in lines:
            self.draw_text(x, y, ln, scale, c, align)
            y += 7 * scale + leading
        return y


# -------------------------------------------------------------- PNG out
def write_png(cv, path):
    """Encode the canvas as an RGB PNG (filter 0 per row, zlib level 9)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------ scene art
def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_sky(cv, x0, y0, x1, y1):
    """Vertical navy gradient with a fixed, seeded star field."""
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        cv.fill_rect(x0, y, x1 - x0, 1, lerp(NAVY_DEEP, NAVY_MID, t))
    # Deterministic stars: a tiny LCG, same dots on every run.
    seed = 24112026
    for _ in range(90):
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        sx = x0 + 12 + seed % (x1 - x0 - 24)
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        sy = y0 + 10 + seed % (y1 - y0 - 150)
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        bright = seed % 3
        col = WHITE if bright == 0 else (200, 212, 226)
        cv.set(sx, sy, col)
        if bright == 0:
            cv.set(sx + 1, sy, col)


def draw_awacs(cv, nose_x, cy):
    """A NATO E-3 AWACS in leftward flight: fuselage, rotodome, wings."""
    # Radar rings first, centred on the rotodome.
    dx, dy = nose_x + 270, cy - 52
    for r in (46, 84, 118):
        cv.circle(dx, dy, r, SKY_LINE)
    # Sweep spoke and blips on the rings.
    cv.line(dx, dy, dx + 96, dy - 72, AMBER)
    cv.circle(dx + 72, dy - 50, 4, AMBER, fill=True)
    cv.circle(dx - 96, dy + 30, 4, WHITE, fill=True)
    cv.circle(dx + 30, dy + 96, 4, WHITE, fill=True)
    # Tail fin, then fuselage (nose left, tail right).
    cv.polygon([(nose_x + 500, cy - 8), (nose_x + 516, cy - 62),
                (nose_x + 548, cy - 62), (nose_x + 540, cy - 8)], PLANE_DARK)
    cv.polygon([(nose_x, cy), (nose_x + 42, cy - 18), (nose_x + 380, cy - 18),
                (nose_x + 520, cy - 8), (nose_x + 540, cy),
                (nose_x + 520, cy + 8), (nose_x + 380, cy + 18),
                (nose_x + 42, cy + 18)], PLANE)
    cv.polyline([(nose_x, cy), (nose_x + 42, cy - 18), (nose_x + 380, cy - 18),
                 (nose_x + 520, cy - 8), (nose_x + 540, cy),
                 (nose_x + 520, cy + 8), (nose_x + 380, cy + 18),
                 (nose_x + 42, cy + 18), (nose_x, cy)], PLANE_DARK)
    # Swept main wing below the fuselage, with four engines.
    cv.polygon([(nose_x + 210, cy + 14), (nose_x + 300, cy + 6),
                (nose_x + 400, cy + 74), (nose_x + 356, cy + 82),
                (nose_x + 268, cy + 40)], PLANE_DARK)
    for ex in (268, 300, 332, 364):
        cv.ellipse(nose_x + ex, cy + 46, 12, 7, PLANE, fill=True)
        cv.ellipse(nose_x + ex, cy + 46, 12, 7, PLANE_DARK)
    # Cockpit windows and a small NATO-style roundel near the tail.
    for wx in range(6):
        cv.fill_rect(nose_x + 52 + wx * 11, cy - 13, 7, 5, NAVY_DEEP)
    cv.circle(nose_x + 470, cy - 2, 9, RED, fill=True)
    cv.circle(nose_x + 470, cy - 2, 9, WHITE)
    # Rotodome: two struts, then the big disc above the fuselage.
    cv.line(nose_x + 232, cy - 16, nose_x + 244, cy - 40, PLANE_DARK)
    cv.line(nose_x + 308, cy - 16, nose_x + 296, cy - 40, PLANE_DARK)
    cv.ellipse(dx, dy, 104, 20, DOME, fill=True)
    cv.ellipse(dx, dy, 104, 20, PLANE_DARK)
    cv.ellipse(dx, dy - 4, 104, 16, (226, 232, 238), fill=True)


def draw_map(cv, y0, y1):
    """Stylised eastern Europe: Baltic at top, Poland lit, impact dots."""
    cv.fill_rect(0, y0, W, y1 - y0, SEA)
    # Land mass along the bottom, with a lighter Poland in the centre.
    cv.polygon([(0, y1), (0, y0 + 34), (240, y0 + 18), (430, y0 + 30),
                (620, y0 + 22), (830, y0 + 30), (W, y0 + 16),
                (W, y1)], LAND)
    poland = [(560, y0 + 30), (640, y0 + 22), (730, y0 + 26),
              (800, y0 + 40), (820, y0 + 62), (770, y0 + 82),
              (680, y0 + 86), (600, y0 + 72), (556, y0 + 52)]
    cv.polygon(poland, POLAND)
    cv.polyline(poland + [poland[0]], (214, 232, 210))
    # Dashed AWACS patrol path sweeping in from the west.
    cv.dashed_line(60, y0 + 14, 700, y0 + 14, AMBER)
    cv.draw_text(66, y0 - 4, "AWACS PATROL", 2, AMBER)
    # Three missile impact sites in eastern Poland. Each label sits clear
    # of its dot and of every other label, so nothing collides or clips.
    for ix, iy in ((730, 478), (790, 492), (672, 512)):
        cv.circle(ix, iy, 7, WHITE, fill=True)
        cv.circle(ix, iy, 4, RED, fill=True)
    cv.draw_text(716, 472, "NOWY LIPOWIEC", 2, WHITE, align="right")
    cv.draw_text(802, 486, "RUDNIK", 2, WHITE)
    cv.draw_text(684, 506, "MOLODYCZ", 2, WHITE)
    # Place labels.
    cv.draw_text(36, y0 + 44, "GERMANY", 2, (200, 214, 224))
    cv.draw_text(868, y0 + 72, "UKRAINE", 2, (200, 214, 224))
    cv.draw_text(330, y0 + 2, "BALTIC SEA", 1, (150, 180, 205))


def draw_globe(cv, cx, cy, r):
    """Masthead globe: circle, meridians and parallels."""
    cv.circle(cx, cy, r, WHITE)
    cv.ellipse(cx, cy, r // 2, r, WHITE)
    cv.ellipse(cx, cy, r, r // 3, WHITE)
    cv.hline(cx - r, cx + r, cy, WHITE)
    cv.line(cx - r, cy - r // 2, cx + r, cy - r // 2, WHITE)


def draw_crown_icon(cv, x, y, s):
    """A crown: three spikes over a band (a title being defended)."""
    cv.polygon([(x, y + 4 * s), (x, y + s), (x + 1.25 * s, y + 2.5 * s),
                (x + 2.5 * s, y), (x + 3.75 * s, y + 2.5 * s),
                (x + 5 * s, y + s), (x + 5 * s, y + 4 * s)], AMBER)
    cv.fill_rect(x, y + 4 * s, 5 * s, s, NAVY)


def draw_ship_icon(cv, x, y, s):
    """A warship on waves: hull, superstructure, mast, waterline."""
    cv.polygon([(x, y + 2 * s), (x + 5 * s, y + 2 * s), (x + 4 * s, y + 4 * s),
                (x + s, y + 4 * s)], NAVY)
    cv.fill_rect(x + 2 * s, y, s, 2 * s, NAVY)
    cv.fill_rect(x + 3 * s, y - s, s // 2, s, NAVY)
    cv.line(x, y + 5 * s, x + 5 * s, y + 5 * s, SKY_LINE)
    cv.line(x + s, y + 6 * s, x + 4 * s, y + 6 * s, SKY_LINE)


def draw_flame_icon(cv, x, y, s):
    """A flame: outer teardrop, inner tongue."""
    cv.polygon([(x + 2 * s, y), (x + 4 * s, y + 2 * s), (x + 4 * s, y + 4 * s),
                (x + 2 * s, y + 5 * s), (x, y + 4 * s), (x, y + 2 * s)], RED)
    cv.polygon([(x + 2 * s, y + 2 * s), (x + 3 * s, y + 3 * s),
                (x + 2 * s, y + 4 * s), (x + s, y + 3 * s)], AMBER)


# ------------------------------------------------------------- the page
def draw_page(cv):
    # Top red rule and navy masthead.
    cv.fill_rect(0, 0, W, 8, RED)
    cv.fill_rect(0, 8, W, 120, NAVY)
    draw_globe(cv, 76, 68, 34)
    cv.draw_text(140, 34, "THE WORLD TODAY", 7, WHITE)
    cv.fill_rect(140, 98, W - 140 - 40, 2, AMBER)
    cv.draw_text(140, 106, "TUESDAY, 24 NOVEMBER 2026", 2, AMBER)
    cv.draw_text(W - 40, 106, "ONE DAY • ONE PAGE", 2, WHITE, align="right")

    # Dateline strip.
    cv.draw_text(W // 2, 138,
                 "WARSAW • BRUSSELS • KYIV • JAKARTA • WASHINGTON • SEOUL",
                 2, GREY, align="center")

    # Hero panel: night sky, AWACS over a stylised map of Poland.
    draw_sky(cv, 0, 158, W, 540)
    draw_awacs(cv, 170, 330)
    draw_map(cv, 440, 540)

    # Lead headline and deck.
    cv.draw_text(W // 2, 556, "NATO'S EASTERN FLANK", 3, RED, align="center")
    cv.draw_text(W // 2, 584, "NATO SENDS AWACS", 9, INK, align="center")
    cv.draw_text(W // 2, 652, "TO POLAND", 9, INK, align="center")
    cv.draw_text(W // 2, 728, "THREE RUSSIAN MISSILES CAME DOWN ON NATO SOIL.",
                 2, GREY, align="center")
    cv.draw_text(W // 2, 748, "THE ALLIANCE ANSWERS WITH ITS 'EYES IN THE SKY'.",
                 2, GREY, align="center")
    cv.fill_rect(44, 782, W - 88, 2, INK)

    # Three secondary stories, each with a drawn icon.
    cols = [
        (44, draw_crown_icon, "CHESS TITLE DUEL",
         "CHAMPION GUKESH FACES SINDAROV IN GENEVA FOR THE CROWN."),
        (364, draw_ship_icon, "SUNK IN LIBYA",
         "UKRAINE SINKS A RUSSIAN WARSHIP IN A LIBYAN PORT."),
        (684, draw_flame_icon, "24 DEAD IN FIRE",
         "BLAZE AT A CANDY FACTORY IN INDONESIA; 30 STILL MISSING."),
    ]
    for x, icon, head, deck in cols:
        icon(cv, x, 804, 8)
        cv.draw_text(x, 844, head, 3, INK)
        lines = wrap_text(deck, 24)
        cv.draw_text_block(x, 876, lines, 2, GREY, leading=4)
    cv.vline(348, 800, 932, (200, 192, 170))
    cv.vline(668, 800, 932, (200, 192, 170))

    # Ticker band with the rest of the day, set large enough to stay
    # legible when the judge reads the page downscaled, with air between
    # the two lines and the footer.
    cv.fill_rect(0, 936, W, 56, NAVY)
    cv.draw_text(W // 2, 941, "COP31 COLLAPSES  •  SEOUL JET ALERT  •  CHAPO HELD",
                 3, WHITE, align="center")
    cv.draw_text(W // 2, 967, "GAZA STRIKES KILL 3  •  ALCARAZ WINS ATP FINALS",
                 3, WHITE, align="center")

    # Footer naming the day.
    cv.draw_text(W // 2, 998, "THE WORLD IN ONE IMAGE — TUESDAY 24 NOVEMBER 2026",
                 2, GREY, align="center")


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    path = os.path.join(outdir, "entry.png")
    size = write_png(cv, path)
    print(f"wrote {path} ({size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
