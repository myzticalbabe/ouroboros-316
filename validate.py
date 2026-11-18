"""Validation for plans and .owh metadata."""

from __future__ import annotations

from typing import Any, Dict, List

REQUIRED_PLAN_KEYS = {"name", "version"}
REQUIRED_STEP_KEYS = {"name", "version"}


class ValidationError(Exception):
    pass


def validate_step(step: Dict[str, Any], known_versions: List[str] = None):
    if not isinstance(step, dict):
        raise ValidationError("step must be a dict")
    missing = REQUIRED_STEP_KEYS - set(step.keys())
    if missing:
        raise ValidationError(f"step missing keys: {missing}")
    if "code" not in step and "action" not in step:
        raise ValidationError(f"step {step.get('name')} needs code or action")
    if known_versions and step["version"] not in known_versions:
        raise ValidationError(f"unknown version {step['version']}")


def validate_plan(plan: Dict[str, Any], known_versions: List[str] = None):
    if not isinstance(plan, dict):
        raise ValidationError("plan must be a dict")
    steps = plan.get("steps")
    if not isinstance(steps, list):
        raise ValidationError("plan needs a 'steps' list")
    names = []
    for s in steps:
        validate_step(s, known_versions)
        names.append(s["name"])
    if len(names) != len(set(names)):
        raise ValidationError("duplicate step names")
    # dependency check
    name_set = set(names)
    for s in steps:
        for dep in s.get("depends_on", []):
            if dep not in name_set:
                raise ValidationError(f"step {s['name']} depends on unknown {dep}")


def validate_owh_metadata(meta: Dict[str, Any]):
    if not isinstance(meta, dict):
        raise ValidationError("metadata must be a dict")
    if "name" not in meta:
        raise ValidationError("metadata missing 'name'")
    if "version" not in meta:
        raise ValidationError("metadata missing 'version'")
    if "sequential_plan" in meta:
        validate_plan({"steps": meta["sequential_plan"]})