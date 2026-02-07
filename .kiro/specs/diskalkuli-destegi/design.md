# Design Document - Diskalkuli Desteği

## Architecture Overview

Diskalkuli (matematik öğrenme güçlüğü) öğrenciler için erişilebilirlik sistemi. Visual math aids, step-by-step solutions, interactive tools ile %40 math confidence artışı sağlar.

## Components

### 1. Visual Math Renderer (frontend/src/features/math/VisualMath.tsx)
- **Purpose**: Görsel matematik temsili
- **Dependencies**: katex>=0.16.0, d3.js>=7.8.0
- **Key Features**:
  - Dot patterns, tally marks, number lines
  - Pie charts, bar models (fractions)
  - Interactive shapes (geometry)
  - Color-coded graphs
  - Customizable size/color/style

### 2. Step-by-Step Solver (app/services/math/step_solver_service.py)
- **Purpose**: Adım adım çözüm
- **Dependencies**: sympy>=1.12.0
- **Key Features**:
  - Each step separate display
  - "Why this step" explanations
  - Navigation (previous, next, jump)
  - Current step highlighting
  - TTS integration
  - Guided practice mode

### 3. Interactive Math Tools (frontend/src/features/math/InteractiveTools.tsx)
- **Purpose**: Somut deneyim
- **Dependencies**: fabric.js>=5.3.0
- **Key Features**:
  - Virtual manipulatives (base-10 blocks, counters, fraction bars)
  - Draggable number line (zoom, labels)
  - Large button calculator (history)
  - Interactive graph tool (plotting, zoom, pan)
  - Equation solver (step-by-step)
  - Keyboard navigation, screen reader support

### 4. Multi-Sensory Engine (frontend/src/features/math/MultiSensory.tsx)
- **Purpose**: Farklı duyularla öğrenme
- **Dependencies**: howler.js>=2.2.0
- **Key Features**:
  - Audio feedback (correct/incorrect sounds)
  - Haptic feedback (mobile vibration)
  - Color coding (operation types)
  - Concept animations
  - Rhythm-based learning (counting rhythm, pattern music)
  - Visual + audio + tactile integration

### 5. Scaffolded Practice Manager (app/services/math/scaffolded_practice_service.py)
- **Purpose**: Kademeli öğrenme
- **Dependencies**: None
- **Key Features**:
  - Start with easy problems
  - Adaptive difficulty
  - Progressive hint system
  - Partial credit (recognize correct steps)
  - Mastery check (3 consecutive correct)
  - Encouraging, specific feedback

### 6. Anxiety Reducer (frontend/src/features/math/AnxietyReduction.tsx)
- **Purpose**: Matematik kaygısı azaltma
- **Dependencies**: None
- **Key Features**:
  - Untimed mode
  - Non-judgmental feedback
  - Positive reinforcement
  - Periodic rest suggestions
  - Stress level monitoring → auto difficulty adjust
  - Growth mindset promotion (effort-based praise)

### 7. Number Sense Developer (app/services/math/number_sense_service.py)
- **Purpose**: Sayı kavramı geliştirme
- **Dependencies**: None
- **Key Features**:
  - Visual magnitude representation (comparison)
  - Reasonable range feedback (estimation)
  - Base-10 block visualization (place value)
  - Strategy suggestions (mental math)
  - Visual pattern highlighting
  - Spaced repetition (fluency)

### 8. Progress Monitor (app/services/math/progress_monitor_service.py)
- **Purpose**: Gelişim takibi
- **Dependencies**: matplotlib>=3.8.0
- **Key Features**:
  - Per-concept progress tracking
  - Skill heatmap (strength/weakness)
  - Timeline chart (growth visualization)
  - Achievable milestones
  - Parent/teacher dashboard
  - Targeted practice recommendations

## Correctness Properties

### Property 1: Visual Representation Accuracy
```python
@given(number=st.integers(min_value=0, max_value=100))
def test_visual_accuracy(number):
    visual = visual_math.render(number)
    assert visual.count_elements() == number
```

### Property 2: Step-by-Step Completeness
```python
@given(problem=st.text())
def test_step_completeness(problem):
    steps = step_solver.solve(problem)
    assert all(step.has_explanation() for step in steps)
```

### Property 3: Difficulty Progression
```python
@given(student_level=st.integers(min_value=1, max_value=10))
def test_difficulty_progression(student_level):
    problems = scaffolded_practice.generate(student_level)
    difficulties = [p.difficulty for p in problems]
    assert difficulties == sorted(difficulties)
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Feature adoption | >= 50% | >= 35% |
| Math confidence improvement | >= 40% | >= 25% |
| Problem solving accuracy | >= 30% increase | >= 20% increase |
| Math anxiety reduction | >= 35% | >= 20% |

## Monitoring

- Feature usage (%)
- Math confidence score
- Problem solving accuracy (%)
- Math anxiety level
- User engagement (%)
