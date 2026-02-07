#!/bin/bash
# Test Setup Fixes Validation Script

echo "=================================="
echo "KIRO2 Frontend Test Setup Validation"
echo "=================================="
echo ""

cd "$(dirname "$0")"

echo "Running test suite..."
npm test -- --run --reporter=verbose > test_results.txt 2>&1

# Extract summary
echo ""
echo "Test Summary:"
echo "=================================="
grep -E "Test Files|Tests|Time" test_results.txt | tail -5

echo ""
echo "Failed Tests:"
echo "=================================="
grep -E "FAIL|failed" test_results.txt | head -20

echo ""
echo "Setup Error Check:"
echo "=================================="
grep -i "resizeObserver.observe is not a function" test_results.txt && echo "❌ ResizeObserver issue still exists" || echo "✅ ResizeObserver fixed"
grep -i "Should not already be working" test_results.txt && echo "❌ React concurrent mode issue still exists" || echo "✅ React concurrent mode fixed"

echo ""
echo "Full results saved to: test_results.txt"
