# utils/normalizer.py
# -*- coding: utf-8 -*-
"""
欄位標準化與文本清洗工具
"""
import re
from typing import Optional


def clean_text(text: Optional[str]) -> str:
    """
    清洗文字：
      1. 若為 None，回傳空字串
      2. 去除首尾空白與換行
      3. 合併多重空白為單一空格
      4. 移除 HTML 標籤
    """
    if not text:
        return ""

    # 1. 去除 HTML 標籤
    text = re.sub(r"<[^>]+>", "", text)
    # 2. 去首尾空白與換行
    text = text.strip()
    # 3. 合併多空白為單一空格
    text = re.sub(r"\s+", " ", text)

    return text


def normalize_date(date_str: str) -> str:
    """
    範例：將 \"2023年 7月 10 日\" 統一成 \"2023-07-10\"
    若格式不符，原樣回傳
    """
    m = re.match(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", date_str)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return date_str

if __name__ == "__main__":
    print("▶ 測試 clean_text")
    assert clean_text("  Hello \nWorld ") == "Hello World"
    print("✅ clean_text OK")
