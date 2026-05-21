"""
League API — F2 Lig Sistemi

Endpoints:
  GET  /api/v1/leagues/current    — Mevcut tier, sıra ve standings
  GET  /api/v1/leagues/history    — Geçmiş haftalık lig sonuçları
  POST /api/v1/leagues/award-xp   — XP ver (quiz/sınav tamamlama sonrası)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/leagues", tags=["Lig Sistemi"])
logger = get_logger("league_api")


# ---------------------------------------------------------------------------
# Pydantic modelleri
# ---------------------------------------------------------------------------


class StandingsEntry(BaseModel):
    student_id: str
    display_name: str
    xp: int
    rank: int
    is_self: bool


class LeagueStandingsResponse(BaseModel):
    tier: str
    rank: int
    weekly_xp: int
    total_in_tier: int
    week_start: str
    standings: list[StandingsEntry]


class LeagueHistoryEntry(BaseModel):
    week_start: str
    from_tier: str
    to_tier: str
    final_rank: int
    final_xp: int
    promoted: bool
    demoted: bool


class AwardXpRequest(BaseModel):
    xp_amount: int = Field(..., gt=0, le=1000, description="Verilecek XP miktarı")
    source: str = Field(..., min_length=1, max_length=50, description="XP kaynağı")


class AwardXpResponse(BaseModel):
    student_id: str
    source: str
    xp_awarded: int
    new_total_xp: int
    tier: str
    week_start: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/current",
    response_model=LeagueStandingsResponse,
    summary="Mevcut lig durumu",
    description=(
        "Öğrencinin mevcut lig tier'ını, sırasını ve tier'daki üst oyuncuları döner."
    ),
)
async def get_current_standings(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> LeagueStandingsResponse:
    """Get current league tier, rank and top standings.

    Returns the authenticated student's tier, weekly XP, rank within
    the tier, and the top 20 players in the same tier.

    Args:
        current_user: The authenticated student.

    Returns:
        League standings including tier info and leaderboard entries.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.league_service import get_league_standings

    try:
        async with get_db_session_context() as db:
            result = await get_league_standings(db=db, student_id=current_user.id)

        return LeagueStandingsResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "League standings error",
            extra_data={"user": current_user.id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lig durumu alınırken hata oluştu",
        )


@router.get(
    "/history",
    response_model=list[LeagueHistoryEntry],
    summary="Geçmiş lig sonuçları",
    description=(
        "Öğrencinin geçmiş haftalık lig sonuçlarını (tier değişimi, sıra, XP) döner."
    ),
)
async def get_league_history(
    limit: int = Query(10, ge=1, le=50, description="Maksimum kayıt sayısı"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[LeagueHistoryEntry]:
    """Get past league results for the authenticated student.

    Returns up to `limit` weeks of historical results ordered most
    recent first. Each entry shows tier promotion/demotion, final rank
    and weekly XP.

    Args:
        limit: Maximum number of history entries to return.
        current_user: The authenticated student.

    Returns:
        List of past league week results.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.league_service import get_league_history

    try:
        async with get_db_session_context() as db:
            results = await get_league_history(
                db=db, student_id=current_user.id, limit=limit
            )

        return [LeagueHistoryEntry(**r) for r in results]

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "League history error",
            extra_data={"user": current_user.id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lig geçmişi alınırken hata oluştu",
        )


@router.post(
    "/award-xp",
    response_model=AwardXpResponse,
    status_code=status.HTTP_200_OK,
    summary="XP ver",
    description=(
        "Kimliği doğrulanmış öğrenciye belirtilen kaynaktan XP verir."
        " Genellikle quiz veya sınav tamamlama sonrası çağrılır."
    ),
)
async def award_xp(
    request: Request,
    body: AwardXpRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AwardXpResponse:
    """Award XP to the authenticated student.

    Adds XP to the student's current week league membership.
    Called internally after quiz/exam completion or daily login.

    Args:
        body: XP amount and source identifier.
        current_user: The authenticated student.

    Returns:
        Updated XP totals, tier and week_start.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from api.auth import _check_rate_limit, _record_attempt
    from services.league_service import award_xp

    await _check_rate_limit(request, "award_xp")
    _record_attempt(request, "award_xp")

    try:
        async with get_db_session_context() as db:
            result = await award_xp(
                db=db,
                student_id=current_user.id,
                xp_amount=body.xp_amount,
                source=body.source,
            )

        return AwardXpResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Award XP error",
            extra_data={
                "user": current_user.id,
                "xp_amount": body.xp_amount,
                "source": body.source,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="XP verilirken hata oluştu",
        )
