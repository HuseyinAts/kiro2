## Session Handoff — 2026-06-03 (garble efsanesi + 55,768 rejected silindi)
**Branch:** master
**Son commit:** 28d56483a docs(rules): garble efsanesi dersleri
**Uncommitted:** temiz (DB değişikliği git'te değil)

### Yapilanlar
- **ÖLÇÜM (ezbersiz):** "61K garble" = VARSAYIM kanıtlandı — `unverified`=incelenmemiş, `student_coherent='false'`=0 satır (drop nedenleri persist edilmemiş)
- `backend/scripts/quality/garble_char_lm.py` — char-trigram garble dedektörü; doğrulama GEÇTİ (sentetik bozma 2.68→4.27) ama popülasyonda karakter-garble ~0 (≥4.5 yalnız 39, çoğu yabancı-dil)
- **DB SİLME (backup'lı, reversible):** 55,768 `rejected`+`is_active=true` → is_active=false (servis sızıntısıydı: `soru_bankasi_service.py:366/414/504/789` is_active-only) + 11 yabancı-dil gold. Aktif havuz 166,675→**110,896**
- Backup tabloları: `question_bank_cleanup_{rejected,foreign}_backup_20260603`
- **DERS KALICILAŞTIRMA (commit 28d56483a):** `.claude/rules/audit-methodology.md` (Varsayım≠Ölçüm, Metrik Doğrulama Gate, Ucuz Filtre Tuzağı) + `.claude/rules/testing.md` Lesson #31 (status≠servis dışı) + MEMORY `project_garble-myth-debunked.md`

### Fail Eden Testler
- YOK (test çalıştırılmadı — sadece DB veri + doküman değişikliği)

### Engelleyiciler
- Gemini key yok (re-OCR / semantik garble fix bloke). Karakter-garble zaten yok → text-repair/cross-OCR çürük

### Sonraki Adimlar (maks 5)
1. **KOD sızıntısı (silme değil):** `soru_bankasi_service.py` is_active-only select'lere (366/414/504/789) `_accepted_status` filtresi ekle → unverified+pending ~98K servis sızıntısını kapat
2. Commit 28d56483a push edilmedi — `git push` (master)
3. Audit doc yaz (opsiyonel): `docs/audits/2026-06-03_garble_myth_cleanup.md`
4. Kalan blind_answer_dispute 559 + 202 concept curator worklist (önceki backlog)
5. P3: kör-solve ölçekle (beta verified_provisional büyüt)

### Kararlar (gelecek session tekrar tartismasin)
- **"re-OCR tek çözüm" / "61K garble" ezberi ÇÜRÜK** — char-garble yok, LLM'in "garbled"ı=semantik tutarsızlık (text-repair düzeltemez). Bkz audit-methodology.md
- **unverified DOKUNULMADI** — yargılanmadı, silmek=varsayım (Hüseyin kuralı)
- DB değişiklikleri git'te değil; rollback için backup tabloları kullan
