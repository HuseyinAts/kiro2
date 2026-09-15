"""345 serisi uc kitabi beta kapisindan gecirir (bireysel denetim atlanarak)

Revision ID: 0023_345_beta_onay
Revises: 0022_biyo345tyt_konu_agaci
Create Date: 2026-09-15

BAGLAM
------
345 yayinlarinin uc kitabi kampanya boyunca bilerek PASIF ithal edildi
(is_ai_generated=true + review_status='PENDING'):

    345 2025 TYT-AYT Geometri Soru Bankasi ... 2708 satir
    345 2025 AYT Biyoloji Soru Bankasi ....... 1315 satir
    345 2025 TYT Biyoloji Soru Bankasi ....... 1023 satir

Urun sahibi bireysel insan denetimini ATLAYIP toplu olarak beta surumunde
yapmaya karar verdi; ayni karar daha once 0014 (AYT fizik), 0016 (TYT fizik)
ve 0018 (Mikro geometri) ile uygulanmisti. Bu migration 345 serisinin
karsiligidir. Kapsam karari urun sahibinindir: "hepsi, ama TYT'nin sekilli
sorulari HARIC".

KAPI YUKU OLCULDU, TAHMIN EDILMEDI
----------------------------------
`v_safe_for_beta` tanimi pg_views'ten okundu ve her kosul UC KITAP ICIN
AYRI AYRI sayildi (backend/_geo_gecici/kapi_olc2.py):

    kosul                              geo        ayt-biyo    tyt-biyo
    pipeline_metadata NOT NULL ....... 2708/2708  1315/1315   1023/1023
    demoted_at yok ................... 2708/2708  1315/1315   1023/1023
    topic_match_quality <> fallback .. 2708/2708  1315/1315   1023/1023
    match_tier tier1 degil ........... 2708/2708  1315/1315   1023/1023
    sik_bos yok ...................... 2702/2708  1315/1315   1023/1023
    gorsel_yok_sekilli yok ........... 2708/2708  1315/1315    689/1023
    quality_review_status uygun ......    0/2708     0/1315      0/1023
    uyum sinyali (6 anahtardan biri) .    0/2708     0/1315      0/1023
    (is_ai_generated=false OR APPROVED)   0/2708     0/1315      0/1023
    is_active ........................    0/2708     0/1315      0/1023

Kapiyi tutan UC kilit var; bu migration ucunu de acar, is_active da acilir.
Ustteki alti kosul zaten geciyor; ikisi KISMI ve hedefi daraltir.

HEDEF 4712 DEGIL 4706
---------------------
Urun sahibinin sectigi kapsam nominal olarak 2708 + 1315 + 689 = 4712 idi.
Gercek sayi 4706: geometrinin 6 satiri `sik_bos` bayragi tasiyor ve bu
bayrak kapinin KENDI kosulu; o satirlar bu migration ne yaparsa yapsin
kapidan gecemez. Aradaki 6 fark tahmin degil olcum sonucudur
(backend/_geo_gecici/hedef_olc.py):

    geometri ..... 2708 - 6 (sik_bos) ................. = 2702
    ayt biyoloji . 1315 - 0 ........................... = 1315
    tyt biyoloji . 1023 - 334 (gorsel_yok_sekilli) .... =  689
                                                          ----
                                                          4706

Hedef sorgusu iki bayragi da EVRENSEL olarak disarida birakir. Bu, kitaba
ozel bir istisna listesi tutmaktan daha saglamdir; olculdu ki `sik_bos`
yalnizca geometride, `gorsel_yok_sekilli` yalnizca TYT biyolojide isiriyor.

TYT BIYOLOJININ 334 SEKILLI SORUSU NEDEN DISARIDA
-------------------------------------------------
Bu kitabin gorsel hatti sayfa ve SUTUN kirpimi uretti, soru kutusu
uretmedi; `question_image_url` NULL yazildi. Sekil iceren 334 soru ithalde
`bayraklar.gorsel_yok_sekilli` ile isaretlendi: metin olarak EKSIKtirler,
ogrenciye sekli olmadan gosterilirse cozulemezler. Bunlar bir kutu tespit
turundan sonra AYRI bir migration ile acilacak; sutun kirpiminin dosya adi
her satirda `pipeline_metadata.sutun_gorseli` olarak durdugu icin esleme
hazir.

KONSENSUS GEREKCESI HER KITAP ICIN AYRI YAZILDI
-----------------------------------------------
0018'in dort sinyalini kopyalamak YANLIS olurdu: o gerekce Mikro geometri
kitabina aitti ve bu uc kitapta karsiligi olmayan kanallar iceriyordu.
Her kitabin sinyalleri kendi YONTEM belgesinden okunup dogrulandi ve
`konsensus_sinyalleri` alanina AYRI AYRI yazilir.

1. GEOMETRI (GEO345_YONTEM.md)
   - anahtar_seridi_cift_okuma: cevap anahtari iki bagimsiz turda
     (7'ser ajan) okundu, beklenen sayi SOYLENMEDI (capa etkisi
     bastirildi). Sayfa duzeyi 767/776, girdi duzeyi 2735/2745.
     9 uyusmazlikta hakem turu; iki hakem 9/9 birbiriyle uyustu.
   - anahtar_numara_surekliligi: okuyuculara kural SOYLENMEDEN, 2743
     girdinin 2742'sinde akis kusursuz. Tek kirilma kitabin DIZGI HATASI
     (c2 s285 sag "11.A"), 20x dogrudan okumayla teyit edildi.
   - konu_bandi_sifir_serbestlik: 17 bant adi sayfa sirasinda tam 17 KOSU
     olusturdu; 37 ara sayfa ve 12 soluk bantli sayfa tek tek okundu,
     gizli 18. konu YOK. 2743/2743 soru bir konu blogunun icinde.

2. AYT BIYOLOJI (BIYO345_YONTEM.md)
   - anahtar_seridi_cift_okuma: iki bagimsiz okuma (farkli ifadelerle
     yazilmis iki ayri gorev), beklenen girdi sayisi HIC SOYLENMEDEN.
     Ikisi de 307 sayfa / 1303 girdi buldu; 13 uyusmazlik 10x hakem
     kirpimiyla 13/13 cozuldu; soluk anahtarli 8 sayfa 8x ile ayrica
     okundu -> 1317 girdi.
   - anahtar_numara_surekliligi: 1317 girdinin tamami tarandi, 0 KIRILMA.
   - metin_anahtar_numara_ortusmesi: METIN kanalinin bagimsiz dogrulayicisi
     -- sutun basina soru numarasi dizisi, anahtardaki numaralarla 600
     sutunun 599'unda birebir ayni. Tek sapma (s0183 sag) yuksek
     buyutmeyle bakilip YAYINEVI DIZGI HATASI oldugu goruldu.

3. TYT BIYOLOJI (BIYO345TYT_YONTEM.md)
   - konu_bandi_sifir_serbestlik: 14 kanonik bant adi sayfa sirasinda tam
     14 KOSU olusturdu; 1024/1024 soru bir blogun icinde.
   - dogrulayici_k1_k11_sifir_kusur: dogrula_ocr_json.py'nin 11 kontrolu
     0 kusur verdi. Bunlarin ikisi bagimsiz kanaldir: K3 ureticinin kendi
     'count_matches' beyanini yeniden hesaplayip YALAN SOYLUYORSA
     isaretler, K11 soru numaralarinin SAYFALAR ARASI surekliligini
     denetler (atlanan soru / kopyalanan sayfa yakalar).
   - manifest_soru_sayisi_ortusmesi: OCR turunun buldugu 1024 soru,
     goruntu hattinin kirpim manifestindeki beklenti ile birebir ayni
     (K1). Iki kanal birbirinden bagimsiz uretildi.

BU UC KITABIN HICBIRINDE SORU METNI CIFT OKUNMADI
-------------------------------------------------
0018'deki `cift_bagimsiz_okuma` sinyali METNIN iki kez okunmasiydi ve bu uc
kitabin HICBIRINDE yok; bu yuzden listelere KONULMADI. Metnin guvencesi
farkli: geometri ve AYT biyolojide numara hizalamasi, TYT biyolojide
K1-K11 denetimi. Sinyal listesi eksikligi gizlenmez, ISARETLENIR.

SINYAL LISTESINE GIRMEYEN BEDAVA CAPRAZ DOGRULAMALAR
----------------------------------------------------
Ithal sirasinda uc kitapta da canli DB ile hash carpismasi gorulmustu:
geometride 35 satir (Mikro Orijinal), AYT biyolojide 2 satir (OSYM 2025
AYT), TYT biyolojide 1 satir (OSYM 2025 TYT). Her biri hattin tamaminin
sifir serbestlik dereceli bir DIS kontroludur -- ama sirasiyla yalnizca
2743'un 35'ini, 1317'nin 2'sini, 1024'un 1'ini kapsar. Satir duzeyinde
sinyal gibi yazmak kalan satirlar icin FAZLA IDDIA olurdu; bu yuzden
`konsensus_sinyalleri` listelerine KONULMADI, yalnizca burada ve YONTEM
belgelerinde kayitlidir.

NE OLDUGU KONUSUNDA DURUST OLMA
-------------------------------
- quality_review_status: 'pending' -> 'auto_judged_high'
  'human_verified' YAZILMIYOR -- hicbir insan bu sorulari tek tek
  dogrulamadi.
- review_status: 'PENDING' -> 'APPROVED'
  Bu TOPLU sahip onayidir; metadata'ya yazilir:
      onay_turu = 'toplu_beta_sahibi'
      bireysel_denetim_yapildi = false
- is_ai_generated ALANINA DOKUNULMUYOR -- true kalir. Kapiyi acmanin kolay
  ama yanlis yolu onu false yapmakti; o yol DB'ye yanlis bir kaynak beyani
  birakirdi.
- CEVAPLAR DOGRULANMADI. Uc kitapta da tek cevap kaynagi kitabin BASILI
  ANAHTARIDIR (urun karari); sorular tekrar cozulmedi. Ustteki sinyaller
  TRANSKRIPSIYONU ve SEGMENTASYONU dogrular, cevabin kendisini degil.
  Ithal sirasinda yazilan `cozum_dogrulamasi` alani yerinde kalir.
- TYT biyolojide acilan 689 satirin 303'u `bayraklar.konu_komsudan`
  tasiyor: konusu bantsiz bir sayfadan, bir onceki bloktan devralindi.
  Bu varsayim 14 blogun tamamini kapsayan 11 ornek sayfada olculdu
  (11/11 dogru cikti) ama her bantsiz sayfa tek tek OKUNMADI. Kapiyi
  tutan bir kosul degil; burada kayit altina alinir.
- GEOMETRIDE sinav turu olculmedi: kitap TYT ve AYT sorularini KARISIK
  basiyor, satirlara kardes kitapla tutarli olsun diye 'AYT' yazildi ve
  durum `pipeline_metadata.sinav_turu_kaynagi` ile isaretli.

AYNI HASH'LI YABANCI SATIRLAR
-----------------------------
Hedef sorgusu `source_book` ile sinirlidir, bu yuzden ayni soru_hash'i
tasiyan Mikro Orijinal / OSYM satirlari bu migration'in kapsaminda
DEGILDIR; onlar kendi kaynaklarinda ve zaten aktiftir.

GERI ALINABILIR
---------------
Degistirilen her satirin ONCEKI degerleri GUNLUK'e yazilir; downgrade() tam
olarak o degerleri geri koyar ve eklenen metadata anahtarlarini siler.

Revizyon adi 18 karakter (sinir 32 -- bkz. 0016'nin ogrendigi ders).
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0023_345_beta_onay"
down_revision: Union[str, None] = "0022_biyo345tyt_konu_agaci"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "uc345_beta_onay_gunlugu_0023"

# Her kitabin KENDI olculmus sinyalleri. Kopyalanmadi; YONTEM belgelerinden
# okundu. Ayrinti icin bu dosyanin basligindaki "KONSENSUS GEREKCESI" bolumu.
KAYNAKLAR: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "345 2025 TYT-AYT Geometri Soru Bankasi",
        (
            "anahtar_seridi_cift_okuma",
            "anahtar_numara_surekliligi",
            "konu_bandi_sifir_serbestlik",
        ),
    ),
    (
        "345 2025 AYT Biyoloji Soru Bankasi",
        (
            "anahtar_seridi_cift_okuma",
            "anahtar_numara_surekliligi",
            "metin_anahtar_numara_ortusmesi",
        ),
    ),
    (
        "345 2025 TYT Biyoloji Soru Bankasi",
        (
            "konu_bandi_sifir_serbestlik",
            "dogrulayici_k1_k11_sifir_kusur",
            "manifest_soru_sayisi_ortusmesi",
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

# Kapinin KENDI kosullari olan iki bayrak evrensel olarak disarida birakilir:
# sik_bos (geometride 6 satir) ve gorsel_yok_sekilli (TYT biyolojide 334).
_HEDEF_SQL = """
SELECT qb.id, qb.is_active, qb.review_status, qs.quality_review_status
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  LEFT JOIN question_statistics qs ON qs.id = qb.id
 WHERE qm.source_book = :kaynak
   AND (qm.pipeline_metadata IS NULL
        OR NOT (qm.pipeline_metadata::jsonb ? 'bayraklar')
        OR (NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')
            AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
                     ? 'gorsel_yok_sekilli')))
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
        _log.info("[0023] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0023] mv_safe_for_beta yenilendi")


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


def _kitabi_ac(b, kaynak: str, sinyaller: tuple[str, ...]) -> int:
    """Tek bir kitabi acar; acilan satir sayisini dondurur."""
    hedef = b.execute(sa.text(_HEDEF_SQL), {"kaynak": kaynak}).fetchall()
    if not hedef:
        _log.info("[0023] %s satiri yok -- atlandi", kaynak)
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

    haric = b.execute(
        sa.text(
            "SELECT count(*) FROM question_metadata"
            " WHERE source_book = :kaynak AND id <> ALL(:idler)"
        ),
        {"kaynak": kaynak, "idler": idler},
    ).scalar_one()
    _log.info(
        "[0023] %s: %s satir acildi, bayrak nedeniyle disarida kalan: %s",
        kaynak,
        len(idler),
        haric,
    )
    return len(idler)


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0023] soru tablolari yok (taze DB?) -- atlandi")
        return

    var_mi = any(
        b.execute(
            sa.text("SELECT 1 FROM question_metadata WHERE source_book = :k LIMIT 1"),
            {"k": kaynak},
        ).first()
        for kaynak, _ in KAYNAKLAR
    )
    if not var_mi:
        _log.info("[0023] 345 serisi satiri yok -- atlandi (veri ithal edilmemis)")
        return

    _gunlugu_kur()
    toplam = sum(_kitabi_ac(b, kaynak, sinyaller) for kaynak, sinyaller in KAYNAKLAR)
    _log.info("[0023] beta kapisi acildi: toplam %s satir", toplam)
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0023] %s yok -- downgrade atlandi", GUNLUK)
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

    _log.info("[0023] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
