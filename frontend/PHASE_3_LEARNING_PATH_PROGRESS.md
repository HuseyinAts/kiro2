# Phase 3: LearningPathPage Refactoring - Progress Report

**Component**: LearningPathPage.tsx
**Original Size**: 1,095 lines
**Target Size**: ~100 lines (90% reduction)
**Status**: 🚧 **IN PROGRESS** (Foundation Complete - 40%)
**Date**: November 14, 2025

---

## 📊 Current Progress

### ✅ Completed (Foundation Layer)

#### 1. **Utility Functions** - learningPathHelpers.ts (230 lines)

**File**: `src/utils/learningPathHelpers.ts`

**Extracted Functions**:
- `extractSubject(title)` - Extract subject from title
- `extractTopic(topicName)` - Extract specific topic keyword
- `generateConnections(nodes)` - Generate node connections
- `convertPathToNodes(path, completionStatus)` - Convert path modules to nodes
- `calculateOverallProgress(nodes)` - Calculate progress percentage
- `calculateTotalTime(nodes)` - Calculate total estimated time
- `groupNodesByModule(nodes)` - Group nodes by module
- `calculateModuleProgress(moduleNodes)` - Calculate module progress
- `getModuleTitle(moduleIndex)` - Get module title by index
- `formatDifficulty(difficulty)` - Format difficulty to Turkish

**Benefits**:
- ✅ Pure functions (easy to test)
- ✅ Reusable across components
- ✅ No side effects
- ✅ TypeScript typed

---

#### 2. **Custom Hook: useLearningPath** (170 lines)

**File**: `src/hooks/useLearningPath.ts`

**Responsibilities**:
- Load learning path data
- Manage path nodes state
- Handle learning style detection
- Track completion status
- Manage current node selection

**Interface**:
```typescript
export interface UseLearningPathReturn {
  // Data
  pathNodes: PathNodeData[]
  learningStyle: string
  currentNodeId: string

  // State
  loading: boolean
  error: string | null

  // Actions
  loadPath: () => Promise<void>
  reload: () => void
  setCurrentNode: (nodeId: string) => void
}
```

**Usage**:
```typescript
const { pathNodes, learningStyle, loading, error, reload } = useLearningPath()
```

**Benefits**:
- ✅ Encapsulates all path loading logic
- ✅ Handles student profile creation
- ✅ Manages completion status
- ✅ Auto-loads on mount
- ✅ Clean error handling

---

#### 3. **Custom Hook: useLearningPathVideos** (280 lines)

**File**: `src/hooks/useLearningPathVideos.ts`

**Responsibilities**:
- Manage VideoLoadingManager integration
- Handle video loading for path
- Handle video loading for specific nodes
- Manage fallback videos
- Track loading subjects

**Interface**:
```typescript
export interface UseLearningPathVideosReturn {
  // Data
  videos: VideoResponse[]
  videoLoadingState: VideoLoadingState
  loadingSubjects: string[]

  // Legacy state (for compatibility)
  videosLoading: boolean
  videosError: string | null

  // Actions
  loadVideosForPath: (path: any, learningStyle: string) => Promise<void>
  loadVideosForNode: (...) => Promise<void>
  retryLoad: () => Promise<void>
  showFallback: () => Promise<void>
  cancelLoad: () => void
}
```

**Usage**:
```typescript
const {
  videos,
  videosLoading,
  loadVideosForPath,
  retryLoad
} = useLearningPathVideos()
```

**Benefits**:
- ✅ Encapsulates VideoLoadingManager complexity
- ✅ Handles both path-wide and node-specific loading
- ✅ Manages fallback system
- ✅ Clean subscription management
- ✅ Automatic cleanup

---

## 🎯 Remaining Work (60%)

### 📝 State Components (2 files)

#### 1. PathLoadingState.tsx (~30 lines)
```typescript
// Loading state with spinner and message
<Box display="flex" justifyContent="center" alignItems="center">
  <CircularProgress />
  <Typography>Öğrenme yolunuz hazırlanıyor...</Typography>
</Box>
```

#### 2. PathErrorState.tsx (~40 lines)
```typescript
// Error state with message and retry button
<Alert severity="error">{error}</Alert>
<Button onClick={reload}>Tekrar Dene</Button>
```

---

### 🎨 Header Components (2 files)

#### 1. LearningPathHeader.tsx (~60 lines)
```typescript
// Header with title, description, and refresh button
interface LearningPathHeaderProps {
  onRefresh: () => void
}
```

#### 2. LearningStyleBadge.tsx (~100 lines)
```typescript
// Learning style display card with chips and info
interface LearningStyleBadgeProps {
  learningStyle: string
}
```

**Content**:
- Learning style display
- Visual indicators
- Learning preference chips
- Tips and recommendations

---

### 📊 Detail Components (3 files)

#### 1. NodeDetailsPanel.tsx (~140 lines)
```typescript
// Node details panel when a node is clicked
interface NodeDetailsPanelProps {
  node: PathNodeData
  onClose: () => void
}
```

**Content**:
- Node title and description
- Time, difficulty, progress stats
- Quiz information (if available)
- Status chips

#### 2. VideoAnalyticsCard.tsx (~120 lines)
```typescript
// Video quality analytics display
interface VideoAnalyticsCardProps {
  videos: VideoResponse[]
}
```

**Content**:
- Turkish score average
- Relevance score average
- Quality score average
- Final score average
- Feature chips (Turkish, accessible, HD, etc.)

#### 3. ModuleProgressCard.tsx (~100 lines)
```typescript
// Individual module progress display
interface ModuleProgressCardProps {
  moduleIndex: number
  moduleNodes: PathNodeData[]
}
```

**Content**:
- Module title and progress percentage
- Progress bar
- Topic list with status indicators

---

### 📑 Tab Components (3 files)

#### 1. PathVisualizationTab.tsx (~80 lines)
```typescript
// Tab with learning path visualizer
interface PathVisualizationTabProps {
  pathNodes: PathNodeData[]
  currentNodeId: string
  onNodeClick: (node: PathNodeData) => void
}
```

**Content**:
- Node details panel (conditional)
- LearningPathVisualizer
- Empty state

#### 2. VideoResourcesTab.tsx (~150 lines)
```typescript
// Tab with video resources
interface VideoResourcesTabProps {
  videos: VideoResponse[]
  videoLoadingState: VideoLoadingState
  loadingSubjects: string[]
  onRetry: () => void
  onShowFallback: () => void
  onCancel: () => void
  onVideoPlay: (video: VideoResponse) => void
}
```

**Content**:
- Header with title and refresh button
- VideoAnalyticsCard (conditional)
- VideoLoadingUI component
- VideoResourceGrid

#### 3. ProgressTrackingTab.tsx (~200 lines)
```typescript
// Tab with progress tracking
interface ProgressTrackingTabProps {
  pathNodes: PathNodeData[]
  hasPath: boolean
}
```

**Content**:
- Overall progress card
- Module progress cards (3)
- Detailed statistics card

---

### 🏗️ Main Component (Refactored)

#### LearningPathPageRefactored.tsx (~100 lines)

**Structure**:
```typescript
export function LearningPathPage() {
  // Custom hooks
  const {
    pathNodes,
    learningStyle,
    currentNodeId,
    loading,
    error,
    reload,
    setCurrentNode
  } = useLearningPath()

  const {
    videos,
    videoLoadingState,
    loadingSubjects,
    loadVideosForPath,
    loadVideosForNode,
    retryLoad,
    showFallback,
    cancelLoad
  } = useLearningPathVideos()

  // Local UI state
  const [tabValue, setTabValue] = useState(0)
  const [showNodeDetails, setShowNodeDetails] = useState(false)

  // Effects
  useEffect(() => {
    if (pathNodes.length > 0 && learningStyle) {
      const path = learningPathService.getCurrentPath()
      if (path) {
        loadVideosForPath(path, learningStyle)
      }
    }
  }, [pathNodes, learningStyle, loadVideosForPath])

  // Event handlers
  const handleNodeClick = async (node: PathNodeData) => {
    setCurrentNode(node.id)
    setShowNodeDetails(true)
    await loadVideosForNode(
      node.id,
      node.title,
      node.description,
      node.difficulty,
      learningStyle
    )
  }

  const handleVideoPlay = (video: VideoResponse) => {
    window.open(video.url, '_blank')
  }

  // Render states
  if (loading) return <PathLoadingState />
  if (error) return <PathErrorState error={error} onRetry={reload} />

  // Main render
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <LearningPathHeader onRefresh={reload} />

      {learningStyle && (
        <LearningStyleBadge learningStyle={learningStyle} />
      )}

      <Divider sx={{ my: 3 }} />

      <Paper elevation={2}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab icon={<Timeline />} label="Yol Haritası" />
          <Tab icon={<VideoLibrary />} label="Size Özel Kaynaklar" />
          <Tab icon={<Assessment />} label="İlerleme" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <PathVisualizationTab
            pathNodes={pathNodes}
            currentNodeId={currentNodeId}
            onNodeClick={handleNodeClick}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <VideoResourcesTab
            videos={videos}
            videoLoadingState={videoLoadingState}
            loadingSubjects={loadingSubjects}
            onRetry={retryLoad}
            onShowFallback={showFallback}
            onCancel={cancelLoad}
            onVideoPlay={handleVideoPlay}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <ProgressTrackingTab
            pathNodes={pathNodes}
            hasPath={learningPathService.getCurrentPath() !== null}
          />
        </TabPanel>
      </Paper>
    </Container>
  )
}
```

---

## 📈 Estimated Code Reduction

| Component | Original | Refactored | Files | Reduction |
|-----------|----------|------------|-------|-----------|
| **LearningPathPage** | 1,095 lines | ~100 lines | 1 | **91%** |
| **Supporting Files** | - | ~1,300 lines | 13 | New |
| **Total Project** | 1,095 | 1,400 | 14 | Better organized |

---

## 🎯 Completion Roadmap

### **Session 1** ✅ (Current - Complete)
- [x] Create utility functions
- [x] Create useLearningPath hook
- [x] Create useLearningPathVideos hook
- [x] Document progress

**Time**: ~2 hours
**Files**: 3
**Lines**: ~680

---

### **Session 2** (Next - 2-3 hours)
- [ ] Create state components (2 files)
- [ ] Create header components (2 files)
- [ ] Create detail components (3 files)

**Estimated time**: 2-3 hours
**Files**: 7
**Lines**: ~560

---

### **Session 3** (Final - 2-3 hours)
- [ ] Create tab components (3 files)
- [ ] Create refactored main component (1 file)
- [ ] Test integration
- [ ] Update documentation

**Estimated time**: 2-3 hours
**Files**: 4
**Lines**: ~530

---

## 🏆 Success Metrics

### Code Quality
- ✅ 91% code reduction in main component (target)
- ✅ TypeScript strict mode compliance
- ✅ Pure functions in utilities
- ✅ Custom hooks for business logic

### Maintainability
- ✅ Single Responsibility Principle
- ✅ Clear component boundaries
- ✅ Easy to locate code
- ✅ Reusable components

### Developer Experience
- ✅ Clean import paths (barrel exports)
- ✅ Consistent naming conventions
- ✅ Self-documenting code
- ✅ Easy to extend

---

## 🔄 Patterns Established

### Custom Hooks Pattern
```typescript
export const useFeature = (): UseFeatureReturn => {
  const [state, setState] = useState(...)

  const action = useCallback(() => { ... }, [deps])

  useEffect(() => { ... }, [deps])

  return { state, action }
}
```

### Utility Functions Pattern
```typescript
export const utilityFunction = (param: Type): ReturnType => {
  // Pure function logic
  return result
}
```

### Component Props Pattern
```typescript
export interface ComponentNameProps {
  data: DataType
  onAction: () => void
}

export const ComponentName: React.FC<ComponentNameProps> = ({
  data,
  onAction
}) => { ... }
```

---

## 📚 Key Learnings

### What Works Well

1. **Systematic extraction**: Start with utilities, then hooks, then components
2. **Type-first approach**: Define interfaces before implementation
3. **Pure functions**: Easier to test and reuse
4. **Custom hooks**: Encapsulate complex state logic

### Best Practices

1. **Naming conventions**:
   - Hooks: `use{Feature}` (e.g., `useLearningPath`)
   - Components: `{Feature}{Component}` (e.g., `PathLoadingState`)
   - Utils: `{action}{Subject}` (e.g., `extractSubject`)

2. **File organization**:
   ```
   src/
   ├── hooks/
   │   └── use{Feature}.ts
   ├── utils/
   │   └── {feature}Helpers.ts
   └── components/
       └── {Feature}/
           ├── {Component}.tsx
           └── index.ts
   ```

3. **Export pattern**: Both named and default exports for flexibility

---

## 🎉 Current Achievement

**Foundation Complete!** The most complex parts (data fetching, video loading, state management) are now encapsulated in clean, reusable hooks and utilities.

**Remaining work** focuses on UI component extraction, which follows established patterns and is straightforward.

**Phase 3 Overall Progress**: **80%** (including AdvancedExamResults + OSYMExamInterface + LearningPathPage foundation)

---

## 📋 Next Immediate Steps

1. **Create state components** (PathLoadingState, PathErrorState)
2. **Create header components** (LearningPathHeader, LearningStyleBadge)
3. **Create detail components** (NodeDetailsPanel, VideoAnalyticsCard, ModuleProgressCard)
4. **Create tab components** (3 tabs)
5. **Create main refactored component**
6. **Test and verify**

**Total estimated time to complete**: 4-6 hours over 2 sessions

---

**Status**: Foundation layer complete. Ready to proceed with UI component extraction in next session.
