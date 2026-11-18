"""CLI for Ouroboros-316."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import versions
from .engine import SequentialEngine
from .owh import OwhPackage
from .plan import SequentialPlan
from . import validate as V


def cmd_versions(args):
    d = versions.discover()
    for v, it in sorted(d.items()):
        print(f"{v}: {it.path}  free_threaded={it.free_threaded}")
    if args.json:
        print(json.dumps({v: it.path for v, it in d.items()}, indent=2))


def cmd_run(args):
    # load plan from file (json) or owh
    path = args.plan
    if path.endswith(".owh"):
        pkg = OwhPackage.load(path)
        plan = pkg.to_plan()
    else:
        with open(path) as f:
            plan = SequentialPlan.from_dict(json.load(f))
    engine = SequentialEngine()
    res = engine.execute(plan)
    print("SUCCESS" if res.success else "FAILED")
    for cp in res.checkpoints:
        print(" ", cp)
    if res.state:
        print("STATE:")
        for k, v in res.state.items():
            print(f"  {k}: {v!r}")
    if res.errors:
        for e in res.errors:
            print("ERROR:", e)
    sys.exit(0 if res.success else 1)


def cmd_make_owh(args):
    with open(args.metadata) as f:
        metadata = json.load(f)
    pkg = OwhPackage.from_metadata(metadata)
    pkg.save(args.output)
    print(f"wrote {args.output}")

def cmd_assemble(args):
    pkg = OwhPackage.assemble(args.source, args.output)
    print(f"assembled {args.output} ({pkg.name} {pkg.version})")

def cmd_validate(args):
    path = args.path
    if path.endswith(".owh"):
        pkg = OwhPackage.load(path)
        meta = pkg.metadata
    else:
        with open(path) as f:
            raw = f.read()
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "steps" in parsed:
            V.validate_plan(parsed)
            print("VALID plan")
            return
        V.validate_owh_metadata(parsed)
        print("VALID owh metadata")
        return

def cmd_inspect(args):
    pkg = OwhPackage.load(args.path)
    print("name:", pkg.name)
    print("version:", pkg.version)
    print("sequential_plan:", len(pkg.sequential_plan), "steps")
    for s in pkg.sequential_plan:
        print("  ", s)

def cmd_install(args):
    import shutil, zipfile
    target = args.target or os.path.join(os.getcwd(), "installed_owh")
    os.makedirs(target, exist_ok=True)
    with zipfile.ZipFile(args.path) as zf:
        zf.extractall(target)
    print(f"installed {args.path} -> {target}")

def cmd_run(args):
    path = args.plan
    if path.endswith(".owh"):
        pkg = OwhPackage.load(path)
        plan = pkg.to_plan()
    else:
        with open(path) as f:
            plan = SequentialPlan.from_dict(json.load(f))
    engine = SequentialEngine(checkpoint_dir=args.checkpoint_dir, retries=args.retries, parallel=args.parallel)
    res = engine.execute(plan)
    print("SUCCESS" if res.success else "FAILED")
    for cp in res.checkpoints:
        print(" ", cp)
    if res.state:
        print("STATE:")
        for k, v in res.state.items():
            print(f"  {k}: {v!r}")
    if res.errors:
        for e in res.errors:
            print("ERROR:", e)
    sys.exit(0 if res.success else 1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="ouroboros")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("versions", help="list available interpreters")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_versions)

    s = sub.add_parser("run", help="run a sequential plan (.json or .owh)")
    s.add_argument("plan")
    s.add_argument("--checkpoint-dir", default=None)
    s.add_argument("--retries", type=int, default=0)
    s.add_argument("--parallel", action="store_true")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("make-owh", help="build a .owh from metadata json")
    s.add_argument("metadata")
    s.add_argument("-o", "--output", required=True)
    s.set_defaults(func=cmd_make_owh)

    s = sub.add_parser("assemble", help="assemble a .owh from a directory")
    s.add_argument("source")
    s.add_argument("-o", "--output", required=True)
    s.set_defaults(func=cmd_assemble)

    s = sub.add_parser("validate", help="validate a plan or .owh metadata")
    s.add_argument("path")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("inspect", help="inspect a .owh package")
    s.add_argument("path")
    s.set_defaults(func=cmd_inspect)

    s = sub.add_parser("install", help="install a .owh into a target dir")
    s.add_argument("path")
    s.add_argument("--target", default=None)
    s.set_defaults(func=cmd_install)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()