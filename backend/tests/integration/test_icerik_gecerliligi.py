"""Y12 — öğrenci kapısının İÇERİK GEÇERLİLİĞİ bekçisi (19 Ağu 2026).

NEDEN VAR
---------
19 Ağu 2026'da `mv_safe_for_beta` (öğrenci kapısı, 27.073 satır) içinden 40 soru
çekilip tek tek okundu. Sonuç: **0'ı servis edilebilir** — %87,5 yanıtlanamaz/bozuk,
%12,5 yanıtlanabilir ama cevap anahtarı yanlış.
(`docs/audits/2026-08-19_beta_kapisi_icerik_gecerliligi.md`, commit `9015ba42b`)

Bu durumu yakalayan **hiçbir test yoktu**. Var olanların hepsi HACİM veya ŞEKİL
ölçüyordu:

    test_question_bank_invariants.py  -> satır sayısı + benzersizlik oranı
    test_quality_gate_leak.py         -> kapı üyeliği (sızıntı var mı)
    test_osym_exam_engine_split.py    -> sorgu WHERE'i doğru mu

Üçü de 27.073 satırlık çöp havuzda YEŞİL kalır. Ders (`L-s231-hacim-vekil-olcum-
icerik-degil`): **hacim bir vekil ölçümdür; içerik geçerliliği ayrı bir ölçümdür.**

İKİ KATMAN — VE NEDEN İKİSİ BİRDEN
-----------------------------------
KATMAN 1 (dağılım invaryantları) evren düzeyinde çalışır ve yanlış-pozitif
üretemez: bir *yargı* taşıdığı iddia edilen alan tek değerliyse, o yargı hiç
yapılmamıştır. 19 Ağu'da `pipeline_metadata` 36.967 satırın **hepsinde birebir
aynı 51 karakterlik dize** idi (`{"student_coherent": "true", "auto_imported":
true}`) ve `reviewed_at` 36.967 satırda **aynı mikrosaniye**. Katman 1 bunu tek
sorguyla yakalar.

KATMAN 2 (satır-içi yapısal kurallar) daha erken uyarı verir ama ucuz-filtre
tuzağı taşır (`.claude/rules/audit-methodology.md`: Türkçe STEM'de naif filtreler
~%89 yanlış-pozitif üretti). Bu yüzden buradaki 6 kural **ölçülerek seçildi**,
tahminle değil:

    aday 9 kural -> 3'ü ATILDI, çünkü doğrulama-1'i geçemediler:
      R7 figür-referansı : temiz katmanda %23,9 vs kirli %18,8  (TERS YÖNDE)
      R8 tek-kelime şık  : temiz %30,5 vs kirli %19,2           (TERS YÖNDE)
      R9 şık uzunluk eşitliği : yalnız 1,7 kat ayırım           (ZAYIF)

    kalan 6 kural, `d-dataset/eslesmis_sorucevap.jsonl` üzerinde ölçüldü:
      gerçek kitap katmanı (page_inline, 55.867)  -> %0,7 bayrak
      AI türevi katman     (21.469)                -> %17,0 bayrak
      => 24 kat ayrım. İyi koldaki 23 bayrağın 23'ü tek tek okundu:
         DOĞRULANMIŞ YANLIŞ-POZİTİF = 0.

DÜRÜST SINIR — bu bekçinin GÖREMEDİĞİ şey
------------------------------------------
Katman 2 kötü kolun yalnız **%30'unu** yakalar. Kaçan %70 "anlamsız Türkçe",
"veri yok, yanıtlanamaz" ve "cevap anahtarı yanlış" sınıfıdır. Özellikle:
**5 anahtar-yanlış sorunun 5'i de 9 kuralın hiçbirine takılmıyor.** Anlamsal
doğruluk deterministik olarak ölçülemez. Bu yüzden `bayrak oranı <= %2` iddiası
bir ALT SINIRDIR — geçmesi "havuz temiz" demek DEĞİLDİR, yalnız "havuz bu
sınıftaki mekanik çöpten arınmış" demektir.

Zemberek (morfolojik sinyal) bugün kullanılamıyor: MCP `status: unhealthy`,
`zemberek_available: false`, ve bağlantı yokken her kelimeyi `is_correct: false`
işaretleyip `accuracy: 0.0` döndürüyor — yani AÇIK-DEVRE başarısız oluyor.
Kontrol kolu (`göre`, `kaç`, `alanı`) da %0 çıktığı için ölçüldü ve elendi.

KONTROL KOLU (metrik doğrulama kapısı — bu bekçinin kendi doğrulaması)
----------------------------------------------------------------------
Bir dedektörün ayırt edici olduğu, hem bilinen-kötüyü kırmızıya hem bilinen-iyiyi
yeşile çevirmesiyle KANITLANIR. İkisi de kırmızıysa dedektör kördür.

Aynı sunucuda `kiro2_temp` veritabanı duruyor: 187.835 soru / 420 kaynak kitap /
5 zorluk seviyesi / 68.022 farklı `irt_difficulty`. Örneklem okundu: 12 sorunun
11'i servis edilebilir ve anahtarı doğru.

ÖLÇÜLDÜ (19 Ağu 2026) — her iddia iki kolda birden:

    iddia                     bilinen-KÖTÜ (canlı)   bilinen-İYİ (kiro2_temp)
    ----------------------    --------------------   ------------------------
    I1 pipeline_metadata      1 farklı        ❌      34.916 farklı        ✅
    I2 source_book oranı      0,0000          ❌      1,0000               ✅
    I3 primary_topic_id       1 farklı        ❌      115 farklı           ✅
    I4 reviewed_at            1 farklı        ❌      0 (hiç iddia yok)    ✅
    I5 zorluk / irt           1 / 1           ❌      5 / 22.559           ✅
    K2 birleşim bayrak oranı  0,2075          ❌      0,0256               ✅
    K2 geçersiz anahtar (R5)  105 satır       ❌      0 satır              ✅

⚠️ KONTROL KOLU BU DOSYAYI İKİ KEZ DÜZELTTİ — ve bu, kontrol kolunun süs
olmadığının kanıtıdır:
  1. I4 ilk sürümde `> 1` idi ve İKİ KOLDA DA düşüyordu (kör dedektör).
     `<> 1` yapıldı (aşağıda gerekçesi).
  2. K2 eşiği ilk sürümde 0,02 idi ve kontrol kolu 0,0256 ile DÜŞÜYORDU.
     Eşik ölçüme dayandırılıp 0,05'e çekildi.
Kontrol kolu koşulmasaydı bu dosya "8 xfailed" verip DOĞRU görünecekti.

⚠️ SINIR: `kiro2_temp` PRE-SPLIT şema (tek 76 kolonlu `question_bank`;
`question_content`/`question_metadata`/`question_statistics` ve
`mv_safe_for_beta` YOK). Bu yüzden kontrol kolu AYNI KOD ile değil, EŞDEĞER
SORGU ile koşuldu (`docs/audits/2026-08-19_y12_kontrol_kolu.md`). Y11 sonrası
kaynak split şemaya geldiğinde kontrol kolu aynı kodla koşulabilir hâle gelir
ve o zaman `--runxfail` ile doğrudan doğrulanmalıdır.

    # BILINEN-KOTU (bugunku canli kapi) -> hepsi xfailed olmali
    cd backend && pytest tests/integration/test_icerik_gecerliligi.py -v

    # BILINEN-IYI (kontrol kolu) -> --runxfail ile hepsi PASSED olmali
    KIRO2_TEST_DSN='postgresql://<kullanici>:<parola>@localhost:5434/kiro2_temp' \\
      pytest tests/integration/test_icerik_gecerliligi.py --runxfail -v

Kontrol kolu YEŞİL vermiyorsa bu dosya bir şey ölçmüyordur ve SİLİNMELİDİR.

NEDEN xfail(strict=True)
------------------------
Eşikler hedef değerlerde; bugün hepsi ihlal hâlinde. `xfail` bugünkü push'u
bloklamaz, ama **Y11 içeriği düzelttiği anda XPASS verip kırar** — yani "düzeldi,
işareti kaldır" sinyali otomatik gelir. Eşikleri bugüne göre ayarlamak (örn.
`bayrak oranı <= %25`) tam olarak vakum-bekçi desenidir: 0/40 servis edilebilir
bir havuzu TEST TARAFINDAN ONAYLANMIŞ hâle getirirdi.

⚠️ Her `xfail` gerekçesi **Y11 ankrajı taşımak ZORUNDA**. Ankrajsız bir xfail,
kâğıt üzerinde kalan bir bekçidir.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

pytestmark = [pytest.mark.icerik_gecerliligi, pytest.mark.asyncio]

# Y11 kapanınca bu işaretler KALDIRILACAK. Tek yerden, ki unutulmasın.
_Y11 = (
    "Y11 AÇIK: kapı içeriği sentetik dolgu (S231, 40/40 okundu, 0 servis "
    "edilebilir). Kaynak `kiro2_temp` (187.835 soru / 420 kitap). Y11 "
    "kapanınca bu xfail işareti KALDIRILACAK — XPASS zaten kıracak."
)


def _y11_xfail(ne: str):
    return pytest.mark.xfail(strict=True, reason=f"{ne} — {_Y11}")


# --- eşikler (hepsi hedef değerde; bugünkü değer yorumda) ------------------

MIN_KAYNAK_KITAP_ORANI = 0.50  # bugün: 0,00 (27.073/27.073 source_book NULL)

# Eşik İKİ KOLDA DA ölçülerek konuldu, tahminle değil (19 Ağu 2026):
#     bilinen-KÖTÜ (canlı kapı, 27.073)      -> 0,2075
#     bilinen-İYİ  (kiro2_temp AJH, 34.982)  -> 0,0256
# 0,05 = bilinen-iyinin ~2 katı (gürültü payı) ve bilinen-kötünün ~4'te biri.
# İlk denenen 0,02 KONTROL KOLUNU DÜŞÜRÜYORDU — yani bekçiyi kör yapardı.
MAKS_BAYRAK_ORANI = 0.05


async def _skaler(oturum, sql: str):
    return (await oturum.execute(text(sql))).scalar_one()


# ===========================================================================
# KATMAN 1 — dağılım invaryantları (evren düzeyi, yanlış-pozitif üretemez)
# ===========================================================================


@_y11_xfail("pipeline_metadata 36.967 satırın hepsinde birebir aynı 51 karakter")
async def test_i1_pipeline_metadata_bilgi_tasiyor(live_db):
    """Yargı taşıdığı iddia edilen alan tek değerliyse, o yargı hiç yapılmamıştır.

    `student_coherent` ve `auto_imported` KOLON DEĞİL — ikisi de bu JSONB'nin
    içinde yaşıyor. 19 Ağu ölçümü: `count(DISTINCT pipeline_metadata::text) = 1`,
    `min(length) = max(length) = 51`. Yani 27.073 satıra toptan basılmış.
    """
    farkli = await _skaler(
        live_db,
        "SELECT count(DISTINCT qm.pipeline_metadata::text) "
        "FROM mv_safe_for_beta m JOIN question_metadata qm ON qm.id = m.id",
    )
    assert farkli > 1, (
        f"pipeline_metadata kapıdaki her satırda AYNI ({farkli} farklı değer). "
        "Bir yargı bayrağı tek değerliyse yargı değil VARSAYIMDIR — "
        "`student_coherent=true` 27.073 satıra toptan basılmış ve okunan 40'ın "
        "en az 35'inde YANLIŞ."
    )


@_y11_xfail("source_book kapıdaki 27.073 satırın 27.073'ünde NULL")
async def test_i2_sorularin_kaynak_kitabi_var(live_db):
    """Kaynağı olmayan soru izlenebilir değildir.

    CLAUDE.md "405 kaynak kitaptan derlenmiş" diyor; canlı DB'de
    `question_metadata.source_book IS NOT NULL` = **0 / 36.967**.
    `kiro2_temp`'te aynı ölçüm: 187.725 / 187.835 (420 farklı kitap).
    """
    toplam, dolu = (
        await live_db.execute(
            text(
                "SELECT count(*), count(qm.source_book) "
                "FROM mv_safe_for_beta m JOIN question_metadata qm ON qm.id = m.id"
            )
        )
    ).one()
    assert toplam > 0, "Kapı BOŞ — bu bekçi hiçbir şey ölçemez (alet arızası)."
    oran = dolu / toplam
    assert oran >= MIN_KAYNAK_KITAP_ORANI, (
        f"Kapıdaki {toplam:,} sorunun yalnız {dolu:,}'inde kaynak kitap var "
        f"(oran {oran:.3f}, taban {MIN_KAYNAK_KITAP_ORANI}). Kaynaksız içerik "
        "izlenebilir değil ve bu depoda sentetik dolgunun birincil imzasıdır."
    )


@_y11_xfail("primary_topic_id 36.967 satırın hepsinde 'Genel' (12 konudan 1'i)")
async def test_i3_konu_dagilimi_var(live_db):
    """Tüm sorular tek konuya bağlıysa konu-bazlı öğrenme yolu anlamsızdır.

    `topic_hierarchy` 12 konu taşıyor, kapı 1'ini kullanıyor.
    """
    farkli = await _skaler(
        live_db,
        "SELECT count(DISTINCT qb.primary_topic_id) "
        "FROM mv_safe_for_beta m JOIN question_bank qb ON qb.id = m.id",
    )
    assert farkli > 1, (
        f"Kapıdaki her soru AYNI konuya bağlı ({farkli} farklı konu). "
        "Konu-bazlı öğrenme yolu, zayıf-konu tespiti ve DAG önkoşulları "
        "bu havuzda yapısal olarak çalışamaz."
    )


@_y11_xfail(
    "kapı BOŞ (0 satır) — 36.967 kitapsız satır 20 Ağu'da silindi; önceki "
    "kusur: reviewed_at 36.967 satırda aynı mikrosaniye (2026-08-17 05:08:04.105754)"
)
async def test_i4_inceleme_damgasi_toptan_degil(live_db):
    """Tek bir zaman damgası = tek bir toplu UPDATE = gerçek inceleme yok.

    İnceleme bireysel bir eylemdir; 27.073 satırın aynı mikrosaniyede
    incelenmiş olması fiziksel olarak imkânsızdır.

    ⚠️ İDDİA `> 1` DEĞİL `<> 1` — bunu KONTROL KOLU yakaladı, tasarım değil.
    İlk sürüm `> 1` diyordu ve `kiro2_temp`'te de DÜŞÜYORDU (orada damga
    36.982/34.982 NULL, yani distinct = 0). İki kolda birden düşen bir
    dedektör kördür ve atılır. Doğru ayrım:

        0 farklı  -> inceleme İDDİA EDİLMEMİŞ (dürüst; bilinen-iyi kol böyle)
        1 farklı  -> toplu UPDATE imzası — "incelendi" YALANI (bilinen-kötü)
        >1 farklı -> gerçek, bireysel inceleme

    `> 1` "hiç incelenmemiş"i "yalan söylemiş" ile karıştırıyordu.
    """
    toplam, farkli = (
        await live_db.execute(
            text(
                "SELECT count(*), count(DISTINCT qs.reviewed_at) "
                "FROM mv_safe_for_beta m JOIN question_statistics qs ON qs.id = m.id"
            )
        )
    ).one()
    # ⚠️ BOŞ KAPI MUAFİYET DEĞİL. `farkli != 1` iddiası boş kümede 0 != 1 ile
    # KENDİLİĞİNDEN geçer. 20 Ağu 2026'da kapı 27.073 -> 0'a düştüğünde bu test
    # XPASS verdi ve "kusur kapandı" diye okundu — kapanmamıştı, ölçülecek satır
    # kalmamıştı. `test_i2`/`test_k2_mekanik` bu korumayı zaten taşıyordu; bu iki
    # bekçide eksikti. Boş küme üstünde geçen bir bekçi, YEŞİL bir alet arızasıdır.
    assert toplam > 0, "Kapı BOŞ — bu bekçi hiçbir şey ölçemez (alet arızası)."
    assert farkli != 1, (
        f"Kapıdaki tüm satırlar AYNI anda 'incelenmiş' ({farkli} farklı damga). "
        "Bu bir toplu UPDATE imzasıdır; `quality_review_status='auto_judged_high'` "
        "hak edilmemiş."
    )


@_y11_xfail("difficulty_level 36.967 satırın hepsi MEDIUM; irt_difficulty 1 değer")
async def test_i5_zorluk_sinyali_ayristirici(live_db):
    """Adaptif motorun (IRT/ZPD/CAT) TEK ayrıştırıcı girdisi budur.

    Tek değerliyse CAT bir sonraki soruyu seçemez, ZPD hesaplanamaz, warm-up
    havuzu boş kalır. `kiro2_temp`: 5 zorluk seviyesi + 68.022 farklı
    `irt_difficulty`. Bu, Y4'ün askıya alınma sebebidir.
    """
    zorluk, irt = (
        await live_db.execute(
            text(
                "SELECT count(DISTINCT qs.difficulty_level), "
                "       count(DISTINCT qs.irt_difficulty) "
                "FROM mv_safe_for_beta m JOIN question_statistics qs ON qs.id = m.id"
            )
        )
    ).one()
    assert zorluk > 1 and irt > 1, (
        f"Zorluk sinyali ayrıştırıcı değil: difficulty_level {zorluk} farklı "
        f"değer, irt_difficulty {irt} farklı değer. Adaptif motorun tek girdisi "
        "bu; tek değerliyken CAT/ZPD/warm-up yapısal olarak çalışamaz "
        "(Y4 bu yüzden askıda)."
    )


@_y11_xfail("kapının elemesi tek başına quality_review_status ile birebir açıklanıyor")
async def test_i6_kapi_lastik_damga_degil(live_db):
    """Kapı birden fazla boyutta elemeli — tek yordamlı kapı lastik damgadır.

    `v_safe_for_beta` 7 yordam taşıyor ama 19 Ağu ölçümünde 6'sı NO-OP
    (36.967/36.967 geçiyor). Ölçüm: tek başına `quality_review_status` ile
    seçilen küme `mv_safe_for_beta` ile İKİ YÖNLÜ birebir aynı (EXCEPT = 0/0).

    Bu iddia görünüm tanımını KOPYALAMAZ — yalnız sonucun tek kolonla
    açıklanabilir olup olmadığını sorar, o yüzden tanım değişince kırılmaz.
    """
    tek_kolon_disinda_elenen = await _skaler(
        live_db,
        # quality_review_status'e göre geçmesi gerekip kapıda OLMAYAN satırlar.
        # >0 ise kapı en az bir başka boyutta daha eliyor demektir.
        "SELECT count(*) FROM question_bank qb "
        "JOIN question_statistics qs ON qs.id = qb.id "
        "WHERE qs.quality_review_status IN ('human_verified', 'auto_judged_high') "
        "  AND qb.id NOT IN (SELECT id FROM mv_safe_for_beta)",
    )
    assert tek_kolon_disinda_elenen > 0, (
        "Kapının elediği her satır TEK BAŞINA `quality_review_status` ile "
        "açıklanıyor — diğer 6 yordam hiçbir satır elemiyor (no-op). "
        "Kapı çok boyutlu bir kalite kontrolü değil, tek kolonluk bir lastik "
        "damga. Kaynak kitap, tutarlılık ve eşleşme yordamları fiilen ölü."
    )


# ===========================================================================
# KATMAN 2 — satır-içi yapısal kurallar (ölçülerek seçildi; 0 doğrulanmış FP)
# ===========================================================================

# Şık normalizasyonu MATEMATİK-GÜVENLİ olmalı: A3 ölçümünde "noktalama sil"
# yaklaşımı `+`/`-` işaretlerini siliyordu ve `(x-2)²+(y+1)²=16` ile
# `(x+2)²+(y-1)²=16`'yı AYNI sayıyordu -> 41 FP'nin 27'si bu alet arızasıydı.
# Bu yüzden YALNIZ baştaki harf etiketi (`A) `, `B. `) soyulur; iç noktalama
# ve işaretler DOKUNULMADAN kalır.
# NOT: Bu SQL bilerek DÜZ bir dize (f-string değil). İlk sürüm normalizasyonu
# `_NORM.format(k=...)` şablonuyla kuruyordu; ruff `S608` (f-string ile SQL)
# ile HAKLI olarak blokladı. Şablon zaten TEK yerde kullanılıyordu, yani
# çivilenemeyen ağırlıktı — `noqa` eklemek yerine şablon kaldırıldı.
# Bu sorgu hiçbir dış girdi almaz; tüm parametreler literal.
_KURALLAR_SQL = r"""
WITH kapi AS (
    SELECT m.id, c.question_text AS metin,
           c.option_a, c.option_b, c.option_c, c.option_d, c.option_e,
           c.correct_answer AS anahtar
    FROM mv_safe_for_beta m
    JOIN question_content c ON c.id = m.id
),
bayraklar AS (
    SELECT
      id,
      -- R1b: en az iki şık, harf etiketi soyulduktan sonra BİREBİR aynı.
      -- Naif `count(DISTINCT option_x)` bu veride 40/40 soruda 5 döndürüyordu:
      -- tekrar eden şıklar `A) `/`B) ` önekiyle yapay olarak ayrışıyor.
      (SELECT count(DISTINCT lower(btrim(regexp_replace(x, '^\s*[A-Ea-e][).]\s*', ''))))
         FROM unnest(ARRAY[option_a, option_b, option_c, option_d, option_e]) x
        WHERE x IS NOT NULL AND btrim(x) <> '') < 5 AS r1b,

      -- R2: beş şıkkın hepsi 10'un kuvveti ve hepsi farklı basamakta.
      -- Uydurma sorunun imzası: 100 / 1000 / 10000 / 100000 / 1000000
      ((SELECT count(*) FROM unnest(ARRAY[option_a, option_b, option_c,
                                          option_d, option_e]) x
         WHERE btrim(x) ~ '^1[0]*$') = 5
       AND (SELECT count(DISTINCT length(btrim(x)))
              FROM unnest(ARRAY[option_a, option_b, option_c,
                                option_d, option_e]) x) = 5) AS r2,

      -- R3: şıklar soru gövdesine gömülmüş (gövdede A) B) C) birlikte).
      (metin LIKE '%A)%' AND metin LIKE '%B)%' AND metin LIKE '%C)%') AS r3,

      -- R4: gövde tek başına yetersiz.
      (length(metin) < 40) AS r4,

      -- R5: anahtar A-E dışında VEYA boş bir şıkka işaret ediyor.
      (anahtar IS NULL OR anahtar NOT IN ('A','B','C','D','E')
       OR btrim(coalesce(
            CASE anahtar WHEN 'A' THEN option_a WHEN 'B' THEN option_b
                         WHEN 'C' THEN option_c WHEN 'D' THEN option_d
                         WHEN 'E' THEN option_e END, '')) = '') AS r5,

      -- R6: ŞIK BLOĞU gövdeye kopyalanmış — en az ÜÇ şık gövdenin birebir
      -- alt dizesi (her biri >=15 karakter).
      --
      -- ⚠️ ">=1 şık" değil ">=3 şık" — bunu YANLIŞ-POZİTİF OKUMA belirledi.
      -- İlk sürüm tek şık eşleşmesine ateşliyordu ve `kiro2_temp`'ten okunan
      -- 10 bayrağın 1'i MEŞRU bir soruydu: "Nüfus artış hızının düşürülmesi
      -- ya da yükseltilmesi..." gövdesi + şık B) "Nüfus artış hızı" (17
      -- karakter, uzunluk tabanını geçiyor). Soru gerçek, yanıtlanabilir ve
      -- anahtarı doğru (D).
      --
      -- Ölçüldü (19 Ağu, iki kol): >=1 -> canlı 968 / temp 232 (5,4x)
      --                            >=3 -> canlı 593 / temp 103 (7,4x)
      -- Sıkılaştırma HEM ayırt ediciliği artırdı HEM FP sınıfını kaldırdı.
      (SELECT count(*) FROM unnest(ARRAY[option_a, option_b, option_c,
                                         option_d, option_e]) x
        WHERE length(btrim(x)) >= 15 AND position(btrim(x) in metin) > 0) >= 3
        AS r6
    FROM kapi
)
SELECT count(*)                                              AS toplam,
       count(*) FILTER (WHERE r1b)                           AS n_r1b,
       count(*) FILTER (WHERE r2)                            AS n_r2,
       count(*) FILTER (WHERE r3)                            AS n_r3,
       count(*) FILTER (WHERE r4)                            AS n_r4,
       count(*) FILTER (WHERE r5)                            AS n_r5,
       count(*) FILTER (WHERE r6)                            AS n_r6,
       count(*) FILTER (WHERE r1b OR r2 OR r3 OR r4 OR r5 OR r6) AS n_birlesim
FROM bayraklar
"""


@_y11_xfail("kapıda birleşim bayrak oranı ~%21,4; gerçek kitap korpusunda %0,7")
async def test_k2_mekanik_cop_orani_tabanin_altinda(live_db):
    """Ölçülmüş 6 kuralın birleşimi kapının en fazla %2'sini bayraklamalı.

    Bu bir ALT SINIR iddiasıdır. Geçmesi "havuz temiz" DEMEZ — bu kural kümesi
    bilinen-kötü kolun yalnız %30'unu yakalıyor; anlamsal kusurları (anahtar
    yanlış, yanıtlanamaz) yapısal olarak göremez. Geçmemesi ise kesin bir
    bulgudur: gerçek kitap korpusunda bu oran %0,7.
    """
    satir = (await live_db.execute(text(_KURALLAR_SQL))).one()
    toplam = satir.toplam
    assert toplam > 0, "Kapı BOŞ — bu bekçi hiçbir şey ölçemez (alet arızası)."

    oran = satir.n_birlesim / toplam
    kirilim = (
        f"R1b(şık kopyası)={satir.n_r1b} R2(10'un kuvveti)={satir.n_r2} "
        f"R3(şık gövdede)={satir.n_r3} R4(gövde<40)={satir.n_r4} "
        f"R5(anahtar geçersiz)={satir.n_r5} R6(şık gövdenin alt dizesi)={satir.n_r6}"
    )
    assert oran <= MAKS_BAYRAK_ORANI, (
        f"Kapıdaki {toplam:,} sorunun {satir.n_birlesim:,}'i mekanik çöp "
        f"bayrağı taşıyor (oran {oran:.3f}, taban {MAKS_BAYRAK_ORANI}).\n"
        f"  kırılım: {kirilim}\n"
        "  kontrol kolu: gerçek kitap korpusu (page_inline, 55.867) = 0,007.\n"
        "  NOT: bu bir ALT SINIRDIR — kural kümesi anlamsal kusurları görmez, "
        "yani gerçek çöp oranı bu sayının ÜSTÜNDE olabilir."
    )


@_y11_xfail(
    "kapı BOŞ (0 satır) — 36.967 kitapsız satır 20 Ağu'da silindi; önceki "
    "kusur: kapıda 105 satırın anahtarı BOŞ şıkka işaret ediyor"
)
async def test_k2_anahtar_dolu_bir_sikka_isaret_ediyor(live_db):
    """R5 tek başına: yanıtlanması matematiksel olarak imkânsız sorular.

    Ayrı test, çünkü bu sınıfın tolere edilebilir bir oranı YOKTUR — birleşim
    eşiği (%2) bunu içinde eritebilirdi. Anahtarı boş şıkka bakan bir soru,
    havuzun geri kalanı ne kadar temiz olursa olsun servis edilemez.
    """
    satir = (await live_db.execute(text(_KURALLAR_SQL))).one()
    # Bkz. `test_i4`: `n_r5 == 0` boş kapıda kendiliğinden geçer. Kardeş test
    # `test_k2_mekanik_cop_orani_tabanin_altinda` bu satırı zaten taşıyordu.
    assert satir.toplam > 0, "Kapı BOŞ — bu bekçi hiçbir şey ölçemez (alet arızası)."
    assert satir.n_r5 == 0, (
        f"Kapıda {satir.n_r5:,} sorunun cevap anahtarı geçersiz: ya A-E dışında "
        "ya da BOŞ bir şıkka işaret ediyor. Bu sorular hiçbir öğrenci "
        "tarafından doğru yanıtlanamaz."
    )
