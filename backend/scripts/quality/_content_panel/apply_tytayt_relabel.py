"""TYT->AYT relabel: 748 doğrulanmış AYT-seviye soru (exam_type düzeltme).

Reversible: backup + exam_type='AYT' + metadata marker. İçerik/cevap DOKUNULMAZ.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = Path("scripts/quality/_content_panel")
BACKUP = "question_bank_tytayt_relabel_backup_20260703"
MARKER = "tytayt_relabel_20260703"
ids = json.loads((P / "ayt_relabel_ids.json").read_text(encoding="utf-8"))
print(f"relabel aday: {len(ids)}")

load_dotenv(".env")
raw = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(make_url(raw).set(host="localhost", port=5434, database="kiro2"))

with engine.begin() as c:
    # spot-check 3
    print("--- spot-check (3) ---")
    for r in c.execute(
        text(
            "SELECT subject_area, exam_type, left(question_text,100) FROM question_bank "
            "WHERE id = ANY(:i) LIMIT 3"
        ),
        {"i": ids[:3]},
    ):
        print(f"  [{r[0]}] mevcut={r[1]} :: {r[2]}")

    # sadece gerçekten TYT olanları relabel et (idempotent guard)
    cur_tyt = c.execute(
        text(
            "SELECT count(*) FROM question_bank WHERE id = ANY(:i) AND exam_type='TYT'"
        ),
        {"i": ids},
    ).scalar()
    print(f"\nşu an TYT etiketli (relabel edilecek): {cur_tyt}/{len(ids)}")

    c.execute(text(f"DROP TABLE IF EXISTS {BACKUP}"))
    c.execute(
        text(
            f"CREATE TABLE {BACKUP} AS SELECT * FROM question_bank WHERE id = ANY(:i)"
        ),
        {"i": ids},
    )
    print(
        f"backup {BACKUP}: {c.execute(text(f'SELECT count(*) FROM {BACKUP}')).scalar()} satır"
    )

    res = c.execute(
        text(
            "UPDATE question_bank SET exam_type='AYT', "
            "pipeline_metadata = COALESCE(pipeline_metadata::jsonb,'{}'::jsonb) || jsonb_build_object(:mk, true) "
            "WHERE id = ANY(:i) AND exam_type='TYT'"
        ),
        {"i": ids, "mk": MARKER},
    )
    print(f"UPDATE edilen: {res.rowcount}")

    # yeni v_safe exam_type dağılımı
    print("\n=== yeni v_safe exam_type dağılımı ===")
    for r in c.execute(
        text(
            "SELECT exam_type, count(*) FROM question_bank WHERE id IN (SELECT id FROM v_safe_for_beta) "
            "GROUP BY exam_type ORDER BY 2 DESC"
        )
    ):
        print(f"  {r[0]}: {r[1]}")

print(
    f"\nGeri alma: UPDATE question_bank q SET exam_type=b.exam_type, pipeline_metadata=b.pipeline_metadata "
    f"FROM {BACKUP} b WHERE q.id=b.id;"
)
