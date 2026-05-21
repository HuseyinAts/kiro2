#!/usr/bin/env python3
"""
Phase 7 kalite spot-check: 50 random sample'ı analiz et.

Metrikler:
- Schema completeness (5 rationale + misconception + solution)
- Turkish char ratio (NFC normalized)
- English bleed (yabanci kelime sızması)
- Self-contradiction patterns ("dogru ama yanlis", "yanlis ama dogru" vb.)
- Rationale length distribution
- Correct option rationale check (DOGRU answer rationale-i "yanlis" demiyor mu)

Output:
- Aggregate metrics console'a
- TSV: 20260521_phase7_spot_check_RAW.tsv (manuel review için)
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = "postgresql://postgres:1470@localhost:5434/kiro2"
SAMPLE_N = 50
THIS_DIR = Path(__file__).resolve().parent

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
    "option",
    "result",
    "value",
}
CONTRADICTION_PATTERNS = [
    (
        r"\b(doğru|dogru)\b.{0,30}\b(ama|fakat|lakin|ancak)\b.{0,30}\b(yanlış|yanlis)\b",
        "dogru_ama_yanlis",
    ),
    (
        r"\b(yanlış|yanlis)\b.{0,30}\b(ama|fakat|lakin|ancak)\b.{0,30}\b(doğru|dogru)\b",
        "yanlis_ama_dogru",
    ),
    (
        r"\b(yalnız|yalniz)\s+(I+|II+|III+|IV)\b.{0,80}\byalnız\s+(I+|II+|III+|IV)\b",
        "yalniz_celisik",
    ),
    (r"hem.{0,30}hem.{0,30}(yanlış|yanlis)", "hem_hem_celisik"),
]


def normalize_tr(t):
    if not t:
        return ""
    return unicodedata.normalize("NFC", t).lower()


def score_rationale(text, is_correct):
    """Tek bir rationale satırının kalite skorunu çıkar."""
    s = {
        "len_chars": len(text or ""),
        "tr_char_ratio": 0.0,
        "english_bleed": 0,
        "contradictions": [],
        "starts_correctly": False,
    }
    if not text:
        return s
    norm = normalize_tr(text)
    s["tr_char_ratio"] = sum(1 for c in text if c in TURKISH_CHARS) / max(len(text), 1)
    s["english_bleed"] = sum(
        1 for w in ENGLISH_BLEED_WORDS if re.search(rf"\b{re.escape(w)}\b", norm)
    )
    for pattern, name in CONTRADICTION_PATTERNS:
        if re.search(pattern, norm):
            s["contradictions"].append(name)
    # Correct option should NOT start with "yanlış" or "yanli"
    if is_correct and (norm.startswith("yanlış") or norm.startswith("yanlis")):
        s["starts_correctly"] = False
    elif not is_correct and (norm.startswith("yanlış") or norm.startswith("yanlis")):
        s["starts_correctly"] = True
    else:
        s["starts_correctly"] = True  # Neutral start, accept
    return s


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT q.id::text, q.subject_area, q.correct_answer, q.question_text,
               q.misconception_tags::text, q.solution_steps::text, q.solo_level,
               q.marzano_level, q.expected_answer_formula,
               json_agg(json_build_object(
                 'letter', r.option_letter,
                 'rationale', r.rationale,
                 'is_correct', r.is_correct
               ) ORDER BY r.option_letter) AS rationales
        FROM question_bank q
        INNER JOIN question_option_rationales r ON r.question_id = q.id::text
        WHERE q.is_active
          AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
          AND r.generated_by = 'gemini-flash-latest'
        GROUP BY q.id
        ORDER BY md5(q.id::text)
        LIMIT %s
        """,
        (SAMPLE_N,),
    )
    rows = cur.fetchall()
    conn.close()
    print(f"[spot-check] {len(rows)} sample loaded")

    # Aggregate metrics
    agg = {
        "n_samples": len(rows),
        "schema_complete": 0,
        "all_5_rationales": 0,
        "has_misconception": 0,
        "has_solution": 0,
        "has_formula_math": 0,
        "contradiction_count": 0,
        "samples_with_contradiction": 0,
        "english_bleed_count": 0,
        "samples_with_eng_bleed": 0,
        "avg_rationale_len": 0,
        "correct_rationale_negates": 0,  # DOGRU cevap "yanlış" diye başlıyor mu
    }
    contradiction_samples = []
    eng_bleed_samples = []
    weird_samples = []
    all_lens = []

    tsv_rows = []

    for row in rows:
        qid, subj, ca, qt, miscon, sol, solo, marzano, formula, rats = row
        has_5 = len(rats) >= 5 and all(r["rationale"] for r in rats)
        has_misc = miscon is not None and miscon != "null"
        has_sol = sol is not None and sol != "null"
        has_form = formula is not None and formula != ""
        if has_5 and has_misc and has_sol:
            agg["schema_complete"] += 1
        if has_5:
            agg["all_5_rationales"] += 1
        if has_misc:
            agg["has_misconception"] += 1
        if has_sol:
            agg["has_solution"] += 1
        if has_form:
            agg["has_formula_math"] += 1

        sample_contradictions = []
        sample_bleed = 0
        for rat in rats:
            letter = rat["letter"]
            text = rat["rationale"] or ""
            is_correct = letter == ca
            sc = score_rationale(text, is_correct)
            all_lens.append(sc["len_chars"])
            if sc["contradictions"]:
                sample_contradictions.extend(sc["contradictions"])
                agg["contradiction_count"] += len(sc["contradictions"])
            sample_bleed += sc["english_bleed"]
            if is_correct and not sc["starts_correctly"]:
                agg["correct_rationale_negates"] += 1
                weird_samples.append((qid, subj, letter, text[:100]))

        if sample_contradictions:
            agg["samples_with_contradiction"] += 1
            contradiction_samples.append((qid, subj, sample_contradictions))
        if sample_bleed > 0:
            agg["english_bleed_count"] += sample_bleed
            agg["samples_with_eng_bleed"] += 1
            eng_bleed_samples.append((qid, subj, sample_bleed))

        # TSV row
        rat_compact = " | ".join(
            f"{r['letter']}{'✓' if r['letter'] == ca else ''}: {(r['rationale'] or '')[:120]}"
            for r in rats
        )
        tsv_rows.append(
            {
                "qid": qid[:8],
                "subj": subj,
                "correct": ca,
                "qt": (qt or "")[:150].replace("\t", " ").replace("\n", " "),
                "rationales": rat_compact.replace("\t", " ").replace("\n", " "),
                "misconception": (miscon or "")[:200]
                .replace("\t", " ")
                .replace("\n", " "),
                "solution": (sol or "")[:300].replace("\t", " ").replace("\n", " "),
                "solo": solo or "",
                "marzano": marzano or "",
                "formula": (formula or "")[:100],
            }
        )

    agg["avg_rationale_len"] = sum(all_lens) // max(len(all_lens), 1)

    # Print aggregate
    print("\n" + "=" * 72)
    print("AGGREGATE METRICS (n=" + str(agg["n_samples"]) + ")")
    print("=" * 72)
    pct = lambda v: f"{v}/{agg['n_samples']} ({v / agg['n_samples'] * 100:.0f}%)"
    print(f"  Schema complete (5 rat+miscon+sol)   : {pct(agg['schema_complete'])}")
    print(f"  All 5 rationales                     : {pct(agg['all_5_rationales'])}")
    print(f"  Has misconception_tags               : {pct(agg['has_misconception'])}")
    print(f"  Has solution_steps                   : {pct(agg['has_solution'])}")
    print(f"  Has expected_answer_formula (math)   : {pct(agg['has_formula_math'])}")
    print()
    print(
        f"  Samples with contradictions          : {pct(agg['samples_with_contradiction'])}"
    )
    print(f"  Total contradiction patterns         : {agg['contradiction_count']}")
    print(
        f"  Samples with English bleed           : {pct(agg['samples_with_eng_bleed'])}"
    )
    print(f"  Total English bleed occurrences      : {agg['english_bleed_count']}")
    print(
        f"  Correct option starts with 'yanlış'  : {agg['correct_rationale_negates']} ⚠️"
    )
    print(f"  Avg rationale length                 : {agg['avg_rationale_len']} chars")

    if contradiction_samples:
        print("\n--- Contradiction samples (first 5) ---")
        for qid, subj, pats in contradiction_samples[:5]:
            print(f"  {qid[:8]} [{subj}]: {pats}")

    if weird_samples:
        print("\n--- Weird: correct option starts 'yanlış' (first 5) ---")
        for qid, subj, letter, text in weird_samples[:5]:
            print(f"  {qid[:8]} [{subj}] opt={letter}: {text!r}")

    # Write TSV
    out_path = THIS_DIR / "20260521_phase7_spot_check_RAW.tsv"
    with out_path.open("w", encoding="utf-8") as f:
        fields = [
            "qid",
            "subj",
            "correct",
            "qt",
            "rationales",
            "misconception",
            "solution",
            "solo",
            "marzano",
            "formula",
        ]
        f.write("\t".join(fields) + "\n")
        for r in tsv_rows:
            f.write("\t".join(str(r[k]) for k in fields) + "\n")
    print(f"\n[saved] {out_path}")
    print("[saved] aggregate report")


if __name__ == "__main__":
    main()
