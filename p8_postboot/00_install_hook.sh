#!/usr/bin/env bash
# 00_install_hook.sh - run INSIDE Ubuntu on P8, as root, after the reboot.
#
# What it does
#   1. stores the ESP stub template and the GRUB validator on the root filesystem
#   2. installs a kernel postinst/postrm hook that re-renders the ESP stub with
#      the CURRENT root UUID every time a kernel is added or removed
#   3. validates the rendered stub before it is trusted, and restores the
#      previous bytes if the validator rejects it
#   4. renders once now, so the ESP is correct immediately
#
# Why a hook and not a one-off edit: the ESP stub is the only thing the firmware
# can execute, and `apt upgrade` rewrites /boot/grub/grub.cfg and re-runs
# grub-install. Without a hook the stub keeps whatever UUID and whatever stale
# kernel list it had at install time, and a kernel upgrade silently reverts the
# machine to a Windows-only menu.
#
# The hook never fails a kernel install: every error is logged and the hook
# exits 0, so a broken ESP can never wedge apt. A rejected stub is rolled back
# instead of published.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: must run as root.  sudo bash $0" >&2
  exit 1
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMPL_SRC="$SRC_DIR/grub.cfg.tmpl"
TMPL_DST=/etc/p8-esp-stub/grub.cfg.tmpl
STORE=/etc/p8-esp-stub
HOOK_INSTALL=/etc/kernel/postinst.d/zzz-p8-esp-stub
HOOK_REMOVE=/etc/kernel/postrm.d/zzz-p8-esp-stub
LOG=/var/log/p8-esp-stub.log

say() { printf '%s\n' "$*"; }

if [ ! -f "$TMPL_SRC" ]; then
  echo "ERROR: template not found: $TMPL_SRC" >&2
  echo "       run this script from the p8_postboot directory" >&2
  exit 1
fi

# The validator is optional: without it the hook still renders, it just cannot
# prove the result. Say so rather than pretending.
validator_src=""
for cand in "$SRC_DIR/validate_grub.py" "$SRC_DIR/../validate_grub.py" "$SRC_DIR/esp_validate.py" "$SRC_DIR/../esp_validate.py"; do
  if [ -f "$cand" ]; then validator_src="$cand"; fi
done

# ---------- 1. ESP must be mounted, or mount it ----------
ESP=/boot/efi
if ! mountpoint -q "$ESP"; then
  say "ESP not mounted at $ESP - looking it up"
  esp_partuuid=80ce903d-fccd-4004-8f95-f4eb447e5465
  esp_dev="$(blkid -t "PARTUUID=$esp_partuuid" -o device 2>/dev/null | head -n1 || true)"
  if [ -z "$esp_dev" ]; then
    esp_dev="$(lsblk -rno NAME,FSTYPE,PARTTYPE | awk '$2=="vfat" && $3 ~ /c12a7328/ {print "/dev/"$1; exit}')"
  fi
  if [ -z "$esp_dev" ]; then
    echo "ERROR: cannot locate the EFI System Partition (PARTUUID $esp_partuuid)" >&2
    exit 1
  fi
  say "mounting $esp_dev at $ESP"
  mkdir -p "$ESP"
  mount "$esp_dev" "$ESP"
fi

if [ ! -d "$ESP/EFI/ubuntu" ]; then
  echo "ERROR: $ESP/EFI/ubuntu missing - this is not the ESP this machine boots from" >&2
  exit 1
fi

# ---------- 2. install template + validator ----------
install -d -m 0755 "$STORE"
install -m 0644 "$TMPL_SRC" "$TMPL_DST"
say "template installed: $TMPL_DST"

if [ -n "$validator_src" ]; then
  install -m 0644 "$validator_src" "$STORE/validate_grub.py"
  if [ -f "$SRC_DIR/esp_validate.py" ]; then
    install -m 0644 "$SRC_DIR/esp_validate.py" "$STORE/esp_validate.py"
  elif [ -f "$SRC_DIR/../esp_validate.py" ]; then
    install -m 0644 "$SRC_DIR/../esp_validate.py" "$STORE/esp_validate.py"
  fi
  install -d -m 0755 /var/lib/p8-esp-stub
  if [ -f "$STORE/esp_validate.py" ]; then
    say "validator installed: $STORE/esp_validate.py"
  else
    say "WARN: esp_validate.py not found next to this script - hook will validate inline only"
  fi
else
  say "WARN: validate_grub.py not found - hook cannot validate its own output"
fi

# ---------- 3. install the hook (same body in both dirs) ----------
install -d -m 0755 /etc/kernel/postinst.d /etc/kernel/postrm.d

hook_body() {
  cat <<'HOOK'
#!/bin/sh
# zzz-p8-esp-stub - keep the ESP recovery stub correct across kernel changes.
# Installed by p8_postboot/00_install_hook.sh. Never fails the caller.
# A rendered stub is validated before it is trusted; a rejected stub is
# rolled back to the previous bytes rather than left on the ESP.
set -u

LOG=/var/log/p8-esp-stub.log
TMPL=/etc/p8-esp-stub/grub.cfg.tmpl
VALIDATOR=/etc/p8-esp-stub/esp_validate.py
VSTATE=/var/lib/p8-esp-stub/validate-state.json
ESP=/boot/efi
TARGET="$ESP/EFI/ubuntu/grub.cfg"

log() { printf '%s %s\n' "$(date -Is)" "$*" >> "$LOG" 2>/dev/null || true; }

validate_or_rollback() {
  prev="$1"
  if [ ! -f "$VALIDATOR" ]; then
    log "SKIP: validator not installed, stub published unproven"
    return 0
  fi
  py="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
  if [ -z "$py" ]; then
    log "SKIP: no python3 on PATH, stub published unproven"
    return 0
  fi
  if "$py" "$VALIDATOR" "$TARGET" --state "$VSTATE" --force >/dev/null 2>&1; then
    log "OK: validator approved stub"
    return 0
  fi
  rc=$?
  log "CRITICAL: validator rejected stub (rc=$rc) - not trusted"
  if [ -n "$prev" ] && [ -f "$prev" ]; then
    if cp -p "$prev" "$TARGET"; then
      sync
      log "OK: rolled back to previous stub"
    else
      log "CRITICAL: rollback copy failed - ESP holds the rejected stub"
    fi
  else
    log "CRITICAL: no previous stub available to roll back to"
  fi
  return 0
}

main() {
  [ -d "$ESP/EFI/ubuntu" ] || { log "SKIP: $ESP/EFI/ubuntu absent"; return 0; }
  [ -f "$TMPL" ] || { log "SKIP: template $TMPL absent"; return 0; }

  uuid="$(findmnt -no UUID / 2>/dev/null || true)"
  [ -n "$uuid" ] || { log "ERROR: cannot read root UUID from findmnt"; return 0; }

  tmp="$TARGET.new.$$"
  if ! sed "s|@P8UUID@|$uuid|g" "$TMPL" > "$tmp" 2>/dev/null; then
    log "ERROR: sed failed rendering template"
    rm -f "$tmp"
    return 0
  fi

  if [ ! -s "$tmp" ]; then
    log "ERROR: rendered stub is empty"
    rm -f "$tmp"
    return 0
  fi

  if ! grep -q "$uuid" "$tmp"; then
    log "ERROR: rendered stub does not contain root UUID $uuid"
    rm -f "$tmp"
    return 0
  fi

  if ! grep -q '^menuentry' "$tmp"; then
    log "ERROR: rendered stub has no menuentry"
    rm -f "$tmp"
    return 0
  fi

  if cmp -s "$tmp" "$TARGET"; then
    log "OK: stub already current for $uuid"
    rm -f "$tmp"
    return 0
  fi

  prev="$TARGET.prev.$$"
  cp -p "$TARGET" "$prev" 2>/dev/null || prev=""

  if mv -f "$tmp" "$TARGET"; then
    sync
    log "OK: stub re-rendered for $uuid ($(wc -c < "$TARGET") bytes)"
    validate_or_rollback "$prev"
  else
    log "ERROR: mv into ESP failed"
    rm -f "$tmp"
  fi

  [ -n "$prev" ] && rm -f "$prev"
  return 0
}

main "$@"
exit 0
HOOK
}

hook_body > "$HOOK_INSTALL"
hook_body > "$HOOK_REMOVE"
chmod 0755 "$HOOK_INSTALL" "$HOOK_REMOVE"
say "hook installed: $HOOK_INSTALL"
say "hook installed: $HOOK_REMOVE"

# ---------- 4. back up the current stub, then render once ----------
if [ -f "$ESP/EFI/ubuntu/grub.cfg" ] && [ ! -f "$ESP/EFI/ubuntu/grub.cfg.pre-hook" ]; then
  cp -p "$ESP/EFI/ubuntu/grub.cfg" "$ESP/EFI/ubuntu/grub.cfg.pre-hook"
  say "backup: $ESP/EFI/ubuntu/grub.cfg.pre-hook"
fi

say "rendering now"
"$HOOK_INSTALL" "$(uname -r)"
sync

stub="$ESP/EFI/ubuntu/grub.cfg"
uuid="$(findmnt -no UUID /)"
if [ ! -f "$stub" ]; then
  echo "ERROR: stub missing after render: $stub" >&2
  exit 1
fi
if ! grep -q "$uuid" "$stub"; then
  echo "ERROR: stub does not carry root UUID $uuid" >&2
  exit 1
fi
say "PASS: $stub carries root UUID $uuid ($(wc -c < "$stub") bytes)"

if [ -f "$STORE/esp_validate.py" ]; then
  say "validating the published stub"
  py="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
  if [ -n "$py" ]; then
    if "$py" "$STORE/esp_validate.py" "$stub" --state /var/lib/p8-esp-stub/validate-state.json --force; then
      say "PASS: validator approved the published stub"
    else
      echo "ERROR: validator rejected the published stub - see $LOG" >&2
      exit 1
    fi
  else
    say "WARN: no python3, skipped validation"
  fi
fi

say "log: $LOG"
say ""
say "Next: bash 01_verify.sh"
