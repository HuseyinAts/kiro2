"""Verify questions in database"""
import sys
import io
import sqlite3

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

conn = sqlite3.connect('backend/kiro2.db')
cursor = conn.cursor()

# Get total count
cursor.execute('SELECT COUNT(*) FROM osym_questions')
total = cursor.fetchone()[0]
print(f"Total Questions in Database: {total}")
print("=" * 100)
print()

# Get sample questions
cursor.execute('''
    SELECT question_id, subject, topic, exam_type, quality_score, stem
    FROM osym_questions
    LIMIT 5
''')

print("Sample Questions:")
print("-" * 100)

for row in cursor.fetchall():
    q_id, subject, topic, exam_type, quality, stem = row
    stem_preview = stem[:80] + '...' if len(stem) > 80 else stem

    print(f"ID: {q_id}")
    print(f"   Subject: {subject} | Topic: {topic} | Exam: {exam_type} | Quality: {quality:.2f}")
    print(f"   Stem: {stem_preview}")
    print()

# Get statistics
cursor.execute('''
    SELECT
        subject,
        COUNT(*) as count,
        AVG(quality_score) as avg_quality
    FROM osym_questions
    GROUP BY subject
''')

print("=" * 100)
print("Statistics by Subject:")
print("-" * 100)

for row in cursor.fetchall():
    subject, count, avg_quality = row
    print(f"{subject:15s} | Count: {count:3d} | Avg Quality: {avg_quality:6.2f}")

conn.close()
