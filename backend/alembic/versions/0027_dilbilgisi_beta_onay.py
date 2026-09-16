"""Dilbilgisi kitabini beta kapisindan gecirir (bireysel denetim atlanarak)

Revision ID: 0027_dilbilgisi_beta
Revises: 0026_dilbilgisi_kaynak_adi
Create Date: 2026-09-16

BAGLAM
------
"Aktif Ogrenme Tyt Dilbilgisi Soru Bankasi 2025" kitabinin 678 sorusu
0025/0026 kampanyasinda bilerek PASIF ithal edildi (is_ai_generated=true +
review_status='PENDING'). Urun sahibi bireysel insan denetimini ATLAYIP
toplu olarak beta surumunde yapmaya karar verdi; ayni karar daha once 0014
(AYT fizik), 0016 (TYT fizik), 0018 (Mikro geometri) ve 0023 (345 serisi)
ile uygulanmisti. Bu migration onun Dilbilgisi karsiligidir.

KAPI YUKU OLCULDU, TAHMIN EDILMEDI
----------------------------------
`v_safe_for_beta` tanimi pg_get_viewdef ile okundu ve her kosul 678 satir
icin AYRI sayildi:

    kosul                                        sonuc
    pipeline_metadata NOT NULL ................. 678/678  gecti
    demoted_at yok ............................. 678/678  gecti
    topic_match_quality <> fallback ............ 678/678  gecti
    match_tier tier1 degil ..................... 678/678  gecti
    bayraklar.sik_bos yok ...................... 678/678  gecti
    quality_review_status uygun ................   0/678  TUTUYOR
    uyum sinyali (6 anahtardan biri) ...........   0/678  TUTUYOR
    (is_ai_generated=false OR APPROVED) ........   0/678  TUTUYOR

Kapiyi tutan UC kilit var; bu migration ucunu de acar, is_active da acilir.
is_public'e DOKUNULMAZ: bu depodaki hicbir kitap ithali herkese acik
degildir (olculdu: dokuz ithal kaynaginin dokuzunda da is_public=0).

HEDEF 678 DEGIL 644
-------------------
Kitabin kendi dizgi kusurlarini tasiyan 34 satir DISARIDA birakilir
(`bayraklar.kaynak_dizgi_kusuru`). Bu, 0023'un `sik_bos` /
`gorsel_yok_sekilli` disarida birakmasiyla ayni sinifta bir karardir:
basili sayfanin kendisi eksik ya da celiskili oldugu icin soru ogrenciye
oldugu gibi gosterilmemelidir. Ornekler (hepsi `kaynak_kusuru` alaninda
tam metin olarak kayitli):

    s130 q13 -- "altI cizili sozcukler" soruluyor, E'de alt cizgi YOK
    s142 q4  -- "altI cizili eylem" soruluyor, D'de alt cizgi YOK
    s105 q1  -- "altI cizili sozcuk" soruluyor, E'de alt cizgi YOK
    s43  q4  -- noktalama sorusu, C'de iki ayracin ici BOS basilmis
    s146 q6  -- dorduncu secenek "D)" yerine "C) IV" basilmis
    s16  q9  -- hem "diyen" hem "sizliyor" altinda "V" basili

Bunlarin hepsi tek tek incelenip aciklanabilir, ama bu karar URUN
SAHIBININ alanindadir; bu migration hicbirini adjuste etmez, hepsini
PASIF birakir. Bolum dagilimi (toplam -> temiz):

    Konu Testi .............. 521 -> 511
    Uygulama Bolumu - Soru ... 71 ->  62
    Kavrama Bolumu - Ornek ... 70 ->  57
    OSYM Sorulari ............ 16 ->  14
                               ---    ---
                               678    644

ESKI 17 SATIR KAPSAM DISI
-------------------------
DB'de bu kitaptan eski gemini hattindan gelen 17 satir daha var; onlar
zaten is_active=1, is_public=1 ve `pipeline_metadata.ithal_araci`
TASIMIYOR. Hedef sorgusu source_book ile DEGIL, ithal_araci ile
daraltilir; boylece o 17 satira dokunulmaz (kullanici karari).

KONSENSUS GEREKCESI UC KANAL ICIN AYRI YAZILDI
----------------------------------------------
Kitap tek kitap ama UC AYRI dogrulama gecmisi var. 0023'un dersi burada da
gecerli: tek bir liste yazip hepsine yapistirmak FAZLA IDDIA olurdu.
Satirlar `pipeline_metadata.anahtar_dogrulamasi` degerine gore ayrilir ve
her gruba KENDI olculmus sinyalleri yazilir (kaynak:
veriseti/zkitap/cikti/DILBILGISI_YONTEM.md).

1. KONU TESTI + OSYM (Faz 1, cevap_kaynagi='cevap_seridi')
   - sayfa_siniflandirmasi_iki_kanal_0_uyusmazlik: soru sayfalari iki
     BAGIMSIZ kanalla bulundu (bant renk imzasi; sayfa altindaki cevap
     seridi metni). Ikisi de ayni 86 sayfayi verdi, UYUSMAZLIK 0.
   - anahtar_seridi_cift_okuma_553_soru_fark_0: cevap anahtari FARKLI
     geometri ve FARKLI olcekte iki kez okundu (A: x690-1280/y942-976,
     2.5x; B: otomatik metin siniri, 3.2x). 553 soruda hem numara hem
     harf karsilastirildi, FARK 0.
   - test_ici_numara_surekliligi_44_test_0_kusur: her test 1..N kesintisiz
     olmali; 44 testin 44'unde kusur 0.
   - imlec_sayisi_anahtar_sayisi_esitligi_90_90: bir sayfada bulunan koyu
     kirmizi soru imleci sayisi, o sayfanin cevap seridindeki soru
     sayisina ESIT olmali. 90 sayfanin 90'inda esit. Bu, METIN kanalinin
     ANAHTAR kanaliyla capraz kontroludur.
   - dogrulayici_k1_k11_tek_bulgu_ithal_disi_birakildi: 11 yapisal kontrol
     553 soruda 1 bulgu verdi (s48 q8: A ve E secenekleri birebir ayni
     basili, tavan cozunurlukte ayirt edilemiyor). O soru ITHAL EDILMEDI;
     ithal edilenler icinde 0 bulgu.

2. UYGULAMA BOLUMU - SORU (Faz 2, cevap_kaynagi='cevap_seridi')
   - anahtar_seridi_cift_okuma_73_soru_fark_0: yine iki farkli geometri ve
     olcek (A: x1040-1340, 3.0x; B: otomatik sinir, 4.2x). FARK 0.
   - unite_ici_numara_surekliligi_16_unite_0_kusur: her unitede Soru
     numaralari 1..N kesintisiz (alt harfli "2a"/"2b" ayni numaranin iki
     parcasi sayilir). 16 unite, kusur 0.
   - dogrulayici_k1_k12_143_soruda_0_kusur
   - ornek_soru_numara_eslesmesi_k4_kapisi: `ornekler[].no` listesi,
     `sorular[].no` listesinin ALT HARFSIZ KOKLERI kumesine esit olmali.
     Iki AYRI sayfa bolgesinden okunan iki liste birbirini dogrular.

3. KAVRAMA BOLUMU - ORNEK (Faz 2, cevap_kaynagi='satir_ici_cevap')
   - dogrulayici_k1_k12_143_soruda_0_kusur
   - ornek_soru_numara_eslesmesi_k4_kapisi
   - satir_ici_cevap_ve_cozum_zorunlulugu_k12_kapisi: Ornek satirlarinda
     satir ici cevap VE cozum ZORUNLU, Soru satirlarinda ikisi de YASAK;
     143 soruda kusur 0.

   BU GRUPTA ANAHTAR CIFT OKUNMADI. Cevap, kitabin satir ici "Cevap: X"
   ibaresinden BIR KEZ okundu. `anahtar_cift_okuma=false` ve
   `anahtar_dogrulamasi='satir_ici_cevap_tek_okuma__cozum_metniyle_birlikte'`
   alanlari YERINDE KALIR; bu migration onlari degistirmez ve sinyal
   listesine olmayan bir cift okuma YAZMAZ. Ayni durum 0023'te TYT
   biyolojinin 689 satirinda da vardi (orada da anahtar tek okunmustu,
   guvence yapisal dogrulayicidan geliyordu).

NE OLDUGU KONUSUNDA DURUST OLMA
-------------------------------
- quality_review_status: 'pending' -> 'auto_judged_high'
  'human_verified' YAZILMIYOR -- hicbir insan bu sorulari tek tek
  dogrulamadi.
- review_status: 'PENDING' -> 'APPROVED'; bu TOPLU sahip onayidir ve
  metadata'ya yazilir: onay_turu='toplu_beta_sahibi',
  bireysel_denetim_yapildi=false.
- is_ai_generated ALANINA DOKUNULMUYOR -- true kalir.
- CEVAPLAR DOGRULANMADI. Tek cevap kaynagi kitabin BASILI anahtaridir
  (urun karari: "sorulari tekrar cozme, cevap anahtarina guven").
  Ustteki sinyaller TRANSKRIPSIYONU ve SEGMENTASYONU dogrular, cevabin
  kendisini degil. `cozum_dogrulamasi` alani yerinde kalir.
- Eski 17 satirin 2'sinin cevabi basili anahtarla CELISIYOR (s107 q6,
  s33 q4). Onlar bu migration'in kapsaminda DEGIL; ayri ele alinir.

GERI ALINABILIR
---------------
Degistirilen her satirin ONCEKI degerleri GUNLUK'e yazilir; downgrade() tam
olarak o degerleri geri koyar ve eklenen metadata anahtarlarini siler.

Revizyon adi 20 karakter (sinir 32 -- bkz. 0016'nin ogrendigi ders).
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0027_dilbilgisi_beta"
down_revision: Union[str, None] = "0026_dilbilgisi_kaynak_adi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "dilbilgisi_beta_onay_gunlugu_0027"

ITHAL_ARACI = "scripts/kitap/dilbilgisi_ithal.py"

# Satirlar `anahtar_dogrulamasi` degerine gore ayrilir; her grubun sinyal
# listesi KENDI olcumunden gelir. Ayrinti icin basliktaki "KONSENSUS
# GEREKCESI" bolumu.
GRUPLAR: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "anahtar_seridi_cift_okuma_fark_0__numara_surekliligi_44_test_0_kusur",
        (
            "sayfa_siniflandirmasi_iki_kanal_0_uyusmazlik",
            "anahtar_seridi_cift_okuma_553_soru_fark_0",
            "test_ici_numara_surekliligi_44_test_0_kusur",
            "imlec_sayisi_anahtar_sayisi_esitligi_90_90",
            "dogrulayici_k1_k11_tek_bulgu_ithal_disi_birakildi",
        ),
    ),
    (
        "anahtar_seridi_cift_okuma_fark_0__numara_surekliligi_0_kusur",
        (
            "anahtar_seridi_cift_okuma_73_soru_fark_0",
            "unite_ici_numara_surekliligi_16_unite_0_kusur",
            "dogrulayici_k1_k12_143_soruda_0_kusur",
            "ornek_soru_numara_eslesmesi_k4_kapisi",
        ),
    ),
    (
        "satir_ici_cevap_tek_okuma__cozum_metniyle_birlikte",
        (
            "dogrulayici_k1_k12_143_soruda_0_kusur",
            "ornek_soru_numara_eslesmesi_k4_kapisi",
            "satir_ici_cevap_ve_cozum_zorunlulugu_k12_kapisi",
        ),
    ),
)

# Eklenen metadata anahtarlari -- downgrade tam olarak bunlari siler.
EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)

# Disarida birakilan bayraklar. Ilk ikisi 0023'ten devralindi (kapinin
# kendi kosullari); ucuncusu bu kitaba ozgudur ve basili sayfanin kendi
# kusurunu isaretler.
_HEDEF_SQL = """
SELECT qb.id, qb.is_active, qb.review_status, qs.quality_review_status
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  LEFT JOIN question_statistics qs ON qs.id = qb.id
 WHERE (qm.pipeline_metadata::jsonb ->> 'ithal_araci') = :arac
   AND (qm.pipeline_metadata::jsonb ->> 'anahtar_dogrulamasi') = :grup
   AND (NOT (qm.pipeline_metadata::jsonb ? 'bayraklar')
        OR (NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')
            AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
                     ? 'gorsel_yok_sekilli')
            AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
                     ? 'kaynak_dizgi_kusuru')))
"""

_META_EKLE = sa.text(
    """
    UPDATE question_metadata
       SET pipeline_metadata = (
             pipeline_metadata::jsonb
             || jsonb_build_object(
                  'consensus_2signal_run', true,
                  'konsensus_sinyalleri', CAST(:sinyaller AS jsonb),
                  'onay_turu', 'toplu_beta_sahibi',
                  'bireysel_denetim_yapildi', false)
           )::json
     WHERE id = ANY(:idler)
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


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0027] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0027] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "question_statistics")
    )


def _gunlugu_kur() -> None:
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("onceki_review_status", sa.String(), nullable=True),
        sa.Column("onceki_quality_review_status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def _grubu_ac(b, grup: str, sinyaller: tuple[str, ...]) -> int:
    """Tek bir dogrulama grubunu acar; acilan satir sayisini dondurur."""
    hedef = b.execute(
        sa.text(_HEDEF_SQL), {"arac": ITHAL_ARACI, "grup": grup}
    ).fetchall()
    if not hedef:
        _log.info("[0027] %s grubunda satir yok -- atlandi", grup)
        return 0

    idler = [r[0] for r in hedef]
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608
            " onceki_quality_review_status)"
            " VALUES (:id, :akt, :rs, :qrs)"
        ),
        [{"id": r[0], "akt": r[1], "rs": r[2], "qrs": r[3]} for r in hedef],
    )
    b.execute(
        sa.text(
            "UPDATE question_bank SET is_active = TRUE, review_status = 'APPROVED',"
            " updated_at = now() WHERE id = ANY(:idler)"
        ),
        {"idler": idler},
    )
    b.execute(
        sa.text(
            "UPDATE question_statistics SET quality_review_status = 'auto_judged_high'"
            " WHERE id = ANY(:idler)"
        ),
        {"idler": idler},
    )
    b.execute(_META_EKLE, {"idler": idler, "sinyaller": json.dumps(list(sinyaller))})
    _log.info("[0027] %s: %s satir acildi", grup, len(idler))
    return len(idler)


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0027] soru tablolari yok (taze DB?) -- atlandi")
        return

    var_mi = b.execute(
        sa.text(
            "SELECT 1 FROM question_metadata"
            " WHERE (pipeline_metadata::jsonb ->> 'ithal_araci') = :arac LIMIT 1"
        ),
        {"arac": ITHAL_ARACI},
    ).first()
    if var_mi is None:
        _log.info("[0027] Dilbilgisi satiri yok -- atlandi (veri ithal edilmemis)")
        return

    _gunlugu_kur()
    toplam = sum(_grubu_ac(b, grup, sinyaller) for grup, sinyaller in GRUPLAR)

    haric = b.execute(
        sa.text(
            "SELECT count(*) FROM question_metadata"
            " WHERE (pipeline_metadata::jsonb ->> 'ithal_araci') = :arac"
            "   AND (pipeline_metadata::jsonb -> 'bayraklar')"
            "       ? 'kaynak_dizgi_kusuru'"
        ),
        {"arac": ITHAL_ARACI},
    ).scalar_one()
    _log.info(
        "[0027] beta kapisi acildi: %s satir; dizgi kusuru nedeniyle pasif kalan: %s",
        toplam,
        haric,
    )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0027] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(
            "SELECT id, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608
            f" onceki_quality_review_status FROM {GUNLUK}"
        )
    ).fetchall()
    for sid, akt, rs, qrs in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = :akt, review_status = :rs,"
                " updated_at = now() WHERE id = :id"
            ),
            {"id": sid, "akt": akt, "rs": rs},
        )
        b.execute(
            sa.text(
                "UPDATE question_statistics SET quality_review_status = :qrs"
                " WHERE id = :id"
            ),
            {"id": sid, "qrs": qrs},
        )

    idler = [r[0] for r in kayitlar]
    for anahtar in EK_ANAHTARLAR:
        b.execute(
            sa.text(
                "UPDATE question_metadata"
                " SET pipeline_metadata = (pipeline_metadata::jsonb - :a)::json"
                " WHERE id = ANY(:idler)"
            ),
            {"a": anahtar, "idler": idler},
        )

    _log.info("[0027] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
