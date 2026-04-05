#!/usr/bin/env python
"""
Quick Test Script for MCP Services
Tests available MCP services to verify they can be imported and initialized
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import(module_name: str) -> bool:
    """Test if a module can be imported"""
    try:
        print(f"Testing: {module_name}...", end=" ")
        __import__(module_name)
        print("[OK]")
        return True
    except ImportError as e:
        print(f"[FAILED]: {e}")
        return False
    except Exception as e:
        print(f"[WARNING]: {e}")
        return False

def test_class_init(module_name: str, class_name: str) -> bool:
    """Test if a class can be instantiated"""
    try:
        print(f"Testing: {module_name}.{class_name}...", end=" ")
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        instance = cls()
        print(f"[OK] (instance: {type(instance).__name__})")
        return True
    except ImportError as e:
        print(f"[FAILED] (import): {e}")
        return False
    except Exception as e:
        print(f"[WARNING] (init): {e}")
        return False

def main():
    print("=" * 60)
    print("MCP Services Test Suite")
    print("=" * 60)
    print()

    # Test environment
    print("1. Testing Environment Setup")
    print("-" * 60)

    env_vars = [
        "REDIS_URL",
        "ELASTICSEARCH_URL",
        "DATABASE_URL",
        "YOUTUBE_API_KEY",
    ]

    for var in env_vars:
        value = os.getenv(var, "NOT SET")
        if value == "NOT SET" or value == "YOUR_API_KEY_HERE_REPLACE_ME":
            print(f"[WARN] {var}: Not configured")
        else:
            # Mask sensitive values
            if "KEY" in var or "PASSWORD" in var or "SECRET" in var:
                masked = value[:8] + "..." if len(value) > 8 else "***"
                print(f"[OK] {var}: {masked}")
            else:
                print(f"[OK] {var}: {value}")

    print()
    print("2. Testing Module Imports")
    print("-" * 60)

    modules_to_test = [
        "backend.services.turkish_content_filter",
        "backend.services.subject_relevance_scorer",
        "backend.services.video_quality_validator",
        "backend.services.enhanced_resource_recommendation_engine",
        "backend.services.video_recommendation_monitoring",
    ]

    results = []
    for module in modules_to_test:
        result = test_import(module)
        results.append((module, result))

    print()
    print("3. Testing Class Initialization")
    print("-" * 60)

    classes_to_test = [
        ("backend.services.turkish_content_filter", "TurkishContentFilter"),
        ("backend.services.subject_relevance_scorer", "SubjectRelevanceScorer"),
        ("backend.services.video_quality_validator", "VideoQualityValidator"),
    ]

    init_results = []
    for module, cls_name in classes_to_test:
        result = test_class_init(module, cls_name)
        init_results.append((f"{module}.{cls_name}", result))

    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    import_success = sum(1 for _, r in results if r)
    import_total = len(results)
    init_success = sum(1 for _, r in init_results if r)
    init_total = len(init_results)

    print(f"Module Imports: {import_success}/{import_total} succeeded")
    print(f"Class Initialization: {init_success}/{init_total} succeeded")

    if import_success == import_total and init_success == init_total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Check output above for details.")
        return 1

if __name__ == "__main__":
    # Load .env.local if exists
    env_file = Path(__file__).parent / ".env.local"
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print()

    sys.exit(main())
