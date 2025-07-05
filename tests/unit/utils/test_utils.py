import pytest
from src.utils import filter_none_values

def test_filter_none_values_removes_none():
    data = {"a": 1, "b": None, "c": 2}
    result = filter_none_values(data)
    assert result == {"a": 1, "c": 2}

def test_filter_none_values_empty():
    assert filter_none_values({}) == {}

def test_filter_none_values_all_none():
    assert filter_none_values({"a": None, "b": None}) == {}
