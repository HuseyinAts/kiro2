"""
GPT-4 Fine-tuning Service
OpenAI GPT-4 fine-tuning altyapısı - ÖSYM soru üretimi için.

Requirements: REQ-48.17-48.20
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Model eğitim metrikleri"""

    bleu_score: float
    rouge_score: float
    bert_score: float
    training_loss: float
    validation_loss: float
    epoch: int
    timestamp: datetime


@dataclass
class HyperParameters:
    """Fine-tuning hyperparameters"""

    learning_rate: float = 1e-5
    batch_size: int = 4
    n_epochs: int = 3
    warmup_steps: int = 100
    weight_decay: float = 0.01


class GPT4FineTuningService:
    """
    GPT-4 Fine-tuning Service

    OpenAI API kullanarak GPT-4 modelini ÖSYM formatında soru üretimi için eğitir.

    Requirements:
    - REQ-48.17: OpenAI fine-tuning API entegrasyonu
    - REQ-48.18: Training data preparation
    - REQ-48.19: Hyperparameter tuning
    - REQ-48.20: Model evaluation metrics
    """

    def __init__(self, api_key: str, organization: Optional[str] = None):
        """
        Initialize GPT-4 Fine-tuning Service

        Args:
            api_key: OpenAI API key
            organization: OpenAI organization ID (optional)
        """
        self.client = OpenAI(api_key=api_key, organization=organization)
        self.training_jobs: Dict[str, Any] = {}
        self.metrics_history: List[TrainingMetrics] = []

        logger.info("GPT-4 Fine-tuning Service initialized")

    def prepare_training_data(
        self, questions: List[Dict[str, Any]], output_file: str = "training_data.jsonl"
    ) -> str:
        """
        ÖSYM formatına uygun training data hazırla

        REQ-48.18: Training data preparation

        Args:
            questions: ÖSYM soruları listesi
            output_file: Çıktı dosyası adı

        Returns:
            str: Hazırlanan dosya yolu
        """
        training_examples = []

        for question in questions:
            # ÖSYM formatında prompt oluştur
            prompt = self._create_osym_prompt(question)
            completion = self._create_osym_completion(question)

            training_examples.append(
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Sen ÖSYM formatında soru üreten bir yapay zeka asistanısın. MEB müfredatına uygun, kaliteli sorular oluşturursun.",
                        },
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": completion},
                    ]
                }
            )

        # JSONL formatında kaydet
        output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            for example in training_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        logger.info(
            f"Training data prepared: {len(training_examples)} examples -> {output_file}"
        )
        return str(output_path)

    def _create_osym_prompt(self, question: Dict[str, Any]) -> str:
        """ÖSYM formatında prompt oluştur"""
        return f"""Konu: {question.get('subject', '')}
Alt Konu: {question.get('topic', '')}
Zorluk: {question.get('difficulty', 'orta')}
Bloom Seviyesi: {question.get('bloom_level', 'uygulama')}

Bu konuda ÖSYM formatında bir soru oluştur."""

    def _create_osym_completion(self, question: Dict[str, Any]) -> str:
        """ÖSYM formatında completion oluştur"""
        stem = question.get("stem", "")
        options = question.get("options", [])
        correct_answer = question.get("correct_answer", 0)
        explanation = question.get("explanation", "")

        completion = f"""Soru: {stem}

Seçenekler:
"""
        for i, option in enumerate(options):
            completion += f"{chr(65+i)}) {option}\n"

        completion += f"\nDoğru Cevap: {chr(65+correct_answer)}\n"
        completion += f"\nAçıklama: {explanation}"

        return completion

    def upload_training_file(self, file_path: str) -> str:
        """
        Training dosyasını OpenAI'ye yükle

        Args:
            file_path: Training data dosya yolu

        Returns:
            str: File ID
        """
        with open(file_path, "rb") as f:
            response = self.client.files.create(file=f, purpose="fine-tune")

        file_id = response.id
        logger.info(f"Training file uploaded: {file_id}")
        return file_id

    def start_fine_tuning(
        self,
        training_file_id: str,
        model: str = "gpt-4-0613",
        hyperparameters: Optional[HyperParameters] = None,
        suffix: Optional[str] = None,
    ) -> str:
        """
        Fine-tuning işlemini başlat

        REQ-48.17: OpenAI fine-tuning API entegrasyonu
        REQ-48.19: Hyperparameter tuning

        Args:
            training_file_id: Training file ID
            model: Base model adı
            hyperparameters: Hyperparameter ayarları
            suffix: Model suffix (opsiyonel)

        Returns:
            str: Fine-tuning job ID
        """
        if hyperparameters is None:
            hyperparameters = HyperParameters()

        # Fine-tuning job oluştur
        response = self.client.fine_tuning.jobs.create(
            training_file=training_file_id,
            model=model,
            hyperparameters={
                "n_epochs": hyperparameters.n_epochs,
                "batch_size": hyperparameters.batch_size,
                "learning_rate_multiplier": hyperparameters.learning_rate / 1e-5,
            },
            suffix=suffix or f"osym-{datetime.now().strftime('%Y%m%d')}",
        )

        job_id = response.id
        self.training_jobs[job_id] = {
            "status": "created",
            "created_at": datetime.now(),
            "hyperparameters": hyperparameters,
        }

        logger.info(f"Fine-tuning job started: {job_id}")
        return job_id

    def check_training_status(self, job_id: str) -> Dict[str, Any]:
        """
        Training durumunu kontrol et

        Args:
            job_id: Fine-tuning job ID

        Returns:
            Dict: Job durumu
        """
        response = self.client.fine_tuning.jobs.retrieve(job_id)

        status = {
            "id": response.id,
            "status": response.status,
            "model": response.model,
            "fine_tuned_model": response.fine_tuned_model,
            "created_at": response.created_at,
            "finished_at": response.finished_at,
            "trained_tokens": response.trained_tokens,
            "error": response.error,
        }

        # Local cache güncelle
        if job_id in self.training_jobs:
            self.training_jobs[job_id]["status"] = response.status
            self.training_jobs[job_id]["fine_tuned_model"] = response.fine_tuned_model

        return status

    def wait_for_completion(
        self, job_id: str, check_interval: int = 60, timeout: int = 3600
    ) -> str:
        """
        Training tamamlanana kadar bekle

        Args:
            job_id: Fine-tuning job ID
            check_interval: Kontrol aralığı (saniye)
            timeout: Maksimum bekleme süresi (saniye)

        Returns:
            str: Fine-tuned model ID

        Raises:
            TimeoutError: Timeout aşıldığında
            RuntimeError: Training başarısız olduğunda
        """
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Fine-tuning timeout: {job_id}")

            status = self.check_training_status(job_id)

            if status["status"] == "succeeded":
                logger.info(f"Fine-tuning completed: {status['fine_tuned_model']}")
                return status["fine_tuned_model"]

            elif status["status"] == "failed":
                error_msg = status.get("error", "Unknown error")
                raise RuntimeError(f"Fine-tuning failed: {error_msg}")

            elif status["status"] in ["cancelled", "expired"]:
                raise RuntimeError(f"Fine-tuning {status['status']}: {job_id}")

            logger.info(f"Fine-tuning in progress: {status['status']}")
            time.sleep(check_interval)

    def evaluate_model(
        self, model_id: str, test_questions: List[Dict[str, Any]]
    ) -> TrainingMetrics:
        """
        Model performansını değerlendir

        REQ-48.20: Model evaluation metrics (BLEU, ROUGE, BERTScore)

        Args:
            model_id: Fine-tuned model ID
            test_questions: Test soruları

        Returns:
            TrainingMetrics: Değerlendirme metrikleri
        """
        from nltk.translate.bleu_score import sentence_bleu
        from rouge_score import rouge_scorer

        bleu_scores = []
        rouge_scores = []

        scorer = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"], use_stemmer=True
        )

        for question in test_questions:
            prompt = self._create_osym_prompt(question)
            expected = self._create_osym_completion(question)

            # Model ile soru üret
            response = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "system",
                        "content": "Sen ÖSYM formatında soru üreten bir yapay zeka asistanısın.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            generated = response.choices[0].message.content

            # BLEU score hesapla
            reference = [expected.split()]
            candidate = generated.split()
            bleu = sentence_bleu(reference, candidate)
            bleu_scores.append(bleu)

            # ROUGE score hesapla
            rouge = scorer.score(expected, generated)
            rouge_scores.append(rouge["rougeL"].fmeasure)

        # Ortalama metrikleri hesapla
        metrics = TrainingMetrics(
            bleu_score=sum(bleu_scores) / len(bleu_scores),
            rouge_score=sum(rouge_scores) / len(rouge_scores),
            bert_score=0.0,  # BERTScore ayrı hesaplanacak
            training_loss=0.0,
            validation_loss=0.0,
            epoch=0,
            timestamp=datetime.now(),
        )

        self.metrics_history.append(metrics)

        logger.info(
            f"Model evaluation: BLEU={metrics.bleu_score:.4f}, ROUGE={metrics.rouge_score:.4f}"
        )
        return metrics

    def list_fine_tuned_models(self) -> List[Dict[str, Any]]:
        """
        Fine-tuned modelleri listele

        Returns:
            List: Model listesi
        """
        response = self.client.fine_tuning.jobs.list(limit=20)

        models = []
        for job in response.data:
            if job.fine_tuned_model:
                models.append(
                    {
                        "id": job.id,
                        "model": job.fine_tuned_model,
                        "base_model": job.model,
                        "status": job.status,
                        "created_at": job.created_at,
                        "finished_at": job.finished_at,
                    }
                )

        return models

    def cancel_fine_tuning(self, job_id: str) -> bool:
        """
        Fine-tuning işlemini iptal et

        Args:
            job_id: Fine-tuning job ID

        Returns:
            bool: İptal başarılı mı
        """
        try:
            self.client.fine_tuning.jobs.cancel(job_id)
            logger.info(f"Fine-tuning cancelled: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel fine-tuning: {e}")
            return False

    def get_metrics_history(self) -> List[TrainingMetrics]:
        """
        Metrik geçmişini getir

        Returns:
            List[TrainingMetrics]: Metrik listesi
        """
        return self.metrics_history
