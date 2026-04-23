"""
Async File Utilities - Asenkron Dosya Islemleri

aiofiles tabanli async dosya okuma/yazma islemleri.
Chunked processing ile buyuk dosyalar icin memory-efficient isleme.

Requirements:
    - REQ-1.4: Async file read/write with aiofiles
    - REQ-1.4: Chunked file processing (chunk_size=8192)
    - REQ-1.4: File size validation

Author: KIRO2 Team
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)

# Varsayilan chunk boyutu (8KB)
DEFAULT_CHUNK_SIZE: int = 8192

# Maksimum dosya boyutu (100MB)
MAX_FILE_SIZE: int = 100 * 1024 * 1024


@dataclass
class FileInfo:
    """
    Dosya bilgileri.

    Attributes:
        path: Dosya yolu
        size: Dosya boyutu (bytes)
        exists: Dosya mevcut mu
        is_file: Dosya mi (dizin degil)
        is_dir: Dizin mi
        extension: Dosya uzantisi
        name: Dosya adi
    """

    path: Path
    size: int = 0
    exists: bool = False
    is_file: bool = False
    is_dir: bool = False

    @property
    def extension(self) -> str:
        """Dosya uzantisi (.txt, .json vb.)."""
        return self.path.suffix.lower()

    @property
    def name(self) -> str:
        """Dosya adi (uzanti dahil)."""
        return self.path.name

    @property
    def stem(self) -> str:
        """Dosya adi (uzanti haric)."""
        return self.path.stem


async def get_file_info(path: str | Path) -> FileInfo:
    """
    Dosya bilgilerini async olarak al.

    Args:
        path: Dosya yolu

    Returns:
        FileInfo objesi
    """
    file_path = Path(path)

    try:
        stat = await aiofiles.os.stat(file_path)
        return FileInfo(
            path=file_path,
            size=stat.st_size,
            exists=True,
            is_file=not (stat.st_mode & 0o40000),  # S_IFDIR
            is_dir=bool(stat.st_mode & 0o40000),
        )
    except FileNotFoundError:
        return FileInfo(path=file_path, exists=False)
    except Exception as e:
        logger.error(f"Dosya bilgisi alinamadi: {path} - {e}")
        return FileInfo(path=file_path, exists=False)


async def validate_file_size(
    path: str | Path,
    max_size: int = MAX_FILE_SIZE,
) -> bool:
    """
    Dosya boyutunu dogrula.

    Args:
        path: Dosya yolu
        max_size: Maksimum boyut (bytes)

    Returns:
        True ise dosya boyutu gecerli

    Raises:
        FileNotFoundError: Dosya bulunamadi
        ValueError: Dosya boyutu limiti asdi
    """
    info = await get_file_info(path)

    if not info.exists:
        raise FileNotFoundError(f"Dosya bulunamadi: {path}")

    if info.size > max_size:
        raise ValueError(
            f"Dosya boyutu limiti asildi: {info.size} > {max_size} bytes"
        )

    return True


async def read_file(
    path: str | Path,
    encoding: str = "utf-8",
    max_size: int = MAX_FILE_SIZE,
) -> str:
    """
    Dosyayi async olarak oku.

    Args:
        path: Dosya yolu
        encoding: Karakter kodlamasi
        max_size: Maksimum dosya boyutu

    Returns:
        Dosya icerigi (string)

    Raises:
        FileNotFoundError: Dosya bulunamadi
        ValueError: Dosya boyutu limiti asdi
    """
    await validate_file_size(path, max_size)

    async with aiofiles.open(path, encoding=encoding) as f:
        content = await f.read()

    logger.debug(f"Dosya okundu: {path} ({len(content)} chars)")
    return content


async def read_file_bytes(
    path: str | Path,
    max_size: int = MAX_FILE_SIZE,
) -> bytes:
    """
    Dosyayi binary olarak oku.

    Args:
        path: Dosya yolu
        max_size: Maksimum dosya boyutu

    Returns:
        Dosya icerigi (bytes)
    """
    await validate_file_size(path, max_size)

    async with aiofiles.open(path, mode="rb") as f:
        content = await f.read()

    logger.debug(f"Dosya okundu (binary): {path} ({len(content)} bytes)")
    return content


async def read_file_chunks(
    path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_size: int = MAX_FILE_SIZE,
) -> AsyncGenerator[bytes, None]:
    """
    Dosyayi chunk'lar halinde oku.

    Buyuk dosyalar icin memory-efficient okuma.

    Args:
        path: Dosya yolu
        chunk_size: Chunk boyutu (bytes)
        max_size: Maksimum dosya boyutu

    Yields:
        Dosya chunk'lari (bytes)

    Example:
        >>> async for chunk in read_file_chunks("large_file.bin"):
        ...     process_chunk(chunk)
    """
    await validate_file_size(path, max_size)

    async with aiofiles.open(path, mode="rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk

    logger.debug(f"Dosya chunked okundu: {path}")


async def read_lines(
    path: str | Path,
    encoding: str = "utf-8",
    max_size: int = MAX_FILE_SIZE,
) -> AsyncGenerator[str, None]:
    """
    Dosyayi satirlar halinde oku.

    Args:
        path: Dosya yolu
        encoding: Karakter kodlamasi
        max_size: Maksimum dosya boyutu

    Yields:
        Dosya satirlari

    Example:
        >>> async for line in read_lines("data.txt"):
        ...     print(line)
    """
    await validate_file_size(path, max_size)

    async with aiofiles.open(path, encoding=encoding) as f:
        async for line in f:
            yield line.rstrip("\n\r")


async def write_file(
    path: str | Path,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> int:
    """
    Dosyaya async olarak yaz.

    Args:
        path: Dosya yolu
        content: Yazilacak icerik
        encoding: Karakter kodlamasi
        create_dirs: True ise dizinleri olustur

    Returns:
        Yazilan byte sayisi
    """
    file_path = Path(path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(file_path, mode="w", encoding=encoding) as f:
        bytes_written = await f.write(content)

    logger.debug(f"Dosya yazildi: {path} ({bytes_written} chars)")
    return bytes_written


async def write_file_bytes(
    path: str | Path,
    content: bytes,
    create_dirs: bool = True,
) -> int:
    """
    Dosyaya binary olarak yaz.

    Args:
        path: Dosya yolu
        content: Yazilacak icerik (bytes)
        create_dirs: True ise dizinleri olustur

    Returns:
        Yazilan byte sayisi
    """
    file_path = Path(path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(file_path, mode="wb") as f:
        bytes_written = await f.write(content)

    logger.debug(f"Dosya yazildi (binary): {path} ({bytes_written} bytes)")
    return bytes_written


async def append_file(
    path: str | Path,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> int:
    """
    Dosyanin sonuna ekle.

    Args:
        path: Dosya yolu
        content: Eklenecek icerik
        encoding: Karakter kodlamasi
        create_dirs: True ise dizinleri olustur

    Returns:
        Yazilan byte sayisi
    """
    file_path = Path(path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(file_path, mode="a", encoding=encoding) as f:
        bytes_written = await f.write(content)

    logger.debug(f"Dosyaya eklendi: {path} ({bytes_written} chars)")
    return bytes_written


async def copy_file(
    src: str | Path,
    dst: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    create_dirs: bool = True,
) -> int:
    """
    Dosyayi async olarak kopyala.

    Chunked copy ile buyuk dosyalar icin memory-efficient.

    Args:
        src: Kaynak dosya yolu
        dst: Hedef dosya yolu
        chunk_size: Chunk boyutu
        create_dirs: True ise hedef dizinleri olustur

    Returns:
        Kopyalanan byte sayisi
    """
    dst_path = Path(dst)

    if create_dirs:
        dst_path.parent.mkdir(parents=True, exist_ok=True)

    total_bytes = 0

    async with aiofiles.open(src, mode="rb") as src_file:
        async with aiofiles.open(dst_path, mode="wb") as dst_file:
            while True:
                chunk = await src_file.read(chunk_size)
                if not chunk:
                    break
                await dst_file.write(chunk)
                total_bytes += len(chunk)

    logger.debug(f"Dosya kopyalandi: {src} -> {dst} ({total_bytes} bytes)")
    return total_bytes


async def delete_file(path: str | Path) -> bool:
    """
    Dosyayi async olarak sil.

    Args:
        path: Dosya yolu

    Returns:
        True ise silme basarili
    """
    try:
        await aiofiles.os.remove(path)
        logger.debug(f"Dosya silindi: {path}")
        return True
    except FileNotFoundError:
        logger.warning(f"Silinecek dosya bulunamadi: {path}")
        return False
    except Exception as e:
        logger.error(f"Dosya silinemedi: {path} - {e}")
        return False


async def file_exists(path: str | Path) -> bool:
    """
    Dosya mevcut mu kontrol et.

    Args:
        path: Dosya yolu

    Returns:
        True ise dosya mevcut
    """
    info = await get_file_info(path)
    return info.exists and info.is_file


async def dir_exists(path: str | Path) -> bool:
    """
    Dizin mevcut mu kontrol et.

    Args:
        path: Dizin yolu

    Returns:
        True ise dizin mevcut
    """
    info = await get_file_info(path)
    return info.exists and info.is_dir


async def ensure_dir(path: str | Path) -> Path:
    """
    Dizin yoksa olustur.

    Args:
        path: Dizin yolu

    Returns:
        Dizin Path objesi
    """
    dir_path = Path(path)

    if not await dir_exists(dir_path):
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Dizin olusturuldu: {path}")

    return dir_path


async def list_files(
    path: str | Path,
    pattern: str = "*",
    recursive: bool = False,
) -> list[Path]:
    """
    Dizindeki dosyalari listele.

    Args:
        path: Dizin yolu
        pattern: Glob pattern (*.txt, *.json vb.)
        recursive: True ise alt dizinleri de tara

    Returns:
        Dosya Path listesi
    """
    dir_path = Path(path)

    if not await dir_exists(dir_path):
        return []

    if recursive:
        files = list(dir_path.rglob(pattern))
    else:
        files = list(dir_path.glob(pattern))

    # Sadece dosyalari filtrele
    return [f for f in files if f.is_file()]


async def read_json(
    path: str | Path,
    encoding: str = "utf-8",
) -> Any:
    """
    JSON dosyasi oku.

    Args:
        path: JSON dosya yolu
        encoding: Karakter kodlamasi

    Returns:
        Parsed JSON data
    """
    import json

    content = await read_file(path, encoding=encoding)
    return json.loads(content)


async def write_json(
    path: str | Path,
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False,
) -> int:
    """
    JSON dosyasi yaz.

    Args:
        path: JSON dosya yolu
        data: Yazilacak data
        encoding: Karakter kodlamasi
        indent: JSON indentation
        ensure_ascii: ASCII-only output

    Returns:
        Yazilan byte sayisi
    """
    import json

    content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    return await write_file(path, content, encoding=encoding)


__all__ = [
    "DEFAULT_CHUNK_SIZE",
    "MAX_FILE_SIZE",
    "FileInfo",
    "append_file",
    "copy_file",
    "delete_file",
    "dir_exists",
    "ensure_dir",
    "file_exists",
    "get_file_info",
    "list_files",
    "read_file",
    "read_file_bytes",
    "read_file_chunks",
    "read_json",
    "read_lines",
    "validate_file_size",
    "write_file",
    "write_file_bytes",
    "write_json",
]
