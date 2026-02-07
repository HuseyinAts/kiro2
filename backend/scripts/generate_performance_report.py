"""
Performance Report Generator - Task 24
Performans test sonuçlarını analiz edip rapor oluşturur

Requirements: 2.1, 2.5, 2.12, 6.6
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
import glob


class PerformanceReportGenerator:
    """Performance report generator"""

    def __init__(self):
        self.report = {
            "generated_at": datetime.now().isoformat(),
            "benchmarks": {},
            "analysis": {},
            "recommendations": [],
        }

    def load_benchmark_results(self, filepath: str) -> Dict[str, Any]:
        """Load benchmark results from JSON file"""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def analyze_response_time(self, data: Dict[str, Any]):
        """Analyze response time benchmark"""
        rt = data.get("response_time", {})

        p95_ms = rt.get("p95_ms", 0)
        target_ms = rt.get("target_p95_ms", 3000)
        passed = rt.get("passed", False)

        analysis = {
            "status": "PASS" if passed else "FAIL",
            "p95_ms": p95_ms,
            "target_ms": target_ms,
            "margin_ms": target_ms - p95_ms,
            "margin_percent": ((target_ms - p95_ms) / target_ms) * 100,
        }

        if not passed:
            self.report["recommendations"].append(
                {
                    "category": "Response Time",
                    "priority": "HIGH",
                    "issue": f"P95 response time {p95_ms:.0f}ms exceeds target {target_ms}ms",
                    "recommendations": [
                        "Implement multi-layer caching",
                        "Enable parallel video discovery",
                        "Optimize database queries with indexes",
                        "Reduce YouTube API call latency",
                    ],
                }
            )

        return analysis

    def analyze_cache_performance(self, data: Dict[str, Any]):
        """Analyze cache performance"""
        cache = data.get("cache_performance", {})

        hit_rate = cache.get("hit_rate_percent", 0)
        target_rate = cache.get("target_hit_rate_percent", 80)
        passed = cache.get("passed", False)

        analysis = {
            "status": "PASS" if passed else "FAIL",
            "hit_rate_percent": hit_rate,
            "target_percent": target_rate,
            "margin_percent": hit_rate - target_rate,
        }

        if not passed:
            self.report["recommendations"].append(
                {
                    "category": "Cache Performance",
                    "priority": "HIGH",
                    "issue": f"Cache hit rate {hit_rate:.1f}% below target {target_rate}%",
                    "recommendations": [
                        "Implement cache warming for popular content",
                        "Optimize cache key generation",
                        "Increase cache TTL for stable content",
                        "Review cache eviction policy",
                    ],
                }
            )

        return analysis

    def analyze_database_queries(self, data: Dict[str, Any]):
        """Analyze database query performance"""
        db = data.get("database_queries", {})

        avg_ms = db.get("average_ms", 0)
        target_ms = db.get("target_avg_ms", 100)
        passed = db.get("passed", False)

        analysis = {
            "status": "PASS" if passed else "FAIL",
            "avg_ms": avg_ms,
            "target_ms": target_ms,
            "margin_ms": target_ms - avg_ms,
        }

        if not passed:
            self.report["recommendations"].append(
                {
                    "category": "Database Performance",
                    "priority": "MEDIUM",
                    "issue": f"Average query time {avg_ms:.1f}ms exceeds target {target_ms}ms",
                    "recommendations": [
                        "Create composite indexes on frequently queried columns",
                        "Optimize N+1 query patterns",
                        "Implement connection pooling",
                        "Use prepared statements",
                    ],
                }
            )

        return analysis

    def analyze_memory_usage(self, data: Dict[str, Any]):
        """Analyze memory usage"""
        mem = data.get("memory_usage", {})

        growth_mb = mem.get("growth_mb", 0)
        target_mb = mem.get("target_growth_mb", 50)
        passed = mem.get("passed", False)

        analysis = {
            "status": "PASS" if passed else "FAIL",
            "growth_mb": growth_mb,
            "target_mb": target_mb,
            "margin_mb": target_mb - growth_mb,
        }

        if not passed:
            self.report["recommendations"].append(
                {
                    "category": "Memory Usage",
                    "priority": "MEDIUM",
                    "issue": f"Memory growth {growth_mb:.1f}MB exceeds target {target_mb}MB",
                    "recommendations": [
                        "Profile memory usage to identify leaks",
                        "Implement proper resource cleanup",
                        "Use generators for large datasets",
                        "Optimize data structures",
                    ],
                }
            )

        return analysis

    def analyze_parallel_processing(self, data: Dict[str, Any]):
        """Analyze parallel processing performance"""
        parallel = data.get("parallel_processing", {})

        speedup = parallel.get("speedup", 0)
        target_speedup = parallel.get("target_speedup", 2.5)
        passed = parallel.get("passed", False)

        analysis = {
            "status": "PASS" if passed else "FAIL",
            "speedup": speedup,
            "target_speedup": target_speedup,
            "efficiency_percent": parallel.get("efficiency_percent", 0),
        }

        if not passed:
            self.report["recommendations"].append(
                {
                    "category": "Parallel Processing",
                    "priority": "LOW",
                    "issue": f"Speedup {speedup:.1f}x below target {target_speedup}x",
                    "recommendations": [
                        "Increase parallelization of independent tasks",
                        "Optimize task scheduling",
                        "Reduce synchronization overhead",
                        "Use asyncio.gather for concurrent operations",
                    ],
                }
            )

        return analysis

    def generate_report(self, benchmark_file: str):
        """Generate comprehensive performance report"""
        # Load benchmark data
        data = self.load_benchmark_results(benchmark_file)

        # Analyze each benchmark
        self.report["benchmarks"] = {
            "response_time": self.analyze_response_time(data.get("benchmarks", {})),
            "cache_performance": self.analyze_cache_performance(
                data.get("benchmarks", {})
            ),
            "database_queries": self.analyze_database_queries(
                data.get("benchmarks", {})
            ),
            "memory_usage": self.analyze_memory_usage(data.get("benchmarks", {})),
            "parallel_processing": self.analyze_parallel_processing(
                data.get("benchmarks", {})
            ),
        }

        # Overall analysis
        passed_count = sum(
            1 for b in self.report["benchmarks"].values() if b.get("status") == "PASS"
        )
        total_count = len(self.report["benchmarks"])

        self.report["analysis"] = {
            "total_benchmarks": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate_percent": (passed_count / total_count) * 100,
            "overall_status": "PASS" if passed_count == total_count else "FAIL",
        }

        return self.report

    def print_report(self):
        """Print formatted report to console"""
        print("\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS REPORT")
        print("=" * 80)
        print(f"Generated: {self.report['generated_at']}\n")

        # Benchmarks
        print("BENCHMARK RESULTS")
        print("-" * 80)

        for name, result in self.report["benchmarks"].items():
            status_icon = "✓" if result["status"] == "PASS" else "✗"
            print(
                f"\n{status_icon} {name.replace('_', ' ').title()}: {result['status']}"
            )

            # Print key metrics
            for key, value in result.items():
                if key != "status":
                    if isinstance(value, float):
                        print(f"    {key}: {value:.2f}")
                    else:
                        print(f"    {key}: {value}")

        # Overall Analysis
        print("\n" + "-" * 80)
        print("OVERALL ANALYSIS")
        print("-" * 80)
        analysis = self.report["analysis"]
        print(f"Total Benchmarks: {analysis['total_benchmarks']}")
        print(f"Passed:           {analysis['passed']}")
        print(f"Failed:           {analysis['failed']}")
        print(f"Pass Rate:        {analysis['pass_rate_percent']:.1f}%")
        print(f"Overall Status:   {analysis['overall_status']}")

        # Recommendations
        if self.report["recommendations"]:
            print("\n" + "-" * 80)
            print("RECOMMENDATIONS")
            print("-" * 80)

            for i, rec in enumerate(self.report["recommendations"], 1):
                print(f"\n{i}. {rec['category']} (Priority: {rec['priority']})")
                print(f"   Issue: {rec['issue']}")
                print("   Recommendations:")
                for r in rec["recommendations"]:
                    print(f"     - {r}")

        print("\n" + "=" * 80 + "\n")

    def save_report(self, output_file: str):
        """Save report to JSON file"""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"Report saved to: {output_file}")

    def save_markdown_report(self, output_file: str):
        """Save report as Markdown"""
        md = []
        md.append("# Performance Analysis Report\n")
        md.append(f"**Generated**: {self.report['generated_at']}\n")

        # Benchmarks
        md.append("## Benchmark Results\n")
        for name, result in self.report["benchmarks"].items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            md.append(f"### {status_icon} {name.replace('_', ' ').title()}\n")
            md.append(f"**Status**: {result['status']}\n")

            for key, value in result.items():
                if key != "status":
                    if isinstance(value, float):
                        md.append(f"- **{key}**: {value:.2f}\n")
                    else:
                        md.append(f"- **{key}**: {value}\n")
            md.append("\n")

        # Overall Analysis
        md.append("## Overall Analysis\n")
        analysis = self.report["analysis"]
        md.append(f"- **Total Benchmarks**: {analysis['total_benchmarks']}\n")
        md.append(f"- **Passed**: {analysis['passed']}\n")
        md.append(f"- **Failed**: {analysis['failed']}\n")
        md.append(f"- **Pass Rate**: {analysis['pass_rate_percent']:.1f}%\n")
        md.append(f"- **Overall Status**: {analysis['overall_status']}\n\n")

        # Recommendations
        if self.report["recommendations"]:
            md.append("## Recommendations\n")
            for i, rec in enumerate(self.report["recommendations"], 1):
                md.append(f"### {i}. {rec['category']} (Priority: {rec['priority']})\n")
                md.append(f"**Issue**: {rec['issue']}\n\n")
                md.append("**Recommendations**:\n")
                for r in rec["recommendations"]:
                    md.append(f"- {r}\n")
                md.append("\n")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("".join(md))

        print(f"Markdown report saved to: {output_file}")


def main():
    """Main report generator"""
    # Find latest benchmark file
    benchmark_files = glob.glob("backend/reports/performance_benchmark_*.json")

    if not benchmark_files:
        print("No benchmark files found. Run performance_benchmark.py first.")
        return

    latest_file = max(benchmark_files, key=os.path.getctime)
    print(f"Analyzing benchmark file: {latest_file}\n")

    # Generate report
    generator = PerformanceReportGenerator()
    generator.generate_report(latest_file)

    # Print report
    generator.print_report()

    # Save reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generator.save_report(f"backend/reports/performance_analysis_{timestamp}.json")
    generator.save_markdown_report(
        f"backend/reports/performance_analysis_{timestamp}.md"
    )


if __name__ == "__main__":
    main()
