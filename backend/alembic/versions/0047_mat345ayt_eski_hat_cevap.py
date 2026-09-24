"""345 AYT Matematik eski hat satirlarini kitabin BASILI cevap satirina hizalar

Revision ID: 0047_mat345ayt_eski_cevap
Revises: 0046_mat345ayt_kaynak_adi
Create Date: 2026-09-24

BAGLAM
------
345 2025 AYT Matematik ithalinde mukerrer taramasi, eski hattan gelen,
AKTIF ve PUBLIC 3 satirin kitabin kendi basili anahtariyla CELISTIGINI
buldu (govde kelime Jaccard >= 0.77 ve bes sikkin besi birebir):

    satir     kaynak                               DB   basili serit
    d2b4fdfc  345 2024 Ayt Matematik  s15 sag 13   B    C
    af48fac5  345 2025 Ayt Matematik  s27 sol 5    A    C
    ada94c26  345 2025 Ayt Matematik  s76 sol 1    D    C

Sahip karari (24 Eyl 2026, 345 TYT icin verildi, ayni kural): "kitabin
basili cevabi baz alinir" (0044 ile ayni desen).

KANIT (soru cozulmedi)
----------------------
* Basili serit her satirin KENDI baskisinda 6x en-yakin-komsu buyutmeyle
  gozle okundu: 2024 s15 sag '12.C 13.C 14.C 15.E'; 2025 s27 sol '5.C 6.C';
  2025 s76 sol '1.C 2.E 3.B 4.B'. 2025 baskisinin s15 sag seridi de
  '13.C' basiyor (iki okuma, bu ithal).
* ada94c26'da eski hattin METNI basili sorudan farkli: basili esitsizlik
  '> 0' (her iki baskida da, sayfa gorseli), eski hat '\\ge 0' yazmis; eski
  cevap o BOZUK metnin cevabi. Yalniz bu ifade parcasi basili hale getirilir:
      ada94c26  $\\frac{x^2+3x}{4-x} \\ge 0$  ->  $\\frac{x^2+3x}{4-x} > 0$
  Sikler (besi de basiliyla ayni) ve gorsel URL'si DEGISMEZ. soru_hash ayni
  formulle (metin_olcum.soru_hash) yeniden hesaplanmis degerine cekilir;
  yeni hash aktif satirlarla CAKISMIYOR (olculdu).
* af48fac5'in explanation alani eski hattin cozum ozeti ve basili cevapla
  celisen sonuca ('en az 3') variyor; NULL yapilir. d2b4fdfc'nin aciklamasi
  sonuc degeri icermeyen yontem cumlesi; dokunulmaz.

CERRAHI KAPSAM
--------------
Guncelleme yalniz id + mevcut soru_hash + mevcut correct_answer UCU BIRDEN
beklenen degerdeyse uygulanir; metin parcasi tam bir kez gecmelidir. Biri
tutmazsa satir ATLANIR ve loglanir (0028 / 0044 deseni).

GERI ALINABILIR
---------------
Onceki cevap, metin, hash ve aciklama GUNLUK'e yazilir; downgrade tam olarak
onlari geri koyar ve eklenen metadata anahtarini siler.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0047_mat345ayt_eski_cevap"
down_revision: Union[str, None] = "0046_mat345ayt_kaynak_adi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mat345ayt_eski_cevap_gunlugu_0047"
META_ANAHTARI = "cevap_duzeltme_0047"

# (id, eski_hash, yeni_hash, eski_cevap, yeni_cevap, eski_parca, yeni_parca,
#  aciklamayi_sil, kaynak)
DUZELTMELER: tuple[
    tuple[str, str, str, str, str, str | None, str | None, bool, str], ...
] = (
    (
        "d2b4fdfc-fb70-5a1a-8e0d-a0be32fa0154",
        "4c13fc6dbbe42b47e57a9af716b3995e",  # pragma: allowlist secret
        "4c13fc6dbbe42b47e57a9af716b3995e",  # pragma: allowlist secret
        "B",
        "C",
        None,
        None,
        False,
        "345_2024_ayt_matematik_s15_sag_serit_13C__345_2025_s15_sag_serit_13C",
    ),
    (
        "af48fac5-4031-5ba8-b451-aef329e794c8",
        "5e1760381d638f6515eec9b5384c1c42",  # pragma: allowlist secret
        "5e1760381d638f6515eec9b5384c1c42",  # pragma: allowlist secret
        "A",
        "C",
        None,
        None,
        True,
        "345_2025_ayt_matematik_s27_sol_serit_5C",
    ),
    (
        "ada94c26-9a41-5f37-8648-2a7764d09e20",
        "61ef0ef93f5e28be7e09953be5d6790c",  # pragma: allowlist secret
        "88adb43447ff65f4d913500f9ffbc0fb",  # pragma: allowlist secret
        "D",
        "C",
        "$\\frac{x^2+3x}{4-x} \\ge 0$",
        "$\\frac{x^2+3x}{4-x} > 0$",
        False,
        "345_2025_ayt_matematik_s76_sol_serit_1C__345_2024_s76_sol_serit_1C",
    ),
)

_SEC_SQL = """
SELECT qc.correct_answer, qc.question_text, qc.explanation
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
                  CAST(:anahtar AS text),
                  jsonb_build_object(
                    'eski', CAST(:eski AS text),
                    'yeni', CAST(:yeni AS text),
                    'kaynak', CAST(:kaynak AS text),
                    'metin_duzeltildi', CAST(:metin AS boolean),
                    'aciklama_silindi', CAST(:sil AS boolean),
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


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0047] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0047] soru tablolari yok (taze DB?) -- atlandi")
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_cevap", sa.String(), nullable=True),
        sa.Column("onceki_metin", sa.Text(), nullable=True),
        sa.Column("onceki_hash", sa.String(), nullable=True),
        sa.Column("onceki_aciklama", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    degisen = 0
    for sid, eh, yh, ec, yc, ep, yp, sil, kaynak in DUZELTMELER:
        satir = b.execute(sa.text(_SEC_SQL), {"id": sid, "hash": eh}).fetchone()
        if satir is None:
            _log.info("[0047] %s bulunamadi (id/hash tutmadi) -- atlandi", sid[:8])
            continue
        cevap, metin, aciklama = satir
        if cevap != ec:
            _log.info("[0047] %s cevabi %r, beklenen %r -- ATLANDI", sid[:8], cevap, ec)
            continue
        yeni_metin = metin
        if ep is not None:
            if metin.count(ep) != 1:
                _log.info("[0047] %s metin parcasi tam bir kez yok -- ATLANDI", sid[:8])
                continue
            yeni_metin = metin.replace(ep, yp)
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, onceki_cevap, onceki_metin, "  # noqa: S608  # nosec B608
                "onceki_hash, onceki_aciklama) VALUES (:id, :c, :m, :h, :a)"
            ),
            {"id": sid, "c": cevap, "m": metin, "h": eh, "a": aciklama},
        )
        b.execute(
            sa.text(
                "UPDATE question_content SET correct_answer = :c, question_text = :m, "
                "explanation = CASE WHEN :sil THEN NULL ELSE explanation END "
                "WHERE id = :id"
            ),
            {"id": sid, "c": yc, "m": yeni_metin, "sil": sil},
        )
        b.execute(
            sa.text("UPDATE question_bank SET soru_hash = :h WHERE id = :id"),
            {"id": sid, "h": yh},
        )
        b.execute(
            _META_EKLE,
            {
                "id": sid,
                "anahtar": META_ANAHTARI,
                "eski": ec,
                "yeni": yc,
                "kaynak": kaynak,
                "metin": ep is not None,
                "sil": sil,
            },
        )
        _log.info("[0047] %s: %s -> %s (%s)", sid[:8], ec, yc, kaynak)
        degisen += 1
    _log.info("[0047] duzeltilen satir: %s / %s", degisen, len(DUZELTMELER))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0047] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    sorgu = f"SELECT id, onceki_cevap, onceki_metin, onceki_hash, onceki_aciklama FROM {GUNLUK}"  # noqa: S608  # nosec B608
    kayitlar = b.execute(sa.text(sorgu)).fetchall()
    for sid, cevap, metin, h, aciklama in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_content SET correct_answer = :c, question_text = :m, "
                "explanation = :a WHERE id = :id"
            ),
            {"id": sid, "c": cevap, "m": metin, "a": aciklama},
        )
        b.execute(
            sa.text("UPDATE question_bank SET soru_hash = :h WHERE id = :id"),
            {"id": sid, "h": h},
        )
        b.execute(
            sa.text(
                "UPDATE question_metadata"
                " SET pipeline_metadata = (pipeline_metadata::jsonb - :a)::json"
                " WHERE id = :id"
            ),
            {"id": sid, "a": META_ANAHTARI},
        )
    _log.info("[0047] geri alindi: %s satir", len(kayitlar))
    op.drop_table(GUNLUK)
    _refresh_safe_for_beta(b)
