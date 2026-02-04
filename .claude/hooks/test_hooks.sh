#!/bin/bash
# Automated Hook Test Suite
# Tests all 5 hooks and generates report

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 HOOK SYSTEM AUTOMATED TEST SUITE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Change to project root
cd "$(dirname "$0")/../.." || exit 1

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test result tracking
declare -a TEST_RESULTS

# Helper function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "📋 Test $TOTAL_TESTS: $test_name"

    # Run the command and capture output
    output=$(eval "$test_command" 2>&1)
    exit_code=$?

    # Check if expected pattern is in output
    if echo "$output" | grep -q "$expected_pattern"; then
        echo "   ✅ PASS"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✅ $test_name")
    else
        echo "   ❌ FAIL"
        echo "      Expected pattern: $expected_pattern"
        echo "      Exit code: $exit_code"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ $test_name")
    fi
    echo ""
}

# Test 1: user-prompt-submit.sh
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST GROUP 1: UserPromptSubmit Hook"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "UserPromptSubmit - Detects 'report' keyword" \
    "bash .claude/hooks/user-prompt-submit.sh 'give me a report'" \
    "REPORTING DETECTED"

run_test "UserPromptSubmit - Shows database status" \
    "bash .claude/hooks/user-prompt-submit.sh 'status report'" \
    "Database:"

run_test "UserPromptSubmit - Shows mock count" \
    "bash .claude/hooks/user-prompt-submit.sh 'report please'" \
    "2454"

run_test "UserPromptSubmit - Shows reminders" \
    "bash .claude/hooks/user-prompt-submit.sh 'rapor'" \
    "DO NOT SAY"

# Test 2: tool-call.sh (PreToolUse)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST GROUP 2: PreToolUse Hook (tool-call.sh)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "PreToolUse - Detects report file write" \
    "bash .claude/hooks/tool-call.sh 'Write' '{\"file_path\":\"STATUS_REPORT.md\"}'" \
    "REPORT FILE WRITE DETECTED"

run_test "PreToolUse - Shows checklist" \
    "bash .claude/hooks/tool-call.sh 'Write' '{\"file_path\":\"SUMMARY.md\"}'" \
    "PRE-WRITE CHECKLIST"

run_test "PreToolUse - Ignores non-report files" \
    "bash .claude/hooks/tool-call.sh 'Write' '{\"file_path\":\"code.ts\"}'" \
    "^$"  # Should be empty output

# Test 3: post-tool-use.sh (PostToolUse wrapper)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST GROUP 3: PostToolUse Hook (post-tool-use.sh)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create a test report file first
TEST_REPORT="TEST_HOOKS_TEMP_REPORT.md"
cat > "$TEST_REPORT" << 'EOF'
# Test Report

Database has 0 rows.
Mock data: 2,454 occurrences.

Production readiness: 20%

## Evidence
```bash
py check_database.py
```
EOF

run_test "PostToolUse - Detects report file" \
    "bash .claude/hooks/post-tool-use.sh 'Write' '{\"file_path\":\"$TEST_REPORT\"}'" \
    "REPORT FILE WRITTEN"

run_test "PostToolUse - Runs verification" \
    "bash .claude/hooks/post-tool-use.sh 'Write' '{\"file_path\":\"$TEST_REPORT\"}'" \
    "Running automatic verification"

run_test "PostToolUse - Calculates score" \
    "bash .claude/hooks/post-tool-use.sh 'Write' '{\"file_path\":\"$TEST_REPORT\"}'" \
    "VERIFICATION SCORE"

# Test 4: pre-report-write.sh
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST GROUP 4: pre-report-write.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "pre-report-write - Runs database check" \
    "bash .claude/hooks/pre-report-write.sh 2>&1 | head -20" \
    "Checking Database"

run_test "pre-report-write - Runs mock check" \
    "bash .claude/hooks/pre-report-write.sh 2>&1 | head -30" \
    "Checking Mock Data"

run_test "pre-report-write - Creates facts file" \
    "bash .claude/hooks/pre-report-write.sh > /dev/null 2>&1 && ls .claude/facts/facts_*.json | wc -l" \
    "[1-9]"

run_test "pre-report-write - Stale detection (if old facts exist)" \
    "bash .claude/hooks/pre-report-write.sh 2>&1 | head -20" \
    "PRE-REPORT VERIFICATION"

# Test 5: post-report-write.sh
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST GROUP 5: post-report-write.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "post-report-write - Checks forbidden phrases" \
    "bash .claude/hooks/post-report-write.sh $TEST_REPORT 2>&1" \
    "Checking for Forbidden Phrases"

run_test "post-report-write - Checks evidence" \
    "bash .claude/hooks/post-report-write.sh $TEST_REPORT 2>&1" \
    "Checking for Evidence"

run_test "post-report-write - Compares with facts" \
    "bash .claude/hooks/post-report-write.sh $TEST_REPORT 2>&1" \
    "Comparing Claims with Facts"

run_test "post-report-write - Calculates verification score" \
    "bash .claude/hooks/post-report-write.sh $TEST_REPORT 2>&1" \
    "VERIFICATION SCORE"

# Test 6: File permissions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST GROUP 6: File Permissions & Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "Permissions - user-prompt-submit.sh executable" \
    "test -x .claude/hooks/user-prompt-submit.sh && echo 'executable'" \
    "executable"

run_test "Permissions - tool-call.sh executable" \
    "test -x .claude/hooks/tool-call.sh && echo 'executable'" \
    "executable"

run_test "Permissions - post-tool-use.sh executable" \
    "test -x .claude/hooks/post-tool-use.sh && echo 'executable'" \
    "executable"

run_test "Configuration - settings.json is valid JSON" \
    "python -m json.tool .claude/settings.local.json > /dev/null 2>&1 && echo 'valid'" \
    "valid"

run_test "Configuration - PostToolUse hook configured" \
    "grep -q 'PostToolUse' .claude/settings.local.json && echo 'configured'" \
    "configured"

# Cleanup
rm -f "$TEST_REPORT"

# Print results
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TEST RESULTS SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS ✅"
echo "Failed: $FAILED_TESTS ❌"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo ""
    RESULT="SUCCESS"
    EXIT_CODE=0
else
    echo "⚠️  SOME TESTS FAILED"
    echo ""
    echo "Failed Tests:"
    for result in "${TEST_RESULTS[@]}"; do
        if echo "$result" | grep -q "❌"; then
            echo "  $result"
        fi
    done
    echo ""
    RESULT="FAILURE"
    EXIT_CODE=1
fi

# Calculate pass rate
PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo "Pass Rate: $PASS_RATE%"
echo ""

# Print all test results
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DETAILED RESULTS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for result in "${TEST_RESULTS[@]}"; do
    echo "$result"
done
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save results to file
RESULTS_FILE=".claude/hooks/test_results_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "Hook System Test Results"
    echo "Date: $(date)"
    echo "Total: $TOTAL_TESTS | Passed: $PASSED_TESTS | Failed: $FAILED_TESTS"
    echo "Pass Rate: $PASS_RATE%"
    echo "Result: $RESULT"
    echo ""
    echo "Tests:"
    for result in "${TEST_RESULTS[@]}"; do
        echo "$result"
    done
} > "$RESULTS_FILE"

echo "📄 Results saved to: $RESULTS_FILE"
echo ""

exit $EXIT_CODE
