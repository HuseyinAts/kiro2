#!/usr/bin/env python3
"""KIRO2 Soru Bankası Detaylı Durum Analizi"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

def connect_db():
    return psycopg2.connect(
        host="localhost",
        port=5434,
        database="kiro2",
        user="postgres",
        cursor_factory=RealDictCursor
    )

def analyze_questions():
    conn = connect_db()
    
    with conn.cursor() as cur:
        # Genel istatistikler
        cur.execute("""
            SELECT 
                COUNT(*) as total_questions,
                COUNT(DISTINCT exam_type) as unique_exam_types,
                COUNT(DISTINCT subject_area) as unique_subjects,
                COUNT(DISTINCT topic) as unique_topics,
                COUNT(DISTINCT difficulty) as unique_difficulties
            FROM questions
        """)
        general_stats = cur.fetchone()
        
        # En çok soru olan konular
        cur.execute("""
            SELECT 
                exam_type,
                subject_area,
                topic,
                COUNT(*) as count
            FROM questions
            WHERE topic IS NOT NULL
            GROUP BY exam_type, subject_area, topic
            ORDER BY count DESC
            LIMIT 20
        """)
        top_topics = cur.fetchall()
        
        # Eksik alanlar
        cur.execute("""
            SELECT 
                SUM(CASE WHEN explanation IS NULL OR explanation = '' THEN 1 ELSE 0 END) as no_explanation,
                SUM(CASE WHEN question_image_url IS NOT NULL AND question_image_url != '' THEN 1 ELSE 0 END) as has_images,
                SUM(CASE WHEN visual_content IS NOT NULL THEN 1 ELSE 0 END) as has_visual_content,
                SUM(CASE WHEN option_e IS NOT NULL AND option_e != '' THEN 1 ELSE 0 END) as has_option_e
            FROM questions
        """)
        field_stats = cur.fetchone()
        
        # Özel sınav tiplerini kontrol
        cur.execute("""
            SELECT DISTINCT exam_type, COUNT(*) as count
            FROM questions
            GROUP BY exam_type
            ORDER BY count DESC
        """)
        exam_types = cur.fetchall()
        
        # Ders bazlı detaylı dağılım
        cur.execute("""
            SELECT 
                subject_area,
                exam_type,
                COUNT(*) as count,
                AVG(irt_difficulty) as avg_irt_diff,
                AVG(irt_discrimination) as avg_irt_disc
            FROM questions
            GROUP BY subject_area, exam_type
            ORDER BY subject_area, count DESC
        """)
        subject_details = cur.fetchall()
        
        # Son güncelleme durumu
        cur.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM questions
            WHERE created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        """)
        recent_activity = cur.fetchall()
        
        print("\n" + "="*80)
        print("KIRO2 SORU BANKASI DETAYLI DURUM RAPORU")
        print("="*80)
        
        print(f"\n📊 GENEL İSTATİSTİKLER:")
        print(f"   Toplam Soru: {general_stats['total_questions']:,}")
        print(f"   Benzersiz Sınav Tipi: {general_stats['unique_exam_types']}")
        print(f"   Benzersiz Ders: {general_stats['unique_subjects']}")
        print(f"   Benzersiz Konu: {general_stats['unique_topics']}")
        print(f"   Benzersiz Zorluk Seviyesi: {general_stats['unique_difficulties']}")
        
        print(f"\n📝 İÇERİK KALİTESİ:")
        print(f"   Açıklaması Olmayan: {field_stats['no_explanation']:,} soru")
        print(f"   Görsel İçeren: {field_stats['has_images']:,} soru")
        print(f"   Visual Content Alanı Dolu: {field_stats['has_visual_content']:,} soru")
        print(f"   5 Seçenekli (E şıkkı olan): {field_stats['has_option_e']:,} soru")
        
        print(f"\n🎯 SINAV TİPİ DAĞILIMI:")
        for exam in exam_types:
            percentage = (exam['count'] / general_stats['total_questions']) * 100
            print(f"   {exam['exam_type']}: {exam['count']:,} soru ({percentage:.1f}%)")
        
        print(f"\n📚 EN ÇOK SORU OLAN KONULAR (İlk 10):")
        for i, topic in enumerate(top_topics[:10], 1):
            print(f"   {i}. [{topic['exam_type']}] {topic['subject_area']} - {topic['topic']}: {topic['count']} soru")
        
        print(f"\n📈 SON 7 GÜN AKTİVİTE:")
        for activity in recent_activity:
            print(f"   {activity['date']}: {activity['count']:,} soru eklendi")
        
        print(f"\n🔬 DERS BAZLI IRT ANALİZİ (İlk 10):")
        for detail in subject_details[:10]:
            if detail['avg_irt_diff'] and detail['avg_irt_disc']:
                print(f"   {detail['subject_area']} ({detail['exam_type']}): {detail['count']} soru")
                print(f"      Ort. IRT Zorluk: {detail['avg_irt_diff']:.3f}, Ayırt Edicilik: {detail['avg_irt_disc']:.3f}")
        
        # Kritik durumlar
        print(f"\n⚠️ KRİTİK TESPİTLER:")
        
        if general_stats['total_questions'] < 50000:
            print(f"   ✓ Soru bankası yeterli büyüklükte ({general_stats['total_questions']:,} soru)")
        
        if field_stats['no_explanation'] > general_stats['total_questions'] * 0.5:
            print(f"   ⚠️ Soruların %{(field_stats['no_explanation']/general_stats['total_questions']*100):.0f}'inde açıklama eksik!")
        
        # TYT/AYT/YDT kontrolü
        tyt_count = next((e['count'] for e in exam_types if e['exam_type'] == 'tyt'), 0)
        ayt_count = next((e['count'] for e in exam_types if e['exam_type'] == 'ayt'), 0)
        ydt_count = next((e['count'] for e in exam_types if e['exam_type'] == 'YDT'), 0)
        
        print(f"\n📊 ANA SINAV TİPLERİ DURUMU:")
        print(f"   TYT: {tyt_count:,} soru - {'✅ YETERLİ' if tyt_count > 10000 else '⚠️ DAHA FAZLA SORU EKLENMELİ'}")
        print(f"   AYT: {ayt_count:,} soru - {'✅ YETERLİ' if ayt_count > 10000 else '⚠️ DAHA FAZLA SORU EKLENMELİ'}")
        print(f"   YDT: {ydt_count:,} soru - {'✅ YETERLİ' if ydt_count > 2000 else '⚠️ DAHA FAZLA SORU EKLENMELİ'}")
        
        print("\n" + "="*80)
        
    conn.close()

if __name__ == "__main__":
    import sys
    import io
    
    # Windows terminal encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    analyze_questions()