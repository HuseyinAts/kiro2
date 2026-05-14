#!/usr/bin/env python3
"""
Faz 1.10 Cut-off Detector — DB question_text cut-off (kesik) tespiti.

Pilot 30 sample'a dayanan kurallar:
  CUT-OFF kabul edilen pattern'ler:
    1. Sonu noktalama degil (?.!)] vb.)
    2. Sonu Turkce soru tamamlayicilarindan biri DEGIL
    3. LaTeX $ sayisi tek (yarim formul)
    4. Toplam kelime sayisi < 6 (cok kisa)
    5. Sonu virgul (',') + soru kelimesi yok
  TAM kabul edilen pattern'ler:
    - Sonu noktalama VEYA soru pattern (kactir?, nedir?, vs.)

Cikti: backend/_pilots/20260516_cutoff_detection_RESULT.{tsv,md}
       - cutoff_yes: Re-OCR adayi
       - cutoff_no:  DB korunur
       - cutoff_unclear: manuel review
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
TSV_OUT = OUT_DIR / "20260516_cutoff_detection_RESULT.tsv"
MD_OUT = OUT_DIR / "20260516_cutoff_detection_RESULT.md"

# Turkce soru tamamlayicilari (son ~50 char icinde aranir)
QUESTION_ENDINGS = [
    "kactir",
    "kaçtır",
    "kaç",
    "kac",
    "nedir",
    "midir",
    "mıdır",
    "dır",
    "dır?",
    "değildir",
    "degildir",
    "tir",
    "tır",
    "tur",
    "tür",
    "hangisidir",
    "hangisi",
    "hangileri",
    "esittir",
    "eşittir",
    "neye eşit",
    "neye esit",
    "kac tane",
    "kaç tane",
    "kac cm",
    "kaç cm",
    "kac derece",
    "kaç derece",
    "kac birim",
    "kaç birim",
    "asagidakilerden",
    "aşağıdakilerden",
    "ifadesi",
    "olabilir",
    "dir.",
    "tır.",
    "tir.",
]

VALID_END_CHARS = set("?.!»\"')]”’")  # cumle sonu noktalama (Latex } dahil edilmedi)


def is_cutoff(text: str) -> tuple[str, str]:
    """Returns (verdict, reason). verdict: 'cutoff'|'ok'|'unclear'"""
    if not text:
        return "cutoff", "empty"
    text_strip = text.strip()
    if len(text_strip) < 10:
        return "cutoff", "too_short"

    word_count = len(text_strip.split())
    if word_count < 5:
        return "cutoff", "few_words"

    last_char = text_strip[-1]
    end_window = text_strip[-50:].lower()

    # LaTeX yarim formul (tek sayida $)
    dollar_count = text_strip.count("$")
    if dollar_count % 2 != 0:
        return "cutoff", "latex_odd_dollar"

    # Sonu gecerli noktalama
    if last_char in VALID_END_CHARS:
        # Ama virgul'le bitiyor olabilir (test)
        return "ok", f"valid_end_{last_char}"

    # Sonu virgul/noktasiz: soru pattern var mi?
    if any(ending in end_window for ending in QUESTION_ENDINGS):
        return "ok", "has_question_ending"

    # Sonu noktalama yok + soru pattern yok = cut-off
    if last_char == ",":
        return "cutoff", "ends_with_comma"

    # Sonu harf veya rakam, soru pattern yok
    if last_char.isalnum():
        return "cutoff", "alphanumeric_end"

    return "unclear", f"unknown_end_{last_char}"


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def main():
    from sqlalchemy import text

    engine = get_engine()
    print("[db] missing rows fetch...", flush=True)
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT id, source_book, source_page, question_text,
                   LENGTH(question_text) AS text_len,
                   pipeline_metadata->'ai_extras'->>'q_no' AS q_no
            FROM question_bank
            WHERE is_active = TRUE
              AND question_image_url IS NULL
              AND (pipeline_metadata->'ai_extras'->>'has_diagram')::boolean = TRUE
        """)
        ).fetchall()
    print(f"[db] {len(rows):,} satir cekildi", flush=True)

    verdict_counts = Counter()
    reason_counts = Counter()
    results = []

    for row in rows:
        id_, book, page, qtext, text_len, q_no = row
        verdict, reason = is_cutoff(qtext or "")
        verdict_counts[verdict] += 1
        reason_counts[reason] += 1
        results.append(
            {
                "id": id_,
                "book": book,
                "page": page,
                "q_no": q_no,
                "text_len": text_len,
                "verdict": verdict,
                "reason": reason,
                "preview": (qtext or "")[-80:].replace("\t", " ").replace("\n", " "),
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(TSV_OUT, "w", encoding="utf-8") as f:
        f.write("id\tbook\tpage\tq_no\ttext_len\tverdict\treason\ttext_end_80char\n")
        for r in results:
            f.write(
                f"{r['id']}\t{r['book']}\t{r['page']}\t{r['q_no']}\t{r['text_len']}\t"
                f"{r['verdict']}\t{r['reason']}\t{r['preview']}\n"
            )

    total = sum(verdict_counts.values())
    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("# Cut-off Detection — 16 May 2026\n\n")
        f.write(f"**Total satır**: {total:,}\n\n")
        f.write("## Verdict Dağılımı\n\n")
        f.write("| Verdict | Count | % | Aksiyon |\n|---|---|---|---|\n")
        actions = {
            "cutoff": "→ Re-OCR adayı",
            "ok": "→ DB korunur, Re-OCR yapılmaz",
            "unclear": "→ Manuel review veya Re-OCR ile sample",
        }
        for v, c in verdict_counts.most_common():
            pct = c * 100 / total if total else 0
            f.write(f"| `{v}` | {c:,} | %{pct:.1f} | {actions.get(v, '?')} |\n")
        f.write("\n## Reason Dağılımı\n\n| Reason | Count |\n|---|---|\n")
        for r, c in reason_counts.most_common(15):
            f.write(f"| `{r}` | {c:,} |\n")

    print("\n=== VERDICTS ===")
    for v, c in verdict_counts.most_common():
        pct = c * 100 / total if total else 0
        print(f"  {v:10s} {c:5d} (%{pct:.1f})")
    print("\n=== TOP REASONS ===")
    for r, c in reason_counts.most_common(10):
        print(f"  {r:30s} {c}")
    print(f"\nTSV: {TSV_OUT}")
    print(f"MD:  {MD_OUT}")


if __name__ == "__main__":
    main()
