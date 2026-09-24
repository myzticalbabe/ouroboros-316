"""Grammar probe: does response_format json_object constrain output?"""
import json
import urllib.request

body = {
    "model": "spark",
    "messages": [{"role": "user",
                  "content": "Reply ONLY with JSON: {\"ok\": true}."}],
    "max_tokens": 100,
    "temperature": 0.0,
    "seed": 7,
    "response_format": {"type": "json_object"},
}
req = urllib.request.Request(
    "http://127.0.0.1:8091/v1/chat/completions",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
msg = json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]
print("CONTENT:", repr(msg.get("content"))[:200])
try:
    json.loads(msg.get("content") or "")
    print("JSON: parses")
except Exception as e:
    print("JSON: FAIL", str(e)[:80])
