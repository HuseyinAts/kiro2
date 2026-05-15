#!/usr/bin/env python3
"""
Faz 1.8 SymPy Symbolic Math Verifier — Iskelet (skeleton).

PURPOSE:
  Math soruları sembolik olarak doğrula. LLM judge'a alternatif/tamamlayıcı
  pipeline (Faz 5.8 math-specific judge prerequisite).

SCOPE (iskelet):
  - LaTeX extraction from question_text + options
  - SymPy parse + re-solve (simple algebra)
  - Compare with correct_answer choice
  - Output: PASS / FAIL / UNPARSEABLE / NO_MATH / NO_OPTIONS

NOT IN SCOPE (gelecek versiyonlar):
  - Geometri (şekil-bağımlı, SymPy yetersiz)
  - Trigonometri (kısmen — basit identity'ler hariç)
  - Sözel matematik (problem hikayesi → denklem çevirimi, LLM gerek)

DEPENDENCIES:
  - sympy >= 1.13
  - antlr4-python3-runtime == 4.11 (LaTeX parse için ZORUNLU — sympy 1.13
    bu spesifik sürümü istiyor. Mevcut sistemde farklı sürüm kuruluysa
    parse_latex() ImportError fırlatır, tüm satırlar UNPARSEABLE döner.)
  - Install: pip install antlr4-python3-runtime==4.11

USAGE:
  python backend/scripts/sympy_verifier.py --sample-size 5     # quick test
  python backend/scripts/sympy_verifier.py --subject MATEMATIK # subject filter
  python backend/scripts/sympy_verifier.py --id <uuid>         # single
  python backend/scripts/sympy_verifier.py --dry-run           # no DB write

OUTPUT:
  backend/_pilots/sympy_verifier_<date>_RESULT.tsv
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"

# LaTeX inline math: $...$ or $$...$$
LATEX_INLINE = re.compile(r"\$([^$]+?)\$")
LATEX_DISPLAY = re.compile(r"\$\$([^$]+?)\$\$")


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def extract_latex(text: str) -> list[str]:
    """Question text'ten LaTeX inline + display math expressions."""
    if not text:
        return []
    return LATEX_DISPLAY.findall(text) + LATEX_INLINE.findall(text)


def try_parse_latex(expr: str):
    """SymPy parse_latex try/except wrapper. None if fails."""
    try:
        from sympy.parsing.latex import parse_latex

        return parse_latex(expr)
    except Exception:
        return None


def try_eval_numeric(sympy_expr) -> float | None:
    """SymPy expression → numeric float. None if symbolic-only or error."""
    try:
        val = sympy_expr.evalf()
        return float(val)
    except Exception:
        return None


def verify_row(row: dict) -> dict:
    """
    Verify a single question.

    Returns dict: {verdict, details, parsed_q, parsed_opts, eval_q, eval_opts}
    """
    q_text = row.get("question_text") or ""
    options = row.get("options") or []
    correct = (row.get("correct_answer") or "").strip().upper()

    if correct not in {"A", "B", "C", "D", "E"}:
        return {"verdict": "NO_ANSWER", "details": f"correct_answer={correct!r}"}

    if not any(options):
        return {"verdict": "NO_OPTIONS", "details": "all options empty"}

    # Extract LaTeX from question + options
    q_latex = extract_latex(q_text)
    opt_latex = [extract_latex(o or "") for o in options]

    if not q_latex and not any(opt_latex):
        return {"verdict": "NO_MATH", "details": "no LaTeX inline math"}

    # Try parse question LaTeX (use last expression — usually the equation)
    parsed_q = None
    for expr in q_latex[::-1]:
        parsed_q = try_parse_latex(expr)
        if parsed_q is not None:
            break

    # Parse option LaTeX (use first for each)
    parsed_opts = []
    for opt_exprs in opt_latex:
        po = None
        for e in opt_exprs:
            po = try_parse_latex(e)
            if po is not None:
                break
        parsed_opts.append(po)

    if parsed_q is None and not any(parsed_opts):
        return {"verdict": "UNPARSEABLE", "details": "neither q nor opts parsed"}

    # Strategy 1: options are numeric, question evaluable → match index
    eval_opts = [try_eval_numeric(p) if p is not None else None for p in parsed_opts]
    eval_q = try_eval_numeric(parsed_q) if parsed_q is not None else None

    if eval_q is not None and any(v is not None for v in eval_opts):
        # Find which option matches eval_q
        matches = []
        for i, v in enumerate(eval_opts):
            if v is None:
                continue
            if abs(eval_q - v) < 1e-6:
                matches.append("ABCDE"[i])
        if len(matches) == 1:
            ok = matches[0] == correct
            return {
                "verdict": "PASS" if ok else "FAIL",
                "details": f"computed={eval_q:.4f} → option {matches[0]}, expected {correct}",
                "eval_q": eval_q,
                "eval_opts": eval_opts,
            }
        if len(matches) > 1:
            return {
                "verdict": "AMBIGUOUS",
                "details": f"eval_q={eval_q:.4f} matches multiple: {matches}",
            }

    # Strategy 2: option = expression equivalent to question (algebraic)
    if parsed_q is not None:
        from sympy import simplify

        matches = []
        for i, po in enumerate(parsed_opts):
            if po is None:
                continue
            try:
                if simplify(parsed_q - po) == 0:
                    matches.append("ABCDE"[i])
            except Exception:
                continue
        if len(matches) == 1:
            ok = matches[0] == correct
            return {
                "verdict": "PASS" if ok else "FAIL",
                "details": f"symbolic match → option {matches[0]}, expected {correct}",
            }

    return {
        "verdict": "INCONCLUSIVE",
        "details": f"eval_q={eval_q}, no unique option match",
    }


def fetch_samples(engine, sample_size: int, subject: str | None, qid: str | None):
    from sqlalchemy import text

    with engine.connect() as conn:
        if qid:
            sql = """
            SELECT id::text, question_text, option_a, option_b, option_c,
                   option_d, option_e, correct_answer, subject_area
            FROM question_bank WHERE id::text = :qid
            """
            params = {"qid": qid}
        else:
            sql = """
            SELECT id::text, question_text, option_a, option_b, option_c,
                   option_d, option_e, correct_answer, subject_area
            FROM question_bank
            WHERE is_active = TRUE
              AND quality_review_status = 'unverified'
              AND question_text ~ '\\$'
            """
            params = {}
            if subject:
                sql += " AND subject_area = :subj"
                params["subj"] = subject
            sql += " ORDER BY md5(id::text || 'verifier_seed') LIMIT :n"
            params["n"] = sample_size
        rows = conn.execute(text(sql), params).fetchall()
    return [
        {
            "id": r[0],
            "question_text": r[1],
            "options": [r[2], r[3], r[4], r[5], r[6]],
            "correct_answer": r[7],
            "subject_area": r[8],
        }
        for r in rows
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-size", type=int, default=5)
    ap.add_argument("--subject", type=str, default="MATEMATIK")
    ap.add_argument("--id", type=str, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    engine = get_engine()
    rows = fetch_samples(engine, args.sample_size, args.subject, args.id)
    if not rows:
        print("[error] No matching rows")
        return 1
    print(f"[fetch] {len(rows)} satır (subject={args.subject})")

    stats = {
        "PASS": 0,
        "FAIL": 0,
        "UNPARSEABLE": 0,
        "NO_MATH": 0,
        "NO_OPTIONS": 0,
        "NO_ANSWER": 0,
        "AMBIGUOUS": 0,
        "INCONCLUSIVE": 0,
    }
    results = []
    for r in rows:
        v = verify_row(r)
        stats[v["verdict"]] = stats.get(v["verdict"], 0) + 1
        results.append({**r, **v})
        print(f"  {r['id'][:8]} | {v['verdict']:13s} | {v['details'][:80]}")

    print(f"\n[summary] (n={len(rows)})")
    for k, c in sorted(stats.items(), key=lambda x: -x[1]):
        if c > 0:
            print(f"  {k:13s}: {c:>3} ({100 * c / len(rows):.1f}%)")

    out_path = (
        PILOTS_DIR
        / f"sympy_verifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}_RESULT.tsv"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("id\tsubject\tverdict\tdetails\tq_text_preview\tcorrect\n")
        for r in results:
            q = (r["question_text"] or "")[:120].replace("\t", " ").replace("\n", " ")
            f.write(
                f"{r['id']}\t{r['subject_area']}\t{r['verdict']}\t"
                f"{r['details'][:200].replace(chr(9), ' ')}\t{q}\t{r['correct_answer']}\n"
            )
    print(f"\n[output] {out_path}")
    print(
        "\n[note] Iskelet seviyesi — strategy 1 (numeric match) + 2 (symbolic equiv)."
    )
    print("       Coverage analizi: NO_MATH + UNPARSEABLE + INCONCLUSIVE = scope dışı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
