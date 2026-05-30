# Beta Clean Core — 386 Çift-Doğrulanmış Soru

**Tarih:** 30 Mayıs 2026
**Ne:** Kök-neden reçetesinin somut çıktısı — render-edilen `question_text` üzerinde **kör-bağımsız 3-solver consensus** gate'inden geçen, beta'ya hazır okunabilir + cevap-onaylı soru çekirdeği.

## Sonuç

| Metrik | Değer |
|--------|-------|
| İşlenen aday | 1,650 (33 batch × 50) |
| Okunabilir + consensus (≥2/3 X-dışı) | 518 |
| **beta_clean_verified (consensus == DB)** | **386** ⭐ çift-doğrulanmış |
| answer_disputed (consensus ≠ DB) | 114 (20'si DB=A → A-bias) |

**Subject dağılımı (386):** MATEMATIK 156, GEOMETRI 78, FIZIK 51, KIMYA 26, TURKCE 21, GENEL 16, BIYOLOJI 13, EDEBIYAT 11, TARIH 10, SOSYAL 3, COGRAFYA 1.

## Gate (kök-neden reçetesi)

- **Aday filtresi:** auto_judged_high + is_active + 5 şık dolu + len 60-600 + figür-referansı YOK (görsel kapalı olduğu için figür-bağımlı okunamaz).
- **Kör çözüm:** 3 bağımsız subagent `question_text`'i (DB cevabını GÖRMEDEN) çözer. Bu hem okunabilirliği (solver çözebildi mi) hem cevabı (consensus) **dairesellik olmadan** test eder — eski pipeline'ın DB-cevabını-aksiyom-sayma hatasının tersi.
- **beta_clean = consensus var (≥2/3 aynı X-dışı harf) VE consensus == DB.** Çift sinyal: bağımsız solver çoğunluğu + kitap anahtarı aynı cevapta birleşiyor.

## Önemli bulgular

- **Havuz ~%80 okunamaz** (pilot/val: temiz verim %14-30). 167K "soru"nun gerçek okunabilir+doğru kısmı ~%15-20. "10,705 beta-safe" proxy'ydi.
- **consensus-vs-DB sadece %77 uyum** → "okunabilir" ≠ "cevap-doğru". 114 ihtilaf, 20'si DB=A→consensus≠A (A-bias DB hataları canlı yakalandı).
- 386 çift-doğrulanmış, 10-20 öğrencilik 1 haftalık **kapalı beta için yeterli** (ilk-ilkeler: ~2-3K ideal ama kontrollü beta için 300-500 yeter).

## DB durumu (uygulandı)

- `pipeline_metadata.beta_clean_verified = true` → **386 soru** (metadata-only; cevap/status DEĞİŞMEDİ).
- `pipeline_metadata.beta_answer_disputed = true` (+ consensus_answer, db_answer) → 114 (Curator review).
- **Backup:** `question_bank_beta_core_backup_20260530` (500 satır, rollback hazır).
- **Sorgu:** `SELECT * FROM question_bank WHERE pipeline_metadata::jsonb->>'beta_clean_verified'='true'`

## Sonraki adımlar

1. **Beta'yı bu 386 ile aç** (10-20 gerçek öğrenci, 1 hafta) — TEK ACT. Gerçek-yanıt → IRT kalibrasyon + cevap-anahtarı gerçek-doğrulama kilidi açılır.
2. **114 disputed'ı Curator'da çöz** — 20 A-bias DB hatası düzelt, gerisi consensus hatası mı ayır.
3. **Çekirdeği büyüt** (gerek varsa): aynı gate'i kalan 67 batch + havuza uygula (fixed workflow, scriptPath hazır). VEYA garbage'ı Vision re-gen (Faz 3) ile kurtar.

## Scriptler / artifactlar

- Gate workflow: `.../workflows/scripts/beta-clean-core-500-wf_fca581e6-b49.js` (no-schema, loop-until-count)
- Apply: `backend/scripts/quality/_beta_core_tmp/apply_beta_core.py`
- Temiz liste: `clean_final.json` (500), `clean_run1.json` (87, ilk run)

---

*İlişkili: `2026-05-30_kalite_kok_neden{,_DERIN,_EN_DERIN}.md`. Bu, "cilayı bırak, gerçeğe dokun" reçetesinin ilk somut adımı.*
