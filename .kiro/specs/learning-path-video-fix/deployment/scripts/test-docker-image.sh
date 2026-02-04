#!/bin/bash
# ============================================================================
# Docker Image Testing Script
# Comprehensive testing before production deployment
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
IMAGE_NAME="${IMAGE_NAME:-ghcr.io/turkiye-sinav/video-api:latest}"
CONTAINER_NAME="video-api-test-$$"
TEST_PORT="${TEST_PORT:-8000}"
TIMEOUT="${TIMEOUT:-60}"

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT

# Test 1: Image exists
test_image_exists() {
    log_info "Test 1: Checking if image exists..."
    
    if docker image inspect "${IMAGE_NAME}" &> /dev/null; then
        log_success "Image exists"
        return 0
    else
        log_error "Image not found: ${IMAGE_NAME}"
        return 1
    fi
}

# Test 2: Image size
test_image_size() {
    log_info "Test 2: Checking image size..."
    
    local size=$(docker image inspect "${IMAGE_NAME}" \
        --format='{{.Size}}' | awk '{print $1/1024/1024}')
    
    log_info "Image size: ${size} MB"
    
    if (( $(echo "$size < 2000" | bc -l) )); then
        log_success "Image size is acceptable (< 2GB)"
        return 0
    else
        log_warning "Image size is large (> 2GB)"
        return 0
    fi
}

# Test 3: Image labels
test_image_labels() {
    log_info "Test 3: Checking image labels..."
    
    local labels=$(docker image inspect "${IMAGE_NAME}" \
        --format='{{json .Config.Labels}}')
    
    if echo "${labels}" | grep -q "org.opencontainers.image"; then
        log_success "Image has proper labels"
        return 0
    else
        log_warning "Image missing OCI labels"
        return 0
    fi
}

# Test 4: Container starts
test_container_starts() {
    log_info "Test 4: Starting container..."
    
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${TEST_PORT}:8000" \
        -e DATABASE_URL="sqlite:///./test.db" \
        -e REDIS_URL="redis://localhost:6379/0" \
        -e YOUTUBE_API_KEY="test_key" \
        -e ENVIRONMENT="test" \
        -e DEBUG="false" \
        "${IMAGE_NAME}" || {
            log_error "Failed to start container"
            return 1
        }
    
    log_success "Container started"
    return 0
}

# Test 5: Container health
test_container_health() {
    log_info "Test 5: Waiting for container to be healthy..."
    
    local retries=0
    local max_retries=$((TIMEOUT / 5))
    
    while [ ${retries} -lt ${max_retries} ]; do
        if docker exec "${CONTAINER_NAME}" \
            curl -sf http://localhost:8000/api/youtube/health &> /dev/null; then
            log_success "Container is healthy"
            return 0
        fi
        
        retries=$((retries + 1))
        log_info "Waiting for health check... (${retries}/${max_retries})"
        sleep 5
    done
    
    log_error "Container health check failed"
    docker logs "${CONTAINER_NAME}"
    return 1
}

# Test 6: Health endpoint response
test_health_endpoint() {
    log_info "Test 6: Testing health endpoint response..."
    
    local response=$(docker exec "${CONTAINER_NAME}" \
        curl -s http://localhost:8000/api/youtube/health)
    
    if echo "${response}" | grep -q '"status"'; then
        log_success "Health endpoint returns valid JSON"
        
        # Check status field
        if echo "${response}" | grep -q '"status":"healthy"'; then
            log_success "Health status is healthy"
        else
            log_warning "Health status is not healthy: ${response}"
        fi
        
        return 0
    else
        log_error "Health endpoint response invalid: ${response}"
        return 1
    fi
}

# Test 7: API test endpoint
test_api_test_endpoint() {
    log_info "Test 7: Testing API test endpoint..."
    
    local response=$(docker exec "${CONTAINER_NAME}" \
        curl -s http://localhost:8000/api/youtube/test)
    
    if echo "${response}" | grep -q '"status":"ok"'; then
        log_success "API test endpoint works"
        return 0
    else
        log_error "API test endpoint failed: ${response}"
        return 1
    fi
}

# Test 8: Metrics endpoint
test_metrics_endpoint() {
    log_info "Test 8: Testing metrics endpoint..."
    
    local response=$(docker exec "${CONTAINER_NAME}" \
        curl -s http://localhost:8000/metrics)
    
    if echo "${response}" | grep -q "http_requests_total"; then
        log_success "Metrics endpoint works"
        return 0
    else
        log_warning "Metrics endpoint may not be configured"
        return 0
    fi
}

# Test 9: Container logs
test_container_logs() {
    log_info "Test 9: Checking container logs..."
    
    local logs=$(docker logs "${CONTAINER_NAME}" 2>&1)
    
    # Check for errors
    if echo "${logs}" | grep -qi "error\|exception\|traceback"; then
        log_warning "Container logs contain errors:"
        echo "${logs}" | grep -i "error\|exception\|traceback" | head -5
    else
        log_success "No errors in container logs"
    fi
    
    # Check for startup message
    if echo "${logs}" | grep -q "Starting Video API"; then
        log_success "Container started successfully"
    fi
    
    return 0
}

# Test 10: Resource usage
test_resource_usage() {
    log_info "Test 10: Checking resource usage..."
    
    local stats=$(docker stats "${CONTAINER_NAME}" --no-stream --format \
        "CPU: {{.CPUPerc}}, Memory: {{.MemUsage}}")
    
    log_info "Resource usage: ${stats}"
    log_success "Resource usage check completed"
    return 0
}

# Test 11: Turkish locale
test_turkish_locale() {
    log_info "Test 11: Testing Turkish locale..."
    
    local locale=$(docker exec "${CONTAINER_NAME}" locale | grep LANG)
    
    if echo "${locale}" | grep -q "tr_TR"; then
        log_success "Turkish locale configured"
        return 0
    else
        log_warning "Turkish locale may not be configured: ${locale}"
        return 0
    fi
}

# Test 12: Timezone
test_timezone() {
    log_info "Test 12: Testing timezone..."
    
    local tz=$(docker exec "${CONTAINER_NAME}" date +%Z)
    
    if [ "${tz}" = "+03" ] || [ "${tz}" = "TRT" ]; then
        log_success "Timezone set to Turkey"
        return 0
    else
        log_warning "Timezone may not be set to Turkey: ${tz}"
        return 0
    fi
}

# Test 13: Non-root user
test_non_root_user() {
    log_info "Test 13: Checking if running as non-root..."
    
    local user=$(docker exec "${CONTAINER_NAME}" whoami)
    
    if [ "${user}" != "root" ]; then
        log_success "Container running as non-root user: ${user}"
        return 0
    else
        log_error "Container running as root (security risk)"
        return 1
    fi
}

# Test 14: File permissions
test_file_permissions() {
    log_info "Test 14: Checking file permissions..."
    
    local perms=$(docker exec "${CONTAINER_NAME}" \
        ls -la /app | grep -E "logs|cache|temp")
    
    if echo "${perms}" | grep -q "videoapi"; then
        log_success "File permissions correct"
        return 0
    else
        log_warning "File permissions may be incorrect"
        return 0
    fi
}

# Test 15: Python version
test_python_version() {
    log_info "Test 15: Checking Python version..."
    
    local version=$(docker exec "${CONTAINER_NAME}" python --version)
    
    if echo "${version}" | grep -q "Python 3.11"; then
        log_success "Python version correct: ${version}"
        return 0
    else
        log_warning "Python version unexpected: ${version}"
        return 0
    fi
}

# Test 16: Dependencies installed
test_dependencies() {
    log_info "Test 16: Checking dependencies..."
    
    local deps="fastapi uvicorn redis asyncpg"
    
    for dep in ${deps}; do
        if docker exec "${CONTAINER_NAME}" \
            python -c "import ${dep}" 2>/dev/null; then
            log_info "✓ ${dep} installed"
        else
            log_error "✗ ${dep} not installed"
            return 1
        fi
    done
    
    log_success "All dependencies installed"
    return 0
}

# Test 17: Graceful shutdown
test_graceful_shutdown() {
    log_info "Test 17: Testing graceful shutdown..."
    
    docker stop -t 30 "${CONTAINER_NAME}" &> /dev/null
    
    local exit_code=$(docker inspect "${CONTAINER_NAME}" \
        --format='{{.State.ExitCode}}')
    
    if [ "${exit_code}" = "0" ]; then
        log_success "Container shut down gracefully"
        return 0
    else
        log_warning "Container exit code: ${exit_code}"
        return 0
    fi
}

# Main test runner
main() {
    log_info "Starting Docker image tests..."
    log_info "Image: ${IMAGE_NAME}"
    echo ""
    
    local failed_tests=0
    local total_tests=17
    
    # Run tests
    test_image_exists || ((failed_tests++))
    test_image_size || ((failed_tests++))
    test_image_labels || ((failed_tests++))
    test_container_starts || ((failed_tests++))
    test_container_health || ((failed_tests++))
    test_health_endpoint || ((failed_tests++))
    test_api_test_endpoint || ((failed_tests++))
    test_metrics_endpoint || ((failed_tests++))
    test_container_logs || ((failed_tests++))
    test_resource_usage || ((failed_tests++))
    test_turkish_locale || ((failed_tests++))
    test_timezone || ((failed_tests++))
    test_non_root_user || ((failed_tests++))
    test_file_permissions || ((failed_tests++))
    test_python_version || ((failed_tests++))
    test_dependencies || ((failed_tests++))
    test_graceful_shutdown || ((failed_tests++))
    
    # Summary
    echo ""
    log_info "Test Summary:"
    echo "Total tests: ${total_tests}"
    echo "Passed: $((total_tests - failed_tests))"
    echo "Failed: ${failed_tests}"
    
    if [ ${failed_tests} -eq 0 ]; then
        log_success "All tests passed! ✓"
        return 0
    else
        log_error "${failed_tests} test(s) failed! ✗"
        return 1
    fi
}

# Run tests
main
