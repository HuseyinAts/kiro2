"""Katman C'nin CANLI kaniti: bozuk oge komsulari oldurmuyor mu? (S255)

Konteyner ICINDE kosar. Katman A ve B bilinen tetikleyicileri kapida
durdurdugu icin bozuk bir oge artik HTTP uzerinden batch'e ULASAMIYOR --
bu yuzden motorun toplu yazim metodu DOGRUDAN cagriliyor.

    docker cp backend/scripts/_katman_c_canli_prob.py kiro2-backend:/tmp/
    docker exec kiro2-backend python /tmp/_katman_c_canli_prob.py <SID> <QID>
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):  # mypy: TextIO taban sinifinda yok
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _oge(sid: str, qid: str, harf: str) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "exam_session_id": sid,
        "question_id": qid,
        "selected_answer": harf,
        "response_time_seconds": 3.0,
        "is_correct": None,
        "answer_changes": 0,
        "time_to_first_answer": 0.0,
    }


async def main(sid: str, qid: str) -> int:
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from core.database import get_db_session_context
    from core.osym_exam_engine import osym_exam_engine
    from models.exam_db import StudentAnswer

    async def satir_sayisi() -> int:
        async with get_db_session_context() as s:
            r = await s.execute(
                text(
                    "SELECT count(*) FROM student_answers WHERE exam_session_id = :sid"
                ),
                {"sid": sid},
            )
            return int(r.scalar_one())

    stmt = pg_insert(StudentAnswer)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_student_answer",
        set_={
            "selected_answer": stmt.excluded.selected_answer,
            "response_time_seconds": stmt.excluded.response_time_seconds,
            "is_correct": stmt.excluded.is_correct,
            "answered_at": datetime.now(),
            "answer_changes": StudentAnswer.answer_changes + 1,
        },
    )

    # 1 GECERLI (var olan soru, UPSERT) + 1 BOZUK (yabanci question_id -> FK).
    bozuk_qid = str(uuid.uuid4())
    batch = [_oge(sid, qid, "D"), _oge(sid, bozuk_qid, "A")]

    once_satir = await satir_sayisi()
    once_hata = osym_exam_engine.toplu_yazim_hata_sayaci
    once_dusen = osym_exam_engine.dusen_cevap_sayaci

    yazilan, dusen = await osym_exam_engine._toplu_yaz_kurtarmali(stmt, batch)

    sonra_satir = await satir_sayisi()

    async with get_db_session_context() as s:
        r = await s.execute(
            text(
                "SELECT selected_answer FROM student_answers "
                "WHERE exam_session_id = :sid AND question_id = :qid"
            ),
            {"sid": sid, "qid": qid},
        )
        gecerli_harf = r.scalar_one_or_none()

    print("=== KATMAN C CANLI PROB ===")
    print("batch                 : 1 gecerli + 1 bozuk (yabanci question_id)")
    print(f"donen (yazilan,dusen) : ({yazilan}, {dusen})   beklenen (1, 1)")
    print(f"gecerli ogenin harfi  : {gecerli_harf!r}   beklenen 'D'")
    print(f"satir sayisi          : {once_satir} -> {sonra_satir} (bozuk yazilmamali)")
    print(
        "sayaclar              : toplu_hata "
        f"{once_hata} -> {osym_exam_engine.toplu_yazim_hata_sayaci} | "
        f"dusen {once_dusen} -> {osym_exam_engine.dusen_cevap_sayaci}"
    )
    tamam = (
        (yazilan, dusen) == (1, 1)
        and gecerli_harf == "D"
        and sonra_satir == once_satir
        and osym_exam_engine.toplu_yazim_hata_sayaci == once_hata + 1
        and osym_exam_engine.dusen_cevap_sayaci == once_dusen + 1
    )
    print("YARGI                 :", "GECTI" if tamam else "DUSTU")
    return 0 if tamam else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1], sys.argv[2])))
