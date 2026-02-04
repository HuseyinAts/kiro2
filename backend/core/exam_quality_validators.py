"""
Exam Quality Validation System
Sınav Kalite Doğrulama Sistemi

Bu sistem:
- IRT kalibrasyonu doğrulaması yapar
- Zorluk seviyesi dengelemesini kontrol eder
- Müfredat eşleştirme kontrolü sağlar
- Konu dağılımı validasyonunu yapar
"""

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from core.structured_logger import get_logger

logger = get_logger(__name__)


# ==================== ENUMS ====================


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""

    VERY_EASY = "very_easy"  # Çok kolay (0-20%)
    EASY = "easy"  # Kolay (20-40%)
    MEDIUM = "medium"  # Orta (40-60%)
    HARD = "hard"  # Zor (60-80%)
    VERY_HARD = "very_hard"  # Çok zor (80-100%)


class ValidationSeverity(Enum):
    """Doğrulama hatası şiddeti"""

    INFO = "info"  # Bilgi amaçlı
    WARNING = "warning"  # Uyarı
    ERROR = "error"  # Hata
    CRITICAL = "critical"  # Kritik hata


class ValidationType(Enum):
    """Doğrulama tipi"""

    IRT_CALIBRATION = "irt_calibration"
    DIFFICULTY_BALANCE = "difficulty_balance"
    CURRICULUM_MATCH = "curriculum_match"
    TOPIC_DISTRIBUTION = "topic_distribution"


# ==================== MODELS ====================


class IRTParameters(BaseModel):
    """IRT parametreleri (3PL Model)"""

    discrimination: float = Field(..., ge=0, le=5)  # a parametresi (ayırt edicilik)
    difficulty: float = Field(..., ge=-4, le=4)  # b parametresi (zorluk)
    guessing: float = Field(default=0.0, ge=0, le=1)  # c parametresi (şans)

    # Kalibrasyon bilgileri
    calibration_sample_size: int = 0
    calibration_date: Optional[datetime] = None
    fit_statistics: Dict[str, float] = Field(default_factory=dict)


class QuestionMetadata(BaseModel):
    """Soru metadatası"""

    question_id: str
    subject: str  # Ders
    topic: str  # Konu
    subtopic: Optional[str] = None  # Alt konu

    # MEB Müfredat
    grade_level: str  # Sınıf seviyesi
    learning_outcomes: List[str] = Field(default_factory=list)  # Kazanımlar

    # ÖSYM bilgileri
    exam_type: str  # tyt, ayt, lgs, vb.
    question_type: str  # test, açık uçlu

    # Zorluk ve IRT
    irt_params: Optional[IRTParameters] = None
    estimated_difficulty: float = Field(default=0.5, ge=0, le=1)  # 0-1 arası

    # İstatistikler
    times_used: int = 0
    avg_correct_rate: Optional[float] = None
    discrimination_index: Optional[float] = None


class ValidationResult(BaseModel):
    """Doğrulama sonucu"""

    validation_id: str = Field(default_factory=lambda: str(id(object())))
    validation_type: ValidationType
    severity: ValidationSeverity
    passed: bool

    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExamBlueprint(BaseModel):
    """Sınav planı/şablonu"""

    exam_id: str
    exam_name: str
    exam_type: str  # tyt, ayt, lgs

    # Genel hedefler
    target_difficulty: float = 0.5  # 0-1 arası
    target_discrimination: float = 1.0  # Ortalama ayırt edicilik

    # Konu dağılımı hedefleri
    topic_distribution: Dict[str, int]  # {"Matematik": 40, "Türkçe": 40}
    subtopic_distribution: Dict[str, int] = Field(default_factory=dict)

    # Zorluk dağılımı hedefleri
    difficulty_distribution: Dict[DifficultyLevel, float] = Field(
        default_factory=lambda: {
            DifficultyLevel.VERY_EASY: 0.1,
            DifficultyLevel.EASY: 0.2,
            DifficultyLevel.MEDIUM: 0.4,
            DifficultyLevel.HARD: 0.2,
            DifficultyLevel.VERY_HARD: 0.1,
        }
    )

    # Kazanım hedefleri
    required_learning_outcomes: List[str] = Field(default_factory=list)
    min_outcomes_coverage: float = 0.8  # En az %80 kazanım kapsama


# ==================== IRT VALIDATION ====================


class IRTCalibrationValidator:
    """
    IRT Kalibrasyon Doğrulayıcı

    3 parametreli lojistik (3PL) modeli kullanır:
    P(θ) = c + (1-c) / (1 + exp(-a(θ-b)))

    a: Discrimination (ayırt edicilik)
    b: Difficulty (zorluk)
    c: Guessing (şans faktörü)
    θ: Yetenek seviyesi
    """

    def __init__(self):
        self.min_calibration_sample = 200  # Minimum öğrenci sayısı
        self.discrimination_range = (0.5, 2.5)  # Kabul edilebilir a değerleri
        self.difficulty_range = (-3, 3)  # Kabul edilebilir b değerleri
        self.max_guessing = 0.35  # Maksimum c değeri (4 şık için 0.25 beklenir)

        logger.info("irt_calibration_validator_initialized")

    def validate_irt_parameters(
        self, question: QuestionMetadata
    ) -> List[ValidationResult]:
        """IRT parametrelerini doğrula"""

        results = []

        if not question.irt_params:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.IRT_CALIBRATION,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"Soru {question.question_id} için IRT parametreleri eksik",
                    suggestions=["Soruyu IRT modeli ile kalibre edin"],
                )
            )
            return results

        params = question.irt_params

        # 1. Kalibrasyon örneklem büyüklüğü kontrolü
        if params.calibration_sample_size < self.min_calibration_sample:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.IRT_CALIBRATION,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"Yetersiz kalibrasyon örneklemi: {params.calibration_sample_size}",
                    details={
                        "sample_size": params.calibration_sample_size,
                        "minimum_required": self.min_calibration_sample,
                    },
                    suggestions=[
                        f"En az {self.min_calibration_sample} öğrenci ile kalibrasyon yapın",
                        "Daha fazla veri toplanana kadar soruyu pilot olarak işaretleyin",
                    ],
                )
            )

        # 2. Discrimination (a) parametresi kontrolü
        if not (
            self.discrimination_range[0]
            <= params.discrimination
            <= self.discrimination_range[1]
        ):
            severity = (
                ValidationSeverity.ERROR
                if params.discrimination < 0.3
                else ValidationSeverity.WARNING
            )
            results.append(
                ValidationResult(
                    validation_type=ValidationType.IRT_CALIBRATION,
                    severity=severity,
                    passed=False,
                    message=f"Ayırt edicilik parametresi normal aralık dışında: {params.discrimination:.2f}",
                    details={
                        "discrimination": params.discrimination,
                        "acceptable_range": self.discrimination_range,
                    },
                    suggestions=[
                        "Düşük ayırt edicilik: Soruyu gözden geçirin, çeldiricileri iyileştirin",
                        "Yüksek ayırt edicilik: Kalibrasyon verilerini kontrol edin",
                    ]
                    if params.discrimination < 0.5
                    else [
                        "Çok yüksek ayırt edicilik değeri olağandışı, veriyi kontrol edin"
                    ],
                )
            )

        # 3. Difficulty (b) parametresi kontrolü
        if not (
            self.difficulty_range[0] <= params.difficulty <= self.difficulty_range[1]
        ):
            results.append(
                ValidationResult(
                    validation_type=ValidationType.IRT_CALIBRATION,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"Zorluk parametresi aşırı değerde: {params.difficulty:.2f}",
                    details={
                        "difficulty": params.difficulty,
                        "acceptable_range": self.difficulty_range,
                    },
                    suggestions=[
                        "Aşırı zor/kolay sorular öğrenci yeteneğini ölçmede yetersizdir",
                        "Soruyu gözden geçirin veya hedef kitleyi değiştirin",
                    ],
                )
            )

        # 4. Guessing (c) parametresi kontrolü
        expected_guessing = 0.25  # 4 şıklı test için
        if params.guessing > self.max_guessing:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.IRT_CALIBRATION,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"Şans faktörü çok yüksek: {params.guessing:.2f}",
                    details={
                        "guessing": params.guessing,
                        "expected": expected_guessing,
                        "max_acceptable": self.max_guessing,
                    },
                    suggestions=[
                        "Yüksek c parametresi sorunun tahmin edilebilir olduğunu gösterir",
                        "Çeldiricileri güçlendirin",
                        "Soru ifadesini netleştirin",
                    ],
                )
            )

        # 5. Model uyum istatistikleri kontrolü
        if params.fit_statistics:
            infit = params.fit_statistics.get("infit", 1.0)
            outfit = params.fit_statistics.get("outfit", 1.0)

            # Kabul edilebilir aralık: 0.7 - 1.3
            if not (0.7 <= infit <= 1.3) or not (0.7 <= outfit <= 1.3):
                results.append(
                    ValidationResult(
                        validation_type=ValidationType.IRT_CALIBRATION,
                        severity=ValidationSeverity.WARNING,
                        passed=False,
                        message="Model uyum istatistikleri kabul edilebilir aralık dışında",
                        details={
                            "infit": infit,
                            "outfit": outfit,
                            "acceptable_range": [0.7, 1.3],
                        },
                        suggestions=[
                            "Soru IRT modeline iyi uymayabilir",
                            "Soruyu gözden geçirin veya farklı bir model deneyin",
                        ],
                    )
                )

        # Tüm kontroller geçtiyse başarılı sonuç ekle
        if not results:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.IRT_CALIBRATION,
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    message=f"Soru {question.question_id} IRT kalibrasyon kontrollerini geçti",
                    details={
                        "discrimination": params.discrimination,
                        "difficulty": params.difficulty,
                        "guessing": params.guessing,
                    },
                )
            )

        return results

    def calculate_information(self, params: IRTParameters, theta: float) -> float:
        """
        Belirli bir yetenek seviyesinde test bilgisi hesapla
        I(θ) = a² * P'(θ)² / P(θ)(1-P(θ))
        """

        a, b, c = params.discrimination, params.difficulty, params.guessing

        # P(θ) hesapla
        p = c + (1 - c) / (1 + math.exp(-a * (theta - b)))

        # P'(θ) hesapla (türev)
        p_prime = (
            a
            * (1 - c)
            * math.exp(-a * (theta - b))
            / (1 + math.exp(-a * (theta - b))) ** 2
        )

        # I(θ) hesapla
        if p == 0 or p == 1:
            return 0.0

        information = (p_prime**2) / (p * (1 - p))
        return information


# ==================== DIFFICULTY BALANCE VALIDATOR ====================


class DifficultyBalanceValidator:
    """Zorluk Seviyesi Dengeleme Doğrulayıcı"""

    def __init__(self):
        self.tolerance = 0.15  # %15 tolerans
        logger.info("difficulty_balance_validator_initialized")

    def _classify_difficulty(self, difficulty: float) -> DifficultyLevel:
        """Zorluk değerini seviyeye dönüştür"""
        if difficulty < 0.2:
            return DifficultyLevel.VERY_EASY
        elif difficulty < 0.4:
            return DifficultyLevel.EASY
        elif difficulty < 0.6:
            return DifficultyLevel.MEDIUM
        elif difficulty < 0.8:
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.VERY_HARD

    def validate_difficulty_distribution(
        self, questions: List[QuestionMetadata], blueprint: ExamBlueprint
    ) -> List[ValidationResult]:
        """Sınav sorularının zorluk dağılımını doğrula"""

        results = []

        if not questions:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.DIFFICULTY_BALANCE,
                    severity=ValidationSeverity.ERROR,
                    passed=False,
                    message="Sınav için soru bulunamadı",
                )
            )
            return results

        # Mevcut zorluk dağılımını hesapla
        difficulty_counts = {level: 0 for level in DifficultyLevel}

        for question in questions:
            # IRT'den veya tahmini zorluktan al
            difficulty = (
                question.irt_params.difficulty
                if question.irt_params
                else question.estimated_difficulty
            )
            # b parametresini 0-1 aralığına normalize et
            if question.irt_params:
                # b parametresi -3 ile 3 arasında, bunu 0-1'e çevir
                normalized_difficulty = (difficulty + 3) / 6
            else:
                normalized_difficulty = difficulty

            level = self._classify_difficulty(normalized_difficulty)
            difficulty_counts[level] += 1

        total_questions = len(questions)

        # Hedef dağılım ile karşılaştır
        for level, target_ratio in blueprint.difficulty_distribution.items():
            actual_count = difficulty_counts[level]
            actual_ratio = actual_count / total_questions
            target_count = int(total_questions * target_ratio)

            difference = abs(actual_ratio - target_ratio)

            if difference > self.tolerance:
                severity = (
                    ValidationSeverity.ERROR
                    if difference > 0.25
                    else ValidationSeverity.WARNING
                )
                results.append(
                    ValidationResult(
                        validation_type=ValidationType.DIFFICULTY_BALANCE,
                        severity=severity,
                        passed=False,
                        message=f"Zorluk seviyesi '{level.value}' dengesiz",
                        details={
                            "level": level.value,
                            "actual_count": actual_count,
                            "target_count": target_count,
                            "actual_ratio": round(actual_ratio, 2),
                            "target_ratio": round(target_ratio, 2),
                            "difference": round(difference, 2),
                        },
                        suggestions=[
                            f"{level.value} seviyesinden {abs(target_count - actual_count)} soru daha {'ekleyin' if actual_count < target_count else 'çıkarın'}",
                            "Soru havuzunu genişletin",
                            "Hedef dağılımı revize edin",
                        ],
                    )
                )

        # Genel zorluk ortalaması kontrolü
        avg_difficulty = (
            sum(
                (q.irt_params.difficulty if q.irt_params else q.estimated_difficulty)
                for q in questions
            )
            / total_questions
        )

        # Normalize edilmiş ortalama
        if any(q.irt_params for q in questions):
            normalized_avg = (avg_difficulty + 3) / 6
        else:
            normalized_avg = avg_difficulty

        target_difficulty = blueprint.target_difficulty

        if abs(normalized_avg - target_difficulty) > 0.2:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.DIFFICULTY_BALANCE,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message="Sınav genel zorluk seviyesi hedeften sapıyor",
                    details={
                        "average_difficulty": round(normalized_avg, 2),
                        "target_difficulty": target_difficulty,
                        "difference": round(abs(normalized_avg - target_difficulty), 2),
                    },
                    suggestions=[
                        f"Sınavı {'zorlaştırmak' if normalized_avg < target_difficulty else 'kolaylaştırmak'} için sorular değiştirin",
                        "Hedef zorluğu gözden geçirin",
                    ],
                )
            )

        # Başarılı ise
        if not results:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.DIFFICULTY_BALANCE,
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    message="Zorluk dağılımı dengeli",
                    details={
                        "average_difficulty": round(normalized_avg, 2),
                        "distribution": {
                            k.value: v for k, v in difficulty_counts.items()
                        },
                    },
                )
            )

        return results


# ==================== CURRICULUM MATCH VALIDATOR ====================


class CurriculumMatchValidator:
    """Müfredat Eşleştirme Kontrolü"""

    def __init__(self):
        self.min_coverage_ratio = 0.7  # Minimum %70 kapsama
        logger.info("curriculum_match_validator_initialized")

    def validate_curriculum_alignment(
        self, questions: List[QuestionMetadata], blueprint: ExamBlueprint
    ) -> List[ValidationResult]:
        """Soruların müfredat ile uyumunu kontrol et"""

        results = []

        # 1. Kazanım kapsamı kontrolü
        required_outcomes = set(blueprint.required_learning_outcomes)
        covered_outcomes = set()

        for question in questions:
            covered_outcomes.update(question.learning_outcomes)

        coverage_ratio = (
            len(covered_outcomes & required_outcomes) / len(required_outcomes)
            if required_outcomes
            else 1.0
        )

        if coverage_ratio < blueprint.min_outcomes_coverage:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.CURRICULUM_MATCH,
                    severity=ValidationSeverity.ERROR,
                    passed=False,
                    message="Müfredat kazanımları yetersiz kapsanmış",
                    details={
                        "covered_outcomes": len(covered_outcomes & required_outcomes),
                        "required_outcomes": len(required_outcomes),
                        "coverage_ratio": round(coverage_ratio, 2),
                        "target_ratio": blueprint.min_outcomes_coverage,
                        "missing_outcomes": list(required_outcomes - covered_outcomes)[
                            :10
                        ],  # İlk 10
                    },
                    suggestions=[
                        f"Kapsanmayan {len(required_outcomes - covered_outcomes)} kazanım için soru ekleyin",
                        "Soru havuzunu genişletin",
                        "Hedef kazanımları gözden geçirin",
                    ],
                )
            )

        # 2. Sınıf seviyesi kontrolü
        grade_mismatches = [
            q
            for q in questions
            if q.grade_level
            and q.grade_level != blueprint.exam_type.split("_")[0]  # Basit kontrol
        ]

        if grade_mismatches:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.CURRICULUM_MATCH,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"{len(grade_mismatches)} soru farklı sınıf seviyesinden",
                    details={
                        "mismatched_count": len(grade_mismatches),
                        "questions": [q.question_id for q in grade_mismatches[:5]],
                    },
                    suggestions=[
                        "Sınıf seviyesi uyumlu sorular seçin",
                        "Soru metadatalarını kontrol edin",
                    ],
                )
            )

        # 3. Sınav tipi uyumu
        exam_type_mismatches = [
            q for q in questions if q.exam_type != blueprint.exam_type
        ]

        if exam_type_mismatches:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.CURRICULUM_MATCH,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"{len(exam_type_mismatches)} soru farklı sınav tipi için hazırlanmış",
                    details={
                        "mismatched_count": len(exam_type_mismatches),
                        "expected_type": blueprint.exam_type,
                    },
                    suggestions=[
                        f"{blueprint.exam_type} sınavına uygun sorular kullanın"
                    ],
                )
            )

        # Başarılı
        if not results:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.CURRICULUM_MATCH,
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    message="Müfredat eşleştirmesi başarılı",
                    details={
                        "coverage_ratio": round(coverage_ratio, 2),
                        "covered_outcomes_count": len(
                            covered_outcomes & required_outcomes
                        ),
                    },
                )
            )

        return results


# ==================== TOPIC DISTRIBUTION VALIDATOR ====================


class TopicDistributionValidator:
    """Konu Dağılımı Doğrulayıcı"""

    def __init__(self):
        self.tolerance = 0.1  # %10 tolerans
        logger.info("topic_distribution_validator_initialized")

    def validate_topic_distribution(
        self, questions: List[QuestionMetadata], blueprint: ExamBlueprint
    ) -> List[ValidationResult]:
        """Konu dağılımını doğrula"""

        results = []

        # Mevcut konu dağılımını hesapla
        topic_counts = {}
        for question in questions:
            topic = question.subject
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        total_questions = len(questions)

        # Hedef dağılım ile karşılaştır
        for topic, target_count in blueprint.topic_distribution.items():
            actual_count = topic_counts.get(topic, 0)
            target_ratio = target_count / sum(blueprint.topic_distribution.values())
            actual_ratio = actual_count / total_questions if total_questions > 0 else 0

            difference = abs(actual_count - target_count)
            ratio_difference = abs(actual_ratio - target_ratio)

            if ratio_difference > self.tolerance:
                severity = (
                    ValidationSeverity.ERROR
                    if ratio_difference > 0.2
                    else ValidationSeverity.WARNING
                )
                results.append(
                    ValidationResult(
                        validation_type=ValidationType.TOPIC_DISTRIBUTION,
                        severity=severity,
                        passed=False,
                        message=f"'{topic}' konu dağılımı dengesiz",
                        details={
                            "topic": topic,
                            "actual_count": actual_count,
                            "target_count": target_count,
                            "difference": difference,
                            "actual_ratio": round(actual_ratio, 2),
                            "target_ratio": round(target_ratio, 2),
                        },
                        suggestions=[
                            f"{topic} konusundan {difference} soru {'ekleyin' if actual_count < target_count else 'çıkarın'}",
                            "Soru havuzunu kontrol edin",
                        ],
                    )
                )

        # Planlanmamış konular var mı kontrol et
        extra_topics = set(topic_counts.keys()) - set(
            blueprint.topic_distribution.keys()
        )
        if extra_topics:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.TOPIC_DISTRIBUTION,
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"Planlanmamış konulardan sorular mevcut: {', '.join(extra_topics)}",
                    details={
                        "extra_topics": list(extra_topics),
                        "extra_questions_count": sum(
                            topic_counts[t] for t in extra_topics
                        ),
                    },
                    suggestions=[
                        "Planlanmamış konu sorularını kaldırın veya plana ekleyin"
                    ],
                )
            )

        # Alt konu dağılımı kontrolü (opsiyonel)
        if blueprint.subtopic_distribution:
            subtopic_counts = {}
            for question in questions:
                if question.subtopic:
                    subtopic_counts[question.subtopic] = (
                        subtopic_counts.get(question.subtopic, 0) + 1
                    )

            for subtopic, target_count in blueprint.subtopic_distribution.items():
                actual_count = subtopic_counts.get(subtopic, 0)
                difference = abs(actual_count - target_count)

                if difference > 2:  # 2 soruluk tolerans
                    results.append(
                        ValidationResult(
                            validation_type=ValidationType.TOPIC_DISTRIBUTION,
                            severity=ValidationSeverity.INFO,
                            passed=False,
                            message=f"Alt konu '{subtopic}' dağılımı hedeften farklı",
                            details={
                                "subtopic": subtopic,
                                "actual_count": actual_count,
                                "target_count": target_count,
                                "difference": difference,
                            },
                            suggestions=[
                                f"{subtopic} alt konusundan {difference} soru {'ekleyin' if actual_count < target_count else 'çıkarın'}"
                            ],
                        )
                    )

        # Başarılı
        if not results:
            results.append(
                ValidationResult(
                    validation_type=ValidationType.TOPIC_DISTRIBUTION,
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    message="Konu dağılımı dengeli",
                    details={"distribution": topic_counts},
                )
            )

        return results


# ==================== UNIFIED VALIDATOR ====================


class ExamQualityValidator:
    """Birleşik Sınav Kalite Doğrulayıcı"""

    def __init__(self):
        self.irt_validator = IRTCalibrationValidator()
        self.difficulty_validator = DifficultyBalanceValidator()
        self.curriculum_validator = CurriculumMatchValidator()
        self.topic_validator = TopicDistributionValidator()

        logger.info("exam_quality_validator_initialized")

    def validate_exam(
        self, questions: List[QuestionMetadata], blueprint: ExamBlueprint
    ) -> Dict[str, Any]:
        """Sınavın tüm kalite kontrollerini yap"""

        logger.info(
            "exam_validation_started",
            exam_id=blueprint.exam_id,
            question_count=len(questions),
        )

        all_results = []

        # 1. IRT Kalibrasyon kontrolü (her soru için)
        irt_results = []
        for question in questions:
            irt_results.extend(self.irt_validator.validate_irt_parameters(question))
        all_results.extend(irt_results)

        # 2. Zorluk dengeleme kontrolü
        difficulty_results = self.difficulty_validator.validate_difficulty_distribution(
            questions, blueprint
        )
        all_results.extend(difficulty_results)

        # 3. Müfredat eşleştirme kontrolü
        curriculum_results = self.curriculum_validator.validate_curriculum_alignment(
            questions, blueprint
        )
        all_results.extend(curriculum_results)

        # 4. Konu dağılımı kontrolü
        topic_results = self.topic_validator.validate_topic_distribution(
            questions, blueprint
        )
        all_results.extend(topic_results)

        # Sonuçları özetle
        summary = self._create_summary(all_results)

        logger.info(
            "exam_validation_completed",
            exam_id=blueprint.exam_id,
            total_checks=len(all_results),
            passed=summary["passed_count"],
            failed=summary["failed_count"],
            overall_status=summary["overall_status"],
        )

        return {
            "exam_id": blueprint.exam_id,
            "exam_name": blueprint.exam_name,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "total_questions": len(questions),
            "summary": summary,
            "results": [r.model_dump(mode="json") for r in all_results],
        }

    def _create_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Doğrulama sonuçlarının özetini oluştur"""

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        # Şiddet bazlı sayım
        severity_counts = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 0,
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.CRITICAL: 0,
        }

        for result in results:
            severity_counts[result.severity] += 1

        # Tip bazlı sayım
        type_counts = {}
        for result in results:
            type_name = result.validation_type.value
            if type_name not in type_counts:
                type_counts[type_name] = {"total": 0, "passed": 0, "failed": 0}
            type_counts[type_name]["total"] += 1
            if result.passed:
                type_counts[type_name]["passed"] += 1
            else:
                type_counts[type_name]["failed"] += 1

        # Genel durum
        has_critical = severity_counts[ValidationSeverity.CRITICAL] > 0
        has_errors = severity_counts[ValidationSeverity.ERROR] > 0
        has_warnings = severity_counts[ValidationSeverity.WARNING] > 0

        if has_critical:
            overall_status = "CRITICAL"
        elif has_errors:
            overall_status = "FAILED"
        elif has_warnings:
            overall_status = "PASSED_WITH_WARNINGS"
        else:
            overall_status = "PASSED"

        return {
            "overall_status": overall_status,
            "total_checks": total,
            "passed_count": passed,
            "failed_count": failed,
            "pass_rate": round(passed / total, 2) if total > 0 else 0,
            "severity_breakdown": {k.value: v for k, v in severity_counts.items()},
            "validation_type_breakdown": type_counts,
            "ready_for_use": overall_status in ["PASSED", "PASSED_WITH_WARNINGS"],
        }


# ==================== SINGLETON INSTANCE ====================

_validator_instance = None


def get_exam_validator() -> ExamQualityValidator:
    """Singleton exam validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ExamQualityValidator()
    return _validator_instance
