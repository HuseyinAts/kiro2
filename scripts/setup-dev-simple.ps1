# KIRO2 Development Environment Setup Script (Simplified)
# Prerequisites: Python 3.11+ installed

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "KIRO2 Development Environment Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Install uv
Write-Host "`nInstalling uv package manager..." -ForegroundColor Yellow
pip install --upgrade uv
if ($LASTEXITCODE -eq 0) {
    Write-Host "uv installed successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to install uv" -ForegroundColor Red
    exit 1
}

# Create venv
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
if (Test-Path .venv) {
    Write-Host "Removing existing .venv..." -ForegroundColor Yellow
    Remove-Item -Path .venv -Recurse -Force
}
python -m venv .venv
Write-Host "Virtual environment created" -ForegroundColor Green

# Activate venv
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install backend dependencies
Write-Host "`nInstalling backend dependencies..." -ForegroundColor Yellow
cd backend
if (Test-Path requirements.txt) {
    pip install -r requirements.txt
    Write-Host "Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "requirements.txt not found" -ForegroundColor Red
}

# Install ruff
Write-Host "`nInstalling ruff..." -ForegroundColor Yellow
pip install ruff
Write-Host "ruff installed" -ForegroundColor Green

# Install pre-commit
Write-Host "`nInstalling pre-commit..." -ForegroundColor Yellow
pip install pre-commit
pre-commit install
Write-Host "pre-commit hooks installed" -ForegroundColor Green

# Go back to root
cd ..

# Install frontend dependencies
Write-Host "`nInstalling frontend dependencies..." -ForegroundColor Yellow
cd frontend
npm install
Write-Host "Frontend dependencies installed" -ForegroundColor Green
cd ..

# Create .env if not exists
if (-not (Test-Path backend\.env)) {
    Write-Host "`nCreating backend\.env file..." -ForegroundColor Yellow
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

# API Keys
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Environment
ENVIRONMENT=development
DEBUG=true
"@ | Out-File -FilePath backend\.env -Encoding UTF8
    Write-Host ".env file created" -ForegroundColor Green
}

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update backend\.env with your credentials" -ForegroundColor White
Write-Host "2. Start PostgreSQL on port 5434" -ForegroundColor White
Write-Host "3. Start Redis on port 6379" -ForegroundColor White
Write-Host "4. Run migrations: cd backend && alembic upgrade head" -ForegroundColor White
Write-Host "5. Start backend: cd backend && uvicorn main:app --reload" -ForegroundColor White
Write-Host "6. Start frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  ruff check backend/      # Run linter" -ForegroundColor White
Write-Host "  ruff format backend/     # Format code" -ForegroundColor White
Write-Host "  pre-commit run --all     # Run pre-commit hooks" -ForegroundColor White
Write-Host ""