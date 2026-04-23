"""
Difficulty Calibration Agent (Stage 2)
IRT parametreleri ile zorluk kalibrasyonu

Weight: 20%

Requirements (REQ-2.x):
- REQ-2.1: IRT difficulty parametresini hesaplar
- REQ-2.2: Difficulty [-4.0, 4.0] aralığında
- REQ-2.3: Discrimination [0.2, 4.0] aralığında
- REQ-2.4: Guessing [0.0, 0.35] aralığında
- REQ-2.5: Soruyu zorluk seviyesine göre optimize eder
- REQ-2.6: ZPD (Zone of Proximal Development) kontrol eder (%15-85)
"""

import time
from typing import Any

from ..stage_base import BasePipelineStage, StageInput, StageOutput
from ..tools.irt_calculator import IRTCalculator


class DifficultyAgent(BasePipelineStage):
    """
    Zorluk Kalibrasyon Agent'ı (Aşama 2)

    IRT (Item Response Theory) parametreleri ile soru zorluğunu kalibre eder.
    ZPD (Zone of Proximal Development) kontrolü yapar.
    """

    STAGE_NAME = "difficulty_calibration"
    STAGE_WEIGHT = 0.20  # 20%

    # Zorluk seviyesi IRT mapping
    DIFFICULTY_MAP = {
        "kolay": -1.5,
        "orta": 0.0,
        "zor": 1.5
    }

    def __init__(
        self,
        llm_client: Any | None = None,
        irt_calculator: IRTCalculator | None = None,
        config: dict[str, Any] | None = None
    ):
        """
        Difficulty Agent başlat

        Args:
            llm_client: LLM istemcisi
            irt_calculator: IRT hesaplayıcı
            config: Ek konfigürasyon
        """
        super().__init__(self.STAGE_NAME, llm_client, config)
        self.irt = irt_calculator or IRTCalculator()

    async def process(self, input_data: StageInput) -> StageOutput:
        """
        Zorluk kalibrasyonu yap

        Args:
            input_data: Pipeline girişi

        Returns:
            StageOutput: Kalibre edilmiş soru ve skor
        """
        start_time = time.time()
        errors = []
        warnings = []
        suggestions = []

        try:
            question_data = input_data.question_data
            question_text = question_data.get("question_text", "")
            target_difficulty = question_data.get("target_difficulty", "orta")

            if not question_text:
                return self._create_error_output(
                    "Soru metni bulunamadı",
                    input_data,
                    time.time() - start_time
                )

            # 1. IRT parametrelerini hesapla (REQ-2.1)
            irt_params = await self._calculate_irt_parameters(
                question_text, target_difficulty
            )

            # 2. Parametre aralıklarını doğrula (REQ-2.2, REQ-2.3, REQ-2.4)
            is_valid, validation_errors = self.irt.validate_parameters(
                irt_params["difficulty"],
                irt_params["discrimination"],
                irt_params["guessing"]
            )

            if not is_valid:
                errors.extend(validation_errors)
                # Parametreleri sınırla
                irt_params = self._clamp_parameters(irt_params)

            # 3. ZPD kontrolü (REQ-2.6)
            in_zpd, zpd_score, zpd_message = self.irt.check_zpd(
                irt_params["difficulty"],
                irt_params["discrimination"],
                irt_params["guessing"]
            )

            if not in_zpd:
                warnings.append(zpd_message)
                suggestions.append("Soru zorluğunu ayarlayın")

            # 4. Gerekirse optimize et (REQ-2.5)
            optimized_text = question_text
            if zpd_score < 0.7 and self.llm:
                optimized_text, new_params = await self._optimize_for_difficulty(
                    question_text, irt_params, target_difficulty
                )
                if new_params:
                    irt_params = new_params
                    # Yeniden ZPD kontrol
                    in_zpd, zpd_score, zpd_message = self.irt.check_zpd(
                        irt_params["difficulty"],
                        irt_params["discrimination"],
                        irt_params["guessing"]
                    )

            # Başarı olasılığını hesapla
            success_probability = self.irt.calculate_probability(
                theta=0.0,  # Ortalama öğrenci
                difficulty=irt_params["difficulty"],
                discrimination=irt_params["discrimination"],
                guessing=irt_params["guessing"]
            )

            # Skor hesapla
            score = self._calculate_stage_score(
                is_valid=is_valid,
                zpd_score=zpd_score,
                in_zpd=in_zpd
            )

            # Output verisi
            output_data = {
                **question_data,
                "question_text": optimized_text,
                "irt_difficulty": irt_params["difficulty"],
                "irt_discrimination": irt_params["discrimination"],
                "irt_guessing": irt_params["guessing"],
                "zpd_score": zpd_score,
                "success_probability": success_probability
            }

            return StageOutput(
                question_data=output_data,
                score=score,
                passed=is_valid and zpd_score >= 0.7,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "stage": self.STAGE_NAME,
                    "irt_params": irt_params,
                    "zpd_score": zpd_score,
                    "in_zpd": in_zpd,
                    "success_probability": success_probability
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_output(
                f"Zorluk kalibrasyon hatası: {e!s}",
                input_data,
                time.time() - start_time
            )

    def get_stage_weight(self) -> float:
        """Stage ağırlığı: 20%"""
        return self.STAGE_WEIGHT

    async def _calculate_irt_parameters(
        self,
        question_text: str,
        target_difficulty: str
    ) -> dict[str, float]:
        """
        IRT parametrelerini hesapla

        Args:
            question_text: Soru metni
            target_difficulty: Hedef zorluk

        Returns:
            Dict[str, float]: IRT parametreleri
        """
        # Temel zorluk
        base_difficulty = self.DIFFICULTY_MAP.get(target_difficulty, 0.0)

        # Metin analizine göre ayarlama
        word_count = len(question_text.split())
        complexity_adjustment = 0.0

        # Uzun sorular daha zor
        if word_count > 100:
            complexity_adjustment += 0.3
        elif word_count > 75:
            complexity_adjustment += 0.15

        # Matematiksel semboller
        math_symbols = ["∑", "∫", "√", "∞", "≤", "≥", "∈", "∀", "∃", "π", "θ"]
        math_count = sum(1 for sym in math_symbols if sym in question_text)
        complexity_adjustment += math_count * 0.1

        # Formül varlığı
        if any(op in question_text for op in ["x²", "x^2", "=", "+", "-", "*", "/"]):
            complexity_adjustment += 0.1

        # LLM ile tahmin (opsiyonel)
        if self.llm:
            try:
                prompt = f"""
                Aşağıdaki sorunun IRT parametrelerini tahmin et:

                Soru: {question_text}

                Hedef zorluk: {target_difficulty} (IRT: {base_difficulty})

                JSON formatında döndür (sadece sayılar):
                {{"difficulty": X, "discrimination": Y, "guessing": Z}}

                Aralıklar:
                - difficulty: -4.0 ile 4.0
                - discrimination: 0.2 ile 4.0
                - guessing: 0.0 ile 0.35
                """

                import json
                response = await self.llm.generate(prompt)
                # JSON parse
                try:
                    params = json.loads(response)
                    return {
                        "difficulty": float(params.get("difficulty", base_difficulty)),
                        "discrimination": float(params.get("discrimination", 1.0)),
                        "guessing": float(params.get("guessing", 0.25))
                    }
                except json.JSONDecodeError:
                    pass
            except Exception:
                pass

        # Varsayılan hesaplama
        final_difficulty = base_difficulty + complexity_adjustment

        return {
            "difficulty": round(final_difficulty, 2),
            "discrimination": 1.0,  # Varsayılan iyi ayırt edicilik
            "guessing": 0.25  # 4 seçenekli soru için
        }

    def _clamp_parameters(self, params: dict[str, float]) -> dict[str, float]:
        """Parametreleri geçerli aralıklara sınırla"""
        return {
            "difficulty": max(-4.0, min(4.0, params["difficulty"])),
            "discrimination": max(0.2, min(4.0, params["discrimination"])),
            "guessing": max(0.0, min(0.35, params["guessing"]))
        }

    async def _optimize_for_difficulty(
        self,
        question_text: str,
        current_params: dict[str, float],
        target_difficulty: str
    ) -> tuple[str, dict[str, float] | None]:
        """
        Soruyu hedef zorluğa göre optimize et

        Args:
            question_text: Mevcut soru metni
            current_params: Mevcut IRT parametreleri
            target_difficulty: Hedef zorluk

        Returns:
            Tuple[str, Dict]: (Optimize edilmiş metin, Yeni parametreler)
        """
        if not self.llm:
            return question_text, None

        try:
            prompt = f"""
            Aşağıdaki soruyu {target_difficulty} seviyesine uygun hale getir.
            Mevcut zorluk skoru: {current_params['difficulty']:.2f}
            Hedef aralık: {self.DIFFICULTY_MAP.get(target_difficulty, 0.0):.2f} civarı

            Orijinal soru:
            {question_text}

            Kurallar:
            - Soru anlamını koru
            - Zorluk seviyesini ayarla
            - {"Daha basit kelimeler kullan" if target_difficulty == "kolay" else "Daha karmaşık ifadeler kullan" if target_difficulty == "zor" else "Dengeyi koru"}

            Optimize edilmiş soru:
            """

            optimized = await self.llm.generate(prompt, max_tokens=300)
            optimized = optimized.strip()

            # Yeni parametreleri tahmin et
            new_params = await self._calculate_irt_parameters(optimized, target_difficulty)

            return optimized, new_params

        except Exception:
            return question_text, None

    def _calculate_stage_score(
        self,
        is_valid: bool,
        zpd_score: float,
        in_zpd: bool
    ) -> float:
        """
        Aşama skoru hesapla

        Args:
            is_valid: Parametreler geçerli mi
            zpd_score: ZPD skoru
            in_zpd: ZPD içinde mi

        Returns:
            float: Aşama skoru (0-1)
        """
        if not is_valid:
            return 0.4

        score = 0.0

        # Parametre geçerliliği
        score += 0.3 if is_valid else 0.0

        # ZPD skoru
        score += 0.5 * zpd_score

        # ZPD içinde mi
        score += 0.2 if in_zpd else 0.0

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
            suggestions=["Soru metnini kontrol edin"],
            metadata={"stage": self.STAGE_NAME, "error": True},
            execution_time=execution_time
        )
