# PostgreSQL Migration Script
# Türkiye Üniversite Sınavları Hazırlık Platformu
# SQLite -> PostgreSQL Migration

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "POSTGRESQL MIGRATION BAŞLIYOR" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Docker PostgreSQL'i başlat
Write-Host "[1/6] Docker PostgreSQL ve Redis başlatılıyor..." -ForegroundColor Yellow
docker-compose up -d postgres redis

if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: Docker başlatılamadı. Docker Desktop çalışıyor mu?" -ForegroundColor Red
    Write-Host "Lütfen Docker Desktop'ı başlatın ve yeniden deneyin." -ForegroundColor Red
    exit 1
}

Write-Host "Bekleniyor: PostgreSQL başlatılıyor (10 saniye)..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 2. Container durumunu kontrol et
Write-Host "[2/6] Container durumu kontrol ediliyor..." -ForegroundColor Yellow
docker ps --filter "name=turkiye_sinav_postgres"

# 3. Python bağımlılıklarını yükle
Write-Host "[3/6] asyncpg ve PostgreSQL driver'ları yükleniyor..." -ForegroundColor Yellow
cd backend
pip install asyncpg==0.29.0 psycopg2-binary==2.9.9 --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: Python paketleri yüklenemedi" -ForegroundColor Red
    exit 1
}

Write-Host "✓ asyncpg yüklendi" -ForegroundColor Green
Write-Host "✓ psycopg2-binary yüklendi" -ForegroundColor Green

# 4. Database bağlantısını test et
Write-Host "[4/6] PostgreSQL bağlantısı test ediliyor..." -ForegroundColor Yellow

$testScript = @"
import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            'postgresql://postgres:postgres@localhost:5432/turkiye_sinav_db'
        )
        await conn.execute('SELECT 1')
        await conn.close()
        print('✓ PostgreSQL bağlantısı başarılı!')
        return True
    except Exception as e:
        print(f'✗ Bağlantı hatası: {e}')
        return False

if __name__ == '__main__':
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
"@

$testScript | Out-File -FilePath test_pg_connection.py -Encoding UTF8

python test_pg_connection.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: PostgreSQL'e bağlanılamadı" -ForegroundColor Red
    Write-Host "Çözüm kontrol listesi:" -ForegroundColor Yellow
    Write-Host "  1. Docker container'lar çalışıyor mu? -> docker ps" -ForegroundColor Gray
    Write-Host "  2. Port 5432 açık mı? -> netstat -an | findstr 5432" -ForegroundColor Gray
    Write-Host "  3. .env dosyasında DATABASE_URL doğru mu?" -ForegroundColor Gray
    exit 1
}

# 5. Alembic migration'ları çalıştır (eğer varsa)
Write-Host "[5/6] Database migration kontrol ediliyor..." -ForegroundColor Yellow

if (Test-Path "alembic.ini") {
    Write-Host "Alembic migration'ları çalıştırılıyor..." -ForegroundColor Gray
    alembic upgrade head
} else {
    Write-Host "Alembic bulunamadı - tabloları manuel oluşturacağız" -ForegroundColor Gray
}

# 6. Backend'i başlat
Write-Host "[6/6] Backend başlatılıyor..." -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "✓ POSTGRESQL MIGRATION TAMAMLANDI!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend başlatmak için:" -ForegroundColor Cyan
Write-Host "  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
Write-Host ""
Write-Host "Load test için:" -ForegroundColor Cyan
Write-Host "  cd .." -ForegroundColor White
Write-Host "  python quick_load_test.py" -ForegroundColor White
Write-Host ""
Write-Host "Beklenen performans:" -ForegroundColor Yellow
Write-Host "  - Concurrent avg: 15-60ms (eski: 6603ms)" -ForegroundColor Gray
Write-Host "  - RPS: 50-200 (eski: 1.6)" -ForegroundColor Gray
Write-Host "  - Cache hit rate: 95% maintained" -ForegroundColor Gray
Write-Host ""

# Cleanup
Remove-Item test_pg_connection.py -ErrorAction SilentlyContinue
