"""
Conftest for unit health tests
"""
import os
import sys

# Add backend path to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
