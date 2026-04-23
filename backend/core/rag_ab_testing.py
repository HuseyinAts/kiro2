"""
A/B Testing Framework for RAG System
Compare different configurations and strategies
"""

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for A/B test experiment"""

    name: str
    description: str
    config: dict[str, Any]
    weight: float = 0.5  # Traffic allocation (0-1)


@dataclass
class SearchMetrics:
    """Metrics for a search operation"""

    query: str
    results_count: int
    latency_ms: float
    relevance_scores: list[float]
    top_1_score: float
    avg_score: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "results_count": self.results_count,
            "latency_ms": self.latency_ms,
            "relevance_scores": self.relevance_scores,
            "top_1_score": self.top_1_score,
            "avg_score": self.avg_score,
            "timestamp": self.timestamp,
        }


@dataclass
class ExperimentResults:
    """Results from an experiment"""

    experiment_name: str
    total_queries: int
    metrics: list[SearchMetrics]

    # Aggregated statistics
    avg_latency: float = 0.0
    p95_latency: float = 0.0
    avg_relevance: float = 0.0
    avg_top_1_score: float = 0.0

    def compute_statistics(self):
        """Compute aggregated statistics"""

        if not self.metrics:
            return

        latencies = [m.latency_ms for m in self.metrics]
        relevances = [m.avg_score for m in self.metrics]
        top_scores = [m.top_1_score for m in self.metrics]

        self.avg_latency = sum(latencies) / len(latencies)
        self.avg_relevance = sum(relevances) / len(relevances)
        self.avg_top_1_score = sum(top_scores) / len(top_scores)

        # P95 latency
        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        self.p95_latency = (
            sorted_latencies[p95_idx]
            if p95_idx < len(sorted_latencies)
            else sorted_latencies[-1]
        )

    def to_dict(self) -> dict:
        return {
            "experiment_name": self.experiment_name,
            "total_queries": self.total_queries,
            "avg_latency": self.avg_latency,
            "p95_latency": self.p95_latency,
            "avg_relevance": self.avg_relevance,
            "avg_top_1_score": self.avg_top_1_score,
            "sample_metrics": [m.to_dict() for m in self.metrics[:10]],
        }


class ABTestRunner:
    """
    A/B test runner for RAG system
    Compares different search strategies
    """

    def __init__(self):
        """Initialize A/B test runner"""

        self.experiments: dict[str, ExperimentConfig] = {}
        self.results: dict[str, ExperimentResults] = {}
        self._user_assignments: dict[str, str] = {}  # user_id -> experiment

    def add_experiment(
        self, name: str, description: str, config: dict[str, Any], weight: float = 0.5
    ):
        """
        Add experiment configuration

        Args:
            name: Experiment name
            description: Description
            config: Configuration dict
            weight: Traffic weight (0-1)
        """

        self.experiments[name] = ExperimentConfig(
            name=name, description=description, config=config, weight=weight
        )

        self.results[name] = ExperimentResults(
            experiment_name=name, total_queries=0, metrics=[]
        )

        logger.info(f"Added experiment: {name} (weight={weight})")

    def assign_experiment(self, user_id: str) -> str:
        """
        Assign user to experiment using consistent hashing

        Args:
            user_id: User identifier

        Returns:
            Experiment name
        """

        # Check if already assigned
        if user_id in self._user_assignments:
            return self._user_assignments[user_id]

        # Consistent hashing
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        threshold = user_hash / (2**128)

        # Allocate based on weights
        cumulative = 0.0
        experiment_names = list(self.experiments.keys())

        for exp_name in experiment_names:
            weight = self.experiments[exp_name].weight
            cumulative += weight

            if threshold < cumulative:
                self._user_assignments[user_id] = exp_name
                return exp_name

        # Fallback to first experiment
        fallback = experiment_names[0] if experiment_names else "default"
        self._user_assignments[user_id] = fallback
        return fallback

    async def run_search(
        self, user_id: str, query: str, search_fn: Callable, **kwargs
    ) -> tuple[list[dict], SearchMetrics]:
        """
        Run search with assigned experiment

        Args:
            user_id: User ID for consistent assignment
            query: Search query
            search_fn: Search function to call
            **kwargs: Additional search parameters

        Returns:
            (results, metrics)
        """

        # Assign experiment
        experiment_name = self.assign_experiment(user_id)
        config = self.experiments[experiment_name].config

        # Merge config with kwargs
        search_params = {**config, **kwargs}

        # Run search with timing
        start_time = time.time()

        try:
            results = await search_fn(query, **search_params)
            latency = (time.time() - start_time) * 1000  # ms

            # Extract scores
            scores = [r.get("score", 0.0) for r in results]

            # Create metrics
            metrics = SearchMetrics(
                query=query,
                results_count=len(results),
                latency_ms=latency,
                relevance_scores=scores,
                top_1_score=scores[0] if scores else 0.0,
                avg_score=sum(scores) / len(scores) if scores else 0.0,
            )

            # Record metrics
            self.results[experiment_name].metrics.append(metrics)
            self.results[experiment_name].total_queries += 1

            return results, metrics

        except Exception as e:
            logger.error(f"Search error in experiment {experiment_name}: {e}")
            raise

    def get_results(
        self, experiment_name: str | None = None
    ) -> dict[str, ExperimentResults]:
        """
        Get experiment results

        Args:
            experiment_name: Specific experiment (or all if None)

        Returns:
            Dictionary of results
        """

        # Compute statistics
        for result in self.results.values():
            result.compute_statistics()

        if experiment_name:
            return {experiment_name: self.results[experiment_name]}

        return self.results

    def compare_experiments(self) -> dict[str, Any]:
        """
        Compare all experiments

        Returns:
            Comparison report
        """

        # Compute statistics
        for result in self.results.values():
            result.compute_statistics()

        # Build comparison
        comparison = {
            "experiments": {},
            "winner": None,
            "winner_metric": "avg_relevance",
        }

        best_relevance = 0.0
        best_experiment = None

        for name, result in self.results.items():
            comparison["experiments"][name] = {
                "total_queries": result.total_queries,
                "avg_latency_ms": round(result.avg_latency, 2),
                "p95_latency_ms": round(result.p95_latency, 2),
                "avg_relevance": round(result.avg_relevance, 4),
                "avg_top_1_score": round(result.avg_top_1_score, 4),
            }

            # Track best
            if result.avg_relevance > best_relevance:
                best_relevance = result.avg_relevance
                best_experiment = name

        comparison["winner"] = best_experiment

        # Calculate relative improvements
        if best_experiment:
            baseline_name = (
                [n for n in self.results.keys() if n != best_experiment][0]
                if len(self.results) > 1
                else None
            )

            if baseline_name:
                baseline = self.results[baseline_name]
                winner = self.results[best_experiment]

                relevance_improvement = (
                    (winner.avg_relevance - baseline.avg_relevance)
                    / baseline.avg_relevance
                    * 100
                    if baseline.avg_relevance > 0
                    else 0
                )

                latency_change = (
                    (winner.avg_latency - baseline.avg_latency)
                    / baseline.avg_latency
                    * 100
                    if baseline.avg_latency > 0
                    else 0
                )

                comparison["improvements"] = {
                    "relevance_improvement_pct": round(relevance_improvement, 2),
                    "latency_change_pct": round(latency_change, 2),
                }

        return comparison

    def export_results(self, filepath: str):
        """Export results to JSON file"""

        # Compute statistics
        for result in self.results.values():
            result.compute_statistics()

        export_data = {
            "experiments": {
                name: config.__dict__ for name, config in self.experiments.items()
            },
            "results": {
                name: result.to_dict() for name, result in self.results.items()
            },
            "comparison": self.compare_experiments(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported results to {filepath}")


class RAGStrategyComparator:
    """
    Compare different RAG strategies:
    - Standard search
    - Hybrid search
    - Multi-query search
    - Reranked search
    """

    def __init__(self, rag_service):
        """
        Initialize comparator

        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service
        self.ab_runner = ABTestRunner()

        self._setup_experiments()

    def _setup_experiments(self):
        """Setup default experiments"""

        # Baseline: Standard search
        self.ab_runner.add_experiment(
            name="baseline",
            description="Standard semantic search",
            config={"method": "standard", "k": 5},
            weight=0.25,
        )

        # Hybrid search
        self.ab_runner.add_experiment(
            name="hybrid",
            description="Hybrid semantic + keyword search",
            config={"method": "hybrid", "k": 5, "alpha": 0.5},
            weight=0.25,
        )

        # Multi-query search
        self.ab_runner.add_experiment(
            name="multi_query",
            description="Search with query expansion",
            config={"method": "multi_query", "k": 5, "num_expansions": 2},
            weight=0.25,
        )

        # Hybrid + multi-query
        self.ab_runner.add_experiment(
            name="hybrid_multi",
            description="Hybrid with query expansion",
            config={
                "method": "hybrid_multi",
                "k": 5,
                "alpha": 0.5,
                "num_expansions": 2,
            },
            weight=0.25,
        )

    async def run_comparison(
        self, test_queries: list[str], num_iterations: int = 10
    ) -> dict[str, Any]:
        """
        Run comprehensive comparison

        Args:
            test_queries: List of test queries
            num_iterations: Number of iterations per query

        Returns:
            Comparison results
        """

        logger.info(
            f"Running comparison with {len(test_queries)} queries, {num_iterations} iterations each"
        )

        for iteration in range(num_iterations):
            for query in test_queries:
                # Simulate different users
                user_id = f"user_{iteration}_{hash(query)}"

                # Run search with assigned experiment
                await self.ab_runner.run_search(
                    user_id=user_id, query=query, search_fn=self._search_dispatcher
                )

        # Get comparison
        comparison = self.ab_runner.compare_experiments()

        logger.info(f"Comparison complete. Winner: {comparison['winner']}")

        return comparison

    async def _search_dispatcher(
        self, query: str, method: str = "standard", **kwargs
    ) -> list[dict]:
        """Dispatch search to appropriate method"""

        if method == "standard":
            return await self.rag_service.search(query, **kwargs)

        if method == "hybrid":
            return await self.rag_service.hybrid_search(query, **kwargs)

        if method == "multi_query":
            return await self.rag_service.multi_query_search(query, **kwargs)

        if method == "hybrid_multi":
            # First multi-query, then hybrid
            results = await self.rag_service.multi_query_search(
                query, k=kwargs.get("k", 5) * 2
            )
            # Apply hybrid to expanded results
            return results[: kwargs.get("k", 5)]

        raise ValueError(f"Unknown method: {method}")


# Example usage
"""
from core.rag_ab_testing import RAGStrategyComparator
from core.rag_service import rag_service

# Create comparator
comparator = RAGStrategyComparator(rag_service)

# Test queries
test_queries = [
    "Pythagoras teoremi nedir?",
    "İkinci dereceden denklem nasıl çözülür?",
    "Fotosentez nedir?",
    "Osmanlı İmparatorluğu ne zaman kuruldu?"
]

# Run comparison
results = await comparator.run_comparison(
    test_queries=test_queries,
    num_iterations=20
)

# Print results
print(f"Winner: {results['winner']}")
print(f"Relevance improvement: {results['improvements']['relevance_improvement_pct']}%")

# Export detailed results
comparator.ab_runner.export_results("rag_ab_test_results.json")
"""
