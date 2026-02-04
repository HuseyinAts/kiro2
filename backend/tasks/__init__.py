"""
Celery Background Tasks
PHASE 1 Sprint 3

Task modules:
- email_tasks: Email sending
- report_tasks: Report generation
- video_tasks: Video processing
- bulk_tasks: Bulk operations
"""
from core.celery_app import celery_app

__all__ = ["celery_app"]
