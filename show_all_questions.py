"""Show all questions from database"""
import sys
import io
import sqlite3
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

conn = sqlite3.connect('backend/kiro2.db')
cursor = conn.cursor()

# Get all questions
cursor.execute('''
    SELECT
        question_id,
        subject,
        topic,
        exam_type,
        quality_score,
        bloom_level,
        irt_difficulty,
        stem,
        key,
        distractors
    FROM osym_questions
    ORDER BY question_id
''')

questions = cursor.fetchall()

print("=" * 120)
print(f"VERİTABANINDA KAYITLI TÜM SORULAR ({len(questions)} SORU)")
print("=" * 120)
print()

for i, row in enumerate(questions, 1):
    q_id, subject, topic, exam_type, quality, bloom, difficulty, stem, key, distractors_json = row

    # Parse distractors
    try:
        distractors = json.loads(distractors_json)
    except:
        distractors = []

    print(f"SORU {i}: {q_id}")
    print("-" * 120)
    print(f"Ders: {subject} | Konu: {topic} | Sınav: {exam_type}")
    print(f"Kalite: {quality:.1f}/100 | Bloom: {bloom} | Zorluk: {difficulty:.2f}")
    print()
    print(f"SORU METNİ:")
    print(stem)
    print()
    print(f"DOĞRU CEVAP: {key}")
    print()

    if distractors:
        print(f"ÇELDİRİCİLER ({len(distractors)} adet):")
        for j, dist in enumerate(distractors, 1):
            print(f"  {j}. {dist}")

    print()
    print("=" * 120)
    print()

conn.close()

print(f"\nTOPLAM: {len(questions)} SORU VERİTABANINDA KAYITLI")
