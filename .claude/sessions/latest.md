## Session Handoff — 2026-08-07 (S205: FAZ 0 + Cursor planları)

**Dal:** feature/self-evolution-optimization · **Son commit:** `d9f6953f6`

### ✅ FAZ 0 kapandı (6 commit)
`1091db7ab` mühür + invaryant testi · `6f3380072` celery DSN + parola maskeleme ·
`eb40cb30d` streak `organization_id` · `d5bf6c339` takipsiz migration ·
`b84bdc503` scratch gitignore · `0a7653911` oturum durumu

`question_bank` **2.304/21 → 187.835/182.519** (aktif 110.858), kapı **25.127**.
Celery zincirinde 3 seri bağlı kusur çözüldü; görev ilk kez çalıştı (`sent: 4`).

### 6 Cursor planı — ölçülmüş durum
| Plan | Durum |
|---|---|
| P4 PWA offline sync | **BİTMİŞ** — 26/26 test |
| P2 CI paralelleştirme | **BİTMİŞ** — pytest.ini + vite `pool:'forks'`; ci.yml değişikliği **gereksiz** (ayarlar config'de, CI zaten okuyor) |
| P6 Teacher Co-Pilot | **TESLİM** (`d9f6953f6`) — mock olarak kayıtlı + etiketli |
| P3 Code-splitting | **YARIM** — granüler chunk'lar oldu, ama `vendor-mui-core` 794 kB + `vendor-prism` 619 kB → planın "sıfır 500+ kB" kriteri tutmuyor |
| P1 Alembic round-trip | **YARIM** — 9 test var ama hepsi statik dosya denetimi; planın istediği gerçek `upgrade→downgrade→upgrade` koşumu YOK. `test_migration_has_downgrade_function` `pass` gövdeli downgrade'i geçiriyor (fa067642bdfe kanıt) |
| P5 Sokratik AI | **BAĞLANMAMIŞ** — service+guard+8 test var, `enhanced_chat.py`'de **0 referans**. Guard ölü kod |

### 🔴 ENGELLEYİCİ — karar bekliyor
`backend/routers/loader.py` ve `frontend/src/App.tsx` commit'siz ve **geniş kapsamlı**:

- **loader.py**: HEAD'de `DISABLED_ROUTERS` **boş**; çalışma ağacında **110 router kapalı**
  ("Over-engineering / Phase 3"). İçinde `api.kvkk_consent_api`, `api.kvkk_privacy_api`,
  `api.kvkk_notice_api` (KVKK yasal uyum), `api.org_billing_api`, `api.audit_api`,
  `api.analytics`, `api.advanced_reports` ve **`api.enhanced_chat`** var.
  → S204'ün "236 frontend yolundan 167'si 404" ve "KVKK 23 ucu kapalı" bulgularının kaynağı bu.
- **App.tsx**: `/login` rotası `KiroLoginRoute` → `ModernLoginPage`'e **geri alınmış**.
  Bu, `05ccfae1f` ile gelen tamamlanmış görev #419'un (A2.2b kademeli-swap) regresyonu.

Bu yüzden P6'nın rota kaydı (`loader.py`) ve `/teacher/copilot` rotası (`App.tsx`)
commit'e **alınmadı** — pano kodu inmiş ama henüz mount edilmemiş durumda.

**P5 de buna bağlı:** guardrail'i `enhanced_chat.py`'ye bağlamak, çalışma ağacında
kapalı olan bir router'a bağlamak demek. Önce loader.py kararı gerekiyor.

### Sonraki adımlar
1. **loader.py kararı** — 110 router kapatma kasıtlı mı? KVKK uçları kapalı kalacak mı?
2. **App.tsx kararı** — `/login` regresyonu geri alınsın mı (KiroLoginRoute'a dönüş)?
3. Karar sonrası: P5 guard bağlama + P6 rota mount
4. P1 gerçek round-trip testi (kolay, bağımsız)
5. P3 `vendor-mui-core` 794 kB (opsiyonel perf)

### Açık kalemler (FAZ 0'dan)
- Celery fix konteynere `docker cp` ile kondu, **imajda yok** — sonraki deploy'da rebuild şart
- `kiro2_app` parola rotasyonu: karar kullanıcıda
- `questions` legacy tablosu silik kalacak (karar verildi)
