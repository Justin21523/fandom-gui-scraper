# scraper/base_spider.py
# -*- coding: utf-8 -*-
import os
import sys
# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import scrapy
from typing import Any, Dict
from cssselect.parser import SelectorSyntaxError
from utils.selectors import selectors
from utils.normalizer import clean_text

class BaseSpider(scrapy.Spider):
    # 給一個預設 name，子類別也可以 override
    name = "base_spider"
    custom_settings = {
        "ITEM_PIPELINES": {
            "scraper.pipelines.MongoPipeline": 300
        },
        "CONCURRENT_REQUESTS": 4,
        "DOWNLOAD_DELAY": 1,
        "USER_AGENT": "my_fandom_scraper (+https://github.com/justin21523/fandom-gui-scraper)"
    }

    def __init__(self, site: str = "default",  name: str = None, *args, **kwargs):
        if name:
            self.name = name
        super().__init__(self.name, *args, **kwargs)
        self.site = site
        # 這裡假設 selectors 已經載入完畢
        self.sel_conf: Dict[str, Dict[str, str]] = selectors[site]

    def extract(self, response: scrapy.http.Response, field: str) -> str:
        """
        通用欄位擷取：
        1. 先嘗試 CSS
        2. 捕捉 SelectorSyntaxError → 空結果
        3. 若 CSS 無結果，或未定義，改用 XPath
        4. 最後清洗、回傳純文字
        """
        cfg = self.sel_conf[field]
        text = None

        # 1. 嘗試 CSS
        if cfg.get("css"):
            try:
                text = response.css(cfg["css"]).get()
            except SelectorSyntaxError:
                # CSS 語法不支援，跳過
                text = None

        # 2. CSS 失敗或沒定義 → XPath
        if not text and cfg.get("xpath"):
            text = response.xpath(cfg["xpath"]).get()

        # 3. 清洗後回傳
        return clean_text(text)

    def parse(self, response: scrapy.http.Response) -> Any:
        """
        由子類別 override：回傳要送到 pipelines 的 dict
        """
        raise NotImplementedError("子類別必須實作 parse()")

if __name__ == "__main__":
    # 簡單自我測試：用 requests 模擬 Scrapy Response
    from scrapy.http import TextResponse
    import requests

    url = "https://starwars.fandom.com/wiki/Luke_Skywalker"
    html = requests.get(url).text
    resp = TextResponse(url, body=html, encoding="utf-8")
    print(" ▶ 測試 BaseSpider")
    spider = BaseSpider(site="default", name="test_base")
    title = spider.extract(resp, "title")
    print("抓到的 title：", title)
    print("✅ BaseSpider OK")
