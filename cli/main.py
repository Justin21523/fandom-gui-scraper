# cli/main.py
"""
Fandom Scraper Command Line Interface.

This module provides a CLI for interacting with the Fandom Scraper
application, including scraping, exporting, and managing character data.

Usage:
    python -m cli.main --help
    python -m cli.main scrape onepiece
    python -m cli.main export --format csv
    python -m cli.main stats
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List
from enum import Enum

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Initialize Typer app
app = typer.Typer(
    name="fandom-scraper",
    help="CLI tool for scraping anime character data from Fandom wikis.",
    add_completion=False,
)

console = Console()
logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class AnimeType(str, Enum):
    """Supported anime types for scraping."""
    ONEPIECE = "onepiece"
    NARUTO = "naruto"
    DRAGONBALL = "dragonball"
    CUSTOM = "custom"


def get_db_manager():
    """Get database manager instance."""
    from models.storage import DatabaseManager
    from utils.config_manager import ConfigManager

    config = ConfigManager()
    config.load_config()

    db = DatabaseManager(
        connection_string=config.database.get_connection_string(),
        database_name=config.database.name or "fandom_scraper",
    )
    return db


@app.command()
def scrape(
    anime: AnimeType = typer.Argument(
        ...,
        help="Anime to scrape (onepiece, naruto, dragonball, or custom)",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url", "-u",
        help="Custom Fandom wiki URL (required for 'custom' anime type)",
    ),
    limit: int = typer.Option(
        0,
        "--limit", "-l",
        help="Maximum number of characters to scrape (0 for unlimited)",
    ),
    delay: float = typer.Option(
        1.0,
        "--delay", "-d",
        help="Delay between requests in seconds",
    ),
):
    """
    Scrape character data from a Fandom wiki.

    Example:
        fandom-scraper scrape onepiece --limit 100
        fandom-scraper scrape custom --url https://naruto.fandom.com
    """
    if anime == AnimeType.CUSTOM and not url:
        console.print("[red]Error:[/red] --url is required for custom anime type")
        raise typer.Exit(1)

    console.print(Panel(f"[bold blue]Starting scrape for {anime.value}[/bold blue]"))

    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings

        # Get spider class based on anime type
        if anime == AnimeType.ONEPIECE:
            from scraper.onepiece_spider import OnePieceSpider
            spider_class = OnePieceSpider
        else:
            from scraper.fandom_spider import FandomSpider
            spider_class = FandomSpider

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing scraper...", total=None)

            settings = get_project_settings()
            settings.set("DOWNLOAD_DELAY", delay)

            if limit > 0:
                settings.set("CLOSESPIDER_ITEMCOUNT", limit)

            process = CrawlerProcess(settings)
            progress.update(task, description="Running spider...")

            if anime == AnimeType.CUSTOM:
                process.crawl(spider_class, start_urls=[url])
            else:
                process.crawl(spider_class)

            process.start()

        console.print("[green]✓[/green] Scraping completed successfully!")

    except ImportError as e:
        console.print(f"[red]Error:[/red] Failed to import scraper module: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def export(
    format: ExportFormat = typer.Option(
        ExportFormat.CSV,
        "--format", "-f",
        help="Export format (csv, json, excel)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file path",
    ),
    anime: Optional[str] = typer.Option(
        None,
        "--anime", "-a",
        help="Filter by anime name",
    ),
    min_quality: float = typer.Option(
        0.0,
        "--min-quality", "-q",
        help="Minimum quality score (0.0 - 1.0)",
    ),
):
    """
    Export character data to file.

    Example:
        fandom-scraper export --format csv --output characters.csv
        fandom-scraper export --format json --anime "One Piece"
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Connecting to database...", total=None)

        try:
            db = get_db_manager()
            db.connect()
            collection = db.get_collection("characters")

            # Build query filter
            query_filter = {}
            if anime:
                query_filter["anime_name"] = anime
            if min_quality > 0:
                query_filter["quality_score"] = {"$gte": min_quality}

            progress.update(task, description="Fetching characters...")
            characters = list(collection.find(query_filter))

            if not characters:
                console.print("[yellow]No characters found matching criteria[/yellow]")
                raise typer.Exit(0)

            progress.update(task, description=f"Exporting {len(characters)} characters...")

            # Generate output path if not specified
            if output is None:
                output = Path(f"characters_export.{format.value}")

            # Export based on format
            if format == ExportFormat.CSV:
                _export_csv(characters, output)
            elif format == ExportFormat.JSON:
                _export_json(characters, output)
            elif format == ExportFormat.EXCEL:
                _export_excel(characters, output)

            console.print(f"[green]✓[/green] Exported {len(characters)} characters to {output}")

        except typer.Exit:
            raise
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)


def _export_csv(characters: List[dict], output: Path):
    """Export characters to CSV."""
    import csv

    fieldnames = ["name", "anime_name", "description", "status", "quality_score", "source_url"]

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for char in characters:
            writer.writerow(char)


def _export_json(characters: List[dict], output: Path):
    """Export characters to JSON."""
    import json
    from datetime import datetime

    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    # Remove MongoDB _id field
    for char in characters:
        if "_id" in char:
            del char["_id"]

    with open(output, "w", encoding="utf-8") as f:
        json.dump(characters, f, indent=2, default=json_serializer, ensure_ascii=False)


def _export_excel(characters: List[dict], output: Path):
    """Export characters to Excel."""
    try:
        import pandas as pd

        # Flatten nested data for Excel
        flat_data = []
        for char in characters:
            flat_char = {
                "name": char.get("name"),
                "anime_name": char.get("anime_name"),
                "description": char.get("description", "")[:500],  # Truncate long descriptions
                "status": char.get("status"),
                "quality_score": char.get("quality_score"),
                "source_url": char.get("source_url"),
                "image_count": len(char.get("images", [])),
                "relationship_count": len(char.get("relationships", [])),
            }
            flat_data.append(flat_char)

        df = pd.DataFrame(flat_data)
        df.to_excel(output, index=False, engine="openpyxl")
    except ImportError:
        console.print("[red]Error:[/red] pandas and openpyxl required for Excel export")
        raise typer.Exit(1)


@app.command()
def stats():
    """
    Display character database statistics.
    """
    try:
        db = get_db_manager()
        db.connect()
        collection = db.get_collection("characters")

        # Get statistics
        total = collection.count_documents({})

        # Characters by anime
        pipeline = [
            {"$group": {"_id": "$anime_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        anime_stats = list(collection.aggregate(pipeline))

        # Quality stats
        quality_pipeline = [
            {"$group": {
                "_id": None,
                "avg_quality": {"$avg": "$quality_score"},
                "max_quality": {"$max": "$quality_score"},
                "min_quality": {"$min": "$quality_score"},
            }}
        ]
        quality_stats = list(collection.aggregate(quality_pipeline))

        # Display results
        console.print(Panel("[bold]Database Statistics[/bold]", expand=False))
        console.print(f"\n[bold]Total Characters:[/bold] {total}\n")

        # Anime table
        if anime_stats:
            table = Table(title="Characters by Anime")
            table.add_column("Anime", style="cyan")
            table.add_column("Count", justify="right", style="green")

            for item in anime_stats:
                if item["_id"]:
                    table.add_row(item["_id"], str(item["count"]))

            console.print(table)

        # Quality stats
        if quality_stats and quality_stats[0].get("avg_quality") is not None:
            q = quality_stats[0]
            console.print("\n[bold]Quality Scores:[/bold]")
            console.print(f"  Average: {q.get('avg_quality', 0):.2f}")
            console.print(f"  Max: {q.get('max_quality', 0):.2f}")
            console.print(f"  Min: {q.get('min_quality', 0):.2f}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def list_characters(
    anime: Optional[str] = typer.Option(
        None,
        "--anime", "-a",
        help="Filter by anime name",
    ),
    limit: int = typer.Option(
        20,
        "--limit", "-l",
        help="Number of characters to display",
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search", "-s",
        help="Search by name",
    ),
):
    """
    List characters in the database.
    """
    try:
        db = get_db_manager()
        db.connect()
        collection = db.get_collection("characters")

        # Build query
        query = {}
        if anime:
            query["anime_name"] = anime
        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        characters = list(collection.find(query).limit(limit))

        if not characters:
            console.print("[yellow]No characters found[/yellow]")
            raise typer.Exit(0)

        # Display table
        table = Table(title=f"Characters ({len(characters)} shown)")
        table.add_column("Name", style="cyan", width=30)
        table.add_column("Anime", style="blue")
        table.add_column("Status", style="yellow")
        table.add_column("Quality", justify="right", style="green")

        for char in characters:
            quality = char.get("quality_score")
            quality_str = f"{quality:.2f}" if quality else "N/A"
            table.add_row(
                char.get("name", "Unknown")[:30],
                char.get("anime_name", "Unknown"),
                char.get("status", "unknown"),
                quality_str,
            )

        console.print(table)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def delete(
    character_id: str = typer.Argument(..., help="Character ID to delete"),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation prompt",
    ),
):
    """
    Delete a character from the database.
    """
    try:
        db = get_db_manager()
        db.connect()
        collection = db.get_collection("characters")

        # Find character first
        character = collection.find_one({"_character_id": character_id})
        if not character:
            console.print(f"[red]Character not found:[/red] {character_id}")
            raise typer.Exit(1)

        # Confirm deletion
        if not force:
            name = character.get("name", "Unknown")
            confirm = typer.confirm(f"Delete character '{name}'?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

        result = collection.delete_one({"_character_id": character_id})
        if result.deleted_count > 0:
            console.print(f"[green]✓[/green] Character deleted successfully")
        else:
            console.print("[red]Failed to delete character[/red]")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def backup(
    collection: str = typer.Option(
        "characters",
        "--collection", "-c",
        help="Collection to backup",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Custom backup name",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for backup",
    ),
):
    """
    Create a backup of the database.

    Example:
        fandom-scraper backup
        fandom-scraper backup --collection characters --name my_backup
    """
    from utils.backup import BackupManager

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating backup...", total=None)

        try:
            db = get_db_manager()
            db.connect()

            backup_dir = str(output_dir) if output_dir else "backups"
            manager = BackupManager(backup_dir=backup_dir)

            progress.update(task, description="Backing up data...")
            result = manager.create_backup(
                db,
                collection_name=collection,
                backup_name=name,
            )

            if result:
                console.print(f"[green]✓[/green] Backup created: {result}")
            else:
                console.print("[red]Backup failed[/red]")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)


@app.command()
def restore(
    backup_file: Path = typer.Argument(..., help="Path to backup file"),
    collection: Optional[str] = typer.Option(
        None,
        "--collection", "-c",
        help="Target collection (uses original if not specified)",
    ),
    drop_existing: bool = typer.Option(
        False,
        "--drop",
        help="Drop existing collection before restore",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation prompt",
    ),
):
    """
    Restore a backup to the database.

    Example:
        fandom-scraper restore backups/characters_20231201.json.gz
        fandom-scraper restore backup.json --collection characters --drop
    """
    from utils.backup import BackupManager

    if not backup_file.exists():
        console.print(f"[red]Backup file not found:[/red] {backup_file}")
        raise typer.Exit(1)

    # Confirm restore
    if not force:
        if drop_existing:
            msg = f"This will DROP the existing collection and restore from {backup_file}. Continue?"
        else:
            msg = f"Restore data from {backup_file}?"

        if not typer.confirm(msg):
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Restoring backup...", total=None)

        try:
            db = get_db_manager()
            db.connect()

            manager = BackupManager()

            progress.update(task, description="Restoring data...")
            result = manager.restore_backup(
                db,
                str(backup_file),
                collection_name=collection,
                drop_existing=drop_existing,
            )

            if result:
                console.print("[green]✓[/green] Restore completed successfully")
            else:
                console.print("[red]Restore failed[/red]")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)


@app.command()
def list_backups():
    """
    List all available backups.
    """
    from utils.backup import BackupManager

    try:
        manager = BackupManager()
        backups = manager.list_backups()

        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            raise typer.Exit(0)

        table = Table(title="Available Backups")
        table.add_column("Backup ID", style="cyan")
        table.add_column("Created", style="blue")
        table.add_column("Collection", style="yellow")
        table.add_column("Documents", justify="right", style="green")
        table.add_column("Size", justify="right")

        for backup in backups:
            created = backup.get("created_at", "Unknown")[:19]
            size_bytes = backup.get("file_size_bytes", 0)
            size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024 * 1024 else f"{size_bytes / 1024 / 1024:.1f} MB"

            table.add_row(
                backup.get("backup_id", "Unknown"),
                created,
                backup.get("collection_name", "Unknown"),
                str(backup.get("document_count", 0)),
                size_str,
            )

        console.print(table)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("scrape-fandom")
def scrape_fandom(
    input_source: str = typer.Argument(
        ...,
        help="Anime name or Fandom URL"
    ),
    input_type: str = typer.Option(
        "name",
        "--type", "-t",
        help="Input type: 'name' or 'url'"
    ),
    max_chars: int = typer.Option(
        100,
        "--max-chars",
        help="Max characters to scrape (0 = unlimited)"
    ),
    max_eps: int = typer.Option(
        50,
        "--max-episodes",
        help="Max episodes to scrape (0 = unlimited)"
    ),
    max_gallery: int = typer.Option(
        200,
        "--max-gallery",
        help="Max gallery images (0 = unlimited)"
    ),
    max_chapters: int = typer.Option(
        0,
        "--max-chapters",
        help="Max chapters to scrape (0 = unlimited)"
    ),
    crawl_characters: bool = typer.Option(
        True,
        "--characters/--no-characters",
        help="Crawl character pages"
    ),
    crawl_episodes: bool = typer.Option(
        True,
        "--episodes/--no-episodes",
        help="Crawl episode pages"
    ),
    crawl_galleries: bool = typer.Option(
        True,
        "--galleries/--no-galleries",
        help="Crawl gallery pages"
    ),
    crawl_chapters: bool = typer.Option(
        False,
        "--chapters/--no-chapters",
        help="Crawl chapter pages"
    ),
    all_categories: bool = typer.Option(
        False,
        "--all",
        help="Enable all categories with no limits"
    ),
):
    """
    Universal Fandom scraper with search support.

    Examples:
        # Using anime name (Brave Search)
        fandom-scraper scrape-fandom "Attack on Titan" --max-chars 100

        # Using direct URL
        fandom-scraper scrape-fandom "https://onepiece.fandom.com" --type url --all

        # Custom scope
        fandom-scraper scrape-fandom "Naruto" --episodes --galleries --no-characters

        # Complete example
        fandom-scraper scrape-fandom "One Piece" \\
          --type name \\
          --max-chars 200 \\
          --max-episodes 100 \\
          --max-gallery 500 \\
          --characters \\
          --episodes \\
          --galleries
    """
    import os

    if all_categories:
        max_chars = max_eps = max_gallery = max_chapters = 0
        crawl_characters = crawl_episodes = crawl_galleries = crawl_chapters = True

    # Validate Brave API key if using name
    if input_type == "name" and not os.getenv("BRAVE_API_KEY"):
        console.print("[red]Error:[/red] BRAVE_API_KEY not found in environment")
        console.print("Please set BRAVE_API_KEY in your ~/.bashrc or environment")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold blue]Universal Fandom Scraper[/bold blue]\n"
        f"Input: {input_source}\n"
        f"Type: {input_type}",
        title="Scraping Configuration",
        expand=False
    ))

    try:
        from scraper.universal_fandom_spider import UniversalFandomSpider
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings

        # Get settings
        settings = get_project_settings()

        # Create crawler process
        process = CrawlerProcess(settings)

        # Spider configuration
        spider_kwargs = {
            'input_source': input_source,
            'input_type': input_type,
            'crawl_characters': crawl_characters,
            'crawl_episodes': crawl_episodes,
            'crawl_galleries': crawl_galleries,
            'crawl_chapters': crawl_chapters,
            'max_chars': max_chars,
            'max_episodes': max_eps,
            'max_gallery_images': max_gallery,
            'max_chapters': max_chapters,
        }

        # Display config
        console.print("\n[bold]Crawl Configuration:[/bold]")
        enabled = []
        if crawl_characters:
            enabled.append(f"Characters (max: {max_chars if max_chars > 0 else 'unlimited'})")
        if crawl_episodes:
            enabled.append(f"Episodes (max: {max_eps if max_eps > 0 else 'unlimited'})")
        if crawl_galleries:
            enabled.append(f"Galleries (max: {max_gallery if max_gallery > 0 else 'unlimited'})")
        if crawl_chapters:
            enabled.append(f"Chapters (max: {max_chapters if max_chapters > 0 else 'unlimited'})")

        for item in enabled:
            console.print(f"  • {item}")

        console.print("\n[yellow]Starting spider...[/yellow]\n")

        # Start crawling
        process.crawl(UniversalFandomSpider, **spider_kwargs)
        process.start()

        console.print("\n[green]✓ Scraping completed successfully![/green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]Error during scraping:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Display version information."""
    console.print(Panel(
        "[bold]Fandom Scraper CLI[/bold]\n"
        "Version: 1.0.0\n"
        "Python: " + sys.version.split()[0],
        title="Version Info",
        expand=False,
    ))


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
