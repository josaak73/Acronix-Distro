#!/usr/bin/env python3
"""Draws every image of the `acronixcosmos` Plymouth theme (original pixel art).

Everything is drawn once on a small logical canvas (320x180 "art pixels") with
a fixed palette, ordered (Bayer) dithering and hand-written 5x7 pixel fonts, and
then enlarged by a WHOLE number (nearest neighbour, never smoothed) for each
supported screen size: files are called s3_*, s4_*, s5_*, s6_*, s8_*. The boot
script picks the smallest scale that covers the screen.

The UNI logo is rebuilt on the same pixel grid from the shapes of the original
pieces (hard edges, dithered light-blue shading, violet rim).

Usage:  scripts/make_assets_cosmos.py            (images + script)
        SCRIPT_ONLY=1 scripts/make_assets_cosmos.py   (only the script, instant)
"""
import math
import os
import random
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "theme" / "acronixcosmos"
LOGO_SRC = ROOT / "theme" / "acronix"          # white logo pieces made by make_assets.sh
SCALES = [3, 4, 5, 6, 8]
W, H = 320, 180
LOGO_LW = 80                                   # logo width in art pixels
MOON_C = (254, 34)                             # moon centre in art pixels


def rgb(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bay(x, y):
    return (BAYER[y & 3][x & 3] + 0.5) / 16


def ramp(colors, t, x, y):
    """Colour at position t (0..1) of a ramp, dithered between neighbours."""
    t = min(max(t, 0.0), 0.9999)
    s = t * (len(colors) - 1)
    i = int(s)
    return colors[i + 1] if s - i > bay(x, y) else colors[i]


# ---------------------------------------------------------------------------
# periodic value noise (wraps horizontally every W pixels so clouds can loop)
# ---------------------------------------------------------------------------
def mk_fbm(seed, base=8, octs=4, vstretch=1.0):
    rnd = random.Random(seed)
    grids = []
    for o in range(octs):
        px = base * (2 ** o)
        py = 64
        grids.append((px, py, [[rnd.random() for _ in range(px)] for _ in range(py + 1)]))

    def f(x, y):
        tot = 0.0
        amp = 1.0
        norm = 0.0
        for px, py, g in grids:
            u = x / W * px
            v = y / (W / px) / vstretch
            x0 = int(math.floor(u)); y0 = int(math.floor(v))
            fx = u - x0; fy = v - y0
            fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
            a = g[y0 % (py + 1)][x0 % px]; b = g[y0 % (py + 1)][(x0 + 1) % px]
            c = g[(y0 + 1) % (py + 1)][x0 % px]; d = g[(y0 + 1) % (py + 1)][(x0 + 1) % px]
            tot += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
            norm += amp
            amp *= 0.5
        return tot / norm
    return f


# ---------------------------------------------------------------------------
# pixel fonts (5x7), hand written
# ---------------------------------------------------------------------------
FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 00000 00100",
    "c": "00000 00000 01110 10000 10000 10001 01110",
    "r": "00000 00000 10110 11001 10000 10000 10000",
    "o": "00000 00000 01110 10001 10001 10001 01110",
    "n": "00000 00000 10110 11001 10001 10001 10001",
    "i": "00100 00000 01100 00100 00100 00100 01110",
    "x": "00000 00000 10001 01010 00100 01010 10001",
}
GLYPH = {k: v.split() for k, v in FONT.items()}
ACUTE = {"Í": "I"}           # drawn as the base letter plus an accent above


def glyph_cells(ch):
    """Set of (col,row) lit cells of a glyph; rows -2..6 (accent above row 0)."""
    acc = False
    if ch in ACUTE:
        ch = ACUTE[ch]; acc = True
    rows = GLYPH[ch]
    cells = {(c, r) for r, row in enumerate(rows) for c, v in enumerate(row) if v == "1"}
    if acc:
        cells |= {(3, -2), (2, -1)}
    return cells


def text_cells(s):
    """Lay out a string; returns (cells, width). Proportional: ink width + 1 gap."""
    cells = set()
    x = 0
    for ch in s:
        if ch == " ":
            x += 3
            continue
        g = glyph_cells(ch)
        minc = min(c for c, _ in g); maxc = max(c for c, _ in g)
        for c, r in g:
            cells.add((x + c - minc, r))
        x += maxc - minc + 2
    return cells, x - 1


def draw_cells(cells, width, scale, fill, shadow=None, outline=None, margin=2):
    """Render lit cells (each `scale` art pixels square) to an RGBA image.
    `fill(row)` -> colour for an art-pixel row (0 = top of the 7-row letter)."""
    rows = [r for _, r in cells]
    top = min(min(rows), 0)
    wpx = width * scale + 2 * margin + 2
    hpx = (7 - top) * scale + 2 * margin + 2
    mask = [[False] * wpx for _ in range(hpx)]
    for c, r in cells:
        for dy in range(scale):
            for dx in range(scale):
                mask[(r - top) * scale + dy + margin][c * scale + dx + margin] = True
    img = Image.new("RGBA", (wpx, hpx), (0, 0, 0, 0))
    px = img.load()

    def get(x, y):
        return 0 <= x < wpx and 0 <= y < hpx and mask[y][x]
    if shadow:
        sc, off = shadow
        for y in range(hpx):
            for x in range(wpx):
                if get(x - off, y - off):
                    px[x, y] = sc + (255,)
    if outline:
        for y in range(hpx):
            for x in range(wpx):
                if not mask[y][x] and any(get(x + a, y + b) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                    px[x, y] = outline + (255,)
    for y in range(hpx):
        for x in range(wpx):
            if mask[y][x]:
                px[x, y] = fill(y - margin + top * scale, x) + (255,)
    return img


def small_text(s, color, shadow, scale=1):
    cells, w = text_cells(s)
    return draw_cells(cells, w, scale, lambda r, x: color, shadow=(shadow, scale), margin=1)


# ---------------------------------------------------------------------------
# background
# ---------------------------------------------------------------------------
SKY = [rgb(c) for c in ("#02010A", "#05031A", "#0A0630", "#130A4C", "#220F70", "#34178C")]


def make_bg():
    img = Image.new("RGB", (W, H))
    px = img.load()
    # sky: vertical gradient, dithered
    for y in range(H):
        for x in range(W):
            px[x, y] = ramp(SKY, (y / 150.0) ** 1.3, x, y)
    # nebulae (dithered tone steps, never smooth)
    nebs = [
        (60, 34, 78, 30, 11, ["#1B0B52", "#32146E", "#5A1F9A", "#8C3AC8"], 1.0),
        (255, 72, 82, 32, 12, ["#2A0B4A", "#5A1070", "#8A1F8C", "#C23AA8"], 0.9),
        (150, 98, 95, 20, 13, ["#0C1A55", "#14308A", "#1F4FB8", "#3F7FE0"], 0.7),
        (22, 98, 50, 28, 14, ["#1B0B52", "#32146E", "#5A1F9A", "#8C3AC8"], 0.8),
        (296, 16, 46, 22, 15, ["#2A0B4A", "#5A1070", "#8A1F8C", "#C23AA8"], 0.8),
    ]
    for cx, cy, rx, ry, seed, cols, gain in nebs:
        n = mk_fbm(seed, 6, 4)
        cols = [rgb(c) for c in cols]
        for y in range(max(0, cy - ry), min(125, cy + ry)):
            for x in range(max(0, cx - rx), min(W, cx + rx)):
                e = 1 - ((x - cx) / rx) ** 2 - ((y - cy) / ry) ** 2
                if e <= 0:
                    continue
                d = e ** 0.8 * (0.25 + 1.1 * n(x, y)) * gain + (bay(x, y) - 0.5) * 0.16
                for t, c in zip((0.14, 0.28, 0.44, 0.6), cols):
                    if d > t:
                        px[x, y] = c
    # stars
    rnd = random.Random(7)
    pal = [("#8F86C8", 55), ("#C6B8FF", 20), ("#FFFFFF", 10), ("#FF9BE8", 8), ("#7FE8F0", 7)]
    pool = [c for c, w in pal for _ in range(w)]
    for _ in range(340):
        x = rnd.randrange(0, W); y = int(rnd.random() ** 1.15 * 118)
        c = rgb(rnd.choice(pool))
        px[x, y] = c
        if rnd.random() < 0.12:
            x2, y2 = (x + 1, y) if rnd.random() < 0.5 else (x, y + 1)
            if x2 < W:
                px[x2, y2] = tuple(v * 2 // 3 for v in c)
    for _ in range(11):                           # small static plus-shaped stars
        x = rnd.randrange(8, W - 8); y = rnd.randrange(6, 100)
        if math.hypot(x - MOON_C[0], y - MOON_C[1]) < 34:
            continue
        for dx, dy, c in ((0, 0, "#F2E6FF"), (1, 0, "#A06AE0"), (-1, 0, "#A06AE0"),
                          (0, 1, "#A06AE0"), (0, -1, "#A06AE0")):
            px[x + dx, y + dy] = rgb(c)
    # horizon: haze + five wavy cloud bands, from far to near
    haze = [SKY[4], rgb("#3B1580"), rgb("#6A25A0"), rgb("#A02FB0"), rgb("#D84CC0")]
    for y in range(108, 145):
        for x in range(W):
            t = ((y - 108) / 37.0) ** 1.6
            if t > bay(x, y) * 0.9 or True:
                px[x, y] = ramp(haze, t, x, y)
    n_a = mk_fbm(21, 8, 4, 0.7)
    n_b = mk_fbm(22, 16, 3, 0.7)
    layers = [
        (138, 6, ["#FFE6F8", "#FFC4EE", "#FF8AD8", "#E84BC0", "#C21E9A"], (2, 5, 10, 16)),
        (148, 5, ["#D8FFF8", "#A8FFF4", "#3FE0E0", "#0BB5C9", "#0A7FA8"], (2, 5, 9, 14)),
        (156, 6, ["#D8C8FF", "#B8A6E8", "#8F6FD0", "#6A3FB8", "#4B1D9A"], (2, 5, 10, 16)),
        (165, 5, ["#A068F0", "#7A2FD0", "#5A22A8", "#3A1580", "#2A1065"], (2, 5, 9, 14)),
        (173, 4, ["#FFD8F4", "#FF8AD8", "#E84BC0", "#C21E9A", "#8A1A8C"], (1, 3, 6, 9)),
    ]
    for base, amp, cols, steps in layers:
        cols = [rgb(c) for c in cols]
        for x in range(W):
            edge = base + (n_a(x, base) - 0.5) * 2 * amp
            for y in range(int(edge) - 1, H):
                depth = y - edge + (n_b(x, y) - 0.5) * 5 + (bay(x, y) - 0.5) * 2.4
                if depth < -0.5:
                    continue
                k = 0
                for s in steps:
                    if depth >= s:
                        k += 1
                px[x, y] = cols[k]
    rnd = random.Random(9)
    for _ in range(46):                           # white glints on the clouds
        x = rnd.randrange(W); y = rnd.randrange(132, 176)
        px[x, y] = rgb("#FFFFFF")
    return img


def cloud_strip(seed, h, thr, cols, vstretch):
    """Transparent, horizontally looping strip (2 x 320 wide) of cloud puffs."""
    n = mk_fbm(seed, 8, 4, vstretch)
    cols = [rgb(c) for c in cols]
    img = Image.new("RGBA", (W * 2, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        env = math.sin(math.pi * (y + 0.5) / h) ** 0.7
        for x in range(W):
            d = n(x, y) * env + (bay(x, y) - 0.5) * 0.14
            if d > thr:
                t = min((d - thr) / 0.22, 0.999)
                c = cols[min(int((1 - t) * len(cols) * 0.999 + (y / h) * 0.9), len(cols) - 1)]
                px[x, y] = c + (255,)
                px[x + W, y] = c + (255,)
    return img


def nebula_shimmer(box, seed, frames, cols):
    """Moving brightest-tone highlights drawn over a nebula region."""
    x0, y0, w, h = box
    n = mk_fbm(seed, 6, 4)
    out = []
    cols = [rgb(c) for c in cols]
    for k in range(frames):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = img.load()
        for y in range(h):
            for x in range(w):
                gx, gy = x0 + x, y0 + y
                v = n((gx + k * 5) % W, gy + k * 1.5)
                d = v + (bay(gx, gy) - 0.5) * 0.18
                if (gx + gy) % 2:                      # sparse, checkered glints only
                    continue
                if d > 0.70:
                    px[x, y] = cols[1] + (255,)
                elif d > 0.65:
                    px[x, y] = cols[0] + (255,)
        out.append(img)
    return out


# ---------------------------------------------------------------------------
# moon, sparkles, stars
# ---------------------------------------------------------------------------
def make_moon(b, f):
    """Crescent moon with violet pixel outline; b = brightness 0..2, f = flicker phase."""
    S = 92
    cx = cy = S // 2
    R = 22
    cut = (cx + 9, cy - 7, 17)
    n = mk_fbm(31, 8, 3)
    inside = [[False] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            d0 = math.hypot(x - cx, y - cy)
            d1 = math.hypot(x - cut[0], y - cut[1])
            inside[y][x] = d0 <= R and d1 > cut[2]
    pts = [(x, y) for y in range(S) for x in range(S) if inside[y][x]]
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    # distance to the moon for the outline and halo (brute force, small area)
    dist = {}
    for y in range(S):
        for x in range(S):
            if inside[y][x]:
                continue
            best = 99.0
            for (qx, qy) in ((x + dx, y + dy) for dy in range(-14, 15) for dx in range(-14, 15)):
                if 0 <= qx < S and 0 <= qy < S and inside[qy][qx]:
                    d = math.hypot(qx - x, qy - y)
                    if d < best:
                        best = d
            dist[(x, y)] = best
    rim = [rgb(c) for c in ("#D9B8FF", "#B66BFF", "#8A3FE0", "#5B22B0")]
    halo_r = 6 + 3 * b
    halo = [rgb(c) for c in ("#8A3FE0", "#6A2AC8", "#4B1D9A")]
    for (x, y), d in dist.items():
        if d <= 1.2:
            px[x, y] = rim[0] + (255,)
        elif d <= 2.2:
            px[x, y] = rim[1] + (255,)
        elif d <= 3.2:
            px[x, y] = rim[2] + (255,)
        elif d <= 4.3:
            px[x, y] = rim[3] + (255,)
        elif d <= 4.3 + halo_r:
            t = (d - 4.3) / halo_r
            if (1 - t) ** 1.7 * (0.8 + 0.1 * b) > bay(x + f * 2, y + f):
                px[x, y] = halo[min(int(t * 3), 2)] + (255,)
    light = [rgb(c) for c in ("#FFFFFF", "#FFF8D0", "#FFF2B8", "#EFE3A0", "#DCCB88")]
    for (x, y) in pts:
        shade = 0.30 + 0.45 * ((x - cx) / R * -0.5 + (y - cy) / R * 0.5 + 1) / 2
        shade += (n(x * 1.0 % W, y) - 0.5) * 0.45 - 0.07 * b
        px[x, y] = ramp(light, min(max(shade, 0), 1), x, y) + (255,)
    return img


def make_star(r, halo):
    """Four pointed luminous star, concave diamond, with a dithered halo."""
    S = 2 * (r + halo) + 3
    c = S // 2
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    e = 0.55
    for y in range(S):
        for x in range(S):
            dx, dy = abs(x - c), abs(y - c)
            v = (dx ** e + dy ** e) / (r ** e)
            if v <= 1.0:
                if v <= 0.28:
                    col = "#FFFFFF"
                elif v <= 0.55:
                    col = "#FFF6C8"
                elif v <= 0.85:
                    col = "#FFB6EC"
                else:
                    col = "#C060F0"
                px[x, y] = rgb(col) + (255,)
            elif halo:
                d = math.hypot(dx, dy)
                t = d / (r + halo)
                if t < 1 and (1 - t) ** 2.2 * 0.85 > bay(x, y):
                    px[x, y] = rgb("#D060E8" if t < 0.5 else "#8A3FE0") + (255,)
    return img


def make_sparkle(f, pink):
    c1, c2, c3 = (("#FFFFFF", "#BFE9FF", "#7A8CD8") if not pink else ("#FFE6FA", "#FF8AD8", "#B04AC8"))
    img = Image.new("RGBA", (7, 7), (0, 0, 0, 0))
    px = img.load()
    if f == 0:
        px[3, 3] = rgb(c3) + (255,)
    elif f == 1:
        px[3, 3] = rgb(c1) + (255,)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px[3 + dx, 3 + dy] = rgb(c2) + (255,)
    else:
        px[3, 3] = rgb(c1) + (255,)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px[3 + dx, 3 + dy] = rgb(c1) + (255,)
        for k in (2, 3):
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                px[3 + dx, 3 + dy] = rgb(c2 if k == 2 else c3) + (255,)
    return img


def make_plate(w, h):
    """Dark plate with a double violet border for password prompts and messages."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if (x in (0, w - 1) and y in (0, h - 1)) or (x in (1, w - 2) and y in (0, h - 1)) \
                    or (x in (0, w - 1) and y in (1, h - 2)):
                continue                                    # notched corners
            edge = min(x, y, w - 1 - x, h - 1 - y)
            col = "#A855F0" if edge == 0 else ("#4B1D9A" if edge == 1 else "#0A0528")
            px[x, y] = rgb(col) + (255,)
    return img


# ---------------------------------------------------------------------------
# five point stars, shooting stars, galaxies, pixel logo
# ---------------------------------------------------------------------------
def star5_cells(R, cx, cy, inner=0.5):
    """Pixels whose centre lies inside a five pointed star of outer radius R."""
    pts = []
    for i in range(10):
        r = R if i % 2 == 0 else R * inner
        a = math.radians(-90 + i * 36)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    def inside(x, y):
        c = False
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]; xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                c = not c
            j = i
        return c
    n = int(cx * 2 + 2)
    return {(x, y) for y in range(n) for x in range(n) if inside(x + 0.5, y + 0.5)}


def make_star5(R, size, glint=False, bright=True):
    """Chunky cartoon star: pale fill, pink belly, violet outline, optional twinkle rays."""
    c = size / 2
    cells = star5_cells(R, c, c + R * 0.08)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    fill = [rgb(x) for x in (("#FFFFFF", "#FFF6C8", "#FFD2F0", "#FF9ADF") if bright
                             else ("#8A74D0", "#6A55B0", "#4B3A90", "#3A2A78"))]
    edge = rgb("#B45AF0" if bright else "#2A1A66")
    low = rgb("#7A2FD0" if bright else "#1E1250")
    ys = [y for _, y in cells]
    y0, y1 = min(ys), max(ys)
    for (x, y) in cells:
        px[x, y] = ramp(fill, (y - y0) / max(y1 - y0, 1), x, y) + (255,)
    for y in range(size):
        for x in range(size):
            if (x, y) in cells:
                continue
            if any((x + dx, y + dy) in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = (low if y > c + 1 else edge) + (255,)
    if glint:
        gc = int(c)
        for k in range(1, 4):
            col = rgb("#FFFFFF" if k == 1 else ("#FFD2F0" if k == 2 else "#B45AF0"))
            for dx, dy in ((k + R - 1, 0), (-(k + R - 1), 0), (0, -(k + R - 1))):
                x, y = gc + dx, gc + dy
                if 0 <= x < size and 0 <= y < size and px[x, y][3] == 0:
                    px[x, y] = col + (255,)
    return img


def make_shooting(frame, right=True):
    """Shooting star with a dithered fading trail. Heads right-down (mirrored for left)."""
    w, h = 44, 24
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    hx, hy = w - 6, h - 5
    for k in range(3, 36):
        x = hx - k
        for dy in (0, 1):
            y = hy - int(k * 0.45) - 1 + dy
            if 0 <= x < w and 0 <= y < h and (1 - k / 36.0) ** 1.1 * 1.05 > bay(x, y):
                col = "#FFFFFF" if k < 9 else ("#FFC4EE" if k < 17 else ("#C070F0" if k < 26 else "#6A3FC8"))
                px[x, y] = rgb(col) + (255,)
    star = make_star5(3.6, 9, glint=bool(frame))
    img.alpha_composite(star, (hx - 4, hy - 4))
    if not right:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def make_galaxy(w, h, tilt, frame):
    """Small pixel spiral galaxy: bright core, two dithered arms, pink/violet palette."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    cx, cy = w / 2, h / 2
    ct, st = math.cos(tilt), math.sin(tilt)
    cols = [rgb(c) for c in ("#4B1D9A", "#8A3FE0", "#C21E9A", "#FF6AD0", "#FFC4EE", "#FFFFFF")]
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ct + dy * st
            v = (-dx * st + dy * ct) * (w / h) * 0.78
            r = math.hypot(u, v) / (w / 2)
            if r >= 1:
                continue
            th = math.atan2(v, u)
            arm = (0.5 + 0.5 * math.cos(2 * (th - 5.5 * r) + frame * 0.9)) ** 2
            d = (1 - r) ** 1.0 * (0.10 + 0.95 * arm) + math.exp(-r * r * 30) * 0.9
            d += (bay(x, y) - 0.5) * 0.24
            k = -1
            for i, t in enumerate((0.16, 0.28, 0.42, 0.56, 0.74, 0.90)):
                if d > t:
                    k = i
            if k >= 0:
                px[x, y] = cols[k] + (255,)
    return img


LOGO_CELL = 5.5          # source pixels of the smooth logo per art pixel
GLOW_PAD = 8


def make_logo_pixels(consts):
    """Rebuild the three logo pieces on the art grid (hard edges, dithered shading)."""
    c = LOGO_CELL
    pad = 4
    W0 = consts["LOGO_W"] + 2 * pad
    H0 = consts["LOGO_H"] + 2 * pad
    aw, ah = math.ceil(W0 * 2 / (c * 2)), math.ceil(H0 * 2 / (c * 2))
    cov = {}
    keep = []
    for n in ("u", "n", "dot"):
        a = Image.open(LOGO_SRC / f"piece_{n}.png").convert("LA").split()[1]
        a = a.resize((a.width * 2, a.height * 2), Image.LANCZOS)
        canvas = Image.new("L", (int(aw * c * 2), int(ah * c * 2)), 0)
        canvas.paste(a, (2 * (consts[f"PIECE_{n.upper()}_X"] + pad), 2 * (consts[f"PIECE_{n.upper()}_Y"] + pad)))
        small = canvas.resize((aw, ah), Image.BOX)
        keep.append(small)                          # pixel access dies with its image
        cov[n] = small.load()
    owner = {}
    for y in range(ah):
        for x in range(aw):
            vals = {n: cov[n][x, y] for n in cov}
            if sum(vals.values()) >= 120:
                owner[(x, y)] = max(vals, key=vals.get)
    body = [rgb(v) for v in ("#FFFFFF", "#E4F6FF", "#B8E6FF", "#86CBF8", "#5FA8EE")]
    ys = [y for _, y in owner]
    y0, y1 = min(ys), max(ys)
    pix = {n: {} for n in cov}
    for (x, y), n in owner.items():
        t = (y - y0) / max(y1 - y0, 1)
        if (x, y - 1) not in owner or (x - 1, y) not in owner:
            t -= 0.38
        if (x + 1, y) not in owner or (x, y + 1) not in owner:
            t += 0.32
        pix[n][(x, y)] = ramp(body, t, x, y)
    rim = rgb("#A855F0")                      # outside edge, like the moon's rim
    gap = rgb("#2A1065")                      # thin channel between interlocking pieces
    for y in range(-1, ah + 1):
        for x in range(-1, aw + 1):
            if (x, y) in owner:
                continue
            nb = sum((x + dx, y + dy) in owner for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            edge = gap if nb >= 2 else rim
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = owner.get((x + dx, y + dy))
                    if n:
                        pix[n][(x, y)] = edge
                        break
                else:
                    continue
                break
    pieces = {}
    for n, d in pix.items():
        xs = [x for x, _ in d]; yy = [y for _, y in d]
        ax, ay = min(xs), min(yy)
        img = Image.new("RGBA", (max(xs) - ax + 1, max(yy) - ay + 1), (0, 0, 0, 0))
        pp = img.load()
        for (x, y), col in d.items():
            pp[x - ax, y - ay] = col + (255,)
        pieces[n] = (img, ax, ay)
    # dithered halo around the finished logo
    solid = set(owner)
    for d in pix.values():
        solid |= set(d)
    gw, gh = aw + 2 * GLOW_PAD, ah + 2 * GLOW_PAD
    glow = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    gp = glow.load()
    for y in range(gh):
        for x in range(gw):
            ax_, ay_ = x - GLOW_PAD, y - GLOW_PAD
            if (ax_, ay_) in solid:
                continue
            best = 99.0
            for dy in range(-GLOW_PAD, GLOW_PAD + 1):
                for dx in range(-GLOW_PAD, GLOW_PAD + 1):
                    if (ax_ + dx, ay_ + dy) in solid:
                        best = min(best, math.hypot(dx, dy))
            if best < GLOW_PAD and (1 - best / GLOW_PAD) ** 1.5 * 0.9 > bay(x, y):
                gp[x, y] = rgb("#8A3FE0" if best < 4 else "#5B22B0") + (255,)
    return {"pieces": pieces, "aw": aw, "ah": ah, "glow": glow}


# ---------------------------------------------------------------------------
# writing
# ---------------------------------------------------------------------------
def save(img, name, scale, nearest=True):
    if nearest and scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(OUT / name, optimize=True)


def parse_logo_consts():
    consts = {}
    for line in (LOGO_SRC / "acronix.script").read_text().splitlines():
        if line.split(" ")[0] in ("LOGO_W", "LOGO_H", "PIECE_U_X", "PIECE_U_Y", "PIECE_N_X",
                                  "PIECE_N_Y", "PIECE_DOT_X", "PIECE_DOT_Y"):
            k, v = line.split("=")
            consts[k.strip()] = int(v.strip().rstrip(";"))
    return consts


TITLE = "AcronixOS"
TITLE_SCALE = 3


def title_layout():
    """Per-letter ink offsets (art pixels) for the big title."""
    x = 0
    items = []
    for ch in TITLE:
        g = glyph_cells(ch)
        minc = min(c for c, _ in g); maxc = max(c for c, _ in g)
        items.append((ch, x, minc, maxc))
        x += (maxc - minc + 2) * TITLE_SCALE
    return items, x - TITLE_SCALE


def make_title_letter(ch):
    g = glyph_cells(ch)
    minc = min(c for c, _ in g)
    cells = {(c - minc, r) for c, r in g}
    w = max(c for c, _ in cells) + 1
    ramp_cols = [rgb(c) for c in ("#FFFFFF", "#FFF6C8", "#FFD2F0", "#FF8AD8", "#E84BC0", "#B02CC0")]
    return draw_cells(cells, w, TITLE_SCALE,
                      lambda y, x: ramp(ramp_cols, max(y, 0) / 21.0, x, y),
                      shadow=(rgb("#12073A"), 2), outline=rgb("#3A1580"), margin=4)


def write_layout(consts, logo):
    items, total = title_layout()
    lines = ["# generated by scripts/make_assets_cosmos.py. Edit theme/acronixcosmos.script.in instead."]
    lines.append(f"LOGO_AW = {logo['aw']};")
    lines.append(f"LOGO_AH = {logo['ah']};")
    lines.append(f"GLOW_PAD = {GLOW_PAD};")
    for n, (img, ax, ay) in logo["pieces"].items():
        lines.append(f"PIECE_{n.upper()}_AX = {ax};")
        lines.append(f"PIECE_{n.upper()}_AY = {ay};")
    lines.append(f"TITLE_N = {len(items)};")
    lines.append(f"TITLE_TOTAL = {total};")
    lines.append(f"TITLE_MARGIN = 4;")
    for i, (ch, x, minc, maxc) in enumerate(items):
        lines.append(f"TITLE_X[{i}] = {x};")
    lines.append(f"MOON_X = {MOON_C[0]};")
    lines.append(f"MOON_Y = {MOON_C[1]};")
    lines.append("SCALES[0] = 3; SCALES[1] = 4; SCALES[2] = 5; SCALES[3] = 6; SCALES[4] = 8;")
    lines.append("N_SCALES = 5;")
    (ROOT / "theme" / "acronixcosmos.layout").write_text("\n".join(lines) + "\n")
    return lines


def write_script():
    layout = (ROOT / "theme" / "acronixcosmos.layout").read_text()
    body = (ROOT / "theme" / "acronixcosmos.script.in").read_text()
    (OUT / "acronixcosmos.script").write_text(layout + "\n" + body)
    (OUT / "acronixcosmos.plymouth").write_text(
        "[Plymouth Theme]\n"
        "Name=Acronix Cosmos\n"
        "Description=Cosmic pixel-art boot: UNI logo assembles under a crescent moon, AcronixOS star title\n"
        "ModuleName=script\n\n"
        "[script]\n"
        "ImageDir=/usr/share/plymouth/themes/acronixcosmos\n"
        "ScriptFile=/usr/share/plymouth/themes/acronixcosmos/acronixcosmos.script\n"
        "ConsoleLogBackgroundColor=0x05031a\n"
        "MonospaceFont=Cantarell 11\n"
        "Font=Cantarell 12\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    consts = parse_logo_consts()
    logo = make_logo_pixels(consts)
    write_layout(consts, logo)
    if os.environ.get("SCRIPT_ONLY") != "1":
        build_images(consts, logo)
    write_script()
    print("acronixcosmos ready in", OUT)


def build_images(consts, logo):
    for old in OUT.glob("*.png"):
        old.unlink()
    # ---- art-pixel images (same pixels for every scale) ----
    art = {}
    art["bg"] = make_bg().convert("RGBA")
    art["cloud_mid"] = cloud_strip(41, 24, 0.50, ["#FFF0FB", "#FF8AD8", "#E84BC0", "#C21E9A"], 0.6)
    art["cloud_front"] = cloud_strip(42, 22, 0.47, ["#FFD8F4", "#FF8AD8", "#E84BC0", "#8A1A8C"], 0.5)
    for k, img in enumerate(nebula_shimmer((0, 0, 160, 75), 51, 3, ["#8C3AC8", "#C070F0"])):
        art[f"neb_a{k}"] = img
    for k, img in enumerate(nebula_shimmer((170, 30, 150, 80), 52, 3, ["#C23AA8", "#F070D0"])):
        art[f"neb_b{k}"] = img
    for b in range(3):
        for f in range(2):
            art[f"moon_{b}{f}"] = make_moon(b, f)
    for i, (r, halo) in enumerate(((4, 3), (8, 5), (12, 7), (16, 9), (20, 11), (22, 12), (24, 13))):
        art[f"star_{i}"] = make_star(r, halo)
    for pink in (0, 1):
        for f in range(3):
            art[f"spark{pink}_{f}"] = make_sparkle(f, pink)
    art["plate"] = make_plate(230, 46)
    art["slot_off"] = make_star5(3.4, 9, bright=False)
    art["slot_on"] = make_star5(3.4, 9)
    for f in range(2):
        art[f"head_{f}"] = make_star5(5.6, 17, glint=bool(f))
    for f, R in enumerate((3.4, 5.4, 7.4)):
        art[f"bstar_{f}"] = make_star5(R, 19, glint=(f == 2))
    for f in range(2):
        art[f"shoot_r{f}"] = make_shooting(f, True)
        art[f"shoot_l{f}"] = make_shooting(f, False)
    for g, (gw, gh, tilt) in enumerate(((45, 27, 0.45), (35, 21, -0.4), (27, 17, 0.1))):
        for f in range(3):
            art[f"gal{g}_{f}"] = make_galaxy(gw, gh, tilt, f)
    uni = small_text("UNIVERSIDAD NACIONAL DE INGENIERÍA", rgb("#DFF6FF"), rgb("#1B0B52"))
    art["txt_uni"] = uni
    art["txt_grp"] = small_text("4T4-COM-S", rgb("#FFE98A"), rgb("#8A1A8C"), 2)
    art["txt_tag"] = small_text("LÍDER EN CIENCIA Y TECNOLOGÍA", rgb("#A8FFF4"), rgb("#1B0B52"))
    full = "LOADING ACRONIXOS..."
    for k in range(4):
        cells, w = text_cells(full)
        cells_k, _ = text_cells("LOADING ACRONIXOS" + "." * k)
        art[f"txt_load{k}"] = draw_cells(cells_k, w, 1, lambda r, x: rgb("#FFFFFF"),
                                         shadow=(rgb("#1B0B52"), 1), margin=1)
    letters = {}
    for i, ch in enumerate(TITLE):
        letters[i] = make_title_letter(ch)

    for s_ in SCALES:
        for name, img in art.items():
            save(img, f"s{s_}_{name}.png", s_)
        for i, img in letters.items():
            save(img, f"s{s_}_title_{i}.png", s_)
        for n, (img, ax, ay) in logo["pieces"].items():
            save(img, f"s{s_}_piece_{n}.png", s_)
        save(logo["glow"], f"s{s_}_logo_glow.png", s_)
    print("images written:", len(list(OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
