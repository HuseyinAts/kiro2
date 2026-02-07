# Design Document - Claude Diary Plugin

## Architecture Overview

Agent günlük tutma ve reflection sistemi. Daily summary, insight extraction, learning journal, emotional tracking ile sürekli öğrenme ve self-awareness sağlar.

## Components

### 1. Daily Summary Generator (backend/services/diary_service.py)
- **Purpose**: Günlük aktivite özeti
- **Dependencies**: schedule>=1.2.0
- **Key Features**:
  - Task aggregation (success/failure count)
  - Key learnings extraction
  - Highlight selection (most impactful)
  - Challenge logging
  - Markdown formatting
  - Persist to .kiro/diary/YYYY-MM-DD.md

### 2. Insight Extractor (backend/services/insight_service.py)
- **Purpose**: Pattern detection ve insight generation
- **Dependencies**: scikit-learn>=1.4.0
- **Key Features**:
  - Success pattern analysis
  - Failure root cause identification
  - Correlation detection
  - Confidence scoring (>= 0.8)
  - Actionable recommendations
  - Categorization (technical, process, communication)

### 3. Reflection Prompter (backend/services/reflection_service.py)
- **Purpose**: Guided reflection questions
- **Dependencies**: None
- **Key Features**:
  - "What went well?" analysis
  - "What could improve?" identification
  - "What did I learn?" extraction
  - "What will I do differently?" planning
  - Depth measurement (surface vs deep)

### 4. Learning Journal (backend/services/learning_journal_service.py)
- **Purpose**: Knowledge tracking
- **Dependencies**: networkx>=3.2.0
- **Key Features**:
  - Knowledge entry creation
  - Categorization (domain, skill, tool tags)
  - Concept linking (knowledge graph)
  - Spaced repetition scheduling
  - Gap detection
  - Interactive visualization

### 5. Emotional Tracker (backend/services/emotional_service.py)
- **Purpose**: Agent state awareness
- **Dependencies**: matplotlib>=3.8.0
- **Key Features**:
  - Confidence level tracking (1-10)
  - Frustration detection (retry count, error frequency)
  - Flow state identification (high productivity periods)
  - Trigger factor analysis
  - Mood trend visualization
  - Self-awareness scoring

### 6. Goal Tracker (backend/services/goal_service.py)
- **Purpose**: Progress monitoring
- **Dependencies**: None
- **Key Features**:
  - SMART criteria validation
  - Progress percentage calculation
  - Milestone celebration
  - Risk detection (early warning)
  - Goal adjustment tracking
  - Retrospective lessons learned

### 7. Peer Comparator (backend/services/peer_comparison_service.py)
- **Purpose**: Performance benchmarking
- **Dependencies**: None
- **Key Features**:
  - Anonymized peer data
  - Percentile calculation (success rate, speed, quality)
  - Strength area highlighting (top 25%)
  - Improvement area identification (bottom 25%)
  - Best practice learning
  - Differential privacy

### 8. Export Manager (backend/services/export_service.py)
- **Purpose**: Diary export ve sharing
- **Dependencies**: reportlab>=4.0.0, cryptography>=41.0.0
- **Key Features**:
  - Format support (markdown, PDF, JSON)
  - Date range filtering
  - Privacy redaction
  - Read-only sharing links
  - Customizable templates
  - Encrypted backup

## Data Flow

```
Task Completion → DiarySummary → InsightExtraction → ReflectionPrompts
                       ↓
                 LearningJournal
                       ↓
                 EmotionalTracking
                       ↓
                   GoalTracking
                       ↓
                 PeerComparison
                       ↓
                  ExportManager
```

## Correctness Properties

### Property 1: Summary Completeness
```python
@given(tasks=st.lists(st.dictionaries(
    keys=st.sampled_from(['status', 'duration', 'type']),
    values=st.text()
)))
def test_summary_completeness(tasks):
    summary = diary_service.generate_summary(tasks)
    assert 'success_count' in summary and 'failure_count' in summary
```

### Property 2: Insight Confidence
```python
@given(pattern_data=st.lists(st.floats(min_value=0, max_value=1)))
def test_insight_confidence(pattern_data):
    insights = insight_service.extract(pattern_data)
    assert all(i['confidence'] >= 0.8 for i in insights)
```

### Property 3: Goal Progress Monotonicity
```python
@given(progress_updates=st.lists(st.integers(min_value=0, max_value=100)))
def test_goal_progress_monotonic(progress_updates):
    for i in range(1, len(progress_updates)):
        assert progress_updates[i] >= progress_updates[i-1]
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Summary generation | < 5s | < 10s |
| Insight extraction | < 10s | < 20s |
| Knowledge graph query | < 2s | < 5s |
| Export generation | < 30s | < 60s |

## Security Considerations

- Sensitive data redaction (PII, credentials)
- Encrypted storage (AES-256)
- Access control (read-only sharing)
- Audit logging

## Monitoring

- Daily entry completion rate (%)
- Insight quality score (%)
- Learning retention rate (%)
- Goal achievement rate (%)
- User engagement (%)

## Pydantic Schemas (backend/api/schemas/diary.py)

### DiaryEntryCreate
```python
class DiaryEntryCreate(BaseModel):
    date: datetime
    tasks: List[TaskSummary]
    notes: Optional[str] = None

class DiaryEntryResponse(BaseModel):
    id: UUID
    date: datetime
    success_count: int
    failure_count: int
    highlights: List[str]
    learnings: List[str]
    challenges: List[str]
    created_at: datetime
```

### InsightResponse
```python
class InsightResponse(BaseModel):
    insight_id: UUID
    confidence: float  # >= 0.8
    category: Literal["technical", "process", "communication"]
    pattern: str
    recommendation: str
    evidence_count: int
```

### GoalCreate
```python
class GoalCreate(BaseModel):
    title: str
    description: str
    target_date: datetime
    milestones: List[MilestoneCreate]

class GoalResponse(BaseModel):
    id: UUID
    title: str
    progress: int  # 0-100
    status: Literal["active", "completed", "at_risk", "cancelled"]
    milestones: List[MilestoneResponse]
```

### LearningEntryCreate
```python
class LearningEntryCreate(BaseModel):
    content: str
    tags: List[str]  # domain, skill, tool
    related_concepts: List[str]

class LearningEntryResponse(BaseModel):
    id: UUID
    content: str
    tags: List[str]
    next_review: datetime  # spaced repetition
    retention_score: float
```

## Database Models (backend/models/diary.py)

### DiaryEntry (SQLAlchemy)
```python
class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    date: Mapped[date] = mapped_column(unique=True, index=True)
    content: Mapped[dict] = mapped_column(JSON)
    success_count: Mapped[int] = mapped_column(default=0)
    failure_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    insights: Mapped[List["Insight"]] = relationship(back_populates="diary_entry")
```

### Insight
```python
class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    diary_entry_id: Mapped[UUID] = mapped_column(ForeignKey("diary_entries.id"))
    category: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column()
    pattern: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)

    diary_entry: Mapped["DiaryEntry"] = relationship(back_populates="insights")
```

### Goal
```python
class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    status: Mapped[str] = mapped_column(String(20), default="active")
    target_date: Mapped[datetime] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### LearningEntry
```python
class LearningEntry(Base):
    __tablename__ = "learning_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))
    next_review: Mapped[datetime] = mapped_column()
    retention_score: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### EmotionalState
```python
class EmotionalState(Base):
    __tablename__ = "emotional_states"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(default=func.now())
    confidence_level: Mapped[int] = mapped_column()  # 1-10
    frustration_score: Mapped[float] = mapped_column(default=0.0)
    flow_state: Mapped[bool] = mapped_column(default=False)
    trigger_factors: Mapped[dict] = mapped_column(JSON, nullable=True)
```

## API Endpoints (backend/api/diary_api.py)

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/api/v1/diary/summary` | GET | Belirli tarih icin ozet | `?date=YYYY-MM-DD` | DiaryEntryResponse |
| `/api/v1/diary/summary` | POST | Manuel ozet olustur | DiaryEntryCreate | DiaryEntryResponse |
| `/api/v1/diary/summary/today` | GET | Bugunun ozeti | - | DiaryEntryResponse |
| `/api/v1/diary/insights` | GET | Icgoruleri listele | `?category=&limit=` | List[InsightResponse] |
| `/api/v1/diary/reflection` | POST | Yansitma kaydet | ReflectionCreate | ReflectionResponse |
| `/api/v1/diary/reflection/prompts` | GET | Rehberli sorular | - | List[str] |
| `/api/v1/diary/learning` | GET | Ogrenme gunlugu | `?tag=&limit=` | List[LearningEntryResponse] |
| `/api/v1/diary/learning` | POST | Yeni kayit | LearningEntryCreate | LearningEntryResponse |
| `/api/v1/diary/learning/review` | GET | Review gereken kanitlar | - | List[LearningEntryResponse] |
| `/api/v1/diary/goals` | GET | Hedefleri listele | `?status=` | List[GoalResponse] |
| `/api/v1/diary/goals` | POST | Yeni hedef | GoalCreate | GoalResponse |
| `/api/v1/diary/goals/{id}` | PUT | Hedef guncelle | GoalUpdate | GoalResponse |
| `/api/v1/diary/goals/{id}/progress` | PATCH | Ilerleme guncelle | `{progress: int}` | GoalResponse |
| `/api/v1/diary/emotional` | GET | Duygusal durum | `?from=&to=` | List[EmotionalState] |
| `/api/v1/diary/emotional` | POST | Durum kaydet | EmotionalStateCreate | EmotionalState |
| `/api/v1/diary/export` | GET | Disa aktar | `?format=&from=&to=` | File |
| `/api/v1/diary/export/share` | POST | Paylasim linki | ShareCreate | ShareResponse |
