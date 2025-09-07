## Additional Notes
Any additional context or considerations for reviewers.
```

## 🧪 Testing Guidelines

### **Testing Framework Setup**

We use **pytest** as our primary testing framework with additional plugins:

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-qt pytest-mock pytest-asyncio

# Run tests
pytest                          # All tests
pytest tests/unit/             # Unit tests only
pytest tests/integration/      # Integration tests only
pytest -v --cov=.             # With coverage report
```

### **Test Structure**

#### **Directory Organization**
```
tests/
├── unit/                      # Unit tests
│   ├── test_models/
│   ├── test_utils/
│   ├── test_scraper/
│   └── test_gui/
├── integration/               # Integration tests
│   ├── test_scraper_integration.py
│   ├── test_gui_integration.py
│   └── test_api_integration.py
├── fixtures/                  # Test data and fixtures
│   ├── sample_html/
│   ├── sample_data/
│   └── mock_responses/
└── conftest.py               # Pytest configuration
```

#### **Test Naming Conventions**
```python
# Test file: test_character_spider.py
class TestCharacterSpider:
    """Test suite for CharacterSpider functionality."""
    
    def test_parse_character_data_success(self):
        """Test successful parsing of character data."""
        pass
    
    def test_parse_character_data_missing_name(self):
        """Test handling when character name is missing."""
        pass
    
    def test_parse_character_data_invalid_html(self):
        """Test handling of malformed HTML content."""
        pass
```

### **Unit Testing Examples**

#### **Testing Data Models**
```python
# tests/unit/test_models/test_character.py
import pytest
from pydantic import ValidationError
from models.schemas.character_schema import CharacterSchema

class TestCharacterSchema:
    """Test character data validation and serialization."""
    
    def test_valid_character_creation(self):
        """Test creating a valid character."""
        character_data = {
            "name": "Monkey D. Luffy",
            "anime": "One Piece",
            "age": "19",
            "description": "Captain of the Straw Hat Pirates"
        }
        
        character = CharacterSchema(**character_data)
        assert character.name == "Monkey D. Luffy"
        assert character.anime == "One Piece"
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterSchema(anime="One Piece")  # Missing name
        
        assert "name" in str(exc_info.value)
    
    def test_data_cleaning(self):
        """Test automatic data cleaning and normalization."""
        character_data = {
            "name": "  Luffy  \n",  # Extra whitespace
            "anime": "One Piece"
        }
        
        character = CharacterSchema(**character_data)
        assert character.name == "Luffy"  # Cleaned
```

#### **Testing Scraper Logic**
```python
# tests/unit/test_scraper/test_base_spider.py
import pytest
from unittest.mock import Mock, patch
from scraper.base_spider import BaseSpider

class TestBaseSpider:
    """Test BaseSpider functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.spider = BaseSpider(anime_name="Test Anime")
    
    def test_url_validation_valid_fandom_url(self):
        """Test URL validation for valid Fandom URLs."""
        valid_url = "https://onepiece.fandom.com/wiki/Luffy"
        assert self.spider.validate_url(valid_url) is True
    
    def test_url_validation_invalid_domain(self):
        """Test URL validation rejects non-Fandom domains."""
        invalid_url = "https://evil-site.com/malware"
        assert self.spider.validate_url(invalid_url) is False
    
    @patch('scraper.base_spider.requests.get')
    def test_parse_character_page_success(self, mock_get):
        """Test successful character page parsing."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <h1 class="page-header__title">Test Character</h1>
            <div class="portable-infobox">
                <div data-source="age">19</div>
            </div>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Test parsing
        result = self.spider.parse_character_page(mock_response)
        assert result["name"] == "Test Character"
```

#### **Testing GUI Components**
```python
# tests/unit/test_gui/test_main_window.py
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

class TestMainWindow:
    """Test MainWindow GUI functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_qt_app(self, qtbot):
        """Set up QApplication for testing."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        self.main_window = MainWindow()
        qtbot.addWidget(self.main_window)
    
    def test_window_initialization(self):
        """Test that main window initializes correctly."""
        assert self.main_window.windowTitle() == "Fandom Scraper"
        assert self.main_window.isVisible() is False
    
    def test_start_scraping_button(self, qtbot):
        """Test start scraping button functionality."""
        # Show window
        self.main_window.show()
        
        # Find start button
        start_button = self.main_window.start_button
        assert start_button.isEnabled() is True
        
        # Simulate button click
        qtbot.mouseClick(start_button, Qt.LeftButton)
        
        # Verify button state change
        assert start_button.isEnabled() is False
```

### **Integration Testing**

#### **Database Integration Tests**
```python
# tests/integration/test_database_integration.py
import pytest
import pymongo
from models.repositories.character_repo import CharacterRepository
from models.schemas.character_schema import CharacterSchema

class TestDatabaseIntegration:
    """Test database operations with real MongoDB instance."""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Set up test database before each test."""
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.test_db = self.client.fandom_scraper_test
        self.repository = CharacterRepository(
            "mongodb://localhost:27017/",
            "fandom_scraper_test"
        )
        
        yield
        
        # Cleanup after test
        self.client.drop_database("fandom_scraper_test")
        self.client.close()
    
    def test_save_and_retrieve_character(self):
        """Test complete save and retrieve cycle."""
        # Create test character
        character_data = {
            "name": "Test Character",
            "anime": "Test Anime",
            "description": "A test character for integration testing"
        }
        
        # Save character
        character_id = self.repository.save_character(character_data)
        assert character_id is not None
        
        # Retrieve character
        retrieved_character = self.repository.find_by_id(character_id)
        assert retrieved_character is not None
        assert retrieved_character["name"] == "Test Character"
    
    def test_duplicate_character_handling(self):
        """Test handling of duplicate character entries."""
        character_data = {
            "name": "Duplicate Test",
            "anime": "Test Anime"
        }
        
        # Save first time
        first_id = self.repository.save_character(character_data)
        
        # Save duplicate (should update, not create new)
        second_id = self.repository.save_character(character_data)
        
        assert first_id == second_id
```

#### **End-to-End Testing**
```python
# tests/integration/test_e2e_scraping.py
import pytest
from unittest.mock import patch, Mock
from main import FandomScraperApp

class TestEndToEndScraping:
    """Test complete scraping workflow."""
    
    @patch('scraper.base_spider.requests.get')
    def test_complete_scraping_workflow(self, mock_get):
        """Test full scraping process from GUI to database."""
        # Mock HTTP responses
        mock_get.side_effect = [
            self._create_mock_character_list_response(),
            self._create_mock_character_page_response()
        ]
        
        # Initialize application
        app = FandomScraperApp()
        
        # Configure scraping project
        project_config = {
            "anime_name": "Test Anime",
            "max_pages": 1,
            "data_types": ["characters"]
        }
        
        # Start scraping
        results = app.start_scraping(project_config)
        
        # Verify results
        assert results["characters_scraped"] > 0
        assert results["errors"] == 0
        
        # Verify database contains data
        characters = app.database.characters.find({"anime": "Test Anime"})
        assert list(characters) != []
    
    def _create_mock_character_list_response(self):
        """Create mock response for character list page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <div class="category-page__members">
            <a href="/wiki/Test_Character">Test Character</a>
        </div>
        """
        return mock_response
    
    def _create_mock_character_page_response(self):
        """Create mock response for character detail page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <h1 class="page-header__title">Test Character</h1>
            <div class="portable-infobox">
                <div data-source="age">25</div>
            </div>
            <p>Character description here.</p>
        </html>
        """
        return mock_response
```

### **Test Configuration**

#### **conftest.py**
```python
# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path
import pymongo
from PyQt5.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qt_app():
    """Create QApplication for GUI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for file storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_database():
    """Set up test database for integration tests."""
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    test_db_name = "fandom_scraper_test"
    
    yield client[test_db_name]
    
    # Cleanup
    client.drop_database(test_db_name)
    client.close()

@pytest.fixture
def sample_character_data():
    """Provide sample character data for tests."""
    return {
        "name": "Test Character",
        "anime": "Test Anime",
        "age": "20",
        "description": "A character for testing purposes",
        "relationships": {"friend": "Test Friend"},
        "abilities": ["Test Ability 1", "Test Ability 2"]
    }
```

## 🔧 Adding New Features

### **Feature Development Process**

#### **1. Planning Phase**
```markdown
# Feature Proposal Template

## Feature Name
Brief descriptive name for the feature

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How will this feature work?

## Technical Design
- Architecture considerations
- New components needed
- Dependencies and integrations
- Performance implications

## Acceptance Criteria
- [ ] Specific, testable requirements
- [ ] Edge cases handled
- [ ] Error scenarios covered

## Testing Strategy
- Unit tests required
- Integration tests needed
- Manual testing checklist

## Documentation Updates
- User guide changes
- API documentation
- Developer documentation
```

#### **2. Implementation Example: Adding New Spider**

**Step 1: Create Spider Class**
```python
# scraper/spiders/naruto_spider.py
from typing import Iterator, Dict, Any
from scrapy.http import Response, Request
from scraper.base_spider import BaseSpider, FandomSpiderMixin

class NarutoSpider(BaseSpider, FandomSpiderMixin):
    """
    Spider for extracting character data from Naruto Fandom wiki.
    
    This spider specializes in parsing Naruto-specific page structures
    and extracting ninja-related information such as villages, jutsu,
    and clan affiliations.
    """
    
    name = "naruto_spider"
    allowed_domains = ["naruto.fandom.com"]
    
    def __init__(self, **kwargs):
        super().__init__(anime_name="Naruto", **kwargs)
        self.start_urls = [
            "https://naruto.fandom.com/wiki/Category:Characters"
        ]
    
    def parse(self, response: Response) -> Iterator[Request]:
        """Parse character category page and generate character requests."""
        # Extract character links
        character_links = response.css(
            '.category-page__members a::attr(href)'
        ).getall()
        
        for link in character_links:
            if self._is_character_link(link):
                character_url = response.urljoin(link)
                yield Request(
                    url=character_url,
                    callback=self.parse_character_page,
                    meta={'character_type': self._get_character_type(link)}
                )
        
        # Follow pagination
        next_page = response.css('.category-page__pagination-next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_character_page(self, response: Response) -> Dict[str, Any]:
        """Parse individual character page for Naruto-specific data."""
        # Use base parsing with Naruto-specific extensions
        character_data = super().parse_character_page(response)
        
        # Add Naruto-specific fields
        character_data.update({
            'village': self._extract_village(response),
            'clan': self._extract_clan(response),
            'jutsu': self._extract_jutsu(response),
            'ninja_rank': self._extract_ninja_rank(response)
        })
        
        return character_data
    
    def _extract_village(self, response: Response) -> str:
        """Extract character's village affiliation."""
        village_selector = '[data-source="village"] .pi-data-value::text'
        return response.css(village_selector).get() or ""
    
    def _extract_clan(self, response: Response) -> str:
        """Extract character's clan affiliation."""
        clan_selector = '[data-source="clan"] .pi-data-value::text'
        return response.css(clan_selector).get() or ""
    
    def _extract_jutsu(self, response: Response) -> List[str]:
        """Extract character's known jutsu."""
        jutsu_selectors = [
            '.jutsu-list li::text',
            '[data-source="jutsu"] .pi-data-value a::text'
        ]
        
        jutsu = []
        for selector in jutsu_selectors:
            jutsu.extend(response.css(selector).getall())
        
        return list(set(jutsu))  # Remove duplicates
```

**Step 2: Add Configuration**
```yaml
# config/selector_configs/naruto.yaml
selectors:
  character_list:
    url_pattern: "https://naruto.fandom.com/wiki/Category:Characters"
    character_links: ".category-page__members a"
    next_page: ".category-page__pagination-next"
  
  character_page:
    name: "h1.page-header__title"
    infobox: ".portable-infobox"
    description: ".mw-parser-output > p:first-of-type"
    
    # Naruto-specific selectors
    village: '[data-source="village"] .pi-data-value'
    clan: '[data-source="clan"] .pi-data-value'
    ninja_rank: '[data-source="rank"] .pi-data-value'
    jutsu: '.jutsu-list li, [data-source="jutsu"] .pi-data-value a'
    
    main_image: ".pi-image img"
    gallery_images: ".wikia-gallery img"

# Advanced parsing rules
parsing_rules:
  village_aliases:
    "Konohagakure": ["Konoha", "Hidden Leaf"]
    "Sunagakure": ["Suna", "Hidden Sand"]
  
  rank_hierarchy:
    - "Academy Student"
    - "Genin"
    - "Chunin"
    - "Jonin"
    - "Kage"
```

**Step 3: Update Spider Factory**
```python
# utils/spider_factory.py
class SpiderFactory:
    """Factory for creating anime-specific spiders."""
    
    SPIDER_MAPPING = {
        "one piece": "scraper.spiders.onepiece_spider.OnePieceSpider",
        "naruto": "scraper.spiders.naruto_spider.NarutoSpider",
        "dragon ball": "scraper.spiders.dragonball_spider.DragonBallSpider"
    }
    
    @classmethod
    def create_spider(cls, anime_name: str, **kwargs) -> BaseSpider:
        """
        Create appropriate spider for given anime.
        
        Args:
            anime_name: Name of the anime series
            **kwargs: Additional spider configuration
            
        Returns:
            Configured spider instance
            
        Raises:
            ValueError: If anime is not supported
        """
        anime_key = anime_name.lower().strip()
        
        if anime_key in cls.SPIDER_MAPPING:
            spider_class_path = cls.SPIDER_MAPPING[anime_key]
            spider_class = cls._import_spider_class(spider_class_path)
            return spider_class(**kwargs)
        else:
            # Fallback to generic spider
            from scraper.spiders.generic_fandom import GenericFandomSpider
            return GenericFandomSpider(anime_name=anime_name, **kwargs)
    
    @staticmethod
    def _import_spider_class(class_path: str):
        """Dynamically import spider class from path."""
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
```

**Step 4: Write Tests**
```python
# tests/unit/test_spiders/test_naruto_spider.py
import pytest
from unittest.mock import Mock
from scraper.spiders.naruto_spider import NarutoSpider

class TestNarutoSpider:
    """Test Naruto-specific spider functionality."""
    
    def setup_method(self):
        self.spider = NarutoSpider()
    
    def test_naruto_specific_field_extraction(self):
        """Test extraction of Naruto-specific character fields."""
        mock_response = Mock()
        mock_response.css.side_effect = [
            # Village
            Mock(get=lambda: "Konohagakure"),
            # Clan
            Mock(get=lambda: "Uzumaki"),
            # Jutsu
            Mock(getall=lambda: ["Rasengan", "Shadow Clone Jutsu"]),
            # Ninja rank
            Mock(get=lambda: "Genin")
        ]
        
        village = self.spider._extract_village(mock_response)
        clan = self.spider._extract_clan(mock_response)
        jutsu = self.spider._extract_jutsu(mock_response)
        rank = self.spider._extract_ninja_rank(mock_response)
        
        assert village == "Konohagakure"
        assert clan == "Uzumaki"
        assert "Rasengan" in jutsu
        assert rank == "Genin"
```

### **GUI Feature Development**

#### **Adding New Widget**
```python
# gui/widgets/character_detail_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QScrollArea, QPushButton
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from typing import Dict, Any

class CharacterDetailWidget(QWidget):
    """
    Widget for displaying detailed character information.
    
    Provides a comprehensive view of character data including
    basic info, description, relationships, and images.
    """
    
    # Signals for communication with parent widgets
    character_updated = pyqtSignal(dict)
    edit_requested = pyqtSignal(str)  # character_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_id = None
        self.character_data = {}
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the user interface layout."""
        layout = QVBoxLayout(self)
        
        # Header section
        header_layout = self._create_header_section()
        layout.addLayout(header_layout)
        
        # Content area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_layout = self._create_content_layout()
        content_widget.setLayout(content_layout)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Action buttons
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
    
    def _create_header_section(self) -> QHBoxLayout:
        """Create character header with name and basic info."""
        layout = QHBoxLayout()
        
        # Character image
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 200)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # Character basic info
        info_layout = QVBoxLayout()
        
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_layout.addWidget(self.name_label)
        
        self.anime_label = QLabel()
        self.anime_label.setStyleSheet("font-size: 14px; color: gray;")
        info_layout.addWidget(self.anime_label)
        
        self.status_info = QLabel()
        info_layout.addWidget(self.status_info)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        return layout
    
    def load_character(self, character_data: Dict[str, Any]):
        """
        Load character data into the widget.
        
        Args:
            character_data: Dictionary containing character information
        """
        self.character_data = character_data
        self.character_id = character_data.get('_id')
        
        # Update UI elements
        self.name_label.setText(character_data.get('name', 'Unknown'))
        self.anime_label.setText(character_data.get('anime', 'Unknown'))
        
        # Load character image
        self._load_character_image(character_data.get('image_urls', []))
        
        # Update description
        description = character_data.get('description', 'No description available.')
        self.description_text.setText(description)
        
        # Update additional fields based on anime type
        self._update_anime_specific_fields(character_data)
    
    def _load_character_image(self, image_urls: list):
        """Load and display character image."""
        if image_urls:
            # Load first available image
            image_path = image_urls[0]
            if image_path.startswith('http'):
                # Download image if URL
                self._download_and_display_image(image_path)
            else:
                # Load local image
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        150, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
```

## 🐛 Debugging and Profiling

### **Logging Configuration**

#### **Debug Logging Setup**
```python
# utils/logger.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_development_logging():
    """Configure comprehensive logging for development."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler for detailed logging
    file_handler = RotatingFileHandler(
        log_dir / "debug.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Specific logger configurations
    scrapy_logger = logging.getLogger('scrapy')
    scrapy_logger.setLevel(logging.INFO)
    
    pymongo_logger = logging.getLogger('pymongo')
    pymongo_logger.setLevel(logging.WARNING)
```

### **Performance Profiling**

#### **Memory Profiling**
```python
# utils/profiling.py
import psutil
import tracemalloc
from functools import wraps
from typing import Callable, Any

def memory_profile(func: Callable) -> Callable:
    """Decorator to profile memory usage of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Start memory tracing
        tracemalloc.start()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Get memory statistics
            current, peak = tracemalloc.get_traced_memory()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            tracemalloc.stop()
            
            logger.info(f"Memory Profile for {func.__name__}:")
            logger.info(f"  Initial Memory: {initial_memory:.2f} MB")
            logger.info(f"  Final Memory: {final_memory:.2f} MB")
            logger.info(f"  Memory Delta: {final_memory - initial_memory:.2f} MB")
            logger.info(f"  Peak Traced: {peak / 1024 / 1024:.2f} MB")
    
    return wrapper

def profile_large_dataset_processing():
    """Profile memory usage during large dataset processing."""
    @memory_profile
    def process_characters(character_list):
        processed = []
        for character in character_list:
            # Simulate processing
            processed_character = {
                **character,
                'processed_at': time.time(),
                'quality_score': calculate_quality_score(character)
            }
            processed.append(processed_character)
        return processed
    
    # Test with large dataset
    large_dataset = generate_test_characters(10000)
    result = process_characters(large_dataset)
```

#### **Performance Benchmarking**
```python
# tests/performance/test_scraping_performance.py
import time
import pytest
from unittest.mock import patch, Mock
from scraper.spiders.onepiece_spider import OnePieceSpider

class TestScrapingPerformance:
    """Test scraping performance and benchmarks."""
    
    def test_character_parsing_performance(self):
        """Benchmark character page parsing speed."""
        spider = OnePieceSpider()
        
        # Create mock response with complex HTML
        mock_response = self._create_complex_mock_response()
        
        # Benchmark parsing
        start_time = time.perf_counter()
        iterations = 1000
        
        for _ in range(iterations):
            result = spider.parse_character_page(mock_response)
        
        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations
        
        # Assert performance requirements
        assert avg_time < 0.01  # Less than 10ms per page
        assert result is not None
        
        print(f"Average parsing time: {avg_time*1000:.2f}ms per page")
    
    def test_concurrent_request_performance(self):
        """Test performance under concurrent request load."""
        # Implementation for concurrent testing
        pass
```

## 🤝 Contributing Guidelines

### **Contribution Process**

#### **Getting Started**
1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up development environment** following this guide
4. **Create feature branch** from `develop`
5. **Make changes** following coding standards
6. **Add tests** for new functionality
7. **Update documentation** as needed
8. **Submit pull request** with detailed description

#### **Pull Request Template**
```markdown
## Description
Brief summary of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist:
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

#### **Code Review Guidelines**

**For Reviewers:**
- Review both functionality and code quality
- Check for security implications
- Verify test coverage
- Ensure documentation is updated
- Consider performance impact
- Validate error handling

**For Contributors:**
- Respond to feedback promptly and professionally
- Make requested changes in separate commits
- Update PR description if scope changes
- Ensure CI/CD checks pass

### **Community Standards**

#### **Communication Guidelines**
- Be respectful and constructive in discussions
- Provide specific, actionable feedback
- Ask questions when requirements are unclear
- Help newcomers get started
- Share knowledge and best practices

#### **Issue Reporting**
When reporting bugs or requesting features:

```markdown
## Bug Report Template

### Bug Description
Clear and concise description of what the bug is.

### To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

### Expected Behavior
Clear description of what you expected to happen.

### Screenshots
If applicable, add screenshots to help explain your problem.

### Environment:
- OS: [e.g. Windows 10, Ubuntu 20.04]
- Python Version: [e.g. 3.10.0]
- Application Version: [e.g. 1.0.0]
- Browser (if applicable): [e.g. chrome, safari]

### Additional Context
Add any other context about the problem here.
```

#### **Feature Request Template**
```markdown
## Feature Request

### Is your feature request related to a problem?
Clear description of what the problem is.

### Describe the solution you'd like
Clear and concise description of what you want to happen.

### Describe alternatives you've considered
Description of any alternative solutions or features you've considered.

### Additional context
Add any other context or screenshots about the feature request here.

### Implementation Ideas
If you have ideas about how this could be implemented, please share them.
```

## 🎯 Advanced Development Topics

### **Performance Optimization**

#### **Database Optimization**
```python
# models/optimizations.py
class DatabaseOptimizer:
    """Tools for database performance optimization."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_indexes(self):
        """Create optimized indexes for common queries."""
        # Compound index for character lookups
        self.db.characters.create_index([
            ("anime", 1),
            ("name", 1)
        ], unique=True)
        
        # Text search index
        self.db.characters.create_index([
            ("name", "text"),
            ("description", "text"),
            ("abilities", "text")
        ])
        
        # Quality score index for filtering
        self.db.characters.create_index("quality_score")
        
        # Date indexes for temporal queries
        self.db.characters.create_index("scraped_at")
        self.db.characters.create_index("updated_at")
    
    def analyze_query_performance(self, query: dict):
        """Analyze query execution performance."""
        explain_result = self.db.characters.find(query).explain()
        
        execution_stats = explain_result.get('executionStats', {})
        total_docs_examined = execution_stats.get('totalDocsExamined', 0)
        total_docs_returned = execution_stats.get('totalDocsReturned', 0)
        execution_time = execution_stats.get('executionTimeMillis', 0)
        
        efficiency_ratio = total_docs_returned / max(total_docs_examined, 1)
        
        logger.info(f"Query Performance Analysis:")
        logger.info(f"  Execution Time: {execution_time}ms")
        logger.info(f"  Documents Examined: {total_docs_examined}")
        logger.info(f"  Documents Returned: {total_docs_returned}")
        logger.info(f"  Efficiency Ratio: {efficiency_ratio:.2%}")
        
        if efficiency_ratio < 0.1:
            logger.warning("Low query efficiency detected. Consider adding indexes.")
        
        return {
            'execution_time': execution_time,
            'efficiency_ratio': efficiency_ratio,
            'needs_optimization': efficiency_ratio < 0.1
        }
```

#### **Memory Management**
```python
# utils/memory_management.py
import gc
import weakref
from typing import Dict, Any, Optional

class ResourceManager:
    """Manages application resources and memory usage."""
    
    def __init__(self):
        self._cache = {}
        self._weak_references = weakref.WeakValueDictionary()
        self._memory_threshold = 500 * 1024 * 1024  # 500MB
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache with automatic memory management."""
        if self._check_memory_usage():
            self._cleanup_cache()
        
        return self._cache.get(key)
    
    def set_cached_data(self, key: str, data: Any, ttl: int = 3600):
        """Set data in cache with TTL and memory monitoring."""
        if self._check_memory_usage():
            self._cleanup_cache()
        
        self._cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def _check_memory_usage(self) -> bool:
        """Check if memory usage exceeds threshold."""
        process = psutil.Process()
        memory_usage = process.memory_info().rss
        return memory_usage > self._memory_threshold
    
    def _cleanup_cache(self):
        """Clean up expired cache entries and force garbage collection."""
        current_time = time.time()
        expired_keys = []
        
        for key, value in self._cache.items():
            if current_time - value['timestamp'] > value['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        # Force garbage collection
        gc.collect()
        
        logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
```

### **Security Considerations**

#### **Input Validation**
```python
# utils/security.py
import re
from urllib.parse import urlparse
from typing import Union

class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL for security concerns."""
        try:
            parsed = urlparse(url)
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for valid domain
            if not parsed.netloc:
                return False
            
            # Block dangerous domains
            dangerous_domains = [
                'localhost',
                '127.0.0.1',
                '0.0.0.0',
                '10.',
                '192.168.',
                '172.16.'
            ]
            
            for dangerous in dangerous_domains:
                if parsed.netloc.startswith(dangerous):
                    return False
            
            # Block file:// and other dangerous schemes
            if parsed.scheme in ['file', 'ftp', 'gopher']:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:251] + ext
        
        return sanitized or 'unnamed_file'
    
    @staticmethod
    def validate_database_query(query: dict) -> bool:
        """Validate database query for injection attacks."""
        # Convert to string for analysis
        query_str = str(query)
        
        # Check for dangerous operators
        dangerous_operators = [
            '$where',
            '$eval',
            'mapReduce',
            'aggregate',
            '$regex'
        ]
        
        for operator in dangerous_operators:
            if operator in query_str:
                logger.warning(f"Potentially dangerous operator detected: {operator}")
                return False
        
        return True
```

### **Monitoring and Observability**

#### **Application Metrics**
```python
# utils/monitoring.py
import time
import psutil
from collections import defaultdict, deque
from typing import Dict, Any

class ApplicationMonitor:
    """Monitor application performance and health."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(deque)
        self.start_time = time.time()
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric."""
        self.counters[name] += value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric."""
        self.gauges[name] = value
    
    def record_timer(self, name: str, duration: float):
        """Record a timing metric."""
        self.timers[name].append({
            'duration': duration,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 measurements
        if len(self.timers[name]) > 1000:
            self.timers[name].popleft()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        process = psutil.Process()
        
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent(),
            'open_files': len(process.open_files()),
            'threads': process.num_threads(),
            'uptime_seconds': time.time() - self.start_time
        }
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics."""
        metrics = {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges)
        }
        
        # Calculate timer statistics
        timer_stats = {}
        for name, measurements in self.timers.items():
            if measurements:
                durations = [m['duration'] for m in measurements]
                timer_stats[name] = {
                    'count': len(durations),
                    'avg': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations)
                }
        
        metrics['timers'] = timer_stats
        
        return metrics

# Context manager for timing operations
class timer:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: ApplicationMonitor, name: str):
        self.monitor = monitor
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.monitor.record_timer(self.name, duration)
```

## 📚 Additional Resources

### **Recommended Reading**
- [Scrapy Documentation](https://docs.scrapy.org/)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Clean Architecture in Python](https://github.com/cosmic-python/book)

### **Useful Tools**
- **Code Quality**: Black, isort, flake8, mypy
- **Testing**: pytest, pytest-cov, pytest-qt
- **Profiling**: py-spy, memory_profiler, line_profiler
- **Monitoring**: Grafana, Prometheus, ELK Stack
- **Documentation**: Sphinx, MkDocs

### **Community Resources**
- **GitHub Discussions**: Project discussions and Q&A
- **Stack Overflow**: Technical questions with tags `scrapy`, `pyqt5`, `mongodb`
- **Reddit**: r/Python, r/webdev communities
- **Discord/Slack**: Python development communities

---

**Happy coding!** 🚀

Remember: Good code is not just working code, but code that is readable, maintainable, and robust. Always consider the future developer (which might be you) who will work on this code.
# 👨‍💻 Developer Guide

Welcome to the Fandom Scraper development guide! This document provides comprehensive information for developers who want to contribute to or extend the project.

## 📋 Table of Contents

- [Development Environment Setup](#-development-environment-setup)
- [Project Architecture](#-project-architecture)
- [Coding Standards](#-coding-standards)
- [Development Workflow](#-development-workflow)
- [Testing Guidelines](#-testing-guidelines)
- [Adding New Features](#-adding-new-features)
- [Debugging and Profiling](#-debugging-and-profiling)
- [Contributing Guidelines](#-contributing-guidelines)

## 🛠️ Development Environment Setup

### **Prerequisites**

- Python 3.10+
- Conda (Miniconda3 or Anaconda)
- Git
- MongoDB
- IDE (VS Code, PyCharm, or similar)

### **Development Installation**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/fandom-scraper-gui.git
cd fandom-scraper-gui

# 2. Create development environment
conda env create -f environment.yml
conda activate env-web

# 3. Install development dependencies
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Setup IDE configuration
# See IDE-specific setup instructions below
```

### **IDE Configuration**

#### **VS Code Setup**
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    }
}
```

#### **PyCharm Setup**
1. Open project in PyCharm
2. Configure Python interpreter: `Settings → Project → Python Interpreter`
3. Set up code style: `Settings → Editor → Code Style → Python`
4. Configure test runner: `Settings → Tools → Python Integrated Tools`

### **Environment Variables**

Create `.env.dev` for development:
```bash
# Development Environment Configuration
DEBUG=True
LOG_LEVEL=DEBUG

# Database (use separate dev database)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=fandom_scraper_dev

# Scraping (more conservative for development)
REQUEST_DELAY=2.0
CONCURRENT_REQUESTS=4

# Testing
TESTING=False
TEST_DATABASE=fandom_scraper_test
```

## 🏗️ Project Architecture

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                 Presentation Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ PyQt5 GUI   │  │ REST API    │  │ CLI Interface   │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                 Business Logic Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Controllers │  │ Services    │  │ Data Processors │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                 Data Access Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Repositories│  │ Models      │  │ Schemas         │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   Storage Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ MongoDB     │  │ File System │  │ Cache           │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### **Module Structure**

#### **GUI Layer** (`gui/`)
- **Purpose**: User interface components and interactions
- **Key Components**:
  - `main_window.py`: Main application window
  - `widgets/`: Custom UI components
  - `controllers/`: GUI business logic

#### **Scraper Layer** (`scraper/`)
- **Purpose**: Web scraping functionality
- **Key Components**:
  - `base_spider.py`: Abstract spider base class
  - `spiders/`: Site-specific spider implementations
  - `pipelines.py`: Data processing pipelines

#### **Models Layer** (`models/`)
- **Purpose**: Data structures and database operations
- **Key Components**:
  - `schemas/`: Pydantic data models
  - `repositories/`: Database access patterns
  - `storage.py`: Database management

#### **Utils Layer** (`utils/`)
- **Purpose**: Shared utilities and helper functions
- **Key Components**:
  - `data_processing/`: Data manipulation tools
  - `export/`: Data export functionality
  - `visualization/`: Chart and graph generation

### **Design Patterns Used**

#### **Repository Pattern**
```python
# Abstract repository interface
class BaseRepository(ABC):
    @abstractmethod
    def save(self, entity: Any) -> str:
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[Any]:
        pass

# Concrete implementation
class CharacterRepository(BaseRepository):
    def __init__(self, db_connection):
        self.collection = db_connection.characters
    
    def save(self, character: Character) -> str:
        result = self.collection.insert_one(character.dict())
        return str(result.inserted_id)
```

#### **Observer Pattern**
```python
# Progress tracking implementation
class ProgressSubject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def notify(self, progress_data):
        for observer in self._observers:
            observer.update(progress_data)

# GUI progress dialog as observer
class ProgressDialog(QDialog):
    def update(self, progress_data):
        self.progress_bar.setValue(progress_data['percentage'])
        self.status_label.setText(progress_data['message'])
```

#### **Factory Pattern**
```python
# Spider factory for different anime wikis
class SpiderFactory:
    @staticmethod
    def create_spider(anime_name: str) -> BaseSpider:
        if anime_name.lower() == "one piece":
            return OnePieceSpider()
        elif anime_name.lower() == "naruto":
            return NarutoSpider()
        else:
            return GenericFandomSpider(anime_name)
```

## 📝 Coding Standards

### **Python Style Guide**

We follow **PEP 8** with the following additions:

#### **Code Organization**
```python
"""
Module docstring explaining purpose and usage.

Example:
    from scraper.base_spider import BaseSpider
    
    spider = BaseSpider(anime_name="One Piece")
    spider.start_scraping()
"""

# Standard library imports
import os
import sys
from typing import Dict, List, Optional, Any

# Third-party imports
import scrapy
import pymongo
from PyQt5.QtWidgets import QMainWindow

# Local application imports
from models.character import Character
from utils.normalizer import DataNormalizer
```

#### **Function Documentation**
```python
def extract_character_data(response: scrapy.http.Response, 
                          selectors: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract character information from a Fandom wiki page.
    
    This function parses HTML content using configured selectors to extract
    structured character data including name, description, and relationships.
    
    Args:
        response: Scrapy Response object containing the HTML page
        selectors: Dictionary mapping field names to CSS selectors
        
    Returns:
        Dictionary containing extracted character data with keys:
        - name: Character name (str)
        - description: Character description (str)
        - age: Character age (Optional[str])
        - relationships: Character relationships (Dict[str, str])
        
    Raises:
        ValueError: If required selectors are missing
        ParseError: If HTML structure is unexpected
        
    Example:
        >>> selectors = {"name": "h1.page-title", "age": ".infobox .age"}
        >>> data = extract_character_data(response, selectors)
        >>> print(data["name"])
        "Monkey D. Luffy"
    """
    if not selectors:
        raise ValueError("Selectors dictionary cannot be empty")
    
    character_data = {}
    
    try:
        # Extract basic information
        character_data["name"] = response.css(selectors["name"]).get()
        character_data["age"] = response.css(selectors.get("age", "")).get()
        
        return character_data
        
    except Exception as e:
        logger.error(f"Failed to extract character data: {e}")
        raise ParseError(f"Character parsing failed: {e}")
```

#### **Class Design**
```python
class CharacterSpider(BaseSpider):
    """
    Spider for extracting character data from Fandom wikis.
    
    This spider specializes in parsing character pages to extract
    comprehensive information including basic details, relationships,
    and associated media files.
    
    Attributes:
        name: Spider identifier for Scrapy framework
        allowed_domains: List of domains this spider can crawl
        character_count: Number of characters processed
        
    Example:
        >>> spider = CharacterSpider(anime_name="One Piece")
        >>> spider.start_urls = ["https://onepiece.fandom.com/wiki/Category:Characters"]
        >>> spider.start()
    """
    
    name = "character_spider"
    allowed_domains = ["fandom.com"]
    
    def __init__(self, anime_name: str = None, **kwargs):
        """Initialize character spider with anime-specific configuration."""
        super().__init__(**kwargs)
        self.anime_name = anime_name
        self.character_count = 0
        self._setup_selectors()
    
    def _setup_selectors(self) -> None:
        """Load and configure CSS selectors for this anime."""
        # Implementation details...
        pass
```

### **Error Handling Standards**

#### **Exception Hierarchy**
```python
# Custom exception hierarchy
class FandomScraperError(Exception):
    """Base exception for all scraper-related errors."""
    pass

class ScrapingError(FandomScraperError):
    """Raised when web scraping operations fail."""
    pass

class ValidationError(FandomScraperError):
    """Raised when data validation fails."""
    pass

class DatabaseError(FandomScraperError):
    """Raised when database operations fail."""
    pass
```

#### **Error Handling Patterns**
```python
def save_character_data(character_data: Dict[str, Any]) -> Optional[str]:
    """Save character data with comprehensive error handling."""
    try:
        # Validate data
        validated_data = Character(**character_data)
        
        # Save to database
        character_id = repository.save(validated_data)
        logger.info(f"Character saved successfully: {character_id}")
        return character_id
        
    except ValidationError as e:
        logger.warning(f"Data validation failed: {e}")
        # Handle validation errors gracefully
        return None
        
    except DatabaseError as e:
        logger.error(f"Database operation failed: {e}")
        # Retry logic or fallback behavior
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in save_character_data: {e}")
        # Log full traceback for debugging
        logger.exception("Full traceback:")
        raise FandomScraperError(f"Character save failed: {e}")
```

### **Logging Standards**

```python
import logging
from utils.logger import get_logger

# Get module-specific logger
logger = get_logger(__name__)

def process_character_page(url: str) -> Dict[str, Any]:
    """Process character page with structured logging."""
    logger.info(f"Processing character page: {url}")
    
    try:
        # Processing logic
        character_data = extract_data(url)
        logger.debug(f"Extracted data fields: {list(character_data.keys())}")
        
        # Validation
        if not character_data.get('name'):
            logger.warning(f"Missing character name for URL: {url}")
        
        logger.info(f"Successfully processed character: {character_data.get('name')}")
        return character_data
        
    except Exception as e:
        logger.error(f"Failed to process character page {url}: {e}")
        raise
```

## 🔄 Development Workflow

### **Git Workflow**

#### **Branch Strategy**
```bash
# Main branches
main          # Production-ready code
develop       # Integration branch

# Feature branches
feature/character-scraper      # New character scraping feature
feature/gui-progress-dialog    # GUI progress dialog
bugfix/memory-leak-fix         # Bug fix

# Release branches
release/v1.0.0                 # Release preparation
```

#### **Commit Message Format**
We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>[optional scope]: <description>

# Feature commits
git commit -m "feat(scraper): implement One Piece character spider"
git commit -m "feat(gui): add real-time progress tracking dialog"

# Bug fix commits
git commit -m "fix(database): resolve MongoDB connection timeout issue"
git commit -m "fix(gui): fix thread safety in progress updates"

# Documentation commits
git commit -m "docs: add comprehensive API documentation"
git commit -m "docs(installation): update cross-platform setup guide"

# Refactoring commits
git commit -m "refactor(models): extract common base class for data models"
git commit -m "refactor: optimize data normalization performance"

# Style/formatting commits
git commit -m "style: format code with Black formatter"

# Test commits
git commit -m "test: add unit tests for character data validation"

# Chore commits
git commit -m "chore: update dependencies to latest versions"
git commit -m "chore(ci): configure GitHub Actions workflow"
```

### **Development Process**

#### **Weekly Development Cycle**

**Monday: Planning & Setup**
```bash
# 1. Update from develop branch
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/new-feature-name

# 3. Review week's objectives
# - Check project roadmap
# - Identify dependencies
# - Plan implementation approach
```

**Tuesday-Thursday: Development**
```bash
# 1. Implement features with regular commits
git add .
git commit -m "feat: implement basic feature structure"

# 2. Write tests alongside development
pytest tests/unit/test_new_feature.py

# 3. Update documentation
# - Add docstrings
# - Update relevant .md files

# 4. Run code quality checks
black .
isort .
flake8 .
mypy .
```

**Friday: Integration & Review**
```bash
# 1. Final testing
pytest tests/

# 2. Code review preparation
git rebase develop  # Clean up commit history

# 3. Create pull request
# - Comprehensive description
# - Link to related issues
# - Add reviewers

# 4. Merge to develop after approval
git checkout develop
git merge feature/new-feature-name
git push origin develop

# 5. Cleanup
git branch -d feature/new-feature-name
```

### **Code Review Process**

#### **Review Checklist**
- [ ] Code follows project style guidelines
- [ ] All functions have appropriate docstrings
- [ ] Error handling is comprehensive
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] No hardcoded values or credentials
- [ ] Performance implications considered
- [ ] Security best practices followed

#### **Review Template**
```markdown
## Summary
Brief description of changes and their purpose.

## Changes Made
- [ ] Feature implementation
- [ ] Test coverage
- [ ] Documentation updates
- [ ] Bug fixes

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance testing (if applicable)

## Breaking Changes
List any breaking changes and migration steps.

## Additional Notes
Any additional context or considerations for review