"""345 AYT Matematik: hedefli ikinci okumanin buldugu transkripsiyon hatalarini duzeltir

Revision ID: 0048_mat345ayt_ikinci_okuma
Revises: 0047_mat345ayt_eski_cevap
Create Date: 2026-09-24

BAGLAM
------
Sahip sorusu: "orneklem alarak tam ikinci okumaya gerek var mi yok mu karar
ver". On kayitli kural (olcumden ONCE yazildi): 210 soruluk orneklemde ilk
okumanin esasli hata oraninin 95% Clopper-Pearson ust siniri <= %3 ise tam
ikinci okuma yok; > %3 ve hatalar bir tabakada toplaniyorsa yalniz o tabaka.

    orneklem       2/210 esasli hata, ust sinir %3.40  -> esik asildi
    tabaka         iki hata da grup_11 ve sinirlayici ((, [, |) ozellikli
    tabaka disi    0/203, ust sinir %1.80
    karar          HEDEFLI ikinci okuma: grup_11 tamami + kitaptaki tum
                   sinirlayici ozellikli sorular = 362 (331 yeni okuma)

Ikinci okuyucular ilk okumayi gormedi. 541 ikinci okumanin 77'sinde fark
cikti; her fark kirpima 8x en-yakin-komsu buyutmeyle bakilarak hukme
baglandi. 10 soruda ilk okuma esasli hataliydi (aralik ucu, dogru parcasi
gosterimi, isaret, sik degeri); 4 soruda yalniz baski kusuru notu eklendi.
Tam kayit: veriseti/zkitap/cikti/345_2025_ayt_matematik_ikinci_okuma.json.
Hicbir soru cozulmedi; cevap anahtari DEGISMEDI.

NE DEGISIR
----------
* 10 satir: question_text ya da option_d icindeki TEK ifade parcasi basili
  hale getirilir; soru_hash ayni formulle (metin_olcum.soru_hash) yeniden
  hesaplanmis degerine cekilir (yeni hash'lerin hicbiri DB'de yok, olculdu);
  kelime istatistikleri ithal ile ayni fonksiyonlardan yeniden yazilir.
  id DEGISMEZ: ithal scripti bu satirlarin id'sini ikinci okuma kaydindaki
  ilk hash'e sabitler (tekrar kosuda cift satir olusmaz).
* 4 satir: pipeline_metadata.kaynak_kusuru notu genisletilir / eklenir ve
  bayraklar ithalin urettigi listeye esitlenir.
* 14 satirin hepsine pipeline_metadata.ikinci_okuma anahtari eklenir.

CERRAHI KAPSAM
--------------
Guncelleme yalniz id + mevcut soru_hash tutarsa uygulanir; metin parcasi
alanda tam bir kez gecmelidir. Biri tutmazsa satir ATLANIR ve loglanir
(0028 / 0044 / 0047 deseni). Tablolar yoksa (taze/CI DB) hicbir sey yapmaz.

GERI ALINABILIR
---------------
Onceki metin, sik, hash, istatistik ve pipeline_metadata GUNLUK'e yazilir;
downgrade tam olarak onlari geri koyar.
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0048_mat345ayt_ikinci_okuma"
down_revision: Union[str, None] = "0047_mat345ayt_eski_cevap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mat345ayt_ikinci_okuma_gunlugu_0048"
META_ANAHTARI = "ikinci_okuma"
KAYIT = "veriseti/zkitap/cikti/345_2025_ayt_matematik_ikinci_okuma.json"
KAYNAK_ADI = "345 2025 AYT Matematik Soru Bankasi"

# 10 esasli metin duzeltmesi:
# (dosya, id, eski_hash, yeni_hash, sutun, eski_parca, yeni_parca,
#  (word_count, unique_word_count, average_word_length, readability_score))
METIN: tuple[
    tuple[str, str, str, str, str, str, str, tuple[int, int, float, float]], ...
] = (
    (
        "MAT345AYT-T045_03",
        "2df02ab5-c2c7-5663-b0f8-d780dba0d407",
        "13c897d27482b773a9c3af514f34a622",  # pragma: allowlist secret
        "5c80ae91a5b9d62d924841efd003dbc7",  # pragma: allowlist secret
        "question_text",
        "2/x_((1)) + 1/1_((x))",
        "2/x + 1/1",
        (96, 66, 4.072916666666667, 96.88),
    ),
    (
        "MAT345AYT-T054_02",
        "18a1f6fa-0219-58de-ae2e-d0ade35e1800",
        "dd22573a4847b67e5ad522152dd02adf",  # pragma: allowlist secret
        "391d0afa5c9ea6301d96e85b7e566190",  # pragma: allowlist secret
        "option_d",
        "(0, 2]",
        "(0, 2)",
        (34, 30, 4.0588235294117645, 91.47),
    ),
    (
        "MAT345AYT-T058_02",
        "3359c5ec-f5e7-5abe-b98c-d23dd115f8a1",
        "d54a3705b429624e6f72e341c1aa015c",  # pragma: allowlist secret
        "dd53c22e6a61ca09347b5b6c231b5edd",  # pragma: allowlist secret
        "question_text",
        "|AD| \u22a5 |CD|\n|AC| \u22a5 |BC|",
        "[AD] \u22a5 [CD]\n[AC] \u22a5 [BC]",
        (15, 13, 4.133333333333334, 100.0),
    ),
    (
        "MAT345AYT-T060_01",
        "895c88f2-d8c5-5d3b-9277-b06675cc9243",
        "339159e3f01d0fbbc72683401806feee",  # pragma: allowlist secret
        "74dc3b23f0798017035fff1bada26a99",  # pragma: allowlist secret
        "question_text",
        "cos2x \u2212 1\n",
        "cos2x + 1\n",
        (17, 15, 4.411764705882353, 100.0),
    ),
    (
        "MAT345AYT-T060_08",
        "5f6db461-21fe-5896-a61e-d7b84af5aaa9",
        "901561d070a58a521e22d4c48c6f67a3",  # pragma: allowlist secret
        "d493f006dc3b182c2604d0fd75fa732d",  # pragma: allowlist secret
        "question_text",
        "(0, 360\u00b0]",
        "(0, 360\u00b0)",
        (16, 15, 3.875, 100.0),
    ),
    (
        "MAT345AYT-T062_03",
        "4950a9ba-198c-5588-afc7-ecefd6edc62e",
        "705716700a7dbf522d49f12d44f72701",  # pragma: allowlist secret
        "064b8add531c7892551d349b8921c24a",  # pragma: allowlist secret
        "question_text",
        "[0, 2\u03c0)",
        "(0, 2\u03c0)",
        (17, 17, 4.647058823529412, 100.0),
    ),
    (
        "MAT345AYT-T062_04",
        "73f4a2a0-c7b0-525a-9d33-685a5afaf09b",
        "8f0a7446bbbb118c645519990762410b",  # pragma: allowlist secret
        "6b6a0b37752869555b51ae2ee69cca9c",  # pragma: allowlist secret
        "question_text",
        "[0, 2\u03c0)",
        "(0, 2\u03c0)",
        (20, 16, 3.8, 100.0),
    ),
    (
        "MAT345AYT-T062_14",
        "055c884b-0afc-5cdf-b61e-1e3d378f5c39",
        "1c01a813567d89cc397ce997c91a6c02",  # pragma: allowlist secret
        "6394cfb78ac8c7fcd8c9ebc0e16ac43a",  # pragma: allowlist secret
        "question_text",
        "[0, 2\u03c0]",
        "(0, 2\u03c0]",
        (15, 14, 4.733333333333333, 100.0),
    ),
    (
        "MAT345AYT-T064_03",
        "95961959-c878-5ed3-aad0-1e1e8a061e41",
        "ad928800195a0fa384bd623813968cff",  # pragma: allowlist secret
        "0cc6ca1bec573110a226d90176968265",  # pragma: allowlist secret
        "question_text",
        "|AD| // |BC|\n|AD| \u22a5 |AB|",
        "[AD] // [BC]\n[AD] \u22a5 [AB]",
        (46, 37, 3.8260869565217392, 92.22),
    ),
    (
        "MAT345AYT-T073_04",
        "727edbfe-5538-5060-a22b-987628c10647",
        "a2644be57c2aa5c324fa879defc596bf",  # pragma: allowlist secret
        "ee789d84002da1afdd8d44c03f312fbb",  # pragma: allowlist secret
        "option_d",
        "36/65",
        "38/65",
        (52, 48, 5.5576923076923075, 91.15),
    ),
)

# 4 kusur notu (hash degismez): (dosya, id, hash, yeni kaynak_kusuru, yeni bayraklar)
KUSUR: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    (
        "MAT345AYT-T046_15",
        "35f59a4c-94cf-5db5-9122-3375aadc5cb1",
        "0d16faaf40ccb303e49838ca1ad0f7b9",  # pragma: allowlist secret
        "\u0130lk sat\u0131rda |BC ifadesinin kapan\u0131\u015f mutlak de\u011fer "
        "\u00e7izgisi g\u00f6r\u00fcnm\u00fcyor (yaln\u0131z nokta var).; ilk "
        "sat\u0131rdaki s\u0131n\u0131rlay\u0131c\u0131lar belirsiz: |AC| ya da "
        "[AC] (do\u011fru par\u00e7as\u0131)",
        ("kaynak_kusuru",),
    ),
    (
        "MAT345AYT-T105_04",
        "413c3e42-5e95-59d0-8557-eea02b7b67a2",
        "7cd9065197e3ff071087a804befe0247",  # pragma: allowlist secret
        "B \u015f\u0131kk\u0131nda sa\u011f kapan\u0131\u015f parantezi "
        "g\u00f6r\u00fcnm\u00fcyor (kesik/silik); ] olarak okundu; D "
        "\u015f\u0131kk\u0131n\u0131n s\u0131n\u0131rlay\u0131c\u0131lar\u0131 "
        "belirsiz: [0, 1] ya da (0, 1)",
        ("kaynak_kusuru",),
    ),
    (
        "MAT345AYT-T143_04",
        "d49f444a-a167-5176-8d20-d2da853b2127",
        "1e5ef10b33ceb112c50578f207921503",  # pragma: allowlist secret
        "y ile f\u2032(x) aras\u0131ndaki e\u015fittir i\u015faretinin alt "
        "\u00e7izgisi bas\u0131mda g\u00f6r\u00fcnm\u00fcyor (tek \u00e7izgi); "
        "= olarak okundu",
        ("kaynak_kusuru",),
    ),
    (
        "MAT345AYT-T162_05",
        "97b82b7c-2358-5338-9066-5f7d0122e793",
        "87f10e8b6d00d034b8804bc36acbc338",  # pragma: allowlist secret
        "|BD| ile 3 aras\u0131ndaki e\u015fittir i\u015faretinin alt \u00e7izgisi "
        "bas\u0131mda g\u00f6r\u00fcnm\u00fcyor (tek \u00e7izgi); = olarak okundu",
        ("kaynak_kusuru",),
    ),
)

_SUTUNLAR = ("question_text", "option_d")


def ikinci_okuma_meta(tur: str) -> dict[str, object]:
    """pipeline_metadata.ikinci_okuma degeri (ithal scripti ayni degeri yazar)."""
    return {
        "tur": tur,
        "kayit": KAYIT,
        "yontem": "hedefli_ikinci_okuma_8x_zoom_hakem",
        "soru_cozulmedi": True,
    }


_SEC_SQL = """
SELECT qc.question_text, qc.option_d, m.word_count, m.unique_word_count,
       m.average_word_length, m.readability_score, m.pipeline_metadata::text
  FROM question_content qc
  JOIN question_bank qb ON qb.id = qc.id
  JOIN question_metadata m ON m.id = qc.id
 WHERE qc.id = :id AND qb.soru_hash = :hash AND m.source_book = :kitap
"""

_META_EKLE = sa.text(
    """
    UPDATE question_metadata
       SET pipeline_metadata = (pipeline_metadata::jsonb || CAST(:ek AS jsonb))::json
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
        _log.info("[0048] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))


def _gunluge_yaz(b, sid: str, h: str, satir) -> None:
    metin, secd, wc, uwc, awl, rs, pm = satir
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, onceki_metin, onceki_option_d, onceki_hash, "  # noqa: S608  # nosec B608
            "onceki_word_count, onceki_unique_word_count, onceki_average_word_length, "
            "onceki_readability_score, onceki_pipeline_metadata) "
            "VALUES (:id, :m, :d, :h, :wc, :uwc, :awl, :rs, :pm)"
        ),
        {
            "id": sid,
            "m": metin,
            "d": secd,
            "h": h,
            "wc": wc,
            "uwc": uwc,
            "awl": awl,
            "rs": rs,
            "pm": pm,
        },
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0048] soru tablolari yok (taze DB?) -- atlandi")
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_metin", sa.Text(), nullable=True),
        sa.Column("onceki_option_d", sa.Text(), nullable=True),
        sa.Column("onceki_hash", sa.String(), nullable=True),
        sa.Column("onceki_word_count", sa.Integer(), nullable=True),
        sa.Column("onceki_unique_word_count", sa.Integer(), nullable=True),
        sa.Column("onceki_average_word_length", sa.Float(), nullable=True),
        sa.Column("onceki_readability_score", sa.Float(), nullable=True),
        sa.Column("onceki_pipeline_metadata", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    degisen = 0
    for dosya, sid, eh, yh, sutun, ep, yp, ist in METIN:
        if sutun not in _SUTUNLAR:  # pragma: no cover  # sabit tablo
            raise ValueError(f"{dosya}: beklenmeyen sutun {sutun}")
        satir = b.execute(
            sa.text(_SEC_SQL), {"id": sid, "hash": eh, "kitap": KAYNAK_ADI}
        ).fetchone()
        if satir is None:
            _log.info("[0048] %s bulunamadi (id/hash tutmadi) -- atlandi", dosya)
            continue
        mevcut = satir[0] if sutun == "question_text" else satir[1]
        if (mevcut or "").count(ep) != 1:
            _log.info("[0048] %s parca tam bir kez yok -- ATLANDI", dosya)
            continue
        _gunluge_yaz(b, sid, eh, satir)
        b.execute(
            sa.text(
                f"UPDATE question_content SET {sutun} = :v WHERE id = :id"  # noqa: S608  # nosec B608
            ),
            {"id": sid, "v": mevcut.replace(ep, yp)},
        )
        b.execute(
            sa.text("UPDATE question_bank SET soru_hash = :h WHERE id = :id"),
            {"id": sid, "h": yh},
        )
        b.execute(
            sa.text(
                "UPDATE question_metadata SET word_count = :wc, unique_word_count = :uwc, "
                "average_word_length = :awl, readability_score = :rs WHERE id = :id"
            ),
            {"id": sid, "wc": ist[0], "uwc": ist[1], "awl": ist[2], "rs": ist[3]},
        )
        b.execute(
            _META_EKLE,
            {"id": sid, "ek": json.dumps({META_ANAHTARI: ikinci_okuma_meta("metin")})},
        )
        _log.info("[0048] %s: %s duzeltildi", dosya, sutun)
        degisen += 1
    for dosya, sid, h, kusur, bayrak in KUSUR:
        satir = b.execute(
            sa.text(_SEC_SQL), {"id": sid, "hash": h, "kitap": KAYNAK_ADI}
        ).fetchone()
        if satir is None:
            _log.info("[0048] %s bulunamadi (id/hash tutmadi) -- atlandi", dosya)
            continue
        _gunluge_yaz(b, sid, h, satir)
        ek: dict[str, object] = {
            "kaynak_kusuru": kusur,
            "bayraklar": list(bayrak),
            META_ANAHTARI: ikinci_okuma_meta("kusur_notu"),
        }
        b.execute(_META_EKLE, {"id": sid, "ek": json.dumps(ek)})
        _log.info("[0048] %s: kusur notu", dosya)
        degisen += 1
    _log.info("[0048] guncellenen satir: %s / %s", degisen, len(METIN) + len(KUSUR))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0048] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    sorgu = (
        "SELECT id, onceki_metin, onceki_option_d, onceki_hash, onceki_word_count, "  # noqa: S608  # nosec B608
        "onceki_unique_word_count, onceki_average_word_length, "
        f"onceki_readability_score, onceki_pipeline_metadata FROM {GUNLUK}"
    )
    kayitlar = b.execute(sa.text(sorgu)).fetchall()
    for sid, metin, secd, h, wc, uwc, awl, rs, pm in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_content SET question_text = :m, option_d = :d WHERE id = :id"
            ),
            {"id": sid, "m": metin, "d": secd},
        )
        b.execute(
            sa.text("UPDATE question_bank SET soru_hash = :h WHERE id = :id"),
            {"id": sid, "h": h},
        )
        b.execute(
            sa.text(
                "UPDATE question_metadata SET word_count = :wc, unique_word_count = :uwc, "
                "average_word_length = :awl, readability_score = :rs, "
                "pipeline_metadata = CAST(:pm AS json) WHERE id = :id"
            ),
            {"id": sid, "wc": wc, "uwc": uwc, "awl": awl, "rs": rs, "pm": pm},
        )
    _log.info("[0048] geri alindi: %s satir", len(kayitlar))
    op.drop_table(GUNLUK)
    _refresh_safe_for_beta(b)
