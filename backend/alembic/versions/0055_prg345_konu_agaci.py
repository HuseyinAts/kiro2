"""345 2025 Paragraf Sifir Risk Soru Bankasi: kitabin kendi bolum agaci (TUR-345P25).

Revision ID: 0055_prg345_agac
Revises: 0054_prg345_kaynak_adi
Create Date: 2026-09-25

NEDEN
-----
Bu kitabin ithali her testi kitabin 7 bolumunden birine baglar. TUR
kokunun altindaki dugumler (TUR-BS*, TUR-D*) baska kitaplarin agaclaridir;
bu kitabin bolumleri ('Kesfet', 'Olc', 'Planla', 'Odaklan', 'Zenginlestir',
'Basar', 'Riskleri Sifirla') konu degil CALISMA ASAMASIDIR ve onlarla
ortusmez. Sessizce "en yakin" paragraf dugumune baglamak yanlis veridir; bu
migration kitabin agacini TUR-345P25 onekiyle ayri bir alt agac olarak kurar
(0053 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_paragraf_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 7 bolum: kitabin bolum ayraci sayfalari (dosya 3, 63, 123, 183, 251,
    283, 329; 'Sifir Risk 01-07' + bolum adi, gozle).
  * Bagimsiz dogrulama: 85 test bant kosusunun 85'i kitap sonu anahtarin
    test sirasiyla ayni; her testin sayfalari tek bir bolumun araliginda.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Bolum kok+1 (TUR kokunun altinda); 85 testin 1012 sorusu bolum dugumune
baglanir. 7 dugum.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0055_prg345_agac"
down_revision: Union[str, None] = "0054_prg345_kaynak_adi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "prg345_konu_gunlugu_0055"
TUR_KOK_KODU = "TUR"
KOD_ONEKI = "TUR-345P25"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    (
        "TUR-345P25-B01",
        "Ke\u015ffet: Farkl\u0131 Soru T\u00fcrleri \u0130le Tan\u0131\u015f!",
    ),
    ("TUR-345P25-B02", "\u00d6l\u00e7: Sorular\u0131 Anla, Zaman\u0131 Yakala!"),
    ("TUR-345P25-B03", "Planla: Sorular\u0131 Anla, Zaman\u0131nda Tamamla!"),
    ("TUR-345P25-B04", "Odaklan: Sadece \u0130htiyac\u0131n Olana!"),
    (
        "TUR-345P25-B05",
        "Zenginle\u015ftir: Farkl\u0131 Temalarla Kendini Geli\u015ftir!",
    ),
    ("TUR-345P25-B06", "Ba\u015far: Seviyeleri Ad\u0131m Ad\u0131m A\u015f!"),
    ("TUR-345P25-B07", "Riskleri S\u0131f\u0131rla: Sorularda Tak\u0131lma!"),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'TURKCE', TRUE, now(), now())
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
    "345 2025 Paragraf Sifir Risk Soru Bankasi'nin bolum ayraci sayfalarindan "
    "(dosya 3, 63, 123, 183, 251, 283, 329) uretildi (0055)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0055] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0055] mv_safe_for_beta yenilendi")


def _yaz(b, kod, ad, level, parent_id) -> str:
    yeni_id = _dugum_id(kod)
    b.execute(
        _EKLE,
        {
            "id": yeni_id,
            "level": level,
            "parent_id": parent_id,
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
    return yeni_id


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0055] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": TUR_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0055] %s kok konusu yok -- atlandi", TUR_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz TUR-345P25 deseni; diger TUR dugumlerine DOKUNULMAZ. LIKE deseni
    # '-' ile biter ki TUR-345P250 gibi bir onek yanlislikla eslesmesin.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }

    eklenen = 0
    for kod, ad in BOLUMLER:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    _log.info(
        "[0055] %s bolum tanimi; bu kosumda eklenen dugum: %s",
        len(BOLUMLER),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0055] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0055] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Tek duzey; cocugu olan silinmez.
        b.execute(
            sa.text(
                "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                "WHERE c.parent_id = topic_hierarchy.id)"
            ),
            {"idler": idler},
        )
    op.drop_table(GUNLUK)
    _log.info("[0055] downgrade tamam; silinmeye aday dugum: %s", len(idler))
