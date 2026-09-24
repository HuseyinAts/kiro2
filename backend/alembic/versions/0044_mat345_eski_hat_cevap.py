"""345 TYT Matematik eski hat satirlarini kitabin BASILI cevap satirina hizalar

Revision ID: 0044_mat345_eski_hat_cevap
Revises: 0043_mat345tyt_kaynak_adi
Create Date: 2026-09-24

BAGLAM
------
345 2025 TYT Matematik ithalinde (PR #331) mukerrer taramasi, eski hattan
(kiro2_batch_v4.14e / gemini ve bayes coklu-model) gelen, AKTIF ve PUBLIC
4 satirin kitabin kendi basili anahtariyla CELISTIGINI buldu (govde kelime
Jaccard >= 0.9 ve bes sikkin besi birebir):

    satir     kaynak                               DB   basili serit
    b5aa8e19  345 2024 Tyt Matematik  s117 sol 9    D    C
    a4919225  345 2024 Tyt Matematik  s117 sag 13   E    B
    2c50e760  345 2024 Tyt Matematik  s172 sol 1    C    B
    58e3f697  345 2025 TYT Matematik  s346 sol 2    B    D

Sahip karari (24 Eyl 2026): "kitabin basili cevabi baz alinir".

KANIT (soru cozulmedi)
----------------------
* Basili serit her satirin KENDI baskisinda 6x en-yakin-komsu kontrast
  buyutmesiyle gozle okundu: 2024 s117 sol '9.C 10.D 11.A 12.E', sag
  '13.B 14.B 15.D', s172 sol '1.B 2.E'; 2025 s346 sol '1.E 2.D 3.B 4.C 5.E'.
  2025 baskisinin ayni sayfalari da ayni harfleri basiyor (iki okuma, PR #331).
* Uc satirda eski hattin METNI de basili sorudan farkli (mutlak deger
  cubuklari / '+' isareti kaybolmus); eski cevap o BOZUK metnin cevabi.
  Yalniz cevabi degistirmek, ekranda gorunen soru ile anahtari celistirirdi.
  Bu yuzden bu uc satirda yalniz bozuk ifade parcasi, sayfa gorseliyle
  karsilastirilarak basili hale getirilir:
      b5aa8e19  $3-|x-1|=1$                ->  $|3-|x-1||=1$
      a4919225  $|a| = 2b$ ... $4b-a=6$     ->  $|a| = |2b|$ ... $4b-|a|=6$
      58e3f697  $xy = \\text{EBOB}(x, y) = 57$ ->  $xy + \\text{EBOB}(x, y) = 57$
  Sikler (besi de basiliyla ayni) ve gorsel URL'si DEGISMEZ. Metin degisen
  satirda soru_hash ayni formulle (metin_olcum.soru_hash) yeniden hesaplanmis
  degerine cekilir; yeni hash'ler aktif satirlarla CAKISMIYOR (olculdu).
* 2c50e760'in explanation alani yalniz eski hattin tahmin notu ('Dogru
  cevap: C (Guven: %98 ...)'); yeni cevapla celistigi icin NULL yapilir.

CERRAHI KAPSAM
--------------
Guncelleme yalniz id + mevcut soru_hash + mevcut correct_answer UCU BIRDEN
beklenen degerdeyse uygulanir; metin parcasi tam bir kez gecmelidir. Biri
tutmazsa satir ATLANIR ve loglanir (0028 deseni).

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

revision: str = "0044_mat345_eski_hat_cevap"
down_revision: Union[str, None] = "0043_mat345tyt_kaynak_adi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mat345_eski_hat_cevap_gunlugu_0044"
META_ANAHTARI = "cevap_duzeltme_0044"
_UZERE = "olmak " + chr(0x00FC) + "zere"

# (id, eski_hash, yeni_hash, eski_cevap, yeni_cevap, eski_parca, yeni_parca,
#  aciklamayi_sil, kaynak)
DUZELTMELER: tuple[
    tuple[str, str, str, str, str, str | None, str | None, bool, str], ...
] = (
    (
        "b5aa8e19-7658-5f96-98b8-a9c8f6e5b918",
        "a44de53c95a5016792450b7be5adcac6",  # pragma: allowlist secret
        "a51fb90700911f198f782878915a8379",  # pragma: allowlist secret
        "D",
        "C",
        "$3-|x-1|=1$",
        "$|3-|x-1||=1$",
        False,
        "345_2024_tyt_matematik_s117_sol_serit_9C__345_2025_s117_sol_serit_9C",
    ),
    (
        "a4919225-930d-52d5-93a4-063c300b3a82",
        "590bfc45dfb9ef2386257e79e65a0c52",  # pragma: allowlist secret
        "e2078af076d2fd9c1a85da7ccae7d138",  # pragma: allowlist secret
        "E",
        "B",
        "$|a| = 2b$ " + _UZERE + " $4b-a=6$",
        "$|a| = |2b|$ " + _UZERE + " $4b-|a|=6$",
        False,
        "345_2024_tyt_matematik_s117_sag_serit_13B__345_2025_s117_sag_serit_13B",
    ),
    (
        "2c50e760-7d21-53d4-a843-ad267371e5d6",
        "3f35cdc52e7205e638f13bd494b79af7",  # pragma: allowlist secret
        "3f35cdc52e7205e638f13bd494b79af7",  # pragma: allowlist secret
        "C",
        "B",
        None,
        None,
        True,
        "345_2024_tyt_matematik_s172_sol_serit_1B__345_2025_s172_sol_serit_1B",
    ),
    (
        "58e3f697-aa25-5be1-a52e-06c95e396a8a",
        "451ac317bbb1ef27dc559b7133f9f9e4",  # pragma: allowlist secret
        "012d4d73c1cb9bc008733d95ad56b3d6",  # pragma: allowlist secret
        "B",
        "D",
        "$xy = \\text{EBOB}(x, y) = 57$",
        "$xy + \\text{EBOB}(x, y) = 57$",
        False,
        "345_2025_tyt_matematik_s346_sol_serit_2D",
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
        _log.info("[0044] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0044] soru tablolari yok (taze DB?) -- atlandi")
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
            _log.info("[0044] %s bulunamadi (id/hash tutmadi) -- atlandi", sid[:8])
            continue
        cevap, metin, aciklama = satir
        if cevap != ec:
            _log.info("[0044] %s cevabi %r, beklenen %r -- ATLANDI", sid[:8], cevap, ec)
            continue
        yeni_metin = metin
        if ep is not None:
            if metin.count(ep) != 1:
                _log.info("[0044] %s metin parcasi tam bir kez yok -- ATLANDI", sid[:8])
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
        _log.info("[0044] %s: %s -> %s (%s)", sid[:8], ec, yc, kaynak)
        degisen += 1
    _log.info("[0044] duzeltilen satir: %s / %s", degisen, len(DUZELTMELER))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0044] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0044] geri alindi: %s satir", len(kayitlar))
    op.drop_table(GUNLUK)
    _refresh_safe_for_beta(b)
