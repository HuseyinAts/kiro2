# Audit: DB Query Optimization
Tarih: 2026-04-10 | Concern: N+1, Missing LIMIT, Lazy Load, Over-fetching | Agent sayısı: 1

## P0 — Hemen Fix (Production Timeout Riski)

1. **dag_service.py:102-103** — `fetchall()` on topic_hierarchy without LIMIT — startup full table scan → add `LIMIT 10000`
2. **dag_service.py:120** — `fetchall()` on topic_prerequisites without LIMIT — `LIMIT 50000` ekle
3. **repositories/cursor_pagination.py:293-298** — `COUNT(*)` full table scan her paginated request'te — approximate count veya cache
4. **learning_path_orchestrator.py:546** — StudentAbility loop: relationship varsa N+1 tetikler → `joinedload()` veya explicit field select

## P1 — Bu Sprint (Scalability)

5. **models/exam_db.py:129,185** — `lazy="select"` on ExamQuestion.question + StudentAnswer.question → `lazy="selectin"`
6. **api/enhanced_chat.py:626** — chat_messages user_id filter: composite index ekle `(user_id, created_at DESC)`
7. **api/gamification_api.py:322,426** — GamUserBadge+Badge join iki kez yapılıyor → reuse earned_slugs set
8. **api/learning_path_v2.py:1284** — `scalars().all()` tüm question alanları çekiyor, sadece id/correct_answer/topic_id lazım
9. **dag_service.py:162-175** — `DISTINCT ON` without tie-breaker → `ORDER BY q.primary_topic_id, cs.completed_at DESC, cs.id DESC`
10. **repositories/base.py:96** — `get_all()` unbounded → enforce `limit=1000` default

## P2 — Teknik Borç

11. **api/realms.py:115** — dict construction loop, O(n) memory for large realm counts
12. **app/services/placement_service.py:303** — unnecessary dict mapping overhead
13. **repositories/exam_repository.py:493** — `completed_at` index eksik sinyali
14. **api/admin.py:88** — mapping chain verbose
15. **learning_path_orchestrator.py:575** — implicit SELECT * in raw SQL

## Öncelik Sırası

```
P0 fix önce: dag_service.py (2 fix) → cursor_pagination.py (1) → learning_path_orchestrator.py (1)
P1 sonra: lazy="selectin" → chat index → gamification dedup → learning_path over-fetch
```

## Tahmin

P0 fix: ~30 dk | P1: ~1 saat | Toplam: ~1.5 saat, 6 dosya
