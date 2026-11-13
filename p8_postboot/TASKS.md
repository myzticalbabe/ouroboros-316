# P8 post-reboot task queue — 2026-11-13

Purpose: make the Ubuntu boot on **Disk0 partition 8** survive a kernel upgrade.
Everything here needs Ubuntu running, because Windows cannot write P8 while P8
is the boot disk (`wsl --mount` returns `ERROR_NOT_FOUND`). Do them in order;
each task states its acceptance command and the line that means it passed.

Facts these tasks are built on, all measured from Windows on 2026-11-13:

| item | value | how it was measured |
| --- | --- | --- |
| root filesystem | P8, ext4, 100,805,902,336 bytes, offset 916,173,357,056 | `Get-Partition -DiskNumber 0 -PartitionNumber 8` |
| root UUID | `58e46179-d777-4203-a807-8794a3fb2351` | superblock at P8+1024, `s_uuid` = `58 E4 61 79 D7 77 42 03 A8 07 87 94 A3 FB 23 51`; corroborated by the root= string on P8: `root=UUID=58e46179-d777-4203-a807-8794a3fb2351` |
| ESP | P1, 272,629,760 bytes, PARTUUID `80ce903d-fccd-4004-8f95-f4eb447e5465` | `Get-Partition`, `blkid` |
| Windows volume | C:, P3, PARTUUID `7a713f0a-e80a-4554-8734-590332358b20` | `Get-Partition` |
| ESP contents | `shimx64.efi` 966,768 · `grubx64.efi` 2,828,168 · `mmx64.efi` 856,280 · `grub.cfg` 3,494 (= v4 stub) | `dir U:\EFI\ubuntu` |
| v4 stub SHA256 | `7a31967e3dc6ff71c7ec7e2c58a0d41ebd0a00671b2de07d6eb1d2b905094500` | re-read off the ESP and re-validated |
| firmware boot | `bootsequence {0f7b2723-df40-11f1-8403-806e6f6e6963}` → `\EFI\ubuntu\shimx64.efi` | `bcdedit /enum {fwbootmgr}` |

---

## T0 — get these files onto P8

The scripts live on C: at `C:\Users\clint\p8_postboot\`. Ubuntu reads NTFS, and
read-only is enough — nothing here writes back to C:.

```bash
sudo mkdir -p /mnt/win
sudo mount -t ntfs3 -o ro /dev/nvme0n1p3 /mnt/win \
  || sudo mount -t ntfs-3g -o ro /dev/nvme0n1p3 /mnt/win
ls -l /mnt/win/Users/clint/p8_postboot/
```

Acceptance: the listing shows `00_install_hook.sh`, `01_verify.sh`,
`02_rollback.sh`, `grub.cfg.tmpl`, `test_hook_offline.py`.

If NTFS refuses (Windows Fast Startup held the volume), copy the folder to a USB
stick from Windows instead, or mount the ESP and read from `/dev/nvme0n1p1` after
placing the files there by hand — the scripts only need to be *readable*.

Work on a copy so you do not need C: mounted for the whole session:

```bash
cp -r /mnt/win/Users/clint/p8_postboot ~/p8_postboot
cd ~/p8_postboot
```

---

## T1 — confirm the machine is the one these scripts describe

```bash
lsblk -o NAME,SIZE,FSTYPE,PARTUUID,MOUNTPOINTS
findmnt -no SOURCE,UUID /
cat /etc/hostname
```

Acceptance, all three:

1. `findmnt -no UUID /` prints `58e46179-d777-4203-a807-8794a3fb2351`
2. the ESP (`nvme0n1p1`) shows `vfat` and PARTUUID `80ce903d-fccd-4004-8f95-f4eb447e5465`
3. `mountpoint -q /boot/efi` exits 0

If the root UUID differs, stop: the disk was re-created and `EXPECT_UUID` in
`01_verify.sh` must be updated before anything else runs.

---

## T2 — install the kernel hook

```bash
sudo bash 00_install_hook.sh
```

Acceptance: the last three lines are

```
hook installed: /etc/kernel/postinst.d/zzz-p8-esp-stub
hook installed: /etc/kernel/postrm.d/zzz-p8-esp-stub
PASS: /boot/efi/EFI/ubuntu/grub.cfg carries root UUID 58e46179-d777-4203-a807-8794a3fb2351
```

Back up what the ESP held before this ran, so the change is reversible:

```bash
sudo cp -p /boot/efi/EFI/ubuntu/grub.cfg ~/grub.cfg.after-hook
sudo cp -p /boot/efi/EFI/ubuntu/grub.cfg.pre-hook ~/grub.cfg.before-hook
```

---

## T3 — verify, as a gate rather than a read-through

```bash
sudo bash 01_verify.sh; echo "EXIT:$?"
```

Acceptance: `EXIT:0` and a final line `0 failed`. The checks that matter most:

- `PASS stub references live UUID …` — a stale UUID is the exact failure that
  produced the Windows-only menu
- `PASS initrd paired for <ver>` for every kernel
- `PASS /boot/grub/grub.cfg mentions <newest ver>`
- `PASS hook executable: /etc/kernel/postinst.d/zzz-p8-esp-stub`
- `PASS firmware lists an ubuntu entry`

Any `FAIL` prints its reason on the same line; fix that before T5.

The same gate runs on the stub alone, and remembers what it approved:

```bash
python3 /etc/p8-esp-stub/esp_validate.py /boot/efi/EFI/ubuntu/grub.cfg \
  --state /var/lib/p8-esp-stub/validate-state.json --force
```

Exit codes: `0` valid (or unchanged since the last approval), `1` the stub
changed and is structurally broken, `2` it could not be checked — which is not
a pass. Without `--force` an unchanged file prints `UNCHANGED sha256=… approved
<timestamp>` and costs nothing.

---

## T4 — prove the hook fires on a real kernel change

A hook nobody has seen run is a hope. Force the trigger without touching the
running kernel:

```bash
# 1. capture the current stub
sudo cp -p /boot/efi/EFI/ubuntu/grub.cfg /tmp/stub.before

# 2. make the stub deliberately wrong, as a stale upgrade would
sudo sed -i 's/58e46179-d777-4203-a807-8794a3fb2351/00000000-0000-0000-0000-000000000000/' \
  /boot/efi/EFI/ubuntu/grub.cfg

# 3. run the hook the way a kernel install does
sudo /etc/kernel/postinst.d/zzz-p8-esp-stub "$(uname -r)"

# 4. it must have put the real UUID back
grep -c 58e46179-d777-4203-a807-8794a3fb2351 /boot/efi/EFI/ubuntu/grub.cfg
tail -n 3 /var/log/p8-esp-stub.log
```

Acceptance: the `grep -c` prints ≥ 2, and the log's last line is
`OK: stub re-rendered for 58e46179-…`. A log line `OK: stub already current for …`
on step 3 followed by a still-zero UUID at step 4 means `sed -i` rewrote the file
but the hook compared against a cache — re-check with `cmp` instead of trusting it.

Restore the captured stub if anything looks off:

```bash
sudo cp -p /tmp/stub.before /boot/efi/EFI/ubuntu/grub.cfg
```

---

## T4b — make the ESP check run on every change

The hook validates its own output (T4's step 3 exercises exactly that), but the
ESP also changes when something other than a kernel install writes it. Two ways
to cover that, pick by where you are:

**On P8, as a poller** — validates only when the bytes differ from the last
approval, so it stays quiet until something actually writes:

```bash
sudo python3 /etc/p8-esp-stub/esp_validate.py /boot/efi/EFI/ubuntu/grub.cfg \
  --state /var/lib/p8-esp-stub/validate-state.json --watch 300
```

Acceptance: first line is `watching … every 300s`, and no output appears until
the file changes. Then, in a second shell, prove it fires:

```bash
echo "# touch" | sudo tee -a /boot/efi/EFI/ubuntu/grub.cfg   # a legal no-op edit
```

Acceptance: within one poll the watcher prints `CHANGED … (content changed)`
followed by `VALID` and exit 0. A byte-level change with no output means the
state file is stale — re-run with `--force`.

**On Windows, before booting back** — `C:\Users\clint\esp_check.ps1` mounts the
ESP, validates, and unmounts, so nothing stays mapped:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\clint\esp_check.ps1
powershell -ExecutionPolicy Bypass -File C:\Users\clint\esp_check.ps1 -Watch 300
```

Acceptance: `VALID U:\EFI\ubuntu\grub.cfg <n> bytes` then `esp_check exit=0`;
a second run prints `UNCHANGED … approved <timestamp>` and `exit=0`. It exits 2
rather than guessing when it is not elevated or the ESP is not where expected.

Measured 2026-11-13 against the live ESP: run 1 `CHANGED … (never checked)` +
`VALID 3494 bytes` + `exit=0`; run 2 `UNCHANGED … approved 2026-11-13T04:28:12-0500`
+ `exit=0`.

## T5 — hostname survives reboots

A kernel upgrade does not touch the hostname, but a hostname that lives only in
memory does not survive a power cycle, and a missing `/etc/hosts` entry makes
`sudo` stall for seconds on every command.

```bash
hostnamectl status | head -n 3
cat /etc/hostname
grep "$(cat /etc/hostname)" /etc/hosts
```

Acceptance: `hostnamectl --static` equals `/etc/hostname`, and `/etc/hosts`
contains a line starting with that name (normally `127.0.1.1 <name>`).

To set it and make it stick:

```bash
sudo hostnamectl set-hostname p8
echo "127.0.1.1 p8" | sudo tee -a /etc/hosts
# then, per the machine's role, also fix the old name if /etc/hosts still has it
```

Acceptance after a reboot: `hostnamectl --static` still prints `p8`.

---

## T6 — clean the bogus firmware entry

`{b7173bfa-dbd1-11f0-8e4f-aa2261939d2d}` is described as
`UEFI: HTTP IPv4 Network Card` but its path is `\EFI\ubuntu\shimx64.efi` — a
mis-typed leftover. It is not in `bootsequence`, so it is harmless today, but it
is a trap for anyone reading the firmware menu.

```bash
sudo apt install -y efibootmgr
efibootmgr -v
sudo efibootmgr -b b7173bfa -B        # note: no braces, no dashes after the first group
efibootmgr -v | grep -i ubuntu
```

Acceptance: exactly one `ubuntu` line remains, and it points at
`\EFI\ubuntu\shimx64.efi` with `Boot####` present in `BootOrder`.
Do not delete `{0f7b2723-df40-11f1-8403-806e6f6e6963}`.

---

## T7 — record the outcome

```bash
sudo bash 01_verify.sh > ~/p8_verify_$(date +%F).txt 2>&1; echo "EXIT:$?"
sha256sum /boot/efi/EFI/ubuntu/grub.cfg
tail -n 20 /var/log/p8-esp-stub.log
```

Acceptance: the file exists, ends `0 failed`, and the sha256 is recorded next to
the date. If the sha256 differs from
`7a31967e3dc6ff71c7ec7e2c58a0d41ebd0a00671b2de07d6eb1d2b905094500`, that is
expected — the hook re-rendered it through the template, which carries a comment
header that differs from the hand-installed v4. Confirm by content instead:

```bash
grep -c '^menuentry' /boot/efi/EFI/ubuntu/grub.cfg   # expect 6
grep -n '^configfile' /boot/efi/EFI/ubuntu/grub.cfg  # expect NO output: a top-level
                                                     # configfile replaces the menu and
                                                     # hides every entry below it (v4's bug)
grep -c "58e46179-d777-4203-a807-8794a3fb2351" /boot/efi/EFI/ubuntu/grub.cfg  # expect >= 2
```

---

## Rollback

```bash
sudo bash 02_rollback.sh
```

Removes both hooks and `/etc/p8-esp-stub`, and restores
`/boot/efi/EFI/ubuntu/grub.cfg.pre-hook` if it exists. After this the ESP stub no
longer follows kernel upgrades — that is the pre-hook behaviour, not a fix.

---

## Offline check you can run before touching P8

`test_hook_offline.py` extracts the hook body out of `00_install_hook.sh`, points
it at a temp ESP with a fake `findmnt`, and drives six paths. Run it on Windows
or on P8; it needs only Python and `sh`.

```bash
python3 test_hook_offline.py; echo "EXIT:$?"
```

Measured 2026-11-13 on Windows: `18 passed, 0 failed`, `EXIT:0`. The five paths
it covers, each asserted to exit 0 so a broken hook can never wedge `apt`:

| path | what is asserted |
| --- | --- |
| success | stub rendered with live UUID, 4 menuentries, Windows entry kept, `OK:` logged |
| template absent | stub byte-identical, `SKIP:` logged, exit 0 |
| template without UUID | stub byte-identical, `ERROR: rendered stub does not contain root UUID`, exit 0 |
| root UUID unreadable | stub byte-identical, `ERROR: cannot read root UUID`, exit 0 |
| structurally broken render | validator rejects it, `CRITICAL: validator rejected stub`, `OK: rolled back to previous stub`, stub byte-identical, exit 0 |
| ESP/EFI/ubuntu absent | `SKIP:` logged, exit 0 |

Measured 2026-11-13 on Windows: `22 passed, 0 failed`, `EXIT:0`.

---

## Why the hook, and what it does not cover

`grub-install` and `update-grub` rewrite `/boot/grub/grub.cfg` and can rewrite
`/boot/efi/EFI/ubuntu/*`. The ESP stub is the only file the firmware executes, and
on this machine it has already been hand-edited three times (840 → 1,596 → 3,494
bytes). Without a hook, the next `apt upgrade` either leaves a stale UUID in the
stub or replaces it with Ubuntu's stock stub — which is the configuration that
gave a Windows-only menu in the first place.

Not covered, by design:

- **The kernel must actually boot.** No config can catch a kernel that panics; the
  `Ubuntu (recovery console)` entry is the way back in when that happens.
- **Secure Boot state.** If Secure Boot is ever re-enabled with a different key
  set, `shimx64.efi` will refuse `grubx64.efi` and print a security violation —
  that is a firmware/key problem, not a stub problem.
- **Firmware NVRAM.** `bootsequence` is one-shot and the `Boot####` entry lives in
  NVRAM; a CMOS clear or BIOS update removes it, and T6's `efibootmgr` check is
  the way to notice.
