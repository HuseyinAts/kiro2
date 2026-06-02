"""
Apply 37 triple-corroborated (b1==b2==DB) pilot candidates → verified_provisional.

Reversible + non-destructive:
  - Backup tablo (id, pipeline_metadata, quality_review_status, correct_answer)
  - pipeline_metadata.verified_provisional='true' + pool_growth_dblind marker EKLE
  - correct_answer DOKUNMA, quality_review_status DOKUNMA, is_active DOKUNMA
  - Yalnız beta-practice yoluna girer (is_active + verified_provisional flag);
    ana servis (auto_judged_high/human_verified) DEĞİŞMEZ.

Mekanizma: osym_exam_engine.py:1289 — pipeline_metadata->>'verified_provisional'='true'.
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import text

from core.database import db_manager

BACKUP = "question_bank_pool_growth_dblind_backup_20260603"
ids = json.loads(Path("/tmp/pool_pilot_candidates.json").read_text(encoding="utf-8"))


async def main() -> None:
    async with db_manager.get_session() as s:
        # Pre-check: bu 37 ID gerçekten unverified/pending + is_active mi, zaten provisional değil mi?
        pre = (
            await s.execute(
                text(
                    """SELECT quality_review_status,
                              COUNT(*) FILTER (WHERE is_active) AS active,
                              COUNT(*) FILTER (WHERE pipeline_metadata::jsonb->>'verified_provisional'='true') AS already_prov,
                              COUNT(*) AS n
                       FROM question_bank WHERE id = ANY(:ids)
                       GROUP BY quality_review_status"""
                ),
                {"ids": ids},
            )
        ).all()
        print(f"aday sayısı: {len(ids)}")
        for r in pre:
            print(
                f"  pre: status={r[0]} n={r[3]} active={r[1]} already_provisional={r[2]}"
            )

        # Backup (rollback + correct_answer dokunulmadığının kanıtı)
        await s.execute(text(f"DROP TABLE IF EXISTS {BACKUP}"))
        await s.execute(
            text(
                f"""CREATE TABLE {BACKUP} AS
                    SELECT id, pipeline_metadata, quality_review_status,
                           correct_answer, is_active
                    FROM question_bank WHERE id = ANY(:ids)"""
            ),
            {"ids": ids},
        )
        bk = (await s.execute(text(f"SELECT COUNT(*) FROM {BACKUP}"))).scalar()
        print(f"backup tablo: {BACKUP} ({bk} satır)")

        # UPDATE — verified_provisional + marker EKLE (canonical rename sql pattern)
        res = await s.execute(
            text(
                """UPDATE question_bank qb
                   SET pipeline_metadata = (
                       COALESCE(qb.pipeline_metadata::jsonb, '{}'::jsonb)
                       || jsonb_build_object(
                            'verified_provisional', 'true',
                            'pool_growth_dblind', '2026_06_03',
                            'dblind_method', 'b1==b2==db_triple_corroborated')
                   )::json
                   WHERE qb.id = ANY(:ids)
                     AND qb.is_active = true
                     AND COALESCE(qb.pipeline_metadata::jsonb->>'verified_provisional','') <> 'true'"""
            ),
            {"ids": ids},
        )
        await s.commit()
        print(f"UPDATE rowcount: {res.rowcount}")

        # Post-verify
        post = (
            await s.execute(
                text(
                    """SELECT COUNT(*) FILTER (WHERE pipeline_metadata::jsonb->>'verified_provisional'='true') AS prov,
                              COUNT(*) FILTER (WHERE pipeline_metadata::jsonb->>'pool_growth_dblind'='2026_06_03') AS marked
                       FROM question_bank WHERE id = ANY(:ids)"""
                ),
                {"ids": ids},
            )
        ).first()
        print(f"post: 37 ID'den provisional={post[0]} marked={post[1]}")

        total_prov = (
            await s.execute(
                text(
                    "SELECT COUNT(*) FROM question_bank "
                    "WHERE pipeline_metadata::jsonb->>'verified_provisional'='true'"
                )
            )
        ).scalar()
        print(
            f"toplam verified_provisional havuz: {total_prov} (önceki ~2,734 → +{res.rowcount})"
        )
        print(
            f"\nROLLBACK: UPDATE question_bank qb SET pipeline_metadata=b.pipeline_metadata "
            f"FROM {BACKUP} b WHERE qb.id=b.id;"
        )


if __name__ == "__main__":
    asyncio.run(main())
