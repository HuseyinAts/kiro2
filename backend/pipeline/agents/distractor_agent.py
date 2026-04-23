"""
Distractor Generator Agent (Stage 3)
Etkili çeldirici seçenekler üretimi

Weight: 20%

Requirements (REQ-3.x):
- REQ-3.1: 3 çeldirici seçenek üretir
- REQ-3.2: Yaygın öğrenci hatalarını temel alır
- REQ-3.3: Her çeldiricinin plausibility skorunu hesaplar
- REQ-3.4: Matematik sorularında hesaplama hatası, kavram karışıklığı, işlem hatası kategorileri
- REQ-3.5: Alfabetik veya sayısal mantıklı sıralama yapar
- REQ-3.6: Hiçbir çeldiricinin doğru cevap kadar cazip olmamasını garanti eder
"""

import re
import time
from typing import Any

from ..stage_base import BasePipelineStage, StageInput, StageOutput


class DistractorAgent(BasePipelineStage):
    """
    Çeldirici Üretim Agent'ı (Aşama 3)

    Yaygın öğrenci hatalarına dayalı etkili çeldirici seçenekler üretir.
    """

    STAGE_NAME = "distractor_generator"
    STAGE_WEIGHT = 0.20  # 20%

    # Ders bazlı hata kategorileri
    ERROR_CATEGORIES = {
        "matematik": [
            "hesaplama_hatası",
            "kavram_karışıklığı",
            "işlem_hatası",
            "işaret_hatası",
            "birim_dönüşüm_hatası"
        ],
        "fizik": [
            "birim_hatası",
            "formül_karışıklığı",
            "kavram_hatası",
            "vektör_yön_hatası",
            "boyut_analizi_hatası"
        ],
        "kimya": [
            "mol_hesaplama_hatası",
            "denge_sabiti_hatası",
            "element_karışıklığı",
            "oksidasyon_hatası"
        ],
        "türkçe": [
            "anlam_karışıklığı",
            "bağlam_hatası",
            "eşanlamlı_karışıklığı",
            "dilbilgisi_yanılgısı"
        ],
        "default": [
            "kısmi_doğru",
            "yaygın_yanlış",
            "mantık_hatası",
            "tersine_anlama"
        ]
    }

    def __init__(
        self,
        llm_client: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        """
        Distractor Agent başlat

        Args:
            llm_client: LLM istemcisi
            config: Ek konfigürasyon
        """
        super().__init__(self.STAGE_NAME, llm_client, config)

    async def process(self, input_data: StageInput) -> StageOutput:
        """
        Çeldirici seçenekler üret

        Args:
            input_data: Pipeline girişi

        Returns:
            StageOutput: Çeldiriciler ve skor
        """
        start_time = time.time()
        errors = []
        warnings = []
        suggestions = []

        try:
            question_data = input_data.question_data
            question_text = question_data.get("question_text", "")
            correct_answer = question_data.get("correct_answer", "")
            subject = question_data.get("subject", "default").lower()

            if not question_text or not correct_answer:
                return self._create_error_output(
                    "Soru metni veya doğru cevap bulunamadı",
                    input_data,
                    time.time() - start_time
                )

            # 1. 3 çeldirici üret (REQ-3.1, REQ-3.2)
            distractors = await self._generate_distractors(
                question_text, correct_answer, subject
            )

            if len(distractors) < 3:
                warnings.append(f"Sadece {len(distractors)} çeldirici üretildi")
                # Eksik çeldiricileri varsayılan ile doldur
                while len(distractors) < 3:
                    distractors.append(f"Seçenek {len(distractors) + 2}")

            # 2. Plausibility skorları hesapla (REQ-3.3)
            plausibility_scores = await self._calculate_plausibility(
                question_text, correct_answer, distractors
            )

            # 3. Çeldiricileri doğrula (REQ-3.6)
            is_valid, validation_issues = await self._validate_distractors(
                correct_answer, distractors, plausibility_scores
            )

            if not is_valid:
                warnings.extend(validation_issues[:2])

            # 4. Seçenekleri sırala (REQ-3.5)
            all_options = [correct_answer] + distractors
            ordered_options, correct_position = self._order_options(all_options)

            # Seçenek objeleri oluştur
            options = []
            labels = ["A", "B", "C", "D"]
            for i, (label, text) in enumerate(zip(labels, ordered_options)):
                is_correct = (i == correct_position)
                plausibility = 1.0 if is_correct else plausibility_scores.get(
                    text, 0.5
                )
                options.append({
                    "label": label,
                    "text": text,
                    "is_correct": is_correct,
                    "plausibility_score": plausibility
                })

            correct_label = labels[correct_position]

            # Ortalama plausibility skoru
            avg_plausibility = sum(plausibility_scores.values()) / max(len(plausibility_scores), 1)

            # Skor hesapla
            score = self._calculate_stage_score(
                has_three_distractors=len(distractors) >= 3,
                is_valid=is_valid,
                avg_plausibility=avg_plausibility
            )

            # Output verisi
            output_data = {
                **question_data,
                "options": options,
                "correct_answer": correct_label,
                "distractor_plausibility": plausibility_scores
            }

            return StageOutput(
                question_data=output_data,
                score=score,
                passed=is_valid and score >= 0.6,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "stage": self.STAGE_NAME,
                    "plausibility_scores": plausibility_scores,
                    "avg_plausibility": avg_plausibility,
                    "correct_position": correct_position
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_output(
                f"Çeldirici üretim hatası: {e!s}",
                input_data,
                time.time() - start_time
            )

    def get_stage_weight(self) -> float:
        """Stage ağırlığı: 20%"""
        return self.STAGE_WEIGHT

    async def _generate_distractors(
        self,
        question_text: str,
        correct_answer: str,
        subject: str
    ) -> list[str]:
        """
        3 çeldirici seçenek üret

        Args:
            question_text: Soru metni
            correct_answer: Doğru cevap
            subject: Ders

        Returns:
            List[str]: Çeldirici listesi
        """
        error_cats = self.ERROR_CATEGORIES.get(
            subject, self.ERROR_CATEGORIES["default"]
        )

        if self.llm:
            try:
                prompt = f"""
                Aşağıdaki soru için 3 çeldirici seçenek üret.

                Soru: {question_text}
                Doğru Cevap: {correct_answer}

                Hata Kategorileri: {', '.join(error_cats[:3])}

                Kurallar:
                - Her çeldirici yaygın bir öğrenci hatasını temsil etmeli
                - Çeldiriciler mantıklı görünmeli ama yanlış olmalı
                - Doğru cevaptan daha cazip olmamalı
                - Her çeldirici farklı bir hata türünü temsil etmeli

                3 çeldirici döndür (her satırda bir tane, sadece cevap metni):
                """

                response = await self.llm.generate(prompt, max_tokens=200)
                lines = [line.strip() for line in response.split('\n') if line.strip()]

                # Temizle
                distractors = []
                for line in lines[:3]:
                    # Numaralama ve işaretleri kaldır
                    cleaned = re.sub(r'^[\d\.\)\-\*]+\s*', '', line)
                    if cleaned and cleaned != correct_answer:
                        distractors.append(cleaned)

                return distractors[:3]

            except Exception:
                pass

        # Fallback: Basit çeldiriciler
        return self._generate_simple_distractors(correct_answer, subject)

    def _generate_simple_distractors(
        self,
        correct_answer: str,
        subject: str
    ) -> list[str]:
        """Basit çeldirici üretimi (fallback)"""
        distractors = []

        # Sayısal cevap kontrolü
        try:
            num = float(correct_answer.replace(",", "."))
            # Yakın değerler
            distractors.append(str(num * 2))
            distractors.append(str(num / 2))
            distractors.append(str(num + 1))
        except ValueError:
            # Metin cevap
            distractors = [
                f"{correct_answer} (hatalı)",
                "Yukarıdakilerden hiçbiri",
                "Bilgi yetersiz"
            ]

        return distractors[:3]

    async def _calculate_plausibility(
        self,
        question_text: str,
        correct_answer: str,
        distractors: list[str]
    ) -> dict[str, float]:
        """
        Çeldirici plausibility skorları hesapla

        Args:
            question_text: Soru metni
            correct_answer: Doğru cevap
            distractors: Çeldiriciler

        Returns:
            Dict[str, float]: Çeldirici -> skor mapping
        """
        scores = {}

        for distractor in distractors:
            # Basit skorlama
            score = 0.5  # Başlangıç

            # Uzunluk benzerliği
            len_ratio = len(distractor) / max(len(correct_answer), 1)
            if 0.7 <= len_ratio <= 1.3:
                score += 0.2

            # Kelime örtüşmesi
            correct_words = set(correct_answer.lower().split())
            distractor_words = set(distractor.lower().split())
            overlap = len(correct_words & distractor_words)
            score += min(0.2, overlap * 0.1)

            # Çok benzer mi (kötü)
            if distractor.lower() == correct_answer.lower():
                score = 0.0
            elif distractor.lower() in correct_answer.lower():
                score -= 0.1

            scores[distractor] = max(0.0, min(0.9, score))

        return scores

    async def _validate_distractors(
        self,
        correct_answer: str,
        distractors: list[str],
        plausibility_scores: dict[str, float]
    ) -> tuple[bool, list[str]]:
        """
        Çeldiricileri doğrula

        Args:
            correct_answer: Doğru cevap
            distractors: Çeldiriciler
            plausibility_scores: Plausibility skorları

        Returns:
            Tuple[bool, List[str]]: (Geçerli mi, Sorunlar)
        """
        issues = []

        # Minimum 3 çeldirici
        if len(distractors) < 3:
            issues.append(f"Yetersiz çeldirici sayısı: {len(distractors)}")

        # Çeldirici doğru cevaba eşit mi
        for d in distractors:
            if d.strip().lower() == correct_answer.strip().lower():
                issues.append("Çeldirici doğru cevapla aynı")

        # Çeldiriciler birbirine eşit mi
        unique_distractors = set(d.strip().lower() for d in distractors)
        if len(unique_distractors) < len(distractors):
            issues.append("Tekrarlanan çeldiriciler var")

        # Plausibility kontrolü
        for d, score in plausibility_scores.items():
            if score >= 0.95:
                issues.append(f"Çeldirici çok cazip: {d[:20]}...")

        return len(issues) == 0, issues

    def _order_options(
        self,
        options: list[str]
    ) -> tuple[list[str], int]:
        """
        Seçenekleri mantıklı sırala

        Args:
            options: Tüm seçenekler (doğru cevap ilk)

        Returns:
            Tuple[List[str], int]: (Sıralı seçenekler, doğru cevap pozisyonu)
        """
        if not options:
            return [], -1

        correct = options[0]

        # Sayısal sıralama dene
        try:
            nums = [(opt, float(opt.replace(",", ".").split()[0])) for opt in options]
            sorted_opts = [opt for opt, _ in sorted(nums, key=lambda x: x[1])]
            correct_pos = sorted_opts.index(correct)
            return sorted_opts, correct_pos
        except (ValueError, IndexError):
            pass

        # Alfabetik sıralama
        sorted_opts = sorted(options)
        correct_pos = sorted_opts.index(correct)
        return sorted_opts, correct_pos

    def _calculate_stage_score(
        self,
        has_three_distractors: bool,
        is_valid: bool,
        avg_plausibility: float
    ) -> float:
        """Aşama skoru hesapla"""
        score = 0.0

        # 3 çeldirici var mı
        score += 0.3 if has_three_distractors else 0.1

        # Geçerli mi
        score += 0.3 if is_valid else 0.1

        # Plausibility
        score += 0.4 * avg_plausibility

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
            suggestions=["Doğru cevabı kontrol edin"],
            metadata={"stage": self.STAGE_NAME, "error": True},
            execution_time=execution_time
        )
