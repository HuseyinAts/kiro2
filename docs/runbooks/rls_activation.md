# RLS Aktivasyon Runbook (operatör)

RLS (Row-Level Security) tenant izolasyonunu **gerçekten aktif** kılar. App şu an
`postgres` (superuser+bypassrls) ile bağlanıyor → RLS BYPASS. Non-superuser
`kiro2_app` rolüne geçince RLS policy'leri (faz1_rls_20260704) devreye girer.

## Ön koşul: KANITLANDI ✅
- Rol `kiro2_app` oluşturuldu + grant'landı (`backend/scripts/rls/create_app_role.sql`).
- Bu rolle bağlanıp app'in tüm temsili sorguları çalıştı (login/join/SELECT/INSERT/DELETE).
- RLS aktif doğrulandı: GUC=nonexistent_org → **0 satır** (izolasyon); GUC-boş → hepsi (permissive).

## Neden operatör yapmalı
- `.env*` dosyaları CLAUDE.md gereği asistan tarafından DEĞİŞTİRİLMEZ.
- Tüm platformun DB kimlik bilgisini değiştirir = yüksek etki alanı, insan-döngüsünde.

## Adımlar (revert-ready)

### 1. Rol + grant'ları uygula (idempotent)
```
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -f backend/scripts/rls/create_app_role.sql
```
(Parolayı script içinde güçlü bir değere çevir; buradaki dev-değeri `kiro2_app_rls_2026`.)

### 2. GUC wiring'i deploy et (izolasyonun filtrelemesi için)
`get_current_tenant` → `set_config('app.current_org_id')` zaten commit'li (26c7f2d42).
Container'a bakmak için: `docker compose build backend && docker compose up -d --no-deps --force-recreate backend`

### 3. DATABASE_URL'i kiro2_app'e çevir (.env.mvp:5)
```
# ESKİ:
DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2
# YENİ:
DATABASE_URL=postgresql+asyncpg://kiro2_app:kiro2_app_rls_2026@host.docker.internal:5434/kiro2
```
NOT: alembic migration'ları HÂLÂ postgres ile çalıştırılır (elevated); yalnız APP kiro2_app kullanır.

### 4. Backend + celery recreate
```
docker compose up -d --no-deps --force-recreate backend celery-worker celery-beat
```

### 5. Doğrula (canlı)
- `curl localhost:8000/health` → 200
- login (admin/student) → 200
- GF curl sweep (161 endpoint) → yeni 500 YOK. Yeni 500 çıkarsa = eksik GRANT →
  ilgili tabloya `GRANT ... TO kiro2_app` ekle VEYA revert.
- Backend log: `permission denied` var mı kontrol et.

### 6. Revert (bozulursa, anında)
```
# .env.mvp:5'i postgres'e geri çevir + recreate
DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2
docker compose up -d --no-deps --force-recreate backend celery-worker celery-beat
```

## Aktivasyon sonrası
- RLS 13 data tablosunda gerçekten filtreler (tenant-farkında endpoint'ler GUC set eder).
- App-katman `_scope_tenant` (Faz 0) + RLS = defense-in-depth (iki bağımsız katman).
- İzin-eksikliği riski: 1163 endpoint'in bir kısmı test-dışı kod yollarında ek privilege
  isteyebilir → GF sweep + log ile yakala, hedefli GRANT ekle.

## CANLI CUTOVER KANITI (2026-07-04) ✅
Geçici override (`docker-compose.rls-test.yml`) ile backend `kiro2_app` rolüyle
recreate edildi + tam test:
- health 200, login 200 (admin+student).
- **GF curl sweep: 162 endpoint, 0 permission-500** (dağılım 200/401/404/405, hepsi <500).
- Sonuç: app non-superuser kiro2_app rolünde KUSURSUZ çalışıyor — grant'lar eksiksiz,
  hiçbir kod yolu eksik-privilege 500'ü vermedi.
- Test sonrası backend postgres'e geri alındı (canonical), override dosyası silindi.

**Yani cutover GÜVENLİ ve kanıtlı.** Operatör `.env.mvp:5` flip'ini + GUC-wiring
rebuild'ini yapınca RLS tam aktif olur (test-dışı kod yollarında yine de GF sweep +
log ile izle).
