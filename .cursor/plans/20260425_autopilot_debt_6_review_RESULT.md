# RESULT — Autopilot Debt #6 (`b5fab34` auth smoke + 6 commit review)

**Tarih:** 2026-04-22  
**Başlangıç/bitiş SHA:** `b5fab34cd4b95aa45c28657c826e7f0f658bd1e3` (HEAD değişmedi)  
**state.md:** `backend/_pilots/20260425_autopilot_debt_6_review_state.md`

---

## ADIM 0 (özet)

| Kontrol | Sonuç |
|---------|--------|
| Backend / Frontend | UP (200 / 200) |
| HEAD SHA | `b5fab34cd4b95aa45c28657c826e7f0f658bd1e3` ✓ |
| Subject birebir | ✗ (ek: `, shared authenticate_user`) |
| origin/master ↔ HEAD | Boş / boş ✓ |
| **D-12** `require_role` konteyner | **FAIL** — `/app/core/auth_dependencies.py` içinde `return require_authorization(roles=list(roles))`; `AuthorizationDependency` dönüşü yok |
| Alembic `current` | **FAIL** — `diary_drift_recovery_20260422` bulunamadı |
| autopilot 6 commit | 6 subject **mevcut**; log’da **ek 4 commit** daha var |
| 0.e endpoint listesi | `Depends(require_role` → ağırlıkla **ADMIN**; STUDENT/TEACHER/PARENT için grep ile ≥3 uygun endpoint **yok** |
| 0.f 3 rol token | **FAIL** — yalnızca `admin@kiro2.com` login doğrulandı; STUDENT/TEACHER/PARENT için kullanıcı/şifre bulunamadı |

**Round 1:** ADIM 0 **FAIL** → ADIM 1 **çalıştırılmadı** (plan onayı + DUR).

---

## ADIM 1 — Smoke matrisi

**Durum:** N/A (bloke). Tüm senaryolar için PASS tablosu üretilmedi.

| Sebep | Açıklama |
|--------|----------|
| D-12 | Runtime kod `b5fab34` auth refactor ile uyumsuz |
| 0.e | Pilot kapsamı (STUDENT/TEACHER/PARENT) ile uyumlu endpoint envanteri çıkmadı |
| 0.f | Üç rol için Bearer token alınamadı |

---

## ADIM 2 — 6 commit sınıflandırma

| SHA | subject | Karar | Gerekçe |
|-----|---------|--------|---------|
| `35561c4` | docs(pilot): chroma stack RESULT + matrix chroma note | **KAPSAM_DIŞI** | Yalnızca Chroma pilot çıktısı ve matrix; üretim runtime’ı değiştirmez. |
| `9c7361e` | docs(pilot): chroma state links RESULT | **KAPSAM_DIŞI** | Pilot state dosyasında link güncellemesi; kod yok. |
| `9d40ff5` | test(autopilot): admin 501, analytics pdf admin path, chroma health, fix endpoint script token | **BRANCH_TE_BIRAK** | Test ve script odaklı; 501 davranışı ve chroma health testleri autopilot dal bağlamına sıkı bağlı. |
| `20610e9` | fix(tests): admin analytics auth shim, generator import path, chroma health routes | **CHERRY_PICK_ADAY** | `core/automated_question_generator` re-export master’da eksikken çok sayıda test/import kırılır; `authenticate_user` override’ları `b5fab34` sonrası desenle uyum için değerli. Chroma pytest uzantısı Chroma pilotu ile birlikte değerlendirilmeli. |
| `59639f4` | feat(chroma): add clustering health route and complete quartet smoke | **KAPSAM_DIŞI** | Chroma/clustering HTTP yüzeyi ve F1 checklist; aşama D kapsamı. |
| `c4fbedf` | docs(autopilot): record F1 completion and frontend gate status | **BRANCH_TE_BIRAK** | Log/matrix dokümantasyonu; dal geçmişi için yeterli bağlam. |

---

## Sapma listesi (D-8…D-13)

| Kod | Oluştu mu | Not |
|-----|-----------|-----|
| D-12 | **Evet** | Konteyner `require_role` gövdesi workspace `b5fab34` ile uyumsuz. |
| D-13 | Hayır | cherry-pick / autopilot checkout yapılmadı. |
| D-10 | Hayır | state.md dolduruldu. |
| Diğer | — | Plan dışı commit yok; plan dışı dosya: yalnızca bu pilot çıktıları. |

---

## Cherry-pick adayları

1. **`20610e9`** — Öncelik: `backend/core/automated_question_generator.py` re-export; isteğe bağlı olarak analytics test shimleri (`test_api_coverage_batch9.py`, `test_api_coverage_batch13.py`) ayrı değerlendirme. Chroma health test genişlemesi **KAPSAM_DIŞI** ile bağlı; tam commit tek seferde alınacaksa Chroma pilotu ile hizala.

---

## Sonraki aksiyon (Hüseyin)

1. **D-12:** `kiro2-backend` imajını/yerel kodu `b5fab34` ile yeniden derleyip deploy et; `docker exec` ile `def require_role(*roles: str) -> AuthorizationDependency` gövdesinin konteynerde olduğunu doğrula.  
2. **Alembic:** `diary_drift_recovery_20260422` revision dosyası ortamda yoksa DB `alembic_version` ve repo head’i hizala (migration drift pilotu).  
3. **0.f:** Backend’in gerçekten bağlandığı Postgres üzerinde STUDENT/TEACHER/PARENT kullanıcı + şifre teyidi (`.env.mvp` DSN; `kiro2_db` örneğinde `users` boş göründü — muhtemelen farklı DB).  
4. **ADIM 1’i yeniden koş:** 0.e için pilot kapsamına uygun endpoint seti netleştir (gerekirse `40_OPEN_DEBTS` / `10_BRIEFING` ile `Depends(require_role` dışı `require_teacher` / `AuthorizationDependency` kullanımı plan revizyonu).  
5. **Cherry-pick pilotu:** Onay sonrası yalnızca `20610e9` veya parça parça uygulama.

---

## Hijyen kontrolü (pilot sonu)

- Yeni/untracked: `backend/_pilots/20260425_autopilot_debt_6_review_state.md`, `.cursor/plans/20260425_autopilot_debt_6_review_RESULT.md` (+ kullanıcıda plan kopyası varsa).  
- `git commit` / `git push` / `git cherry-pick` **yapılmadı**.

## Round 2 — A1.a Deploy Fix + A2/A3/A4 Teşhis (2026-04-22)

### Özet

Round 1 ADIM 0 FAIL nedenlerinin çözümü:

1. **D-12 giderildi (A1.a)**: Workspace `b5fab34` require_role gövdesi
   (AuthorizationDependency dönüşü) container'a docker cp ile kopyalandı,
   .pyc temizlendi, restart sonrası health 200. Teyit: container'da yeni
   gövde `return AuthorizationDependency(required_roles=normalized or ["admin"])`.
   Detay: backend/_pilots/20260422_autopilot_debt_6_review_state.md §A1.a.

2. **Alembic head (A2)**: Tek head `diary_drift_recovery_20260422`. Parent
   zinciri: diary_drift_recovery_20260422 → offline_sync_pkg_20260420 →
   student_review_drift_001 → osb_access_001. Round 1'deki "revision
   bulunamadı" durumu bu ortamda görülmedi. 10_BRIEFING'deki
   "head=offline_sync_pkg_20260420" iddiası geride kalmış — artık parent,
   yeni head 22 Nisan diary drift recovery.

3. **DB topolojisi netleşti (A3)**: Backend gerçek DSN
   `postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2`
   (native Windows PostgreSQL, port 5434). `kiro2_postgres` Docker
   konteyneri AYRI bir instance — backend ona bağlanmıyor. Round 1'deki
   `kiro2_db` sorgusu yanlış hedefti. 10_BRIEFING §Stack Özeti'ne netlik
   notu gerekli (patch pending).

4. **role enum case (A3 sub-bulgu)**: PostgreSQL `userrole` etiketleri
   BÜYÜK HARF: STUDENT, TEACHER, ADMIN, PARENT. require_role kodu içindeki
   .lower() normalize input hoşgörüsü için — DB enum'u küçük harf saklamıyor.
   10_BRIEFING §Kritik Kolon Adları "BÜYÜK HARF" iddiası doğrulandı.

5. **Seed user tespit (A3)**: 12 STUDENT test kullanıcısı var
   (beta001-beta027@kiro2test.com). TEACHER/PARENT test-email kullanıcıları
   `ORDER BY role LIMIT 12` dilimine girmedi — per-rol ayrı sorgu veya
   LIMIT artırma gerekli. Runtime smoke için TEACHER/PARENT seed eksik.

6. **Auth pattern karma (A4)**: Baskın A4.i + PARENT için A4.iii
   tamamlayıcı. STUDENT/TEACHER için modül-seviyesi factory
   (`require_student`, `require_teacher` — hiyerarşik required_roles
   listeleri küçük harf). PARENT için fabrika YOK, `parent.py` içinde
   `if current_user.role != UserRole.PARENT` runtime check. ADMIN için bol
   `Depends(require_role("ADMIN"))`. `Depends(require_role())` argümansız
   kullanım yok (default "admin" tetiklenmiyor).

### Round 1 Kararlarına Etki

ADIM 2 commit sınıflandırması (Round 1'de yapıldı) DEĞİŞMEDİ:
- 35561c4 KAPSAM_DIŞI
- 9c7361e KAPSAM_DIŞI
- 9d40ff5 BRANCH_TE_BIRAK
- 20610e9 CHERRY_PICK_ADAY (kısmi) — A5 için ayrı pilot
- 59639f4 KAPSAM_DIŞI
- c4fbedf BRANCH_TE_BIRAK

### Pilot Durumu

Round 2 plan §Başarı Kriterleri:
- A1 çözüldü (deploy fix, A1.a)
- A2 teşhis tamamlandı, fix gerektirmedi (tek head sağlıklı)
- A3 kısmi — DB topolojisi + STUDENT seed tespit edildi,
  TEACHER/PARENT seed eksik kaldı (runtime smoke'a engel)
- A4 tamamlandı — pattern belgelendi (karma)
- A5 cherry-pick pilotu için KARAR: 20610e9 ayrı pilot (plan taslağı
  Hüseyin onayı sonrası)

**Pilot KAPANDI — kısmi başarı.** TEACHER/PARENT seed user + runtime
smoke ayrı mini-pilota bırakıldı (40_OPEN_DEBTS §Borç #6 kapsam
revizyonu gerekli).

### Referanslar

- Round 2 ham çıktılar: backend/_pilots/20260422_autopilot_debt_6_review_state.md
- Round 2 plan: .cursor/plans/20260422_autopilot_debt_6_review.md
- Round 1 RESULT yukarıda (bu dosyanın önceki bölümü)
- Round 1 state: backend/_pilots/20260425_autopilot_debt_6_review_state.md

### Pending Aksiyonlar (Hüseyin karar)

1. 10_BRIEFING v16 patch: alembic head + DB topolojisi (host vs container) +
   role enum BÜYÜK HARF teyidi
2. 40_OPEN_DEBTS §Borç #6 kapsam revizyonu (TEACHER/PARENT seed user
   durumu, 3 rol × ≥3 endpoint matrisi runtime smoke için ayrı pilot mu)
3. A5 cherry-pick pilot planı (20610e9)
