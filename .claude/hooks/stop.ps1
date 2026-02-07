# Stop Hook - Task Completion Verification
# PURPOSE: Claude yanit vermeyi bitirdiginde final dogrulama
# TRIGGER: Her Claude yaniti sonrasi (Stop event)
# EXIT CODE: Informational only (non-blocking)

param(
    [Parameter(Mandatory=$false)]
    [string]$TaskSummary = ""
)

$ErrorActionPreference = "Continue"
$ProjectRoot = "C:\Users\husey\kiro2"

# Color output functions
function Write-Success { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Info { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }

Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "  TASK COMPLETION VERIFICATION - Stop Hook" -ForegroundColor Magenta
Write-Host "  Final quality check before response delivery" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""

$Issues = @()
$Warnings = @()

# ============================================================
# 1. UNCOMMITTED CHANGES CHECK
# ============================================================

Write-Info "Checking for uncommitted changes..."

Push-Location $ProjectRoot

$gitStatus = git status --porcelain 2>$null
if ($gitStatus) {
    $changedFiles = ($gitStatus | Measure-Object).Count
    if ($changedFiles -gt 0) {
        $Warnings += "Uncommitted changes detected: $changedFiles file(s)"
        Write-Warning "Uncommitted changes: $changedFiles file(s)"
    }
} else {
    Write-Success "Working directory clean"
}

Pop-Location

# ============================================================
# 2. TODO LIST CHECK
# ============================================================

Write-Info "Checking todo list status..."

# Check if there's a todo list with incomplete items
# This would require integration with Claude's internal state
# For now, we just remind about it

Write-Info "Remember to check your todo list for incomplete items"

# ============================================================
# 3. BUILD STATUS CHECK (Quick)
# ============================================================

Write-Info "Quick build status check..."

# Check if last build was successful by looking for build artifacts
$FrontendDist = Join-Path $ProjectRoot "frontend\dist"
$BackendPyCache = Join-Path $ProjectRoot "backend\__pycache__"

if (Test-Path $FrontendDist) {
    $lastBuild = (Get-Item $FrontendDist).LastWriteTime
    $hoursSinceBuild = ((Get-Date) - $lastBuild).TotalHours

    if ($hoursSinceBuild -lt 24) {
        Write-Success "Frontend build recent ($('{0:N1}' -f $hoursSinceBuild) hours ago)"
    } else {
        $Warnings += "Frontend build may be stale ($('{0:N1}' -f $hoursSinceBuild) hours old)"
    }
} else {
    $Warnings += "No frontend build found"
}

# ============================================================
# 4. TEST STATUS CHECK
# ============================================================

Write-Info "Checking test coverage status..."

$CoverageFile = Join-Path $ProjectRoot "backend\coverage_reports\coverage.json"
if (Test-Path $CoverageFile) {
    try {
        $coverage = Get-Content $CoverageFile -Raw | ConvertFrom-Json
        $percent = $coverage.totals.percent_covered
        Write-Info "Backend coverage: $percent%"

        if ($percent -lt 50) {
            $Warnings += "Low test coverage: $percent%"
        }
    } catch {
        Write-Info "Could not parse coverage file"
    }
} else {
    Write-Info "No coverage report found"
}

# ============================================================
# 5. ERROR LOG CHECK
# ============================================================

Write-Info "Checking for recent errors..."

$ErrorLogs = @(
    (Join-Path $ProjectRoot "backend\logs\error.log"),
    (Join-Path $ProjectRoot "frontend\npm-debug.log")
)

foreach ($log in $ErrorLogs) {
    if (Test-Path $log) {
        $logAge = ((Get-Date) - (Get-Item $log).LastWriteTime).TotalMinutes
        if ($logAge -lt 30) {
            $Warnings += "Recent error log found: $log ($('{0:N0}' -f $logAge) min ago)"
        }
    }
}

# ============================================================
# SUMMARY
# ============================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "  COMPLETION SUMMARY" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""

if ($Issues.Count -gt 0) {
    Write-Host "Issues Found:" -ForegroundColor Red
    foreach ($issue in $Issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
    Write-Host ""
}

if ($Warnings.Count -gt 0) {
    Write-Host "Warnings:" -ForegroundColor Yellow
    foreach ($warn in $Warnings) {
        Write-Host "  - $warn" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($Issues.Count -eq 0 -and $Warnings.Count -eq 0) {
    Write-Success "All checks passed - task completed successfully"
} elseif ($Issues.Count -eq 0) {
    Write-Info "Task completed with $($Warnings.Count) warning(s)"
} else {
    Write-Warning "Task completed with $($Issues.Count) issue(s) requiring attention"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "  BORIS CHERNY REMINDER" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  'Verification feedback loops kaliteyi %200-300 artiriyor.'" -ForegroundColor Cyan
Write-Host "  - Her degisiklik sonrasi test calistir" -ForegroundColor White
Write-Host "  - Commit oncesi code review yap" -ForegroundColor White
Write-Host "  - Mock data yerine gercek veri kullan" -ForegroundColor White
Write-Host ""

# Stop hook is informational - always exit 0
exit 0
