"""
File Upload Security & Validation
SECURITY FIX: Prevent malicious file uploads
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from .structured_logger import get_logger

logger = get_logger("file_upload_security")


@dataclass
class FileValidationConfig:
    """File upload validation configuration"""

    allowed_extensions: set[str]
    allowed_mime_types: set[str]
    max_file_size: int  # bytes
    check_magic_bytes: bool = True
    sanitize_filename: bool = True
    scan_for_malware: bool = False  # Future: integrate with antivirus


# Magic bytes for common file types
MAGIC_BYTES = {
    # Images
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"],
    "gif": [b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61"],
    "webp": [b"\x52\x49\x46\x46", b"\x57\x45\x42\x50"],
    # Documents
    "pdf": [b"\x25\x50\x44\x46"],
    "doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    "docx": [b"\x50\x4b\x03\x04", b"\x50\x4b\x05\x06", b"\x50\x4b\x07\x08"],
    "xls": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    "xlsx": [b"\x50\x4b\x03\x04", b"\x50\x4b\x05\x06", b"\x50\x4b\x07\x08"],
    # Archives
    "zip": [b"\x50\x4b\x03\x04", b"\x50\x4b\x05\x06", b"\x50\x4b\x07\x08"],
    "rar": [b"\x52\x61\x72\x21\x1a\x07"],
    "7z": [b"\x37\x7a\xbc\xaf\x27\x1c"],
    # Video/Audio
    "mp4": [b"\x00\x00\x00\x18\x66\x74\x79\x70", b"\x00\x00\x00\x20\x66\x74\x79\x70"],
    "mp3": [b"\x49\x44\x33", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "wav": [b"\x52\x49\x46\x46"],
}


class FileUploadValidator:
    """
    File upload security validator

    Features:
    - File type whitelist
    - MIME type validation
    - File size limits
    - Magic bytes verification
    - Filename sanitization
    - Duplicate detection
    """

    # Dangerous extensions (always blocked)
    DANGEROUS_EXTENSIONS = {
        "exe",
        "bat",
        "cmd",
        "com",
        "pif",
        "scr",
        "vbs",
        "js",
        "jar",
        "msi",
        "dll",
        "sys",
        "drv",
        "sh",
        "bash",
        "ps1",
        "app",
        "deb",
        "rpm",
    }

    # Default allowed configuration (restrictive)
    DEFAULT_CONFIG = FileValidationConfig(
        allowed_extensions={"pdf", "jpg", "jpeg", "png"},
        allowed_mime_types={
            "application/pdf",
            "image/jpeg",
            "image/png",
        },
        max_file_size=10 * 1024 * 1024,  # 10MB
        check_magic_bytes=True,
        sanitize_filename=True,
    )

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and injection

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path separators and null bytes
        filename = filename.replace("/", "").replace("\\", "").replace("\x00", "")

        # Remove leading dots (hidden files)
        filename = filename.lstrip(".")

        # Replace spaces and special chars with underscores
        filename = re.sub(r"[^\w\s\-\.]", "_", filename)

        # Remove multiple dots (except before extension)
        parts = filename.rsplit(".", 1)
        if len(parts) == 2:
            name, ext = parts
            name = name.replace(".", "_")
            filename = f"{name}.{ext}"

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            max_name_len = 255 - len(ext) - 1
            filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]

        return filename

    @classmethod
    def get_file_extension(cls, filename: str) -> str:
        """Get file extension (lowercase)"""
        return Path(filename).suffix.lower().lstrip(".")

    @classmethod
    def validate_extension(cls, filename: str, config: FileValidationConfig) -> str:
        """
        Validate file extension

        Args:
            filename: Filename to validate
            config: Validation configuration

        Returns:
            Extension

        Raises:
            HTTPException: If extension not allowed
        """
        ext = cls.get_file_extension(filename)

        # Check dangerous extensions
        if ext in cls.DANGEROUS_EXTENSIONS:
            logger.error(
                f"Dangerous file extension blocked: {ext}",
                extra_data={"filename": filename, "extension": ext},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{ext}' is not allowed for security reasons",
            )

        # Check whitelist
        if ext not in config.allowed_extensions:
            logger.warning(
                f"File extension not in whitelist: {ext}",
                extra_data={"filename": filename, "extension": ext},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{ext}' is not allowed. Allowed types: {', '.join(config.allowed_extensions)}",
            )

        return ext

    @classmethod
    def validate_mime_type(cls, file: UploadFile, config: FileValidationConfig) -> str:
        """
        Validate MIME type

        Args:
            file: Uploaded file
            config: Validation configuration

        Returns:
            MIME type

        Raises:
            HTTPException: If MIME type not allowed
        """
        mime_type = file.content_type

        if mime_type not in config.allowed_mime_types:
            logger.warning(
                f"MIME type not allowed: {mime_type}",
                extra_data={"filename": file.filename, "mime_type": mime_type},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File MIME type '{mime_type}' is not allowed",
            )

        return mime_type

    @classmethod
    async def validate_file_size(
        cls, file: UploadFile, config: FileValidationConfig
    ) -> int:
        """
        Validate file size

        Args:
            file: Uploaded file
            config: Validation configuration

        Returns:
            File size in bytes

        Raises:
            HTTPException: If file too large
        """
        # Read file to get size
        contents = await file.read()
        file_size = len(contents)

        # Reset file pointer
        await file.seek(0)

        if file_size > config.max_file_size:
            max_mb = config.max_file_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            logger.warning(
                "File size exceeds limit",
                extra_data={
                    "filename": file.filename,
                    "size_mb": actual_mb,
                    "max_mb": max_mb,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({actual_mb:.2f}MB) exceeds maximum allowed size ({max_mb:.2f}MB)",
            )

        return file_size

    @classmethod
    async def validate_magic_bytes(cls, file: UploadFile, extension: str) -> bool:
        """
        Validate file magic bytes (file signature)

        Args:
            file: Uploaded file
            extension: Expected extension

        Returns:
            True if valid

        Raises:
            HTTPException: If magic bytes don't match
        """
        # Read first 32 bytes for magic byte check
        magic = await file.read(32)
        await file.seek(0)

        # Get expected magic bytes for this extension
        expected_magics = MAGIC_BYTES.get(extension, [])

        if not expected_magics:
            # No magic bytes defined for this extension, skip check
            return True

        # Check if file starts with any of the expected magic bytes
        for expected in expected_magics:
            if magic.startswith(expected):
                return True

        logger.error(
            "Magic bytes mismatch - possible file type spoofing",
            extra_data={
                "filename": file.filename,
                "extension": extension,
                "magic_bytes": magic[:16].hex(),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content does not match extension '{extension}'. Possible file type spoofing.",
        )

    @classmethod
    async def validate_upload(
        cls, file: UploadFile, config: FileValidationConfig = None
    ) -> tuple[str, int, str]:
        """
        Complete file upload validation

        Args:
            file: Uploaded file
            config: Validation configuration (uses DEFAULT_CONFIG if None)

        Returns:
            (sanitized_filename, file_size, extension)

        Raises:
            HTTPException: If validation fails
        """
        config = config or cls.DEFAULT_CONFIG

        # 1. Sanitize filename
        original_filename = file.filename or "unnamed"
        sanitized_filename = (
            cls.sanitize_filename(original_filename)
            if config.sanitize_filename
            else original_filename
        )

        logger.info(
            "File upload validation started",
            extra_data={
                "original_filename": original_filename,
                "sanitized_filename": sanitized_filename,
            },
        )

        # 2. Validate extension
        extension = cls.validate_extension(sanitized_filename, config)

        # 3. Validate MIME type
        mime_type = cls.validate_mime_type(file, config)

        # 4. Validate file size
        file_size = await cls.validate_file_size(file, config)

        # 5. Validate magic bytes
        if config.check_magic_bytes:
            await cls.validate_magic_bytes(file, extension)

        logger.info(
            "File upload validation passed",
            extra_data={
                "filename": sanitized_filename,
                "extension": extension,
                "mime_type": mime_type,
                "size_bytes": file_size,
            },
        )

        return sanitized_filename, file_size, extension

    @classmethod
    def generate_safe_filename(
        cls, original_filename: str, user_id: str | None = None
    ) -> str:
        """
        Generate safe filename with hash

        Args:
            original_filename: Original filename
            user_id: User ID (optional)

        Returns:
            Safe filename with timestamp and hash
        """
        import time

        sanitized = cls.sanitize_filename(original_filename)
        name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")

        # Create unique hash
        timestamp = str(int(time.time()))
        hash_input = f"{original_filename}{timestamp}{user_id or ''}".encode()
        file_hash = hashlib.md5(hash_input, usedforsecurity=False).hexdigest()[:8]

        # Generate safe filename
        safe_name = f"{name}_{timestamp}_{file_hash}"
        if ext:
            safe_name = f"{safe_name}.{ext}"

        return safe_name


# Predefined configurations
IMAGE_UPLOAD_CONFIG = FileValidationConfig(
    allowed_extensions={"jpg", "jpeg", "png", "gif", "webp"},
    allowed_mime_types={"image/jpeg", "image/png", "image/gif", "image/webp"},
    max_file_size=5 * 1024 * 1024,  # 5MB
    check_magic_bytes=True,
    sanitize_filename=True,
)

DOCUMENT_UPLOAD_CONFIG = FileValidationConfig(
    allowed_extensions={"pdf", "doc", "docx"},
    allowed_mime_types={
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    max_file_size=10 * 1024 * 1024,  # 10MB
    check_magic_bytes=True,
    sanitize_filename=True,
)

PROFILE_PICTURE_CONFIG = FileValidationConfig(
    allowed_extensions={"jpg", "jpeg", "png"},
    allowed_mime_types={"image/jpeg", "image/png"},
    max_file_size=2 * 1024 * 1024,  # 2MB
    check_magic_bytes=True,
    sanitize_filename=True,
)


# Helper function for route usage
async def validate_file_upload(
    file: UploadFile, config: FileValidationConfig = None
) -> tuple[str, int, str]:
    """
    Validate file upload (convenience function)

    Usage in route:
        @router.post("/upload")
        async def upload_file(file: UploadFile = File(...)):
            filename, size, ext = await validate_file_upload(file, IMAGE_UPLOAD_CONFIG)
            # Save file...
    """
    return await FileUploadValidator.validate_upload(file, config)
