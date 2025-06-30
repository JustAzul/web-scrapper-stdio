from src.utils import filter_none_values


def test_filter_none_values_typical():
    d = {"a": 1, "b": None, "c": 3, "d": None}
    assert filter_none_values(d) == {"a": 1, "c": 3}


def test_filter_none_values_all_none():
    d = {"a": None, "b": None}
    assert filter_none_values(d) == {}


def test_filter_none_values_no_none():
    d = {"a": 0, "b": "", "c": False, "d": []}
    # 0, '', False, [] are not None, so should be kept
    assert filter_none_values(d) == d


def test_filter_none_values_empty():
    d = {}
    assert filter_none_values(d) == {}


def test_filter_none_values_nested():
    d = {"a": None, "b": {"x": None}, "c": [None, 1], "d": 2}
    # Only top-level None is removed
    assert filter_none_values(d) == {"b": {"x": None}, "c": [None, 1], "d": 2}


def test_filter_none_values_does_not_mutate_input():
    original = {"a": 1, "b": None, "c": 2}
    copy = original.copy()
    _ = filter_none_values(original)
    assert original == copy, "filter_none_values should not mutate its input dict"
