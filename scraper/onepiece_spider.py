# scraper/onepiece_spider.py
# -*- coding: utf-8 -*-
import os
import sys
# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import scrapy
from scrapy.http import TextResponse
import requests
from utils.selectors import selectors
from utils.normalizer import clean_text
from scraper.fandom_spider import FandomSpider

class OnePieceSpider(FandomSpider):
    """
    OnePieceSpider 繼承自 FandomSpider，用於解析 One Piece Wiki 特有欄位。
    """
    name = "onepiece_spider"

    def __init__(self, start_urls=None, *args, **kwargs):
        # 指定 site 為 "onepiece"，載入 utils/selectors.py 中的配置
        super().__init__(site="onepiece", start_urls=start_urls, *args, **kwargs)

    def parse(self, response: scrapy.http.Response):
        # 先呼叫父類 parse() 產生通用欄位
        for item in super().parse(response):
            # 取得 onepiece 特有的 selectors 設定
            conf = selectors.get('onepiece', {})

            # 處理人物列表 (characters)
            chars = (
                response.css(conf['characters']['css']).getall() or
                response.xpath(conf['characters']['xpath']).getall()
            )
            item['characters'] = [clean_text(c) for c in chars if clean_text(c)]

            # 處理首播日期 (first_release)
            first = (
                response.css(conf['first_release']['css']).get() or
                response.xpath(conf['first_release']['xpath']).get()
            )
            item['first_release'] = clean_text(first)

            yield item

if __name__ == '__main__':
    # 簡易自測：用 requests + TextResponse 模擬 Scrapy
    url = 'https://onepiece.fandom.com/wiki/Luffy'
    html = requests.get(url).text
    resp = TextResponse(url, body=html, encoding='utf-8')

    spider = OnePieceSpider(start_urls=[url], name='test_onepiece')
    for page in spider.parse(resp):
        print('\n=== One Piece Page Data ===')
        for k, v in page.items():
            print(f"{k}: {v if not isinstance(v, list) else v[:5]}")
    print("\n✅ OnePieceSpider OK")
