from ouroboros import validate as V

def test_validate_plan_ok():
    V.validate_plan({"steps": [{"name": "a", "version": "3.14", "code": "result=1"}]})

def test_validate_plan_missing_name():
    try:
        V.validate_plan({"steps": [{"version": "3.14", "code": "result=1"}]})
        assert False
    except V.ValidationError:
        pass

def test_validate_owh_ok():
    V.validate_owh_metadata({"name": "x", "version": "1.0"})

def test_validate_step_unknown_dep():
    try:
        V.validate_plan({"steps": [{"name": "a", "version": "3.14", "code": "x", "depends_on": ["zzz"]}]} )
        assert False
    except V.ValidationError:
        pass