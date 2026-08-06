## Session Handoff — 2026-08-07 02:00
**Branch:** feature/self-evolution-optimization
**Son commit:** `2c845b736` docs: Gemini devir plani — durum, tuzaklar, 17 kalemlik oncelikli is listesi
**Uncommitted:** 249 dosya (218 changed, +7061/-5918) — **TRIYAJ EDILMEDI, P0 risk**

### Yapilanlar
- `backend/scripts/clean_import_question_bank.py` — TRUNCATE script'i mühürlendi, env-override + exit 2 (`1091db7ab`)
- `backend/tests/db/test_question_bank_invariants.py` — hacim+benzersizlik invaryantı, RED→GREEN kanıtlı (`1091db7ab`)
- `question_bank` **2.304/21 → 187.835/182.519 benzersiz** restore; kapı `mv_safe_for_beta` 2.200 → **25.127** (DB, commit yok)
- `backend/tasks/push_tasks.py` — 3 seri bağlı kusur: DSN çözümü + parola maskeleme (`6f3380072`), `organization_id` (`eb40cb30d`)
- `backend/alembic/versions/fa067642bdfe_force_drop_questions.py` — takipsizdi, sürüm kontrolüne alındı (`d5bf6c339`)
- `.gitignore` — 22 scratch script, glob değil açık liste (`b84bdc503`)
- `backend/api/teacher_copilot_api.py` + `frontend/src/components/Teacher/TeacherCoPilotDashboard.tsx` — mock olarak etiketlendi, bayrak true iken 501 (`d9f6953f6`)
- `docs/audits/2026-08-07_disabled_routers_envanteri.md` — 110/110 router frontend'ce çağrılıyor, hiçbiri ölü değil (`0fb271e97`)
- `backend/routers/loader.py` — 6 yasal/ticari kritik router açıldı, 104 kapalı (`0d17f924f`)
- `frontend/src/App.tsx` — `/login` regresyonu geri alındı + `/teacher/copilot` mount (`af99079c2`)
- `docs/HANDOFF_2026-08-07_gemini.md` — Gemini devir planı (`2c845b736`)

### Fail Eden Testler
- **Backend (dokunulanlar): 18 passed, 2 skipped** — skip'ler `test_question_bank_invariants.py`;
  `KVKK_VERIFY_DSN` yoksa sessizce atlanıyor. ⚠️ Yani bekçi CI'da **fiilen kapalı**.
- 🔴 **Frontend: 28 dosya / 111 test KIRIK** — kök neden bilinmiyor. `git stash` ile
  `App.tsx` çıkarılıp tekrar koşuldu, aynı kırık → bu oturumun regresyonu DEĞİL, önceden var.
  Örnek: `frontend/src/test/components/LearningPath/VideoResourceGrid.test.tsx:164`
- 🔴 **Backend uçtan uca ÖLÇÜLEMİYOR** — `pytest_asyncio` teardown deadlock (önceden var)

### Engelleyiciler
- **249 commit'siz dosya** — bu ağaçta 3 regresyon bulundu (S204: 2, ben: `/login`). Daha olabilir.
- **Celery fix imajda YOK** — `docker cp` ile kondu. Konteyner yeniden oluşturulursa
  görev yine ölür + `kiro2_app` parolası tekrar log'a düşer (14 kayıt temizlenmişti).
- **SMTP 6/6 değişken tanımsız** (`.env.mvp`) → şifremi-unuttum akışı ölü (kod hazır, 54/54 test).

### Sonraki Adimlar (maks 5)
1. **İş #1** — 249 dosyayı küme küme diff okuyarak triyaj + commit (`docs/HANDOFF_2026-08-07_gemini.md` §3)
2. **İş #2** — İş #1 sonrası `docker compose build celery-worker celery-beat` (fix'i imaja al)
3. **İş #3** — SMTP kimlik bilgisi + gerçek e-postayla uçtan uca doğrulama
4. **İş #6** — 111 kırık frontend testinin kök nedeni (test paketi şu an karar aracı değil)
5. **İş #7** — Kalan 104 router: açılış maliyetini ölç, sonra kademeli aç

### Kararlar (gelecek session tekrar tartismasin)
- `questions` legacy tablosu **geri yüklenmeyecek** — çift-tablo tuzağını (testing.md #23) diriltmemek için. Yedek: `backups/kiro2_pre_schema_restore_20260727.dump`
- Teacher Co-Pilot **mock kalacak, etiketli** — gerçek veri yok (`user_item_fsrs`=1, `student_learning_profiles`=2, `student_question_flags`=0). Bağlansa pano boş görünürdü.
- Kalan 104 router **kapalı bırakıldı** — kapatma gerekçesi (açılış performansı) hiç ölçülmedi; ölçmeden açmak da kapatmak kadar dayanaksız olurdu.
- HNSW **tek** index kuruldu — `ix_question_embedding_hnsw` birebir kopyaydı, geri getirilmedi (22→21 index).
- İkinci HNSW ve `loader.py`'nin 104 kalemi dışında **çalışma ağacına dokunulmadı** — kapsamı diff'le ölçmeden commit etmemek için.
- Proje **Gemini'ye devrediliyor**: `docs/HANDOFF_2026-08-07_gemini.md` kendi kendine yeterli.
