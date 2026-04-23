"""
Async File Operations - File I/O Utilities

aiofiles ile async file okuma/yazma işlemleri.
Chunked processing ve file size validation içerir.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-1.4
"""

import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Union

import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)

# Default chunk size for large file processing (8KB)
DEFAULT_CHUNK_SIZE = 8192

# Maximum file size (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


async def read_file(
    file_path: Union[str, Path],
    encoding: str = "utf-8"
) -> str:
    """
    Async olarak dosya okur.
    
    Args:
        file_path: Dosya yolu
        encoding: Karakter encoding (default: utf-8)
        
    Returns:
        Dosya içeriği (string)
        
    Raises:
        FileNotFoundError: Dosya bulunamazsa
        ValueError: Dosya çok büyükse
        
    Example:
        content = await read_file("data.txt")
    """
    file_path = Path(file_path)

    # File size validation
    file_size = await aiofiles.os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE} bytes)"
        )

    logger.debug(f"Reading file: {file_path} ({file_size} bytes)")

    async with aiofiles.open(file_path, encoding=encoding) as f:
        content = await f.read()

    logger.debug(f"File read complete: {file_path}")
    return content


async def write_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> None:
    """
    Async olarak dosyaya yazar.
    
    Args:
        file_path: Dosya yolu
        content: Yazılacak içerik
        encoding: Karakter encoding (default: utf-8)
        create_dirs: Parent directory'leri oluştur (default: True)
        
    Example:
        await write_file("output.txt", "Hello, World!")
    """
    file_path = Path(file_path)

    # Create parent directories if needed
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {file_path.parent}")

    logger.debug(f"Writing file: {file_path} ({len(content)} chars)")

    async with aiofiles.open(file_path, mode="w", encoding=encoding) as f:
        await f.write(content)

    logger.debug(f"File write complete: {file_path}")


async def append_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8"
) -> None:
    """
    Async olarak dosyaya append eder.
    
    Args:
        file_path: Dosya yolu
        content: Eklenecek içerik
        encoding: Karakter encoding (default: utf-8)
        
    Example:
        await append_file("log.txt", "New log entry\\n")
    """
    file_path = Path(file_path)

    logger.debug(f"Appending to file: {file_path} ({len(content)} chars)")

    async with aiofiles.open(file_path, mode="a", encoding=encoding) as f:
        await f.write(content)

    logger.debug(f"File append complete: {file_path}")


async def read_file_chunked(
    file_path: Union[str, Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    encoding: str = "utf-8"
) -> AsyncGenerator[str, None]:
    """
    Büyük dosyaları chunk'lar halinde okur.
    
    Args:
        file_path: Dosya yolu
        chunk_size: Chunk boyutu (bytes, default: 8192)
        encoding: Karakter encoding (default: utf-8)
        
    Yields:
        Dosya chunk'ları (string)
        
    Example:
        async for chunk in read_file_chunked("large_file.txt"):
            process(chunk)
    """
    file_path = Path(file_path)

    file_size = await aiofiles.os.path.getsize(file_path)
    logger.debug(
        f"Reading file in chunks: {file_path} ({file_size} bytes, "
        f"chunk_size={chunk_size})"
    )

    async with aiofiles.open(file_path, encoding=encoding) as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk

    logger.debug(f"Chunked file read complete: {file_path}")


async def read_binary_file(file_path: Union[str, Path]) -> bytes:
    """
    Binary dosya okur.
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        Dosya içeriği (bytes)
        
    Raises:
        ValueError: Dosya çok büyükse
        
    Example:
        data = await read_binary_file("image.png")
    """
    file_path = Path(file_path)

    # File size validation
    file_size = await aiofiles.os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE} bytes)"
        )

    logger.debug(f"Reading binary file: {file_path} ({file_size} bytes)")

    async with aiofiles.open(file_path, mode="rb") as f:
        content = await f.read()

    logger.debug(f"Binary file read complete: {file_path}")
    return content


async def write_binary_file(
    file_path: Union[str, Path],
    content: bytes,
    create_dirs: bool = True
) -> None:
    """
    Binary dosya yazar.
    
    Args:
        file_path: Dosya yolu
        content: Yazılacak binary içerik
        create_dirs: Parent directory'leri oluştur (default: True)
        
    Example:
        await write_binary_file("output.bin", b"\\x00\\x01\\x02")
    """
    file_path = Path(file_path)

    # Create parent directories if needed
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {file_path.parent}")

    logger.debug(f"Writing binary file: {file_path} ({len(content)} bytes)")

    async with aiofiles.open(file_path, mode="wb") as f:
        await f.write(content)

    logger.debug(f"Binary file write complete: {file_path}")


async def read_binary_chunked(
    file_path: Union[str, Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> AsyncGenerator[bytes, None]:
    """
    Büyük binary dosyaları chunk'lar halinde okur.
    
    Args:
        file_path: Dosya yolu
        chunk_size: Chunk boyutu (bytes, default: 8192)
        
    Yields:
        Binary chunk'lar (bytes)
        
    Example:
        async for chunk in read_binary_chunked("large_file.bin"):
            process(chunk)
    """
    file_path = Path(file_path)

    file_size = await aiofiles.os.path.getsize(file_path)
    logger.debug(
        f"Reading binary file in chunks: {file_path} ({file_size} bytes, "
        f"chunk_size={chunk_size})"
    )

    async with aiofiles.open(file_path, mode="rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk

    logger.debug(f"Chunked binary file read complete: {file_path}")


async def file_exists(file_path: Union[str, Path]) -> bool:
    """
    Dosyanın var olup olmadığını kontrol eder.
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        True if file exists, False otherwise
        
    Example:
        if await file_exists("config.json"):
            config = await read_file("config.json")
    """
    return await aiofiles.os.path.exists(file_path)


async def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Dosya boyutunu döndürür.
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        Dosya boyutu (bytes)
        
    Example:
        size = await get_file_size("data.txt")
        print(f"File size: {size} bytes")
    """
    return await aiofiles.os.path.getsize(file_path)


async def delete_file(file_path: Union[str, Path]) -> None:
    """
    Dosyayı siler.
    
    Args:
        file_path: Dosya yolu
        
    Example:
        await delete_file("temp.txt")
    """
    file_path = Path(file_path)

    if await file_exists(file_path):
        await aiofiles.os.remove(file_path)
        logger.debug(f"File deleted: {file_path}")
    else:
        logger.warning(f"File not found for deletion: {file_path}")


async def copy_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> None:
    """
    Dosyayı async olarak kopyalar (chunked).
    
    Args:
        source: Kaynak dosya yolu
        destination: Hedef dosya yolu
        chunk_size: Chunk boyutu (bytes, default: 8192)
        
    Example:
        await copy_file("source.txt", "backup/source.txt")
    """
    source = Path(source)
    destination = Path(destination)

    # Create destination directory if needed
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)

    file_size = await get_file_size(source)
    logger.debug(f"Copying file: {source} -> {destination} ({file_size} bytes)")

    async with aiofiles.open(source, mode="rb") as src:
        async with aiofiles.open(destination, mode="wb") as dst:
            while True:
                chunk = await src.read(chunk_size)
                if not chunk:
                    break
                await dst.write(chunk)

    logger.debug(f"File copy complete: {source} -> {destination}")
