# Simple Backend Cleanup Script
param([switch]$AutoStart = $false)

Write-Host "MASTER CLEANUP STARTING..." -ForegroundColor Cyan
Write-Host ""

# Kill all Python processes
Write-Host "[1/3] Killing all Python processes..." -ForegroundColor Yellow
taskkill /F /IM python.exe /T 2>&1 | Out-Null
Start-Sleep -Seconds 3

# Kill processes on port 8000
Write-Host "[2/3] Clearing port 8000..." -ForegroundColor Yellow
$port = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port) {
    $pid = $port[0].OwningProcess
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
}

# Restart Docker containers
Write-Host "[3/3] Restarting Docker containers..." -ForegroundColor Yellow
docker-compose restart postgres redis 2>&1 | Out-Null

Start-Sleep -Seconds 5

# Verify
Write-Host ""
Write-Host "VERIFICATION:" -ForegroundColor Cyan
$pythonCount = (Get-Process python* -ErrorAction SilentlyContinue).Count
$portFree = -not (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue)
$pgStatus = docker ps --filter "name=postgres" --format "{{.Status}}"
$redisStatus = docker ps --filter "name=redis" --format "{{.Status}}"

Write-Host "  Python processes: $pythonCount" -ForegroundColor $(if ($pythonCount -eq 0) { "Green" } else { "Red" })
Write-Host "  Port 8000: $(if ($portFree) { 'FREE' } else { 'BUSY' })" -ForegroundColor $(if ($portFree) { "Green" } else { "Red" })
Write-Host "  PostgreSQL: $pgStatus" -ForegroundColor Green
Write-Host "  Redis: $redisStatus" -ForegroundColor Green

Write-Host ""
if ($pythonCount -eq 0 -and $portFree) {
    Write-Host "SYSTEM READY!" -ForegroundColor Green
    Write-Host ""

    if ($AutoStart) {
        Write-Host "Starting backend..." -ForegroundColor Cyan
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\husey\kiro2\backend; py -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
        Start-Sleep -Seconds 15

        Write-Host ""
        Write-Host "Backend started! Testing..." -ForegroundColor Cyan
        Start-Sleep -Seconds 10

        Write-Host "Running performance test..." -ForegroundColor Cyan
        cd C:\Users\husey\kiro2
        py quick_load_test.py
    } else {
        Write-Host "Start backend with:" -ForegroundColor Cyan
        Write-Host "  cd backend" -ForegroundColor White
        Write-Host "  py -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
    }
} else {
    Write-Host "CLEANUP INCOMPLETE - Manual intervention needed" -ForegroundColor Red
}
