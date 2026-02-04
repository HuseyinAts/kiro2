"""
Soru Seçimi ve Optimizasyon Sistemi (Item Selection Optimizer)
Task 62: Soru Seçimi ve Optimizasyon
Requirements: REQ-49.53-49.68

Bu modül adaptif test sisteminde soru seçimi ve optimizasyonu sağlar:
- Content balancing (konu dağılımı dengesi)
- Exposure control (soru maruziyeti kontrolü)
- ZPD içinde soru seçimi
- Spacing effect (aralıklı tekrar)
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from services.irt_psychometric_analysis import IRTParameters

logger = logging.getLogger(__name__)


@dataclass
class ContentConstraint:
    """Konu kısıtı"""

    subject: str
    topic: str
    min_questions: int
    max_questions: int
    priority: float = 1.0  # Öncelik (1.0 = normal)


@dataclass
class ExposureRecord:
    """Soru maruziyeti kaydı"""

    question_id: str
    total_exposures: int = 0
    total_tests: int = 0
    exposure_rate: float = 0.0
    last_used: Optional[datetime] = None
    rotation_group: int = 0  # Rotasyon grubu (0-9)


@dataclass
class SpacedRepetitionSchedule:
    """Aralıklı tekrar programı"""

    question_id: str
    student_id: str
    last_review: datetime
    next_review: datetime
    review_count: int = 0
    ease_factor: float = 2.5  # FSRS ease factor
    interval_days: int = 1


class ItemSelectionOptimizer:
    """
    Soru Seçimi ve Optimizasyon Sistemi

    REQ-49.53-49.56: Content balancing
    REQ-49.57-49.60: Exposure control
    REQ-49.61-49.64: ZPD içinde soru seçimi
    REQ-49.65-49.68: Spacing effect
    """

    def __init__(self):
        """Soru seçim optimizatörünü başlat"""
        # Content balancing parametreleri
        self.content_balance_weight = 0.3

        # Exposure control parametreleri
        self.max_exposure_rate = 0.2  # Maksimum %20 maruz kalma
        self.sympson_hetter_k = 5  # Sympson-Hetter K parametresi
        self.rotation_groups = 10  # Rotasyon grup sayısı

        # ZPD parametreleri
        self.zpd_range = 1.0  # Theta ± 1.0
        self.frustration_threshold = 2.0  # Çok zor soru eşiği

        # Spacing effect parametreleri
        self.spacing_intervals = [1, 3, 7, 14, 30]  # Gün cinsinden
        self.forgetting_curve_factor = 0.5  # Ebbinghaus faktörü

        # Veri yapıları
        self.exposure_records: Dict[str, ExposureRecord] = {}
        self.spaced_schedules: Dict[Tuple[str, str], SpacedRepetitionSchedule] = {}

        logger.info("Item Selection Optimizer başlatıldı")

    # ==================== SUBTASK 62.1: Content Balancing ====================

    def apply_content_balancing(
        self,
        question_pool: List[Dict],
        content_constraints: List[ContentConstraint],
        current_coverage: Dict[str, int],
    ) -> List[Dict]:
        """
        Konu dağılımı dengesini uygula.

        REQ-49.53: Topic distribution constraints - konu dağılım kısıtlarını uygulama
        REQ-49.54: Curriculum alignment - MEB müfredatına uygun olma
        REQ-49.55: Balanced difficulty distribution - kolay-orta-zor dengesi kurma
        REQ-49.56: Her konudan minimum soru sayısını garanti etme

        Args:
            question_pool: Soru havuzu
            content_constraints: Konu kısıtları
            current_coverage: Mevcut konu kapsamı {topic: count}

        Returns:
            Dengeli soru havuzu
        """
        logger.info(
            f"Content balancing uygulanıyor - "
            f"Pool size: {len(question_pool)}, "
            f"Constraints: {len(content_constraints)}"
        )

        # Her soru için content balance skoru hesapla
        scored_questions = []

        for question in question_pool:
            topic = question.get("topic", "unknown")
            difficulty = question.get("difficulty_level", "medium")

            # Konu dengesi skoru (REQ-49.53, REQ-49.56)
            topic_score = self._calculate_topic_balance_score(
                topic, current_coverage, content_constraints
            )

            # Zorluk dengesi skoru (REQ-49.55)
            difficulty_score = self._calculate_difficulty_balance_score(
                difficulty, current_coverage
            )

            # Müfredat uygunluk skoru (REQ-49.54)
            curriculum_score = self._calculate_curriculum_alignment_score(question)

            # Toplam content balance skoru
            total_score = (
                0.5 * topic_score + 0.3 * difficulty_score + 0.2 * curriculum_score
            )

            scored_questions.append(
                {
                    **question,
                    "content_balance_score": total_score,
                    "topic_score": topic_score,
                    "difficulty_score": difficulty_score,
                    "curriculum_score": curriculum_score,
                }
            )

        # Skora göre sırala (yüksekten düşüğe)
        scored_questions.sort(key=lambda q: q["content_balance_score"], reverse=True)

        logger.info(
            f"Content balancing tamamlandı - "
            f"Top score: {scored_questions[0]['content_balance_score']:.3f}"
        )

        return scored_questions

    def _calculate_topic_balance_score(
        self,
        topic: str,
        current_coverage: Dict[str, int],
        constraints: List[ContentConstraint],
    ) -> float:
        """
        Konu dengesi skorunu hesapla.

        REQ-49.53: Topic distribution constraints
        REQ-49.56: Minimum soru sayısı garantisi

        Args:
            topic: Konu adı
            current_coverage: Mevcut kapsam
            constraints: Konu kısıtları

        Returns:
            Konu dengesi skoru (0-1 arası, yüksek = daha çok ihtiyaç var)
        """
        # Bu konu için kısıt bul
        constraint = next((c for c in constraints if c.topic == topic), None)

        if not constraint:
            return 0.5  # Kısıt yoksa orta skor

        current_count = current_coverage.get(topic, 0)

        # Minimum gereksinimi karşılamıyorsa yüksek skor (REQ-49.56)
        if current_count < constraint.min_questions:
            deficit = constraint.min_questions - current_count
            # Eksiklik oranına göre skor (1.0 = tam eksik, 0.5 = yarı eksik)
            score = 0.5 + (deficit / constraint.min_questions) * 0.5
            return min(1.0, score * constraint.priority)

        # Maksimum aşılmışsa düşük skor
        if current_count >= constraint.max_questions:
            return 0.1

        # Arada ise dengeli skor
        progress = (current_count - constraint.min_questions) / (
            constraint.max_questions - constraint.min_questions
        )
        score = 0.5 * (1.0 - progress)  # Daha az ilerleme = daha yüksek skor

        return score * constraint.priority

    def _calculate_difficulty_balance_score(
        self, difficulty: str, current_coverage: Dict[str, int]
    ) -> float:
        """
        Zorluk dengesi skorunu hesapla.

        REQ-49.55: Balanced difficulty distribution

        Args:
            difficulty: Zorluk seviyesi (easy/medium/hard)
            current_coverage: Mevcut kapsam

        Returns:
            Zorluk dengesi skoru (0-1 arası)
        """
        # Hedef dağılım: %30 kolay, %50 orta, %20 zor
        target_distribution = {"easy": 0.30, "medium": 0.50, "hard": 0.20}

        # Mevcut dağılımı hesapla
        total_questions = sum(
            current_coverage.get(f"difficulty_{d}", 0)
            for d in ["easy", "medium", "hard"]
        )

        if total_questions == 0:
            # İlk sorular için hedef dağılıma göre skor
            return target_distribution.get(difficulty, 0.5)

        current_count = current_coverage.get(f"difficulty_{difficulty}", 0)
        current_ratio = current_count / total_questions
        target_ratio = target_distribution.get(difficulty, 0.33)

        # Hedeften ne kadar uzak?
        deficit = target_ratio - current_ratio

        if deficit > 0:
            # Eksik var, yüksek skor
            return 0.5 + min(0.5, deficit * 2)
        else:
            # Fazla var, düşük skor
            return 0.5 - min(0.4, abs(deficit) * 2)

    def _calculate_curriculum_alignment_score(self, question: Dict) -> float:
        """
        Müfredat uygunluk skorunu hesapla.

        REQ-49.54: Curriculum alignment

        Args:
            question: Soru bilgileri

        Returns:
            Müfredat uygunluk skoru (0-1 arası)
        """
        # MEB müfredat uygunluğu (metadata'dan)
        is_meb_aligned = question.get("is_meb_aligned", False)
        meb_standard_id = question.get("meb_standard_id")
        osym_format = question.get("osym_format_compliant", False)

        score = 0.0

        if is_meb_aligned:
            score += 0.4

        if meb_standard_id:
            score += 0.3

        if osym_format:
            score += 0.3

        return min(1.0, score)

    def enforce_content_constraints(
        self, selected_questions: List[Dict], constraints: List[ContentConstraint]
    ) -> bool:
        """
        İçerik kısıtlarının karşılandığını doğrula.

        REQ-49.56: Content constraints uygulaması

        Args:
            selected_questions: Seçilen sorular
            constraints: Konu kısıtları

        Returns:
            Kısıtlar karşılandı mı?
        """
        # Konu bazlı sayım
        topic_counts = {}
        for question in selected_questions:
            topic = question.get("topic", "unknown")
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Her kısıtı kontrol et
        for constraint in constraints:
            count = topic_counts.get(constraint.topic, 0)

            if count < constraint.min_questions:
                logger.warning(
                    f"Content constraint ihlali - "
                    f"Topic: {constraint.topic}, "
                    f"Required: {constraint.min_questions}, "
                    f"Actual: {count}"
                )
                return False

            if count > constraint.max_questions:
                logger.warning(
                    f"Content constraint ihlali - "
                    f"Topic: {constraint.topic}, "
                    f"Max: {constraint.max_questions}, "
                    f"Actual: {count}"
                )
                return False

        logger.info("Tüm content constraints karşılandı")
        return True

    # ==================== SUBTASK 62.2: Exposure Control ====================

    def track_item_exposure(
        self, question_id: str, test_count: int = 1
    ) -> ExposureRecord:
        """
        Soru maruziyetini takip et.

        REQ-49.57: Item exposure rate tracking - her sorunun kullanım sıklığını takip etme

        Args:
            question_id: Soru ID'si
            test_count: Test sayısı artışı

        Returns:
            Güncellenmiş maruz kalma kaydı
        """
        if question_id not in self.exposure_records:
            # Yeni kayıt oluştur
            self.exposure_records[question_id] = ExposureRecord(
                question_id=question_id,
                rotation_group=hash(question_id) % self.rotation_groups,
            )

        record = self.exposure_records[question_id]
        record.total_exposures += 1
        record.total_tests += test_count
        record.last_used = datetime.now()

        # Exposure rate hesapla
        if record.total_tests > 0:
            record.exposure_rate = record.total_exposures / record.total_tests

        logger.debug(
            f"Exposure tracked - Question: {question_id}, "
            f"Exposures: {record.total_exposures}, "
            f"Rate: {record.exposure_rate:.3f}"
        )

        return record

    def apply_sympson_hetter_method(
        self, question_pool: List[Dict], target_exposure_rate: float = 0.2
    ) -> List[Dict]:
        """
        Sympson-Hetter metodu ile exposure control uygula.

        REQ-49.58: Sympson-Hetter method - soru maruziyetini sınırlama

        Sympson-Hetter metodu, her sorunun seçilme olasılığını kontrol ederek
        soru havuzundaki tüm soruların dengeli kullanılmasını sağlar.

        Args:
            question_pool: Soru havuzu
            target_exposure_rate: Hedef maruz kalma oranı

        Returns:
            Exposure control uygulanmış soru havuzu
        """
        logger.info(
            f"Sympson-Hetter method uygulanıyor - "
            f"Pool size: {len(question_pool)}, "
            f"Target rate: {target_exposure_rate}"
        )

        controlled_pool = []

        for question in question_pool:
            question_id = question.get("id", question.get("question_id"))

            # Exposure kaydını al
            record = self.exposure_records.get(
                question_id, ExposureRecord(question_id=question_id)
            )

            # Sympson-Hetter control probability hesapla
            control_prob = self._calculate_sympson_hetter_probability(
                record.exposure_rate, target_exposure_rate, self.sympson_hetter_k
            )

            # Soruyu kontrol olasılığı ile ekle
            controlled_question = {
                **question,
                "exposure_rate": record.exposure_rate,
                "control_probability": control_prob,
                "exposure_penalty": control_prob,  # Skor çarpanı olarak kullan
            }

            controlled_pool.append(controlled_question)

        logger.info(
            f"Sympson-Hetter method tamamlandı - "
            f"Controlled pool size: {len(controlled_pool)}"
        )

        return controlled_pool

    def _calculate_sympson_hetter_probability(
        self, current_rate: float, target_rate: float, k: float
    ) -> float:
        """
        Sympson-Hetter control probability hesapla.

        REQ-49.58: Sympson-Hetter method

        Formula: P(select) = 1 / (1 + exp(k * (current_rate - target_rate)))

        Args:
            current_rate: Mevcut maruz kalma oranı
            target_rate: Hedef maruz kalma oranı
            k: Kontrol parametresi (yüksek k = daha sıkı kontrol)

        Returns:
            Seçilme olasılığı (0-1 arası)
        """
        if current_rate == 0:
            return 1.0  # Hiç kullanılmamış, tam olasılık

        # Logistic function
        exponent = k * (current_rate - target_rate)
        probability = 1.0 / (1.0 + math.exp(exponent))

        return max(0.1, min(1.0, probability))  # [0.1, 1.0] aralığında sınırla

    def rotate_item_pool(
        self, question_pool: List[Dict], active_rotation_groups: Set[int]
    ) -> List[Dict]:
        """
        Soru havuzunu döngüsel olarak kullan.

        REQ-49.59: Item pool rotation - soru havuzunu döngüsel kullanma

        Args:
            question_pool: Soru havuzu
            active_rotation_groups: Aktif rotasyon grupları (0-9 arası)

        Returns:
            Rotasyon uygulanmış soru havuzu
        """
        logger.info(
            f"Item pool rotation uygulanıyor - "
            f"Active groups: {active_rotation_groups}"
        )

        rotated_pool = []

        for question in question_pool:
            question_id = question.get("id", question.get("question_id"))

            # Rotasyon grubunu al
            record = self.exposure_records.get(
                question_id,
                ExposureRecord(
                    question_id=question_id,
                    rotation_group=hash(question_id) % self.rotation_groups,
                ),
            )

            # Aktif grupta mı?
            if record.rotation_group in active_rotation_groups:
                rotated_pool.append(
                    {
                        **question,
                        "rotation_group": record.rotation_group,
                        "is_active_rotation": True,
                    }
                )

        logger.info(
            f"Item pool rotation tamamlandı - "
            f"Original: {len(question_pool)}, "
            f"Rotated: {len(rotated_pool)}"
        )

        return rotated_pool

    def disable_overexposed_items(
        self, question_pool: List[Dict], max_exposure_rate: Optional[float] = None
    ) -> List[Dict]:
        """
        Aşırı maruz kalmış soruları geçici olarak devre dışı bırak.

        REQ-49.60: Exposure limit aşıldığında soruyu geçici olarak devre dışı bırakma

        Args:
            question_pool: Soru havuzu
            max_exposure_rate: Maksimum maruz kalma oranı

        Returns:
            Filtrelenmiş soru havuzu
        """
        if max_exposure_rate is None:
            max_exposure_rate = self.max_exposure_rate

        logger.info(
            f"Overexposed items filtreleniyor - " f"Max rate: {max_exposure_rate}"
        )

        filtered_pool = []
        disabled_count = 0

        for question in question_pool:
            question_id = question.get("id", question.get("question_id"))

            # Exposure kaydını al
            record = self.exposure_records.get(question_id)

            if record and record.exposure_rate > max_exposure_rate:
                # Aşırı maruz kalmış, devre dışı bırak
                logger.debug(
                    f"Question disabled - ID: {question_id}, "
                    f"Rate: {record.exposure_rate:.3f} > {max_exposure_rate}"
                )
                disabled_count += 1
                continue

            filtered_pool.append({**question, "is_exposure_controlled": True})

        logger.info(
            f"Overexposed items filtrelendi - "
            f"Disabled: {disabled_count}, "
            f"Remaining: {len(filtered_pool)}"
        )

        return filtered_pool

    def get_exposure_statistics(self) -> Dict:
        """
        Maruz kalma istatistiklerini al.

        REQ-49.57: Item exposure rate tracking

        Returns:
            Maruz kalma istatistikleri
        """
        if not self.exposure_records:
            return {
                "total_items": 0,
                "avg_exposure_rate": 0.0,
                "max_exposure_rate": 0.0,
                "overexposed_count": 0,
            }

        rates = [r.exposure_rate for r in self.exposure_records.values()]

        return {
            "total_items": len(self.exposure_records),
            "avg_exposure_rate": np.mean(rates),
            "max_exposure_rate": np.max(rates),
            "min_exposure_rate": np.min(rates),
            "std_exposure_rate": np.std(rates),
            "overexposed_count": sum(1 for r in rates if r > self.max_exposure_rate),
        }

    # ==================== SUBTASK 62.3: ZPD İçinde Soru Seçimi ====================

    def select_within_zpd(
        self,
        question_pool: List[Dict],
        student_theta: float,
        zpd_range: Optional[float] = None,
    ) -> List[Dict]:
        """
        Zone of Proximal Development (ZPD) içinde soru seç.

        REQ-49.61: Zone of Proximal Development targeting - ZPD hedefleme
        REQ-49.62: Optimal challenge level - öğrenci yetenek seviyesine göre ayarlama
        REQ-49.63: Frustration prevention - çok zor soruları filtreleme
        REQ-49.64: Theta ± 1 aralığında soru seçme

        Args:
            question_pool: Soru havuzu
            student_theta: Öğrenci yetenek seviyesi
            zpd_range: ZPD aralığı (varsayılan: 1.0)

        Returns:
            ZPD içindeki sorular
        """
        if zpd_range is None:
            zpd_range = self.zpd_range

        # ZPD aralığını hesapla (REQ-49.64)
        zpd_min = student_theta - zpd_range
        zpd_max = student_theta + zpd_range

        logger.info(
            f"ZPD filtering uygulanıyor - "
            f"Student theta: {student_theta:.3f}, "
            f"ZPD range: [{zpd_min:.3f}, {zpd_max:.3f}]"
        )

        zpd_questions = []
        too_easy_count = 0
        too_hard_count = 0

        for question in question_pool:
            # Soru zorluğunu al (IRT b parametresi)
            difficulty = question.get("difficulty_b", question.get("difficulty", 0.0))

            # Frustration prevention (REQ-49.63)
            if difficulty > student_theta + self.frustration_threshold:
                too_hard_count += 1
                continue

            # ZPD içinde mi? (REQ-49.61, REQ-49.64)
            if zpd_min <= difficulty <= zpd_max:
                # Optimal challenge level skoru hesapla (REQ-49.62)
                challenge_score = self._calculate_challenge_score(
                    difficulty, student_theta
                )

                zpd_questions.append(
                    {
                        **question,
                        "is_in_zpd": True,
                        "challenge_score": challenge_score,
                        "difficulty_distance": abs(difficulty - student_theta),
                    }
                )
            elif difficulty < zpd_min:
                too_easy_count += 1
            else:
                too_hard_count += 1

        logger.info(
            f"ZPD filtering tamamlandı - "
            f"In ZPD: {len(zpd_questions)}, "
            f"Too easy: {too_easy_count}, "
            f"Too hard: {too_hard_count}"
        )

        return zpd_questions

    def _calculate_challenge_score(
        self, difficulty: float, student_theta: float
    ) -> float:
        """
        Optimal challenge level skorunu hesapla.

        REQ-49.62: Optimal challenge level

        Optimal challenge, öğrencinin mevcut seviyesinden biraz daha zor
        sorulardır (theta + 0.5 civarı).

        Args:
            difficulty: Soru zorluğu (b parametresi)
            student_theta: Öğrenci yetenek seviyesi

        Returns:
            Challenge skoru (0-1 arası, yüksek = daha optimal)
        """
        # Optimal zorluk: theta + 0.5
        optimal_difficulty = student_theta + 0.5

        # Optimal zorluğa ne kadar yakın?
        distance = abs(difficulty - optimal_difficulty)

        # Gaussian benzeri skor (optimal'e yakın = yüksek skor)
        score = math.exp(-(distance**2) / 0.5)

        return score

    def prevent_frustration(
        self,
        question_pool: List[Dict],
        student_theta: float,
        frustration_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Frustration (hayal kırıklığı) önleme filtresi uygula.

        REQ-49.63: Frustration prevention - çok zor soruları filtreleme

        Args:
            question_pool: Soru havuzu
            student_theta: Öğrenci yetenek seviyesi
            frustration_threshold: Frustration eşiği (theta + threshold)

        Returns:
            Filtrelenmiş soru havuzu
        """
        if frustration_threshold is None:
            frustration_threshold = self.frustration_threshold

        max_difficulty = student_theta + frustration_threshold

        logger.info(
            f"Frustration prevention uygulanıyor - "
            f"Max difficulty: {max_difficulty:.3f}"
        )

        filtered_pool = []
        filtered_count = 0

        for question in question_pool:
            difficulty = question.get("difficulty_b", question.get("difficulty", 0.0))

            if difficulty <= max_difficulty:
                filtered_pool.append({**question, "frustration_prevented": True})
            else:
                filtered_count += 1

        logger.info(
            f"Frustration prevention tamamlandı - "
            f"Filtered: {filtered_count}, "
            f"Remaining: {len(filtered_pool)}"
        )

        return filtered_pool

    def adjust_zpd_range(
        self, student_performance: Dict, current_zpd_range: float
    ) -> float:
        """
        Öğrenci performansına göre ZPD aralığını ayarla.

        REQ-49.62: Optimal challenge level - öğrenci yetenek seviyesine göre ayarlama

        Args:
            student_performance: Öğrenci performans verileri
            current_zpd_range: Mevcut ZPD aralığı

        Returns:
            Ayarlanmış ZPD aralığı
        """
        accuracy = student_performance.get("accuracy", 0.5)
        response_time_avg = student_performance.get("response_time_avg", 60.0)

        # Başarı oranına göre ayarlama
        if accuracy > 0.8:
            # Çok başarılı, aralığı genişlet (daha zor sorular)
            adjusted_range = current_zpd_range * 1.1
        elif accuracy < 0.4:
            # Başarısız, aralığı daralt (daha kolay sorular)
            adjusted_range = current_zpd_range * 0.9
        else:
            # Optimal aralıkta, değiştirme
            adjusted_range = current_zpd_range

        # Sınırla (0.5 - 1.5 arası)
        adjusted_range = max(0.5, min(1.5, adjusted_range))

        logger.info(
            f"ZPD range adjusted - "
            f"Accuracy: {accuracy:.2f}, "
            f"Old range: {current_zpd_range:.2f}, "
            f"New range: {adjusted_range:.2f}"
        )

        return adjusted_range

    # ==================== SUBTASK 62.4: Spacing Effect ====================

    def apply_spacing_effect(
        self,
        question_pool: List[Dict],
        student_id: str,
        current_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Spacing effect (aralıklı tekrar) uygula.

        REQ-49.65: Spaced repetition integration - optimal tekrar zamanlaması yapma
        REQ-49.66: Optimal review timing - FSRS algoritması kullanma
        REQ-49.67: Forgetting curve - Ebbinghaus modelini kullanma
        REQ-49.68: 1-3-7-14-30 gün aralıkları önerme

        Args:
            question_pool: Soru havuzu
            student_id: Öğrenci ID'si
            current_time: Mevcut zaman (test için)

        Returns:
            Spacing effect uygulanmış soru havuzu
        """
        if current_time is None:
            current_time = datetime.now()

        logger.info(
            f"Spacing effect uygulanıyor - "
            f"Student: {student_id}, "
            f"Pool size: {len(question_pool)}"
        )

        spaced_questions = []

        for question in question_pool:
            question_id = question.get("id", question.get("question_id"))

            # Spaced repetition schedule'ı al veya oluştur
            schedule_key = (student_id, question_id)
            schedule = self.spaced_schedules.get(schedule_key)

            if schedule is None:
                # İlk kez görülüyor, schedule oluştur
                schedule = self._create_initial_schedule(
                    question_id, student_id, current_time
                )
                self.spaced_schedules[schedule_key] = schedule

            # Tekrar zamanı geldi mi? (REQ-49.65)
            is_due = current_time >= schedule.next_review

            # Forgetting curve skoru hesapla (REQ-49.67)
            forgetting_score = self._calculate_forgetting_score(schedule, current_time)

            # Spacing priority skoru hesapla
            spacing_priority = self._calculate_spacing_priority(
                schedule, is_due, forgetting_score
            )

            spaced_questions.append(
                {
                    **question,
                    "is_due_for_review": is_due,
                    "forgetting_score": forgetting_score,
                    "spacing_priority": spacing_priority,
                    "next_review": schedule.next_review,
                    "review_count": schedule.review_count,
                    "interval_days": schedule.interval_days,
                }
            )

        # Spacing priority'ye göre sırala (yüksekten düşüğe)
        spaced_questions.sort(key=lambda q: q["spacing_priority"], reverse=True)

        logger.info(
            f"Spacing effect tamamlandı - "
            f"Due for review: {sum(1 for q in spaced_questions if q['is_due_for_review'])}"
        )

        return spaced_questions

    def _create_initial_schedule(
        self, question_id: str, student_id: str, current_time: datetime
    ) -> SpacedRepetitionSchedule:
        """
        İlk spaced repetition schedule'ı oluştur.

        REQ-49.68: 1-3-7-14-30 gün aralıkları

        Args:
            question_id: Soru ID'si
            student_id: Öğrenci ID'si
            current_time: Mevcut zaman

        Returns:
            Spaced repetition schedule
        """
        # İlk interval: 1 gün (REQ-49.68)
        initial_interval = self.spacing_intervals[0]

        return SpacedRepetitionSchedule(
            question_id=question_id,
            student_id=student_id,
            last_review=current_time,
            next_review=current_time + timedelta(days=initial_interval),
            review_count=0,
            ease_factor=2.5,  # FSRS varsayılan
            interval_days=initial_interval,
        )

    def update_spacing_schedule(
        self,
        student_id: str,
        question_id: str,
        is_correct: bool,
        response_quality: float,
        current_time: Optional[datetime] = None,
    ) -> SpacedRepetitionSchedule:
        """
        Yanıta göre spacing schedule'ı güncelle.

        REQ-49.66: Optimal review timing - FSRS algoritması kullanma
        REQ-49.68: 1-3-7-14-30 gün aralıkları önerme

        Args:
            student_id: Öğrenci ID'si
            question_id: Soru ID'si
            is_correct: Yanıt doğru mu?
            response_quality: Yanıt kalitesi (0-1 arası)
            current_time: Mevcut zaman

        Returns:
            Güncellenmiş schedule
        """
        if current_time is None:
            current_time = datetime.now()

        schedule_key = (student_id, question_id)
        schedule = self.spaced_schedules.get(schedule_key)

        if schedule is None:
            # Schedule yoksa oluştur
            schedule = self._create_initial_schedule(
                question_id, student_id, current_time
            )

        # FSRS algoritması ile interval hesapla (REQ-49.66)
        new_interval = self._calculate_fsrs_interval(
            schedule, is_correct, response_quality
        )

        # Interval'i spacing_intervals listesine yaklaştır (REQ-49.68)
        new_interval = self._snap_to_spacing_intervals(new_interval)

        # Schedule'ı güncelle
        schedule.last_review = current_time
        schedule.next_review = current_time + timedelta(days=new_interval)
        schedule.review_count += 1
        schedule.interval_days = new_interval

        # Ease factor güncelle (FSRS)
        if is_correct:
            schedule.ease_factor = min(3.0, schedule.ease_factor + 0.1)
        else:
            schedule.ease_factor = max(1.3, schedule.ease_factor - 0.2)

        self.spaced_schedules[schedule_key] = schedule

        logger.debug(
            f"Spacing schedule güncellendi - "
            f"Student: {student_id}, Question: {question_id}, "
            f"Correct: {is_correct}, New interval: {new_interval} days"
        )

        return schedule

    def _calculate_fsrs_interval(
        self,
        schedule: SpacedRepetitionSchedule,
        is_correct: bool,
        response_quality: float,
    ) -> int:
        """
        FSRS algoritması ile yeni interval hesapla.

        REQ-49.66: FSRS algoritması

        Args:
            schedule: Mevcut schedule
            is_correct: Yanıt doğru mu?
            response_quality: Yanıt kalitesi (0-1 arası)

        Returns:
            Yeni interval (gün cinsinden)
        """
        current_interval = schedule.interval_days
        ease_factor = schedule.ease_factor

        if not is_correct:
            # Yanlış cevap: interval'i sıfırla
            return 1

        # Doğru cevap: interval'i artır
        # FSRS formülü: new_interval = current_interval * ease_factor * quality_modifier
        quality_modifier = 0.5 + (response_quality * 0.5)  # 0.5 - 1.0 arası

        new_interval = current_interval * ease_factor * quality_modifier

        # Integer'a çevir ve sınırla
        new_interval = int(round(new_interval))
        new_interval = max(1, min(90, new_interval))  # 1-90 gün arası

        return new_interval

    def _snap_to_spacing_intervals(self, interval: int) -> int:
        """
        Interval'i spacing_intervals listesine yaklaştır.

        REQ-49.68: 1-3-7-14-30 gün aralıkları

        Args:
            interval: Hesaplanan interval

        Returns:
            Yaklaştırılmış interval
        """
        # En yakın spacing interval'i bul
        closest_interval = min(self.spacing_intervals, key=lambda x: abs(x - interval))

        # Eğer interval çok büyükse, en büyük spacing interval'i kullan
        if interval > self.spacing_intervals[-1]:
            return self.spacing_intervals[-1]

        return closest_interval

    def _calculate_forgetting_score(
        self, schedule: SpacedRepetitionSchedule, current_time: datetime
    ) -> float:
        """
        Forgetting curve skorunu hesapla (Ebbinghaus modeli).

        REQ-49.67: Forgetting curve - Ebbinghaus modelini kullanma

        Ebbinghaus forgetting curve: R(t) = e^(-t/S)
        R(t) = retention at time t
        S = strength of memory

        Args:
            schedule: Spaced repetition schedule
            current_time: Mevcut zaman

        Returns:
            Forgetting skoru (0-1 arası, yüksek = daha çok unutulmuş)
        """
        # Son review'dan bu yana geçen süre
        time_since_review = (
            current_time - schedule.last_review
        ).total_seconds() / 86400  # gün

        # Memory strength (ease factor ve interval'e bağlı)
        memory_strength = schedule.ease_factor * schedule.interval_days

        # Ebbinghaus forgetting curve
        retention = math.exp(
            -time_since_review / (memory_strength * self.forgetting_curve_factor)
        )

        # Forgetting score (1 - retention)
        forgetting_score = 1.0 - retention

        return max(0.0, min(1.0, forgetting_score))

    def _calculate_spacing_priority(
        self, schedule: SpacedRepetitionSchedule, is_due: bool, forgetting_score: float
    ) -> float:
        """
        Spacing priority skorunu hesapla.

        REQ-49.65: Optimal review timing

        Args:
            schedule: Spaced repetition schedule
            is_due: Tekrar zamanı geldi mi?
            forgetting_score: Forgetting skoru

        Returns:
            Spacing priority skoru (0-1 arası, yüksek = daha öncelikli)
        """
        # Base priority
        if is_due:
            base_priority = 0.8
        else:
            base_priority = 0.2

        # Forgetting score ile artır
        priority = base_priority + (forgetting_score * 0.2)

        # Review count ile azalt (çok tekrar edilmiş sorular daha az öncelikli)
        review_penalty = min(0.3, schedule.review_count * 0.05)
        priority -= review_penalty

        return max(0.0, min(1.0, priority))

    def get_due_reviews(
        self, student_id: str, current_time: Optional[datetime] = None
    ) -> List[str]:
        """
        Tekrar zamanı gelmiş soruları al.

        REQ-49.65: Spaced repetition integration

        Args:
            student_id: Öğrenci ID'si
            current_time: Mevcut zaman

        Returns:
            Tekrar zamanı gelmiş soru ID'leri
        """
        if current_time is None:
            current_time = datetime.now()

        due_questions = []

        for (sid, qid), schedule in self.spaced_schedules.items():
            if sid == student_id and current_time >= schedule.next_review:
                due_questions.append(qid)

        logger.info(f"Due reviews - Student: {student_id}, Count: {len(due_questions)}")

        return due_questions

    def get_spacing_statistics(self, student_id: str) -> Dict:
        """
        Spacing istatistiklerini al.

        Args:
            student_id: Öğrenci ID'si

        Returns:
            Spacing istatistikleri
        """
        student_schedules = [
            s for (sid, _), s in self.spaced_schedules.items() if sid == student_id
        ]

        if not student_schedules:
            return {
                "total_items": 0,
                "avg_interval": 0.0,
                "avg_review_count": 0.0,
                "due_count": 0,
            }

        current_time = datetime.now()

        return {
            "total_items": len(student_schedules),
            "avg_interval": np.mean([s.interval_days for s in student_schedules]),
            "avg_review_count": np.mean([s.review_count for s in student_schedules]),
            "avg_ease_factor": np.mean([s.ease_factor for s in student_schedules]),
            "due_count": sum(
                1 for s in student_schedules if current_time >= s.next_review
            ),
        }
