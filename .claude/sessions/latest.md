## Session Handoff — 2026-04-10 14:45
**Branch:** master
**Son commit:** b11fb9a docs(rules): add case-convention.md
**Uncommitted:** temiz (origin güncel)

### Yapilanlar
- `backend/services/mastery_confidence_service.py:199` — LOWER(qb.subject_area) → exact match + subject.upper() (f6187cb)
- `frontend/src/pages/ModernExamStartPage.tsx:91,93` — exam_type/subject toUpperCase() (f6187cb)
- `frontend/src/pages/CozumDuellosuPage.tsx:44,67` — subject state UPPERCASE + API toUpperCase() (f6187cb)
- `backend/app/services/cat_session.py:68` — _normalize_subject() Turkish char helper, DRY (a4ef60f)
- `backend/services/bkt_service.py:316` — _slug_lower = subject_slug.lower() defensive guard (a4ef60f)
- `backend/api/learning_path_v2.py:1267,1293` — q_meta subject REVERTED .lower() (BKT lowercase bekliyor) (a4ef60f)
- `frontend/src/pages/ModernExamStartPage.tsx:94` — difficulty .toUpperCase() kaldırıldı (backend lowercase) (a4ef60f)
- `.claude/rules/case-convention.md` — yeni kural belgesi, 3 katman haritası (b11fb9a)
- Code review: 15 bulguden 13 phantom, 2 gerçek fix (orchestrator+dag Session 132'de zaten fix)

### Fail Eden Testler
- YOK. Router registration PASS. Ruff clean.

### Engelleyiciler
- YOK

### Sonraki Adimlar (maks 5)
1. **Test coverage:** backend ~53% → 80% hedef — case convention test ekle (mastery_confidence, BKT uppercase input)
2. **MVP beta launch** — seed data + docker-compose hazır, E2E 7/7 PASS
3. **Re-OCR recovery** — 1,521-2,511 soru kurtarma potansiyeli
4. **Health check optimization** — 9s timeout → skip veya reduce
5. **Frontend Teacher UI** — teacher_classroom backend hazır, frontend yok

### Kararlar (gelecek session tekrar tartismasin)
- case-convention katman kuralı: DB=UPPERCASE, BKT_slug=lowercase, FSRSCard_enum=lowercase, DAG=UPPERCASE
- dag_service.py:243 defansif .upper() kalıcı guard — kaldırma
- q_meta["subject"] = lowercase (BKT pipeline internal convention)
- difficulty: frontend lowercase gönderir (kolay/orta/zor), backend lowercase bekliyor
- mastery_confidence_service: subject.upper() yapıyor, caller lowercase gönderebilir (defensif)
