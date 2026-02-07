"""
Token Usage Tracker
Tracks token usage, optimization savings, and costs across all LLM providers

Author: KIRO AI Team
Date: 2025-10-19
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
from collections import defaultdict
import statistics


class TokenUsageTracker:
    """
    Token Usage Tracker

    Tracks:
    - Original vs optimized token counts
    - Token savings per provider
    - Cost savings
    - Daily/weekly/monthly aggregates
    """

    def __init__(self, log_path: str = "logs/token_usage.jsonl"):
        """
        Initialize tracker

        Args:
            log_path: Path to log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(exist_ok=True, parents=True)

    def log_usage(
        self,
        provider: str,
        request_id: str,
        original_tokens: int,
        optimized_tokens: int,
        cost_per_1k: float,
        optimization_method: str = "turkish_optimizer",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log token usage

        Args:
            provider: LLM provider name (openai, claude, qwen)
            request_id: Unique request ID
            original_tokens: Original token count before optimization
            optimized_tokens: Token count after optimization
            cost_per_1k: Cost per 1000 tokens in USD
            optimization_method: Method used for optimization
            metadata: Additional metadata (topic, exam_type, etc.)
        """
        savings = original_tokens - optimized_tokens
        savings_percentage = (
            (savings / original_tokens * 100) if original_tokens > 0 else 0
        )

        original_cost = (original_tokens / 1000) * cost_per_1k
        optimized_cost = (optimized_tokens / 1000) * cost_per_1k
        cost_saved = original_cost - optimized_cost

        entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "provider": provider,
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "tokens_saved": savings,
            "savings_percentage": round(savings_percentage, 2),
            "original_cost_usd": round(original_cost, 6),
            "optimized_cost_usd": round(optimized_cost, 6),
            "cost_saved_usd": round(cost_saved, 6),
            "cost_per_1k_tokens": cost_per_1k,
            "optimization_method": optimization_method,
            "metadata": metadata or {},
        }

        # Append to log file
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get token usage statistics

        Args:
            start_date: Start date filter
            end_date: End date filter
            provider: Provider filter

        Returns:
            Statistics dictionary
        """
        if not self.log_path.exists():
            return self._empty_stats()

        # Read all entries
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())

                    # Apply filters
                    entry_date = datetime.fromisoformat(entry["timestamp"])

                    if start_date and entry_date < start_date:
                        continue
                    if end_date and entry_date > end_date:
                        continue
                    if provider and entry["provider"] != provider:
                        continue

                    entries.append(entry)
                except Exception:
                    continue

        if not entries:
            return self._empty_stats()

        # Calculate aggregates
        total_requests = len(entries)
        total_original_tokens = sum(e["original_tokens"] for e in entries)
        total_optimized_tokens = sum(e["optimized_tokens"] for e in entries)
        total_tokens_saved = sum(e["tokens_saved"] for e in entries)
        total_cost_saved = sum(e["cost_saved_usd"] for e in entries)

        savings_percentages = [e["savings_percentage"] for e in entries]
        avg_savings_percentage = statistics.mean(savings_percentages)

        # Per-provider breakdown
        provider_stats = defaultdict(
            lambda: {
                "requests": 0,
                "original_tokens": 0,
                "optimized_tokens": 0,
                "tokens_saved": 0,
                "cost_saved_usd": 0,
            }
        )

        for entry in entries:
            p = entry["provider"]
            provider_stats[p]["requests"] += 1
            provider_stats[p]["original_tokens"] += entry["original_tokens"]
            provider_stats[p]["optimized_tokens"] += entry["optimized_tokens"]
            provider_stats[p]["tokens_saved"] += entry["tokens_saved"]
            provider_stats[p]["cost_saved_usd"] += entry["cost_saved_usd"]

        return {
            "total_requests": total_requests,
            "total_original_tokens": total_original_tokens,
            "total_optimized_tokens": total_optimized_tokens,
            "total_tokens_saved": total_tokens_saved,
            "average_savings_percentage": round(avg_savings_percentage, 2),
            "total_cost_saved_usd": round(total_cost_saved, 2),
            "provider_breakdown": dict(provider_stats),
            "date_range": {
                "start": entries[0]["timestamp"] if entries else None,
                "end": entries[-1]["timestamp"] if entries else None,
            },
        }

    def get_daily_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get daily statistics for last N days

        Args:
            days: Number of days to include

        Returns:
            Daily statistics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return self.get_stats(start_date=start_date, end_date=end_date)

    def get_monthly_projection(self) -> Dict[str, Any]:
        """
        Get monthly cost savings projection based on recent usage

        Returns:
            Monthly projection
        """
        # Get last 7 days stats
        weekly_stats = self.get_daily_stats(days=7)

        if weekly_stats["total_requests"] == 0:
            return {
                "projected_monthly_requests": 0,
                "projected_monthly_cost_saved": 0,
                "projected_annual_cost_saved": 0,
            }

        # Project to monthly
        daily_avg_requests = weekly_stats["total_requests"] / 7
        daily_avg_cost_saved = weekly_stats["total_cost_saved_usd"] / 7

        monthly_requests = daily_avg_requests * 30
        monthly_cost_saved = daily_avg_cost_saved * 30
        annual_cost_saved = monthly_cost_saved * 12

        return {
            "projected_monthly_requests": int(monthly_requests),
            "projected_monthly_cost_saved": round(monthly_cost_saved, 2),
            "projected_annual_cost_saved": round(annual_cost_saved, 2),
            "based_on_last_7_days": weekly_stats,
        }

    def generate_report(self, days: int = 30) -> str:
        """
        Generate human-readable report

        Args:
            days: Number of days to include

        Returns:
            Formatted report string
        """
        stats = self.get_daily_stats(days=days)
        projection = self.get_monthly_projection()

        report = f"""
TOKEN USAGE OPTIMIZATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {days} days

=== SUMMARY ===
Total Requests: {stats['total_requests']:,}
Total Tokens Saved: {stats['total_tokens_saved']:,}
Average Savings: {stats['average_savings_percentage']:.1f}%
Total Cost Saved: ${stats['total_cost_saved_usd']:.2f}

=== PROVIDER BREAKDOWN ===
"""

        for provider, pstats in stats["provider_breakdown"].items():
            provider_savings_pct = (
                (pstats["tokens_saved"] / pstats["original_tokens"] * 100)
                if pstats["original_tokens"] > 0
                else 0
            )
            report += f"""
{provider.upper()}:
  Requests: {pstats['requests']:,}
  Tokens Saved: {pstats['tokens_saved']:,}
  Savings: {provider_savings_pct:.1f}%
  Cost Saved: ${pstats['cost_saved_usd']:.2f}
"""

        report += f"""
=== MONTHLY PROJECTION ===
Projected Monthly Requests: {projection['projected_monthly_requests']:,}
Projected Monthly Savings: ${projection['projected_monthly_cost_saved']:.2f}/month
Projected Annual Savings: ${projection['projected_annual_cost_saved']:.2f}/year

"""
        return report

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure"""
        return {
            "total_requests": 0,
            "total_original_tokens": 0,
            "total_optimized_tokens": 0,
            "total_tokens_saved": 0,
            "average_savings_percentage": 0,
            "total_cost_saved_usd": 0,
            "provider_breakdown": {},
            "date_range": {"start": None, "end": None},
        }

    def export_csv(self, output_path: str, days: int = 30):
        """
        Export usage data to CSV

        Args:
            output_path: Output CSV file path
            days: Number of days to include
        """
        import csv

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        if not self.log_path.exists():
            return

        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_date = datetime.fromisoformat(entry["timestamp"])

                    if start_date <= entry_date <= end_date:
                        entries.append(entry)
                except Exception:
                    continue

        if not entries:
            return

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "timestamp",
                "request_id",
                "provider",
                "original_tokens",
                "optimized_tokens",
                "tokens_saved",
                "savings_percentage",
                "original_cost_usd",
                "optimized_cost_usd",
                "cost_saved_usd",
                "optimization_method",
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for entry in entries:
                row = {k: entry.get(k, "") for k in fieldnames}
                writer.writerow(row)

        print(f"Exported {len(entries)} entries to {output_path}")


# Singleton instance
_tracker_instance = None


def get_tracker() -> TokenUsageTracker:
    """Get global tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = TokenUsageTracker()
    return _tracker_instance


# Example usage
if __name__ == "__main__":
    tracker = TokenUsageTracker()

    # Simulate some usage
    tracker.log_usage(
        provider="openai",
        request_id="test-1",
        original_tokens=100,
        optimized_tokens=95,
        cost_per_1k=0.01,
        metadata={"topic": "matematik", "exam_type": "TYT"},
    )

    tracker.log_usage(
        provider="claude",
        request_id="test-2",
        original_tokens=150,
        optimized_tokens=140,
        cost_per_1k=0.003,
        metadata={"topic": "fen", "exam_type": "AYT"},
    )

    # Get stats
    stats = tracker.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # Generate report
    print(tracker.generate_report(days=7))
