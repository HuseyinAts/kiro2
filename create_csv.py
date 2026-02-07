import json
import uuid
import os

JSONL_PATH = r"C:\Users\husey\kiro2\d-dataset\eslesmis_sorucevap.jsonl"
CSV_PATH = r"C:\Users\husey\kiro2\kiro2_import.csv"

def detect_subject(book_name):
    book_lower = book_name.lower()
    for key, value in [('matematik', 'MAT'), ('geometri', 'GEO'), ('fizik', 'FIZ'),
                       ('kimya', 'KIM'), ('biyoloji', 'BIO'), ('turkce', 'TUR'),
                       ('edebiyat', 'EDB'), ('tarih', 'TAR'), ('cografya', 'COG'), 
                       ('paragraf', 'PAR')]:
        if key in book_lower:
            return value
    return 'GEN'

def clean_text(text):
    if not text:
        return ''
    return str(text).replace('\t', ' ').replace('\n', ' ').replace('\r', '').replace('\\', '\\\\')

print("JSONL okunuyor...")
questions = []
with open(JSONL_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            questions.append(json.loads(line))
        except:
            pass

print(f"{len(questions)} soru yuklendi")

print("CSV olusturuluyor...")
with open(CSV_PATH, 'w', encoding='utf-8') as f:
    for q in questions:
        options = q.get('options', {})
        book_name = q.get('book_name', '')
        subject_code = detect_subject(book_name)
        exam_type = 'AYT' if 'ayt' in book_name.lower() else 'TYT'
        
        row = [
            str(uuid.uuid4()),
            clean_text(q.get('text', ''))[:5000],
            clean_text(options.get('A', ''))[:1000],
            clean_text(options.get('B', ''))[:1000],
            clean_text(options.get('C', ''))[:1000],
            clean_text(options.get('D', ''))[:1000],
            clean_text(options.get('E', ''))[:1000] if 'E' in options else '',
            q.get('answer', 'A'),
            subject_code,
            exam_type,
            subject_code,
            '11',
            'medium',
            'true',
            'true',
            '0'
        ]
        f.write('\t'.join(row) + '\n')

size_mb = os.path.getsize(CSV_PATH) / (1024*1024)
print(f"CSV olusturuldu: {CSV_PATH}")
print(f"Boyut: {size_mb:.2f} MB")
