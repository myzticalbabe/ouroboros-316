"""Sequential execution engine: runs a plan across Python versions."""

from __future__ import annotations

import concurrent.futures
from typing import Any, Dict, List, Optional

from .adapter import VersionAdapter
from .plan import SequentialPlan


class ExecutionResult:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.checkpoints: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    @property
    def success(self) -> bool:
        return not self.errors


class SequentialEngine:
    def __init__(self, adapters: Dict[str, VersionAdapter] = None,
                 checkpoint_dir: str = None, retries: int = 0, parallel: bool = False):
        self.adapters = adapters or {}
        self.checkpoint_dir = checkpoint_dir
        self.retries = retries
        self.parallel = parallel

    def _adapter(self, version: str) -> VersionAdapter:
        if version not in self.adapters:
            self.adapters[version] = VersionAdapter(version)
        return self.adapters[version]

    def _run_step(self, step, input_data):
        adapter = self._adapter(step.version)
        last_err = None
        for attempt in range(self.retries + 1):
            try:
                result = adapter.execute(step.code, input_data)
                return result, None
            except Exception as e:
                last_err = e
        return None, last_err

    def execute(self, plan: SequentialPlan) -> ExecutionResult:
        res = ExecutionResult()
        ordered = plan.topological_sort()
        by_name = {s.name: s for s in ordered}

        # level-based scheduling
        remaining = list(ordered)

        def ready(step):
            return all(dep in res.state for dep in step.depends_on)

        while remaining:
            batch = [s for s in remaining if ready(s)]
            if not batch:
                res.errors.append("deadlock: no ready steps")
                break
            for s in batch:
                remaining.remove(s)

            if self.parallel and len(batch) > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as ex:
                    futures = {}
                    for step in batch:
                        input_data = self._build_input(step, res.state)
                        futures[ex.submit(self._run_step, step, input_data)] = step
                    for fut in concurrent.futures.as_completed(futures):
                        step = futures[fut]
                        result, err = fut.result()
                        self._record(res, step, result, err)
            else:
                for step in batch:
                    input_data = self._build_input(step, res.state)
                    result, err = self._run_step(step, input_data)
                    self._record(res, step, result, err)
                    if err is not None:
                        return res
            # check errors
            if res.errors:
                return res

        return res

    def _build_input(self, step, state):
        if not step.depends_on:
            return None
        if len(step.depends_on) == 1:
            return state.get(step.depends_on[0])
        return {dep: state.get(dep) for dep in step.depends_on}

    def _record(self, res, step, result, err):
        if err is not None:
            res.errors.append(f"{step.name} ({step.version}): {err}")
            res.checkpoints.append({"step": step.name, "version": step.version,
                                   "ok": False, "error": str(err)})
        else:
            res.state[step.name] = result
            res.checkpoints.append({"step": step.name, "version": step.version,
                                   "ok": True})
            if self.checkpoint_dir:
                from .checkpoint import save_checkpoint
                save_checkpoint(self.checkpoint_dir, step.name, step.version, result)