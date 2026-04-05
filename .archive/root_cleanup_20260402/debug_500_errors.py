"""
500 hatasi veren endpoint'leri debug et
Konum: C:/Users/husey/kiro2/
"""

import asyncio
import httpx
import json
from datetime import datetime

async def debug_endpoint(url: str, name: str):
    """Endpoint'i debug et ve detayli hata bilgisi al"""
    print(f"\n{'='*70}")
    print(f"DEBUG: {name}")
    print(f"{'='*70}")
    print(f"URL: {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)

            print(f"\nResponse:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")

            # Response body
            print(f"\nResponse Body:")
            try:
                data = response.json()
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            except:
                print(response.text[:500])

            # Eger 500 ise backend loglarina bak
            if response.status_code == 500:
                print(f"\n[ERROR] 500 INTERNAL SERVER ERROR!")
                print(f"   Backend loglarini kontrol edin:")
                print(f"   Terminal'de 'Traceback' veya 'ERROR' arayin")

            return response.status_code

        except Exception as e:
            print(f"\n[ERROR] Request Exception: {e}")
            return None

async def check_backend_logs():
    """Backend log dosyasini kontrol et"""
    import os
    from pathlib import Path

    print(f"\n{'='*70}")
    print(f"BACKEND LOG KONTROLU")
    print(f"{'='*70}")

    log_files = [
        Path(r"C:\Users\husey\kiro2\backend\app.log"),
        Path(r"C:\Users\husey\kiro2\app.log"),
        Path(r"C:\Users\husey\kiro2\backend.log"),
    ]

    for log_file in log_files:
        if log_file.exists():
            print(f"\n[OK] Log dosyasi bulundu: {log_file}")

            # Son 50 satiri oku
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-50:] if len(lines) > 50 else lines

                print("\nSon 50 satir:")
                print("-"*70)
                for line in last_lines:
                    if "ERROR" in line or "Exception" in line or "Traceback" in line:
                        print(f"[ERROR] {line.strip()}")
                    else:
                        print(f"   {line.strip()}")

            return True

    print("\n[WARN] Log dosyasi bulunamadi")
    print("   Backend'de logging yapilandirmasi gerekebilir")
    return False

async def test_database_connection():
    """Database baglantisini test et"""
    print(f"\n{'='*70}")
    print(f"DATABASE BAGLANTI TESTI")
    print(f"{'='*70}")

    # .env dosyasini kontrol et
    from pathlib import Path
    env_files = [
        Path(r"C:\Users\husey\kiro2\.env"),
        Path(r"C:\Users\husey\kiro2\backend\.env"),
    ]

    found_env = False
    for env_file in env_files:
        if env_file.exists():
            print(f"[OK] .env dosyasi bulundu: {env_file}")
            found_env = True

            with open(env_file, 'r') as f:
                content = f.read()

                # Database URL'i kontrol et
                if "DATABASE_URL" in content:
                    print("[OK] DATABASE_URL tanimli")
                    # Degeri gosterme (guvenlik)
                    print("   (Guvenlik nedeniyle deger gosterilmiyor)")
                else:
                    print("[ERROR] DATABASE_URL tanimli DEGIL!")
                    print("   .env dosyasina ekleyin:")
                    print("   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db")

                # Redis URL'i kontrol et
                if "REDIS_URL" in content:
                    print("[OK] REDIS_URL tanimli")
                else:
                    print("[WARN] REDIS_URL tanimli degil (opsiyonel)")

    if not found_env:
        print("[ERROR] .env dosyasi bulunamadi!")
        print(f"   Beklenen konumlar: {[str(f) for f in env_files]}")

async def check_service_availability():
    """Gerekli servislerin calisip calismadigini kontrol et"""
    print(f"\n{'='*70}")
    print(f"SERVIS KONTROLU")
    print(f"{'='*70}")

    services = [
        ("PostgreSQL", "localhost", 5432),
        ("Redis", "localhost", 6379),
        ("Elasticsearch", "localhost", 9200),
    ]

    import socket

    for service_name, host, port in services:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                print(f"[OK] {service_name} (port {port}): CALISIYOR")
            else:
                print(f"[ERROR] {service_name} (port {port}): CALISMIYOR")
                print(f"   Baslatin: docker-compose up -d {service_name.lower()}")
        except Exception as e:
            print(f"[WARN] {service_name} (port {port}): Kontrol edilemedi - {e}")

async def main():
    """Ana debug fonksiyonu"""
    print("="*70)
    print("500 ERROR DEBUG ARACI")
    print("="*70)
    print(f"Baslangic: {datetime.now().strftime('%H:%M:%S')}")

    # 1. Problemli endpoint'leri test et
    print("\n\n" + "="*70)
    print("1. ENDPOINT TESTLERI")
    print("="*70)

    endpoints = [
        ("http://localhost:8000/api/v1/learning-style/detect/test_student_123",
         "Learning Style - Detect"),
        ("http://localhost:8000/api/v1/learning-style/hybrid-codes",
         "Learning Style - Hybrid Codes"),
        ("http://localhost:8000/api/v1/learning-style/statistics",
         "Learning Style - Statistics"),
    ]

    results = {}
    for url, name in endpoints:
        status = await debug_endpoint(url, name)
        results[name] = status
        await asyncio.sleep(1)

    # 2. Backend loglarini kontrol et
    print("\n\n" + "="*70)
    print("2. LOG DOSYASI KONTROLU")
    print("="*70)
    await check_backend_logs()

    # 3. Database baglantisini test et
    print("\n\n" + "="*70)
    print("3. CONFIGURATION KONTROLU")
    print("="*70)
    await test_database_connection()

    # 4. Servisleri kontrol et
    await check_service_availability()

    # OZET
    print("\n\n" + "="*70)
    print("DEBUG OZETI")
    print("="*70)

    for name, status in results.items():
        if status == 200:
            print(f"[OK] {name}: Calisiyor")
        elif status == 500:
            print(f"[ERROR] {name}: 500 Error")
        else:
            print(f"[WARN] {name}: {status}")

    print("\nONERILER:")
    print("1. Backend terminalinde hata mesajlarini kontrol edin")
    print("2. PostgreSQL/Redis'in calistigindan emin olun")
    print("3. .env dosyasinda DATABASE_URL tanimli olmali")
    print("4. Database migration calistirin: alembic upgrade head")

    print("\n[OK] Debug tamamlandi!")
    print("Ciktiyi buraya yapistirin...")

if __name__ == "__main__":
    asyncio.run(main())
