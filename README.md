# Acronix Distro

Customizations for the Acronix Linux distro (UNI).

## Plymouth boot animation

There are two themes. They share the logo pieces; nothing in one depends on the other.

| Theme | Look |
|-------|------|
| `acronix64` | **Nintendo 64 / Smash 64 style** (current work) |
| `acronix`   | First version: modern, dark, soft glow (kept as it was) |

### acronix64: storyboard

All timings are seconds after the splash appears (constants at the top of `theme/acronix64.script.in`).

1. **0.0 CRT turn-on.** A white line opens into a flash; a dithered diamond-lattice backdrop appears under scanlines and darkened corners.
2. **0.5 UNI intro.** A character-select style frame (yellow band, white card, corner studs) drops in and bounces. The three logo blocks, in the official blue and as chunky 3D blocks, zoom in from the camera over manga speed lines and slam onto it: white flash, shake, comic burst, sparkles, a red "P1" tag and the tagline as a name plate.
3. **3.2 Versus wipe.** A red slab and a blue slab slam together with a burst at the seam. While they cover the screen the scene changes: the logo group moves to the top and the backdrop turns purple. Then they slide away.
4. **3.8 AcronixOS.** The letters of **ACRONIXOS** (outlined, extruded, dithered) zoom in one by one, then the red "PROYECTO DEL GRUPO 4T4-COM-S" plate stamps in from the right.
5. **After that.** The boot progress is shown as a Smash-style damage percent (white, then yellow, orange, red as it climbs). A hop wave runs along the letters, sparkles twinkle.
6. **Boot finished.** The counter jumps to 100% and Plymouth hands over to the login screen.

Plymouth callbacks handled: refresh, boot progress, system update progress (offline updates), quit, password, question, normal display and messages. The script module has no pause callback; Plymouth simply stops calling the refresh function while paused.

### Files

| Path | What it is |
|------|------------|
| `sources/logoUNI.jpg` | Original logo |
| `scripts/make_assets.sh` | Splits the logo into white PNG pieces (used by both themes) and builds the `acronix` theme |
| `scripts/make_assets64.sh` | Draws every image of `acronix64` with ImageMagick and builds its script. `SCRIPT_ONLY=1` rebuilds just the script in a second |
| `theme/acronix64.script.in` | The `acronix64` animation. **Edit this one**, not the generated `theme/acronix64/acronix64.script` |
| `theme/acronix64.layout` | Generated constants (piece offsets, letter spacing); needed by `SCRIPT_ONLY=1` |
| `theme/acronix64/` | The installable theme (generated) |
| `theme/acronix.script.in`, `theme/acronix/` | The first theme |
| `scripts/preview_plymouth.sh` | Preview window; installs nothing |
| `scripts/install_plymouth.sh` | Real install (needs sudo) |

Fonts: the images are pre-rendered with Noto Sans Black / Black Italic, so the boot screen needs no fonts. Use `FONT=... FONT_ITALIC=... scripts/make_assets64.sh` if they live elsewhere.

### Preview (safe, no sudo, installs nothing)

```bash
THEME=acronix64 scripts/preview_plymouth.sh 14        # 14 seconds in a window
PREVIEW_PROMPT=1 THEME=acronix64 scripts/preview_plymouth.sh 8   # also shows a message and a password prompt
DEBUG_LOG=/tmp/ply.log THEME=acronix64 scripts/preview_plymouth.sh   # keep plymouthd's log
```

### Install, update, go back

```bash
scripts/make_assets64.sh                    # after changing the logo, fonts or art
SCRIPT_ONLY=1 scripts/make_assets64.sh      # after editing only theme/acronix64.script.in
sudo scripts/install_plymouth.sh acronix64  # install + select + rebuild initramfs; run again to update
sudo plymouth-set-default-theme -R manjaro  # go back to the original theme
```

Installing copies the theme next to the existing ones; nothing is removed. Test it first in a VM or with a spare kernel entry if the machine matters.

### Performance notes (read before changing the animation)

Plymouth composites in software, and in the X11 preview it costs roughly **20 ns per repainted pixel**: a full 1080p repaint is about 40 ms. The animation is built around that:

- It updates **25 times per second** (every second Plymouth tick), like an N64 game.
- Every sprite update goes through `put` / `alpha` / `face` (top of the script), which skip the call when nothing changed. Plymouth repaints a sprite's area on *any* setter call, even with the same value.
- Each part of `refresh()` only runs inside its own time window.
- Nothing is scaled per update: zoom effects swap between pre-scaled copies (the stepped look is intended). Flashes last 3 updates.
- Full-screen images (background, CRT overlay, speed lines) are drawn at native 1080p so they are not rescaled at boot on 1080p screens. The background scroll stops when the title is in.
- The whole timeline is counted in frames (the script language has no clock). On a slow machine the animation plays slower, but never out of order.
- Size: about 3.6 MB of PNGs, which go into the initramfs.

### What has and has not been tested

- Tested: the theme loads in a real `plymouthd` (X11 preview), runs without script errors, every scene and the password/message screens render as designed, CPU use settles to about 10% when idle.
- Not tested: a real boot with the DRM renderer, other resolutions (the layout scales from 1920x1080 but only 1080p was looked at), and an encrypted-disk prompt with real keystrokes.

## GRUB

Planned: N64 Smash-style theme.
