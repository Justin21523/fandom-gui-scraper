# tests/unit/test_selectors.py

import os, sys
# ─── 把專案根目錄加入模組搜尋路徑 ───────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))
# ─────────────────────────────────────────────────────────────────────────

from bs4 import BeautifulSoup
from utils.selectors import selectors

def test_title_unit():
    html = '<h1 class="page-header__title">Unit Test Title</h1>'
    soup = BeautifulSoup(html, 'html.parser')
    conf = selectors["default"]["title"]
    # CSS selector 裡可能含 ::text，把它去掉
    css_path = conf["css"].split("::")[0]
    el = soup.select_one(css_path)
    title = el.get_text(strip=True) if el else None
    assert title == "Unit Test Title", f"Expected 'Unit Test Title' but got {title}"
    print("✅ test_title_unit passed.")

def test_content_paragraphs_unit():
    html = """
    <div class="mw-parser-output">
      <p>First paragraph</p>
      <p>Second paragraph</p>
    </div>
    """
    soup = BeautifulSoup(html, 'html.parser')
    conf = selectors["default"]["content_paragraphs"]
    css_path = conf["css"].split("::")[0]
    ps = soup.select(css_path)
    paras = [p.get_text(strip=True) for p in ps]
    assert paras == ["First paragraph", "Second paragraph"], f"Got {paras}"
    print("✅ test_content_paragraphs_unit passed.")

if __name__ == "__main__":
    test_title_unit()
    test_content_paragraphs_unit()
    print("🎉 All selector unit tests passed.")
