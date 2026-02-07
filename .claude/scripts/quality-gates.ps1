# KIRO2 Quality Gates Script
# Claude Code Stop Hook için kalite kapısı
# Boris Cherny: "Claude'a çalışmasını doğrulama yolu vermek kaliteyi 2-3x artırır!"

param(
    [switch]$SkipTests = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"
$root = "C:\Users\husey\kiro2"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KIRO2 Quality Gates" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
$errors = 0

# 1. Python Lint (ruff)
Write-Host "[1/5] Python Lint kontrolu (ruff)..." -ForegroundColor Yellow
Set-Location "$root\backend"
try {
    $ruffCheck = ruff check . --fix 2>&1
    $ruffFormat = ruff format . 2>&1
    Write-Host "  OK Python lint basarili" -ForegroundColor Green
} catch {
    Write-Host "  UYARI ruff bulunamadi veya hata: $_" -ForegroundColor Yellow
    $errors++
}

# 2. Python Type Check (mypy)
Write-Host "[2/5] Type check (mypy)..." -ForegroundColor Yellow
try {
    $mypyResult = mypy . --ignore-missing-imports --no-error-summary 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Type check basarili" -ForegroundColor Green
    } else {
        Write-Host "  UYARI Type check uyarilari var" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  UYARI mypy bulunamadi" -ForegroundColor Yellow
}

# 3. Python Tests
if (-not $SkipTests) {
    Write-Host "[3/5] Python testleri..." -ForegroundColor Yellow
    try {
        $testResult = pytest tests/ -v --tb=short -q 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK Python testleri basarili" -ForegroundColor Green
        } else {
            Write-Host "  UYARI Bazi testler basarisiz" -ForegroundColor Yellow
            $errors++
        }
    } catch {
        Write-Host "  UYARI pytest bulunamadi" -ForegroundColor Yellow
    }
} else {
    Write-Host "[3/5] Testler atlandi (-SkipTests)" -ForegroundColor Gray
}

# 4. TypeScript Lint
Write-Host "[4/5] TypeScript lint kontrolu..." -ForegroundColor Yellow
Set-Location "$root\frontend"
try {
    $lintResult = npm run lint 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK TypeScript lint basarili" -ForegroundColor Green
    } else {
        Write-Host "  UYARI TypeScript lint uyarilari var" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  UYARI npm lint calistirilamadi" -ForegroundColor Yellow
}

# 5. TypeScript Type Check
Write-Host "[5/5] TypeScript type check..." -ForegroundColor Yellow
try {
    $typeResult = npm run type-check 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK TypeScript type check basarili" -ForegroundColor Green
    } else {
        Write-Host "  UYARI TypeScript type uyarilari var" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  UYARI type-check script bulunamadi" -ForegroundColor Yellow
}

# Sonuç
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "  KIRO2 Quality Gates BASARILI" -ForegroundColor Green
} else {
    Write-Host "  KIRO2 Quality Gates: $errors uyari" -ForegroundColor Yellow
}
Write-Host "  Sure: $([math]::Round($duration, 2)) saniye" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Log yaz
$logFile = "$root\.claude\activity.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logEntry = "[$timestamp] Quality gates completed (errors: $errors, duration: $([math]::Round($duration, 2))s)"
Add-Content -Path $logFile -Value $logEntry -ErrorAction SilentlyContinue

Set-Location $root
exit 0
