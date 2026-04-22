"""
ChromaDB client factory: embedded persist vs. remote HttpClient.

Env:
  CHROMADB_HOST — Uzak Chroma (ör. ``chroma`` servisi); boşsa embedded Client.
  CHROMADB_PORT — Varsayılan 8000.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def chromadb_connection_mode() -> str:
    """``http`` veya ``embedded`` (health / log için)."""
    return "http" if (os.environ.get("CHROMADB_HOST") or "").strip() else "embedded"


def create_chromadb_client(*, persist_directory: str) -> Any:
    """
    Chroma client döndür. ``CHROMADB_HOST`` set ise ``HttpClient``, aksi halde
    yerel ``chromadb.Client`` (persist).
    """
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    host = (os.environ.get("CHROMADB_HOST") or "").strip()
    if host:
        port_raw = (os.environ.get("CHROMADB_PORT") or "8000").strip()
        try:
            port = int(port_raw)
        except ValueError:
            port = 8000
        try:
            client = chromadb.HttpClient(host=host, port=port)
            logger.info("ChromaDB HttpClient: %s:%s", host, port)
            return client
        except Exception as exc:
            logger.warning(
                "ChromaDB HttpClient failed for %s:%s (%s); using embedded",
                host,
                port,
                exc,
            )

    return chromadb.Client(
        ChromaSettings(
            persist_directory=persist_directory,
            anonymized_telemetry=False,
        )
    )
