from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List


class _InfoboxHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows: List[Dict[str, str]] = []
        self._in_infobox = False
        self._depth = 0
        self._current_field: str | None = None
        self._current_value: List[str] = []
        self._capture_label = False
        self._capture_value = False
        self._buffer: List[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")
        is_infobox = "portable-infobox" in classes or "infobox" in classes
        if not self._in_infobox and is_infobox:
            self._in_infobox = True
            self._depth = 1
            return
        if self._in_infobox:
            self._depth += 1
            if "pi-data-label" in classes or tag in {"th", "dt"}:
                self._capture_label = True
                self._buffer = []
            elif "pi-data-value" in classes or tag in {"td", "dd"}:
                self._capture_value = True
                self._buffer = []

    def handle_endtag(self, tag):
        if not self._in_infobox:
            return
        if self._capture_label and tag in {"h3", "div", "th", "dt"}:
            text = _clean(" ".join(self._buffer))
            if text:
                self._current_field = text
            self._capture_label = False
            self._buffer = []
        elif self._capture_value and tag in {"div", "td", "dd"}:
            text = _clean(" ".join(self._buffer))
            if text:
                self._current_value.append(text)
            self._capture_value = False
            self._buffer = []
            self._flush_row()
        self._depth -= 1
        if self._depth <= 0:
            self._in_infobox = False

    def handle_data(self, data):
        if self._in_infobox and (self._capture_label or self._capture_value):
            self._buffer.append(data)

    def _flush_row(self):
        if not self._current_field or not self._current_value:
            return
        self.rows.append(
            {
                "field_name": self._current_field,
                "field_value": _clean(" | ".join(self._current_value)),
                "source": "html_infobox",
            }
        )
        self._current_field = None
        self._current_value = []


def _clean(value: str) -> str:
    value = unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def parse_infobox_fields(html: str) -> List[Dict[str, str]]:
    if not html:
        return []
    parser = _InfoboxHTMLParser()
    parser.feed(html)
    seen = set()
    rows: List[Dict[str, str]] = []
    for row in parser.rows:
        key = (row["field_name"].lower(), row["field_value"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    return rows
