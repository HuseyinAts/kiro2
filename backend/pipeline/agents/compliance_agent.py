"""
ÖSYM Compliance Validator Agent (Stage 4)
ÖSYM standartlarına uyumluluk kontrolü

Weight: 20%

Requirements (REQ-4.x):
- REQ-4.1: ÖSYM format kontrolü yapar
- REQ-4.2: Soru metni, 4 seçenek (A, B, C, D), doğru cevap varlığını doğrular
- REQ-4.3: Maksimum 150 kelime sınırını uygular
- REQ-4.4: Seçeneklerin benzer uzunlukta olmasını kontrol eder
- REQ-4.5: Görsel kalitesi ve erişilebilirliğini kontrol eder
- REQ-4.6: Compliance skoru >= 95% bekler
"""

import time
from typing import Any

from ..stage_base import BasePipelineStage, StageInput, StageOutput


class ComplianceAgent(BasePipelineStage):
    """
    ÖSYM Uyumluluk Doğrulama Agent'ı (Aşama 4)

    ÖSYM sınav formatına uygunluğu kontrol eder.
    """

    STAGE_NAME = "osym_compliance"
    STAGE_WEIGHT = 0.20  # 20%

    # ÖSYM standartları
    MAX_QUESTION_WORDS = 150
    MIN_OPTION_COUNT = 4
    MAX_OPTION_COUNT = 4
    VALID_LABELS = ["A", "B", "C", "D"]

    # Seçenek uzunluk toleransı
    OPTION_LENGTH_TOLERANCE = 0.5  # 50% fark kabul edilir

    # Hedef compliance skoru
    TARGET_COMPLIANCE = 0.95

    def __init__(
        self,
        llm_client: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        """
        Compliance Agent başlat

        Args:
            llm_client: LLM istemcisi (opsiyonel)
            config: Ek konfigürasyon
        """
        super().__init__(self.STAGE_NAME, llm_client, config)

    async def process(self, input_data: StageInput) -> StageOutput:
        """
        ÖSYM uyumluluk kontrolü yap

        Args:
            input_data: Pipeline girişi

        Returns:
            StageOutput: Uyumluluk sonucu ve skor
        """
        start_time = time.time()
        errors = []
        warnings = []
        suggestions = []
        checks = {}

        try:
            question_data = input_data.question_data

            # 1. Format kontrolü (REQ-4.1, REQ-4.2)
            format_valid, format_errors = self._check_format(question_data)
            checks["format"] = format_valid
            errors.extend(format_errors)

            # 2. Kelime sayısı kontrolü (REQ-4.3)
            word_count_valid, word_count = self._check_word_count(question_data)
            checks["word_count"] = word_count_valid
            if not word_count_valid:
                warnings.append(f"Soru {word_count} kelime (max: {self.MAX_QUESTION_WORDS})")
                suggestions.append("Soru metnini kısaltın")

            # 3. Seçenek uzunluk kontrolü (REQ-4.4)
            option_length_valid, length_issues = self._check_option_lengths(question_data)
            checks["option_length"] = option_length_valid
            warnings.extend(length_issues[:2])

            # 4. Görsel kontrolü (REQ-4.5)
            visual_valid, visual_issues = self._check_visuals(question_data)
            checks["visual"] = visual_valid
            if visual_issues:
                warnings.extend(visual_issues[:2])

            # 5. Doğru cevap kontrolü
            correct_answer_valid = self._check_correct_answer(question_data)
            checks["correct_answer"] = correct_answer_valid
            if not correct_answer_valid:
                errors.append("Geçerli doğru cevap bulunamadı")

            # 6. Ek ÖSYM kontrolleri
            additional_checks = self._additional_osym_checks(question_data)
            checks.update(additional_checks["checks"])
            warnings.extend(additional_checks["warnings"])

            # Compliance skoru hesapla (REQ-4.6)
            compliance_score = self._calculate_compliance_score(checks)

            # Genel skor
            score = compliance_score
            passed = compliance_score >= self.TARGET_COMPLIANCE

            if not passed:
                suggestions.append(f"Hedef uyumluluk: {self.TARGET_COMPLIANCE * 100:.0f}%")

            # Output verisi
            output_data = {
                **question_data,
                "compliance_score": compliance_score,
                "compliance_checks": checks
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
                    "compliance_score": compliance_score,
                    "checks": checks,
                    "word_count": word_count
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_output(
                f"Uyumluluk kontrol hatası: {e!s}",
                input_data,
                time.time() - start_time
            )

    def get_stage_weight(self) -> float:
        """Stage ağırlığı: 20%"""
        return self.STAGE_WEIGHT

    def _check_format(self, question_data: dict) -> tuple[bool, list[str]]:
        """
        Format kontrolü

        Args:
            question_data: Soru verisi

        Returns:
            Tuple[bool, List[str]]: (Geçerli mi, Hatalar)
        """
        errors = []

        # Soru metni
        question_text = question_data.get("question_text", "")
        if not question_text or len(question_text.strip()) < 10:
            errors.append("Soru metni eksik veya çok kısa")

        # Seçenekler
        options = question_data.get("options", [])
        if not options or len(options) != self.MIN_OPTION_COUNT:
            errors.append(f"Tam {self.MIN_OPTION_COUNT} seçenek gerekli")
        else:
            # Label kontrolü
            labels = [opt.get("label") if isinstance(opt, dict) else None for opt in options]
            if sorted(labels) != self.VALID_LABELS:
                errors.append("Seçenek etiketleri A, B, C, D olmalı")

            # Boş seçenek kontrolü
            for opt in options:
                text = opt.get("text", "") if isinstance(opt, dict) else str(opt)
                if not text or len(text.strip()) < 1:
                    errors.append("Boş seçenek var")
                    break

        # Doğru cevap
        correct_answer = question_data.get("correct_answer", "")
        if not correct_answer or correct_answer not in self.VALID_LABELS:
            errors.append(f"Doğru cevap A, B, C, D olmalı: '{correct_answer}'")

        return len(errors) == 0, errors

    def _check_word_count(self, question_data: dict) -> tuple[bool, int]:
        """
        Kelime sayısı kontrolü

        Args:
            question_data: Soru verisi

        Returns:
            Tuple[bool, int]: (Geçerli mi, Kelime sayısı)
        """
        question_text = question_data.get("question_text", "")
        context = question_data.get("context", "")

        # Toplam metin
        total_text = f"{question_text} {context}".strip()
        word_count = len(total_text.split())

        return word_count <= self.MAX_QUESTION_WORDS, word_count

    def _check_option_lengths(self, question_data: dict) -> tuple[bool, list[str]]:
        """
        Seçenek uzunluk dengesi kontrolü

        Args:
            question_data: Soru verisi

        Returns:
            Tuple[bool, List[str]]: (Dengeli mi, Uyarılar)
        """
        options = question_data.get("options", [])
        if not options:
            return False, ["Seçenek bulunamadı"]

        # Uzunlukları hesapla
        lengths = []
        for opt in options:
            text = opt.get("text", "") if isinstance(opt, dict) else str(opt)
            lengths.append(len(text))

        if not lengths:
            return False, ["Seçenek metni bulunamadı"]

        avg_length = sum(lengths) / len(lengths)
        issues = []

        # Uzunluk farkını kontrol et
        for i, length in enumerate(lengths):
            if avg_length > 0:
                deviation = abs(length - avg_length) / avg_length
                if deviation > self.OPTION_LENGTH_TOLERANCE:
                    label = self.VALID_LABELS[i] if i < len(self.VALID_LABELS) else str(i)
                    issues.append(f"Seçenek {label} uzunluğu dengesiz")

        return len(issues) == 0, issues

    def _check_visuals(self, question_data: dict) -> tuple[bool, list[str]]:
        """
        Görsel kontrolü

        Args:
            question_data: Soru verisi

        Returns:
            Tuple[bool, List[str]]: (Geçerli mi, Uyarılar)
        """
        issues = []

        # Görsel referansı var mı
        question_text = question_data.get("question_text", "")
        has_visual_reference = any(
            word in question_text.lower()
            for word in ["şekil", "grafik", "tablo", "resim", "diyagram"]
        )

        # Görsel URL'i var mı
        visual_url = question_data.get("visual_url", question_data.get("image_url", ""))

        if has_visual_reference and not visual_url:
            issues.append("Görsel referansı var ama görsel eklenmemiş")

        # Alt text kontrolü (erişilebilirlik)
        if visual_url:
            alt_text = question_data.get("visual_alt_text", "")
            if not alt_text:
                issues.append("Görsel için alt text eksik (erişilebilirlik)")

        return len(issues) == 0, issues

    def _check_correct_answer(self, question_data: dict) -> bool:
        """
        Doğru cevap kontrolü

        Args:
            question_data: Soru verisi

        Returns:
            bool: Geçerli mi
        """
        correct_answer = question_data.get("correct_answer", "")

        # Label formatında mı
        if correct_answer in self.VALID_LABELS:
            # Seçeneklerde doğru işaretli var mı kontrol et
            options = question_data.get("options", [])
            for opt in options:
                if isinstance(opt, dict):
                    if opt.get("label") == correct_answer:
                        return True
                    if opt.get("is_correct", False):
                        return True
            # Label varsa kabul et
            return True

        return False

    def _additional_osym_checks(self, question_data: dict) -> dict:
        """
        Ek ÖSYM kontrolleri

        Args:
            question_data: Soru verisi

        Returns:
            Dict: Kontrol sonuçları ve uyarılar
        """
        checks = {}
        warnings = []

        question_text = question_data.get("question_text", "")

        # Türkçe karakter kontrolü
        turkish_chars = set("çğıöşüÇĞİÖŞÜ")
        has_turkish = any(char in question_text for char in turkish_chars)
        checks["turkish_chars"] = True  # Zorunlu değil ama tercih edilir

        # Soru işareti kontrolü
        checks["question_mark"] = question_text.strip().endswith("?") or \
                                   "aşağıdakilerden" in question_text.lower() or \
                                   "hangisi" in question_text.lower()

        if not checks["question_mark"]:
            warnings.append("Soru soru işareti veya soru kalıbı içermeli")

        # Negatif soru kontrolü
        negative_words = ["değildir", "olmayan", "hariç", "dışında"]
        has_negative = any(word in question_text.lower() for word in negative_words)
        if has_negative:
            # Negatif kelime vurgulanmalı
            if not any(word.upper() in question_text for word in negative_words):
                warnings.append("Negatif kelimeler büyük harfle vurgulanmalı")
        checks["negative_emphasized"] = not has_negative or any(
            word.upper() in question_text for word in negative_words
        )

        # Çift negatif kontrolü
        negative_count = sum(1 for word in negative_words if word in question_text.lower())
        checks["no_double_negative"] = negative_count <= 1
        if negative_count > 1:
            warnings.append("Çift negatif kullanımı karışıklığa yol açabilir")

        return {"checks": checks, "warnings": warnings}

    def _calculate_compliance_score(self, checks: dict[str, bool]) -> float:
        """
        Compliance skoru hesapla

        Args:
            checks: Kontrol sonuçları

        Returns:
            float: Compliance skoru (0-1)
        """
        if not checks:
            return 0.0

        # Ağırlıklar
        weights = {
            "format": 0.30,
            "word_count": 0.15,
            "option_length": 0.15,
            "visual": 0.10,
            "correct_answer": 0.20,
            "question_mark": 0.05,
            "negative_emphasized": 0.03,
            "no_double_negative": 0.02
        }

        total_score = 0.0
        total_weight = 0.0

        for check_name, passed in checks.items():
            weight = weights.get(check_name, 0.05)
            total_weight += weight
            if passed:
                total_score += weight

        if total_weight == 0:
            return 0.0

        return round(total_score / total_weight, 4)

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
            suggestions=["Soru formatını kontrol edin"],
            metadata={"stage": self.STAGE_NAME, "error": True},
            execution_time=execution_time
        )
