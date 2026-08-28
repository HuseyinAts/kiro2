"""U02 — FSRS aralığı YKS sınav tarihini aşmamalı.

NEDEN VAR
---------
`docs/audits/2026-08-12_25uzman/iddialar.yaml` U02, 22 Ağu 2026'da **iki bağımsız
çürütücü** tarafından `dogrulandi` olarak ölçüldü. Kanıt (canlı motor koşturuldu):

    5 ardışık PUAN_İYİ  -> interval=194 gün (kümülatif 317)
    rep4                -> interval=6055 gün, due=2043-03-21

Kök neden: `fsrs_engine.py` yalnız `MAX_INTERVAL_DAYS=36_500` (100 yıl) ile
clamp'liyordu; sınav tarihi farkındalığı YOKTU
(`grep 'yks_tarih|sinav_tarih|exam_date' fsrs_engine.py fsrs_service.py` -> 0).

İDDİADAN DAHA GENİŞ: tetikleyici "Çok Kolay" işaretlemek DEĞİL. O buton üründe
yok; `FSRSReviewPage` yalnız `{question_id, is_correct}` gönderiyor, `response_ms`
hiç gitmiyor -> `answer_to_fsrs_rating()` her zaman PUAN_İYİ(3) döndürüyor.
Yani **herhangi 2-3 ardışık doğru cevap** aynı patlamayı üretiyor.

ÜRÜN GEREKÇESİ: YKS'ye 30 gün kalmışken 194 gün sonrasına tekrar planlamak
öğrenci için değersizdir — kart sınavdan sonra gelir.

MUTASYONLA ÇİVİLENDİ (22 Ağu 2026) — her mutasyon FARKLI sayıda test öldürdü,
yani assert'ler bağımsız yük taşıyor:
  M1: cap bloğu tamamen silindi      -> 2 test düştü (iki cap testi)
  M2: cap yalnız açık parametrede uygulansın (`yks_gun_kalan()` varsayılanı
      kaldırıldı)          -> 1 test düştü (varsayılan-çağrı testi).
      KRİTİK: canlı kusuru kapatan yol budur — fsrs_service.py:327,359
      parametre GEÇMİYOR, yani yalnız açık-parametre fix'i yetmezdi.
  M3: `interval = 1` (aşırı cap)     -> 1 test düştü (kontrol kolu)
  M4: `hedef <= bugun` -> `<`        -> 1 test düştü (sınav günü 0 dönerdi)
  Geri alım sha256 ile doğrulandı: 5abc7890…

REGRESYON KONTROL KOLU: `test_fsrs_card_persistence.py` (2F+2E) ve
`test_fsrs_schema_contract.py` (2F) bu değişiklikten ÖNCE de aynı sonucu
veriyordu — kök neden `user_item_fsrs` tablosunun canlı şemada olmaması
(`to_regclass('public.user_item_fsrs')` -> NULL), bu fix'le ilgisiz.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.services.fsrs_engine import (
    DURUM_TEKRAR,
    MIN_INTERVAL_DAYS,
    PUAN_İYİ,
    FSRSState,
    _interval_from_stability,
    fsrs_update,
    yks_gun_kalan,
)


def _tekrar_state(stability: float) -> FSRSState:
    """TEKRAR aşamasında, verilen stabiliteye sahip bir kart."""
    return FSRSState(
        user_id="u-test",
        question_id="q-test",
        stability=stability,
        difficulty=5.0,
        state=DURUM_TEKRAR,
        last_review=datetime.now(UTC) - timedelta(days=1),
    )


def test_olculen_kusur_gercekten_var_capsiz_aralik_patliyor():
    """ALET DOĞRULAMASI: cap olmadan aralık gerçekten sınavı aşacak kadar büyüyor.

    Bu test fix'i ölçmez — kusurun premisini ölçer. Düşerse, bu dosyadaki
    diğer testler anlamsız hale gelir (kapatılacak bir şey yok demektir).
    """
    ham = _interval_from_stability(5000.0, desired_r=0.90)
    assert ham > 366, (
        f"cap'siz doğal aralık {ham} gün — 1 yıldan küçük çıktı, "
        "U02'nin premisi bu motorda üretilemiyor"
    )


def test_aralik_verilen_sinav_capini_asamaz():
    """Açık `max_interval_days` verildiğinde aralık onu aşmamalı."""
    sonuc = fsrs_update(_tekrar_state(5000.0), PUAN_İYİ, max_interval_days=30)

    assert (
        sonuc.interval_days <= 30
    ), f"aralık {sonuc.interval_days} gün — 30 günlük sınav cap'i aşıldı"
    assert sonuc.new_state.scheduled_days <= 30
    # due_date de cap'lenmeli — sadece interval_days'i kısmak yetmez
    sinir = datetime.now(UTC) + timedelta(days=30, hours=1)
    assert (
        sonuc.new_state.due_date <= sinir
    ), f"due_date {sonuc.new_state.due_date} cap'in ötesinde"


def test_varsayilan_cagri_da_yks_tarihini_asamaz():
    """KRİTİK: çağrı yerleri (fsrs_service.py:327,359) parametre GEÇMİYOR.

    Fix yalnız açık parametrede çalışırsa canlı kusur kapanmaz — varsayılan
    davranışın da sınav-farkında olması gerekir.
    """
    sonuc = fsrs_update(_tekrar_state(5000.0), PUAN_İYİ)

    kalan = yks_gun_kalan()
    assert sonuc.interval_days <= kalan, (
        f"varsayılan çağrıda aralık {sonuc.interval_days} gün, "
        f"YKS'ye kalan {kalan} gün — cap uygulanmamış"
    )


def test_cap_dogal_araligi_gereksiz_kismiyor():
    """KONTROL KOLU: cap, aralığı toptan 1'e düşürmemeli.

    Bu assert olmadan `interval = 1` yazan bir "fix" tüm cap testlerini
    geçerdi. Fix'in aşırıya kaçmadığını çivileyen tek assert budur.
    """
    sonuc = fsrs_update(_tekrar_state(200.0), PUAN_İYİ, max_interval_days=100_000)

    assert sonuc.interval_days > 30, (
        f"cap gevşekken bile aralık {sonuc.interval_days} güne düşmüş — "
        "fix doğal FSRS aralığını eziyor"
    )


def test_cap_minimumun_altina_inemez():
    """Sınav yarın olsa bile aralık MIN_INTERVAL_DAYS'in altına inmemeli."""
    sonuc = fsrs_update(_tekrar_state(5000.0), PUAN_İYİ, max_interval_days=0)

    assert sonuc.interval_days >= MIN_INTERVAL_DAYS
    assert sonuc.new_state.due_date > datetime.now(UTC)


def test_yks_gun_kalan_hep_pozitif_ve_bir_yili_asmaz():
    """Yardımcı invaryantı: 1 <= kalan <= 366, sınav günü dahil."""
    for bugun in (
        date(2026, 1, 1),
        date(2026, 6, 6),
        date(2026, 6, 7),  # sınav günü — 0 değil, gelecek yılınki
        date(2026, 6, 8),
        date(2026, 12, 31),
    ):
        kalan = yks_gun_kalan(bugun)
        assert 1 <= kalan <= 366, f"{bugun} için kalan={kalan} aralık dışında"
