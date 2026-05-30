"""Beta pratik soru seçimi testleri.

Beta pratik modu, kör 3-solver gate'inden geçmiş (pipeline_metadata.
beta_clean_verified == 'true') 386 çekirdek soruyu kullanır. Standart ÖSYM
soru-seçim base_filters'ı (uzunluk>=50, passage regex, geometri-görsel şartı
vb.) bu mod için UYGULANMAZ — gate, o sezgisel proxy'lerden daha güçlü bir
kalite kanıtı sağlar (öğrenci-eşdeğeri kör çözüm).

Mock kullanılmaz: beta havuzu yalnızca prod DB'de (port 5434) bulunduğu için
testler gerçek DB'ye karşı çalışır; DB ulaşılamazsa skip eder (repo deseni).
"""

import pytest

from core.osym_exam_engine import OSYMExamEngine


async def _beta_pool_available() -> bool:
    """Gerçek DB erişilebilir ve beta havuzu dolu mu?"""
    try:
        from sqlalchemy import func, select

        from core.database import get_db_session_context
        from models.question_bank import QuestionBankItem as Question

        async with get_db_session_context() as db_session:
            result = await db_session.execute(
                select(func.count())
                .select_from(Question)
                .where(
                    Question.is_active.is_(True),
                    Question.pipeline_metadata.op("->>")("beta_clean_verified")
                    == "true",
                )
            )
            return (result.scalar() or 0) >= 20
    except Exception:
        return False


def _is_beta_clean(question) -> bool:
    meta = question.pipeline_metadata or {}
    # JSON boolean true veya string "true" — her iki serileştirmeyi de kabul et
    return meta.get("beta_clean_verified") in (True, "true")


@pytest.fixture(scope="module")
async def beta_pool_ready():
    if not await _beta_pool_available():
        pytest.skip("Beta clean havuzu (>=20) erişilemez — gerçek DB gerekli")
    return True


async def test_select_beta_questions_returns_requested_count(beta_pool_ready):
    """İstenen sayıda soru döndürür (havuz >= istenen)."""
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(20)
    assert len(questions) == 20


async def test_select_beta_questions_all_beta_clean(beta_pool_ready):
    """Dönen her soru beta_clean_verified ve aktif."""
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(20)
    assert questions, "Beta havuzundan soru gelmedi"
    for q in questions:
        assert q.is_active is True
        assert _is_beta_clean(q), f"Soru {q.id} beta_clean değil"


async def test_select_beta_questions_caps_at_pool_size(beta_pool_ready):
    """İstenen sayı havuzdan büyükse havuz boyutuyla sınırlanır (çökmez)."""
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(10_000)
    assert 0 < len(questions) <= 10_000
    # Tümü yine beta_clean olmalı
    assert all(_is_beta_clean(q) for q in questions)
