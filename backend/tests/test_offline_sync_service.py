"""offline_sync_service F821 regression — process_sync_results NameError'ları.

Bug: `questions_map` ve `cards` döngüden önce hiç tanımlanmamış (ruff F821);
`_next_sync_at_iso` `timezone.utc` kullanıyor ama dosya yalnız `UTC` import ediyor.
Sonuç: her offline-sonuç işleme çağrısı NameError'a düşüyordu.

DB'siz test: process_sync_results'a sahte (capturing) AsyncSession verilir.
Fix öncesi NameError → FAIL, sonrası senkron işleme → PASS.
"""

from __future__ import annotations

from typing import Any

import pytest


class _Result:
    def __init__(self, mapping=None, scalar_list=None):
        self._mapping = mapping
        self._scalar_list = scalar_list or []

    def mappings(self):
        outer = self

        class _M:
            def first(self):
                return outer._mapping

        return _M()

    def scalars(self):
        outer = self

        class _S:
            def all(self):
                return outer._scalar_list

        return _S()


class _FakeQuestion:
    def __init__(self, qid: str):
        self.id = qid


class _FakeCard:
    """_apply_fsrs_grade'in yerinde mutasyona ugrattigi alanlari tasir."""

    def __init__(self, qid: str):
        self.front_text = f"question:{qid}"
        self.lapses = 0
        self.reps = 0
        self.stability = 1.0
        self.scheduled_days = 1
        self.state = "new"
        self.last_review = None
        self.due_date = None


class _FakeSession:
    """Statement içeriğine göre cevap döndüren minimal async session sahtesi."""

    def __init__(self, student_id: str, questions=None, cards=None):
        self.student_id = student_id
        self.questions = questions or []
        self.cards = cards or []
        self.added: list[Any] = []
        self.committed = False

    async def execute(self, stmt, params=None):
        s = str(stmt).lower()
        if "update offline_sync_packages" in s:
            return _Result()
        if "offline_sync_packages" in s:  # package SELECT
            return _Result(mapping={"student_id": self.student_id, "consumed_at": None})
        if "fsrs" in s:
            return _Result(scalar_list=list(self.cards))
        if "question_bank" in s:
            return _Result(scalar_list=list(self.questions))
        return _Result(scalar_list=[])

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


def test_next_sync_at_iso_no_nameerror():
    """_next_sync_at_iso geçerli ISO string dönmeli (timezone NameError olmamalı)."""
    from datetime import datetime

    from services.offline_sync_service import _next_sync_at_iso

    out = _next_sync_at_iso()
    # NameError olsaydı buraya gelinemezdi; ayrıca parse edilebilir olmalı
    parsed = datetime.fromisoformat(out)
    assert parsed is not None


@pytest.mark.asyncio
async def test_process_sync_results_valid_question_synced():
    """Geçerli (var olan) soru için cevap senkronlanmalı — questions_map/cards tanımlı."""
    from services.offline_sync_service import process_sync_results

    db = _FakeSession("stu-1", questions=[_FakeQuestion("q1")], cards=[_FakeCard("q1")])
    out = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-1",
        results=[
            {
                "question_id": "q1",
                "selected_answer": "A",
                "is_correct": True,
                "time_seconds": 5.0,
            }
        ],
        completed_at="2026-06-19T00:00:00",
    )
    assert out["synced_count"] == 1, f"beklenen 1 senkron, alınan: {out}"
    assert out["failed_count"] == 0
    assert "next_sync_recommended_at" in out
    # Kart GERCEKTEN mutasyona ugradi ve db.add edildi -- "senkronlandi" bunu demeli
    assert db.added, "synced sayildi ama hicbir kart db.add edilmedi"
    assert db.added[0].state == "review"


@pytest.mark.asyncio
async def test_process_sync_results_unknown_question_failed():
    """questions_map'te olmayan soru failed sayılmalı (NameError'a değil)."""
    from services.offline_sync_service import process_sync_results

    db = _FakeSession("stu-1", questions=[], cards=[])
    out = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-1",
        results=[
            {
                "question_id": "ghost",
                "selected_answer": "B",
                "is_correct": False,
                "time_seconds": 3.0,
            }
        ],
        completed_at="2026-06-19T00:00:00",
    )
    assert out["synced_count"] == 0
    assert out["failed_count"] == 1


# ---------------------------------------------------------------------------
# S251: synced_count FAZLA-RAPORLUYORDU
#
# Kusur: `synced += 1` FSRS karti bulunamadiginda da calisiyordu. Ogrenci
# cevrimdisi 40 soru cozup senkronlarsa ve hicbirinin karti yoksa API
# "synced_count: 40" donuyordu -- oysa HICBIR SEY kalici olmamisti.
# Karar (kullanici): 3. sayac `skipped_count`. "failed" demek yanlis olurdu --
# kart yoklugu ogrencinin hatasi degil, sistemin eksigi.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_karti_olmayan_yanit_skipped_sayilir_synced_degil():
    """Soru VAR ama FSRS karti YOK -> hicbir sey kalici olmaz -> synced DEGIL."""
    from services.offline_sync_service import process_sync_results

    db = _FakeSession("stu-1", questions=[_FakeQuestion("q1")], cards=[])
    out = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-1",
        results=[
            {
                "question_id": "q1",
                "selected_answer": "A",
                "is_correct": True,
                "time_seconds": 5.0,
            }
        ],
        completed_at="2026-06-19T00:00:00",
    )

    assert (
        out["synced_count"] == 0
    ), f"kart yokken 'senkronlandi' denemez, alinan: {out}"
    assert out["skipped_count"] == 1
    assert out["failed_count"] == 0, "kart yoklugu ogrencinin HATASI degil"
    assert not db.added, "hicbir kart eklenmedigi halde add cagrildi"


@pytest.mark.asyncio
async def test_uc_sayac_toplami_gonderilen_yanit_sayisina_esittir():
    """Hicbir yanit sayilmadan kaybolmamali: synced + skipped + failed == N."""
    from services.offline_sync_service import process_sync_results

    db = _FakeSession(
        "stu-1",
        questions=[_FakeQuestion("q1"), _FakeQuestion("q2")],
        cards=[_FakeCard("q1")],
    )
    yanitlar = [
        # q1: karti VAR -> synced
        {
            "question_id": "q1",
            "selected_answer": "A",
            "is_correct": True,
            "time_seconds": 5.0,
        },
        # q2: soru var, kart YOK -> skipped
        {
            "question_id": "q2",
            "selected_answer": "B",
            "is_correct": False,
            "time_seconds": 9.0,
        },
        # hayalet soru -> failed
        {
            "question_id": "ghost",
            "selected_answer": "C",
            "is_correct": False,
            "time_seconds": 3.0,
        },
        # gecersiz secenek -> failed
        {
            "question_id": "q1",
            "selected_answer": "Z",
            "is_correct": False,
            "time_seconds": 1.0,
        },
    ]

    out = await process_sync_results(
        db=db,
        student_id="stu-1",
        package_id="pkg-1",
        results=yanitlar,
        completed_at="2026-06-19T00:00:00",
    )

    assert out["synced_count"] == 1
    assert out["skipped_count"] == 1
    assert out["failed_count"] == 2
    toplam = out["synced_count"] + out["skipped_count"] + out["failed_count"]
    assert toplam == len(
        yanitlar
    ), f"{len(yanitlar)} yanit gonderildi ama {toplam} raporlandi -- yanit kayboldu"
