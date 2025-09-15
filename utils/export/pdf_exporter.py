# utils/export/pdf_exporter.py
"""
PDF export functionality for character data.
Provides formatted PDF reports with images and styling.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import io


class PDFExporter:
    """
    Advanced PDF exporter for character reports.

    Features:
    - Formatted PDF reports
    - Image embedding
    - Custom styling and layouts
    - Multi-page support
    - Table of contents
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF exporter.

        Args:
            config: Configuration dictionary with export parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "layout": {
                "page_size": "A4",
                "margin": 72,  # 1 inch in points
                "font_size": 12,
                "title_font_size": 16,
                "header_font_size": 14,
            },
            "styling": {
                "primary_color": "#1f77b4",
                "secondary_color": "#ff7f0e",
                "text_color": "#333333",
                "background_color": "#ffffff",
            },
            "content": {
                "include_images": True,
                "max_image_width": 200,
                "max_image_height": 150,
                "include_toc": True,
                "characters_per_page": 3,
            },
            "output": {"encoding": "utf-8", "quality": "high"},
        }

        if config:
            self.config.update(config)

        # Check for ReportLab
        self.reportlab_available = False
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Image,
                Table,
                TableStyle,
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors

            self.letter = letter
            self.A4 = A4
            self.SimpleDocTemplate = SimpleDocTemplate
            self.Paragraph = Paragraph
            self.Spacer = Spacer
            self.Image = Image
            self.Table = Table
            self.TableStyle = TableStyle
            self.getSampleStyleSheet = getSampleStyleSheet
            self.ParagraphStyle = ParagraphStyle
            self.inch = inch
            self.colors = colors

            self.reportlab_available = True
            self.logger.info("ReportLab available for PDF export")
        except ImportError:
            self.logger.warning("ReportLab not available - PDF export disabled")

    def export_character_report(
        self,
        characters: List[Dict[str, Any]],
        output_path: str,
        title: str = "Character Report",
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export characters as formatted PDF report.

        Args:
            characters: List of character data
            output_path: Output PDF file path
            title: Report title
            custom_config: Optional custom configuration

        Returns:
            Export result with status and metadata
        """
        if not characters:
            return {"success": False, "error": "No characters provided"}

        if not self.reportlab_available:
            return {"success": False, "error": "ReportLab not available for PDF export"}

        self.logger.info(
            f"Exporting {len(characters)} characters to PDF: {output_path}"
        )

        try:
            # Apply configuration
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Create PDF document
            page_size = (
                self.A4 if config["layout"]["page_size"] == "A4" else self.letter
            )
            doc = self.SimpleDocTemplate(
                str(output_path),
                pagesize=page_size,
                rightMargin=config["layout"]["margin"],
                leftMargin=config["layout"]["margin"],
                topMargin=config["layout"]["margin"],
                bottomMargin=config["layout"]["margin"],
            )

            # Create styles
            styles = self._create_pdf_styles(config)

            # Build document content
            story = []

            # Add title page
            self._add_title_page(story, title, characters, styles, config)

            # Add table of contents if configured
            if config["content"]["include_toc"]:
                self._add_table_of_contents(story, characters, styles)

            # Add character sections
            self._add_character_sections(story, characters, styles, config)

            # Add statistics summary
            self._add_statistics_summary(story, characters, styles, config)

            # Build PDF
            doc.build(story)

            # Get file statistics
            file_size = output_file.stat().st_size

            return {
                "success": True,
                "output_path": str(output_path),
                "characters_exported": len(characters),
                "file_size": file_size,
                "pages_estimated": len(characters)
                // config["content"]["characters_per_page"]
                + 3,
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            error_msg = f"PDF export failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def export_summary_report(
        self,
        characters: List[Dict[str, Any]],
        output_path: str,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export summary statistics report as PDF.

        Args:
            characters: List of character data
            output_path: Output PDF file path
            custom_config: Optional custom configuration

        Returns:
            Export result
        """
        if not self.reportlab_available:
            return {"success": False, "error": "ReportLab not available for PDF export"}

        try:
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Create PDF document
            page_size = (
                self.A4 if config["layout"]["page_size"] == "A4" else self.letter
            )
            doc = self.SimpleDocTemplate(str(output_path), pagesize=page_size)

            # Create styles
            styles = self._create_pdf_styles(config)

            # Build summary content
            story = []

            # Title
            story.append(
                self.Paragraph("Character Data Summary Report", styles["title"])
            )
            story.append(self.Spacer(1, 20))

            # Generate and add statistics
            stats = self._calculate_statistics(characters)
            self._add_statistics_content(story, stats, styles)

            # Build PDF
            doc.build(story)

            file_size = output_file.stat().st_size

            return {
                "success": True,
                "output_path": str(output_path),
                "file_size": file_size,
                "report_type": "summary",
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": f"Summary report export failed: {e}"}

    def _create_pdf_styles(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create PDF styles for formatting."""
        styles = self.getSampleStyleSheet()

        # Custom styles
        custom_styles = {
            "title": self.ParagraphStyle(
                "CustomTitle",
                parent=styles["Title"],
                fontSize=config["layout"]["title_font_size"],
                textColor=config["styling"]["primary_color"],
                spaceAfter=30,
                alignment=1,  # Center
            ),
            "heading": self.ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading1"],
                fontSize=config["layout"]["header_font_size"],
                textColor=config["styling"]["primary_color"],
                spaceAfter=12,
                spaceBefore=20,
            ),
            "normal": self.ParagraphStyle(
                "CustomNormal",
                parent=styles["Normal"],
                fontSize=config["layout"]["font_size"],
                textColor=config["styling"]["text_color"],
            ),
            "character_name": self.ParagraphStyle(
                "CharacterName",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=config["styling"]["secondary_color"],
                spaceAfter=8,
                spaceBefore=16,
            ),
        }

        return custom_styles

    def _add_title_page(
        self,
        story: List,
        title: str,
        characters: List[Dict[str, Any]],
        styles: Dict[str, Any],
        config: Dict[str, Any],
    ):
        """Add title page to the PDF."""
        # Main title
        story.append(self.Paragraph(title, styles["title"]))
        story.append(self.Spacer(1, 30))

        # Report information
        report_info = [
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Characters: {len(characters)}",
            f"Sources: {len(set(char.get('source', 'Unknown') for char in characters))}",
        ]

        for info in report_info:
            story.append(self.Paragraph(info, styles["normal"]))
            story.append(self.Spacer(1, 10))

        # Page break
        from reportlab.platypus import PageBreak

        story.append(PageBreak())

    def _add_table_of_contents(
        self, story: List, characters: List[Dict[str, Any]], styles: Dict[str, Any]
    ):
        """Add table of contents."""
        story.append(self.Paragraph("Table of Contents", styles["heading"]))
        story.append(self.Spacer(1, 20))

        toc_data = [["Character Name", "Page"]]

        # Estimate page numbers (simplified)
        page_num = 3  # Start after title and TOC
        chars_per_page = 3

        for i, character in enumerate(characters):
            name = character.get("name", "Unknown")
            if i > 0 and i % chars_per_page == 0:
                page_num += 1
            toc_data.append([name, str(page_num)])

        # Add statistics section
        toc_data.append(["Statistics Summary", str(page_num + 1)])

        # Create table
        toc_table = self.Table(toc_data)
        toc_table.setStyle(
            self.TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), self.colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, self.colors.black),
                ]
            )
        )

        story.append(toc_table)

        # Page break
        from reportlab.platypus import PageBreak

        story.append(PageBreak())

    def _add_character_sections(
        self,
        story: List,
        characters: List[Dict[str, Any]],
        styles: Dict[str, Any],
        config: Dict[str, Any],
    ):
        """Add character sections to the PDF."""
        chars_added = 0

        for character in characters:
            # Character name as heading
            name = character.get("name", "Unknown Character")
            story.append(self.Paragraph(name, styles["character_name"]))

            # Character details
            self._add_character_details(story, character, styles, config)

            chars_added += 1

            # Add page break if needed
            if chars_added % config["content"]["characters_per_page"] == 0:
                from reportlab.platypus import PageBreak

                story.append(PageBreak())
            else:
                story.append(self.Spacer(1, 20))

    def _add_character_details(
        self,
        story: List,
        character: Dict[str, Any],
        styles: Dict[str, Any],
        config: Dict[str, Any],
    ):
        """Add details for a single character."""
        # Basic information
        basic_info = []

        source = character.get("source", "Unknown")
        basic_info.append(f"<b>Source:</b> {source}")

        if character.get("categories"):
            categories = ", ".join(character["categories"][:5])  # Limit to 5
            basic_info.append(f"<b>Categories:</b> {categories}")

        if character.get("url"):
            basic_info.append(f"<b>Source URL:</b> {character['url']}")

        # Add basic info paragraphs
        for info in basic_info:
            story.append(self.Paragraph(info, styles["normal"]))
            story.append(self.Spacer(1, 8))

        # Description
        description = character.get("description", "")
        if description:
            story.append(self.Paragraph("<b>Description:</b>", styles["normal"]))
            # Truncate long descriptions
            if len(description) > 500:
                description = description[:500] + "..."
            story.append(self.Paragraph(description, styles["normal"]))
            story.append(self.Spacer(1, 12))

        # Add image if available and configured
        if config["content"]["include_images"] and character.get("images"):
            self._add_character_image(story, character, config)

    def _add_character_image(
        self, story: List, character: Dict[str, Any], config: Dict[str, Any]
    ):
        """Add character image to PDF if available."""
        try:
            images = character.get("images", [])
            if not images:
                return

            # Try to use the first image
            image_info = (
                images[0] if isinstance(images[0], dict) else {"url": images[0]}
            )
            image_path = image_info.get("local_path") or image_info.get("url")

            if image_path and Path(image_path).exists():
                # Add image
                img = self.Image(
                    image_path,
                    width=config["content"]["max_image_width"],
                    height=config["content"]["max_image_height"],
                    kind="proportional",
                )
                story.append(img)
                story.append(self.Spacer(1, 12))

        except Exception as e:
            self.logger.warning(f"Failed to add image for character: {e}")

    def _add_statistics_summary(
        self,
        story: List,
        characters: List[Dict[str, Any]],
        styles: Dict[str, Any],
        config: Dict[str, Any],
    ):
        """Add statistics summary section."""
        from reportlab.platypus import PageBreak

        story.append(PageBreak())

        story.append(self.Paragraph("Statistics Summary", styles["heading"]))
        story.append(self.Spacer(1, 20))

        # Calculate statistics
        stats = self._calculate_statistics(characters)

        # Add statistics content
        self._add_statistics_content(story, stats, styles)

    def _add_statistics_content(
        self, story: List, stats: Dict[str, Any], styles: Dict[str, Any]
    ):
        """Add statistics content to the story."""
        # Overview
        overview_data = [
            ["Metric", "Value"],
            ["Total Characters", str(stats["total_characters"])],
            ["Unique Sources", str(stats["unique_sources"])],
            ["Total Categories", str(stats["total_categories"])],
            ["Characters with Images", str(stats["characters_with_images"])],
            [
                "Average Description Length",
                f"{stats['avg_description_length']:.0f} chars",
            ],
        ]

        overview_table = self.Table(overview_data)
        overview_table.setStyle(
            self.TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), self.colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, self.colors.black),
                ]
            )
        )

        story.append(overview_table)
        story.append(self.Spacer(1, 20))

        # Source distribution
        if stats["source_distribution"]:
            story.append(self.Paragraph("Source Distribution", styles["heading"]))
            story.append(self.Spacer(1, 12))

            source_data = [["Source", "Count", "Percentage"]]
            total = stats["total_characters"]

            for source, count in sorted(
                stats["source_distribution"].items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / total * 100) if total > 0 else 0
                source_data.append([source, str(count), f"{percentage:.1f}%"])

            source_table = self.Table(source_data)
            source_table.setStyle(
                self.TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), self.colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), self.colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, self.colors.black),
                    ]
                )
            )

            story.append(source_table)
            story.append(self.Spacer(1, 20))

        # Top categories
        if stats["category_distribution"]:
            story.append(self.Paragraph("Top Categories", styles["heading"]))
            story.append(self.Spacer(1, 12))

            # Show top 10 categories
            top_categories = sorted(
                stats["category_distribution"].items(), key=lambda x: x[1], reverse=True
            )[:10]

            cat_data = [["Category", "Count"]]
            for category, count in top_categories:
                cat_data.append([category, str(count)])

            cat_table = self.Table(cat_data)
            cat_table.setStyle(
                self.TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), self.colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), self.colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, self.colors.black),
                    ]
                )
            )

            story.append(cat_table)

    def _calculate_statistics(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics for the character data."""
        stats = {
            "total_characters": len(characters),
            "unique_sources": 0,
            "source_distribution": {},
            "total_categories": 0,
            "category_distribution": {},
            "characters_with_images": 0,
            "characters_with_descriptions": 0,
            "avg_description_length": 0,
            "date_range": {},
        }

        description_lengths = []
        all_categories = []
        sources = set()

        for character in characters:
            # Source tracking
            source = character.get("source", "Unknown")
            sources.add(source)
            stats["source_distribution"][source] = (
                stats["source_distribution"].get(source, 0) + 1
            )

            # Categories
            categories = character.get("categories", [])
            if categories:
                all_categories.extend(categories)
                for category in categories:
                    stats["category_distribution"][category] = (
                        stats["category_distribution"].get(category, 0) + 1
                    )

            # Images
            if character.get("images"):
                stats["characters_with_images"] += 1

            # Descriptions
            description = character.get("description", "")
            if description:
                stats["characters_with_descriptions"] += 1
                description_lengths.append(len(description))

        # Calculate averages and totals
        stats["unique_sources"] = len(sources)
        stats["total_categories"] = len(set(all_categories))
        stats["avg_description_length"] = (
            sum(description_lengths) / len(description_lengths)
            if description_lengths
            else 0
        )

        return stats


def create_pdf_export_config() -> Dict[str, Any]:
    """Create default configuration for PDF exporter."""
    return {
        "layout": {
            "page_size": "A4",
            "margin": 72,
            "font_size": 12,
            "title_font_size": 16,
            "header_font_size": 14,
        },
        "styling": {
            "primary_color": "#1f77b4",
            "secondary_color": "#ff7f0e",
            "text_color": "#333333",
            "background_color": "#ffffff",
        },
        "content": {
            "include_images": True,
            "max_image_width": 200,
            "max_image_height": 150,
            "include_toc": True,
            "characters_per_page": 3,
        },
        "output": {"encoding": "utf-8", "quality": "high"},
    }
