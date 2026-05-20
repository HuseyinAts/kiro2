#!/usr/bin/env python3
"""
Phase 7 v3: LLM-dependent metadata via Ollama (Qwen3-8B local).

Architecture (v3 — paralel + bulk + cluster reuse):
  - ThreadPoolExecutor: paralel LLM çağrıları (default parallel=3)
  - Bulk INSERT (execute_values): her N satır tek transaction (default bulk=10)
  - Cluster reuse (optional): pgvector kNN ile near-duplicate metadata kopyala
    (cosine sim>=threshold, default 0.92)

Per question generates:
  - rationales (5 option açıklamaları)
  - misconception_tags
  - solution_steps
  - expected_answer_formula (math için)

Rule-based deterministic fields (LLM'e sorulmaz):
  - solo_level, marzano_level (taxonomy mappings)
  - is_math_solvable (subject lookup)

Resume support: WHERE clause var olan rationale satırlarını atlar.

CLI:
  python metadata_phase7_llm_generation.py --limit 500 --gold-only --apply
  python metadata_phase7_llm_generation.py --limit 500 --gold-only --apply \\
      --parallel 4 --bulk-size 20 --cluster-reuse --cluster-threshold 0.92
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# ─── Rule-based taxonomy mappings ─────────────────────────────────────────

# Bloom → Marzano New Taxonomy (Marzano & Kendall 2007)
BLOOM_TO_MARZANO = {
    "bilgi": "retrieval",
    "kavrama": "comprehension",
    "uygulama": "knowledge_utilization",
    "analiz": "analysis",
    "sentez": "knowledge_utilization",
    "degerlendirme": "metacognitive",
    "değerlendirme": "metacognitive",
}

# (Difficulty, Bloom) → SOLO (Biggs & Collis 1982)
SOLO_TABLE = {
    ("VERY_EASY", "bilgi"): "unistructural",
    ("VERY_EASY", "kavrama"): "unistructural",
    ("EASY", "bilgi"): "unistructural",
    ("EASY", "kavrama"): "multistructural",
    ("EASY", "uygulama"): "multistructural",
    ("MEDIUM", "bilgi"): "unistructural",
    ("MEDIUM", "kavrama"): "multistructural",
    ("MEDIUM", "uygulama"): "multistructural",
    ("MEDIUM", "analiz"): "relational",
    ("HARD", "kavrama"): "multistructural",
    ("HARD", "uygulama"): "relational",
    ("HARD", "analiz"): "relational",
    ("HARD", "sentez"): "extended_abstract",
    ("HARD", "degerlendirme"): "extended_abstract",
    ("HARD", "değerlendirme"): "extended_abstract",
    ("VERY_HARD", "analiz"): "relational",
    ("VERY_HARD", "sentez"): "extended_abstract",
    ("VERY_HARD", "degerlendirme"): "extended_abstract",
    ("VERY_HARD", "değerlendirme"): "extended_abstract",
}
SOLO_FALLBACK = "multistructural"

# Subject → is_math_solvable (SymPy uyumlu sorular)
MATH_SUBJECTS = {"MATEMATIK", "GEOMETRI", "FIZIK", "KIMYA"}


def derive_taxonomy(subject_area, difficulty_level, bloom_category):
    """Rule-based: LLM hallucination'ı önler + 3 alan output token tasarrufu."""
    bloom = (bloom_category or "kavrama").lower().strip()
    diff = (difficulty_level or "MEDIUM").upper().strip()
    subj = (subject_area or "").upper().strip()

    marzano = BLOOM_TO_MARZANO.get(bloom, "comprehension")
    solo = SOLO_TABLE.get((diff, bloom), SOLO_FALLBACK)
    is_math = subj in MATH_SUBJECTS
    return solo, marzano, is_math


# ─── LLM prompt ──────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """Sen Türkiye YKS (TYT/AYT) sınavlarına hazırlık konusunda uzman bir eğitimcisin. Aşağıdaki çoktan seçmeli soruyu analiz et ve istenen metadata'yı JSON formatında üret.

KONU: {subject_area} ({exam_type})
ZORLUK: {difficulty_level}
BLOOM: {bloom_category}

SORU: {question_text}

SEÇENEKLER:
A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}
E) {option_e}

DOĞRU CEVAP: {correct_answer}

KISALIK KURALI: Her rationale TEK CÜMLE (max 25 kelime). Her solution_step TEK CÜMLE (max 20 kelime). Tekrar etme, döngüye girme.

Aşağıdaki JSON formatında yanıt ver (sadece JSON, başka açıklama yok):

{{
  "rationales": {{
    "A": "Tek cümle, max 25 kelime",
    "B": "Tek cümle, max 25 kelime",
    "C": "Tek cümle, max 25 kelime",
    "D": "Tek cümle, max 25 kelime",
    "E": "Tek cümle, max 25 kelime"
  }},
  "misconception_tags": ["kavram_yanılgısı_1", "kavram_yanılgısı_2"],
  "solution_steps": ["Adım 1: ...", "Adım 2: ...", "Adım 3: ..."],
  "expected_answer_formula": "Eğer matematik sorusu ise SymPy uyumlu sembolik ifade (örn: 'x**2 + 3*x - 4'), değilse null"
}}"""


def ollama_generate(prompt, timeout=120):
    """Single LLM call. Thread-safe (urllib.request)."""
    data = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 1500},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    result = json.loads(resp.read())
    return result.get("response", "")


def parse_llm_response(text):
    """Parse LLM JSON response. Returns dict or None."""
    text = (text or "").strip()
    if "{" in text and "}" in text:
        start = text.index("{")
        end = text.rindex("}") + 1
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return None
    return None


# ─── Thread-local DB connection (workers için) ───────────────────────────

_tls = threading.local()


def _worker_conn():
    """Thread-local read connection (cluster reuse kNN için)."""
    if not hasattr(_tls, "conn") or _tls.conn.closed:
        _tls.conn = psycopg2.connect(DSN)
    return _tls.conn


# ─── Cluster reuse (pgvector kNN) ────────────────────────────────────────

CLUSTER_QUERY = """
WITH target AS (
    SELECT embedding FROM question_bank
    WHERE id::text = %s AND embedding IS NOT NULL
    LIMIT 1
),
neighbor AS (
    SELECT q.id::text AS nid,
           1 - (q.embedding <=> (SELECT embedding FROM target)) AS cos_sim,
           q.misconception_tags, q.solution_steps, q.expected_answer_formula
    FROM question_bank q
    WHERE q.embedding IS NOT NULL
      AND q.metadata_filled_at IS NOT NULL
      AND q.id::text != %s
      AND EXISTS (
          SELECT 1 FROM question_option_rationales
          WHERE question_id = q.id::text AND option_letter = 'A'
      )
    ORDER BY q.embedding <=> (SELECT embedding FROM target)
    LIMIT 1
)
SELECT n.nid, n.cos_sim, n.misconception_tags, n.solution_steps, n.expected_answer_formula,
       (SELECT json_object_agg(option_letter, rationale)
        FROM question_option_rationales
        WHERE question_id = n.nid) AS rationales
FROM neighbor n
WHERE n.cos_sim >= %s
"""


def find_cluster_neighbor(qid, threshold):
    """pgvector kNN ile yakın komşu ara. Returns dict|None."""
    try:
        conn = _worker_conn()
        cur = conn.cursor()
        cur.execute(CLUSTER_QUERY, (qid, qid, threshold))
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        nid, sim, miscon, solution, formula, rationales = row
        if not rationales:
            return None
        return {
            "neighbor_id": nid,
            "cos_sim": float(sim),
            "rationales": rationales,
            "misconception": miscon if isinstance(miscon, list) else (miscon or []),
            "solution": solution if isinstance(solution, list) else (solution or []),
            "formula": formula,
        }
    except Exception:
        # Cluster failure → fall through to LLM
        return None


# ─── Worker (LLM call + optional cluster reuse) ──────────────────────────


def process_row(row, cluster_reuse, cluster_threshold):
    """
    Thread worker. Returns result dict:
      {row, ok, source, rationales, misconception, solution, formula, reason?}
    """
    qid, qt, oa, ob, oc, od, oe, ca, subj, exam, diff, bloom = row

    # 1. Cluster reuse (if enabled)
    if cluster_reuse:
        neighbor = find_cluster_neighbor(qid, cluster_threshold)
        if neighbor:
            rationales = neighbor["rationales"] or {}
            if sum(1 for v in rationales.values() if v) >= 5:
                return {
                    "row": row,
                    "ok": True,
                    "source": f"cluster:{neighbor['cos_sim']:.3f}",
                    "rationales": rationales,
                    "misconception": neighbor["misconception"],
                    "solution": neighbor["solution"],
                    "formula": neighbor["formula"],
                }

    # 2. LLM call
    prompt = PROMPT_TEMPLATE.format(
        subject_area=subj or "Genel",
        exam_type=exam or "TYT",
        difficulty_level=diff or "MEDIUM",
        bloom_category=bloom or "kavrama",
        question_text=qt[:1000],
        option_a=oa[:300],
        option_b=ob[:300],
        option_c=oc[:300],
        option_d=(od or "")[:300],
        option_e=(oe or "")[:300],
        correct_answer=ca,
    )

    try:
        raw = ollama_generate(prompt)
    except Exception as e:
        return {
            "row": row,
            "ok": False,
            "reason": f"ollama:{type(e).__name__}:{str(e)[:100]}",
        }

    parsed = parse_llm_response(raw)
    if not parsed or not parsed.get("rationales"):
        return {
            "row": row,
            "ok": False,
            "reason": "parse_fail",
            "raw_head": (raw or "")[:200],
        }

    rationales = parsed.get("rationales", {}) or {}
    if sum(1 for v in rationales.values() if v) < 5:
        return {"row": row, "ok": False, "reason": "incomplete_rationales"}

    return {
        "row": row,
        "ok": True,
        "source": "llm",
        "rationales": rationales,
        "misconception": parsed.get("misconception_tags", []) or [],
        "solution": parsed.get("solution_steps", []) or [],
        "formula": parsed.get("expected_answer_formula"),
    }


# ─── Bulk writer (main thread, single transaction per batch) ─────────────


def bulk_write(writer_conn, results):
    """Bulk INSERT/UPDATE for a batch. Returns (success_count, fail_count)."""
    if not results:
        return 0, 0

    cur = writer_conn.cursor()

    rationales_data = []  # (qid, letter, rationale, is_correct, generated_by)
    qb_updates = []  # (miscon_json, solution_json, solo, marzano, formula, is_math, qid)
    math_rows = []  # (qid, formula)

    success = 0
    fail = 0

    for r in results:
        if not r["ok"]:
            fail += 1
            continue

        qid, _, _, _, _, _, _, ca, subj, _, diff, bloom = r["row"]
        rationales = r["rationales"]
        miscon = r["misconception"]
        solution = r["solution"]
        formula = r["formula"]

        solo, marzano, is_math = derive_taxonomy(subj, diff, bloom)

        # Rationale rows
        for letter in "ABCDE":
            rtxt = rationales.get(letter)
            if rtxt:
                rationales_data.append(
                    (qid, letter, str(rtxt)[:1000], letter == ca, MODEL)
                )

        # question_bank UPDATE
        qb_updates.append(
            (
                json.dumps(miscon, ensure_ascii=False) if miscon else None,
                json.dumps(solution, ensure_ascii=False) if solution else None,
                solo,
                marzano,
                formula,
                is_math,
                qid,
            )
        )

        # question_math
        if is_math and formula:
            math_rows.append((qid, str(formula)[:500]))

        success += 1

    try:
        # 1. Bulk INSERT rationales (execute_values, NOW() in template)
        if rationales_data:
            execute_values(
                cur,
                """
                INSERT INTO question_option_rationales
                  (question_id, option_letter, rationale, is_correct, generated_by, generated_at)
                VALUES %s
                ON CONFLICT (question_id, option_letter)
                  DO UPDATE SET rationale = EXCLUDED.rationale, generated_at = NOW()
                """,
                rationales_data,
                template="(%s, %s, %s, %s, %s, NOW())",
            )

        # 2. Bulk UPDATE question_bank (executemany within transaction)
        if qb_updates:
            cur.executemany(
                """
                UPDATE question_bank
                SET misconception_tags = %s,
                    solution_steps = %s,
                    solo_level = %s,
                    marzano_level = %s,
                    expected_answer_formula = %s,
                    is_math_solvable = %s,
                    metadata_filled_at = NOW()
                WHERE id::text = %s
                """,
                qb_updates,
            )

        # 3. Bulk INSERT question_math
        if math_rows:
            execute_values(
                cur,
                """
                INSERT INTO question_math
                  (question_id, expected_answer_sympy, is_symbolic_verifiable, created_at)
                VALUES %s
                ON CONFLICT (question_id)
                  DO UPDATE SET expected_answer_sympy = EXCLUDED.expected_answer_sympy
                """,
                math_rows,
                template="(%s, %s, TRUE, NOW())",
            )

        writer_conn.commit()
    except Exception as e:
        writer_conn.rollback()
        # Treat all `ok` rows in this batch as failed
        fail += success
        success = 0
        print(
            f"  [bulk-write] ROLLBACK: {type(e).__name__}: {str(e)[:200]}", flush=True
        )

    return success, fail


# ─── Main ────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="Max questions to process")
    ap.add_argument("--apply", action="store_true", help="Persist writes to DB")
    ap.add_argument(
        "--gold-only",
        action="store_true",
        help="Filter to R4_rule_based_gold (beta-eligible) only",
    )
    ap.add_argument(
        "--parallel", type=int, default=3, help="Concurrent LLM workers (default 3)"
    )
    ap.add_argument(
        "--bulk-size",
        type=int,
        default=10,
        help="Bulk write batch size (default 10)",
    )
    ap.add_argument(
        "--cluster-reuse",
        action="store_true",
        help="Enable pgvector kNN cluster reuse",
    )
    ap.add_argument(
        "--cluster-threshold",
        type=float,
        default=0.92,
        help="Minimum cosine similarity for cluster reuse (default 0.92)",
    )
    args = ap.parse_args()

    # Fetch rows (resume-aware via LEFT JOIN)
    fetch_conn = psycopg2.connect(DSN)
    fetch_cur = fetch_conn.cursor()
    gold_filter = (
        "AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'"
        if args.gold_only
        else ""
    )
    fetch_cur.execute(
        f"""
        SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
               q.correct_answer, q.subject_area, q.exam_type, q.difficulty_level::text, q.bloom_category
        FROM question_bank q
        LEFT JOIN question_option_rationales r ON r.question_id = q.id::text AND r.option_letter = 'A'
        WHERE q.is_active = true
          AND q.question_text IS NOT NULL
          AND q.option_a IS NOT NULL
          AND q.correct_answer IN ('A', 'B', 'C', 'D', 'E')
          AND r.question_id IS NULL
          {gold_filter}
        ORDER BY q.created_at DESC
        LIMIT %s
        """,
        (args.limit,),
    )
    rows = fetch_cur.fetchall()
    fetch_conn.close()

    print(
        f"[scan] {len(rows):,} rows | model={MODEL} | parallel={args.parallel} | "
        f"bulk={args.bulk_size} | cluster_reuse={args.cluster_reuse}"
        f"{f' (sim>={args.cluster_threshold})' if args.cluster_reuse else ''} | "
        f"apply={args.apply}\n",
        flush=True,
    )

    if not rows:
        print("[done] no rows to process")
        return

    writer = psycopg2.connect(DSN) if args.apply else None

    success_total = 0
    failed_total = 0
    source_counts = {"llm": 0, "cluster": 0}
    t_start = time.time()
    pending = []

    def flush():
        nonlocal success_total, failed_total
        if not pending:
            return
        if args.apply:
            s, f = bulk_write(writer, pending)
            success_total += s
            failed_total += f
        else:
            success_total += sum(1 for r in pending if r["ok"])
            failed_total += sum(1 for r in pending if not r["ok"])

        # Track sources
        for r in pending:
            if r.get("ok"):
                src = r.get("source", "llm").split(":")[0]
                source_counts[src] = source_counts.get(src, 0) + 1

        # Show first few fails for debugging
        for r in pending:
            if not r.get("ok") and (failed_total <= 3):
                print(
                    f"  [fail] {r['row'][0][:8]} reason={r.get('reason', '?')}",
                    flush=True,
                )

        pending.clear()

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {
            pool.submit(
                process_row, row, args.cluster_reuse, args.cluster_threshold
            ): row
            for row in rows
        }
        for fut in as_completed(futures):
            result = fut.result()
            pending.append(result)

            if len(pending) >= args.bulk_size:
                flush()
                elapsed = time.time() - t_start
                completed = success_total + failed_total
                rate = completed / elapsed * 60 if elapsed > 0 else 0
                src_str = f" sources={source_counts}" if args.cluster_reuse else ""
                print(
                    f"  [{completed}/{len(rows)}] success={success_total} "
                    f"failed={failed_total} rate={rate:.1f}/min{src_str}",
                    flush=True,
                )

    flush()

    elapsed = time.time() - t_start
    rate = (success_total + failed_total) / elapsed * 60 if elapsed > 0 else 0
    print(
        f"\n[done] processed {len(rows)} | success={success_total} failed={failed_total} | "
        f"time={elapsed / 60:.1f}min | final_rate={rate:.1f}/min"
    )
    if args.cluster_reuse:
        print(f"  sources: {source_counts}")
    if writer:
        writer.close()


if __name__ == "__main__":
    main()
