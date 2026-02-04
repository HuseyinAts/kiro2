# MASTER CLEANUP & RESTART
# System restart yerine en kapsamlı temizlik
# Tüm yöntemleri birleştiren master script

param(
    [switch]$AutoStart = $false  # Backend'i otomatik başlatsın mı?
)

Write-Host ""
Write-Host "###############################################################" -ForegroundColor Cyan
Write-Host "#                                                              #" -ForegroundColor Cyan
Write-Host "#           MASTER CLEANUP - FULL SYSTEM RESET                #" -ForegroundColor Cyan
Write-Host "#         (System Restart Alternatifi - 3 Yöntem)             #" -ForegroundColor Cyan
Write-Host "#                                                              #" -ForegroundColor Cyan
Write-Host "###############################################################" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$script:totalKilled = 0
$script:errors = @()

# ============================================================================
# YÖNTEM 1: GRACEFUL SHUTDOWN (Önce nazikçe)
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "YÖNTEM 1: GRACEFUL SHUTDOWN" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

function Stop-BackendProcessGracefully {
    $processes = Get-Process python*,uvicorn* -ErrorAction SilentlyContinue
    if (-not $processes) {
        Write-Host "  ✓ Hiç backend process bulunamadı" -ForegroundColor Green
        return 0
    }
    
    Write-Host "  $($processes.Count) process bulundu, graceful shutdown deneniyor..." -ForegroundColor Gray
    $killed = 0
    
    foreach ($proc in $processes) {
        try {
            # Try close main window first
            if ($proc.CloseMainWindow()) {
                Write-Host "    ✓ PID $($proc.Id): Main window kapatıldı" -ForegroundColor Green
                $killed++
            }
        }
        catch {
            # Ignore errors
        }
    }
    
    Start-Sleep -Seconds 2
    return $killed
}

$gracefulKilled = Stop-BackendProcessGracefully
$script:totalKilled += $gracefulKilled
Write-Host "  Sonuç: $gracefulKilled process gracefully kapatıldı" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# YÖNTEM 2: FORCE KILL (PowerShell Stop-Process)
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "YÖNTEM 2: FORCE KILL (PowerShell)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

function Stop-BackendProcessForce {
    $processes = Get-Process python*,uvicorn* -ErrorAction SilentlyContinue
    if (-not $processes) {
        Write-Host "  ✓ Hiç process kalmadı" -ForegroundColor Green
        return 0
    }
    
    Write-Host "  $($processes.Count) process kaldı, force kill yapılıyor..." -ForegroundColor Gray
    $killed = 0
    
    foreach ($proc in $processes) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "    ✓ PID $($proc.Id): Force killed" -ForegroundColor Green
            $killed++
        }
        catch {
            Write-Host "    ! PID $($proc.Id): Başarısız - $($_.Exception.Message)" -ForegroundColor Red
            $script:errors += "Force kill PID $($proc.Id): $($_.Exception.Message)"
        }
    }
    
    return $killed
}

$forceKilled = Stop-BackendProcessForce
$script:totalKilled += $forceKilled
Write-Host "  Sonuç: $forceKilled process force killed" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# YÖNTEM 3: WINDOWS TASKKILL (System-level)
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "YÖNTEM 3: WINDOWS TASKKILL (System-level)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

Write-Host "  taskkill /F /IM python.exe /T çalıştırılıyor..." -ForegroundColor Gray
$taskkillPython = taskkill /F /IM python.exe /T 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "    ✓ Python.exe processes sonlandırıldı" -ForegroundColor Green
}
else {
    Write-Host "    ℹ Sonuç: $taskkillPython" -ForegroundColor Gray
}

Write-Host "  taskkill /F /IM uvicorn.exe /T çalıştırılıyor..." -ForegroundColor Gray
$taskkillUvicorn = taskkill /F /IM uvicorn.exe /T 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "    ✓ Uvicorn.exe processes sonlandırıldı" -ForegroundColor Green
}
else {
    Write-Host "    ℹ Sonuç: $taskkillUvicorn" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# PORT CLEANUP
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "PORT 8000 CLEANUP" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "  Port 8000 hala kullanımda!" -ForegroundColor Red
    foreach ($conn in $port8000) {
        $pid = $conn.OwningProcess
        $procName = (Get-Process -Id $pid -ErrorAction SilentlyContinue).Name
        Write-Host "    PID $pid ($procName) sonlandırılıyor..." -ForegroundColor Gray
        
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "      ✓ Sonlandırıldı" -ForegroundColor Green
        }
        catch {
            Write-Host "      ! Başarısız" -ForegroundColor Red
            $script:errors += "Port 8000 PID $pid: $($_.Exception.Message)"
        }
    }
}
else {
    Write-Host "  ✓ Port 8000 temiz" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# DOCKER CLEANUP
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "DOCKER CLEANUP & RESTART" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

# Backend container cleanup
Write-Host "  Backend container temizleniyor..." -ForegroundColor Gray
$backend = docker ps -a --filter "name=turkiye_sinav_backend" --format "{{.Names}}" 2>$null
if ($backend) {
    docker stop $backend 2>&1 | Out-Null
    docker rm $backend 2>&1 | Out-Null
    Write-Host "    ✓ Backend container silindi" -ForegroundColor Green
}
else {
    Write-Host "    ✓ Backend container yok" -ForegroundColor Green
}

# PostgreSQL + Redis restart
Write-Host "  PostgreSQL ve Redis restart ediliyor..." -ForegroundColor Gray
docker-compose restart postgres redis 2>&1 | Out-Null
Write-Host "    ✓ Container'lar restart edildi" -ForegroundColor Green

# Network cleanup
Write-Host "  Unused network'ler temizleniyor..." -ForegroundColor Gray
docker network prune -f 2>&1 | Out-Null
Write-Host "    ✓ Network temizliği tamamlandı" -ForegroundColor Green

Write-Host ""

# ============================================================================
# BEKLEME VE DOĞRULAMA
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "DOĞRULAMA" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Sistem stabilize oluyor (10 saniye)..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Final checks
$remainingPython = Get-Process python* -ErrorAction SilentlyContinue
$remainingUvicorn = Get-Process uvicorn* -ErrorAction SilentlyContinue
$remainingPort = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$postgresStatus = docker ps --filter "name=turkiye_sinav_postgres" --format "{{.Status}}" 2>$null
$redisStatus = docker ps --filter "name=turkiye_sinav_redis" --format "{{.Status}}" 2>$null

Write-Host ""
Write-Host "###############################################################" -ForegroundColor White
Write-Host "#                     CLEANUP SONUÇLARI                        #" -ForegroundColor White
Write-Host "###############################################################" -ForegroundColor White
Write-Host ""

# Processes
Write-Host "Backend Process'ler:" -ForegroundColor Cyan
if (-not $remainingPython -and -not $remainingUvicorn) {
    Write-Host "  ✓ TÜM PROCESS'LER TEMİZLENDİ" -ForegroundColor Green
}
else {
    $total = ($remainingPython ? $remainingPython.Count : 0) + ($remainingUvicorn ? $remainingUvicorn.Count : 0)
    Write-Host "  ! $total process hala çalışıyor" -ForegroundColor Red
    
    if ($remainingPython) {
        Write-Host "    Python: $($remainingPython.Count)" -ForegroundColor Gray
    }
    if ($remainingUvicorn) {
        Write-Host "    Uvicorn: $($remainingUvicorn.Count)" -ForegroundColor Gray
    }
}

# Port
Write-Host ""
Write-Host "Port 8000:" -ForegroundColor Cyan
if (-not $remainingPort) {
    Write-Host "  ✓ BOŞ - Backend başlatmaya hazır!" -ForegroundColor Green
}
else {
    Write-Host "  ! Hala meşgul (PID: $($remainingPort[0].OwningProcess))" -ForegroundColor Red
}

# Docker
Write-Host ""
Write-Host "Docker Container'lar:" -ForegroundColor Cyan
if ($postgresStatus) {
    Write-Host "  ✓ PostgreSQL: $postgresStatus" -ForegroundColor Green
}
else {
    Write-Host "  ✗ PostgreSQL çalışmıyor" -ForegroundColor Red
}

if ($redisStatus) {
    Write-Host "  ✓ Redis: $redisStatus" -ForegroundColor Green
}
else {
    Write-Host "  ✗ Redis çalışmıyor" -ForegroundColor Red
}

# Stats
Write-Host ""
Write-Host "İstatistikler:" -ForegroundColor Cyan
Write-Host "  Sonlandırılan process: $script:totalKilled" -ForegroundColor Gray
Write-Host "  Hatalar: $($script:errors.Count)" -ForegroundColor Gray

# Errors
if ($script:errors.Count -gt 0) {
    Write-Host ""
    Write-Host "Hata Detayları:" -ForegroundColor Yellow
    foreach ($err in $script:errors | Select-Object -First 5) {
        Write-Host "  - $err" -ForegroundColor Gray
    }
}

Write-Host ""

# Final verdict
$systemReady = (-not $remainingPython) -and (-not $remainingUvicorn) -and (-not $remainingPort) -and $postgresStatus -and $redisStatus

if ($systemReady) {
    Write-Host "###############################################################" -ForegroundColor Green
    Write-Host "#                                                              #" -ForegroundColor Green
    Write-Host "#               ✓ SİSTEM TAM HAZIR!                           #" -ForegroundColor Green
    Write-Host "#                                                              #" -ForegroundColor Green
    Write-Host "###############################################################" -ForegroundColor Green
    Write-Host ""
    
    if ($AutoStart) {
        Write-Host "Backend otomatik başlatılıyor..." -ForegroundColor Cyan
        Write-Host ""
        & ".\start_clean_backend.ps1"
    }
    else {
        Write-Host "Backend başlatmak için:" -ForegroundColor Cyan
        Write-Host "  .\start_clean_backend.ps1" -ForegroundColor White
        Write-Host ""
        Write-Host "VEYA otomatik başlatmak için:" -ForegroundColor Cyan
        Write-Host "  .\master_cleanup.ps1 -AutoStart" -ForegroundColor White
    }
}
else {
    Write-Host "###############################################################" -ForegroundColor Yellow
    Write-Host "#                                                              #" -ForegroundColor Yellow
    Write-Host "#         ⚠ SİSTEM KISMEN HAZIR - MANUEL KONTROL GEREKLİ     #" -ForegroundColor Yellow
    Write-Host "#                                                              #" -ForegroundColor Yellow
    Write-Host "###############################################################" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Önerilen çözümler:" -ForegroundColor Yellow
    Write-Host "  1. Task Manager'dan manuel cleanup (Ctrl+Shift+Esc)" -ForegroundColor White
    Write-Host "  2. Bu scripti yeniden çalıştır" -ForegroundColor White
    Write-Host "  3. Son çare: System restart" -ForegroundColor White
}

Write-Host ""
Write-Host "Beklenen Performans (Tek instance + PostgreSQL + Cache):" -ForegroundColor Cyan
Write-Host "  - Health:       <50ms" -ForegroundColor Gray
Write-Host "  - Hybrid-codes: 15-60ms (95% cache hit)" -ForegroundColor Gray
Write-Host "  - Statistics:   20-50ms" -ForegroundColor Gray
Write-Host "  - RPS:          50-200" -ForegroundColor Gray
Write-Host ""
