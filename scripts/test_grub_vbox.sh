#!/usr/bin/env bash
# Boots the theme in a throw-away VirtualBox VM and saves a screenshot of REAL GRUB.
# Nothing on your system is touched: the theme is embedded in a private disk image
# (BIOS GRUB with a memdisk), the VM is deleted at the end.
#
#   scripts/test_grub_vbox.sh [RESOLUTION] [OUT.png] [KEYS...]
#   scripts/test_grub_vbox.sh 1920x1080 /tmp/shot.png down down enter
#
# KEYS: up down enter esc e c (sent after GRUB is up; one screenshot at the end)
# Needs: VirtualBox, python3, grub (grub-mkimage). Work dir: $WORK (default /tmp/acx-grub-vm).
set -euo pipefail

RES=${1:-1920x1080}
OUT=${2:-$PWD/grub-vm-$RES.png}
shift $(( $# < 2 ? $# : 2 ))
KEYS=("$@")
HERE=$(cd "$(dirname "$0")/.." && pwd)
THEME=${THEME_DIR:-$HERE/grub/acronixos-cosmic/$RES}
WORK=${WORK:-/tmp/acx-grub-vm}
VM=acx-grub-test
GRUBDIR=/usr/lib/grub/i386-pc

[ -d "$THEME" ] || { echo "no theme for $RES in $HERE/grub/acronixos-cosmic" >&2; exit 1; }
for t in VBoxManage grub-mkimage python3; do command -v $t >/dev/null || { echo "missing: $t" >&2; exit 1; }; done
[ -d "$GRUBDIR" ] || { echo "missing $GRUBDIR (install grub with BIOS modules)" >&2; exit 1; }

rm -rf "$WORK"; mkdir -p "$WORK/mem/boot/grub" "$WORK/mem/themes" "$WORK/gd"
cp -r "$THEME" "$WORK/mem/themes/acronixos-cosmic"

# Test menu: the same --class lists that grub-mkconfig / os-prober generate.
{
cat <<EOF
insmod all_video
insmod gfxterm
insmod png
set gfxmode=${RES}x32
set gfxpayload=keep
terminal_output gfxterm
EOF
for f in "$WORK"/mem/themes/acronixos-cosmic/*.pf2; do echo "loadfont (memdisk)/themes/acronixos-cosmic/$(basename "$f")"; done
cat <<'EOF'
set theme=(memdisk)/themes/acronixos-cosmic/theme.txt
export theme
set timeout=30
set default=1
menuentry 'Arch Linux' --class arch --class gnu-linux --class gnu --class os { true }
menuentry 'Manjaro Linux' --class manjaro --class gnu-linux --class gnu --class os { true }
submenu 'Advanced options for Arch Linux' --class arch --class gnu-linux --class gnu --class os {
  menuentry 'Arch Linux, with Linux linux' --class arch --class gnu-linux --class os { true }
  menuentry 'Arch Linux, with Linux linux-lts' --class arch --class gnu-linux --class os { true }
}
menuentry 'Debian GNU/Linux' --class debian --class gnu-linux --class gnu --class os { true }
menuentry 'Ubuntu 24.04 LTS (on /dev/sda3)' --class ubuntu --class gnu-linux --class gnu --class os { true }
menuentry 'Fedora Linux (on /dev/sda4)' --class fedora --class gnu-linux --class gnu --class os { true }
menuentry 'Linux Mint (on /dev/sda5)' --class linuxmint --class gnu-linux --class gnu --class os { true }
menuentry 'Windows 11 (on /dev/nvme0n1p1)' --class windows --class os { true }
menuentry 'SomeUnknownDistro' --class somedistro --class gnu-linux --class gnu --class os { true }
menuentry 'UEFI Firmware Settings' --class efi { true }
EOF
} > "$WORK/mem/boot/grub/grub.cfg"

tar -C "$WORK/mem" -cf "$WORK/memdisk.tar" boot themes
grub-mkimage -O i386-pc -d $GRUBDIR -o "$WORK/gd/core.img" -p '(memdisk)/boot/grub' \
  -m "$WORK/memdisk.tar" biosdisk memdisk tar normal gfxterm gfxmenu png all_video vbe \
  video_bochs video_cirrus configfile echo true part_msdos >/dev/null
cp $GRUBDIR/boot.img "$WORK/gd/"

# grub-bios-setup refuses plain files, so lay the boot sectors out by hand:
# LBA0 = boot.img, LBA1.. = core.img, first core sector ends with the block list.
python3 -I - "$WORK" <<'EOF'
import struct, sys
w = sys.argv[1]
boot = bytearray(open(w + "/gd/boot.img", "rb").read())
core = bytearray(open(w + "/gd/core.img", "rb").read())
core += b"\0" * (-len(core) % 512)
n = len(core) // 512
struct.pack_into("<Q", boot, 0x5C, 1)
struct.pack_into("<QHH", core, 512 - 12, 2, n - 1, 0x820)
img = bytearray(16 * 1024 * 1024)
img[0:512] = boot
img[512:512 + len(core)] = core
open(w + "/disk.img", "wb").write(img)
EOF

cleanup() { VBoxManage controlvm $VM poweroff >/dev/null 2>&1 || true; sleep 1
            VBoxManage unregistervm $VM --delete >/dev/null 2>&1 || true; }
trap cleanup EXIT
VBoxManage unregistervm $VM --delete >/dev/null 2>&1 || true
VBoxManage convertfromraw "$WORK/disk.img" "$WORK/disk.vdi" --format VDI >/dev/null
VBoxManage createvm --name $VM --ostype Other_64 --register --basefolder "$WORK/vms" >/dev/null
VBoxManage modifyvm $VM --memory 128 --vram 64 --graphicscontroller vboxvga --boot1 disk \
  --firmware bios --audio-driver none --usb off
VBoxManage storagectl $VM --name sata --add sata >/dev/null
VBoxManage storageattach $VM --storagectl sata --port 0 --device 0 --type hdd --medium "$WORK/disk.vdi"
VBoxManage setextradata $VM CustomVideoMode1 ${RES}x32
VBoxManage startvm $VM --type headless >/dev/null
sleep 8

declare -A SC=([up]="e0 48 e0 c8" [down]="e0 50 e0 d0" [enter]="1c 9c" [esc]="01 81" [e]="12 92" [c]="2e ae")
for k in "${KEYS[@]}"; do
  VBoxManage controlvm $VM keyboardputscancode ${SC[$k]}; sleep 1
done
sleep 2
VBoxManage controlvm $VM screenshotpng "$OUT"
echo "screenshot: $OUT"
