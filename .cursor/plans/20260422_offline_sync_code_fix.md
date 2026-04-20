# Plan: offline_sync_service — ORM Alan Uyumsuzluğu Fix (Kod Borcu #4)

**Tarih:** 2026-04-22
**Tür:** **Kod düzeltme pilotu** (router aktivasyon değil — aktivasyon pilotu `20260421_offline_sync_activation.md` Kısmi başarı ile bitti)
**Yürütücü:** Composer 2 (kod değişikliği + smoke) + insan onayı (docker cp + commit)
**Kaynak:** `20260421_offline_sync_RESULT.md` §11.1 #4; model `models/question_bank.py`; servis `services/offline_sync_service.py`
**Süre tahmini:** 45 dk – 1 saat (tek dosya, tek satır, smoke regression)
**Risk seviyesi:** Düşük — migration yok, model yok, izole fonksiyon; rollback `git restore` ile 30 saniye

---

## 1. Neden Bu Pilot

Aktivasyon pilotunun 4. kod borcu: `GET /api/v1/offline/sync-package` 500 dönüyor çünkü `build_sync_package` `QuestionBankItem.options` (dict) okuyor, ama ORM'de bu attribute yok; alanlar `option_a` … `option_e`. Bu endpoint **hiç çalışmıyor** — frontend offline pakedini üretemez, POST'a gerçek `package_id` gönderemez. Diğer 3 kod borcu (#1 student_answers, #2 package_id persist, #3 FSRS eşleme) daha büyük iş (ürün kararı + migration); bu 4. tek başına izole ve hızlı.

**Tek başına #4'ü çözmek mantıklı çünkü:**
- GET endpoint'i canlı hale gelir → pilot "Kısmi" yerine tam başarı
- Diğer 3 borç için zemin hazırlar (servis dokunulur ama dar kalır)
- Kapsam tek dosya → commit temiz, review kolay

---

## 2. Prior Knowledge (Doğrulanmış)

Bu faktaları Composer 2 tekrar sorgulamasın:

| Fakta | Kaynak |
|---|---|
| `QuestionBankItem.__tablename__` = `question_bank` | `models/question_bank.py` (Claude okudu) |
| Kolonlar: `option_a`, `option_b`, `option_c`, `option_d` (Text, NOT NULL) + `option_e` (Text, nullable) | model dosyası |
| `QuestionBankItem.options` **diye bir attribute YOK** (hybrid_property da değil) | model dosyası tam okundu |
| Hata satırı: `raw_options = q.options if isinstance(q.options, dict) else {}` (`build_sync_package` içinde) | `offline_sync_service.py` |
| Pydantic `OfflineQuestion.options: dict` (dict bekliyor — boş {} da geçerli) | `api/offline_sync_api.py` |
| Docker geliştirme akışı: `docker cp` + `find .pyc -delete` + `docker restart`; image rebuild gerekmez | briefing v13 "DOSYA GUNCELLEME" |
| Aktivasyon pilotu HEAD commit'i: `1ad070a` | kullanıcı mesajı |
| Servisin diğer ORM erişimleri (`q.question_text`, `q.correct_answer`, `q.subject_area`, `q.primary_topic_id`, `q.difficulty_level`) **model ile uyumlu** | model + servis cross-check |

---

## 3. Fix'in Kesin İçeriği

### Hedef dosya
`backend/services/offline_sync_service.py`

### Hedef fonksiyon
`build_sync_package` (tek yer)

### Değişecek satır
Mevcut (yaklaşık satır 78–92 civarı — fonksiyonun soru döngüsünde):

```python
for q in questions_db:
    # options is stored as a JSON dict {"A": "...", "B": "...", ...}
    raw_options = q.options if isinstance(q.options, dict) else {}
    questions.append(
        {
            "id": q.id,
            "text": q.question_text or "",
            "options": raw_options,
            ...
        }
    )
```

### Yeni hali

```python
for q in questions_db:
    # QuestionBankItem ORM has option_a..option_e columns (Text).
    # Compose into a dict for the OfflineQuestion.options payload.
    raw_options: dict[str, str] = {
        "A": q.option_a or "",
        "B": q.option_b or "",
        "C": q.option_c or "",
        "D": q.option_d or "",
    }
    if q.option_e:
        raw_options["E"] = q.option_e
    questions.append(
        {
            "id": q.id,
            "text": q.question_text or "",
            "options": raw_options,
            ...
        }
    )
```

**Neden böyle:**
- `option_a..d` NOT NULL ama defensive `or ""` — model değişirse patlamasın
- `option_e` nullable → varsa ekle, yoksa key'i atla (frontend 4-şıklı soruyu 5. şıksız alır)
- Yorum güncel — "stored as JSON dict" yorumunu sildim, ORM gerçeği yazdım
- Type annotation eklendi (kolay review)

### Ne DEĞİŞMEYECEK

- Model (`models/question_bank.py`) — dokunulmayacak
- Migration — yok
- API Pydantic schema (`api/offline_sync_api.py`) — dokunulmayacak (zaten uyumlu)
- `process_sync_results`, `get_sync_status`, `_apply_fsrs_grade` fonksiyonları
- Router / loader / config

---

## 4. Ön Koşullar (İnsan, ~5 dk)

- [ ] **Docker healthy:** `docker ps | Select-String kiro2-backend` → `(healthy)`
- [ ] **Git temiz**: `git status` → `1ad070a HEAD`, yalnızca `M KIRO2_SESSION_BRIEFING.md` + bilinen untracked'ler
- [ ] **Backup** (fix write endpoint davranışını değiştirebileceği için öneri — zorunlu değil, aktivasyon pilotu backup'ı 24 saat içinde ise yeter):
  ```powershell
  $env:PGPASSWORD='postgres'
  & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -p 5434 -U postgres -d kiro2 -F c -f "C:\Users\husey\kiro2\backups\kiro2_pre_offline_fix_20260422.dump"
  ```
- [ ] **Rollback planı hazır:**
  ```powershell
  # Fix sonrası patlama olursa:
  git restore backend/services/offline_sync_service.py
  docker cp C:\Users\husey\kiro2\backend\services\offline_sync_service.py kiro2-backend:/app/services/offline_sync_service.py
  docker exec kiro2-backend bash -c "find /app -name '*.pyc' -delete"
  docker restart kiro2-backend
  ```

---

## 5. Adım Adım Plan

### ADIM 0 — Sürpriz Kontrolü (10 dk)

**Composer 2 yapar. Kod dokunma, sadece doğrulama.**

Amaç: #4 dışında `QuestionBankItem` ile başka ORM uyumsuzluğu var mı kontrol et.

```powershell
# Servisteki tüm `q.` erişimlerini listele
Select-String -Path C:\Users\husey\kiro2\backend\services\offline_sync_service.py -Pattern "q\.\w+" | ForEach-Object { $_.Line.Trim() }

# Model'de gerçekten var olan attribute'lar
Select-String -Path C:\Users\husey\kiro2\backend\models\question_bank.py -Pattern "^\s+\w+:\s*Mapped\[" -Context 0 | Select-Object -First 60
```

**Karar noktası (Composer 2 özet verir, insan onaylar):**
- Her `q.<attr>` erişimi model'de var mı?
- Varsa tip uyumu (mesela `q.difficulty_level.value` — Enum olmalı)?
- Tek uyumsuzluk `q.options` ise → ADIM 1'e geç
- Ek uyumsuzluk varsa → DUR, plan revize

### ADIM 1 — Fix Uygula (5 dk)

**Composer 2 düzenler, insan docker cp onaylar.**

1. `backend/services/offline_sync_service.py` dosyasında §3'teki değişikliği yap (`str_replace` / `edit_block` kullan; tek satır değişimi, `for q in questions_db:` bloğu içinde).

2. **Lokal diff kontrol:**
   ```powershell
   cd C:\Users\husey\kiro2
   git diff backend/services/offline_sync_service.py
   ```
   Bekleniyor: sadece ~8–10 satır değişim, yalnızca `build_sync_package` içinde.

3. **Container'a kopyala + cache temizle + restart** (İNSAN komutu onayla):
   ```powershell
   docker cp C:\Users\husey\kiro2\backend\services\offline_sync_service.py kiro2-backend:/app/services/offline_sync_service.py
   docker exec kiro2-backend bash -c "find /app -name '*.pyc' -delete"
   docker restart kiro2-backend
   Start-Sleep -Seconds 10
   ```

4. **Health check:**
   ```powershell
   curl.exe -s http://localhost:8000/health
   docker logs kiro2-backend --tail 30 | Select-String -Pattern "offline|ERROR"
   ```
   Bekleniyor: `{"status":"ok"}`, log'da `Registered learning/offline_sync_api` yeni bir hata yok.

### ADIM 2 — Smoke Regression (15 dk)

**Composer 2 yapar. Aktivasyon pilotunun smoke'unu tekrarla — 4. borç yüzünden başarısız olanı ölç.**

```powershell
$body = '{"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}'
$login = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/giris" `
         -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
$t = ($login.Content | ConvertFrom-Json).access_token
$h = @{ Authorization = "Bearer $t" }
```

#### 2.1 — `GET /sync-package?limit=5` (yeşil olması BEKLENEN REGRESSION)

```powershell
$r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/offline/sync-package?limit=5" `
     -Headers $h -UseBasicParsing
$r.StatusCode
$pkg = $r.Content | ConvertFrom-Json
$pkg.package_id
$pkg.total_questions
$pkg.questions.Count
# options dict'inin gerçek içeriği
if ($pkg.questions.Count -gt 0) {
    $pkg.questions[0].options | ConvertTo-Json
}
```

**Beklenen:**
- HTTP **200** (önceki 500'dü — #4 düzeldi)
- `questions[0].options` bir dict; keys: A, B, C, D (çoğu soruda) ve bazı soru için E de var
- `$pkg.package_id` geçerli UUID string

**Kırmızı bayrak:**
- 500 → başka ORM uyumsuzluğu (ADIM 0 atlanmış)
- 200 ama `options` boş dict → dict composition hatalı, fix'i gözden geçir
- 422 → Pydantic schema uyumsuz (beklenmez ama ölç)

#### 2.2 — `GET /sync-status` (regression — hala 200 olmalı)

```powershell
$r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/offline/sync-status" `
     -Headers $h -UseBasicParsing
$r.StatusCode
$r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

Bekleniyor: 200, aktivasyon pilotundakine denk yanıt.

#### 2.3 — `POST /sync-results` (gerçek `package_id` ile — #2 borcu doğrulama)

Bu sefer 2.1'den alınan **gerçek** `package_id`'i kullan. #2 borcu "package_id persist değil" olduğu için sunucu yine kabul edecek — ama bu fix onun görevi değil. Regression kontrolü olarak 200 beklenir.

```powershell
$qid = & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -t -A -c `
       "SELECT id FROM question_bank WHERE is_active=true LIMIT 1;"
$qid = $qid.Trim()
$now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$payload = @{
  package_id   = $pkg.package_id
  completed_at = $now
  results = @(
    @{ question_id=$qid; selected_answer="A"; is_correct=$true; time_seconds=10.0; answered_at=$now }
  )
} | ConvertTo-Json -Depth 4

$r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/offline/sync-results" `
     -Method POST -Headers $h -ContentType "application/json" -Body $payload -UseBasicParsing
$r.StatusCode
$r.Content | ConvertFrom-Json
```

Bekleniyor: 200, `synced_count=1`, `failed_count=0`. (`next_sync_recommended_at` ISO string.)

#### 2.4 — Post-smoke log taraması

```powershell
docker logs kiro2-backend --tail 150 2>&1 | Select-String -Pattern "offline|ERROR|CRITICAL" | Select-Object -Last 20
```

Yeni `ERROR` yoksa fix temiz.

### ADIM 3 — (Opsiyonel) Unit Test Ekle (15 dk)

**Karar noktası — insan onayı gerekir.**

Bu fix gibi "sessiz attribute hatası" için küçük bir unit test gelecekteki regression'ı yakalar. Ama pilot scope'unu genişletir.

**Seçenek A — Test yaz (Composer 2 üretir):**
- `backend/tests/services/test_offline_sync_service.py` (yeni dosya)
- Mock DB session, 2 soru: biri option_e'li, biri option_e=None
- Assert: dönen paketin `questions[i].options` dict'i doğru key'lerle dolu

**Seçenek B — Atla, pilot'u dar tut:**
- Test yok, smoke regression yeterli kanıt
- `20260422_offline_sync_code_fix_RESULT.md`'ye "test eksik, ileri iş" notu

**Önerim:** Seçenek B — bu fix için unit test marjinal değer (smoke zaten kanıtladı), ama genel bir politika olarak "her kod fix commit'ine test ekle" kuralına insanın karar vermesi gerek. Bu pilotta atlanabilir.

### ADIM 4 — Commit + Rapor (15 dk)

**Composer 2 rapor + commit mesajı üretir, insan commit eder.**

#### 4.1 Kapsam kontrolü

```powershell
git status --short
```

**Beklenen yeni/değişen dosyalar (yalnızca bunlar):**
- `M backend/services/offline_sync_service.py` (fix)
- `?? .cursor/plans/20260422_offline_sync_code_fix.md` (bu plan)
- `?? .cursor/plans/20260422_offline_sync_code_fix_RESULT.md` (yeni)
- (Seçenek A ise) `?? backend/tests/services/test_offline_sync_service.py`

**Hala `M`:** `KIRO2_SESSION_BRIEFING.md` (v13 pending, ayrı iş, dokunma).

#### 4.2 RESULT dosyası şablonu

`.cursor/plans/20260422_offline_sync_code_fix_RESULT.md`:

```markdown
# Code Fix RESULT — offline_sync_service #4

**Tarih:** 2026-04-22
**Tür:** Kod düzeltme pilotu
**Sonuç:** Başarı

## ADIM 0 özet
- Servisteki q.* erişimleri: (liste)
- #4 dışında ORM uyumsuzluğu: Yok

## Değişiklik
- Dosya: `backend/services/offline_sync_service.py`
- Fonksiyon: `build_sync_package`
- Satır sayısı değişimi: +N / -M
- Model değişikliği: Yok
- Migration: Yok

## Smoke regression sonuçları
| Test | Öncesi | Sonrası | Not |
|---|---|---|---|
| GET /sync-status | 200 | 200 | aynı yanıt |
| GET /sync-package?limit=5 | **500** | **200** | options dict doğru şekilde dolu |
| POST /sync-results (gerçek package_id) | 200 (dummy UUID ile) | 200 | synced=1 failed=0 |

## Etki
- Kod borcu #4: KAPANDI
- Kod borcu #1, #2, #3: hala açık (ayrı pilotlar gerekli)
- Aktivasyon pilotu "Kısmi başarı" statusu artık "Başarı" olarak güncellenebilir (brief update ayrı iş)

## Kapsam dışı (açıkça ayrıldı)
- Unit test: (Seçenek A/B — insan kararı)
- Briefing v13 açık konular güncelleme

## Sonraki adım
Diğer 3 kod borcu için ayrı planlar:
- `.cursor/plans/20260423_offline_sync_debt_1_student_answers.md`
- `.cursor/plans/20260424_offline_sync_debt_2_package_persist.md`
- `.cursor/plans/20260425_offline_sync_debt_3_fsrs_fk.md`

Ya da öncelik kayarsa: `api.pwa_sync_api` aktivasyon pilotu.
```

#### 4.3 Commit

```powershell
git add backend/services/offline_sync_service.py
git add .cursor/plans/20260422_offline_sync_code_fix.md
git add .cursor/plans/20260422_offline_sync_code_fix_RESULT.md
# (Seçenek A ise) git add backend/tests/services/test_offline_sync_service.py

git -c core.hooksPath=.git/hooks-empty commit -m "fix(offline_sync): build_sync_package compose options from option_a..e (debt #4)"
```

**YASAK:** `git push`, `KIRO2_SESSION_BRIEFING.md`'ye dokunma, `api/offline_sync_api.py`'a dokunma, diğer kod borçlarını fix'e karıştırma.

---

## 6. Risk Matrisi

| Risk | Etki | Olasılık | Azaltma |
|---|---|---|---|
| ADIM 0'da `q.options` dışında başka uyumsuzluk bulunur | Fix yetersiz, smoke hala fail | Düşük | ADIM 0 her `q.*` erişimini cross-check eder; ek bulguyla plan revize |
| Diff'te beklenmedik değişiklik | Review yükü, commit kirli | Düşük | ADIM 1.2'de `git diff` zorunlu |
| `docker cp` ile yanlış dosya kopyalanır | Container bozulur | Düşük | Kesin path, rollback komutu hazır (§4) |
| `.pyc` temizlik atlanır, eski kod çalışır | Smoke fail ama kod doğru | Düşük | ADIM 1.3 explicit |
| Smoke geçer ama üretim kullanıcısında `option_e` hep null → frontend 5-şık bekliyorsa çakışır | Minor UI bug | Çok düşük | `option_e` varsa eklenir (dict'te key dinamik); frontend `options["E"]` yoksa kontrol etmeli (ayrı iş) |
| Aynı fonksiyon'da gelecek kod borçları (#1 `student_answers`) fix'ini bu commit'e alma eğilimi | Scope creep | Orta | Composer 2 prompt'unda açıkça yasak; RESULT'ta "kapsam dışı" satırı |

---

## 7. Başarı Ölçütleri

- [ ] ADIM 0 raporu üretildi, ek uyumsuzluk yok onaylandı
- [ ] `git diff` 1 dosyayı, 1 fonksiyonu gösteriyor (~8–10 satır)
- [ ] `GET /sync-package?limit=5` → 200 (önceki 500'den regression)
- [ ] Yanıtta `questions[i].options` doğru formatta dict (A..D, varsa E)
- [ ] `GET /sync-status` → 200 (regression, değişmemiş)
- [ ] `POST /sync-results` → 200 (gerçek package_id ile)
- [ ] `docker logs` yeni ERROR yok
- [ ] Commit temiz: 3 dosya (fix + plan + RESULT), briefing dokunulmamış
- [ ] RESULT'ta "kod borcu #4 kapandı, diğer 3 açık" açıkça yazılı

---

## 8. Kapsam Dışı (Açıkça Ayrıldı)

Bu pilot **DÜZELTMEZ:**

- **#1 `student_answers` persist YOK** — ayrı plan (ürün kararı: virtual exam_session mi, yoksa offline_answers ayrı tablo mu?)
- **#2 `package_id` uçucu** — ayrı plan (yeni tablo + migration)
- **#3 FSRS eşleme `front_text.contains`** — ayrı plan (migration ile FK eklemek + process_sync_results refactor + `synced += 1` sessiz başarı sayacı düzeltmesi)
- **Briefing v13 güncellemesi** — aktivasyon pilotundan beri pending
- **Unit test coverage** — Seçenek B önerildi
- **Frontend offline_e handling** — frontend ayrı iş

---

## 9. Sonraki Pilot

**Öncelik sırası (sende karar hakkı):**

1. **#2 package_id persist** — orta zor (tek tablo migration + process doğrulama), saldırı yüzeyini kapatır
2. **#3 FSRS FK** — zor (migration + servis refactor + sessiz başarı sayacı)
3. **#1 student_answers** — en zor (ürün kararı önce)
4. **Alternatif yol:** `api.pwa_sync_api` aktivasyon pilotu (batch rapor 2. sıra); offline borçları bir kenarda bırak

---

## 10. Composer 2 için Yükleme Prompt'u

Cursor'da yeni turn olarak yolla:

```
@.cursor/plans/20260422_offline_sync_code_fix.md — uygula.

Prior (okunmuş olarak al, tekrar sorgulama):
  @backend/_pilots/20260421_offline_sync_state.md
  @.cursor/plans/20260421_offline_sync_RESULT.md

HEDEF: offline_sync_service.py build_sync_package fonksiyonunda q.options 
erişimini §3'te verilen dict comprehension ile değiştir. Migration YOK, 
model YOK, diğer 3 kod borcuna DOKUNMA.

ADIMLAR (sırayla):
  ADIM 0 — §5.0 Sürpriz kontrolü. Başka q.<attr> uyumsuzluğu varsa DUR, 
           bana göster.
  ADIM 1 — §5.1 Fix + docker cp + pyc temizle + restart. Her docker komutunu 
           bana onaylat.
  ADIM 2 — §5.2 Smoke regression (sync-package 500→200 beklenir).
  ADIM 3 — ATLA (Seçenek B — unit test ayrı karar).
  ADIM 4 — §5.4 RESULT dosyası + commit önerisi. Commit komutunu bana GÖSTER 
           ama ÇALIŞTIRMA — ben yapacağım.

YASAK:
  × Migration yazma, alembic upgrade
  × Model değişikliği (models/question_bank.py)
  × api/offline_sync_api.py'a dokunma
  × #1, #2, #3 borçlarını bu fix'e karıştırma
  × KIRO2_SESSION_BRIEFING.md'ye dokunma
  × git push
  × Unit test eklemeye kalkışma (Seçenek B karar verildi)

ÇIKTILAR:
  1. ADIM 0 özeti — q.<attr> listesi + uyumsuzluk var/yok kararı
  2. git diff çıktısı (ADIM 1.2)
  3. Smoke tablosu (ADIM 2, 3 endpoint)
  4. .cursor/plans/20260422_offline_sync_code_fix_RESULT.md
  5. Commit komut önerisi (çalıştırma)

KURALLAR:
  • Token alanı access_token
  • Hook'suz commit: git -c core.hooksPath=.git/hooks-empty commit -m "..."
  • Commit mesajı: "fix(offline_sync): build_sync_package compose options from option_a..e (debt #4)"
  • Herhangi bir sürpriz → DUR, göster, sor
```

---

*Plan v1 hazırlandı: 2026-04-22 (Claude, `20260421_offline_sync_activation.md` v2 pattern'inden; model + servis cross-read ile doğrulandı). Kapsam dar: tek dosya, tek fonksiyon, 8–10 satır.*
