#!/bin/bash
# ============================================================================
# Video API Production Deployment Script
# Automated deployment with health checks and rollback capability
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-video-api}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-ghcr.io/turkiye-sinav}"
IMAGE_NAME="${IMAGE_NAME:-video-api}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DEPLOYMENT_NAME="video-api"
TIMEOUT="${TIMEOUT:-600}"  # 10 minutes
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-30}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-10}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error_exit "kubectl not found. Please install kubectl."
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        error_exit "docker not found. Please install docker."
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        error_exit "Cannot connect to Kubernetes cluster."
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    local build_date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    local vcs_ref=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    local version="${IMAGE_TAG}"
    
    docker build \
        -f .kiro/specs/learning-path-video-fix/deployment/Dockerfile.video-api \
        -t "${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_REGISTRY}/${IMAGE_NAME}:${vcs_ref}" \
        --build-arg BUILD_DATE="${build_date}" \
        --build-arg VCS_REF="${vcs_ref}" \
        --build-arg VERSION="${version}" \
        . || error_exit "Docker build failed"
    
    log_success "Docker image built successfully"
}

# Test image locally
test_image() {
    log_info "Testing Docker image locally..."
    
    # Run container with test configuration
    local container_id=$(docker run -d \
        -p 8000:8000 \
        -e DATABASE_URL="sqlite:///./test.db" \
        -e REDIS_URL="redis://localhost:6379/0" \
        -e YOUTUBE_API_KEY="test_key" \
        -e ENVIRONMENT="test" \
        "${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}")
    
    # Wait for container to start
    sleep 10
    
    # Test health endpoint
    if curl -sf http://localhost:8000/api/youtube/health > /dev/null; then
        log_success "Image test passed"
    else
        log_error "Image test failed"
        docker logs "${container_id}"
        docker stop "${container_id}" && docker rm "${container_id}"
        error_exit "Image health check failed"
    fi
    
    # Cleanup
    docker stop "${container_id}" && docker rm "${container_id}"
}

# Push image to registry
push_image() {
    log_info "Pushing image to registry..."
    
    docker push "${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" || \
        error_exit "Failed to push image"
    
    local vcs_ref=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    if [ "${vcs_ref}" != "unknown" ]; then
        docker push "${IMAGE_REGISTRY}/${IMAGE_NAME}:${vcs_ref}" || \
            log_warning "Failed to push image with VCS ref tag"
    fi
    
    log_success "Image pushed successfully"
}

# Create namespace if not exists
create_namespace() {
    log_info "Checking namespace..."
    
    if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_info "Creating namespace ${NAMESPACE}..."
        kubectl create namespace "${NAMESPACE}" || \
            error_exit "Failed to create namespace"
    fi
    
    log_success "Namespace ready"
}

# Apply Kubernetes manifests
apply_manifests() {
    log_info "Applying Kubernetes manifests..."
    
    kubectl apply -f .kiro/specs/learning-path-video-fix/deployment/k8s/video-api-deployment.yaml || \
        error_exit "Failed to apply manifests"
    
    log_success "Manifests applied"
}

# Wait for rollout to complete
wait_for_rollout() {
    log_info "Waiting for deployment rollout..."
    
    if kubectl rollout status deployment/"${DEPLOYMENT_NAME}" \
        -n "${NAMESPACE}" \
        --timeout="${TIMEOUT}s"; then
        log_success "Deployment rollout completed"
    else
        error_exit "Deployment rollout failed or timed out"
    fi
}

# Verify deployment health
verify_deployment() {
    log_info "Verifying deployment health..."
    
    # Get pod names
    local pods=$(kubectl get pods -n "${NAMESPACE}" \
        -l app.kubernetes.io/name=video-api \
        -o jsonpath='{.items[*].metadata.name}')
    
    if [ -z "${pods}" ]; then
        error_exit "No pods found"
    fi
    
    # Check each pod
    for pod in ${pods}; do
        log_info "Checking pod: ${pod}"
        
        # Check pod status
        local status=$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
            -o jsonpath='{.status.phase}')
        
        if [ "${status}" != "Running" ]; then
            log_error "Pod ${pod} is not running (status: ${status})"
            kubectl describe pod "${pod}" -n "${NAMESPACE}"
            error_exit "Pod health check failed"
        fi
        
        # Check health endpoint
        local retries=0
        while [ ${retries} -lt ${HEALTH_CHECK_RETRIES} ]; do
            if kubectl exec "${pod}" -n "${NAMESPACE}" -- \
                curl -sf http://localhost:8000/api/youtube/health > /dev/null; then
                log_success "Pod ${pod} health check passed"
                break
            else
                retries=$((retries + 1))
                if [ ${retries} -eq ${HEALTH_CHECK_RETRIES} ]; then
                    log_error "Pod ${pod} health check failed after ${HEALTH_CHECK_RETRIES} retries"
                    kubectl logs "${pod}" -n "${NAMESPACE}"
                    error_exit "Health check failed"
                fi
                log_info "Health check retry ${retries}/${HEALTH_CHECK_RETRIES}..."
                sleep ${HEALTH_CHECK_INTERVAL}
            fi
        done
    done
    
    log_success "All pods are healthy"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Port forward to service
    kubectl port-forward -n "${NAMESPACE}" \
        service/video-api-service 8000:8000 &
    local port_forward_pid=$!
    
    # Wait for port forward
    sleep 5
    
    # Test health endpoint
    if ! curl -sf http://localhost:8000/api/youtube/health > /dev/null; then
        kill ${port_forward_pid}
        error_exit "Smoke test: Health endpoint failed"
    fi
    log_success "Smoke test: Health endpoint passed"
    
    # Test video recommendations endpoint
    local response=$(curl -sf -X POST http://localhost:8000/api/youtube/recommendations \
        -H "Content-Type: application/json" \
        -d '{
            "goals": ["Matematik TYT"],
            "currentLevel": {"matematik": 50},
            "learningStyle": "visual",
            "preferences": {"language": "tr"}
        }' || echo "failed")
    
    if [ "${response}" = "failed" ]; then
        kill ${port_forward_pid}
        error_exit "Smoke test: Video recommendations endpoint failed"
    fi
    log_success "Smoke test: Video recommendations endpoint passed"
    
    # Cleanup
    kill ${port_forward_pid}
    
    log_success "All smoke tests passed"
}

# Display deployment info
display_info() {
    log_info "Deployment Information:"
    echo ""
    echo "Namespace: ${NAMESPACE}"
    echo "Image: ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    
    log_info "Pods:"
    kubectl get pods -n "${NAMESPACE}" -l app.kubernetes.io/name=video-api
    echo ""
    
    log_info "Services:"
    kubectl get services -n "${NAMESPACE}"
    echo ""
    
    log_info "HPA:"
    kubectl get hpa -n "${NAMESPACE}"
    echo ""
    
    log_info "Ingress:"
    kubectl get ingress -n "${NAMESPACE}" 2>/dev/null || echo "No ingress configured"
    echo ""
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    kubectl rollout undo deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}" || \
        error_exit "Rollback failed"
    
    log_info "Waiting for rollback to complete..."
    kubectl rollout status deployment/"${DEPLOYMENT_NAME}" \
        -n "${NAMESPACE}" \
        --timeout="${TIMEOUT}s" || \
        error_exit "Rollback failed"
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting Video API deployment..."
    log_info "Target: ${NAMESPACE}"
    log_info "Image: ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    
    # Trap errors for rollback
    trap 'log_error "Deployment failed. Consider rollback."; exit 1' ERR
    
    # Run deployment steps
    check_prerequisites
    build_image
    test_image
    push_image
    create_namespace
    apply_manifests
    wait_for_rollout
    verify_deployment
    run_smoke_tests
    display_info
    
    log_success "Deployment completed successfully!"
    log_info "Monitor the deployment with: kubectl get pods -n ${NAMESPACE} -w"
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    verify)
        verify_deployment
        ;;
    smoke-test)
        run_smoke_tests
        ;;
    info)
        display_info
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|verify|smoke-test|info}"
        exit 1
        ;;
esac
