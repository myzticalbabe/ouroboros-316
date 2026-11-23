import json, os, subprocess, sys

from require_interpreter import require_for_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUST = os.path.join(ROOT, "native", "rust", "target", "release", "ouroboros-rs.exe")
C_HOST = os.path.join(ROOT, "native", "host", "ouroboros_host.exe")

def test_rust_e2e_plan():
    if not os.path.isfile(RUST):
        import pytest; pytest.skip("rust binary not built")
    plan = os.path.join(ROOT, "examples", "plan.json")
    r = subprocess.run([RUST, plan], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert "step_a: 5" in r.stdout or "step_a" in r.stdout
    assert "step_c" in r.stdout

def test_python_cli_e2e():
    plan = os.path.join(ROOT, "examples", "plan.json")
    require_for_file(plan)
    r = subprocess.run([sys.executable, "-m", "ouroboros", "run", plan],
                       capture_output=True, text=True, timeout=120, cwd=os.path.dirname(ROOT))
    assert r.returncode == 0, r.stderr
    assert "SUCCESS" in r.stdout

def test_c_host_e2e():
    if not os.path.isfile(C_HOST):
        import pytest; pytest.skip("c host not built")
    codefile = os.path.join(ROOT, "examples", "_tmp_code.py")
    with open(codefile, "w") as f:
        f.write("result = 6 * 7\n")
    r = subprocess.run([C_HOST, codefile], capture_output=True, text=True, timeout=60)
    os.remove(codefile)
    assert r.returncode == 0, r.stderr
    assert "RESULT: 42" in r.stdout

def test_owh_e2e():
    owh = os.path.join(ROOT, "examples", "cross.owh")
    require_for_file(owh)
    r = subprocess.run([sys.executable, "-m", "ouroboros", "run", owh],
                       capture_output=True, text=True, timeout=120, cwd=os.path.dirname(ROOT))
    assert r.returncode == 0, r.stderr
    assert "SUCCESS" in r.stdout