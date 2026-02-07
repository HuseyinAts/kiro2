# CLAUDE.md Self-Improvement Monitoring Runbook

> **Version:** 1.0.0
> **Son Guncelleme:** 2026-01-19
> **On-Call Team:** Platform Engineering

## 1. Dashboard Overview

### 1.1 Key Metrics to Monitor

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Task Success Rate | >= 75% | < 60% | < 40% |
| Rule Effectiveness (avg) | >= 80% | < 70% | < 50% |
| A/B Test Win Rate | >= 60% | < 50% | < 30% |
| Feedback Processing Time | < 1s | > 2s | > 5s |
| Pattern Detection Time | < 10s | > 15s | > 20s |

### 1.2 Grafana Dashboard Access

```
URL: https://grafana.kiro2.com/d/claude-md-improvement
User: Read-only access via SSO
```

### 1.3 Dashboard Panels

1. **Task Success Rate** (Time Series)
   - Shows success rate over time
   - Threshold lines at 60% and 40%

2. **Rule Effectiveness Distribution** (Bar Chart)
   - Per-rule effectiveness scores
   - Color-coded: Green (>0.8), Yellow (0.6-0.8), Red (<0.6)

3. **Pending Triggers** (Stat Panel)
   - Count of improvement triggers awaiting action

4. **A/B Test Status** (Table)
   - Active tests with sample counts and preliminary results

5. **Anomaly Events** (Alert List)
   - Recent anomalies detected (Z-score > 3)

## 2. Daily Checks

### 2.1 Morning Checklist (09:00 UTC)

- [ ] Check overnight pattern detection results
- [ ] Review any triggered alerts
- [ ] Verify hourly feedback collection ran
- [ ] Check pending approval requests

### 2.2 Feedback Collection Status

```bash
# Check last successful collection
SELECT MAX(collection_time)
FROM claude_md_feedback_collection_log
WHERE status = 'success';

# Check error rate
SELECT COUNT(*) as errors
FROM claude_md_feedback_collection_log
WHERE status = 'error'
AND collection_time > NOW() - INTERVAL '24 hours';
```

### 2.3 Pattern Detection Results

```bash
# View latest patterns
SELECT pattern_type, confidence, detected_at
FROM claude_md_pattern_detections
WHERE detected_at > NOW() - INTERVAL '24 hours'
ORDER BY detected_at DESC
LIMIT 10;
```

## 3. Weekly Reviews

### 3.1 A/B Test Results Review

Every Monday, review completed A/B tests:

1. Navigate to Grafana > A/B Test History
2. For each completed test:
   - Verify statistical significance (p < 0.05)
   - Confirm sample sizes (>= 1000 per variant)
   - Document decision (promote/reject)

### 3.2 Rule Effectiveness Trend

```sql
-- Weekly rule effectiveness trend
SELECT
    DATE_TRUNC('week', updated_at) as week,
    AVG(effectiveness_score) as avg_effectiveness,
    COUNT(DISTINCT rule_id) as rules_evaluated
FROM claude_md_rule_effectiveness
WHERE updated_at > NOW() - INTERVAL '4 weeks'
GROUP BY week
ORDER BY week;
```

### 3.3 Success Metrics Dashboard

Target vs Actual:

| Metric | Target | This Week | Trend |
|--------|--------|-----------|-------|
| Task Success Improvement | >= 25% | [value] | [trend] |
| Rule Effectiveness | >= 80% | [value] | [trend] |
| A/B Win Rate | >= 60% | [value] | [trend] |

## 4. Responding to Alerts

### 4.1 ClaudeMdTaskSuccessRateLow

**Severity:** Warning

**Immediate Actions:**
1. Check recent rule changes in git log
2. Review pattern detection recommendations
3. Check for correlated infrastructure issues

**Investigation:**
```bash
# Find rules with declining effectiveness
SELECT rule_id, effectiveness_score, updated_at
FROM claude_md_rule_effectiveness
WHERE effectiveness_score < 0.6
ORDER BY updated_at DESC;
```

### 4.2 ClaudeMdAnomalyDetected

**Severity:** Warning

**Immediate Actions:**
1. Check anomaly details in monitoring dashboard
2. Correlate with any recent deployments
3. Review affected metrics

**Investigation:**
```bash
# View anomaly details
SELECT metric, value, z_score, detected_at
FROM claude_md_anomaly_logs
WHERE detected_at > NOW() - INTERVAL '1 hour'
ORDER BY z_score DESC;
```

### 4.3 ClaudeMdLowEffectivenessRules

**Severity:** Warning

**Immediate Actions:**
1. List affected rules
2. Check if patterns are consistent
3. Consider triggering rule evolution

**Resolution:**
```bash
# Trigger evolution check manually
celery call tasks.claude_md_improvement.check_rule_evolution
```

## 5. Metrics Reference

### 5.1 Prometheus Metrics

| Metric Name | Type | Description |
|-------------|------|-------------|
| claude_md_task_outcomes_total | Counter | Task outcomes by type |
| claude_md_rule_effectiveness | Gauge | Per-rule effectiveness |
| claude_md_feedback_processing_seconds | Histogram | Feedback processing latency |
| claude_md_pattern_detection_duration_seconds | Gauge | Pattern detection duration |
| claude_md_anomaly_count | Gauge | Current anomaly count |
| claude_md_regression_count | Counter | Regression events |
| claude_md_rollback_triggered | Gauge | Rollback status (0/1) |

### 5.2 Log Queries

```bash
# Loki query for errors
{app="claude-md-improvement"} |= "error"

# Recent improvement triggers
{app="claude-md-improvement"} |= "improvement_trigger"
```

## 6. Escalation Path

| Level | Contact | When |
|-------|---------|------|
| L1 | Platform On-Call | All alerts |
| L2 | Platform Engineering | After 30min |
| L3 | Tech Lead | Critical alerts > 1h |

## 7. Contact Information

- **Slack Channel:** #claude-md-improvement-alerts
- **PagerDuty:** platform-engineering
- **Email:** platform@kiro2.com
