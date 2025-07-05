# models/storage.py
# -*- coding: utf-8 -*-
import os
import sys
# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Optional, List, Dict
from models.document import AnimePage

class MongoStorage:
    """
    負責跟 MongoDB 互動的 CRUD 操作
    """
    def __init__(self, uri: str = "mongodb://localhost:27017",
                       db_name: str = "fandom_scraper",
                       collection_name: str = "pages"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.col: Collection = self.db[collection_name]

    def insert_page(self, page: AnimePage) -> str:
        """新增一筆 AnimePage，回傳 inserted_id"""
        doc = page.dict()
        result = self.col.insert_one(doc)
        return str(result.inserted_id)

    def get_page_by_title(self, title: str) -> Optional[Dict]:
        """依 title 查詢一筆資料，回傳原始 dict"""
        return self.col.find_one({"title": title})

    def update_page(self, title: str, data: Dict) -> int:
        """依 title 更新資料欄位，回傳 modified_count"""
        result = self.col.update_one({"title": title}, {"$set": data})
        return result.modified_count

    def delete_page(self, title: str) -> int:
        """依 title 刪除一筆，回傳 deleted_count"""
        result = self.col.delete_one({"title": title})
        return result.deleted_count

    def list_titles(self) -> List[str]:
        """回傳所有 title 清單"""
        return [doc["title"] for doc in self.col.find({}, {"title": 1})]


if __name__ == "__main__":
    print("▶ 測試 MongoStorage")
    # 連到本地 test DB
    storage = MongoStorage(db_name="test_db", collection_name="test_coll")
    page = AnimePage(title="T", content_paragraphs=["a","b"])
    _id = storage.insert_page(page)
    print("  插入 ID:", _id)
    doc = storage.get_page_by_title("T")
    print("  讀取結果:", doc)
    storage.delete_page("T")
    print("✅ MongoStorage OK")
