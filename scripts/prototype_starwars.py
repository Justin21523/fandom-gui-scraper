# scripts/prototype_starwars.py

import requests
from parsel import Selector
from utils.selectors import selectors

def test_title():
    """測試 title selector"""
    url = "https://starwars.fandom.com/wiki/Luke_Skywalker"
    html = requests.get(url, timeout=10).text
    sel = Selector(html)
    conf = selectors["default"]["title"]
    # 先試 CSS，再試 XPath
    title = sel.css(conf["css"]).get() or sel.xpath(conf["xpath"]).get()
    print("TITLE:", title)
    assert title and "Luke Skywalker" in title, "❌ title 沒抓到 Luke Skywalker"

def test_paragraphs():
    """測試 content_paragraphs selector（取前兩段）"""
    url = "https://starwars.fandom.com/wiki/Luke_Skywalker"
    html = requests.get(url, timeout=10).text
    sel = Selector(html)
    conf = selectors["default"]["content_paragraphs"]
    paras = sel.css(conf["css"]).getall() or sel.xpath(conf["xpath"]).getall()
    paras = [p.strip() for p in paras[:2]]
    print("PARAGRAPHS:", paras)
    assert len(paras) == 2, f"❌ 只抓到 {len(paras)} 段"
    assert "fictional character" in paras[0].lower(), "❌ 第一段內容不對"

def main():
    print("🔍 開始手動測試 selectors …\n")
    test_title()
    print("✅ title 測試通過\n")
    test_paragraphs()
    print("✅ paragraphs 測試通過\n")
    print("🎉 全部測試成功！")

if __name__ == "__main__":
    main()
