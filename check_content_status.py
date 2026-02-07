#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIRO2 İçerik Durumu Detaylı Analizi"""

import asyncio
import asyncpg
import sys
import io

# Windows encoding fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def analyze_content():
    """Veritabanındaki içeriği detaylı analiz et"""
    
    # PostgreSQL bağlantısı
    conn = await asyncpg.connect(
        host='localhost', 
        port=5434, 
        user='postgres', 
        password='1470', 
        database='turkiye_sinav_db'
    )
    
    print("="*60)
    print("KIRO2 İÇERİK DURUMU ANALİZİ")
    print("="*60)
    
    # 1. Toplam soru sayısı
    total_questions = await conn.fetchval('SELECT COUNT(*) FROM sorular WHERE aktif = true')
    print(f"\n📊 TOPLAM AKTİF SORU: {total_questions}")
    
    # Durum değerlendirmesi
    if total_questions < 50:
        print("🔴 KRİTİK: Platform kullanılamaz durumda!")
        print("   → ACİL: emergency_content.sql yüklenmeli")
    elif total_questions < 500:
        print("🟡 UYARI: Soru sayısı yetersiz")
        print("   → OSYM PDF'leri işlenmeli")
    elif total_questions < 5000:
        print("🟠 ORTA: Daha fazla içerik gerekli")
    else:
        print("🟢 İYİ: İçerik yeterli seviyede")
    
    # 2. Sınav tiplerine göre dağılım
    print("\n📚 SINAV TİPLERİNE GÖRE DAĞILIM:")
    exam_distribution = await conn.fetch("""
        SELECT sinav_tipi, COUNT(*) as sayi 
        FROM sorular 
        WHERE aktif = true 
        GROUP BY sinav_tipi 
        ORDER BY sayi DESC
    """)
    
    for row in exam_distribution:
        exam_type = row['sinav_tipi'] or 'Belirtilmemiş'
        count = row['sayi']
        percentage = (count / total_questions * 100) if total_questions > 0 else 0
        print(f"   {exam_type}: {count} soru ({percentage:.1f}%)")
    
    # 3. Konulara göre dağılım
    print("\n📖 KONULARA GÖRE DAĞILIM (İlk 10):")
    topic_distribution = await conn.fetch("""
        SELECT konu, COUNT(*) as sayi 
        FROM sorular 
        WHERE aktif = true AND konu IS NOT NULL
        GROUP BY konu 
        ORDER BY sayi DESC 
        LIMIT 10
    """)
    
    for row in topic_distribution:
        topic = row['konu']
        count = row['sayi']
        print(f"   {topic}: {count} soru")
    
    # 4. Zorluk seviyesi dağılımı
    print("\n💪 ZORLUK SEVİYESİ DAĞILIMI:")
    difficulty_distribution = await conn.fetch("""
        SELECT zorluk, COUNT(*) as sayi 
        FROM sorular 
        WHERE aktif = true AND zorluk IS NOT NULL
        GROUP BY zorluk 
        ORDER BY zorluk
    """)
    
    if difficulty_distribution:
        for row in difficulty_distribution:
            difficulty = row['zorluk']
            count = row['sayi']
            bar = "█" * (count // 10) if count > 0 else ""
            print(f"   Seviye {difficulty}: {bar} {count} soru")
    else:
        print("   ⚠️ Zorluk seviyeleri tanımlı değil")
    
    # 5. Eksik bilgiler analizi
    print("\n⚠️ EKSİK BİLGİLER:")
    
    no_correct_answer = await conn.fetchval("""
        SELECT COUNT(*) FROM sorular 
        WHERE aktif = true AND (dogru_cevap IS NULL OR dogru_cevap = '')
    """)
    print(f"   Cevapsız sorular: {no_correct_answer}")
    
    no_topic = await conn.fetchval("""
        SELECT COUNT(*) FROM sorular 
        WHERE aktif = true AND konu IS NULL
    """)
    print(f"   Konusuz sorular: {no_topic}")
    
    no_exam_type = await conn.fetchval("""
        SELECT COUNT(*) FROM sorular 
        WHERE aktif = true AND sinav_tipi IS NULL
    """)
    print(f"   Sınav tipi belirtilmemiş: {no_exam_type}")
    
    # 6. Türkçe karakter kontrolü
    print("\n🔤 TÜRKÇE KARAKTER ANALİZİ:")
    turkish_chars = await conn.fetch("""
        SELECT COUNT(*) as sayi,
               SUM(CASE WHEN metin LIKE '%ğ%' OR metin LIKE '%Ğ%' THEN 1 ELSE 0 END) as g_char,
               SUM(CASE WHEN metin LIKE '%ş%' OR metin LIKE '%Ş%' THEN 1 ELSE 0 END) as s_char,
               SUM(CASE WHEN metin LIKE '%ı%' OR metin LIKE '%İ%' THEN 1 ELSE 0 END) as i_char,
               SUM(CASE WHEN metin LIKE '%ç%' OR metin LIKE '%Ç%' THEN 1 ELSE 0 END) as c_char
        FROM sorular 
        WHERE aktif = true
    """)
    
    if turkish_chars:
        row = turkish_chars[0]
        print(f"   'ğ/Ğ' içeren: {row['g_char']} soru")
        print(f"   'ş/Ş' içeren: {row['s_char']} soru")
        print(f"   'ı/İ' içeren: {row['i_char']} soru")
        print(f"   'ç/Ç' içeren: {row['c_char']} soru")
    
    # 7. Son eklenen sorular
    print("\n📝 SON EKLENEN 3 SORU:")
    recent_questions = await conn.fetch("""
        SELECT metin, sinav_tipi, konu, olusturma_tarihi
        FROM sorular 
        WHERE aktif = true 
        ORDER BY olusturma_tarihi DESC 
        LIMIT 3
    """)
    
    for i, q in enumerate(recent_questions, 1):
        text = q['metin'][:100] if q['metin'] else "Metin yok"
        exam = q['sinav_tipi'] or "?"
        topic = q['konu'] or "?"
        print(f"\n   {i}. [{exam}] {text}...")
        print(f"      Konu: {topic}")
    
    # 8. Öneriler
    print("\n💡 ÖNERİLER:")
    
    if total_questions < 500:
        print("   1. ACİL: emergency_content.sql dosyasını yükleyin")
        print("      psql -U postgres -d turkiye_sinav_db -p 5434 -f emergency_content.sql")
        
        print("\n   2. Python scriptlerini çalıştırın:")
        print("      python backend/load_50_questions.py")
        print("      python backend/generate_20_working.py")
        
        print("\n   3. OSYM PDF'lerini işleyin:")
        print("      python extract_osym_2025.py")
    
    elif total_questions < 5000:
        print("   1. Tüm OSYM arşivini işleyin (2016-2025)")
        print("   2. Kaliteli yayınevlerinden içerik ekleyin")
        print("   3. AI ile varyasyon üretimi başlatın")
    
    else:
        print("   ✅ İçerik seviyesi iyi durumda")
        print("   - Düzenli olarak yeni sorular ekleyin")
        print("   - Kalite kontrollerini sürdürün")
    
    # 9. Hedef durumu
    print("\n🎯 HEDEF DURUMU:")
    target = 50000
    progress = (total_questions / target * 100) if target > 0 else 0
    filled = int(progress / 5)
    bar = "█" * filled + "░" * (20 - filled)
    print(f"   İlerleme: [{bar}] {progress:.1f}%")
    print(f"   Mevcut: {total_questions:,} / Hedef: {target:,}")
    print(f"   Kalan: {target - total_questions:,} soru")
    
    print("\n" + "="*60)
    
    # Bağlantıyı kapat
    await conn.close()
    
    return total_questions

if __name__ == "__main__":
    total = asyncio.run(analyze_content())
    
    # Exit code based on status
    if total < 50:
        sys.exit(2)  # Critical
    elif total < 500:
        sys.exit(1)  # Warning
    else:
        sys.exit(0)  # OK