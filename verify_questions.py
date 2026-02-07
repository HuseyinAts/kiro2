#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify loaded questions in SQLite database"""

import sqlite3
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('turkiye_sinav.db')
cursor = conn.cursor()

# Get total count
cursor.execute('SELECT COUNT(*) FROM questions')
total = cursor.fetchone()[0]
print(f'✅ Total questions loaded: {total}')

# Get distribution
cursor.execute('SELECT exam_type, COUNT(*) FROM questions GROUP BY exam_type')
print('\n📊 Distribution by exam type:')
for exam_type, count in cursor.fetchall():
    print(f'   {exam_type}: {count} questions')

# Show sample questions
print('\n📝 Sample questions:')
cursor.execute('SELECT question_text, correct_answer, exam_type FROM questions LIMIT 5')
for i, (question, answer, exam_type) in enumerate(cursor.fetchall(), 1):
    print(f'\n{i}. [{exam_type}] {question[:80]}...')
    print(f'   Correct Answer: {answer}')

conn.close()
print('\n✨ Verification complete!')