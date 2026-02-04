#!/bin/bash
# Tool Call Hook
# Runs BEFORE any tool is called
# Purpose: Monitor Write tool usage for report files and provide reminders

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Check if Write tool is being used for report files
if [ "$TOOL_NAME" = "Write" ]; then
    # Extract file path from arguments (basic parsing)
    FILE_PATH=$(echo "$TOOL_ARGS" | grep -o '"file_path":"[^"]*"' | cut -d'"' -f4)

    # Check if it's a report file
    if echo "$FILE_PATH" | grep -qi "report\|summary\|status\|completion"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⚠️  REPORT FILE WRITE DETECTED: $FILE_PATH"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📋 PRE-WRITE CHECKLIST:"
        echo ""
        echo "Required BEFORE writing report:"
        echo "  [ ] Run: py .claude/scripts/check_database.py"
        echo "  [ ] Run: bash .claude/scripts/check_mocks.sh"
        echo "  [ ] Include actual numbers (not estimates)"
        echo "  [ ] Add evidence blocks with command outputs"
        echo "  [ ] Use objective % scale"
        echo "  [ ] List all known issues"
        echo ""
        echo "Required AFTER writing report:"
        echo "  [ ] Run: bash .claude/hooks/post-report-write.sh $FILE_PATH"
        echo "  [ ] Check verification score ≥ 75/100"
        echo ""
        echo "See: .claude/instructions.md and REPORTING_STANDARDS.md"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    fi
fi

# Always exit 0 to allow tool call to proceed
exit 0
