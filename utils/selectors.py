# utils/selectors.py
# -*- coding: utf-8 -*-
"""
管理各動畫的 CSS/XPath selector，
外部只要用 anime_name 拿到對應的設定。
"""

from typing import Dict

selectors: dict[str, dict[str, dict[str, str]]] = {
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
        }
    },
    # 未來可依 domain 或 fandom 名稱，覆寫或擴充特定站點的 selectors
    "starwars": { ... },
    "got":      { ... }
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
