# CLAUDE.md Approval Workflow Runbook

> **Version:** 1.0.0
> **Son Guncelleme:** 2026-01-19
> **Owner:** Platform Engineering

## 1. Approval Types

### 1.1 Risk-Based Classification

| Risk Level | Score | Approval Type | Response Time |
|------------|-------|---------------|---------------|
| Low | <= 0.3 | Auto-approved | Immediate |
| Medium | 0.3-0.7 | Auto-approved (with log) | Immediate |
| High | > 0.7 | Manual approval required | 24 hours |
| Critical | Security flagged | Manual + Security review | 48 hours |

### 1.2 Changes Requiring Manual Approval

- Risk score > 0.7 (REQ-8.2)
- Contains risky patterns (delete, drop, rm -rf, eval, exec)
- Modifies security-related rules
- Major version bump (breaking changes)
- First rule from new category

## 2. Review Process

### 2.1 Accessing Pending Approvals

**Via API:**
```bash
curl http://localhost:8000/api/claude-md-improvement/triggers/pending \
  -H "Authorization: Bearer $TOKEN"
```

**Via Dashboard:**
1. Open Grafana > CLAUDE.md Improvement
2. Navigate to "Pending Approvals" panel
3. Click on individual items for details

### 2.2 Reviewer Assignment

Approvals are assigned based on:

| Category | Primary Reviewer | Backup |
|----------|------------------|--------|
| Rule text changes | Platform Engineer | Tech Lead |
| Security-related | Security Engineer | Tech Lead |
| Performance rules | Platform Engineer | SRE |
| A/B test promotion | Product Manager | Tech Lead |

### 2.3 Review Checklist

Before approving, verify:

- [ ] Change description is clear
- [ ] Risk assessment is accurate
- [ ] No security concerns
- [ ] Consistent with existing rules
- [ ] A/B test results support change (if applicable)
- [ ] No conflicting rules introduced

### 2.4 Decision Criteria

**Approve if:**
- Clear improvement in effectiveness expected
- Well-documented rationale
- A/B test showed significant improvement
- No security or safety concerns

**Reject if:**
- Unclear or missing rationale
- Conflicts with existing high-performing rules
- Security concern identified
- Insufficient A/B test data
- Violates platform guidelines

## 3. Approval Steps

### 3.1 Viewing Request Details

```bash
# Get specific trigger details
curl http://localhost:8000/api/claude-md-improvement/triggers/{trigger_id} \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "id": "trigger-123",
  "rule_id": "rule-456",
  "trigger_type": "a_b_test_complete",
  "proposed_change": {
    "old_text": "Always use async for database operations",
    "new_text": "Use async/await for all I/O-bound operations including database, file, and network calls"
  },
  "risk_level": "high",
  "risk_score": 0.75,
  "risk_factors": ["Broad scope change"],
  "suggested_actions": ["review", "approve", "reject"],
  "ab_test_results": {
    "winner": "treatment",
    "p_value": 0.023,
    "improvement": "12.5%"
  },
  "created_at": "2026-01-19T10:00:00Z",
  "status": "pending"
}
```

### 3.2 Approving a Change

```bash
curl -X POST http://localhost:8000/api/claude-md-improvement/triggers/{trigger_id}/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": "your-name",
    "comment": "Approved based on A/B test results showing 12.5% improvement",
    "conditions": []
  }'
```

**Approval with Conditions:**
```json
{
  "approved_by": "your-name",
  "comment": "Approved with modifications",
  "conditions": [
    "Add example for async file operations",
    "Limit scope to I/O operations only"
  ]
}
```

### 3.3 Rejecting a Change

```bash
curl -X POST http://localhost:8000/api/claude-md-improvement/triggers/{trigger_id}/reject \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rejected_by": "your-name",
    "reason": "Insufficient A/B test data - only 800 samples collected",
    "feedback": "Extend A/B test duration to collect 1000+ samples per variant"
  }'
```

### 3.4 Documentation Requirements

Every approval/rejection must include:

- **Approver name:** Who made the decision
- **Comment/Reason:** Why the decision was made
- **Timestamp:** Automatically recorded

## 4. Rejection Handling

### 4.1 Feedback to System

When rejecting, provide actionable feedback:

| Rejection Reason | Feedback Template |
|------------------|-------------------|
| Insufficient samples | "Extend A/B test to collect N more samples" |
| Conflicting rules | "Resolve conflict with rule-XYZ first" |
| Security concern | "Review with security team, flag: [issue]" |
| Unclear scope | "Clarify which scenarios this applies to" |

### 4.2 Re-submission Guidelines

After rejection, the system may:

1. Extend A/B test duration
2. Modify the proposed change
3. Add more context/examples
4. Resubmit for approval

Reviewers should check:
- Original feedback was addressed
- New evidence supports the change
- Risk factors are mitigated

## 5. SLA and Escalation

### 5.1 Response Time SLAs

| Risk Level | Initial Review | Final Decision |
|------------|----------------|----------------|
| High | 4 hours | 24 hours |
| Critical | 2 hours | 48 hours |

### 5.2 Escalation Path

If SLA breached:

1. **4 hours:** Notify backup reviewer
2. **8 hours:** Escalate to Tech Lead
3. **24 hours:** Auto-expire (requires re-trigger)

### 5.3 Out-of-Hours Approvals

- Critical changes: PagerDuty on-call
- High changes: Next business day
- Can be expedited via explicit request

## 6. Audit and Compliance

### 6.1 Audit Trail

All approvals are logged:

```sql
SELECT
    al.action,
    al.performed_by,
    al.reason,
    al.created_at
FROM claude_md_audit_logs al
WHERE al.entity_type = 'approval'
ORDER BY al.created_at DESC;
```

### 6.2 Compliance Requirements

- All high-risk changes require human approval
- Audit logs retained for 1 year
- Reviewers must have appropriate role
- No self-approval allowed

### 6.3 Periodic Review

Monthly:
- Review approval/rejection ratio
- Analyze common rejection reasons
- Update review checklist if needed
- Assess SLA compliance

## 7. Quick Reference

### Approve
```bash
curl -X POST .../triggers/{id}/approve -d '{"approved_by": "name", "comment": "..."}'
```

### Reject
```bash
curl -X POST .../triggers/{id}/reject -d '{"rejected_by": "name", "reason": "..."}'
```

### List Pending
```bash
curl .../triggers/pending
```

### Approval Alert
When pending > 4 hours, alert `ClaudeMdHighRiskChangePending` fires.

## 8. Contact

- **Questions:** #claude-md-improvement Slack
- **Urgent:** PagerDuty platform-engineering
- **Process Changes:** Platform Engineering Team
