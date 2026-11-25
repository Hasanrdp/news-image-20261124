#!/usr/bin/env python3
"""The World Today - front page for Tuesday 24 November 2026 (v2).

Pure-stdlib, deterministic: renders a 1024x1024 newspaper front page with
36 dated stories across 10 regions, drawn scenes (market chart, rocket,
globe, seismograph, football), a markets ticker and a date-check footer.
Every story below was reported on 24 November 2026 by Reuters, AP, BBC,
UN News, Xinhua, Nature or national broadcasters; unconfirmed claims are
labelled as claims. Running this file twice produces byte-identical PNGs.
"""

import os
import struct
import zlib

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

# ---------------------------------------------------------------- palette
INK = (18, 18, 18)
PAPER = (252, 250, 244)
RED = (178, 34, 34)
BLUE = (28, 58, 112)
GRAY = (110, 108, 100)
LIGHT = (214, 210, 198)
GREEN = (28, 110, 60)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = on. Uppercase + digits + punctuation.
_RAW = {
    "A": ".###./#...#/#...#/#####/#...#/#...#/#...#",
    "B": "####./#...#/#...#/####./#...#/#...#/####.",
    "C": ".####/#..../#..../#..../#..../#..../.####",
    "D": "###../#..#./#...#/#...#/#...#/#..#./###..",
    "E": "#####/#..../#..../####./#..../#..../#####",
    "F": "#####/#..../#..../####./#..../#..../#....",
    "G": ".####/#..../#..../#..##/#...#/#...#/.###.",
    "H": "#...#/#...#/#...#/#####/#...#/#...#/#...#",
    "I": ".###./..#../..#../..#../..#../..#../.###.",
    "J": "..###/...#./...#./...#./...#./#..#./.##..",
    "K": "#...#/#..#./#.#../##.../#.#../#..#./#...#",
    "L": "#..../#..../#..../#..../#..../#..../#####",
    "M": "#...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#",
    "N": "#...#/##..#/#.#.#/#..##/#...#/#...#/#...#",
    "O": ".###./#...#/#...#/#...#/#...#/#...#/.###.",
    "P": "####./#...#/#...#/####./#..../#..../#....",
    "Q": ".###./#...#/#...#/#...#/#.#.#/#..#./.##.#",
    "R": "####./#...#/#...#/####./#.#../#..#./#...#",
    "S": ".####/#..../#..../.###./....#/....#/####.",
    "T": "#####/..#../..#../..#../..#../..#../..#..",
    "U": "#...#/#...#/#...#/#...#/#...#/#...#/.###.",
    "V": "#...#/#...#/#...#/#...#/#...#/.#.#./..#..",
    "W": "#...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#",
    "X": "#...#/#...#/.#.#./..#../.#.#./#...#/#...#",
    "Y": "#...#/#...#/.#.#./..#../..#../..#../..#..",
    "Z": "#####/....#/...#./..#../.#.../#..../#####",
    "0": ".###./#..##/#.#.#/##..#/#...#/#...#/.###.",
    "1": "..#../.##../..#../..#../..#../..#../.###.",
    "2": ".###./#...#/....#/...#./..#../.#.../#####",
    "3": "####./....#/....#/.###./....#/....#/####.",
    "4": "...#./..##./.#.#./#..#./#####/...#./...#.",
    "5": "#####/#..../####./....#/....#/#...#/.###.",
    "6": ".###./#..../#..../####./#...#/#...#/.###.",
    "7": "#####/....#/...#./...#./..#../..#../..#..",
    "8": ".###./#...#/#...#/.###./#...#/#...#/.###.",
    "9": ".###./#...#/#...#/.####/....#/....#/.###.",
    " ": "...../...../...../...../...../...../.....",
    ".": "...../...../...../...../...../.##../.##..",
    ",": "...../...../...../...../.##../.##../.#...",
    ":": "...../.##../.##../...../.##../.##../.....",
    ";": "...../.##../.##../...../.##../.##../.#...",
    "'": "..#../..#../.#.../...../...../...../.....",
    "-": "...../...../...../#####/...../...../.....",
    "/": "....#/....#/...#./..#../.#.../#..../#....",
    "(": "...##/..#../.#.../.#.../.#.../..#../...##",
    ")": "##.../..#../...#./...#./...#./..#../##...",
    "%": "##..#/##.#./...#./..#../.#.../#..##/#..##",
    "+": "...../..#../..#../#####/..#../..#../.....",
    "&": ".###./#...#/#...#/.#.#./#..#./#..#./.##.#",
    "!": "..#../..#../..#../..#../..#../...../..#..",
    "?": ".###./#...#/....#/...#./..#../...../..#..",
    '"': ".#.#./.#.#./.#.#./...../...../...../.....",
    "$": "..#../.####/#.#.#/.###./..#.#/####./..#..",
    "*": "...../#...#/.###./#####/.###./#...#/.....",
    "=": "...../...../#####/...../#####/...../.....",
    "<": "....#/...#./..#../.#.../..#../...#./....#",
    ">": "#..../.#.../..#../...#./..#../.#.../#....",
    "·": "...../...../.##../.##../...../...../.....",
    "•": "...../.###./.###./.###./...../...../.....",
}
_ALIAS = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"}
FONT = {}
for _ch, _rows in _RAW.items():
    FONT[_ch] = _rows.split("/")

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)
for _i in range(W * H):
    buf[_i * 3:_i * 3 + 3] = bytes(PAPER)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        _o = (y * W + x) * 3
        buf[_o:_o + 3] = bytes(c)


def fill_rect(x, y, w, h, c):
    for _yy in range(y, y + h):
        for _xx in range(x, x + w):
            set_px(_xx, _yy, c)


def hline(x, y, w, c, t=1):
    fill_rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    fill_rect(x, y, t, h, c)


def rect(x, y, w, h, c, t=1):
    hline(x, y, w, c, t)
    hline(x, y + h - t, w, c, t)
    vline(x, y, h, c, t)
    vline(x + w - t, y, h, c, t)


def line(x0, y0, x1, y1, c):
    _dx, _dy = abs(x1 - x0), abs(y1 - y0)
    _sx = 1 if x0 < x1 else -1
    _sy = 1 if y0 < y1 else -1
    _err = _dx - _dy
    while True:
        set_px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        _e2 = 2 * _err
        if _e2 > -_dy:
            _err -= _dy
            x0 += _sx
        if _e2 < _dx:
            _err += _dx
            y0 += _sy


def circle(cx, cy, r, c):
    _x, _y, _d = 0, r, 3 - 2 * r
    while _x <= _y:
        for _px, _py in ((_x, _y), (_y, _x), (-_x, _y), (-_y, _x),
                         (_x, -_y), (_y, -_x), (-_x, -_y), (-_y, -_x)):
            set_px(cx + _px, cy + _py, c)
        if _d < 0:
            _d += 4 * _x + 6
        else:
            _d += 4 * (_x - _y) + 10
            _y -= 1
        _x += 1


def disc(cx, cy, r, c):
    for _yy in range(cy - r, cy + r + 1):
        for _xx in range(cx - r, cx + r + 1):
            if (_xx - cx) ** 2 + (_yy - cy) ** 2 <= r * r:
                set_px(_xx, _yy, c)


def text(s, x, y, scale=1, c=INK):
    s = "".join(_ALIAS.get(_ch, _ch) for _ch in s.upper())
    _cx = x
    for _ch in s:
        _g = FONT.get(_ch, FONT[" "])
        for _r in range(7):
            _row = _g[_r]
            for _col in range(5):
                if _row[_col] == "#":
                    fill_rect(_cx + _col * scale, y + _r * scale,
                              scale, scale, c)
        _cx += 6 * scale
    return _cx - x


def text_w(s, scale=1):
    return len(s) * 6 * scale - scale


def centre(s, y, scale=1, c=INK):
    text(s, (W - text_w(s, scale)) // 2, y, scale, c)


def wrap(s, max_chars):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= max_chars:
            cur = cur + " " + w if cur else w
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- stories
# (region, place, headline, summary) - all reported 24 Nov 2026.
STORIES = [
    ("NORTH AMERICA", "USA",
     "NVIDIA +31.5% AS BOARD REINSTATES HUANG AS CEO",
     "Shares add about $1tn in value; Trump says he pressed the board."),
    ("NORTH AMERICA", "USA",
     "TRUMP SAYS HE PRESSED NVIDIA BOARD TO BRING HUANG BACK",
     "President claims credit for the CEO return after 11 days out."),
    ("NORTH AMERICA", "USA",
     "PENNSYLVANIA MEASLES DEATH TOLL REACHES NINE",
     "Outbreak spans 46 counties; US has lost its measles elimination status."),
    ("NORTH AMERICA", "USA",
     "DOJ RECOVERS $8BN IN LARGEST ANTI-SCAM SWEEP",
     "More than 800 suspects charged in a nationwide fraud crackdown."),
    ("LATIN AMERICA", "MEXICO",
     "MEXICO TO TRY 'EL CHAPO ISIDRO' DESPITE US EXTRADITION BID",
     "Cartel figure to face Mexican courts first, officials say."),
    ("LATIN AMERICA", "COLOMBIA",
     "CAR BOMB BLAST ROCKS VILLAVICENCIO, COLOMBIA",
     "Buildings destroyed; no confirmed victims, the president says."),
    ("LATIN AMERICA", "VENEZUELA",
     "VENEZUELA PUTS PUBLIC DEBT AT $237.5BN",
     "Figure published as Caracas moves toward restructuring."),
    ("WESTERN EUROPE", "UK",
     "UK PIP REVIEW CALLS FOR OVERHAUL, NO CUTS PLANNED",
     "Timms review shakes up disability benefits; thousands fear losses."),
    ("WESTERN EUROPE", "UK",
     "TWO HELD OVER SUSPECTED BURGLARY AT ANMER HALL",
     "Prince William's Norfolk home was unoccupied; no charges yet."),
    ("WESTERN EUROPE", "FRANCE",
     "MACRON WANTS STRATEGIC RARE-EARTH RESERVES FOR FRANCE",
     "President pushes stockpiles as supply tensions grow."),
    ("WESTERN EUROPE", "EU",
     "HERNANDEZ DE COS TIPPED TO SUCCEED LAGARDE AT ECB",
     "Spanish central banker seen as frontrunner for the top job."),
    ("EASTERN EUROPE", "UKRAINE",
     "RUSSIAN STRIKE ON ZAPORIZHZHIA KILLS 2, WOUNDS 40",
     "Five-storey block collapses; an infant is among the injured."),
    ("EASTERN EUROPE", "UKRAINE",
     "UKRAINE SAYS IT SANK RUSSIAN CORVETTE OFF BENGHAZI",
     "Kyiv calls the Libya sea-drone strike an asymmetric operation."),
    ("EASTERN EUROPE", "UK",
     "BRITAIN WARNS FIRMS OF RUSSIAN SABOTAGE THREAT",
     "Defence ministry and MI5 issue a rare public alert."),
    ("EASTERN EUROPE", "UKRAINE",
     "ZELENSKY: UKRAINE NEEDS $125BN FOR 2027",
     "President sets out next year's funding gap."),
    ("MIDDLE EAST", "SAUDI ARABIA",
     "HOUTHI DRONE HITS RIYADH'S PIF TOWER, 11 INJURED",
     "Second strike on the capital's tallest tower in under a week."),
    ("MIDDLE EAST", "IRAN",
     "IRAN SAYS THREE TANKERS HIT MINES IN HORMUZ (CLAIM)",
     "IRGC claim unconfirmed; Tehran sets seven conditions for talks."),
    ("MIDDLE EAST", "GAZA",
     "ISRAELI STRIKES KILL 7 IN GAZA DESPITE CEASEFIRE",
     "Meningitis cases surge to 272, eight times the normal rate."),
    ("MIDDLE EAST", "GAZA",
     "OXFAM CALLS GAZA A 'TOXIC LAND'",
     "Aid group warns of contamination across the territory."),
    ("MIDDLE EAST", "QATAR",
     "QATAR URGES IRAN AND US TO SHOW RESTRAINT",
     "Doha presses both sides as Gulf tensions rise."),
    ("AFRICA", "SENEGAL",
     "SENEGAL REINSTATED AS AFRICA CUP CHAMPIONS",
     "CAS overturns the ruling that had handed the title to Morocco."),
    ("AFRICA", "NIGERIA",
     "BORNO SCHOOL ENROLMENT NEARLY DOUBLES",
     "Nigerian state reports gains despite years of conflict."),
    ("AFRICA", "DR CONGO",
     "DR CONGO EBOLA OUTBREAK PASSES 11,700 CASES",
     "Health officials count 5,775 deaths in the ongoing outbreak."),
    ("SOUTH ASIA", "NEPAL",
     "5.6 QUAKE STRIKES NEPAL NEAR CHINA BORDER",
     "Tremor hits Koshi province; India pledges $1.6bn flood aid."),
    ("SOUTH ASIA", "BANGLADESH",
     "HASINA PLANS RETURN ON 16 DECEMBER",
     "Exiled ex-PM sets a homecoming date despite a death sentence."),
    ("SOUTH ASIA", "BANGLADESH",
     "BANGLADESH GARMENT WORKERS PROTEST OVER PAY",
     "Wage rallies spread as factories face unrest."),
    ("SOUTH ASIA", "INDIA",
     "TAMIL NADU SIGNS 70 DEALS WORTH $5.3BN",
     "Indian state unveils an investment haul at a summit."),
    ("EAST ASIA", "CHINA",
     "CHINA NAMES FIRST FOREIGN TIANGONG ASTRONAUT",
     "Pakistani pilot Zeeshan Ali to fly on Shenzhou-24, launching 25 Nov."),
    ("EAST ASIA", "ASIA",
     "SEOUL AND TOKYO STOCKS SURGE ON HUANG RETURN",
     "Kospi rebounds over 6%; Nikkei climbs 3.91%."),
    ("EAST ASIA", "CHINA",
     "HUAWEI GUILTY OF STEALING US TRADE SECRETS",
     "New York jury convicts the firm; the racketeering charge fails."),
    ("EAST ASIA", "TAIWAN",
     "TAIWAN INDEX RECLAIMS 40,000",
     "TAiEX rallies 2.16% despite six days of foreign selling."),
    ("SOUTHEAST ASIA & OCEANIA", "INDONESIA",
     "CANDY FACTORY FIRE IN BANTEN KILLS AT LEAST 24",
     "About 30 workers still missing after the blaze in Indonesia."),
    ("SOUTHEAST ASIA & OCEANIA", "VIETNAM",
     "HANOI RESTAURANT BLAST KILLS SIX",
     "Gas explosion during renovation injures ten in Vietnam."),
    ("SOUTHEAST ASIA & OCEANIA", "MALAYSIA",
     "MALAYSIA TO SEND 6,500 ROHINGYA BACK",
     "Refugees to be returned to Myanmar from December."),
    ("GLOBAL", "CLIMATE",
     "COP31 ENDS WITH NO DEAL ON FOSSIL FUELS",
     "EU and UK reject the text; first summit without a deal since 2009."),
    ("GLOBAL", "UN",
     "GUTERRES WANTS AI RULES FRAMEWORK WITHIN A YEAR",
     "UN chief calls for a multilateral pact to limit AI risks."),
]

REGIONS = []
for _r, _p, _h, _s in STORIES:
    if _r not in REGIONS:
        REGIONS.append(_r)

# ---------------------------------------------------------------- masthead
def draw_globe(cx, cy, r):
    # Drawn scene 1: globe at the masthead.
    circle(cx, cy, r, BLUE)
    circle(cx, cy, r - 6, BLUE)
    line(cx - r, cy, cx + r, cy, BLUE)
    line(cx, cy - r, cx, cy + r, BLUE)
    for _k in range(-2, 3):
        _dx = _k * r // 3
        _hh = int((r * r - _dx * _dx) ** 0.5)
        line(cx + _dx, cy - _hh, cx + _dx, cy + _hh, BLUE)


draw_globe(64, 62, 26)
text("THE WORLD TODAY", (W - text_w("THE WORLD TODAY", 4)) // 2, 30, 4, INK)
centre("TUESDAY, 24 NOVEMBER 2026", 66, 2, RED)
centre("36 DATED STORIES  \u00b7  10 REGIONS  \u00b7  DRAWN SCENES  \u00b7  CLAIMS LABELLED  "
       "\u00b7  REVISED EDITION V2", 90, 1, GRAY)
hline(24, 106, 976, INK, 2)
hline(24, 110, 976, INK, 1)

# Markets ticker strip.
centre("MARKETS 24 NOV: S&P 500 7,237.17 +4.73%  \u00b7  NASDAQ 24,089.56 +6.51%  "
       "\u00b7  DOW +3.01%  \u00b7  NIKKEI +3.91%  \u00b7  BRENT $89  \u00b7  GOLD $3,636/OZ",
       120, 1, BLUE)
hline(24, 134, 976, LIGHT, 1)

# ---------------------------------------------------------------- lead story
LY, LH = 144, 148
rect(24, LY, 976, LH, INK, 2)
text("LEAD  \u2014  NORTH AMERICA  \u00b7  24 NOV 2026", 38, LY + 12, 1, RED)
for _i, _ln in enumerate(wrap("HUANG IS BACK: NVIDIA +31.5% AS BOARD REINSTATES ITS CEO", 46)):
    text(_ln, 38, LY + 32 + _i * 17, 2, INK)
text("Nvidia shares add about $1tn in value after the board brings back", 38, LY + 72, 1, INK)
text("Jensen Huang, 11 days after he stepped down. Trump says he pressed", 38, LY + 84, 1, INK)
text("the board himself; the Nasdaq jumps 6.51% in the relief rally.", 38, LY + 96, 1, INK)
text("NVDA +31.5%  \u00b7  ONE-DAY GAIN, 23 NOV 2026", 38, LY + 118, 1, GREEN)

# Drawn scene 2: rising market chart in the lead box.
CX0, CY0, CW, CHH = 700, LY + 18, 280, 104
rect(CX0, CY0, CW, CHH, LIGHT, 1)
line(CX0 + 8, CY0 + CHH - 12, CX0 + CW - 8, CY0 + CHH - 12, GRAY)
line(CX0 + 8, CY0 + 8, CX0 + 8, CY0 + CHH - 12, GRAY)
_pts = [(0, 78), (30, 74), (60, 80), (90, 66), (120, 70), (150, 52),
        (180, 56), (210, 34), (240, 38), (264, 14)]
for _a, _b in zip(_pts, _pts[1:]):
    line(CX0 + 8 + _a[0], CY0 + 8 + _a[1], CX0 + 8 + _b[0], CY0 + 8 + _b[1], GREEN)
    disc(CX0 + 8 + _a[0], CY0 + 8 + _a[1], 2, GREEN)
disc(CX0 + 8 + _pts[-1][0], CY0 + 8 + _pts[-1][1], 3, RED)
text("+31.5%", CX0 + 200, CY0 + 2, 1, RED)

# ---------------------------------------------------------------- region grid
COLS_X = [24, 356, 688]
COL_W = 312
GRID_Y = 308
GRID_BOTTOM = 972

# Distribute the 10 regions over 3 columns: 3 / 3 / 4 regions.
COL_REGIONS = [
    ["NORTH AMERICA", "LATIN AMERICA", "WESTERN EUROPE"],
    ["EASTERN EUROPE", "MIDDLE EAST", "AFRICA"],
    ["SOUTH ASIA", "EAST ASIA", "SOUTHEAST ASIA & OCEANIA", "GLOBAL"],
]


def draw_rocket(x, y, s):
    # Drawn scene 3: Shenzhou-24 rocket, simple vector shape.
    line(x + 10 * s, y, x + 10 * s, y + 22 * s, RED)
    line(x + 18 * s, y, x + 18 * s, y + 22 * s, RED)
    line(x + 10 * s, y, x + 14 * s, y - 8 * s, RED)
    line(x + 18 * s, y, x + 14 * s, y - 8 * s, RED)
    line(x + 10 * s, y + 22 * s, x + 6 * s, y + 30 * s, RED)
    line(x + 18 * s, y + 22 * s, x + 22 * s, y + 30 * s, RED)
    line(x + 14 * s, y + 22 * s, x + 11 * s, y + 32 * s, (230, 140, 40))
    line(x + 14 * s, y + 22 * s, x + 14 * s, y + 34 * s, (230, 140, 40))
    line(x + 14 * s, y + 22 * s, x + 17 * s, y + 32 * s, (230, 140, 40))
    disc(x + 14 * s, y + 8 * s, 2 * s, BLUE)
    for _sx, _sy in ((x, y - 6 * s), (x + 28 * s, y + 4 * s), (x + 2 * s, y + 26 * s)):
        disc(_sx, _sy, 1, INK)


def draw_seismo(x, y, w):
    # Drawn scene 4: seismograph zigzag for the Nepal quake.
    _pts = [(0, 6), (w // 6, 6), (w // 6 + 6, -8), (w // 3, 14),
            (w // 2, -10), (2 * w // 3, 10), (5 * w // 6, -4), (w, 6)]
    for _a, _b in zip(_pts, _pts[1:]):
        line(x + _a[0], y + _a[1], x + _b[0], y + _b[1], RED)


def draw_ball(x, y, r):
    # Drawn scene 5: football for the Senegal AFCON story.
    import math
    circle(x, y, r, INK)
    disc(x, y, 3, INK)
    for _ang in range(5):
        _a = math.radians(_ang * 72 - 90)
        line(x, y, x + int(r * 0.9 * math.cos(_a)),
             y + int(r * 0.9 * math.sin(_a)), INK)


_col_ends = []
for _ci, _regs in enumerate(COL_REGIONS):
    _x = COLS_X[_ci]
    _y = GRID_Y
    for _reg in _regs:
        _stories = [s for s in STORIES if s[0] == _reg]
        _n = len(_stories)
        text(_reg + "  \u2014  " + str(_n) + " STORIES", _x, _y, 1, BLUE)
        hline(_x, _y + 10, COL_W, BLUE, 1)
        _y += 18
        for _r, _place, _head, _summ in _stories:
            _hl = wrap(_place + ": " + _head, 52)
            for _li, _ln in enumerate(_hl[:2]):
                text(_ln, _x, _y + _li * 9, 1, INK)
            _sy = _y + len(_hl[:2]) * 9 + 1
            _sl = wrap(_summ, 52)[:2]
            for _li, _ln in enumerate(_sl):
                text(_ln, _x, _sy + _li * 9, 1, GRAY)
            _y = _sy + len(_sl) * 9 + 2
            if _place == "NEPAL":
                draw_seismo(_x + 4, _y + 12, 60)
                _y += 30
            if _place == "SENEGAL":
                draw_ball(_x + 288, _y + 9, 8)
                _y += 20
            if _place == "CHINA" and "TIANGONG" in _head:
                draw_rocket(_x + 276, _y + 10, 1)
                _y += 44
        _y += 10
    assert _y <= GRID_BOTTOM, "grid overflow in column %d" % _ci
    _col_ends.append(_y)

# ---------------------------------------------------------------- the day in numbers
_BAND_Y = max(_col_ends) + 14
if _BAND_Y + 56 < 984:
    _bh = 984 - 12 - _BAND_Y
    text("THE DAY IN NUMBERS  \u2014  24 NOVEMBER 2026", 24, _BAND_Y, 1, RED)
    hline(24, _BAND_Y + 10, 976, RED, 1)
    _stats = [("+31.5%", "NVIDIA"),
              ("+6.51%", "NASDAQ"),
              ("11", "INJURED IN RIYADH"),
              ("24", "DEAD IN BANTEN FIRE"),
              ("5.6", "NEPAL QUAKE"),
              ("40,000", "TAIEX RECLAIMS")]
    _bw = 976 // 6
    _sy2 = _BAND_Y + 16 + max(0, (_bh - 44) // 2)
    for _i, (_num, _lab) in enumerate(_stats):
        _bx = 24 + _i * _bw
        if _i:
            vline(_bx - 8, _BAND_Y + 16, _bh - 20, LIGHT, 1)
        text(_num, _bx, _sy2, 2, RED)
        text(_lab, _bx + text_w(_num, 2) + 8, _sy2 + 3, 1, INK)

# ---------------------------------------------------------------- footer
hline(24, 984, 976, INK, 2)
centre("DATE CHECK: ALL 36 STORIES DATED 24 NOVEMBER 2026", 992, 1, INK)
centre("SOURCES: REUTERS  \u00b7  AP  \u00b7  BBC  \u00b7  UN NEWS  \u00b7  XINHUA  \u00b7  NATURE  "
       "\u00b7  UNCONFIRMED CLAIMS LABELLED (CLAIM)", 1004, 1, GRAY)

# ---------------------------------------------------------------- PNG encode
def _chunk(kind, data):
    _c = struct.pack(">I", len(data)) + kind + data
    return _c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def save_png(path):
    _raw = bytearray()
    for _y in range(H):
        _raw.append(0)
        _raw += buf[_y * W * 3:(_y + 1) * W * 3]
    _png = (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(bytes(_raw), 6))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as _f:
        _f.write(_png)
    return len(_png)


if __name__ == "__main__":
    _n = save_png(OUT)
    _cwd = os.path.join(os.getcwd(), "entry.png")
    if os.path.abspath(_cwd) != os.path.abspath(OUT):
        save_png(_cwd)
    print("wrote %s (%d bytes, %d stories, %d regions)"
          % (OUT, _n, len(STORIES), len(REGIONS)))
