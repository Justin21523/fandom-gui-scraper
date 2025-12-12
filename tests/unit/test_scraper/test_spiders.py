# tests/unit/test_scraper/test_spiders.py
"""
Unit tests for spider modules.

Tests spider class attributes and basic configuration.
"""

import pytest


class TestNarutoSpider:
    """Tests for NarutoSpider class."""

    def test_spider_name(self):
        """Test spider has correct name."""
        from scraper.naruto_spider import NarutoSpider
        assert NarutoSpider.name == "naruto"

    def test_allowed_domains(self):
        """Test spider has correct allowed domains."""
        from scraper.naruto_spider import NarutoSpider
        assert "naruto.fandom.com" in NarutoSpider.allowed_domains

    def test_start_urls(self):
        """Test spider has start URLs defined."""
        from scraper.naruto_spider import NarutoSpider
        assert len(NarutoSpider.start_urls) > 0
        assert "naruto.fandom.com" in NarutoSpider.start_urls[0]


class TestDragonBallSpider:
    """Tests for DragonBallSpider class."""

    def test_spider_name(self):
        """Test spider has correct name."""
        from scraper.dragonball_spider import DragonBallSpider
        assert DragonBallSpider.name == "dragonball"

    def test_allowed_domains(self):
        """Test spider has correct allowed domains."""
        from scraper.dragonball_spider import DragonBallSpider
        assert "dragonball.fandom.com" in DragonBallSpider.allowed_domains

    def test_start_urls(self):
        """Test spider has start URLs defined."""
        from scraper.dragonball_spider import DragonBallSpider
        assert len(DragonBallSpider.start_urls) > 0
        assert "dragonball.fandom.com" in DragonBallSpider.start_urls[0]

    def test_parse_power_level_function(self):
        """Test power level parsing logic."""
        import re

        def parse_power_level(power_level_str):
            try:
                cleaned = re.sub(r"[^\d]", "", power_level_str)
                if cleaned:
                    return int(cleaned)
            except (ValueError, TypeError):
                pass
            return None

        assert parse_power_level("9,000") == 9000
        assert parse_power_level("Over 9000!") == 9000
        assert parse_power_level("1,500,000") == 1500000
        assert parse_power_level("Unknown") is None
        assert parse_power_level("") is None


class TestOnePieceSpider:
    """Tests for OnePieceSpider class."""

    def test_spider_name(self):
        """Test spider has correct name."""
        from scraper.onepiece_spider import OnePieceSpider
        assert OnePieceSpider.name == "onepiece"


class TestFandomSpider:
    """Tests for base FandomSpider class."""

    def test_spider_name(self):
        """Test spider has correct name."""
        from scraper.fandom_spider import FandomSpider
        assert FandomSpider.name == "fandom"


class TestSpiderImports:
    """Tests for spider module imports."""

    def test_can_import_all_spiders(self):
        """Test that all spiders can be imported."""
        from scraper import (
            BaseSpider,
            FandomSpider,
            OnePieceSpider,
            NarutoSpider,
            DragonBallSpider,
        )

        assert BaseSpider is not None
        assert FandomSpider is not None
        assert OnePieceSpider is not None
        assert NarutoSpider is not None
        assert DragonBallSpider is not None

    def test_spider_names_unique(self):
        """Test that all spiders have unique names."""
        from scraper.onepiece_spider import OnePieceSpider
        from scraper.naruto_spider import NarutoSpider
        from scraper.dragonball_spider import DragonBallSpider

        names = [OnePieceSpider.name, NarutoSpider.name, DragonBallSpider.name]
        assert len(names) == len(set(names))

    def test_spider_inheritance(self):
        """Test that specialized spiders inherit from FandomSpider."""
        from scraper.fandom_spider import FandomSpider
        from scraper.onepiece_spider import OnePieceSpider
        from scraper.naruto_spider import NarutoSpider
        from scraper.dragonball_spider import DragonBallSpider

        assert issubclass(OnePieceSpider, FandomSpider)
        assert issubclass(NarutoSpider, FandomSpider)
        assert issubclass(DragonBallSpider, FandomSpider)
