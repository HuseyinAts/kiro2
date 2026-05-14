# C1+C2+C3 Audit Scoring Guide

**Tarih:** 14 May 2026 (Faz 0.2)
**Hedef:** 110 sample (30+50+30) için her satıra `verdict` + `error_type` + `notes` doldur.
**Süre:** 2-3 saat toplam (saatte ~40-50 satır).

---

## Dosyalar

| Dosya | n | Yöntem |
|---|---|---|
| `20260515_audit_C1_SCORING.tsv` | 30 | Excel/LibreOffice'te aç, son 3 kolonu doldur, kaydet |
| `20260515_audit_C2_SCORING.tsv` | 50 | Aynı |
| `20260515_audit_C3_SCORING.tsv` | 30 | Aynı |

**Tip:** Excel'de aç → "Veri" tab → "Metinden Sütunlara" → Tab delimiter → multi-line cells doğru görünür.

---

## Üç Audit Üç Farklı Soru Soruyor

### C1 — Missing Diagram Audit (30 satır)

**Hedef soru:** "Bu sorunun gerçekten bir diyagrama ihtiyacı var mı, yoksa `has_diagram=true` flag'i yanlış mı?"

| verdict | Anlam |
|---|---|
| `pass` | Soru text-only çözülebilir; flag yanlış set edilmiş |
| `fail` | Soru gerçekten diyagram gerektiriyor (şekil, grafik, koordinat sistemi) ve image yok = beta'ya alınmamalı |
| `unclear` | Karar veremedim, kitaba bakmam lazım |

**Tipik fail örneği:** "Aşağıdaki dik koordinat düzleminde d: y=18-3x doğrusu, y=4x²-x³ eğrisine T noktasında teğettir. Boyalı A ve B alanlarının toplamı..." → "boyalı alanlar" diyagramda gösteriliyor → fail.

**Tipik pass örneği:** "ABCD kare, $|EF|=2$, $|AD|=10$, ADE üçgeninin çevresi..." → tam metin verilmiş, diyagram olmadan da çözülebilir → pass.

---

### C2 — Wrong Answer Audit (50 satır)

**Hedef soru:** "DB'deki `correct_answer` matematik/mantık olarak doğru mu?"

| verdict | Anlam |
|---|---|
| `pass` | Cevap doğru, kontrolden geçti |
| `fail` | Cevap yanlış (yaptım, başka çıktı) veya soru-cevap uyumsuz |
| `unclear` | Hesaplayamadım, soru eksik/anlaşılmaz, görsel gerekli |

**Tipik fail örneği:** "log a = 2 olduğuna göre, (ln a + ln b) / (ln a - ln b)..." → log b verilmemiş, hesaplanamaz → fail (eksik bilgi).

**Tipik fail örneği 2:** "Üçgenin kenarları 10, 8, açı 60° → alan = 1/2·10·8·sin60° = 20√3 ≈ 34.6". Cevap "A=20" → fail (doğrusu 36'a yakın, ya 30 ya 36).

**Tipik pass örneği:** "P(x)=ax²+bx+c için P(0) = ?" Cevap "D=c" → pass.

---

### C3 — Legacy v3 Unaudited Quality Audit (30 satır)

**Hedef soru:** "Bu satır komple beta-safe mi (soru anlamlı + şıklar tutarlı + cevap doğru)?"

| verdict | Anlam |
|---|---|
| `pass` | Soru anlamlı, şıklar normal, cevap doğru — beta'ya alınabilir |
| `fail` | Herhangi bir problem var (soru saçma, OCR bozuk, şık tekrarı, yanlış cevap, yanlış konu) |
| `unclear` | Kararsızım |

C3 için beklenti: yüksek hata oranı (Convention v2'nin smoking gun analizi: hardcoded approved %87 hatalı çıktı).

---

## error_type Taksonomisi

verdict=fail veya unclear ise mutlaka error_type doldur:

| error_type | Anlam | Örnek |
|---|---|---|
| `missing_diagram` | Görsel gerekli ama image yok | C1 dominant tür |
| `ocr` | Soru metninde OCR bozulması, eksik harf, anlamsız | "matematik" → "matemat,k" |
| `wrong_answer` | Cevap matematik/mantık olarak yanlış | C2 sample 7 (üçgen alan) |
| `incomplete` | Soru eksik bilgi içeriyor (hesaplanamaz) | log a=2 verilmiş ama log b sorulmuş |
| `wrong_topic` | subject_area soru içeriğiyle uyuşmuyor | TARIH etiketli ama içerik kimya |
| `duplicate_option` | Şıklarda tekrarlı cevap | A=10, C=10 |
| `garbage_text` | Soru tamamen anlamsız/saçma | C3 sample 7, 11 (perişanın davranışları) |
| `other` | Başka bir problem (notes ile açıkla) | — |

**verdict=pass ise error_type boş kalsın.**

---

## Workflow Tip'leri

1. **Sırayla gitme zorunluluğu yok** — ilk önce kolay olanlar (text-only matematik, kısa Türkçe), sonra zor olanlar (geometri, görsel)
2. **Kuşkulandığında `unclear`'ı seç** — false pass'tan iyidir
3. **notes** kolonu serbest, kısa Türkçe yazabilirsin: "B doğru görünüyor, A=10 saçma" gibi
4. **Tek bir sample bile fail görüyorsan, error_type'ı dikkatli seç** — istatistik bu dağılıma dayanacak
5. **Source_book + page** kayıtlı, kitaba bakmak istersen `d-dataset/output/crops/<book>/p<page>_*.png` altındaki crop'lara bakabilirsin (opsiyonel)

---

## Skorlama Sonrası

Bittiğinde bana şunu söyle: "C1, C2, C3 scoring tamam." Ben:
1. Üç dosyayı okurum
2. İstatistik üretirim (verdict dağılımı, error_type dağılımı, strata bazında)
3. RESULT.md artifact'larını yazarım (`20260514_C1_RESULT.md`, `_C2_RESULT.md`, `_C3_RESULT.md`)
4. Combined synthesis: 130-örnek (önceki 100+30) + bu 110-örnek = 240-örnek toplam
5. Plan v1'in faz hedeflerini bu sonuçlarla ayarlarım (KPI revize)

---

## Hızlı Referans (TL;DR)

```
verdict ∈ {pass, fail, unclear}
error_type ∈ {missing_diagram, ocr, wrong_answer, incomplete,
              wrong_topic, duplicate_option, garbage_text, other}
              veya boş (verdict=pass için)
notes: serbest Türkçe, kısa
```

Saatte ~40-50 satır → 110 satır ~2.5 saat.
