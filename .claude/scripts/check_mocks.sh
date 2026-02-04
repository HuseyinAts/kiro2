#!/bin/bash
# Mock Data Detector for Kiro2 Project
# Scans codebase for mock, hardcoded, TODO, and placeholder code

echo "============================================================"
echo "KIRO2 MOCK DATA & TODO DETECTOR"
echo "============================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Colors for output (if supported)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Counters
total_mocks=0
total_todos=0
total_fixmes=0
total_hardcoded=0

# Output file
OUTPUT_JSON=".claude/scripts/mock_facts.json"
mkdir -p "$(dirname "$OUTPUT_JSON")"

echo "{" > "$OUTPUT_JSON"
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$OUTPUT_JSON"
echo "  \"scans\": {" >> "$OUTPUT_JSON"

# Function to scan directory
scan_directory() {
    local dir=$1
    local pattern=$2
    local label=$3
    local extensions=$4

    echo "📁 Scanning: $dir ($label)"

    if [ ! -d "$dir" ]; then
        echo "   ❌ Directory not found"
        echo "    \"$label\": {\"error\": \"Directory not found\"}," >> "$OUTPUT_JSON"
        return
    fi

    # Count occurrences
    local mock_count=$(grep -ri "mock" "$dir" $extensions 2>/dev/null | wc -l)
    local todo_count=$(grep -ri "TODO\|FIXME\|XXX\|HACK" "$dir" $extensions 2>/dev/null | wc -l)
    local hardcoded_count=$(grep -ri "hardcoded\|placeholder\|fake\|dummy" "$dir" $extensions 2>/dev/null | wc -l)

    # Update totals
    total_mocks=$((total_mocks + mock_count))
    total_todos=$((total_todos + todo_count))
    total_hardcoded=$((total_hardcoded + hardcoded_count))

    echo "   Mock occurrences: $mock_count"
    echo "   TODO/FIXME: $todo_count"
    echo "   Hardcoded/Placeholder: $hardcoded_count"

    # List top files with mocks
    if [ $mock_count -gt 0 ]; then
        echo "   Top files with 'mock':"
        grep -ril "mock" "$dir" $extensions 2>/dev/null | head -5 | while read file; do
            local count=$(grep -i "mock" "$file" 2>/dev/null | wc -l)
            echo "      - $file ($count)"
        done
    fi

    echo ""

    # JSON output
    echo "    \"$label\": {" >> "$OUTPUT_JSON"
    echo "      \"directory\": \"$dir\"," >> "$OUTPUT_JSON"
    echo "      \"mock_count\": $mock_count," >> "$OUTPUT_JSON"
    echo "      \"todo_count\": $todo_count," >> "$OUTPUT_JSON"
    echo "      \"hardcoded_count\": $hardcoded_count" >> "$OUTPUT_JSON"
    echo "    }," >> "$OUTPUT_JSON"
}

# Scan backend services
scan_directory "backend/services" "" "Backend Services" "--include=*.py"

# Scan backend API routes
scan_directory "backend/api" "" "Backend API Routes" "--include=*.py"

# Scan backend core
scan_directory "backend/core" "" "Backend Core" "--include=*.py"

# Scan frontend pages
scan_directory "frontend/src/pages" "" "Frontend Pages" "--include=*.tsx --include=*.ts"

# Scan frontend components
scan_directory "frontend/src/components" "" "Frontend Components" "--include=*.tsx --include=*.ts"

# Close JSON (remove trailing comma)
echo "    \"summary\": {}" >> "$OUTPUT_JSON"
echo "  }," >> "$OUTPUT_JSON"

# Summary
echo "============================================================"
echo "SUMMARY"
echo "============================================================"
echo "Total 'mock' occurrences: $total_mocks"
echo "Total 'TODO/FIXME': $total_todos"
echo "Total 'hardcoded/placeholder': $total_hardcoded"
echo ""

# Add summary to JSON
echo "  \"summary\": {" >> "$OUTPUT_JSON"
echo "    \"total_mocks\": $total_mocks," >> "$OUTPUT_JSON"
echo "    \"total_todos\": $total_todos," >> "$OUTPUT_JSON"
echo "    \"total_hardcoded\": $total_hardcoded," >> "$OUTPUT_JSON"
echo "    \"grand_total\": $((total_mocks + total_todos + total_hardcoded))" >> "$OUTPUT_JSON"
echo "  }," >> "$OUTPUT_JSON"

# Assessment
echo "ASSESSMENT:"
if [ $total_mocks -gt 100 ]; then
    echo "❌ CRITICAL: High number of mock data ($total_mocks occurrences)"
    echo "   - System heavily reliant on mock data"
    echo "   - NOT production-ready"
    echo ""
    echo "REPORTING GUIDANCE:"
    echo "   ❌ Do NOT say: 'System fully functional' or 'Production-ready'"
    echo "   ✓ DO say: 'System in development with $total_mocks mock data points'"
    assessment="critical"
elif [ $total_mocks -gt 50 ]; then
    echo "⚠️  WARNING: Moderate mock data ($total_mocks occurrences)"
    echo "   - Significant mock data still present"
    echo "   - Needs refactoring before production"
    echo ""
    echo "REPORTING GUIDANCE:"
    echo "   ⚠️  Do NOT say: '100% production-ready'"
    echo "   ✓ DO say: 'Core functionality implemented, $total_mocks mock data points being replaced'"
    assessment="warning"
elif [ $total_mocks -gt 10 ]; then
    echo "✓ ACCEPTABLE: Low mock data ($total_mocks occurrences)"
    echo "   - Minimal mock data (likely in tests or fallbacks)"
    echo "   - Approaching production-ready"
    echo ""
    echo "REPORTING GUIDANCE:"
    echo "   ✓ 'System functional with $total_mocks remaining mock data points (non-critical)'"
    assessment="acceptable"
else
    echo "✓ EXCELLENT: Minimal to no mock data ($total_mocks occurrences)"
    echo "   - Clean codebase"
    echo "   - Production-ready from mock perspective"
    echo ""
    echo "REPORTING GUIDANCE:"
    echo "   ✓ 'System production-ready (mock data removed)'"
    assessment="excellent"
fi

echo ""

# Add assessment to JSON
echo "  \"assessment\": \"$assessment\"" >> "$OUTPUT_JSON"
echo "}" >> "$OUTPUT_JSON"

echo "📄 Detailed results saved to: $OUTPUT_JSON"
echo ""

# Find specific problematic patterns
echo "============================================================"
echo "SPECIFIC ISSUES DETECTED"
echo "============================================================"

# Check for common anti-patterns
echo "Checking for anti-patterns..."

# Hardcoded statistics
hardcoded_stats=$(grep -ri "tamamlanan_dersler=45\|ortalama_puan=78" backend/services/ frontend/src/ 2>/dev/null | wc -l)
if [ $hardcoded_stats -gt 0 ]; then
    echo "⚠️  Found $hardcoded_stats hardcoded statistics (should be from DB)"
    grep -rn "tamamlanan_dersler=45\|ortalama_puan=78" backend/services/ frontend/src/ 2>/dev/null | head -3
    echo ""
fi

# Mock response messages
mock_responses=$(grep -ri "This is a placeholder\|Mock response\|FAKE" backend/ frontend/src/ 2>/dev/null | wc -l)
if [ $mock_responses -gt 0 ]; then
    echo "⚠️  Found $mock_responses mock response messages"
    grep -rn "This is a placeholder\|Mock response\|FAKE" backend/ frontend/src/ 2>/dev/null | head -3
    echo ""
fi

# TODO in production code (not tests)
prod_todos=$(grep -ri "TODO\|FIXME" backend/services/ backend/api/ frontend/src/pages/ 2>/dev/null | grep -v test | wc -l)
if [ $prod_todos -gt 20 ]; then
    echo "⚠️  Found $prod_todos TODOs in production code (excluding tests)"
    echo "   Consider creating tickets for these items"
    echo ""
fi

echo "============================================================"
echo ""

# Exit codes
if [ $total_mocks -gt 100 ]; then
    exit 1  # Critical
elif [ $total_mocks -gt 50 ]; then
    exit 2  # Warning
else
    exit 0  # OK
fi
