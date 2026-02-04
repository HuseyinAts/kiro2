# Claude Code AI - Project Instructions

## 🎯 Mission
Türkiye Üniversite Sınavları Hazırlık Platformu - Honest, Verified, Production-Quality Code and Documentation

---

## 🚨 CRITICAL: REPORTING GUIDELINES - MANDATORY

### Before Writing ANY Report (*.md, *_REPORT.md, *_SUMMARY.md)

**YOU MUST VERIFY EVERY CLAIM WITH EVIDENCE.**

#### Rule 1: Database Claims
```bash
# ALWAYS run these commands BEFORE claiming database status:
python .claude/scripts/check_database.py
sqlite3 backend/kiro2.db "SELECT name FROM sqlite_master WHERE type='table';"
sqlite3 backend/turkiye_sinav.db "SELECT COUNT(*) FROM sorular;" 2>/dev/null || echo "Table doesn't exist"
```

**Report ACTUAL counts, not planned/hoped:**
- ❌ WRONG: "Database with 10,000 sorular ready"
- ✅ RIGHT: "Database structure defined (migrations), currently 23 rows in sorular table"

#### Rule 2: API Endpoint Claims
```bash
# ALWAYS test endpoints BEFORE claiming they work:
curl -X GET http://localhost:8001/health
curl -X GET http://localhost:8001/api/v1/soru-bankasi/rastgele?count=2
```

**Only claim "working" if returns 200 OK:**
- ❌ WRONG: "API endpoints fully functional"
- ✅ RIGHT: "API endpoints defined and registered. Health check: ✓ Working. Sorular endpoint: ⚠️ 405 Method Not Allowed (needs investigation)"

#### Rule 3: Mock Data Detection
```bash
# ALWAYS check for mock/hardcoded data:
grep -r "mock\|TODO\|FIXME\|hardcoded\|placeholder" backend/services/*.py | wc -l
grep -r "Mock\|FAKE\|TODO" frontend/src/pages/*.tsx | wc -l
```

**Report mock occurrences explicitly:**
- ❌ WRONG: "Dashboard service complete"
- ✅ RIGHT: "Dashboard service implemented. WARNING: 12 mock data occurrences found in student_dashboard_service.py. Real database integration pending."

#### Rule 4: Production Readiness Scale

**Use OBJECTIVE scale, not wishful thinking:**

| Score | Criteria | Example |
|-------|----------|---------|
| 0-20% | Early prototype, mostly mock data | Current state (database empty, services mock) |
| 21-40% | Core features coded, needs real data | Migration files ready, awaiting execution |
| 41-60% | Feature-complete, integration pending | All endpoints defined, testing incomplete |
| 61-80% | Integrated, tested, minor bugs | E2E tests passing, small fixes needed |
| 81-95% | Production-ready, polish needed | Live beta with <10 users, no critical bugs |
| 96-100% | Battle-tested in production | 100+ active users, uptime >99% |

**NEVER claim >80% unless you have real user data and uptime metrics.**

#### Rule 5: Forbidden Phrases (Unless Verified)

**YOU MAY NOT USE these phrases without evidence:**

- ❌ "Production-ready" → Requires: Live deployment + Real users + Uptime data
- ❌ "100% complete" → Requires: All tests passing + No TODOs + Code review
- ❌ "All tests passing" → Requires: Actual test output, coverage report
- ❌ "Fully functional" → Requires: Manual testing + No errors + Real data
- ❌ "10,000+ sorular" → Requires: `SELECT COUNT(*)` output showing >=10,000
- ❌ "World-class" / "Revolutionary" → Subjective, avoid unless quoting external review

#### Rule 6: Required Evidence Format

**EVERY claim needs:**

```markdown
### Claim: [Your claim]

**Evidence:**
```bash
$ [command you ran]
[actual output]
```

**Assessment:**
- ✓ Verified
- ⚠️ Partial (explain)
- ❌ Unverified (explain)

**Files:**
- `path/to/file.py` (lines 123-456)
```

---

## 📋 REPORTING STANDARDS

### Report Structure Template

```markdown
# [Feature Name] - Status Report

**Date:** YYYY-MM-DD
**Verification Status:** ❌ Not Verified | ⚠️ Partially Verified | ✓ Fully Verified

---

## Executive Summary (Max 5 sentences)
[What was done, what works, what doesn't]

---

## Verified Claims

### Claim 1: [Specific claim]
[Use evidence format above]

### Claim 2: [Next claim]
[Repeat]

---

## Known Issues

### Issue #1: [Title]
**Severity:** Critical | High | Medium | Low
**Evidence:** [Error logs, screenshots]
**Status:** Open | In Progress | Fixed

---

## Quantitative Metrics

| Metric | Before | After | Change | Evidence |
|--------|--------|-------|--------|----------|
| Database rows | 3 | 23 | +20 | `check_database.py` |
| Mock occurrences | 180 | 150 | -30 | `grep -r "mock"` |
| Test coverage | 75% | 78% | +3% | `coverage.json` |

---

## Manual Testing Checklist

- [ ] Database accessible, tables exist
- [ ] API endpoints return 200 OK (not 405/500)
- [ ] Frontend displays real data (not mock)
- [ ] No console errors
- [ ] Performance acceptable (<2s load time)

**Screenshots/Logs:**
[Attach evidence]

---

## Deployment Readiness

**Current Phase:** Prototype | Development | Testing | Staging | Production

**Objective Assessment:**
- Infrastructure: [0-100]% - [Justification]
- Features: [0-100]% - [Justification]
- Testing: [0-100]% - [Justification]
- Documentation: [0-100]% - [Justification]

**OVERALL: [0-100]%**

**Critical Gaps:**
1. [Specific gap]
2. [Specific gap]

---

## Self-Audit

**Did you:**
- [ ] Run all verification commands?
- [ ] Test manually (not just read code)?
- [ ] Report actual numbers (not goals)?
- [ ] Include evidence for every claim?
- [ ] Acknowledge ALL known issues?
- [ ] Use objective readiness scale?

If any checkbox is unchecked, **DO NOT PUBLISH THIS REPORT.**

---

**Verification Signature:**
- Manual testing: [Yes/No]
- Automated checks: [Yes/No]
- Peer review: [Yes/No]
- Last verified: YYYY-MM-DD HH:MM
```

---

## 🔍 DETECTION PATTERNS (Red Flags)

### When Writing Reports, AVOID:

**Inflation Language:**
- "Revolutionary", "World-class", "Perfect", "Flawless"
- "100%", "All", "Every", "Complete" (without proof)
- "10,000+", "Millions", "Unlimited" (unless counted)

**Future-as-Present:**
- "We built..." → Should be "We are building..." (if incomplete)
- "Platform is ready" → Should be "Platform will be ready when..." (if not deployed)
- "10,000 sorular available" → Should be "10,000 sorular target" (if only 23 exist)

**Unverified Technical Claims:**
- "Migration files created" (Did you run them? Are tables populated?)
- "API endpoints defined" (Did you test them? Do they return 200?)
- "Database exists" (Is it empty or populated?)

---

## ✅ GOOD EXAMPLES

### Example 1: Honest Database Report
```markdown
### Database Status

**Claim:** "Database structure defined, minimal test data"

**Evidence:**
```bash
$ python .claude/scripts/check_database.py
[OK] turkiye_sinav.db exists (124 KB)
[OK] sorular table EXISTS
[OK] Current row count: 23
```

**Assessment:** ✓ Verified

**Interpretation:**
- Migration files executed successfully ✓
- Schema created ✓
- Contains 23 rows (not 10,000 as originally planned) ⚠️
- Production needs: Additional 9,977 sorular
```

### Example 2: API Status with Issues
```markdown
### API Health Status

**Claim:** "API partially functional, 1 endpoint failing"

**Evidence:**
```bash
$ curl http://localhost:8001/health
{"status": "healthy"} ✓

$ curl http://localhost:8001/api/v1/soru-bankasi/rastgele?count=2
405 Method Not Allowed ❌
```

**Assessment:** ⚠️ Partial - Health endpoint works, sorular endpoint broken

**Issue:** Route registration problem (investigating)
```

### Example 3: Mock Data Acknowledgment
```markdown
### Dashboard Service Status

**Claim:** "Dashboard service implemented with mock data"

**Evidence:**
```bash
$ grep -n "Mock\|hardcoded" backend/services/student_dashboard_service.py
23: # Mock veri - gerçek implementasyonda database kullanılacak
37: return DashboardIstatistikleri(tamamlanan_dersler=45, ...)  # HARDCODED
```

**Assessment:** ⚠️ Functional but not production-ready

**Production Readiness:** 30%
- Code structure: ✓ Complete
- Database integration: ❌ Pending
- Real data: ❌ Using mocks
- **Next step:** Replace mock returns with actual DB queries
```

---

## 🚫 BAD EXAMPLES (DO NOT COPY)

### ❌ Example 1: Unverified Overstatement
```markdown
### Database Status
"Database fully operational with 10,000+ sorular ready for production!" ❌

WHY BAD:
- No command output shown
- "10,000+" not verified
- "production ready" not tested
```

### ❌ Example 2: Technical Existence ≠ Functional
```markdown
### API Status
"All API endpoints implemented and working!" ❌

WHY BAD:
- Didn't test endpoints
- "Working" unverified
- Could be 405/500 errors
```

### ❌ Example 3: Hiding Mock Data
```markdown
### Dashboard Status
"Dashboard service complete, delivering real-time student statistics!" ❌

WHY BAD:
- Service uses hardcoded mock data
- Not "real-time"
- Not "complete" (no DB integration)
```

---

## 🤖 AI SELF-AWARENESS

**Remember:**
- You are Claude Code AI
- You have written previous reports that were INACCURATE
- Users trust you, but VERIFICATION is mandatory
- "Trust, but verify" - ALWAYS verify your own claims

**Before hitting "Save" on any report, ask yourself:**
1. Did I run the verification commands?
2. Did I see the actual output?
3. Am I reporting what EXISTS, not what's PLANNED?
4. Would a technical auditor agree with my percentages?
5. Am I being honest about limitations?

**If answer to ANY question is "No", DO NOT SAVE THE REPORT.**

---

## 📊 SELF-AUDIT CHECKLIST

Run this before finalizing reports:
```bash
# Count unverified claims:
grep -i "production-ready\|100%\|fully functional\|all.*working" YOUR_REPORT.md

# If any matches found, verify each claim or remove it.
```

---

## 🎯 PROJECT-SPECIFIC CONTEXT

### Current Reality (as of 2025-11-09)

**Database:**
- Structure: ✓ Defined (27+ migrations)
- Population: ⚠️ turkiye_sinav.db has 23 rows, kiro2.db empty
- Target: 10,000 sorular (9,977 gap)

**Backend:**
- APIs: ✓ 50+ endpoints registered
- Mock data: ⚠️ 150+ occurrences
- Production-ready: ~20-30%

**Frontend:**
- Pages: ✓ 44 pages created
- Mock data: ⚠️ Some components use hardcoded stats
- Integration: Partial

**Honest Assessment:** Early-stage prototype with strong architecture, needs data and integration work.

---

## 💡 WHEN IN DOUBT

**If unsure about a claim:**
1. Run the verification command
2. If it fails, report the failure honestly
3. If you can't verify, say "Unverified" or "To be tested"
4. NEVER guess or assume

**Better to say "I don't know" than to lie.**

---

## 🔄 UPDATE HISTORY

- 2025-11-09: Initial version - Response to inaccurate reporting incident
- Purpose: Prevent future misleading reports through mandatory verification

---

**This is your operating manual. Follow it strictly. Users deserve truth.**
