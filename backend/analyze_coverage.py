import json

with open("coverage.json") as f:
    data = json.load(f)

# Collect 0% coverage files
zero_coverage_api = []
zero_coverage_core = []

for file, info in data["files"].items():
    coverage_pct = info["summary"]["percent_covered"]
    lines = info["summary"]["num_statements"]

    if coverage_pct == 0:
        if file.startswith("api/") and file.endswith(".py"):
            zero_coverage_api.append((file, lines))
        elif file.startswith("core/") and file.endswith(".py"):
            zero_coverage_core.append((file, lines))

# Sort by lines (smaller = easier)
zero_coverage_api.sort(key=lambda x: x[1])
zero_coverage_core.sort(key=lambda x: x[1])

print("=" * 80)
print("0% COVERAGE MODULES - ÖNCELİKLENDİRİLMİŞ LİSTE")
print("=" * 80)
print()

print("📁 API ENDPOINTS (0% coverage, küçükten büyüğe):")
print("-" * 80)
for i, (file, lines) in enumerate(zero_coverage_api[:15], 1):
    print(f"{i:2d}. {lines:4d} satır - {file}")

print()
print("📁 CORE MODULES (0% coverage, küçükten büyüğe):")
print("-" * 80)
for i, (file, lines) in enumerate(zero_coverage_core[:15], 1):
    print(f"{i:2d}. {lines:4d} satır - {file}")

print()
print(f"Toplam 0% API: {len(zero_coverage_api)}")
print(f"Toplam 0% Core: {len(zero_coverage_core)}")
print()

# Recommend easy wins
print("🎯 ÖNERİLEN İLK 5 HEDEF (En kolay kazançlar):")
print("-" * 80)
easy_targets = []
for file, lines in zero_coverage_api[:3]:
    if lines < 100:
        easy_targets.append((file, lines, "API"))
for file, lines in zero_coverage_core[:3]:
    if lines < 80:
        easy_targets.append((file, lines, "Core"))

easy_targets.sort(key=lambda x: x[1])
for i, (file, lines, type_) in enumerate(easy_targets[:5], 1):
    print(f"{i}. [{type_:4s}] {lines:3d} satır - {file}")
