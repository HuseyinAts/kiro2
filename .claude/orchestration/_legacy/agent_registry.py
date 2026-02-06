"""
Agent Registry - Dinamik Agent Kesfi ve Yonetimi

Tum agent'lari kayit altina alir, kesif yapar ve yasam dongusunu yonetir.
"""

import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from .agent_genome import AgentGenome, AgentStatus, Capability, CapabilityType


class HealthStatus(Enum):
    """Agent saglik durumu"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentDefinition:
    """Agent tanimi - registry'de saklanir"""
    genome: AgentGenome
    file_path: Optional[str] = None
    is_dynamic: bool = False  # Factory tarafindan olusturuldu mu?
    last_heartbeat: datetime = field(default_factory=datetime.now)
    health_status: HealthStatus = HealthStatus.UNKNOWN
    error_count: int = 0
    consecutive_failures: int = 0

    def to_dict(self) -> dict:
        return {
            "genome": self.genome.to_dict(),
            "file_path": self.file_path,
            "is_dynamic": self.is_dynamic,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "health_status": self.health_status.value,
            "error_count": self.error_count,
            "consecutive_failures": self.consecutive_failures,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentDefinition":
        return cls(
            genome=AgentGenome.from_dict(data["genome"]),
            file_path=data.get("file_path"),
            is_dynamic=data.get("is_dynamic", False),
            last_heartbeat=datetime.fromisoformat(data.get("last_heartbeat", datetime.now().isoformat())),
            health_status=HealthStatus(data.get("health_status", "unknown")),
            error_count=data.get("error_count", 0),
            consecutive_failures=data.get("consecutive_failures", 0),
        )


class AgentRegistry:
    """
    Agent Registry - Merkezi agent yonetimi

    Ozellikler:
    - Statik agent'lari .claude/agents/ klasorunden yukle
    - Dinamik agent'lari kayit et
    - Yetenek bazli agent kesfi
    - Saglik kontrolu
    - Yasam dongusu yonetimi
    """

    def __init__(self, base_path: str = ".claude"):
        self.base_path = Path(base_path)
        self.agents_dir = self.base_path / "agents"
        self.registry_file = self.base_path / "orchestration" / "registry.json"

        self._agents: dict[str, AgentDefinition] = {}
        self._capability_index: dict[str, list[str]] = {}  # capability -> agent_ids
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Registry'yi baslat ve mevcut agent'lari yukle"""
        # Load from registry file if exists
        if self.registry_file.exists():
            await self._load_registry()

        # Discover static agents from .md files
        await self._discover_static_agents()

        # Build capability index
        self._build_capability_index()

    async def _load_registry(self) -> None:
        """Registry dosyasindan yukle"""
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for agent_data in data.get("agents", []):
                    agent_def = AgentDefinition.from_dict(agent_data)
                    self._agents[agent_def.genome.agent_id] = agent_def
        except Exception as e:
            print(f"Warning: Could not load registry: {e}")

    async def _save_registry(self) -> None:
        """Registry'yi dosyaya kaydet"""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "agents": [agent.to_dict() for agent in self._agents.values()],
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def _discover_static_agents(self) -> None:
        """Statik .md dosyalarindan agent'lari kesf et"""
        if not self.agents_dir.exists():
            return

        for md_file in self.agents_dir.glob("**/*.md"):
            if md_file.name.startswith("_"):
                continue

            try:
                agent_def = await self._parse_agent_markdown(md_file)
                if agent_def and agent_def.genome.agent_id not in self._agents:
                    self._agents[agent_def.genome.agent_id] = agent_def
            except Exception as e:
                print(f"Warning: Could not parse {md_file}: {e}")

    async def _parse_agent_markdown(self, file_path: Path) -> Optional[AgentDefinition]:
        """Agent .md dosyasini parse et"""
        content = file_path.read_text(encoding="utf-8")

        # Extract agent name from filename
        name = file_path.stem

        # Parse frontmatter if exists (YAML between ---)
        tools = []
        model = "inherit"
        description = ""

        lines = content.split("\n")
        in_frontmatter = False
        frontmatter_lines = []

        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    in_frontmatter = False
                    break
            if in_frontmatter:
                frontmatter_lines.append(line)

        # Simple YAML parsing
        for line in frontmatter_lines:
            if line.startswith("tools:"):
                tools_str = line.replace("tools:", "").strip()
                tools = [t.strip() for t in tools_str.split(",")]
            elif line.startswith("model:"):
                model = line.replace("model:", "").strip()
            elif line.startswith("description:"):
                description = line.replace("description:", "").strip()

        # Create capabilities based on agent name patterns
        capabilities = self._infer_capabilities(name, content)

        genome = AgentGenome(
            agent_id=f"static-{name}",
            name=name,
            tools=tools,
            capabilities=capabilities,
            system_prompt=content,
        )

        return AgentDefinition(
            genome=genome,
            file_path=str(file_path),
            is_dynamic=False,
            health_status=HealthStatus.HEALTHY,
        )

    def _infer_capabilities(self, name: str, content: str) -> list[Capability]:
        """Agent isminden ve icerikten yetenekleri cikar"""
        capabilities = []
        name_lower = name.lower()
        content_lower = content.lower()

        capability_patterns = {
            "backend": (CapabilityType.BACKEND, ["api", "backend", "fastapi", "endpoint"]),
            "frontend": (CapabilityType.FRONTEND, ["frontend", "react", "component", "ui"]),
            "test": (CapabilityType.TESTING, ["test", "pytest", "jest", "coverage"]),
            "debug": (CapabilityType.DEBUGGING, ["debug", "hata", "error", "fix"]),
            "review": (CapabilityType.REVIEW, ["review", "incele", "quality", "pr"]),
            "nlp": (CapabilityType.NLP, ["nlp", "turkce", "turkish", "dil"]),
            "database": (CapabilityType.DATABASE, ["database", "veritabani", "sql", "migration"]),
            "devops": (CapabilityType.DEVOPS, ["devops", "deploy", "docker", "kubernetes"]),
            "content": (CapabilityType.CONTENT, ["content", "icerik", "soru", "question"]),
        }

        for cap_name, (cap_type, keywords) in capability_patterns.items():
            for keyword in keywords:
                if keyword in name_lower or keyword in content_lower:
                    capabilities.append(Capability(
                        name=cap_name,
                        type=cap_type,
                        proficiency=0.7,
                        description=f"Inferred from {keyword}",
                    ))
                    break

        return capabilities

    def _build_capability_index(self) -> None:
        """Yetenek bazli index olustur"""
        self._capability_index.clear()

        for agent_id, agent_def in self._agents.items():
            for cap in agent_def.genome.capabilities:
                cap_key = cap.type.value
                if cap_key not in self._capability_index:
                    self._capability_index[cap_key] = []
                if agent_id not in self._capability_index[cap_key]:
                    self._capability_index[cap_key].append(agent_id)

    async def register_agent(self, agent_def: AgentDefinition) -> str:
        """Yeni agent kayit et"""
        async with self._lock:
            self._agents[agent_def.genome.agent_id] = agent_def
            self._build_capability_index()
            await self._save_registry()
            return agent_def.genome.agent_id

    async def deregister_agent(self, agent_id: str) -> bool:
        """Agent'i kayittan sil"""
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                self._build_capability_index()
                await self._save_registry()
                return True
            return False

    async def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """Agent ID ile getir"""
        return self._agents.get(agent_id)

    async def get_agent_by_name(self, name: str) -> Optional[AgentDefinition]:
        """Agent ismi ile getir"""
        for agent in self._agents.values():
            if agent.genome.name == name:
                return agent
        return None

    async def discover_agents(self, capability: str) -> list[AgentDefinition]:
        """Yetenek bazli agent'lari bul"""
        agent_ids = self._capability_index.get(capability, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    async def discover_by_capabilities(
        self,
        required_capabilities: list[str],
        min_proficiency: float = 0.5
    ) -> list[AgentDefinition]:
        """Birden fazla yetenek gerektiren agent'lari bul"""
        matching_agents = []

        for agent in self._agents.values():
            agent_caps = {c.type.value: c.proficiency for c in agent.genome.capabilities}
            has_all = all(
                cap in agent_caps and agent_caps[cap] >= min_proficiency
                for cap in required_capabilities
            )
            if has_all:
                matching_agents.append(agent)

        # Sort by fitness score
        matching_agents.sort(key=lambda a: a.genome.fitness_score, reverse=True)
        return matching_agents

    async def get_agent_health(self, agent_id: str) -> HealthStatus:
        """Agent saglik durumunu getir"""
        agent = self._agents.get(agent_id)
        if not agent:
            return HealthStatus.UNKNOWN

        # Check consecutive failures
        if agent.consecutive_failures >= 5:
            return HealthStatus.UNHEALTHY
        elif agent.consecutive_failures >= 2:
            return HealthStatus.DEGRADED

        # Check heartbeat
        elapsed = (datetime.now() - agent.last_heartbeat).total_seconds()
        if elapsed > 300:  # 5 dakika
            return HealthStatus.UNHEALTHY
        elif elapsed > 60:  # 1 dakika
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def update_heartbeat(self, agent_id: str) -> None:
        """Agent heartbeat guncelle"""
        if agent_id in self._agents:
            self._agents[agent_id].last_heartbeat = datetime.now()

    async def record_success(self, agent_id: str, response_time_ms: float) -> None:
        """Basarili islem kaydet"""
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            agent.genome.metrics.total_tasks += 1
            agent.genome.metrics.successful_tasks += 1
            agent.consecutive_failures = 0

            # Update average response time
            total = agent.genome.metrics.total_tasks
            current_avg = agent.genome.metrics.avg_response_time_ms
            agent.genome.metrics.avg_response_time_ms = (
                (current_avg * (total - 1) + response_time_ms) / total
            )

            agent.genome.calculate_fitness()
            await self._save_registry()

    async def record_failure(self, agent_id: str) -> None:
        """Basarisiz islem kaydet"""
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            agent.genome.metrics.total_tasks += 1
            agent.genome.metrics.failed_tasks += 1
            agent.consecutive_failures += 1
            agent.error_count += 1
            agent.health_status = await self.get_agent_health(agent_id)
            agent.genome.calculate_fitness()
            await self._save_registry()

    async def list_all_agents(self) -> list[AgentDefinition]:
        """Tum agent'lari listele"""
        return list(self._agents.values())

    async def list_healthy_agents(self) -> list[AgentDefinition]:
        """Saglikli agent'lari listele"""
        healthy = []
        for agent in self._agents.values():
            health = await self.get_agent_health(agent.genome.agent_id)
            if health == HealthStatus.HEALTHY:
                healthy.append(agent)
        return healthy

    async def get_best_agent_for_task(
        self,
        required_capabilities: list[str],
        exclude_ids: Optional[list[str]] = None
    ) -> Optional[AgentDefinition]:
        """Gorev icin en uygun agent'i sec"""
        exclude_ids = exclude_ids or []

        candidates = await self.discover_by_capabilities(required_capabilities)
        candidates = [c for c in candidates if c.genome.agent_id not in exclude_ids]

        if not candidates:
            return None

        # Filter by health
        healthy_candidates = []
        for agent in candidates:
            health = await self.get_agent_health(agent.genome.agent_id)
            if health in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
                healthy_candidates.append(agent)

        if not healthy_candidates:
            return candidates[0]  # Return best even if unhealthy

        # Return highest fitness
        return healthy_candidates[0]

    def get_statistics(self) -> dict:
        """Registry istatistikleri"""
        total = len(self._agents)
        static = sum(1 for a in self._agents.values() if not a.is_dynamic)
        dynamic = total - static

        health_counts = {status.value: 0 for status in HealthStatus}
        for agent in self._agents.values():
            health_counts[agent.health_status.value] += 1

        return {
            "total_agents": total,
            "static_agents": static,
            "dynamic_agents": dynamic,
            "health_distribution": health_counts,
            "capabilities": list(self._capability_index.keys()),
            "capability_coverage": {k: len(v) for k, v in self._capability_index.items()},
        }
