# tests/utils/test_normalizer.py
from utils.normalizer import clean_text, normalize_date

def test_clean_text_basic():
    assert clean_text("  Hello   World\n") == "Hello World"
    assert clean_text(None) == ""

def test_clean_text_html():
    raw = "<p>Line1</p><br><div>Line2</div>"
    assert clean_text(raw) == "Line1 Line2"

def test_normalize_date_success():
    assert normalize_date("2023年7月 4日") == "2023-07-04"

def test_normalize_date_fail():
    assert normalize_date("July 4, 2023") == "July 4, 2023"
