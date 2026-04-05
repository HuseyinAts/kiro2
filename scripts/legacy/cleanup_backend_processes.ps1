# Backend Process Cleanup Script
# Türkiye Üniversite Sınavları Hazırlık Platformu
# Tüm eski backend process'lerini temizle ve tek clean instance başlat

Write-Host "================================================" -ForegroundColor Red
Write-Host "BACKEND PROCESS CLEANUP" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host ""

# 1. Tüm Python/uvicorn process'lerini listele
Write-Host "[1/4] Mevcut backend process'leri tespit ediliyor..." -ForegroundColor Yellow

$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
$uvicornProcesses = Get-Process uvicorn* -ErrorAction SilentlyContinue

$totalProcesses = 0
if ($pythonProcesses) {
    $totalProcesses += $pythonProcesses.Count
    Write-Host "  Python process'ler: $($pythonProcesses.Count)" -ForegroundColor Gray
}
if ($uvicornProcesses) {
    $totalProcesses += $uvicornProcesses.Count
    Write-Host "  Uvicorn process'ler: $($uvicornProcesses.Count)" -ForegroundColor Gray
}

Write-Host "  TOPLAM: $totalProcesses process bulundu" -ForegroundColor Cyan

if ($totalProcesses -eq 0) {
    Write-Host "  ✓ Hiç backend process çalışmıyor" -ForegroundColor Green
} else {
    Write-Host "  ! $totalProcesses backend process çalışıyor (Temizlenecek)" -ForegroundColor Yellow
}

Write-Host ""

# 2. Port 8000'i kullanan process'i bul ve öldür
Write-Host "[2/4] Port 8000'i kullanan process temizleniyor..." -ForegroundColor Yellow

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    $processId = $port8000[0].OwningProcess
    Write-Host "  Port 8000 kullanan process: PID $processId" -ForegroundColor Gray
    
    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Host "  ✓ Process $processId sonlandırıldı" -ForegroundColor Green
    } catch {
        Write-Host "  ! Process sonlandırılamadı (zaten kapanmış olabilir)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ Port 8000 boş" -ForegroundColor Green
}

Write-Host ""

# 3. Kalan tüm backend process'lerini temizle
Write-Host "[3/4] Tüm backend process'leri temizleniyor..." -ForegroundColor Yellow

$killedCount = 0

# Python process'leri
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        # main.py veya uvicorn içeren process'leri öldür
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($cmdLine -match "main\.py|uvicorn") {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                Write-Host "  ✓ Backend process sonlandırıldı: PID $($proc.Id)" -ForegroundColor Green
                $killedCount++
            } catch {
                Write-Host "  ! Process $($proc.Id) sonlandırılamadı" -ForegroundColor Yellow
            }
        }
    }
}

# Uvicorn process'leri
$uvicornProcesses = Get-Process uvicorn* -ErrorAction SilentlyContinue
if ($uvicornProcesses) {
    foreach ($proc in $uvicornProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "  ✓ Uvicorn process sonlandırıldı: PID $($proc.Id)" -ForegroundColor Green
            $killedCount++
        } catch {
            Write-Host "  ! Process $($proc.Id) sonlandırılamadı" -ForegroundColor Yellow
        }
    }
}

Write-Host "  Toplam $killedCount process temizlendi" -ForegroundColor Cyan
Write-Host ""

# Bekle (process'lerin tamamen kapanması için)
Write-Host "Bekleniyor: Process'lerin tamamen kapanması için 3 saniye..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 4. Doğrulama - hiç process kaldı mı?
Write-Host "[4/4] Temizlik doğrulanıyor..." -ForegroundColor Yellow

$remainingPython = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    $cmdLine -match "main\.py|uvicorn"
}

$remainingUvicorn = Get-Process uvicorn* -ErrorAction SilentlyContinue

if (-not $remainingPython -and -not $remainingUvicorn) {
    Write-Host "  ✓ Tüm backend process'leri temizlendi" -ForegroundColor Green
} else {
    Write-Host "  ! Bazı process'ler hala çalışıyor:" -ForegroundColor Yellow
    if ($remainingPython) {
        foreach ($proc in $remainingPython) {
            Write-Host "    - Python PID: $($proc.Id)" -ForegroundColor Gray
        }
    }
    if ($remainingUvicorn) {
        foreach ($proc in $remainingUvicorn) {
            Write-Host "    - Uvicorn PID: $($proc.Id)" -ForegroundColor Gray
        }
    }
    Write-Host "  Manuel sonlandırma gerekebilir: Task Manager'dan kontrol edin" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "✓ CLEANUP TAMAMLANDI!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# 5. Port durumu
Write-Host "Port Durumu:" -ForegroundColor Cyan
$port8000Check = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if (-not $port8000Check) {
    Write-Host "  ✓ Port 8000 ŞİMDİ BOŞ - Backend başlatmaya hazır!" -ForegroundColor Green
} else {
    Write-Host "  ! Port 8000 hala meşgul" -ForegroundColor Red
    Write-Host "    Lütfen Task Manager'dan manuel temizlik yapın" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Temiz Backend Başlatmak İçin:" -ForegroundColor Cyan
Write-Host "  cd C:\Users\husey\kiro2\backend" -ForegroundColor White
Write-Host "  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
Write-Host ""
Write-Host "Load Test İçin:" -ForegroundColor Cyan
Write-Host "  cd C:\Users\husey\kiro2" -ForegroundColor White
Write-Host "  python quick_load_test.py" -ForegroundColor White
Write-Host ""
Write-Host "Beklenen Performans (Tek Instance + PostgreSQL + Cache):" -ForegroundColor Yellow
Write-Host "  - Health check: under 50ms (şu an: 3853ms)" -ForegroundColor Gray
Write-Host "  - Hybrid-codes: 15-60ms avg (şu an: timeout)" -ForegroundColor Gray
Write-Host "  - Statistics: 20-50ms avg (şu an: timeout)" -ForegroundColor Gray
Write-Host "  - Cache hit rate: 95% (korunacak)" -ForegroundColor Gray
Write-Host "  - RPS: 50-200 (şu an: under 1)" -ForegroundColor Gray
Write-Host ""
