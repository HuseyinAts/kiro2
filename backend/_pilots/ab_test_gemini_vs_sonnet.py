#!/usr/bin/env python3
"""
A/B Test: Gemini Flash latest vs Claude Sonnet 4.6 (thinking).

Identical 50 questions to both models. Side-by-side comparison.
Output: TSV + aggregate metrics + 79K cost projection.
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
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SAMPLE_N = int(os.getenv("SAMPLE_N", "50"))

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-flash-latest"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-6"


def fetch_samples(n: int):
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
        }
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {str(e)[:200]}"}


def call_sonnet(prompt: str, timeout: int = 180):
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4000,
        "temperature": 1,  # thinking mode requires temp=1
        "thinking": {"type": "enabled", "budget_tokens": 2000},
        "messages": [
            {
                "role": "user",
                "content": prompt
                + "\n\nÖNEMLİ: Yalnızca JSON döndür, başka hiçbir metin ekleme.",
            }
        ],
    }
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        dt = time.time() - t0
        # Sonnet thinking returns content as array; find text block
        text = ""
        for blk in result.get("content", []):
            if blk.get("type") == "text":
                text += blk.get("text", "")
        usage = result.get("usage", {})
        return {
            "ok": True,
            "text": text,
            "dt": dt,
            "in_tokens": usage.get("input_tokens", 0),
            "out_tokens": usage.get("output_tokens", 0),
            "reasoning_tokens": usage.get(
                "cache_read_input_tokens", 0
            ),  # not exposed for thinking
        }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "err": f"HTTP {e.code}: {err_body[:300]}"}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {str(e)[:200]}"}


def score_quality(text: str) -> dict:
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
    prompt = build_prompt(row)
    qid = row[0]
    subj = row[8]
    ca = row[7]
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_g = pool.submit(call_gemini, prompt)
        f_s = pool.submit(call_sonnet, prompt)
        r_g = f_g.result()
        r_s = f_s.result()
    return {"qid": qid, "subj": subj, "ca": ca, "gem": r_g, "son": r_s, "row": row}


def main():
    if not GEMINI_KEY:
        print("FATAL: GEMINI_API_KEY missing")
        sys.exit(1)
    if not ANTHROPIC_KEY:
        print("FATAL: ANTHROPIC_API_KEY missing")
        sys.exit(1)

    rows = fetch_samples(SAMPLE_N)
    print(f"[ab-test] n={len(rows)} | gemini={GEMINI_MODEL} | sonnet={ANTHROPIC_MODEL}")
    subj_dist = dict.fromkeys(set(r[8] for r in rows), 0)
    for r in rows:
        subj_dist[r[8]] += 1
    print("  subj: " + ", ".join(f"{k}={v}" for k, v in sorted(subj_dist.items())))

    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(process_one, row) for row in rows]
        for i, f in enumerate(as_completed(futures)):
            r = f.result()
            results.append(r)
            mark_g = "✓" if r["gem"]["ok"] else "✗"
            mark_s = "✓" if r["son"]["ok"] else "✗"
            dt_g = r["gem"].get("dt", 0)
            dt_s = r["son"].get("dt", 0)
            extra = ""
            if not r["gem"]["ok"]:
                extra += f" gem_err={r['gem'].get('err', '')[:80]}"
            if not r["son"]["ok"]:
                extra += f" son_err={r['son'].get('err', '')[:80]}"
            print(
                f"  [{i + 1}/{len(rows)}] {r['qid'][:8]} {r['subj']:10s} "
                f"gem={mark_g} {dt_g:.1f}s | son={mark_s} {dt_s:.1f}s{extra}",
                flush=True,
            )

    g_ok = sum(1 for r in results if r["gem"]["ok"])
    s_ok = sum(1 for r in results if r["son"]["ok"])
    g_qual = [score_quality(r["gem"]["text"]) for r in results if r["gem"]["ok"]]
    s_qual = [score_quality(r["son"]["text"]) for r in results if r["son"]["ok"]]

    print("\n" + "=" * 72)
    print("AGGREGATE METRICS")
    print("=" * 72)

    def summarize(name, oks, qual, results_subset, key):
        ts = [r[key].get("dt", 0) for r in results_subset if r[key]["ok"]]
        in_ts = [r[key].get("in_tokens", 0) for r in results_subset if r[key]["ok"]]
        out_ts = [r[key].get("out_tokens", 0) for r in results_subset if r[key]["ok"]]
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
            f"  Success rate     : {oks}/{len(results_subset)} "
            f"({oks / len(results_subset) * 100:.0f}%)"
        )
        if ts:
            print(f"  Avg duration     : {sum(ts) / len(ts):.1f}s")
            print(f"  Avg in tokens    : {sum(in_ts) / len(in_ts):.0f}")
            print(f"  Avg out tokens   : {sum(out_ts) / len(out_ts):.0f}")
        print(
            f"  JSON valid       : {json_ok}/{len(qual)} "
            f"({json_ok / max(len(qual), 1) * 100:.0f}%)"
        )
        print(f"  All 5 rationales : {all5}/{len(qual)}")
        print(f"  Has misconception: {has_misc}/{len(qual)}")
        print(f"  Has solution     : {has_sol}/{len(qual)}")
        print(f"  Avg rationale len: {avg_len} chars")

    summarize(f"Gemini ({GEMINI_MODEL})", g_ok, g_qual, results, "gem")
    summarize(f"Sonnet ({ANTHROPIC_MODEL}) thinking", s_ok, s_qual, results, "son")

    # Cost
    print("\n" + "=" * 72)
    print("COST PROJECTION (79K rows, batch API estimate)")
    print("=" * 72)
    g_in = sum(r["gem"].get("in_tokens", 0) for r in results if r["gem"]["ok"]) / max(
        g_ok, 1
    )
    g_out = sum(r["gem"].get("out_tokens", 0) for r in results if r["gem"]["ok"]) / max(
        g_ok, 1
    )
    s_in = sum(r["son"].get("in_tokens", 0) for r in results if r["son"]["ok"]) / max(
        s_ok, 1
    )
    s_out = sum(r["son"].get("out_tokens", 0) for r in results if r["son"]["ok"]) / max(
        s_ok, 1
    )
    # Batch prices: Gemini Flash $0.75/$4.50 (50% off $1.50/$9); Sonnet 4.6 $1.50/$7.50 (50% off $3/$15)
    g_cost = (79000 * g_in / 1e6) * 0.75 + (79000 * g_out / 1e6) * 4.50
    s_cost = (79000 * s_in / 1e6) * 1.50 + (79000 * s_out / 1e6) * 7.50
    print(f"  Gemini batch : ~${g_cost:.0f}  ({g_in:.0f}in + {g_out:.0f}out)")
    print(f"  Sonnet batch : ~${s_cost:.0f}  ({s_in:.0f}in + {s_out:.0f}out)")

    out_path = THIS_DIR / "20260521_ab_test_gemini_vs_sonnet_RAW.tsv"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("qid\tsubject\tcorrect\tquestion_text\tgemini_text\tsonnet_text\n")
        for r in results:
            row = r["row"]
            qt = (row[1] or "").replace("\t", " ").replace("\n", " ")[:300]
            g_text = (
                r["gem"]
                .get("text", r["gem"].get("err", ""))
                .replace("\t", " ")
                .replace("\n", "\\n")
            )
            s_text = (
                r["son"]
                .get("text", r["son"].get("err", ""))
                .replace("\t", " ")
                .replace("\n", "\\n")
            )
            f.write(f"{r['qid']}\t{r['subj']}\t{r['ca']}\t{qt}\t{g_text}\t{s_text}\n")
    print(f"\n[saved] {out_path}")


if __name__ == "__main__":
    main()
