# utils/export/excel_exporter.py
"""
Excel export functionality for character data.
Provides advanced Excel export with multiple sheets, formatting, and charts.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class ExcelExporter:
    """
    Advanced Excel exporter with multiple sheets and formatting options.

    Features:
    - Multiple sheet support
    - Rich formatting and styling
    - Charts and visualizations
    - Data validation
    - Conditional formatting
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Excel exporter.

        Args:
            config: Configuration dictionary with export parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "formatting": {
                "header_style": {
                    "bold": True,
                    "bg_color": "#4472C4",
                    "font_color": "#FFFFFF",
                    "border": 1,
                },
                "data_style": {"border": 1, "text_wrap": True},
                "freeze_panes": True,
            },
            "sheets": {
                "main_sheet": "Characters",
                "stats_sheet": "Statistics",
                "sources_sheet": "Sources",
            },
            "charts": {"include_charts": True, "chart_types": ["pie", "column"]},
            "output": {"encoding": "utf-8", "date_format": "YYYY-MM-DD HH:MM:SS"},
        }

        if config:
            self.config.update(config)

        # Check for xlsxwriter
        self.xlsxwriter_available = False
        try:
            import xlsxwriter

            self.xlsxwriter = xlsxwriter
            self.xlsxwriter_available = True
            self.logger.info("XlsxWriter available for Excel export")
        except ImportError:
            self.logger.warning("XlsxWriter not available - Excel export disabled")

    def export_to_excel(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export character data to Excel file with multiple sheets.

        Args:
            data: List of character records to export
            output_path: Output Excel file path
            custom_config: Optional custom configuration

        Returns:
            Export result with status and metadata
        """
        if not data:
            return {"success": False, "error": "No data provided"}

        if not self.xlsxwriter_available:
            return {
                "success": False,
                "error": "XlsxWriter not available for Excel export",
            }

        self.logger.info(f"Exporting {len(data)} records to Excel: {output_path}")

        try:
            # Apply configuration
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Create workbook
            workbook = self.xlsxwriter.Workbook(str(output_path))

            # Create formats
            formats = self._create_formats(workbook, config)

            # Export main data sheet
            self._export_characters_sheet(workbook, data, formats, config)

            # Export statistics sheet
            self._export_statistics_sheet(workbook, data, formats, config)

            # Export sources sheet
            self._export_sources_sheet(workbook, data, formats, config)

            # Add charts if configured
            if config["charts"]["include_charts"]:
                self._add_charts(workbook, data, config)

            # Close workbook
            workbook.close()

            # Get file statistics
            file_size = output_file.stat().st_size

            return {
                "success": True,
                "output_path": str(output_path),
                "records_exported": len(data),
                "file_size": file_size,
                "sheets_created": len(config["sheets"]),
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            error_msg = f"Excel export failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def _create_formats(self, workbook, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Excel formats for styling."""
        formats = {}

        # Header format
        header_style = config["formatting"]["header_style"]
        formats["header"] = workbook.add_format(
            {
                "bold": header_style.get("bold", True),
                "bg_color": header_style.get("bg_color", "#4472C4"),
                "font_color": header_style.get("font_color", "#FFFFFF"),
                "border": header_style.get("border", 1),
                "align": "center",
                "valign": "vcenter",
            }
        )

        # Data format
        data_style = config["formatting"]["data_style"]
        formats["data"] = workbook.add_format(
            {
                "border": data_style.get("border", 1),
                "text_wrap": data_style.get("text_wrap", True),
                "valign": "top",
            }
        )

        # Date format
        formats["date"] = workbook.add_format(
            {"num_format": config["output"]["date_format"], "border": 1}
        )

        # Number format
        formats["number"] = workbook.add_format({"num_format": "0.00", "border": 1})

        return formats

    def _export_characters_sheet(
        self,
        workbook,
        data: List[Dict[str, Any]],
        formats: Dict[str, Any],
        config: Dict[str, Any],
    ):
        """Export main characters data to worksheet."""
        worksheet = workbook.add_worksheet(config["sheets"]["main_sheet"])

        # Prepare data for export
        flattened_data = self._flatten_data_for_excel(data)

        if not flattened_data:
            return

        # Get headers
        headers = list(flattened_data[0].keys())

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header.replace("_", " ").title(), formats["header"])

        # Write data
        for row, record in enumerate(flattened_data, 1):
            for col, header in enumerate(headers):
                value = record.get(header, "")

                # Format based on data type
                if isinstance(value, datetime):
                    worksheet.write(row, col, value, formats["date"])
                elif isinstance(value, (int, float)):
                    worksheet.write(row, col, value, formats["number"])
                else:
                    worksheet.write(row, col, str(value), formats["data"])

        # Set column widths
        for col, header in enumerate(headers):
            if "description" in header.lower():
                worksheet.set_column(col, col, 50)
            elif "name" in header.lower():
                worksheet.set_column(col, col, 25)
            elif "url" in header.lower():
                worksheet.set_column(col, col, 40)
            else:
                worksheet.set_column(col, col, 15)

        # Freeze panes
        if config["formatting"]["freeze_panes"]:
            worksheet.freeze_panes(1, 0)

        # Add filters
        worksheet.autofilter(0, 0, len(flattened_data), len(headers) - 1)

    def _export_statistics_sheet(
        self,
        workbook,
        data: List[Dict[str, Any]],
        formats: Dict[str, Any],
        config: Dict[str, Any],
    ):
        """Export statistics summary to worksheet."""
        worksheet = workbook.add_worksheet(config["sheets"]["stats_sheet"])

        # Calculate statistics
        stats = self._calculate_export_statistics(data)

        # Write statistics
        row = 0

        # Title
        worksheet.write(row, 0, "Export Statistics", formats["header"])
        row += 2

        # Basic stats
        worksheet.write(row, 0, "Total Characters:", formats["data"])
        worksheet.write(row, 1, stats["total_characters"], formats["number"])
        row += 1

        worksheet.write(row, 0, "Export Date:", formats["data"])
        worksheet.write(row, 1, datetime.now(), formats["date"])
        row += 2

        # Source distribution
        worksheet.write(row, 0, "Source Distribution:", formats["header"])
        row += 1

        for source, count in stats["source_distribution"].items():
            worksheet.write(row, 0, source, formats["data"])
            worksheet.write(row, 1, count, formats["number"])
            row += 1

        # Set column widths
        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 15)

    def _export_sources_sheet(
        self,
        workbook,
        data: List[Dict[str, Any]],
        formats: Dict[str, Any],
        config: Dict[str, Any],
    ):
        """Export source information to worksheet."""
        worksheet = workbook.add_worksheet(config["sheets"]["sources_sheet"])

        # Extract unique sources
        sources_info = self._extract_sources_info(data)

        # Headers
        headers = [
            "Source",
            "Character Count",
            "First Scraped",
            "Last Scraped",
            "Sample URLs",
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, formats["header"])

        # Write source data
        for row, (source, info) in enumerate(sources_info.items(), 1):
            worksheet.write(row, 0, source, formats["data"])
            worksheet.write(row, 1, info["count"], formats["number"])
            worksheet.write(
                row,
                2,
                info["first_scraped"],
                formats["date"] if info["first_scraped"] else formats["data"],
            )
            worksheet.write(
                row,
                3,
                info["last_scraped"],
                formats["date"] if info["last_scraped"] else formats["data"],
            )
            worksheet.write(row, 4, ", ".join(info["sample_urls"][:3]), formats["data"])

        # Set column widths
        worksheet.set_column(0, 0, 20)  # Source
        worksheet.set_column(1, 1, 15)  # Count
        worksheet.set_column(2, 3, 20)  # Dates
        worksheet.set_column(4, 4, 50)  # URLs

        # Freeze panes
        worksheet.freeze_panes(1, 0)

    def _add_charts(self, workbook, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Add charts to the workbook."""
        try:
            # Get statistics
            stats = self._calculate_export_statistics(data)

            # Create charts worksheet
            chart_sheet = workbook.add_worksheet("Charts")

            # Source distribution pie chart
            if "pie" in config["charts"]["chart_types"]:
                chart = workbook.add_chart({"type": "pie"})

                # Add data to chart sheet for reference
                row = 1
                chart_sheet.write(0, 0, "Source")
                chart_sheet.write(0, 1, "Count")

                for source, count in stats["source_distribution"].items():
                    chart_sheet.write(row, 0, source)
                    chart_sheet.write(row, 1, count)
                    row += 1

                # Configure chart
                chart.add_series(
                    {
                        "name": "Character Distribution by Source",
                        "categories": ["Charts", 1, 0, row - 1, 0],
                        "values": ["Charts", 1, 1, row - 1, 1],
                    }
                )

                chart.set_title({"name": "Character Distribution by Source"})
                chart.set_style(10)

                # Insert chart
                chart_sheet.insert_chart("D2", chart)

        except Exception as e:
            self.logger.warning(f"Failed to add charts: {e}")

    def _flatten_data_for_excel(
        self, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Flatten nested data for Excel export."""
        flattened = []

        for record in data:
            flat_record = {}

            for key, value in record.items():
                if isinstance(value, dict):
                    # Flatten nested dictionaries
                    for sub_key, sub_value in value.items():
                        flat_key = f"{key}_{sub_key}"
                        flat_record[flat_key] = sub_value
                elif isinstance(value, list):
                    # Convert lists to string
                    flat_record[key] = "; ".join(str(item) for item in value)
                else:
                    flat_record[key] = value

            flattened.append(flat_record)

        return flattened

    def _calculate_export_statistics(
        self, data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistics for the exported data."""
        stats = {
            "total_characters": len(data),
            "source_distribution": {},
            "categories_count": 0,
            "images_count": 0,
        }

        # Count sources
        for record in data:
            source = record.get("source", "Unknown")
            stats["source_distribution"][source] = (
                stats["source_distribution"].get(source, 0) + 1
            )

        # Count categories and images
        for record in data:
            if record.get("categories"):
                stats["categories_count"] += len(record["categories"])
            if record.get("images"):
                stats["images_count"] += len(record["images"])

        return stats

    def _extract_sources_info(
        self, data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract detailed information about sources."""
        sources_info = {}

        for record in data:
            source = record.get("source", "Unknown")

            if source not in sources_info:
                sources_info[source] = {
                    "count": 0,
                    "first_scraped": None,
                    "last_scraped": None,
                    "sample_urls": [],
                }

            info = sources_info[source]
            info["count"] += 1

            # Track scraping dates
            scraped_at = record.get("scraped_at")
            if scraped_at:
                try:
                    if isinstance(scraped_at, str):
                        scraped_date = datetime.fromisoformat(
                            scraped_at.replace("Z", "+00:00")
                        )
                    else:
                        scraped_date = scraped_at

                    if (
                        not info["first_scraped"]
                        or scraped_date < info["first_scraped"]
                    ):
                        info["first_scraped"] = scraped_date

                    if not info["last_scraped"] or scraped_date > info["last_scraped"]:
                        info["last_scraped"] = scraped_date

                except Exception:
                    pass

            # Collect sample URLs
            url = record.get("url")
            if url and url not in info["sample_urls"] and len(info["sample_urls"]) < 5:
                info["sample_urls"].append(url)

        return sources_info


def create_excel_export_config() -> Dict[str, Any]:
    """Create default configuration for Excel exporter."""
    return {
        "formatting": {
            "header_style": {
                "bold": True,
                "bg_color": "#4472C4",
                "font_color": "#FFFFFF",
                "border": 1,
            },
            "data_style": {"border": 1, "text_wrap": True},
            "freeze_panes": True,
        },
        "sheets": {
            "main_sheet": "Characters",
            "stats_sheet": "Statistics",
            "sources_sheet": "Sources",
        },
        "charts": {"include_charts": True, "chart_types": ["pie", "column"]},
        "output": {"encoding": "utf-8", "date_format": "YYYY-MM-DD HH:MM:SS"},
    }
