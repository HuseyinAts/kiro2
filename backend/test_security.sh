#!/bin/bash
# KIRO2 Security Testing Script
# Tests: JWT, Rate Limiting, Input Validation, CORS

set -e

API_URL="${API_URL:-http://localhost:8000}"
COLORS=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# ==================== 1. HEALTH CHECK ====================
print_section "1. Health Check"

print_test "Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")

if [ "$HEALTH_RESPONSE" -eq 200 ]; then
    print_pass "Health endpoint is up (200)"
else
    print_fail "Health endpoint returned $HEALTH_RESPONSE"
    exit 1
fi

# ==================== 2. CORS TESTS ====================
print_section "2. CORS Configuration"

print_test "Testing CORS with allowed origin..."
CORS_RESPONSE=$(curl -s -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -X OPTIONS "$API_URL/api/test" \
    -w "\n%{http_code}" | tail -n1)

if [ "$CORS_RESPONSE" -eq 200 ]; then
    print_pass "CORS allows localhost:3000"
else
    print_warn "CORS test returned $CORS_RESPONSE"
fi

print_test "Testing CORS with disallowed origin..."
CORS_BLOCKED=$(curl -s -H "Origin: http://evil.com" \
    -H "Access-Control-Request-Method: POST" \
    -X OPTIONS "$API_URL/api/test" \
    -i | grep -i "access-control-allow-origin" || echo "BLOCKED")

if [ "$CORS_BLOCKED" = "BLOCKED" ]; then
    print_pass "CORS blocks evil.com"
else
    print_fail "CORS allows evil.com (security risk!)"
fi

# ==================== 3. RATE LIMITING TESTS ====================
print_section "3. Rate Limiting"

print_test "Testing rate limiting (sending 150 requests)..."
RATE_LIMIT_HIT=false

for i in {1..150}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/test" || echo "000")

    if [ "$STATUS" -eq 429 ]; then
        RATE_LIMIT_HIT=true
        print_pass "Rate limit activated at request $i (429 Too Many Requests)"
        break
    fi

    # Progress indicator
    if [ $((i % 20)) -eq 0 ]; then
        echo -n "."
    fi
done

echo ""

if [ "$RATE_LIMIT_HIT" = false ]; then
    print_warn "Rate limit not hit after 150 requests"
else
    # Test Retry-After header
    RETRY_AFTER=$(curl -s -i "$API_URL/api/test" | grep -i "retry-after" | awk '{print $2}' | tr -d '\r')
    if [ -n "$RETRY_AFTER" ]; then
        print_pass "Retry-After header present: ${RETRY_AFTER}s"
    else
        print_warn "Retry-After header missing"
    fi
fi

# ==================== 4. INPUT VALIDATION TESTS ====================
print_section "4. Input Validation"

print_test "Testing SQL injection protection..."
SQL_INJECTION_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "$API_URL/api/search?q='; DROP TABLE users--")

if [ "$SQL_INJECTION_RESPONSE" -eq 403 ]; then
    print_pass "SQL injection blocked (403)"
elif [ "$SQL_INJECTION_RESPONSE" -eq 400 ]; then
    print_pass "SQL injection blocked (400)"
else
    print_fail "SQL injection not blocked! Response: $SQL_INJECTION_RESPONSE"
fi

print_test "Testing XSS protection..."
XSS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$API_URL/api/comment" \
    -H "Content-Type: application/json" \
    -d '{"text":"<script>alert(1)</script>"}')

if [ "$XSS_RESPONSE" -eq 403 ]; then
    print_pass "XSS blocked (403)"
elif [ "$XSS_RESPONSE" -eq 400 ]; then
    print_pass "XSS blocked (400)"
else
    print_fail "XSS not blocked! Response: $XSS_RESPONSE"
fi

print_test "Testing request size limit..."
LARGE_PAYLOAD=$(python3 -c "print('a' * (11 * 1024 * 1024))")  # 11MB
SIZE_LIMIT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$API_URL/api/upload" \
    -H "Content-Type: application/json" \
    -d "{\"data\":\"$LARGE_PAYLOAD\"}" || echo "000")

if [ "$SIZE_LIMIT_RESPONSE" -eq 413 ] || [ "$SIZE_LIMIT_RESPONSE" -eq 400 ]; then
    print_pass "Request size limit enforced (${SIZE_LIMIT_RESPONSE})"
else
    print_warn "Request size limit test returned $SIZE_LIMIT_RESPONSE"
fi

# ==================== 5. JWT AUTHENTICATION TESTS ====================
print_section "5. JWT Authentication"

print_test "Testing protected endpoint without token..."
NO_TOKEN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "$API_URL/api/protected")

if [ "$NO_TOKEN_RESPONSE" -eq 401 ]; then
    print_pass "Protected endpoint requires authentication (401)"
else
    print_warn "Protected endpoint returned $NO_TOKEN_RESPONSE"
fi

print_test "Testing with invalid token..."
INVALID_TOKEN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer invalid.token.here" \
    "$API_URL/api/protected")

if [ "$INVALID_TOKEN_RESPONSE" -eq 401 ]; then
    print_pass "Invalid token rejected (401)"
else
    print_warn "Invalid token test returned $INVALID_TOKEN_RESPONSE"
fi

# ==================== 6. SECURITY HEADERS TESTS ====================
print_section "6. Security Headers"

print_test "Checking security headers..."
HEADERS=$(curl -s -I "$API_URL/")

check_header() {
    HEADER_NAME=$1
    if echo "$HEADERS" | grep -qi "$HEADER_NAME"; then
        print_pass "$HEADER_NAME present"
    else
        print_fail "$HEADER_NAME missing"
    fi
}

check_header "X-Content-Type-Options"
check_header "X-Frame-Options"
check_header "X-XSS-Protection"
check_header "Strict-Transport-Security"
check_header "Content-Security-Policy"

# ==================== 7. BOT DETECTION TESTS ====================
print_section "7. Bot Detection"

print_test "Testing bot user-agent detection..."
BOT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -A "Mozilla/5.0 (compatible; Googlebot/2.1)" \
    "$API_URL/api/test")

if [ "$BOT_RESPONSE" -eq 403 ]; then
    print_pass "Bot user-agent blocked (403)"
elif [ "$BOT_RESPONSE" -eq 200 ]; then
    print_warn "Bot user-agent allowed (may be intentional for SEO)"
else
    print_warn "Bot detection returned $BOT_RESPONSE"
fi

# ==================== 8. ENDPOINT ENUMERATION TESTS ====================
print_section "8. Endpoint Security"

print_test "Testing endpoint enumeration protection..."
NOT_FOUND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "$API_URL/api/admin/secret-endpoint-12345")

if [ "$NOT_FOUND_RESPONSE" -eq 404 ]; then
    print_pass "Non-existent endpoint returns 404"
else
    print_warn "Non-existent endpoint returned $NOT_FOUND_RESPONSE"
fi

# ==================== SUMMARY ====================
print_section "Security Test Summary"

echo ""
echo "Security tests completed!"
echo ""
echo "Manual verification required:"
echo "  1. Check logs for security events"
echo "  2. Verify JWT secret is strong (min 32 chars)"
echo "  3. Review CORS origins for production"
echo "  4. Test with actual valid JWT tokens"
echo "  5. Monitor rate limit effectiveness in production"
echo ""
echo "For detailed security configuration, see: SECURITY.md"
echo ""
