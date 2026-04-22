# Pilot Plan: Autopilot Debt #6 — Round 2 (D-12 fix + kapsam revizyonu + cherry-pick karar)

**Tarih:** 2026-04-22
**Borç ID:** #6 (bkz. `40_OPEN_DEBTS` §Borç #6)
**Kapsam:** Round 1 (Composer 2 tarafından plan dosyası olmadan çalıştırıldı) ADIM 0'da FAIL verdi; bu plan Round 2'nin aksiyon çerçevesidir. Kod değişikliği aksiyon bazında, commit Round 2 sonunda tek toplu.
**Aşama:** A alt-varyantı (auth pattern smoke + değerlendirme).

## Round 1 Özeti (Referans)

Round 1 artifact'leri mevcut:
- `backend/_pilots/20260425_autopilot_debt_6_review_state.md` — ADIM 0 ham çıktısı
- `.cursor/plans/20260425_autopilot_debt_6_review_RESULT.md` — Round 1 FAIL raporu + ADIM 2 ön kararları

**Önemli not**: Round 1 artifact'leri `20260425_` prefix'iyle kayıtlı (Composer 2 o tarihle yazdı), ama gerçek çalışma 22 Nisan. Hüseyin karar: rename mi, olduğu gibi mi? Şu anki plan `20260422_` prefix'iyle.

**Round 1 ADIM 0 FAIL nedenleri** (state.md + RESULT'tan özet):

1. **D-12 deploy drift**: `docker exec kiro2-backend grep 'def require_role' /app/core/auth_dependencies.py` sonucu `def require_role(*roles: str):` gövdesi `return require_authorization(roles=list(roles))` — `AuthorizationDependency` dönüşü yok. Workspace `b5fab34` ile container uyumsuz.
2. **Alembic current FAIL**: `diary_drift_recovery_20260422` revision bulunamadı. 10_BRIEFING'deki `offline_sync_pkg_20260420` iddiası ortamla uyumsuz.
3. **0.e endpoint envanteri uyumsuz**: `Depends(require_role(...))` çoğunlukla `"ADMIN"` için (`/api/v1/analytics/admin/dashboard`, `/api/v1/monitoring/quality/*`). STUDENT/TEACHER/PARENT için ≥3 endpoint **bulunamadı** — pilot kapsamı (40_OPEN_DEBTS §Borç #6: 3 rol) bu pattern ile çelişiyor.
4. **0.f seed user yok**: `kiro2_db` üzerinde `public.users` 0 satır. Backend muhtemelen farklı DB'ye bağlanıyor (`.env.mvp` DSN teyit edilmedi).

**Round 1 ADIM 2 ön kararları** (RESULT'tan — kalan 6 autopilot commit):

| SHA | Ön karar |
|-----|----------|
| `35561c4` | KAPSAM_DIŞI (chroma doc) |
| `9c7361e` | KAPSAM_DIŞI (chroma state links) |
| `9d40ff5` | BRANCH_TE_BIRAK (test + script, autopilot route'lara bağlı) |
| `20610e9` | **CHERRY_PICK_ADAY (kısmi)** — `core/automated_question_generator` re-export master'da eksik, test import'ları kırılıyor; `authenticate_user` override'ları `b5fab34` pattern'iyle uyumlu |
| `59639f4` | KAPSAM_DIŞI (chroma clustering runtime, Aşama D) |
| `c4fbedf` | BRANCH_TE_BIRAK (F1 completion log) |

---

## Round 2 Aksiyon Zinciri (A1–A5)

Her aksiyon atomik. A1 ve A2 birbirinden bağımsız, paralel yapılabilir. A3 bağımsız. A4, A1 sonrası yapılmalı (D-12 fix edilmezse envanter anlamsız). A5 ayrı pilot — bu plan onayını tetikler, uygulama başka pilot.

### A1 — D-12 Deploy Drift Fix (veya Dokümantasyon Fix)

**İki olasılık var** — önce teyit, sonra karar:

**Olasılık A1.a**: Workspace'te `b5fab34` gerçekten `require_role`'u `AuthorizationDependency` dönecek şekilde değiştirmiş, ama container imajı eski kodla yeniden derlenmiş. **D-12 klasik**, deploy eksik.

**Olasılık A1.b**: Workspace kodu da `return require_authorization(roles=list(roles))` içeriyor — yani `b5fab34` aslında sadece `class AuthorizationDependency` ekledi (satır 124'te), `require_role` fonksiyonunun gövdesi geriye uyumluluk için eski kaldı. Bu durumda **D-12 değil**, 10_BRIEFING yanıltıcı dokümantasyon (`§Auth Şeması` "require_role artık AuthorizationDependency döndürüyor" ifadesi yanlış). §1.11 varyantı — canonical statik dosya aldatıcı.

**Önce teyit**:

```powershell
# Workspace kodu (container değil)
Select-String -Path C:\Users\husey\kiro2\backend\core\auth_dependencies.py `
  -Pattern "def require_role" -Context 0,5
# Çıktıdaki fonksiyon gövdesi:
#   - Eğer "return AuthorizationDependency(...)" → Olasılık A1.a, deploy gerek
#   - Eğer "return require_authorization(roles=list(roles))" → Olasılık A1.b, dokümantasyon yanlış
```

**Olasılık A1.a için aksiyon** (Agent mode, PowerShell — Hüseyin çalıştırır):

```powershell
docker cp C:\Users\husey\kiro2\backend\core\auth_dependencies.py `
  kiro2-backend:/app/core/auth_dependencies.py
docker exec kiro2-backend bash -c "find /app -name '*.pyc' -delete"
docker restart kiro2-backend
Start-Sleep -Seconds 5

# Teyit
docker exec kiro2-backend grep -n "def require_role" /app/core/auth_dependencies.py
# YENİ gövde görünmeli. Eski görünürse docker cp başarısız.
```

**Olasılık A1.b için aksiyon** (dokümantasyon düzelt, deploy YOK):
- 10_BRIEFING §Auth Şeması 24 Nisan notu düzelt: "require_role artık AuthorizationDependency döndürüyor" ifadesi kaldırılır veya revize edilir — gerçek: `b5fab34` yeni `AuthorizationDependency` class'ı ekledi, ama `require_role` fonksiyonu backward-compat için eski gövdede, yeni class direkt `Depends(AuthorizationDependency(roles=[...]))` olarak kullanılır.
- Bu durumda `b5fab34`'ün "runtime smoke"u anlamsız — yeni pattern henüz bir endpoint'te kullanılmıyor olabilir. 40_OPEN_DEBTS §Borç #6 kapsamı yeniden tanımlanır.


### A2 — Alembic Drift Teşhisi

```powershell
# Repo'da hangi revision'lar var
Get-ChildItem C:\Users\husey\kiro2\backend\alembic\versions\*.py | Select-Object Name | `
  Where-Object { $_.Name -match "diary_drift|offline_sync|student_review" }

# Container'da alembic durumu
docker exec kiro2-backend alembic current
docker exec kiro2-backend alembic heads
docker exec kiro2-backend alembic history --verbose | Select-Object -First 30
```

**Karar seçenekleri** (sonraki pilot):
- **A2.i** `alembic_version` kolonu manuel `UPDATE` ile doğru head'e hizalama
- **A2.ii** Recovery migration yaz (idempotent, `CREATE TABLE IF NOT EXISTS`)
- **A2.iii** Alembic drift'i başka bir borç olarak ayırıp bu pilot kapsam dışı tut

### A3 — Seed User + DB Bağlantı Teşhisi

Backend gerçek DB'ye bağlanıyor mu teyit:

```powershell
# Env değişkenleri — docker runtime
docker exec kiro2-backend env | Select-String -Pattern "DB_|DATABASE_|POSTGRES"

# .env.mvp DSN
Select-String -Path C:\Users\husey\kiro2\.env.mvp -Pattern "DB_|DATABASE_|POSTGRES"

# Bağlanılan DB'de users sayısı (psql ile, gerçek DB adı .env.mvp'den gelecek)
docker exec kiro2_postgres psql -U postgres -d <gerçek_db> -c "SELECT COUNT(*) FROM users;"
```

Gerçek DB'de 3 rol seed user sorgusu:

```sql
SELECT id, email, role FROM users
WHERE role IN ('STUDENT', 'TEACHER', 'PARENT')
  AND (email LIKE '%test%' OR email LIKE '%seed%' OR email LIKE '%dev%')
ORDER BY role, created_at LIMIT 12;
```

### A4 — 0.e Kapsam Revizyonu (A1 sonrası)

Round 1'de `Depends(require_role(...))` ağırlıkla ADMIN için bulundu. STUDENT/TEACHER/PARENT için auth pattern muhtemelen farklı — alternatif helper'lar var olmalı:

```powershell
# Genişletilmiş grep — tüm olası auth helper pattern'leri
docker exec kiro2-backend bash -c `
  "grep -rn 'require_student\|require_teacher\|require_parent\|AuthorizationDependency(roles' /app --include='*.py' | head -40"

# Runtime role kontrolü yapan endpoint'ler (Depends(authenticate_user) + if role check)
docker exec kiro2-backend bash -c `
  "grep -rn 'current_user.role\|user.role ==' /app --include='*.py' | head -40"
```

Üç olası sonuç:
- **A4.i**: STUDENT/TEACHER/PARENT için ayrı factory (`require_student` gibi) var — matris bu yeni pattern'e göre kurulur, 40_OPEN_DEBTS §Borç #6 kapsamı geçerli
- **A4.ii**: Tek `AuthorizationDependency(roles=[...])` ama argüman olarak STUDENT/TEACHER/PARENT kullanıyor — matris geçerli
- **A4.iii**: Runtime role kontrolü yapan endpoint'ler var ama `Depends(require_role)` kullanmıyor — bu pilot kapsamı dışı (farklı auth mekanizması)

A4 çıktısına göre 40_OPEN_DEBTS §Borç #6 kapsamı güncellenir.

### A5 — Cherry-Pick Pilotu Tetikleme (`20610e9`)

Round 1 ADIM 2 `20610e9`'u `CHERRY_PICK_ADAY (kısmi)` işaretledi. **Uygulama bu plan dışı**, ayrı pilot:

- Plan: `.cursor/plans/20260422_cherry_pick_20610e9.md` (Hüseyin onayı sonrası Claude yazar)
- Kapsam sabit: yalnızca `backend/core/automated_question_generator.py` re-export + `authenticate_user` override'ları içeren test shim'leri
- Kapsam DIŞI: chroma health route eklentileri (ayrı F1 ChromaDB pilotu, Aşama D)

Cherry-pick pilotu Hüseyin'in onayı + A1 çözümü sonrası başlar.

---

## Round 2 Başarı Kriterleri

- A1 çözüldü: ya container deploy edildi (A1.a) ya dokümantasyon düzeltildi (A1.b). state.md'ye sonuç yazıldı.
- A2 teşhisi tamamlandı, alembic drift için karar verildi (fix / ayrı borç).
- A3 çözüldü: backend'in bağlandığı DB tespit edildi, 3 rol seed user bulundu (veya yok diye netleşti).
- A4 tamamlandı: STUDENT/TEACHER/PARENT için auth pattern belgelendi (alternatif factory, role check, veya kapsam dışı).
- A5 cherry-pick pilot planı için **karar alındı** (uygulama ayrı pilot).
- RESULT'a Round 2 bölümü append edildi (Round 1 silinmez, §20_PILOT Round pattern).

## DUR Sinyalleri (Round 2 İçin)

1. A1 teyidinde workspace ve container kodu **aynı** (ikisi de eski gövde) + `class AuthorizationDependency` workspace'te kullanılmıyor → `b5fab34` kapsamı yanlış dokümante edilmiş, Hüseyin'e rapor + 40_OPEN_DEBTS §Borç #6 yeniden değerlendirilmeli.
2. A2'de çift alembic head → DUR, alembic drift kritik, ayrı pilot öncelik.
3. A3'te backend ENV'de DB bilgisi yok veya erişilemiyor → DUR, deployment ayrı sorun.
4. A4'te hiçbir STUDENT/TEACHER/PARENT auth pattern bulunamıyor → 40_OPEN_DEBTS §Borç #6 kapsamı fiilen geçersiz, pilot yeniden tanımlanmalı.
5. Herhangi aksiyon sırasında plan-dışı kod değişikliği — DUR.
6. `git commit` / `git push` / `git cherry-pick` herhangi bir komut — DUR, bu pilot uygulama yapmıyor.

## YASAK Listesi (Round 2)

- `git commit` / `git push` / `git cherry-pick`
- `git checkout` başka branch (master'da kal — D-13 önlem)
- `alembic upgrade` (A2'de karar değil, sadece teşhis)
- Workspace'te kod değişikliği (yalnızca teşhis + dokümantasyon güncelleme)
- Composer 2 ile RESULT yeniden yazma (Round 1 silinmez, Round 2 append)
- ADMIN 4. rol matrisi (40_OPEN_DEBTS §Borç #6 kapsamı 3 rol)
- A5 cherry-pick uygulama (ayrı pilot)

## Referanslar

- **Round 1 artifact'leri**: `.cursor/plans/20260425_autopilot_debt_6_review_RESULT.md`, `backend/_pilots/20260425_autopilot_debt_6_review_state.md`
- **10_BRIEFING**: §Auth Şeması (`/api/v1/auth/giris`, `AuthorizationDependency` iddia), §Kritik Kolon Adları (`users.role` BÜYÜK HARF), §Stack Özeti (port 8000), §Aşama Sınıflandırması (A/B/D/E)
- **40_OPEN_DEBTS** §Borç #6 — 3 rol kapsam, 6 commit listesi (A4 sonrası güncellenir)
- **30_DERSLER**:
  - §1.11 — plan yazarken stack literal'leri ezberden yazma (canlı kanıt bu pilotta)
  - §1.9 — transkript varsayımı
  - §Bölüm 6 Tuzak 9 — Files güncel varsayımı
  - §Bölüm 4 Prensip 6 — repo bizzat oku
- **20_PILOT_PROTOCOL** — §Round N pattern, §Sapma Örüntüleri D-12/D-13
- **AUTOPILOT_LOG.md** §B-02 — auth refactor kaynak
- **CAPABILITY_MATRIX.md** — F1 ChromaDB ayrı pilot

## Composer 2'ye Özel Notlar

1. Bu plan **Round 2 çerçevesi**, Round 1 tekrar edilmez.
2. A1 teyidi öncesi deploy fix YASAK — önce workspace ve container kodu karşılaştır.
3. A3'te token state.md'ye yazılmaz (güvenlik).
4. A5 cherry-pick kararı yazılır, uygulama başka pilot.
5. Bu plan sonunda yeni commit YOK — sadece state.md Round 2 ekleri + RESULT Round 2 append.
