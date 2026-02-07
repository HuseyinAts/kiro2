"""
KIRO2 Platform Integration Verification Script
Based on INTEGRATION_CHECKLISTS.md

This script systematically verifies all critical component integrations
as outlined in the comprehensive integration checklists.
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))


class IntegrationVerifier:
    """Systematic integration verification based on checklists"""

    def __init__(self):
        self.results = {
            "critical": [],  # Blocking issues
            "high": [],      # Degraded functionality
            "medium": [],    # Performance/optimization
            "low": [],       # Nice-to-have
            "passed": []     # Successful checks
        }

    def check_layer_1_frontend_api_integration(self) -> Dict:
        """Layer 1: Frontend ↔ API Gateway Integration"""
        print("\n" + "="*80)
        print("LAYER 1: Frontend ↔ API Gateway Integration")
        print("="*80)

        checks = []

        # Check 1.1: OpenAPI Schema Generation
        openapi_path = backend_path / "openapi.json"
        if openapi_path.exists():
            checks.append(("✅", "OpenAPI schema exists", openapi_path))
            with open(openapi_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                endpoint_count = len(schema.get('paths', {}))
                checks.append(("✅", f"OpenAPI endpoints: {endpoint_count}", None))
        else:
            checks.append(("❌", "OpenAPI schema NOT found", "critical"))
            self.results["critical"].append("OpenAPI schema missing - run: cd backend && python export_openapi_schema.py")

        # Check 1.2: TypeScript Types Generated
        frontend_types = Path(__file__).parent / "frontend/src/types/api.generated.ts"
        if frontend_types.exists():
            size = frontend_types.stat().st_size
            checks.append(("✅", f"TypeScript types exist ({size:,} bytes)", frontend_types))
        else:
            checks.append(("⚠️", "TypeScript types NOT generated", "high"))
            self.results["high"].append("TypeScript types missing - run: npm run generate:types")

        # Check 1.3: API Base URL Configuration
        env_files = [
            Path(__file__).parent / "frontend/.env",
            Path(__file__).parent / "frontend/.env.local",
            Path(__file__).parent / "frontend/.env.development"
        ]
        env_found = any(f.exists() for f in env_files)
        if env_found:
            checks.append(("✅", "Frontend environment config exists", None))
        else:
            checks.append(("⚠️", "Frontend .env files not found", "medium"))

        return {"layer": "Frontend ↔ API Gateway", "checks": checks}

    def check_layer_2_api_gateway_middleware(self) -> Dict:
        """Layer 2: API Gateway ↔ Core Infrastructure"""
        print("\n" + "="*80)
        print("LAYER 2: API Gateway ↔ Core Infrastructure (Middleware)")
        print("="*80)

        checks = []

        try:
            # Import main to trigger middleware loading
            from main import app

            # Check middleware count
            middleware_count = len(app.user_middleware)
            checks.append(("✅", f"Middleware loaded: {middleware_count}", None))

            # Check route count
            route_count = len(app.routes)
            checks.append(("✅", f"Routes registered: {route_count}", None))

        except Exception as e:
            checks.append(("❌", f"Backend import failed: {str(e)[:100]}", "critical"))
            self.results["critical"].append(f"Backend import error: {e}")

        # Check specific middleware files
        middleware_files = [
            "core/middleware/timeout_middleware.py",
            "core/middleware/logging_middleware.py",
            "core/rate_limiting.py",
            "core/auth_rate_limiting.py",
            "core/csrf_protection.py"
        ]

        for mw_file in middleware_files:
            mw_path = backend_path / mw_file
            if mw_path.exists():
                checks.append(("✅", f"Middleware file: {mw_file}", None))
            else:
                checks.append(("⚠️", f"Missing: {mw_file}", "medium"))

        return {"layer": "API Gateway ↔ Middleware", "checks": checks}

    def check_layer_3_database_integration(self) -> Dict:
        """Layer 3: Core Infrastructure ↔ Database"""
        print("\n" + "="*80)
        print("LAYER 3: Core Infrastructure ↔ Database")
        print("="*80)

        checks = []

        # Check database configuration
        db_config = backend_path / "core/database.py"
        if db_config.exists():
            checks.append(("✅", "Database config exists", db_config))
        else:
            checks.append(("❌", "Database config missing", "critical"))

        # Check Alembic migrations
        alembic_dir = backend_path / "alembic"
        if alembic_dir.exists():
            versions = list((alembic_dir / "versions").glob("*.py"))
            checks.append(("✅", f"Alembic migrations: {len(versions)} files", None))
        else:
            checks.append(("❌", "Alembic directory not found", "critical"))

        # Check models
        models_dir = backend_path / "models"
        if models_dir.exists():
            model_files = list(models_dir.glob("*.py"))
            checks.append(("✅", f"Model files: {len(model_files)}", None))
        else:
            checks.append(("❌", "Models directory not found", "critical"))

        return {"layer": "Core Infrastructure ↔ Database", "checks": checks}

    def check_layer_4_redis_cache_integration(self) -> Dict:
        """Layer 4: Core Infrastructure ↔ Redis Cache"""
        print("\n" + "="*80)
        print("LAYER 4: Core Infrastructure ↔ Redis Cache")
        print("="*80)

        checks = []

        # Check Redis configuration
        redis_files = [
            "core/cache.py",
            "core/redis_cache.py",
            "core/multi_layer_cache.py"
        ]

        for redis_file in redis_files:
            redis_path = backend_path / redis_file
            if redis_path.exists():
                checks.append(("✅", f"Redis file: {redis_file}", None))
            else:
                checks.append(("⚠️", f"Missing: {redis_file}", "medium"))

        return {"layer": "Core Infrastructure ↔ Redis", "checks": checks}

    def check_layer_5_ai_integration(self) -> Dict:
        """Layer 5: Business Logic ↔ AI/ML Services"""
        print("\n" + "="*80)
        print("LAYER 5: Business Logic ↔ AI/ML Services")
        print("="*80)

        checks = []

        # Check AI service files
        ai_services = [
            "services/llm_service.py",
            "services/berturk_service.py",
            "services/multi_agent_service.py",
            "algorithms/irt_morfoloji_service.py",
            "algorithms/turkish_zpd_maarif_system.py"
        ]

        for ai_file in ai_services:
            ai_path = backend_path / ai_file
            if ai_path.exists():
                checks.append(("✅", f"AI service: {ai_file}", None))
            else:
                checks.append(("⚠️", f"Missing: {ai_file}", "high"))

        return {"layer": "Business Logic ↔ AI/ML", "checks": checks}

    def check_layer_6_monitoring_integration(self) -> Dict:
        """Layer 6: Platform ↔ Monitoring Services"""
        print("\n" + "="*80)
        print("LAYER 6: Platform ↔ Monitoring Services")
        print("="*80)

        checks = []

        # Check monitoring configuration
        monitoring_files = [
            "core/sentry_config.py",
            "core/opentelemetry_config.py",
            "monitoring/enhanced_prometheus_metrics.py"
        ]

        for mon_file in monitoring_files:
            mon_path = backend_path / mon_file
            if mon_path.exists():
                checks.append(("✅", f"Monitoring: {mon_file}", None))
            else:
                checks.append(("⚠️", f"Missing: {mon_file}", "medium"))

        # Check monitoring directories
        mon_dirs = [
            Path(__file__).parent / "monitoring/prometheus",
            Path(__file__).parent / "monitoring/grafana",
            Path(__file__).parent / "monitoring/jaeger"
        ]

        for mon_dir in mon_dirs:
            if mon_dir.exists():
                checks.append(("✅", f"Monitoring dir: {mon_dir.name}", None))
            else:
                checks.append(("ℹ️", f"Optional: {mon_dir.name}", "low"))

        return {"layer": "Platform ↔ Monitoring", "checks": checks}

    def check_critical_files(self) -> Dict:
        """Check critical configuration files"""
        print("\n" + "="*80)
        print("CRITICAL CONFIGURATION FILES")
        print("="*80)

        checks = []

        critical_files = [
            ("backend/.env", "Backend environment config", "critical"),
            ("backend/config.yaml", "Backend YAML config", "critical"),
            ("backend/requirements.txt", "Python dependencies", "critical"),
            ("frontend/package.json", "Node dependencies", "critical"),
            ("docker-compose.yml", "Docker orchestration", "high"),
            (".gitignore", "Git ignore rules", "medium")
        ]

        for file_path, description, severity in critical_files:
            full_path = Path(__file__).parent / file_path
            if full_path.exists():
                checks.append(("✅", f"{description}: {file_path}", None))
            else:
                checks.append(("❌", f"Missing: {file_path}", severity))
                self.results[severity].append(f"Missing {description}: {file_path}")

        return {"layer": "Critical Files", "checks": checks}

    def run_all_checks(self):
        """Run all integration checks"""
        print("\n" + "="*80)
        print("KIRO2 PLATFORM INTEGRATION VERIFICATION")
        print("Based on INTEGRATION_CHECKLISTS.md")
        print("="*80)

        all_results = []

        # Run all layer checks
        all_results.append(self.check_layer_1_frontend_api_integration())
        all_results.append(self.check_layer_2_api_gateway_middleware())
        all_results.append(self.check_layer_3_database_integration())
        all_results.append(self.check_layer_4_redis_cache_integration())
        all_results.append(self.check_layer_5_ai_integration())
        all_results.append(self.check_layer_6_monitoring_integration())
        all_results.append(self.check_critical_files())

        # Print summary
        self.print_summary(all_results)

        return all_results

    def print_summary(self, all_results: List[Dict]):
        """Print verification summary"""
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)

        total_checks = 0
        passed_checks = 0

        for layer_result in all_results:
            layer_name = layer_result["layer"]
            checks = layer_result["checks"]

            layer_passed = sum(1 for check in checks if check[0] == "✅")
            layer_total = len(checks)

            total_checks += layer_total
            passed_checks += layer_passed

            status = "✅ PASS" if layer_passed == layer_total else "⚠️ ISSUES"
            print(f"\n{status} {layer_name}: {layer_passed}/{layer_total} checks passed")

            # Print failed checks
            for icon, message, severity in checks:
                if icon != "✅":
                    print(f"  {icon} {message}")

        # Overall score
        print("\n" + "="*80)
        score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        print(f"OVERALL INTEGRATION HEALTH: {score:.1f}% ({passed_checks}/{total_checks})")
        print("="*80)

        # Print prioritized issues
        if self.results["critical"]:
            print("\n❌ CRITICAL ISSUES (Must fix immediately):")
            for issue in self.results["critical"]:
                print(f"  - {issue}")

        if self.results["high"]:
            print("\n⚠️ HIGH PRIORITY (Degraded functionality):")
            for issue in self.results["high"]:
                print(f"  - {issue}")

        if self.results["medium"]:
            print("\nℹ️ MEDIUM PRIORITY (Performance/optimization):")
            for issue in self.results["medium"][:5]:  # Show first 5
                print(f"  - {issue}")
            if len(self.results["medium"]) > 5:
                print(f"  ... and {len(self.results['medium']) - 5} more")


if __name__ == "__main__":
    verifier = IntegrationVerifier()
    results = verifier.run_all_checks()

    # Exit with error code if critical issues found
    if verifier.results["critical"]:
        sys.exit(1)
    else:
        sys.exit(0)
