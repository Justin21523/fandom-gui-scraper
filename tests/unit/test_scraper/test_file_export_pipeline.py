"""
Unit tests for FileExportPipeline.

Test Coverage:
- Pipeline initialization and configuration
- Content type determination
- Character export to JSON
- Episode export to JSON
- Gallery image metadata export
- Chapter export to JSON
- Directory structure creation (AI_WAREHOUSE 3.0)
- Index file generation
- Scrape manifest creation
- Name sanitization
- ID generation (MD5 hashing)
"""

import pytest
import json
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from itemadapter import ItemAdapter

from scraper.pipelines import FileExportPipeline


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_export_dir(tmp_path):
    """Create temporary export directory."""
    export_dir = tmp_path / "fandom_exports"
    export_dir.mkdir()
    return export_dir


@pytest.fixture
def mock_settings(temp_export_dir):
    """Mock Scrapy settings."""
    settings = Mock()
    settings.getbool = Mock(return_value=True)  # ENABLE_FILE_EXPORT=True
    settings.get = Mock(return_value=str(temp_export_dir))  # FANDOM_DATA_ROOT
    return settings


@pytest.fixture
def pipeline(temp_export_dir):
    """Create FileExportPipeline instance with mocked settings."""
    with patch('scrapy.utils.project.get_project_settings') as mock_get_settings:
        mock_settings = Mock()
        def _getbool(key, default=None):
            if key == "EXPORT_JSON_GZIP":
                return False
            return True
        mock_settings.getbool = Mock(side_effect=_getbool)
        mock_settings.get = Mock(return_value=str(temp_export_dir))
        mock_get_settings.return_value = mock_settings

        pipeline = FileExportPipeline()
        return pipeline


@pytest.fixture
def mock_spider():
    """Mock spider instance."""
    spider = Mock()
    spider.name = "test_spider"
    spider.anime_name = "One Piece"
    spider.crawl_config = {
        'characters': True,
        'episodes': True,
        'galleries': False,
        'chapters': False
    }
    return spider


@pytest.fixture
def sample_character_item():
    """Sample character item."""
    return {
        'name': 'Monkey D. Luffy',
        'anime_name': 'One Piece',
        'source_url': 'https://onepiece.fandom.com/wiki/Monkey_D._Luffy',
        'description': 'The main protagonist',
        'age': '19',
        'gender': 'Male',
        'images': ['https://example.com/luffy1.jpg'],
        'abilities': ['Gomu Gomu no Mi'],
        'relationships': [{'name': 'Nami', 'type': 'crewmate'}]
    }


@pytest.fixture
def sample_episode_item():
    """Sample episode item."""
    return {
        'title': 'I\'m Luffy! The Man Who\'s Gonna Be King of the Pirates!',
        'number': 1,
        'season': 1,
        'anime_name': 'One Piece',
        'source_url': 'https://onepiece.fandom.com/wiki/Episode_1',
        'air_date': '1999-10-20',
        'summary': 'First episode'
    }


@pytest.fixture
def sample_gallery_item():
    """Sample gallery image item."""
    return {
        'url': 'https://example.com/images/luffy_concept.jpg',
        'anime_name': 'One Piece',
        'source_url': 'https://onepiece.fandom.com/wiki/Luffy_Gallery',
        'category': 'concept_art',
        'width': 1920,
        'height': 1080,
        'caption': 'Luffy concept art'
    }


@pytest.fixture
def sample_chapter_item():
    """Sample chapter item."""
    return {
        'title': 'Romance Dawn',
        'number': 1,
        'volume': 1,
        'anime_name': 'One Piece',
        'source_url': 'https://onepiece.fandom.com/wiki/Chapter_1',
        'page_count': 50,
        'release_date': '1997-07-22'
    }


# ============================================================================
# Test Pipeline Initialization
# ============================================================================


class TestFileExportPipelineInitialization:
    """Test FileExportPipeline initialization."""

    def test_initialization_with_defaults(self, pipeline, temp_export_dir):
        """Test pipeline initializes with default settings."""
        assert pipeline.enabled is True
        assert pipeline.base_path == Path(str(temp_export_dir))
        assert pipeline.exported_count == 0
        assert pipeline.failed_exports == 0
        assert pipeline.character_indexes == {}

    def test_initialization_disabled(self, temp_export_dir):
        """Test pipeline with export disabled."""
        with patch('scrapy.utils.project.get_project_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.getbool = Mock(return_value=False)  # Disabled
            mock_settings.get = Mock(return_value=str(temp_export_dir))
            mock_get_settings.return_value = mock_settings

            pipeline = FileExportPipeline()
            assert pipeline.enabled is False

    def test_logger_initialization(self, pipeline):
        """Test logger is initialized."""
        assert pipeline.logger is not None
        assert hasattr(pipeline, 'logger')


# ============================================================================
# Test Content Type Determination
# ============================================================================


class TestContentTypeDetermination:
    """Test _determine_content_type method."""

    def test_determine_character_type(self, pipeline, sample_character_item):
        """Test character content type detection."""
        adapter = ItemAdapter(sample_character_item)
        content_type = pipeline._determine_content_type(adapter)
        assert content_type == 'character'

    def test_determine_episode_type(self, pipeline, sample_episode_item):
        """Test episode content type detection."""
        adapter = ItemAdapter(sample_episode_item)
        content_type = pipeline._determine_content_type(adapter)
        assert content_type == 'episode'

    def test_determine_gallery_type(self, pipeline, sample_gallery_item):
        """Test gallery content type detection."""
        adapter = ItemAdapter(sample_gallery_item)
        content_type = pipeline._determine_content_type(adapter)
        assert content_type == 'gallery'

    def test_determine_chapter_type(self, pipeline, sample_chapter_item):
        """Test chapter content type detection."""
        adapter = ItemAdapter(sample_chapter_item)
        content_type = pipeline._determine_content_type(adapter)
        assert content_type == 'chapter'

    def test_determine_type_with_episode_number_field(self, pipeline):
        """Test episode detection with episode_number field."""
        item = {'episode_number': 5, 'anime_name': 'Test'}
        adapter = ItemAdapter(item)
        content_type = pipeline._determine_content_type(adapter)
        assert content_type == 'episode'

    def test_determine_type_with_number_and_page_count(self, pipeline):
        """Test chapter detection with number and page_count."""
        item = {'number': 10, 'page_count': 50, 'anime_name': 'Test'}
        adapter = ItemAdapter(item)
        content_type = pipeline._determine_content_type(adapter)
        assert content_type == 'chapter'


# ============================================================================
# Test Character Export
# ============================================================================


class TestCharacterExport:
    """Test _export_character method."""

    def test_export_character_creates_directory(self, pipeline, sample_character_item, mock_spider):
        """Test character export creates proper directory structure."""
        adapter = ItemAdapter(sample_character_item)
        pipeline._export_character(adapter, 'One Piece')

        # Check directory exists
        anime_dir = pipeline.base_path / 'One Piece'
        characters_dir = anime_dir / 'characters'
        assert anime_dir.exists()
        assert characters_dir.exists()

    def test_export_character_creates_json_file(self, pipeline, sample_character_item, mock_spider):
        """Test character export creates JSON file."""
        adapter = ItemAdapter(sample_character_item)
        pipeline._export_character(adapter, 'One Piece')

        characters_dir = pipeline.base_path / 'One Piece' / 'characters'
        json_files = list(characters_dir.glob('*.json'))

        assert len(json_files) == 1
        assert json_files[0].name.endswith('.json')

    def test_export_character_json_content(self, pipeline, sample_character_item, mock_spider):
        """Test character JSON file contains correct data."""
        adapter = ItemAdapter(sample_character_item)
        pipeline._export_character(adapter, 'One Piece')

        characters_dir = pipeline.base_path / 'One Piece' / 'characters'
        json_file = list(characters_dir.glob('*.json'))[0]

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data['name'] == 'Monkey D. Luffy'
        assert data['anime_name'] == 'One Piece'
        assert data['age'] == '19'
        assert data['gender'] == 'Male'

    def test_export_character_updates_index(self, pipeline, sample_character_item, mock_spider):
        """Test character export updates character index."""
        adapter = ItemAdapter(sample_character_item)
        pipeline._export_character(adapter, 'One Piece')

        assert 'One Piece' in pipeline.character_indexes
        assert len(pipeline.character_indexes['One Piece']) == 1
        assert pipeline.character_indexes['One Piece'][0]['name'] == 'Monkey D. Luffy'

    def test_export_multiple_characters(self, pipeline, mock_spider):
        """Test exporting multiple characters to same anime."""
        characters = [
            {'name': 'Luffy', 'anime_name': 'One Piece', 'source_url': 'http://example.com/luffy'},
            {'name': 'Zoro', 'anime_name': 'One Piece', 'source_url': 'http://example.com/zoro'},
            {'name': 'Nami', 'anime_name': 'One Piece', 'source_url': 'http://example.com/nami'},
        ]

        for char in characters:
            adapter = ItemAdapter(char)
            pipeline._export_character(adapter, 'One Piece')

        assert len(pipeline.character_indexes['One Piece']) == 3

        characters_dir = pipeline.base_path / 'One Piece' / 'characters'
        json_files = list(characters_dir.glob('*.json'))
        assert len(json_files) == 3


# ============================================================================
# Test Episode Export
# ============================================================================


class TestEpisodeExport:
    """Test _export_episode method."""

    def test_export_episode_creates_directory(self, pipeline, sample_episode_item):
        """Test episode export creates proper directory."""
        adapter = ItemAdapter(sample_episode_item)
        pipeline._export_episode(adapter, 'One Piece')

        anime_dir = pipeline.base_path / 'One Piece'
        episodes_dir = anime_dir / 'episodes'
        assert anime_dir.exists()
        assert episodes_dir.exists()

    def test_export_episode_with_season(self, pipeline, sample_episode_item):
        """Test episode export with season number."""
        adapter = ItemAdapter(sample_episode_item)
        pipeline._export_episode(adapter, 'One Piece')

        episodes_dir = pipeline.base_path / 'One Piece' / 'episodes'
        episode_file = episodes_dir / 's01e01.json'

        assert episode_file.exists()

    def test_export_episode_without_season(self, pipeline):
        """Test episode export without season number."""
        item = {
            'title': 'Test Episode',
            'number': 5,
            'anime_name': 'Test Anime',
            'source_url': 'http://example.com/ep5'
        }
        adapter = ItemAdapter(item)
        pipeline._export_episode(adapter, 'Test Anime')

        episodes_dir = pipeline.base_path / 'Test Anime' / 'episodes'
        episode_file = episodes_dir / 'ep005.json'

        assert episode_file.exists()

    def test_export_episode_json_content(self, pipeline, sample_episode_item):
        """Test episode JSON file content."""
        adapter = ItemAdapter(sample_episode_item)
        pipeline._export_episode(adapter, 'One Piece')

        episodes_dir = pipeline.base_path / 'One Piece' / 'episodes'
        episode_file = episodes_dir / 's01e01.json'

        with open(episode_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data['title'] == 'I\'m Luffy! The Man Who\'s Gonna Be King of the Pirates!'
        assert data['number'] == 1
        assert data['season'] == 1

    def test_export_episode_with_episode_number_field(self, pipeline):
        """Test episode export using episode_number field."""
        item = {
            'title': 'Test',
            'episode_number': 10,
            'anime_name': 'Test',
            'source_url': 'http://example.com/ep10'
        }
        adapter = ItemAdapter(item)
        pipeline._export_episode(adapter, 'Test')

        episodes_dir = pipeline.base_path / 'Test' / 'episodes'
        episode_file = episodes_dir / 'ep010.json'

        assert episode_file.exists()


# ============================================================================
# Test Gallery Image Export
# ============================================================================


class TestGalleryImageExport:
    """Test _export_gallery_image method."""

    def test_export_gallery_creates_directory(self, pipeline, sample_gallery_item):
        """Test gallery export creates proper directory."""
        adapter = ItemAdapter(sample_gallery_item)
        pipeline._export_gallery_image(adapter, 'One Piece')

        anime_dir = pipeline.base_path / 'One Piece'
        gallery_dir = anime_dir / 'gallery'
        assert anime_dir.exists()
        assert gallery_dir.exists()

    def test_export_gallery_image_creates_json(self, pipeline, sample_gallery_item):
        """Test gallery image metadata export."""
        adapter = ItemAdapter(sample_gallery_item)
        pipeline._export_gallery_image(adapter, 'One Piece')

        gallery_dir = pipeline.base_path / 'One Piece' / 'gallery'
        json_files = list(gallery_dir.glob('*.json'))

        assert len(json_files) == 1

    def test_export_gallery_image_json_content(self, pipeline, sample_gallery_item):
        """Test gallery image JSON content."""
        adapter = ItemAdapter(sample_gallery_item)
        pipeline._export_gallery_image(adapter, 'One Piece')

        gallery_dir = pipeline.base_path / 'One Piece' / 'gallery'
        json_file = list(gallery_dir.glob('*.json'))[0]

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data['url'] == 'https://example.com/images/luffy_concept.jpg'
        assert data['category'] == 'concept_art'
        assert data['width'] == 1920
        assert data['height'] == 1080


# ============================================================================
# Test Chapter Export
# ============================================================================


class TestChapterExport:
    """Test _export_chapter method."""

    def test_export_chapter_creates_directory(self, pipeline, sample_chapter_item):
        """Test chapter export creates proper directory."""
        adapter = ItemAdapter(sample_chapter_item)
        pipeline._export_chapter(adapter, 'One Piece')

        anime_dir = pipeline.base_path / 'One Piece'
        chapters_dir = anime_dir / 'chapters'
        assert anime_dir.exists()
        assert chapters_dir.exists()

    def test_export_chapter_with_volume(self, pipeline, sample_chapter_item):
        """Test chapter export with volume number."""
        adapter = ItemAdapter(sample_chapter_item)
        pipeline._export_chapter(adapter, 'One Piece')

        chapters_dir = pipeline.base_path / 'One Piece' / 'chapters'
        chapter_file = chapters_dir / 'vol01ch001.json'

        assert chapter_file.exists()

    def test_export_chapter_without_volume(self, pipeline):
        """Test chapter export without volume number."""
        item = {
            'title': 'Test Chapter',
            'number': 5,
            'anime_name': 'Test Manga',
            'source_url': 'http://example.com/ch5',
            'page_count': 20
        }
        adapter = ItemAdapter(item)
        pipeline._export_chapter(adapter, 'Test Manga')

        chapters_dir = pipeline.base_path / 'Test Manga' / 'chapters'
        chapter_file = chapters_dir / 'ch005.json'

        assert chapter_file.exists()

    def test_export_chapter_json_content(self, pipeline, sample_chapter_item):
        """Test chapter JSON content."""
        adapter = ItemAdapter(sample_chapter_item)
        pipeline._export_chapter(adapter, 'One Piece')

        chapters_dir = pipeline.base_path / 'One Piece' / 'chapters'
        chapter_file = chapters_dir / 'vol01ch001.json'

        with open(chapter_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data['title'] == 'Romance Dawn'
        assert data['number'] == 1
        assert data['volume'] == 1
        assert data['page_count'] == 50


# ============================================================================
# Test process_item Method
# ============================================================================


class TestProcessItem:
    """Test process_item method."""

    def test_process_item_disabled(self, temp_export_dir):
        """Test process_item when export is disabled."""
        with patch('scrapy.utils.project.get_project_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.getbool = Mock(return_value=False)  # Disabled
            mock_settings.get = Mock(return_value=str(temp_export_dir))
            mock_get_settings.return_value = mock_settings

            pipeline = FileExportPipeline()

            item = {'name': 'Test', 'anime_name': 'Test'}
            result = pipeline.process_item(item, Mock())

            # Should return item unchanged without processing
            assert result == item
            assert pipeline.exported_count == 0

    def test_process_item_character(self, pipeline, sample_character_item, mock_spider):
        """Test processing character item."""
        result = pipeline.process_item(sample_character_item, mock_spider)

        assert result == sample_character_item  # Returns unchanged
        assert pipeline.exported_count == 1
        assert pipeline.failed_exports == 0

    def test_process_item_episode(self, pipeline, sample_episode_item, mock_spider):
        """Test processing episode item."""
        result = pipeline.process_item(sample_episode_item, mock_spider)

        assert result == sample_episode_item
        assert pipeline.exported_count == 1

    def test_process_item_gallery(self, pipeline, sample_gallery_item, mock_spider):
        """Test processing gallery item."""
        result = pipeline.process_item(sample_gallery_item, mock_spider)

        assert result == sample_gallery_item
        assert pipeline.exported_count == 1

    def test_process_item_chapter(self, pipeline, sample_chapter_item, mock_spider):
        """Test processing chapter item."""
        result = pipeline.process_item(sample_chapter_item, mock_spider)

        assert result == sample_chapter_item
        assert pipeline.exported_count == 1

    def test_process_item_error_handling(self, pipeline, mock_spider):
        """Test error handling in process_item."""
        # Mock _export_character to raise an exception
        with patch.object(pipeline, '_export_character', side_effect=Exception("Export failed")):
            item = {'name': 'Test', 'anime_name': 'Test', 'source_url': 'http://example.com'}
            result = pipeline.process_item(item, mock_spider)

            # Should return item even if export fails
            assert result == item
            assert pipeline.failed_exports == 1


# ============================================================================
# Test Utility Methods
# ============================================================================


class TestUtilityMethods:
    """Test utility methods."""

    def test_sanitize_name_basic(self, pipeline):
        """Test basic name sanitization."""
        assert pipeline._sanitize_name('One Piece') == 'One Piece'

    def test_sanitize_name_special_characters(self, pipeline):
        """Test sanitizing special characters."""
        result = pipeline._sanitize_name('Test/Name:With<Special>Characters')
        assert '/' not in result
        assert ':' not in result
        assert '<' not in result
        assert '>' not in result

    def test_sanitize_name_strips_whitespace(self, pipeline):
        """Test whitespace stripping."""
        assert pipeline._sanitize_name('  Test Name  ') == 'Test Name'

    def test_generate_id(self, pipeline):
        """Test ID generation using MD5."""
        text = "One Piece:Monkey D. Luffy"
        generated_id = pipeline._generate_id(text)

        # Should be 16-character hex string (MD5 hash truncated)
        assert len(generated_id) == 16
        assert all(c in '0123456789abcdef' for c in generated_id)

    def test_generate_id_consistent(self, pipeline):
        """Test ID generation is consistent."""
        text = "Test:Character"
        id1 = pipeline._generate_id(text)
        id2 = pipeline._generate_id(text)

        assert id1 == id2

    def test_generate_id_unique(self, pipeline):
        """Test different inputs generate different IDs."""
        id1 = pipeline._generate_id("Text 1")
        id2 = pipeline._generate_id("Text 2")

        assert id1 != id2


# ============================================================================
# Test close_spider Method
# ============================================================================


class TestCloseSpider:
    """Test close_spider method."""

    def test_close_spider_writes_character_index(self, pipeline, sample_character_item, mock_spider):
        """Test character index file generation."""
        # Export some characters
        adapter = ItemAdapter(sample_character_item)
        pipeline._export_character(adapter, 'One Piece')

        # Close spider
        pipeline.close_spider(mock_spider)

        # Check index file exists
        characters_dir = pipeline.base_path / 'One Piece' / 'characters'
        index_file = characters_dir / 'character_index.json'

        assert index_file.exists()

    def test_close_spider_index_content(self, pipeline, mock_spider):
        """Test character index file content."""
        # Export multiple characters
        characters = [
            {'name': 'Luffy', 'anime_name': 'One Piece', 'source_url': 'http://example.com/luffy'},
            {'name': 'Zoro', 'anime_name': 'One Piece', 'source_url': 'http://example.com/zoro'},
        ]

        for char in characters:
            adapter = ItemAdapter(char)
            pipeline._export_character(adapter, 'One Piece')

        pipeline.close_spider(mock_spider)

        # Read index file
        characters_dir = pipeline.base_path / 'One Piece' / 'characters'
        index_file = characters_dir / 'character_index.json'

        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        assert index_data['anime_name'] == 'One Piece'
        assert index_data['total_characters'] == 2
        assert len(index_data['characters']) == 2
        assert 'generated_at' in index_data

    def test_close_spider_writes_scrape_manifest(self, pipeline, mock_spider):
        """Test scrape manifest generation."""
        pipeline.exported_count = 10
        pipeline.failed_exports = 1

        pipeline.close_spider(mock_spider)

        # Check manifest file
        metadata_dir = pipeline.base_path / 'One Piece' / 'metadata'
        manifest_file = metadata_dir / 'scrape_manifest.json'

        assert manifest_file.exists()

    def test_close_spider_manifest_content(self, pipeline, mock_spider):
        """Test scrape manifest content."""
        pipeline.exported_count = 15
        pipeline.failed_exports = 2

        pipeline.close_spider(mock_spider)

        metadata_dir = pipeline.base_path / 'One Piece' / 'metadata'
        manifest_file = metadata_dir / 'scrape_manifest.json'

        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)

        assert manifest_data['anime_name'] == 'One Piece'
        assert manifest_data['spider_name'] == 'test_spider'
        assert manifest_data['items_exported'] == 15
        assert manifest_data['failed_exports'] == 2
        assert 'scrape_date' in manifest_data
        assert 'categories_scraped' in manifest_data

    def test_close_spider_no_anime_name(self, pipeline):
        """Test close_spider when spider has no anime_name attribute."""
        spider = Mock()
        spider.name = "test_spider"
        # No anime_name attribute
        delattr(spider, 'anime_name')

        # Should not raise error
        pipeline.close_spider(spider)


# ============================================================================
# Test AI_WAREHOUSE 3.0 Directory Structure
# ============================================================================


class TestAIWarehouseStructure:
    """Test AI_WAREHOUSE 3.0 directory structure."""

    def test_complete_directory_structure(self, pipeline, mock_spider):
        """Test complete directory structure is created."""
        # Export all content types
        character_item = {'name': 'Luffy', 'anime_name': 'One Piece', 'source_url': 'http://ex.com/luffy'}
        episode_item = {'title': 'Ep1', 'number': 1, 'anime_name': 'One Piece', 'source_url': 'http://ex.com/ep1'}
        gallery_item = {'url': 'http://ex.com/img.jpg', 'anime_name': 'One Piece', 'source_url': 'http://ex.com/gal', 'category': 'screenshot'}
        chapter_item = {'title': 'Ch1', 'number': 1, 'anime_name': 'One Piece', 'source_url': 'http://ex.com/ch1', 'page_count': 20}

        pipeline.process_item(character_item, mock_spider)
        pipeline.process_item(episode_item, mock_spider)
        pipeline.process_item(gallery_item, mock_spider)
        pipeline.process_item(chapter_item, mock_spider)
        pipeline.close_spider(mock_spider)

        # Check all directories exist
        anime_dir = pipeline.base_path / 'One Piece'
        assert (anime_dir / 'characters').exists()
        assert (anime_dir / 'episodes').exists()
        assert (anime_dir / 'gallery').exists()
        assert (anime_dir / 'chapters').exists()
        assert (anime_dir / 'metadata').exists()

    def test_directory_names_sanitized(self, pipeline, mock_spider):
        """Test directory names are properly sanitized."""
        item = {
            'name': 'Test Character',
            'anime_name': 'Test/Anime:Name<With>Special|Chars',
            'source_url': 'http://example.com/test'
        }

        pipeline.process_item(item, mock_spider)

        # Check sanitized directory exists
        sanitized_dirs = list(pipeline.base_path.iterdir())
        assert len(sanitized_dirs) > 0

        # Directory name should not contain special chars
        dir_name = sanitized_dirs[0].name
        assert '/' not in dir_name
        assert ':' not in dir_name
        assert '<' not in dir_name
        assert '>' not in dir_name
        assert '|' not in dir_name
