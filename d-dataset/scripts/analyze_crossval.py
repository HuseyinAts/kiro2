import json

# Load production data
production = []
with open('C:/Users/husey/kiro2/d-dataset/processed/eslesmis_sorucevap_rematched_v2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            production.append(json.loads(line))

print("="*70)
print("ADIM ADIM CROSS-VALIDATION ANALIZI")
print("="*70)

print(f"\n1. TOPLAM SORU: {len(production):,}")

# Check answer_source distribution
from collections import Counter
sources = Counter(p.get('answer_source', 'unknown') for p in production)
print("\n2. ANSWER_SOURCE DAGILIMI:")
for src, cnt in sources.most_common():
    pct = 100 * cnt / len(production)
    print(f"   {src}: {cnt:,} ({pct:.1f}%)")

# Check has_answer
has_answer = sum(1 for p in production if p.get('answer'))
print(f"\n3. CEVABI OLAN: {has_answer:,} ({100*has_answer/len(production):.1f}%)")

# AI coverage
has_ai = sum(1 for p in production if p.get('ai_answer'))
print(f"   AI CEVABI OLAN: {has_ai:,} ({100*has_ai/len(production):.1f}%)")

# Check if there's original_answer vs answer
has_original = sum(1 for p in production if p.get('original_answer'))
print(f"\n4. ORIGINAL ANSWER OLAN: {has_original:,}")

# Changed from original
if has_original > 0:
    changed = sum(1 for p in production if p.get('original_answer') != p.get('answer'))
    print(f"   DEGISEN: {changed:,} ({100*changed/has_original:.1f}%)")
    print(f"   DEGISMEYEN: {has_original-changed:,} ({100*(has_original-changed)/has_original:.1f}%)")

# Answer distribution
answers = Counter(p.get('answer') for p in production if p.get('answer'))
print("\n5. CEVAP DAGILIMI:")
total_ans = sum(answers.values())
for ans in ['A', 'B', 'C', 'D', 'E']:
    cnt = answers.get(ans, 0)
    pct = 100 * cnt / total_ans
    bar = "#" * int(pct / 2)
    print(f"   {ans}: {cnt:,} ({pct:5.1f}%) {bar}")

# Chi-square calculation
expected = total_ans / 5
chi_sq = sum((answers.get(ans, 0) - expected)**2 / expected for ans in ['A', 'B', 'C', 'D', 'E'])
print(f"\n   Chi-square: {chi_sq:.2f} (threshold: 9.49)")
print(f"   Sonuc: {'PASS' if chi_sq < 9.49 else 'FAIL'}")

# Check bayesian_posterior if exists
has_posterior = sum(1 for p in production if p.get('bayesian_posterior') is not None)
print(f"\n6. BAYESIAN POSTERIOR OLAN: {has_posterior:,} ({100*has_posterior/len(production):.1f}%)")

if has_posterior > 0:
    # Posterior distribution
    high = sum(1 for p in production if p.get('bayesian_posterior', 0) >= 0.9)
    med_high = sum(1 for p in production if 0.7 <= p.get('bayesian_posterior', 0) < 0.9)
    med = sum(1 for p in production if 0.5 <= p.get('bayesian_posterior', 0) < 0.7)
    low = sum(1 for p in production if p.get('bayesian_posterior', 0) < 0.5)

    print(f"   VERY HIGH (>=0.90): {high:,} ({100*high/has_posterior:.1f}%)")
    print(f"   HIGH (0.70-0.90): {med_high:,} ({100*med_high/has_posterior:.1f}%)")
    print(f"   MEDIUM (0.50-0.70): {med:,} ({100*med/has_posterior:.1f}%)")
    print(f"   LOW (<0.50): {low:,} ({100*low/has_posterior:.1f}%)")

# Check scoring_method
scoring = Counter(p.get('scoring_method', 'unknown') for p in production)
print("\n7. SKORLAMA YONTEMI:")
for method, cnt in scoring.most_common(10):
    pct = 100 * cnt / len(production)
    print(f"   {method}: {cnt:,} ({pct:.1f}%)")
