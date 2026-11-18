from ouroboros.engine import SequentialEngine
from ouroboros.plan import SequentialPlan, Step

def test_engine_single_step():
    plan = SequentialPlan()
    plan.add(Step(name="s", version="3.14", code="result = 7"))
    res = SequentialEngine().execute(plan)
    assert res.success
    assert res.state["s"] == 7

def test_engine_cross_version():
    plan = SequentialPlan()
    plan.add(Step(name="a", version="3.8", code="result = 4"))
    plan.add(Step(name="b", version="3.16t", code="result = input_data + 1", depends_on=["a"]))
    res = SequentialEngine().execute(plan)
    assert res.success
    assert res.state["b"] == 5