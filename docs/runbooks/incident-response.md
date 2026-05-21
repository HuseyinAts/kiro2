# KIRO2 Incident Response Runbook

**Created:** Session 179 (S179 fix B-P1-15)
**Status:** v1 — minimum-viable. Expand per incident retrospective.

This runbook is intentionally short. Long runbooks are not read at 3 AM.

---

## Severity ladder

| SEV | Trigger | Page | Target MTTR |
|---|---|---|---|
| 1 | Production DB unreachable / data loss / auth bypass live | YES, immediately | 30 min |
| 2 | Feature broken for ≥10% of users / >5min downtime | YES, business hours | 2 hours |
| 3 | One feature degraded, workaround exists | Slack only | 24 hours |
| 4 | Cosmetic / single user / no UX impact | Issue tracker | 1 week |

If unsure → escalate one level up. Easier to downgrade than upgrade.

---

## SEV-1 declared — first 5 minutes

1. **State publicly** in the team channel: `[SEV-1] <one-line>`.
2. **One IC (incident commander).** Everyone else stops touching prod.
3. **Don't run destructive commands** (`DROP`, `force push`, `rm -rf`)
   while diagnosing. Make a backup first.
4. **Capture state**: `docker ps`, recent logs, `git log -5`, last deploy.
5. **Communicate** every 15 minutes — even if no progress.

---

## Common SEV-1 playbooks

### A. Backend 503 / unhealthy

```bash
# 1. Is the container alive?
docker ps --filter "name=kiro2-backend"
docker inspect kiro2-backend --format '{{.State.Health.Status}}'

# 2. Recent errors?
docker logs kiro2-backend --tail 200

# 3. DB reachable?
pg_isready -h localhost -p 5434
redis-cli -h localhost ping

# 4. Restart only if step 1-3 don't explain it
docker restart kiro2-backend
sleep 22
curl -sf http://localhost:8000/health
```

### B. PostgreSQL down

```bash
# Verify
pg_isready -h localhost -p 5434

# Native Windows service
# (must be done by Hüseyin from the host — no remote autostart)
sc query postgresql-x64-18

# After restart
PGPASSWORD=$PG_PW psql -h localhost -p 5434 -d kiro2 -c "SELECT 1"
```

If data file corruption suspected: **STOP**, do not start. Capture
`pg_log` first. Recovery is reversible only before re-replay.

### C. Redis down (cache + rate limit + leaderboard)

```bash
docker logs kiro2-redis --tail 100
docker restart kiro2-redis
redis-cli ping
```

Impact while down: login rate limit becomes in-memory (per-worker),
leaderboard reads fall back to slower DB query, FSRS due fallback to
empty list. **No data loss** — Redis is cache-only for KIRO2.

### D. Auth bypass / live IDOR

1. **Immediately** rotate `JWT_SECRET` and invalidate all sessions:
   ```bash
   # Generate new secret
   python -c "import secrets; print(secrets.token_urlsafe(64))" > /tmp/new
   # Set in .env.mvp + restart backend
   docker compose up -d --no-deps backend
   ```
2. Blacklist all active tokens in Redis (auto-expires in 7d).
3. Document what was exposed. KVKK timer starts.

### E. Frontend crash loop / build broken

```bash
# 1. Last successful commit
git log --oneline -10

# 2. Revert
git revert <bad-sha>

# 3. Frontend container
docker compose restart frontend
```

---

## Rollback procedure

```bash
# 1. Identify last known good
git log --oneline --all | head -20

# 2. Tag current state for forensic
git tag rollback-$(date +%Y%m%d-%H%M)

# 3. Reset on a new branch (NEVER force-push main)
git checkout -b rollback/$(date +%Y%m%d) <good-sha>
git push origin rollback/$(date +%Y%m%d)

# 4. Redeploy from rollback branch
```

**Alembic downgrade** (if migration is the cause):

```bash
cd backend
alembic current        # see what's deployed
alembic history -r-3:   # see recent migrations
alembic downgrade -1    # one step back
```

Never `alembic downgrade base` on production. Data migrations are
not always reversible.

---

## Communication template

```
[SEV-X] <one-line>
IC: <name>
Status: investigating | identified | mitigating | resolved
ETR: <time> | unknown
Impact: <who, what>
Last update: <iso8601>
```

Update every 15 min for SEV-1, hourly for SEV-2.

---

## Postmortem (within 48 hours of resolution)

Create `docs/runbooks/postmortems/<YYYY-MM-DD>-<slug>.md`:

1. **Summary** — what happened, blast radius, MTTR
2. **Timeline** — minute-by-minute
3. **Root cause** — 5-whys, not "the disk filled"
4. **What worked** — keep doing this
5. **What didn't** — fix this
6. **Action items** — concrete, owner, due date, tracker ID

No blame. Systems fail; the question is what guard rail we add.

---

## Useful contacts

- **Project lead:** Hüseyin (`huseyinates038@gmail.com`)
- **DB:** Native PostgreSQL 18, port 5434, db `kiro2` (NOT `kiro2_db`)
- **Redis:** `kiro2-redis` container, port 6379
- **Audit history:** `docs/audits/`
- **Session handoffs:** `.claude/sessions/latest.md`

---

*Update this file after every SEV-1 retrospective.*
