"""
Language Quality Assurance Agent (Stage 5)
Dil kalitesi ve okunabilirlik kontrolü

Weight: 15%

Requirements (REQ-5.x):
- REQ-5.1: Zemberek-NLP ile morfolojik analiz yapar
- REQ-5.2: Yazım hatalarını tespit eder ve düzeltir
- REQ-5.3: Flesch Reading Ease skorunu hesaplar
- REQ-5.4: Öğrenci seviyesine uygun kelime kullanımını kontrol eder
- REQ-5.5: Türkçe noktalama kurallarına uygunluğu doğrular
- REQ-5.6: Anlaşılırlık skoru 60-70 hedefler (lise seviyesi)
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from ..stage_base import BasePipelineStage, StageInput, StageOutput
from ..tools.zemberek_client import ZemberekClient
from ..tools.readability_scorer import TurkishReadabilityScorer


class LanguageQAAgent(BasePipelineStage):
    """
    Dil Kalite Kontrol Agent'ı (Aşama 5)

    Türkçe dil kalitesi, yazım ve okunabilirlik kontrolü yapar.
    """

    STAGE_NAME = "language_qa"
    STAGE_WEIGHT = 0.15  # 15%

    # Hedef okunabilirlik aralığı (lise seviyesi)
    TARGET_READABILITY_MIN = 60
    TARGET_READABILITY_MAX = 70

    # Türkçe noktalama kuralları
    PUNCTUATION_RULES = {
        "sentence_end": [".", "!", "?"],
        "comma_after": ["ancak", "fakat", "lakin", "ama", "ve", "veya"],
        "no_space_before": [".", ",", "!", "?", ":", ";"],
        "space_after": [".", ",", "!", "?", ":", ";"]
    }

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        zemberek_client: Optional[ZemberekClient] = None,
        readability_scorer: Optional[TurkishReadabilityScorer] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Language QA Agent başlat

        Args:
            llm_client: LLM istemcisi
            zemberek_client: Zemberek NLP istemcisi
            readability_scorer: Okunabilirlik skorlayıcı
            config: Ek konfigürasyon
        """
        super().__init__(self.STAGE_NAME, llm_client, config)
        self.zemberek = zemberek_client or ZemberekClient()
        self.readability = readability_scorer or TurkishReadabilityScorer()

    async def process(self, input_data: StageInput) -> StageOutput:
        """
        Dil kalitesi kontrolü yap

        Args:
            input_data: Pipeline girişi

        Returns:
            StageOutput: Dil kalitesi sonucu ve skor
        """
        start_time = time.time()
        errors = []
        warnings = []
        suggestions = []

        try:
            question_data = input_data.question_data
            question_text = question_data.get("question_text", "")

            if not question_text:
                return self._create_error_output(
                    "Soru metni bulunamadı",
                    input_data,
                    time.time() - start_time
                )

            # Tüm metni birleştir
            context = question_data.get("context", "")
            options = question_data.get("options", [])
            option_texts = [
                opt.get("text", "") if isinstance(opt, dict) else str(opt)
                for opt in options
            ]
            full_text = f"{question_text} {context} {' '.join(option_texts)}".strip()

            # 1. Morfolojik analiz (REQ-5.1)
            morphology_valid, morphology_issues = await self._check_morphology(full_text)
            if morphology_issues:
                warnings.extend(morphology_issues[:3])

            # 2. Yazım kontrolü (REQ-5.2)
            spelling_valid, spelling_errors = await self._check_spelling(full_text)
            corrected_text = question_text
            if spelling_errors:
                warnings.extend([f"Yazım hatası: {e}" for e in spelling_errors[:3]])
                suggestions.append("Yazım hatalarını düzeltin")

            # 3. Okunabilirlik skoru (REQ-5.3, REQ-5.6)
            readability_result = self.readability.analyze(full_text)
            readability_valid, readability_score = self._check_readability(
                readability_result.flesch_score
            )
            if not readability_valid:
                warnings.append(
                    f"Okunabilirlik: {readability_result.flesch_score:.0f} "
                    f"(hedef: {self.TARGET_READABILITY_MIN}-{self.TARGET_READABILITY_MAX})"
                )
                suggestions.extend(readability_result.suggestions[:2])

            # 4. Kelime seviyesi kontrolü (REQ-5.4)
            vocabulary_valid, vocabulary_issues = self._check_vocabulary_level(
                full_text, question_data.get("grade_level", 11)
            )
            warnings.extend(vocabulary_issues[:2])

            # 5. Noktalama kontrolü (REQ-5.5)
            punctuation_valid, punctuation_errors = self._check_punctuation(question_text)
            if punctuation_errors:
                warnings.extend(punctuation_errors[:2])

            # Genel skor hesapla
            score = self._calculate_stage_score(
                morphology_valid=morphology_valid,
                spelling_valid=spelling_valid,
                readability_score=readability_score,
                vocabulary_valid=vocabulary_valid,
                punctuation_valid=punctuation_valid
            )

            passed = score >= 0.6

            # Output verisi
            output_data = {
                **question_data,
                "question_text": corrected_text,
                "language_score": score,
                "readability_score": readability_result.flesch_score,
                "readability_level": readability_result.grade_level
            }

            return StageOutput(
                question_data=output_data,
                score=score,
                passed=passed,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "stage": self.STAGE_NAME,
                    "readability": {
                        "flesch_score": readability_result.flesch_score,
                        "grade_level": readability_result.grade_level,
                        "word_count": readability_result.word_count,
                        "avg_sentence_length": readability_result.avg_sentence_length
                    },
                    "spelling_errors_count": len(spelling_errors),
                    "morphology_valid": morphology_valid
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_output(
                f"Dil kalitesi kontrol hatası: {str(e)}",
                input_data,
                time.time() - start_time
            )

    def get_stage_weight(self) -> float:
        """Stage ağırlığı: 15%"""
        return self.STAGE_WEIGHT

    async def _check_morphology(self, text: str) -> Tuple[bool, List[str]]:
        """
        Morfolojik analiz

        Args:
            text: Analiz edilecek metin

        Returns:
            Tuple[bool, List[str]]: (Geçerli mi, Sorunlar)
        """
        is_valid, errors, score = await self.zemberek.validate_turkish_text(text)
        return is_valid, errors

    async def _check_spelling(self, text: str) -> Tuple[bool, List[str]]:
        """
        Yazım kontrolü

        Args:
            text: Kontrol edilecek metin

        Returns:
            Tuple[bool, List[str]]: (Hatasız mı, Hatalar)
        """
        results = await self.zemberek.check_spelling(text)
        spelling_errors = [r.word for r in results if not r.is_correct]
        return len(spelling_errors) == 0, spelling_errors

    def _check_readability(self, flesch_score: float) -> Tuple[bool, float]:
        """
        Okunabilirlik kontrolü

        Args:
            flesch_score: Flesch skoru

        Returns:
            Tuple[bool, float]: (Hedef aralıkta mı, Normalize skor)
        """
        # Hedef aralıkta mı
        in_range = self.TARGET_READABILITY_MIN <= flesch_score <= self.TARGET_READABILITY_MAX

        # Normalize skor
        if in_range:
            normalized_score = 1.0
        elif flesch_score < self.TARGET_READABILITY_MIN:
            # Çok zor
            deviation = (self.TARGET_READABILITY_MIN - flesch_score) / self.TARGET_READABILITY_MIN
            normalized_score = max(0.5, 1.0 - deviation)
        else:
            # Çok kolay
            deviation = (flesch_score - self.TARGET_READABILITY_MAX) / self.TARGET_READABILITY_MAX
            normalized_score = max(0.6, 1.0 - deviation * 0.5)

        return in_range, normalized_score

    def _check_vocabulary_level(
        self,
        text: str,
        grade_level: int
    ) -> Tuple[bool, List[str]]:
        """
        Kelime seviyesi kontrolü

        Args:
            text: Metin
            grade_level: Sınıf seviyesi

        Returns:
            Tuple[bool, List[str]]: (Uygun mu, Uyarılar)
        """
        warnings = []

        # Karmaşık kelimeler (basit kontrol)
        complex_patterns = [
            r'\b\w{15,}\b',  # 15+ harfli kelimeler
        ]

        for pattern in complex_patterns:
            matches = re.findall(pattern, text)
            if matches:
                warnings.append(f"Karmaşık kelimeler: {', '.join(matches[:3])}")

        # Akademik terimler (basit kontrol)
        academic_terms = ["paradigma", "epistemoloji", "ontoloji", "fenomenoloji"]
        found_academic = [term for term in academic_terms if term in text.lower()]
        if found_academic and grade_level < 12:
            warnings.append("Akademik terimler lise seviyesi için zor olabilir")

        return len(warnings) == 0, warnings

    def _check_punctuation(self, text: str) -> Tuple[bool, List[str]]:
        """
        Noktalama kontrolü

        Args:
            text: Metin

        Returns:
            Tuple[bool, List[str]]: (Geçerli mi, Hatalar)
        """
        errors = []

        # Noktalama öncesi boşluk kontrolü
        for punct in self.PUNCTUATION_RULES["no_space_before"]:
            pattern = rf'\s+\{punct}'
            if re.search(pattern, text):
                errors.append(f"'{punct}' öncesi gereksiz boşluk")

        # Cümle sonu kontrolü
        sentences = re.split(r'[.!?]', text)
        for i, sentence in enumerate(sentences[:-1]):  # Son parça hariç
            sentence = sentence.strip()
            if sentence and sentence[-1] not in self.PUNCTUATION_RULES["sentence_end"]:
                # Cümle düzgün bitmiyor olabilir
                pass

        # Çift noktalama
        double_punct = re.findall(r'[.!?,;:]{2,}', text)
        if double_punct:
            errors.append("Çift noktalama işareti tespit edildi")

        # Türkçe tırnak kontrolü
        if '"' in text and '«' not in text and '»' not in text:
            # İngilizce tırnak kullanılmış, ama zorunlu değil
            pass

        return len(errors) == 0, errors

    def _calculate_stage_score(
        self,
        morphology_valid: bool,
        spelling_valid: bool,
        readability_score: float,
        vocabulary_valid: bool,
        punctuation_valid: bool
    ) -> float:
        """
        Aşama skoru hesapla

        Args:
            morphology_valid: Morfoloji geçerli mi
            spelling_valid: Yazım hatasız mı
            readability_score: Okunabilirlik skoru
            vocabulary_valid: Kelime seviyesi uygun mu
            punctuation_valid: Noktalama doğru mu

        Returns:
            float: Aşama skoru (0-1)
        """
        score = 0.0

        # Ağırlıklar
        score += 0.20 if morphology_valid else 0.10
        score += 0.25 if spelling_valid else 0.10
        score += 0.30 * readability_score
        score += 0.15 if vocabulary_valid else 0.08
        score += 0.10 if punctuation_valid else 0.05

        return min(1.0, score)

    def _create_error_output(
        self,
        error_message: str,
        input_data: StageInput,
        execution_time: float
    ) -> StageOutput:
        """Hata output'u oluştur"""
        return StageOutput(
            question_data=input_data.question_data,
            score=0.0,
            passed=False,
            errors=[error_message],
            warnings=[],
            suggestions=["Metin içeriğini kontrol edin"],
            metadata={"stage": self.STAGE_NAME, "error": True},
            execution_time=execution_time
        )
