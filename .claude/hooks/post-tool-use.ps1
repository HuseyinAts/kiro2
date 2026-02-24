# PostToolUse Hook - Verification Feedback Loop (Silent Mode)
# Successful checks produce zero output. Errors/warnings print and exit 2.
# Input: JSON via stdin from Claude Code (tool_input.file_path)

$ErrorActionPreference = "Continue"
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName

# Read hook input from stdin JSON (non-blocking, 500ms timeout)
$ToolName = ""
$FilePath = ""
try {
    $stream = [Console]::OpenStandardInput()
    $buffer = New-Object byte[] 65536
    $asyncResult = $stream.BeginRead($buffer, 0, $buffer.Length, $null, $null)
    if ($asyncResult.AsyncWaitHandle.WaitOne(500)) {
        $bytesRead = $stream.EndRead($asyncResult)
        if ($bytesRead -gt 0) {
            $json = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $bytesRead)
            $hookInput = $json | ConvertFrom-Json
            $ToolName = $hookInput.tool_name
            $FilePath = $hookInput.tool_input.file_path
        }
    }
} catch {}

# If no file path, nothing to check — exit clean
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

# 2. REWARD HACKING DETECTION (skip .claude/ infra files to avoid self-match)
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

$isInfraFile = $FilePath -match '[\\/]\.claude[\\/]'
if (-not $isInfraFile -and $FilePath -and (Test-Path $FilePath)) {
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

# 4. FINAL VERDICT - errors go to stderr (fed back to Claude)
if ($HasErrors) {
    [Console]::Error.WriteLine("[FAIL] VERIFICATION FAILED")
    foreach ($err in $ErrorMessages) {
        [Console]::Error.WriteLine("  - $err")
    }
    exit 2
}

exit 0
