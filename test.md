---
allowed-tools: Bash(npm:*), Bash(pytest:*), Bash(uv:*), Read
argument-hint: [test-pattern]
description: Run tests with optional pattern
---

Run tests for: $ARGUMENTS

## Backend (Python)
```bash
cd backend && pytest -v --tb=short $ARGUMENTS
```

## Frontend (TypeScript)
```bash
cd frontend && npm test -- $ARGUMENTS
```

## Both
```bash
# Backend
cd backend && pytest -v

# Frontend  
cd frontend && npm test
```

Show results and any failures.
