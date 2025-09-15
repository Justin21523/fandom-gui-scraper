# scraper/items/character_item.py
"""
Character data structure for scrapy items.

This module defines the data structure for character information
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


class CharacterItem(scrapy.Item):
    """
    Scrapy item for character data.

    This item defines the structure for character information
    including basic details, physical characteristics, and metadata.
    """

    # Basic Information
    name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    japanese_name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    english_name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    aliases = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=list,  # Keep as list for multiple aliases
    )

    # Character Details
    anime_series = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    occupation = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    affiliation = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    status = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Physical Characteristics
    age = scrapy.Field(
        input_processor=MapCompose(extract_number), output_processor=TakeFirst()
    )

    height = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    weight = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    gender = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    birthday = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    blood_type = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    # Character Background
    description = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    personality = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    history = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=Join("\n")
    )

    abilities = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Relations
    family = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    friends = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    enemies = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Media
    image_urls = scrapy.Field()
    images = scrapy.Field()

    profile_image = scrapy.Field(
        input_processor=TakeFirst(), output_processor=TakeFirst()
    )

    gallery_images = scrapy.Field()

    # Voice Acting
    voice_actor_japanese = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    voice_actor_english = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
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

    # Story Arcs and Episodes
    first_appearance = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )

    story_arcs = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text), output_processor=list
    )

    # Additional Custom Fields (for extensibility)
    custom_fields = scrapy.Field()

    # Data Quality Indicators
    completeness_score = scrapy.Field(output_processor=TakeFirst())

    reliability_score = scrapy.Field(output_processor=TakeFirst())
