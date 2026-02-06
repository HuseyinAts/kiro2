"""
Meta-Orkestrator - Tum Sistemin Beyni

Kullanici isteklerini analiz eder, uygun agent'lari secer,
workflow olusturur ve sonuclari ogrenme icin kullanir.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from enum import Enum

from .agent_registry import AgentRegistry, AgentDefinition, HealthStatus
from .agent_genome import AgentGenome, CapabilityType, Capability
from .workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    StepType,
    create_sequential_workflow,
    create_parallel_workflow,
)


class RequestType(Enum):
    """Istek tipi"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    TESTING = "testing"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    CONTENT = "content"
    GENERAL = "general"


@dataclass
class UserRequest:
    """Kullanici istegi"""
    request_id: str
    content: str
    context: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "content": self.content,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
        }


@dataclass
class RequestAnalysis:
    """Istek analizi sonucu"""
    request_type: RequestType
    required_capabilities: list[str]
    complexity: float  # 0.0 - 1.0
    estimated_steps: int
    keywords: list[str]
    language: str  # "tr" or "en"
    confidence: float
    suggested_agents: list[str] = field(default_factory=list)
    parallel_execution_possible: bool = False

    def to_dict(self) -> dict:
        return {
            "request_type": self.request_type.value,
            "required_capabilities": self.required_capabilities,
            "complexity": self.complexity,
            "estimated_steps": self.estimated_steps,
            "keywords": self.keywords,
            "language": self.language,
            "confidence": self.confidence,
            "suggested_agents": self.suggested_agents,
            "parallel_execution_possible": self.parallel_execution_possible,
        }


@dataclass
class OrchestratorResponse:
    """Orkestrator yaniti"""
    request_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution: Optional[WorkflowExecution] = None
    agents_used: list[str] = field(default_factory=list)
    total_duration_ms: float = 0.0
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution": self.execution.to_dict() if self.execution else None,
            "agents_used": self.agents_used,
            "total_duration_ms": self.total_duration_ms,
            "tokens_used": self.tokens_used,
        }


class MetaOrchestrator:
    """
    Meta-Orkestrator - Sistemin Beyni

    Gorevler:
    1. Kullanici isteklerini analiz et
    2. Uygun agent'lari sec
    3. Workflow olustur
    4. Execution'i yonet
    5. Sonuclardan ogren
    """

    # Turkce ve Ingilizce keyword pattern'leri
    KEYWORD_PATTERNS = {
        RequestType.CODE_GENERATION: {
            "tr": ["olustur", "yaz", "ekle", "implement", "kodla", "gelistir"],
            "en": ["create", "write", "add", "implement", "code", "develop", "build"],
        },
        RequestType.CODE_REVIEW: {
            "tr": ["incele", "kontrol", "gozden gecir", "review", "kalite"],
            "en": ["review", "check", "inspect", "quality", "audit"],
        },
        RequestType.BUG_FIX: {
            "tr": ["hata", "duzelt", "fix", "bug", "sorun", "coz", "patla", "calismadi"],
            "en": ["bug", "fix", "error", "issue", "broken", "crash", "fail"],
        },
        RequestType.TESTING: {
            "tr": ["test", "pytest", "jest", "coverage", "birim test"],
            "en": ["test", "pytest", "jest", "coverage", "unit test", "e2e"],
        },
        RequestType.REFACTORING: {
            "tr": ["refactor", "optimize", "iyilestir", "temizle", "duzenle"],
            "en": ["refactor", "optimize", "improve", "clean", "restructure"],
        },
        RequestType.DOCUMENTATION: {
            "tr": ["dokumantasyon", "belge", "acikla", "readme", "api doc"],
            "en": ["documentation", "docs", "readme", "explain", "api doc"],
        },
        RequestType.DEPLOYMENT: {
            "tr": ["deploy", "yayinla", "canli", "production", "docker", "kubernetes"],
            "en": ["deploy", "release", "production", "docker", "kubernetes", "ci/cd"],
        },
        RequestType.ANALYSIS: {
            "tr": ["analiz", "incele", "ara", "bul", "nerede", "nasil"],
            "en": ["analyze", "investigate", "find", "search", "where", "how"],
        },
        RequestType.CONTENT: {
            "tr": ["soru", "icerik", "yukle", "osym", "tyt", "ayt", "yks"],
            "en": ["question", "content", "upload", "exam", "quiz"],
        },
    }

    # Domain-specific keywords for better agent selection
    DOMAIN_KEYWORDS = {
        "backend": ["api", "endpoint", "fastapi", "veritabani", "database", "sunucu", "server", "backend", "crud", "rest"],
        "frontend": ["react", "component", "komponent", "ui", "arayuz", "frontend", "sayfa", "page", "tsx", "css", "tailwind"],
        "content": ["soru", "question", "icerik", "content", "yukle", "upload", "osym", "yks", "tyt", "ayt", "pdf"],
        "devops": ["deploy", "docker", "kubernetes", "k8s", "ci/cd", "pipeline", "monitoring", "grafana", "prometheus"],
        "nlp": ["turkce", "turkish", "nlp", "dil", "language", "zemberek", "berturk", "analiz"],
        "database": ["migration", "alembic", "sqlalchemy", "postgresql", "redis", "cache", "query"],
    }

    # Capability mapping
    REQUEST_CAPABILITIES = {
        RequestType.CODE_GENERATION: [CapabilityType.CODING.value, CapabilityType.BACKEND.value],
        RequestType.CODE_REVIEW: [CapabilityType.REVIEW.value],
        RequestType.BUG_FIX: [CapabilityType.DEBUGGING.value],
        RequestType.TESTING: [CapabilityType.TESTING.value],
        RequestType.REFACTORING: [CapabilityType.CODING.value, CapabilityType.ANALYSIS.value],
        RequestType.DOCUMENTATION: [CapabilityType.GENERATION.value],
        RequestType.DEPLOYMENT: [CapabilityType.DEVOPS.value],
        RequestType.ANALYSIS: [CapabilityType.ANALYSIS.value],
        RequestType.CONTENT: [CapabilityType.CONTENT.value],
    }

    def __init__(self, base_path: str = ".claude"):
        self.base_path = Path(base_path)
        self.registry = AgentRegistry(base_path)
        self.workflow_engine = WorkflowEngine()

        # Set agent executor
        self.workflow_engine.set_executor(self._execute_agent)

        # Metrics
        self._request_count = 0
        self._success_count = 0
        self._total_duration_ms = 0.0

        # Learning data storage
        self._learning_data_file = self.base_path / "orchestration" / "learning_data.json"
        self._learning_data: list[dict] = []

    async def initialize(self) -> None:
        """Orkestrator'u baslat"""
        await self.registry.initialize()
        await self._load_learning_data()
        print(f"MetaOrchestrator initialized with {len(await self.registry.list_all_agents())} agents")

    async def _load_learning_data(self) -> None:
        """Ogrenme verisini yukle"""
        if self._learning_data_file.exists():
            try:
                with open(self._learning_data_file, "r", encoding="utf-8") as f:
                    self._learning_data = json.load(f)
            except Exception:
                self._learning_data = []

    async def _save_learning_data(self) -> None:
        """Ogrenme verisini kaydet"""
        self._learning_data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._learning_data_file, "w", encoding="utf-8") as f:
            json.dump(self._learning_data[-1000:], f, indent=2, ensure_ascii=False)  # Keep last 1000

    async def process_request(self, request: UserRequest) -> OrchestratorResponse:
        """
        Kullanici istegini isle

        Args:
            request: Kullanici istegi

        Returns:
            OrchestratorResponse
        """
        start_time = datetime.now()
        self._request_count += 1

        try:
            # 1. Analyze request
            analysis = await self.analyze_request(request)

            # 2. Select agents
            agents = await self.select_agents(analysis)

            if not agents:
                return OrchestratorResponse(
                    request_id=request.request_id,
                    success=False,
                    error="No suitable agents found for this request",
                )

            # 3. Create workflow
            workflow = await self.create_workflow(agents, analysis, request)

            # 4. Execute workflow
            execution = await self.workflow_engine.execute_workflow(
                workflow,
                initial_context={"request": request.to_dict(), "analysis": analysis.to_dict()},
            )

            # 5. Build response
            duration = (datetime.now() - start_time).total_seconds() * 1000
            success = execution.status.value == "completed"

            if success:
                self._success_count += 1

            self._total_duration_ms += duration

            # 6. Learn from result
            await self.learn_from_result(request, analysis, execution, success)

            # Extract final result
            result = None
            if execution.step_results:
                last_step_id = list(execution.step_results.keys())[-1]
                result = execution.step_results[last_step_id].output

            return OrchestratorResponse(
                request_id=request.request_id,
                success=success,
                result=result,
                execution=execution,
                agents_used=[a.genome.agent_id for a in agents],
                total_duration_ms=duration,
                error=execution.error,
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return OrchestratorResponse(
                request_id=request.request_id,
                success=False,
                error=str(e),
                total_duration_ms=duration,
            )

    async def analyze_request(self, request: UserRequest) -> RequestAnalysis:
        """
        Istegi analiz et

        Args:
            request: Kullanici istegi

        Returns:
            RequestAnalysis
        """
        content_lower = request.content.lower()

        # Detect language
        turkish_chars = set("çğıöşüÇĞİÖŞÜ")
        has_turkish = any(c in request.content for c in turkish_chars)
        turkish_words = ["ve", "ile", "icin", "bir", "bu", "ne", "nasil", "nerede"]
        has_turkish_words = any(w in content_lower for w in turkish_words)
        language = "tr" if (has_turkish or has_turkish_words) else "en"

        # Detect request type and keywords
        # Check BOTH Turkish and English patterns for better detection
        type_scores = {}
        all_keywords = []

        for req_type, patterns in self.KEYWORD_PATTERNS.items():
            score = 0
            matched_keywords = []

            # Check both TR and EN patterns
            all_patterns = patterns.get("tr", []) + patterns.get("en", [])

            for pattern in all_patterns:
                if pattern in content_lower:
                    score += 1
                    matched_keywords.append(pattern)

            if score > 0:
                type_scores[req_type] = score
                all_keywords.extend(matched_keywords)

        # Determine primary request type
        if type_scores:
            request_type = max(type_scores, key=type_scores.get)
            confidence = min(1.0, type_scores[request_type] / 3)
        else:
            request_type = RequestType.GENERAL
            confidence = 0.5

        # Get required capabilities
        required_capabilities = self.REQUEST_CAPABILITIES.get(
            request_type,
            [CapabilityType.CODING.value]
        )

        # Estimate complexity based on content length and keywords
        word_count = len(request.content.split())
        complexity = min(1.0, word_count / 100)

        # Estimate steps
        if request_type in [RequestType.CODE_GENERATION, RequestType.REFACTORING]:
            estimated_steps = max(2, int(complexity * 5))
        elif request_type in [RequestType.BUG_FIX, RequestType.TESTING]:
            estimated_steps = max(2, int(complexity * 3))
        else:
            estimated_steps = max(1, int(complexity * 2))

        # Check for parallel execution possibility
        parallel_possible = (
            "paralel" in content_lower or
            "parallel" in content_lower or
            "ayni anda" in content_lower or
            "simultaneously" in content_lower
        )

        # Detect domain for better agent suggestion
        domain_scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                domain_scores[domain] = score

        # Build suggested agents based on domain
        suggested_agents = []
        if domain_scores:
            top_domain = max(domain_scores, key=domain_scores.get)
            domain_to_agent = {
                "backend": "kiro2-backend-api",
                "frontend": "kiro2-frontend-specialist",
                "content": "kiro2-content-manager",
                "devops": "kiro2-devops-engineer",
                "nlp": "turkish-nlp-specialist",
                "database": "kiro2-backend-api",
            }
            if top_domain in domain_to_agent:
                suggested_agents.append(domain_to_agent[top_domain])

        return RequestAnalysis(
            request_type=request_type,
            required_capabilities=required_capabilities,
            complexity=complexity,
            estimated_steps=estimated_steps,
            keywords=list(set(all_keywords)),
            language=language,
            confidence=confidence,
            suggested_agents=suggested_agents,
            parallel_execution_possible=parallel_possible,
        )

    async def select_agents(self, analysis: RequestAnalysis) -> list[AgentDefinition]:
        """
        Analiz sonucuna gore agent'lari sec

        Args:
            analysis: Istek analizi

        Returns:
            Secilen agent'lar listesi
        """
        # First check suggested agents from domain analysis
        if analysis.suggested_agents:
            suggested_defs = []
            for agent_name in analysis.suggested_agents:
                agent = await self.registry.get_agent_by_name(agent_name)
                if agent:
                    suggested_defs.append(agent)
            if suggested_defs:
                return suggested_defs

        # Find agents with required capabilities
        candidates = await self.registry.discover_by_capabilities(
            analysis.required_capabilities,
            min_proficiency=0.3
        )

        if not candidates:
            # Fallback to any healthy agent
            candidates = await self.registry.list_healthy_agents()

        if not candidates:
            # Last resort - get any agent
            candidates = await self.registry.list_all_agents()

        # Sort by fitness and health
        scored_agents = []
        for agent in candidates:
            health = await self.registry.get_agent_health(agent.genome.agent_id)
            health_score = 1.0 if health == HealthStatus.HEALTHY else 0.5 if health == HealthStatus.DEGRADED else 0.1

            # Calculate match score
            match_score = 0
            agent_caps = {c.type.value for c in agent.genome.capabilities}
            for req_cap in analysis.required_capabilities:
                if req_cap in agent_caps:
                    match_score += 1

            total_score = (
                agent.genome.fitness_score * 0.4 +
                health_score * 0.3 +
                (match_score / max(1, len(analysis.required_capabilities))) * 0.3
            )

            scored_agents.append((agent, total_score))

        scored_agents.sort(key=lambda x: x[1], reverse=True)

        # Select top agents based on complexity
        num_agents = min(analysis.estimated_steps, len(scored_agents), 3)
        return [agent for agent, score in scored_agents[:num_agents]]

    async def create_workflow(
        self,
        agents: list[AgentDefinition],
        analysis: RequestAnalysis,
        request: UserRequest
    ) -> WorkflowDefinition:
        """
        Agent'lar icin workflow olustur

        Args:
            agents: Secilen agent'lar
            analysis: Istek analizi
            request: Orijinal istek

        Returns:
            WorkflowDefinition
        """
        agent_ids = [a.genome.agent_id for a in agents]

        if analysis.parallel_execution_possible and len(agents) > 1:
            return create_parallel_workflow(
                name=f"{analysis.request_type.value}-parallel",
                agent_ids=agent_ids,
                initial_input={
                    "request_content": request.content,
                    "request_context": request.context,
                },
            )

        # Sequential workflow with dependencies
        steps = []
        for i, agent in enumerate(agents):
            step = WorkflowStep(
                step_id=f"step-{i}",
                name=f"{analysis.request_type.value}-{agent.genome.name}",
                agent_id=agent.genome.agent_id,
                step_type=StepType.SEQUENTIAL,
                depends_on=[f"step-{i-1}"] if i > 0 else [],
                input_mapping={f"step-{i-1}": "previous_result"} if i > 0 else {},
            )
            steps.append(step)

        return WorkflowDefinition(
            workflow_id=f"wf-{request.request_id}",
            name=f"Workflow for {analysis.request_type.value}",
            description=f"Auto-generated workflow for: {request.content[:100]}...",
            steps=steps,
            initial_input={
                "request_content": request.content,
                "request_context": request.context,
            },
        )

    async def _execute_agent(self, agent_id: str, input_data: dict) -> Any:
        """
        Agent'i calistir

        Bu metod gercek agent calistiricisi tarafindan override edilebilir.
        Simdilik placeholder olarak calistiriyor.
        """
        agent = await self.registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Record start
        start_time = datetime.now()

        try:
            # Placeholder execution - gercek implementasyonda
            # Claude API veya Task tool kullanilacak
            result = {
                "agent_id": agent_id,
                "agent_name": agent.genome.name,
                "status": "executed",
                "input_received": input_data,
                "message": f"Agent {agent.genome.name} executed successfully",
            }

            # Record success
            duration = (datetime.now() - start_time).total_seconds() * 1000
            await self.registry.record_success(agent_id, duration)
            await self.registry.update_heartbeat(agent_id)

            return result

        except Exception as e:
            await self.registry.record_failure(agent_id)
            raise

    async def learn_from_result(
        self,
        request: UserRequest,
        analysis: RequestAnalysis,
        execution: WorkflowExecution,
        success: bool
    ) -> None:
        """
        Sonuctan ogren

        Basarili/basarisiz islemlerden ogrenme verisi topla.
        """
        learning_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_type": analysis.request_type.value,
            "keywords": analysis.keywords,
            "agents_used": [
                step.agent_id for step in execution.workflow.steps
            ],
            "success": success,
            "duration_ms": execution.duration_ms,
            "complexity": analysis.complexity,
            "confidence": analysis.confidence,
        }

        self._learning_data.append(learning_entry)
        await self._save_learning_data()

        # Update agent fitness based on result
        for step_id, result in execution.step_results.items():
            step = next(
                (s for s in execution.workflow.steps if s.step_id == step_id),
                None
            )
            if step:
                agent = await self.registry.get_agent(step.agent_id)
                if agent:
                    if result.success:
                        await self.registry.record_success(
                            step.agent_id,
                            result.duration_ms
                        )
                    else:
                        await self.registry.record_failure(step.agent_id)

    def get_statistics(self) -> dict:
        """Orkestrator istatistikleri"""
        return {
            "total_requests": self._request_count,
            "successful_requests": self._success_count,
            "success_rate": self._success_count / max(1, self._request_count),
            "average_duration_ms": self._total_duration_ms / max(1, self._request_count),
            "learning_entries": len(self._learning_data),
            "registry_stats": self.registry.get_statistics(),
        }

    async def get_recommendations(self, request_type: RequestType) -> list[str]:
        """
        Istek tipi icin agent onerileri

        Ogrenme verisine dayanarak en basarili agent'lari oner.
        """
        # Filter learning data by request type
        relevant_data = [
            d for d in self._learning_data
            if d.get("request_type") == request_type.value and d.get("success")
        ]

        if not relevant_data:
            return []

        # Count agent success
        agent_success = {}
        for entry in relevant_data:
            for agent_id in entry.get("agents_used", []):
                if agent_id not in agent_success:
                    agent_success[agent_id] = 0
                agent_success[agent_id] += 1

        # Sort by success count
        sorted_agents = sorted(agent_success.items(), key=lambda x: x[1], reverse=True)

        return [agent_id for agent_id, count in sorted_agents[:5]]


# Factory function
async def create_orchestrator(base_path: str = ".claude") -> MetaOrchestrator:
    """Orkestrator olustur ve baslat"""
    orchestrator = MetaOrchestrator(base_path)
    await orchestrator.initialize()
    return orchestrator
