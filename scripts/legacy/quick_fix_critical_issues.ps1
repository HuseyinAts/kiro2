# Quick Fix Script for Critical Issues (P0)
# Türkiye Üniversite Sınavları Hazırlık Platformu
# Tarih: 19 Ekim 2025

Write-Host "🚀 Critical Issues Quick Fix Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  Warning: Not running as administrator. Some operations may fail." -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if a command exists
function Test-Command {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Function to check if a service is running
function Test-ServiceRunning {
    param($ServiceName)
    try {
        $service = docker ps --filter "name=$ServiceName" --format "{{.Names}}"
        return $service -eq $ServiceName
    } catch {
        return $false
    }
}

Write-Host "📋 Step 1: Checking Prerequisites" -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Green

# Check Docker
if (Test-Command docker) {
    Write-Host "✅ Docker is installed" -ForegroundColor Green
    docker --version
} else {
    Write-Host "❌ Docker is NOT installed" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Python
if (Test-Command python) {
    Write-Host "✅ Python is installed" -ForegroundColor Green
    python --version
} else {
    Write-Host "❌ Python is NOT installed" -ForegroundColor Red
    Write-Host "   Please install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check Node.js
if (Test-Command node) {
    Write-Host "✅ Node.js is installed" -ForegroundColor Green
    node --version
} else {
    Write-Host "⚠️  Node.js is NOT installed (optional for frontend)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Step 2: Starting PostgreSQL Database" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

if (Test-ServiceRunning "postgres") {
    Write-Host "✅ PostgreSQL is already running" -ForegroundColor Green
} else {
    Write-Host "🔄 Starting PostgreSQL..." -ForegroundColor Yellow
    try {
        docker-compose up -d postgres
        Start-Sleep -Seconds 5
        
        if (Test-ServiceRunning "postgres") {
            Write-Host "✅ PostgreSQL started successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to start PostgreSQL" -ForegroundColor Red
            Write-Host "   Try manually: docker-compose up -d postgres" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Error starting PostgreSQL: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📋 Step 3: Initializing Database" -ForegroundColor Green
Write-Host "---------------------------------" -ForegroundColor Green

if (Test-Path "backend/init_db.py") {
    Write-Host "🔄 Running database initialization..." -ForegroundColor Yellow
    try {
        Set-Location backend
        python init_db.py
        Set-Location ..
        Write-Host "✅ Database initialized successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error initializing database: $_" -ForegroundColor Red
        Write-Host "   Try manually: cd backend; python init_db.py" -ForegroundColor Yellow
        Set-Location ..
    }
} else {
    Write-Host "⚠️  init_db.py not found, skipping..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Step 4: Checking API Keys Configuration" -ForegroundColor Green
Write-Host "-------------------------------------------" -ForegroundColor Green

$envFile = ".env"
$envExample = ".env.example"

if (Test-Path $envFile) {
    Write-Host "✅ .env file exists" -ForegroundColor Green
    
    # Check for required API keys
    $envContent = Get-Content $envFile -Raw
    
    $youtubeKey = $envContent -match "YOUTUBE_API_KEY=.+"
    $openaiKey = $envContent -match "OPENAI_API_KEY=.+"
    $zemberekUrl = $envContent -match "ZEMBEREK_URL=.+"
    
    if ($youtubeKey) {
        Write-Host "✅ YOUTUBE_API_KEY is configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  YOUTUBE_API_KEY is NOT configured" -ForegroundColor Yellow
        Write-Host "   Add to .env: YOUTUBE_API_KEY=your_youtube_api_key" -ForegroundColor Yellow
    }
    
    if ($openaiKey) {
        Write-Host "✅ OPENAI_API_KEY is configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  OPENAI_API_KEY is NOT configured" -ForegroundColor Yellow
        Write-Host "   Add to .env: OPENAI_API_KEY=your_openai_api_key" -ForegroundColor Yellow
    }
    
    if ($zemberekUrl) {
        Write-Host "✅ ZEMBEREK_URL is configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  ZEMBEREK_URL is NOT configured" -ForegroundColor Yellow
        Write-Host "   Add to .env: ZEMBEREK_URL=http://localhost:8080" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .env file does NOT exist" -ForegroundColor Yellow
    
    if (Test-Path $envExample) {
        Write-Host "🔄 Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item $envExample $envFile
        Write-Host "✅ .env file created" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env and add your API keys" -ForegroundColor Yellow
    } else {
        Write-Host "❌ .env.example not found" -ForegroundColor Red
        Write-Host "   Please create .env manually with required API keys" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "📋 Step 5: Starting Zemberek NLP Service" -ForegroundColor Green
Write-Host "-----------------------------------------" -ForegroundColor Green

if (Test-ServiceRunning "zemberek-nlp") {
    Write-Host "✅ Zemberek NLP is already running" -ForegroundColor Green
} else {
    Write-Host "🔄 Starting Zemberek NLP..." -ForegroundColor Yellow
    try {
        docker-compose up -d zemberek-nlp
        Start-Sleep -Seconds 5
        
        if (Test-ServiceRunning "zemberek-nlp") {
            Write-Host "✅ Zemberek NLP started successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Zemberek NLP may not be configured in docker-compose.yml" -ForegroundColor Yellow
            Write-Host "   Check docker-compose.yml for zemberek-nlp service" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Error starting Zemberek NLP: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📋 Step 6: Starting Redis Cache" -ForegroundColor Green
Write-Host "--------------------------------" -ForegroundColor Green

if (Test-ServiceRunning "redis") {
    Write-Host "✅ Redis is already running" -ForegroundColor Green
} else {
    Write-Host "🔄 Starting Redis..." -ForegroundColor Yellow
    try {
        docker-compose up -d redis
        Start-Sleep -Seconds 3
        
        if (Test-ServiceRunning "redis") {
            Write-Host "✅ Redis started successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to start Redis" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error starting Redis: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📋 Step 7: Validating Services" -ForegroundColor Green
Write-Host "-------------------------------" -ForegroundColor Green

Write-Host "🔄 Running service validation..." -ForegroundColor Yellow

# Check if validation scripts exist
if (Test-Path "scripts/validate_external_services.py") {
    try {
        python scripts/validate_external_services.py
        Write-Host "✅ Service validation completed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Service validation failed: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Validation script not found, skipping..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Summary" -ForegroundColor Cyan
Write-Host "===========" -ForegroundColor Cyan
Write-Host ""

# Check overall status
$postgresRunning = Test-ServiceRunning "postgres"
$redisRunning = Test-ServiceRunning "redis"
$zemberekRunning = Test-ServiceRunning "zemberek-nlp"

Write-Host "Service Status:" -ForegroundColor White
Write-Host "  PostgreSQL:  $(if ($postgresRunning) { '✅ Running' } else { '❌ Not Running' })" -ForegroundColor $(if ($postgresRunning) { 'Green' } else { 'Red' })
Write-Host "  Redis:       $(if ($redisRunning) { '✅ Running' } else { '❌ Not Running' })" -ForegroundColor $(if ($redisRunning) { 'Green' } else { 'Red' })
Write-Host "  Zemberek:    $(if ($zemberekRunning) { '✅ Running' } else { '⚠️  Not Running' })" -ForegroundColor $(if ($zemberekRunning) { 'Green' } else { 'Yellow' })

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Edit .env file and add your API keys (YOUTUBE_API_KEY, OPENAI_API_KEY)" -ForegroundColor Yellow
Write-Host "  2. Start backend: cd backend && python main.py" -ForegroundColor Yellow
Write-Host "  3. Start frontend: cd frontend && npm run dev" -ForegroundColor Yellow
Write-Host "  4. Run validation: python scripts/validate_api_links.py" -ForegroundColor Yellow

Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor White
Write-Host "  - Comprehensive Review: COMPREHENSIVE_CODE_REVIEW_REPORT.md" -ForegroundColor Cyan
Write-Host "  - Quick Summary: CODE_REVIEW_SUMMARY.md" -ForegroundColor Cyan
Write-Host "  - Task 135 Report: reports/TASK_135_FINAL_REPORT.md" -ForegroundColor Cyan

Write-Host ""
Write-Host "Quick Fix Script Completed!" -ForegroundColor Green
Write-Host ""
