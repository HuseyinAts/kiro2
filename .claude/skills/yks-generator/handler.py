"""YKS Soru Uretici Skill Handler.

SKILL.md'deki spec'e uygun soru uretim handler'i.
Ollama/Qwen ile SOLO+Marzano hedefli YKS sorulari uretir.

Pipeline: Parse Args → Retrieve → Skeleton → Generate → Verify → Output
"""

from __future__ import annotations

import json
import math
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx


# --- Config ---

@dataclass
class GeneratorConfig:
    """Soru uretici konfigurasyonu."""

    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
    pg_dsn: str = os.getenv("PG_DSN", "postgresql://kiro2_user:password@localhost:5434/kiro2")
    max_attempts: int = 4
    temperature: float = 0.4
    solo_fit_min: int = 75
    marzano_fit_min: int = 70
    copy_risk_max: int = 25
    db_similarity_max: float = 0.92

    # IRT bounds
    difficulty_range: tuple[float, float] = (-4.0, 4.0)
    discrimination_range: tuple[float, float] = (0.2, 4.0)
    guessing_range: tuple[float, float] = (0.0, 0.35)

    # ZPD
    zpd_min: float = 0.15
    zpd_max: float = 0.85


# --- Exam Types ---

EXAM_SPECS: dict[str, dict[str, Any]] = {
    "TYT": {
        "options_count": 5,
        "max_guessing": 0.20,
        "subjects": ["Turkce", "Matematik", "Fen Bilimleri", "Sosyal Bilimler"],
    },
    "AYT-SAY": {
        "options_count": 5,
        "max_guessing": 0.20,
        "subjects": ["Matematik", "Fizik", "Kimya", "Biyoloji"],
    },
    "AYT-EA": {
        "options_count": 5,
        "max_guessing": 0.20,
        "subjects": ["Matematik", "Turk Dili ve Edebiyati", "Tarih-1", "Cografya-1"],
    },
    "AYT-SOZ": {
        "options_count": 5,
        "max_guessing": 0.20,
        "subjects": ["Turk Dili ve Edebiyati", "Tarih", "Cografya", "Felsefe"],
    },
    "YDT": {
        "options_count": 5,
        "max_guessing": 0.20,
        "subjects": ["Ingilizce", "Almanca", "Fransizca"],
    },
}

SOLO_LEVELS = ("uni", "multi", "relational", "extended_abstract")
MARZANO_LEVELS = (
    "cognitive_recall", "cognitive_comprehension",
    "cognitive_analysis", "cognitive_knowledge_utilization",
    "meta_planning", "meta_monitoring", "meta_strategy_selection",
)


# --- Ollama Client ---

def ollama_generate(
    prompt: str,
    config: GeneratorConfig,
    *,
    temperature: float | None = None,
    num_predict: int = 1000,
) -> str:
    """Ollama/Qwen ile metin uret.

    Args:
        prompt: Model prompt'u.
        config: Generator konfigurasyonu.
        temperature: Uretim sicakligi.
        num_predict: Maksimum token sayisi.

    Returns:
        Model ciktisi (string).
    """
    url = f"{config.ollama_url}/api/generate"
    payload = {
        "model": config.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature or config.temperature,
            "top_p": 0.9,
            "repeat_penalty": 1.15,
            "num_predict": num_predict,
        },
    }
    resp = httpx.post(url, json=payload, timeout=180.0)
    resp.raise_for_status()
    return resp.json().get("response", "")


# --- Prompt Templates ---

def prompt_skeleton(
    subject: str,
    target_solo: str,
    target_marzano: str,
    examples_compact: str,
) -> str:
    """Skeleton extraction prompt'u."""
    return f"""SEN: Olcme-degerlendirme uzmanisin.
GOREV: Asagidaki orneklerden SADECE "kavramsal iskelet" cikar. Metin kopyalama YASAK.
CIKTI JSON olmali.

Istenen alanlar:
{{
 "core_skill": "...",
 "prereqs": ["..."],
 "solution_steps": ["..."],
 "distractor_misconceptions": ["..."],
 "solo_hint": "{target_solo}",
 "marzano_hint": "{target_marzano}",
 "notes": ["kopyalama yok", "YKS 5 sik", "tek dogru"]
}}

DERS: {subject}
HEDEF SOLO: {target_solo}
HEDEF MARZANO: {target_marzano}

[ORNEKLER - KISALTI]
{examples_compact}"""


def prompt_generate_question(
    subject: str,
    topic: str,
    target_solo: str,
    target_marzano: str,
    difficulty: float,
    skeleton_json: str,
) -> str:
    """Soru uretim prompt'u."""
    return f"""ROL: YKS soru yazari + denetci.

HEDEF:
- Ders: {subject}
- Konu: {topic}
- SOLO: {target_solo}
- Marzano: {target_marzano}
- Zorluk: {difficulty}
- Format: 5 sikli coktan secmeli (A-E)

KURALLAR:
- Tek dogru cevap ZORUNLU.
- Belirsizlik, cift dogru, ipucu sizintisi YASAK.
- Ornekleri kopyalama veya yakin paraphrase yapma YASAK.
- Celdirici tasarimi: en az 2 tur kullan:
  (1) kavram yanilgisi (2) islem/hesap hatasi (3) yanlis genelleme/iliski
- Once PLAN (kisa) sonra JSON uret.

CIKTI SADECE JSON:
{{
 "stem":"...",
 "options":{{"A":"...","B":"...","C":"...","D":"...","E":"..."}},
 "answer":"A|B|C|D|E",
 "rationale":"3-6 cumle kisa cozum",
 "evidence_claim":"Bu soru hangi beceriyi kanitliyor? 1 cumle",
 "solo_target":"{target_solo}",
 "marzano_target":"{target_marzano}"
}}

[SKELETON]
{skeleton_json}"""


def prompt_judge(
    subject: str,
    target_solo: str,
    target_marzano: str,
    question_json: str,
    skeleton_json: str,
) -> str:
    """Judge dogrulama prompt'u."""
    return f"""Sen acimasiz bir YKS denetcisisin. Asagidaki soruyu kontrol et.
Hedefler:
- Ders: {subject}
- SOLO: {target_solo}
- Marzano: {target_marzano}

Asagidakileri degerlendir ve SADECE JSON uret:
{{
 "single_correct": true|false,
 "ambiguity": true|false,
 "solo_fit": 0-100,
 "marzano_fit": 0-100,
 "distractor_quality": 0-100,
 "copy_risk": 0-100,
 "notes": ["..."]
}}

[SKELETON]
{skeleton_json}

[SORU_JSON]
{question_json}"""


# --- Rule Check ---

def rule_check_mcq(q: dict[str, Any]) -> list[str]:
    """Deterministik MCQ kural kontrolu.

    Args:
        q: Soru JSON'u.

    Returns:
        Hata flag listesi (bos = gecerli).
    """
    flags: list[str] = []
    opts = q.get("options") or {}
    if set(opts.keys()) != set("ABCDE"):
        flags.append("missing_options")

    ans = q.get("answer")
    if ans not in list("ABCDE"):
        flags.append("invalid_answer")

    stem = (q.get("stem") or "").strip()
    if not stem or len(stem) < 10:
        flags.append("bad_stem")

    rationale = (q.get("rationale") or "").lower()
    if re.search(r"\bdogru cevap\b", rationale):
        flags.append("rationale_leak_phrase")

    for k in "ABCDE":
        if not str(opts.get(k, "")).strip():
            flags.append(f"empty_option_{k}")

    return flags


# --- IRT ---

def irt_probability(
    theta: float,
    difficulty: float,
    discrimination: float = 1.0,
    guessing: float = 0.2,
) -> float:
    """3PL basari olasiligi."""
    d = 1.7
    exponent = -d * discrimination * (theta - difficulty)
    exponent = max(-500, min(500, exponent))
    return guessing + (1.0 - guessing) / (1.0 + math.exp(exponent))


def validate_irt(
    difficulty: float,
    discrimination: float,
    guessing: float,
    config: GeneratorConfig,
) -> list[str]:
    """IRT parametre dogrulama."""
    errors: list[str] = []
    d_min, d_max = config.difficulty_range
    a_min, a_max = config.discrimination_range
    c_min, c_max = config.guessing_range

    if not (d_min <= difficulty <= d_max):
        errors.append(f"difficulty {difficulty} out of [{d_min}, {d_max}]")
    if not (a_min <= discrimination <= a_max):
        errors.append(f"discrimination {discrimination} out of [{a_min}, {a_max}]")
    if not (c_min <= guessing <= c_max):
        errors.append(f"guessing {guessing} out of [{c_min}, {c_max}]")
    return errors


# --- JSON Parser ---

def safe_json_parse(text: str) -> dict[str, Any]:
    """Ollama ciktisindan JSON parse et.

    Args:
        text: Model ciktisi (JSON iceren).

    Returns:
        Parsed dict.

    Raises:
        ValueError: JSON bulunamazsa.
    """
    if not text:
        raise ValueError("empty model response")
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1 or e <= s:
        raise ValueError(f"no json object in response: {text[:200]}")
    return json.loads(text[s : e + 1])


# --- Argument Parser ---

@dataclass
class GenerateRequest:
    """Skill argumanlari."""

    exam_type: str = "TYT"
    subject: str = "Matematik"
    topic: str = ""
    difficulty: float = 0.5
    target_solo: str = "relational"
    target_marzano: str = "cognitive_analysis"
    count: int = 1
    cognitive_level: str = ""

    @classmethod
    def from_arguments(cls, arguments: str) -> GenerateRequest:
        """SKILL.md orneklerine gore arguman parse et.

        Ornekler:
            "TYT Matematik - Olasilik - Orta zorluk"
            "AYT Fizik - Elektrik - difficulty:1.5"
            "TYT Turkce - Paragraf - count:5"
            "AYT Kimya - Organik - level:Analiz"
        """
        req = cls()
        # Split by " - " (space-dash-space) to preserve "AYT-SAY" etc.
        parts = [p.strip() for p in re.split(r"\s+-\s+", arguments)]

        # İlk part: exam_type + subject
        if parts:
            first = parts[0].strip()
            # Match exam type from first part tokens
            first_upper = first.upper()
            matched_exam = False
            # Check if first part starts with a known exam type (with word boundary)
            for etype in sorted(EXAM_SPECS.keys(), key=len, reverse=True):
                # Must match at word boundary: "AYT-SAY " or "AYT-SAY" at end
                if first_upper == etype or first_upper.startswith(etype + " "):
                    req.exam_type = etype
                    remainder = first[len(etype):].strip()
                    if remainder:
                        req.subject = remainder
                    matched_exam = True
                    break

            if not matched_exam:
                tokens = first.split()
                for token in tokens:
                    upper = token.upper()
                    # Check compound: "AYT" alone → try to infer from subject later
                    if upper in EXAM_SPECS:
                        req.exam_type = upper
                        matched_exam = True
                    elif upper == "AYT":
                        req.exam_type = "AYT-SAY"  # default AYT
                        matched_exam = True
                    elif token not in ("", "-"):
                        req.subject = token

        # İkinci part: topic
        if len(parts) > 1:
            req.topic = parts[1].strip()

        # Sonraki partlar: modifiers
        for part in parts[2:]:
            lower = part.lower().strip()
            if lower.startswith("difficulty:"):
                try:
                    req.difficulty = float(lower.split(":")[1])
                except ValueError:
                    pass
            elif lower.startswith("count:"):
                try:
                    req.count = int(lower.split(":")[1])
                except ValueError:
                    pass
            elif lower.startswith("level:"):
                req.cognitive_level = lower.split(":")[1].strip()
            elif "kolay" in lower:
                req.difficulty = -1.0
            elif "orta" in lower:
                req.difficulty = 0.0
            elif "zor" in lower:
                req.difficulty = 1.5

        return req


# --- Main Generator ---

@dataclass
class GenerationResult:
    """Tek bir soru uretim sonucu."""

    run_id: str
    status: str  # "accepted" | "rejected" | "error"
    question: dict[str, Any] | None = None
    verdict: dict[str, Any] | None = None
    attempts: int = 0
    latency_ms: int = 0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "run_id": self.run_id,
            "status": self.status,
            "attempts": self.attempts,
            "latency_ms": self.latency_ms,
        }
        if self.question:
            result["question"] = self.question
        if self.verdict:
            result["verdict"] = self.verdict
        if self.error:
            result["error"] = self.error
        return result

    def to_markdown(self) -> str:
        """SKILL.md cikti formatinda markdown."""
        if self.status != "accepted" or not self.question:
            return f"**Durum:** {self.status}\n**Hata:** {self.error or 'Soru kabul edilemedi'}"

        q = self.question
        opts = q.get("options", {})
        opts_str = "\n".join(f"{k}) {v}" for k, v in sorted(opts.items()))

        return f"""## Uretilen Soru

**Sinav:** {q.get('exam_type', 'N/A')}
**Ders:** {q.get('subject', 'N/A')}
**Konu:** {q.get('topic', 'N/A')}

### Soru
{q.get('stem', '')}

### Siklar
{opts_str}

### Dogru Cevap
{q.get('answer', '')}

### Cozum
{q.get('rationale', '')}

### IRT Parametreleri
- Zorluk: {q.get('difficulty', 'N/A')}
- SOLO: {q.get('solo_target', 'N/A')}
- Marzano: {q.get('marzano_target', 'N/A')}

### Kalite
- SOLO Fit: {self.verdict.get('solo_fit', 'N/A') if self.verdict else 'N/A'}
- Marzano Fit: {self.verdict.get('marzano_fit', 'N/A') if self.verdict else 'N/A'}
- Celdirici Kalitesi: {self.verdict.get('distractor_quality', 'N/A') if self.verdict else 'N/A'}
- Kopya Riski: {self.verdict.get('copy_risk', 'N/A') if self.verdict else 'N/A'}

*Uretim: {self.attempts} deneme, {self.latency_ms}ms*"""


class YKSQuestionGenerator:
    """YKS soru uretim motoru.

    SOLO design doc pipeline'ini implement eder:
    Retrieve → Skeleton → Generate → Verify → Accept/Reject

    Example:
        >>> gen = YKSQuestionGenerator()
        >>> req = GenerateRequest.from_arguments("TYT Matematik - Olasilik - Orta zorluk")
        >>> result = gen.generate(req)
        >>> print(result.to_markdown())
    """

    def __init__(self, config: GeneratorConfig | None = None) -> None:
        self.config = config or GeneratorConfig()

    def generate(self, request: GenerateRequest) -> GenerationResult:
        """Tek bir YKS sorusu uret.

        Args:
            request: Uretim istegi.

        Returns:
            GenerationResult with question or error.
        """
        run_id = str(uuid.uuid4())
        t0 = time.time()

        try:
            # 1) Skeleton uret
            skeleton = self._generate_skeleton(request)

            # 2) Generate + Verify loop
            last_draft: dict[str, Any] | None = None
            last_verdict: dict[str, Any] | None = None

            for attempt in range(1, self.config.max_attempts + 1):
                draft = self._generate_question(request, skeleton)
                last_draft = draft

                # Rule check
                flags = rule_check_mcq(draft)

                # Judge
                verdict = self._judge_question(request, draft, skeleton)
                verdict["rule_flags"] = flags
                last_verdict = verdict

                ok = (
                    verdict.get("single_correct") is True
                    and verdict.get("ambiguity") is False
                    and int(verdict.get("solo_fit", 0)) >= self.config.solo_fit_min
                    and int(verdict.get("marzano_fit", 0)) >= self.config.marzano_fit_min
                    and int(verdict.get("copy_risk", 100)) <= self.config.copy_risk_max
                    and len(flags) == 0
                )

                if ok:
                    draft["exam_type"] = request.exam_type
                    draft["subject"] = request.subject
                    draft["topic"] = request.topic
                    draft["difficulty"] = request.difficulty

                    return GenerationResult(
                        run_id=run_id,
                        status="accepted",
                        question=draft,
                        verdict=verdict,
                        attempts=attempt,
                        latency_ms=int((time.time() - t0) * 1000),
                    )

            return GenerationResult(
                run_id=run_id,
                status="rejected",
                question=last_draft,
                verdict=last_verdict,
                attempts=self.config.max_attempts,
                latency_ms=int((time.time() - t0) * 1000),
            )

        except Exception as e:
            return GenerationResult(
                run_id=run_id,
                status="error",
                error=str(e),
                latency_ms=int((time.time() - t0) * 1000),
            )

    def _generate_skeleton(self, request: GenerateRequest) -> dict[str, Any]:
        """Skeleton uret (kopyalama onleme icin)."""
        prompt = prompt_skeleton(
            request.subject,
            request.target_solo,
            request.target_marzano,
            f"Konu: {request.topic or request.subject}, Zorluk: {request.difficulty}",
        )
        raw = ollama_generate(prompt, self.config, temperature=0.2, num_predict=700)
        return safe_json_parse(raw)

    def _generate_question(
        self, request: GenerateRequest, skeleton: dict[str, Any],
    ) -> dict[str, Any]:
        """Soru uret."""
        prompt = prompt_generate_question(
            request.subject,
            request.topic or request.subject,
            request.target_solo,
            request.target_marzano,
            request.difficulty,
            json.dumps(skeleton, ensure_ascii=False),
        )
        raw = ollama_generate(prompt, self.config, temperature=0.45, num_predict=1100)
        return safe_json_parse(raw)

    def _judge_question(
        self,
        request: GenerateRequest,
        draft: dict[str, Any],
        skeleton: dict[str, Any],
    ) -> dict[str, Any]:
        """Soru kalite degerlendirmesi."""
        prompt = prompt_judge(
            request.subject,
            request.target_solo,
            request.target_marzano,
            json.dumps(draft, ensure_ascii=False),
            json.dumps(skeleton, ensure_ascii=False),
        )
        raw = ollama_generate(prompt, self.config, temperature=0.2, num_predict=600)
        return safe_json_parse(raw)


# --- Entry Point ---

def handle(arguments: str) -> str:
    """Skill entry point (/yks-generator cagrildiginda).

    Args:
        arguments: Kullanici argumanlari.

    Returns:
        Markdown formatinda sonuc.
    """
    request = GenerateRequest.from_arguments(arguments)
    generator = YKSQuestionGenerator()

    results: list[str] = []
    for i in range(request.count):
        result = generator.generate(request)
        results.append(result.to_markdown())
        if request.count > 1:
            results.append(f"\n---\n*Soru {i + 1}/{request.count}*\n")

    return "\n\n".join(results)
