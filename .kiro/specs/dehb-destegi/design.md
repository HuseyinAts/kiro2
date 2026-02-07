# Design Document - DEHB Desteği

## Architecture Overview

DEHB (Dikkat Eksikliği Hiperaktivite Bozukluğu) öğrenciler için erişilebilirlik sistemi. Focus mode, Pomodoro, gamification, attention monitoring ile %50 focus iyileşmesi sağlar.

## Components

### 1. Focus Mode Manager (frontend/src/features/accessibility/FocusMode.tsx)
- **Purpose**: Dikkat dağıtıcı önleme
- **Dependencies**: react>=18.0.0
- **Key Features**:
  - Distraction-free interface
  - Notification suspension
  - Minimal UI (essential elements only)
  - Background noise (white noise, ambient)
  - Focus timer (countdown)
  - Completion celebration

### 2. Pomodoro Timer (frontend/src/features/accessibility/PomodoroTimer.tsx)
- **Purpose**: Zaman yönetimi
- **Dependencies**: react-timer-hook>=3.0.0
- **Key Features**:
  - 25 min work + 5 min break cycle
  - Customizable durations
  - Gentle notifications + sound
  - Long break (15-30 min after 4 cycles)
  - Pause/resume
  - Daily/weekly tracking

### 3. Task Chunker (app/services/task_chunking_service.py)
- **Purpose**: Büyük görevleri parçalama
- **Dependencies**: None
- **Key Features**:
  - Automatic sub-task breakdown
  - 5-15 min duration targeting
  - Visual progress bar
  - Immediate positive feedback
  - Priority-based ordering
  - Overwhelm detection

### 4. Gamification Engine (app/services/gamification_service.py)
- **Purpose**: Motivasyon artırma
- **Dependencies**: None
- **Key Features**:
  - Point system (task completion)
  - Badge/achievement unlocking
  - Streak tracking (consecutive days)
  - Optional leaderboard
  - Progressive difficulty
  - Personalized rewards

### 5. Attention Monitor (app/services/attention_monitor_service.py)
- **Purpose**: Dikkat durumu tracking
- **Dependencies**: pandas>=2.2.0
- **Key Features**:
  - Engagement pattern analysis
  - Attention drift detection
  - Optimal focus time identification
  - Fatigue detection
  - Average focus duration calculation
  - Pattern visualization

### 6. Hyperactivity Accommodator (frontend/src/features/accessibility/HyperactivityTools.tsx)
- **Purpose**: Enerji yönetimi
- **Dependencies**: framer-motion>=10.0.0
- **Key Features**:
  - Movement break reminders
  - Interactive widgets (spinner, clicker)
  - Sit/stand reminders
  - Kinesthetic activities
  - Energy level tracking
  - Gesture-based interaction

### 7. Impulsivity Manager (frontend/src/features/accessibility/ImpulsivityControl.tsx)
- **Purpose**: Düşünerek karar verme
- **Dependencies**: None
- **Key Features**:
  - "Pause and think" prompts
  - Review reminders
  - Easy undo option
  - "Are you sure?" confirmations
  - Stop-think-act framework
  - Awareness feedback

### 8. Learning Pace Adapter (app/services/learning_pace_service.py)
- **Purpose**: Kişiselleştirilmiş hız
- **Dependencies**: None
- **Key Features**:
  - Adaptive speed
  - Bite-sized lessons
  - Spaced repetition optimization
  - Skip option (known content)
  - Too fast/slow indicators
  - Optimal learning time identification

## Correctness Properties

### Property 1: Focus Session Completeness
```python
@given(duration=st.integers(min_value=1, max_value=60))
def test_focus_session(duration):
    session = focus_mode.start(duration)
    assert session.has_timer() and session.has_celebration()
```

### Property 2: Pomodoro Cycle Consistency
```python
@given(cycles=st.integers(min_value=1, max_value=10))
def test_pomodoro_cycles(cycles):
    completed = pomodoro.run_cycles(cycles)
    assert len(completed) == cycles
```

### Property 3: Task Chunking Size
```python
@given(task=st.text(min_size=100))
def test_task_chunking(task):
    subtasks = task_chunker.chunk(task)
    assert all(5 <= st.duration <= 15 for st in subtasks)
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Feature adoption | >= 65% | >= 50% |
| Focus duration improvement | >= 50% | >= 30% |
| Task completion rate | >= 40% increase | >= 25% increase |
| User engagement | >= 80% | >= 60% |

## Monitoring

- Feature usage (%)
- Focus session duration (min)
- Task completion rate (%)
- Pomodoro completion count
- User satisfaction score
