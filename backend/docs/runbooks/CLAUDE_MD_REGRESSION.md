# CLAUDE.md Regression Handling Runbook

> **Version:** 1.0.0
> **Son Guncelleme:** 2026-01-19
> **Critical:** Yes - Immediate response required

## 1. Regression Detection

### 1.1 Automatic Detection Criteria

A regression is automatically detected when:

- Task success rate drops > 5% compared to baseline
- Rule effectiveness drops > 10% in 24 hours
- Anomaly with Z-score > 3 persists for > 10 minutes

### 1.2 Manual Detection Signs

Watch for:
- Sudden spike in task failures
- User complaints about agent behavior
- Increased retry rates
- Longer task completion times

### 1.3 Alerts Indicating Regression

| Alert | Action |
|-------|--------|
| ClaudeMdRegressionDetected | Auto-rollback triggered |
| ClaudeMdTaskSuccessRateCritical | Investigate immediately |
| ClaudeMdRollbackTriggered | Verify rollback success |

## 2. Immediate Response

### 2.1 Auto-Rollback Verification

When `ClaudeMdRollbackTriggered` fires:

1. **Verify rollback completed:**
```bash
# Check rollback status
SELECT * FROM claude_md_rollback_events
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

2. **Confirm CLAUDE.md version:**
```bash
# Check current version
git log --oneline CLAUDE.md | head -5
```

3. **Verify metrics recovering:**
   - Open Grafana dashboard
   - Watch task success rate for improvement

### 2.2 Manual Rollback Steps

If auto-rollback failed or was not triggered:

```bash
# 1. Find the last known good version
git log --oneline CLAUDE.md

# 2. Rollback to specific version
git checkout <commit-hash> -- CLAUDE.md

# 3. Commit the rollback
git add CLAUDE.md
git commit -m "Manual rollback: regression detected"

# 4. Notify the system
curl -X POST http://localhost:8000/api/claude-md-improvement/manual-rollback \
  -H "Content-Type: application/json" \
  -d '{"reason": "Manual rollback due to regression", "commit": "<commit-hash>"}'
```

### 2.3 Time Target

**Rollback must complete in < 5 seconds** (REQ-8.4)

If rollback takes longer:
1. Check disk I/O
2. Check git repository health
3. Consider emergency stop

## 3. Root Cause Analysis

### 3.1 Investigation Checklist

- [ ] Identify the change that caused regression
- [ ] Review A/B test results if applicable
- [ ] Check pattern detection recommendations
- [ ] Review recent approval decisions
- [ ] Analyze affected rules

### 3.2 Finding the Problematic Change

```sql
-- Find recent rule changes before regression
SELECT
    rv.rule_id,
    rv.old_text,
    rv.new_text,
    rv.change_type,
    rv.created_at
FROM claude_md_rule_versions rv
WHERE rv.created_at > NOW() - INTERVAL '48 hours'
ORDER BY rv.created_at DESC;
```

### 3.3 Common Causes

| Cause | Indicator | Solution |
|-------|-----------|----------|
| Conflicting rules | Multiple rules with contradicting guidance | Conflict resolution |
| Over-specified rule | Rule too narrow for general use | Simplify rule |
| Under-specified rule | Rule too vague | Add specificity |
| A/B test false positive | p-value close to 0.05 | Require more samples |
| Edge case not covered | Failures in specific scenarios | Add examples |

### 3.4 Correlation Analysis

```sql
-- Correlate regression with rule changes
SELECT
    rv.rule_id,
    rv.created_at as change_time,
    re.effectiveness_score,
    re.updated_at as effectiveness_time
FROM claude_md_rule_versions rv
JOIN claude_md_rule_effectiveness re ON rv.rule_id = re.rule_id
WHERE rv.created_at BETWEEN NOW() - INTERVAL '48 hours' AND NOW()
ORDER BY rv.created_at;
```

## 4. Recovery Procedures

### 4.1 After Rollback

1. **Verify system stability:**
   - Monitor for 30 minutes
   - Check task success rate returning to baseline
   - Verify no new alerts

2. **Document the incident:**
   - Create incident report
   - Record timeline
   - Note root cause

3. **Update patterns:**
```bash
# Mark the problematic pattern
curl -X POST http://localhost:8000/api/claude-md-improvement/mark-anti-pattern \
  -H "Content-Type: application/json" \
  -d '{"rule_id": "<rule-id>", "reason": "Caused regression"}'
```

### 4.2 Version Restoration

```bash
# List available versions
git tag -l "claude-md-v*"

# Restore specific version
git checkout claude-md-v2.3.0 -- CLAUDE.md

# Create new version tag
git tag claude-md-v2.3.1
git push --tags
```

### 4.3 Service Restart (if needed)

```bash
# Restart the improvement service
systemctl restart claude-md-improvement

# Or in Docker
docker-compose restart claude-md-improvement

# Verify health
curl http://localhost:8000/api/claude-md-improvement/health
```

## 5. Post-Incident

### 5.1 Incident Report Template

```markdown
## Incident Report: CLAUDE.md Regression

**Date:** YYYY-MM-DD
**Duration:** HH:MM
**Severity:** [Critical/High/Medium]

### Timeline
- HH:MM - Regression detected
- HH:MM - Alert triggered
- HH:MM - Rollback initiated
- HH:MM - Service recovered

### Root Cause
[Description of what caused the regression]

### Impact
- Task success rate dropped from X% to Y%
- Z tasks affected

### Resolution
[Steps taken to resolve]

### Prevention
[Actions to prevent recurrence]
```

### 5.2 Follow-up Actions

- [ ] Update test coverage for the edge case
- [ ] Add pattern to anti-pattern detection
- [ ] Review A/B testing sample size requirements
- [ ] Update documentation if needed
- [ ] Schedule retrospective if major incident

## 6. Emergency Contacts

| Role | Contact | When |
|------|---------|------|
| Platform On-Call | PagerDuty | First response |
| Tech Lead | Slack @tech-lead | > 30 min incidents |
| VP Engineering | Phone | > 1 hour, major impact |
