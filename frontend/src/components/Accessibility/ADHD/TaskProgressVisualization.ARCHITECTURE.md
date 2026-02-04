# Task Progress Visualization - Architecture

## Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                TaskProgressVisualization                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Progress Header                        │    │
│  │  ┌──────────────────┐  ┌──────────────────┐       │    │
│  │  │   Task Title     │  │  Status Badge    │       │    │
│  │  └──────────────────┘  └──────────────────┘       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Progress Section (REQ-52.46)             │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │  Progress Label        60%               │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │ ████████████████░░░░░░░░░░░░░░░░░░░░░░  │     │    │
│  │  │        Progress Bar with Shine           │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │        Subtasks Section (REQ-52.47)                │    │
│  │  ✓  3 / 5 alt görev tamamlandı                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │        Milestones Section (REQ-52.48)              │    │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐          │    │
│  │  │  🚀  │  │  ⚡  │  │  🎯  │  │  🎉  │          │    │
│  │  │ 25%  │  │ 50%  │  │ 75%  │  │ 100% │          │    │
│  │  │  ✓   │  │  ✓   │  │      │  │      │          │    │
│  │  └──────┘  └──────┘  └──────┘  └──────┘          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Time Section                             │    │
│  │  Tahmini: 2h 0m  |  Geçen: 1h 15m  |  Kalan: 45m  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Actions                                  │    │
│  │  [ 🔄 Yenile ]  [ Görevi Görüntüle ]              │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│   Browser    │
└──────┬───────┘
       │
       │ 1. Component Mount
       ▼
┌──────────────────────────┐
│ TaskProgressVisualization│
│                          │
│  useEffect(() => {       │
│    fetchProgressData()   │
│  }, [taskId])           │
└──────┬───────────────────┘
       │
       │ 2. API Request
       ▼
┌──────────────────────────────────────┐
│  GET /api/adhd-task-management/      │
│      tasks/{taskId}/progress         │
│                                      │
│  Headers:                            │
│    Authorization: Bearer {token}     │
└──────┬───────────────────────────────┘
       │
       │ 3. Response
       ▼
┌──────────────────────────┐
│  ProgressVisualizationData│
│  {                       │
│    task_id,              │
│    title,                │
│    progress_percentage,  │
│    completed_subtasks,   │
│    total_subtasks,       │
│    milestones,           │
│    ...                   │
│  }                       │
└──────┬───────────────────┘
       │
       │ 4. State Update
       ▼
┌──────────────────────────┐
│  setProgressData(data)   │
│  setAnimatedProgress()   │
└──────┬───────────────────┘
       │
       │ 5. Render
       ▼
┌──────────────────────────┐
│   Visual Components      │
│   - Progress Bar         │
│   - Milestones           │
│   - Time Tracking        │
└──────────────────────────┘
```

## State Management

```typescript
// Component State
const [progressData, setProgressData] = useState<ProgressVisualizationData | null>(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [animatedProgress, setAnimatedProgress] = useState(0);

// State Transitions
┌─────────────┐
│   Initial   │
│ loading=true│
└──────┬──────┘
       │
       ├─── Success ───┐
       │               ▼
       │        ┌──────────────┐
       │        │   Loaded     │
       │        │ loading=false│
       │        │ data=present │
       │        └──────────────┘
       │
       └─── Error ────┐
                      ▼
               ┌──────────────┐
               │    Error     │
               │ loading=false│
               │ error=message│
               └──────────────┘
```

## Animation Timeline

```
Progress Bar Animation (1s)
├─ 0ms:   width: 0%
├─ 100ms: Delay before animation starts
├─ 1100ms: width: {progress_percentage}%
└─ Shine effect loops every 2s

Milestone Pulse (1.5s infinite)
├─ 0ms:    scale(1)
├─ 750ms:  scale(1.1)
└─ 1500ms: scale(1)

Checkmark Appear (0.5s)
├─ 0ms:   scale(0) rotate(-180deg) opacity(0)
└─ 500ms: scale(1) rotate(0deg) opacity(1)
```

## CSS Architecture

```
TaskProgressVisualization.css
├─ Layout
│  ├─ .task-progress-visualization (container)
│  ├─ .progress-header (flex)
│  ├─ .progress-section (block)
│  ├─ .subtasks-section (block)
│  ├─ .milestones-section (grid)
│  ├─ .time-section (grid)
│  └─ .progress-actions (flex)
│
├─ Components
│  ├─ Progress Bar
│  │  ├─ .progress-bar-container
│  │  ├─ .progress-bar-fill
│  │  └─ .progress-bar-shine
│  │
│  ├─ Milestones
│  │  ├─ .milestone
│  │  ├─ .milestone-icon
│  │  ├─ .milestone-info
│  │  └─ .milestone-checkmark
│  │
│  └─ Time Tracking
│     ├─ .time-grid
│     ├─ .time-item
│     └─ .time-value
│
├─ States
│  ├─ Loading (.task-progress-loading)
│  ├─ Error (.task-progress-error)
│  └─ Success (default)
│
├─ Animations
│  ├─ @keyframes shine
│  ├─ @keyframes pulse
│  ├─ @keyframes checkmark-appear
│  └─ @keyframes spin
│
└─ Media Queries
   ├─ @media (max-width: 768px)
   ├─ @media (prefers-contrast: high)
   └─ @media (prefers-reduced-motion: reduce)
```

## Component Lifecycle

```
1. Mount
   ├─ useEffect(() => fetchProgressData(), [taskId])
   └─ Initial render with loading state

2. Data Fetch
   ├─ API call to backend
   ├─ Loading state displayed
   └─ Spinner animation

3. Data Received
   ├─ setProgressData(data)
   ├─ setLoading(false)
   └─ Trigger progress animation

4. Animation
   ├─ setTimeout(() => setAnimatedProgress(progress), 100)
   └─ CSS transition animates progress bar

5. User Interaction
   ├─ Refresh button → fetchProgressData()
   └─ Custom action → onRefresh callback

6. Unmount
   └─ Cleanup timers and event listeners
```

## Accessibility Tree

```
TaskProgressVisualization
├─ heading (h3) "Matematik Sınavına Hazırlan"
├─ status "Devam Ediyor"
├─ group "Genel İlerleme"
│  ├─ text "60%"
│  └─ progressbar
│     ├─ role="progressbar"
│     ├─ aria-valuenow="60"
│     ├─ aria-valuemin="0"
│     ├─ aria-valuemax="100"
│     └─ aria-label="Görev ilerleme yüzdesi: 60%"
├─ group "Alt Görevler"
│  └─ text "3 / 5 alt görev tamamlandı"
├─ group "Kilometre Taşları"
│  ├─ article "Başlangıç - 25%"
│  ├─ article "Yarı Yol - 50%"
│  ├─ article "Son Çeyrek - 75%"
│  └─ article "Tamamlandı - 100%"
├─ group "Zaman Takibi"
│  ├─ text "Tahmini Süre: 2 saat 0 dakika"
│  ├─ text "Geçen Süre: 1 saat 15 dakika"
│  └─ text "Kalan Süre: 45 dakika"
└─ group "Actions"
   ├─ button "Yenile" aria-label="İlerlemeyi yenile"
   └─ button "Görevi Görüntüle"
```

## Performance Optimization

```
Optimization Strategies
├─ CSS Animations (GPU-accelerated)
│  ├─ transform (instead of left/top)
│  ├─ opacity (instead of visibility)
│  └─ will-change property
│
├─ React Optimization
│  ├─ useState for local state
│  ├─ useEffect with dependencies
│  └─ Conditional rendering
│
├─ API Optimization
│  ├─ Single API call on mount
│  ├─ Manual refresh only
│  └─ Error retry mechanism
│
└─ Bundle Optimization
   ├─ CSS in separate file
   ├─ No external dependencies
   └─ Tree-shakeable exports
```

## Error Handling Flow

```
┌─────────────┐
│ API Request │
└──────┬──────┘
       │
       ├─── Success ───┐
       │               ▼
       │        ┌──────────────┐
       │        │ Display Data │
       │        └──────────────┘
       │
       └─── Error ────┐
                      ▼
               ┌──────────────────┐
               │ Catch Error      │
               │ setError(message)│
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Display Error UI │
               │ - Error message  │
               │ - Retry button   │
               └────────┬─────────┘
                        │
                        │ User clicks retry
                        ▼
               ┌──────────────────┐
               │ fetchProgressData│
               └──────────────────┘
```

## Responsive Breakpoints

```
Desktop (> 768px)
├─ 4-column milestone grid
├─ Full-width progress bar
├─ Horizontal time layout
└─ 24px padding

Mobile (≤ 768px)
├─ 2-column milestone grid
├─ Full-width progress bar
├─ Vertical time layout
├─ 16px padding
└─ Smaller fonts
   ├─ Title: 18px (from 20px)
   └─ Percentage: 20px (from 24px)
```

## Integration Points

```
TaskProgressVisualization
├─ Backend API
│  └─ GET /api/adhd-task-management/tasks/{taskId}/progress
│
├─ Authentication
│  └─ localStorage.getItem('token')
│
├─ Parent Components
│  ├─ Dashboard
│  ├─ Task List
│  └─ Student Profile
│
└─ Related Components
   ├─ VisualTimer (Pomodoro)
   ├─ FocusMode (Distraction-free)
   └─ TaskDecomposition (Task breakdown)
```

---

**Architecture Version**: 1.0  
**Last Updated**: 24 Ekim 2025  
**Status**: Production Ready
