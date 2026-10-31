#!/usr/bin/env bash
# Removes GRUB's plain-text "Loading Linux ... / Loading initial ramdisk ..." lines from a grub.cfg,
# so after you pick an entry the themed menu stays on screen until the kernel starts.
#
#   scripts/grub_quiet_boot.sh -            filter stdin -> stdout (used by the installer)
#   sudo scripts/grub_quiet_boot.sh FILE    filter FILE in place (backup: FILE.acronix-quiet-backup)
#
# Works in any language: it drops a lone `echo '...'` line that is directly followed by a
# linux/initrd command (that is exactly how 10_linux emits them), nothing else.
# grub-mkconfig regenerates those lines whenever it runs again (Debian/Ubuntu do that on every
# kernel update), so re-run this on the new grub.cfg, or use the installer again.
# Distros whose 10_linux is built with quiet-boot (Manjaro) or that use BLS entries (Fedora)
# have no such lines and this is a harmless no-op.
set -euo pipefail

filter() {
  awk '
    function flush() { if (held != "") { print held; held = "" } }
    {
      if ($0 ~ /^[ \t]*echo[ \t]+(\047[^\047]*\047|"[^"]*")[ \t]*$/) { flush(); held = $0; next }
      if (held != "" && $0 ~ /^[ \t]*(linux|linuxefi|linux16|initrd|initrdefi|initrd16)[ \t]/) {
        held = ""; print; next
      }
      flush(); print
    }
    END { flush() }'
}

case ${1:-} in
  ""|-h|--help) sed -n 2,13p "$0"; [ -n "${1:-}" ] && exit 0 || exit 2 ;;
  -) filter ;;
  *)
    f=$1
    [ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }
    cp -p "$f" "$f.acronix-quiet-backup"
    tmp=$(mktemp)
    filter < "$f" > "$tmp"
    if command -v grub-script-check >/dev/null && ! grub-script-check "$tmp"; then
      echo "filtered file failed grub-script-check; left $f untouched" >&2; rm -f "$tmp"; exit 1
    fi
    cat "$tmp" > "$f"; rm -f "$tmp"
    echo "removed $(( $(wc -l < "$f.acronix-quiet-backup") - $(wc -l < "$f") )) boot message line(s) from $f"
    ;;
esac
