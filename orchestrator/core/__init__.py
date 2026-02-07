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

from .state import (
    TaskStatus,
    GateResult,
    DiffStats,
    RunState,
    StateStore,
    RedisStateStore,
    get_state_store,
)

from .memory import (
    LessonType,
    ConfidenceLevel,
    Lesson,
    RoutingPolicyModel,
    MemoryStore,
    get_memory_store,
)

from .quality_gates import (
    GateAction,
    GateOutput,
    QualityGate,
    LintGate,
    TypeCheckGate,
    UnitTestGate,
    SecurityGate,
    QualityGatePipeline,
    get_quality_pipeline,
)

from .routing import (
    TaskType,
    RiskLevel,
    TaskAnalysis,
    RoutingDecision,
    RoutingEngine,
    get_routing_engine,
)

from .self_improvement import (
    ImprovementType,
    PerformanceMetrics,
    ImprovementAction,
    MetricsCollector,
    SelfImprovementEngine,
    get_improvement_engine,
)

# graph - LangGraph orchestration (enabled)
try:
    from .graph import (
        OrchestratorState,
        KiroOrchestrator,
        create_orchestrator,
    )
except ImportError:
    OrchestratorState = None
    KiroOrchestrator = None
    create_orchestrator = None

from .llm_gateway import (
    ModelProvider,
    LLMConfig,
    LLMResponse,
    LLMUsage,
    LLMClient,
    ClaudeClient,
    OpenAIClient,
    LLMGateway,
    get_llm_gateway,
)

from .tool_executor import (
    ToolCategory,
    ToolResult,
    ToolConfig,
    ToolExecutor,
    FileOperations,
    ShellExecutor,
    LintRunner,
    TestRunner,
    SandboxToolExecutor,
    get_tool_executor,
    TOOL_ALLOWLIST,
    TOOL_BLOCKLIST,
)

from .agents import (
    AgentRole,
    AgentOutput,
    Agent,
    PlannerAgent,
    ImplementerAgent,
    ReviewerAgent,
    FixerAgent,
    TesterAgent,
    SecurityAuditorAgent,
    DocumentWriterAgent,
    AgentFactory,
    get_agent,
    AGENT_PROMPTS,
)

from .diff_guard import (
    DiffLimits,
    DiffGuard,
    DIFF_LIMITS,
)

from .template_manager import (
    TemplateCategory,
    ModelTarget,
    TemplateVariable,
    Template,
    TemplateManager,
    get_template_manager,
)

from .scope_validator import (
    ScopeViolationType,
    RiskCategory,
    ScopeLimits,
    FileChange,
    ScopeValidator,
    get_scope_validator,
)

from .policy_change_log import (
    ChangeType,
    ChangeSource,
    PolicySnapshot,
    ChangeRecord,
    PolicyChangeLog,
    get_change_log,
    reset_change_log,
)

from .repo_scanner import (
    FileType,
    FrameworkHint,
    FileInfo,
    DirectoryInfo,
    DependencyInfo,
    ScanResult,
    RepoScanner,
    get_repo_scanner,
    reset_scanner,
    quick_scan,
)

from .signal_dictionary import (
    SignalCategory,
    SignalPriority,
    ActionType,
    Signal,
    SignalMatch,
    SignalDictionary,
    get_signal_dictionary,
)

from .metrics_collector import (
    MetricType,
    MetricCategory,
    MetricPoint,
    MetricSummary,
    MetricsCollector as AdvancedMetricsCollector,  # Avoid conflict with self_improvement.MetricsCollector
    TimerContext,
    get_metrics_collector,
)

from .learning_loop import (
    StrategyType,
    Strategy,
    ParameterBound,
    LearningResult,
    LearningLoop,
    get_learning_loop,
)

from .policy_engine import (
    PolicyCategory,
    PolicySeverity,
    PolicyResult,
    Policy,
    PolicyEngine,
    get_policy_engine,
)

from .resource_manager import (
    ResourceType,
    ResourceState,
    AllocationPriority,
    ResourceQuota,
    ResourceAllocation,
    ResourceRequest,
    ResourcePool,
    RateLimiter,
    AgentPool,
    ResourceManager,
)

from .loop_guardrail import (
    GuardrailAction,
    ViolationType,
    GuardrailConfig,
    GuardrailResult,
    LoopGuardrail,
)

from .risk_map_generator import (
    RiskLevel as RiskMapLevel,  # Avoid conflict with routing.RiskLevel
    RiskCategory as RiskMapCategory,  # Avoid conflict with scope_validator.RiskCategory
    RiskFactor,
    RiskMap,
    RiskMapGenerator,
)

from .regression_tracker import (
    RegressionType,
    Severity,
    MetricSnapshot,
    RegressionAlert,
    RegressionConfig,
    RegressionTracker,
)

from .cost_tracker import (
    ModelTier,
    UsageRecord,
    BudgetConfig,
    BudgetAlert,
    CostSummary,
    CostTracker,
)

from .question_pipeline import (
    QuestionStatus,
    IRTParams,
    QuestionDraft,
    PipelineConfig,
    QuestionPipeline,
)

from .student_analytics import (
    PerformanceTrend,
    MasteryLevel,
    StudentResponse,
    TopicMastery,
    StudentProfile,
    StudentAnalyticsPipeline,
)

from .calibration_pipeline import (
    CalibrationStatus,
    CalibrationFlag,
    ResponseData,
    CalibrationResult,
    CalibrationPipeline,
)

from .exam_simulation import (
    ExamType,
    ExamMode,
    ExamQuestion,
    ExamAnswer,
    ExamSession,
    ExamAnalytics,
    ExamSimulationEngine,
)

from .repetition_pipeline import (
    CardState,
    ReviewGrade,
    CulturalPeriod,
    RepetitionCard,
    ReviewResult,
    StudySession as RepetitionStudySession,  # Avoid conflict
    RepetitionStats,
    RepetitionConfig,
    RepetitionPipeline,
)

from .adaptive_recommender import (
    BanditAlgorithm,
    ContentType,
    ArmStats,
    Recommendation,
    RecommenderConfig,
    StudentBanditProfile,
    AdaptiveRecommender,
)

from .taxonomy_classifier import (
    TaxonomyType,
    SOLOLevel,
    MarzanoSystem,
    MarzanoCognitiveLevel,
    PatternEntry,
    SOLOResult,
    MarzanoResult,
    TaxonomyResult,
    TaxonomyConfig,
    TaxonomyClassifier,
)

from .cognitive_profiler import (
    TaggedResponse,
    TaxonomyPerformance,
    SubjectCognitiveProfile,
    CognitiveProfile,
    CognitiveProfilerConfig,
    CognitiveProfiler,
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

__version__ = "3.2.1"  # Taxonomy v2: weighted scoring, structure/relation cues, margin confidence
