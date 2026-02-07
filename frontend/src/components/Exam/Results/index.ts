/**
 * Results Components Barrel Export
 *
 * Central export for all exam results components
 */

// Main Components
export { ExamResultsHeader } from './ExamResultsHeader';
export type { ExamResultsHeaderProps } from './ExamResultsHeader';

// State Components
export { ResultsLoadingState } from './ResultsLoadingState';
export { ResultsErrorState } from './ResultsErrorState';
export type { ResultsErrorStateProps } from './ResultsErrorState';
export { ResultsEmptyState } from './ResultsEmptyState';

// Dialog Components
export { RecommendationsDialog } from './RecommendationsDialog';
export type { RecommendationsDialogProps } from './RecommendationsDialog';

// Tab Components
export { BasicResultsTab } from './Tabs/BasicResultsTab';
export type { BasicResultsTabProps } from './Tabs/BasicResultsTab';

export { IRTMorphologyTab } from './Tabs/IRTMorphologyTab';
export type { IRTMorphologyTabProps } from './Tabs/IRTMorphologyTab';

export { ZPDAnalysisTab } from './Tabs/ZPDAnalysisTab';
export type { ZPDAnalysisTabProps } from './Tabs/ZPDAnalysisTab';

export { LearningStyleTab } from './Tabs/LearningStyleTab';
export type { LearningStyleTabProps } from './Tabs/LearningStyleTab';

export { OSYMETSComparisonTab } from './Tabs/OSYMETSComparisonTab';
export type { OSYMETSComparisonTabProps } from './Tabs/OSYMETSComparisonTab';

export { PerformanceTrendTab } from './Tabs/PerformanceTrendTab';
export type { PerformanceTrendTabProps } from './Tabs/PerformanceTrendTab';
