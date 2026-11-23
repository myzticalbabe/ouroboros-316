import datetime
from ouroboros.marshal import CrossVersionMarshaler

m = CrossVersionMarshaler()

def test_roundtrip_primitives():
    for v in [None, True, False, 0, 42, 3.14, "hi", b"raw"]:
        assert m.unmarshal(m.marshal(v)) == v

def test_roundtrip_collections():
    data = [1, 2, (3, 4), {5, 6}, {"a": [7, 8]}, frozenset([9])]
    dec = m.unmarshal(m.marshal(data))
    assert dec[0:2] == [1, 2]
    assert isinstance(dec[2], tuple)
    assert set(dec[3]) == {5, 6}
    assert dec[4] == {"a": [7, 8]}
    assert isinstance(dec[5], frozenset)

def test_roundtrip_datetime():
    now = datetime.datetime(2026, 11, 17, 12, 0, 0)
    assert m.unmarshal(m.marshal(now)) == now

def test_roundtrip_bytes():
    b = b"\x00\x01\xff"
    assert m.unmarshal(m.marshal(b)) == b