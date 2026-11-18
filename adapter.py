"""Version adapter: runs code in a target Python interpreter via subprocess."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from typing import Any, Optional

from . import versions
from .marshal import CrossVersionMarshaler

_RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_runner.py")


class AdapterError(Exception):
    pass


class VersionAdapter:
    def __init__(self, version: str, interpreter_path: Optional[str] = None):
        self.version = version
        self.interp = None
        if interpreter_path:
            self.interp = versions.Interpreter(version=version, path=interpreter_path,
                                             free_threaded=version.endswith("t"))
        else:
            self.interp = versions.resolve(version)
        if self.interp is None:
            raise AdapterError(f"no interpreter for version {version}")
        self.marshaler = CrossVersionMarshaler()

    def execute(self, code: str, input_data: Any = None) -> Any:
        # marshal input to tagged-json string for transport
        input_str = self.marshaler.marshal(input_data) if input_data is not None else None
        envelope = {"code": code, "input": input_str}
        stdin_data = json.dumps(envelope).encode("utf-8")

        env = dict(os.environ)
        env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + env.get("PYTHONPATH", "")

        try:
            proc = subprocess.run(
                [self.interp.path, _RUNNER],
                input=stdin_data,
                capture_output=True,
                timeout=120,
                env=env,
            )
        except subprocess.TimeoutExpired as e:
            raise AdapterError(f"timeout executing on {self.version}: {e}")

        stdout = proc.stdout.decode("utf-8", errors="replace").strip()
        if not stdout:
            raise AdapterError(f"empty output from {self.version}: stderr={proc.stderr.decode(errors='replace')[:500]}")
        try:
            payload = json.loads(base64.b64decode(stdout))
        except Exception as e:
            raise AdapterError(f"bad transport from {self.version}: {e}; stdout={stdout[:200]}")
        if not payload.get("ok"):
            raise AdapterError(f"exec failed on {self.version}: {payload.get('error')}\n{payload.get('tb','')}")
        result_str = payload.get("result")
        if isinstance(result_str, str):
            try:
                return self.marshaler.unmarshal(result_str)
            except Exception:
                return result_str
        return result_str


def make_adapter(version: str) -> VersionAdapter:
    return VersionAdapter(version)