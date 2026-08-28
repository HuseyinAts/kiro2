# Kitapsız (sentetik) soru havuzunun silinmesi — S238, 20 Ağustos 2026

**Sonuç:** `question_bank` **40.583 → 3.616**. Silinen 36.967 satırın tamamı
yedeklendi (`*_cop_yedek_20260820`, 4 tablo × 36.967). Öğrenci kapısı
`mv_safe_for_beta` **27.073 → 0** — kasıtlı.

---

## 1. Ayırıcı: içerik sezgisi değil PROVENANS

| Ölçüt | eski parti | Y11 KIMYA |
|---|---|---|
| `source_book IS NULL` | **36.967 / 36.967** | **0 / 3.616** |
| `pipeline_metadata->>'auto_imported'='true'` | 36.967 | 0 |
| farklı `source_book` | 0 | 26 |

Yanlış-pozitif **0**, yanlış-negatif **0**. Bu bir eşik değil, kaynak kaydı.

**Ucuz içerik dedektörleri TEK BAŞINA YETMEZDİ.** Görsel-atıf / boş şık / kısa
metin / tekrar eden şık / geçersiz anahtar birleşimi aynı kümenin yalnız
**8.696**'sını (%23,5) yakalıyordu. Onlarla silinseydi **28.271 çöp havuzda
kalır** ve havuz "temizlenmiş" görünürdü — hiç yapmamaktan kötü.

## 2. Çöp olduğu ÖLÇÜLDÜ (varsayılmadı)

| Tur | Örneklem | Servis edilebilir |
|---|---|---|
| S231 (19 Ağu) | kapıdan 40 | **0 / 40** |
| S238 elle | kitapsız havuzdan 12 | **0 / 12** |
| S238 adversarial | dedektörlerin **TEMİZ dediği** alt kümeden 180 (12 ders × 15) | **0 / 180** |

Adversarial tur: 6 bağımsız yargıç; "servis edilebilir" diyen her karar 3 ayrı
mercekle (dil / çözülebilirlik / anahtar) çürütülecekti — **hiç karar çıkmadı**.

### 2.1 Aletin kendisi doğrulandı (kör kontrol kolu)

`0/180` bir ilerleme sayacında **yanlış-sıfır** olabilirdi. 60 soruluk kör set
kuruldu: 30 bilinen-İYİ (Y11, kitaplı) + 30 bilinen-KÖTÜ (kitapsız), provenans
gizli, **ders eşlendi (ikisi de KIMYA)**, id-hash'e göre karıştırıldı.

```
                yargic: SERVIS   yargic: COP
bilinen IYI        27 (TP)          3 (FN)
bilinen KOTU        0 (FP)         30 (TN)

ozgulluk   30/30 = %100     duyarlilik 27/30 = %90     yanlis-pozitif 0
```

3 kaçak (K04/K14/K25) gerçek OCR kusuru için reddedildi — yargıç haklı, yani
gerçek duyarlılık daha yüksek. **Alet kör değil.**

**Üst sınır:** ~%90 duyarlılıkla 180 çekilişte 0 bulmak → üçler kuralıyla %95
güven üst sınırı ≈ **%1,9**. Yani kitapsız havuzda en fazla ~520 satır
kurtarılabilir olabilirdi; nokta tahmini **0**. O ~520'nin de `source_book`'u
NULL, görseli yok, `irt_difficulty`'si tek değerli — adaptif sinyal taşımıyor.
Aynı anda `kiro2_temp` **187.745** gerçek satır tutuyor.

## 3. Tahribat: yok (ölçüldü)

`question_bank.id`'ye FK'li **11 tablonun 11'i** `ON DELETE CASCADE` ve
**hepsi boş** (`student_answers` dahil 0 satır). Canlıda 7 kullanıcı /
4 öğrenci profili; hiçbiri bu sorulardan birini yanıtlamamış.

## 4. Geri alınabilirlik YAPISAL

`DELETE` id kümesini predikatı yeniden değerlendirerek değil **yedek tablodan**
alır → "silinen küme == yedeklenen küme" bir assert değil, **inşa özelliği**.
Yedeklenmemiş satır silinemez.

```sql
INSERT INTO question_bank       SELECT * FROM question_bank_cop_yedek_20260820;
INSERT INTO question_content    SELECT * FROM question_content_cop_yedek_20260820;
INSERT INTO question_metadata   SELECT * FROM question_metadata_cop_yedek_20260820;
INSERT INTO question_statistics SELECT * FROM question_statistics_cop_yedek_20260820;
REFRESH MATERIALIZED VIEW mv_safe_for_beta;
```

## 5. Uygulama

PROVA (`--kalici` yok) → 13 ölçümün 13'ü beklendiği gibi, `DELETE 36967`,
`ROLLBACK` sonrası taban 40.583 / 27.073 / 0 yedek tablo. Sonra kalıcı koşum.

Bağımsız doğrulama (ayrı bağlantı, REFRESH sonrası):

```
question_bank/content/metadata/statistics = 3616 x4
mv_safe_for_beta   = 0        kalan kitapsiz = 0
kalan Y11 damgali  = 3616     farkli kaynak kitap = 26 (once 0)
YEDEK x4           = 36967
```

## 6. 🔴 SİLME İKİ BEKÇİDE **VAKUM DELİĞİ** AÇIĞA ÇIKARDI

Kapı boşalınca `test_icerik_gecerliligi.py`'de iki bekçi **XPASS(strict)** verdi:

| Bekçi | İddia | Boş kümede |
|---|---|---|
| `test_i4_inceleme_damgasi_toptan_degil` | `farkli != 1` | `0 != 1` → **kendiliğinden geçer** |
| `test_k2_anahtar_dolu_bir_sikka_isaret_ediyor` | `n_r5 == 0` | bayrak yok → **kendiliğinden geçer** |

XPASS bunu *"kusur kapandı, işareti kaldır"* diye raporluyordu. **Kusur
kapanmamıştı — ölçülecek satır kalmamıştı.** İşaretler kaldırılsaydı iki bekçi
kalıcı olarak kaybedilir, gerçek içerik geldiğinde geri dönmezlerdi.

Kardeş testler korumayı **zaten taşıyordu** (`test_i2:193`,
`test_k2_mekanik:399`: `assert toplam > 0, "Kapı BOŞ — bu bekçi hiçbir şey
ölçemez (alet arızası)"`). Aynı deyim iki eksik bekçiye taşındı.

**Ders:** *boş küme üstünde geçen bir bekçi, yeşil bir alet arızasıdır.* Bir
bekçiyi "düzeldi" diye emekliye ayırmadan önce **evrenin boş olmadığını ölç.**

## 7. Kapı durumu

22 dosyalık zorlayıcı kapı (defterden türetildi):

```
once : 197 passed / 9 skipped /  8 xfailed / 9 FAILED   EXIT=1
simdi: 197 passed / 9 skipped / 17 xfailed / 0 failed   EXIT=0
toplam 223 -- S237 tabaniyla (214+0+9) BIREBIR
```

9 CAT testi `xfail(strict)` ile ankrajlandı: dolu aday havuzu onların
**önkoşulu**, test ettikleri şey değil (SQL metni üzerinde iddia eden 3 kardeş
test boş havuzda da ölçüyor ve **geçiyor** — ayrımın kanıtı bu).

9 skip **önceden vardı** (DSN yok). DSN verilerek ayrıca koşuldu:
`benzersizlik_orani` **PASSED** (3.616'da oran ≥ 0,90), `hacim_tabani`
**XFAIL** (3.616 < 150.000 — doğru kırmızı). *Atlanan bekçi hiçbir şey ölçmez.*

## 8. Açık kalan

- **Kapı 0** — öğrenciye servis edilecek soru yok. İkmal: `kiro2_temp`
  **53.937 TYT MATEMATİK** (%98,1 görselli) — A1 kabul kriterinin tam ihtiyacı.
- 3.616 Y11 KIMYA `pending` durumda, kapının dışında (FAZ E terfi ayrı onay).
- Yedek tablolar 4 × 36.967 disk tutuyor; ikmal doğrulanınca düşürülebilir.
- `soru_hash` çakışması silme sonrası **yeniden ölçülmeli** (çapraz-DB dedup
  sayısı "34" idi; kitapsız havuz kalkınca değişmiş olabilir).

## Artefaktlar

`backend/scripts/quality/y11_cop_sil.py` · `backend/tests/fast/test_y11_cop_sil.py`
(29 test) · commit `569b995b6` (modül) · `66cd9c958` (vakum deliği) ·
`3a5d98f61` (kapı ankrajı)
