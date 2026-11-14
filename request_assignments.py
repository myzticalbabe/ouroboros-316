#!/usr/bin/env python3
"""request_assignments.py - ask the other lanes to assign their open work to us.

The board is a delivery plane: work reaches a lane when that lane pushes it,
or when it is posted into that lane's queue. Nothing wakes a session when
work arrives, so the opencode lane can sit on an idle queue while another
lane holds 87 unclaimed items.

This posts ONE request row per lane into that lane's queue, naming the rows
it is asking about, so the request is actionable rather than a nudge. It is
idempotent: `post_task` collapses an identical re-post.

Usage:  python request_assignments.py [--dry-run] [--lane opencode]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, r"C:\Azazael\azazael")
sys.path.insert(0, r"C:\Azazael\azazael\src")
from CORE.LaneMessageBoard import LaneMessageBoard  # noqa: E402

TARGET = "opencode"
# The lanes we can ask. crush and agy are parked; asking them adds noise.
ASKABLE = ("kilo", "freebuff")
MAX_LISTED = 15


def open_items(board: LaneMessageBoard, lane: str) -> list:
    """The rows a claim on `lane` would hand out right now."""
    out = []
    for t in board.poll_tasks(lane, limit=200):
        row_id = (t.metadata or {}).get("_row_id")
        out.append((row_id, t.action or "", t.task_id or "", t.source_lane or ""))
    return out


def build_detail(lane: str, items: list, stamp: str) -> str:
    if not items:
        return (
            f"REQUEST AN ASSIGNMENT -> {TARGET} ({stamp}).\n"
            f"{lane} holds no open items, so there is nothing to hand over. "
            f"If you have work in flight that fits the {TARGET} lane, push it "
            f"to lane.{TARGET}.tasks (LaneMessageBoard.push_hook(dst_lane='{TARGET}', ...)), "
            f"and the delivery row plus its audit row will name what landed.\n"
            f"Named items: none (the queue is empty)."
        )
    lines = [
        f"REQUEST AN ASSIGNMENT -> {TARGET} ({stamp}).",
        f"{lane} holds {len(items)} open item(s) that nobody has claimed. "
        f"Push the ones the {TARGET} lane can take to lane.{TARGET}.tasks "
        f"(push_hook writes the delivery row and the lane.push.{lane}->{TARGET} "
        f"audit row that names it).",
        "",
        "Named items (open work on the " + lane + " queue):",
    ]
    for row_id, action, task_id, source in items[:MAX_LISTED]:
        lines.append(f"  Board-{row_id} | {task_id} | {action[:110]}")
    if len(items) > MAX_LISTED:
        lines.append(f"  ... and {len(items) - MAX_LISTED} more "
                     f"(ask for the rest by claiming the lane).")
    lines += [
        "",
        "Why this row exists: nothing wakes a session when work arrives, so a "
        "queued item is queued, not received. The opencode lane now runs a "
        "scheduled board_watch check (every minute) that notices arrivals and "
        "drains what is claimable, so a pushed item is picked up on the next "
        "check rather than sitting.",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lane", default=TARGET)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    board = LaneMessageBoard(lane=args.lane)
    for lane in ASKABLE:
        try:
            items = open_items(board, lane)
        except Exception as exc:
            print(f"ERROR: could not read the {lane} queue: {exc}")
            continue
        detail = build_detail(lane, items, stamp)
        action = (f"ASSIGN {len(items)} OPEN ITEM(S) TO {args.lane.upper()}"
                  if items else f"PROVIDE AN ASSIGNMENT TO {args.lane.upper()}")
        task_id = f"assign-to-{args.lane}-{lane}-{stamp[:10]}"
        if args.dry_run:
            print(f"[dry-run] would post to {lane}: {action}")
            print(detail)
            print("-" * 70)
            continue
        try:
            row = board.post_task(lane=lane, action=action, detail=detail,
                                   task_id=task_id, source_lane=args.lane)
        except Exception as exc:
            print(f"ERROR: could not post the request to {lane}: {exc}")
            continue
        print(f"posted Board-{row} -> {lane} :: {action}")
        # Read it back: a post you cannot read back did not land.
        found = [t for t in board.poll_tasks(lane, limit=200)
                 if (t.metadata or {}).get("_row_id") == row]
        print(f"  readback: {'OK Board-' + str(row) if found else 'NOT FOUND'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
