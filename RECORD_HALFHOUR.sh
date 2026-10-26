#!/bin/bash
# RECORD_HALFHOUR.sh — 30 minutes in 30-second clips (60 parts), proper spec.
# As run 2026-10-26 08:39 and 10:49 (verified: 60/60 clips both runs).
# Spec (do not weaken): H.264, preset medium, CRF 23, yuv420p, 30fps, 1920x1200.
# Windows are pre-arranged (RECORD_BOTH_30S.ps1 or manual); this loop only captures.
# Usage: ./RECORD_HALFHOUR.sh [outdir]
TS=$(date +%Y%m%d_%H%M%S)
D=${1:-/c/Users/clint/Desktop/HTML_MP4}
for i in $(seq -w 1 60); do
  echo "[$(date +%H:%M:%S)] Clip $i/60"
  ffmpeg -y -v error -f gdigrab -framerate 30 -i desktop \
    -vf 'scale=1920:1200' -c:v libx264 -preset medium -crf 23 \
    -pix_fmt yuv420p -r 30 -an -t 30 "$D/HALFHOUR_30s_${TS}_part${i}.mp4"
done
echo "HALFHOUR DONE $TS"
