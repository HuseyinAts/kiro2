"""
Unit tests for `core.chroma_client` (env switching + embedded path).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.chroma_client import chromadb_connection_mode, create_chromadb_client


def test_chromadb_connection_mode_embedded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHROMADB_HOST", raising=False)
    assert chromadb_connection_mode() == "embedded"


def test_chromadb_connection_mode_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHROMADB_HOST", "chroma")
    assert chromadb_connection_mode() == "http"


def test_chromadb_connection_mode_whitespace_host_is_embedded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHROMADB_HOST", "   ")
    assert chromadb_connection_mode() == "embedded"


def test_create_chromadb_client_embedded_uses_persist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CHROMADB_HOST", raising=False)
    pd = str(tmp_path / "chroma_persist")
    Path(pd).mkdir(parents=True, exist_ok=True)
    client = create_chromadb_client(persist_directory=pd)
    assert client is not None
    assert hasattr(client, "list_collections") or hasattr(client, "heartbeat")
