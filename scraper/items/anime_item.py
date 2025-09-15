"""
Anime data structure for scrapy items.

This module defines the data structure for anime/series information
scraped from Fandom wikis.
"""

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
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


def extract_year(value):
    """Extract year from date string."""
    if value:
        import re

        years = re.findall(r"\b(19|20)\d{2}\b", str(value))
        return int(years[0]) if years else None
    return None


class AnimeItem(scrapy.Item):
    """
    Scrapy item for anime/series data.

    This item defines the structure for anime series information
    including basic details, production info, and metadata.
    """

    # Basic Information
    title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    japanese_title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    english_title = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    alternative_titles = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Series Details
    type = scrapy.Field(  # TV series, Movie, OVA, etc.
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    status = scrapy.Field(  # Ongoing, Completed, Upcoming
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    genre = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    themes = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Production Information
    studio = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    director = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    producer = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    writer = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Release Information
    release_date = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    end_date = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    premiere_year = scrapy.Field(
        input_processor=MapCompose(extract_year), output_processor=TakeFirst()
    )

    season = scrapy.Field(  # Spring, Summer, Fall, Winter
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Episode Information
    total_episodes = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    episode_duration = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Content Description
    synopsis = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    plot_summary = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    # Ratings and Reviews
    rating = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    user_rating = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    popularity_rank = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    # Media Content
    image_urls = scrapy.Field()
    images = scrapy.Field()

    poster_image = scrapy.Field(
        input_processor=TakeFirst(), output_processor=TakeFirst()
    )

    cover_image = scrapy.Field(
        input_processor=TakeFirst(), output_processor=TakeFirst()
    )

    screenshot_images = scrapy.Field()

    trailer_url = scrapy.Field(
        input_processor=TakeFirst(), output_processor=TakeFirst()
    )

    # Related Content
    manga_source = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    light_novel_source = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    related_series = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    sequel_series = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    prequel_series = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Characters
    main_characters = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    supporting_characters = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Music and Audio
    opening_theme = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    ending_theme = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    background_music = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Broadcast Information
    original_network = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    broadcast_day = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    broadcast_time = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # International Information
    international_releases = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    dubbing_languages = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    subtitle_languages = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
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

    # Categories and Classification
    categories = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    tags = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    age_rating = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    content_warnings = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Story Structure
    story_arcs = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    seasons_count = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    # Commercial Information
    box_office = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    budget = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    merchandise = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Additional Custom Fields
    custom_fields = scrapy.Field()

    # Data Quality Indicators
    completeness_score = scrapy.Field(output_processor=TakeFirst())

    reliability_score = scrapy.Field(output_processor=TakeFirst())
