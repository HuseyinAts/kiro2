# Start Critical Services
Write-Host "Starting Critical Services..." -ForegroundColor Cyan
Write-Host ""

# Start PostgreSQL
Write-Host "1. Starting PostgreSQL..." -ForegroundColor Yellow
docker-compose up -d postgres
Start-Sleep -Seconds 5

# Start Redis
Write-Host "2. Starting Redis..." -ForegroundColor Yellow
docker-compose up -d redis
Start-Sleep -Seconds 3

# Check status
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}"

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Green
Write-Host "1. Edit .env file and add API keys" -ForegroundColor White
Write-Host "2. Initialize database: cd backend; python init_db.py" -ForegroundColor White
Write-Host "3. Start Zemberek: docker-compose up -d zemberek-nlp" -ForegroundColor White
Write-Host ""
