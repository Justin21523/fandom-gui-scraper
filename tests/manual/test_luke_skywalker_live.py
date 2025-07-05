# tests/manual/test_luke_skywalker_live.py

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

import requests
from bs4 import BeautifulSoup
from utils.selectors import selectors

def main():
    url = "https://starwars.fandom.com/wiki/Luke_Skywalker"
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    conf = selectors["default"]

    # CSS vs XPath 只是示意，這裡我們用 CSS
    title_css = soup.select_one(conf["title"]["css"].split("::")[0])
    print("TITLE:", title_css.get_text(strip=True) if title_css else None)

    ps = soup.select(conf["content_paragraphs"]["css"].split("::")[0])
    print("PARA[:2]:", [p.get_text(strip=True) for p in ps[:2]])

    print("\n⚠️ 請手動核對以上輸出是否正確。")

if __name__ == "__main__":
    main()
