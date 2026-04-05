import sys, re, glob

files = [
    "clustering_api",
    "hybrid_question_generation",
    "manipulatives_api",
    "manipulatives_progress_api",
    "quality_gates_api",
    "rag",
    "zemberek",
]

base = "/app/api"
fixed = []
errors = []

for name in files:
    path = f"{base}/{name}.py"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        old = "from core.auth_dependencies import get_current_user"
        new = "from core.dependencies import get_current_user  # fixed: was auth_dependencies (no blacklist)"

        if old in content:
            content = content.replace(old, new, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            fixed.append(name)
        else:
            errors.append(f"{name}: pattern not found")
    except Exception as e:
        errors.append(f"{name}: {e}")

print("FIXED:", fixed)
print("ERRORS:", errors)
