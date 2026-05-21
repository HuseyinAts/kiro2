#!/usr/bin/env python3
"""
A/B Test: o3 (OpenAI reasoning) vs gemini-flash-latest (Google reasoning).

Identical 50 questions to both models. Compare side-by-side.
Output: TSV with both rationales for manual review.

Usage:
    OPENAI_API_KEY=... GEMINI_API_KEY=... python ab_test_o3_vs_gemini.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "scripts" / "quality"))
from metadata_phase7_llm_generation import PROMPT_TEMPLATE  # noqa

DSN = "postgresql://postgres:1470@localhost:5434/kiro2"
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
SAMPLE_N = int(os.getenv("SAMPLE_N", "50"))

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-flash-latest"  # auto-routes to newest Flash (3.x)
OPENAI_MODEL = "o3"


def fetch_samples(n: int):
    """Pull n random pending gold rows, balanced by subject."""
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
               q.option_e, q.correct_answer, q.subject_area, q.exam_type,
               q.difficulty_level::text, q.bloom_category
        FROM question_bank q
        LEFT JOIN question_option_rationales r
          ON r.question_id = q.id::text AND r.option_letter = 'A'
        WHERE q.is_active AND q.question_text IS NOT NULL AND q.option_a IS NOT NULL
          AND q.correct_answer IN ('A','B','C','D','E') AND r.question_id IS NULL
          AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
        ORDER BY md5(q.id::text)
        LIMIT %s
        """,
        (n,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


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


def call_o3(prompt: str, timeout: int = 120):
    body = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 4000,
        "reasoning_effort": "medium",
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        OPENAI_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        dt = time.time() - t0
        text = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        return {
            "ok": True,
            "text": text,
            "dt": dt,
            "in_tokens": usage.get("prompt_tokens", 0),
            "out_tokens": usage.get("completion_tokens", 0),
            "reasoning_tokens": usage.get("completion_tokens_details", {}).get(
                "reasoning_tokens", 0
            ),
        }
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {str(e)[:200]}"}


def call_gemini(prompt: str, timeout: int = 120):
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4000,
            "responseMimeType": "application/json",
        },
    }
    url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        dt = time.time() - t0
        cands = result.get("candidates") or []
        if not cands:
            return {"ok": False, "err": "empty candidates"}
        parts = cands[0].get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        usage = result.get("usageMetadata", {})
        return {
            "ok": True,
            "text": text,
            "dt": dt,
            "in_tokens": usage.get("promptTokenCount", 0),
            "out_tokens": usage.get("candidatesTokenCount", 0),
            "reasoning_tokens": usage.get("thoughtsTokenCount", 0),
            "model_version": result.get("modelVersion", ""),
        }
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {str(e)[:200]}"}


def score_quality(text: str) -> dict:
    """Extract JSON and score schema completeness."""
    s = {
        "json_valid": False,
        "n_rationales": 0,
        "all_5_options": False,
        "has_misconception": False,
        "has_solution": False,
        "avg_rationale_len": 0,
    }
    text = (text or "").replace("\x00", "")
    if "{" not in text:
        return s
    start = text.find("{")
    end = text.rfind("}")
    raw = text[start : end + 1]
    try:
        d = json.loads(raw)
        s["json_valid"] = True
    except Exception:
        return s
    rats = d.get("rationales") or {}
    if isinstance(rats, dict):
        non_empty = [v for v in rats.values() if v]
        s["n_rationales"] = len(non_empty)
        s["all_5_options"] = len(non_empty) >= 5
        if non_empty:
            s["avg_rationale_len"] = sum(len(str(v)) for v in non_empty) // len(
                non_empty
            )
    s["has_misconception"] = bool(d.get("misconception_tags"))
    s["has_solution"] = bool(d.get("solution_steps"))
    return s


def process_one(row):
    """Call both models in parallel for one question."""
    prompt = build_prompt(row)
    qid = row[0]
    subj = row[8]
    ca = row[7]

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_o3 = pool.submit(call_o3, prompt)
        f_gem = pool.submit(call_gemini, prompt)
        r_o3 = f_o3.result()
        r_gem = f_gem.result()

    return {"qid": qid, "subj": subj, "ca": ca, "o3": r_o3, "gem": r_gem, "row": row}


def main():
    if not OPENAI_KEY:
        print("FATAL: OPENAI_API_KEY missing")
        sys.exit(1)
    if not GEMINI_KEY:
        print("FATAL: GEMINI_API_KEY missing")
        sys.exit(1)

    rows = fetch_samples(SAMPLE_N)
    print(f"[ab-test] n={len(rows)} | o3={OPENAI_MODEL} | gemini={GEMINI_MODEL}")
    print(
        "  subj distribution: "
        + ", ".join(
            f"{s}={c}"
            for s, c in {
                s: sum(1 for r in rows if r[8] == s) for s in set(r[8] for r in rows)
            }.items()
        )
    )

    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(process_one, row) for row in rows]
        for i, f in enumerate(as_completed(futures)):
            r = f.result()
            results.append(r)
            mark_o3 = "✓" if r["o3"]["ok"] else "✗"
            mark_gem = "✓" if r["gem"]["ok"] else "✗"
            dt_o3 = r["o3"].get("dt", 0)
            dt_gem = r["gem"].get("dt", 0)
            print(
                f"  [{i + 1}/{len(rows)}] {r['qid'][:8]} {r['subj']:10s} "
                f"o3={mark_o3} {dt_o3:.1f}s | gem={mark_gem} {dt_gem:.1f}s",
                flush=True,
            )

    # Aggregate
    o3_ok = sum(1 for r in results if r["o3"]["ok"])
    gem_ok = sum(1 for r in results if r["gem"]["ok"])
    o3_qual = [score_quality(r["o3"]["text"]) for r in results if r["o3"]["ok"]]
    gem_qual = [score_quality(r["gem"]["text"]) for r in results if r["gem"]["ok"]]

    print("\n" + "=" * 72)
    print("AGGREGATE METRICS")
    print("=" * 72)

    def summarize(name, oks, qual, results_subset, key):
        ts = [r[key].get("dt", 0) for r in results_subset if r[key]["ok"]]
        in_ts = [r[key].get("in_tokens", 0) for r in results_subset if r[key]["ok"]]
        out_ts = [r[key].get("out_tokens", 0) for r in results_subset if r[key]["ok"]]
        reas_ts = [
            r[key].get("reasoning_tokens", 0) for r in results_subset if r[key]["ok"]
        ]
        json_ok = sum(1 for q in qual if q["json_valid"])
        all5 = sum(1 for q in qual if q["all_5_options"])
        has_misc = sum(1 for q in qual if q["has_misconception"])
        has_sol = sum(1 for q in qual if q["has_solution"])
        avg_len = (
            sum(q["avg_rationale_len"] for q in qual) // max(len(qual), 1)
            if qual
            else 0
        )
        print(f"\n{name}:")
        print(
            f"  Success rate    : {oks}/{len(results_subset)} ({oks / len(results_subset) * 100:.0f}%)"
        )
        if ts:
            print(f"  Avg duration    : {sum(ts) / len(ts):.1f}s")
            print(f"  Avg in tokens   : {sum(in_ts) / len(in_ts):.0f}")
            print(f"  Avg out tokens  : {sum(out_ts) / len(out_ts):.0f}")
            print(f"  Avg reasoning   : {sum(reas_ts) / len(reas_ts):.0f}")
        print(
            f"  JSON valid      : {json_ok}/{len(qual)} ({json_ok / max(len(qual), 1) * 100:.0f}%)"
        )
        print(f"  All 5 rationales: {all5}/{len(qual)}")
        print(f"  Has misconception: {has_misc}/{len(qual)}")
        print(f"  Has solution    : {has_sol}/{len(qual)}")
        print(f"  Avg rationale length: {avg_len} chars")

    summarize("o3 (OpenAI reasoning)", o3_ok, o3_qual, results, "o3")
    summarize(f"Gemini ({GEMINI_MODEL})", gem_ok, gem_qual, results, "gem")

    # 79K cost projection
    print("\n" + "=" * 72)
    print("COST PROJECTION (79K rows, batch API estimate)")
    print("=" * 72)
    o3_in = sum(r["o3"].get("in_tokens", 0) for r in results if r["o3"]["ok"]) / max(
        o3_ok, 1
    )
    o3_out = sum(r["o3"].get("out_tokens", 0) for r in results if r["o3"]["ok"]) / max(
        o3_ok, 1
    )
    gem_in = sum(r["gem"].get("in_tokens", 0) for r in results if r["gem"]["ok"]) / max(
        gem_ok, 1
    )
    gem_out = sum(
        r["gem"].get("out_tokens", 0) for r in results if r["gem"]["ok"]
    ) / max(gem_ok, 1)
    # batch prices: o3 $1.00/$4.00 (50% off $2/$8); gemini flash $0.75/$4.50 (batch)
    o3_cost = (79000 * o3_in / 1e6) * 1.00 + (79000 * o3_out / 1e6) * 4.00
    gem_cost = (79000 * gem_in / 1e6) * 0.75 + (79000 * gem_out / 1e6) * 4.50
    print(
        f"  o3 batch     : ~${o3_cost:.0f}  ({o3_in:.0f}in + {o3_out:.0f}out per call)"
    )
    print(
        f"  Gemini batch : ~${gem_cost:.0f}  ({gem_in:.0f}in + {gem_out:.0f}out per call)"
    )

    # Write side-by-side TSV
    out_path = THIS_DIR / "20260521_ab_test_o3_vs_gemini_RAW.tsv"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("qid\tsubject\tcorrect\tquestion_text\to3_text\tgemini_text\n")
        for r in results:
            row = r["row"]
            qt = (row[1] or "").replace("\t", " ").replace("\n", " ")[:300]
            o3_text = (
                r["o3"]
                .get("text", r["o3"].get("err", ""))
                .replace("\t", " ")
                .replace("\n", "\\n")
            )
            gem_text = (
                r["gem"]
                .get("text", r["gem"].get("err", ""))
                .replace("\t", " ")
                .replace("\n", "\\n")
            )
            f.write(
                f"{r['qid']}\t{r['subj']}\t{r['ca']}\t{qt}\t{o3_text}\t{gem_text}\n"
            )
    print(f"\n[saved] {out_path}")


if __name__ == "__main__":
    main()
