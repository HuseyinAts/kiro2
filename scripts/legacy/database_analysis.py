"""
KIRO2 Veritabanı Gerçek Durum Analizi
=====================================
Bu script veritabanınızın gerçek durumunu analiz eder.
"""

import psycopg2
from psycopg2 import sql
import json
from datetime import datetime
import os
import sys

# Backend path'i ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def analyze_kiro2_database():
    """Veritabanı analizi"""
    
    # Bağlantı parametreleri - .env dosyanızdan alın veya güncelleyin
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'kiro2',
        'user': 'postgres',
        'password': 'postgres',  # Kendi şifrenizi girin
        'port': 5432
    }
    
    print("🔍 KIRO2 VERİTABANI ANALİZİ BAŞLIYOR...")
    print("="*70)
    
    try:
        # PostgreSQL bağlantısı
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("✅ Veritabanı bağlantısı başarılı!\n")
        
        # 1. TABLO LİSTESİ
        print("📋 TABLOLAR:")
        print("-"*30)
        cur.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        for table, col_count in tables:
            # Her tablo için satır sayısı
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cur.fetchone()[0]
            print(f"  ├─ {table}: {row_count} kayıt, {col_count} sütun")
        
        print(f"\n  Toplam: {len(tables)} tablo\n")
        
        # 2. QUESTIONS TABLOSU DETAYLI ANALİZ
        print("📚 SORU BANKASI ANALİZİ:")
        print("-"*30)
        
        # Toplam soru
        cur.execute("SELECT COUNT(*) FROM questions")
        total_questions = cur.fetchone()[0]
        print(f"  Toplam Soru: {total_questions}")
        
        if total_questions > 0:
            # Sınav tipi dağılımı
            print("\n  📝 Sınav Tipi Dağılımı:")
            cur.execute("""
                SELECT exam_type, COUNT(*) as count
                FROM questions 
                GROUP BY exam_type
                ORDER BY count DESC
            """)
            for exam_type, count in cur.fetchall():
                percentage = (count/total_questions)*100
                print(f"    ├─ {exam_type}: {count} soru ({percentage:.1f}%)")
            
            # Konu dağılımı
            print("\n  📖 Konu Dağılımı:")
            cur.execute("""
                SELECT subject_area, COUNT(*) as count
                FROM questions 
                WHERE subject_area IS NOT NULL
                GROUP BY subject_area
                ORDER BY count DESC
            """)
            for subject, count in cur.fetchall():
                percentage = (count/total_questions)*100
                print(f"    ├─ {subject}: {count} soru ({percentage:.1f}%)")
            
            # Zorluk dağılımı
            print("\n  ⚡ Zorluk Seviyesi:")
            cur.execute("""
                SELECT difficulty, COUNT(*) as count
                FROM questions 
                WHERE difficulty IS NOT NULL
                GROUP BY difficulty
                ORDER BY difficulty
            """)
            for difficulty, count in cur.fetchall():
                percentage = (count/total_questions)*100
                bar = "█" * int(percentage/5)
                print(f"    ├─ {difficulty}: {count} soru {bar} {percentage:.1f}%")
            
            # IRT parametreleri olan sorular
            cur.execute("""
                SELECT COUNT(*) 
                FROM questions 
                WHERE irt_difficulty IS NOT NULL
            """)
            irt_count = cur.fetchone()[0]
            print(f"\n  🎯 IRT Kalibreli Sorular: {irt_count}/{total_questions}")
            
            # Açıklaması olan sorular
            cur.execute("""
                SELECT COUNT(*) 
                FROM questions 
                WHERE explanation IS NOT NULL AND explanation != ''
            """)
            explained_count = cur.fetchone()[0]
            print(f"  💡 Açıklamalı Sorular: {explained_count}/{total_questions}")
            
            # Görsel içeren sorular
            cur.execute("""
                SELECT COUNT(*) 
                FROM questions 
                WHERE image_url IS NOT NULL AND image_url != ''
            """)
            image_count = cur.fetchone()[0]
            print(f"  🖼️ Görsel İçeren Sorular: {image_count}/{total_questions}")
            
            # Son eklenen soru
            cur.execute("""
                SELECT question_text, created_at 
                FROM questions 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            last_question = cur.fetchone()
            if last_question:
                print(f"\n  📅 Son Eklenen Soru:")
                print(f"    Tarih: {last_question[1]}")
                print(f"    Soru: {last_question[0][:100]}...")
        
        # 3. KULLANICILAR
        print("\n👥 KULLANICI ANALİZİ:")
        print("-"*30)
        
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        print(f"  Toplam Kullanıcı: {total_users}")
        
        if total_users > 0:
            # Rol dağılımı
            cur.execute("""
                SELECT role, COUNT(*) 
                FROM users 
                GROUP BY role
            """)
            print("\n  Rol Dağılımı:")
            for role, count in cur.fetchall():
                print(f"    ├─ {role}: {count} kullanıcı")
            
            # Aktif kullanıcılar
            cur.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
            active_users = cur.fetchone()[0]
            print(f"\n  ✅ Aktif Kullanıcılar: {active_users}")
            
            # Doğrulanmış kullanıcılar
            cur.execute("SELECT COUNT(*) FROM users WHERE is_verified = true")
            verified_users = cur.fetchone()[0]
            print(f"  ✅ Doğrulanmış Kullanıcılar: {verified_users}")
        
        # 4. İÇERİK KALİTESİ SKORU
        print("\n📊 İÇERİK KALİTESİ SKORU:")
        print("-"*30)
        
        quality_score = 0
        max_score = 100
        
        # Skorlama kriterleri
        if total_questions >= 2000: quality_score += 25
        elif total_questions >= 1000: quality_score += 15
        elif total_questions >= 500: quality_score += 10
        elif total_questions >= 100: quality_score += 5
        
        if total_questions > 0:
            if explained_count/total_questions >= 0.8: quality_score += 25
            elif explained_count/total_questions >= 0.5: quality_score += 15
            elif explained_count/total_questions >= 0.3: quality_score += 10
            
            if irt_count/total_questions >= 0.8: quality_score += 25
            elif irt_count/total_questions >= 0.5: quality_score += 15
            elif irt_count/total_questions >= 0.3: quality_score += 10
            
            if image_count/total_questions >= 0.3: quality_score += 25
            elif image_count/total_questions >= 0.15: quality_score += 15
            elif image_count/total_questions >= 0.05: quality_score += 10
        
        # Skor gösterimi
        score_bar = "█" * int(quality_score/5) + "░" * int((max_score-quality_score)/5)
        print(f"  Kalite Skoru: [{score_bar}] {quality_score}/{max_score}")
        
        if quality_score >= 80:
            print("  Durum: 🟢 Mükemmel - Üretime hazır!")
        elif quality_score >= 60:
            print("  Durum: 🟡 İyi - Biraz daha içerik gerekli")
        elif quality_score >= 40:
            print("  Durum: 🟠 Orta - Önemli geliştirmeler gerekli")
        elif quality_score >= 20:
            print("  Durum: 🔴 Zayıf - Acil içerik eklenmeli")
        else:
            print("  Durum: ⚫ Kritik - İçerik yok denecek kadar az!")
        
        # 5. ÖNERİLER
        print("\n💡 ÖNERİLER:")
        print("-"*30)
        
        if total_questions < 100:
            print("  🚨 ACİL: En az 100 soru eklenmeli!")
            print("     - production_seed.py scriptini çalıştırın")
            print("     - populate_question_bank.py ile toplu yükleme yapın")
        elif total_questions < 500:
            print("  ⚠️ ÖNEMLİ: 500+ soru hedefine ulaşın")
            print("     - ÖSYM PDF'lerinden soru çıkarın")
            print("     - AI ile soru üretimi yapın")
        elif total_questions < 1000:
            print("  📈 İYİ: 1000+ soru için çalışın")
        elif total_questions < 2000:
            print("  ✨ ÇOK İYİ: 2000+ soru için son hamle")
        else:
            print("  🎉 MÜKEMMEL: İçerik hedefine ulaşıldı!")
        
        if total_questions > 0 and explained_count/total_questions < 0.5:
            print("\n  📝 Soruların %50'sinden fazlasına açıklama ekleyin")
        
        if total_questions > 0 and irt_count/total_questions < 0.5:
            print("  📊 IRT kalibrasyonu eksik - calibrate_irt.py çalıştırın")
        
        # 6. HIZLI EYLEM PLANI
        print("\n🚀 HIZLI EYLEM PLANI:")
        print("-"*30)
        print("  1. cd C:\\Users\\husey\\kiro2\\backend\\scripts")
        print("  2. python production_seed.py")
        print("  3. python populate_question_bank.py")
        print("  4. python osym_question_extractor.py")
        print("  5. python osym_to_db_import.py")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✅ Analiz tamamlandı!")
        
        return {
            'total_questions': total_questions,
            'total_users': total_users,
            'quality_score': quality_score,
            'tables': len(tables)
        }
        
    except psycopg2.OperationalError as e:
        print("❌ Veritabanı bağlantı hatası!")
        print(f"   Hata: {str(e)}")
        print("\n🔧 Çözüm önerileri:")
        print("  1. PostgreSQL servisinin çalıştığından emin olun")
        print("  2. Bağlantı bilgilerini kontrol edin (host, port, user, password)")
        print("  3. 'kiro2' veritabanının oluşturulduğundan emin olun")
        print("\n  Veritabanı oluşturmak için:")
        print("  psql -U postgres -c \"CREATE DATABASE kiro2;\"")
        return None
        
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\nKIRO2 - Veritabanı Gerçek Durum Analizi")
    print("========================================\n")
    
    result = analyze_kiro2_database()
    
    if result:
        print(f"\n📊 ÖZET:")
        print(f"  • {result['tables']} tablo")
        print(f"  • {result['total_questions']} soru")
        print(f"  • {result['total_users']} kullanıcı")
        print(f"  • Kalite skoru: {result['quality_score']}/100")
