#!/usr/bin/env python
# coding: utf-8
import sys
import json
import os
AZAZAEL = r"C:/Azazael/azazael"
if AZAZAEL not in sys.path:
    sys.path.insert(0, AZAZAEL)
if os.path.join(AZAZAEL, "src") not in sys.path:
    sys.path.insert(0, os.path.join(AZAZAEL, "src"))

from CORE.LaneMessageBoard import LaneMessageBoard
import sqlite3

board = LaneMessageBoard(lane='kilo')
conn = board._state_conn()
cursor = conn.cursor()
cursor.execute("SELECT * FROM lane_task_state WHERE lane='kilo' ORDER BY board_id DESC LIMIT 10")
print("Recent kilo task states:")
for row in cursor.fetchall():
    print(f"  {dict(row)}")

conn.close()