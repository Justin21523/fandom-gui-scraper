# models/document.py
# -*- coding: utf-8 -*-
import os
import sys
# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import List, Optional

class AnimePage(BaseModel):
    """
    定義一頁 Fandom 動畫條目的資料結構
    """
    title: str = Field(..., description="頁面標題")
    content_paragraphs: List[str] = Field(..., description="文字段落清單")
    image_urls: List[HttpUrl] = Field(default_factory=list, description="圖片網址清單")
    categories: List[str] = Field(default_factory=list, description="分類連結或名稱")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="抓取時間")

    class Config:
        # 允許轉成 dict 時，自動把 datetime 轉成 ISO 格式
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
