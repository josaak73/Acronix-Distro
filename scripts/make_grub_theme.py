#!/usr/bin/env python3
"""Builds the `acronixos-cosmic` GRUB theme (original pixel art, Pillow only).

Re-uses the sky / nebula / moon / cloud / galaxy / star routines of the Plymouth
generator (scripts/make_assets_cosmos.py) so both boot stages look the same.

Layout is designed once on the 320x180 "art pixel" grid and enlarged by a WHOLE
number (nearest neighbour). Each supported resolution gets its own self-contained
folder (GRUB smooths any image it has to scale, so nothing is scaled at boot):

    1920x1080  x6      1600x900  x5      1366x768  x5 (centre crop)      1280x720  x4

Fine pixels ("U") are used for icons, selector and fonts: 3 px, or 2 px at 720p.

Usage: scripts/make_grub_theme.py          (needs grub-mkfont + Terminus bitmap fonts)
"""
import math
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_assets_cosmos as mac            # noqa: E402
from make_assets_cosmos import rgb, ramp, bay   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "grub" / "acronixos-cosmic"
FONT_DIR = Path("/usr/share/fonts/misc")
VERSION = "1.0"

# resolution -> art scale S, fine unit U, crop (px removed left/top), fonts (item, small)
RES = {
    "1920x1080": dict(S=6, U=3, crop=(0, 0), item=24, small=18),
    "1600x900":  dict(S=5, U=3, crop=(0, 0), item=22, small=16),
    "1366x768":  dict(S=5, U=3, crop=(110, 52), item=20, small=16),
    "1280x720":  dict(S=4, U=2, crop=(0, 0), item=18, small=14),
}

# ---- layout in art pixels (inside x 30..290, y 18..162 so the 1366x768 crop keeps it) ----
PANEL = (30, 44, 160, 90)          # menu panel x, y, w, h
FOOT = (30, 150, 260, 14)          # footer panel
RING_C = (250, 72)                 # countdown ring / moon centre
RING_SIZE = 78
HANDOFF_DIM = 50                   # % brightness of handoff.png
TICKS = 16

# ---- OS icons ---------------------------------------------------------------
OUTLINE = rgb("#12073A")


def _mask():
    m = Image.new("L", (16, 16), 0)
    return m, ImageDraw.Draw(m)


def _paint(img, mask, cols, flat=False):
    px = img.load()
    mp = mask.load()
    ys = [y for y in range(16) for x in range(16) if mp[x, y]]
    if not ys:
        return
    y0, y1 = min(ys), max(ys)
    cols = [rgb(c) for c in cols]
    for y in range(16):
        for x in range(16):
            if mp[x, y]:
                px[x, y] = (cols[0] if flat else ramp(cols, (y - y0) / max(y1 - y0 + 1, 1), x, y)) + (255,)


def _outline(img):
    px = img.load()
    out = img.copy()
    op = out.load()
    for y in range(16):
        for x in range(16):
            if px[x, y][3] == 0 and any(
                    0 <= x + a < 16 and 0 <= y + b < 16 and px[x + a, y + b][3]
                    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                op[x, y] = OUTLINE + (255,)
    return out


def _dot(img, pts, col):
    for x, y in pts:
        img.putpixel((x, y), rgb(col) + (255,))


def ico_arch():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m, d = _mask()
    d.polygon([(8, 1), (13, 13), (10, 13), (8, 8), (6, 13), (3, 13)], fill=255)
    _paint(img, m, ["#E8FFFF", "#7FE8F0", "#2FC4DC", "#0A7FA8"])
    m, d = _mask()
    d.rectangle([7, 8, 8, 9], fill=255)
    _paint(img, m, ["#FFFFFF"], flat=True)
    return _outline(img)


def ico_debian():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m, d = _mask()
    d.arc([2, 2, 13, 13], 40, 350, fill=255, width=2)
    d.arc([5, 5, 10, 10], 100, 360, fill=255, width=2)
    d.rectangle([7, 7, 8, 8], fill=255)
    d.rectangle([12, 4, 13, 5], fill=255)
    _paint(img, m, ["#FFD0E4", "#FF5C96", "#E0245E", "#A0124A"])
    return _outline(img)


def ico_ubuntu():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m, d = _mask()
    d.ellipse([2, 2, 13, 13], outline=255, width=2)
    _paint(img, m, ["#FFC080", "#FF8A3D", "#E8502A", "#B02A3A"])
    m, d = _mask()
    for a in (-90, 30, 150):
        cx, cy = 7.5 + 5.5 * math.cos(math.radians(a)), 7.5 + 5.5 * math.sin(math.radians(a))
        d.ellipse([cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6], fill=255)
    _paint(img, m, ["#FFFFFF", "#FFE6F8", "#FFB0E8"])
    return _outline(img)


def ico_fedora():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m, d = _mask()
    d.ellipse([1, 1, 14, 14], fill=255)
    _paint(img, m, ["#7FB8FF", "#3F82E8", "#2556C0", "#16348A"])
    m, d = _mask()                                   # infinity loop
    d.ellipse([3, 5, 8, 10], outline=255, width=1)
    d.ellipse([7, 5, 12, 10], outline=255, width=1)
    _paint(img, m, ["#FFFFFF", "#DFF0FF"])
    return _outline(img)


def ico_mint():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m, d = _mask()
    d.polygon([(2, 14), (2, 8), (5, 4), (10, 2), (14, 2), (14, 7), (11, 11), (6, 14)], fill=255)
    _paint(img, m, ["#C8FFB0", "#7FE060", "#3FB84A", "#1F7A3A"])
    m, d = _mask()
    d.line([(3, 13), (12, 4)], fill=255, width=1)
    d.line([(7, 9), (7, 6)], fill=255)
    d.line([(9, 7), (12, 7)], fill=255)
    _paint(img, m, ["#F2FFE6"], flat=True)
    return _outline(img)


def ico_manjaro():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x0, y0, x1, y1) in ((1, 2, 4, 13), (6, 2, 9, 8), (11, 2, 14, 13)):
        m, d = _mask()
        d.rectangle([x0, y0, x1, y1], fill=255)
        _paint(img, m, ["#C4FFD6", "#5AE08A", "#2AB860", "#157A40"])
    return _outline(img)


def ico_windows():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x0, y0, x1, y1) in ((2, 3, 7, 7), (2, 9, 7, 13), (9, 2, 14, 6), (9, 8, 14, 12)):
        m, d = _mask()
        d.rectangle([x0, y0, x1, y1], fill=255)
        _paint(img, m, ["#CFF4FF", "#6FD0FF", "#2F8CF0", "#1F52C0"])
    return _outline(img)


def ico_linux():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m, d = _mask()
    d.ellipse([3, 1, 12, 14], fill=255)
    d.rectangle([4, 11, 11, 14], fill=255)
    _paint(img, m, ["#8A74D0", "#5A3FB0", "#3A2584", "#2A1A66"])
    m, d = _mask()
    d.ellipse([5, 6, 10, 13], fill=255)
    _paint(img, m, ["#FFFFFF", "#FFF2C8", "#FFD2F0"])
    m, d = _mask()
    d.rectangle([7, 4, 8, 5], fill=255)
    d.rectangle([2, 14, 5, 14], fill=255)
    d.rectangle([10, 14, 13, 14], fill=255)
    _paint(img, m, ["#FFD040", "#FF9A20"])
    _dot(img, [(5, 3), (10, 3)], "#FFFFFF")
    _dot(img, [(6, 3), (9, 3)], "#12073A")
    return _outline(img)


def ico_unknown():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m, d = _mask()
    d.rectangle([3, 3, 12, 12], fill=255)
    for k in (4, 6, 8, 10):
        d.point([(1, k), (2, k), (13, k), (14, k), (k, 1), (k, 2), (k, 13), (k, 14)], fill=255)
    _paint(img, m, ["#C6B8FF", "#8A5CE0", "#5A2FB8", "#3A1A80"])
    m, d = _mask()
    d.rectangle([5, 5, 10, 10], fill=255)
    _paint(img, m, ["#0A0528"], flat=True)
    star = mac.make_star5(2.9, 7)
    img.alpha_composite(star, (4, 4))
    return _outline(img)


ICONS = {"arch": ico_arch, "debian": ico_debian, "ubuntu": ico_ubuntu, "fedora": ico_fedora,
         "mint": ico_mint, "manjaro": ico_manjaro, "windows": ico_windows,
         "linux": ico_linux, "unknown": ico_unknown}

# GRUB tries `icons/<class>.png` for every --class of the entry, in order, and uses the
# first one that exists. These are the class names that grub-mkconfig / os-prober produce.
ALIASES = {
    "arch": "archlinux endeavouros artix garuda cachyos arcolinux archcraft blackarch steamos",
    "debian": "kali raspbian mx devuan pureos deepin parrot siduction proxmox tails",
    "ubuntu": "kubuntu xubuntu lubuntu pop pop_os zorin elementary neon tuxedo",
    "fedora": "rhel redhat red centos rocky almalinux oracle nobara bazzite silverblue kinoite",
    "mint": "linuxmint linux_mint lmde",
    "windows": "microsoft",
    "linux": "gnu-linux gnu tux",
    "unknown": "os efi osx darwin hurd uefi firmware memtest bsd freebsd",
}


# ---- background -------------------------------------------------------------
def make_art_bg(panels=True):
    img = mac.make_bg().convert("RGBA")
    cx, cy = RING_C
    moon = mac.make_moon(1, 0)
    img.alpha_composite(moon, (cx - moon.width // 2, cy - moon.height // 2))
    for (g, (gw, gh, tilt)), pos in zip(enumerate(((45, 27, 0.45), (35, 21, -0.4), (27, 17, 0.1))),
                                        ((196, 12), (258, 14), (266, 108))):
        img.alpha_composite(mac.make_galaxy(gw, gh, tilt, 1), pos)
    for (R, size, glint), pos in (((3.4, 9, False), (196, 58)), ((5.4, 13, True), (292, 62)),
                                  ((7.4, 17, True), (200, 84)), ((3.4, 9, True), (290, 96)),
                                  ((3.4, 9, False), (236, 128))):
        img.alpha_composite(mac.make_star5(R, size, glint=glint), pos)
    img.alpha_composite(mac.make_shooting(1, True), (146, 8))
    # header: star emblem, pixel title, subtitle
    img.alpha_composite(mac.make_star5(6.2, 17, glint=True), (28, 17))
    cells, w = mac.text_cells("ACRONIXOS")
    cols = [rgb(c) for c in ("#FFFFFF", "#FFF6C8", "#FFD2F0", "#FF8AD8", "#E84BC0", "#B02CC0")]
    title = mac.draw_cells(cells, w, 2, lambda y, x: ramp(cols, max(y, 0) / 14.0, x, y),
                           shadow=(rgb("#12073A"), 1), outline=rgb("#3A1580"), margin=2)
    img.alpha_composite(title, (50, 15))
    sub = mac.small_text("COSMIC BOOT MENU  V" + VERSION, rgb("#A8FFF4"), rgb("#1B0B52"))
    img.alpha_composite(sub, (52, 33))
    if panels:
        for (x, y, w_, h_) in (PANEL, FOOT):
            img.alpha_composite(mac.make_plate(w_, h_), (x, y))
    return img


# ---- selector, scrollbar, countdown tick -------------------------------------
SEL_BG = "#2A1065"


def solid(w, h, col):
    return Image.new("RGBA", (w, h), rgb(col) + (255,))


def make_select_parts():
    """Nine-patch for the selected entry, in fine pixels. Glowing five point star on the left."""
    ih, wl = 22, 24
    w = solid(wl, ih, SEL_BG)
    px = w.load()
    sc = (11, 11)
    for y in range(ih):
        for x in range(wl):
            d = math.hypot(x - sc[0], y - sc[1])
            t = d / 12.0
            if t < 1 and (1 - t) ** 1.6 * 0.95 > bay(x, y):
                px[x, y] = rgb("#8A3FE0" if t > 0.55 else "#C23AA8") + (255,)
    w.alpha_composite(mac.make_star5(7.6, 19, glint=True), (2, 1))
    parts = {"w": w, "c": solid(4, ih, SEL_BG)}
    top = ["#FF8AD8"]
    bot = ["#8A3FE0"]
    parts["n"] = solid(4, 1, top[0])
    parts["s"] = solid(4, 1, bot[0])
    parts["e"] = solid(2, ih, "#8A3FE0")
    parts["nw"] = solid(wl, 1, top[0])
    parts["ne"] = solid(2, 1, top[0])
    parts["sw"] = solid(wl, 1, bot[0])
    parts["se"] = solid(2, 1, bot[0])
    return parts, ih


def scale(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


# ---- font -------------------------------------------------------------------
def make_font(size, bold, out_dir):
    src = FONT_DIR / f"ter-u{size}{'b' if bold else 'n'}.otb"
    dst = out_dir / f"terminus_{'bold' if bold else 'regular'}_{size}.pf2"
    subprocess.run(["grub-mkfont", "-s", str(size), "-o", str(dst), str(src)], check=True,
                   capture_output=True)
    return dst


def font_name(pf2):
    data = pf2.read_bytes()
    i = data.index(b"NAME")
    ln = int.from_bytes(data[i + 4:i + 8], "big")
    return data[i + 8:i + 8 + ln].rstrip(b"\0").decode()


# ---- one resolution ---------------------------------------------------------
def build(res, cfg, art, handoff):
    S, U = cfg["S"], cfg["U"]
    cx0, cy0 = cfg["crop"]
    w, h = map(int, res.split("x"))
    d = OUT / res
    if d.exists():
        shutil.rmtree(d)
    (d / "icons").mkdir(parents=True)

    big = scale(art, S).convert("RGB")
    big.crop((cx0, cy0, cx0 + w, cy0 + h)).save(d / "background.png", optimize=True)
    # shown by GRUB's text terminal after the menu closes (console, editor, boot): same scene without
    # the empty panels, dimmed so GRUB text stays readable
    hb = scale(handoff, S).convert("RGB").crop((cx0, cy0, cx0 + w, cy0 + h))
    hb = Image.eval(hb, lambda v: v * HANDOFF_DIM // 100)
    hb.save(d / "handoff.png", optimize=True)

    for name, fn in ICONS.items():
        img = scale(fn(), U)
        img.save(d / "icons" / f"{name}.png", optimize=True)
        for al in ALIASES.get(name, "").split():
            img.save(d / "icons" / f"{al}.png", optimize=True)

    parts, ih = make_select_parts()
    for k, im in parts.items():
        scale(im, U).save(d / f"select_{k}.png")
    solid(U * 3, U, "#C070F0").save(d / "sb_thumb_c.png")
    solid(U * 3, U, "#1B0B52").save(d / "sb_frame_c.png")
    tick = scale(mac.make_star5(2.9, 7), S)
    tick.save(d / "tick.png")
    Image.new("RGBA", (S, S), (0, 0, 0, 0)).save(d / "center.png")

    f_item = make_font(cfg["item"], True, d)
    f_small = make_font(cfg["small"], True, d)
    n_item, n_small = font_name(f_item), font_name(f_small)

    def px(x, y):                      # art -> screen px
        return x * S - cx0, y * S - cy0

    px_, py_, pw, ph = PANEL
    mx, my = px(px_ + 3, py_ + 3)
    mw, mh = (pw - 6) * S, (ph - 6) * S
    item_h, icon = ih * U, 16 * U
    rc = px(RING_C[0] - RING_SIZE // 2, RING_C[1] - RING_SIZE // 2)
    fx, fy, fw, fh = FOOT
    lx, _ = px(fx + 4, fy)
    ly = fy * S - cy0 + (fh * S - cfg["small"]) // 2
    theme = f"""# AcronixOS Cosmic - GRUB theme, {res}. GENERATED by scripts/make_grub_theme.py: do not edit.
title-text: ""
desktop-image: "background.png"
desktop-color: "#05031a"
message-font: "{n_small}"
message-color: "#FFFFFF"
message-bg-color: "#0A0528"
terminal-font: "{n_small}"
terminal-left: "0"
terminal-top: "0"
terminal-width: "100%"
terminal-height: "100%"
terminal-border: "0"

+ boot_menu {{
  left = {mx}
  top = {my}
  width = {mw}
  height = {mh}
  item_font = "{n_item}"
  selected_item_font = "{n_item}"
  item_color = "#B8A6E8"
  selected_item_color = "#FFFFFF"
  icon_width = {icon}
  icon_height = {icon}
  item_icon_space = {4 * U}
  item_height = {item_h}
  item_padding = 0
  item_spacing = {2 * U}
  selected_item_pixmap_style = "select_*.png"
  scrollbar = true
  scrollbar_width = {3 * U}
  scrollbar_frame = "sb_frame_*.png"
  scrollbar_thumb = "sb_thumb_*.png"
}}

+ circular_progress {{
  id = "__timeout__"
  left = {rc[0]}
  top = {rc[1]}
  width = {RING_SIZE * S}
  height = {RING_SIZE * S}
  num_ticks = {TICKS}
  ticks_disappear = true
  start_angle = -64
  tick_bitmap = "tick.png"
  center_bitmap = "center.png"
}}

+ label {{
  id = "__timeout__"
  left = {lx}
  top = {ly}
  width = {(fw // 2) * S}
  height = {cfg['small']}
  text = "Booting in %d s"
  font = "{n_small}"
  color = "#FFE98A"
  align = "left"
}}

+ label {{
  left = {px(fx + fw // 2, fy)[0]}
  top = {ly}
  width = {(fw // 2 - 4) * S}
  height = {cfg['small']}
  text = "UP/DOWN: choose   ENTER: boot   E: edit   C: console"
  font = "{n_small}"
  color = "#A8FFF4"
  align = "right"
}}
"""
    (d / "theme.txt").write_text(theme)
    return dict(menu=(mx, my, mw, mh), item_h=item_h, icon=icon, fonts=(cfg["item"], cfg["small"]),
                ring=rc)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    art = make_art_bg()
    handoff = make_art_bg(panels=False)
    info = {}
    for res, cfg in RES.items():
        info[res] = build(res, cfg, art, handoff)
        print(res, "ok")
    art.save(OUT / "_art_320x180.png")        # source canvas, handy for previews
    (OUT / "_art_320x180.png").unlink()


if __name__ == "__main__":
    main()
