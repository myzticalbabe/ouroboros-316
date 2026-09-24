"""repaird: closed self-repair loop (watchdog). Detect -> diagnose -> act -> verify.

Scope (allowlist ONLY — everything else escalates to human):
  R1 stale sweep status   : last_error older than current progress  -> clear it
  R2 stale ledger lock    : evolve_log.jsonl.lock older than 10 min -> remove it
  R3 dead partials        : *.incomplete + 0-byte *.gguf under models/ -> delete
  R4 temp cruft           : %TEMP% older than 7 days -> delete (bounded)
  R5 integrity drift      : scripts differ from baseline -> REPORT ONLY
                            (never auto-fix code; escalate)
Interlocks (never violated):
  - If sweep_status.json state == running: NO server actions, NO layer
    relaunches (the sweep owns :8091 and its own lifecycle).
  - Never: git ops, weight-file deletes (nonzero *.gguf/*.safetensors/*.npy),
    ledger edits, anything outside edge0-intel (azazael/BCC off limits).
  - Every action logged; failures escalate, never retry-loop.

Usage:
  python scripts/repaird.py          # one pass, prints actions + escalations
  python scripts/repaird.py --report # dry run (lists what WOULD happen)
  python scripts/repaird.py --status # one-line health for monitors
Exit 0 clean-or-fixed, 1 escalations pending, 2 loop error.
"""
import json
import os
import sys
import time

BASE = r"C:\Users\clint\edge0-intel"
LOGF = os.path.join(BASE, "repaird.log")
STATF = os.path.join(BASE, "sweep_status.json")
LEDGER_LOCK = os.path.join(BASE, "evolve_log.jsonl.lock")
MODELS = os.path.join(BASE, "models")
ALLOW_AGE_TMP_DAYS = 7


def say(m, fh):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    fh.write(line + "\n")


def sweep_running():
    try:
        s = json.load(open(STATF, encoding="utf-8"))
        if s.get("state") != "running":
            return False
        import datetime
        up = datetime.datetime.fromisoformat(s.get("updated", "2000-01-01"))
        age = (datetime.datetime.now() - up).total_seconds()
        return age < 3600  # running + fresh heartbeat only
    except Exception:
        return False


def file_age_s(path):
    try:
        return time.time() - os.path.getmtime(path)
    except OSError:
        return -1.0


def main():
    report = "--report" in sys.argv
    fh = open(LOGF, "a", encoding="utf-8")
    actions, escalate = [], []
    say(f"repaird pass report={report}", fh)

    # R1: stale last_error (status merged dict keeps it forever).
    try:
        s = json.load(open(STATF, encoding="utf-8"))
        if s.get("last_error") and int(s.get("done", 0)) > 0:
            # Stale iff progress continued past the error: done>0 with a
            # last_result present means later steps succeeded.
            if s.get("last_result"):
                msg = f"R1 clear stale last_error ({s['last_error']})"
                if not report:
                    del s["last_error"]
                    json.dump(s, open(STATF, "w"), indent=1)
                actions.append(msg)
                say(("WOULD " if report else "") + msg, fh)
    except Exception as e:
        escalate.append(f"R1 status unreadable: {e}")

    # R2: stale ledger lock.
    age = file_age_s(LEDGER_LOCK)
    if age >= 0:
        if age > 600:
            msg = f"R2 remove stale ledger lock ({age/60:.0f}min old)"
            if not report:
                try:
                    os.remove(LEDGER_LOCK)
                except OSError as e:
                    escalate.append(f"R2 lock unremovable: {e}")
                    msg = ""
            if msg:
                actions.append(msg)
                say(("WOULD " if report else "") + msg, fh)

    # R3: dead partials (exact patterns only).
    if os.path.isdir(MODELS):
        for dirpath, _, files in os.walk(MODELS):
            for fn in files:
                p = os.path.join(dirpath, fn)
                try:
                    dead = (fn.endswith(".incomplete")
                            or (fn.endswith(".gguf") and os.path.getsize(p) == 0))
                except OSError:
                    continue
                if dead:
                    msg = f"R3 delete dead partial {os.path.relpath(p, BASE)}"
                    if not report:
                        try:
                            os.remove(p)
                        except OSError as e:
                            escalate.append(f"R3 {fn} undeletable: {e}")
                            continue
                    actions.append(msg)
                    say(("WOULD " if report else "") + msg, fh)

    # R4: temp cruft (bounded, old only).
    try:
        import tempfile
        tmp = tempfile.gettempdir()
        cutoff = time.time() - ALLOW_AGE_TMP_DAYS * 86400
        n = 0
        for dirpath, _, files in os.walk(tmp):
            for fn in files:
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getmtime(p) < cutoff:
                        if not report:
                            os.remove(p)
                        n += 1
                except OSError:
                    pass
            if n > 500:
                break
        if n:
            msg = f"R4 removed {n} temp files older than {ALLOW_AGE_TMP_DAYS}d"
            actions.append(msg)
            say(("WOULD " if report else "") + msg, fh)
    except Exception as e:
        escalate.append(f"R4 temp walk failed: {e}")

    # R5: integrity drift -> report only, always escalate.
    try:
        sys.path.insert(0, os.path.join(BASE, "scripts"))
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(BASE, "scripts", "integrity.py"),
             "check"], capture_output=True, text=True, timeout=120)
        if r.returncode == 1:
            escalate.append("R5 integrity DRIFT (code changes unrecorded) - "
                            "human reviews, never auto-fixed")
        elif r.returncode != 0:
            escalate.append("R5 integrity checker errored")
    except Exception as e:
        escalate.append(f"R5 checker failed: {e}")

    # Sweep interlock note (no server actions exist yet by design).
    if sweep_running():
        say("interlock: sweep active, server lifecycle untouched", fh)

    say(f"pass done: {len(actions)} actions, {len(escalate)} escalations", fh)
    for e in escalate:
        say(f"ESCALATE: {e}", fh)
    fh.close()
    return 1 if escalate else 0


def status_main():
    if os.path.exists(LOGF):
        with open(LOGF, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-3:]
        print("".join(lines), end="")
    else:
        print("repaird never ran")


if __name__ == "__main__":
    if "--status" in sys.argv:
        status_main()
    else:
        sys.exit(main())
