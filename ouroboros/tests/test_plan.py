from ouroboros.plan import SequentialPlan, Step

def test_topological_sort():
    plan = SequentialPlan()
    plan.add(Step(name="b", version="3.14", code="", depends_on=["a"]))
    plan.add(Step(name="a", version="3.8", code=""))
    ordered = [s.name for s in plan.topological_sort()]
    assert ordered == ["a", "b"]

def test_cycle_detection():
    plan = SequentialPlan()
    plan.add(Step(name="a", version="3.8", code="", depends_on=["b"]))
    plan.add(Step(name="b", version="3.8", code="", depends_on=["a"]))
    try:
        plan.topological_sort()
        assert False, "expected cycle error"
    except ValueError:
        pass

def test_roundtrip_dict():
    plan = SequentialPlan()
    plan.add(Step(name="x", version="3.8", code="result=1"))
    d = plan.to_dict()
    p2 = SequentialPlan.from_dict(d)
    assert p2.steps[0].name == "x"
    assert p2.steps[0].code == "result=1"