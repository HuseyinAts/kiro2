import json

with open("coverage_full.json") as f:
    data = json.load(f)

files = [(k.replace("\\", "/"), v) for k, v in data["files"].items()]
zero_cov = [
    (f, d["summary"]["percent_covered"])
    for f, d in files
    if d["summary"]["percent_covered"] == 0 and not f.startswith("tests/")
]

print(f"\n=== COVERAGE ANALYSIS ===")
print(f'Total Coverage: {data["totals"]["percent_covered"]:.2f}%')
print(f"Files with 0% coverage: {len(zero_cov)}\n")

print("=== TOP 15 LARGEST FILES WITH 0% COVERAGE ===")
largest_zero = sorted(
    [
        (f, v)
        for f, v in files
        if v["summary"]["percent_covered"] == 0
        and not f.startswith("tests/")
        and v["summary"]["num_statements"] > 100
    ],
    key=lambda x: -x[1]["summary"]["num_statements"],
)[:15]

for f, d in largest_zero:
    print(f'  {f}: {int(d["summary"]["num_statements"])} lines')

print("\n=== FILES WITH LOW COVERAGE (<10%) ===")
low_cov = sorted(
    [
        (f, v["summary"]["percent_covered"], v["summary"]["num_statements"])
        for f, v in files
        if 0 < v["summary"]["percent_covered"] < 10
        and not f.startswith("tests/")
        and v["summary"]["num_statements"] > 100
    ],
    key=lambda x: -x[2],
)[:15]

for f, cov, lines in low_cov:
    print(f"  {f}: {cov:.1f}% ({lines} lines)")
