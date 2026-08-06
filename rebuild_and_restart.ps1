<#
.SYNOPSIS
Rebuilds and restarts KIRO2 containers without cache to resolve staleness issues.

.DESCRIPTION
This script stops existing containers, removes orphaned containers, builds new 
images without using the cache (preventing stale packages or 404/ImportError), 
and starts the stack in detached mode.

.EXAMPLE
.\rebuild_and_restart.ps1
#>

Write-Host "Stopping existing KIRO2 containers..." -ForegroundColor Cyan
docker compose down --remove-orphans

Write-Host "Rebuilding images without cache (resolving staleness)..." -ForegroundColor Yellow
docker compose build --no-cache backend frontend celery-worker celery-beat

Write-Host "Starting KIRO2 containers in detached mode..." -ForegroundColor Green
docker compose up -d

Write-Host "Done! Use 'docker compose logs -f' to view logs." -ForegroundColor Cyan
