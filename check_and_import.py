"""
KIRO2 PostgreSQL Soru Import Scripti
36,967 soruyu question_bank tablosuna aktarır
"""

import asyncio
import json
import uuid
from datetime import datetime

try:
    import asyncpg
except ImportError:
    print("asyncpg yükleniyor...")
    import subprocess
    subprocess.run(["pip", "install", "asyncpg"])
    import asyncpg

# Veritabanı ayarları
DATABASE_URL = "postgresql://postgres:1470@localhost:5434/kiro2"
JSONL_PATH = r"C:\Users\husey\kiro2\d-dataset\eslesmis_sorucevap.jsonl"

# Konu haritalama
SUBJECT_MAP = {
    "matematik": "Matematik",
    "geometri": "Geometri", 
    "fizik": "Fizik",
    "kimya": "Kimya",
    "biyoloji": "Biyoloji",
    "turkce": "Türkçe",
    "türkce": "Türkçe",
    "edebiyat": "Edebiyat",
    "tarih": "Tarih",
    "cografya": "Coğrafya",
    "paragraf": "Paragraf",
}

SUBJECT_TOPIC_MAP = {
    "Matematik": {"code": "MAT", "name_tr": "Matematik"},
    "Geometri": {"code": "GEO", "name_tr": "Geometri"},
    "Fizik": {"code": "FIZ", "name_tr": "Fizik"},
    "Kimya": {"code": "KIM", "name_tr": "Kimya"},
    "Biyoloji": {"code": "BIO", "name_tr": "Biyoloji"},
    "Türkçe": {"code": "TUR", "name_tr": "Türkçe"},
    "Edebiyat": {"code": "EDB", "name_tr": "Edebiyat"},
    "Tarih": {"code": "TAR", "name_tr": "Tarih"},
    "Coğrafya": {"code": "COG", "name_tr": "Coğrafya"},
    "Paragraf": {"code": "PAR", "name_tr": "Paragraf"},
    "Genel": {"code": "GEN", "name_tr": "Genel"},
}

def detect_subject(book_name):
    """Kitap adından konu tespit et"""
    book_lower = book_name.lower()
    for key, value in SUBJECT_MAP.items():
        if key in book_lower:
            return value
    return "Genel"

def detect_exam_type(book_name):
    """Kitap adından sınav tipi tespit et"""
    book_lower = book_name.lower()
    if 'ayt' in book_lower:
        return 'AYT'
    return 'TYT'

async def check_database():
    """Veritabanı durumunu kontrol et"""
    print(f"🔗 Veritabanına bağlanılıyor...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Veritabanı bağlantısı başarılı!")
        
        # question_bank tablosu var mı?
        qb_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'question_bank'
            )
        """)
        
        if qb_exists:
            count = await conn.fetchval('SELECT COUNT(*) FROM question_bank')
            print(f"📊 question_bank tablosu mevcut, {count} soru var")
        else:
            print("⚠️ question_bank tablosu bulunamadı!")
            
        # topic_hierarchy tablosu var mı?
        th_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'topic_hierarchy'
            )
        """)
        
        if th_exists:
            count = await conn.fetchval('SELECT COUNT(*) FROM topic_hierarchy')
            print(f"📊 topic_hierarchy tablosu mevcut, {count} konu var")
        else:
            print("⚠️ topic_hierarchy tablosu bulunamadı!")
            
        await conn.close()
        return qb_exists and th_exists
        
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        return False

async def get_or_create_topic(conn, subject: str, topic_cache: dict) -> str:
    """Konu ID'sini al veya oluştur"""
    if subject in topic_cache:
        return topic_cache[subject]
        
    topic_info = SUBJECT_TOPIC_MAP.get(subject, SUBJECT_TOPIC_MAP["Genel"])
    
    # Mevcut konuyu kontrol et
    row = await conn.fetchrow(
        "SELECT id FROM topic_hierarchy WHERE code = $1",
        topic_info["code"]
    )
    
    if row:
        topic_cache[subject] = row["id"]
        return row["id"]
    
    # Yeni konu oluştur
    topic_id = str(uuid.uuid4())
    try:
        await conn.execute("""
            INSERT INTO topic_hierarchy (id, level, code, name_tr, meb_code, is_active, created_at, updated_at)
            VALUES ($1, 1, $2, $3, $4, true, NOW(), NOW())
        """, topic_id, topic_info["code"], topic_info["name_tr"], topic_info["code"])
        topic_cache[subject] = topic_id
    except Exception as e:
        # Conflict durumunda tekrar oku
        row = await conn.fetchrow("SELECT id FROM topic_hierarchy WHERE code = $1", topic_info["code"])
        if row:
            topic_cache[subject] = row["id"]
            return row["id"]
    
    return topic_id

async def import_questions():
    """JSONL dosyasından soruları import et"""
    
    print(f"\n🚀 KIRO2 Soru Import Başlatılıyor...")
    print(f"📁 Kaynak: {JSONL_PATH}")
    
    # Veritabanı kontrolü
    if not await check_database():
        print("\n❌ Veritabanı hazır değil. Lütfen tabloları oluşturun.")
        return
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Mevcut soru sayısı
        count_before = await conn.fetchval("SELECT COUNT(*) FROM question_bank")
        print(f"\n📊 Import öncesi soru sayısı: {count_before}")
        
        # JSONL dosyasını oku
        print(f"📖 JSONL dosyası okunuyor...")
        questions = []
        with open(JSONL_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    questions.append(json.loads(line))
                except:
                    pass
        
        print(f"📁 Toplam {len(questions)} soru yüklenecek")
        
        # Topic cache
        topic_cache = {}
        
        # Import
        inserted = 0
        skipped = 0
        errors = []
        
        for i, q in enumerate(questions):
            try:
                # Konu tespit et
                book_name = q.get('book_name', '')
                subject = detect_subject(book_name)
                exam_type = detect_exam_type(book_name)
                
                # Topic ID al
                topic_id = await get_or_create_topic(conn, subject, topic_cache)
                
                # Options parse et
                options = q.get('options', {})
                if not options:
                    options = {'A': '', 'B': '', 'C': '', 'D': ''}
                
                # Soru ID
                question_id = str(uuid.uuid4())
                
                # Insert
                await conn.execute("""
                    INSERT INTO question_bank (
                        id, question_text, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, primary_topic_id, exam_type, subject_area, grade_level,
                        quality_score, is_active, is_public, difficulty_level, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW(), NOW()
                    )
                """,
                    question_id,
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
                    'medium',
                )
                inserted += 1
                
            except Exception as e:
                skipped += 1
                if len(errors) < 5:
                    errors.append(str(e))
            
            # İlerleme
            if (i + 1) % 5000 == 0:
                print(f"  📥 İlerleme: {i+1}/{len(questions)} ({100*(i+1)/len(questions):.1f}%)")
        
        # Sonuç
        count_after = await conn.fetchval("SELECT COUNT(*) FROM question_bank")
        
        print(f"\n{'='*50}")
        print(f"✅ IMPORT TAMAMLANDI!")
        print(f"{'='*50}")
        print(f"📊 Eklenen soru: {inserted}")
        print(f"⚠️ Atlanan soru: {skipped}")
        print(f"📊 Toplam soru (önce): {count_before}")
        print(f"📊 Toplam soru (sonra): {count_after}")
        print(f"📊 Net artış: {count_after - count_before}")
        
        if errors:
            print(f"\n⚠️ İlk birkaç hata:")
            for e in errors[:3]:
                print(f"  - {e[:100]}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(import_questions())
