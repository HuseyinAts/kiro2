"""
Save questions directly to SQLite database using raw SQL
"""
import sys
import os
import io
import json
import sqlite3
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 80)
print(">>> DIRECT SQL - SAVE QUESTIONS TO DATABASE")
print("=" * 80)
print()

# Database path
DB_PATH = 'backend/kiro2.db'
print(f"Database: {DB_PATH}")

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if osym_questions table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='osym_questions'")
if cursor.fetchone():
    print("[OK] osym_questions table exists")
else:
    print("[ERROR] osym_questions table NOT found!")
    sys.exit(1)

# Get column names
cursor.execute("PRAGMA table_info(osym_questions)")
columns = cursor.fetchall()
print(f"[INFO] Table has {len(columns)} columns")
print()

# Find and load questions
possible_files = [
    'URETILEN_20_SORU.json',
    'claude45_gercek_sorular.json',
    'claude_uretilen_sorular.json'
]

json_file = None
for f in possible_files:
    if os.path.exists(f):
        json_file = f
        break

if not json_file:
    print("[ERROR] No question JSON files found")
    sys.exit(1)

print(f"[INFO] Loading from: {json_file}")

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Handle different JSON formats
if isinstance(data, list):
    questions = data
elif isinstance(data, dict):
    questions = data.get('questions', [])
else:
    questions = []

print(f"[OK] Loaded {len(questions)} questions")
print()

print("=" * 80)
print(">>> SAVING TO DATABASE")
print("=" * 80)
print()

saved_count = 0
skipped_count = 0
error_count = 0

for i, q in enumerate(questions, 1):
    try:
        # Generate unique question_id
        question_id = f"GEN{datetime.now().strftime('%Y%m%d')}{i:04d}"

        # Check if already exists
        cursor.execute("SELECT id FROM osym_questions WHERE question_id = ?", (question_id,))
        if cursor.fetchone():
            print(f"[{i}/{len(questions)}] SKIP - {question_id} already exists")
            skipped_count += 1
            continue

        # Extract data
        stem = q.get('stem', q.get('soru_metni', ''))

        # Handle options/distractors
        options = q.get('options', q.get('secenekler', []))
        correct_answer = q.get('correct_answer', q.get('dogru_cevap', q.get('key', 'A')))

        # Build distractors
        if isinstance(options, list) and len(options) >= 4:
            # Filter out correct answer from options to get distractors
            distractors = [opt for opt in options if opt != correct_answer]
        else:
            # Try to get from distractor_1, distractor_2, etc.
            distractors = []
            for j in range(1, 5):
                dist = q.get(f'distractor_{j}', q.get(f'celdirici_{j}', ''))
                if dist:
                    distractors.append(dist)

        # Convert distractors to JSON
        distractors_json = json.dumps(distractors, ensure_ascii=False)

        # Get metadata
        exam_type = q.get('exam_type', q.get('sinav_turu', 'TYT'))
        subject = q.get('subject', q.get('ders', 'Matematik'))
        topic = q.get('topic', q.get('konu', 'Genel'))
        subtopic = q.get('subtopic', q.get('alt_konu', ''))

        # Get difficulty and quality scores
        difficulty = q.get('difficulty', q.get('zorluk', 0.5))
        quality_score = q.get('quality_score_total', q.get('quality_score', q.get('kalite_skoru', 0.85))) * 100

        # Bloom level
        bloom_level = q.get('bloom_level', q.get('bloom_seviyesi', 2))

        # Insert into database
        sql = """
        INSERT INTO osym_questions (
            question_id, stem, key, distractors,
            year, exam_type, subject, topic, subtopic,
            bloom_level, bloom_category, bloom_confidence,
            irt_difficulty, irt_discrimination, irt_guessing, irt_calibrated,
            quality_score, status,
            has_image, has_formula,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            question_id,
            stem,
            correct_answer[0] if correct_answer else 'A',  # First char only
            distractors_json,
            2025,  # year
            exam_type,
            subject,
            topic,
            subtopic or '',
            bloom_level,
            q.get('bloom_category', 'kavrama'),
            0.8,  # bloom_confidence
            difficulty,
            1.0,  # irt_discrimination
            0.25,  # irt_guessing
            0,  # irt_calibrated (False)
            quality_score,
            'approved',
            0,  # has_image
            0,  # has_formula
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        )

        cursor.execute(sql, values)
        conn.commit()

        print(f"[{i}/{len(questions)}] SAVED - {question_id}")
        saved_count += 1

    except Exception as e:
        print(f"[{i}/{len(questions)}] ERROR - {str(e)[:80]}")
        error_count += 1
        conn.rollback()
        continue

conn.close()

print()
print("=" * 80)
print(">>> SUMMARY")
print("=" * 80)
print(f"Total questions:  {len(questions)}")
print(f"Saved:            {saved_count}")
print(f"Skipped:          {skipped_count}")
print(f"Errors:           {error_count}")
print()

if saved_count > 0:
    print(f"[OK] {saved_count} questions successfully saved to database!")

    # Verify
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM osym_questions")
    total = cursor.fetchone()[0]
    conn.close()
    print(f"[INFO] Total questions in database: {total}")
else:
    print("[WARN] No questions were saved")

print("=" * 80)
