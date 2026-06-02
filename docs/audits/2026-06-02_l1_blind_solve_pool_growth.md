# L1 — Kör-Solve Beta Havuz Büyütme (Gemini'siz)

**Tarih:** 2 Haziran 2026
**Yöntem:** Claude-Workflow kör-solve (dairesellik panzehiri), non-destructive metadata flag
**Karar:** İçerik kalite çarkı, Gemini'siz (key rotate bekliyor) → verified_core motorunu yeniden kullan

---

## Özet

Beta havuzu (`verified_provisional`) **2,689 → 3,109 (+420, +%15.6)**. Tek kör-solve
sinyaliyle DB cevabına anlaşan, okunabilir, figür-bağımsız sorular beta'ya terfi etti.
`correct_answer` HİÇ değiştirilmedi (0 satır). Backup: `question_bank_l1_backup_20260602`.

## Aday seti

`student_coherent=true` AND NOT `verified_provisional` AND damgasız
(`blind_unsolvable`/`answer_dispute`/`true_subject`/`needs_figure` YOK) = **997 soru**.
Hepsi image_url'li. Konu dağılımı: TÜRKÇE 427, MAT 218, GEO 108, KİMYA 74, FİZİK 56,
TARİH 41, EDEB 36, BİYO 30, diğer 7.

## Pilot (150 stratified) — GATE GEÇTİ

| Metrik | Değer |
|--------|-------|
| UNSOLVABLE (figür/garble) | 36 (%24) |
| Çözülen | 114 |
| **Anlaşma (blind==DB)** | **68/114 = %59.6** (gate ≥%50) |
| High-conf anlaşma (≥0.7) | 35/47 = %74.5 |

### Spot-check (15 soru, elle çözüldü)
- **AGREE (3):** hepsi gerçekten doğru+temiz → beta güvenli ✓
- **UNSOLVABLE (3):** hepsi gerçekten çözülemez (eksik kütle / garble şık / belirsiz terim) → dışlama doğru ✓
- **DISAGREE (9):** karışım — **2 gerçek DB cevap-hatası kör yakalandı** (4c452c22 a=12 değil 16; 57019fc1 π/8 değil −π/8), 4 solver hatası, 1 çürük soru
- **Ders:** Tek-blind anlaşmazlık ASLA auto-düzeltme değil → 2. sinyal kuyruğu. A-bias canlı (DB=A fazla).

## Tam-run (997)

| Kategori | Sayı | Oran | Aksiyon |
|----------|------|------|---------|
| AGREE | 420 | %42.1 | `verified_provisional=true` → beta |
| UNSOLVABLE | 193 | %19.4 | `l1_blind_unsolvable=true` → beta-dışı |
| DISAGREE | 334 | %33.5 | `l1_blind_dispute` + `l1_blind_answer` → 2. sinyal kuyruğu |
| EKSİK | 50 | %5.0 | dokunulmadı (tekrar solve fail — zor/belirsiz, ertelendi) |

**Metadata marker:** `l1_run=2026_06_02_l1`. `correct_answer` dokunulmadı (doğrulandı: backup vs canlı fark=0).

## Workflow operasyon dersi (529 rate-limit)

- **16+ eşzamanlı agent → 529 rate-limit → 0 token, boş sonuç.** Pilot (15) geçti, tam-run (85 burst) patladı.
- **Çözüm:** sıralı dalgalar, ≤6 eşzamanlı (`for` döngüsü + `await parallel(chunk)`). MEMORY S181 dersinin tekrarı.
- **Schema/StructuredOutput bu harness'ta güvenilmez** (15/15 "completed without calling StructuredOutput", 0 token). Çözüm: schema YOK, agent düz JSON text döndürür, workflow JS'inde `JSON.parse` (fence-strip + `{...}` extract).
- 50 inatçı soru token harcayıp parse=0 verdi (muhtemelen prose+JSON karışık çıktı) → ertelendi.

## Kapsam ve dürüst sınır

- Gemini'siz büyüme havuzu **~997 ile sınırlı** (okunabilir+figür-bağımsız tükenmiş).
- Asıl kilit **61K unverified/garble + 884 unsolvable + figür** → re-OCR / figür-crop = **Gemini-bloke**.
- L1 tavan ~3,400'dü, ulaşılan 3,109 (50 ertelenen + 193 unsolvable çıkınca beklenen aralıkta).

## L1d — DISAGREE 334 → 2. bağımsız kör-solve (628-dispute deseni)

334 dispute → 2. bağımsız kör-solve (34 batch, sıralı 6 dalga, 3.36M token). 294 kapsandı, 40 eksik.

| Sınıf | Sayı | Mantık | Aksiyon |
|-------|------|--------|---------|
| FALSE_DISPUTE | 55 | 2.blind==DB≠L1 (L1 yanıldı) | `verified_provisional=true` → **beta terfi** |
| REAL_ERROR | **143** | 2.blind==L1≠DB (2 sinyal DB'ye karşı) | `l1d_real_error`+suggested → curator/3-sinyal |
| UNSOLVABLE | 57 | 2.blind figür/garble | `l1d_unsolvable` |
| SPLIT | 39 | 2.blind ≠ L1 ≠ DB | `l1d_split` → curator |
| EKSİK | 40 | rate-limit | ertelendi |

**Beta: 3,109 → 3,164 (+55).** 143 gerçek DB cevap-hatası 2-sinyalle teyit (A-bias canlı doğrulaması).
`correct_answer` DOKUNULMADI (backup vs canlı fark=0). Backup `question_bank_l1d_backup_20260602`,
marker `l1d_run=2026_06_02_l1d`.

**SESSION TOPLAM: beta 2,689 → 3,164 (+475, +%17.7) + 143 DB hatası bulundu.**

## L1d-3 — 143 REAL_ERROR → 3. sinyal düzeltme (MAT+GEO)

143 REAL_ERROR'ın MAT+GEO alt-kümesi = 30 (16 MAT + 14 GEO; 113 concept → curator).
3. bağımsız kör-solve → **25 CONFIRM** (3==agreed), 1 REJECT, 4 UNSOLVABLE.
**25 `correct_answer` DÜZELTİLDİ** (`correct_answer`=blind, marker `answer_corrected_3signal`,
`answer_corrected_from`). Backup `question_bank_l1d_correct_backup_20260602`.
Elle spot-check 4/4 (4c452c22 C→B a=12; 580ed94a A→E mesafe∈[256,648]; f39f3956 A→E 13·14·15=2730=15!/12!;
7fa7bb9f E→C der[P·Q]=2n çift). **Bu session'ın TEK correct_answer değişikliği** (3-sinyal + elle teyit).

## SESSION FİNAL TOPLAM
- **Beta havuzu: 2,689 → 3,164 (+475, +%17.7)**
- **25 DB cevap-hatası düzeltildi** (3-sinyal, MAT+GEO)
- **118 REAL_ERROR kaldı** (113 concept + 5 MAT/GEO reject/unsolvable) → curator
- Figür/garble flag: 250 (beta-dışı) | curator/split: 39
- Tüm değişiklikler backup'lı, 5 backup tablo

## L1-retry — ertelenen 90 (L1 50 + L1d 40)

wave=3 retry → 30 çözüldü (60 kalıcı erteleme, tekrar parse-fail = gerçekten zor/belirsiz).
L1: agree 5 (→beta), unsolv 4, disagree 7. L1d: real_error 5, unsolvable 5, split 4, false_dispute 0.
**Beta 3,164 → 3,169 (+5).** correct_answer DOKUNULMADI, backup `question_bank_retry_backup_20260602`.

## SESSION FİNAL (güncel)
- **Beta havuzu: 2,689 → 3,169 (+480, +%17.9)**
- **25 DB cevap-hatası düzeltildi** (3-sinyal MAT+GEO)
- **123 REAL_ERROR** (113 concept + 5 retry + 5 MAT/GEO reject) → curator
- 60 soru kalıcı erteleme (parse-fail dirençli)

## L1d-curator — 123 REAL_ERROR curator-ready paketleme (202-concept deseni)

123 uncorrected REAL_ERROR (TÜRKÇE 71, KİMYA 12, TARİH 11, EDEBİYAT 10, MAT 8, FİZİK 8, diğer 3):
- `quality_review_status` auto_judged_high → **pending** (curator kuyruğuna girdi, gold'dan çıktı — 628 deseni: 2-sinyal-yanlış gold'da kalmaz)
- `dispute_suggestion` metadata = "Kör-solver 2-sinyal: DB=X → öneri=Y" (curator UI yüzeye çıkarır)
- `correct_answer` DOKUNULMADI (0). Backup `question_bank_l1d_curator_backup_20260602` (123).
- Worklist CSV: `backend/scripts/quality/_l1_curator_tmp/concept_real_error_worklist.tsv` (Hüseyin accept/reject).

## SESSION FİNAL (güncel)
- **Beta havuzu: 2,689 → 3,169 (+480, +%17.9)**
- **25 DB cevap-hatası düzeltildi** (3-sinyal MAT+GEO)
- **123 REAL_ERROR → curator kuyruğu** (dispute_suggestion + pending + worklist)
- 60 soru kalıcı erteleme

## Sonraki

1. **Hüseyin: 123 curator worklist** accept/reject (curator UI'da dispute_suggestion görünür).
2. **60 kalıcı-ertelenen** → curator veya manuel.
3. Gemini key rotate → 61K garble re-OCR (en büyük kilit).

## Dosyalar
- Apply SQL: `backend/scripts/quality/_l1_full_tmp/l1_apply.sql`
- Kategori: `backend/scripts/quality/_l1_full_tmp/l1_categorized.json`
- Backup tablo: `question_bank_l1_backup_20260602` (947 satır, rollback hazır)
