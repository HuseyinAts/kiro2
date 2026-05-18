#!/usr/bin/env python3
"""
Beta01 (Faz 7.1 manual beta) — flag'lenen 15 soruyu DB'de resolve et.

Aksiyon:
  1. flag'lenen soruyu quality_review_status='rejected' yap
  2. pipeline_metadata.beta_feedback_v1 audit trail ekle
  3. student_question_flags'de resolved_at + resolution + resolved_by doldur

Kategori dağılımı (beta01, 18-19 May 2026):
  9× image-bound (frontend image render disabled — kullanılamaz)
  1× wrong_answer (math doğrulanır: 38261f49)
  2× incomplete_text (numaralı işaret eksik)
  2× düzensiz metin (paragraf yarıda)
  1× LaTeX render bug (opsiyonlarda \frac raw — soru OK ama UI render bug)

USAGE:
  python backend/scripts/quality/beta_flag_resolver.py --dry-run
  python backend/scripts/quality/beta_flag_resolver.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")

# (question_id, category, note) — beta01 18 flag'inden gerçek 15 (smoke 3 hariç)
FLAGS = [
    # 9× image-bound (frontend Bug #11 fix image render suppress; bu sorular
    # image olmadan çözülemez ama image gösterilmiyor → pool'dan çıkar)
    ("4da43c90-fdc3-501b-8c0c-7ba0d48911ba", "image_bound", "FIZIK görsel"),
    ("6f8427a9-c954-5812-ae27-06a4a283640e", "image_bound", "Şema"),
    ("9b8f9859-adcc-5aab-bcc0-389f614be3bb", "image_bound", "Numaralı liste görsel"),
    ("514d85e1-3f4e-5bee-b6ce-11e3a8d13326", "image_bound", "Deney düzeneği"),
    ("d93e70d9-0cea-517b-ae57-ddb2e317935e", "image_bound", "ABCD paralelkenar"),
    ("04de6419-bc19-5bc3-a287-c384b6e52278", "image_bound", "Numaralı özellik"),
    ("4dcbf9ae-9999-54ee-ad56-7e01bea0f279", "image_bound", "ABCD paralelkenar"),
    ("dfc45dd7-a159-5637-a009-ca38d8ed3298", "image_bound", "Kavram haritası"),
    ("07a87ff6-8f4b-5ec0-996e-1387289b7923", "image_bound", "Şekildeki kaplar"),
    # 1× wrong_answer (matematik doğrulanır → DB cevabı yanlış)
    (
        "38261f49-b60b-5bc9-8b76-718d4e0dd16c",
        "wrong_answer",
        "x*(1/3)*(1/2)=12 → x=72=A, DB:E",
    ),
    # 2× incomplete_text (numaralı işaret eksik metin)
    (
        "a2b9c7b0-05ad-5470-8b3f-4fe6878b9654",
        "incomplete_text",
        "Numaralı sözcük eksik",
    ),
    (
        "cfd8b64f-4ef7-5ae6-af6a-61a79254b5e4",
        "incomplete_text",
        "Numaralı sözcük eksik",
    ),
    # 2× düzensiz metin
    ("616813f6-537d-5f8b-a4ff-1561ac409898", "broken_text", "Paragraf III yarıda"),
    ("d914f415-6b4f-554b-88a4-189da491d41d", "broken_text", "Reflow"),
    # 1× LaTeX render bug (soru content OK ama frontend opt render bug)
    ("7c49c4d7-dfd3-5c85-b3ca-8912efa30c31", "latex_render_bug", "Opt \\frac raw"),
]


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("[error] --dry-run veya --apply gerekli")
        return 2

    from sqlalchemy import text

    eng = get_engine()
    mode = "apply" if args.apply else "dryrun"
    today = datetime.now().strftime("%Y%m%d")
    result_md = PILOTS_DIR / f"{today}_beta_flag_resolver_{mode}_RESULT.md"

    audit_obj = {
        "date": AUDIT_DATE,
        "source": "beta01_flag_resolver_v1",
        "beta_user_id": "4ce67404-4a40-46b2-91ba-9659cc3f0e12",
    }
    audit_json = json.dumps(audit_obj)

    print(f"[mode] {mode}")
    print(f"[flags] {len(FLAGS)} soru işlenecek\n")

    counts: dict[str, int] = {"reject": 0, "flag_resolve": 0}

    for qid, category, note in FLAGS:
        # 1. Soruyu rejected yap
        qb_sql = """
            UPDATE question_bank
            SET quality_review_status = 'rejected',
                pipeline_metadata = jsonb_set(
                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                    '{beta_flag_v1}',
                    CAST(:audit AS jsonb) || CAST(:meta AS jsonb),
                    TRUE
                )::json,
                updated_at = NOW()
            WHERE id::text = :qid AND quality_review_status='auto_judged_high'
        """
        meta = json.dumps({"category": category, "note": note})

        # 2. Flag'i resolved işaretle
        flag_sql = """
            UPDATE student_question_flags
            SET resolved_at = NOW(),
                resolution = :resolution,
                resolved_by = 'system_auto'
            WHERE question_id::text = :qid
              AND resolved_at IS NULL
        """
        # check constraint: confirmed | rejected | duplicate
        # confirmed = flag doğruydu (bizim case)
        resolution = "confirmed"

        if args.apply:
            with eng.begin() as c:
                r1 = c.execute(
                    text(qb_sql), {"audit": audit_json, "meta": meta, "qid": qid}
                )
                r2 = c.execute(text(flag_sql), {"resolution": resolution, "qid": qid})
                counts["reject"] += r1.rowcount
                counts["flag_resolve"] += r2.rowcount
                print(
                    f"[apply] {qid[:8]} {category}: reject={r1.rowcount} flag={r2.rowcount}"
                )
        else:
            with eng.connect() as c:
                exists = c.execute(
                    text(
                        "SELECT COUNT(*) FROM question_bank "
                        "WHERE id::text=:qid AND quality_review_status='auto_judged_high'"
                    ),
                    {"qid": qid},
                ).scalar()
                flag_count = c.execute(
                    text(
                        "SELECT COUNT(*) FROM student_question_flags "
                        "WHERE question_id::text=:qid AND resolved_at IS NULL"
                    ),
                    {"qid": qid},
                ).scalar()
                counts["reject"] += exists
                counts["flag_resolve"] += flag_count
                print(
                    f"[dry-run] {qid[:8]} {category}: "
                    f"qb_active={exists} flag_open={flag_count}"
                )

    print(f"\n[total] reject={counts['reject']} flag_resolve={counts['flag_resolve']}")

    # RESULT MD
    lines = [
        f"# Beta Flag Resolver — {mode.upper()} RESULT",
        f"\n**Date:** {AUDIT_DATE}",
        "**Beta user:** beta01@kiro2.com",
        f"**Toplam flag:** {len(FLAGS)} (E2E smoke testi 3 hariç)\n",
        "## Kategori Dağılımı\n",
        "| Kategori | Sayı |\n|---|---|",
        f"| image_bound (frontend image suppress) | {sum(1 for _, c, _ in FLAGS if c == 'image_bound')} |",
        f"| wrong_answer | {sum(1 for _, c, _ in FLAGS if c == 'wrong_answer')} |",
        f"| incomplete_text | {sum(1 for _, c, _ in FLAGS if c == 'incomplete_text')} |",
        f"| broken_text | {sum(1 for _, c, _ in FLAGS if c == 'broken_text')} |",
        f"| latex_render_bug | {sum(1 for _, c, _ in FLAGS if c == 'latex_render_bug')} |",
        "",
        "## Aksiyon Sonuçları\n",
        f"- Rejected: {counts['reject']}",
        f"- Flag resolved: {counts['flag_resolve']}",
        "",
        "## Notes\n",
        "- 9 image_bound soru: Bug #11 fix frontend `question_image_url` suppress eder",
        "  → bu sorular image olmadan çözülemez, pool'dan çıkarıldı.",
        "  Sprint sonrası vision re-crop ile geri kazanılır.",
        "- 1 wrong_answer (`38261f49`): math doğrulanır E=4 yanlış, A=72 doğru.",
        "  Şu an rejected; manuel cevap düzeltmesi sonra (curator).",
        "- 1 latex_render_bug (`7c49c4d7`): opsiyonlarda raw `\\frac` görünüyor.",
        "  Bug #1 fix sadece question_text MathText wrap yaptı, opsiyonlar için",
        "  yapılmamış. Sprint follow-up: ayrı commit.",
    ]
    result_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[result] {result_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
