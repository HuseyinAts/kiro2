#!/bin/bash
# API Test Script for Kiro2 Platform

echo "================================================"
echo "Kiro2 Platform - API Testing"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo "Testing Backend API endpoints..."
echo ""

# Test 1: Health Check
echo -n "1. Health Check... "
HEALTH=$(curl -s ${BASE_URL}/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
    echo "   Response: $HEALTH"
else
    echo -e "${RED}FAILED${NC}"
fi
echo ""

# Test 2: Create TYT Exam
echo "2. Create TYT Exam..."
EXAM_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/osym-exam/olustur \
  -H "Content-Type: application/json" \
  -d '{"ogrenci_id": "test_student_001", "sinav_tipi": "TYT"}')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
    echo "   Response: $EXAM_RESPONSE" | head -c 200
    echo "..."
else
    echo -e "${RED}FAILED${NC}"
fi
echo ""

# Test 3: Create AYT Exam
echo "3. Create AYT Exam..."
AYT_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/osym-exam/olustur \
  -H "Content-Type: application/json" \
  -d '{"ogrenci_id": "test_student_002", "sinav_tipi": "AYT"}')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
    echo "   Response: $AYT_RESPONSE" | head -c 200
    echo "..."
else
    echo -e "${RED}FAILED${NC}"
fi
echo ""

# Test 4: ZPD Calculation
echo "4. Calculate ZPD (Turkish Cultural)..."
ZPD_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/zpd-maarif/hesapla \
  -H "Content-Type: application/json" \
  -d '{
    "ogrenci_id": "test_student_003",
    "konu": "matematik",
    "mevcut_seviye": 6.0
  }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
    echo "   Response: $ZPD_RESPONSE" | head -c 200
    echo "..."
else
    echo -e "${RED}FAILED${NC}"
fi
echo ""

echo "================================================"
echo "API Testing Complete"
echo "================================================"
echo ""
echo "For more tests, check:"
echo "- Backend tests: cd backend && pytest -v"
echo "- ZPD tests: cd backend && python run_zpd_tests.py"
echo "- API docs: ${BASE_URL}/docs"
echo ""
