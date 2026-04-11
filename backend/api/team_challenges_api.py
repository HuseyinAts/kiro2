# Team Challenges API Endpoints

import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from pydantic import BaseModel

from core.dependencies import AuthenticatedUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/challenges", tags=["Team Challenges"])


class CreateTeamRequest(BaseModel):
    team_name: str
    is_public: bool = True


class CreateBattleRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    max_participants: int = 4


class JoinBattleRequest(BaseModel):
    room_code: str


@router.post("/teams/create")
async def create_team(
    request: CreateTeamRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Yeni bir takim olusturur ve kullaniciyi takim lideri olarak atar."""
    from services._deprecated.team_challenges import TeamChallengeManager

    # current_user.id is a UUID string; dataclasses don't enforce int typing at runtime
    user_id = str(current_user.id)
    manager = TeamChallengeManager()
    team = manager.create_team(request.team_name, user_id)

    return {
        "team_id": team.team_id,
        "team_name": team.team_name,
        "leader_id": team.leader_id,
        "join_code": team.team_id,
    }


@router.post("/battles/create")
async def create_quiz_battle(
    request: CreateBattleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Yeni bir quiz savasi odasi olusturur. Oda kodu ile diger kullanicilar katilabilir."""
    from services._deprecated.team_challenges import TeamChallengeManager

    host_id = str(current_user.id)
    manager = TeamChallengeManager()
    battle = manager.create_quiz_battle(
        host_id=host_id, topic=request.topic, max_participants=request.max_participants
    )

    return {
        "battle_id": battle.battle_id,
        "room_code": battle.room_code,
        "topic": battle.topic,
        "max_participants": battle.max_participants,
    }


@router.post("/battles/join")
async def join_quiz_battle(
    request: JoinBattleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Oda kodu ile mevcut bir quiz savasina katilir."""
    from services._deprecated.team_challenges import TeamChallengeManager

    user_id = str(current_user.id)
    manager = TeamChallengeManager()

    # Find battle by room code
    battle = None
    for b in manager.battles.values():
        if b.room_code == request.room_code:
            battle = b
            break

    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    success = battle.add_participant(user_id)

    if not success:
        raise HTTPException(status_code=400, detail="Battle is full or already joined")

    return {
        "battle_id": battle.battle_id,
        "participants": battle.participants,
        "status": "joined",
    }


@router.get("/battles/{battle_id}/leaderboard")
async def get_battle_leaderboard(battle_id: str):
    """Belirli bir quiz savasinin skor tablosunu dondurur."""
    from services._deprecated.team_challenges import TeamChallengeManager

    manager = TeamChallengeManager()
    battle = manager.battles.get(battle_id)

    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    return {"battle_id": battle_id, "leaderboard": battle.get_leaderboard()}


@router.get("/teams/leaderboard")
async def get_team_leaderboard(limit: int = 10):
    """Tum takimlarin genel siralamasini puan ve kazanilan yarisma sayisina gore dondurur."""
    from services._deprecated.team_challenges import TeamChallengeManager

    manager = TeamChallengeManager()
    teams = manager.get_team_leaderboard(limit)

    return {
        "leaderboard": [
            {
                "rank": idx + 1,
                "team_id": team.team_id,
                "team_name": team.team_name,
                "total_points": team.total_points,
                "challenges_won": team.challenges_won,
            }
            for idx, team in enumerate(teams)
        ]
    }


@router.websocket("/ws/battle/{battle_id}")
async def websocket_battle(websocket: WebSocket, battle_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "submit_answer":
                response = {"type": "answer_result", "correct": True, "points": 100}
                await websocket.send_json(response)

            elif data["type"] == "get_scores":
                response = {"type": "scores_update", "scores": {}}
                await websocket.send_json(response)

    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        await websocket.close()
