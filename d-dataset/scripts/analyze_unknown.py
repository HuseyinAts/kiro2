import json
from collections import Counter

data = []
with open('C:/Users/husey/kiro2/d-dataset/processed/vision_solve_sonnet/vision_results.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

print("="*70)
print("DERIN ANALIZ: UNKNOWN SOURCE (YENI COZULEN SORULAR)")
print("="*70)

# Unknown = DB'de cevabı olmayan sorular
unknown = [d for d in data if d.get('answer_source') == 'unknown']
print(f"\nToplam UNKNOWN: {len(unknown)} soru")

# Bunların current_answer durumu
has_current = [d for d in unknown if d.get('current_answer')]
no_current = [d for d in unknown if not d.get('current_answer')]
print(f"  current_answer VAR: {len(has_current)}")
print(f"  current_answer YOK: {len(no_current)}")

# AI cevap dağılımı
ai_answers = Counter(d.get('ai_answer') for d in unknown)
print(f"\nAI CEVAP DAGILIMI (unknown):")
total_ai = sum(1 for d in unknown if d.get('ai_answer'))
for ans, cnt in ai_answers.most_common():
    if ans:
        print(f"  {ans}: {cnt} ({100*cnt/total_ai:.1f}%)")

# Confidence dağılımı
conf_high = sum(1 for d in unknown if d.get('confidence', 0) >= 0.9)
conf_med = sum(1 for d in unknown if 0.7 <= d.get('confidence', 0) < 0.9)
conf_low = sum(1 for d in unknown if d.get('confidence', 0) < 0.7)
print(f"\nCONFIDENCE DAGILIMI:")
print(f"  high (>=0.9): {conf_high} ({100*conf_high/len(unknown):.1f}%)")
print(f"  med (0.7-0.9): {conf_med} ({100*conf_med/len(unknown):.1f}%)")
print(f"  low (<0.7): {conf_low} ({100*conf_low/len(unknown):.1f}%)")

# Hata durumu
errors = [d for d in unknown if d.get('error')]
no_errors = [d for d in unknown if not d.get('error')]
print(f"\nHATA DURUMU:")
print(f"  Error yok (basarili): {len(no_errors)} ({100*len(no_errors)/len(unknown):.1f}%)")
print(f"  Error var: {len(errors)}")

# Ornek sorular
print(f"\nORNEK SORULAR (unknown):")
for d in unknown[:5]:
    err = d.get('error', '')
    if err:
        err = f"ERROR: {err[:30]}"
    print(f"  {d['book_name'][:35]} p{d['page_number']} q{d['question_number']} | AI:{d['ai_answer']} conf:{d['confidence']} {err}")

print("\n" + "="*70)
print("KARSILASTIRMA: DB CEVABI OLAN vs OLMAYAN")
print("="*70)

# DB cevabı olanlar
db_sources = [d for d in data if d.get('answer_source') in ['db_v7', 'jsonl_v11']]
print(f"\nDB CEVABI OLAN: {len(db_sources)} soru")

# Bunların confidence dağılımı
db_conf_high = sum(1 for d in db_sources if d.get('confidence', 0) >= 0.9)
db_conf_med = sum(1 for d in db_sources if 0.7 <= d.get('confidence', 0) < 0.9)
db_conf_low = sum(1 for d in db_sources if d.get('confidence', 0) < 0.7)
print(f"  high (>=0.9): {db_conf_high} ({100*db_conf_high/len(db_sources):.1f}%)")
print(f"  med (0.7-0.9): {db_conf_med} ({100*db_conf_med/len(db_sources):.1f}%)")
print(f"  low (<0.7): {db_conf_low} ({100*db_conf_low/len(db_sources):.1f}%)")

# Sonuç
print("\n" + "="*70)
print("SONUC")
print("="*70)
print(f"""
1. AI {len(data)} soru islemlis
2. Bunlardan {len(unknown)} ({100*len(unknown)/len(data):.1f}%) YENI (DB'de cevap yok)
3. {len(db_sources)} ({100*len(db_sources)/len(data):.1f}%) icin DB karsilastirmasi yapilabilir
4. DB ile eslesen: 150 ({100*150/len(db_sources):.1f}%)
5. DB ile eslesmeyen ama YENI soru olarak eklenebilir: {len(no_errors)} ({100*len(no_errors)/len(unknown):.1f}%)
""")
