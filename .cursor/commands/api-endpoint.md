# Yeni API Endpoint

KIRO2 standartlarına uygun yeni FastAPI endpoint ekle. Kullanıcı endpoint
tanımını (method, path, amaç) komut sonrası belirtecek.

## Pre-Check (Zorunlu)

Yeni endpoint yazmadan önce:

1. `@Codebase` ile benzer endpoint arat — varsa onu extend et, yoktan yaratma
2. İlgili router dosyasını bul: `backend/app/api/v1/<domain>.py`
3. Schema dosyasını belirle: `backend/app/schemas/<domain>.py`
4. Service katmanı: `backend/app/services/<domain>/`

## Şablon — Endpoint

```python
# backend/app/api/v1/<domain>.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models import User
from app.schemas.<domain> import <Resource>Response, <Resource>Create
from app.services.<domain> import <domain>_service

router = APIRouter(prefix="/<domain>", tags=["<domain>"])


@router.get("/{resource_id}", response_model=<Resource>Response)
async def get_<resource>(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> <Resource>Response:
    """<Resource>'u ID ile getir.

    Args:
        resource_id: Kaynak ID'si
        db: Async DB session
        current_user: Auth kullanıcısı

    Returns:
        <Resource> response modeli

    Raises:
        HTTPException 404: Kaynak bulunamadı
        HTTPException 403: Başka kullanıcının kaynağı (IDOR)
    """
    resource = await <domain>_service.get_by_id(db, resource_id)

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="<Resource> bulunamadı",
        )

    # IDOR check — ZORUNLU (Session 78 pattern)
    if resource.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kaynağa erişim izniniz yok",
        )

    return <Resource>Response.from_orm(resource)
```

## Zorunlu Kontroller (checklist)

- [ ] `Depends(get_current_user)` — auth
- [ ] IDOR ownership check — `resource.user_id == current_user.id`
- [ ] Pydantic response_model tanımlı
- [ ] Async session kullanılıyor (`AsyncSession`, `await`)
- [ ] Türkçe docstring
- [ ] Exception mapping (domain error → HTTPException)
- [ ] Rate limiting decorator (kritik endpoint'lerde)

## Router Kaydı (Session 120 — KRİTİK)

Yeni router dosyası oluşturduysan `backend/routers/loader.py` ROUTER_MAPPING'e
ekle:

```python
# routers/loader.py
ROUTER_MAPPING = {
    ...
    "app.api.v1.<domain>": ("<category>", "app.api.v1.<domain>"),
}
```

Aksi halde endpoint 404 döner (Session 112'de 5 router 2+ hafta kayıtsız kaldı).

Kontrol: `pytest tests/test_router_registration.py`

## Test Zorunluluğu

Her yeni endpoint için minimum 3 test:

```python
# backend/tests/unit/test_<domain>_api.py

async def test_get_<resource>_happy_path(async_client, auth_headers):
    response = await async_client.get("/api/v1/<domain>/1", headers=auth_headers)
    assert response.status_code == 200

async def test_get_<resource>_not_found(async_client, auth_headers):
    response = await async_client.get("/api/v1/<domain>/999999", headers=auth_headers)
    assert response.status_code == 404

async def test_get_<resource>_idor_blocked(async_client, other_user_auth_headers):
    # Başka kullanıcının resource'u
    response = await async_client.get("/api/v1/<domain>/1", headers=other_user_auth_headers)
    assert response.status_code == 403
```

## İlgili Kurallar

- `.cursor/rules/10-backend.mdc` — backend pattern'ları
- `.claude/rules/security.md` — JWT, rate limit, RBAC detayları
- `.claude/rules/testing.md` — test yazma öğrenilen dersler
