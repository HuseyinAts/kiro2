#!/usr/bin/env python3
"""Test all critical imports for KIRO2 backend"""

import sys
print(f"Python: {sys.version}")
print("=" * 60)

packages = {
    # Core Web Framework
    "FastAPI": "fastapi",
    "Pydantic": "pydantic",
    "SQLAlchemy": "sqlalchemy",
    "Alembic": "alembic",
    
    # Database
    "asyncpg": "asyncpg",
    "psycopg": "psycopg",
    
    # Cache & Queue
    "Redis": "redis",
    # "aioredis": "aioredis",  # DEPRECATED in Python 3.13
    "Celery": "celery",
    
    # HTTP
    "aiohttp": "aiohttp",
    "httpx": "httpx",
    
    # Testing
    "pytest": "pytest",
    "pytest_asyncio": "pytest_asyncio",
    
    # ML/Data
    "NumPy": "numpy",
    "scikit-learn": "sklearn",
    "matplotlib": "matplotlib",
    
    # Utils
    "Pillow": "PIL",
    "structlog": "structlog",
    "psutil": "psutil",
}

failed = []
for name, module in packages.items():
    try:
        __import__(module)
        print(f"[OK] {name:15} imported successfully")
    except ImportError as e:
        failed.append(f"{name}: {e}")
        print(f"[FAIL] {name:15} - {e}")

print("=" * 60)
if failed:
    print(f"[WARNING] {len(failed)} packages failed to import:")
    for f in failed:
        print(f"  - {f}")
else:
    print("[SUCCESS] All critical packages imported successfully!")
print(f"\n[INFO] Total: {len(packages) - len(failed)}/{len(packages)} packages working")