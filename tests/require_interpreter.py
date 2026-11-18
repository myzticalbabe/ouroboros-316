"""Skip version-dependent tests when the interpreter is absent.

Same pattern the suite already uses for native binaries
(`pytest.skip("rust binary not built")`): a test that needs Python 3.8
cannot run where Python 3.8 does not exist, so it skips instead of
failing. `versions.resolve()` is the single source of truth.
"""

from __future__ import annotations

import json
import os

import pytest

from ouroboros import versions


def require(*wanted):
    """Skip unless every wanted version resolves to an interpreter."""
    missing = [v for v in wanted if versions.resolve(v) is None]
    if missing:
        pytest.skip(f"no interpreter for version(s): {', '.join(missing)}")


def require_for_file(path):
    """Skip unless every interpreter version named in a plan/.owh resolves."""
    if path.endswith(".owh"):
        from ouroboros.owh import OwhPackage

        steps = OwhPackage.load(path).sequential_plan
    else:
        with open(path) as f:
            steps = json.load(f).get("steps", [])
    require(*sorted({s.get("version") for s in steps if s.get("version")}))
