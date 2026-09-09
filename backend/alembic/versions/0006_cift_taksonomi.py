"""cift taksonomi: ayni ebeveyn altinda ayni adli kopya konular tekillestirildi

Revision ID: 0006_cift_taksonomi
Revises: 0005_mufredat_agaci
Create Date: 2026-09-09

SORUN (docs/veritabani-denetimi-20260909.md bolum 4.2)
-------------------------------------------------------
topic_hierarchy'de iki taksonomi ic ice: noktali agac (MAT.*, TUR.*, KIM.*,
name_en dolu, seed_dungeon_topics.py ile bilincli kurulmus) ve eski duz liste
(TYT-XX-NN, name_en bos). TUR altinda ayni ad iki kez:

    TUR.PAR    Paragraf        7 soru      TYT-TR-03  Paragraf      134 soru
    TUR.DIL    Dil Bilgisi     9 soru      TYT-TR-02  Dil Bilgisi    51 soru

Ogrenci konu listesinde "Paragraf"i iki kez goruyor; ilerleme/istatistik iki
konuya bolunuyor.

OLCUM
-----
topic_hierarchy'ye FK ile bagli kolonlar: question_bank.primary_topic_id,
duels.topic_id, dungeon_progress.topic_id, topic_prerequisites.topic_id /
prereq_id, topic_hierarchy.parent_id. FK'siz ama konu id'si tasiyan:
fsrs_cards.topic. Kopyalara bagli satir (yerel): yalnizca question_bank.

Sinav motoru (api/v1/exams.py `_branch_topic_ids`) konulari
`code IN SUBJECT_MAPPING[...]` VEYA `lower(subject_area) IN ...` ile bulur,
`topic_hierarchy.is_active` SUZMEZ. TUR.PAR/TUR.DIL subject_area=TURKCE
oldugu icin tasinan sorular TYT derlemesinde erisilebilir kalir.

KURAL
-----
Ayni `parent_id` altinda, `lower(name_tr)` esit, aktif birden fazla konu
varsa: hayatta kalan = kodu nokta iceren (noktali taksonomi); yoksa en cok
sorusu olan; yoksa alfabetik ilk. Kaybedenin tum referanslari hayatta
kalana tasinir, kaybeden pasife alinir (SILINMEZ).

dungeon_progress'in PK'si (user_id, topic_id): tasima carpisma yaratirsa o
satir DOKUNULMADAN birakilir (pasif konuya isaret eder, FK bozulmaz).
topic_prerequisites icin de ayni: hedef cift zaten varsa satir birakilir.

Ayrica `PAR` koku (level 1, subject_area NULL, "Paragraf", 0 referans)
pasife alinir: Paragraf bir DERS degil, Turkce'nin konusu. `GEO` koku
BILINCLI OLARAK DOKUNULMADI -- MAT.GEO ile ayni adi tasisa da kopya degil:
sinav motoru SUBJECT_MAPPING["MAT"] icinde "GEO"yu ve subject_area
"geometri"yi ayri anahtar olarak bekliyor; GEO, GEOMETRI dersinin bos
yuvasi. MAT.GEO'nun 63 sorusunun GEOMETRI diye yeniden etiketlenip
etiketlenmeyecegi bir icerik karari, bu migration'in isi degil.

GERI ALINABILIRLIK
------------------
Her tasinan referans `topic_birlestirme_gunlugu` tablosuna yazilir;
downgrade() gunlukten birebir geri alir, kaybedenleri yeniden aktifler,
gunlugu dusurur. 0005'teki "olcmedigimi geri alamam" sinirinin dersi:
bu kez neye dokunuldugu kaydediliyor.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0006_cift_taksonomi"
down_revision: Union[str, None] = "0005_mufredat_agaci"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# S608 (f-string SQL) bu dosyada bilincli olarak noqa: f-string'e giren her
# parca MODUL SABITI (gunluk tablosu adi, _REFERANSLAR'daki tablo/kolon
# adlari, sabit kolon adlari). Konu kimlikleri ve satir anahtarlari gibi
# VERI degerleri her zaman bagli parametre (:giden, :kalan, :kid, :a) ile
# geciyor -- dis girdi yok, migration ortaminda cagiran da yok.
_GUNLUK = "topic_birlestirme_gunlugu"

# (tablo, kolon, satir anahtari kolonu) -- basit tek-kolon anahtarli tablolar
_REFERANSLAR = (
    ("question_bank", "primary_topic_id", "id"),
    ("fsrs_cards", "topic", "id"),
    ("duels", "topic_id", "id"),
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


def _tablo_var(baglanti, ad: str) -> bool:
    return bool(
        baglanti.execute(
            sa.text("SELECT to_regclass(:ad) IS NOT NULL"), {"ad": ad}
        ).scalar()
    )


def _pasiflestir_ve_kaydet(baglanti, konu_id: str, kalan_id: str) -> None:
    """Konuyu pasife al ve bunu gunluge yaz (tablo='topic_hierarchy')."""
    baglanti.execute(
        sa.text(
            f"""
            INSERT INTO {_GUNLUK} (tablo, kolon, satir_anahtar, eski_topic_id, yeni_topic_id)
            VALUES ('topic_hierarchy', 'is_active', :kid, :kid, :kalan)
            """  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
        ),
        {"kid": konu_id, "kalan": kalan_id},
    )
    baglanti.execute(
        sa.text(
            "UPDATE topic_hierarchy SET is_active = false, updated_at = now() WHERE id = :kid"
        ),
        {"kid": konu_id},
    )


def upgrade() -> None:
    b = op.get_bind()

    b.execute(
        sa.text(
            f"""
            CREATE TABLE IF NOT EXISTS {_GUNLUK} (
                id            BIGSERIAL PRIMARY KEY,
                tablo         TEXT NOT NULL,
                kolon         TEXT NOT NULL,
                satir_anahtar TEXT NOT NULL,
                eski_topic_id TEXT NOT NULL,
                yeni_topic_id TEXT NOT NULL,
                kaydedildi    TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    )

    ciftler = b.execute(
        sa.text(
            """
            WITH aday AS (
                SELECT t.id, t.parent_id, lower(t.name_tr) AS ad, t.code,
                       (SELECT count(*) FROM question_bank q
                         WHERE q.primary_topic_id = t.id) AS soru
                  FROM topic_hierarchy t
                 WHERE t.is_active IS TRUE AND t.parent_id IS NOT NULL
            ),
            grup AS (
                SELECT parent_id, ad,
                       array_agg(id ORDER BY (code LIKE '%.%') DESC, soru DESC, code) AS ids
                  FROM aday GROUP BY parent_id, ad HAVING count(*) > 1
            )
            SELECT ids[1] AS kalan, unnest(ids[2:]) AS giden FROM grup
            """
        )
    ).fetchall()

    for kalan, giden in ciftler:
        for tablo, kolon, anahtar in _REFERANSLAR:
            if not _tablo_var(b, tablo):
                continue
            b.execute(
                sa.text(
                    f"""
                    INSERT INTO {_GUNLUK} (tablo, kolon, satir_anahtar, eski_topic_id, yeni_topic_id)
                    SELECT '{tablo}', '{kolon}', "{anahtar}"::text, :giden, :kalan
                      FROM "{tablo}" WHERE "{kolon}" = :giden
                    """  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
                ),
                {"giden": giden, "kalan": kalan},
            )
            b.execute(
                sa.text(
                    f'UPDATE "{tablo}" SET "{kolon}" = :kalan WHERE "{kolon}" = :giden'  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
                ),
                {"giden": giden, "kalan": kalan},
            )

        # dungeon_progress: PK (user_id, topic_id) -- carpismayanlari tasi
        if _tablo_var(b, "dungeon_progress"):
            b.execute(
                sa.text(
                    f"""
                    INSERT INTO {_GUNLUK} (tablo, kolon, satir_anahtar, eski_topic_id, yeni_topic_id)
                    SELECT 'dungeon_progress', 'topic_id', d.user_id::text, :giden, :kalan
                      FROM dungeon_progress d
                     WHERE d.topic_id = :giden
                       AND NOT EXISTS (SELECT 1 FROM dungeon_progress e
                                        WHERE e.user_id = d.user_id AND e.topic_id = :kalan)
                    """  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
                ),
                {"giden": giden, "kalan": kalan},
            )
            b.execute(
                sa.text(
                    """
                    UPDATE dungeon_progress d SET topic_id = :kalan
                     WHERE d.topic_id = :giden
                       AND NOT EXISTS (SELECT 1 FROM dungeon_progress e
                                        WHERE e.user_id = d.user_id AND e.topic_id = :kalan)
                    """
                ),
                {"giden": giden, "kalan": kalan},
            )

        # topic_prerequisites: iki kolon, hedef cift zaten varsa dokunma
        if _tablo_var(b, "topic_prerequisites"):
            for kolon, diger in (("topic_id", "prereq_id"), ("prereq_id", "topic_id")):
                b.execute(
                    sa.text(
                        f"""
                        INSERT INTO {_GUNLUK} (tablo, kolon, satir_anahtar, eski_topic_id, yeni_topic_id)
                        SELECT 'topic_prerequisites', '{kolon}', p.id::text, :giden, :kalan
                          FROM topic_prerequisites p
                         WHERE p."{kolon}" = :giden
                           AND p."{diger}" <> :kalan
                           AND NOT EXISTS (SELECT 1 FROM topic_prerequisites e
                                            WHERE e."{kolon}" = :kalan AND e."{diger}" = p."{diger}")
                        """  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
                    ),
                    {"giden": giden, "kalan": kalan},
                )
                b.execute(
                    sa.text(
                        f"""
                        UPDATE topic_prerequisites p SET "{kolon}" = :kalan
                         WHERE p.id::text IN (SELECT satir_anahtar FROM {_GUNLUK}
                                               WHERE tablo = 'topic_prerequisites'
                                                 AND kolon = '{kolon}'
                                                 AND eski_topic_id = :giden
                                                 AND yeni_topic_id = :kalan)
                        """  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
                    ),
                    {"giden": giden, "kalan": kalan},
                )

        # Pasiflestirmenin kendisi de gunluge yazilir: referansi SIFIR olan bir
        # kaybeden aksi halde gunlukte hic gorunmez ve downgrade onu geri
        # aktifleyemezdi.
        _pasiflestir_ve_kaydet(b, giden, kalan)

    # PAR koku: Paragraf ders degil. 0 referans olculdu; kural degil, acik kod
    # (GEO'yu yakalamamak icin -- bkz. docstring).
    par_id = b.execute(
        sa.text(
            """
            SELECT id FROM topic_hierarchy t
             WHERE code = 'PAR' AND parent_id IS NULL AND subject_area IS NULL
               AND is_active IS TRUE
               AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c WHERE c.parent_id = t.id)
               AND NOT EXISTS (SELECT 1 FROM question_bank q WHERE q.primary_topic_id = t.id)
            """
        )
    ).scalar()
    if par_id:
        _pasiflestir_ve_kaydet(b, par_id, "-")

    b.execute(sa.text(_SAYAC_SQL))


def downgrade() -> None:
    b = op.get_bind()
    if not _tablo_var(b, _GUNLUK):
        return

    kayitlar = b.execute(
        sa.text(
            f"SELECT tablo, kolon, satir_anahtar, eski_topic_id, yeni_topic_id FROM {_GUNLUK} ORDER BY id DESC"  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
        )
    ).fetchall()

    for tablo, kolon, anahtar, eski, yeni in kayitlar:
        if tablo == "topic_hierarchy":
            continue  # pasiflestirme kayitlari asagida toplu islenir
        if tablo == "dungeon_progress":
            b.execute(
                sa.text(
                    "UPDATE dungeon_progress SET topic_id = :eski WHERE user_id = :a AND topic_id = :yeni"
                ),
                {"eski": eski, "yeni": yeni, "a": anahtar},
            )
        else:
            b.execute(
                sa.text(
                    f'UPDATE "{tablo}" SET "{kolon}" = :eski WHERE "id"::text = :a AND "{kolon}" = :yeni'  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
                ),
                {"eski": eski, "yeni": yeni, "a": anahtar},
            )

    b.execute(
        sa.text(
            f"""
            UPDATE topic_hierarchy SET is_active = true, updated_at = now()
             WHERE id IN (SELECT satir_anahtar FROM {_GUNLUK}
                           WHERE tablo = 'topic_hierarchy' AND kolon = 'is_active')
            """  # noqa: S608 -- bkz. modul basi: sabit tablo/kolon adi, veri bagli parametre  # nosec B608
        )
    )
    b.execute(sa.text(f"DROP TABLE {_GUNLUK}"))
    b.execute(sa.text(_SAYAC_SQL))
