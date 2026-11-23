import json, os, tempfile
from ouroboros.owh import OwhPackage

def test_owh_save_load():
    meta = {"name": "demo", "version": "1.0", "sequential_plan": [
        {"name": "s", "version": "3.14", "action": "run"}
    ]}
    pkg = OwhPackage.from_metadata(meta)
    d = tempfile.mkdtemp()
    path = os.path.join(d, "demo.owh")
    pkg.save(path)
    loaded = OwhPackage.load(path)
    assert loaded.name == "demo"
    assert loaded.version == "1.0"