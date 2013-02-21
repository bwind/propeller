from propeller.util.dict import *


def setup():
    pass

def teardown():
    pass


def test_multidict_empty():
    m = MultiDict()
    assert m == {}

def test_multidict_super():
    m = MultiDict()
    m['_items'] = {}
    assert m == {}

def test_multidict_single():
    m = MultiDict()
    m['foo'] = 'bar'
    assert m['foo'] == ['bar']

def test_multidict_multiple():
    m = MultiDict()
    m.add('foo', 1)
    m.add('foo', 2)
    assert m['foo'] == [1, 2]

def test_multidict_contains():
    m = MultiDict()
    m['foo'] = 'bar'
    assert 'foo' in m

def test_multidict_repr():
    m = MultiDict()
    m['foo'] = 'bar'
    assert repr(m) == "{'foo': ['bar']}"

def test_multidict_iter():
    m = MultiDict()
    m.add('foo', 1)
    m.add('foo', 2)
    for v in m:
        assert v == 'foo'

def test_multidict_items():
    m = MultiDict()
    m.add('foo', 1)
    m.add('foo', 2)
    assert m.items() == [('foo', 1), ('foo', 2)]


def test_immutablemultidict_len():
    m = ImmutableMultiDict([('foo', 1), ('foo', 2)])
    assert len(m) == 1

def test_immutablemultidict_items():
    m = ImmutableMultiDict([('foo', 1), ('foo', 2)])
    assert m.items() == [('foo', 1), ('foo', 2)]


def test_immutabledict_items():
    m = ImmutableDict({'foo': 'bar'})
    assert m.items() == [('foo', 'bar')]

def test_immutabledict_eq():
    m = ImmutableDict({'foo': 'bar'})
    assert m == {'foo': 'bar'}

def test_immutabledict_repr():
    m = ImmutableDict({'foo': 'bar'})
    assert repr(m) == "{'foo': 'bar'}"

def test_immutabledict_len():
    m = ImmutableDict({'foo': 1, 'bar': 2})
    assert len(m) == 2

def test_immutabledict_iter():
    m = ImmutableDict({'foo': 1, 'bar': 2})
    i = iter(m)
    assert next(i) == 'foo'
    assert next(i) == 'bar'
