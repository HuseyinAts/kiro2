"""
ÖSYM Puan Hesaplama Sistemi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül ÖSYM'nin resmi puan hesaplama formüllerini uygular:
- Net sayısı hesaplama (Doğru - Yanlış/4)
- Ham puan hesaplama (katsayılı puanlama)
- Yerleştirme puanı tahmini (OBP + YKS puanı)
- Sıralama tahmini (geçmiş yıl verileri ile)

Requirements: REQ-1.4, REQ-1.5
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from core.structured_logger import get_logger

logger = get_logger("osym_scoring_system")


class ScoreType(Enum):
    """Puan türleri"""

    TYT = "tyt"  # Temel Yeterlilik Testi
    SAY = "say"  # Sayısal (AYT)
    EA = "ea"  # Eşit Ağırlık (AYT)
    SOZ = "soz"  # Sözel (AYT)
    DIL = "dil"  # Dil (YDT)


@dataclass
class SubjectNet:
    """Ders bazlı net sayısı"""

    subject: str
    correct: int
    wrong: int
    empty: int
    net: float


@dataclass
class ExamNetScores:
    """Sınav net skorları"""

    exam_type: str
    subject_nets: list[SubjectNet]
    total_net: float
    total_correct: int
    total_wrong: int
    total_empty: int


@dataclass
class OSYMScore:
    """ÖSYM puanı"""

    score_type: ScoreType
    raw_score: float  # Ham puan (0-500 arası)
    weighted_score: float  # Katsayılı puan
    tyt_score: float  # TYT puanı
    ayt_score: float  # AYT puanı (varsa)
    ydt_score: float  # YDT puanı (varsa)
    obp_contribution: float  # OBP katkısı (0.12 * OBP)
    total_score: float  # Toplam yerleştirme puanı


@dataclass
class PlacementScore:
    """Yerleştirme puanı"""

    score_type: ScoreType
    base_score: float  # Temel puan (TYT + AYT)
    obp_bonus: float  # Diploma notu bonusu
    additional_bonus: float  # Ek puanlar (engelli, vb.)
    total_placement_score: float  # Toplam yerleştirme puanı
    min_required_score: float  # Minimum gerekli puan (180)


@dataclass
class RankingEstimate:
    """Sıralama tahmini"""

    score_type: ScoreType
    placement_score: float
    estimated_rank: int  # Tahmini sıralama
    percentile: float  # Yüzdelik dilim
    total_candidates: int  # Toplam aday sayısı
    confidence_level: float  # Tahmin güven seviyesi (0-1)


class OSYMScoringSystem:
    """
    ÖSYM Puan Hesaplama Sistemi

    Bu sınıf ÖSYM'nin resmi puan hesaplama formüllerini uygular.

    Formüller:
    - Net = Doğru - (Yanlış / 4)
    - Ham Puan = Σ(Net * Katsayı) / Σ(Katsayı) * 5
    - Yerleştirme Puanı = (TYT * 0.4) + (AYT * 0.6) + (OBP * 0.12)
    """

    def __init__(self):
        # ÖSYM 2024-2025 resmi katsayıları
        # Kaynak: ÖSYM Yükseköğretim Programları ve Kontenjanları Kılavuzu

        # TYT Katsayıları (Toplam: 120 soru)
        self.tyt_coefficients = {
            "TURKCE": 3.0,  # 40 soru
            "MATEMATIK": 3.0,  # 40 soru
            "FEN": 3.0,  # 20 soru (Fizik, Kimya, Biyoloji)
            "SOSYAL": 3.0,  # 20 soru (Tarih, Coğrafya, Felsefe)
        }

        # AYT Sayısal Katsayıları
        self.ayt_sayisal_coefficients = {
            "MATEMATIK": 5.0,  # 40 soru
            "FIZIK": 4.0,  # 14 soru
            "KIMYA": 3.0,  # 13 soru
            "BIYOLOJI": 3.0,  # 13 soru
        }

        # AYT Sözel Katsayıları
        self.ayt_sozel_coefficients = {
            "EDEBIYAT": 5.0,  # 24 soru
            "TARIH_1": 4.0,  # 10 soru
            "COGRAFYA_1": 4.0,  # 6 soru
            "TARIH_2": 4.0,  # 11 soru
            "COGRAFYA_2": 4.0,  # 11 soru
            "FELSEFE": 4.0,  # 12 soru
            "DIN": 4.0,  # 6 soru
        }

        # YDT Katsayıları
        self.ydt_coefficients = {
            "INGILIZCE": 5.0,  # 80 soru
            "ALMANCA": 5.0,  # 80 soru
            "FRANSIZCA": 5.0,  # 80 soru
        }

        # Puan türü ağırlıkları (TYT + AYT kombinasyonları)
        self.score_type_weights = {
            ScoreType.SAY: {  # Sayısal
                "tyt_weight": 0.4,
                "ayt_weight": 0.6,
                "tyt_subjects": ["TURKCE", "MATEMATIK", "FEN", "SOSYAL"],
                "ayt_subjects": ["MATEMATIK", "FIZIK", "KIMYA", "BIYOLOJI"],
            },
            ScoreType.EA: {  # Eşit Ağırlık
                "tyt_weight": 0.4,
                "ayt_weight": 0.6,
                "tyt_subjects": ["TURKCE", "MATEMATIK", "FEN", "SOSYAL"],
                "ayt_subjects": ["MATEMATIK", "EDEBIYAT", "TARIH_1", "COGRAFYA_1"],
            },
            ScoreType.SOZ: {  # Sözel
                "tyt_weight": 0.4,
                "ayt_weight": 0.6,
                "tyt_subjects": ["TURKCE", "MATEMATIK", "FEN", "SOSYAL"],
                "ayt_subjects": [
                    "EDEBIYAT",
                    "TARIH_1",
                    "COGRAFYA_1",
                    "TARIH_2",
                    "COGRAFYA_2",
                    "FELSEFE",
                    "DIN",
                ],
            },
            ScoreType.DIL: {  # Dil
                "tyt_weight": 0.4,
                "ydt_weight": 0.6,
                "tyt_subjects": ["TURKCE", "MATEMATIK", "FEN", "SOSYAL"],
                "ydt_subjects": ["INGILIZCE"],  # veya ALMANCA, FRANSIZCA
            },
        }

        # Minimum puanlar
        self.min_tyt_score = 150.0  # TYT'den minimum 150 puan gerekli
        self.min_placement_score = 180.0  # Yerleştirme için minimum 180 puan

        # OBP (Ortaöğretim Başarı Puanı) katkısı
        self.obp_weight = 0.12  # OBP'nin %12'si eklenir

        # Geçmiş yıl istatistikleri (örnek veriler - gerçek verilerle güncellenecek)
        self.historical_data = {
            ScoreType.SAY: {
                "total_candidates": 500000,
                "score_distribution": self._generate_score_distribution(500000),
            },
            ScoreType.EA: {
                "total_candidates": 300000,
                "score_distribution": self._generate_score_distribution(300000),
            },
            ScoreType.SOZ: {
                "total_candidates": 400000,
                "score_distribution": self._generate_score_distribution(400000),
            },
            ScoreType.DIL: {
                "total_candidates": 100000,
                "score_distribution": self._generate_score_distribution(100000),
            },
        }

    def calculate_net_score(self, correct: int, wrong: int, empty: int = 0) -> float:
        """
        Net sayısı hesapla (ÖSYM formülü)

        Formül: Net = Doğru - (Yanlış / 4)

        Args:
            correct: Doğru cevap sayısı
            wrong: Yanlış cevap sayısı
            empty: Boş cevap sayısı (opsiyonel)

        Returns:
            float: Net sayısı

        Requirements: REQ-1.4
        """
        try:
            # ÖSYM resmi formülü: Doğru - (Yanlış / 4)
            net = correct - (wrong / 4.0)

            # Net negatif olamaz
            net = max(0.0, net)

            logger.debug(
                "Net hesaplandı",
                extra_data={
                    "correct": correct,
                    "wrong": wrong,
                    "empty": empty,
                    "net": net,
                },
            )

            return round(net, 2)

        except Exception as e:
            logger.error(f"Net hesaplama hatası: {e}")
            return 0.0

    def calculate_subject_nets(
        self, subject_results: dict[str, dict[str, int]]
    ) -> list[SubjectNet]:
        """
        Ders bazlı net sayılarını hesapla

        Args:
            subject_results: Ders bazlı sonuçlar
                {
                    "TURKCE": {"correct": 30, "wrong": 8, "empty": 2},
                    "MATEMATIK": {"correct": 25, "wrong": 10, "empty": 5},
                    ...
                }

        Returns:
            List[SubjectNet]: Ders bazlı net listesi

        Requirements: REQ-1.4
        """
        try:
            subject_nets = []

            for subject, results in subject_results.items():
                correct = results.get("correct", 0)
                wrong = results.get("wrong", 0)
                empty = results.get("empty", 0)

                net = self.calculate_net_score(correct, wrong, empty)

                subject_net = SubjectNet(
                    subject=subject,
                    correct=correct,
                    wrong=wrong,
                    empty=empty,
                    net=net,
                )

                subject_nets.append(subject_net)

            logger.info(
                "Ders bazlı netler hesaplandı",
                extra_data={"subject_count": len(subject_nets)},
            )

            return subject_nets

        except Exception as e:
            logger.error(f"Ders bazlı net hesaplama hatası: {e}")
            return []

    def calculate_exam_nets(
        self, exam_type: str, subject_results: dict[str, dict[str, int]]
    ) -> ExamNetScores:
        """
        Sınav toplam net skorlarını hesapla

        Args:
            exam_type: Sınav türü (TYT, AYT, YDT)
            subject_results: Ders bazlı sonuçlar

        Returns:
            ExamNetScores: Sınav net skorları

        Requirements: REQ-1.4
        """
        try:
            subject_nets = self.calculate_subject_nets(subject_results)

            total_net = sum(sn.net for sn in subject_nets)
            total_correct = sum(sn.correct for sn in subject_nets)
            total_wrong = sum(sn.wrong for sn in subject_nets)
            total_empty = sum(sn.empty for sn in subject_nets)

            exam_nets = ExamNetScores(
                exam_type=exam_type,
                subject_nets=subject_nets,
                total_net=round(total_net, 2),
                total_correct=total_correct,
                total_wrong=total_wrong,
                total_empty=total_empty,
            )

            logger.info(
                "Sınav netleri hesaplandı",
                extra_data={
                    "exam_type": exam_type,
                    "total_net": total_net,
                    "total_correct": total_correct,
                },
            )

            return exam_nets

        except Exception as e:
            logger.error(f"Sınav net hesaplama hatası: {e}")
            return ExamNetScores(
                exam_type=exam_type,
                subject_nets=[],
                total_net=0.0,
                total_correct=0,
                total_wrong=0,
                total_empty=0,
            )

    def calculate_raw_score(
        self, subject_nets: list[SubjectNet], coefficients: dict[str, float]
    ) -> float:
        """
        Ham puan hesapla (katsayılı puanlama)

        Formül: Ham Puan = Σ(Net * Katsayı) / Σ(Katsayı) * 5

        Args:
            subject_nets: Ders bazlı net listesi
            coefficients: Ders katsayıları

        Returns:
            float: Ham puan (0-500 arası)

        Requirements: REQ-1.4
        """
        try:
            weighted_sum = 0.0
            coefficient_sum = 0.0

            for subject_net in subject_nets:
                subject = subject_net.subject
                coefficient = coefficients.get(subject, 1.0)

                weighted_sum += subject_net.net * coefficient
                coefficient_sum += coefficient

            if coefficient_sum == 0:
                return 0.0

            # ÖSYM formülü: (Ağırlıklı toplam / Katsayı toplamı) * 5
            raw_score = (weighted_sum / coefficient_sum) * 5.0

            # 0-500 arası sınırla
            raw_score = max(0.0, min(500.0, raw_score))

            logger.debug(
                "Ham puan hesaplandı",
                extra_data={
                    "weighted_sum": weighted_sum,
                    "coefficient_sum": coefficient_sum,
                    "raw_score": raw_score,
                },
            )

            return round(raw_score, 3)

        except Exception as e:
            logger.error(f"Ham puan hesaplama hatası: {e}")
            return 0.0

    def _generate_score_distribution(self, total_candidates: int) -> dict[int, int]:
        """
        Puan dağılımı oluştur (normal dağılım simülasyonu)

        Args:
            total_candidates: Toplam aday sayısı

        Returns:
            Dict[int, int]: Puan -> Aday sayısı
        """
        # Basit normal dağılım simülasyonu
        # Gerçek uygulamada geçmiş yıl verileri kullanılacak
        distribution = {}

        import math

        mean = 300.0  # Ortalama puan
        std_dev = 80.0  # Standart sapma

        for score in range(180, 501):  # 180-500 arası puanlar
            # Normal dağılım olasılığı
            z = (score - mean) / std_dev
            probability = (1 / (std_dev * math.sqrt(2 * math.pi))) * math.exp(
                -0.5 * z * z
            )

            # Aday sayısı tahmini (PDF * bin_width * total)
            candidates = int(probability * total_candidates)
            distribution[score] = candidates

        return distribution

    def _get_coefficients_for_score_type(
        self, score_type: ScoreType, exam_part: str
    ) -> dict[str, float]:
        """
        Puan türüne göre katsayıları getir

        Args:
            score_type: Puan türü
            exam_part: Sınav bölümü (tyt, ayt, ydt)

        Returns:
            Dict[str, float]: Katsayılar
        """
        if exam_part == "tyt":
            return self.tyt_coefficients
        if exam_part == "ayt":
            if score_type == ScoreType.SAY:
                return self.ayt_sayisal_coefficients
            if score_type == ScoreType.SOZ:
                return self.ayt_sozel_coefficients
            # EA
            # Eşit ağırlık için karma katsayılar
            return {
                "MATEMATIK": 5.0,
                "EDEBIYAT": 5.0,
                "TARIH_1": 4.0,
                "COGRAFYA_1": 4.0,
            }
        if exam_part == "ydt":
            return self.ydt_coefficients

        return {}

    def calculate_osym_score(
        self,
        score_type: ScoreType,
        tyt_subject_results: dict[str, dict[str, int]],
        ayt_subject_results: dict[str, dict[str, int]] | None = None,
        ydt_subject_results: dict[str, dict[str, int]] | None = None,
    ) -> OSYMScore:
        """
        ÖSYM puanını hesapla (TYT + AYT/YDT kombinasyonu)

        Args:
            score_type: Puan türü (SAY, EA, SOZ, DIL)
            tyt_subject_results: TYT ders sonuçları
            ayt_subject_results: AYT ders sonuçları (opsiyonel)
            ydt_subject_results: YDT ders sonuçları (opsiyonel)

        Returns:
            OSYMScore: ÖSYM puanı

        Requirements: REQ-1.4
        """
        try:
            # TYT netleri ve ham puanı hesapla
            tyt_nets = self.calculate_subject_nets(tyt_subject_results)
            tyt_raw_score = self.calculate_raw_score(tyt_nets, self.tyt_coefficients)

            # TYT minimum puan kontrolü
            if tyt_raw_score < self.min_tyt_score:
                logger.warning(
                    f"TYT puanı minimum puanın altında: {tyt_raw_score} < {self.min_tyt_score}"
                )

            # AYT/YDT puanlarını hesapla
            ayt_raw_score = 0.0
            ydt_raw_score = 0.0

            if ayt_subject_results:
                ayt_nets = self.calculate_subject_nets(ayt_subject_results)
                ayt_coefficients = self._get_coefficients_for_score_type(
                    score_type, "ayt"
                )
                ayt_raw_score = self.calculate_raw_score(ayt_nets, ayt_coefficients)

            if ydt_subject_results:
                ydt_nets = self.calculate_subject_nets(ydt_subject_results)
                ydt_raw_score = self.calculate_raw_score(
                    ydt_nets, self.ydt_coefficients
                )

            # Puan türüne göre ağırlıklı puan hesapla
            weights = self.score_type_weights[score_type]
            tyt_weight = weights.get("tyt_weight", 0.4)

            if score_type == ScoreType.DIL:
                # Dil puanı: TYT (0.4) + YDT (0.6)
                ydt_weight = weights.get("ydt_weight", 0.6)
                weighted_score = (tyt_raw_score * tyt_weight) + (
                    ydt_raw_score * ydt_weight
                )
            else:
                # Diğer puan türleri: TYT (0.4) + AYT (0.6)
                ayt_weight = weights.get("ayt_weight", 0.6)
                weighted_score = (tyt_raw_score * tyt_weight) + (
                    ayt_raw_score * ayt_weight
                )

            osym_score = OSYMScore(
                score_type=score_type,
                raw_score=weighted_score,
                weighted_score=weighted_score,
                tyt_score=tyt_raw_score,
                ayt_score=ayt_raw_score,
                ydt_score=ydt_raw_score,
                obp_contribution=0.0,  # OBP sonradan eklenecek
                total_score=weighted_score,
            )

            logger.info(
                "ÖSYM puanı hesaplandı",
                extra_data={
                    "score_type": score_type.value,
                    "tyt_score": tyt_raw_score,
                    "ayt_score": ayt_raw_score,
                    "ydt_score": ydt_raw_score,
                    "weighted_score": weighted_score,
                },
            )

            return osym_score

        except Exception as e:
            logger.error(f"ÖSYM puan hesaplama hatası: {e}")
            return OSYMScore(
                score_type=score_type,
                raw_score=0.0,
                weighted_score=0.0,
                tyt_score=0.0,
                ayt_score=0.0,
                ydt_score=0.0,
                obp_contribution=0.0,
                total_score=0.0,
            )

    def calculate_placement_score(
        self,
        osym_score: OSYMScore,
        obp: float,
        additional_bonus: float = 0.0,
    ) -> PlacementScore:
        """
        Yerleştirme puanı hesapla

        Formül: Yerleştirme Puanı = YKS Puanı + (OBP * 0.12) + Ek Puanlar

        Args:
            osym_score: ÖSYM puanı
            obp: Ortaöğretim Başarı Puanı (0-100 arası)
            additional_bonus: Ek puanlar (engelli, vb.)

        Returns:
            PlacementScore: Yerleştirme puanı

        Requirements: REQ-1.4, REQ-1.5
        """
        try:
            # OBP katkısı hesapla (OBP'nin %12'si)
            obp_bonus = obp * self.obp_weight

            # Toplam yerleştirme puanı
            total_placement_score = (
                osym_score.weighted_score + obp_bonus + additional_bonus
            )

            # Minimum puan kontrolü
            meets_minimum = total_placement_score >= self.min_placement_score

            placement_score = PlacementScore(
                score_type=osym_score.score_type,
                base_score=osym_score.weighted_score,
                obp_bonus=obp_bonus,
                additional_bonus=additional_bonus,
                total_placement_score=round(total_placement_score, 3),
                min_required_score=self.min_placement_score,
            )

            logger.info(
                "Yerleştirme puanı hesaplandı",
                extra_data={
                    "score_type": osym_score.score_type.value,
                    "base_score": osym_score.weighted_score,
                    "obp_bonus": obp_bonus,
                    "total_placement_score": total_placement_score,
                    "meets_minimum": meets_minimum,
                },
            )

            return placement_score

        except Exception as e:
            logger.error(f"Yerleştirme puanı hesaplama hatası: {e}")
            return PlacementScore(
                score_type=osym_score.score_type,
                base_score=0.0,
                obp_bonus=0.0,
                additional_bonus=0.0,
                total_placement_score=0.0,
                min_required_score=self.min_placement_score,
            )

    def estimate_ranking(
        self,
        placement_score: PlacementScore,
    ) -> RankingEstimate:
        """
        Sıralama tahmini yap (geçmiş yıl verileri ile)

        Args:
            placement_score: Yerleştirme puanı

        Returns:
            RankingEstimate: Sıralama tahmini

        Requirements: REQ-1.4, REQ-1.5
        """
        try:
            score_type = placement_score.score_type
            score = placement_score.total_placement_score

            # Geçmiş yıl verilerini al
            historical = self.historical_data.get(score_type, {})
            total_candidates = historical.get("total_candidates", 100000)
            score_distribution = historical.get("score_distribution", {})

            # Puandan daha düşük puan alan aday sayısını hesapla
            candidates_below = 0
            for dist_score, count in score_distribution.items():
                if dist_score < int(score):
                    candidates_below += count

            # Tahmini sıralama
            estimated_rank = total_candidates - candidates_below

            # Yüzdelik dilim hesapla
            percentile = (
                (candidates_below / total_candidates) * 100
                if total_candidates > 0
                else 0
            )

            # Güven seviyesi hesapla (basit implementasyon)
            # Gerçek uygulamada daha sofistike bir model kullanılabilir
            confidence_level = 0.85  # %85 güven seviyesi

            ranking_estimate = RankingEstimate(
                score_type=score_type,
                placement_score=score,
                estimated_rank=estimated_rank,
                percentile=round(percentile, 2),
                total_candidates=total_candidates,
                confidence_level=confidence_level,
            )

            logger.info(
                "Sıralama tahmini yapıldı",
                extra_data={
                    "score_type": score_type.value,
                    "placement_score": score,
                    "estimated_rank": estimated_rank,
                    "percentile": percentile,
                },
            )

            return ranking_estimate

        except Exception as e:
            logger.error(f"Sıralama tahmini hatası: {e}")
            return RankingEstimate(
                score_type=placement_score.score_type,
                placement_score=placement_score.total_placement_score,
                estimated_rank=0,
                percentile=0.0,
                total_candidates=0,
                confidence_level=0.0,
            )

    def calculate_program_specific_score(
        self,
        placement_score: PlacementScore,
        program_coefficients: dict[str, float],
        tyt_subject_results: dict[str, dict[str, int]],
        ayt_subject_results: dict[str, dict[str, int]] | None = None,
    ) -> float:
        """
        Program özel puanı hesapla (farklı katsayılarla)

        Bazı programlar farklı ders katsayıları kullanır.
        Örneğin: Tıp fakülteleri için Fen derslerinin katsayısı daha yüksektir.

        Args:
            placement_score: Temel yerleştirme puanı
            program_coefficients: Program özel katsayılar
            tyt_subject_results: TYT ders sonuçları
            ayt_subject_results: AYT ders sonuçları

        Returns:
            float: Program özel puan

        Requirements: REQ-1.4, REQ-1.5
        """
        try:
            # TYT netleri hesapla
            tyt_nets = self.calculate_subject_nets(tyt_subject_results)

            # Program özel katsayılarla ham puan hesapla
            program_score = self.calculate_raw_score(tyt_nets, program_coefficients)

            # AYT varsa ekle
            if ayt_subject_results:
                ayt_nets = self.calculate_subject_nets(ayt_subject_results)
                ayt_program_score = self.calculate_raw_score(
                    ayt_nets, program_coefficients
                )

                # Ağırlıklı toplam
                program_score = (program_score * 0.4) + (ayt_program_score * 0.6)

            logger.debug(
                "Program özel puan hesaplandı",
                extra_data={"program_score": program_score},
            )

            return round(program_score, 3)

        except Exception as e:
            logger.error(f"Program özel puan hesaplama hatası: {e}")
            return 0.0

    def get_score_analysis(
        self,
        osym_score: OSYMScore,
        placement_score: PlacementScore,
        ranking_estimate: RankingEstimate,
    ) -> dict[str, any]:
        """
        Kapsamlı puan analizi raporu oluştur

        Args:
            osym_score: ÖSYM puanı
            placement_score: Yerleştirme puanı
            ranking_estimate: Sıralama tahmini

        Returns:
            Dict: Analiz raporu
        """
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "score_type": osym_score.score_type.value,
                "scores": {
                    "tyt": osym_score.tyt_score,
                    "ayt": osym_score.ayt_score,
                    "ydt": osym_score.ydt_score,
                    "weighted": osym_score.weighted_score,
                    "placement": placement_score.total_placement_score,
                },
                "ranking": {
                    "estimated_rank": ranking_estimate.estimated_rank,
                    "percentile": ranking_estimate.percentile,
                    "total_candidates": ranking_estimate.total_candidates,
                    "confidence": ranking_estimate.confidence_level,
                },
                "bonuses": {
                    "obp": placement_score.obp_bonus,
                    "additional": placement_score.additional_bonus,
                },
                "status": {
                    "meets_minimum_tyt": osym_score.tyt_score >= self.min_tyt_score,
                    "meets_minimum_placement": placement_score.total_placement_score
                    >= self.min_placement_score,
                },
            }

            return analysis

        except Exception as e:
            logger.error(f"Puan analizi oluşturma hatası: {e}")
            return {}


# Global ÖSYM scoring system instance
osym_scoring_system = OSYMScoringSystem()
