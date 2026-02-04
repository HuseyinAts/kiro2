# Simple MCP Services Startup Script
# Starts MCP servers without complex health checks

$PROJECT_ROOT = "c:\Users\husey\kiro2"
$LOG_DIR = Join-Path $PROJECT_ROOT "logs"
$PID_DIR = Join-Path $PROJECT_ROOT ".mcp_pids"

# Create directories
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $PID_DIR | Out-Null

Write-Host "=== Starting MCP Services ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pythonCmd = Get-Command py -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python not found" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python found: $($pythonCmd.Source)" -ForegroundColor Green

# Check Java
$javaCmd = Get-Command java -ErrorAction SilentlyContinue
if ($javaCmd) {
    Write-Host "[OK] Java found: $($javaCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "[WARN] Java not found - Zemberek NLP will be skipped" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""

# Helper function to start service
function Start-Service {
    param(
        [string]$Name,
        [string]$Command,
        [string[]]$Args
    )

    Write-Host "Starting $Name..." -ForegroundColor White

    $logFile = Join-Path $LOG_DIR "$Name.log"
    $errFile = Join-Path $LOG_DIR "$Name.err.log"
    $pidFile = Join-Path $PID_DIR "$Name.pid"

    try {
        $process = Start-Process -FilePath $Command -ArgumentList $Args `
            -WorkingDirectory $PROJECT_ROOT `
            -RedirectStandardOutput $logFile `
            -RedirectStandardError $errFile `
            -NoNewWindow -PassThru

        $process.Id | Out-File -FilePath $pidFile -Encoding ASCII
        Write-Host "  [OK] $Name started (PID: $($process.Id))" -ForegroundColor Green
        Start-Sleep -Seconds 2

    } catch {
        Write-Host "  [ERROR] Failed to start $Name" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Set environment variables
$env:REDIS_URL = "redis://localhost:6379/0"
$env:ELASTICSEARCH_URL = "http://localhost:9200"
$env:DATABASE_URL = "postgresql+asyncpg://postgres:changeme_strong_password_here@localhost:5432/turkiye_sinav_db"

# 1. Multi-Agent Blackboard Coordinator
Start-Service -Name "blackboard-coordinator" `
    -Command "py" `
    -Args @("-m", "backend.agents.blackboard_coordinator")

# 2. Hybrid Learning Style Detector
Start-Service -Name "hybrid-learning-style-detector" `
    -Command "py" `
    -Args @("-m", "backend.services.hybrid_learning_style_detector")

# 3. Turkish Content Filter
Start-Service -Name "turkish-content-filter" `
    -Command "py" `
    -Args @("-m", "backend.services.turkish_content_filter")

# 4. Subject Relevance Scorer
Start-Service -Name "subject-relevance-scorer" `
    -Command "py" `
    -Args @("-m", "backend.services.subject_relevance_scorer")

# 5. Video Quality Validator
Start-Service -Name "video-quality-validator" `
    -Command "py" `
    -Args @("-m", "backend.services.video_quality_validator")

# 6. Enhanced Recommendation Engine
Start-Service -Name "enhanced-recommendation-engine" `
    -Command "py" `
    -Args @("-m", "backend.services.enhanced_resource_recommendation_engine")

# 7. Video Recommendation Monitoring
Start-Service -Name "video-recommendation-monitoring" `
    -Command "py" `
    -Args @("-m", "backend.services.video_recommendation_monitoring")

# 8. Platform Health Audit
Start-Service -Name "platform-health-audit" `
    -Command "py" `
    -Args @("-m", "backend.analytics.health_audit_service")

# 9. Prometheus Exporter
Start-Service -Name "prometheus-exporter" `
    -Command "py" `
    -Args @("-m", "backend.monitoring.prometheus_exporter")

Write-Host ""
Write-Host "=== Startup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs directory: $LOG_DIR" -ForegroundColor White
Write-Host "PID directory: $PID_DIR" -ForegroundColor White
Write-Host ""
Write-Host "To check running services, run: Get-ChildItem .mcp_pids" -ForegroundColor Yellow
Write-Host "To stop services, run: .\scripts\stop_mcp_services.ps1" -ForegroundColor Yellow
Write-Host ""
