#!/bin/bash

# WebSocket Load Test Runner for KIRO2
#
# Usage:
#   ./run_websocket_load_test.sh [mode] [users] [spawn_rate] [duration]
#
# Modes:
#   smoke      - Quick CI test (50 users, 2min)
#   dev        - Development test (100 users, 5min)
#   staging    - Staging test (500 users, 10min)
#   production - Production test (1000 users, 15min)
#   stress     - Stress test (5000 users, 30min)
#   pytest     - Run pytest smoke test
#
# Examples:
#   ./run_websocket_load_test.sh smoke
#   ./run_websocket_load_test.sh dev
#   ./run_websocket_load_test.sh production
#   ./run_websocket_load_test.sh pytest
#   ./run_websocket_load_test.sh custom 2000 100 20m

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE="${1:-dev}"
HOST="${KIRO2_HOST:-http://localhost:8000}"
RESULTS_DIR="results"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if backend is running
check_backend() {
    print_info "Checking if backend is running at $HOST..."

    if curl -s -f "$HOST/health" > /dev/null 2>&1; then
        print_success "Backend is running!"
        return 0
    else
        print_error "Backend is not running at $HOST"
        print_info "Start backend with: cd backend && uvicorn main:app --reload --port 8000"
        return 1
    fi
}

# Function to run pytest smoke test
run_pytest() {
    print_info "Running pytest smoke test..."

    if ! check_backend; then
        exit 1
    fi

    pytest tests/load/test_websocket_load.py -v --timeout=300

    if [ $? -eq 0 ]; then
        print_success "Pytest smoke test passed!"
    else
        print_error "Pytest smoke test failed!"
        exit 1
    fi
}

# Function to run locust test
run_locust() {
    local users=$1
    local spawn_rate=$2
    local duration=$3
    local mode_name=$4

    print_info "Running $mode_name load test..."
    print_info "  Users: $users"
    print_info "  Spawn Rate: $spawn_rate users/sec"
    print_info "  Duration: $duration"
    print_info "  Host: $HOST"

    if ! check_backend; then
        exit 1
    fi

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local csv_prefix="${RESULTS_DIR}/websocket_${mode_name}_${timestamp}"

    print_info "Results will be saved to: $csv_prefix*.csv"

    locust -f tests/load/locustfile_websocket.py \
        --users "$users" \
        --spawn-rate "$spawn_rate" \
        --run-time "$duration" \
        --host "$HOST" \
        --headless \
        --csv="$csv_prefix" \
        --html="${csv_prefix}.html" \
        --logfile="${csv_prefix}.log"

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        print_success "Load test completed successfully!"
        print_info "Results:"
        print_info "  CSV: ${csv_prefix}_stats.csv"
        print_info "  HTML: ${csv_prefix}.html"
        print_info "  Log: ${csv_prefix}.log"
    else
        print_error "Load test failed with exit code: $exit_code"
        exit $exit_code
    fi
}

# Main execution
case "$MODE" in
    pytest)
        print_info "=== PYTEST SMOKE TEST ==="
        run_pytest
        ;;

    smoke)
        print_info "=== SMOKE TEST MODE ==="
        run_locust 50 10 "2m" "smoke"
        ;;

    dev)
        print_info "=== DEVELOPMENT TEST MODE ==="
        run_locust 100 20 "5m" "dev"
        ;;

    staging)
        print_info "=== STAGING TEST MODE ==="
        run_locust 500 50 "10m" "staging"
        ;;

    production)
        print_info "=== PRODUCTION TEST MODE ==="
        run_locust 1000 50 "15m" "production"
        ;;

    stress)
        print_info "=== STRESS TEST MODE ==="
        print_warning "This will run a high-load stress test!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_locust 5000 100 "30m" "stress"
        else
            print_info "Stress test cancelled."
            exit 0
        fi
        ;;

    custom)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
            print_error "Custom mode requires: users spawn_rate duration"
            print_info "Example: $0 custom 2000 100 20m"
            exit 1
        fi

        print_info "=== CUSTOM TEST MODE ==="
        run_locust "$2" "$3" "$4" "custom"
        ;;

    *)
        print_error "Unknown mode: $MODE"
        echo
        echo "Usage: $0 [mode]"
        echo
        echo "Available modes:"
        echo "  pytest       - Run pytest smoke test"
        echo "  smoke        - Quick CI test (50 users, 2min)"
        echo "  dev          - Development test (100 users, 5min)"
        echo "  staging      - Staging test (500 users, 10min)"
        echo "  production   - Production test (1000 users, 15min)"
        echo "  stress       - Stress test (5000 users, 30min)"
        echo "  custom       - Custom test (requires users, spawn_rate, duration)"
        echo
        echo "Examples:"
        echo "  $0 smoke"
        echo "  $0 dev"
        echo "  $0 production"
        echo "  $0 custom 2000 100 20m"
        echo
        echo "Environment variables:"
        echo "  KIRO2_HOST   - Backend host (default: http://localhost:8000)"
        echo
        exit 1
        ;;
esac

print_success "All tests completed!"
