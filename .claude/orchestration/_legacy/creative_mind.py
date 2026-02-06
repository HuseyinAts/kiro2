"""
Creative Mind - Sistem Evolusyonu ve Yenilik

Sistemdeki eksiklikleri tespit eder, yeni agent tipleri tasarlar
ve sistem genelinde iyilestirmeler onerir.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from .agent_genome import AgentGenome, Capability, CapabilityType, AgentModel
from .agent_registry import AgentRegistry, AgentDefinition
from .agent_factory import AgentFactory, TemplateType
from .performance_monitor import PerformanceMonitor
from .evolution_engine import EvolutionEngine
from .collective_memory import CollectiveMemory, InsightType


class GapType(Enum):
    """Eksiklik tipi"""
    CAPABILITY_GAP = "capability_gap"        # Yetenek eksikligi
    COVERAGE_GAP = "coverage_gap"            # Kapsam eksikligi
    PERFORMANCE_GAP = "performance_gap"      # Performans eksikligi
    SPECIALIZATION_GAP = "specialization"    # Uzmanlik eksikligi
    COORDINATION_GAP = "coordination"        # Koordinasyon eksikligi


class ImprovementCategory(Enum):
    """Iyilestirme kategorisi"""
    AGENT_CREATION = "agent_creation"
    AGENT_EVOLUTION = "agent_evolution"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    ARCHITECTURE = "architecture"


@dataclass
class CapabilityGap:
    """Tespit edilen yetenek eksikligi"""
    gap_type: GapType
    capability: str
    severity: float  # 0.0 - 1.0
    description: str
    affected_tasks: list[str] = field(default_factory=list)
    suggested_solution: str = ""
    priority: int = 5  # 1-10

    def to_dict(self) -> dict:
        return {
            "gap_type": self.gap_type.value,
            "capability": self.capability,
            "severity": self.severity,
            "description": self.description,
            "affected_tasks": self.affected_tasks,
            "suggested_solution": self.suggested_solution,
            "priority": self.priority,
        }


@dataclass
class SystemImprovement:
    """Sistem iyilestirme onerisi"""
    category: ImprovementCategory
    title: str
    description: str
    expected_impact: float  # 0.0 - 1.0
    implementation_effort: str  # low, medium, high
    steps: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    priority: int = 5

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "expected_impact": self.expected_impact,
            "implementation_effort": self.implementation_effort,
            "steps": self.steps,
            "dependencies": self.dependencies,
            "priority": self.priority,
        }


@dataclass
class Innovation:
    """Yenilik onerisi"""
    innovation_id: str
    title: str
    description: str
    innovation_type: str
    potential_value: float  # 0.0 - 1.0
    risk_level: float  # 0.0 - 1.0
    resources_required: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "innovation_id": self.innovation_id,
            "title": self.title,
            "description": self.description,
            "innovation_type": self.innovation_type,
            "potential_value": self.potential_value,
            "risk_level": self.risk_level,
            "resources_required": self.resources_required,
            "created_at": self.created_at.isoformat(),
        }


class CreativeMind:
    """
    Creative Mind - Sistemin Yaratici Zihni

    Gorevler:
    1. Sistemdeki eksiklikleri tespit et
    2. Yeni agent tipleri tasarla
    3. Sistem iyilestirmeleri oner
    4. Yenilikleri degerlendir
    5. Evolusyon stratejileri gelistir
    """

    # KIRO2 platformu icin gerekli yetenekler
    REQUIRED_CAPABILITIES = {
        CapabilityType.BACKEND.value: {
            "description": "FastAPI, veritabani, API gelistirme",
            "priority": 10,
        },
        CapabilityType.FRONTEND.value: {
            "description": "React 18, TypeScript, UI/UX",
            "priority": 9,
        },
        CapabilityType.TESTING.value: {
            "description": "pytest, jest, test yazimi",
            "priority": 8,
        },
        CapabilityType.DEBUGGING.value: {
            "description": "Hata ayiklama, troubleshooting",
            "priority": 8,
        },
        CapabilityType.NLP.value: {
            "description": "Turkce NLP, soru analizi",
            "priority": 9,
        },
        CapabilityType.CONTENT.value: {
            "description": "YKS/TYT/AYT icerik yonetimi",
            "priority": 9,
        },
        CapabilityType.DEVOPS.value: {
            "description": "Docker, deployment, CI/CD",
            "priority": 7,
        },
        CapabilityType.DATABASE.value: {
            "description": "PostgreSQL, Redis, migration",
            "priority": 8,
        },
        CapabilityType.REVIEW.value: {
            "description": "Kod inceleme, kalite kontrol",
            "priority": 7,
        },
        CapabilityType.ANALYSIS.value: {
            "description": "Sistem analizi, performans",
            "priority": 6,
        },
    }

    def __init__(self, base_path: str = ".claude"):
        self.base_path = Path(base_path)
        self.innovations_file = self.base_path / "orchestration" / "innovations.json"

        self._innovations: list[Innovation] = []
        self._gap_history: list[CapabilityGap] = []

    async def initialize(
        self,
        registry: AgentRegistry,
        factory: AgentFactory,
        monitor: PerformanceMonitor,
        evolution: EvolutionEngine,
        memory: CollectiveMemory
    ) -> None:
        """Creative Mind'i baslat"""
        self.registry = registry
        self.factory = factory
        self.monitor = monitor
        self.evolution = evolution
        self.memory = memory
        await self._load_innovations()

    async def _load_innovations(self) -> None:
        """Yenilikleri yukle"""
        if self.innovations_file.exists():
            try:
                with open(self.innovations_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._innovations = [
                        Innovation(
                            innovation_id=i["innovation_id"],
                            title=i["title"],
                            description=i["description"],
                            innovation_type=i["innovation_type"],
                            potential_value=i["potential_value"],
                            risk_level=i["risk_level"],
                            resources_required=i.get("resources_required", {}),
                            created_at=datetime.fromisoformat(i["created_at"]),
                        )
                        for i in data.get("innovations", [])
                    ]
            except Exception as e:
                print(f"Warning: Could not load innovations: {e}")

    async def _save_innovations(self) -> None:
        """Yenilikleri kaydet"""
        self.innovations_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "innovations": [i.to_dict() for i in self._innovations],
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.innovations_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def analyze_gaps(self) -> list[CapabilityGap]:
        """
        Sistemdeki eksiklikleri tespit et

        Returns:
            Tespit edilen eksiklikler
        """
        gaps = []

        # Get current capability coverage
        agents = await self.registry.list_all_agents()
        current_capabilities = {}

        for agent in agents:
            for cap in agent.genome.capabilities:
                cap_key = cap.type.value
                if cap_key not in current_capabilities:
                    current_capabilities[cap_key] = []
                current_capabilities[cap_key].append({
                    "agent_id": agent.genome.agent_id,
                    "proficiency": cap.proficiency,
                })

        # Check for missing or weak capabilities
        for cap_type, info in self.REQUIRED_CAPABILITIES.items():
            coverage = current_capabilities.get(cap_type, [])

            if not coverage:
                # Complete gap
                gaps.append(CapabilityGap(
                    gap_type=GapType.CAPABILITY_GAP,
                    capability=cap_type,
                    severity=1.0,
                    description=f"No agent covers {cap_type}: {info['description']}",
                    suggested_solution=f"Create new {cap_type} specialist agent",
                    priority=info["priority"],
                ))
            else:
                # Check proficiency
                avg_proficiency = sum(c["proficiency"] for c in coverage) / len(coverage)
                if avg_proficiency < 0.5:
                    gaps.append(CapabilityGap(
                        gap_type=GapType.PERFORMANCE_GAP,
                        capability=cap_type,
                        severity=1.0 - avg_proficiency,
                        description=f"Low proficiency ({avg_proficiency:.0%}) for {cap_type}",
                        suggested_solution="Evolve existing agents or create specialist",
                        priority=info["priority"] - 2,
                    ))

                # Check coverage breadth
                if len(coverage) == 1:
                    gaps.append(CapabilityGap(
                        gap_type=GapType.COVERAGE_GAP,
                        capability=cap_type,
                        severity=0.5,
                        description=f"Single point of failure for {cap_type}",
                        suggested_solution="Create backup agent with same capability",
                        priority=info["priority"] - 3,
                    ))

        # Check for coordination gaps
        coordinator_count = sum(
            1 for a in agents
            if any(c.type == CapabilityType.COORDINATION for c in a.genome.capabilities)
        )
        if coordinator_count == 0:
            gaps.append(CapabilityGap(
                gap_type=GapType.COORDINATION_GAP,
                capability="coordination",
                severity=0.7,
                description="No coordinator agent for complex workflows",
                suggested_solution="Create coordinator agent",
                priority=6,
            ))

        # Sort by priority and severity
        gaps.sort(key=lambda g: (g.priority, g.severity), reverse=True)

        self._gap_history = gaps
        return gaps

    async def design_new_agent(self, gap: CapabilityGap) -> AgentGenome:
        """
        Eksikligi kapatan yeni agent tasarla

        Args:
            gap: Kapatilacak eksiklik

        Returns:
            Tasarlanan agent genome
        """
        # Determine template type
        template_mapping = {
            GapType.CAPABILITY_GAP: TemplateType.SPECIALIST,
            GapType.PERFORMANCE_GAP: TemplateType.OPTIMIZER,
            GapType.COVERAGE_GAP: TemplateType.WORKER,
            GapType.SPECIALIZATION_GAP: TemplateType.SPECIALIST,
            GapType.COORDINATION_GAP: TemplateType.COORDINATOR,
        }

        template_type = template_mapping.get(gap.gap_type, TemplateType.WORKER)

        # Design capabilities
        capabilities = [
            Capability(
                name=f"{gap.capability}_expert",
                type=CapabilityType(gap.capability) if gap.capability in [c.value for c in CapabilityType] else CapabilityType.CODING,
                proficiency=0.8,
                description=gap.description,
            )
        ]

        # Add complementary capabilities
        if gap.capability == CapabilityType.BACKEND.value:
            capabilities.append(Capability(
                name="database_knowledge",
                type=CapabilityType.DATABASE,
                proficiency=0.6,
            ))
        elif gap.capability == CapabilityType.FRONTEND.value:
            capabilities.append(Capability(
                name="accessibility",
                type=CapabilityType.FRONTEND,
                proficiency=0.6,
            ))
        elif gap.capability == CapabilityType.NLP.value:
            capabilities.append(Capability(
                name="turkish_language",
                type=CapabilityType.NLP,
                proficiency=0.8,
            ))

        # Choose model based on complexity
        model = AgentModel.OPUS if gap.priority >= 8 else AgentModel.SONNET

        # Design system prompt
        system_prompt = f"""
Sen bir KIRO2 {gap.capability} uzman agent'isin.

Uzmanlik Alani:
{gap.description}

Platform Baglami:
- KIRO2: Turkiye Universite Giris Sinav Hazirlık Platformu
- YKS/TYT/AYT sinav hazirlik
- Hedef: 100.000+ ogrenci
- Performans: <200ms API yanit suresi

Gorevler:
1. {gap.capability} alaninda en iyi pratikleri uygula
2. KIRO2 standartlarina uy
3. Turkce-first yaklas
4. Production-ready kod uret
5. Test ve dokumantasyon ekle

{gap.suggested_solution}
"""

        # Create agent through factory
        agent_def = await self.factory.create_agent(
            name=f"kiro2-{gap.capability}-auto",
            template_type=template_type,
            capabilities=capabilities,
            model=model,
            system_prompt=system_prompt,
        )

        return agent_def.genome

    async def propose_system_improvements(self) -> list[SystemImprovement]:
        """
        Sistem genelinde iyilestirmeler oner

        Returns:
            Iyilestirme onerileri
        """
        improvements = []

        # Analyze current state
        registry_stats = self.registry.get_statistics()
        gaps = await self.analyze_gaps()

        # Agent creation suggestions
        high_priority_gaps = [g for g in gaps if g.priority >= 8]
        if high_priority_gaps:
            improvements.append(SystemImprovement(
                category=ImprovementCategory.AGENT_CREATION,
                title="Kritik Yetenek Eksikliklerini Kapat",
                description=f"{len(high_priority_gaps)} kritik yetenek eksikligi tespit edildi",
                expected_impact=0.3,
                implementation_effort="medium",
                steps=[
                    f"Eksiklik: {g.capability} - {g.description}" for g in high_priority_gaps[:3]
                ] + ["Factory ile yeni agent olustur"],
                priority=9,
            ))

        # Evolution suggestions
        evolution_stats = self.evolution.get_evolution_statistics()
        if evolution_stats.get("stagnation_counter", 0) > 5:
            improvements.append(SystemImprovement(
                category=ImprovementCategory.AGENT_EVOLUTION,
                title="Evolusyon Stagnasyonu Coz",
                description="Agent evolusyonu durmus, yeni stratejiler gerekli",
                expected_impact=0.2,
                implementation_effort="medium",
                steps=[
                    "Mutation rate artir",
                    "Yeni genetic operators ekle",
                    "Population diversity artir",
                ],
                priority=7,
            ))

        # Health-based improvements
        healthy_ratio = registry_stats.get("health_distribution", {}).get("healthy", 0) / max(1, registry_stats.get("total_agents", 1))
        if healthy_ratio < 0.8:
            improvements.append(SystemImprovement(
                category=ImprovementCategory.RESOURCE_OPTIMIZATION,
                title="Agent Sagligini Iyilestir",
                description=f"Saglikli agent orani: {healthy_ratio:.0%}",
                expected_impact=0.25,
                implementation_effort="low",
                steps=[
                    "Unhealthy agent'lari analiz et",
                    "Timeout ve retry parametrelerini ayarla",
                    "Circuit breaker pattern uygula",
                ],
                priority=8,
            ))

        # Knowledge sharing
        memory_stats = self.memory.get_statistics()
        if memory_stats.get("total_insights", 0) < 50:
            improvements.append(SystemImprovement(
                category=ImprovementCategory.KNOWLEDGE_SHARING,
                title="Bilgi Havuzunu Zenginlestir",
                description="Collective memory yetersiz bilgi iceriyor",
                expected_impact=0.15,
                implementation_effort="low",
                steps=[
                    "Basarili stratejileri kaydet",
                    "Anti-pattern'leri dokumante et",
                    "Agent arasi bilgi paylasimini tetikle",
                ],
                priority=5,
            ))

        # Architecture improvements
        if registry_stats.get("total_agents", 0) > 20:
            improvements.append(SystemImprovement(
                category=ImprovementCategory.ARCHITECTURE,
                title="Agent Sayisini Optimize Et",
                description="Cok fazla agent, konsolidasyon gerekli",
                expected_impact=0.1,
                implementation_effort="high",
                steps=[
                    "Benzer agent'lari tespit et",
                    "Dusuk performansli agent'lari deprecate et",
                    "Hybrid agent'lar olustur",
                ],
                priority=4,
            ))

        # Sort by priority
        improvements.sort(key=lambda i: i.priority, reverse=True)

        return improvements

    async def evaluate_innovation(self, innovation: Innovation) -> dict:
        """
        Yenilik onerisi degerlendir

        Args:
            innovation: Degerlendirilecek yenilik

        Returns:
            Degerlendirme sonucu
        """
        # Calculate scores
        value_score = innovation.potential_value
        risk_score = innovation.risk_level

        # Adjusted score
        adjusted_score = value_score * (1 - risk_score * 0.5)

        # Resource feasibility
        resources = innovation.resources_required
        feasibility = 1.0

        if resources.get("agents_needed", 0) > 5:
            feasibility *= 0.8
        if resources.get("time_days", 0) > 30:
            feasibility *= 0.7
        if resources.get("complexity", "low") == "high":
            feasibility *= 0.6

        final_score = adjusted_score * feasibility

        # Recommendation
        if final_score >= 0.7:
            recommendation = "STRONGLY_RECOMMENDED"
        elif final_score >= 0.5:
            recommendation = "RECOMMENDED"
        elif final_score >= 0.3:
            recommendation = "CONSIDER"
        else:
            recommendation = "NOT_RECOMMENDED"

        return {
            "innovation_id": innovation.innovation_id,
            "value_score": value_score,
            "risk_score": risk_score,
            "feasibility": feasibility,
            "final_score": final_score,
            "recommendation": recommendation,
            "evaluated_at": datetime.now().isoformat(),
        }

    async def create_innovation(
        self,
        title: str,
        description: str,
        innovation_type: str,
        potential_value: float,
        risk_level: float,
        resources: Optional[dict] = None
    ) -> Innovation:
        """Yeni inovasyon olustur"""
        import hashlib

        innovation_id = hashlib.sha256(
            f"{title}-{datetime.now().isoformat()}".encode()
        ).hexdigest()[:10]

        innovation = Innovation(
            innovation_id=innovation_id,
            title=title,
            description=description,
            innovation_type=innovation_type,
            potential_value=potential_value,
            risk_level=risk_level,
            resources_required=resources or {},
        )

        self._innovations.append(innovation)
        await self._save_innovations()

        return innovation

    async def auto_improve_system(self) -> dict:
        """
        Sistemi otomatik iyilestir

        Returns:
            Yapilan iyilestirmeler
        """
        results = {
            "gaps_fixed": 0,
            "agents_created": 0,
            "agents_evolved": 0,
            "improvements_applied": 0,
        }

        # 1. Analyze gaps
        gaps = await self.analyze_gaps()

        # 2. Fix critical gaps
        for gap in gaps[:3]:  # Top 3 priority
            if gap.priority >= 8:
                try:
                    await self.design_new_agent(gap)
                    results["gaps_fixed"] += 1
                    results["agents_created"] += 1
                except Exception as e:
                    print(f"Warning: Could not create agent for {gap.capability}: {e}")

        # 3. Evolve weak agents
        evolution_targets = await self.evolution.suggest_evolution_targets()
        for agent_id in evolution_targets[:5]:  # Top 5
            try:
                await self.evolution.evolve_agent(agent_id, generations=3)
                results["agents_evolved"] += 1
            except Exception as e:
                print(f"Warning: Could not evolve {agent_id}: {e}")

        # 4. Apply improvements
        improvements = await self.propose_system_improvements()
        for imp in improvements:
            if imp.implementation_effort == "low" and imp.priority >= 7:
                # Auto-apply low effort improvements
                await self._apply_improvement(imp)
                results["improvements_applied"] += 1

        return results

    async def _apply_improvement(self, improvement: SystemImprovement) -> None:
        """Iyilestirmeyi uygula"""
        # Log to collective memory
        await self.memory.store_insight(
            agent_id="creative-mind",
            insight_type=InsightType.STRATEGY,
            title=improvement.title,
            content=improvement.description,
            tags=[improvement.category.value],
            context={"steps": improvement.steps},
        )

    def get_statistics(self) -> dict:
        """Creative Mind istatistikleri"""
        return {
            "total_innovations": len(self._innovations),
            "gap_history_size": len(self._gap_history),
            "recent_gaps": [g.to_dict() for g in self._gap_history[:5]],
        }
