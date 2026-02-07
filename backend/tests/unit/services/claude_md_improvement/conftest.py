"""
Test fixtures for CLAUDE.md Self-Improvement services.

Bu conftest.py modül yollarını ayarlar ve ortak fixtures sağlar.
"""

import os
import sys

# Backend dizinini Python path'e ekle
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

