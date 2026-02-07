# KIRO2 Development Helper Script
# Quick commands for daily development

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Ensure we're in project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Activate virtual environment if not already active
if (-not $env:VIRTUAL_ENV) {
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .venv\Scripts\Activate.ps1
    }
}

switch ($Command.ToLower()) {
    "help" {
        Write-Host "KIRO2 Development Helper" -ForegroundColor Cyan
        Write-Host "========================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\scripts\dev.ps1 <command> [args]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Green
        Write-Host "  install        - Install all dependencies with uv"
        Write-Host "  update         - Update all dependencies"
        Write-Host "  format         - Format code with ruff"
        Write-Host "  lint           - Run ruff linter"
        Write-Host "  fix            - Fix linting issues automatically"
        Write-Host "  check          - Run all checks (lint, type, test)"
        Write-Host "  test           - Run tests"
        Write-Host "  test-fast      - Run fast tests only"
        Write-Host "  test-cov       - Run tests with coverage"
        Write-Host "  mypy           - Run type checking"
        Write-Host "  pre-commit     - Run pre-commit hooks"
        Write-Host "  clean          - Clean temporary files"
        Write-Host "  backend        - Start backend server"
        Write-Host "  frontend       - Start frontend dev server"
        Write-Host "  db-upgrade     - Run database migrations"
        Write-Host "  db-downgrade   - Rollback database migration"
        Write-Host "  redis          - Start Redis server"
        Write-Host "  postgres       - Start PostgreSQL server"
        Write-Host "  services       - Start all services (postgres, redis)"
        Write-Host ""
    }
    
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        uv pip sync pyproject.toml
        uv pip install -e ".[dev]"
        Write-Host "✓ Dependencies installed" -ForegroundColor Green
    }
    
    "update" {
        Write-Host "Updating dependencies..." -ForegroundColor Yellow
        uv pip install --upgrade -r pyproject.toml
        Write-Host "✓ Dependencies updated" -ForegroundColor Green
    }
    
    "format" {
        Write-Host "Formatting code with ruff..." -ForegroundColor Yellow
        ruff format backend/
        Write-Host "✓ Code formatted" -ForegroundColor Green
    }
    
    "lint" {
        Write-Host "Running ruff linter..." -ForegroundColor Yellow
        ruff check backend/
    }
    
    "fix" {
        Write-Host "Fixing linting issues..." -ForegroundColor Yellow
        ruff check backend/ --fix
        Write-Host "✓ Issues fixed" -ForegroundColor Green
    }
    
    "check" {
        Write-Host "Running all checks..." -ForegroundColor Yellow
        
        Write-Host "`n→ Linting..." -ForegroundColor Cyan
        ruff check backend/
        
        Write-Host "`n→ Type checking..." -ForegroundColor Cyan
        mypy backend/ --config-file pyproject.toml
        
        Write-Host "`n→ Testing..." -ForegroundColor Cyan
        pytest backend/tests/ --tb=short -x
        
        Write-Host "`n✓ All checks complete" -ForegroundColor Green
    }
    
    "test" {
        Write-Host "Running tests..." -ForegroundColor Yellow
        Set-Location backend
        if ($Args) {
            pytest $Args
        } else {
            pytest --tb=short -v
        }
        Set-Location ..
    }
    
    "test-fast" {
        Write-Host "Running fast tests..." -ForegroundColor Yellow
        Set-Location backend
        pytest -m "not slow" --tb=short -x
        Set-Location ..
    }
    
    "test-cov" {
        Write-Host "Running tests with coverage..." -ForegroundColor Yellow
        Set-Location backend
        pytest --cov=. --cov-report=term-missing --cov-report=html
        Set-Location ..
        Write-Host "✓ Coverage report generated in htmlcov/" -ForegroundColor Green
    }
    
    "mypy" {
        Write-Host "Running type checker..." -ForegroundColor Yellow
        mypy backend/ --config-file pyproject.toml
    }
    
    "pre-commit" {
        Write-Host "Running pre-commit hooks..." -ForegroundColor Yellow
        pre-commit run --all-files
    }
    
    "clean" {
        Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
        
        # Python cache
        Get-ChildItem -Path . -Include __pycache__,*.pyc,*.pyo -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        
        # Test and coverage
        Remove-Item -Path .coverage -Force -ErrorAction SilentlyContinue
        Remove-Item -Path htmlcov -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path .pytest_cache -Recurse -Force -ErrorAction SilentlyContinue
        
        # Ruff cache
        Remove-Item -Path .ruff_cache -Recurse -Force -ErrorAction SilentlyContinue
        
        # MyPy cache
        Remove-Item -Path .mypy_cache -Recurse -Force -ErrorAction SilentlyContinue
        
        Write-Host "✓ Cleaned temporary files" -ForegroundColor Green
    }
    
    "backend" {
        Write-Host "Starting backend server..." -ForegroundColor Yellow
        Set-Location backend
        uvicorn main:app --reload --port 8000 --host 0.0.0.0
    }
    
    "frontend" {
        Write-Host "Starting frontend dev server..." -ForegroundColor Yellow
        Set-Location frontend
        npm run dev -- --port 3001
    }
    
    "db-upgrade" {
        Write-Host "Running database migrations..." -ForegroundColor Yellow
        Set-Location backend
        alembic upgrade head
        Set-Location ..
        Write-Host "✓ Database migrated" -ForegroundColor Green
    }
    
    "db-downgrade" {
        Write-Host "Rolling back database migration..." -ForegroundColor Yellow
        Set-Location backend
        if ($Args) {
            alembic downgrade $Args[0]
        } else {
            alembic downgrade -1
        }
        Set-Location ..
        Write-Host "✓ Database rolled back" -ForegroundColor Green
    }
    
    "redis" {
        Write-Host "Starting Redis server on port 6379..." -ForegroundColor Yellow
        redis-server --port 6379
    }
    
    "postgres" {
        Write-Host "Starting PostgreSQL on port 5434..." -ForegroundColor Yellow
        # Adjust this command based on your PostgreSQL installation
        pg_ctl -D "C:\Program Files\PostgreSQL\14\data" -o "-p 5434" start
    }
    
    "services" {
        Write-Host "Starting all services..." -ForegroundColor Yellow
        
        # Start PostgreSQL in background
        Start-Process powershell -ArgumentList "pg_ctl -D 'C:\Program Files\PostgreSQL\14\data' -o '-p 5434' start" -NoNewWindow
        
        # Start Redis in background
        Start-Process redis-server -ArgumentList "--port 6379" -WindowStyle Hidden
        
        Write-Host "✓ Services started" -ForegroundColor Green
        Write-Host "  PostgreSQL: localhost:5434" -ForegroundColor Cyan
        Write-Host "  Redis: localhost:6379" -ForegroundColor Cyan
    }
    
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\scripts\dev.ps1 help' for usage" -ForegroundColor Yellow
    }
}