#!/bin/bash
# Celery Workers Startup Script for Linux/Mac
# PHASE 1 Sprint 3: Async Processing

echo "Starting Celery Workers for Kiro2..."
echo ""

# Check if Redis is running
echo "[1/4] Checking Redis connection..."
python3 -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('Redis OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Redis is not running!"
    echo "Please start Redis first: redis-server or docker run -d -p 6379:6379 redis:latest"
    exit 1
fi
echo "Redis connection: OK"
echo ""

# Start Celery Beat (scheduler)
echo "[2/4] Starting Celery Beat (scheduler)..."
celery -A core.celery_app beat --loglevel=info --detach

sleep 2

# Start Celery Worker
echo "[3/4] Starting Celery Worker..."
celery -A core.celery_app worker --loglevel=info --concurrency=8 --detach

sleep 2

# Start Flower monitoring
echo "[4/4] Starting Flower monitoring dashboard..."
celery -A core.celery_app flower --port=5555 &

sleep 2

echo ""
echo "================================================"
echo "   Celery Workers Started Successfully!"
echo "================================================"
echo "   Worker Dashboard: http://localhost:5555"
echo "   Stop: pkill -f celery"
echo "================================================"
echo ""
