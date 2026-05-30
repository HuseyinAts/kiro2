# Session — Beta Pratik Testi (Plan A) (30 May 2026)

> Önceki oturum: kalite kök-neden + 386 beta clean core üretildi. Bu oturum
> kök-neden reçetesinin **TEK ACT**'ini uyguluyor: 386'yı gerçek öğrenciye aç.

---

## 🎯 BU OTURUM: Beta Pratik Testi (backend GREEN, frontend kod-tamam)

386 beta_clean soru standart ÖSYM formatına (TYT 120 / AYT 160) sığmıyor
(TUR 21, COG 1). Karar: **kısa karışık pratik** — 20 soru, ÖSYM dağılımı yok,
386'dan rastgele, süre serbest (120 dk taşıyıcı).

### ✅ TAMAMLANAN + DOĞRULANAN
- **Premise doğrulandı (iyi haber):** cevap-leak riski zaten kapalı.
  `ModernOSYMExamInterface.tsx:551 false &&` görsel suppress = kasıtlı Bug #11
  defansı. `content` kolonu YOK → frontend daima gate-onaylı `question_text`
  gösteriyor. API'de `correct_answer` da YOK (E2E doğrulandı).
- **Backend (TDD RED→GREEN, gerçek DB):**
  - `core/osym_exam_engine.py`: `OSYMExamConfig.beta_practice` alanı +
    `_select_beta_questions(count)` (beta_clean havuzundan rastgele, proxy
    base_filters UYGULANMAZ — gate daha güçlü) + `_select_questions` erken-dal +
    `create_exam_session` beta flag.
  - `api/sinav.py`: `POST /api/v1/osym-exam/beta-practice?num_questions=20`.
  - **E2E canlı stack (kiro2-backend):** create=200 (20 soru) → start=200 →
    current-question = okunabilir MATEMATIK sorusu + şıklar, `correct_answer`
    sızıntısı YOK. `_select_beta_questions(20)` → 9 ders karışık, all_clean=True.
  - Test: `backend/tests/integration/test_beta_practice_selection.py` (gerçek DB,
    DB yoksa skip). Doğrulama script: `backend/scripts/_verify_beta_selection.py`.
- **Frontend (tip-temiz + BROWSER DOĞRULANDI):**
  - `services/examService.ts`: `createBetaPractice(numQuestions=20)`.
  - `pages/ModernExamStartPage.tsx`: üstte "🚀 Beta Pratik Testi" banner +
    `handleStartBeta` → `/exam/{id}` (mevcut sınav arayüzü + sonuç akışını kullanır).
  - `npx tsc --noEmit` değişen dosyalarda 0 hata.
  - **Playwright E2E (kiro2-frontend yeni build):** login → /exam/start → banner
    görünür → "Beta Pratiğe Başla" → ön-sınav "20 Soru/120 dk" → checklist+sistem
    kontrol → Sınavı Başlat → **Soru 1/20 render: gerçek metin + 5 şık, görsel yok,
    cevap sızıntısı yok, 0 console error.** Kök-neden reçetesi: gerçek UI'da soru.
  - **Build gotcha:** İlk `docker compose build frontend` BuildKit cache (#14 CACHED)
    eski dist kopyaladı → değişiklik gelmedi. `--no-cache` ile çözüldü. Bundle
    `/usr/share/nginx/html/js/` altında (assets/ DEĞİL).

### ✅ RE-CURATE (kullanıcı browser'da dairesel soru yakaladı → ikinci gate)
- Hüseyin gerçek UI'da "ABC üçgenünde A açısı 60° ise A açısı kaç?" (dairesel) yakaladı.
  Kör 3-solver gate'in kör noktası: dairesel/garbled soru metin kendini cevaplıyorsa geçer.
- **6 paralel Claude subagent tutarlılık yargıcı** 386'yı yeniden yargıladı (metin+şık,
  görsel yok): **221 keep / 165 drop (~%42!)**. Defects: garbled 75, circular 34,
  answer_wrong 30, open_ended 13, figure_dependent 8.
- Spot-check: kullanıcının sorusu+2 kopya → drop/circular ✅; meşru benzerler ("A=60,B=45→C")
  → keep ✅. Yargıç ayrımı güçlü.
- **DB applied:** backup `question_bank_beta_recurate_backup_20260530` (386). 165 drop →
  `beta_clean_verified=false` + audit `beta_recurate_2026_05_30`. Metadata-only.
  Doğrulama: **beta_clean_verified=true → 221** | backup 386 | audit-marked 165.
- Backend restart → in-memory pool cache temizlendi → beta canlıda 221'den çekiyor (20 soru,
  all_clean, doğrulandı). Detay: `docs/audits/2026-05-30_beta_recurate_coherence_gate.md`.

### ✅ GOLD POOL TAM-RUN (P1) — tutarlılık gate'i tüm havuza
- Stratified pilot (572) → %63 drop → tam-run gerekçeli.
- **Workflow** `wf_9a48d483-e16`: 13,595 yargılandı. **İlk 136-eşzamanlı run 529
  rate-limit yedi (0 iş)** → script ≤6 sıralı dalgaya çevrildi → başarılı (18.7M tok, ~102dk).
- **keep 5,513 (%40.6) / drop 7,835 / missing 238.** Drop baskın: garbled 4,915.
- DB: `pipeline_metadata.student_coherent=true` (5,513), backup
  `question_bank_student_coherent_backup_20260531`, `quality_review_status` dokunulmadı.
- **Beta-practice → student_coherent'a çevrildi** (221→5,513): `_select_beta_questions`
  filtresi + cache key `BETA:student_coherent:all`. Canlı doğrulandı (20 soru, all_clean PASS).
- Doc: `docs/audits/2026-05-31_goldpool_coherence_pilot.md`. Commits: f4cb61632, 61a243e90, +bu.

### ⏳ KALAN (sonraki adımlar)
1. **Öğrenci daveti** — 10-20 kişi (kayıt açık/KVKK hazır → buton görünür). Artık 5,513 temiz havuz.
2. **garbled 4,915 → Vision re-OCR** (GEMINI key AUP rotate bekliyor) — flag gizler, re-gen çözer.
3. **figure_dependent 1,880** → görsel-ekleme veya kalıcı eleme.
4. **subject_tag kontaminasyonu** (6 ajan raporladı: FİZİK/EDEBİYAT etiketi sıkça bozuk-matematik) — ayrı P1.
5. Önceki: 114 disputed Curator.

## 🔧 STATE
- Branch **master**. Backend/Frontend/Redis/PG **UP & healthy** (handoff yanılmış).
- Beta backend değişiklikleri **canlı container'a deploy edildi** (cp+restart),
  ama **commit edilmedi** + frontend rebuild edilmedi.
- 386 beta_clean: `pipeline_metadata::jsonb->>'beta_clean_verified'='true'`, 386
  total/active, 0 bozuk metin, 11 ders.

## ⚙️ GOTCHA (bu oturum)
- Git Bash `/tmp/...`'i Windows yoluna çevirir → `docker exec` için
  `MSYS_NO_PATHCONV=1` + `-e PYTHONPATH=/app -w /app`.
- `.venv_win`'de cachetools/ruff YOK → backend Python doğrulaması container'da.
- Test conftest `TEST_DATABASE_URL` yoksa SQLite → integration test beta havuzunu
  göremez (skip). Gerçek doğrulama: container script veya curl E2E.
- ModernButton variant: `gradient|glass|solid|outlined|text` (primary YOK).
- `_select_beta_questions` ilk sorgu 161ms (seq scan, JSON ->> index yok); pool
  cache'leniyor. 10-20 öğrenci için sorun değil (YAGNI).
