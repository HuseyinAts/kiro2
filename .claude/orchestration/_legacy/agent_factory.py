"""
Agent Factory - Dinamik Agent Olusturma ve Guncelleme

Ihtiyaca gore yeni agent'lar olusturur ve mevcut agent'lari gelistirir.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from .agent_genome import (
    AgentGenome,
    AgentModel,
    AgentStatus,
    Capability,
    CapabilityType,
    LearningParameters,
    PerformanceMetrics,
)
from .agent_registry import AgentRegistry, AgentDefinition


class TemplateType(Enum):
    """Temel agent sablonlari"""
    WORKER = "worker"          # Genel gorev isleyici
    ANALYZER = "analyzer"      # Analiz ve inceleme
    LEARNER = "learner"        # Ogrenme ve adaptasyon
    COORDINATOR = "coordinator" # Diger agent'lari koordine
    SPECIALIST = "specialist"  # Uzman alan bilgisi
    VALIDATOR = "validator"    # Dogrulama ve kalite kontrol
    OPTIMIZER = "optimizer"    # Performans optimizasyonu


@dataclass
class BaseTemplate:
    """Temel agent sablonu"""
    template_type: TemplateType
    name: str
    description: str
    default_capabilities: list[Capability] = field(default_factory=list)
    default_tools: list[str] = field(default_factory=list)
    default_model: AgentModel = AgentModel.INHERIT
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    system_prompt_template: str = ""

    def to_dict(self) -> dict:
        return {
            "template_type": self.template_type.value,
            "name": self.name,
            "description": self.description,
            "default_capabilities": [c.to_dict() for c in self.default_capabilities],
            "default_tools": self.default_tools,
            "default_model": self.default_model.value,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "system_prompt_template": self.system_prompt_template,
        }


@dataclass
class MutationConfig:
    """Mutasyon konfigurasyonu"""
    mutation_rate: float = 0.1
    temperature_variance: float = 0.1
    learning_rate_variance: float = 0.01
    exploration_rate_variance: float = 0.05
    capability_mutation_chance: float = 0.1
    tool_mutation_chance: float = 0.05


class AgentFactory:
    """
    Agent Factory - Dinamik Agent Olusturma

    Gorevler:
    - Sablon bazli yeni agent olusturma
    - Mevcut agent'lari klonlama ve mutasyon
    - Performans bazli agent gelistirme
    - Agent sablonlarini yonetme
    """

    # 7 Temel Sablon
    BASE_TEMPLATES = {
        TemplateType.WORKER: BaseTemplate(
            template_type=TemplateType.WORKER,
            name="Base Worker",
            description="Genel gorev isleyici agent",
            default_capabilities=[
                Capability(name="task_execution", type=CapabilityType.CODING, proficiency=0.7),
            ],
            default_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            default_model=AgentModel.SONNET,
            system_prompt_template="""
Sen bir gorev isleyici agent'sin. Verilen gorevleri dikkatli ve metodlu bir sekilde yerine getir.

Kurallar:
- Kod yazarken KIRO2 projesi standartlarina uy
- Turkce yorumlar ve aciklamalar kullan
- Her degisiklik icin test yazilmali
- Hatalari yakala ve raporla

Gorev: {task_description}
""",
        ),
        TemplateType.ANALYZER: BaseTemplate(
            template_type=TemplateType.ANALYZER,
            name="Base Analyzer",
            description="Kod ve sistem analizi yapan agent",
            default_capabilities=[
                Capability(name="code_analysis", type=CapabilityType.ANALYSIS, proficiency=0.8),
                Capability(name="pattern_detection", type=CapabilityType.ANALYSIS, proficiency=0.7),
            ],
            default_tools=["Read", "Glob", "Grep"],
            default_model=AgentModel.OPUS,
            default_temperature=0.3,
            system_prompt_template="""
Sen bir analiz uzman agent'sin. Kodu ve sistemi derinlemesine analiz et.

Gorevler:
- Kod kalitesini degerlendir
- Potansiyel sorunlari tespit et
- Iyilestirme onerileri sun
- Pattern'leri ve anti-pattern'leri belirle

Analiz hedefi: {analysis_target}
""",
        ),
        TemplateType.LEARNER: BaseTemplate(
            template_type=TemplateType.LEARNER,
            name="Base Learner",
            description="Ogrenme ve adaptasyon agent'i",
            default_capabilities=[
                Capability(name="pattern_learning", type=CapabilityType.LEARNING, proficiency=0.6),
                Capability(name="feedback_processing", type=CapabilityType.LEARNING, proficiency=0.7),
            ],
            default_tools=["Read", "Glob", "Grep"],
            default_model=AgentModel.SONNET,
            default_temperature=0.5,
            system_prompt_template="""
Sen bir ogrenme agent'isin. Deneyimlerden ve geri bildirimlerden ogren.

Gorevler:
- Basarili pattern'leri kaydet
- Hatalarden ders cikar
- Ogrenimleri paylas
- Strateji onerileri gelistir

Ogrenme alani: {learning_domain}
""",
        ),
        TemplateType.COORDINATOR: BaseTemplate(
            template_type=TemplateType.COORDINATOR,
            name="Base Coordinator",
            description="Diger agent'lari koordine eden agent",
            default_capabilities=[
                Capability(name="task_distribution", type=CapabilityType.COORDINATION, proficiency=0.8),
                Capability(name="conflict_resolution", type=CapabilityType.COORDINATION, proficiency=0.6),
            ],
            default_tools=["Read", "Glob"],
            default_model=AgentModel.OPUS,
            default_temperature=0.4,
            system_prompt_template="""
Sen bir koordinator agent'sin. Diger agent'larin calismasini yonet.

Gorevler:
- Gorevleri uygun agent'lara dagit
- Cakismalari coz
- Ilerlemeyi takip et
- Sonuclari birlestir

Koordinasyon senaryosu: {coordination_scenario}
""",
        ),
        TemplateType.SPECIALIST: BaseTemplate(
            template_type=TemplateType.SPECIALIST,
            name="Base Specialist",
            description="Uzman alan bilgisine sahip agent",
            default_capabilities=[
                Capability(name="domain_expertise", type=CapabilityType.CODING, proficiency=0.9),
            ],
            default_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            default_model=AgentModel.OPUS,
            default_temperature=0.5,
            system_prompt_template="""
Sen bir uzman agent'sin. Belirli bir alanda derin bilgi ve deneyime sahipsin.

Uzmanlik alani: {specialty_area}

Gorevler:
- Alan spesifik sorunlari coz
- En iyi pratikleri uygula
- Karmasik senaryolari ele al
- Bilgi paylas

Gorev: {task_description}
""",
        ),
        TemplateType.VALIDATOR: BaseTemplate(
            template_type=TemplateType.VALIDATOR,
            name="Base Validator",
            description="Dogrulama ve kalite kontrol agent'i",
            default_capabilities=[
                Capability(name="validation", type=CapabilityType.TESTING, proficiency=0.8),
                Capability(name="quality_assessment", type=CapabilityType.REVIEW, proficiency=0.7),
            ],
            default_tools=["Read", "Bash", "Glob", "Grep"],
            default_model=AgentModel.SONNET,
            default_temperature=0.2,
            system_prompt_template="""
Sen bir dogrulama agent'isin. Kod ve ciktiların kalitesini kontrol et.

Gorevler:
- Kod standartlarina uygunlugu kontrol et
- Test coverage'i degerlendir
- Guvenlik aciklarina bak
- Performans sorunlarini tespit et

Dogrulama hedefi: {validation_target}
""",
        ),
        TemplateType.OPTIMIZER: BaseTemplate(
            template_type=TemplateType.OPTIMIZER,
            name="Base Optimizer",
            description="Performans optimizasyonu agent'i",
            default_capabilities=[
                Capability(name="performance_analysis", type=CapabilityType.ANALYSIS, proficiency=0.8),
                Capability(name="optimization", type=CapabilityType.CODING, proficiency=0.7),
            ],
            default_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            default_model=AgentModel.SONNET,
            default_temperature=0.4,
            system_prompt_template="""
Sen bir optimizasyon agent'isin. Performansi artir ve kaynaklari verimli kullan.

Gorevler:
- Darbogazlari tespit et
- Optimizasyon stratejileri olustur
- Degisiklikleri uygula
- Sonuclari olc

Optimizasyon hedefi: {optimization_target}
""",
        ),
    }

    def __init__(self, base_path: str = ".claude"):
        self.base_path = Path(base_path)
        self.agents_dir = self.base_path / "agents"
        self.templates_file = self.base_path / "orchestration" / "templates.json"

        self._custom_templates: dict[str, BaseTemplate] = {}
        self._generation_count = 0

    async def initialize(self, registry: AgentRegistry) -> None:
        """Factory'yi baslat"""
        self.registry = registry
        await self._load_custom_templates()

    async def _load_custom_templates(self) -> None:
        """Ozel sablonlari yukle"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, template_data in data.items():
                        # Parse template from JSON
                        caps = [
                            Capability.from_dict(c)
                            for c in template_data.get("default_capabilities", [])
                        ]
                        template = BaseTemplate(
                            template_type=TemplateType(template_data["template_type"]),
                            name=template_data["name"],
                            description=template_data.get("description", ""),
                            default_capabilities=caps,
                            default_tools=template_data.get("default_tools", []),
                            default_model=AgentModel(template_data.get("default_model", "inherit")),
                            default_temperature=template_data.get("default_temperature", 0.7),
                            default_max_tokens=template_data.get("default_max_tokens", 4096),
                            system_prompt_template=template_data.get("system_prompt_template", ""),
                        )
                        self._custom_templates[name] = template
            except Exception as e:
                print(f"Warning: Could not load custom templates: {e}")

    async def _save_custom_templates(self) -> None:
        """Ozel sablonlari kaydet"""
        self.templates_file.parent.mkdir(parents=True, exist_ok=True)
        data = {name: t.to_dict() for name, t in self._custom_templates.items()}
        with open(self.templates_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_template(self, template_type: TemplateType) -> BaseTemplate:
        """Sablon getir"""
        return self.BASE_TEMPLATES.get(template_type)

    async def create_agent(
        self,
        name: str,
        template_type: TemplateType,
        capabilities: Optional[list[Capability]] = None,
        tools: Optional[list[str]] = None,
        model: Optional[AgentModel] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AgentDefinition:
        """
        Yeni agent olustur

        Args:
            name: Agent ismi
            template_type: Temel sablon tipi
            capabilities: Ek yetenekler
            tools: Ek araclar
            model: LLM model secimi
            system_prompt: Ozel system prompt

        Returns:
            Olusturulan AgentDefinition
        """
        template = self.get_template(template_type)
        if not template:
            raise ValueError(f"Template not found: {template_type}")

        self._generation_count += 1

        # Merge capabilities
        all_capabilities = template.default_capabilities.copy()
        if capabilities:
            all_capabilities.extend(capabilities)

        # Merge tools
        all_tools = template.default_tools.copy()
        if tools:
            all_tools = list(set(all_tools + tools))

        # Create genome
        genome = AgentGenome(
            agent_id=f"dynamic-{name}-{self._generation_count}",
            name=name,
            version="1.0.0",
            capabilities=all_capabilities,
            tools=all_tools,
            model=model or template.default_model,
            temperature=kwargs.get("temperature", template.default_temperature),
            max_tokens=kwargs.get("max_tokens", template.default_max_tokens),
            system_prompt=system_prompt or template.system_prompt_template,
            learning_params=LearningParameters(),
        )

        # Create agent definition
        agent_def = AgentDefinition(
            genome=genome,
            is_dynamic=True,
        )

        # Generate .md file
        await self._generate_agent_markdown(agent_def)

        # Register with registry
        if self.registry:
            await self.registry.register_agent(agent_def)

        return agent_def

    async def evolve_agent(
        self,
        agent_id: str,
        performance_data: Optional[PerformanceMetrics] = None
    ) -> AgentDefinition:
        """
        Mevcut agent'i performansa gore gelistir

        Args:
            agent_id: Gelistirilecek agent ID
            performance_data: Performans verileri

        Returns:
            Gelistirilmis yeni agent
        """
        if not self.registry:
            raise RuntimeError("Registry not initialized")

        original = await self.registry.get_agent(agent_id)
        if not original:
            raise ValueError(f"Agent not found: {agent_id}")

        # Update metrics if provided
        if performance_data:
            original.genome.metrics = performance_data
            original.genome.calculate_fitness()

        # Create evolved version
        evolved_genome = original.genome.mutate(mutation_rate=0.1)
        evolved_genome.name = f"{original.genome.name}-evolved"

        # Increase proficiency for successful capabilities
        if original.genome.metrics.success_rate > 0.7:
            for cap in evolved_genome.capabilities:
                cap.proficiency = min(1.0, cap.proficiency + 0.05)

        evolved_def = AgentDefinition(
            genome=evolved_genome,
            is_dynamic=True,
        )

        # Generate .md file
        await self._generate_agent_markdown(evolved_def)

        # Register
        await self.registry.register_agent(evolved_def)

        return evolved_def

    async def clone_and_mutate(
        self,
        source_agent_id: str,
        mutation_config: Optional[MutationConfig] = None
    ) -> AgentDefinition:
        """
        Agent'i klonla ve mutasyona ugrat

        Args:
            source_agent_id: Kaynak agent ID
            mutation_config: Mutasyon ayarlari

        Returns:
            Mutasyona ugramis yeni agent
        """
        if not self.registry:
            raise RuntimeError("Registry not initialized")

        source = await self.registry.get_agent(source_agent_id)
        if not source:
            raise ValueError(f"Agent not found: {source_agent_id}")

        config = mutation_config or MutationConfig()

        # Clone and mutate
        mutated_genome = source.genome.mutate(config.mutation_rate)
        mutated_genome.name = f"{source.genome.name}-mutant-{self._generation_count}"

        mutated_def = AgentDefinition(
            genome=mutated_genome,
            is_dynamic=True,
        )

        # Generate .md file
        await self._generate_agent_markdown(mutated_def)

        # Register
        await self.registry.register_agent(mutated_def)

        return mutated_def

    async def crossover_agents(
        self,
        parent1_id: str,
        parent2_id: str,
        name: Optional[str] = None
    ) -> AgentDefinition:
        """
        Iki agent'in ozelliklerini birlestir

        Args:
            parent1_id: Birinci parent agent ID
            parent2_id: Ikinci parent agent ID
            name: Yeni agent ismi

        Returns:
            Hybrid agent
        """
        if not self.registry:
            raise RuntimeError("Registry not initialized")

        parent1 = await self.registry.get_agent(parent1_id)
        parent2 = await self.registry.get_agent(parent2_id)

        if not parent1 or not parent2:
            raise ValueError("Parent agent(s) not found")

        # Crossover genomes
        child_genome = AgentGenome.crossover(parent1.genome, parent2.genome)
        child_genome.name = name or f"{parent1.genome.name[:4]}-{parent2.genome.name[:4]}-child"

        child_def = AgentDefinition(
            genome=child_genome,
            is_dynamic=True,
        )

        # Generate .md file
        await self._generate_agent_markdown(child_def)

        # Register
        await self.registry.register_agent(child_def)

        return child_def

    async def _generate_agent_markdown(self, agent_def: AgentDefinition) -> str:
        """Agent icin .md dosyasi olustur"""
        genome = agent_def.genome

        # Build markdown content
        tools_str = ", ".join(genome.tools)
        capabilities_str = "\n".join([
            f"- {cap.name} ({cap.type.value}): {cap.proficiency:.0%}"
            for cap in genome.capabilities
        ])

        md_content = f"""---
name: {genome.name}
description: Dynamically generated agent
tools: {tools_str}
model: {genome.model.value}
version: {genome.version}
generated: true
---

# {genome.name}

**Agent ID:** {genome.agent_id}
**Generation:** {genome.generation}
**Fitness Score:** {genome.fitness_score:.2f}

## Capabilities

{capabilities_str}

## System Prompt

{genome.system_prompt}

## Configuration

- **Temperature:** {genome.temperature}
- **Max Tokens:** {genome.max_tokens}
- **Learning Rate:** {genome.learning_params.learning_rate}
- **Exploration Rate:** {genome.learning_params.exploration_rate}

## Performance Metrics

- **Total Tasks:** {genome.metrics.total_tasks}
- **Success Rate:** {genome.metrics.success_rate:.0%}
- **Avg Response Time:** {genome.metrics.avg_response_time_ms:.0f}ms

---
*Generated by KIRO2 Agent Factory*
*Created: {genome.created_at.isoformat()}*
"""

        # Save to file
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.agents_dir / f"{genome.name}.md"
        file_path.write_text(md_content, encoding="utf-8")

        agent_def.file_path = str(file_path)
        return str(file_path)

    async def create_specialized_agent(
        self,
        specialty: str,
        domain_knowledge: str
    ) -> AgentDefinition:
        """
        Uzman agent olustur

        Args:
            specialty: Uzmanlik alani (backend, frontend, nlp, etc.)
            domain_knowledge: Alan bilgisi aciklamasi

        Returns:
            Uzman agent
        """
        specialty_mapping = {
            "backend": (CapabilityType.BACKEND, ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]),
            "frontend": (CapabilityType.FRONTEND, ["Read", "Write", "Edit", "Glob", "Grep"]),
            "testing": (CapabilityType.TESTING, ["Read", "Bash", "Glob", "Grep"]),
            "nlp": (CapabilityType.NLP, ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]),
            "devops": (CapabilityType.DEVOPS, ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]),
            "database": (CapabilityType.DATABASE, ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]),
            "content": (CapabilityType.CONTENT, ["Read", "Write", "Edit", "Glob", "Grep"]),
        }

        cap_type, tools = specialty_mapping.get(
            specialty.lower(),
            (CapabilityType.CODING, ["Read", "Write", "Edit", "Bash", "Glob", "Grep"])
        )

        capabilities = [
            Capability(
                name=f"{specialty}_expert",
                type=cap_type,
                proficiency=0.85,
                description=domain_knowledge,
            )
        ]

        system_prompt = f"""
Sen bir {specialty} uzmani agent'sin.

Alan Bilgisi:
{domain_knowledge}

KIRO2 Projesi Baglami:
- Turkiye Universite Giris Sinav Hazirlık Platformu
- YKS/TYT/AYT sinav hazirlik
- Turkce-first tasarim
- FastAPI + React 18 + PostgreSQL

Gorevler:
- {specialty} alaninda en iyi pratikleri uygula
- KIRO2 kod standartlarina uy
- Performans ve guvenlik oncelikli calis
- Kapsamli hata yakalama yap
"""

        return await self.create_agent(
            name=f"kiro2-{specialty}-specialist",
            template_type=TemplateType.SPECIALIST,
            capabilities=capabilities,
            tools=tools,
            model=AgentModel.OPUS,
            system_prompt=system_prompt,
        )

    def get_statistics(self) -> dict:
        """Factory istatistikleri"""
        return {
            "generation_count": self._generation_count,
            "base_templates": list(self.BASE_TEMPLATES.keys()),
            "custom_templates": list(self._custom_templates.keys()),
        }
