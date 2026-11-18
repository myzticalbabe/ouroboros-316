"""The .owh (Ouroboros Wheel Header) package format."""

from __future__ import annotations

import json
import os
import zipfile
from typing import Any, Dict, List


class OwhPackage:
    def __init__(self, metadata: Dict[str, Any]):
        self.metadata = metadata

    @property
    def name(self) -> str:
        return self.metadata.get("name", "unknown")

    @property
    def version(self) -> str:
        return self.metadata.get("version", "0.0.0")

    @property
    def sequential_plan(self) -> List[Dict[str, Any]]:
        return self.metadata.get("sequential_plan", [])

    def to_plan(self):
        from .plan import SequentialPlan, Step
        plan = SequentialPlan()
        # build steps from sequential_plan entries
        for i, entry in enumerate(self.sequential_plan):
            # entry may be {"version":..., "action":..., ...} or a step dict
            step_name = entry.get("name") or f"step_{i}_{entry.get('action','run')}"
            code = entry.get("code", "")
            deps = entry.get("depends_on", [])
            plan.add(Step(name=step_name, version=entry["version"], code=code,
                          depends_on=deps))
        return plan

    def save(self, path: str):
        """Save as a .owh zip archive with ouroboros.json metadata."""
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("ouroboros.json", json.dumps(self.metadata, indent=2))

    @classmethod
    def load(cls, path: str) -> "OwhPackage":
        if os.path.isdir(path):
            meta_path = os.path.join(path, "ouroboros.json")
            with open(meta_path) as f:
                metadata = json.load(f)
            return cls(metadata)
        with zipfile.ZipFile(path) as zf:
            with zf.open("ouroboros.json") as f:
                metadata = json.load(f)
        return cls(metadata)

    @classmethod
    def from_metadata(cls, metadata: Dict[str, Any]) -> "OwhPackage":
        return cls(metadata)

    @staticmethod
    def assemble(source_dir: str, output: str) -> "OwhPackage":
        """Assemble a .owh from a directory containing ouroboros.json + layers/."""
        meta_path = os.path.join(source_dir, "ouroboros.json")
        with open(meta_path) as f:
            metadata = json.load(f)
        pkg = OwhPackage(metadata)
        # include layer files in zip
        parent = os.path.dirname(os.path.abspath(output))
        os.makedirs(parent, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("ouroboros.json", json.dumps(metadata, indent=2))
            for root, _, files in os.walk(source_dir):
                for fn in files:
                    if fn == "ouroboros.json":
                        continue
                    full = os.path.join(root, fn)
                    arc = os.path.relpath(full, source_dir)
                    zf.write(full, arc)
        return pkg