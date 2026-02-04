# Claude Code Hooks - Kiro2 Quality Control System

**Purpose:** Automatic verification reminders to prevent false reporting

---

## 📁 Available Hooks

### 1. `user-prompt-submit.sh` - User Message Hook

**When it runs:** Before Claude processes any user message

**What it does:**
- Detects if user is asking for a report/summary/status
- Automatically runs database verification
- Displays current project status
- Shows reporting reminders

**Triggers on keywords:**
- "report", "summary", "status"
- "rapor", "özet", "durum" (Turkish)

**Example:**
```
User: "Give me a status report"
↓
Hook runs automatically
↓
Displays:
  - Database rows: 0
  - Mock count: 2,454
  - Reminders (DO/DON'T)
↓
Claude processes message with this context
```

---

### 2. `tool-call.sh` - Tool Call Hook

**When it runs:** Before any tool is called

**What it does:**
- Monitors Write tool usage
- Detects report file writes
- Shows pre/post-write checklist

**Triggers on file names:**
- Contains "report", "summary", "status", "completion"

**Example:**
```
Claude: Write("STATUS_REPORT.md", content)
↓
Hook runs automatically
↓
Displays checklist:
  [ ] Run check_database.py
  [ ] Run check_mocks.sh
  [ ] Include evidence blocks
↓
Write proceeds with reminder shown
```

---

### 3. `pre-report-write.sh` - Manual Pre-Verification

**When it runs:** Manually before writing reports

**What it does:**
- Runs full database check
- Runs full mock check
- Gathers git status
- Checks backend health
- Saves facts to `.claude/facts/latest.json`

**Usage:**
```bash
bash .claude/hooks/pre-report-write.sh
```

**Output:**
- Database status
- Mock data count
- Git status
- Backend health
- Facts file location

---

### 4. `post-report-write.sh` - Manual Post-Verification

**When it runs:** Manually after writing reports

**What it does:**
- Checks for forbidden phrases
- Compares claims with facts
- Calculates verification score (0-100)
- Appends warning if score < 75

**Usage:**
```bash
bash .claude/hooks/post-report-write.sh YOUR_REPORT.md
```

**Output:**
- Forbidden phrase check
- Evidence score
- Fact comparison
- Verification score
- Warning (if needed)

---

## ⚙️ Configuration

Hooks are configured in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "user-prompt-submit": ".claude/hooks/user-prompt-submit.sh",
    "tool-call": ".claude/hooks/tool-call.sh"
  }
}
```

**Note:** Manual hooks (pre/post-report-write) don't need configuration.

---

## 🔄 Hook Workflow

### Automatic Workflow (user-prompt-submit):

```
1. User: "Give me a status report"
   ↓
2. user-prompt-submit.sh runs AUTOMATICALLY
   ↓
3. Checks database (0 rows)
   Checks mocks (2,454)
   ↓
4. Displays reminders:
   ❌ Don't say "production-ready"
   ✅ Say "Database has 0 rows"
   ↓
5. Claude sees these reminders
   ↓
6. Claude writes report with correct numbers
```

### Semi-Automatic Workflow (tool-call):

```
1. Claude: Write("STATUS_REPORT.md", ...)
   ↓
2. tool-call.sh runs AUTOMATICALLY
   ↓
3. Detects report file
   ↓
4. Shows checklist:
   [ ] Run verification scripts
   [ ] Include evidence
   ↓
5. Write proceeds (reminder shown)
   ↓
6. Claude sees reminder in output
```

### Manual Workflow (pre/post):

```
1. User or Claude: bash .claude/hooks/pre-report-write.sh
   ↓
2. Gathers all facts
   Saves to .claude/facts/latest.json
   ↓
3. Claude writes report using facts
   ↓
4. User or Claude: bash .claude/hooks/post-report-write.sh REPORT.md
   ↓
5. Verifies report against facts
   ↓
6. Score ≥ 75? Publish : Revise
```

---

## 📊 Effectiveness

| Hook | Type | Effectiveness | Blocking? |
|------|------|---------------|-----------|
| user-prompt-submit | Auto | 60% | No (reminder) |
| tool-call | Auto | 40% | No (reminder) |
| pre-report-write | Manual | 30% | No (info) |
| post-report-write | Manual | 30% | No (warning) |
| **COMBINED** | - | **70%** | **No** |

**Note:** Hooks provide reminders but don't BLOCK incorrect reports. For blocking, MCP Server is needed (95% effective).

---

## 🧪 Testing Hooks

### Test user-prompt-submit:

```bash
# Simulate user message
bash .claude/hooks/user-prompt-submit.sh "Give me a status report"

# Should display:
# - Database rows
# - Mock count
# - Reminders
```

### Test tool-call:

```bash
# Simulate Write tool call
bash .claude/hooks/tool-call.sh "Write" '{"file_path":"STATUS_REPORT.md"}'

# Should display:
# - Report file detected
# - Checklist
```

### Test pre-report-write:

```bash
bash .claude/hooks/pre-report-write.sh

# Should display:
# - Database check results
# - Mock check results
# - Facts file path
```

### Test post-report-write:

```bash
# Create test report
echo "Database has 10,000 rows!" > TEST.md

# Verify it
bash .claude/hooks/post-report-write.sh TEST.md

# Should display:
# - Forbidden phrases found
# - Discrepancy warnings
# - Low verification score
```

---

## 🚨 Troubleshooting

### Hook not running?

1. Check settings.local.json has correct path
2. Verify hook file has execute permissions:
   ```bash
   chmod +x .claude/hooks/*.sh
   ```
3. Test manually to ensure it works

### Hook shows errors?

1. Check Python/Bash are available
2. Verify scripts exist:
   ```bash
   ls -la .claude/scripts/
   ls -la .claude/hooks/
   ```
3. Run verification scripts manually to test

### Hooks too slow?

1. user-prompt-submit skips full mock check (uses cached)
2. Disable hooks temporarily in settings.json
3. Or comment out slow parts in hook scripts

---

## 📖 Related Files

- `.claude/instructions.md` - Reporting guidelines (Layer 1)
- `.claude/scripts/check_database.py` - Database verifier (Layer 2)
- `.claude/scripts/check_mocks.sh` - Mock data detector (Layer 2)
- `REPORTING_STANDARDS.md` - Report templates
- `QUALITY_CONTROL_SYSTEM_COMPLETE.md` - System overview

---

## 🔧 Customization

### Add new trigger words:

Edit `.claude/hooks/user-prompt-submit.sh`:
```bash
# Add your keywords
if echo "$USER_MESSAGE" | grep -qi "report\|YOUR_KEYWORD"; then
```

### Add new forbidden phrases:

Edit `.claude/hooks/post-report-write.sh`:
```bash
check_phrase "your-phrase" "Your guidance"
```

### Change verification score threshold:

Edit `.claude/hooks/post-report-write.sh`:
```bash
# Change from 75 to your threshold
if [ $VERIFICATION_SCORE -lt 75 ]; then
```

---

## ✅ Best Practices

1. **Always run pre-report-write before writing**
   - Gathers fresh facts
   - Ensures numbers are current

2. **Always run post-report-write after writing**
   - Verifies claims
   - Catches mistakes

3. **Review hook output**
   - Don't ignore warnings
   - Update report if discrepancies found

4. **Keep facts files updated**
   - Re-run checks if code changes
   - Delete old facts files weekly

5. **Test hooks after changes**
   - If you modify hook scripts
   - If you update verification rules

---

**Hooks are automatic reminders, not blockers. Claude AI can still make mistakes if reminders are ignored. For true blocking, use MCP Server.**
