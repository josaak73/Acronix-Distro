#!/usr/bin/env bash
# Installs the AcronixOS Cosmic GRUB theme.
#
#   sudo scripts/install_grub_theme.sh [--resolution WxH] [--yes] [--no-mkconfig] [--dry-run]
#
# What it does (and nothing else):
#   1. backs up /etc/default/grub                       -> /etc/default/grub.acronix-backup-<time>
#   2. copies the theme for your resolution             -> <grub dir>/themes/acronixos-cosmic
#   3. appends ONE marked block to /etc/default/grub    (GRUB_THEME, GRUB_GFXMODE, menu style)
#   4. regenerates grub.cfg safely: written to a temp file, checked with grub-script-check,
#      the old one is backed up, and only then replaced.
# Your menu entries, kernels, os-prober and the existing lines of /etc/default/grub are untouched.
# Undo with scripts/uninstall_grub_theme.sh.
#
# For testing without root: ROOT_PREFIX=/some/dir sets up a fake / (use with --no-mkconfig).
set -euo pipefail

THEME_NAME=acronixos-cosmic
BEGIN="# >>> acronixos-cosmic (managed block, remove with uninstall_grub_theme.sh) >>>"
END="# <<< acronixos-cosmic <<<"
KNOWN=(1920x1080 1600x900 1366x768 1280x720)
HERE=$(cd "$(dirname "$0")/.." && pwd)
SRC=$HERE/grub/$THEME_NAME
P=${ROOT_PREFIX:-}
DEFAULTS=$P/etc/default/grub

RES=; YES=0; MKCONFIG=1; DRY=0
while [ $# -gt 0 ]; do
  case $1 in
    --resolution) RES=$2; shift ;;
    --yes|-y) YES=1 ;;
    --no-mkconfig) MKCONFIG=0 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n 2,16p "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac; shift
done

esc() { printf '%s' "$1" | sed 's/[][\.*^$|]/\\&/g'; }
say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
run() { if [ $DRY = 1 ]; then echo "   [dry-run] $*"; else "$@"; fi; }
[ "$(id -u)" = 0 ] || [ -n "$P" ] || { echo "run as root (sudo)" >&2; exit 1; }
[ -f "$DEFAULTS" ] || { echo "$DEFAULTS not found: is GRUB installed here?" >&2; exit 1; }

# ---- GRUB directory and tools -------------------------------------------------
if   [ -d "$P/boot/grub" ];  then GRUBDIR=/boot/grub
elif [ -d "$P/boot/grub2" ]; then GRUBDIR=/boot/grub2
else echo "no /boot/grub or /boot/grub2 found" >&2; exit 1; fi
MKCONFIG_BIN=$(command -v grub-mkconfig || command -v grub2-mkconfig || true)
CHECK_BIN=$(command -v grub-script-check || command -v grub2-script-check || true)

# ---- resolution ---------------------------------------------------------------
if [ -z "$RES" ]; then
  gm=$(bash -c "set +u; . '$DEFAULTS' >/dev/null 2>&1; echo \"\${GRUB_GFXMODE:-}\"" || true)
  gm=${gm%%[,;]*}
  if [[ $gm =~ ^([0-9]+)x([0-9]+) ]]; then dw=${BASH_REMATCH[1]}; dh=${BASH_REMATCH[2]}
  elif [ -r /sys/class/graphics/fb0/virtual_size ]; then
    IFS=, read -r dw dh < /sys/class/graphics/fb0/virtual_size
  else dw=0; dh=0; fi
  RES=1280x720
  for r in "${KNOWN[@]}"; do
    w=${r%x*}; h=${r#*x}
    if [ "${dw:-0}" -ge "$w" ] && [ "${dh:-0}" -ge "$h" ]; then RES=$r; break; fi
  done
  say "resolution: $RES (detected ${dw:-?}x${dh:-?}; override with --resolution)"
fi
[ -d "$SRC/$RES" ] || { echo "no theme for $RES. Available: ${KNOWN[*]}" >&2; exit 1; }

# ---- confirmation -------------------------------------------------------------
TS=$(date +%Y%m%d-%H%M%S)
DEST=$P$GRUBDIR/themes/$THEME_NAME
say "theme   : $SRC/$RES  ->  $GRUBDIR/themes/$THEME_NAME"
say "config  : $DEFAULTS (backup: grub.acronix-backup-$TS, then one managed block appended)"
if [ $MKCONFIG = 1 ] && [ -n "$MKCONFIG_BIN" ]; then
  say "grub.cfg: regenerated with $(basename "$MKCONFIG_BIN"), checked first, old one backed up"
else
  say "grub.cfg: NOT regenerated (run $(basename "${MKCONFIG_BIN:-grub-mkconfig}") -o $GRUBDIR/grub.cfg yourself)"
fi
if [ $YES = 0 ] && [ $DRY = 0 ]; then
  read -r -p "Continue? [y/N] " a; [[ $a =~ ^[yY]$ ]] || { echo aborted; exit 1; }
fi

# ---- 1. backup ----------------------------------------------------------------
# (if an older copy of our block is present it is left out, so the backup is always the pristine file)
strip_block() { sed "\|^$(esc "$BEGIN")\$|,\|^$(esc "$END")\$|d" "$1" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}'; }
if [ $DRY = 1 ]; then echo "   [dry-run] backup $DEFAULTS.acronix-backup-$TS"
else strip_block "$DEFAULTS" > "$DEFAULTS.acronix-backup-$TS"; chmod --reference="$DEFAULTS" "$DEFAULTS.acronix-backup-$TS"; fi

# ---- 2. theme files -----------------------------------------------------------
run rm -rf "$DEST"
run mkdir -p "$DEST"
run cp -r "$SRC/$RES/." "$DEST/"

# ---- 3. managed block (later assignments override earlier ones; nothing is edited) --
timeout_now=$(bash -c "set +u; . '$DEFAULTS' >/dev/null 2>&1; echo \"\${GRUB_TIMEOUT:-5}\"" || echo 5)
[[ $timeout_now =~ ^[0-9]+$ ]] || timeout_now=5
[ "$timeout_now" -ge 1 ] || timeout_now=5          # 0 would skip the menu and the countdown
BLOCK="$BEGIN
GRUB_THEME=\"$GRUBDIR/themes/$THEME_NAME/theme.txt\"
GRUB_GFXMODE=\"$RES,auto\"
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=$timeout_now
GRUB_TERMINAL_OUTPUT=gfxterm
$END"
if [ $DRY = 1 ]; then echo "   [dry-run] would append:"; echo "$BLOCK" | sed 's/^/      /'
else
  # drop an older copy of the block first so re-running is idempotent
  strip_block "$DEFAULTS" > "$DEFAULTS.tmp.$$" && cat "$DEFAULTS.tmp.$$" > "$DEFAULTS" && rm -f "$DEFAULTS.tmp.$$"
  printf '\n%s\n' "$BLOCK" >> "$DEFAULTS"
fi

# ---- 4. grub.cfg --------------------------------------------------------------
if [ $MKCONFIG = 1 ] && [ -n "$MKCONFIG_BIN" ] && [ $DRY = 0 ]; then
  tmp=$(mktemp)
  "$MKCONFIG_BIN" -o "$tmp"
  if [ -n "$CHECK_BIN" ] && ! "$CHECK_BIN" "$tmp"; then
    echo "generated grub.cfg failed grub-script-check; NOT installed. Restoring $DEFAULTS" >&2
    cp -p "$DEFAULTS.acronix-backup-$TS" "$DEFAULTS"; rm -f "$tmp"; exit 1
  fi
  grep -q "$THEME_NAME/theme.txt" "$tmp" || echo "warning: grub.cfg does not mention the theme" >&2
  cp -p "$GRUBDIR/grub.cfg" "$GRUBDIR/grub.cfg.acronix-backup-$TS" 2>/dev/null || true
  cat "$tmp" > "$GRUBDIR/grub.cfg"; rm -f "$tmp"
  say "grub.cfg updated (backup: grub.cfg.acronix-backup-$TS)"
fi
say "done. Reboot to see it. Rollback: scripts/uninstall_grub_theme.sh"
