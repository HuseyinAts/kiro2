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

## Sonraki

1. **DISAGREE 334 → 2. bağımsız kör-solve** (628-dispute deseni): gerçek DB hataları (A-bias) düzelt, false-dispute temizle.
2. **50 ertelenen** → wave=2 ile tekrar veya curator.
3. Gemini key rotate → 61K garble re-OCR (en büyük kilit).

## Dosyalar
- Apply SQL: `backend/scripts/quality/_l1_full_tmp/l1_apply.sql`
- Kategori: `backend/scripts/quality/_l1_full_tmp/l1_categorized.json`
- Backup tablo: `question_bank_l1_backup_20260602` (947 satır, rollback hazır)
