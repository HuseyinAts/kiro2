"""İçerik paneli P0: doğrulanmış cevap-anahtarı/geçersizlik hatalarını devre dışı bırak.

Reversible: backup tablo + is_active=false + pipeline_metadata marker.
Yalnız 13 adversaryal-doğrulanmış (wrong_answer/no_correct/multiple_correct) ID.
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
BACKUP = "question_bank_content_panel_deact_backup_20260703"
MARKER = "content_panel_deactivated_20260703"

ids = [
    c["id"] for c in json.loads((P / "deactivate_ids.json").read_text(encoding="utf-8"))
]
assert len(ids) == 13, f"beklenen 13, gelen {len(ids)}"

load_dotenv("C:/Users/husey/kiro2/backend/.env")
raw = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(make_url(raw).set(host="localhost", port=5434, database="kiro2"))

with engine.begin() as c:
    # 1) mevcut durum + spot-check (ilk 3)
    rows = c.execute(
        text(
            "SELECT id::text, subject_area, is_active, left(question_text,90) qt, "
            "correct_answer FROM question_bank WHERE id = ANY(:ids)"
        ),
        {"ids": ids},
    ).fetchall()
    print(f"=== DB'de bulunan: {len(rows)}/13 ===")
    active_now = sum(1 for r in rows if r.is_active)
    print(f"şu an is_active=true: {active_now}")
    print("--- spot-check (ilk 3) ---")
    for r in rows[:3]:
        print(
            f"  [{r.subject_area}] key={r.correct_answer} active={r.is_active} :: {r.qt}"
        )

    found = {r.id for r in rows}
    missing = [i for i in ids if i not in found]
    if missing:
        print("UYARI eksik id:", missing)

    # 2) backup (idempotent: varsa drop)
    c.execute(text(f"DROP TABLE IF EXISTS {BACKUP}"))
    c.execute(
        text(
            f"CREATE TABLE {BACKUP} AS SELECT * FROM question_bank WHERE id = ANY(:ids)"
        ),
        {"ids": ids},
    )
    bkc = c.execute(text(f"SELECT count(*) FROM {BACKUP}")).scalar()
    print(f"\n=== backup tablo {BACKUP}: {bkc} satır ===")

    # 3) deaktive et + marker
    res = c.execute(
        text(
            "UPDATE question_bank SET is_active=false, "
            "quality_review_status='rejected', "
            "pipeline_metadata = COALESCE(pipeline_metadata::jsonb,'{}'::jsonb) || "
            "jsonb_build_object(:mk, true) "
            "WHERE id = ANY(:ids) AND is_active=true"
        ),
        {"ids": ids, "mk": MARKER},
    )
    print(f"UPDATE etkilenen satır: {res.rowcount}")

    # 4) doğrula
    still = c.execute(
        text(
            "SELECT count(*) FROM question_bank WHERE id = ANY(:ids) AND is_active=true"
        ),
        {"ids": ids},
    ).scalar()
    vsafe = c.execute(text("SELECT count(*) FROM v_safe_for_beta")).scalar()
    print(f"\n=== SONUÇ: hâlâ aktif {still} (0 olmalı) | v_safe_for_beta: {vsafe} ===")

print(
    f"\nGeri alma: UPDATE question_bank q SET is_active=b.is_active, "
    f"quality_review_status=b.quality_review_status, pipeline_metadata=b.pipeline_metadata "
    f"FROM {BACKUP} b WHERE q.id=b.id;"
)
