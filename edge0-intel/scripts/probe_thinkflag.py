"""Test: does Spark honor enable_thinking=false? Times a summary-sized call."""
import json
import time
import urllib.request

with open(r"C:\Users\clint\edge0-intel\scripts\svi.py", encoding="utf-8") as f:
    code = f.read()[:3000]

body = json.dumps({
    "model": "spark",
    "messages": [
        {"role": "user", "content": "Summarize what this file does in 3 sentences:\n" + code},
    ],
    "max_tokens": 300,
    "enable_thinking": False,
}).encode()
t0 = time.time()
req = urllib.request.Request("http://127.0.0.1:8091/v1/chat/completions",
                             data=body,
                             headers={"Content-Type": "application/json"})
msg = json.loads(urllib.request.urlopen(req, timeout=600).read())["choices"][0]["message"]
dt = time.time() - t0
print("SECS:", round(dt, 1))
print("CONTENT:", repr((msg.get("content") or ""))[:300])
print("THINK_LEN:", len(msg.get("reasoning_content") or ""))
