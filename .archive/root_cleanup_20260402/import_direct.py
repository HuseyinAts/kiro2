# -*- coding: utf-8 -*-
"""
KIRO2 Direkt Import Scripti
psycopg2 kullanarak senkron import yapar
"""

import json
import uuid
import sys
import os

# psycopg2 kontrol et
try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("psycopg2 yukleniyor...")
    os.system("pip install psycopg2-binary")
    import psycopg2
    from psycopg2.extras import execute_batch

# Ayarlar
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'kiro2',
    'user': 'postgres',
    'password': '1470'
}

JSONL_PATH = r"C:\Users\husey\kiro2\d-dataset\eslesmis_sorucevap.jsonl"

# Konu tespiti
SUBJECT_MAP = {
    'matematik': 'Matematik', 'geometri': 'Geometri', 'fizik': 'Fizik',
    'kimya': 'Kimya', 'biyoloji': 'Biyoloji', 'turkce': 'Turkce',
    'türkce': 'Turkce', 'edebiyat': 'Edebiyat', 'tarih': 'Tarih',
    'cografya': 'Cografya', 'paragraf': 'Paragraf'
}

SUBJECT_CODE = {
    'Matematik': 'MAT', 'Geometri': 'GEO', 'Fizik': 'FIZ', 'Kimya': 'KIM',
    'Biyoloji': 'BIO', 'Turkce': 'TUR', 'Edebiyat': 'EDB', 'Tarih': 'TAR',
    'Cografya': 'COG', 'Paragraf': 'PAR', 'Genel': 'GEN'
}

def detect_subject(book_name):
    book_lower = book_name.lower()
    for key, value in SUBJECT_MAP.items():
        if key in book_lower:
            return value
    return 'Genel'

def detect_exam_type(book_name):
    return 'AYT' if 'ayt' in book_name.lower() else 'TYT'

def main():
    print("=" * 50)
    print("  KIRO2 SORU IMPORT")
    print("=" * 50)
    
    # Veritabanı bağlantısı
    print("\n[1/5] Veritabanina baglaniliyor...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cur = conn.cursor()
        print("  OK - Baglanti basarili")
    except Exception as e:
        print(f"  HATA: {e}")
        return
    
    # Mevcut soru sayısı
    print("\n[2/5] Mevcut durum kontrol ediliyor...")
    cur.execute("SELECT COUNT(*) FROM question_bank")
    count_before = cur.fetchone()[0]
    print(f"  Mevcut soru sayisi: {count_before}")
    
    # Topic ID'lerini al
    print("\n[3/5] Topic ID'leri aliniyor...")
    topic_ids = {}
    cur.execute("SELECT code, id FROM topic_hierarchy")
    for row in cur.fetchall():
        topic_ids[row[0]] = row[1]
    print(f"  {len(topic_ids)} topic bulundu")
    
    # Eksik topic varsa oluştur
    for subject, code in SUBJECT_CODE.items():
        if code not in topic_ids:
            new_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO topic_hierarchy (id, level, code, name_tr, meb_code, is_active, created_at, updated_at)
                VALUES (%s, 1, %s, %s, %s, true, NOW(), NOW())
                ON CONFLICT (code) DO NOTHING
            """, (new_id, code, subject, code))
            topic_ids[code] = new_id
    conn.commit()
    
    # JSONL oku
    print(f"\n[4/5] JSONL okunuyor: {JSONL_PATH}")
    questions = []
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                questions.append(json.loads(line))
            except:
                pass
    print(f"  {len(questions)} soru yuklendi")
    
    # Import
    print("\n[5/5] Sorular ekleniyor...")
    inserted = 0
    skipped = 0
    batch_size = 1000
    
    insert_sql = """
        INSERT INTO question_bank (
            id, question_text, option_a, option_b, option_c, option_d, option_e,
            correct_answer, primary_topic_id, exam_type, subject_area, grade_level,
            quality_score, is_active, is_public, difficulty_level, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON CONFLICT DO NOTHING
    """
    
    batch_data = []
    
    for i, q in enumerate(questions):
        try:
            book_name = q.get('book_name', '')
            subject = detect_subject(book_name)
            exam_type = detect_exam_type(book_name)
            
            # Topic ID bul
            subject_code = SUBJECT_CODE.get(subject, 'GEN')
            topic_id = topic_ids.get(subject_code)
            
            if not topic_id:
                skipped += 1
                continue
            
            options = q.get('options', {})
            
            data = (
                str(uuid.uuid4()),
                str(q.get('text', ''))[:5000],
                str(options.get('A', ''))[:1000],
                str(options.get('B', ''))[:1000],
                str(options.get('C', ''))[:1000],
                str(options.get('D', ''))[:1000],
                str(options.get('E', ''))[:1000] if 'E' in options else None,
                q.get('answer', 'A'),
                topic_id,
                exam_type,
                subject,
                11,
                float(q.get('quality_score', 0) or 0),
                True,
                True,
                'medium'
            )
            
            batch_data.append(data)
            
            # Batch insert
            if len(batch_data) >= batch_size:
                execute_batch(cur, insert_sql, batch_data)
                conn.commit()
                inserted += len(batch_data)
                batch_data = []
                print(f"  Ilerleme: {i+1}/{len(questions)} ({100*(i+1)/len(questions):.1f}%)")
                
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  Hata: {str(e)[:100]}")
    
    # Kalan batch
    if batch_data:
        execute_batch(cur, insert_sql, batch_data)
        conn.commit()
        inserted += len(batch_data)
    
    # Sonuç
    cur.execute("SELECT COUNT(*) FROM question_bank")
    count_after = cur.fetchone()[0]
    
    print("\n" + "=" * 50)
    print("  IMPORT TAMAMLANDI!")
    print("=" * 50)
    print(f"  Eklenen soru   : {inserted}")
    print(f"  Atlanan soru   : {skipped}")
    print(f"  Onceki toplam  : {count_before}")
    print(f"  Yeni toplam    : {count_after}")
    print(f"  Net artis      : {count_after - count_before}")
    print("=" * 50)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
