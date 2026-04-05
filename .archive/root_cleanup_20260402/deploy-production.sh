#!/bin/bash

echo "===================================="
echo "Teknofest 2025 - Production Deployment"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "[1/4] Docker is running..."

echo "[2/4] Building and starting services..."
docker-compose -f docker-compose.production.yml up -d --build

if [ $? -ne 0 ]; then
    echo "ERROR: Deployment failed!"
    exit 1
fi

echo "[3/4] Waiting for services to start (30 seconds)..."
sleep 30

echo "[4/4] Checking service status..."
docker-compose -f docker-compose.production.yml ps

echo ""
echo "===================================="
echo "DEPLOYMENT COMPLETE!"
echo "===================================="
echo ""
echo "Access points:"
echo "- Frontend: https://localhost (accept self-signed certificate)"
echo "- API Health: https://localhost/health"
echo "- Grafana: http://localhost:3001"
echo "  Username: admin"
echo "  Password: GrafanaAdmin_494b68f7"
echo "- Prometheus: http://localhost:9090"
echo ""
echo "To view logs: docker-compose -f docker-compose.production.yml logs -f"
echo "To stop: docker-compose -f docker-compose.production.yml down"
echo ""