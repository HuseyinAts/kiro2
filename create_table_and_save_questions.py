"""
Create osym_questions table and save generated questions
"""
import sys
import os
import io
import json

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime
import glob

# Load environment
load_dotenv('backend/.env')

# Import models
from models.base import Base
from models.osym_question import OSYMQuestion

# Database connection - Use SQLite for simplicity
SQLITE_DB = 'backend/kiro2.db'
DATABASE_URL = f'sqlite:///{SQLITE_DB}'

print("=" * 80)
print(">>> OSYM QUESTIONS TABLE CREATION & DATA IMPORT")
print("=" * 80)
print(f"Database: {SQLITE_DB}")
print()

# Create engine
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

# Check if table exists
existing_tables = inspector.get_table_names()
print(f"[INFO] Existing tables: {len(existing_tables)}")

if 'osym_questions' in existing_tables:
    print("[OK] osym_questions table already exists")
else:
    print("[WARN] osym_questions table NOT found - creating...")

    # Debug: Show registered models
    print(f"[DEBUG] Base.metadata tables: {list(Base.metadata.tables.keys())}")

    # Create all tables from models
    Base.metadata.create_all(engine)
    print("[OK] Base.metadata.create_all() executed")

# Verify table creation - create NEW inspector to see updated state
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
print(f"[DEBUG] Tables after creation: {existing_tables}")

if 'osym_questions' in existing_tables:
    print("[OK] osym_questions table confirmed")

    # Get column info
    columns = inspector.get_columns('osym_questions')
    print(f"[INFO] Table has {len(columns)} columns:")
    for col in columns[:10]:  # Show first 10 columns
        print(f"       - {col['name']}: {col['type']}")
else:
    print("[ERROR] Table creation failed!")
    sys.exit(1)

print()
print("=" * 80)
print(">>> LOADING GENERATED QUESTIONS")
print("=" * 80)
print()

# Find question JSON files
possible_files = [
    'URETILEN_20_SORU.json',
    'claude45_gercek_sorular.json',
    'claude_uretilen_sorular.json',
    'openai_uretilen_sorular.json'
]

json_file = None
for f in possible_files:
    if os.path.exists(f):
        json_file = f
        break

if not json_file:
    # Try glob patterns
    patterns = ['50_questions_*.json', '*_questions_*.json']
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            json_file = matches[0]
            break

if not json_file:
    print("[ERROR] No question JSON files found")
    sys.exit(1)

print(f"[INFO] Loading from: {json_file}")

# Load questions
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

# Create session
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print(">>> SAVING QUESTIONS TO DATABASE")
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
        existing = session.query(OSYMQuestion).filter_by(question_id=question_id).first()
        if existing:
            print(f"[{i}/{len(questions)}] SKIP - {question_id} already exists")
            skipped_count += 1
            continue

        # Extract data from question dict
        stem = q.get('stem', '')

        # Handle options/distractors format
        options = q.get('options', [])
        correct_answer = q.get('correct_answer', q.get('key', 'A'))

        # Build distractors list
        if isinstance(options, list) and len(options) == 5:
            # Options are already in list format
            distractors = [opt for opt in options if opt != correct_answer]
        else:
            # Build from distractor_1, distractor_2, etc.
            distractors = []
            for j in range(1, 5):
                dist = q.get(f'distractor_{j}', '')
                if dist:
                    distractors.append(dist)

        # Create OSYMQuestion instance
        question = OSYMQuestion(
            question_id=question_id,
            stem=stem,
            key=correct_answer[0] if correct_answer else 'A',  # First char only
            distractors=distractors,

            # Metadata
            year=q.get('year', 2025),
            exam_type=q.get('exam_type', 'TYT'),
            subject=q.get('subject', 'Matematik'),
            topic=q.get('topic', 'Genel'),
            subtopic=q.get('subtopic', ''),

            # Bloom
            bloom_level=q.get('bloom_level', 2),
            bloom_category=q.get('bloom_category', 'kavrama'),
            bloom_confidence=q.get('bloom_confidence', 0.8),

            # IRT
            irt_difficulty=q.get('difficulty', 0.5),
            irt_discrimination=q.get('discrimination', 1.0),
            irt_guessing=q.get('guessing', 0.25),
            irt_calibrated=False,

            # Quality
            quality_score=q.get('quality_score_total', q.get('osym_compliance_score', 0.85)) * 100,

            # Status
            status='approved',  # Auto-approve generated questions

            # Visual
            has_image=q.get('has_image', False),
            has_formula=q.get('has_formula', False),

            # Timestamps
            created_at=datetime.utcnow(),
            generated_at=datetime.utcnow()
        )

        session.add(question)
        session.commit()

        print(f"[{i}/{len(questions)}] SAVED - {question_id}")
        saved_count += 1

    except Exception as e:
        print(f"[{i}/{len(questions)}] ERROR - {str(e)[:100]}")
        error_count += 1
        session.rollback()
        continue

session.close()

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
    print("[OK] Questions successfully saved to database!")
else:
    print("[WARN] No questions were saved")

print("=" * 80)
