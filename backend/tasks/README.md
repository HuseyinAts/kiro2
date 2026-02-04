# Celery Background Tasks

PHASE 1 Sprint 3: Async Processing Infrastructure

## Overview

This module provides background task processing using Celery for time-consuming operations:

- **Email Tasks**: Welcome emails, notifications, password resets
- **Report Tasks**: Analytics, progress reports, summaries
- **Video Tasks**: Video processing, transcoding, thumbnails
- **Bulk Tasks**: Data import/export, cleanup, archival

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│   FastAPI   │────▶│  Celery  │────▶│    Redis    │
│  API Server │     │  Broker  │     │   (Queue)   │
└─────────────┘     └──────────┘     └─────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │  Celery  │
                    │  Workers │
                    └──────────┘
                          │
                          ▼
                    ┌──────────┐
                    │   Task   │
                    │Execution │
                    └──────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install celery[redis] flower
```

### 2. Start Redis

```bash
# Linux/Mac
redis-server

# Windows (WSL or Docker)
docker run -d -p 6379:6379 redis:latest
```

### 3. Start Celery Workers

```bash
# Windows
start_celery_workers.bat

# Linux/Mac
chmod +x start_celery_workers.sh
./start_celery_workers.sh
```

### 4. Monitor with Flower

Open browser: http://localhost:5555

## Task Queues & Priorities

| Queue | Priority | Use Case | Workers |
|-------|----------|----------|---------|
| `emails` | 9 (Highest) | User emails, notifications | 2-4 |
| `reports` | 5 (Medium) | Analytics, progress reports | 2-3 |
| `videos` | 3 (Low) | Video processing | 1-2 |
| `bulk` | 1 (Lowest) | Data import, cleanup | 1 |

## Usage Examples

### Email Tasks

```python
from tasks.email_tasks import send_welcome_email, send_notification_email

# Async - returns task ID immediately
task = send_welcome_email.delay(
    user_email="user@example.com",
    user_name="Ahmet Yılmaz"
)

# Check status
result = task.get(timeout=10)
print(result)  # {'success': True, 'email': '...', ...}
```

### Report Tasks

```python
from tasks.report_tasks import generate_student_progress_report

# Generate report asynchronously
task = generate_student_progress_report.delay(
    student_id="student123",
    start_date="2025-01-01",
    end_date="2025-11-09"
)

# Wait for result (blocking)
report = task.get(timeout=300)  # 5 minutes timeout
print(report['report_data'])
```

### Video Tasks

```python
from tasks.video_tasks import process_video_upload

# Process video in background
task = process_video_upload.delay(
    video_id="vid_123",
    video_url="https://storage.com/video.mp4",
    user_id="teacher_456"
)

# Don't wait - task runs in background
print(f"Video processing started: {task.id}")
```

### Bulk Tasks

```python
from tasks.bulk_tasks import bulk_import_questions

# Import large dataset
questions = [...]  # List of 10,000 questions

task = bulk_import_questions.delay(
    questions_data=questions,
    import_source="osym_2024",
    user_id="admin_001"
)

# Check progress periodically
while not task.ready():
    time.sleep(5)
    print(f"Task status: {task.state}")
```

## Scheduled Tasks (Celery Beat)

Periodic tasks automatically executed:

```python
# Daily analytics (every day at 8 AM)
generate_daily_analytics_report()

# Weekly summary (every Monday at 9 AM)
generate_weekly_summary_report()

# Cache cleanup (every hour)
cleanup_expired_cache_entries()

# Video cache refresh (every 6 hours)
refresh_popular_video_cache()
```

## Task Retry Configuration

All tasks have automatic retry on failure:

- **Max Retries**: 3
- **Retry Delay**: 60 seconds (exponential backoff)
- **Backoff Max**: 600 seconds (10 minutes)
- **Jitter**: Enabled (prevents thundering herd)

Example:
```python
# Task fails -> retries in 1 minute
# Fails again -> retries in 2 minutes
# Fails again -> retries in 4 minutes
# Max 3 retries
```

## Monitoring

### Flower Dashboard

Access: http://localhost:5555

Features:
- Real-time task monitoring
- Worker status
- Task history
- Execution graphs
- Retry analytics

### Logs

Structured logging via `core.structured_logger`:

```python
logger.info("task_started", task_id=task.id, args=args)
logger.error("task_failed", task_id=task.id, error=str(e))
logger.info("task_success", task_id=task.id, duration=duration)
```

## Production Deployment

### Supervisor Configuration

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A celery_worker worker --loglevel=info --concurrency=8
directory=/path/to/backend
user=celery
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A celery_worker beat --loglevel=info
directory=/path/to/backend
user=celery
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

### Docker Compose

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A celery_worker worker --loglevel=info --concurrency=8
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

  celery_beat:
    build: .
    command: celery -A celery_worker beat --loglevel=info
    depends_on:
      - redis

  flower:
    build: .
    command: celery -A celery_worker flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
```

## Performance Tips

1. **Use `.delay()` for fire-and-forget tasks**
   ```python
   send_email.delay(email, content)  # Non-blocking
   ```

2. **Use `.apply_async()` for advanced options**
   ```python
   send_email.apply_async(
       args=[email, content],
       countdown=300,  # Delay 5 minutes
       expires=3600,   # Task expires in 1 hour
       priority=9      # High priority
   )
   ```

3. **Batch processing for bulk operations**
   ```python
   # Process in chunks of 100
   for chunk in chunks(data, 100):
       process_chunk.delay(chunk)
   ```

4. **Use task groups for parallel execution**
   ```python
   from celery import group
   job = group(process_video.s(vid) for vid in video_ids)
   result = job.apply_async()
   ```

## Troubleshooting

### Workers not processing tasks

```bash
# Check Redis connection
redis-cli ping

# Check worker status
celery -A celery_worker inspect active

# Check registered tasks
celery -A celery_worker inspect registered
```

### Task stuck in pending

```bash
# Revoke task
celery -A celery_worker control revoke <task_id>

# Purge all tasks in queue
celery -A celery_worker purge
```

### High memory usage

```bash
# Restart workers after N tasks
celery -A celery_worker worker --max-tasks-per-child=100
```

## Best Practices

1. ✅ **Keep tasks idempotent** - Safe to retry
2. ✅ **Set task timeouts** - Prevent hanging tasks
3. ✅ **Log task progress** - Structured logging
4. ✅ **Handle failures gracefully** - Return error info
5. ✅ **Monitor task queues** - Use Flower
6. ✅ **Scale workers horizontally** - Add more workers for load
7. ✅ **Use priority queues** - Critical tasks first

## Support

For issues or questions:
- Documentation: `/backend/docs/`
- Flower UI: http://localhost:5555
- Logs: `/var/log/celery/` (production)
