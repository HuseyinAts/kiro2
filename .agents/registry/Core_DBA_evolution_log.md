# Core_DBA Evolution Log

### Iteration 1
- **Observation**: Detected high CPU usage and long wait times for pg_stat_statements. `auth/login` endpoint is doing heavy sequential scans on `users` table due to missing index on email, and the password hashing algorithm `bcrypt` is blocking the event loop or taking too much CPU.
- **Action**: Suggested adding `Index("idx_user_email", "email")` (which already exists but maybe needs `varchar_pattern_ops`). Also suggested using pgBouncer for connection pooling to avoid connection limits when 5000 concurrent users hit.
- **Evolution**: Updated System Prompt to always check connection pool limits and index usage during high concurrency.
