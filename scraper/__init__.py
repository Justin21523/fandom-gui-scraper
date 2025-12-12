# scraper/__init__.py
"""
Fandom Scraper package.

This package provides web scraping functionality for extracting
anime character data from Fandom wiki sites.

Available Spiders:
    - BaseSpider: Abstract base spider with common functionality
    - FandomSpider: Generic Fandom wiki spider
    - OnePieceSpider: Specialized One Piece spider
    - NarutoSpider: Specialized Naruto spider
    - DragonBallSpider: Specialized Dragon Ball spider

Usage:
    from scraper import OnePieceSpider, NarutoSpider, DragonBallSpider

    # Run with Scrapy
    scrapy crawl onepiece
    scrapy crawl naruto
    scrapy crawl dragonball
"""

from scraper.base_spider import BaseSpider
from scraper.fandom_spider import FandomSpider
from scraper.onepiece_spider import OnePieceSpider
from scraper.naruto_spider import NarutoSpider
from scraper.dragonball_spider import DragonBallSpider

__all__ = [
    "BaseSpider",
    "FandomSpider",
    "OnePieceSpider",
    "NarutoSpider",
    "DragonBallSpider",
]
