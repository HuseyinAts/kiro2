# ============================================================
# KIRO2 — CAT + IRT Kurulum Scripti
# Kullanım: cd C:\Users\husey\kiro2 && .\scripts\install_cat.ps1
# ============================================================
param(
    [string]$Root      = "C:\Users\husey\kiro2",
    [string]$Deploy    = $PSScriptRoot + "\..",
    [string]$DbPort    = "5434",
    [string]$DbName    = "turkiye_sinav_db",
    [string]$Container = "turkiye_sinav_postgres"
)

$ErrorActionPreference = "Continue"
function OK   { Write-Host "  ✓ $args" -ForegroundColor Green }
function WARN { Write-Host "  ⚠ $args" -ForegroundColor Yellow }
function STEP { Write-Host "`n► $args" -ForegroundColor Cyan }

Write-Host "KIRO2 CAT+IRT Kurulum" -ForegroundColor Magenta

# ── ADIM 1: Bağımlılıklar ──────────────────────────────────────
STEP "Python bağımlılıkları"
$req = "$Root\backend\requirements.txt"
@("scipy>=1.11.0","redis[asyncio]>=5.0.0","celery[redis]>=5.3.0") | ForEach-Object {
    $pkg = $_ -split "[>=\[]" | Select-Object -First 1
    if (-not (Select-String -Path $req -Pattern "^$pkg" -Quiet 2>$null)) {
        Add-Content $req $_; OK "Eklendi: $_"
    } else { WARN "Zaten var: $pkg" }
}
Push-Location "$Root\backend"
pip install -r requirements.txt -q | Select-Object -Last 2
OK "pip install tamamlandı"
Pop-Location

# ── ADIM 2: Dosyaları kopyala ──────────────────────────────────
STEP "Dosyaları kopyala"
$map = @{
    "backend\app\services\irt_engine.py"      = "$Deploy\backend\app\services\irt_engine.py"
    "backend\app\services\cat_session.py"     = "$Deploy\backend\app\services\cat_session.py"
    "backend\app\services\irt_calibrator.py"  = "$Deploy\backend\app\services\irt_calibrator.py"
    "backend\app\api\cat.py"                  = "$Deploy\backend\app\api\cat.py"
    "backend\app\schemas\cat_schemas.py"      = "$Deploy\backend\app\schemas\cat_schemas.py"
    "backend\app\tasks\calibration_task.py"   = "$Deploy\backend\app\tasks\calibration_task.py"
    "backend\tests\test_cat.py"               = "$Deploy\backend\tests\test_cat.py"
    "backend\tests\test_irt_calibration.py"   = "$Deploy\backend\tests\test_irt_calibration.py"
}
foreach ($dst in $map.Keys) {
    $src = $map[$dst]; $full = "$Root\$dst"
    if (-not (Test-Path (Split-Path $full))) { New-Item -Type Directory -Force (Split-Path $full) | Out-Null }
    if (Test-Path $full) { Copy-Item $full "$full.bak" -Force }
    if (Test-Path $src)  { Copy-Item $src $full -Force; OK $dst }
    else                 { WARN "Kaynak yok: $src" }
}

# ── ADIM 3: __init__.py ────────────────────────────────────────
STEP "__init__.py kontrol"
@("$Root\backend\app\tasks") | ForEach-Object {
    $f = "$_\__init__.py"
    if (-not (Test-Path $f)) { New-Item -Type File -Force $f | Out-Null; OK $f }
    else { WARN "Var: $f" }
}

# ── ADIM 4: main.py router ekle ───────────────────────────────
STEP "main.py güncelle"
$main = "$Root\backend\app\main.py"
if (Test-Path $main) {
    $c = Get-Content $main -Raw
    if ($c -notmatch "cat_router") {
        Copy-Item $main "$main.bak"
        $importLine = "`nfrom app.api.cat import router as cat_router  # CAT Engine"
        $routerLine = "`napp.include_router(cat_router)  # CAT Engine"
        # Import'u ekle
        if ($c -match "from app\.api") {
            $c = $c -replace "(from app\.api[^\n]+)", "`$1$importLine"
        } else { $c = $importLine + "`n" + $c }
        # Router'ı ekle
        $c += $routerLine
        Set-Content $main $c -Encoding UTF8
        OK "main.py güncellendi"
        WARN "main.py'yi kontrol et — import ve include_router doğru yerde mi?"
    } else { WARN "cat_router zaten var" }
} else { WARN "main.py bulunamadı: $main" }

# ── ADIM 5: deps.py'ye get_redis ekle ─────────────────────────
STEP "deps.py güncelle"
$deps = "$Root\backend\app\core\deps.py"
if (Test-Path $deps) {
    if (-not (Select-String -Path $deps -Pattern "get_redis" -Quiet)) {
        $block = Get-Content "$Deploy\backend\app\core\deps_addition.py" -Raw
        Add-Content $deps $block
        OK "get_redis eklendi"
    } else { WARN "get_redis zaten var" }
} else { WARN "deps.py bulunamadı" }

# ── ADIM 6: Redis lifespan ─────────────────────────────────────
STEP "main.py Redis lifespan — MANUEL KONTROL GEREKLİ"
WARN "main.py'deki lifespan fonksiyonuna Redis başlatma kodunu eklemen gerekiyor."
WARN "main_addition.py dosyasını oku: $Deploy\backend\app\main_addition.py"
Get-Content "$Deploy\backend\app\main_addition.py" | Write-Host -ForegroundColor DarkGray

# ── ADIM 7: Celery beat schedule ──────────────────────────────
STEP "celeryconfig.py güncelle"
$cc = "$Root\backend\celeryconfig.py"
if (Test-Path $cc) {
    if (-not (Select-String -Path $cc -Pattern "irt-calibration" -Quiet)) {
        $block = Get-Content "$Deploy\backend\celeryconfig.py" -Raw
        Add-Content $cc $block
        OK "Beat schedule eklendi"
    } else { WARN "Schedule zaten var" }
} else {
    Copy-Item "$Deploy\backend\celeryconfig.py" $cc
    OK "celeryconfig.py oluşturuldu"
}

# ── ADIM 8: Migration ─────────────────────────────────────────
STEP "Database migration"
$running = docker ps --filter "name=$Container" --format "{{.Names}}" 2>$null
if ($running) {
    foreach ($sql in @("001_cat_sessions.sql","002_irt_calibration.sql")) {
        $path = "$Deploy\alembic\versions\$sql"
        if (Test-Path $path) {
            Get-Content $path | docker exec -i $Container psql -U postgres -d $DbName 2>&1 | Select-Object -Last 2
            OK "Migration: $sql"
        }
    }
    Push-Location "$Root\backend"
    alembic upgrade head 2>&1 | Select-Object -Last 3
    OK "alembic upgrade head"
    Pop-Location
} else {
    WARN "Docker container çalışmıyor — migration atlandı"
    WARN "Manuel: docker exec -i $Container psql -U postgres -d $DbName < 001_cat_sessions.sql"
}

# ── ADIM 9: Testler ───────────────────────────────────────────
STEP "Testleri çalıştır"
Push-Location "$Root\backend"
python -m pytest tests/test_cat.py tests/test_irt_calibration.py -q --tb=short 2>&1 | Select-Object -Last 5
Pop-Location

# ── ÖZET ──────────────────────────────────────────────────────
Write-Host @"

✅ Kurulum tamamlandı!

Kontrol listesi:
  [ ] main.py lifespan'e Redis kodu eklendi mi?
  [ ] uvicorn app.main:app --reload  →  /docs'ta /api/v1/cat/ var mı?
  [ ] redis-cli ping  →  PONG
  [ ] celery -A celery_app worker --loglevel=info

API uç noktaları:
  POST   /api/v1/cat/sessions
  POST   /api/v1/cat/sessions/{id}/answer
  GET    /api/v1/cat/sessions/{id}
  DELETE /api/v1/cat/sessions/{id}

IRT Kalibrasyon:
  celery -A celery_app call kiro2.tasks.irt_calibration
  SELECT * FROM vw_irt_calibration_status;
"@ -ForegroundColor Cyan
