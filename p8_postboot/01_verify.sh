#!/usr/bin/env bash
# 01_verify.sh - assert the post-reboot state. Run inside Ubuntu, as root.
# Every check prints PASS or FAIL with the reason, and the script exits 1 if
# any check failed. A check that cannot run prints FAIL, never PASS.
set -uo pipefail

ESP=/boot/efi
STUB="$ESP/EFI/ubuntu/grub.cfg"
EXPECT_UUID=58e46179-d777-4203-a807-8794a3fb2351
pass=0
fail=0

ok()   { printf 'PASS  %s\n' "$*"; pass=$((pass + 1)); }
bad()  { printf 'FAIL  %s\n' "$*"; fail=$((fail + 1)); }
info() { printf '      %s\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root so the ESP can be read.  sudo bash $0" >&2
  exit 1
fi

# ---- 1. ESP mounted and carrying the expected files ----
if mountpoint -q "$ESP"; then
  ok "ESP mounted at $ESP"
else
  bad "ESP not mounted at $ESP (mount it: mount /dev/nvme0n1p1 $ESP)"
fi

for f in shimx64.efi grubx64.efi mmx64.efi; do
  if [ -s "$ESP/EFI/ubuntu/$f" ]; then
    ok "present $f ($(wc -c < "$ESP/EFI/ubuntu/$f") bytes)"
  else
    bad "missing or empty $ESP/EFI/ubuntu/$f"
  fi
done

if [ -s "$STUB" ]; then
  ok "stub present ($(wc -c < "$STUB") bytes)"
else
  bad "stub missing or empty: $STUB"
fi

# ---- 2. the stub carries the live root UUID, not a stale one ----
live_uuid="$(findmnt -no UUID / 2>/dev/null || true)"
if [ -z "$live_uuid" ]; then
  bad "cannot read live root UUID from findmnt"
elif [ "$live_uuid" = "$EXPECT_UUID" ]; then
  ok "root UUID is $live_uuid (matches the UUID recorded on Windows)"
else
  bad "root UUID is $live_uuid, expected $EXPECT_UUID - the disk was re-created"
fi

if [ -s "$STUB" ] && [ -n "$live_uuid" ]; then
  if grep -q "$live_uuid" "$STUB"; then
    ok "stub references live UUID $live_uuid"
  else
    bad "stub does NOT reference live UUID $live_uuid - it points at a stale filesystem"
  fi
fi

# ---- 3. stub structure is not truncated ----
if [ -s "$STUB" ]; then
  entries="$(grep -c '^menuentry' "$STUB" || true)"
  if [ "${entries:-0}" -ge 3 ]; then
    ok "stub defines $entries menu entries"
  else
    bad "stub defines ${entries:-0} menu entries, expected at least 3"
  fi
  if grep -q 'bootmgfw.efi' "$STUB"; then
    ok "stub keeps a Windows chainload entry"
  else
    bad "stub lost its Windows chainload entry"
  fi
fi

# ---- 4. kernels and initrds are paired ----
kernels="$(ls -1 /boot/vmlinuz-* 2>/dev/null || true)"
if [ -z "$kernels" ]; then
  bad "no /boot/vmlinuz-* present"
else
  ok "kernels present: $(echo "$kernels" | wc -l)"
  for k in $kernels; do
    ver="${k#/boot/vmlinuz-}"
    if [ -s "/boot/initrd.img-$ver" ]; then
      ok "initrd paired for $ver"
    else
      bad "no initrd for $ver (/boot/initrd.img-$ver)"
    fi
  done
fi

newest="$(ls -1 /boot/vmlinuz-* 2>/dev/null | sort -V | tail -n1 || true)"
if [ -n "$newest" ]; then
  ver="${newest#/boot/vmlinuz-}"
  info "newest kernel: $ver"
  if [ -s /boot/grub/grub.cfg ] && grep -q "$ver" /boot/grub/grub.cfg; then
    ok "/boot/grub/grub.cfg mentions $ver"
  else
    bad "/boot/grub/grub.cfg does not mention $ver - run update-grub"
  fi
fi

# ---- 4b. the validator approves the live stub ----
if [ -f /etc/p8-esp-stub/esp_validate.py ] && [ -s "$STUB" ]; then
  py="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
  if [ -z "$py" ]; then
    bad "python3 missing - cannot run the stub validator"
  elif "$py" /etc/p8-esp-stub/esp_validate.py "$STUB" \
        --state /var/lib/p8-esp-stub/validate-state.json --force >/tmp/esp_validate.out 2>&1; then
    ok "validator approved $STUB ($(grep -c '^menuentry' "$STUB") entries)"
  else
    bad "validator rejected $STUB - see /tmp/esp_validate.out"
    sed 's/^/      /' /tmp/esp_validate.out
  fi
else
  bad "validator not installed at /etc/p8-esp-stub/esp_validate.py - stub unproven"
fi

# ---- 5. hook installed and executable ----
for h in /etc/kernel/postinst.d/zzz-p8-esp-stub /etc/kernel/postrm.d/zzz-p8-esp-stub; do
  if [ -x "$h" ]; then
    ok "hook executable: $h"
  else
    bad "hook missing or not executable: $h"
  fi
done
if [ -s /etc/p8-esp-stub/grub.cfg.tmpl ]; then
  ok "template installed: /etc/p8-esp-stub/grub.cfg.tmpl"
else
  bad "template missing: /etc/p8-esp-stub/grub.cfg.tmpl"
fi

# ---- 6. firmware entry still points at shim ----
if command -v efibootmgr >/dev/null 2>&1; then
  if efibootmgr -v 2>/dev/null | grep -qi 'ubuntu'; then
    ok "firmware lists an ubuntu entry"
    efibootmgr -v 2>/dev/null | grep -i 'ubuntu' | sed 's/^/      /'
  else
    bad "firmware lists no ubuntu entry - efibootmgr -v | grep -i ubuntu was empty"
  fi
else
  bad "efibootmgr not installed: apt install efibootmgr"
fi

# ---- 7. hostname is what it should be, and will survive a reboot ----
want_host="$(cat /etc/hostname 2>/dev/null | tr -d '[:space:]')"
live_host="$(hostnamectl --static 2>/dev/null || cat /proc/sys/kernel/hostname)"
if [ -z "$want_host" ]; then
  bad "/etc/hostname is empty - hostname will not survive a reboot"
elif [ "$want_host" = "$live_host" ]; then
  ok "hostname '$live_host' matches /etc/hostname"
else
  bad "hostname '$live_host' does not match /etc/hostname '$want_host'"
fi
if grep -q "$want_host" /etc/hosts 2>/dev/null; then
  ok "/etc/hosts has an entry for $want_host"
else
  bad "/etc/hosts has no entry for $want_host - sudo may stall on 'unable to resolve host'"
fi

# ---- 8. ESP has room to write ----
avail="$(df -Pk "$ESP" 2>/dev/null | awk 'NR==2 {print $4}' || true)"
if [ -n "$avail" ] && [ "$avail" -gt 2048 ]; then
  ok "ESP free space $((avail / 1024)) MB"
else
  bad "ESP free space ${avail:-unknown} KB - too small to re-render the stub"
fi

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
