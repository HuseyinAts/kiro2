"""
A/B Testing Altyapısı

Soru versiyonlarını karşılaştırmak için A/B testing framework'ü.
İstatistiksel anlamlılık testi ve performans karşılaştırması sağlar.

Requirements: REQ-48.61 - REQ-48.64
"""

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExperimentStatus(Enum):
    """Deney durumu"""

    DRAFT = "draft"  # Taslak
    RUNNING = "running"  # Çalışıyor
    PAUSED = "paused"  # Duraklatıldı
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal edildi


class VariantType(Enum):
    """Varyant tipi"""

    CONTROL = "control"  # Kontrol grubu (A)
    TREATMENT = "treatment"  # Test grubu (B)


@dataclass
class Variant:
    """Deney varyantı"""

    id: str
    name: str
    type: VariantType
    question_id: str
    question_text: str
    options: list[str]
    correct_answer: int
    traffic_allocation: float = 0.5  # Trafik dağılımı (0-1 arası)

    # Metrikler
    impressions: int = 0  # Gösterim sayısı
    responses: int = 0  # Yanıt sayısı
    correct_responses: int = 0  # Doğru yanıt sayısı
    total_response_time_seconds: float = 0.0  # Toplam yanıt süresi

    @property
    def response_rate(self) -> float:
        """Yanıt oranı"""
        return self.responses / self.impressions if self.impressions > 0 else 0.0

    @property
    def accuracy_rate(self) -> float:
        """Doğruluk oranı"""
        return self.correct_responses / self.responses if self.responses > 0 else 0.0

    @property
    def average_response_time(self) -> float:
        """Ortalama yanıt süresi (saniye)"""
        return (
            self.total_response_time_seconds / self.responses
            if self.responses > 0
            else 0.0
        )


@dataclass
class Experiment:
    """A/B test deneyi"""

    id: str
    name: str
    description: str
    subject: str
    difficulty_level: str
    status: ExperimentStatus
    variants: list[Variant]
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    minimum_sample_size: int = 100  # Minimum örneklem büyüklüğü
    significance_level: float = 0.05  # p-value eşiği (varsayılan %5)
    winner: str | None = None  # Kazanan varyant ID


@dataclass
class StatisticalTestResult:
    """İstatistiksel test sonucu"""

    is_significant: bool  # İstatistiksel olarak anlamlı mı?
    p_value: float  # p-değeri
    confidence_level: float  # Güven seviyesi (%)
    effect_size: float  # Etki büyüklüğü
    winner_variant_id: str | None  # Kazanan varyant
    recommendation: str  # Öneri


class ABTestingFramework:
    """
    A/B Testing Framework

    REQ-48.61: Experiment design framework
    REQ-48.62: Statistical significance testing (p-value < 0.05)
    REQ-48.63: Performance comparison dashboard
    REQ-48.64: Kazanan versiyonu otomatik seçme
    """

    def __init__(self):
        """Framework'ü başlat"""
        self.experiments: dict[str, Experiment] = {}

    def create_experiment(
        self,
        name: str,
        description: str,
        subject: str,
        difficulty_level: str,
        control_question: dict,
        treatment_question: dict,
        traffic_allocation: tuple[float, float] = (0.5, 0.5),
        minimum_sample_size: int = 100,
        significance_level: float = 0.05,
    ) -> Experiment:
        """
        Yeni A/B test deneyi oluştur (REQ-48.61)

        Args:
            name: Deney adı
            description: Açıklama
            subject: Konu
            difficulty_level: Zorluk seviyesi
            control_question: Kontrol grubu sorusu (A)
            treatment_question: Test grubu sorusu (B)
            traffic_allocation: Trafik dağılımı (A, B) - toplam 1.0 olmalı
            minimum_sample_size: Minimum örneklem büyüklüğü
            significance_level: Anlamlılık seviyesi (varsayılan 0.05)

        Returns:
            Experiment: Oluşturulan deney
        """
        if sum(traffic_allocation) != 1.0:
            raise ValueError("Trafik dağılımı toplamı 1.0 olmalı")

        experiment_id = str(uuid.uuid4())

        # Kontrol varyantı (A)
        control_variant = Variant(
            id=str(uuid.uuid4()),
            name="Control (A)",
            type=VariantType.CONTROL,
            question_id=control_question.get("id", str(uuid.uuid4())),
            question_text=control_question["question_text"],
            options=control_question["options"],
            correct_answer=control_question["correct_answer"],
            traffic_allocation=traffic_allocation[0],
        )

        # Test varyantı (B)
        treatment_variant = Variant(
            id=str(uuid.uuid4()),
            name="Treatment (B)",
            type=VariantType.TREATMENT,
            question_id=treatment_question.get("id", str(uuid.uuid4())),
            question_text=treatment_question["question_text"],
            options=treatment_question["options"],
            correct_answer=treatment_question["correct_answer"],
            traffic_allocation=traffic_allocation[1],
        )

        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            subject=subject,
            difficulty_level=difficulty_level,
            status=ExperimentStatus.DRAFT,
            variants=[control_variant, treatment_variant],
            minimum_sample_size=minimum_sample_size,
            significance_level=significance_level,
        )

        self.experiments[experiment_id] = experiment
        return experiment

    def start_experiment(self, experiment_id: str) -> bool:
        """
        Deneyi başlat

        Args:
            experiment_id: Deney ID

        Returns:
            bool: Başlatma başarılı mı?
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False

        if experiment.status != ExperimentStatus.DRAFT:
            return False

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()
        return True

    def record_impression(self, experiment_id: str, variant_id: str) -> bool:
        """
        Gösterim kaydet

        Args:
            experiment_id: Deney ID
            variant_id: Varyant ID

        Returns:
            bool: Kayıt başarılı mı?
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return False

        variant = self._find_variant(experiment, variant_id)
        if not variant:
            return False

        variant.impressions += 1
        return True

    def record_response(
        self,
        experiment_id: str,
        variant_id: str,
        is_correct: bool,
        response_time_seconds: float,
    ) -> bool:
        """
        Yanıt kaydet

        Args:
            experiment_id: Deney ID
            variant_id: Varyant ID
            is_correct: Doğru mu?
            response_time_seconds: Yanıt süresi (saniye)

        Returns:
            bool: Kayıt başarılı mı?
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return False

        variant = self._find_variant(experiment, variant_id)
        if not variant:
            return False

        variant.responses += 1
        if is_correct:
            variant.correct_responses += 1
        variant.total_response_time_seconds += response_time_seconds

        # Otomatik tamamlama kontrolü
        self._check_auto_completion(experiment)

        return True

    def _check_auto_completion(self, experiment: Experiment) -> None:
        """
        Deney otomatik tamamlanma kontrolü

        Minimum örneklem büyüklüğüne ulaşıldıysa ve istatistiksel
        anlamlılık varsa deneyi otomatik tamamla.
        """
        # Minimum örneklem kontrolü
        min_responses = min(v.responses for v in experiment.variants)
        if min_responses < experiment.minimum_sample_size:
            return

        # İstatistiksel test yap
        result = self.run_statistical_test(experiment.id)

        # Anlamlı sonuç varsa tamamla
        if result and result.is_significant:
            self.complete_experiment(experiment.id, auto_select_winner=True)

    def run_statistical_test(
        self, experiment_id: str, metric: str = "accuracy_rate"
    ) -> StatisticalTestResult | None:
        """
        İstatistiksel anlamlılık testi yap (REQ-48.62)

        Z-test kullanarak iki oran arasındaki farkı test eder.

        Args:
            experiment_id: Deney ID
            metric: Test edilecek metrik (accuracy_rate, response_rate)

        Returns:
            StatisticalTestResult veya None
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or len(experiment.variants) != 2:
            return None

        control = experiment.variants[0]
        treatment = experiment.variants[1]

        # Metrik değerlerini al
        if metric == "accuracy_rate":
            p1 = control.accuracy_rate
            n1 = control.responses
            p2 = treatment.accuracy_rate
            n2 = treatment.responses
        elif metric == "response_rate":
            p1 = control.response_rate
            n1 = control.impressions
            p2 = treatment.response_rate
            n2 = treatment.impressions
        else:
            return None

        # Yeterli veri var mı?
        if n1 < 30 or n2 < 30:
            return StatisticalTestResult(
                is_significant=False,
                p_value=1.0,
                confidence_level=0.0,
                effect_size=0.0,
                winner_variant_id=None,
                recommendation="Yeterli veri yok. Minimum 30 örneklem gerekli.",
            )

        # Z-test hesapla
        p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / n1 + 1 / n2))

        if se == 0:
            z_score = 0.0
        else:
            z_score = (p2 - p1) / se

        # P-value hesapla (two-tailed test)
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))

        # İstatistiksel anlamlılık (REQ-48.62: p < 0.05)
        is_significant = p_value < experiment.significance_level

        # Güven seviyesi
        confidence_level = (1 - p_value) * 100

        # Etki büyüklüğü (Cohen's h)
        effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))

        # Kazanan belirle
        winner_variant_id = None
        if is_significant:
            if p2 > p1:
                winner_variant_id = treatment.id
            else:
                winner_variant_id = control.id

        # Öneri oluştur
        recommendation = self._generate_recommendation(
            is_significant, p_value, p1, p2, winner_variant_id, treatment.id
        )

        return StatisticalTestResult(
            is_significant=is_significant,
            p_value=round(p_value, 4),
            confidence_level=round(confidence_level, 2),
            effect_size=round(effect_size, 4),
            winner_variant_id=winner_variant_id,
            recommendation=recommendation,
        )

    def _normal_cdf(self, x: float) -> float:
        """
        Standart normal dağılım kümülatif dağılım fonksiyonu

        Yaklaşık hesaplama (error function kullanarak)
        """
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    def _generate_recommendation(
        self,
        is_significant: bool,
        p_value: float,
        p1: float,
        p2: float,
        winner_id: str | None,
        treatment_id: str,
    ) -> str:
        """Öneri metni oluştur"""
        if not is_significant:
            return (
                f"İstatistiksel olarak anlamlı fark yok (p={p_value:.4f}). "
                f"Daha fazla veri toplayın veya kontrol grubunu kullanmaya devam edin."
            )

        if winner_id == treatment_id:
            improvement = ((p2 - p1) / p1) * 100 if p1 > 0 else 0
            return (
                f"✅ Treatment (B) versiyonu anlamlı şekilde daha iyi (p={p_value:.4f}). "
                f"Performans artışı: %{improvement:.1f}. Treatment versiyonunu kullanın."
            )
        decline = ((p1 - p2) / p1) * 100 if p1 > 0 else 0
        return (
            f"⚠️ Control (A) versiyonu anlamlı şekilde daha iyi (p={p_value:.4f}). "
            f"Treatment %{decline:.1f} daha düşük performans gösteriyor. "
            f"Control versiyonunu kullanmaya devam edin."
        )

    def complete_experiment(
        self, experiment_id: str, auto_select_winner: bool = True
    ) -> bool:
        """
        Deneyi tamamla (REQ-48.64)

        Args:
            experiment_id: Deney ID
            auto_select_winner: Kazananı otomatik seç mi?

        Returns:
            bool: Tamamlama başarılı mı?
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False

        if experiment.status not in [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]:
            return False

        experiment.status = ExperimentStatus.COMPLETED
        experiment.completed_at = datetime.now()

        # Kazananı otomatik seç (REQ-48.64)
        if auto_select_winner:
            result = self.run_statistical_test(experiment_id)
            if result and result.is_significant and result.winner_variant_id:
                experiment.winner = result.winner_variant_id

        return True

    def get_performance_comparison(self, experiment_id: str) -> dict | None:
        """
        Performans karşılaştırma raporu (REQ-48.63)

        Args:
            experiment_id: Deney ID

        Returns:
            Karşılaştırma raporu dictionary
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        # İstatistiksel test sonucu
        stat_result = self.run_statistical_test(experiment_id)

        # Varyant metrikleri
        variants_data = []
        for variant in experiment.variants:
            variants_data.append(
                {
                    "id": variant.id,
                    "name": variant.name,
                    "type": variant.type.value,
                    "impressions": variant.impressions,
                    "responses": variant.responses,
                    "correct_responses": variant.correct_responses,
                    "response_rate": round(variant.response_rate * 100, 2),
                    "accuracy_rate": round(variant.accuracy_rate * 100, 2),
                    "average_response_time": round(variant.average_response_time, 2),
                    "traffic_allocation": round(variant.traffic_allocation * 100, 2),
                }
            )

        # Karşılaştırma
        if len(experiment.variants) == 2:
            control = experiment.variants[0]
            treatment = experiment.variants[1]

            accuracy_diff = (treatment.accuracy_rate - control.accuracy_rate) * 100
            response_time_diff = (
                treatment.average_response_time - control.average_response_time
            )

            comparison = {
                "accuracy_difference_percent": round(accuracy_diff, 2),
                "response_time_difference_seconds": round(response_time_diff, 2),
                "better_accuracy": "Treatment (B)"
                if accuracy_diff > 0
                else "Control (A)",
                "faster_response": "Treatment (B)"
                if response_time_diff < 0
                else "Control (A)",
            }
        else:
            comparison = {}

        return {
            "experiment_id": experiment.id,
            "name": experiment.name,
            "status": experiment.status.value,
            "subject": experiment.subject,
            "difficulty_level": experiment.difficulty_level,
            "started_at": experiment.started_at.isoformat()
            if experiment.started_at
            else None,
            "completed_at": experiment.completed_at.isoformat()
            if experiment.completed_at
            else None,
            "minimum_sample_size": experiment.minimum_sample_size,
            "significance_level": experiment.significance_level,
            "winner": experiment.winner,
            "variants": variants_data,
            "comparison": comparison,
            "statistical_test": {
                "is_significant": stat_result.is_significant if stat_result else False,
                "p_value": stat_result.p_value if stat_result else None,
                "confidence_level": stat_result.confidence_level
                if stat_result
                else None,
                "effect_size": stat_result.effect_size if stat_result else None,
                "winner_variant_id": stat_result.winner_variant_id
                if stat_result
                else None,
                "recommendation": stat_result.recommendation
                if stat_result
                else "Henüz yeterli veri yok",
            }
            if stat_result
            else None,
        }

    def get_experiment_summary(self, experiment_id: str) -> dict | None:
        """
        Deney özeti

        Args:
            experiment_id: Deney ID

        Returns:
            Özet dictionary
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        total_impressions = sum(v.impressions for v in experiment.variants)
        total_responses = sum(v.responses for v in experiment.variants)

        return {
            "id": experiment.id,
            "name": experiment.name,
            "status": experiment.status.value,
            "total_impressions": total_impressions,
            "total_responses": total_responses,
            "variants_count": len(experiment.variants),
            "winner": experiment.winner,
            "created_at": experiment.created_at.isoformat(),
            "started_at": experiment.started_at.isoformat()
            if experiment.started_at
            else None,
            "completed_at": experiment.completed_at.isoformat()
            if experiment.completed_at
            else None,
        }

    def list_experiments(self, status: ExperimentStatus | None = None) -> list[dict]:
        """
        Deneyleri listele

        Args:
            status: Durum filtresi (opsiyonel)

        Returns:
            Deney özet listesi
        """
        experiments = list(self.experiments.values())

        if status:
            experiments = [e for e in experiments if e.status == status]

        return [self.get_experiment_summary(e.id) for e in experiments]

    def _find_variant(
        self, experiment: Experiment, variant_id: str
    ) -> Variant | None:
        """Varyantı bul"""
        for variant in experiment.variants:
            if variant.id == variant_id:
                return variant
        return None
