"""
Scraper controller for managing web scraping operations from GUI.

This controller acts as a bridge between the GUI components and the
Scrapy spider system, providing thread-safe operation management,
progress tracking, and data handling.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
import subprocess
import sys
import os

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, QMutex, QMutexLocker
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from twisted.internet.defer import inlineCallbacks

from utils.logger import get_logger
from scraper.fandom_spider import FandomSpider
from scraper.onepiece_spider import OnePieceSpider
from models.storage import DatabaseManager


class ScrapyWorkerThread(QThread):
    """
    Worker thread for running Scrapy spiders.

    Runs scrapy operations in a separate thread to prevent
    GUI blocking and provide proper isolation.
    """

    # Signals for communication with main thread
    spider_started = pyqtSignal(str)  # Spider name
    spider_finished = pyqtSignal(dict)  # Results
    spider_error = pyqtSignal(str)  # Error message
    progress_updated = pyqtSignal(str, int)  # Message and progress
    data_received = pyqtSignal(dict)  # Individual item data

    def __init__(self, config: Dict[str, Any], parent=None):
        """
        Initialize the worker thread.

        Args:
            config: Scraping configuration
            parent: Parent QObject
        """
        super().__init__(parent)

        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.is_running = False
        self.should_stop = False
        self.should_pause = False

        # Results storage
        self.scraped_data = []
        self.statistics = {
            "items_scraped": 0,
            "pages_processed": 0,
            "errors_encountered": 0,
            "start_time": None,
            "end_time": None,
        }

        # Thread safety
        self.mutex = QMutex()

    def run(self):
        """Main thread execution method."""
        try:
            with QMutexLocker(self.mutex):
                self.is_running = True
                self.should_stop = False
                self.statistics["start_time"] = datetime.now()

            self.logger.info("Starting scraper worker thread")
            self.spider_started.emit(self.config.get("anime_name", "Unknown"))

            # Run the scraping operation
            self.run_scraping()

        except Exception as e:
            self.logger.error(f"Worker thread error: {e}")
            self.spider_error.emit(str(e))
        finally:
            with QMutexLocker(self.mutex):
                self.is_running = False
                self.statistics["end_time"] = datetime.now()

            if not self.should_stop:
                self.spider_finished.emit(self.get_results())

    def run_scraping(self):
        """Execute the scraping operation."""
        # Create spider instance
        spider_class = self.get_spider_class()
        if not spider_class:
            raise ValueError("No suitable spider class found")

        # Configure spider settings
        settings = self.get_spider_settings()

        # Create spider instance with callbacks
        spider = spider_class(
            anime_name=self.config.get("anime_name", "unknown"),
            base_url=self.config.get("base_url", ""),
            character_list_url=self.config.get("character_list_url", ""),
            max_characters=self.config.get("max_characters", 100),
            progress_callback=self.on_progress_update,
            data_callback=self.on_data_received,
            error_callback=self.on_error_occurred,
        )

        # Configure spider with custom settings
        self.configure_spider(spider)

        # Start scraping process
        self.run_spider_process(spider, settings)

    def get_spider_class(self):
        """
        Get appropriate spider class based on configuration.

        Returns:
            Spider class to use
        """
        anime_name = self.config.get("anime_name", "").lower()

        if "one piece" in anime_name:
            return OnePieceSpider
        else:
            return FandomSpider

    def get_spider_settings(self) -> Dict[str, Any]:
        """
        Generate Scrapy settings from configuration.

        Returns:
            Settings dictionary for Scrapy
        """
        settings = {
            "ROBOTSTXT_OBEY": True,
            "DOWNLOAD_DELAY": self.config.get("download_delay", 1.0),
            "RANDOMIZE_DOWNLOAD_DELAY": self.config.get("randomize_delay", True),
            "CONCURRENT_REQUESTS": self.config.get("concurrent_requests", 8),
            "RETRY_TIMES": self.config.get("retry_times", 3),
            "RETRY_HTTP_CODES": self.config.get(
                "retry_http_codes", [500, 502, 503, 504, 408, 429]
            ),
            "USER_AGENT": self.config.get("user_agent", "fandom-scraper 1.0"),
            # Memory settings
            "MEMUSAGE_ENABLED": True,
            "MEMUSAGE_LIMIT_MB": self.config.get("memory_limit_mb", 2048),
            # Cache settings
            "HTTPCACHE_ENABLED": self.config.get("cache_enabled", False),
            "HTTPCACHE_EXPIRATION_SECS": self.config.get("cache_expiration", 3600),
            # Auto throttle
            "AUTOTHROTTLE_ENABLED": self.config.get("auto_throttle", True),
            "AUTOTHROTTLE_START_DELAY": 1,
            "AUTOTHROTTLE_MAX_DELAY": 60,
            "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
            # Pipelines
            "ITEM_PIPELINES": {
                "scraper.pipelines.DuplicateFilterPipeline": 100,
                "scraper.pipelines.DataValidationPipeline": 200,
                "scraper.pipelines.ImageDownloadPipeline": 300,
                "scraper.pipelines.DataStoragePipeline": 500,
            },
            # Logging
            "LOG_LEVEL": self.config.get("log_level", "INFO"),
            "LOG_ENABLED": True,
        }

        # Add custom headers if specified
        custom_headers = self.config.get("custom_headers", {})
        if custom_headers:
            settings["DEFAULT_REQUEST_HEADERS"] = custom_headers

        # Add proxy settings if enabled
        if self.config.get("proxy_enabled", False):
            proxy_url = self.config.get("proxy_url", "")
            if proxy_url:
                settings["DOWNLOADER_MIDDLEWARES"] = {
                    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 110,
                }
                settings["HTTP_PROXY"] = proxy_url

        return settings

    def configure_spider(self, spider):
        """
        Configure spider with custom settings.

        Args:
            spider: Spider instance to configure
        """
        # Set selector configuration
        selectors = {
            "name": self.config.get("name_selector", ""),
            "description": self.config.get("description_selector", ""),
            "infobox": self.config.get("infobox_selector", ""),
            "images": self.config.get("image_selector", ""),
            "categories": self.config.get("categories_selector", ""),
        }
        spider.selector_config = {"character_page": selectors}

        # Set extraction options
        spider.extract_options = {
            "infobox": self.config.get("extract_infobox", True),
            "images": self.config.get("extract_images", True),
            "categories": self.config.get("extract_categories", True),
            "relationships": self.config.get("extract_relationships", False),
            "abilities": self.config.get("extract_abilities", False),
            "appearances": self.config.get("extract_appearances", False),
        }

        # Set limits
        spider.max_characters = self.config.get("max_characters", 100)
        spider.max_pages_per_character = self.config.get("max_pages_per_character", 5)
        spider.max_images_per_character = self.config.get(
            "max_images_per_character", 10
        )

    def run_spider_process(self, spider, settings: Dict[str, Any]):
        """
        Run the spider using subprocess to avoid reactor issues.

        Args:
            spider: Spider instance
            settings: Spider settings
        """
        try:
            # Create a simple script to run the spider
            script_content = self.generate_spider_script(spider, settings)

            # Write script to temporary file
            script_path = Path.cwd() / "temp_spider_script.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Run spider in subprocess
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path.cwd()),
            )

            # Monitor process output
            self.monitor_spider_process(process)

            # Clean up temporary script
            script_path.unlink(missing_ok=True)

        except Exception as e:
            self.logger.error(f"Failed to run spider process: {e}")
            raise

    def generate_spider_script(self, spider, settings: Dict[str, Any]) -> str:
        """
        Generate Python script for running the spider.

        Args:
            spider: Spider instance
            settings: Spider settings

        Returns:
            Python script content
        """
        script = f"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scrapy.crawler import CrawlerProcess
from scraper.{spider.__class__.__module__.split('.')[-1]} import {spider.__class__.__name__}

def main():
    # Configure process settings
    settings = {repr(settings)}

    # Create crawler process
    process = CrawlerProcess(settings)

    # Add spider with configuration
    process.crawl(
        {spider.__class__.__name__},
        anime_name="{spider.anime_name}",
        base_url="{spider.base_url}",
        character_list_url="{spider.character_list_url}",
        max_characters={spider.max_characters}
    )

    # Start crawling
    process.start()

if __name__ == "__main__":
    main()
"""
        return script

    def monitor_spider_process(self, process):
        """
        Monitor spider process output and update progress.

        Args:
            process: Subprocess instance
        """
        try:
            # Read output line by line
            while True:
                with QMutexLocker(self.mutex):
                    if self.should_stop:
                        process.terminate()
                        break

                # Check if process is still running
                if process.poll() is not None:
                    break

                # Read output with timeout
                try:
                    output = process.stdout.readline()
                    if output:
                        self.parse_spider_output(output.strip())
                except:
                    pass

                # Small delay to prevent high CPU usage
                time.sleep(0.1)

            # Wait for process to complete
            return_code = process.wait()

            if return_code != 0:
                error_output = process.stderr.read()
                self.logger.error(f"Spider process failed: {error_output}")
                self.spider_error.emit(f"Spider process failed with code {return_code}")

        except Exception as e:
            self.logger.error(f"Error monitoring spider process: {e}")
            self.spider_error.emit(str(e))

    def parse_spider_output(self, output: str):
        """
        Parse spider output for progress updates.

        Args:
            output: Output line from spider
        """
        # Simple parsing - in a real implementation, you'd use structured logging
        if "Scraped" in output:
            self.statistics["items_scraped"] += 1
            progress = min(
                100,
                (
                    self.statistics["items_scraped"]
                    / self.config.get("max_characters", 100)
                )
                * 100,
            )
            self.progress_updated.emit(
                f"Scraped item {self.statistics['items_scraped']}", int(progress)
            )

        elif "ERROR" in output:
            self.statistics["errors_encountered"] += 1
            self.spider_error.emit(output)

    # Callback methods for spider communication
    def on_progress_update(self, message: str, progress: int):
        """Handle progress updates from spider."""
        self.progress_updated.emit(message, progress)

    def on_data_received(self, data: Dict[str, Any]):
        """Handle data received from spider."""
        with QMutexLocker(self.mutex):
            self.scraped_data.append(data)

        self.data_received.emit(data)

    def on_error_occurred(self, error: str):
        """Handle errors from spider."""
        with QMutexLocker(self.mutex):
            self.statistics["errors_encountered"] += 1

        self.spider_error.emit(error)

    def stop_scraping(self):
        """Request scraping to stop."""
        with QMutexLocker(self.mutex):
            self.should_stop = True

        self.logger.info("Stop requested for scraper worker")

    def pause_scraping(self):
        """Request scraping to pause."""
        with QMutexLocker(self.mutex):
            self.should_pause = True

    def resume_scraping(self):
        """Request scraping to resume."""
        with QMutexLocker(self.mutex):
            self.should_pause = False

    def get_results(self) -> Dict[str, Any]:
        """
        Get scraping results.

        Returns:
            Dictionary containing results and statistics
        """
        with QMutexLocker(self.mutex):
            return {
                "characters": self.scraped_data.copy(),
                "statistics": self.statistics.copy(),
                "config": self.config.copy(),
            }


class ScraperController(QObject):
    """
    Main controller for managing web scraping operations.

    Provides high-level interface for starting, stopping, and monitoring
    scraping operations from the GUI components.
    """

    # Signals for GUI communication
    scraping_started = pyqtSignal(str)  # Anime name
    scraping_finished = pyqtSignal(dict)  # Results
    scraping_stopped = pyqtSignal()  # User stopped
    progress_updated = pyqtSignal(str, int)  # Message and progress
    status_updated = pyqtSignal(str)  # Status message
    error_occurred = pyqtSignal(str)  # Error message
    data_received = pyqtSignal(dict)  # Individual item data

    def __init__(self, parent=None):
        """
        Initialize the scraper controller.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        # Initialize logger
        self.logger = get_logger(self.__class__.__name__)

        # State management
        self.is_scraping = False
        self.current_worker = None
        self.current_config = None

        # Database manager
        self.db_manager = None

        # Results storage
        self.last_results = {}
        self.scraped_items = []

        # Thread safety
        self.mutex = QMutex()

        self.logger.info("Scraper controller initialized")

    def start_scraping(self, config: Dict[str, Any]):
        """
        Start a new scraping operation.

        Args:
            config: Scraping configuration dictionary
        """
        with QMutexLocker(self.mutex):
            if self.is_scraping:
                self.logger.warning("Scraping already in progress")
                self.error_occurred.emit("Scraping already in progress")
                return

            self.is_scraping = True
            self.current_config = config.copy()
            self.scraped_items = []

        try:
            # Validate configuration
            self.validate_configuration(config)

            # Initialize database connection if needed
            self.initialize_database(config)

            # Create and configure worker thread
            self.current_worker = ScrapyWorkerThread(config, self)
            self.setup_worker_connections()

            # Start worker thread
            self.current_worker.start()

            anime_name = config.get("anime_name", "Unknown")
            self.logger.info(f"Started scraping for {anime_name}")
            self.status_updated.emit(f"Started scraping {anime_name}")
            self.scraping_started.emit(anime_name)

        except Exception as e:
            with QMutexLocker(self.mutex):
                self.is_scraping = False
                self.current_worker = None

            error_msg = f"Failed to start scraping: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

    def stop_scraping(self):
        """Stop the current scraping operation."""
        with QMutexLocker(self.mutex):
            if not self.is_scraping or not self.current_worker:
                self.logger.warning("No scraping operation to stop")
                return

            worker = self.current_worker

        try:
            # Request worker to stop
            worker.stop_scraping()

            # Wait for worker to finish (with timeout)
            if worker.wait(5000):  # 5 second timeout
                self.logger.info("Scraping stopped successfully")
                self.status_updated.emit("Scraping stopped")
                self.scraping_stopped.emit()
            else:
                # Force terminate if doesn't stop gracefully
                worker.terminate()
                worker.wait(2000)
                self.logger.warning("Scraping force terminated")
                self.status_updated.emit("Scraping force stopped")
                self.scraping_stopped.emit()

        except Exception as e:
            error_msg = f"Error stopping scraping: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            with QMutexLocker(self.mutex):
                self.is_scraping = False
                self.current_worker = None

    def pause_scraping(self):
        """Pause the current scraping operation."""
        with QMutexLocker(self.mutex):
            if not self.is_scraping or not self.current_worker:
                return

            worker = self.current_worker

        worker.pause_scraping()
        self.status_updated.emit("Scraping paused")
        self.logger.info("Scraping paused")

    def resume_scraping(self):
        """Resume the paused scraping operation."""
        with QMutexLocker(self.mutex):
            if not self.is_scraping or not self.current_worker:
                return

            worker = self.current_worker

        worker.resume_scraping()
        self.status_updated.emit("Scraping resumed")
        self.logger.info("Scraping resumed")

    def validate_configuration(self, config: Dict[str, Any]):
        """
        Validate scraping configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ["anime_name", "base_url", "character_list_url"]

        for field in required_fields:
            if not config.get(field):
                raise ValueError(f"Required field '{field}' is missing or empty")

        # Validate URLs
        for url_field in ["base_url", "character_list_url"]:
            url = config.get(url_field, "")
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"'{url_field}' must be a valid HTTP/HTTPS URL")

        # Validate numeric fields
        numeric_fields = {
            "max_characters": (1, 10000),
            "download_delay": (0.1, 60.0),
            "concurrent_requests": (1, 32),
            "retry_times": (0, 10),
        }

        for field, (min_val, max_val) in numeric_fields.items():
            value = config.get(field)
            if value is not None:
                if not isinstance(value, (int, float)) or not (
                    min_val <= value <= max_val
                ):
                    raise ValueError(
                        f"'{field}' must be between {min_val} and {max_val}"
                    )

    def initialize_database(self, config: Dict[str, Any]):
        """
        Initialize database connection.

        Args:
            config: Configuration containing database settings
        """
        try:
            mongo_uri = config.get("mongo_uri", "mongodb://localhost:27017/")
            db_name = config.get("database_name", "fandom_scraper")

            self.db_manager = DatabaseManager(mongo_uri, db_name)
            self.db_manager.connect()

            self.logger.info("Database connection initialized")

        except Exception as e:
            # Database connection failure is not critical
            self.logger.warning(f"Database connection failed: {e}")
            self.db_manager = None

    def setup_worker_connections(self):
        """Set up signal connections for worker thread."""
        if not self.current_worker:
            return

        worker = self.current_worker

        # Connect worker signals
        worker.spider_started.connect(self.on_worker_started)
        worker.spider_finished.connect(self.on_worker_finished)
        worker.spider_error.connect(self.on_worker_error)
        worker.progress_updated.connect(self.on_worker_progress)
        worker.data_received.connect(self.on_worker_data)

    # Worker signal handlers
    def on_worker_started(self, anime_name: str):
        """Handle worker started signal."""
        self.status_updated.emit(f"Scraping {anime_name} started")

    def on_worker_finished(self, results: Dict[str, Any]):
        """Handle worker finished signal."""
        with QMutexLocker(self.mutex):
            self.is_scraping = False
            self.current_worker = None
            self.last_results = results.copy()

        # Store results in database if available
        if self.db_manager:
            try:
                characters = results.get("characters", [])
                for character in characters:
                    self.db_manager.save_character(character)  # type: ignore

                self.logger.info(f"Saved {len(characters)} characters to database")

            except Exception as e:
                self.logger.error(f"Failed to save to database: {e}")

        # Emit completion signal
        statistics = results.get("statistics", {})
        items_count = len(results.get("characters", []))

        self.status_updated.emit(f"Scraping completed - {items_count} items scraped")
        self.scraping_finished.emit(results)

        self.logger.info(f"Scraping completed with {items_count} items")

    def on_worker_error(self, error_message: str):
        """Handle worker error signal."""
        self.logger.error(f"Worker error: {error_message}")
        self.error_occurred.emit(error_message)

    def on_worker_progress(self, message: str, progress: int):
        """Handle worker progress signal."""
        self.progress_updated.emit(message, progress)

    def on_worker_data(self, data: Dict[str, Any]):
        """Handle individual data items from worker."""
        with QMutexLocker(self.mutex):
            self.scraped_items.append(data)

        self.data_received.emit(data)

    # Public methods for external access
    def get_scraping_status(self) -> Dict[str, Any]:
        """
        Get current scraping status.

        Returns:
            Dictionary containing status information
        """
        with QMutexLocker(self.mutex):
            return {
                "is_scraping": self.is_scraping,
                "current_config": (
                    self.current_config.copy() if self.current_config else {}
                ),
                "items_scraped": len(self.scraped_items),
                "has_worker": self.current_worker is not None,
            }

    def get_last_results(self) -> Dict[str, Any]:
        """
        Get results from last completed scraping operation.

        Returns:
            Dictionary containing last results
        """
        with QMutexLocker(self.mutex):
            return self.last_results.copy()

    def get_current_items(self) -> List[Dict[str, Any]]:
        """
        Get items scraped in current session.

        Returns:
            List of scraped items
        """
        with QMutexLocker(self.mutex):
            return self.scraped_items.copy()

    def test_connection(self, url: str) -> bool:
        """
        Test connection to a target URL.

        Args:
            url: URL to test

        Returns:
            True if connection successful
        """
        try:
            import requests

            response = requests.get(url, timeout=10)
            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def test_database_connection(self, mongo_uri: str, db_name: str) -> bool:
        """
        Test database connection.

        Args:
            mongo_uri: MongoDB URI
            db_name: Database name

        Returns:
            True if connection successful
        """
        try:
            test_manager = DatabaseManager(mongo_uri, db_name)
            test_manager.connect()
            test_manager.disconnect()
            return True

        except Exception as e:
            self.logger.error(f"Database test failed: {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        # Stop any running scraping
        if self.is_scraping:
            self.stop_scraping()

        # Close database connection
        if self.db_manager:
            self.db_manager.disconnect()

        self.logger.info("Scraper controller cleaned up")
