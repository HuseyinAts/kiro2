# KIRO2 — Migration + Backend Restart v2
# Calistir: .\scripts\migrate_and_restart.ps1

$Root   = "C:\Users\husey\kiro2"
$Db     = "kiro2"
$PgPort = "5434"
$PgUser = "postgres"
$PgPass = "changeme_strong_password_here"
$PgHost = "localhost"
$Psql   = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

function OK  { Write-Host "  [OK] $args" -ForegroundColor Green }
function ERR { Write-Host "  [!!] $args" -ForegroundColor Red }
function INF { Write-Host "  [--] $args" -ForegroundColor Cyan }
function HDR { Write-Host "`n=== $args ===" -ForegroundColor Magenta }

# ── 1. MIGRATIONS ────────────────────────────────────────────────────────────
HDR "1. MIGRATIONS"
$env:PGPASSWORD = $PgPass
@("001_cat_sessions","002_irt_calibration","003_fsrs","004_dag") | ForEach-Object {
    $name = $_
    $sql  = "$Root\alembic\versions\$name.sql"
    if (-not (Test-Path $sql)) { ERR "$name.sql dosya yok"; return }
    $out  = & $Psql -h $PgHost -p $PgPort -U $PgUser -d $Db -f $sql 2>&1
    $err  = $out | Where-Object { $_ -match "ERROR" -and $_ -notmatch "already exists" }
    if ($err) { ERR "$name.sql: $($err[0])" } else { OK "$name.sql" }
}
Remove-Item Env:\PGPASSWORD -EA SilentlyContinue

# ── 2. TABLO KONTROL ─────────────────────────────────────────────────────────
HDR "2. TABLOLAR"
$env:PGPASSWORD = $PgPass
$q = "SELECT tablename FROM pg_tables WHERE tablename IN ('kiro2_cat_sessions','user_item_fsrs','topic_prerequisites','kiro2_learning_events') ORDER BY tablename;"
$tables = & $Psql -h $PgHost -p $PgPort -U $PgUser -d $Db -t -c $q 2>&1
Remove-Item Env:\PGPASSWORD -EA SilentlyContinue
$found = $tables | Where-Object { $_.Trim() -ne "" -and $_ -notmatch "ERROR" }
if ($found) { $found | ForEach-Object { OK $_.Trim() } }
else { ERR "Tablo olusturulamadi" }

# ── 3. SADECE UVICORN'U DURDUR ───────────────────────────────────────────────
HDR "3. UVICORN DURDUR"
# Sadece uvicorn process'ini bul — Docker/WSL'e dokunma
$uvicornPids = Get-WmiObject Win32_Process -Filter "Name='python.exe' OR Name='python3.exe'" -EA SilentlyContinue |
    Where-Object { $_.CommandLine -like "*uvicorn*" } |
    Select-Object -ExpandProperty ProcessId

if ($uvicornPids) {
    $uvicornPids | ForEach-Object {
        INF "uvicorn PID $_ durduruluyor..."
        Stop-Process -Id $_ -Force -EA SilentlyContinue
    }
    Start-Sleep -Seconds 2
    OK "uvicorn durduruldu"
} else {
    INF "Calisir uvicorn bulunamadi"
}

# ── 4. BACKEND BASLAT ────────────────────────────────────────────────────────
HDR "4. BACKEND BASLAT"
Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/k cd /d `"$Root\backend`" && uvicorn main:app --reload --port 8000" `
    -WindowStyle Normal

# BERTurk yuklenmesi ~15s suruyor — 20s bekle
INF "BERTurk modeli yukleniyor, 20s bekliyorum..."
Start-Sleep -Seconds 20

# ── 5. DOGRULA ───────────────────────────────────────────────────────────────
HDR "5. DOGRULA"
$ready = $false
for ($i = 1; $i -le 3; $i++) {
    try {
        $r = Invoke-WebRequest "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 2>$null
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    if ($i -lt 3) { INF "Deneme $i basarisiz, 5s daha bekliyorum..."; Start-Sleep -Seconds 5 }
}

if ($ready) {
    OK "Backend calisiyor: http://localhost:8000"
    $spec = (Invoke-WebRequest "http://localhost:8000/openapi.json" -UseBasicParsing 2>$null).Content | ConvertFrom-Json
    @("/api/v1/cat","/api/v1/fsrs","/api/v1/dag","/api/v1/placement","/api/v1/estimate") | ForEach-Object {
        $p = $_
        $n = ($spec.paths.PSObject.Properties.Name | Where-Object { $_ -like "*$p*" }).Count
        if ($n -gt 0) { OK "$p ($n endpoint)" } else { ERR "$p eksik" }
    }
} else {
    ERR "Backend 30s icinde baslamadi"
    INF "Yeni terminaldeki loglara bak: $Root\backend\kiro2_backend.log"
}

Write-Host "`nTAMAMLANDI" -ForegroundColor Cyan
