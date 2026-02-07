---
allowed-tools: Bash(ruff:*), Bash(npm:*)
description: Run linting and formatting
---

Run code quality checks:

## Backend (Python)
```bash
cd backend && ruff check . --fix && ruff format .
```

## Frontend (TypeScript)  
```bash
cd frontend && npm run lint && npm run format
```

Report remaining issues.
