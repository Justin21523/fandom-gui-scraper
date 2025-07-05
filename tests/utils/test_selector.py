# tests/utils/test_selectors.py
import pytest
from utils.selectors import get_selector

def test_get_selector_success():
    s = get_selector("onepiece", "title")
    assert "//h1/text()" in s

def test_get_selector_fail():
    with pytest.raises(KeyError):
        get_selector("onepiece", "nonexistent")
