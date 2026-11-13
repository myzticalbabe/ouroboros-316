#!/usr/bin/env bash
# 02_rollback.sh - undo 00_install_hook.sh. Run inside Ubuntu, as root.
# Leaves the ESP with a stub that is never auto-updated again, which is the
# state the machine was in before the hook was installed.
set -euo pipefail

ESP=/boot/efi
STUB="$ESP/EFI/ubuntu/grub.cfg"
BACKUP="$ESP/EFI/ubuntu/grub.cfg.pre-hook"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: must run as root.  sudo bash $0" >&2
  exit 1
fi

for h in /etc/kernel/postinst.d/zzz-p8-esp-stub /etc/kernel/postrm.d/zzz-p8-esp-stub; do
  if [ -e "$h" ]; then
    rm -f "$h"
    echo "removed $h"
  else
    echo "absent  $h"
  fi
done

if [ -d /etc/p8-esp-stub ]; then
  rm -rf /etc/p8-esp-stub
  echo "removed /etc/p8-esp-stub (template + validator)"
fi

if [ -d /var/lib/p8-esp-stub ]; then
  rm -rf /var/lib/p8-esp-stub
  echo "removed /var/lib/p8-esp-stub (validation state)"
fi

if [ -f "$BACKUP" ]; then
  cp -p "$BACKUP" "$STUB"
  sync
  echo "restored $BACKUP -> $STUB ($(wc -c < "$STUB") bytes)"
else
  echo "WARN: no $BACKUP to restore; stub left as-is"
fi

echo ""
echo "Hook removed. The ESP stub will no longer follow kernel upgrades."
