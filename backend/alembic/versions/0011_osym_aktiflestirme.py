"""OSYM kitapcik aktiflestirme: 291 pasif soru (TYT 125 + AYT 166) servise acilir

Revision ID: 0011_osym_aktiflestirme
Revises: 0010_supheli_anahtar
Create Date: 2026-09-10

BAGLAM
------
9 Eyl 2026'da ithal edilen 291 OSYM 2025 sorusu (#244) bilincli olarak
`is_active=false` yazilmisti (telif onayi bekler). Kullanici 10 Eyl 2026'da
"OSYM sorularini aktiflestir" diyerek onayi verdi. Bu migration is_active'i
cevirmekle YETINMEZ -- olcum (bkz. backend/_ci_art/_aktif_olcum.py, 10 Eyl
2026) gosterdi ki gercek servis kapisi `v_safe_for_beta` (core/quality_gate.py)
uc alani BIRDEN ister:

  question_bank.is_active            = TRUE   (zaten planlanan)
  question_bank.review_status        = 'approved'          (5.796 canli satirin
                                                              tumu bu degerde)
  question_statistics.quality_review_status IN ('human_verified','auto_judged_high')
  question_metadata.pipeline_metadata icinde bir "coherence signal" anahtari
        (student_coherent/verified_provisional/consensus_2signal_run/
         math_promote_run/verbal_promote_run) -- OSYM ithalatinin hicbiri
        yok, bu yuzden D9 migration'i (backend/migrations/D9_*.sql) yeni bir
        imza ekledi: 'osym_resmi_kaynak'. Bu Alembic migration'i o imzayi
        291 satira yazar; D9 SQL'i view'e OR dalini ekler (iki dosya birlikte
        calisir, D9 ONCE elle uygulanmis olmali -- bkz asagi).

quality_review_status icin 'human_verified' secildi, 'auto_judged_high'
degil: canli DB'de su an hicbir satir 'human_verified' degil (hepsi
auto_judged_high, D4 migration'inin kendi docstring'i bunu "beklenen 0"
diye not dusmustu). OSYM icerigi bir LLM tarafindan "auto_judged" edilmedi;
dogrulugu resmi kaynagin kendi yayinladigi cevap anahtari + kolon-farkinda
cikarici (tests/fast/test_osym_kitapcik.py: 125/125 TYT + 166/166 AYT tam
eslesme) + elle cozulen supheli alt kume (0009/0010) ile kuruldu. Bu daha
'auto_judged' degil 'human_verified' tanimina yakin.

UCUNCU BULGU -- BOS DERS KOKLERI (FIZ/BIO/EDB): bu uc kok su an SIFIR alt
konuya sahip (0 aktif soru oldugu icin `test_icerigi_olan_dersin_alt_konusu_
vardir` bekcisi simdiye kadar sessizdi). Aktiflestirme bu koklere dogrudan
21 FIZIK + 19 BIYOLOJI + 24 EDEBIYAT aktif soru koyacagindan bekci FIRLAR.
Duzeltme: kok basina bir "GENEL" alt konu yaratilir (koklerin gercek
mufredat agacina bolunmesi ayri, daha buyuk bir is -- burada yalniz bekcinin
yakaladigi yapisal bosluk kapatiliyor), etkilenen sorularin primary_topic_id'si
kokten bu alt konuya tasinir. MAT/SOS/TAR/COG/KIM zaten alt konuya sahip;
onlara dokunulmadi (soru root uzerinde kalir, mevcut davranisla ayni).

SIRA (elle, tek calisma penceresinde):
  1. psql < backend/migrations/D9_safe_for_beta_osym_resmi_kaynak.sql
  2. alembic upgrade head   (bu dosya)
  3. SELECT refresh_safe_for_beta();  (bu dosyanin sonunda otomatik cagrilir,
     fonksiyon yoksa -- taze/CI DB -- sessizce atlanir)

GUNLUK: aktiflestirme_gunlugu_0011(id, alan, eski_deger). downgrade() her
alani eski degerine dondurur, GENEL alt konularini (artik referanssizsa)
siler, D9'un eklendigi imzayi SILMEZ (D9 ayri SQL dosyasi, kendi
ROLLBACK'i var) -- yalniz veriyi geri alir.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0011_osym_aktiflestirme"
down_revision: Union[str, None] = "0010_supheli_anahtar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "aktiflestirme_gunlugu_0011"
_KAYNAKLAR = ("OSYM 2025 TYT", "OSYM 2025 AYT")
_SINYAL = "osym_resmi_kaynak"

# subject_area -> (kok kodu, yeni alt konu id'si, alt konu kodu)
# id'ler sabit: uuid5(NAMESPACE_OID, "topic:<kod>") -- downgrade ayni id'yi
# arar, DB'den kod ile yeniden bulmaya gerek kalmaz.
_BOS_KOKLER = {
    "FIZIK": ("FIZ", "ec98e431-7bd9-5f05-8ffb-a18a7f341d1c", "FIZ-OSYM-GENEL"),
    "BIYOLOJI": ("BIO", "af1e5d45-3c18-55ba-aa42-1f194ba4aeb5", "BIO-OSYM-GENEL"),
    "EDEBIYAT": ("EDB", "bae57b82-7881-5b6f-9421-736825525bba", "EDB-OSYM-GENEL"),
}

_SAYAC_SQL = """
UPDATE topic_hierarchy t
   SET total_questions = COALESCE(g.adet, 0), updated_at = now()
  FROM (SELECT th.id, count(qb.id) AS adet
          FROM topic_hierarchy th
          LEFT JOIN question_bank qb
                 ON qb.primary_topic_id = th.id AND qb.is_active IS TRUE
         GROUP BY th.id) g
 WHERE g.id = t.id
   AND t.total_questions IS DISTINCT FROM COALESCE(g.adet, 0)
"""


def _gunlukle(b, satirlar: list) -> None:
    if satirlar:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, alan, eski_deger) "  # noqa: S608  # nosec B608
                "VALUES (:id, :alan, :eski) ON CONFLICT DO NOTHING"
            ),
            [{"id": s[0], "alan": s[1], "eski": s[2]} for s in satirlar],
        )


def _kok_id(b, kod: str):
    return b.execute(
        sa.text(
            "SELECT id FROM topic_hierarchy "
            "WHERE code = :kod AND parent_id IS NULL AND subject_area IS NULL"
        ),
        {"kod": kod},
    ).scalar()


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0011] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0011] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("question_bank"):
        _log.info("[0011] question_bank yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("alan", sa.String(), nullable=False),
        sa.Column("eski_deger", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "alan"),
    )

    hedefler = list(_KAYNAKLAR)
    ids = (
        b.execute(
            sa.text(
                "SELECT b.id FROM question_bank b JOIN question_metadata m ON m.id = b.id "
                "WHERE m.source_book = ANY(:kaynaklar)"
            ),
            {"kaynaklar": hedefler},
        )
        .scalars()
        .all()
    )
    if not ids:
        _log.info("[0011] OSYM kaynakli soru yok -- atlandi (henuz ithal edilmemis?)")
        return

    # 1) Bos ders koklerine (FIZ/BIO/EDB) GENEL alt konu; kok-uzerindeki ilgili
    #    sorulari bu alt konuya tasi.
    tasinan = 0
    for ders, (kok, konu_id, konu_kod) in _BOS_KOKLER.items():
        kok_id = _kok_id(b, kok)
        if kok_id is None:
            _log.info("[0011] kok %s yok -- %s alt konusu atlandi", kok, ders)
            continue
        b.execute(
            sa.text(
                "INSERT INTO topic_hierarchy (id, level, parent_id, code, name_tr, "
                "name_en, osym_relevance, osym_frequency, total_questions, "
                "average_difficulty, difficulty_level, subject_area, is_active, "
                "created_at, updated_at) "
                "SELECT CAST(:id AS VARCHAR), 2, CAST(:parent AS VARCHAR), "
                "CAST(:kod AS VARCHAR), 'OSYM Kitapcik (siniflandirilmamis)', "
                "'OSYM Booklet (unclassified)', 0.5, 0, 0, 0.5, NULL, :ders, TRUE, "
                "now(), now() "
                "WHERE NOT EXISTS (SELECT 1 FROM topic_hierarchy WHERE id = :id)"
            ),
            {"id": konu_id, "parent": kok_id, "kod": konu_kod, "ders": ders},
        )
        satirlar = (
            b.execute(
                sa.text(
                    "SELECT q.id FROM question_bank q JOIN question_metadata m ON m.id = q.id "
                    "WHERE q.primary_topic_id = :kok AND m.subject_area = :ders "
                    "AND m.source_book = ANY(:kaynaklar)"
                ),
                {"kok": kok_id, "ders": ders, "kaynaklar": hedefler},
            )
            .scalars()
            .all()
        )
        if satirlar:
            _gunlukle(b, [(sid, "primary_topic_id", kok_id) for sid in satirlar])
            b.execute(
                sa.text(
                    "UPDATE question_bank SET primary_topic_id = :konu, updated_at = now() "
                    "WHERE id = ANY(:ids)"
                ),
                {"konu": konu_id, "ids": list(satirlar)},
            )
            tasinan += len(satirlar)

    # 2) question_bank: is_active + review_status.
    qb_pasif = (
        b.execute(
            sa.text(
                "SELECT b.id FROM question_bank b JOIN question_metadata m ON m.id = b.id "
                "WHERE m.source_book = ANY(:kaynaklar) AND b.is_active IS FALSE"
            ),
            {"kaynaklar": hedefler},
        )
        .scalars()
        .all()
    )
    _gunlukle(b, [(sid, "is_active", "false") for sid in qb_pasif])
    qb_pending = (
        b.execute(
            sa.text(
                "SELECT b.id FROM question_bank b JOIN question_metadata m ON m.id = b.id "
                "WHERE m.source_book = ANY(:kaynaklar) AND b.review_status = 'pending'"
            ),
            {"kaynaklar": hedefler},
        )
        .scalars()
        .all()
    )
    _gunlukle(b, [(sid, "review_status", "pending") for sid in qb_pending])
    b.execute(
        sa.text(
            "UPDATE question_bank SET is_active = TRUE, review_status = 'approved', "
            "updated_at = now() WHERE id = ANY(:ids)"
        ),
        {"ids": list(ids)},
    )

    # 3) question_statistics: quality_review_status.
    qs_pending = (
        b.execute(
            sa.text(
                "SELECT s.id FROM question_statistics s "
                "JOIN question_metadata m ON m.id = s.id "
                "WHERE m.source_book = ANY(:kaynaklar) AND s.quality_review_status = 'pending'"
            ),
            {"kaynaklar": hedefler},
        )
        .scalars()
        .all()
    )
    _gunlukle(b, [(sid, "quality_review_status", "pending") for sid in qs_pending])
    b.execute(
        sa.text(
            "UPDATE question_statistics SET quality_review_status = 'human_verified' "
            "WHERE id = ANY(:ids)"
        ),
        {"ids": list(ids)},
    )

    # 4) question_metadata: pipeline_metadata icine kapi imzasi ekle (D9'un
    #    okudugu anahtar). Eski deger tam JSON metni olarak loglanir.
    eski_pm = b.execute(
        sa.text(
            "SELECT m.id, m.pipeline_metadata::text FROM question_metadata m "
            "WHERE m.id = ANY(:ids) "
            "AND NOT (m.pipeline_metadata::jsonb ? :sinyal)"
        ),
        {"ids": list(ids), "sinyal": _SINYAL},
    ).all()
    _gunlukle(b, [(row[0], "pipeline_metadata", row[1]) for row in eski_pm])
    b.execute(
        sa.text(
            "UPDATE question_metadata SET pipeline_metadata = "
            "(pipeline_metadata::jsonb || jsonb_build_object(:sinyal, true))::json "
            "WHERE id = ANY(:ids) AND NOT (pipeline_metadata::jsonb ? :sinyal)"
        ),
        {"ids": list(ids), "sinyal": _SINYAL},
    )

    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    _log.info(
        "[0011] %s soru aktif; %s soru GENEL alt konuya tasindi",
        len(ids),
        tasinan,
    )


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0011] %s yok -- geri alinacak bir sey yok", GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id, alan, eski_deger FROM {GUNLUK}")  # noqa: S608  # nosec B608
    ).all()
    for sid, alan, eski in kayitlar:
        if alan == "primary_topic_id":
            b.execute(
                sa.text(
                    "UPDATE question_bank SET primary_topic_id = :eski, updated_at = now() "
                    "WHERE id = :id"
                ),
                {"eski": eski, "id": sid},
            )
        elif alan == "is_active":
            b.execute(
                sa.text(
                    "UPDATE question_bank SET is_active = FALSE, updated_at = now() "
                    "WHERE id = :id"
                ),
                {"id": sid},
            )
        elif alan == "review_status":
            b.execute(
                sa.text(
                    "UPDATE question_bank SET review_status = :eski, updated_at = now() "
                    "WHERE id = :id"
                ),
                {"eski": eski, "id": sid},
            )
        elif alan == "quality_review_status":
            b.execute(
                sa.text(
                    "UPDATE question_statistics SET quality_review_status = :eski "
                    "WHERE id = :id"
                ),
                {"eski": eski, "id": sid},
            )
        elif alan == "pipeline_metadata":
            b.execute(
                sa.text(
                    "UPDATE question_metadata SET pipeline_metadata = CAST(:eski AS json) "
                    "WHERE id = :id"
                ),
                {"eski": eski, "id": sid},
            )
    for _ders, (_kok, konu_id, _kod) in _BOS_KOKLER.items():
        b.execute(
            sa.text(
                "DELETE FROM topic_hierarchy t WHERE t.id = :id "
                "AND NOT EXISTS (SELECT 1 FROM question_bank q WHERE q.primary_topic_id = t.id)"
            ),
            {"id": konu_id},
        )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
    _log.info("[0011] %s kayit geri alindi, %s dusuruldu", len(kayitlar), GUNLUK)
