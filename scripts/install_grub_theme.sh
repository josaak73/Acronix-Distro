#!/usr/bin/env bash
# Installs the AcronixOS Cosmic GRUB theme (Arch / Manjaro, Debian / Ubuntu, Fedora and friends).
#
#   sudo scripts/install_grub_theme.sh [--resolution WxH] [--yes] [--dry-run]
#                                      [--no-mkconfig] [--keep-boot-messages] [--cfg PATH]
#
# What it does (and nothing else):
#   1. copies the theme for your resolution       -> <grub dir>/themes/acronixos-cosmic
#   2. writes the settings (GRUB_THEME, GRUB_GFXMODE, menu style...) to
#        /etc/default/grub.d/99-acronixos-cosmic.cfg      (/etc/default/grub is NOT edited)
#      or, if this grub-mkconfig is too old to read that folder, appends one marked block to
#      /etc/default/grub (backed up first)
#   3. installs /etc/grub.d/08_acronixos_handoff   (cosmic background behind GRUB's text screens)
#   4. regenerates grub.cfg safely: temp file -> remove the plain "Loading Linux ..." lines
#      -> grub-script-check -> backup of the old grub.cfg -> replace
# Your entries, kernels, os-prober and the EFI boot entry are untouched.
# Undo with scripts/uninstall_grub_theme.sh.
#
# For testing without root: ROOT_PREFIX=/some/dir sets up a fake / (use with --no-mkconfig).
# ACRONIX_FORCE_BLOCK=1 forces the old "append a block to /etc/default/grub" method.
set -euo pipefail

THEME_NAME=acronixos-cosmic
BEGIN="# >>> acronixos-cosmic (managed block, remove with uninstall_grub_theme.sh) >>>"
END="# <<< acronixos-cosmic <<<"
KNOWN=(1920x1080 1600x900 1366x768 1280x720)
HERE=$(cd "$(dirname "$0")/.." && pwd)
SRC=$HERE/grub/$THEME_NAME
P=${ROOT_PREFIX:-}
DEFAULTS=$P/etc/default/grub
DROPIN=$P/etc/default/grub.d/99-acronixos-cosmic.cfg
HANDOFF=$P/etc/grub.d/08_acronixos_handoff

RES=; YES=0; MKCONFIG=1; DRY=0; QUIET=1; CFG=
while [ $# -gt 0 ]; do
  case $1 in
    --resolution) RES=$2; shift ;;
    --cfg) CFG=$2; shift ;;
    --yes|-y) YES=1 ;;
    --no-mkconfig) MKCONFIG=0 ;;
    --keep-boot-messages) QUIET=0 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n 2,19p "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac; shift
done

esc() { printf '%s' "$1" | sed 's/[][\.*^$|]/\\&/g'; }
say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
run() { if [ $DRY = 1 ]; then echo "   [dry-run] $*"; else "$@"; fi; }
[ "$(id -u)" = 0 ] || [ -n "$P" ] || { echo "run as root (sudo)" >&2; exit 1; }
[ -f "$DEFAULTS" ] || { echo "$DEFAULTS not found: is GRUB installed here?" >&2; exit 1; }

# ---- GRUB directory, tools, distro -------------------------------------------
if   [ -d "$P/boot/grub" ];  then GRUBDIR=/boot/grub
elif [ -d "$P/boot/grub2" ]; then GRUBDIR=/boot/grub2
else echo "no /boot/grub or /boot/grub2 found" >&2; exit 1; fi
MKCONFIG_BIN=$(command -v grub-mkconfig || command -v grub2-mkconfig || true)
CHECK_BIN=$(command -v grub-script-check || command -v grub2-script-check || true)
if [ -z "$CFG" ]; then
  CFG=$GRUBDIR/grub.cfg
  # older Fedora/RHEL on UEFI keep the real grub.cfg on the ESP
  if [ -f "$P/boot/efi/EFI/fedora/grub.cfg" ] && [ ! -L "$P/boot/efi/EFI/fedora/grub.cfg" ]; then
    CFG=/boot/efi/EFI/fedora/grub.cfg
  fi
fi
ID=; ID_LIKE=
[ -r "$P/etc/os-release" ] && eval "$(grep -E '^(ID|ID_LIKE)=' "$P/etc/os-release")" || true
FAMILY="$ID $ID_LIKE"

# newer GRUB (2.04+) reads /etc/default/grub.d/*.cfg itself; older ones do not
USE_DROPIN=1
if [ "${ACRONIX_FORCE_BLOCK:-0}" = 1 ]; then USE_DROPIN=0
elif [ -n "$MKCONFIG_BIN" ] && ! grep -q 'default/grub.d' "$MKCONFIG_BIN" 2>/dev/null; then USE_DROPIN=0; fi

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

# ---- plan and confirmation ----------------------------------------------------
TS=$(date +%Y%m%d-%H%M%S)
DEST=$P$GRUBDIR/themes/$THEME_NAME
timeout_now=$(bash -c "set +u; . '$DEFAULTS' >/dev/null 2>&1; echo \"\${GRUB_TIMEOUT:-5}\"" || echo 5)
[[ $timeout_now =~ ^[0-9]+$ ]] || timeout_now=5
[ "$timeout_now" -ge 1 ] || timeout_now=5          # 0 would skip the menu and the countdown
SETTINGS="GRUB_THEME=\"$GRUBDIR/themes/$THEME_NAME/theme.txt\"
GRUB_GFXMODE=\"$RES,auto\"
GRUB_GFXPAYLOAD_LINUX=keep
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=$timeout_now
GRUB_TERMINAL_OUTPUT=gfxterm"

say "distro  : ${ID:-unknown} (${ID_LIKE:-no ID_LIKE})"
say "theme   : $SRC/$RES  ->  $GRUBDIR/themes/$THEME_NAME"
if [ $USE_DROPIN = 1 ]; then say "settings: ${DROPIN#"$P"} (new file; /etc/default/grub is not edited)"
else say "settings: block appended to /etc/default/grub (this GRUB does not read grub.d; backup first)"; fi
say "handoff : ${HANDOFF#"$P"} (cosmic background behind GRUB text screens)"
if [ $MKCONFIG = 1 ] && [ -n "$MKCONFIG_BIN" ]; then
  say "grub.cfg: $CFG regenerated with $(basename "$MKCONFIG_BIN")$([ $QUIET = 1 ] && echo ', boot messages removed'), checked, old one backed up"
else
  say "grub.cfg: NOT regenerated (run $(basename "${MKCONFIG_BIN:-grub-mkconfig}") -o $CFG yourself)"
fi
case " $FAMILY " in
  *" debian "*|*" ubuntu "*)
    for f in "$P"/etc/default/grub.d/*.cfg; do
      [ -e "$f" ] && [ "$f" != "$DROPIN" ] && grep -qE '^(GRUB_TERMINAL|GRUB_TIMEOUT_STYLE|GRUB_THEME)=' "$f" \
        && warn "$(basename "$f") also sets GRUB_TERMINAL/TIMEOUT_STYLE/THEME; ours is read last (99) and wins"
    done
    say "note    : Debian/Ubuntu regenerate grub.cfg on every kernel update, which brings the 'Loading Linux' lines back; run scripts/grub_quiet_boot.sh /boot/grub/grub.cfg afterwards"
    say "note    : Windows/other systems need GRUB_DISABLE_OS_PROBER=false and os-prober installed" ;;
  *" fedora "*|*" rhel "*)
    say "note    : Fedora uses BLS entries (no 'Loading Linux' lines to remove); icons depend on the class of each BLS entry" ;;
  *" arch "*)
    say "note    : Arch regenerates grub.cfg only when you run grub-mkconfig; re-run this installer (or scripts/grub_quiet_boot.sh) after it" ;;
esac
if [ $YES = 0 ] && [ $DRY = 0 ]; then
  read -r -p "Continue? [y/N] " a; [[ $a =~ ^[yY]$ ]] || { echo aborted; exit 1; }
fi

# ---- 1. theme files -----------------------------------------------------------
run rm -rf "$DEST"
run mkdir -p "$DEST"
run cp -r "$SRC/$RES/." "$DEST/"

# ---- 2. settings ----------------------------------------------------------------
strip_block() { sed "\|^$(esc "$BEGIN")\$|,\|^$(esc "$END")\$|d" "$1" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}'; }
if [ $USE_DROPIN = 1 ]; then
  if [ $DRY = 1 ]; then echo "   [dry-run] would write ${DROPIN#"$P"}:"; echo "$SETTINGS" | sed 's/^/      /'
  else
    mkdir -p "$(dirname "$DROPIN")"
    printf '# AcronixOS Cosmic GRUB theme. Written by install_grub_theme.sh; remove with uninstall_grub_theme.sh\n%s\n' "$SETTINGS" > "$DROPIN"
    # a block from an older install would now be redundant
    if grep -qF "$BEGIN" "$DEFAULTS"; then strip_block "$DEFAULTS" > "$DEFAULTS.tmp.$$" && cat "$DEFAULTS.tmp.$$" > "$DEFAULTS"; rm -f "$DEFAULTS.tmp.$$"; fi
  fi
else
  if [ $DRY = 1 ]; then echo "   [dry-run] backup $DEFAULTS.acronix-backup-$TS and append block"
  else
    strip_block "$DEFAULTS" > "$DEFAULTS.acronix-backup-$TS"; chmod --reference="$DEFAULTS" "$DEFAULTS.acronix-backup-$TS"
    strip_block "$DEFAULTS" > "$DEFAULTS.tmp.$$" && cat "$DEFAULTS.tmp.$$" > "$DEFAULTS"; rm -f "$DEFAULTS.tmp.$$"
    printf '\n%s\n%s\n%s\n' "$BEGIN" "$SETTINGS" "$END" >> "$DEFAULTS"
  fi
fi

# ---- 3. handoff script ----------------------------------------------------------
run mkdir -p "$(dirname "$HANDOFF")"
run install -m 755 "$HERE/grub/grub.d/08_acronixos_handoff" "$HANDOFF"

# ---- 4. grub.cfg ------------------------------------------------------------------
if [ $MKCONFIG = 1 ] && [ -n "$MKCONFIG_BIN" ] && [ $DRY = 0 ]; then
  tmp=$(mktemp); tmp2=$(mktemp)
  "$MKCONFIG_BIN" -o "$tmp"
  if [ $QUIET = 1 ]; then "$HERE/scripts/grub_quiet_boot.sh" - < "$tmp" > "$tmp2"; else cp "$tmp" "$tmp2"; fi
  if [ -n "$CHECK_BIN" ] && ! "$CHECK_BIN" "$tmp2"; then
    echo "generated grub.cfg failed grub-script-check; NOT installed. Old grub.cfg left in place." >&2
    echo "Run scripts/uninstall_grub_theme.sh to remove the settings again." >&2
    rm -f "$tmp" "$tmp2"; exit 1
  fi
  grep -q "$THEME_NAME/theme.txt" "$tmp2" || warn "grub.cfg does not mention the theme (is GRUB_THEME overridden elsewhere?)"
  cp -p "$P$CFG" "$P$CFG.acronix-backup-$TS" 2>/dev/null || true
  cat "$tmp2" > "$P$CFG"; rm -f "$tmp" "$tmp2"
  say "grub.cfg updated (backup: $CFG.acronix-backup-$TS)"
fi
say "done. Reboot to see it. Rollback: scripts/uninstall_grub_theme.sh"
