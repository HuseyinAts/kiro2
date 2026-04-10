# Path Naming Convention — Backend ↔ Frontend Drift Control

Session 135'de eklendi. Kök neden: aynı özellik için hem Türkçe (`/ogretmen`,
`/veli`, `/sinav`) hem İngilizce (`/teacher`, `/parent`, `/exam`) endpoint
implementasyonları var. Frontend hangisini çağıracağını tahmin etmek zorunda
kalıyor, drift sessizce 404 üretiyor.

## Kural

Yeni endpoint eklerken:

1. **İngilizce path segment kullan.** Route prefix + resource adı İngilizce.
   - ✅ `/api/v1/teacher/classes`
   - ❌ `/api/v1/ogretmen/siniflar`

2. **İki istisna:**
   - **Ürün adları** (`bilge-alp`, `soru-meydani`, `oba-seferleri`, `usta-cirak`,
     `cozum-duellosu`, `zpd-maarif`) — bunlar kullanıcıya görünen marka adları,
     çevrilmezler. `.claude/rules/path-naming.md` TR_ALLOWLIST'e ekle.
   - **Mevzuat terimleri** (`kvkk`) — resmi kısaltmalar.

3. **Duplicate implementasyon yasak.** Aynı özellik için `/ogretmen/*` VE
   `/teacher/*` koexist etmemeli. Biri legacy, biri canonical.
   - Yeni feature → sadece canonical (İngilizce)
   - Mevcut duplicate → audit ile tespit, plan ile legacy sil

4. **Frontend fetch path'leri backend OpenAPI'de mevcut olmalı.**
   - Audit script drift'i yakalar, CI gate reject eder

## Audit Aracı

```bash
# Yerel kontrol (backend çalışır olmalı)
python backend/scripts/audit_path_drift.py

# Rapor yaz
python backend/scripts/audit_path_drift.py --write

# CI mode — drift varsa exit 1
python backend/scripts/audit_path_drift.py --fail

# Custom backend URL
python backend/scripts/audit_path_drift.py --url http://staging:8000/openapi.json
```

## Audit Çıktısı — 3 Kategori

| Kategori | Anlam | Aksiyon |
|----------|-------|---------|
| **TR/EN Duplicate** | `/ogretmen/X` VE `/teacher/X` ikisi de mevcut | Legacy olanı sil |
| **Turkish-Only** | Sadece `/veli/cocuklar` var, İngilizce yok | İngilizce canonical ekle, legacy'yi deprecate et |
| **Frontend 404 Risk** | Frontend fetch path backend'de yok | Backend endpoint eksik veya frontend typo |

## Bilinen Backlog (10 Nis 2026, Session 135)

- **22 Turkish-only path**: `/api/v1/ogretmen/*`, `/api/v1/veli/*`, `/api/v1/zpd-maarif/*`,
  `/api/v1/student-dashboard/{profil,bildirimler,istatistikler,sinav-gecmisi}`,
  `/api/v1/auth/{profil,ogrenci-profil,ogretmen-profil,veli-profil}`.
  Bunların İngilizce karşılıkları `/api/v1/teacher/*`, `/api/v1/parent/*`,
  `/api/v1/users/*` altında kısmen var ama farklı operasyonlar implement ediyor.
- **~40 `/api/v1/study-rooms/*`** frontend 404: Backend modülü hiç yok,
  frontend VideoConference/Whiteboard/ChatInterface componentleri kitle halinde
  eksik endpoint çağırıyor. Bu bir missing-feature, naming drift değil.
- **Diğer frontend 404'lar**: `.migration-backup/` klasöründeki .bak dosyalar
  (beklenen), `/api/v1/parsed-questions/*` (router kayıtlı mı kontrol et).

## CI Gate

Pull request'te drift count artarsa PR merge'lenmemeli. Bu kural Adım 6'nın
(Golden Flow CI gate) bir parçası olarak `.github/workflows/` altına eklenir.

## İlişkili Kurallar

- `.claude/rules/case-convention.md` — Endpoint Gate (subject identifier normalization)
- `.claude/rules/debugging-first.md` — Root cause analysis gate

---

*Oluşturulma: 2026-04-10 Session 135*
