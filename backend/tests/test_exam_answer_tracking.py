# -*- coding: utf-8 -*-
"""
Sınav Cevap Takip Testleri
Türkiye Üniversite Sınavları Hazırlık Platformu

Task 69.2: Boş bırakma testleri
- Cevaplanmayan soru takibi
- Boş cevap işleme
- Tamamlanma yüzdesi hesaplama

REQ-1.6: Sınav arayüzü gereksinimleri
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import (
    ExamSession,
    ExamQuestion,
    StudentAnswer,
    StudentProfile,
    User,
    UserRole,
    ExamType,
)
from services.exam_answer_tracking_service import (
    ExamAnswerTrackingService,
    create_answer_tracking_service,
)


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Test kullanıcısı oluştur"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_student(db_session: AsyncSession, test_user):
    """Test öğrenci profili oluştur"""
    student = StudentProfile(user_id=test_user.id, grade_level=12)
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student


@pytest.fixture
async def test_exam_session(db_session: AsyncSession, test_student):
    """Test sınav oturumu oluştur"""
    exam_session = ExamSession(
        student_id=test_student.id,
        exam_type=ExamType.TYT,
        exam_name="Test TYT Denemesi",
        total_questions=120,
        duration_minutes=135,
        status="in_progress",
    )
    db_session.add(exam_session)
    await db_session.commit()
    await db_session.refresh(exam_session)
    return exam_session


@pytest.fixture
async def test_exam_questions(db_session: AsyncSession, test_exam_session):
    """Test sınav soruları oluştur"""
    from models.database import Question, SubjectArea, QuestionDifficulty

    questions = []
    exam_questions = []

    for i in range(10):  # 10 soruluk küçük test sınavı
        # Soru oluştur
        question = Question(
            question_text=f"Test sorusu {i+1}",
            option_a="A şıkkı",
            option_b="B şıkkı",
            option_c="C şıkkı",
            option_d="D şıkkı",
            correct_answer="A",
            exam_type=ExamType.TYT,
            subject_area=SubjectArea.MATEMATIK,
            topic="Test Konusu",
            difficulty=QuestionDifficulty.MEDIUM,
        )
        db_session.add(question)
        questions.append(question)

    await db_session.commit()

    # Sınav-soru ilişkileri oluştur
    for i, question in enumerate(questions):
        await db_session.refresh(question)
        exam_question = ExamQuestion(
            exam_session_id=test_exam_session.id,
            question_id=question.id,
            question_order=i + 1,
        )
        db_session.add(exam_question)
        exam_questions.append(exam_question)

    await db_session.commit()

    # Sınav oturumunu güncelle
    test_exam_session.total_questions = len(questions)
    await db_session.commit()

    return exam_questions


@pytest.mark.asyncio
async def test_get_completion_stats_empty_exam(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Hiç cevap verilmemiş sınav için tamamlanma istatistikleri

    REQ-1.6: Tamamlanma yüzdesi hesaplama
    """
    service = await create_answer_tracking_service(db_session)

    stats = await service.get_completion_stats(test_exam_session.id)

    assert stats.total_questions == 10
    assert stats.answered_questions == 0
    assert stats.unanswered_questions == 10
    assert stats.empty_answers == 0
    assert stats.completion_percentage == 0.0
    assert len(stats.unanswered_question_ids) == 10
    assert len(stats.unanswered_question_orders) == 10


@pytest.mark.asyncio
async def test_get_completion_stats_partial_answers(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Kısmen cevaplandırılmış sınav için tamamlanma istatistikleri

    REQ-1.6: Tamamlanma yüzdesi hesaplama
    """
    # İlk 5 soruya cevap ver (3 dolu, 2 boş)
    for i in range(5):
        answer = StudentAnswer(
            exam_session_id=test_exam_session.id,
            question_id=test_exam_questions[i].question_id,
            selected_answer="A" if i < 3 else None,  # İlk 3 dolu, son 2 boş
            is_correct=True if i < 3 else None,
            response_time_seconds=30.0,
        )
        db_session.add(answer)

    await db_session.commit()

    service = await create_answer_tracking_service(db_session)
    stats = await service.get_completion_stats(test_exam_session.id)

    assert stats.total_questions == 10
    assert stats.answered_questions == 3  # Sadece dolu cevaplar
    assert stats.unanswered_questions == 5  # Hiç dokunulmamış
    assert stats.empty_answers == 2  # Boş bırakılan
    assert stats.completion_percentage == 50.0  # 5/10 = %50
    assert len(stats.unanswered_question_ids) == 5
    assert len(stats.unanswered_question_orders) == 5


@pytest.mark.asyncio
async def test_get_completion_stats_all_answered(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Tüm sorular cevaplandırılmış sınav için tamamlanma istatistikleri

    REQ-1.6: Tamamlanma yüzdesi hesaplama
    """
    # Tüm sorulara cevap ver
    for exam_question in test_exam_questions:
        answer = StudentAnswer(
            exam_session_id=test_exam_session.id,
            question_id=exam_question.question_id,
            selected_answer="A",
            is_correct=True,
            response_time_seconds=30.0,
        )
        db_session.add(answer)

    await db_session.commit()

    service = await create_answer_tracking_service(db_session)
    stats = await service.get_completion_stats(test_exam_session.id)

    assert stats.total_questions == 10
    assert stats.answered_questions == 10
    assert stats.unanswered_questions == 0
    assert stats.empty_answers == 0
    assert stats.completion_percentage == 100.0
    assert len(stats.unanswered_question_ids) == 0
    assert len(stats.unanswered_question_orders) == 0


@pytest.mark.asyncio
async def test_get_all_answer_statuses(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Tüm cevap durumlarını getir

    REQ-1.6: Cevap durumu takibi
    """
    # Bazı sorulara cevap ver
    for i in range(3):
        answer = StudentAnswer(
            exam_session_id=test_exam_session.id,
            question_id=test_exam_questions[i].question_id,
            selected_answer="B",
            is_correct=False,
            response_time_seconds=45.0,
        )
        db_session.add(answer)

    await db_session.commit()

    service = await create_answer_tracking_service(db_session)
    statuses = await service.get_all_answer_statuses(test_exam_session.id)

    assert len(statuses) == 10

    # İlk 3 soru cevaplandı
    for i in range(3):
        assert statuses[i].is_answered is True
        assert statuses[i].selected_answer == "B"
        assert statuses[i].is_empty is False
        assert statuses[i].response_time_seconds == 45.0

    # Geri kalan 7 soru cevaplanmadı
    for i in range(3, 10):
        assert statuses[i].is_answered is False
        assert statuses[i].selected_answer is None
        assert statuses[i].is_empty is True
        assert statuses[i].response_time_seconds == 0.0


@pytest.mark.asyncio
async def test_mark_answer_as_empty(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Cevabı boş olarak işaretle

    REQ-1.6: Boş cevap işaretleme
    """
    service = await create_answer_tracking_service(db_session)

    question_id = test_exam_questions[0].question_id

    # Cevabı boş olarak işaretle
    success = await service.mark_answer_as_empty(
        exam_session_id=test_exam_session.id, question_id=question_id
    )

    assert success is True

    # Cevap durumunu kontrol et
    status = await service.get_answer_status(
        exam_session_id=test_exam_session.id, question_id=question_id
    )

    assert status is not None
    assert status.is_answered is False
    assert status.selected_answer is None
    assert status.is_empty is True


@pytest.mark.asyncio
async def test_mark_existing_answer_as_empty(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Mevcut cevabı boş olarak güncelle

    REQ-1.6: Boş cevap işaretleme
    """
    question_id = test_exam_questions[0].question_id

    # Önce dolu bir cevap ver
    answer = StudentAnswer(
        exam_session_id=test_exam_session.id,
        question_id=question_id,
        selected_answer="C",
        is_correct=True,
        response_time_seconds=60.0,
    )
    db_session.add(answer)
    await db_session.commit()

    service = await create_answer_tracking_service(db_session)

    # Cevabı boş olarak işaretle
    success = await service.mark_answer_as_empty(
        exam_session_id=test_exam_session.id, question_id=question_id
    )

    assert success is True

    # Cevap durumunu kontrol et
    status = await service.get_answer_status(
        exam_session_id=test_exam_session.id, question_id=question_id
    )

    assert status is not None
    assert status.is_answered is False
    assert status.selected_answer is None
    assert status.is_empty is True


@pytest.mark.asyncio
async def test_update_exam_session_stats(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Sınav oturumu istatistiklerini güncelle

    REQ-1.6: Otomatik istatistik güncelleme
    """
    # Bazı sorulara boş cevap ver
    for i in range(3):
        answer = StudentAnswer(
            exam_session_id=test_exam_session.id,
            question_id=test_exam_questions[i].question_id,
            selected_answer=None,
            is_correct=None,
            response_time_seconds=0.0,
        )
        db_session.add(answer)

    await db_session.commit()

    service = await create_answer_tracking_service(db_session)

    # İstatistikleri güncelle
    success = await service.update_exam_session_stats(test_exam_session.id)

    assert success is True

    # Sınav oturumunu yeniden yükle
    await db_session.refresh(test_exam_session)

    # Boş cevap sayısının güncellendiğini kontrol et
    assert test_exam_session.total_empty == 3


@pytest.mark.asyncio
async def test_completion_percentage_calculation(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Tamamlanma yüzdesi doğru hesaplanıyor mu?

    REQ-1.6: Tamamlanma yüzdesi hesaplama
    """
    service = await create_answer_tracking_service(db_session)

    # Test senaryoları
    test_cases = [
        (0, 0.0),  # Hiç cevap yok
        (1, 10.0),  # 1/10 = %10
        (5, 50.0),  # 5/10 = %50
        (7, 70.0),  # 7/10 = %70
        (10, 100.0),  # 10/10 = %100
    ]

    for answered_count, expected_percentage in test_cases:
        # Önceki cevapları temizle
        from sqlalchemy import delete

        await db_session.execute(
            delete(StudentAnswer).where(
                StudentAnswer.exam_session_id == test_exam_session.id
            )
        )
        await db_session.commit()

        # Yeni cevaplar ekle
        for i in range(answered_count):
            answer = StudentAnswer(
                exam_session_id=test_exam_session.id,
                question_id=test_exam_questions[i].question_id,
                selected_answer="A",
                is_correct=True,
                response_time_seconds=30.0,
            )
            db_session.add(answer)

        await db_session.commit()

        # İstatistikleri kontrol et
        stats = await service.get_completion_stats(test_exam_session.id)

        assert (
            stats.completion_percentage == expected_percentage
        ), f"Expected {expected_percentage}% for {answered_count} answers, got {stats.completion_percentage}%"


@pytest.mark.asyncio
async def test_empty_vs_unanswered_distinction(
    db_session: AsyncSession, test_exam_session, test_exam_questions
):
    """
    Test: Boş cevap ile cevaplanmayan soru ayrımı

    REQ-1.6: Boş cevap ve cevaplanmayan soru takibi
    """
    # 3 soru: dolu cevap
    # 2 soru: boş cevap
    # 5 soru: hiç dokunulmamış

    for i in range(3):
        answer = StudentAnswer(
            exam_session_id=test_exam_session.id,
            question_id=test_exam_questions[i].question_id,
            selected_answer="A",
            is_correct=True,
            response_time_seconds=30.0,
        )
        db_session.add(answer)

    for i in range(3, 5):
        answer = StudentAnswer(
            exam_session_id=test_exam_session.id,
            question_id=test_exam_questions[i].question_id,
            selected_answer=None,
            is_correct=None,
            response_time_seconds=0.0,
        )
        db_session.add(answer)

    await db_session.commit()

    service = await create_answer_tracking_service(db_session)
    stats = await service.get_completion_stats(test_exam_session.id)

    # Doğrulamalar
    assert stats.answered_questions == 3  # Sadece dolu cevaplar
    assert stats.empty_answers == 2  # Boş bırakılan
    assert stats.unanswered_questions == 5  # Hiç dokunulmamış
    assert stats.total_questions == 10

    # Toplam kontrol: answered + empty + unanswered = total
    assert (
        stats.answered_questions + stats.empty_answers + stats.unanswered_questions
    ) == stats.total_questions
