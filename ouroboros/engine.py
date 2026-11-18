"""Sequential execution engine: runs a plan across Python versions."""

from __future__ import annotations

from typing import Any, Dict, List

from .adapter import VersionAdapter
from .plan import SequentialPlan


class ExecutionResult:
    def __init__(self):
        self.state: Dict[str, Any] = {}   # step name -> result
        self.checkpoints: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    @property
    def success(self) -> bool:
        return not self.errors


class SequentialEngine:
    def __init__(self, adapters: Dict[str, VersionAdapter] = None):
        self.adapters = adapters or {}

    def _adapter(self, version: str) -> VersionAdapter:
        if version not in self.adapters:
            self.adapters[version] = VersionAdapter(version)
        return self.adapters[version]

    def execute(self, plan: SequentialPlan) -> ExecutionResult:
        res = ExecutionResult()
        ordered = plan.topological_sort()
        for step in ordered:
            adapter = self._adapter(step.version)
            # build input from dependencies
            input_data = None
            if step.depends_on:
                if len(step.depends_on) == 1:
                    input_data = res.state.get(step.depends_on[0])
                else:
                    input_data = {dep: res.state.get(dep) for dep in step.depends_on}
            try:
                result = adapter.execute(step.code, input_data)
                res.state[step.name] = result
                res.checkpoints.append({"step": step.name, "version": step.version,
                                       "ok": True})
            except Exception as e:
                res.errors.append(f"{step.name} ({step.version}): {e}")
                res.checkpoints.append({"step": step.name, "version": step.version,
                                       "ok": False, "error": str(e)})
                break
        return res