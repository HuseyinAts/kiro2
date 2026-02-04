#!/bin/bash

# Post-Deployment Verification Script
# Comprehensive checks after production deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="${NAMESPACE:-production}"
DEPLOYMENT_NAME="video-api"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
VERIFICATION_DURATION=300  # 5 minutes

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Post-Deployment Verification - Video API              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Namespace: $NAMESPACE"
echo "Deployment: $DEPLOYMENT_NAME"
echo "Verification Duration: ${VERIFICATION_DURATION}s"
echo "Timestamp: $(date)"
echo ""

# Verification results
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Helper function
check_status() {
    local check_name=$1
    local status=$2
    local message=$3
    
    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✓${NC} $check_name: $message"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [ "$status" = "fail" ]; then
        echo -e "${RED}✗${NC} $check_name: $message"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    else
        echo -e "${YELLOW}⚠${NC} $check_name: $message"
        CHECKS_WARNING=$((CHECKS_WARNING + 1))
    fi
}

# ============================================================================
# Section 1: Kubernetes Resources
# ============================================================================
echo -e "${YELLOW}═══ Section 1: Kubernetes Resources ═══${NC}"
echo ""

# Check 1.1: Deployment Status
echo "Check 1.1: Deployment Status"
DEPLOYMENT_STATUS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "Unknown")

if [ "$DEPLOYMENT_STATUS" = "True" ]; then
    REPLICAS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.replicas}')
    READY_REPLICAS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    check_status "Deployment Available" "pass" "$READY_REPLICAS/$REPLICAS replicas ready"
else
    check_status "Deployment Available" "fail" "Deployment not available"
fi
echo ""

# Check 1.2: Pod Status
echo "Check 1.2: Pod Status"
POD_COUNT=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME --field-selector=status.phase=Running -o json | jq '.items | length')
TOTAL_PODS=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o json | jq '.items | length')

if [ $POD_COUNT -eq $TOTAL_PODS ] && [ $POD_COUNT -gt 0 ]; then
    check_status "Pods Running" "pass" "$POD_COUNT/$TOTAL_PODS pods running"
else
    check_status "Pods Running" "fail" "Only $POD_COUNT/$TOTAL_PODS pods running"
fi
echo ""

# Check 1.3: Pod Restarts
echo "Check 1.3: Pod Restart Count"
MAX_RESTARTS=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o json | jq '[.items[].status.containerStatuses[].restartCount] | max')

if [ "$MAX_RESTARTS" = "null" ] || [ $MAX_RESTARTS -eq 0 ]; then
    check_status "Pod Restarts" "pass" "No restarts detected"
elif [ $MAX_RESTARTS -lt 3 ]; then
    check_status "Pod Restarts" "warning" "$MAX_RESTARTS restarts detected"
else
    check_status "Pod Restarts" "fail" "$MAX_RESTARTS restarts detected (too many)"
fi
echo ""

# Check 1.4: Resource Usage
echo "Check 1.4: Resource Usage"
echo "Current resource usage:"
kubectl top pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME 2>/dev/null || echo "Metrics not available"
echo ""

# ============================================================================
# Section 2: Health Checks
# ============================================================================
echo -e "${YELLOW}═══ Section 2: Health Checks ═══${NC}"
echo ""

# Setup port forwarding for health checks
echo "Setting up port forwarding..."
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward -n $NAMESPACE $POD_NAME 8000:8000 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!
sleep 3

# Check 2.1: API Connectivity
echo "Check 2.1: API Connectivity"
if curl -f -s --max-time 10 $API_BASE_URL/api/youtube/test > /dev/null 2>&1; then
    check_status "API Connectivity" "pass" "API is reachable"
else
    check_status "API Connectivity" "fail" "API is not reachable"
fi
echo ""

# Check 2.2: Health Endpoint
echo "Check 2.2: Health Endpoint"
HEALTH_RESPONSE=$(curl -s --max-time 10 $API_BASE_URL/api/youtube/health 2>/dev/null)
HEALTH_STATUS=$(echo $HEALTH_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

if [ "$HEALTH_STATUS" = "healthy" ]; then
    check_status "Health Status" "pass" "System is healthy"
elif [ "$HEALTH_STATUS" = "degraded" ]; then
    check_status "Health Status" "warning" "System is degraded"
else
    check_status "Health Status" "fail" "System is unhealthy or unreachable"
fi

# Check component health
if [ "$HEALTH_STATUS" != "unknown" ]; then
    echo "Component health details:"
    echo $HEALTH_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for component in data.get('components', []):
        status = component.get('status', 'unknown')
        name = component.get('name', 'unknown')
        color = '\033[0;32m' if status == 'healthy' else '\033[0;31m'
        print(f'  {color}●\033[0m {name}: {status}')
except:
    pass
" 2>/dev/null
fi
echo ""

# Check 2.3: Database Connectivity
echo "Check 2.3: Database Connectivity"
DB_STATUS=$(echo $HEALTH_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for comp in data.get('components', []):
        if comp.get('name') == 'Database':
            print(comp.get('status', 'unknown'))
            break
except:
    print('unknown')
" 2>/dev/null)

if [ "$DB_STATUS" = "healthy" ]; then
    check_status "Database" "pass" "Database is healthy"
else
    check_status "Database" "fail" "Database is $DB_STATUS"
fi
echo ""

# Check 2.4: Redis Cache
echo "Check 2.4: Redis Cache"
REDIS_STATUS=$(echo $HEALTH_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for comp in data.get('components', []):
        if 'Redis' in comp.get('name', ''):
            print(comp.get('status', 'unknown'))
            break
except:
    print('unknown')
" 2>/dev/null)

if [ "$REDIS_STATUS" = "healthy" ]; then
    check_status "Redis Cache" "pass" "Redis is healthy"
else
    check_status "Redis Cache" "fail" "Redis is $REDIS_STATUS"
fi
echo ""

# Check 2.5: YouTube API
echo "Check 2.5: YouTube API"
YOUTUBE_STATUS=$(echo $HEALTH_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for comp in data.get('components', []):
        if 'YouTube' in comp.get('name', ''):
            print(comp.get('status', 'unknown'))
            break
except:
    print('unknown')
" 2>/dev/null)

if [ "$YOUTUBE_STATUS" = "healthy" ]; then
    check_status "YouTube API" "pass" "YouTube API is healthy"
else
    check_status "YouTube API" "warning" "YouTube API is $YOUTUBE_STATUS"
fi
echo ""

# ============================================================================
# Section 3: Functional Tests
# ============================================================================
echo -e "${YELLOW}═══ Section 3: Functional Tests ═══${NC}"
echo ""

# Check 3.1: Video Recommendations Endpoint
echo "Check 3.1: Video Recommendations Endpoint"
TEST_PAYLOAD='{"goals":["TYT Matematik"],"currentLevel":{"matematik":50},"learningStyle":"visual","preferences":{}}'

START_TIME=$(date +%s%N)
RECOMMENDATIONS_RESPONSE=$(curl -s --max-time 30 -X POST \
    -H 'Content-Type: application/json' \
    -d "$TEST_PAYLOAD" \
    $API_BASE_URL/api/youtube/recommendations 2>/dev/null)
END_TIME=$(date +%s%N)

RESPONSE_TIME_MS=$(( (END_TIME - START_TIME) / 1000000 ))

if echo "$RECOMMENDATIONS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); sys.exit(0 if isinstance(data, list) else 1)" 2>/dev/null; then
    VIDEO_COUNT=$(echo "$RECOMMENDATIONS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(sum(len(item.get('videos', [])) for item in data))" 2>/dev/null)
    check_status "Recommendations" "pass" "Returned $VIDEO_COUNT videos in ${RESPONSE_TIME_MS}ms"
else
    check_status "Recommendations" "fail" "Invalid response or error"
fi
echo ""

# Check 3.2: Response Time Performance
echo "Check 3.2: Response Time Performance"
if [ $RESPONSE_TIME_MS -lt 3000 ]; then
    check_status "Response Time" "pass" "${RESPONSE_TIME_MS}ms (target: <3000ms)"
elif [ $RESPONSE_TIME_MS -lt 5000 ]; then
    check_status "Response Time" "warning" "${RESPONSE_TIME_MS}ms (target: <3000ms)"
else
    check_status "Response Time" "fail" "${RESPONSE_TIME_MS}ms (target: <3000ms)"
fi
echo ""

# Check 3.3: Turkish Content Filtering
echo "Check 3.3: Turkish Content Filtering"
if [ ! -z "$RECOMMENDATIONS_RESPONSE" ]; then
    TURKISH_VIDEO_COUNT=$(echo "$RECOMMENDATIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    turkish_count = 0
    total_count = 0
    for item in data:
        for video in item.get('videos', []):
            total_count += 1
            title = video.get('title', '')
            # Check for Turkish characters
            if any(c in title for c in 'çğıöşüÇĞİÖŞÜ'):
                turkish_count += 1
    print(f'{turkish_count}/{total_count}')
except:
    print('0/0')
" 2>/dev/null)
    
    check_status "Turkish Content" "pass" "$TURKISH_VIDEO_COUNT videos contain Turkish characters"
fi
echo ""

# Check 3.4: Error Handling
echo "Check 3.4: Error Handling"
INVALID_PAYLOAD='{"invalid":"data"}'
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -X POST \
    -H 'Content-Type: application/json' \
    -d "$INVALID_PAYLOAD" \
    $API_BASE_URL/api/youtube/recommendations)

if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    check_status "Error Handling" "pass" "Returns proper error code ($HTTP_CODE)"
else
    check_status "Error Handling" "fail" "Unexpected error code ($HTTP_CODE)"
fi
echo ""

# Kill port forward
kill $PORT_FORWARD_PID 2>/dev/null || true

# ============================================================================
# Section 4: Monitoring & Metrics
# ============================================================================
echo -e "${YELLOW}═══ Section 4: Monitoring & Metrics ═══${NC}"
echo ""

# Check 4.1: Prometheus Metrics
echo "Check 4.1: Prometheus Metrics Endpoint"
kubectl port-forward -n $NAMESPACE $POD_NAME 8000:8000 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!
sleep 3

if curl -f -s --max-time 10 http://localhost:8000/metrics > /dev/null 2>&1; then
    METRIC_COUNT=$(curl -s --max-time 10 http://localhost:8000/metrics | grep -c "^video_" || echo "0")
    check_status "Metrics Endpoint" "pass" "$METRIC_COUNT video metrics available"
else
    check_status "Metrics Endpoint" "fail" "Metrics endpoint not accessible"
fi

kill $PORT_FORWARD_PID 2>/dev/null || true
echo ""

# Check 4.2: Grafana Dashboard
echo "Check 4.2: Grafana Dashboard"
echo "Please verify Grafana dashboard manually:"
echo "  URL: $GRAFANA_URL/d/video-api-dashboard"
echo "  Expected panels: Request Rate, Response Time, Error Rate, Cache Hit Rate"
echo ""

# Check 4.3: Prometheus Alerts
echo "Check 4.3: Prometheus Alerts"
echo "Please verify Prometheus alerts manually:"
echo "  URL: $PROMETHEUS_URL/alerts"
echo "  Expected alerts: HighErrorRate, SlowResponseTime, LowCacheHitRate, YouTubeQuotaLow"
echo ""

# ============================================================================
# Section 5: Performance Monitoring (5 minutes)
# ============================================================================
echo -e "${YELLOW}═══ Section 5: Performance Monitoring (${VERIFICATION_DURATION}s) ═══${NC}"
echo ""

echo "Monitoring system performance for ${VERIFICATION_DURATION} seconds..."
echo "This will track:"
echo "  - Request rate"
echo "  - Error rate"
echo "  - Response time"
echo "  - Resource usage"
echo ""

# Setup port forwarding for monitoring
kubectl port-forward -n $NAMESPACE $POD_NAME 8000:8000 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!
sleep 3

# Initial metrics
INITIAL_REQUESTS=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep "video_requests_total" | grep -v "#" | awk '{sum+=$2} END {print sum}' || echo "0")
INITIAL_ERRORS=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep 'video_requests_total.*status="error"' | awk '{sum+=$2} END {print sum}' || echo "0")

echo "Initial metrics captured. Waiting ${VERIFICATION_DURATION}s..."
sleep $VERIFICATION_DURATION

# Final metrics
FINAL_REQUESTS=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep "video_requests_total" | grep -v "#" | awk '{sum+=$2} END {print sum}' || echo "0")
FINAL_ERRORS=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep 'video_requests_total.*status="error"' | awk '{sum+=$2} END {print sum}' || echo "0")

# Calculate rates
REQUEST_RATE=$(echo "scale=2; ($FINAL_REQUESTS - $INITIAL_REQUESTS) / $VERIFICATION_DURATION" | bc)
ERROR_RATE=$(echo "scale=2; ($FINAL_ERRORS - $INITIAL_ERRORS) / $VERIFICATION_DURATION" | bc)

if [ $(echo "$FINAL_REQUESTS > $INITIAL_REQUESTS" | bc) -eq 1 ]; then
    ERROR_PERCENTAGE=$(echo "scale=2; (($FINAL_ERRORS - $INITIAL_ERRORS) / ($FINAL_REQUESTS - $INITIAL_REQUESTS)) * 100" | bc)
else
    ERROR_PERCENTAGE="0"
fi

echo ""
echo "Performance Results:"
echo "  Request Rate: $REQUEST_RATE req/sec"
echo "  Error Rate: $ERROR_RATE errors/sec"
echo "  Error Percentage: $ERROR_PERCENTAGE%"
echo ""

# Evaluate performance
if [ $(echo "$ERROR_PERCENTAGE < 1" | bc) -eq 1 ]; then
    check_status "Error Rate" "pass" "Error rate is ${ERROR_PERCENTAGE}% (<1%)"
elif [ $(echo "$ERROR_PERCENTAGE < 5" | bc) -eq 1 ]; then
    check_status "Error Rate" "warning" "Error rate is ${ERROR_PERCENTAGE}% (<5%)"
else
    check_status "Error Rate" "fail" "Error rate is ${ERROR_PERCENTAGE}% (>5%)"
fi

kill $PORT_FORWARD_PID 2>/dev/null || true
echo ""

# ============================================================================
# Section 6: Logs Analysis
# ============================================================================
echo -e "${YELLOW}═══ Section 6: Logs Analysis ═══${NC}"
echo ""

# Check 6.1: Error Logs
echo "Check 6.1: Recent Error Logs"
ERROR_LOG_COUNT=$(kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=500 --since=5m 2>/dev/null | grep -c "ERROR" || echo "0")

if [ $ERROR_LOG_COUNT -eq 0 ]; then
    check_status "Error Logs" "pass" "No errors in last 5 minutes"
elif [ $ERROR_LOG_COUNT -lt 10 ]; then
    check_status "Error Logs" "warning" "$ERROR_LOG_COUNT errors in last 5 minutes"
else
    check_status "Error Logs" "fail" "$ERROR_LOG_COUNT errors in last 5 minutes"
fi
echo ""

# Check 6.2: Warning Logs
echo "Check 6.2: Recent Warning Logs"
WARNING_LOG_COUNT=$(kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=500 --since=5m 2>/dev/null | grep -c "WARNING" || echo "0")

if [ $WARNING_LOG_COUNT -lt 5 ]; then
    check_status "Warning Logs" "pass" "$WARNING_LOG_COUNT warnings in last 5 minutes"
elif [ $WARNING_LOG_COUNT -lt 20 ]; then
    check_status "Warning Logs" "warning" "$WARNING_LOG_COUNT warnings in last 5 minutes"
else
    check_status "Warning Logs" "fail" "$WARNING_LOG_COUNT warnings in last 5 minutes"
fi
echo ""

# ============================================================================
# Final Summary
# ============================================================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Verification Summary                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Checks Passed:  ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks Warning: ${YELLOW}$CHECKS_WARNING${NC}"
echo -e "Checks Failed:  ${RED}$CHECKS_FAILED${NC}"
echo -e "Total Checks:   $((CHECKS_PASSED + CHECKS_WARNING + CHECKS_FAILED))"
echo ""

# Overall status
if [ $CHECKS_FAILED -eq 0 ] && [ $CHECKS_WARNING -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment verification PASSED - All checks successful!${NC}"
    EXIT_CODE=0
elif [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ Deployment verification PASSED with warnings${NC}"
    echo "Please review warnings and monitor closely."
    EXIT_CODE=0
else
    echo -e "${RED}✗ Deployment verification FAILED${NC}"
    echo "Please investigate failed checks and consider rollback."
    EXIT_CODE=1
fi

echo ""
echo "Verification completed at: $(date)"
echo ""

# Next steps
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Monitor Grafana dashboard for 24 hours"
echo "2. Check Prometheus alerts regularly"
echo "3. Review application logs for any issues"
echo "4. Monitor user feedback and support tickets"
echo "5. Schedule post-deployment review meeting"
echo ""

exit $EXIT_CODE
