"""
Duel Service — F1 1v1 Düello
Handles matchmaking, game flow, ELO calculation, and Redis queue management.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger
from models.duel import DuelMatch, DuelRating, DuelSession

logger = get_logger("duel_service")

# ELO constants
ELO_K_FACTOR = 32
ELO_DEFAULT = 1200.0
ELO_BRACKET_SIZE = 200
MATCHMAKING_TTL_SEC = 60
DUEL_SESSION_TTL_SEC = 600


# ---------------------------------------------------------------------------
# ELO helpers
# ---------------------------------------------------------------------------

def calculate_elo_change(
    rating_a: float, rating_b: float, score_a: float
) -> tuple[float, float]:
    """Calculate ELO rating changes for both players.

    Args:
        rating_a: Player A's current rating.
        rating_b: Player B's current rating.
        score_a: Player A's result (1.0=win, 0.5=draw, 0.0=loss).

    Returns:
        Tuple of (change_a, change_b).
    """
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    change_a = ELO_K_FACTOR * (score_a - expected_a)
    change_b = -change_a
    return round(change_a, 1), round(change_b, 1)


def get_elo_bracket(elo: float) -> int:
    """Return the bracket index for matchmaking (groups of 200)."""
    return int(elo // ELO_BRACKET_SIZE) * ELO_BRACKET_SIZE


# ---------------------------------------------------------------------------
# Matchmaking (Redis)
# ---------------------------------------------------------------------------

async def enqueue_matchmaking(
    redis,
    *,
    student_id: str,
    subject: str,
    elo_rating: float,
) -> Optional[str]:
    """Try to find a match or enqueue the player.

    Uses Redis SETNX for atomic lock and LPUSH/RPOP for queue.
    Returns duel session ID if matched, None if queued.
    """
    bracket = get_elo_bracket(elo_rating)
    queue_key = f"duel:queue:{subject}:{bracket}"

    # Atomic check-and-pop: try to grab an opponent from the queue
    opponent_data = await redis.rpop(queue_key)

    if opponent_data:
        opponent = json.loads(opponent_data)
        if opponent["student_id"] == student_id:
            # Same player — re-queue and return None
            await redis.lpush(queue_key, opponent_data)
            return None

        # Match found — create session ID
        session_id = str(uuid.uuid4())
        match_info = {
            "session_id": session_id,
            "player1_id": opponent["student_id"],
            "player2_id": student_id,
            "subject": subject,
            "player1_elo": opponent["elo_rating"],
            "player2_elo": elo_rating,
        }
        # Store match in Redis for SSE consumers
        await redis.set(
            f"duel:session:{session_id}",
            json.dumps(match_info),
            ex=DUEL_SESSION_TTL_SEC,
        )
        logger.info(
            "Duel match found",
            extra_data={"session_id": session_id, "p1": opponent["student_id"], "p2": student_id},
        )
        return session_id

    # No opponent — enqueue this player
    player_data = json.dumps({
        "student_id": student_id,
        "elo_rating": elo_rating,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    await redis.lpush(queue_key, player_data)
    await redis.expire(queue_key, MATCHMAKING_TTL_SEC)
    return None


async def cancel_matchmaking(redis, *, student_id: str, subject: str, elo_rating: float) -> bool:
    """Remove player from matchmaking queue."""
    bracket = get_elo_bracket(elo_rating)
    queue_key = f"duel:queue:{subject}:{bracket}"

    # Get all entries, filter out this student, re-set
    entries = await redis.lrange(queue_key, 0, -1)
    remaining = [e for e in entries if json.loads(e)["student_id"] != student_id]

    pipe = redis.pipeline()
    await pipe.delete(queue_key)
    for entry in remaining:
        await pipe.lpush(queue_key, entry)
    if remaining:
        await pipe.expire(queue_key, MATCHMAKING_TTL_SEC)
    await pipe.execute()
    return True


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------

async def get_or_create_rating(*, db: AsyncSession, student_id: str) -> DuelRating:
    """Get or create the ELO rating for a student."""
    result = await db.execute(
        select(DuelRating).where(DuelRating.student_id == student_id)
    )
    rating = result.scalar_one_or_none()
    if not rating:
        rating = DuelRating(student_id=student_id)
        db.add(rating)
        await db.flush()
    return rating


async def create_duel_session(
    *,
    db: AsyncSession,
    session_id: str,
    player1_id: str,
    player2_id: str,
    subject: str,
    question_ids: list[str],
) -> DuelSession:
    """Create a duel session and its question matches in DB."""
    session = DuelSession(
        id=session_id,
        player1_id=player1_id,
        player2_id=player2_id,
        subject=subject,
        question_count=len(question_ids),
        status="active",
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)

    for i, qid in enumerate(question_ids):
        match = DuelMatch(
            session_id=session_id,
            question_id=qid,
            question_order=i,
        )
        db.add(match)

    await db.flush()
    return session


async def process_duel_answer(
    *,
    db: AsyncSession,
    session_id: str,
    player_id: str,
    question_order: int,
    answer: str,
    time_ms: int,
    is_correct: bool,
) -> dict:
    """Record a player's answer for a duel question round.

    Returns dict with round status (both answered? scores so far?).
    """
    # Get the session to determine which player number
    sess_result = await db.execute(
        select(DuelSession).where(DuelSession.id == session_id)
    )
    session = sess_result.scalar_one_or_none()
    if not session or session.status != "active":
        return {"error": "Invalid or inactive session"}

    is_player1 = player_id == session.player1_id
    if not is_player1 and player_id != session.player2_id:
        return {"error": "Player not in this session"}

    # Get the match round
    match_result = await db.execute(
        select(DuelMatch).where(
            DuelMatch.session_id == session_id,
            DuelMatch.question_order == question_order,
        )
    )
    match = match_result.scalar_one_or_none()
    if not match:
        return {"error": "Invalid question order"}

    # Update player's answer
    if is_player1:
        match.player1_answer = answer
        match.player1_time_ms = time_ms
        match.player1_correct = is_correct
        if is_correct:
            session.player1_score += 1
    else:
        match.player2_answer = answer
        match.player2_time_ms = time_ms
        match.player2_correct = is_correct
        if is_correct:
            session.player2_score += 1

    await db.flush()

    # Check if both players answered this round
    both_answered = (
        match.player1_answer is not None and match.player2_answer is not None
    )

    return {
        "round_complete": both_answered,
        "question_order": question_order,
        "player1_score": session.player1_score,
        "player2_score": session.player2_score,
        "is_correct": is_correct,
    }


async def finish_duel(*, db: AsyncSession, session_id: str) -> Optional[dict]:
    """Finalize a duel session: calculate winner and ELO changes."""
    sess_result = await db.execute(
        select(DuelSession).where(DuelSession.id == session_id)
    )
    session = sess_result.scalar_one_or_none()
    if not session or session.status != "active":
        return None

    # Determine winner
    if session.player1_score > session.player2_score:
        session.winner_id = session.player1_id
        score_a = 1.0
    elif session.player2_score > session.player1_score:
        session.winner_id = session.player2_id
        score_a = 0.0
    else:
        session.winner_id = None  # draw
        score_a = 0.5

    # Get ratings
    r1 = await get_or_create_rating(db=db, student_id=session.player1_id)
    r2 = await get_or_create_rating(db=db, student_id=session.player2_id)

    # Calculate ELO changes
    change_a, change_b = calculate_elo_change(r1.elo_rating, r2.elo_rating, score_a)

    r1.elo_rating += change_a
    r2.elo_rating += change_b
    r1.peak_rating = max(r1.peak_rating, r1.elo_rating)
    r2.peak_rating = max(r2.peak_rating, r2.elo_rating)

    session.player1_elo_change = change_a
    session.player2_elo_change = change_b

    # Update W/L/D
    if score_a == 1.0:
        r1.wins += 1
        r2.losses += 1
    elif score_a == 0.0:
        r1.losses += 1
        r2.wins += 1
    else:
        r1.draws += 1
        r2.draws += 1

    session.status = "completed"
    session.finished_at = datetime.now(timezone.utc)

    await db.flush()

    return {
        "winner_id": session.winner_id,
        "player1_score": session.player1_score,
        "player2_score": session.player2_score,
        "player1_elo_change": change_a,
        "player2_elo_change": change_b,
        "player1_new_elo": r1.elo_rating,
        "player2_new_elo": r2.elo_rating,
    }


async def get_duel_history(*, db: AsyncSession, student_id: str, limit: int = 20) -> list[dict]:
    """Get recent duel results for a student."""
    result = await db.execute(
        select(DuelSession)
        .where(
            DuelSession.status == "completed",
            (DuelSession.player1_id == student_id) | (DuelSession.player2_id == student_id),
        )
        .order_by(DuelSession.finished_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "session_id": s.id,
            "subject": s.subject,
            "opponent_id": s.player2_id if s.player1_id == student_id else s.player1_id,
            "my_score": s.player1_score if s.player1_id == student_id else s.player2_score,
            "opponent_score": s.player2_score if s.player1_id == student_id else s.player1_score,
            "won": s.winner_id == student_id,
            "draw": s.winner_id is None,
            "elo_change": s.player1_elo_change if s.player1_id == student_id else s.player2_elo_change,
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
        }
        for s in sessions
    ]
