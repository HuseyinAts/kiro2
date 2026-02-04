"""
Database migration ve test data olustur
Konum: C:/Users/husey/kiro2/
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Backend path'i ekle
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

async def check_alembic():
    """Alembic'in kurulu oldugunu kontrol et"""
    print("="*70)
    print("1. ALEMBIC KONTROLU")
    print("="*70)

    try:
        import alembic
        print(f"[OK] Alembic kurulu: {alembic.__version__}")
        return True
    except ImportError:
        print("[ERROR] Alembic kurulu degil!")
        print("\nKurulum icin:")
        print("   pip install alembic")
        return False

async def check_database_config():
    """Database konfigurasyonunu kontrol et"""
    print("\n" + "="*70)
    print("2. DATABASE KONFIGURASYON KONTROLU")
    print("="*70)

    # .env dosyasi
    env_files = [
        Path(r"C:\Users\husey\kiro2\.env"),
        Path(r"C:\Users\husey\kiro2\backend\.env"),
    ]

    found = False
    for env_file in env_files:
        if not env_file.exists():
            continue

        found = True
        print(f"[OK] .env bulundu: {env_file}")

        with open(env_file, 'r') as f:
            content = f.read()

        # DATABASE_URL kontrolu
        if "DATABASE_URL" in content:
            print("[OK] DATABASE_URL tanimli")

            # URL'i parse et (guvenli gosterim)
            for line in content.split('\n'):
                if line.startswith('DATABASE_URL'):
                    url = line.split('=', 1)[1].strip()
                    # Sifreyi gizle
                    if '@' in url:
                        parts = url.split('@')
                        safe_url = parts[0].split(':')[0] + ':***@' + parts[1]
                        print(f"   URL: {safe_url}")
                    break
            return True
        else:
            print("[ERROR] DATABASE_URL tanimli degil!")
            print("\n.env dosyasina ekleyin:")
            print("DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/turkiye_sinav_db")
            return False

    if not found:
        print("[ERROR] .env dosyasi bulunamadi!")
        print(f"   Beklenen konumlar: {[str(f) for f in env_files]}")
        return False

async def check_alembic_config():
    """Alembic yapilandirmasini kontrol et"""
    print("\n" + "="*70)
    print("3. ALEMBIC YAPILANDIRMA KONTROLU")
    print("="*70)

    alembic_ini = Path(r"C:\Users\husey\kiro2\alembic.ini")
    backend_alembic_ini = Path(r"C:\Users\husey\kiro2\backend\alembic.ini")

    if alembic_ini.exists():
        print(f"[OK] alembic.ini bulundu: {alembic_ini}")
        return str(alembic_ini.parent), True
    elif backend_alembic_ini.exists():
        print(f"[OK] alembic.ini bulundu: {backend_alembic_ini}")
        return str(backend_alembic_ini.parent), True
    else:
        print("[ERROR] alembic.ini bulunamadi!")
        print("\nAlembic baslatmak icin:")
        print("   cd C:\\Users\\husey\\kiro2\\backend")
        print("   alembic init alembic")
        print("\nYa da migration olmadan devam edebiliriz (seed data icin)")
        return None, False

async def run_migrations(work_dir: str):
    """Migration'lari calistir"""
    print("\n" + "="*70)
    print("4. MIGRATION CALISTIRMA")
    print("="*70)

    import subprocess
    import os

    print(f"Working directory: {work_dir}")

    # Alembic upgrade head komutu
    print("\nMigration calistiriliyor: alembic upgrade head")
    print("-"*70)

    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("[WARN] Stderr:", result.stderr)

        if result.returncode == 0:
            print("\n[OK] Migration basarili!")
            return True
        else:
            print(f"\n[ERROR] Migration basarisiz! Return code: {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("[ERROR] Migration timeout!")
        return False
    except FileNotFoundError:
        print("[ERROR] 'alembic' komutu bulunamadi!")
        print("   pip install alembic ile kurun")
        return False
    except Exception as e:
        print(f"[ERROR] Hata: {e}")
        return False

async def create_mock_seed_data():
    """Mock test verisi olustur (database olmadan)"""
    print("\n" + "="*70)
    print("5. MOCK TEST VERISI OLUSTURMA")
    print("="*70)

    print("[INFO] Database baglantisi olmadan mock data kullanilacak")
    print("   Bu, endpoint'lerin calismasi icin yeterli olmayabilir")
    print("   Ancak servisin yapisini test edebiliriz")

    # Mock data ornegi
    mock_students = [
        {
            "student_id": "test_student_123",
            "learning_style": "VARK",
            "profile": {
                "visual": 0.8,
                "auditory": 0.6,
                "reading": 0.7,
                "kinesthetic": 0.5
            }
        },
        {
            "student_id": "demo_student_456",
            "learning_style": "VAKI",
            "profile": {
                "visual": 0.7,
                "auditory": 0.9,
                "kinesthetic": 0.6,
                "intuitive": 0.8
            }
        }
    ]

    print(f"\n[OK] {len(mock_students)} mock ogrenci profili hazirlandi")
    for student in mock_students:
        print(f"   - {student['student_id']}: {student['learning_style']}")

    return True

async def verify_endpoints():
    """Endpoint'leri dogrula"""
    print("\n" + "="*70)
    print("6. ENDPOINT DOGRULAMA")
    print("="*70)

    import httpx

    endpoints = [
        ("http://localhost:8000/health", "Health Check"),
        ("http://localhost:8000/api/v1/learning-style/detect/test_student_123", "LS Detect"),
        ("http://localhost:8000/api/v1/learning-style/statistics", "LS Statistics"),
        ("http://localhost:8000/api/v1/learning-style/hybrid-codes", "LS Hybrid Codes"),
    ]

    success_count = 0

    async with httpx.AsyncClient(timeout=10.0) as client:
        for url, name in endpoints:
            try:
                response = await client.get(url)

                if response.status_code == 200:
                    print(f"   [OK] {name}: 200 OK")
                    success_count += 1
                elif response.status_code == 500:
                    print(f"   [ERROR] {name}: 500 (still broken)")
                else:
                    print(f"   [WARN] {name}: {response.status_code}")

            except Exception as e:
                print(f"   [ERROR] {name}: {str(e)[:50]}")

    print(f"\nBasari: {success_count}/{len(endpoints)}")
    return success_count == len(endpoints)

async def check_database_tables():
    """Database tablolarini kontrol et"""
    print("\n" + "="*70)
    print("BONUS: DATABASE TABLO KONTROLU")
    print("="*70)

    try:
        from sqlalchemy import create_engine, inspect, text
        import os
        from dotenv import load_dotenv

        load_dotenv()

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("[ERROR] DATABASE_URL bulunamadi")
            return False

        # asyncpg -> psycopg2 (sync)
        sync_url = database_url.replace("+asyncpg", "")

        print(f"[INFO] Baglanti kuruluyor...")

        engine = create_engine(sync_url)

        with engine.connect() as conn:
            print("[OK] Database baglantisi basarili!")

            # Tablolari listele
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            if tables:
                print(f"\n[OK] {len(tables)} tablo bulundu:")
                for table in tables[:10]:  # Ilk 10 tablo
                    print(f"   - {table}")
                if len(tables) > 10:
                    print(f"   ... ve {len(tables) - 10} tablo daha")
            else:
                print("\n[WARN] Hic tablo bulunamadi!")
                print("   Migration calistirmalisiniz: alembic upgrade head")

        return len(tables) > 0

    except ImportError as e:
        print(f"[WARN] SQLAlchemy veya psycopg2 bulunamadi: {e}")
        print("   Kurulum: pip install sqlalchemy psycopg2-binary")
        return False
    except Exception as e:
        print(f"[ERROR] Database baglanti hatasi: {e}")
        return False

async def main():
    """Ana setup fonksiyonu"""
    print("="*70)
    print("DATABASE SETUP VE SEED DATA OLUSTURMA")
    print("="*70)
    print(f"Baslangic: {datetime.now().strftime('%H:%M:%S')}")

    steps_success = []

    # 1. Alembic kontrolu
    step1 = await check_alembic()
    steps_success.append(("Alembic Kurulumu", step1))

    # 2. Database config kontrolu
    step2 = await check_database_config()
    steps_success.append(("Database Config", step2))

    if not step2:
        print("\n[WARN] .env dosyasini duzenleyin ve tekrar deneyin")
        # Yine de devam edebiliriz

    # 3. Alembic config kontrolu
    work_dir, step3 = await check_alembic_config()
    steps_success.append(("Alembic Config", step3))

    # 4. Migration calistir (eger alembic.ini varsa)
    if step3 and work_dir:
        step4 = await run_migrations(work_dir)
        steps_success.append(("Database Migration", step4))
    else:
        print("\n[INFO] alembic.ini olmadan migration calistirilamaz")
        print("   Mock data ile devam ediyoruz...")
        step4 = False
        steps_success.append(("Database Migration", False))

    # 5. Database tablolari kontrol et
    if step2:
        step5 = await check_database_tables()
        steps_success.append(("Database Tables", step5))
    else:
        step5 = False
        steps_success.append(("Database Tables", False))

    # 6. Mock seed data olustur
    step6 = await create_mock_seed_data()
    steps_success.append(("Mock Seed Data", step6))

    # 7. Endpoint'leri dogrula (backend calisiyorsa)
    print("\n[INFO] Backend'in calisip calismadigini kontrol ediyoruz...")
    await asyncio.sleep(1)

    step7 = await verify_endpoints()
    steps_success.append(("Endpoint Dogrulama", step7))

    # OZET
    print("\n" + "="*70)
    print("SETUP OZETI")
    print("="*70)

    for step_name, success in steps_success:
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {step_name}")

    success_count = sum(1 for _, s in steps_success if s)
    total_count = len(steps_success)

    print(f"\nBasari Orani: {success_count}/{total_count}")

    if step7:
        print("\n[SUCCESS] TUM ENDPOINT'LER CALISIYOR!")
        print("   500 hatalari duzelmis!")
    elif success_count >= 4:
        print("\n[PARTIAL] Setup kismen basarili")
        print("   Bazi adimlar basarisiz ama devam edebiliriz")
    else:
        print("\n[WARN] Bircok adim basarisiz")
        print("   Yukaridaki hata mesajlarini kontrol edin")

    print("\n[INFO] Sonraki adimlar:")
    if not step3:
        print("1. Alembic ini olustur: alembic init alembic")
    if not step4:
        print("2. Migration calistir: alembic upgrade head")
    if not step7:
        print("3. Backend'i calistir: python -m backend.main")
        print("4. Endpoint'leri test et: python test_real_endpoints.py")

    print("\n[OK] Setup tamamlandi!")
    print("Ciktiyi buraya yapistirin...")

if __name__ == "__main__":
    asyncio.run(main())
