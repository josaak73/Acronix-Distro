#!/usr/bin/env bash
# Preview the Acronix Plymouth theme in a window, without installing anything.
#
# plymouthd insists on /run/plymouth, /etc/plymouth and /usr/share/plymouth/themes.
# Instead of touching them for real, we enter a private user+mount namespace
# (unshare) where those paths are replaced by a scratch copy that includes our
# theme. Everything disappears when the script exits; the host is untouched.
#
# Usage: [THEME=acronix64] scripts/preview_plymouth.sh [seconds]   (defaults: acronix, 8)
# PREVIEW_PROMPT=1 also shows a status message and a password prompt at the end.
# The theme is the folder name under theme/. Set DEBUG_LOG=/path to keep the full plymouthd log.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECONDS_TO_RUN="${1:-8}"
THEME="${THEME:-acronix}"
[[ -d "$ROOT/theme/$THEME" ]] || { echo "No such theme: theme/$THEME" >&2; exit 1; }
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

mkdir -p "$SCRATCH/themes" "$SCRATCH/etc"
cp -r /usr/share/plymouth/themes/. "$SCRATCH/themes/"
cp -r "$ROOT/theme/$THEME" "$SCRATCH/themes/$THEME"
printf '[Daemon]\nTheme=%s\nShowDelay=0\n' "$THEME" > "$SCRATCH/etc/plymouthd.conf"

inner() {
    mount --bind "$SCRATCH/themes" /usr/share/plymouth/themes
    mount --bind "$SCRATCH/etc/plymouthd.conf" /etc/plymouth/plymouthd.conf
    mount -t tmpfs tmpfs /run
    mkdir -p /run/plymouth

    plymouthd --no-daemon --debug --debug-file="$SCRATCH/debug.log" \
        --mode=boot --graphical-boot --no-boot-log &
    sleep 1
    plymouth show-splash
    # fake boot progress so the bar moves
    for i in $(seq 1 "$SECONDS_TO_RUN"); do
        plymouth system-update --progress=$((i * 100 / SECONDS_TO_RUN)) || true
        sleep 1
    done
    # PREVIEW_PROMPT=1 also shows a status message and a password prompt near the end
    if [[ "${PREVIEW_PROMPT:-0}" == 1 ]]; then
        plymouth display-message --text "Comprobando el sistema de archivos..." || true
        ( timeout 6 plymouth ask-for-password --prompt "Introduce la contraseña del disco" >/dev/null 2>&1 & )
        sleep 3
        plymouth update --status=x >/dev/null 2>&1 || true
        sleep 2
    fi
    plymouth quit || true
    wait || true
}
export SCRATCH SECONDS_TO_RUN THEME PREVIEW_PROMPT
export -f inner
unshare --user --map-root-user --mount bash -c inner || true

[[ -n "${DEBUG_LOG:-}" ]] && cp "$SCRATCH/debug.log" "$DEBUG_LOG"
echo "--- plymouthd debug log (errors only) ---"
grep -iE 'error|fail|script' "$SCRATCH/debug.log" 2>/dev/null | head -20 || true
