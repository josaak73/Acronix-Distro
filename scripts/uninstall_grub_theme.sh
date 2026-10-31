#!/usr/bin/env bash
# Removes the AcronixOS Cosmic GRUB theme and puts GRUB back as it was.
#
#   sudo scripts/uninstall_grub_theme.sh [--yes] [--no-mkconfig] [--restore-backup] [--cfg PATH]
#
# Removes: /etc/default/grub.d/99-acronixos-cosmic.cfg, /etc/grub.d/08_acronixos_handoff, the theme
# folder and (if an older install or an old GRUB used it) the marked block in /etc/default/grub.
# Then regenerates grub.cfg the same safe way the installer does (checked, old one backed up).
#   --restore-backup  also copies back the newest /etc/default/grub.acronix-backup-* file
#
# Emergency (the menu is not what you expect): at the GRUB menu press `c` and run
#   configfile /boot/grub/grub.cfg.acronix-backup-<time>
# or, from a live USB, copy that backup over /boot/grub/grub.cfg.
# For testing without root: ROOT_PREFIX=/some/dir (use with --no-mkconfig).
set -euo pipefail

THEME_NAME=acronixos-cosmic
BEGIN="# >>> acronixos-cosmic (managed block, remove with uninstall_grub_theme.sh) >>>"
END="# <<< acronixos-cosmic <<<"
P=${ROOT_PREFIX:-}
DEFAULTS=$P/etc/default/grub
DROPIN=$P/etc/default/grub.d/99-acronixos-cosmic.cfg
HANDOFF=$P/etc/grub.d/08_acronixos_handoff
HERE=$(cd "$(dirname "$0")/.." && pwd)
YES=0; MKCONFIG=1; RESTORE=0; CFG=
while [ $# -gt 0 ]; do
  case $1 in
    --yes|-y) YES=1 ;;
    --no-mkconfig) MKCONFIG=0 ;;
    --restore-backup) RESTORE=1 ;;
    --cfg) CFG=$2; shift ;;
    -h|--help) sed -n 2,14p "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac; shift
done
esc() { printf '%s' "$1" | sed 's/[][\.*^$|]/\\&/g'; }
say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
[ "$(id -u)" = 0 ] || [ -n "$P" ] || { echo "run as root (sudo)" >&2; exit 1; }
[ -f "$DEFAULTS" ] || { echo "$DEFAULTS not found" >&2; exit 1; }
if   [ -d "$P/boot/grub" ];  then GRUBDIR=/boot/grub
elif [ -d "$P/boot/grub2" ]; then GRUBDIR=/boot/grub2
else echo "no /boot/grub or /boot/grub2 found" >&2; exit 1; fi
if [ -z "$CFG" ]; then
  CFG=$GRUBDIR/grub.cfg
  if [ -f "$P/boot/efi/EFI/fedora/grub.cfg" ] && [ ! -L "$P/boot/efi/EFI/fedora/grub.cfg" ]; then
    CFG=/boot/efi/EFI/fedora/grub.cfg
  fi
fi
MKCONFIG_BIN=$(command -v grub-mkconfig || command -v grub2-mkconfig || true)
CHECK_BIN=$(command -v grub-script-check || command -v grub2-script-check || true)

if [ $YES = 0 ]; then
  read -r -p "Remove the $THEME_NAME theme and its settings? [y/N] " a
  [[ $a =~ ^[yY]$ ]] || { echo aborted; exit 1; }
fi
TS=$(date +%Y%m%d-%H%M%S)

if [ $RESTORE = 1 ]; then
  # shellcheck disable=SC2012
  b=$(ls -1t "$DEFAULTS".acronix-backup-* 2>/dev/null | head -1 || true)
  [ -n "$b" ] || { echo "no $DEFAULTS.acronix-backup-* file found" >&2; exit 1; }
  cp -p "$DEFAULTS" "$DEFAULTS.acronix-before-uninstall-$TS"
  cp -p "$b" "$DEFAULTS"; say "restored $b"
elif grep -qF "$BEGIN" "$DEFAULTS"; then
  cp -p "$DEFAULTS" "$DEFAULTS.acronix-before-uninstall-$TS"
  sed "\|^$(esc "$BEGIN")\$|,\|^$(esc "$END")\$|d" "$DEFAULTS" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > "$DEFAULTS.tmp.$$"
  cat "$DEFAULTS.tmp.$$" > "$DEFAULTS"; rm -f "$DEFAULTS.tmp.$$"
  say "managed block removed from $DEFAULTS"
fi
[ -e "$DROPIN" ] && { rm -f "$DROPIN"; say "removed ${DROPIN#"$P"}"; }
[ -e "$HANDOFF" ] && { rm -f "$HANDOFF"; say "removed ${HANDOFF#"$P"}"; }
rm -rf "$P$GRUBDIR/themes/$THEME_NAME"; say "theme folder removed"

if [ $MKCONFIG = 1 ] && [ -n "$MKCONFIG_BIN" ]; then
  tmp=$(mktemp)
  "$MKCONFIG_BIN" -o "$tmp"
  if [ -n "$CHECK_BIN" ] && ! "$CHECK_BIN" "$tmp"; then
    echo "generated grub.cfg failed grub-script-check; left the old grub.cfg in place" >&2
    rm -f "$tmp"; exit 1
  fi
  cp -p "$P$CFG" "$P$CFG.acronix-backup-$TS" 2>/dev/null || true
  cat "$tmp" > "$P$CFG"; rm -f "$tmp"
  say "grub.cfg regenerated (previous one: $CFG.acronix-backup-$TS)"
else
  say "grub.cfg NOT regenerated: run grub-mkconfig -o $CFG"
fi
