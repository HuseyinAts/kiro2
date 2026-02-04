#!/bin/bash
# Pre-Report-Write Hook
# Runs BEFORE any report is written to gather facts

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 PRE-REPORT VERIFICATION - Gathering Facts..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Change to project root
cd "$(dirname "$0")/../.." || exit 1

# Create facts directory
mkdir -p .claude/facts

# Check for stale facts
if [ -f .claude/facts/latest.json ]; then
    # Get file modification time (seconds since epoch)
    if [ "$(uname)" = "Darwin" ] || [ "$(uname)" = "Linux" ]; then
        # macOS/Linux
        FACTS_MTIME=$(stat -f %m .claude/facts/latest.json 2>/dev/null || stat -c %Y .claude/facts/latest.json 2>/dev/null)
    else
        # Windows/Git Bash - use Python for cross-platform compatibility
        FACTS_MTIME=$(python -c "import os; print(int(os.path.getmtime('.claude/facts/latest.json')))" 2>/dev/null || echo "0")
    fi

    CURRENT_TIME=$(date +%s)
    FACTS_AGE=$((CURRENT_TIME - FACTS_MTIME))
    FACTS_AGE_MINUTES=$((FACTS_AGE / 60))

    # Warn if facts are older than 1 hour (3600 seconds)
    if [ $FACTS_AGE -gt 3600 ]; then
        echo ""
        echo "⚠️  WARNING: Existing facts file is STALE"
        echo "   Age: $FACTS_AGE_MINUTES minutes old"
        echo "   Location: .claude/facts/latest.json"
        echo "   Recommendation: Running fresh verification now..."
        echo ""
    fi
fi

# Timestamp
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
FACTS_FILE=".claude/facts/facts_${TIMESTAMP}.json"

echo "{"  > "$FACTS_FILE"
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$FACTS_FILE"
echo "  \"checks\": {" >> "$FACTS_FILE"

# 1. Database Check
echo "📊 Checking Database..."
if python .claude/scripts/check_database.py > /dev/null 2>&1; then
    echo "   ✓ Database check completed"
    DB_EXIT_CODE=$?
else
    echo "   ⚠️  Database check had warnings (exit code: $?)"
    DB_EXIT_CODE=$?
fi

# Copy database facts
if [ -f .claude/scripts/database_facts.json ]; then
    echo "    \"database\": $(cat .claude/scripts/database_facts.json)," >> "$FACTS_FILE"
else
    echo "    \"database\": {\"error\": \"Check failed\"}," >> "$FACTS_FILE"
fi

echo ""

# 2. Mock Data Check
echo "🎭 Checking Mock Data..."
if bash .claude/scripts/check_mocks.sh > /dev/null 2>&1; then
    echo "   ✓ Mock check completed"
    MOCK_EXIT_CODE=$?
else
    echo "   ⚠️  Mock check had warnings (exit code: $?)"
    MOCK_EXIT_CODE=$?
fi

# Copy mock facts
if [ -f .claude/scripts/mock_facts.json ]; then
    echo "    \"mocks\": $(cat .claude/scripts/mock_facts.json)," >> "$FACTS_FILE"
else
    echo "    \"mocks\": {\"error\": \"Check failed\"}," >> "$FACTS_FILE"
fi

echo ""

# 3. Git Status (uncommitted changes)
echo "📝 Checking Git Status..."
GIT_MODIFIED=$(git status --porcelain | wc -l)
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
GIT_COMMIT=$(git rev-parse --short HEAD)

echo "   Branch: $GIT_BRANCH"
echo "   Commit: $GIT_COMMIT"
echo "   Modified files: $GIT_MODIFIED"

echo "    \"git\": {" >> "$FACTS_FILE"
echo "      \"branch\": \"$GIT_BRANCH\"," >> "$FACTS_FILE"
echo "      \"commit\": \"$GIT_COMMIT\"," >> "$FACTS_FILE"
echo "      \"modified_files\": $GIT_MODIFIED" >> "$FACTS_FILE"
echo "    }," >> "$FACTS_FILE"

echo ""

# 4. Backend Status (if running)
echo "🖥️  Checking Backend..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✓ Backend is running"
    BACKEND_STATUS="running"
    HEALTH_RESPONSE=$(curl -s http://localhost:8001/health)
else
    echo "   ❌ Backend not running"
    BACKEND_STATUS="not_running"
    HEALTH_RESPONSE="{}"
fi

echo "    \"backend\": {" >> "$FACTS_FILE"
echo "      \"status\": \"$BACKEND_STATUS\"," >> "$FACTS_FILE"
echo "      \"health\": $HEALTH_RESPONSE" >> "$FACTS_FILE"
echo "    }," >> "$FACTS_FILE"

echo ""

# 5. File Counts
echo "📁 Counting Files..."
PY_FILES=$(find backend -name "*.py" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" 2>/dev/null | wc -l)
TSX_FILES=$(find frontend/src -name "*.tsx" -o -name "*.ts" 2>/dev/null | wc -l)
MD_FILES=$(find . -name "*.md" ! -path "*/node_modules/*" 2>/dev/null | wc -l)

echo "   Python files: $PY_FILES"
echo "   TypeScript files: $TSX_FILES"
echo "   Markdown files: $MD_FILES"

echo "    \"files\": {" >> "$FACTS_FILE"
echo "      \"python\": $PY_FILES," >> "$FACTS_FILE"
echo "      \"typescript\": $TSX_FILES," >> "$FACTS_FILE"
echo "      \"markdown\": $MD_FILES" >> "$FACTS_FILE"
echo "    }" >> "$FACTS_FILE"

# Close JSON
echo "  }" >> "$FACTS_FILE"
echo "}" >> "$FACTS_FILE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Facts Gathered Successfully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📄 Facts saved to: $FACTS_FILE"
echo ""

# Create symlink to latest facts
ln -sf "$FACTS_FILE" .claude/facts/latest.json

# Warning Messages Based on Checks
if [ $DB_EXIT_CODE -eq 1 ]; then
    echo "⚠️  WARNING: Database is EMPTY or has critical issues"
    echo "   Before reporting 'database ready', verify tables are populated"
    echo ""
fi

if [ $MOCK_EXIT_CODE -eq 1 ]; then
    echo "⚠️  WARNING: HIGH number of mock data occurrences"
    echo "   Before reporting 'production-ready', replace mock data with real implementations"
    echo ""
fi

if [ "$BACKEND_STATUS" != "running" ]; then
    echo "⚠️  WARNING: Backend is not running"
    echo "   Cannot verify API endpoint functionality"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 REPORTING REMINDERS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ DO:"
echo "   - Report ACTUAL numbers from facts file"
echo "   - Include evidence (command outputs)"
echo "   - Acknowledge known issues"
echo "   - Use objective readiness scale (0-100%)"
echo ""
echo "❌ DON'T:"
echo "   - Say 'production-ready' without proof"
echo "   - Report goals as if achieved"
echo "   - Hide mock data or TODOs"
echo "   - Use '100%' without verification"
echo ""
echo "📖 See: .claude/instructions.md and REPORTING_STANDARDS.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
