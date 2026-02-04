#!/bin/bash

# =============================================================================
# Kubernetes Deployment Script for Türkiye Üniversite Sınav Hazırlık Platformu
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="turkiye-sinav-platform"
KUBECTL_TIMEOUT="300s"
DEPLOYMENT_TIMEOUT="600s"

# Functions
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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    fi
    
    log_success "Prerequisites check completed"
}

create_namespace() {
    log_info "Creating namespace..."
    kubectl apply -f k8s/namespace.yaml
    log_success "Namespace created/updated"
}

deploy_secrets() {
    log_info "Deploying secrets..."
    
    # Check if secrets exist
    if kubectl get secret turkiye-sinav-secrets -n "$NAMESPACE" &> /dev/null; then
        log_warning "Secrets already exist. Skipping creation."
        log_warning "To update secrets, delete them first: kubectl delete secret turkiye-sinav-secrets -n $NAMESPACE"
    else
        kubectl apply -f k8s/secrets.yaml
        log_success "Secrets deployed"
    fi
}

deploy_configmaps() {
    log_info "Deploying ConfigMaps..."
    kubectl apply -f k8s/configmap.yaml
    log_success "ConfigMaps deployed"
}

deploy_rbac() {
    log_info "Deploying RBAC..."
    kubectl apply -f k8s/rbac.yaml
    log_success "RBAC deployed"
}

deploy_storage() {
    log_info "Deploying storage resources..."
    kubectl apply -f k8s/pvc.yaml
    
    # Wait for PVCs to be bound
    log_info "Waiting for PVCs to be bound..."
    kubectl wait --for=condition=Bound pvc --all -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    log_success "Storage resources deployed"
}

deploy_statefulsets() {
    log_info "Deploying StatefulSets..."
    kubectl apply -f k8s/statefulset.yaml
    
    # Wait for StatefulSets to be ready
    log_info "Waiting for StatefulSets to be ready..."
    kubectl wait --for=condition=Ready statefulset --all -n "$NAMESPACE" --timeout="$DEPLOYMENT_TIMEOUT"
    log_success "StatefulSets deployed and ready"
}

deploy_services() {
    log_info "Deploying Services..."
    kubectl apply -f k8s/service.yaml
    log_success "Services deployed"
}

deploy_applications() {
    log_info "Deploying Applications..."
    kubectl apply -f k8s/deployment.yaml
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=Available deployment --all -n "$NAMESPACE" --timeout="$DEPLOYMENT_TIMEOUT"
    log_success "Applications deployed and ready"
}

deploy_autoscaling() {
    log_info "Deploying HorizontalPodAutoscalers..."
    kubectl apply -f k8s/hpa.yaml
    log_success "HorizontalPodAutoscalers deployed"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -n "$NAMESPACE" -o wide
    
    # Check service endpoints
    log_info "Checking service endpoints..."
    kubectl get endpoints -n "$NAMESPACE"
    
    # Test application health endpoint
    log_info "Testing application health..."
    APP_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=turkiye-sinav-app -o jsonpath='{.items[0].metadata.name}')
    if kubectl exec -n "$NAMESPACE" "$APP_POD" -- curl -f http://localhost:8000/health; then
        log_success "Application health check passed"
    else
        log_error "Application health check failed"
        return 1
    fi
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo "=========================="
    
    # Get LoadBalancer IP
    EXTERNAL_IP=$(kubectl get service turkiye-sinav-nginx-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
    echo "External IP: $EXTERNAL_IP"
    
    # Show resource usage
    echo ""
    echo "Resource Usage:"
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "Metrics not available"
    
    # Show HPA status
    echo ""
    echo "HPA Status:"
    kubectl get hpa -n "$NAMESPACE"
    
    echo ""
    echo "Access URLs:"
    if [ "$EXTERNAL_IP" != "Pending" ]; then
        echo "  Application: https://$EXTERNAL_IP"
        echo "  API: https://$EXTERNAL_IP/api/v1"
    else
        echo "  Waiting for LoadBalancer IP assignment..."
    fi
}

cleanup_failed_deployment() {
    log_warning "Cleaning up failed deployment..."
    
    # Delete deployments
    kubectl delete deployment --all -n "$NAMESPACE" --ignore-not-found=true
    
    # Delete StatefulSets
    kubectl delete statefulset --all -n "$NAMESPACE" --ignore-not-found=true
    
    # Delete services
    kubectl delete service --all -n "$NAMESPACE" --ignore-not-found=true
    
    log_info "Cleanup completed. You can retry the deployment."
}

main() {
    log_info "Starting Kubernetes deployment for Türkiye Üniversite Sınav Hazırlık Platformu"
    log_info "Namespace: $NAMESPACE"
    
    # Trap to cleanup on failure
    trap cleanup_failed_deployment ERR
    
    check_prerequisites
    create_namespace
    deploy_secrets
    deploy_configmaps
    deploy_rbac
    deploy_storage
    deploy_statefulsets
    deploy_services
    deploy_applications
    deploy_autoscaling
    
    # Remove trap after successful deployment
    trap - ERR
    
    run_health_checks
    show_deployment_info
    
    log_success "Deployment completed successfully!"
    log_info "Monitor the deployment with: kubectl get all -n $NAMESPACE"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "cleanup")
        log_warning "Cleaning up entire deployment..."
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
        log_success "Cleanup completed"
        ;;
    "status")
        kubectl get all -n "$NAMESPACE"
        ;;
    "logs")
        kubectl logs -f deployment/turkiye-sinav-app -n "$NAMESPACE"
        ;;
    *)
        echo "Usage: $0 [deploy|cleanup|status|logs]"
        echo "  deploy  - Deploy the application (default)"
        echo "  cleanup - Remove the entire deployment"
        echo "  status  - Show deployment status"
        echo "  logs    - Follow application logs"
        exit 1
        ;;
esac