# scraper/fandom_spider.py
# -*- coding: utf-8 -*-
import os
import sys
# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import scrapy
from typing import List, Any, Dict
from utils.normalizer import clean_text
from utils.selectors import selectors
from scraper.base_spider  import BaseSpider

class FandomSpider(BaseSpider):
    # 為了 scrapy 能識別，必須有 name
    name = "fandom_spider"
    # allowed_domains 可留空，或依站點動態設定
    allowed_domains = []

    def __init__(
        self,
        site: str = "default",
        start_urls: List[str] = None,
        *args,
        **kwargs
    ):
        # 先呼叫 BaseSpider，載入 selectors
        super().__init__(site=site, *args, **kwargs)

        # 動態設置 start_urls
        if start_urls:
            self.start_urls = start_urls
        elif not getattr(self, "start_urls", None):
            raise ValueError("請提供 start_urls")

    def parse(self, response: scrapy.http.Response) -> Any:
        """
        通用解析：走訪 selectors[site] 裡的所有欄位設定，
        單值欄位用 extract(), 多值欄位則 .getall() + clean_text
        """
        item: Dict[str, Any] = {}
        conf: Dict[str, Dict[str, str]] = selectors[self.site]

        for field, cfg in conf.items():
            # 多值欄位
            if field in ("content_paragraphs", "image_urls", "categories"):
                # 優先用 CSS，不行就 XPath
                values = (
                    response.css(cfg["css"]).getall() or
                    response.xpath(cfg["xpath"]).getall()
                )
                # 清洗每個值
                item[field] = [clean_text(v) for v in values if clean_text(v)]
            else:
                # 單值欄位
                item[field] = self.extract(response, field)

        yield item


if __name__ == "__main__":
    # 簡易自測：用 requests + TextResponse
    import requests
    from scrapy.http import TextResponse

    url = "https://starwars.fandom.com/wiki/Luke_Skywalker"
    html = requests.get(url).text
    resp = TextResponse(url, body=html, encoding="utf-8")

    spider = FandomSpider(
        site="default",
        start_urls=[url],
        name="test_fandom"
    )
    for itm in spider.parse(resp):
        print("解析結果：")
        for k, v in itm.items():
            print(f"  {k}: {v[:2] if isinstance(v, list) else v}")
    print("✅ FandomSpider 通用爬取邏輯正常")
