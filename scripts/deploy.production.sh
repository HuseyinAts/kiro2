#!/bin/bash

# KIRO2 Production Deployment Script
# Turkish University Exam Preparation Platform
# Türkiye Üniversite Sınavları Hazırlık Platformu

set -euo pipefail  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.production"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.production.yml"
BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log "🔍 Pre-deployment checks başlıyor..."
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        error "Bu script root kullanıcısı ile çalıştırılmamalıdır!"
    fi
    
    # Check if .env.production exists
    if [[ ! -f "$ENV_FILE" ]]; then
        error ".env.production dosyası bulunamadı! Lütfen .env.production.template dosyasını kopyalayın ve düzenleyin."
    fi
    
    # Check if docker-compose.production.yml exists
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        error "docker-compose.production.yml dosyası bulunamadı!"
    fi
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        error "Docker kurulu değil!"
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose kurulu değil!"
    fi
    
    # Check environment variables
    source "$ENV_FILE"
    
    required_vars=(
        "SECRET_KEY"
        "JWT_SECRET_KEY" 
        "DATABASE_URL"
        "REDIS_URL"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "GRAFANA_ADMIN_PASSWORD"
        "GRAFANA_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Gerekli environment variable eksik: $var"
        fi
    done
    
    # Check disk space (minimum 5GB)
    available_space=$(df / | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        warning "Disk alanı yetersiz olabilir (< 5GB). Devam edilsin mi? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    success "Pre-deployment checks tamamlandı"
}

# Backup current deployment
backup_current_deployment() {
    log "📦 Mevcut deployment backup alınıyor..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup environment file
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$BACKUP_DIR/"
    fi
    
    # Backup database if containers are running
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q postgres; then
        log "📊 Database backup alınıyor..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_dumpall -c -U "${POSTGRES_USER:-kiro2user}" > "$BACKUP_DIR/database_backup.sql" || true
    fi
    
    # Backup volumes
    log "💾 Volume backup alınıyor..."
    docker run --rm -v postgres-data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data . || true
    docker run --rm -v redis-data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/redis_data.tar.gz -C /data . || true
    
    success "Backup tamamlandı: $BACKUP_DIR"
}

# Build and prepare images
build_images() {
    log "🏗️  Docker images build ediliyor..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend production image
    if [[ -f "backend/Dockerfile.production" ]]; then
        docker build -t kiro2-backend-prod:latest -f backend/Dockerfile.production ./backend
    else
        warning "backend/Dockerfile.production bulunamadı, geliştirme Dockerfile kullanılıyor"
        docker build -t kiro2-backend-prod:latest ./backend
    fi
    
    # Build frontend production image  
    if [[ -f "frontend/Dockerfile.production" ]]; then
        docker build -t kiro2-frontend-prod:latest -f frontend/Dockerfile.production ./frontend
    else
        warning "frontend/Dockerfile.production bulunamadı"
    fi
    
    success "Docker images build tamamlandı"
}

# Deploy services
deploy_services() {
    log "🚀 Services deploy ediliyor..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    # Deploy with zero-downtime strategy
    log "🔄 Rolling deployment başlatılıyor..."
    
    # Start infrastructure services first
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis elasticsearch prometheus grafana node-exporter
    
    # Wait for infrastructure to be ready
    log "⏳ Infrastructure services hazır olması bekleniyor..."
    sleep 30
    
    # Health check for database
    for i in {1..30}; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-kiro2user}" -d "${POSTGRES_DB:-kiro2_production}"; then
            success "Database hazır"
            break
        fi
        if [[ $i -eq 30 ]]; then
            error "Database health check başarısız!"
        fi
        sleep 5
    done
    
    # Deploy application services
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d backend1 backend2 backend3 celery-worker celery-beat
    
    # Wait for backends to be healthy
    log "⏳ Backend services health check..."
    sleep 45
    
    for backend in backend1 backend2 backend3; do
        for i in {1..20}; do
            if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$backend" curl -f http://localhost:8000/health; then
                success "$backend hazır"
                break
            fi
            if [[ $i -eq 20 ]]; then
                error "$backend health check başarısız!"
            fi
            sleep 10
        done
    done
    
    # Deploy nginx last
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d nginx
    
    # Start backup service
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d backup
    
    success "Services deploy tamamlandı"
}

# Post-deployment verification
post_deployment_verification() {
    log "✅ Post-deployment verification..."
    
    cd "$PROJECT_ROOT"
    
    # Check all services are running
    log "📋 Service durumları kontrol ediliyor..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Health checks
    services_to_check=("nginx" "backend1" "backend2" "backend3" "postgres" "redis" "elasticsearch")
    
    for service in "${services_to_check[@]}"; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            success "$service çalışıyor"
        else
            error "$service çalışmıyor!"
        fi
    done
    
    # Application health check
    log "🌐 Application health check..."
    if curl -f http://localhost/health > /dev/null 2>&1; then
        success "Application health check başarılı"
    else
        error "Application health check başarısız!"
    fi
    
    # Database connectivity test
    log "📊 Database connectivity test..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres psql -U "${POSTGRES_USER:-kiro2user}" -d "${POSTGRES_DB:-kiro2_production}" -c "SELECT 1;" > /dev/null; then
        success "Database connectivity başarılı"
    else
        error "Database connectivity başarısız!"
    fi
    
    # Redis connectivity test
    log "🔄 Redis connectivity test..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli --pass "${REDIS_PASSWORD}" ping | grep -q PONG; then
        success "Redis connectivity başarılı"
    else
        error "Redis connectivity başarısız!"
    fi
    
    success "Post-deployment verification tamamlandı"
}

# Cleanup old resources
cleanup_old_resources() {
    log "🧹 Eski resources temizleniyor..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused volumes (be careful!)
    warning "Kullanılmayan volumes silinecek. Devam edilsin mi? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    # Remove old backups (keep last 7)
    find "$PROJECT_ROOT/backups" -type d -name "*_*" | sort -r | tail -n +8 | xargs rm -rf 2>/dev/null || true
    
    success "Cleanup tamamlandı"
}

# Show deployment info
show_deployment_info() {
    log "📋 Deployment bilgileri:"
    echo ""
    echo "🌐 Application URL: http://$(hostname -I | awk '{print $1}')"
    echo "📊 Grafana Dashboard: http://$(hostname -I | awk '{print $1}'):3000"
    echo "📈 Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
    echo "🔍 Elasticsearch: http://$(hostname -I | awk '{print $1}'):9200"
    echo ""
    echo "📁 Log dosyaları:"
    echo "   - Nginx: $PROJECT_ROOT/logs/nginx/"
    echo "   - Backend: $PROJECT_ROOT/logs/backend/"
    echo "   - Celery: $PROJECT_ROOT/logs/celery/"
    echo ""
    echo "📦 Backup lokasyonu: $BACKUP_DIR"
    echo ""
    success "KIRO2 Production deployment başarıyla tamamlandı! 🎉"
}

# Rollback function
rollback() {
    log "🔙 Rollback işlemi başlatılıyor..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Backup directory bulunamadı: $BACKUP_DIR"
    fi
    
    warning "Bu işlem mevcut deployment'ı geri alacak. Devam edilsin mi? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Rollback iptal edildi"
        exit 0
    fi
    
    # Stop current services
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    
    # Restore database backup
    if [[ -f "$BACKUP_DIR/database_backup.sql" ]]; then
        log "📊 Database restore ediliyor..."
        # Start only postgres for restore
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres
        sleep 20
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres psql -U "${POSTGRES_USER:-kiro2user}" -d "${POSTGRES_DB:-kiro2_production}" < "$BACKUP_DIR/database_backup.sql"
    fi
    
    # Restore environment file
    if [[ -f "$BACKUP_DIR/.env.production" ]]; then
        cp "$BACKUP_DIR/.env.production" "$ENV_FILE"
    fi
    
    success "Rollback tamamlandı"
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            log "🚀 KIRO2 Production Deployment Başlıyor..."
            pre_deployment_checks
            backup_current_deployment
            build_images
            deploy_services
            post_deployment_verification
            cleanup_old_resources
            show_deployment_info
            ;;
        "rollback")
            rollback
            ;;
        "health-check")
            post_deployment_verification
            ;;
        "backup")
            backup_current_deployment
            ;;
        *)
            echo "Kullanım: $0 [deploy|rollback|health-check|backup]"
            echo ""
            echo "  deploy       - Production deployment yap (default)"
            echo "  rollback     - Son backup'a geri dön"
            echo "  health-check - Mevcut deployment sağlık kontrolü"
            echo "  backup       - Mevcut deployment'ın backup'ını al"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"