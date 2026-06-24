from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .errors import InvalidWikiTargetError


@dataclass(frozen=True)
class WikiTarget:
    original: str
    base_url: str
    api_url: str
    host: str
    article_path: str | None = None
    is_fandom: bool = False


def _ensure_http_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise InvalidWikiTargetError("Wiki target is required")
    if value.startswith(("http://", "https://")):
        return value
    if ".fandom.com" in value:
        return f"https://{value}"
    raise InvalidWikiTargetError("Generic MediaWiki targets must be explicit http(s) api.php endpoints")


def normalize_wiki_target(value: str) -> WikiTarget:
    """正規化 Fandom URL 或明確的 MediaWiki api.php endpoint。"""
    original = value
    url = _ensure_http_url(value)
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidWikiTargetError(f"Invalid wiki target: {original}")

    host = parsed.netloc.lower()
    path = parsed.path or ""
    is_fandom = host.endswith(".fandom.com")

    if is_fandom:
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        article_path = path if path.startswith("/wiki/") else None
        return WikiTarget(
            original=original,
            base_url=base_url,
            api_url=f"{base_url}/api.php",
            host=host,
            article_path=article_path,
            is_fandom=True,
        )

    if path.rstrip("/").endswith("/api.php") or path == "/api.php":
        api_path = path.rstrip("/")
        base_path = api_path[: -len("/api.php")] or ""
        base_url = f"{parsed.scheme}://{parsed.netloc}{base_path}".rstrip("/")
        return WikiTarget(
            original=original,
            base_url=base_url,
            api_url=f"{parsed.scheme}://{parsed.netloc}{api_path}",
            host=host,
            article_path=None,
            is_fandom=False,
        )

    raise InvalidWikiTargetError("Non-Fandom MediaWiki targets must point to api.php")
