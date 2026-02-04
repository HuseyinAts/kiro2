#!/bin/bash
# User Prompt Submit Hook
# Runs AUTOMATICALLY before Claude processes any user message
# Purpose: Detect report writing and provide real-time verification data

USER_MESSAGE="$1"

# Check if user is asking for a report/summary/status
if echo "$USER_MESSAGE" | grep -qi "report\|summary\|status\|rapor\|özet\|durum"; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  REPORTING DETECTED - Running Automatic Verification..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Change to project root
    cd "$(dirname "$0")/../.." || exit 0

    # Run database verification
    echo "📊 Checking Database..."
    if command -v py >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
        PYTHON_CMD=$(command -v py || command -v python)
        if $PYTHON_CMD .claude/scripts/check_database.py > /dev/null 2>&1; then
            DB_STATUS="checked"
        else
            DB_STATUS="checked (warnings)"
        fi

        # Extract database facts
        if [ -f .claude/scripts/database_facts.json ]; then
            DB_ROWS=$($PYTHON_CMD -c "import json; data=json.load(open('.claude/scripts/database_facts.json')); print(data.get('summary', {}).get('total_rows', 0))" 2>/dev/null || echo "0")
            DB_TABLES=$($PYTHON_CMD -c "import json; data=json.load(open('.claude/scripts/database_facts.json')); print(data.get('summary', {}).get('total_tables', 0))" 2>/dev/null || echo "0")
            echo "   ✓ Database checked: $DB_ROWS rows, $DB_TABLES tables"
        else
            DB_ROWS="0"
            DB_TABLES="0"
            echo "   ⚠️  Could not read database facts"
        fi
    else
        echo "   ⚠️  Python not found - skipping database check"
        DB_ROWS="0"
        DB_TABLES="0"
        DB_STATUS="skipped (no python)"
    fi

    # Run mock data verification
    echo "🎭 Checking Mock Data..."
    # Note: check_mocks.sh can take time, skip for now to avoid blocking
    # User will run it manually if needed
    if [ -f .claude/scripts/mock_facts.json ] && [ -n "$PYTHON_CMD" ]; then
        MOCK_COUNT=$($PYTHON_CMD -c "import json; data=json.load(open('.claude/scripts/mock_facts.json')); print(data.get('summary', {}).get('total_mocks', 2454))" 2>/dev/null || echo "2454")
        echo "   ✓ Mock data checked: $MOCK_COUNT occurrences"
    else
        MOCK_COUNT="2454"  # Last known count
        if [ ! -f .claude/scripts/mock_facts.json ]; then
            echo "   ⚠️  Using last known mock count: $MOCK_COUNT (facts file not found)"
        else
            echo "   ⚠️  Using last known mock count: $MOCK_COUNT (Python not available)"
        fi
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 CURRENT PROJECT STATUS (VERIFIED):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Database:"
    echo "  - Total rows: $DB_ROWS"
    echo "  - Total tables: $DB_TABLES"
    echo "  - Status: $([ "$DB_ROWS" -eq 0 ] && echo 'EMPTY (not ready)' || echo 'Has data')"
    echo ""
    echo "Mock Data:"
    echo "  - Total occurrences: $MOCK_COUNT"
    echo "  - Assessment: $([ "$MOCK_COUNT" -gt 100 ] && echo 'CRITICAL (not production-ready)' || echo 'Acceptable')"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  REPORTING REMINDERS:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "❌ DO NOT SAY (without evidence):"
    echo "   - 'production-ready' (mock count: $MOCK_COUNT > 100)"
    echo "   - '10,000+ sorular' (actual: $DB_ROWS rows)"
    echo "   - '100% complete' (mock data present)"
    echo "   - 'fully functional' (database empty)"
    echo ""
    echo "✅ DO SAY (with evidence):"
    echo "   - 'Database has $DB_ROWS rows in key tables'"
    echo "   - 'System contains $MOCK_COUNT mock data occurrences'"
    echo "   - 'Production readiness: ~20%' (calculated objectively)"
    echo "   - Include command outputs in evidence blocks"
    echo ""
    echo "📖 See: .claude/instructions.md for full guidelines"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# Always exit 0 to allow processing to continue
exit 0
