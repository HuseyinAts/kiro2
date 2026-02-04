#!/usr/bin/env python3
"""
Redis Caching ile Backend Restart
Tüm eski process'leri kapatır ve yeni backend başlatır
"""

import subprocess
import time
import sys
import os


def kill_all_python_processes():
    """Tüm Python process'lerini kapat"""
    print("[1/5] Eski Python process'leri kapatılıyor...")
    try:
        # Windows taskk kill komutları
        subprocess.run(
            ["taskkill", "/F", "/IM", "python.exe"], capture_output=True, text=True
        )
        subprocess.run(
            ["taskkill", "/F", "/IM", "py.exe"], capture_output=True, text=True
        )
        subprocess.run(
            ["taskkill", "/F", "/IM", "python3.exe"], capture_output=True, text=True
        )
        time.sleep(3)
        print("   ✓ Python process'leri kapatıldı")
    except Exception as e:
        print(f"   ! Uyarı: {e}")


def kill_port_9000():
    """Port 9000'i kullanan process'leri kapat"""
    print("[2/5] Port 9000 temizleniyor...")
    try:
        # Port 9000'i kullanan PID'leri bul
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)

        for line in result.stdout.split("\n"):
            if ":9000" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    pid = parts[-1]
                    print(f"   Kapatılıyor PID: {pid}")
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)

        time.sleep(2)
        print("   ✓ Port 9000 temizlendi")
    except Exception as e:
        print(f"   ! Uyarı: {e}")


def verify_port_free():
    """Port 9000'in boş olduğunu doğrula"""
    print("[3/5] Port durumu kontrol ediliyor...")
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)

        for line in result.stdout.split("\n"):
            if ":9000" in line and "LISTENING" in line:
                print("   ✗ Port 9000 hala kullanılıyor!")
                return False

        print("   ✓ Port 9000 boş")
        return True
    except Exception as e:
        print(f"   ! Hata: {e}")
        return False


def start_backend():
    """Backend'i başlat"""
    print("[4/5] Backend başlatılıyor (CACHING AKTIF)...")
    print("\n" + "=" * 50)
    print("Backend: http://localhost:9000")
    print("Caching: AKTIF (Redis)")
    print("Mode: Development (--reload)")
    print("=" * 50 + "\n")

    # Backend klasörüne git
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    # UTF-8 encoding ayarla
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # Backend'i başlat
    print("[5/5] Uvicorn başlatılıyor...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--reload",
        ],
        env=env,
    )


def main():
    print("\n" + "=" * 50)
    print("REDIS CACHING BACKEND RESTART")
    print("=" * 50 + "\n")

    kill_all_python_processes()
    kill_port_9000()

    if not verify_port_free():
        print("\n⚠️  Port 9000 temizlenemedi!")
        print("Manuel olarak Task Manager'dan Python process'lerini kapatın.\n")
        input("Hazır olunca ENTER'a basın...")

    start_backend()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBackend durduruldu.")
        sys.exit(0)
