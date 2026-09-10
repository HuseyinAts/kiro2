"""Neofizik AYT Fizik soru bankasi icin FIZ alt konu agacini kurar

Revision ID: 0013_neofizik_konu_agaci
Revises: 0012_osym_sikki_bos_pasif
Create Date: 2026-09-10

BAGLAM
------
FIZ koku bugune kadar tek bir alt dugume sahipti (FIZ-OSYM-GENEL,
"siniflandirilmamis"). 0011'in kapanis notunda "yaprak duzeyde konu
siniflandirmasi" ayri bir is olarak birakilmisti.

Neofizik AYT Fizik Soru Bankasi 2025'in kendi icindekiler sayfasi bu
siniflandirmayi HAZIR veriyor: 6 bolum, altinda 44 konu, her konunun
sayfa araligi belli. OCR hatti her soruyu zaten bu konuya bagli olarak
uretti (bkz. veriseti/zkitap/cikti/YONTEM.md). Bu migration o agaci
topic_hierarchy'ye kurar; ithal script'i (scripts/kitap/neofizik_ithal.py)
sorulari YAPRAGA baglar -- kok'e degil.

NEDEN MIGRATION, NEDEN SCRIPT DEGIL
-----------------------------------
Konu agaci referans veridir (schema-benzeri): her ortamda ayni olmali,
surumlenmeli ve geri alinabilmeli. Sorularin kendisi ise ithal script'iyle
gelir (buyuk, ortama gore degisen, git disi veri). 0011/0012 ile ayni ayrim.

IDEMPOTENT
----------
Var olan kodlar ATLANIR. Olusturulan her dugumun id'si GUNLUK'e yazilir;
downgrade() yalnizca KENDI olusturdugu ve hicbir soru tarafindan
kullanilmayan dugumleri siler (kullanilan varsa dokunmaz ve loglar).

Kodlar: FIZ-NEO-B<bolum> (level 2) ve FIZ-NEO-B<bolum>-<KONU> (level 3).
topic_hierarchy.code varchar(50) oldugu icin konu kodu 50 karakterde
kesilir -- ithal script'indeki konu_kodu() ile birebir ayni kural.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0013_neofizik_konu_agaci"
down_revision: Union[str, None] = "0012_osym_sikki_bos_pasif"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "neofizik_konu_gunlugu_0013"
FIZ_KOK_KODU = "FIZ"

BOLUMLER: tuple[tuple[int, str, str], ...] = (
    (1, "FIZ-NEO-B1", "Kuvvet, Hareket ve Enerji: Fizikte Temel Ilkeler"),
    (2, "FIZ-NEO-B2", "Elektrik ve Manyetizma: Doganin Gorunmez Gucleri"),
    (3, "FIZ-NEO-B3", "Hareket ve Kuvvet: Evrenin Dinamigi"),
    (4, "FIZ-NEO-B4", "Dalga Mekanigi: Dalgalarin Dunyasina Yolculuk"),
    (5, "FIZ-NEO-B5", "Atom Fizigi: Maddenin ve Enerjinin Sirlarini Kesfetmek"),
    (6, "FIZ-NEO-B6", "Modern Fizigin Temelleri: Madde ve Isigin Gizemli Dunyasi"),
)

KONULAR: tuple[tuple[int, str, str], ...] = (
    (1, "FIZ-NEO-B1-BAGIL-HAREKET", "Bagil Hareket"),
    (1, "FIZ-NEO-B1-BASIT-MAKINELER", "Basit Makineler"),
    (1, "FIZ-NEO-B1-BIR-BOYUTTA-SABIT-IVMELI-HAREKET", "Bir Boyutta Sabit Ivmeli Hareket"),
    (1, "FIZ-NEO-B1-DENGE", "Denge"),
    (1, "FIZ-NEO-B1-ENERJI", "Enerji"),
    (1, "FIZ-NEO-B1-IKI-BOYUTTA-SABIT-IVMELI-HAREKET", "Iki Boyutta Sabit Ivmeli Hareket"),
    (1, "FIZ-NEO-B1-ITME-VE-CIZGISEL-MOMENTUM", "Itme ve Cizgisel Momentum"),
    (1, "FIZ-NEO-B1-KUTLE-MERKEZI", "Kutle Merkezi"),
    (1, "FIZ-NEO-B1-NEWTON-UN-HAREKET-YASALARI", "Newton'un Hareket Yasalari"),
    (1, "FIZ-NEO-B1-TORK", "Tork"),
    (1, "FIZ-NEO-B1-VEKTORLER", "Vektorler"),
    (2, "FIZ-NEO-B2-ALTERNATIF-AKIM", "Alternatif Akim"),
    (2, "FIZ-NEO-B2-DUZGUN-ELEKTRIKSEL-ALAN", "Duzgun Elektriksel Alan"),
    (2, "FIZ-NEO-B2-ELEKTRIKSEL-KUVVET-VE-ELEKTRIKSEL-ALAN", "Elektriksel Kuvvet ve Elektriksel Alan"),
    (2, "FIZ-NEO-B2-ELEKTRIKSEL-POTANSIYEL-VE-ELEKTRIKSEL-P", "Elektriksel Potansiyel ve Elektriksel Potansiyel Enerji"),
    (2, "FIZ-NEO-B2-ELEKTROMANYETIK-INDUKSIYON", "Elektromanyetik Induksiyon"),
    (2, "FIZ-NEO-B2-MANYETIK-AKI", "Manyetik Aki"),
    (2, "FIZ-NEO-B2-MANYETIK-ALAN", "Manyetik Alan"),
    (2, "FIZ-NEO-B2-MANYETIK-KUVVET", "Manyetik Kuvvet"),
    (2, "FIZ-NEO-B2-SIGACLAR", "Sigaclar"),
    (2, "FIZ-NEO-B2-TRANSFORMATORLER", "Transformatorler"),
    (3, "FIZ-NEO-B3-ACISAL-MOMENTUM", "Acisal Momentum"),
    (3, "FIZ-NEO-B3-BASIT-HARMONIK-HAREKET", "Basit Harmonik Hareket"),
    (3, "FIZ-NEO-B3-CEMBERSEL-HAREKET", "Cembersel Hareket"),
    (3, "FIZ-NEO-B3-DONEREK-OTELEME-HAREKETI", "Donerek Oteleme Hareketi"),
    (3, "FIZ-NEO-B3-GENEL-CEKIM-YASASI", "Genel Cekim Yasasi"),
    (3, "FIZ-NEO-B3-KEPLER-YASASI", "Kepler Yasasi"),
    (4, "FIZ-NEO-B4-DOPPLER-OLAYI", "Doppler Olayi"),
    (4, "FIZ-NEO-B4-ELEKTROMANYETIK-DALGALAR", "Elektromanyetik Dalgalar"),
    (4, "FIZ-NEO-B4-ISIKTA-GIRISIM", "Isikta Girisim"),
    (4, "FIZ-NEO-B4-SU-DALGALARINDA-KIRINIM-VE-GIRISIM", "Su Dalgalarinda Kirinim ve Girisim"),
    (5, "FIZ-NEO-B5-ATOM-MODELLERI", "Atom Modelleri"),
    (5, "FIZ-NEO-B5-ATOMALTI-PARCACIKLAR", "Atomalti Parcaciklar"),
    (5, "FIZ-NEO-B5-BUYUK-PATLAMA-VE-EVRENIN-OLUSUMU", "Buyuk Patlama ve Evrenin Olusumu"),
    (5, "FIZ-NEO-B5-RADYOAKTIVITE", "Radyoaktivite"),
    (6, "FIZ-NEO-B6-COMPTON-SACILMASI-VE-MADDE-DALGALARI", "Compton Sacilmasi ve Madde Dalgalari"),
    (6, "FIZ-NEO-B6-FOTOELEKTRIK-ETKI", "Fotoelektrik Etki"),
    (6, "FIZ-NEO-B6-GORUNTULEME-TEKNOLOJILERI", "Goruntuleme Teknolojileri"),
    (6, "FIZ-NEO-B6-KARA-CISIM-ISIMASI", "Kara Cisim Isimasi"),
    (6, "FIZ-NEO-B6-LAZER", "Lazer"),
    (6, "FIZ-NEO-B6-NANOTEKNOLOJI", "Nanoteknoloji"),
    (6, "FIZ-NEO-B6-OZEL-GORELILIK", "Ozel Gorelilik"),
    (6, "FIZ-NEO-B6-SUPER-ILETKENLER", "Super Iletkenler"),
    (6, "FIZ-NEO-B6-YARI-ILETKEN-TEKNOLOJILERI", "Yari Iletken Teknolojileri"),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'FIZIK', TRUE, now(), now())
    """
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

_ACIKLAMA = (
    "Neofizik AYT Fizik Soru Bankasi 2025 icindekiler agacindan uretildi "
    "(0013_neofizik_konu_agaci)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; tekrar kosumda ayni id uretilir."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0013] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0013] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0013] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": FIZ_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0013] %s kok konusu yok -- atlandi", FIZ_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE 'FIZ-NEO-%'")
        ).fetchall()
    }

    eklenen = 0
    for level_ofset, kayitlar in ((1, BOLUMLER), (2, KONULAR)):
        for bolum_no, kod, ad in kayitlar:
            if kod in mevcut:
                continue
            ust = kok_id if level_ofset == 1 else _dugum_id(f"FIZ-NEO-B{bolum_no}")
            yeni_id = _dugum_id(kod)
            b.execute(
                _EKLE,
                {
                    "id": yeni_id,
                    "level": kok_level + level_ofset,
                    "parent_id": ust,
                    "code": kod,
                    "name_tr": ad,
                    "aciklama": _ACIKLAMA,
                },
            )
            b.execute(
                sa.text(
                    f"INSERT INTO {GUNLUK} (id, kod, olusturuldu) "  # noqa: S608  # nosec B608
                    "VALUES (:id, :kod, TRUE)"
                ),
                {"id": yeni_id, "kod": kod},
            )
            eklenen += 1

    _log.info(
        "[0013] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
        len(BOLUMLER),
        len(KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0013] %s yok -- downgrade atlandi", GUNLUK)
        return
    idler = [
        r[0]
        for r in b.execute(
            sa.text(f"SELECT id FROM {GUNLUK} WHERE olusturuldu IS TRUE")  # noqa: S608  # nosec B608
        ).fetchall()
    ]
    if idler and sa.inspect(b).has_table("question_bank"):
        kullanilan = {
            r[0]
            for r in b.execute(
                sa.text(
                    "SELECT DISTINCT primary_topic_id FROM question_bank "
                    "WHERE primary_topic_id = ANY(:idler)"
                ),
                {"idler": idler},
            ).fetchall()
        }
        if kullanilan:
            _log.warning(
                "[0013] %s dugum hala soru tasiyor -- SILINMEDI (once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # once yapraklar, sonra bolumler: alt dugumleri olan silinmez
        b.execute(
            sa.text(
                "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c WHERE c.parent_id = topic_hierarchy.id)"
            ),
            {"idler": idler},
        )
        b.execute(
            sa.text(
                "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c WHERE c.parent_id = topic_hierarchy.id)"
            ),
            {"idler": idler},
        )
        _log.info("[0013] geri alindi: %s dugum silindi", len(idler))
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
