## Session Handoff — 2026-06-03 14:30
**Branch:** master
**Son commit:** 932d18372 chore(data): 884 blind_unsolvable reddedildi (%90 OCR artefaktı)
**Uncommitted:** temiz (10 commit master'da push BEKLİYOR)

### Yapilanlar — P2 Figür-İzolasyon Aksiyon-1 ölçümü + 884 reddi
- `docs/audits/2026-06-03_p2_figure_isolatability_measurement.md` (commit 4c3e65264): 884 blind_unsolvable stratified 50 sample görsel ölçüm (seed 42). **İzole-edilebilir figür+temiz metin sadece %6** → brainstorm %20 eşik altı → P2 crop-pipeline ERTELE/İPTAL.
- Bulgu: `image_url`'ler `*_PAGE.png` = **1920×1080 tam-sayfa viewer screenshot** (izole crop DEĞİL). Dağılım: MULTIQ tam-sayfa-çok-soru %46 (K3 soru↔crop bağ yok) + NOFIG figürsüz %44 (K2 garble/halüsinasyon) + ISO_OK %6. **~%90 OCR artefaktı, figür-bağımlı değil.**
- **884 REDDEDİLDİ** (commit 932d18372, Hüseyin "çoğu kötüyse sil"): ölçüm öncesi hepsi `is_active=true`+`auto_judged_high` (aktif gold'da servis!). Soft-reject: `is_active=false`+`rejected`+metadata `p2_rejected_blind_unsolvable`. SQL `backend/scripts/quality/_p2_measure_tmp/reject_884.sql`. Backup `question_bank_blind_unsolvable_reject_backup_20260603` (884 satır). correct_answer DOKUNULMADI.
- Etki: auto_judged_high ~13,355→~12,471. Beta (verified_provisional) ETKİLENMEDİ.
- `docs/brainstorms/2026-06-02_p2_figur_izolasyon.md` başına SONUÇ banner'ı eklendi.

### Fail Eden Testler
- YOK (DB-only iş + doc, kod değişmedi). Ölçüm 37/50 görsel + 13/50 manifest sınıflandırma.

### Engelleyiciler
- 61K garble + 884'ün %90'ı → tek çözüm re-OCR, **Gemini-bloke (AUP key rotate bekliyor)**.

### Sonraki Adimlar (maks 5)
1. `git push` — 10 commit master'da bekliyor (origin/master..master).
2. **Gemini key rotate → 61K garble re-OCR** — en büyük kilit (K2). 884 ISO_OK ~53 de bu turda kaynaktan gelir.
3. 123 curator worklist (önceki session, `backend/scripts/quality/_l1_curator_tmp/curator_worklist_123_FULL.csv`) — Hüseyin accept/reject doldur.
4. Beta gerçek-öğrenci sürüyor — yeni flag → A1 + L1 pattern tekrarla.
5. `_p2_measure_tmp/` gitignore'da (geçici); audit doc kalıcı kayıt.

### Kararlar (gelecek session tekrar tartismasin)
- P2 figür-izolasyon İPTAL: ROI %6 << %20 eşik. Brainstorm öncülü (tam-blok crop) çürüdü; gerçek = tam-sayfa screenshot + halüsinasyon metin. Standalone crop-sprint K2/K3 kilidini açmaz.
- Çöp gold reddi: blind_unsolvable gibi sistematik-bozuk set, tek tek %6 iyiyi ayıklamak yerine toplu reddedilir (backup'lı, geri-alınabilir). İyi olanlar re-OCR'da kaynaktan döner.
- Tüm DB değişikliği non-destructive: backup tablo + soft flag, correct_answer asla dokunulmaz.
