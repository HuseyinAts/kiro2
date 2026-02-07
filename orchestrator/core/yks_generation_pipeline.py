"""YKS Soru Üretim Pipeline - Ollama/Qwen entegrasyonlu üretim.

5 aşamalı pipeline:
1. Retrieve: Konu bazlı referans sorular getir
2. Skeleton: Soru iskeleti oluştur (konu, zorluk, SOLO hedef)
3. Generate: LLM ile tam soru üret
4. Verify: Kalite doğrulama (IRT, MCQ, Türkçe, copy-risk)
5. Accept/Reject: Otomatik karar veya insan kuyruğuna gönder

Kullanım:
    pipeline = YKSGenerationPipeline()
    result = await pipeline.generate_one(request)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

try:
    from .question_pipeline import (
        IRTParams,
        PipelineConfig,
        QuestionDraft,
        QuestionPipeline,
        QuestionStatus,
    )
except ImportError:
    from question_pipeline import (  # type: ignore[no-redef]
        IRTParams,
        PipelineConfig,
        QuestionDraft,
        QuestionPipeline,
        QuestionStatus,
    )

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:14b"


@dataclass
class GenerationRequest:
    """Üretim isteği."""

    exam_type: str = "TYT"
    subject: str = "Matematik"
    topic: str = ""
    subtopic: str = ""
    target_difficulty: int = 3  # 1-5
    target_solo: str = ""  # uni/multi/relational/extended_abstract
    target_count: int = 1
    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    max_retries: int = 3


@dataclass
class GenerationResult:
    """Tek soru üretim sonucu."""

    success: bool
    question: QuestionDraft | None = None
    stage_failed: str = ""
    error: str = ""
    attempts: int = 0
    duration_seconds: float = 0.0
    tokens_used: int = 0


@dataclass
class BatchResult:
    """Toplu üretim sonucu."""

    total_requested: int = 0
    generated: int = 0
    accepted: int = 0
    rejected: int = 0
    questions: list[QuestionDraft] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    total_tokens: int = 0


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------


class OllamaClient:
    """Ollama API istemcisi."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Ollama API'ye istek gönder.

        Args:
            prompt: Sistem + kullanıcı promptu.
            model: Model adı.
            temperature: Sıcaklık.
            max_tokens: Maksimum token.

        Returns:
            {"text": str, "tokens": int, "duration_ms": int}
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "text": data.get("response", ""),
                "tokens": data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                "duration_ms": data.get("total_duration", 0) // 1_000_000,
            }

    async def is_available(self) -> bool:
        """Ollama sunucusu erişilebilir mi?"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------


def prompt_skeleton(request: GenerationRequest) -> str:
    """Soru iskeleti oluşturma promptu."""
    difficulty_map = {1: "cok kolay", 2: "kolay", 3: "orta", 4: "zor", 5: "cok zor"}
    diff_label = difficulty_map.get(request.target_difficulty, "orta")

    solo_instruction = ""
    if request.target_solo:
        solo_map = {
            "uni": "tek bilgi parcasi soran (tanim, hatirlama)",
            "multi": "birden fazla bilgi parcasi soran (listeleme, birden fazla oncul)",
            "relational": "kavramlar arasi iliski kuran (neden-sonuc, karsilastirma)",
            "extended_abstract": "farkli baglama transfer gerektiren (hipotez, genelleme)",
        }
        solo_desc = solo_map.get(request.target_solo, request.target_solo)
        solo_instruction = f"\nSOLO seviye: {request.target_solo} - {solo_desc}"

    return f"""Sen bir OSYM soru yazarisin. Asagidaki parametrelere gore bir YKS sorusu icin iskelet olustur.

Sinav: {request.exam_type}
Ders: {request.subject}
Konu: {request.topic or 'Genel'}
Alt konu: {request.subtopic or '-'}
Zorluk: {diff_label} (seviye {request.target_difficulty}/5){solo_instruction}

Sadece JSON formatinda cevap ver:
{{
  "stem_outline": "Soru metninin ana fikri (1-2 cumle)",
  "key_concept": "Test edilen temel kavram",
  "distractor_strategy": "Celdiricilerin nasil olusturulacagi",
  "expected_bloom": 1-6,
  "estimated_time_seconds": 60-180
}}"""


def prompt_generate(
    request: GenerationRequest,
    skeleton: dict[str, Any],
) -> str:
    """Tam soru üretim promptu."""
    return f"""Sen bir OSYM soru yazarisin. Verilen iskeleye gore tam bir YKS sorusu yaz.

ISKELET:
- Ana fikir: {skeleton.get('stem_outline', '')}
- Temel kavram: {skeleton.get('key_concept', '')}
- Celdirici strateji: {skeleton.get('distractor_strategy', '')}

KURALLAR:
1. Turkce yaz, OSYM formatinda
2. 5 secenek (A-E), tek dogru cevap
3. Celdiriciler mantikli ama yanlis olmali
4. Soru metni en az 30 karakter
5. Her secenek bos olmamali
6. Aciklama en az 50 karakter

Sadece JSON formatinda cevap ver:
{{
  "question_text": "Soru metni",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
  "correct_answer": "A|B|C|D|E",
  "explanation": "Detayli cozum aciklamasi",
  "solution_steps": ["Adim 1", "Adim 2", "..."],
  "irt_params": {{"difficulty": -4..4, "discrimination": 0.2..4.0, "guessing": 0..0.35}},
  "topic_tags": ["tag1", "tag2"]
}}"""


def prompt_judge(question: dict[str, Any]) -> str:
    """Soru yargılama promptu."""
    q_text = question.get("question_text", "")
    options = question.get("options", {})
    answer = question.get("correct_answer", "")

    options_str = "\n".join(f"  {k}: {v}" for k, v in options.items())

    return f"""Sen bir OSYM soru kalite kontrolcususun. Asagidaki soruyu degerlendir.

SORU: {q_text}
SECENEKLER:
{options_str}
DOGRU CEVAP: {answer}

KONTROL ET:
1. Soru metni acik ve anlasilir mi?
2. Dogru cevap gercekten dogru mu?
3. Celdiriciler mantikli mi?
4. Turkce dil kalitesi iyi mi?
5. OSYM formatina uygun mu?

Sadece JSON formatinda cevap ver:
{{
  "verdict": "accept|reject",
  "quality_score": 0-100,
  "reasoning": "Kisa aciklama",
  "issues": ["varsa sorunlar"]
}}"""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _safe_json_parse(text: str) -> dict[str, Any] | None:
    """LLM çıktısından JSON parse et."""
    text = text.strip()
    # Find JSON block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _text_hash(text: str) -> str:
    """Metin hash'i (duplicate detection)."""
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


class YKSGenerationPipeline:
    """YKS soru üretim pipeline'ı.

    Ollama/Qwen ile soru üretir, mevcut QuestionPipeline ile doğrular.
    """

    def __init__(
        self,
        ollama_url: str = OLLAMA_BASE_URL,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self.llm = OllamaClient(base_url=ollama_url)
        self.model = model
        self.validation_pipeline = QuestionPipeline(config=PipelineConfig())
        self._generated_hashes: set[str] = set()

    async def generate_one(self, request: GenerationRequest) -> GenerationResult:
        """Tek soru üret ve doğrula.

        Args:
            request: Üretim isteği.

        Returns:
            GenerationResult.
        """
        start_time = time.monotonic()
        total_tokens = 0

        for attempt in range(1, request.max_retries + 1):
            try:
                # Stage 1: Skeleton
                skeleton_resp = await self.llm.generate(
                    prompt=prompt_skeleton(request),
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=512,
                )
                total_tokens += skeleton_resp["tokens"]
                skeleton = _safe_json_parse(skeleton_resp["text"])
                if not skeleton:
                    logger.warning("Skeleton parse failed (attempt %d)", attempt)
                    continue

                # Stage 2: Generate
                gen_resp = await self.llm.generate(
                    prompt=prompt_generate(request, skeleton),
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=2048,
                )
                total_tokens += gen_resp["tokens"]
                question_data = _safe_json_parse(gen_resp["text"])
                if not question_data:
                    logger.warning("Question parse failed (attempt %d)", attempt)
                    continue

                # Duplicate check (session-level)
                q_hash = _text_hash(question_data.get("question_text", ""))
                if q_hash in self._generated_hashes:
                    logger.warning("Duplicate detected (attempt %d)", attempt)
                    continue
                self._generated_hashes.add(q_hash)

                # Build QuestionDraft
                irt_data = question_data.get("irt_params", {})
                draft = QuestionDraft(
                    exam_type=request.exam_type,
                    subject=request.subject,
                    topic=request.topic,
                    subtopic=request.subtopic,
                    question_text=question_data.get("question_text", ""),
                    options=question_data.get("options", {}),
                    correct_answer=question_data.get("correct_answer", "A"),
                    difficulty_level=request.target_difficulty,
                    explanation=question_data.get("explanation", ""),
                    solution_steps=question_data.get("solution_steps", []),
                    topic_tags=question_data.get("topic_tags", []),
                    irt_params=IRTParams(
                        difficulty=float(irt_data.get("difficulty", 0.0)),
                        discrimination=float(irt_data.get("discrimination", 1.0)),
                        guessing=float(irt_data.get("guessing", 0.2)),
                    ),
                )

                # Stage 3: Validation pipeline
                self.validation_pipeline.process(draft)

                if draft.status == QuestionStatus.REJECTED:
                    logger.info(
                        "Question rejected (attempt %d): %s",
                        attempt,
                        draft.reject_reasons,
                    )
                    continue

                # Stage 4: Judge (LLM self-review)
                judge_resp = await self.llm.generate(
                    prompt=prompt_judge(question_data),
                    model=request.model,
                    temperature=0.3,
                    max_tokens=512,
                )
                total_tokens += judge_resp["tokens"]
                judge_data = _safe_json_parse(judge_resp["text"])

                if judge_data:
                    verdict = judge_data.get("verdict", "reject")
                    judge_score = float(judge_data.get("quality_score", 0))
                    if verdict == "reject" and judge_score < 50:
                        logger.info("Judge rejected (attempt %d)", attempt)
                        continue
                    # Blend quality scores
                    draft.quality_score = (draft.quality_score + judge_score / 100) / 2

                elapsed = time.monotonic() - start_time
                return GenerationResult(
                    success=True,
                    question=draft,
                    attempts=attempt,
                    duration_seconds=round(elapsed, 2),
                    tokens_used=total_tokens,
                )

            except httpx.HTTPError as e:
                logger.error("LLM HTTP error (attempt %d): %s", attempt, e)
            except Exception as e:
                logger.error("Pipeline error (attempt %d): %s", attempt, e)

        elapsed = time.monotonic() - start_time
        return GenerationResult(
            success=False,
            stage_failed="max_retries_exceeded",
            error=f"{request.max_retries} deneme basarisiz",
            attempts=request.max_retries,
            duration_seconds=round(elapsed, 2),
            tokens_used=total_tokens,
        )

    async def generate_batch(self, request: GenerationRequest) -> BatchResult:
        """Toplu soru üret.

        Args:
            request: Üretim isteği (target_count ile).

        Returns:
            BatchResult.
        """
        start_time = time.monotonic()
        result = BatchResult(total_requested=request.target_count)

        for i in range(request.target_count):
            gen_result = await self.generate_one(request)
            result.total_tokens += gen_result.tokens_used

            if gen_result.success and gen_result.question:
                result.generated += 1
                if gen_result.question.status == QuestionStatus.APPROVED:
                    result.accepted += 1
                else:
                    result.rejected += 1
                result.questions.append(gen_result.question)
            else:
                result.errors.append(
                    f"Soru {i + 1}: {gen_result.error or gen_result.stage_failed}"
                )

        result.duration_seconds = round(time.monotonic() - start_time, 2)
        return result

    async def check_llm_available(self) -> bool:
        """LLM sunucusu erişilebilir mi?"""
        return await self.llm.is_available()
