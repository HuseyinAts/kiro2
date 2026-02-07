# CLAUDE.md Emergency Stop Runbook

> **Version:** 1.0.0
> **Son Guncelleme:** 2026-01-19
> **Critical:** Yes - Use only in emergencies

## 1. When to Use Emergency Stop

### 1.1 Criteria for Emergency Stop

Use emergency stop when ANY of these occur:

- **Critical system failure:** Service completely unresponsive
- **Security incident:** Suspected malicious rule injection
- **Cascading failures:** Repeated auto-rollbacks not resolving
- **Data integrity issue:** Suspected corruption in feedback data
- **Production impact:** Direct impact on user-facing systems

### 1.2 Do NOT Use For

- Regular performance issues (use monitoring first)
- Single rule underperforming (use rule evolution)
- A/B test issues (cancel the specific test)
- Slow pattern detection (tune parameters)

## 2. Emergency Stop Procedure

### 2.1 API Method (Preferred)

```bash
# Trigger emergency stop via API
curl -X POST http://localhost:8000/api/claude-md-improvement/emergency-stop \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Describe the emergency",
    "operator": "your-name"
  }'
```

**Expected Response:**
```json
{
  "status": "stopped",
  "stopped_at": "2026-01-19T12:00:00Z",
  "reason": "Describe the emergency",
  "operator": "your-name",
  "services_halted": [
    "feedback_collection",
    "pattern_detection",
    "rule_evolution",
    "ab_testing",
    "doc_updater"
  ]
}
```

### 2.2 Manual Method (If API Unavailable)

```bash
# 1. Stop the Celery workers
systemctl stop celery-claude-md-improvement

# 2. Set emergency flag in Redis
redis-cli SET claude_md_emergency_stop "true" EX 86400

# 3. Notify via webhook (if configured)
curl -X POST $SLACK_WEBHOOK \
  -H "Content-Type: application/json" \
  -d '{"text": "EMERGENCY STOP: CLAUDE.md improvement halted"}'
```

### 2.3 Docker/Kubernetes Method

```bash
# Docker Compose
docker-compose stop claude-md-improvement

# Kubernetes
kubectl scale deployment claude-md-improvement --replicas=0

# Verify stopped
kubectl get pods -l app=claude-md-improvement
```

## 3. Notification Checklist

After activating emergency stop:

- [ ] Alert sent to #claude-md-improvement-alerts Slack channel
- [ ] PagerDuty incident created
- [ ] Tech Lead notified
- [ ] VP Engineering notified (if major incident)
- [ ] Status page updated (if user-facing impact)

### 3.1 Slack Template

```
EMERGENCY STOP ACTIVATED

Time: [timestamp]
Operator: [your-name]
Reason: [describe emergency]

Services Halted:
- Feedback collection
- Pattern detection
- Rule evolution
- A/B testing
- Doc updater

Next Steps: See runbook CLAUDE_MD_EMERGENCY_STOP.md
```

## 4. Investigation Steps

### 4.1 Initial Assessment

1. **Check service logs:**
```bash
# Recent errors
journalctl -u claude-md-improvement --since "1 hour ago" | grep ERROR

# Or Loki
{app="claude-md-improvement"} |= "error" | json
```

2. **Check database connectivity:**
```bash
# PostgreSQL
psql -h localhost -p 5434 -U kiro2 -c "SELECT 1"

# Redis
redis-cli PING
```

3. **Check external dependencies:**
   - MCP servers (chromadb, zemberek)
   - Git repository access
   - Network connectivity

### 4.2 Data Integrity Check

```sql
-- Check for corrupted feedback records
SELECT COUNT(*) as invalid_records
FROM claude_md_feedback_records
WHERE outcome IS NULL
   OR rule_id IS NULL
   OR created_at IS NULL;

-- Check for orphaned triggers
SELECT COUNT(*) as orphaned
FROM claude_md_improvement_triggers
WHERE rule_id NOT IN (SELECT rule_id FROM claude_md_rule_effectiveness);
```

### 4.3 Security Investigation

If security incident suspected:

1. **Audit recent changes:**
```sql
SELECT * FROM claude_md_audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

2. **Check for unauthorized access:**
```bash
# Review access logs
grep "claude-md-improvement" /var/log/nginx/access.log | tail -100
```

3. **Contact security team** if malicious activity confirmed

## 5. Manual Restart Procedure

### 5.1 Prerequisites for Restart

Before restarting, verify:

- [ ] Root cause identified
- [ ] Fix implemented (if applicable)
- [ ] Data integrity confirmed
- [ ] Services healthy
- [ ] Team notified

### 5.2 Restart Steps

```bash
# 1. Clear emergency flag
redis-cli DEL claude_md_emergency_stop

# 2. Restart services via API
curl -X POST http://localhost:8000/api/claude-md-improvement/restart \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operator": "your-name",
    "reason": "Emergency resolved: [description]"
  }'

# 3. Verify health
curl http://localhost:8000/api/claude-md-improvement/health
```

**Expected Health Response:**
```json
{
  "status": "healthy",
  "components": {
    "feedback_collection": "running",
    "pattern_detection": "running",
    "rule_evolution": "running",
    "ab_testing": "running",
    "doc_updater": "running"
  },
  "last_restart": "2026-01-19T13:00:00Z"
}
```

### 5.3 Verification Checklist

After restart:

- [ ] Health endpoint returns "healthy"
- [ ] Celery workers running
- [ ] Scheduled tasks executing
- [ ] Metrics being collected
- [ ] No new alerts triggered
- [ ] Monitor for 30 minutes

### 5.4 Docker/Kubernetes Restart

```bash
# Docker Compose
docker-compose up -d claude-md-improvement

# Kubernetes
kubectl scale deployment claude-md-improvement --replicas=2
kubectl rollout status deployment/claude-md-improvement
```

## 6. Post-Emergency

### 6.1 Incident Documentation

Create incident report within 24 hours:

```markdown
## Emergency Stop Incident Report

**Date:** YYYY-MM-DD HH:MM
**Duration:** X hours Y minutes
**Operator:** [name]

### Trigger
[What caused the emergency stop]

### Impact
- Services halted for X minutes
- Y feedback records not collected
- Z tasks affected

### Root Cause
[Detailed analysis]

### Resolution
[Steps taken to resolve]

### Prevention
[Actions to prevent recurrence]
```

### 6.2 Follow-up Actions

- [ ] Complete incident report
- [ ] Update runbooks if needed
- [ ] Review monitoring thresholds
- [ ] Schedule post-mortem (if major)
- [ ] Update safety policies if needed

## 7. Quick Reference

### Emergency Stop Command
```bash
curl -X POST http://localhost:8000/api/claude-md-improvement/emergency-stop \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "...", "operator": "..."}'
```

### Restart Command
```bash
curl -X POST http://localhost:8000/api/claude-md-improvement/restart \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"operator": "...", "reason": "..."}'
```

### Key Contacts
- **On-Call:** PagerDuty
- **Slack:** #claude-md-improvement-alerts
- **Tech Lead:** @tech-lead
