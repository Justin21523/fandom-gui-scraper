# examples/spider_usage_examples.py
"""
Fandom Scraper Usage Examples

This file demonstrates various ways to use the Fandom scraper system
for different scenarios and use cases.
"""

import sys
import asyncio
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scraper.runner import SpiderRunner, BatchSpiderRunner
from scraper.runner import run_onepiece_scraper, run_generic_scraper
from utils.logger import get_logger

logger = get_logger(__name__)


def example_1_basic_onepiece_scraping():
    """
    Example 1: Basic One Piece character scraping
    """
    print("=" * 60)
    print("Example 1: Basic One Piece Character Scraping")
    print("=" * 60)

    try:
        # Simple way to scrape One Piece characters
        results = run_onepiece_scraper(
            max_characters=10, environment="development"  # Limit for testing
        )

        print(f"✅ Scraping completed successfully!")
        print(f"📊 Characters scraped: {results['items_scraped']}")
        print(f"⏱️  Duration: {results['duration_seconds']:.2f} seconds")
        print(f"📅 Completed at: {results['end_time']}")

    except Exception as e:
        print(f"❌ Scraping failed: {e}")


def example_2_custom_anime_scraping():
    """
    Example 2: Scraping a different anime using generic spider
    """
    print("\n" + "=" * 60)
    print("Example 2: Custom Anime Scraping (Naruto)")
    print("=" * 60)

    try:
        # Scrape Naruto characters using generic spider
        results = run_generic_scraper(
            anime_name="Naruto", max_characters=15, environment="development"
        )

        print(f"✅ Naruto scraping completed!")
        print(f"📊 Characters scraped: {results['items_scraped']}")
        print(f"⏱️  Duration: {results['duration_seconds']:.2f} seconds")

    except Exception as e:
        print(f"❌ Naruto scraping failed: {e}")


def example_3_advanced_spider_runner():
    """
    Example 3: Advanced spider runner with callbacks
    """
    print("\n" + "=" * 60)
    print("Example 3: Advanced Spider Runner with Callbacks")
    print("=" * 60)

    # Progress tracking
    def progress_callback(message: str, progress: float):
        print(f"🔄 Progress: {progress:.1f}% - {message}")

    # Completion callback
    def completion_callback(stats: dict):
        print(f"🎉 Scraping completed!")
        print(f"📈 Final statistics: {stats}")

    # Error callback
    def error_callback(error_message: str):
        print(f"💥 Error occurred: {error_message}")

    try:
        # Create runner with callbacks
        runner = SpiderRunner(environment="development")
        runner.set_progress_callback(progress_callback)
        runner.set_completion_callback(completion_callback)
        runner.set_error_callback(error_callback)

        # Run with custom settings
        results = runner.run_spider(
            spider_name="onepiece",
            max_characters=5,
            custom_delay=2.0,  # Extra polite delay
            save_images=True,
        )

    except Exception as e:
        print(f"❌ Advanced scraping failed: {e}")


def example_4_batch_scraping():
    """
    Example 4: Batch scraping multiple anime
    """
    print("\n" + "=" * 60)
    print("Example 4: Batch Scraping Multiple Anime")
    print("=" * 60)

    try:
        # Create batch runner
        batch_runner = BatchSpiderRunner(environment="development")

        # Add multiple scraping jobs
        batch_runner.add_spider_job(spider_name="onepiece", max_characters=8)

        batch_runner.add_spider_job(
            spider_name="fandom", anime_name="Dragon Ball", max_characters=6
        )

        batch_runner.add_spider_job(
            spider_name="fandom", anime_name="Attack on Titan", max_characters=5
        )

        print("🚀 Starting batch execution...")

        # Run all jobs sequentially
        results = batch_runner.run_sequential()

        # Get summary
        summary = batch_runner.get_batch_summary()

        print(f"📊 Batch Summary:")
        print(f"   Total jobs: {summary['total_jobs']}")
        print(f"   Successful: {summary['successful_jobs']}")
        print(f"   Failed: {summary['failed_jobs']}")
        print(f"   Success rate: {summary['success_rate']:.1f}%")
        print(f"   Total characters: {summary['total_items_scraped']}")
        print(f"   Total duration: {summary['total_duration_seconds']:.2f}s")

    except Exception as e:
        print(f"❌ Batch scraping failed: {e}")


def example_5_configuration_validation():
    """
    Example 5: Configuration validation and debugging
    """
    print("\n" + "=" * 60)
    print("Example 5: Configuration Validation")
    print("=" * 60)

    runner = SpiderRunner(environment="development")

    # Check available spiders
    available_spiders = runner.get_available_spiders()
    print(f"🕷️  Available spiders: {available_spiders}")

    # Validate configurations
    test_configs = [
        ("onepiece", {}),
        ("fandom", {"anime_name": "Naruto"}),
        ("fandom", {}),  # This should fail - missing anime_name
        ("invalid_spider", {"anime_name": "Test"}),  # This should fail - invalid spider
    ]

    for spider_name, config in test_configs:
        is_valid = runner.validate_spider_config(spider_name, **config)
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{status} - {spider_name}: {config}")


def example_6_monitoring_and_control():
    """
    Example 6: Real-time monitoring and control
    """
    print("\n" + "=" * 60)
    print("Example 6: Real-time Monitoring and Control")
    print("=" * 60)

    import threading
    import time

    runner = SpiderRunner(environment="development")

    # Status monitoring function
    def monitor_status():
        while True:
            status = runner.get_spider_status()
            if status["is_running"]:
                print(
                    f"📊 Status: {status['current_spider']} running for {status.get('duration', 0):.1f}s"
                )
                print(f"📈 Stats: {status['stats']}")
            time.sleep(5)  # Check every 5 seconds

            if not status["is_running"]:
                break

    try:
        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_status, daemon=True)
        monitor_thread.start()

        # Run spider
        results = runner.run_spider(spider_name="onepiece", max_characters=3)

        print(f"🏁 Final results: {results}")

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user, stopping spider...")
        runner.stop_spider()
    except Exception as e:
        print(f"❌ Monitoring example failed: {e}")


def example_7_error_handling_and_recovery():
    """
    Example 7: Error handling and recovery strategies
    """
    print("\n" + "=" * 60)
    print("Example 7: Error Handling and Recovery")
    print("=" * 60)

    runner = SpiderRunner(environment="development")

    # Test various error scenarios
    error_scenarios = [
        {
            "name": "Invalid anime name",
            "spider": "fandom",
            "params": {"anime_name": "NonExistentAnime123"},
        },
        {
            "name": "Database connection error",
            "spider": "onepiece",
            "params": {"mongo_uri": "invalid://connection"},
        },
        {
            "name": "Valid configuration",
            "spider": "onepiece",
            "params": {"max_characters": 2},
        },
    ]

    for scenario in error_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")

        try:
            results = runner.run_spider(scenario["spider"], **scenario["params"])
            print(f"✅ Success: {results.get('items_scraped', 0)} items scraped")

        except Exception as e:
            print(f"❌ Expected error: {str(e)[:100]}...")
            print(f"🔧 Recovery: Continuing with next scenario")


def example_8_performance_benchmarking():
    """
    Example 8: Performance benchmarking
    """
    print("\n" + "=" * 60)
    print("Example 8: Performance Benchmarking")
    print("=" * 60)

    benchmark_configs = [
        {"max_characters": 5, "environment": "development"},
        {"max_characters": 10, "environment": "development"},
        {"max_characters": 15, "environment": "development"},
    ]

    results = []

    for i, config in enumerate(benchmark_configs, 1):
        print(f"\n📊 Benchmark {i}/3: {config['max_characters']} characters")

        try:
            start_time = time.time()
            result = run_onepiece_scraper(**config)
            end_time = time.time()

            benchmark_result = {
                "max_characters": config["max_characters"],
                "items_scraped": result["items_scraped"],
                "duration": end_time - start_time,
                "items_per_second": result["items_scraped"] / (end_time - start_time),
            }

            results.append(benchmark_result)

            print(f"⏱️  Duration: {benchmark_result['duration']:.2f}s")
            print(f"📈 Rate: {benchmark_result['items_per_second']:.2f} items/sec")

        except Exception as e:
            print(f"❌ Benchmark {i} failed: {e}")

    # Summary
    if results:
        print(f"\n📊 Benchmark Summary:")
        for result in results:
            print(
                f"   {result['max_characters']} chars: "
                f"{result['duration']:.2f}s, "
                f"{result['items_per_second']:.2f} items/sec"
            )


def main():
    """
    Run all examples
    """
    print("🚀 Fandom Scraper - Usage Examples")
    print("=" * 60)

    examples = [
        example_1_basic_onepiece_scraping,
        example_2_custom_anime_scraping,
        example_3_advanced_spider_runner,
        example_4_batch_scraping,
        example_5_configuration_validation,
        example_6_monitoring_and_control,
        example_7_error_handling_and_recovery,
        example_8_performance_benchmarking,
    ]

    for i, example_func in enumerate(examples, 1):
        try:
            print(f"\n🔍 Running Example {i}...")
            example_func()
            print(f"✅ Example {i} completed successfully")
        except Exception as e:
            print(f"❌ Example {i} failed: {e}")

        # Add pause between examples
        if i < len(examples):
            print(f"\n⏳ Waiting 3 seconds before next example...")
            time.sleep(3)

    print(f"\n🎉 All examples completed!")


if __name__ == "__main__":
    main()
