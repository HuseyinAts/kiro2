"""mufredat agaci onarimi: agac disinda asili 14 konu + test artigi + sayac

Revision ID: 0005_mufredat_agaci
Revises: 0004_billing_subscriptions
Create Date: 2026-09-09

SORUN
-----
topic_hierarchy'de 14 konu `subject_area` DOLU oldugu halde `parent_id` NULL.
Yani bir derse ait olduklarini soyluyorlar ama agacta hicbir derse bagli
degiller.

Bu bir veri hijyeni sorunu DEGIL, kullaniciya gorunen bir kusur.
services/question_bank_service.py:226-231:

    query = select(TopicHierarchy).where(TopicHierarchy.is_active.is_(True))
    if parent_id:  query = query.where(TopicHierarchy.parent_id == parent_id)
    else:          query = query.where(TopicHierarchy.parent_id.is_(None))

"Kok konular" = parent_id IS NULL. Dolayisiyla bu 14 konu ana konu listesinde
DERS gibi gorunuyor.

OLCUM (9 Eyl 2026, canli DB)
----------------------------
get_topic_hierarchy(parent_id=None) -> 28 kayit donuyor:

    BIO  Biyoloji            soru=0
    KIM  Kimya               soru=263
    KIM.DEN Kimyasal Denge   soru=1262   <- KONU, ders degil
    KIM.ASI Asitler ve Bazlar soru=478   <- KONU, ders degil
    TYT-KIM-01 Atom Yapisi   soru=277    <- KONU, ders degil
    ... (14 tanesi konu)
    TEST.BATCH2A Test Konu Batch2A       <- test artigi

Ve alt konu sayilari:

    MAT  20      KIM  0
    TUR   7      SOS  0
    TAR   7      FIZ  0
    COG   7      BIO  0

Yani en cok icerige sahip ders olan Kimya'ya (3.531 soru) tiklayan ogrenci
BOS liste goruyor; onun 11 konusu ust seviyede ders gibi duruyor.

Agac disinda asili konulara bagli toplam soru: 3.266 / 5.796 (%56).

DEGISIKLIK
----------
1) 11 KIMYA konusu -> parent KIM, level 2
2) 2 SOSYAL konusu (SOC02, SOC03) -> parent SOS, level 2
3) TEST.BATCH2A -> is_active = false
   DIKKAT: SILINMIYOR. `is_active` uc uretim servisi tarafindan zaten
   suzuluyor (question_bank_service, learning_event_service,
   soru_bankasi_service), dolayisiyla pasife almak kayittan cikarmaya
   yetiyor. Kalici silme veri silme islemidir ve ayri onay ister.
4) total_questions sayaci gercek sayimla dolduruluyor.
   Olculdu: 57 konuda sayac yanlisti (56'sinda 0, MAT.TRV'de 129 iken
   gercek 0). Bu alani okuyan her ekran yanlis sayi gosteriyordu.

Kodla degil KODLARLA calisiyor (`WHERE code IN (...)`): UUID'ler ortama
gore degisebilir, kod sabittir. Satir yoksa islem no-op.

GERI ALINABILIR
---------------
downgrade() olculmus onceki durumu birebir geri yaziyor (asagidaki
_ONCEKI_DURUM tablosu 9 Eyl 2026 canli olcumunden alinmistir).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0005_mufredat_agaci"
down_revision: Union[str, None] = "0004_billing_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# kod -> (hedef ebeveyn kodu, yeni level)
_YETIMLER: dict[str, tuple[str, int]] = {
    "KIM.ASI": ("KIM", 2),
    "KIM.DEN": ("KIM", 2),
    "KIM.ORG": ("KIM", 2),
    "KIM.TER": ("KIM", 2),
    "TYT-KIM-01": ("KIM", 2),
    "TYT-KIM-02": ("KIM", 2),
    "TYT-KIM-03": ("KIM", 2),
    "TYT-KIM-04": ("KIM", 2),
    "TYT-KIM-09": ("KIM", 2),
    "TYT-KIM-10": ("KIM", 2),
    "TYT-KIM-11": ("KIM", 2),
    "TYT-KIM-12": ("KIM", 2),
    "SOC02": ("SOS", 2),
    "SOC03": ("SOS", 2),
}

# 9 Eyl 2026 olcumu -- downgrade bunlari birebir geri yazar.
_ONCEKI_LEVEL: dict[str, int] = {
    "KIM.ASI": 2,
    "KIM.DEN": 2,
    "KIM.ORG": 2,
    "KIM.TER": 2,
    "TYT-KIM-01": 1,
    "TYT-KIM-02": 2,
    "TYT-KIM-03": 3,
    "TYT-KIM-04": 4,
    "TYT-KIM-09": 1,
    "TYT-KIM-10": 1,
    "TYT-KIM-11": 1,
    "TYT-KIM-12": 1,
    "SOC02": 1,
    "SOC03": 1,
}


def upgrade() -> None:
    baglanti = op.get_bind()

    # 1-2) Yetim konulari dogru derse bagla
    for kod, (ebeveyn_kodu, yeni_level) in _YETIMLER.items():
        baglanti.execute(
            sa.text(
                """
                UPDATE topic_hierarchy
                   SET parent_id = (
                           SELECT id FROM topic_hierarchy
                            WHERE code = :ebeveyn AND parent_id IS NULL
                            LIMIT 1
                       ),
                       level = :seviye,
                       updated_at = now()
                 WHERE code = :kod
                   AND parent_id IS NULL
                   AND EXISTS (
                           SELECT 1 FROM topic_hierarchy
                            WHERE code = :ebeveyn AND parent_id IS NULL
                       )
                """
            ),
            {"kod": kod, "ebeveyn": ebeveyn_kodu, "seviye": yeni_level},
        )

    # 3) Test artigini pasife al (SILME degil)
    baglanti.execute(
        sa.text(
            """
            UPDATE topic_hierarchy
               SET is_active = false, updated_at = now()
             WHERE code = 'TEST.BATCH2A'
            """
        )
    )

    # 4) total_questions sayacini gercek sayimla doldur
    baglanti.execute(
        sa.text(
            """
            UPDATE topic_hierarchy t
               SET total_questions = COALESCE(g.adet, 0),
                   updated_at = now()
              FROM (
                    SELECT th.id, count(qb.id) AS adet
                      FROM topic_hierarchy th
                      LEFT JOIN question_bank qb
                             ON qb.primary_topic_id = th.id
                            AND qb.is_active IS TRUE
                     GROUP BY th.id
                   ) g
             WHERE g.id = t.id
               AND t.total_questions IS DISTINCT FROM COALESCE(g.adet, 0)
            """
        )
    )


def downgrade() -> None:
    baglanti = op.get_bind()

    for kod, onceki in _ONCEKI_LEVEL.items():
        baglanti.execute(
            sa.text(
                """
                UPDATE topic_hierarchy
                   SET parent_id = NULL, level = :seviye, updated_at = now()
                 WHERE code = :kod
                """
            ),
            {"kod": kod, "seviye": onceki},
        )

    baglanti.execute(
        sa.text(
            """
            UPDATE topic_hierarchy
               SET is_active = true, updated_at = now()
             WHERE code = 'TEST.BATCH2A'
            """
        )
    )

    # Sayac olcum oncesi durumu: MAT.TRV 129, digerlerinin hepsi 0.
    baglanti.execute(
        sa.text("UPDATE topic_hierarchy SET total_questions = 0, updated_at = now()")
    )
    baglanti.execute(
        sa.text(
            """
            UPDATE topic_hierarchy
               SET total_questions = 129, updated_at = now()
             WHERE code = 'MAT.TRV'
            """
        )
    )
