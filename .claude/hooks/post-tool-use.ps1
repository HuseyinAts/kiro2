# PostToolUse Hook - Boris Cherny Verification Feedback Loop
# PURPOSE: %200-300 kalite artisi saglayan otomatik dogrulama
# TRIGGER: Her Edit/Write/Bash tool kullanimi sonrasi
# EXIT CODE 2: BLOCKS operation and feeds error back to Claude

param(
    [Parameter(Mandatory=$false)]
    [string]$ToolName = "",
    [Parameter(Mandatory=$false)]
    [string]$FilePath = ""
)

$ErrorActionPreference = "Continue"
$ProjectRoot = "C:\Users\husey\kiro2"

# Color output functions
function Write-Success { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[FAIL] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }

Write-Host ""
Write-Host "================================================================" -ForegroundColor Blue
Write-Host "  VERIFICATION FEEDBACK LOOP - PostToolUse Hook" -ForegroundColor Blue
Write-Host "  Boris Cherny: 'Kaliteyi %200-300 artiran dogrulama'" -ForegroundColor Blue
Write-Host "================================================================" -ForegroundColor Blue
Write-Host ""

$HasErrors = $false
$ErrorMessages = @()

# 1. PYTHON FILE VERIFICATION (ruff + mypy) - Only for .py files
if ($FilePath -match "\.py$") {
    Write-Info "Python dosya degisikligi tespit edildi: $FilePath"

    # Run ruff only on the changed file
    Write-Info "Ruff linter calistiriliyor (sadece degisen dosya)..."
    $ruffResult = & ruff check "$FilePath" --select=E,F,W --ignore=E501 2>&1
    $ruffExitCode = $LASTEXITCODE

    if ($ruffExitCode -ne 0 -and $ruffResult -match "error|Error") {
        Write-Warning "Ruff linting issues found (non-blocking)"
        Write-Host $ruffResult -ForegroundColor Yellow
        # Ruff errors are warnings, not blockers
    } else {
        Write-Success "Ruff linting passed"
    }

    # Run mypy only on the changed file
    Write-Info "MyPy type checker calistiriliyor (sadece degisen dosya)..."
    $mypyResult = & mypy --ignore-missing-imports --no-error-summary --cache-dir="$ProjectRoot\backend\.mypy_cache" "$FilePath" 2>&1
    $mypyExitCode = $LASTEXITCODE

    if ($mypyExitCode -ne 0 -and $mypyResult -match "error:") {
        Write-Warning "MyPy found type errors (non-blocking)"
    } else {
        Write-Success "MyPy type check passed"
    }
}

# 2. TYPESCRIPT/REACT FILE VERIFICATION - Skipped per-edit (too slow)
# Full tsc --noEmit runs on Stop hook / commit, not per-edit
if ($FilePath -match "\.(ts|tsx|js|jsx)$") {
    Write-Info "TypeScript/React dosya degisikligi: $FilePath (full tsc skipped for speed)"
    Write-Success "TypeScript per-file edit - full typecheck deferred to commit"
}

# 3. REWARD HACKING DETECTION (Test Sabotage)
Write-Info "Reward hacking pattern kontrolu..."

$RewardHackingPatterns = @(
    "ASSERT_TRUE\s*\(\s*true\s*\)",
    "ASSERT_TRUE\s*\(\s*True\s*\)",
    "assert\s+True\s*$",
    "assert\s+true\s*$",
    "echo\s+['\"]?Success['\"]?\s*$",
    "print\s*\(\s*['\"]Success['\"]\s*\)",
    "# TODO: implement",
    "# FIXME: fake",
    "pass\s*#\s*placeholder",
    "return\s+None\s*#\s*stub"
)

if ($FilePath -and (Test-Path $FilePath)) {
    $FileContent = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue

    foreach ($pattern in $RewardHackingPatterns) {
        if ($FileContent -match $pattern) {
            Write-Error "REWARD HACKING DETECTED: Pattern '$pattern' found!"
            $HasErrors = $true
            $ErrorMessages += "Reward Hacking: Suspicious pattern '$pattern' detected in $FilePath"
        }
    }

    if (-not $HasErrors) {
        Write-Success "No reward hacking patterns detected"
    }
}

# 4. TEST FILE INTEGRITY CHECK
if ($FilePath -match "test.*\.py$" -or $FilePath -match "\.test\.(ts|tsx)$") {
    Write-Info "Test dosyasi degisikligi - integrity check..."

    # Check for suspicious test patterns
    if ($FilePath -and (Test-Path $FilePath)) {
        $TestContent = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue

        # Check for empty test bodies
        if ($TestContent -match "def\s+test_\w+\([^)]*\):\s*\n\s*(pass|\.\.\.)\s*\n") {
            Write-Error "Empty test body detected! Tests must have assertions."
            $HasErrors = $true
            $ErrorMessages += "Test Integrity: Empty test body in $FilePath"
        }

        # Check for skipped tests without reason
        if ($TestContent -match "@pytest\.mark\.skip\s*\n" -and $TestContent -notmatch "@pytest\.mark\.skip\s*\(\s*reason\s*=") {
            Write-Warning "Skipped test without reason - consider adding reason"
        }

        if (-not $HasErrors) {
            Write-Success "Test integrity check passed"
        }
    }
}

# 5. FINAL VERDICT
Write-Host ""
Write-Host "================================================================" -ForegroundColor Blue
Write-Host "  VERIFICATION RESULT" -ForegroundColor Blue
Write-Host "================================================================" -ForegroundColor Blue

if ($HasErrors) {
    Write-Host ""
    Write-Error "VERIFICATION FAILED - Operation should be reviewed"
    Write-Host ""
    Write-Host "Errors found:" -ForegroundColor Red
    foreach ($err in $ErrorMessages) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "ACTION: Fix the issues above before proceeding." -ForegroundColor Yellow
    Write-Host ""

    # EXIT CODE 2 = BLOCKING ERROR (Daisy Stanton recommendation)
    # This will feed the error back to Claude for correction
    exit 2
} else {
    Write-Host ""
    Write-Success "All verification checks passed!"
    Write-Host ""
    Write-Host "Verification completed successfully." -ForegroundColor Green
    Write-Host ""

    # EXIT CODE 0 = SUCCESS
    exit 0
}
