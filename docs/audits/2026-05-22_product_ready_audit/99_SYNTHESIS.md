# Product-Readiness Synthesis (2026-05-22)

7 paralel `Explore` agent + independent verification by main thread.

## ⛔ Verdict: **NOT PRODUCTION-READY**

3 ana eksen production launch'ı engelliyor:

1. **Veri bütünlüğü kaybolmuş**: MEMORY claims 77K questions / 93.8% rationale; gerçek 167K questions / Phase 7 gold pool 0% rationale.
2. **Mock data canlıda**: 35+ endpoint hâlâ mock döndürüyor (advanced_reports 4, analytics 23, content_management 8).
3. **Login UX kabul edilemez**: 1.3s p50 (target <4ms, 325x sapma).

## P0 Konsolidasyon — 18 production-blocker

| # | Domain | P0 Issue | Evidence | ETA |
|---|---|---|---|---|
| 1 | Data | MEMORY 77,336 → live 167,559 active (+116% drift) | 05.md §verification | doc 1h |
| 2 | Data | auto_judged_high (gold, 15,321 q) **0% Phase 7 rationale** | 05.md §Phase 7 | Phase 7 re-run ~$300, 1d |
| 3 | Backend | 35 mock endpoint canlıda (advanced_reports/analytics/content) | 01.md §1 | feature wiring 5d |
| 4 | Frontend | TS build FAIL — 5 hata, build:fast bypass aktif | 03.md §build | 4h |
| 5 | Integration | Study Rooms API yok — 40+ FE call → 404 | 04.md §1 | 2d (yeni backend modülü) |
| 6 | Production | Login 1.3s p50 (bcrypt cost 12 + pool wait 841ms) | 06.md §6 | 2-7d (bcrypt 10 + pool tuning) |
| 7 | Production | Rate limiter library var, endpoint'e wire DEĞİL | 06.md §10 | 4h |
| 8 | Production | `.env` tracked: teknofest-2025/backend/.env potansiyel leak | 06.md §3 | 1h audit + remove |
| 9 | Algorithm | `_SUBJECT_AREA_MAP` 6 entry — GENEL (1996 q) + TDE (13 q) enum violation | 02.md §enum | 30min |
| 10 | Algorithm | Fire-forget exception swallowed — `algorithm_degraded=False` even if all 4 stages fail | 02.md §race | 2h |
| 11 | Algorithm | Placement fallback uses subject_name not UUID (orphan signal) | 02.md §placement | 1h |
| 12 | Frontend | 3 active file useExamStore (deprecated) import — silent break risk | 03.md §dead-store | 2h refactor |
| 13 | Frontend | 10 raw fetch services bypass apiClient (19 in revolutionaryFeatures alone) | 03.md §fetch | 1d |
| 14 | Frontend | 8 component `<img>` missing alt — WCAG-A violation | 03.md §a11y | 2h |
| 15 | Test | 5 critical middleware module 0% coverage (1,921 LOC: unified_auth + auth_middleware + security_middleware + turkish_exam + auth_security_utils) | 07.md §auth-0% | 2 sprint |
| 16 | Production | Frontend `depends_on backend` missing `service_healthy` → 502 cold start | 06.md §1 | 5min |
| 17 | Production | Migration dry-run banner SADECE docstring — `alembic upgrade head` korumasız | 06.md §4 | 30min |
| 18 | Production | Sentry not integrated (production-required by startup_validator) | 06.md §5 | 2h |

## P1 Yan İhtiyaçlar (post-launch)

- Test coverage 16.64% → 80% hedef (2 ay refactor)
- KVKK/compliance module 0% test
- 20,275 inactive question recovery markers eksik
- Frontend hook count 45 (target 40) — 5 over, scope creep
- 2 duplicate workflow file (quality-gate.yml + quality-gates.yml)
- Image asset backup strategy undefined
- 33 Turkish-only endpoint w/o English (path-naming drift)
- WebSocket routes for Study Rooms eksik (FE polling fallback)
- Knowledge Graph v2 frontend calls — backend v2 yok

## P0'lar arasındaki bağımlılıklar

```
#1 (MEMORY drift) ─┐
                   ├──→ Tüm session özetleri yanlış. Önce düzelt, sonra fix.
#2 (Phase 7 gold) ─┘

#3 (mock endpoints) ──→ #15 (test coverage) bağımlı — gerçek endpoint wiring sonrası test yaz.

#5 (Study Rooms) ──→ #4 (TS build) etkilenmez ama #13 (raw fetch) UI kısmından kalkar.

#6 (login latency) ┐
#7 (rate limit)    ├──→ #18 (Sentry) ile birlikte: auth surface observability paketi.
#8 (.env leak)     ┘

#9 (subject enum) ──→ #10 (fire-forget) bağımlı — birlikte fix, observability beraber.

#16 (depends_on) ──→ 5dk fix. İlk yap.
#17 (migration enforce) ──→ 30dk fix. Hemen sonra.
```

## Önerilen Sprint Planı

**Sprint 0 — Quick wins (1 gün, <8h toplam)**:
- #16 depends_on service_healthy (5min)
- #17 migration code-level dry-run gate (30min)
- #9 subject enum extend MATEMATIK/SOSYAL → GENEL/TDE map (30min)
- #11 placement fallback → raise (1h)
- #7 redis_rate_limiter middleware wire (4h)
- #4 TS build 5 errors fix (varsa, 4h)

**Sprint 1 — Data integrity (3 gün)**:
- #1 MEMORY.md refresh (1h doc)
- #2 Phase 7 gold pool batch retry (1d execute + monitor)
- #15 auth module smoke test landing (2 sprint scope — başla)

**Sprint 2 — Performance + security (1 hafta)**:
- #6 Login bcrypt + pool tune (2-7d)
- #8 .env leak audit + remove (1h)
- #18 Sentry integration (2h)
- #14 WCAG-A alt= sweep (2h)

**Sprint 3 — Mock burndown (1 hafta)**:
- #3 35 mock endpoint wiring (advanced_reports 4 + analytics 23 + content 8)
- #10 fire-forget per-stage degradation flag
- #12 useExamStore consumer refactor

**Sprint 4 — Missing features (2 hafta)**:
- #5 Study Rooms backend implementation (40+ endpoints)
- #13 raw fetch → apiClient migration

## Karpathy "Önce Düşün" Self-Critique

Bu audit'in metodolojik kazanımı: **agent claim'lerini bağımsız doğruladım** (önceki session'da varsayım hatasından öğrendim):

- Agent 2'nin "6 subject missing" iddiası → gerçek 2 subject (GENEL+TDE), 1.2% impact (Agent abartmış)
- Agent 3'ün "5 TS error" iddiası → DOĞRU (commit 9094dd50c iddiam yanlıştı)
- Agent 5'in "167K active, 0% gold rationale" iddiası → DOĞRU (MEMORY severely stale)
- Agent 6'nın "migration chain broken" iddiası → YANLIŞ (alembic 1 head, chain sağlam)

## Karar Noktaları (kullanıcıya sun)

| Karar | Seçenek A | Seçenek B |
|---|---|---|
| MEMORY refresh | Hemen tek commit | Sprint 1 ile birleştir |
| Phase 7 gold rerun | Bu hafta ($300 maliyet kabul) | Beta öncesine ertele |
| TS build fix | Hemen 4h | Sprint 0'a dahil |
| Rate limiter wire | 4h bu hafta | Sprint 2'ye ertele |
| Mock endpoint burndown | Sprint sırası | Beta scope-out (display @WARN gate) |

## Methodology

- 7 paralel `Explore` agent (read-only, ~3-5 dk her biri)
- 4 P0 iddiası bağımsız `psql`/`grep`/`alembic`/`tsc` ile doğrulandı
- Her domain raporu 200-300 satır arası, file:line evidence zorunlu
- Toplam ~900 satır audit dokümanı, 1 sentez (bu dosya)
- Önceki audit `EVIDENCE_BASED_DEEP_REVIEW.md` (May 21) referans, NOT duplicate
- Constraint: READ-ONLY. 0 kod değişikliği.

## Çıktı Dosyaları

```
docs/audits/2026-05-22_product_ready_audit/
├── 01_backend_api.md          (Mock + IDOR + router + middleware)
├── 02_algorithm_pipeline.md   (BKT→IRT→FSRS→ZPD chain)
├── 03_frontend.md             (TS build + dead store + fetch + a11y)
├── 04_integration.md          (FE↔BE contract drift)
├── 05_data_quality.md         (167K active, gold pool 0% rationale)
├── 06_production_readiness.md (login lat, rate limit, secrets, monitor)
├── 07_test_coverage.md        (16.64% real, auth 0%)
└── 99_SYNTHESIS.md            (THIS — cross-cutting + priority matrix)
```
