#!/bin/bash
# Environment Setup Script
# Sets up the complete development/production environment

set -e  # Exit on error

echo "🚀 Türkiye Üniversite Sınavları Hazırlık Platformu - Environment Setup"
echo "========================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created. Please edit it with your actual values!${NC}"
    echo ""
    echo "Required API keys:"
    echo "  - YOUTUBE_API_KEY (Get from: https://console.cloud.google.com/apis/credentials)"
    echo "  - OPENAI_API_KEY (Get from: https://platform.openai.com/api-keys)"
    echo "  - SECRET_KEY (Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
    echo "  - JWT_SECRET_KEY (Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
    echo ""
    read -p "Press Enter after you've updated .env file..."
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "📦 Step 1: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

echo "🐘 Step 2: Starting PostgreSQL..."
docker-compose up -d postgres
echo -e "${GREEN}✅ PostgreSQL started${NC}"
echo ""

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

echo "📊 Step 3: Starting Redis..."
docker-compose up -d redis
echo -e "${GREEN}✅ Redis started${NC}"
echo ""

echo "🔍 Step 4: Starting Elasticsearch..."
docker-compose up -d elasticsearch
echo -e "${GREEN}✅ Elasticsearch started${NC}"
echo ""

echo "🇹🇷 Step 5: Starting Zemberek NLP..."
docker-compose up -d zemberek
echo -e "${GREEN}✅ Zemberek NLP started${NC}"
echo ""

echo "📈 Step 6: Starting Monitoring Stack (Prometheus + Grafana)..."
docker-compose up -d prometheus grafana node-exporter cadvisor
echo -e "${GREEN}✅ Monitoring stack started${NC}"
echo ""

echo "⏳ Waiting for services to be fully ready..."
sleep 10

echo "🗄️  Step 7: Initializing Database..."
if [ -f backend/init_db.py ]; then
    cd backend
    python init_db.py
    cd ..
    echo -e "${GREEN}✅ Database initialized${NC}"
else
    echo -e "${YELLOW}⚠️  backend/init_db.py not found. Skipping database initialization.${NC}"
fi
echo ""

echo "🔍 Step 8: Running Database Migrations..."
if [ -f backend/alembic.ini ]; then
    cd backend
    alembic upgrade head
    cd ..
    echo -e "${GREEN}✅ Database migrations applied${NC}"
else
    echo -e "${YELLOW}⚠️  Alembic not configured. Skipping migrations.${NC}"
fi
echo ""

echo "✅ Step 9: Verifying Services..."
echo ""
echo "Service Status:"
echo "---------------"

# Check PostgreSQL
if docker ps | grep -q turkiye_sinav_postgres; then
    echo -e "${GREEN}✅ PostgreSQL: Running (port 5432)${NC}"
else
    echo -e "${RED}❌ PostgreSQL: Not running${NC}"
fi

# Check Redis
if docker ps | grep -q turkiye_sinav_redis; then
    echo -e "${GREEN}✅ Redis: Running (port 6379)${NC}"
else
    echo -e "${RED}❌ Redis: Not running${NC}"
fi

# Check Elasticsearch
if docker ps | grep -q turkiye_sinav_elasticsearch; then
    echo -e "${GREEN}✅ Elasticsearch: Running (port 9200)${NC}"
else
    echo -e "${RED}❌ Elasticsearch: Not running${NC}"
fi

# Check Zemberek
if docker ps | grep -q turkiye_sinav_zemberek; then
    echo -e "${GREEN}✅ Zemberek NLP: Running (port 8081)${NC}"
else
    echo -e "${RED}❌ Zemberek NLP: Not running${NC}"
fi

# Check Prometheus
if docker ps | grep -q turkiye_sinav_prometheus; then
    echo -e "${GREEN}✅ Prometheus: Running (port 9090)${NC}"
else
    echo -e "${RED}❌ Prometheus: Not running${NC}"
fi

# Check Grafana
if docker ps | grep -q turkiye_sinav_grafana; then
    echo -e "${GREEN}✅ Grafana: Running (port 3001)${NC}"
else
    echo -e "${RED}❌ Grafana: Not running${NC}"
fi

echo ""
echo "========================================================================"
echo -e "${GREEN}🎉 Environment setup complete!${NC}"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "  1. Start backend: cd backend && uvicorn main:app --reload"
echo "  2. Start frontend: cd frontend && npm run dev"
echo "  3. Access Grafana: http://localhost:3001 (admin/changeme_grafana_password)"
echo "  4. Access Prometheus: http://localhost:9090"
echo ""
echo "To stop all services: docker-compose down"
echo "To view logs: docker-compose logs -f [service-name]"
echo ""
