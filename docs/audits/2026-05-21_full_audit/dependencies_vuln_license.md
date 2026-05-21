# KIRO2 Dependency Vulnerability + License + SBOM Audit

**Audit date:** 2026-05-21
**Scope:** Backend Python (`requirements.txt`, installed env 356 pkgs), Frontend Node (`package.json`, 1175 pkgs), Docker base images
**Tooling:** `pip-audit 2.10.0`, `safety 3.7.0`, `pip-licenses 5.5.5`, `pipdeptree 2.35.3`, `npm audit`, `depcheck`, `license-checker`
**Read-only:** No package upgrades performed. Tooling install only.
**Raw output:** Side-files in this directory (`pip_audit.json`, `npm_audit.json`, `pip_vuln_table.txt`, etc.)

---

## 0. Executive Summary

| Surface | Total pkg | Vulnerable pkg | Total CVEs | CRITICAL | HIGH | MEDIUM/LOW |
|---|---|---|---|---|---|---|
| **Backend Python** (installed) | 356 | 34 | **82** | **~33** | ~16 | ~33 |
| **Frontend Node** (incl transitive) | 1,344 | 28 | **29** | **1** | **17** | 11 |
| Docker base | python:3.11-slim, node:20-alpine, nginx:alpine | — | unscanned (trivy unavailable) | — | — | — |

**Headline numbers:**

- **111 known vulnerabilities** across the codebase (82 Python + 29 Node).
- **34 CRITICAL+HIGH severity findings** — many with available fix versions a single point release away.
- 1 **AGPL-3.0** (Ultralytics) and 1 **GPL-3.0+** (rfc3987) packages in production deps — **license-compliance risk** (see §5).
- Frontend has 1175 transitive packages → 14× bus-factor exposure vs. 83 direct.
- Dependabot **is configured** (weekly schedule) — but Renovate is not, and the volume of outdated packages (54 frontend, 171 Python) indicates the PRs are not being merged.

**P0 (act within 24h):** §1.1 lines 1–10 — `transformers`, `aiohttp`, `pillow`, `urllib3`, `pyjwt`, `python-multipart`, `cryptography`, `langchain-core`, `idna`, `setuptools`. All have CRITICAL CVE + available fix.

---

## 1. Backend Python — pip-audit results

### 1.1 Vulnerabilities by severity

Severity inferred from CVE description keywords (RCE/SQL/auth-bypass = CRITICAL; XSS/SSRF/path-traversal/prototype-pollution/DoS/ReDoS = HIGH; remainder = MEDIUM). This is best-effort; CVSS scores not available in pip-audit JSON.

| SEV | Package | Version | CVE | Fix |
|---|---|---|---|---|
| CRITICAL | aiohttp | 3.13.3 | CVE-2026-34515 | 3.13.4 |
| CRITICAL | aiohttp | 3.13.3 | CVE-2026-34517 | 3.13.4 |
| CRITICAL | fastmcp | 0.2.0 | CVE-2025-69196 | 2.14.2 |
| CRITICAL | fastmcp | 0.2.0 | CVE-2025-64340 | 3.2.0 |
| CRITICAL | fastmcp | 0.2.0 | CVE-2026-27124 | 3.2.0 |
| CRITICAL | filelock | 3.20.0 | CVE-2026-22701 | 3.20.3 |
| CRITICAL | idna | 3.11 | CVE-2026-45409 | 3.15 |
| CRITICAL | langchain-core | 1.2.7 | CVE-2026-26013 | 1.2.11 |
| CRITICAL | langchain-core | 1.2.7 | CVE-2026-44843 | 1.3.3 |
| CRITICAL | langgraph-checkpoint | 3.0.1 | CVE-2026-27794 | 4.0.0 |
| CRITICAL | langsmith | 0.6.2 | CVE-2026-45134 | 0.8.0 |
| CRITICAL | nltk | 3.9.4 | PYSEC-2026-97 | **(no fix)** |
| CRITICAL | ollama | 0.6.1 | PYSEC-2025-146 | **(no fix)** |
| CRITICAL | pillow | 12.0.0 | CVE-2026-42310 | 12.2.0 |
| CRITICAL | pillow | 12.0.0 | CVE-2026-42311 | 12.2.0 |
| CRITICAL | pyasn1 | 0.6.1 | CVE-2026-23490 | 0.6.2 |
| CRITICAL | pyasn1 | 0.6.1 | CVE-2026-30922 | 0.6.3 |
| CRITICAL | pyjwt | 2.10.1 | PYSEC-2025-183 | **(no fix listed)** |
| CRITICAL | python-dotenv | 1.2.1 | CVE-2026-28684 | 1.2.2 |
| CRITICAL | python-multipart | 0.0.21 | CVE-2026-24486 | 0.0.22 |
| CRITICAL | setuptools | 70.2.0 | PYSEC-2025-49 | 78.1.1 |
| CRITICAL | transformers | 4.57.3 | PYSEC-2025-211..218, CVE-2026-1839 | 5.0.0rc3 (×8 CVEs) |
| CRITICAL | urllib3 | 2.6.2 | PYSEC-2026-142, CVE-2026-21441 | 2.7.0 |
| CRITICAL | uv | 0.9.21 | GHSA-pjjw-68hj-v9mw | 0.11.6 |
| HIGH | aiohttp | 3.13.3 | CVE-2026-34513, CVE-2026-34516 | 3.13.4 |
| HIGH | ecdsa | 0.19.1 | CVE-2026-33936 | 0.19.2 |
| HIGH | fastmcp | 0.2.0 | CVE-2025-62800 | 2.13.0 |
| HIGH | filelock | 3.20.0 | CVE-2025-68146 | 3.20.1 |
| HIGH | langchain-text-splitters | 1.1.0 | PYSEC-2026-77 | 1.1.2 |
| HIGH | langsmith | 0.6.2 | CVE-2026-25528 | 0.6.3 |
| HIGH | ollama | 0.6.1 | PYSEC-2025-144, 145; PYSEC-2026-101, 102 | **(no fix)** |
| HIGH | pillow | 12.0.0 | CVE-2026-40192 | 12.2.0 |
| HIGH | py | 1.11.0 | PYSEC-2022-42969 | **(unmaintained)** |
| HIGH | pytest | 8.4.2 | CVE-2025-71176 | 9.0.3 |
| HIGH | python-jose | 3.5.0 | PYSEC-2025-185 | **(no fix listed)** |
| HIGH | python-multipart | 0.0.21 | CVE-2026-40347, CVE-2026-42561 | 0.0.27 |
| MEDIUM | aiohttp | 3.13.3 | 6 CVEs | 3.13.4 |
| MEDIUM | cryptography | 46.0.3 | PYSEC-2026-35, 36; CVE-2026-26007 | 46.0.5–46.0.7 |
| MEDIUM | ecdsa | 0.19.1 | CVE-2024-23342 | **(no fix)** |
| MEDIUM | flask-cors | 6.0.2 | PYSEC-2024-271 | **(no fix)** |
| MEDIUM | joblib | 1.5.3 | PYSEC-2024-277 | **(no fix)** |
| MEDIUM | langchain-community | 0.4.1 | PYSEC-2024-278 | **(no fix)** |
| MEDIUM | mako | 1.3.10 | CVE-2026-44307 | 1.3.12 |
| MEDIUM | orjson | 3.11.5 | CVE-2025-67221 | 3.11.6 |
| MEDIUM | pip | 26.0 | CVE-2026-3219, CVE-2026-6357 | 26.1 |
| MEDIUM | pygments | 2.19.2 | CVE-2026-4539 | 2.20.0 |
| MEDIUM | requests | 2.32.5 | CVE-2026-25645 | 2.33.0 |
| MEDIUM | urllib3 | 2.6.2 | PYSEC-2026-141 | 2.7.0 |
| MEDIUM | werkzeug | 3.1.5 | CVE-2026-27199 | 3.1.6 |

**Worst offenders** (by raw CVE count):

| Package | CVE count | Fix version |
|---|---|---|
| aiohttp 3.13.3 | 10 | 3.13.4 (one patch release away!) |
| transformers 4.57.3 | 9 | 5.0.0rc3 (major bump) |
| fastmcp 0.2.0 | 6 | 2.14.2 / 3.2.0 (drastic catch-up) |
| ollama 0.6.1 | 6 | **no fixes available** |
| pillow 12.0.0 | 6 | 12.1.1 / 12.2.0 |

**Unfixable now (need replacement or removal):**

- `nltk 3.9.4` — PYSEC-2026-97 CRITICAL, no fix.
- `ollama 0.6.1` — 6 CVEs (4 HIGH, 1 CRITICAL), no fix versions.
- `py 1.11.0` — PYSEC-2022-42969 HIGH (ReDoS), package unmaintained for 3+ years. Likely transitive of `pytest`/`pytest-something` — `python -m pipdeptree -p py` will confirm.
- `python-jose 3.5.0` — PYSEC-2025-185 HIGH, no fix listed (project effectively dead).
- `pyjwt 2.10.1` — PYSEC-2025-183 CRITICAL, fix `2.12.0` listed for a separate CVE only.

### 1.2 Outdated Python packages

171 packages are outdated. Top representative gaps:

| Package | Current | Latest | Diff |
|---|---|---|---|
| anthropic | 0.75.0 | 0.103.1 | 28 minor (SDK drift) |
| bcrypt | 4.0.1 | 5.0.0 | major (pinned `<4.1.0` for passlib compat — see `requirements.txt:147`) |
| fastapi | 0.128.0 | 0.136.1 | 8 minor |
| fastmcp | 0.2.0 | 3.3.1 | **3 major releases behind** |
| google-genai | 2.0.0 | 2.5.0 | 5 minor |
| huggingface-hub | 0.36.0 | 1.16.0 | major |
| ollama | 0.6.1 | (vuln) | unmaintained version |
| starlette | 0.50.0 | 1.0.0 | major |
| transformers | 4.57.3 | (5.0.0rc3) | major-rc |
| uvicorn | 0.40.0 | 0.47.0 | 7 minor |

(Full list: `python_outdated.txt`, 171 lines.)

### 1.3 Critical security packages — status

| Package | Current | Latest | CVEs | Action |
|---|---|---|---|---|
| cryptography | 46.0.3 | 48.0.0 | 3 | UPDATE |
| PyJWT | 2.10.1 | 2.12.1 | 2 | UPDATE |
| python-jose | 3.5.0 | (latest) | 1 | UPDATE (unfixable — replace?) |
| urllib3 | 2.6.2 | 2.7.0 | 3 | UPDATE |
| requests | 2.32.5 | 2.34.2 | 1 | UPDATE |
| pillow | 12.0.0 | 12.2.0 | 6 | UPDATE |
| pydantic | 2.12.5 | 2.13.4 | 0 | minor |
| sqlalchemy | 2.0.45 | 2.0.49 | 0 | minor |
| fastapi | 0.128.0 | 0.136.1 | 0 | minor |
| starlette | 0.50.0 | 1.0.0 | 0 | major bump available |
| passlib | 1.7.4 | 1.7.4 | 0 | OK (note: bcrypt pin `<4.1.0` is for passlib compat) |
| bleach | 6.3.0 | 6.3.0 | 0 | OK |
| authlib | 1.7.2 | 1.7.2 | 0 | OK |
| jinja2 | 3.1.6 | 3.1.6 | 0 | OK |

**JWT stack is in worst shape.** `pyjwt` has a CRITICAL no-fix, `python-jose` has HIGH no-fix. Both are present — the security review needs to confirm which library the authentication actually uses (CLAUDE.local.md cites JWT but does not specify the library), then drop the unused one and migrate off `python-jose` entirely (project is dormant).

---

## 2. Frontend Node — npm audit results

### 2.1 npm audit summary

```
info: 0  |  low: 1  |  moderate: 10  |  high: 17  |  critical: 1  |  total: 29
```

**Dependency counts (audit metadata):**

```
prod: 383   dev: 960   optional: 109   total: 1,344
```

### 2.2 Vulnerabilities by package

| Package | Sev | Fix avail? | Via (first 2 chain heads) |
|---|---|---|---|
| **basic-ftp** | **CRITICAL** | yes | Path traversal in downloadToDir(); CRLF injection |
| @babel/plugin-transform-modules-systemjs | high | yes | arbitrary code gen on malicious input |
| @remix-run/router | high | yes | XSS via open redirects |
| @rollup/plugin-terser | high | yes | serialize-javascript |
| **axios** | high | yes | NO_PROXY normalization SSRF; auth bypass via prototype pollution |
| fast-uri | high | yes | path traversal via %-encoded dot segments |
| flatted | high | yes | unbounded recursion DoS in parse() |
| **lodash** | high | yes | prototype pollution in `_.unset`/`_.omit`; code injection in `_.template` |
| lodash-es | high | yes | same as lodash |
| minimatch | high | yes | ReDoS via repeated wildcards |
| path-to-regexp | high | yes | ReDoS |
| picomatch | high | yes | method injection in POSIX character classes |
| **react-router** | high | yes | unexpected external redirect via untrusted paths |
| **react-router-dom** | high | yes | transitive via react-router |
| serialize-javascript | high | yes | RCE via RegExp.flags / Date.prototype.toISOString |
| tar | high | yes | arbitrary file create/overwrite via hardlink |
| **vite** | high | yes | `server.fs.deny` bypass via backslash on Windows; path traversal in optimized deps `.map` |
| workbox-build | high | yes | @rollup/plugin-terser |
| brace-expansion | moderate | yes | zero-step seq → process hang |
| dompurify | moderate | yes | XSS; ADD_ATTR skips URI validation |
| follow-redirects | moderate | yes | leaks custom auth headers cross-domain |
| ip-address | moderate | yes | XSS in Address6 HTML emit |
| js-yaml | moderate | yes | prototype pollution via merge `<<` |
| mdast-util-to-hast | moderate | yes | unsanitized class attribute |
| mermaid | moderate | yes | Gantt chart infinite loop; classDefs CSS injection |
| postcss | moderate | yes | XSS via unescaped `</style>` |
| ws | moderate | yes | uninitialized memory disclosure |
| yaml | moderate | yes | stack overflow via deeply nested |
| qs | low | yes | arrayLimit bypass DoS |

**Production-runtime exposure (not just dev):** `axios`, `dompurify`, `react-router-dom`, `lodash`, `mermaid`, `qs`. All are in the runtime bundle. Frontend code uses `katex` + `react-markdown` + `dompurify` for math/markdown rendering — DOMPurify's moderate XSS issue is a direct risk to the question/solution rendering path.

### 2.3 Outdated Node packages

54 direct deps are outdated. Major bumps available:

| Package | Current | Latest | Notes |
|---|---|---|---|
| react | 18.3.1 | 19.2.6 | major (dependabot pinned to 18.x — see `.github/dependabot.yml:78`) |
| react-router-dom | 6.30.1 | 7.15.1 | major + HIGH CVE |
| react-dom | 18.3.1 | 19.2.6 | major (paired with react) |
| @mui/material | 5.18.0 | 9.0.1 | **4 major versions behind** |
| @mui/icons-material | 5.18.0 | 9.0.1 | 4 major |
| vite | 7.1.6 | 8.0.14 | major + HIGH CVE |
| vitest / @vitest | 3.2.4 | 4.1.7 | major |
| eslint | 8.57.1 | 10.4.0 | 2 majors |
| typescript | 5.9.2 | 6.0.3 | major |
| framer-motion | 10.18.0 | 12.40.0 | 2 majors |
| zustand | 4.5.7 | 5.0.13 | major |
| mermaid | 10.9.5 | 11.15.0 | major + moderate CVE |
| jsdom | 23.2.0 | 29.1.1 | **6 majors behind** |
| jest-axe | 8.0.0 | 10.0.0 | 2 majors |
| recharts | 2.15.4 | 3.8.1 | major |
| lucide-react | 0.263.1 | 1.16.0 | **major (jumped >1.0)** |
| @testing-library/react | 14.3.1 | 16.3.2 | 2 majors |

(Full list: `npm_outdated.json`, 54 entries.)

---

## 3. Pin tightness audit

### 3.1 Backend `requirements.txt`

| Pin type | Count | % |
|---|---|---|
| Exact (`==`) | 45 | 54% |
| Floor (`>=`) | 38 | 46% |
| Upper bound (`<`) | 1 | 1% (only `bcrypt<4.1.0` for passlib compat) |
| No pin | 0 | 0% |

**Risk:** **No transitive lockfile is committed** (`requirements.qa.lock.txt` exists at 234 lines but `requirements.txt` is loaded primarily by Docker — see `backend/Dockerfile`). Mixed `==`/`>=` strategy means production reproducibility is environment-dependent. Docker rebuilds at different times will resolve different transitive trees.

**Recommendation:** Switch to `uv pip compile` or `pip-tools` to generate a fully-pinned `requirements.lock` from `requirements.txt`. Already have `uv 0.9.21` installed (it itself has a CVE — bump to 0.11.6 first).

### 3.2 Frontend `package.json`

| Pin type | Count | % |
|---|---|---|
| Caret (`^`) | 83 | 100% |
| Tilde (`~`) | 0 | 0% |
| Exact | 0 | 0% |

`package-lock.json` is committed, so reproducibility is OK. But `^` everywhere means any `npm update` minor bump silently applies. No upper bounds.

---

## 4. License compliance

### 4.1 Backend Python license distribution

Total: 351 packages analyzed (`pip-licenses --format=plain --summary`).

| Category | Count | Risk |
|---|---|---|
| MIT / MIT License / MIT-CMU / MIT-0 | ~149 | OK |
| Apache-2.0 / Apache Software License (variants) | ~85 | OK |
| BSD (2/3/License) | ~73 | OK |
| ISC | 3 | OK |
| Python Software Foundation | 4 | OK |
| MPL-2.0 (weak copyleft) | 9 | OK (file-level copyleft, fine for SaaS) |
| LGPL-3.0-only / LGPL | 3 (`psycopg`, `psycopg-binary`, `psycopg2-binary`) | OK if dynamically linked (default for pip wheels) |
| **GPL-3.0+** | **1** (`rfc3987 1.3.8`) | **REVIEW** |
| **AGPL-3.0+** | **3** (`ultralytics 8.4.12`, `ultralytics-thop 2.0.18`, `PyMuPDF 1.27.2.2` dual-licensed) | **HIGH RISK** |
| UNKNOWN | 1 | Review |

**P0 license findings:**

1. **`ultralytics` (AGPL-3.0+) + `ultralytics-thop` (AGPL-3.0+).** AGPL requires source disclosure for *any* network use. If KIRO2's backend uses these in a request path (likely for vision/object detection), the AGPL-3.0 license can require open-sourcing the **entire** backend or buying a commercial Artifex/Ultralytics license. Verify whether these are imported in any production code path — if yes, this is a release blocker.

2. **`PyMuPDF 1.27.2.2`** is dual-licensed AGPL-3.0 OR Artifex Commercial. Same risk profile if no commercial license is held — and KIRO2 does use PDF processing (`reportlab`, `pdfplumber`, `PyPDF2`, `pytesseract`, `pdf2image` are in `requirements.txt`).

3. **`rfc3987` (GPL-3.0+).** Likely transitive (Jupyter-derived). Linking against GPL-3.0 from KIRO2's proprietary code is a violation. `pipdeptree -p rfc3987` should confirm the chain.

### 4.2 Frontend Node license distribution

```
MIT: 1012
ISC: 90
Apache-2.0: 41
BSD-3-Clause: 30
BSD-2-Clause: 16
BlueOak-1.0.0: 11
MPL-2.0: 5
CC0-1.0: 3
(MIT OR CC0-1.0): 3
Unlicense: 2
Python-2.0: 1
CC-BY-4.0: 1
(MPL-2.0 OR Apache-2.0): 1
EPL-2.0: 1   <-- Eclipse Public License - weak copyleft, review
(AFL-2.1 OR BSD-3-Clause): 1
MIT*: 1
UNLICENSED: 1   <-- the kiro2 frontend itself ("private": true) - OK
0BSD: 1
MIT AND ISC: 1
```

**No GPL/AGPL/SSPL found in npm tree.** OK.

**Review:** `EPL-2.0` (1 package — likely `xpath` or similar) is weak copyleft; usage as a library does not trigger source disclosure but verify the package name.

### 4.3 npm deprecation warnings (from license-checker run)

```
inflight@1.0.6   - memory leak, do not use (transitive)
debuglog@1.0.1   - no longer supported
readdir-scoped-modules@1.1.0 - moved to @npmcli/fs
osenv@0.1.5      - no longer supported
glob@7.2.3       - known security issues, must update
read-package-json@2.1.2 - use @npmcli/package-json
read-installed@4.0.3 - no longer supported
```

7 deprecated transitive packages → npm tree is aging.

---

## 5. SBOM-like summary

### 5.1 Backend

```
Direct in requirements.txt:   83
Total installed in env:      356
Transitive expansion ratio:  4.3×

Top 5 by direct child count (biggest sub-trees):
  chromadb              27 children
  schemathesis          21
  safety                17
  locust                15
  mcp                   14
  ultralytics           13   <- AGPL-3.0+
  langchain-community   12
```

### 5.2 Frontend

```
Direct deps in package.json:  37 production + 46 dev = 83 total
Total in node_modules:        1,175 packages (897 top-level + scoped sub-dirs)
Audit-tracked dep count:      1,344 (prod 383 + dev 960 + optional 109)
Transitive expansion ratio:   ~14×
```

`node_modules` size was not measured (background `du` was still running at audit close). Estimated: typical Vite + MUI 5 + React Markdown stacks land at 500–800 MB.

### 5.3 Docker base images

| Image | Base | Source files | CVE scan |
|---|---|---|---|
| backend (prod) | `python:3.11-slim` (multi-stage) | `backend/Dockerfile` | unscanned (trivy unavailable in env) |
| backend (production variant) | `python:3.11-slim-bullseye` | `backend/Dockerfile.production` | unscanned |
| backend (minimal/dev/zemberek/exporter/expert-agents) | `python:3.11-slim` | various | unscanned |
| frontend (prod) | `node:20-alpine` build → `nginx:alpine` runtime | `frontend/Dockerfile` | unscanned |
| frontend (alt) | `node:18-alpine` build → `nginx:alpine` runtime | `frontend/Dockerfile.nginx` | unscanned (also: Node 18 is now EOL — see §7) |

**Live image sizes:**
- `kiro2-backend:latest`: **9.76 GB** (huge — Ollama + torch + transformers + easyocr all baked in)
- `kiro2-frontend:latest`: 105 MB
- `kiro2-celery-worker:latest`: 9.04 GB
- `kiro2-celery-beat:latest`: 9.04 GB

Backend image bloat (~10 GB) suggests `torch`, `transformers`, `easyocr`, `sentence-transformers`, `ollama` and CUDA libs are bundled. Most are pulled in by AI features; many can be moved to a separate `kiro2-ai-worker` image, slimming the API container by an order of magnitude. Smaller image = smaller attack surface.

---

## 6. Unused dependencies

### 6.1 Frontend (`depcheck`)

Unused production deps (6):
```
@lottiefiles/dotlottie-react
class-variance-authority
date-fns          <- still listed but no imports detected
react-window      <- depcheck false-negative? note: @types/react-window also unused (devDep)
tailwind-merge
use-sound
```

Unused devDeps (7):
```
@tailwindcss/postcss
@types/jest
@types/react-window
@vitest/coverage-v8        <- false positive? script "test:coverage" uses it implicitly
autoprefixer               <- false positive? postcss config likely uses it
cross-env                  <- false positive? scripts use it
postcss                    <- false positive? config file
```

**Missing deps** (declared in code but not in `package.json`): 18, including `eslint-config-react-app`, `webpack`, several `workbox-*` modules, `zod`. These are likely from removed features or pre-Vite migration leftovers. Each `import` of a missing package will fail at build — verify which are dead code vs. broken.

### 6.2 Backend

No `pip-deps-unused` / `deptry` tool installed; pipdeptree only shows tree. A manual `grep -r "^import\|^from"` audit across `backend/app/` vs. `requirements.txt` direct deps would be the next step but is out of scope for a 45-minute pass.

---

## 7. Supply chain risk

### 7.1 No-fix-available packages (force a replacement decision)

| Package | Severity | Status | Action |
|---|---|---|---|
| `nltk 3.9.4` | CRITICAL (PYSEC-2026-97) | maintained but unpatched | wait or replace |
| `ollama 0.6.1` | 5 vulns, no fixes | client library | update upstream when patched |
| `python-jose 3.5.0` | HIGH PYSEC-2025-185 | **last release Mar 2025, repo dormant** | **migrate to `pyjwt` or `authlib.jose`** |
| `py 1.11.0` | HIGH ReDoS PYSEC-2022-42969 | unmaintained 3+ years | drop (likely pytest transitive ghost) |
| `ecdsa 0.19.1` | MEDIUM CVE-2024-23342 | timing attack, unfixed for >18 months | replace with `cryptography` only |
| `joblib 1.5.3` | PYSEC-2024-277 | maintained but unpatched | wait |
| `flask-cors 6.0.2` | PYSEC-2024-271 | maintained but unpatched | KIRO2 uses FastAPI not Flask — likely transitive, prune |
| `langchain-community 0.4.1` | PYSEC-2024-278 | active project, may not see fix in old line | upgrade major |

### 7.2 Dormant / single-maintainer red flags

- `python-jose` — release `3.5.0` on Mar 2025, no commits since. Bus factor = 1.
- `py` — declared "no longer maintained" by author. Should not be in any modern dependency graph.
- `rfc3987` — small one-maintainer package, GPL-3.0+, transitive only.

### 7.3 Backend major-version drift (>2 majors behind)

- `fastmcp 0.2.0 → 3.3.1` (jumped through `1.x`, `2.x`, `3.x`)
- `huggingface-hub 0.36.0 → 1.16.0`
- `chromadb 1.4.1 → 1.5.9` (only minor) — OK
- `starlette 0.50.0 → 1.0.0` (jumped major boundary)
- `bcrypt 4.0.x → 5.0.0` (pinned `<4.1.0` due to passlib API compat — passlib itself dormant since 2020; KIRO2 may need a passlib successor)
- `transformers 4.x → 5.0.0rc3` (security forces a major eventually)

### 7.4 Frontend major-version drift

- `react 18 → 19` (Dependabot intentionally pins to 18.x per config line 78 — that's a policy choice, not a vuln, but blocks fixes that ship in 19.x)
- `@mui/material 5 → 9` (4 majors)
- `vite 7 → 8` (major, also unblocks CVE fix)
- `vitest 3 → 4`
- `eslint 8 → 10`
- `typescript 5 → 6`
- `jsdom 23 → 29` (six majors)
- `lucide-react 0.263 → 1.16` (post-1.0)

### 7.5 Dependabot config

`.github/dependabot.yml` is configured. Schedules:

- Python (pip) — weekly Monday 03:00, limit 10 PRs
- Docker — weekly Monday 04:00
- GitHub Actions — weekly Monday 05:00
- npm (frontend) — weekly Tuesday 03:00, limit 10 PRs, react pinned 18.x/19.x ignored

**Observation:** Despite this config being in place, 171 Python packages and 54 npm packages are outdated. **Dependabot PRs are not being merged.** This is a process gap, not a config gap. A backlog of unmerged PRs is essentially the same as no Dependabot.

---

## 8. Critical security packages summary (final)

### Backend (with CVE + action)

| Pkg | Ver | Latest | CVE n | Severity peak | Action |
|---|---|---|---|---|---|
| cryptography | 46.0.3 | 48.0.0 | 3 | MEDIUM | bump to 46.0.7 (CVE fix), then minor to 48.x |
| pyjwt | 2.10.1 | 2.12.1 | 2 | **CRITICAL** | bump + confirm JWT lib in use |
| python-jose | 3.5.0 | dormant | 1 | HIGH | **REPLACE** with pyjwt or authlib.jose |
| urllib3 | 2.6.2 | 2.7.0 | 3 | CRITICAL | bump to 2.7.0 |
| requests | 2.32.5 | 2.34.2 | 1 | MEDIUM | bump |
| pillow | 12.0.0 | 12.2.0 | 6 | CRITICAL | bump to 12.2.0 |
| transformers | 4.57.3 | 5.0.0rc3 | 9 | CRITICAL | major-bump (5.x rc) or wait |
| aiohttp | 3.13.3 | 3.13.4 | 10 | CRITICAL | bump patch (3.13.4) — quick win |
| python-multipart | 0.0.21 | 0.0.27 | 3 | CRITICAL | bump |
| idna | 3.11 | 3.15 | 1 | CRITICAL | bump |
| filelock | 3.20.0 | 3.20.3 | 2 | CRITICAL | bump |
| pyasn1 | 0.6.1 | 0.6.3 | 2 | CRITICAL | bump (likely transitive) |
| setuptools | 70.2.0 | 78.1.1 | 2 | CRITICAL | bump |
| langchain-core | 1.2.7 | 1.3.3 | 3 | CRITICAL | bump |

### Frontend

| Pkg | Ver | Latest | Severity | Action |
|---|---|---|---|---|
| react-router-dom | 6.30.1 | 7.15.1 | HIGH | major-bump or apply security patch ≥6.30.2 |
| axios | 1.12.2 | 1.16.1 | HIGH | bump |
| vite | 7.1.6 | 8.0.14 | HIGH | major-bump |
| lodash | 4.17.21 | 4.18.1 | HIGH | bump |
| dompurify | 3.3.1 | 3.4.5 | MODERATE | bump (renders user math/markdown — prod path) |
| mermaid | 10.9.5 | 11.15.0 | MODERATE | major bump |
| basic-ftp | (transitive) | yes | **CRITICAL** | trace via `npm ls basic-ftp` — likely from `backstopjs` |

---

## 9. Prioritized findings

### P0 — fix this week (security regressions or licensing release-blocker)

1. **Verify Ultralytics/PyMuPDF AGPL exposure.** If imported in any production code path, either purchase commercial license or remove. `grep -r "import ultralytics\|from ultralytics\|import fitz\|import pymupdf" backend/` is the immediate check. **Release blocker if used.**
2. **Backend P0 vuln batch** (single PR, all bump-only fixes available):
   - `aiohttp 3.13.3 → 3.13.4` (10 CVEs)
   - `pillow 12.0.0 → 12.2.0` (6 CVEs)
   - `urllib3 2.6.2 → 2.7.0` (3 CVEs)
   - `idna 3.11 → 3.15` (CRITICAL)
   - `python-multipart 0.0.21 → 0.0.27` (3 CVEs)
   - `filelock 3.20.0 → 3.20.3` (2 CVEs)
   - `pyasn1 0.6.1 → 0.6.3` (2 CVEs)
   - `langchain-core 1.2.7 → 1.3.3` (3 CVEs)
   - `setuptools 70.2.0 → 78.1.1` (2 CVEs)
3. **Frontend P0 vuln batch:**
   - `axios → 1.16.1`
   - `react-router-dom → patched 6.30.x or 7.x`
   - `lodash → 4.18.1`
   - `dompurify → 3.4.5` (production rendering surface)
   - `vite → 8.x` (dev/build tool — lower risk but HIGH CVE)
   - `basic-ftp` — identify parent (`npm ls basic-ftp`) and bump or drop
4. **Replace `python-jose`** in any code path with `pyjwt 2.12+` or `authlib.jose`. Dormant project + HIGH no-fix CVE.

### P1 — fix this month

5. **Generate a Python lockfile.** Use `uv pip compile requirements.txt -o requirements.lock` (after bumping `uv` to 0.11.6 to fix `GHSA-pjjw-68hj-v9mw`). Commit the lock. Docker builds load lock only.
6. **Drop `bcrypt<4.1.0` pin.** This forces `bcrypt 4.0.1` (>1 year old) just for passlib compat. Either migrate off passlib (dormant since 2020) or accept the bcrypt 4.1.0 72-byte truncation behavior (it's a security improvement, not a regression).
7. **Sync Dependabot expectations with reality.** Configure auto-merge on patch-only security PRs, or assign a dependency-PR review rotation. Backlog of 200+ outdated packages with Dependabot configured is a worse signal than no Dependabot.
8. **Slim the backend Docker image.** 9.76 GB is excessive. Split AI workers (`torch`, `transformers`, `easyocr`, `ollama` clients, `sentence-transformers`) into a separate image. API container should be ≤500 MB.
9. **Audit unused frontend deps** identified by depcheck (manual confirmation needed — some are false positives) and prune.
10. **Backend depcheck equivalent.** Install `deptry` or run a manual `import` cross-reference vs. `requirements.txt`. `nltk`, `easyocr`, `sympy`, `matplotlib`, `plotly`, `pdf2image`, `gTTS`, `pyttsx3` may be unused in production endpoints.

### P2 — quarterly hygiene

11. **Trivy / Grype Docker image scan** in CI. Currently base images are not scanned at all.
12. **Migrate from `python:3.11-slim` to `python:3.12-slim`** (Python 3.11 receives security fixes only until Oct 2027 but 3.12 is the modern default).
13. **`Dockerfile.nginx` uses `node:18-alpine`** — Node 18 reached EOL April 2025. Either delete the file or bump to `node:20-alpine` (matches main Dockerfile).
14. **Replace `py 1.11.0`** transitive. Run `pipdeptree -p py` to find the parent — most likely `pytest-something`-old, swap for a maintained alternative.
15. **License-CI gate.** Add a step that fails the build if a new AGPL/GPL/SSPL package enters either dep tree.
16. **Renovate** as a Dependabot alternative — supports auto-merge rules natively without GitHub Actions wiring.

---

## Appendix: raw output files

- `pip_audit.json` — full pip-audit output (356 deps, 82 vulns)
- `pip_vuln_table.txt` — severity-categorized vuln table
- `npm_audit.json` — npm audit JSON (29 vulns)
- `python_licenses.txt` — pip-licenses plain output
- `python_outdated.txt` — pip list --outdated (171 entries)
- `npm_licenses_summary.txt` — license-checker summary
- `npm_outdated.json` — npm outdated --json (54 entries)
- `pipdeptree.json` — full Python dep tree
- `depcheck.json` — frontend unused deps report

---

*Generated: 2026-05-21. Audit scope: backend Python + frontend Node + Docker. Trivy/Grype not available in environment so Docker image CVE scan was skipped. CVSS severity inferred from CVE description keywords — re-run with `safety check --output json` for upstream-assigned CVSS scores if needed.*
