#!/bin/bash
# Post-Report-Write Hook
# Runs AFTER a report is written to verify claims against facts

# Check if report file was provided
if [ -z "$1" ]; then
    echo "Usage: post-report-write.sh <report_file.md>"
    exit 1
fi

REPORT_FILE="$1"

if [ ! -f "$REPORT_FILE" ]; then
    echo "Error: Report file not found: $REPORT_FILE"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔎 POST-REPORT VERIFICATION - Checking Claims..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Report: $REPORT_FILE"
echo ""

# Change to project root
cd "$(dirname "$0")/../.." || exit 1

# Load latest facts
FACTS_FILE=".claude/facts/latest.json"

if [ ! -f "$FACTS_FILE" ]; then
    echo "⚠️  WARNING: No facts file found"
    echo "   Run pre-report-write.sh first to gather facts"
    echo ""
    exit 1
fi

# Check for forbidden phrases
echo "🚫 Checking for Forbidden Phrases..."
FORBIDDEN_FOUND=0

# Check each forbidden phrase
check_phrase() {
    local phrase="$1"
    local guidance="$2"

    if grep -qi "$phrase" "$REPORT_FILE"; then
        echo "   ❌ Found: '$phrase'"
        echo "      Guidance: $guidance"
        FORBIDDEN_FOUND=$((FORBIDDEN_FOUND + 1))
    fi
}

check_phrase "production-ready" "Only use if deployed to production with real users"
check_phrase "100% complete" "Use specific % based on objective criteria"
check_phrase "fully functional" "Verify all features work with manual tests"
check_phrase "10,000+ sorular" "Report actual count from database query"
check_phrase "all tests passing" "Include test output as evidence"
check_phrase "world-class" "Avoid subjective claims"
check_phrase "revolutionary" "Avoid marketing language"

if [ $FORBIDDEN_FOUND -eq 0 ]; then
    echo "   ✓ No forbidden phrases found"
fi
echo ""

# Check for evidence
echo "📊 Checking for Evidence..."
EVIDENCE_SCORE=0

if grep -q '```bash' "$REPORT_FILE"; then
    echo "   ✓ Contains bash command blocks"
    EVIDENCE_SCORE=$((EVIDENCE_SCORE + 1))
fi

if grep -q '```' "$REPORT_FILE"; then
    echo "   ✓ Contains code blocks (evidence)"
    EVIDENCE_SCORE=$((EVIDENCE_SCORE + 1))
fi

if grep -qi 'evidence:\|proof:\|verification:' "$REPORT_FILE"; then
    echo "   ✓ Contains evidence sections"
    EVIDENCE_SCORE=$((EVIDENCE_SCORE + 1))
fi

if grep -q 'Assessment:' "$REPORT_FILE"; then
    echo "   ✓ Contains assessment sections"
    EVIDENCE_SCORE=$((EVIDENCE_SCORE + 1))
fi

if [ $EVIDENCE_SCORE -lt 2 ]; then
    echo "   ⚠️  WARNING: Low evidence score ($EVIDENCE_SCORE/4)"
    echo "      Add more command outputs and verification"
fi
echo ""

# Compare claims with facts
echo "🔍 Comparing Claims with Facts..."

# Extract database row count from facts
if command -v python >/dev/null 2>&1 || command -v py >/dev/null 2>&1; then
    PYTHON_CMD=$(command -v python || command -v py)
    DB_ROWS=$($PYTHON_CMD -c "import json; f=open('$FACTS_FILE'); data=json.load(f); print(data.get('checks', {}).get('database', {}).get('summary', {}).get('total_rows', 0))" 2>/dev/null || echo "0")
    MOCK_COUNT=$($PYTHON_CMD -c "import json; f=open('$FACTS_FILE'); data=json.load(f); print(data.get('checks', {}).get('mocks', {}).get('summary', {}).get('total_mocks', 0))" 2>/dev/null || echo "0")
else
    echo "   ⚠️  WARNING: Python not found - cannot extract facts"
    DB_ROWS="unknown"
    MOCK_COUNT="unknown"
fi

echo "   Facts (from .claude/facts/latest.json):"
echo "      - Database rows: $DB_ROWS"
echo "      - Mock occurrences: $MOCK_COUNT"
echo ""

# Check database claims
if grep -qi "10,000" "$REPORT_FILE" && [ "$DB_ROWS" -lt 1000 ]; then
    echo "   ⚠️  DISCREPANCY: Report mentions '10,000' but database has $DB_ROWS rows"
fi

if grep -qi "database.*ready\|database.*operational" "$REPORT_FILE" && [ "$DB_ROWS" -lt 100 ]; then
    echo "   ⚠️  DISCREPANCY: Report says 'database ready' but only $DB_ROWS rows found"
fi

# Check mock claims
if grep -qi "production.ready" "$REPORT_FILE" && [ "$MOCK_COUNT" -gt 100 ]; then
    echo "   ⚠️  DISCREPANCY: Report says 'production-ready' but $MOCK_COUNT mock occurrences found"
fi

if ! grep -qi "mock" "$REPORT_FILE" && [ "$MOCK_COUNT" -gt 50 ]; then
    echo "   ⚠️  WARNING: Report doesn't mention mocks but $MOCK_COUNT occurrences exist"
fi

echo ""

# Calculate verification score
VERIFICATION_SCORE=0

# Has evidence blocks (+25)
if [ $EVIDENCE_SCORE -ge 3 ]; then
    VERIFICATION_SCORE=$((VERIFICATION_SCORE + 25))
fi

# No forbidden phrases (+25)
if [ $FORBIDDEN_FOUND -eq 0 ]; then
    VERIFICATION_SCORE=$((VERIFICATION_SCORE + 25))
fi

# Mentions database facts (+25)
if grep -qi "database" "$REPORT_FILE" && grep -q "$DB_ROWS" "$REPORT_FILE"; then
    VERIFICATION_SCORE=$((VERIFICATION_SCORE + 25))
fi

# Mentions mocks or issues (+25)
if grep -qi "mock\|issue\|warning\|gap" "$REPORT_FILE"; then
    VERIFICATION_SCORE=$((VERIFICATION_SCORE + 25))
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VERIFICATION SCORE: $VERIFICATION_SCORE/100"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Rating
if [ $VERIFICATION_SCORE -ge 75 ]; then
    echo "✅ EXCELLENT: Report appears well-verified"
elif [ $VERIFICATION_SCORE -ge 50 ]; then
    echo "⚠️  GOOD: Report has some verification, could improve"
elif [ $VERIFICATION_SCORE -ge 25 ]; then
    echo "⚠️  WARNING: Report lacks sufficient verification"
else
    echo "❌ CRITICAL: Report appears unverified"
fi

echo ""

# Append verification section to report
if [ $VERIFICATION_SCORE -lt 75 ] || [ $FORBIDDEN_FOUND -gt 0 ]; then
    echo "📝 Appending Verification Warning to Report..."
    echo "" >> "$REPORT_FILE"
    echo "---" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "## ⚠️ AUTOMATED VERIFICATION" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**Verification Score:** $VERIFICATION_SCORE/100" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    if [ $FORBIDDEN_FOUND -gt 0 ]; then
        echo "**Warnings:**" >> "$REPORT_FILE"
        echo "- Contains $FORBIDDEN_FOUND forbidden phrase(s) that require evidence" >> "$REPORT_FILE"
    fi

    if [ $EVIDENCE_SCORE -lt 3 ]; then
        echo "- Low evidence score ($EVIDENCE_SCORE/4) - add more command outputs" >> "$REPORT_FILE"
    fi

    echo "" >> "$REPORT_FILE"
    echo "**Ground Truth (from .claude/facts/latest.json):**" >> "$REPORT_FILE"
    echo "- Database rows: $DB_ROWS" >> "$REPORT_FILE"
    echo "- Mock data occurrences: $MOCK_COUNT" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "*Compare claims above with these facts. Discrepancies >20% indicate potential accuracy issues.*" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**See:** `.claude/instructions.md` for reporting standards" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "---" >> "$REPORT_FILE"

    echo "   ✅ Verification section appended to report"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Exit with warning code if score too low
if [ $VERIFICATION_SCORE -lt 50 ]; then
    echo "⚠️  Report verification FAILED (score < 50)"
    echo "   Consider revising report with more evidence"
    exit 1
else
    echo "✅ Report verification PASSED"
    exit 0
fi
