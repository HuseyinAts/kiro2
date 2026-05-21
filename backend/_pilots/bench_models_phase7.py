#!/usr/bin/env python3
"""
Deep benchmark — 5 models vs 10 real Phase 7 prompts.

Metrics:
- duration (ms) per call
- eval_count, eval_duration (token/sn)
- JSON valid: parse success
- Schema complete: has rationales A-E + misconception + solution + (formula)
- Turkish quality: ratio of Turkish-specific characters (ı, ğ, ş, ç, ö, ü), no English bleed words

Models tested (all Q4_K_M GGUF via Ollama):
  qwen3:8b      — current production, thinking-capable
  qwen3:14b     — bigger, slower, available
  qwen2.5:7b    — no thinking, faster
  qwen2.5:3b    — small, fastest
  qwen3:4b      — small qwen3

Phase 7 prompt is gold subset stratified (3 math, 3 fizik, 2 sosyal, 2 edebiyat).
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "quality"))
from metadata_phase7_llm_generation import PROMPT_TEMPLATE  # noqa: E402

DSN = "postgresql://postgres:1470@localhost:5434/kiro2"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Stratified 10 sample (3 math, 3 fizik, 2 sosyal, 2 edebiyat)
SAMPLE_SQL = """
(
SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
       q.correct_answer, q.subject_area, q.exam_type, q.difficulty_level::text, q.bloom_category
FROM question_bank q
LEFT JOIN question_option_rationales r ON r.question_id = q.id::text AND r.option_letter = 'A'
WHERE q.is_active = true
  AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
  AND r.question_id IS NULL
  AND q.subject_area IN ('MATEMATIK','GEOMETRI') LIMIT 3
)
UNION ALL
(
SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
       q.correct_answer, q.subject_area, q.exam_type, q.difficulty_level::text, q.bloom_category
FROM question_bank q
LEFT JOIN question_option_rationales r ON r.question_id = q.id::text AND r.option_letter = 'A'
WHERE q.is_active = true
  AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
  AND r.question_id IS NULL
  AND q.subject_area = 'FIZIK' LIMIT 3
)
UNION ALL
(
SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
       q.correct_answer, q.subject_area, q.exam_type, q.difficulty_level::text, q.bloom_category
FROM question_bank q
LEFT JOIN question_option_rationales r ON r.question_id = q.id::text AND r.option_letter = 'A'
WHERE q.is_active = true
  AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
  AND r.question_id IS NULL
  AND q.subject_area IN ('SOSYAL','TARIH','COGRAFYA') LIMIT 2
)
UNION ALL
(
SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
       q.correct_answer, q.subject_area, q.exam_type, q.difficulty_level::text, q.bloom_category
FROM question_bank q
LEFT JOIN question_option_rationales r ON r.question_id = q.id::text AND r.option_letter = 'A'
WHERE q.is_active = true
  AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
  AND r.question_id IS NULL
  AND q.subject_area IN ('TURKCE','EDEBIYAT') LIMIT 2
)
"""

TURKISH_CHARS = set("ıİğĞşŞçÇöÖüÜ")
ENGLISH_BLEED_WORDS = {
    "the",
    "is",
    "are",
    "this",
    "that",
    "answer",
    "correct",
    "wrong",
    "explanation",
    "because",
    "therefore",
    "since",
    "however",
}


def build_prompt(row):
    qid, qt, oa, ob, oc, od, oe, ca, subj, exam, diff, bloom = row
    return PROMPT_TEMPLATE.format(
        subject_area=subj or "Genel",
        exam_type=exam or "TYT",
        difficulty_level=diff or "MEDIUM",
        bloom_category=bloom or "kavrama",
        question_text=qt[:1000],
        option_a=oa[:300] if oa else "",
        option_b=ob[:300] if ob else "",
        option_c=oc[:300] if oc else "",
        option_d=(od or "")[:300],
        option_e=(oe or "")[:300],
        correct_answer=ca,
    )


def call_ollama(model: str, prompt: str, timeout: int = 180):
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {"temperature": 0.1, "num_predict": 1500},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    resp = urllib.request.urlopen(req, timeout=timeout)
    result = json.loads(resp.read())
    return (time.time() - t0) * 1000.0, result


def score_quality(raw_text: str) -> dict:
    score = {
        "json_valid": False,
        "has_rationales_5": False,
        "has_misconception": False,
        "has_solution": False,
        "tr_char_ratio": 0.0,
        "english_bleed": 0,
        "total_text_chars": 0,
    }
    try:
        d = json.loads(raw_text)
        score["json_valid"] = True
    except Exception:
        return score
    rats = d.get("rationales") or {}
    if isinstance(rats, dict) and all(k in rats and rats[k] for k in "ABCDE"):
        score["has_rationales_5"] = True
    if d.get("misconception_tags"):
        score["has_misconception"] = True
    if d.get("solution_steps"):
        score["has_solution"] = True
    all_text = (
        " ".join(str(v) for v in (rats or {}).values())
        + " "
        + " ".join(d.get("solution_steps") or [])
    )
    if all_text.strip():
        tr_chars = sum(1 for c in all_text if c in TURKISH_CHARS)
        score["tr_char_ratio"] = tr_chars / max(len(all_text), 1)
        score["total_text_chars"] = len(all_text)
        low = all_text.lower()
        score["english_bleed"] = sum(
            1 for w in ENGLISH_BLEED_WORDS if re.search(rf"\b{re.escape(w)}\b", low)
        )
    return score


def bench_model(model: str, samples: list):
    print(f"\n{'=' * 72}\nMODEL: {model}\n{'=' * 72}")
    # Warmup
    try:
        _ = call_ollama(model, "hi", timeout=120)
    except Exception as e:
        print(f"  [SKIP] warmup failed: {e}")
        return None
    results = []
    for i, row in enumerate(samples):
        prompt = build_prompt(row)
        try:
            dt, r = call_ollama(model, prompt)
        except Exception as e:
            print(f"  [{i + 1}/{len(samples)}] ERROR: {e}")
            results.append({"err": str(e), "subj": row[8]})
            continue
        text = r.get("response", "")
        q = score_quality(text)
        eval_count = r.get("eval_count", 0)
        eval_dur_ms = r.get("eval_duration", 0) / 1e6
        tps = eval_count / (eval_dur_ms / 1000) if eval_dur_ms else 0
        print(
            f"  [{i + 1}/{len(samples)}] {row[8]:10s} dt={dt:6.0f}ms tps={tps:5.1f} "
            f"json={'✓' if q['json_valid'] else '✗'} "
            f"5opt={'✓' if q['has_rationales_5'] else '✗'} "
            f"misc={'✓' if q['has_misconception'] else '✗'} "
            f"sol={'✓' if q['has_solution'] else '✗'} "
            f"tr={q['tr_char_ratio'] * 100:.0f}% en={q['english_bleed']}"
        )
        results.append(
            {
                "dt": dt,
                "tps": tps,
                "eval_count": eval_count,
                "q": q,
                "subj": row[8],
                "qid": row[0][:8],
            }
        )
    # Aggregate
    valid = [r for r in results if "dt" in r]
    if not valid:
        return None
    avg_dt = sum(r["dt"] for r in valid) / len(valid)
    avg_tps = sum(r["tps"] for r in valid) / len(valid)
    rate_q_per_min = 60000 / avg_dt
    json_ok = sum(1 for r in valid if r["q"]["json_valid"]) / len(valid)
    schema_ok = sum(
        1 for r in valid if r["q"]["has_rationales_5"] and r["q"]["has_solution"]
    ) / len(valid)
    tr_avg = sum(r["q"]["tr_char_ratio"] for r in valid) / len(valid)
    en_bleed_avg = sum(r["q"]["english_bleed"] for r in valid) / len(valid)
    print(
        f"  >> avg_dt={avg_dt:.0f}ms | tps={avg_tps:.1f} | "
        f"q/min={rate_q_per_min:.1f} | json_ok={json_ok * 100:.0f}% | "
        f"schema_ok={schema_ok * 100:.0f}% | tr_ratio={tr_avg * 100:.1f}% | "
        f"en_bleed={en_bleed_avg:.2f}/call"
    )
    return {
        "model": model,
        "avg_dt": avg_dt,
        "tps": avg_tps,
        "rate_q_per_min": rate_q_per_min,
        "json_ok": json_ok,
        "schema_ok": schema_ok,
        "tr_ratio": tr_avg,
        "en_bleed": en_bleed_avg,
        "details": results,
    }


def main():
    # Load samples
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(SAMPLE_SQL)
    samples = cur.fetchall()
    conn.close()
    print(f"Loaded {len(samples)} stratified samples")
    for s in samples:
        print(f"  {s[0][:8]} {s[8]:10s} qlen={len(s[1])}")

    # Models to test (filter by what's available)
    candidates = [
        "qwen3:8b",
        "qwen2.5:7b-instruct",
        "qwen2.5:3b-instruct",
        "qwen3:4b",
        "qwen3:14b",
    ]
    available = []
    try:
        r = urllib.request.urlopen("http://localhost:11434/api/tags").read()
        installed = {m["name"] for m in json.loads(r)["models"]}
        for c in candidates:
            if c in installed:
                available.append(c)
            else:
                print(f"  [skip] not installed: {c}")
    except Exception as e:
        print(f"warning: {e}")
        available = candidates

    print(f"\nBenchmarking {len(available)} models on {len(samples)} samples...")

    all_results = []
    for model in available:
        r = bench_model(model, samples)
        if r:
            all_results.append(r)

    # Summary table
    print(f"\n{'=' * 72}\nFINAL COMPARISON\n{'=' * 72}")
    print(
        f"{'Model':<25s} {'q/min':>7s} {'tps':>6s} {'json%':>6s} {'schema%':>8s} "
        f"{'tr%':>6s} {'en_bleed':>9s} {'79K_hours':>10s}"
    )
    print("-" * 80)
    for r in sorted(all_results, key=lambda x: -x["rate_q_per_min"]):
        hours = 79000 / r["rate_q_per_min"] / 60
        print(
            f"{r['model']:<25s} {r['rate_q_per_min']:>7.1f} {r['tps']:>6.1f} "
            f"{r['json_ok'] * 100:>5.0f}% {r['schema_ok'] * 100:>7.0f}% "
            f"{r['tr_ratio'] * 100:>5.1f}% {r['en_bleed']:>8.2f} {hours:>9.1f}h"
        )

    # Save raw
    out = Path(__file__).parent / "20260520_bench_models_RESULT.json"
    out.write_text(
        json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()
