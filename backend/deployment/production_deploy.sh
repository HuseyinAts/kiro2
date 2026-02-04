#!/bin/bash

# Production Deployment Script - Learning Path Video Fix
# Rolling deployment with health checks and rollback capability

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_NAME="video-api"
NAMESPACE="production"
IMAGE_TAG="${1:-latest}"
HEALTH_CHECK_URL="http://localhost:8000/api/youtube/health"
SMOKE_TEST_SCRIPT="./deployment/smoke_tests.sh"
ROLLBACK_ENABLED=true

echo -e "${GREEN}=== Production Deployment Started ===${NC}"
echo "Deployment: $DEPLOYMENT_NAME"
echo "Namespace: $NAMESPACE"
echo "Image Tag: $IMAGE_TAG"
echo "Timestamp: $(date)"
echo ""

# Step 1: Pre-deployment checks
echo -e "${YELLOW}Step 1: Pre-deployment checks${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}Error: Namespace $NAMESPACE does not exist${NC}"
    exit 1
fi

# Verify Docker image exists
echo "Verifying Docker image: $DEPLOYMENT_NAME:$IMAGE_TAG"
if ! docker image inspect $DEPLOYMENT_NAME:$IMAGE_TAG &> /dev/null; then
    echo -e "${RED}Error: Docker image not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Pre-deployment checks passed${NC}"
echo ""

# Step 2: Backup current deployment
echo -e "${YELLOW}Step 2: Backing up current deployment${NC}"

BACKUP_FILE="./deployment/backups/deployment-backup-$(date +%Y%m%d-%H%M%S).yaml"
mkdir -p ./deployment/backups

kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o yaml > $BACKUP_FILE
echo "Backup saved to: $BACKUP_FILE"
echo -e "${GREEN}✓ Backup completed${NC}"
echo ""

# Step 3: Update deployment with new image
echo -e "${YELLOW}Step 3: Updating deployment${NC}"

kubectl set image deployment/$DEPLOYMENT_NAME \
    backend=$DEPLOYMENT_NAME:$IMAGE_TAG \
    -n $NAMESPACE

echo "Deployment updated with image: $DEPLOYMENT_NAME:$IMAGE_TAG"
echo ""

# Step 4: Monitor rollout
echo -e "${YELLOW}Step 4: Monitoring rollout${NC}"

# Wait for rollout to complete (timeout: 5 minutes)
if kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=5m; then
    echo -e "${GREEN}✓ Rollout completed successfully${NC}"
else
    echo -e "${RED}✗ Rollout failed or timed out${NC}"
    
    if [ "$ROLLBACK_ENABLED" = true ]; then
        echo -e "${YELLOW}Initiating automatic rollback...${NC}"
        kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
        echo -e "${YELLOW}Rollback initiated. Check status with: kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE${NC}"
    fi
    
    exit 1
fi
echo ""

# Step 5: Health check
echo -e "${YELLOW}Step 5: Health check${NC}"

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod \
    -l app=$DEPLOYMENT_NAME \
    -n $NAMESPACE \
    --timeout=2m

# Get pod IP for health check
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o jsonpath='{.items[0].metadata.name}')
echo "Testing health endpoint on pod: $POD_NAME"

# Port forward for health check
kubectl port-forward -n $NAMESPACE $POD_NAME 8000:8000 &
PORT_FORWARD_PID=$!
sleep 5

# Health check with retry
MAX_RETRIES=5
RETRY_COUNT=0
HEALTH_CHECK_PASSED=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Health check attempt $((RETRY_COUNT + 1))/$MAX_RETRIES..."
    
    if curl -f -s $HEALTH_CHECK_URL > /dev/null; then
        HEALTH_CHECK_PASSED=true
        echo -e "${GREEN}✓ Health check passed${NC}"
        break
    else
        echo "Health check failed, retrying in 10 seconds..."
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

# Kill port forward
kill $PORT_FORWARD_PID 2>/dev/null || true

if [ "$HEALTH_CHECK_PASSED" = false ]; then
    echo -e "${RED}✗ Health check failed after $MAX_RETRIES attempts${NC}"
    
    if [ "$ROLLBACK_ENABLED" = true ]; then
        echo -e "${YELLOW}Initiating automatic rollback...${NC}"
        kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    fi
    
    exit 1
fi
echo ""

# Step 6: Smoke tests
echo -e "${YELLOW}Step 6: Running smoke tests${NC}"

if [ -f "$SMOKE_TEST_SCRIPT" ]; then
    if bash $SMOKE_TEST_SCRIPT; then
        echo -e "${GREEN}✓ Smoke tests passed${NC}"
    else
        echo -e "${RED}✗ Smoke tests failed${NC}"
        
        if [ "$ROLLBACK_ENABLED" = true ]; then
            echo -e "${YELLOW}Initiating automatic rollback...${NC}"
            kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
        fi
        
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: Smoke test script not found${NC}"
fi
echo ""

# Step 7: Post-deployment verification
echo -e "${YELLOW}Step 7: Post-deployment verification${NC}"

# Check pod status
echo "Pod status:"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME

# Check deployment status
echo ""
echo "Deployment status:"
kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE

# Check service endpoints
echo ""
echo "Service endpoints:"
kubectl get endpoints -n $NAMESPACE -l app=$DEPLOYMENT_NAME

echo ""
echo -e "${GREEN}✓ Post-deployment verification completed${NC}"
echo ""

# Step 8: Deployment summary
echo -e "${GREEN}=== Deployment Summary ===${NC}"
echo "Status: SUCCESS"
echo "Deployment: $DEPLOYMENT_NAME"
echo "Namespace: $NAMESPACE"
echo "Image: $DEPLOYMENT_NAME:$IMAGE_TAG"
echo "Timestamp: $(date)"
echo "Backup: $BACKUP_FILE"
echo ""

# Step 9: Monitoring instructions
echo -e "${YELLOW}=== Monitoring Instructions ===${NC}"
echo "1. Check logs:"
echo "   kubectl logs -f deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
echo ""
echo "2. Check metrics:"
echo "   kubectl top pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME"
echo ""
echo "3. Access Grafana dashboard:"
echo "   kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "   Open: http://localhost:3000/d/video-api-dashboard"
echo ""
echo "4. Check Prometheus alerts:"
echo "   kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "   Open: http://localhost:9090/alerts"
echo ""
echo "5. Rollback if needed:"
echo "   kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
echo ""

echo -e "${GREEN}=== Deployment Completed Successfully ===${NC}"
