#  scraper/items/media_item.py
"""
Media data structure for scrapy items.

This module defines the data structure for multimedia content
(images, videos, audio) scraped from Fandom wikis.
"""

import scrapy
from itemloaders.processors import TakeFirst, MapCompose
from w3lib.html import remove_tags


def clean_text(value):
    """Clean text by removing extra whitespaces and newlines."""
    if value:
        return " ".join(value.strip().split())
    return value


def extract_number(value):
    """Extract numeric values from text."""
    if value:
        import re

        numbers = re.findall(r"\d+", str(value))
        return int(numbers[0]) if numbers else None
    return None


def extract_file_size(value):
    """Extract file size in bytes from various formats."""
    if value:
        import re

        # Look for patterns like "1.5 MB", "500 KB", "2 GB"
        size_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(KB|MB|GB|B)", str(value), re.IGNORECASE
        )
        if size_match:
            size = float(size_match.group(1))
            unit = size_match.group(2).upper()

            multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
            return int(size * multipliers.get(unit, 1))
    return None


class MediaItem(scrapy.Item):
    """
    Scrapy item for multimedia content.

    This item defines the structure for images, videos, and audio files
    associated with characters, episodes, or anime series.
    """

    # Basic Media Information
    filename = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    original_filename = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    description = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    caption = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Media Type and Format
    media_type = scrapy.Field(  # image, video, audio
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    file_format = scrapy.Field(  # jpg, png, gif, mp4, mp3, etc.
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    mime_type = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # File Properties
    file_size = scrapy.Field(
        input_processor=MapCompose(extract_file_size), output_processor=TakeFirst()
    )

    file_size_readable = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # URLs and Paths
    url = scrapy.Field(output_processor=TakeFirst())

    original_url = scrapy.Field(output_processor=TakeFirst())

    local_path = scrapy.Field(output_processor=TakeFirst())

    thumbnail_url = scrapy.Field(output_processor=TakeFirst())

    thumbnail_path = scrapy.Field(output_processor=TakeFirst())

    # Image-specific Properties
    width = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    height = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    resolution = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    aspect_ratio = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    color_depth = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    # Video-specific Properties
    duration = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    duration_seconds = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    frame_rate = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    video_codec = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    audio_codec = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    bitrate = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # Audio-specific Properties
    sample_rate = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    channels = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    audio_bitrate = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # Content Classification
    category = scrapy.Field(  # character_image, episode_screenshot, cover_art, etc.
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    subcategory = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    image_type = scrapy.Field(  # profile, gallery, screenshot, artwork, etc.
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # Associated Content
    character_name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    anime_series = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    episode_number = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    episode_title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Artist and Creation Information
    artist = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    creator = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    copyright_holder = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    creation_date = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Upload and Source Information
    upload_date = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    uploader = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    source_page = scrapy.Field(output_processor=TakeFirst())

    wiki_page = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Usage and Context
    usage_context = scrapy.Field(  # infobox, gallery, content, thumbnail
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    featured_on_pages = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Quality and Processing
    quality_score = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    is_processed = scrapy.Field(
        input_processor=MapCompose(lambda x: x.lower() in ["yes", "true", "1"]),
        output_processor=TakeFirst(),
    )

    processing_notes = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Alternative Versions
    has_thumbnail = scrapy.Field(
        input_processor=MapCompose(lambda x: x.lower() in ["yes", "true", "1"]),
        output_processor=TakeFirst(),
    )

    has_large_version = scrapy.Field(
        input_processor=MapCompose(lambda x: x.lower() in ["yes", "true", "1"]),
        output_processor=TakeFirst(),
    )

    alternative_sizes = scrapy.Field(output_processor=list)

    # Licensing and Rights
    license = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    usage_rights = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    fair_use = scrapy.Field(
        input_processor=MapCompose(lambda x: x.lower() in ["yes", "true", "1"]),
        output_processor=TakeFirst(),
    )

    # Technical Metadata
    exif_data = scrapy.Field()

    color_palette = scrapy.Field(output_processor=list)

    dominant_colors = scrapy.Field(output_processor=list)

    # Download Status
    download_status = scrapy.Field(  # pending, completed, failed, skipped
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    download_error = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    download_attempts = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    # Metadata
    source_url = scrapy.Field(output_processor=TakeFirst())

    source_wiki = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    scraped_at = scrapy.Field(output_processor=TakeFirst())

    last_modified = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Tags and Categories
    tags = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    categories = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Additional Custom Fields
    custom_fields = scrapy.Field()

    # Data Quality Indicators
    completeness_score = scrapy.Field(output_processor=TakeFirst())

    reliability_score = scrapy.Field(output_processor=TakeFirst())
