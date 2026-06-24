# scraper/__init__.py
"""Fandom scraper package.

Spider classes are loaded lazily so importing `scraper.settings` does not load
every model and spider. Direct imports from concrete modules still work.
"""

__all__ = [
    "BaseSpider",
    "FandomSpider",
    "OnePieceSpider",
    "NarutoSpider",
    "DragonBallSpider",
]

_LAZY_IMPORTS = {
    "BaseSpider": ("scraper.base_spider", "BaseSpider"),
    "FandomSpider": ("scraper.fandom_spider", "FandomSpider"),
    "OnePieceSpider": ("scraper.onepiece_spider", "OnePieceSpider"),
    "NarutoSpider": ("scraper.naruto_spider", "NarutoSpider"),
    "DragonBallSpider": ("scraper.dragonball_spider", "DragonBallSpider"),
}


def __getattr__(name: str):
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module 'scraper' has no attribute {name!r}")
    module_name, attr_name = _LAZY_IMPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
