"""
Import Check Script
===================
Verifies that all 9 router files can be imported without TypeErrors.
"""

import sys
import importlib
import os

# Change to backend directory
os.chdir(r"c:\Users\husey\kiro2\backend")
sys.path.insert(0, ".")

# List of routers to check
routers = [
    "api.berturk_api",
    "api.learning_path_v2",
    "api.rag",
    "api.turkish_nlp_chat",
    "api.vision_api",
    "api.youtube_routes",
    "api.v1.expert_agents_api",
    "api.v1.semantic_search"
]

ok = 0
fail = 0
errors = []

print("=" * 60)
print("KIRO2 Router Import Check")
print("=" * 60)
print()

for router_module in routers:
    try:
        module = importlib.import_module(router_module)
        ok += 1
        print(f"[OK]   {router_module}")
    except Exception as e:
        fail += 1
        error_msg = f"{type(e).__name__}: {str(e)}"
        errors.append((router_module, error_msg))
        print(f"[FAIL] {router_module}")
        print(f"       {error_msg}")

print()
print("=" * 60)
print(f"Results: OK={ok}, FAIL={fail}")
print("=" * 60)

if errors:
    print()
    print("Failed imports:")
    for module, error in errors:
        print(f"  - {module}")
        print(f"    {error}")
    sys.exit(1)
else:
    print()
    print("All routers imported successfully!")
    sys.exit(0)
