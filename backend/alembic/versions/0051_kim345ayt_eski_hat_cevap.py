"""345 AYT Kimya eski hat satirlarini kitabin BASILI cevap satirina hizalar

Revision ID: 0051_kim345ayt_eski_cevap
Revises: 0050_kim345ayt_kaynak_adi
Create Date: 2026-09-25

BAGLAM
------
345 2025 AYT Kimya ithalinde eski hat taramasi (363 satir, '345 2024/2025
Ayt Kimya Soru Bankasi'; her eski satir icin bu kitaptaki en iyi soru:
govde kelime Jaccard >= 0.75 VE bes sikkin >= 3'u birebir ya da sik
kumesi ayni) AKTIF ve PUBLIC 7 satirin kitabin kendi basili anahtariyla
CEVAP ICERIGINDE celistigini buldu. Bu migration 6'sini duzeltir:

    satir     kaynak etiketi / sayfa      DB   basili   eski hattaki okuma hatasi
    a0ee5afc  2025  s32  sol 2            A    E        Cr^+ -> Cr^{2+}; sik B/D yer degismis
    118a2a68  2024  s36  sol 2            A    E        np^5 -> np^3; 'bir grubundaki' -> 'II. grubundaki'
    2e60703b  2025  s129 sag 6            A    E        (metin ve sikler basiliyla ayni)
    6453cd45  2024  s33  sol 9            E    D        sik D/E alt indisleri yer degismis (N_2O_5 / P_2O_3)
    076f3caa  2024  s207 sol 1            C    E        'yukseltgendir' -> 'yukseltgenir'
    53c380ed  2025  s289 sol 6            B    A        C_4H_8 -> C_2H_6, 11 -> 7 sigma, sik B

Sahip karari (24 Eyl 2026): "kitabin basili cevabi baz alinir" (0044 / 0047
ile ayni desen).

KANIT (soru cozulmedi)
----------------------
* Basili serit her satir icin 3x en-yakin-komsu buyutmeyle gozle okundu
  (2025 baskisi): s32 sol '1.D 2.E', s36 sol '1.D 2.E 3.E', s129 sag '5.E 6.E',
  s207 sol '1.E 2.B 3.D', s289 sol '6.A 7.D 8.C'; s33 sol 9.D iki bagimsiz
  okuma + piksel kanali. 2024 etiketli satirlarin sayfalarinda 2024
  yakalamasi 2025 ile piksel olarak ayni (fark yalniz okuyucu simgeleri,
  <= 390 piksel; cevap seridi satirlari farksiz).
* Metin ve sik duzeltmeleri basili sorunun kirpimina bakilarak yazildi
  (345_2025_ayt_kimya_metin.json ile ayni icerik). Eski hattin METNI ya da
  SIKLARI basilidan farkli oldugu satirlarda eski cevap o BOZUK icerigin
  cevabidir; yalniz cevabi degistirmek satiri kendi icinde tutarsiz
  birakirdi. Bu yuzden metin parcasi / sik da basili hale getirilir.
* Eski hattin `explanation` alani basili cevapla celisen sonuca variyorsa
  NULL yapilir (076f3caa'da zaten NULL).
* soru_hash ayni formulle (metin_olcum.soru_hash) yeniden hesaplanmis
  degerine cekilir; yeni hash'lerin hicbiri baska bir satirla CAKISMIYOR
  (olculdu).

KAPSAM DISI (7. celiski, sahip karari)
--------------------------------------
0344bdd2 (2024 etiketi, s129 sag 6) 2e60703b'nin IKIZIDIR (ayni soru, iki
baski etiketi); sik D/E'yi yanlis okumus, dogru icerik ('I, II ve III')
siklarinda YOK. Basiliya cekilirse 2e60703b ile ayni soru_hash'i alir ve
uq_qb_soru_hash_active kisitini bozar. Ikizlerden birinin kapatilmasi urun
karari; bu migration ona DOKUNMAZ.

CERRAHI KAPSAM
--------------
Guncelleme yalniz id + mevcut soru_hash + mevcut correct_answer UCU BIRDEN
beklenen degerdeyse, her metin parcasi tam bir kez geciyorsa ve her
degisecek sik beklenen eski degerdeyse uygulanir. Biri tutmazsa satir
ATLANIR ve loglanir (0028 / 0044 / 0047 deseni).

GERI ALINABILIR
---------------
Onceki cevap, metin, bes sik, hash ve aciklama GUNLUK'e yazilir; downgrade
tam olarak onlari geri koyar ve eklenen metadata anahtarini siler.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0051_kim345ayt_eski_cevap"
down_revision: Union[str, None] = "0050_kim345ayt_kaynak_adi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "kim345ayt_eski_cevap_gunlugu_0051"
META_ANAHTARI = "cevap_duzeltme_0051"
SIK_KOLON = {h: f"option_{h.lower()}" for h in "ABCDE"}

# (id, eski_hash, yeni_hash, eski_cevap, yeni_cevap,
#  ((eski_parca, yeni_parca), ...), ((sik, eski, yeni), ...), aciklamayi_sil, kaynak)
DUZELTMELER: tuple[
    tuple[
        str,
        str,
        str,
        str,
        str,
        tuple[tuple[str, str], ...],
        tuple[tuple[str, str, str], ...],
        bool,
        str,
    ],
    ...,
] = (
    (  # T014_02 (345_2025_ayt_kimya_s32_sol_serit_2E)
        "a0ee5afc-2697-5e46-ab8c-5cf3cf187dc1",
        "26ad627671719767e524011521620fbe",  # pragma: allowlist secret
        "ac6b03419e04848dd88a793ec264a9c1",  # pragma: allowlist secret
        "A",
        "E",
        (
            ("$_{24}Cr^{2+}$ ve", "$_{24}Cr^{+}$ ve"),
            ("$_{24}Cr^{2+} > _{26}Fe^{3+}$", "$_{24}Cr^{+} > _{26}Fe^{3+}$"),
        ),
        (
            ("B", "I ve II", "I ve III"),
            ("D", "I ve III", "I ve II"),
        ),
        True,
        "345_2025_ayt_kimya_s32_sol_serit_2E",
    ),
    (  # T016_02 (345_2025_ayt_kimya_s36_sol_serit_2E__345_2024_s36_sol_serit_ayni)
        "118a2a68-432a-524b-90f5-ccbe4fbc2c82",
        "75021a1178bad8d904372788678fcaa0",  # pragma: allowlist secret
        "d6ba928fd87a49e79b19bc7d2c6a2d7b",  # pragma: allowlist secret
        "A",
        "E",
        (
            ("$ns^2np^3$", "$ns^2np^5$"),
            ("cetvelin II. grubundaki", "cetvelin bir grubundaki"),
        ),
        (),
        True,
        "345_2025_ayt_kimya_s36_sol_serit_2E__345_2024_s36_sol_serit_ayni",
    ),
    (  # T061_06_2025 (345_2025_ayt_kimya_s129_sag_serit_6E)
        "2e60703b-ae1d-586c-817f-5c14cc4ad451",
        "e1adcd65185a01b4804327939764c3c8",  # pragma: allowlist secret
        "e1adcd65185a01b4804327939764c3c8",  # pragma: allowlist secret
        "A",
        "E",
        (),
        (),
        True,
        "345_2025_ayt_kimya_s129_sag_serit_6E",
    ),
    (  # T014_09 (345_2025_ayt_kimya_s33_sol_serit_9D)
        "6453cd45-1c4d-5b75-ae68-e6794bf56ef8",
        "c2e5f5b6be3570263e264b6a2aa980d5",  # pragma: allowlist secret
        "462590f805af74565a85e9fe8485dd31",  # pragma: allowlist secret
        "E",
        "D",
        (),
        (
            ("D", "$N_2O_3$", "$N_2O_5$"),
            ("E", "$P_2O_5$", "$P_2O_3$"),
        ),
        True,
        "345_2025_ayt_kimya_s33_sol_serit_9D",
    ),
    (  # T100_01 (345_2025_ayt_kimya_s207_sol_serit_1E__345_2024_s207_sol_serit_ayni)
        "076f3caa-d8ac-5405-8b1c-f0d95bdc3d34",
        "b6504d8e4123a3e5a66d0121bfe99214",  # pragma: allowlist secret
        "dba0a7a16c44c389e96cc392a9c97ffc",  # pragma: allowlist secret
        "C",
        "E",
        (
            (
                "Elektron alan madde y\xfckseltgenir.",
                "Elektron alan madde y\xfckseltgendir.",
            ),
        ),
        (),
        False,
        "345_2025_ayt_kimya_s207_sol_serit_1E__345_2024_s207_sol_serit_ayni",
    ),
    (  # T136_06 (345_2025_ayt_kimya_s289_sol_serit_6A)
        "53c380ed-07ee-5bab-8898-9238baf3b9b1",
        "b9cedb2fdf4695ddabd5bc2f233d8819",  # pragma: allowlist secret
        "68786f2d21603a7d3ab822f15bece616",  # pragma: allowlist secret
        "B",
        "A",
        (
            ("$C_2H_6$ bile", "$C_4H_8$ bile"),
            ("7 tane sigma", "11 tane sigma"),
            ("$sp^3$ ve $sp^2$", "$sp^2$ ve $sp^3$"),
        ),
        (("B", "Yaln\u0131z II", "I ve II"),),
        True,
        "345_2025_ayt_kimya_s289_sol_serit_6A",
    ),
)

_SEC_SQL = """
SELECT qc.correct_answer, qc.question_text, qc.explanation,
       qc.option_a, qc.option_b, qc.option_c, qc.option_d, qc.option_e
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
                    'sik_duzeltildi', CAST(:sik AS boolean),
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
        _log.info("[0051] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0051] soru tablolari yok (taze DB?) -- atlandi")
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_cevap", sa.String(), nullable=True),
        sa.Column("onceki_metin", sa.Text(), nullable=True),
        sa.Column("onceki_hash", sa.String(), nullable=True),
        sa.Column("onceki_aciklama", sa.Text(), nullable=True),
        sa.Column("onceki_a", sa.Text(), nullable=True),
        sa.Column("onceki_b", sa.Text(), nullable=True),
        sa.Column("onceki_c", sa.Text(), nullable=True),
        sa.Column("onceki_d", sa.Text(), nullable=True),
        sa.Column("onceki_e", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    degisen = 0
    for sid, eh, yh, ec, yc, parcalar, sikler, sil, kaynak in DUZELTMELER:
        satir = b.execute(sa.text(_SEC_SQL), {"id": sid, "hash": eh}).fetchone()
        if satir is None:
            _log.info("[0051] %s bulunamadi (id/hash tutmadi) -- atlandi", sid[:8])
            continue
        cevap, metin, aciklama = satir[0], satir[1], satir[2]
        eski_sik = dict(zip("ABCDE", satir[3:8], strict=True))
        if cevap != ec:
            _log.info("[0051] %s cevabi %r, beklenen %r -- ATLANDI", sid[:8], cevap, ec)
            continue
        yeni_metin = metin
        tamam = True
        for ep, yp in parcalar:
            if yeni_metin.count(ep) != 1:
                tamam = False
                break
            yeni_metin = yeni_metin.replace(ep, yp)
        if not tamam:
            _log.info("[0051] %s metin parcasi tam bir kez yok -- ATLANDI", sid[:8])
            continue
        yeni_sik = dict(eski_sik)
        for h, es, ys in sikler:
            if eski_sik[h] != es:
                tamam = False
                break
            yeni_sik[h] = ys
        if not tamam:
            _log.info("[0051] %s sik beklenen eski degerde degil -- ATLANDI", sid[:8])
            continue
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, onceki_cevap, onceki_metin, "  # noqa: S608  # nosec B608
                "onceki_hash, onceki_aciklama, onceki_a, onceki_b, onceki_c, "
                "onceki_d, onceki_e) VALUES (:id, :c, :m, :h, :a, :oa, :ob, :oc, :od, :oe)"
            ),
            {
                "id": sid,
                "c": cevap,
                "m": metin,
                "h": eh,
                "a": aciklama,
                **{f"o{h.lower()}": eski_sik[h] for h in "ABCDE"},
            },
        )
        b.execute(
            sa.text(
                "UPDATE question_content SET correct_answer = :c, question_text = :m, "
                "option_a = :oa, option_b = :ob, option_c = :oc, option_d = :od, "
                "option_e = :oe, "
                "explanation = CASE WHEN :sil THEN NULL ELSE explanation END "
                "WHERE id = :id"
            ),
            {
                "id": sid,
                "c": yc,
                "m": yeni_metin,
                "sil": sil,
                **{f"o{h.lower()}": yeni_sik[h] for h in "ABCDE"},
            },
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
                "metin": bool(parcalar),
                "sik": bool(sikler),
                "sil": sil,
            },
        )
        _log.info("[0051] %s: %s -> %s (%s)", sid[:8], ec, yc, kaynak)
        degisen += 1
    _log.info("[0051] duzeltilen satir: %s / %s", degisen, len(DUZELTMELER))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0051] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    sorgu = (
        "SELECT id, onceki_cevap, onceki_metin, onceki_hash, onceki_aciklama, "  # noqa: S608  # nosec B608
        f"onceki_a, onceki_b, onceki_c, onceki_d, onceki_e FROM {GUNLUK}"
    )
    kayitlar = b.execute(sa.text(sorgu)).fetchall()
    for sid, cevap, metin, h, aciklama, oa, ob, oc, od, oe in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_content SET correct_answer = :c, question_text = :m, "
                "explanation = :a, option_a = :oa, option_b = :ob, option_c = :oc, "
                "option_d = :od, option_e = :oe WHERE id = :id"
            ),
            {
                "id": sid,
                "c": cevap,
                "m": metin,
                "a": aciklama,
                "oa": oa,
                "ob": ob,
                "oc": oc,
                "od": od,
                "oe": oe,
            },
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
    _log.info("[0051] geri alindi: %s satir", len(kayitlar))
    op.drop_table(GUNLUK)
    _refresh_safe_for_beta(b)
