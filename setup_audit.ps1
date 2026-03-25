# KIRO2 Fullstack Audit - Tam Otonom (v4 Final)
# PowerShell: cd C:\Users\husey\kiro2 && .\setup_audit.ps1

$projectRoot = "C:\Users\husey\kiro2"

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8)
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " KIRO2 Tam Otonom Audit (v4 Final)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path "$projectRoot\.claude\commands" | Out-Null
New-Item -ItemType Directory -Force -Path "$projectRoot\docs\audit" | Out-Null

$content = @'
---
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
description: KIRO2 tam otonom fullstack audit — tek komut, tum fazlar, otomatik fix
---

Sen KIRO2 fullstack audit uzmanisin. TAMAMEN OTONOM calis.
Kullaniciya ASLA soru sorma, onay bekleme, her karari kendin al.

# RESUME — ONCE BUNU KONTROL ET
```
for f in 00_kontrat_haritasi 01_guvenlik_tarama 02_entegrasyon_raporu 03_veri_katmani_raporu 04_deadcode_raporu 05_guvenlik_fix 06_entegrasyon_fix 07_veri_fix AUDIT_FINAL_RAPOR; do
  if [ -f "docs/audit/${f}.md" ] && grep -q "STATUS: TAMAM" "docs/audit/${f}.md" 2>/dev/null; then
    echo "${f}: TAMAM"
  else
    echo "${f}: YAPILACAK"
  fi
done
```
TAMAM olanlari ATLA. Ilk YAPILACAK'tan devam et. Hepsi TAMAM ise "Audit tamamlanmis" de, dur.

# KURALLAR
- Kullaniciya ASLA soru sorma.
- Her rapor dosyasinin SONUNA `## STATUS: TAMAM` yaz (resume icin).
- KRITIK/YUKSEK bulgulari fix et. ORTA/DUSUK sadece raporla.
- TDD: test yaz (RED) → fix uygula (GREEN) → commit.
- ASLA full project root'ta grep calistirma. Sadece backend/app/ veya frontend/src/.
- Buyuk grep ciktilari > /tmp/dosya.txt yaz, sonra oku.
- CWD KURALI: `cd` komutlarini `(cd backend && ...)` subshell icinde calistir. Ana CWD proje root'u kalmali.
- git add HEDEFLI: `git add docs/audit/ backend/ frontend/` — ASLA `git add -A` kullanma.

# PROJE BILGILERI
- Backend: FastAPI, backend/app/api/ (50+ router), backend/app/models/, backend/app/services/
- Frontend: React 18 + TypeScript, frontend/src/
- DB: PostgreSQL port 5434, container turkiye_sinav_postgres
- Auth: JWT + OAuth2 → Depends(get_current_user), Depends(get_current_admin)
- Middleware: Log→Trace→Sentry→QueryMon→Auth→CSRF→Security→RateLimit→DDoS→Perf→Timeout
- KRITIK: questions tablosu BOS, question_bank 77K kayit.

---

# ============================
# PRE-FLIGHT
# ============================
```
curl -s http://localhost:8000/health -w "\n%{http_code}" 2>/dev/null || echo "BACKEND KAPALI"
docker ps --format "{{.Names}} {{.Status}}" 2>/dev/null | grep -i postgres || echo "DB KAPALI"
(cd backend && python -m pytest -x --tb=line -q 2>&1 | tail -5)
git status --short
```
Basarisiz olsa bile devam et — sorunlari raporla.
Branch:
```
git checkout -b audit/fullstack-$(date +%Y%m%d-%H%M) 2>/dev/null || true
```

---

# ============================
# FAZ 0: KONTRAT HARITASI
# ============================
# Cikti: docs/audit/00_kontrat_haritasi.md

Adim 1 — Backend route'lari:
```
grep -rn "@router\.\(get\|post\|put\|delete\|patch\)\|@app\.\(get\|post\|put\|delete\)" backend/app/api/ --include="*.py" > /tmp/backend_routes.txt
wc -l /tmp/backend_routes.txt
```
/tmp/backend_routes.txt oku. Her route: dosya, satir, method, path, auth guard var mi.

Adim 2 — Frontend API cagrilari:
```
grep -rn "fetch(\|axios\.\|apiClient\.\|api\.\(get\|post\|put\|delete\)\|useQuery(\|useMutation(\|useSWR(" frontend/src/ --include="*.ts" --include="*.tsx" > /tmp/frontend_calls.txt 2>/dev/null
wc -l /tmp/frontend_calls.txt
```

Adim 3 — Eslestirme tablosu olustur. Mismatch'leri bul:
- Frontend var / backend yok
- Backend var / frontend yok
- URL farkli (singular/plural, /api/v1 prefix)
- Method farkli
- localhost:8000 hardcode

Raporu docs/audit/00_kontrat_haritasi.md'ye yaz. Sona `## STATUS: TAMAM` ekle.
```
git add docs/audit/00_kontrat_haritasi.md && git commit -m "audit(faz0): kontrat haritasi"
```

---

# ============================
# FAZ 1a: GUVENLIK TARAMA (sadece tarama, fix yok)
# ============================
# Cikti: docs/audit/01_guvenlik_tarama.md

Adim 1 — Auth kontrolu ENDPOINT BAZINDA (dosya bazinda degil!):
```
grep -rn "@router\.\(get\|post\|put\|delete\|patch\)" backend/app/api/ --include="*.py" > /tmp/all_endpoints.txt
```
/tmp/all_endpoints.txt oku. HER endpoint icin o fonksiyonun icinde veya parametrelerinde
Depends(get_current_user) veya Depends(get_current_admin) var mi kontrol et.
YOKSA → auth eksik endpoint olarak raporla.
Public olmasi gerekenler (BEYAZ LISTE): health, login, register, public-questions, docs, openapi.json

Adim 2 — Credentials eksik:
```
grep -rn "fetch(\|axios\.\|apiClient\." frontend/src/ --include="*.ts" --include="*.tsx" | grep -v "credentials\|withCredentials" > /tmp/no_creds.txt
wc -l /tmp/no_creds.txt
```

Adim 3 — IDOR:
```
grep -rn "user_id.*Path\|student_id.*Path\|Path.*user_id\|Path.*student_id" backend/app/api/ --include="*.py"
```

Adim 4 — Admin-only:
```
grep -rn "cache_clear\|cache_invalidate\|batch_\|bulk_delete\|purge\|reset_all\|import_data\|export_all\|seed_\|migrate\|truncate" backend/app/api/ --include="*.py"
```

Raporu docs/audit/01_guvenlik_tarama.md'ye yaz.
Her bulgu: | # | Dosya:Satir | Tur (AUTH/IDOR/CRED/ADMIN) | Oncelik | Detay |
Sona `## STATUS: TAMAM` ekle.
```
git add docs/audit/ && git commit -m "audit(faz1a): guvenlik tarama raporu"
```

---

# ============================
# FAZ 1b: GUVENLIK FIX (sadece KRITIK ve YUKSEK)
# ============================
# Cikti: docs/audit/05_guvenlik_fix.md

docs/audit/01_guvenlik_tarama.md oku. KRITIK ve YUKSEK bulgulari sec.

Her fix icin TDD:

Auth eksik fix:
1. Endpoint dosyasini oku
2. Test yaz: endpoint'e token'siz istek → 401 beklenmeli
3. (cd backend && python -m pytest tests/test_[dosya].py -x --tb=short -q)
4. Endpoint fonksiyonuna `current_user: User = Depends(get_current_user)` ekle
5. Testi tekrar calistir → 401 donmeli
6. git add docs/audit/ backend/ && git commit -m "fix(security): auth guard [endpoint]"

IDOR fix:
1. user_id parametresini kaldir, current_user.id kullan
2. Test + commit

Credentials fix:
1. Frontend axios instance veya fetch wrapper dosyasini bul ve oku
2. withCredentials: true ekle (tek yerden fix = tum cagrilar duzulur)
3. git add docs/audit/ frontend/ && git commit -m "fix(security): credentials"

Fix raporu docs/audit/05_guvenlik_fix.md'ye yaz.
Her fix: | # | Bulgu | Fix | Test | Commit |
Sona `## STATUS: TAMAM` ekle.
```
git add docs/audit/ && git commit -m "audit(faz1b): guvenlik fix tamamlandi"
```

---

# ============================
# FAZ 2: ENTEGRASYON TARAMA + FIX
# ============================
# Cikti: docs/audit/02_entegrasyon_raporu.md + docs/audit/06_entegrasyon_fix.md

Adim 1 — Route ordering:
```
grep -rn "/{" backend/app/api/ --include="*.py" > /tmp/wildcard_routes.txt
```
Her wildcard'in ayni dosyada ALTINDA static route var mi kontrol et.

Adim 2 — URL mismatch: docs/audit/00_kontrat_haritasi.md'den mismatch'leri oku.

Adim 3 — Proxy/Middleware:
```
find . -maxdepth 3 -name "nginx*" -o -name "docker-compose*" -o -name "Caddyfile" 2>/dev/null
grep -rn "add_middleware\|Middleware" backend/app/core/ backend/app/main.py --include="*.py" 2>/dev/null
```

Raporu docs/audit/02_entegrasyon_raporu.md'ye yaz. `## STATUS: TAMAM`

Fix'ler:
- Static route'lari wildcard'dan once tasi
- Frontend URL'leri backend'e uyumla
Fix raporu docs/audit/06_entegrasyon_fix.md. `## STATUS: TAMAM`
```
git add docs/audit/ backend/ frontend/ && git commit -m "audit(faz2): entegrasyon rapor + fix"
```

---

# ============================
# FAZ 3: VERI KATMANI TARAMA + FIX
# ============================
# Cikti: docs/audit/03_veri_katmani_raporu.md + docs/audit/07_veri_fix.md

Adim 0 — Alembic drift:
```
(cd backend && python -m alembic check 2>&1) || echo "DRIFT VAR"
```

Adim 1 — Yanlis tablo:
```
grep -rn "\"questions\"" backend/app/ --include="*.py" | grep -v "question_bank\|__pycache__" > /tmp/wrong_table.txt
```

Adim 2 — is_active eksik:
```
grep -rn "\.filter\|\.where\|select(" backend/app/ --include="*.py" | grep -v "is_active\|__pycache__" > /tmp/no_isactive.txt
```

Adim 3 — N+1:
```
grep -rn "for .* in .*:" backend/app/api/ backend/app/services/ --include="*.py" -A5 | grep -E "await.*\.(get|filter|execute|fetch)|session\." > /tmp/n1.txt
```

Adim 4 — Index eksik FK:
```
grep -rn "ForeignKey" backend/app/models/ --include="*.py" | grep -v "index=True" > /tmp/no_idx.txt
```

Adim 5 — Case convention:
```
grep -rn "class.*Enum\|Enum(" backend/app/ --include="*.py" | head -20
```

Raporu docs/audit/03_veri_katmani_raporu.md'ye yaz. `## STATUS: TAMAM`

Fix'ler (TDD ile):
- questions → question_bank
- is_active filtresi ekle
- joinedload/selectinload ekle
Fix raporu docs/audit/07_veri_fix.md. `## STATUS: TAMAM`
```
git add docs/audit/ backend/ && git commit -m "audit(faz3): veri katmani rapor + fix"
```

---

# ============================
# FAZ 4: DEAD CODE (sadece tarama, silme yok)
# ============================
# Cikti: docs/audit/04_deadcode_raporu.md

Kontrat haritasindan:
- Frontend var / backend yok → stub gerekli mi?
- Backend var / frontend yok → dead code mu?
```
grep -rn "^def \|^async def " backend/app/api/ --include="*.py" > /tmp/all_funcs.txt
```
Raporu docs/audit/04_deadcode_raporu.md'ye yaz. Dead code SILME, sadece raporla.
`## STATUS: TAMAM`
```
git add docs/audit/ && git commit -m "audit(faz4): dead code raporu"
```

---

# ============================
# FINAL RAPOR
# ============================
# Cikti: docs/audit/AUDIT_FINAL_RAPOR.md

Tum raporlari oku (00 ile 07 arasi).

Birlestir — tek tablo:
| # | Bulgu | Katman | Oncelik | Durum (FIXED/ACIK) | Dosya |

Istatistikler:
- Toplam bulgu / fix edilen / acik kalan
- Faz bazinda dagilim
- Sonraki audit icin oneriler
`## STATUS: TAMAM`

# SON DOGRULAMA
```
(cd backend && python -m pytest -x --tb=short -q 2>&1 | tail -10)
```
Fail varsa FIX ET ve commit at.
Basarili ise:
```
git add docs/audit/ && git commit -m "audit: final rapor tamamlandi"
git log --oneline -20
```

Kullaniciya tek paragraf ozet ver: kac bulgu, kac fix, kac acik, ne kadar surdu.

## TAMAMLANDI.
'@
Write-Utf8NoBom "$projectRoot\.claude\commands\audit-full.md" $content
Write-Host "  OK - audit-full.md" -ForegroundColor Green

# .gitignore
$gp = "$projectRoot\.gitignore"
if (Test-Path $gp) {
    $gc = Get-Content $gp -Raw
    if ($gc -notmatch "CLAUDE\.local\.md") {
        Add-Content -Path $gp -Value "`n# Claude Code`nCLAUDE.local.md`n.claude/settings.local.json"
    }
}

Write-Host "`n TAMAMLANDI. Claude Code'da: /audit-full" -ForegroundColor Green
