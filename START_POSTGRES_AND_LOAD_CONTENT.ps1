# KIRO2 - Start PostgreSQL and Load Content
# ==========================================
# This script starts PostgreSQL and loads emergency question content

param(
    [switch]$SkipContentLoad = $false
)

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "KIRO2 - PostgreSQL Start & Content Load" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Change to kiro2 directory
$workDir = "C:\Users\husey\kiro2"
Set-Location $workDir
Write-Host "Working Directory: $workDir" -ForegroundColor Cyan
Write-Host ""

# STEP 1: Check and start PostgreSQL
Write-Host "[1/4] Checking PostgreSQL..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

# Try Docker first
$dockerRunning = $false
try {
    $dockerCheck = docker ps --filter "name=postgres" --format "{{.Names}}" 2>$null
    if ($dockerCheck -match "postgres") {
        Write-Host "✅ PostgreSQL (Docker) is already running" -ForegroundColor Green
        $dockerRunning = $true
    } else {
        Write-Host "Starting PostgreSQL via Docker..." -ForegroundColor Yellow
        docker-compose up -d postgres
        Start-Sleep -Seconds 5

        $dockerCheck = docker ps --filter "name=postgres" --format "{{.Names}}" 2>$null
        if ($dockerCheck -match "postgres") {
            Write-Host "✅ PostgreSQL (Docker) started successfully" -ForegroundColor Green
            $dockerRunning = $true
        }
    }
} catch {
    Write-Host "⚠️ Docker not available, checking Windows service..." -ForegroundColor Yellow
}

# If Docker didn't work, try Windows service
if (-not $dockerRunning) {
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($pgService) {
        if ($pgService.Status -ne "Running") {
            Write-Host "Starting PostgreSQL Windows service..." -ForegroundColor Yellow
            Start-Service $pgService.Name
            Start-Sleep -Seconds 3
        }
        Write-Host "✅ PostgreSQL (Windows Service) is running" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL not found (Docker or Windows Service)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install PostgreSQL or start Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""

# STEP 2: Verify database connection
Write-Host "[2/4] Verifying database connection..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

$env:PGPASSWORD = "1470"  # kiro2 database password
$dbCheck = & psql -U postgres -h localhost -p 5432 -d kiro2 -c "SELECT 1;" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database connection successful" -ForegroundColor Green
} else {
    Write-Host "⚠️ Database 'kiro2' not found, creating..." -ForegroundColor Yellow
    & psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE kiro2;" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database 'kiro2' created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create database" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# STEP 3: Check if content loading is needed
if ($SkipContentLoad) {
    Write-Host "[3/4] Content loading skipped (parameter -SkipContentLoad)" -ForegroundColor Yellow
} else {
    Write-Host "[3/4] Checking question content..." -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Gray

    # Count existing questions
    cd backend
    $questionCount = py -c "import sys; sys.path.insert(0, '.'); from count_questions import count_all_questions; print(count_all_questions())" 2>$null
    cd ..

    if ($questionCount -and [int]$questionCount -gt 10) {
        Write-Host "✅ Database has $questionCount questions" -ForegroundColor Green
        Write-Host "Content loading not needed" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Database has few questions ($questionCount)" -ForegroundColor Yellow
        Write-Host "Loading emergency content..." -ForegroundColor Yellow
        Write-Host ""

        # Check for emergency SQL file
        if (Test-Path "emergency_content.sql") {
            Write-Host "Loading emergency_content.sql..." -ForegroundColor Cyan
            $env:PGPASSWORD = "1470"
            & psql -U postgres -h localhost -p 5432 -d kiro2 -f emergency_content.sql 2>&1 | Select-String -Pattern "INSERT|COPY" | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            Write-Host "✅ Emergency SQL loaded" -ForegroundColor Green
        }

        # Check for Python content loader
        if (Test-Path "backend\load_emergency_content.py") {
            Write-Host "Running Python content loader..." -ForegroundColor Cyan
            cd backend
            py load_emergency_content.py
            cd ..
        } elseif (Test-Path "backend\generate_questions_simple.py") {
            Write-Host "Running question generator..." -ForegroundColor Cyan
            cd backend
            py generate_questions_simple.py
            cd ..
        }
    }
}

Write-Host ""

# STEP 4: Verify final state
Write-Host "[4/4] Final verification..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

# Check PostgreSQL status
if ($dockerRunning) {
    $pgStatus = docker ps --filter "name=postgres" --format "Status: {{.Status}}"
    Write-Host "PostgreSQL (Docker): $pgStatus" -ForegroundColor Green
} else {
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($pgService) {
        Write-Host "PostgreSQL (Service): $($pgService.Status)" -ForegroundColor Green
    }
}

# Check Redis
try {
    $redisCheck = docker ps --filter "name=redis" --format "{{.Names}}" 2>$null
    if ($redisCheck -match "redis") {
        Write-Host "Redis (Docker): Running" -ForegroundColor Green
    } else {
        Write-Host "Redis: Not running (optional)" -ForegroundColor Gray
    }
} catch {}

# Count questions
cd backend
$finalCount = py -c "import sys; sys.path.insert(0, '.'); from count_questions import count_all_questions; print(count_all_questions())" 2>$null
cd ..
if ($finalCount) {
    Write-Host "Question Bank: $finalCount questions" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "✅ SETUP COMPLETE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start backend:  cd backend; py main.py" -ForegroundColor White
Write-Host "2. Start frontend: npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Database connection:" -ForegroundColor Cyan
Write-Host "  Host: localhost" -ForegroundColor Gray
Write-Host "  Port: 5432" -ForegroundColor Gray
Write-Host "  Database: kiro2" -ForegroundColor Gray
Write-Host "  User: postgres" -ForegroundColor Gray
Write-Host "  Password: 1470" -ForegroundColor Gray
Write-Host ""
