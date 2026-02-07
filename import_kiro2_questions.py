#!/usr/bin/env python3
"""
KIRO2 Soru Veritabanı Import Scripti
36,967 soruyu PostgreSQL'e aktarır

Kullanım: python import_kiro2_questions.py
"""

import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path

# PostgreSQL bağlantısı için
import asyncpg

# Veritabanı ayarları
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "user": "postgres",
    "password": "1470",
    "database": "kiro2"
}

# Konu -> subject_area mapping
SUBJECT_MAPPING = {
    "Matematik": "matematik",
    "Geometri": "geometri",
    "Fizik": "fizik",
    "Kimya": "kimya",
    "Biyoloji": "biyoloji",
    "Edebiyat": "edebiyat",
    "Paragraf": "turkce",
    "Tarih": "tarih",
    "Türkçe": "turkce",
    "Coğrafya": "cografya",
    "Genel": "genel"
}

# Exam type mapping
EXAM_MAPPING = {
    "TYT": "TYT",
    "AYT": "AYT"
}


async def check_topic_exists(conn, topic_code: str) -> str:
    """Konu ID'sini kontrol et, yoksa default konu ID döndür"""
    result = await conn.fetchrow(
        "SELECT id FROM topic_hierarchy WHERE code = $1",
        topic_code
    )
    if result:
        return result['id']
    
    # Default topic_hierarchy kontrolü
    result = await conn.fetchrow(
        "SELECT id FROM topic_hierarchy LIMIT 1"
    )
    if result:
        return result['id']
    
    return None


async def create_default_topic(conn) -> str:
    """Varsayılan konu oluştur"""
    topic_id = str(uuid.uuid4())
    await conn.execute("""
        INSERT INTO topic_hierarchy (id, level, code, name_tr, is_active, created_at, updated_at)
        VALUES ($1, 1, 'GENEL', 'Genel', true, NOW(), NOW())
        ON CONFLICT (code) DO NOTHING
    """, topic_id)
    
    result = await conn.fetchrow("SELECT id FROM topic_hierarchy WHERE code = 'GENEL'")
    return result['id'] if result else topic_id


async def import_questions(input_file: str):
    """Soruları PostgreSQL'e aktar"""
    
    print(f"📂 Dosya okunuyor: {input_file}")
    
    # JSONL dosyasını oku
    questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            questions.append(json.loads(line))
    
    print(f"📊 Toplam {len(questions)} soru bulundu")
    
    # Veritabanına bağlan
    print(f"🔌 PostgreSQL'e bağlanılıyor...")
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        print("✅ Bağlantı başarılı!")
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return
    
    try:
        # Mevcut soru sayısını kontrol et
        existing_count = await conn.fetchval("SELECT COUNT(*) FROM question_bank")
        print(f"📊 Mevcut soru sayısı: {existing_count}")
        
        # Default topic ID al veya oluştur
        default_topic_id = await create_default_topic(conn)
        print(f"📁 Varsayılan konu ID: {default_topic_id}")
        
        # Batch insert için hazırlık
        inserted = 0
        skipped = 0
        errors = 0
        batch_size = 100
        
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i+batch_size]
            
            for q in batch:
                try:
                    question_id = str(uuid.uuid4())
                    
                    # Seçenekleri parse et
                    options = q.get('options', {})
                    option_a = options.get('A', '')
                    option_b = options.get('B', '')
                    option_c = options.get('C', '')
                    option_d = options.get('D', '')
                    option_e = options.get('E', None)
                    
                    # Subject area
                    subject = SUBJECT_MAPPING.get(q.get('subject', 'Genel'), 'genel')
                    
                    # Exam type
                    exam_type = q.get('exam_type', 'TYT')
                    
                    # Insert query
                    await conn.execute("""
                        INSERT INTO question_bank (
                            id, question_text, option_a, option_b, option_c, option_d, option_e,
                            correct_answer, primary_topic_id, exam_type, subject_area, grade_level,
                            quality_score, is_active, created_at, updated_at,
                            irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
                            difficulty_level
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7,
                            $8, $9, $10, $11, $12,
                            $13, $14, NOW(), NOW(),
                            $15, $16, $17, $18,
                            $19
                        )
                        ON CONFLICT DO NOTHING
                    """,
                        question_id,
                        q.get('stem', '')[:5000],  # question_text
                        str(option_a)[:2000] if option_a else '',
                        str(option_b)[:2000] if option_b else '',
                        str(option_c)[:2000] if option_c else '',
                        str(option_d)[:2000] if option_d else '',
                        str(option_e)[:2000] if option_e else None,
                        q.get('correct_option', 'A'),
                        default_topic_id,
                        exam_type,
                        subject,
                        11,  # grade_level (varsayılan 11. sınıf)
                        float(q.get('quality_score', 50)),
                        True,  # is_active
                        1.0,  # irt_discrimination
                        0.0,  # irt_difficulty
                        0.25,  # irt_guessing
                        1.0,  # irt_upper_asymptote
                        'medium'  # difficulty_level
                    )
                    inserted += 1
                    
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"⚠️ Hata (soru {i}): {e}")
            
            # Progress
            if (i + batch_size) % 1000 == 0 or i + batch_size >= len(questions):
                print(f"📈 İlerleme: {min(i + batch_size, len(questions))}/{len(questions)} ({inserted} eklendi, {errors} hata)")
        
        # Final count
        final_count = await conn.fetchval("SELECT COUNT(*) FROM question_bank")
        print(f"\n✅ Import tamamlandı!")
        print(f"📊 Toplam eklenen: {inserted}")
        print(f"📊 Hata: {errors}")
        print(f"📊 Veritabanındaki toplam soru: {final_count}")
        
    except Exception as e:
        print(f"❌ Import hatası: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await conn.close()
        print("🔌 Bağlantı kapatıldı")


async def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🚀 KIRO2 Soru Veritabanı Import")
    print("=" * 60)
    
    # Input dosyası
    input_file = Path(__file__).parent / "d-dataset" / "output" / "kiro2_questions.jsonl"
    
    # Alternatif konumlar
    alt_locations = [
        Path(__file__).parent / "kiro2_questions.jsonl",
        Path.home() / "Downloads" / "kiro2_questions.jsonl",
    ]
    
    if not input_file.exists():
        print(f"⚠️ Dosya bulunamadı: {input_file}")
        for alt in alt_locations:
            if alt.exists():
                input_file = alt
                print(f"✅ Alternatif dosya bulundu: {input_file}")
                break
    
    if not input_file.exists():
        print("❌ kiro2_questions.jsonl dosyası bulunamadı!")
        print("📁 Lütfen dosyayı şu konumlardan birine kopyalayın:")
        print(f"   - {Path(__file__).parent / 'd-dataset' / 'output' / 'kiro2_questions.jsonl'}")
        print(f"   - {Path(__file__).parent / 'kiro2_questions.jsonl'}")
        return
    
    await import_questions(str(input_file))


if __name__ == "__main__":
    asyncio.run(main())
