# START CLEAN BACKEND - Single Instance Only
# PostgreSQL + Redis + Cache ready
# Expected: 15-60ms avg, 50-200 RPS

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "STARTING CLEAN BACKEND - PostgreSQL + Cache" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# 1. Port kontrolü
Write-Host "[1/5] Port 8000 durumu kontrol ediliyor..." -ForegroundColor Yellow
$portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($portCheck) {
    Write-Host "  ✗ Port 8000 meşgul!" -ForegroundColor Red
    Write-Host "    Lütfen önce cleanup_backend_processes.ps1 çalıştırın" -ForegroundColor Yellow
    Write-Host "    VEYA Task Manager'dan python.exe process'lerini sonlandırın" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "  ✓ Port 8000 boş" -ForegroundColor Green
}

# 2. Docker kontrol
Write-Host "[2/5] Docker container'lar kontrol ediliyor..." -ForegroundColor Yellow
$postgresRunning = docker ps --filter "name=turkiye_sinav_postgres" --format "{{.Status}}" 2>$null
$redisRunning = docker ps --filter "name=turkiye_sinav_redis" --format "{{.Status}}" 2>$null

if (-not $postgresRunning) {
    Write-Host "  ✗ PostgreSQL container çalışmıyor!" -ForegroundColor Red
    Write-Host "    Başlatılıyor..." -ForegroundColor Yellow
    docker-compose up -d postgres redis
    Start-Sleep -Seconds 5
} else {
    Write-Host "  ✓ PostgreSQL çalışıyor: $postgresRunning" -ForegroundColor Green
}

if (-not $redisRunning) {
    Write-Host "  ✗ Redis container çalışmıyor!" -ForegroundColor Red
    Write-Host "    Başlatılıyor..." -ForegroundColor Yellow
    docker-compose up -d redis
    Start-Sleep -Seconds 3
} else {
    Write-Host "  ✓ Redis çalışıyor: $redisRunning" -ForegroundColor Green
}

# 3. Backend klasörüne git
Write-Host "[3/5] Backend klasörüne gidiliyor..." -ForegroundColor Yellow
cd backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Backend klasörü bulunamadı!" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Backend klasöründe: $(Get-Location)" -ForegroundColor Green

# 4. Bağımlılıkları kontrol
Write-Host "[4/5] PostgreSQL driver'ları kontrol ediliyor..." -ForegroundColor Yellow
$asyncpgCheck = pip show asyncpg 2>$null
$psycopgCheck = pip show psycopg2-binary 2>$null

if (-not $asyncpgCheck -or -not $psycopgCheck) {
    Write-Host "  ! Driver'lar eksik, yükleniyor..." -ForegroundColor Yellow
    pip install asyncpg==0.29.0 psycopg2-binary==2.9.9 --quiet
    Write-Host "  ✓ Driver'lar yüklendi" -ForegroundColor Green
} else {
    Write-Host "  ✓ Driver'lar hazır" -ForegroundColor Green
}

# 5. Backend başlat
Write-Host "[5/5] Backend başlatılıyor..." -ForegroundColor Yellow
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "✓ READY TO START!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "Backend Konfigürasyonu:" -ForegroundColor Cyan
Write-Host "  - Database:      PostgreSQL (pool_size=20, max_overflow=40)" -ForegroundColor Gray
Write-Host "  - Cache:         Redis (95% hit rate expected)" -ForegroundColor Gray
Write-Host "  - Port:          8000" -ForegroundColor Gray
Write-Host "  - Host:          0.0.0.0" -ForegroundColor Gray
Write-Host "  - Reload:        Enabled" -ForegroundColor Gray
Write-Host ""
Write-Host "Expected Performance:" -ForegroundColor Yellow
Write-Host "  - Health check:  <50ms" -ForegroundColor Gray
Write-Host "  - Hybrid-codes:  15-60ms (20 concurrent, 95% cache hit)" -ForegroundColor Gray
Write-Host "  - Statistics:    20-50ms (20 concurrent)" -ForegroundColor Gray
Write-Host "  - RPS:           50-200" -ForegroundColor Gray
Write-Host ""
Write-Host "Starting uvicorn..." -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor White
Write-Host ""

# Backend'i başlat (foreground - bu script bu noktada bekler)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
