"""
ÖSYM Puan Hesaplama Sistemi Testleri
"""

import pytest

from services.osym_scoring_system import (
    OSYMScoringSystem,
    ScoreType,
    SubjectNet,
    ExamNetScores,
    OSYMScore,
    PlacementScore,
    RankingEstimate,
)


class TestOSYMScoringSystem:
    """ÖSYM Puan Hesaplama Sistemi test sınıfı"""

    @pytest.fixture
    def scoring_system(self):
        """Scoring system fixture"""
        return OSYMScoringSystem()

    # Test 68.2: Net sayısı hesaplama
    def test_calculate_net_score_basic(self, scoring_system):
        """Temel net hesaplama testi"""
        # Doğru - (Yanlış / 4)
        net = scoring_system.calculate_net_score(correct=30, wrong=8, empty=2)
        expected = 30 - (8 / 4)  # 30 - 2 = 28
        assert net == expected

    def test_calculate_net_score_no_wrong(self, scoring_system):
        """Yanlış olmadan net hesaplama"""
        net = scoring_system.calculate_net_score(correct=40, wrong=0, empty=0)
        assert net == 40.0

    def test_calculate_net_score_all_wrong(self, scoring_system):
        """Tüm yanlış net hesaplama"""
        net = scoring_system.calculate_net_score(correct=0, wrong=40, empty=0)
        # Net negatif olamaz, 0 olmalı
        assert net == 0.0

    def test_calculate_net_score_negative_prevented(self, scoring_system):
        """Negatif net önleme testi"""
        net = scoring_system.calculate_net_score(correct=5, wrong=30, empty=5)
        # 5 - (30/4) = 5 - 7.5 = -2.5, ama 0 olmalı
        assert net == 0.0

    def test_calculate_subject_nets(self, scoring_system):
        """Ders bazlı net hesaplama testi"""
        subject_results = {
            "TURKCE": {"correct": 30, "wrong": 8, "empty": 2},
            "MATEMATIK": {"correct": 25, "wrong": 10, "empty": 5},
            "FEN": {"correct": 15, "wrong": 3, "empty": 2},
            "SOSYAL": {"correct": 18, "wrong": 2, "empty": 0},
        }

        subject_nets = scoring_system.calculate_subject_nets(subject_results)

        assert len(subject_nets) == 4

        # Türkçe: 30 - (8/4) = 28
        turkce_net = next(sn for sn in subject_nets if sn.subject == "TURKCE")
        assert turkce_net.net == 28.0
        assert turkce_net.correct == 30
        assert turkce_net.wrong == 8

        # Matematik: 25 - (10/4) = 22.5
        matematik_net = next(sn for sn in subject_nets if sn.subject == "MATEMATIK")
        assert matematik_net.net == 22.5

    def test_calculate_exam_nets(self, scoring_system):
        """Sınav toplam net hesaplama testi"""
        subject_results = {
            "TURKCE": {"correct": 30, "wrong": 8, "empty": 2},
            "MATEMATIK": {"correct": 25, "wrong": 10, "empty": 5},
            "FEN": {"correct": 15, "wrong": 3, "empty": 2},
            "SOSYAL": {"correct": 18, "wrong": 2, "empty": 0},
        }

        exam_nets = scoring_system.calculate_exam_nets("TYT", subject_results)

        assert exam_nets.exam_type == "TYT"
        assert exam_nets.total_correct == 88
        assert exam_nets.total_wrong == 23
        assert exam_nets.total_empty == 9

        # Toplam net: 28 + 22.5 + 14.25 + 17.5 = 82.25
        expected_total_net = 28.0 + 22.5 + 14.25 + 17.5
        assert abs(exam_nets.total_net - expected_total_net) < 0.01

    # Test 68.1: ÖSYM puan hesaplama formülü
    def test_calculate_raw_score_tyt(self, scoring_system):
        """TYT ham puan hesaplama testi"""
        subject_nets = [
            SubjectNet("TURKCE", 30, 8, 2, 28.0),
            SubjectNet("MATEMATIK", 25, 10, 5, 22.5),
            SubjectNet("FEN", 15, 3, 2, 14.25),
            SubjectNet("SOSYAL", 18, 2, 0, 17.5),
        ]

        raw_score = scoring_system.calculate_raw_score(
            subject_nets, scoring_system.tyt_coefficients
        )

        # Tüm katsayılar 3.0
        # Ağırlıklı toplam = (28*3 + 22.5*3 + 14.25*3 + 17.5*3) = 246.75
        # Katsayı toplamı = 12
        # Ham puan = (246.75 / 12) * 5 = 102.8125
        expected = ((28.0 + 22.5 + 14.25 + 17.5) * 3.0 / 12.0) * 5.0
        assert abs(raw_score - expected) < 0.01

    def test_calculate_raw_score_ayt_sayisal(self, scoring_system):
        """AYT Sayısal ham puan hesaplama testi"""
        subject_nets = [
            SubjectNet("MATEMATIK", 35, 4, 1, 34.0),
            SubjectNet("FIZIK", 12, 1, 1, 11.75),
            SubjectNet("KIMYA", 11, 2, 0, 10.5),
            SubjectNet("BIYOLOJI", 10, 2, 1, 9.5),
        ]

        raw_score = scoring_system.calculate_raw_score(
            subject_nets, scoring_system.ayt_sayisal_coefficients
        )

        # Matematik: 34 * 5 = 170
        # Fizik: 11.75 * 4 = 47
        # Kimya: 10.5 * 3 = 31.5
        # Biyoloji: 9.5 * 3 = 28.5
        # Toplam: 277
        # Katsayı toplamı: 15
        # Ham puan: (277 / 15) * 5 = 92.33
        assert raw_score > 0
        assert raw_score <= 500

    def test_calculate_osym_score_sayisal(self, scoring_system):
        """Sayısal ÖSYM puanı hesaplama testi"""
        tyt_results = {
            "TURKCE": {"correct": 30, "wrong": 8, "empty": 2},
            "MATEMATIK": {"correct": 35, "wrong": 4, "empty": 1},
            "FEN": {"correct": 18, "wrong": 2, "empty": 0},
            "SOSYAL": {"correct": 16, "wrong": 3, "empty": 1},
        }

        ayt_results = {
            "MATEMATIK": {"correct": 35, "wrong": 4, "empty": 1},
            "FIZIK": {"correct": 12, "wrong": 1, "empty": 1},
            "KIMYA": {"correct": 11, "wrong": 2, "empty": 0},
            "BIYOLOJI": {"correct": 10, "wrong": 2, "empty": 1},
        }

        osym_score = scoring_system.calculate_osym_score(
            ScoreType.SAY, tyt_results, ayt_results
        )

        assert osym_score.score_type == ScoreType.SAY
        assert osym_score.tyt_score > 0
        assert osym_score.ayt_score > 0
        assert osym_score.weighted_score > 0

        # TYT %40, AYT %60 ağırlıklı
        expected_weighted = (osym_score.tyt_score * 0.4) + (osym_score.ayt_score * 0.6)
        assert abs(osym_score.weighted_score - expected_weighted) < 0.01

    def test_calculate_osym_score_sozel(self, scoring_system):
        """Sözel ÖSYM puanı hesaplama testi"""
        tyt_results = {
            "TURKCE": {"correct": 38, "wrong": 2, "empty": 0},
            "MATEMATIK": {"correct": 25, "wrong": 10, "empty": 5},
            "FEN": {"correct": 15, "wrong": 3, "empty": 2},
            "SOSYAL": {"correct": 18, "wrong": 2, "empty": 0},
        }

        ayt_results = {
            "EDEBIYAT": {"correct": 22, "wrong": 2, "empty": 0},
            "TARIH_1": {"correct": 9, "wrong": 1, "empty": 0},
            "COGRAFYA_1": {"correct": 5, "wrong": 1, "empty": 0},
            "TARIH_2": {"correct": 10, "wrong": 1, "empty": 0},
            "COGRAFYA_2": {"correct": 10, "wrong": 1, "empty": 0},
            "FELSEFE": {"correct": 11, "wrong": 1, "empty": 0},
            "DIN": {"correct": 5, "wrong": 1, "empty": 0},
        }

        osym_score = scoring_system.calculate_osym_score(
            ScoreType.SOZ, tyt_results, ayt_results
        )

        assert osym_score.score_type == ScoreType.SOZ
        assert osym_score.tyt_score > 0
        assert osym_score.ayt_score > 0

    def test_calculate_osym_score_dil(self, scoring_system):
        """Dil ÖSYM puanı hesaplama testi"""
        tyt_results = {
            "TURKCE": {"correct": 35, "wrong": 4, "empty": 1},
            "MATEMATIK": {"correct": 30, "wrong": 8, "empty": 2},
            "FEN": {"correct": 16, "wrong": 3, "empty": 1},
            "SOSYAL": {"correct": 17, "wrong": 2, "empty": 1},
        }

        ydt_results = {
            "INGILIZCE": {"correct": 70, "wrong": 8, "empty": 2},
        }

        osym_score = scoring_system.calculate_osym_score(
            ScoreType.DIL, tyt_results, ydt_subject_results=ydt_results
        )

        assert osym_score.score_type == ScoreType.DIL
        assert osym_score.tyt_score > 0
        assert osym_score.ydt_score > 0
        assert osym_score.ayt_score == 0.0  # Dil puanında AYT yok

    # Test 68.3: Yerleştirme puanı tahmini
    def test_calculate_placement_score(self, scoring_system):
        """Yerleştirme puanı hesaplama testi"""
        osym_score = OSYMScore(
            score_type=ScoreType.SAY,
            raw_score=400.0,
            weighted_score=400.0,
            tyt_score=380.0,
            ayt_score=410.0,
            ydt_score=0.0,
            obp_contribution=0.0,
            total_score=400.0,
        )

        obp = 85.0  # Diploma notu

        placement_score = scoring_system.calculate_placement_score(osym_score, obp)

        assert placement_score.score_type == ScoreType.SAY
        assert placement_score.base_score == 400.0

        # OBP katkısı: 85 * 0.12 = 10.2
        expected_obp_bonus = 85.0 * 0.12
        assert abs(placement_score.obp_bonus - expected_obp_bonus) < 0.01

        # Toplam: 400 + 10.2 = 410.2
        expected_total = 400.0 + expected_obp_bonus
        assert abs(placement_score.total_placement_score - expected_total) < 0.01

    def test_calculate_placement_score_with_bonus(self, scoring_system):
        """Ek puanlı yerleştirme puanı testi"""
        osym_score = OSYMScore(
            score_type=ScoreType.EA,
            raw_score=350.0,
            weighted_score=350.0,
            tyt_score=340.0,
            ayt_score=355.0,
            ydt_score=0.0,
            obp_contribution=0.0,
            total_score=350.0,
        )

        obp = 90.0
        additional_bonus = 5.0  # Engelli puanı

        placement_score = scoring_system.calculate_placement_score(
            osym_score, obp, additional_bonus
        )

        # OBP: 90 * 0.12 = 10.8
        # Toplam: 350 + 10.8 + 5 = 365.8
        expected_total = 350.0 + (90.0 * 0.12) + 5.0
        assert abs(placement_score.total_placement_score - expected_total) < 0.01
        assert placement_score.additional_bonus == 5.0

    def test_placement_score_minimum_check(self, scoring_system):
        """Minimum yerleştirme puanı kontrolü"""
        osym_score = OSYMScore(
            score_type=ScoreType.SAY,
            raw_score=170.0,
            weighted_score=170.0,
            tyt_score=160.0,
            ayt_score=175.0,
            ydt_score=0.0,
            obp_contribution=0.0,
            total_score=170.0,
        )

        obp = 70.0

        placement_score = scoring_system.calculate_placement_score(osym_score, obp)

        # 170 + (70 * 0.12) = 178.4 < 180 (minimum)
        assert placement_score.total_placement_score < 180.0
        assert placement_score.min_required_score == 180.0

    # Test 68.4: Sıralama tahmini
    def test_estimate_ranking(self, scoring_system):
        """Sıralama tahmini testi"""
        placement_score = PlacementScore(
            score_type=ScoreType.SAY,
            base_score=400.0,
            obp_bonus=10.2,
            additional_bonus=0.0,
            total_placement_score=410.2,
            min_required_score=180.0,
        )

        ranking = scoring_system.estimate_ranking(placement_score)

        assert ranking.score_type == ScoreType.SAY
        assert ranking.placement_score == 410.2
        assert ranking.estimated_rank > 0
        assert 0 <= ranking.percentile <= 100
        assert ranking.total_candidates > 0
        assert 0 <= ranking.confidence_level <= 1.0

    def test_estimate_ranking_high_score(self, scoring_system):
        """Yüksek puan sıralama tahmini"""
        placement_score = PlacementScore(
            score_type=ScoreType.SAY,
            base_score=480.0,
            obp_bonus=12.0,
            additional_bonus=0.0,
            total_placement_score=492.0,
            min_required_score=180.0,
        )

        ranking = scoring_system.estimate_ranking(placement_score)

        # Yüksek puan = düşük sıralama
        assert ranking.estimated_rank < ranking.total_candidates / 10
        # Yüksek yüzdelik dilim
        assert ranking.percentile > 90.0

    def test_estimate_ranking_low_score(self, scoring_system):
        """Düşük puan sıralama tahmini"""
        placement_score = PlacementScore(
            score_type=ScoreType.SAY,
            base_score=200.0,
            obp_bonus=8.4,
            additional_bonus=0.0,
            total_placement_score=208.4,
            min_required_score=180.0,
        )

        ranking = scoring_system.estimate_ranking(placement_score)

        # Düşük puan = yüksek sıralama
        assert ranking.estimated_rank > ranking.total_candidates / 2
        # Düşük yüzdelik dilim
        assert ranking.percentile < 50.0

    def test_program_specific_score(self, scoring_system):
        """Program özel puan hesaplama testi"""
        placement_score = PlacementScore(
            score_type=ScoreType.SAY,
            base_score=400.0,
            obp_bonus=10.2,
            additional_bonus=0.0,
            total_placement_score=410.2,
            min_required_score=180.0,
        )

        # Tıp fakültesi için özel katsayılar (örnek)
        program_coefficients = {
            "TURKCE": 3.0,
            "MATEMATIK": 5.0,
            "FEN": 6.0,  # Fen dersleri daha ağırlıklı
            "SOSYAL": 2.0,
        }

        tyt_results = {
            "TURKCE": {"correct": 30, "wrong": 8, "empty": 2},
            "MATEMATIK": {"correct": 35, "wrong": 4, "empty": 1},
            "FEN": {"correct": 18, "wrong": 2, "empty": 0},
            "SOSYAL": {"correct": 16, "wrong": 3, "empty": 1},
        }

        program_score = scoring_system.calculate_program_specific_score(
            placement_score, program_coefficients, tyt_results
        )

        assert program_score > 0
        assert program_score <= 500

    def test_get_score_analysis(self, scoring_system):
        """Puan analizi raporu testi"""
        osym_score = OSYMScore(
            score_type=ScoreType.SAY,
            raw_score=400.0,
            weighted_score=400.0,
            tyt_score=380.0,
            ayt_score=410.0,
            ydt_score=0.0,
            obp_contribution=10.2,
            total_score=410.2,
        )

        placement_score = PlacementScore(
            score_type=ScoreType.SAY,
            base_score=400.0,
            obp_bonus=10.2,
            additional_bonus=0.0,
            total_placement_score=410.2,
            min_required_score=180.0,
        )

        ranking = RankingEstimate(
            score_type=ScoreType.SAY,
            placement_score=410.2,
            estimated_rank=25000,
            percentile=95.0,
            total_candidates=500000,
            confidence_level=0.85,
        )

        analysis = scoring_system.get_score_analysis(
            osym_score, placement_score, ranking
        )

        assert "timestamp" in analysis
        assert "score_type" in analysis
        assert "scores" in analysis
        assert "ranking" in analysis
        assert "bonuses" in analysis
        assert "status" in analysis

        assert analysis["scores"]["tyt"] == 380.0
        assert analysis["scores"]["ayt"] == 410.0
        assert analysis["scores"]["placement"] == 410.2

        assert analysis["ranking"]["estimated_rank"] == 25000
        assert analysis["ranking"]["percentile"] == 95.0

        assert analysis["status"]["meets_minimum_tyt"] == True
        assert analysis["status"]["meets_minimum_placement"] == True

    def test_edge_case_zero_questions(self, scoring_system):
        """Sıfır soru edge case testi"""
        net = scoring_system.calculate_net_score(0, 0, 0)
        assert net == 0.0

    def test_edge_case_perfect_score(self, scoring_system):
        """Mükemmel puan edge case testi"""
        tyt_results = {
            "TURKCE": {"correct": 40, "wrong": 0, "empty": 0},
            "MATEMATIK": {"correct": 40, "wrong": 0, "empty": 0},
            "FEN": {"correct": 20, "wrong": 0, "empty": 0},
            "SOSYAL": {"correct": 20, "wrong": 0, "empty": 0},
        }

        exam_nets = scoring_system.calculate_exam_nets("TYT", tyt_results)

        assert exam_nets.total_correct == 120
        assert exam_nets.total_wrong == 0
        assert exam_nets.total_net == 120.0

    def test_edge_case_all_empty(self, scoring_system):
        """Tüm boş edge case testi"""
        tyt_results = {
            "TURKCE": {"correct": 0, "wrong": 0, "empty": 40},
            "MATEMATIK": {"correct": 0, "wrong": 0, "empty": 40},
            "FEN": {"correct": 0, "wrong": 0, "empty": 20},
            "SOSYAL": {"correct": 0, "wrong": 0, "empty": 20},
        }

        exam_nets = scoring_system.calculate_exam_nets("TYT", tyt_results)

        assert exam_nets.total_correct == 0
        assert exam_nets.total_wrong == 0
        assert exam_nets.total_empty == 120
        assert exam_nets.total_net == 0.0
