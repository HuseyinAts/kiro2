# Session Handoff — 2026-06-22/23 (Tam DB Profil + İçerik Temizlik + Pool A Büyüme + P1/P3)

**Branch:** feature/self-evolution-optimization | **HEAD:** 5d001d079 (pushed) | **PG18:** 5434 manuel-açık
**v_safe: 25.855** | **DB: 177 tablo (39 backup)** | **correct_answer/is_active HİÇ DOKUNULMADI**

---
## 1. BU SESSION'DA YAPILANLAR (kronolojik, hepsi commit+push'lu)

### Tam DB Derin Profil (eksiksiz)
- 178 tablo / **2.421 sütun** deterministik profiler ile tarandı (0 atlama garantisi). Mutabakat: 1.261 dolu-tablo + 221 view + 939 boş-tablo sütunu = 2.421. Tüm satırlar tarandı (en büyük 187K < limit 200K).
- Profiler: `docs/audits/_dbprofile/generate_profile.py` (+ inventory.tsv, columns_meta.tsv, column_profile.tsv).
- FK: **0 orphan** (107 declared FK). question_bank: 0 bad-key, 0 kısa-metin.
- Rapor: `docs/audits/2026-06-22_full_db_deep_profile.md`

### İçerik Kalitesi (kanıt, blind n=448)
- Served pool: **%89.5 okunabilir / %96.9 çözülebilir / %79.5 blind-AGREE / %11.8 garble** (verbal-yoğun: TÜRKÇE %26).
- Eski gold %40 okunabilirlikten dramatik iyileşme — blind-solve+2signal pipeline'ı işe yaradı.

### Uygulanan içerik fix'leri (reversible, backup'lı)
- **v_safe dedup:** −356 mükerrer (demoted_at flag)
- **Garble sweep 2-PASS (false-pozitif guard'lı):** verbal 372→41 demote (331 FP kurtarıldı), STEM 223→17 demote (206 FP kurtarıldı). **Toplam 743 geçerli soru kurtarıldı** — tek-pass körü silerdi.
- **A3 bank dedup:** 5.315 mükerrer → `duplicate_of` flag (kanonik korundu)
- **B1 Pool A AYT/sözel-sosyal büyüme:** 2.214 çözüldü → **570 promote** (v_safe +570; AYT 2041→2160, dengesizlik azaldı)

### DB temizlik (kanıtlı-güvenli)
- mock_ai_telemetry+mock_ocr_data (200K, kodda 0-ref) + 4 eski backup + platform_stats (tek DEAD) kaldırıldı.

### Meta-audit + şema sınıflama (agent-team)
- 82 boş tablo: 51 WIRED(lansman-bekliyor) / 30 stub / **1 DEAD** → "boş=sil" çürüdü (81 modelli).
- 15 çekirdek wired-boş write-path: 10 DORMANT(trafik bekliyor) / 5 NO_WRITE_PATH(quiz/achievement inşa edilmemiş).
- Önceki meta-audit (kod): 5 bulgu→3 gerçek fix (F4 beta_vp index, F5 Pydantic validate-shadow, F2 dead-dup sil) + 2 phantom.

### P3 Beta E2E (canlı backend)
- Golden Flow 14 PASS / 12 FAIL / 150 skip. **Çekirdek öğrenci akışı PASS** (login→placement→exam→review→qbank).
- 12 fail HEPSİ çevresel (7×500: teacher/KVKK/Khan/EBA/video — sync-get_db-trap). Rapor: `docs/audits/2026-06-22_p3_beta_e2e.md`

---
## 2. AÇIK İŞLER (gated/blocked/deferred — kanıtla)
- **P3 redeploy+rerun (P0, deploy-gate):** container 3-gün STALE. `docker compose build backend && up -d --no-deps backend` → E2E re-run → stale-vs-gerçek ayrışsın → kalan gerçek 500'leri TDD'yle fix (Pattern A trap reçetesi golden-flows.md/middleware.md).
- **GF1x logout-security:** logout sonrası /me 200≠401 — doğrula (stale mı gerçek mi).
- **B2 gold terfi (BLOKE):** 1.778 `poolA_2signal` aday, farklı-model 3.sinyal yok (qwen STEM-zayıf/gemini-bloke) → infra kararı.
- **A2 dispute (ERTELENDİ):** düşük-ROI (served temiz; dispute≠yanlış-anahtar). 25K 2.-solve değmez.
- **C2/C3 şema-drop (deploy-gate):** 30 stub + 165 ölü sütun + legacy questions(36K) → model+tablo+test birlikte, container-test'li. Otonom-drop GÜVENLİ DEĞİL.
- **Pool A kalan ~9.000 fallback** (çoğu STEM-TYT, fazla-temsil) → sonraki dalgalar (proven recipe).
- **Latent bug:** quiz_submissions sessiz-veri-kaybı (writer learning_path_repository.py:443 var ama submit endpoint'e unwired) — quiz-feature inşa edilirse şart.

---
## 3. KRİTİK DERSLER (bu session canlı kanıt)
1. **Türkçe içerikte tek-pass silme = %89 FP.** 2-pass + domain-guard ZORUNLU (743 geçerli soru kurtarıldı).
2. **"Boş/wired-boş = silinebilir/aktive-edilebilir borç" YANLIŞ.** Çoğu lansman-öncesi-doğru. Trace et, varsayma.
3. **2 dev workflow eşzamanlı = rate-limit** (3 kez yendi: 529+session+weekly). SIRALI + resume (cache'li, güvenilir).
4. **Eksiksizlik = deterministik araç (SQL/script), LLM ajanı değil.** Doğrulamanın kendisi de doğrulanmalı (scope; fallback_videos repo-katmanı kaçtı).
5. **Stale-baseline'a güvenme** (container 3-gün eski → E2E fail'leri belirsiz).

---
## 4. STATE/ALTYAPI
- PG18 5434 manuel: `pg_ctl -D "C:/Program Files/PostgreSQL/18/data" -l C:/Users/husey/pg18_manual_start.log start`
- Tüm container'lar healthy (backend/frontend/redis/celery/ollama, 3 gün up — ama backend kod-stale).
- Reçeteler: `_poolA_retag/POOLA_RESULT.md` (blind-solve dalga), `_dbprofile/` (profiler), `docs/audits/2026-06-22_*` (3 rapor).
- Backup'lar (39): question_bank_*backup* + poolA_w{1,2,3,b1} + garble_{verbal,stem,demote} + vsafe_dedup + stale_vp + dup_flag — hepsi reversible.

---
## 5. SONRAKİ ADIM (öneri sırası)
1. **Backend redeploy + P3 E2E re-run** (gerçek 500'leri ortaya çıkarır — en yüksek değer, deploy-gate)
2. Gerçek 500'leri TDD fix (Pattern A sync-get_db-trap)
3. B2 gold için farklı-model kararı (gemini-unblock?)
4. Pool A STEM-TYT dalgaları (otonom, isteğe bağlı)
