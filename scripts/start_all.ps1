# KIRO2 — Redis + Backend Tam Baslangic v2
# Calistir: .\scripts\start_all.ps1

$Root = "C:\Users\husey\kiro2"

function OK  { Write-Host "  [OK] $args" -ForegroundColor Green }
function ERR { Write-Host "  [!!] $args" -ForegroundColor Red }
function INF { Write-Host "  [--] $args" -ForegroundColor Cyan }
function HDR { Write-Host "`n=== $args ===" -ForegroundColor Magenta }

# ── 1. DOCKER BACKEND DURDUR (port 8000 temizle) ─────────────────────────────
HDR "1. PORT 8000 TEMIZLE"
$bcOut = docker stop kiro2-backend 2>&1
if ($LASTEXITCODE -eq 0) { OK "kiro2-backend container durduruldu" }
else { INF "kiro2-backend zaten kapali veya yok" }

# Uvicorn process varsa onu da durdur
$procs = Get-WmiObject Win32_Process -Filter "Name='python.exe'" -EA SilentlyContinue |
    Where-Object { $_.CommandLine -like "*uvicorn*" }
if ($procs) {
    $procs | ForEach-Object {
        INF "uvicorn PID $($_.ProcessId) durduruluyor..."
        Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue
    }
    Start-Sleep -Seconds 2
    OK "uvicorn durduruldu"
}

# ── 2. REDIS ─────────────────────────────────────────────────────────────────
HDR "2. REDIS"
Set-Location $Root
docker compose up redis -d 2>&1 | Out-Null
Start-Sleep -Seconds 3
$redisOk = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -EA SilentlyContinue
if ($redisOk.TcpTestSucceeded) { OK "localhost:6379 Redis hazir" }
else { ERR "Redis baglanti hatasi" }

# ── 3. BACKEND BASLAT ────────────────────────────────────────────────────────
HDR "3. BACKEND BASLAT"
Start-Process "cmd.exe" -ArgumentList "/k cd /d `"$Root\backend`" && uvicorn main:app --reload --port 8000" -WindowStyle Normal
INF "Backend baslatildi — BERTurk GPU yuklemesi ~15s suruyor..."
Start-Sleep -Seconds 25

# ── 4. DOGRULA ───────────────────────────────────────────────────────────────
HDR "4. DOGRULA"

# Hangi process port 8000'de?
$pid8000 = netstat -ano 2>$null | Select-String ":8000 " |
    ForEach-Object { ($_ -split '\s+')[-1] } |
    Select-Object -Unique | Where-Object { $_ -match '^\d+$' } |
    Select-Object -First 1
if ($pid8000) {
    $p8000 = Get-Process -Id $pid8000 -EA SilentlyContinue
    INF "Port 8000: PID $pid8000 ($($p8000.ProcessName))"
}

# Backend hazir mi? 5 deneme
$ready = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        $r = Invoke-WebRequest "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 2>$null
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    INF "Deneme $i/5 — 5s bekliyorum..."; Start-Sleep -Seconds 5
}

if (-not $ready) {
    ERR "Backend 50s icinde baslamadi."
    INF "Yeni terminaldeki loglara bak."
    exit 1
}

OK "Backend: http://localhost:8000"

# Endpoint sayim
$spec = (Invoke-WebRequest "http://localhost:8000/openapi.json" -UseBasicParsing 2>$null).Content | ConvertFrom-Json
$toplam = 0
@("/api/v1/cat","/api/v1/fsrs","/api/v1/dag","/api/v1/placement","/api/v1/estimate") | ForEach-Object {
    $p = $_
    $n = ($spec.paths.PSObject.Properties.Name | Where-Object { $_ -like "*$p*" }).Count
    $toplam += $n
    if ($n -gt 0) { OK "$p ($n endpoint)" } else { ERR "$p eksik" }
}

Write-Host ""
if ($toplam -ge 20) {
    Write-Host "  BASARILI: $toplam yeni endpoint aktif" -ForegroundColor Green
} else {
    Write-Host "  UYARI: Sadece $toplam endpoint bulundu (beklenen: 27)" -ForegroundColor Yellow
}
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "`nTAMAMLANDI" -ForegroundColor Cyan
