#!/usr/bin/env python3
"""Render the news poster for Thursday 19 November 2026 — DENSE NEWSPAPER format.

Structure follows the winning 20261117 front page (structure only, original
content): masthead date, 3 lead panels, 2x5 small panels, schematic world
map with numbered pins, numbered index of the remaining stories, sources
footer. Story content is unchanged from v1 (see SOURCES.md).

v2 (sharpening pass): the whole page is drawn on a 3x supersampled canvas
(3072x3072) through a coordinate-scaling draw proxy, then downscaled to
1024x1024 with LANCZOS and given a mild unsharp mask — letter edges and
hairlines land far cleaner than a native-1024 render. Typography is a step
larger, ink contrast is deepened, the world map uses recognisable continent
polygons with region labels, and the Hormuz panel is redrawn so no label
sits under the tanker. No network. Deterministic: the paper grain uses a
fixed-seed RNG, so re-runs produce byte-identical PNGs.

v3 (flag fix): summit-panel flags drawn to spec (US stripes + canton star
grid, China big star + arc of four, Russia equal white-blue-red bands) and
the EU panel uses the same proper 5-point star for its circle of 12.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1024, 1024
SS = 3  # supersampling factor
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")
GRAIN_N = 110000

CREAM = (247, 242, 231)
CARD = (253, 251, 245)
INK = (10, 10, 10)
RED = (176, 32, 30)
NAVY = (16, 42, 74)
GOLD = (176, 130, 40)
GREY = (70, 66, 60)
BORDER = (198, 190, 168)
SEA = (203, 222, 233)
LAND = (232, 220, 183)

SERIF_X = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF_SB = "/usr/share/fonts/truetype/noto/NotoSerif-SemiBold.ttf"
SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
SANS_SB = "/usr/share/fonts/truetype/noto/NotoSans-SemiBold.ttf"

REGIONS = {
    "AMERICAS": (176, 32, 30),
    "EUROPE": (16, 42, 74),
    "MIDDLE EAST": (208, 116, 20),
    "ASIA": (110, 60, 160),
    "AFRICA": (0, 110, 84),
    "GLOBAL": (90, 90, 90),
    "US": (176, 32, 30),
    "WORLD": (0, 105, 120),
}


def F(path, size):
    return ImageFont.truetype(path, int(round(size * SS)))


def tw(fnt, s):
    return fnt.getbbox(s)[2] / SS


def lsize(fnt):
    return fnt.size / SS


def fit(path, s, size, max_w, minimum=8):
    while size > minimum and tw(F(path, size), s) > max_w:
        size -= 1
    return F(path, size)


def wrap(s, fnt, max_w):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(fnt, t) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


class SD:
    """Draw proxy that scales final-unit coordinates (and line widths)
    onto the supersampled canvas. Fonts are scaled inside F()."""

    def __init__(self, d, s):
        self._d = d
        self._s = s

    def _n(self, v):
        if isinstance(v, tuple):
            return tuple(self._n(x) for x in v)
        if isinstance(v, list):
            return [self._n(x) for x in v]
        if isinstance(v, (int, float)):
            return v * self._s
        return v

    def _kw(self, kw):
        kw = dict(kw)
        if "width" in kw:
            kw["width"] = max(1, int(round(kw["width"] * self._s)))
        if "radius" in kw:
            kw["radius"] = kw["radius"] * self._s
        return kw

    def rectangle(self, xy, **kw):
        self._d.rectangle(self._n(xy), **self._kw(kw))

    def ellipse(self, xy, **kw):
        self._d.ellipse(self._n(xy), **self._kw(kw))

    def polygon(self, xy, **kw):
        self._d.polygon(self._n(xy), **self._kw(kw))

    def line(self, xy, **kw):
        self._d.line(self._n(xy), **self._kw(kw))

    def arc(self, xy, **kw):
        self._d.arc(self._n(xy), **self._kw(kw))

    def rounded_rectangle(self, xy, **kw):
        self._d.rounded_rectangle(self._n(xy), **self._kw(kw))

    def point(self, xy, **kw):
        x, y = xy[0] * self._s, xy[1] * self._s
        self._d.rectangle([x, y, x + self._s - 1, y + self._s - 1], **kw)

    def text(self, xy, s, **kw):
        self._d.text(self._n(xy), s, **kw)


def badge(d, x, y, n, color, r=9):
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=color)
    f = F(SANS_B, 10 if n < 10 else 8)
    d.text((x + r, y + r), str(n), font=f, fill=(255, 255, 255), anchor="mm")


def star(d, cx, cy, r, fill, rot=-90):
    """A proper 5-pointed star polygon. rot = direction (degrees) of the
    first outer point; -90 points one tip straight up."""
    import math
    pts = []
    for i in range(10):
        ang = math.radians(rot + i * 36)
        rr = r if i % 2 == 0 else r * 0.382
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)


# ---------- flat illustration helpers (drawn inside a box) ----------

def illo_gta(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(38, 30, 64))
    d.rectangle([x, y + h * 0.45, x + w, y + h], fill=(24, 60, 84))
    for bx, bw, bh, col in [(6, 26, 52, (16, 18, 34)), (40, 20, 66, (12, 14, 30)), (68, 30, 44, (18, 20, 38)), (210, 24, 58, (14, 16, 32)), (244, 20, 70, (10, 12, 28)), (272, 26, 48, (16, 18, 34))]:
        d.rectangle([x + bx, y + h * 0.45 - bh + 10, x + bx + bw, y + h * 0.45 + 10], fill=col)
        for wy in range(3):
            for wx in range(2):
                d.rectangle([x + bx + 4 + wx * 10, y + h * 0.45 - bh + 16 + wy * 12, x + bx + 8 + wx * 10, y + h * 0.45 - bh + 22 + wy * 12], fill=(250, 205, 90))
    d.ellipse([x + w - 52, y + 8, x + w - 16, y + 44], fill=(250, 170, 60))
    for px in (120, 150, 182):
        d.line([x + px, y + h - 6, x + px, y + h * 0.52], fill=(20, 90, 60), width=4)
        for a in range(5):
            import math
            ang = -0.4 + a * 0.45
            d.line([x + px, y + h * 0.52, x + px + int(16 * math.sin(ang + 1.2)), y + h * 0.52 - int(12 * math.cos(ang))], fill=(24, 120, 70), width=3)
    d.rectangle([x + 96, y + h - 22, x + 208, y + h - 8], fill=(200, 40, 90))
    d.rectangle([x + 104, y + h - 30, x + 168, y + h - 22], fill=(140, 200, 230))


def illo_summit(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(120, 30, 36))
    # v3 (flag fix): the three flags drawn to spec at 3:2 — US 13 stripes
    # with a blue canton and a grid of small white stars, China one big
    # star + four small stars in an arc, Russia three equal bands
    # white-blue-red top to bottom.
    import math
    FW, FH = 60, 40
    for i, tag in enumerate(["US", "CN", "RU"]):
        fx = x + 30 + i * (w - 60) // 2 - 30
        fy = y + 8
        d.line([fx, fy, fx, y + h - 8], fill=(230, 230, 230), width=3)
        if tag == "US":
            sh = FH / 13
            for s in range(13):
                col = (178, 34, 52) if s % 2 == 0 else (255, 255, 255)
                d.rectangle([fx, fy + s * sh, fx + FW, fy + (s + 1) * sh + 0.6], fill=col)
            cw, chh = FW * 0.42, sh * 7
            d.rectangle([fx, fy, fx + cw, fy + chh], fill=(28, 38, 110))
            for r_ in range(5):
                for c_ in range(6):
                    star(d, fx + (c_ + 0.5) * cw / 6, fy + (r_ + 0.5) * chh / 5, 1.55, (255, 255, 255))
        elif tag == "CN":
            d.rectangle([fx, fy, fx + FW, fy + FH], fill=(222, 41, 38))
            star(d, fx + 11, fy + 12, 6.5, (250, 220, 60))
            for a in (-40, -15, 10, 35):
                ang = math.radians(a)
                sx, sy = fx + 11 + 14 * math.cos(ang), fy + 12 + 14 * math.sin(ang)
                star(d, sx, sy, 2.6, (250, 220, 60), rot=a + 180)
        else:
            bh = FH / 3
            d.rectangle([fx, fy, fx + FW, fy + bh + 0.6], fill=(255, 255, 255))
            d.rectangle([fx, fy + bh, fx + FW, fy + 2 * bh + 0.6], fill=(30, 60, 160))
            d.rectangle([fx, fy + 2 * bh, fx + FW, fy + FH], fill=(200, 40, 40))
        d.rectangle([fx, fy, fx + FW, fy + FH], outline=(60, 20, 22), width=1)
    d.rectangle([x + 20, y + h - 16, x + w - 20, y + h - 6], fill=(90, 20, 24))


def illo_gulf(d, x, y, w, h):
    """Strait of Hormuz, redrawn: Iran along the north shore, Arabia along
    the south, Kuwait at the NW head of the Gulf, Bahrain as a small island
    with a leader line, and the tanker inside the strait — every label sits
    on open land or open water, nothing under the ship."""
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    # Iran — northern shore
    d.polygon([(x, y), (x + w, y), (x + w, y + h * 0.34), (x + w * 0.72, y + h * 0.26),
               (x + w * 0.45, y + h * 0.33), (x + w * 0.18, y + h * 0.24), (x, y + h * 0.30)],
              fill=LAND, outline=(170, 158, 120))
    # Arabian peninsula — southern shore, Musandam tip reaching into the strait
    d.polygon([(x, y + h), (x, y + h * 0.80), (x + w * 0.20, y + h * 0.70),
               (x + w * 0.46, y + h * 0.73), (x + w * 0.64, y + h * 0.82),
               (x + w * 0.73, y + h * 0.66), (x + w * 0.79, y + h * 0.82), (x + w * 0.88, y + h)],
              fill=LAND, outline=(170, 158, 120))
    # Oman side, beyond the strait (bottom-right corner)
    d.polygon([(x + w * 0.90, y + h), (x + w * 0.94, y + h * 0.78), (x + w, y + h * 0.72), (x + w, y + h)],
              fill=LAND, outline=(170, 158, 120))
    f = F(SANS_B, 10)
    d.text((x + w * 0.44, y + h * 0.06), "IRAN", font=f, fill=INK)
    d.text((x + w * 0.02, y + h * 0.60), "KUWAIT", font=f, fill=INK)
    d.text((x + w * 0.27, y + h * 0.705), "ARABIA", font=f, fill=INK)
    # Bahrain: island dot + leader line + label on open water
    bx, by_ = x + w * 0.34, y + h * 0.52
    d.line([bx + 3, by_ - 3, x + w * 0.40, y + h * 0.42], fill=(90, 84, 70), width=1)
    d.ellipse([bx - 3, by_ - 3, bx + 3, by_ + 3], fill=LAND, outline=(170, 158, 120))
    d.text((x + w * 0.41, y + h * 0.36), "BAHRAIN", font=f, fill=INK)
    d.text((x + w * 0.76, y + h * 0.38), "HORMUZ", font=f, fill=INK)
    # attack marks: Kuwaiti coast and Bahrain — clear of every label
    for cx, cy in [(x + w * 0.20, y + h * 0.60), (bx, by_)]:
        d.line([cx - 5, cy - 5, cx + 5, cy + 5], fill=RED, width=3)
        d.line([cx - 5, cy + 5, cx + 5, cy - 5], fill=RED, width=3)
    # tanker in the strait, below the HORMUZ label
    hx, hy = x + w * 0.79, y + h * 0.64
    d.polygon([(hx, hy), (hx + 40, hy), (hx + 33, hy + 7), (hx + 5, hy + 7)], fill=(52, 52, 56))
    d.rectangle([hx + 7, hy - 5, hx + 27, hy], fill=(90, 90, 96))
    d.ellipse([hx + 28, hy - 13, hx + 37, hy - 4], fill=(230, 110, 30))


def illo_bars(d, x, y, w, h, tag):
    d.rectangle([x, y, x + w, y + h], fill=(14, 22, 38))
    base = y + h - 10
    for i, bh in enumerate([0.3, 0.42, 0.38, 0.55, 0.72, 0.95]):
        bx = x + 14 + i * (w - 90) / 5
        d.rectangle([bx, base - bh * (h - 26), bx + 16, base], fill=(46, 190, 120))
    d.line([x + 8, base, x + w - 70, base], fill=(200, 200, 200), width=1)
    f = fit(SANS_B, tag, 18, w - 20)
    d.text((x + w - tw(f, tag) - 8, y + 8), tag, font=f, fill=(250, 200, 70))


def illo_eu(d, x, y, w, h, tag):
    d.rectangle([x, y, x + w, y + h], fill=(24, 44, 110))
    import math
    # circle sits a touch high: the panel caption strip overlays the bottom
    # 13 units of the illustration, and all 12 stars must stay visible
    cx, cy, r = x + w * 0.3, y + h * 0.42, h * 0.28
    for i in range(12):
        a = 2 * math.pi * i / 12 - math.pi / 2
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        star(d, sx, sy, 4.6, (250, 205, 60))
    f = fit(SANS_B, tag, 21, w * 0.55)
    d.text((x + w * 0.52, y + h / 2 - 12), tag, font=f, fill=(255, 255, 255))


def illo_probe(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(8, 10, 26))
    rng = random.Random(7)
    for _ in range(46):
        sx, sy = x + rng.randrange(w), y + rng.randrange(h)
        d.point((sx, sy), fill=(230, 230, 240))
    cx, cy = x + w * 0.34, y + h * 0.52
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], outline=(220, 220, 230), width=2)
    d.line([cx, cy, cx + 26, cy - 20], fill=(220, 220, 230), width=2)
    d.rectangle([cx - 4, cy + 12, cx + 4, cy + 30], fill=(200, 170, 90))
    for i in range(3):
        d.arc([x + w * 0.52 + i * 14, y + h * 0.2, x + w * 0.52 + i * 14 + 34, y + h * 0.2 + 44], start=300, end=60, fill=(110, 200, 250), width=2)
    f = F(SANS_B, 11)
    d.text((x + 8, y + 6), "1 LIGHT-DAY", font=f, fill=(160, 210, 250))


def illo_tents(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(216, 196, 160))
    d.rectangle([x, y + h * 0.62, x + w, y + h], fill=(186, 158, 116))
    for i, (tx, tw_) in enumerate([(10, 52), (74, 44), (128, 56), (196, 46)]):
        ty = y + h * 0.3 + (i % 2) * 8
        d.polygon([(x + tx, ty + 30), (x + tx + tw_ / 2, ty), (x + tx + tw_, ty + 30)], fill=(240, 236, 226), outline=(120, 100, 70))
        d.polygon([(x + tx + tw_ / 2, ty + 30), (x + tx + tw_ / 2, ty + 5), (x + tx + tw_ - 6, ty + 30)], fill=(208, 202, 188), outline=(120, 100, 70))
    d.ellipse([x + w - 40, y + 6, x + w - 14, y + 32], fill=(244, 178, 84))


def illo_bridge(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(120, 160, 190))
    d.rectangle([x, y + h * 0.6, x + w, y + h], fill=(70, 110, 150))
    d.rectangle([x, y + h * 0.42, x + w, y + h * 0.48], fill=(90, 90, 96))
    for px in (0.22, 0.5, 0.78):
        d.rectangle([x + w * px - 3, y + h * 0.3, x + w * px + 3, y + h * 0.62], fill=(80, 80, 88))
    d.polygon([(x + w * 0.52, y + h * 0.42), (x + w * 0.62, y + h * 0.42), (x + w * 0.58, y + h * 0.58)], fill=(60, 60, 66))
    for i in range(3):
        d.ellipse([x + w * 0.54 + i * 5, y + h * 0.16 - i * 5, x + w * 0.54 + i * 5 + 12 + i * 3, y + h * 0.16 - i * 5 + 10 + i * 2], fill=(105, 105, 110))


def illo_ship(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(90, 150, 185))
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=(50, 100, 140))
    cols = [(200, 60, 50), (240, 150, 40), (60, 130, 200), (60, 170, 90), (150, 90, 180)]
    for i, c in enumerate(cols):
        d.rectangle([x + 16 + i * 30, y + h * 0.42, x + 42 + i * 30, y + h * 0.6], fill=c)
    d.rectangle([x + 10, y + h * 0.6, x + w - 10, y + h * 0.72], fill=(40, 44, 52))
    d.rectangle([x + w - 40, y + h * 0.26, x + w - 18, y + h * 0.42], fill=(235, 235, 230))


def illo_health(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 236, 226))
    d.ellipse([x + w * 0.36, y + h * 0.16, x + w * 0.64, y + h * 0.84], fill=(206, 84, 84))
    for dx, dy in [(-16, 8), (14, -12), (20, 14), (-8, -16), (0, 20), (-20, -4)]:
        cx, cy = x + w / 2 + dx, y + h / 2 + dy
        d.line([cx, cy, cx + dx // 2, cy + dy // 2], fill=(180, 60, 60), width=3)
        d.ellipse([cx + dx // 2 - 4, cy + dy // 2 - 4, cx + dx // 2 + 4, cy + dy // 2 + 4], fill=(180, 60, 60))
    f = F(SANS_B, 10)
    d.text((x + 8, y + h - 16), "MEASLES", font=f, fill=(150, 40, 40))


def illo_court(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(52, 58, 74))
    d.polygon([(x + 14, y + 16), (x + w - 14, y + 16), (x + w / 2, y + 2)], fill=(210, 200, 170))
    for i in range(4):
        cx = x + 24 + i * (w - 48) / 3
        d.rectangle([cx - 5, y + 22, cx + 5, y + h - 18], fill=(225, 220, 205))
    d.rectangle([x + 12, y + h - 16, x + w - 12, y + h - 8], fill=(210, 200, 170))


def illo_milk(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(238, 205, 130))
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=(198, 152, 84))
    d.ellipse([x + w - 44, y + 6, x + w - 12, y + 38], fill=(246, 168, 60))
    bx, by = x + w * 0.28, y + h * 0.2
    d.rectangle([bx, by, bx + 46, by + 22], fill=(250, 248, 244), outline=(90, 84, 78))
    d.ellipse([bx + 40, by + 1, bx + 58, by + 19], fill=(250, 248, 244), outline=(90, 84, 78))
    for sx, sy in [(7, 5), (26, 12), (14, 15)]:
        d.ellipse([bx + sx, by + sy, bx + sx + 9, by + sy + 6], fill=(60, 56, 52))
    for lx in (5, 36):
        d.line([bx + lx, by + 22, bx + lx, by + 33], fill=(60, 56, 52), width=3)
    d.rectangle([x + w * 0.68, y + h * 0.3, x + w * 0.68 + 16, y + h * 0.3 + 34], fill=(250, 250, 250))
    d.rectangle([x + w * 0.68 + 3, y + h * 0.3 - 6, x + w * 0.68 + 13, y + h * 0.3], fill=(60, 120, 200))


def illo_chart(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(250, 248, 242))
    pts = [(0.06, 0.62), (0.24, 0.55), (0.42, 0.66), (0.58, 0.44), (0.74, 0.36), (0.93, 0.2)]
    pp = [(x + px * w, y + py * h) for px, py in pts]
    d.line(pp, fill=RED, width=3)
    for px, py in pp:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED)
    f = F(SANS_B, 10)
    d.text((x + 8, y + 6), "RATES UP?", font=f, fill=INK)


# ---------- panel ----------

def panel(d, x, y, w, h, n, region, rlabel, illo, caption, headline, deck, lead=False):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=BORDER, width=1)
    ih = 96 if lead else 58
    illo(d, x + 1, y + 1, w - 2, ih)
    d.rectangle([x + 1, y + ih - 13, x + w - 1, y + ih + 1], fill=(24, 24, 24))
    fc = fit(SANS_B, caption, 10, w - 10, minimum=7)
    d.text((x + 5, y + ih - 11), caption, font=fc, fill=(245, 242, 232))
    ty = y + ih + 5
    badge(d, x + 5, ty, n, REGIONS[region], r=8)
    fl = fit(SANS_B, rlabel, 11, w - 30, minimum=8)
    d.text((x + 26, ty + 2), rlabel, font=fl, fill=REGIONS[region])
    ty += 20
    fh = fit(SERIF_B, headline, 22 if lead else 16, w - 10, minimum=11)
    for ln in wrap(headline, fh, w - 10)[:3 if lead else 2]:
        d.text((x + 5, ty), ln, font=fh, fill=INK)
        ty += lsize(fh) + 2
    fd = F(SANS, 13 if lead else 11)
    for ln in wrap(deck, fd, w - 10)[:3 if lead else 2]:
        d.text((x + 5, ty), ln, font=fd, fill=(34, 32, 30))
        ty += lsize(fd) + 2


LEADS = [
    (1, "GLOBAL", "GLOBAL · CULTURE — THE BIG RELEASE", illo_gta, "VICE CITY, LEONIDA — OUT NOW",
     "GTA VI arrives after a 13-year wait",
     "The rollout began in New Zealand at midnight; about 16m copies were already sold before launch day, and critics score it 99."),
    (2, "ASIA", "ASIA · DIPLOMACY — APEC, SHENZHEN", illo_summit, "SHENZHEN — THREE PRESIDENTS, ONE ROOM",
     "Trump, Xi and Putin meet in Shenzhen",
     "A first trilateral, on APEC's sidelines: arms control, Ukraine and Iran on the table. Putin sees \"big potential benefit\"."),
    (3, "MIDDLE EAST", "MIDDLE EAST · THE IRAN WAR", illo_gulf, "HORMUZ — TANKER CREW MISSING",
     "Iran widens its attacks to Kuwait and Bahrain",
     "Drones at a US-used Kuwaiti base; Bahrain's fourth attack in six days. A tanker crewman is missing, 11 hurt; Brent $92.70."),
]

SMALL = [
    (4, "US", "US · BUSINESS — AI", lambda d, x, y, w, h: illo_bars(d, x, y, w, h, "$81.3BN"), "NASDAQ — ANTHROPIC DEBUTS AS 'ANT'",
     "Anthropic's $81.3bn IPO is the biggest ever",
     "Priced at $83, above its range; it eclipses SpaceX's record debut."),
    (5, "EUROPE", "EUROPE · UKRAINE", lambda d, x, y, w, h: illo_eu(d, x, y, w, h, "€45BN"), "BRUSSELS — REPARATIONS ARE THE COLLATERAL",
     "EU proposes a €45bn loan for Ukraine",
     "Kyiv repays only after Russia pays reparations; its gap is put at €70bn."),
    (6, "GLOBAL", "GLOBAL · SPACE", illo_probe, "DEEP SPACE — THE SIGNAL TAKES A DAY",
     "Voyager 1 reaches one light-day from Earth",
     "Nearly five decades after launch, NASA's probe crosses a new distance mark."),
    (7, "MIDDLE EAST", "MIDDLE EAST · GAZA", illo_tents, "CENTRAL GAZA — FAMILIES ON THE MOVE",
     "Israeli troops launch a ground operation in central Gaza",
     "Displaced families flee tents in an area left under last year's ceasefire."),
    (8, "EUROPE", "EUROPE · UKRAINE WAR", illo_bridge, "KERCH STRAIT — A SPAN IN THE SEA",
     "Crimea's bridge is attacked again; traffic halted",
     "A Russian official reports a new strike on the key supply route."),
    (9, "ASIA", "ASIA · TRADE", illo_ship, "JAKARTA–BRUSSELS — A TARIFF COUNTERWEIGHT",
     "EU governments approve a trade deal with Indonesia",
     "The pact is meant to offset the drag of Trump's tariffs."),
    (10, "US", "US · HEALTH", illo_health, "PENNSYLVANIA — A HISTORIC RESURGENCE",
     "Unvaccinated resident dies amid US measles surge",
     "The death comes as measles runs at historic levels across the US."),
    (11, "WORLD", "WORLD · JUSTICE", illo_court, "THE HAGUE — GAMBIA v. MYANMAR",
     "World court prepares its Rohingya ruling",
     "The ICJ's genocide-case judgment on Myanmar is keenly awaited."),
    (12, "AFRICA", "AFRICA · CLIMATE & FOOD", illo_milk, "KENYA — DRY PASTURES, EMPTY CHURNS",
     "Kenya's milk shortage deepens as drought bites",
     "Dry pastures hit herders; supplies shrink and prices climb."),
    (13, "US", "US · ECONOMY", illo_chart, "WASHINGTON — MINUTES OF 27–28 OCT",
     "Fed minutes point to more rate hikes",
     "Most officials expect further rises to bring inflation back to 2%."),
]

INDEX = [
    (14, "US", "Senators warn AI cyber threats are outpacing defences"),
    (15, "ASIA", "Nvidia halts H-series chip shipments to mainland China"),
    (16, "US", "House panel seeks briefing on Microsoft–ByteDance AI talks"),
    (17, "AMERICAS", "Carney adjusts China ties, seeking the right US deal"),
    (18, "EUROPE", "Mélenchon could win the presidency, France's justice chief says"),
    (19, "EUROPE", "Deutsche Bank handled $582m in Epstein-linked deals — FT"),
    (20, "AFRICA", "Somalia accuses the UAE of secretly building bases on its soil"),
    (21, "AFRICA", "Somalia's charter overhaul tests its fragile federal bargain"),
    (22, "AFRICA", "Cocaine and millions of pills seized in eastern Libya"),
    (23, "MIDDLE EAST", "Saudi says danger has passed in three southern cities"),
    (24, "US", "Garcia orders 12 Trump allies to preserve records"),
    (25, "EUROPE", "EU pauses long-term UK talks pending a Brexit stance"),
    (26, "AMERICAS", "Panel: call China's Panama-flag detentions 'coercion'"),
    (27, "EUROPE", "Russia accuses France of deploying troops to Ukraine"),
    (28, "ASIA", "Amazon pledges $7bn for renewables in India by 2030"),
    (29, "GLOBAL", "'Missing billion years' blamed on mantle currents, ice sheets"),
    (30, "GLOBAL", "Bacterial toxin linked to early-onset bowel cancer surge"),
    (31, "MIDDLE EAST", "Peace Board warns Gaza reconstruction has stalled"),
    (32, "EUROPE", "Football: German FA backs Diallo for FIFA presidency"),
    (33, "EUROPE", "Kyiv touts interceptor drones reaching 500 km/h"),
    (34, "ASIA", "Xi and Putin attack protectionism in Shenzhen speeches"),
    (35, "GLOBAL", "Oil falls as risk aversion rises, despite the Gulf"),
    (36, "ASIA", "Electric micro-vehicles crowd China's city streets"),
    (37, "US", "Liu Yunping elected House Democratic Caucus chair"),
    (38, "MIDDLE EAST", "Third US carrier in region as Iran's army chief warns"),
]

# world-map pins for stories 1-13, in the 430x290 map space, placed on the
# continent they belong to (1 Florida, 2 China, 3 Iran, 4 US West, 5 Europe,
# 6 deep space off the NE corner, 7 Levant, 8 Crimea, 9 Indonesia,
# 10 Pennsylvania, 11 The Hague, 12 Kenya, 13 Washington)
PINS = {
    1: (112, 118), 2: (322, 74), 3: (264, 60), 4: (30, 58), 5: (210, 47),
    6: (386, 16), 7: (248, 88), 8: (240, 44), 9: (338, 142), 10: (100, 88),
    11: (192, 46), 12: (234, 126), 13: (106, 100),
}
DOTS = [(160, 34), (232, 50), (296, 66), (70, 108), (252, 98), (206, 128),
        (326, 102), (58, 88), (266, 98), (356, 146), (196, 40), (242, 88)]

# recognisable continent polygons in the same 430x290 space
LANDS = [
    # North America (with the Hudson Bay notch and a Florida peninsula)
    [(12, 48), (30, 34), (58, 30), (84, 34), (104, 28), (122, 40), (138, 34),
     (150, 46), (136, 54), (142, 64), (128, 58), (124, 72), (134, 80),
     (128, 92), (112, 88), (104, 98), (110, 110), (96, 116), (84, 108),
     (76, 118), (88, 128), (102, 132), (112, 126), (118, 140), (104, 150),
     (88, 142), (72, 128), (56, 118), (44, 102), (30, 84), (20, 66)],
    # Greenland
    [(150, 18), (176, 14), (184, 30), (164, 42), (148, 32)],
    # South America
    [(92, 140), (108, 132), (124, 138), (136, 152), (142, 176), (136, 208),
     (124, 238), (110, 252), (100, 232), (92, 200), (84, 168), (84, 150)],
    # Europe
    [(178, 52), (186, 38), (200, 30), (216, 34), (228, 26), (240, 38),
     (232, 48), (240, 56), (226, 60), (218, 52), (206, 62), (196, 58),
     (188, 66), (180, 62)],
    # Ukraine / Black Sea bridge
    [(226, 34), (254, 34), (258, 50), (240, 58), (226, 48)],
    # Africa
    [(186, 84), (206, 78), (232, 82), (248, 96), (252, 118), (242, 150),
     (228, 176), (210, 186), (196, 160), (188, 128), (184, 104)],
    # Levant / Arabia
    [(230, 74), (256, 70), (268, 86), (260, 106), (242, 104), (230, 90)],
    # Iran
    [(250, 50), (282, 46), (294, 60), (274, 74), (252, 68)],
    # Asia (with the SE-Asian peninsula)
    [(240, 38), (268, 28), (300, 24), (336, 30), (368, 24), (398, 36),
     (410, 56), (392, 72), (372, 66), (360, 84), (344, 78), (336, 96),
     (322, 108), (306, 100), (296, 114), (284, 102), (268, 108), (256, 90),
     (246, 72), (238, 56)],
    # India
    [(258, 86), (276, 84), (272, 106), (260, 100)],
    # Indonesia (three island arcs)
    [(300, 132), (322, 128), (326, 140), (304, 144)],
    [(332, 138), (356, 134), (362, 146), (338, 150)],
    [(366, 142), (388, 140), (390, 150), (368, 152)],
    # Japan
    [(366, 52), (380, 42), (386, 48), (374, 60), (364, 58)],
    # Australia
    [(344, 168), (372, 158), (398, 164), (406, 182), (388, 196), (360, 194),
     (342, 184)],
    # New Zealand
    [(408, 204), (418, 198), (414, 212), (406, 212)],
]

MAP_LABELS = [
    ("N. AMERICA", 52, 52, 7), ("S. AMERICA", 93, 190, 7), ("EUROPE", 186, 58, 7),
    ("AFRICA", 200, 140, 7), ("ASIA", 314, 50, 8), ("AUSTRALIA", 352, 178, 7),
]


def draw_map(d, x, y, w, h):
    d.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=SEA, outline=BORDER)
    sx, sy = w / 430, h / 290
    for poly in LANDS:
        d.polygon([(x + px * sx, y + py * sy) for px, py in poly], fill=LAND, outline=(176, 164, 128))
    flab = F(SANS_B, 7)
    for label, lx, ly, _sz in MAP_LABELS:
        fnt = F(SANS_B, _sz)
        d.text((x + lx * sx, y + ly * sy), label, font=fnt, fill=(96, 88, 66))
    for dx, dy in DOTS:
        d.ellipse([x + dx * sx - 2, y + dy * sy - 2, x + dx * sx + 2, y + dy * sy + 2], fill=GREY)
    for n, (px, py) in PINS.items():
        cx, cy = x + px * sx, y + py * sy
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=RED, outline=(255, 255, 255), width=1)
        f = F(SANS_B, 9 if n < 10 else 8)
        s = str(n)
        d.text((cx - tw(f, s) / 2, cy - 5), s, font=f, fill=(255, 255, 255))
    f = F(SANS, 9)
    d.text((x + 8, y + h - 14), "Pins: stories 1–13 · dots: 14–38", font=f, fill=(48, 48, 48))


def main():
    img = Image.new("RGB", (W * SS, H * SS), CREAM)
    d = SD(ImageDraw.Draw(img), SS)

    MX = 26
    # kicker
    fk = fit(SANS_B, "THE DAILY COMPASS · THE WORLD'S NEWS IN ONE PICTURE", 13, 560)
    d.text((MX, 10), "THE DAILY COMPASS · THE WORLD'S NEWS IN ONE PICTURE", font=fk, fill=RED)
    right = "38 STORIES · 6 CONTINENTS · ALL FROM THURSDAY"
    fr = fit(SANS_B, right, 13, 380)
    d.text((W - MX - tw(fr, right), 10), right, font=fr, fill=INK)
    d.line([MX, 30, W - MX, 30], fill=INK, width=2)
    # masthead date
    date = "Thursday 19 November 2026"
    fdate = fit(SERIF_X, date, 88, W - 2 * MX)
    d.text(((W - tw(fdate, date)) / 2, 36), date, font=fdate, fill=INK)
    d.line([MX, 122, W - MX, 122], fill=INK, width=3)
    d.line([MX, 127, W - MX, 127], fill=INK, width=1)

    # lead row: 3 panels
    lw = (W - 2 * MX - 16) // 3
    for i, st in enumerate(LEADS):
        panel(d, MX + i * (lw + 8), 136, lw, 196, *st, lead=True)
    # small rows: 5 per row
    sw = (W - 2 * MX - 32) // 5
    for r in range(2):
        for c in range(5):
            st = SMALL[r * 5 + c]
            panel(d, MX + c * (sw + 8), 340 + r * 156, sw, 148, *st)

    # bottom section
    by = 656
    fh1 = F(SANS_B, 13)
    d.text((MX, by), "WHERE IT HAPPENED", font=fh1, fill=RED)
    also = "ALSO ON THURSDAY 19 NOVEMBER"
    d.text((MX + 424, by), also, font=fh1, fill=RED)
    d.line([MX, by + 16, W - MX, by + 16], fill=BORDER, width=1)
    draw_map(d, MX, by + 22, 400, 268)
    # legend
    fl = F(SANS, 9)
    lx = MX
    for label, col in [("Americas", REGIONS["AMERICAS"]), ("Europe", REGIONS["EUROPE"]), ("Middle East", REGIONS["MIDDLE EAST"]), ("Asia", REGIONS["ASIA"]), ("Africa", REGIONS["AFRICA"]), ("Global", REGIONS["GLOBAL"])]:
        d.ellipse([lx, by + 296, lx + 7, by + 303], fill=col)
        d.text((lx + 10, by + 294), label, font=fl, fill=INK)
        lx += 10 + tw(fl, label) + 12
    # index: two columns
    ix = MX + 424
    colw = (W - MX - ix - 12) // 2
    per = 13
    rh = 22
    for i, (n, region, text) in enumerate(INDEX):
        col = 0 if i < per else 1
        row = i if i < per else i - per
        cx = ix + col * (colw + 12)
        cy = by + 24 + row * rh
        badge(d, cx, cy, n, REGIONS[region], r=7)
        fi = fit(SANS_SB, text, 12, colw - 20, minimum=8)
        d.text((cx + 18, cy + 1), text, font=fi, fill=INK)

    # footer
    d.line([MX, 986, W - MX, 986], fill=INK, width=1)
    ff = F(SANS, 10)
    d.text((MX, 992), "Every story here was reported on Thursday 19 November 2026. Contested claims are marked as claims.", font=ff, fill=GREY)
    src = "Sources: Reuters, AP, AFP, BBC, Al Jazeera, NPR, FT, Sky News, People. Original drawings."
    d.text((W - MX - tw(ff, src), 992), src, font=ff, fill=GREY)

    # downscale, sharpen, grain — the delivered 1024x1024 image
    img = img.resize((W, H), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=35, threshold=3))
    rng = random.Random(1907)
    for _ in range(GRAIN_N):
        px, py = rng.randrange(W), rng.randrange(H)
        v = rng.randrange(-5, 6)
        base = img.getpixel((px, py))
        img.putpixel((px, py), tuple(max(0, min(255, c + v)) for c in base))

    img.save(OUT, optimize=True)
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
