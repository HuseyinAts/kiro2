#!/bin/bash
# Post Tool Use Hook
# Runs AUTOMATICALLY after any tool completes
# Purpose: Verify report files after writing

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Only process Write tool
if [ "$TOOL_NAME" = "Write" ]; then
    # Extract file path from tool arguments
    FILE_PATH=$(echo "$TOOL_ARGS" | grep -o '"file_path":"[^"]*"' | cut -d'"' -f4)

    # Check if it's a report file
    if echo "$FILE_PATH" | grep -qi "report\|summary\|status\|completion"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✓ REPORT FILE WRITTEN: $FILE_PATH"
        echo "   Running automatic verification..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        # Change to project root
        cd "$(dirname "$0")/../.." || exit 0

        # Check if file exists
        if [ -f "$FILE_PATH" ]; then
            # Run post-report verification
            bash .claude/hooks/post-report-write.sh "$FILE_PATH"
        else
            echo "⚠️  File not found: $FILE_PATH"
            echo "   Verification skipped"
        fi

        echo ""
    fi
fi

# Always exit 0 to allow processing to continue
exit 0
