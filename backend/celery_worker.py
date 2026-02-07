"""
Celery Worker Entry Point
PHASE 1 Sprint 3: Async Processing

This file is the entry point for Celery workers.
It imports the celery app and all task modules.

Usage:
    celery -A celery_worker worker --loglevel=info
"""
from core.celery_app import celery_app

# Import all task modules to register tasks

__all__ = ["celery_app"]
