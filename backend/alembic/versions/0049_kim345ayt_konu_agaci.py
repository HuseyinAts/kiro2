"""345 2025 AYT Kimya Soru Bankasi: kitabin kendi konu agaci (KIM-345A25).

Revision ID: 0049_kim345ayt_agac
Revises: 0048_mat345ayt_ikinci_okuma
Create Date: 2026-09-25

NEDEN
-----
Bu kitabin ithali her soruyu bir konu ya da unite dugumune baglar. KIM
kokunun altinda yalniz genel KIM.ASI / KIM.DEN / KIM.ORG / KIM.TER dugumleri
var; kitabin 12 unitesi ve 50 konusu (or. 'Atomun Kuantum Modeli', 'Sulu
Cozelti Dengeleri', 'Hidrokarbonlar / Alkinler') onlarla birebir ortusmuyor.
Sessizce "en yakin" dugume baglamak yanlis veridir; bu migration kitabin
agacini KIM-345A25 onekiyle ayri bir alt agac olarak kurar (0045 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_ayt_kimya_konu_haritasi.json`
ile BIREBIR aynidir (ASCII katlanmis); o dosya:
  * 12 unite + 50 konu + baslangic sayfalari: kitabin KENDI icindekiler
    sayfalari (dosya 3-4); unite ayraci sayfalari 5, 39, ..., 325.
  * Bagimsiz dogrulama: 160 testin 160'i tek bir icindekiler araligina
    dusuyor; 100 Kazanim Odakli testin 100'unde bant basligi == konu adi.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Unite kok+1, konu kok+2. Kazanim Odakli testler (100 test, 834 soru) KONU
dugumune, OSYM Tadinda ve Orijinal testler (60 test, 470 soru) UNITE
dugumune baglanir: bu testler kitapta unite sonunda, uniteyi bir butun
olarak yoklar; konuya dagitmak uydurma olurdu.

12 unite + 50 konu = 62 dugum.

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

revision: str = "0049_kim345ayt_agac"
down_revision: Union[str, None] = "0048_mat345ayt_ikinci_okuma"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "kim345ayt_konu_gunlugu_0049"
KIM_KOK_KODU = "KIM"
KOD_ONEKI = "KIM-345A25"

# (kod, ad)
UNITELER: tuple[tuple[str, str], ...] = (
    ("KIM-345A25-U01", "Modern Atom Teorisi"),
    ("KIM-345A25-U02", "Gazlar"),
    ("KIM-345A25-U03", "Sivi Cozeltiler ve Cozunurluk"),
    ("KIM-345A25-U04", "Kimyasal Tepkimelerde Enerji"),
    ("KIM-345A25-U05", "Kimyasal Tepkimelerde Hiz"),
    ("KIM-345A25-U06", "Kimyasal Tepkimelerde Denge"),
    ("KIM-345A25-U07", "Sulu Cozelti Dengeleri"),
    ("KIM-345A25-U08", "Kimya ve Elektrik"),
    ("KIM-345A25-U09", "Karbon Kimyasina Giris"),
    ("KIM-345A25-U10", "Organik Bilesikler - 1"),
    ("KIM-345A25-U11", "Organik Bilesikler - 2"),
    ("KIM-345A25-U12", "Enerji Kaynaklari ve Bilimsel Gelismeler"),
)

# (ust unite kodu, kod, ad)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("KIM-345A25-U01", "KIM-345A25-U01-01", "Atomun Kuantum Modeli"),
    ("KIM-345A25-U01", "KIM-345A25-U01-02", "Elektron Dizilimleri"),
    ("KIM-345A25-U01", "KIM-345A25-U01-03", "Periyodik Ozellikler"),
    ("KIM-345A25-U01", "KIM-345A25-U01-04", "Elementleri Taniyalim"),
    ("KIM-345A25-U01", "KIM-345A25-U01-05", "Yukseltgenme Basamaklari"),
    ("KIM-345A25-U02", "KIM-345A25-U02-01", "Gazlarin Ozellikleri"),
    ("KIM-345A25-U02", "KIM-345A25-U02-02", "Gaz Yasalari"),
    ("KIM-345A25-U02", "KIM-345A25-U02-03", "Ideal Gaz Yasasi"),
    ("KIM-345A25-U02", "KIM-345A25-U02-04", "Gazlarda Kinetik Teori"),
    ("KIM-345A25-U02", "KIM-345A25-U02-05", "Gaz Karisimlari"),
    ("KIM-345A25-U02", "KIM-345A25-U02-06", "Gercek Gazlar"),
    ("KIM-345A25-U03", "KIM-345A25-U03-01", "Cozucu - Cozunen Etkilesimleri"),
    ("KIM-345A25-U03", "KIM-345A25-U03-02", "Derisim Birimleri"),
    ("KIM-345A25-U03", "KIM-345A25-U03-03", "Koligatif Ozellikler"),
    ("KIM-345A25-U03", "KIM-345A25-U03-04", "Cozunurluk"),
    ("KIM-345A25-U03", "KIM-345A25-U03-05", "Cozunurluge Etki Eden Faktorler"),
    ("KIM-345A25-U04", "KIM-345A25-U04-01", "Tepkimelerde Isi Degisimi"),
    ("KIM-345A25-U04", "KIM-345A25-U04-02", "Entalpi Turleri"),
    ("KIM-345A25-U04", "KIM-345A25-U04-03", "Bag Enerjileri"),
    ("KIM-345A25-U04", "KIM-345A25-U04-04", "Tepkime Isilarinin Toplanabilirligi"),
    ("KIM-345A25-U05", "KIM-345A25-U05-01", "Kimyasal Tepkimeler ve Carpisma Teorisi"),
    ("KIM-345A25-U05", "KIM-345A25-U05-02", "Tepkime Hizi"),
    ("KIM-345A25-U05", "KIM-345A25-U05-03", "Tepkime Hizini Etkileyen Faktorler"),
    ("KIM-345A25-U06", "KIM-345A25-U06-01", "Kimyasal Denge"),
    ("KIM-345A25-U06", "KIM-345A25-U06-02", "Dengeyi Etkileyen Faktorler"),
    ("KIM-345A25-U07", "KIM-345A25-U07-01", "Asit - Baz"),
    ("KIM-345A25-U07", "KIM-345A25-U07-02", "Cozunurluk Dengesi"),
    ("KIM-345A25-U08", "KIM-345A25-U08-01", "Indirgenme - Yukseltgenme Tepkimeleri"),
    ("KIM-345A25-U08", "KIM-345A25-U08-02", "Metalik Aktiflik"),
    (
        "KIM-345A25-U08",
        "KIM-345A25-U08-03",
        "Elektrokimyasal Hucreler ve Elektrot Potansiyelleri",
    ),
    ("KIM-345A25-U08", "KIM-345A25-U08-04", "Elektroliz"),
    ("KIM-345A25-U09", "KIM-345A25-U09-01", "Organik ve Anorganik Bilesikler"),
    ("KIM-345A25-U09", "KIM-345A25-U09-02", "Basit ve Molekul Formul"),
    ("KIM-345A25-U09", "KIM-345A25-U09-03", "Dogada Karbon"),
    ("KIM-345A25-U09", "KIM-345A25-U09-04", "Lewis Formulleri"),
    ("KIM-345A25-U09", "KIM-345A25-U09-05", "Hibritlesme ve Molekul Geometrisi"),
    ("KIM-345A25-U10", "KIM-345A25-U10-01", "Hidrokarbonlar / Alkanlar"),
    ("KIM-345A25-U10", "KIM-345A25-U10-02", "Hidrokarbonlar / Alkenler"),
    ("KIM-345A25-U10", "KIM-345A25-U10-03", "Hidrokarbonlar / Alkinler"),
    ("KIM-345A25-U11", "KIM-345A25-U11-01", "Aromatik Bilesikler (Arenler)"),
    ("KIM-345A25-U11", "KIM-345A25-U11-02", "Fonksiyonel Gruplar"),
    ("KIM-345A25-U11", "KIM-345A25-U11-03", "Alkoller"),
    ("KIM-345A25-U11", "KIM-345A25-U11-04", "Eterler"),
    ("KIM-345A25-U11", "KIM-345A25-U11-05", "Karbonil Bilesikleri"),
    ("KIM-345A25-U11", "KIM-345A25-U11-06", "Karboksilik Asitler"),
    ("KIM-345A25-U11", "KIM-345A25-U11-07", "Esterler"),
    ("KIM-345A25-U12", "KIM-345A25-U12-01", "Fosil Yakitlar"),
    ("KIM-345A25-U12", "KIM-345A25-U12-02", "Alternatif Enerji Kaynaklari"),
    ("KIM-345A25-U12", "KIM-345A25-U12-03", "Surdurulebilirlik"),
    ("KIM-345A25-U12", "KIM-345A25-U12-04", "Nanoteknoloji"),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'KIMYA', TRUE, now(), now())
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
    "345 2025 AYT Kimya Soru Bankasi'nin kendi icindekiler sayfalarindan "
    "(dosya 3-4) uretildi (0049)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0049] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0049] mv_safe_for_beta yenilendi")


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
        _log.info("[0049] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KIM_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0049] %s kok konusu yok -- atlandi", KIM_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz KIM-345A25 deseni; KIM.* genel dugumlerine DOKUNULMAZ. LIKE deseni
    # '-' ile biter ki KIM-345A250 gibi bir onek yanlislikla eslesmesin.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }

    kimlik: dict[str, str] = {}

    def _id_al(kod: str) -> str:
        mevcut_id: str = b.execute(
            sa.text("SELECT id FROM topic_hierarchy WHERE code = :k"), {"k": kod}
        ).scalar_one()
        return mevcut_id

    eklenen = 0
    for kod, ad in UNITELER:
        if kod in mevcut:
            kimlik[kod] = _id_al(kod)
            continue
        kimlik[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    for ust, kod, ad in KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, kimlik[ust])
        eklenen += 1

    _log.info(
        "[0049] %s unite + %s konu tanimi; bu kosumda eklenen dugum: %s",
        len(UNITELER),
        len(KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0049] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0049] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Once yapraklar (konu), sonra uniteler: cocugu olan silinmez.
        for _ in range(2):
            b.execute(
                sa.text(
                    "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                    "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                    "WHERE c.parent_id = topic_hierarchy.id)"
                ),
                {"idler": idler},
            )
    op.drop_table(GUNLUK)
    _log.info("[0049] downgrade tamam; silinmeye aday dugum: %s", len(idler))
