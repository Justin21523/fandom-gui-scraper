# scraper/items/episode_item.py
"""
Episode data structure for scrapy items.

This module defines the data structure for individual episode information
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


def extract_duration_minutes(value):
    """Extract duration in minutes from various formats."""
    if value:
        import re

        # Look for patterns like "24 min", "24 minutes", "00:24:00"
        minutes_match = re.search(r"(\d+)\s*(?:min|minutes)", str(value), re.IGNORECASE)
        if minutes_match:
            return int(minutes_match.group(1))

        # Look for time format HH:MM:SS or MM:SS
        time_match = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", str(value))
        if time_match:
            hours = int(time_match.group(1)) if len(time_match.group(1)) > 2 else 0
            minutes = (
                int(time_match.group(1))
                if len(time_match.group(1)) <= 2
                else int(time_match.group(2))
            )
            if hours > 0:
                minutes += hours * 60
            return minutes
    return None


class EpisodeItem(scrapy.Item):
    """
    Scrapy item for episode data.

    This item defines the structure for individual episode information
    including details, characters, and plot summary.
    """

    # Basic Episode Information
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

    # Episode Identification
    episode_number = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    season_number = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    absolute_episode_number = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    anime_series = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Release Information
    air_date = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    original_air_date = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    international_air_dates = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Episode Content
    summary = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    plot = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    synopsis = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    # Production Details
    duration = scrapy.Field(
        input_processor=MapCompose(extract_duration_minutes),
        output_processor=TakeFirst(),
    )

    director = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    writer = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    storyboard = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    animation_director = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Characters and Cast
    featured_characters = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    main_characters = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    guest_characters = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    voice_actors = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Story Arc and Context
    story_arc = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    saga = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    chapter_adapted = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    manga_chapters = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Episode Navigation
    previous_episode = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    next_episode = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Visual Content
    image_urls = scrapy.Field()
    images = scrapy.Field()

    episode_thumbnail = scrapy.Field(
        input_processor=TakeFirst(), output_processor=TakeFirst()
    )

    screenshots = scrapy.Field()

    keyframes = scrapy.Field()

    # Audio Information
    opening_theme = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    ending_theme = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    insert_songs = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    background_music = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Ratings and Reception
    rating = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    user_rating = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    viewership = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Episode Type and Categorization
    episode_type = scrapy.Field(  # Regular, Filler, Recap, Special, OVA
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    filler_episode = scrapy.Field(
        input_processor=MapCompose(lambda x: x.lower() in ["yes", "true", "filler"]),
        output_processor=TakeFirst(),
    )

    special_episode = scrapy.Field(
        input_processor=MapCompose(lambda x: x.lower() in ["yes", "true", "special"]),
        output_processor=TakeFirst(),
    )

    # Notable Events and Plot Points
    major_events = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    character_debuts = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    character_deaths = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    techniques_introduced = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Broadcast Information
    broadcast_network = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    time_slot = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # International Information
    dubbed_languages = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    subtitle_languages = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Trivia and Notes
    trivia = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    notes = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    errors = scrapy.Field(
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

    # Categories and Tags
    categories = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    tags = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Additional Custom Fields
    custom_fields = scrapy.Field()

    # Data Quality Indicators
    completeness_score = scrapy.Field(output_processor=TakeFirst())

    reliability_score = scrapy.Field(output_processor=TakeFirst())
