---
name: code-review
description: PR ve kod kalitesi incelemesi. OWASP kontrolleri, KIRO2 conventions, Boris Cherny standartları. Session 77 analiz — sık hatalar dahil.
---

# Code Review

`/review` slash command'inin alt-altyapısı. Dosya/PR/commit için kapsamlı
review. Security, performance, maintainability, KIRO2-özel kontroller.

## Ne Zaman Yüklenmeli

- `/review` slash command çağrıldığında
- PR açılmadan önce self-review
- Büyük refactor sonrası
- BugBot manual trigger (`bugbot run`) öncesi

## Ön Kontroller (Session 77 dersleri)

77 session analizinden derlenmiş en sık hatalar:

| Kontrol | Açıklama | Öncelik |
|---|---|---|
| Dual Table | `question_bank` (77K) vs boş `questions` | P0 |
| Route Collision | Endpoint doğru dosyada mı? loader.py'de kayıtlı mı? | P0 |
| Pydantic Access | `obj["field"]` yerine `obj.field` | P1 |
| is_active Filter | Soru sorgularında var mı? | P1 |
| Case Convention | UPPERCASE DB vs lowercase enum | P1 |
| Session Type | `get_async_session` (gen) vs `get_db_session_context` (ctx mgr) | P1 |

## OWASP Top 10 Kontrolü

| Kontrol | Açıklama | Öncelik |
|---|---|---|
| SQL Injection | Parameterized query, ORM kullanımı | P0 |
| XSS | Input sanitization, escape output | P0 |
| Auth Bypass | get_current_user Depends + IDOR | P0 |
| Sensitive Data | Hardcoded secret, log leak | P0 |
| CSRF | Token validation, middleware | P1 |
| Injection | Command injection, path traversal | P0 |
| Insecure Deser | Pickle, eval yasak | P1 |
| Outdated Deps | requirements.txt son audit | P2 |
| Weak Logging | Audit trail, sensitive mask | P2 |

## Yasak Pattern'lar (Boris Cherny)

```python
# ❌ REWARD HACKING — test "geçtiğini" göstermek için
assert True
assert 1 == 1
expect(true).toBe(true)

# ❌ STUB KOD
def foo():
    pass  # placeholder
    return None  # stub

# ❌ GEREKÇESIZ COVERAGE IHMAL
# pragma: no cover  (reason olmadan)

# ❌ ECHO "success"
echo Success
print("Success")
```

## KIRO2 Convention Kontrolü

```python
# ✅ DOĞRU import path'leri
from backend.core.config import settings  # lowercase singleton
from frontend.src.store.authStore import useAuthStore  # store/ tekil

# ❌ YANLIŞ
from backend.core.config import Settings  # uppercase class
from frontend.src.stores.authStore import useAuthStore  # stores/ çoğul
```

## Çıktı Formatı

```markdown
## Code Review: <target>

### Özet
- Dosya: X, Satır: Y
- P0: N, P1: M, P2: K

### P0 — Merge Engeli
| Dosya:Satır | Sorun | Öneri |
|---|---|---|

### P1 — Önemli
...

### P2 — İyileştirme
...

### Onay
- Güvenlik: ✅/❌
- Performans: ✅/❌
- Test Coverage: ✅/❌
- Code Style: ✅/❌

### Sonuç
🟢 ONAY / 🟡 KÜÇÜK DÜZELTME / 🔴 MAJOR REVIZYON
```

## Fail-Fast Kuralları

Lint ve test **önce** çalıştırılır:
```bash
cd backend && ruff check . --select=E,F,W,S,B
cd backend && mypy backend/ --no-error-summary
cd backend && pytest tests/unit/ -x --tb=short -q
```

Bunlar fail olursa review bile başlatılmaz — önce kodun temel sağlığı.

## Detaylı Rehber

- `.claude/skills/code-review/SKILL.md` — tam protokol
- `.claude/skills/security-checklist/SKILL.md` — güvenlik derinliği
- `.claude/rules/security.md` — KVKK, JWT, rate limit
- `.cursor/rules/10-backend.mdc` — Dual Table, IDOR, Middleware
- `.cursor/commands/review.md` — CLI workflow
