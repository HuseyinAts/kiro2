"""Eski Dilbilgisi satirlarindaki iki yanlis cevabi basili anahtara gore duzeltir

Revision ID: 0028_dilbilgisi_cevap
Revises: 0027_dilbilgisi_beta
Create Date: 2026-09-16

BAGLAM
------
"Aktif Ogrenme Tyt Dilbilgisi Soru Bankasi 2025" kitabindan DB'de eski bir
hattan (kiro2_batch_v4.14e / y11_tur_tyt_20260907) gelen 17 satir var.
Bunlar 0025/0026 ithalinde bilerek ATLANDI (kullanici karari: "dokunma,
yeni ithal onlari atlasin") ve halen is_active=1, is_public=1.

Ithal sirasinda bu 17 satir UCUNCU BAGIMSIZ KANAL olarak kullanildi: her
biri kelime kumesi ortusmesi 1.00 ile tek bir basili soruya eslesti ve
cevaplari kitabin basili cevap seridiyle karsilastirildi.

    15 satir bu kanalda eslesti  ->  13 cevap UYUSTU, 2 cevap FARKLI

FARKLI OLAN IKI SATIR
---------------------
    s033 soru 4 -- DB "A"  |  basili serit "B"
    s107 soru 6 -- DB "C"  |  basili serit "E"

Her iki serit de UC KEZ okundu; sonuncusu 5x buyutmede, sayfanin kendi
numarasi (33 / 107) ayni kirpimda gorunur haldeyken:

    s033 serit: Soru 1/B  Soru 2/D  Soru 3/E  Soru 4/B  Soru 5/D  Soru 6/E
    s107 serit: Soru 1/A  Soru 2/B  Soru 3/C  Soru 4/E  Soru 5/D  Soru 6/E

SECENEK SIRASI DA DOGRULANDI
----------------------------
Harf esleme ancak secenekler ayni sirada ise anlamlidir; ikisi de olculdu:

    58238cd6...  A=I  B=II  C=III  D=IV  E=V     (basili sayfayla ayni)
    e0afeff6...  A=1  B=2   C=3    D=4   E=5     (basili sayfayla ayni)

Yani A->B "I yerine II", C->E "3 yerine 5" demektir.

URUN KARARI DEGISMEDI
---------------------
"Sorulari tekrar cozme, cevap anahtarina guven" kurali gecerlidir; bu
migration sorulari COZMEZ. Yaptigi tek sey, DB'deki degeri kitabin kendi
basili anahtarina HIZALAMAKTIR. Eski satirlarin gerisine (metin, sik,
konu, metadata) DOKUNULMAZ.

NEDEN SIMDI
-----------
Bu iki satir is_active=1 VE is_public=1; yani ogrenciye su anda YANLIS
cevap donuyorlar. 0027 ile kitabin 644 sorusu acilirken bu iki satirin
yanlis kalmasi, ayni kitabin iki farkli dogruluk standardina sahip olmasi
demek olurdu.

CERRAHI KAPSAM VE UC KATLI KORUMA
---------------------------------
Guncelleme yalnizca su UC kosulun AYNI ANDA tuttugu satira uygulanir:

    1. id      -- tam eslesme
    2. soru_hash -- metin+sik icerigi degismemis olmali
    3. mevcut correct_answer -- beklenen ESKI deger olmali

Herhangi biri tutmazsa o satir ATLANIR ve loglanir. Bu, satir bu
migration'dan once elle duzeltilmisse ya da icerigi degismisse sessiz bir
uzerine yazma OLMAMASINI garanti eder.

GERI ALINABILIR
---------------
Onceki deger GUNLUK'e yazilir; downgrade() tam olarak onu geri koyar ve
eklenen metadata anahtarini siler.

Revizyon adi 21 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0028_dilbilgisi_cevap"
down_revision: Union[str, None] = "0027_dilbilgisi_beta"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "dilbilgisi_cevap_duzeltme_gunlugu_0028"

META_ANAHTARI = "cevap_duzeltme_0028"

# (id, soru_hash, eski_cevap, yeni_cevap, serit_kaynagi)
# Her satirin dogrulamasi bu dosyanin basligindaki "FARKLI OLAN IKI SATIR"
# bolumunde; serit uc kez okundu, secenek sirasi ayrica dogrulandi.
DUZELTMELER: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "58238cd6-4737-52b1-9443-0432a4c2dc96",
        "f8f35660dfcf79ddd3b7e3ba26022e5f",  # pragma: allowlist secret
        "A",
        "B",
        "basili_cevap_seridi_s033_soru4",
    ),
    (
        "e0afeff6-6c8f-5790-ab22-f42e1ef4421a",
        "46bb7f05cd8734a900cf4634dfad7c31",  # pragma: allowlist secret
        "C",
        "E",
        "basili_cevap_seridi_s107_soru6",
    ),
)

_SEC_SQL = """
SELECT qc.correct_answer
  FROM question_content qc
  JOIN question_bank qb ON qb.id = qc.id
 WHERE qc.id = :id AND qb.soru_hash = :hash
"""

_META_EKLE = sa.text(
    """
    UPDATE question_metadata
       SET pipeline_metadata = (
             pipeline_metadata::jsonb
             || jsonb_build_object(
                  :anahtar,
                  jsonb_build_object(
                    'eski', CAST(:eski AS text),
                    'yeni', CAST(:yeni AS text),
                    'kaynak', CAST(:kaynak AS text),
                    'okuma_sayisi', 3,
                    'soru_cozulmedi', true))
           )::json
     WHERE id = :id
    """
)


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_content", "question_metadata")
    )


def _gunlugu_kur() -> None:
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_cevap", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0028] soru tablolari yok (taze DB?) -- atlandi")
        return

    _gunlugu_kur()
    degisen = 0
    for sid, shash, eski, yeni, kaynak in DUZELTMELER:
        mevcut = b.execute(sa.text(_SEC_SQL), {"id": sid, "hash": shash}).scalar()
        if mevcut is None:
            _log.info("[0028] %s bulunamadi (id/hash tutmadi) -- atlandi", sid[:8])
            continue
        if mevcut != eski:
            _log.info(
                "[0028] %s cevabi %r, beklenen %r -- ATLANDI (elle degismis olabilir)",
                sid[:8],
                mevcut,
                eski,
            )
            continue
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, onceki_cevap)"  # noqa: S608  # nosec B608
                " VALUES (:id, :cev)"
            ),
            {"id": sid, "cev": mevcut},
        )
        b.execute(
            sa.text(
                "UPDATE question_content SET correct_answer = :yeni WHERE id = :id"
            ),
            {"id": sid, "yeni": yeni},
        )
        b.execute(
            _META_EKLE,
            {
                "id": sid,
                "anahtar": META_ANAHTARI,
                "eski": eski,
                "yeni": yeni,
                "kaynak": kaynak,
            },
        )
        _log.info("[0028] %s: %s -> %s (%s)", sid[:8], eski, yeni, kaynak)
        degisen += 1

    _log.info("[0028] duzeltilen satir: %s / %s", degisen, len(DUZELTMELER))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0028] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(f"SELECT id, onceki_cevap FROM {GUNLUK}")  # noqa: S608  # nosec B608
    ).fetchall()
    for sid, cev in kayitlar:
        b.execute(
            sa.text("UPDATE question_content SET correct_answer = :cev WHERE id = :id"),
            {"id": sid, "cev": cev},
        )
        b.execute(
            sa.text(
                "UPDATE question_metadata"
                " SET pipeline_metadata = (pipeline_metadata::jsonb - :a)::json"
                " WHERE id = :id"
            ),
            {"id": sid, "a": META_ANAHTARI},
        )

    _log.info("[0028] geri alindi: %s satir eski cevabina dondu", len(kayitlar))
    op.drop_table(GUNLUK)
