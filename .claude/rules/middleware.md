# Middleware — HTTPException propagation

Session 148 (GF99 root cause). This rule exists because the CSRF
middleware `raise HTTPException(403, ...)` bug silently surfaced as a
generic 500 for weeks, and we only caught it when Wave 11 GF99 probed
the admin key-rotation endpoint with a student Bearer token.

## The rule

> **Never `raise HTTPException` from inside `BaseHTTPMiddleware.dispatch()`
> (or any other middleware). Return a concrete `starlette.responses.Response`
> — usually `JSONResponse` with an explicit `status_code`.**

## Why

FastAPI's global `HTTPException` handler only runs for exceptions raised
from *route handlers* (or dependencies resolved inside the route-handler
scope). An exception raised from a middleware `dispatch` does **not**
propagate through `handle_exc`; it escapes the middleware stack and is
caught by Starlette's default `ServerErrorMiddleware`, which converts it
to a plain `500 Internal Server Error` with no body shape, no logging
context, and no correlation with the middleware that raised it.

In practice this means:

- A 401/403/429 raised from middleware becomes a 500 at the client.
- Monitoring fires on the wrong status code (crash, not auth failure).
- Clients that branch on `response.status !== 500` (half of them) will
  not retry or re-auth, making the bug user-visible.

## The fix pattern

Wrong (surfaces as 500):

```python
class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not self._validate_csrf(request):
            raise HTTPException(
                status_code=403,
                detail="CSRF token mismatch",
            )
        return await call_next(request)
```

Right (surfaces as 403 to client):

```python
from starlette.responses import JSONResponse

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not self._validate_csrf(request):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch"},
            )
        return await call_next(request)
```

## Scope

This rule applies to any subclass of `starlette.middleware.base.BaseHTTPMiddleware`
under `backend/core/`, `backend/middleware/`, or anywhere else. It also
applies to any middleware attached via `@app.middleware("http")` that
uses `call_next` — those wrappers run in the same exception scope as
`BaseHTTPMiddleware.dispatch`.

**Exception:** middleware that lives *inside* a FastAPI dependency
(e.g. a dependency function that raises `HTTPException`) is fine —
dependencies resolve inside the route scope, so `HTTPException` there
still propagates to the global handler correctly. This rule is only
about the outer middleware ring.

## Known incidents

- **GF99 / Session 147**: `core/csrf_protection.py` `raise HTTPException(403)`
  surfaced as 500. Two-part fix required:
  1. `return JSONResponse(status_code=403, content={...})` instead of raise.
  2. Early-return `await call_next(request)` for Bearer-authenticated
     clients (they can't be CSRF'd and shouldn't trip the check).
  See commit `cf4147b` for the full diff.

## Related rules

- `.claude/rules/golden-flows.md` — GF99 probe covers this surface.
- `.claude/rules/debugging-first.md` — Middleware 500s are almost always
  a "500 is actually a 4xx" class bug. Check middleware before tracing
  handler code.

---

*Oluşturulma: 2026-04-12 Session 148*
