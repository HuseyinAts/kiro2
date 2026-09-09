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
1) subject_area DOLU + parent_id NULL olan HER konu, subject_area'sinin
   isaret ettigi ders kokune baglanir (level = kok.level + 1). Yerel
   olcumde bu 11 KIMYA + 2 SOSYAL konusu demekti; CI'da ayrica
   MVP.MAT.GOLDEN (MATEMATIK) cikti.
2) (1 ile ayni kural)
3) Test artiklari (code LIKE 'TEST.%' veya adi 'Test Konu...') ->
   is_active = false
   DIKKAT: SILINMIYOR. `is_active` uc uretim servisi tarafindan zaten
   suzuluyor (question_bank_service, learning_event_service,
   soru_bankasi_service), dolayisiyla pasife almak kayittan cikarmaya
   yetiyor. Kalici silme veri silme islemidir ve ayri onay ister.
4) total_questions sayaci gercek sayimla dolduruluyor.
   Olculdu: 57 konuda sayac yanlisti (56'sinda 0, MAT.TRV'de 129 iken
   gercek 0). Bu alani okuyan her ekran yanlis sayi gosteriyordu.

UUID ile degil KOD ile calisiyor: kimlikler ortama gore degisir, kodlar
sabittir. Eslesme bulunmayan satira dokunulmaz (uydurma ebeveyn atanmaz).

KURAL TABANLI, LISTE TABANLI DEGIL
-----------------------------------
Ilk yazimda yukaridaki 14 kodu tek tek saymistim -- yerel DB'de olculen
kume buydu. CI'nin veritabaninda bu listede OLMAYAN baska bir yetim cikti:

    MVP.MAT.GOLDEN  "MVP Matematik (Golden seed)"  12 soru

ve ikinci bir test artigi (TEST.BATCH1B). Yani liste tabanli bir migration
yalnizca olculdugu ortami onarir. upgrade() artik invaryanti KURAL olarak
uyguluyor; her ortamda ayni sonucu veriyor.

GERI ALINABILIRLIK SINIRI (durust olmak gerekirse)
---------------------------------------------------
downgrade(), 9 Eyl 2026 yerel olcumunde tespit edilen 14 satiri birebir
eski haline (parent_id NULL + olculmus level) dondurur. Kuralin BASKA bir
ortamda buldugu satirlari (ornegin MVP.MAT.GOLDEN) geri alamaz, cunku
migration hangi satirlara dokundugunu kaydetmiyor.

Bu bilincli bir tercih: bu satirlari geri almak, onlari yeniden BOZUK
duruma (agacta asili, ana listede ders gibi gorunur) dondurmek demek.
downgrade'in amaci fidelity degil, kacis kapisi. Olcmedigim seyi geri
aldigimi iddia etmemek icin siniri buraya yaziyorum.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0005_mufredat_agaci"
down_revision: Union[str, None] = "0004_billing_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 9 Eyl 2026 YEREL olcumunde yetim bulunan satirlarin ONCEKI level'lari.
# upgrade() bu listeyi KULLANMIYOR -- o kural tabanli calisiyor. Liste
# yalnizca downgrade icin, ve yalnizca olculmus satirlar icin gecerli
# (bkz. yukaridaki "GERI ALINABILIRLIK SINIRI").
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

    # 1-2) Yetim konulari dogru derse bagla -- KURAL ile, liste ile DEGIL.
    #
    # Ilk yazimda 14 kodu tek tek saymistim; yerel DB'de olculen kume buydu.
    # CI'nin veritabaninda bu listede OLMAYAN baska yetimler cikti
    # (MVP.MAT.GOLDEN, 12 soru). Yani liste tabanli bir migration yalnizca
    # olculen ortami onariyor. Asagidaki kural her ortamda ayni invaryanti
    # uyguluyor: "subject_area DOLU olan her konunun bir ebeveyni olmali".
    #
    # Kural yalnizca subject_area -> kok eslesmesi BULUNAN satirlara
    # dokunuyor; eslesme yoksa satir oldugu gibi birakiliyor (uydurma
    # ebeveyn atanmiyor).
    baglanti.execute(
        sa.text(
            """
            WITH esleme(alan, kok_kodu) AS (
                VALUES ('FIZIK','FIZ'), ('KIMYA','KIM'), ('BIYOLOJI','BIO'),
                       ('MATEMATIK','MAT'), ('GEOMETRI','GEO'),
                       ('TURKCE','TUR'), ('EDEBIYAT','EDB'),
                       ('TARIH','TAR'), ('COGRAFYA','COG'),
                       ('SOSYAL','SOS'), ('FEN','FEN'),
                       ('GENEL','GEN'), ('PARAGRAF','PAR')
            ),
            kok AS (
                SELECT t.id, t.code, t.level
                  FROM topic_hierarchy t
                 WHERE t.parent_id IS NULL
                   AND t.subject_area IS NULL
            )
            UPDATE topic_hierarchy y
               SET parent_id = k.id,
                   level = k.level + 1,
                   updated_at = now()
              FROM esleme e
              JOIN kok k ON k.code = e.kok_kodu
             WHERE y.subject_area IS NOT NULL
               AND y.parent_id IS NULL
               AND upper(y.subject_area) = e.alan
               AND y.id <> k.id
            """
        )
    )

    # 3) Test artigini pasife al (SILME degil) -- yine kural ile.
    # Gozlenen adlandirma: TEST.BATCH2A / TEST.BATCH1B, adlari "Test Konu ...".
    # Desen, tests/db/test_mufredat_agaci_saglik.py'deki bekci ile AYNI
    # tutuluyor ki ikisi birbirinden ayrisamasin.
    baglanti.execute(
        sa.text(
            """
            UPDATE topic_hierarchy
               SET is_active = false, updated_at = now()
             WHERE is_active IS TRUE
               AND (code LIKE 'TEST.%' OR name_tr ILIKE 'Test Konu%')
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
