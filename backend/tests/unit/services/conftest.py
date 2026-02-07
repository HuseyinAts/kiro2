"""
Test configuration for services unit tests.

Ensures proper Python path setup for imports.
"""

import sys
from pathlib import Path

# Add backend directory to Python path for imports
# This file is at: backend/tests/unit/services/conftest.py
backend_dir = str(Path(__file__).resolve().parent.parent.parent.parent)

# Ensure backend is first in path
if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

# Verify imports work
try:
    from services import insight_service
    _services_available = True
except ImportError:
    _services_available = False
    print(f"WARNING: Could not import services from {backend_dir}")
