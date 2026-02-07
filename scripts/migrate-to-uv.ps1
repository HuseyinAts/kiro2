# Quick migration script from pip/poetry to uv
# This script helps migrate existing Python projects to uv

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migrating KIRO2 from pip to uv" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend\requirements.txt")) {
    Write-Host "Error: backend/requirements.txt not found!" -ForegroundColor Red
    Write-Host "Please run this script from the KIRO2 project root." -ForegroundColor Red
    exit 1
}

# Step 1: Install uv globally if not present
Write-Host "Step 1: Checking uv installation..." -ForegroundColor Yellow
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    pip install --upgrade uv
    Write-Host "✓ uv installed" -ForegroundColor Green
} else {
    Write-Host "✓ uv already installed" -ForegroundColor Green
}

# Step 2: Backup existing virtual environment
Write-Host "`nStep 2: Backing up existing environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    $backupName = ".venv-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Rename-Item -Path .venv -NewName $backupName
    Write-Host "✓ Existing .venv backed up to $backupName" -ForegroundColor Green
} else {
    Write-Host "No existing .venv found" -ForegroundColor Yellow
}

# Step 3: Create new virtual environment with uv
Write-Host "`nStep 3: Creating new virtual environment with uv..." -ForegroundColor Yellow
uv venv --python 3.11
Write-Host "✓ New virtual environment created" -ForegroundColor Green

# Step 4: Activate the virtual environment
Write-Host "`nStep 4: Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Step 5: Install dependencies using uv
Write-Host "`nStep 5: Installing dependencies with uv..." -ForegroundColor Yellow
uv pip sync pyproject.toml
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Step 6: Install development dependencies
Write-Host "`nStep 6: Installing development dependencies..." -ForegroundColor Yellow
uv pip install -e ".[dev]"
Write-Host "✓ Development dependencies installed" -ForegroundColor Green

# Step 7: Verify installation
Write-Host "`nStep 7: Verifying installation..." -ForegroundColor Yellow
$packages = uv pip list 2>&1
$packageCount = ($packages | Measure-Object -Line).Lines
Write-Host "✓ $packageCount packages installed" -ForegroundColor Green

# Step 8: Install and configure ruff
Write-Host "`nStep 8: Setting up ruff..." -ForegroundColor Yellow
uv pip install ruff
Write-Host "✓ Ruff installed" -ForegroundColor Green

# Step 9: Run ruff to check code
Write-Host "`nStep 9: Running ruff check..." -ForegroundColor Yellow
ruff check backend/ --statistics
Write-Host "✓ Ruff check complete" -ForegroundColor Green

# Step 10: Install pre-commit hooks
Write-Host "`nStep 10: Installing pre-commit hooks..." -ForegroundColor Yellow
pre-commit install
pre-commit install --hook-type commit-msg
Write-Host "✓ Pre-commit hooks installed" -ForegroundColor Green

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What changed:" -ForegroundColor Yellow
Write-Host "  • pip → uv for package management" -ForegroundColor White
Write-Host "  • black/isort/flake8 → ruff for linting/formatting" -ForegroundColor White
Write-Host "  • Added pyproject.toml for unified configuration" -ForegroundColor White
Write-Host "  • Pre-commit hooks updated to use ruff" -ForegroundColor White
Write-Host ""
Write-Host "New commands to use:" -ForegroundColor Yellow
Write-Host "  uv pip install <package>     # Install a package" -ForegroundColor White
Write-Host "  uv pip list                  # List installed packages" -ForegroundColor White
Write-Host "  uv pip sync pyproject.toml   # Sync dependencies" -ForegroundColor White
Write-Host "  ruff check backend/          # Lint code" -ForegroundColor White
Write-Host "  ruff format backend/         # Format code" -ForegroundColor White
Write-Host "  pre-commit run --all         # Run all hooks" -ForegroundColor White
Write-Host ""
Write-Host "Old virtual environment backed up. You can delete it if everything works:" -ForegroundColor Yellow
Get-ChildItem -Path . -Filter ".venv-backup-*" | ForEach-Object {
    Write-Host "  Remove-Item -Path $($_.Name) -Recurse -Force" -ForegroundColor Gray
}
Write-Host ""