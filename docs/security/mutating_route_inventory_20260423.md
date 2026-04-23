# Mutating HTTP route envanteri (F4 — Dalga A)

**Tarih:** 2026-04-23  
**Yöntem:** `backend/api/**/*.py` içinde `@router.post|put|patch|delete` sayımı (`rg`).

## Özet

| Desen | Yaklaşık eşleşme (dosya başına) |
|--------|----------------------------------|
| `@router.post(` | ~280+ (çoklu dosya) |
| `@router.put(` | (post ile birlikte sayıldı) |
| `delete` / `patch` | dağıtılmış |

**Not:** Bu sayım **dekoratör satırı** bazlıdır; alt router birleşimleri ve `app.include_router` önekleri OpenAPI ile birlikte doğrulanmalı.

## En yoğun modüller (mutating endpoint)

Örnek yüksek sayım (tek dosya): `diary_api.py`, `teacher_routes.py`, `live_session_routes.py`, `auth.py`, `multisensory_learning_api.py`, `video_analytics_routes.py`, `student_dashboard.py`, `question_crud_api.py`, `learning_path_v2.py`, `zpd_maarif.py`.

## Dalga B önceliği (öğrenci verisi)

1. `student_id` / `user_id` gövde veya path taşıyan **POST/PUT/PATCH** (öğrenci rolü ile).  
2. `question_crud_api`, `learning_path_v2`, `offline_sync_api`, `pwa_sync_api`, `student_dashboard` (hedef yazma).  
3. Chroma: `content_recommendation`, `semantic_search`, `duplicate_detection` — **IDOR** (plan F4).

## Komut (yenileme)

```bash
cd backend && rg "@router\.(post|put|patch|delete)\(" api --glob "*.py" -c
```

## Sonraki adım

- Dalga B: öğrenci yüzeyi için CSV (path, method, `student_id` param, auth guard).  
- Her düzeltme sonrası ilgili `test_golden_flows` veya birim test.
