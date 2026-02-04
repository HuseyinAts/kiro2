# AGGRESSIVE CLEANUP - Nuclear Option (Restart olmadan)
# Tüm Python/Uvicorn process'lerini zorla sonlandır
# Port 8000'i temizle, Docker container'ları restart et

Write-Host "=" * 70 -ForegroundColor Red
Write-Host "AGGRESSIVE CLEANUP - NUCLEAR OPTION" -ForegroundColor Red
Write-Host "Tüm backend process'leri ve zombie'ler temizlenecek!" -ForegroundColor Red
Write-Host "=" * 70 -ForegroundColor Red
Write-Host ""

$killedCount = 0
$errors = @()

# ============================================================================
# STEP 1: TÜM PYTHON PROCESS'LERİNİ ÖLDÜRMEYİ DENE
# ============================================================================
Write-Host "[1/6] Tüm Python process'leri bulunuyor..." -ForegroundColor Yellow

$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "  Bulunan Python process'ler: $($pythonProcesses.Count)" -ForegroundColor Gray
    
    foreach ($proc in $pythonProcesses) {
        try {
            $procInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue
            $cmdLine = if ($procInfo) { $procInfo.CommandLine } else { "N/A" }
            
            Write-Host "  Killing PID $($proc.Id): $($cmdLine.Substring(0, [Math]::Min(60, $cmdLine.Length)))..." -ForegroundColor Gray
            
            # Try graceful first
            $proc.CloseMainWindow() | Out-Null
            Start-Sleep -Milliseconds 500
            
            # Force kill
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            $killedCount++
            Write-Host "    ✓ Killed" -ForegroundColor Green
        }
        catch {
            Write-Host "    ! Failed: $($_.Exception.Message)" -ForegroundColor Yellow
            $errors += "Python PID $($proc.Id): $($_.Exception.Message)"
        }
    }
}
else {
    Write-Host "  ✓ Hiç Python process bulunamadı" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# STEP 2: UVICORN PROCESS'LERİNİ ÖLDÜRMEYİ DENE
# ============================================================================
Write-Host "[2/6] Uvicorn process'leri bulunuyor..." -ForegroundColor Yellow

$uvicornProcesses = Get-Process uvicorn* -ErrorAction SilentlyContinue
if ($uvicornProcesses) {
    Write-Host "  Bulunan Uvicorn process'ler: $($uvicornProcesses.Count)" -ForegroundColor Gray
    
    foreach ($proc in $uvicornProcesses) {
        try {
            Write-Host "  Killing Uvicorn PID $($proc.Id)..." -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            $killedCount++
            Write-Host "    ✓ Killed" -ForegroundColor Green
        }
        catch {
            Write-Host "    ! Failed: $($_.Exception.Message)" -ForegroundColor Yellow
            $errors += "Uvicorn PID $($proc.Id): $($_.Exception.Message)"
        }
    }
}
else {
    Write-Host "  ✓ Hiç Uvicorn process bulunamadı" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# STEP 3: PORT 8000'İ KULLANAN PROCESS'İ ÖLDÜRMEYİ DENE
# ============================================================================
Write-Host "[3/6] Port 8000'i kullanan process bulunuyor..." -ForegroundColor Yellow

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    foreach ($conn in $port8000) {
        $processId = $conn.OwningProcess
        try {
            $procName = (Get-Process -Id $processId -ErrorAction SilentlyContinue).Name
            Write-Host "  Port 8000 kullanan: PID $processId ($procName)" -ForegroundColor Gray
            Write-Host "  Killing..." -ForegroundColor Gray
            
            Stop-Process -Id $processId -Force -ErrorAction Stop
            $killedCount++
            Write-Host "    ✓ Killed" -ForegroundColor Green
        }
        catch {
            Write-Host "    ! Failed: $($_.Exception.Message)" -ForegroundColor Yellow
            $errors += "Port 8000 PID $processId: $($_.Exception.Message)"
        }
    }
}
else {
    Write-Host "  ✓ Port 8000 zaten boş" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# STEP 4: WINDOWS TASK KILL KOMUTUYLA ZORLA TEMIZLE
# ============================================================================
Write-Host "[4/6] Windows taskkill ile son temizlik..." -ForegroundColor Yellow

# Python.exe'yi taskkill ile zorla öldür
$taskkillResult = taskkill /F /IM python.exe /T 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ taskkill başarılı: python.exe" -ForegroundColor Green
}
else {
    Write-Host "  ℹ taskkill sonuç: $taskkillResult" -ForegroundColor Gray
}

# Uvicorn.exe'yi taskkill ile zorla öldür
$taskkillUvicorn = taskkill /F /IM uvicorn.exe /T 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ taskkill başarılı: uvicorn.exe" -ForegroundColor Green
}
else {
    Write-Host "  ℹ taskkill sonuç: $taskkillUvicorn" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# STEP 5: DOCKER BACKEND CONTAINER'I DURDUR (eğer çalışıyorsa)
# ============================================================================
Write-Host "[5/6] Docker backend container kontrol ediliyor..." -ForegroundColor Yellow

$backendContainer = docker ps -a --filter "name=turkiye_sinav_backend" --format "{{.Names}}" 2>$null
if ($backendContainer) {
    Write-Host "  Backend container bulundu: $backendContainer" -ForegroundColor Gray
    Write-Host "  Durduruluyor ve siliniyor..." -ForegroundColor Gray
    
    docker stop $backendContainer 2>&1 | Out-Null
    docker rm $backendContainer 2>&1 | Out-Null
    
    Write-Host "  ✓ Backend container temizlendi" -ForegroundColor Green
}
else {
    Write-Host "  ✓ Backend container bulunamadı" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# STEP 6: BEKLEYİP DOĞRULA
# ============================================================================
Write-Host "[6/6] Temizlik doğrulanıyor..." -ForegroundColor Yellow
Write-Host "  5 saniye bekleniyor..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Python process kontrolü
$remainingPython = Get-Process python* -ErrorAction SilentlyContinue
$remainingUvicorn = Get-Process uvicorn* -ErrorAction SilentlyContinue
$remainingPort = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

$allClean = (-not $remainingPython) -and (-not $remainingUvicorn) -and (-not $remainingPort)

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "CLEANUP SONUÇLARI" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

Write-Host "Process'ler:" -ForegroundColor White
if (-not $remainingPython) {
    Write-Host "  ✓ Python process'ler temiz" -ForegroundColor Green
}
else {
    Write-Host "  ! $($remainingPython.Count) Python process hala çalışıyor" -ForegroundColor Red
    foreach ($proc in $remainingPython | Select-Object -First 3) {
        Write-Host "    - PID: $($proc.Id)" -ForegroundColor Gray
    }
}

if (-not $remainingUvicorn) {
    Write-Host "  ✓ Uvicorn process'ler temiz" -ForegroundColor Green
}
else {
    Write-Host "  ! $($remainingUvicorn.Count) Uvicorn process hala çalışıyor" -ForegroundColor Red
}

Write-Host ""
Write-Host "Port Durumu:" -ForegroundColor White
if (-not $remainingPort) {
    Write-Host "  ✓ Port 8000 BOŞ - Backend başlatmaya hazır!" -ForegroundColor Green
}
else {
    Write-Host "  ! Port 8000 hala meşgul (PID: $($remainingPort[0].OwningProcess))" -ForegroundColor Red
}

Write-Host ""
Write-Host "Özet:" -ForegroundColor White
Write-Host "  Sonlandırılan process sayısı: $killedCount" -ForegroundColor Gray
if ($errors.Count -gt 0) {
    Write-Host "  Hatalar: $($errors.Count)" -ForegroundColor Yellow
    foreach ($err in $errors | Select-Object -First 3) {
        Write-Host "    - $err" -ForegroundColor Gray
    }
}

Write-Host ""
if ($allClean) {
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host "✓ TEMİZLİK BAŞARILI!" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host ""
    Write-Host "Şimdi backend başlatabilirsiniz:" -ForegroundColor Cyan
    Write-Host "  .\start_clean_backend.ps1" -ForegroundColor White
}
else {
    Write-Host "=" * 70 -ForegroundColor Yellow
    Write-Host "⚠ TEMİZLİK KISMEN BAŞARILI" -ForegroundColor Yellow
    Write-Host "=" * 70 -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bazı process'ler hala çalışıyor." -ForegroundColor Yellow
    Write-Host "Önerilen çözümler:" -ForegroundColor Cyan
    Write-Host "  1. Task Manager'ı aç (Ctrl+Shift+Esc)" -ForegroundColor White
    Write-Host "  2. Details sekmesinde python.exe process'lerini manuel sonlandır" -ForegroundColor White
    Write-Host "  3. VEYA bilgisayarı restart et" -ForegroundColor White
    Write-Host ""
    Write-Host "Eğer sorun devam ederse:" -ForegroundColor Cyan
    Write-Host "  Get-Process python* | Stop-Process -Force" -ForegroundColor White
}

Write-Host ""
