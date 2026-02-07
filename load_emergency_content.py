#!/usr/bin/env python3
"""
KIRO2 Acil İçerik Yükleme Scripti
=================================
50 adet YKS sorusunu veritabanına yükler
"""

import psycopg2
from psycopg2 import sql
import sys
import os
from datetime import datetime
import uuid
import hashlib

# Backend path'i ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Veritabanı bağlantı bilgileri
DB_CONFIG = {
    'host': 'localhost',
    'database': 'kiro2',
    'user': 'postgres',
    'password': 'postgres',  # PostgreSQL şifrenizi buraya girin
    'port': 5432
}

def test_connection():
    """Veritabanı bağlantısını test et"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"✅ PostgreSQL bağlantısı başarılı!")
        print(f"   Versiyon: {version[:50]}...")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return False

def create_tables():
    """Tabloları oluştur (eğer yoksa)"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Questions tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                question_text TEXT NOT NULL,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                option_e TEXT,
                correct_answer VARCHAR(1) NOT NULL,
                explanation TEXT,
                exam_type VARCHAR(10),
                subject_area VARCHAR(50),
                topic VARCHAR(100),
                subtopic VARCHAR(100),
                difficulty VARCHAR(20),
                irt_difficulty FLOAT DEFAULT 0.0,
                irt_discrimination FLOAT DEFAULT 1.2,
                irt_guessing FLOAT DEFAULT 0.25,
                morphology_complexity FLOAT,
                readability_score FLOAT,
                image_url TEXT,
                source VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Users tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE,
                password_hash TEXT NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                role VARCHAR(20) DEFAULT 'student',
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # İndeksler
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_questions_exam_type ON questions(exam_type);
            CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject_area);
            CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
            CREATE INDEX IF NOT EXISTS idx_questions_active ON questions(is_active);
        """)
        
        conn.commit()
        print("✅ Tablolar kontrol edildi/oluşturuldu")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Tablo oluşturma hatası: {e}")
        return False

def check_existing_questions():
    """Mevcut soru sayısını kontrol et"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM questions")
        count = cur.fetchone()[0]
        
        if count > 0:
            cur.execute("""
                SELECT exam_type, COUNT(*) 
                FROM questions 
                GROUP BY exam_type
            """)
            distribution = cur.fetchall()
            
            print(f"\n📊 Mevcut Durum:")
            print(f"   Toplam soru: {count}")
            for exam, cnt in distribution:
                print(f"   {exam}: {cnt} soru")
        else:
            print(f"\n📊 Veritabanı boş, soru yok")
        
        conn.close()
        return count
    except Exception as e:
        print(f"⚠️ Soru kontrolü yapılamadı: {e}")
        return 0

def run_sql_file():
    """emergency_content.sql dosyasını çalıştır"""
    sql_file = os.path.join(os.path.dirname(__file__), 'emergency_content.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL dosyası bulunamadı: {sql_file}")
        return False
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"📄 SQL dosyası çalıştırılıyor: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            cur.execute(sql_content)
        
        conn.commit()
        print("✅ SQL dosyası başarıyla çalıştırıldı")
        
        # Sonuçları kontrol et
        cur.execute("SELECT COUNT(*) FROM questions")
        new_count = cur.fetchone()[0]
        print(f"📈 Toplam soru sayısı: {new_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ SQL çalıştırma hatası: {e}")
        return False

def create_admin_user():
    """Admin kullanıcı oluştur"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Admin var mı kontrol et
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cur.fetchone()[0]
        
        if admin_count == 0:
            # Basit hash (production'da bcrypt kullanın!)
            password = 'admin123'
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cur.execute("""
                INSERT INTO users (
                    email, username, password_hash, 
                    first_name, last_name, role, 
                    is_active, is_verified
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                'admin@kiro2.com', 'admin', password_hash,
                'Platform', 'Admin', 'admin',
                True, True
            ))
            
            conn.commit()
            print(f"✅ Admin kullanıcı oluşturuldu:")
            print(f"   Email: admin@kiro2.com")
            print(f"   Şifre: admin123")
        else:
            print(f"ℹ️ Admin kullanıcı zaten mevcut ({admin_count} adet)")
        
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ Admin kullanıcı oluşturulamadı: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 KIRO2 ACİL İÇERİK YÜKLEME")
    print("="*60)
    
    # 1. Bağlantı testi
    print("\n[1/5] Veritabanı Bağlantısı Test Ediliyor...")
    if not test_connection():
        print("\n❌ Veritabanına bağlanılamadı!")
        print("\n🔧 Çözüm önerileri:")
        print("1. PostgreSQL servisinin çalıştığından emin olun")
        print("2. DB_CONFIG içindeki şifreyi kontrol edin")
        print("3. 'kiro2' veritabanının oluşturulduğundan emin olun:")
        print("   psql -U postgres -c \"CREATE DATABASE kiro2;\"")
        return
    
    # 2. Tablolar
    print("\n[2/5] Tablolar Kontrol Ediliyor...")
    if not create_tables():
        return
    
    # 3. Mevcut durum
    print("\n[3/5] Mevcut İçerik Kontrol Ediliyor...")
    existing = check_existing_questions()
    
    # 4. SQL yükle
    if existing < 50:
        print("\n[4/5] İçerik Yükleniyor...")
        if run_sql_file():
            print("✅ İçerik başarıyla yüklendi!")
    else:
        print(f"ℹ️ Yeterli içerik mevcut ({existing} soru), ekleme yapılmadı")
    
    # 5. Admin kullanıcı
    print("\n[5/5] Admin Kullanıcı Kontrol Ediliyor...")
    create_admin_user()
    
    # Final durum
    print("\n" + "="*60)
    print("📊 ÖZET RAPOR")
    print("="*60)
    
    final_count = check_existing_questions()
    
    if final_count >= 50:
        print("\n✅ Platform test için hazır!")
        print("🎯 Sonraki adımlar:")
        print("   1. Backend sunucusunu başlatın:")
        print("      cd backend && uvicorn main:app --reload")
        print("   2. Frontend'i başlatın:")
        print("      cd frontend && npm start")
        print("   3. Admin panele giriş yapın:")
        print("      http://localhost:3000/admin")
        print("      Email: admin@kiro2.com")
        print("      Şifre: admin123")
    else:
        print("\n⚠️ Daha fazla içerik eklenmeli")
        print("🔧 Öneriler:")
        print("   1. ÖSYM PDF'lerden soru çıkarın:")
        print("      cd backend/scripts")
        print("      python osym_question_extractor.py")
        print("   2. AI ile soru üretin")
        print("   3. Manuel soru ekleyin")
    
    print("\n" + "="*60)
    print("✨ İşlem tamamlandı!")
    print("="*60)

if __name__ == "__main__":
    main()
