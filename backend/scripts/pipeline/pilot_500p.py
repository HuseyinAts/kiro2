"""
Pilot 500p - Icerik Pipeline v1.2.1 ana pilot script.

Plan: .cursor/plans/20260427_icerik_pipeline_v1_2.md
M3 iskelet: .cursor/plans/20260428_pipeline_M3_iskelet.md
Mimari: Hibrit C (28 Nis "opus 47" sohbeti) - Claude Code CLI subprocess + Max havuzu
Pre-pilot M1+S1+M2 tamamlandi (commit 36549f9).

Akis (M3 sec.1):
    PNG -> extract_page (claude CLI) -> validate_page -> write_staging
        -> resolve_conflict -> apply_decision -> finalize_batch

Conflict policy (M3 sec.3):
    Katman 1: hash yok -> INSERT question_bank
    Katman 2: hash var, kullanilmamis -> DELETE old + INSERT new
    Katman 3: hash var, korumali -> manual_review_queue

Calistirma (K-M3-7 hibrit):
    # Dry-run (DB yazimi yok, claude CLI yine cagirilir - JSON uretimi icin)
    python pilot_500p.py --book-dir <kitap> --dry-run --max-pages=3

    # Host smoke (5-10 sayfa, gercek DB)
    python pilot_500p.py --book-dir <kitap> --concurrency=1 --max-pages=10

    # 500p production
    python pilot_500p.py --book-dir <kitap> --concurrency=4

    # Resume
    python pilot_500p.py --book-dir <kitap> --resume <batch_id>

Env:
    DATABASE_URL          postgresql://user:pass@host:port/db (DB yazim icin zorunlu)
    ANTHROPIC_API_KEY     OPSIYONEL ve KULLANILMAZ. Varsa subprocess'lerden UNSET
                          edilir, claude CLI Max OAuth ile oturum acar.

Onkosul:
    Claude Code CLI (Max abonelik) yuklu ve PATH'te `claude` komutu olmali.
    Test: `claude --version`
    Ek bagimliliklar: tenacity, asyncpg

Cikti dizini:
    backend/scripts/pipeline/runs/<batch_id>/
        failed_pages.csv      extract asamasinda dusenler (DB'de iz yok)
        batch_summary.json    finalize_batch ozeti
        qa_sample.csv         %1 random + %100 needs_manual_review

Sade tutuldu - sadece M3 sec.6 smoke kabul kriterlerini saglayacak kadar.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import os
import re
import sys
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

import asyncpg

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


# ============================================================================
# Sabitler
# ============================================================================

DEFAULT_MODEL = "claude-opus-4-7"  # K-M3-6
DEFAULT_CONCURRENCY = 1            # smoke=1, 500p=4, prod=8 (K-M3-2)
POOL_OVERHEAD = 2                  # K-M3-3: pool size = concurrency + 2

CLAUDE_CLI = "claude"              # Claude Code CLI binary (Max abonelik)
CLAUDE_TIMEOUT = 180               # subprocess timeout (saniye)
EXTRACT_RETRY_TRANSIENT = 3        # subprocess transient hata - 3 retry
EXTRACT_RETRY_PARSE = 1            # JSON parse fail - 1 retry farkli prompt
DB_RETRY = 3                       # DB connection lost 3 retry

QA_RANDOM_RATIO = 0.01             # %1 random sample (Plan sec.1.2)
SUBJECT_AREA_ENUM = {
    "MATEMATIK", "GEOMETRI", "FIZIK", "KIMYA", "BIYOLOJI",
    "TURKCE", "EDEBIYAT", "TARIH", "COGRAFYA", "SOSYAL",
    "FEN", "INGILIZCE", "GENEL",
}
EXAM_TYPE_ENUM = {"AYT", "TYT"}
DIFFICULTY_ENUM = {"VERY_EASY", "EASY", "MEDIUM", "HARD", "VERY_HARD"}
PAGE_TYPE_ENUM = {"questions", "lecture", "chapter_cover", "unit_cover", "mixed"}


# ============================================================================
# Logging - basit prefix format
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("pilot")


# ============================================================================
# Veri sozlesmeleri (M3 sec.2.2)
# ============================================================================


class ExtractedQuestion(TypedDict):
    position_on_page: int
    question_number_on_page: int
    question_text: str
    options: dict[str, str | None]
    correct_answer: str
    has_diagram: bool
    is_real_exam_question: bool
    exam_year: int | None
    bloom_level_estimate: int
    difficulty_estimate: str


class ExtractedPage(TypedDict):
    file_page: str
    book_page_from_footer: int | None
    page_type: str
    test_no: int | None
    test_category: str | None
    subject_area: str
    primary_topic_code: str
    exam_type: str
    questions: list[ExtractedQuestion]
    extraction_confidence: float
    page_notes: str


class ValidationFlags(TypedDict):
    schema_ok: bool
    has_anomaly: bool
    anomaly_reasons: list[str]
    needs_manual_review: bool


class ValidatedPage(TypedDict):
    extracted: ExtractedPage
    flags: ValidationFlags


class ConflictDecision(TypedDict):
    staging_id: str
    soru_hash: str
    layer: int  # 1, 2, 3
    target_status: str
    existing_question_id: str | None
    keep_old_reason: str | None


# ============================================================================
# Helper'lar
# ============================================================================


def _normalize_turkish(text: str) -> str:
    """NFC normalize + leading/trailing whitespace temizle.

    Briefing kurali: tum Turkce metin UTF-8 + NFC normalized.
    Hash hesaplamasindan once cagrilir."""
    return unicodedata.normalize("NFC", text).strip()


def _hash_question(
    question_text: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    option_e: str | None,
) -> str:
    """MD5(LOWER(TRIM(question_text)) || '|' || A..D || '|' || COALESCE(E, '')).

    backfill_soru_hash.py + M2 partial UNIQUE INDEX ile birebir uyumlu.
    Pre-pilot M1 commit 36549f9'da bu formul DB'de uygulandi."""
    qt = _normalize_turkish(question_text).lower()
    a = _normalize_turkish(option_a)
    b = _normalize_turkish(option_b)
    c = _normalize_turkish(option_c)
    d = _normalize_turkish(option_d)
    e = _normalize_turkish(option_e) if option_e else ""
    payload = f"{qt}|{a}|{b}|{c}|{d}|{e}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def _uuid5_from_hash(soru_hash: str) -> str:
    """Deterministik UUID v5 - ayni hash -> ayni id.

    Plan v1.2.1 sec.6 mapping: id VARCHAR PK, UUID v5 hash bazli."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, soru_hash))


def _word_stats(text: str) -> tuple[int, int, float, float]:
    """word_count, unique_word_count, average_word_length, morphology_complexity.

    morphology_complexity = unique/total ratio (Plan v1.2.1 sec.6)."""
    norm = _normalize_turkish(text)
    words = norm.split()
    if not words:
        return 0, 0, 0.0, 0.0
    word_count = len(words)
    unique = len(set(w.lower() for w in words))
    avg_len = sum(len(w) for w in words) / word_count
    morph = unique / word_count if word_count else 0.0
    return word_count, unique, avg_len, morph


def _slugify(name: str) -> str:
    """Dizin adi -> slug. '345 2025 Ayt Matematik' -> '345_2025_ayt_matematik'."""
    norm = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    norm = re.sub(r"[^A-Za-z0-9]+", "_", norm).strip("_").lower()
    return norm or "kitap"


def _make_batch_id(book_dir: Path) -> str:
    """pilot_<book_slug>_<YYYYMMDD_HHMMSS> (M3 sec.4.1)."""
    slug = _slugify(book_dir.name)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"pilot_{slug}_{ts}"


def _normalize_dsn(url: str) -> str:
    """Backend DATABASE_URL '+asyncpg' suffix'ini cikarir."""
    return url.replace("+asyncpg", "").replace("+psycopg", "")


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ============================================================================
# Claude Code CLI prompt'lari (M3 sec.3.2 + Plan v1.2.1 sec.3.3)
# ============================================================================
# Hibrit C: Claude Code CLI subprocess + Max abonelik havuzu (28 Nis "opus 47" sohbeti).
# ANTHROPIC_API_KEY UNSET -> Max OAuth ile oturum acilir, ek ucret yok.
# Sayfa basi yeni subprocess = clean session (state birikmez).


EXTRACT_SYSTEM_PROMPT = """\
Sen bir Turkce YKS soru bankasi sayfa ekstraktorusun. Verilen image dosyasini
oku ve sayfadaki sorulari belirtilen JSON semasinda dondur. SADECE gecerli JSON
dondur, baska aciklama veya kod blogu yazma.
"""


EXTRACT_USER_PROMPT_TEMPLATE = """\
Read the image at: {png_path}

Extract YKS questions and return ONLY a JSON object matching this schema:

{{
  "file_page": "0015",
  "book_page_from_footer": 14,
  "page_type": "questions",
  "test_no": 1,
  "test_category": "Karma Sorular",
  "subject_area": "MATEMATIK",
  "primary_topic_code": "MAT.POL",
  "exam_type": "AYT",
  "questions": [
    {{
      "position_on_page": 1,
      "question_number_on_page": 1,
      "question_text": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
      "correct_answer": "A",
      "has_diagram": false,
      "is_real_exam_question": false,
      "exam_year": null,
      "bloom_level_estimate": 2,
      "difficulty_estimate": "MEDIUM"
    }}
  ],
  "extraction_confidence": 0.95,
  "page_notes": ""
}}

Kurallar:
- page_type: questions | lecture | chapter_cover | unit_cover | mixed
- subject_area BUYUK harf (Turkce karakter yok): MATEMATIK GEOMETRI FIZIK KIMYA
  BIYOLOJI TURKCE EDEBIYAT TARIH COGRAFYA SOSYAL FEN INGILIZCE GENEL
- exam_type: AYT veya TYT
- primary_topic_code SADECE asagidaki gecerli kodlardan biri olmali (DB'de mevcut
  topic_hierarchy.code degerleri):
  MATEMATIK: MAT.CRP MAT.DIZ MAT.DNK MAT.EST MAT.FON MAT.GEO MAT.INT MAT.IST
             MAT.KMB MAT.LMT MAT.LOG MAT.MTL MAT.OLS MAT.POL MAT.PRB MAT.PRM
             MAT.SAY MAT.TRG MAT.TRV MAT.USL
  FIZIK:     FIZ.ELE FIZ.MAG FIZ.MOD FIZ.OPT
  KIMYA:     KIM.ASI KIM.DEN KIM.ORG KIM.TER
  BIYOLOJI:  BIY.BIT BIY.EKO BIY.EVR BIY.GEN BIY.HUC BIY.SIS
  TURKCE:    TUR.ANL TUR.DIL TUR.PAR TUR.SOZ TUR.YAZ
  Sorunun konusuna en yakin kod hangisiyse onu sec.
- correct_answer: A B C D veya E (sayfa altindaki cevap anahtari satirindan oku)
- options.E null olabilir (4 sikli sorular)
- difficulty_estimate: VERY_EASY EASY MEDIUM HARD VERY_HARD
- bloom_level_estimate: 1-6
- Sayfa soru icermiyorsa (lecture/chapter_cover/unit_cover): questions = []
- file_page degeri dosya adindaki 4 haneli numara

SADECE JSON dondur, baska metin yazma.
"""


EXTRACT_USER_PROMPT_STRICT_RETRY = """\
{base}

ONEMLI: Onceki cevabinda JSON parse edilemedi. SADECE gecerli JSON dondur,
hicbir aciklama veya markdown kod blogu yazma.
"""


# JSON cevabi extract et - Claude bazen ```json fence ile sarabilir
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _strip_json_fence(text: str) -> str:
    m = _JSON_FENCE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


# ============================================================================
# extract_page (M3 sec.2.3) - Claude Code CLI subprocess (Hibrit C)
# ============================================================================


class ClaudeCliError(RuntimeError):
    """Claude CLI transient hatasi - tenacity retry'i tetikler."""


class ClaudeCliCriticalError(RuntimeError):
    """Claude CLI critical hatasi (auth/quota) - pilot durur, retry yok."""


async def _run_claude_cli(png_path: Path, user_prompt: str, model: str) -> str:
    """Claude Code CLI subprocess'ini calistir, stdout'u dondur.

    Max abonelik havuzu icin ANTHROPIC_API_KEY env'den UNSET edilir
    (subprocess child miras almasin).
    """
    # Child env: ANTHROPIC_API_KEY haric tum ana env
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

    cmd = [
        CLAUDE_CLI,
        "-p",                                  # print mode (non-interactive)
        "--model", model,
        "--no-session-persistence",            # disk'e kaydetme
        "--add-dir", str(png_path.parent),     # Read tool dizine erissin
        "--allowedTools", "Read",              # sadece Read, baska tool yok
        "--system-prompt", EXTRACT_SYSTEM_PROMPT,
        user_prompt,                           # son arg = user prompt
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=CLAUDE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        proc.kill()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            pass
        raise ClaudeCliError(f"claude CLI timeout ({CLAUDE_TIMEOUT}s): {png_path.name}")

    if proc.returncode != 0:
        err_text = stderr.decode("utf-8", errors="replace").strip()
        low = err_text.lower()
        # Auth/quota = critical, retry yok
        if any(s in low for s in ("not authenticated", "subscription", "quota", "rate limit")):
            raise ClaudeCliCriticalError(f"claude CLI critical: {err_text}")
        raise ClaudeCliError(f"claude CLI exit {proc.returncode}: {err_text[:500]}")

    return stdout.decode("utf-8", errors="replace")


@retry(
    stop=stop_after_attempt(EXTRACT_RETRY_TRANSIENT),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type(ClaudeCliError),
    reraise=True,
)
async def _run_claude_cli_retried(png_path: Path, user_prompt: str, model: str) -> str:
    """tenacity transient retry (3 deneme, exp backoff 2s/4s/8s)."""
    return await _run_claude_cli(png_path, user_prompt, model)


async def extract_page(
    png_path: Path,
    model: str = DEFAULT_MODEL,
) -> ExtractedPage:
    """Tek PNG'den Claude Code CLI ile extraction (Hibrit C).

    Hata kurtarma (M3 sec.5 + 28 Nis "opus 47" sohbeti):
      - Transient (timeout / non-zero exit) -> tenacity 3 retry exp backoff
      - JSON parse fail -> 1 retry strict prompt
      - Auth/quota/rate-limit -> ClaudeCliCriticalError, pilot durur
    """
    file_page = png_path.stem.replace("sayfa_", "")
    base_user_prompt = EXTRACT_USER_PROMPT_TEMPLATE.format(png_path=str(png_path))

    # Ilk deneme + tenacity transient retry
    raw = await _run_claude_cli_retried(png_path, base_user_prompt, model)
    try:
        data = json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError:
        # 1 retry strict prompt
        log.warning("extract_page %s JSON parse fail, retry with strict prompt", file_page)
        strict_prompt = EXTRACT_USER_PROMPT_STRICT_RETRY.format(base=base_user_prompt)
        raw2 = await _run_claude_cli_retried(png_path, strict_prompt, model)
        try:
            data = json.loads(_strip_json_fence(raw2))
        except json.JSONDecodeError as e:
            raise ClaudeCliError(
                f"extract_page {file_page}: JSON parse fail after strict retry: {e}"
            ) from e

    # file_page'i dosya adindan force et (CLI icindekini override)
    data["file_page"] = file_page
    return data  # type: ignore[return-value]


# ============================================================================
# validate_page (M3 sec.2.3) - saf fonksiyon
# ============================================================================


def validate_page(extracted: ExtractedPage) -> ValidatedPage:
    """Schema dogrulama + anomali kurallari (M3 hata matrisi)."""
    flags: ValidationFlags = {
        "schema_ok": True,
        "has_anomaly": False,
        "anomaly_reasons": [],
        "needs_manual_review": False,
    }

    # Sema kontrol - eksik zorunlu alan
    required = {"file_page", "page_type", "subject_area", "exam_type", "questions"}
    missing = required - set(extracted.keys())
    if missing:
        flags["schema_ok"] = False
        flags["has_anomaly"] = True
        flags["anomaly_reasons"].append(f"missing_keys:{','.join(sorted(missing))}")

    # Confidence threshold
    conf = _safe_float(extracted.get("extraction_confidence"), 0.0)
    if conf < 0.7:
        flags["needs_manual_review"] = True
        flags["anomaly_reasons"].append(f"low_confidence:{conf:.2f}")

    # subject_area enum
    sa = extracted.get("subject_area", "")
    if sa not in SUBJECT_AREA_ENUM:
        flags["has_anomaly"] = True
        flags["needs_manual_review"] = True
        flags["anomaly_reasons"].append(f"subject_area_invalid:{sa}")

    # exam_type enum
    et = extracted.get("exam_type", "")
    if et not in EXAM_TYPE_ENUM:
        flags["has_anomaly"] = True
        flags["anomaly_reasons"].append(f"exam_type_invalid:{et}")

    # page_type enum
    pt = extracted.get("page_type", "")
    if pt not in PAGE_TYPE_ENUM:
        flags["has_anomaly"] = True
        flags["anomaly_reasons"].append(f"page_type_invalid:{pt}")

    # questions=[] ama page_type='questions'
    questions = extracted.get("questions", [])
    if pt == "questions" and not questions:
        flags["has_anomaly"] = True
        flags["anomaly_reasons"].append("questions_empty_but_page_type_questions")

    # Her soru icin kontrol
    for i, q in enumerate(questions):
        ca = q.get("correct_answer")
        opts = q.get("options") or {}
        if ca not in {"A", "B", "C", "D", "E"}:
            flags["has_anomaly"] = True
            flags["needs_manual_review"] = True   # Session 88 fix: kalite gate tutarliligi
            flags["anomaly_reasons"].append(f"q{i}_correct_answer_invalid:{ca}")
        elif ca and opts.get(ca) is None:
            flags["has_anomaly"] = True
            flags["anomaly_reasons"].append(f"q{i}_correct_answer_not_in_options:{ca}")

        diff = q.get("difficulty_estimate")
        if diff not in DIFFICULTY_ENUM:
            flags["has_anomaly"] = True
            flags["anomaly_reasons"].append(f"q{i}_difficulty_invalid:{diff}")

        bloom = _safe_int(q.get("bloom_level_estimate"))
        if bloom is None or not (1 <= bloom <= 6):
            flags["has_anomaly"] = True
            flags["anomaly_reasons"].append(f"q{i}_bloom_invalid:{bloom}")

    return {"extracted": extracted, "flags": flags}


# ============================================================================
# write_staging (M3 sec.2.3) - INSERT into question_bank_staging
# ============================================================================


# Staging INSERT - 41 NOT NULL + 4 nullable doldurulan kolon (Plan v1.2.1 sec.5.5)
# Pre-pilot M1: question_bank_staging = LIKE question_bank INCLUDING DEFAULTS
#   + staging_id (UUID PK, gen_random_uuid)
#   + staging_status (default 'pending')
#   + staging_batch_id
#   + staging_created_at (default NOW())
_STAGING_INSERT_SQL = """
INSERT INTO question_bank_staging (
    id, question_text,
    option_a, option_b, option_c, option_d, option_e,
    correct_answer,
    primary_topic_id,
    bloom_level, bloom_category,
    difficulty_level, irt_based_difficulty,
    student_success_rate, difficulty_update_count,
    irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
    is_calibrated, calibration_sample_size, calibration_quality_score,
    morphology_complexity, word_count, unique_word_count, average_word_length,
    readability_score,
    times_asked, times_correct, times_wrong, times_skipped,
    average_response_time, median_response_time, exposure_rate,
    exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year,
    quality_score, quality_review_status,
    source_book, source_page, pipeline_metadata,
    is_active, is_public, is_calib_pool,
    soru_hash,
    staging_batch_id, staging_status
)
VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
    $11, $12::questiondifficultylevel, $13, $14, $15, $16, $17, $18, $19, $20,
    $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
    $31, $32, $33, $34, $35, $36, $37, $38, $39, $40,
    $41, $42, $43, $44, $45, $46, $47, $48, $49, $50
)
RETURNING staging_id::text
"""


async def _lookup_topic_id(topic_code: str, conn: asyncpg.Connection) -> str | None:
    """topic_hierarchy.code -> id lookup. None ise caller fail eder.

    Sema teyit (28 Nis 2026): topic_hierarchy.code VARCHAR(50) UNIQUE NOT NULL,
    topic_hierarchy.id VARCHAR PK.

    Fallback (3 May 2026 smoke fix): code bulunamazsa name_tr ILIKE dene.
    CLI yanlis kod uretirse (orn 'matematik.polinomlar') name_tr=Polinomlar ile
    yakalanir. Birden fazla match varsa level=2 (kavramsal taksonomi) tercih edilir.
    """
    row = await conn.fetchrow(
        "SELECT id FROM topic_hierarchy WHERE code = $1 LIMIT 1",
        topic_code,
    )
    if row:
        return str(row["id"])

    # Fallback: name_tr fuzzy match (kod nokta sonrasi son parcasini name candidate kabul et)
    # 'matematik.polinomlar' -> 'polinomlar', 'MAT.POL' -> 'POL' (zayif)
    candidate = topic_code.split('.')[-1].split('-')[-1].strip()
    if len(candidate) < 3:
        return None
    row2 = await conn.fetchrow(
        """
        SELECT id, code, name_tr FROM topic_hierarchy
        WHERE name_tr ILIKE $1
        ORDER BY level ASC, code ASC
        LIMIT 1
        """,
        f"%{candidate}%",
    )
    if row2:
        log.warning(
            "topic code='%s' bulunamadi, name_tr fallback ile cozuldu: %s (%s)",
            topic_code, row2["code"], row2["name_tr"],
        )
        return str(row2["id"])
    return None


async def write_staging(
    validated: ValidatedPage,
    batch_id: str,
    book_name: str,
    conn: asyncpg.Connection,
    *,
    dry_run: bool = False,
    model: str = DEFAULT_MODEL,
) -> list[str]:
    """Sayfadaki her soru icin staging satiri yazar.

    dry_run=True ise DB'ye yazmaz, sadece olusacak kayit sayisini hesaplar.
    Donus: olusturulan staging_id listesi (dry_run'da bos liste).
    """
    extracted = validated["extracted"]
    questions = extracted.get("questions", [])
    if not questions:
        return []

    file_page = extracted.get("file_page", "0000")
    source_page = _safe_int(file_page) or 0
    exam_type = extracted.get("exam_type", "AYT")
    subject_area = extracted.get("subject_area", "GENEL")
    topic_code = extracted.get("primary_topic_code", "")

    # Topic lookup - dry_run'da skip
    primary_topic_id = None
    if not dry_run:
        primary_topic_id = await _lookup_topic_id(topic_code, conn)
        if primary_topic_id is None:
            raise RuntimeError(
                f"topic_hierarchy.code='{topic_code}' bulunamadi (page {file_page})"
            )
    else:
        primary_topic_id = "DRYRUN_TOPIC_ID"

    pipeline_meta = {
        "pipeline": "v1.2.1",
        "model": model,                            # K-M3-6 + runtime --model flag
        "batch_id": batch_id,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "extraction_confidence": _safe_float(extracted.get("extraction_confidence"), 0.0),
        "page_type": extracted.get("page_type", ""),
        "test_no": extracted.get("test_no"),
        "book_page_from_footer": extracted.get("book_page_from_footer"),
        "needs_manual_review": validated["flags"]["needs_manual_review"],
        "anomaly_reasons": validated["flags"]["anomaly_reasons"],
    }

    staging_ids: list[str] = []

    for q in questions:
        qt = q.get("question_text", "")
        opt_a = q.get("options", {}).get("A", "") or ""
        opt_b = q.get("options", {}).get("B", "") or ""
        opt_c = q.get("options", {}).get("C", "") or ""
        opt_d = q.get("options", {}).get("D", "") or ""
        opt_e = q.get("options", {}).get("E")  # nullable
        correct = q.get("correct_answer", "A")

        # Hash + deterministik ID
        soru_hash = _hash_question(qt, opt_a, opt_b, opt_c, opt_d, opt_e)
        question_id = _uuid5_from_hash(soru_hash)

        # Word stats
        word_count, unique_words, avg_word_len, morph = _word_stats(qt)

        # Bloom level (1-6, fail-safe)
        bloom = _safe_int(q.get("bloom_level_estimate")) or 2
        bloom = max(1, min(6, bloom))

        # Difficulty
        diff_level = q.get("difficulty_estimate", "MEDIUM")
        if diff_level not in DIFFICULTY_ENUM:
            diff_level = "MEDIUM"

        osym_year = _safe_int(q.get("exam_year"))

        # Plan v1.2.1 sec.5.5 default'lari
        params = (
            question_id,                      # $1  id
            _normalize_turkish(qt),           # $2  question_text
            _normalize_turkish(opt_a),        # $3  option_a
            _normalize_turkish(opt_b),        # $4  option_b
            _normalize_turkish(opt_c),        # $5  option_c
            _normalize_turkish(opt_d),        # $6  option_d
            _normalize_turkish(opt_e) if opt_e else None,  # $7 option_e nullable
            correct,                          # $8  correct_answer
            primary_topic_id,                 # $9  primary_topic_id (FK)
            bloom,                            # $10 bloom_level
            "kavrama",                        # $11 bloom_category default
            diff_level,                       # $12 difficulty_level (buyuk harf)
            "medium",                         # $13 irt_based_difficulty (kucuk harf!)
            0.0,                              # $14 student_success_rate
            0,                                # $15 difficulty_update_count
            1.0,                              # $16 irt_discrimination
            0.0,                              # $17 irt_difficulty
            0.2,                              # $18 irt_guessing
            1.0,                              # $19 irt_upper_asymptote
            False,                            # $20 is_calibrated (S5)
            0,                                # $21 calibration_sample_size
            0.0,                              # $22 calibration_quality_score
            morph,                            # $23 morphology_complexity
            word_count,                       # $24 word_count
            unique_words,                     # $25 unique_word_count
            avg_word_len,                     # $26 average_word_length
            50.0,                             # $27 readability_score default
            0,                                # $28 times_asked
            0,                                # $29 times_correct
            0,                                # $30 times_wrong
            0,                                # $31 times_skipped
            0.0,                              # $32 average_response_time
            0.0,                              # $33 median_response_time
            0.0,                              # $34 exposure_rate
            exam_type,                        # $35 exam_type
            subject_area,                     # $36 subject_area
            11,                               # $37 grade_level (AYT/TYT default 11)
            True,                             # $38 osym_format_compliant
            osym_year,                        # $39 osym_year (nullable)
            75.0,                             # $40 quality_score (Plan: dürüst 75 değer)
            "pending",                        # $41 quality_review_status
            book_name,                        # $42 source_book
            source_page,                      # $43 source_page
            pipeline_meta,                    # $44 pipeline_metadata (JSONB string)
            True,                             # $45 is_active
            False,                            # $46 is_public
            False,                            # $47 is_calib_pool (S5)
            soru_hash,                        # $48 soru_hash
            batch_id,                         # $49 staging_batch_id
            "pending",                        # $50 staging_status
        )

        if dry_run:
            staging_ids.append(f"DRYRUN_{question_id}")
            continue

        row = await conn.fetchrow(_STAGING_INSERT_SQL, *params)
        staging_ids.append(row["staging_id"])

    return staging_ids


# ============================================================================
# resolve_conflict + apply_decision (M3 sec.3)
# ============================================================================


# Tum question_bank kolonlari (staging'den question_bank'e SELECT-INSERT icin)
# Plan v1.2.1 sec.5.5 41+4 kolon. created_at/updated_at otomatik.
_QB_COLUMNS = (
    "id, question_text, "
    "option_a, option_b, option_c, option_d, option_e, "
    "correct_answer, primary_topic_id, "
    "bloom_level, bloom_category, "
    "difficulty_level, irt_based_difficulty, "
    "student_success_rate, difficulty_update_count, "
    "irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote, "
    "is_calibrated, calibration_sample_size, calibration_quality_score, "
    "morphology_complexity, word_count, unique_word_count, average_word_length, "
    "readability_score, "
    "times_asked, times_correct, times_wrong, times_skipped, "
    "average_response_time, median_response_time, exposure_rate, "
    "exam_type, subject_area, grade_level, "
    "osym_format_compliant, osym_year, "
    "quality_score, quality_review_status, "
    "source_book, source_page, pipeline_metadata, "
    "is_active, is_public, is_calib_pool, "
    "soru_hash"
)


async def resolve_conflict(
    staging_id: str,
    conn: asyncpg.Connection,
) -> ConflictDecision:
    """Karar agaci (Plan v1.2.1 sec.5.4 + M3 sec.3).

    Hash yoksa -> Katman 1 (INSERT)
    Hash var, kullanilmamis -> Katman 2 (DELETE + INSERT)
    Hash var, korunacak -> Katman 3 (KEEP_OLD -> MRQ)

    Session 88 ek: kalite gate (correct_answer NULL/invalid veya
    needs_manual_review=True) -> hash kontrolunden bagimsiz Katman 3.
    Vision modelin sekilli/grafikli sorularda correct_answer cikaramamasi
    durumunda staging row'u manual_review_queue'ya yonlendirir.
    """
    staging = await conn.fetchrow(
        "SELECT staging_id::text, soru_hash, correct_answer, "
        "pipeline_metadata->>'needs_manual_review' AS needs_review "
        "FROM question_bank_staging WHERE staging_id = $1",
        uuid.UUID(staging_id),
    )
    if staging is None:
        raise ValueError(f"Staging row not found: {staging_id}")

    # Kalite gate (Session 88): NULL/invalid correct_answer veya validate flag
    # -> hash kontrolunden once Layer 3'e zorla. Layer 1/2 question_bank.correct_answer
    # NOT NULL constraint'inde patlardi.
    ca = staging["correct_answer"]
    needs_review = staging["needs_review"] == "true"
    if ca not in {"A", "B", "C", "D", "E"} or needs_review:
        return {
            "staging_id": staging_id,
            "soru_hash": staging["soru_hash"],
            "layer": 3,
            "target_status": "conflict_kept_old",
            "existing_question_id": None,  # _staging_to_mrq 'or ""' ile bos string'e cevirir
            "keep_old_reason": f"quality_gate:correct_answer={ca},needs_review={needs_review}",
        }

    existing = await conn.fetchrow(
        """
        SELECT
            q.id,
            q.is_calibrated,
            q.is_calib_pool,
            EXISTS(
                SELECT 1 FROM student_answers sa
                WHERE sa.question_id = q.id
            ) AS has_answers
        FROM question_bank q
        WHERE q.soru_hash = $1 AND q.is_active = TRUE
        LIMIT 1
        """,
        staging["soru_hash"],
    )

    if existing is None:
        return {
            "staging_id": staging_id,
            "soru_hash": staging["soru_hash"],
            "layer": 1,
            "target_status": "inserted",
            "existing_question_id": None,
            "keep_old_reason": None,
        }

    is_protected = (
        existing["is_calibrated"]
        or existing["is_calib_pool"]
        or existing["has_answers"]
    )

    # NOT: irt_calibrated kolonu Plan v1.2.1 sec.5.4'te zikrediliyor ama
    # mevcut DB'de TRUE=0 (briefing v16). Pilotta bu kolon eklenirse buraya
    # da eklenir; simdilik is_calibrated yeterli.

    if not is_protected:
        return {
            "staging_id": staging_id,
            "soru_hash": staging["soru_hash"],
            "layer": 2,
            "target_status": "conflict_replaced",
            "existing_question_id": str(existing["id"]),
            "keep_old_reason": None,
        }

    reasons = []
    if existing["is_calibrated"]:
        reasons.append("is_calibrated")
    if existing["is_calib_pool"]:
        reasons.append("is_calib_pool")
    if existing["has_answers"]:
        reasons.append("has_answers")

    return {
        "staging_id": staging_id,
        "soru_hash": staging["soru_hash"],
        "layer": 3,
        "target_status": "conflict_kept_old",
        "existing_question_id": str(existing["id"]),
        "keep_old_reason": "kept_old: " + ",".join(reasons),
    }


async def _staging_to_qb(staging_id: str, conn: asyncpg.Connection) -> None:
    """staging row'u question_bank'e kopyalar (LIKE INCLUDING DEFAULTS sayesinde
    sema birebir ayni, SELECT-INSERT yeterli)."""
    sql = f"""
        INSERT INTO question_bank ({_QB_COLUMNS})
        SELECT {_QB_COLUMNS}
        FROM question_bank_staging
        WHERE staging_id = $1
    """
    await conn.execute(sql, uuid.UUID(staging_id))


async def _staging_to_mrq(
    staging_id: str,
    old_question_id: str | None,
    reason: str,
    conn: asyncpg.Connection,
) -> None:
    """Staging row'u manual_review_queue'ya tasir.

    new_payload_json = to_jsonb(s) - PostgreSQL native row->jsonb donusumu,
    ayri Python mapping'e gerek yok. Tum staging kolonlari (LIKE question_bank
    + 4 staging kolonu) JSONB icine gomulur.
    """
    await conn.execute(
        """
        INSERT INTO manual_review_queue (
            old_question_id, new_payload_json, reason, source_book, source_page
        )
        SELECT
            $1,
            to_jsonb(s),
            $2,
            s.source_book,
            s.source_page
        FROM question_bank_staging s
        WHERE s.staging_id = $3
        """,
        old_question_id,
        reason,
        uuid.UUID(staging_id),
    )


async def _update_staging_status(
    staging_id: str,
    status: str,
    conn: asyncpg.Connection,
) -> None:
    await conn.execute(
        "UPDATE question_bank_staging SET staging_status = $1 WHERE staging_id = $2",
        status,
        uuid.UUID(staging_id),
    )


async def apply_decision(
    decision: ConflictDecision,
    conn: asyncpg.Connection,
) -> None:
    """Karara gore DB degisikligi - tek transaction (M3 sec.2.3 + sec.3)."""
    sid = decision["staging_id"]
    layer = decision["layer"]

    async with conn.transaction():
        if layer == 1:
            await _staging_to_qb(sid, conn)
            # Constraint allow: pending|validated|conflict_kept_old|conflict_replaced|failed
            # Layer 1 = yeni soru basari ile question_bank'e tasindi -> 'validated'
            await _update_staging_status(sid, "validated", conn)

        elif layer == 2:
            await conn.execute(
                "DELETE FROM question_bank WHERE id = $1",
                decision["existing_question_id"],
            )
            await _staging_to_qb(sid, conn)
            await _update_staging_status(sid, "conflict_replaced", conn)

        else:  # Katman 3
            await _staging_to_mrq(
                staging_id=sid,
                # Session 88: Quality gate'den gelirse existing_question_id None,
                # NULL FK'yi tetiklemez. Klasik Katman 3 (mevcut korunan) icin '' yerine
                # gercek UUID gelecek.
                old_question_id=decision["existing_question_id"],
                reason=decision["keep_old_reason"] or "kept_old:unknown",
                conn=conn,
            )
            await _update_staging_status(sid, "conflict_kept_old", conn)


# ============================================================================
# finalize_batch (M3 sec.2.3) - summary + qa_sample
# ============================================================================


async def finalize_batch(
    batch_id: str,
    output_dir: Path,
    conn: asyncpg.Connection,
    *,
    failed_pages_csv: Path,
) -> dict:
    """Batch sonu ozet + qa_sample uretir.

    - batch_summary.json: katman dagilimlari, failed sayisi, sureler
    - qa_sample.csv: %1 random + %100 needs_manual_review
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Status dagilimi
    rows = await conn.fetch(
        """
        SELECT staging_status, COUNT(*) AS n
        FROM question_bank_staging
        WHERE staging_batch_id = $1
        GROUP BY staging_status
        """,
        batch_id,
    )
    status_counts = {r["staging_status"]: r["n"] for r in rows}

    # Toplam soru
    total_staged = sum(status_counts.values())

    # MRQ sayisi (bu batch'in pipeline_metadata.batch_id'sine gore)
    mrq_row = await conn.fetchrow(
        """
        SELECT COUNT(*) AS n
        FROM manual_review_queue m
        WHERE m.new_payload_json->>'staging_batch_id' = $1
        """,
        batch_id,
    )
    mrq_count = mrq_row["n"] if mrq_row else 0

    # QA sample - %1 random + %100 needs_manual_review
    qa_size_random = max(1, int(total_staged * QA_RANDOM_RATIO)) if total_staged else 0

    qa_rows = await conn.fetch(
        f"""
        WITH flagged AS (
            SELECT staging_id::text, source_page, soru_hash, staging_status,
                   pipeline_metadata->>'needs_manual_review' AS needs_review,
                   pipeline_metadata->>'anomaly_reasons' AS anomaly_reasons,
                   'flagged' AS sample_type
            FROM question_bank_staging
            WHERE staging_batch_id = $1
              AND pipeline_metadata->>'needs_manual_review' = 'true'
        ),
        random_sample AS (
            SELECT staging_id::text, source_page, soru_hash, staging_status,
                   pipeline_metadata->>'needs_manual_review' AS needs_review,
                   pipeline_metadata->>'anomaly_reasons' AS anomaly_reasons,
                   'random' AS sample_type
            FROM question_bank_staging
            WHERE staging_batch_id = $1
              AND pipeline_metadata->>'needs_manual_review' != 'true'
            ORDER BY random()
            LIMIT {qa_size_random}
        )
        SELECT * FROM flagged
        UNION ALL
        SELECT * FROM random_sample
        """,
        batch_id,
    )

    qa_csv_path = output_dir / "qa_sample.csv"
    with qa_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "staging_id", "source_page", "soru_hash", "staging_status",
            "needs_manual_review", "anomaly_reasons", "sample_type",
        ])
        for r in qa_rows:
            writer.writerow([
                r["staging_id"], r["source_page"], r["soru_hash"], r["staging_status"],
                r["needs_review"], r["anomaly_reasons"], r["sample_type"],
            ])

    # failed_pages.csv satir sayisi
    failed_extract_count = 0
    if failed_pages_csv.exists():
        with failed_pages_csv.open(encoding="utf-8") as f:
            failed_extract_count = max(0, sum(1 for _ in f) - 1)  # header haric

    summary = {
        "batch_id": batch_id,
        "finalized_at": datetime.now(timezone.utc).isoformat(),
        "total_staged": total_staged,
        "status_counts": status_counts,
        "manual_review_queue_added": mrq_count,
        "extract_failed_pages": failed_extract_count,
        "qa_sample_size": len(qa_rows),
        "qa_sample_path": str(qa_csv_path),
        "qa_random_target": qa_size_random,
        "qa_flagged": sum(1 for r in qa_rows if r["sample_type"] == "flagged"),
    }

    summary_path = output_dir / "batch_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("finalize: %s", summary_path)

    return summary


# ============================================================================
# Resume helper (M3 sec.4.2)
# ============================================================================


async def already_completed_pages(
    batch_id: str,
    conn: asyncpg.Connection,
) -> set[int]:
    """Bu batch'te tamamlanmis sayfalar (resume icin atlanir)."""
    rows = await conn.fetch(
        """
        SELECT DISTINCT source_page
        FROM question_bank_staging
        WHERE staging_batch_id = $1
          AND staging_status IN ('validated', 'conflict_replaced', 'conflict_kept_old')
        """,
        batch_id,
    )
    return {r["source_page"] for r in rows if r["source_page"] is not None}


async def batch_id_exists(batch_id: str, conn: asyncpg.Connection) -> bool:
    row = await conn.fetchrow(
        "SELECT 1 FROM question_bank_staging WHERE staging_batch_id = $1 LIMIT 1",
        batch_id,
    )
    return row is not None


# ============================================================================
# Sayfa isleme - extract+validate+stage+resolve+apply tek akis
# ============================================================================


async def _process_page(
    png_path: Path,
    batch_id: str,
    book_name: str,
    pool: asyncpg.Pool | None,
    semaphore: asyncio.Semaphore,
    failed_writer: Any,  # csv._writer instance, runtime tip
    failed_lock: asyncio.Lock,
    *,
    model: str,
    dry_run: bool,
) -> dict:
    """Tek sayfa: extract -> validate -> stage -> resolve -> apply.

    Donus: {file_page, status, layer_counts, error}
    Sayfa-basi 1 connection 1 transaction (K-M3-3).
    """
    file_page = png_path.stem.replace("sayfa_", "")
    result = {
        "file_page": file_page,
        "status": "ok",
        "layer_counts": {1: 0, 2: 0, 3: 0},
        "error": None,
    }

    async with semaphore:
        # 1) Preprocess (Layer 1 + Layer 2 yayinevi-bazli crop, smoke1f-style hazir
        # PNG'lerde no-op). Cache: <book>/.cropped/sayfa_NNNN.png
        from crop_preprocessor import preprocess_page
        try:
            png_to_extract = preprocess_page(png_path)
        except Exception as e:
            log.warning("preprocess %s FAILED, ham PNG ile devam: %s", file_page, e)
            png_to_extract = png_path

        # 2) Extract (DB'siz, claude CLI subprocess)
        try:
            extracted = await extract_page(png_to_extract, model=model)
        except ClaudeCliCriticalError:
            # Auth/quota - pilot durmali, tekrar raise et
            raise
        except Exception as e:
            result["status"] = "extract_failed"
            result["error"] = str(e)
            log.error("extract_page %s FAILED: %s", file_page, e)
            async with failed_lock:
                failed_writer.writerow([file_page, str(png_path), "extract_failed", str(e)])
            return result

        # 2) Validate (saf)
        validated = validate_page(extracted)

        # Dry-run: DB'ye dokunmadan validated JSON'i raporla + dosyaya yaz
        if dry_run or pool is None:
            log.info(
                "dry_run page=%s type=%s subject=%s questions=%d conf=%.2f anomaly=%s review=%s",
                file_page,
                extracted.get("page_type", "?"),
                extracted.get("subject_area", "?"),
                len(extracted.get("questions", [])),
                _safe_float(extracted.get("extraction_confidence"), 0.0),
                validated["flags"]["has_anomaly"],
                validated["flags"]["needs_manual_review"],
            )
            # Debug: extracted JSON'u diske yaz, manuel inceleme icin
            extracted_dir = (
                Path(__file__).parent / "runs" / batch_id / "extracted"
            )
            extracted_dir.mkdir(parents=True, exist_ok=True)
            (extracted_dir / f"sayfa_{file_page}.json").write_text(
                json.dumps(extracted, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return result

        # 3) DB akisi - sayfa-basi connection, sayfa-ici transaction
        try:
            async with pool.acquire() as conn:
                # write_staging (kendi tx'i, hash check pre-pilot UNIQUE'le karsilanir)
                staging_ids = await write_staging(
                    validated, batch_id, book_name, conn,
                    dry_run=False, model=model,
                )

                # Her staging row icin resolve + apply (bagimsiz tx'ler)
                for sid in staging_ids:
                    decision = await resolve_conflict(sid, conn)
                    await apply_decision(decision, conn)
                    result["layer_counts"][decision["layer"]] += 1

                log.info(
                    "page=%s questions=%d L1=%d L2=%d L3=%d",
                    file_page, len(staging_ids),
                    result["layer_counts"][1],
                    result["layer_counts"][2],
                    result["layer_counts"][3],
                )

        except Exception as e:
            result["status"] = "db_failed"
            result["error"] = str(e)
            log.error("page %s DB step failed: %s", file_page, e)
            return result

    return result


# ============================================================================
# main + arg parsing
# ============================================================================


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Pilot 500p - Icerik Pipeline v1.2.1",
    )
    p.add_argument("--book-dir", required=True, type=Path,
                   help="Sayfa PNG'lerini iceren dizin (sayfa_*.png)")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                   help="Paralel sayfa sayisi (smoke=1, 500p=4, prod=8)")
    p.add_argument("--dry-run", action="store_true",
                   help="DB yazimi yok, sadece extract+validate (MCP smoke)")
    p.add_argument("--resume", type=str, default=None,
                   help="Var olan batch_id ile devam (pending+failed sayfalar)")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL,
                   help=f"Anthropic modeli (default: {DEFAULT_MODEL})")
    p.add_argument("--start-page", type=int, default=None,
                   help="Hangi file_page numarasindan baslasin (1-indexed, ornek: --start-page=15)")
    p.add_argument("--max-pages", type=int, default=None,
                   help="Smoke icin sayfa sayisini sinirla (None=hepsi)")
    p.add_argument("--book-name", type=str, default=None,
                   help="source_book degeri (default: book-dir adi)")
    return p.parse_args()


async def _amain(args: argparse.Namespace) -> int:
    book_dir: Path = args.book_dir.resolve()
    if not book_dir.is_dir():
        log.error("--book-dir gecersiz: %s", book_dir)
        return 2

    pages = sorted(book_dir.glob("sayfa_*.png"))
    if not pages:
        log.error("Hicbir sayfa_*.png bulunamadi: %s", book_dir)
        return 2

    book_name = args.book_name or book_dir.name

    # Hibrit C: Claude Code CLI subprocess + Max abonelik havuzu.
    # ANTHROPIC_API_KEY env zorunlu DEGIL; varsa subprocess'e gecirilmez (UNSET).
    # claude CLI Max OAuth ile oturum acar.
    if "ANTHROPIC_API_KEY" in os.environ:
        log.info(
            "ANTHROPIC_API_KEY env var, subprocess'lerden UNSET edilecek (Max havuzu zorlanir)"
        )

    # batch_id - resume veya yeni
    if args.resume:
        batch_id = args.resume
        log.info("RESUME mode: batch_id=%s", batch_id)
    else:
        batch_id = _make_batch_id(book_dir)
        log.info("NEW batch: batch_id=%s", batch_id)

    # Output dizini
    output_dir = Path(__file__).parent / "runs" / batch_id
    output_dir.mkdir(parents=True, exist_ok=True)
    failed_csv_path = output_dir / "failed_pages.csv"

    # Pool - dry_run degilse
    pool: asyncpg.Pool | None = None
    if not args.dry_run:
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            log.error("DATABASE_URL env ayarli degil")
            return 2
        dsn = _normalize_dsn(dsn)
        pool_size = max(2, args.concurrency + POOL_OVERHEAD)
        log.info("asyncpg pool olusturuluyor: min=2 max=%d", pool_size)

        async def _init_conn(conn: asyncpg.Connection) -> None:
            # JSONB ve JSON icin Python dict <-> JSON donusumu
            # Sema teyit: pipeline_metadata 'json', manual_review_queue.new_payload_json 'jsonb'
            await conn.set_type_codec(
                "jsonb",
                encoder=json.dumps,
                decoder=json.loads,
                schema="pg_catalog",
            )
            await conn.set_type_codec(
                "json",
                encoder=json.dumps,
                decoder=json.loads,
                schema="pg_catalog",
            )

        pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=pool_size,
            command_timeout=60,
            init=_init_conn,
        )

    # Resume - tamamlanmis sayfalari atla
    if args.resume and pool is not None:
        async with pool.acquire() as conn:
            if not await batch_id_exists(batch_id, conn):
                log.error("RESUME: batch_id=%s DB'de bulunamadi", batch_id)
                await pool.close()
                return 2
            completed = await already_completed_pages(batch_id, conn)
        before = len(pages)
        pages = [p for p in pages if (_safe_int(p.stem.replace("sayfa_", "")) or -1) not in completed]
        log.info("RESUME: %d completed, %d remaining (toplam %d)", len(completed), len(pages), before)

    # start-page: belli bir sayfadan basla (1-indexed)
    if args.start_page is not None:
        pages = [
            p for p in pages
            if (_safe_int(p.stem.replace("sayfa_", "")) or 0) >= args.start_page
        ]
        log.info("start-page=%d uygulanmis, kalan: %d", args.start_page, len(pages))

    # max-pages limiti
    if args.max_pages is not None:
        pages = pages[: args.max_pages]
        log.info("max-pages=%d uygulanmis, islenecek: %d", args.max_pages, len(pages))

    # failed_pages.csv - append modu (resume'da eski entry'ler korunsun)
    file_exists = failed_csv_path.exists()
    failed_f = failed_csv_path.open("a", newline="", encoding="utf-8")
    failed_writer = csv.writer(failed_f)
    if not file_exists:
        failed_writer.writerow(["file_page", "png_path", "reason", "error"])

    # Anthropic client kaldirildi - extract_page artik claude CLI subprocess kullaniyor
    # (Hibrit C, 28 Nis "opus 47" sohbeti)

    semaphore = asyncio.Semaphore(args.concurrency)
    failed_lock = asyncio.Lock()

    log.info(
        "PILOT START: pages=%d concurrency=%d dry_run=%s model=%s output=%s",
        len(pages), args.concurrency, args.dry_run, args.model, output_dir,
    )

    t0 = time.time()
    tasks = [
        _process_page(
            p, batch_id, book_name, pool, semaphore,
            failed_writer, failed_lock,
            model=args.model, dry_run=args.dry_run,
        )
        for p in pages
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    elapsed = time.time() - t0

    failed_f.close()

    # Ozet
    ok = sum(1 for r in results if r["status"] == "ok")
    extract_failed = sum(1 for r in results if r["status"] == "extract_failed")
    db_failed = sum(1 for r in results if r["status"] == "db_failed")

    layer_total = {1: 0, 2: 0, 3: 0}
    for r in results:
        for k, v in r["layer_counts"].items():
            layer_total[k] += v

    log.info(
        "PILOT END: %.1fs ok=%d extract_failed=%d db_failed=%d  layers L1=%d L2=%d L3=%d",
        elapsed, ok, extract_failed, db_failed,
        layer_total[1], layer_total[2], layer_total[3],
    )

    # finalize_batch (sadece DB modunda)
    if pool is not None:
        async with pool.acquire() as conn:
            await finalize_batch(
                batch_id, output_dir, conn, failed_pages_csv=failed_csv_path,
            )
        await pool.close()
    else:
        # Dry-run minimal summary
        summary = {
            "batch_id": batch_id,
            "mode": "dry_run",
            "pages_processed": len(results),
            "ok": ok,
            "extract_failed": extract_failed,
            "elapsed_seconds": elapsed,
        }
        (output_dir / "batch_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        log.info("dry_run summary: %s", output_dir / "batch_summary.json")

    return 0 if (extract_failed + db_failed) == 0 else 1


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(_amain(args))
    except KeyboardInterrupt:
        log.warning("Interrupted - mevcut tx'ler commit'li, resume ile devam edilebilir")
        return 130


if __name__ == "__main__":
    sys.exit(main())
