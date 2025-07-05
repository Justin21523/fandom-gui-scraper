# tests/unit/test_normalizer.py

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))

from utils.normalizer import clean_text, normalize_date

def test_clean_text():
    raw = "  Hello <b>World</b>!  \n"
    out = clean_text(raw)
    assert out == "Hello World!", f"clean_text output: '{out}'"
    print("✅ test_clean_text passed.")

def test_normalize_date():
    cases = {
        "2020-01-02": "2020-01-02",
        "Jan 2, 2020": "2020-01-02",
        "2 January 2020": "2020-01-02",
    }
    for raw, exp in cases.items():
        got = normalize_date(raw)
        assert got == exp, f"normalize_date('{raw}') -> '{got}', expected '{exp}'"
    print("✅ test_normalize_date passed.")

if __name__ == "__main__":
    test_clean_text()
    test_normalize_date()
    print("🎉 All normalizer unit tests passed.")
