"""MAT.GEO geometri sorulari GEOMETRI dersine etiketlendi, konu GEO kokune tasindi

Revision ID: 0007_mat_geo_geometri
Revises: 0006_cift_taksonomi
Create Date: 2026-09-09

KARAR (docs/veritabani-denetimi-20260909.md madde 14)
-----------------------------------------------------
TYT blueprint GEOMETRI 14 soru istiyor, havuzda subject_area=GEOMETRI olan
0 soru var. MAT.GEO ("Geometri", MAT kokunun altinda, 63 soru) ise
subject_area=MATEMATIK. GEO koku (level 1, GEOMETRI dersinin yuvasi) bos.
Sinav motoru (api/v1/exams.py) MAT dalini `code IN SUBJECT_MAPPING["MAT"]`
(MAT, GEO, TYT-MAT-01) VEYA `lower(subject_area) IN ("matematik",
"geometri")` birlesimiyle kurar: yeniden etiketlenen sorular MAT
derlemesinden DUSMEZ, ustune GEOMETRI yuvasi dolar.

OLCUM (63 soru, anahtar-kelime denetimi + ornek okuma)
------------------------------------------------------
57'si guclu geometri terimi tasiyor (ucgen, dortgen, cember, aci, kosegen,
prizma, ...). Kalan 6'nin 1'i geometri (mavi/kirmizi kare alani, [AB] dik
[BC]); 5'i geometri DEGIL:
  4 x geometrik dizi / ardisik kat ("geometrik" kelimesi yuzunden yanlis
      etiket)                                     -> MAT.DIZ (Diziler, 0 soru)
  1 x sembol tanimi ($a^2+3a$, "cember icine yazilan sayi")  -> MAT.SAY
  1 x kartezyen carpim / kumeler                  -> MAT.FON (kartezyen
      carpim MEB'de fonksiyonlar unitesinin girisi; ayri "Kumeler" konusu yok)
Bu 6 satir sabit id ile tasinir (olculdu, tahmin degil); subject_area'lari
MATEMATIK kalir.

NE DEGISIR
----------
1. 6 soru: primary_topic_id MAT.GEO -> MAT.DIZ/MAT.SAY/MAT.FON (yukaridaki).
2. Kalan MAT.GEO sorulari: question_metadata.subject_area = 'GEOMETRI'.
3. MAT.GEO konusu: parent_id = GEO koku, subject_area = 'GEOMETRI',
   level = GEO.level + 1 (kod "MAT.GEO" korunur: seed/dungeon scriptleri
   koda bagli, yeniden adlandirma ayri is).
4. total_questions sayaci yeniden hesaplanir (0005/0006 ile ayni SQL).

GERI ALINABILIRLIK
------------------
Degisim kumesi deterministik ve kucuk: downgrade 6 sabit id'yi MAT.GEO'ya
geri alir, subject_area=GEOMETRI olup MAT.GEO'ya bagli sorulari MATEMATIK'e
cevirir, konuyu MAT kokune (level MAT+1) geri tasir, sayaci yeniden hesaplar.
GEO koku olmayan bir DB'de (taze CI) upgrade hicbir sey yapmaz ve bunu
loglar; sozlesme bekcisi tests/db/test_mufredat_agaci_saglik.py'de.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0007_mat_geo_geometri"
down_revision: Union[str, None] = "0006_cift_taksonomi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

# (soru id, hedef konu kodu) -- 9 Eyl 2026 olcumu, docstring'deki 6 satir.
_YENIDEN_ETIKET: tuple[tuple[str, str], ...] = (
    ("4abab2bd-adde-5445-b265-073425ae5868", "MAT.DIZ"),  # geometrik dizi a4/a2
    ("5f96e661-5f04-577f-953d-1ec72295943b", "MAT.DIZ"),  # kumbara, 2^n
    ("7ad97ab0-7eea-5cb8-8d3e-c5b639a44c46", "MAT.DIZ"),  # f(x)=2x-1, ortak fark
    ("8c5a3c0c-af1e-5d4f-afc5-ee109f80dc43", "MAT.DIZ"),  # besinci terim 64
    ("73d0a29d-4621-5702-9741-71b602ad0900", "MAT.SAY"),  # sembol tanimi a^2+3a
    ("7bac2f60-4f6c-50a8-88c7-64d8497fa3da", "MAT.FON"),  # kartezyen carpim
)

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


def _konu_id(b, kod: str) -> Union[str, None]:
    sonuc: Union[str, None] = b.execute(
        sa.text("SELECT id FROM topic_hierarchy WHERE code = :kod"), {"kod": kod}
    ).scalar()
    return sonuc


def _kok_id(b, kod: str) -> Union[str, None]:
    sonuc: Union[str, None] = b.execute(
        sa.text(
            "SELECT id FROM topic_hierarchy "
            "WHERE code = :kod AND parent_id IS NULL AND subject_area IS NULL"
        ),
        {"kod": kod},
    ).scalar()
    return sonuc


def upgrade() -> None:
    b = op.get_bind()
    geo_kok = _kok_id(b, "GEO")
    mat_geo = _konu_id(b, "MAT.GEO")
    if geo_kok is None or mat_geo is None:
        _log.info("[0007] GEO koku veya MAT.GEO yok (taze DB?) -- atlandi")
        return

    # 1) Yanlis etiketli 6 soru MAT.GEO'dan cikar (yalnizca hala orada ise).
    for soru_id, hedef_kod in _YENIDEN_ETIKET:
        hedef = _konu_id(b, hedef_kod)
        if hedef is None:
            _log.info("[0007] %s yok, %s MAT.GEO'da birakildi", hedef_kod, soru_id)
            continue
        b.execute(
            sa.text(
                "UPDATE question_bank SET primary_topic_id = :hedef, updated_at = now() "
                "WHERE id = :sid AND primary_topic_id = :eski"
            ),
            {"hedef": hedef, "sid": soru_id, "eski": mat_geo},
        )

    # 2) Kalan MAT.GEO sorulari GEOMETRI dersine.
    n = b.execute(
        sa.text(
            "UPDATE question_metadata m SET subject_area = 'GEOMETRI' "
            "FROM question_bank q "
            "WHERE q.id = m.id AND q.primary_topic_id = :mg AND m.subject_area = 'MATEMATIK'"
        ),
        {"mg": mat_geo},
    ).rowcount

    # 3) Konu GEO kokune.
    b.execute(
        sa.text(
            "UPDATE topic_hierarchy SET parent_id = :kok, subject_area = 'GEOMETRI', "
            "level = (SELECT level + 1 FROM topic_hierarchy WHERE id = :kok), "
            "updated_at = now() WHERE id = :mg"
        ),
        {"kok": geo_kok, "mg": mat_geo},
    )
    b.execute(sa.text(_SAYAC_SQL))
    _log.info(
        "[0007] MAT.GEO -> GEO koku; %s soru GEOMETRI, %s soru yeniden etiketlendi",
        n,
        len(_YENIDEN_ETIKET),
    )


def downgrade() -> None:
    b = op.get_bind()
    mat_kok = _kok_id(b, "MAT")
    mat_geo = _konu_id(b, "MAT.GEO")
    if mat_kok is None or mat_geo is None:
        _log.info("[0007] MAT koku veya MAT.GEO yok -- geri alinacak bir sey yok")
        return

    for soru_id, hedef_kod in _YENIDEN_ETIKET:
        hedef = _konu_id(b, hedef_kod)
        if hedef is None:
            continue
        b.execute(
            sa.text(
                "UPDATE question_bank SET primary_topic_id = :mg, updated_at = now() "
                "WHERE id = :sid AND primary_topic_id = :hedef"
            ),
            {"mg": mat_geo, "sid": soru_id, "hedef": hedef},
        )
    b.execute(
        sa.text(
            "UPDATE question_metadata m SET subject_area = 'MATEMATIK' "
            "FROM question_bank q "
            "WHERE q.id = m.id AND q.primary_topic_id = :mg AND m.subject_area = 'GEOMETRI'"
        ),
        {"mg": mat_geo},
    )
    b.execute(
        sa.text(
            "UPDATE topic_hierarchy SET parent_id = :kok, subject_area = 'MATEMATIK', "
            "level = (SELECT level + 1 FROM topic_hierarchy WHERE id = :kok), "
            "updated_at = now() WHERE id = :mg"
        ),
        {"kok": mat_kok, "mg": mat_geo},
    )
    b.execute(sa.text(_SAYAC_SQL))
