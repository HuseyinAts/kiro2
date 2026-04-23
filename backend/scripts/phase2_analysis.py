#!/usr/bin/env python3
"""
Phase 2 Analysis - Core Modules Strategic Coverage
Target: 35% overall coverage focusing on core business logic
"""

import json
import sys
from dataclasses import dataclass


@dataclass
class Phase2Target:
    """Phase 2 coverage target"""

    phase: str
    target_percentage: float
    focus_areas: list[str]
    test_types: list[str]
    estimated_effort: str
    priority_level: str


class Phase2AnalysisStrategy:
    """Phase 2 core modules analysis strategy"""

    def __init__(self):
        self.phase2_targets = [
            Phase2Target(
                phase="Phase 2: Core Modules",
                target_percentage=35.0,
                focus_areas=[
                    "Database Layer & ORM",
                    "API Endpoints & Controllers",
                    "Service Integrations",
                    "Business Logic Methods",
                    "Data Processing Pipelines",
                    "Authentication & Authorization",
                ],
                test_types=[
                    "Integration Tests",
                    "Method-Level Unit Tests",
                    "Database Tests",
                    "API Endpoint Tests",
                    "Service Layer Tests",
                ],
                estimated_effort="2-3 days",
                priority_level="High",
            )
        ]

    def analyze_phase2_targets(self):
        """Phase 2 target dosyalarını analiz et"""

        try:
            # Baseline coverage oku
            with open("coverage.json") as f:
                coverage_data = json.load(f)
        except FileNotFoundError:
            print("Coverage.json bulunamadı. Önce coverage raporu oluşturun.")
            return False

        print("PHASE 2: CORE MODULES ANALYSIS")
        print("=" * 60)
        print(
            f"Current Overall Coverage: {coverage_data['totals']['percent_covered']:.2f}%"
        )
        print("Target Coverage: 35.0%")
        print(f"Gap to Close: {35.0 - coverage_data['totals']['percent_covered']:.1f}%")
        print()

        # Core modules priority sıralaması
        print("CORE MODULES PRIORITY ANALYSIS:")
        print("-" * 40)

        core_modules = []

        for file_path, file_data in coverage_data["files"].items():
            filename = (
                file_path.split("/")[-1]
                if "/" in file_path
                else file_path.split("\\")[-1]
            )

            # Core module patterns
            is_core = any(
                pattern in file_path.lower()
                for pattern in [
                    "api/",
                    "core/",
                    "services/",
                    "models/",
                    "database/",
                    "auth/",
                    "handlers/",
                    "controllers/",
                    "middleware/",
                ]
            )

            if is_core and filename.endswith(".py"):
                current_cov = file_data["summary"]["percent_covered"]
                lines = file_data["summary"]["num_statements"]
                missing_lines = file_data["summary"]["missing_lines"]

                # Core module skorlama
                impact_score = self.calculate_core_impact_score(
                    filename, lines, current_cov, file_path
                )

                core_modules.append(
                    {
                        "filename": filename,
                        "path": file_path,
                        "lines": lines,
                        "current_coverage": current_cov,
                        "missing_lines": missing_lines,
                        "impact_score": impact_score,
                        "category": self.categorize_core_module(file_path),
                    }
                )

        # Impact score'a göre sırala
        core_modules.sort(key=lambda x: x["impact_score"], reverse=True)

        # Top 8 core modules
        top_core_modules = core_modules[:8]

        print(
            f"{'Rank':<4} {'File':<30} {'Lines':<6} {'Coverage':<9} {'Category':<15} {'Impact':<6}"
        )
        print("-" * 80)

        for i, module in enumerate(top_core_modules, 1):
            print(
                f"{i:<4} {module['filename']:<30} {module['lines']:<6} "
                f"{module['current_coverage']:>6.1f}% {module['category']:<15} {module['impact_score']:<6.1f}"
            )

        print()

        # Phase 2 strategy breakdown
        print("PHASE 2 STRATEGY BREAKDOWN:")
        print("-" * 30)

        categories = {}
        for module in top_core_modules:
            cat = module["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(module)

        for category, modules in categories.items():
            total_lines = sum(m["lines"] for m in modules)
            avg_coverage = sum(m["current_coverage"] for m in modules) / len(modules)

            print(f"{category}:")
            print(f"   Files: {len(modules)}")
            print(f"   Total Lines: {total_lines:,}")
            print(f"   Avg Coverage: {avg_coverage:.1f}%")
            print(f"   Priority: {'HIGH' if avg_coverage < 25 else 'MEDIUM'}")
            print()

        # Test implementasyon planı
        print("PHASE 2 TEST IMPLEMENTATION PLAN:")
        print("-" * 35)

        for i, module in enumerate(top_core_modules[:5], 1):
            print(f"{i}. {module['filename']} ({module['category']})")
            print(f"   Current: {module['current_coverage']:.1f}% | Target: +15-20%")
            print(f"   Focus: {self.get_test_focus(module['category'])}")
            print(f"   Lines: {module['lines']} | Missing: {module['missing_lines']}")
            print()

        # Effort estimation
        print("EFFORT ESTIMATION:")
        print("-" * 18)

        total_missing_lines = sum(m["missing_lines"] for m in top_core_modules[:5])
        estimated_tests = total_missing_lines // 20  # Rough estimate

        print(
            f"Total Priority Lines: {sum(m['lines'] for m in top_core_modules[:5]):,}"
        )
        print(f"Total Missing Lines: {total_missing_lines:,}")
        print(f"Estimated Tests: {estimated_tests}")
        print("Estimated Time: 2-3 days")
        print()

        # Next actions
        print("IMMEDIATE NEXT ACTIONS:")
        print("-" * 22)
        print("1. Start with highest impact core module")
        print("2. Focus on method-level testing")
        print("3. Add integration tests for service interactions")
        print("4. Implement database layer tests")
        print("5. Create API endpoint comprehensive tests")

        return True

    def calculate_core_impact_score(
        self, filename: str, lines: int, coverage: float, file_path: str
    ) -> float:
        """Core module impact skorunu hesapla"""

        base_score = lines * (100 - coverage) / 100

        # Core importance multipliers
        multipliers = {
            "api": 2.0,  # API endpoints çok kritik
            "service": 1.8,  # Business logic critical
            "model": 1.6,  # Data models important
            "auth": 1.9,  # Security critical
            "database": 1.7,  # Data layer important
            "handler": 1.5,  # Request handlers
            "controller": 1.5,  # Controllers
            "middleware": 1.4,  # Middleware
        }

        multiplier = 1.0
        for pattern, mult in multipliers.items():
            if pattern in file_path.lower() or pattern in filename.lower():
                multiplier = max(multiplier, mult)

        # Business criticality boost
        critical_patterns = [
            "auth",
            "security",
            "payment",
            "user",
            "student",
            "teacher",
        ]
        for pattern in critical_patterns:
            if pattern in filename.lower():
                multiplier *= 1.2

        return base_score * multiplier

    def categorize_core_module(self, file_path: str) -> str:
        """Core module kategorisini belirle"""

        path_lower = file_path.lower()

        if "api/" in path_lower or "endpoint" in path_lower:
            return "API Layer"
        if "service" in path_lower:
            return "Service Layer"
        if "model" in path_lower or "schema" in path_lower:
            return "Data Models"
        if "auth" in path_lower or "security" in path_lower:
            return "Security"
        if "database" in path_lower or "db" in path_lower:
            return "Database"
        if "handler" in path_lower or "controller" in path_lower:
            return "Controllers"
        if "middleware" in path_lower:
            return "Middleware"
        return "Core Logic"

    def get_test_focus(self, category: str) -> str:
        """Kategori için test odak noktasını belirle"""

        focus_map = {
            "API Layer": "Endpoint testing, request/response validation, error handling",
            "Service Layer": "Business logic methods, service interactions, data flow",
            "Data Models": "Model validation, relationships, serialization",
            "Security": "Authentication, authorization, input validation, encryption",
            "Database": "Query testing, transaction handling, data integrity",
            "Controllers": "Request routing, parameter handling, response formatting",
            "Middleware": "Request processing, filtering, cross-cutting concerns",
            "Core Logic": "Algorithm testing, data processing, business rules",
        }

        return focus_map.get(category, "Comprehensive method and integration testing")


def main():
    """Main analysis function"""
    strategy = Phase2AnalysisStrategy()

    if not strategy.analyze_phase2_targets():
        print("Phase 2 analysis failed!")
        return False

    print("\nPhase 2 analysis completed successfully!")
    print("Ready to implement core modules testing strategy.")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
