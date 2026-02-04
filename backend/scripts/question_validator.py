"""
AI-Generated Question Quality Validator
BEST PRACTICE: QUEST Framework + Bloom's Taxonomy + IRT Analysis
Araştırma: BMC Medical Education 2025, arxiv.org/abs/2508.08314
"""
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
import anthropic
import openai


class QualityLevel(Enum):
    """Kalite seviyeleri"""

    EXCELLENT = "excellent"  # 90-100 puan
    GOOD = "good"  # 75-89 puan
    ACCEPTABLE = "acceptable"  # 60-74 puan
    NEEDS_REVISION = "needs_revision"  # 40-59 puan
    REJECT = "reject"  # 0-39 puan


class ValidationResult(BaseModel):
    """Doğrulama sonucu"""

    overall_score: float  # 0-100
    quality_level: QualityLevel
    approved: bool

    # Alt skorlar
    content_quality: float  # 0-100
    difficulty_accuracy: float  # 0-100
    bloom_alignment: float  # 0-100
    distractor_quality: float  # 0-100 (yanlış seçeneklerin kalitesi)
    language_quality: float  # 0-100
    pedagogical_value: float  # 0-100

    # Feedback
    strengths: List[str]
    weaknesses: List[str]
    revision_suggestions: List[str]

    # IRT prediction
    predicted_difficulty: float  # 0.0-1.0 (IRT b parameter)
    predicted_discrimination: float  # 0.0-4.0 (IRT a parameter)


class QuestionValidator:
    """
    QUEST Framework tabanlı soru doğrulayıcı
    Research: Ensuring Quality in AI-Generated Multiple-Choice Questions
    """

    def __init__(self, use_ai_validator: bool = True):
        """
        use_ai_validator: True = Claude/GPT ile otomatik validasyon
                          False = Sadece rule-based validation
        """
        self.use_ai = use_ai_validator
        if use_ai_validator:
            self.claude_client = anthropic.Anthropic()
            self.gpt_client = openai.OpenAI()

    # ========================================================================
    # RULE-BASED VALIDATION (Fast, Deterministic)
    # ========================================================================

    def validate_format(self, question: Dict) -> Tuple[bool, List[str]]:
        """Format kontrolü"""
        errors = []

        # Required fields
        required_fields = ["metin", "secenekler", "dogru_cevap"]
        for field in required_fields:
            if field not in question:
                errors.append(f"Eksik alan: {field}")

        # Seçenekler kontrolü
        if "secenekler" in question:
            if len(question["secenekler"]) != 5:
                errors.append("5 seçenek olmalı (A, B, C, D, E)")

            if not all(
                k in ["A", "B", "C", "D", "E"] for k in question["secenekler"].keys()
            ):
                errors.append("Seçenek harfleri A-E arası olmalı")

        # Doğru cevap kontrolü
        if "dogru_cevap" in question and "secenekler" in question:
            if question["dogru_cevap"] not in question["secenekler"]:
                errors.append("Doğru cevap seçeneklerde yok")

        return len(errors) == 0, errors

    def validate_language(self, question: Dict) -> Tuple[float, List[str]]:
        """
        Dil kalitesi kontrolü
        BEST PRACTICE: Otomatik gramer kontrolü
        """
        issues = []
        score = 100.0

        metin = question.get("metin", "")

        # Türkçe karakter kontrolü
        if not any(c in metin for c in "çğıöşüÇĞİÖŞÜ"):
            issues.append("Türkçe özel karakter yok (şüpheli)")
            score -= 10

        # Cümle uzunluğu (çok uzun = anlaşılmaz)
        word_count = len(metin.split())
        if word_count > 100:
            issues.append(f"Soru çok uzun ({word_count} kelime)")
            score -= 15

        # Noktalama kontrolü
        if not metin.strip().endswith("?"):
            issues.append("Soru '?' ile bitmiyor")
            score -= 10

        # Seçenek uzunluğu dengesizliği
        if "secenekler" in question:
            lengths = [len(v) for v in question["secenekler"].values()]
            avg_len = sum(lengths) / len(lengths)
            if max(lengths) > avg_len * 3:
                issues.append("Bir seçenek diğerlerinden çok uzun (ipucu olabilir)")
                score -= 15

        return max(score, 0), issues

    def validate_distractors(self, question: Dict) -> Tuple[float, List[str]]:
        """
        Distractor (yanlış seçenekler) kalitesi
        BEST PRACTICE: Plausible distractors
        """
        issues = []
        score = 100.0

        secenekler = question.get("secenekler", {})
        dogru = question.get("dogru_cevap")

        if not secenekler or not dogru:
            return 0, ["Seçenekler veya doğru cevap eksik"]

        # Tüm seçenekler aynı uzunlukta mı? (çok benzer = iyi)
        lengths = [len(v) for v in secenekler.values()]
        length_variance = max(lengths) - min(lengths)

        if length_variance > 50:
            issues.append("Seçenekler uzunluk olarak çok farklı")
            score -= 20

        # "Hepsi" veya "Hiçbiri" gibi açık ipuçları
        suspicious_words = ["hepsi", "hiçbiri", "asla", "kesinlikle", "her zaman"]
        for key, val in secenekler.items():
            if any(word in val.lower() for word in suspicious_words):
                issues.append(f"Seçenek {key} şüpheli kelime içeriyor: {val[:50]}...")
                score -= 15

        return max(score, 0), issues

    def predict_difficulty_irt(self, question: Dict) -> float:
        """
        IRT b parametresi (zorluk) tahmini
        BEST PRACTICE: AutoIRT approach (ML-based)
        """
        # Basit heuristik (gerçek sistemde ML model kullanılmalı)
        difficulty = 0.0

        metin = question.get("metin", "")
        word_count = len(metin.split())

        # Kelime sayısı → zorluk
        if word_count > 80:
            difficulty += 0.3
        elif word_count > 50:
            difficulty += 0.1

        # Matematiksel ifadeler → zorluk
        if any(char in metin for char in ["∫", "∑", "√", "²", "³"]):
            difficulty += 0.2

        # Çoklu kavram → zorluk
        concepts = question.get("kazanim", "").split(",")
        if len(concepts) > 2:
            difficulty += 0.2

        # Bloom seviyesi → zorluk
        bloom_difficulty = {
            "remember": 0.0,
            "understand": 0.1,
            "apply": 0.3,
            "analyze": 0.5,
            "evaluate": 0.7,
            "create": 0.9,
        }
        bloom_level = question.get("bloom_level", "understand")
        difficulty += bloom_difficulty.get(bloom_level, 0.3)

        return min(difficulty, 1.0)

    def predict_discrimination_irt(self, question: Dict) -> float:
        """
        IRT a parametresi (ayırt edicilik) tahmini
        Yüksek = soru iyi öğrenciyi ayırt eder
        """
        discrimination = 1.0  # Orta seviye baseline

        # Distractor kalitesi yüksekse → ayırt edicilik yüksek
        distractor_score, _ = self.validate_distractors(question)
        if distractor_score > 80:
            discrimination += 0.5
        elif distractor_score < 50:
            discrimination -= 0.3

        # Açık ipuçları varsa → ayırt edicilik düşük
        metin = question.get("metin", "")
        if "aşağıdakilerden hangisi" in metin.lower():
            discrimination += 0.2  # Standart format, iyi

        return max(0.5, min(discrimination, 2.5))

    # ========================================================================
    # AI-POWERED VALIDATION (Slow, Intelligent)
    # ========================================================================

    async def validate_with_claude(self, question: Dict) -> Dict:
        """
        Claude ile pedagojik kalite analizi
        BEST PRACTICE: Claude'un empati ve pedagojik anlayışı
        """
        prompt = f"""Sen bir eğitim uzmanısın. Aşağıdaki TYT/AYT sorusunu değerlendir:

**SORU:**
{question.get('metin', '')}

**SEÇENEKLER:**
{chr(10).join(f"{k}) {v}" for k, v in question.get('secenekler', {}).items())}

**DOĞRU CEVAP:** {question.get('dogru_cevap', '')}

**DEĞERLENDİRME KRİTERLERİ:**
1. **İçerik Kalitesi (0-100):** Soru anlamlı ve pedagojik değeri var mı?
2. **Distractor Kalitesi (0-100):** Yanlış seçenekler plausible (inandırıcı) mı?
3. **Dil Kalitesi (0-100):** Türkçe kusursuz mu?
4. **Pedagojik Değer (0-100):** Öğrenciye ne öğretiyor?

**ÇIKTI (JSON):**
{{
    "content_quality": 85,
    "distractor_quality": 75,
    "language_quality": 90,
    "pedagogical_value": 80,
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "revision_suggestions": ["...", "..."]
}}
"""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            import json

            return json.loads(response.content[0].text)

        except Exception as e:
            print(f"Claude validation error: {e}")
            return {
                "content_quality": 70,
                "distractor_quality": 70,
                "language_quality": 70,
                "pedagogical_value": 70,
                "strengths": [],
                "weaknesses": [f"AI validation failed: {e}"],
                "revision_suggestions": [],
            }

    # ========================================================================
    # MAIN VALIDATION PIPELINE
    # ========================================================================

    async def validate(self, question: Dict) -> ValidationResult:
        """
        Ana validasyon pipeline
        BEST PRACTICE: Multi-stage validation
        """
        # Stage 1: Format validation (fast, mandatory)
        format_ok, format_errors = self.validate_format(question)
        if not format_ok:
            return ValidationResult(
                overall_score=0,
                quality_level=QualityLevel.REJECT,
                approved=False,
                content_quality=0,
                difficulty_accuracy=0,
                bloom_alignment=0,
                distractor_quality=0,
                language_quality=0,
                pedagogical_value=0,
                strengths=[],
                weaknesses=format_errors,
                revision_suggestions=["Format hatalarını düzelt"],
                predicted_difficulty=0.5,
                predicted_discrimination=1.0,
            )

        # Stage 2: Rule-based validation (fast)
        language_score, language_issues = self.validate_language(question)
        distractor_score, distractor_issues = self.validate_distractors(question)

        # Stage 3: IRT predictions
        predicted_difficulty = self.predict_difficulty_irt(question)
        predicted_discrimination = self.predict_discrimination_irt(question)

        # Stage 4: AI validation (slow, optional)
        if self.use_ai:
            ai_result = await self.validate_with_claude(question)
            content_quality = ai_result.get("content_quality", 70)
            pedagogical_value = ai_result.get("pedagogical_value", 70)
            strengths = ai_result.get("strengths", [])
            weaknesses = ai_result.get("weaknesses", [])
            revision_suggestions = ai_result.get("revision_suggestions", [])
        else:
            content_quality = 75
            pedagogical_value = 75
            strengths = ["Format doğru"]
            weaknesses = language_issues + distractor_issues
            revision_suggestions = ["Uzman kontrolü gerekli"]

        # Stage 5: Calculate overall score
        overall_score = (
            content_quality * 0.25
            + language_score * 0.20
            + distractor_score * 0.25
            + pedagogical_value * 0.20
            + (100 - abs(predicted_difficulty - 0.5) * 100) * 0.10  # Orta zorluk ideal
        )

        # Determine quality level
        if overall_score >= 90:
            quality_level = QualityLevel.EXCELLENT
            approved = True
        elif overall_score >= 75:
            quality_level = QualityLevel.GOOD
            approved = True
        elif overall_score >= 60:
            quality_level = QualityLevel.ACCEPTABLE
            approved = True  # Ama revizyon önerilir
        elif overall_score >= 40:
            quality_level = QualityLevel.NEEDS_REVISION
            approved = False
        else:
            quality_level = QualityLevel.REJECT
            approved = False

        return ValidationResult(
            overall_score=round(overall_score, 2),
            quality_level=quality_level,
            approved=approved,
            content_quality=content_quality,
            difficulty_accuracy=100 - abs(predicted_difficulty - 0.5) * 100,
            bloom_alignment=80,  # Placeholder (gerçekte Bloom taxonomy classifier gerekir)
            distractor_quality=distractor_score,
            language_quality=language_score,
            pedagogical_value=pedagogical_value,
            strengths=strengths,
            weaknesses=weaknesses,
            revision_suggestions=revision_suggestions,
            predicted_difficulty=predicted_difficulty,
            predicted_discrimination=predicted_discrimination,
        )


# ============================================================================
# BATCH VALIDATION
# ============================================================================


async def validate_batch(
    questions: List[Dict], validator: Optional[QuestionValidator] = None
) -> List[ValidationResult]:
    """Toplu validasyon"""
    if validator is None:
        validator = QuestionValidator(use_ai_validator=True)

    import asyncio

    tasks = [validator.validate(q) for q in questions]
    results = await asyncio.gather(*tasks)

    return results


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


async def main_example():
    """Örnek kullanım"""
    # Test sorusu
    test_question = {
        "metin": "Bir cisim 10 m/s hızla düşey yukarı atılıyor. Cismin maksimum yüksekliği kaç metredir? (g=10 m/s²)",
        "secenekler": {"A": "2.5 m", "B": "5 m", "C": "10 m", "D": "15 m", "E": "20 m"},
        "dogru_cevap": "B",
        "konu": "Fizik",
        "alt_konu": "Hareket",
        "kazanim": "Düşey atış hareketini analiz edebilme",
        "zorluk": "medium",
        "bloom_level": "apply",
    }

    # Validasyon
    validator = QuestionValidator(use_ai_validator=True)
    result = await validator.validate(test_question)

    print("=== VALIDATION RESULT ===")
    print(f"Overall Score: {result.overall_score}/100")
    print(f"Quality Level: {result.quality_level.value}")
    print(f"Approved: {'✅ YES' if result.approved else '❌ NO'}")
    print(f"\nPredicted IRT Difficulty: {result.predicted_difficulty:.2f}")
    print(f"Predicted IRT Discrimination: {result.predicted_discrimination:.2f}")
    print(f"\nStrengths:")
    for s in result.strengths:
        print(f"  + {s}")
    print(f"\nWeaknesses:")
    for w in result.weaknesses:
        print(f"  - {w}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main_example())
