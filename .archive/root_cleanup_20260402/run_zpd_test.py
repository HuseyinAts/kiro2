import subprocess
import sys
import os

print("=" * 70)
print("ZPD MAARIF TEST RUNNER")
print("=" * 70)

# Test dosyası yolu
test_file = r"C:\Users\husey\kiro2\backend\tests\unit\test_zpd_maarif_service.py"
backend_dir = r"C:\Users\husey\kiro2\backend"

print(f"Test File: {test_file}")
print(f"Backend Dir: {backend_dir}")
print(f"Python: {sys.executable}")
print("=" * 70)

# Test çalıştır
try:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    print("\n" + "STDOUT:" + "\n" + "=" * 70)
    print(result.stdout)
    
    if result.stderr:
        print("\n" + "STDERR:" + "\n" + "=" * 70)
        print(result.stderr)
    
    print("\n" + "=" * 70)
    print(f"EXIT CODE: {result.returncode}")
    print("=" * 70)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
