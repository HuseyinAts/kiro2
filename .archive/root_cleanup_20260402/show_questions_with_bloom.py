"""Show questions with updated Bloom levels"""
import sys
import io
import sqlite3
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

conn = sqlite3.connect('backend/kiro2.db')
cursor = conn.cursor()

# Get questions grouped by Bloom level
cursor.execute('''
    SELECT
        question_id,
        subject,
        topic,
        exam_type,
        quality_score,
        bloom_level,
        bloom_category,
        irt_difficulty,
        stem,
        key,
        distractors
    FROM osym_questions
    ORDER BY bloom_level DESC, question_id
''')

questions = cursor.fetchall()

print("=" * 120)
print("GÜNCELLENMİŞ BLOOM SEVİYELERİ İLE SORULAR")
print("=" * 120)
print()

# Group by Bloom level
bloom_groups = {}
for q in questions:
    bloom = q[5]
    if bloom not in bloom_groups:
        bloom_groups[bloom] = []
    bloom_groups[bloom].append(q)

bloom_names = {
    1: "Hatırlama",
    2: "Kavrama",
    3: "Uygulama",
    4: "Analiz",
    5: "Sentez",
    6: "Değerlendirme"
}

# Show questions by Bloom level
for bloom_level in sorted(bloom_groups.keys(), reverse=True):
    questions_in_level = bloom_groups[bloom_level]
    print()
    print("=" * 120)
    print(f"BLOOM SEVİYE {bloom_level}: {bloom_names[bloom_level].upper()} ({len(questions_in_level)} SORU)")
    print("=" * 120)
    print()

    for i, row in enumerate(questions_in_level, 1):
        q_id, subject, topic, exam_type, quality, bloom, bloom_cat, difficulty, stem, key, distractors_json = row

        # Parse distractors
        try:
            distractors = json.loads(distractors_json)
        except:
            distractors = []

        print(f"{i}. SORU: {q_id}")
        print("-" * 120)
        print(f"📚 Ders: {subject} | 📖 Konu: {topic} | 📝 Sınav: {exam_type}")
        print(f"⭐ Kalite: {quality:.1f}/100 | 🎯 Bloom: {bloom} ({bloom_cat}) | 📊 Zorluk: {difficulty:.2f}")
        print()
        print(f"SORU:")
        print(stem)
        print()
        print(f"✅ DOĞRU CEVAP: {key}")

        if distractors and len(distractors) > 0:
            print(f"❌ Çeldiriciler: {len(distractors)} adet")
        print()

conn.close()

# Summary statistics
print()
print("=" * 120)
print("İSTATİSTİKLER")
print("=" * 120)
print()

# Bloom distribution
print("Bloom Dağılımı:")
for bloom_level in sorted(bloom_groups.keys(), reverse=True):
    count = len(bloom_groups[bloom_level])
    pct = count / len(questions) * 100
    bar = '█' * int(pct / 5)
    print(f"  Seviye {bloom_level} ({bloom_names[bloom_level]:15s}): {count:2d} soru ({pct:5.1f}%) {bar}")

print()
print(f"Toplam: {len(questions)} soru")
