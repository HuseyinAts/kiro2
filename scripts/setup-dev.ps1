# KIRO2 Development Environment Setup Script (Windows)
# Prerequisites: Python 3.11+ installed

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "KIRO2 Development Environment Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1 | Out-String
    if ($pythonVersion -match "Python 3\.(1[1-9]|[2-9][0-9])") {
        Write-Host "✓ Python version OK: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Python 3.11+ required. Current: $pythonVersion" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Python not found in PATH" -ForegroundColor Red
    exit 1
}

# Install uv if not present
Write-Host "`nChecking for uv..." -ForegroundColor Yellow
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Host "Installing uv package manager..." -ForegroundColor Yellow
    
    # Install using pip first
    pip install --upgrade uv
    
    # Alternative: Install using PowerShell
    # irm https://astral.sh/uv/install.ps1 | iex
    
    Write-Host "✓ uv installed successfully" -ForegroundColor Green
} else {
    Write-Host "✓ uv already installed" -ForegroundColor Green
}

# Create virtual environment with uv
Write-Host "`nSetting up Python virtual environment..." -ForegroundColor Yellow
try {
    Set-Location -Path "$PSScriptRoot\.."
} catch {
    Write-Host "Error changing directory" -ForegroundColor Red
    exit 1
}

if (Test-Path .venv) {
    Write-Host "Virtual environment already exists" -ForegroundColor Yellow
    $response = Read-Host "Do you want to recreate it? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Remove-Item -Path .venv -Recurse -Force
        uv venv --python 3.11
        Write-Host "✓ Virtual environment recreated" -ForegroundColor Green
    }
} else {
    uv venv --python 3.11
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Install dependencies with uv
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
uv pip sync pyproject.toml
Write-Host "✓ Python dependencies installed" -ForegroundColor Green

# Install development dependencies
Write-Host "`nInstalling development dependencies..." -ForegroundColor Yellow
uv pip install -e ".[dev]"
Write-Host "✓ Development dependencies installed" -ForegroundColor Green

# Install pre-commit hooks
Write-Host "`nSetting up pre-commit hooks..." -ForegroundColor Yellow
$precommitInstalled = Get-Command pre-commit -ErrorAction SilentlyContinue
if ($precommitInstalled) {
    pre-commit install
    pre-commit install --hook-type commit-msg
    Write-Host "✓ Pre-commit hooks installed" -ForegroundColor Green
} else {
    Write-Host "⚠ pre-commit not found, skipping hook installation" -ForegroundColor Yellow
}

# Setup PostgreSQL connection
Write-Host "`nDatabase Configuration:" -ForegroundColor Yellow
Write-Host "  PostgreSQL should be running on port 5434" -ForegroundColor Cyan
Write-Host "  Redis should be running on port 6379" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path backend\.env)) {
    Write-Host "`nCreating .env file from template..." -ForegroundColor Yellow
    if (Test-Path backend\.env.example) {
        Copy-Item backend\.env.example backend\.env
        Write-Host "✓ .env file created (please update with your credentials)" -ForegroundColor Green
    } else {
        Write-Host "⚠ No .env.example found, creating minimal .env..." -ForegroundColor Yellow
        @"
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/kiro2

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys (add your keys)
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Environment
ENVIRONMENT=development
DEBUG=true
"@ | Out-File -FilePath backend\.env -Encoding UTF8
        Write-Host "✓ Minimal .env file created" -ForegroundColor Green
    }
}

# Frontend setup
Write-Host "`nSetting up frontend..." -ForegroundColor Yellow
Set-Location frontend
if (Test-Path node_modules) {
    Write-Host "Node modules already exist" -ForegroundColor Yellow
} else {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
}
Set-Location ..

# Generate TypeScript types from OpenAPI
Write-Host "`nGenerating TypeScript types..." -ForegroundColor Yellow
if (Test-Path scripts\generate-types.ps1) {
    & scripts\generate-types.ps1
    Write-Host "✓ TypeScript types generated" -ForegroundColor Green
} else {
    Write-Host "⚠ Type generation script not found" -ForegroundColor Yellow
}

# Run initial tests
Write-Host "`nRunning initial tests..." -ForegroundColor Yellow
Set-Location backend
$testResult = pytest --tb=short --maxfail=5 -x 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All tests passed" -ForegroundColor Green
} else {
    Write-Host "⚠ Some tests failed (this might be expected for first setup)" -ForegroundColor Yellow
}
Set-Location ..

# Final instructions
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update backend\.env with your credentials" -ForegroundColor White
Write-Host "2. Start PostgreSQL on port 5434" -ForegroundColor White
Write-Host "3. Start Redis on port 6379" -ForegroundColor White
Write-Host "4. Run database migrations: cd backend && alembic upgrade head" -ForegroundColor White
Write-Host "5. Start backend: cd backend && uvicorn main:app --reload --port 8000" -ForegroundColor White
Write-Host "6. Start frontend: cd frontend && npm run dev -- --port 3001" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  uv pip list              # List installed packages" -ForegroundColor White
Write-Host "  ruff check backend/      # Run linter" -ForegroundColor White
Write-Host "  ruff format backend/     # Format code" -ForegroundColor White
Write-Host "  pre-commit run --all     # Run all pre-commit hooks" -ForegroundColor White
Write-Host "  pytest backend/tests/    # Run tests" -ForegroundColor White
Write-Host ""