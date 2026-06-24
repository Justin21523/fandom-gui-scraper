"""MediaWiki Action API helpers for Fandom and generic MediaWiki sites."""

from .client import MediaWikiActionClient
from .errors import (
    AccessRestrictedError,
    InvalidWikiTargetError,
    MediaWikiAPIError,
    RobotsDeniedError,
)
from .repository import WikiSQLiteRepository
from .target import WikiTarget, normalize_wiki_target

__all__ = [
    "AccessRestrictedError",
    "HarvestConfig",
    "InvalidWikiTargetError",
    "MediaWikiAPIError",
    "MediaWikiActionClient",
    "MediaWikiHarvester",
    "RobotsDeniedError",
    "WikiTarget",
    "WikiSQLiteRepository",
    "harvest_to_sqlite",
    "normalize_wiki_target",
]


def __getattr__(name):
    if name in {"HarvestConfig", "MediaWikiHarvester", "harvest_to_sqlite"}:
        from . import harvester

        return getattr(harvester, name)
    raise AttributeError(name)
