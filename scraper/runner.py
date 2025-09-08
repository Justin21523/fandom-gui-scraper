# scraper/runner.py
"""
Scrapy Spider Runner

This module provides a high-level interface for running Fandom spiders
with proper configuration and monitoring capabilities.
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from multiprocessing import Process, Queue
from datetime import datetime

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging

from scraper.fandom_spider import FandomSpider
from scraper.onepiece_spider import OnePieceSpider
from scraper.settings import get_settings_for_environment, validate_settings
from utils.logger import get_logger
from models.storage import DatabaseManager


class SpiderRunner:
    """
    High-level spider runner with monitoring and control capabilities.

    This class provides:
    - Easy spider execution with custom parameters
    - Progress monitoring and callbacks
    - Error handling and recovery
    - Statistics collection and reporting
    - Graceful shutdown handling
    """

    def __init__(self, environment: str = "development"):
        """
        Initialize spider runner.

        Args:
            environment: Environment name ('development', 'production', 'testing')
        """
        self.environment = environment
        self.logger = get_logger(self.__class__.__name__)

        # Get and validate settings
        self.settings = get_settings_for_environment(environment)
        validate_settings()

        # Initialize components
        self.crawler_process = None
        self.current_spider = None
        self.is_running = False
        self.start_time = None
        self.stats = {}

        # Callbacks
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info(f"Spider runner initialized for {environment} environment")

    def run_spider(
        self,
        spider_name: str,
        anime_name: str = None,  # type: ignore
        max_characters: int = None,  # type: ignore
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run a specific spider with given parameters.

        Args:
            spider_name: Name of spider to run ('fandom', 'onepiece', etc.)
            anime_name: Target anime name
            max_characters: Maximum characters to scrape
            **kwargs: Additional spider parameters

        Returns:
            Execution results and statistics
        """
        self.logger.info(f"Starting spider: {spider_name}")
        self.logger.info(f"Target anime: {anime_name}")
        self.logger.info(f"Max characters: {max_characters}")

        try:
            # Setup spider parameters
            spider_kwargs = {
                "anime_name": anime_name,
                "max_characters": max_characters,
                "progress_callback": self._progress_update,
                "data_callback": self._data_received,
                **kwargs,
            }

            # Get spider class
            spider_class = self._get_spider_class(spider_name)
            if not spider_class:
                raise ValueError(f"Unknown spider: {spider_name}")

            # Configure logging
            configure_logging(self.settings)

            # Create crawler process
            self.crawler_process = CrawlerProcess(self.settings)

            # Add spider to crawler
            self.crawler_process.crawl(spider_class, **spider_kwargs)

            # Start crawling
            self.is_running = True
            self.start_time = datetime.now()
            self.current_spider = spider_name

            self.logger.info("Starting crawler process...")
            self.crawler_process.start()  # This blocks until completion

            # Process completed
            self.is_running = False
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()

            # Collect final statistics
            final_stats = self._collect_final_stats(duration)

            self.logger.info(f"Spider completed successfully in {duration:.2f} seconds")

            # Call completion callback
            if self.completion_callback:
                self.completion_callback(final_stats)

            return final_stats

        except Exception as e:
            self.is_running = False
            self.logger.error(f"Spider execution failed: {e}")

            # Call error callback
            if self.error_callback:
                self.error_callback(str(e))

            raise

    def run_spider_async(
        self,
        spider_name: str,
        anime_name: str = None,  # type: ignore
        max_characters: int = None,  # type: ignore
        **kwargs,
    ) -> Process:
        """
        Run spider in separate process (non-blocking).

        Args:
            spider_name: Name of spider to run
            anime_name: Target anime name
            max_characters: Maximum characters to scrape
            **kwargs: Additional spider parameters

        Returns:
            Process object for the running spider
        """
        # Create process for spider execution
        result_queue = Queue()

        def spider_worker():
            try:
                result = self.run_spider(
                    spider_name, anime_name, max_characters, **kwargs
                )
                result_queue.put(("success", result))
            except Exception as e:
                result_queue.put(("error", str(e)))

        process = Process(target=spider_worker)
        process.start()

        self.logger.info(f"Spider {spider_name} started in process {process.pid}")
        return process

    def stop_spider(self, force: bool = False) -> None:
        """
        Stop currently running spider.

        Args:
            force: Whether to force stop immediately
        """
        if not self.is_running:
            self.logger.warning("No spider is currently running")
            return

        self.logger.info("Stopping spider...")

        try:
            if force:
                # Force stop by stopping reactor
                if reactor and hasattr(reactor, "running") and reactor.running:  # type: ignore
                    reactor.stop()  # type: ignore
            else:
                # Graceful stop
                if self.crawler_process:
                    # Send stop signal to crawler
                    self.crawler_process.stop()

            self.is_running = False
            self.logger.info("Spider stopped successfully")

        except Exception as e:
            self.logger.error(f"Error stopping spider: {e}")

    def get_spider_status(self) -> Dict[str, Any]:
        """
        Get current spider execution status.

        Returns:
            Status information dictionary
        """
        status = {
            "is_running": self.is_running,
            "current_spider": self.current_spider,
            "environment": self.environment,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration": None,
            "stats": self.stats.copy(),
        }

        if self.is_running and self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            status["duration"] = duration

        return status

    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """
        Set callback function for progress updates.

        Args:
            callback: Function that accepts (message, progress_percentage)
        """
        self.progress_callback = callback

    def set_completion_callback(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Set callback function for completion notification.

        Args:
            callback: Function that accepts final statistics
        """
        self.completion_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback function for error notification.

        Args:
            callback: Function that accepts error message
        """
        self.error_callback = callback

    def get_available_spiders(self) -> List[str]:
        """
        Get list of available spider names.

        Returns:
            List of spider names
        """
        return ["fandom", "onepiece", "naruto", "dragonball"]

    def validate_spider_config(self, spider_name: str, **kwargs) -> bool:
        """
        Validate spider configuration before running.

        Args:
            spider_name: Name of spider to validate
            **kwargs: Spider parameters

        Returns:
            True if configuration is valid
        """
        try:
            # Check if spider exists
            spider_class = self._get_spider_class(spider_name)
            if not spider_class:
                return False

            # Validate required parameters
            if spider_name in ["fandom", "onepiece"] and not kwargs.get("anime_name"):
                return False

            # Validate database connection
            db_manager = DatabaseManager(
                self.settings["MONGO_URI"], self.settings["MONGO_DATABASE"]
            )
            db_manager.connect()
            db_manager.disconnect()

            return True

        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def _get_spider_class(self, spider_name: str):
        """
        Get spider class by name.

        Args:
            spider_name: Name of spider

        Returns:
            Spider class or None
        """
        spider_classes = {
            "fandom": FandomSpider,
            "onepiece": OnePieceSpider,
            # Add more spiders here as they are implemented
        }

        return spider_classes.get(spider_name)

    def _progress_update(self, message: str, progress: float) -> None:
        """
        Handle progress updates from spider.

        Args:
            message: Progress message
            progress: Progress percentage (0-100)
        """
        self.stats["last_progress"] = progress
        self.stats["last_message"] = message
        self.stats["last_update"] = datetime.now().isoformat()

        self.logger.debug(f"Progress: {progress:.1f}% - {message}")

        # Call external progress callback
        if self.progress_callback:
            self.progress_callback(message, progress)

    def _data_received(self, data: Dict[str, Any]) -> None:
        """
        Handle data received from spider.

        Args:
            data: Character data received
        """
        self.stats["items_scraped"] = self.stats.get("items_scraped", 0) + 1
        self.stats["last_character"] = data.get("name", "Unknown")

        self.logger.debug(f"Data received: {data.get('name', 'Unknown')}")

    def _collect_final_stats(self, duration: float) -> Dict[str, Any]:
        """
        Collect final execution statistics.

        Args:
            duration: Execution duration in seconds

        Returns:
            Final statistics dictionary
        """
        stats = {
            "spider_name": self.current_spider,
            "duration_seconds": duration,
            "start_time": self.start_time.isoformat(),  # type: ignore
            "end_time": datetime.now().isoformat(),
            "items_scraped": self.stats.get("items_scraped", 0),
            "environment": self.environment,
            "success": True,
        }

        # Add spider-specific stats if available
        if hasattr(self.crawler_process, "crawlers"):
            for crawler in self.crawler_process.crawlers:  # type: ignore
                if hasattr(crawler, "stats"):
                    stats["crawler_stats"] = dict(crawler.stats.get_stats())

        return stats

    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle system signals for graceful shutdown.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_names = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}

        signal_name = signal_names.get(signum, str(signum))  # type: ignore
        self.logger.info(f"Received {signal_name} signal, stopping spider...")

        self.stop_spider(force=False)


class BatchSpiderRunner:
    """
    Runner for executing multiple spiders in sequence or parallel.
    """

    def __init__(self, environment: str = "development"):
        """
        Initialize batch runner.

        Args:
            environment: Environment name
        """
        self.environment = environment
        self.logger = get_logger(self.__class__.__name__)
        self.runners = []
        self.results = []

    def add_spider_job(
        self,
        spider_name: str,
        anime_name: str = None,  # type: ignore
        max_characters: int = None,  # type: ignore
        **kwargs,
    ) -> None:
        """
        Add spider job to batch.

        Args:
            spider_name: Name of spider
            anime_name: Target anime name
            max_characters: Maximum characters to scrape
            **kwargs: Additional parameters
        """
        job = {
            "spider_name": spider_name,
            "anime_name": anime_name,
            "max_characters": max_characters,
            "kwargs": kwargs,
        }

        self.runners.append(job)
        self.logger.info(f"Added job: {spider_name} for {anime_name}")

    def run_sequential(self) -> List[Dict[str, Any]]:
        """
        Run all spider jobs sequentially.

        Returns:
            List of execution results
        """
        self.logger.info(f"Starting sequential execution of {len(self.runners)} jobs")

        results = []

        for i, job in enumerate(self.runners):
            self.logger.info(
                f"Starting job {i+1}/{len(self.runners)}: {job['spider_name']}"
            )

            try:
                runner = SpiderRunner(self.environment)
                result = runner.run_spider(
                    job["spider_name"],
                    job["anime_name"],
                    job["max_characters"],
                    **job["kwargs"],
                )
                result["job_index"] = i
                results.append(result)

            except Exception as e:
                self.logger.error(f"Job {i+1} failed: {e}")
                results.append(
                    {
                        "job_index": i,
                        "success": False,
                        "error": str(e),
                        "spider_name": job["spider_name"],
                    }
                )

        self.results = results
        self.logger.info(
            f"Sequential execution completed: {len(results)} jobs processed"
        )
        return results

    def run_parallel(self, max_workers: int = 3) -> List[Dict[str, Any]]:
        """
        Run spider jobs in parallel (limited workers).

        Args:
            max_workers: Maximum number of parallel workers

        Returns:
            List of execution results
        """
        self.logger.info(f"Starting parallel execution with {max_workers} workers")

        # Implementation would use multiprocessing or asyncio
        # For now, fall back to sequential execution
        self.logger.warning("Parallel execution not yet implemented, using sequential")
        return self.run_sequential()

    def get_batch_summary(self) -> Dict[str, Any]:
        """
        Get summary of batch execution results.

        Returns:
            Batch execution summary
        """
        if not self.results:
            return {"status": "not_executed"}

        successful = sum(1 for r in self.results if r.get("success", False))
        failed = len(self.results) - successful
        total_items = sum(r.get("items_scraped", 0) for r in self.results)
        total_duration = sum(r.get("duration_seconds", 0) for r in self.results)

        return {
            "total_jobs": len(self.results),
            "successful_jobs": successful,
            "failed_jobs": failed,
            "total_items_scraped": total_items,
            "total_duration_seconds": total_duration,
            "success_rate": (successful / len(self.results)) * 100,
            "average_items_per_job": (
                total_items / len(self.results) if self.results else 0
            ),
        }


# Convenience functions for easy usage
def run_onepiece_scraper(
    max_characters: int = 100, environment: str = "development"
) -> Dict[str, Any]:
    """
    Convenience function to run One Piece scraper.

    Args:
        max_characters: Maximum characters to scrape
        environment: Environment name

    Returns:
        Execution results
    """
    runner = SpiderRunner(environment)
    return runner.run_spider("onepiece", max_characters=max_characters)


def run_generic_scraper(
    anime_name: str, max_characters: int = 100, environment: str = "development"
) -> Dict[str, Any]:
    """
    Convenience function to run generic Fandom scraper.

    Args:
        anime_name: Target anime name
        max_characters: Maximum characters to scrape
        environment: Environment name

    Returns:
        Execution results
    """
    runner = SpiderRunner(environment)
    return runner.run_spider(
        "fandom", anime_name=anime_name, max_characters=max_characters
    )


# Example usage
if __name__ == "__main__":
    # Example: Run One Piece scraper
    try:
        results = run_onepiece_scraper(max_characters=50)
        print(f"Scraping completed: {results['items_scraped']} characters collected")
    except Exception as e:
        print(f"Scraping failed: {e}")
