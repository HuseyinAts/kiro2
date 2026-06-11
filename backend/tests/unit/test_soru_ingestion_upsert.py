"""
Unit tests for SoruEkleRequest hashing and SoruBankasiServisi zero-crash upsert.
"""

import hashlib
import re
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

from api.soru_bankasi import SoruEkleRequest
from services.soru_bankasi_service import soru_bankasi_servisi
from models.question_bank import QuestionBankItem as Question
from models.question_bank import TopicHierarchy, QuestionDifficultyLevel
from core.database import db_manager


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    """Compile JSONB as JSON for SQLite dialect in tests."""
    return "JSON"



def test_soru_ekle_request_canonical_hash():
    """Verify that SoruEkleRequest cleans inputs and computes canonical SHA-256 hash sliced to 32 characters."""
    payload = {
        "soru_metni": "<p>2+2\u200b kaçtır?</p>",
        "secenekler": ["  a)  1  ", "b) 2", "c) 3", "d) 4"],
        "dogru_cevap": "D",
        "sinav_tipi": "TYT",
        "konu": "Matematik",
        "zorluk_seviyesi": "kolay",
    }
    
    req = SoruEkleRequest(**payload)
    
    # Expected inputs cleaned:
    # question: "2+2 kaçtır?"
    # options: "1", "2", "3", "4"
    # hash_input: "2+2 kaçtır?|1|2|3|4|"
    expected_hash_input = "2+2 kaçtır?|1|2|3|4|"
    expected_hash = hashlib.sha256(expected_hash_input.encode('utf-8')).hexdigest()[:32]
    
    assert req.soru_hash == expected_hash
    assert len(req.soru_hash) == 32


@pytest.mark.asyncio
async def test_soru_ekle_upsert_fallback(db_session: AsyncSession):
    """Verify that inserting a duplicate question rolls back and gracefully returns the existing question."""
    # Seed the TopicHierarchy first so validation passes
    topic = TopicHierarchy(
        id="t-001",
        subject_area="MATEMATIK",
        name_tr="Matematik",
        name_en="Mathematics",
        code="MAT",
        level=1,
        is_active=True
    )
    db_session.add(topic)
    await db_session.commit()
    
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def mock_get_session():
        yield db_session

    # Patch db_manager's session manager so the service uses our test database session
    with patch.object(db_manager, "get_session", side_effect=mock_get_session):
        payload = {
            "soru_metni": "Unique question text here",
            "secenekler": ["Secenek A", "Secenek B", "Secenek C", "Secenek D"],
            "dogru_cevap": "A",
            "sinav_tipi": "TYT",
            "konu": "Matematik",
            "zorluk_seviyesi": "orta",
            "created_by": None
        }
        
        # Ingestion 1: First insert (should succeed)
        req1 = SoruEkleRequest(**payload)
        soru_data1 = payload.copy()
        soru_data1["soru_hash"] = req1.soru_hash
        
        yeni_soru1 = await soru_bankasi_servisi.soru_ekle(soru_data1)
        assert yeni_soru1 is not None
        assert yeni_soru1.question_text == "Unique question text here"
        assert yeni_soru1.soru_hash == req1.soru_hash
        
        # Ingestion 2: Duplicate insert (should catch IntegrityError, rollback, and return first)
        yeni_soru2 = await soru_bankasi_servisi.soru_ekle(soru_data1)
        assert yeni_soru2 is not None
        assert yeni_soru2.id == yeni_soru1.id
        assert yeni_soru2.soru_hash == yeni_soru1.soru_hash
