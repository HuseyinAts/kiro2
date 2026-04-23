"""
Matematik Adım Adım Çözüm Servisi
Requirements: REQ-51.21-51.40 (Diskalkuli Desteği - Adım Adım Çözüm)

Bu servis matematik problemlerinin adım adım çözümlerini oluşturur ve yönetir.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StepType(str, Enum):
    """Çözüm adımı türleri"""

    SETUP = "setup"  # Problemi kurma
    SIMPLIFICATION = "simplification"  # Basitleştirme
    OPERATION = "operation"  # İşlem yapma
    SUBSTITUTION = "substitution"  # Yerine koyma
    VERIFICATION = "verification"  # Doğrulama
    CONCLUSION = "conclusion"  # Sonuç


class DifficultyLevel(str, Enum):
    """Zorluk seviyeleri"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


@dataclass
class MathSolutionStep:
    """Tek bir çözüm adımı"""

    step_number: int
    step_type: StepType
    title: str
    description: str
    math_expression: str  # LaTeX formatında
    explanation: str
    visual_aids: list[str] | None = None  # Görsel yardımcılar (URL'ler)
    color_coding: dict[str, str] | None = None  # Renk kodlama
    hints: list[str] = field(default_factory=list)  # İpuçları (3 seviye)
    common_errors: list[str] = field(default_factory=list)  # Yaygın hatalar
    duration_estimate_seconds: int = 30  # Tahmini süre

    def to_dict(self) -> dict[str, Any]:
        """Dictionary'e dönüştür"""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "title": self.title,
            "description": self.description,
            "math_expression": self.math_expression,
            "explanation": self.explanation,
            "visual_aids": self.visual_aids or [],
            "color_coding": self.color_coding or {},
            "hints": self.hints,
            "common_errors": self.common_errors,
            "duration_estimate_seconds": self.duration_estimate_seconds,
        }


@dataclass
class MathSolution:
    """Tam matematik çözümü"""

    problem_id: str
    problem_statement: str
    problem_type: str  # algebra, geometry, calculus, etc.
    difficulty_level: DifficultyLevel
    steps: list[MathSolutionStep]
    total_duration_estimate_seconds: int
    prerequisites: list[str] = field(default_factory=list)  # Ön koşul konular
    related_concepts: list[str] = field(default_factory=list)  # İlgili kavramlar
    alternative_methods: list[str] = field(default_factory=list)  # Alternatif yöntemler
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Dictionary'e dönüştür"""
        return {
            "problem_id": self.problem_id,
            "problem_statement": self.problem_statement,
            "problem_type": self.problem_type,
            "difficulty_level": self.difficulty_level.value,
            "steps": [step.to_dict() for step in self.steps],
            "total_steps": len(self.steps),
            "total_duration_estimate_seconds": self.total_duration_estimate_seconds,
            "prerequisites": self.prerequisites,
            "related_concepts": self.related_concepts,
            "alternative_methods": self.alternative_methods,
            "created_at": self.created_at,
        }


class MathSolutionStepService:
    """Matematik adım adım çözüm servisi"""

    def __init__(self):
        self.solutions_cache: dict[str, MathSolution] = {}
        logger.info("MathSolutionStepService initialized")

    def generate_solution(
        self,
        problem_id: str,
        problem_statement: str,
        problem_type: str,
        difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
    ) -> MathSolution:
        """
        Matematik problemi için adım adım çözüm oluştur

        Args:
            problem_id: Problem ID'si
            problem_statement: Problem ifadesi
            problem_type: Problem türü (algebra, geometry, etc.)
            difficulty_level: Zorluk seviyesi

        Returns:
            MathSolution: Tam çözüm
        """
        logger.info(f"Generating solution for problem: {problem_id}")

        # Cache'de varsa dön
        if problem_id in self.solutions_cache:
            logger.info(f"Returning cached solution for: {problem_id}")
            return self.solutions_cache[problem_id]

        # Problem türüne göre çözüm oluştur
        if problem_type == "linear_equation":
            solution = self._generate_linear_equation_solution(
                problem_id, problem_statement, difficulty_level
            )
        elif problem_type == "quadratic_equation":
            solution = self._generate_quadratic_equation_solution(
                problem_id, problem_statement, difficulty_level
            )
        elif problem_type == "fraction_operations":
            solution = self._generate_fraction_operations_solution(
                problem_id, problem_statement, difficulty_level
            )
        else:
            # Genel çözüm şablonu
            solution = self._generate_generic_solution(
                problem_id, problem_statement, problem_type, difficulty_level
            )

        # Cache'e ekle
        self.solutions_cache[problem_id] = solution

        return solution

    def _generate_linear_equation_solution(
        self, problem_id: str, problem_statement: str, difficulty_level: DifficultyLevel
    ) -> MathSolution:
        """Doğrusal denklem çözümü oluştur"""

        # Örnek: 2x + 5 = 13
        steps = [
            MathSolutionStep(
                step_number=1,
                step_type=StepType.SETUP,
                title="Denklemi Yaz",
                description="Problemi matematiksel denklem olarak yazalım",
                math_expression=r"2x + 5 = 13",
                explanation="Verilen denklemi standart formda yazıyoruz",
                hints=[
                    "Denklemi eşitlik işaretine göre düzenle",
                    "Sol tarafta bilinmeyen, sağ tarafta sayılar olmalı",
                    "Denklemi olduğu gibi yaz: 2x + 5 = 13",
                ],
                common_errors=[
                    "Eşitlik işaretini unutmak",
                    "Katsayıları yanlış yazmak",
                ],
                duration_estimate_seconds=20,
            ),
            MathSolutionStep(
                step_number=2,
                step_type=StepType.SIMPLIFICATION,
                title="Sabiti Karşıya At",
                description="5'i eşitliğin sağ tarafına atalım",
                math_expression=r"2x = 13 - 5",
                explanation="Eşitliğin her iki tarafından 5 çıkarıyoruz",
                color_coding={
                    "moved_term": "#FF6B6B",  # Kırmızı - taşınan terim
                    "result": "#51CF66",  # Yeşil - sonuç
                },
                hints=[
                    "Bir terimi karşıya atarken işareti değişir",
                    "+5 karşıya -5 olarak geçer",
                    "13 - 5 işlemini yap",
                ],
                common_errors=[
                    "İşaret değiştirmeyi unutmak",
                    "Yanlış taraftan çıkarmak",
                ],
                duration_estimate_seconds=30,
            ),
            MathSolutionStep(
                step_number=3,
                step_type=StepType.OPERATION,
                title="İşlemi Yap",
                description="Sağ taraftaki çıkarma işlemini yapalım",
                math_expression=r"2x = 8",
                explanation="13 - 5 = 8 işlemini yapıyoruz",
                hints=["13'ten 5 çıkar", "Basit çıkarma işlemi: 13 - 5", "Sonuç: 8"],
                common_errors=["Çıkarma işlemini yanlış yapmak"],
                duration_estimate_seconds=20,
            ),
            MathSolutionStep(
                step_number=4,
                step_type=StepType.SIMPLIFICATION,
                title="x'i Yalnız Bırak",
                description="Her iki tarafı 2'ye bölelim",
                math_expression=r"x = \frac{8}{2}",
                explanation="x'in katsayısı olan 2'yi karşıya bölme olarak atıyoruz",
                color_coding={
                    "coefficient": "#FF6B6B",  # Kırmızı - katsayı
                    "result": "#51CF66",  # Yeşil - sonuç
                },
                hints=[
                    "x'in önündeki sayıyı karşıya at",
                    "2 ile çarpım, karşıya 2'ye bölme olur",
                    "8'i 2'ye böl",
                ],
                common_errors=[
                    "Sadece bir tarafı bölmek",
                    "Bölme yerine çarpma yapmak",
                ],
                duration_estimate_seconds=30,
            ),
            MathSolutionStep(
                step_number=5,
                step_type=StepType.CONCLUSION,
                title="Sonucu Bul",
                description="Bölme işlemini yaparak x'i bulalım",
                math_expression=r"x = 4",
                explanation="8 ÷ 2 = 4, dolayısıyla x = 4",
                hints=["8 bölü 2 kaç eder?", "Basit bölme: 8 ÷ 2", "Cevap: 4"],
                common_errors=["Bölme işlemini yanlış yapmak"],
                duration_estimate_seconds=20,
            ),
            MathSolutionStep(
                step_number=6,
                step_type=StepType.VERIFICATION,
                title="Doğrulama",
                description="Bulduğumuz değeri yerine koyarak kontrol edelim",
                math_expression=r"2(4) + 5 = 13 \quad \checkmark",
                explanation="x = 4'ü orijinal denklemde yerine koyuyoruz: 2×4 + 5 = 8 + 5 = 13 ✓",
                hints=[
                    "x yerine 4 yaz",
                    "İşlemleri sırayla yap",
                    "Sonuç 13'e eşit mi kontrol et",
                ],
                common_errors=["İşlem önceliğini unutmak", "Doğrulama yapmamak"],
                duration_estimate_seconds=40,
            ),
        ]

        total_duration = sum(step.duration_estimate_seconds for step in steps)

        return MathSolution(
            problem_id=problem_id,
            problem_statement=problem_statement,
            problem_type="linear_equation",
            difficulty_level=difficulty_level,
            steps=steps,
            total_duration_estimate_seconds=total_duration,
            prerequisites=["Dört işlem", "Eşitlik kavramı", "Değişken kavramı"],
            related_concepts=[
                "Doğrusal denklemler",
                "Bilinmeyen bulma",
                "Eşitlik özellikleri",
            ],
            alternative_methods=["Grafik yöntemi", "Deneme-yanılma yöntemi"],
        )

    def _generate_quadratic_equation_solution(
        self, problem_id: str, problem_statement: str, difficulty_level: DifficultyLevel
    ) -> MathSolution:
        """İkinci dereceden denklem çözümü oluştur"""

        # Örnek: x² - 5x + 6 = 0
        steps = [
            MathSolutionStep(
                step_number=1,
                step_type=StepType.SETUP,
                title="Denklemi Standart Forma Getir",
                description="İkinci dereceden denklemi ax² + bx + c = 0 formunda yazalım",
                math_expression=r"x^2 - 5x + 6 = 0",
                explanation="a=1, b=-5, c=6 katsayılarını belirliyoruz",
                hints=[
                    "ax² + bx + c = 0 formunu hatırla",
                    "Katsayıları belirle: a, b, c",
                    "a=1, b=-5, c=6",
                ],
                duration_estimate_seconds=30,
            ),
            MathSolutionStep(
                step_number=2,
                step_type=StepType.OPERATION,
                title="Çarpanlara Ayır",
                description="Denklemi çarpanlarına ayıralım",
                math_expression=r"(x - 2)(x - 3) = 0",
                explanation="x² - 5x + 6 = (x-2)(x-3) şeklinde çarpanlara ayrılır",
                hints=[
                    "Hangi iki sayının çarpımı 6, toplamı -5?",
                    "-2 ve -3 sayılarını dene",
                    "(x-2)(x-3) formunu yaz",
                ],
                common_errors=["Yanlış çarpan seçmek", "İşaretleri karıştırmak"],
                duration_estimate_seconds=60,
            ),
            MathSolutionStep(
                step_number=3,
                step_type=StepType.CONCLUSION,
                title="Kökleri Bul",
                description="Her çarpanı sıfıra eşitleyerek kökleri bulalım",
                math_expression=r"x - 2 = 0 \text{ veya } x - 3 = 0",
                explanation="Çarpım sıfırsa, çarpanlardan en az biri sıfırdır",
                hints=[
                    "Her parantezi ayrı ayrı sıfıra eşitle",
                    "x - 2 = 0 ise x = ?",
                    "x - 3 = 0 ise x = ?",
                ],
                duration_estimate_seconds=40,
            ),
            MathSolutionStep(
                step_number=4,
                step_type=StepType.CONCLUSION,
                title="Sonuçları Yaz",
                description="Denklemin köklerini yazalım",
                math_expression=r"x_1 = 2, \quad x_2 = 3",
                explanation="Denklemin iki kökü vardır: x=2 ve x=3",
                hints=["İki kök bulduk", "x₁ = 2", "x₂ = 3"],
                duration_estimate_seconds=20,
            ),
        ]

        total_duration = sum(step.duration_estimate_seconds for step in steps)

        return MathSolution(
            problem_id=problem_id,
            problem_statement=problem_statement,
            problem_type="quadratic_equation",
            difficulty_level=difficulty_level,
            steps=steps,
            total_duration_estimate_seconds=total_duration,
            prerequisites=[
                "Çarpanlara ayırma",
                "Çarpım sıfırsa kuralı",
                "Doğrusal denklemler",
            ],
            related_concepts=[
                "İkinci dereceden denklemler",
                "Çarpanlara ayırma",
                "Kökler",
            ],
            alternative_methods=[
                "Karekök alma yöntemi",
                "Tamamlama yöntemi",
                "Formül yöntemi",
            ],
        )

    def _generate_fraction_operations_solution(
        self, problem_id: str, problem_statement: str, difficulty_level: DifficultyLevel
    ) -> MathSolution:
        """Kesir işlemleri çözümü oluştur"""

        # Örnek: 1/2 + 1/3
        steps = [
            MathSolutionStep(
                step_number=1,
                step_type=StepType.SETUP,
                title="Kesirleri Yaz",
                description="Toplanacak kesirleri yazalım",
                math_expression=r"\frac{1}{2} + \frac{1}{3}",
                explanation="İki kesri toplamak istiyoruz",
                hints=[
                    "Kesirleri yan yana yaz",
                    "Payda ve payları belirle",
                    "1/2 + 1/3",
                ],
                duration_estimate_seconds=20,
            ),
            MathSolutionStep(
                step_number=2,
                step_type=StepType.OPERATION,
                title="Ortak Paydayı Bul",
                description="2 ve 3'ün en küçük ortak katını bulalım",
                math_expression=r"\text{EKOK}(2, 3) = 6",
                explanation="2 ve 3'ün en küçük ortak katı 6'dır",
                hints=[
                    "2'nin katları: 2, 4, 6, 8...",
                    "3'ün katları: 3, 6, 9...",
                    "Ortak en küçük kat: 6",
                ],
                duration_estimate_seconds=40,
            ),
            MathSolutionStep(
                step_number=3,
                step_type=StepType.OPERATION,
                title="Kesirleri Eşitle",
                description="Her iki kesri de paydası 6 olacak şekilde genişletelim",
                math_expression=r"\frac{1 \times 3}{2 \times 3} + \frac{1 \times 2}{3 \times 2} = \frac{3}{6} + \frac{2}{6}",
                explanation="1/2'yi 3 ile, 1/3'ü 2 ile genişletiyoruz",
                color_coding={
                    "multiplier": "#FF6B6B",  # Kırmızı - çarpan
                    "result": "#51CF66",  # Yeşil - sonuç
                },
                hints=[
                    "1/2'yi kaçla çarpmalıyız ki paydası 6 olsun?",
                    "1/3'ü kaçla çarpmalıyız ki paydası 6 olsun?",
                    "Pay ve paydayı aynı sayı ile çarp",
                ],
                common_errors=["Sadece paydayı çarpmak", "Yanlış çarpan seçmek"],
                duration_estimate_seconds=50,
            ),
            MathSolutionStep(
                step_number=4,
                step_type=StepType.OPERATION,
                title="Payları Topla",
                description="Paydalar eşit olduğuna göre payları toplayalım",
                math_expression=r"\frac{3 + 2}{6} = \frac{5}{6}",
                explanation="3 + 2 = 5, payda aynı kalır",
                hints=[
                    "Paydalar aynı, sadece payları topla",
                    "3 + 2 = ?",
                    "Sonuç: 5/6",
                ],
                duration_estimate_seconds=30,
            ),
            MathSolutionStep(
                step_number=5,
                step_type=StepType.CONCLUSION,
                title="Sonucu Yaz",
                description="Toplama işleminin sonucunu yazalım",
                math_expression=r"\frac{1}{2} + \frac{1}{3} = \frac{5}{6}",
                explanation="Sonuç: 5/6 (sadeleştirilmiş hali)",
                hints=[
                    "Sonuç sadeleştirilmiş mi kontrol et",
                    "5 ve 6'nın ortak böleni var mı?",
                    "Cevap: 5/6",
                ],
                duration_estimate_seconds=20,
            ),
        ]

        total_duration = sum(step.duration_estimate_seconds for step in steps)

        return MathSolution(
            problem_id=problem_id,
            problem_statement=problem_statement,
            problem_type="fraction_operations",
            difficulty_level=difficulty_level,
            steps=steps,
            total_duration_estimate_seconds=total_duration,
            prerequisites=["Kesir kavramı", "EKOK bulma", "Kesir genişletme"],
            related_concepts=["Kesir toplama", "Ortak payda", "Kesir sadeleştirme"],
            alternative_methods=["Çapraz çarpım yöntemi"],
        )

    def _generate_generic_solution(
        self,
        problem_id: str,
        problem_statement: str,
        problem_type: str,
        difficulty_level: DifficultyLevel,
    ) -> MathSolution:
        """Genel çözüm şablonu"""

        steps = [
            MathSolutionStep(
                step_number=1,
                step_type=StepType.SETUP,
                title="Problemi Anla",
                description="Problemi dikkatlice okuyalım ve ne istendiğini belirleyelim",
                math_expression=problem_statement,
                explanation="Verilen bilgileri ve istenen sonucu belirleyelim",
                hints=[
                    "Problemi birkaç kez oku",
                    "Verilen bilgileri listele",
                    "Ne bulman gerekiyor?",
                ],
                duration_estimate_seconds=60,
            ),
            MathSolutionStep(
                step_number=2,
                step_type=StepType.SETUP,
                title="Strateji Belirle",
                description="Çözüm için hangi yöntemi kullanacağımıza karar verelim",
                math_expression="",
                explanation="Problem türüne uygun çözüm yöntemini seçelim",
                hints=[
                    "Hangi konu ile ilgili?",
                    "Benzer problemleri hatırla",
                    "Hangi formül veya yöntem kullanılabilir?",
                ],
                duration_estimate_seconds=40,
            ),
            MathSolutionStep(
                step_number=3,
                step_type=StepType.CONCLUSION,
                title="Çözümü Tamamla",
                description="Seçtiğimiz yöntemi uygulayarak çözümü tamamlayalım",
                math_expression="",
                explanation="Adım adım işlemleri yaparak sonuca ulaşalım",
                hints=[
                    "Her adımı dikkatlice yap",
                    "İşlem sırasını takip et",
                    "Sonucu kontrol et",
                ],
                duration_estimate_seconds=120,
            ),
        ]

        total_duration = sum(step.duration_estimate_seconds for step in steps)

        return MathSolution(
            problem_id=problem_id,
            problem_statement=problem_statement,
            problem_type=problem_type,
            difficulty_level=difficulty_level,
            steps=steps,
            total_duration_estimate_seconds=total_duration,
            prerequisites=[],
            related_concepts=[],
            alternative_methods=[],
        )

    def get_step(self, problem_id: str, step_number: int) -> MathSolutionStep | None:
        """Belirli bir adımı getir"""
        solution = self.solutions_cache.get(problem_id)
        if not solution:
            return None

        for step in solution.steps:
            if step.step_number == step_number:
                return step

        return None

    def get_hint(
        self, problem_id: str, step_number: int, hint_level: int = 1
    ) -> str | None:
        """
        Belirli bir adım için ipucu getir

        Args:
            problem_id: Problem ID'si
            step_number: Adım numarası
            hint_level: İpucu seviyesi (1: hafif, 2: orta, 3: detaylı)

        Returns:
            str: İpucu metni veya None
        """
        step = self.get_step(problem_id, step_number)
        if not step or not step.hints:
            return None

        # İpucu seviyesini kontrol et (1-3 arası)
        hint_level = max(1, min(3, hint_level))
        hint_index = hint_level - 1

        if hint_index < len(step.hints):
            return step.hints[hint_index]

        return None

    def clear_cache(self):
        """Cache'i temizle"""
        self.solutions_cache.clear()
        logger.info("Solution cache cleared")


# Global instance
math_solution_step_service = MathSolutionStepService()
