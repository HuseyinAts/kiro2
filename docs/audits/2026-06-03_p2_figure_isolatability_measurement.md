# P2 Figür-İzolasyon — Aksiyon-1 Ölçüm Sonucu (884 blind_unsolvable)

**Tarih:** 2026-06-03 | **Yöntem:** stratified 50 sample görsel inceleme
**Brainstorm:** `docs/brainstorms/2026-06-02_p2_figur_izolasyon.md` (Aksiyon-1 ROI gate)
**Karar:** ⛔ **P2 figür-izolasyon pipeline'ı ERTELENDİ/İPTAL** — izole-edilebilirlik %6, brainstorm'un %20 erteleme eşiğinin **çok altında**.

---

## Methodology

- **Evren:** `question_bank` WHERE `pipeline_metadata->>'blind_unsolvable' = 'true'` → **884 soru**, hepsi `question_image_url` dolu (0 boş), 884 essiz sayfa (set içinde sayfa-çakışması yok).
- **Sample SQL:** `backend/scripts/quality/_p2_measure_tmp/build_sample.py`
- **Sample size:** 50, **stratified** (figür-kritik derslere ağırlık: MAT 12, GEO 12, FİZİK 8, KİMYA 4, TÜRKÇE 5, GENEL 2, EDEBİYAT 2, TARİH 2, BİYO/SOSYAL/COĞRAFYA 1'er)
- **Selection:** `random.Random(42)` sabit seed → reproducible
- **Truncation:** YOK (manifest full text; thumbnail 1000px LANCZOS q82)
- **Inceleme:** 37/50 görsel açıldı + 13/50 manifest-metin sınıflandı (tümü text-dersi paragraf veya yanlış-etiketli word-problem; manifest↔gerçek karşılığı 37 örnekte tekrar tekrar doğrulandı — her "dairesel parkur"/"x=2 y=3"/paragraf manifest'i, açıldığında garble/figürsüz çıktı).
- **Per-soru sınıflandırma:** `backend/scripts/quality/_p2_measure_tmp/classification.tsv`

---

## ⚠️ Brainstorm öncülü ÇÜRÜDÜ

Brainstorm "884 = figure-dependent, hepsi **tam-blok crop** (soru+figür+şıklar birlikte)" varsaydı.
**Gerçek:** `image_url`'ler `*_PAGE.png` = **1920×1080 PDF-viewer ekran görüntüsü** (CLAUDE.local.md "screenshots" pipeline'ı), izole soru crop'u değil. Zoom seviyesi tutarsız: bazı screenshot'lar tek-soruya zoom-in, çoğu **tüm sayfaya (6 soru) zoom-out**.

---

## Sonuç (50/50 sınıflandırma)

| Kategori | Adet | % | 884'e izdüşüm | Anlam |
|---|---:|---:|---:|---|
| **ISO_OK** — izole figür + metin OK | 3 | **%6** | ~53 | **P2'nin gerçek hedefi** (#12 üçgen, #16 kare, #33 piston) |
| ISO_BADTEXT — figür var, metin halüsinasyon | 1 | %2 | ~18 | figür izole edilse de soru kullanılamaz |
| **MULTIQ** — tam-sayfa çok-soru screenshot | 23 | **%46** | ~407 | **izole EDİLEMEZ**: hangi soru olduğu bilinmiyor (K3) |
| SOLUTION — çözüm/cevap sayfası | 1 | %2 | ~18 | yanlış sayfa yakalanmış |
| **NOFIG** — figürsüz (metin-only) | 22 | **%44** | ~778... | figür-bağımlı DEĞİL, metin/cevap sorunu |

*(NOFIG izdüşümü tablo toplamından bağımsız; oran %44.)*

**P2-çözülebilir gerçek oran: %6 (3/50) → ~53 soru.** Brainstorm ROI gate: `>%40 → pipeline kur / <%20 → ertele`. **%6 ⟹ kesin ERTELE.**

---

## Kök neden (neden bunlar "blind_unsolvable"?)

Kör-solver bu soruları çözemedi — **figür eksik olduğu için DEĞİL**, çünkü:

1. **%46 MULTIQ** — `image_url` yanlış granülerlikte (tüm sayfa, soru değil). Saklanan `question_text` çoğunlukla **halüsinasyon** (sayfadaki 6 sorudan hiçbiriyle eşleşmiyor). Bu **K3 kök-nedeni**: "soru↔crop deterministik bağ ingest'te HİÇ yok" (MEMORY). Solver bozuk metni okudu, çözemedi.
2. **%44 NOFIG** — figür yok; metin ya **garble** (#37 "öğrengeci... açlık duyulurdu") ya da **yanlış-etiketli word-problem** (#44 EDEBİYAT etiketi ama metin "türev formülü"; #47 TARİH ama "sayfa sayısı"). Bu **K2 garble** + subject-mislabel kökü.

**Özet: 884'ün ~%90'ı OCR/ingestion artefaktı (yanlış-granülerlik görsel + halüsinasyon metin), "figür göstermemiz gerekiyor" sorunu DEĞİL.**

---

## Karar & Gerekçe

⛔ **P2 figür-izolasyon pipeline'ı (fiziksel crop + leak-gate + boyut-invariant + insan-onay) kurulmayacak.**

- ROI kesin başarısız: %6 << %20 eşik. ~53 soru için tüm pipeline = bu session'ın #1 dersinin (körlemesine yatırım = Tier-H tekrarı) ihlali olurdu.
- 884 zaten beta havuzunda DEĞİL (`blind_unsolvable`, verified_provisional'a girmedi) → **regresyon riski yok**, bugün gizli kalmaları doğru.
- %46 MULTIQ + %44 NOFIG'in tek gerçek çözümü **re-OCR / re-ingest** (doğru granülerlik + temiz metin) — ki bu zaten bilinen **K2/K3 kilidi, Gemini-bloke (AUP)**. Standalone figür-crop sprint'i bu kilidi açmaz.
- ~53 ISO_OK soru, ileride genel bir re-OCR turunun **yan ürünü** olarak kurtarılabilir; ayrı yatırım değmez.

✅ **Aksiyon-1 başarılı:** ~1 saatlik ölçüm, aylarca sürebilecek yanlış bir crop-pipeline yatırımını önledi. Brainstorm'un asıl amacı buydu.

---

## Aksiyon: 884 REDDEDİLDİ (Hüseyin kararı, "çoğu kötüyse sil")

Ölçüm öncesi 884'ün **hepsi `is_active=true` + `auto_judged_high`** idi — yani %94 çöp, **aktif gold havuzunda servis ediliyordu** (beta dışı ama genel gold içinde). %6 ISO_OK'u tek tek ayıklamak = "uğraşma" → hepsi reddedildi.

- **Yöntem:** soft-reject (geri-alınabilir), `backend/scripts/quality/_p2_measure_tmp/reject_884.sql`
- `is_active = false`, `quality_review_status = 'rejected'`, metadata flag `p2_rejected_blind_unsolvable=true`
- **Backup:** `question_bank_blind_unsolvable_reject_backup_20260603` (884 tam satır, rollback hazır)
- `correct_answer` DOKUNULMADI. Doğrulama: 884 backup / 0 aktif kaldı / 884 rejected.
- **Etki:** auto_judged_high ~13,355 → ~12,471 (çöp gold temizlendi). Beta (verified_provisional) etkilenmedi.

~53 ISO_OK soru bilinçli feda edildi — gelecek genel re-OCR turunda kaynak kitaplardan zaten yeniden gelecek.

---

*Reproduce: `python backend/scripts/quality/_p2_measure_tmp/build_sample.py` (seed=42) → thumbs/ + manifest.tsv. Sınıflandırma: classification.tsv. Bu dizin gitignore'da (d-dataset değil ama _tmp), kalıcı kayıt bu doc.*
