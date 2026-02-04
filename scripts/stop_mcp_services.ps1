# MCP Services Stop Script
# Version: 1.0
# Description: Gracefully stops all MCP servers and optionally Docker services

param(
    [switch]$StopDocker,
    [switch]$Force
)

$ErrorActionPreference = "Continue"

# Color output functions
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }

# Configuration
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$PID_DIR = Join-Path $PROJECT_ROOT ".mcp_pids"
$LOG_DIR = Join-Path $PROJECT_ROOT "logs"

Write-Info "=== MCP Services Stop Script ==="
Write-Info "Project Root: $PROJECT_ROOT"
Write-Info ""

# Step 1: Stop MCP Servers
Write-Info "Step 1: Stopping MCP servers..."

if (Test-Path $PID_DIR) {
    $pidFiles = Get-ChildItem -Path $PID_DIR -Filter "*.pid"

    if ($pidFiles.Count -eq 0) {
        Write-Warning "No MCP service PID files found."
    } else {
        foreach ($pidFile in $pidFiles) {
            $serviceName = $pidFile.BaseName
            $pidContent = Get-Content $pidFile.FullName

            try {
                $process = Get-Process -Id $pidContent -ErrorAction Stop

                if ($Force) {
                    Stop-Process -Id $pidContent -Force
                    Write-Success "$serviceName stopped forcefully (PID: $pidContent)"
                } else {
                    Stop-Process -Id $pidContent
                    Write-Success "$serviceName stopped gracefully (PID: $pidContent)"
                }

                # Remove PID file
                Remove-Item -Path $pidFile.FullName -Force
            } catch {
                Write-Warning "$serviceName (PID: $pidContent) not found or already stopped"
                # Clean up stale PID file
                Remove-Item -Path $pidFile.FullName -Force -ErrorAction SilentlyContinue
            }
        }
    }
} else {
    Write-Warning "MCP PID directory not found: $PID_DIR"
}

# Step 2: Stop Docker Services (optional)
if ($StopDocker) {
    Write-Info ""
    Write-Info "Step 2: Stopping Docker services..."

    try {
        Push-Location $PROJECT_ROOT
        docker-compose down
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker services stopped successfully"
        } else {
            Write-Error "Failed to stop Docker services"
        }
        Pop-Location
    } catch {
        Write-Error "Docker error: $_"
    }
} else {
    Write-Info ""
    Write-Info "Skipping Docker services (use --StopDocker to stop Docker)"
}

# Step 3: Cleanup
Write-Info ""
Write-Info "Step 3: Cleanup..."

# Remove PID directory if empty
if (Test-Path $PID_DIR) {
    $remainingPids = Get-ChildItem -Path $PID_DIR -Filter "*.pid"
    if ($remainingPids.Count -eq 0) {
        Remove-Item -Path $PID_DIR -Force -Recurse -ErrorAction SilentlyContinue
        Write-Success "PID directory cleaned up"
    }
}

# Archive old logs (optional)
if (Test-Path $LOG_DIR) {
    $archiveDir = Join-Path $LOG_DIR "archive"
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

    Get-ChildItem -Path $LOG_DIR -Filter "*.log*" | ForEach-Object {
        $archiveName = "$($_.BaseName)_$timestamp$($_.Extension)"
        Move-Item -Path $_.FullName -Destination (Join-Path $archiveDir $archiveName) -Force -ErrorAction SilentlyContinue
    }

    Write-Success "Logs archived to: $archiveDir"
}

Write-Info ""
Write-Success "All MCP services stopped successfully!"
Write-Info ""
Write-Info "To restart services, run: .\scripts\start_mcp_services.ps1"
