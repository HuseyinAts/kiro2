---
allowed-tools: Bash(git:*), Bash(npm:*), Bash(pytest:*)
description: Show project status and health
---

## Git Status
```bash
git status --short
git log --oneline -5
```

## Backend Health
```bash
cd backend && pytest --collect-only 2>&1 | grep "test session starts"
```

## Frontend Health  
```bash
cd frontend && npm run typecheck 2>&1 | tail -5
```

## Database
```bash
psql -U postgres -d kiro2 -c "SELECT COUNT(*) as question_count FROM questions;" 2>/dev/null || echo "Database not running"
```

Show summary of project health.
