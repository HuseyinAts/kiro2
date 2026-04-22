# Pilot state — Autopilot Debt #6 (Auth smoke + 6 commit review)

**Tarih:** 2026-04-22 (çalıştırma; plan dosya adı 20260425)  
**Repo:** `C:\Users\husey\kiro2`  
**HEAD:** `b5fab34cd4b95aa45c28657c826e7f0f658bd1e3`

---

## 0.0 — Özet sağlık (`/status` eşdeğeri; ham)

| Alan | Ham |
|------|-----|
| Backend `GET http://localhost:8000/health` | `200` |
| Frontend `GET http://localhost:3000` | `200` |
| Docker (ilk satırlar) | `kiro2-backend: Up (healthy)`, `kiro2_postgres: Up`, … |
| Branch | `master` |
| `git log -1 --format=%H%n%s` | Aşağıda 0.a |
| `git status --short` | Çok sayıda `M` frontend test + `??` `.cursor/*` vb. (tam liste: çalıştırma anı git status) |
| Production JSONL `d-dataset/eslesmis_sorucevap.jsonl` satır sayısı | `77336` |
| `pytest tests/unit/ --co -q` | `11573 tests collected, 5 errors during collection` (çıkış kodu 1) |

---

## 0.a — HEAD ve origin

```
b5fab34cd4b95aa45c28657c826e7f0f658bd1e3
fix(auth): require_role as AuthorizationDependency, shared authenticate_user
```

- **Beklenen tam SHA:** `b5fab34cd4b95aa45c28657c826e7f0f658bd1e3` → **EŞLEŞİYOR**.
- **Beklenen subject (plan metni birebir):** `fix(auth): require_role as AuthorizationDependency`  
  **Gözlem:** Gerçek subject ek içeriyor: `, shared authenticate_user` → plan **birebir subject** kriteri **SAĞLANMIYOR** (sapma notu).
- `git log origin/master..HEAD --oneline` → **boş** (çıktıda yalnızca `---` ayırıcı görüldü).
- `git log HEAD..origin/master --oneline` → **boş**.

---

## 0.b — Container `kiro2-backend` auth sembolleri (D-12)

`grep -rln 'AuthorizationDependency' /app --include='*.py'`:

```
/app/api/v1/content_recommendation.py
/app/api/v1/duplicate_detection.py
/app/api/sequential_reasoning_api.py
/app/core/auth_dependencies.py
```

`grep -n "class AuthorizationDependency" /app/core/auth_dependencies.py`:

```
124:class AuthorizationDependency:
```

`grep -n "def require_role" /app/core/auth_dependencies.py` (ham):

```
318:def require_role(*roles: str):
319:    """Decorator to require specific roles"""
320:    return require_authorization(roles=list(roles))
```

**D-12:** Workspace `b5fab34` ile karşılaştırıldığında `require_role` konteynerde **`AuthorizationDependency` döndürmüyor**; `require_authorization(roles=list(roles))` dönüyor. Plan DUR sinyali (eski pattern).

`grep -n "def authenticate_user" /app/core/auth_dependencies.py` → **0 satır** (fonksiyon tanımı yok).

`grep -n authenticate_user /app/core/auth_dependencies.py` (ham):

```
223:authenticate_user = AuthenticationDependency(required=True)
227:get_current_user = authenticate_user
445:async def get_profile(current_user: User = Depends(authenticate_user)):
```

**Not:** Tekil `authenticate_user` ataması var; `authenticate_user_from_token` ikililiği yok.

---

## 0.c — Alembic

```
FAILED: Can't locate revision identified by 'diary_drift_recovery_20260422'
```

Beklenen `offline_sync_pkg_20260420` **doğrulanamadı** (komut hata ile çıktı).

---

## 0.d — `origin/autopilot/student-ready-20260421` vs `master`

`git fetch origin autopilot/student-ready-20260421` → OK.

`git log origin/autopilot/student-ready-20260421 --not master --oneline` (ham):

```
c4fbedf docs(autopilot): record F1 completion and frontend gate status
59639f4 feat(chroma): add clustering health route and complete quartet smoke
20610e9 fix(tests): admin analytics auth shim, generator import path, chroma health routes
9d40ff5 test(autopilot): admin 501, analytics pdf admin path, chroma health, fix endpoint script token
9c7361e docs(pilot): chroma state links RESULT
35561c4 docs(pilot): chroma stack RESULT + matrix chroma note
2392983 fix(auth): require_role as AuthorizationDependency, shared authenticate_user
2e9ffc6 docs(autopilot): log push + docker build for B-01
a1b12e9 feat(autopilot): search router category, live_session SQL, chromadb+vector volume
5008ab6 fix(offline_sync): persist package_id in offline_sync_packages with guard (debt #2)
```

Planlı **6 subject** bu listede **hepsi mevcut** (SHA önekleri eşleşiyor).  
**Ek:** Plan metnindeki “yalnızca bu 6 commit” beklentisi ile uyum için **ek 4 commit** daha var → sapma notu (force-push / kapsam değil — Hüseyin kararı).

---

## 0.e — `b5fab34` stat + `Depends(require_role` envanter + endpoint listesi

`git show --stat b5fab34` (özet): `AUTOPILOT_LOG.md`, `CAPABILITY_MATRIX.md`, `backend/core/auth_dependencies.py`, `backend/tests/fast/test_api_agents.py`, `backend/tests/fast/test_api_monitoring.py`.

`docker exec` ile `/app` altında `Depends(require_role` grep: **yalnızca `ADMIN`** (ve `learning_path_auth` docstring eşleşmesi dışında) kullanımlar; **STUDENT / TEACHER / PARENT** ile etiketlenecek `Depends(require_role(...))` **bulunamadı**.

Sabit endpoint listesi (plan formatı, roller `require_role("ADMIN")` → **[role=ADMIN]**; pilot metni ADMIN hariç tuttuğu için **matris kapsamı ile çelişki**):

| METHOD | path | role | source |
|--------|------|------|--------|
| GET | /api/v1/analytics/admin/dashboard | ADMIN | `/app/api/analytics.py:282` |
| GET | /api/v1/monitoring/quality/stats | ADMIN | `/app/api/production_monitoring.py:28` |
| GET | /api/v1/monitoring/quality/... | ADMIN | (dosyada çoklu satır; tam envanter grep çıktısında) |

**0.e onay maddesi “≥3 endpoint, STUDENT/TEACHER/PARENT”:** Bu grep ile **karşılanmıyor**.

---

## 0.f — Login (3 rol)

- **Postgres:** `docker exec kiro2_postgres psql -U postgres -d kiro2_db` — `public.users` **0 satır**; `STUDENT`/`TEACHER`/`PARENT` seed sorgusu **boş**. (Plan SQL `kiro2` DB adı; bu host’ta `kiro2` DB yok, `kiro2_db` kullanıldı.)
- **`POST http://localhost:8000/api/v1/auth/giris`** — `admin@kiro2.com` / `Kiro2Beta2026@x` → **200**, `access_token` alındı.
- **STUDENT / TEACHER / PARENT:** Bu ortamda **bilinen şifre + satır içeren kullanıcı bulunamadı** → plan 0.f **tam PASS değil** (tokenlar state’e yazılmadı).

---

## ADIM 0 onay özeti (pilot kriterleri)

| Kriter | Sonuç |
|--------|--------|
| 0.0 | OK (servisler ayakta) |
| 0.a SHA + origin | SHA OK; subject plan metni ile **birebir değil** |
| 0.b | **FAIL (D-12)** — `require_role` konteynerde eski gövde |
| 0.c | **FAIL** — `diary_drift_recovery_20260422` revision eksik |
| 0.d | 6 commit var; **ek commit’ler** var |
| 0.e | **FAIL** — STUDENT/TEACHER/PARENT `Depends(require_role` yok |
| 0.f | **FAIL** — 3 rol tokenı alınamadı (yalnızca admin doğrulandı) |

**ADIM 1:** Plan gereği ADIM 0 onayı şart; yukarıdaki nedenlerle **bloke** (ayrıca D-12 ile runtime smoke anlamsız).

---

## ADIM 2 — `git show` ham özeti + ön karar (taslak)

| SHA | Ön karar | Gerekçe (2–3 satır) |
|-----|----------|---------------------|
| 35561c4 | KAPSAM_DIŞI | Chroma pilot RESULT + matrix notu; runtime kod yok. |
| 9c7361e | KAPSAM_DIŞI | Tek satır pilot state linki; dokümantasyon. |
| 9d40ff5 | BRANCH_TE_BIRAK | Fast test + script + log; admin 501 beklentisi ve chroma health testleri branch bağlamına yakın. |
| 20610e9 | CHERRY_PICK_ADAY (kısmi) | `core/automated_question_generator` re-export master’da yokken test importları kırılır; auth shim `authenticate_user` ile uyumlu. Chroma health genişlemesi Chroma kapsamında. |
| 59639f4 | KAPSAM_DIŞI | `clustering_api` health + F1/Chroma quartet; ayrı pilot. |
| c4fbedf | BRANCH_TE_BIRAK | AUTOPILOT_LOG + matrix; F1/F5 durum dokümantasyonu. |

*(Final karar: `.cursor/plans/20260425_autopilot_debt_6_review_RESULT.md`.)*

---

## Hüseyin onayı

ADIM 0 bu dosyadaki FAIL/DUR seti ile **onay beklememeli** — plan DUR sinyalleri tetiklendi. Sonraki adım: konteyner imajını `b5fab34` ile hizalama, Alembic revision drift çözümü, seed kullanıcılar veya DB erişim teyidi, sonra ADIM 1.
