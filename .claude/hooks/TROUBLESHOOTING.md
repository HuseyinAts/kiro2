# Hooks Troubleshooting Guide

**For:** Kiro2 Quality Control Hook System
**Updated:** 2025-11-09

---

## Quick Diagnosis

### Is the hook system working?

Run this quick test:
```bash
bash .claude/hooks/user-prompt-submit.sh "test report"
```

**Expected:** Should display database status and reminders
**If nothing happens:** See [Hook Not Running](#hook-not-running)
**If errors appear:** See [Common Errors](#common-errors)

---

## Common Issues

### 1. Hook Not Running

**Symptoms:**
- No output when you expect hook to trigger
- Settings.json configured but hooks don't fire
- Manual execution works but auto-trigger doesn't

**Diagnosis:**
```bash
# Check if hook file exists
ls -la .claude/hooks/user-prompt-submit.sh

# Check if executable
if [ -x .claude/hooks/user-prompt-submit.sh ]; then
    echo "✓ Executable"
else
    echo "✗ Not executable"
fi

# Check settings.json syntax
cat .claude/settings.local.json | python -m json.tool > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ JSON valid"
else
    echo "✗ JSON syntax error"
fi
```

**Solutions:**

**Solution 1.1: Make hooks executable**
```bash
chmod +x .claude/hooks/*.sh
```

**Solution 1.2: Fix JSON syntax**
```bash
# Validate JSON
python -m json.tool .claude/settings.local.json

# Look for:
# - Missing commas
# - Trailing commas in last array item
# - Unescaped quotes
# - Mismatched brackets
```

**Solution 1.3: Check hook path**
```bash
# Settings.json should have absolute or relative path
# CORRECT:
"command": "bash .claude/hooks/user-prompt-submit.sh \"$USER_MESSAGE\""

# WRONG:
"command": "bash hooks/user-prompt-submit.sh"  # Missing .claude/
```

**Solution 1.4: Restart Claude Code**
- Settings changes require Claude Code restart
- Close and reopen the workspace

---

### 2. Python Not Found

**Symptoms:**
```
⚠️  Python not found - skipping database check
```

**Diagnosis:**
```bash
# Check Python availability
which python
which py
python --version
py --version
```

**Solutions:**

**Solution 2.1: Install Python**
- Download from https://python.org
- Or use package manager: `winget install Python.Python.3.11`

**Solution 2.2: Add Python to PATH**
```bash
# Windows
set PATH=%PATH%;C:\Python311

# Linux/Mac
export PATH=$PATH:/usr/local/bin/python3
```

**Solution 2.3: Use fallback values**
- Hooks will use cached/default values if Python unavailable
- This is acceptable for quick checks
- For full verification, install Python

---

### 3. Facts File Missing

**Symptoms:**
```
⚠️  WARNING: No facts file found
Run pre-report-write.sh first to gather facts
```

**Diagnosis:**
```bash
ls -la .claude/facts/latest.json
```

**Solutions:**

**Solution 3.1: Run pre-report-write**
```bash
bash .claude/hooks/pre-report-write.sh
```
This creates fresh facts file and symlink.

**Solution 3.2: Check symlink**
```bash
# If symlink is broken:
cd .claude/facts
ls -la latest.json

# Fix it:
ln -sf facts_20251109_063745.json latest.json  # Use latest file
```

**Solution 3.3: Manually create facts directory**
```bash
mkdir -p .claude/facts
bash .claude/hooks/pre-report-write.sh
```

---

### 4. Stale Facts Warning

**Symptoms:**
```
⚠️  WARNING: Existing facts file is STALE
   Age: 120 minutes old
```

**This is NORMAL if:**
- You haven't run verification recently
- Database or code changed since last check

**Solutions:**

**Solution 4.1: Accept and continue**
- pre-report-write automatically gathers fresh facts
- Warning is informational only

**Solution 4.2: Suppress warning (not recommended)**
```bash
# Edit pre-report-write.sh line 32:
# Change: if [ $FACTS_AGE -gt 3600 ]; then
# To:     if [ $FACTS_AGE -gt 86400 ]; then  # 24 hours instead of 1 hour
```

---

### 5. Database Check Fails

**Symptoms:**
```
⚠️  Database check had warnings (exit code: 127)
```

**Diagnosis:**
```bash
# Run check manually
python .claude/scripts/check_database.py

# Or:
py .claude/scripts/check_database.py
```

**Solutions:**

**Solution 5.1: Exit code 127 - Command not found**
```bash
# Python not in PATH
which python
which py

# Add to PATH or use full path in script
```

**Solution 5.2: Exit code 1 - Database empty**
- This is EXPECTED if database not populated
- Not an error, just a warning
- Hooks will report "0 rows"

**Solution 5.3: ModuleNotFoundError**
```bash
# Install required modules
pip install sqlite3  # Usually built-in
pip install json     # Usually built-in
```

---

### 6. Mock Check Slow

**Symptoms:**
- check_mocks.sh takes 30+ seconds
- user-prompt-submit hangs

**This is NORMAL:**
- check_mocks scans entire codebase
- 2,454 files to check

**Solutions:**

**Solution 6.1: Use cached value (current behavior)**
- user-prompt-submit skips full scan
- Uses last known count from mock_facts.json
- This is intentional to avoid blocking

**Solution 6.2: Run manually if needed**
```bash
# When you need fresh mock count:
bash .claude/scripts/check_mocks.sh

# Then user-prompt-submit will use updated value
```

**Solution 6.3: Optimize check_mocks (advanced)**
```bash
# Exclude more directories
# Edit check_mocks.sh, add to EXCLUDE_PATTERNS:
--exclude-dir=".git" \
--exclude-dir="node_modules" \
--exclude-dir="__pycache__" \
--exclude-dir=".venv" \
--exclude-dir="dist" \
--exclude-dir="build"
```

---

### 7. Verification Score Always Low

**Symptoms:**
```
📊 VERIFICATION SCORE: 25/100
```

**This is EXPECTED if:**
- Report lacks evidence blocks
- Report uses forbidden phrases
- Report doesn't mention database/mocks
- Report claims don't match facts

**Solutions:**

**Solution 7.1: Add evidence blocks**
```markdown
## Evidence

\`\`\`bash
# Run actual commands
py .claude/scripts/check_database.py
\`\`\`

Output:
\`\`\`
Total rows: 0
\`\`\`
```
**Score increase:** +25 points

**Solution 7.2: Remove forbidden phrases**
```
❌ "production-ready" → ✅ "production readiness: 20%"
❌ "100% complete" → ✅ "Phase 1 complete (20%)"
❌ "fully functional" → ✅ "Core features implemented"
```
**Score increase:** +25 points

**Solution 7.3: Include database facts**
```markdown
## Database Status

Current state:
- Total rows: 0 (verified via check_database.py)
- Total tables: 5 (structure defined)
```
**Score increase:** +25 points

**Solution 7.4: Mention issues/gaps**
```markdown
## Known Issues

- Database structure defined but not populated (0 rows)
- 2,454 mock data occurrences in codebase
- Backend not running (cannot verify API)
```
**Score increase:** +25 points

**Target:** 75+ points for passing score

---

### 8. PostToolUse Hook Not Triggering

**Symptoms:**
- Write report but no automatic verification
- No "AUTOMATED VERIFICATION" section appended

**Diagnosis:**
```bash
# Check if hook configured
grep -A 10 "PostToolUse" .claude/settings.local.json

# Should see:
# "PostToolUse": [
#   {
#     "matcher": "Write",
#     "hooks": [...]
#   }
# ]
```

**Solutions:**

**Solution 8.1: Add PostToolUse to settings**
See `.claude/settings.local.json` lines 70-80 for correct format.

**Solution 8.2: Restart Claude Code**
- Close workspace
- Reopen workspace
- Hooks reload from settings

**Solution 8.3: Test manually**
```bash
# Simulate PostToolUse
bash .claude/hooks/post-tool-use.sh "Write" '{"file_path":"TEST.md"}'
```

---

### 9. File Permission Denied

**Symptoms:**
```
bash: .claude/hooks/user-prompt-submit.sh: Permission denied
```

**Solutions:**

**Solution 9.1: Make executable**
```bash
chmod +x .claude/hooks/*.sh
```

**Solution 9.2: Run with bash explicitly**
```bash
# Instead of:
./claude/hooks/user-prompt-submit.sh

# Use:
bash .claude/hooks/user-prompt-submit.sh
```

**Solution 9.3: Check file ownership**
```bash
ls -la .claude/hooks/
# Should show your username, not root
# If root: sudo chown -R $USER:$USER .claude/
```

---

### 10. JSON Parsing Errors

**Symptoms:**
```
ValueError: Expecting value: line 1 column 1 (char 0)
```

**Diagnosis:**
```bash
# Validate facts JSON
python -m json.tool .claude/facts/latest.json

# Validate database facts
python -m json.tool .claude/scripts/database_facts.json

# Validate mock facts
python -m json.tool .claude/scripts/mock_facts.json
```

**Solutions:**

**Solution 10.1: Regenerate facts**
```bash
# Delete corrupt files
rm .claude/facts/latest.json
rm .claude/scripts/*.json

# Regenerate
bash .claude/hooks/pre-report-write.sh
```

**Solution 10.2: Check for truncated files**
```bash
# Files should end with }
tail -n 1 .claude/facts/latest.json
# Should show: }

# If not, file was truncated during write
# Regenerate as in Solution 10.1
```

---

## Advanced Troubleshooting

### Enable Debug Mode

Add to hook scripts (temporarily):
```bash
#!/bin/bash
set -x  # Enable debug output
set -e  # Exit on error (be careful with this)
```

Run hook and capture full output:
```bash
bash -x .claude/hooks/user-prompt-submit.sh "test" 2>&1 | tee debug.log
```

### Check Hook Execution Order

Hooks run in this order:
1. **UserPromptSubmit** - When user sends message
2. **PreToolUse** - Before Write tool executes
3. *Write tool executes*
4. **PostToolUse** - After Write tool completes

To verify:
```bash
# Add timestamp to each hook
echo "Hook started: $(date)" >> /tmp/hook-log.txt
```

### Test Individual Components

```bash
# Test database check
python .claude/scripts/check_database.py
echo $?  # Exit code: 0=success, 1=warnings

# Test mock check
bash .claude/scripts/check_mocks.sh
echo $?

# Test facts gathering
bash .claude/hooks/pre-report-write.sh
ls -la .claude/facts/

# Test report verification
bash .claude/hooks/post-report-write.sh TEST.md
```

---

## Performance Issues

### Hook Too Slow

**Symptoms:** Hooks take >10 seconds

**Solutions:**

1. **Skip slow checks in auto hooks**
   - user-prompt-submit already skips full mock scan
   - This is intentional

2. **Run full checks manually when needed**
   ```bash
   bash .claude/hooks/pre-report-write.sh  # Full check
   ```

3. **Optimize check_mocks.sh**
   - Add more exclude patterns
   - Use `--exclude-dir` for large directories

### Database Check Slow

Usually <1 second. If slow:

```bash
# Check database size
ls -lh backend/*.db

# Large DB? Optimize queries in check_database.py
# Add indexes or limit row counts
```

---

## Getting Help

### 1. Check Documentation
- [README.md](README.md) - Hook usage guide
- [END_TO_END_TEST_RESULTS.md](END_TO_END_TEST_RESULTS.md) - Test scenarios
- [HOOKS_INSTALLATION_COMPLETE.md](../../HOOKS_INSTALLATION_COMPLETE.md) - Installation guide

### 2. Verify Installation
```bash
# Run full system check
bash .claude/hooks/user-prompt-submit.sh "test"
bash .claude/hooks/pre-report-write.sh
bash .claude/hooks/post-report-write.sh TEST_POST_HOOK_REPORT.md
```

### 3. Check System Requirements
- Bash (Git Bash on Windows, native on Linux/Mac)
- Python 3.7+ (`python` or `py` command)
- Git (for project root detection)
- Write permissions in .claude/ directory

### 4. Reset to Working State
```bash
# Backup current state
cp .claude/settings.local.json .claude/settings.backup.json

# Reset hooks
chmod +x .claude/hooks/*.sh

# Regenerate facts
rm -f .claude/facts/*.json
bash .claude/hooks/pre-report-write.sh

# Test
bash .claude/hooks/user-prompt-submit.sh "test report"
```

---

## Reporting Bugs

If none of the above solutions work:

**Gather this information:**

1. **System Info:**
   ```bash
   uname -a
   python --version
   bash --version
   ```

2. **Hook Output:**
   ```bash
   bash -x .claude/hooks/user-prompt-submit.sh "test" 2>&1 > debug.log
   ```

3. **Settings:**
   ```bash
   cat .claude/settings.local.json | python -m json.tool
   ```

4. **File Permissions:**
   ```bash
   ls -laR .claude/
   ```

5. **Error Message:**
   - Full error text
   - Which hook failed
   - What command triggered it

**Then:**
- Check GitHub issues: https://github.com/anthropics/claude-code/issues
- Or document the issue for the development team

---

## Success Checklist

✅ All hooks executable (`chmod +x .claude/hooks/*.sh`)
✅ Settings.json has valid JSON syntax
✅ Python available in PATH
✅ Facts files generated (`.claude/facts/latest.json`)
✅ Manual test of each hook passes
✅ Verification score calculation works
✅ Error messages are clear and helpful

**If all checked:** System is working correctly!

---

## Appendix: Hook File Locations

```
kiro2/
└── .claude/
    ├── settings.local.json          # Hook configuration (CRITICAL)
    ├── instructions.md               # Reporting guidelines
    ├── hooks/
    │   ├── user-prompt-submit.sh    # Auto: detects report requests
    │   ├── tool-call.sh              # Auto: warns before write
    │   ├── post-tool-use.sh          # Auto: wrapper for post-report
    │   ├── post-report-write.sh      # Core: verifies report
    │   ├── pre-report-write.sh       # Manual: gathers facts
    │   ├── README.md                 # Usage guide
    │   ├── END_TO_END_TEST_RESULTS.md
    │   └── TROUBLESHOOTING.md       # This file
    ├── scripts/
    │   ├── check_database.py         # Database verification
    │   ├── check_mocks.sh            # Mock detection
    │   ├── database_facts.json       # Output
    │   └── mock_facts.json           # Output
    └── facts/
        ├── latest.json               # Symlink to current facts
        └── facts_YYYYMMDD_HHMMSS.json  # Historical facts
```

---

**Last Updated:** 2025-11-09
**System Version:** 1.0 (70% effective)
**Next Review:** After 1 week of real usage
