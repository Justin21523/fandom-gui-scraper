# scraper/runner.py
"""
Scrapy spider runner and management utilities.

This module provides utilities to run spiders programmatically,
manage spider processes, and handle concurrent spider execution.
"""

import os
import sys
import signal
import logging
import threading
from typing import Dict, List, Optional, Callable, Any
from multiprocessing import Process, Queue, Event
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from twisted.internet.defer import inlineCallbacks

logger = logging.getLogger(__name__)


class SpiderRunner:
    """
    Run Scrapy spiders programmatically with configuration options.

    This class provides a high-level interface for running spiders
    with custom settings and monitoring capabilities.
    """

    def __init__(
        self, settings: Optional[Dict[str, Any]] = None, log_level: str = "INFO"
    ):
        """
        Initialize spider runner.

        Args:
            settings: Custom Scrapy settings
            log_level: Logging level
        """
        self.custom_settings = settings or {}
        self.log_level = log_level
        self.runner = None
        self.process = None
        self.is_running = False

        # Setup logging
        configure_logging({"LOG_LEVEL": log_level})

    def get_spider_settings(self) -> Dict[str, Any]:
        """
        Get combined Scrapy settings.

        Returns:
            Dictionary of settings
        """
        # Start with project settings
        settings = get_project_settings()

        # Apply custom settings
        for key, value in self.custom_settings.items():
            settings.set(key, value)

        # Ensure log level is set
        settings.set("LOG_LEVEL", self.log_level)

        return settings  # type: ignore

    def run_spider(
        self,
        spider_name: str,
        spider_kwargs: Optional[Dict[str, Any]] = None,
        blocking: bool = True,
    ) -> Optional[defer.Deferred]:
        """
        Run a single spider.

        Args:
            spider_name: Name of the spider to run
            spider_kwargs: Additional arguments for the spider
            blocking: Whether to block until completion

        Returns:
            Deferred object if non-blocking, None if blocking
        """
        spider_kwargs = spider_kwargs or {}

        if blocking:
            return self._run_spider_blocking(spider_name, spider_kwargs)
        else:
            return self._run_spider_non_blocking(spider_name, spider_kwargs)

    def _run_spider_blocking(self, spider_name: str, spider_kwargs: Dict[str, Any]):
        """Run spider in blocking mode using CrawlerProcess."""
        try:
            settings = self.get_spider_settings()
            self.process = CrawlerProcess(settings)

            self.is_running = True
            logger.info(f"Starting spider: {spider_name}")

            self.process.crawl(spider_name, **spider_kwargs)
            self.process.start()  # This blocks until completion

        except Exception as e:
            logger.error(f"Error running spider {spider_name}: {e}")
            raise
        finally:
            self.is_running = False
            logger.info(f"Spider {spider_name} finished")

    @inlineCallbacks
    def _run_spider_non_blocking(self, spider_name: str, spider_kwargs: Dict[str, Any]):
        """Run spider in non-blocking mode using CrawlerRunner."""
        try:
            settings = self.get_spider_settings()

            if not self.runner:
                self.runner = CrawlerRunner(settings)

            self.is_running = True
            logger.info(f"Starting spider: {spider_name}")

            deferred = self.runner.crawl(spider_name, **spider_kwargs)
            yield deferred

            logger.info(f"Spider {spider_name} finished")

        except Exception as e:
            logger.error(f"Error running spider {spider_name}: {e}")
            raise
        finally:
            self.is_running = False

    def stop_spider(self):
        """Stop the currently running spider."""
        if self.is_running:
            logger.info("Stopping spider...")

            if self.process:
                self.process.stop()

            if self.runner:
                self.runner.stop()

            self.is_running = False


class MultiSpiderRunner:
    """
    Run multiple spiders concurrently or sequentially.

    This class manages the execution of multiple spiders
    with different scheduling strategies.
    """

    def __init__(
        self, settings: Optional[Dict[str, Any]] = None, log_level: str = "INFO"
    ):
        """
        Initialize multi-spider runner.

        Args:
            settings: Custom Scrapy settings
            log_level: Logging level
        """
        self.settings = settings or {}
        self.log_level = log_level
        self.runners = {}
        self.results = {}

    def run_spiders_sequential(
        self, spider_configs: List[Dict[str, Any]], stop_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Run spiders sequentially one after another.

        Args:
            spider_configs: List of spider configuration dictionaries
            stop_on_error: Whether to stop if a spider fails

        Returns:
            Dictionary with results for each spider
        """
        results = {}

        for config in spider_configs:
            spider_name = config["name"]
            spider_kwargs = config.get("kwargs", {})
            spider_settings = config.get("settings", {})

            try:
                logger.info(f"Running spider {spider_name} sequentially")

                # Merge settings
                combined_settings = self.settings.copy()
                combined_settings.update(spider_settings)

                # Create runner for this spider
                runner = SpiderRunner(combined_settings, self.log_level)

                # Run spider
                runner.run_spider(spider_name, spider_kwargs, blocking=True)

                results[spider_name] = {"status": "completed", "error": None}
                logger.info(f"Spider {spider_name} completed successfully")

            except Exception as e:
                error_msg = f"Spider {spider_name} failed: {e}"
                logger.error(error_msg)

                results[spider_name] = {"status": "failed", "error": str(e)}

                if stop_on_error:
                    logger.error("Stopping execution due to spider failure")
                    break

        return results

    def run_spiders_parallel(
        self, spider_configs: List[Dict[str, Any]], max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Run spiders in parallel using multiprocessing.

        Args:
            spider_configs: List of spider configuration dictionaries
            max_workers: Maximum number of concurrent spiders

        Returns:
            Dictionary with results for each spider
        """
        from concurrent.futures import ProcessPoolExecutor, as_completed

        results = {}

        def run_spider_process(config):
            """Function to run spider in separate process."""
            spider_name = config["name"]
            spider_kwargs = config.get("kwargs", {})
            spider_settings = config.get("settings", {})

            try:
                # Merge settings
                combined_settings = self.settings.copy()
                combined_settings.update(spider_settings)

                # Create runner
                runner = SpiderRunner(combined_settings, self.log_level)

                # Run spider
                runner.run_spider(spider_name, spider_kwargs, blocking=True)

                return {"name": spider_name, "status": "completed", "error": None}

            except Exception as e:
                return {"name": spider_name, "status": "failed", "error": str(e)}

        # Execute spiders in parallel
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all spider tasks
            future_to_spider = {
                executor.submit(run_spider_process, config): config["name"]
                for config in spider_configs
            }

            # Collect results as they complete
            for future in as_completed(future_to_spider):
                spider_name = future_to_spider[future]
                try:
                    result = future.result()
                    results[result["name"]] = {
                        "status": result["status"],
                        "error": result["error"],
                    }
                    logger.info(
                        f"Spider {spider_name} completed with status: {result['status']}"
                    )

                except Exception as e:
                    results[spider_name] = {"status": "failed", "error": str(e)}
                    logger.error(f"Spider {spider_name} failed: {e}")

        return results

    @inlineCallbacks
    def run_spiders_async(self, spider_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run spiders asynchronously using Twisted reactor.

        Args:
            spider_configs: List of spider configuration dictionaries

        Returns:
            Dictionary with results for each spider
        """
        results = {}

        # Create runners for all spiders
        runners = []
        for config in spider_configs:
            spider_name = config["name"]
            spider_kwargs = config.get("kwargs", {})
            spider_settings = config.get("settings", {})

            # Merge settings
            combined_settings = self.settings.copy()
            combined_settings.update(spider_settings)

            runner = SpiderRunner(combined_settings, self.log_level)
            runners.append((runner, spider_name, spider_kwargs))

        # Run all spiders concurrently
        deferreds = []
        for runner, spider_name, spider_kwargs in runners:
            deferred = runner._run_spider_non_blocking(spider_name, spider_kwargs)
            deferreds.append(deferred)

        # Wait for all to complete
        try:
            yield defer.DeferredList(deferreds, consumeErrors=True)

            # Collect results
            for i, (runner, spider_name, _) in enumerate(runners):
                if deferreds[i].called and not hasattr(deferreds[i], "exception"):
                    results[spider_name] = {"status": "completed", "error": None}
                else:
                    error = getattr(deferreds[i], "exception", "Unknown error")
                    results[spider_name] = {"status": "failed", "error": str(error)}

        except Exception as e:
            logger.error(f"Error in async spider execution: {e}")
            for runner, spider_name, _ in runners:
                if spider_name not in results:
                    results[spider_name] = {"status": "failed", "error": str(e)}

        defer.returnValue(results)


class SpiderManager:
    """
    High-level spider management interface.

    This class provides a convenient interface for managing
    and running spiders with different configurations.
    """

    def __init__(self, default_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize spider manager.

        Args:
            default_settings: Default settings for all spiders
        """
        self.default_settings = default_settings or {}
        self.spider_configs = {}
        self.progress_callbacks = []

    def register_spider(
        self,
        name: str,
        spider_class: str,
        settings: Optional[Dict[str, Any]] = None,
        default_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Register a spider configuration.

        Args:
            name: Spider identifier
            spider_class: Spider class name
            settings: Spider-specific settings
            default_kwargs: Default keyword arguments
        """
        self.spider_configs[name] = {
            "class": spider_class,
            "settings": settings or {},
            "default_kwargs": default_kwargs or {},
        }

        logger.info(f"Registered spider: {name}")

    def run_spider(
        self,
        name: str,
        kwargs: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        blocking: bool = True,
    ) -> Any:
        """
        Run a registered spider.

        Args:
            name: Spider identifier
            kwargs: Additional keyword arguments
            settings: Additional settings
            blocking: Whether to block until completion

        Returns:
            Result of spider execution
        """
        if name not in self.spider_configs:
            raise ValueError(f"Spider '{name}' not registered")

        config = self.spider_configs[name]

        # Merge settings
        combined_settings = self.default_settings.copy()
        combined_settings.update(config["settings"])
        if settings:
            combined_settings.update(settings)

        # Merge kwargs
        combined_kwargs = config["default_kwargs"].copy()
        if kwargs:
            combined_kwargs.update(kwargs)

        # Create and run spider
        runner = SpiderRunner(combined_settings)
        return runner.run_spider(config["class"], combined_kwargs, blocking)

    def run_multiple_spiders(
        self, spider_names: List[str], mode: str = "sequential", **kwargs
    ) -> Dict[str, Any]:  # type: ignore
        """
        Run multiple registered spiders.

        Args:
            spider_names: List of spider identifiers
            mode: Execution mode ('sequential', 'parallel', 'async')
            **kwargs: Additional arguments for the execution mode

        Returns:
            Dictionary with results for each spider
        """
        # Build spider configurations
        spider_configs = []
        for name in spider_names:
            if name not in self.spider_configs:
                logger.warning(f"Spider '{name}' not registered, skipping")
                continue

            config = self.spider_configs[name]
            spider_config = {
                "name": config["class"],
                "kwargs": config["default_kwargs"],
                "settings": {**self.default_settings, **config["settings"]},
            }
            spider_configs.append(spider_config)

        # Create multi-spider runner
        multi_runner = MultiSpiderRunner(self.default_settings)

        # Run based on mode
        if mode == "sequential":
            return multi_runner.run_spiders_sequential(spider_configs, **kwargs)
        elif mode == "parallel":
            return multi_runner.run_spiders_parallel(spider_configs, **kwargs)
        elif mode == "async":
            # For async mode, we need to run in reactor
            def run_async():
                return multi_runner.run_spiders_async(spider_configs)

            if not reactor.running:
                reactor.callWhenRunning(run_async)
                reactor.run()
            else:
                return run_async()
        else:
            raise ValueError(f"Invalid execution mode: {mode}")

    def add_progress_callback(self, callback: Callable[[str, str, Dict], None]):
        """
        Add progress callback function.

        Args:
            callback: Function called with (spider_name, status, data)
        """
        self.progress_callbacks.append(callback)

    def get_spider_list(self) -> List[str]:
        """Get list of registered spider names."""
        return list(self.spider_configs.keys())

    def get_spider_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered spider."""
        return self.spider_configs.get(name)


# Utility functions for common spider management tasks


def create_spider_runner(
    settings_override: Optional[Dict[str, Any]] = None,
) -> SpiderRunner:
    """
    Create a spider runner with common settings.

    Args:
        settings_override: Settings to override defaults

    Returns:
        Configured SpiderRunner instance
    """
    default_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "AUTOTHROTTLE_DEBUG": False,
    }

    if settings_override:
        default_settings.update(settings_override)

    return SpiderRunner(default_settings)


def run_fandom_spider(
    wiki_name: str,
    character_list: Optional[List[str]] = None,
    max_pages: Optional[int] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to run a Fandom spider.

    Args:
        wiki_name: Name of the Fandom wiki
        character_list: List of characters to scrape
        max_pages: Maximum number of pages to scrape
        output_file: Output file path

    Returns:
        Execution results
    """
    settings = {}

    if output_file:
        settings["FEEDS"] = {
            output_file: {
                "format": "json",
                "encoding": "utf8",
                "store_empty": False,
                "indent": 2,
            }
        }

    kwargs = {"wiki_name": wiki_name}

    if character_list:
        kwargs["character_list"] = character_list

    if max_pages:
        kwargs["max_pages"] = max_pages

    runner = create_spider_runner(settings)

    try:
        result = runner.run_spider("fandom_spider", kwargs, blocking=True)
        return {"status": "completed", "error": None, "result": result}
    except Exception as e:
        return {"status": "failed", "error": str(e), "result": None}


def stop_all_spiders():
    """Emergency stop function to terminate all running spiders."""
    try:
        if reactor.running:
            reactor.stop()

        # Send SIGTERM to current process
        os.kill(os.getpid(), signal.SIGTERM)

    except Exception as e:
        logger.error(f"Error stopping spiders: {e}")


# Signal handlers for graceful shutdown
def setup_signal_handlers():
    """Setup signal handlers for graceful spider shutdown."""

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down spiders...")
        stop_all_spiders()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
