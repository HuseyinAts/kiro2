"""
Quick verification script for integration fixes
Checks if all fixes have been applied correctly
"""

import sys
from pathlib import Path

print("=" * 80)
print("KIRO2 INTEGRATION FIXES VERIFICATION")
print("=" * 80)

fixes_applied = 0
total_fixes = 8

# Fix 1: Check if backend/config.yaml exists
print("\n[1/8] Checking backend/config.yaml...")
config_path = Path("backend/config.yaml")
if config_path.exists():
    print("[PASS] backend/config.yaml exists")
    fixes_applied += 1
else:
    print("[FAIL] backend/config.yaml missing")

# Fix 2: Check if get_current_user exists in jwt_auth.py
print("\n[2/8] Checking get_current_user in core/jwt_auth.py...")
jwt_auth_path = Path("backend/core/jwt_auth.py")
if jwt_auth_path.exists():
    content = jwt_auth_path.read_text(encoding='utf-8')
    if "async def get_current_user" in content:
        print("[PASS] PASS: get_current_user function exists")
        fixes_applied += 1
    else:
        print("[FAIL] FAIL: get_current_user function not found")
else:
    print("[FAIL] FAIL: jwt_auth.py not found")

# Fix 3: Check if AuthenticationContext exists
print("\n[3/8] Checking AuthenticationContext in core/enhanced_authentication.py...")
auth_path = Path("backend/core/enhanced_authentication.py")
if auth_path.exists():
    content = auth_path.read_text(encoding='utf-8')
    if "class AuthenticationContext" in content:
        print("[PASS] PASS: AuthenticationContext class exists")
        fixes_applied += 1
    else:
        print("[FAIL] FAIL: AuthenticationContext class not found")
else:
    print("[FAIL] FAIL: enhanced_authentication.py not found")

# Fix 4: Check if DifficultyLevel exists in models/enums.py
print("\n[4/8] Checking DifficultyLevel in models/enums.py...")
enums_path = Path("backend/models/enums.py")
if enums_path.exists():
    content = enums_path.read_text(encoding='utf-8')
    if "class DifficultyLevel" in content:
        print("[PASS] PASS: DifficultyLevel enum exists")
        fixes_applied += 1
    else:
        print("[FAIL] FAIL: DifficultyLevel enum not found")
else:
    print("[FAIL] FAIL: enums.py not found")

# Fix 5: Check if CacheService is exported from core/cache.py
print("\n[5/8] Checking CacheService export in core/cache.py...")
cache_path = Path("backend/core/cache.py")
if cache_path.exists():
    content = cache_path.read_text(encoding='utf-8')
    if "CacheService" in content and "CacheService = CacheManager" in content:
        print("[PASS] PASS: CacheService alias exists")
        fixes_applied += 1
    else:
        print("[FAIL] FAIL: CacheService export not found")
else:
    print("[FAIL] FAIL: cache.py not found")

# Fix 6: Check if student_profiles has extend_existing
print("\n[6/8] Checking student_profiles table fix in learning_path_models.py...")
learning_path_path = Path("backend/models/learning_path_models.py")
if learning_path_path.exists():
    content = learning_path_path.read_text(encoding='utf-8')
    if "extend_existing" in content and "student_profiles" in content:
        print("[PASS] PASS: extend_existing added to student_profiles")
        fixes_applied += 1
    else:
        print("[FAIL] FAIL: extend_existing not found")
else:
    print("[FAIL] FAIL: learning_path_models.py not found")

# Fix 7: Check if UTF-8 encoding added to main.py
print("\n[7/8] Checking UTF-8 encoding fix in backend/main.py...")
main_path = Path("backend/main.py")
if main_path.exists():
    content = main_path.read_text(encoding='utf-8')
    if "sys.stdout = io.TextIOWrapper" in content and "encoding='utf-8'" in content:
        print("[PASS] PASS: UTF-8 encoding wrapper added")
        fixes_applied += 1
    else:
        print("[FAIL] FAIL: UTF-8 encoding wrapper not found")
else:
    print("[FAIL] FAIL: main.py not found")

# Fix 8: Check if initialize_wave2b moved to lifespan
print("\n[8/8] Checking initialize_wave2b fix in backend/main.py...")
if main_path.exists():
    content = main_path.read_text(encoding='utf-8')
    if "await initialize_wave2b()" in content and "# Initialize Wave 2B Quality Evaluation System" in content:
        print("[PASS] PASS: initialize_wave2b moved to lifespan context")
        fixes_applied += 1
    else:
        print("[FAIL] FAIL: initialize_wave2b not properly moved")
else:
    print("[FAIL] FAIL: main.py not found")

# Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
score = (fixes_applied / total_fixes) * 100
print(f"\n[PASS] Fixes Applied: {fixes_applied}/{total_fixes} ({score:.1f}%)")

if fixes_applied == total_fixes:
    print("\n[SUCCESS] ALL FIXES SUCCESSFULLY APPLIED!")
    print("\nNext steps:")
    print("1. Run backend: cd backend && uvicorn main:app --reload")
    print("2. Check for import errors")
    print("3. Test API endpoints")
    sys.exit(0)
else:
    print(f"\n[WARNING] {total_fixes - fixes_applied} fix(es) still need attention")
    sys.exit(1)
