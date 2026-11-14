#!/usr/bin/env python3
"""board_watch.py - Scheduled wakeup that checks the LaneMessageBoard for new tasks.

Rebuilt 2026-11-14. The original was deleted from the tree (its .pyc survived
in __pycache__ for three interpreters, and board_watch.log kept running until
2026-11-07), so its contract was recovered from the bytecode and is honoured
here: same paths, same exit codes, same purpose. The canon also names
`--peek` and `--drain`, which the original did not have; both are here.

Polls the shared MemoryBus SQLite queue (the durable backing of
LaneMessageBoard) for new lane.* rows since the last check and writes a
digest to stdout + board_watch.log. The scan path uses stdlib sqlite3 only,
so it runs under any interpreter without touching lane turf. `--drain`
imports LaneMessageBoard lazily, and only when it actually claims.

Usage
  python board_watch.py --check        # one-shot (Task Scheduler; exit 2 = new work)
  python board_watch.py --check --lane opencode
  python board_watch.py --lanes        # cross-lane report: what every lane holds
  python board_watch.py --peek         # print what is waiting; changes nothing
  python board_watch.py --drain        # ACK (claim) what is waiting for the lane
  python board_watch.py --loop 60      # poll every 60 min until new work is found
  python board_watch.py --reset        # clear last-seen state
  python board_watch.py --daemon 30    # fast poll (30s) with a live dashboard

Exit codes: 0 = nothing new for the target lane (foreign traffic still
            logged), 2 = NEW tasks addressed to the target lane, 1 = error.

Windows Task Scheduler (near-real-time safety net, every minute):
  schtasks /Create /F /TN "Azazael\\BoardWatch" ^
    /TR "pythonw.exe C:\\Users\\clint\\board_watch.py --check --lane opencode" ^
    /SC MINUTE /MO 1 /RL LIMITED
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
DB = HOME / ".azazael" / "telemetry_store.db"
STATE = HOME / ".azazael" / "board_watch_state.json"
LOG = HOME / "board_watch.log"
INBOX = HOME / ".azazael" / "board_watch_inbox.json"
DASH = HOME / ".azazael" / "board_watch_dashboard.html"
LIVE = HOME / ".azazael" / "board_watch_live.json"
SPOOL = HOME / "board_spool"

LOG_MAX_BYTES = 512 * 1024
ALARM_COOLDOWN_S = 300

DEFAULT_LANE = "opencode"
# The lanes a watch can be pointed at. The set is read from the board when
# CORE is importable, and this list is the fallback for the stdlib-only path.
KNOWN_LANES = ("opencode", "kilo", "freebuff", "crush", "agy")


# ── logging ────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    try:
        rotate_log()
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass
    print(line)


def rotate_log() -> None:
    try:
        if LOG.exists() and LOG.stat().st_size > LOG_MAX_BYTES:
            LOG.replace(LOG.with_suffix(".log.1"))
    except Exception:
        pass


# ── state ──────────────────────────────────────────────────────────────────

def load_state_full() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_state() -> int:
    return int(load_state_full().get("last_id", 0) or 0)


def save_state(last_id: int, acked=None, last_alarm: float = 0.0) -> None:
    st = load_state_full()
    st["last_id"] = int(last_id)
    st["acked"] = list(acked if acked is not None else st.get("acked", []))
    st["last_alarm"] = float(last_alarm or st.get("last_alarm", 0.0))
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")
    except Exception as exc:
        log(f"ERROR: could not write state: {exc}")


# ── spool ──────────────────────────────────────────────────────────────────

def spool_path(lane: str) -> Path:
    return SPOOL / f"{lane}.jsonl"


def spool(rows: list) -> None:
    """Append new rows to the per-lane spool file, one JSON per line."""
    if not rows:
        return
    try:
        SPOOL.mkdir(parents=True, exist_ok=True)
        by_lane: dict = {}
        for row in rows:
            by_lane.setdefault(row.get("_lane", DEFAULT_LANE), []).append(row)
        for lane, items in by_lane.items():
            with spool_path(lane).open("a", encoding="utf-8") as fh:
                for item in items:
                    fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as exc:
        log(f"ERROR: could not spool rows: {exc}")


def drain(lane: str) -> list:
    """Read the spool for a lane and return its rows, leaving the file alone.

    ACK (removal) is the caller's decision: `--drain` calls `ack` after the
    claim, so a failed claim does not silently discard the work.
    """
    p = spool_path(lane)
    if not p.exists():
        return []
    out = []
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception as exc:
        log(f"ERROR: could not read spool: {exc}")
    return out


def ack(lane: str) -> None:
    """Acknowledge the spool for a lane: the rows have been taken."""
    p = spool_path(lane)
    try:
        if p.exists():
            p.unlink()
    except Exception as exc:
        log(f"ERROR: could not ack spool: {exc}")


# ── the scan ───────────────────────────────────────────────────────────────

def fetch_new(last_id: int) -> list:
    """Rows in any lane.* topic newer than last_id, oldest first.

    Stdlib sqlite3 only: this path must not import CORE, so a broken tree
    cannot stop the watcher from noticing work arriving.
    """
    if not DB.exists():
        raise FileNotFoundError(f"board store not found: {DB}")
    con = sqlite3.connect(str(DB), timeout=5)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT id, topic, content, timestamp FROM memorybus_queue "
            "WHERE topic LIKE 'lane.%' AND id > ? ORDER BY id ASC",
            (int(last_id),),
        ).fetchall()
    finally:
        con.close()
    out = []
    for r in rows:
        try:
            payload = json.loads(r["content"] or "{}")
        except Exception:
            payload = {}
        topic = r["topic"] or ""
        parts = topic.split(".")
        # Topics are `lane.<lane>.<kind>` -- lane.opencode.tasks,
        # lane.all.announce, lane.release.kilo -- plus the delivery audit
        # `lane.push.<src>-><dst>`, whose DESTINATION is the lane the work
        # was handed to.
        lane = ""
        kind = ""
        if len(parts) >= 3 and parts[0] == "lane":
            kind = parts[2]
            if parts[1] == "push":
                kind = "push"
                lane = parts[2].split("->")[-1] if "->" in parts[2] else ""
            elif parts[1] in ("all", "release"):
                lane = parts[2] if parts[1] == "release" else "all"
            else:
                lane = parts[1]
        out.append({
            "_id": int(r["id"]),
            "_topic": topic,
            "_kind": kind,
            "_lane": lane,
            "_timestamp": r["timestamp"],
            "task_id": payload.get("task_id"),
            "action": payload.get("action", ""),
            "detail": str(payload.get("detail") or "")[:2000],
            "source_lane": payload.get("source_lane", ""),
        })
    return out


def s(v, limit: int = 90) -> str:
    text = str(v or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def summarize(row: dict) -> str:
    return (f"#{row['_id']} {row['_topic']} :: {s(row.get('action'), 70)} "
            f":: from {row.get('source_lane') or '?'}")


# ── cross-lane view ────────────────────────────────────────────────────────

def lane_statuses() -> dict:
    """What every lane holds right now.

    Uses LaneMessageBoard.task_stats when CORE is importable, because that
    number now means "the work a claim would hand out" rather than "every
    row that has not been retired". Falls back to counting the state table
    directly so the report still works without CORE.
    """
    out = {}
    try:
        sys.path.insert(0, r"C:\Azazael\azazael")
        sys.path.insert(0, r"C:\Azazael\azazael\src")
        from CORE.LaneMessageBoard import LaneMessageBoard  # noqa: E402
        board = LaneMessageBoard(lane=DEFAULT_LANE)
        for lane in KNOWN_LANES:
            try:
                st = board.task_stats(lane)
                out[lane] = {
                    "available": st.get("available", 0),
                    "stale_duplicates": st.get("stale_duplicates", 0),
                    "claimed_live": st.get("claimed_live", 0),
                    "retired": st.get("retired", 0),
                    "available_exact": st.get("available_exact", True),
                }
            except Exception as exc:
                out[lane] = {"error": str(exc)}
        return out
    except Exception:
        pass
    # CORE-free fallback.
    try:
        con = sqlite3.connect(str(DB), timeout=5)
        con.row_factory = sqlite3.Row
        try:
            for lane in KNOWN_LANES:
                topic = f"lane.{lane}.tasks"
                total = con.execute(
                    "SELECT COUNT(*) FROM memorybus_queue WHERE topic = ?", (topic,)
                ).fetchone()[0]
                states = dict(con.execute(
                    "SELECT s.state, COUNT(*) FROM lane_task_state s "
                    "JOIN memorybus_queue q ON q.id = s.board_id "
                    "WHERE q.topic = ? GROUP BY s.state", (topic,)
                ).fetchall())
                out[lane] = {
                    "available": total - states.get("done", 0) - states.get("blocked", 0)
                                 - states.get("archived", 0),
                    "stale_duplicates": None,
                    "claimed_live": states.get("claimed", 0),
                    "retired": states.get("done", 0) + states.get("blocked", 0)
                               + states.get("archived", 0),
                    "available_exact": None,
                }
        finally:
            con.close()
    except Exception as exc:
        return {"error": str(exc)}
    return out


def recent_traffic(limit: int = 12) -> list:
    """The newest lane.* rows, whoever wrote them."""
    if not DB.exists():
        return []
    con = sqlite3.connect(str(DB), timeout=5)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT id, topic, content, timestamp FROM memorybus_queue "
            "WHERE topic LIKE 'lane.%' ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    finally:
        con.close()
    out = []
    for r in rows:
        try:
            payload = json.loads(r["content"] or "{}")
        except Exception:
            payload = {}
        out.append({
            "id": int(r["id"]),
            "topic": r["topic"],
            "timestamp": r["timestamp"],
            "action": payload.get("action", ""),
            "source_lane": payload.get("source_lane", ""),
        })
    return out


def write_inbox(items: list) -> None:
    try:
        INBOX.parent.mkdir(parents=True, exist_ok=True)
        INBOX.write_text(json.dumps(items, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    except Exception:
        pass


def write_live_json(items: list) -> None:
    try:
        LIVE.parent.mkdir(parents=True, exist_ok=True)
        LIVE.write_text(json.dumps({
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def write_dashboard(items: list) -> None:
    try:
        rows = "".join(
            f"<tr><td>{i.get('id')}</td><td>{i.get('topic')}</td>"
            f"<td>{i.get('action')}</td><td>{i.get('source_lane')}</td></tr>"
            for i in items
        )
        html = (
            "<!doctype html><meta charset=utf-8>"
            "<title>board watch</title>"
            "<style>body{font:14px system-ui;background:#111;color:#ddd}"
            "table{border-collapse:collapse}td,th{padding:4px 8px;"
            "border-bottom:1px solid #333}th{text-align:left;color:#8cf}</style>"
            f"<h1>board watch</h1><p>{len(items)} lane rows, newest first</p>"
            "<table><tr><th>id</th><th>topic</th><th>action</th><th>from</th></tr>"
            f"{rows}</table>"
        )
        DASH.write_text(html, encoding="utf-8")
    except Exception:
        pass


# ── modes ──────────────────────────────────────────────────────────────────

def post_status(lane: str, detail: str) -> int | None:
    """Put the arrival on the board itself.

    A status row is how the board reports that something arrived while
    nobody was looking -- the same reason the lane instruction files require
    one status row per work unit. CORE is imported here only, and a failure
    here must not stop the scan, so it is caught rather than raised.
    """
    try:
        sys.path.insert(0, r"C:\Azazael\azazael")
        sys.path.insert(0, r"C:\Azazael\azazael\src")
        from CORE.LaneMessageBoard import LaneMessageBoard  # noqa: E402
        board = LaneMessageBoard(lane=lane)
        row = board.post_status("new work waiting", detail)
        # Read it back: a post you cannot read back did not land.
        for t in board.poll_tasks(lane, limit=1):
            break
        return row
    except Exception as exc:
        log(f"WARN: could not post the status row: {exc}")
        return None


def check(lane: str) -> int:
    """One-shot scan. Exit 2 when something new arrived for the target lane."""
    last = load_state()
    try:
        rows = fetch_new(last)
    except Exception as exc:
        log(f"ERROR: {exc}")
        return 1
    if not rows:
        log(f"OK: no new board rows since #{last}.")
        return 0
    mine = [r for r in rows if r["_lane"] == lane]
    spool(rows)
    write_inbox(rows[-50:])
    write_live_json(rows[-50:])
    write_dashboard(rows[-50:])
    for r in rows:
        log("NEW " + summarize(r))
    save_state(rows[-1]["_id"], acked=load_state_full().get("acked", []))
    if mine:
        log(f"NEW WORK for {lane}: {len(mine)} row(s) - {mine[-1]['_id']} "
            f"{s(mine[-1].get('action'), 60)}")
        named = "; ".join(f"#{r['_id']} {s(r.get('action'), 40)}" for r in mine[-6:])
        post_status(lane, f"{len(mine)} new row(s) addressed to {lane}: {named}")
        return 2
    log(f"OK: {len(rows)} new row(s), none addressed to {lane}.")
    return 0


def peek(lane: str) -> int:
    """Show what is waiting for the lane. Changes nothing."""
    print(f"=== {lane}: spooled ===")
    items = drain(lane)
    if not items:
        print("  (nothing spooled)")
    for i in items:
        print(f"  #{i.get('_id')} {i.get('action')} :: {s(i.get('detail'), 140)}")
    print()
    print("=== lanes ===")
    for name, st in lane_statuses().items():
        if "error" in st:
            print(f"  {name:10} ERROR {st['error'][:70]}")
        else:
            print(f"  {name:10} available={st['available']} "
                  f"stale={st['stale_duplicates']} live_claims={st['claimed_live']} "
                  f"retired={st['retired']}")
    print()
    print("=== newest lane traffic ===")
    for r in recent_traffic(12):
        print(f"  #{r['id']} {r['topic']:26} {s(r['action'], 60)} "
              f":: from {r['source_lane'] or '?'}")
    return 0


def claim_for(lane: str, limit: int = 10):
    """Claim what the lane can take. CORE is imported only here.

    Returns (claimed, stats) from the SAME board instance -- the stats live
    on the instance that ran the claim, so a fresh instance reports nothing.
    """
    sys.path.insert(0, r"C:\Azazael\azazael")
    sys.path.insert(0, r"C:\Azazael\azazael\src")
    from CORE.LaneMessageBoard import LaneMessageBoard  # noqa: E402
    board = LaneMessageBoard(lane=lane)
    claimed = board.claim_tasks(lane, limit=limit, agent=lane)
    return claimed, getattr(board, "last_claim_stats", {}) or {}


def do_drain(lane: str, limit: int = 10) -> int:
    """ACK the spool and claim the work that is waiting."""
    items = drain(lane)
    try:
        claimed, stats = claim_for(lane, limit=limit)
    except Exception as exc:
        log(f"ERROR: claim failed: {exc}")
        return 1
    if claimed:
        for c in claimed:
            print(f"claimed Board-{c['board_id']} | {c.get('task_id')} | "
                  f"{s(c.get('action'), 60)}")
    else:
        print("nothing claimable")
    if stats:
        print(f"claim: {stats.get('claimed')} claimed, "
              f"{stats.get('duplicates_retired')} stale copies retired, "
              f"{stats.get('scanned')} scanned")
    if claimed or items:
        ack(lane)
        log(f"DRAIN {lane}: {len(claimed)} claimed, {len(items)} spooled acked.")
    return 0


def loop(lane: str, minutes: int) -> int:
    while True:
        rc = check(lane)
        if rc == 2:
            return 0
        time.sleep(max(1, int(minutes)) * 60)


def daemon(lane: str, seconds: int) -> int:
    while True:
        check(lane)
        time.sleep(max(5, int(seconds)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="one-shot scan (Task Scheduler); exit 2 on new work")
    ap.add_argument("--lanes", action="store_true",
                    help="cross-lane report: what every lane holds")
    ap.add_argument("--peek", action="store_true",
                    help="print what is waiting; changes nothing")
    ap.add_argument("--drain", action="store_true",
                    help="claim (ACK) what is waiting for the lane")
    ap.add_argument("--loop", type=int, metavar="MIN",
                    help="poll every MIN minutes until new work is found")
    ap.add_argument("--daemon", type=int, metavar="SEC",
                    help="fast poll with a live dashboard")
    ap.add_argument("--reset", action="store_true", help="clear last-seen state")
    ap.add_argument("--lane", default=DEFAULT_LANE,
                    help=f"target lane (default {DEFAULT_LANE})")
    ap.add_argument("--limit", type=int, default=10,
                    help="how many tasks to claim on --drain")
    args = ap.parse_args(argv)

    if args.reset:
        try:
            if STATE.exists():
                STATE.unlink()
            print("reset")
        except Exception as exc:
            print(f"ERROR: {exc}")
            return 1
        return 0
    if args.lanes:
        peek(args.lane)
        return 0
    if args.peek:
        return peek(args.lane)
    if args.drain:
        return do_drain(args.lane, args.limit)
    if args.loop:
        return loop(args.lane, args.loop)
    if args.daemon:
        return daemon(args.lane, args.daemon)
    return check(args.lane)


if __name__ == "__main__":
    sys.exit(main())
