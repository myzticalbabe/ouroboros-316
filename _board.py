#!/usr/bin/env python3
"""_board.py — cross-lane task board CLI (wraps LaneMessageBoard).

Usage:
    python C:/Users/clint/_board.py claim <lane> [limit] [agent]
    python C:/Users/clint/_board.py done <board_id> "<evidence>"
    python C:/Users/clint/_board.py block <board_id> "<blocker>"
    python C:/Users/clint/_board.py stats [lane]
    python C:/Users/clint/_board.py tasks [lane] [since_id] [--all] [--claimed] [--limit N]
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
    # A claim also retires stale COPIES of work already done. That was
    # invisible, so a claim that retired 10 copies and found no work printed
    # exactly what a claim that found nothing at all printed -- and the
    # copies could sit in front of the real work indefinitely.
    stats = getattr(b, "last_claim_stats", None) or {}
    dups = stats.get("duplicates_retired")
    if dups is None:
        # The attribute exists but carries no claim stats: the backing
        # LaneMessageBoard does not publish them. That is DIFFERENT from "this
        # claim retired nothing", and a reader that cannot tell the two apart
        # is exactly the failure this line was written to prevent. An empty
        # dict default cannot express it; a missing key can.
        print("NOTE: this LaneMessageBoard publishes no claim stats "
              "(no 'duplicates_retired' key) -- a claim that retired copies "
              "is indistinguishable from one that found nothing")
    elif dups:
        print(f"retired {dups} stale duplicate row(s) during this claim; "
              f"scanned {stats.get('scanned')} of {stats.get('scan_limit')}")
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
    # The lane is part of the predicate: a lane may retire only work on its
    # own queue. Without it, one lane's `done` could retire another lane's
    # claimed row and that work would vanish -- never finished, only marked
    # finished. Pass the lane to act for another one.
    lane = getattr(args, "lane", None) or "opencode"
    b = get_board(lane)
    ok = b.complete_task(bid, state="done", note=note)
    if ok:
        print(f"retired Board-{bid} as done")
    else:
        print(f"FAILED to retire Board-{bid} (never claimed, not claimed by "
              f"{lane}, or already retired)")
        return 1
    return 0


def cmd_block(args):
    bid = int(args.board_id)
    note = args.note or ""
    lane = getattr(args, "lane", None) or "opencode"
    b = get_board(lane)
    ok = b.complete_task(bid, state="blocked", note=note)
    if ok:
        print(f"retired Board-{bid} as blocked")
    else:
        print(f"FAILED to retire Board-{bid} (never claimed, not claimed by "
              f"{lane}, or already retired)")
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
    # A lane typo used to reach LaneMessageBoard's constructor and surface as a
    # raw ValueError traceback, which reads as a broken tool rather than a bad
    # argument. Name the valid lanes and leave with 2, the same code argparse
    # uses for a usage error, so scripts can tell "you typed it wrong" apart
    # from "the board is broken" (1) and "this ran clean" (0).
    lane = args.lane or "opencode"
    valid = tuple(getattr(LaneMessageBoard, "VALID_LANES", ()))
    if valid and lane not in valid:
        print(f"unknown lane {lane!r}; valid lanes: {', '.join(valid)}")
        return 2
    since = None
    if args.since:
        try:
            since = int(args.since)
        except ValueError:
            print(f"since_id must be an integer row id, got {args.since!r}")
            return 2
    b = get_board(lane)
    # `--all` is the audit view (retired rows and live leases included);
    # `--claimed` widens the default view to rows another lane holds.
    want_all = bool(getattr(args, "all", False))
    want_claimed = bool(getattr(args, "claimed", False))
    # poll_tasks caps at 50 by default and the CLI never passed a limit, so the
    # documented audit view could only ever show the newest 50 rows: measured
    # against a lane holding 50 open + 475 retired, `tasks --all` printed 50 and
    # said "total: 50". An audit view that cannot reach the history is the same
    # defect class as the AttributeError that used to crash this function.
    # `--all` therefore means "no cap"; `--limit 0` is the explicit spelling and
    # a positive N is always honoured. poll_tasks slices `tasks[:limit]`, so 0
    # would return nothing -- the uncapped form has to be a large bound, not 0.
    uncapped = 10 ** 9
    explicit = getattr(args, "limit", None)
    if explicit is None:
        limit = uncapped if want_all else 50
    else:
        limit = uncapped if int(explicit) == 0 else int(explicit)
    tasks = b.poll_tasks(lane, since_id=since, limit=limit,
                         include_retired=want_all,
                         include_claimed=want_all or want_claimed)
    for t in tasks:
        # poll_tasks returns LaneTask dataclasses, NOT dicts. Calling .get()
        # on one raised AttributeError, so the documented reader for the
        # queue crashed on every call and the only way to see work was to
        # claim it blind. metadata is a dict by default but a legacy row
        # can carry `"metadata": null`, so it is guarded rather than assumed.
        meta = t.metadata if isinstance(t.metadata, dict) else {}
        row_id = meta.get("_row_id")
        board = f"Board-{row_id}" if row_id is not None else "Board-?"
        # detail is a string on modern rows and a dict on legacy ones.
        print(f"{board} | {t.task_id} | {t.action} | {str(t.detail or '')[:120]}")
    # HED-9: a count without its denominator cannot be audited, and the rows a
    # cap drops are always the oldest -- the ones an audit view exists for.
    # The denominator is proved by the poll itself (ask for one row past the
    # cap) rather than borrowed from `task_stats`: on 2026-11-14 a foreign
    # lane's in-flight edit to CORE/LaneMessageBoard.py left `_state_conn()`
    # returning None, so `task_stats` raised AttributeError and a reader that
    # depended on it reported the queue as unreadable while `poll_tasks` was
    # still handing out rows. A reader must not lose its own reading to a
    # counter it does not need.
    shown = len(tasks)
    if limit >= uncapped:
        print(f"total: {shown}")
    elif since is not None:
        print(f"total: {shown} (since {since})")
    else:
        probe = b.poll_tasks(lane, since_id=since, limit=limit + 1,
                             include_retired=want_all,
                             include_claimed=want_all or want_claimed)
        if len(probe) > limit:
            print(f"total: {shown} (capped at {limit}; more rows exist -- "
                  f"pass --limit 0 or --all for the rest)")
        else:
            print(f"total: {shown}")
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
    p_done.add_argument("lane", nargs="?",
                        help="the lane the row belongs to (default opencode); "
                             "a lane may retire only its own work")
    p_done.set_defaults(func=cmd_done)

    p_block = sub.add_parser("block")
    p_block.add_argument("board_id")
    p_block.add_argument("note", nargs="?")
    p_block.add_argument("lane", nargs="?",
                         help="the lane the row belongs to (default opencode); "
                              "a lane may retire only its own work")
    p_block.set_defaults(func=cmd_block)

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("lane", nargs="?")
    p_stats.set_defaults(func=cmd_stats)

    p_tasks = sub.add_parser("tasks")
    p_tasks.add_argument("lane", nargs="?")
    p_tasks.add_argument("since", nargs="?")
    p_tasks.add_argument("--all", action="store_true",
                         help="audit view: retired rows and live leases included")
    p_tasks.add_argument("--claimed", action="store_true",
                         help="also show rows another lane holds under a live lease")
    p_tasks.add_argument("--limit", type=int, default=None, metavar="N",
                         help="max rows (default 50; 0 = no cap; --all implies no cap)")
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
