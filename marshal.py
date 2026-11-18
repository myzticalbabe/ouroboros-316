"""Cross-version marshaling: version-agnostic encode/decode via tagged JSON."""

from __future__ import annotations

import base64
import datetime
import json
from typing import Any


def _encode(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (bytes, bytearray)):
        return {"$b": base64.b64encode(bytes(obj)).decode("ascii")}
    if isinstance(obj, datetime.datetime):
        return {"$dt": obj.isoformat()}
    if isinstance(obj, datetime.date):
        return {"$d": obj.isoformat()}
    if isinstance(obj, datetime.timedelta):
        return {"$td": obj.total_seconds()}
    if isinstance(obj, tuple):
        return {"$t": [_encode(x) for x in obj]}
    if isinstance(obj, set):
        return {"$s": [_encode(x) for x in obj]}
    if isinstance(obj, frozenset):
        return {"$fs": [_encode(x) for x in obj]}
    if isinstance(obj, list):
        return [_encode(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _encode(v) for k, v in obj.items()}
    # numpy (optional)
    try:
        import numpy as np
        if isinstance(obj, np.ndarray):
            return {"$nd": {"shape": list(obj.shape), "dtype": str(obj.dtype),
                            "data": _encode(obj.ravel().tolist())}}
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
    except Exception:
        pass
    # fallback: repr
    return {"$r": repr(obj), "$type": type(obj).__name__}


def _decode(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_decode(x) for x in obj]
    if isinstance(obj, dict):
        if len(obj) == 1:
            k = next(iter(obj))
            if k == "$b":
                return base64.b64decode(obj["$b"])
            if k == "$dt":
                return datetime.datetime.fromisoformat(obj["$dt"])
            if k == "$d":
                return datetime.date.fromisoformat(obj["$d"])
            if k == "$td":
                return datetime.timedelta(seconds=obj["$td"])
            if k == "$t":
                return tuple(_decode(x) for x in obj["$t"])
            if k == "$s":
                return set(_decode(x) for x in obj["$s"])
            if k == "$fs":
                return frozenset(_decode(x) for x in obj["$fs"])
            if k == "$nd":
                nd = obj["$nd"]
                try:
                    import numpy as np
                    arr = np.array(nd["data"], dtype=nd["dtype"]).reshape(nd["shape"])
                    return arr
                except Exception:
                    return nd
        # ndarray data nested
        if "$nd" in obj and isinstance(obj.get("$nd"), dict):
            nd = obj["$nd"]
            try:
                import numpy as np
                arr = np.array(_decode(nd["data"]), dtype=nd["dtype"]).reshape(nd["shape"])
                return arr
            except Exception:
                return nd
        return {k: _decode(v) for k, v in obj.items()}
    return obj


class CrossVersionMarshaler:
    def marshal(self, obj: Any) -> str:
        return json.dumps(_encode(obj), ensure_ascii=False)

    def unmarshal(self, data) -> Any:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")
        return _decode(json.loads(data))

    def marshal_bytes(self, obj: Any) -> bytes:
        return self.marshal(obj).encode("utf-8")

    def unmarshal_bytes(self, data: bytes) -> Any:
        return self.unmarshal(data)


if __name__ == "__main__":
    m = CrossVersionMarshaler()
    samples = [42, 3.14, "hi", b"raw", [1, 2, (3, 4)], {"a": {1, 2}}, datetime.datetime.now()]
    for s in samples:
        enc = m.marshal(s)
        dec = m.unmarshal(enc)
        print(repr(s), "->", enc[:60], "->", repr(dec))