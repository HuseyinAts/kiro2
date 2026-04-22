#!/usr/bin/env python3
"""
F1 minimum ingest: kiro2_questions koleksiyonuna birkaç kayıt (embedding + metin).

API ile aynı yolu kullanır: core.chroma_client + services.embedding_service.
Çalıştır: repo kökünden değil ``backend/`` altından (``cd backend``).

    cd backend
    python scripts/chroma_seed_kiro2_questions.py

Konteyner:

    docker exec -w /app kiro2-backend python scripts/chroma_seed_kiro2_questions.py

``kiro2-seed-*`` id'leri idempotent upsert; tekrar koşmak güvenli.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _setup_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.chdir(root)
    return root


def main() -> None:
    _setup_path()
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None
    if load_dotenv:
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    from core.chroma_client import create_chromadb_client
    from services.embedding_service import get_embedding_service

    persist = os.environ.get("CHROMADB_PERSIST_DIR", "./vector_db")
    client = create_chromadb_client(persist_directory=persist)
    coll = client.get_or_create_collection(
        name="kiro2_questions",
        metadata={"hnsw:space": "cosine"},
    )
    emb = get_embedding_service()

    seeds: list[tuple[str, str, dict]] = [
        (
            "kiro2-seed-tyt-mat-001",
            (
                "TYT Matematik: Bir f(x) fonksiyonunun belirli integralini [a,b] "
                "aralığında hesaplayınız."
            ),
            {
                "subject": "MATEMATIK",
                "exam_type": "TYT",
                "difficulty": 0.0,
                "seed": "1",
            },
        ),
        (
            "kiro2-seed-tyt-tur-001",
            "Türkçe paragraf: Ana fikir ve yardımcı fikirleri ayırt ediniz.",
            {
                "subject": "TURKCE",
                "exam_type": "TYT",
                "difficulty": 0.0,
                "seed": "1",
            },
        ),
    ]
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []
    embeddings: list[list[float]] = []
    for doc_id, text, meta in seeds:
        ids.append(doc_id)
        docs.append(text)
        metas.append(meta)
        embeddings.append(emb.embed(text))

    coll.upsert(
        ids=ids,
        documents=docs,
        metadatas=metas,
        embeddings=embeddings,
    )
    n = coll.count()
    print(f"chroma_seed_kiro2_questions: upserted {len(ids)} ids, collection count={n}")


if __name__ == "__main__":
    main()
