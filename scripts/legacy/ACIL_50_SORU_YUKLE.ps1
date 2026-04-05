# KIRO2 - ACİL 50 SORU YÜKLEME
# ================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "KIRO2 - ACİL 50 SORU YÜKLEME" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

$workDir = "C:\Users\husey\kiro2"
Set-Location $workDir

# ADIM 1: PostgreSQL Kontrol
Write-Host "[1/3] PostgreSQL kontrol ediliyor..." -ForegroundColor Cyan
$pgRunning = $false

# Docker PostgreSQL kontrol
try {
    $dockerCheck = docker ps --filter "name=postgres" --format "{{.Names}}" 2>$null
    if ($dockerCheck -match "postgres") {
        Write-Host "  PostgreSQL (Docker) calisiyor" -ForegroundColor Green
        $pgRunning = $true
    }
} catch {}

if (-not $pgRunning) {
    Write-Host "  HATA: PostgreSQL bulunamadi!" -ForegroundColor Red
    exit 1
}

# ADIM 2: Veritabanını sorular tablosuna dönüştür
Write-Host ""
Write-Host "[2/3] emergency_content.sql dosyasi sorular tablosuna donusturuluyor..." -ForegroundColor Cyan

if (Test-Path "emergency_content.sql") {
    # SQL dosyasını oku
    $sqlContent = Get-Content "emergency_content.sql" -Raw -Encoding UTF8

    # questions -> sorular dönüşümü yap
    $sqlContent = $sqlContent -replace 'CREATE TABLE IF NOT EXISTS questions', 'CREATE TABLE IF NOT EXISTS sorular'
    $sqlContent = $sqlContent -replace 'INSERT INTO questions', 'INSERT INTO sorular'

    # Sütun isimlerini Türkçeleştir
    $sqlContent = $sqlContent -replace 'question_text', 'metin'
    $sqlContent = $sqlContent -replace 'option_a', 'secenek_a'
    $sqlContent = $sqlContent -replace 'option_b', 'secenek_b'
    $sqlContent = $sqlContent -replace 'option_c', 'secenek_c'
    $sqlContent = $sqlContent -replace 'option_d', 'secenek_d'
    $sqlContent = $sqlContent -replace 'option_e', 'secenek_e'
    $sqlContent = $sqlContent -replace 'correct_answer', 'dogru_cevap'
    $sqlContent = $sqlContent -replace 'explanation', 'aciklama'
    $sqlContent = $sqlContent -replace 'exam_type', 'sinav_tipi'
    $sqlContent = $sqlContent -replace 'subject_area', 'konu'
    $sqlContent = $sqlContent -replace 'difficulty', 'zorluk'
    $sqlContent = $sqlContent -replace 'is_active', 'aktif'
    $sqlContent = $sqlContent -replace 'created_at', 'olusturma_tarihi'
    $sqlContent = $sqlContent -replace 'updated_at', 'guncelleme_tarihi'

    # Geçici dosyaya yaz
    $sqlContent | Out-File "emergency_sorular.sql" -Encoding UTF8

    Write-Host "  SQL dosyasi donusturuldu" -ForegroundColor Green
} else {
    Write-Host "  HATA: emergency_content.sql bulunamadi!" -ForegroundColor Red
    exit 1
}

# ADIM 3: SQL dosyasını yükle
Write-Host ""
Write-Host "[3/3] Sorular veritabanina yukleniyor..." -ForegroundColor Cyan

$env:PGPASSWORD = "1470"

# psql komutu ile yükle
$output = & psql -U postgres -h localhost -p 5434 -d turkiye_sinav_db -f emergency_sorular.sql 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  50 soru basariyla yuklendi!" -ForegroundColor Green
} else {
    Write-Host "  HATA: SQL yukleme basarisiz!" -ForegroundColor Red
    Write-Host "  Detay: $output" -ForegroundColor Yellow
}

# Soru sayısını kontrol et
Write-Host ""
Write-Host "Veritabanindaki toplam soru sayisi kontrol ediliyor..." -ForegroundColor Cyan

cd backend
$questionCount = py -c "import asyncio; from count_questions import count_all_questions; print(asyncio.run(count_all_questions()))" 2>$null
cd ..

if ($questionCount) {
    Write-Host "  Toplam soru sayisi: $questionCount" -ForegroundColor Green
} else {
    Write-Host "  Soru sayisi alinamadi" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "TAMAMLANDI!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Simdi API'yi test edebilirsiniz:" -ForegroundColor Cyan
Write-Host "  curl http://localhost:8000/api/v1/questions?limit=5" -ForegroundColor White
Write-Host ""

# Geçici dosyayı temizle
if (Test-Path "emergency_sorular.sql") {
    Remove-Item "emergency_sorular.sql" -Force
}
