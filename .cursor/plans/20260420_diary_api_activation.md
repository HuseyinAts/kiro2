# Plan: `api.diary_api` Pilot Aktivasyonu

**Tarih:** 2026-04-20
**Yürütücü:** Composer 2 (pattern işi) + insan onayı (risk noktalarında)
**Kaynak:** `KIRO2_SESSION_BRIEFING.md` — "P1 — 13 disabled router"
**Süre tahmini:** 2-4 saat (ilk pilot, rahatça)
**Risk seviyesi:** Orta — migration geri dönüşü zor, tablolar arası FK var

---

## 1. Neden Pilot

- Briefing'te 13 disabled router listelenmiş. `api.diary_api` ilk sırada çünkü:
  - Model dosyası **tek** (`backend/models/diary.py`) — bütünlük kolay doğrulanır
  - 8 tablo içeriyor — pattern'i zor ve öğretici kılacak boyutta
  - API dosyası zaten mevcut (`backend/api/diary_api.py`, 51 KB, 11 Nisan)
- Eski migration **var ama disabled** (`20260119_add_diary_tables.py.disabled`) → hata örneği olarak değerlendirilecek
- Pilot başarılı olursa kalan 12 router için Composer 2 ile paralel uygulama güvenilir olur

---

## 2. Doğrulanmış Mevcut Durum (20 Nisan 2026 itibariyle)

Kullanıcının gözlem yaparak doğruladığı:

| Alan | Durum | Kaynak |
|---|---|---|
| `backend/models/diary.py` | **Var**, 8 model class (DiaryEntry, Insight, Reflection, LearningEntry, EmotionalState, Goal, PeerComparison, DiaryExport) | Dosya okundu |
| `backend/api/diary_api.py` | **Var**, 51 KB, 11.04.2026'da oluşturulmuş | `get_file_info` |
| `backend/api/schemas/diary.py` | **Var** (API dosyası import ediyor) | diary_api.py ilk 40 satır |
| `backend/alembic/versions/20260119_add_diary_tables.py.disabled` | **Var**, UUID kullanmış (model String beklerken) | Dosya okundu |
| `backend/routers/loader.py` `DISABLED_ROUTERS` set'i | **Boş** — yani router kod olarak aktif yüklenmeye çalışıyor | loader.py satır 21-25 |
| PostgreSQL'de 8 diary tablosu | **BİLİNMİYOR** — ADIM 0'da doğrulanacak | - |
| Alembic head | **BİLİNMİYOR** — briefing 6 Nisan `20260406_uni_dept` demiş, ama 20260410-12 dosyaları var | - |

### Kritik Çelişkiler

1. **Briefing**: "13 disabled router" → **Kod**: `DISABLED_ROUTERS = {}` (boş). Hangisi doğru?
2. **Model**: `id = Column(String, ...)` → **Disabled migration**: `id = postgresql.UUID(as_uuid=True)`. Tip uyumsuz.
3. **Briefing kuralı**: "users.id VARCHAR → user_id FK sa.String" → **Disabled migration**: `user_id = postgresql.UUID(as_uuid=True)`. Kural ihlali.

---

## 3. Risk Matrisi (Dürüst)

| Risk | Etki | Olasılık | Azaltma |
|---|---|---|---|
| Tablolar kısmen var (eski disabled migration'dan) | Migration upgrade fail | Orta | ADIM 0'da kontrol et |
| Model-schema uyumsuz (User.id vs diary_entries.user_id) | Runtime HTTP 500 | Yüksek | Tip pattern'i birebir uygula |
| Alembic zinciri kopuk | Migration uygulanamaz | Düşük | ADIM 0'da `alembic current` + `alembic heads` |
| Router zaten yüklü ama tablolar yok | Backend bazı endpoint'lerde 500 veriyor | Orta | ADIM 0'da `docker logs` incele |
| İki paralel diary migration (disabled + yeni) | Alembic karışır | Orta | `.disabled` dosyayı `_archive/`'a taşı |
| Production DB'de veri var | Migration sonrası veri kaybı | Düşük (dev ortam) | Backup al (pg_dump) |

---

## 4. Ön Koşullar (İnsan Yapacak — 15 dk)

- [ ] Backup al:
  ```powershell
  $env:PGPASSWORD='postgres'
  & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -p 5434 -U postgres -d kiro2 -F c -f "C:\Users\husey\kiro2\backups\kiro2_pre_diary_20260420.dump"
  ```
- [ ] Backend loglarına bak, halihazırda diary ile ilgili hata var mı?
  ```powershell
  docker logs kiro2-backend --tail 200 | Select-String -Pattern "diary" -CaseSensitive:$false
  ```
- [ ] Git durumu temiz mi?
  ```powershell
  cd C:\Users\husey\kiro2; git status
  ```
  Çalışan değişiklikleri `git stash` veya commit et.

---

## 5. Adım Adım Plan

### ADIM 0 — Gerçek Durum Tespiti (30 dk)

**Amaç:** Briefing ile kod arasındaki çelişkiyi çöz, başlangıç noktasını net belirle.

**Composer 2 yapabilir. Çıktı rapor, kod dokunma.**

```
Görev 0.1: PostgreSQL'de diary tabloları var mı?
---
$env:PGPASSWORD='postgres'
$q = @"
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema='public' 
  AND table_name IN (
    'diary_entries', 'insights', 'reflections', 'learning_entries',
    'emotional_states', 'goals', 'peer_comparisons', 'diary_exports'
  )
ORDER BY table_name;
"@
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c $q

Görev 0.2: Eğer bir tablo varsa, users.id ile FK tipi uyuyor mu?
---
SELECT 
  c.table_name, 
  c.column_name, 
  c.data_type, 
  c.character_maximum_length
FROM information_schema.columns c
WHERE c.table_name IN ('diary_entries','insights',...)
  AND c.column_name IN ('id','user_id','diary_entry_id')
ORDER BY c.table_name, c.ordinal_position;

Beklenen: 
- id → character varying (VARCHAR)
- user_id → character varying
- diary_entry_id → character varying

Eğer 'uuid' görürsen → disabled migration kısmen uygulanmış, AŞAMA 2'ye geç.

Görev 0.3: Alembic durumu
---
docker exec kiro2-backend alembic current
docker exec kiro2-backend alembic heads
docker exec kiro2-backend alembic history --verbose | Select-Object -First 30

Beklenen çıktı: Head TEK bir revision olmalı. Çift head varsa merge gerekir.

Görev 0.4: Router şu anda yükleniyor mu?
---
docker logs kiro2-backend 2>&1 | Select-String "api.diary_api"

Beklenen: "Registered router diary_api" benzeri log veya "Failed to import api.diary_api".

Çıktı: backend/_diary_pilot_state_20260420.md
  | Soru | Bulgu | Anlamı |
```

**Karar noktası:** Rapor bana göster. Aşamalardan hangisi geçerli:

- **AŞAMA A**: Hiç tablo yok → yeni migration yaz, ADIM 2'ye git
- **AŞAMA B**: Tablolar var, doğru tipte → migration zaten uygulanmış, ADIM 5'e git (sadece loader + doğrulama)
- **AŞAMA C**: Tablolar kısmen var, yanlış tipte (UUID) → önce drop, sonra yeni migration
- **AŞAMA D**: Beklenmeyen durum → durdur, planı gözden geçir

---

### ADIM 1 — Eski Disabled Migration'ı Arşivle (5 dk)

**İnsan + Composer 2.** Eski dosyayı silme ama göz önünden çıkar:

```bash
# Arşiv dizini
mkdir -p backend/alembic/versions/_archive/

# Disabled dosyayı taşı
mv backend/alembic/versions/20260119_add_diary_tables.py.disabled \
   backend/alembic/versions/_archive/20260119_add_diary_tables.py.disabled

mv backend/alembic/versions/c937128ce051_merge_diary_and_quality_gates.py.disabled \
   backend/alembic/versions/_archive/c937128ce051_merge_diary_and_quality_gates.py.disabled
```

**Neden arşiv?** Alembic `.disabled` uzantılı dosyaları zaten okumaz, ama başka bir migration merge ederken karşılaşmak istemeyiz.

---

### ADIM 2 — Yeni Migration Yaz (Composer 2'nin Sweet Spot'u)

**Eğer AŞAMA A veya C ise (ADIM 0 sonucu).**

Referans pattern: `backend/alembic/versions/20260406_uni_dept.py`

**Composer 2 için prompt (Plan Mode):**

```
Dosya: backend/alembic/versions/20260420_diary_tables.py

GİRDİ: backend/models/diary.py — 8 tabloyu model class'lardan türet.

ÇIKTI TEMPLATE: 20260406_uni_dept.py'ın yapısını kopyala (import + upgrade + downgrade).

KURALLAR (briefing'den, asla ihlal etme):
1. PK tipleri: Model'de Column(String) → migration'da sa.String (UUID DEĞİL).
2. user_id FK tipi: sa.String (users.id VARCHAR!).
3. diary_entry_id (insights, reflections): sa.String (diary_entries.id String).
4. ondelete="CASCADE" → FK tanımında belirt.
5. SQLEnum → sa.String(20) kullan. Migration'da CREATE TYPE DO ... BEGIN EXCEPTION şablonu:
   
   op.execute("""
   DO $$ BEGIN
     CREATE TYPE insight_category AS ENUM ('technical','process','communication');
   EXCEPTION WHEN duplicate_object THEN NULL;
   END $$;
   """)
   
   Sonra kolon: sa.Column("category", sa.String(20), nullable=False, default="technical")
   
6. JSONB, ARRAY(String), Date, DateTime(timezone=True) model'le birebir.
7. Her tabloda indeksler:
   - user_id (varsa)
   - date (diary_entries)
   - confidence (insights)
   - next_review (learning_entries)
   - GIN index: tags array (learning_entries) → postgresql_using="gin"
8. Unique composite: diary_entries (user_id, date) — model'de `unique=True` var.
9. down_revision: ADIM 0'dan gelen mevcut alembic head (briefing'deki 20260406_uni_dept DEĞİL muhtemelen).
10. revision = "20260420_diary".

ÖNEMLI: Migration'ı YAZDIKTAN SONRA UYGULAMA. İnsan review edecek.

Çıktı:
- backend/alembic/versions/20260420_diary_tables.py (yeni dosya)
- backend/_DIARY_MIGRATION_REVIEW_20260420.md (model ↔ migration karşılaştırma tablosu)
```

**İnsan review checklist (10 dk):**

- [ ] PK tipleri String mi? (grep "id.*UUID" → 0 eşleşme olmalı)
- [ ] user_id hep sa.String mi? (grep "user_id.*UUID" → 0 eşleşme)
- [ ] ForeignKey'ler ondelete="CASCADE" mi?
- [ ] down_revision gerçek head'e mi işaret ediyor?
- [ ] 4 enum için DO $$ BEGIN blokları var mı?
- [ ] Index'ler eksiksiz mi (model'deki __table_args__ ile karşılaştır)?
- [ ] downgrade() tabloları DROP ediyor mu (ters sıra: goals önce FK olmayan, sonra diary_entries)?

---

### ADIM 3 — Staging Deploy (30 dk)

**İnsan yapar — Composer 2'ye verme.**

```powershell
# 1. Kopya dosyayı container'a
docker cp C:\Users\husey\kiro2\backend\alembic\versions\20260420_diary_tables.py kiro2-backend:/app/alembic/versions/

# 2. Dry-run (önce SQL'i göster, uygulamadan)
docker exec kiro2-backend alembic upgrade head --sql > C:\Users\husey\kiro2\backend\_diary_migration_preview.sql

# 3. SQL preview'i oku, mantıklı mı?
notepad C:\Users\husey\kiro2\backend\_diary_migration_preview.sql
```

**Karar noktası:** SQL mantıklı mı?
- Yanlış tip görürsen ADIM 2'ye dön.
- Doğruysa devam.

```powershell
# 4. Gerçek upgrade
docker exec kiro2-backend alembic upgrade head

# 5. Hemen doğrula
$env:PGPASSWORD='postgres'
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c "\d diary_entries"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c "\d insights"
```

**Beklenen:** 8 tablo listeleniyor, tipler doğru.

**Rollback** (bir şey ters giderse):
```powershell
docker exec kiro2-backend alembic downgrade -1
```

---

### ADIM 4 — Loader Güncelle (Composer 2 yapabilir)

Briefing'de deniyor: "loader.py'den DISABLED_ROUTERS set'inden sil".

Ama `DISABLED_ROUTERS = {}` zaten boş. Yani diary_api muhtemelen **ROUTER_MAPPING**'de var ve şu anda da yüklenmeye çalışılıyor. Bu durumda:

```
Composer 2 görev:
1. backend/routers/loader.py'ı oku.
2. "api.diary_api" ROUTER_MAPPING'te var mı kontrol et.
3. Yoksa doğru yere ekle (learning kategorisi):
   "api.diary_api": ("learning", "api.diary_api"),
4. Backend'i restart et:
   docker exec kiro2-backend bash -c "find /app -name '*.pyc' -delete"
   docker restart kiro2-backend
5. 30 saniye bekle, logları oku:
   docker logs kiro2-backend --tail 100 | Select-String "diary"

Beklenen log: "Registered router diary_api with prefix: /api/diary"
Hata varsa: "Failed to import api.diary_api: ..." → bana göster.
```

---

### ADIM 5 — Runtime Doğrulama (20 dk)

**İnsan + Composer 2 birlikte.**

**1. Health check:**
```powershell
curl -s http://localhost:8000/health
```

**2. Auth token al:**
```powershell
$body = '{"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}'
$login = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/giris" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
$t = ($login.Content | ConvertFrom-Json).token
```

**3. En basit diary endpoint'i dene:**
```powershell
# Diary api'nin GET endpoint'ini bul
docker exec kiro2-backend grep -n "@router.get" /app/api/diary_api.py | Select-Object -First 5

# Örnek çağrı (yol diary_api.py'ya göre değişir)
$headers = @{Authorization = "Bearer $t"}
Invoke-WebRequest -Uri "http://localhost:8000/api/diary/entries" -Headers $headers -UseBasicParsing
```

**Beklenen sonuç:**
- 200 OK + boş list (`[]`) — tablolar var, endpoint çalışıyor, veri yok
- 401 — auth sorunu (diary_api ayarında değil, ayrı iş)
- 500 — model/schema uyumsuzluğu, ADIM 2'ye dön, migration review et

**4. Create endpoint'i dene (içgörü için):**
```powershell
$body = @{date="2026-04-20"; success_count=5; total_tasks=5; learnings=@("Composer 2 migration pattern'i öğrenildi")} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/diary/entries" -Method POST -Headers $headers -ContentType "application/json" -Body $body -UseBasicParsing
```

**Beklenen:** 201 Created + dönen diary entry ID. Sonra GET tekrar çağır, 1 kayıt dönmeli.

---

### ADIM 6 — Commit + Rapor (15 dk)

**Composer 2 yazabilir, insan onaylar.**

```
Görev: 
1. git status
2. Kapsam kontrol: sadece şu dosyalar değişmiş olmalı:
   - backend/alembic/versions/20260420_diary_tables.py (yeni)
   - backend/routers/loader.py (minör ekleme, eğer gerekiyorsa)
   - backend/alembic/versions/_archive/*.disabled (taşıma)
3. Commit message:
   "feat(diary): enable api.diary_api router with proper schema (VARCHAR FKs)
   
   - Add backend/alembic/versions/20260420_diary_tables.py (8 tables)
   - Archive old .disabled migration (UUID incompatible with users.id VARCHAR)
   - Router already registered in ROUTER_MAPPING, now functional
   
   Pattern follows SESSION_BRIEFING.md 06.04.2026 — users.id VARCHAR rule.
   
   Tested: POST /api/diary/entries → 201, GET → 200 with data."
4. git commit (don't push, insan push edecek)

Ayrıca rapor üret: .cursor/plans/20260420_diary_api_RESULT.md
- Before/after state (ADIM 0 bulguları vs ADIM 5 test sonuçları)
- Bulunan sorunlar ve çözümleri
- Kalan 12 disabled router için çıkarılan dersler (öneri)
```

---

## 6. Composer 2 Bu Pilotta Ne Yapar, Ne Yapmaz

### ✅ Composer 2 için iyi (güçlü tarafı)

| Görev | Neden iyi? |
|---|---|
| ADIM 0 — Terminal sorguları, psql, docker logs | Terminal integration native |
| ADIM 1 — Dosya taşıma mekanik | Mekanik pattern |
| ADIM 2 — Model'den migration üretme | Pattern matching (uni_dept örneği) |
| ADIM 4 — loader.py'da bir satır ekleme | Basit multi-file |
| ADIM 5 — psql + curl testleri | Terminal |
| ADIM 6 — Commit mesajı + rapor | Metin üretimi |

### ❌ Composer 2'ye vermeme (insan karar noktaları)

| Görev | Neden? |
|---|---|
| **ADIM 0 sonucu → aşama seçimi** | Mimari karar, veri kaybı riski |
| **ADIM 2 migration review** | Tip uyumsuzluğu production bug'ı olabilir |
| **ADIM 3 alembic upgrade** | Geri dönüşsüz. İnsan elle yapmalı. |
| **Backup alma** | Felaket kurtarma — güven matrisi |
| **git push** | Bilinçli karar |

---

## 7. Başarı Ölçütleri

Pilot **başarılı** sayılır ancak ve ancak:

- [ ] 8 tablo PostgreSQL'de doğru tipte oluştu (hepsi VARCHAR PK)
- [ ] `alembic current` `20260420_diary` gösteriyor
- [ ] `docker logs kiro2-backend` içinde "Registered router diary_api" var, hata yok
- [ ] `POST /api/diary/entries` endpoint'i 201 dönüyor
- [ ] `GET /api/diary/entries` endpoint'i 200 ve oluşturulan kaydı dönüyor
- [ ] Git commit temiz, sadece planlanan dosyalar

Birini kaçırırsak: Rollback + post-mortem + planı güncelle.

---

## 8. Sonraki Adım (Pilot BAŞARILI olursa)

12 disabled router kaldı — **ama dikkat**: briefing "13 disabled router" dese de `DISABLED_ROUTERS = {}` boş. ADIM 0'da bu çelişki çözüldükten sonra gerçek liste belli olur.

**Kalan router'lar için Composer 2 pattern'i:** Her router bu pilotun 6 adımını izler. `live_session_routes` (11 tablo) en büyük, pilotun ikinci aşaması olabilir. `productive_failure_api` önce `solution_steps` tablosu kontrolü gerekiyor (briefing uyarısı).

**Önerilen sıra (pilot sonrası):**

1. `api.offline_sync_api` + `api.pwa_sync_api` (basit, birlikte)
2. `api.live_session_routes` (büyük ama benzer pattern)
3. `api.productive_failure_api` (solution_steps kontrolü gerekli)
4. ChromaDB bağımlı 4 router (ES migration gerektirir — ayrı plan)
5. Mock/stub router'lar (`api.revolutionary_features`, `api.team_challenges_api`) — önce mock'ları gerçek yap

---

## 9. Referanslar

- **Pattern kaynağı:** `backend/alembic/versions/20260406_uni_dept.py` (24.9 KB, 21 tablo, briefing commit `a51626f`)
- **Model:** `backend/models/diary.py` (578 satır, 8 class, 4 enum)
- **API:** `backend/api/diary_api.py` (51 KB, 11.04.2026)
- **Briefing:** `KIRO2_SESSION_BRIEFING.md` — "MİGRASYON YAZARKEN ÖĞRENİLEN DERSLER" bölümü
- **Audit:** `BACKEND_AUDIT.md` Section 1.3 — "43 disabled routers" (6 Nisan'da 23'e, 13'e, sonra 0'a düşmüş görünüyor — çelişki ADIM 0'da çözülecek)

---

## 10. Uyarılar

- **Staging DB yok.** Kullanıcı development DB kullanıyor (5434 native host). Backup al, backup kontrol et, sonra ilerle.
- **Production data yok** — admin@kiro2.com dışında kullanıcı tabanı sınırlı, ama migration'ı "dev'de denedim, tamam" diye production'a kopyalamak YASAK. Bu DEV'de çalışır demek production'da çalışır anlamına GELMEZ.
- **Diary plugin REQ-1-8** production kritikliği bilinmiyor — özellik seti geniş (emotional tracking, peer comparison) ama kullanılıyor mu belirsiz. Pilot öncesi sor: "Kimler bu özelliği kullanıyor?"
- **Alembic autogenerate YASAK** (briefing altın kuralı). Migration elle yazılmalı.

---

*Plan hazırlandı: 2026-04-20, bu dosya Cursor Plan Mode ile yüklenir (Shift+Tab → "Load Plan" → bu dosyayı seç).*
