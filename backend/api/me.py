"""GET /api/v1/me — frontend `getMe()` icin tek veri kaynagi (#447).

Frontend'de 30 cagri yeri (19 ekran) bu uca gidiyor ve su ana kadar 404
aliyordu; cagrilarin 25'i `Promise.all` icinde korumasiz oldugu icin o
ekranlar hic veri yukleyemiyordu.

Bu modul YALNIZCA HTTP katmani: auth kapisi + servis cagrisi + durum kodu.
Agregasyon ve esleme `services/persona_service.py` icinde ve orasi DB'ye
dokunmayan saf bir fonksiyonla testleniyor.

404 KARARI: kimligi gecerli ama `users` satiri olmayan istek 404 alir, 500
DEGIL. Olculdu — test JWT'sinin kullanicisi (id="1") canli DB'de yok; servis
`.one()` kullansaydi `NoResultFound` yukselir ve "veri yok" durumu sunucu
hatasi gibi gorunurdu.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import AuthenticatedUser, get_current_user, get_db
from services.persona_service import PersonaResponse, persona_getir

router = APIRouter(prefix="/api/v1", tags=["Me"])


@router.get(
    "/me",
    response_model=PersonaResponse,
    summary="Oturumdaki kullanicinin persona bilgisi",
)
async def me(
    mevcut: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    persona = await persona_getir(db, str(mevcut.id))
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanici kaydi bulunamadi",
        )
    return persona
