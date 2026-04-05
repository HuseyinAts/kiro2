# -*- coding: utf-8 -*-
"""
KIRO2 PostgreSQL Import - psycopg2 ile doğrudan yükleme
"""
import json
import uuid
import sys

print("=" * 60)
print("  KIRO2 SORU IMPORT - 36,967 Soru")
print("=" * 60)

# psycopg2 import
try:
    import psycopg2
    from psycopg2.extras import execute_values
    print("[OK] psycopg2 yuklendi")
except ImportError:
    print("[!] psycopg2 yukleniyor...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
    import psycopg2
    from psycopg2.extras import execute_values

# Ayarlar
JSONL_PATH = r"C:\Users\husey\kiro2\d-dataset\eslesmis_sorucevap.jsonl"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'kiro2',
    'user': 'postgres',
    'password': '1470'
}

def detect_subject(book_name):
    book_lower = book_name.lower()
    mapping = [
        ('matematik', 'MAT', 'Matematik'),
        ('geometri', 'GEO', 'Geometri'),
        ('fizik', 'FIZ', 'Fizik'),
        ('kimya', 'KIM', 'Kimya'),
        ('biyoloji', 'BIO', 'Biyoloji'),
        ('turkce', 'TUR', 'Turkce'),
        ('edebiyat', 'EDB', 'Edebiyat'),
        ('tarih', 'TAR', 'Tarih'),
        ('cografya', 'COG', 'Cografya'),
        ('paragraf', 'PAR', 'Paragraf'),
    ]
    for key, code, name in mapping:
        if key in book_lower:
            return code, name
    return 'GEN', 'Genel'

def main():
    # 1. Veritabanına bağlan
    print("\n[1/5] Veritabanina baglaniliyor...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cur = conn.cursor()
        print("      Baglanti basarili!")
    except Exception as e:
        print(f"      HATA: {e}")
        return
    
    # 2. Mevcut durum
    print("\n[2/5] Mevcut durum kontrol ediliyor...")
    cur.execute("SELECT COUNT(*) FROM question_bank")
    count_before = cur.fetchone()[0]
    print(f"      Mevcut soru sayisi: {count_before}")
    
    # 3. Topic'leri oluştur ve ID'lerini al
    print("\n[3/5] Topic'ler olusturuluyor...")
    topics = [
        ('MAT', 'Matematik'), ('GEO', 'Geometri'), ('FIZ', 'Fizik'),
        ('KIM', 'Kimya'), ('BIO', 'Biyoloji'), ('TUR', 'Turkce'),
        ('EDB', 'Edebiyat'), ('TAR', 'Tarih'), ('COG', 'Cografya'),
        ('PAR', 'Paragraf'), ('GEN', 'Genel')
    ]
    
    topic_ids = {}
    for code, name in topics:
        cur.execute("""
            INSERT INTO topic_hierarchy (id, level, code, name_tr, meb_code, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), 1, %s, %s, %s, true, NOW(), NOW())
            ON CONFLICT (code) DO UPDATE SET name_tr = EXCLUDED.name_tr
            RETURNING id
        """, (code, name, code))
        result = cur.fetchone()
        if result:
            topic_ids[code] = result[0]
    conn.commit()
    
    # Eksik topic ID'leri al
    cur.execute("SELECT code, id FROM topic_hierarchy")
    for row in cur.fetchall():
        topic_ids[row[0]] = row[1]
    print(f"      {len(topic_ids)} topic hazir")
    
    # 4. JSONL oku
    print(f"\n[4/5] JSONL okunuyor...")
    print(f"      Dosya: {JSONL_PATH}")
    questions = []
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                questions.append(json.loads(line))
            except:
                pass
    print(f"      {len(questions)} soru yuklendi")
    
    # 5. Soruları ekle
    print("\n[5/5] Sorular ekleniyor...")
    
    insert_sql = """
        INSERT INTO question_bank (
            id, question_text, option_a, option_b, option_c, option_d, option_e,
            correct_answer, primary_topic_id, exam_type, subject_area, grade_level,
            difficulty_level, is_active, is_public, quality_score, created_at, updated_at
        ) VALUES %s
        ON CONFLICT (id) DO NOTHING
    """
    
    batch = []
    inserted = 0
    batch_size = 500
    
    for i, q in enumerate(questions):
        book_name = q.get('book_name', '')
        subject_code, subject_name = detect_subject(book_name)
        exam_type = 'AYT' if 'ayt' in book_name.lower() else 'TYT'
        
        topic_id = topic_ids.get(subject_code, topic_ids.get('GEN'))
        options = q.get('options', {})
        
        data = (
            str(uuid.uuid4()),                              # id
            str(q.get('text', ''))[:5000],                  # question_text
            str(options.get('A', ''))[:1000],               # option_a
            str(options.get('B', ''))[:1000],               # option_b
            str(options.get('C', ''))[:1000],               # option_c
            str(options.get('D', ''))[:1000],               # option_d
            str(options.get('E', ''))[:1000] if 'E' in options else None,  # option_e
            q.get('answer', 'A'),                           # correct_answer
            topic_id,                                        # primary_topic_id
            exam_type,                                       # exam_type
            subject_name,                                    # subject_area
            11,                                              # grade_level
            'medium',                                        # difficulty_level
            True,                                            # is_active
            True,                                            # is_public
            float(q.get('quality_score', 0) or 0),          # quality_score
            'NOW()',                                         # created_at (placeholder)
            'NOW()'                                          # updated_at (placeholder)
        )
        batch.append(data)
        
        if len(batch) >= batch_size:
            try:
                execute_values(cur, insert_sql, batch, template="""(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s::question_difficulty_level, %s, %s, %s, NOW(), NOW()
                )""")
                conn.commit()
                inserted += len(batch)
            except Exception as e:
                print(f"      Batch hatasi: {str(e)[:100]}")
                conn.rollback()
            batch = []
            
            if (i + 1) % 5000 == 0:
                print(f"      Ilerleme: {i+1}/{len(questions)} ({100*(i+1)/len(questions):.0f}%)")
    
    # Kalan batch
    if batch:
        try:
            execute_values(cur, insert_sql, batch, template="""(
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s::question_difficulty_level, %s, %s, %s, NOW(), NOW()
            )""")
            conn.commit()
            inserted += len(batch)
        except Exception as e:
            print(f"      Son batch hatasi: {str(e)[:100]}")
    
    # Sonuç
    cur.execute("SELECT COUNT(*) FROM question_bank")
    count_after = cur.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("  IMPORT TAMAMLANDI!")
    print("=" * 60)
    print(f"  Onceki soru sayisi : {count_before}")
    print(f"  Yeni soru sayisi   : {count_after}")
    print(f"  Eklenen            : {count_after - count_before}")
    print("=" * 60)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
