#!/bin/bash
# Monitoring Stack Startup Script
# Teknofest 2025 - Eğitim Eylemci Projesi

set -e

echo "🚀 Starting Monitoring Stack..."
echo "================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cat > .env << EOF
# Slack Webhook URL for alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email configuration for critical alerts
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Grafana admin password
GRAFANA_PASSWORD=teknofest2025
EOF
    echo "✅ .env file created. Please update with your credentials."
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p prometheus/alerts
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/dashboards
mkdir -p alertmanager

# Start monitoring stack
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus is not responding"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana is not responding"
fi

# Check Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    echo "✅ Alertmanager is healthy"
else
    echo "❌ Alertmanager is not responding"
fi

echo ""
echo "================================"
echo "✅ Monitoring Stack Started!"
echo "================================"
echo ""
echo "📊 Access URLs:"
echo "  - Grafana:      http://localhost:3000"
echo "  - Prometheus:   http://localhost:9090"
echo "  - Alertmanager: http://localhost:9093"
echo ""
echo "🔑 Grafana Credentials:"
echo "  - Username: admin"
echo "  - Password: teknofest2025"
echo ""
echo "📈 Dashboard:"
echo "  Navigate to: Dashboards → Browse → Video API → Video API Monitoring Dashboard"
echo ""
echo "📝 View logs:"
echo "  docker-compose -f docker-compose.monitoring.yml logs -f"
echo ""
echo "🛑 Stop monitoring:"
echo "  docker-compose -f docker-compose.monitoring.yml down"
echo ""
