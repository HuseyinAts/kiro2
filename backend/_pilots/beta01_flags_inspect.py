#!/usr/bin/env python3
"""Inspect each flagged question content + image_url + quality_review_status."""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text

OUT = Path(__file__).parent / "beta01_flags_INSPECT.md"
eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Flag pairs (question_id, flag_type, note)
flags = [
    ("7c49c4d7-dfd3-5c85-b3ca-8912efa30c31", "other", "LaTeX \\frac + topic mismatch"),
    ("4da43c90-fdc3-501b-8c0c-7ba0d48911ba", "other", "Görsel eksik"),
    ("6f8427a9-c954-5812-ae27-06a4a283640e", "other", "Görsel eksik"),
    ("38261f49-b60b-5bc9-8b76-718d4e0dd16c", "wrong_answer", "Cevap yanlış"),
    ("a2b9c7b0-05ad-5470-8b3f-4fe6878b9654", "incomplete_text", "Metin eksik"),
    ("9b8f9859-adcc-5aab-bcc0-389f614be3bb", "other", "Görsel eksik"),
    ("514d85e1-3f4e-5bee-b6ce-11e3a8d13326", "other", "Görsel eksik"),
    ("d93e70d9-0cea-517b-ae57-ddb2e317935e", "other", "Görsel eksik"),
    ("04de6419-bc19-5bc3-a287-c384b6e52278", "other", "Görsel eksik"),
    ("4dcbf9ae-9999-54ee-ad56-7e01bea0f279", "other", "Görsel eksik"),
    ("dfc45dd7-a159-5637-a009-ca38d8ed3298", "other", "Görsel eksik"),
    ("616813f6-537d-5f8b-a4ff-1561ac409898", "other", "Metin düzensiz"),
    ("d914f415-6b4f-554b-88a4-189da491d41d", "other", "Metin düzensiz"),
    ("07a87ff6-8f4b-5ec0-996e-1387289b7923", "other", "Görsel eksik"),
    ("cfd8b64f-4ef7-5ae6-af6a-61a79254b5e4", "incomplete_text", "Metin eksik"),
]

lines = ["# Beta01 Flag'lenen Sorular — Gerçek İçerik İncelemesi\n"]
lines.append(f"**Toplam:** {len(flags)} soru (smoke testleri hariç)\n")

with eng.connect() as c:
    for qid, ftype, note in flags:
        row = c.execute(
            text(
                "SELECT id::text, question_text, question_image_url, subject_area, "
                "  source_book, quality_review_status, correct_answer, "
                "  option_a, option_b, option_c, option_d, option_e "
                "FROM question_bank WHERE id::text = :qid"
            ),
            {"qid": qid},
        ).fetchone()

        if not row:
            lines.append(f"\n## ⚠️ Soru bulunamadı: `{qid}`\n")
            continue

        lines.append(f"\n## 🚩 `{qid[:8]}` — {ftype}: {note}\n")
        lines.append(f"- **Status:** `{row.quality_review_status}`")
        lines.append(f"- **Subject:** {row.subject_area}")
        lines.append(f"- **Book:** {row.source_book}")
        lines.append(f"- **Correct:** {row.correct_answer}")
        lines.append(f"- **Image URL:** `{row.question_image_url}`")
        qt = (row.question_text or "").replace("\n", " ")[:500]
        lines.append(f"- **Text:** {qt}")
        lines.append(f"- **A:** {(row.option_a or '')[:80]}")
        lines.append(f"- **B:** {(row.option_b or '')[:80]}")
        lines.append(f"- **C:** {(row.option_c or '')[:80]}")
        lines.append(f"- **D:** {(row.option_d or '')[:80]}")
        lines.append(f"- **E:** {(row.option_e or '')[:80]}")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Written: {OUT}")
