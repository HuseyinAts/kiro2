# Subagent Coordination Directory

File-based coordination for parallel subagent operations.

## Structure
```
coordination/
├── tasks/        # Pending task definitions (JSON)
├── results/      # Completed task results (JSON)
├── locks/        # File locks for race condition prevention
├── state.json    # Global coordination state
└── README.md     # This file
```

## Task Format
```json
{
  "id": "task-001",
  "type": "security-review",
  "status": "pending|in_progress|completed|failed",
  "created": "ISO-8601",
  "assigned_to": "agent-name|null",
  "input": {},
  "dependencies": [],
  "priority": 1
}
```

## Result Format
```json
{
  "task_id": "task-001",
  "status": "completed|failed",
  "completed_at": "ISO-8601",
  "agent": "agent-name",
  "output": {},
  "metrics": {"duration_ms": 0, "tokens_used": 0}
}
```

## Lock Convention
- Lock file name: `{filepath-with-dashes}.lock`
- Contains PID of locking process
- Auto-expires after 30 minutes
