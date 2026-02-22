import json
from collections import Counter

data = []
with open('C:/Users/husey/kiro2/d-dataset/processed/vision_solve_sonnet/vision_results.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

print(f"Toplam: {len(data)} soru")

# Source breakdown
source_count = Counter(d.get('answer_source', 'unknown') for d in data)
print('\nSOURCE DAGILIMI:')
for src, cnt in source_count.most_common():
    print(f'  {src}: {cnt} ({100*cnt/len(data):.1f}%)')

# Match analysis
db_v7 = [d for d in data if d.get('answer_source') == 'db_v7']
jsonl = [d for d in data if d.get('answer_source') == 'jsonl_v11']

db_match = sum(1 for d in db_v7 if d.get('current_answer') == d.get('ai_answer'))
jsonl_match = sum(1 for d in jsonl if d.get('current_answer') == d.get('ai_answer'))

print(f'\nMATCH ORANI:')
print(f'  db_v7: {db_match}/{len(db_v7)} ({100*db_match/len(db_v7):.1f}%)')
print(f'  jsonl_v11: {jsonl_match}/{len(jsonl)} ({100*jsonl_match/len(jsonl):.1f}%)')
print(f'  TOPLAM: {db_match+jsonl_match}/{len(db_v7)+len(jsonl)} ({100*(db_match+jsonl_match)/(len(db_v7)+len(jsonl)):.1f}%)')

# Mismatch = AI yanlis cevap vermis
mismatches = [d for d in data if d.get('current_answer') and d.get('ai_answer') and d['current_answer'] != d['ai_answer']]
print(f'\nMISMATCH (AI yanlis): {len(mismatches)} soru')

# Yuksek confidence ama hala mismatch
high_conf_mismatch = [d for d in mismatches if d.get('confidence', 0) >= 0.9]
print(f'Yuksek confidence (>=0.9) ama yanlis: {len(high_conf_mismatch)}')

# Aynı kitap/sayfa içinde birden fazla qnum var mı?
book_page_qnums = {}
for d in data:
    key = (d['book_name'], d['page_number'])
    if key not in book_page_qnums:
        book_page_qnums[key] = []
    book_page_qnums[key].append(d['question_number'])

# Aynı sayfada birden fazla qnum olanlar
multi_q = {k: v for k, v in book_page_qnums.items() if len(v) > 1}
print(f'\nAyni sayfada birden fazla soru: {len(multi_q)} sayfa')

# Ornek
sample = list(multi_q.items())[:5]
print('\nORNEK (ayni sayfada birden fazla soru):')
for (book, page), qnums in sample:
    print(f'  {book[:40]} sayfa {page}: {sorted(qnums)}')

# Mismatch olanlarda qnum sırası kontrolü
print('\n\nMISMATCH DETAYLI ANALIZ:')
print('='*60)

# Aynı kitapta farklı sayfalardaki aynı qnum'lar
book_qnums = {}
for d in data:
    key = d['book_name']
    if key not in book_qnums:
        book_qnums[key] = []
    book_qnums[key].append((d['page_number'], d['question_number'], d.get('current_answer'), d.get('ai_answer'), d.get('confidence')))

# Her kitap için
for book, qlist in list(book_qnums.items())[:3]:
    print(f'\nKitap: {book[:50]}')
    # Sayfa sırasıyla
    for page, qnum, db_ans, ai_ans, conf in sorted(qlist)[:10]:
        match = 'OK' if db_ans == ai_ans else 'X'
        print(f'  p{page} q{qnum}: DB={db_ans} AI={ai_ans} {match}')
