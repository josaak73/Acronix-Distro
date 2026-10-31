#!/usr/bin/env bash
# Removes the AcronixOS Cosmic GRUB theme and puts GRUB back as it was.
#
#   sudo scripts/uninstall_grub_theme.sh [--yes] [--no-mkconfig] [--restore-backup]
#
#   default           deletes the managed block from /etc/default/grub (everything else is
#                     left as it is) and regenerates grub.cfg the same safe way the installer does
#   --restore-backup  instead copies back the newest /etc/default/grub.acronix-backup-* file
#
# Emergency (nothing boots the menu you expect): at the GRUB menu press `c` and run
#   configfile /boot/grub/grub.cfg.acronix-backup-<time>
# or, from a live USB, copy that backup over /boot/grub/grub.cfg.
# For testing without root: ROOT_PREFIX=/some/dir (use with --no-mkconfig).
set -euo pipefail

THEME_NAME=acronixos-cosmic
BEGIN="# >>> acronixos-cosmic (managed block, remove with uninstall_grub_theme.sh) >>>"
END="# <<< acronixos-cosmic <<<"
P=${ROOT_PREFIX:-}
DEFAULTS=$P/etc/default/grub
YES=0; MKCONFIG=1; RESTORE=0
while [ $# -gt 0 ]; do
  case $1 in
    --yes|-y) YES=1 ;;
    --no-mkconfig) MKCONFIG=0 ;;
    --restore-backup) RESTORE=1 ;;
    -h|--help) sed -n 2,14p "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac; shift
done
say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
[ "$(id -u)" = 0 ] || [ -n "$P" ] || { echo "run as root (sudo)" >&2; exit 1; }
[ -f "$DEFAULTS" ] || { echo "$DEFAULTS not found" >&2; exit 1; }
if   [ -d "$P/boot/grub" ];  then GRUBDIR=/boot/grub
elif [ -d "$P/boot/grub2" ]; then GRUBDIR=/boot/grub2
else echo "no /boot/grub or /boot/grub2 found" >&2; exit 1; fi
MKCONFIG_BIN=$(command -v grub-mkconfig || command -v grub2-mkconfig || true)
CHECK_BIN=$(command -v grub-script-check || command -v grub2-script-check || true)

if [ $YES = 0 ]; then
  read -r -p "Remove the $THEME_NAME theme and its /etc/default/grub block? [y/N] " a
  [[ $a =~ ^[yY]$ ]] || { echo aborted; exit 1; }
fi
TS=$(date +%Y%m%d-%H%M%S)
cp -p "$DEFAULTS" "$DEFAULTS.acronix-before-uninstall-$TS"

if [ $RESTORE = 1 ]; then
  # shellcheck disable=SC2012
  b=$(ls -1t "$DEFAULTS".acronix-backup-* 2>/dev/null | head -1 || true)
  [ -n "$b" ] || { echo "no $DEFAULTS.acronix-backup-* file found" >&2; exit 1; }
  cp -p "$b" "$DEFAULTS"; say "restored $b"
else
  esc() { printf '%s' "$1" | sed 's/[][\.*^$|]/\\&/g'; }
  sed "\|^$(esc "$BEGIN")\$|,\|^$(esc "$END")\$|d" "$DEFAULTS" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > "$DEFAULTS.tmp.$$"
  cat "$DEFAULTS.tmp.$$" > "$DEFAULTS"; rm -f "$DEFAULTS.tmp.$$"
  say "managed block removed from $DEFAULTS"
fi
rm -rf "$P$GRUBDIR/themes/$THEME_NAME"; say "theme folder removed"

if [ $MKCONFIG = 1 ] && [ -n "$MKCONFIG_BIN" ]; then
  tmp=$(mktemp)
  "$MKCONFIG_BIN" -o "$tmp"
  if [ -n "$CHECK_BIN" ] && ! "$CHECK_BIN" "$tmp"; then
    echo "generated grub.cfg failed grub-script-check; left the old grub.cfg in place" >&2
    rm -f "$tmp"; exit 1
  fi
  cp -p "$GRUBDIR/grub.cfg" "$GRUBDIR/grub.cfg.acronix-backup-$TS" 2>/dev/null || true
  cat "$tmp" > "$GRUBDIR/grub.cfg"; rm -f "$tmp"
  say "grub.cfg regenerated (previous one: grub.cfg.acronix-backup-$TS)"
else
  say "grub.cfg NOT regenerated: run grub-mkconfig -o $GRUBDIR/grub.cfg"
fi
