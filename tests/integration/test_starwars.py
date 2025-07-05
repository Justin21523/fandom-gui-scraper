# tests/integration/test_starwars.py
import os
import sys
# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests
from bs4 import BeautifulSoup
from utils.selectors import selectors



def main():
    url = "https://starwars.fandom.com/wiki/Luke_Skywalker"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    conf = selectors["default"]

    # title
    css_title = conf["title"]["css"].split("::")[0]
    el = soup.select_one(css_title)
    title = el.get_text(strip=True) if el else ""
    if "Luke Skywalker" not in title:
        raise AssertionError(f"❌ integration title failed, got {title!r}")
    print("✅ integration title passed:", title)

    # 前兩段
    css_para = conf["content_paragraphs"]["css"].split("::")[0]
    ps = soup.select(css_para)
    paras = [p.get_text(strip=True) for p in ps[:2]]
    if len(paras) < 2:
        raise AssertionError(f"❌ only {len(paras)} paras: {paras}")
    print("✅ integration paragraphs passed:", paras)

    print("🎉 All integration tests passed!")

if __name__ == "__main__":
   main()
