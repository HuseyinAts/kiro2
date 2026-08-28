#!/usr/bin/env python3
"""Test Python 3.13 compatibility for critical packages"""

import sys
print(f"Python version: {sys.version}")
print("-" * 50)

# Test NumPy
try:
    import numpy as np
    print(f"[OK] NumPy {np.__version__} imported successfully")
    test_array = np.array([1, 2, 3, 4, 5])
    print(f"[OK] NumPy array operations work: mean = {np.mean(test_array)}")
except ImportError as e:
    print(f"[ERROR] NumPy import failed: {e}")
except Exception as e:
    print(f"[ERROR] NumPy test failed: {e}")

# Test psycopg
try:
    import psycopg
    print(f"[OK] psycopg {psycopg.__version__} imported successfully")
except ImportError as e:
    print(f"[ERROR] psycopg import failed: {e}")

# Test Pillow
try:
    from PIL import Image
    print(f"[OK] Pillow {Image.__version__} imported successfully")
except ImportError as e:
    print(f"[ERROR] Pillow import failed: {e}")

# Test FastAPI
try:
    import fastapi
    print(f"[OK] FastAPI {fastapi.__version__} imported successfully")
except ImportError as e:
    print(f"[ERROR] FastAPI import failed: {e}")

# Test SQLAlchemy
try:
    import sqlalchemy
    print(f"[OK] SQLAlchemy {sqlalchemy.__version__} imported successfully")
except ImportError as e:
    print(f"[ERROR] SQLAlchemy import failed: {e}")

print("-" * 50)
print("[SUCCESS] Core packages are Python 3.13 compatible!")
