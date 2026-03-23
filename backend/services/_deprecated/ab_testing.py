"""
A/B Testing System for Multi-LLM OSYM Question Generation
Compares optimized vs non-optimized performance

Author: KIRO AI Team
Date: 2025-10-19
"""

import random
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict


class ModelVersion(Enum):
    """Model version variants"""

    BASE = "base"  # No optimization
    OPTIMIZED_PROMPT = "optimized_prompt"  # Prompt optimization only
    OPTIMIZED_VOCAB = "optimized_vocab"  # Extended vocabulary (Qwen only)
    OPTIMIZED_FULL = "optimized_full"  # Both optimizations


@dataclass
class ABTestResult:
    """A/B test result"""

    test_id: str
    timestamp: str
    user_id: Optional[str]
    version: str
    provider: str

    # Performance metrics
    tokens_used: int
    latency_ms: float
    cost_usd: float

    # Quality metrics
    quality_score: float
    irt_difficulty: float
    bloom_level: int

    # Question metadata
    topic: str
    exam_type: str
    metadata: Dict[str, Any]


class ABTestManager:
    """
    A/B Testing Manager

    Manages:
    - User assignment to test groups
    - Test result logging
    - Statistical analysis
    - Performance comparison
    """

    def __init__(
        self,
        log_path: str = "logs/ab_test_results.jsonl",
        optimized_percentage: int = 50,
    ):
        """
        Initialize A/B test manager

        Args:
            log_path: Path to log file
            optimized_percentage: Percentage of traffic to optimized version (0-100)
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(exist_ok=True, parents=True)
        self.optimized_percentage = optimized_percentage

    def assign_version(
        self, user_id: Optional[str] = None, provider: str = "openai"
    ) -> ModelVersion:
        """
        Assign model version to user

        Args:
            user_id: User ID (None for random assignment)
            provider: LLM provider name

        Returns:
            Assigned model version
        """
        if user_id:
            # Deterministic assignment based on user ID
            hash_value = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
            percentile = hash_value % 100

            if percentile < self.optimized_percentage:
                # Assign optimized version
                if provider == "qwen":
                    # Qwen can use full optimization (vocab + prompt)
                    return ModelVersion.OPTIMIZED_FULL
                else:
                    # OpenAI/Claude only use prompt optimization
                    return ModelVersion.OPTIMIZED_PROMPT
            else:
                return ModelVersion.BASE
        else:
            # Random assignment
            if random.random() < (self.optimized_percentage / 100):
                if provider == "qwen":
                    return ModelVersion.OPTIMIZED_FULL
                else:
                    return ModelVersion.OPTIMIZED_PROMPT
            else:
                return ModelVersion.BASE

    def log_result(
        self,
        version: ModelVersion,
        provider: str,
        tokens_used: int,
        latency_ms: float,
        cost_usd: float,
        quality_score: float,
        irt_difficulty: float,
        bloom_level: int,
        topic: str,
        exam_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ABTestResult:
        """
        Log A/B test result

        Args:
            version: Model version used
            provider: LLM provider
            tokens_used: Total tokens used
            latency_ms: Latency in milliseconds
            cost_usd: Cost in USD
            quality_score: Quality score (0-100)
            irt_difficulty: IRT difficulty parameter
            bloom_level: Bloom taxonomy level
            topic: Question topic
            exam_type: Exam type (TYT/AYT/YDT)
            user_id: User ID (optional)
            metadata: Additional metadata

        Returns:
            ABTestResult object
        """
        test_id = hashlib.md5(
            f"{datetime.now().isoformat()}{user_id}{provider}".encode()
        ).hexdigest()[:12]

        result = ABTestResult(
            test_id=test_id,
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            version=version.value,
            provider=provider,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            quality_score=quality_score,
            irt_difficulty=irt_difficulty,
            bloom_level=bloom_level,
            topic=topic,
            exam_type=exam_type,
            metadata=metadata or {},
        )

        # Log to file
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")

        return result

    def analyze_results(
        self, provider: Optional[str] = None, days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze A/B test results

        Args:
            provider: Filter by provider (optional)
            days: Number of days to analyze

        Returns:
            Analysis results
        """
        if not self.log_path.exists():
            return self._empty_analysis()

        # Load results
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        results_by_version = {}

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    result = json.loads(line.strip())

                    # Apply filters
                    result_date = datetime.fromisoformat(result["timestamp"])
                    if result_date < cutoff_date:
                        continue

                    if provider and result["provider"] != provider:
                        continue

                    # Group by version
                    version = result["version"]
                    if version not in results_by_version:
                        results_by_version[version] = []

                    results_by_version[version].append(result)

                except Exception:
                    continue

        if not results_by_version:
            return self._empty_analysis()

        # Calculate statistics for each version
        import statistics

        analysis = {}

        for version, results in results_by_version.items():
            n = len(results)

            tokens = [r["tokens_used"] for r in results]
            latencies = [r["latency_ms"] for r in results]
            costs = [r["cost_usd"] for r in results]
            qualities = [r["quality_score"] for r in results]

            analysis[version] = {
                "sample_size": n,
                "tokens": {
                    "mean": statistics.mean(tokens),
                    "median": statistics.median(tokens),
                    "stdev": statistics.stdev(tokens) if n > 1 else 0,
                },
                "latency_ms": {
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "stdev": statistics.stdev(latencies) if n > 1 else 0,
                },
                "cost_usd": {
                    "mean": statistics.mean(costs),
                    "median": statistics.median(costs),
                    "total": sum(costs),
                },
                "quality_score": {
                    "mean": statistics.mean(qualities),
                    "median": statistics.median(qualities),
                    "stdev": statistics.stdev(qualities) if n > 1 else 0,
                },
            }

        # Calculate improvement percentages
        if "base" in analysis:
            base_stats = analysis["base"]

            for version in analysis:
                if version == "base":
                    continue

                version_stats = analysis[version]

                # Token improvement
                token_improvement = (
                    (base_stats["tokens"]["mean"] - version_stats["tokens"]["mean"])
                    / base_stats["tokens"]["mean"]
                    * 100
                )

                # Cost improvement
                cost_improvement = (
                    (base_stats["cost_usd"]["mean"] - version_stats["cost_usd"]["mean"])
                    / base_stats["cost_usd"]["mean"]
                    * 100
                )

                # Quality change
                quality_change = (
                    version_stats["quality_score"]["mean"]
                    - base_stats["quality_score"]["mean"]
                )

                analysis[version]["improvements"] = {
                    "token_savings_percentage": round(token_improvement, 2),
                    "cost_savings_percentage": round(cost_improvement, 2),
                    "quality_score_change": round(quality_change, 2),
                }

        return {
            "analysis_period_days": days,
            "provider_filter": provider,
            "versions": analysis,
        }

    def generate_report(self, provider: Optional[str] = None, days: int = 7) -> str:
        """
        Generate human-readable report

        Args:
            provider: Filter by provider
            days: Number of days to analyze

        Returns:
            Formatted report
        """
        analysis = self.analyze_results(provider=provider, days=days)

        if not analysis.get("versions"):
            return "No A/B test data available"

        report = f"""
A/B TESTING REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {days} days
Provider: {provider or 'All'}

=== RESULTS BY VERSION ===
"""

        for version, stats in analysis["versions"].items():
            report += f"\n{version.upper()} (n={stats['sample_size']})\n"
            report += f"  Tokens: {stats['tokens']['mean']:.0f} ± {stats['tokens']['stdev']:.0f}\n"
            report += f"  Latency: {stats['latency_ms']['mean']:.0f}ms ± {stats['latency_ms']['stdev']:.0f}ms\n"
            report += f"  Cost: ${stats['cost_usd']['mean']:.6f}\n"
            report += f"  Quality: {stats['quality_score']['mean']:.1f} ± {stats['quality_score']['stdev']:.1f}\n"

            if "improvements" in stats:
                imp = stats["improvements"]
                report += "\n  IMPROVEMENTS vs BASE:\n"
                report += f"    Token Savings: {imp['token_savings_percentage']:.1f}%\n"
                report += f"    Cost Savings: {imp['cost_savings_percentage']:.1f}%\n"
                report += f"    Quality Change: {imp['quality_score_change']:+.1f}\n"

        # Winner determination
        if "base" in analysis["versions"] and len(analysis["versions"]) > 1:
            report += "\n=== RECOMMENDATION ===\n"

            optimized_versions = [v for v in analysis["versions"] if v != "base"]

            if optimized_versions:
                best_version = max(
                    optimized_versions,
                    key=lambda v: analysis["versions"][v]
                    .get("improvements", {})
                    .get("cost_savings_percentage", 0),
                )

                best_stats = analysis["versions"][best_version]
                improvements = best_stats.get("improvements", {})

                report += f"\nBest performing version: {best_version.upper()}\n"
                report += f"  Token savings: {improvements.get('token_savings_percentage', 0):.1f}%\n"
                report += f"  Cost savings: {improvements.get('cost_savings_percentage', 0):.1f}%\n"
                report += f"  Quality change: {improvements.get('quality_score_change', 0):+.1f}\n"

                if improvements.get("quality_score_change", 0) >= -2:
                    report += (
                        "\n✓ RECOMMENDED: Deploy optimized version to 100% of traffic\n"
                    )
                else:
                    report += "\n⚠ WARNING: Quality decreased. Review before full deployment.\n"

        return report

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {"analysis_period_days": 0, "provider_filter": None, "versions": {}}


# Singleton instance
_ab_test_manager = None


def get_ab_test_manager() -> ABTestManager:
    """Get global AB test manager instance"""
    global _ab_test_manager
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager()
    return _ab_test_manager


# Example usage
if __name__ == "__main__":
    import sys
    import io

    # Fix UTF-8 encoding for Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    manager = ABTestManager(optimized_percentage=50)

    # Simulate some test results
    for i in range(100):
        user_id = f"user_{i % 50}"  # 50 unique users
        version = manager.assign_version(user_id, provider="openai")

        # Simulate metrics
        if version == ModelVersion.BASE:
            tokens = 100
            cost = 0.001
            quality = 75
        else:
            tokens = 95  # 5% savings
            cost = 0.00095
            quality = 76  # Slight quality improvement

        manager.log_result(
            version=version,
            provider="openai",
            tokens_used=tokens,
            latency_ms=500,
            cost_usd=cost,
            quality_score=quality,
            irt_difficulty=0.5,
            bloom_level=3,
            topic="matematik",
            exam_type="TYT",
            user_id=user_id,
        )

    # Generate report
    print(manager.generate_report(days=30))
