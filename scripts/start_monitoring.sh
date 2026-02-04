#!/bin/bash
# Start Monitoring Stack
# Video API Monitoring - Task 19

set -e

echo "🚀 Starting Teknofest Video API Monitoring Stack..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Please update .env with your Slack webhook URL and SMTP credentials"
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "⚠️  SLACK_WEBHOOK_URL not set in .env"
    echo "   Alerts will not be sent to Slack"
fi

if [ -z "$SMTP_USERNAME" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo "⚠️  SMTP credentials not set in .env"
    echo "   Email alerts will not work"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p monitoring/alertmanager
mkdir -p backend/config
mkdir -p backend/docs

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing monitoring containers..."
docker-compose -f docker-compose.monitoring.yml down

# Build Prometheus exporter image
echo "🔨 Building Prometheus exporter image..."
docker-compose -f docker-compose.monitoring.yml build prometheus-exporter

# Start monitoring stack
echo "🚀 Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

services=("prometheus" "alertmanager" "grafana" "redis" "prometheus-exporter")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "$service.*Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo ""
    echo "✅ All monitoring services are running!"
    echo ""
    echo "📊 Access URLs:"
    echo "   - Prometheus:    http://localhost:9090"
    echo "   - Alertmanager:  http://localhost:9093"
    echo "   - Grafana:       http://localhost:3000 (admin/admin)"
    echo "   - Metrics:       http://localhost:9091/metrics"
    echo ""
    echo "📈 Grafana Dashboards:"
    echo "   - Video API Dashboard: http://localhost:3000/d/video-api"
    echo "   - Database Dashboard:  http://localhost:3000/d/database"
    echo ""
    echo "🔔 Alert Channels:"
    echo "   - Slack: #backend-youtube-api, #backend-critical, #backend-health"
    echo "   - Email: backend-team@teknofest-egitim.com"
    echo ""
    echo "📚 Documentation:"
    echo "   - Setup Guide: backend/docs/MONITORING_ALERTING_SETUP.md"
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Open Grafana and import dashboards"
    echo "   2. Configure Slack webhook URL in .env"
    echo "   3. Test alerts: curl http://localhost:9093/api/v1/alerts"
    echo "   4. Start backend application to generate metrics"
    echo ""
else
    echo ""
    echo "❌ Some services failed to start. Check logs:"
    echo "   docker-compose -f docker-compose.monitoring.yml logs"
    exit 1
fi
