# Fallback Audit — 30 Random Sample
**Tarih:** 13 May 2026
**Pool:** v4.14e Gemini Flash fallback (41,473 satir)
**Method:** RANDOM(), 30 sample

---

## Benim sayilarim (tek basina metinle dogrulayabildiklerim)

### **Kategori A — Net dogru cevap (10 soru)** ✓

3, 7, 9, 11, 12, 15, 20, 21, 23, 29

### **Kategori B — Net yanlis cevap (1 soru)** ✗

**#6** (ACIL-Geometri-296): A(m,-2) ile B(3,1) uzakligi 5 → (m-3)²+9=25 → m=7 veya m=-1 → carpim = **-7**. DB'de cevap **D=-4 (YANLIS)**. Dogru = A=-7.

### **Kategori C — Hatali soru / OCR'de duplicate option (2 soru)** ⚠️

**#4** (Aktif-Kimya): I ve III bilesikleri **birebir ayni** (CH3-CH2-CH2-OH). Karsilastirma yapilamaz, soru hatali.

**#25** (345-Geometri): E sikinda "$\frac{36}{7}$ (Tekrar eden sik, muhtemelen hata)" — pipeline kendi acikladigi OCR duplicate.

### **Kategori D — Suheli (1 soru)** ?

**#17** (Iki cember tegeti): DB cevap C=24, benim hesabim 18√2≈25.46. Belki gorsel farkli geometri.

### **Kategori E — Konu etiketi yanlis (1 soru)** ⚠️

**#29** (WWF raporu): source_book="Esen Ayt **Tarih** Soru Bankasi" ama soru **cevre/cografya** icerikli. Topic mapping fallback haklisindeki kanit — kitap etiketi tutarsiz.

### **Kategori F — Gorsel gerekli, dogrulayamam (15 soru)**

1, 2, 5, 8, 10, 13, 14, 16, 18, 19, 22, 26, 27, 28, 30 — diyagram/sekil/grafik referansli.

---

## Istatistik (15 dogrulanabilir orneklemde)

| Sonuc | n | % (of 15) | % (of 30) |
|---|---|---|---|
| Net dogru | 10 | 67% | 33% |
| Net yanlis | 1 | 7% | 3% |
| Hatali soru / OCR duplicate | 2 | 13% | 7% |
| Supheli | 1 | 7% | 3% |
| Konu etiketi yanlis (cevap dogru) | 1 | 7% | 3% |

**Net dogruluk oranı (dogrulanabilir grupta):** %67-73

---

## Yorum

Bu, A**sama 2a'nin gerekceleri ile celisiyor.**

- Asama 1 (demoted): 5 ornekte 2 yanlis cevap = **%60 hatalı**. Cikarilmasi haklı.
- Fallback (bu audit): 15 ornekte 1 kesin yanlis + 2 OCR duplicate = **%80 toplam saglikli**.

Yani fallback grubu, **demoted grup kadar kotu degil**. Asama 2a'da 41,473 sorunun cogu (%73-80) muhtemelen dogru cevaplari iceriyordu. Korlemesine cikarmak gereksiz kayba neden olmus olabilir.

**Onemli not:** Bu istatistik %50 sample'da gorsel-gerektigi icin yapilamadi. Gercek dogruluk olcumu kitap denetimi gerektirir. Yine de "dogrulanabilir sub-set" gostergesi cok dusuk degil.

## Asama 2a kararının yeniden degerlendirmesi

Uc olasi yon:

**Yon 1 — Tam rollback:** Asama 2a'yi geri al, fallback'leri beta havuzuna geri koy.
- Beta count: 81,760 → 123,233
- Risk: %20'de hatali/supheli, IRT calibration biraz bozulur ama buyuk degil
- Kazanim: 41,473 muhtemelen-saglikli soru beta'da

**Yon 2 — Hedefli dislama:** Sadece `fallback AND has_diagram=true` olanlari cikar.
- Hipotez: Gorsel + konu yanlis = cok riskli; gorselsiz fallback = dogruluk yuksek
- Sayim gerekli: kac fallback'in has_diagram=true?

**Yon 3 — Devam (Asama 2a'yi koru):** Defansif kalsin, %20 risk yine de fazla.
- Onceki argument: STRATEJI_B_KARAR.md'deki %15-17 DLQ yapısal zayıflığı + duplicate option riski.

## Onerim

**Yon 2 (hedefli) en mantikli.** Iki adım:
1. `fallback AND has_diagram=true` sayisini ol
2. Eger %20-30 ise: hedefli ekstra filter, geri kalan fallback'leri tut
3. Eger >%60 ise: Asama 2a yine de hakli
