"""
Dungeon Learning Path API
GET  /api/v1/dungeon/{subject}  — dungeon map + progress
POST /api/v1/dungeon/{subject}/complete — quiz completion UPSERT
"""

from __future__ import annotations

from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db

router = APIRouter(prefix="/api/v1/dungeon", tags=["Dungeon Learning Path"])

CODE_PREFIX_MAP: dict[str, str] = {
    "MATEMATIK": "MAT.",
    "GEOMETRI": "GEO",
    "FIZIK": "FIZ",
    "KIMYA": "KIM",
    "BIYOLOJI": "BIY",
    "TURKCE": "TUR",
    "TARIH": "TAR",
    "COGRAFYA": "COG",
    "EDEBIYAT": "EDU",
}

# subject_area → subject_id (student_abilities PK)
_SUBJECT_ID_MAP: dict[str, int] = {
    "MATEMATIK": 1,
    "GEOMETRI": 2,
    "FIZIK": 3,
    "KIMYA": 4,
    "BIYOLOJI": 5,
    "TURKCE": 6,
    "TARIH": 7,
    "COGRAFYA": 8,
    "EDEBIYAT": 9,
    "FELSEFE": 10,
    "DIN": 11,
    "SOSYAL": 12,
}


# ── Pydantic models ────────────────────────────────────────────────


class DungeonProgressData(BaseModel):
    attempt_count: int = 0
    best_score: int = 0
    last_score: int = 0
    completed: bool = False


class DungeonRoomOut(BaseModel):
    topic_id: str
    code: str
    name_tr: str
    parent_subject: str
    prereqs_met: bool
    dag_depth: int
    progress: DungeonProgressData
    question_count: int


class DungeonEdgeOut(BaseModel):
    from_topic: str
    to_topic: str
    prereq_type: str


class DungeonMapResponse(BaseModel):
    subject: str
    theta: float
    theta_se: float
    rooms: list[DungeonRoomOut]
    edges: list[DungeonEdgeOut]


class QuizCompleteRequest(BaseModel):
    topic_id: str
    score: int


class QuizCompleteResponse(BaseModel):
    completed: bool
    attempt_count: int
    best_score: int


# ── Pure functions (testable without DB) ───────────────────────────


def compute_dag_depths(
    rooms: list[dict],
    edges: list[dict],
) -> dict[str, int]:
    """Kahn's algorithm — returns topological depth per topic_id."""
    if not rooms:
        return {}

    topic_ids = {r["topic_id"] for r in rooms}
    in_degree: dict[str, int] = dict.fromkeys(topic_ids, 0)
    children: dict[str, list[str]] = defaultdict(list)

    for e in edges:
        src, dst = e["from_topic"], e["to_topic"]
        if src in topic_ids and dst in topic_ids:
            in_degree[dst] = in_degree.get(dst, 0) + 1
            children[src].append(dst)

    queue: deque[tuple[str, int]] = deque()
    for tid, deg in in_degree.items():
        if deg == 0:
            queue.append((tid, 0))

    depths: dict[str, int] = {}
    while queue:
        tid, depth = queue.popleft()
        depths[tid] = depth
        for child in children.get(tid, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append((child, depth + 1))

    # Nodes not reached (cycles or orphans) get max depth + 1
    max_depth = max(depths.values(), default=0)
    for tid in topic_ids:
        if tid not in depths:
            depths[tid] = max_depth + 1

    return depths


def compute_question_counts(
    direct_counts: dict[str, int],
    root_count: int,
    sibling_count: int,
) -> dict[str, int]:
    """Fallback: if direct count is 0, use root_count // sibling_count."""
    fallback = root_count // sibling_count if sibling_count > 0 else 0
    return {tid: cnt if cnt > 0 else fallback for tid, cnt in direct_counts.items()}


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("/{subject}", response_model=DungeonMapResponse)
async def get_dungeon_map(
    subject: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DungeonMapResponse:
    """Return dungeon map for a subject: rooms + edges + progress."""
    subject_upper = subject.upper()
    prefix = CODE_PREFIX_MAP.get(subject_upper)
    if not prefix:
        raise HTTPException(404, f"Unknown subject: {subject}")

    # ── 1. Fetch topics ──
    result = await db.execute(
        text("""
            SELECT id, code, name_tr, subject_area
            FROM topic_hierarchy
            WHERE is_active = true
              AND (
                  subject_area = :subj
                  OR (subject_area IS NULL AND code LIKE :prefix || '%')
              )
              AND code != :prefix_root
        """),
        {
            "subj": subject_upper,
            "prefix": prefix,
            "prefix_root": prefix.rstrip("."),  # exclude root like 'MAT'
        },
    )
    topics = result.mappings().all()

    if not topics:
        raise HTTPException(404, f"No topics found for subject: {subject}")

    topic_ids = [str(t["id"]) for t in topics]

    # ── 2. Fetch edges ──
    edge_result = await db.execute(
        text("""
            SELECT tp.topic_id::text AS to_topic,
                   tp.prereq_id::text AS from_topic,
                   tp.prereq_type
            FROM topic_prerequisites tp
            WHERE tp.topic_id = ANY(CAST(:ids AS text[])) OR tp.prereq_id = ANY(CAST(:ids AS text[]))
        """),
        {"ids": topic_ids},
    )
    edges_raw = edge_result.mappings().all()
    topic_id_set = set(topic_ids)
    edges = [
        {
            "from_topic": e["from_topic"],
            "to_topic": e["to_topic"],
            "prereq_type": e["prereq_type"],
        }
        for e in edges_raw
        if e["from_topic"] in topic_id_set and e["to_topic"] in topic_id_set
    ]

    # ── 3. Fetch progress ──
    prog_result = await db.execute(
        text("""
            SELECT topic_id::text, attempt_count, best_score, last_score, completed
            FROM dungeon_progress
            WHERE user_id = :uid AND topic_id = ANY(CAST(:ids AS text[]))
        """),
        {"uid": str(current_user.id), "ids": topic_ids},
    )
    progress_map: dict[str, dict] = {}
    for row in prog_result.mappings().all():
        progress_map[row["topic_id"]] = {
            "attempt_count": row["attempt_count"],
            "best_score": row["best_score"],
            "last_score": row["last_score"],
            "completed": row["completed"],
        }

    # ── 4. Fetch theta (LP-02: use student_abilities — same source as orchestrator) ──
    subj_id = _SUBJECT_ID_MAP.get(subject_upper, 0)
    theta_result = await db.execute(
        text("""
            SELECT theta, theta_se FROM student_abilities
            WHERE student_id = :uid AND subject_id = :sid
        """),
        {"uid": str(current_user.id), "sid": subj_id},
    )
    theta_row = theta_result.mappings().first()
    theta = float(theta_row["theta"]) if theta_row else 0.0
    theta_se = float(theta_row["theta_se"]) if theta_row else 0.5

    # ── 5. Question counts (direct + root fallback) ──
    count_result = await db.execute(
        text("""
            SELECT primary_topic_id::text AS tid, COUNT(*) AS cnt
            FROM question_bank
            WHERE is_active = true AND primary_topic_id = ANY(CAST(:ids AS text[]))
            GROUP BY primary_topic_id
        """),
        {"ids": topic_ids},
    )
    direct_counts = {r["tid"]: r["cnt"] for r in count_result.mappings().all()}

    # Root topic count for fallback
    root_result = await db.execute(
        text("""
            SELECT COUNT(*) FROM question_bank qb
            JOIN topic_hierarchy th ON qb.primary_topic_id = th.id
            WHERE qb.is_active = true AND th.code = :root_code
        """),
        {"root_code": prefix.rstrip(".")},
    )
    root_count = root_result.scalar() or 0

    q_counts = compute_question_counts(
        {tid: direct_counts.get(tid, 0) for tid in topic_ids},
        root_count,
        len(topic_ids),
    )

    # ── 6. DAG depths ──
    rooms_raw = [{"topic_id": tid} for tid in topic_ids]
    depths = compute_dag_depths(rooms_raw, edges)

    # ── 7. Prereqs met check ──
    hard_prereqs: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e["prereq_type"] == "hard":
            hard_prereqs[e["to_topic"]].append(e["from_topic"])

    def prereqs_met(topic_id: str) -> bool:
        reqs = hard_prereqs.get(topic_id, [])
        if not reqs:
            return True
        return all(progress_map.get(r, {}).get("completed", False) for r in reqs)

    # ── 8. Build response ──
    topic_lookup = {str(t["id"]): t for t in topics}
    rooms = []
    for tid in topic_ids:
        t = topic_lookup[tid]
        prog = progress_map.get(tid, {})
        rooms.append(
            DungeonRoomOut(
                topic_id=tid,
                code=t["code"],
                name_tr=t["name_tr"],
                parent_subject=t["subject_area"] or subject_upper,
                prereqs_met=prereqs_met(tid),
                dag_depth=depths.get(tid, 0),
                progress=DungeonProgressData(
                    attempt_count=prog.get("attempt_count", 0),
                    best_score=prog.get("best_score", 0),
                    last_score=prog.get("last_score", 0),
                    completed=prog.get("completed", False),
                ),
                question_count=q_counts.get(tid, 0),
            )
        )

    return DungeonMapResponse(
        subject=subject_upper,
        theta=theta,
        theta_se=theta_se,
        rooms=rooms,
        edges=[DungeonEdgeOut(**e) for e in edges],
    )


@router.post("/{subject}/complete", response_model=QuizCompleteResponse)
async def complete_dungeon_quiz(
    subject: str,
    body: QuizCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizCompleteResponse:
    """Record quiz completion — UPSERT dungeon_progress."""
    await db.execute(
        text("""
            INSERT INTO dungeon_progress
                (user_id, topic_id, attempt_count, best_score, last_score, completed)
            VALUES (:uid, :tid, 1, :score, :score, FALSE)
            ON CONFLICT (user_id, topic_id) DO UPDATE SET
                attempt_count = dungeon_progress.attempt_count + 1,
                best_score = GREATEST(dungeon_progress.best_score, EXCLUDED.best_score),
                last_score = EXCLUDED.last_score,
                completed = CASE
                    WHEN dungeon_progress.attempt_count + 1 >= 5
                         AND GREATEST(dungeon_progress.best_score, EXCLUDED.best_score) >= 80
                    THEN TRUE ELSE dungeon_progress.completed END,
                last_attempt = NOW()
        """),
        {"uid": str(current_user.id), "tid": body.topic_id, "score": body.score},
    )
    await db.commit()

    # Return updated state
    result = await db.execute(
        text("""
            SELECT attempt_count, best_score, completed
            FROM dungeon_progress
            WHERE user_id = :uid AND topic_id = :tid
        """),
        {"uid": str(current_user.id), "tid": body.topic_id},
    )
    row = result.mappings().first()
    return QuizCompleteResponse(
        completed=row["completed"],
        attempt_count=row["attempt_count"],
        best_score=row["best_score"],
    )
