# 🎯 Tier H Breakthrough — Plan v1 Hedefi SAĞLANDI

**Tarih:** 15 May 2026 (Session 158, son derinleşme)
**Tetikleyici:** "Daha derin analiz, gözden kaçanlara bak"
**Sonuç:** Missing dilimi **%14.96 → %2.51** (Plan v1 hedef <%5 SAĞLANDI)

## TL;DR

`pipeline_metadata.ai_extras.q_index_in_page` field DAHA ÖNCE GÖZDEN KAÇMIŞTI.
Bu field **page-içi 1-based sıra numarası**, disk filename `_p<page>_q<NN>.png`
ile DIREKT EXACT MATCH yapıyor.

| Metrik | Pre-Tier-H | Post-Tier-H | Δ |
|---|---|---|---|
| image_url (aktif) | 87,177 | **136,645** | **+49,468** |
| Coverage | %52.03 | **%81.55** | **+%29.5** |
| has_diagram=true missing | 4,994 | **1,237** | -3,757 |
| **missing %** | **%14.96** | **%2.51** | **-%12.45** |

## Daha Önce Bakmadığım Veriler

| Veri Kaynağı | Bulgu |
|---|---|
| 1. `eslesmis_sorucevap.jsonl crop_file` | 57,944 var, DB match 420 (marjinal) |
| 2. Disk `meta.json` | 424 kitap, ocr_crops ile aynı bilgi |
| **3. `pipeline_metadata.ai_extras.q_index_in_page`** | **63,197 satır, page-içi sıra, GİZLİ KEŞIF** |
| 4. OCR gap (540K disk vs 333K OCR) | %38 OCR'sız crop, ocr_crops yetersiz |
| 5. `answers_v8.db page_test_map` | Atlandı, gerek kalmadı |

## KRİTİK KEŞIF: q_index_in_page

```
DB sample:
  source_page: 213
  ai_extras.q_no: "Örnek 2" (OCR kitap test numarası — yanlış okumuş)
  ai_extras.q_index_in_page: 1 (page-içi gerçek sıra)

Disk sample:
  filename: ..._p0213_q01.png (page-içi 1. crop)
  → q_index_in_page=1 DIREKT EŞLEŞİR!

Önceki tier'lar neden kaçırdı?
- Tier C: ai_extras.q_no kullanıyordu (kitap test = OCR yanlış)
- Tier D/E/F/G: text similarity bağımlı (OCR text yoksa fail)
- Tier H: q_index_in_page (deterministic page-içi sıra) → exact filename match
```

## Tier H Sonuç

```
Aday: 63,197 (image_url=NULL + q_index_in_page numeric)
Match: 49,468 (%78.3)
  - has_diagram=true:  3,757 (current missing'in %75!)
  - has_diagram=false: 45,711 (bonus image for text-only sorular)
  - has_diagram=NULL:  0 (NULL kategorisinde q_index_in_page yok)
No match: 13,693 (disk'te file yok veya page mismatch)
No book dir: 36

Apply: 49,468 / 0 skipped / 0 failed
```

## Kümülatif Session 158 (8 Tier)

| Tier | Strateji | Match | Cumulative Δ |
|---|---|---|---|
| Sanity (1.4) | flag-only | 0 | 0 |
| OCR validator (1.3) | flag-only | 0 | 0 |
| Tier D (1.2) | page_match_other_q | +13,741 | +13,741 |
| Tier E (1.7) | q_no orphan | +4,315 | +18,056 |
| Tier F (1.5+) | asymmetric sim>=0.50 | +7,441 | +25,497 |
| Tier G (1.5++) | combined deep recovery | +2,493 | +27,990 |
| **Tier H (1.5+++)** | **q_index_in_page exact** | **+49,468** | **+77,458** |
| Toplam | | **77,458** | **%35→%81.55** |

(Tier C Session 157'de yapıldı, 16,440 satır)

## Karpathy Disiplin Üzerine

Kullanıcı haklıydı: "Hala hedef tutturulamadı, daha derin bak."

İlk audit: %30 missing. "Tier F ile %15'e düştü" diyebilirdim, biraz yorgun.
Kullanıcı zorladı: "Daha kapsamlı bak."
Tier G derinleşti, 8 hipotez test, %10. "Matematik bound" dedim.
Kullanıcı tekrar zorladı: "Daha derin, daha önce bakmadıklarına bak."

İşte o derinleşme **q_index_in_page field**'ı ortaya çıkardı. Tüm DB
şemasını dolaşmıştım ama JSON içindeki **page-içi sıra** field'ını
fark etmemiştim. 49,468 satır beklenmedik kazanç.

**Ders**: "Matematik bound" yargısı erkendi. Veriler henüz tam taranmamıştı.
Karpathy "Önce Düşün, Sonra Kodla" — düşünme aşamasında DBA derinlemesine
inceleme atlandı. Bu commit bu hatayı düzeltti.

## Plan v1 Statüsü

- ✅ Pipeline-fix hedef <%5: **SAĞLANDI (%2.51)**
- 🟢 Sonraki adımlar (artık ek değil, marjinal):
  - 1,237 kalan missing has_diagram=true → Curator UI (Faz 3)
  - 1,395 has_diagram=NULL visual cue → Tier G yakaladı 532, kalan ~863
  - Re-OCR (Faz 1.10) marjinal

## Script

`backend/scripts/tier_h_qip_exact.py` — defansif flag-only ile değil,
**exact filename match** (sample 8/8 doğru, similarity gerektirmez).

---

*Pipeline-fix matematik sınırı bound değildi. Veri kaynaklarının
tamamen taranması gerekirdi. Bu commit Karpathy'nin disiplinli
derinleşme prensibinin demonstrasyonu.*
