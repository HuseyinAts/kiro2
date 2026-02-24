# PostToolUse Hook - Verification Feedback Loop (Silent Mode)
# Successful checks produce zero output. Errors/warnings print and exit 2.
# Reads file path from env var CLAUDE_FILE_PATH (set by Claude Code)

param(
    [Parameter(Mandatory=$false)]
    [string]$ToolName = "",
    [Parameter(Mandatory=$false)]
    [string]$FilePath = ""
)

$ErrorActionPreference = "Continue"
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName

# Primary: env vars (no shell parsing issues)
if (-not $FilePath) { $FilePath = $env:CLAUDE_FILE_PATH }
if (-not $ToolName) { $ToolName = $env:CLAUDE_TOOL_USE_TOOL_NAME }

# If still no file path, nothing to check — exit clean
if (-not $FilePath) { exit 0 }

$HasErrors = $false
$ErrorMessages = @()

# 1. PYTHON FILE VERIFICATION (ruff + mypy) - Only for .py files that exist
if ($FilePath -match "\.py$" -and (Test-Path $FilePath)) {
    # Auto-format (silent)
    & ruff format "$FilePath" 2>&1 | Out-Null

    # Auto-fix lint issues (silent)
    & ruff check "$FilePath" --select=E,F,W --ignore=E501 --fix 2>&1 | Out-Null

    # Report remaining unfixable issues
    $ruffResult = & ruff check "$FilePath" --select=E,F,W --ignore=E501 2>&1
    $ruffExitCode = $LASTEXITCODE

    if ($ruffExitCode -ne 0 -and $ruffResult -match "error|Error") {
        Write-Host "[WARN] Ruff linting issues found (non-blocking)" -ForegroundColor Yellow
        Write-Host $ruffResult -ForegroundColor Yellow
    }

    # Run mypy on the changed file
    $mypyResult = & mypy --ignore-missing-imports --no-error-summary --cache-dir="$ProjectRoot\backend\.mypy_cache" "$FilePath" 2>&1
    $mypyExitCode = $LASTEXITCODE

    if ($mypyExitCode -ne 0 -and $mypyResult -match "error:") {
        Write-Host "[WARN] MyPy found type errors (non-blocking)" -ForegroundColor Yellow
    }
}

# 2. REWARD HACKING DETECTION
$RewardHackingPatterns = @(
    'ASSERT_TRUE\s*\(\s*true\s*\)',
    'ASSERT_TRUE\s*\(\s*True\s*\)',
    'assert\s+True\s*$',
    'assert\s+true\s*$',
    'echo\s+[\x27\x22]?Success[\x27\x22]?\s*$',
    'print\s*\(\s*[\x27\x22]?Success[\x27\x22]?\s*\)',
    '# TODO: implement',
    '# FIXME: fake',
    'pass\s*#\s*placeholder',
    'return\s+None\s*#\s*stub'
)

if ($FilePath -and (Test-Path $FilePath)) {
    $FileContent = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue

    foreach ($pattern in $RewardHackingPatterns) {
        if ($FileContent -match $pattern) {
            Write-Host "[FAIL] REWARD HACKING DETECTED: Pattern '$pattern' found!" -ForegroundColor Red
            $HasErrors = $true
            $ErrorMessages += "Reward Hacking: Suspicious pattern '$pattern' detected in $FilePath"
        }
    }
}

# 3. TEST FILE INTEGRITY CHECK
if ($FilePath -match "test.*\.py$" -or $FilePath -match "\.test\.(ts|tsx)$") {
    if ($FilePath -and (Test-Path $FilePath)) {
        $TestContent = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue

        if ($TestContent -match "def\s+test_\w+\([^)]*\):\s*\n\s*(pass|\.\.\.)\s*\n") {
            Write-Host "[FAIL] Empty test body detected! Tests must have assertions." -ForegroundColor Red
            $HasErrors = $true
            $ErrorMessages += "Test Integrity: Empty test body in $FilePath"
        }

        if ($TestContent -match "@pytest\.mark\.skip\s*\n" -and $TestContent -notmatch "@pytest\.mark\.skip\s*\(\s*reason\s*=") {
            Write-Host "[WARN] Skipped test without reason - consider adding reason" -ForegroundColor Yellow
        }
    }
}

# 4. FINAL VERDICT - only output on failure
if ($HasErrors) {
    Write-Host "" -ForegroundColor Red
    Write-Host "[FAIL] VERIFICATION FAILED" -ForegroundColor Red
    foreach ($err in $ErrorMessages) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    exit 2
}

exit 0
