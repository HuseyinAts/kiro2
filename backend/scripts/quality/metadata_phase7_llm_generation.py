#!/usr/bin/env python3
"""
Phase 7: LLM-dependent metadata via Ollama (Qwen3-8B local).

Generates per question:
  - rationale_per_option (5 rationales, A-E)
  - misconception_tags (1-3 tags for wrong answers)
  - solution_steps (numbered steps)
  - solo_level, marzano_level (taxonomy classifications)
  - expected_answer_formula (SymPy expression for math)
  - is_math_solvable (bool)

Single-prompt strategy: one call returns JSON with all metadata.
Cost: $0 (local Ollama) but slow (~30sec/question on CPU).

Resume support: skip rows where rationale already populated.
"""

import argparse
import json
import os
import sys
import time
import urllib.request

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

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
  "solo_level": "unistructural | multistructural | relational | extended_abstract",
  "marzano_level": "retrieval | comprehension | analysis | knowledge_utilization | metacognitive",
  "expected_answer_formula": "Eğer matematik sorusu ise SymPy uyumlu sembolik ifade (örn: 'x**2 + 3*x - 4'), değilse null",
  "is_math_solvable": true_veya_false
}}"""


def ollama_generate(prompt, timeout=120):
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
    """Parse LLM JSON response, with fallback for malformed."""
    text = text.strip()
    # Find JSON block
    if "{" in text and "}" in text:
        start = text.index("{")
        end = text.rindex("}") + 1
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="Max questions to process")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--gold-only",
        action="store_true",
        help="Filter to R4_rule_based_gold (beta-eligible) only",
    )
    args = ap.parse_args()

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    gold_filter = (
        "AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'"
        if args.gold_only
        else ""
    )
    # Resume: skip rows already having rationale
    cur.execute(
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
    rows = cur.fetchall()
    print(f"[scan] {len(rows):,} rows to process via {MODEL}\n")

    success = 0
    failed = 0
    t_start = time.time()

    for i, r in enumerate(rows, 1):
        qid, qt, oa, ob, oc, od, oe, ca, subj, exam, diff, bloom = r

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
            parsed = parse_llm_response(raw)
            if not parsed or not parsed.get("rationales"):
                failed += 1
                if failed <= 3:
                    print(
                        f"  [{i}] parse fail for {qid[:8]} - raw={raw[:200]!r}",
                        flush=True,
                    )
                continue
        except Exception as e:
            failed += 1
            print(f"  [{i}] ollama error: {e}", flush=True)
            continue

        # Validate + extract
        rationales = parsed.get("rationales", {}) or {}
        misconception = parsed.get("misconception_tags", []) or []
        solution = parsed.get("solution_steps", []) or []
        solo = parsed.get("solo_level")
        marzano = parsed.get("marzano_level")
        formula = parsed.get("expected_answer_formula")
        is_math = bool(parsed.get("is_math_solvable", False))

        if args.apply:
            try:
                # Insert rationales
                for letter in "ABCDE":
                    rtxt = rationales.get(letter)
                    if rtxt:
                        cur.execute(
                            """
                            INSERT INTO question_option_rationales
                              (question_id, option_letter, rationale, is_correct, generated_by, generated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (question_id, option_letter)
                              DO UPDATE SET rationale = EXCLUDED.rationale, generated_at = NOW()
                        """,
                            (qid, letter, rtxt[:1000], letter == ca, MODEL),
                        )

                # Update question_bank
                cur.execute(
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
                    (
                        json.dumps(misconception, ensure_ascii=False)
                        if misconception
                        else None,
                        json.dumps(solution, ensure_ascii=False) if solution else None,
                        solo,
                        marzano,
                        formula,
                        is_math,
                        qid,
                    ),
                )

                # Insert into question_math if math
                if is_math and formula:
                    cur.execute(
                        """
                        INSERT INTO question_math
                          (question_id, expected_answer_sympy, is_symbolic_verifiable, created_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (question_id)
                          DO UPDATE SET expected_answer_sympy = EXCLUDED.expected_answer_sympy
                    """,
                        (qid, formula[:500], True),
                    )

                conn.commit()
                success += 1
            except Exception as e:
                conn.rollback()
                failed += 1
                print(f"  [{i}] db error for {qid[:8]}: {e}", flush=True)
                continue

        if i % 5 == 0:
            elapsed = time.time() - t_start
            rate = i / elapsed * 60
            print(
                f"  [{i}/{len(rows)}] success={success} failed={failed} rate={rate:.1f}/min",
                flush=True,
            )

    elapsed = time.time() - t_start
    print(
        f"\n[done] processed {len(rows)} | success={success} failed={failed} | total time={elapsed / 60:.1f}min"
    )
    conn.close()


if __name__ == "__main__":
    main()
