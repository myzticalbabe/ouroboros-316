"""Probe: can Spark-X2.5 drive mesh-style agent calls (JSON discipline, routing)."""
import json
import urllib.request

URL = "http://127.0.0.1:8091/v1/chat/completions"


def chat(system, user, max_tokens=600):
    body = json.dumps({
        "model": "spark",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        msg = json.loads(r.read())["choices"][0]["message"]
    # Reasoning models (Spark) think in reasoning_content; answer may live
    # there when content is empty. Prefer content, fall back to tail of why.
    text = (msg.get("content") or "").strip()
    if not text:
        text = (msg.get("reasoning_content") or "").strip()[-400:]
    return text


t1 = chat(
    "Reply with ONLY this JSON object and no other text: "
    '{"category": "<name>", "priority": <1-5>}.',
    "Worm NETWORXZ reports port 22 open on an unknown host. Classify it.",
)
print("T1-JSON:", t1[:200].replace("\n", " "))
try:
    d = json.loads(t1)
    print("T1-PARSE: ok keys=", sorted(d.keys()))
except Exception as e:
    print("T1-PARSE: FAIL", str(e)[:100])

t2 = chat(
    "You are a router. Reply with exactly one word: CPU, GPU, or SKIP.",
    "Task: 4GB model surgery job, 16 cores free, 10GB RAM. Which backend?",
)
print("T2-ROUTE:", t2.strip()[:40].replace("\n", " "))
