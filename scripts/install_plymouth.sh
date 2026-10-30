#!/usr/bin/env bash
# Installs one of the Acronix Plymouth themes system-wide and rebuilds the initramfs.
# Run it yourself when you're happy with the preview:
#
#   sudo scripts/install_plymouth.sh acronixcosmos # cosmic pixel art (current)
#   sudo scripts/install_plymouth.sh acronix64     # Nintendo 64 / Smash 64 style
#   sudo scripts/install_plymouth.sh acronix       # the first, modern-looking version
#
# Installing only COPIES the theme next to the others and selects it; the previous
# default (manjaro) stays installed, and the last line tells you how to go back.
# Needs the `plymouth` hook in /etc/mkinitcpio.conf HOOKS (Manjaro has it by
# default) and `splash` on the kernel command line.
set -euo pipefail

THEME="${1:-}"
case "$THEME" in
    acronix|acronix64|acronixcosmos) ;;
    *) echo "Usage: sudo $0 acronixcosmos|acronix64|acronix" >&2; exit 1 ;;
esac

if [[ $EUID -ne 0 ]]; then
    echo "Run as root: sudo $0 $THEME" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREVIOUS="$(plymouth-set-default-theme)"

# rebuild the assets as the invoking user so generated files don't end up owned by root
BUILDER="${SUDO_USER:-root}"
case "$THEME" in
    acronix)   su "$BUILDER" -c "'$ROOT/scripts/make_assets.sh'"   > /dev/null ;;
    acronixcosmos) su "$BUILDER" -c "'$ROOT/scripts/make_assets_cosmos.py'" > /dev/null ;;
    acronix64) su "$BUILDER" -c "'$ROOT/scripts/make_assets64.sh'" > /dev/null ;;
esac

DEST="/usr/share/plymouth/themes/$THEME"
rm -rf "$DEST"
cp -r "$ROOT/theme/$THEME" "$DEST"

# -R rebuilds the initramfs so the theme is available at early boot
plymouth-set-default-theme -R "$THEME"
echo "Installed '$THEME' (was '$PREVIOUS'). Reboot to see it."
echo "To go back: sudo plymouth-set-default-theme -R $PREVIOUS"
