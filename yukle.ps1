# KIRO2 İçerik Yükleme PowerShell Script
# ======================================

Write-Host "============================================" -ForegroundColor Green
Write-Host "KIRO2 ACİL İÇERİK YÜKLEME" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Çalışma dizini
$workDir = "C:\Users\husey\kiro2"
Set-Location $workDir

# 1. PostgreSQL Kontrolü
Write-Host "[1/5] PostgreSQL servisi kontrol ediliyor..." -ForegroundColor Cyan
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($pgService) {
    if ($pgService.Status -ne "Running") {
        Write-Host "PostgreSQL başlatılıyor..." -ForegroundColor Yellow
        Start-Service $pgService.Name
        Start-Sleep -Seconds 3
    }
    Write-Host "✅ PostgreSQL çalışıyor" -ForegroundColor Green
} else {
    Write-Host "⚠️ PostgreSQL servisi bulunamadı" -ForegroundColor Red
}

# 2. Veritabanı oluştur
Write-Host ""
Write-Host "[2/5] Veritabanı kontrol ediliyor..." -ForegroundColor Cyan
$env:PGPASSWORD = "postgres"
& psql -U postgres -c "CREATE DATABASE kiro2;" 2>$null
Write-Host "✅ Veritabanı hazır" -ForegroundColor Green

# 3. SQL yükle
Write-Host ""
Write-Host "[3/5] SQL dosyası yükleniyor..." -ForegroundColor Cyan
if (Test-Path "emergency_content.sql") {
    & psql -U postgres -d kiro2 -f emergency_content.sql | Out-Null
    Write-Host "✅ 50 soru yüklendi" -ForegroundColor Green
} else {
    Write-Host "❌ emergency_content.sql bulunamadı" -ForegroundColor Red
}

# 4. Python script çalıştır
Write-Host ""
Write-Host "[4/5] Python loader çalıştırılıyor..." -ForegroundColor Cyan
if (Test-Path "load_emergency_content.py") {
    py load_emergency_content.py
} else {
    Write-Host "⚠️ Python loader bulunamadı" -ForegroundColor Yellow
}

# 5. İstatistikler
Write-Host ""
Write-Host "[5/5] İstatistikler..." -ForegroundColor Cyan
$result = & psql -U postgres -d kiro2 -t -c "SELECT COUNT(*) FROM questions;" 2>$null
if ($result) {
    $count = [int]$result.Trim()
    Write-Host "📊 Toplam soru sayısı: $count" -ForegroundColor Green

    if ($count -ge 50) {
        Write-Host "✅ Platform test için hazır!" -ForegroundColor Green
    } elseif ($count -ge 20) {
        Write-Host "🟡 Minimum içerik var, daha fazla eklenmeli" -ForegroundColor Yellow
    } else {
        Write-Host "🔴 Yetersiz içerik, acil ekleme gerekli" -ForegroundColor Red
    }
}

# Backend scriptleri kontrol
Write-Host ""
Write-Host "Backend scriptleri kontrol ediliyor..." -ForegroundColor Cyan
$backendScripts = @(
    "backend\scripts\production_seed.py",
    "backend\scripts\populate_question_bank.py",
    "backend\scripts\osym_question_extractor.py"
)

foreach ($script in $backendScripts) {
    if (Test-Path $script) {
        Write-Host "  ✅ $script" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $script bulunamadı" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "İŞLEM TAMAMLANDI!" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 SONRAKİ ADIMLAR:" -ForegroundColor Cyan
Write-Host "1. Backend başlat: cd backend && uvicorn main:app --reload"
Write-Host "2. Frontend başlat: cd frontend && npm start"
Write-Host "3. Admin panel: http://localhost:3000/admin"
Write-Host "   Email: admin@kiro2.com"
Write-Host "   Şifre: admin123"
Write-Host ""

Read-Host "Devam etmek için Enter'a basın"
