import os, tempfile, json
from ouroboros.owh import OwhPackage

def test_assemble():
    d = tempfile.mkdtemp()
    src = os.path.join(d, "src")
    os.makedirs(src + "/layers", exist_ok=True)
    meta = {"name": "t", "version": "2.0", "sequential_plan": [{"name": "s", "version": "3.14", "code": "result=1"}]}
    open(src + "/ouroboros.json", "w").write(json.dumps(meta))
    open(src + "/layers/x.txt", "w").write("hi")
    out = os.path.join(d, "t.owh")
    OwhPackage.assemble(src, out)
    assert os.path.isfile(out)
    pkg = OwhPackage.load(out)
    assert pkg.name == "t"