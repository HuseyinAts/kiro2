#!/bin/bash

# Smoke Tests - Learning Path Video Fix
# Quick validation tests after deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TIMEOUT=10

echo -e "${GREEN}=== Running Smoke Tests ===${NC}"
echo "API Base URL: $API_BASE_URL"
echo "Timestamp: $(date)"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "Testing: $test_name... "
    
    if eval $test_command > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test 1: API Connectivity
echo -e "${YELLOW}Test 1: API Connectivity${NC}"
run_test "API reachable" "curl -f -s --max-time $TIMEOUT $API_BASE_URL/api/youtube/test"
echo ""

# Test 2: Health Check Endpoint
echo -e "${YELLOW}Test 2: Health Check Endpoint${NC}"
run_test "Health endpoint responds" "curl -f -s --max-time $TIMEOUT $API_BASE_URL/api/youtube/health"

# Verify health status
HEALTH_RESPONSE=$(curl -s --max-time $TIMEOUT $API_BASE_URL/api/youtube/health)
HEALTH_STATUS=$(echo $HEALTH_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo -e "Health status: ${GREEN}$HEALTH_STATUS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "Health status: ${RED}$HEALTH_STATUS${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 3: Video Recommendations Endpoint
echo -e "${YELLOW}Test 3: Video Recommendations Endpoint${NC}"

# Create test payload
TEST_PAYLOAD='{
  "goals": ["TYT Matematik"],
  "currentLevel": {"matematik": 50},
  "learningStyle": "visual",
  "preferences": {}
}'

# Test recommendations endpoint
run_test "Recommendations endpoint responds" "curl -f -s --max-time 30 -X POST \
    -H 'Content-Type: application/json' \
    -d '$TEST_PAYLOAD' \
    $API_BASE_URL/api/youtube/recommendations"

# Verify response structure
RECOMMENDATIONS_RESPONSE=$(curl -s --max-time 30 -X POST \
    -H 'Content-Type: application/json' \
    -d "$TEST_PAYLOAD" \
    $API_BASE_URL/api/youtube/recommendations 2>/dev/null)

if echo "$RECOMMENDATIONS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); sys.exit(0 if isinstance(data, list) and len(data) > 0 else 1)" 2>/dev/null; then
    echo -e "Response structure: ${GREEN}✓ Valid${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "Response structure: ${RED}✗ Invalid${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4: Response Time
echo -e "${YELLOW}Test 4: Response Time${NC}"

START_TIME=$(date +%s%N)
curl -f -s --max-time 30 -X POST \
    -H 'Content-Type: application/json' \
    -d "$TEST_PAYLOAD" \
    $API_BASE_URL/api/youtube/recommendations > /dev/null 2>&1
END_TIME=$(date +%s%N)

RESPONSE_TIME_MS=$(( (END_TIME - START_TIME) / 1000000 ))

echo "Response time: ${RESPONSE_TIME_MS}ms"

if [ $RESPONSE_TIME_MS -lt 5000 ]; then
    echo -e "Performance: ${GREEN}✓ Good (<5s)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "Performance: ${YELLOW}⚠ Slow (>5s)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 5: Error Handling
echo -e "${YELLOW}Test 5: Error Handling${NC}"

# Test with invalid payload
INVALID_PAYLOAD='{"invalid": "data"}'

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT -X POST \
    -H 'Content-Type: application/json' \
    -d "$INVALID_PAYLOAD" \
    $API_BASE_URL/api/youtube/recommendations)

if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "Error handling: ${GREEN}✓ Returns proper error code ($HTTP_CODE)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "Error handling: ${RED}✗ Unexpected code ($HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 6: CORS Headers
echo -e "${YELLOW}Test 6: CORS Headers${NC}"

CORS_HEADERS=$(curl -s -I --max-time $TIMEOUT -X OPTIONS \
    -H "Origin: http://localhost:3001" \
    -H "Access-Control-Request-Method: POST" \
    $API_BASE_URL/api/youtube/recommendations)

if echo "$CORS_HEADERS" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "CORS headers: ${GREEN}✓ Present${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "CORS headers: ${RED}✗ Missing${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 7: Rate Limiting
echo -e "${YELLOW}Test 7: Rate Limiting${NC}"

# Send multiple requests quickly
RATE_LIMIT_TRIGGERED=false
for i in {1..15}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT \
        $API_BASE_URL/api/youtube/test)
    
    if [ "$HTTP_CODE" = "429" ]; then
        RATE_LIMIT_TRIGGERED=true
        break
    fi
done

if [ "$RATE_LIMIT_TRIGGERED" = true ]; then
    echo -e "Rate limiting: ${GREEN}✓ Working (429 returned)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "Rate limiting: ${YELLOW}⚠ Not triggered (may need adjustment)${NC}"
fi
echo ""

# Test Summary
echo -e "${GREEN}=== Smoke Test Summary ===${NC}"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some smoke tests failed!${NC}"
    exit 1
fi
