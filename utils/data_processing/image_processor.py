# utils/data_processing/image_processor.py
"""
Image processing utilities for character images.
Provides image optimization, validation, and metadata extraction.
"""

import logging
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import requests
from urllib.parse import urlparse


class ImageProcessor:
    """
    Comprehensive image processing engine for character images.

    Features:
    - Image download and validation
    - Format conversion and optimization
    - Metadata extraction
    - Duplicate detection
    - Thumbnail generation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize image processor.

        Args:
            config: Configuration dictionary with processing parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "download": {
                "timeout": 30,
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "user_agent": "Fandom-Scraper/1.0",
                "retry_attempts": 3,
                "retry_delay": 1.0,
            },
            "validation": {
                "allowed_formats": ["jpg", "jpeg", "png", "gif", "webp"],
                "min_width": 50,
                "min_height": 50,
                "max_width": 4000,
                "max_height": 4000,
                "max_file_size": 10 * 1024 * 1024,
            },
            "optimization": {
                "jpeg_quality": 85,
                "png_optimize": True,
                "strip_metadata": True,
                "convert_format": None,  # Auto-select best format
            },
            "thumbnails": {
                "sizes": [(150, 150), (300, 300)],
                "quality": 80,
                "format": "JPEG",
            },
            "storage": {
                "base_path": "storage/images",
                "structure": "{category}/{character_id}",
                "naming": "{hash}_{width}x{height}.{ext}",
            },
        }

        if config:
            self.config.update(config)

        # Try to import PIL for image processing
        self.pil_available = False
        try:
            from PIL import Image, ImageOps

            self.Image = Image
            self.ImageOps = ImageOps
            self.pil_available = True
            self.logger.info("PIL/Pillow available for image processing")
        except ImportError:
            self.logger.warning("PIL/Pillow not available - limited image processing")

    def process_image_url(
        self, url: str, character_id: str, category: str = "characters"
    ) -> Dict[str, Any]:
        """
        Download and process an image from URL.

        Args:
            url: Image URL to download
            character_id: Character identifier for storage
            category: Image category (characters, animes, episodes)

        Returns:
            Processing result with file paths and metadata
        """
        if not url:
            return {"success": False, "error": "Empty URL provided"}

        self.logger.info(f"Processing image URL: {url}")

        try:
            # Download image
            download_result = self._download_image(url)
            if not download_result["success"]:
                return download_result

            # Validate image
            validation_result = self._validate_image(download_result["content"])
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid image: {validation_result['errors']}",
                }

            # Generate file info
            file_info = self._generate_file_info(url, download_result["content"])

            # Save original image
            save_result = self._save_image(
                download_result["content"], character_id, category, file_info
            )

            if not save_result["success"]:
                return save_result

            result = {
                "success": True,
                "original_url": url,
                "file_path": save_result["file_path"],
                "file_size": len(download_result["content"]),
                "metadata": file_info,
                "validation": validation_result,
            }

            # Generate thumbnails if PIL is available
            if self.pil_available and save_result["file_path"]:
                thumbnail_result = self._generate_thumbnails(
                    save_result["file_path"], character_id, category
                )
                result["thumbnails"] = thumbnail_result

            return result

        except Exception as e:
            self.logger.error(f"Error processing image {url}: {e}")
            return {"success": False, "error": str(e)}

    def process_image_batch(
        self, image_urls: List[str], character_id: str, category: str = "characters"
    ) -> Dict[str, Any]:
        """
        Process multiple images for a character.

        Args:
            image_urls: List of image URLs
            character_id: Character identifier
            category: Image category

        Returns:
            Batch processing results
        """
        if not image_urls:
            return {
                "success": True,
                "results": [],
                "summary": {"total": 0, "successful": 0, "failed": 0},
            }

        self.logger.info(
            f"Processing {len(image_urls)} images for character {character_id}"
        )

        results = []
        successful = 0
        failed = 0

        for i, url in enumerate(image_urls):
            self.logger.debug(f"Processing image {i+1}/{len(image_urls)}: {url}")

            result = self.process_image_url(url, character_id, category)
            results.append(result)

            if result["success"]:
                successful += 1
            else:
                failed += 1
                self.logger.warning(
                    f"Failed to process {url}: {result.get('error', 'Unknown error')}"
                )

        summary = {
            "total": len(image_urls),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(image_urls)) * 100,
        }

        return {"success": True, "results": results, "summary": summary}

    def validate_image_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate an existing image file.

        Args:
            file_path: Path to image file

        Returns:
            Validation result
        """
        if not os.path.exists(file_path):
            return {"valid": False, "errors": ["File does not exist"]}

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            return self._validate_image(content)

        except Exception as e:
            return {"valid": False, "errors": [f"Error reading file: {e}"]}

    def get_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from image file.

        Args:
            file_path: Path to image file

        Returns:
            Image metadata
        """
        if not self.pil_available:
            return {"error": "PIL not available for metadata extraction"}

        try:
            with self.Image.open(file_path) as img:
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "has_transparency": img.mode in ("RGBA", "LA")
                    or "transparency" in img.info,
                }

                # Add EXIF data if available
                if hasattr(img, "_getexif") and img._getexif():
                    metadata["exif"] = dict(img._getexif())

                return metadata

        except Exception as e:
            return {"error": f"Error extracting metadata: {e}"}

    def optimize_image(
        self, input_path: str, output_path: str = None
    ) -> Dict[str, Any]:
        """
        Optimize image file size and quality.

        Args:
            input_path: Path to input image
            output_path: Path for optimized image (optional)

        Returns:
            Optimization result
        """
        if not self.pil_available:
            return {"success": False, "error": "PIL not available for optimization"}

        if not output_path:
            output_path = input_path

        try:
            with self.Image.open(input_path) as img:
                # Convert RGBA to RGB if saving as JPEG
                if img.mode == "RGBA" and output_path.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    # Create white background
                    background = self.Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(
                        img, mask=img.split()[-1] if img.mode == "RGBA" else None
                    )
                    img = background

                # Optimize based on format
                save_kwargs = {}

                if output_path.lower().endswith((".jpg", ".jpeg")):
                    save_kwargs.update(
                        {
                            "format": "JPEG",
                            "quality": self.config["optimization"]["jpeg_quality"],
                            "optimize": True,
                        }
                    )
                elif output_path.lower().endswith(".png"):
                    save_kwargs.update(
                        {
                            "format": "PNG",
                            "optimize": self.config["optimization"]["png_optimize"],
                        }
                    )

                # Strip metadata if configured
                if self.config["optimization"]["strip_metadata"]:
                    # Create new image without metadata
                    img_copy = img.copy()
                    img_copy.save(output_path, **save_kwargs)
                else:
                    img.save(output_path, **save_kwargs)

                # Calculate size reduction
                original_size = os.path.getsize(input_path)
                optimized_size = os.path.getsize(output_path)
                reduction = ((original_size - optimized_size) / original_size) * 100

                return {
                    "success": True,
                    "original_size": original_size,
                    "optimized_size": optimized_size,
                    "size_reduction": reduction,
                    "output_path": output_path,
                }

        except Exception as e:
            return {"success": False, "error": f"Optimization failed: {e}"}

    def detect_duplicate_images(self, image_paths: List[str]) -> List[List[str]]:
        """
        Detect duplicate images using hash comparison.

        Args:
            image_paths: List of image file paths

        Returns:
            List of duplicate groups
        """
        if not image_paths:
            return []

        self.logger.info(f"Detecting duplicates among {len(image_paths)} images")

        # Calculate hashes for all images
        hash_groups = {}

        for path in image_paths:
            if os.path.exists(path):
                try:
                    image_hash = self._calculate_image_hash(path)
                    if image_hash not in hash_groups:
                        hash_groups[image_hash] = []
                    hash_groups[image_hash].append(path)
                except Exception as e:
                    self.logger.warning(f"Error hashing {path}: {e}")

        # Find groups with multiple images
        duplicate_groups = [paths for paths in hash_groups.values() if len(paths) > 1]

        self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def _download_image(self, url: str) -> Dict[str, Any]:
        """Download image from URL with retries."""
        config = self.config["download"]

        headers = {
            "User-Agent": config["user_agent"],
            "Accept": "image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        for attempt in range(config["retry_attempts"]):
            try:
                response = requests.get(
                    url, headers=headers, timeout=config["timeout"], stream=True
                )
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("image/"):
                    return {
                        "success": False,
                        "error": f"Invalid content type: {content_type}",
                    }

                # Check content length
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > config["max_file_size"]:
                    return {"success": False, "error": "File too large"}

                # Download with size limit
                content = b""
                for chunk in response.iter_content(chunk_size=8192):
                    content += chunk
                    if len(content) > config["max_file_size"]:
                        return {
                            "success": False,
                            "error": "File too large during download",
                        }

                return {
                    "success": True,
                    "content": content,
                    "content_type": content_type,
                    "size": len(content),
                }

            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"Download attempt {attempt + 1} failed for {url}: {e}"
                )
                if attempt == config["retry_attempts"] - 1:
                    return {
                        "success": False,
                        "error": f'Download failed after {config["retry_attempts"]} attempts: {e}',
                    }

                # Wait before retry
                import time

                time.sleep(config["retry_delay"])

    def _validate_image(self, content: bytes) -> Dict[str, Any]:
        """Validate image content."""
        errors = []

        # Check minimum size
        if len(content) < 100:  # Very small files are likely invalid
            errors.append("File too small")

        # Check maximum size
        max_size = self.config["validation"]["max_file_size"]
        if len(content) > max_size:
            errors.append(f"File too large (max {max_size} bytes)")

        # Check image format if PIL is available
        if self.pil_available:
            try:
                from io import BytesIO

                with self.Image.open(BytesIO(content)) as img:
                    # Check format
                    if img.format and img.format.lower() not in [
                        f.upper() for f in self.config["validation"]["allowed_formats"]
                    ]:
                        errors.append(f"Unsupported format: {img.format}")

                    # Check dimensions
                    width, height = img.size
                    min_w, min_h = (
                        self.config["validation"]["min_width"],
                        self.config["validation"]["min_height"],
                    )
                    max_w, max_h = (
                        self.config["validation"]["max_width"],
                        self.config["validation"]["max_height"],
                    )

                    if width < min_w or height < min_h:
                        errors.append(
                            f"Image too small: {width}x{height} (min {min_w}x{min_h})"
                        )

                    if width > max_w or height > max_h:
                        errors.append(
                            f"Image too large: {width}x{height} (max {max_w}x{max_h})"
                        )

                    # Check if image is corrupted
                    img.verify()

            except Exception as e:
                errors.append(f"Invalid image format: {e}")
        else:
            # Basic validation without PIL
            # Check magic bytes for common formats
            if not self._check_image_magic_bytes(content):
                errors.append("Invalid image format (magic bytes)")

        return {"valid": len(errors) == 0, "errors": errors}

    def _check_image_magic_bytes(self, content: bytes) -> bool:
        """Check image magic bytes for format validation."""
        if len(content) < 12:
            return False

        # Common image format magic bytes
        magic_bytes = {
            b"\xff\xd8\xff": "jpeg",
            b"\x89PNG\r\n\x1a\n": "png",
            b"GIF87a": "gif",
            b"GIF89a": "gif",
            b"RIFF": "webp",  # WebP starts with RIFF
        }

        for magic, fmt in magic_bytes.items():
            if content.startswith(magic):
                return True

        return False

    def _generate_file_info(self, url: str, content: bytes) -> Dict[str, Any]:
        """Generate file information and metadata."""
        # Calculate content hash
        content_hash = hashlib.md5(content).hexdigest()

        # Parse URL for filename
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)

        # Detect format from content if PIL available
        image_format = None
        dimensions = None

        if self.pil_available:
            try:
                from io import BytesIO

                with self.Image.open(BytesIO(content)) as img:
                    image_format = img.format.lower() if img.format else None
                    dimensions = img.size
            except Exception:
                pass

        # Fallback format detection
        if not image_format:
            if content.startswith(b"\xff\xd8\xff"):
                image_format = "jpeg"
            elif content.startswith(b"\x89PNG"):
                image_format = "png"
            elif content.startswith(b"GIF"):
                image_format = "gif"
            elif b"WEBP" in content[:12]:
                image_format = "webp"

        return {
            "hash": content_hash,
            "original_url": url,
            "original_filename": original_filename,
            "format": image_format,
            "size_bytes": len(content),
            "dimensions": dimensions,
            "downloaded_at": datetime.now().isoformat(),
        }

    def _save_image(
        self,
        content: bytes,
        character_id: str,
        category: str,
        file_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save image to storage with organized structure."""
        try:
            # Generate storage path
            base_path = Path(self.config["storage"]["base_path"])

            # Create category/character directory structure
            structure = self.config["storage"]["structure"].format(
                category=category, character_id=character_id
            )
            save_dir = base_path / structure
            save_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            dimensions = file_info.get("dimensions", (0, 0))
            width, height = dimensions if dimensions else (0, 0)

            filename = self.config["storage"]["naming"].format(
                hash=file_info["hash"][:12],  # Use first 12 chars of hash
                width=width,
                height=height,
                ext=file_info.get("format", "jpg"),
            )

            file_path = save_dir / filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(content)

            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "directory": str(save_dir),
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to save image: {e}"}

    def _generate_thumbnails(
        self, image_path: str, character_id: str, category: str
    ) -> List[Dict[str, Any]]:
        """Generate thumbnails for an image."""
        if not self.pil_available:
            return []

        thumbnails = []

        try:
            with self.Image.open(image_path) as img:
                for size in self.config["thumbnails"]["sizes"]:
                    thumbnail_result = self._create_thumbnail(
                        img, size, image_path, character_id, category
                    )
                    if thumbnail_result["success"]:
                        thumbnails.append(thumbnail_result)

        except Exception as e:
            self.logger.error(f"Error generating thumbnails for {image_path}: {e}")

        return thumbnails

    def _create_thumbnail(
        self,
        img,
        size: Tuple[int, int],
        original_path: str,
        character_id: str,
        category: str,
    ) -> Dict[str, Any]:
        """Create a single thumbnail."""
        try:
            # Create thumbnail
            img_copy = img.copy()
            img_copy.thumbnail(size, self.Image.Resampling.LANCZOS)

            # Generate thumbnail path
            original_stem = Path(original_path).stem
            thumb_filename = f"{original_stem}_thumb_{size[0]}x{size[1]}.jpg"

            base_path = Path(self.config["storage"]["base_path"])
            structure = self.config["storage"]["structure"].format(
                category=category, character_id=character_id
            )
            thumb_dir = base_path / structure / "thumbnails"
            thumb_dir.mkdir(parents=True, exist_ok=True)

            thumb_path = thumb_dir / thumb_filename

            # Save thumbnail
            if img_copy.mode == "RGBA":
                # Convert to RGB with white background
                background = self.Image.new("RGB", img_copy.size, (255, 255, 255))
                background.paste(img_copy, mask=img_copy.split()[-1])
                img_copy = background

            img_copy.save(
                thumb_path,
                format=self.config["thumbnails"]["format"],
                quality=self.config["thumbnails"]["quality"],
                optimize=True,
            )

            return {
                "success": True,
                "size": size,
                "path": str(thumb_path),
                "file_size": os.path.getsize(thumb_path),
            }

        except Exception as e:
            return {"success": False, "error": f"Thumbnail creation failed: {e}"}

    def _calculate_image_hash(self, image_path: str) -> str:
        """Calculate hash for duplicate detection."""
        try:
            with open(image_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Error calculating hash for {image_path}: {e}")
            return ""


def create_image_processor_config() -> Dict[str, Any]:
    """Create default configuration for image processor."""
    return {
        "download": {
            "timeout": 30,
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "user_agent": "Fandom-Scraper/1.0",
            "retry_attempts": 3,
            "retry_delay": 1.0,
        },
        "validation": {
            "allowed_formats": ["jpg", "jpeg", "png", "gif", "webp"],
            "min_width": 50,
            "min_height": 50,
            "max_width": 4000,
            "max_height": 4000,
            "max_file_size": 10 * 1024 * 1024,
        },
        "optimization": {
            "jpeg_quality": 85,
            "png_optimize": True,
            "strip_metadata": True,
            "convert_format": None,
        },
        "thumbnails": {
            "sizes": [(150, 150), (300, 300)],
            "quality": 80,
            "format": "JPEG",
        },
        "storage": {
            "base_path": "storage/images",
            "structure": "{category}/{character_id}",
            "naming": "{hash}_{width}x{height}.{ext}",
        },
    }
