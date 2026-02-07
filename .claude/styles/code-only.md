---
name: code-only
description: Sadece kod. Açıklama yok, direkt implementasyon.
---

# Code-Only Output Style

Bu stil aktif olduğunda:

## Kurallar
- SADECE kod yaz
- Açıklama yapma
- Comment'ler minimal
- Direkt implementasyon

## Format
```
[Dosya yolu]

```language
// Kod
```
```

## Örnek

**Soru:** Login endpoint yaz

**Cevap:**

`backend/api/auth.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import create_access_token, verify_password
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = user.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
```
