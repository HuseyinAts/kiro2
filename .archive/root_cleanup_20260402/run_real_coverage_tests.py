"""
Coverage Boost - Test Çalıştırma Scripti
Bu script gerçek coverage artışı sağlar
"""
import subprocess
import sys
import io
from pathlib import Path

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def run_real_coverage_tests():
    """Gerçek coverage testlerini çalıştır"""

    print("=" * 70)
    print("🚀 GERÇEK COVERAGE BOOST TESTLERİ")
    print("=" * 70)
    print()

    backend_dir = Path(__file__).parent / "backend"

    print("📊 Coverage artışı için gerçek testler çalıştırılıyor...")
    print("-" * 70)

    # Gerçek coverage testleri
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/fast/test_real_coverage_boost.py",
        "-v",
        "--tb=short",
        "--cov=core.unified",
        "--cov=api",
        "--cov-report=term-missing",
        "--cov-report=html"
    ], cwd=backend_dir)

    print()
    print("=" * 70)

    if result.returncode == 0:
        print("✅ TESTLER BAŞARILI!")
        print()
        print("📊 Coverage Raporu:")
        print("   - HTML: backend/htmlcov/index.html")
        print("   - Terminal: Yukarıda görüntülendi")
        print()
        print("🎯 Beklenen Artış:")
        print("   - core.unified.monitoring_system: %47 → %60+")
        print("   - core.unified.auth_system: %44 → %60+")
        print("   - core.unified.cache_system: %32 → %50+")
        print("   - core.unified.database_system: %36 → %50+")
        print("   - core.unified.security_system: %40 → %55+")
    else:
        print("⚠️ Bazı testler başarısız!")
        print("   Ancak coverage yine de artmış olabilir.")
        print("   Raporu kontrol edin: backend/htmlcov/index.html")

    print()
    print("=" * 70)

if __name__ == "__main__":
    run_real_coverage_tests()
