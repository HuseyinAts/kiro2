# Plan: `api.offline_sync_api` Pilot Aktivasyonu

**Tarih:** 2026-04-21 (v2 — ADIM 0 sonrası revizyon)
**Yürütücü:** Composer 2 (pattern işi) + insan onayı (risk noktalarında)
**Kaynak:** Batch ADIM 0 önerisi — `backend/_pilots/20260420_batch_router_state.md` Bölüm 3
**Onaylanmış aşama:** **B (şema) + D (kod borcu bilinen, ayrı iş)** — `backend/_pilots/20260421_offline_sync_state.md`
**Süre tahmini:** 1–2 saat (ADIM 0 bitti, kalan smoke + rapor + commit)
**Risk seviyesi:** Düşük — yeni tablo yok, migration yok; smoke sadece gözlem + davranış delili toplar

---

## 1. Neden Bu Pilot

- **Batch raporu önerdi:** `20260420_batch_router_state.md` Bölüm 3 — `api.offline_sync_api` Aşama B, dış bağımlılık yok.
- **Dar endpoint yüzeyi:** 3 endpoint (`GET /sync-package`, `POST /sync-results`, `GET /sync-status`).
- **Pattern pekiştirme:** Diary pilotunun iş akışını 2. kez uygulayarak tekrar edilebilirliği kanıtla.
- **ADIM 0 ek kazanım:** Servis katmanında 3 teknik borç (aşağıda §11.1) tespit edildi; pilot bunları belgeler ama düzeltmez — ayrı iş.

---

## 2. Prior Knowledge (Önceki Pilotlar + Bu Pilotun ADIM 0'ı)

Aşağıdakiler teyit edildi, Composer 2 tekrar sorgulamasın:

| Fakta | Kaynak |
|---|---|
| `DISABLED_ROUTERS = {}` boş | `20260420_diary_api_state.md` §0.4 |
| Alembic head: `student_review_drift_001` (tek head) | diary state §0.3 |
| `users.id` = `character varying` (VARCHAR) | diary state §0.2 |
| `api.offline_sync_api` `ROUTER_MAPPING`'te, kategori `learning` | batch state Bölüm 1 #9 |
| Log: `Registered … at /api/v1/offline`, import hatası yok | offline_sync state §0.1 |
| Token alanı: `access_token` | briefing v13, diary state |
| Auth endpoint: `POST /api/v1/auth/giris` | briefing v13 |
| `question_bank.id`, `student_answers.id`, `fsrs_cards.id`, `topic_progress.student_id` hepsi VARCHAR | offline_sync state §0.3 |
| FSRS tablosu = `fsrs_cards` (servis yalnızca bu tabloyu kullanıyor) | offline_sync state §0.2, §0.5 |
| `offline_sync_service` `topic_progress` **sorgulamıyor** (batch raporunun önkoşul varsayımı bu servis için geçersiz) | offline_sync state §0.2 |
| `student_answers` tablosu var, ama `student_id` kolonu **YOK** (bağlantı `exam_session_id` üzerinden) | offline_sync state §0.3 |
| `offline_sync_service.process_sync_results` `student_answers`'a **INSERT yapmıyor** (yalnızca `fsrs_cards` günceller) | offline_sync state §0.2 |
| `package_id` DB'ye persist edilmiyor (uçucu UUID) | offline_sync state §0.2 |
| FSRS eşleme: `FSRSCard.front_text.contains(question_id)` — substring arama, kırılgan | offline_sync state §0.2 |

**Bu faktaların hiçbiri yeniden sorgulanmayacak.** Smoke bu davranış çerçevesi içinde tasarlandı.

---

## 3. Doğrulanmış Mevcut Durum (21 Nisan 2026, ADIM 0 sonrası)

| Alan | Durum | Kaynak |
|---|---|---|
| `backend/api/offline_sync_api.py` | Var, 8.8 KB, 11.04.2026 | plan yazımı |
| Router prefix / endpoint | `/api/v1/offline`, 3 endpoint (GET sync-package, POST sync-results, GET sync-status) | API dosyası |
| Service dependency | `services.offline_sync_service` — 3 fonksiyon (build/process/status) | lazy import |
| `backend/services/offline_sync_service.py` | Var, 10.7 KB, 13.03.2026 | ADIM 0 tam okundu |
| FSRS tabloları (DB) | `fsrs_cards`, `fsrs_reviews`, `fsrs_schedules`, `fsrs_student_profiles`, `fsrs_study_sessions`, `fsrs_subject_stats`, `user_item_fsrs` — **7 tablo mevcut** | offline_sync state §0.3 |
| Çekirdek tablolar | `question_bank`, `student_answers`, `topic_progress` — hepsi var, VARCHAR uyumlu | offline_sync state §0.3 |
| Alembic drift | FSRS için history'de satırlar var (`20260401_add_missing_tables`, `20260401_fix_fsrs_reviews_fk`, `20260410_create_user_item_fsrs`) — offline'a özgü migration yok (servis tablo yaratmıyor, gerek yok) | offline_sync state §0.4 |
| Docker servisleri | `kiro2-backend` healthy, PG/Redis/Ollama ayakta; celery-worker/beat, frontend, ES şu an down (pilot için blok değil) | `docker ps` |
| **Bilinen kod sorunları** | 3 adet (§11.1) — pilot bunları belgeler, düzeltmez | offline_sync state §0.2 |

---

## 4. Risk Matrisi

| Risk | Etki | Olasılık | Azaltma |
|---|---|---|---|
| Admin user'ın `fsrs_cards`'ta kartı yok → eşleşme=0, smoke "sessiz başarı" yazar | Smoke "synced=1 failed=0" ama DB değişmiyor (beklenen davranış, belgelenir) | Yüksek | Pre-call `fsrs_cards` sayımı yap; post-call karşılaştır; yoksa durumu RESULT'ta açıkla |
| `process_sync_results` transaction hatası | 500 | Düşük | Tek elemanlı `results` listesiyle test |
| Geçerli `question_id` alamama | sync-results input validation fail | Düşük | Psql ile `question_bank` → `is_active=true LIMIT 1` |
| Smoke sırasında log'a yeni ERROR düşmesi | Gizli bozulma | Düşük | Post-smoke `docker logs kiro2-backend --tail 100` taraması |
| Kod borcu (§11.1) birilerinin "bu çalışıyor" diye yanlış yorumlaması | Ürün kararı distorsiyonu | Orta | RESULT'ta "Known limitations" bölümü belirgin; briefing v13 açık konular'a eklenir |

---

## 5. Ön Koşullar (İnsan yapar, ~5 dk)

- [x] **ADIM 0 raporu okundu:** `backend/_pilots/20260421_offline_sync_state.md`
- [ ] **Backup** (yazma endpoint'i `fsrs_cards`'a update yapabilir):
  ```powershell
  $env:PGPASSWORD='postgres'
  & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -p 5434 -U postgres -d kiro2 -F c -f "C:\Users\husey\kiro2\backups\kiro2_pre_offline_sync_20260421.dump"
  ```
- [ ] **Docker sağlık:** `docker ps | Select-String kiro2-backend` → `Up X (healthy)`
- [ ] **Git durumu:** Beklenmeyen değişiklik olmamalı. `M KIRO2_SESSION_BRIEFING.md`, `?? NEXT_SESSION_HANDOFF.md`, `?? DERSLER.md`, `?? backups/` mevcut — bunlar olduğu gibi kalır.

---

## 6. Adım Adım Plan

### ADIM 0 — Durum Tespiti ✅ TAMAMLANDI

**Çıktı:** `backend/_pilots/20260421_offline_sync_state.md`
**Özet:** Aşama B (şema uyumlu) + Aşama D (3 kod borcu — §11.1).
**Karar:** Pilot Aşama B çerçevesinde smoke + RESULT + commit ile devam. Migration YOK, kod değişikliği YOK.

### ADIM 1A — (Şartlı) Migration — ATLANIR

Aşama B sonucu: tüm gerekli tablolar mevcut ve VARCHAR uyumlu. Migration dosyası **yazılmayacak**.

### ADIM 2 — Smoke Test (20–30 dk)

**Composer 2 yapar. HTTP çağrısı + psql gözlem; kod/migration/commit yok.**

#### 2.1 Auth

```powershell
$body = '{"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}'
$login = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/giris" `
         -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
$t = ($login.Content | ConvertFrom-Json).access_token
$h = @{ Authorization = "Bearer $t" }

# Admin user_id'yi al (psql), sonraki adımlarda kullanılacak
$env:PGPASSWORD='postgres'
$uid = & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -t -A -c `
       "SELECT id FROM users WHERE email='admin@kiro2.com';"
$uid = $uid.Trim()
```

#### 2.2 `GET /api/v1/offline/sync-status`

```powershell
$r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/offline/sync-status" `
     -Headers $h -UseBasicParsing
$r.StatusCode
$r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 4
```

**Beklenen:** 200, alanlar: `last_sync_at` (null olabilir), `pending_results_count` (integer), `offline_package_version` (string).
**Kırmızı bayrak:** 500 / 503.

#### 2.3 `GET /api/v1/offline/sync-package?limit=5`

```powershell
$r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/offline/sync-package?limit=5" `
     -Headers $h -UseBasicParsing
$r.StatusCode
$pkg = $r.Content | ConvertFrom-Json
"package_id: $($pkg.package_id)"
"total_questions: $($pkg.total_questions)"
"questions returned: $($pkg.questions.Count)"
"fsrs_due_cards: $($pkg.fsrs_due_cards.Count)"
```

**Beklenen:** 200, `package_id` string, `questions` array (admin user'da FSRS geçmişi yoksa boş olabilir — meşru senaryo).

#### 2.4 `POST /api/v1/offline/sync-results` (write path + FSRS gözlemi)

**Ön-ölçüm** — bu student için `fsrs_cards` durumu:

```powershell
$q_pre = @"
SELECT COUNT(*) AS total, MAX(last_review) AS last_rev
FROM fsrs_cards
WHERE student_id = '$uid';
"@
Write-Host "PRE-CALL fsrs_cards state for admin:"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c $q_pre
```

**Geçerli `question_id` seç:**

```powershell
$qid = & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -t -A -c `
       "SELECT id FROM question_bank WHERE is_active=true LIMIT 1;"
$qid = $qid.Trim()
Write-Host "Using question_id: $qid"
```

**POST çağrısı** (eğer 2.3 package dönmüşse onu kullan, yoksa dummy UUID):

```powershell
$pkgid = if ($pkg -and $pkg.package_id) { $pkg.package_id } else { [guid]::NewGuid().ToString() }
$now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$payload = @{
  package_id   = $pkgid
  completed_at = $now
  results = @(
    @{
      question_id     = $qid
      selected_answer = "A"
      is_correct      = $true
      time_seconds    = 12.5
      answered_at     = $now
    }
  )
} | ConvertTo-Json -Depth 4

$r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/offline/sync-results" `
     -Method POST -Headers $h -ContentType "application/json" -Body $payload -UseBasicParsing
$r.StatusCode
$resp = $r.Content | ConvertFrom-Json
"synced_count: $($resp.synced_count)"
"failed_count: $($resp.failed_count)"
"next_sync_recommended_at: $($resp.next_sync_recommended_at)"
```

**Beklenen:**
- 200 OK
- `synced_count` integer (1 bekleniyor ama servis kart eşleşmese bile sayıyor — §11.1 kod borcu #3)
- `failed_count` integer (0 veya 1 ikisi de meşru)
- `next_sync_recommended_at` ISO string

**Kırmızı bayrak:** 500 (transaction/exception), 422 (schema), 401 (auth kayması).

#### 2.5 DB davranış gözlemi (FSRS odaklı, `student_answers` DEĞİL)

```powershell
Write-Host "POST-CALL fsrs_cards state for admin:"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c $q_pre

# FSRS eşleme yolunu da gözlemle: question_id front_text'te mi?
$q_match = @"
SELECT COUNT(*) AS matching_cards
FROM fsrs_cards
WHERE student_id = '$uid'
  AND front_text LIKE '%$qid%';
"@
Write-Host "FSRS front_text LIKE match count:"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c $q_match
```

**Yorumlama:**
- Pre-call `total` == Post-call `total`, `last_rev` aynı, `matching_cards = 0` → admin'in bu soruya ait kartı yok; servis `synced=1` dedi ama DB değişmedi. Bu **§11.1 kod borcu #3'ün canlı kanıtı**, pilot "başarılı + bilinen sınırlama" sayılır.
- `last_rev` arttıysa ve `matching_cards > 0` → FSRS güncellemesi gerçekten uygulandı, servis "çalışıyor" (ancak front_text substring yöntemi hala kırılgan).
- `total` değiştiyse → beklenmeyen, araştır.

#### 2.6 Post-smoke log taraması

```powershell
docker logs kiro2-backend --tail 100 2>&1 | Select-String -Pattern "offline|ERROR|CRITICAL" | Select-Object -Last 20
```

Yeni `ERROR` yoksa pilot smoke bölümü temiz.

---

### ADIM 3 — Commit + Rapor (15–20 dk)

**Composer 2 üretir, insan onaylar + commit eder.**

#### 3.1 Kapsam kontrolü

```powershell
cd C:\Users\husey\kiro2
git status --short
```

**Beklenen yeni/değişen dosyalar (yalnızca bunlar):**
- `?? backend/_pilots/20260421_offline_sync_state.md` (ADIM 0 çıktısı — zaten mevcut)
- `?? .cursor/plans/20260421_offline_sync_activation.md` (bu plan — zaten mevcut)
- `?? .cursor/plans/20260421_offline_sync_RESULT.md` (yeni)

**YASAK:** `loader.py`, `main.py`, `core/*`, `services/offline_sync_service.py`, `api/offline_sync_api.py`, `KIRO2_SESSION_BRIEFING.md`'ye dokunma. Kod borcu ayrı iş.

#### 3.2 RESULT dosyası (`.cursor/plans/20260421_offline_sync_RESULT.md`)

```markdown
# Pilot RESULT — api.offline_sync_api

**Tarih:** 2026-04-21
**Aşama:** B (şema) + D (3 kod borcu belgelendi, ayrı iş)
**Sonuç:** Başarılı (bilinen sınırlamalarla)

## ADIM 0 özet
(state dosyasından 3-4 satırlık özet)

## Smoke test sonuçları
| Endpoint | Status | Süre | Not |
|---|---|---|---|
| GET /sync-status  | 200 | Xms | last_sync_at=..., pending=N |
| GET /sync-package?limit=5 | 200 | Xms | N soru, M fsrs card, package_id=... |
| POST /sync-results | 200 | Xms | synced=N failed=M |

## DB gözlem (fsrs_cards)
Pre-call:  total=X,  last_review=...
Post-call: total=Y,  last_review=...
matching_cards (front_text LIKE '%qid%'): Z
Yorum: (senaryoya göre, §2.5 yorumlamasından)

## Bilinen sınırlamalar (kod borcu — ayrı iş, bu pilotta düzeltilmedi)
1. student_answers persist edilmiyor (API docstring yanıltıcı)
2. package_id uçucu (audit açığı — rastgele UUID kabul ediliyor)
3. FSRS eşleme front_text.contains ile kırılgan; eşleşme olmasa bile synced artıyor

## Briefing v13 için öneri notu
(varsa) — örn. "P1 açık konular"a offline_sync 3 kod borcu eklenebilir

## Sonraki pilot önerisi
`api.pwa_sync_api` (Aşama B, batch rapor 2. sıra, prefix kararı gerekli)
```

#### 3.3 Commit

```powershell
git add backend/_pilots/20260421_offline_sync_state.md
git add .cursor/plans/20260421_offline_sync_activation.md
git add .cursor/plans/20260421_offline_sync_RESULT.md

git -c core.hooksPath=.git/hooks-empty commit -m "chore(pilots): offline_sync_api activation (Stage B schema OK, Stage D code debt logged)"
```

---

## 7. Composer 2 İş Bölümü (Revize)

| Görev | Kim |
|---|---|
| ADIM 0 (TAMAM) | Composer 2 |
| Aşama kararı (TAMAM — B+D onaylı) | İnsan |
| Smoke test çalıştırma (ADIM 2) | Composer 2 |
| DB gözlem sorguları (psql) | Composer 2 |
| RESULT dosyası draft | Composer 2 |
| Git kapsam kontrolü + commit | İnsan onaylar |
| Servis kodu düzeltme | **Bu pilot değil** — ayrı iş, ayrı plan |

---

## 8. Başarı Ölçütleri (Revize)

Pilot **başarılı** sayılır ancak ve ancak:

- [x] ADIM 0 raporu mevcut ve okundu
- [x] Aşama kararı yazılı ve insan onaylı (B + D)
- [ ] `GET /sync-status` → 200, geçerli JSON
- [ ] `GET /sync-package?limit=5` → 200, şema uyumlu yanıt
- [ ] `POST /sync-results` → 200, integer `synced_count` ve `failed_count`
- [ ] `fsrs_cards` pre/post gözlemi kaydedildi (değişsin veya değişmesin, RESULT'ta belgelendi)
- [ ] Post-smoke log'da yeni ERROR/CRITICAL yok
- [ ] 3 kod borcu RESULT'ta "Known limitations" altında belgelenmiş
- [ ] Commit temiz (yalnızca 3 planlanan dosya; servis/API/loader dokunulmamış)

---

## 9. Sonraki Pilot (Bu Başarılı Olursa)

**`api.pwa_sync_api`** (batch rapor 2. önerisi):
- Prefix tutarsız: `/api/pwa-sync-api`. Pilot'ta karar: düzelt mi, belgele mi?
- Tablolar: `exam_sessions`, `student_answers` — ikincisi zaten bu pilotta kontrol edildi, prior knowledge avantajı.
- ADIM 0'da endpoint listesi dosyadan çıkarılmalı.

**Ya da alternatif yol:** Offline_sync 3 kod borcunu düzeltme pilotu (`.cursor/plans/20260422_offline_sync_code_debt.md`). Ama bu auth + service refactor gerektirir, ayrı risk profili.

---

## 10. Referanslar

- **Pattern planı:** `.cursor/plans/20260420_diary_api_activation.md`
- **Bu pilotun ADIM 0'ı:** `backend/_pilots/20260421_offline_sync_state.md`
- **Prior state'ler:** `backend/_pilots/20260420_diary_api_state.md`, `20260420_batch_router_state.md`
- **API:** `backend/api/offline_sync_api.py`
- **Service:** `backend/services/offline_sync_service.py`
- **FSRS referanslar:** `backend/models/fsrs_models.py`, `alembic/versions/20260401_fix_fsrs_reviews_fk.py`
- **Briefing v13:** `KIRO2_SESSION_BRIEFING.md`

---

## 11. Uyarılar

- **Backup zorunlu** (fsrs_cards write path'i var — update-only ama yine de).
- **Dev'de çalışan prod'da çalışır anlamına gelmez.**
- **`DISABLED_ROUTERS`'a dokunma.**
- **Servis kodu bu pilotta YAZILMAZ.** Bulgular RESULT'ta belgelenir, ayrı plana havale.
- **Commit kapsamı dar** — yalnızca 3 doküman dosyası.

---

## 11.1 Known Limitations (ADIM 0'da Tespit Edildi, Ayrı İş)

Bu üç madde **offline_sync_service.py** kod seviyesinde gerçek teknik borçlar. Pilot bunları **düzeltmez**, yalnızca belgeler:

**#1 — `student_answers` persist YOK**
- `offline_sync_api.py` docstring: "student_answers'a kayıt eklenir"
- `offline_sync_service.process_sync_results` gerçeği: `student_answers` tablosuna INSERT yok; yalnızca `fsrs_cards` update
- **Etki:** Öğrencinin offline cevabı cevap tarihçesinde görünmüyor; sadece FSRS zamanlamasına yansıyor
- **Fix niyeti:** Servise `StudentAnswer` INSERT ekle (yeni `exam_session` yaratma veya "virtual offline session" kararı gerekli)

**#2 — `package_id` uçucu (audit açığı)**
- `build_sync_package` `uuid.uuid4()` üretir, yanıtta döner
- Hiçbir tabloya persist edilmez
- `process_sync_results` `package_id`'i parametre alır ama DOĞRULAMAZ — rastgele UUID kabul edilir
- **Etki:** Audit/replay imkânsız; kötüye kullanımda bir saldırgan package üretmeden sync-results POST edebilir
- **Fix niyeti:** `offline_sync_packages` tablosu (package_id, student_id, created_at, consumed_at) ve process içinde doğrulama

**#3 — FSRS eşleme `front_text.contains(question_id)` ile kırılgan**
- `FSRSCard` ile `QuestionBankItem` arasında **doğru bir FK yok**
- Servis `FSRSCard.front_text.contains(question_id)` substring arar
- Eşleşme bulunamazsa bile `synced += 1` (satır ~227) — sessiz başarı
- **Etki:** Servis "başarılı" dese bile FSRS zamanlaması güncellenmeyebilir; metrikler yanıltıcı
- **Fix niyeti:** `FSRSCard.question_id` kolonu + FK ekle; migration yaz; front_text.contains'i FK join'e dönüştür; eşleşmezse `failed += 1` yap

---

## 12. Composer 2 için Yükleme Prompt'u (v2 — Smoke + RESULT turu)

Cursor'da bu prompt'u yeni turn olarak yolla (ADIM 0 zaten yapıldı):

```
@.cursor/plans/20260421_offline_sync_activation.md — REVİZE edilmiş v2.

ADIM 0 TAMAM. Aşama kararı onaylı: B (şema) + D (3 kod borcu §11.1 belgelendi).

Bu turda SADECE:
  1. ADIM 2 smoke test (§6.2.1 → 2.6)
  2. ADIM 3 RESULT dosyası (§3.2 şablonu)
  3. ADIM 3 commit (§3.3)

YAPMAYACAKLARIN:
  × Kod değişikliği (services/ veya api/ altında)
  × Migration yazma veya alembic upgrade
  × loader.py / routers/__init__.py / DISABLED_ROUTERS'a dokunma
  × Known limitations'ı (§11.1) düzeltmeye kalkışma — pilot bunları yalnızca BELGELER
  × git push
  × Briefing veya DERSLER dosyalarına dokunma

ÖN KOŞUL (sen yapmayacaksın, ben yaptım/yapacağım):
  • Backup alındı/alınacak (insan)
  • Docker healthy kontrolü (plan §5)

SMOKE YÖNTEMİ (plan §6):
  1. Auth + admin user_id (§2.1)
  2. GET sync-status (§2.2) — 200 bekle
  3. GET sync-package?limit=5 (§2.3) — 200 bekle, package kaydet
  4. PRE-call fsrs_cards sayımı (§2.4) — pre ölçüm
  5. POST sync-results (§2.4) — 200 bekle; synced/failed sayısını NOT AL
  6. POST-call fsrs_cards + front_text LIKE sayımı (§2.5) — karşılaştır
  7. Post-smoke log taraması (§2.6) — yeni ERROR yoksa devam

RAPOR:
  → .cursor/plans/20260421_offline_sync_RESULT.md (plan §3.2 şablonunu aynen kullan)
  → §2.5 yorumlamasını RESULT "DB gözlem" bölümüne yaz
  → Known limitations bölümünü §11.1'den aynen al

COMMIT:
  git add ile YALNIZCA şu 3 dosyayı ekle:
    backend/_pilots/20260421_offline_sync_state.md
    .cursor/plans/20260421_offline_sync_activation.md
    .cursor/plans/20260421_offline_sync_RESULT.md
  git status --short → başka dosya görünüyorsa BANA SOR, ekleme.
  Commit mesajı: "chore(pilots): offline_sync_api activation (Stage B schema OK, Stage D code debt logged)"
  Hook'suz: git -c core.hooksPath=.git/hooks-empty commit -m "..."
  Push YAPMA.

KURALLAR:
  • Token alanı access_token
  • Prior knowledge §2'deki faktaları tekrar doğrulama
  • Herhangi bir sürpriz (500, log'da yeni ERROR, beklenmedik DB değişimi) → DUR, bana göster
  • admin user'ın fsrs_cards'ta kartı olmaması BEKLENEN DURUM, hata değil — RESULT'a "sessiz başarı kanıtı" olarak yaz
```

---

*Plan v2 hazırlandı: 2026-04-21, ADIM 0 (backend/_pilots/20260421_offline_sync_state.md) bulguları üzerinden Claude revize etti. Değişenler: §2 Prior Knowledge'a 5 yeni satır; §3 ADIM 0 sonrası duruma çekildi; §4 risk matrisi kod borcu odağına kaydı; §6 ADIM 0 "TAMAM" işaretlendi, ADIM 2.5 student_answers yerine fsrs_cards gözlemine dönüştürüldü; §8 başarı ölçütleri revize; §11.1 Known Limitations yeni eklendi; §12 prompt v2 — ADIM 0 tekrar etmez, smoke+RESULT+commit turu.*
