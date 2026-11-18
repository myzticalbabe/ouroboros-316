"""Subprocess runner executed inside a target Python interpreter."""

import base64
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from marshal import CrossVersionMarshaler
    _m = CrossVersionMarshaler()
except Exception:
    _m = None


def _dec(s):
    if _m is not None:
        try:
            return _m.unmarshal(s)
        except Exception:
            pass
    try:
        return json.loads(s)
    except Exception:
        return s


def main():
    raw = sys.stdin.buffer.read()
    if not raw:
        env = {"code": "", "input": None}
    else:
        try:
            env = json.loads(raw.decode("utf-8"))
        except Exception:
            try:
                env = json.loads(base64.b64decode(raw).decode("utf-8"))
            except Exception as e:
                out = {"ok": False, "error": repr(e), "tb": traceback.format_exc()}
                sys.stdout.write(base64.b64encode(json.dumps(out).encode()).decode())
                sys.stdout.flush()
                return
    code = env.get("code", "")
    inp = env.get("input", None)
    if isinstance(inp, str):
        try:
            inp = _dec(inp)
        except Exception:
            pass
    ns = {"input_data": inp, "result": None}
    try:
        exec(compile(code, "<ouroboros-step>", "exec"), ns)
        res = ns.get("result", None)
        out = {"ok": True, "result": (_m.marshal(res) if _m else json.dumps(res))}
    except Exception:
        out = {"ok": False, "error": repr(sys.exc_info()[1]),
               "tb": traceback.format_exc()}
    payload = base64.b64encode(json.dumps(out).encode("utf-8")).decode("ascii")
    sys.stdout.write(payload)
    sys.stdout.flush()


if __name__ == "__main__":
    main()