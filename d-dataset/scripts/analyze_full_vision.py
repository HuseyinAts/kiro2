import json
from pathlib import Path
from collections import Counter

BASE = Path('C:/Users/husey/kiro2/d-dataset/processed')

# 1. Load ALL vision results
print("="*70)
print("TAM KAPSAMLI VISION SONUCLARI")
print("="*70)

all_vision = {}

# Opus v1
opus_v1 = BASE / 'vision_solve_opus' / 'vision_results.jsonl'
if opus_v1.exists():
    data = {}
    with open(opus_v1, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                key = (d['book_name'], d['page_number'], d['question_number'])
                data[key] = d
    print(f"Opus v1: {len(data):,} soru")
    all_vision['opus_v1'] = data

# Opus v2
opus_v2 = BASE / 'vision_solve_opus_v2' / 'vision_results.jsonl'
if opus_v2.exists():
    data = {}
    with open(opus_v2, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                key = (d['book_name'], d['page_number'], d['question_number'])
                data[key] = d
    print(f"Opus v2: {len(data):,} soru")
    all_vision['opus_v2'] = data

# Sonnet
sonnet = BASE / 'vision_solve_sonnet' / 'vision_results.jsonl'
if sonnet.exists():
    data = {}
    with open(sonnet, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                key = (d['book_name'], d['page_number'], d['question_number'])
                data[key] = d
    print(f"Sonnet: {len(data):,} soru")
    all_vision['sonnet'] = data

# Gemini
gemini = BASE / 'vision_solve_gemini' / 'vision_results_clean.jsonl'
if gemini.exists():
    data = {}
    with open(gemini, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                key = (d['book_name'], d['page_number'], d['question_number'])
                data[key] = d
    print(f"Gemini: {len(data):,} soru")
    all_vision['gemini'] = data

# Merge all (prioritize: Sonnet > Opus v2 > Opus v1 > Gemini)
merged = {}
priority = ['sonnet', 'opus_v2', 'opus_v1', 'gemini']

for source in priority:
    if source in all_vision:
        for key, val in all_vision[source].items():
            if key not in merged:
                merged[key] = val
                val['source'] = source

print(f"\nTOPLAM BIRLESTIRILMIS: {len(merged):,} unik soru")

# Check how many have valid answers
valid_answers = sum(1 for v in merged.values() if v.get('ai_answer') and v.get('ai_answer') in 'ABCDE')
print(f"Gecerli AI cevabi: {valid_answers:,}")

# By source breakdown
source_count = Counter(v.get('source') for v in merged.values())
print("\nKAYNAK DAGILIMI:")
for src, cnt in source_count.most_common():
    valid = sum(1 for v in merged.values() if v.get('source') == src and v.get('ai_answer') in 'ABCDE')
    print(f"  {src}: {cnt:,} toplam, {valid:,} gecerli")

# Check errors
errors = Counter(v.get('error') for v in merged.values() if v.get('error'))
print("\nHATA DAGILIMI:")
for err, cnt in errors.most_common(5):
    print(f"  {err[:50]}: {cnt:,}")

print("\n" + "="*70)
print("KRITIK BULGU: SONNET DAHIL EDILMEMIS!")
print("="*70)
print(f"""
Mevcut cross-validation sadece Opus yukluyor:
  - Opus v1: 1,300
  - Opus v2: 10,525
  - Toplam: 11,825

Ama bunlar DAHIL DEGIL:
  - Sonnet: 4,254 soru (TAMAMEN EKSIK!)
  - Gemini: 8,423 soru (TAMAMEN EKSIK!)

EKSIK: {4,254 + 8,423:,} soru!
""")
