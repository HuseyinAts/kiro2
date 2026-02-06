"""
Evolution Engine - Genetik Algoritma ile Agent Evoluasyonu

Agent'lari performansa gore evoluasyona ugratir, en iyileri secip cogaltir.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from .agent_genome import (
    AgentGenome,
    AgentModel,
    Capability,
    CapabilityType,
    LearningParameters,
    PerformanceMetrics,
)
from .performance_monitor import PerformanceMonitor


class SelectionStrategy(Enum):
    """Parent secim stratejisi"""
    TOURNAMENT = "tournament"       # En iyiler arasinda turnuva
    ROULETTE = "roulette"           # Fitness oranli secim
    ELITE = "elite"                 # En iyi N tane
    DIVERSE = "diverse"             # Cesitlilik oncelikli


@dataclass
class EvolutionConfig:
    """Evolusyon konfigurasyonu"""
    population_size: int = 10
    generation_limit: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_count: int = 2
    selection_strategy: SelectionStrategy = SelectionStrategy.TOURNAMENT
    tournament_size: int = 3
    min_fitness_threshold: float = 0.3
    diversity_weight: float = 0.2


@dataclass
class GenerationStats:
    """Jenerasyon istatistikleri"""
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    diversity_score: float
    timestamp: datetime = field(default_factory=datetime.now)


class EvolutionEngine:
    """
    Genetik Algoritma ile Agent Evoluasyonu

    Gorevler:
    - Parent secimi (tournament, roulette, elite)
    - Crossover (yetenek ve parametre birlestirme)
    - Mutasyon (rastgele degisiklikler)
    - Jenerasyon yonetimi
    - Fitness takibi
    """

    def __init__(
        self,
        performance_monitor: Optional[PerformanceMonitor] = None,
        config: Optional[EvolutionConfig] = None
    ):
        self.performance_monitor = performance_monitor
        self.config = config or EvolutionConfig()

        self._population: list[AgentGenome] = []
        self._generation = 0
        self._history: list[GenerationStats] = []

    async def initialize(
        self,
        initial_population: list[AgentGenome]
    ) -> None:
        """
        Baslangic populasyonu ile initialize et

        Args:
            initial_population: Baslangic genome listesi
        """
        self._population = initial_population.copy()
        self._generation = 0

    async def select_parents(
        self,
        population: list[AgentGenome],
        fitness_scores: dict[str, float]
    ) -> tuple[AgentGenome, AgentGenome]:
        """
        Evoluasyon icin parent sec

        Args:
            population: Mevcut populasyon
            fitness_scores: Fitness skorlari

        Returns:
            (parent1, parent2) tuple
        """
        strategy = self.config.selection_strategy

        if strategy == SelectionStrategy.TOURNAMENT:
            parent1 = await self._tournament_select(population, fitness_scores)
            parent2 = await self._tournament_select(population, fitness_scores)
        elif strategy == SelectionStrategy.ROULETTE:
            parent1 = await self._roulette_select(population, fitness_scores)
            parent2 = await self._roulette_select(population, fitness_scores)
        elif strategy == SelectionStrategy.ELITE:
            parents = await self._elite_select(population, fitness_scores, 2)
            parent1, parent2 = parents[0], parents[1] if len(parents) > 1 else parents[0]
        else:  # DIVERSE
            parent1 = await self._diverse_select(population, fitness_scores)
            parent2 = await self._diverse_select(population, fitness_scores, exclude=parent1)

        return parent1, parent2

    async def _tournament_select(
        self,
        population: list[AgentGenome],
        fitness_scores: dict[str, float]
    ) -> AgentGenome:
        """Tournament secimi"""
        size = min(self.config.tournament_size, len(population))
        tournament = random.sample(population, size)

        winner = max(
            tournament,
            key=lambda g: fitness_scores.get(g.agent_id, 0)
        )
        return winner

    async def _roulette_select(
        self,
        population: list[AgentGenome],
        fitness_scores: dict[str, float]
    ) -> AgentGenome:
        """Roulette wheel secimi"""
        total_fitness = sum(fitness_scores.get(g.agent_id, 0.01) for g in population)
        if total_fitness == 0:
            return random.choice(population)

        pick = random.uniform(0, total_fitness)
        current = 0

        for genome in population:
            current += fitness_scores.get(genome.agent_id, 0.01)
            if current >= pick:
                return genome

        return population[-1]

    async def _elite_select(
        self,
        population: list[AgentGenome],
        fitness_scores: dict[str, float],
        count: int
    ) -> list[AgentGenome]:
        """En iyi N tanesini sec"""
        sorted_pop = sorted(
            population,
            key=lambda g: fitness_scores.get(g.agent_id, 0),
            reverse=True
        )
        return sorted_pop[:count]

    async def _diverse_select(
        self,
        population: list[AgentGenome],
        fitness_scores: dict[str, float],
        exclude: Optional[AgentGenome] = None
    ) -> AgentGenome:
        """Cesitlilik oncelikli secim"""
        candidates = [g for g in population if g != exclude]
        if not candidates:
            return population[0]

        # Calculate diversity score for each
        diversity_scores = []
        for genome in candidates:
            # Fitness component
            fitness = fitness_scores.get(genome.agent_id, 0)

            # Diversity: number of unique capability types
            cap_types = set(c.type for c in genome.capabilities)
            diversity = len(cap_types) / len(CapabilityType)

            # Combined score
            score = (
                fitness * (1 - self.config.diversity_weight) +
                diversity * self.config.diversity_weight
            )
            diversity_scores.append((genome, score))

        # Select based on combined score with randomness
        diversity_scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates = diversity_scores[:max(3, len(diversity_scores) // 2)]
        return random.choice(top_candidates)[0]

    async def crossover(
        self,
        parent1: AgentGenome,
        parent2: AgentGenome
    ) -> AgentGenome:
        """
        Iki genome'u birlestir

        Args:
            parent1: Birinci parent
            parent2: Ikinci parent

        Returns:
            Yeni child genome
        """
        # Use built-in crossover
        child = AgentGenome.crossover(parent1, parent2)

        # Additional refinements
        # Average temperature
        child.temperature = (parent1.temperature + parent2.temperature) / 2

        # Combine learning parameters
        child.learning_params = LearningParameters(
            learning_rate=(parent1.learning_params.learning_rate +
                           parent2.learning_params.learning_rate) / 2,
            exploration_rate=(parent1.learning_params.exploration_rate +
                              parent2.learning_params.exploration_rate) / 2,
            memory_size=max(
                parent1.learning_params.memory_size,
                parent2.learning_params.memory_size
            ),
        )

        return child

    async def mutate(
        self,
        genome: AgentGenome,
        mutation_rate: Optional[float] = None
    ) -> AgentGenome:
        """
        Genome'a mutasyon uygula

        Args:
            genome: Mutasyona ugratilacak genome
            mutation_rate: Mutasyon orani

        Returns:
            Mutasyona ugramis genome
        """
        rate = mutation_rate or self.config.mutation_rate

        # Use built-in mutation
        mutated = genome.mutate(rate)

        # Additional mutations
        if random.random() < rate:
            # Mutate temperature
            mutated.temperature = max(0.1, min(1.0,
                mutated.temperature + random.uniform(-0.1, 0.1)
            ))

        if random.random() < rate:
            # Mutate max tokens
            mutated.max_tokens = max(1024, min(8192,
                mutated.max_tokens + random.randint(-512, 512)
            ))

        if random.random() < rate:
            # Mutate model (rarely)
            models = list(AgentModel)
            mutated.model = random.choice(models)

        if random.random() < rate * 0.5:
            # Add random tool
            all_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"]
            new_tool = random.choice(all_tools)
            if new_tool not in mutated.tools:
                mutated.tools.append(new_tool)

        return mutated

    async def evolve_generation(
        self,
        population: list[AgentGenome]
    ) -> list[AgentGenome]:
        """
        Bir jenerasyon evoluasyonu yap

        Args:
            population: Mevcut populasyon

        Returns:
            Yeni jenerasyon
        """
        # Get fitness scores
        fitness_scores = {}
        for genome in population:
            if self.performance_monitor:
                fitness_scores[genome.agent_id] = await self.performance_monitor.calculate_fitness(
                    genome.agent_id
                )
            else:
                fitness_scores[genome.agent_id] = genome.fitness_score

        # Record stats
        stats = await self._calculate_generation_stats(population, fitness_scores)
        self._history.append(stats)

        new_population = []

        # Elite selection - keep the best unchanged
        elites = await self._elite_select(
            population, fitness_scores, self.config.elite_count
        )
        for elite in elites:
            new_population.append(elite.clone())

        # Fill rest with crossover and mutation
        while len(new_population) < self.config.population_size:
            # Select parents
            parent1, parent2 = await self.select_parents(population, fitness_scores)

            # Crossover
            if random.random() < self.config.crossover_rate:
                child = await self.crossover(parent1, parent2)
            else:
                child = random.choice([parent1, parent2]).clone()

            # Mutate
            child = await self.mutate(child)

            # Update generation info
            child.generation = self._generation + 1

            new_population.append(child)

        self._generation += 1
        self._population = new_population

        return new_population

    async def _calculate_generation_stats(
        self,
        population: list[AgentGenome],
        fitness_scores: dict[str, float]
    ) -> GenerationStats:
        """Jenerasyon istatistiklerini hesapla"""
        scores = [fitness_scores.get(g.agent_id, 0) for g in population]

        # Diversity: unique capability combinations
        cap_sets = [
            frozenset((c.name, c.type) for c in g.capabilities)
            for g in population
        ]
        diversity = len(set(cap_sets)) / len(population) if population else 0

        return GenerationStats(
            generation=self._generation,
            best_fitness=max(scores) if scores else 0,
            avg_fitness=sum(scores) / len(scores) if scores else 0,
            worst_fitness=min(scores) if scores else 0,
            diversity_score=diversity,
        )

    async def run_evolution(
        self,
        generations: Optional[int] = None,
        target_fitness: Optional[float] = None
    ) -> list[AgentGenome]:
        """
        Tam evolusyon dongusu calistir

        Args:
            generations: Max jenerasyon sayisi
            target_fitness: Hedef fitness (erken durdurma)

        Returns:
            Final populasyon
        """
        max_gens = generations or self.config.generation_limit

        for _ in range(max_gens):
            self._population = await self.evolve_generation(self._population)

            # Check early stopping
            if target_fitness and self._history:
                if self._history[-1].best_fitness >= target_fitness:
                    break

            # Check stagnation
            if len(self._history) > 10:
                recent = self._history[-10:]
                if all(abs(r.best_fitness - recent[0].best_fitness) < 0.01 for r in recent):
                    # Inject diversity
                    await self._inject_diversity()

        return self._population

    async def _inject_diversity(self) -> None:
        """Populasyona cesitlilik ekle"""
        # Replace worst performers with random mutations of best
        if not self._population:
            return

        fitness_scores = {g.agent_id: g.fitness_score for g in self._population}
        sorted_pop = sorted(
            self._population,
            key=lambda g: fitness_scores.get(g.agent_id, 0),
            reverse=True
        )

        # Take best and create highly mutated versions
        best = sorted_pop[0]
        num_to_replace = len(sorted_pop) // 4

        for i in range(num_to_replace):
            mutated = await self.mutate(best.clone(), mutation_rate=0.3)
            if len(sorted_pop) - 1 - i >= 0:
                sorted_pop[-(i + 1)] = mutated

        self._population = sorted_pop

    async def get_best_genome(self) -> Optional[AgentGenome]:
        """En iyi genome'u getir"""
        if not self._population:
            return None

        fitness_scores = {g.agent_id: g.fitness_score for g in self._population}
        return max(
            self._population,
            key=lambda g: fitness_scores.get(g.agent_id, 0)
        )

    async def get_evolution_report(self) -> str:
        """Evolusyon raporu olustur"""
        if not self._history:
            return "No evolution history available."

        report = f"""# Evolution Report

## Summary
- Total Generations: {self._generation}
- Population Size: {len(self._population)}
- Best Fitness Achieved: {max(s.best_fitness for s in self._history):.3f}

## Generation History

| Gen | Best | Avg | Worst | Diversity |
|-----|------|-----|-------|-----------|
"""
        for stats in self._history[-20:]:  # Last 20 generations
            report += f"| {stats.generation} | {stats.best_fitness:.3f} | "
            report += f"{stats.avg_fitness:.3f} | {stats.worst_fitness:.3f} | "
            report += f"{stats.diversity_score:.2f} |\n"

        # Best genome details
        best = await self.get_best_genome()
        if best:
            report += f"""
## Best Genome

- **ID:** {best.agent_id}
- **Name:** {best.name}
- **Generation:** {best.generation}
- **Fitness:** {best.fitness_score:.3f}
- **Capabilities:** {len(best.capabilities)}
- **Tools:** {', '.join(best.tools)}
"""

        return report

    def get_statistics(self) -> dict:
        """Istatistikleri getir"""
        return {
            "generation": self._generation,
            "population_size": len(self._population),
            "history_length": len(self._history),
            "config": {
                "population_size": self.config.population_size,
                "mutation_rate": self.config.mutation_rate,
                "crossover_rate": self.config.crossover_rate,
                "selection_strategy": self.config.selection_strategy.value,
            },
        }
