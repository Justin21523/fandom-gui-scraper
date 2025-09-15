# scraper/utils/response_parser.py
"""
Response parsing utilities for web scraping.

This module provides utilities to parse HTML responses,
extract data using CSS selectors and XPath, and handle
common parsing tasks for Fandom wikis.
"""

import re
import json
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin, urlparse
from scrapy import Selector
from scrapy.http import Response
from w3lib.html import remove_tags
import logging

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    Parse HTML responses and extract structured data.

    This class provides methods to extract common data patterns
    from web pages using CSS selectors and XPath expressions.
    """

    def __init__(self, response: Response):
        """
        Initialize the parser with a response.

        Args:
            response: Scrapy Response object
        """
        self.response = response
        self.selector = Selector(response)  # type: ignore
        self.url = response.url
        self.base_url = (
            f"{urlparse(response.url).scheme}://{urlparse(response.url).netloc}"
        )

    def extract_text(
        self, selector_path: str, clean: bool = True, join_text: str = " "
    ) -> Optional[str]:
        """
        Extract text content using CSS selector or XPath.

        Args:
            selector_path: CSS selector or XPath expression
            clean: Whether to clean extracted text
            join_text: String to join multiple text elements

        Returns:
            Extracted text or None if not found
        """
        try:
            if selector_path.startswith(("/", "//")):
                # XPath expression
                elements = self.selector.xpath(selector_path)
            else:
                # CSS selector
                elements = self.selector.css(selector_path)

            if elements:
                texts = elements.getall()
                if clean:
                    texts = [self.clean_text(text) for text in texts if text.strip()]

                if texts:
                    return join_text.join(texts)

        except Exception as e:
            logger.warning(
                f"Error extracting text with selector '{selector_path}': {e}"
            )

        return None

    def extract_first_text(
        self, selector_path: str, clean: bool = True
    ) -> Optional[str]:
        """
        Extract first text match using CSS selector or XPath.

        Args:
            selector_path: CSS selector or XPath expression
            clean: Whether to clean extracted text

        Returns:
            First extracted text or None if not found
        """
        try:
            if selector_path.startswith(("/", "//")):
                # XPath expression
                element = self.selector.xpath(selector_path).get()
            else:
                # CSS selector
                element = self.selector.css(selector_path).get()

            if element:
                text = remove_tags(element) if clean else element
                return self.clean_text(text) if clean else text

        except Exception as e:
            logger.warning(
                f"Error extracting first text with selector '{selector_path}': {e}"
            )

        return None

    def extract_list(
        self, selector_path: str, clean: bool = True, filter_empty: bool = True
    ) -> List[str]:
        """
        Extract list of text elements.

        Args:
            selector_path: CSS selector or XPath expression
            clean: Whether to clean extracted text
            filter_empty: Whether to filter out empty strings

        Returns:
            List of extracted text elements
        """
        try:
            if selector_path.startswith(("/", "//")):
                # XPath expression
                elements = self.selector.xpath(selector_path).getall()
            else:
                # CSS selector
                elements = self.selector.css(selector_path).getall()

            if clean:
                elements = [self.clean_text(remove_tags(elem)) for elem in elements]

            if filter_empty:
                elements = [elem for elem in elements if elem and elem.strip()]

            return elements

        except Exception as e:
            logger.warning(
                f"Error extracting list with selector '{selector_path}': {e}"
            )
            return []

    def extract_attributes(self, selector_path: str, attribute: str) -> List[str]:
        """
        Extract attribute values from elements.

        Args:
            selector_path: CSS selector or XPath expression
            attribute: Attribute name to extract

        Returns:
            List of attribute values
        """
        try:
            if selector_path.startswith(("/", "//")):
                # XPath expression
                attrs = self.selector.xpath(f"{selector_path}/@{attribute}").getall()
            else:
                # CSS selector
                attrs = self.selector.css(f"{selector_path}::{attribute}").getall()

            return [attr.strip() for attr in attrs if attr and attr.strip()]

        except Exception as e:
            logger.warning(
                f"Error extracting attributes with selector '{selector_path}': {e}"
            )
            return []

    def extract_urls(self, selector_path: str, make_absolute: bool = True) -> List[str]:
        """
        Extract URLs from href or src attributes.

        Args:
            selector_path: CSS selector for elements with URLs
            make_absolute: Whether to convert relative URLs to absolute

        Returns:
            List of URLs
        """
        # Try href first, then src
        urls = []

        # Extract href attributes
        href_urls = self.extract_attributes(selector_path, "href")
        urls.extend(href_urls)

        # Extract src attributes
        src_urls = self.extract_attributes(selector_path, "src")
        urls.extend(src_urls)

        if make_absolute:
            urls = [urljoin(self.url, url) for url in urls]

        # Filter out invalid URLs
        return [
            url
            for url in urls
            if url and not url.startswith(("javascript:", "mailto:", "#"))
        ]

    def extract_images(
        self, selector_path: str = "img", make_absolute: bool = True
    ) -> List[Dict[str, str]]:
        """
        Extract image information including src, alt, and title.

        Args:
            selector_path: CSS selector for image elements
            make_absolute: Whether to convert relative URLs to absolute

        Returns:
            List of image dictionaries with src, alt, title, etc.
        """
        images = []

        try:
            img_elements = self.selector.css(selector_path)

            for img in img_elements:
                src = img.css("::attr(src)").get()
                if not src:
                    continue

                if make_absolute:
                    src = urljoin(self.url, src)

                image_data = {
                    "src": src,
                    "alt": img.css("::attr(alt)").get() or "",
                    "title": img.css("::attr(title)").get() or "",
                    "width": img.css("::attr(width)").get(),
                    "height": img.css("::attr(height)").get(),
                    "class": img.css("::attr(class)").get() or "",
                }

                # Extract data-* attributes
                for attr in img.css("::attr(*)").getall():
                    if "data-" in str(attr):
                        attr_name = (
                            img.css("::attr(*)").re(r"data-([^=]+)")[0]
                            if img.css("::attr(*)").re(r"data-([^=]+)")
                            else None
                        )
                        if attr_name:
                            image_data[f"data_{attr_name}"] = attr

                images.append(image_data)

        except Exception as e:
            logger.warning(f"Error extracting images: {e}")

        return images

    def extract_json_ld(self) -> List[Dict]:
        """
        Extract JSON-LD structured data from the page.

        Returns:
            List of JSON-LD objects
        """
        json_ld_data = []

        try:
            json_scripts = self.selector.css(
                'script[type="application/ld+json"]::text'
            ).getall()

            for script_content in json_scripts:
                try:
                    data = json.loads(script_content.strip())
                    json_ld_data.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Error parsing JSON-LD: {e}")

        except Exception as e:
            logger.warning(f"Error extracting JSON-LD: {e}")

        return json_ld_data

    def extract_meta_tags(self) -> Dict[str, str]:
        """
        Extract meta tag information from the page.

        Returns:
            Dictionary of meta tag content
        """
        meta_data = {}

        try:
            # Extract standard meta tags
            meta_tags = self.selector.css("meta")

            for meta in meta_tags:
                name = meta.css("::attr(name)").get()
                property_attr = meta.css("::attr(property)").get()
                content = meta.css("::attr(content)").get()

                if content:
                    if name:
                        meta_data[name] = content
                    elif property_attr:
                        meta_data[property_attr] = content

        except Exception as e:
            logger.warning(f"Error extracting meta tags: {e}")

        return meta_data

    def extract_table_data(
        self, table_selector: str, header_row: int = 0
    ) -> List[Dict[str, str]]:
        """
        Extract data from HTML tables.

        Args:
            table_selector: CSS selector for the table
            header_row: Index of header row (0-based)

        Returns:
            List of dictionaries representing table rows
        """
        table_data = []

        try:
            table = self.selector.css(table_selector).get()
            if not table:
                return table_data

            table_sel = Selector(text=table)
            rows = table_sel.css("tr")

            if len(rows) <= header_row:
                return table_data

            # Extract headers
            header_cells = rows[header_row].css("th, td")
            headers = [
                self.clean_text(remove_tags(cell.get() or "")) for cell in header_cells
            ]

            # Extract data rows
            for row in rows[header_row + 1 :]:
                cells = row.css("td")
                if len(cells) >= len(headers):
                    row_data = {}
                    for i, cell in enumerate(cells[: len(headers)]):
                        if i < len(headers) and headers[i]:
                            cell_text = self.clean_text(remove_tags(cell.get() or ""))
                            row_data[headers[i]] = cell_text

                    if row_data:
                        table_data.append(row_data)

        except Exception as e:
            logger.warning(f"Error extracting table data: {e}")

        return table_data

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing extra whitespace and unwanted characters.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove HTML entities
        text = re.sub(r"&[a-zA-Z0-9#]+;", " ", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove non-printable characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        return text.strip()

    def extract_number(
        self, selector_path: str, pattern: str = r"\d+"
    ) -> Optional[int]:
        """
        Extract numeric value from text.

        Args:
            selector_path: CSS selector or XPath expression
            pattern: Regex pattern to extract numbers

        Returns:
            Extracted number or None
        """
        text = self.extract_first_text(selector_path)
        if text:
            numbers = re.findall(pattern, text)
            if numbers:
                try:
                    return int(numbers[0])
                except ValueError:
                    pass
        return None


class FandomResponseParser(ResponseParser):
    """
    Specialized parser for Fandom wiki responses.

    This class extends ResponseParser with Fandom-specific
    parsing methods and selectors.
    """

    def extract_infobox_data(
        self, infobox_selector: str = ".infobox"
    ) -> Dict[str, str]:
        """
        Extract data from a Fandom infobox.

        Args:
            infobox_selector: CSS selector for infobox element

        Returns:
            Dictionary of infobox field names and values
        """
        infobox_data = {}

        try:
            infobox = self.selector.css(infobox_selector)
            if not infobox:
                return infobox_data

            # Extract rows with labels and values
            rows = infobox.css("tr")

            for row in rows:
                # Try different patterns for label/value pairs
                label_elem = row.css("th, .infobox-label")
                value_elem = row.css("td, .infobox-data")

                if label_elem and value_elem:
                    label = self.clean_text(remove_tags(label_elem.get() or ""))
                    value = self.clean_text(remove_tags(value_elem.get() or ""))

                    if label and value:
                        infobox_data[label] = value

        except Exception as e:
            logger.warning(f"Error extracting infobox data: {e}")

        return infobox_data

    def extract_categories(self) -> List[str]:
        """
        Extract page categories from Fandom wiki.

        Returns:
            List of category names
        """
        categories = []

        try:
            # Extract from category links
            cat_links = self.selector.css("#mw-normal-catlinks a::text").getall()
            categories.extend([cat.strip() for cat in cat_links if cat.strip()])

            # Extract from hidden categories if present
            hidden_cats = self.selector.css("#mw-hidden-catlinks a::text").getall()
            categories.extend([cat.strip() for cat in hidden_cats if cat.strip()])

        except Exception as e:
            logger.warning(f"Error extracting categories: {e}")

        return list(set(categories))  # Remove duplicates

    def extract_page_title(self) -> str:
        """
        Extract the main page title.

        Returns:
            Page title
        """
        # Try different selectors for page title
        title_selectors = [
            "#firstHeading::text",
            ".page-header__title::text",
            "h1.entry-title::text",
            "title::text",
        ]

        for selector in title_selectors:
            title = self.extract_first_text(selector)
            if title:
                return title

        return ""

    def extract_page_content(self) -> str:
        """
        Extract main page content text.

        Returns:
            Page content as text
        """
        content_selectors = [
            "#mw-content-text .mw-parser-output",
            ".page-content",
            "#content .entry-content",
            ".wiki-content",
        ]

        for selector in content_selectors:
            content = self.extract_text(selector, join_text="\n")
            if content:
                return content

        return ""

    def extract_gallery_images(self) -> List[Dict[str, str]]:
        """
        Extract images from gallery sections.

        Returns:
            List of gallery image data
        """
        gallery_images = []

        try:
            # Different gallery selectors used by Fandom
            gallery_selectors = [
                ".wikia-gallery .wikia-gallery-item img",
                ".gallery .gallerybox img",
                ".mw-gallery .gallerybox img",
                ".portable-infobox .pi-image img",
            ]

            for selector in gallery_selectors:
                images = self.extract_images(selector)
                gallery_images.extend(images)

        except Exception as e:
            logger.warning(f"Error extracting gallery images: {e}")

        return gallery_images

    def extract_navigation_links(self) -> Dict[str, List[str]]:
        """
        Extract navigation links from the page.

        Returns:
            Dictionary with different types of navigation links
        """
        nav_links = {
            "internal_links": [],
            "external_links": [],
            "category_links": [],
            "file_links": [],
        }

        try:
            # Internal wiki links
            internal_links = self.selector.css(
                'a[href*="/wiki/"]:not([href*=":"]):not([class*="external"])::attr(href)'
            ).getall()
            nav_links["internal_links"] = [
                urljoin(self.url, link) for link in internal_links
            ]

            # External links
            external_links = self.selector.css("a.external::attr(href)").getall()
            nav_links["external_links"] = external_links

            # Category links
            category_links = self.selector.css(
                'a[href*="/wiki/Category:"]::attr(href)'
            ).getall()
            nav_links["category_links"] = [
                urljoin(self.url, link) for link in category_links
            ]

            # File links
            file_links = self.selector.css(
                'a[href*="/wiki/File:"]::attr(href)'
            ).getall()
            nav_links["file_links"] = [urljoin(self.url, link) for link in file_links]

        except Exception as e:
            logger.warning(f"Error extracting navigation links: {e}")

        return nav_links
