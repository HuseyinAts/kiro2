#!/usr/bin/env python3
"""
Download Zemberek JAR file from Maven Central

Usage:
    python scripts/download_zemberek_jar.py
    python scripts/download_zemberek_jar.py --version 0.17.1
    python scripts/download_zemberek_jar.py --output /path/to/lib
"""

import argparse
import hashlib
import logging
import sys
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Maven Central base URL
MAVEN_BASE = "https://repo1.maven.org/maven2"

# Known Zemberek versions with SHA256 hashes
ZEMBEREK_VERSIONS = {
    "0.17.1": {
        "url": f"{MAVEN_BASE}/zemberek-nlp/zemberek-full/0.17.1/zemberek-full-0.17.1.jar",
        "sha256": None,  # Will verify download success only
        "size_mb": 150,  # Approximate size
    },
    "0.18.0": {
        "url": f"{MAVEN_BASE}/zemberek-nlp/zemberek-full/0.18.0/zemberek-full-0.18.0.jar",
        "sha256": None,
        "size_mb": 155,
    },
}

DEFAULT_VERSION = "0.17.1"


def get_default_output_dir() -> Path:
    """Get default output directory"""
    script_dir = Path(__file__).parent.parent
    lib_dir = script_dir / "lib" / "zemberek"
    lib_dir.mkdir(parents=True, exist_ok=True)
    return lib_dir


def download_with_progress(url: str, output_path: Path, expected_size_mb: int = 0) -> bool:
    """
    Download file with progress indicator

    Args:
        url: URL to download from
        output_path: Path to save file
        expected_size_mb: Expected file size in MB (for progress)

    Returns:
        True if download successful
    """
    logger.info(f"Downloading from: {url}")
    logger.info(f"Saving to: {output_path}")

    try:
        # Get file info
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get("content-length", 0))

            if total_size == 0 and expected_size_mb > 0:
                total_size = expected_size_mb * 1024 * 1024

            # Download in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            downloaded = 0

            with open(output_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    f.write(chunk)
                    downloaded += len(chunk)

                    # Progress
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(
                            f"\rProgress: {mb_downloaded:.1f}MB / {mb_total:.1f}MB ({percent:.1f}%)",
                            end="",
                            flush=True,
                        )
                    else:
                        mb_downloaded = downloaded / (1024 * 1024)
                        print(f"\rDownloaded: {mb_downloaded:.1f}MB", end="", flush=True)

            print()  # New line after progress
            logger.info(f"Download complete: {downloaded / (1024 * 1024):.1f}MB")
            return True

    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"URL error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False


def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    """Verify file SHA256 hash"""
    if expected_hash is None:
        logger.info("No SHA256 hash provided, skipping verification")
        return True

    logger.info("Verifying SHA256 hash...")
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    actual_hash = sha256.hexdigest()

    if actual_hash == expected_hash:
        logger.info("SHA256 hash verified successfully")
        return True
    logger.error("SHA256 mismatch!")
    logger.error(f"Expected: {expected_hash}")
    logger.error(f"Actual:   {actual_hash}")
    return False


def verify_jar(file_path: Path) -> bool:
    """Verify JAR file is valid"""
    import zipfile

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # Check for Zemberek classes
            namelist = zf.namelist()

            required_paths = [
                "zemberek/",
                "zemberek/morphology/",
            ]

            for required in required_paths:
                if not any(name.startswith(required) for name in namelist):
                    logger.error(f"JAR missing required path: {required}")
                    return False

            logger.info(f"JAR contains {len(namelist)} entries")
            logger.info("JAR structure verified successfully")
            return True

    except zipfile.BadZipFile:
        logger.error("File is not a valid JAR/ZIP archive")
        return False
    except Exception as e:
        logger.error(f"JAR verification error: {e}")
        return False


def download_zemberek(
    version: str = DEFAULT_VERSION,
    output_dir: Path = None,
    force: bool = False,
) -> Path:
    """
    Download Zemberek JAR file

    Args:
        version: Zemberek version to download
        output_dir: Output directory (default: backend/lib/zemberek)
        force: Force re-download even if file exists

    Returns:
        Path to downloaded JAR file

    Raises:
        ValueError: If version not found
        RuntimeError: If download or verification fails
    """
    if version not in ZEMBEREK_VERSIONS:
        raise ValueError(
            f"Unknown version: {version}. "
            f"Available versions: {list(ZEMBEREK_VERSIONS.keys())}"
        )

    version_info = ZEMBEREK_VERSIONS[version]
    output_dir = output_dir or get_default_output_dir()
    output_path = output_dir / f"zemberek-full-{version}.jar"

    # Check existing file
    if output_path.exists() and not force:
        logger.info(f"JAR already exists: {output_path}")

        if verify_jar(output_path):
            logger.info("Existing JAR is valid")
            return output_path
        logger.warning("Existing JAR is invalid, re-downloading...")

    # Download
    if not download_with_progress(
        version_info["url"],
        output_path,
        version_info.get("size_mb", 0),
    ):
        raise RuntimeError("Download failed")

    # Verify hash
    if not verify_sha256(output_path, version_info.get("sha256")):
        output_path.unlink()  # Delete invalid file
        raise RuntimeError("Hash verification failed")

    # Verify JAR structure
    if not verify_jar(output_path):
        output_path.unlink()
        raise RuntimeError("JAR verification failed")

    # Create symlink for convenience
    symlink_path = output_dir / "zemberek-full.jar"
    if symlink_path.exists():
        symlink_path.unlink()

    try:
        symlink_path.symlink_to(output_path.name)
        logger.info(f"Created symlink: {symlink_path}")
    except OSError:
        # Symlinks may not work on Windows without admin
        logger.warning("Could not create symlink (may require admin on Windows)")

    logger.info(f"Zemberek {version} downloaded successfully to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Download Zemberek JAR from Maven Central"
    )
    parser.add_argument(
        "--version",
        "-v",
        default=DEFAULT_VERSION,
        choices=list(ZEMBEREK_VERSIONS.keys()),
        help=f"Zemberek version (default: {DEFAULT_VERSION})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output directory (default: backend/lib/zemberek)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-download even if file exists",
    )
    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List available versions",
    )

    args = parser.parse_args()

    if args.list_versions:
        print("Available Zemberek versions:")
        for ver in ZEMBEREK_VERSIONS:
            print(f"  - {ver}")
        return 0

    try:
        jar_path = download_zemberek(
            version=args.version,
            output_dir=args.output,
            force=args.force,
        )
        print(f"\nSuccess! JAR path: {jar_path}")
        print("\nSet environment variable:")
        print(f"  export ZEMBEREK_JAR_PATH={jar_path}")
        return 0

    except Exception as e:
        logger.error(f"Failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
