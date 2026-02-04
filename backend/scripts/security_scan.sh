#!/bin/bash
#
# Security Scanning Script
# Runs Bandit (code security) and Safety (dependency security)
#

echo "========================================="
echo "SECURITY SCANNING"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: Run this script from backend/ directory"
    exit 1
fi

# Install tools if needed
echo "[1/4] Installing security scanning tools..."
pip install bandit safety --quiet

echo ""
echo "[2/4] Running Bandit (Code Security Scan)..."
echo "-----------------------------------------"
bandit -r . \
    --exclude ./tests,./alembic \
    --format txt \
    --output bandit_report.txt \
    --severity-level medium

# Show summary
if [ -f "bandit_report.txt" ]; then
    echo "Bandit report saved to: bandit_report.txt"
    echo ""
    echo "Summary:"
    grep -A 5 "Test results:" bandit_report.txt || echo "No issues found"
fi

echo ""
echo "[3/4] Running Safety (Dependency Security Scan)..."
echo "---------------------------------------------------"
safety check --output text > safety_report.txt 2>&1

if [ -f "safety_report.txt" ]; then
    echo "Safety report saved to: safety_report.txt"
    echo ""
    echo "Summary:"
    head -20 safety_report.txt
fi

echo ""
echo "[4/4] Checking for hardcoded secrets..."
echo "----------------------------------------"
# Simple grep-based secret detection
echo "Searching for potential hardcoded secrets..."
grep -rn --include="*.py" \
    -e "password\s*=\s*['\"]" \
    -e "api_key\s*=\s*['\"]" \
    -e "secret\s*=\s*['\"]" \
    -e "token\s*=\s*['\"]" \
    . 2>/dev/null | grep -v ".env" | grep -v "test" | head -10 || echo "No obvious secrets found"

echo ""
echo "========================================="
echo "SECURITY SCAN COMPLETE"
echo "========================================="
echo ""
echo "Reports generated:"
echo "  - bandit_report.txt (code security issues)"
echo "  - safety_report.txt (vulnerable dependencies)"
echo ""
echo "Review these files and address any HIGH or MEDIUM severity issues."
