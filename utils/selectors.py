# utils/selectors.py
# -*- coding: utf-8 -*-
"""
管理各動畫的 CSS/XPath selector，
外部只要用 anime_name 拿到對應的設定。
"""

from typing import Dict

selectors: Dict[str, Dict[str, Dict[str, str]]] = {
    "default": {
        "title": {
            "css": "h1.page-header__title::text",
            "xpath": "//h1[@class='page-header__title']/text()"
        },
        "content_paragraphs": {
            "css": "div.mw-parser-output > p::text",
            "xpath": "//div[contains(@class,'mw-parser-output')]/p/text()"
        },
        "infobox": {
            "css": "table.infobox, aside.portable-infobox",
            "xpath": "//table[contains(@class,'infobox')] | //aside[contains(@class,'portable-infobox')]"
        },
        "infobox_fields": {
            "css": "aside.portable-infobox .pi-item",
            "xpath": "//aside[contains(@class,'portable-infobox')]//section[contains(@class,'pi-item')]"
        },
        "image_urls": {
            "css": "aside.portable-infobox img::attr(src), div.mw-parser-output img::attr(src)",
            "xpath": "//aside[contains(@class,'portable-infobox')]//img/@src | //div[contains(@class,'mw-parser-output')]//img/@src"
        },
        "categories": {
            "css": "#catlinks li a::attr(href)",
            "xpath": "//div[@id='catlinks']//li/a/@href"
        },
    },

    # **只更新這邊**：移除 :has()、:contains()  等不支援的 CSS，改用最簡單能選到的元素
    "onepiece": {
        "title": {
            "css": "h1.page-header__title::text",
            "xpath": "//h1[contains(@class,'page-header__title')]/text()"
        },
        "synopsis": {
            "css": "div.mw-parser-output > p::text",
            "xpath": "//div[contains(@class,'mw-parser-output')]/p[1]/text()"
        },
        "image_urls": {
            "css": "aside.portable-infobox img::attr(src)",
            "xpath": "//aside[contains(@class,'portable-infobox')]//img/@src"
        },
        # 原本的複雜 CSS 改成「選出所有 infobox 內 <a> 文字」
        "characters": {
            "css": "table.infobox td a::text",
            "xpath": "//table[contains(@class,'infobox')]//tr[th/text()='Characters']/td//a/text()"
        },
        # 讓 CSS 空白，統一走 XPath
        "first_release": {
            "css": "",
            "xpath": "//table[contains(@class,'infobox')]//tr[th/text()='First appearance']/td/text()"
        },
    }
}

def get_selector(anime: str, field: str) -> str:
    """
    取得指定動畫、指定欄位的 selector 字串。
    若找不到，拋出 KeyError。
    """
    try:
        return selectors[anime][field]
    except KeyError as e:
        raise KeyError(f"找不到動畫 {anime} 的欄位 {field} 的 selector") from e

def get_selector(site: str, field: str, method="css") -> str:

    """
    取得指定頁面、指定欄位的 selector 字串。
    若找不到，拋出 KeyError。
    """
    try:
        cfg = selectors[site][field]
    except KeyError as e:
        raise KeyError(f"找不到網站 {site} 的欄位 {field} 的 selector") from e
    return cfg.get(method)


if __name__ == "__main__":
    # 用最簡單的 assert 測試
    print("▶ 測試 get_selector")
    assert get_selector("default", "title") == "h1.page-header__title::text"
    print("✅ selectors OK")
