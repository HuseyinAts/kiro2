# Frontend Raw `fetch()` → `apiClient` Migration Runbook

**S180 audit reference**: `docs/audits/2026-05-22_product_ready_audit/03_frontend.md` §fetch
**Estimated effort**: 1 sprint (~5 days), depends on consumer count per file.
**Risk**: Centralized auth retry, rate-limit handling, error normalization currently bypassed in 10 services.

## Inventory (live as of 2026-05-22)

| File | Raw fetch calls | Priority |
|---|---|---|
| `services/revolutionaryFeaturesService.ts` | **19** | 🔴 P0 |
| `services/chatService.ts` | several | 🟡 P1 |
| `services/fsrsService.ts` | — | 🟡 P1 |
| `services/backgroundSyncService.ts` | — | 🟡 P1 |
| `services/culturalAdaptationService.ts` | — | 🟢 P2 |
| `services/multiAgentService.ts` | — | 🟡 P1 |
| `services/NetworkDetector.ts` | — | 🟢 P2 |
| `services/offlineStorageService.ts` | — | 🟢 P2 |
| `services/socialService.ts` | — | 🟡 P1 |
| `services/VideoLoadingManager.ts` | — | 🟢 P2 |

## Canonical migration pattern

### BEFORE (raw fetch)

```typescript
const response = await fetch('/api/v1/some/endpoint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
  credentials: 'include',
});

if (!response.ok) {
  throw new Error('Request failed');
}

const data = await response.json();
```

### AFTER (apiClient wrapper)

```typescript
import { apiClient } from '@/services/apiClient';

const data = await apiClient.post<MyResponse>('/some/endpoint', payload);
```

**Benefits gained**:
- Centralized auth header injection (httpOnly cookie via `credentials: 'include'` default)
- Auto-retry on 401 with refresh token (single source)
- Consistent error envelope shape (`{detail: string, code?: string}`)
- Sentry/observability hook integration (via `apiClient.interceptors`)
- Rate-limit 429 handling with exponential backoff
- `/api/v1/` prefix automatic — current raw fetches hardcode it (drift risk)

## Per-file migration order (recommended)

### Step 1 — `revolutionaryFeaturesService.ts` (P0, 19 sites)

Highest blast radius. Audit one by one:
```bash
grep -nE "fetch\(" frontend/src/services/revolutionaryFeaturesService.ts
```
Each call gets converted to `apiClient.get/post/put/delete` with typed response.

### Step 2 — `chatService.ts` + `socialService.ts` + `multiAgentService.ts` (P1)

These ship to many users daily. Same conversion pattern.

### Step 3 — `fsrsService.ts` + `backgroundSyncService.ts` (P1)

Important for offline-mode resilience but not user-facing.

### Step 4 — Remaining (P2)

`culturalAdaptationService.ts`, `NetworkDetector.ts`, `offlineStorageService.ts`,
`VideoLoadingManager.ts` — lower-traffic, defer until P0/P1 done.

## Validation per file

After each file migration:

```bash
cd frontend
npm run lint -- src/services/<filename>
npx tsc --noEmit
npm test -- src/services/__tests__/<filename>.test.ts
```

Then E2E smoke:
- Boot frontend (`npm run dev`)
- Trigger UX path that hits the migrated service
- Verify network tab shows `Authorization` not in headers (cookie only) and `/api/v1/` prefix

## Anti-patterns (DO NOT do)

```typescript
// BAD: bypass apiClient because "it's just one call"
const r = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/x`, ...);

// BAD: manually adding Authorization header
fetch(url, { headers: { Authorization: `Bearer ${token}` } });

// BAD: re-implementing apiClient retry logic
let attempt = 0;
while (attempt < 3) { ... }
```

## Tracking

Add this file to the next sprint plan. Each file conversion gets a separate commit
of pattern `refactor(frontend): migrate <service> to apiClient (S180 #13)`.

When all 10 files are done, delete this runbook.
