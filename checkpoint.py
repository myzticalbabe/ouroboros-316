"""State checkpointing per step."""

from __future__ import annotations

import json
import os
from typing import Any, Dict


def save_checkpoint(directory: str, step_name: str, version: str, state: Any) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{step_name}.checkpoint.json")
    with open(path, "w") as f:
        json.dump({"step": step_name, "version": version, "state": state}, f, default=str)
    return path


def load_checkpoint(directory: str, step_name: str) -> Dict[str, Any]:
    path = os.path.join(directory, f"{step_name}.checkpoint.json")
    with open(path) as f:
        return json.load(f)