"""
Import Validation Script
Validates that all refactored modules can be imported correctly
"""

import sys
import traceback


def validate_imports():
    """Validate all module imports"""
    results = []
    errors = []

    modules_to_test = [
        # Models
        (
            "Models",
            "backend.agents.learning_path.models",
            [
                "StudentProfile",
                "LearningResource",
                "LearningPath",
                "LearningPhase",
                "LearningStyle",
                "KnowledgeLevel",
            ],
        ),
        # Core components
        (
            "StudentProfiler",
            "backend.agents.learning_path.core.student_profiler",
            ["StudentProfiler"],
        ),
        (
            "AssessmentCreator",
            "backend.agents.learning_path.core.assessment_creator",
            ["AssessmentCreator"],
        ),
        (
            "ResourceFinder",
            "backend.agents.learning_path.core.resource_finder",
            ["ResourceFinder"],
        ),
        (
            "PathGenerator",
            "backend.agents.learning_path.core.path_generator",
            ["PathGenerator"],
        ),
        (
            "PathOptimizer",
            "backend.agents.learning_path.core.path_optimizer",
            ["PathOptimizer"],
        ),
        # Strategies
        (
            "LearningStyleStrategy",
            "backend.agents.learning_path.strategies.learning_style_strategy",
            ["LearningStyleStrategy"],
        ),
        (
            "DifficultyAdapter",
            "backend.agents.learning_path.strategies.difficulty_adapter",
            ["DifficultyAdapter"],
        ),
        (
            "TimePlanner",
            "backend.agents.learning_path.strategies.time_planner",
            ["TimePlanner"],
        ),
        # Integrations
        (
            "YouTubeIntegration",
            "backend.agents.learning_path.integrations.youtube_integration",
            ["YouTubeIntegration"],
        ),
        (
            "KhanIntegration",
            "backend.agents.learning_path.integrations.khan_integration",
            ["KhanIntegration"],
        ),
        (
            "OERIntegration",
            "backend.agents.learning_path.integrations.oer_integration",
            ["OERIntegration"],
        ),
        (
            "ChatIntegration",
            "backend.agents.learning_path.integrations.chat_integration",
            ["ChatIntegration"],
        ),
        (
            "FormIntegration",
            "backend.agents.learning_path.integrations.form_integration",
            ["FormIntegration"],
        ),
        # Utilities
        (
            "Validators",
            "backend.agents.learning_path.utils.validators",
            [
                "ValidationError",
                "StudentDataValidator",
                "AssessmentDataValidator",
                "ResourceDataValidator",
                "PathDataValidator",
                "ChatDataValidator",
            ],
        ),
        (
            "Formatters",
            "backend.agents.learning_path.utils.formatters",
            [
                "StudentProfileFormatter",
                "ResourceFormatter",
                "PathFormatter",
                "AssessmentFormatter",
                "ProgressFormatter",
                "ChatFormatter",
                "ErrorFormatter",
            ],
        ),
        # Main Agent
        (
            "LearningPathAgent",
            "backend.agents.learning_path.agent",
            ["LearningPathAgent"],
        ),
        # Package exports
        (
            "Package Main",
            "backend.agents.learning_path",
            ["LearningPathAgent", "StudentProfile"],
        ),
    ]

    print("=" * 80)
    print("LEARNING PATH AGENT - IMPORT VALIDATION")
    print("=" * 80)
    print()

    for module_name, module_path, classes in modules_to_test:
        try:
            # Import the module
            module = __import__(module_path, fromlist=classes)

            # Check if all expected classes exist
            missing_classes = []
            for cls_name in classes:
                if not hasattr(module, cls_name):
                    missing_classes.append(cls_name)

            if missing_classes:
                status = "⚠️  PARTIAL"
                error_msg = f"Missing: {', '.join(missing_classes)}"
                errors.append(f"{module_name}: {error_msg}")
            else:
                status = "✅ SUCCESS"
                error_msg = ""

            results.append(
                {"module": module_name, "status": status, "error": error_msg}
            )

            print(f"{status:12} | {module_name:30} | {error_msg}")

        except Exception as e:
            status = "❌ FAILED"
            error_msg = str(e)
            errors.append(f"{module_name}: {error_msg}")
            results.append(
                {"module": module_name, "status": status, "error": error_msg}
            )

            print(f"{status:12} | {module_name:30} | {error_msg}")
            if "--verbose" in sys.argv:
                traceback.print_exc()

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    success_count = sum(1 for r in results if "SUCCESS" in r["status"])
    partial_count = sum(1 for r in results if "PARTIAL" in r["status"])
    failed_count = sum(1 for r in results if "FAILED" in r["status"])
    total_count = len(results)

    print(f"Total Modules: {total_count}")
    print(f"✅ Success: {success_count}")
    print(f"⚠️  Partial: {partial_count}")
    print(f"❌ Failed: {failed_count}")
    print()

    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print()

    # Exit code
    if failed_count > 0:
        print("❌ VALIDATION FAILED")
        return 1
    if partial_count > 0:
        print("⚠️  VALIDATION PARTIAL SUCCESS")
        return 2
    print("✅ ALL IMPORTS VALIDATED SUCCESSFULLY")
    return 0


if __name__ == "__main__":
    exit_code = validate_imports()
    sys.exit(exit_code)
