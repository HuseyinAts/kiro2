# MCP Services Startup Script
# Version: 1.0
# Description: Starts all required MCP servers in correct order with health checks

param(
    [switch]$SkipDocker,
    [switch]$SkipHealthCheck,
    [int]$HealthCheckRetries = 10
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }

# Configuration
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$LOG_DIR = Join-Path $PROJECT_ROOT "logs"
$PID_DIR = Join-Path $PROJECT_ROOT ".mcp_pids"

# Create directories
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $PID_DIR | Out-Null

Write-Info "=== MCP Services Startup Script ==="
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

    Write-Info "Waiting for services to be ready (30 seconds)..."
    Start-Sleep -Seconds 30
} else {
    Write-Warning "Skipping Docker startup (--SkipDocker flag set)"
}

# Step 2: Check Docker services health
Write-Info ""
Write-Info "Step 2: Checking Docker services health..."

$services = @{
    "Redis" = @{ Port = 6379; Check = { Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet } }
    "Elasticsearch" = @{ Port = 9200; Check = { Test-NetConnection -ComputerName localhost -Port 9200 -InformationLevel Quiet } }
    "PostgreSQL" = @{ Port = 5432; Check = { Test-NetConnection -ComputerName localhost -Port 5432 -InformationLevel Quiet } }
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

# Step 3: Start MCP Servers in order
Write-Info ""
Write-Info "Step 3: Starting MCP servers in dependency order..."

# Helper function to start a service
function Start-MCPService {
    param(
        [string]$Name,
        [string]$Command,
        [string[]]$Args,
        [hashtable]$Env = @{},
        [int]$Port = 0
    )

    Write-Info "Starting $Name..."

    $logFile = Join-Path $LOG_DIR "$Name.log"
    $pidFile = Join-Path $PID_DIR "$Name.pid"

    try {
        # Set environment variables
        foreach ($key in $Env.Keys) {
            $value = $Env[$key]
            # Replace environment variable placeholders
            if ($value -match '\$\{(\w+)\}') {
                $envVar = $matches[1]
                $value = [Environment]::GetEnvironmentVariable($envVar)
                if (-not $value) {
                    Write-Warning "Environment variable $envVar not set for $Name"
                }
            }
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }

        # Start the process
        $process = Start-Process -FilePath $Command -ArgumentList $Args `
            -WorkingDirectory $PROJECT_ROOT `
            -RedirectStandardOutput $logFile `
            -RedirectStandardError "${logFile}.err" `
            -NoNewWindow -PassThru

        # Save PID
        $process.Id | Out-File -FilePath $pidFile -Encoding ASCII

        Write-Success "$Name started (PID: $($process.Id))"

        # Wait for port if specified
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

# Check if Java is available
$javaAvailable = Get-Command java -ErrorAction SilentlyContinue
$pythonAvailable = Get-Command python -ErrorAction SilentlyContinue

# 1. Zemberek NLP Service (Java)
if ($javaAvailable) {
    $zemberekJar = Join-Path $PROJECT_ROOT "services\zemberek-nlp-server.jar"
    if (Test-Path $zemberekJar) {
        Start-MCPService -Name "zemberek-nlp" `
            -Command "java" `
            -Args @("-Xmx2G", "-Xms512M", "-jar", $zemberekJar, "--port", "8081") `
            -Env @{ "ZEMBEREK_CACHE_ENABLED" = "true" } `
            -Port 8081
    } else {
        Write-Warning "Zemberek JAR not found at: $zemberekJar"
    }
} else {
    Write-Warning "Java not found. Skipping Zemberek NLP Service."
}

Start-Sleep -Seconds 5

# 2. Multi-Agent Blackboard (Python)
if ($pythonAvailable) {
    Start-MCPService -Name "blackboard-coordinator" `
        -Command "python" `
        -Args @("-m", "backend.agents.blackboard_coordinator") `
        -Env @{
            "WEBSOCKET_PORT" = "8765"
            "REDIS_PUBSUB_URL" = "redis://localhost:6379/1"
            "AUTO_RECONNECT_ENABLED" = "true"
        } `
        -Port 8765

    Start-Sleep -Seconds 3

    # 3. Video Quality Validators (parallel)
    $validators = @(
        @{ Name = "turkish-content-filter"; Module = "backend.services.turkish_content_filter" }
        @{ Name = "subject-relevance-scorer"; Module = "backend.services.subject_relevance_scorer" }
        @{ Name = "video-quality-validator"; Module = "backend.services.video_quality_validator" }
    )

    foreach ($validator in $validators) {
        Start-MCPService -Name $validator.Name `
            -Command "python" `
            -Args @("-m", $validator.Module)
        Start-Sleep -Seconds 1
    }

    Start-Sleep -Seconds 5

    # 4. Enhanced Recommendation Engine (depends on validators)
    Start-MCPService -Name "enhanced-recommendation-engine" `
        -Command "python" `
        -Args @("-m", "backend.services.enhanced_resource_recommendation_engine") `
        -Env @{
            "REDIS_URL" = "redis://localhost:6379/0"
            "RECOMMENDATION_CACHE_TTL" = "3600"
            "MAX_RECOMMENDATIONS" = "50"
        }

    Start-Sleep -Seconds 3

    # 5. Monitoring Service
    Start-MCPService -Name "video-recommendation-monitoring" `
        -Command "python" `
        -Args @("-m", "backend.services.video_recommendation_monitoring") `
        -Env @{
            "PROMETHEUS_PORT" = "9091"
            "LOG_LEVEL" = "INFO"
        } `
        -Port 9091

    # 6. Learning Style Detector
    Start-MCPService -Name "hybrid-learning-style-detector" `
        -Command "python" `
        -Args @("-m", "backend.services.hybrid_learning_style_detector") `
        -Env @{
            "VARK_FELDER_PROFILES" = "64"
            "TURKISH_ZPD_ENABLED" = "true"
            "MEB_MAARIF_CULTURAL_FACTORS" = "true"
        }

    # 7. Platform Health Audit
    Start-MCPService -Name "platform-health-audit" `
        -Command "python" `
        -Args @("-m", "backend.analytics.health_audit_service") `
        -Env @{
            "HEALTH_CHECK_INTERVAL_SECONDS" = "300"
            "ALERT_THRESHOLD_SCORE" = "80"
            "REPORT_OUTPUT_DIR" = "reports/health"
        }

} else {
    Write-Warning "Python not found. Skipping Python-based MCP services."
}

# Step 4: Final Health Check
Write-Info ""
Write-Info "Step 4: Final health check..."
Start-Sleep -Seconds 10

$runningServices = Get-ChildItem -Path $PID_DIR -Filter "*.pid" | ForEach-Object {
    $pidContent = Get-Content $_.FullName
    $serviceName = $_.BaseName

    try {
        $process = Get-Process -Id $pidContent -ErrorAction Stop
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

if ($successCount -eq $totalCount) {
    Write-Success "All MCP services started successfully!"
    exit 0
} else {
    Write-Warning "Some services failed to start. Check logs in $LOG_DIR"
    exit 1
}
