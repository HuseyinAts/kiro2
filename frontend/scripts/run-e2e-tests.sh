#!/bin/bash

###############################################################################
# E2E Test Runner Script
# 
# Bu script, Learning Path video loading E2E testlerini local ortamda
# çalıştırmak için gerekli tüm adımları otomatikleştirir.
#
# Kullanım:
#   ./scripts/run-e2e-tests.sh [options]
#
# Options:
#   --headed        Tarayıcıyı görünür modda çalıştır
#   --debug         Debug modunda çalıştır
#   --ui            UI modunda çalıştır
#   --browser       Belirli bir tarayıcıda çalıştır (chromium, firefox, webkit)
#   --help          Bu yardım mesajını göster
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
HEADED=false
DEBUG=false
UI=false
BROWSER=""
BACKEND_PORT=8001
FRONTEND_PORT=3002

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --headed)
      HEADED=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --ui)
      UI=true
      shift
      ;;
    --browser)
      BROWSER="$2"
      shift 2
      ;;
    --help)
      echo "E2E Test Runner"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --headed        Run browser in headed mode"
      echo "  --debug         Run in debug mode"
      echo "  --ui            Run in UI mode"
      echo "  --browser       Run specific browser (chromium, firefox, webkit)"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         E2E Test Runner - Video Loading Tests             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if backend is running
echo -e "${YELLOW}[1/6] Checking backend server...${NC}"
if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Backend is running on port $BACKEND_PORT${NC}"
else
  echo -e "${RED}✗ Backend is not running!${NC}"
  echo -e "${YELLOW}Please start the backend server first:${NC}"
  echo -e "  cd backend && python -m uvicorn main:app --port $BACKEND_PORT"
  exit 1
fi

# Check if frontend is running
echo -e "${YELLOW}[2/6] Checking frontend server...${NC}"
if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Frontend is running on port $FRONTEND_PORT${NC}"
else
  echo -e "${RED}✗ Frontend is not running!${NC}"
  echo -e "${YELLOW}Please start the frontend server first:${NC}"
  echo -e "  cd frontend && npm run dev"
  exit 1
fi

# Check if Playwright is installed
echo -e "${YELLOW}[3/6] Checking Playwright installation...${NC}"
if [ ! -d "node_modules/@playwright/test" ]; then
  echo -e "${RED}✗ Playwright is not installed!${NC}"
  echo -e "${YELLOW}Installing Playwright...${NC}"
  npm install
fi
echo -e "${GREEN}✓ Playwright is installed${NC}"

# Check if Playwright browsers are installed
echo -e "${YELLOW}[4/6] Checking Playwright browsers...${NC}"
if ! npx playwright --version > /dev/null 2>&1; then
  echo -e "${RED}✗ Playwright browsers are not installed!${NC}"
  echo -e "${YELLOW}Installing Playwright browsers...${NC}"
  npx playwright install --with-deps
fi
echo -e "${GREEN}✓ Playwright browsers are installed${NC}"

# Set environment variables
echo -e "${YELLOW}[5/6] Setting environment variables...${NC}"
export VITE_API_URL=http://localhost:$BACKEND_PORT
export VITE_APP_URL=http://localhost:$FRONTEND_PORT
echo -e "${GREEN}✓ Environment variables set${NC}"

# Build test command
echo -e "${YELLOW}[6/6] Running E2E tests...${NC}"
TEST_CMD="npx playwright test"

if [ "$UI" = true ]; then
  TEST_CMD="$TEST_CMD --ui"
elif [ "$DEBUG" = true ]; then
  TEST_CMD="$TEST_CMD --debug"
elif [ "$HEADED" = true ]; then
  TEST_CMD="$TEST_CMD --headed"
fi

if [ -n "$BROWSER" ]; then
  TEST_CMD="$TEST_CMD --project=$BROWSER"
fi

echo -e "${BLUE}Running: $TEST_CMD${NC}"
echo ""

# Run tests
if eval $TEST_CMD; then
  echo ""
  echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║                  ✓ All tests passed!                       ║${NC}"
  echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${BLUE}View test report:${NC}"
  echo -e "  npm run test:e2e:report"
  exit 0
else
  echo ""
  echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}║                  ✗ Some tests failed!                      ║${NC}"
  echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${YELLOW}Debugging tips:${NC}"
  echo -e "  1. Check screenshots: test-results/screenshots/"
  echo -e "  2. Check videos: test-results/videos/"
  echo -e "  3. View test report: npm run test:e2e:report"
  echo -e "  4. Run in debug mode: $0 --debug"
  echo -e "  5. Run in UI mode: $0 --ui"
  exit 1
fi
