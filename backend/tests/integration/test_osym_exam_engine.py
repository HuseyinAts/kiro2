"""
ÖSYM Sınav Motoru Unit Testleri
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül ÖSYM sınav motorunun tüm bileşenlerini test eder:
- Sınav oturumu oluşturma ve yönetimi
- Soru navigasyonu ve cevap kaydetme
- Performans analizi ve puanlama
- Otomatik kaydetme ve tamamlama
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Test için gerekli import'ları mock'layalım
with patch.dict(
    "sys.modules",
    {
        "models.database": MagicMock(),
        "core.database": MagicMock(),
        "core.structured_logger": MagicMock(),
    },
):
    from core.osym_exam_engine import ExamStatus, OSYMExamEngine, SubjectPerformance


# Mock enum'lar
class MockExamType:
    TYT = "TYT"
    AYT = "AYT"
    YDT = "YDT"


class MockQuestionDifficulty:
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MockSubjectArea:
    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN = "fen"
    SOSYAL = "sosyal"


# Mock Question sınıfı
class MockQuestion:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestOSYMExamEngine:
    """ÖSYM Sınav Motoru test sınıfı"""

    @pytest.fixture
    def exam_engine(self):
        """Test için sınav motoru instance'ı"""
        return OSYMExamEngine()

    @pytest.fixture
    def mock_questions(self):
        """Test için mock sorular"""
        questions = []
        subjects = ["TURKCE", "MATEMATIK", "FEN", "SOSYAL"]

        for i in range(120):  # TYT için 120 soru
            subject_index = i % len(subjects)
            question = MockQuestion(
                id=f"question_{i+1}",
                question_text=f"Test sorusu {i+1}",
                option_a="Seçenek A",
                option_b="Seçenek B",
                option_c="Seçenek C",
                option_d="Seçenek D",
                correct_answer="A",
                exam_type=MockExamType.TYT,
                subject_area=MockSubjectArea.MATEMATIK,
                topic=f"Konu {subject_index + 1}",
                difficulty=MockQuestionDifficulty.MEDIUM,
                irt_difficulty=0.0,
                irt_discrimination=1.0,
                is_active=True,
            )
            questions.append(question)

        return questions

    @pytest.fixture
    def student_id(self):
        """Test öğrenci ID'si"""
        return "test_student_123"

    @pytest.mark.asyncio
    async def test_exam_config_initialization(self, exam_engine):
        """Sınav konfigürasyonlarının doğru başlatılması"""
        # TYT konfigürasyonu kontrolü
        tyt_config = exam_engine.exam_configs[ExamType.TYT]
        assert tyt_config.exam_type == ExamType.TYT
        assert tyt_config.total_questions == 120
        assert tyt_config.duration_minutes == 165
        assert tyt_config.subject_distribution["TURKCE"] == 40
        assert tyt_config.subject_distribution["MATEMATIK"] == 40
        assert tyt_config.subject_distribution["FEN"] == 20
        assert tyt_config.subject_distribution["SOSYAL"] == 20

        # AYT konfigürasyonu kontrolü
        ayt_config = exam_engine.exam_configs[ExamType.AYT]
        assert ayt_config.exam_type == ExamType.AYT
        assert ayt_config.total_questions == 160
        assert ayt_config.duration_minutes == 210

        # YDT konfigürasyonu kontrolü
        ydt_config = exam_engine.exam_configs[ExamType.YDT]
        assert ydt_config.exam_type == ExamType.YDT
        assert ydt_config.total_questions == 80
        assert ydt_config.duration_minutes == 180
        assert ydt_config.subject_distribution["INGILIZCE"] == 80

    @pytest.mark.asyncio
    async def test_create_exam_session_success(
        self, exam_engine, student_id, mock_questions
    ):
        """Başarılı sınav oturumu oluşturma"""
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            # Mock database session
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Sınav oturumu oluştur
            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )

            # Sonuçları kontrol et
            assert session_id is not None
            assert session_id in exam_engine.active_sessions

            session_data = exam_engine.active_sessions[session_id]
            assert session_data.student_id == student_id
            assert session_data.exam_config.exam_type == ExamType.TYT
            assert session_data.status == ExamStatus.NOT_STARTED
            assert len(session_data.questions) == 120

            # Database kayıt kontrolü
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_exam_session_insufficient_questions(
        self, exam_engine, student_id
    ):
        """Yetersiz soru durumunda hata fırlatma"""
        with patch.object(exam_engine, "_select_questions", return_value=[]):
            with pytest.raises(ValueError, match="Yeterli soru bulunamadı"):
                await exam_engine.create_exam_session(
                    student_id=student_id, exam_type=ExamType.TYT
                )

    @pytest.mark.asyncio
    async def test_create_exam_session_custom_config(
        self, exam_engine, student_id, mock_questions
    ):
        """Özel konfigürasyon ile sınav oluşturma"""
        custom_config = {
            "duration_minutes": 120,
            "subject_distribution": {"TURKCE": 50, "MATEMATIK": 50},
        }

        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id,
                exam_type=ExamType.TYT,
                custom_config=custom_config,
            )

            session_data = exam_engine.active_sessions[session_id]
            assert session_data.exam_config.duration_minutes == 120

    @pytest.mark.asyncio
    async def test_start_exam_success(self, exam_engine, student_id, mock_questions):
        """Başarılı sınav başlatma"""
        # Önce sınav oturumu oluştur
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )

        # Sınavı başlat
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_data = await exam_engine.start_exam(session_id)

            # Sonuçları kontrol et
            assert session_data.status == ExamStatus.IN_PROGRESS
            assert session_data.started_at is not None
            assert session_id in exam_engine.auto_save_tasks

            # Database güncelleme kontrolü
            mock_db.execute.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_start_exam_not_found(self, exam_engine):
        """Var olmayan sınav başlatma hatası"""
        with pytest.raises(ValueError, match="Sınav oturumu bulunamadı"):
            await exam_engine.start_exam("nonexistent_session")

    @pytest.mark.asyncio
    async def test_start_exam_already_started(
        self, exam_engine, student_id, mock_questions
    ):
        """Zaten başlatılmış sınav hatası"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )

            await exam_engine.start_exam(session_id)

        # Tekrar başlatmaya çalış
        with pytest.raises(
            ValueError, match="Sınav zaten başlatılmış veya tamamlanmış"
        ):
            await exam_engine.start_exam(session_id)

    @pytest.mark.asyncio
    async def test_get_current_question_success(
        self, exam_engine, student_id, mock_questions
    ):
        """Mevcut soru getirme başarılı"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Mevcut soruyu getir
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock query result
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_questions[0]
            mock_db.execute.return_value = mock_result

            question = await exam_engine.get_current_question(session_id)

            assert question is not None
            assert question.id == "question_1"

    @pytest.mark.asyncio
    async def test_get_current_question_not_in_progress(
        self, exam_engine, student_id, mock_questions
    ):
        """Başlatılmamış sınavda soru getirme"""
        # Sadece sınav oluştur, başlatma
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )

        # Mevcut soruyu getirmeye çalış
        question = await exam_engine.get_current_question(session_id)
        assert question is None

    @pytest.mark.asyncio
    async def test_save_answer_success(self, exam_engine, student_id, mock_questions):
        """Başarılı cevap kaydetme"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Cevap kaydet
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock existing answer check
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            success = await exam_engine.save_answer(
                session_id=session_id,
                question_id="question_1",
                selected_answer="A",
                response_time=30.5,
            )

            assert success is True

            # Session data kontrolü
            session_data = exam_engine.active_sessions[session_id]
            assert session_data.answers["question_1"] == "A"
            assert session_data.time_spent_per_question["question_1"] == 30.5

    @pytest.mark.asyncio
    async def test_save_answer_update_existing(
        self, exam_engine, student_id, mock_questions
    ):
        """Mevcut cevabı güncelleme"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Mevcut cevabı güncelle
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock existing answer
            mock_existing = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_existing
            mock_db.execute.return_value = mock_result

            success = await exam_engine.save_answer(
                session_id=session_id,
                question_id="question_1",
                selected_answer="B",
                response_time=45.0,
            )

            assert success is True

            # Update query kontrolü
            mock_db.execute.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_save_answer_remove_answer(
        self, exam_engine, student_id, mock_questions
    ):
        """Cevabı kaldırma (None gönderme)"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Önce cevap kaydet
        session_data = exam_engine.active_sessions[session_id]
        session_data.answers["question_1"] = "A"

        # Cevabı kaldır
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            success = await exam_engine.save_answer(
                session_id=session_id, question_id="question_1", selected_answer=None
            )

            assert success is True
            assert "question_1" not in session_data.answers

    @pytest.mark.asyncio
    async def test_navigate_to_question_success(
        self, exam_engine, student_id, mock_questions
    ):
        """Başarılı soru navigasyonu"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # 10. soruya git
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_questions[
                9
            ]  # 0-based index
            mock_db.execute.return_value = mock_result

            question = await exam_engine.navigate_to_question(session_id, 9)

            assert question is not None
            assert question.id == "question_10"

            # Session data kontrolü
            session_data = exam_engine.active_sessions[session_id]
            assert session_data.current_question_index == 9

    @pytest.mark.asyncio
    async def test_navigate_to_question_invalid_index(
        self, exam_engine, student_id, mock_questions
    ):
        """Geçersiz soru indeksi ile navigasyon"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Geçersiz indekse git
        question = await exam_engine.navigate_to_question(
            session_id, 150
        )  # 120 soruluk sınavda 150. soru
        assert question is None

        # Negatif indeks
        question = await exam_engine.navigate_to_question(session_id, -1)
        assert question is None

    @pytest.mark.asyncio
    async def test_flag_question_success(self, exam_engine, student_id, mock_questions):
        """Başarılı soru işaretleme"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Soruyu işaretle
        success = await exam_engine.flag_question(session_id, "question_1", True)
        assert success is True

        session_data = exam_engine.active_sessions[session_id]
        assert "question_1" in session_data.flagged_questions

        # İşareti kaldır
        success = await exam_engine.flag_question(session_id, "question_1", False)
        assert success is True
        assert "question_1" not in session_data.flagged_questions

    @pytest.mark.asyncio
    async def test_get_remaining_time_success(
        self, exam_engine, student_id, mock_questions
    ):
        """Kalan süre hesaplama"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Kalan süreyi getir
        remaining_time = await exam_engine.get_remaining_time(session_id)

        assert remaining_time is not None
        assert remaining_time > 0
        assert remaining_time <= 165 * 60  # 165 dakika = 9900 saniye

    @pytest.mark.asyncio
    async def test_get_remaining_time_not_started(
        self, exam_engine, student_id, mock_questions
    ):
        """Başlatılmamış sınavda kalan süre"""
        # Sadece sınav oluştur
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )

        # Kalan süreyi getir
        remaining_time = await exam_engine.get_remaining_time(session_id)
        assert remaining_time is None

    @pytest.mark.asyncio
    async def test_complete_exam_success(self, exam_engine, student_id, mock_questions):
        """Başarılı sınav tamamlama"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Bazı cevaplar ekle
        session_data = exam_engine.active_sessions[session_id]
        session_data.answers["question_1"] = "A"  # Doğru
        session_data.answers["question_2"] = "B"  # Yanlış (doğru A)
        session_data.answers["question_3"] = "A"  # Doğru

        # Sınavı tamamla
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock correct answer queries
            mock_results = [
                MagicMock(scalar_one_or_none=MagicMock(return_value="A")),  # question_1
                MagicMock(scalar_one_or_none=MagicMock(return_value="A")),  # question_2
                MagicMock(scalar_one_or_none=MagicMock(return_value="A")),  # question_3
            ]
            mock_db.execute.side_effect = mock_results

            performance = await exam_engine.complete_exam(session_id)

            # Sonuçları kontrol et
            assert performance.total_questions == 120
            assert performance.answered_questions == 3
            assert performance.correct_answers == 2
            assert performance.wrong_answers == 1
            assert performance.empty_answers == 117
            assert performance.net_score == 2 - (1 / 4)  # 2 doğru - (1 yanlış / 4)
            assert performance.raw_score == (2 / 120) * 100  # %1.67

            # Session durumu kontrolü
            assert session_data.status == ExamStatus.COMPLETED
            assert session_data.completed_at is not None
            assert session_data.performance_metrics == performance

    @pytest.mark.asyncio
    async def test_complete_exam_already_completed(
        self, exam_engine, student_id, mock_questions
    ):
        """Zaten tamamlanmış sınavı tekrar tamamlama"""
        # Sınav oluştur, başlat ve tamamla
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

            # İlk tamamlama
            mock_results = []
            mock_db.execute.side_effect = mock_results
            performance1 = await exam_engine.complete_exam(session_id)

            # İkinci tamamlama
            performance2 = await exam_engine.complete_exam(session_id)

            # Aynı sonucu döndürmeli
            assert performance1 == performance2

    @pytest.mark.asyncio
    async def test_get_session_data(self, exam_engine, student_id, mock_questions):
        """Oturum verilerini getirme"""
        # Sınav oluştur
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )

        # Oturum verilerini getir
        session_data = await exam_engine.get_session_data(session_id)

        assert session_data is not None
        assert session_data.session_id == session_id
        assert session_data.student_id == student_id
        assert session_data.exam_config.exam_type == ExamType.TYT

        # Var olmayan oturum
        nonexistent_data = await exam_engine.get_session_data("nonexistent")
        assert nonexistent_data is None

    @pytest.mark.asyncio
    async def test_get_subject_performance(
        self, exam_engine, student_id, mock_questions
    ):
        """Konu bazlı performans analizi"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            await exam_engine.start_exam(session_id)

        # Konu performansını getir
        with patch("core.osym_exam_engine.get_async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock query results
            mock_question_answer_pairs = []
            for i, question in enumerate(mock_questions[:8]):  # İlk 8 soru
                mock_answer = MagicMock()
                mock_answer.selected_answer = "A" if i % 2 == 0 else "B"  # Yarısı doğru
                mock_answer.response_time_seconds = 30.0 + i
                mock_question_answer_pairs.append((question, mock_answer))

            mock_result = MagicMock()
            mock_result.__iter__ = lambda self: iter(mock_question_answer_pairs)
            mock_db.execute.return_value = mock_result

            subject_performances = await exam_engine.get_subject_performance(session_id)

            assert len(subject_performances) > 0

            # Her konu için kontrol
            for perf in subject_performances:
                assert isinstance(perf, SubjectPerformance)
                assert perf.subject in ["turkce", "matematik", "fen", "sosyal"]
                assert perf.total_questions >= 0
                assert 0 <= perf.success_rate <= 100
                assert perf.average_response_time >= 0

    @pytest.mark.asyncio
    async def test_estimate_ability(self, exam_engine):
        """IRT yetenek tahmini"""
        # Mükemmel performans
        ability_perfect = exam_engine._estimate_ability(100, 0, 100)
        assert ability_perfect > 2.0

        # Ortalama performans
        ability_average = exam_engine._estimate_ability(50, 50, 100)
        assert -1.0 < ability_average < 1.0

        # Zayıf performans
        ability_poor = exam_engine._estimate_ability(10, 90, 100)
        assert ability_poor < -1.0

        # Sınır değerler
        ability_zero = exam_engine._estimate_ability(0, 0, 0)
        assert ability_zero == 0.0

    @pytest.mark.asyncio
    async def test_calculate_confidence(self, exam_engine):
        """Güven seviyesi hesaplama"""
        # Tam tamamlama
        confidence_full = exam_engine._calculate_confidence(100, 100)
        assert confidence_full == 1.0

        # Yarı tamamlama
        confidence_half = exam_engine._calculate_confidence(50, 100)
        assert 0.5 < confidence_half < 1.0

        # Hiç tamamlama
        confidence_none = exam_engine._calculate_confidence(0, 100)
        assert confidence_none == 0.0

        # Sıfır soru
        confidence_zero = exam_engine._calculate_confidence(0, 0)
        assert confidence_zero == 0.0

    @pytest.mark.asyncio
    async def test_auto_save_functionality(
        self, exam_engine, student_id, mock_questions
    ):
        """Otomatik kaydetme fonksiyonalitesi"""
        # Sınav oluştur ve başlat
        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )

            # Otomatik kaydetme task'ının başlatıldığını kontrol et
            await exam_engine.start_exam(session_id)
            assert session_id in exam_engine.auto_save_tasks

            # Task'ın çalıştığını kontrol et
            task = exam_engine.auto_save_tasks[session_id]
            assert not task.done()

            # Sınavı tamamla ve task'ın durduğunu kontrol et
            await exam_engine.complete_exam(session_id)
            assert session_id not in exam_engine.auto_save_tasks

    @pytest.mark.asyncio
    async def test_auto_complete_functionality(
        self, exam_engine, student_id, mock_questions
    ):
        """Otomatik tamamlama fonksiyonalitesi"""
        # Kısa süreli sınav konfigürasyonu
        custom_config = {"duration_minutes": 1}  # 1 dakika

        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions[:120]
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            session_id = await exam_engine.create_exam_session(
                student_id=student_id,
                exam_type=ExamType.TYT,
                custom_config=custom_config,
            )

            await exam_engine.start_exam(session_id)

            # Kısa bir süre bekle (gerçek uygulamada 1 dakika bekler)
            # Test için mock'lama yapıyoruz
            with patch.object(exam_engine, "complete_exam") as mock_complete:
                # Otomatik tamamlama task'ını manuel tetikle
                await exam_engine._auto_complete_task(session_id)

                # Otomatik tamamlamanın çağrıldığını kontrol et
                mock_complete.assert_called_once_with(
                    session_id, manual_completion=False
                )


class TestOSYMExamEngineIntegration:
    """ÖSYM Sınav Motoru entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_full_exam_workflow(self):
        """Tam sınav akışı entegrasyon testi"""
        exam_engine = OSYMExamEngine()
        student_id = "integration_test_student"

        # Mock questions
        mock_questions = []
        for i in range(120):
            question = Question(
                id=f"q_{i+1}",
                question_text=f"Soru {i+1}",
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
                correct_answer="A",
                exam_type=ExamType.TYT,
                subject_area=SubjectArea.matematik,
                topic="Test",
                difficulty=QuestionDifficulty.MEDIUM,
                irt_difficulty=0.0,
                is_active=True,
            )
            mock_questions.append(question)

        with patch(
            "core.osym_exam_engine.get_async_session"
        ) as mock_session, patch.object(
            exam_engine, "_select_questions", return_value=mock_questions
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # 1. Sınav oluştur
            session_id = await exam_engine.create_exam_session(
                student_id=student_id, exam_type=ExamType.TYT
            )
            assert session_id is not None

            # 2. Sınavı başlat
            session_data = await exam_engine.start_exam(session_id)
            assert session_data.status == ExamStatus.IN_PROGRESS

            # 3. Sorulara cevap ver
            for i in range(10):  # İlk 10 soruya cevap ver
                question_id = f"q_{i+1}"
                answer = "A" if i % 2 == 0 else "B"  # Yarısı doğru

                success = await exam_engine.save_answer(
                    session_id=session_id,
                    question_id=question_id,
                    selected_answer=answer,
                    response_time=30.0 + i,
                )
                assert success is True

            # 4. Bazı soruları işaretle
            await exam_engine.flag_question(session_id, "q_3", True)
            await exam_engine.flag_question(session_id, "q_7", True)

            # 5. Soru navigasyonu
            question = await exam_engine.navigate_to_question(session_id, 5)
            assert question is not None

            # 6. Kalan süreyi kontrol et
            remaining_time = await exam_engine.get_remaining_time(session_id)
            assert remaining_time is not None
            assert remaining_time > 0

            # 7. Sınavı tamamla
            mock_results = [
                MagicMock(scalar_one_or_none=MagicMock(return_value="A"))
                for _ in range(10)
            ]
            mock_db.execute.side_effect = mock_results

            performance = await exam_engine.complete_exam(session_id)

            # 8. Sonuçları kontrol et
            assert performance.total_questions == 120
            assert performance.answered_questions == 10
            assert performance.correct_answers == 5  # Yarısı doğru
            assert performance.wrong_answers == 5
            assert performance.empty_answers == 110
            assert performance.net_score == 5 - (5 / 4)  # 3.75

            # 9. Konu performansını kontrol et
            subject_performances = await exam_engine.get_subject_performance(session_id)
            assert len(subject_performances) > 0

            # 10. Oturum verilerini kontrol et
            final_session = await exam_engine.get_session_data(session_id)
            assert final_session.status == ExamStatus.COMPLETED
            assert len(final_session.flagged_questions) == 2
            assert len(final_session.answers) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
