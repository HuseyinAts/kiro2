"""
KIRO2 Orchestrator - Routing Engine (Policy-Driven)
===================================================
Hangi işi hangi modele/ajana vereceğini KANITA DAYALI seçer.

Sinyaller:
- Görev türü (refactor/bugfix/test/security/docs)
- Risk alanı (auth/db/migration/infra)
- Etki alanı (tahmini diff büyüklüğü)
- Geçmiş performans (LangSmith metrikleri)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class TaskType(str, Enum):
    """Görev tipleri"""
    TURKISH_NLP = "turkish_nlp"
    SECURITY = "security"
    REFACTOR = "refactor"
    BUGFIX = "bugfix"
    FEATURE = "feature"
    TEST = "test"
    DOCS = "docs"
    FRONTEND = "frontend"
    BACKEND = "backend"
    MIGRATION = "migration"
    INFRA = "infra"
    PSYCHOMETRICS = "psychometrics"
    QUESTION_PIPELINE = "question_pipeline"
    QUALITY_EVALUATION = "quality_evaluation"
    EXAM_ENGINE = "exam_engine"
    LEARNING_ANALYTICS = "learning_analytics"
    DATA_PIPELINE = "data_pipeline"
    VIDEO_DISCOVERY = "video_discovery"


class RiskLevel(str, Enum):
    """Risk seviyeleri"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModelChoice(str, Enum):
    """Model seçenekleri"""
    CLAUDE_OPUS = "claude-opus-4"
    CLAUDE_SONNET = "claude-sonnet-4"
    CODEX_CLI = "codex-cli"
    QWEN_TURKISH = "qwen3-8b-turkish"
    GPT4O = "gpt-4o"


@dataclass
class RoutingDecision:
    """Routing kararı"""
    primary_model: ModelChoice
    fallback_model: Optional[ModelChoice] = None
    agent_type: str = "general"
    
    # İzinler
    allowed_tools: list[str] = field(default_factory=list)
    blocked_tools: list[str] = field(default_factory=list)
    
    # Kısıtlamalar
    max_diff_lines: int = 200
    max_files: int = 5
    requires_human_review: bool = False
    
    # Metadata
    confidence: float = 0.8
    reason: str = ""


@dataclass
class TaskAnalysis:
    """Görev analizi"""
    task_type: TaskType
    risk_level: RiskLevel
    estimated_diff_size: str  # small, medium, large
    affected_modules: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


class TaskAnalyzer:
    """Görev analiz edici"""
    
    # Türkçe NLP anahtar kelimeleri
    TURKISH_NLP_KEYWORDS = [
        "türkçe", "turkish", "nlp", "qwen", "sentiment", "zemberek",
        "morfoloji", "tokenizer", "embedding", "ocr kalite", "metin analiz"
    ]

    # Psikometri anahtar kelimeleri
    PSYCHOMETRICS_KEYWORDS = [
        "irt", "fsrs", "zpd", "kalibrasyon", "calibration", "psikometri",
        "psychometric", "item response", "spaced repetition", "ability estimate"
    ]

    # Soru üretim pipeline anahtar kelimeleri
    QUESTION_PIPELINE_KEYWORDS = [
        "soru üret", "question generat", "template", "taxonomy soru",
        "solo sınıfla", "marzano sınıfla", "bloom sınıfla", "soru pipeline"
    ]

    # Kalite değerlendirme anahtar kelimeleri
    QUALITY_EVALUATION_KEYWORDS = [
        "kalite skor", "bertscore", "osym skor", "expert review", "hitl",
        "plagiarism", "içerik kalite", "soru kalite", "quality evaluat"
    ]

    # Sınav motoru anahtar kelimeleri
    EXAM_ENGINE_KEYWORDS = [
        "sınav", "sinav", "exam engine", "mock test", "puanlama", "scoring",
        "tyt format", "ayt format", "ydt format", "sınav simülasyon"
    ]

    # Öğrenme analitik anahtar kelimeleri
    LEARNING_ANALYTICS_KEYWORDS = [
        "öğrenci analiz", "learning analytic", "bilişsel profil",
        "öğrenme stili", "cognitive profile", "performans analiz",
        "öğrenme yolu", "learning path analiz"
    ]
    
    # Veri pipeline anahtar kelimeleri
    DATA_PIPELINE_KEYWORDS = [
        "matching kalite", "confidence improve", "duplicate detect",
        "refinement", "veri kalite", "benchmark", "low confidence",
        "match rate", "eslesmis", "deduplication", "data quality"
    ]

    # Video discovery anahtar kelimeleri
    VIDEO_DISCOVERY_KEYWORDS = [
        "youtube", "video search", "eba tv", "khan academy",
        "video recommend", "transcript", "video analytics",
        "video discovery", "playlist", "video cache", "eba sync"
    ]

    # Güvenlik anahtar kelimeleri
    SECURITY_KEYWORDS = [
        "security", "güvenlik", "auth", "authentication", "authorization",
        "jwt", "oauth", "vulnerability", "audit", "xss", "sql injection",
        "csrf", "encryption", "password", "secret", "api key"
    ]
    
    # Risk dosya desenleri
    HIGH_RISK_PATTERNS = [
        r".*security.*\.py$",
        r".*auth.*\.py$",
        r".*migration.*\.py$",
        r".*alembic.*",
        r".*\.env.*",
        r"docker-compose.*\.yml$",
    ]
    
    CRITICAL_PATTERNS = [
        r".*/core/security/.*",
        r".*/alembic/versions/.*",
        r".*secrets.*",
    ]
    
    def analyze(self, description: str, files: list[str] = None) -> TaskAnalysis:
        """Görevi analiz et"""
        description_lower = description.lower()
        files = files or []
        
        # Görev tipi tespit
        task_type = self._detect_task_type(description_lower)
        
        # Risk seviyesi tespit
        risk_level = self._detect_risk_level(description_lower, files)
        
        # Diff boyutu tahmini
        diff_size = self._estimate_diff_size(description_lower, len(files))
        
        # Anahtar kelimeler
        keywords = self._extract_keywords(description_lower)
        
        return TaskAnalysis(
            task_type=task_type,
            risk_level=risk_level,
            estimated_diff_size=diff_size,
            affected_modules=self._extract_modules(files),
            keywords=keywords,
        )
    
    def _detect_task_type(self, desc: str) -> TaskType:
        """Görev tipini tespit et"""
        # Specialist agent'lar (öncelikli - daha spesifik eşleşmeler)
        if any(kw in desc for kw in self.PSYCHOMETRICS_KEYWORDS):
            return TaskType.PSYCHOMETRICS
        if any(kw in desc for kw in self.EXAM_ENGINE_KEYWORDS):
            return TaskType.EXAM_ENGINE
        if any(kw in desc for kw in self.QUALITY_EVALUATION_KEYWORDS):
            return TaskType.QUALITY_EVALUATION
        if any(kw in desc for kw in self.QUESTION_PIPELINE_KEYWORDS):
            return TaskType.QUESTION_PIPELINE
        if any(kw in desc for kw in self.LEARNING_ANALYTICS_KEYWORDS):
            return TaskType.LEARNING_ANALYTICS
        if any(kw in desc for kw in self.DATA_PIPELINE_KEYWORDS):
            return TaskType.DATA_PIPELINE
        if any(kw in desc for kw in self.VIDEO_DISCOVERY_KEYWORDS):
            return TaskType.VIDEO_DISCOVERY

        # Türkçe NLP kontrolü (psikometri sonrası - IRT/FSRS artık psychometrics'e gidiyor)
        if any(kw in desc for kw in self.TURKISH_NLP_KEYWORDS):
            return TaskType.TURKISH_NLP

        # Güvenlik kontrolü
        if any(kw in desc for kw in self.SECURITY_KEYWORDS):
            return TaskType.SECURITY

        # Diğer tipler
        type_keywords = {
            TaskType.REFACTOR: ["refactor", "restructure", "reorganize", "düzenle"],
            TaskType.BUGFIX: ["fix", "bug", "hata", "error", "issue", "problem"],
            TaskType.TEST: ["test", "pytest", "jest", "coverage", "unit test"],
            TaskType.DOCS: ["document", "readme", "docstring", "comment", "belge"],
            TaskType.FRONTEND: ["react", "component", "ui", "css", "tailwind", "frontend"],
            TaskType.BACKEND: ["api", "endpoint", "fastapi", "route", "backend"],
            TaskType.MIGRATION: ["migration", "alembic", "schema", "database change"],
            TaskType.INFRA: ["docker", "ci", "cd", "deploy", "kubernetes", "k8s"],
        }
        
        for task_type, keywords in type_keywords.items():
            if any(kw in desc for kw in keywords):
                return task_type
        
        return TaskType.FEATURE
    
    def _detect_risk_level(self, desc: str, files: list[str]) -> RiskLevel:
        """Risk seviyesini tespit et"""
        # Kritik dosya kontrolü
        for f in files:
            for pattern in self.CRITICAL_PATTERNS:
                if re.match(pattern, f):
                    return RiskLevel.CRITICAL
        
        # Yüksek risk dosya kontrolü
        for f in files:
            for pattern in self.HIGH_RISK_PATTERNS:
                if re.match(pattern, f):
                    return RiskLevel.HIGH
        
        # Güvenlik anahtar kelimeleri
        if any(kw in desc for kw in self.SECURITY_KEYWORDS):
            return RiskLevel.HIGH
        
        # Migration
        if "migration" in desc or "alembic" in desc:
            return RiskLevel.HIGH
        
        return RiskLevel.MEDIUM
    
    def _estimate_diff_size(self, desc: str, file_count: int) -> str:
        """Diff boyutunu tahmin et"""
        if file_count > 10 or "large" in desc or "major" in desc:
            return "large"
        elif file_count > 3 or "refactor" in desc:
            return "medium"
        return "small"
    
    def _extract_keywords(self, desc: str) -> list[str]:
        """Anahtar kelimeleri çıkar"""
        keywords = []
        all_keywords = (
            self.TURKISH_NLP_KEYWORDS
            + self.SECURITY_KEYWORDS
            + self.PSYCHOMETRICS_KEYWORDS
            + self.QUESTION_PIPELINE_KEYWORDS
            + self.QUALITY_EVALUATION_KEYWORDS
            + self.EXAM_ENGINE_KEYWORDS
            + self.LEARNING_ANALYTICS_KEYWORDS
            + self.DATA_PIPELINE_KEYWORDS
            + self.VIDEO_DISCOVERY_KEYWORDS
        )
        for kw in all_keywords:
            if kw in desc:
                keywords.append(kw)
        return keywords
    
    def _extract_modules(self, files: list[str]) -> list[str]:
        """Etkilenen modülleri çıkar"""
        modules = set()
        for f in files:
            parts = f.split("/")
            if len(parts) > 1:
                modules.add(parts[0])
        return list(modules)


class RoutingEngine:
    """
    Policy-driven routing engine.
    
    Basit başla, karmaşıklığı metrikler gerektirdikçe artır.
    Faz 4 için: task_type → model mapping ile başla.
    """
    
    # Temel routing tablosu (task_type → model)
    DEFAULT_ROUTING = {
        TaskType.TURKISH_NLP: {
            "primary": ModelChoice.CLAUDE_OPUS,
            "fallback": ModelChoice.QWEN_TURKISH,
            "agent": "implementer",
        },
        TaskType.SECURITY: {
            "primary": ModelChoice.CLAUDE_OPUS,
            "fallback": ModelChoice.GPT4O,
            "agent": "security_auditor",
        },
        TaskType.REFACTOR: {
            "primary": ModelChoice.CLAUDE_OPUS,
            "fallback": ModelChoice.CLAUDE_SONNET,
            "agent": "implementer",
        },
        TaskType.FRONTEND: {
            "primary": ModelChoice.CODEX_CLI,
            "fallback": ModelChoice.CLAUDE_SONNET,
            "agent": "implementer",
        },
        TaskType.BACKEND: {
            "primary": ModelChoice.CODEX_CLI,
            "fallback": ModelChoice.CLAUDE_SONNET,
            "agent": "implementer",
        },
        TaskType.TEST: {
            "primary": ModelChoice.CODEX_CLI,
            "fallback": ModelChoice.GPT4O,
            "agent": "tester",
        },
        TaskType.DOCS: {
            "primary": ModelChoice.CODEX_CLI,
            "fallback": ModelChoice.CLAUDE_SONNET,
            "agent": "document_writer",
        },
        TaskType.BUGFIX: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CODEX_CLI,
            "agent": "fixer",
        },
        TaskType.FEATURE: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CODEX_CLI,
            "agent": "implementer",
        },
        TaskType.MIGRATION: {
            "primary": ModelChoice.CLAUDE_OPUS,
            "fallback": ModelChoice.CLAUDE_SONNET,
            "agent": "implementer",
        },
        TaskType.INFRA: {
            "primary": ModelChoice.CODEX_CLI,
            "fallback": ModelChoice.CLAUDE_SONNET,
            "agent": "implementer",
        },
        TaskType.PSYCHOMETRICS: {
            "primary": ModelChoice.CLAUDE_OPUS,
            "fallback": ModelChoice.CLAUDE_SONNET,
            "agent": "psychometrics_specialist",
        },
        TaskType.QUESTION_PIPELINE: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CODEX_CLI,
            "agent": "question_pipeline_specialist",
        },
        TaskType.QUALITY_EVALUATION: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CLAUDE_OPUS,
            "agent": "quality_evaluator",
        },
        TaskType.EXAM_ENGINE: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CODEX_CLI,
            "agent": "exam_engine_specialist",
        },
        TaskType.LEARNING_ANALYTICS: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CLAUDE_OPUS,
            "agent": "learning_analytics_specialist",
        },
        TaskType.DATA_PIPELINE: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CODEX_CLI,
            "agent": "data_pipeline_specialist",
        },
        TaskType.VIDEO_DISCOVERY: {
            "primary": ModelChoice.CLAUDE_SONNET,
            "fallback": ModelChoice.CODEX_CLI,
            "agent": "video_discovery_specialist",
        },
    }
    
    # Risk bazlı kısıtlamalar
    RISK_CONSTRAINTS = {
        RiskLevel.LOW: {
            "max_diff_lines": 500,
            "max_files": 10,
            "requires_human_review": False,
        },
        RiskLevel.MEDIUM: {
            "max_diff_lines": 200,
            "max_files": 5,
            "requires_human_review": False,
        },
        RiskLevel.HIGH: {
            "max_diff_lines": 100,
            "max_files": 3,
            "requires_human_review": True,
        },
        RiskLevel.CRITICAL: {
            "max_diff_lines": 50,
            "max_files": 2,
            "requires_human_review": True,
        },
    }
    
    # Tool allowlist (güvenlik)
    TOOL_ALLOWLIST = [
        "file_read", "file_write", "file_edit",
        "bash_run_tests", "bash_run_lint", "bash_run_typecheck",
        "git_diff", "git_status", "git_log", "git_add", "git_commit",
    ]
    
    TOOL_BLOCKLIST = [
        "bash_rm_rf", "bash_curl", "bash_wget",
        "file_delete_recursive", "git_push_force",
    ]
    
    def __init__(self, memory_store=None):
        self.analyzer = TaskAnalyzer()
        self.memory_store = memory_store
    
    async def route(self, description: str, files: list[str] = None) -> RoutingDecision:
        """
        Görevi route et.
        
        Args:
            description: Görev açıklaması
            files: Etkilenen dosyalar
            
        Returns:
            RoutingDecision
        """
        # Analiz
        analysis = self.analyzer.analyze(description, files)
        
        # Temel routing
        routing = self.DEFAULT_ROUTING.get(analysis.task_type, self.DEFAULT_ROUTING[TaskType.FEATURE])
        
        # Risk kısıtlamaları
        constraints = self.RISK_CONSTRAINTS[analysis.risk_level]
        
        # Memory'den geçmiş performans kontrolü (opsiyonel, advisory only)
        policy_override = None
        if self.memory_store:
            policy_override = await self.memory_store.get_routing_policy(analysis.task_type.value)
        
        # Final karar
        primary = ModelChoice(policy_override["primary_model"]) if policy_override else routing["primary"]
        fallback = routing.get("fallback")
        
        decision = RoutingDecision(
            primary_model=primary,
            fallback_model=fallback,
            agent_type=routing["agent"],
            allowed_tools=self.TOOL_ALLOWLIST.copy(),
            blocked_tools=self.TOOL_BLOCKLIST.copy(),
            max_diff_lines=constraints["max_diff_lines"],
            max_files=constraints["max_files"],
            requires_human_review=constraints["requires_human_review"],
            confidence=0.85 if policy_override else 0.75,
            reason=f"Task type: {analysis.task_type.value}, Risk: {analysis.risk_level.value}",
        )
        
        return decision
    
    def get_model_config(self, model: ModelChoice) -> dict:
        """Model konfigürasyonunu döndür"""
        configs = {
            ModelChoice.CLAUDE_OPUS: {
                "provider": "anthropic",
                "model": "claude-opus-4-20250514",
                "max_tokens": 16000,
                "temperature": 0.3,
            },
            ModelChoice.CLAUDE_SONNET: {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 8000,
                "temperature": 0.4,
            },
            ModelChoice.CODEX_CLI: {
                "provider": "openai",
                "model": "codex-cli",
                "type": "cli_tool",
            },
            ModelChoice.QWEN_TURKISH: {
                "provider": "local",
                "model": "qwen3-8b-turkish",
                "endpoint": "http://localhost:8080/v1",
            },
            ModelChoice.GPT4O: {
                "provider": "openai",
                "model": "gpt-4o",
                "max_tokens": 8000,
                "temperature": 0.4,
            },
        }
        return configs.get(model, {})


# Factory function
_default_routing_engine: Optional[RoutingEngine] = None

def get_routing_engine() -> RoutingEngine:
    """Get or create the default routing engine instance"""
    global _default_routing_engine
    if _default_routing_engine is None:
        _default_routing_engine = RoutingEngine()
    return _default_routing_engine
