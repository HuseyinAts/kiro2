# KIRO2 Services Startup Script (Updated for Phase 3 Architecture)
# Version: 2.0
# Description: Starts Docker, Zemberek, FastAPI Backend, and Celery worker.

param(
    [switch]$SkipDocker,
    [switch]$SkipHealthCheck,
    [int]$HealthCheckRetries = 15
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Error { Write-Host "[FAIL] $args" -ForegroundColor Red }
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }

# Configuration
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$LOG_DIR = Join-Path $PROJECT_ROOT "logs"
$PID_DIR = Join-Path $PROJECT_ROOT ".mcp_pids"

# Create directories
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $PID_DIR | Out-Null

Write-Info "=== KIRO2 Services Startup Script ==="
Write-Info "Project Root: $PROJECT_ROOT"
Write-Info ""

# Step 1: Start Docker Services
if (-not $SkipDocker) {
    Write-Info "Step 1: Starting Docker services (Redis, Elasticsearch, PostgreSQL)..."
    try {
        Push-Location $PROJECT_ROOT
        docker-compose up -d redis elasticsearch postgres prometheus
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker services started successfully"
        } else {
            Write-Error "Failed to start Docker services"
            exit 1
        }
        Pop-Location
    } catch {
        Write-Error "Docker error: $_"
        exit 1
    }
    Write-Info "Waiting for services to be ready (10 seconds)..."
    Start-Sleep -Seconds 10
} else {
    Write-Warning "Skipping Docker startup (--SkipDocker flag set)"
}

# Step 2: Check Docker services health
Write-Info ""
Write-Info "Step 2: Checking Docker services health..."

$services = @{
    "Redis" = @{ Port = 6379; Check = { Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet } }
    "Elasticsearch" = @{ Port = 9200; Check = { Test-NetConnection -ComputerName localhost -Port 9200 -InformationLevel Quiet } }
    "PostgreSQL" = @{ Port = 5434; Check = { Test-NetConnection -ComputerName localhost -Port 5434 -InformationLevel Quiet } }
}

$allHealthy = $true
foreach ($name in $services.Keys) {
    $service = $services[$name]
    if (& $service.Check) {
        Write-Success "$name is running on port $($service.Port)"
    } else {
        Write-Error "$name is NOT running on port $($service.Port)"
        $allHealthy = $false
    }
}

if (-not $allHealthy) {
    Write-Error "Some Docker services are not healthy. Please check docker-compose logs."
    exit 1
}

# Step 3: Start Services
Write-Info ""
Write-Info "Step 3: Starting Application Services..."

function Start-AppService {
    param(
        [string]$Name,
        [string]$Command,
        [string[]]$Arguments,
        [hashtable]$Env = @{},
        [int]$Port = 0,
        [string]$WorkingDirectory = $PROJECT_ROOT
    )

    Write-Info "Starting $Name..."

    $logFile = Join-Path $LOG_DIR "$Name.log"
    $pidFile = Join-Path $PID_DIR "$Name.pid"

    try {
        foreach ($key in $Env.Keys) {
            [Environment]::SetEnvironmentVariable($key, $Env[$key], "Process")
        }

        $process = Start-Process -FilePath $Command -ArgumentList $Arguments `
            -WorkingDirectory $WorkingDirectory `
            -RedirectStandardOutput $logFile `
            -RedirectStandardError "${logFile}.err" `
            -NoNewWindow -PassThru

        $process.Id | Out-File -FilePath $pidFile -Encoding ASCII

        Write-Success "$Name started (PID: $($process.Id))"

        if ($Port -gt 0) {
            Write-Info "Waiting for $Name to listen on port $Port..."
            $retries = 0
            while ($retries -lt $HealthCheckRetries) {
                if (Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet) {
                    Write-Success "$Name is listening on port $Port"
                    return $true
                }
                Start-Sleep -Seconds 2
                $retries++
            }
            Write-Warning "$Name did not start listening on port $Port within timeout"
            return $false
        }

        return $true
    } catch {
        Write-Error "Failed to start ${Name}: $($_.Exception.Message)"
        return $false
    }
}

$javaAvailable = Get-Command java -ErrorAction SilentlyContinue
$pythonAvailable = Get-Command python -ErrorAction SilentlyContinue

# Set PYTHONPATH for Python services
[Environment]::SetEnvironmentVariable("PYTHONPATH", (Join-Path $PROJECT_ROOT "backend"), "Process")

# 1. Zemberek NLP Service (Java)
if ($javaAvailable) {
    $zemberekJar = Join-Path $PROJECT_ROOT "services\zemberek-nlp-server.jar"
    if (Test-Path $zemberekJar) {
        Start-AppService -Name "zemberek-nlp" -Command "java" -Arguments @("-Xmx2G", "-Xms512M", "-jar", $zemberekJar, "--port", "8081") -Env @{ "ZEMBEREK_CACHE_ENABLED" = "true" } -Port 8081
    } else {
        Write-Warning "Zemberek JAR not found at: $zemberekJar"
    }
} else {
    Write-Warning "Java not found. Skipping Zemberek NLP Service."
}

# 2. FastAPI Backend & Celery Worker
if ($pythonAvailable) {
    # FastAPI Backend
    Start-AppService -Name "fastapi-backend" -Command "python" -Arguments @("-m", "uvicorn", "main:app", "--port", "8000") -WorkingDirectory (Join-Path $PROJECT_ROOT "backend") -Port 8000
    
    Start-Sleep -Seconds 2
    
    # Celery Worker
    Start-AppService -Name "celery-worker" -Command "python" -Arguments @("-m", "celery", "-A", "celery_worker", "worker", "--loglevel=info", "--pool=solo") -WorkingDirectory (Join-Path $PROJECT_ROOT "backend")
} else {
    Write-Warning "Python not found. Skipping Backend and Celery."
}

# Step 4: Final Health Check
Write-Info ""
Write-Info "Step 4: Final health check..."
Start-Sleep -Seconds 5

$runningServices = Get-ChildItem -Path $PID_DIR -Filter "*.pid" | ForEach-Object {
    $pidContent = Get-Content $_.FullName
    $serviceName = $_.BaseName
    try {
        $process = Get-Process -Id $pidContent -ErrorAction Stop
        if ($process.HasExited) { throw "Process exited" }
        Write-Success "$serviceName is running (PID: $pidContent)"
        return $true
    } catch {
        Write-Error "$serviceName is NOT running (PID file: $pidContent)"
        return $false
    }
}

$successCount = ($runningServices | Where-Object { $_ -eq $true }).Count
$totalCount = $runningServices.Count

Write-Info ""
Write-Info "=== Startup Summary ==="
Write-Info "Services started: $successCount / $totalCount"
Write-Info "Logs directory: $LOG_DIR"
Write-Info "PID directory: $PID_DIR"
Write-Info ""

if ($successCount -eq $totalCount -and $totalCount -gt 0) {
    Write-Success "All core services started successfully!"
    exit 0
} else {
    Write-Warning "Some services failed to start. Check logs in $LOG_DIR"
    exit 1
}
