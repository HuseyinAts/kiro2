"""
Base Domain Agent - Tum Alan Uzman Agent'lar icin Temel Sinif
REQ-1 to REQ-6, REQ-7.1, REQ-7.2
Teknofest 2025 - KIRO2 YKS Platformu

Sid Bidasaria subagent mimarisi uygulamasi:
- 200K token context izolasyonu (REQ-7.2)
- Domain-specific knowledge loading
- Tool integration (SymPy, matplotlib, Zemberek, etc.)
- Specialization scoring desteği
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..base_agent import AgentStatus, AgentType, BaseAgent

logger = logging.getLogger(__name__)


class DomainType(str, Enum):
    """Alan turleri (REQ-1 to REQ-6)"""

    MATEMATIK = "matematik"  # REQ-1: Cebir, Geometri, Analiz, Olasilik
    FIZIK = "fizik"  # REQ-2: Mekanik, Elektrik, Optik, Termodinamik
    TURKCE = "turkce"  # REQ-3: Dilbilgisi, Edebiyat, Anlam Bilgisi
    SOSYAL = "sosyal"  # REQ-4: Tarih, Cografya, Felsefe, Din Kulturu
    BIYOLOJI = "biyoloji"  # REQ-5: Hucre, Genetik, Ekoloji, Anatomi
    YABANCI_DIL = "yabanci_dil"  # REQ-6: Grammar, Vocabulary, Reading, Writing


@dataclass
class DomainContext:
    """
    Agent context container (REQ-7.2: 200K token limit)

    Her agent icin izole context, domain bilgisi ve gecmis
    """

    domain: DomainType
    max_tokens: int = 200_000  # CRITICAL: 200K limit per agent
    current_tokens: int = 0
    domain_knowledge: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    shared_context: dict[str, Any] = field(default_factory=dict)  # From blackboard
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def can_add_tokens(self, token_count: int) -> bool:
        """Token limiti asilmadan eklenebilir mi?"""
        return (self.current_tokens + token_count) <= self.max_tokens

    def add_tokens(self, token_count: int) -> bool:
        """Token ekle, limit asilirsa False dondur"""
        if not self.can_add_tokens(token_count):
            logger.warning(
                f"Token limit would be exceeded: {self.current_tokens} + {token_count} > {self.max_tokens}"
            )
            return False
        self.current_tokens += token_count
        self.last_updated = datetime.now()
        return True

    def get_remaining_tokens(self) -> int:
        """Kalan token sayisi"""
        return self.max_tokens - self.current_tokens

    def clear_history(self):
        """Gecmisi temizle, token sayacini sifirla"""
        history_tokens = self._estimate_history_tokens()
        self.conversation_history.clear()
        self.current_tokens = max(0, self.current_tokens - history_tokens)
        self.last_updated = datetime.now()
        logger.info(f"Context history cleared, freed ~{history_tokens} tokens")

    def _estimate_history_tokens(self) -> int:
        """Gecmisteki token sayisini tahmin et (4 char ~ 1 token)"""
        total_chars = sum(
            len(str(msg.get("content", ""))) for msg in self.conversation_history
        )
        return total_chars // 4

    def add_domain_knowledge(
        self,
        content: str,
        topic: str = "general",
        estimated_tokens: int = 0
    ) -> bool:
        """
        Domain bilgisi ekle

        Args:
            content: Bilgi icerigi
            topic: Konu anahtari (ornegin: temel_kavramlar, formuller)
            estimated_tokens: Tahmini token sayisi (0 ise otomatik hesaplanir)

        Returns:
            bool: Ekleme basarili mi?
        """
        if estimated_tokens == 0:
            # Otomatik token tahmini (Turkish ~3.5 chars per token)
            estimated_tokens = len(str(content)) // 4

        if not self.can_add_tokens(estimated_tokens):
            logger.warning(f"Cannot add domain knowledge '{topic}': token limit would be exceeded")
            return False

        self.domain_knowledge[topic] = content
        self.add_tokens(estimated_tokens)
        logger.debug(f"Added domain knowledge '{topic}' (~{estimated_tokens} tokens)")
        return True

    def add_to_history(self, role: str, content: str) -> bool:
        """
        Konusma gecmisine ekle

        Args:
            role: 'user' veya 'assistant'
            content: Mesaj icerigi

        Returns:
            bool: Ekleme basarili mi?
        """
        estimated_tokens = len(content) // 4
        if not self.can_add_tokens(estimated_tokens):
            logger.warning("Cannot add to history: token limit would be exceeded")
            return False

        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.add_tokens(estimated_tokens)
        return True

    def get_status(self) -> dict[str, Any]:
        """Context durumunu dondur"""
        return {
            "domain": self.domain.value,
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "remaining_tokens": self.get_remaining_tokens(),
            "usage_percentage": (self.current_tokens / self.max_tokens) * 100,
            "history_length": len(self.conversation_history),
            "knowledge_keys": list(self.domain_knowledge.keys()),
            "last_updated": self.last_updated.isoformat(),
        }

    def update_shared_context(self, data: dict[str, Any]):
        """Blackboard'dan gelen paylasilan context'i guncelle"""
        self.shared_context.update(data)
        self.last_updated = datetime.now()

    # === Alias methods for test compatibility ===

    def add_content(self, content: str, topic: str = "general") -> bool:
        """
        Add content to context (test compatibility alias for add_domain_knowledge)

        Args:
            content: Content to add
            topic: Topic key

        Returns:
            bool: Success
        """
        return self.add_domain_knowledge(content, topic)

    def get_content(self) -> str:
        """
        Get combined content from context

        Returns:
            str: Combined domain knowledge content
        """
        parts = []
        for key, value in self.domain_knowledge.items():
            parts.append(f"[{key}]: {value}")
        return "\n".join(parts)

    def add_message(self, role: str, content: str) -> bool:
        """
        Add message to conversation history (alias for add_to_history)

        Args:
            role: 'user' or 'assistant'
            content: Message content

        Returns:
            bool: Success
        """
        return self.add_to_history(role, content)

    @property
    def token_count(self) -> int:
        """Current token count (test compatibility property)"""
        return self.current_tokens


@dataclass
class DomainResponse:
    """
    Agent yanit yapisi

    Attributes:
        domain: Yaniti ureten agent'in alani
        content: Ana yanit icerigi
        confidence: Yanit guven skoru [0, 1]
        tools_used: Kullanilan araclar (SymPy, matplotlib, etc.)
        visualizations: Olusturulan gorseller (base64 veya path)
        references: Kaynak referanslari
        context_additions: Blackboard'a yazilacak context
        response_time_ms: Yanit suresi (milisaniye)
        tokens_used: Kullanilan token sayisi
    """

    domain: DomainType
    content: str
    confidence: float = 0.0  # [0, 1]
    tools_used: list[str] = field(default_factory=list)
    visualizations: list[dict[str, Any]] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    context_additions: dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0.0
    tokens_used: int = 0
    step_by_step_solution: list[str] = field(default_factory=list)
    latex_expressions: list[str] = field(default_factory=list)
    error: str | None = None

    def is_successful(self) -> bool:
        """Yanit basarili mi?"""
        return self.error is None and len(self.content) > 0

    def to_dict(self) -> dict[str, Any]:
        """Dict'e donustur"""
        return {
            "domain": self.domain.value,
            "content": self.content,
            "confidence": self.confidence,
            "tools_used": self.tools_used,
            "visualizations": self.visualizations,
            "references": self.references,
            "context_additions": self.context_additions,
            "response_time_ms": self.response_time_ms,
            "tokens_used": self.tokens_used,
            "step_by_step_solution": self.step_by_step_solution,
            "latex_expressions": self.latex_expressions,
            "error": self.error,
        }


class BaseDomainAgent(BaseAgent):
    """
    Tum Alan Uzman Agent'lar icin temel sinif

    Ozellikler:
    - 200K token izole context (REQ-7.2)
    - Domain-specific tool integration
    - Step-by-step solution generation
    - Blackboard koordinasyonu
    """

    def __init__(
        self,
        agent_id: str,
        domain: DomainType,
        specialization_areas: list[str],
        llm_service: Any = None,
    ):
        """
        Domain Expert Agent olustur

        Args:
            agent_id: Benzersiz agent ID
            domain: Agent'in uzmanlik alani
            specialization_areas: Alt uzmanlik alanlari
            llm_service: LLM servisi (LangChain)
        """
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.CONTENT_MANAGER,  # Re-use existing type
            name=f"{domain.value.capitalize()} Expert Agent",
            description=f"YKS {domain.value} alani uzman agent'i",
        )

        self.domain = domain
        self.specialization_areas = specialization_areas
        self.llm_service = llm_service

        # Context management (REQ-7.2)
        self.context = DomainContext(domain=domain)

        # Domain-specific tools
        self.tools: dict[str, callable] = {}

        # Performance tracking
        self.total_questions_answered = 0
        self.total_tokens_used = 0
        self.average_confidence = 0.0

        # Initialize domain-specific components
        self._load_domain_knowledge()
        self._register_tools()

        logger.info(
            f"Initialized {domain.value} agent with areas: {specialization_areas}"
        )

    @abstractmethod
    def _load_domain_knowledge(self):
        """
        Domain bilgisini yukle (alt siniflar implement eder)

        Her domain icin:
        - Temel kavramlar
        - Formüller/kurallar
        - Ornek sorular
        - YKS/TYT/AYT spesifik bilgiler
        """

    @abstractmethod
    def _register_tools(self):
        """
        Domain-specific araclari kaydet (alt siniflar implement eder)

        Ornek:
        - Matematik: SymPy, matplotlib
        - Turkce: Zemberek
        - Fizik: Unit analysis
        """

    @abstractmethod
    async def solve_question(
        self,
        question: str,
        shared_context: dict[str, Any] | None = None,
    ) -> DomainResponse:
        """
        Soruyu coz (alt siniflar implement eder)

        Args:
            question: Soru metni
            shared_context: Blackboard'dan gelen paylasilan context

        Returns:
            DomainResponse: Cozum yaniti
        """

    async def process_request(
        self,
        request_type: str,
        parameters: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        BaseAgent abstract metodunu implement et

        Args:
            request_type: "solve_question", "explain_concept", etc.
            parameters: Istek parametreleri
            context: Ek context

        Returns:
            Islem sonucu
        """
        import time

        start_time = time.perf_counter()

        try:
            self.status = AgentStatus.WORKING

            if request_type == "solve_question":
                question = parameters.get("question", "")
                shared_context = parameters.get("shared_context", {})

                response = await self.solve_question(question, shared_context)

                # Apply IRT-based confidence adjustment if theta provided
                student_theta = parameters.get("student_theta")
                question_difficulty = parameters.get("question_difficulty", 0.0)
                if student_theta is not None:
                    response.confidence = self.adjust_confidence_with_irt(
                        response.confidence, question_difficulty, student_theta
                    )

                return {
                    "success": response.is_successful(),
                    "response": response.to_dict(),
                    "processing_time_ms": (time.perf_counter() - start_time) * 1000,
                }

            if request_type == "get_specialization_areas":
                return {
                    "success": True,
                    "domain": self.domain.value,
                    "areas": self.specialization_areas,
                }

            if request_type == "get_context_status":
                return {
                    "success": True,
                    "current_tokens": self.context.current_tokens,
                    "max_tokens": self.context.max_tokens,
                    "remaining_tokens": self.context.get_remaining_tokens(),
                }

            return {
                "success": False,
                "error": f"Unknown request type: {request_type}",
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            self.status = AgentStatus.IDLE

    def adjust_confidence_with_irt(
        self,
        base_confidence: float,
        question_difficulty: float,
        student_theta: float | None = None,
    ) -> float:
        """
        Adjust response confidence using IRT model parameters.

        When student ability (theta) is known, we can better estimate
        whether the agent's answer is appropriate for the student's level.

        Args:
            base_confidence: Agent's base confidence [0, 1]
            question_difficulty: IRT difficulty parameter (b) [-4, 4]
            student_theta: Student ability estimate [-4, 4] (optional)

        Returns:
            Adjusted confidence [0, 1]
        """
        import math

        if student_theta is None:
            return base_confidence

        # Clamp inputs to valid ranges
        base_confidence = max(0.0, min(1.0, base_confidence))
        question_difficulty = max(-4.0, min(4.0, question_difficulty))
        student_theta = max(-4.0, min(4.0, student_theta))

        # IRT 3PL success probability
        exponent = -(student_theta - question_difficulty)
        exponent = max(-20.0, min(20.0, exponent))
        p_success = 1.0 / (1.0 + math.exp(exponent))

        # If question is in student's ZPD (0.15-0.85), boost confidence
        if 0.15 <= p_success <= 0.85:
            zpd_bonus = 0.1
        else:
            zpd_bonus = -0.05

        adjusted = min(1.0, max(0.0, base_confidence + zpd_bonus))
        logger.debug(
            f"IRT confidence: base={base_confidence:.2f}, "
            f"theta={student_theta:.2f}, b={question_difficulty:.2f}, "
            f"P={p_success:.2f}, adjusted={adjusted:.2f}"
        )
        return adjusted

    def get_tool(self, tool_name: str) -> callable | None:
        """Kayitli araci al"""
        return self.tools.get(tool_name)

    def register_tool(self, name: str, func: callable, description: str = ""):
        """Yeni arac kaydet"""
        self.tools[name] = func
        logger.debug(f"Registered tool '{name}' for {self.domain.value} agent")

    async def update_context_from_blackboard(self, shared_context: dict[str, Any]):
        """Blackboard'dan gelen context ile guncelle"""
        if shared_context:
            self.context.shared_context.update(shared_context)
            # Estimate tokens added
            context_str = str(shared_context)
            token_estimate = len(context_str) // 4
            self.context.add_tokens(token_estimate)
            logger.debug(f"Updated shared context, added ~{token_estimate} tokens")

    def get_performance_metrics(self) -> dict[str, Any]:
        """Agent performans metriklerini al"""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain.value,
            "specialization_areas": self.specialization_areas,
            "total_questions_answered": self.total_questions_answered,
            "total_tokens_used": self.total_tokens_used,
            "average_confidence": self.average_confidence,
            "context_usage": {
                "current_tokens": self.context.current_tokens,
                "max_tokens": self.context.max_tokens,
                "usage_percentage": (
                    self.context.current_tokens / self.context.max_tokens * 100
                ),
            },
            "tools_registered": list(self.tools.keys()),
        }

    def _count_tokens(self, text: str) -> int:
        """
        Token sayisini hesapla (tiktoken yoksa tahmin)

        Production'da tiktoken kullanilmali
        """
        try:
            import tiktoken

            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except ImportError:
            # Fallback: 4 karakter ~ 1 token
            return len(text) // 4

    def _update_performance_metrics(self, response: DomainResponse):
        """Performans metriklerini guncelle"""
        self.total_questions_answered += 1
        self.total_tokens_used += response.tokens_used

        # Running average for confidence
        n = self.total_questions_answered
        self.average_confidence = (
            self.average_confidence * (n - 1) + response.confidence
        ) / n
