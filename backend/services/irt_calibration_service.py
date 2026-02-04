"""
IRT Kalibrasyon Servisi
Türkçe morfoloji analizi ile soru zorluk kalibrasyonu
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from algorithms.turkish_zpd_maarif_system import TurkishZPDMaarifSystem

logger = logging.getLogger(__name__)


@dataclass
class IRTParameters:
    """IRT parametreleri veri sınıfı"""

    difficulty: float  # b parametresi (-3 ile +3 arası)
    discrimination: float  # a parametresi (0.5 ile 2.5 arası)
    guessing: float  # c parametresi (0 ile 1 arası, genelde 0.2-0.25)
    morphology_complexity: float  # Türkçe morfolojik karmaşıklık (0-1 arası)
    readability_score: float  # Okunabilirlik skoru (0-1 arası)
    calibration_confidence: float  # Kalibrasyon güven skoru (0-1 arası)


@dataclass
class MorphologyAnalysis:
    """Türkçe morfoloji analizi sonucu"""

    word_count: int
    average_word_length: float
    suffix_complexity: float
    compound_word_ratio: float
    derivational_depth: float
    phonetic_changes: int
    semantic_ambiguity: float
    overall_complexity: float


class IRTCalibrationService:
    """
    IRT Kalibrasyon Servisi
    - Türkçe morfoloji analizi ile zorluk kalibrasyonu
    - ÖSYM/ETS standartlarını aşan soru analizi
    - Adaptif zorluk ayarlama
    """

    def __init__(self):
        self.zpd_system = TurkishZPDMaarifSystem()

        # Türkçe morfolojik karmaşıklık faktörleri
        self.morphology_weights = {
            "suffix_count": 0.15,  # Ek sayısı
            "derivational_depth": 0.20,  # Türetim derinliği
            "compound_complexity": 0.25,  # Birleşik kelime karmaşıklığı
            "phonetic_changes": 0.10,  # Ses değişimleri
            "semantic_ambiguity": 0.30,  # Anlam belirsizliği
        }

        # IRT kalibrasyon parametreleri
        self.calibration_params = {
            "min_difficulty": -3.0,
            "max_difficulty": 3.0,
            "min_discrimination": 0.5,
            "max_discrimination": 2.5,
            "default_guessing": 0.25,  # 4 seçenekli sorular için
            "morphology_impact": 0.4,  # Morfolojinin zorluk üzerindeki etkisi
            "readability_impact": 0.3,  # Okunabilirliğin zorluk üzerindeki etkisi
        }

        # Konu bazlı zorluk ayarlamaları
        self.subject_adjustments = {
            "Matematik": 0.2,
            "Fizik": 0.3,
            "Kimya": 0.1,
            "Biyoloji": 0.0,
            "Türkçe": -0.1,
            "İngilizce": 0.0,
            "Sosyal": -0.2,
        }

        logger.info(
            "IRT Kalibrasyon Servisi başlatıldı - Türkçe morfoloji desteği aktif"
        )

    async def analyze_turkish_morphology(self, text: str) -> MorphologyAnalysis:
        """
        Türkçe morfolojik analiz - Zemberek benzeri işlevsellik
        Gerçek implementasyonda Zemberek-NLP kullanılacak
        """

        words = text.split()
        if not words:
            return MorphologyAnalysis(0, 0, 0, 0, 0, 0, 0, 0)

        word_count = len(words)
        total_length = sum(len(word) for word in words)
        average_word_length = total_length / word_count

        # Ek karmaşıklığı analizi (basitleştirilmiş)
        suffix_indicators = [
            "-lar",
            "-ler",
            "-dan",
            "-den",
            "-ta",
            "-te",
            "-da",
            "-de",
            "-ın",
            "-in",
            "-un",
            "-ün",
            "-ı",
            "-i",
            "-u",
            "-ü",
            "-dığı",
            "-diği",
            "-duğu",
            "-düğü",
            "-arak",
            "-erek",
            "-ince",
            "-ınca",
            "-unca",
            "-ünce",
            "-ken",
            "-iken",
        ]

        suffix_count = 0
        for word in words:
            for suffix in suffix_indicators:
                if suffix in word.lower():
                    suffix_count += 1

        suffix_complexity = min(1.0, suffix_count / (word_count * 2))

        # Birleşik kelime oranı (basitleştirilmiş tespit)
        compound_indicators = ["okul", "ev", "araba", "kitap", "masa", "kalem"]
        compound_count = 0
        for word in words:
            for indicator in compound_indicators:
                if indicator in word.lower() and len(word) > len(indicator) + 2:
                    compound_count += 1
                    break

        compound_word_ratio = compound_count / word_count

        # Türetim derinliği (basitleştirilmiş)
        derivational_suffixes = [
            "-lık",
            "-lik",
            "-luk",
            "-lük",
            "-sal",
            "-sel",
            "-ci",
            "-cı",
        ]
        derivational_count = 0
        for word in words:
            for suffix in derivational_suffixes:
                if suffix in word.lower():
                    derivational_count += 1

        derivational_depth = min(1.0, derivational_count / word_count)

        # Ses değişimleri (basitleştirilmiş tespit)
        phonetic_changes = 0
        phonetic_patterns = ["ğ", "ş", "ç", "ı", "ü", "ö"]
        for word in words:
            if any(pattern in word.lower() for pattern in phonetic_patterns):
                phonetic_changes += 1

        # Anlam belirsizliği (kelime uzunluğu ve ek sayısına dayalı basit hesaplama)
        semantic_ambiguity = min(
            1.0, (average_word_length / 10 + suffix_complexity) / 2
        )

        # Genel karmaşıklık skoru
        overall_complexity = (
            suffix_complexity * self.morphology_weights["suffix_count"]
            + derivational_depth * self.morphology_weights["derivational_depth"]
            + compound_word_ratio * self.morphology_weights["compound_complexity"]
            + (phonetic_changes / word_count)
            * self.morphology_weights["phonetic_changes"]
            + semantic_ambiguity * self.morphology_weights["semantic_ambiguity"]
        )

        return MorphologyAnalysis(
            word_count=word_count,
            average_word_length=average_word_length,
            suffix_complexity=suffix_complexity,
            compound_word_ratio=compound_word_ratio,
            derivational_depth=derivational_depth,
            phonetic_changes=phonetic_changes,
            semantic_ambiguity=semantic_ambiguity,
            overall_complexity=min(1.0, overall_complexity),
        )

    async def calculate_readability_score(self, text: str) -> float:
        """
        Türkçe okunabilirlik skoru hesaplama
        Flesch-Kincaid benzeri ama Türkçe'ye uyarlanmış
        """

        if not text.strip():
            return 0.0

        # Cümle sayısı
        sentence_count = text.count(".") + text.count("!") + text.count("?")
        if sentence_count == 0:
            sentence_count = 1

        # Kelime sayısı
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            return 0.0

        # Hece sayısı (basitleştirilmiş)
        syllable_count = sum(self._count_syllables(word) for word in words)

        # Türkçe için uyarlanmış okunabilirlik formülü
        # Flesch Reading Ease'in Türkçe adaptasyonu
        readability = (
            206.835
            - (1.015 * (word_count / sentence_count))
            - (84.6 * (syllable_count / word_count))
        )

        # 0-1 arası normalize et (yüksek skor = daha okunabilir)
        normalized_score = max(0.0, min(1.0, readability / 100))

        return normalized_score

    def _count_syllables(self, word: str) -> int:
        """Basit hece sayma algoritması"""
        vowels = "aeiouüöıAEIOUÜÖI"
        syllable_count = sum(1 for char in word if char in vowels)
        return max(1, syllable_count)  # En az 1 hece

    async def calibrate_question_irt(
        self,
        question_text: str,
        options: List[str],
        subject: str,
        initial_difficulty: str,
        student_responses: Optional[List[Dict[str, Any]]] = None,
    ) -> IRTParameters:
        """
        Soru için IRT parametrelerini kalibre et
        Türkçe morfoloji analizi ile geliştirilmiş
        """

        logger.info(f"IRT kalibrasyon başlatıldı - Konu: {subject}")

        # Morfoloji analizi
        full_text = question_text + " " + " ".join(options)
        morphology = await self.analyze_turkish_morphology(full_text)

        # Okunabilirlik analizi
        readability = await self.calculate_readability_score(full_text)

        # Temel zorluk seviyesi
        difficulty_map = {"kolay": -0.5, "orta": 0.0, "zor": 0.5}
        base_difficulty = difficulty_map.get(initial_difficulty.lower(), 0.0)

        # Konu bazlı ayarlama
        subject_adjustment = self.subject_adjustments.get(subject, 0.0)

        # Morfolojik karmaşıklık etkisi
        morphology_impact = (
            morphology.overall_complexity * self.calibration_params["morphology_impact"]
        )

        # Okunabilirlik etkisi (düşük okunabilirlik = yüksek zorluk)
        readability_impact = (1.0 - readability) * self.calibration_params[
            "readability_impact"
        ]

        # Final zorluk parametresi
        final_difficulty = (
            base_difficulty
            + subject_adjustment
            + morphology_impact
            + readability_impact
        )

        # Sınırlar içinde tut
        final_difficulty = max(
            self.calibration_params["min_difficulty"],
            min(self.calibration_params["max_difficulty"], final_difficulty),
        )

        # Ayırıcılık parametresi (morfoloji karmaşıklığına dayalı)
        base_discrimination = 1.0
        discrimination_bonus = morphology.overall_complexity * 0.5
        final_discrimination = base_discrimination + discrimination_bonus

        # Sınırlar içinde tut
        final_discrimination = max(
            self.calibration_params["min_discrimination"],
            min(self.calibration_params["max_discrimination"], final_discrimination),
        )

        # Tahmin parametresi (seçenek sayısına göre)
        option_count = len(options)
        guessing_parameter = (
            1.0 / option_count
            if option_count > 0
            else self.calibration_params["default_guessing"]
        )

        # Öğrenci yanıtları varsa empirical kalibrasyon
        if student_responses:
            empirical_params = await self._empirical_calibration(
                student_responses,
                final_difficulty,
                final_discrimination,
                guessing_parameter,
            )
            final_difficulty = empirical_params["difficulty"]
            final_discrimination = empirical_params["discrimination"]

        # Kalibrasyon güven skoru
        confidence = self._calculate_calibration_confidence(
            morphology, readability, len(student_responses) if student_responses else 0
        )

        irt_params = IRTParameters(
            difficulty=final_difficulty,
            discrimination=final_discrimination,
            guessing=guessing_parameter,
            morphology_complexity=morphology.overall_complexity,
            readability_score=readability,
            calibration_confidence=confidence,
        )

        logger.info(
            f"IRT kalibrasyon tamamlandı - Zorluk: {final_difficulty:.3f}, Ayırıcılık: {final_discrimination:.3f}"
        )
        return irt_params

    async def _empirical_calibration(
        self,
        student_responses: List[Dict[str, Any]],
        initial_difficulty: float,
        initial_discrimination: float,
        guessing: float,
    ) -> Dict[str, float]:
        """
        Öğrenci yanıtlarına dayalı empirical kalibrasyon
        Maximum Likelihood Estimation (MLE) benzeri yaklaşım
        """

        if len(student_responses) < 10:
            # Yeterli veri yoksa initial değerleri döndür
            return {
                "difficulty": initial_difficulty,
                "discrimination": initial_discrimination,
            }

        # Doğru/yanlış oranları
        correct_responses = sum(
            1 for r in student_responses if r.get("is_correct", False)
        )
        total_responses = len(student_responses)
        correct_ratio = correct_responses / total_responses

        # Öğrenci yetenek seviyelerini tahmin et (basitleştirilmiş)
        student_abilities = []
        for response in student_responses:
            # Öğrencinin genel performansına dayalı yetenek tahmini
            overall_score = response.get("overall_score", 0.5)
            ability = (overall_score - 0.5) * 4  # -2 ile +2 arası normalize et
            student_abilities.append(ability)

        # Zorluk parametresi ayarlaması
        if correct_ratio > 0.8:
            # Çok kolay, zorluğu artır
            adjusted_difficulty = initial_difficulty - 0.3
        elif correct_ratio < 0.3:
            # Çok zor, zorluğu azalt
            adjusted_difficulty = initial_difficulty + 0.3
        else:
            # Uygun zorluk
            adjusted_difficulty = initial_difficulty

        # Ayırıcılık parametresi ayarlaması
        # Yetenek seviyelerine göre doğru cevap dağılımını analiz et
        ability_groups = {
            "low": [
                r for r, a in zip(student_responses, student_abilities) if a < -0.5
            ],
            "medium": [
                r
                for r, a in zip(student_responses, student_abilities)
                if -0.5 <= a <= 0.5
            ],
            "high": [
                r for r, a in zip(student_responses, student_abilities) if a > 0.5
            ],
        }

        # Her grup için doğru cevap oranı
        group_correct_ratios = {}
        for group, responses in ability_groups.items():
            if responses:
                group_correct_ratios[group] = sum(
                    1 for r in responses if r.get("is_correct", False)
                ) / len(responses)
            else:
                group_correct_ratios[group] = 0.5

        # Ayırıcılık = yüksek yetenek grubu ile düşük yetenek grubu arasındaki fark
        discrimination_indicator = group_correct_ratios.get(
            "high", 0.5
        ) - group_correct_ratios.get("low", 0.5)

        if discrimination_indicator > 0.4:
            # İyi ayırıcılık
            adjusted_discrimination = min(2.5, initial_discrimination + 0.2)
        elif discrimination_indicator < 0.1:
            # Zayıf ayırıcılık
            adjusted_discrimination = max(0.5, initial_discrimination - 0.2)
        else:
            # Orta ayırıcılık
            adjusted_discrimination = initial_discrimination

        return {
            "difficulty": adjusted_difficulty,
            "discrimination": adjusted_discrimination,
        }

    def _calculate_calibration_confidence(
        self, morphology: MorphologyAnalysis, readability: float, response_count: int
    ) -> float:
        """Kalibrasyon güven skoru hesapla"""

        confidence_factors = []

        # Morfoloji analizi güveni
        if morphology.word_count > 5:
            morphology_confidence = 0.8
        elif morphology.word_count > 2:
            morphology_confidence = 0.6
        else:
            morphology_confidence = 0.4

        confidence_factors.append(morphology_confidence * 0.3)

        # Okunabilirlik güveni
        readability_confidence = 0.9 if 0.3 <= readability <= 0.8 else 0.6
        confidence_factors.append(readability_confidence * 0.2)

        # Empirical veri güveni
        if response_count >= 50:
            empirical_confidence = 0.9
        elif response_count >= 20:
            empirical_confidence = 0.7
        elif response_count >= 10:
            empirical_confidence = 0.5
        else:
            empirical_confidence = 0.3

        confidence_factors.append(empirical_confidence * 0.5)

        return sum(confidence_factors)

    async def batch_calibrate_questions(
        self, questions: List[Dict[str, Any]], batch_size: int = 50
    ) -> List[IRTParameters]:
        """
        Toplu soru kalibrasyonu
        Büyük soru bankası için optimize edilmiş
        """

        logger.info(
            f"Toplu kalibrasyon başlatıldı - {len(questions)} soru, batch boyutu: {batch_size}"
        )

        calibrated_params = []

        for i in range(0, len(questions), batch_size):
            batch = questions[i : i + batch_size]
            batch_params = []

            for question in batch:
                try:
                    params = await self.calibrate_question_irt(
                        question_text=question["soru_metni"],
                        options=question["secenekler"],
                        subject=question["konu"],
                        initial_difficulty=question["zorluk_seviyesi"],
                    )
                    batch_params.append(params)

                except Exception as e:
                    logger.error(f"Soru kalibrasyonu hatası: {e}")
                    # Varsayılan parametreler
                    default_params = IRTParameters(
                        difficulty=0.0,
                        discrimination=1.0,
                        guessing=0.25,
                        morphology_complexity=0.5,
                        readability_score=0.5,
                        calibration_confidence=0.3,
                    )
                    batch_params.append(default_params)

            calibrated_params.extend(batch_params)

            # İlerleme logu
            if (i // batch_size + 1) % 10 == 0:
                logger.info(
                    f"Kalibrasyon ilerlemesi: {i + len(batch)}/{len(questions)} soru tamamlandı"
                )

        logger.info(
            f"Toplu kalibrasyon tamamlandı - {len(calibrated_params)} soru kalibre edildi"
        )
        return calibrated_params

    async def validate_irt_parameters(
        self, questions_with_params: List[Tuple[Dict[str, Any], IRTParameters]]
    ) -> Dict[str, Any]:
        """
        IRT parametrelerini doğrula ve kalite kontrolü yap
        """

        validation_results = {
            "total_questions": len(questions_with_params),
            "valid_questions": 0,
            "parameter_distribution": {
                "difficulty": {"min": 0, "max": 0, "mean": 0, "std": 0},
                "discrimination": {"min": 0, "max": 0, "mean": 0, "std": 0},
                "morphology_complexity": {"min": 0, "max": 0, "mean": 0, "std": 0},
            },
            "quality_metrics": {
                "high_discrimination_ratio": 0.0,
                "balanced_difficulty_distribution": 0.0,
                "morphology_coverage": 0.0,
            },
            "warnings": [],
        }

        if not questions_with_params:
            return validation_results

        # Parametreleri çıkar
        difficulties = [params.difficulty for _, params in questions_with_params]
        discriminations = [params.discrimination for _, params in questions_with_params]
        morphologies = [
            params.morphology_complexity for _, params in questions_with_params
        ]

        # Dağılım istatistikleri
        validation_results["parameter_distribution"]["difficulty"] = {
            "min": min(difficulties),
            "max": max(difficulties),
            "mean": sum(difficulties) / len(difficulties),
            "std": np.std(difficulties) if len(difficulties) > 1 else 0,
        }

        validation_results["parameter_distribution"]["discrimination"] = {
            "min": min(discriminations),
            "max": max(discriminations),
            "mean": sum(discriminations) / len(discriminations),
            "std": np.std(discriminations) if len(discriminations) > 1 else 0,
        }

        validation_results["parameter_distribution"]["morphology_complexity"] = {
            "min": min(morphologies),
            "max": max(morphologies),
            "mean": sum(morphologies) / len(morphologies),
            "std": np.std(morphologies) if len(morphologies) > 1 else 0,
        }

        # Kalite metrikleri
        high_discrimination_count = sum(1 for d in discriminations if d >= 1.5)
        validation_results["quality_metrics"][
            "high_discrimination_ratio"
        ] = high_discrimination_count / len(discriminations)

        # Zorluk dağılımı dengesi
        easy_count = sum(1 for d in difficulties if d < -0.5)
        medium_count = sum(1 for d in difficulties if -0.5 <= d <= 0.5)
        hard_count = sum(1 for d in difficulties if d > 0.5)

        total = len(difficulties)
        ideal_distribution = [0.3, 0.4, 0.3]  # %30 kolay, %40 orta, %30 zor
        actual_distribution = [
            easy_count / total,
            medium_count / total,
            hard_count / total,
        ]

        # Dağılım dengesi skoru (1 - ortalama sapma)
        balance_score = (
            1
            - sum(
                abs(ideal - actual)
                for ideal, actual in zip(ideal_distribution, actual_distribution)
            )
            / 2
        )
        validation_results["quality_metrics"][
            "balanced_difficulty_distribution"
        ] = balance_score

        # Morfoloji kapsama
        high_morphology_count = sum(1 for m in morphologies if m >= 0.6)
        validation_results["quality_metrics"][
            "morphology_coverage"
        ] = high_morphology_count / len(morphologies)

        # Uyarılar
        if validation_results["quality_metrics"]["high_discrimination_ratio"] < 0.5:
            validation_results["warnings"].append(
                "Düşük ayırıcılık parametreli soru oranı yüksek"
            )

        if balance_score < 0.7:
            validation_results["warnings"].append("Zorluk dağılımı dengesiz")

        if validation_results["quality_metrics"]["morphology_coverage"] < 0.3:
            validation_results["warnings"].append(
                "Yüksek morfolojik karmaşıklık kapsama düşük"
            )

        validation_results["valid_questions"] = len(questions_with_params)

        logger.info(
            f"IRT parametreleri doğrulandı - Geçerli soru: {validation_results['valid_questions']}"
        )
        return validation_results

    async def export_calibrated_questions(
        self,
        questions_with_params: List[Tuple[Dict[str, Any], IRTParameters]],
        output_format: str = "json",
    ) -> str:
        """
        Kalibre edilmiş soruları dışa aktar
        """

        export_data = []

        for question, params in questions_with_params:
            export_item = {
                **question,  # Orijinal soru verisi
                "calibrated_irt_parameters": {
                    "difficulty": params.difficulty,
                    "discrimination": params.discrimination,
                    "guessing": params.guessing,
                    "morphology_complexity": params.morphology_complexity,
                    "readability_score": params.readability_score,
                    "calibration_confidence": params.calibration_confidence,
                },
                "calibration_timestamp": datetime.now().isoformat(),
            }
            export_data.append(export_item)

        if output_format.lower() == "json":
            import json

            return json.dumps(export_data, ensure_ascii=False, indent=2)
        else:
            # CSV veya diğer formatlar için genişletilebilir
            return str(export_data)
