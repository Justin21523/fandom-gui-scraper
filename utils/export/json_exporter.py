# utils/export/json_exporter.py
"""
JSON export functionality for character data.
Provides flexible JSON export with customizable formatting and filtering.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path


class JSONExporter:
    """
    Advanced JSON exporter with multiple formatting options and filters.

    Features:
    - Customizable JSON formatting
    - Field filtering and selection
    - Data transformation and sanitization
    - Multiple output formats (compact, pretty, structured)
    - Export validation and verification
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize JSON exporter.

        Args:
            config: Configuration dictionary with export parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "formatting": {
                "indent": 2,
                "ensure_ascii": False,
                "sort_keys": True,
                "separators": (",", ": "),
            },
            "output": {
                "include_metadata": True,
                "include_empty_fields": False,
                "include_private_fields": False,
                "timestamp_format": "iso",
                "encoding": "utf-8",
            },
            "validation": {
                "validate_output": True,
                "max_file_size": 100 * 1024 * 1024,  # 100MB
                "check_json_validity": True,
            },
            "filters": {
                "exclude_fields": ["_id", "__v"],
                "include_only": None,  # If set, only these fields are included
                "transform_functions": {},
            },
        }

        if config:
            self.config.update(config)

    def export_single(
        self,
        data: Dict[str, Any],
        output_path: str,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export single character record to JSON file.

        Args:
            data: Character data to export
            output_path: Output file path
            custom_config: Optional custom configuration

        Returns:
            Export result with status and metadata
        """
        if not data:
            return {"success": False, "error": "No data provided"}

        self.logger.info(f"Exporting single record to {output_path}")

        try:
            # Apply configuration
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)

            # Process data
            processed_data = self._process_single_record(data, config)

            # Add export metadata
            if config["output"]["include_metadata"]:
                processed_data = self._add_export_metadata(processed_data, "single")

            # Write to file
            result = self._write_json_file(processed_data, output_path, config)

            if result["success"]:
                self.logger.info(f"Successfully exported to {output_path}")

            return result

        except Exception as e:
            error_msg = f"Export failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def export_multiple(
        self,
        data_list: List[Dict[str, Any]],
        output_path: str,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export multiple character records to JSON file.

        Args:
            data_list: List of character data to export
            output_path: Output file path
            custom_config: Optional custom configuration

        Returns:
            Export result with status and metadata
        """
        if not data_list:
            return {"success": False, "error": "No data provided"}

        self.logger.info(f"Exporting {len(data_list)} records to {output_path}")

        try:
            # Apply configuration
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)

            # Process all records
            processed_records = []
            for record in data_list:
                processed_record = self._process_single_record(record, config)
                processed_records.append(processed_record)

            # Create export structure
            export_data = {
                "characters": processed_records,
                "count": len(processed_records),
            }

            # Add export metadata
            if config["output"]["include_metadata"]:
                export_data = self._add_export_metadata(export_data, "multiple")

            # Write to file
            result = self._write_json_file(export_data, output_path, config)

            if result["success"]:
                self.logger.info(
                    f"Successfully exported {len(data_list)} records to {output_path}"
                )

            return result

        except Exception as e:
            error_msg = f"Export failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def export_structured(
        self,
        data_list: List[Dict[str, Any]],
        output_path: str,
        group_by: str = "source",
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export data in structured format grouped by specified field.

        Args:
            data_list: List of character data to export
            output_path: Output file path
            group_by: Field to group records by
            custom_config: Optional custom configuration

        Returns:
            Export result with status and metadata
        """
        if not data_list:
            return {"success": False, "error": "No data provided"}

        self.logger.info(
            f"Exporting {len(data_list)} records grouped by '{group_by}' to {output_path}"
        )

        try:
            # Apply configuration
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)

            # Group data by specified field
            grouped_data = {}
            processed_count = 0

            for record in data_list:
                processed_record = self._process_single_record(record, config)
                group_value = str(processed_record.get(group_by, "unknown"))

                if group_value not in grouped_data:
                    grouped_data[group_value] = []

                grouped_data[group_value].append(processed_record)
                processed_count += 1

            # Create structured export
            export_data = {
                "grouped_by": group_by,
                "groups": grouped_data,
                "group_count": len(grouped_data),
                "total_records": processed_count,
            }

            # Add summary statistics
            export_data["statistics"] = self._calculate_group_statistics(grouped_data)

            # Add export metadata
            if config["output"]["include_metadata"]:
                export_data = self._add_export_metadata(export_data, "structured")

            # Write to file
            result = self._write_json_file(export_data, output_path, config)

            if result["success"]:
                self.logger.info(
                    f"Successfully exported structured data to {output_path}"
                )

            return result

        except Exception as e:
            error_msg = f"Structured export failed: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def export_compact(
        self, data: Union[Dict, List[Dict]], output_path: str
    ) -> Dict[str, Any]:
        """
        Export data in compact format (minimal whitespace).

        Args:
            data: Data to export
            output_path: Output file path

        Returns:
            Export result
        """
        compact_config = {
            "formatting": {"indent": None, "separators": (",", ":")},
            "output": {"include_metadata": False},
        }

        if isinstance(data, list):
            return self.export_multiple(data, output_path, compact_config)
        else:
            return self.export_single(data, output_path, compact_config)

    def export_pretty(
        self, data: Union[Dict, List[Dict]], output_path: str
    ) -> Dict[str, Any]:
        """
        Export data in pretty format (readable formatting).

        Args:
            data: Data to export
            output_path: Output file path

        Returns:
            Export result
        """
        pretty_config = {
            "formatting": {"indent": 4, "sort_keys": True},
            "output": {"include_metadata": True, "include_empty_fields": True},
        }

        if isinstance(data, list):
            return self.export_multiple(data, output_path, pretty_config)
        else:
            return self.export_single(data, output_path, pretty_config)

    def export_filtered(
        self,
        data: Union[Dict, List[Dict]],
        output_path: str,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Export data with specific field filtering.

        Args:
            data: Data to export
            output_path: Output file path
            include_fields: Fields to include (if specified, only these are included)
            exclude_fields: Fields to exclude

        Returns:
            Export result
        """
        filter_config = {
            "filters": {
                "include_only": include_fields,
                "exclude_fields": exclude_fields or [],
            }
        }

        if isinstance(data, list):
            return self.export_multiple(data, output_path, filter_config)
        else:
            return self.export_single(data, output_path, filter_config)

    def _process_single_record(
        self, record: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single record according to configuration."""
        processed = dict(record)

        # Apply field filters
        processed = self._apply_field_filters(processed, config["filters"])

        # Transform timestamps
        processed = self._transform_timestamps(
            processed, config["output"]["timestamp_format"]
        )

        # Remove empty fields if configured
        if not config["output"]["include_empty_fields"]:
            processed = self._remove_empty_fields(processed)

        # Remove private fields if configured
        if not config["output"]["include_private_fields"]:
            processed = self._remove_private_fields(processed)

        # Apply custom transformations
        processed = self._apply_transformations(
            processed, config["filters"].get("transform_functions", {})
        )

        return processed

    def _apply_field_filters(
        self, record: Dict[str, Any], filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply field inclusion/exclusion filters."""
        filtered = dict(record)

        # Include only specific fields if specified
        include_only = filters.get("include_only")
        if include_only:
            filtered = {k: v for k, v in filtered.items() if k in include_only}

        # Exclude specified fields
        exclude_fields = filters.get("exclude_fields", [])
        for field in exclude_fields:
            filtered.pop(field, None)

        return filtered

    def _transform_timestamps(
        self, record: Dict[str, Any], timestamp_format: str
    ) -> Dict[str, Any]:
        """Transform timestamp fields according to format."""
        transformed = dict(record)

        timestamp_fields = ["created_at", "updated_at", "scraped_at", "exported_at"]

        for field in timestamp_fields:
            if field in transformed and transformed[field]:
                try:
                    if timestamp_format == "iso":
                        # Ensure ISO format
                        if isinstance(transformed[field], datetime):
                            transformed[field] = transformed[field].isoformat()
                    elif timestamp_format == "unix":
                        # Convert to Unix timestamp
                        if isinstance(transformed[field], str):
                            dt = datetime.fromisoformat(
                                transformed[field].replace("Z", "+00:00")
                            )
                            transformed[field] = int(dt.timestamp())
                    elif timestamp_format == "readable":
                        # Convert to readable format
                        if isinstance(transformed[field], str):
                            dt = datetime.fromisoformat(
                                transformed[field].replace("Z", "+00:00")
                            )
                            transformed[field] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except Exception as e:
                    self.logger.warning(f"Failed to transform timestamp {field}: {e}")

        return transformed

    def _remove_empty_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Remove fields with empty values."""
        return {
            k: v
            for k, v in record.items()
            if v is not None and v != "" and v != [] and v != {}
        }

    def _remove_private_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Remove private fields (starting with underscore)."""
        return {k: v for k, v in record.items() if not k.startswith("_")}

    def _apply_transformations(
        self, record: Dict[str, Any], transformations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom field transformations."""
        transformed = dict(record)

        for field, transform_func in transformations.items():
            if field in transformed and callable(transform_func):
                try:
                    transformed[field] = transform_func(transformed[field])
                except Exception as e:
                    self.logger.warning(f"Transformation failed for field {field}: {e}")

        return transformed

    def _add_export_metadata(
        self, data: Dict[str, Any], export_type: str
    ) -> Dict[str, Any]:
        """Add export metadata to the data."""
        metadata = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "export_type": export_type,
                "exporter": "JSONExporter",
                "version": "1.0",
            }
        }

        # Add to existing data
        if isinstance(data, dict):
            result = dict(data)
            result["_metadata"] = metadata
            return result
        else:
            return {"data": data, "_metadata": metadata}

    def _calculate_group_statistics(
        self, grouped_data: Dict[str, List]
    ) -> Dict[str, Any]:
        """Calculate statistics for grouped data."""
        stats = {}

        for group_name, records in grouped_data.items():
            stats[group_name] = {
                "count": len(records),
                "percentage": 0,  # Will be calculated after all groups
            }

        # Calculate percentages
        total_records = sum(stat["count"] for stat in stats.values())
        for group_name, stat in stats.items():
            stat["percentage"] = (
                (stat["count"] / total_records) * 100 if total_records > 0 else 0
            )

        return stats

    def _write_json_file(
        self, data: Any, output_path: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Write data to JSON file with validation."""
        try:
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Prepare JSON serialization parameters
            json_params = config["formatting"].copy()
            json_params["ensure_ascii"] = config["formatting"]["ensure_ascii"]

            # Convert data to JSON string first for validation
            json_string = json.dumps(data, **json_params)

            # Validate JSON if configured
            if config["validation"]["validate_output"]:
                validation_result = self._validate_json_output(json_string, config)
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": f"Validation failed: {validation_result['errors']}",
                    }

            # Write to file
            encoding = config["output"]["encoding"]
            with open(output_path, "w", encoding=encoding) as f:
                f.write(json_string)

            # Get file statistics
            file_size = output_file.stat().st_size

            return {
                "success": True,
                "output_path": str(output_path),
                "encoding": encoding,
                "records_exported": self._count_records(data),
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to write JSON file: {e}"}

    def _validate_json_output(
        self, json_string: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate JSON output before writing."""
        errors = []

        # Check file size
        size_bytes = len(json_string.encode("utf-8"))
        max_size = config["validation"]["max_file_size"]
        if size_bytes > max_size:
            errors.append(
                f"Output size ({size_bytes} bytes) exceeds maximum ({max_size} bytes)"
            )

        # Validate JSON syntax
        if config["validation"]["check_json_validity"]:
            try:
                json.loads(json_string)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON syntax: {e}")

        return {"valid": len(errors) == 0, "errors": errors, "size_bytes": size_bytes}

    def _count_records(self, data: Any) -> int:
        """Count the number of records in the data."""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            if "characters" in data and isinstance(data["characters"], list):
                return len(data["characters"])
            elif "groups" in data and isinstance(data["groups"], dict):
                return sum(len(group) for group in data["groups"].values())
            else:
                return 1
        else:
            return 1


def create_json_export_config() -> Dict[str, Any]:
    """Create default configuration for JSON exporter."""
    return {
        "formatting": {
            "indent": 2,
            "ensure_ascii": False,
            "sort_keys": True,
            "separators": (",", ": "),
        },
        "output": {
            "include_metadata": True,
            "include_empty_fields": False,
            "include_private_fields": False,
            "timestamp_format": "iso",  # 'iso', 'unix', 'readable'
            "encoding": "utf-8",
        },
        "validation": {
            "validate_output": True,
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "check_json_validity": True,
        },
        "filters": {
            "exclude_fields": ["_id", "__v", "_rev"],
            "include_only": None,
            "transform_functions": {},
        },
    }
