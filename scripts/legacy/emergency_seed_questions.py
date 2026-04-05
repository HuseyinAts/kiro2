"""
KIRO2 - Emergency İçerik Yükleme Scripti
Bu script veritabanına acil olarak temel sorular yükler
"""

import psycopg2
from datetime import datetime
import uuid
import json

# Veritabanı bağlantı bilgileri
DB_CONFIG = {
    'host': 'localhost',
    'database': 'kiro2',
    'user': 'postgres',
    'password': 'postgres',  # Kendi şifrenizi güncelleyin
    'port': 5432
}

def create_tables():
    """Tabloları oluştur (eğer yoksa)"""
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
            difficulty VARCHAR(20),
            irt_difficulty FLOAT,
            irt_discrimination FLOAT,
            irt_guessing FLOAT DEFAULT 0.25,
            image_url TEXT,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    conn.close()
    print("✅ Tablolar kontrol edildi/oluşturuldu")

def seed_emergency_questions():
    """Acil soru seti yükle"""
    
    questions = [
        # TYT MATEMATİK
        {
            'question_text': 'Bir sayının %20\'si 40 ise, bu sayının %30\'u kaçtır?',
            'option_a': '50',
            'option_b': '60',
            'option_c': '70',
            'option_d': '80',
            'option_e': '90',
            'correct_answer': 'B',
            'explanation': 'Sayı x olsun. x\'in %20\'si = 40 ise x = 200. x\'in %30\'u = 200 × 0.3 = 60',
            'exam_type': 'TYT',
            'subject_area': 'Matematik',
            'topic': 'Yüzdeler',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.5
        },
        {
            'question_text': '2x + 3 = 11 denkleminin çözüm kümesi nedir?',
            'option_a': '{2}',
            'option_b': '{3}',
            'option_c': '{4}',
            'option_d': '{5}',
            'option_e': '{6}',
            'correct_answer': 'C',
            'explanation': '2x + 3 = 11 → 2x = 8 → x = 4',
            'exam_type': 'TYT',
            'subject_area': 'Matematik',
            'topic': 'Denklemler',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.8
        },
        {
            'question_text': 'Bir üçgenin iç açılarının toplamı kaç derecedir?',
            'option_a': '90°',
            'option_b': '180°',
            'option_c': '270°',
            'option_d': '360°',
            'option_e': '540°',
            'correct_answer': 'B',
            'explanation': 'Herhangi bir üçgenin iç açılarının toplamı her zaman 180 derecedir.',
            'exam_type': 'TYT',
            'subject_area': 'Matematik',
            'topic': 'Geometri',
            'difficulty': 'Çok Kolay',
            'irt_difficulty': -1.0
        },
        
        # TYT TÜRKÇE
        {
            'question_text': 'Aşağıdaki kelimelerden hangisi doğru yazılmıştır?',
            'option_a': 'yanlız',
            'option_b': 'yalnız',
            'option_c': 'yalnış',
            'option_d': 'yanlış',
            'option_e': 'yanlıs',
            'correct_answer': 'B',
            'explanation': 'Doğru yazım "yalnız" şeklindedir.',
            'exam_type': 'TYT',
            'subject_area': 'Türkçe',
            'topic': 'Yazım Kuralları',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.3
        },
        {
            'question_text': '"Gitmek" fiilinin geniş zamanının olumsuzu hangisidir?',
            'option_a': 'gitmem',
            'option_b': 'gitmiyor',
            'option_c': 'gitmez',
            'option_d': 'gitmeyecek',
            'option_e': 'gitmedi',
            'correct_answer': 'C',
            'explanation': 'Geniş zaman eki -r/-ar/-er/-ır ve olumsuzluk eki -mez/-maz birleşimi.',
            'exam_type': 'TYT',
            'subject_area': 'Türkçe',
            'topic': 'Fiil Çekimi',
            'difficulty': 'Orta',
            'irt_difficulty': 0.2
        },
        
        # TYT FEN
        {
            'question_text': 'Suyun kimyasal formülü nedir?',
            'option_a': 'H2O',
            'option_b': 'CO2',
            'option_c': 'O2',
            'option_d': 'H2',
            'option_e': 'OH',
            'correct_answer': 'A',
            'explanation': 'Su molekülü 2 hidrojen ve 1 oksijen atomundan oluşur: H2O',
            'exam_type': 'TYT',
            'subject_area': 'Fen',
            'topic': 'Kimya',
            'difficulty': 'Çok Kolay',
            'irt_difficulty': -1.5
        },
        {
            'question_text': 'Işığın boşluktaki hızı yaklaşık kaç km/s\'dir?',
            'option_a': '30.000',
            'option_b': '300.000',
            'option_c': '3.000.000',
            'option_d': '30',
            'option_e': '3.000',
            'correct_answer': 'B',
            'explanation': 'Işık hızı yaklaşık 300.000 km/s veya 3×10^8 m/s\'dir.',
            'exam_type': 'TYT',
            'subject_area': 'Fen',
            'topic': 'Fizik',
            'difficulty': 'Orta',
            'irt_difficulty': 0.0
        },
        
        # TYT SOSYAL
        {
            'question_text': 'Türkiye Cumhuriyeti\'nin başkenti neresidir?',
            'option_a': 'İstanbul',
            'option_b': 'İzmir',
            'option_c': 'Ankara',
            'option_d': 'Bursa',
            'option_e': 'Antalya',
            'correct_answer': 'C',
            'explanation': 'Türkiye Cumhuriyeti\'nin başkenti Ankara\'dır.',
            'exam_type': 'TYT',
            'subject_area': 'Sosyal',
            'topic': 'Coğrafya',
            'difficulty': 'Çok Kolay',
            'irt_difficulty': -2.0
        },
        {
            'question_text': 'Türkiye Cumhuriyeti hangi yıl kurulmuştur?',
            'option_a': '1920',
            'option_b': '1921',
            'option_c': '1922',
            'option_d': '1923',
            'option_e': '1924',
            'correct_answer': 'D',
            'explanation': 'Türkiye Cumhuriyeti 29 Ekim 1923\'te kurulmuştur.',
            'exam_type': 'TYT',
            'subject_area': 'Sosyal',
            'topic': 'Tarih',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.7
        },
        
        # AYT MATEMATİK
        {
            'question_text': 'lim(x→2) (x²-4)/(x-2) limitinin değeri kaçtır?',
            'option_a': '0',
            'option_b': '2',
            'option_c': '4',
            'option_d': '8',
            'option_e': 'Tanımsız',
            'correct_answer': 'C',
            'explanation': '(x²-4)/(x-2) = (x-2)(x+2)/(x-2) = x+2. x→2 için limit = 4',
            'exam_type': 'AYT',
            'subject_area': 'Matematik',
            'topic': 'Limit',
            'difficulty': 'Orta',
            'irt_difficulty': 0.3
        },
        {
            'question_text': 'f(x) = x³ fonksiyonunun türevi nedir?',
            'option_a': 'x²',
            'option_b': '2x²',
            'option_c': '3x²',
            'option_d': '3x³',
            'option_e': 'x³/3',
            'correct_answer': 'C',
            'explanation': 'f\'(x) = 3x²',
            'exam_type': 'AYT',
            'subject_area': 'Matematik',
            'topic': 'Türev',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.2
        },
        {
            'question_text': '∫x² dx integralinin sonucu nedir?',
            'option_a': 'x³ + C',
            'option_b': 'x³/3 + C',
            'option_c': '3x³ + C',
            'option_d': '2x + C',
            'option_e': 'x²/2 + C',
            'correct_answer': 'B',
            'explanation': '∫x² dx = x³/3 + C',
            'exam_type': 'AYT',
            'subject_area': 'Matematik',
            'topic': 'İntegral',
            'difficulty': 'Orta',
            'irt_difficulty': 0.1
        },
        
        # AYT FİZİK
        {
            'question_text': 'Newton\'un ikinci yasasına göre F = ?',
            'option_a': 'ma',
            'option_b': 'mv',
            'option_c': 'mg',
            'option_d': 'mv²',
            'option_e': 'mgh',
            'correct_answer': 'A',
            'explanation': 'Newton\'un ikinci yasası: F = m.a (Kuvvet = kütle × ivme)',
            'exam_type': 'AYT',
            'subject_area': 'Fizik',
            'topic': 'Dinamik',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.4
        },
        {
            'question_text': 'Kinetik enerji formülü nedir?',
            'option_a': 'mgh',
            'option_b': 'mv',
            'option_c': '1/2 mv²',
            'option_d': 'mv²',
            'option_e': 'Fd',
            'correct_answer': 'C',
            'explanation': 'Kinetik enerji = 1/2 × kütle × hız²',
            'exam_type': 'AYT',
            'subject_area': 'Fizik',
            'topic': 'Enerji',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.3
        },
        
        # AYT KİMYA
        {
            'question_text': 'Periyodik tabloda 1. grupta bulunan elementler hangi adla anılır?',
            'option_a': 'Halojenler',
            'option_b': 'Soy gazlar',
            'option_c': 'Alkali metaller',
            'option_d': 'Toprak alkali metaller',
            'option_e': 'Geçiş metalleri',
            'correct_answer': 'C',
            'explanation': '1. grup elementleri alkali metallerdir (Li, Na, K, Rb, Cs, Fr)',
            'exam_type': 'AYT',
            'subject_area': 'Kimya',
            'topic': 'Periyodik Tablo',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.1
        },
        {
            'question_text': 'pH = 7 olan bir çözelti nasıl tanımlanır?',
            'option_a': 'Asidik',
            'option_b': 'Bazik',
            'option_c': 'Nötr',
            'option_d': 'Amfoterik',
            'option_e': 'Tampon',
            'correct_answer': 'C',
            'explanation': 'pH = 7 nötr çözeltiyi gösterir. pH < 7 asidik, pH > 7 baziktir.',
            'exam_type': 'AYT',
            'subject_area': 'Kimya',
            'topic': 'Asit-Baz',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.5
        },
        
        # AYT BİYOLOJİ
        {
            'question_text': 'DNA\'nın yapısında hangi şeker bulunur?',
            'option_a': 'Glikoz',
            'option_b': 'Fruktoz',
            'option_c': 'Riboz',
            'option_d': 'Deoksiriboz',
            'option_e': 'Maltoz',
            'correct_answer': 'D',
            'explanation': 'DNA\'da deoksiriboz şekeri, RNA\'da riboz şekeri bulunur.',
            'exam_type': 'AYT',
            'subject_area': 'Biyoloji',
            'topic': 'Nükleik Asitler',
            'difficulty': 'Orta',
            'irt_difficulty': 0.0
        },
        {
            'question_text': 'Fotosentezin gerçekleştiği organele ne ad verilir?',
            'option_a': 'Mitokondri',
            'option_b': 'Kloroplast',
            'option_c': 'Ribozom',
            'option_d': 'Lizozom',
            'option_e': 'Golgi',
            'correct_answer': 'B',
            'explanation': 'Fotosentez kloroplastlarda gerçekleşir.',
            'exam_type': 'AYT',
            'subject_area': 'Biyoloji',
            'topic': 'Hücre',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.6
        },
        
        # YDT İNGİLİZCE
        {
            'question_text': 'What is the past tense of "go"?',
            'option_a': 'goed',
            'option_b': 'gone',
            'option_c': 'went',
            'option_d': 'going',
            'option_e': 'goes',
            'correct_answer': 'C',
            'explanation': 'Go fiilinin geçmiş zaman hali "went"tir.',
            'exam_type': 'YDT',
            'subject_area': 'İngilizce',
            'topic': 'Grammar',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.8
        },
        {
            'question_text': 'Choose the correct form: "She _____ to school every day."',
            'option_a': 'go',
            'option_b': 'goes',
            'option_c': 'going',
            'option_d': 'went',
            'option_e': 'gone',
            'correct_answer': 'B',
            'explanation': 'Present simple, 3. tekil şahıs için fiile -s takısı eklenir.',
            'exam_type': 'YDT',
            'subject_area': 'İngilizce',
            'topic': 'Present Simple',
            'difficulty': 'Kolay',
            'irt_difficulty': -0.7
        }
    ]
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    inserted = 0
    for q in questions:
        try:
            cur.execute("""
                INSERT INTO questions (
                    question_text, option_a, option_b, option_c, option_d, option_e,
                    correct_answer, explanation, exam_type, subject_area, topic,
                    difficulty, irt_difficulty, irt_discrimination, irt_guessing
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                q['question_text'], q['option_a'], q['option_b'], q['option_c'],
                q['option_d'], q.get('option_e'), q['correct_answer'], q['explanation'],
                q['exam_type'], q['subject_area'], q['topic'], q['difficulty'],
                q['irt_difficulty'], 1.2, 0.25
            ))
            inserted += 1
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            continue
        except Exception as e:
            print(f"⚠️ Soru eklenemedi: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ {inserted} adet soru başarıyla eklendi!")
    return inserted

def seed_admin_user():
    """Admin kullanıcı oluştur"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # Basit bir hash (gerçek uygulamada bcrypt kullanın!)
        import hashlib
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        
        cur.execute("""
            INSERT INTO users (
                email, username, password_hash, first_name, last_name,
                role, is_active, is_verified
            ) VALUES (
                'admin@kiro2.com', 'admin', %s, 'Platform', 'Admin',
                'admin', true, true
            )
        """, (password_hash,))
        
        conn.commit()
        print("✅ Admin kullanıcı oluşturuldu (admin@kiro2.com / admin123)")
    except psycopg2.errors.UniqueViolation:
        print("ℹ️ Admin kullanıcı zaten mevcut")
    except Exception as e:
        print(f"⚠️ Admin kullanıcı oluşturulamadı: {e}")
    
    conn.close()

def main():
    print("\n🚀 KIRO2 ACİL İÇERİK YÜKLEME")
    print("="*50)
    
    try:
        # Tabloları oluştur
        create_tables()
        
        # Test bağlantısı
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Mevcut soru sayısı
        cur.execute("SELECT COUNT(*) FROM questions")
        existing_count = cur.fetchone()[0]
        print(f"📊 Mevcut soru sayısı: {existing_count}")
        
        conn.close()
        
        if existing_count < 20:
            print("\n🔄 Acil içerik yükleniyor...")
            inserted = seed_emergency_questions()
            print(f"📈 Toplam soru sayısı: {existing_count + inserted}")
        else:
            print("ℹ️ Yeterli soru mevcut, ekleme yapılmadı")
        
        # Admin kullanıcı
        seed_admin_user()
        
        print("\n✅ İşlem tamamlandı!")
        print("\n📝 Sonraki adımlar:")
        print("1. python database_analysis.py - Detaylı analiz")
        print("2. cd backend/scripts && python populate_question_bank.py - Toplu yükleme")
        print("3. python osym_question_extractor.py - ÖSYM sorularını çıkar")
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Veritabanı bağlantı hatası: {e}")
        print("\n🔧 Çözüm:")
        print("1. PostgreSQL servisinin çalıştığından emin olun")
        print("2. DB_CONFIG içindeki bilgileri kontrol edin")
        print("3. psql -U postgres -c \"CREATE DATABASE kiro2;\"")
    except Exception as e:
        print(f"\n❌ Hata: {e}")

if __name__ == "__main__":
    main()
