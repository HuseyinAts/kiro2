# Audit: API Security Hardening
Tarih: 2026-04-10 | Concern: Auth bypass, rate limit, IDOR, input validation | Agent: 1

## P0 — Hemen Fix

1. **api/auth.py:1315** — reset-password token: store.get() + store.delete() arasında race condition → atomic işlem
2. **api/adhd_task_management_api.py:477** — UpdateTaskRequest IDOR risk → doğrulama gerekli

## P1 — Bu Sprint

3. **api/auth.py:1283** — `/reset-password` endpoint'inde rate limit yok → `_check_rate_limit` ekle
4. **api/auth.py:1391** — PUT `/profile` Dict[str, Any] → mass assignment riski → Pydantic whitelist model
5. **api/admin.py:283** — `zorluk` param string, enum validation yok → Literal type
6. **api/bilge_alp.py:228** — SSE `/chat` endpoint rate limit yok → slowloris riski
7. **api/cache.py:185** — DELETE `/user/{user_id}` admin-only ama path param riski
8. **api/admin.py:75** — Hierarchical admin check yok (admin → super_admin)

## P2 — Teknik Borç

9. **api/api_key_api.py:23** — APIKeyCreateRequest field validation eksik
10. **api/ocr_api.py:210** — batch upload boyut limiti yok
11. **api/admin.py:90,133** — exc_info=True production'da stack trace leak
12. **api/auth.py:1283** — Email enumeration timing attack

## Öncelik

P0 fix önce: auth.py token race condition
P1: reset-password rate limit → profile mass assignment → zorluk enum
