"""
Agent Genome - Agent'in DNA'si

Her agent'in tum ozelliklerini tanimlayan yapisal veri modeli.
Genetik algoritma ile evolusyon icin kullanilir.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import json
import hashlib


class AgentStatus(Enum):
    """Agent durumu"""
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    OFFLINE = "offline"
    EVOLVING = "evolving"
    DEPRECATED = "deprecated"


class ModelProvider(Enum):
    """LLM saglayicilari"""
    ANTHROPIC = "anthropic"     # Claude modelleri
    OPENAI = "openai"           # GPT, o1 modelleri
    GOOGLE = "google"           # Gemini modelleri
    LOCAL = "local"             # Ollama, vLLM, yerel modeller


class AgentModel(Enum):
    """
    Kullanilabilir LLM modelleri - Multi-Provider
    Guncelleme: Ocak 2026

    Kaynaklar:
    - https://platform.claude.com/docs/en/about-claude/pricing
    - https://openai.com/api/pricing/
    - https://ai.google.dev/gemini-api/docs/pricing
    """

    # ============================================
    # ANTHROPIC CLAUDE MODELLERI (Ocak 2026)
    # ============================================
    # Claude 4.5 Serisi (En Guncel - Kasim 2025)
    CLAUDE_OPUS_4_5 = "claude-opus-4-5-20251101"      # En guclü, %67 ucuz
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5-20251101"  # Dengeli
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5-20251101"    # Hizli/ucuz

    # Claude 4 Serisi (Legacy)
    CLAUDE_OPUS_4 = "claude-opus-4-20250514"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"

    # Claude 3 Serisi (Legacy)
    CLAUDE_HAIKU_3 = "claude-3-haiku-20240307"

    # ============================================
    # OPENAI MODELLERI (Ocak 2026)
    # ============================================
    # GPT-5 Serisi (En Guncel)
    GPT5 = "gpt-5"                          # Flagship, agentic coding
    GPT5_MINI = "gpt-5-mini"                # Daha kucuk, ucuz
    GPT5_NANO = "gpt-5-nano"                # En kucuk
    GPT5_2_CODEX = "gpt-5.2-codex"          # Agentic coding icin optimize

    # o-Serisi Reasoning Modelleri
    O3 = "o3"                               # En guclu reasoning
    O3_PRO = "o3-pro"                       # Daha fazla compute
    O3_MINI = "o3-mini"                     # Hizli reasoning
    O4_MINI = "o4-mini"                     # En yeni, verimli reasoning

    # GPT-4 Serisi (Legacy ama hala kullanilir)
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4_1 = "gpt-4.1"                      # GPT-4 guncellemesi

    # ============================================
    # GOOGLE GEMINI MODELLERI (Ocak 2026)
    # ============================================
    # Gemini 3 Serisi (En Guncel)
    GEMINI_3_FLASH = "gemini-3-flash"       # En hizli
    GEMINI_3_PRO = "gemini-3-pro-preview"   # Guclu

    # Gemini 2 Serisi
    GEMINI_2_FLASH = "gemini-2.0-flash"     # Hizli, ucuz
    GEMINI_2_FLASH_LITE = "gemini-2.0-flash-lite"  # En ucuz
    GEMINI_2_PRO = "gemini-2.0-pro"         # Dengeli

    # Gemini 1.5 Serisi (Legacy)
    GEMINI_1_5_PRO = "gemini-1.5-pro"       # 1M context
    GEMINI_1_5_FLASH = "gemini-1.5-flash"

    # ============================================
    # YEREL MODELLER (Ollama/vLLM)
    # ============================================
    QWEN3_8B = "qwen3-8b"                   # Turkce fine-tuned
    QWEN2_5_72B = "qwen2.5-72b"             # Buyuk Qwen
    LLAMA3_3_70B = "llama-3.3-70b"          # Meta Llama
    DEEPSEEK_V3 = "deepseek-v3"             # DeepSeek en yeni
    DEEPSEEK_CODER_V2 = "deepseek-coder-v2" # Coding icin
    CODESTRAL = "codestral-latest"          # Mistral coding

    # ============================================
    # OZEL
    # ============================================
    INHERIT = "inherit"
    AUTO = "auto"  # ModelRouter tarafindan secilecek

    # Geriye uyumluluk alias'lari
    HAIKU = "claude-haiku-4-5-20251101"
    SONNET = "claude-sonnet-4-5-20251101"
    OPUS = "claude-opus-4-5-20251101"

    @property
    def provider(self) -> ModelProvider:
        """Model'in provider'ini dondur"""
        provider_map = {
            # Anthropic
            "claude-opus-4-5-20251101": ModelProvider.ANTHROPIC,
            "claude-sonnet-4-5-20251101": ModelProvider.ANTHROPIC,
            "claude-haiku-4-5-20251101": ModelProvider.ANTHROPIC,
            "claude-opus-4-20250514": ModelProvider.ANTHROPIC,
            "claude-sonnet-4-20250514": ModelProvider.ANTHROPIC,
            "claude-3-haiku-20240307": ModelProvider.ANTHROPIC,
            # OpenAI
            "gpt-5": ModelProvider.OPENAI,
            "gpt-5-mini": ModelProvider.OPENAI,
            "gpt-5-nano": ModelProvider.OPENAI,
            "gpt-5.2-codex": ModelProvider.OPENAI,
            "o3": ModelProvider.OPENAI,
            "o3-pro": ModelProvider.OPENAI,
            "o3-mini": ModelProvider.OPENAI,
            "o4-mini": ModelProvider.OPENAI,
            "gpt-4o": ModelProvider.OPENAI,
            "gpt-4o-mini": ModelProvider.OPENAI,
            "gpt-4-turbo": ModelProvider.OPENAI,
            "gpt-4.1": ModelProvider.OPENAI,
            # Google
            "gemini-3-flash": ModelProvider.GOOGLE,
            "gemini-3-pro-preview": ModelProvider.GOOGLE,
            "gemini-2.0-flash": ModelProvider.GOOGLE,
            "gemini-2.0-flash-lite": ModelProvider.GOOGLE,
            "gemini-2.0-pro": ModelProvider.GOOGLE,
            "gemini-1.5-pro": ModelProvider.GOOGLE,
            "gemini-1.5-flash": ModelProvider.GOOGLE,
            # Local
            "qwen3-8b": ModelProvider.LOCAL,
            "qwen2.5-72b": ModelProvider.LOCAL,
            "llama-3.3-70b": ModelProvider.LOCAL,
            "deepseek-v3": ModelProvider.LOCAL,
            "deepseek-coder-v2": ModelProvider.LOCAL,
            "codestral-latest": ModelProvider.LOCAL,
        }
        return provider_map.get(self.value, ModelProvider.ANTHROPIC)

    @property
    def cost_per_1k_tokens(self) -> dict:
        """
        Token basina maliyet (USD) - input/output per 1K tokens
        Guncelleme: Ocak 2026
        """
        costs = {
            # Anthropic Claude 4.5 (Kasim 2025 fiyatlari)
            "claude-opus-4-5-20251101": {"input": 0.005, "output": 0.025},      # %67 ucuzladi
            "claude-sonnet-4-5-20251101": {"input": 0.003, "output": 0.015},
            "claude-haiku-4-5-20251101": {"input": 0.001, "output": 0.005},
            # Anthropic Claude 4 (Legacy)
            "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
            "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},

            # OpenAI GPT-5 Serisi
            "gpt-5": {"input": 0.00125, "output": 0.01},
            "gpt-5-mini": {"input": 0.00025, "output": 0.002},
            "gpt-5-nano": {"input": 0.00005, "output": 0.0004},
            "gpt-5.2-codex": {"input": 0.00125, "output": 0.01},
            # OpenAI o-Serisi
            "o3": {"input": 0.002, "output": 0.008},
            "o3-pro": {"input": 0.01, "output": 0.04},
            "o3-mini": {"input": 0.0011, "output": 0.0044},
            "o4-mini": {"input": 0.0011, "output": 0.0044},
            # OpenAI GPT-4 Serisi
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4.1": {"input": 0.002, "output": 0.008},

            # Google Gemini
            "gemini-3-flash": {"input": 0.0001, "output": 0.0004},
            "gemini-3-pro-preview": {"input": 0.002, "output": 0.008},
            "gemini-2.0-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-2.0-flash-lite": {"input": 0.00005, "output": 0.0002},
            "gemini-2.0-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},

            # Local - Ucretsiz
            "qwen3-8b": {"input": 0.0, "output": 0.0},
            "qwen2.5-72b": {"input": 0.0, "output": 0.0},
            "llama-3.3-70b": {"input": 0.0, "output": 0.0},
            "deepseek-v3": {"input": 0.0, "output": 0.0},
            "deepseek-coder-v2": {"input": 0.0, "output": 0.0},
            "codestral-latest": {"input": 0.0, "output": 0.0},
        }
        return costs.get(self.value, {"input": 0.0, "output": 0.0})

    @property
    def context_window(self) -> int:
        """Maksimum context penceresi (token)"""
        windows = {
            # Anthropic
            "claude-opus-4-5-20251101": 200000,
            "claude-sonnet-4-5-20251101": 200000,
            "claude-haiku-4-5-20251101": 200000,
            "claude-opus-4-20250514": 200000,
            "claude-sonnet-4-20250514": 200000,
            "claude-3-haiku-20240307": 200000,
            # OpenAI
            "gpt-5": 196000,
            "gpt-5-mini": 128000,
            "gpt-5-nano": 64000,
            "gpt-5.2-codex": 196000,
            "o3": 200000,
            "o3-pro": 200000,
            "o3-mini": 200000,
            "o4-mini": 200000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4.1": 128000,
            # Google
            "gemini-3-flash": 1000000,
            "gemini-3-pro-preview": 1000000,
            "gemini-2.0-flash": 1000000,
            "gemini-2.0-flash-lite": 1000000,
            "gemini-2.0-pro": 1000000,
            "gemini-1.5-pro": 1000000,
            "gemini-1.5-flash": 1000000,
            # Local
            "qwen3-8b": 32000,
            "qwen2.5-72b": 128000,
            "llama-3.3-70b": 128000,
            "deepseek-v3": 128000,
            "deepseek-coder-v2": 128000,
            "codestral-latest": 32000,
        }
        return windows.get(self.value, 8192)

    @property
    def tier(self) -> str:
        """Model seviyesi: budget, standard, premium, reasoning, flagship"""
        tiers = {
            # Budget - Hizli, ucuz
            "claude-haiku-4-5-20251101": "budget",
            "claude-3-haiku-20240307": "budget",
            "gpt-5-nano": "budget",
            "gpt-4o-mini": "budget",
            "gemini-2.0-flash": "budget",
            "gemini-2.0-flash-lite": "budget",
            "gemini-3-flash": "budget",

            # Standard - Dengeli
            "claude-sonnet-4-5-20251101": "standard",
            "claude-sonnet-4-20250514": "standard",
            "gpt-5-mini": "standard",
            "gpt-4o": "standard",
            "gpt-4.1": "standard",
            "gemini-2.0-pro": "standard",
            "gemini-1.5-pro": "standard",

            # Premium - En iyi kalite
            "claude-opus-4-5-20251101": "premium",
            "claude-opus-4-20250514": "premium",
            "gpt-5": "premium",
            "gpt-4-turbo": "premium",
            "gemini-3-pro-preview": "premium",

            # Flagship - Agentic/Coding
            "gpt-5.2-codex": "flagship",

            # Reasoning - Derin dusunme
            "o3": "reasoning",
            "o3-pro": "reasoning",
            "o3-mini": "reasoning",
            "o4-mini": "reasoning",

            # Local
            "qwen3-8b": "local",
            "qwen2.5-72b": "local",
            "llama-3.3-70b": "local",
            "deepseek-v3": "local",
            "deepseek-coder-v2": "local",
            "codestral-latest": "local",
        }
        return tiers.get(self.value, "standard")

    @property
    def max_output_tokens(self) -> int:
        """Maksimum output token sayisi"""
        outputs = {
            "claude-opus-4-5-20251101": 64000,   # 2x artirildi
            "claude-sonnet-4-5-20251101": 16000,
            "claude-haiku-4-5-20251101": 8192,
            "gpt-5": 32000,
            "gpt-5.2-codex": 32000,
            "o3": 100000,
            "o3-mini": 100000,
            "o4-mini": 100000,
            "gemini-2.0-flash": 8192,
            "gemini-1.5-pro": 8192,
        }
        return outputs.get(self.value, 4096)


class CapabilityType(Enum):
    """Yetenek kategorileri"""
    CODING = "coding"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    REVIEW = "review"
    TESTING = "testing"
    DEBUGGING = "debugging"
    NLP = "nlp"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    CONTENT = "content"
    COORDINATION = "coordination"
    LEARNING = "learning"


@dataclass
class Capability:
    """Agent yetenegi tanimi"""
    name: str
    type: CapabilityType
    proficiency: float = 0.5  # 0.0 - 1.0 arasi
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "proficiency": self.proficiency,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Capability":
        return cls(
            name=data["name"],
            type=CapabilityType(data["type"]),
            proficiency=data.get("proficiency", 0.5),
            description=data.get("description", ""),
        )


@dataclass
class PerformanceMetrics:
    """Agent performans metrikleri"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time_ms: float = 0.0
    total_tokens_used: int = 0
    user_ratings: list[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks

    @property
    def avg_user_rating(self) -> float:
        if not self.user_ratings:
            return 0.0
        return sum(self.user_ratings) / len(self.user_ratings)

    def to_dict(self) -> dict:
        return {
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_response_time_ms": self.avg_response_time_ms,
            "total_tokens_used": self.total_tokens_used,
            "user_ratings": self.user_ratings,
            "success_rate": self.success_rate,
            "avg_user_rating": self.avg_user_rating,
        }


@dataclass
class LearningParameters:
    """Ogrenme parametreleri"""
    learning_rate: float = 0.01
    exploration_rate: float = 0.1  # Epsilon-greedy
    memory_size: int = 1000
    batch_size: int = 32
    discount_factor: float = 0.99

    def to_dict(self) -> dict:
        return {
            "learning_rate": self.learning_rate,
            "exploration_rate": self.exploration_rate,
            "memory_size": self.memory_size,
            "batch_size": self.batch_size,
            "discount_factor": self.discount_factor,
        }


@dataclass
class AgentGenome:
    """
    Agent'in DNA'si - tum ozellikleri tanimlar

    Genetik algoritma operasyonlari:
    - Crossover: Iki parent'in ozelliklerini birlestir
    - Mutation: Rastgele degisiklikler
    - Selection: Fitness'a gore secim
    """

    # Kimlik
    agent_id: str
    name: str
    version: str = "1.0.0"
    parent_id: Optional[str] = None
    generation: int = 0

    # Yetenekler
    capabilities: list[Capability] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    model: AgentModel = AgentModel.INHERIT

    # Davranis
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = ""

    # Ogrenme Parametreleri
    learning_params: LearningParameters = field(default_factory=LearningParameters)

    # Performans Metrikleri
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)

    # Fitness Skoru (0.0 - 1.0)
    fitness_score: float = 0.5

    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: AgentStatus = AgentStatus.IDLE

    def __post_init__(self):
        if not self.agent_id:
            self.agent_id = self._generate_id()

    def _generate_id(self) -> str:
        """Benzersiz agent ID olustur"""
        content = f"{self.name}-{self.version}-{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def calculate_fitness(self) -> float:
        """
        Fitness skorunu hesapla

        Faktörler:
        - Success rate (%40)
        - Response time (%20)
        - User rating (%25)
        - Capability coverage (%15)
        """
        # Success rate (0-1)
        success_score = self.metrics.success_rate * 0.4

        # Response time (lower is better, normalize to 0-1)
        # Assume 5000ms is worst, 100ms is best
        rt = self.metrics.avg_response_time_ms
        if rt <= 100:
            time_score = 1.0
        elif rt >= 5000:
            time_score = 0.0
        else:
            time_score = 1.0 - ((rt - 100) / 4900)
        time_score *= 0.2

        # User rating (0-5 to 0-1)
        rating_score = (self.metrics.avg_user_rating / 5.0) * 0.25

        # Capability coverage (proficiency average)
        if self.capabilities:
            cap_score = sum(c.proficiency for c in self.capabilities) / len(self.capabilities)
        else:
            cap_score = 0.0
        cap_score *= 0.15

        self.fitness_score = success_score + time_score + rating_score + cap_score
        return self.fitness_score

    def mutate(self, mutation_rate: float = 0.1) -> "AgentGenome":
        """
        Genome'u mutasyona ugrat

        Args:
            mutation_rate: Mutasyon olasiligi (0.0 - 1.0)

        Returns:
            Mutasyona ugramis yeni genome
        """
        import random
        import copy

        mutated = copy.deepcopy(self)
        mutated.parent_id = self.agent_id
        mutated.generation = self.generation + 1
        mutated.agent_id = mutated._generate_id()

        # Temperature mutation
        if random.random() < mutation_rate:
            mutated.temperature = max(0.0, min(2.0,
                self.temperature + random.gauss(0, 0.1)))

        # Learning rate mutation
        if random.random() < mutation_rate:
            mutated.learning_params.learning_rate = max(0.001, min(0.1,
                self.learning_params.learning_rate + random.gauss(0, 0.01)))

        # Exploration rate mutation
        if random.random() < mutation_rate:
            mutated.learning_params.exploration_rate = max(0.01, min(0.5,
                self.learning_params.exploration_rate + random.gauss(0, 0.05)))

        # Capability proficiency mutation
        for cap in mutated.capabilities:
            if random.random() < mutation_rate:
                cap.proficiency = max(0.0, min(1.0,
                    cap.proficiency + random.gauss(0, 0.1)))

        mutated.updated_at = datetime.now()
        mutated.metrics = PerformanceMetrics()  # Reset metrics

        return mutated

    @staticmethod
    def crossover(parent1: "AgentGenome", parent2: "AgentGenome") -> "AgentGenome":
        """
        Iki parent'in ozelliklerini birlestir

        Args:
            parent1: Birinci parent genome
            parent2: Ikinci parent genome

        Returns:
            Yeni child genome
        """
        import random

        child = AgentGenome(
            agent_id="",  # Will be generated
            name=f"{parent1.name}-{parent2.name[:3]}",
            version="1.0.0",
            parent_id=parent1.agent_id,
            generation=max(parent1.generation, parent2.generation) + 1,
        )

        # Crossover capabilities
        all_caps = {}
        for cap in parent1.capabilities + parent2.capabilities:
            if cap.name not in all_caps:
                all_caps[cap.name] = cap
            else:
                # Average proficiency
                existing = all_caps[cap.name]
                existing.proficiency = (existing.proficiency + cap.proficiency) / 2
        child.capabilities = list(all_caps.values())

        # Crossover tools (union)
        child.tools = list(set(parent1.tools + parent2.tools))

        # Crossover model (prefer higher performing parent)
        child.model = parent1.model if parent1.fitness_score >= parent2.fitness_score else parent2.model

        # Crossover parameters (average)
        child.temperature = (parent1.temperature + parent2.temperature) / 2
        child.max_tokens = max(parent1.max_tokens, parent2.max_tokens)

        # Learning params crossover
        child.learning_params = LearningParameters(
            learning_rate=(parent1.learning_params.learning_rate + parent2.learning_params.learning_rate) / 2,
            exploration_rate=(parent1.learning_params.exploration_rate + parent2.learning_params.exploration_rate) / 2,
            memory_size=max(parent1.learning_params.memory_size, parent2.learning_params.memory_size),
        )

        # System prompt - prefer higher fitness
        child.system_prompt = parent1.system_prompt if parent1.fitness_score >= parent2.fitness_score else parent2.system_prompt

        return child

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "tools": self.tools,
            "model": self.model.value,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "learning_params": self.learning_params.to_dict(),
            "metrics": self.metrics.to_dict(),
            "fitness_score": self.fitness_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentGenome":
        """Deserialize from dictionary"""
        genome = cls(
            agent_id=data["agent_id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            parent_id=data.get("parent_id"),
            generation=data.get("generation", 0),
        )

        genome.capabilities = [Capability.from_dict(c) for c in data.get("capabilities", [])]
        genome.tools = data.get("tools", [])
        genome.model = AgentModel(data.get("model", "inherit"))
        genome.temperature = data.get("temperature", 0.7)
        genome.max_tokens = data.get("max_tokens", 4096)
        genome.system_prompt = data.get("system_prompt", "")

        if "learning_params" in data:
            lp = data["learning_params"]
            genome.learning_params = LearningParameters(
                learning_rate=lp.get("learning_rate", 0.01),
                exploration_rate=lp.get("exploration_rate", 0.1),
                memory_size=lp.get("memory_size", 1000),
            )

        if "metrics" in data:
            m = data["metrics"]
            genome.metrics = PerformanceMetrics(
                total_tasks=m.get("total_tasks", 0),
                successful_tasks=m.get("successful_tasks", 0),
                failed_tasks=m.get("failed_tasks", 0),
                avg_response_time_ms=m.get("avg_response_time_ms", 0.0),
                total_tokens_used=m.get("total_tokens_used", 0),
                user_ratings=m.get("user_ratings", []),
            )

        genome.fitness_score = data.get("fitness_score", 0.5)
        genome.status = AgentStatus(data.get("status", "idle"))

        if "created_at" in data:
            genome.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            genome.updated_at = datetime.fromisoformat(data["updated_at"])

        return genome

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentGenome":
        """Deserialize from JSON string"""
        return cls.from_dict(json.loads(json_str))
