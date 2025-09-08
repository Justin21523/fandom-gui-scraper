# scraper/settings.py
"""
Scrapy Configuration Settings

This module contains all configuration settings for the Fandom scraper,
including pipeline configurations, download settings, and middleware.
"""

import os
from pathlib import Path


# Scrapy Project Settings
BOT_NAME = "fandom_scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure User Agent
USER_AGENT = "FandomScraper/1.0 (+https://github.com/user/fandom-scraper)"

# Configure delays and concurrency
DOWNLOAD_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_DELAY_RANDOMIZE_RANGE = 0.5

# Concurrent requests settings
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# AutoThrottle extension settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# Cookie settings
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Telnet Console (for debugging)
TELNETCONSOLE_ENABLED = False

# Database Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "fandom_scraper")

# Image Storage Configuration
PROJECT_ROOT = Path(__file__).parent.parent
IMAGES_STORE = str(PROJECT_ROOT / "storage" / "images")
IMAGES_EXPIRES = 365  # Days to keep images
IMAGES_THUMBS = {
    "small": (50, 50),
    "medium": (150, 150),
    "large": (300, 300),
}

# File Storage Configuration
FILES_STORE = str(PROJECT_ROOT / "storage" / "files")
FILES_EXPIRES = 90

# Configure Pipelines (order matters!)
ITEM_PIPELINES = {
    # Data validation and normalization (first)
    "scraper.pipelines.DuplicateFilterPipeline": 100,
    "scraper.pipelines.DataValidationPipeline": 200,
    # Image processing
    "scraper.pipelines.ImageDownloadPipeline": 300,
    # Quality assessment
    "scraper.pipelines.DataQualityPipeline": 400,
    # Database storage (last)
    "scraper.pipelines.DataStoragePipeline": 500,
}

# Configure Middlewares
DOWNLOADER_MIDDLEWARES = {
    # User Agent rotation middleware
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
    # Retry middleware
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    # HTTP cache middleware (for development)
    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 900,
}

# HTTP Cache settings (useful for development)
HTTPCACHE_ENABLED = False  # Set to True for development
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour
HTTPCACHE_DIR = str(PROJECT_ROOT / ".scrapy" / "httpcache")
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 403, 404, 408, 429]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = str(PROJECT_ROOT / "logs" / "scrapy.log")
LOG_ENCODING = "utf-8"
LOG_STDOUT = True

# Custom logging format
LOG_FORMAT = "%(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# Memory usage monitoring
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048  # 2GB
MEMUSAGE_WARNING_MB = 1024  # 1GB

# Stats collection
STATS_CLASS = "scrapy.statscollectors.MemoryStatsCollector"

# Extensions
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
    "scrapy.extensions.memusage.MemoryUsage": 0,
    "scrapy.extensions.closespider.CloseSpider": 0,
}

# Spider close reasons
CLOSESPIDER_ERRORCOUNT = 100  # Close spider after 100 errors
CLOSESPIDER_ITEMCOUNT = 0  # No limit on items (set to number to limit)
CLOSESPIDER_PAGECOUNT = 0  # No limit on pages
CLOSESPIDER_TIMEOUT = 0  # No timeout (set to seconds for timeout)

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

# Compression
COMPRESSION_ENABLED = True

# DNS settings
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# FTP settings (if needed)
FTP_USER = "anonymous"
FTP_PASSWORD = "guest"

# Media pipeline settings
MEDIA_ALLOW_REDIRECTS = True


# Custom Settings for Different Environments
class DevelopmentSettings:
    """Development environment settings."""

    # Enable debugging features
    HTTPCACHE_ENABLED = True
    LOG_LEVEL = "DEBUG"
    AUTOTHROTTLE_DEBUG = True
    COOKIES_DEBUG = True

    # Reduced delays for faster development
    DOWNLOAD_DELAY = 0.5
    CONCURRENT_REQUESTS = 32
    CONCURRENT_REQUESTS_PER_DOMAIN = 16

    # Memory settings for development
    MEMUSAGE_LIMIT_MB = 1024  # 1GB
    MEMUSAGE_WARNING_MB = 512  # 512MB


class ProductionSettings:
    """Production environment settings."""

    # Conservative settings for production
    DOWNLOAD_DELAY = 2.0
    RANDOMIZE_DOWNLOAD_DELAY = True
    DOWNLOAD_DELAY_RANDOMIZE_RANGE = 1.0

    # Respect servers in production
    CONCURRENT_REQUESTS = 8
    CONCURRENT_REQUESTS_PER_DOMAIN = 4

    # Robust retry settings
    RETRY_TIMES = 5
    AUTOTHROTTLE_MAX_DELAY = 30.0

    # Production logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "/var/log/fandom_scraper/scrapy.log"

    # Disable debug features
    HTTPCACHE_ENABLED = False
    AUTOTHROTTLE_DEBUG = False
    TELNETCONSOLE_ENABLED = False


class TestingSettings:
    """Testing environment settings."""

    # Fast settings for testing
    DOWNLOAD_DELAY = 0
    RANDOMIZE_DOWNLOAD_DELAY = False
    CONCURRENT_REQUESTS = 64

    # Disable unnecessary features
    ROBOTSTXT_OBEY = False
    HTTPCACHE_ENABLED = True

    # Test-specific pipelines
    ITEM_PIPELINES = {
        "scraper.pipelines.DataValidationPipeline": 200,
        "scraper.pipelines.DataQualityPipeline": 400,
    }

    # Use in-memory database for testing
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DATABASE = "fandom_scraper_test"

    # Minimal logging for tests
    LOG_LEVEL = "WARNING"
    LOG_STDOUT = False


def get_settings_for_environment(env: str = None) -> dict:  # type: ignore
    """
    Get Scrapy settings for specific environment.

    Args:
        env: Environment name ('development', 'production', 'testing')

    Returns:
        Dictionary of settings for the environment
    """
    # Default settings (base configuration)
    settings = {
        "BOT_NAME": BOT_NAME,
        "SPIDER_MODULES": SPIDER_MODULES,
        "NEWSPIDER_MODULE": NEWSPIDER_MODULE,
        "ROBOTSTXT_OBEY": ROBOTSTXT_OBEY,
        "USER_AGENT": USER_AGENT,
        "DOWNLOAD_DELAY": DOWNLOAD_DELAY,
        "RANDOMIZE_DOWNLOAD_DELAY": RANDOMIZE_DOWNLOAD_DELAY,
        "CONCURRENT_REQUESTS": CONCURRENT_REQUESTS,
        "CONCURRENT_REQUESTS_PER_DOMAIN": CONCURRENT_REQUESTS_PER_DOMAIN,
        "AUTOTHROTTLE_ENABLED": AUTOTHROTTLE_ENABLED,
        "RETRY_ENABLED": RETRY_ENABLED,
        "RETRY_TIMES": RETRY_TIMES,
        "MONGO_URI": MONGO_URI,
        "MONGO_DATABASE": MONGO_DATABASE,
        "IMAGES_STORE": IMAGES_STORE,
        "ITEM_PIPELINES": ITEM_PIPELINES,
        "DOWNLOADER_MIDDLEWARES": DOWNLOADER_MIDDLEWARES,
        "LOG_LEVEL": LOG_LEVEL,
        "LOG_FILE": LOG_FILE,
        "EXTENSIONS": EXTENSIONS,
    }

    # Apply environment-specific overrides
    if env == "development":
        env_settings = DevelopmentSettings()
    elif env == "production":
        env_settings = ProductionSettings()
    elif env == "testing":
        env_settings = TestingSettings()
    else:
        # Use default settings
        return settings

    # Merge environment settings
    for attr_name in dir(env_settings):
        if not attr_name.startswith("_"):
            settings[attr_name] = getattr(env_settings, attr_name)

    return settings


# Spider-specific settings
SPIDER_SETTINGS = {
    "onepiece": {
        "DOWNLOAD_DELAY": 1.5,  # Be extra respectful to One Piece wiki
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "CLOSESPIDER_ITEMCOUNT": 200,  # Limit for testing
    },
    "naruto": {
        "DOWNLOAD_DELAY": 1.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 6,
    },
    "dragonball": {
        "DOWNLOAD_DELAY": 1.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 6,
    },
}


def get_spider_settings(spider_name: str) -> dict:
    """
    Get spider-specific settings.

    Args:
        spider_name: Name of the spider

    Returns:
        Dictionary of spider-specific settings
    """
    return SPIDER_SETTINGS.get(spider_name, {})


# User Agent Pool for rotation
USER_AGENT_POOL = [
    "FandomScraper/1.0 (+https://github.com/user/fandom-scraper)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
]

# Headers to use for requests
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Feed exports configuration for data output
FEEDS = {
    "storage/exports/characters_%(name)s_%(time)s.json": {
        "format": "json",
        "encoding": "utf8",
        "store_empty": False,
        "fields": ["name", "anime_name", "description", "quality_score", "source_url"],
        "indent": 2,
    },
    "storage/exports/characters_%(name)s_%(time)s.csv": {
        "format": "csv",
        "encoding": "utf8",
        "store_empty": False,
        "fields": ["name", "anime_name", "description", "quality_score", "source_url"],
    },
}

# Item export settings
FEED_EXPORT_ENCODING = "utf-8"
FEED_STORE_EMPTY = False
FEED_EXPORT_INDENT = 2

# Dupefilter settings
DUPEFILTER_CLASS = "scrapy.dupefilters.RFPDupeFilter"
DUPEFILTER_DEBUG = False

# Scheduler settings
SCHEDULER_PRIORITY_QUEUE = "scrapy.pqueues.ScrapyPriorityQueue"

# Item processor settings
ITEM_PROCESSOR = "itemproc.ItemProcessor"

# Reactor settings
REACTOR_THREADPOOL_MAXSIZE = 20

# Twisted settings
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# SSL/TLS settings
DOWNLOADER_CLIENT_TLS_METHOD = "TLS"

# HTTP settings
DOWNLOAD_TIMEOUT = 180
DOWNLOAD_MAXSIZE = 1073741824  # 1GB
DOWNLOAD_WARNSIZE = 33554432  # 32MB

# Proxy settings (if needed)
# DOWNLOADER_MIDDLEWARES['scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware'] = 110
# HTTPPROXY_ENABLED = True

# Ban avoidance settings
RANDOMIZE_DOWNLOAD_DELAY = True
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Custom validation settings for pipelines
VALIDATION_SETTINGS = {
    "required_fields": ["name", "anime_name", "source_url"],
    "min_name_length": 2,
    "max_name_length": 100,
    "min_description_length": 0,
    "max_description_length": 5000,
    "max_images_per_character": 20,
    "allowed_image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
    "max_image_size_mb": 10,
}

# Quality scoring settings
QUALITY_SETTINGS = {
    "high_quality_threshold": 80,
    "medium_quality_threshold": 50,
    "weights": {
        "name": 10,
        "description": 8,
        "images": 6,
        "relationships": 4,
        "abilities": 4,
        "appearances": 3,
        "metadata": 2,
    },
}

# Anti-ban settings
ANTI_BAN_SETTINGS = {
    "user_agent_rotation": True,
    "proxy_rotation": False,
    "delay_randomization": True,
    "respect_robots_txt": True,
    "max_requests_per_minute": 30,
    "session_rotation_interval": 100,  # requests
}

# Performance monitoring settings
PERFORMANCE_SETTINGS = {
    "enable_memory_monitoring": True,
    "enable_stats_collection": True,
    "stats_dump_interval": 300,  # seconds
    "memory_warning_threshold_mb": 1024,
    "memory_limit_threshold_mb": 2048,
}

# Error handling settings
ERROR_SETTINGS = {
    "max_errors_per_spider": 50,
    "error_retry_delay": 5.0,
    "error_backoff_factor": 2.0,
    "max_error_retry_delay": 300.0,
}

# Development helper settings
DEVELOPMENT_SETTINGS = {
    "enable_debug_logging": False,
    "save_failed_responses": True,
    "failed_responses_dir": "storage/debug/failed_responses",
    "enable_request_debugging": False,
    "enable_item_debugging": False,
}


# Environment-specific configuration loader
def configure_for_environment():
    """
    Configure settings based on environment variables.
    """
    import os

    env = os.getenv("SCRAPY_ENV", "development").lower()

    if env == "production":
        # Production overrides
        globals().update(
            {
                "LOG_LEVEL": "INFO",
                "DOWNLOAD_DELAY": 2.0,
                "CONCURRENT_REQUESTS": 8,
                "HTTPCACHE_ENABLED": False,
                "AUTOTHROTTLE_DEBUG": False,
            }
        )
    elif env == "testing":
        # Testing overrides
        globals().update(
            {
                "LOG_LEVEL": "WARNING",
                "DOWNLOAD_DELAY": 0,
                "ROBOTSTXT_OBEY": False,
                "HTTPCACHE_ENABLED": True,
                "MONGO_DATABASE": "fandom_scraper_test",
            }
        )
    else:
        # Development overrides (default)
        globals().update(
            {
                "LOG_LEVEL": "DEBUG",
                "DOWNLOAD_DELAY": 0.5,
                "HTTPCACHE_ENABLED": True,
                "AUTOTHROTTLE_DEBUG": True,
            }
        )


# Load environment configuration
configure_for_environment()


# Custom settings validation
def validate_settings():
    """
    Validate critical settings before starting spider.
    """
    errors = []

    # Check required directories exist
    required_dirs = [IMAGES_STORE, FILES_STORE, Path(LOG_FILE).parent]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")

    # Validate MongoDB URI format
    if not MONGO_URI.startswith(("mongodb://", "mongodb+srv://")):
        errors.append(f"Invalid MongoDB URI format: {MONGO_URI}")

    # Check memory limits
    if MEMUSAGE_LIMIT_MB < MEMUSAGE_WARNING_MB:
        errors.append("Memory limit must be greater than warning threshold")

    # Validate pipeline order
    pipeline_order = sorted(ITEM_PIPELINES.values())
    if pipeline_order != list(range(100, 600, 100)):
        errors.append("Pipeline priorities should be in increments of 100")

    if errors:
        raise ValueError(f"Settings validation failed: {'; '.join(errors)}")


# Custom settings for specific spiders
SPIDER_CUSTOM_SETTINGS = {
    "onepiece": {
        "custom_settings": {
            "DOWNLOAD_DELAY": 1.5,
            "CLOSESPIDER_ITEMCOUNT": 500,
            "FEEDS": {
                "storage/exports/onepiece_characters_%(time)s.json": {
                    "format": "json",
                    "encoding": "utf8",
                    "fields": ["name", "epithet", "bounty", "devil_fruit", "crew"],
                }
            },
        }
    },
    "naruto": {
        "custom_settings": {
            "DOWNLOAD_DELAY": 1.0,
            "CLOSESPIDER_ITEMCOUNT": 300,
            "FEEDS": {
                "storage/exports/naruto_characters_%(time)s.json": {
                    "format": "json",
                    "encoding": "utf8",
                    "fields": ["name", "village", "rank", "jutsu", "team"],
                }
            },
        }
    },
}

# Selector configuration paths
SELECTOR_CONFIG_PATHS = {
    "generic_fandom": "config/selector_configs/generic_fandom.json",
    "onepiece": "config/selector_configs/onepiece.json",
    "naruto": "config/selector_configs/naruto.json",
    "dragonball": "config/selector_configs/dragonball.json",
}

# Image classification settings
IMAGE_CLASSIFICATION_SETTINGS = {
    "enable_ai_classification": False,  # Future feature
    "manual_classification_rules": {
        "portrait": ["portrait", "headshot", "face", "profile"],
        "full_body": ["full", "body", "standing", "whole"],
        "action": ["fight", "battle", "action", "combat"],
        "group": ["group", "team", "crew", "together"],
        "thumbnail": ["thumb", "small", "mini", "icon"],
    },
    "preferred_image_types": ["portrait", "full_body", "action"],
    "max_images_per_type": 5,
}

# Data export templates
EXPORT_TEMPLATES = {
    "character_summary": [
        "name",
        "anime_name",
        "description",
        "source_url",
        "quality_score",
        "extraction_date",
    ],
    "character_detailed": [
        "name",
        "anime_name",
        "description",
        "images",
        "relationships",
        "abilities",
        "appearances",
        "quality_score",
        "quality_report",
        "source_url",
        "extraction_date",
    ],
    "onepiece_specific": [
        "name",
        "epithet",
        "bounty",
        "devil_fruit",
        "crew",
        "origin",
        "fighting_abilities",
        "haki",
        "first_appearance",
    ],
}

# Middleware configuration
MIDDLEWARE_SETTINGS = {
    "user_agent_rotation": {
        "enabled": True,
        "agents_file": "config/user_agents.txt",
        "fallback_agent": USER_AGENT,
    },
    "proxy_rotation": {
        "enabled": False,
        "proxy_file": "config/proxies.txt",
        "retry_with_different_proxy": True,
    },
    "session_rotation": {
        "enabled": True,
        "rotation_interval": 100,  # requests
        "clear_cookies": True,
    },
}
