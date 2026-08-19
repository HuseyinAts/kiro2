# Y12 içerik-geçerliliği bekçisi — metrik doğrulama kapısı (kontrol kolu)

**Tarih:** 19 Ağustos 2026 · **Oturum:** S232
**Bekçi:** `backend/tests/integration/test_icerik_gecerliligi.py`
**Alet:** `backend/scripts/quality/y12_kontrol_kolu.sql`

---

## Neden bu belge var

`.claude/rules/audit-methodology.md` → **Metrik Doğrulama Gate**: bir ölçüm metriği
uygulanmadan ÖNCE kendi doğrulamasını geçmeli — bilinen-iyiyi bilinen-kötüden
ayırmalı. Geçemezse o metrikle aksiyon ALINMAZ (word-DF metriğinin başına gelen).

Y12 sekiz iddia taşıyor. Hepsi bugünkü canlı kapıda düşüyor. **Bu tek başına
hiçbir şey kanıtlamaz** — her zaman düşen bir bekçi de her zaman düşer. Ayırt
edici olduğu, bilinen-iyi bir havuzda YEŞİL vermesiyle kanıtlanır.

---

## İki kol

| Kol | Kaynak | Neden bu etiket |
|---|---|---|
| **bilinen-KÖTÜ** | `kiro2` · `mv_safe_for_beta` (27.073) | 40 soru tek tek okundu, **0'ı servis edilebilir** (`2026-08-19_beta_kapisi_icerik_gecerliligi.md`). Bağımsız 20'lik ikinci örneklemde 1/20, `Genel` dersinden 0/22, kapı dışı `pending`'den 0/10. |
| **bilinen-İYİ** | `kiro2_temp` · `question_bank` AJH+aktif (34.982) | 187.835 soru / 420 kaynak kitap. Bağımsız hash tuzuyla 12 soru okundu, **11'i servis edilebilir ve anahtarı doğru** (Kepler yasaları, teğet çember, EBOB, `tan(arcsin 7/25)`, çift yarık girişimi — aritmetiği elle doğrulandı). |

⚠️ **Bilinen-iyi kol da bir ÖRNEKLEM sonucudur.** 12/12 değil 11/12; ve `kiro2_temp`'in
popülasyon kalite oranı ölçülmedi. Y11'e girmeden önce 40-60 satırlık stratifiye
okuma gerekir. Buradaki iddia "kiro2_temp mükemmel" değil, "kiro2_temp ile canlı
kapı arasında ölçülebilir, büyük ve tutarlı bir fark var".

⚠️ **Kontrol kolu AYNI KOD ile koşulmadı.** `kiro2_temp` pre-split şema (tek 76
kolonlu `question_bank`; `question_content`/`question_metadata`/`question_statistics`
ve `mv_safe_for_beta` YOK). Bu yüzden eşdeğer sorgu yazıldı
(`backend/scripts/quality/y12_kontrol_kolu.sql`). Y11 sonrası kaynak split şemaya
geldiğinde kontrol kolu `KIRO2_TEST_DSN=... pytest --runxfail` ile **aynı kodla**
koşulabilir hâle gelir ve o zaman öyle doğrulanmalıdır.

---

## Sonuç

| İddia | bilinen-KÖTÜ (canlı) | bilinen-İYİ (`kiro2_temp`) | Ayırt edici? |
|---|---|---|---|
| I1 `pipeline_metadata` distinct > 1 | **1** ❌ | **34.916** ✅ | evet |
| I2 `source_book` dolu oranı ≥ 0,50 | **0,0000** ❌ | **1,0000** ✅ | evet |
| I3 `primary_topic_id` distinct > 1 | **1** ❌ | **115** ✅ | evet |
| I4 `reviewed_at` distinct ≠ 1 | **1** ❌ | **0** ✅ | evet *(düzeltmeden sonra)* |
| I5 `difficulty_level` > 1 ve `irt_difficulty` > 1 | **1 / 1** ❌ | **5 / 22.559** ✅ | evet |
| I6 kapı tek kolonla açıklanamaz | **açıklanıyor** ❌ | — *(kapı eşdeğeri zaten tek yordam)* | N/A |
| K2 birleşim bayrak oranı ≤ 0,05 | **0,2075** ❌ | **0,0256** ✅ | 8,1x |
| K2 geçersiz anahtar (R5) = 0 | **105** ❌ | **0** ✅ | evet |

---

## 🔴 Kontrol kolu bu bekçiyi İKİ KEZ düzeltti

Bu bölüm belgenin asıl gerekçesi. Kontrol kolu koşulmasaydı Y12 **"8 xfailed"
verip doğru görünecekti** — ve iki kusuru fark edilmeyecekti.

### 1. I4 KÖR bir dedektördü (`> 1` → `<> 1`)

İlk sürüm `count(DISTINCT reviewed_at) > 1` diyordu. Ölçüldü:

    canlı kapı  : 1 farklı damga  -> DÜŞER  (doğru)
    kiro2_temp  : 0 farklı damga  -> DÜŞER  (YANLIŞ — hepsi NULL)

İki kolda birden düşen bir dedektör hiçbir şey ölçmez. Kusur kavramsaldı:
iddia **"hiç incelenmemiş"** ile **"incelendi yalanı"**nı karıştırıyordu.

    0 farklı  -> inceleme İDDİA EDİLMEMİŞ   (dürüst)
    1 farklı  -> toplu UPDATE imzası        (yalan)  <- yakalanması gereken
    >1 farklı -> gerçek, bireysel inceleme

### 2. K2 eşiği bilinen-İYİYİ reddediyordu (0,02 → 0,05)

İlk eşik `0,02` idi ve `d-dataset/eslesmis_sorucevap.jsonl`'in `page_inline`
katmanından (0,007) alınmıştı — **farklı bir popülasyon**. `kiro2_temp` ölçülünce
0,0256 çıktı, yani gerçek korpus eşiği geçemiyordu. Y11 mükemmel çalışsa bile
bekçi kırmızı kalacaktı.

Yeni eşik iki koldan da ölçüldü: bilinen-iyinin ~2 katı, bilinen-kötünün ~4'te biri.

---

## R6 sıkılaştırması — yanlış-pozitif OKUYARAK bulundu

`kiro2_temp`'te bayraklanan 10 satır tek tek okundu: **8 gerçek kusur, 1 doğrulanmış
yanlış-pozitif, 1 sınırda**. FP:

> **Esen Ayt Tarih** — *"Nüfus artış hızının düşürülmesi ya da yükseltilmesi
> yönünde uygulanan nüfus politikalarının, aşağıdakilerden hangisine etkisi
> beklenmez?"* · şık B) *"Nüfus artış hızı"* (17 karakter → uzunluk tabanını
> geçiyor) · **soru gerçek, yanıtlanabilir, anahtarı doğru (D)**.

R6'nın gerçek sinyali "bir şık gövdede geçiyor" değil, **"şık bloğu gövdeye
kopyalanmış"**. Eşik `≥1 şık` → `≥3 şık` yapıldı. İki kolda da ölçüldü:

| R6 varyantı | canlı | `kiro2_temp` | ayrım | birleşim (canlı / temp) |
|---|---|---|---|---|
| ≥1 şık | 968 | 232 | 5,4x | 0,2145 / 0,0288 |
| **≥3 şık** | **593** | **103** | **7,4x** | **0,2075 / 0,0256** (8,1x) |

Sıkılaştırma hem ayırt ediciliği artırdı hem FP sınıfını kaldırdı — nadir bir
ikili kazanç, ve yalnız **bayrakları okuyarak** görülebilirdi.

---

## Daha önce elenmiş kurallar (referans)

Aday 9 kuraldan 3'ü bu kapıyı **geçemedi** ve Y12'ye hiç girmedi:

| Kural | temiz katman | kirli katman | Karar |
|---|---|---|---|
| R7 figür-referansı | %23,9 | %18,8 | **ATILDI** — ters yönde ateşliyor |
| R8 tek-kelime şık + uzun gövde | %30,5 | %19,2 | **ATILDI** — ters yönde |
| R9 şık uzunluk tekdüzeliği | %24,9 | %43,3 | **ATILDI** — yalnız 1,7x; temiz katmanda dörtte bir ateşliyor (5 şıkkı da düz sayı olan soru standart YKS biçimi) |

Ayrıca **Zemberek elendi**: MCP `status: unhealthy`, `zemberek_available: false`,
ve bağlantı yokken her kelimeyi `is_correct: false` işaretleyip `accuracy: 0.0`
döndürüyor (açık-devre başarısızlık). Kontrol kolu (`göre`, `kaç`, `alanı`) da %0
çıktığı için ölçüldü ve kullanılmadı.

---

## Bu bekçinin GÖREMEDİĞİ şey (dürüst sınır)

Katman 2, bilinen-kötü kolun yalnız **%30'unu** yakalıyor. Kaçan %70 "anlamsız
Türkçe", "veri yok / yanıtlanamaz" ve **"cevap anahtarı yanlış"** sınıfı.
Özellikle: S231'in aritmetikle doğruladığı **5 anahtar-yanlış sorunun 5'i de**
9 kuralın hiçbirine takılmıyor. Anlamsal doğruluk deterministik olarak ölçülemez.

Dolayısıyla `K2 birleşim ≤ 0,05` bir **ALT SINIRDIR**. Geçmesi "havuz temiz"
DEMEZ; yalnız "havuz bu sınıftaki mekanik çöpten arınmış" der. Anlamsal
geçerlilik hâlâ örneklem okumasıyla ölçülür (Y11 kabul kriteri).

---

## Yeniden koşturma

```bash
# bilinen-KÖTÜ (canlı kapı) — 8 xfailed bekleniyor
cd backend && python -m pytest tests/integration/test_icerik_gecerliligi.py -n0 -q

# gerçek assert çıktılarını gör
cd backend && python -m pytest tests/integration/test_icerik_gecerliligi.py -n0 --runxfail --tb=line

# bilinen-İYİ (kontrol kolu) — 7/7 GECTI bekleniyor
PGPASSWORD=<parola> "C:/Program Files/PostgreSQL/18/bin/psql.exe" \
  -h localhost -p 5434 -U kiro2_app -d kiro2_temp \
  -tA -f backend/scripts/quality/y12_kontrol_kolu.sql
```

---

## İlgili

- `docs/audits/2026-08-19_beta_kapisi_icerik_gecerliligi.md` — 40 soruluk okuma (S231)
- `docs/audits/2026-08-19_beta_kapisi_orneklem.txt` — ham örneklem
- `.claude/rules/audit-methodology.md` — Metrik Doğrulama Gate · Ucuz Filtre Tuzağı
- `backend/tests/db/test_question_bank_invariants.py` — kardeş hacim/benzersizlik bekçisi
