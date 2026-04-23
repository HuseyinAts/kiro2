"""
Test Expert Review Queue

ExpertReviewQueue sınıfı için comprehensive unit testler.
REQ-48.57 - REQ-48.60 gereksinimlerini test eder.
"""

from datetime import datetime, timedelta

import pytest

from services.quality.expert_review_queue import (
    ExpertProfile,
    ExpertReviewQueue,
    ReviewItem,
    ReviewPriority,
    ReviewStatus,
)


class TestExpertReviewQueue:
    """ExpertReviewQueue test sınıfı"""

    @pytest.fixture
    def queue(self):
        """Boş kuyruk instance"""
        return ExpertReviewQueue()

    @pytest.fixture
    def sample_question(self):
        """Örnek soru"""
        return {
            "question_id": "q001",
            "question_text": "Türkiye'nin başkenti neresidir?",
            "options": ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya"],
            "correct_answer": 0,
            "explanation": "Türkiye'nin başkenti 1923'ten beri Ankara'dır.",
            "subject": "Sosyal Bilgiler",
            "difficulty_level": "kolay",
            "quality_score": 85.5,
        }

    # ==================== INITIALIZATION TESTS ====================

    def test_queue_initialization(self):
        """Test: Kuyruk başlatma"""
        queue = ExpertReviewQueue()

        assert queue.review_queue == []
        assert queue.experts == {}
        assert queue.completed_reviews == []

    # ==================== ADD TO QUEUE TESTS (REQ-48.57) ====================

    def test_add_to_queue_basic(self, queue, sample_question):
        """Test: Kuyruğa soru ekleme (REQ-48.57)"""
        review_item = queue.add_to_queue(**sample_question)

        assert isinstance(review_item, ReviewItem)
        assert review_item.question_id == "q001"
        assert review_item.status == ReviewStatus.PENDING
        assert len(queue.review_queue) == 1

    def test_add_to_queue_with_priority(self, queue, sample_question):
        """Test: Öncelikli soru ekleme"""
        review_item = queue.add_to_queue(
            **sample_question, priority=ReviewPriority.URGENT
        )

        assert review_item.priority == ReviewPriority.URGENT

    def test_add_to_queue_multiple(self, queue, sample_question):
        """Test: Birden fazla soru ekleme"""
        for i in range(5):
            q = sample_question.copy()
            q["question_id"] = f"q{i:03d}"
            queue.add_to_queue(**q)

        assert len(queue.review_queue) == 5

    def test_add_to_queue_auto_assign(self, queue, sample_question):
        """Test: Otomatik uzman ataması"""
        # Önce uzman ekle
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        # Soru ekle
        review_item = queue.add_to_queue(**sample_question)

        # Otomatik atanmış olmalı
        assert review_item.assigned_to == "exp001"
        assert review_item.status == ReviewStatus.IN_REVIEW

    # ==================== EXPERT REGISTRATION TESTS ====================

    def test_register_expert_basic(self, queue):
        """Test: Uzman kaydı"""
        expert = queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Matematik", "Fizik"],
        )

        assert isinstance(expert, ExpertProfile)
        assert expert.id == "exp001"
        assert expert.name == "Ahmet Yılmaz"
        assert len(expert.expertise_subjects) == 2
        assert "exp001" in queue.experts

    def test_register_expert_custom_capacity(self, queue):
        """Test: Özel kapasite ile uzman kaydı"""
        expert = queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Matematik"],
            max_concurrent_reviews=20,
        )

        assert expert.max_concurrent_reviews == 20

    def test_register_multiple_experts(self, queue):
        """Test: Birden fazla uzman kaydı"""
        for i in range(3):
            queue.register_expert(
                expert_id=f"exp{i:03d}",
                name=f"Uzman {i}",
                email=f"uzman{i}@test.com",
                expertise_subjects=["Matematik"],
            )

        assert len(queue.experts) == 3

    # ==================== ASSIGNMENT TESTS (REQ-48.58) ====================

    def test_assign_to_expert_basic(self, queue, sample_question):
        """Test: Uzmana atama (REQ-48.58)"""
        # Uzman ve soru ekle
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)
        review_item.status = ReviewStatus.PENDING  # Otomatik atamayı sıfırla
        review_item.assigned_to = None

        # Manuel atama
        success = queue.assign_to_expert(review_item.id, "exp001")

        assert success is True
        assert review_item.assigned_to == "exp001"
        assert review_item.status == ReviewStatus.IN_REVIEW
        assert review_item.assigned_at is not None

    def test_assign_to_expert_capacity_check(self, queue, sample_question):
        """Test: Kapasite kontrolü"""
        # Kapasite 1 olan uzman
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
            max_concurrent_reviews=1,
        )

        # İki soru ekle
        q1 = sample_question.copy()
        q1["question_id"] = "q001"
        review1 = queue.add_to_queue(**q1)

        q2 = sample_question.copy()
        q2["question_id"] = "q002"
        review2 = queue.add_to_queue(**q2)
        review2.status = ReviewStatus.PENDING
        review2.assigned_to = None

        # İkinci atama başarısız olmalı (kapasite dolu)
        success = queue.assign_to_expert(review2.id, "exp001")

        assert success is False

    def test_assign_to_expert_invalid_review(self, queue):
        """Test: Geçersiz review ID"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Matematik"],
        )

        success = queue.assign_to_expert("invalid_id", "exp001")

        assert success is False

    def test_assign_to_expert_invalid_expert(self, queue, sample_question):
        """Test: Geçersiz expert ID"""
        review_item = queue.add_to_queue(**sample_question)

        success = queue.assign_to_expert(review_item.id, "invalid_expert")

        assert success is False

    def test_auto_assign_by_expertise(self, queue):
        """Test: Uzmanlık alanına göre otomatik atama (REQ-48.58)"""
        # Farklı uzmanlık alanlarında uzmanlar
        queue.register_expert(
            expert_id="exp_math",
            name="Matematik Uzmanı",
            email="math@test.com",
            expertise_subjects=["Matematik"],
        )

        queue.register_expert(
            expert_id="exp_turkish",
            name="Türkçe Uzmanı",
            email="turkish@test.com",
            expertise_subjects=["Türkçe"],
        )

        # Türkçe sorusu ekle
        review = queue.add_to_queue(
            question_id="q001",
            question_text="Türkçe sorusu?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
            explanation="Açıklama",
            subject="Türkçe",
            difficulty_level="orta",
            quality_score=80.0,
        )

        # Türkçe uzmanına atanmış olmalı
        assert review.assigned_to == "exp_turkish"

    def test_auto_assign_load_balancing(self, queue):
        """Test: Yük dengeleme ile otomatik atama"""
        # İki matematik uzmanı
        queue.register_expert(
            expert_id="exp001",
            name="Uzman 1",
            email="exp1@test.com",
            expertise_subjects=["Matematik"],
        )

        queue.register_expert(
            expert_id="exp002",
            name="Uzman 2",
            email="exp2@test.com",
            expertise_subjects=["Matematik"],
        )

        # İlk uzmanı doldur
        queue.experts["exp001"].current_review_count = 5
        queue.experts["exp002"].current_review_count = 2

        # Yeni soru ekle
        review = queue.add_to_queue(
            question_id="q001",
            question_text="Matematik sorusu?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
            explanation="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            quality_score=80.0,
        )

        # Daha az yüklü uzmana atanmış olmalı
        assert review.assigned_to == "exp002"

    # ==================== SUBMIT REVIEW TESTS (REQ-48.59) ====================

    def test_submit_review_approved(self, queue, sample_question):
        """Test: Onaylı inceleme gönderimi (REQ-48.59)"""
        # Uzman ve soru ekle
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        # İnceleme gönder
        success = queue.submit_review(
            review_id=review_item.id,
            expert_id="exp001",
            status=ReviewStatus.APPROVED,
            reviewer_comments="Mükemmel soru",
            feedback=["Kaliteli içerik", "ÖSYM formatına uygun"],
        )

        assert success is True
        assert review_item.status == ReviewStatus.APPROVED
        assert review_item.reviewed_at is not None
        assert review_item.reviewer_comments == "Mükemmel soru"
        assert len(review_item.feedback) == 2

    def test_submit_review_rejected(self, queue, sample_question):
        """Test: Reddedilen inceleme"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        success = queue.submit_review(
            review_id=review_item.id,
            expert_id="exp001",
            status=ReviewStatus.REJECTED,
            reviewer_comments="Kalite yetersiz",
        )

        assert success is True
        assert review_item.status == ReviewStatus.REJECTED
        assert review_item not in queue.review_queue
        assert review_item in queue.completed_reviews

    def test_submit_review_needs_revision(self, queue, sample_question):
        """Test: Revizyon gerektiren inceleme"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        success = queue.submit_review(
            review_id=review_item.id,
            expert_id="exp001",
            status=ReviewStatus.NEEDS_REVISION,
            reviewer_comments="Açıklama eksik",
        )

        assert success is True
        assert review_item.status == ReviewStatus.PENDING
        assert review_item.revision_count == 1
        assert review_item.assigned_to is None

    def test_submit_review_expert_statistics_update(self, queue, sample_question):
        """Test: Uzman istatistikleri güncelleme"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        expert = queue.experts["exp001"]
        initial_count = expert.total_reviews_completed

        review_item = queue.add_to_queue(**sample_question)

        queue.submit_review(
            review_id=review_item.id, expert_id="exp001", status=ReviewStatus.APPROVED
        )

        assert expert.total_reviews_completed == initial_count + 1
        assert expert.current_review_count == 0

    def test_submit_review_invalid_expert(self, queue, sample_question):
        """Test: Yanlış uzman ile gönderim"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        # Farklı uzman ile göndermeye çalış
        success = queue.submit_review(
            review_id=review_item.id,
            expert_id="exp002",  # Yanlış uzman
            status=ReviewStatus.APPROVED,
        )

        assert success is False

    # ==================== QUERY TESTS ====================

    def test_get_pending_reviews(self, queue, sample_question):
        """Test: Bekleyen incelemeleri getir"""
        # Birkaç soru ekle
        for i in range(3):
            q = sample_question.copy()
            q["question_id"] = f"q{i:03d}"
            review = queue.add_to_queue(**q)
            review.status = ReviewStatus.PENDING
            review.assigned_to = None

        pending = queue.get_pending_reviews()

        assert len(pending) == 3
        assert all(r.status == ReviewStatus.PENDING for r in pending)

    def test_get_pending_reviews_filtered_by_subject(self, queue):
        """Test: Konuya göre filtreleme"""
        # Farklı konularda sorular
        queue.add_to_queue(
            question_id="q001",
            question_text="Matematik sorusu?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
            explanation="Açıklama",
            subject="Matematik",
            difficulty_level="orta",
            quality_score=80.0,
        )

        queue.add_to_queue(
            question_id="q002",
            question_text="Türkçe sorusu?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
            explanation="Açıklama",
            subject="Türkçe",
            difficulty_level="orta",
            quality_score=80.0,
        )

        # Tüm soruları pending yap
        for review in queue.review_queue:
            review.status = ReviewStatus.PENDING
            review.assigned_to = None

        math_reviews = queue.get_pending_reviews(subject="Matematik")

        assert len(math_reviews) == 1
        assert math_reviews[0].subject == "Matematik"

    def test_get_pending_reviews_sorted_by_priority(self, queue, sample_question):
        """Test: Önceliğe göre sıralama"""
        # Farklı önceliklerde sorular
        for priority in [
            ReviewPriority.LOW,
            ReviewPriority.URGENT,
            ReviewPriority.MEDIUM,
        ]:
            q = sample_question.copy()
            q["question_id"] = f"q_{priority.name}"
            review = queue.add_to_queue(**q, priority=priority)
            review.status = ReviewStatus.PENDING
            review.assigned_to = None

        pending = queue.get_pending_reviews()

        # İlk sırada URGENT olmalı
        assert pending[0].priority == ReviewPriority.URGENT

    def test_get_expert_reviews(self, queue, sample_question):
        """Test: Uzmanın incelemelerini getir"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        # Birkaç soru ekle
        for i in range(3):
            q = sample_question.copy()
            q["question_id"] = f"q{i:03d}"
            queue.add_to_queue(**q)

        expert_reviews = queue.get_expert_reviews("exp001")

        assert len(expert_reviews) == 3
        assert all(r.assigned_to == "exp001" for r in expert_reviews)

    def test_get_approved_questions(self, queue, sample_question):
        """Test: Onaylanmış soruları getir (REQ-48.60)"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        queue.submit_review(
            review_id=review_item.id, expert_id="exp001", status=ReviewStatus.APPROVED
        )

        approved = queue.get_approved_questions()

        assert len(approved) == 1
        assert approved[0].status == ReviewStatus.APPROVED

    # ==================== STATISTICS TESTS ====================

    def test_get_queue_statistics(self, queue, sample_question):
        """Test: Kuyruk istatistikleri"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        # Birkaç soru ekle ve işle
        for i in range(5):
            q = sample_question.copy()
            q["question_id"] = f"q{i:03d}"
            review = queue.add_to_queue(**q)

            if i < 3:
                queue.submit_review(
                    review_id=review.id,
                    expert_id="exp001",
                    status=ReviewStatus.APPROVED,
                )

        stats = queue.get_queue_statistics()

        assert "total_pending" in stats
        assert "total_in_review" in stats
        assert "total_approved" in stats
        assert "total_rejected" in stats
        assert "approval_rate_percent" in stats
        assert "average_review_time_minutes" in stats
        assert stats["total_approved"] == 3

    def test_get_expert_statistics(self, queue, sample_question):
        """Test: Uzman istatistikleri"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        stats = queue.get_expert_statistics("exp001")

        assert stats is not None
        assert stats["expert_id"] == "exp001"
        assert "total_reviews_completed" in stats
        assert "approval_rate_percent" in stats
        assert "capacity_utilization_percent" in stats

    def test_get_expert_statistics_invalid_expert(self, queue):
        """Test: Geçersiz uzman istatistikleri"""
        stats = queue.get_expert_statistics("invalid_expert")

        assert stats is None

    # ==================== EXPORT TESTS (REQ-48.60) ====================

    def test_export_approved_to_question_bank(self, queue, sample_question):
        """Test: Onaylanmış soruları dışa aktar (REQ-48.60)"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        queue.submit_review(
            review_id=review_item.id,
            expert_id="exp001",
            status=ReviewStatus.APPROVED,
            reviewer_comments="Mükemmel",
        )

        exported = queue.export_approved_to_question_bank()

        assert len(exported) == 1
        assert exported[0]["id"] == "q001"
        assert exported[0]["reviewed_by"] == "exp001"
        assert exported[0]["reviewer_comments"] == "Mükemmel"

    def test_export_with_date_filter(self, queue, sample_question):
        """Test: Tarih filtresi ile dışa aktarma"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        queue.submit_review(
            review_id=review_item.id, expert_id="exp001", status=ReviewStatus.APPROVED
        )

        # Gelecek tarih ile filtrele
        future_date = datetime.now() + timedelta(days=1)
        exported = queue.export_approved_to_question_bank(since=future_date)

        assert len(exported) == 0

    # ==================== EDGE CASES ====================

    def test_multiple_revisions(self, queue, sample_question):
        """Test: Çoklu revizyonlar"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
        )

        review_item = queue.add_to_queue(**sample_question)

        # İlk revizyon
        queue.submit_review(
            review_id=review_item.id,
            expert_id="exp001",
            status=ReviewStatus.NEEDS_REVISION,
        )

        assert review_item.revision_count == 1

        # Tekrar ata ve revizyon iste
        queue.assign_to_expert(review_item.id, "exp001")
        queue.submit_review(
            review_id=review_item.id,
            expert_id="exp001",
            status=ReviewStatus.NEEDS_REVISION,
        )

        assert review_item.revision_count == 2

    def test_concurrent_expert_capacity(self, queue, sample_question):
        """Test: Eşzamanlı uzman kapasitesi"""
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Sosyal Bilgiler"],
            max_concurrent_reviews=2,
        )

        # 3 soru ekle
        for i in range(3):
            q = sample_question.copy()
            q["question_id"] = f"q{i:03d}"
            queue.add_to_queue(**q)

        expert = queue.experts["exp001"]

        # Maksimum 2 olmalı
        assert expert.current_review_count <= 2


# ==================== INTEGRATION TESTS ====================


class TestExpertReviewQueueIntegration:
    """Integration testleri"""

    def test_full_review_workflow(self):
        """Test: Tam inceleme iş akışı"""
        queue = ExpertReviewQueue()

        # 1. Uzman kaydı
        queue.register_expert(
            expert_id="exp001",
            name="Ahmet Yılmaz",
            email="ahmet@test.com",
            expertise_subjects=["Matematik"],
        )

        # 2. Soru ekleme
        review = queue.add_to_queue(
            question_id="q001",
            question_text="2 + 2 = ?",
            options=["3", "4", "5", "6", "7"],
            correct_answer=1,
            explanation="2 + 2 = 4",
            subject="Matematik",
            difficulty_level="kolay",
            quality_score=90.0,
        )

        # 3. Otomatik atama yapılmış olmalı
        assert review.assigned_to == "exp001"

        # 4. İnceleme gönderimi
        queue.submit_review(
            review_id=review.id,
            expert_id="exp001",
            status=ReviewStatus.APPROVED,
            reviewer_comments="Mükemmel soru",
        )

        # 5. Onaylanmış sorular listesinde olmalı
        approved = queue.get_approved_questions()
        assert len(approved) == 1

        # 6. Soru bankasına aktarılabilir
        exported = queue.export_approved_to_question_bank()
        assert len(exported) == 1

    def test_multi_expert_load_balancing(self):
        """Test: Çoklu uzman yük dengeleme"""
        queue = ExpertReviewQueue()

        # 3 uzman kaydet
        for i in range(3):
            queue.register_expert(
                expert_id=f"exp{i:03d}",
                name=f"Uzman {i}",
                email=f"uzman{i}@test.com",
                expertise_subjects=["Matematik"],
            )

        # 10 soru ekle
        for i in range(10):
            queue.add_to_queue(
                question_id=f"q{i:03d}",
                question_text=f"Soru {i}?",
                options=["A", "B", "C", "D", "E"],
                correct_answer=0,
                explanation="Açıklama",
                subject="Matematik",
                difficulty_level="orta",
                quality_score=80.0,
            )

        # Yük dengeli dağıtılmış olmalı
        for expert in queue.experts.values():
            assert 2 <= expert.current_review_count <= 4
