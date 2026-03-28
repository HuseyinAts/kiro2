"""
KIRO2 Orchestrator Core Module
==============================
"Doğru Kod" odaklı hibrit mimari implementasyonu.

Ana Bileşenler:
- State: Run-scoped state management (SOURCE OF TRUTH)
- Memory: Project-scoped persistent learning (ADVISORY ONLY)
- QualityGates: Sequential quality validation pipeline
- Routing: Policy-driven task routing
- SelfImprovement: Evidence-based improvement (NO self-replication)
- Graph: LangGraph deterministic orchestration
- LLMGateway: Unified LLM interface
- ToolExecutor: Sandboxed tool execution
- Agents: 7 specialized agent templates

Kritik Prensip: State ASLA Memory tarafından override edilemez.
"""

from .memory import (
    ConfidenceLevel,
    Lesson,
    LessonType,
    MemoryStore,
    RoutingPolicyModel,
    get_memory_store,
)
from .quality_gates import (
    GateAction,
    GateOutput,
    LintGate,
    QualityGate,
    QualityGatePipeline,
    SecurityGate,
    TypeCheckGate,
    UnitTestGate,
    get_quality_pipeline,
)
from .routing import (
    RiskLevel,
    RoutingDecision,
    RoutingEngine,
    TaskAnalysis,
    TaskType,
    get_routing_engine,
)
from .self_improvement import (
    ImprovementAction,
    ImprovementType,
    MetricsCollector,
    PerformanceMetrics,
    SelfImprovementEngine,
    get_improvement_engine,
)
from .state import (
    DiffStats,
    GateResult,
    RedisStateStore,
    RunState,
    StateStore,
    TaskStatus,
    get_state_store,
)

# graph - LangGraph orchestration (enabled)
try:
    from .graph import (
        KiroOrchestrator,
        OrchestratorState,
        create_orchestrator,
    )
except ImportError:
    OrchestratorState = None
    KiroOrchestrator = None
    create_orchestrator = None

from .adaptive_recommender import (
    AdaptiveRecommender,
    ArmStats,
    BanditAlgorithm,
    ContentType,
    Recommendation,
    RecommenderConfig,
    StudentBanditProfile,
)
from .agents import (
    AGENT_PROMPTS,
    Agent,
    AgentFactory,
    AgentOutput,
    AgentRole,
    DocumentWriterAgent,
    FixerAgent,
    ImplementerAgent,
    PlannerAgent,
    ReviewerAgent,
    SecurityAuditorAgent,
    TesterAgent,
    get_agent,
)
from .calibration_pipeline import (
    CalibrationFlag,
    CalibrationPipeline,
    CalibrationResult,
    CalibrationStatus,
    ResponseData,
)
from .cognitive_profiler import (
    CognitiveProfile,
    CognitiveProfiler,
    CognitiveProfilerConfig,
    SubjectCognitiveProfile,
    TaggedResponse,
    TaxonomyPerformance,
)
from .cost_tracker import (
    BudgetAlert,
    BudgetConfig,
    CostSummary,
    CostTracker,
    ModelTier,
    UsageRecord,
)
from .diff_guard import (
    DIFF_LIMITS,
    DiffGuard,
    DiffLimits,
)
from .exam_simulation import (
    ExamAnalytics,
    ExamAnswer,
    ExamMode,
    ExamQuestion,
    ExamSession,
    ExamSimulationEngine,
    ExamType,
)
from .learning_loop import (
    LearningLoop,
    LearningResult,
    ParameterBound,
    Strategy,
    StrategyType,
    get_learning_loop,
)
from .llm_gateway import (
    ClaudeClient,
    LLMClient,
    LLMConfig,
    LLMGateway,
    LLMResponse,
    LLMUsage,
    ModelProvider,
    OpenAIClient,
    get_llm_gateway,
)
from .loop_guardrail import (
    GuardrailAction,
    GuardrailConfig,
    GuardrailResult,
    LoopGuardrail,
    ViolationType,
)
from .metrics_collector import (
    MetricCategory,
    MetricPoint,
    MetricsCollector as AdvancedMetricsCollector,  # Avoid conflict with self_improvement.MetricsCollector
    MetricSummary,
    MetricType,
    TimerContext,
    get_metrics_collector,
)
from .policy_change_log import (
    ChangeRecord,
    ChangeSource,
    ChangeType,
    PolicyChangeLog,
    PolicySnapshot,
    get_change_log,
    reset_change_log,
)
from .policy_engine import (
    Policy,
    PolicyCategory,
    PolicyEngine,
    PolicyResult,
    PolicySeverity,
    get_policy_engine,
)
from .question_pipeline import (
    IRTParams,
    PipelineConfig,
    QuestionDraft,
    QuestionPipeline,
    QuestionStatus,
)
from .regression_tracker import (
    MetricSnapshot,
    RegressionAlert,
    RegressionConfig,
    RegressionTracker,
    RegressionType,
    Severity,
)
from .repetition_pipeline import (
    CardState,
    CulturalPeriod,
    RepetitionCard,
    RepetitionConfig,
    RepetitionPipeline,
    RepetitionStats,
    ReviewGrade,
    ReviewResult,
    StudySession as RepetitionStudySession,  # Avoid conflict
)
from .repo_scanner import (
    DependencyInfo,
    DirectoryInfo,
    FileInfo,
    FileType,
    FrameworkHint,
    RepoScanner,
    ScanResult,
    get_repo_scanner,
    quick_scan,
    reset_scanner,
)
from .resource_manager import (
    AgentPool,
    AllocationPriority,
    RateLimiter,
    ResourceAllocation,
    ResourceManager,
    ResourcePool,
    ResourceQuota,
    ResourceRequest,
    ResourceState,
    ResourceType,
)
from .risk_map_generator import (
    RiskCategory as RiskMapCategory,  # Avoid conflict with scope_validator.RiskCategory
    RiskFactor,
    RiskLevel as RiskMapLevel,  # Avoid conflict with routing.RiskLevel
    RiskMap,
    RiskMapGenerator,
)
from .scope_validator import (
    FileChange,
    RiskCategory,
    ScopeLimits,
    ScopeValidator,
    ScopeViolationType,
    get_scope_validator,
)
from .signal_dictionary import (
    ActionType,
    Signal,
    SignalCategory,
    SignalDictionary,
    SignalMatch,
    SignalPriority,
    get_signal_dictionary,
)
from .student_analytics import (
    MasteryLevel,
    PerformanceTrend,
    StudentAnalyticsPipeline,
    StudentProfile,
    StudentResponse,
    TopicMastery,
)
from .taxonomy_classifier import (
    MarzanoCognitiveLevel,
    MarzanoResult,
    MarzanoSystem,
    PatternEntry,
    SOLOLevel,
    SOLOResult,
    TaxonomyClassifier,
    TaxonomyConfig,
    TaxonomyResult,
    TaxonomyType,
)
from .template_manager import (
    ModelTarget,
    Template,
    TemplateCategory,
    TemplateManager,
    TemplateVariable,
    get_template_manager,
)
from .tool_executor import (
    TOOL_ALLOWLIST,
    TOOL_BLOCKLIST,
    FileOperations,
    LintRunner,
    SandboxToolExecutor,
    ShellExecutor,
    TestRunner,
    ToolCategory,
    ToolConfig,
    ToolExecutor,
    ToolResult,
    get_tool_executor,
)

__all__ = [
    # State
    "TaskStatus",
    "GateResult",
    "DiffStats",
    "RunState",
    "StateStore",
    "RedisStateStore",
    "get_state_store",
    # Memory
    "LessonType",
    "ConfidenceLevel",
    "Lesson",
    "RoutingPolicyModel",
    "MemoryStore",
    "get_memory_store",
    # Quality Gates
    "GateAction",
    "GateOutput",
    "QualityGate",
    "LintGate",
    "TypeCheckGate",
    "UnitTestGate",
    "SecurityGate",
    "QualityGatePipeline",
    "get_quality_pipeline",
    # Routing
    "TaskType",
    "RiskLevel",
    "TaskAnalysis",
    "RoutingDecision",
    "RoutingEngine",
    "get_routing_engine",
    # Self Improvement
    "ImprovementType",
    "PerformanceMetrics",
    "ImprovementAction",
    "MetricsCollector",
    "SelfImprovementEngine",
    "get_improvement_engine",
    # Graph - LangGraph orchestration (enabled)
    "OrchestratorState",
    "KiroOrchestrator",
    "create_orchestrator",
    # LLM Gateway
    "ModelProvider",
    "LLMConfig",
    "LLMResponse",
    "LLMUsage",
    "LLMClient",
    "ClaudeClient",
    "OpenAIClient",
    "LLMGateway",
    "get_llm_gateway",
    # Tool Executor
    "ToolCategory",
    "ToolResult",
    "ToolConfig",
    "ToolExecutor",
    "FileOperations",
    "ShellExecutor",
    "LintRunner",
    "TestRunner",
    "SandboxToolExecutor",
    "get_tool_executor",
    "TOOL_ALLOWLIST",
    "TOOL_BLOCKLIST",
    # Diff Guard
    "DiffLimits",
    "DiffGuard",
    "DIFF_LIMITS",
    # Template Manager
    "TemplateCategory",
    "ModelTarget",
    "TemplateVariable",
    "Template",
    "TemplateManager",
    "get_template_manager",
    # Scope Validator
    "ScopeViolationType",
    "RiskCategory",
    "ScopeLimits",
    "FileChange",
    "ScopeValidator",
    "get_scope_validator",
    # Policy Change Log
    "ChangeType",
    "ChangeSource",
    "PolicySnapshot",
    "ChangeRecord",
    "PolicyChangeLog",
    "get_change_log",
    "reset_change_log",
    # Repo Scanner
    "FileType",
    "FrameworkHint",
    "FileInfo",
    "DirectoryInfo",
    "DependencyInfo",
    "ScanResult",
    "RepoScanner",
    "get_repo_scanner",
    "reset_scanner",
    "quick_scan",
    # Signal Dictionary
    "SignalCategory",
    "SignalPriority",
    "ActionType",
    "Signal",
    "SignalMatch",
    "SignalDictionary",
    "get_signal_dictionary",
    # Metrics Collector (Advanced)
    "MetricType",
    "MetricCategory",
    "MetricPoint",
    "MetricSummary",
    "AdvancedMetricsCollector",
    "TimerContext",
    "get_metrics_collector",
    # Learning Loop
    "StrategyType",
    "Strategy",
    "ParameterBound",
    "LearningResult",
    "LearningLoop",
    "get_learning_loop",
    # Policy Engine
    "PolicyCategory",
    "PolicySeverity",
    "PolicyResult",
    "Policy",
    "PolicyEngine",
    "get_policy_engine",
    # Resource Manager
    "ResourceType",
    "ResourceState",
    "AllocationPriority",
    "ResourceQuota",
    "ResourceAllocation",
    "ResourceRequest",
    "ResourcePool",
    "RateLimiter",
    "AgentPool",
    "ResourceManager",
    # Agents
    "AgentRole",
    "AgentOutput",
    "Agent",
    "PlannerAgent",
    "ImplementerAgent",
    "ReviewerAgent",
    "FixerAgent",
    "TesterAgent",
    "SecurityAuditorAgent",
    "DocumentWriterAgent",
    "AgentFactory",
    "get_agent",
    "AGENT_PROMPTS",
    # Loop Guardrail
    "GuardrailAction",
    "ViolationType",
    "GuardrailConfig",
    "GuardrailResult",
    "LoopGuardrail",
    # Risk Map Generator
    "RiskMapLevel",
    "RiskMapCategory",
    "RiskFactor",
    "RiskMap",
    "RiskMapGenerator",
    # Regression Tracker
    "RegressionType",
    "Severity",
    "MetricSnapshot",
    "RegressionAlert",
    "RegressionConfig",
    "RegressionTracker",
    # Cost Tracker
    "ModelTier",
    "UsageRecord",
    "BudgetConfig",
    "BudgetAlert",
    "CostSummary",
    "CostTracker",
    # Question Pipeline
    "QuestionStatus",
    "IRTParams",
    "QuestionDraft",
    "PipelineConfig",
    "QuestionPipeline",
    # Student Analytics
    "PerformanceTrend",
    "MasteryLevel",
    "StudentResponse",
    "TopicMastery",
    "StudentProfile",
    "StudentAnalyticsPipeline",
    # Calibration Pipeline
    "CalibrationStatus",
    "CalibrationFlag",
    "ResponseData",
    "CalibrationResult",
    "CalibrationPipeline",
    # Exam Simulation
    "ExamType",
    "ExamMode",
    "ExamQuestion",
    "ExamAnswer",
    "ExamSession",
    "ExamAnalytics",
    "ExamSimulationEngine",
    # Repetition Pipeline
    "CardState",
    "ReviewGrade",
    "CulturalPeriod",
    "RepetitionCard",
    "ReviewResult",
    "RepetitionStudySession",
    "RepetitionStats",
    "RepetitionConfig",
    "RepetitionPipeline",
    # Adaptive Recommender
    "BanditAlgorithm",
    "ContentType",
    "ArmStats",
    "Recommendation",
    "RecommenderConfig",
    "StudentBanditProfile",
    "AdaptiveRecommender",
    # Taxonomy Classifier
    "TaxonomyType",
    "SOLOLevel",
    "MarzanoSystem",
    "MarzanoCognitiveLevel",
    "PatternEntry",
    "SOLOResult",
    "MarzanoResult",
    "TaxonomyResult",
    "TaxonomyConfig",
    "TaxonomyClassifier",
    # Cognitive Profiler
    "TaggedResponse",
    "TaxonomyPerformance",
    "SubjectCognitiveProfile",
    "CognitiveProfile",
    "CognitiveProfilerConfig",
    "CognitiveProfiler",
]

__version__ = "2.5.0"
