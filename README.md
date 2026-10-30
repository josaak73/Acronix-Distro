# Acronix Distro

Customizations for the Acronix Linux distro (UNI).

## Plymouth boot animation

There are three themes. They share the logo pieces; nothing in one depends on the other.

| Theme | Look |
|-------|------|
| `acronixcosmos` | **Cosmic pixel art** (current work, see below) |
| `acronix64` | Nintendo 64 / Smash 64 style |
| `acronix`   | First version: modern, dark, soft glow (kept as it was) |

### acronixcosmos: cosmic pixel art

Original pixel art inspired by the atmosphere of 16-bit/GBA-era space backdrops (starfield, violet nebulae, a crescent moon, a layered pink/cyan/purple cloud horizon). No third-party art is used.

Storyboard (seconds after the splash appears):

1. **0.0** Dark sky, stars and nebulae fade in; the clouds start drifting.
2. **1.4** The crescent moon (the recurring AcronixOS symbol) fades in and flickers softly.
3. **1.8-3.6** The three UNI logo pieces (redrawn as pixel art from the original logo shape) enter from different sides and assemble, then a dithered glow pulse.
4. **3.9-5.0** `UNIVERSIDAD NACIONAL DE INGENIERÍA`, then `4T4-COM-S`.
5. **5.0** The progress path appears: 16 five-point stars that light up as boot advances, a travelling bright star, `LOADING ACRONIXOS...`. More twinkling stars appear and the moon brightens with progress.

Throughout: big five-point stars twinkle, three small spiral galaxies turn slowly, and two shooting stars with fading trails cross the sky every few seconds.
6. **6.3-9** The UNI group fades out, a luminous star rises, `AcronixOS` drops in letter by letter, tagline appears, small stars sparkle around the title.
7. **Boot finished** The path is left full and Plymouth hands over to the login screen.

How the art stays crisp: everything is drawn on a 320x180 grid and enlarged by a **whole number** (nearest neighbour) at build time into `s3_`, `s4_`, `s5_`, `s6_`, `s8_` image sets. The script picks the smallest scale that covers the screen (1080p uses x6, 720p x4); screens that are not 16:9 are centred and cropped at the edges. Nothing is resized at boot.

| Path | What it is |
|------|------------|
| `scripts/make_assets_cosmos.py` | Draws all images (Python + Pillow, no other tools). `SCRIPT_ONLY=1` rebuilds only the script |
| `theme/acronixcosmos.script.in` | The animation. **Edit this one**, not the generated script |
| `theme/acronixcosmos.layout` | Generated constants |
| `theme/acronixcosmos/` | The installable theme (generated, about 1.4 MB) |

```bash
THEME=acronixcosmos scripts/preview_plymouth.sh 14            # preview, installs nothing
python3 scripts/make_assets_cosmos.py                         # after changing the art
sudo scripts/install_plymouth.sh acronixcosmos                # install + select + rebuild initramfs
sudo plymouth-set-default-theme -R manjaro                    # go back
```

Plymouth script gotchas found while building it (worth knowing before editing): arrays first written inside a function become private to it, so declare them at top level first; a helper taking a start time as its first argument returned wrong values, so the time windows are written inline; global constants must be defined before the function that uses them.

Tested: loads in a real `plymouthd` (X11 preview) at 1920x1080 and 1366x768, full timeline, password prompt; CPU about 20-30% of one core while animating. Not tested: a real DRM boot, 4:3 screens, 4K.

### Testing in an Arch Linux VM

Packages in the VM: `plymouth` (always). For a quick preview you also need an X11 session (`xorg-server` plus any desktop or window manager); `unshare` comes with `util-linux`. For a real boot test you need `mkinitcpio` (default on Arch) and your bootloader (`grub`, for example). Only if you regenerate the art inside the VM: `python` and `python-pillow`. Optional: `openssh` to copy files with `scp`/`rsync`.

Copy the files (the generated theme folder is enough for a real boot; add `scripts/` for the preview):

```bash
rsync -a theme/acronixcosmos user@vm-ip:~/            # from the host
rsync -a scripts user@vm-ip:~/                        # only for the preview
```

**A. Preview inside the VM, nothing installed** (X11 session, repo layout `theme/` + `scripts/` needed):

```bash
THEME=acronixcosmos scripts/preview_plymouth.sh 14
```

**B. Real boot test** (take a VM snapshot first):

```bash
sudo cp -r ~/acronixcosmos /usr/share/plymouth/themes/
# /etc/mkinitcpio.conf: put `plymouth` in HOOKS after `udev` and before `encrypt`/`filesystems`, e.g.
#   HOOKS=(base udev autodetect modconf kms keyboard keymap consolefont block plymouth filesystems fsck)
sudo plymouth-set-default-theme -R acronixcosmos      # runs mkinitcpio -P
# kernel command line needs `quiet splash` (GRUB):
#   edit GRUB_CMDLINE_LINUX_DEFAULT in /etc/default/grub, then
sudo grub-mkconfig -o /boot/grub/grub.cfg
sudo reboot
```

Go back with `plymouth-set-default-theme --list` to see what is installed, then `sudo plymouth-set-default-theme -R <previous-theme>`.

VM tips: use a virtual GPU with KMS (virt-manager/QEMU: virtio or QXL; VirtualBox: VMSVGA; VMware: vmwgfx). A 16:9 resolution (1920x1080, 1280x720) shows the art exactly. If the splash does not appear: check that `plymouth` is in HOOKS before `filesystems`, that `splash` is on the command line, and run `sudo plymouthd --debug --debug-file=/tmp/ply.log` to look for script errors. These Arch steps were written from the host's Arch-family setup and have not been run on a real Arch VM.

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

Planned (style to be confirmed: the Plymouth direction moved from N64/Smash to cosmic pixel art).
