"""
Analyze extracted JSONs for answer coverage
"""
import glob
import json
import os

print("Analyzing all extracted JSONs for answer coverage...")
print("=" * 80)

results = []
for json_path in sorted(glob.glob("osym_extracted/*.json")):
    filename = os.path.basename(json_path)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    total = len(data["questions"])
    with_answers = sum(1 for q in data["questions"] if q.get("correct_answer"))
    coverage = (with_answers / total * 100) if total > 0 else 0

    # Count Matematik questions
    matematik = [q for q in data["questions"] if q.get("subject") == "Matematik"]
    mat_total = len(matematik)
    mat_answered = sum(1 for q in matematik if q.get("correct_answer"))

    results.append(
        {
            "file": filename,
            "total": total,
            "answered": with_answers,
            "coverage": coverage,
            "mat_total": mat_total,
            "mat_answered": mat_answered,
        }
    )

# Print summary
print(
    f"{'File':<50} {'Total':<8} {'Answered':<10} {'Coverage':<10} {'Mat Total':<12} {'Mat Ans'}"
)
print("-" * 105)

total_questions = 0
total_answered = 0
total_mat = 0
total_mat_ans = 0

for r in results:
    status = (
        "[OK]" if r["coverage"] > 50 else "[LOW]" if r["coverage"] > 0 else "[NONE]"
    )
    print(
        f"{r['file']:<50} {r['total']:<8} {r['answered']:<10} {r['coverage']:<9.1f}% {r['mat_total']:<12} {r['mat_answered']} {status}"
    )
    total_questions += r["total"]
    total_answered += r["answered"]
    total_mat += r["mat_total"]
    total_mat_ans += r["mat_answered"]

print("-" * 105)
print("\nSUMMARY:")
print(f"Total Questions: {total_questions}")
print(
    f"Total Answered: {total_answered} ({total_answered/total_questions*100 if total_questions > 0 else 0:.1f}%)"
)
print(f"\nMatematik Questions: {total_mat}")
print(
    f"Matematik Answered: {total_mat_ans} ({total_mat_ans/total_mat*100 if total_mat > 0 else 0:.1f}%)"
)

# Show files with 100% coverage (these extracted answer keys successfully)
print(f"\n{'='*80}")
print("FILES WITH SUCCESSFUL ANSWER KEY EXTRACTION (100% coverage):")
print("-" * 80)
for r in results:
    if r["coverage"] == 100:
        print(f"  [V] {r['file']} - {r['total']} questions")
