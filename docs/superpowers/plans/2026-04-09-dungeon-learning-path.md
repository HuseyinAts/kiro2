# Dungeon Learning Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing learning path visualizer with an RPG dungeon-themed map featuring hand-drawn rooms (Rough.js), DAG-based layout (dagre), fog of war, and room evolution based on student progress.

**Architecture:** New `/api/v1/dungeon/{subject}` backend endpoint serves topic DAG + progress data. Frontend `DungeonMap` component renders SVG with Rough.js sketch aesthetic, dagre for layout, @use-gesture for pan/zoom. New `dungeon_progress` table tracks per-topic attempts/scores. Existing `topic_hierarchy` and `topic_prerequisites` tables provide the DAG structure.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic (backend); React 18, TypeScript, Rough.js, dagre, @use-gesture/react, Framer Motion (frontend)

**Spec:** `docs/superpowers/specs/2026-04-09-dungeon-learning-path-design.md`

---

## File Map

### Backend (Create)
| File | Responsibility |
|------|---------------|
| `backend/models/dungeon_models.py` | DungeonProgress ORM model |
| `backend/alembic/versions/20260410_create_dungeon_progress.py` | Migration |
| `backend/app/api/learning_path_dungeon.py` | GET + POST dungeon endpoints |
| `backend/scripts/seed_dungeon_topics.py` | Subject area UPDATE + new topics + prereqs |
| `backend/tests/unit/test_dungeon_endpoint.py` | Endpoint tests |
| `backend/tests/unit/test_dungeon_progress.py` | ORM + UPSERT tests |

### Backend (Modify)
| File | Change |
|------|--------|
| `backend/routers/loader.py` | Add ROUTER_MAPPING entry |
| `backend/models/__init__.py` | Import DungeonProgress |

### Frontend (Create)
| File | Responsibility |
|------|---------------|
| `frontend/src/hooks/useDungeonMap.ts` | Fetch + dagre layout + state |
| `frontend/src/components/LearningPath/DungeonMap.tsx` | SVG viewport + pan/zoom + orchestration |
| `frontend/src/components/LearningPath/DungeonRoom.tsx` | Rough.js room (4 levels) |
| `frontend/src/components/LearningPath/OrganicPath.tsx` | Rough.js Bezier edges |
| `frontend/src/components/LearningPath/FogOfWar.tsx` | SVG filter + opacity |
| `frontend/src/components/LearningPath/ParchmentBackground.tsx` | CSS background |
| `frontend/src/types/dungeon.ts` | TypeScript interfaces |

### Frontend (Modify)
| File | Change |
|------|--------|
| `frontend/src/pages/ModernLearningPathPage.tsx:909-916` | Replace ModernLearningPathVisualizer with DungeonMap |

---

## Task 1: Install Frontend Dependencies

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install roughjs, dagre, @use-gesture/react, and types**

```bash
cd frontend
npm install roughjs dagre @use-gesture/react
npm install -D @types/dagre
```

- [ ] **Step 2: Verify installation**

```bash
cd frontend
node -e "require('roughjs'); require('dagre'); console.log('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd frontend
git add package.json package-lock.json
git commit -m "chore: add roughjs, dagre, @use-gesture/react dependencies"
```

---

## Task 2: TypeScript Interfaces

**Files:**
- Create: `frontend/src/types/dungeon.ts`
- Test: N/A (type-only file, verified by tsc)

- [ ] **Step 1: Create dungeon types**

Create `frontend/src/types/dungeon.ts`:

```typescript
export interface DungeonProgressData {
  attempt_count: number;
  best_score: number;
  last_score: number;
  completed: boolean;
}

export interface DungeonRoom {
  topic_id: string;
  code: string;
  name_tr: string;
  parent_subject: string;
  prereqs_met: boolean;
  dag_depth: number;
  progress: DungeonProgressData;
  question_count: number;
}

export interface DungeonEdge {
  from_topic: string;
  to_topic: string;
  prereq_type: 'hard' | 'soft';
}

export interface DungeonMapResponse {
  subject: string;
  theta: number;
  theta_se: number;
  rooms: DungeonRoom[];
  edges: DungeonEdge[];
}

/** Room visual level derived from progress */
export type RoomLevel = 0 | 1 | 2 | 3;

export function getRoomLevel(progress: DungeonProgressData): RoomLevel {
  if (progress.completed) return 3;
  if (progress.best_score >= 50) return 2;
  if (progress.attempt_count > 0) return 1;
  return 0;
}

/** Seeded pseudo-random for deterministic Rough.js offsets */
export function seededRandom(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
  }
  return ((Math.sin(hash * 9301 + 49297) % 233280) + 233280) % 233280 / 233280;
}

/** Fog opacity based on theta + dag_depth + completion */
export function fogOpacity(
  room: DungeonRoom,
  theta: number,
): number {
  if (!room.prereqs_met) return 0.9;
  if (room.progress.completed) return 0;

  const thetaFactor = Math.max(0, Math.min(1, (theta + 3) / 6));
  const depthFactor = Math.max(0, 1 - room.dag_depth * 0.15);

  return Math.max(0, 0.7 - thetaFactor * 0.4 - depthFactor * 0.2);
}
```

- [ ] **Step 2: Verify types compile**

```bash
cd frontend && npx tsc --noEmit src/types/dungeon.ts
```

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/dungeon.ts
git commit -m "feat(dungeon): add TypeScript interfaces and utility functions"
```

---

## Task 3: DungeonProgress ORM Model

**Files:**
- Create: `backend/models/dungeon_models.py`
- Modify: `backend/models/__init__.py` (import)
- Test: `backend/tests/unit/test_dungeon_progress.py`

- [ ] **Step 1: Write failing test for the model**

Create `backend/tests/unit/test_dungeon_progress.py`:

```python
"""Tests for DungeonProgress ORM model."""
import pytest
from models.dungeon_models import DungeonProgress


def test_dungeon_progress_table_name():
    assert DungeonProgress.__tablename__ == "dungeon_progress"


def test_dungeon_progress_columns():
    cols = {c.name for c in DungeonProgress.__table__.columns}
    expected = {
        "user_id", "topic_id", "attempt_count", "best_score",
        "last_score", "completed", "first_attempt", "last_attempt",
    }
    assert expected == cols


def test_dungeon_progress_primary_key():
    pk_cols = [c.name for c in DungeonProgress.__table__.primary_key.columns]
    assert sorted(pk_cols) == ["topic_id", "user_id"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/unit/test_dungeon_progress.py -v --tb=short
```

Expected: FAIL — `ModuleNotFoundError: No module named 'models.dungeon_models'`

- [ ] **Step 3: Create the ORM model**

Create `backend/models/dungeon_models.py`:

```python
"""Dungeon Learning Path ORM Models."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)

from .database import Base


class DungeonProgress(Base):
    """Per-user per-topic dungeon progress — attempts, scores, completion."""

    __tablename__ = "dungeon_progress"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    topic_id = Column(String, ForeignKey("topic_hierarchy.id"), primary_key=True)
    attempt_count = Column(Integer, nullable=False, server_default="0")
    best_score = Column(Integer, nullable=False, server_default="0")
    last_score = Column(Integer, nullable=False, server_default="0")
    completed = Column(Boolean, nullable=False, server_default="false")
    first_attempt = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_attempt = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_dungeon_progress_user", "user_id"),
    )
```

- [ ] **Step 4: Add import to models/__init__.py**

Find `backend/models/__init__.py` and add at the end of the import section:

```python
from .dungeon_models import DungeonProgress  # noqa: F401
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/unit/test_dungeon_progress.py -v --tb=short
```

Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/models/dungeon_models.py backend/models/__init__.py backend/tests/unit/test_dungeon_progress.py
git commit -m "feat(dungeon): add DungeonProgress ORM model with tests"
```

---

## Task 4: Alembic Migration

**Files:**
- Create: `backend/alembic/versions/20260410_create_dungeon_progress.py`

- [ ] **Step 1: Create migration file**

Create `backend/alembic/versions/20260410_create_dungeon_progress.py`:

```python
"""Create dungeon_progress table

Revision ID: dungeon_progress_001
Revises: user_item_fsrs_001
Create Date: 2026-04-10
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "dungeon_progress_001"
down_revision: Union[str, None] = "user_item_fsrs_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dungeon_progress",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("topic_id", sa.String(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "first_attempt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_attempt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topic_hierarchy.id"]),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
    )
    op.create_index("idx_dungeon_progress_user", "dungeon_progress", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_dungeon_progress_user", table_name="dungeon_progress")
    op.drop_table("dungeon_progress")
```

- [ ] **Step 2: Run migration**

```bash
cd backend && alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade user_item_fsrs_001 -> dungeon_progress_001`

- [ ] **Step 3: Verify table in DB**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 -c "\d dungeon_progress"
```

Expected: Table with 8 columns, PK (user_id, topic_id), idx_dungeon_progress_user index

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/20260410_create_dungeon_progress.py
git commit -m "feat(dungeon): add dungeon_progress migration"
```

---

## Task 5: Seed Script — Fix subject_area + Add Topics + Prerequisites

**Files:**
- Create: `backend/scripts/seed_dungeon_topics.py`

- [ ] **Step 1: Create seed script**

Create `backend/scripts/seed_dungeon_topics.py`:

```python
"""
Dungeon Topic Seed Script
=========================
1. Fix subject_area=NULL on MAT.xxx topics (→ MATEMATIK)
2. Add ~19 new subtopics for underrepresented subjects
3. Add ~25 new prerequisite edges

Idempotent: ON CONFLICT DO UPDATE / DO NOTHING.

Usage:
    cd backend
    python scripts/seed_dungeon_topics.py [--dry-run]
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import NamedTuple

import asyncpg

DB_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5434/kiro2",
)


class NewTopic(NamedTuple):
    code: str
    name_tr: str
    name_en: str
    subject_area: str
    level: int = 2
    description: str = ""


class Prereq(NamedTuple):
    topic_code: str
    prereq_code: str
    prereq_type: str = "hard"
    strength: float = 0.8


# ── Step 1: subject_area UPDATE for NULL-subject subtopics ──────────
SUBJECT_AREA_FIXES = {
    "MAT.": "MATEMATIK",
}

# ── Step 2: New subtopics for underrepresented subjects ─────────────
NEW_TOPICS: list[NewTopic] = [
    # Turkce (mevcut: 3 topic, +5 yeni)
    NewTopic("TUR.PAR", "Paragraf", "Paragraph", "TURKCE"),
    NewTopic("TUR.ANL", "Anlam Bilgisi", "Semantics", "TURKCE"),
    NewTopic("TUR.YAZ", "Yazim Kurallari", "Spelling Rules", "TURKCE"),
    NewTopic("TUR.DIL", "Dil Bilgisi", "Grammar", "TURKCE"),
    NewTopic("TUR.SOZ", "Soz Varigi", "Vocabulary", "TURKCE"),
    # Biyoloji (mevcut: 2 topic, +6 yeni)
    NewTopic("BIY.HUC", "Hucre Biyolojisi", "Cell Biology", "BIYOLOJI"),
    NewTopic("BIY.GEN", "Genetik", "Genetics", "BIYOLOJI"),
    NewTopic("BIY.EKO", "Ekoloji", "Ecology", "BIYOLOJI"),
    NewTopic("BIY.SIS", "Sistemler", "Body Systems", "BIYOLOJI"),
    NewTopic("BIY.EVR", "Evrim", "Evolution", "BIYOLOJI"),
    NewTopic("BIY.BIT", "Bitki Biyolojisi", "Plant Biology", "BIYOLOJI"),
    # Fizik (mevcut: 4 TYT topic, +4 yeni AYT)
    NewTopic("FIZ.OPT", "Optik", "Optics", "FIZIK"),
    NewTopic("FIZ.ELE", "Elektrik", "Electricity", "FIZIK"),
    NewTopic("FIZ.MAG", "Manyetizma", "Magnetism", "FIZIK"),
    NewTopic("FIZ.MOD", "Modern Fizik", "Modern Physics", "FIZIK"),
    # Kimya (mevcut: 4 TYT topic, +4 yeni AYT)
    NewTopic("KIM.ORG", "Organik Kimya", "Organic Chemistry", "KIMYA"),
    NewTopic("KIM.ASI", "Asitler ve Bazlar", "Acids and Bases", "KIMYA"),
    NewTopic("KIM.DEN", "Kimyasal Denge", "Chemical Equilibrium", "KIMYA"),
    NewTopic("KIM.TER", "Termokimya", "Thermochemistry", "KIMYA"),
]

# ── Step 3: New prerequisite edges ──────────────────────────────────
NEW_PREREQS: list[Prereq] = [
    # Turkce
    Prereq("TUR.ANL", "TUR.PAR", "hard", 0.8),
    Prereq("TUR.YAZ", "TUR.DIL", "hard", 0.8),
    Prereq("TUR.SOZ", "TUR.PAR", "soft", 0.6),
    # Biyoloji
    Prereq("BIY.GEN", "BIY.HUC", "hard", 0.9),
    Prereq("BIY.SIS", "BIY.HUC", "hard", 0.8),
    Prereq("BIY.EVR", "BIY.GEN", "hard", 0.8),
    Prereq("BIY.BIT", "BIY.HUC", "soft", 0.6),
    Prereq("BIY.EKO", "BIY.SIS", "soft", 0.6),
    # Fizik
    Prereq("FIZ.ELE", "TYT-FIZ-03", "hard", 0.8),  # Enerji → Elektrik
    Prereq("FIZ.MAG", "FIZ.ELE", "hard", 0.9),
    Prereq("FIZ.OPT", "TYT-FIZ-04", "hard", 0.8),  # Dalgalar → Optik
    Prereq("FIZ.MOD", "FIZ.ELE", "soft", 0.7),
    # Kimya
    Prereq("KIM.ORG", "TYT-KIM-03", "hard", 0.8),  # Kim Baglar → Organik
    Prereq("KIM.ASI", "TYT-KIM-04", "hard", 0.8),  # Reaksiyonlar → Asit/Baz
    Prereq("KIM.DEN", "KIM.ASI", "hard", 0.8),
    Prereq("KIM.TER", "TYT-KIM-04", "hard", 0.7),  # Reaksiyonlar → Termokimya
]


async def main(dry_run: bool = False) -> None:
    conn = await asyncpg.connect(DB_URL)
    try:
        # ── Step 1: Fix subject_area ──
        for prefix, subject in SUBJECT_AREA_FIXES.items():
            if dry_run:
                rows = await conn.fetch(
                    "SELECT code FROM topic_hierarchy WHERE code LIKE $1 AND subject_area IS NULL",
                    f"{prefix}%",
                )
                print(f"[DRY-RUN] Would UPDATE {len(rows)} topics: {prefix}* → {subject}")
            else:
                result = await conn.execute(
                    "UPDATE topic_hierarchy SET subject_area = $1 WHERE code LIKE $2 AND subject_area IS NULL",
                    subject, f"{prefix}%",
                )
                print(f"[UPDATE] {prefix}* → {subject}: {result}")

        # ── Step 2: Insert new topics ──
        for t in NEW_TOPICS:
            if dry_run:
                print(f"[DRY-RUN] Would INSERT topic: {t.code} ({t.name_tr})")
            else:
                await conn.execute(
                    """
                    INSERT INTO topic_hierarchy
                        (id, code, name_tr, name_en, subject_area, level, description,
                         meb_code, meb_kazanim, osym_relevance, osym_frequency,
                         total_questions, average_difficulty, is_active)
                    VALUES
                        (gen_random_uuid(), $1, $2, $3, $4, $5, $6,
                         '', '', 0.5, 0.5, 0, 0.5, true)
                    ON CONFLICT (code) DO UPDATE SET
                        name_tr = EXCLUDED.name_tr,
                        subject_area = EXCLUDED.subject_area
                    """,
                    t.code, t.name_tr, t.name_en, t.subject_area, t.level, t.description,
                )
                print(f"[INSERT] {t.code}: {t.name_tr}")

        # ── Step 3: Insert new prerequisites ──
        for p in NEW_PREREQS:
            if dry_run:
                print(f"[DRY-RUN] Would INSERT prereq: {p.topic_code} → {p.prereq_code} ({p.prereq_type})")
            else:
                await conn.execute(
                    """
                    INSERT INTO topic_prerequisites (id, topic_id, prereq_id, prereq_type, strength, is_active)
                    SELECT gen_random_uuid(), t.id, p.id, $3, $4, true
                    FROM topic_hierarchy t, topic_hierarchy p
                    WHERE t.code = $1 AND p.code = $2
                    ON CONFLICT DO NOTHING
                    """,
                    p.topic_code, p.prereq_code, p.prereq_type, p.strength,
                )
                print(f"[PREREQ] {p.topic_code} → {p.prereq_code} ({p.prereq_type})")

        # ── Summary ──
        count = await conn.fetchval("SELECT COUNT(*) FROM topic_hierarchy WHERE subject_area IS NOT NULL")
        prereq_count = await conn.fetchval("SELECT COUNT(*) FROM topic_prerequisites")
        print(f"\n[DONE] Topics with subject_area: {count}, Prerequisites: {prereq_count}")

    finally:
        await conn.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(main(dry_run=dry_run))
```

- [ ] **Step 2: Dry-run the seed script**

```bash
cd backend && python scripts/seed_dungeon_topics.py --dry-run
```

Expected: Lines showing what would be updated/inserted, no errors

- [ ] **Step 3: Run the seed script for real**

```bash
cd backend && python scripts/seed_dungeon_topics.py
```

Expected: UPDATE + INSERT lines, final summary showing increased topic/prereq counts

- [ ] **Step 4: Verify in DB**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 -c "
SELECT subject_area, COUNT(*) FROM topic_hierarchy
WHERE subject_area IS NOT NULL GROUP BY subject_area ORDER BY count DESC;"
```

Expected: MATEMATIK should show ~40+ (was 20), new subjects visible

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/seed_dungeon_topics.py
git commit -m "feat(dungeon): add seed script — subject_area fix + 19 topics + 16 prereqs"
```

---

## Task 6: Backend Endpoint — GET /dungeon/{subject}

**Files:**
- Create: `backend/app/api/learning_path_dungeon.py`
- Modify: `backend/routers/loader.py`
- Test: `backend/tests/unit/test_dungeon_endpoint.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/unit/test_dungeon_endpoint.py`:

```python
"""Tests for dungeon endpoint."""
import pytest

from app.api.learning_path_dungeon import (
    CODE_PREFIX_MAP,
    compute_dag_depths,
    compute_question_counts,
)


def test_code_prefix_map_has_nine_subjects():
    assert len(CODE_PREFIX_MAP) == 9
    assert "MATEMATIK" in CODE_PREFIX_MAP
    assert "FIZIK" in CODE_PREFIX_MAP


def test_compute_dag_depths_empty():
    result = compute_dag_depths([], [])
    assert result == {}


def test_compute_dag_depths_chain():
    """A → B → C should give depths 0, 1, 2."""
    rooms = [
        {"topic_id": "a"},
        {"topic_id": "b"},
        {"topic_id": "c"},
    ]
    edges = [
        {"from_topic": "a", "to_topic": "b"},
        {"from_topic": "b", "to_topic": "c"},
    ]
    depths = compute_dag_depths(rooms, edges)
    assert depths["a"] == 0
    assert depths["b"] == 1
    assert depths["c"] == 2


def test_compute_question_counts_with_fallback():
    """When direct count is 0, use root_count / sibling_count."""
    direct = {"topic-1": 100, "topic-2": 0}
    root_count = 1000
    sibling_count = 5
    result = compute_question_counts(direct, root_count, sibling_count)
    assert result["topic-1"] == 100
    assert result["topic-2"] == 200  # 1000 // 5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/unit/test_dungeon_endpoint.py -v --tb=short
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.api.learning_path_dungeon'`

- [ ] **Step 3: Create endpoint file**

Create `backend/app/api/learning_path_dungeon.py`:

```python
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
    in_degree: dict[str, int] = {tid: 0 for tid in topic_ids}
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
    return {
        tid: cnt if cnt > 0 else fallback
        for tid, cnt in direct_counts.items()
    }


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
            WHERE tp.topic_id = ANY(:ids) OR tp.prereq_id = ANY(:ids)
        """),
        {"ids": topic_ids},
    )
    edges_raw = edge_result.mappings().all()
    edges = [
        {"from_topic": e["from_topic"], "to_topic": e["to_topic"], "prereq_type": e["prereq_type"]}
        for e in edges_raw
        if e["from_topic"] in set(topic_ids) and e["to_topic"] in set(topic_ids)
    ]

    # ── 3. Fetch progress ──
    prog_result = await db.execute(
        text("""
            SELECT topic_id::text, attempt_count, best_score, last_score, completed
            FROM dungeon_progress
            WHERE user_id = :uid AND topic_id = ANY(:ids)
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

    # ── 4. Fetch theta ──
    theta_result = await db.execute(
        text("""
            SELECT theta_estimate, theta_se FROM user_theta
            WHERE user_id = :uid AND subject_area = :subj
        """),
        {"uid": str(current_user.id), "subj": subject_upper},
    )
    theta_row = theta_result.mappings().first()
    theta = float(theta_row["theta_estimate"]) if theta_row else 0.0
    theta_se = float(theta_row["theta_se"]) if theta_row else 0.5

    # ── 5. Question counts (direct + root fallback) ──
    count_result = await db.execute(
        text("""
            SELECT primary_topic_id::text AS tid, COUNT(*) AS cnt
            FROM question_bank
            WHERE is_active = true AND primary_topic_id = ANY(:ids)
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
    # A room's prereqs are met if all hard prereqs are completed
    hard_prereqs: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e["prereq_type"] == "hard":
            hard_prereqs[e["to_topic"]].append(e["from_topic"])

    def prereqs_met(topic_id: str) -> bool:
        reqs = hard_prereqs.get(topic_id, [])
        if not reqs:
            return True
        return all(
            progress_map.get(r, {}).get("completed", False) for r in reqs
        )

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
```

- [ ] **Step 4: Run tests to verify pure functions pass**

```bash
cd backend && python -m pytest tests/unit/test_dungeon_endpoint.py -v --tb=short
```

Expected: 4 PASSED

- [ ] **Step 5: Register router in loader.py**

Add to `ROUTER_MAPPING` in `backend/routers/loader.py` (after the learning_path entries):

```python
    "app.api.learning_path_dungeon": ("learning", "app.api.learning_path_dungeon"),
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/learning_path_dungeon.py backend/routers/loader.py backend/tests/unit/test_dungeon_endpoint.py
git commit -m "feat(dungeon): add GET/POST dungeon endpoints with tests"
```

---

## Task 7: Frontend Hook — useDungeonMap

**Files:**
- Create: `frontend/src/hooks/useDungeonMap.ts`

- [ ] **Step 1: Create the hook**

Create `frontend/src/hooks/useDungeonMap.ts`:

```typescript
/**
 * useDungeonMap Hook
 *
 * Fetches dungeon map data for a subject and computes dagre layout.
 * Returns rooms with x/y positions, edges, loading state, and refetch.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import dagre from 'dagre';
import { apiRequest } from '@/utils/apiHelpers';
import type {
  DungeonMapResponse,
  DungeonRoom,
  DungeonEdge,
} from '@/types/dungeon';

export interface LayoutNode extends DungeonRoom {
  x: number;
  y: number;
}

export interface LayoutEdge extends DungeonEdge {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
}

interface UseDungeonMapReturn {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  theta: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const NODE_WIDTH = 120;
const NODE_HEIGHT = 90;
const RANK_SEP = 140;
const NODE_SEP = 100;

function computeLayout(
  rooms: DungeonRoom[],
  edges: DungeonEdge[],
): { nodes: LayoutNode[]; edges: LayoutEdge[] } {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'TB', ranksep: RANK_SEP, nodesep: NODE_SEP });
  g.setDefaultEdgeLabel(() => ({}));

  rooms.forEach((r) => {
    g.setNode(r.topic_id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });
  edges.forEach((e) => {
    g.setEdge(e.from_topic, e.to_topic);
  });

  dagre.layout(g);

  const nodeMap = new Map<string, { x: number; y: number }>();
  g.nodes().forEach((id) => {
    const node = g.node(id);
    if (node) nodeMap.set(id, { x: node.x, y: node.y });
  });

  const layoutNodes: LayoutNode[] = rooms.map((r) => ({
    ...r,
    x: nodeMap.get(r.topic_id)?.x ?? 0,
    y: nodeMap.get(r.topic_id)?.y ?? 0,
  }));

  const layoutEdges: LayoutEdge[] = edges
    .map((e) => ({
      ...e,
      fromX: nodeMap.get(e.from_topic)?.x ?? 0,
      fromY: nodeMap.get(e.from_topic)?.y ?? 0,
      toX: nodeMap.get(e.to_topic)?.x ?? 0,
      toY: nodeMap.get(e.to_topic)?.y ?? 0,
    }))
    .filter((e) => nodeMap.has(e.from_topic) && nodeMap.has(e.to_topic));

  return { nodes: layoutNodes, edges: layoutEdges };
}

export function useDungeonMap(subject: string): UseDungeonMapReturn {
  const [data, setData] = useState<DungeonMapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMap = useCallback(async () => {
    if (!subject) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await apiRequest<DungeonMapResponse>(
        `/api/v1/dungeon/${encodeURIComponent(subject)}`,
      );
      setData(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Harita yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, [subject]);

  useEffect(() => {
    fetchMap();
  }, [fetchMap]);

  const layout = useMemo(() => {
    if (!data) return { nodes: [], edges: [] };
    return computeLayout(data.rooms, data.edges);
  }, [data]);

  return {
    nodes: layout.nodes,
    edges: layout.edges,
    theta: data?.theta ?? 0,
    loading,
    error,
    refetch: fetchMap,
  };
}
```

- [ ] **Step 2: Verify types compile**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useDungeonMap.ts
git commit -m "feat(dungeon): add useDungeonMap hook with dagre layout"
```

---

## Task 8: ParchmentBackground Component

**Files:**
- Create: `frontend/src/components/LearningPath/ParchmentBackground.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/LearningPath/ParchmentBackground.tsx`:

```tsx
import React from 'react';

const PARCHMENT_STYLE: React.CSSProperties = {
  position: 'absolute',
  inset: 0,
  background: `
    radial-gradient(ellipse at 50% 0%, rgba(255,248,220,0.9) 0%, transparent 70%),
    radial-gradient(ellipse at 80% 100%, rgba(210,180,140,0.3) 0%, transparent 50%),
    linear-gradient(180deg, #FFF8DC 0%, #F5E6C8 30%, #E8D5B0 70%, #DBC4A0 100%)
  `,
  zIndex: 0,
};

/** Full-size parchment background for the dungeon map viewport. */
export const ParchmentBackground: React.FC = () => (
  <div style={PARCHMENT_STYLE} aria-hidden="true" />
);
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/LearningPath/ParchmentBackground.tsx
git commit -m "feat(dungeon): add ParchmentBackground component"
```

---

## Task 9: FogOfWar Component

**Files:**
- Create: `frontend/src/components/LearningPath/FogOfWar.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/LearningPath/FogOfWar.tsx`:

```tsx
import React from 'react';

/** SVG filter definitions for fog of war effect. Place inside <svg><defs>. */
export const FogOfWarDefs: React.FC = () => (
  <filter id="dungeon-fog">
    <feGaussianBlur stdDeviation="4" />
    <feColorMatrix
      type="matrix"
      values="0.3 0 0 0 0.2
              0 0.3 0 0 0.2
              0 0 0.3 0 0.25
              0 0 0 1 0"
    />
  </filter>
);

interface FogWrapperProps {
  opacity: number;
  children: React.ReactNode;
}

/**
 * Wraps children in fog effect when opacity > 0.1.
 * opacity=0 → no fog, opacity=0.9 → near-opaque fog.
 */
export const FogWrapper: React.FC<FogWrapperProps> = ({ opacity, children }) => {
  const hasFog = opacity > 0.1;
  return (
    <g
      filter={hasFog ? 'url(#dungeon-fog)' : undefined}
      opacity={1 - opacity}
    >
      {children}
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/LearningPath/FogOfWar.tsx
git commit -m "feat(dungeon): add FogOfWar SVG filter component"
```

---

## Task 10: DungeonRoom Component

**Files:**
- Create: `frontend/src/components/LearningPath/DungeonRoom.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/LearningPath/DungeonRoom.tsx`:

```tsx
import React, { useEffect, useRef } from 'react';
import rough from 'roughjs';
import { AnimatePresence, motion } from 'framer-motion';
import type { DungeonProgressData, RoomLevel } from '@/types/dungeon';
import { getRoomLevel } from '@/types/dungeon';

interface DungeonRoomProps {
  topicId: string;
  code: string;
  nameTr: string;
  x: number;
  y: number;
  progress: DungeonProgressData;
  questionCount: number;
  onClick: () => void;
}

const ROOM_WIDTH = 100;
const ROOM_HEIGHT = 70;

const LEVEL_STYLES: Record<RoomLevel, {
  roughness: number;
  strokeWidth: number;
  stroke: string;
  fill?: string;
}> = {
  0: { roughness: 3, strokeWidth: 1, stroke: '#666' },
  1: { roughness: 2, strokeWidth: 2, stroke: '#8B7355' },
  2: { roughness: 1, strokeWidth: 2, stroke: '#DAA520', fill: 'rgba(255,215,0,0.1)' },
  3: { roughness: 0.5, strokeWidth: 3, stroke: '#FFD700', fill: 'rgba(255,215,0,0.2)' },
};

const LEVEL_ICONS: Record<RoomLevel, string> = {
  0: '\u{1F512}', // lock
  1: '\u{1F6E1}', // shield
  2: '\u2B50',     // star
  3: '\u{1F451}',  // crown
};

export const DungeonRoom: React.FC<DungeonRoomProps> = ({
  topicId,
  code,
  nameTr,
  x,
  y,
  progress,
  questionCount,
  onClick,
}) => {
  const gRef = useRef<SVGGElement>(null);
  const level = getRoomLevel(progress);
  const style = LEVEL_STYLES[level];

  useEffect(() => {
    const g = gRef.current;
    if (!g) return;

    const svg = g.ownerSVGElement;
    if (!svg) return;

    // Clear previous Rough.js rendering
    while (g.firstChild) g.removeChild(g.firstChild);

    const rc = rough.svg(svg);
    const rect = rc.rectangle(
      -ROOM_WIDTH / 2,
      -ROOM_HEIGHT / 2,
      ROOM_WIDTH,
      ROOM_HEIGHT,
      {
        roughness: style.roughness,
        strokeWidth: style.strokeWidth,
        stroke: style.stroke,
        fill: style.fill,
        fillStyle: style.fill ? 'solid' : undefined,
      },
    );
    g.appendChild(rect);
  }, [level, style]);

  return (
    <AnimatePresence mode="wait">
      <motion.g
        key={`room-${topicId}-${level}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        transform={`translate(${x}, ${y})`}
        onClick={onClick}
        style={{ cursor: 'pointer' }}
        role="button"
        aria-label={`${nameTr} — ${LEVEL_ICONS[level]}`}
      >
        {/* Rough.js rendered rectangle */}
        <g ref={gRef} />

        {/* Icon */}
        <text
          textAnchor="middle"
          dominantBaseline="central"
          y={-15}
          fontSize="18"
        >
          {LEVEL_ICONS[level]}
        </text>

        {/* Topic name */}
        <text
          textAnchor="middle"
          dominantBaseline="central"
          y={8}
          fontSize="11"
          fontFamily="serif"
          fill="#3E2723"
        >
          {nameTr.length > 16 ? nameTr.slice(0, 14) + '...' : nameTr}
        </text>

        {/* Question count */}
        <text
          textAnchor="middle"
          y={28}
          fontSize="9"
          fill="#795548"
        >
          {questionCount} soru
        </text>
      </motion.g>
    </AnimatePresence>
  );
};
```

- [ ] **Step 2: Verify types compile**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/LearningPath/DungeonRoom.tsx
git commit -m "feat(dungeon): add DungeonRoom component with Rough.js 4-level rendering"
```

---

## Task 11: OrganicPath Component

**Files:**
- Create: `frontend/src/components/LearningPath/OrganicPath.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/LearningPath/OrganicPath.tsx`:

```tsx
import React, { useEffect, useRef } from 'react';
import rough from 'roughjs';
import { seededRandom } from '@/types/dungeon';

interface OrganicPathProps {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  fromTopic: string;
  toTopic: string;
  prereqType: 'hard' | 'soft';
}

export const OrganicPath: React.FC<OrganicPathProps> = ({
  fromX,
  fromY,
  toX,
  toY,
  fromTopic,
  toTopic,
  prereqType,
}) => {
  const gRef = useRef<SVGGElement>(null);

  useEffect(() => {
    const g = gRef.current;
    if (!g) return;

    const svg = g.ownerSVGElement;
    if (!svg) return;

    while (g.firstChild) g.removeChild(g.firstChild);

    const rc = rough.svg(svg);
    const seed = seededRandom(`${fromTopic}-${toTopic}`);
    const cx = (fromX + toX) / 2 + (seed - 0.5) * 30;
    const cy = (fromY + toY) / 2;

    const isHard = prereqType === 'hard';
    const pathNode = rc.path(
      `M ${fromX} ${fromY} Q ${cx} ${cy} ${toX} ${toY}`,
      {
        roughness: 1.5,
        stroke: isHard ? '#8B4513' : '#A0A0A0',
        strokeWidth: isHard ? 2 : 1,
      },
    );
    g.appendChild(pathNode);
  }, [fromX, fromY, toX, toY, fromTopic, toTopic, prereqType]);

  return <g ref={gRef} />;
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/LearningPath/OrganicPath.tsx
git commit -m "feat(dungeon): add OrganicPath component with seeded Rough.js Bezier"
```

---

## Task 12: DungeonMap Component (Orchestrator)

**Files:**
- Create: `frontend/src/components/LearningPath/DungeonMap.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/LearningPath/DungeonMap.tsx`:

```tsx
import React, { useState, useCallback } from 'react';
import { useGesture } from '@use-gesture/react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useDungeonMap, type LayoutNode } from '@/hooks/useDungeonMap';
import { fogOpacity } from '@/types/dungeon';
import { ParchmentBackground } from './ParchmentBackground';
import { FogOfWarDefs, FogWrapper } from './FogOfWar';
import { DungeonRoom } from './DungeonRoom';
import { OrganicPath } from './OrganicPath';

interface DungeonMapProps {
  subject: string;
  onNodeClick?: (node: LayoutNode) => void;
}

const SVG_PADDING = 100;

export const DungeonMap: React.FC<DungeonMapProps> = ({
  subject,
  onNodeClick,
}) => {
  const { nodes, edges, theta, loading, error, refetch } = useDungeonMap(subject);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });

  const bind = useGesture({
    onDrag: ({ delta: [dx, dy], event }) => {
      event.preventDefault();
      setTransform((t) => ({ ...t, x: t.x + dx, y: t.y + dy }));
    },
    onPinch: ({ offset: [scale] }) => {
      setTransform((t) => ({
        ...t,
        scale: Math.max(0.3, Math.min(3, scale)),
      }));
    },
  }, {
    drag: { filterTaps: true },
  });

  const handleNodeClick = useCallback(
    (node: LayoutNode) => {
      onNodeClick?.(node);
    },
    [onNodeClick],
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (nodes.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography color="text.secondary">
          Bu ders icin henuz konu bulunamadi.
        </Typography>
      </Box>
    );
  }

  // Compute SVG viewBox from node positions
  const xs = nodes.map((n) => n.x);
  const ys = nodes.map((n) => n.y);
  const minX = Math.min(...xs) - SVG_PADDING;
  const minY = Math.min(...ys) - SVG_PADDING;
  const maxX = Math.max(...xs) + SVG_PADDING;
  const maxY = Math.max(...ys) + SVG_PADDING;
  const width = maxX - minX;
  const height = maxY - minY;

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: 500,
        overflow: 'hidden',
        borderRadius: 2,
        touchAction: 'none',
      }}
    >
      <ParchmentBackground />

      <svg
        {...bind()}
        width="100%"
        height="100%"
        viewBox={`${minX} ${minY} ${width} ${height}`}
        style={{
          position: 'relative',
          zIndex: 1,
          transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
          transformOrigin: 'center center',
        }}
      >
        <defs>
          <FogOfWarDefs />
        </defs>

        {/* Edges (behind rooms) */}
        {edges.map((e) => (
          <OrganicPath
            key={`${e.from_topic}-${e.to_topic}`}
            fromX={e.fromX}
            fromY={e.fromY}
            toX={e.toX}
            toY={e.toY}
            fromTopic={e.from_topic}
            toTopic={e.to_topic}
            prereqType={e.prereq_type}
          />
        ))}

        {/* Rooms */}
        {nodes.map((node) => {
          const fog = fogOpacity(node, theta);
          return (
            <FogWrapper key={node.topic_id} opacity={fog}>
              <DungeonRoom
                topicId={node.topic_id}
                code={node.code}
                nameTr={node.name_tr}
                x={node.x}
                y={node.y}
                progress={node.progress}
                questionCount={node.question_count}
                onClick={() => handleNodeClick(node)}
              />
            </FogWrapper>
          );
        })}
      </svg>
    </Box>
  );
};
```

- [ ] **Step 2: Verify types compile**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/LearningPath/DungeonMap.tsx
git commit -m "feat(dungeon): add DungeonMap orchestrator component with pan/zoom"
```

---

## Task 13: Replace ModernLearningPathVisualizer

**Files:**
- Modify: `frontend/src/pages/ModernLearningPathPage.tsx:909-916`

- [ ] **Step 1: Add import at top of file**

At the top of `frontend/src/pages/ModernLearningPathPage.tsx`, add:

```typescript
import { DungeonMap } from '@/components/LearningPath/DungeonMap';
import type { LayoutNode } from '@/hooks/useDungeonMap';
```

- [ ] **Step 2: Add subject state** (near other useState declarations)

```typescript
const [dungeonSubject, setDungeonSubject] = useState('MATEMATIK');
```

- [ ] **Step 3: Add node click handler** (near other handler functions)

```typescript
const handleDungeonNodeClick = useCallback((node: LayoutNode) => {
  handleNodeClick(node.topic_id);
}, [handleNodeClick]);
```

- [ ] **Step 4: Replace the visualizer** (lines 909-916)

Replace:

```tsx
<ModernLearningPathVisualizer
  nodes={pathNodes}
  connections={pathConnections}
  currentNodeId={currentNodeId}
  onNodeClick={handleNodeClick}
  viewMode="tree"
/>
```

With:

```tsx
<DungeonMap
  subject={dungeonSubject}
  onNodeClick={handleDungeonNodeClick}
/>
```

- [ ] **Step 5: Verify types compile**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 6: Build to ensure no runtime issues**

```bash
cd frontend && npm run build:fast
```

Expected: Build succeeds

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/ModernLearningPathPage.tsx
git commit -m "feat(dungeon): replace ModernLearningPathVisualizer with DungeonMap"
```

---

## Task 14: Frontend Tests

**Files:**
- Create: `frontend/src/types/__tests__/dungeon.test.ts`

- [ ] **Step 1: Create unit tests for utility functions**

Create `frontend/src/types/__tests__/dungeon.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import {
  getRoomLevel,
  seededRandom,
  fogOpacity,
  type DungeonRoom,
  type DungeonProgressData,
} from '../dungeon';

describe('getRoomLevel', () => {
  it('returns 0 when no attempts', () => {
    const p: DungeonProgressData = { attempt_count: 0, best_score: 0, last_score: 0, completed: false };
    expect(getRoomLevel(p)).toBe(0);
  });

  it('returns 1 when attempted but low score', () => {
    const p: DungeonProgressData = { attempt_count: 2, best_score: 30, last_score: 30, completed: false };
    expect(getRoomLevel(p)).toBe(1);
  });

  it('returns 2 when best_score >= 50', () => {
    const p: DungeonProgressData = { attempt_count: 3, best_score: 60, last_score: 40, completed: false };
    expect(getRoomLevel(p)).toBe(2);
  });

  it('returns 3 when completed', () => {
    const p: DungeonProgressData = { attempt_count: 5, best_score: 85, last_score: 85, completed: true };
    expect(getRoomLevel(p)).toBe(3);
  });
});

describe('seededRandom', () => {
  it('returns deterministic value for same seed', () => {
    const a = seededRandom('topic-a-topic-b');
    const b = seededRandom('topic-a-topic-b');
    expect(a).toBe(b);
  });

  it('returns different values for different seeds', () => {
    const a = seededRandom('topic-a-topic-b');
    const c = seededRandom('topic-x-topic-y');
    expect(a).not.toBe(c);
  });

  it('returns value between 0 and 1', () => {
    const v = seededRandom('any-seed');
    expect(v).toBeGreaterThanOrEqual(0);
    expect(v).toBeLessThanOrEqual(1);
  });
});

describe('fogOpacity', () => {
  const makeRoom = (overrides: Partial<DungeonRoom> = {}): DungeonRoom => ({
    topic_id: 'test',
    code: 'TST.01',
    name_tr: 'Test',
    parent_subject: 'TEST',
    prereqs_met: true,
    dag_depth: 0,
    progress: { attempt_count: 0, best_score: 0, last_score: 0, completed: false },
    question_count: 10,
    ...overrides,
  });

  it('returns 0.9 when prereqs not met', () => {
    const room = makeRoom({ prereqs_met: false });
    expect(fogOpacity(room, 0)).toBe(0.9);
  });

  it('returns 0 when completed', () => {
    const room = makeRoom({
      progress: { attempt_count: 5, best_score: 90, last_score: 90, completed: true },
    });
    expect(fogOpacity(room, 0)).toBe(0);
  });

  it('returns lower fog for higher theta', () => {
    const room = makeRoom();
    const lowTheta = fogOpacity(room, -2);
    const highTheta = fogOpacity(room, 2);
    expect(highTheta).toBeLessThan(lowTheta);
  });

  it('returns higher fog for deeper dag_depth', () => {
    const shallow = makeRoom({ dag_depth: 0 });
    const deep = makeRoom({ dag_depth: 5 });
    const theta = 0;
    expect(fogOpacity(deep, theta)).toBeGreaterThan(fogOpacity(shallow, theta));
  });
});
```

- [ ] **Step 2: Run tests**

```bash
cd frontend && npx vitest run src/types/__tests__/dungeon.test.ts
```

Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/__tests__/dungeon.test.ts
git commit -m "test(dungeon): add unit tests for getRoomLevel, seededRandom, fogOpacity"
```

---

## Task 15: Docker Rebuild + E2E Smoke Test

**Files:** None (verification only)

- [ ] **Step 1: Rebuild Docker backend**

```bash
cd C:/Users/husey/kiro2
docker compose build --no-cache backend
docker compose up -d
```

- [ ] **Step 2: Wait for healthy + run seed**

```bash
docker exec kiro2-backend bash -c "cd /app && python scripts/seed_dungeon_topics.py"
```

- [ ] **Step 3: Test endpoint via curl**

```bash
curl -s http://localhost:8000/api/v1/dungeon/MATEMATIK | python -m json.tool | head -30
```

Expected: JSON with `subject`, `theta`, `rooms[]`, `edges[]`

Note: This will return 401 without auth. To test with auth, use the demo login:

```bash
# Login to get session cookie
curl -s -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@kiro2.com","password":"Kiro2Beta2026@x"}'

# Fetch dungeon map
curl -s -b cookies.txt http://localhost:8000/api/v1/dungeon/MATEMATIK | python -m json.tool | head -40
```

- [ ] **Step 4: Rebuild frontend + test in browser**

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

Open `http://localhost:3000`, login with demo credentials, navigate to Learning Path tab. The DungeonMap should render with rooms and connections.

- [ ] **Step 5: Commit any fixes found during E2E**

```bash
git add -A
git commit -m "fix(dungeon): E2E smoke test fixes"
```

---

## Dependency Graph

```
Task 1 (npm install)
  └─→ Task 2 (types) ─→ Task 7 (hook) ─→ Task 12 (DungeonMap) ─→ Task 13 (replace)
                       ├─→ Task 8 (ParchmentBg)─┘
                       ├─→ Task 9 (FogOfWar)─────┘
                       ├─→ Task 10 (DungeonRoom)─┘
                       └─→ Task 11 (OrganicPath)─┘

Task 3 (ORM model) ─→ Task 4 (migration) ─→ Task 5 (seed) ─→ Task 6 (endpoint)

Task 14 (frontend tests) — after Tasks 2+7
Task 15 (E2E) — after all tasks
```

Tasks 1-2 and Tasks 3-5 can run in parallel (frontend vs backend).
