"""
Quick Win Test Çalıştırma Scripti
Bu dosyayı çalıştırarak quick win testlerini başlatabilirsiniz
"""
import subprocess
import sys
import io
from pathlib import Path

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def run_quick_tests():
    """Quick win testlerini çalıştır"""

    print("=" * 60)
    print("🚀 QUICK WIN TESTLER BAŞLATILIYOR")
    print("=" * 60)
    print()

    backend_dir = Path(__file__).parent / "backend"

    # Test 1: Monitoring testleri
    print("📊 Test 1: Core Monitoring Testleri")
    print("-" * 60)
    result1 = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/fast/test_monitoring_quick.py",
        "-v", "--tb=short"
    ], cwd=backend_dir)

    print()

    # Test 2: API testleri
    print("🌐 Test 2: API Endpoint Testleri")
    print("-" * 60)
    result2 = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/fast/test_api_quick.py",
        "-v", "--tb=short"
    ], cwd=backend_dir)

    print()
    print("=" * 60)
    print("✅ TESTLER TAMAMLANDI")
    print("=" * 60)

    # Coverage raporu
    print()
    print("📊 Coverage Raporu Oluşturuluyor...")
    subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/fast/test_monitoring_quick.py",
        "tests/fast/test_api_quick.py",
        "--cov=core",
        "--cov=api",
        "--cov-report=term",
        "--cov-report=html"
    ], cwd=backend_dir)

    print()
    print("✅ Coverage raporu: backend/htmlcov/index.html")
    print()
    print("🎯 Sonraki adımlar:")
    print("1. Coverage raporunu inceleyin")
    print("2. Başarısız testleri düzeltin")
    print("3. Daha fazla test ekleyin")

if __name__ == "__main__":
    run_quick_tests()
