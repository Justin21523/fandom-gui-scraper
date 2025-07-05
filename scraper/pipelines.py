# scraper/pipelines.py
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import os
import sys
# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request
from models.document import AnimePage
from models.storage import MongoStorage
from scrapy.exceptions import DropItem
from urllib.parse import urlparse


class FandomImagesPipeline(ImagesPipeline):
    """
    繼承 Scrapy 的 ImagesPipeline，自動下載 item['image_urls'] 中的圖片。
    """
    def get_media_requests(self, item, info):
        for url in item.get("image_urls", []):
            yield Request(url)

    def file_path(self, request, response=None, info=None, *, item=None):
        # 自訂下載路徑：images/<title>/<filename>
        parsed = urlparse(request.url)
        filename = os.path.basename(parsed.path)
        title = item.get("title", "unknown").replace(" ", "_")
        return f"images/{title}/{filename}"


class MongoPipeline:
    """
    把清理、下載完圖片的 item 寫入 MongoDB。
    """
    def __init__(self, uri=None, db_name=None, collection=None):
        # 你可以從 settings.py 用 get() 讀取，或用預設
        self.storage = MongoStorage(
            uri=uri or "mongodb://localhost:27017",
            db_name=db_name or "fandom_scraper",
            collection_name=collection or "pages"
        )

    @classmethod
    def from_crawler(cls, crawler):
        # 從 settings.py 讀取參數
        return cls(
            uri=crawler.settings.get("MONGO_URI"),
            db_name=crawler.settings.get("MONGO_DB"),
            collection=crawler.settings.get("MONGO_COLLECTION")
        )

    def process_item(self, item, spider):
        # 只處理結構正確的 dict item
        try:
            page = AnimePage(**item)
        except Exception as e:
            raise DropItem(f"Invalid item: {e}")

        # 寫入 MongoDB
        inserted_id = self.storage.insert_page(page)
        spider.logger.info(f"Stored page {page.title} with id {inserted_id}")
        return item


if __name__ == "__main__":
    # 測試 MongoPipeline
    sample = {
        "title": "Test",
        "content_paragraphs": ["p1", "p2"],
        "image_urls": [],
        "categories": ["Cat"],
    }
    pipe = MongoPipeline()
    print("Inserted ID:", pipe.storage.insert_page(AnimePage(**sample)))
    print("Fetched:", pipe.storage.get_page_by_title("Test"))
    pipe.storage.delete_page("Test")
    print("✅ MongoPipeline OK")
