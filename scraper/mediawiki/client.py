from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, Iterator, Mapping, Sequence
from urllib.parse import urlencode
from urllib.robotparser import RobotFileParser

import requests

from .errors import AccessRestrictedError, MediaWikiAPIError, RobotsDeniedError
from .target import WikiTarget, normalize_wiki_target


RESTRICTION_MARKERS = (
    "captcha",
    "cf-browser-verification",
    "attention required",
    "rate limit",
    "too many requests",
)


class MediaWikiActionClient:
    """Small synchronous MediaWiki Action API client."""

    def __init__(
        self,
        target: str | WikiTarget,
        *,
        session: requests.Session | None = None,
        user_agent: str = "FandomGuiScraper/1.0 (+https://github.com/user/fandom-gui-scraper)",
        timeout: float = 30.0,
        rate_delay: float = 1.0,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        respect_robots: bool = True,
    ):
        self.target = normalize_wiki_target(target) if isinstance(target, str) else target
        self.session = session or requests.Session()
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_delay = rate_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.respect_robots = respect_robots
        self._last_request_at = 0.0
        self._robots_checked: dict[str, bool] = {}

    def build_query_url(self, params: Mapping[str, Any]) -> str:
        query = self._with_defaults(params)
        return f"{self.target.api_url}?{urlencode(query, doseq=True)}"

    def build_categorymembers_url(self, category_title: str, cmcontinue: str | None = None) -> str:
        return self.build_query_url(self.categorymembers_params(category_title, cmcontinue=cmcontinue))

    def get_siteinfo(self) -> Dict[str, Any]:
        return self.get(
            {
                "action": "query",
                "meta": "siteinfo",
                "siprop": "general|namespaces",
            }
        )

    def iter_category_members(
        self,
        category_title: str,
        *,
        namespaces: Sequence[int | str] = (0, 14),
        limit: int = 500,
    ) -> Iterator[Dict[str, Any]]:
        cmcontinue = None
        while True:
            payload = self.get(
                self.categorymembers_params(
                    category_title,
                    namespaces=namespaces,
                    limit=limit,
                    cmcontinue=cmcontinue,
                )
            )
            members = ((payload.get("query") or {}).get("categorymembers")) or []
            yield from members

            cmcontinue = (payload.get("continue") or {}).get("cmcontinue")
            if not cmcontinue:
                break

    def query_pages(
        self,
        *,
        titles: Iterable[str] | None = None,
        pageids: Iterable[int | str] | None = None,
        props: Sequence[str] = ("info", "revisions", "categories"),
        rvprop: Sequence[str] = ("ids", "timestamp", "user", "size"),
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "action": "query",
            "prop": "|".join(props),
            "rvprop": "|".join(rvprop),
        }
        if titles:
            params["titles"] = "|".join(titles)
        if pageids:
            params["pageids"] = "|".join(str(pageid) for pageid in pageids)
        if "titles" not in params and "pageids" not in params:
            raise MediaWikiAPIError("query_pages requires titles or pageids")
        return self.get(params)

    def get(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        url = self.build_query_url(params)
        self._check_robots(url)
        self._wait_for_rate_limit()

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                    timeout=self.timeout,
                )
                self._raise_for_restriction(response.status_code, response.text)
                if response.status_code >= 500:
                    raise MediaWikiAPIError(f"MediaWiki API HTTP {response.status_code}")
                response.raise_for_status()
                payload = response.json()
                if "error" in payload:
                    error = payload["error"]
                    raise MediaWikiAPIError(error.get("info") or error.get("code") or "MediaWiki API error")
                return payload
            except AccessRestrictedError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(60.0, self.backoff_factor**attempt))

        raise MediaWikiAPIError(str(last_error) if last_error else "MediaWiki API request failed")

    @staticmethod
    def categorymembers_params(
        category_title: str,
        *,
        namespaces: Sequence[int | str] = (0, 14),
        limit: int = 500,
        cmcontinue: str | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": limit,
            "cmnamespace": "|".join(str(ns) for ns in namespaces),
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        return params

    @staticmethod
    def extract_category_members(payload: Mapping[str, Any]) -> list[Dict[str, Any]]:
        return list(((payload.get("query") or {}).get("categorymembers")) or [])

    @staticmethod
    def extract_cmcontinue(payload: Mapping[str, Any]) -> str | None:
        return (payload.get("continue") or {}).get("cmcontinue")

    def _with_defaults(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        query = {
            "format": "json",
            "formatversion": "2",
        }
        query.update(dict(params))
        return query

    def _wait_for_rate_limit(self) -> None:
        if self.rate_delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.rate_delay:
            time.sleep(self.rate_delay - elapsed)
        self._last_request_at = time.monotonic()

    def _check_robots(self, url: str) -> None:
        if not self.respect_robots:
            return
        if self.target.host in self._robots_checked:
            if not self._robots_checked[self.target.host]:
                raise RobotsDeniedError(f"robots.txt disallows {url}")
            return

        robots_url = f"{self.target.base_url}/robots.txt"
        parser = RobotFileParser()
        try:
            response = self.session.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                self._robots_checked[self.target.host] = True
                return
            parser.parse(response.text.splitlines())
            allowed = parser.can_fetch(self.user_agent, url)
        except Exception:
            allowed = True

        self._robots_checked[self.target.host] = allowed
        if not allowed:
            raise RobotsDeniedError(f"robots.txt disallows {url}")

    def _raise_for_restriction(self, status_code: int, body: str) -> None:
        body_lower = (body or "").lower()
        if status_code in (403, 429) or any(marker in body_lower for marker in RESTRICTION_MARKERS):
            raise AccessRestrictedError(f"Access restricted by remote site: HTTP {status_code}")

        # 某些保護頁會回 HTML 但狀態碼為 200；避免當作 JSON 繼續處理。
        if body and body.lstrip().startswith("<"):
            try:
                json.loads(body)
            except Exception:
                if "api.php" in body_lower and "mediawiki" not in body_lower:
                    raise AccessRestrictedError("Unexpected HTML response from MediaWiki API")
