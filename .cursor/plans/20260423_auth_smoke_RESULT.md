# Auth smoke sonucu — `require_role` → `AuthorizationDependency` (ref: `b5fab34`)

**Tarih:** 2026-04-23  
**Ortam:** Yerel API `http://127.0.0.1:8000`, PostgreSQL `localhost:5434` / `kiro2`  
**Referans kullanıcılar:** `test@kiro2.com` (STUDENT), `ogretmen@kiro2.com` (TEACHER), `veli@kiro2.com` (PARENT) — şifre seed/e2e ile uyumlu `Kiro2Beta2026@x`

---

## 1. `backend/auth/` ve `require_role`

- Repoda **`backend/auth/`** dizini yok; kimlik ve yetki birleşik olarak **`backend/core/auth_dependencies.py`** içinde.
- **`require_role(*roles)`** artık doğrudan **`AuthorizationDependency`** döndürüyor: roller **küçük harfe normalize** edilir (`"ADMIN"` → `"admin"`), ardından RBAC `check_permission` ile doğrulanıyor.
- **`AuthorizationDependency`**: `Depends(authenticate_user)` ile JWT kullanıcıyı alır, `AuthorizationContext` oluşturup `rbac_manager.check_permission` sonucuna göre **403** veya kullanıcıyı geçirir.

---

## 2. `backend/routers/` ve rol örnekleri

- **`backend/routers/`** yalnızca dinamik yükleyici (`loader.py`, `router_registry`); route gövdeleri **`backend/api/*.py`** altında.
- **`Depends(require_role("ADMIN"))`** örneği: `backend/api/production_monitoring.py` → `GET /api/v1/monitoring/quality/stats` (ve dosyadaki diğer `/stats` varyantları).
- **STUDENT / TEACHER / PARENT** için prod kodda çok sayıda yer **`require_role` yerine** `UserRole`/`KullaniciRolu` ile **manuel** kontrol kullanıyor (ör. `backend/api/parent.py`, `backend/api/ogretmen.py`, `backend/api/veli.py`). Smoke bu yüzden hem **AuthorizationDependency (ADMIN)** hem de **manuel rol korumalı** uçları içerir.

---

## 3. PostgreSQL (salt okunur)

Sorgu:

```sql
SELECT id, email, role FROM users
WHERE role IN ('STUDENT','TEACHER','PARENT')
ORDER BY role LIMIT 6;
```

**Özet sayım:** STUDENT 61, TEACHER 1, PARENT 2 — **her rolden en az bir kullanıcı mevcut** (DUR koşulu sağlandı).

---

## 4. `POST /api/v1/auth/giris`

| Rol      | HTTP |
|----------|------|
| STUDENT  | 200  |
| TEACHER  | 200  |
| PARENT   | 200  |

---

## 5–6. Token ile korumalı uçlar (matris)

### A) `require_role` / `AuthorizationDependency` (ADMIN)

| Endpoint | Beklenti (STUDENT/TEACHER/PARENT) |
|----------|-----------------------------------|
| `GET /api/v1/monitoring/quality/stats` | **403** (ADMIN değil) |

**Gözlem:** Üç rol için **403**; gövde örneği: `insufficient_permissions`, `"User has no active roles"` (RBAC mesajı). Bu, `AuthorizationDependency` + `require_role("ADMIN")` yolunun runtime’da çalıştığını doğrular.

### B) Manuel rol koruması — öğretmen paneli (DEPRECATED)

| Token → | `GET /api/v1/ogretmen/dashboard` |
|---------|-------------------------------------|
| STUDENT | 403 |
| TEACHER | **400** |
| PARENT  | 403 |

**Not:** TEACHER için **403 değil 400** — `ogretmen_yetkisi_kontrol` geçildikten sonra servis katmanı `ValueError` → genel 400 (`"Islem basarisiz. Lutfen tekrar deneyin."`). Yani **rol kapısı açıldı**, “mutlu yol” 200 değil.

### C) Manuel rol koruması — veli (`parent`)

| Token → | `GET /api/v1/parent/children` |
|---------|-------------------------------|
| STUDENT | 403 |
| TEACHER | 403 |
| PARENT  | 200 |

### D) Genel kimlik (rol ayrımı yok — referans)

| Token → | `GET /api/v1/auth/profil` |
|---------|----------------------------|
| STUDENT / TEACHER / PARENT | 200 |

### E) Öğrenci-onay (sadece STUDENT rolü; diğerleri 403)

| Token → | `PUT /api/v1/parent/approval/1?approved=false` |
|---------|-----------------------------------------------|
| STUDENT | **400** (onay bekleyen ilişki yok / iş kuralı) |
| TEACHER | 403 |
| PARENT  | 403 |

**Not:** STUDENT için **403 değil 400** — rol kontrolü geçiliyor; `ValueError` ile 400 dönüyor. Veli/öğretmen için **403** beklenen şekilde.

### F) Öğrenme stili `GET` (bu smoke için matrise alınmadı)

`GET /api/v1/learning-style/detect/{student_id}` içinde `verify_student_access` hata verse bile üst seviye `except Exception` **403’ü de yakalayıp** varsayılan profille **200** dönebiliyor; bu yüzden 403 doğrulaması için kullanılmadı.

---

## 7. Özet (b5fab34 auth davranışı)

- **`require_role` → `AuthorizationDependency`**: `GET /api/v1/monitoring/quality/stats` üzerinde **ADMIN olmayan tüm roller 403** — smoke **geçti**.
- **STUDENT/TEACHER/PARENT birbirinden ayrılan manuel uçlar:** `parent/children` (veli 200, diğerleri 403) ve `ogretmen/dashboard` (öğretmen dışı 403) **beklentiyle uyumlu**; öğretmen dashboard’da TEACHER **200 yerine 400** (iş kuralı / deprecated servis).
- **Giriş:** Üç rol için `POST /api/v1/auth/giris` **200**.

---

## Komut / bağlantı notu

- DB sorgusu: **psycopg** ile `localhost:5434` (repo `db-query` skill ile aynı varsayılan; ortamda `psql` yoktu).
- HTTP: `httpx` ile yerel çalışan API’ye istek (önce `GET /docs` → 200 ile servis doğrulandı).
