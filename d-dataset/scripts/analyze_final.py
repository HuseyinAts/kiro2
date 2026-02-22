import json
from collections import Counter

data = []
with open('C:/Users/husey/kiro2/d-dataset/processed/vision_solve_sonnet/vision_results.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

print("="*70)
print("DERIN ANALIZ: qnum BUG TESPITI")
print("="*70)

# answer_source = None olanlar = DB'de cevap yok
no_db = [d for d in data if d.get('answer_source') is None]
has_db = [d for d in data if d.get('answer_source') is not None]

print(f"\nVERI DAGILIMI:")
print(f"  DB'de cevap YOK (answer_source=None): {len(no_db)} ({100*len(no_db)/len(data):.1f}%)")
print(f"  DB'de cevap VAR: {len(has_db)} ({100*len(has_db)/len(data):.1f}%)")

# DB cevabı olanların match analizi
db_match = sum(1 for d in has_db if d.get('current_answer') == d.get('ai_answer') and d.get('ai_answer'))
print(f"\nDB ILE ESLESME (sadece answer_source != None):")
print(f"  Toplam: {len(has_db)}")
print(f"  Eslesen: {db_match} ({100*db_match/len(has_db):.1f}%)")
print(f"  Eslesmeyen: {len(has_db) - db_match}")

# qnum bug kanıtı - "cannot_solve" içinde
cannot_solve = [d for d in data if d.get('error') and 'numaralı soru' in str(d.get('error', ''))]
print(f"\n\nqnum BUG KANITI:")
print(f"  'cannot_solve' + 'numarali soru': {len(cannot_solve)}")

# Ornek qnum bug
print("\nORNEKLER:")
for d in cannot_solve[:5]:
    print(f"  {d['book_name'][:40]} p{d['page_number']} | AI q{d['question_number']} buldu ama: {d.get('error')[:60]}...")

# current_answer = None olanlar
no_current = [d for d in data if not d.get('current_answer')]
print(f"\n\ncurrent_answer = None: {len(no_current)}")

# Bunların answer_source'u
no_current_sources = Counter(d.get('answer_source') for d in no_current)
print("  Source dagilimi:")
for src, cnt in no_current_sources.most_common():
    print(f"    {src}: {cnt}")

# DB'de cevap olmadan AI cevabı olanlar (yeni sorular)
new_solved = [d for d in no_current if d.get('ai_answer') and not d.get('error')]
print(f"\n\nYENI COZULEN SORULAR (DB yok + AI cevap var + error yok):")
print(f"  Toplam: {len(new_solved)}")

# Bunların answer dağılımı
ai_ans_dist = Counter(d.get('ai_answer') for d in new_solved)
print("\n  AI cevap dagilimi:")
for ans, cnt in ai_ans_dist.most_common():
    if ans:
        print(f"    {ans}: {cnt} ({100*cnt/len(new_solved):.1f}%)")

# Confidence dağılımı
conf_high = sum(1 for d in new_solved if d.get('confidence', 0) >= 0.9)
conf_med = sum(1 for d in new_solved if 0.7 <= d.get('confidence', 0) < 0.9)
conf_low = sum(1 for d in new_solved if d.get('confidence', 0) < 0.7)
print(f"\n  Confidence:")
print(f"    high (>=0.9): {conf_high} ({100*conf_high/len(new_solved):.1f}%)")
print(f"    med (0.7-0.9): {conf_med} ({100*conf_med/len(new_solved):.1f}%)")
print(f"    low (<0.7): {conf_low} ({100*conf_low/len(new_solved):.1f}%)")

print("\n" + "="*70)
print("SONUC")
print("="*70)
print(f"""
1. AI {len(data)} soru islemlis
2. {len(no_db)} ({100*len(no_db)/len(data):.1f}%) icin DB'de cevap YOK
3. DB olan {len(has_db)} sorunun sadece {db_match} ({100*db_match/len(has_db):.1f}%) eslesti
4. {len(new_solved)} YENI SORU DB'ye eklenebilir (conf >= 0.7)
""")
