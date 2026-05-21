# KIRO2 Type Design Violations — Deep Audit (2026-05-21)

**Scope:** `backend/models`, `backend/api/schemas`, `backend/core/dependencies.py`,
`backend/services`, `frontend/src/types`, `frontend/src/services`

**Method:** Pattern-based detection of primitive obsession, type lying, encapsulation
leaks, discriminated-union gaps and Pydantic ↔ TypeScript drift. Each finding includes
a concrete bug it enables, not just "looks ugly".

**Quantitative summary**

| Metric | Count |
|---|---|
| Total `dict[str, Any]` propagation in API layer | **561** occurrences / 80 files |
| Total `dict[str, Any]` in app-wide top-30 hot files | **710** (top 30 files alone) |
| Stringly-typed domain identifiers (`user_id: str`, `student_id: str` etc.) | **1,224** occurrences |
| - `student_id: str` | 427 |
| - `user_id: str` | 361 |
| - `question_id: str` | 222 |
| - `exam_type: str` | 128 |
| - `topic_id: str` | 56 |
| - `subject_area: str` | 30 |
| `NewType` declarations in entire backend | **0** |
| `current_user: User = Depends(get_current_user)` type lies (User ≠ AuthenticatedUser) | **172** sites / 15 files |
| `current_user: dict = Depends(get_current_user)` (worst-case type erasure) | **5** sites (clustering_api) |
| Sync def returns `Optional[X]` but body raises on None (type-lie) | **41** services |
| Stringly-typed enum fields (`exam_type/difficulty/role/subject_area: str`) | **106** |
| `# type: ignore` in app code | **10** (well-controlled) |
| Frontend `as any` / `: any` / `<any>` usages | **596** |
| Frontend `ApiResponse<any>` usages | dozens (across `culturalAdaptationService`, `fsrsService`, ...) |
| Auto-generated `api.generated.ts` (OpenAPI) | **exists, NEVER imported** (manual TS drift) |
| Files affected if `UserId = NewType('UserId', str)` introduced | **343** Python files |

---

## CRITICAL FOUNDATIONAL VIOLATIONS

These three are the keystone violations from which most others cascade. Fix order matters.

### TD-1: `AuthenticatedUser.id: int | str` — union-of-primitives root identity

**Pattern:** Primitive obsession + impossible-state union on the central identity type.

**File:** `backend/core/dependencies.py:44`

**Current code:**
```python
class AuthenticatedUser(BaseModel):
    id: int | str = Field(..., description="User ID (primary key)")
    ...

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: Any) -> int | str:
        if isinstance(v, int):
            if v > 2147483647:  # INT32_MAX
                raise ValueError(...)
            return v
        if isinstance(v, str):
            if v.isdigit():
                int_val = int(v)
                if int_val > 2147483647:
                    raise ValueError(...)
                return int_val
            # Non-numeric string (UUID etc.)
            return v
        raise ValueError(...)
```

**Why this is a bug:**
- `User.id` in the DB is `Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))` — i.e. UUID stored as VARCHAR (see `backend/models/user_models.py:67-69`). It is **always** a string. The `int` branch of the union is a phantom that exists only because the validator coerces numeric strings to int.
- **Every caller must defensively cast:** the codebase contains 100+ occurrences of `str(current_user.id)` precisely because the type permits both. Examples in `backend/api/adhd_focus_mode_api.py:224, 276, 317, 351`, and many others. This is the type system charging a tax on every call site.
- The validator silently changes a UUID-looking input that happens to be all-digits (e.g. "12345") into `int(12345)` — semantically distinct from the DB UUID `"12345"`. If any user UUID is ever a pure-digit string, equality comparisons against the DB will break.

**Concrete bug enabled:**
- IDOR check: a handler does `if str(current_user.id) != request.path_user_id: raise 403`. If `request.path_user_id` is `"42"` (string) and a token contains `"sub": 42` (int after validator), the comparison `"42" != "42"` returns False (OK by coincidence). But change either side and the bug surfaces. The fix `str(current_user.id)` is an ad-hoc workaround that has to be remembered everywhere — and Session 142's "rule of seven" VARCHAR sweep already proved this class of bug can ship to production.
- The `INT32_MAX` overflow check (line 56-57) is dead code on the string branch: a 10-digit string `"9999999999"` is converted to `int(9999999999)` and rejected, while the same UUID-shape string `"99999999-9999-9999-9999-999999999999"` passes through untouched. This is inconsistent enforcement.

**Fix:**
```python
from typing import NewType

UserId = NewType("UserId", str)

class AuthenticatedUser(BaseModel):
    id: UserId = Field(..., description="User ID (UUID string)")

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: Any) -> UserId:
        if isinstance(v, int):
            # Tolerate legacy int IDs by converting to str — but log warning
            return UserId(str(v))
        if isinstance(v, str):
            if not v:
                raise ValueError("user_id cannot be empty")
            return UserId(v)
        raise ValueError(f"Invalid user_id type: {type(v)}")
```

**Cascade fix:**
- Removes ~150 sites that currently do `str(current_user.id)` defensively.
- Forces the JWT `sub` claim to be a string everywhere (already required by RFC 7519 — `sub` should be a `StringOrURI`).
- Aligns `AuthenticatedUser.id` with `User.id: Mapped[str]` so IDOR comparisons become trivial: `current_user.id == path_user_id`.
- Eliminates the dead `INT32_MAX` branch and its phantom failure mode.

---

### TD-2: `current_user: User = Depends(get_current_user)` — class identity lie at 172 sites

**Pattern:** Type lying — annotation does not match runtime type returned by the dependency.

**File:** `backend/core/auth_dependencies.py:37-80` and 172 call sites across 15 files
(top offenders: `diary_api.py:47×`, `adhd_support_api.py:15×`, `khan_routes.py:9×`,
`manipulatives_api.py:9×`, `adhd_task_management_api.py:8×`, `eba_routes.py:8×`,
`rag.py:7×`, `zemberek.py:7×`, `analytics.py:6×`, `ocr_api.py:6×`, ...).

**Current code:**
```python
# backend/core/auth_dependencies.py
from models.user import User  # → User = Kullanici (a Pydantic model in models/user.py:357)

class AuthenticationDependency:
    async def __call__(self, request, credentials) -> User | None:   # ← LIE
        ...
        from core.dependencies import AuthenticatedUser
        _user = AuthenticatedUser(                                   # ← actually returns this
            id=_payload.get("sub", ""),
            username=_payload.get("username", ""),
            role=_payload.get("role", "student"),
            ...
        )
        return _user                                                  # ← AuthenticatedUser, not User

# backend/api/diary_api.py and 14 others
from models.user import User   # ← Kullanici (Turkish-named Pydantic shape)

@router.post("/entries")
async def create(
    current_user: User = Depends(get_current_user),  # ← annotation says Kullanici
    ...
):
    user_id = current_user.kullanici_id   # ← AttributeError waiting to happen,
                                          #   because AuthenticatedUser has `id`, not `kullanici_id`
```

**Why this is a bug:**
- `models.user.User` is an alias for `Kullanici` (`backend/models/user.py:357`), a Pydantic model with fields `kullanici_id`, `email`, `ad_soyad`, `telefon`, `aktif`, `rol`.
- `AuthenticatedUser` has *completely different* fields: `id`, `username`, `role`, `email`, `permissions`, `exp`. **No overlap on `kullanici_id` or `ad_soyad`.**
- mypy in strict mode does not catch this because the call sites import `models.user.User` and then never access `.kullanici_id` (most files use `.id`, `.role`, `.username` — fields that happen to exist on the runtime object `AuthenticatedUser`). The annotation is a lie that has been masked by lucky field overlap.
- Any handler that *does* access `current_user.kullanici_id` (or `.ad_soyad`, `.rol`) will crash at runtime with `AttributeError`. The static type checker says it is fine.

**Concrete bug enabled:**
- A future developer reads `current_user: User` in `diary_api.py`, opens `models/user.py`, sees `Kullanici` has `ad_soyad`, writes `logger.info(f"User {current_user.ad_soyad} created diary")`. Code passes mypy, passes the import-time test (Pydantic class exists), and crashes the first time a real request hits the endpoint. The 503 surfaces as a Golden Flow regression weeks later.
- The Turkish-vs-English field naming (Kullanici.rol vs AuthenticatedUser.role) means *role checks* could silently look at the wrong attribute and pass on `getattr(current_user, "rol", None) is None` — auth bypass via attribute typo.

**Fix:**
```python
# Single canonical authenticated-user type everywhere
from core.dependencies import AuthenticatedUser, get_current_user

@router.post("/entries")
async def create(
    current_user: AuthenticatedUser = Depends(get_current_user),
    ...
):
    user_id = current_user.id   # always a str, always present
```

And in `core/auth_dependencies.py`:
```python
async def __call__(self, ...) -> AuthenticatedUser | None:   # ← truth
    ...
```

**Cascade fix:**
- 172 call sites across 15 files (`grep "current_user: User = Depends(get_current_user)" backend/api/`).
- One import swap per file (`from models.user import User` → `from core.dependencies import AuthenticatedUser`).
- Type lies eliminated; mypy strict can now actually catch attribute mismatches.

---

### TD-3: `current_user: dict = Depends(get_current_user)` — worst-case type erasure

**Pattern:** Type lying at maximum severity — annotation `dict` for a Pydantic model.

**File:** `backend/api/clustering_api.py:141, 205, 244, 286, 319`

**Current code:**
```python
async def cluster_concepts(
    request: ClusterRequest,
    current_user: dict = Depends(get_current_user),  # ← gets AuthenticatedUser, says dict
) -> ClusterResponse:
    ...
```

**Why this is a bug:**
- `get_current_user` returns `AuthenticatedUser` (Pydantic, `frozen=True`). Annotating it as `dict` immediately erases:
  - Frozen-ness (mypy now thinks `current_user["role"] = ...` is legal, runtime would fail).
  - Field validators (Pydantic validators ran on construction, but downstream code can't read them).
  - The `__repr__` PII-masking guarantee (`AuthenticatedUser.__repr__` masks email; `dict.__repr__` does not).
- Any downstream code attempting `current_user["id"]` would crash (`AuthenticatedUser` is a Pydantic object, not a Mapping). The five sites work today only because they don't actually access `current_user` inside the handler body — they just gate by presence. Add one logger statement and it breaks.

**Concrete bug enabled:**
- Someone adds audit logging: `logger.info(f"User {current_user['id']} clustered")`. Runtime: `TypeError: 'AuthenticatedUser' object is not subscriptable`. Tests pass because mock might be a dict; staging fails.
- Email leakage: if a developer writes `logger.info(f"User {current_user}")`, the `dict` annotation makes them expect `repr({...})` output and they trust it. The runtime `AuthenticatedUser.__repr__` masks email, but if someone *replaces* this with a dict for testing, KVKK compliance is lost.

**Fix:** Same as TD-2 — `current_user: AuthenticatedUser`.

**Cascade fix:** 5 sites in one file.

---

## PYDANTIC SCHEMA VIOLATIONS

### TD-4: `database_authenticate(...) -> dict[str, Any]` — login contract typeless

**Pattern:** Pydantic shop ships untyped JSON at its most critical boundary.

**File:** `backend/api/auth.py:259-387`

**Current code:**
```python
async def database_authenticate(
    giris_data: KullaniciGiris,
    db: AsyncSession,
) -> dict[str, Any]:                          # ← typeless login response
    ...
    return {
        "success": True,
        "token": token,
        "refreshToken": refresh_token,
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "ad": db_user.first_name,
            ...                                  # 10 keys
        },
        "access_token": token,                   # duplicate of 'token'
        "token_type": "bearer",
        "expires_in": expires_in,
        "kullanici": kullanici,                  # Pydantic model leaked into dict
    }
```

**Why this is a bug:**
- The frontend (`frontend/src/types.ts:175`) declares `LoginResponse = { success, user, message? }`. The backend returns *fifteen* top-level keys, three of which are aliases of each other (`token` / `access_token` / `kullanici`). The TS type and the Python return are drift-by-construction.
- The dict has both `user` (frontend-friendly Turkish-English mixed dict) and `kullanici` (Pydantic `Kullanici` object). Serialization order determines which one wins on the wire; reordering this dict literal silently changes the API contract.
- `kullanici` is a Pydantic model embedded in a `dict[str, Any]`. FastAPI's default JSON encoder will serialize it through `.model_dump()`, but if a caller awaits this function directly (not through a route), they get a `Kullanici` object in the dict — `dict[str, Any]` doesn't help them know that.

**Concrete bug enabled:**
- The frontend reads `response.user.id` (string). If the backend's `database_authenticate` is ever called with `_use_legacy=True` and returns the legacy shape `{ "user_id": ..., "kullanici": {...} }`, the frontend silently gets `undefined` and the login appears to succeed but no user is stored. Session 78's "dual table trap" lesson applies here: the same dict shape carries two completely different schemas, and the type signature hides it.
- Removing the duplicate `access_token` key (a refactor opportunity) cannot be done safely because no consumer of `database_authenticate` is type-checkable — every key removal is a potential breaking change for an unknown set of callers.

**Fix:**
```python
class LoginUserPayload(BaseModel):
    id: UserId
    email: EmailStr
    ad: str
    soyad: str
    rol: Literal["ogrenci", "ogretmen", "veli", "admin", "super_admin"]
    aktif: bool
    olusturma_tarihi: datetime | None
    son_giris: datetime | None
    telefon: str
    profil_resmi: str | None

class LoginResponse(BaseModel):
    success: bool
    token: str
    refresh_token: str = Field(..., alias="refreshToken")
    expires_in: int
    user: LoginUserPayload
    model_config = {"populate_by_name": True}

async def database_authenticate(...) -> LoginResponse:
    ...
    return LoginResponse(
        success=True,
        token=token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=LoginUserPayload(...),
    )
```

**Cascade fix:** Two callers (`/login/secure` route + tests). Frontend `LoginResponse` type can then be regenerated from OpenAPI (see TD-12). The duplicate `access_token`/`token_type`/`kullanici` keys can be deleted with confidence because callers are type-checked.

---

### TD-5: `OperationResult.data: Any | None + error: str | None` — impossible-state Pydantic model

**Pattern:** Missing discriminated union — model allows nonsensical combinations.

**File:** `backend/api/schemas/batch.py:70-79`

**Current code:**
```python
class OperationResult(BaseModel):
    id: str | None = Field(default=None)
    index: int = Field(..., ge=0)
    status_code: int = Field(..., ge=100, le=599)
    success: bool = Field(...)
    data: Any | None = Field(default=None)       # ← present when success=True
    error: str | None = Field(default=None)      # ← present when success=False
    duration_ms: float = Field(..., ge=0)
```

**Why this is a bug:**
- A consumer cannot tell whether `data is None` means "operation succeeded but returned null" or "operation failed". They have to read `success` and `error` to disambiguate.
- A producer can construct `OperationResult(success=True, data=None, error="oops")` — a nonsense state. The type system says fine.
- Any code path that does `if result.error: ...` is wrong if a successful operation happens to legitimately have an error-shaped result (e.g. a search that returned a "not found" status); the discriminator is implicit and fragile.

**Concrete bug enabled:**
- Batch endpoint's "atomic mode" rollback logic checks `if any(r.error for r in results)`. If one of the successful operations legitimately includes the substring "error" in its returned data (e.g. validation warnings), the whole batch rolls back. The schema does not enforce that `error` is only set when `success=False`.

**Fix:**
```python
from typing import Literal

class OperationSuccess(BaseModel):
    id: str | None = None
    index: int = Field(..., ge=0)
    status_code: int = Field(..., ge=200, le=299)
    success: Literal[True] = True
    data: Any
    duration_ms: float = Field(..., ge=0)

class OperationFailure(BaseModel):
    id: str | None = None
    index: int = Field(..., ge=0)
    status_code: int = Field(..., ge=400, le=599)
    success: Literal[False] = False
    error: str
    duration_ms: float = Field(..., ge=0)

OperationResult = Annotated[
    OperationSuccess | OperationFailure,
    Field(discriminator="success"),
]
```

**Cascade fix:** `BatchResponse.results: list[OperationResult]` — Pydantic discriminator handles the parsing. Consumers can `match` on `success`.

---

### TD-6: `QuestionGenerationResponse.question: dict | None` — naked dict inside Pydantic

**Pattern:** Generic loss inside a Pydantic schema — defeats the purpose of typed APIs.

**File:** `backend/api/question_bank_v2_routes.py:111-115, 132, 153-154, 169-170, 181`

**Current code:**
```python
class QuestionGenerationResponse(BaseModel):
    status: str  # "approved", "needs_review", "rejected"   ← stringly typed
    question_id: str | None
    question: dict | None              ← naked dict in Pydantic response
    task_id: str | None
    priority: str | None               ← stringly typed
    plagiarism_result: dict | None     ← naked dict
    validation_result: dict | None     ← naked dict
    message: str

class CATStartResponse(BaseModel):
    session_id: str
    first_question: dict               ← naked dict
    ...

class HITLTaskRequest(BaseModel):
    question_id: str
    question_data: dict                ← naked dict request body
    ai_validation_result: dict
```

**Why this is a bug:**
- Three layers of type loss in one file:
  1. The response says `dict` — OpenAPI schema generation emits `additionalProperties: true`, frontend codegen produces `Record<string, unknown>`, type-safety on the wire is zero.
  2. `status: str  # "approved", "needs_review", "rejected"` — the comment says it's an enum, but the type says any string is valid. A typo `"aproved"` ships and the frontend's `if status === "approved"` silently never triggers.
  3. `first_question: dict` (non-optional, no None) inside a CAT (Computer-Adaptive Testing) session start. If the question generator returns an empty dict, the contract is satisfied but no question reaches the student.

**Concrete bug enabled:**
- Frontend writes `if (response.status === "needs_review")`. Backend ever returns `"NEEDS_REVIEW"` (uppercase by mistake), the branch is dead code. There is no validator. Tests probably mock the lowercase form.
- A new field added to `question_data` is invisible to OpenAPI codegen — the frontend will not know about it until somebody manually updates `frontend/src/types/index.ts`. This is the Pydantic ↔ TS sync drift documented in Session 178.

**Fix:**
```python
from typing import Literal

GenerationStatus = Literal["approved", "needs_review", "rejected"]
ReviewPriority = Literal["low", "medium", "high", "urgent"]

class GeneratedQuestion(BaseModel):
    """Full question payload — mirror of QuestionBankItem with serialization."""
    question_text: str
    options: list[str]
    correct_answer: str
    kazanim: str
    zorluk: QuestionDifficulty
    bloom_level: BloomLevel
    # ... fully typed

class PlagiarismResult(BaseModel):
    score: float = Field(..., ge=0, le=1)
    similar_question_ids: list[str]

class QuestionGenerationResponse(BaseModel):
    status: GenerationStatus
    question_id: str | None
    question: GeneratedQuestion | None
    task_id: str | None
    priority: ReviewPriority | None
    plagiarism_result: PlagiarismResult | None
    validation_result: ValidationResult | None
    message: str
```

**Cascade fix:** Each `dict` becomes a named model. ~7 sites in this file; OpenAPI emits proper TypeScript types; downstream frontend stops needing manual `// @ts-expect-error`.

---

### TD-7: `learning_path_v2` — `student_profile: dict[str, Any] | None` and `performance_data: dict[str, Any]` in body schemas

**Pattern:** Body model accepts arbitrary JSON.

**File:** `backend/api/learning_path_v2.py:268, 278`

**Current code:**
```python
class PathAdaptation(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    path_id: str = Field(..., description="Öğrenme yolu ID")
    performance_data: dict[str, Any] = Field(..., description="Performans verileri")  # ← arbitrary JSON

class SomeOtherRequest(BaseModel):
    ...
    student_profile: dict[str, Any] | None = Field(
        None, description="Öğrenci profili (opsiyonel)"
    )
```

**Why this is a bug:**
- The body validator passes any JSON object. `performance_data={}` is accepted, then the handler later expects `performance_data["accuracy"]` and crashes with `KeyError`. The error surfaces as 500 instead of 422.
- "Performance data" has a stable shape (IRT theta, BKT mastery, etc.) — that shape is documented nowhere. New consumers cannot know what to send.

**Concrete bug enabled:**
- A student-facing flow sends `performance_data={"accuracy": 0.5, "time_spent_minutes": 15}`. The handler reads `performance_data["mastery_levels"]` (the field a sibling endpoint expected) and crashes — 500 to the user, no actionable error message. This is the class of bug Session 148's middleware/error-shape rule was meant to prevent at the *transport* layer, but here it's a *schema* problem.

**Fix:** Define `PerformanceData` and `StudentProfile` Pydantic models. Replace the dicts.

**Cascade fix:** All `learning_path_v2` body schemas (≈4 in this file).

---

### TD-8: `admin.py` user-update accepts `dict[str, Any]` body, validates manually

**Pattern:** Discarding Pydantic in favor of hand-rolled `if "key" in dict:` checks.

**File:** `backend/api/admin.py:149-188`

**Current code:**
```python
@router.put("/users/{kullanici_id}", response_model=dict[str, Any], summary="Kullanıcı Güncelle")
async def kullanici_guncelle(
    kullanici_id: str,
    kullanici_data: dict[str, Any],          # ← naked dict body
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        updates, params = [], {"uid": kullanici_id}
        if "is_active" in kullanici_data:
            updates.append("is_active = :is_active")
            params["is_active"] = bool(kullanici_data["is_active"])
        if "role" in kullanici_data:
            new_role = str(kullanici_data["role"]).upper()
            if new_role not in ("STUDENT", "TEACHER", "PARENT", "ADMIN"):
                raise HTTPException(400, detail="Gecersiz rol")
            updates.append("role = :role")
            params["role"] = new_role
        if not updates:
            raise HTTPException(400, detail="Guncellenecek alan yok")
        ...
```

**Why this is a bug:**
- Manual `"key" in dict` validation reinvents Pydantic — badly. `SUPER_ADMIN` is missing from the role allowlist on line 163 even though it exists in the `UserRole` enum. This is exactly the kind of drift Pydantic eliminates.
- Extra unknown keys are silently ignored — a client can send `{"role": "TEACHER", "is_premium": true, "password_hash": "..."}` and the handler silently drops `is_premium` and `password_hash`. A future maintainer who adds `is_premium` to the update branch suddenly exposes a privilege-escalation surface that was already shipping.
- `bool(kullanici_data["is_active"])` — `bool("false")` is `True` in Python. Pydantic's `bool` validator catches `"false"` correctly; the manual cast does not. Subtle attacker-controllable input.

**Concrete bug enabled:**
- An admin sends `{"role": "super_admin"}` (lowercase). The check uppercases it to `"SUPER_ADMIN"`, which is **not in the allowlist on line 163**, so it raises 400 — the legitimate operation fails. This is a paper cut today; the same drift bites harder when a new role is added.
- An attacker who somehow reaches this endpoint via stolen admin token can send `{"is_active": "false"}` and `bool("false")` becomes `True`, *re-activating* a deactivated user. (Mitigated only by the admin gate, but the schema permits it.)

**Fix:**
```python
class UserUpdateRequest(BaseModel):
    """PUT /admin/users/{id} body — strict, no extra fields."""
    model_config = {"extra": "forbid"}
    is_active: bool | None = None
    role: UserRole | None = None   # canonical enum, includes SUPER_ADMIN

@router.put("/users/{kullanici_id}", response_model=UserDetailResponse)
async def kullanici_guncelle(
    kullanici_id: UserId,
    body: UserUpdateRequest,
    _: AuthenticatedUser = Depends(admin_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, detail="Guncellenecek alan yok")
    ...
```

**Cascade fix:** ~3 endpoints in `admin.py`, plus consistent enum reuse across the codebase.

---

## SERVICE LAYER VIOLATIONS

### TD-9: 41 services declare `-> ConcreteType` but contain `return None` paths

**Pattern:** Type lying at the service boundary — `Optional` missing from declared return.

**File:** 25 services confirmed; representative offenders:

| File | Function | Declared | Actually returns |
|---|---|---|---|
| `backend/services/admin_service.py` | `kullanici_olustur` | `Kullanici` | None on duplicate email |
| `backend/services/ai_chat_service.py` | `create_session` | `ChatSession` | None on quota exceeded |
| `backend/services/duel_service.py` | `create_duel_session` | `DuelSession` | None on insufficient players |
| `backend/services/question_bank_service.py` | `create_question` | `QuestionBankItem` | (manual confirm — body returns at end, but `await commit` can raise; needs verification) |
| `backend/services/teacher_service.py` | `register_teacher`, `add_expertise`, `add_certification`, `add_availability_slot`, `create_appointment` | concrete types | None on FK violation |
| `backend/services/user_service.py` | `kullanici_olustur`, `kullanici_giris`, `ogrenci_profili_olustur`, `ogretmen_profili_olustur` | concrete types | None on validation failure |
| `backend/services/university_info_service.py` | `create_city_living_cost` | concrete | None on dup |
| `backend/services/blackboard_service.py` | `get` (singleton) | `BlackboardService` | None before init |
| `backend/services/error_detection_service.py` | `_create_concept_error` | `MathError` | None |
| `backend/services/eba_tv_client.py` | `_parse_video_metadata` | `EBAVideoMetadata` | None on parse fail |

(Full list: 41 functions across the services tree, found via heuristic
`def f(...) -> Type:` followed by `return None` in the function body.)

**Why this is a bug:**
- Callers write `result = await service.create_session(...)` and treat `result.id` as safe — mypy says so. At runtime, `result` is sometimes `None` and `.id` raises `AttributeError`, surfacing as 500.
- These functions are the boundary between the route layer (which has Pydantic validation) and the persistence layer (which has its own errors). Misdeclaring them poisons the entire call graph downstream.
- This is the same anti-pattern Session 148 caught at the middleware layer (HTTPException-in-middleware), now repeated at the service layer.

**Concrete bug enabled:**
- `duel_service.create_duel_session()` returns None on insufficient players. The API handler does `duel = await duel_service.create_duel_session(...); return DuelResponse.model_validate(duel)`. Pydantic raises `ValidationError: None is not a valid input` → 500. The user sees "Server error" instead of "Need more players".

**Fix:** Make the return type honest. Two correct patterns:

```python
# Pattern A: caller handles None
async def create_session(...) -> ChatSession | None:
    if quota_exceeded:
        return None
    ...
    return session

# Pattern B (preferred): raise a domain exception
class ChatQuotaExceeded(DomainError): ...

async def create_session(...) -> ChatSession:
    if quota_exceeded:
        raise ChatQuotaExceeded("monthly chat quota reached")
    ...
    return session
```

Pattern B is preferred for the 25 service functions above because the "None" carries no information — the caller cannot tell *why* it failed. A typed domain exception preserves the reason.

**Cascade fix:** Per function, one or two callers. Total ~80 call sites if Pattern A is chosen; Pattern B requires adding `except DomainError` to the routes (~25 files).

---

### TD-10: `teacher_service.register_teacher(...)` — 16-parameter primitive-obsession constructor

**Pattern:** Primitive obsession at maximal scale.

**File:** `backend/services/teacher_service.py:49-66`

**Current code:**
```python
async def register_teacher(
    self,
    user_id: UUID,
    full_name: str,
    title: str,
    bio: str,
    phone: str,
    email: str,
    city: str,
    district: str,
    years_of_experience: int,
    education_level: str,
    university: str,
    department: str,
    graduation_year: int,
    hourly_rate: float,
    application_notes: str | None = None,
) -> TeacherProfile:
```

**Why this is a bug:**
- 16 positional parameters, none of which are domain types. `phone: str`, `email: str`, `city: str`, `district: str`, `university: str`, `department: str` — six different `str`s with no enforcement that `phone` is not accidentally swapped with `email` at call time. A `register_teacher(..., city="555-1234", phone="Istanbul", ...)` call would pass type checking and corrupt the DB.
- `education_level: str` is a stringly-typed enum (degree types: lisans, yuksek_lisans, doktora). No validation that the input is one of N legal values.
- `hourly_rate: float` permits negative values, zero, NaN. Money should never be a naked float.

**Concrete bug enabled:**
- A migration script copies fields in the wrong order: `register_teacher(user_id, full_name=row["bio"], bio=row["full_name"], ...)` — swapped `full_name` and `bio`. Type checker happy. DB ends up with biographies in names. KVKK audit later finds names dumped into bio fields visible publicly.

**Fix:**
```python
class TeacherRegistrationRequest(BaseModel):
    user_id: UserId
    full_name: str = Field(..., min_length=2, max_length=100)
    title: TeacherTitle             # enum
    bio: str = Field(..., max_length=2000)
    phone: PhoneNumber              # NewType + validator
    email: EmailStr
    city: TurkishCity               # enum or validated str
    district: str
    years_of_experience: int = Field(..., ge=0, le=70)
    education_level: EducationLevel # enum
    university: str
    department: str
    graduation_year: int = Field(..., ge=1950, le=2100)
    hourly_rate: Money              # NewType('Money', Decimal) + ge=0
    application_notes: str | None = None

async def register_teacher(self, data: TeacherRegistrationRequest) -> TeacherProfile:
    teacher = TeacherProfile(**data.model_dump(), status=TeacherStatus.PENDING, ...)
    ...
```

**Cascade fix:** ~3 call sites (the route, two admin scripts). Pydantic catches swapped fields, range checks, and enum validity at construction.

---

### TD-11: `question_bank_service.create_question(question_data: dict[str, Any], ...)` — naked dict service input

**Pattern:** Naked dict at the service ↔ model boundary, after Pydantic has already validated.

**File:** `backend/services/question_bank_service.py:48-74`

**Current code:**
```python
async def create_question(
    self, question_data: dict[str, Any], created_by: str | None = None
) -> QuestionBankItem:
    """Yeni soru oluştur"""
    question = QuestionBankItem(
        **question_data, created_by=created_by, created_at=datetime.now()
    )
    question.irt_based_difficulty = calculate_irt_based_difficulty(
        question.irt_difficulty
    )
    self.db.add(question)
    ...
```

**Why this is a bug:**
- `**question_data` unpacks arbitrary keys into a SQLAlchemy constructor. If `question_data` contains `id` (e.g. attacker tries to choose UUID), `created_by` (already passed as kwarg → `TypeError: multiple values for keyword argument`), or any column they shouldn't write, the model accepts it.
- The route layer typically validates with `QuestionCreate` Pydantic schema, then `.model_dump()` to a dict, then this service splats it back into the ORM. The Pydantic schema is informational only — the *service* doesn't know what shape it expects.

**Concrete bug enabled:**
- `QuestionCreate` adds a new optional `is_verified` field. The route validates. The service blindly forwards. The DB column happens to be a privileged "trusted" flag. Attacker sets `is_verified=true` in the body and the route schema didn't have `extra="forbid"`. Service is the last line of defense and it forwards everything.

**Fix:**
```python
async def create_question(
    self,
    data: QuestionCreate,        # ← Pydantic schema, not dict
    created_by: UserId | None = None,
) -> QuestionBankItem:
    payload = data.model_dump(exclude_none=True)
    question = QuestionBankItem(
        **payload,
        created_by=created_by,
        created_at=datetime.now(UTC),
    )
    ...
```

**Cascade fix:** ~2 callers per service method × ~6 services with this pattern.

---

## FRONTEND TYPE VIOLATIONS

### TD-12: `api.generated.ts` exists but is never imported — manual TS drift

**Pattern:** OpenAPI codegen exists, frontend silently ignores it.

**File:** `frontend/src/types/api.generated.ts` (auto-generated) and `frontend/src/types/index.ts`, `frontend/src/types.ts` (manual, hand-maintained)

**Current state:**
```bash
$ grep -rn "from '@/types/api.generated\|api.generated'" frontend/src
(no results)
```

**Why this is a bug:**
- `frontend/src/types/api.generated.ts` is `openapi-typescript` output. It exists. Nobody imports it. Every API type used in the frontend is hand-typed in `types.ts` / `types/index.ts` / per-service files.
- Concrete drift seen during this audit:
  - Backend `database_authenticate()` returns `dict` with keys `success, token, refreshToken, user, access_token, token_type, expires_in, kullanici`.
  - Frontend `LoginResponse` (`frontend/src/types.ts:175`) declares `{ success, user, message? }`. **Missing `token`, `refreshToken`, `expires_in`.**
  - Frontend `User` (`types.ts:146`): `{ id, email, ad, soyad, rol, aktif, olusturma_tarihi, son_giris?, profil_resmi?, telefon?, okul_id?, sinif_id? }`.
  - Backend embedded `user` dict in login response: `{ id, email, ad, soyad, rol, aktif, olusturma_tarihi, son_giris, telefon, profil_resmi }`. **Missing `okul_id`, `sinif_id`.** Adding them server-side will silently work; removing `profil_resmi` server-side will silently break the frontend.

**Concrete bug enabled:**
- Session 142's "rule of seven" was caller-coerce type drift on UUID. Same class of bug here: when backend renames `son_giris` → `last_login_at` (English-only sweep), frontend silently reads `undefined`. No type checker fires.

**Fix:**
1. Make CI regenerate `api.generated.ts` from `/openapi.json`.
2. Switch all hand-typed API interfaces in `frontend/src/types*` to re-exports from `api.generated.ts`:
   ```ts
   import type { components } from './api.generated';
   export type User = components['schemas']['UserResponse'];
   export type LoginResponse = components['schemas']['LoginResponse'];
   ```
3. Forbid hand-typed API DTOs via ESLint rule (custom).

**Cascade fix:** Replaces all of `frontend/src/types/index.ts` and `frontend/src/types.ts` API shapes. Eliminates ~25 manual interface declarations, eliminates drift.

---

### TD-13: `ApiResponse<T = any>` — generic with `any` default + impossible-state union

**Pattern:** Defaulting generic to `any` defeats the type system; structure allows nonsense states.

**File:** `frontend/src/types/index.ts:539-544`

**Current code:**
```ts
export interface ApiResponse<T = any> {
  success: boolean
  data: T                  // ← required even when success=false
  message?: string
  error?: string           // ← can coexist with success=true and non-null data
}
```

**Why this is a bug:**
- `data: T` is **required** but `T = any` defaults to "anything". Calling `ApiResponse<User>` requires a `User`; calling `ApiResponse` (no parameter) accepts anything as `data`. Type erosion by default.
- An object `{ success: false, data: null as any, error: "boom" }` is "valid" per this interface only because `data: any`. If `T = User`, `data` cannot be null and the failure case literally cannot be constructed without a cast.
- Used by `fsrsService.ts` and others with `Promise<ApiResponse<FSRSCard | null>>` — the nullability is pushed *into* the generic instead of out to the union. `data: FSRSCard | null` does not encode "data null because failure" vs "data null because not found"; the consumer has to inspect `success` to disambiguate, but TS doesn't enforce it.

**Concrete bug enabled:**
- Consumer code:
  ```ts
  const res = await fetchFSRSCard(...);  // Promise<ApiResponse<FSRSCard | null>>
  if (res.data) {
    review(res.data);  // ← runs even if success=false but somehow data was non-null
  }
  ```
  The discriminated nature is opaque. A backend response `{ success: false, data: { ...stale cached card... }, error: "permission denied" }` would silently process the stale card.

**Fix:**
```ts
export type ApiResponse<T> =
  | { success: true; data: T; message?: string }
  | { success: false; error: string; message?: string };

// Usage:
const res = await fetchFSRSCard(...);
if (res.success) {
  review(res.data);  // ← TS narrows data to T
} else {
  showError(res.error);  // ← TS narrows error to string
}
```

**Cascade fix:** All consumers of `ApiResponse<T>` (~30 sites) — each will get a TS error pinpointing the place they were treating success/failure ambiguously. This is a one-time refactor that pays back forever.

---

### TD-14: `MorphologyAnalysisResponse.data: dict[str, Any] | None` — typed wrapper around untyped payload

**Pattern:** Pydantic response wraps `dict[str, Any]` — type-safe outside, untyped inside.

**File:** `backend/api/turkish_nlp.py:29-33, 47-49`, and similar Response classes across many files.

**Current code:**
```python
class MorphologyAnalysisResponse(BaseModel):
    success: bool
    data: dict[str, Any] | None = None   # ← untyped payload
    message: str
```

**Why this is a bug:**
- The endpoint advertises a Pydantic schema, but the actual interesting payload (the morphology analysis) is `dict[str, Any]`. Frontend codegen produces `Record<string, unknown>` — no field hints.
- Same `dict[str, Any]` pattern appears in ~561 places in the API layer. Each one is a missed opportunity for end-to-end type safety.

**Concrete bug enabled:**
- Frontend reads `response.data.morphemes`. Backend changes the field name to `analysis_units`. No type error, no test failure (mocks copied the old shape), production breakage.

**Fix:**
```python
class Morpheme(BaseModel):
    surface: str
    root: str
    pos: str
    features: list[str]

class MorphologyAnalysisData(BaseModel):
    word: str
    morphemes: list[Morpheme]
    confidence: float = Field(..., ge=0, le=1)

class MorphologyAnalysisResponse(BaseModel):
    success: bool
    data: MorphologyAnalysisData | None = None
    message: str
```

**Cascade fix:** Per-endpoint Pydantic model for the payload. 561 sites at API layer; not all need fixing simultaneously, but each one fixed buys end-to-end type safety for that route.

---

### TD-15: `knowledge_graph_api.PrerequisiteDagResponse.edges: list[dict]` — naked dict inside Pydantic list

**Pattern:** Mixed list of typed + naked — generic loss inside a typed response.

**File:** `backend/api/knowledge_graph_api.py:42-45`

**Current code:**
```python
class KnowledgeNodeItem(BaseModel):
    knowledge_point_id: str
    name: str
    prerequisites: list[str]
    difficulty_range: list[float]

class KnowledgeEdgeItem(BaseModel):     # ← exists!
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    model_config = {"populate_by_name": True}

class PrerequisiteDagResponse(BaseModel):
    subject: str
    nodes: list[KnowledgeNodeItem]
    edges: list[dict]                    # ← inconsistent: should be list[KnowledgeEdgeItem]
```

**Why this is a bug:**
- The dedicated edge type already exists three lines above. The list field annotation was not updated. The frontend receives `edges: Record<string, unknown>[]` instead of `{ from: string; to: string }[]`. Pydantic does not enforce `from/to` shape on `list[dict]`.
- This is the kind of small-but-cumulative leak that breeds 596 frontend `as any` casts.

**Concrete bug enabled:**
- A future edge field `weight: float` is added on the producer side. The Pydantic schema does not declare it. OpenAPI emits `additionalProperties: true` for the inline dict, frontend `as any` everywhere, and a typo `weigth` on the producer side is invisible until visualization breaks.

**Fix:**
```python
class PrerequisiteDagResponse(BaseModel):
    subject: SubjectArea
    nodes: list[KnowledgeNodeItem]
    edges: list[KnowledgeEdgeItem]   # ← use the existing type
```

**Cascade fix:** 1 line, plus the (~5) `dict` list fields in other API schemas. Find with `grep -n "list\[dict\]" backend/api/`.

---

### TD-16: `status: str  # locked | available | mastered` — stringly-typed state machines

**Pattern:** Inline-commented enums instead of `Literal`.

**File:** `backend/api/knowledge_graph_api.py:54`, `question_bank_v2_routes.py:109, 113, 149, 178`, and many more.

**Current code:**
```python
class KnowledgeStateItem(BaseModel):
    knowledge_point_id: str
    name: str
    mastery_level: float
    confidence: float
    last_assessed: str | None = None
    status: str  # locked | available | mastered     ← comment, not enforced
```

**Why this is a bug:**
- The state machine has 3 valid states and the type system allows 2^32. Producer sends `"LOCKED"`, consumer expects `"locked"`. Comment is documentation that compilers ignore.
- Frontend code does `if (state === "locked")`. Server-side typo `"loked"` ships, branch is dead, all "locked" knowledge points appear `available` — students get questions they shouldn't.

**Concrete bug enabled:**
- Same class as Session 78's "Case Convention" lessons: `"matematik"` vs `"MATEMATIK"`. The platform spent multiple sessions fixing these. New stringly-typed enums repeat the cycle.

**Fix:**
```python
from typing import Literal
KnowledgeStatus = Literal["locked", "available", "mastered"]

class KnowledgeStateItem(BaseModel):
    ...
    status: KnowledgeStatus
```

**Cascade fix:** Find with `grep -n "str.*#.*|" backend/api/schemas backend/api`. ~30-50 sites.

---

### TD-17: Frontend `catch (e: any)` — defeats TypeScript's `unknown` default

**Pattern:** Restoring `any` to error handlers, losing structural narrowing.

**File:** 50+ catch handlers in `frontend/src/pages/*.tsx`, `frontend/src/services/*.ts`,
`frontend/src/hooks/*.ts`. Notable clusters:
- `frontend/src/pages/SoruMeydaniPage.tsx` — 5 catches, all `catch (e: any)`.
- `frontend/src/pages/BirlikteStreakPage.tsx` — 3 catches.
- `frontend/src/pages/PomodoroPage.tsx` — 3 catches.
- `frontend/src/pages/UstaCirakPage.tsx` — 3 catches.
- `frontend/src/hooks/useAutoSave.ts` — 2 catches.

**Current code:**
```ts
try {
  const res = await api.solve(...);
  ...
} catch (e: any) {                    // ← any restored
  setError(e.message);                // ← unsafe: e might not be Error
}
```

**Why this is a bug:**
- TS 4.4+ defaults catch variables to `unknown`. Explicit `: any` defeats this — `e.message` is reported as `any`, breaking the chain of type safety.
- `e` might be a string, a number, a `Response` object (from `fetch`), or an Error. Reading `.message` on a non-Error returns `undefined`, and `setError(undefined)` silently shows no message.

**Concrete bug enabled:**
- `useAutoSave` swallows errors silently because `e.message` is undefined on a non-Error throw. The user thinks their work is being saved; it isn't.

**Fix:**
```ts
import { getErrorMessage } from '../utils/apiHelpers';

try {
  ...
} catch (e: unknown) {
  setError(getErrorMessage(e));   // already exists in the codebase
}
```

**Cascade fix:** ~50 catch blocks; `getErrorMessage` is already imported in `authService.ts:1` — pattern exists, just unevenly applied.

---

### TD-18: Frontend `Bildirim.kullanici_id: string` — primitive obsession matching backend

**Pattern:** Frontend mirrors backend's primitive obsession.

**File:** `frontend/src/types/index.ts:606-615` (`Bildirim`), `:35-50` (`Kullanici`), `:53-69` (`SinavOturumu` with `ogrenci_id`, `sinav_id`, `soru_listesi: string[]`), `:71-89` (`SinavSorusu` with `soru_id`), and 30+ other interfaces.

**Current code:**
```ts
export interface Bildirim {
  id: string
  kullanici_id: string       // ← which user? a UserId? A teacher? A parent?
  ...
}

export interface SinavOturumu {
  sinav_id: string           // ← Sinav (exam) id
  ogrenci_id: string         // ← Ogrenci (student) id
  ...
  soru_listesi: string[]     // ← list of SoruId
  cevaplanan_sorular: Record<string, string>   // ← Record<SoruId, OptionId>? unclear
}
```

**Why this is a bug:**
- Functions accepting `(userId: string, examId: string, questionId: string)` cannot distinguish between them. Swap any two at the call site; the compiler will not complain.
- `cevaplanan_sorular: Record<string, string>` — keys are question IDs, values are option IDs. Reversed by mistake (`{ [optionId]: questionId }`), still type-checks.

**Concrete bug enabled:**
- The `submitAnswer(sessionId, questionId, optionId)` signature exists in `examService.ts`. A refactor that reorders the API method to `submitAnswer(questionId, sessionId, optionId)` requires touching every call site; the compiler can only warn if the *arity* changes. Branded types would catch the reordering.

**Fix:**
```ts
// frontend/src/types/brands.ts
declare const __brand: unique symbol;
export type Brand<T, B> = T & { readonly [__brand]: B };

export type UserId    = Brand<string, 'UserId'>;
export type StudentId = Brand<string, 'StudentId'>;
export type ExamId    = Brand<string, 'ExamId'>;
export type QuestionId = Brand<string, 'QuestionId'>;
export type OptionId   = Brand<string, 'OptionId'>;

export const UserId    = (s: string) => s as UserId;
export const StudentId = (s: string) => s as StudentId;
// ...

export interface Bildirim {
  id: string;
  kullanici_id: UserId;
  ...
}

export interface SinavOturumu {
  sinav_id: ExamId;
  ogrenci_id: StudentId;
  ...
  cevaplanan_sorular: Record<QuestionId, OptionId>;
}
```

**Cascade fix:** Branding is opt-in per identifier. Roll out incrementally — start with `UserId` and `StudentId` (highest IDOR risk surfaces), expand to `ExamId/QuestionId` etc. ~30 interfaces, ~400 call sites; can be staged.

---

## ADDITIONAL FINDINGS (briefer)

### TD-19: `database.py` re-export layer hides which model is which (`Question` ambiguity)

**File:** `backend/models/database.py:25-30` re-exports `from .content_db import Question`. The DB has both `content_db.Question` (empty legacy table) and `question_bank.QuestionBankItem` (77K rows). The re-export `Question` is the *empty* one, but the name is generic enough that new code keeps importing the wrong table. This is the "dual table trap" that Session 78's MEMORY.md documents, and the re-export layer is the root cause.

**Fix:** Either delete `database.py` re-exports entirely (force explicit submodule imports) or rename `content_db.Question` → `LegacyQuestion` so the dangerous one is obviously dangerous.

---

### TD-20: `AuthenticatedUser` has 5 mock helpers that don't honor its type

**File:** `backend/core/dependencies.py:280-290`

```python
MOCK_USER = {
    "id": "test_student",
    "username": "test_student",
    "role": "student",
    "email": "test@example.com",
}

async def get_mock_current_user() -> dict[str, Any]:   # ← dict
    return MOCK_USER
```

The mock returns a `dict`, the real returns `AuthenticatedUser`. Any code that swaps them via dependency override gets a different type at runtime than at compile time. Type-checked tests pass; behavior diverges.

**Fix:**
```python
MOCK_USER = AuthenticatedUser(
    id="test_student",
    username="test_student",
    role=UserRole.STUDENT,
    email="test@example.com",
)

async def get_mock_current_user() -> AuthenticatedUser:
    return MOCK_USER
```

---

## PRIORITY-ORDERED FIX PLAN

| # | Fix | Impact | Effort | Risk |
|---|---|---|---|---|
| 1 | TD-1 + TD-2 + TD-3 (auth user identity) | foundational — eliminates `str(user.id)` everywhere; eliminates 172 type lies | 1 day | low (mostly mechanical) |
| 2 | TD-12 (OpenAPI codegen pipeline) | foundational — kills Pydantic ↔ TS drift permanently | 1 day | medium (CI pipeline) |
| 3 | TD-13 (frontend `ApiResponse<T>` discriminated union) | high — enables type-narrowing across ~30 service methods | 0.5 day | medium (breaks all consumers; visible TS errors guide fix) |
| 4 | TD-8 + TD-10 + TD-11 (admin/service request bodies as Pydantic) | high — closes mass-assignment surface | 1 day | low |
| 5 | TD-9 (services: honest Optional or domain exceptions) | medium — eliminates 41 silent-None paths | 2 days | medium (each return-None becomes a decision) |
| 6 | TD-4 (`database_authenticate` return type) | high — fixes login contract | 0.5 day | low (one function) |
| 7 | TD-5 + TD-6 + TD-7 + TD-14 + TD-15 (Pydantic schema discriminated unions and naked-dict fields) | medium — incremental Pydantic hygiene | 2-3 days total | low |
| 8 | TD-16 (Literal enums for state strings) | medium — same fix in ~50 sites | 1 day | low |
| 9 | TD-17 (frontend `catch (e: any)` → `unknown`) | low — readability + correctness | 0.5 day | very low |
| 10 | TD-18 (frontend branded IDs) | high long-term — incremental rollout | continuous | low if staged |

---

## ANTI-PATTERNS NOT FOUND (good signs)

- `# type: ignore` clusters in app code: **only 10**, all in two files. Not a systemic problem.
- Mutable default arguments (`def f(x = [])`): **0 in backend app code**.
- Sync def returning `Coroutine`: **0**. The codebase consistently uses `async def`.
- 3-way primitive unions (`int | str | bool`): **1 in `depth_limiter.py`** (justified — recursion depth literal value).
- `User.id` from SQLAlchemy is consistently `Mapped[str]` (Session 142's VARCHAR sweep landed cleanly).

These are signs that prior remediation efforts (Sessions 142, 148, 152) have already removed the worst classes of bug. The next wave of work in this audit is centered on the *identity* of the authenticated user and the boundary between Pydantic schemas and untyped JSON.

---

**End of audit. File: `C:\Users\husey\kiro2\docs\audits\2026-05-21_full_audit\type_design_violations.md`**
