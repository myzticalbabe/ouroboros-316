#!/usr/bin/env python3
"""_board.py — cross-lane task board CLI (wraps LaneMessageBoard).

Usage:
    python C:/Users/clint/_board.py claim <lane> [limit] [agent]
    python C:/Users/clint/_board.py done <board_id> "<evidence>"
    python C:/Users/clint/_board.py block <board_id> "<blocker>"
    python C:/Users/clint/_board.py stats [lane]
    python C:/Users/clint/_board.py tasks [lane] [since_id]
    python C:/Users/clint/_board.py announce <text>
    python C:/Users/clint/_board.py max
    python C:/Users/clint/_board.py store
"""
import argparse
import json
import os
import sys

# Ensure azazael src is importable
AZAZAEL = r"C:\Azazael\azazael"
if AZAZAEL not in sys.path:
    sys.path.insert(0, AZAZAEL)
if os.path.join(AZAZAEL, "src") not in sys.path:
    sys.path.insert(0, os.path.join(AZAZAEL, "src"))

from CORE.LaneMessageBoard import LaneMessageBoard  # noqa: E402

STORE = r"C:\Users\clint\.azazael\telemetry_store.db"


def get_board(lane="opencode"):
    return LaneMessageBoard(lane=lane)


def cmd_claim(args):
    lane = args.lane
    limit = int(args.limit) if args.limit else 10
    agent = args.agent or lane
    b = get_board(lane)
    tasks = b.claim_tasks(lane, limit=limit, agent=agent)
    if not tasks:
        print("NO OPEN TASKS")
        return 0
    for t in tasks:
        bid = t.get("board_id")
        tid = t.get("task_id")
        action = t.get("action", "")
        detail = str(t.get("detail", ""))[:200]
        print(f"Board-{bid} | task_id={tid} | {action} | {detail}")
    return 0


def cmd_done(args):
    bid = int(args.board_id)
    note = args.note or ""
    b = get_board()
    ok = b.complete_task(bid, state="done", note=note)
    if ok:
        print(f"retired Board-{bid} as done")
    else:
        print(f"FAILED to retire Board-{bid} (not claimed?)")
        return 1
    return 0


def cmd_block(args):
    bid = int(args.board_id)
    note = args.note or ""
    b = get_board()
    ok = b.complete_task(bid, state="blocked", note=note)
    if ok:
        print(f"retired Board-{bid} as blocked")
    else:
        print(f"FAILED to retire Board-{bid} (not claimed?)")
        return 1
    return 0


def cmd_stats(args):
    lane = args.lane
    b = get_board(lane or "opencode")
    if lane:
        print(lane, b.task_stats(lane))
    else:
        for ln in ("opencode", "kilo", "freebuff", "crush", "agy"):
            print(ln, b.task_stats(ln))
    return 0


def cmd_tasks(args):
    lane = args.lane
    since = int(args.since) if args.since else None
    b = get_board(lane or "opencode")
    if lane:
        tasks = b.poll_tasks(lane, since_id=since)
    else:
        tasks = b.poll_tasks("opencode", since_id=since)
    for t in tasks:
        print(f"Board-{t.get('board_id')} | {t.get('task_id')} | {t.get('action')} | {str(t.get('detail',''))[:120]}")
    print(f"total: {len(tasks)}")
    return 0


def cmd_announce(args):
    text = " ".join(args.text)
    b = get_board()
    rid = b.post_announcement(text)
    print(f"announced Board-{rid}")
    # read back
    return 0


def cmd_max(args):
    b = get_board()
    mid = b.max_id()
    print(f"max_id: {mid}")
    return 0


def cmd_store(args):
    import sqlite3
    print(f"store: {STORE}")
    print(f"exists: {os.path.exists(STORE)}")
    if os.path.exists(STORE):
        con = sqlite3.connect(STORE, timeout=5)
        print(f"size: {os.path.getsize(STORE)}")
        cnt = con.execute("SELECT COUNT(*) FROM memorybus_queue").fetchone()[0]
        print(f"rows: {cnt}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Cross-lane task board CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_claim = sub.add_parser("claim")
    p_claim.add_argument("lane")
    p_claim.add_argument("limit", nargs="?")
    p_claim.add_argument("agent", nargs="?")
    p_claim.set_defaults(func=cmd_claim)

    p_done = sub.add_parser("done")
    p_done.add_argument("board_id")
    p_done.add_argument("note", nargs="?")
    p_done.set_defaults(func=cmd_done)

    p_block = sub.add_parser("block")
    p_block.add_argument("board_id")
    p_block.add_argument("note", nargs="?")
    p_block.set_defaults(func=cmd_block)

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("lane", nargs="?")
    p_stats.set_defaults(func=cmd_stats)

    p_tasks = sub.add_parser("tasks")
    p_tasks.add_argument("lane", nargs="?")
    p_tasks.add_argument("since", nargs="?")
    p_tasks.set_defaults(func=cmd_tasks)

    p_ann = sub.add_parser("announce")
    p_ann.add_argument("text", nargs="+")
    p_ann.set_defaults(func=cmd_announce)

    p_max = sub.add_parser("max")
    p_max.set_defaults(func=cmd_max)

    p_store = sub.add_parser("store")
    p_store.set_defaults(func=cmd_store)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
