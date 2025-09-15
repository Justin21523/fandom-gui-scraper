"""
CSV export functionality for character data.
Provides flexible CSV export with data flattening and customizable formatting.
"""

import csv
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import json


class CSVExporter:
    """
    Advanced CSV exporter with data flattening and formatting options.

    Features:
    - Automatic data flattening for nested structures
    - Customizable field selection and ordering
    - Multiple CSV dialects and formats
    - Data type handling and formatting
    - Large dataset streaming support
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CSV exporter.

        Args:
            config: Configuration dictionary with export parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "csv_format": {
                "delimiter": ",",
                "quotechar": '"',
                "quoting": csv.QUOTE_MINIMAL,
                "lineterminator": "\n",
                "escapechar": None,
            },
            "data_handling": {
                "flatten_nested": True,
                "flatten_separator": "_",
                "list_separator": "; ",
                "null_value": "",
                "boolean_format": "true/false",  # 'true/false', '1/0', 'yes/no'
                "date_format": "%Y-%m-%d %H:%M:%S",
            },
            "output": {
                "include_headers": True,
                "encoding": "utf-8-sig",  # UTF-8 with BOM for Excel compatibility
                "include_metadata": False,
                "max_field_length": 32767,  # Excel cell limit
            },
            "field_config": {
                "exclude_fields": ["_id", "__v"],
                "include_only": None,
                "field_order": None,  # List of fields in desired order
                "custom_headers": {},  # Map field names to custom header names
            },
        }

        if config:
            self.config.update(config)

    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export character data to CSV file.

        Args:
            data: List of character records to export
            output_path: Output CSV file path
            custom_config: Optional custom configuration

        Returns:
            Export result with status and metadata
        """
        if not data:
            return {"success": False, "error": "No data provided"}

        self.logger.info(f"Exporting {len(data)} records to CSV: {output_path}")

        try:
            # Apply configuration
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)

            # Flatten and process data
            flattened_data = self._flatten_data(data, config)

            # Determine fields and headers
            fields, headers = self._determine_fields_and_headers(flattened_data, config)

            # Write CSV file
            result = self._write_csv_file(
                flattened_data, fields, headers, output_path, config
            )

            if result["success"]:
                self.logger.info(
                    f"Successfully exported {len(data)} records to {output_path}"
                )

            return result

        except Exception as e:
            error_msg = f"CSV export failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def export_filtered_csv(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Export filtered CSV with specific field selection.

        Args:
            data: List of character records
            output_path: Output file path
            include_fields: Fields to include (if specified, only these are included)
            exclude_fields: Fields to exclude

        Returns:
            Export result
        """
        filter_config = {
            "field_config": {
                "include_only": include_fields,
                "exclude_fields": exclude_fields or [],
            }
        }

        return self.export_to_csv(data, output_path, filter_config)

    def export_with_custom_headers(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        header_mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Export CSV with custom column headers.

        Args:
            data: List of character records
            output_path: Output file path
            header_mapping: Map of field names to custom headers

        Returns:
            Export result
        """
        header_config = {"field_config": {"custom_headers": header_mapping}}

        return self.export_to_csv(data, output_path, header_config)

    def export_excel_compatible(
        self, data: List[Dict[str, Any]], output_path: str
    ) -> Dict[str, Any]:
        """
        Export CSV optimized for Excel compatibility.

        Args:
            data: List of character records
            output_path: Output file path

        Returns:
            Export result
        """
        excel_config = {
            "csv_format": {
                "delimiter": ",",
                "quotechar": '"',
                "quoting": csv.QUOTE_ALL,
            },
            "output": {
                "encoding": "utf-8-sig",  # UTF-8 with BOM
                "include_headers": True,
            },
            "data_handling": {
                "max_field_length": 32767,  # Excel limit
                "date_format": "%Y-%m-%d %H:%M:%S",
            },
        }

        return self.export_to_csv(data, output_path, excel_config)

    def export_streaming(
        self, data_generator, output_path: str, total_records: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Export large datasets using streaming to avoid memory issues.

        Args:
            data_generator: Generator yielding character records
            output_path: Output file path
            total_records: Total number of records (for progress tracking)

        Returns:
            Export result
        """
        self.logger.info(f"Starting streaming CSV export to {output_path}")

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            config = self.config
            processed_count = 0
            fields_determined = False
            fields = []
            headers = []

            with open(
                output_path, "w", newline="", encoding=config["output"]["encoding"]
            ) as csvfile:
                writer = None

                for record in data_generator:
                    # Flatten record
                    flattened = self._flatten_single_record(record, config)

                    # Determine fields from first record
                    if not fields_determined:
                        fields, headers = self._determine_fields_and_headers(
                            [flattened], config
                        )

                        # Create CSV writer
                        writer = csv.DictWriter(
                            csvfile, fieldnames=fields, **config["csv_format"]
                        )

                        # Write headers
                        if config["output"]["include_headers"]:
                            header_row = dict(zip(fields, headers))
                            writer.writerow(header_row)

                        fields_determined = True

                    # Write record
                    filtered_record = {
                        field: flattened.get(field, "") for field in fields
                    }
                    writer.writerow(filtered_record)
                    processed_count += 1

                    # Log progress periodically
                    if processed_count % 1000 == 0:
                        self.logger.info(f"Processed {processed_count} records")

            file_size = output_file.stat().st_size

            return {
                "success": True,
                "output_path": str(output_path),
                "records_exported": processed_count,
                "file_size": file_size,
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            error_msg = f"Streaming export failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def _flatten_data(
        self, data: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Flatten nested data structures for CSV format."""
        flattened_records = []

        for record in data:
            flattened = self._flatten_single_record(record, config)
            flattened_records.append(flattened)

        return flattened_records

    def _flatten_single_record(
        self, record: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Flatten a single record."""
        if not config["data_handling"]["flatten_nested"]:
            return self._process_simple_record(record, config)

        flattened = {}
        separator = config["data_handling"]["flatten_separator"]

        def flatten_recursive(obj: Any, prefix: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}{separator}{key}" if prefix else key
                    flatten_recursive(value, new_key)
            elif isinstance(obj, list):
                # Handle lists by joining elements or flattening each item
                if all(isinstance(item, (str, int, float, bool)) for item in obj):
                    # Simple list - join elements
                    list_sep = config["data_handling"]["list_separator"]
                    flattened[prefix] = list_sep.join(str(item) for item in obj)
                else:
                    # Complex list - flatten each item with index
                    for i, item in enumerate(obj):
                        new_key = f"{prefix}{separator}{i}"
                        flatten_recursive(item, new_key)
            else:
                # Simple value
                flattened[prefix] = self._format_value(obj, config)

        flatten_recursive(record)

        # Apply field filters
        return self._apply_field_filters(flattened, config["field_config"])

    def _process_simple_record(
        self, record: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process record without flattening nested structures."""
        processed = {}
        list_sep = config["data_handling"]["list_separator"]

        for key, value in record.items():
            if isinstance(value, list):
                # Convert list to string
                processed[key] = list_sep.join(str(item) for item in value)
            elif isinstance(value, dict):
                # Convert dict to JSON string
                processed[key] = json.dumps(value, ensure_ascii=False)
            else:
                processed[key] = self._format_value(value, config)

        return self._apply_field_filters(processed, config["field_config"])

    def _format_value(self, value: Any, config: Dict[str, Any]) -> str:
        """Format a value for CSV output."""
        if value is None:
            return config["data_handling"]["null_value"]

        if isinstance(value, bool):
            bool_format = config["data_handling"]["boolean_format"]
            if bool_format == "1/0":
                return "1" if value else "0"
            elif bool_format == "yes/no":
                return "yes" if value else "no"
            else:  # 'true/false'
                return "true" if value else "false"

        if isinstance(value, datetime):
            return value.strftime(config["data_handling"]["date_format"])

        # Convert to string and limit length if necessary
        str_value = str(value)
        max_length = config["output"]["max_field_length"]
        if len(str_value) > max_length:
            str_value = str_value[: max_length - 3] + "..."

        return str_value

    def _apply_field_filters(
        self, record: Dict[str, Any], field_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply field inclusion/exclusion filters."""
        filtered = dict(record)

        # Include only specific fields if specified
        include_only = field_config.get("include_only")
        if include_only:
            filtered = {k: v for k, v in filtered.items() if k in include_only}

        # Exclude specified fields
        exclude_fields = field_config.get("exclude_fields", [])
        for field in exclude_fields:
            filtered.pop(field, None)

        return filtered

    def _determine_fields_and_headers(
        self, data: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> tuple[List[str], List[str]]:
        """Determine field order and headers for CSV."""
        # Collect all unique fields from all records
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())

        # Apply field ordering
        field_config = config["field_config"]
        field_order = field_config.get("field_order")

        if field_order:
            # Use specified order, add remaining fields at the end
            ordered_fields = []
            for field in field_order:
                if field in all_fields:
                    ordered_fields.append(field)

            # Add remaining fields
            remaining_fields = sorted(all_fields - set(ordered_fields))
            fields = ordered_fields + remaining_fields
        else:
            # Default alphabetical order
            fields = sorted(all_fields)

        # Generate headers
        custom_headers = field_config.get("custom_headers", {})
        headers = []

        for field in fields:
            if field in custom_headers:
                headers.append(custom_headers[field])
            else:
                # Convert field name to readable header
                header = field.replace("_", " ").title()
                headers.append(header)

        return fields, headers

    def _write_csv_file(
        self,
        data: List[Dict[str, Any]],
        fields: List[str],
        headers: List[str],
        output_path: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Write data to CSV file."""
        try:
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write CSV file
            with open(
                output_path, "w", newline="", encoding=config["output"]["encoding"]
            ) as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=fields, **config["csv_format"]
                )

                # Write headers
                if config["output"]["include_headers"]:
                    header_row = dict(zip(fields, headers))
                    writer.writerow(header_row)

                # Write data rows
                for record in data:
                    # Ensure all fields are present
                    row_data = {field: record.get(field, "") for field in fields}
                    writer.writerow(row_data)

            # Get file statistics
            file_size = output_file.stat().st_size

            return {
                "success": True,
                "output_path": str(output_path),
                "records_exported": len(data),
                "fields_exported": len(fields),
                "file_size": file_size,
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to write CSV file: {e}"}


def create_csv_export_config() -> Dict[str, Any]:
    """Create default configuration for CSV exporter."""
    return {
        "csv_format": {
            "delimiter": ",",
            "quotechar": '"',
            "quoting": csv.QUOTE_MINIMAL,
            "lineterminator": "\n",
            "escapechar": None,
        },
        "data_handling": {
            "flatten_nested": True,
            "flatten_separator": "_",
            "list_separator": "; ",
            "null_value": "",
            "boolean_format": "true/false",
            "date_format": "%Y-%m-%d %H:%M:%S",
        },
        "output": {
            "include_headers": True,
            "encoding": "utf-8-sig",
            "include_metadata": False,
            "max_field_length": 32767,
        },
        "field_config": {
            "exclude_fields": ["_id", "__v", "_rev"],
            "include_only": None,
            "field_order": ["name", "description", "source", "url"],
            "custom_headers": {
                "name": "Character Name",
                "description": "Description",
                "source": "Data Source",
                "url": "Source URL",
                "scraped_at": "Last Updated",
            },
        },
    }
