from __future__ import annotations

from unittest.mock import Mock

import pytest

from scraper.mediawiki import (
    AccessRestrictedError,
    InvalidWikiTargetError,
    MediaWikiActionClient,
    RobotsDeniedError,
    normalize_wiki_target,
)


class FakeResponse:
    def __init__(self, status_code=200, text="", payload=None):
        self.status_code = status_code
        self.text = text
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def make_session(*responses):
    session = Mock()
    session.get.side_effect = list(responses)
    return session


class TestWikiTargetNormalization:
    def test_normalizes_fandom_base_url(self):
        target = normalize_wiki_target("https://onepiece.fandom.com")

        assert target.base_url == "https://onepiece.fandom.com"
        assert target.api_url == "https://onepiece.fandom.com/api.php"
        assert target.host == "onepiece.fandom.com"
        assert target.article_path is None
        assert target.is_fandom is True

    def test_normalizes_fandom_page_url_without_scheme(self):
        target = normalize_wiki_target("onepiece.fandom.com/wiki/Main_Page")

        assert target.base_url == "https://onepiece.fandom.com"
        assert target.api_url == "https://onepiece.fandom.com/api.php"
        assert target.article_path == "/wiki/Main_Page"

    def test_normalizes_generic_mediawiki_api_endpoint(self):
        target = normalize_wiki_target("https://wiki.example.org/w/api.php")

        assert target.base_url == "https://wiki.example.org/w"
        assert target.api_url == "https://wiki.example.org/w/api.php"
        assert target.is_fandom is False

    def test_rejects_generic_non_api_url(self):
        with pytest.raises(InvalidWikiTargetError):
            normalize_wiki_target("https://wiki.example.org/wiki/Main_Page")

    def test_rejects_empty_target(self):
        with pytest.raises(InvalidWikiTargetError):
            normalize_wiki_target("  ")


class TestMediaWikiActionClient:
    def test_build_query_url_adds_json_defaults(self):
        client = MediaWikiActionClient("https://onepiece.fandom.com", respect_robots=False, rate_delay=0)

        url = client.build_query_url({"action": "query", "meta": "siteinfo"})

        assert url.startswith("https://onepiece.fandom.com/api.php?")
        assert "format=json" in url
        assert "formatversion=2" in url
        assert "action=query" in url
        assert "meta=siteinfo" in url

    def test_build_categorymembers_url_includes_continue(self):
        client = MediaWikiActionClient("https://onepiece.fandom.com", respect_robots=False, rate_delay=0)

        url = client.build_categorymembers_url("Category:Characters", cmcontinue="next-page")

        assert "list=categorymembers" in url
        assert "cmtitle=Category%3ACharacters" in url
        assert "cmnamespace=0%7C14" in url
        assert "cmcontinue=next-page" in url

    def test_iter_category_members_follows_cmcontinue(self):
        session = make_session(
            FakeResponse(text="User-agent: *\nAllow: /\n"),
            FakeResponse(
                payload={
                    "query": {"categorymembers": [{"title": "Page A", "ns": 0}]},
                    "continue": {"cmcontinue": "cursor"},
                }
            ),
            FakeResponse(payload={"query": {"categorymembers": [{"title": "Page B", "ns": 0}]}}),
        )
        client = MediaWikiActionClient("https://onepiece.fandom.com", session=session, rate_delay=0)

        members = list(client.iter_category_members("Category:Characters"))

        assert [member["title"] for member in members] == ["Page A", "Page B"]
        assert session.get.call_count == 3

    def test_query_pages_requires_titles_or_pageids(self):
        client = MediaWikiActionClient("https://onepiece.fandom.com", respect_robots=False, rate_delay=0)

        with pytest.raises(Exception, match="query_pages requires"):
            client.query_pages()

    def test_query_pages_posts_expected_props(self):
        session = make_session(
            FakeResponse(text="User-agent: *\nAllow: /\n"),
            FakeResponse(payload={"query": {"pages": []}}),
        )
        client = MediaWikiActionClient("https://onepiece.fandom.com", session=session, rate_delay=0)

        payload = client.query_pages(titles=["Monkey D. Luffy"])

        assert payload == {"query": {"pages": []}}
        api_url = session.get.call_args_list[-1].args[0]
        assert "prop=info%7Crevisions%7Ccategories" in api_url
        assert "rvprop=ids%7Ctimestamp%7Cuser%7Csize" in api_url
        assert "titles=Monkey+D.+Luffy" in api_url

    def test_robots_denied_raises(self):
        session = make_session(FakeResponse(text="User-agent: *\nDisallow: /api.php\n"))
        client = MediaWikiActionClient("https://onepiece.fandom.com", session=session, rate_delay=0)

        with pytest.raises(RobotsDeniedError):
            client.get_siteinfo()

    @pytest.mark.parametrize("status_code", [403, 429])
    def test_access_restricted_status_raises(self, status_code):
        session = make_session(FakeResponse(status_code=status_code, text="restricted"))
        client = MediaWikiActionClient(
            "https://onepiece.fandom.com",
            session=session,
            respect_robots=False,
            rate_delay=0,
        )

        with pytest.raises(AccessRestrictedError):
            client.get_siteinfo()

    def test_access_restricted_body_marker_raises(self):
        session = make_session(FakeResponse(status_code=200, text="captcha required"))
        client = MediaWikiActionClient(
            "https://onepiece.fandom.com",
            session=session,
            respect_robots=False,
            rate_delay=0,
        )

        with pytest.raises(AccessRestrictedError):
            client.get_siteinfo()
