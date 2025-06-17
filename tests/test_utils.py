import pytest
from src.utils import filter_none_values


def test_filter_none_values_typical():
    d = {'a': 1, 'b': None, 'c': 3, 'd': None}
    assert filter_none_values(d) == {'a': 1, 'c': 3}


def test_filter_none_values_all_none():
    d = {'a': None, 'b': None}
    assert filter_none_values(d) == {}


def test_filter_none_values_no_none():
    d = {'a': 0, 'b': '', 'c': False, 'd': []}
    # 0, '', False, [] are not None, so should be kept
    assert filter_none_values(d) == d


def test_filter_none_values_empty():
    d = {}
    assert filter_none_values(d) == {}


def test_filter_none_values_nested():
    d = {'a': None, 'b': {'x': None}, 'c': [None, 1], 'd': 2}
    # Only top-level None is removed
    assert filter_none_values(d) == {'b': {'x': None}, 'c': [None, 1], 'd': 2}


def test_filter_none_values_does_not_mutate_input():
    original = {'a': 1, 'b': None, 'c': 2}
    copy = original.copy()
    _ = filter_none_values(original)
    assert original == copy, "filter_none_values should not mutate its input dict"


def test_filter_none_values_with_null_strings():
    d = {'a': 1, 'b': None, 'c': 'null', 'd': 3, 'e': 'null'}
    assert filter_none_values(d) == {'a': 1, 'd': 3}


def test_filter_none_values_mixed_none_and_null():
    d = {'a': None, 'b': 'null', 'c': 'valid', 'd': 0, 'e': 'null', 'f': None}
    assert filter_none_values(d) == {'c': 'valid', 'd': 0}


def test_filter_none_values_only_null_strings():
    d = {'a': 'null', 'b': 'null', 'c': 'null'}
    assert filter_none_values(d) == {}


def test_filter_none_values_preserves_valid_strings_containing_null():
    d = {'a': 'null_value', 'b': 'not_null', 'c': 'null', 'd': None}
    # Should only filter exact "null" strings, not strings containing "null"
    assert filter_none_values(d) == {'a': 'null_value', 'b': 'not_null'}
