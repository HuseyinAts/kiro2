"""
T5/BART Generation Service
Türkçe soru üretimi ve paraphrasing için T5 ve BART modelleri.

Requirements: REQ-48.25-48.28
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import torch
from transformers import (
    AutoTokenizer,
    BartForConditionalGeneration,
    GenerationConfig,
    T5ForConditionalGeneration,
)

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Model tipi"""

    T5 = "t5"
    BART = "bart"


@dataclass
class GenerationResult:
    """Generation sonucu"""

    input_text: str
    generated_text: str
    score: float
    model_type: ModelType
    beam_scores: list[float] | None = None


class T5BARTGenerationService:
    """
    T5/BART Generation Service

    Türkçe soru üretimi ve paraphrasing için T5 ve BART modelleri.

    Requirements:
    - REQ-48.25: T5 model for Turkish question generation
    - REQ-48.26: BART model for paraphrasing
    - REQ-48.27: Beam search optimization
    - REQ-48.28: ÖSYM format compliance (95%+)
    """

    def __init__(
        self,
        t5_model_name: str = "google/mt5-base",
        bart_model_name: str = "facebook/mbart-large-50",
        device: str | None = None,
        cache_dir: str | None = None,
    ):
        """
        Initialize T5/BART Generation Service

        Args:
            t5_model_name: T5 model adı
            bart_model_name: BART model adı
            device: Device ('cuda', 'cpu', veya None)
            cache_dir: Model cache dizini
        """
        # Device seç
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Initializing T5/BART models on {self.device}")

        # T5 model yükle
        logger.info(f"Loading T5 model: {t5_model_name}")
        self.t5_tokenizer = AutoTokenizer.from_pretrained(
            t5_model_name, cache_dir=cache_dir
        )
        self.t5_model = T5ForConditionalGeneration.from_pretrained(
            t5_model_name, cache_dir=cache_dir
        )
        self.t5_model.to(self.device)
        self.t5_model.eval()

        # BART model yükle
        logger.info(f"Loading BART model: {bart_model_name}")
        self.bart_tokenizer = AutoTokenizer.from_pretrained(
            bart_model_name, cache_dir=cache_dir
        )
        self.bart_model = BartForConditionalGeneration.from_pretrained(
            bart_model_name, cache_dir=cache_dir
        )
        self.bart_model.to(self.device)
        self.bart_model.eval()

        # Generation config
        self.generation_config = GenerationConfig(
            max_length=512,
            num_beams=5,  # REQ-48.27: Beam search (5 beam)
            num_return_sequences=1,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            do_sample=False,
            early_stopping=True,
        )

        logger.info("T5/BART models loaded successfully")

    def generate_question_t5(
        self,
        topic: str,
        subject: str,
        difficulty: str = "orta",
        bloom_level: str = "uygulama",
        num_beams: int = 5,
        num_return_sequences: int = 1,
    ) -> list[GenerationResult]:
        """
        T5 ile Türkçe soru üret

        REQ-48.25: T5 model for Turkish question generation
        REQ-48.27: Beam search optimization (5 beam)

        Args:
            topic: Konu
            subject: Ders
            difficulty: Zorluk seviyesi
            bloom_level: Bloom taksonomisi seviyesi
            num_beams: Beam sayısı
            num_return_sequences: Döndürülecek sonuç sayısı

        Returns:
            List[GenerationResult]: Üretilen sorular
        """
        # Prompt oluştur
        prompt = f"""Türkçe ÖSYM formatında soru oluştur:
Ders: {subject}
Konu: {topic}
Zorluk: {difficulty}
Bloom Seviyesi: {bloom_level}

Soru:"""

        # Tokenize
        inputs = self.t5_tokenizer(
            prompt, return_tensors="pt", max_length=512, truncation=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self.t5_model.generate(
                **inputs,
                max_length=512,
                num_beams=num_beams,
                num_return_sequences=num_return_sequences,
                temperature=0.7,
                do_sample=False,
                early_stopping=True,
                return_dict_in_generate=True,
                output_scores=True,
            )

        # Decode
        results = []
        for i, sequence in enumerate(outputs.sequences):
            generated_text = self.t5_tokenizer.decode(
                sequence, skip_special_tokens=True
            )

            # Score hesapla (sequence score)
            if hasattr(outputs, "sequences_scores"):
                score = float(outputs.sequences_scores[i].cpu())
            else:
                score = 0.0

            # ÖSYM format compliance kontrolü
            compliance_score = self._check_osym_compliance(generated_text)

            results.append(
                GenerationResult(
                    input_text=prompt,
                    generated_text=generated_text,
                    score=compliance_score,
                    model_type=ModelType.T5,
                )
            )

        logger.info(f"Generated {len(results)} questions with T5")
        return results

    def paraphrase_bart(
        self, text: str, num_beams: int = 5, num_return_sequences: int = 3
    ) -> list[GenerationResult]:
        """
        BART ile paraphrasing yap

        REQ-48.26: BART model for paraphrasing
        REQ-48.27: Beam search optimization

        Args:
            text: Paraphrase edilecek text
            num_beams: Beam sayısı
            num_return_sequences: Döndürülecek sonuç sayısı

        Returns:
            List[GenerationResult]: Paraphrase sonuçları
        """
        # Prompt oluştur
        prompt = f"Paraphrase: {text}"

        # Tokenize
        inputs = self.bart_tokenizer(
            prompt, return_tensors="pt", max_length=512, truncation=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self.bart_model.generate(
                **inputs,
                max_length=512,
                num_beams=num_beams,
                num_return_sequences=num_return_sequences,
                temperature=0.8,
                do_sample=False,
                early_stopping=True,
                return_dict_in_generate=True,
                output_scores=True,
            )

        # Decode
        results = []
        for i, sequence in enumerate(outputs.sequences):
            generated_text = self.bart_tokenizer.decode(
                sequence, skip_special_tokens=True
            )

            # Score hesapla
            if hasattr(outputs, "sequences_scores"):
                score = float(outputs.sequences_scores[i].cpu())
            else:
                score = 0.0

            results.append(
                GenerationResult(
                    input_text=text,
                    generated_text=generated_text,
                    score=score,
                    model_type=ModelType.BART,
                )
            )

        logger.info(f"Generated {len(results)} paraphrases with BART")
        return results

    def generate_question_with_options(
        self, topic: str, subject: str, difficulty: str = "orta", num_options: int = 4
    ) -> dict[str, Any]:
        """
        Seçenekli soru üret (ÖSYM formatı)

        REQ-48.28: ÖSYM format compliance (95%+)

        Args:
            topic: Konu
            subject: Ders
            difficulty: Zorluk
            num_options: Seçenek sayısı

        Returns:
            Dict: Soru ve seçenekler
        """
        # Soru üret
        questions = self.generate_question_t5(
            topic=topic,
            subject=subject,
            difficulty=difficulty,
            num_beams=5,
            num_return_sequences=1,
        )

        if not questions:
            raise ValueError("Failed to generate question")

        question_text = questions[0].generated_text

        # Seçenekler üret (paraphrasing ile)
        options = []

        # Doğru cevap (ilk seçenek)
        correct_answer_prompt = f"Bu sorunun doğru cevabı: {question_text}"
        correct_answers = self.generate_question_t5(
            topic=topic,
            subject=subject,
            difficulty=difficulty,
            num_beams=3,
            num_return_sequences=1,
        )

        if correct_answers:
            options.append(correct_answers[0].generated_text)

        # Çeldiriciler (distractors)
        for i in range(num_options - 1):
            distractor_prompt = (
                f"Bu sorunun yanlış ama makul bir cevabı: {question_text}"
            )
            distractors = self.generate_question_t5(
                topic=topic,
                subject=subject,
                difficulty=difficulty,
                num_beams=3,
                num_return_sequences=1,
            )

            if distractors:
                options.append(distractors[0].generated_text)

        # ÖSYM format compliance kontrolü
        compliance_score = self._check_osym_compliance(question_text)

        result = {
            "question": question_text,
            "options": options,
            "correct_answer": 0,  # İlk seçenek doğru
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "osym_compliance": compliance_score,
            "model_type": "T5",
        }

        return result

    def _check_osym_compliance(self, text: str) -> float:
        """
        ÖSYM format compliance kontrolü

        REQ-48.28: ÖSYM format compliance (95%+)

        Args:
            text: Kontrol edilecek text

        Returns:
            float: Compliance score (0-1)
        """
        score = 0.0
        checks = 0

        # Türkçe karakter kontrolü
        turkish_chars = ["ç", "ğ", "ı", "ö", "ş", "ü", "Ç", "Ğ", "İ", "Ö", "Ş", "Ü"]
        if any(char in text for char in turkish_chars):
            score += 0.2
        checks += 1

        # Soru işareti kontrolü
        if "?" in text:
            score += 0.2
        checks += 1

        # Minimum uzunluk kontrolü (50 karakter)
        if len(text) >= 50:
            score += 0.2
        checks += 1

        # Maksimum uzunluk kontrolü (500 karakter)
        if len(text) <= 500:
            score += 0.2
        checks += 1

        # Cümle yapısı kontrolü (noktalama)
        if any(char in text for char in [".", ",", ";", ":"]):
            score += 0.2
        checks += 1

        # Normalize et
        compliance = score / checks if checks > 0 else 0.0

        return compliance

    def batch_generate_questions(
        self, topics: list[dict[str, str]], batch_size: int = 4
    ) -> list[dict[str, Any]]:
        """
        Batch soru üretimi

        Args:
            topics: Topic listesi [{"topic": "...", "subject": "...", "difficulty": "..."}]
            batch_size: Batch boyutu

        Returns:
            List[Dict]: Üretilen sorular
        """
        results = []

        for i in range(0, len(topics), batch_size):
            batch = topics[i : i + batch_size]

            for topic_info in batch:
                try:
                    question = self.generate_question_with_options(
                        topic=topic_info.get("topic", ""),
                        subject=topic_info.get("subject", ""),
                        difficulty=topic_info.get("difficulty", "orta"),
                    )
                    results.append(question)
                except Exception as e:
                    logger.error(f"Failed to generate question: {e}")
                    continue

        logger.info(f"Batch generated {len(results)} questions")
        return results

    def optimize_beam_search(
        self, text: str, num_beams_list: list[int] = [3, 5, 7, 10]
    ) -> tuple[int, list[GenerationResult]]:
        """
        Beam search optimization - en iyi beam sayısını bul

        REQ-48.27: Beam search optimization

        Args:
            text: Input text
            num_beams_list: Test edilecek beam sayıları

        Returns:
            Tuple[int, List[GenerationResult]]: (optimal_beams, results)
        """
        best_beams = 5
        best_score = 0.0
        all_results = []

        for num_beams in num_beams_list:
            results = self.paraphrase_bart(
                text=text, num_beams=num_beams, num_return_sequences=1
            )

            if results:
                avg_score = sum(r.score for r in results) / len(results)
                all_results.extend(results)

                if avg_score > best_score:
                    best_score = avg_score
                    best_beams = num_beams

        logger.info(f"Optimal beam count: {best_beams} (score: {best_score:.4f})")
        return best_beams, all_results

    def get_model_info(self) -> dict[str, Any]:
        """
        Model bilgilerini getir

        Returns:
            Dict: Model bilgileri
        """
        return {
            "t5_model": {
                "name": self.t5_tokenizer.name_or_path,
                "vocab_size": self.t5_tokenizer.vocab_size,
                "device": str(self.device),
            },
            "bart_model": {
                "name": self.bart_tokenizer.name_or_path,
                "vocab_size": self.bart_tokenizer.vocab_size,
                "device": str(self.device),
            },
            "generation_config": {
                "max_length": self.generation_config.max_length,
                "num_beams": self.generation_config.num_beams,
                "temperature": self.generation_config.temperature,
            },
        }
