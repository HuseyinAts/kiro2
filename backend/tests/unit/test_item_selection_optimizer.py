import pytest
pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Test: Soru Seçimi ve Optimizasyon Sistemi
Task 62: Soru Seçimi ve Optimizasyon
Requirements: REQ-49.53-49.68
"""

import pytest
from datetime import datetime, timedelta
from services.item_selection_optimizer import (
    ItemSelectionOptimizer,
    ContentConstraint,
    SpacedRepetitionSchedule,
)


@pytest.fixture
def optimizer():
    """Item selection optimizer fixture"""
    return ItemSelectionOptimizer()


@pytest.fixture
def sample_questions():
    """Sample question pool"""
    return [
        {
            "id": "q1",
            "topic": "matematik_algebra",
            "difficulty_level": "easy",
            "difficulty_b": -0.5,
            "is_meb_aligned": True,
            "meb_standard_id": "MAT-9-1",
            "osym_format_compliant": True,
        },
        {
            "id": "q2",
            "topic": "matematik_geometri",
            "difficulty_level": "medium",
            "difficulty_b": 0.0,
            "is_meb_aligned": True,
            "meb_standard_id": "MAT-9-2",
            "osym_format_compliant": True,
        },
        {
            "id": "q3",
            "topic": "matematik_algebra",
            "difficulty_level": "hard",
            "difficulty_b": 1.5,
            "is_meb_aligned": True,
            "osym_format_compliant": False,
        },
        {
            "id": "q4",
            "topic": "fizik_mekanik",
            "difficulty_level": "medium",
            "difficulty_b": 0.5,
            "is_meb_aligned": False,
            "osym_format_compliant": True,
        },
    ]


@pytest.fixture
def content_constraints():
    """Sample content constraints"""
    return [
        ContentConstraint(
            subject="matematik",
            topic="matematik_algebra",
            min_questions=2,
            max_questions=5,
            priority=1.5,
        ),
        ContentConstraint(
            subject="matematik",
            topic="matematik_geometri",
            min_questions=1,
            max_questions=3,
            priority=1.0,
        ),
        ContentConstraint(
            subject="fizik",
            topic="fizik_mekanik",
            min_questions=1,
            max_questions=2,
            priority=0.8,
        ),
    ]


# ==================== SUBTASK 62.1: Content Balancing Tests ====================


class TestContentBalancing:
    """Content balancing testleri"""

    def test_apply_content_balancing(
        self, optimizer, sample_questions, content_constraints
    ):
        """
        REQ-49.53: Topic distribution constraints
        REQ-49.54: Curriculum alignment
        REQ-49.55: Balanced difficulty distribution
        REQ-49.56: Minimum soru sayısı garantisi
        """
        current_coverage = {}

        result = optimizer.apply_content_balancing(
            sample_questions, content_constraints, current_coverage
        )

        # Sonuç döndü mü?
        assert len(result) == len(sample_questions)

        # Her soruda content_balance_score var mı?
        for question in result:
            assert "content_balance_score" in question
            assert 0.0 <= question["content_balance_score"] <= 2.0
            assert "topic_score" in question
            assert "difficulty_score" in question
            assert "curriculum_score" in question

    def test_topic_balance_score_deficit(self, optimizer, content_constraints):
        """Eksik konular için yüksek skor (REQ-49.56)"""
        current_coverage = {"matematik_algebra": 0}  # Minimum 2 gerekli

        score = optimizer._calculate_topic_balance_score(
            "matematik_algebra", current_coverage, content_constraints
        )

        # Eksik konu için yüksek skor
        assert score > 0.7

    def test_topic_balance_score_satisfied(self, optimizer, content_constraints):
        """Yeterli konular için orta skor"""
        current_coverage = {"matematik_algebra": 3}  # 2-5 arası, yeterli

        score = optimizer._calculate_topic_balance_score(
            "matematik_algebra", current_coverage, content_constraints
        )

        # Yeterli konu için orta skor
        assert 0.2 <= score <= 0.6

    def test_topic_balance_score_exceeded(self, optimizer, content_constraints):
        """Maksimum aşılmış konular için düşük skor"""
        current_coverage = {"matematik_algebra": 6}  # Maksimum 5

        score = optimizer._calculate_topic_balance_score(
            "matematik_algebra", current_coverage, content_constraints
        )

        # Aşılmış konu için düşük skor
        assert score < 0.2

    def test_difficulty_balance_score(self, optimizer):
        """
        REQ-49.55: Balanced difficulty distribution
        Hedef: %30 kolay, %50 orta, %20 zor
        """
        # Hiç soru yok, hedef dağılıma göre skor
        current_coverage = {}

        easy_score = optimizer._calculate_difficulty_balance_score(
            "easy", current_coverage
        )
        medium_score = optimizer._calculate_difficulty_balance_score(
            "medium", current_coverage
        )
        hard_score = optimizer._calculate_difficulty_balance_score(
            "hard", current_coverage
        )

        # İlk sorular için hedef dağılıma göre skor
        assert easy_score == 0.30
        assert medium_score == 0.50
        assert hard_score == 0.20

    def test_curriculum_alignment_score(self, optimizer):
        """REQ-49.54: Curriculum alignment"""
        # Tam uyumlu soru
        question_full = {
            "is_meb_aligned": True,
            "meb_standard_id": "MAT-9-1",
            "osym_format_compliant": True,
        }

        score_full = optimizer._calculate_curriculum_alignment_score(question_full)
        assert score_full == 1.0

        # Kısmi uyumlu soru
        question_partial = {"is_meb_aligned": True, "osym_format_compliant": False}

        score_partial = optimizer._calculate_curriculum_alignment_score(
            question_partial
        )
        assert 0.4 <= score_partial < 1.0

        # Uyumsuz soru
        question_none = {}

        score_none = optimizer._calculate_curriculum_alignment_score(question_none)
        assert score_none == 0.0

    def test_enforce_content_constraints_success(
        self, optimizer, sample_questions, content_constraints
    ):
        """REQ-49.56: Content constraints başarılı"""
        # Kısıtları karşılayan seçim
        selected = [
            sample_questions[0],  # matematik_algebra
            sample_questions[2],  # matematik_algebra
            sample_questions[1],  # matematik_geometri
            sample_questions[3],  # fizik_mekanik
        ]

        result = optimizer.enforce_content_constraints(selected, content_constraints)
        assert result is True

    def test_enforce_content_constraints_failure(
        self, optimizer, sample_questions, content_constraints
    ):
        """REQ-49.56: Content constraints başarısız"""
        # Kısıtları karşılamayan seçim (matematik_algebra eksik)
        selected = [
            sample_questions[1],  # matematik_geometri
            sample_questions[3],  # fizik_mekanik
        ]

        result = optimizer.enforce_content_constraints(selected, content_constraints)
        assert result is False


# ==================== SUBTASK 62.2: Exposure Control Tests ====================


class TestExposureControl:
    """Exposure control testleri"""

    def test_track_item_exposure(self, optimizer):
        """REQ-49.57: Item exposure rate tracking"""
        question_id = "q1"

        # İlk maruz kalma
        record1 = optimizer.track_item_exposure(question_id, test_count=10)
        assert record1.total_exposures == 1
        assert record1.total_tests == 10
        assert record1.exposure_rate == 0.1

        # İkinci maruz kalma
        record2 = optimizer.track_item_exposure(question_id, test_count=10)
        assert record2.total_exposures == 2
        assert record2.total_tests == 20
        assert record2.exposure_rate == 0.1

    def test_sympson_hetter_method(self, optimizer, sample_questions):
        """REQ-49.58: Sympson-Hetter method"""
        # Bazı soruları maruz bırak
        optimizer.track_item_exposure("q1", test_count=100)
        optimizer.track_item_exposure("q2", test_count=100)

        result = optimizer.apply_sympson_hetter_method(
            sample_questions, target_exposure_rate=0.2
        )

        # Her soruda exposure bilgisi var mı?
        for question in result:
            assert "exposure_rate" in question
            assert "control_probability" in question
            assert "exposure_penalty" in question
            assert 0.1 <= question["control_probability"] <= 1.0

    def test_sympson_hetter_probability(self, optimizer):
        """Sympson-Hetter probability hesaplama"""
        # Hiç kullanılmamış
        prob_new = optimizer._calculate_sympson_hetter_probability(0.0, 0.2, 5)
        assert prob_new == 1.0

        # Hedef oranın altında
        prob_low = optimizer._calculate_sympson_hetter_probability(0.1, 0.2, 5)
        assert prob_low > 0.5

        # Hedef oranın üstünde
        prob_high = optimizer._calculate_sympson_hetter_probability(0.3, 0.2, 5)
        assert prob_high < 0.5

    def test_rotate_item_pool(self, optimizer, sample_questions):
        """REQ-49.59: Item pool rotation"""
        # Aktif rotasyon grupları: 0, 1, 2
        active_groups = {0, 1, 2}

        result = optimizer.rotate_item_pool(sample_questions, active_groups)

        # Sadece aktif gruplardaki sorular
        assert len(result) <= len(sample_questions)
        for question in result:
            assert question["is_active_rotation"] is True
            assert question["rotation_group"] in active_groups

    def test_disable_overexposed_items(self, optimizer, sample_questions):
        """REQ-49.60: Overexposed items devre dışı bırakma"""
        # q1'i aşırı maruz bırak - her test sonrası test_count ile çağır
        # Her çağrı için test_count=1 kullan, böylece rate = exposures/total_tests olur
        for _ in range(30):
            optimizer.track_item_exposure("q1", test_count=1)

        result = optimizer.disable_overexposed_items(
            sample_questions, max_exposure_rate=0.2  # %20 max
        )

        # q1'in exposure rate'i 30/30 = 1.0 (100%) olmalı, 0.2'den büyük
        # Bu yüzden filtrelenmeli
        result_ids = [q["id"] for q in result]
        assert "q1" not in result_ids
        assert len(result) < len(sample_questions)

    def test_get_exposure_statistics(self, optimizer):
        """Exposure istatistikleri"""
        # Bazı soruları maruz bırak
        optimizer.track_item_exposure("q1", test_count=100)
        optimizer.track_item_exposure("q2", test_count=100)
        optimizer.track_item_exposure("q3", test_count=100)

        stats = optimizer.get_exposure_statistics()

        assert stats["total_items"] == 3
        assert stats["avg_exposure_rate"] > 0
        assert stats["max_exposure_rate"] >= stats["avg_exposure_rate"]


# ==================== SUBTASK 62.3: ZPD Selection Tests ====================


class TestZPDSelection:
    """ZPD içinde soru seçimi testleri"""

    def test_select_within_zpd(self, optimizer, sample_questions):
        """
        REQ-49.61: Zone of Proximal Development targeting
        REQ-49.64: Theta ± 1 aralığında soru seçme
        """
        student_theta = 0.0

        result = optimizer.select_within_zpd(
            sample_questions, student_theta, zpd_range=1.0
        )

        # ZPD içindeki sorular (-1.0 ile +1.0 arası)
        for question in result:
            assert question["is_in_zpd"] is True
            assert "challenge_score" in question
            assert "difficulty_distance" in question
            difficulty = question["difficulty_b"]
            assert -1.0 <= difficulty <= 1.0

    def test_calculate_challenge_score(self, optimizer):
        """REQ-49.62: Optimal challenge level"""
        student_theta = 0.0

        # Optimal zorluk (theta + 0.5)
        score_optimal = optimizer._calculate_challenge_score(0.5, student_theta)

        # Çok kolay
        score_easy = optimizer._calculate_challenge_score(-1.0, student_theta)

        # Çok zor
        score_hard = optimizer._calculate_challenge_score(2.0, student_theta)

        # Optimal en yüksek skora sahip olmalı
        assert score_optimal > score_easy
        assert score_optimal > score_hard

    def test_prevent_frustration(self, optimizer, sample_questions):
        """REQ-49.63: Frustration prevention"""
        student_theta = 0.0

        result = optimizer.prevent_frustration(
            sample_questions, student_theta, frustration_threshold=2.0
        )

        # Çok zor sorular filtrelenmeli
        for question in result:
            assert question["frustration_prevented"] is True
            difficulty = question["difficulty_b"]
            assert difficulty <= student_theta + 2.0

    def test_adjust_zpd_range(self, optimizer):
        """REQ-49.62: ZPD aralığı ayarlama"""
        current_range = 1.0

        # Yüksek başarı -> aralık genişler
        performance_high = {"accuracy": 0.85, "response_time_avg": 45.0}
        adjusted_high = optimizer.adjust_zpd_range(performance_high, current_range)
        assert adjusted_high > current_range

        # Düşük başarı -> aralık daralır
        performance_low = {"accuracy": 0.35, "response_time_avg": 90.0}
        adjusted_low = optimizer.adjust_zpd_range(performance_low, current_range)
        assert adjusted_low < current_range

        # Orta başarı -> aralık değişmez
        performance_mid = {"accuracy": 0.60, "response_time_avg": 60.0}
        adjusted_mid = optimizer.adjust_zpd_range(performance_mid, current_range)
        assert adjusted_mid == current_range


# ==================== SUBTASK 62.4: Spacing Effect Tests ====================


class TestSpacingEffect:
    """Spacing effect testleri"""

    def test_apply_spacing_effect(self, optimizer, sample_questions):
        """
        REQ-49.65: Spaced repetition integration
        REQ-49.66: FSRS algoritması
        REQ-49.67: Forgetting curve
        REQ-49.68: 1-3-7-14-30 gün aralıkları
        """
        student_id = "student1"

        result = optimizer.apply_spacing_effect(sample_questions, student_id)

        # Her soruda spacing bilgisi var mı?
        for question in result:
            assert "is_due_for_review" in question
            assert "forgetting_score" in question
            assert "spacing_priority" in question
            assert "next_review" in question
            assert "review_count" in question
            assert "interval_days" in question

    def test_create_initial_schedule(self, optimizer):
        """İlk schedule oluşturma (REQ-49.68)"""
        current_time = datetime.now()

        schedule = optimizer._create_initial_schedule("q1", "student1", current_time)

        # İlk interval 1 gün olmalı
        assert schedule.interval_days == 1
        assert schedule.review_count == 0
        assert schedule.ease_factor == 2.5
        assert schedule.next_review == current_time + timedelta(days=1)

    def test_update_spacing_schedule_correct(self, optimizer):
        """Doğru yanıt ile schedule güncelleme (REQ-49.66)"""
        student_id = "student1"
        question_id = "q1"
        current_time = datetime.now()

        # İlk schedule oluştur ve 3 günlük interval ver
        initial = optimizer._create_initial_schedule(
            question_id, student_id, current_time
        )
        initial.interval_days = 3  # 3 günlük interval
        initial.next_review = current_time + timedelta(days=3)
        optimizer.spaced_schedules[(student_id, question_id)] = initial

        # Doğru yanıt ile güncelle
        updated = optimizer.update_spacing_schedule(
            student_id,
            question_id,
            is_correct=True,
            response_quality=0.8,
            current_time=current_time,
        )

        # Interval artmalı (3 günden daha fazla olmalı)
        assert updated.interval_days >= initial.interval_days
        assert updated.review_count == 1
        assert updated.ease_factor >= initial.ease_factor

    def test_update_spacing_schedule_incorrect(self, optimizer):
        """Yanlış yanıt ile schedule güncelleme"""
        student_id = "student1"
        question_id = "q1"
        current_time = datetime.now()

        # Schedule oluştur
        initial = optimizer._create_initial_schedule(
            question_id, student_id, current_time
        )
        initial.interval_days = 7  # 7 günlük interval
        initial.ease_factor = 2.5  # Başlangıç ease factor
        optimizer.spaced_schedules[(student_id, question_id)] = initial

        # Yanlış yanıt ile güncelle
        updated = optimizer.update_spacing_schedule(
            student_id,
            question_id,
            is_correct=False,
            response_quality=0.2,
            current_time=current_time,
        )

        # Interval sıfırlanmalı (1 gün)
        assert updated.interval_days == 1
        # Ease factor azalmalı (2.5 - 0.2 = 2.3)
        assert updated.ease_factor <= initial.ease_factor

    def test_snap_to_spacing_intervals(self, optimizer):
        """Interval'i spacing_intervals'e yaklaştırma (REQ-49.68)"""
        # 1-3-7-14-30 gün aralıkları
        assert optimizer._snap_to_spacing_intervals(2) == 1
        assert optimizer._snap_to_spacing_intervals(5) == 3
        assert optimizer._snap_to_spacing_intervals(10) == 7
        assert optimizer._snap_to_spacing_intervals(20) == 14
        assert optimizer._snap_to_spacing_intervals(40) == 30
        assert optimizer._snap_to_spacing_intervals(100) == 30  # Maksimum

    def test_calculate_forgetting_score(self, optimizer):
        """Forgetting curve skoru (REQ-49.67)"""
        current_time = datetime.now()

        # Yeni review
        schedule_new = SpacedRepetitionSchedule(
            question_id="q1",
            student_id="student1",
            last_review=current_time,
            next_review=current_time + timedelta(days=1),
            interval_days=1,
            ease_factor=2.5,
        )

        score_new = optimizer._calculate_forgetting_score(schedule_new, current_time)
        assert score_new < 0.2  # Az unutulmuş

        # Eski review
        schedule_old = SpacedRepetitionSchedule(
            question_id="q1",
            student_id="student1",
            last_review=current_time - timedelta(days=30),
            next_review=current_time,
            interval_days=1,
            ease_factor=2.5,
        )

        score_old = optimizer._calculate_forgetting_score(schedule_old, current_time)
        assert score_old > 0.5  # Çok unutulmuş

    def test_get_due_reviews(self, optimizer):
        """Tekrar zamanı gelmiş sorular (REQ-49.65)"""
        student_id = "student1"
        current_time = datetime.now()

        # Bazı schedule'lar oluştur
        schedule1 = SpacedRepetitionSchedule(
            question_id="q1",
            student_id=student_id,
            last_review=current_time - timedelta(days=2),
            next_review=current_time - timedelta(days=1),  # Geçmiş
            interval_days=1,
        )

        schedule2 = SpacedRepetitionSchedule(
            question_id="q2",
            student_id=student_id,
            last_review=current_time,
            next_review=current_time + timedelta(days=1),  # Gelecek
            interval_days=1,
        )

        optimizer.spaced_schedules[(student_id, "q1")] = schedule1
        optimizer.spaced_schedules[(student_id, "q2")] = schedule2

        due = optimizer.get_due_reviews(student_id, current_time)

        # Sadece q1 tekrar zamanı gelmiş
        assert "q1" in due
        assert "q2" not in due

    def test_get_spacing_statistics(self, optimizer):
        """Spacing istatistikleri"""
        student_id = "student1"
        current_time = datetime.now()

        # Bazı schedule'lar oluştur
        for i in range(3):
            schedule = SpacedRepetitionSchedule(
                question_id=f"q{i}",
                student_id=student_id,
                last_review=current_time,
                next_review=current_time + timedelta(days=i + 1),
                interval_days=i + 1,
                review_count=i,
                ease_factor=2.5,
            )
            optimizer.spaced_schedules[(student_id, f"q{i}")] = schedule

        stats = optimizer.get_spacing_statistics(student_id)

        assert stats["total_items"] == 3
        assert stats["avg_interval"] > 0
        assert stats["avg_review_count"] >= 0
        assert stats["avg_ease_factor"] == 2.5
