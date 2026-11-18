"""Sequential execution plan (DAG) with version annotations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Step:
    name: str
    version: str
    code: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class SequentialPlan:
    steps: List[Step] = field(default_factory=list)

    def add(self, step: Step):
        self.steps.append(step)

    @property
    def versions(self) -> List[str]:
        seen = []
        for s in self.steps:
            if s.version not in seen:
                seen.append(s.version)
        return seen

    def topological_sort(self) -> List[Step]:
        by_name = {s.name: s for s in self.steps}
        visited = set()
        result: List[Step] = []
        visiting = set()

        def visit(name: str):
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"cycle detected at {name}")
            visiting.add(name)
            step = by_name[name]
            for dep in step.depends_on:
                if dep not in by_name:
                    raise ValueError(f"unknown dependency {dep} for {name}")
                visit(dep)
            visiting.discard(name)
            visited.add(name)
            result.append(step)

        for s in self.steps:
            visit(s.name)
        return result

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SequentialPlan":
        plan = cls()
        for s in d.get("steps", []):
            plan.add(Step(
                name=s["name"],
                version=s["version"],
                code=s.get("code", ""),
                depends_on=list(s.get("depends_on", [])),
            ))
        return plan

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": [
            {"name": s.name, "version": s.version, "code": s.code,
             "depends_on": list(s.depends_on)} for s in self.steps
        ]}