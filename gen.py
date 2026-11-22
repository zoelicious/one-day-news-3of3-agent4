#!/usr/bin/env python3
"""Build the 3/3 Agent 4 entry for news-image-20261121.

Draws a one-day newspaper front page for Saturday 21 November 2026:
cream paper, red masthead, 6-number stat strip, region bar totalling 35,
3 hero panels + 10 small panels (13 numbered), halftone world map with
pins 1-13, ALSO list 14-35, HOW WE CHECKED legend, DATE CHECK box.
Everything is drawn with PIL primitives; no generated imagery.
"""
import hashlib
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
CREAM = (248, 242, 228)
PANEL = (255, 253, 247)
INK = (26, 26, 26)
RED = (176, 30, 36)
RULE = (160, 145, 115)
MUTED = (110, 100, 80)
SKY = (214, 228, 238)
SEA = (196, 214, 226)

SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def wrap(text, font, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if font.getlength(trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_c(d, cx, y, s, font, fill=INK):
    w = font.getlength(s)
    d.text((cx - w / 2, y), s, font=font, fill=fill)


def para(d, x, y, lines, font, fill=INK, leading=None):
    if leading is None:
        leading = font.size + 3
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


CHIP_FILL = {
    "OFFICIAL": (30, 122, 52),
    "CONFIRMED": (29, 78, 158),
    "REPORTED": (178, 120, 20),
    "CLAIM": (107, 107, 107),
}


def chip(d, x, y, label):
    f = F(SANS_B, 9)
    w = f.getlength(label) + 10
    d.rounded_rectangle([x, y, x + w, y + 14], radius=7, fill=CHIP_FILL[label])
    d.text((x + 5, y + 2), label, font=f, fill=(255, 255, 255))
    return w


def badge(d, cx, cy, num, r=13):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED, outline=(255, 255, 255), width=2)
    f = F(SANS_B, 14 if num < 10 else 12)
    s = str(num)
    d.text((cx - f.getlength(s) / 2, cy - f.size / 2 - 1), s, font=f, fill=(255, 255, 255))


# ---------------------------------------------------------------- stories
# (num, kind, headline, body, verify, source, region, lon, lat)
HEROES = [
    (1, "COP31 deadlocks into day 13",
     "Antalya talks run into overtime with no deal. A third draft with no "
     "fossil-fuel phase-out splits ~200 nations.",
     "CONFIRMED", "REUTERS", "Global", 30.7, 36.9),
    (2, "Missiles downed over Riyadh",
     "Houthi missiles downed above the Saudi capital; two blasts about 02:00. "
     "No casualties.",
     "CONFIRMED", "REUTERS", "Middle East", 46.7, 24.7),
    (3, "M6.7 quake shakes Peru",
     "Junin / Carhuamayo, 00:09 UTC, 108 km deep. No deaths and no tsunami, "
     "officials say.",
     "OFFICIAL", "USGS", "Americas", -75.5, -11.0),
]

SMALL = [
    (4, "Double-tap strike on Kryvyi Rih",
     "Russia hits the Ukrainian city twice; 2 killed, 42 hurt.",
     "CONFIRMED", "AP", "Europe", 33.4, 47.9),
    (5, "Zelensky: Crimea bridge \u201cwill not stay\u201d",
     "Ukraine's president tells NBC the bridge \u201cwill not stay\u201d.",
     "REPORTED", "NBC", "Europe", 36.5, 45.3),
    (6, "Iran claims it downed a US drone",
     "Tehran claims an MQ-9 downed over Hormuz, its 58th claim.",
     "CLAIM", "REUTERS", "Middle East", 56.5, 26.5),
    (7, "Iran: uranium stays in Iran",
     "Tehran: its stockpile stays home; seeks a \u201cfair solution\u201d.",
     "OFFICIAL", "AP", "Middle East", 51.4, 35.7),
    (8, "Trump vows tax on foreign data centres",
     "A new tax promised on data centres abroad; no details yet.",
     "OFFICIAL", "AP", "Americas", -77.0, 38.9),
    (9, "China tells Japan: correct Taiwan words",
     "Beijing demands a correction; Tokyo: stance unchanged.",
     "OFFICIAL", "REUTERS", "Asia", 116.4, 39.9),
    (10, "767 lands safely in Davao",
     "Emergency landing ends with all 146 aboard safe.",
     "CONFIRMED", "AP", "Asia", 125.6, 7.1),
    (11, "EU\u2013Indonesia seal CEPA trade deal",
     "Tariffs fall on 98.5% of EU lines, 90.4% of Indonesia's.",
     "OFFICIAL", "REUTERS", "Asia", 4.35, 50.85),
    (12, "Mexico captures \u2018El Chapo Isidro\u2019",
     "Troops seize the cartel figure in Guasave; 11 killed.",
     "CONFIRMED", "AP", "Americas", -108.5, 25.6),
    (13, "Russell fastest; Verstappen on pole",
     "Russell 1:34.041 in wet practice; Verstappen takes pole.",
     "OFFICIAL", "REUTERS", "Americas", -115.1, 36.2),
]

# ALSO list 14-35: (num, text, region)
ALSO = [
    (14, "Rahul 124*, India 344/2 in Wellington", "Oceania"),
    (15, "BepiColombo reaches Mercury after 8 years", "Europe"),
    (16, "M6.8 Banda Sea quake, 132 km deep", "Asia"),
    (17, "Sparta II burns off Finland; 16 saved", "Europe"),
    (18, "Aswan Forum pushes debt relief", "Africa"),
    (19, "Bitcoin $58,983, down 3.9% in a day", "Americas"),
    (20, "Australia, China agree to talk on AI", "Oceania"),
    (21, "Rutte in Warsaw: defend \u2018every inch\u2019", "Europe"),
    (22, "Denmark expels Russian defence attach\u00e9", "Europe"),
    (23, "Freight train derails in Sejong", "Asia"),
    (24, "Kim visits a factory in Pyongyang", "Asia"),
    (25, "Bangkok unveils arsenic plan", "Asia"),
    (26, "SCO forum meets in New Delhi", "Asia"),
    (27, "Israel strikes Gaza; 6 killed", "Middle East"),
    (28, "Houthis threaten Jeddah", "Middle East"),
    (29, "ANC falls to 31%, worst since 1994", "Africa"),
    (30, "Vance: Iran strike is Trump's call", "Americas"),
    (31, "Roundup settlement: $7.25bn in Missouri", "Americas"),
    (32, "Texas execution takes 63 minutes", "Americas"),
    (33, "Palisades fire verdict in LA; 12 killed", "Americas"),
    (34, "First US measles death of 2026, Virginia", "Americas"),
    (35, "Starc 7/58 as Ashes open in Perth", "Oceania"),
]

REGIONS = [("Europe", 6, (46, 95, 163)), ("Asia", 8, (46, 125, 50)),
           ("Middle East", 5, (217, 123, 41)), ("Africa", 2, (141, 110, 99)),
           ("Americas", 10, (176, 30, 36)), ("Oceania", 3, (0, 131, 143)),
           ("Global", 1, (117, 117, 117))]

STATS = [
    ("M6.8", "BANDA SEA QUAKE,\n132 KM DEEP"),
    ("98.5%", "EU TARIFF LINES CUT\nIN EU\u2013INDONESIA CEPA"),
    ("11", "KILLED AS MEXICO\nCAPTURES \u2018EL CHAPO ISIDRO\u2019"),
    ("128", "NATIONS IN UN\nKILLER-ROBOT TALKS"),
    ("146", "SAFE AS AIR NIUGINI\n767 LANDS IN DAVAO"),
    ("$58,983", "BITCOIN,\nDOWN 3.9% IN 24 HOURS"),
]

# ------------------------------------------------------- flat illustrations
def art_cop31(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(178, 216, 178))
    d.ellipse([x + w / 2 - 34, y + 6, x + w / 2 + 34, y + 74], fill=(64, 130, 190))
    d.ellipse([x + w / 2 - 22, y + 16, x + w / 2 - 2, y + 32], fill=(96, 170, 90))
    d.ellipse([x + w / 2 + 4, y + 34, x + w / 2 + 24, y + 52], fill=(96, 170, 90))
    d.ellipse([x + w / 2 - 26, y + 44, x + w / 2 - 6, y + 60], fill=(120, 185, 110))
    d.text((x + 8, y + h - 20), "DAY 13", font=F(SANS_B, 13), fill=(26, 90, 40))
    d.ellipse([x + w - 26, y + 8, x + w - 10, y + 24], fill=(232, 160, 40))


def art_riyadh(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(28, 42, 74))
    for sx, sy in [(20, 12), (70, 22), (130, 10), (180, 26), (240, 14), (290, 24)]:
        d.ellipse([x + sx, y + sy, x + sx + 3, y + sy + 3], fill=(255, 255, 255))
    d.polygon([(x + 8, y + h), (x + 40, y + h - 34), (x + 72, y + h)], fill=(60, 60, 70))
    d.polygon([(x + 90, y + h), (x + 130, y + h - 48), (x + 170, y + h)], fill=(50, 50, 62))
    d.polygon([(x + 190, y + h), (x + 230, y + h - 30), (x + 270, y + h)], fill=(60, 60, 70))
    for (x1, y1, x2, y2) in [(60, 30, 110, 58), (150, 18, 200, 52), (230, 34, 280, 62)]:
        d.line([x + x1, y + y1, x + x2, y + y2], fill=(255, 200, 80), width=3)
        d.ellipse([x + x2 - 5, y + y2 - 5, x + x2 + 5, y + y2 + 5],
                  fill=(255, 220, 120), outline=(255, 140, 40), width=2)


def art_peru(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 214, 178))
    d.line([x + 6, y + 14, x + 40, y + 14, x + 52, y + 30, x + 70, y + 6,
            x + 92, y + 26, x + 120, y + 10, x + 150, y + 30, x + 180, y + 12,
            x + 210, y + 26, x + 250, y + 14, x + w - 6, y + 20],
           fill=(176, 30, 36), width=2)
    d.polygon([(x, y + h), (x + 90, y + 52), (x + 130, y + h)], fill=(150, 110, 70))
    d.polygon([(x + 150, y + h), (x + 230, y + 46), (x + w, y + h)], fill=(130, 95, 60))
    d.line([x + 130, y + 52, x + 150, y + 66, x + 138, y + 78, x + 168, y + h - 6],
           fill=(60, 40, 20), width=3)


def art_city(d, x, y, w, h, smoke=(220, 120, 60)):
    d.rectangle([x, y, x + w, y + h], fill=(226, 222, 210))
    for bx, bw, bh in [(8, 34, 30), (48, 26, 40), (80, 36, 26), (122, 30, 44), (158, 28, 32)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h], fill=(90, 88, 84))
        for wy in range(y + h - bh + 5, y + h - 4, 9):
            for wx in range(x + bx + 5, x + bx + bw - 5, 10):
                d.rectangle([wx, wy, wx + 4, wy + 5], fill=(240, 210, 90))
    d.ellipse([x + 120, y + 4, x + 140, y + 20], fill=smoke)
    d.ellipse([x + 132, y + 12, x + 152, y + 28], fill=smoke)


def art_bridge(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY)
    d.rectangle([x, y + h - 22, x + w, y + h], fill=(70, 130, 180))
    d.arc([x + 10, y + 6, x + w - 10, y + h + 10], 180, 360, fill=(90, 90, 90), width=5)
    for px in range(30, w - 20, 28):
        d.line([x + px, y + 18, x + px, y + h - 22], fill=(90, 90, 90), width=3)
    d.line([x, y + h - 30, x + w, y + h - 30], fill=(60, 60, 60), width=4)


def art_drone(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    for wy in (h - 18, h - 10):
        d.line([x + 4, y + wy, x + w - 4, y + wy], fill=(255, 255, 255), width=2)
    cx, cy = x + w / 2, y + 22
    d.ellipse([cx - 26, cy - 6, cx + 26, cy + 6], fill=(70, 70, 78))
    d.line([cx - 26, cy, cx - 44, cy - 8], fill=(70, 70, 78), width=3)
    d.line([cx + 26, cy, cx + 44, cy - 8], fill=(70, 70, 78), width=3)
    d.ellipse([cx - 4, cy - 10, cx + 4, cy - 2], fill=(40, 40, 46))
    d.line([cx - 52, cy + 16, cx + 52, cy + 16], fill=(176, 30, 36), width=2)


def art_atom(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(228, 226, 214))
    cx, cy = x + w / 2, y + h / 2 - 2
    for ang in (0, 60, 120):
        d.arc([cx - 34, cy - 14, cx + 34, cy + 14], 0, 360, fill=(60, 90, 140), width=2)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(176, 30, 36))
    d.rectangle([x + 14, y + h - 16, x + 34, y + h - 6], fill=(90, 90, 90))
    d.rectangle([x + 40, y + h - 16, x + 60, y + h - 6], fill=(110, 110, 110))


def art_servers(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 228, 232))
    for i, bx in enumerate((14, 66, 118)):
        d.rectangle([x + bx, y + 6, x + bx + 42, y + h - 8], fill=(60, 70, 84))
        for ry in range(y + 12, y + h - 12, 10):
            d.rectangle([x + bx + 5, ry, x + bx + 37, ry + 4], fill=(90, 200, 120) if i != 1 else (240, 200, 90))
    d.ellipse([x + w - 34, y + 4, x + w - 6, y + 32], fill=(232, 200, 60))
    d.text((x + w - 27, y + 7), "$", font=F(SANS_B, 16), fill=(120, 80, 0))


def art_flags(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(238, 236, 226))
    d.rectangle([x + 12, y + 10, x + 82, y + 34], fill=(222, 60, 60))
    for sx in range(x + 20, x + 76, 14):
        d.ellipse([sx, y + 17, sx + 5, y + 22], fill=(255, 220, 60))
    d.rectangle([x + 100, y + 10, x + 170, y + 34], fill=(255, 255, 255), outline=(180, 40, 40), width=2)
    d.ellipse([x + 128, y + 15, x + 142, y + 29], fill=(180, 40, 40))
    d.rounded_rectangle([x + 30, y + h - 22, x + w - 30, y + h - 6], radius=6, fill=(255, 255, 255), outline=(90, 90, 90))
    d.text((x + 40, y + h - 20), "\u201ccorrect it\u201d", font=F(SERIF_I, 11), fill=INK)


def art_plane(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY)
    d.ellipse([x + 130, y + 6, x + 146, y + 22], fill=(255, 255, 255))
    d.ellipse([x + 150, y + 12, x + 168, y + 28], fill=(255, 255, 255))
    d.polygon([(x + 18, y + 26), (x + 150, y + 20), (x + 168, y + 30), (x + 40, y + 40)], fill=(240, 240, 240))
    d.polygon([(x + 150, y + 20), (x + 176, y + 12), (x + 172, y + 30)], fill=(220, 60, 60))
    d.polygon([(x + 90, y + 40), (x + 108, y + 52), (x + 92, y + 52)], fill=(200, 200, 200))
    d.rectangle([x, y + h - 10, x + w, y + h - 4], fill=(80, 80, 80))
    for lx in range(10, w - 10, 26):
        d.rectangle([x + lx, y + h - 9, x + lx + 12, y + h - 5], fill=(255, 255, 255))
    d.ellipse([x + w - 30, y + h - 30, x + w - 12, y + h - 12], fill=(30, 122, 52))
    d.text((x + w - 25, y + h - 28), "\u2713", font=F(SANS_B, 12), fill=(255, 255, 255))


def art_cepa(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(226, 232, 244))
    cx, cy = x + 46, y + h / 2
    for k in range(12):
        import math
        a = math.radians(k * 30)
        sx, sy = cx + 26 * math.cos(a), cy + 26 * math.sin(a)
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(240, 200, 60))
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(29, 78, 158))
    d.text((cx - 5, cy - 9), "EU", font=F(SANS_B, 10), fill=(255, 255, 255))
    d.polygon([(x + 96, y + 16), (x + 112, y + 16), (x + 104, y + 34)], fill=(30, 122, 52))
    d.line([x + 104, y + 34, x + 104, y + h - 18], fill=(30, 122, 52), width=3)
    d.text((x + 118, y + 8), "\u221298.5%", font=F(SANS_B, 15), fill=(30, 122, 52))
    d.text((x + 118, y + 28), "tariffs", font=F(SANS, 10), fill=INK)


def art_sinaloa(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 220, 180))
    d.polygon([(x, y + h), (x + 50, y + 18), (x + 100, y + h)], fill=(180, 140, 90))
    d.polygon([(x + 80, y + h), (x + 140, y + 10), (x + w, y + h)], fill=(160, 120, 75))
    d.ellipse([x + w - 46, y + 6, x + w - 14, y + 38], fill=(240, 200, 60))
    cx, cy = x + 34, y + h - 22
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(29, 78, 158))
    d.text((cx - 5, cy - 8), "\u2605", font=F(SANS_B, 13), fill=(255, 255, 255))


def art_f1(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(30, 30, 40))
    for i in range(6):
        for j in range(2):
            c = (255, 255, 255) if (i + j) % 2 == 0 else (20, 20, 20)
            d.rectangle([x + 8 + i * 10, y + 6 + j * 10, x + 18 + i * 10, y + 16 + j * 10], fill=c)
    d.polygon([(x + 30, y + h - 18), (x + 110, y + h - 26), (x + 150, y + h - 18),
               (x + 150, y + h - 8), (x + 30, y + h - 8)], fill=(200, 30, 40))
    d.ellipse([x + 52, y + h - 16, x + 66, y + h - 2], fill=(20, 20, 20))
    d.ellipse([x + 122, y + h - 16, x + 136, y + h - 2], fill=(20, 20, 20))
    d.text((x + 84, y + 8), "1:34.041", font=F(SANS_B, 13), fill=(255, 220, 60))


ART = {1: art_cop31, 2: art_riyadh, 3: art_peru, 4: art_city, 5: art_bridge,
       6: art_drone, 7: art_atom, 8: art_servers, 9: art_flags, 10: art_plane,
       11: art_cepa, 12: art_sinaloa, 13: art_f1}


# ------------------------------------------------------------- halftone map
NA = [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-75, 73), (-55, 52),
      (-60, 45), (-75, 35), (-80, 25), (-90, 20), (-97, 16), (-105, 20),
      (-115, 30), (-125, 40), (-125, 49), (-145, 60), (-168, 66)]
SA = [(-80, 10), (-60, 8), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
      (-58, -35), (-65, -45), (-70, -55), (-73, -40), (-80, -20), (-80, -5),
      (-80, 10)]
AF = [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28),
      (43, 12), (51, 11), (48, 0), (40, -10), (35, -20), (30, -30), (20, -35),
      (15, -30), (12, -18), (9, -2), (9, 4), (-8, 5), (-17, 15)]
EU = [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
      (18, 56), (21, 55), (24, 59), (28, 60), (30, 62), (30, 68), (40, 68),
      (45, 66), (40, 60), (35, 55), (30, 50), (28, 45), (23, 40), (19, 42),
      (12, 44), (8, 44), (3, 42), (0, 38), (-9, 37), (-10, 36)]
AS = [(30, 68), (40, 68), (50, 70), (60, 70), (70, 72), (80, 73), (90, 75),
      (100, 77), (110, 76), (120, 73), (130, 72), (140, 72), (150, 70),
      (160, 66), (162, 60), (158, 52), (142, 50), (140, 40), (135, 35),
      (130, 33), (127, 35), (122, 38), (120, 32), (115, 23), (110, 20),
      (108, 12), (105, 9), (100, 8), (97, 15), (94, 17), (90, 22), (86, 20),
      (80, 15), (77, 8), (73, 16), (66, 25), (61, 25), (57, 26), (52, 28),
      (48, 30), (44, 29), (40, 31), (36, 36), (35, 42), (30, 46), (28, 50),
      (30, 55), (30, 60), (30, 68)]
AU = [(113, -22), (114, -30), (115, -35), (124, -33), (129, -32), (132, -32),
      (135, -35), (137, -35), (140, -38), (145, -38), (150, -37), (153, -32),
      (153, -27), (150, -23), (146, -19), (142, -15), (142, -11), (137, -12),
      (135, -15), (132, -12), (130, -13), (126, -14), (122, -17), (118, -20),
      (113, -22)]
LAND = [NA, SA, AF, EU, AS, AU]


def _inside(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xin = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < xin:
                inside = not inside
    return inside


def on_land(lon, lat):
    return any(_inside(lon, lat, p) for p in LAND)


# ------------------------------------------------------------------- layout
def hero_panel(d, x, y, w, h, st):
    num, head, body, verify, src, _reg, _lo, _la = st
    d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=RULE, width=1)
    ART[num](d, x + 1, y + 1, w - 2, 92)
    badge(d, x + 20, y + 20, num)
    hl = wrap(head, F(SERIF_B, 17), w - 16)
    yy = para(d, x + 8, y + 100, hl, F(SERIF_B, 17), leading=20)
    bl = wrap(body, F(SANS, 11), w - 16)[:2]
    para(d, x + 8, yy + 3, bl, F(SANS, 11), leading=14)
    chip(d, x + 8, y + h - 22, verify)
    sf = F(SANS, 8)
    d.text((x + w - 8 - sf.getlength(src), y + h - 20), src, font=sf, fill=MUTED)


def small_panel(d, x, y, w, h, st):
    num, head, body, verify, src, _reg, _lo, _la = st
    d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=RULE, width=1)
    ART[num](d, x + 1, y + 1, w - 2, 44)
    badge(d, x + 15, y + 15, num, r=11)
    hl = wrap(head, F(SERIF_B, 12), w - 12)[:2]
    yy = para(d, x + 6, y + 50, hl, F(SERIF_B, 12), leading=15)
    bl = wrap(body, F(SANS, 10), w - 12)[:3]
    para(d, x + 6, yy + 2, bl, F(SANS, 10), leading=12)
    chip(d, x + 6, y + h - 20, verify)
    sf = F(SANS, 8)
    d.text((x + w - 6 - sf.getlength(src), y + h - 18), src, font=sf, fill=MUTED)


PIN_ADJ = {1: (-6, -4), 2: (-7, 8), 4: (5, -7), 5: (16, -2), 6: (12, 12), 7: (8, 6)}


def draw_map(d, x0, y0, w, h):
    for gy in range(0, h, 6):
        lat = 84 - (gy + 3) / h * 142
        for gx in range(0, w, 6):
            lon = -180 + (gx + 3) / w * 360
            if on_land(lon, lat):
                d.ellipse([x0 + gx + 1, y0 + gy + 1, x0 + gx + 4, y0 + gy + 4],
                          fill=(138, 120, 90))
    for st in HEROES + SMALL:
        num, _hd, _bd, _vf, _src, _rg, lon, lat = st
        px = x0 + (lon + 180) / 360 * w
        py = y0 + (84 - lat) / 142 * h
        dx, dy = PIN_ADJ.get(num, (0, 0))
        px, py = px + dx, py + dy
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED,
                  outline=(255, 255, 255), width=1)
        f = F(SANS_B, 8)
        s = str(num)
        d.text((px - f.getlength(s) / 2, py - 5), s, font=f, fill=(255, 255, 255))


def main():
    # --- region totals must match the bar, or the paper contradicts itself
    counts = {}
    for st in HEROES + SMALL:
        counts[st[5]] = counts.get(st[5], 0) + 1
    for _n, _t, rg in ALSO:
        counts[rg] = counts.get(rg, 0) + 1
    total = sum(counts.values())
    assert total == 35, total
    for name, want, _c in REGIONS:
        assert counts.get(name, 0) == want, (name, counts.get(name, 0), want)

    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, W - 11, H - 11], outline=RULE, width=2)
    d.rectangle([14, 14, W - 15, H - 15], outline=RULE, width=1)

    # masthead + date
    text_c(d, W / 2, 22, "THE WORLD IN ONE DAY", F(SERIF_B, 40), RED)
    d.line([22, 70, W - 22, 70], fill=INK, width=2)
    d.line([22, 74, W - 22, 74], fill=INK, width=1)
    text_c(d, W / 2, 80, "Saturday 21 November 2026", F(SERIF_B, 44), INK)
    text_c(d, W / 2, 130,
           "COP31 deadlocked in Antalya  \u2022  Missiles over Riyadh  \u2022  Peru shakes \u2014 35 stories from one day",
           F(SERIF_I, 16), INK)

    # stat strip: 6 boxes
    bw, gap = 160, 4
    for i, (num, lab) in enumerate(STATS):
        bx = 22 + i * (bw + gap)
        d.rectangle([bx, 152, bx + bw, 204], fill=PANEL, outline=RULE, width=1)
        text_c(d, bx + bw / 2, 156, num, F(SERIF_B, 20), RED)
        for j, ln in enumerate(lab.split("\n")):
            text_c(d, bx + bw / 2, 181 + j * 10, ln, F(SANS_B, 8), MUTED)

    # region bar
    text_c(d, W / 2, 209, "STORIES BY REGION \u2014 35 IN ALL", F(SANS_B, 11), INK)
    bx, bw_total = 22, 980
    for name, count, col in REGIONS:
        seg = bw_total * count / 35
        d.rectangle([bx, 224, bx + seg, 240], fill=col)
        bx += seg
    d.rectangle([22, 224, 1002, 240], outline=INK, width=1)
    lx = 22
    items = []
    for name, count, col in REGIONS:
        items.append((f"{name} {count}", col))
    widths = [F(SANS_B, 10).getlength(t) + 14 for t, _c in items]
    lx = (W - sum(widths)) // 2
    for (t, col), wd in zip(items, widths):
        d.rectangle([lx, 246, lx + 9, 255], fill=col)
        d.text((lx + 12, 245), t, font=F(SANS_B, 10), fill=INK)
        lx += wd

    # heroes
    for i, st in enumerate(HEROES):
        hero_panel(d, 22 + i * 330, 264, 320, 182, st)

    # small panels, 2 rows of 5
    for r in range(2):
        for c in range(5):
            st = SMALL[r * 5 + c]
            small_panel(d, 22 + c * 198, 454 + r * 144, 188, 136, st)

    # bottom: map (left) + ALSO list (right)
    d.rectangle([22, 742, 452, 912], fill=PANEL, outline=RULE, width=1)
    d.text((30, 749), "WHERE IT HAPPENED", font=F(SANS_B, 12), fill=INK)
    d.text((30, 765), "Halftone world map \u2014 pins match the numbered stories above.",
           font=F(SANS, 9), fill=MUTED)
    draw_map(d, 28, 782, 418, 124)

    d.rectangle([464, 742, 1002, 912], fill=PANEL, outline=RULE, width=1)
    d.text((472, 749), "ALSO ON SATURDAY 21 NOVEMBER \u2014 22 MORE STORIES",
           font=F(SANS_B, 11), fill=INK)
    fnum, ftx = F(SANS_B, 10), F(SANS, 10)
    for i, (num, txt, _rg) in enumerate(ALSO):
        col = i // 11
        row = i % 11
        cx = 472 + col * 266
        cy = 772 + row * 12
        d.text((cx, cy), f"{num}.", font=fnum, fill=RED)
        d.text((cx + 24, cy), txt, font=ftx, fill=INK)

    # how we checked
    text_c(d, W / 2, 920,
           "HOW WE CHECKED:   OFFICIAL = authority statement   \u2022   CONFIRMED = 2+ outlets   \u2022   REPORTED = one outlet   \u2022   CLAIM = unverified claim",
           F(SANS_B, 10), INK)

    # date check
    d.rectangle([22, 938, 1002, 990], outline=RED, width=2)
    d.text((30, 943), "DATE CHECK \u2014 LEFT OUT ON PURPOSE", font=F(SANS_B, 11), fill=RED)
    dc = ("Not from 21 Nov: Wall Street's slide into correction; Russia's strike on Kyiv's bridge; "
          "a missile in Poland; the UK\u2013EU reset deal; Cyclone Akvan's landfall (all Fri 20 Nov); "
          "Voyager 1 one light-day out (18 Nov).  Not yet confirmed when drawn: BepiColombo's Mercury "
          "orbit insertion; the final COP31 text.")
    para(d, 30, 959, wrap(dc, F(SANS, 10), 964), F(SANS, 10), leading=13)

    text_c(d, W / 2, 996,
           "Every story here happened, or was first reported, on Saturday 21 November 2026.   Sources: Reuters \u00b7 AP \u00b7 AFP \u00b7 Al Jazeera \u00b7 USGS \u00b7 ESA \u00b7 NBC",
           F(SANS, 10), MUTED)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    im.save(out, optimize=True)
    data = open(out, "rb").read()
    print("bytes:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())
    assert len(data) <= 1048576


if __name__ == "__main__":
    main()
